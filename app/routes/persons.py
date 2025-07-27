"""
Persons CRUD routes
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import logging
from app.services.person import PersonService
from app.services.assignment import AssignmentService
from app.models.person import Person
from app.models.base import ModelValidationException
from app.security import CSRFProtection
from app.security_csfr import generate_csrf_token, validate_csrf_token, add_csrf_to_context

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_person_service():
    return PersonService()


def get_assignment_service():
    return AssignmentService()


@router.get("/", response_class=HTMLResponse)
async def list_persons(
    request: Request,
    search: Optional[str] = None,
    filter_type: Optional[str] = None,
    person_service: PersonService = Depends(get_person_service)
):
    """List all persons"""
    try:
        if search:
            persons = person_service.search(search, ['name', 'short_name', 'email'])
        else:
            persons = person_service.get_all()
        
        # Apply filters
        if filter_type:
            if filter_type == "with_assignments":
                persons = [p for p in persons if p.current_assignments_count > 0]
            elif filter_type == "without_assignments":
                persons = [p for p in persons if p.current_assignments_count == 0]
            elif filter_type == "multiple_assignments":
                persons = [p for p in persons if p.current_assignments_count > 1]
        
        return templates.TemplateResponse(
            "persons/list.html",
            {
                "request": request,
                "persons": persons,
                "search": search or "",
                "filter_type": filter_type or "",
                "page_title": "Persone",
                "page_icon": "people"
            }
        )
    except Exception as e:
        logger.error(f"Error listing persons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new", response_class=HTMLResponse)
async def create_person_form(
    request: Request,
    csrf_token: str = Depends(generate_csrf_token)
    ):
    """Show create person form"""
    try:
        context = {
            "request": request,
            "page_title": "Nuova Persona",
            "page_icon": "person-plus",
            "breadcrumb": [
                {"name": "Persone", "url": "/persons"},
                {"name": "Nuova Persona"}
            ],
            "csrf_token": csrf_token
        }
        return templates.TemplateResponse("persons/create.html", context)
    except Exception as e:
        logger.error(f"Error loading create person form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def create_person(
    request: Request,
    csrf_protection: bool = Depends(validate_csrf_token),
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    person_service: PersonService = Depends(get_person_service)
):
    """Create new person"""
    try:
        # Create person model
        person = Person(
            name=name.strip(),
            short_name=short_name.strip() if short_name else None,
            email=email.strip() if email else None
        )
        
        # Create person
        created_person = person_service.create(person)
        
        return RedirectResponse(
            url=f"/persons/{created_person.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        return templates.TemplateResponse(
            "persons/create.html",
            {
                "request": request,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": await request.form(),
                "page_title": "Nuova Persona",
                "page_icon": "person-plus",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": "Nuova Persona"}
                ]
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating person: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/duplicates", response_class=HTMLResponse)
async def find_duplicate_persons(
    request: Request,
    person_service: PersonService = Depends(get_person_service)
):
    """Find potential duplicate persons"""
    try:
        # Find potential duplicates based on name similarity
        duplicates = person_service.find_potential_duplicates()
        
        return templates.TemplateResponse(
            "persons/duplicates.html",
            {
                "request": request,
                "duplicates": duplicates,
                "page_title": "Persone Duplicate",
                "page_icon": "people-fill",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": "Duplicati"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error finding duplicate persons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/statistics", response_class=HTMLResponse)
async def person_statistics_report(
    request: Request,
    person_service: PersonService = Depends(get_person_service)
):
    """Show person statistics report"""
    try:
        # Get comprehensive statistics
        statistics = person_service.get_comprehensive_statistics()
        
        return templates.TemplateResponse(
            "persons/statistics.html",
            {
                "request": request,
                "statistics": statistics,
                "page_title": "Statistiche Persone",
                "page_icon": "bar-chart",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": "Statistiche"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error generating person statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{person_id}", response_class=HTMLResponse)
async def person_detail(
    request: Request,
    person_id: int,
    person_service: PersonService = Depends(get_person_service),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Show person details"""
    try:
        person = person_service.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        # Get current assignments
        current_assignments = assignment_service.get_assignments_by_person(person_id, current_only=True)
        
        # Get assignment history (last 10)
        assignment_history = assignment_service.get_assignments_by_person(person_id, current_only=False)[:10]
        
        # Get person statistics
        person_stats = person_service.get_person_statistics(person_id)
        
        return templates.TemplateResponse(
            "persons/detail.html",
            {
                "request": request,
                "person": person,
                "current_assignments": current_assignments,
                "assignment_history": assignment_history,
                "person_stats": person_stats,
                "page_title": f"Persona: {person.name}",
                "page_icon": "person",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": person.name}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{person_id}/edit", response_class=HTMLResponse)
async def edit_person_form(
    request: Request,
    person_id: int,
    person_service: PersonService = Depends(get_person_service)
):
    """Show edit person form"""
    try:
        person = person_service.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        return templates.TemplateResponse(
            "persons/edit.html",
            {
                "request": request,
                "person": person,
                "page_title": f"Modifica Persona: {person.name}",
                "page_icon": "person-gear",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": person.name, "url": f"/persons/{person_id}"},
                    {"name": "Modifica"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading edit form for person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{person_id}/edit")
async def update_person(
    request: Request,
    person_id: int,
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    person_service: PersonService = Depends(get_person_service)
):
    """Update existing person"""
    try:
        # Get existing person
        existing_person = person_service.get_by_id(person_id)
        if not existing_person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        # Update person model
        existing_person.name = name.strip()
        existing_person.short_name = short_name.strip() if short_name else None
        existing_person.email = email.strip() if email else None
        
        # Update person
        updated_person = person_service.update(existing_person)
        
        return RedirectResponse(
            url=f"/persons/{updated_person.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        person = person_service.get_by_id(person_id)
        return templates.TemplateResponse(
            "persons/edit.html",
            {
                "request": request,
                "person": person,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": await request.form(),
                "page_title": f"Modifica Persona: {person.name}",
                "page_icon": "person-gear",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": person.name, "url": f"/persons/{person_id}"},
                    {"name": "Modifica"}
                ]
            },
            status_code=400
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{person_id}/delete")
async def delete_person(
    person_id: int,
    person_service: PersonService = Depends(get_person_service)
):
    """Delete person"""
    try:
        # Check if person can be deleted
        can_delete, reason = person_service.can_delete(person_id)
        if not can_delete:
            raise HTTPException(status_code=400, detail=reason)
        
        # Delete person
        success = person_service.delete(person_id)
        if not success:
            raise HTTPException(status_code=500, detail="Errore durante l'eliminazione della persona")
        
        return RedirectResponse(url="/persons", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{person_id}/assignments", response_class=HTMLResponse)
async def person_assignments(
    request: Request,
    person_id: int,
    show_history: bool = False,
    person_service: PersonService = Depends(get_person_service),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Show assignments for person"""
    try:
        person = person_service.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        if show_history:
            assignments = assignment_service.get_assignments_by_person(person_id, current_only=False)
            page_title = f"Storico Incarichi: {person.name}"
        else:
            assignments = assignment_service.get_assignments_by_person(person_id, current_only=True)
            page_title = f"Incarichi Correnti: {person.name}"
        
        # Group assignments by unit and job title for better visualization
        grouped_assignments = {}
        for assignment in assignments:
            key = f"{assignment.unit_name} - {assignment.job_title_name}"
            if key not in grouped_assignments:
                grouped_assignments[key] = []
            grouped_assignments[key].append(assignment)
        
        return templates.TemplateResponse(
            "persons/assignments.html",
            {
                "request": request,
                "person": person,
                "assignments": assignments,
                "grouped_assignments": grouped_assignments,
                "show_history": show_history,
                "page_title": page_title,
                "page_icon": "person-badge",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": person.name, "url": f"/persons/{person_id}"},
                    {"name": "Storico Incarichi" if show_history else "Incarichi Correnti"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing assignments for person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{person_id}/timeline", response_class=HTMLResponse)
async def person_timeline(
    request: Request,
    person_id: int,
    person_service: PersonService = Depends(get_person_service),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Show person assignment timeline"""
    try:
        person = person_service.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        # Get all assignments for timeline
        all_assignments = assignment_service.get_assignments_by_person(person_id, current_only=False)
        
        # Create timeline data
        timeline_data = person_service.create_assignment_timeline(person_id, all_assignments)
        
        return templates.TemplateResponse(
            "persons/timeline.html",
            {
                "request": request,
                "person": person,
                "timeline_data": timeline_data,
                "page_title": f"Timeline: {person.name}",
                "page_icon": "clock-history",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": person.name, "url": f"/persons/{person_id}"},
                    {"name": "Timeline"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing timeline for person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{person_id}/profile", response_class=HTMLResponse)
async def person_profile(
    request: Request,
    person_id: int,
    person_service: PersonService = Depends(get_person_service),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Show person professional profile"""
    try:
        person = person_service.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        # Get current assignments
        current_assignments = assignment_service.get_assignments_by_person(person_id, current_only=True)
        
        # Get career progression
        career_progression = person_service.get_career_progression(person_id)
        
        # Get competency areas based on assignments
        competency_areas = person_service.get_competency_areas(person_id)
        
        # Get organizational relationships
        relationships = person_service.get_organizational_relationships(person_id)
        
        return templates.TemplateResponse(
            "persons/profile.html",
            {
                "request": request,
                "person": person,
                "current_assignments": current_assignments,
                "career_progression": career_progression,
                "competency_areas": competency_areas,
                "relationships": relationships,
                "page_title": f"Profilo: {person.name}",
                "page_icon": "person-vcard",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": person.name, "url": f"/persons/{person_id}"},
                    {"name": "Profilo"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing profile for person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{person_id}/workload", response_class=HTMLResponse)
async def person_workload(
    request: Request,
    person_id: int,
    person_service: PersonService = Depends(get_person_service),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Show person workload analysis"""
    try:
        person = person_service.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        # Get current assignments for workload calculation
        current_assignments = assignment_service.get_assignments_by_person(person_id, current_only=True)
        
        # Calculate workload metrics
        workload_analysis = person_service.calculate_workload(person_id, current_assignments)
        
        # Get workload history
        workload_history = person_service.get_workload_history(person_id)
        
        return templates.TemplateResponse(
            "persons/workload.html",
            {
                "request": request,
                "person": person,
                "current_assignments": current_assignments,
                "workload_analysis": workload_analysis,
                "workload_history": workload_history,
                "page_title": f"Carico di Lavoro: {person.name}",
                "page_icon": "speedometer2",
                "breadcrumb": [
                    {"name": "Persone", "url": "/persons"},
                    {"name": person.name, "url": f"/persons/{person_id}"},
                    {"name": "Carico di Lavoro"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing workload for person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{person_id}/merge")
async def merge_person(
    request: Request,
    person_id: int,
    target_person_id: int = Form(...),
    person_service: PersonService = Depends(get_person_service)
):
    """Merge person with another person (for duplicates)"""
    try:
        # Check if both persons exist
        source_person = person_service.get_by_id(person_id)
        target_person = person_service.get_by_id(target_person_id)
        
        if not source_person:
            raise HTTPException(status_code=404, detail="Persona sorgente non trovata")
        if not target_person:
            raise HTTPException(status_code=404, detail="Persona destinazione non trovata")
        
        if person_id == target_person_id:
            raise HTTPException(status_code=400, detail="Non è possibile unire una persona con se stessa")
        
        # Perform merge operation
        success = person_service.merge_persons(person_id, target_person_id)
        if not success:
            raise HTTPException(status_code=500, detail="Errore durante l'unione delle persone")
        
        return RedirectResponse(
            url=f"/persons/{target_person_id}",
            status_code=303
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging person {person_id} with {target_person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

