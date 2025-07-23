"""
Job Titles CRUD routes
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, List
import logging
from datetime import date
from app.services.job_title import JobTitleService
from app.services.unit import UnitService
from app.models.job_title import JobTitle
from app.models.base import Alias, ModelValidationException

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_job_title_service():
    return JobTitleService()


def get_unit_service():
    return UnitService()


@router.get("/", response_class=HTMLResponse)
async def list_job_titles(
    request: Request,
    search: Optional[str] = None,
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """List all job titles"""
    try:
        if search:
            job_titles = job_title_service.search(search, ['name', 'short_name'])
        else:
            job_titles = job_title_service.get_all()
        
        return templates.TemplateResponse(
            "job_titles/list.html",
            {
                "request": request,
                "job_titles": job_titles,
                "search": search or "",
                "page_title": "Ruoli Lavorativi",
                "page_icon": "briefcase"
            }
        )
    except Exception as e:
        logger.error(f"Error listing job titles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_title_id}", response_class=HTMLResponse)
async def job_title_detail(
    request: Request,
    job_title_id: int,
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Show job title details"""
    try:
        job_title = job_title_service.get_by_id(job_title_id)
        if not job_title:
            raise HTTPException(status_code=404, detail="Ruolo lavorativo non trovato")
        
        # Get assignable units
        assignable_units = job_title_service.get_assignable_units(job_title_id)
        
        # Get current assignments for this job title
        current_assignments = job_title_service.get_current_assignments(job_title_id)
        
        # Get assignment history
        assignment_history = job_title_service.get_assignment_history(job_title_id)
        
        return templates.TemplateResponse(
            "job_titles/detail.html",
            {
                "request": request,
                "job_title": job_title,
                "assignable_units": assignable_units,
                "current_assignments": current_assignments,
                "assignment_history": assignment_history,
                "page_title": f"Ruolo: {job_title.name}",
                "page_icon": "briefcase",
                "breadcrumb": [
                    {"name": "Ruoli", "url": "/job-titles"},
                    {"name": job_title.name}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing job title {job_title_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new", response_class=HTMLResponse)
async def create_job_title_form(
    request: Request,
    unit_service: UnitService = Depends(get_unit_service)
):
    """Show create job title form"""
    try:
        # Get all units for assignable units selection
        all_units = unit_service.get_all()
        
        return templates.TemplateResponse(
            "job_titles/create.html",
            {
                "request": request,
                "all_units": all_units,
                "page_title": "Nuovo Ruolo Lavorativo",
                "page_icon": "briefcase-plus",
                "breadcrumb": [
                    {"name": "Ruoli", "url": "/job-titles"},
                    {"name": "Nuovo Ruolo"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading create job title form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def create_job_title(
    request: Request,
    id: Optional[int] = Form(None),
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    alias_values: List[str] = Form([]),
    alias_langs: List[str] = Form([]),
    assignable_unit_ids: List[int] = Form([]),
    job_title_service: JobTitleService = Depends(get_job_title_service),
    unit_service: UnitService = Depends(get_unit_service)
):
    """Create new job title"""
    try:
        # Parse dates
        start_date_parsed = None
        if start_date:
            try:
                start_date_parsed = date.fromisoformat(start_date)
            except ValueError:
                pass
        
        end_date_parsed = None
        if end_date:
            try:
                end_date_parsed = date.fromisoformat(end_date)
            except ValueError:
                pass
        
        # Parse aliases
        aliases = []
        for i, value in enumerate(alias_values):
            if value.strip():
                lang = alias_langs[i] if i < len(alias_langs) and alias_langs[i] else "it-IT"
                aliases.append(Alias(value=value.strip(), lang=lang))
        
        # Create job title model
        job_title = JobTitle(
            id=id,
            name=name.strip(),
            short_name=short_name.strip() if short_name else None,
            start_date=start_date_parsed,
            end_date=end_date_parsed,
            aliases=aliases
        )
        
        # Create job title
        created_job_title = job_title_service.create(job_title)
        
        # Set assignable units
        if assignable_unit_ids:
            job_title_service.set_assignable_units(created_job_title.id, assignable_unit_ids)
        
        return RedirectResponse(
            url=f"/job-titles/{created_job_title.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        all_units = unit_service.get_all()
        form_data = await request.form()
        
        return templates.TemplateResponse(
            "job_titles/create.html",
            {
                "request": request,
                "all_units": all_units,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": form_data,
                "page_title": "Nuovo Ruolo Lavorativo",
                "page_icon": "briefcase-plus",
                "breadcrumb": [
                    {"name": "Ruoli", "url": "/job-titles"},
                    {"name": "Nuovo Ruolo"}
                ]
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating job title: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_title_id}/edit", response_class=HTMLResponse)
async def edit_job_title_form(
    request: Request,
    job_title_id: int,
    job_title_service: JobTitleService = Depends(get_job_title_service),
    unit_service: UnitService = Depends(get_unit_service)
):
    """Show edit job title form"""
    try:
        job_title = job_title_service.get_by_id(job_title_id)
        if not job_title:
            raise HTTPException(status_code=404, detail="Ruolo lavorativo non trovato")
        
        # Get all units for assignable units selection
        all_units = unit_service.get_all()
        
        # Get current assignable units
        assignable_units = job_title_service.get_assignable_units(job_title_id)
        assignable_unit_ids = [unit.id for unit in assignable_units]
        
        return templates.TemplateResponse(
            "job_titles/edit.html",
            {
                "request": request,
                "job_title": job_title,
                "all_units": all_units,
                "assignable_unit_ids": assignable_unit_ids,
                "page_title": f"Modifica Ruolo: {job_title.name}",
                "page_icon": "briefcase-gear",
                "breadcrumb": [
                    {"name": "Ruoli", "url": "/job-titles"},
                    {"name": job_title.name, "url": f"/job-titles/{job_title_id}"},
                    {"name": "Modifica"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading edit form for job title {job_title_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_title_id}/edit")
async def update_job_title(
    request: Request,
    job_title_id: int,
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    alias_values: List[str] = Form([]),
    alias_langs: List[str] = Form([]),
    assignable_unit_ids: List[int] = Form([]),
    job_title_service: JobTitleService = Depends(get_job_title_service),
    unit_service: UnitService = Depends(get_unit_service)
):
    """Update existing job title"""
    try:
        # Get existing job title
        existing_job_title = job_title_service.get_by_id(job_title_id)
        if not existing_job_title:
            raise HTTPException(status_code=404, detail="Ruolo lavorativo non trovato")
        
        # Parse dates
        start_date_parsed = None
        if start_date:
            try:
                start_date_parsed = date.fromisoformat(start_date)
            except ValueError:
                pass
        
        end_date_parsed = None
        if end_date:
            try:
                end_date_parsed = date.fromisoformat(end_date)
            except ValueError:
                pass
        
        # Parse aliases
        aliases = []
        for i, value in enumerate(alias_values):
            if value.strip():
                lang = alias_langs[i] if i < len(alias_langs) and alias_langs[i] else "it-IT"
                aliases.append(Alias(value=value.strip(), lang=lang))
        
        # Update job title model
        existing_job_title.name = name.strip()
        existing_job_title.short_name = short_name.strip() if short_name else None
        existing_job_title.start_date = start_date_parsed
        existing_job_title.end_date = end_date_parsed
        existing_job_title.aliases = aliases
        
        # Update job title
        updated_job_title = job_title_service.update(existing_job_title)
        
        # Update assignable units
        job_title_service.set_assignable_units(job_title_id, assignable_unit_ids)
        
        return RedirectResponse(
            url=f"/job-titles/{updated_job_title.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        job_title = job_title_service.get_by_id(job_title_id)
        all_units = unit_service.get_all()
        assignable_units = job_title_service.get_assignable_units(job_title_id)
        assignable_unit_ids = [unit.id for unit in assignable_units]
        form_data = await request.form()
        
        return templates.TemplateResponse(
            "job_titles/edit.html",
            {
                "request": request,
                "job_title": job_title,
                "all_units": all_units,
                "assignable_unit_ids": assignable_unit_ids,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": form_data,
                "page_title": f"Modifica Ruolo: {job_title.name}",
                "page_icon": "briefcase-gear",
                "breadcrumb": [
                    {"name": "Ruoli", "url": "/job-titles"},
                    {"name": job_title.name, "url": f"/job-titles/{job_title_id}"},
                    {"name": "Modifica"}
                ]
            },
            status_code=400
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job title {job_title_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_title_id}/delete")
async def delete_job_title(
    job_title_id: int,
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Delete job title"""
    try:
        # Check if job title can be deleted
        can_delete, reason = job_title_service.can_delete(job_title_id)
        if not can_delete:
            raise HTTPException(status_code=400, detail=reason)
        
        # Delete job title
        success = job_title_service.delete(job_title_id)
        if not success:
            raise HTTPException(status_code=500, detail="Errore durante l'eliminazione del ruolo")
        
        return RedirectResponse(url="/job-titles", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job title {job_title_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_title_id}/assignable-units", response_class=HTMLResponse)
async def manage_assignable_units(
    request: Request,
    job_title_id: int,
    job_title_service: JobTitleService = Depends(get_job_title_service),
    unit_service: UnitService = Depends(get_unit_service)
):
    """Manage assignable units for job title"""
    try:
        job_title = job_title_service.get_by_id(job_title_id)
        if not job_title:
            raise HTTPException(status_code=404, detail="Ruolo lavorativo non trovato")
        
        # Get all units
        all_units = unit_service.get_all()
        
        # Get current assignable units
        assignable_units = job_title_service.get_assignable_units(job_title_id)
        assignable_unit_ids = [unit.id for unit in assignable_units]
        
        return templates.TemplateResponse(
            "job_titles/assignable_units.html",
            {
                "request": request,
                "job_title": job_title,
                "all_units": all_units,
                "assignable_unit_ids": assignable_unit_ids,
                "page_title": f"Unità Assegnabili: {job_title.name}",
                "page_icon": "diagram-3",
                "breadcrumb": [
                    {"name": "Ruoli", "url": "/job-titles"},
                    {"name": job_title.name, "url": f"/job-titles/{job_title_id}"},
                    {"name": "Unità Assegnabili"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing assignable units for job title {job_title_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_title_id}/assignable-units")
async def update_assignable_units(
    job_title_id: int,
    assignable_unit_ids: List[int] = Form([]),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Update assignable units for job title"""
    try:
        # Check if job title exists
        job_title = job_title_service.get_by_id(job_title_id)
        if not job_title:
            raise HTTPException(status_code=404, detail="Ruolo lavorativo non trovato")
        
        # Update assignable units
        job_title_service.set_assignable_units(job_title_id, assignable_unit_ids)
        
        return RedirectResponse(
            url=f"/job-titles/{job_title_id}/assignable-units",
            status_code=303
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assignable units for job title {job_title_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_title_id}/assignments", response_class=HTMLResponse)
async def job_title_assignments(
    request: Request,
    job_title_id: int,
    show_history: bool = False,
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Show assignments for job title"""
    try:
        job_title = job_title_service.get_by_id(job_title_id)
        if not job_title:
            raise HTTPException(status_code=404, detail="Ruolo lavorativo non trovato")
        
        if show_history:
            assignments = job_title_service.get_assignment_history(job_title_id)
            page_title = f"Storico Incarichi: {job_title.name}"
        else:
            assignments = job_title_service.get_current_assignments(job_title_id)
            page_title = f"Incarichi Correnti: {job_title.name}"
        
        return templates.TemplateResponse(
            "job_titles/assignments.html",
            {
                "request": request,
                "job_title": job_title,
                "assignments": assignments,
                "show_history": show_history,
                "page_title": page_title,
                "page_icon": "person-badge",
                "breadcrumb": [
                    {"name": "Ruoli", "url": "/job-titles"},
                    {"name": job_title.name, "url": f"/job-titles/{job_title_id}"},
                    {"name": "Storico Incarichi" if show_history else "Incarichi Correnti"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing assignments for job title {job_title_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))