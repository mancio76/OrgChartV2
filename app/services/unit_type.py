"""
Unit Type service
"""

import logging
from typing import List, Optional, Tuple
from app.services.base import BaseService
from app.models.unit_type import UnitType
from app.database import DatabaseManager

logger = logging.getLogger(__name__)

class UnitTypeService(BaseService):
    """Service for managing unit types"""

    def __init__(self):
        super().__init__(UnitType, "unit_types")

    def get_list_query(self) -> str:
        """Get query for listing unit types with statistics"""
        return """
        SELECT ut.*, 
               COUNT(u.id) as units_count
        FROM unit_types ut
        LEFT JOIN units u ON ut.id = u.unit_type_id
        GROUP BY ut.id, ut.name, ut.aliases, ut.datetime_created, ut.datetime_updated
        ORDER BY ut.name
        """

    def get_by_id_query(self) -> str:
        """Get query for fetching unit type by ID with statistics"""
        return """
        SELECT ut.*, 
               COUNT(u.id) as units_count
        FROM unit_types ut
        LEFT JOIN units u ON ut.id = u.unit_type_id
        WHERE ut.id = ?
        GROUP BY ut.id, ut.name, ut.aliases, ut.datetime_created, ut.datetime_updated
        """

    def get_insert_query(self) -> str:
        """Get query for inserting unit type"""
        return """
        INSERT INTO unit_types (name, aliases, datetime_created, datetime_updated)
        VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """

    def get_update_query(self) -> str:
        """Get query for updating unit type"""
        return """
        UPDATE unit_types 
        SET name = ?, aliases = ?, datetime_updated = CURRENT_TIMESTAMP
        WHERE id = ?
        """

    def get_delete_query(self) -> str:
        """Get query for deleting unit type"""
        return "DELETE FROM unit_types WHERE id = ?"

    def model_to_insert_params(self, unit_type: UnitType) -> tuple:
        """Convert unit type to parameters for insert query"""
        return (
            unit_type.id,
            unit_type.name,
            unit_type.short_name,
            unit_type.aliases_json,
            unit_type.level
        )

    def model_to_update_params(self, unit_type: UnitType) -> tuple:
        """Convert unit type to parameters for update query"""
        return (
            unit_type.name,
            unit_type.short_name,
            unit_type.aliases_json,
            unit_type.level,
            unit_type.id
        )

    def create(self, unit_type: UnitType) -> UnitType:
        """Create new unit type"""
        try:
            # Validate unit type
            validation_errors = unit_type.validate()
            if validation_errors:
                from app.models.base import ModelValidationException
                raise ModelValidationException(validation_errors)

            db_manager = DatabaseManager()
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    self.get_insert_query(),
                    (unit_type.name, unit_type.aliases_json)
                )
                unit_type.id = cursor.lastrowid
                conn.commit()

                logger.info(f"Created unit type: {unit_type.name} (ID: {unit_type.id})")
                return self.get_by_id(unit_type.id)
        except Exception as e:
            logger.error(f"Error creating unit type: {e}")
            raise

    def update(self, unit_type: UnitType) -> UnitType:
        """Update existing unit type"""
        try:
            # Validate unit type
            validation_errors = unit_type.validate()
            if validation_errors:
                from app.models.base import ModelValidationException
                raise ModelValidationException(validation_errors)

            db_manager = DatabaseManager()
            with db_manager.get_connection() as conn:
                conn.execute(
                    self.get_update_query(),
                    (unit_type.name, unit_type.aliases_json, unit_type.id)
                )
                conn.commit()

                logger.info(f"Updated unit type: {unit_type.name} (ID: {unit_type.id})")
                return self.get_by_id(unit_type.id)

        except Exception as e:
            logger.error(f"Error updating unit type {unit_type.id}: {e}")
            raise

    def can_delete(self, unit_type_id: int) -> Tuple[bool, str]:
        """Check if unit type can be deleted"""
        try:
            db_manager = DatabaseManager()
            with db_manager.get_connection() as conn:
                # Check if unit type has associated units
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM units WHERE unit_type_id = ?",
                    (unit_type_id,)
                )
                result = cursor.fetchone()
                units_count = result['count'] if result else 0

                if units_count > 0:
                    return False, f"Cannot delete unit type: {units_count} units are using this type"

                return True, ""

        except Exception as e:
            logger.error(f"Error checking if unit type {unit_type_id} can be deleted: {e}")
            return False, "Error checking unit type dependencies"

    def get_units_by_type(self, unit_type_id: int) -> List:
        """Get all units of a specific type"""
        try:
            db_manager = DatabaseManager()
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT u.*, ut.name as unit_type_name
                    FROM units u
                    JOIN unit_types ut ON u.unit_type_id = ut.id
                    WHERE u.unit_type_id = ?
                    ORDER BY u.name
                """, (unit_type_id,))
                from app.models.unit import Unit
                return [Unit.from_sqlite_row(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting units for type {unit_type_id}: {e}")
            return []

    def get_statistics(self) -> dict:
        """Get unit type statistics"""
        try:
            db_manager = DatabaseManager()
            with db_manager.get_connection() as conn:
                # Get unit type counts
                cursor = conn.execute("""
                    SELECT ut.name, ut.id, COUNT(u.id) as units_count
                    FROM unit_types ut
                    LEFT JOIN units u ON ut.id = u.unit_type_id
                    GROUP BY ut.id, ut.name
                    ORDER BY units_count DESC
                """)

                type_stats = []
                total_units = 0
                for row in cursor.fetchall():
                    units_count = row['units_count']
                    total_units += units_count
                    type_stats.append({
                        'id': row['id'],
                        'name': row['name'],
                        'units_count': units_count
                    })

                return {
                    'total_types': len(type_stats),
                    'total_units': total_units,
                    'type_distribution': type_stats
                }

        except Exception as e:
            logger.error(f"Error getting unit type statistics: {e}")
            return {
                'total_types': 0,
                'total_units': 0,
                'type_distribution': []
            }
