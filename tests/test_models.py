"""
Unit tests for model validation and serialization.

This module tests all domain models including validation logic,
serialization/deserialization, and business rule enforcement
as required by Task 9.1.
"""

import pytest
from datetime import date, datetime
from typing import List

from app.models.base import BaseModel, ValidationError, ModelValidationException, Alias, parse_aliases, serialize_aliases
from app.models.unit_type import UnitType
from app.models.unit import Unit
from app.models.person import Person
from app.models.job_title import JobTitle
from app.models.assignment import Assignment


class TestBaseModel:
    """Test BaseModel functionality"""
    
    def test_to_dict_conversion(self):
        """Test model to dictionary conversion"""
        model = BaseModel()
        model.datetime_created = datetime(2023, 1, 1, 10, 0, 0)
        model.datetime_updated = datetime(2023, 1, 2, 11, 0, 0)
        
        result = model.to_dict()
        
        assert result['datetime_created'] == '2023-01-01T10:00:00'
        assert result['datetime_updated'] == '2023-01-02T11:00:00'
    
    def test_from_dict_conversion(self):
        """Test dictionary to model conversion"""
        data = {
            'datetime_created': '2023-01-01T10:00:00',
            'datetime_updated': '2023-01-02T11:00:00'
        }
        
        model = BaseModel.from_dict(data)
        
        assert model.datetime_created == datetime(2023, 1, 1, 10, 0, 0)
        assert model.datetime_updated == datetime(2023, 1, 2, 11, 0, 0)
    
    def test_validate_base_implementation(self):
        """Test base validation returns empty list"""
        model = BaseModel()
        errors = model.validate()
        assert errors == []
    
    def test_is_valid(self):
        """Test is_valid method"""
        model = BaseModel()
        assert model.is_valid() is True
    
    def test_set_audit_fields_create(self):
        """Test audit field setting for create operation"""
        model = BaseModel()
        model.set_audit_fields(is_update=False)
        
        assert model.datetime_created is not None
        assert model.datetime_updated is not None


class TestAlias:
    """Test Alias model functionality"""
    
    def test_alias_creation(self):
        """Test Alias creation with default language"""
        alias = Alias("Test Value")
        assert alias.value == "Test Value"
        assert alias.lang == "it-IT"
    
    def test_alias_to_dict(self):
        """Test Alias to dictionary conversion"""
        alias = Alias("Test Value", "en-US")
        result = alias.to_dict()
        
        expected = {"value": "Test Value", "lang": "en-US"}
        assert result == expected


class TestUnitType:
    """Test UnitType model"""
    
    def test_unit_type_validation_empty_name(self):
        """Test UnitType validation with empty name"""
        unit_type = UnitType(name="")
        errors = unit_type.validate()
        
        assert len(errors) == 1
        assert errors[0].field == "name"
        assert errors[0].message == "Name is required"
    
    def test_unit_type_alias_management(self):
        """Test UnitType alias management methods"""
        unit_type = UnitType(name="Function")
        
        # Add alias
        unit_type.add_alias("Funzione", "it-IT")
        assert len(unit_type.aliases) == 1
        assert unit_type.get_alias_by_language("it-IT") == "Funzione"
        
        # Add another alias for different language
        unit_type.add_alias("Fonction", "fr-FR")
        assert len(unit_type.aliases) == 2
        
        # Replace existing alias
        unit_type.add_alias("Funzione Aziendale", "it-IT")
        assert len(unit_type.aliases) == 2
        assert unit_type.get_alias_by_language("it-IT") == "Funzione Aziendale"
    
    def test_unit_type_localized_name(self):
        """Test UnitType localized name functionality"""
        unit_type = UnitType(name="Function")
        unit_type.add_alias("Funzione", "it-IT")
        
        # Should return alias for existing language
        assert unit_type.get_localized_name("it-IT") == "Funzione"
        
        # Should return default name for non-existing language
        assert unit_type.get_localized_name("fr-FR") == "Function"
    
    def test_unit_type_display_name(self):
        """Test UnitType display_name property"""
        unit_type = UnitType(name="Organizational Unit")
        assert unit_type.display_name == "Organizational Unit"
    
    def test_unit_type_aliases_json_property(self):
        """Test UnitType aliases_json property"""
        unit_type = UnitType(
            name="Function",
            aliases=[Alias("Funzione", "it-IT"), Alias("Fonction", "fr-FR")]
        )
        
        json_string = unit_type.aliases_json
        assert "Funzione" in json_string
        assert "it-IT" in json_string
        assert "Fonction" in json_string
        assert "fr-FR" in json_string


class TestUnit:
    """Test Unit model"""
    
    def test_unit_validation_empty_name(self):
        """Test Unit validation with empty name"""
        unit = Unit(name="", unit_type_id=1)
        errors = unit.validate()
        
        assert len(errors) == 1
        assert errors[0].field == "name"
        assert errors[0].message == "Name is required"
    
    def test_unit_validation_invalid_date_range(self):
        """Test Unit validation with invalid date range"""
        unit = Unit(
            name="Test",
            unit_type_id=1,
            start_date=date(2023, 6, 1),
            end_date=date(2023, 1, 1)
        )
        errors = unit.validate()
        
        assert len(errors) == 1
        assert errors[0].field == "end_date"
        assert "after start date" in errors[0].message


class TestPerson:
    """Test Person model"""
    
    def test_person_validation_empty_name(self):
        """Test Person validation with empty name"""
        person = Person(name="")
        errors = person.validate()
        
        assert len(errors) == 1
        assert errors[0].field == "name"
        assert errors[0].message == "Name is required"
    
    def test_person_validation_invalid_email(self):
        """Test Person validation with invalid email"""
        person = Person(name="Test", email="invalid-email")
        errors = person.validate()
        
        assert len(errors) == 1
        assert errors[0].field == "email"
        assert errors[0].message == "Invalid email format"
    
    def test_person_validation_valid_emails(self):
        """Test Person validation with various valid email formats"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@domain.com"
        ]
        
        for email in valid_emails:
            person = Person(name="Test", email=email)
            errors = person.validate()
            assert errors == [], f"Email {email} should be valid"


class TestJobTitle:
    """Test JobTitle model"""
    
    def test_job_title_validation_empty_name(self):
        """Test JobTitle validation with empty name"""
        job_title = JobTitle(name="")
        errors = job_title.validate()
        
        assert len(errors) == 1
        assert errors[0].field == "name"
        assert errors[0].message == "Name is required"
    
    def test_job_title_level_indicator(self):
        """Test JobTitle level indicator property"""
        test_cases = [
            ("Chief Executive Officer", "C-Level"),
            ("CTO", "C-Level"),
            ("Head of Engineering", "Head"),
            ("Engineering Manager", "Manager"),
            ("Responsabile IT", "Manager"),
            ("President", "Executive"),
            ("Software Engineer", "Staff"),
        ]
        
        for name, expected_level in test_cases:
            job_title = JobTitle(name=name)
            assert job_title.level_indicator == expected_level
    
    def test_job_title_alias_management(self):
        """Test JobTitle alias management methods"""
        job_title = JobTitle(name="Software Engineer")
        
        # Add alias
        job_title.add_alias("Ingegnere Software", "it-IT")
        assert len(job_title.aliases) == 1
        assert job_title.get_alias_by_language("it-IT") == "Ingegnere Software"
        
        # Add another alias for different language
        job_title.add_alias("Software-Ingenieur", "de-DE")
        assert len(job_title.aliases) == 2
        
        # Replace existing alias
        job_title.add_alias("Sviluppatore Software", "it-IT")
        assert len(job_title.aliases) == 2
        assert job_title.get_alias_by_language("it-IT") == "Sviluppatore Software"
    
    def test_job_title_localized_name(self):
        """Test JobTitle localized name functionality"""
        job_title = JobTitle(name="Software Engineer")
        job_title.add_alias("Ingegnere Software", "it-IT")
        
        # Should return alias for existing language
        assert job_title.get_localized_name("it-IT") == "Ingegnere Software"
        
        # Should return default name for non-existing language
        assert job_title.get_localized_name("fr-FR") == "Software Engineer"


class TestAssignment:
    """Test Assignment model"""
    
    def test_assignment_validation_invalid_person_id(self):
        """Test Assignment validation with invalid person_id"""
        assignment = Assignment(person_id=0, unit_id=1, job_title_id=1)
        errors = assignment.validate()
        
        assert len(errors) == 1
        assert errors[0].field == "person_id"
        assert errors[0].message == "Person is required"
    
    def test_assignment_validation_invalid_percentage(self):
        """Test Assignment validation with invalid percentage"""
        test_cases = [0.0, -0.1, 1.1, 2.0]
        
        for percentage in test_cases:
            assignment = Assignment(
                person_id=1, unit_id=1, job_title_id=1, percentage=percentage
            )
            errors = assignment.validate()
            
            assert len(errors) == 1
            assert errors[0].field == "percentage"
            assert "between 0 and 100%" in errors[0].message
    
    def test_assignment_percentage_display(self):
        """Test Assignment percentage_display property"""
        assignment = Assignment(
            person_id=1, unit_id=1, job_title_id=1, percentage=1.0
        )
        assert assignment.percentage_display == "100%"
        
        assignment_50 = Assignment(
            person_id=1, unit_id=1, job_title_id=1, percentage=0.5
        )
        assert assignment_50.percentage_display == "50%"


class TestModelValidationException:
    """Test ModelValidationException"""
    
    def test_model_validation_exception_creation(self):
        """Test ModelValidationException creation"""
        errors = [
            ValidationError("name", "Name is required"),
            ValidationError("email", "Invalid email format")
        ]
        
        exception = ModelValidationException(errors)
        
        assert exception.errors == errors
        assert "Validation failed" in str(exception)
        assert "name: Name is required" in str(exception)
        assert "email: Invalid email format" in str(exception)

class TestModelSerialization:
    """Test model serialization and deserialization edge cases"""
    
    def test_unit_from_sqlite_row_with_aliases(self, sample_sqlite_row, unit_row_data):
        """Test Unit creation from SQLite row with aliases"""
        row = sample_sqlite_row(unit_row_data)
        unit = Unit.from_sqlite_row(row)
        
        assert unit.id == 1
        assert unit.name == "IT Department"
        assert unit.aliases[0].value == "Dipartimento IT"
        assert unit.aliases[0].lang == "it-IT"
    
    def test_assignment_from_sqlite_row_with_computed_fields(self, sample_sqlite_row, assignment_row_data):
        """Test Assignment creation from SQLite row with computed fields"""
        row = sample_sqlite_row(assignment_row_data)
        assignment = Assignment.from_sqlite_row(row)
        
        assert assignment.id == 1
        assert assignment.person_name == "Mario Rossi"
        assert assignment.unit_name == "IT Department"
        assert assignment.job_title_name == "Software Engineer"
        assert assignment.percentage_display == "100%"
        assert assignment.status == "CURRENT"
    
    def test_assignment_status_property(self):
        """Test Assignment status property logic"""
        # Current assignment
        current = Assignment(person_id=1, unit_id=1, job_title_id=1, is_current=True)
        assert current.status == "CURRENT"
        
        # Terminated assignment
        terminated = Assignment(
            person_id=1, unit_id=1, job_title_id=1, 
            is_current=False, valid_to=date(2023, 12, 31)
        )
        assert terminated.status == "TERMINATED"
        
        # Historical assignment
        historical = Assignment(
            person_id=1, unit_id=1, job_title_id=1, 
            is_current=False, valid_to=None
        )
        assert historical.status == "HISTORICAL"
    
    def test_unit_display_properties(self):
        """Test Unit display properties"""
        # Unit with short name
        unit_with_short = Unit(name="Information Technology", short_name="IT", unit_type_id=1)
        assert unit_with_short.display_name == "IT"
        
        # Unit without short name
        unit_without_short = Unit(name="Information Technology", unit_type_id=1)
        assert unit_without_short.display_name == "Information Technology"
        
        # Root unit
        root_unit = Unit(name="Company", unit_type_id=1, parent_unit_id=None)
        assert root_unit.is_root is True
        
        # Child unit
        child_unit = Unit(name="Department", unit_type_id=1, parent_unit_id=1)
        assert child_unit.is_root is False


class TestModelValidationEdgeCases:
    """Test model validation edge cases and boundary conditions"""
    
    def test_assignment_validation_edge_cases(self):
        """Test Assignment validation with edge cases"""
        # Valid percentage boundaries
        valid_assignment = Assignment(person_id=1, unit_id=1, job_title_id=1, percentage=0.01)
        errors = valid_assignment.validate()
        assert len(errors) == 0
        
        valid_assignment_100 = Assignment(person_id=1, unit_id=1, job_title_id=1, percentage=1.0)
        errors = valid_assignment_100.validate()
        assert len(errors) == 0
        
        # Invalid percentage - exactly 0
        zero_assignment = Assignment(person_id=1, unit_id=1, job_title_id=1, percentage=0.0)
        errors = zero_assignment.validate()
        assert len(errors) == 1
        assert errors[0].field == "percentage"
    
    def test_unit_validation_date_edge_cases(self):
        """Test Unit validation with date edge cases"""
        # Same start and end date (should be valid)
        same_date_unit = Unit(
            name="Test", unit_type_id=1,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 1)
        )
        errors = same_date_unit.validate()
        assert len(errors) == 0
        
        # End date one day after start date (should be valid)
        valid_range_unit = Unit(
            name="Test", unit_type_id=1,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 2)
        )
        errors = valid_range_unit.validate()
        assert len(errors) == 0
    
    def test_person_email_validation_edge_cases(self):
        """Test Person email validation with edge cases"""
        # Valid email with numbers
        person_numeric = Person(name="Test", email="user123@domain123.com")
        errors = person_numeric.validate()
        assert len(errors) == 0
        
        # Valid email with special characters
        person_special = Person(name="Test", email="user.name+tag@example-domain.co.uk")
        errors = person_special.validate()
        assert len(errors) == 0
        
        # Invalid email - missing @ symbol
        person_no_at = Person(name="Test", email="userdomain.com")
        errors = person_no_at.validate()
        assert len(errors) == 1
        assert errors[0].field == "email"


class TestModelAliasHandling:
    """Test model alias handling functionality"""
    
    def test_alias_parsing_from_json_string(self):
        """Test parsing aliases from JSON string"""
        json_aliases = '[{"value": "Test Value", "lang": "en-US"}, {"value": "Valore Test", "lang": "it-IT"}]'
        aliases = parse_aliases(json_aliases)
        
        assert len(aliases) == 2
        assert aliases[0].value == "Test Value"
        assert aliases[0].lang == "en-US"
        assert aliases[1].value == "Valore Test"
        assert aliases[1].lang == "it-IT"
    
    def test_alias_serialization_to_json(self):
        """Test serializing aliases to JSON string"""
        aliases = [
            Alias("Test Value", "en-US"),
            Alias("Valore Test", "it-IT")
        ]
        json_string = serialize_aliases(aliases)
        
        # Parse back to verify
        parsed_aliases = parse_aliases(json_string)
        assert len(parsed_aliases) == 2
        assert parsed_aliases[0].value == "Test Value"
        assert parsed_aliases[1].value == "Valore Test"
    
    def test_unit_post_init_alias_parsing(self):
        """Test Unit post-init alias parsing"""
        # Create unit with string aliases (simulating database load)
        unit_data = {
            'name': 'Test Unit',
            'unit_type_id': 1,
            'aliases': '[{"value": "Unità Test", "lang": "it-IT"}]'
        }
        unit = Unit(**unit_data)
        
        # Post-init should have parsed the string into Alias objects
        assert len(unit.aliases) == 1
        assert isinstance(unit.aliases[0], Alias)
        assert unit.aliases[0].value == "Unità Test"
        assert unit.aliases[0].lang == "it-IT"


class TestModelBusinessLogic:
    """Test model business logic and computed properties"""
    
    def test_assignment_percentage_display_formatting(self):
        """Test Assignment percentage display formatting"""
        test_cases = [
            (0.01, "1%"),
            (0.25, "25%"),
            (0.5, "50%"),
            (0.75, "75%"),
            (1.0, "100%"),
            (0.333, "33%"),  # Should round to nearest integer
            (0.666, "67%")   # Should round to nearest integer
        ]
        
        for percentage, expected in test_cases:
            assignment = Assignment(person_id=1, unit_id=1, job_title_id=1, percentage=percentage)
            assert assignment.percentage_display == expected
    
    def test_unit_aliases_json_property(self):
        """Test Unit aliases_json property"""
        unit = Unit(
            name="Test Unit",
            unit_type_id=1,
            aliases=[Alias("Unità Test", "it-IT"), Alias("Test Einheit", "de-DE")]
        )
        
        json_string = unit.aliases_json
        assert "Unità Test" in json_string
        assert "it-IT" in json_string
        assert "Test Einheit" in json_string
        assert "de-DE" in json_string
    
    def test_model_audit_fields_behavior(self):
        """Test model audit fields behavior"""
        model = BaseModel()
        
        # Test create audit fields
        model.set_audit_fields(is_update=False)
        assert model.datetime_created is not None
        assert model.datetime_updated is not None
        
        # Store original created time
        original_created = model.datetime_created
        
        # Test update audit fields
        model.set_audit_fields(is_update=True)
        assert model.datetime_created == original_created  # Should not change
        assert model.datetime_updated != original_created  # Should be updated


class TestModelComplexValidation:
    """Test complex model validation scenarios"""
    
    def test_unit_circular_reference_validation(self):
        """Test Unit validation prevents circular references"""
        unit = Unit(id=1, name="Test Unit", unit_type_id=1, parent_unit_id=1)
        errors = unit.validate()
        
        assert len(errors) == 1
        assert errors[0].field == "parent_unit_id"
        assert "cannot be its own parent" in errors[0].message
    
    def test_unit_active_status_property(self):
        """Test Unit is_active property logic"""
        from datetime import date, timedelta
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Active unit (no dates)
        active_unit = Unit(name="Active", unit_type_id=1)
        assert active_unit.is_active is True
        
        # Active unit (started yesterday)
        started_unit = Unit(name="Started", unit_type_id=1, start_date=yesterday)
        assert started_unit.is_active is True
        
        # Inactive unit (starts tomorrow)
        future_unit = Unit(name="Future", unit_type_id=1, start_date=tomorrow)
        assert future_unit.is_active is False
        
        # Inactive unit (ended yesterday)
        ended_unit = Unit(name="Ended", unit_type_id=1, end_date=yesterday)
        assert ended_unit.is_active is False
    
    def test_person_initials_property(self):
        """Test Person initials property"""
        test_cases = [
            ("Mario Rossi", "MR"),
            ("Anna Maria Bianchi", "AMB"),
            ("Giuseppe", "G"),
            ("", ""),
            ("   ", ""),
            ("Mario  Rossi", "MR"),  # Multiple spaces
        ]
        
        for name, expected_initials in test_cases:
            person = Person(name=name)
            assert person.initials == expected_initials
    
    def test_assignment_version_validation_edge_cases(self):
        """Test Assignment validation with version edge cases"""
        # Valid assignment with minimum percentage
        valid_assignment = Assignment(
            person_id=1, unit_id=1, job_title_id=1, 
            percentage=0.01, version=1
        )
        errors = valid_assignment.validate()
        assert len(errors) == 0
        
        # Invalid assignment with zero percentage
        zero_assignment = Assignment(
            person_id=1, unit_id=1, job_title_id=1, 
            percentage=0.0, version=1
        )
        errors = zero_assignment.validate()
        assert len(errors) == 1
        assert errors[0].field == "percentage"
    
    def test_model_serialization_with_none_values(self):
        """Test model serialization handles None values correctly"""
        unit = Unit(name="Test", unit_type_id=1, short_name=None, end_date=None)
        result = unit.to_dict()
        
        assert result['name'] == "Test"
        assert result['short_name'] is None
        assert result['end_date'] is None
        assert 'unit_type_id' in result
    
    def test_model_from_dict_with_missing_fields(self):
        """Test model creation from dict with missing optional fields"""
        minimal_data = {'name': 'Test Unit', 'unit_type_id': 1}
        unit = Unit.from_dict(minimal_data)
        
        assert unit.name == "Test Unit"
        assert unit.unit_type_id == 1
        assert unit.short_name is None
        assert unit.aliases == []


class TestModelErrorHandling:
    """Test model error handling and edge cases"""
    
    def test_base_model_validate_and_raise_success(self):
        """Test BaseModel validate_and_raise with valid model"""
        model = BaseModel()
        # Should not raise exception for valid base model
        model.validate_and_raise()
    
    def test_base_model_validate_and_raise_failure(self):
        """Test BaseModel validate_and_raise with invalid model"""
        person = Person(name="")  # Invalid - empty name
        
        with pytest.raises(ModelValidationException) as exc_info:
            person.validate_and_raise()
        
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0].field == "name"
    
    def test_alias_parsing_malformed_json(self):
        """Test alias parsing with malformed JSON"""
        from app.models.base import parse_aliases
        
        # Test various malformed JSON inputs
        malformed_inputs = [
            '{"invalid": json}',  # Invalid JSON
            '[{"value": "test"}',  # Incomplete JSON
            'not json at all',     # Not JSON
            None,                  # None input
            '',                    # Empty string
        ]
        
        for malformed_input in malformed_inputs:
            aliases = parse_aliases(malformed_input)
            assert isinstance(aliases, list)
            # Should return empty list for malformed input
            if malformed_input not in [None, '']:
                assert len(aliases) == 0
    
    def test_unit_date_parsing_edge_cases(self):
        """Test Unit date parsing with various edge cases"""
        # Test with invalid date strings
        row_data = {
            'id': 1,
            'name': 'Test Unit',
            'unit_type_id': 1,
            'start_date': 'invalid-date',
            'end_date': '2023-13-45',  # Invalid date
            'aliases': '[]'
        }
        
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def __contains__(self, key):
                return key in self._data
            def get(self, key, default=None):
                return self._data.get(key, default)
            def keys(self):
                return self._data.keys()
            def values(self):
                return self._data.values()
            def items(self):
                return self._data.items()
            def __iter__(self):
                return iter(self._data)
        
        row = MockRow(row_data)
        unit = Unit.from_sqlite_row(row)
        
        # Should handle invalid dates gracefully
        assert unit.start_date is None
        assert unit.end_date is None
        assert unit.name == "Test Unit"