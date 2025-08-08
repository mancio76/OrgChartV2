"""
Integration tests for dependency resolution with CSV/JSON processors
"""

import pytest
import tempfile
import json
import csv
import os
from app.services.dependency_resolver import DependencyResolver, ForeignKeyResolver
from app.services.csv_processor import CSVProcessor
from app.services.json_processor import JSONProcessor


class TestDependencyIntegration:
    """Integration tests for dependency resolution system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.dependency_resolver = DependencyResolver()
        self.fk_resolver = ForeignKeyResolver(self.dependency_resolver)
        self.csv_processor = CSVProcessor()
        self.json_processor = JSONProcessor()
    
    def test_processing_order_with_sample_data(self):
        """Test that processing order works correctly with sample data"""
        # Sample data that respects dependencies
        sample_data = {
            'assignments': [
                {'person_id': 1, 'unit_id': 1, 'job_title_id': 1, 'percentage': 1.0}
            ],
            'persons': [
                {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
            ],
            'units': [
                {'id': 1, 'name': 'IT Department', 'unit_type_id': 1}
            ],
            'unit_types': [
                {'id': 1, 'name': 'Department', 'level': 1}
            ],
            'job_titles': [
                {'id': 1, 'name': 'Software Engineer'}
            ]
        }
        
        # Get processing order
        entity_types = list(sample_data.keys())
        processing_order = self.dependency_resolver.get_processing_order(entity_types)
        
        # Verify that dependencies come before dependents
        unit_types_idx = processing_order.index('unit_types')
        units_idx = processing_order.index('units')
        persons_idx = processing_order.index('persons')
        job_titles_idx = processing_order.index('job_titles')
        assignments_idx = processing_order.index('assignments')
        
        assert unit_types_idx < units_idx
        assert persons_idx < assignments_idx
        assert units_idx < assignments_idx
        assert job_titles_idx < assignments_idx
    
    def test_foreign_key_resolution_with_temp_ids(self):
        """Test foreign key resolution with temporary IDs"""
        # Create mappings for temporary IDs
        created_mappings = {
            'persons': {'temp_person_1': 101, 'temp_person_2': 102},
            'units': {'temp_unit_1': 201},
            'job_titles': {'temp_job_1': 301}
        }
        
        # Assignment record with temporary IDs
        assignment_record = {
            'person_id': 'temp_person_1',
            'unit_id': 'temp_unit_1',
            'job_title_id': 'temp_job_1',
            'percentage': 0.8,
            'is_current': True
        }
        
        # Resolve foreign keys
        resolved_record = self.fk_resolver.resolve_foreign_keys(
            'assignments', assignment_record, created_mappings
        )
        
        # Verify resolution
        assert resolved_record['person_id'] == 101
        assert resolved_record['unit_id'] == 201
        assert resolved_record['job_title_id'] == 301
        assert resolved_record['percentage'] == 0.8  # Non-FK field unchanged
        assert resolved_record['is_current'] == True
    
    def test_dependency_validation_with_missing_refs(self):
        """Test dependency validation catches missing references"""
        # Data with missing dependencies
        incomplete_data = {
            'assignments': [
                {'person_id': 'person1', 'unit_id': 'unit1', 'job_title_id': 'job1'}
            ],
            'persons': [
                {'id': 'person1', 'name': 'John Doe'}
            ]
            # Missing units and job_titles
        }
        
        # Validate dependencies
        errors = self.dependency_resolver.validate_dependencies_exist(incomplete_data)
        
        # Should report missing units and job_titles
        assert len(errors) == 2
        assert any('units' in error for error in errors)
        assert any('job_titles' in error for error in errors)
    
    def test_reference_validation_with_sample_data(self):
        """Test foreign key reference validation"""
        # Sample assignment records
        assignment_records = [
            {'person_id': 'person1', 'unit_id': 'unit1', 'job_title_id': 'job1'},
            {'person_id': 'person2', 'unit_id': 'unit1', 'job_title_id': 'job2'},
            {'person_id': 'person3', 'unit_id': 'nonexistent', 'job_title_id': 'job1'}
        ]
        
        # Available entities
        available_entities = {
            'persons': {'person1', 'person2', 'person3'},
            'units': {'unit1'},
            'job_titles': {'job1', 'job2'}
        }
        
        # Validate references
        errors = self.fk_resolver.validate_foreign_key_references(
            'assignments', assignment_records, available_entities
        )
        
        # Should have one error for nonexistent unit
        assert len(errors) == 1
        assert 'nonexistent' in errors[0]
        assert 'unit_id' in errors[0]
    
    def test_build_reference_map_from_json_data(self):
        """Test building reference map from JSON-like data"""
        json_data = {
            'persons': [
                {'id': 1, 'name': 'John Doe', 'short_name': 'J.Doe'},
                {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
            ],
            'units': [
                {'id': 10, 'name': 'IT Department', 'short_name': 'IT'},
                {'name': 'HR Department'}  # No ID
            ],
            'job_titles': [
                {'id': 100, 'name': 'Software Engineer'}
            ]
        }
        
        reference_map = self.fk_resolver.build_reference_map(json_data)
        
        # Verify persons references
        person_refs = reference_map['persons']
        assert '1' in person_refs
        assert '2' in person_refs
        assert 'John Doe' in person_refs
        assert 'Jane Smith' in person_refs
        assert 'J.Doe' in person_refs
        
        # Verify units references
        unit_refs = reference_map['units']
        assert '10' in unit_refs
        assert 'IT Department' in unit_refs
        assert 'HR Department' in unit_refs
        assert 'IT' in unit_refs
        
        # Verify job titles references
        job_refs = reference_map['job_titles']
        assert '100' in job_refs
        assert 'Software Engineer' in job_refs
    
    def test_self_referential_units_processing(self):
        """Test handling of self-referential units (parent_unit_id)"""
        units_data = [
            {'id': 1, 'name': 'Root Department', 'unit_type_id': 1, 'parent_unit_id': None},
            {'id': 2, 'name': 'Sub Department', 'unit_type_id': 1, 'parent_unit_id': 1},
            {'id': 3, 'name': 'Sub-Sub Department', 'unit_type_id': 1, 'parent_unit_id': 2}
        ]
        
        # Verify that units are detected as self-referential
        assert self.dependency_resolver.is_self_referential('units') == True
        
        # Verify that processing order still works
        processing_order = self.dependency_resolver.get_processing_order(['units', 'unit_types'])
        assert processing_order.index('unit_types') < processing_order.index('units')
        
        # Test foreign key resolution for self-referential case
        created_mappings = {'units': {'temp_unit_1': 1}}
        
        unit_record = {
            'id': 2,
            'name': 'Sub Department',
            'unit_type_id': 1,
            'parent_unit_id': 'temp_unit_1'  # Reference to another unit
        }
        
        resolved_record = self.fk_resolver.resolve_foreign_keys(
            'units', unit_record, created_mappings
        )
        
        assert resolved_record['parent_unit_id'] == 1
    
    def test_complete_import_workflow_simulation(self):
        """Test a complete import workflow simulation"""
        # Simulate import data in correct dependency order
        import_data = {
            'unit_types': [
                {'id': 'temp_ut_1', 'name': 'Department', 'level': 1}
            ],
            'job_titles': [
                {'id': 'temp_jt_1', 'name': 'Manager'},
                {'id': 'temp_jt_2', 'name': 'Developer'}
            ],
            'persons': [
                {'id': 'temp_p_1', 'name': 'John Manager'},
                {'id': 'temp_p_2', 'name': 'Jane Developer'}
            ],
            'units': [
                {'id': 'temp_u_1', 'name': 'IT Department', 'unit_type_id': 'temp_ut_1'}
            ],
            'assignments': [
                {'person_id': 'temp_p_1', 'unit_id': 'temp_u_1', 'job_title_id': 'temp_jt_1'},
                {'person_id': 'temp_p_2', 'unit_id': 'temp_u_1', 'job_title_id': 'temp_jt_2'}
            ]
        }
        
        # Get processing order
        processing_order = self.dependency_resolver.get_processing_order(list(import_data.keys()))
        
        # Simulate processing each entity type in order
        created_mappings = {}
        
        for entity_type in processing_order:
            records = import_data[entity_type]
            created_mappings[entity_type] = {}
            
            for i, record in enumerate(records):
                # Resolve foreign keys if needed
                if entity_type in ['units', 'assignments']:
                    resolved_record = self.fk_resolver.resolve_foreign_keys(
                        entity_type, record, created_mappings
                    )
                else:
                    resolved_record = record
                
                # Simulate database insertion (assign real ID)
                real_id = (i + 1) * 100 + hash(entity_type) % 100
                temp_id = record.get('id', f'temp_{entity_type}_{i}')
                created_mappings[entity_type][str(temp_id)] = real_id
        
        # Verify that all temporary IDs were resolved
        assert len(created_mappings) == 5
        assert 'unit_types' in created_mappings
        assert 'units' in created_mappings
        assert 'assignments' in created_mappings
        
        # Verify assignments got their foreign keys resolved
        assignments = import_data['assignments']
        for assignment in assignments:
            resolved = self.fk_resolver.resolve_foreign_keys(
                'assignments', assignment, created_mappings
            )
            # All foreign keys should be integers now
            assert isinstance(resolved['person_id'], int)
            assert isinstance(resolved['unit_id'], int)
            assert isinstance(resolved['job_title_id'], int)


if __name__ == '__main__':
    pytest.main([__file__])