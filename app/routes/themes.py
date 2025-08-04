"""
Unit Type Theme management routes
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
import logging
import json

from app.services.unit_type_theme import UnitTypeThemeService
from app.services.unit_type import UnitTypeService
from app.models.unit_type_theme import UnitTypeTheme
from app.models.base import ModelValidationException
from app.security import InputValidator, SecurityValidationError, get_client_ip, log_security_event
from app.security_csfr import generate_csrf_token, validate_csrf_token_flexible

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_theme_service():
    return UnitTypeThemeService()


def get_unit_type_service():
    return UnitTypeService()


@router.get("/", response_class=HTMLResponse)
async def list_themes(
    request: Request,
    search: Optional[str] = None,
    csrf_token: str = Depends(generate_csrf_token),
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """List all themes with usage statistics and preview"""
    try:
        if search:
            themes = theme_service.search(search, ['name', 'description', 'display_label'])
        else:
            themes = theme_service.get_themes_with_usage_stats()
        
        # Get usage statistics
        usage_stats = theme_service.get_theme_usage_statistics()
        
        return templates.TemplateResponse(
            "themes/list.html",
            {
                "request": request,
                "themes": themes,
                "usage_stats": usage_stats,
                "search": search or "",
                "page_title": "Gestione Temi",
                "page_subtitle": "Personalizza l'aspetto dei tipi di unità",
                "csrf_token" : csrf_token
            }
        )
    except Exception as e:
        logger.error(f"Error listing themes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new", response_class=HTMLResponse)
async def create_theme_form(
    request: Request,
    csrf_token: str = Depends(generate_csrf_token)
):
    """Show create theme form with live preview"""
    try:
        context = {
            "request": request,
            "page_title": "Crea Nuovo Tema",
            "page_subtitle": "Definisci un nuovo tema per i tipi di unità",
            "breadcrumb": [
                {"name": "Temi", "url": "/themes"},
                {"name": "Nuovo Tema"}
            ],
            "csrf_token": csrf_token
        }

        return templates.TemplateResponse("themes/create.html", context)
    except Exception as e:
        logger.error(f"Error loading create theme form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def create_theme(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    icon_class: str = Form(...),
    emoji_fallback: str = Form(...),
    primary_color: str = Form(...),
    secondary_color: str = Form(...),
    text_color: str = Form(...),
    border_color: Optional[str] = Form(None),
    border_width: int = Form(...),
    border_style: str = Form(...),
    background_gradient: Optional[str] = Form(None),
    css_class_suffix: str = Form(...),
    hover_shadow_color: Optional[str] = Form(None),
    hover_shadow_intensity: float = Form(...),
    display_label: str = Form(...),
    display_label_plural: Optional[str] = Form(None),
    high_contrast_mode: bool = Form(False),
    is_active: bool = Form(True),
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Create new theme with validation"""
    try:
        # Security validation
        form_data = {
            'name': name,
            'description': description,
            'icon_class': icon_class,
            'emoji_fallback': emoji_fallback,
            'display_label': display_label,
            'display_label_plural': display_label_plural,
            'css_class_suffix': css_class_suffix,
            'background_gradient': background_gradient,
            'hover_shadow_color': hover_shadow_color
        }
        
        try:
            sanitized_data = InputValidator.validate_and_sanitize_input(form_data)
        except SecurityValidationError as e:
            log_security_event('FORM_SECURITY_VIOLATION', {
                'form': 'create_theme',
                'errors': e.errors,
                'client_ip': get_client_ip(request)
            }, request)
            raise HTTPException(status_code=400, detail="Input non sicuro rilevato")
        
        # Create theme model
        theme = UnitTypeTheme(
            name=sanitized_data['name'].strip(),
            description=sanitized_data['description'].strip() if sanitized_data['description'] else None,
            icon_class=sanitized_data['icon_class'].strip(),
            emoji_fallback=sanitized_data['emoji_fallback'].strip(),
            primary_color=primary_color.strip(),
            secondary_color=secondary_color.strip(),
            text_color=text_color.strip(),
            border_color=border_color.strip() if border_color else None,
            border_width=border_width,
            border_style=border_style.strip(),
            background_gradient=sanitized_data['background_gradient'].strip() if sanitized_data['background_gradient'] else None,
            css_class_suffix=sanitized_data['css_class_suffix'].strip(),
            hover_shadow_color=sanitized_data['hover_shadow_color'].strip() if sanitized_data['hover_shadow_color'] else None,
            hover_shadow_intensity=hover_shadow_intensity,
            display_label=sanitized_data['display_label'].strip(),
            display_label_plural=sanitized_data['display_label_plural'].strip() if sanitized_data['display_label_plural'] else None,
            high_contrast_mode=high_contrast_mode,
            is_active=is_active,
            created_by="system"  # TODO: Get from session/auth
        )
        
        # Create theme
        created_theme = theme_service.create(theme)
        
        # Log successful creation
        log_security_event('THEME_CREATED', {
            'theme_id': created_theme.id,
            'theme_name': created_theme.name,
            'client_ip': get_client_ip(request)
        }, request)
        
        return RedirectResponse(
            url=f"/themes/{created_theme.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        return templates.TemplateResponse(
            "themes/create.html",
            {
                "request": request,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": await request.form(),
                "page_title": "Crea Nuovo Tema"
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating theme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assign/unit-types", response_class=HTMLResponse)
async def theme_assignment_interface(
    request: Request,
    csrf_token: str = Depends(generate_csrf_token),
    theme_service: UnitTypeThemeService = Depends(get_theme_service),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Show theme assignment interface for unit types"""
    try:
        # Get all themes and unit types
        themes = theme_service.get_all()
        unit_types = unit_type_service.get_all()
        
        # Get current assignments
        assignments = {}
        for unit_type in unit_types:
            if unit_type.theme_id:
                assignments[unit_type.id] = unit_type.theme_id
        
        return templates.TemplateResponse(
            "themes/assign.html",
            {
                "request": request,
                "themes": themes,
                "unit_types": unit_types,
                "assignments": assignments,
                "page_title": "Assegnazione Temi",
                "page_subtitle": "Assegna temi ai tipi di unità",
                "breadcrumb": [
                    {"name": "Temi", "url": "/themes"},
                    {"name": "Assegnazione"}
                ],
                "csrf_token": csrf_token
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading theme assignment interface: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign/unit-types")
async def update_theme_assignments(
    request: Request,
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service),
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Update theme assignments for unit types with validation"""
    try:
        form_data = await request.form()
        
        # Process assignments with validation
        updated_count = 0
        validation_errors = []
        
        for key, value in form_data.items():
            if key.startswith("unit_type_") and key != "csrf_token":
                unit_type_id = int(key.replace("unit_type_", ""))
                theme_id = int(value) if value and value != "0" else None
                
                # Validate theme reference
                is_valid, theme, error_message = theme_service.validate_theme_reference(theme_id)
                if not is_valid:
                    validation_errors.append(f"Tipo unità {unit_type_id}: {error_message}")
                    continue
                
                # Get and update unit type
                unit_type = unit_type_service.get_by_id(unit_type_id)
                if unit_type:
                    unit_type.theme_id = theme_id
                    unit_type_service.update(unit_type)
                    updated_count += 1
        
        if validation_errors:
            # Return to form with errors
            themes = theme_service.get_all()
            unit_types = unit_type_service.get_all()
            assignments = {}
            for unit_type in unit_types:
                if unit_type.theme_id:
                    assignments[unit_type.id] = unit_type.theme_id
            
            return templates.TemplateResponse(
                "themes/assign.html",
                {
                    "request": request,
                    "themes": themes,
                    "unit_types": unit_types,
                    "assignments": assignments,
                    "errors": validation_errors,
                    "page_title": "Assegnazione Temi",
                    "page_subtitle": "Assegna temi ai tipi di unità",
                    "breadcrumb": [
                        {"name": "Temi", "url": "/themes"},
                        {"name": "Assegnazione"}
                    ]
                },
                status_code=400
            )
        
        # Log successful assignment update
        log_security_event('THEME_ASSIGNMENTS_UPDATED', {
            'updated_count': updated_count,
            'client_ip': get_client_ip(request)
        }, request)
        
        return RedirectResponse(url="/themes/assign/unit-types", status_code=303)
        
    except Exception as e:
        logger.error(f"Error updating theme assignments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/validate", response_class=JSONResponse)
async def validate_theme_data(
    request: Request,
    name: Optional[str] = None,
    css_class_suffix: Optional[str] = None,
    primary_color: Optional[str] = None,
    secondary_color: Optional[str] = None,
    text_color: Optional[str] = None,
    icon_class: Optional[str] = None,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for real-time theme validation"""
    try:
        validation_results = {}
        
        # Create a temporary theme for validation
        temp_theme = UnitTypeTheme(
            name=name or "",
            css_class_suffix=css_class_suffix or "",
            primary_color=primary_color or "#0dcaf0",
            secondary_color=secondary_color or "#f0fdff",
            text_color=text_color or "#0dcaf0",
            icon_class=icon_class or "diagram-2",
            display_label="Test"
        )
        
        # Validate individual fields
        if name:
            validation_results['name'] = {
                'valid': bool(name.strip() and len(name.strip()) <= 100),
                'message': 'Nome valido' if name.strip() and len(name.strip()) <= 100 else 'Nome non valido'
            }
            
            # Check uniqueness
            existing = theme_service.get_by_field("name", name.strip())
            if existing:
                validation_results['name']['valid'] = False
                validation_results['name']['message'] = 'Nome già esistente'
        
        if css_class_suffix:
            validation_results['css_class_suffix'] = {
                'valid': temp_theme._is_valid_css_class_suffix(css_class_suffix),
                'message': 'Suffisso CSS valido' if temp_theme._is_valid_css_class_suffix(css_class_suffix) else 'Suffisso CSS non valido'
            }
            
            # Check uniqueness
            existing = theme_service.get_by_field("css_class_suffix", css_class_suffix.strip())
            if existing:
                validation_results['css_class_suffix']['valid'] = False
                validation_results['css_class_suffix']['message'] = 'Suffisso CSS già esistente'
        
        if primary_color:
            validation_results['primary_color'] = {
                'valid': temp_theme._is_valid_color(primary_color),
                'message': 'Colore primario valido' if temp_theme._is_valid_color(primary_color) else 'Colore primario non valido'
            }
        
        if secondary_color:
            validation_results['secondary_color'] = {
                'valid': temp_theme._is_valid_color(secondary_color),
                'message': 'Colore secondario valido' if temp_theme._is_valid_color(secondary_color) else 'Colore secondario non valido'
            }
        
        if text_color:
            validation_results['text_color'] = {
                'valid': temp_theme._is_valid_color(text_color),
                'message': 'Colore testo valido' if temp_theme._is_valid_color(text_color) else 'Colore testo non valido'
            }
        
        if icon_class:
            validation_results['icon_class'] = {
                'valid': temp_theme._is_valid_icon_class(icon_class),
                'message': 'Classe icona valida' if temp_theme._is_valid_icon_class(icon_class) else 'Classe icona non valida'
            }
        
        # Color contrast validation
        if primary_color and text_color:
            try:
                primary_rgb = temp_theme._hex_to_rgb(primary_color)
                text_rgb = temp_theme._hex_to_rgb(text_color)
                
                if primary_rgb and text_rgb:
                    contrast_ratio = temp_theme._calculate_contrast_ratio(primary_rgb, text_rgb)
                    validation_results['color_contrast'] = {
                        'valid': contrast_ratio >= 3.0,
                        'ratio': round(contrast_ratio, 2),
                        'message': f'Contrasto {contrast_ratio:.2f}:1 {"(sufficiente)" if contrast_ratio >= 3.0 else "(insufficiente)"}'
                    }
            except Exception:
                validation_results['color_contrast'] = {
                    'valid': False,
                    'message': 'Impossibile calcolare il contrasto'
                }
        
        return JSONResponse(content={
            'success': True,
            'validation_results': validation_results
        })
        
    except Exception as e:
        logger.error(f"Error in theme validation API: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': str(e)
            },
            status_code=500
        )


@router.get("/analytics/dashboard", response_class=HTMLResponse)
async def theme_analytics_dashboard(
    request: Request,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Show comprehensive theme analytics dashboard"""
    try:
        # Get analytics data
        dashboard_data = theme_service.get_theme_analytics_dashboard()
        
        return templates.TemplateResponse(
            "themes/analytics_dashboard.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "page_title": "Dashboard Analisi Temi",
                "page_subtitle": "Panoramica completa dell'utilizzo e delle performance dei temi",
                "breadcrumb": [
                    {"name": "Temi", "url": "/themes"},
                    {"name": "Dashboard Analisi"}
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading theme analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/usage-report", response_class=HTMLResponse)
async def theme_usage_report(
    request: Request,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Show detailed theme usage report"""
    try:
        # Get usage report data
        usage_report = theme_service.get_most_least_used_themes_report()
        
        return templates.TemplateResponse(
            "themes/usage_report.html",
            {
                "request": request,
                "usage_report": usage_report,
                "page_title": "Report Utilizzo Temi",
                "page_subtitle": "Analisi dettagliata dell'utilizzo dei temi più e meno utilizzati",
                "breadcrumb": [
                    {"name": "Temi", "url": "/themes"},
                    {"name": "Report Utilizzo"}
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading theme usage report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/dashboard-data", response_class=JSONResponse)
async def get_dashboard_analytics_api(
    request: Request,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for dashboard analytics data (for AJAX updates)"""
    try:
        dashboard_data = theme_service.get_theme_analytics_dashboard()
        
        return JSONResponse(content={
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics API data: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': str(e)
            },
            status_code=500
        )


@router.get("/api/analytics/usage-stats", response_class=JSONResponse)
async def get_usage_statistics_api(
    request: Request,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for theme usage statistics"""
    try:
        usage_stats = theme_service.get_theme_usage_statistics()
        
        return JSONResponse(content={
            'success': True,
            'data': usage_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting usage statistics API data: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': str(e)
            },
            status_code=500
        )


@router.get("/api/analytics/{theme_id}/impact", response_class=JSONResponse)
async def get_theme_impact_api(
    request: Request,
    theme_id: int,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for theme impact analysis"""
    try:
        impact_analysis = theme_service.get_theme_impact_analysis(theme_id)
        
        return JSONResponse(content={
            'success': True,
            'data': impact_analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting theme impact API data for theme {theme_id}: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': str(e)
            },
            status_code=500
        )


@router.post("/api/performance-metrics", response_class=JSONResponse)
async def record_performance_metrics(
    request: Request,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for recording client-side performance metrics"""
    try:
        # Get metrics from request body
        metrics_data = await request.json()
        
        # Log performance metrics for monitoring
        logger.info(f"Theme performance metrics: {json.dumps(metrics_data, indent=2)}")
        
        # You could store these metrics in a database for analysis
        # For now, we just acknowledge receipt
        
        return JSONResponse(content={
            'success': True,
            'message': 'Performance metrics recorded'
        })
        
    except Exception as e:
        logger.error(f"Error recording performance metrics: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': 'Failed to record performance metrics'
            },
            status_code=500
        )


@router.get("/api/performance/metrics", response_class=JSONResponse)
async def get_performance_metrics(
    request: Request,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for getting server-side performance metrics"""
    try:
        metrics = theme_service.get_performance_metrics()
        
        return JSONResponse(content={
            'success': True,
            'data': metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': 'Failed to get performance metrics'
            },
            status_code=500
        )


@router.get("/api/accessibility/validate-contrast", response_class=JSONResponse)
async def validate_color_contrast(
    request: Request,
    primary_color: str,
    text_color: str,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for validating color contrast ratios"""
    try:
        # Create a temporary theme object for validation
        temp_theme = UnitTypeTheme(
            name="temp",
            primary_color=primary_color,
            text_color=text_color,
            display_label="temp"
        )
        
        # Get accessibility info which includes contrast validation
        accessibility_info = temp_theme.get_accessibility_info()
        
        return JSONResponse(content={
            'success': True,
            'data': {
                'contrast_ratios': accessibility_info.get('contrast_ratios', {}),
                'accessibility_score': accessibility_info.get('accessibility_score', 0),
                'recommendations': accessibility_info.get('recommendations', [])
            }
        })
        
    except Exception as e:
        logger.error(f"Error validating color contrast: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': 'Failed to validate color contrast'
            },
            status_code=500
        )


@router.post("/api/cache/invalidate", response_class=JSONResponse)
async def invalidate_css_cache(
    request: Request,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for manually invalidating CSS cache"""
    try:
        # Validate CSRF token for security
        form_data = await request.form()
        csrf_token = form_data.get('csrf_token')
        
        if not validate_csrf_token_flexible(csrf_token, request):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
        
        # Invalidate CSS cache
        theme_service.invalidate_css_cache()
        
        logger.info("CSS cache manually invalidated")
        
        return JSONResponse(content={
            'success': True,
            'message': 'CSS cache invalidated successfully'
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invalidating CSS cache: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': 'Failed to invalidate CSS cache'
            },
            status_code=500
        )


@router.get("/{theme_id}/edit", response_class=HTMLResponse)
async def edit_theme_form(
    request: Request,
    theme_id: int,
    csrf_token: str = Depends(generate_csrf_token),
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Show edit theme form with live preview"""
    try:
        theme = theme_service.get_by_id(theme_id)
        if not theme:
            raise HTTPException(status_code=404, detail="Tema non trovato")
        
        return templates.TemplateResponse(
            "themes/edit.html",
            {
                "request": request,
                "theme": theme,
                "page_title": f"Modifica Tema: {theme.name}",
                "breadcrumb": [
                    {"name": "Temi", "url": "/themes"},
                    {"name": theme.name, "url": f"/themes/{theme.id}"},
                    {"name": "Modifica"}
                ],
                "csrf_token": csrf_token
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading edit form for theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{theme_id}/edit")
async def update_theme(
    request: Request,
    theme_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    icon_class: str = Form(...),
    emoji_fallback: str = Form(...),
    primary_color: str = Form(...),
    secondary_color: str = Form(...),
    text_color: str = Form(...),
    border_color: Optional[str] = Form(None),
    border_width: int = Form(...),
    border_style: str = Form(...),
    background_gradient: Optional[str] = Form(None),
    css_class_suffix: str = Form(...),
    hover_shadow_color: Optional[str] = Form(None),
    hover_shadow_intensity: float = Form(...),
    display_label: str = Form(...),
    display_label_plural: Optional[str] = Form(None),
    high_contrast_mode: bool = Form(False),
    is_active: bool = Form(True),
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Update existing theme"""
    try:
        # Get existing theme
        existing_theme = theme_service.get_by_id(theme_id)
        if not existing_theme:
            raise HTTPException(status_code=404, detail="Tema non trovato")
        
        # Security validation
        form_data = {
            'name': name,
            'description': description,
            'icon_class': icon_class,
            'emoji_fallback': emoji_fallback,
            'display_label': display_label,
            'display_label_plural': display_label_plural,
            'css_class_suffix': css_class_suffix,
            'background_gradient': background_gradient,
            'hover_shadow_color': hover_shadow_color
        }
        
        try:
            sanitized_data = InputValidator.validate_and_sanitize_input(form_data)
        except SecurityValidationError as e:
            log_security_event('FORM_SECURITY_VIOLATION', {
                'form': 'update_theme',
                'errors': e.errors,
                'client_ip': get_client_ip(request)
            }, request)
            raise HTTPException(status_code=400, detail="Input non sicuro rilevato")
        
        # Update theme model
        existing_theme.name = sanitized_data['name'].strip()
        existing_theme.description = sanitized_data['description'].strip() if sanitized_data['description'] else None
        existing_theme.icon_class = sanitized_data['icon_class'].strip()
        existing_theme.emoji_fallback = sanitized_data['emoji_fallback'].strip()
        existing_theme.primary_color = primary_color.strip()
        existing_theme.secondary_color = secondary_color.strip()
        existing_theme.text_color = text_color.strip()
        existing_theme.border_color = border_color.strip() if border_color else None
        existing_theme.border_width = border_width
        existing_theme.border_style = border_style.strip()
        existing_theme.background_gradient = sanitized_data['background_gradient'].strip() if sanitized_data['background_gradient'] else None
        existing_theme.css_class_suffix = sanitized_data['css_class_suffix'].strip()
        existing_theme.hover_shadow_color = sanitized_data['hover_shadow_color'].strip() if sanitized_data['hover_shadow_color'] else None
        existing_theme.hover_shadow_intensity = hover_shadow_intensity
        existing_theme.display_label = sanitized_data['display_label'].strip()
        existing_theme.display_label_plural = sanitized_data['display_label_plural'].strip() if sanitized_data['display_label_plural'] else None
        existing_theme.high_contrast_mode = high_contrast_mode
        existing_theme.is_active = is_active
        
        # Update theme
        updated_theme = theme_service.update(existing_theme)
        
        # Log successful update
        log_security_event('THEME_UPDATED', {
            'theme_id': updated_theme.id,
            'theme_name': updated_theme.name,
            'client_ip': get_client_ip(request)
        }, request)
        
        return RedirectResponse(
            url=f"/themes/{updated_theme.id}",
            status_code=303
        )
        
    except ModelValidationException as e:
        # Show form again with errors
        theme = theme_service.get_by_id(theme_id)
        return templates.TemplateResponse(
            "themes/edit.html",
            {
                "request": request,
                "theme": theme,
                "errors": [{"field": err.field, "message": err.message} for err in e.errors],
                "form_data": await request.form(),
                "page_title": f"Modifica Tema: {theme.name}"
            },
            status_code=400
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{theme_id}/delete")
async def delete_theme(
    request: Request,
    theme_id: int,
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Delete theme"""
    try:
        # Check if theme can be deleted
        can_delete, reason = theme_service.can_delete_theme(theme_id)
        if not can_delete:
            raise HTTPException(status_code=400, detail=reason)
        
        # Get theme name for logging
        theme = theme_service.get_by_id(theme_id)
        theme_name = theme.name if theme else f"ID {theme_id}"
        
        # Delete theme
        success = theme_service.delete(theme_id)
        if not success:
            raise HTTPException(status_code=500, detail="Impossibile eliminare il tema")
        
        # Log successful deletion
        log_security_event('THEME_DELETED', {
            'theme_id': theme_id,
            'theme_name': theme_name,
            'client_ip': get_client_ip(request)
        }, request)
        
        return RedirectResponse(url="/themes", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{theme_id}/clone")
async def clone_theme(
    request: Request,
    theme_id: int,
    new_name: str = Form(...),
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Clone existing theme with new name"""
    try:
        # Security validation
        if not InputValidator.validate_name(new_name):
            raise HTTPException(status_code=400, detail="Nome tema non valido")
        
        # Clone theme
        cloned_theme = theme_service.clone_theme(
            theme_id=theme_id,
            new_name=new_name.strip(),
            created_by="system"  # TODO: Get from session/auth
        )
        
        # Log successful cloning
        log_security_event('THEME_CLONED', {
            'source_theme_id': theme_id,
            'new_theme_id': cloned_theme.id,
            'new_theme_name': cloned_theme.name,
            'client_ip': get_client_ip(request)
        }, request)
        
        return RedirectResponse(
            url=f"/themes/{cloned_theme.id}",
            status_code=303
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{theme_id}", response_class=HTMLResponse)
async def theme_detail(
    request: Request,
    theme_id: int,
    theme_service: UnitTypeThemeService = Depends(get_theme_service),
    unit_type_service: UnitTypeService = Depends(get_unit_type_service)
):
    """Show theme details with usage information"""
    try:
        theme = theme_service.get_by_id(theme_id)
        if not theme:
            raise HTTPException(status_code=404, detail="Tema non trovato")
        
        # Get unit types using this theme
        unit_types_using_theme = theme_service.get_unit_types_using_theme(theme_id)
        
        # Check if theme can be deleted
        can_delete, delete_reason = theme_service.can_delete_theme(theme_id)
        
        return templates.TemplateResponse(
            "themes/detail.html",
            {
                "request": request,
                "theme": theme,
                "unit_types_using_theme": unit_types_using_theme,
                "can_delete": can_delete,
                "delete_reason": delete_reason,
                "page_title": f"Tema: {theme.name}",
                "breadcrumb": [
                    {"name": "Temi", "url": "/themes"},
                    {"name": theme.name}
                ]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{theme_id}/preview", response_class=JSONResponse)
async def theme_preview(
    request: Request,
    theme_id: int,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Get theme preview data for live preview functionality"""
    try:
        theme = theme_service.get_by_id(theme_id)
        if not theme:
            raise HTTPException(status_code=404, detail="Tema non trovato")
        
        # Generate preview data
        preview_data = {
            "css_class_name": theme.generate_css_class_name(),
            "css_variables": theme.to_css_variables(),
            "css_rules": theme.generate_css_rules(),
            "theme_data": theme.to_dict()
        }
        
        return JSONResponse(content=preview_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview for theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{theme_id}/repair")
async def repair_theme_data(
    request: Request,
    theme_id: int,
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Repair corrupted theme data"""
    try:
        success, repair_actions = theme_service.repair_corrupted_theme_data(theme_id)
        
        if success:
            # Log successful repair
            log_security_event('THEME_REPAIRED', {
                'theme_id': theme_id,
                'repair_actions': repair_actions,
                'client_ip': get_client_ip(request)
            }, request)
            
            return RedirectResponse(
                url=f"/themes/{theme_id}?repaired=1",
                status_code=303
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Impossibile riparare il tema: {'; '.join(repair_actions)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error repairing theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{theme_id}/impact-analysis", response_class=HTMLResponse)
async def theme_impact_analysis(
    request: Request,
    theme_id: int,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """Show impact analysis for a specific theme"""
    try:
        # Get impact analysis data
        impact_analysis = theme_service.get_theme_impact_analysis(theme_id)
        
        return templates.TemplateResponse(
            "themes/impact_analysis.html",
            {
                "request": request,
                "impact_analysis": impact_analysis,
                "page_title": f"Analisi Impatto: {impact_analysis['theme']['name']}",
                "page_subtitle": "Analisi dell'impatto delle modifiche al tema",
                "breadcrumb": [
                    {"name": "Temi", "url": "/themes"},
                    {"name": impact_analysis['theme']['name'], "url": f"/themes/{theme_id}"},
                    {"name": "Analisi Impatto"}
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading impact analysis for theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{theme_id}/lazy", response_class=JSONResponse)
async def get_lazy_theme_data(
    request: Request,
    theme_id: int,
    theme_service: UnitTypeThemeService = Depends(get_theme_service)
):
    """API endpoint for lazy loading theme data"""
    try:
        # Get minimal theme data for lazy loading
        lazy_data = theme_service.get_lazy_theme_data([theme_id])
        
        if theme_id not in lazy_data:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        return JSONResponse(content={
            'success': True,
            'data': lazy_data[theme_id]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lazy theme data for theme {theme_id}: {e}")
        return JSONResponse(
            content={
                'success': False,
                'error': 'Failed to load theme data'
            },
            status_code=500
        )
