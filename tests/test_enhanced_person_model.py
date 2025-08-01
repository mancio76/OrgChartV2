"""
Unit tests for enhanced Person model with new fields.

This module tests the enhanced Person model including:
- first_name, last_name, registration_no, profile_image fields
- suggested_name_format property
- display_name property
- profile image handling
- backward compatibility with name field

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 6.1, 6.2, 6.4
"""

import pytest
from datetime import date, datetime
from app.models.person import Person
from app.models.base import ValidationError


class TestEnhancedPersonModel:
    """Test enhanced Person model with new fields"""
    
    def test_person_creation_with_enhanced_fields(self):
        """Test Person creation with all enhanced fields"""
        person = Person(
            name="Mario Rossi",
            first_name="Mario",
            last_name="Rossi",
            registration_no="EMP001",
            profile_image="mario_rossi.jpg",
            email="mario.rossi@example.com",
            short_name="M. Rossi"
        )
        
        assert person.name == "Mario Rossi"
        assert person.first_name == "Mario"
        assert person.last_name == "Rossi"
        assert person.registration_no == "EMP001"
        assert person.profile_image == "mario_rossi.jpg"
        assert person.email == "mario.rossi@example.com"
        assert person.short_name == "M. Rossi"
    
    def test_suggested_name_format_property(self):
        """Test suggested_name_format property generation (Requirement 2.1)"""
        test_cases = [
            # (first_name, last_name, expected_format)
            ("Mario", "Rossi", "Rossi, Mario"),
            ("Anna", "Bianchi", "Bianchi, Anna"),
            ("Giuseppe", "Verdi", "Verdi, Giuseppe"),
            ("Maria Luisa", "De Sanctis", "De Sanctis, Maria Luisa"),
            ("", "Rossi", "Rossi"),  # Empty first name
            ("Mario", "", "Mario"),  # Empty last name
            ("", "", "Test"),  # Both empty, falls back to name
        ]
        
        for first_name, last_name, expected in test_cases:
            person = Person(
                name="Test",
                first_name=first_name if first_name else None,
                last_name=last_name if last_name else None
            )
            assert person.suggested_name_format == expected
    
    def test_suggested_name_format_with_none_values(self):
        """Test suggested_name_format with None values"""
        person = Person(name="Test")
        # When first_name and last_name are None
        assert person.suggested_name_format == "Test"
        
        person.first_name = "Mario"
        person.last_name = None
        assert person.suggested_name_format == "Mario"
        
        person.first_name = None
        person.last_name = "Rossi"
        assert person.suggested_name_format == "Rossi"
    
    def test_display_name_property(self):
        """Test display_name property logic (Requirement 1.1, 1.2)"""
        # Test with first_name and last_name available
        person = Person(
            name="Mario Rossi",
            first_name="Mario",
            last_name="Rossi"
        )
        assert person.display_name == "Mario Rossi"
        
        # Test with only first_name
        person = Person(
            name="Mario Rossi",
            first_name="Mario",
            last_name=""
        )
        assert person.display_name == "Mario"
        
        # Test with only last_name
        person = Person(
            name="Mario Rossi",
            first_name="",
            last_name="Rossi"
        )
        assert person.display_name == "Rossi"
        
        # Test fallback to name field
        person = Person(
            name="Mario Rossi",
            first_name="",
            last_name=""
        )
        assert person.display_name == "Mario Rossi"
        
        # Test with None values
        person = Person(
            name="Mario Rossi",
            first_name=None,
            last_name=None
        )
        assert person.display_name == "Mario Rossi"
    
    def test_registration_no_validation(self):
        """Test registration_no field validation (Requirement 1.5)"""
        # Valid registration number
        person = Person(
            name="Test",
            registration_no="EMP001"
        )
        errors = person.validate()
        assert not any(error.field == "registration_no" for error in errors)
        
        # Registration number at max length (25 chars)
        person = Person(
            name="Test",
            registration_no="A" * 25
        )
        errors = person.validate()
        assert not any(error.field == "registration_no" for error in errors)
        
        # Registration number too long (26 chars)
        person = Person(
            name="Test",
            registration_no="A" * 26
        )
        errors = person.validate()
        assert any(
            error.field == "registration_no" and 
            "25 characters" in error.message 
            for error in errors
        )
    
    def test_profile_image_validation(self):
        """Test profile_image field validation (Requirement 6.1, 6.4)"""
        # Valid profile image path
        person = Person(
            name="Test",
            profile_image="mario_rossi.jpg"
        )
        errors = person.validate()
        assert not any(error.field == "profile_image" for error in errors)
        
        # Profile image at max length (1024 chars) with valid extension
        long_path = "a" * 1020 + ".jpg"  # 1024 chars total
        person = Person(
            name="Test",
            profile_image=long_path
        )
        errors = person.validate()
        assert not any(error.field == "profile_image" for error in errors)
        
        # Profile image too long (1025 chars)
        person = Person(
            name="Test",
            profile_image="A" * 1025
        )
        errors = person.validate()
        assert any(
            error.field == "profile_image" and 
            "1024 characters" in error.message 
            for error in errors
        )
        
        # Empty profile image when provided should be invalid
        person = Person(
            name="Test",
            profile_image=""
        )
        errors = person.validate()
        assert any(error.field == "profile_image" for error in errors)
        
        # Invalid image extension
        person = Person(
            name="Test",
            profile_image="document.txt"
        )
        errors = person.validate()
        assert any(error.field == "profile_image" for error in errors)
    
    def test_first_name_validation(self):
        """Test first_name field validation (Requirement 1.3)"""
        # Valid first name
        person = Person(
            name="Test",
            first_name="Mario"
        )
        errors = person.validate()
        assert not any(error.field == "first_name" for error in errors)
        
        # Empty first name when provided should be invalid
        person = Person(
            name="Test",
            first_name=""
        )
        errors = person.validate()
        assert any(error.field == "first_name" for error in errors)
    
    def test_last_name_validation(self):
        """Test last_name field validation (Requirement 1.4)"""
        # Valid last name
        person = Person(
            name="Test",
            last_name="Rossi"
        )
        errors = person.validate()
        assert not any(error.field == "last_name" for error in errors)
        
        # Empty last name when provided should be invalid
        person = Person(
            name="Test",
            last_name=""
        )
        errors = person.validate()
        assert any(error.field == "last_name" for error in errors)
    
    def test_profile_image_properties(self):
        """Test profile image related properties (Requirement 6.4)"""
        # Person without profile image
        person = Person(name="Test")
        assert person.has_profile_image is False
        assert person.profile_image_url == ""
        
        # Person with empty profile image
        person = Person(name="Test", profile_image="")
        assert person.has_profile_image is False
        assert person.profile_image_url == ""
        
        # Person with profile image
        person = Person(name="Test", profile_image="mario_rossi.jpg")
        assert person.has_profile_image is True
        assert person.profile_image_url == "/static/profiles/mario_rossi.jpg"
    
    def test_initials_property_with_enhanced_fields(self):
        """Test initials property with enhanced fields"""
        # Test with first_name and last_name
        person = Person(
            name="Mario Rossi",
            first_name="Mario",
            last_name="Rossi"
        )
        assert person.initials == "MR"
        
        # Test with only first_name
        person = Person(
            name="Mario Rossi",
            first_name="Mario",
            last_name=""
        )
        assert person.initials == "M"
        
        # Test with only last_name
        person = Person(
            name="Mario Rossi",
            first_name="",
            last_name="Rossi"
        )
        assert person.initials == "R"
        
        # Test fallback to name field
        person = Person(
            name="Mario Rossi",
            first_name="",
            last_name=""
        )
        assert person.initials == "MR"
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing name field (Requirement 5.3)"""
        # Person created with only name field (old way)
        person = Person(name="Mario Rossi")
        
        # Should still work with all properties
        assert person.name == "Mario Rossi"
        assert person.display_name == "Mario Rossi"
        assert person.initials == "MR"
        
        # Validation should still work
        errors = person.validate()
        assert not any(error.field == "name" for error in errors)
    
    def test_from_sqlite_row_with_enhanced_fields(self):
        """Test from_sqlite_row method with enhanced fields"""
        # Mock SQLite row with all fields
        row_data = {
            'id': 1,
            'name': "Mario Rossi",
            'first_name': "Mario",
            'last_name': "Rossi",
            'registration_no': "EMP001",
            'profile_image': "mario_rossi.jpg",
            'short_name': "M. Rossi",
            'email': "mario.rossi@example.com",
            'current_assignments_count': 0,
            'total_assignments_count': 0,
            'datetime_created': "2023-01-01 10:00:00",
            'datetime_updated': "2023-01-02 11:00:00"
        }
        
        # Create a mock row that behaves like a SQLite row
        class MockRow:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
            
            def __iter__(self):
                return iter(self.__dict__.items())
            
            def keys(self):
                return self.__dict__.keys()
            
            def __getitem__(self, key):
                return self.__dict__[key]
        
        row = MockRow(row_data)
        person = Person.from_sqlite_row(row)
        
        assert person.id == 1
        assert person.name == "Mario Rossi"
        assert person.first_name == "Mario"
        assert person.last_name == "Rossi"
        assert person.registration_no == "EMP001"
        assert person.profile_image == "mario_rossi.jpg"
        assert person.short_name == "M. Rossi"
        assert person.email == "mario.rossi@example.com"
    
    def test_from_sqlite_row_with_none_values(self):
        """Test from_sqlite_row method with None values for enhanced fields"""
        row_data = {
            'id': 1,
            'name': "Mario Rossi",
            'first_name': None,
            'last_name': None,
            'registration_no': None,
            'profile_image': None,
            'short_name': None,
            'email': None,
            'current_assignments_count': 0,
            'total_assignments_count': 0,
            'datetime_created': "2023-01-01 10:00:00",
            'datetime_updated': "2023-01-02 11:00:00"
        }
        
        # Create a mock row that behaves like a SQLite row
        class MockRow:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
            
            def __iter__(self):
                return iter(self.__dict__.items())
            
            def keys(self):
                return self.__dict__.keys()
            
            def __getitem__(self, key):
                return self.__dict__[key]
        
        row = MockRow(row_data)
        person = Person.from_sqlite_row(row)
        
        assert person.id == 1
        assert person.name == "Mario Rossi"
        assert person.first_name is None
        assert person.last_name is None
        assert person.registration_no is None
        assert person.profile_image is None
        assert person.short_name is None
        assert person.email is None
    
    def test_multiple_validation_errors(self):
        """Test multiple validation errors at once"""
        person = Person(
            name="",  # Required field empty
            first_name="",  # Empty when provided
            last_name="",   # Empty when provided
            registration_no="C" * 26,  # Too long
            profile_image="D" * 1025,  # Too long
            email="invalid-email"  # Invalid format
        )
        
        errors = person.validate()
        
        # Should have multiple errors
        assert len(errors) >= 3
        
        # Check specific error fields
        error_fields = [error.field for error in errors]
        assert "registration_no" in error_fields
        assert "profile_image" in error_fields
        assert "email" in error_fields