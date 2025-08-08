"""
Integration tests for validation framework with import/export service.

This module tests the integration between the validation framework,
conflict resolution system, and the import/export service.
"""

import pytest
from app.services.import_export import ImportExportService
from app.models.import_export import ImportOptions, ConflictResolutionStrategy


class TestValidationIntegration:
    """Integration tests for validation framework."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ImportExportService()
    
    def test_service_initialization(self):
        """Test that the service initializes with all validation components."""
        assert self.service.validation_framework is not None
        assert self.service.conflict_resolution_manager is not None
        assert self.service.dependency_resolver is not None
        assert self.service.foreign_key_resolver is not None
    
    def test_validate_import_data_valid(self):
        """Test validation of valid import data."""
        # Valid unit types data
        data = {
            'unit_types': [
                {
                    'id': 1,
                    'name': 'Test Unit Type',
                    'short_name': 'TUT',
                    'level': 1,
                    'aliases': '[]'
                },
                {
                    'id': 2,
                    'name': 'Another Unit Type',
                    'short_name': 'AUT',
                    'level': 2,
                    'aliases': '[]'
                }
            ]
        }
        
        options = ImportOptions(
            entity_types=['unit_types'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            validate_only=True
        )
        
        result = self.service.validate_import_data(data, options)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.validated_records == 2
    
    def test_validate_import_data_invalid(self):
        """Test validation of invalid import data."""
        # Invalid unit types data (missing required fields)
        data = {
            'unit_types': [
                {
                    'id': 1,
                    'short_name': 'TUT',
                    'level': 1
                    # Missing required 'name' field
                },
                {
                    'id': 2,
                    'name': 'Valid Unit Type',
                    'short_name': 'VUT',
                    'level': -1  # Invalid level (should be positive)
                }
            ]
        }
        
        options = ImportOptions(
            entity_types=['unit_types'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            validate_only=True
        )
        
        result = self.service.validate_import_data(data, options)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2  # At least one for missing name, one for invalid level
        assert result.validated_records == 2
        
        # Check for specific error types
        missing_field_errors = [e for e in result.errors if 'name' in e.field and 'required' in e.message.lower()]
        assert len(missing_field_errors) >= 1
        
        invalid_value_errors = [e for e in result.errors if 'level' in e.field]
        assert len(invalid_value_errors) >= 1
    
    def test_validate_import_data_business_rules(self):
        """Test validation of business rules."""
        # Data with business rule violations (invalid date range)
        data = {
            'units': [
                {
                    'id': 1,
                    'name': 'Test Unit',
                    'short_name': 'TU',
                    'unit_type_id': 1,
                    'start_date': '2024-12-31',
                    'end_date': '2024-01-01'  # End date before start date
                }
            ]
        }
        
        options = ImportOptions(
            entity_types=['units'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            validate_only=True,
            skip_validation=False  # Enable validation
        )
        
        result = self.service.validate_import_data(data, options)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Should have business rule violation for date range
        date_range_errors = [e for e in result.errors if 'date_range' in e.field]
        assert len(date_range_errors) >= 1
    
    def test_validate_import_data_skip_validation(self):
        """Test skipping validation when requested."""
        # Invalid data that should normally fail validation
        data = {
            'unit_types': [
                {
                    'id': 1,
                    'short_name': 'TUT'
                    # Missing required 'name' field
                }
            ]
        }
        
        options = ImportOptions(
            entity_types=['unit_types'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            validate_only=True,
            skip_validation=True  # Skip validation
        )
        
        result = self.service.validate_import_data(data, options)
        
        # Should be valid because validation was skipped
        assert result.validated_records == 1
        # Note: The result might still have some errors from other validation layers
    
    def test_validate_field_rules_coverage(self):
        """Test that validation framework has rules for all expected entity types."""
        expected_entities = ['unit_types', 'unit_type_themes', 'units', 'job_titles', 'persons', 'assignments']
        
        for entity_type in expected_entities:
            field_rules = self.service.validation_framework.get_field_rules(entity_type)
            assert len(field_rules) > 0, f"No field rules found for {entity_type}"
            
            # Check that common fields have rules (where applicable)
            if entity_type not in ['unit_type_themes', 'assignments']:  # These entities might not have all common fields
                assert 'name' in field_rules, f"No 'name' field rule for {entity_type}"
            
            # All entities should have an id field rule
            assert 'id' in field_rules, f"No 'id' field rule for {entity_type}"
    
    def test_business_rules_coverage(self):
        """Test that business rules are properly configured."""
        all_rules = self.service.validation_framework.get_business_rules()
        assert len(all_rules) > 0
        
        # Check for specific business rules
        rule_names = [rule.name for rule in all_rules]
        assert 'date_range_validation' in rule_names
        assert 'unit_hierarchy_validation' in rule_names
        assert 'assignment_validity_validation' in rule_names
        assert 'percentage_range_validation' in rule_names
    
    def test_conflict_resolution_manager_integration(self):
        """Test that conflict resolution manager is properly integrated."""
        # Test that the manager has the required components
        assert self.service.conflict_resolution_manager.detector is not None
        assert self.service.conflict_resolution_manager.resolver is not None
        
        # Test that unique field combinations are configured
        detector = self.service.conflict_resolution_manager.detector
        expected_entities = ['unit_types', 'unit_type_themes', 'units', 'job_titles', 'persons', 'assignments']
        
        for entity_type in expected_entities:
            assert entity_type in detector.unique_field_combinations
            combinations = detector.unique_field_combinations[entity_type]
            assert len(combinations) > 0, f"No unique field combinations for {entity_type}"


if __name__ == '__main__':
    pytest.main([__file__])