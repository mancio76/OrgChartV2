"""
FastAPI main application entry point
Organigramma Web App with Security-by-Design
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_database, cleanup_database
from app.security import SecurityConfig, get_security_config

from app.middleware.security import SecurityMiddleware, InputValidationMiddleware, SQLInjectionProtectionMiddleware
from app.middleware.security_mini import MiniSecurityMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routes import (
    home, units, unit_types, job_titles, persons, companies,
    assignments, orgchart, api, health, themes, import_export
)

# Get configuration
settings = get_settings()

# Setup logging based on configuration
def setup_logging():
    """Configure logging based on settings"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.logging.level))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(settings.logging.format)
    
    # Console handler
    if settings.logging.to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if settings.logging.to_file:
        file_handler = RotatingFileHandler(
            settings.logging.file_path,
            maxBytes=settings.logging.max_file_size,
            backupCount=settings.logging.backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)

logger = setup_logging()

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup and cleanup on shutdown"""
    logger.info(f"Starting {settings.application.title} v{settings.application.version}")
    logger.info(f"Environment: {settings.application.environment}")
    logger.info(f"Debug mode: {settings.server.debug}")
    logger.info(f"Log level: {settings.logging.level}")
    
    try:
        init_database()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    logger.info(f"Shutting down {settings.application.title}")
    try:
        cleanup_database()
        logger.info("Database cleanup completed")
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")

# FastAPI app instance with configuration-based settings
app = FastAPI(
    title=settings.application.title,
    description=settings.application.description,
    version=settings.application.version,
    debug=settings.server.debug,
    lifespan=lifespan
)

# Security configuration
security_config = SecurityConfig({
    'secret_key': settings.security.secret_key,
    'csrf_protection': settings.security.csrf_protection,
    'secure_cookies': settings.security.secure_cookies,
    'https_only': settings.security.https_only,
    'allowed_hosts': settings.security.allowed_hosts,
    'rate_limit_enabled': True,
    'max_requests_per_minute': 100
})

# REQUIRED: Add SessionMiddleware for CSRF to work properly
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.security.secret_key,
    max_age=86400,  # 24 hours
    same_site="lax",
    https_only=settings.security.https_only
)

#OR (for a more lightweight check)
# app.add_middleware(
#     MiniSecurityMiddleware,
#     secret_key=settings.security.secret_key
# )

# Add security middleware (order matters - add in reverse order of execution)
app.add_middleware(SecurityMiddleware, security_config=security_config)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(SQLInjectionProtectionMiddleware)

# CORS middleware (if needed)
if settings.security.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates (shared instance with registered helpers)
from app.templates import templates

# Include routes
app.include_router(health.router, tags=["Health"])
app.include_router(home.router, tags=["Home"])
app.include_router(units.router, prefix="/units", tags=["Units"])
app.include_router(unit_types.router, prefix="/unit_types", tags=["Unit Types"])
app.include_router(job_titles.router, prefix="/job-titles", tags=["Job Titles"])
app.include_router(persons.router, prefix="/persons", tags=["Persons"])
app.include_router(companies.router, prefix="/companies", tags=["Companies"])
app.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
app.include_router(orgchart.router, prefix="/orgchart", tags=["Orgchart"])
app.include_router(themes.router, prefix="/themes", tags=["Themes"])
app.include_router(import_export.router, prefix="/import-export", tags=["Import/Export"])
app.include_router(api.router, prefix="/api", tags=["API"])

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/img/favicon.ico")

# Dynamic CSS generation route
@app.get("/css/themes.css", include_in_schema=False)
async def dynamic_themes_css(request: Request):
    """Serve dynamically generated CSS for unit type themes with conditional requests support"""
    from fastapi.responses import Response
    from app.services.unit_type_theme import UnitTypeThemeService
    import hashlib
    import time
    
    try:
        theme_service = UnitTypeThemeService()
        css_content = theme_service.generate_dynamic_css()
        
        # Generate ETag for caching based on content hash
        etag = hashlib.md5(css_content.encode()).hexdigest()
        
        # Check if client has cached version (conditional request)
        client_etag = request.headers.get("if-none-match", "").strip('"')
        if client_etag == etag:
            logger.debug("CSS not modified, returning 304")
            return Response(status_code=304)
        
        # Set cache headers for performance
        headers = {
            "Content-Type": "text/css; charset=utf-8",
            "Cache-Control": "public, max-age=3600, must-revalidate",  # Cache for 1 hour with validation
            "ETag": f'"{etag}"',
            "Last-Modified": time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
            "Vary": "Accept-Encoding"
        }
        
        logger.debug(f"Serving dynamic CSS ({len(css_content)} chars) with ETag: {etag}")
        return Response(content=css_content, headers=headers)
        
    except Exception as e:
        logger.error(f"Error generating dynamic CSS: {e}")
        # Return minimal fallback CSS
        fallback_css = """
/* Fallback CSS - Theme generation failed */
.unit-themed {
    border: 2px solid #0dcaf0;
    background: linear-gradient(135deg, #ffffff 0%, #f0fdff 100%);
    transition: all 0.3s ease;
}
.unit-themed:hover {
    box-shadow: 0 1rem 2rem rgba(13, 202, 240, 0.25);
    transform: translateY(-2px);
}
.unit-organizational {
    border: 2px solid #0dcaf0;
    background: linear-gradient(135deg, #ffffff 0%, #f0fdff 100%);
}
.unit-organizational:hover {
    box-shadow: 0 1rem 2rem rgba(13, 202, 240, 0.25);
}
"""
        return Response(
            content=fallback_css,
            headers={
                "Content-Type": "text/css; charset=utf-8",
                "Cache-Control": "no-cache"
            }
        )

# Test route for Task 6.3 - Form validation and user feedback
@app.get("/test-validation", response_class=HTMLResponse)
async def test_validation(request: Request):
    """Test page for enhanced form validation features"""
    return templates.TemplateResponse(
        "test_validation.html",
        {
            "request": request,
            "page_title": "Test Validazione Avanzata",
            "page_subtitle": "Implementazione Task 6.3 - Form validation e user feedback"
        }
    )

# Test route for Task 6 - Theme helper functions
@app.get("/test-theme-helpers", response_class=HTMLResponse)
async def test_theme_helpers(request: Request):
    """Test page for theme helper functions"""
    from app.models.unit import Unit
    from app.models.unit_type import UnitType
    from app.models.unit_type_theme import UnitTypeTheme
    
    # Create test data
    theme = UnitTypeTheme(
        id=1,
        name="Test Theme",
        icon_class="building",
        emoji_fallback="🏢",
        primary_color="#0d6efd",
        secondary_color="#f8f9ff",
        text_color="#0d6efd",
        border_color="#0d6efd",
        border_width=4,
        css_class_suffix="test",
        display_label="Test Unit Type"
    )
    
    unit_type = UnitType(id=1, name="Test Unit Type", theme_id=1)
    unit_type.theme = theme
    
    unit = Unit(id=1, name="Test Unit", unit_type_id=1)
    unit.unit_type = unit_type
    
    return templates.TemplateResponse(
        "test_theme_helpers.html",
        {
            "request": request,
            "unit": unit
        }
    )

# API Test page
@app.get("/api-test", response_class=HTMLResponse)
async def api_test_page(request: Request):
    """API testing page"""
    return templates.TemplateResponse(
        "api_test.html",
        {
            "request": request,
            "page_title": "API Test",
            "page_icon": "code-slash"
        }
    )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/404.html", 
        {"request": request}, 
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Server error: {exc}")
    return templates.TemplateResponse(
        "errors/500.html", 
        {"request": request}, 
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.server.host, 
        port=settings.server.port, 
        reload=settings.server.reload,
        log_level=settings.logging.level.lower(),
        access_log=settings.server.access_log
    )