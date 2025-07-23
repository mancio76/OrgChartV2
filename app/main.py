"""
FastAPI main application entry point
Organigramma Web App
"""
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.database import init_database, cleanup_database
from app.routes import (
    home, units, job_titles, persons, 
    assignments, orgchart, api
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup and cleanup on shutdown"""
    logger.info("Starting Organigramma Web App")
    try:
        init_database()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    logger.info("Shutting down Organigramma Web App")
    try:
        cleanup_database()
        logger.info("Database cleanup completed")
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")

# FastAPI app instance
app = FastAPI(
    title="Organigramma Web App",
    description="Sistema di gestione organigramma aziendale con storicizzazione",
    version="1.0.0",
    lifespan=lifespan
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
    uvicorn.run(app, host=os.getenv("RUN_HOST", "0.0.0.0"), port=os.getenv("RUN_PORT", 8000), reload=True)