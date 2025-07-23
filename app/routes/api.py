"""
API routes for AJAX and external integrations
RESTful endpoints for all CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
from datetime import date
from pydantic import BaseModel, Field

from app.services.unit import UnitService
from app.services.person import PersonService
from app.services.job_title import JobTitleService
from app.services.assignment import AssignmentService
from app.services.orgchart import OrgchartService
from app.models.base import ModelValidationException

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for API requests/responses
class ApiResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    message: str = ""
    data: Any = None
    errors: List[str] = []

class UnitCreateRequest(BaseModel):
    """Unit creation request"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    type: str = Field(..., pattern="^(function|OrganizationalUnit)$")
    parent_unit_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class PersonCreateRequest(BaseModel):
    """Person creation request"""
    name: str = Field(..., min_length=1, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None) #, regex=r"^[^@]+@[^@]+\.[^@]+$")

class JobTitleCreateRequest(BaseModel):
    """Job title creation request"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    assignable_unit_ids: List[int] = []

class AssignmentCreateRequest(BaseModel):
    """Assignment creation request"""
    person_id: int
    unit_id: int
    job_title_id: int
    percentage: float = Field(..., gt=0, le=100)
    ad_interim: bool = False
    notes: Optional[str] = None
    flags: Optional[str] = None
    valid_from: Optional[str] = None

# Dependency functions
def get_unit_service():
    return UnitService()

def get_person_service():
    return PersonService()

def get_job_title_service():
    return JobTitleService()

def get_assignment_service():
    return AssignmentService()

def get_orgchart_service():
    return OrgchartService()

# Utility functions
def handle_service_exception(e: Exception, operation: str) -> JSONResponse:
    """Handle service exceptions and return appropriate JSON response"""
    if isinstance(e, ModelValidationException):
        return JSONResponse(
            status_code=400,
            content=ApiResponse(
                success=False,
                message=f"Validation error during {operation}",
                errors=[f"{err.field}: {err.message}" for err in e.errors]
            ).dict()
        )
    else:
        logger.error(f"Error during {operation}: {e}")
        return JSONResponse(
            status_code=500,
            content=ApiResponse(
                success=False,
                message=f"Internal error during {operation}",
                errors=[str(e)]
            ).dict()
        )

def parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object"""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None

# UNITS API ENDPOINTS

@router.get("/units")
async def api_list_units(
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    unit_service: UnitService = Depends(get_unit_service)
):
    """Get list of units with optional filters"""
    try:
        if search:
            units = unit_service.search(search, ['name', 'short_name'])
        else:
            units = unit_service.get_all()
        
        # Apply filters
        if type:
            units = [u for u in units if u.type == type]
        if parent_id is not None:
            units = [u for u in units if u.parent_unit_id == parent_id]
        
        return ApiResponse(
            data=[unit.to_dict() for unit in units],
            message=f"Found {len(units)} units"
        )
    except Exception as e:
        return handle_service_exception(e, "listing units")

@router.get("/units/{unit_id}")
async def api_get_unit(
    unit_id: int,
    unit_service: UnitService = Depends(get_unit_service)
):
    """Get single unit by ID"""
    try:
        unit = unit_service.get_by_id(unit_id)
        if not unit:
            return JSONResponse(
                status_code=404,
                content=ApiResponse(
                    success=False,
                    message="Unit not found"
                ).dict()
            )
        
        return ApiResponse(
            data=unit.to_dict(),
            message="Unit retrieved successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "getting unit")

@router.post("/units")
async def api_create_unit(
    unit_data: UnitCreateRequest,
    unit_service: UnitService = Depends(get_unit_service)
):
    """Create new unit"""
    try:
        from app.models.unit import Unit
        
        # Create unit model
        unit = Unit(
            id=unit_data.id,
            name=unit_data.name,
            short_name=unit_data.short_name,
            type=unit_data.type,
            parent_unit_id=unit_data.parent_unit_id,
            start_date=parse_date_string(unit_data.start_date),
            end_date=parse_date_string(unit_data.end_date)
        )
        
        # Create unit
        created_unit = unit_service.create(unit)
        
        return JSONResponse(
            status_code=201,
            content=ApiResponse(
                data=created_unit.to_dict(),
                message="Unit created successfully"
            ).dict()
        )
    except Exception as e:
        return handle_service_exception(e, "creating unit")

@router.put("/units/{unit_id}")
async def api_update_unit(
    unit_id: int,
    unit_data: UnitCreateRequest,
    unit_service: UnitService = Depends(get_unit_service)
):
    """Update existing unit"""
    try:
        # Get existing unit
        existing_unit = unit_service.get_by_id(unit_id)
        if not existing_unit:
            return JSONResponse(
                status_code=404,
                content=ApiResponse(
                    success=False,
                    message="Unit not found"
                ).dict()
            )
        
        # Update unit properties
        existing_unit.name = unit_data.name
        existing_unit.short_name = unit_data.short_name
        existing_unit.type = unit_data.type
        existing_unit.parent_unit_id = unit_data.parent_unit_id
        existing_unit.start_date = parse_date_string(unit_data.start_date)
        existing_unit.end_date = parse_date_string(unit_data.end_date)
        
        # Update unit
        updated_unit = unit_service.update(existing_unit)
        
        return ApiResponse(
            data=updated_unit.to_dict(),
            message="Unit updated successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "updating unit")

@router.delete("/units/{unit_id}")
async def api_delete_unit(
    unit_id: int,
    unit_service: UnitService = Depends(get_unit_service)
):
    """Delete unit"""
    try:
        # Check if unit can be deleted
        can_delete, reason = unit_service.can_delete(unit_id)
        if not can_delete:
            return JSONResponse(
                status_code=400,
                content=ApiResponse(
                    success=False,
                    message=reason
                ).dict()
            )
        
        # Delete unit
        success = unit_service.delete(unit_id)
        if not success:
            return JSONResponse(
                status_code=500,
                content=ApiResponse(
                    success=False,
                    message="Failed to delete unit"
                ).dict()
            )
        
        return ApiResponse(message="Unit deleted successfully")
    except Exception as e:
        return handle_service_exception(e, "deleting unit")

@router.get("/units/{unit_id}/hierarchy")
async def api_get_unit_hierarchy(
    unit_id: int,
    unit_service: UnitService = Depends(get_unit_service)
):
    """Get unit hierarchy (children tree)"""
    try:
        children = unit_service.get_children(unit_id)
        return ApiResponse(
            data=[child.to_dict() for child in children],
            message=f"Found {len(children)} child units"
        )
    except Exception as e:
        return handle_service_exception(e, "getting unit hierarchy")

# PERSONS API ENDPOINTS

@router.get("/persons")
async def api_list_persons(
    search: Optional[str] = Query(None),
    has_assignments: Optional[bool] = Query(None),
    person_service: PersonService = Depends(get_person_service)
):
    """Get list of persons with optional filters"""
    try:
        if search:
            persons = person_service.search(search, ['name', 'short_name', 'email'])
        else:
            persons = person_service.get_all()
        
        # Apply filters
        if has_assignments is not None:
            if has_assignments:
                persons = [p for p in persons if p.current_assignments_count > 0]
            else:
                persons = [p for p in persons if p.current_assignments_count == 0]
        
        return ApiResponse(
            data=[person.to_dict() for person in persons],
            message=f"Found {len(persons)} persons"
        )
    except Exception as e:
        return handle_service_exception(e, "listing persons")

@router.get("/persons/{person_id}")
async def api_get_person(
    person_id: int,
    person_service: PersonService = Depends(get_person_service)
):
    """Get single person by ID"""
    try:
        person = person_service.get_by_id(person_id)
        if not person:
            return JSONResponse(
                status_code=404,
                content=ApiResponse(
                    success=False,
                    message="Person not found"
                ).dict()
            )
        
        return ApiResponse(
            data=person.to_dict(),
            message="Person retrieved successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "getting person")

@router.post("/persons")
async def api_create_person(
    person_data: PersonCreateRequest,
    person_service: PersonService = Depends(get_person_service)
):
    """Create new person"""
    try:
        from app.models.person import Person
        
        # Create person model
        person = Person(
            name=person_data.name,
            short_name=person_data.short_name,
            email=person_data.email
        )
        
        # Create person
        created_person = person_service.create(person)
        
        return JSONResponse(
            status_code=201,
            content=ApiResponse(
                data=created_person.to_dict(),
                message="Person created successfully"
            ).dict()
        )
    except Exception as e:
        return handle_service_exception(e, "creating person")

@router.put("/persons/{person_id}")
async def api_update_person(
    person_id: int,
    person_data: PersonCreateRequest,
    person_service: PersonService = Depends(get_person_service)
):
    """Update existing person"""
    try:
        # Get existing person
        existing_person = person_service.get_by_id(person_id)
        if not existing_person:
            return JSONResponse(
                status_code=404,
                content=ApiResponse(
                    success=False,
                    message="Person not found"
                ).dict()
            )
        
        # Update person properties
        existing_person.name = person_data.name
        existing_person.short_name = person_data.short_name
        existing_person.email = person_data.email
        
        # Update person
        updated_person = person_service.update(existing_person)
        
        return ApiResponse(
            data=updated_person.to_dict(),
            message="Person updated successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "updating person")

@router.delete("/persons/{person_id}")
async def api_delete_person(
    person_id: int,
    person_service: PersonService = Depends(get_person_service)
):
    """Delete person"""
    try:
        # Check if person can be deleted
        can_delete, reason = person_service.can_delete(person_id)
        if not can_delete:
            return JSONResponse(
                status_code=400,
                content=ApiResponse(
                    success=False,
                    message=reason
                ).dict()
            )
        
        # Delete person
        success = person_service.delete(person_id)
        if not success:
            return JSONResponse(
                status_code=500,
                content=ApiResponse(
                    success=False,
                    message="Failed to delete person"
                ).dict()
            )
        
        return ApiResponse(message="Person deleted successfully")
    except Exception as e:
        return handle_service_exception(e, "deleting person")

@router.get("/persons/{person_id}/assignments")
async def api_get_person_assignments(
    person_id: int,
    current_only: bool = Query(True),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Get assignments for person"""
    try:
        assignments = assignment_service.get_assignments_by_person(person_id, current_only)
        return ApiResponse(
            data=[assignment.to_dict() for assignment in assignments],
            message=f"Found {len(assignments)} assignments"
        )
    except Exception as e:
        return handle_service_exception(e, "getting person assignments")

# JOB TITLES API ENDPOINTS

@router.get("/job-titles")
async def api_list_job_titles(
    search: Optional[str] = Query(None),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Get list of job titles with optional filters"""
    try:
        if search:
            job_titles = job_title_service.search(search, ['name', 'short_name'])
        else:
            job_titles = job_title_service.get_all()
        
        return ApiResponse(
            data=[job_title.to_dict() for job_title in job_titles],
            message=f"Found {len(job_titles)} job titles"
        )
    except Exception as e:
        return handle_service_exception(e, "listing job titles")

@router.get("/job-titles/{job_title_id}")
async def api_get_job_title(
    job_title_id: int,
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Get single job title by ID"""
    try:
        job_title = job_title_service.get_by_id(job_title_id)
        if not job_title:
            return JSONResponse(
                status_code=404,
                content=ApiResponse(
                    success=False,
                    message="Job title not found"
                ).dict()
            )
        
        return ApiResponse(
            data=job_title.to_dict(),
            message="Job title retrieved successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "getting job title")

@router.post("/job-titles")
async def api_create_job_title(
    job_title_data: JobTitleCreateRequest,
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Create new job title"""
    try:
        from app.models.job_title import JobTitle
        
        # Create job title model
        job_title = JobTitle(
            id=job_title_data.id,
            name=job_title_data.name,
            short_name=job_title_data.short_name,
            start_date=parse_date_string(job_title_data.start_date),
            end_date=parse_date_string(job_title_data.end_date)
        )
        
        # Create job title
        created_job_title = job_title_service.create(job_title)
        
        # Set assignable units if provided
        if job_title_data.assignable_unit_ids:
            job_title_service.set_assignable_units(created_job_title.id, job_title_data.assignable_unit_ids)
        
        return JSONResponse(
            status_code=201,
            content=ApiResponse(
                data=created_job_title.to_dict(),
                message="Job title created successfully"
            ).dict()
        )
    except Exception as e:
        return handle_service_exception(e, "creating job title")

# ASSIGNMENTS API ENDPOINTS

@router.get("/assignments")
async def api_list_assignments(
    current_only: bool = Query(True),
    person_id: Optional[int] = Query(None),
    unit_id: Optional[int] = Query(None),
    job_title_id: Optional[int] = Query(None),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Get list of assignments with optional filters"""
    try:
        if current_only:
            assignments = assignment_service.get_current_assignments()
        else:
            assignments = assignment_service.get_full_history()
        
        # Apply filters
        if person_id:
            assignments = [a for a in assignments if a.person_id == person_id]
        if unit_id:
            assignments = [a for a in assignments if a.unit_id == unit_id]
        if job_title_id:
            assignments = [a for a in assignments if a.job_title_id == job_title_id]
        
        return ApiResponse(
            data=[assignment.to_dict() for assignment in assignments],
            message=f"Found {len(assignments)} assignments"
        )
    except Exception as e:
        return handle_service_exception(e, "listing assignments")

@router.get("/assignments/{assignment_id}")
async def api_get_assignment(
    assignment_id: int,
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Get single assignment by ID"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            return JSONResponse(
                status_code=404,
                content=ApiResponse(
                    success=False,
                    message="Assignment not found"
                ).dict()
            )
        
        return ApiResponse(
            data=assignment.to_dict(),
            message="Assignment retrieved successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "getting assignment")

@router.post("/assignments")
async def api_create_assignment(
    assignment_data: AssignmentCreateRequest,
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Create new assignment (or new version)"""
    try:
        from app.models.assignment import Assignment
        
        # Create assignment model
        assignment = Assignment(
            person_id=assignment_data.person_id,
            unit_id=assignment_data.unit_id,
            job_title_id=assignment_data.job_title_id,
            percentage=assignment_data.percentage / 100.0,  # Convert to decimal
            ad_interim=assignment_data.ad_interim,
            notes=assignment_data.notes,
            flags=assignment_data.flags,
            valid_from=parse_date_string(assignment_data.valid_from),
            is_current=True
        )
        
        # Create assignment (will handle versioning automatically)
        created_assignment = assignment_service.create_or_update_assignment(assignment)
        
        return JSONResponse(
            status_code=201,
            content=ApiResponse(
                data=created_assignment.to_dict(),
                message="Assignment created successfully"
            ).dict()
        )
    except Exception as e:
        return handle_service_exception(e, "creating assignment")

@router.post("/assignments/{assignment_id}/terminate")
async def api_terminate_assignment(
    assignment_id: int,
    termination_data: Dict[str, Any] = Body({"termination_date": None}),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Terminate assignment"""
    try:
        termination_date = date.today()
        if termination_data.get("termination_date"):
            termination_date = parse_date_string(termination_data["termination_date"]) or date.today()
        
        success = assignment_service.terminate_assignment(assignment_id, termination_date)
        if not success:
            return JSONResponse(
                status_code=500,
                content=ApiResponse(
                    success=False,
                    message="Failed to terminate assignment"
                ).dict()
            )
        
        return ApiResponse(message="Assignment terminated successfully")
    except Exception as e:
        return handle_service_exception(e, "terminating assignment")

@router.get("/assignments/{assignment_id}/history")
async def api_get_assignment_history(
    assignment_id: int,
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Get version history for assignment"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            return JSONResponse(
                status_code=404,
                content=ApiResponse(
                    success=False,
                    message="Assignment not found"
                ).dict()
            )
        
        history = assignment_service.get_assignment_history(
            assignment.person_id, assignment.unit_id, assignment.job_title_id
        )
        
        return ApiResponse(
            data=[version.to_dict() for version in history],
            message=f"Found {len(history)} versions"
        )
    except Exception as e:
        return handle_service_exception(e, "getting assignment history")

# ORGCHART API ENDPOINTS

@router.get("/orgchart/tree")
async def api_get_orgchart_tree(
    unit_id: Optional[int] = Query(None),
    show_persons: bool = Query(True),
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Get orgchart tree structure"""
    try:
        if unit_id:
            tree_data = orgchart_service.get_subtree(unit_id, show_persons=show_persons)
        else:
            tree_data = orgchart_service.get_complete_tree(show_persons=show_persons)
        
        return ApiResponse(
            data=tree_data,
            message="Orgchart tree retrieved successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "getting orgchart tree")

@router.get("/orgchart/statistics")
async def api_get_orgchart_statistics(
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Get organizational statistics"""
    try:
        overview = orgchart_service.get_organization_overview()
        metrics = orgchart_service.get_organization_metrics()
        
        return ApiResponse(
            data={**overview, **metrics},
            message="Statistics retrieved successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "getting orgchart statistics")

@router.get("/orgchart/vacant-positions")
async def api_get_vacant_positions(
    orgchart_service: OrgchartService = Depends(get_orgchart_service)
):
    """Get vacant positions"""
    try:
        vacant_positions = orgchart_service.get_vacant_positions()
        return ApiResponse(
            data=vacant_positions,
            message=f"Found {len(vacant_positions)} vacant positions"
        )
    except Exception as e:
        return handle_service_exception(e, "getting vacant positions")

# SEARCH AND UTILITY ENDPOINTS

@router.get("/search")
async def api_global_search(
    query: str = Query(..., min_length=2),
    entity_types: List[str] = Query(["units", "persons", "job_titles"]),
    limit: int = Query(10),
    unit_service: UnitService = Depends(get_unit_service),
    person_service: PersonService = Depends(get_person_service),
    job_title_service: JobTitleService = Depends(get_job_title_service)
):
    """Global search across all entities"""
    try:
        results = {}
        
        if "units" in entity_types:
            units = unit_service.search(query, ['name', 'short_name'])[:limit]
            results['units'] = [unit.to_dict() for unit in units]
        
        if "persons" in entity_types:
            persons = person_service.search(query, ['name', 'short_name', 'email'])[:limit]
            results['persons'] = [person.to_dict() for person in persons]
        
        if "job_titles" in entity_types:
            job_titles = job_title_service.search(query, ['name', 'short_name'])[:limit]
            results['job_titles'] = [jt.to_dict() for jt in job_titles]
        
        total_results = sum(len(results[key]) for key in results)
        
        return ApiResponse(
            data=results,
            message=f"Found {total_results} results for '{query}'"
        )
    except Exception as e:
        return handle_service_exception(e, "performing global search")

@router.get("/validate/assignment")
async def api_validate_assignment(
    person_id: int = Query(...),
    unit_id: int = Query(...),
    job_title_id: int = Query(...),
    percentage: float = Query(...),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Validate assignment before creation"""
    try:
        from app.models.assignment import Assignment
        
        # Create temporary assignment for validation
        temp_assignment = Assignment(
            person_id=person_id,
            unit_id=unit_id,
            job_title_id=job_title_id,
            percentage=percentage / 100.0
        )
        
        # Validate business rules
        warnings = assignment_service.validate_assignment_rules(temp_assignment)
        validation_errors = temp_assignment.validate()
        
        is_valid = len(validation_errors) == 0
        
        return ApiResponse(
            data={
                'is_valid': is_valid,
                'warnings': warnings,
                'errors': [{'field': err.field, 'message': err.message} for err in validation_errors]
            },
            message="Validation completed"
        )
    except Exception as e:
        return handle_service_exception(e, "validating assignment")

@router.get("/health")
async def api_health_check():
    """API health check endpoint"""
    try:
        # Basic health check - could be extended with database connectivity, etc.
        return ApiResponse(
            data={
                'status': 'healthy',
                'timestamp': date.today().isoformat(),
                'version': '1.0.0'
            },
            message="API is healthy"
        )
    except Exception as e:
        return handle_service_exception(e, "health check")

@router.get("/stats")
async def api_get_global_stats(
    unit_service: UnitService = Depends(get_unit_service),
    person_service: PersonService = Depends(get_person_service),
    job_title_service: JobTitleService = Depends(get_job_title_service),
    assignment_service: AssignmentService = Depends(get_assignment_service)
):
    """Get global application statistics"""
    try:
        stats = {
            'units': unit_service.count(),
            'persons': person_service.count(),
            'job_titles': job_title_service.count(),
            'active_assignments': len(assignment_service.get_current_assignments())
        }
        
        # Get assignment statistics
        assignment_stats = assignment_service.get_statistics()
        stats.update(assignment_stats)
        
        return ApiResponse(
            data=stats,
            message="Global statistics retrieved successfully"
        )
    except Exception as e:
        return handle_service_exception(e, "getting global statistics")