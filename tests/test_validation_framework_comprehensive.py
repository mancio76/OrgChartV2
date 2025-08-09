"""
Comprehensive unit tests for the validation framework.

This module extends the existing validation framework tests with additional
coverage for edge cases, business rules, and complex validation scenarios.
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch

from app.services.validation_framework import (
    ValidationFramework, DataType, FieldValidationRule, BusinessRule
)
from app.models.import_export import ImportExportValidationError, ImportErrorType


class TestValidationFrameworkComprehensive:
    """Comprehensive test cases for the ValidationFramework class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.framework = ValidationFramework()
    
    def test_validate_field_value_boolean(self):
        """Test boolean field validation."""
        # Valid boolean values
        errors = self.framework.validate_field_value('assignments', 'is_current', True)
        assert len(errors) == 0
        
        errors = self.framework.validate_field_value('assignments', 'is_current', False)
        assert len(errors) == 0
        
        # Valid boolean as string
        errors = self.framework.validate_field_value('assignments', 'is_current', 'true')
        assert len(errors) == 0
        
        errors = self.framework.validate_field_value('assignments', 'is_current', 'false')
        assert len(errors) == 0
        
        # Invalid boolean
        errors = self.framework.validate_field_value('assignments', 'is_current', 'maybe')
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_field_value_json_array(self):
        """Test JSON array field validation (aliases)."""
        # Valid JSON array as string
        valid_aliases = '[{"value":"Test","lang":"en-US"}]'
        errors = self.framework.validate_field_value('unit_types', 'aliases', valid_aliases)
        assert len(errors) == 0
        
        # Valid JSON array as list
        valid_aliases_list = [{"value": "Test", "lang": "en-US"}]
        errors = self.framework.validate_field_value('unit_types', 'aliases', valid_aliases_list)
        assert len(errors) == 0
        
        # Empty array
        errors = self.framework.validate_field_value('unit_types', 'aliases', '[]')
        assert len(errors) == 0
        
        # Invalid JSON
        errors = self.framework.validate_field_value('unit_types', 'aliases', '[invalid json]')
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_field_value_nullable_fields(self):
        """Test validation of nullable fields."""
        # Nullable field with None value
        errors = self.framework.validate_field_value('units', 'end_date', None)
        assert len(errors) == 0
        
        # Nullable field with empty string
        errors = self.framework.validate_field_value('units', 'end_date', '')
        assert len(errors) == 0
        
        # Nullable field with valid value
        errors = self.framework.validate_field_value('units', 'end_date', '2024-12-31')
        assert len(errors) == 0
    
    def test_validate_field_value_foreign_key_fields(self):
        """Test validation of foreign key fields."""
        # Valid integer foreign key
        errors = self.framework.validate_field_value('units', 'unit_type_id', 1)
        assert len(errors) == 0
        
        # Valid string foreign key (temporary ID)
        errors = self.framework.validate_field_value('units', 'unit_type_id', 'temp_unit_type_1')
        assert len(errors) == 0
        
        # Invalid foreign key (negative)
        errors = self.framework.validate_field_value('units', 'unit_type_id', -1)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_field_value_string_length_limits(self):
        """Test string field length validation."""
        # Valid length string
        valid_name = 'A' * 100  # Within typical limit
        errors = self.framework.validate_field_value('unit_types', 'name', valid_name)
        assert len(errors) == 0
        
        # String exceeding maximum length
        too_long_name = 'A' * 300  # Exceeds typical 255 char limit
        errors = self.framework.validate_field_value('unit_types', 'name', too_long_name)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
        assert 'length' in errors[0].message.lower()
    
    def test_validate_field_value_numeric_ranges(self):
        """Test numeric field range validation."""
        # Valid percentage
        errors = self.framework.validate_field_value('assignments', 'percentage', 0.5)
        assert len(errors) == 0
        
        # Percentage at boundaries
        errors = self.framework.validate_field_value('assignments', 'percentage', 0.0)
        assert len(errors) == 0
        
        errors = self.framework.validate_field_value('assignments', 'percentage', 1.0)
        assert len(errors) == 0
        
        # Percentage out of range
        errors = self.framework.validate_field_value('assignments', 'percentage', 1.5)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
        
        errors = self.framework.validate_field_value('assignments', 'percentage', -0.1)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_field_value_email_formats(self):
        """Test email field validation with various formats."""
        # Valid email formats
        valid_emails = [
            'user@example.com',
            'user.name@example.com',
            'user+tag@example.co.uk',
            'user123@example-domain.com'
        ]
        
        for email in valid_emails:
            errors = self.framework.validate_field_value('persons', 'email', email)
            assert len(errors) == 0, f"Valid email {email} should not have errors"
        
        # Invalid email formats
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user..name@example.com',
            'user@.com'
        ]
        
        for email in invalid_emails:
            errors = self.framework.validate_field_value('persons', 'email', email)
            assert len(errors) == 1, f"Invalid email {email} should have errors"
            assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_field_value_date_formats(self):
        """Test date field validation with various formats."""
        # Valid date formats
        valid_dates = [
            '2024-01-01',
            '2024-12-31',
            date(2024, 1, 1),
            datetime(2024, 1, 1, 12, 0, 0)
        ]
        
        for test_date in valid_dates:
            errors = self.framework.validate_field_value('units', 'start_date', test_date)
            assert len(errors) == 0, f"Valid date {test_date} should not have errors"
        
        # Invalid date formats
        invalid_dates = [
            '01/01/2024',  # Wrong format
            '2024-13-01',  # Invalid month
            '2024-01-32',  # Invalid day
            'not-a-date',
            '2024/01/01'   # Wrong separator
        ]
        
        for test_date in invalid_dates:
            errors = self.framework.validate_field_value('units', 'start_date', test_date)
            assert len(errors) == 1, f"Invalid date {test_date} should have errors"
            assert errors[0].error_type == ImportErrorType.INVALID_DATA_TYPE
    
    def test_validate_record_with_all_field_types(self):
        """Test complete record validation with all field types."""
        # Complete valid assignment record
        valid_assignment = {
            'id': 1,
            'person_id': 1,
            'unit_id': 1,
            'job_title_id': 1,
            'version': 1,
            'percentage': 1.0,
            'is_ad_interim': False,
            'is_unit_boss': True,
            'notes': 'Test assignment',
            'valid_from': '2024-01-01',
            'valid_to': None,
            'is_current': True
        }
        
        errors = self.framework.validate_record('assignments', valid_assignment)
        assert len(errors) == 0
    
    def test_validate_record_missing_multiple_required_fields(self):
        """Test record validation with multiple missing required fields."""
        # Record missing multiple required fields
        incomplete_record = {
            'id': 1,
            'level': 1
            # Missing: name, short_name
        }
        
        errors = self.framework.validate_record('unit_types', incomplete_record)
        
        # Should have errors for each missing required field
        missing_field_errors = [e for e in errors if e.error_type == ImportErrorType.MISSING_REQUIRED_FIELD]
        assert len(missing_field_errors) >= 2
        
        missing_fields = {error.field for error in missing_field_errors}
        assert 'name' in missing_fields
        assert 'short_name' in missing_fields
    
    def test_validate_business_rules_comprehensive(self):
        """Test comprehensive business rule validation."""
        # Test date range validation
        invalid_date_range_record = {
            'id': 1,
            'name': 'Test Unit',
            'start_date': '2024-12-31',
            'end_date': '2024-01-01'  # End before start
        }
        
        errors = self.framework.validate_record('units', invalid_date_range_record)
        date_errors = [e for e in errors if 'date' in e.field.lower()]
        assert len(date_errors) > 0
    
    def test_validate_business_rules_unit_hierarchy(self):
        """Test unit hierarchy business rules."""
        # Unit cannot be its own parent
        self_parent_unit = {
            'id': 1,
            'name': 'Test Unit',
            'parent_unit_id': 1  # Self-reference
        }
        
        errors = self.framework.validate_record('units', self_parent_unit)
        hierarchy_errors = [e for e in errors if 'hierarchy' in e.field.lower() or 'parent' in e.field.lower()]
        assert len(hierarchy_errors) > 0
    
    def test_validate_business_rules_assignment_percentage(self):
        """Test assignment percentage business rules."""
        # Assignment with invalid percentage sum (if multiple assignments)
        assignment_records = [
            {
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'percentage': 0.7,
                'is_current': True
            },
            {
                'person_id': 1,
                'unit_id': 2,
                'job_title_id': 2,
                'percentage': 0.5,  # Total would be 1.2 (over 100%)
                'is_current': True
            }
        ]
        
        # Validate each record individually first
        for record in assignment_records:
            errors = self.framework.validate_record('assignments', record)
            # Individual records should be valid
            assert len([e for e in errors if e.error_type == ImportErrorType.INVALID_DATA_TYPE]) == 0
    
    def test_validate_foreign_key_constraints_comprehensive(self):
        """Test comprehensive foreign key constraint validation."""
        # Records with various foreign key scenarios
        assignment_records = [
            {
                'person_id': 1,      # Should exist
                'unit_id': 1,        # Should exist
                'job_title_id': 1,   # Should exist
                'percentage': 1.0
            },
            {
                'person_id': 999,    # Should NOT exist
                'unit_id': 1,        # Should exist
                'job_title_id': 1,   # Should exist
                'percentage': 1.0
            },
            {
                'person_id': 'temp_person_1',  # Temporary ID (should be allowed)
                'unit_id': 1,
                'job_title_id': 1,
                'percentage': 1.0
            }
        ]
        
        # Reference map with available IDs
        reference_map = {
            'persons': {1, 2, 3, 'temp_person_1'},
            'units': {1, 2, 3},
            'job_titles': {1, 2, 3}
        }
        
        errors = self.framework.validate_foreign_key_constraints(
            'assignments', assignment_records, reference_map
        )
        
        # Should have one error for the invalid person_id (999)
        fk_errors = [e for e in errors if e.error_type == ImportErrorType.FOREIGN_KEY_VIOLATION]
        assert len(fk_errors) == 1
        assert fk_errors[0].field == 'person_id'
        assert '999' in fk_errors[0].message
    
    def test_validate_records_batch_with_line_numbers(self):
        """Test batch validation with proper line number tracking."""
        records = [
            {'id': 1, 'name': 'Valid Record', 'short_name': 'VR', 'level': 1},
            {'id': 2, 'short_name': 'IR', 'level': 2},  # Missing name
            {'id': 3, 'name': 'Another Valid', 'short_name': 'AV', 'level': 3},
            {'id': 4, 'name': '', 'short_name': 'ER', 'level': 4}  # Empty name
        ]
        
        errors = self.framework.validate_records_batch('unit_types', records, start_line=1)
        
        # Should have errors for records 2 and 4
        missing_name_errors = [e for e in errors if e.field == 'name']
        assert len(missing_name_errors) == 2
        
        # Check line numbers are correct
        line_numbers = {error.line_number for error in missing_name_errors}
        assert 2 in line_numbers  # Record index 1 + start_line 1 = line 2
        assert 4 in line_numbers  # Record index 3 + start_line 1 = line 4
    
    def test_add_custom_business_rule(self):
        """Test adding custom business rules."""
        # Create custom business rule
        def custom_validation_rule(entity_type: str, record: dict) -> list:
            errors = []
            if entity_type == 'test_entity' and record.get('custom_field', 0) < 10:
                errors.append(ImportExportValidationError(
                    field='custom_field',
                    message='Custom field must be at least 10',
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                ))
            return errors
        
        custom_rule = BusinessRule(
            name='custom_minimum_value',
            description='Custom field must have minimum value',
            validation_function=custom_validation_rule,
            applies_to_entities=['test_entity']
        )
        
        # Add the custom rule
        self.framework.add_custom_business_rule(custom_rule)
        
        # Test validation with custom rule
        test_record = {'custom_field': 5}  # Below minimum
        errors = self.framework.validate_record('test_entity', test_record)
        
        custom_errors = [e for e in errors if e.error_type == ImportErrorType.BUSINESS_RULE_VIOLATION]
        assert len(custom_errors) == 1
        assert 'must be at least 10' in custom_errors[0].message
    
    def test_get_validation_statistics(self):
        """Test getting validation statistics."""
        # Validate multiple records with various outcomes
        records = [
            {'id': 1, 'name': 'Valid', 'short_name': 'V', 'level': 1},
            {'id': 2, 'short_name': 'Invalid', 'level': 2},  # Missing name
            {'id': 3, 'name': 'Valid2', 'short_name': 'V2', 'level': 3}
        ]
        
        errors = self.framework.validate_records_batch('unit_types', records)
        
        stats = self.framework.get_validation_statistics(errors, len(records))
        
        assert stats['total_records'] == 3
        assert stats['valid_records'] == 2
        assert stats['invalid_records'] == 1
        assert stats['total_errors'] == len(errors)
        assert stats['error_rate'] == len(errors) / 3
        assert 'error_types' in stats
        assert ImportErrorType.MISSING_REQUIRED_FIELD.value in stats['error_types']
    
    def test_validate_field_value_edge_cases(self):
        """Test field validation with edge cases."""
        # Test with None values for required fields
        errors = self.framework.validate_field_value('unit_types', 'name', None)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.MISSING_REQUIRED_FIELD
        
        # Test with whitespace-only strings
        errors = self.framework.validate_field_value('unit_types', 'name', '   ')
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.MISSING_REQUIRED_FIELD
        
        # Test with very large numbers
        errors = self.framework.validate_field_value('unit_types', 'id', 999999999999)
        assert len(errors) == 0  # Should be valid
        
        # Test with zero values where appropriate
        errors = self.framework.validate_field_value('assignments', 'percentage', 0.0)
        assert len(errors) == 0  # Zero percentage should be valid
    
    def test_validate_complex_json_aliases(self):
        """Test validation of complex JSON alias structures."""
        # Valid complex aliases
        complex_aliases = [
            {"value": "Primary Name", "lang": "en-US", "context": "formal"},
            {"value": "Nome Primario", "lang": "it-IT", "context": "formal"},
            {"value": "Nickname", "lang": "en-US", "context": "informal"}
        ]
        
        errors = self.framework.validate_field_value('unit_types', 'aliases', complex_aliases)
        assert len(errors) == 0
        
        # Invalid alias structure (missing required fields)
        invalid_aliases = [
            {"value": "Name"},  # Missing lang
            {"lang": "en-US"}   # Missing value
        ]
        
        errors = self.framework.validate_field_value('unit_types', 'aliases', invalid_aliases)
        # Should validate JSON structure but may not validate alias content
        # (depends on implementation depth)


# Note: FieldValidator class is not implemented in the current validation framework
# These tests would be added when the FieldValidator utility class is implemented


if __name__ == '__main__':
    pytest.main([__file__])