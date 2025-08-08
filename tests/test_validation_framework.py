"""
Tests for the validation framework.

This module tests the comprehensive validation framework including
field validation, business rules, and foreign key constraints.
"""

import pytest
from datetime import date, datetime
from app.services.validation_framework import ValidationFramework, DataType, FieldValidationRule
from app.models.import_export import ImportExportValidationError, ImportErrorType


class TestValidationFramework:
    """Test cases for the ValidationFramework class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.framework = ValidationFramework()
    
    def test_initialization(self):
        """Test that the validation framework initializes correctly."""
        assert self.framework is not None
        assert len(self.framework.field_rules) > 0
        assert len(self.framework.business_rules) > 0
        
        # Check that all expected entity types have rules
        expected_entities = ['unit_types', 'unit_type_themes', 'units', 'job_titles', 'persons', 'assignments']
        for entity_type in expected_entities:
            assert entity_type in self.framework.field_rules
    
    def test_validate_field_value_string(self):
        """Test string field validation."""
        # Valid string
        errors = self.framework.validate_field_value('unit_types', 'name', 'Test Unit Type')
        assert len(errors) == 0
        
        # Empty required string
        errors = self.framework.validate_field_value('unit_types', 'name', '')
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.MISSING_REQUIRED_FIELD
        
        # String too long
        long_string = 'x' * 300  # Exceeds max_length of 255
        errors = self.framework.validate_field_value('unit_types', 'name', long_string)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_field_value_integer(self):
        """Test integer field validation."""
        # Valid integer
        errors = self.framework.validate_field_value('unit_types', 'id', 123)
        assert len(errors) == 0
        
        # Valid integer as string
        errors = self.framework.validate_field_value('unit_types', 'id', '123')
        assert len(errors) == 0
        
        # Invalid integer
        errors = self.framework.validate_field_value('unit_types', 'id', 'not_a_number')
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
        
        # Integer below minimum
        errors = self.framework.validate_field_value('unit_types', 'id', 0)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_field_value_email(self):
        """Test email field validation."""
        # Valid email
        errors = self.framework.validate_field_value('persons', 'email', 'test@example.com')
        assert len(errors) == 0
        
        # Invalid email
        errors = self.framework.validate_field_value('persons', 'email', 'invalid_email')
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
        
        # Null email (should be allowed)
        errors = self.framework.validate_field_value('persons', 'email', None)
        assert len(errors) == 0
    
    def test_validate_field_value_date(self):
        """Test date field validation."""
        # Valid date string
        errors = self.framework.validate_field_value('units', 'start_date', '2024-01-01')
        assert len(errors) == 0
        
        # Valid date object
        errors = self.framework.validate_field_value('units', 'start_date', date(2024, 1, 1))
        assert len(errors) == 0
        
        # Invalid date format
        errors = self.framework.validate_field_value('units', 'start_date', '01/01/2024')
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_field_value_percentage(self):
        """Test percentage field validation."""
        # Valid percentage
        errors = self.framework.validate_field_value('assignments', 'percentage', 0.5)
        assert len(errors) == 0
        
        # Valid percentage as string
        errors = self.framework.validate_field_value('assignments', 'percentage', '0.75')
        assert len(errors) == 0
        
        # Percentage out of range (too high)
        errors = self.framework.validate_field_value('assignments', 'percentage', 1.5)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
        
        # Percentage out of range (negative)
        errors = self.framework.validate_field_value('assignments', 'percentage', -0.1)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_record_complete(self):
        """Test complete record validation."""
        # Valid unit type record
        record = {
            'id': 1,
            'name': 'Test Unit Type',
            'short_name': 'TUT',
            'level': 1,
            'aliases': '[]'
        }
        
        errors = self.framework.validate_record('unit_types', record)
        assert len(errors) == 0
        
        # Invalid record with missing required field
        invalid_record = {
            'id': 1,
            'short_name': 'TUT',
            'level': 1
            # Missing required 'name' field
        }
        
        errors = self.framework.validate_record('unit_types', invalid_record)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.MISSING_REQUIRED_FIELD
        assert errors[0].field == 'name'
    
    def test_validate_business_rules_date_range(self):
        """Test business rule validation for date ranges."""
        # Valid date range
        record = {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        
        errors = self.framework.validate_record('units', record)
        date_range_errors = [e for e in errors if 'date_range' in e.field]
        assert len(date_range_errors) == 0
        
        # Invalid date range (start after end)
        invalid_record = {
            'start_date': '2024-12-31',
            'end_date': '2024-01-01'
        }
        
        errors = self.framework.validate_record('units', invalid_record)
        date_range_errors = [e for e in errors if 'date_range' in e.field]
        assert len(date_range_errors) == 1
    
    def test_validate_business_rules_unit_hierarchy(self):
        """Test business rule validation for unit hierarchy."""
        # Valid unit (different parent)
        record = {
            'id': 1,
            'parent_unit_id': 2
        }
        
        errors = self.framework.validate_record('units', record)
        hierarchy_errors = [e for e in errors if 'hierarchy' in e.field]
        assert len(hierarchy_errors) == 0
        
        # Invalid unit (self-parent)
        invalid_record = {
            'id': 1,
            'parent_unit_id': 1
        }
        
        errors = self.framework.validate_record('units', invalid_record)
        hierarchy_errors = [e for e in errors if 'hierarchy' in e.field]
        assert len(hierarchy_errors) == 1
    
    def test_validate_records_batch(self):
        """Test batch record validation."""
        records = [
            {
                'id': 1,
                'name': 'Unit Type 1',
                'short_name': 'UT1',
                'level': 1
            },
            {
                'id': 2,
                'name': 'Unit Type 2',
                'short_name': 'UT2',
                'level': 2
            },
            {
                # Invalid record - missing name
                'id': 3,
                'short_name': 'UT3',
                'level': 3
            }
        ]
        
        errors = self.framework.validate_records_batch('unit_types', records)
        
        # Should have one error for the missing name in record 3
        missing_name_errors = [e for e in errors if e.field == 'name' and e.line_number == 3]
        assert len(missing_name_errors) == 1
        assert missing_name_errors[0].error_type == ImportErrorType.MISSING_REQUIRED_FIELD
    
    def test_validate_foreign_key_constraints(self):
        """Test foreign key constraint validation."""
        # Records with foreign key references
        records = [
            {
                'id': 1,
                'name': 'Test Unit',
                'unit_type_id': 1,  # Should exist in reference map
                'parent_unit_id': 2  # Should exist in reference map
            },
            {
                'id': 2,
                'name': 'Test Unit 2',
                'unit_type_id': 999,  # Should NOT exist in reference map
                'parent_unit_id': None  # Null is allowed
            }
        ]
        
        # Reference map with available IDs
        reference_map = {
            'unit_types': {1, 2, 3},
            'units': {1, 2, 3}
        }
        
        errors = self.framework.validate_foreign_key_constraints('units', records, reference_map)
        
        # Should have one error for the invalid unit_type_id in record 2
        fk_errors = [e for e in errors if e.error_type == ImportErrorType.FOREIGN_KEY_VIOLATION]
        assert len(fk_errors) == 1
        assert fk_errors[0].field == 'unit_type_id'
    
    def test_add_custom_field_rule(self):
        """Test adding custom field validation rules."""
        # Add custom rule
        custom_rule = FieldValidationRule(
            field_name='custom_field',
            data_type=DataType.STRING,
            required=True,
            max_length=10
        )
        
        self.framework.add_custom_field_rule('test_entity', custom_rule)
        
        # Verify rule was added
        assert 'test_entity' in self.framework.field_rules
        assert 'custom_field' in self.framework.field_rules['test_entity']
        
        # Test validation with custom rule
        errors = self.framework.validate_field_value('test_entity', 'custom_field', 'valid')
        assert len(errors) == 0
        
        errors = self.framework.validate_field_value('test_entity', 'custom_field', 'this_is_too_long')
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_get_field_rules(self):
        """Test getting field rules for entity types."""
        unit_rules = self.framework.get_field_rules('unit_types')
        assert len(unit_rules) > 0
        assert 'name' in unit_rules
        assert 'id' in unit_rules
        
        # Non-existent entity
        empty_rules = self.framework.get_field_rules('non_existent')
        assert len(empty_rules) == 0
    
    def test_get_business_rules(self):
        """Test getting business rules."""
        all_rules = self.framework.get_business_rules()
        assert len(all_rules) > 0
        
        # Rules for specific entity
        unit_rules = self.framework.get_business_rules('units')
        assert len(unit_rules) > 0
        
        # Check that rules are filtered correctly
        assignment_rules = self.framework.get_business_rules('assignments')
        assignment_specific_rules = [r for r in assignment_rules if r.applies_to_entities and 'assignments' in r.applies_to_entities]
        assert len(assignment_specific_rules) > 0


if __name__ == '__main__':
    pytest.main([__file__])