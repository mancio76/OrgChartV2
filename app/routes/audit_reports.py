"""
Audit reports routes for import/export operations.

This module provides web interface routes for accessing audit reports,
operation history, and compliance information.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from ..services.audit_reporting import (
    get_audit_reporting_service, AuditReportingService, ReportPeriod
)
from ..services.audit_trail import get_audit_manager, OperationType, OperationStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def audit_dashboard(request: Request):
    """Display audit dashboard with overview of recent activities."""
    try:
        audit_reporting_service = get_audit_reporting_service()
        
        # Get recent operation summary
        operation_summary = audit_reporting_service.generate_operation_summary(
            period=ReportPeriod.LAST_WEEK
        )
        
        # Get recent data change summary
        data_change_summary = audit_reporting_service.generate_data_change_summary(
            period=ReportPeriod.LAST_WEEK
        )
        
        # Get recent failed operations
        audit_manager = get_audit_manager()
        failed_operations = audit_manager.get_operation_history(
            status=OperationStatus.FAILED,
            start_date=datetime.now() - timedelta(days=7),
            limit=10
        )
        
        return templates.TemplateResponse("audit/dashboard.html", {
            "request": request,
            "operation_summary": operation_summary,
            "data_change_summary": data_change_summary,
            "failed_operations": failed_operations,
            "page_title": "Audit Dashboard"
        })
    
    except Exception as e:
        logger.error(f"Error loading audit dashboard: {e}")
        raise HTTPException(status_code=500, detail="Errore nel caricamento della dashboard audit")


@router.get("/operations", response_class=HTMLResponse)
async def operation_history(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(50, description="Maximum number of operations to return")
):
    """Display operation history with filtering options."""
    try:
        audit_manager = get_audit_manager()
        
        # Convert string parameters to enums
        operation_type_enum = None
        if operation_type:
            try:
                operation_type_enum = OperationType(operation_type)
            except ValueError:
                pass
        
        status_enum = None
        if status:
            try:
                status_enum = OperationStatus(status)
            except ValueError:
                pass
        
        # Get operation history
        start_date = datetime.now() - timedelta(days=days)
        operations = audit_manager.get_operation_history(
            user_id=user_id,
            operation_type=operation_type_enum,
            status=status_enum,
            start_date=start_date,
            limit=limit
        )
        
        return templates.TemplateResponse("audit/operations.html", {
            "request": request,
            "operations": operations,
            "filters": {
                "user_id": user_id,
                "operation_type": operation_type,
                "status": status,
                "days": days,
                "limit": limit
            },
            "operation_types": [op_type.value for op_type in OperationType],
            "statuses": [status.value for status in OperationStatus],
            "page_title": "Operation History"
        })
    
    except Exception as e:
        logger.error(f"Error loading operation history: {e}")
        raise HTTPException(status_code=500, detail="Errore nel caricamento dello storico operazioni")


@router.get("/operations/{operation_id}", response_class=HTMLResponse)
async def operation_details(request: Request, operation_id: str):
    """Display detailed information about a specific operation."""
    try:
        audit_manager = get_audit_manager()
        
        # Get operation details
        operation = audit_manager.get_operation_details(operation_id)
        if not operation:
            raise HTTPException(status_code=404, detail="Operazione non trovata")
        
        return templates.TemplateResponse("audit/operation_details.html", {
            "request": request,
            "operation": operation,
            "page_title": f"Operation Details - {operation_id}"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading operation details for {operation_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore nel caricamento dei dettagli operazione")


@router.get("/reports/compliance", response_class=HTMLResponse)
async def compliance_report(
    request: Request,
    period: str = Query("last_month", description="Report period"),
    start_date: Optional[str] = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end date (YYYY-MM-DD)")
):
    """Generate and display compliance report."""
    try:
        audit_reporting_service = get_audit_reporting_service()
        
        # Parse period
        try:
            report_period = ReportPeriod(period)
        except ValueError:
            report_period = ReportPeriod.LAST_MONTH
        
        # Parse custom dates if provided
        custom_start_date = None
        custom_end_date = None
        
        if start_date:
            try:
                custom_start_date = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        if end_date:
            try:
                custom_end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Generate compliance report
        if report_period == ReportPeriod.CUSTOM and custom_start_date and custom_end_date:
            compliance_report = audit_reporting_service.generate_compliance_report(
                ReportPeriod.CUSTOM, custom_start_date, custom_end_date
            )
        else:
            compliance_report = audit_reporting_service.generate_compliance_report(report_period)
        
        return templates.TemplateResponse("audit/compliance_report.html", {
            "request": request,
            "report": compliance_report,
            "available_periods": [period.value for period in ReportPeriod],
            "selected_period": period,
            "page_title": "Compliance Report"
        })
    
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail="Errore nella generazione del report di compliance")


@router.get("/reports/user/{user_id}", response_class=HTMLResponse)
async def user_activity_report(
    request: Request,
    user_id: str,
    period: str = Query("last_month", description="Report period"),
    start_date: Optional[str] = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end date (YYYY-MM-DD)")
):
    """Generate and display user activity report."""
    try:
        audit_reporting_service = get_audit_reporting_service()
        
        # Parse period
        try:
            report_period = ReportPeriod(period)
        except ValueError:
            report_period = ReportPeriod.LAST_MONTH
        
        # Parse custom dates if provided
        custom_start_date = None
        custom_end_date = None
        
        if start_date:
            try:
                custom_start_date = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        if end_date:
            try:
                custom_end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Generate user activity report
        if report_period == ReportPeriod.CUSTOM and custom_start_date and custom_end_date:
            activity_report = audit_reporting_service.get_user_activity_report(
                user_id, ReportPeriod.CUSTOM, custom_start_date, custom_end_date
            )
        else:
            activity_report = audit_reporting_service.get_user_activity_report(
                user_id, report_period
            )
        
        return templates.TemplateResponse("audit/user_activity_report.html", {
            "request": request,
            "report": activity_report,
            "user_id": user_id,
            "available_periods": [period.value for period in ReportPeriod],
            "selected_period": period,
            "page_title": f"User Activity Report - {user_id}"
        })
    
    except Exception as e:
        logger.error(f"Error generating user activity report for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore nella generazione del report attività utente")


@router.get("/entities/{entity_type}/changes", response_class=HTMLResponse)
async def entity_change_history(
    request: Request,
    entity_type: str,
    entity_id: Optional[int] = Query(None, description="Specific entity ID"),
    limit: int = Query(100, description="Maximum number of changes to return")
):
    """Display change history for a specific entity type or entity."""
    try:
        audit_reporting_service = get_audit_reporting_service()
        
        # Get entity change history
        changes = audit_reporting_service.get_entity_change_history(
            entity_type, entity_id, limit
        )
        
        return templates.TemplateResponse("audit/entity_changes.html", {
            "request": request,
            "changes": changes,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "limit": limit,
            "page_title": f"Change History - {entity_type}"
        })
    
    except Exception as e:
        logger.error(f"Error loading entity change history for {entity_type}: {e}")
        raise HTTPException(status_code=500, detail="Errore nel caricamento dello storico modifiche")


# API endpoints for programmatic access

@router.get("/api/summary")
async def api_operation_summary(
    period: str = Query("last_week", description="Report period"),
    start_date: Optional[str] = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end date (YYYY-MM-DD)")
):
    """API endpoint to get operation summary."""
    try:
        audit_reporting_service = get_audit_reporting_service()
        
        # Parse period
        try:
            report_period = ReportPeriod(period)
        except ValueError:
            report_period = ReportPeriod.LAST_WEEK
        
        # Parse custom dates if provided
        custom_start_date = None
        custom_end_date = None
        
        if start_date:
            try:
                custom_start_date = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        if end_date:
            try:
                custom_end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Generate summary
        if report_period == ReportPeriod.CUSTOM and custom_start_date and custom_end_date:
            summary = audit_reporting_service.generate_operation_summary(
                ReportPeriod.CUSTOM, custom_start_date, custom_end_date
            )
        else:
            summary = audit_reporting_service.generate_operation_summary(report_period)
        
        return JSONResponse({
            "success": True,
            "data": {
                "total_operations": summary.total_operations,
                "successful_operations": summary.successful_operations,
                "failed_operations": summary.failed_operations,
                "success_rate": summary.success_rate,
                "failure_rate": summary.failure_rate,
                "total_records_processed": summary.total_records_processed,
                "total_records_created": summary.total_records_created,
                "total_records_updated": summary.total_records_updated,
                "average_duration": summary.average_duration,
                "operations_by_type": summary.operations_by_type,
                "operations_by_user": summary.operations_by_user
            }
        })
    
    except Exception as e:
        logger.error(f"Error in API operation summary: {e}")
        return JSONResponse({
            "success": False,
            "error": "Errore nella generazione del riepilogo operazioni"
        }, status_code=500)


@router.get("/api/operations/{operation_id}")
async def api_operation_details(operation_id: str):
    """API endpoint to get operation details."""
    try:
        audit_manager = get_audit_manager()
        
        # Get operation details
        operation = audit_manager.get_operation_details(operation_id)
        if not operation:
            return JSONResponse({
                "success": False,
                "error": "Operazione non trovata"
            }, status_code=404)
        
        return JSONResponse({
            "success": True,
            "data": operation
        })
    
    except Exception as e:
        logger.error(f"Error in API operation details for {operation_id}: {e}")
        return JSONResponse({
            "success": False,
            "error": "Errore nel recupero dei dettagli operazione"
        }, status_code=500)