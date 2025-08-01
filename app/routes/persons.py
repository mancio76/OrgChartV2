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
from app.security_csfr import generate_csrf_token, validate_csrf_token, validate_csrf_token_flexible, add_csrf_to_context
from app.services.base import ServiceValidationException

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_person_service():
    return PersonService()


def get_assignment_service():
    return AssignmentService()


def validate_and_clean_form_data(form_data: dict) -> dict:
    """Validate and clean form data for person creation/update"""
    cleaned_data = {}
    
    # Clean string fields
    string_fields = ['name', 'first_name', 'last_name', 'short_name', 'email', 'registration_no', 'profile_image']
    for field in string_fields:
        value = form_data.get(field)
        if value:
            cleaned_value = value.strip()
            cleaned_data[field] = cleaned_value if cleaned_value else None
        else:
            cleaned_data[field] = None
    
    return cleaned_data


def ensure_name_consistency(person_data: dict) -> dict:
    """Ensure consistency between name fields (Requirement 2.1)"""
    first_name = person_data.get('first_name')
    last_name = person_data.get('last_name')
    name = person_data.get('name')
    
    # If we have first_name/last_name but no name, generate it
    if (first_name or last_name) and not name:
        parts = [first_name, last_name]
        person_data['name'] = ' '.join(filter(None, parts))
    
    # If we have name but no first_name/last_name, try to split it
    elif name and not (first_name or last_name):
        parts = name.split()
        if len(parts) >= 2:
            person_data['first_name'] = parts[0]
            person_data['last_name'] = ' '.join(parts[1:])
        elif len(parts) == 1:
            person_data['first_name'] = parts[0]
    
    return person_data


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
    name: str = Form(""),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    short_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    registration_no: Optional[str] = Form(None),
    profile_image: Optional[str] = Form(None),
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    csrf_token: Optional[str] = Form(None),
    person_service: PersonService = Depends(get_person_service)
):
    """Create new person with enhanced field support (Requirements 1.1-1.5, 2.1-2.4, 6.1-6.2)"""
    logger.info("=== STARTING PERSON CREATION ===")
    logger.info(f"Request received - Name: {name}, First: {first_name}, Last: {last_name}, Email: {email}")

    try:
        # Prepare form data
        form_data = {
            'name': name,
            'first_name': first_name,
            'last_name': last_name,
            'short_name': short_name,
            'email': email,
            'registration_no': registration_no,
            'profile_image': profile_image
        }
        
        # Clean and validate form data
        cleaned_data = validate_and_clean_form_data(form_data)
        
        # Ensure name consistency (Requirement 2.1)
        cleaned_data = ensure_name_consistency(cleaned_data)
        
        # Create person model with enhanced fields
        person = Person(
            name=cleaned_data['name'] or "",
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name'],
            short_name=cleaned_data['short_name'],
            email=cleaned_data['email'],
            registration_no=cleaned_data['registration_no'],
            profile_image=cleaned_data['profile_image']
        )
        
        # Create person
        created_person = person_service.create(person)
        
        logger.info(f"Successfully created person with ID: {created_person.id}")
        logger.info(f"Person details - Name: {created_person.name}, First: {created_person.first_name}, Last: {created_person.last_name}")
        
        return RedirectResponse(
            url=f"/persons/{created_person.id}",
            status_code=303
        )
        
    except (ModelValidationException, ServiceValidationException) as e:
        # Show form again with errors
        if isinstance(e, ModelValidationException):
            errors = [{"field": err.field, "message": err.message} for err in e.errors]
        else:
            # ServiceValidationException - usually field-specific
            field_name = "registration_no" if "registration number" in str(e).lower() else "email" if "email" in str(e).lower() else "general"
            errors = [{"field": field_name, "message": str(e)}]
        
        return templates.TemplateResponse(
            "persons/create.html",
            {
                "request": request,
                "errors": errors,
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
    name: str = Form(""),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    short_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    registration_no: Optional[str] = Form(None),
    profile_image: Optional[str] = Form(None),
    person_service: PersonService = Depends(get_person_service)
):
    """Update existing person with enhanced field support (Requirements 1.1-1.5, 2.1-2.4, 6.1-6.2)"""
    try:
        # Get existing person
        existing_person = person_service.get_by_id(person_id)
        if not existing_person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        # Prepare form data
        form_data = {
            'name': name,
            'first_name': first_name,
            'last_name': last_name,
            'short_name': short_name,
            'email': email,
            'registration_no': registration_no,
            'profile_image': profile_image
        }
        
        # Clean and validate form data
        cleaned_data = validate_and_clean_form_data(form_data)
        
        # Ensure name consistency (Requirement 2.1)
        cleaned_data = ensure_name_consistency(cleaned_data)
        
        # Update person model with enhanced fields
        existing_person.name = cleaned_data['name'] or ""
        existing_person.first_name = cleaned_data['first_name']
        existing_person.last_name = cleaned_data['last_name']
        existing_person.short_name = cleaned_data['short_name']
        existing_person.email = cleaned_data['email']
        existing_person.registration_no = cleaned_data['registration_no']
        existing_person.profile_image = cleaned_data['profile_image']
        
        logger.info(f"Updating person {person_id} - Name: {existing_person.name}, First: {existing_person.first_name}, Last: {existing_person.last_name}")
        
        # Update person
        updated_person = person_service.update(existing_person)
        
        return RedirectResponse(
            url=f"/persons/{updated_person.id}",
            status_code=303
        )
        
    except (ModelValidationException, ServiceValidationException) as e:
        # Show form again with errors
        person = person_service.get_by_id(person_id)
        
        if isinstance(e, ModelValidationException):
            errors = [{"field": err.field, "message": err.message} for err in e.errors]
        else:
            # ServiceValidationException - usually field-specific
            field_name = "registration_no" if "registration number" in str(e).lower() else "email" if "email" in str(e).lower() else "general"
            errors = [{"field": field_name, "message": str(e)}]
        
        return templates.TemplateResponse(
            "persons/edit.html",
            {
                "request": request,
                "person": person,
                "errors": errors,
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


@router.post("/suggest-name-format")
async def suggest_name_format(
    request: Request,
    first_name: str = Form(""),
    last_name: str = Form(""),
    person_service: PersonService = Depends(get_person_service)
):
    """API endpoint to suggest name format from first_name and last_name (Requirement 2.1)"""
    try:
        # Create temporary person to use the suggestion method
        temp_person = Person(
            first_name=first_name.strip() if first_name else None,
            last_name=last_name.strip() if last_name else None
        )
        
        suggested_format = person_service.suggest_name_format(temp_person)
        
        return {
            "success": True,
            "suggested_format": suggested_format,
            "full_name": temp_person.suggest_name_from_parts()
        }
        
    except Exception as e:
        logger.error(f"Error suggesting name format: {e}")
        return {
            "success": False,
            "error": "Errore durante la generazione del formato nome"
        }


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

