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
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_database, cleanup_database
from app.security import SecurityConfig, get_security_config
from app.middleware.security import SecurityMiddleware, InputValidationMiddleware, SQLInjectionProtectionMiddleware
from app.routes import (
    home, units, job_titles, persons, 
    assignments, orgchart, api
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

# Templates
templates = Jinja2Templates(directory="templates")

# Include routes
app.include_router(home.router, tags=["Home"])
app.include_router(units.router, prefix="/units", tags=["Units"])
app.include_router(job_titles.router, prefix="/job-titles", tags=["Job Titles"])
app.include_router(persons.router, prefix="/persons", tags=["Persons"])
app.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
app.include_router(orgchart.router, prefix="/orgchart", tags=["Orgchart"])
app.include_router(api.router, prefix="/api", tags=["API"])

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