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

    def _get_next_version(self, person_id: int, unit_id: int, job_title_id: int) -> int:
        """Get next version number for assignment combination"""
        
        query = """
        SELECT COALESCE(MAX(version), 0) + 1 as next_version
        FROM person_job_assignments
        WHERE person_id = ? AND unit_id = ? AND job_title_id = ?
        """
        
        result = self.db_manager.fetch_one(query, (person_id, unit_id, job_title_id))
        return result['next_version'] if result else 1

    def _deactivate_previous_assignments(self, person_id: int, unit_id: int, job_title_id: int, valid_from: date):
        """Deactivate previous current assignments"""
        
        update_query = """
        UPDATE person_job_assignments
        SET is_current = 0, 
            valid_to = ?
        WHERE person_id = ? AND unit_id = ? AND job_title_id = ? 
          AND is_current = 1
        """
        
        self.db_manager.execute_query(update_query, (
            valid_from.isoformat(),
            person_id,
            unit_id, 
            job_title_id
        ))
    
    def _create_new_version(self, assignment: Assignment) -> Assignment:
        """Create new version of existing assignment"""
        # Set current assignment as historical
        assignment.is_current = True  # New version will be current
        assignment.id = None  # Will get new ID
        assignment.version = None  # Will be set by create_assignment
        
        return self.create_assignment(assignment)
    
    def _update_historical(self, assignment: Assignment) -> Assignment:
        """Update historical (non-current) assignment"""
        
        update_query = """
        UPDATE person_job_assignments
        SET percentage = ?, is_ad_interim = ?, is_unit_boss = ?,
            notes = ?, flags = ?, valid_from = ?, valid_to = ?
        WHERE id = ? AND is_current = 0
        """
        
        self.db_manager.execute_query(update_query, (
            assignment.percentage,
            assignment.is_ad_interim,
            assignment.is_unit_boss,
            assignment.notes,
            assignment.flags,
            assignment.valid_from.isoformat() if assignment.valid_from else None,
            assignment.valid_to.isoformat() if assignment.valid_to else None,
            assignment.id
        ))
        
        return assignment

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
        (person_id, unit_id, job_title_id, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, is_current)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            1 if assignment.is_ad_interim else 0,
            1 if assignment.is_unit_boss else 0,
            assignment.notes,
            assignment.flags,
            assignment.valid_from.isoformat() if assignment.valid_from else None,
            1 if assignment.is_current else 0
        )
    
    def model_to_update_params(self, assignment: Assignment) -> tuple:
        """For assignments, update creates a new version"""
        return self.model_to_insert_params(assignment)
    
    def get_current_assignments(self) -> List[Assignment]:
        """Get all current assignments (is_current=true only)"""
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
    
    def get_current_assignments_by_person(self, person_id: int) -> List[Assignment]:
        """Get current assignments for a specific person (is_current=true only)"""
        return self.get_assignments_by_person(person_id, current_only=True)
    
    def get_current_assignments_by_unit(self, unit_id: int) -> List[Assignment]:
        """Get current assignments for a specific unit (is_current=true only)"""
        return self.get_assignments_by_unit(unit_id, current_only=True)
    
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
        """Get complete version history for a specific assignment combination"""
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
            history = [Assignment.from_sqlite_row(row) for row in rows]
            
            # Validate version consistency
            consistency_errors = self._validate_version_consistency(person_id, unit_id, job_title_id)
            if consistency_errors:
                logger.warning(f"Version consistency issues for assignment {person_id}-{unit_id}-{job_title_id}: {consistency_errors}")
            
            return history
        except Exception as e:
            logger.error(f"Error fetching assignment history: {e}")
            return []
    
    def get_full_history(self) -> List[Assignment]:
        """Get complete assignment history for all assignments"""
        try:
            return self.get_all()
        except Exception as e:
            logger.error(f"Error fetching full history: {e}")
            return []
    
    def get_historical_assignments(self, include_terminated: bool = True) -> List[Assignment]:
        """Get all historical (non-current) assignments"""
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
            WHERE pja.is_current = 0
            """
            if not include_terminated:
                query += " AND pja.valid_to IS NULL"
            
            query += " ORDER BY p.name, u.name, jt.name, pja.version DESC"
            
            rows = self.db_manager.fetch_all(query)
            return [Assignment.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching historical assignments: {e}")
            return []
    
    def create_assignment(self, assignment: Assignment) -> Assignment:
        """Create new assignment with proper versioning"""
        #db_manager = get_db_manager()
        
        try:
            with self.db_manager.get_connection() as conn:
                # Start transaction
                conn.execute("BEGIN TRANSACTION")
                
                # 1. Get next version number
                next_version = self._get_next_version(
                    assignment.person_id, 
                    assignment.unit_id, 
                    assignment.job_title_id
                )
                assignment.version = next_version
                
                # 2. If this is a current assignment, deactivate previous ones
                if assignment.is_current:
                    self._deactivate_previous_assignments(
                        assignment.person_id,
                        assignment.unit_id, 
                        assignment.job_title_id,
                        assignment.valid_from or date.today()
                    )
                
                # 3. Insert new assignment
                insert_query = """
                INSERT INTO person_job_assignments 
                (person_id, unit_id, job_title_id, version, percentage, 
                 is_ad_interim, is_unit_boss, notes, flags, valid_from, 
                 valid_to, is_current)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor = conn.execute(insert_query, (
                    assignment.person_id,
                    assignment.unit_id,
                    assignment.job_title_id,
                    assignment.version,
                    assignment.percentage,
                    assignment.is_ad_interim,
                    assignment.is_unit_boss,
                    assignment.notes,
                    assignment.flags,
                    assignment.valid_from.isoformat() if assignment.valid_from else None,
                    assignment.valid_to.isoformat() if assignment.valid_to else None,
                    assignment.is_current
                ))
                
                assignment.id = cursor.lastrowid
                
                # Commit transaction
                conn.execute("COMMIT")
                
                logger.info(f"Created assignment {assignment.id} version {assignment.version}")
                return assignment
                
        except Exception as e:
            # Rollback on error
            try:
                conn.execute("ROLLBACK")
            except:
                pass
            logger.error(f"Failed to create assignment: {e}")
            raise

    def _modify_assignment(self, assignment: Assignment) -> Assignment:
        """Update assignment - creates new version if current"""
        if assignment.is_current:
            # For current assignments, create new version instead of updating
            return self._create_new_version(assignment)
        else:
            # For historical assignments, allow direct update
            return self._update_historical(assignment)

    def modify_assignment(self, person_id: int, unit_id: int, job_title_id: int, new_assignment_data: Assignment) -> Assignment:
        # Validate new assignment data
        errors = new_assignment_data.validate()
        if errors:
            from app.models.base import ModelValidationException
            raise ModelValidationException(errors)

        # Validate foreign key references
        self._validate_for_create(new_assignment_data)

        old_assignment = self._get_current_assignment(
            person_id, 
            unit_id, 
            job_title_id
        )

        if not old_assignment:
            raise ValueError(f"No current assignment found for person {person_id}, unit {unit_id}, job_title {job_title_id}")

        return self._modify_assignment(new_assignment_data);

    def terminate_assignment_old(self, assignment_id: int, termination_date: date = None) -> bool:
        """Terminate a current assignment with valid_to dates and is_current=false"""
        try:
            if termination_date is None:
                termination_date = date.today()
            
            # Get the assignment to terminate
            assignment = self.get_by_id(assignment_id)
            if not assignment:
                raise ValueError(f"Assignment with ID {assignment_id} not found")
            
            if not assignment.is_current:
                raise ValueError(f"Assignment {assignment_id} is not current and cannot be terminated")
            
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
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Terminated assignment {assignment_id} on {termination_date}")
            else:
                logger.warning(f"No assignment was terminated for ID {assignment_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error terminating assignment {assignment_id}: {e}")
            raise

    def terminate_assignment(self, assignment_id: int, termination_date: date = None) -> Assignment:
        """Terminate an assignment"""
        #db_manager = get_db_manager()
        
        if not termination_date:
            termination_date = date.today()
        
        update_query = """
        UPDATE person_job_assignments 
        SET valid_to = ?, is_current = 0, datetime_updated = CURRENT_TIMESTAMP
        WHERE id = ? AND is_current = 1
        """
        
        self.db_manager.execute_query(update_query, (
            termination_date.isoformat(),
            assignment_id
        ))
        
        # Return updated assignment
        return self.get_by_id(assignment_id)

    def terminate_assignment_by_combination(self, person_id: int, unit_id: int, job_title_id: int, 
                                          termination_date: date = None) -> bool:
        """Terminate current assignment by person/unit/job_title combination"""
        try:
            current_assignment = self._get_current_assignment(person_id, unit_id, job_title_id)
            if not current_assignment:
                raise ValueError(f"No current assignment found for person {person_id}, unit {unit_id}, job_title {job_title_id}")
            
            return self.terminate_assignment(current_assignment.id, termination_date)
            
        except Exception as e:
            logger.error(f"Error terminating assignment by combination: {e}")
            raise
    
    def create_or_update_assignment(self, assignment: Assignment) -> Assignment:
        """Create new assignment or create new version of existing one (backward compatibility)"""
        try:
            # Check if this combination already exists
            existing = self._get_current_assignment(
                assignment.person_id, 
                assignment.unit_id, 
                assignment.job_title_id
            )
            
            if existing:
                # Modify existing assignment (create new version)
                return self.modify_assignment(
                    assignment.person_id,
                    assignment.unit_id,
                    assignment.job_title_id,
                    assignment
                )
            else:
                # Create new assignment
                return self.create_assignment(assignment)
                
        except Exception as e:
            logger.error(f"Error creating/updating assignment: {e}")
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
                "SELECT COUNT(*) as count FROM person_job_assignments WHERE is_ad_interim = 1 AND is_current = 1"
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
                WHERE id != ? AND person_id = ? AND is_current = 1
            """, (assignment.id, assignment.person_id,))
            
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
    
    def _get_current_assignment(self, person_id: int, unit_id: int, job_title_id: int) -> Optional[Assignment]:
        """Get current assignment for a specific person/unit/job_title combination"""
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
            WHERE pja.person_id = ? AND pja.unit_id = ? AND pja.job_title_id = ? AND pja.is_current = 1
            """
            row = self.db_manager.fetch_one(query, (person_id, unit_id, job_title_id))
            return Assignment.from_sqlite_row(row) if row else None
            
        except Exception as e:
            logger.error(f"Error fetching current assignment: {e}")
            return None
    
    def _validate_version_consistency(self, person_id: int, unit_id: int, job_title_id: int) -> List[str]:
        """Validate version consistency for an assignment combination"""
        errors = []
        try:
            # Check for version gaps
            query = """
            SELECT version FROM person_job_assignments
            WHERE person_id = ? AND unit_id = ? AND job_title_id = ?
            ORDER BY version
            """
            rows = self.db_manager.fetch_all(query, (person_id, unit_id, job_title_id))
            versions = [row['version'] for row in rows]
            
            if versions:
                # Check for gaps in version sequence
                expected_versions = list(range(1, len(versions) + 1))
                if versions != expected_versions:
                    errors.append(f"Version sequence has gaps: expected {expected_versions}, found {versions}")
                
                # Check that only one version is current
                current_count_query = """
                SELECT COUNT(*) as count FROM person_job_assignments
                WHERE person_id = ? AND unit_id = ? AND job_title_id = ? AND is_current = 1
                """
                current_count = self.db_manager.fetch_one(current_count_query, (person_id, unit_id, job_title_id))
                if current_count and current_count['count'] > 1:
                    errors.append(f"Multiple current versions found: {current_count['count']}")
                
        except Exception as e:
            logger.error(f"Error validating version consistency: {e}")
            errors.append(f"Error validating version consistency: {e}")
        
        return errors
    
    def validate_all_version_consistency(self) -> Dict[str, List[str]]:
        """Validate version consistency for all assignment combinations"""
        try:
            # Get all unique assignment combinations
            query = """
            SELECT DISTINCT person_id, unit_id, job_title_id
            FROM person_job_assignments
            ORDER BY person_id, unit_id, job_title_id
            """
            combinations = self.db_manager.fetch_all(query)
            
            all_errors = {}
            for combo in combinations:
                person_id = combo['person_id']
                unit_id = combo['unit_id']
                job_title_id = combo['job_title_id']
                
                errors = self._validate_version_consistency(person_id, unit_id, job_title_id)
                if errors:
                    key = f"{person_id}-{unit_id}-{job_title_id}"
                    all_errors[key] = errors
            
            return all_errors
            
        except Exception as e:
            logger.error(f"Error validating all version consistency: {e}")
            return {"error": [str(e)]}
    
    def get_version_statistics(self) -> Dict[str, Any]:
        """Get statistics about assignment versioning"""
        try:
            stats = {}
            
            # Total versions
            stats['total_versions'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM person_job_assignments"
            )['count']
            
            # Current versions
            stats['current_versions'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM person_job_assignments WHERE is_current = 1"
            )['count']
            
            # Historical versions
            stats['historical_versions'] = stats['total_versions'] - stats['current_versions']
            
            # Unique assignment combinations
            stats['unique_combinations'] = self.db_manager.fetch_one("""
                SELECT COUNT(DISTINCT person_id || '-' || unit_id || '-' || job_title_id) as count
                FROM person_job_assignments
            """)['count']
            
            # Average versions per combination
            if stats['unique_combinations'] > 0:
                stats['avg_versions_per_combination'] = round(
                    stats['total_versions'] / stats['unique_combinations'], 2
                )
            else:
                stats['avg_versions_per_combination'] = 0
            
            # Combinations with multiple versions
            stats['combinations_with_multiple_versions'] = self.db_manager.fetch_one("""
                SELECT COUNT(*) as count FROM (
                    SELECT person_id, unit_id, job_title_id
                    FROM person_job_assignments
                    GROUP BY person_id, unit_id, job_title_id
                    HAVING COUNT(*) > 1
                )
            """)['count']
            
            # Terminated assignments
            stats['terminated_assignments'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM person_job_assignments WHERE valid_to IS NOT NULL"
            )['count']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching version statistics: {e}")
            return {}
    
    def get_assignment_timeline(self, person_id: int, unit_id: int, job_title_id: int) -> List[Dict[str, Any]]:
        """Get timeline of changes for a specific assignment combination"""
        try:
            history = self.get_assignment_history(person_id, unit_id, job_title_id)
            timeline = []
            
            for assignment in reversed(history):  # Chronological order
                event = {
                    'version': assignment.version,
                    'date': assignment.valid_from or assignment.datetime_created.date(),
                    'event_type': 'created' if assignment.version == 1 else 'modified',
                    'percentage': assignment.percentage,
                    'is_ad_interim': assignment.is_ad_interim,
                    'is_unit_boss': assignment.is_unit_boss,
                    'is_current': assignment.is_current,
                    'notes': assignment.notes
                }
                
                if assignment.valid_to:
                    event['termination_date'] = assignment.valid_to
                    event['event_type'] = 'terminated'
                
                timeline.append(event)
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error fetching assignment timeline: {e}")
            return []