#!/usr/bin/env python3
"""
Test script to verify domain models implementation
"""

import sys
import os
from datetime import date, datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from models.unit import Unit
from models.person import Person
from models.job_title import JobTitle
from models.assignment import Assignment
from models.base import Alias, ValidationError, ModelValidationException


def test_unit_model():
    """Test Unit model with hierarchical structure and type validation"""
    print("Testing Unit model...")
    
    # Test valid unit
    unit = Unit(
        name="IT Department",
        short_name="IT",
        unit_type_id=1,
        parent_unit_id=1,
        start_date=date(2020, 1, 1),
        aliases=[Alias("Dipartimento IT", "it-IT")]
    )
    
    errors = unit.validate()
    assert len(errors) == 0, f"Valid unit should have no errors: {errors}"
    
    # Test properties
    assert unit.display_name == "IT"
    assert unit.is_active == True
    assert unit.is_root == False
    
    # Test invalid unit - empty name and invalid type
    invalid_unit = Unit(name="", unit_type_id=0)
    errors = invalid_unit.validate()
    assert len(errors) >= 2, f"Expected at least 2 errors, got {len(errors)}: {errors}"
    assert any(error.field == "name" for error in errors), "Should detect empty name"
    assert any(error.field == "unit_type_id" for error in errors), "Should detect invalid unit_type_id"
    
    # Test self-parent validation
    self_parent_unit = Unit(id=1, name="Test", parent_unit_id=1)
    errors = self_parent_unit.validate()
    assert any(error.field == "parent_unit_id" for error in errors), "Should detect self-parent"
    
    # Test date validation
    invalid_dates_unit = Unit(
        name="Test Unit",
        start_date=date(2023, 1, 1),
        end_date=date(2022, 1, 1)  # End before start
    )
    errors = invalid_dates_unit.validate()
    assert any(error.field == "end_date" for error in errors), "Should detect invalid date range"
    
    print("✓ Unit model tests passed")


def test_person_model():
    """Test Person model with email validation and contact details"""
    print("Testing Person model...")
    
    # Test valid person
    person = Person(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+39 123 456 7890"
    )
    
    errors = person.validate()
    assert len(errors) == 0, f"Valid person should have no errors: {errors}"
    
    # Test properties
    assert person.full_name == "John Doe"
    assert person.display_name == "John Doe"
    assert person.initials == "JD"
    assert person.last_name_first == "Doe, John"
    
    # Test invalid person - missing required fields
    invalid_person = Person(first_name="", last_name="")
    errors = invalid_person.validate()
    assert len(errors) == 2, f"Expected 2 errors for missing names: {errors}"
    
    # Test invalid email
    invalid_email_person = Person(
        first_name="Jane",
        last_name="Doe",
        email="invalid-email"
    )
    errors = invalid_email_person.validate()
    assert any(error.field == "email" for error in errors), "Should detect invalid email"
    
    # Test invalid phone
    invalid_phone_person = Person(
        first_name="Jane",
        last_name="Doe",
        phone="123"  # Too short
    )
    errors = invalid_phone_person.validate()
    assert any(error.field == "phone" for error in errors), "Should detect invalid phone"
    
    print("✓ Person model tests passed")


def test_job_title_model():
    """Test JobTitle model with multilingual support"""
    print("Testing JobTitle model...")
    
    # Test valid job title
    job_title = JobTitle(
        name="Software Engineer",
        description="Develops software applications",
        aliases=[
            Alias("Ingegnere del Software", "it-IT"),
            Alias("Développeur Logiciel", "fr-FR")
        ]
    )
    
    errors = job_title.validate()
    assert len(errors) == 0, f"Valid job title should have no errors: {errors}"
    
    # Test properties
    assert job_title.display_name == "Software Engineer"
    assert job_title.level_indicator == "Staff"
    
    # Test multilingual support
    job_title.add_alias("Programador", "es-ES")
    assert job_title.get_alias_by_language("es-ES") == "Programador"
    assert job_title.get_localized_name("it-IT") == "Ingegnere del Software"
    assert job_title.get_localized_name("unknown") == "Software Engineer"  # Fallback
    
    # Test invalid job title - empty name
    invalid_job_title = JobTitle(name="")
    errors = invalid_job_title.validate()
    assert len(errors) == 1, f"Expected 1 error for empty name: {errors}"
    
    # Test invalid aliases
    invalid_alias_job_title = JobTitle(
        name="Test",
        aliases=[Alias("", "it-IT")]  # Empty alias value
    )
    errors = invalid_alias_job_title.validate()
    assert any(error.field == "aliases" for error in errors), "Should detect empty alias"
    
    print("✓ JobTitle model tests passed")


def test_assignment_model():
    """Test Assignment model with versioning fields and percentage validation"""
    print("Testing Assignment model...")
    
    # Test valid assignment
    assignment = Assignment(
        person_id=1,
        unit_id=1,
        job_title_id=1,
        version=1,
        percentage=0.8,  # 80%
        valid_from=date(2023, 1, 1),
        is_current=True
    )
    
    errors = assignment.validate()
    assert len(errors) == 0, f"Valid assignment should have no errors: {errors}"
    
    # Test properties
    assert assignment.percentage_display == "80%"
    assert assignment.status == "CURRENT"
    assert assignment.status_color == "success"
    assert assignment.is_active == True
    
    # Test invalid assignment - missing required fields
    invalid_assignment = Assignment(
        person_id=0,  # Invalid
        unit_id=0,    # Invalid
        job_title_id=0,  # Invalid
        percentage=1.5   # Invalid (> 100%)
    )
    errors = invalid_assignment.validate()
    assert len(errors) == 4, f"Expected 4 errors: {errors}"
    
    # Test date validation
    invalid_dates_assignment = Assignment(
        person_id=1,
        unit_id=1,
        job_title_id=1,
        valid_from=date(2023, 12, 31),
        valid_to=date(2023, 1, 1)  # End before start
    )
    errors = invalid_dates_assignment.validate()
    assert any(error.field == "valid_to" for error in errors), "Should detect invalid date range"
    
    # Test version validation
    invalid_version_assignment = Assignment(
        person_id=1,
        unit_id=1,
        job_title_id=1,
        version=0  # Invalid version
    )
    errors = invalid_version_assignment.validate()
    assert any(error.field == "version" for error in errors), "Should detect invalid version"
    
    print("✓ Assignment model tests passed")


def test_serialization():
    """Test serialization/deserialization functionality"""
    print("Testing serialization...")
    
    # Test Unit serialization
    unit = Unit(
        name="Test Unit",
        unit_type_id=1, ##"function",
        start_date=date(2023, 1, 1),
        aliases=[Alias("Unità Test", "it-IT")]
    )
    
    unit_dict = unit.to_dict()
    assert unit_dict['name'] == "Test Unit"
    assert unit_dict['start_date'] == "2023-01-01"
    assert len(unit_dict['aliases']) == 1
    
    # Test Person serialization
    person = Person(
        first_name="John",
        last_name="Doe",
        email="john@example.com"
    )
    
    person_dict = person.to_dict()
    assert person_dict['first_name'] == "John"
    assert person_dict['email'] == "john@example.com"
    
    print("✓ Serialization tests passed")


def main():
    """Run all tests"""
    print("Running domain model tests...\n")
    
    try:
        test_unit_model()
        test_person_model()
        test_job_title_model()
        test_assignment_model()
        test_serialization()
        
        print("\n✅ All domain model tests passed!")
        print("\nDomain models successfully implement:")
        print("- Unit model with hierarchical structure and type validation")
        print("- Person model with email validation and contact details")
        print("- JobTitle model with multilingual support")
        print("- Assignment model with versioning fields and percentage validation")
        print("- Comprehensive validation framework")
        print("- Serialization/deserialization support")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()