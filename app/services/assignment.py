"""
Assignment service for business logic with versioning support
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import date
from app.services.base import BaseService
from app.models.assignment import Assignment

logger = logging.getLogger(__name__)


class AssignmentService(BaseService):
    """Assignment service class with versioning support"""
    
    def __init__(self):
        super().__init__(Assignment, "person_job_assignments")
    
    def get_list_query(self) -> str:
        """Get query for listing all assignments with joined data"""
        return """
        SELECT pja.*,
               p.name as person_name,
               p.short_name as person_short_name,
               u.name as unit_name,
               u.short_name as unit_short_name,
               jt.name as job_title_name,
               jt.short_name as job_title_short_name
        FROM person_job_assignments pja
        JOIN persons p ON pja.person_id = p.id
        JOIN units u ON pja.unit_id = u.id
        JOIN job_titles jt ON pja.job_title_id = jt.id
        ORDER BY p.name, u.name, jt.name, pja.version DESC
        """
    
    def get_by_id_query(self) -> str:
        """Get query for fetching single assignment by ID"""
        return """
        SELECT pja.*,
               p.name as person_name,
               p.short_name as person_short_name,
               u.name as unit_name,
               u.short_name as unit_short_name,
               jt.name as job_title_name,
               jt.short_name as job_title_short_name
        FROM person_job_assignments pja
        JOIN persons p ON pja.person_id = p.id
        JOIN units u ON pja.unit_id = u.id
        JOIN job_titles jt ON pja.job_title_id = jt.id
        WHERE pja.id = ?
        """
    
    def get_insert_query(self) -> str:
        return """
        INSERT INTO person_job_assignments 
        (person_id, unit_id, job_title_id, percentage, ad_interim, notes, flags, valid_from, is_current)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    
    def get_update_query(self) -> str:
        # For assignments, we create new versions instead of updating
        return self.get_insert_query()
    
    def get_delete_query(self) -> str:
        return "DELETE FROM person_job_assignments WHERE id = ?"
    
    def model_to_insert_params(self, assignment: Assignment) -> tuple:
        """Convert assignment to parameters for insert query"""
        return (
            assignment.person_id,
            assignment.unit_id,
            assignment.job_title_id,
            assignment.percentage,
            1 if assignment.ad_interim else 0,
            assignment.notes,
            assignment.flags,
            assignment.valid_from.isoformat() if assignment.valid_from else None,
            1 if assignment.is_current else 0
        )
    
    def model_to_update_params(self, assignment: Assignment) -> tuple:
        """For assignments, update creates a new version"""
        return self.model_to_insert_params(assignment)
    
    def get_current_assignments(self) -> List[Assignment]:
        """Get all current assignments"""
        try:
            query = """
            SELECT pja.*,
                   p.name as person_name,
                   p.short_name as person_short_name,
                   u.name as unit_name,
                   u.short_name as unit_short_name,
                   jt.name as job_title_name,
                   jt.short_name as job_title_short_name
            FROM person_job_assignments pja
            JOIN persons p ON pja.person_id = p.id
            JOIN units u ON pja.unit_id = u.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            WHERE pja.is_current = 1
            ORDER BY p.name, u.name, jt.name, pja.version DESC
            """
            rows = self.db_manager.fetch_all(query)
            return [Assignment.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching current assignments: {e}")
            return []
    
    def get_assignments_by_person(self, person_id: int, current_only: bool = False) -> List[Assignment]:
        """Get all assignments for a person"""
        try:
            query = """
            SELECT pja.*,
                   p.name as person_name,
                   p.short_name as person_short_name,
                   u.name as unit_name,
                   u.short_name as unit_short_name,
                   jt.name as job_title_name,
                   jt.short_name as job_title_short_name
            FROM person_job_assignments pja
            JOIN persons p ON pja.person_id = p.id
            JOIN units u ON pja.unit_id = u.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            WHERE pja.person_id = ?
            """
            if current_only:
                query += " AND pja.is_current = 1"
            query += " ORDER BY p.name, u.name, jt.name, pja.version DESC"
            rows = self.db_manager.fetch_all(query, (person_id,))
            return [Assignment.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching assignments for person {person_id}: {e}")
            return []
    
    def get_assignments_by_unit(self, unit_id: int, current_only: bool = False) -> List[Assignment]:
        """Get all assignments for a unit"""
        try:
            query = """
            SELECT pja.*,
                   p.name as person_name,
                   p.short_name as person_short_name,
                   u.name as unit_name,
                   u.short_name as unit_short_name,
                   jt.name as job_title_name,
                   jt.short_name as job_title_short_name
            FROM person_job_assignments pja
            JOIN persons p ON pja.person_id = p.id
            JOIN units u ON pja.unit_id = u.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            WHERE pja.unit_id = ?
            """
            if current_only:
                query += " AND pja.is_current = 1"
            query += " ORDER BY p.name, u.name, jt.name, pja.version DESC"
            rows = self.db_manager.fetch_all(query, (unit_id,))
            return [Assignment.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching assignments for unit {unit_id}: {e}")
            return []
    
    def get_assignment_history(self, person_id: int, unit_id: int, job_title_id: int) -> List[Assignment]:
        """Get version history for a specific assignment combination"""
        try:
            query = """
            SELECT pja.*,
                   p.name as person_name,
                   p.short_name as person_short_name,
                   u.name as unit_name,
                   u.short_name as unit_short_name,
                   jt.name as job_title_name,
                   jt.short_name as job_title_short_name
            FROM person_job_assignments pja
            JOIN persons p ON pja.person_id = p.id
            JOIN units u ON pja.unit_id = u.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            WHERE pja.person_id = ? AND pja.unit_id = ? AND pja.job_title_id = ?
            ORDER BY pja.version DESC
            """
            rows = self.db_manager.fetch_all(query, (person_id, unit_id, job_title_id))
            return [Assignment.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching assignment history: {e}")
            return []
    
    def get_full_history(self) -> List[Assignment]:
        """Get complete assignment history"""
        try:
            return self.get_all()
        except Exception as e:
            logger.error(f"Error fetching full history: {e}")
            return []
    
    def create_or_update_assignment(self, assignment: Assignment) -> Assignment:
        """Create new assignment or create new version of existing one"""
        try:
            # Validate assignment
            errors = assignment.validate()
            if errors:
                from app.models.base import ModelValidationException
                raise ModelValidationException(errors)
            
            # Check if this combination already exists
            existing_query = """
            SELECT * FROM person_job_assignments 
            WHERE person_id = ? AND unit_id = ? AND job_title_id = ? AND is_current = 1
            """
            existing = self.db_manager.fetch_one(
                existing_query, 
                (assignment.person_id, assignment.unit_id, assignment.job_title_id)
            )
            
            if existing:
                logger.info(f"Creating new version for assignment {assignment.person_id}-{assignment.unit_id}-{assignment.job_title_id}")
            else:
                logger.info(f"Creating new assignment {assignment.person_id}-{assignment.unit_id}-{assignment.job_title_id}")
            
            # Insert new assignment (trigger will handle versioning)
            cursor = self.db_manager.execute_query(
                self.get_insert_query(),
                self.model_to_insert_params(assignment)
            )
            
            # Return created assignment
            if cursor.lastrowid:
                return self.get_by_id(cursor.lastrowid)
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error creating/updating assignment: {e}")
            raise
    
    def terminate_assignment(self, assignment_id: int, termination_date: date = None) -> bool:
        """Terminate a current assignment"""
        try:
            if termination_date is None:
                termination_date = date.today()
            
            # Update the assignment to set is_current = False and valid_to date
            query = """
            UPDATE person_job_assignments 
            SET is_current = 0, valid_to = ?, datetime_updated = CURRENT_TIMESTAMP
            WHERE id = ? AND is_current = 1
            """
            cursor = self.db_manager.execute_query(
                query, 
                (termination_date.isoformat(), assignment_id)
            )
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error terminating assignment {assignment_id}: {e}")
            raise
    
    def can_delete(self, assignment_id: int) -> tuple[bool, str]:
        """Check if assignment can be deleted"""
        try:
            assignment = self.get_by_id(assignment_id)
            if not assignment:
                return False, "Assignment not found"
            
            # Check if this is the only version
            history = self.get_assignment_history(
                assignment.person_id, 
                assignment.unit_id, 
                assignment.job_title_id
            )
            
            if len(history) == 1:
                return True, ""
            else:
                return True, f"This will delete one version (total versions: {len(history)})"
            
        except Exception as e:
            logger.error(f"Error checking if assignment {assignment_id} can be deleted: {e}")
            return False, "Error checking dependencies"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get assignment statistics"""
        try:
            stats = {}
            
            # Total assignments
            stats['total_assignments'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM person_job_assignments"
            )['count']
            
            # Current assignments
            stats['current_assignments'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM person_job_assignments WHERE is_current = 1"
            )['count']
            
            # Interim assignments
            stats['interim_assignments'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM person_job_assignments WHERE ad_interim = 1 AND is_current = 1"
            )['count']
            
            # People with assignments
            stats['people_with_assignments'] = self.db_manager.fetch_one(
                "SELECT COUNT(DISTINCT person_id) as count FROM person_job_assignments WHERE is_current = 1"
            )['count']
            
            # Units with assignments
            stats['units_with_assignments'] = self.db_manager.fetch_one(
                "SELECT COUNT(DISTINCT unit_id) as count FROM person_job_assignments WHERE is_current = 1"
            )['count']
            
            # Average assignment duration for terminated assignments
            duration_row = self.db_manager.fetch_one("""
                SELECT AVG(julianday(valid_to) - julianday(valid_from)) as avg_duration
                FROM person_job_assignments 
                WHERE valid_from IS NOT NULL AND valid_to IS NOT NULL
            """)
            stats['avg_duration_days'] = round(duration_row['avg_duration']) if duration_row['avg_duration'] else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching assignment statistics: {e}")
            return {}
    
    def validate_assignment_rules(self, assignment: Assignment) -> List[str]:
        """Validate business rules for assignments"""
        warnings = []
        
        try:
            # Check if person already has assignment in same unit
            existing_in_unit = self.db_manager.fetch_all("""
                SELECT jt.name 
                FROM person_job_assignments pja
                JOIN job_titles jt ON pja.job_title_id = jt.id
                WHERE pja.person_id = ? AND pja.unit_id = ? 
                AND pja.is_current = 1 AND pja.job_title_id != ?
            """, (assignment.person_id, assignment.unit_id, assignment.job_title_id))
            
            if existing_in_unit:
                roles = ", ".join([row['name'] for row in existing_in_unit])
                warnings.append(f"Person already has roles in this unit: {roles}")
            
            # Check for high workload (total percentage > 150%)
            total_percentage = self.db_manager.fetch_one("""
                SELECT SUM(percentage) as total
                FROM person_job_assignments
                WHERE person_id = ? AND is_current = 1
            """, (assignment.person_id,))
            
            if total_percentage and total_percentage['total']:
                current_total = float(total_percentage['total']) + assignment.percentage
                if current_total > 1.5:
                    warnings.append(f"High workload: total percentage would be {current_total*100:.0f}%")
            
            # All job titles are assignable to all units for now
            # This could be enhanced with a job_title_assignable_units table in the future
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error validating assignment rules: {e}")
            return ["Error validating assignment rules"]
    
    def get_searchable_fields(self) -> List[str]:
        """Get list of fields that can be searched for assignments"""
        return ["person_name", "unit_name", "job_title_name", "notes"]
    
    def _validate_for_create(self, assignment: Assignment) -> None:
        """Perform additional validation before creating an assignment"""
        # Validate foreign key references exist
        from app.services.person import PersonService
        from app.services.unit import UnitService
        from app.services.job_title import JobTitleService
        
        person_service = PersonService()
        unit_service = UnitService()
        job_title_service = JobTitleService()
        
        if not person_service.exists(assignment.person_id):
            from app.services.base import ServiceValidationException
            raise ServiceValidationException(f"Person with ID {assignment.person_id} does not exist")
        
        if not unit_service.exists(assignment.unit_id):
            from app.services.base import ServiceValidationException
            raise ServiceValidationException(f"Unit with ID {assignment.unit_id} does not exist")
        
        if not job_title_service.exists(assignment.job_title_id):
            from app.services.base import ServiceValidationException
            raise ServiceValidationException(f"Job title with ID {assignment.job_title_id} does not exist")
        
        # Validate business rules
        warnings = self.validate_assignment_rules(assignment)
        if warnings:
            logger.warning(f"Assignment validation warnings: {warnings}")
    
    def _validate_for_update(self, assignment: Assignment, existing: Assignment) -> None:
        """Perform additional validation before updating an assignment"""
        # For assignments, updates create new versions, so use create validation
        self._validate_for_create(assignment)
    
    def _validate_for_delete(self, assignment: Assignment) -> None:
        """Perform validation before deleting an assignment"""
        can_delete, message = self.can_delete(assignment.id)
        if not can_delete:
            from app.services.base import ServiceIntegrityException
            raise ServiceIntegrityException(message)