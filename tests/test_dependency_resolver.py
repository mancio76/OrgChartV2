"""
Tests for the dependency resolution system
"""

import pytest
from app.services.dependency_resolver import (
    DependencyResolver, 
    ForeignKeyResolver,
    EntityDependency,
    ForeignKeyMapping,
    DependencyError,
    CircularDependencyError
)


class TestDependencyResolver:
    """Test cases for DependencyResolver class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.resolver = DependencyResolver()
    
    def test_get_processing_order_all_entities(self):
        """Test getting processing order for all entities"""
        order = self.resolver.get_processing_order()
        
        # Verify all entity types are included
        expected_entities = {'unit_types', 'unit_type_themes', 'units', 'job_titles', 'persons', 'assignments'}
        assert set(order) == expected_entities
        
        # Verify dependency order is correct
        unit_types_idx = order.index('unit_types')
        units_idx = order.index('units')
        assignments_idx = order.index('assignments')
        persons_idx = order.index('persons')
        job_titles_idx = order.index('job_titles')
        
        # Units must come after unit_types
        assert unit_types_idx < units_idx
        
        # Assignments must come after persons, units, and job_titles
        assert persons_idx < assignments_idx
        assert units_idx < assignments_idx
        assert job_titles_idx < assignments_idx
    
    def test_get_processing_order_subset(self):
        """Test getting processing order for a subset of entities"""
        subset = ['assignments', 'persons', 'units']
        order = self.resolver.get_processing_order(subset)
        
        # Verify only requested entities are included
        assert set(order) == set(subset)
        
        # Verify dependency order is maintained
        persons_idx = order.index('persons')
        units_idx = order.index('units')
        assignments_idx = order.index('assignments')
        
        assert persons_idx < assignments_idx
        assert units_idx < assignments_idx
    
    def test_get_processing_order_invalid_entity(self):
        """Test error handling for invalid entity types"""
        with pytest.raises(DependencyError) as exc_info:
            self.resolver.get_processing_order(['invalid_entity'])
        
        assert "Invalid entity types" in str(exc_info.value)
        assert "invalid_entity" in str(exc_info.value)
    
    def test_detect_circular_dependencies_none(self):
        """Test circular dependency detection when none exist"""
        cycles = self.resolver.detect_circular_dependencies()
        assert cycles == []
    
    def test_get_dependencies(self):
        """Test getting dependencies for specific entity types"""
        # Test entity with no dependencies
        unit_type_deps = self.resolver.get_dependencies('unit_types')
        assert unit_type_deps == []
        
        # Test entity with dependencies
        assignment_deps = self.resolver.get_dependencies('assignments')
        assert len(assignment_deps) == 3
        
        dep_entities = {dep.depends_on for dep in assignment_deps}
        assert dep_entities == {'persons', 'units', 'job_titles'}
    
    def test_get_dependencies_invalid_entity(self):
        """Test error handling for invalid entity type"""
        with pytest.raises(DependencyError):
            self.resolver.get_dependencies('invalid_entity')
    
    def test_get_foreign_key_mappings(self):
        """Test getting foreign key mappings"""
        # Test entity with no foreign keys
        person_fks = self.resolver.get_foreign_key_mappings('persons')
        assert person_fks == []
        
        # Test entity with foreign keys
        assignment_fks = self.resolver.get_foreign_key_mappings('assignments')
        assert len(assignment_fks) == 3
        
        fk_fields = {fk.source_field for fk in assignment_fks}
        assert fk_fields == {'person_id', 'unit_id', 'job_title_id'}
    
    def test_validate_dependencies_exist(self):
        """Test validation of dependency existence in data"""
        # Valid data with all dependencies
        valid_data = {
            'unit_types': [{'id': 1, 'name': 'Department'}],
            'units': [{'id': 1, 'name': 'IT', 'unit_type_id': 1}],
            'persons': [{'id': 1, 'name': 'John Doe'}],
            'job_titles': [{'id': 1, 'name': 'Manager'}],
            'assignments': [{'person_id': 1, 'unit_id': 1, 'job_title_id': 1}]
        }
        
        errors = self.resolver.validate_dependencies_exist(valid_data)
        assert errors == []
        
        # Invalid data missing dependencies
        invalid_data = {
            'assignments': [{'person_id': 1, 'unit_id': 1, 'job_title_id': 1}]
        }
        
        errors = self.resolver.validate_dependencies_exist(invalid_data)
        assert len(errors) == 3  # Missing persons, units, job_titles
        assert any('persons' in error for error in errors)
        assert any('units' in error for error in errors)
        assert any('job_titles' in error for error in errors)
    
    def test_get_entity_hierarchy(self):
        """Test getting entity hierarchy levels"""
        hierarchy = self.resolver.get_entity_hierarchy()
        
        # Unit types should be processed first (level 0)
        assert hierarchy['unit_types'] == 0
        
        # Units depend on unit_types, so should have higher level
        assert hierarchy['units'] > hierarchy['unit_types']
        
        # Assignments depend on multiple entities, so should have highest level
        assert hierarchy['assignments'] > hierarchy['persons']
        assert hierarchy['assignments'] > hierarchy['units']
        assert hierarchy['assignments'] > hierarchy['job_titles']
        
        # Verify assignments has the highest level
        max_level = max(hierarchy.values())
        assert hierarchy['assignments'] == max_level
    
    def test_is_self_referential(self):
        """Test detection of self-referential entities"""
        # Units can reference themselves (parent_unit_id)
        assert self.resolver.is_self_referential('units') == True
        
        # Other entities are not self-referential
        assert self.resolver.is_self_referential('persons') == False
        assert self.resolver.is_self_referential('assignments') == False
    
    def test_get_dependents(self):
        """Test getting entities that depend on a given entity"""
        # Units are depended on by assignments
        unit_dependents = self.resolver.get_dependents('units')
        assert 'assignments' in unit_dependents
        
        # Unit types are depended on by units
        unit_type_dependents = self.resolver.get_dependents('unit_types')
        assert 'units' in unit_type_dependents
        
        # Assignments have no dependents
        assignment_dependents = self.resolver.get_dependents('assignments')
        assert assignment_dependents == []
    
    def test_temporary_id_mappings(self):
        """Test temporary ID mapping functionality"""
        # Initially empty
        assert self.resolver.resolve_temporary_id('persons', 'temp1') is None
        
        # Add mapping
        self.resolver.add_temporary_mapping('persons', 'temp1', 123)
        assert self.resolver.resolve_temporary_id('persons', 'temp1') == 123
        
        # Get all mappings
        mappings = self.resolver.get_temporary_mappings('persons')
        assert mappings == {'temp1': 123}
        
        # Clear mappings
        self.resolver.clear_temporary_mappings()
        assert self.resolver.resolve_temporary_id('persons', 'temp1') is None


class TestForeignKeyResolver:
    """Test cases for ForeignKeyResolver class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.dependency_resolver = DependencyResolver()
        self.fk_resolver = ForeignKeyResolver(self.dependency_resolver)
    
    def test_resolve_foreign_keys_valid(self):
        """Test resolving foreign keys with valid references"""
        # Set up temporary mappings
        created_mappings = {
            'persons': {'temp_person_1': 101},
            'units': {'temp_unit_1': 201},
            'job_titles': {'temp_job_1': 301}
        }
        
        # Test record with temporary IDs
        record = {
            'person_id': 'temp_person_1',
            'unit_id': 'temp_unit_1',
            'job_title_id': 'temp_job_1',
            'percentage': 1.0
        }
        
        resolved = self.fk_resolver.resolve_foreign_keys('assignments', record, created_mappings)
        
        assert resolved['person_id'] == 101
        assert resolved['unit_id'] == 201
        assert resolved['job_title_id'] == 301
        assert resolved['percentage'] == 1.0  # Non-FK field unchanged
    
    def test_resolve_foreign_keys_integer_ids(self):
        """Test resolving foreign keys with integer IDs"""
        record = {
            'person_id': 101,
            'unit_id': 201,
            'job_title_id': 301
        }
        
        resolved = self.fk_resolver.resolve_foreign_keys('assignments', record, {})
        
        # Integer IDs should be preserved if valid
        assert resolved['person_id'] == 101
        assert resolved['unit_id'] == 201
        assert resolved['job_title_id'] == 301
    
    def test_resolve_foreign_keys_missing_required(self):
        """Test error handling for missing required foreign keys"""
        record = {
            'person_id': 'nonexistent',
            'unit_id': 201,
            'job_title_id': 301
        }
        
        with pytest.raises(DependencyError) as exc_info:
            self.fk_resolver.resolve_foreign_keys('assignments', record, {})
        
        assert "Cannot resolve required foreign key" in str(exc_info.value)
        assert "person_id" in str(exc_info.value)
    
    def test_resolve_foreign_keys_optional(self):
        """Test resolving optional foreign keys"""
        record = {
            'unit_type_id': 1,
            'theme_id': 'nonexistent'  # Optional foreign key
        }
        
        resolved = self.fk_resolver.resolve_foreign_keys('unit_types', record, {})
        
        assert resolved['unit_type_id'] == 1
        assert resolved['theme_id'] is None  # Optional FK set to None when not found
    
    def test_validate_foreign_key_references(self):
        """Test validation of foreign key references"""
        records = [
            {'person_id': 'person1', 'unit_id': 'unit1', 'job_title_id': 'job1'},
            {'person_id': 'person2', 'unit_id': 'unit1', 'job_title_id': 'job2'},
            {'person_id': 'person3', 'unit_id': 'nonexistent', 'job_title_id': 'job1'}
        ]
        
        available_entities = {
            'persons': {'person1', 'person2', 'person3'},
            'units': {'unit1'},
            'job_titles': {'job1', 'job2'}
        }
        
        errors = self.fk_resolver.validate_foreign_key_references(
            'assignments', records, available_entities
        )
        
        # Should have one error for the nonexistent unit
        assert len(errors) == 1
        assert "nonexistent" in errors[0]
        assert "unit_id" in errors[0]
    
    def test_build_reference_map(self):
        """Test building reference map from import data"""
        data = {
            'persons': [
                {'id': 1, 'name': 'John Doe', 'short_name': 'J.Doe'},
                {'id': 2, 'name': 'Jane Smith'}
            ],
            'units': [
                {'id': 10, 'name': 'IT Department'},
                {'name': 'HR Department'}  # No ID
            ]
        }
        
        reference_map = self.fk_resolver.build_reference_map(data)
        
        # Check persons references
        person_refs = reference_map['persons']
        assert '1' in person_refs
        assert '2' in person_refs
        assert 'John Doe' in person_refs
        assert 'Jane Smith' in person_refs
        assert 'J.Doe' in person_refs
        
        # Check units references
        unit_refs = reference_map['units']
        assert '10' in unit_refs
        assert 'IT Department' in unit_refs
        assert 'HR Department' in unit_refs
    
    def test_clear_cache(self):
        """Test clearing the entity cache"""
        # Add some cache data
        self.fk_resolver._existing_entity_cache['persons'] = {1: 1, 2: 2}
        
        # Clear cache
        self.fk_resolver.clear_cache()
        
        # Verify cache is empty
        assert self.fk_resolver._existing_entity_cache == {}
    
    def test_preload_existing_entities(self):
        """Test preloading existing entities"""
        entity_types = ['persons', 'units']
        
        self.fk_resolver.preload_existing_entities(entity_types)
        
        # Verify cache is initialized for specified types
        for entity_type in entity_types:
            assert entity_type in self.fk_resolver._existing_entity_cache
    
    def test_get_resolution_statistics(self):
        """Test getting resolution statistics"""
        # Add some test data
        self.fk_resolver._existing_entity_cache['persons'] = {1: 1, 2: 2}
        self.dependency_resolver.add_temporary_mapping('units', 'temp1', 101)
        
        stats = self.fk_resolver.get_resolution_statistics()
        
        assert 'cached_entities' in stats
        assert 'temporary_mappings' in stats
        assert stats['cached_entities']['persons'] == 2
        assert stats['temporary_mappings']['units'] == 1


class TestEntityDependency:
    """Test cases for EntityDependency dataclass"""
    
    def test_entity_dependency_creation(self):
        """Test creating EntityDependency instances"""
        dep = EntityDependency(
            entity_type='assignments',
            depends_on='persons',
            foreign_key_field='person_id',
            is_optional=False,
            description='Assignments must reference a person'
        )
        
        assert dep.entity_type == 'assignments'
        assert dep.depends_on == 'persons'
        assert dep.foreign_key_field == 'person_id'
        assert dep.is_optional == False
        assert dep.description == 'Assignments must reference a person'


class TestForeignKeyMapping:
    """Test cases for ForeignKeyMapping dataclass"""
    
    def test_foreign_key_mapping_creation(self):
        """Test creating ForeignKeyMapping instances"""
        mapping = ForeignKeyMapping(
            source_field='person_id',
            target_entity='persons',
            target_field='id',
            is_required=True,
            allow_temporary_ids=True
        )
        
        assert mapping.source_field == 'person_id'
        assert mapping.target_entity == 'persons'
        assert mapping.target_field == 'id'
        assert mapping.is_required == True
        assert mapping.allow_temporary_ids == True
    
    def test_foreign_key_mapping_defaults(self):
        """Test default values for ForeignKeyMapping"""
        mapping = ForeignKeyMapping(
            source_field='unit_id',
            target_entity='units'
        )
        
        assert mapping.target_field == 'id'  # Default value
        assert mapping.is_required == True  # Default value
        assert mapping.allow_temporary_ids == True  # Default value


if __name__ == '__main__':
    pytest.main([__file__])