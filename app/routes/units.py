"""
Units CRUD routes
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import logging
from datetime import date
from app.services.unit import UnitService
from app.services.unit_type import UnitTypeService
from app.models.unit import Unit
from app.models.base import Alias, ModelValidationException
from app.security import InputValidator, SecurityValidationError, get_client_ip, log_security_event

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_unit_service():
    return UnitService()


def get_unit_type_service():
    return UnitTypeService()


@router.get("/", response_class=HTMLResponse)
async def list_units(
    request: Request,
    search: Optional[str] = None,
    unit_service: UnitService = Depends(get_unit_service),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """List all units"""
    try:
        if search:
            units = unit_service.search(search, ['name', 'short_name'])
        else:
            units = unit_service.get_all()
        
        for unit in units:
            unit.unit_type = unit_type_service.get_by_id(unit.unit_type_id).name

        return templates.TemplateResponse(
            "units/list.html",
            {
                "request": request,
                "units": units,
                "search": search or "",
                "page_title": "Units"
            }
        )
    except Exception as e:
        logger.error(f"Error listing units: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{unit_id}", response_class=HTMLResponse)
async def unit_detail(
    request: Request,
    unit_id: int,
    unit_service: UnitService = Depends(get_unit_service),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Show unit details"""
    try:
        unit = unit_service.get_by_id(unit_id)

        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        
        type = unit_type_service.get_by_id(unit.unit_type_id)
        unit.unit_type = type.name;

        # Get children units
        children = unit_service.get_children(unit_id)
        
        # Get parent unit if exists
        parent = None
        if unit.parent_unit_id:
            parent = unit_service.get_by_id(unit.parent_unit_id)
        
        return templates.TemplateResponse(
            "units/detail.html",
            {
                "request": request,
                "unit": unit,
                #"type": type.name,
                #"unit_type": type.name,
                "children": children,
                "parent": parent,
                "page_title": f"Unit: {unit.name}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing unit {unit_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new", response_class=HTMLResponse)
async def create_unit_form(
    request: Request,
    unit_service: UnitService = Depends(get_unit_service),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Show create unit form"""
    try:
        # Get available parent units
        available_parents = unit_service.get_available_parents()
        
        # Get unit types
        unit_types = unit_type_service.get_all()
        
        return templates.TemplateResponse(
            "units/create.html",
            {
                "request": request,
                "available_parents": available_parents,
                "unit_types": unit_types,
                "page_title": "Create Unit"
            }
        )
    except Exception as e:
        logger.error(f"Error loading create unit form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def create_unit(
    request: Request,
    id: Optional[int] = Form(None),
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    unit_type_id: int = Form(...),
    parent_unit_id: Optional[int] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    unit_service: UnitService = Depends(get_unit_service),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Create new unit with security validation"""
    try:
        # Security validation
        form_data = {
            'name': name,
            'short_name': short_name,
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            sanitized_data = InputValidator.validate_and_sanitize_input(form_data)
        except SecurityValidationError as e:
            log_security_event('FORM_SECURITY_VIOLATION', {
                'form': 'create_unit',
                'errors': e.errors,
                'client_ip': get_client_ip(request)
            }, request)
            raise HTTPException(status_code=400, detail="Input non sicuro rilevato")
        
        # Additional validation
        if not InputValidator.validate_name(sanitized_data['name']):
            raise HTTPException(status_code=400, detail="Nome unità non valido")
        
        if sanitized_data['short_name'] and not InputValidator.validate_name(sanitized_data['short_name']):
            raise HTTPException(status_code=400, detail="Nome breve non valido")
        
        if not InputValidator.validate_id(unit_type_id):
            raise HTTPException(status_code=400, detail="Tipo unità non valido")
        
        if parent_unit_id is not None and not InputValidator.validate_id(parent_unit_id):
            raise HTTPException(status_code=400, detail="Unità padre non valida")
        
        # Parse dates
        start_date_parsed = None
        if sanitized_data['start_date']:
            try:
                start_date_parsed = date.fromisoformat(sanitized_data['start_date'])
            except ValueError:
                raise HTTPException(status_code=400, detail="Data inizio non valida")
        
        end_date_parsed = None
        if sanitized_data['end_date']:
            try:
                end_date_parsed = date.fromisoformat(sanitized_data['end_date'])
            except ValueError:
                raise HTTPException(status_code=400, detail="Data fine non valida")
        
        # Handle parent_unit_id
        if parent_unit_id == 0:
            parent_unit_id = None
        
        # Create unit model
        unit = Unit(
            id=id,
            name=sanitized_data['name'].strip(),
            short_name=sanitized_data['short_name'].strip() if sanitized_data['short_name'] else None,
            unit_type_id=unit_type_id,
            parent_unit_id=parent_unit_id,
            start_date=start_date_parsed,
            end_date=end_date_parsed
        )
        
        # Create unit
        created_unit = unit_service.create(unit)
        
        # Log successful creation
        log_security_event('UNIT_CREATED', {
            'unit_id': created_unit.id,
            'unit_name': created_unit.name,
            'client_ip': get_client_ip(request)
        }, request)
        
        return RedirectResponse(
            url=f"/units/{created_unit.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        available_parents = unit_service.get_available_parents()
        unit_types = unit_type_service.get_all()
        return templates.TemplateResponse(
            "units/create.html",
            {
                "request": request,
                "available_parents": available_parents,
                "unit_types": unit_types,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": await request.form(),
                "page_title": "Create Unit"
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating unit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{unit_id}/edit", response_class=HTMLResponse)
async def edit_unit_form(
    request: Request,
    unit_id: int,
    unit_service: UnitService = Depends(get_unit_service),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Show edit unit form"""
    try:
        unit = unit_service.get_by_id(unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        
        # Get available parent units (excluding self and descendants)
        available_parents = unit_service.get_available_parents(unit_id)
        
        # Get unit types
        unit_types = unit_type_service.get_all()
        
        return templates.TemplateResponse(
            "units/edit.html",
            {
                "request": request,
                "unit": unit,
                "available_parents": available_parents,
                "unit_types": unit_types,
                "page_title": f"Edit Unit: {unit.name}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading edit form for unit {unit_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{unit_id}/edit")
async def update_unit(
    request: Request,
    unit_id: int,
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    unit_type_id: int = Form(...),
    parent_unit_id: Optional[int] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    unit_service: UnitService = Depends(get_unit_service),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Update existing unit"""
    try:
        # Get existing unit
        existing_unit = unit_service.get_by_id(unit_id)
        if not existing_unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        
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
        
        # Handle parent_unit_id
        if parent_unit_id == 0:
            parent_unit_id = None
        
        # Update unit model
        existing_unit.name = name.strip()
        existing_unit.short_name = short_name.strip() if short_name else None
        existing_unit.unit_type_id = unit_type_id
        existing_unit.parent_unit_id = parent_unit_id
        existing_unit.start_date = start_date_parsed
        existing_unit.end_date = end_date_parsed
        
        # Update unit
        updated_unit = unit_service.update(existing_unit)
        
        return RedirectResponse(
            url=f"/units/{updated_unit.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        unit = unit_service.get_by_id(unit_id)
        available_parents = unit_service.get_available_parents(unit_id)
        unit_types = unit_type_service.get_all()
        return templates.TemplateResponse(
            "units/edit.html",
            {
                "request": request,
                "unit": unit,
                "available_parents": available_parents,
                "unit_types": unit_types,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": await request.form(),
                "page_title": f"Edit Unit: {unit.name}"
            },
            status_code=400
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating unit {unit_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{unit_id}/delete")
async def delete_unit(
    unit_id: int,
    unit_service: UnitService = Depends(get_unit_service)
):
    """Delete unit"""
    try:
        # Check if unit can be deleted
        can_delete, reason = unit_service.can_delete(unit_id)
        if not can_delete:
            raise HTTPException(status_code=400, detail=reason)
        
        # Delete unit
        success = unit_service.delete(unit_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete unit")
        
        return RedirectResponse(url="/units", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting unit {unit_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))