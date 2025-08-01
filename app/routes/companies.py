"""
Companies CRUD routes
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from datetime import date
import logging
from app.services.company import CompanyService
from app.services.person import PersonService
from app.models.company import Company
from app.models.base import ModelValidationException
from app.services.base import ServiceValidationException
from app.security_csfr import generate_csrf_token, validate_csrf_token_flexible

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_company_service():
    return CompanyService()


def get_person_service():
    return PersonService()


def validate_and_clean_company_data(form_data: dict) -> dict:
    """Validate and clean form data for company creation/update"""
    cleaned_data = {}
    
    # Clean string fields
    string_fields = [
        'name', 'short_name', 'registration_no', 'address', 'city', 
        'postal_code', 'country', 'phone', 'email', 'website', 'notes'
    ]
    for field in string_fields:
        value = form_data.get(field)
        if value:
            cleaned_value = value.strip()
            cleaned_data[field] = cleaned_value if cleaned_value else None
        else:
            cleaned_data[field] = None
    
    # Handle integer fields
    int_fields = ['main_contact_id', 'financial_contact_id']
    for field in int_fields:
        value = form_data.get(field)
        if value and str(value).strip():
            try:
                cleaned_data[field] = int(value)
            except (ValueError, TypeError):
                cleaned_data[field] = None
        else:
            cleaned_data[field] = None
    
    # Handle date fields
    date_fields = ['valid_from', 'valid_to']
    for field in date_fields:
        value = form_data.get(field)
        if value and str(value).strip():
            try:
                cleaned_data[field] = date.fromisoformat(str(value))
            except (ValueError, TypeError):
                cleaned_data[field] = None
        else:
            cleaned_data[field] = None
    
    return cleaned_data


@router.get("/", response_class=HTMLResponse)
async def list_companies(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    company_service: CompanyService = Depends(get_company_service)
):
    """List all companies with optional filtering (Requirement 3.1)"""
    try:
        if search:
            companies = company_service.search_companies(search)
        elif status:
            companies = company_service.get_companies_by_status(status)
        else:
            companies = company_service.get_all()
        
        # Get statistics for the sidebar
        statistics = company_service.get_company_statistics()
        
        return templates.TemplateResponse(
            "companies/list.html",
            {
                "request": request,
                "companies": companies,
                "search": search or "",
                "status": status or "",
                "statistics": statistics,
                "page_title": "Aziende",
                "page_icon": "building"
            }
        )
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new", response_class=HTMLResponse)
async def create_company_form(
    request: Request,
    company_service: CompanyService = Depends(get_company_service),
    csrf_token: str = Depends(generate_csrf_token)
):
    """Show create company form (Requirement 3.1)"""
    try:
        # Get available contact persons (Requirement 3.6)
        contact_persons = company_service.get_contact_persons()
        
        context = {
            "request": request,
            "contact_persons": contact_persons,
            "page_title": "Nuova Azienda",
            "page_icon": "building-add",
            "breadcrumb": [
                {"name": "Aziende", "url": "/companies"},
                {"name": "Nuova Azienda"}
            ],
            "csrf_token": csrf_token
        }
        return templates.TemplateResponse("companies/create.html", context)
    except Exception as e:
        logger.error(f"Error loading create company form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def create_company(
    request: Request,
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    registration_no: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    country: str = Form("Italy"),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    main_contact_id: Optional[int] = Form(None),
    financial_contact_id: Optional[int] = Form(None),
    valid_from: Optional[str] = Form(None),
    valid_to: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    csrf_token: Optional[str] = Form(None),
    company_service: CompanyService = Depends(get_company_service)
):
    """Create new company (Requirements 3.1, 3.2, 3.3, 3.4, 3.5)"""
    logger.info("=== STARTING COMPANY CREATION ===")
    logger.info(f"Request received - Name: {name}, Registration: {registration_no}")

    try:
        # Prepare form data
        form_data = {
            'name': name,
            'short_name': short_name,
            'registration_no': registration_no,
            'address': address,
            'city': city,
            'postal_code': postal_code,
            'country': country,
            'phone': phone,
            'email': email,
            'website': website,
            'main_contact_id': main_contact_id,
            'financial_contact_id': financial_contact_id,
            'valid_from': valid_from,
            'valid_to': valid_to,
            'notes': notes
        }
        
        # Clean and validate form data
        cleaned_data = validate_and_clean_company_data(form_data)
        
        # Create company model
        company = Company(
            name=cleaned_data['name'],
            short_name=cleaned_data['short_name'],
            registration_no=cleaned_data['registration_no'],
            address=cleaned_data['address'],
            city=cleaned_data['city'],
            postal_code=cleaned_data['postal_code'],
            country=cleaned_data['country'] or "Italy",
            phone=cleaned_data['phone'],
            email=cleaned_data['email'],
            website=cleaned_data['website'],
            main_contact_id=cleaned_data['main_contact_id'],
            financial_contact_id=cleaned_data['financial_contact_id'],
            valid_from=cleaned_data['valid_from'],
            valid_to=cleaned_data['valid_to'],
            notes=cleaned_data['notes']
        )
        
        # Create company
        created_company = company_service.create(company)
        
        logger.info(f"Successfully created company with ID: {created_company.id}")
        
        return RedirectResponse(
            url=f"/companies/{created_company.id}",
            status_code=303
        )
        
    except (ModelValidationException, ServiceValidationException) as e:
        # Show form again with errors
        contact_persons = company_service.get_contact_persons()
        
        if isinstance(e, ModelValidationException):
            errors = [{"field": err.field, "message": err.message} for err in e.errors]
        else:
            # ServiceValidationException - usually field-specific
            field_name = "registration_no" if "registration number" in str(e).lower() else "main_contact_id" if "contact" in str(e).lower() else "general"
            errors = [{"field": field_name, "message": str(e)}]
        
        return templates.TemplateResponse(
            "companies/create.html",
            {
                "request": request,
                "contact_persons": contact_persons,
                "errors": errors,
                "form_data": await request.form(),
                "page_title": "Nuova Azienda",
                "page_icon": "building-add",
                "breadcrumb": [
                    {"name": "Aziende", "url": "/companies"},
                    {"name": "Nuova Azienda"}
                ]
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}", response_class=HTMLResponse)
async def company_detail(
    request: Request,
    company_id: int,
    company_service: CompanyService = Depends(get_company_service)
):
    """Show company details (Requirement 3.8)"""
    try:
        company = company_service.get_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Azienda non trovata")
        
        return templates.TemplateResponse(
            "companies/detail.html",
            {
                "request": request,
                "company": company,
                "page_title": f"Azienda: {company.name}",
                "page_icon": "building",
                "breadcrumb": [
                    {"name": "Aziende", "url": "/companies"},
                    {"name": company.name}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/edit", response_class=HTMLResponse)
async def edit_company_form(
    request: Request,
    company_id: int,
    company_service: CompanyService = Depends(get_company_service)
):
    """Show edit company form (Requirement 3.1)"""
    try:
        company = company_service.get_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Azienda non trovata")
        
        # Get available contact persons (Requirement 3.6)
        contact_persons = company_service.get_contact_persons()
        
        return templates.TemplateResponse(
            "companies/edit.html",
            {
                "request": request,
                "company": company,
                "contact_persons": contact_persons,
                "page_title": f"Modifica Azienda: {company.name}",
                "page_icon": "building-gear",
                "breadcrumb": [
                    {"name": "Aziende", "url": "/companies"},
                    {"name": company.name, "url": f"/companies/{company_id}"},
                    {"name": "Modifica"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading edit form for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{company_id}/edit")
async def update_company(
    request: Request,
    company_id: int,
    name: str = Form(...),
    short_name: Optional[str] = Form(None),
    registration_no: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    country: str = Form("Italy"),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    main_contact_id: Optional[int] = Form(None),
    financial_contact_id: Optional[int] = Form(None),
    valid_from: Optional[str] = Form(None),
    valid_to: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    company_service: CompanyService = Depends(get_company_service)
):
    """Update existing company (Requirements 3.1, 3.2, 3.3, 3.4, 3.5)"""
    try:
        # Get existing company
        existing_company = company_service.get_by_id(company_id)
        if not existing_company:
            raise HTTPException(status_code=404, detail="Azienda non trovata")
        
        # Prepare form data
        form_data = {
            'name': name,
            'short_name': short_name,
            'registration_no': registration_no,
            'address': address,
            'city': city,
            'postal_code': postal_code,
            'country': country,
            'phone': phone,
            'email': email,
            'website': website,
            'main_contact_id': main_contact_id,
            'financial_contact_id': financial_contact_id,
            'valid_from': valid_from,
            'valid_to': valid_to,
            'notes': notes
        }
        
        # Clean and validate form data
        cleaned_data = validate_and_clean_company_data(form_data)
        
        # Update company model
        existing_company.name = cleaned_data['name']
        existing_company.short_name = cleaned_data['short_name']
        existing_company.registration_no = cleaned_data['registration_no']
        existing_company.address = cleaned_data['address']
        existing_company.city = cleaned_data['city']
        existing_company.postal_code = cleaned_data['postal_code']
        existing_company.country = cleaned_data['country'] or "Italy"
        existing_company.phone = cleaned_data['phone']
        existing_company.email = cleaned_data['email']
        existing_company.website = cleaned_data['website']
        existing_company.main_contact_id = cleaned_data['main_contact_id']
        existing_company.financial_contact_id = cleaned_data['financial_contact_id']
        existing_company.valid_from = cleaned_data['valid_from']
        existing_company.valid_to = cleaned_data['valid_to']
        existing_company.notes = cleaned_data['notes']
        
        logger.info(f"Updating company {company_id} - Name: {existing_company.name}")
        
        # Update company
        updated_company = company_service.update(existing_company)
        
        return RedirectResponse(
            url=f"/companies/{updated_company.id}",
            status_code=303
        )
        
    except (ModelValidationException, ServiceValidationException) as e:
        # Show form again with errors
        company = company_service.get_by_id(company_id)
        contact_persons = company_service.get_contact_persons()
        
        if isinstance(e, ModelValidationException):
            errors = [{"field": err.field, "message": err.message} for err in e.errors]
        else:
            # ServiceValidationException - usually field-specific
            field_name = "registration_no" if "registration number" in str(e).lower() else "main_contact_id" if "contact" in str(e).lower() else "general"
            errors = [{"field": field_name, "message": str(e)}]
        
        return templates.TemplateResponse(
            "companies/edit.html",
            {
                "request": request,
                "company": company,
                "contact_persons": contact_persons,
                "errors": errors,
                "form_data": await request.form(),
                "page_title": f"Modifica Azienda: {company.name}",
                "page_icon": "building-gear",
                "breadcrumb": [
                    {"name": "Aziende", "url": "/companies"},
                    {"name": company.name, "url": f"/companies/{company_id}"},
                    {"name": "Modifica"}
                ]
            },
            status_code=400
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{company_id}/delete")
async def delete_company(
    company_id: int,
    company_service: CompanyService = Depends(get_company_service)
):
    """Delete company (Requirements 3.1, 3.7)"""
    try:
        # Check if company can be deleted
        can_delete, reason = company_service.can_delete(company_id)
        if not can_delete:
            raise HTTPException(status_code=400, detail=reason)
        
        # Delete company
        success = company_service.delete(company_id)
        if not success:
            raise HTTPException(status_code=500, detail="Errore durante l'eliminazione dell'azienda")
        
        return RedirectResponse(url="/companies", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/statistics", response_class=HTMLResponse)
async def company_statistics_report(
    request: Request,
    company_service: CompanyService = Depends(get_company_service)
):
    """Show company statistics report"""
    try:
        # Get comprehensive statistics
        statistics = company_service.get_company_statistics()
        
        return templates.TemplateResponse(
            "companies/statistics.html",
            {
                "request": request,
                "statistics": statistics,
                "page_title": "Statistiche Aziende",
                "page_icon": "bar-chart",
                "breadcrumb": [
                    {"name": "Aziende", "url": "/companies"},
                    {"name": "Statistiche"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error generating company statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiring", response_class=HTMLResponse)
async def companies_expiring_soon(
    request: Request,
    days: int = 30,
    company_service: CompanyService = Depends(get_company_service)
):
    """Show companies expiring soon"""
    try:
        companies = company_service.get_companies_expiring_soon(days)
        
        return templates.TemplateResponse(
            "companies/expiring.html",
            {
                "request": request,
                "companies": companies,
                "days": days,
                "page_title": f"Aziende in Scadenza ({days} giorni)",
                "page_icon": "clock",
                "breadcrumb": [
                    {"name": "Aziende", "url": "/companies"},
                    {"name": "In Scadenza"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error fetching expiring companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_class=HTMLResponse)
async def list_active_companies(
    request: Request,
    company_service: CompanyService = Depends(get_company_service)
):
    """List only active companies (Requirement 3.1)"""
    try:
        companies = company_service.get_active_companies()
        
        # Get statistics for the sidebar
        statistics = company_service.get_company_statistics()
        
        return templates.TemplateResponse(
            "companies/list.html",
            {
                "request": request,
                "companies": companies,
                "search": "",
                "status": "active",
                "statistics": statistics,
                "page_title": "Aziende Attive",
                "page_icon": "check-circle",
                "breadcrumb": [
                    {"name": "Aziende", "url": "/companies"},
                    {"name": "Attive"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error listing active companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/contact-persons", response_class=HTMLResponse)
async def get_contact_persons_api(
    request: Request,
    company_service: CompanyService = Depends(get_company_service)
):
    """API endpoint to get available contact persons (Requirement 3.6)"""
    try:
        contact_persons = company_service.get_contact_persons()
        
        return {
            "success": True,
            "contact_persons": contact_persons
        }
        
    except Exception as e:
        logger.error(f"Error fetching contact persons: {e}")
        return {
            "success": False,
            "error": "Errore durante il recupero dei contatti"
        }