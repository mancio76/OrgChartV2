"""
Unit Types CRUD routes
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, List
import logging

from app.services.unit_type import UnitTypeService
from app.services.unit_type_theme import UnitTypeThemeService
from app.models.unit_type import UnitType
from app.models.base import Alias, ModelValidationException
from app.security import InputValidator, SecurityValidationError, get_client_ip, log_security_event
from app.security_csfr import generate_csrf_token, validate_csrf_token_flexible

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_unit_type_service():
    return UnitTypeService()


def get_unit_type_theme_service():
    return UnitTypeThemeService()


@router.get("/", response_class=HTMLResponse)
async def list_unit_types(
    request: Request,
    search: Optional[str] = None,
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """List all unit types with theme information"""
    try:
        if search:
            unit_types = unit_type_service.search(search, ['name', 'short_name'])
        else:
            unit_types = unit_type_service.get_all()

        return templates.TemplateResponse(
            "unit_types/list.html",
            {
                "request": request,
                "unit_types": unit_types,
                "search": search or "",
                "page_title": "Tipi di Unità"
            }
        )
    except Exception as e:
        logger.error(f"Error listing unit types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new", response_class=HTMLResponse)
async def create_unit_type_form(
    request: Request,
    csrf_token: str = Depends(generate_csrf_token),
    theme_service: UnitTypeThemeService = Depends(get_unit_type_theme_service)
):
    """Show create unit type form"""
    try:
        # Get available themes
        themes = theme_service.get_all()

        context = {
            "request": request,
            "themes": themes,
            "page_title": "Crea Tipo di Unità",
            "breadcrumb": [
                {"name": "Tipi di Unità", "url": "/unit_types"},
                {"name": "Nuovo Tipo"}
            ],
            "csrf_token": csrf_token
        }

        return templates.TemplateResponse("unit_types/create.html", context)
    except Exception as e:
        logger.error(f"Error loading create unit type form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def create_unit_type(
    request: Request,
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    theme_id: Optional[int] = Form(None),
    level: Optional[int] = Form(None),
    aliases: Optional[str] = Form(None),
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    csrf_token: Optional[str] = Form(None),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service),
    theme_service: UnitTypeThemeService = Depends(get_unit_type_theme_service)
):
    """Create new unit type with security validation"""
    try:
        # Security validation
        form_data = {
            'name': name,
            'short_name': short_name,
            'aliases': aliases
        }
        
        try:
            sanitized_data = InputValidator.validate_and_sanitize_input(form_data)
        except SecurityValidationError as e:
            log_security_event('FORM_SECURITY_VIOLATION', {
                'form': 'create_unit_type',
                'errors': e.errors,
                'client_ip': get_client_ip(request)
            }, request)
            raise HTTPException(status_code=400, detail="Input non sicuro rilevato")
        
        # Additional validation
        if not InputValidator.validate_name(sanitized_data['name']):
            raise HTTPException(status_code=400, detail="Nome tipo unità non valido")
        
        if sanitized_data['short_name'] and not InputValidator.validate_name(sanitized_data['short_name']):
            raise HTTPException(status_code=400, detail="Nome breve non valido")
        
        if theme_id is not None and not InputValidator.validate_id(theme_id):
            raise HTTPException(status_code=400, detail="Tema non valido")
        
        # Handle theme_id
        if theme_id == 0:
            theme_id = None
        
        # Parse aliases
        alias_list = []
        if sanitized_data['aliases']:
            # Simple parsing - each line is an alias
            for line in sanitized_data['aliases'].strip().split('\n'):
                line = line.strip()
                if line:
                    alias_list.append(Alias(value=line, lang="it-IT"))
        
        # Create unit type model
        unit_type = UnitType(
            name=sanitized_data['name'].strip(),
            short_name=sanitized_data['short_name'].strip() if sanitized_data['short_name'] else None,
            theme_id=theme_id,
            level=level,
            aliases=alias_list
        )
        
        # Create unit type
        created_unit_type = unit_type_service.create(unit_type)
        
        # Log successful creation
        log_security_event('UNIT_TYPE_CREATED', {
            'unit_type_id': created_unit_type.id,
            'unit_type_name': created_unit_type.name,
            'client_ip': get_client_ip(request)
        }, request)
        
        return RedirectResponse(
            url=f"/unit_types/{created_unit_type.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        themes = theme_service.get_all()
        return templates.TemplateResponse(
            "unit_types/create.html",
            {
                "request": request,
                "themes": themes,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": await request.form(),
                "page_title": "Crea Tipo di Unità"
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating unit type: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{unit_type_id}/edit", response_class=HTMLResponse)
async def edit_unit_type_form(
    request: Request,
    unit_type_id: int,
    unit_type_service: UnitTypeService = Depends(get_unit_type_service),
    theme_service: UnitTypeThemeService = Depends(get_unit_type_theme_service)
):
    """Show edit unit type form"""
    try:
        unit_type = unit_type_service.get_by_id(unit_type_id)
        if not unit_type:
            raise HTTPException(status_code=404, detail="Unit type not found")
        
        # Get available themes
        themes = theme_service.get_all()
        
        return templates.TemplateResponse(
            "unit_types/edit.html",
            {
                "request": request,
                "unit_type": unit_type,
                "themes": themes,
                "page_title": f"Modifica Tipo di Unità: {unit_type.name}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading edit form for unit type {unit_type_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{unit_type_id}/edit")
async def update_unit_type(
    request: Request,
    unit_type_id: int,
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    theme_id: Optional[int] = Form(None),
    level: Optional[int] = Form(None),
    aliases: Optional[str] = Form(None),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service),
    theme_service: UnitTypeThemeService = Depends(get_unit_type_theme_service)
):
    """Update existing unit type"""
    try:
        # Get existing unit type
        existing_unit_type = unit_type_service.get_by_id(unit_type_id)
        if not existing_unit_type:
            raise HTTPException(status_code=404, detail="Unit type not found")
        
        # Handle theme_id
        if theme_id == 0:
            theme_id = None
        
        # Parse aliases
        alias_list = []
        if aliases:
            # Simple parsing - each line is an alias
            for line in aliases.strip().split('\n'):
                line = line.strip()
                if line:
                    alias_list.append(Alias(value=line, lang="it-IT"))
        
        # Update unit type model
        existing_unit_type.name = name.strip()
        existing_unit_type.short_name = short_name.strip() if short_name else None
        existing_unit_type.theme_id = theme_id
        existing_unit_type.level = level
        existing_unit_type.aliases = alias_list
        
        # Update unit type
        updated_unit_type = unit_type_service.update(existing_unit_type)
        
        return RedirectResponse(
            url=f"/unit_types/{updated_unit_type.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        unit_type = unit_type_service.get_by_id(unit_type_id)
        themes = theme_service.get_all()
        return templates.TemplateResponse(
            "unit_types/edit.html",
            {
                "request": request,
                "unit_type": unit_type,
                "themes": themes,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": await request.form(),
                "page_title": f"Modifica Tipo di Unità: {unit_type.name}"
            },
            status_code=400
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating unit type {unit_type_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{unit_type_id}/delete")
async def delete_unit_type(
    unit_type_id: int,
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Delete unit type"""
    try:
        # Check if unit type can be deleted
        can_delete, reason = unit_type_service.can_delete(unit_type_id)
        if not can_delete:
            raise HTTPException(status_code=400, detail=reason)
        
        # Delete unit type
        success = unit_type_service.delete(unit_type_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete unit type")
        
        return RedirectResponse(url="/unit_types", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting unit type {unit_type_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{unit_type_id}", response_class=HTMLResponse)
async def unit_type_detail(
    request: Request,
    unit_type_id: int,
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Show unit type details"""
    try:
        unit_type = unit_type_service.get_by_id(unit_type_id)
        if not unit_type:
            raise HTTPException(status_code=404, detail="Unit type not found")
        
        # Get units using this type
        units = unit_type_service.get_units_by_type(unit_type_id)
        
        return templates.TemplateResponse(
            "unit_types/detail.html",
            {
                "request": request,
                "unit_type": unit_type,
                "units": units,
                "page_title": f"Tipo di Unità: {unit_type.name}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing unit type {unit_type_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))