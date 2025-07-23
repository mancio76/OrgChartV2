"""
Home page routes
"""

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
from app.services.unit import UnitService
from app.services.assignment import AssignmentService

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_unit_service():
    return UnitService()


def get_assignment_service():
    return AssignmentService()


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    unit_service: UnitService = Depends(get_unit_service),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Dashboard homepage"""
    try:
        # Get dashboard statistics
        stats = {
            'total_units': unit_service.count(),
            'total_persons': 0,  # Will be updated when person service is created
            'total_job_titles': 0,  # Will be updated when job title service is created
        }
        
        # Get assignment statistics
        assignment_stats = assignment_service.get_statistics()
        stats.update(assignment_stats)
        
        # Get recent assignments (last 10)
        recent_assignments = assignment_service.get_current_assignments()[:10]
        
        # Get hierarchy overview
        hierarchy_stats = unit_service.get_hierarchy_stats()
        
        return templates.TemplateResponse(
            "home/dashboard.html",
            {
                "request": request,
                "stats": stats,
                "recent_assignments": recent_assignments,
                "hierarchy_stats": hierarchy_stats[:5],  # Top 5 units
                "page_title": "Dashboard"
            }
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return templates.TemplateResponse(
            "errors/500.html",
            {"request": request, "error": str(e)},
            status_code=500
        )