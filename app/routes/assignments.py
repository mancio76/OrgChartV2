"""
Assignments CRUD routes with versioning support
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, List
import logging
from datetime import date
from app.services.assignment import AssignmentService
from app.services.person import PersonService
from app.services.unit import UnitService
from app.services.job_title import JobTitleService
from app.models.assignment import Assignment
from app.models.base import ModelValidationException

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_assignment_service():
    return AssignmentService()


def get_person_service():
    return PersonService()


def get_unit_service():
    return UnitService()


def get_job_title_service():
    return JobTitleService()

@router.get("/", response_class=HTMLResponse)
async def list_assignments(
    request: Request,
    filter_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    person_id: Optional[int] = Query(None),
    unit_id: Optional[int] = Query(None),
    job_title_id: Optional[int] = Query(None),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    person_service: PersonService = Depends(get_person_service),
    unit_service: UnitService = Depends(get_unit_service),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """List assignments with filters"""
    try:
        # Get base assignments
        if filter_type == "history":
            assignments = assignment_service.get_full_history()
            page_title = "Storico Incarichi"
        else:
            assignments = assignment_service.get_current_assignments()
            page_title = "Incarichi Correnti"
        
        # Apply filters
        if person_id:
            assignments = [a for a in assignments if a.person_id == person_id]
        if unit_id:
            assignments = [a for a in assignments if a.unit_id == unit_id]
        if job_title_id:
            assignments = [a for a in assignments if a.job_title_id == job_title_id]
        
        # Apply additional filters
        if filter_type == "interim":
            assignments = [a for a in assignments if a.is_ad_interim]
            page_title = "Incarichi Ad Interim"
        elif filter_type == "overloaded":
            # Get persons with > 100% workload
            person_workloads = {}
            for assignment in assignments:
                if assignment.person_id not in person_workloads:
                    person_workloads[assignment.person_id] = 0
                person_workloads[assignment.person_id] += assignment.percentage
            overloaded_persons = [pid for pid, workload in person_workloads.items() if workload > 1.0]
            assignments = [a for a in assignments if a.person_id in overloaded_persons]
            page_title = "Persone Sovraccariche"
        
        # Apply search
        if search:
            search_lower = search.lower()
            assignments = [a for a in assignments if 
                         search_lower in a.person_name.lower() or
                         search_lower in a.unit_name.lower() or
                         search_lower in a.job_title_name.lower()]
        
        # Get filter options for dropdowns
        all_persons = person_service.get_all()
        all_units = unit_service.get_all()
        all_job_titles = job_title_service.get_all()
        
        # Calculate summary statistics
        stats = {
            'total_assignments': len(assignments),
            'interim_count': len([a for a in assignments if a.is_ad_interim]),
            'boss_count': len([a for a in assignments if a.is_unit_boss]),
            'unique_persons': len(set(a.person_id for a in assignments)),
            'unique_units': len(set(a.unit_id for a in assignments))
        }
        
        return templates.TemplateResponse(
            "assignments/list.html",
            {
                "request": request,
                "assignments": assignments,
                "all_persons": all_persons,
                "all_units": all_units,
                "all_job_titles": all_job_titles,
                "filter_type": filter_type or "",
                "search": search or "",
                "person_id": person_id,
                "unit_id": unit_id,
                "job_title_id": job_title_id,
                "stats": stats,
                "page_title": page_title,
                "page_icon": "person-badge"
            }
        )
    except Exception as e:
        logger.error(f"Error listing assignments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assignment_id}", response_class=HTMLResponse)
async def assignment_detail(
    request: Request,
    assignment_id: int,
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Show assignment details with version history"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Incarico non trovato")
        
        # Get version history for this assignment combination
        version_history = assignment_service.get_assignment_history(
            assignment.person_id, assignment.unit_id, assignment.job_title_id
        )
        
        # Get business rule validation warnings
        warnings = assignment_service.validate_assignment_rules(assignment)
        
        return templates.TemplateResponse(
            "assignments/detail.html",
            {
                "request": request,
                "assignment": assignment,
                "version_history": version_history,
                "warnings": warnings,
                "page_title": f"Incarico: {assignment.person_name} - {assignment.job_title_name}",
                "page_icon": "person-badge",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": f"{assignment.person_name} - {assignment.job_title_name}"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new", response_class=HTMLResponse)
async def create_assignment_form(
    request: Request,
    person_id: Optional[int] = Query(None),
    unit_id: Optional[int] = Query(None),
    job_title_id: Optional[int] = Query(None),
    person_service: PersonService = Depends(get_person_service),
    unit_service: UnitService = Depends(get_unit_service),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Show create assignment form"""
    try:
        # Get all options for dropdowns
        all_persons = person_service.get_all()
        all_units = unit_service.get_all()
        all_job_titles = job_title_service.get_all()
        
        # Pre-selected values
        selected_person = person_service.get_by_id(person_id) if person_id else None
        selected_unit = unit_service.get_by_id(unit_id) if unit_id else None
        selected_job_title = job_title_service.get_by_id(job_title_id) if job_title_id else None
        
        return templates.TemplateResponse(
            "assignments/create.html",
            {
                "request": request,
                "all_persons": all_persons,
                "all_units": all_units,
                "all_job_titles": all_job_titles,
                "selected_person": selected_person,
                "selected_unit": selected_unit,
                "selected_job_title": selected_job_title,
                "page_title": "Nuovo Incarico",
                "page_icon": "person-plus-fill",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": "Nuovo Incarico"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading create assignment form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def create_assignment(
    request: Request,
    person_id: int = Form(...),
    unit_id: int = Form(...),
    job_title_id: int = Form(...),
    percentage: float = Form(...),
    is_ad_interim: bool = Form(False),
    is_unit_boss: bool = Form(False),
    notes: Optional[str] = Form(None),
    flags: Optional[str] = Form(None),
    valid_from: Optional[str] = Form(None),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    person_service: PersonService = Depends(get_person_service),
    unit_service: UnitService = Depends(get_unit_service),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Create new assignment or new version"""
    try:
        # Parse date
        valid_from_parsed = None
        if valid_from:
            try:
                valid_from_parsed = date.fromisoformat(valid_from)
            except ValueError:
                pass
        
        # Create assignment model
        assignment = Assignment(
            person_id=person_id,
            unit_id=unit_id,
            job_title_id=job_title_id,
            percentage=percentage / 100.0,  # Convert percentage to decimal
            is_ad_interim=is_ad_interim,
            is_unit_boss=is_unit_boss,
            notes=notes.strip() if notes else None,
            flags=flags.strip() if flags else None,
            valid_from=valid_from_parsed,
            is_current=True
        )
        
        # Validate business rules and show warnings
        warnings = assignment_service.validate_assignment_rules(assignment)
        
        # Create assignment (will automatically version if needed)
        created_assignment = assignment_service.create_or_update_assignment(assignment)
        
        # Add success message with any warnings
        success_message = "Incarico creato con successo"
        if warnings:
            success_message += f" (Avvisi: {'; '.join(warnings)})"
        
        return RedirectResponse(
            url=f"/assignments/{created_assignment.id}?message={success_message}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        all_persons = person_service.get_all()
        all_units = unit_service.get_all()
        all_job_titles = job_title_service.get_all()
        form_data = await request.form()
        
        return templates.TemplateResponse(
            "assignments/create.html",
            {
                "request": request,
                "all_persons": all_persons,
                "all_units": all_units,
                "all_job_titles": all_job_titles,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": form_data,
                "page_title": "Nuovo Incarico",
                "page_icon": "person-plus-fill",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": "Nuovo Incarico"}
                ]
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assignment_id}/edit", response_class=HTMLResponse)
async def edit_assignment_form(
    request: Request,
    assignment_id: int,
    assignment_service: AssignmentService = Depends(get_assignment_service),
    person_service: PersonService = Depends(get_person_service),
    unit_service: UnitService = Depends(get_unit_service),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Show edit assignment form (creates new version)"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Incarico non trovato")
        
        # Get all options for dropdowns
        all_persons = person_service.get_all()
        all_units = unit_service.get_all()
        all_job_titles = job_title_service.get_all()
        
        # Get version history
        version_history = assignment_service.get_assignment_history(
            assignment.person_id, assignment.unit_id, assignment.job_title_id
        )
        
        return templates.TemplateResponse(
            "assignments/edit.html",
            {
                "request": request,
                "assignment": assignment,
                "all_persons": all_persons,
                "all_units": all_units,
                "all_job_titles": all_job_titles,
                "version_history": version_history,
                "page_title": f"Modifica Incarico: {assignment.person_name} - {assignment.job_title_name}",
                "page_icon": "person-gear",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": f"{assignment.person_name} - {assignment.job_title_name}", "url": f"/assignments/{assignment_id}"},
                    {"name": "Modifica"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading edit form for assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assignment_id}/edit")
async def update_assignment(
    request: Request,
    assignment_id: int,
    person_id: int = Form(...),
    unit_id: int = Form(...),
    job_title_id: int = Form(...),
    percentage: float = Form(...),
    is_ad_interim: bool = Form(False),
    is_unit_boss: bool = Form(False),
    notes: Optional[str] = Form(None),
    flags: Optional[str] = Form(None),
    valid_from: Optional[str] = Form(None),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    person_service: PersonService = Depends(get_person_service),
    unit_service: UnitService = Depends(get_unit_service),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Update assignment (creates new version)"""
    try:
        # Get existing assignment
        existing_assignment = assignment_service.get_by_id(assignment_id)
        if not existing_assignment:
            raise HTTPException(status_code=404, detail="Incarico non trovato")
        
        # Parse date
        valid_from_parsed = None
        if valid_from:
            try:
                valid_from_parsed = date.fromisoformat(valid_from)
            except ValueError:
                pass
        
        # Create new assignment (will create new version)
        new_assignment = Assignment(
            person_id=person_id,
            unit_id=unit_id,
            job_title_id=job_title_id,
            percentage=percentage / 100.0,  # Convert percentage to decimal
            is_ad_interim=is_ad_interim,
            is_unit_boss=is_unit_boss,
            notes=notes.strip() if notes else None,
            flags=flags.strip() if flags else None,
            valid_from=valid_from_parsed,
            is_current=True
        )
        
        # Create new version
        updated_assignment = assignment_service.create_or_update_assignment(new_assignment)
        
        return RedirectResponse(
            url=f"/assignments/{updated_assignment.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        assignment = assignment_service.get_by_id(assignment_id)
        all_persons = person_service.get_all()
        all_units = unit_service.get_all()
        all_job_titles = job_title_service.get_all()
        version_history = assignment_service.get_assignment_history(
            assignment.person_id, assignment.unit_id, assignment.job_title_id
        )
        form_data = await request.form()
        
        return templates.TemplateResponse(
            "assignments/edit.html",
            {
                "request": request,
                "assignment": assignment,
                "all_persons": all_persons,
                "all_units": all_units,
                "all_job_titles": all_job_titles,
                "version_history": version_history,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": form_data,
                "page_title": f"Modifica Incarico: {assignment.person_name} - {assignment.job_title_name}",
                "page_icon": "person-gear",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": f"{assignment.person_name} - {assignment.job_title_name}", "url": f"/assignments/{assignment_id}"},
                    {"name": "Modifica"}
                ]
            },
            status_code=400
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assignment_id}/terminate")
async def terminate_assignment(
    request: Request,
    assignment_id: int,
    termination_date: Optional[str] = Form(None),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Terminate an active assignment"""
    try:
        # Parse termination date
        termination_date_parsed = date.today()
        if termination_date:
            try:
                termination_date_parsed = date.fromisoformat(termination_date)
            except ValueError:
                pass
        
        # Terminate assignment
        success = assignment_service.terminate_assignment(assignment_id, termination_date_parsed)
        if not success:
            raise HTTPException(status_code=500, detail="Errore durante la terminazione dell'incarico")
        
        return RedirectResponse(
            url=f"/assignments/{assignment_id}",
            status_code=303
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error terminating assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assignment_id}/delete")
async def delete_assignment(
    assignment_id: int,
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Delete assignment version"""
    try:
        # Check if assignment can be deleted
        can_delete, reason = assignment_service.can_delete(assignment_id)
        if not can_delete:
            raise HTTPException(status_code=400, detail=reason)
        
        # Delete assignment
        success = assignment_service.delete(assignment_id)
        if not success:
            raise HTTPException(status_code=500, detail="Errore durante l'eliminazione dell'incarico")
        
        return RedirectResponse(url="/assignments", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_class=HTMLResponse)
async def assignment_history(
    request: Request,
    person_id: Optional[int] = Query(None),
    unit_id: Optional[int] = Query(None),
    job_title_id: Optional[int] = Query(None),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    person_service: PersonService = Depends(get_person_service),
    unit_service: UnitService = Depends(get_unit_service),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Show assignment history with filters"""
    try:
        # Get history based on filters
        if person_id and unit_id and job_title_id:
            history = assignment_service.get_assignment_history(person_id, unit_id, job_title_id)
            context_title = "Storico Versioni Incarico"
        else:
            history = assignment_service.get_full_history()
            context_title = "Storico Completo Incarichi"
        
        # Get filter options
        all_persons = person_service.get_all()
        all_units = unit_service.get_all()
        all_job_titles = job_title_service.get_all()
        
        # Group history by person+unit+job_title combination
        grouped_history = {}
        for assignment in history:
            key = f"{assignment.person_id}_{assignment.unit_id}_{assignment.job_title_id}"
            if key not in grouped_history:
                grouped_history[key] = {
                    'person_name': assignment.person_name,
                    'unit_name': assignment.unit_name,
                    'job_title_name': assignment.job_title_name,
                    'versions': []
                }
            grouped_history[key]['versions'].append(assignment)
        
        # Sort versions within each group
        for group in grouped_history.values():
            group['versions'].sort(key=lambda x: x.version, reverse=True)
        
        return templates.TemplateResponse(
            "assignments/history.html",
            {
                "request": request,
                "history": history,
                "grouped_history": grouped_history,
                "all_persons": all_persons,
                "all_units": all_units,
                "all_job_titles": all_job_titles,
                "person_id": person_id,
                "unit_id": unit_id,
                "job_title_id": job_title_id,
                "page_title": context_title,
                "page_icon": "clock-history",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": "Storico"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error showing assignment history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/workload", response_class=HTMLResponse)
async def workload_report(
    request: Request,
    assignment_service: AssignmentService = Depends(get_assignment_service),
    person_service: PersonService = Depends(get_person_service)
):
    """Show workload analysis report"""
    try:
        # Get current assignments
        current_assignments = assignment_service.get_current_assignments()
        
        # Calculate workload by person
        person_workloads = {}
        for assignment in current_assignments:
            person_id = assignment.person_id
            if person_id not in person_workloads:
                person_workloads[person_id] = {
                    'person_name': assignment.person_name,
                    'person_short_name': assignment.person_short_name,
                    'total_percentage': 0.0,
                    'assignments': [],
                    'interim_count': 0,
                    'units_count': 0
                }
            
            person_workloads[person_id]['total_percentage'] += assignment.percentage
            person_workloads[person_id]['assignments'].append(assignment)
            if assignment.is_ad_interim:
                person_workloads[person_id]['interim_count'] += 1
        
        # Count unique units per person
        for person_data in person_workloads.values():
            unique_units = set(a.unit_id for a in person_data['assignments'])
            person_data['units_count'] = len(unique_units)
        
        # Categorize workloads
        workload_categories = {
            'overloaded': [],  # > 120%
            'high': [],        # 100-120%
            'normal': [],      # 50-100%
            'low': []          # < 50%
        }
        
        for person_data in person_workloads.values():
            percentage = person_data['total_percentage']
            person_data['percentage_display'] = f"{percentage * 100:.0f}%"
            person_data['workload_color'] = 'success'
            
            if percentage > 1.2:
                workload_categories['overloaded'].append(person_data)
                person_data['workload_color'] = 'danger'
            elif percentage > 1.0:
                workload_categories['high'].append(person_data)
                person_data['workload_color'] = 'warning'
            elif percentage >= 0.5:
                workload_categories['normal'].append(person_data)
                person_data['workload_color'] = 'success'
            else:
                workload_categories['low'].append(person_data)
                person_data['workload_color'] = 'info'
        
        # Sort each category by percentage descending
        for category in workload_categories.values():
            category.sort(key=lambda x: x['total_percentage'], reverse=True)
        
        # Calculate statistics
        total_persons = len(person_workloads)
        avg_workload = sum(p['total_percentage'] for p in person_workloads.values()) / total_persons if total_persons > 0 else 0
        
        workload_stats = {
            'total_persons': total_persons,
            'avg_workload': f"{avg_workload * 100:.1f}%",
            'overloaded_count': len(workload_categories['overloaded']),
            'high_workload_count': len(workload_categories['high']),
            'normal_workload_count': len(workload_categories['normal']),
            'low_workload_count': len(workload_categories['low'])
        }
        
        return templates.TemplateResponse(
            "assignments/workload_report.html",
            {
                "request": request,
                "workload_categories": workload_categories,
                "workload_stats": workload_stats,
                "page_title": "Report Carico di Lavoro",
                "page_icon": "speedometer2",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": "Report Workload"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error generating workload report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/statistics", response_class=HTMLResponse)
async def assignment_statistics_report(
    request: Request,
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Show comprehensive assignment statistics"""
    try:
        # Get comprehensive statistics
        statistics = assignment_service.get_statistics()
        
        return templates.TemplateResponse(
            "assignments/statistics.html",
            {
                "request": request,
                "statistics": statistics,
                "page_title": "Statistiche Incarichi",
                "page_icon": "bar-chart",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": "Statistiche"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error generating assignment statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bulk/operations", response_class=HTMLResponse)
async def bulk_operations_form(
    request: Request,
    person_service: PersonService = Depends(get_person_service),
    unit_service: UnitService = Depends(get_unit_service),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Show bulk operations form"""
    try:
        # Get all options for bulk operations
        all_persons = person_service.get_all()
        all_units = unit_service.get_all()
        all_job_titles = job_title_service.get_all()
        
        return templates.TemplateResponse(
            "assignments/bulk_operations.html",
            {
                "request": request,
                "all_persons": all_persons,
                "all_units": all_units,
                "all_job_titles": all_job_titles,
                "page_title": "Operazioni in Blocco",
                "page_icon": "list-check",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": "Operazioni in Blocco"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading bulk operations form: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk/terminate")
async def bulk_terminate_assignments(
    request: Request,
    assignment_ids: List[int] = Form([]),
    termination_date: Optional[str] = Form(None),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Bulk terminate assignments"""
    try:
        if not assignment_ids:
            raise HTTPException(status_code=400, detail="Nessun incarico selezionato")
        
        # Parse termination date
        termination_date_parsed = date.today()
        if termination_date:
            try:
                termination_date_parsed = date.fromisoformat(termination_date)
            except ValueError:
                pass
        
        # Terminate each assignment
        success_count = 0
        for assignment_id in assignment_ids:
            if assignment_service.terminate_assignment(assignment_id, termination_date_parsed):
                success_count += 1
        
        return RedirectResponse(
            url=f"/assignments?message=Terminati {success_count} incarichi su {len(assignment_ids)}",
            status_code=303
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk terminating assignments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/update-percentage")
async def bulk_update_percentage(
    request: Request,
    assignment_ids: List[int] = Form([]),
    new_percentage: float = Form(...),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Bulk update assignment percentages"""
    try:
        if not assignment_ids:
            raise HTTPException(status_code=400, detail="Nessun incarico selezionato")
        
        if not (0 < new_percentage <= 100):
            raise HTTPException(status_code=400, detail="Percentuale deve essere tra 1 e 100")
        
        success_count = 0
        percentage_decimal = new_percentage / 100.0
        
        for assignment_id in assignment_ids:
            # Get existing assignment
            existing = assignment_service.get_by_id(assignment_id)
            if existing and existing.is_current:
                # Create new version with updated percentage
                new_assignment = Assignment(
                    person_id=existing.person_id,
                    unit_id=existing.unit_id,
                    job_title_id=existing.job_title_id,
                    percentage=percentage_decimal,
                    is_ad_interim=existing.is_ad_interim,
                    is_unit_boss=existing.is_unit_boss,
                    notes=existing.notes,
                    flags=existing.flags,
                    valid_from=date.today(),
                    is_current=True
                )
                
                if assignment_service.create_or_update_assignment(new_assignment):
                    success_count += 1
        
        return RedirectResponse(
            url=f"/assignments?message=Aggiornati {success_count} incarichi su {len(assignment_ids)}",
            status_code=303
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk updating percentages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/transfer")
async def bulk_transfer_assignments(
    request: Request,
    assignment_ids: List[int] = Form([]),
    target_unit_id: int = Form(...),
    transfer_date: Optional[str] = Form(None),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    unit_service: UnitService = Depends(get_unit_service)
):
    """Bulk transfer assignments to different unit"""
    try:
        if not assignment_ids:
            raise HTTPException(status_code=400, detail="Nessun incarico selezionato")
        
        # Verify target unit exists
        target_unit = unit_service.get_by_id(target_unit_id)
        if not target_unit:
            raise HTTPException(status_code=400, detail="Unità di destinazione non trovata")
        
        # Parse transfer date
        transfer_date_parsed = date.today()
        if transfer_date:
            try:
                transfer_date_parsed = date.fromisoformat(transfer_date)
            except ValueError:
                pass
        
        success_count = 0
        
        for assignment_id in assignment_ids:
            # Get existing assignment
            existing = assignment_service.get_by_id(assignment_id)
            if existing and existing.is_current:
                # Create new version with different unit
                new_assignment = Assignment(
                    person_id=existing.person_id,
                    unit_id=target_unit_id,
                    job_title_id=existing.job_title_id,
                    percentage=existing.percentage,
                    is_ad_interim=existing.is_ad_interim,
                    is_unit_boss=existing.is_unit_boss,
                    notes=f"Trasferito da {existing.unit_name}",
                    flags=existing.flags,
                    valid_from=transfer_date_parsed,
                    is_current=True
                )
                
                if assignment_service.create_or_update_assignment(new_assignment):
                    success_count += 1
        
        return RedirectResponse(
            url=f"/assignments?message=Trasferiti {success_count} incarichi su {len(assignment_ids)} verso {target_unit.name}",
            status_code=303
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk transferring assignments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate/{person_id}", response_class=HTMLResponse)
async def validate_person_assignments(
    request: Request,
    person_id: int,
    assignment_service: AssignmentService = Depends(get_assignment_service),
    person_service: PersonService = Depends(get_person_service)
):
    """Validate all assignments for a person"""
    try:
        person = person_service.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona non trovata")
        
        # Get current assignments
        current_assignments = assignment_service.get_assignments_by_person(person_id, current_only=True)
        
        # Validate each assignment
        validation_results = []
        for assignment in current_assignments:
            warnings = assignment_service.validate_assignment_rules(assignment)
            validation_results.append({
                'assignment': assignment,
                'warnings': warnings,
                'is_valid': len(warnings) == 0
            })
        
        # Calculate person workload
        person_stats = person_service.get_person_statistics(person_id)
        workload_analysis = person_service.calculate_workload(person_id, current_assignments)
        
        return templates.TemplateResponse(
            "assignments/validation.html",
            {
                "request": request,
                "person": person,
                "validation_results": validation_results,
                "person_stats": person_stats,
                "workload_analysis": workload_analysis,
                "page_title": f"Validazione Incarichi: {person.name}",
                "page_icon": "check-circle",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": person.name, "url": f"/persons/{person_id}"},
                    {"name": "Validazione"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating assignments for person {person_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts", response_class=HTMLResponse)
async def assignment_conflicts(
    request: Request,
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Show assignment conflicts and validation issues"""
    try:
        # Get all current assignments
        current_assignments = assignment_service.get_current_assignments()
        
        # Find conflicts
        conflicts = []
        person_assignments = {}
        
        # Group assignments by person
        for assignment in current_assignments:
            person_id = assignment.person_id
            if person_id not in person_assignments:
                person_assignments[person_id] = []
            person_assignments[person_id].append(assignment)
        
        # Check each person's assignments for conflicts
        for person_id, assignments in person_assignments.items():
            person_name = assignments[0].person_name
            total_percentage = sum(a.percentage for a in assignments)
            
            # Workload conflicts
            if total_percentage > 1.5:  # > 150%
                conflicts.append({
                    'type': 'overload',
                    'severity': 'high',
                    'person_id': person_id,
                    'person_name': person_name,
                    'description': f"Carico di lavoro eccessivo: {total_percentage*100:.0f}%",
                    'assignments': assignments
                })
            elif total_percentage > 1.2:  # > 120%
                conflicts.append({
                    'type': 'high_workload',
                    'severity': 'medium',
                    'person_id': person_id,
                    'person_name': person_name,
                    'description': f"Carico di lavoro elevato: {total_percentage*100:.0f}%",
                    'assignments': assignments
                })
            
            # Multiple interim assignments
            interim_count = sum(1 for a in assignments if a.is_ad_interim)
            if interim_count > 2:
                conflicts.append({
                    'type': 'multiple_interim',
                    'severity': 'medium',
                    'person_id': person_id,
                    'person_name': person_name,
                    'description': f"Troppi incarichi ad interim: {interim_count}",
                    'assignments': [a for a in assignments if a.is_ad_interim]
                })
            
            # Same unit multiple roles
            unit_roles = {}
            for assignment in assignments:
                unit_id = assignment.unit_id
                if unit_id not in unit_roles:
                    unit_roles[unit_id] = []
                unit_roles[unit_id].append(assignment)
            
            for unit_id, unit_assignments in unit_roles.items():
                if len(unit_assignments) > 1:
                    conflicts.append({
                        'type': 'multiple_roles_same_unit',
                        'severity': 'low',
                        'person_id': person_id,
                        'person_name': person_name,
                        'description': f"Ruoli multipli nella stessa unità: {unit_assignments[0].unit_name}",
                        'assignments': unit_assignments
                    })
        
        # Sort conflicts by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        conflicts.sort(key=lambda x: (severity_order[x['severity']], x['person_name']))
        
        # Statistics
        conflict_stats = {
            'total_conflicts': len(conflicts),
            'high_severity': len([c for c in conflicts if c['severity'] == 'high']),
            'medium_severity': len([c for c in conflicts if c['severity'] == 'medium']),
            'low_severity': len([c for c in conflicts if c['severity'] == 'low']),
            'affected_persons': len(set(c['person_id'] for c in conflicts))
        }
        
        return templates.TemplateResponse(
            "assignments/conflicts.html",
            {
                "request": request,
                "conflicts": conflicts,
                "conflict_stats": conflict_stats,
                "page_title": "Conflitti Incarichi",
                "page_icon": "exclamation-triangle",
                "breadcrumb": [
                    {"name": "Incarichi", "url": "/assignments"},
                    {"name": "Conflitti"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error checking assignment conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/csv")
async def export_assignments_csv(
    filter_type: Optional[str] = Query(None),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Export assignments to CSV"""
    try:
        from fastapi.responses import StreamingResponse
        import csv
        import io
        
        # Get assignments based on filter
        if filter_type == "history":
            assignments = assignment_service.get_full_history()
            filename = "storico_incarichi.csv"
        else:
            assignments = assignment_service.get_current_assignments()
            filename = "incarichi_correnti.csv"
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Persona', 'Unità', 'Ruolo', 'Percentuale', 'Ad Interim',
            'Data Inizio', 'Data Fine', 'Status', 'Versione', 'Note', 'Data Creazione'
        ])
        
        # Data rows
        for assignment in assignments:
            writer.writerow([
                assignment.id,
                assignment.person_name,
                assignment.unit_name,
                assignment.job_title_name,
                f"{assignment.percentage * 100:.0f}%",
                "Sì" if assignment.is_ad_interim else "No",
                assignment.valid_from.isoformat() if assignment.valid_from else "",
                assignment.valid_to.isoformat() if assignment.valid_to else "",
                assignment.status,
                assignment.version,
                assignment.notes or "",
                assignment.datetime_created.isoformat() if assignment.datetime_created else ""
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting assignments to CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))