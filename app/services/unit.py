"""
Unit service for business logic
"""

import logging
from typing import List, Optional, Dict, Any
from app.services.base import BaseService
from app.services.unit_type import UnitTypeService
from app.models.unit import Unit
from app.models.assignment import Assignment
from app.models.person import Person

logger = logging.getLogger(__name__)


class UnitService(BaseService):
    """Unit service class"""
    
    def __init__(self):
        super().__init__(Unit, "units")
    
    def get_list_query(self) -> str:
        """Get query for listing all units with computed fields"""
        return """
        SELECT * FROM unit_get_list_query
        """ 
        # """
        # SELECT u.*,
        #        p.name as parent_name,
        #        COUNT(DISTINCT c.id) as children_count,
        #        COUNT(DISTINCT pja.id) as person_count
        # FROM units u
        # LEFT JOIN units p ON u.parent_unit_id = p.id
        # LEFT JOIN units c ON c.parent_unit_id = u.id
        # LEFT JOIN person_job_assignments pja ON pja.unit_id = u.id AND pja.is_current = 1
        # GROUP BY u.id, u.name, u.short_name, u.unit_type_id, u.parent_unit_id, 
        #          u.start_date, u.end_date, u.aliases, 
        #          u.datetime_created, u.datetime_updated, p.name
        # ORDER BY u.unit_type_id, u.name
        # """
    
    def get_by_id_query(self) -> str:
        """Get query for fetching single unit by ID"""
        return """
        SELECT u.*,
               p.name as parent_name,
               COUNT(DISTINCT c.id) as children_count,
               COUNT(DISTINCT pja.id) as person_count
        FROM units u
        LEFT JOIN units p ON u.parent_unit_id = p.id
        LEFT JOIN units c ON c.parent_unit_id = u.id
        LEFT JOIN person_job_assignments pja ON pja.unit_id = u.id AND pja.is_current = 1
        WHERE u.id = ?
        GROUP BY u.id, u.name, u.short_name, u.unit_type_id, u.parent_unit_id, 
                 u.start_date, u.end_date, u.aliases, 
                 u.datetime_created, u.datetime_updated, p.name
        """
    
    def get_insert_query(self) -> str:
        return """
        INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    
    def get_update_query(self) -> str:
        return """
        UPDATE units 
        SET name = ?, short_name = ?, aliases = ?, unit_type_id = ?, 
            parent_unit_id = ?, start_date = ?, end_date = ?
        WHERE id = ?
        """
    
    def get_delete_query(self) -> str:
        return "DELETE FROM units WHERE id = ?"
    
    def model_to_insert_params(self, unit: Unit) -> tuple:
        """Convert unit to parameters for insert query"""
        return (
            unit.id,
            unit.name,
            unit.short_name,
            unit.aliases_json,
            unit.unit_type_id,
            unit.parent_unit_id,
            unit.start_date.isoformat() if unit.start_date else None,
            unit.end_date.isoformat() if unit.end_date else None
        )
    
    def model_to_update_params(self, unit: Unit) -> tuple:
        """Convert unit to parameters for update query"""
        return (
            unit.name,
            unit.short_name,
            unit.aliases_json,
            unit.unit_type_id,
            unit.parent_unit_id,
            unit.start_date.isoformat() if unit.start_date else None,
            unit.end_date.isoformat() if unit.end_date else None,
            unit.id
        )
    
    def get_root_units(self) -> List[Unit]:
        """Get all root units (no parent)"""
        try:
            query = """
            SELECT u.*,
                   ut.name as unit_type,
                   p.name as parent_name,
                   COUNT(DISTINCT c.id) as children_count,
                   COUNT(DISTINCT pja.id) as person_count
            FROM units u
            JOIN unit_types ut ON u.unit_type_id = ut.id
            LEFT JOIN units p ON u.parent_unit_id = p.id
            LEFT JOIN units c ON c.parent_unit_id = u.id
            LEFT JOIN person_job_assignments pja ON pja.unit_id = u.id AND pja.is_current = 1
            WHERE u.parent_unit_id IS NULL OR u.parent_unit_id = -1
            GROUP BY u.id, u.name, u.short_name, ut.name, u.parent_unit_id, 
                     u.start_date, u.end_date, u.aliases, 
                     u.datetime_created, u.datetime_updated, p.name
            ORDER BY ut.name, u.name
            """
            rows = self.db_manager.fetch_all(query)
            return [Unit.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching root units: {e}")
            return []
    
    # def get_assigned_persons(self, unit_id: int) -> List[Person]:
    #     """Get all assignments of a unit"""
    #     try:
    #         query = """
    #         SELECT p.*
    #         FROM units u
    #         LEFT JOIN person_job_assignments pja ON pja.unit_id = u.id AND pja.is_current = 1
    #         LEFT JOIN persons p ON pja.person_id = p.id
    #         WHERE u.id = ?
    #         ORDER BY p.name
    #         """
    #         rows = self.db_manager.fetch_all(query, (unit_id,))
    #         return [Person.from_sqlite_row(row) for row in rows]
    #     except Exception as e:
    #         logger.error(f"Error fetching assignments for unit {unit_id}: {e}")
    #         return []

    def get_children(self, parent_id: int) -> List[Unit]:
        """Get all children of a unit"""
        try:
            query = """
            SELECT u.*,
                   p.name as parent_name,
                   COUNT(DISTINCT c.id) as children_count,
                   COUNT(DISTINCT pja.id) as person_count
            FROM units u
            LEFT JOIN units p ON u.parent_unit_id = p.id
            LEFT JOIN units c ON c.parent_unit_id = u.id
            LEFT JOIN person_job_assignments pja ON pja.unit_id = u.id AND pja.is_current = 1
            WHERE u.parent_unit_id = ?
            GROUP BY u.id, u.name, u.short_name, u.unit_type_id, u.parent_unit_id, 
                     u.start_date, u.end_date, u.aliases, 
                     u.datetime_created, u.datetime_updated, p.name
            ORDER BY u.unit_type_id, u.name
            """
            rows = self.db_manager.fetch_all(query, (parent_id,))
            return [Unit.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching children for unit {parent_id}: {e}")
            return []
    
    def get_hierarchy(self) -> List[Dict[str, Any]]:
        """Get complete unit hierarchy"""
        try:
            query = """
            WITH RECURSIVE unit_tree AS (
                SELECT id, name, short_name, unit_type_id, parent_unit_id,
                       0 as level,
                       CAST(id AS TEXT) as path,
                       name as full_path
                FROM units 
                WHERE parent_unit_id IS NULL OR parent_unit_id = -1
                
                UNION ALL
                
                SELECT u.id, u.name, u.short_name, u.unit_type_id, u.parent_unit_id,
                       ut.level + 1,
                       ut.path || '/' || CAST(u.id AS TEXT),
                       ut.full_path || ' > ' || u.name
                FROM units u
                JOIN unit_tree ut ON u.parent_unit_id = ut.id
            )
            SELECT * FROM unit_tree ORDER BY path
            """
            tree_query = "select * from get_complete_tree order by path"
            rows = self.db_manager.fetch_all(query, ('YOUSHALLPASS',))
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching unit hierarchy: {e}")
            return []
    
    def get_hierarchy_stats(self) -> List[Dict[str, Any]]:
        """Get unit hierarchy with statistics"""
        try:
            query = """
            SELECT uh.*, 
                   COUNT(pja.id) as person_count
            FROM units_hierarchy uh
            LEFT JOIN person_job_assignments pja ON uh.id = pja.unit_id AND pja.is_current = 1
            GROUP BY uh.id, uh.name, uh.short_name, uh.unit_type, uh.unit_type_short, uh.parent_unit_id, 
                     uh.level, uh.path, uh.full_path
            ORDER BY uh.path
            """
            rows = self.db_manager.fetch_all(query)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching hierarchy stats: {e}")
            return []
    
    def can_delete(self, unit_id: int) -> tuple[bool, str]:
        """Check if unit can be deleted"""
        try:
            # Check for children
            children = self.get_children(unit_id)
            if children:
                return False, f"Unit has {len(children)} child units"
            
            # Check for current assignments
            query = """
            SELECT COUNT(*) as count 
            FROM person_job_assignments 
            WHERE unit_id = ? AND is_current = 1
            """
            row = self.db_manager.fetch_one(query, (unit_id,))
            if row and row['count'] > 0:
                return False, f"Unit has {row['count']} current assignments"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking if unit {unit_id} can be deleted: {e}")
            return False, "Error checking dependencies"
    
    def get_available_parents(self, unit_id: Optional[int] = None) -> List[Unit]:
        """Get list of units that can be parents (excluding self and descendants)"""
        try:
            if unit_id:
                # Exclude self and descendants
                query = """
                WITH RECURSIVE descendants AS (
                    SELECT id FROM units WHERE id = ?
                    UNION ALL
                    SELECT u.id FROM units u
                    JOIN descendants d ON u.parent_unit_id = d.id
                )
                SELECT u.*, p.name as parent_name,
                       0 as children_count, 0 as person_count
                FROM units u
                LEFT JOIN units p ON u.parent_unit_id = p.id
                WHERE u.id NOT IN (SELECT id FROM descendants)
                ORDER BY u.name
                """
                rows = self.db_manager.fetch_all(query, (unit_id,))
            else:
                rows = self.db_manager.fetch_all(
                    "SELECT *, NULL as parent_name, 0 as children_count, 0 as person_count FROM units ORDER BY name"
                )
            
            return [Unit.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching available parents: {e}")
            return []
    
    def get_searchable_fields(self) -> List[str]:
        """Get list of fields that can be searched for units"""
        return ["name", "short_name", "type"]
    
    def _validate_for_create(self, unit: Unit) -> None:
        """Perform additional validation before creating a unit"""
        # Check for duplicate names
        existing = self.db_manager.fetch_one(
            "SELECT id FROM units WHERE name = ? AND id != ?",
            (unit.name, unit.id or -1)
        )
        if existing:
            from app.services.base import ServiceValidationException
            raise ServiceValidationException(f"Unit with name '{unit.name}' already exists")
        
        # Validate unit type exists if specified
        if unit.unit_type_id and unit.unit_type_id != -1:
            type = UnitTypeService().get_by_id(unit.unit_type_id)
            if not type:
                from app.services.base import ServiceValidationException
                raise ServiceValidationException(f"Unit type with ID {unit.unit_type_id} does not exist")

        # Validate parent unit exists if specified
        if unit.parent_unit_id and unit.parent_unit_id != -1:
            parent = self.get_by_id(unit.parent_unit_id)
            if not parent:
                from app.services.base import ServiceValidationException
                raise ServiceValidationException(f"Parent unit with ID {unit.parent_unit_id} does not exist")

        # Validate parent unit exists if specified
        if unit.parent_unit_id and unit.parent_unit_id != -1:
            parent = self.get_by_id(unit.parent_unit_id)
            if not parent:
                from app.services.base import ServiceValidationException
                raise ServiceValidationException(f"Parent unit with ID {unit.parent_unit_id} does not exist")
    
    def _validate_for_update(self, unit: Unit, existing: Unit) -> None:
        """Perform additional validation before updating a unit"""
        # Check for duplicate names (excluding current unit)
        duplicate = self.db_manager.fetch_one(
            "SELECT id FROM units WHERE name = ? AND id != ?",
            (unit.name, unit.id)
        )
        if duplicate:
            from app.services.base import ServiceValidationException
            raise ServiceValidationException(f"Unit with name '{unit.name}' already exists")
        
        # Validate parent unit exists and prevent circular references
        if unit.parent_unit_id and unit.parent_unit_id != -1:
            if unit.parent_unit_id == unit.id:
                from app.services.base import ServiceValidationException
                raise ServiceValidationException("Unit cannot be its own parent")
            
            parent = self.get_by_id(unit.parent_unit_id)
            if not parent:
                from app.services.base import ServiceValidationException
                raise ServiceValidationException(f"Parent unit with ID {unit.parent_unit_id} does not exist")
    
    def _validate_for_delete(self, unit: Unit) -> None:
        """Perform validation before deleting a unit"""
        can_delete, message = self.can_delete(unit.id)
        if not can_delete:
            from app.services.base import ServiceIntegrityException
            raise ServiceIntegrityException(message)