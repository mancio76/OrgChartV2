"""
Orgchart visualization and analysis routes
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, Dict, Any, List
import logging
from app.services.orgchart import OrgchartService
from app.services.unit import UnitService
from app.services.assignment import AssignmentService
from app.services.person import PersonService
from app.templates import templates

logger = logging.getLogger(__name__)
router = APIRouter()


def get_orgchart_service():
    return OrgchartService()


def get_unit_service():
    return UnitService()


def get_assignment_service():
    return AssignmentService()


def get_person_service():
    return PersonService()


@router.get("/", response_class=HTMLResponse)
async def orgchart_home(
    request: Request,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Orgchart homepage with overview"""
    try:
        # Get organization overview
        overview = orgchart_service.get_organization_overview()
        
        # Get key metrics
        metrics = orgchart_service.get_organization_metrics()
        
        # Get recent changes
        recent_changes = orgchart_service.get_recent_organizational_changes(limit=10)
        
        return templates.TemplateResponse(
            "orgchart/overview.html",
            {
                "request": request,
                "overview": overview,
                "metrics": metrics,
                "recent_changes": recent_changes,
                "page_title": "Organigramma",
                "page_icon": "diagram-3"
            }
        )
    except Exception as e:
        logger.error(f"Error loading orgchart home: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tree", response_class=HTMLResponse)
async def orgchart_tree(
    request: Request,
    unit_id: Optional[int] = Query(None),
    expand_all: bool = Query(False),
    show_persons: bool = Query(True),
    show_vacant: bool = Query(True),
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Interactive orgchart tree visualization"""
    try:
        # Get tree structure
        if unit_id:
            tree_data = orgchart_service.get_subtree(unit_id, show_persons=show_persons)
            root_unit = orgchart_service.get_unit_with_details(unit_id)
        else:
            tree_data = orgchart_service.get_complete_tree(show_persons=show_persons)
            root_unit = None
        
        # Get units without assignments (vacant positions)
        vacant_positions = orgchart_service.get_vacant_positions() if show_vacant else []
        
        # Get tree statistics
        tree_stats = orgchart_service.calculate_tree_statistics(tree_data)
        
        # Get navigation breadcrumb for subtree
        breadcrumb_path = []
        if unit_id and root_unit:
            breadcrumb_path = orgchart_service.get_unit_path(unit_id)
        
        breadcrumb = [
            {
                "name": "Organigramma", 
                "url": "/orgchart"
            }
        ]

        if breadcrumb_path and len(breadcrumb_path) > 0:
            breadcrumb.extend([
                {
                    "name": item['name']
                    , "url": f"/orgchart/tree?unit_id={item['id']}"
                } for item in breadcrumb_path
            ])

        return templates.TemplateResponse(
            "orgchart/tree.html",
            {
                "request": request,
                "tree_data": tree_data,
                "root_unit": root_unit,
                "vacant_positions": vacant_positions,
                "tree_stats": tree_stats,
                "breadcrumb_path": breadcrumb_path,
                "unit_id": unit_id,
                "expand_all": expand_all,
                "show_persons": show_persons,
                "show_vacant": show_vacant,
                "page_title": f"Organigramma {'- ' + root_unit['name'] if root_unit else ''}",
                "page_icon": "diagram-3",
                "breadcrumb": breadcrumb
            }
        )
    except Exception as e:
        logger.error(f"Error loading orgchart tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unit/{unit_id}", response_class=HTMLResponse)
async def orgchart_unit_detail(
    request: Request,
    unit_id: int,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Detailed view of organizational unit in context"""
    try:
        # Get unit with full organizational context
        unit_detail = orgchart_service.get_unit_organizational_context(unit_id)
        if not unit_detail:
            raise HTTPException(status_code=404, detail="Unità non trovata")
        
        # Get unit performance metrics
        performance_metrics = orgchart_service.get_unit_performance_metrics(unit_id)
        
        # Get reporting relationships
        reporting_structure = orgchart_service.get_reporting_relationships(unit_id)
        
        # Get unit change history
        change_history = orgchart_service.get_unit_change_history(unit_id, limit=20)
        
        return templates.TemplateResponse(
            "orgchart/unit_detail.html",
            {
                "request": request,
                "unit_detail": unit_detail,
                "performance_metrics": performance_metrics,
                "reporting_structure": reporting_structure,
                "change_history": change_history,
                "page_title": f"Unità: {unit_detail['unit'].name}",
                "page_icon": "building",
                "breadcrumb": [
                    {"name": "Organigramma", "url": "/orgchart"},
                    {"name": "Struttura", "url": "/orgchart/tree"},
                    {"name": unit_detail['unit'].name}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading unit detail {unit_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matrix", response_class=HTMLResponse)
async def orgchart_matrix_view(
    request: Request,
    view_type: str = Query("skills"),  # skills, workload, hierarchy
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Matrix view of organizational structure"""
    try:
        if view_type == "skills":
            matrix_data = orgchart_service.get_skills_matrix()
            page_title = "Matrice Competenze"
        elif view_type == "workload":
            matrix_data = orgchart_service.get_workload_matrix()
            page_title = "Matrice Carico di Lavoro"
        elif view_type == "hierarchy":
            matrix_data = orgchart_service.get_hierarchy_matrix()
            page_title = "Matrice Gerarchica"
        else:
            raise HTTPException(status_code=400, detail="Tipo di vista non valido")
        
        return templates.TemplateResponse(
            "orgchart/matrix.html",
            {
                "request": request,
                "matrix_data": matrix_data,
                "view_type": view_type,
                "page_title": page_title,
                "page_icon": "grid-3x3",
                "breadcrumb": [
                    {"name": "Organigramma", "url": "/orgchart"},
                    {"name": "Vista Matrice"}
                ]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading matrix view {view_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_class=HTMLResponse)
async def orgchart_statistics(
    request: Request,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Comprehensive organizational statistics"""
    try:
        # Get comprehensive statistics
        org_statistics = orgchart_service.get_comprehensive_statistics()
        
        # Get distribution analytics
        distribution_data = orgchart_service.get_distribution_analytics()
        
        # Get trend analysis
        trend_data = orgchart_service.get_organizational_trends()
        
        # Get efficiency metrics
        efficiency_metrics = orgchart_service.get_efficiency_metrics()
        
        return templates.TemplateResponse(
            "orgchart/statistics.html",
            {
                "request": request,
                "org_statistics": org_statistics,
                "distribution_data": distribution_data,
                "trend_data": trend_data,
                "efficiency_metrics": efficiency_metrics,
                "page_title": "Statistiche Organizzative",
                "page_icon": "bar-chart",
                "breadcrumb": [
                    {"name": "Organigramma", "url": "/orgchart"},
                    {"name": "Statistiche"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading orgchart statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/gaps", response_class=HTMLResponse)
async def organizational_gap_analysis(
    request: Request,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Organizational gap analysis"""
    try:
        # Get gap analysis
        gap_analysis = orgchart_service.perform_gap_analysis()
        
        # Get recommendations
        recommendations = orgchart_service.get_organizational_recommendations()
        
        return templates.TemplateResponse(
            "orgchart/gap_analysis.html",
            {
                "request": request,
                "gap_analysis": gap_analysis,
                "recommendations": recommendations,
                "page_title": "Analisi Gap Organizzativi",
                "page_icon": "exclamation-diamond",
                "breadcrumb": [
                    {"name": "Organigramma", "url": "/orgchart"},
                    {"name": "Analisi Gap"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading gap analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulation", response_class=HTMLResponse)
async def organizational_simulation(
    request: Request,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Organizational change simulation interface"""
    try:
        # Get current state for simulation baseline
        current_state = orgchart_service.get_simulation_baseline()
        
        # Get predefined simulation scenarios
        scenarios = orgchart_service.get_simulation_scenarios()
        
        return templates.TemplateResponse(
            "orgchart/simulation.html",
            {
                "request": request,
                "current_state": current_state,
                "scenarios": scenarios,
                "page_title": "Simulazione Organizzativa",
                "page_icon": "diagram-2",
                "breadcrumb": [
                    {"name": "Organigramma", "url": "/orgchart"},
                    {"name": "Simulazione"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading simulation interface: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/span-of-control", response_class=HTMLResponse)
async def span_of_control_report(
    request: Request,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Span of control analysis report"""
    try:
        # Get span of control analysis
        span_analysis = orgchart_service.analyze_span_of_control()
        
        return templates.TemplateResponse(
            "orgchart/span_of_control.html",
            {
                "request": request,
                "span_analysis": span_analysis,
                "page_title": "Analisi Span of Control",
                "page_icon": "diagram-3-fill",
                "breadcrumb": [
                    {"name": "Organigramma", "url": "/orgchart"},
                    {"name": "Report"},
                    {"name": "Span of Control"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading span of control report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/organizational-health", response_class=HTMLResponse)
async def organizational_health_report(
    request: Request,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Organizational health assessment"""
    try:
        # Get health assessment
        health_assessment = orgchart_service.assess_organizational_health()
        
        return templates.TemplateResponse(
            "orgchart/organizational_health.html",
            {
                "request": request,
                "health_assessment": health_assessment,
                "page_title": "Salute Organizzativa",
                "page_icon": "heart-pulse",
                "breadcrumb": [
                    {"name": "Organigramma", "url": "/orgchart"},
                    {"name": "Report"},
                    {"name": "Salute Organizzativa"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading organizational health report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoints for interactive features

@router.get("/api/tree-data")
async def get_tree_data_api(
    unit_id: Optional[int] = Query(None),
    show_persons: bool = Query(True),
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """API endpoint for tree data (for dynamic loading)"""
    try:
        if unit_id:
            tree_data = orgchart_service.get_subtree(unit_id, show_persons=show_persons)
        else:
            tree_data = orgchart_service.get_complete_tree(show_persons=show_persons)
        
        return JSONResponse(content={"tree_data": tree_data})
    except Exception as e:
        logger.error(f"Error getting tree data via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/unit-details/{unit_id}")
async def get_unit_details_api(
    unit_id: int,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """API endpoint for unit details"""
    try:
        unit_details = orgchart_service.get_unit_with_details(unit_id)
        if not unit_details:
            raise HTTPException(status_code=404, detail="Unit not found")
        
        return JSONResponse(content=unit_details)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unit details via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/search-units")
async def search_units_api(
    query: str = Query(...),
    limit: int = Query(10),
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """API endpoint for unit search"""
    try:
        if len(query) < 2:
            return JSONResponse(content={"results": []})
        
        search_results = orgchart_service.search_organizational_units(query, limit=limit)
        return JSONResponse(content={"results": search_results})
    except Exception as e:
        logger.error(f"Error searching units via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/simulate-change")
async def simulate_organizational_change(
    request: Request,
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """API endpoint for organizational change simulation"""
    try:
        simulation_data = await request.json()
        
        # Perform simulation
        simulation_result = orgchart_service.simulate_organizational_change(simulation_data)
        
        return JSONResponse(content=simulation_result)
    except Exception as e:
        logger.error(f"Error simulating organizational change: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/performance-metrics/{unit_id}")
async def get_unit_performance_api(
    unit_id: int,
    period: str = Query("current"),  # current, last_month, last_quarter
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """API endpoint for unit performance metrics"""
    try:
        performance_data = orgchart_service.get_unit_performance_metrics(unit_id, period=period)
        return JSONResponse(content=performance_data)
    except Exception as e:
        logger.error(f"Error getting performance metrics via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/orgchart")
async def export_orgchart(
    format_type: str = Query("svg"),  # svg, pdf, png
    unit_id: Optional[int] = Query(None),
    show_persons: bool = Query(True),
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Export orgchart in various formats"""
    try:
        if format_type not in ["svg", "pdf", "png"]:
            raise HTTPException(status_code=400, detail=f"Formato '{format_type}' non supportato")
        
        # Get tree data
        if unit_id:
            tree_data = orgchart_service.get_subtree(unit_id, show_persons=show_persons)
        else:
            tree_data = orgchart_service.get_complete_tree(show_persons=show_persons)
        
        # Generate export
        export_data = orgchart_service.generate_export(tree_data, format_type)
        
        if format_type == "svg":
            from fastapi.responses import Response
            return Response(
                content=export_data,
                media_type="image/svg+xml",
                headers={"Content-Disposition": "attachment; filename=organigramma.svg"}
            )
        elif format_type == "pdf":
            from fastapi.responses import Response
            return Response(
                content=export_data,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=organigramma.pdf"}
            )
        elif format_type == "png":
            from fastapi.responses import Response
            return Response(
                content=export_data,
                media_type="image/png",
                headers={"Content-Disposition": "attachment; filename=organigramma.png"}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting orgchart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def compare_organizational_structures(
    request: Request,
    date1: Optional[str] = Query(None),
    date2: Optional[str] = Query(None),
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Compare organizational structures between different dates"""
    try:
        # Parse dates or use defaults
        from datetime import date, timedelta
        
        if not date1:
            date1_parsed = date.today() - timedelta(days=30)  # 30 days ago
        else:
            date1_parsed = date.fromisoformat(date1)
        
        if not date2:
            date2_parsed = date.today()  # Today
        else:
            date2_parsed = date.fromisoformat(date2)
        
        # Get comparison data
        comparison_data = orgchart_service.compare_organizational_structures(date1_parsed, date2_parsed)
        
        return templates.TemplateResponse(
            "orgchart/comparison.html",
            {
                "request": request,
                "comparison_data": comparison_data,
                "date1": date1_parsed,
                "date2": date2_parsed,
                "page_title": "Confronto Strutture Organizzative",
                "page_icon": "arrow-left-right",
                "breadcrumb": [
                    {"name": "Organigramma", "url": "/orgchart"},
                    {"name": "Confronto"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error comparing organizational structures: {e}")
        raise HTTPException(status_code=500, detail=str(e))