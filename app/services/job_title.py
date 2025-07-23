"""
Job Title service for business logic
"""

import logging
from typing import List, Optional, Dict, Any
from app.services.base import BaseService
from app.models.job_title import JobTitle
from app.models.unit import Unit
from app.models.assignment import Assignment

logger = logging.getLogger(__name__)


class JobTitleService(BaseService):
    """Job Title service class"""
    
    def __init__(self):
        super().__init__(JobTitle, "job_titles")
    
    def get_list_query(self) -> str:
        """Get query for listing all job titles with computed fields"""
        return """
        SELECT jt.*,
               COUNT(DISTINCT pja_current.id) as current_assignments_count,
               COUNT(DISTINCT pja_all.id) as total_assignments_count
        FROM job_titles jt
        LEFT JOIN person_job_assignments pja_current ON jt.id = pja_current.job_title_id AND pja_current.is_current = 1
        LEFT JOIN person_job_assignments pja_all ON jt.id = pja_all.job_title_id
        GROUP BY jt.id, jt.name, jt.short_name, jt.aliases, 
                 jt.start_date, jt.end_date, jt.datetime_created, jt.datetime_updated
        ORDER BY jt.name
        """
    
    def get_by_id_query(self) -> str:
        """Get query for fetching single job title by ID"""
        return """
        SELECT jt.*,
               COUNT(DISTINCT pja_current.id) as current_assignments_count,
               COUNT(DISTINCT pja_all.id) as total_assignments_count
        FROM job_titles jt
        LEFT JOIN person_job_assignments pja_current ON jt.id = pja_current.job_title_id AND pja_current.is_current = 1
        LEFT JOIN person_job_assignments pja_all ON jt.id = pja_all.job_title_id
        WHERE jt.id = ?
        GROUP BY jt.id, jt.name, jt.short_name, jt.aliases, 
                 jt.start_date, jt.end_date, jt.datetime_created, jt.datetime_updated
        """
    
    def get_insert_query(self) -> str:
        return """
        INSERT INTO job_titles (name, short_name, aliases, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
        """
    
    def get_update_query(self) -> str:
        return """
        UPDATE job_titles 
        SET name = ?, short_name = ?, aliases = ?, start_date = ?, end_date = ?
        WHERE id = ?
        """
    
    def get_delete_query(self) -> str:
        return "DELETE FROM job_titles WHERE id = ?"
    
    def model_to_insert_params(self, job_title: JobTitle) -> tuple:
        """Convert job title to parameters for insert query"""
        return (
            job_title.name,
            job_title.short_name,
            job_title.aliases_json,
            job_title.start_date.isoformat() if job_title.start_date else None,
            job_title.end_date.isoformat() if job_title.end_date else None
        )
    
    def model_to_update_params(self, job_title: JobTitle) -> tuple:
        """Convert job title to parameters for update query"""
        return (
            job_title.name,
            job_title.short_name,
            job_title.aliases_json,
            job_title.start_date.isoformat() if job_title.start_date else None,
            job_title.end_date.isoformat() if job_title.end_date else None,
            job_title.id
        )
    
    def get_assignable_units(self, job_title_id: int) -> List[Unit]:
        """Get units that this job title can be assigned to (all units for now)"""
        try:
            from app.services.unit import UnitService
            unit_service = UnitService()
            return unit_service.get_all()
        except Exception as e:
            logger.error(f"Error fetching assignable units for job title {job_title_id}: {e}")
            return []
    
    def set_assignable_units(self, job_title_id: int, unit_ids: List[int]) -> bool:
        """Set which units this job title can be assigned to (placeholder for future implementation)"""
        # For now, all job titles can be assigned to all units
        # This could be implemented with a separate table in the future
        logger.info(f"Setting assignable units for job title {job_title_id}: {unit_ids}")
        return True
    
    def get_current_assignments(self, job_title_id: int) -> List[Assignment]:
        """Get current assignments for this job title"""
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
            WHERE pja.job_title_id = ? AND pja.is_current = 1
            ORDER BY p.name, u.name
            """
            rows = self.db_manager.fetch_all(query, (job_title_id,))
            return [Assignment.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching current assignments for job title {job_title_id}: {e}")
            return []
    
    def get_assignment_history(self, job_title_id: int) -> List[Assignment]:
        """Get complete assignment history for this job title"""
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
            WHERE pja.job_title_id = ?
            ORDER BY p.name, u.name, pja.version DESC
            """
            rows = self.db_manager.fetch_all(query, (job_title_id,))
            return [Assignment.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching assignment history for job title {job_title_id}: {e}")
            return []
    
    def can_delete(self, job_title_id: int) -> tuple[bool, str]:
        """Check if job title can be deleted"""
        try:
            # Check for current assignments
            current_assignments_query = """
            SELECT COUNT(*) as count 
            FROM person_job_assignments 
            WHERE job_title_id = ? AND is_current = 1
            """
            row = self.db_manager.fetch_one(current_assignments_query, (job_title_id,))
            if row and row['count'] > 0:
                return False, f"Il ruolo ha {row['count']} incarichi correnti"
            
            # Check for historical assignments (allow deletion but warn)
            all_assignments_query = """
            SELECT COUNT(*) as count 
            FROM person_job_assignments 
            WHERE job_title_id = ?
            """
            row = self.db_manager.fetch_one(all_assignments_query, (job_title_id,))
            if row and row['count'] > 0:
                return True, f"Attenzione: il ruolo ha {row['count']} incarichi storici che verranno eliminati"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking if job title {job_title_id} can be deleted: {e}")
            return False, "Errore durante il controllo delle dipendenze"
    
    def get_by_level(self, level: str = None) -> List[JobTitle]:
        """Get job titles by organizational level"""
        try:
            job_titles = self.get_all()
            
            if not level:
                return job_titles
            
            filtered = []
            for jt in job_titles:
                if jt.level_indicator.lower() == level.lower():
                    filtered.append(jt)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error fetching job titles by level {level}: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get job title statistics"""
        try:
            stats = {}
            
            # Total job titles
            stats['total_job_titles'] = self.count()
            
            # Active job titles (no end date or end date in future)
            from datetime import date
            today = date.today()
            
            active_query = """
            SELECT COUNT(*) as count 
            FROM job_titles 
            WHERE end_date IS NULL OR end_date > ?
            """
            row = self.db_manager.fetch_one(active_query, (today.isoformat(),))
            stats['active_job_titles'] = row['count'] if row else 0
            
            # Job titles with current assignments
            assigned_query = """
            SELECT COUNT(DISTINCT job_title_id) as count 
            FROM person_job_assignments 
            WHERE is_current = 1
            """
            row = self.db_manager.fetch_one(assigned_query)
            stats['assigned_job_titles'] = row['count'] if row else 0
            
            # Job titles by level
            level_query = """
            SELECT jt.name, COUNT(pja.id) as assignment_count
            FROM job_titles jt
            LEFT JOIN person_job_assignments pja ON jt.id = pja.job_title_id AND pja.is_current = 1
            GROUP BY jt.id, jt.name
            ORDER BY assignment_count DESC
            LIMIT 5
            """
            rows = self.db_manager.fetch_all(level_query)
            stats['top_assigned_roles'] = [dict(row) for row in rows]
            
            # Total units (all units are assignable for now)
            units_query = """
            SELECT COUNT(*) as total_assignable_units
            FROM units
            """
            row = self.db_manager.fetch_one(units_query)
            stats['total_assignable_units'] = row['total_assignable_units'] if row else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching job title statistics: {e}")
            return {}
    
    def get_available_for_unit(self, unit_id: int) -> List[JobTitle]:
        """Get job titles that can be assigned to a specific unit (all job titles for now)"""
        try:
            return self.get_all()
        except Exception as e:
            logger.error(f"Error fetching available job titles for unit {unit_id}: {e}")
            return []
    
    def get_unassigned_to_unit(self, unit_id: int) -> List[JobTitle]:
        """Get job titles that are NOT assignable to a specific unit (empty for now since all are assignable)"""
        try:
            return []  # All job titles are assignable to all units for now
        except Exception as e:
            logger.error(f"Error fetching unassigned job titles for unit {unit_id}: {e}")
            return []
    
    def bulk_assign_to_units(self, job_title_id: int, unit_ids: List[int]) -> bool:
        """Bulk assign job title to multiple units (placeholder for future implementation)"""
        logger.info(f"Bulk assigning job title {job_title_id} to units: {unit_ids}")
        return True  # All job titles are assignable to all units for now
    
    def remove_from_units(self, job_title_id: int, unit_ids: List[int]) -> bool:
        """Remove job title from multiple units (placeholder for future implementation)"""
        logger.info(f"Removing job title {job_title_id} from units: {unit_ids}")
        return True  # All job titles are assignable to all units for now
    
    def duplicate_job_title(self, job_title_id: int, new_name: str) -> Optional[JobTitle]:
        """Create a duplicate of an existing job title"""
        try:
            # Get original job title
            original = self.get_by_id(job_title_id)
            if not original:
                return None
            
            # Create new job title
            new_job_title = JobTitle(
                name=new_name,
                short_name=f"{original.short_name}_COPY" if original.short_name else None,
                aliases=original.aliases.copy(),
                start_date=original.start_date,
                end_date=original.end_date
            )
            
            # Create the job title
            created = self.create(new_job_title)
            
            # Copy assignable units (placeholder - all units are assignable for now)
            logger.info(f"Duplicated job title {job_title_id} as {created.id}")
            
            return created
            
        except Exception as e:
            logger.error(f"Error duplicating job title {job_title_id}: {e}")
            return None
    
    def get_alias_suggestions(self, partial_name: str) -> List[str]:
        """Get alias suggestions based on partial job title name"""
        try:
            # This could be enhanced with a more sophisticated suggestion system
            # For now, return some common aliases based on keywords
            suggestions = []
            name_lower = partial_name.lower()
            
            # Common role translations and abbreviations
            alias_map = {
                'chief': ['CEO', 'CTO', 'CFO', 'CIO', 'COO'],
                'manager': ['MGR', 'Responsabile', 'Gestore'],
                'director': ['DIR', 'Direttore'],
                'head': ['Responsabile', 'Capo'],
                'officer': ['Ufficiale', 'Responsabile'],
                'analyst': ['Analista'],
                'specialist': ['Specialista', 'Esperto'],
                'coordinator': ['Coordinatore', 'COORD'],
                'assistant': ['Assistente', 'ASS'],
                'senior': ['SR', 'Senior'],
                'junior': ['JR', 'Junior']
            }
            
            for keyword, aliases in alias_map.items():
                if keyword in name_lower:
                    suggestions.extend(aliases)
            
            return list(set(suggestions))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting alias suggestions for '{partial_name}': {e}")
            return []
    
    def get_searchable_fields(self) -> List[str]:
        """Get list of fields that can be searched for job titles"""
        return ["name", "short_name"]
    
    def _validate_for_create(self, job_title: JobTitle) -> None:
        """Perform additional validation before creating a job title"""
        # Check for duplicate names
        existing = self.db_manager.fetch_one(
            "SELECT id FROM job_titles WHERE name = ? AND id != ?",
            (job_title.name, job_title.id or -1)
        )
        if existing:
            from app.services.base import ServiceValidationException
            raise ServiceValidationException(f"Job title with name '{job_title.name}' already exists")
    
    def _validate_for_update(self, job_title: JobTitle, existing: JobTitle) -> None:
        """Perform additional validation before updating a job title"""
        # Check for duplicate names (excluding current job title)
        duplicate = self.db_manager.fetch_one(
            "SELECT id FROM job_titles WHERE name = ? AND id != ?",
            (job_title.name, job_title.id)
        )
        if duplicate:
            from app.services.base import ServiceValidationException
            raise ServiceValidationException(f"Job title with name '{job_title.name}' already exists")
    
    def _validate_for_delete(self, job_title: JobTitle) -> None:
        """Perform validation before deleting a job title"""
        can_delete, message = self.can_delete(job_title.id)
        if not can_delete:
            from app.services.base import ServiceIntegrityException
            raise ServiceIntegrityException(message)