"""
Dependency Resolution System for Import/Export Operations

This module provides dependency graph management and topological sorting
for entity processing order during import/export operations.
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Exception raised for dependency resolution errors"""
    pass


class CircularDependencyError(DependencyError):
    """Exception raised when circular dependencies are detected"""
    pass


@dataclass
class EntityDependency:
    """Represents a dependency relationship between entities"""
    entity_type: str
    depends_on: str
    foreign_key_field: str
    is_optional: bool = False
    description: str = ""


@dataclass
class ForeignKeyMapping:
    """Represents a foreign key mapping for entity resolution"""
    source_field: str
    target_entity: str
    target_field: str = "id"
    is_required: bool = True
    allow_temporary_ids: bool = True


class DependencyResolver:
    """
    Handles dependency resolution and topological sorting for entity processing.
    
    This class manages the dependency graph for all entity types in the system
    and provides methods for determining processing order and resolving foreign keys.
    """
    
    def __init__(self):
        """Initialize the dependency resolver with entity mappings"""
        self._dependency_graph = self._build_dependency_graph()
        self._foreign_key_mappings = self._build_foreign_key_mappings()
        self._temporary_id_mappings: Dict[str, Dict[str, int]] = {}
    
    def _build_dependency_graph(self) -> Dict[str, List[EntityDependency]]:
        """
        Build the complete dependency graph for all entity types.
        
        Returns:
            Dictionary mapping entity types to their dependencies
        """
        return {
            'unit_types': [
                # Unit types have no dependencies - they are root entities
            ],
            'unit_type_themes': [
                # Unit type themes have no dependencies - they are independent
            ],
            'units': [
                EntityDependency(
                    entity_type='units',
                    depends_on='unit_types',
                    foreign_key_field='unit_type_id',
                    is_optional=False,
                    description='Units must reference a valid unit type'
                ),
                EntityDependency(
                    entity_type='units',
                    depends_on='units',
                    foreign_key_field='parent_unit_id',
                    is_optional=True,
                    description='Units can have a parent unit (self-referential)'
                )
            ],
            'job_titles': [
                # Job titles have no dependencies - they are independent entities
            ],
            'persons': [
                # Persons have no dependencies - they are independent entities
            ],
            'assignments': [
                EntityDependency(
                    entity_type='assignments',
                    depends_on='persons',
                    foreign_key_field='person_id',
                    is_optional=False,
                    description='Assignments must reference a valid person'
                ),
                EntityDependency(
                    entity_type='assignments',
                    depends_on='units',
                    foreign_key_field='unit_id',
                    is_optional=False,
                    description='Assignments must reference a valid unit'
                ),
                EntityDependency(
                    entity_type='assignments',
                    depends_on='job_titles',
                    foreign_key_field='job_title_id',
                    is_optional=False,
                    description='Assignments must reference a valid job title'
                )
            ]
        }
    
    def _build_foreign_key_mappings(self) -> Dict[str, List[ForeignKeyMapping]]:
        """
        Build foreign key mappings for all entity types.
        
        Returns:
            Dictionary mapping entity types to their foreign key mappings
        """
        return {
            'unit_types': [
                ForeignKeyMapping(
                    source_field='theme_id',
                    target_entity='unit_type_themes',
                    target_field='id',
                    is_required=False,
                    allow_temporary_ids=True
                )
            ],
            'unit_type_themes': [
                # No foreign keys
            ],
            'units': [
                ForeignKeyMapping(
                    source_field='unit_type_id',
                    target_entity='unit_types',
                    target_field='id',
                    is_required=True,
                    allow_temporary_ids=True
                ),
                ForeignKeyMapping(
                    source_field='parent_unit_id',
                    target_entity='units',
                    target_field='id',
                    is_required=False,
                    allow_temporary_ids=True
                )
            ],
            'job_titles': [
                # No foreign keys
            ],
            'persons': [
                # No foreign keys
            ],
            'assignments': [
                ForeignKeyMapping(
                    source_field='person_id',
                    target_entity='persons',
                    target_field='id',
                    is_required=True,
                    allow_temporary_ids=True
                ),
                ForeignKeyMapping(
                    source_field='unit_id',
                    target_entity='units',
                    target_field='id',
                    is_required=True,
                    allow_temporary_ids=True
                ),
                ForeignKeyMapping(
                    source_field='job_title_id',
                    target_entity='job_titles',
                    target_field='id',
                    is_required=True,
                    allow_temporary_ids=True
                )
            ]
        }
    
    def get_processing_order(self, entity_types: Optional[List[str]] = None) -> List[str]:
        """
        Get the correct processing order for entity types using topological sort.
        
        Args:
            entity_types: Optional list of specific entity types to order.
                         If None, returns order for all entity types.
        
        Returns:
            List of entity types in dependency order
            
        Raises:
            CircularDependencyError: If circular dependencies are detected
            DependencyError: If invalid entity types are provided
        """
        if entity_types is None:
            entity_types = list(self._dependency_graph.keys())
        
        # Validate entity types
        invalid_types = set(entity_types) - set(self._dependency_graph.keys())
        if invalid_types:
            raise DependencyError(f"Invalid entity types: {invalid_types}")
        
        # Build adjacency list for the specified entity types
        graph = {}
        in_degree = {}
        
        for entity_type in entity_types:
            graph[entity_type] = []
            in_degree[entity_type] = 0
        
        # Add edges based on dependencies
        for entity_type in entity_types:
            dependencies = self._dependency_graph[entity_type]
            for dep in dependencies:
                if dep.depends_on in entity_types:
                    # Skip self-referential dependencies for topological sort
                    # They will be handled separately during processing
                    if dep.depends_on != entity_type:
                        graph[dep.depends_on].append(entity_type)
                        in_degree[entity_type] += 1
        
        # Perform topological sort using Kahn's algorithm
        result = []
        queue = [entity for entity in entity_types if in_degree[entity] == 0]
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Remove edges from current node
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for circular dependencies
        if len(result) != len(entity_types):
            remaining = set(entity_types) - set(result)
            raise CircularDependencyError(
                f"Circular dependency detected among entities: {remaining}"
            )
        
        logger.info(f"Processing order determined: {result}")
        return result
    
    def detect_circular_dependencies(self, entity_types: Optional[List[str]] = None) -> List[List[str]]:
        """
        Detect circular dependencies in the dependency graph.
        
        Args:
            entity_types: Optional list of specific entity types to check.
                         If None, checks all entity types.
        
        Returns:
            List of cycles found (each cycle is a list of entity types)
        """
        if entity_types is None:
            entity_types = list(self._dependency_graph.keys())
        
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            dependencies = self._dependency_graph.get(node, [])
            for dep in dependencies:
                if dep.depends_on in entity_types:
                    # Skip self-referential dependencies - they're not circular in the problematic sense
                    if dep.depends_on == node:
                        continue
                        
                    if dep.depends_on in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(dep.depends_on)
                        cycle = path[cycle_start:] + [dep.depends_on]
                        cycles.append(cycle)
                    elif dep.depends_on not in visited:
                        dfs(dep.depends_on, path.copy())
            
            rec_stack.remove(node)
        
        for entity_type in entity_types:
            if entity_type not in visited:
                dfs(entity_type, [])
        
        return cycles
    
    def get_dependencies(self, entity_type: str) -> List[EntityDependency]:
        """
        Get all dependencies for a specific entity type.
        
        Args:
            entity_type: The entity type to get dependencies for
            
        Returns:
            List of dependencies for the entity type
            
        Raises:
            DependencyError: If entity type is invalid
        """
        if entity_type not in self._dependency_graph:
            raise DependencyError(f"Invalid entity type: {entity_type}")
        
        return self._dependency_graph[entity_type].copy()
    
    def get_foreign_key_mappings(self, entity_type: str) -> List[ForeignKeyMapping]:
        """
        Get foreign key mappings for a specific entity type.
        
        Args:
            entity_type: The entity type to get mappings for
            
        Returns:
            List of foreign key mappings for the entity type
            
        Raises:
            DependencyError: If entity type is invalid
        """
        if entity_type not in self._foreign_key_mappings:
            raise DependencyError(f"Invalid entity type: {entity_type}")
        
        return self._foreign_key_mappings[entity_type].copy()
    
    def validate_dependencies_exist(self, data: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """
        Validate that all required dependencies exist in the provided data.
        
        Args:
            data: Dictionary mapping entity types to lists of records
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        for entity_type, records in data.items():
            if entity_type not in self._dependency_graph:
                errors.append(f"Unknown entity type: {entity_type}")
                continue
            
            dependencies = self._dependency_graph[entity_type]
            for dep in dependencies:
                if not dep.is_optional and dep.depends_on not in data:
                    errors.append(
                        f"Entity type '{entity_type}' requires '{dep.depends_on}' "
                        f"but it's not present in the data"
                    )
        
        return errors
    
    def get_entity_hierarchy(self) -> Dict[str, int]:
        """
        Get the hierarchy level for each entity type (0 = no dependencies).
        
        Returns:
            Dictionary mapping entity types to their hierarchy levels
        """
        processing_order = self.get_processing_order()
        return {entity_type: level for level, entity_type in enumerate(processing_order)}
    
    def is_self_referential(self, entity_type: str) -> bool:
        """
        Check if an entity type has self-referential dependencies.
        
        Args:
            entity_type: The entity type to check
            
        Returns:
            True if the entity type references itself
        """
        dependencies = self._dependency_graph.get(entity_type, [])
        return any(dep.depends_on == entity_type for dep in dependencies)
    
    def get_dependents(self, entity_type: str) -> List[str]:
        """
        Get all entity types that depend on the specified entity type.
        
        Args:
            entity_type: The entity type to find dependents for
            
        Returns:
            List of entity types that depend on the specified type
        """
        dependents = []
        
        for ent_type, dependencies in self._dependency_graph.items():
            for dep in dependencies:
                if dep.depends_on == entity_type and ent_type != entity_type:
                    dependents.append(ent_type)
        
        return list(set(dependents))  # Remove duplicates
    
    def clear_temporary_mappings(self) -> None:
        """Clear all temporary ID mappings"""
        self._temporary_id_mappings.clear()
        logger.debug("Cleared temporary ID mappings")
    
    def add_temporary_mapping(self, entity_type: str, temp_id: str, real_id: int) -> None:
        """
        Add a temporary ID to real ID mapping.
        
        Args:
            entity_type: The entity type
            temp_id: The temporary ID (usually from import data)
            real_id: The real database ID
        """
        if entity_type not in self._temporary_id_mappings:
            self._temporary_id_mappings[entity_type] = {}
        
        self._temporary_id_mappings[entity_type][temp_id] = real_id
        logger.debug(f"Added temporary mapping: {entity_type}[{temp_id}] -> {real_id}")
    
    def resolve_temporary_id(self, entity_type: str, temp_id: str) -> Optional[int]:
        """
        Resolve a temporary ID to a real database ID.
        
        Args:
            entity_type: The entity type
            temp_id: The temporary ID to resolve
            
        Returns:
            The real database ID, or None if not found
        """
        return self._temporary_id_mappings.get(entity_type, {}).get(temp_id)
    
    def get_temporary_mappings(self, entity_type: str) -> Dict[str, int]:
        """
        Get all temporary mappings for an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            Dictionary mapping temporary IDs to real IDs
        """
        return self._temporary_id_mappings.get(entity_type, {}).copy()


class ForeignKeyResolver:
    """
    Handles foreign key resolution during import operations.
    
    This class manages the resolution of foreign key references, including
    temporary ID mapping and validation of references before processing.
    """
    
    def __init__(self, dependency_resolver: DependencyResolver):
        """
        Initialize the foreign key resolver.
        
        Args:
            dependency_resolver: The dependency resolver instance
        """
        self.dependency_resolver = dependency_resolver
        self._existing_entity_cache: Dict[str, Dict[Any, int]] = {}
    
    def resolve_foreign_keys(self, entity_type: str, record: Dict[str, Any], 
                           created_mappings: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """
        Resolve foreign key references in a record using created record mappings.
        
        Args:
            entity_type: The type of entity being processed
            record: The record data to resolve foreign keys for
            created_mappings: Dictionary of temporary ID to real ID mappings
            
        Returns:
            Record with resolved foreign key references
            
        Raises:
            DependencyError: If required foreign keys cannot be resolved
        """
        resolved_record = record.copy()
        fk_mappings = self.dependency_resolver.get_foreign_key_mappings(entity_type)
        
        for fk_mapping in fk_mappings:
            source_value = resolved_record.get(fk_mapping.source_field)
            
            # Skip if field is not present or is None
            if source_value is None:
                if fk_mapping.is_required:
                    raise DependencyError(
                        f"Required foreign key '{fk_mapping.source_field}' is missing "
                        f"in {entity_type} record"
                    )
                continue
            
            # Try to resolve the foreign key
            resolved_id = self._resolve_foreign_key_value(
                source_value, 
                fk_mapping, 
                created_mappings
            )
            
            if resolved_id is None:
                if fk_mapping.is_required:
                    raise DependencyError(
                        f"Cannot resolve required foreign key '{fk_mapping.source_field}' "
                        f"with value '{source_value}' in {entity_type} record"
                    )
                # For optional foreign keys, keep the original value or set to None
                resolved_record[fk_mapping.source_field] = None
            else:
                resolved_record[fk_mapping.source_field] = resolved_id
        
        return resolved_record
    
    def _resolve_foreign_key_value(self, value: Any, fk_mapping: ForeignKeyMapping, 
                                 created_mappings: Dict[str, Dict[str, int]]) -> Optional[int]:
        """
        Resolve a single foreign key value.
        
        Args:
            value: The foreign key value to resolve
            fk_mapping: The foreign key mapping configuration
            created_mappings: Dictionary of temporary ID to real ID mappings
            
        Returns:
            The resolved database ID, or None if not found
        """
        target_entity = fk_mapping.target_entity
        
        # If it's already an integer, check if it exists in database
        if isinstance(value, int):
            if self._validate_existing_id(target_entity, value):
                return value
            return None
        
        # Convert to string for temporary ID lookup
        str_value = str(value)
        
        # Try to resolve from temporary mappings first
        if target_entity in created_mappings:
            temp_mapping = created_mappings[target_entity].get(str_value)
            if temp_mapping is not None:
                return temp_mapping
        
        # Try to resolve from dependency resolver's temporary mappings
        resolved_id = self.dependency_resolver.resolve_temporary_id(target_entity, str_value)
        if resolved_id is not None:
            return resolved_id
        
        # Try to parse as integer and validate
        try:
            int_value = int(str_value)
            if self._validate_existing_id(target_entity, int_value):
                return int_value
        except (ValueError, TypeError):
            pass
        
        # Try to find by natural key (name, etc.)
        natural_key_id = self._resolve_by_natural_key(target_entity, str_value)
        if natural_key_id is not None:
            return natural_key_id
        
        return None
    
    def _validate_existing_id(self, entity_type: str, entity_id: int) -> bool:
        """
        Validate that an entity ID exists in the database.
        
        Args:
            entity_type: The entity type to check
            entity_id: The ID to validate
            
        Returns:
            True if the ID exists, False otherwise
        """
        # Use cache to avoid repeated database queries
        if entity_type not in self._existing_entity_cache:
            self._existing_entity_cache[entity_type] = {}
        
        if entity_id in self._existing_entity_cache[entity_type]:
            return self._existing_entity_cache[entity_type][entity_id] is not None
        
        # This would need to be implemented with actual database access
        # For now, we'll assume the ID exists if it's positive
        # In a real implementation, this would query the database
        exists = entity_id > 0
        self._existing_entity_cache[entity_type][entity_id] = entity_id if exists else None
        
        return exists
    
    def _resolve_by_natural_key(self, entity_type: str, value: str) -> Optional[int]:
        """
        Try to resolve a foreign key by natural key (name field).
        
        Args:
            entity_type: The entity type to search
            value: The natural key value to search for
            
        Returns:
            The database ID if found, None otherwise
        """
        # This would need to be implemented with actual database access
        # For now, we'll return None to indicate not found
        # In a real implementation, this would query the database by name
        return None
    
    def validate_foreign_key_references(self, entity_type: str, records: List[Dict[str, Any]], 
                                      available_entities: Dict[str, Set[Any]]) -> List[str]:
        """
        Validate that all foreign key references can be resolved.
        
        Args:
            entity_type: The entity type being validated
            records: List of records to validate
            available_entities: Dictionary of available entity IDs by type
            
        Returns:
            List of validation error messages
        """
        errors = []
        fk_mappings = self.dependency_resolver.get_foreign_key_mappings(entity_type)
        
        for i, record in enumerate(records):
            for fk_mapping in fk_mappings:
                source_value = record.get(fk_mapping.source_field)
                
                # Skip if field is not present or is None
                if source_value is None:
                    if fk_mapping.is_required:
                        errors.append(
                            f"Record {i+1}: Required foreign key '{fk_mapping.source_field}' is missing"
                        )
                    continue
                
                # Check if the reference can be resolved
                target_entity = fk_mapping.target_entity
                available_ids = available_entities.get(target_entity, set())
                
                # Convert value to string for comparison
                str_value = str(source_value)
                
                # Check if it's in available entities (from current import)
                if str_value in available_ids:
                    continue
                
                # Check if it's a valid integer ID that might exist in database
                try:
                    int_value = int(str_value)
                    if int_value > 0:
                        # Assume existing database IDs are valid for now
                        # In real implementation, would validate against database
                        continue
                except (ValueError, TypeError):
                    pass
                
                # If we get here, the reference cannot be resolved
                errors.append(
                    f"Record {i+1}: Cannot resolve foreign key '{fk_mapping.source_field}' "
                    f"with value '{source_value}' for entity type '{target_entity}'"
                )
        
        return errors
    
    def build_reference_map(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Set[Any]]:
        """
        Build a map of available entity references from import data.
        
        Args:
            data: Dictionary mapping entity types to lists of records
            
        Returns:
            Dictionary mapping entity types to sets of available IDs
        """
        reference_map = {}
        
        for entity_type, records in data.items():
            available_ids = set()
            
            for record in records:
                # Add the record's ID if present
                if 'id' in record and record['id'] is not None:
                    available_ids.add(str(record['id']))
                
                # Add natural keys (name fields) for reference resolution
                for field_name in ['name', 'short_name']:
                    if field_name in record and record[field_name]:
                        available_ids.add(str(record[field_name]))
            
            reference_map[entity_type] = available_ids
        
        return reference_map
    
    def clear_cache(self) -> None:
        """Clear the existing entity cache"""
        self._existing_entity_cache.clear()
        logger.debug("Cleared foreign key resolver cache")
    
    def preload_existing_entities(self, entity_types: List[str]) -> None:
        """
        Preload existing entities from database to improve resolution performance.
        
        Args:
            entity_types: List of entity types to preload
        """
        # This would be implemented with actual database access
        # For now, we'll just initialize the cache
        for entity_type in entity_types:
            if entity_type not in self._existing_entity_cache:
                self._existing_entity_cache[entity_type] = {}
        
        logger.debug(f"Preloaded existing entities for types: {entity_types}")
    
    def get_resolution_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about foreign key resolution operations.
        
        Returns:
            Dictionary containing resolution statistics
        """
        stats = {
            'cached_entities': {
                entity_type: len(cache) 
                for entity_type, cache in self._existing_entity_cache.items()
            },
            'temporary_mappings': {
                entity_type: len(mappings)
                for entity_type, mappings in self.dependency_resolver._temporary_id_mappings.items()
            }
        }
        
        return stats