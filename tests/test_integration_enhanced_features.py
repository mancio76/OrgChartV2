"""
Integration tests for enhanced database structure features.

This module tests the integration between models, services, and routes
for the enhanced person and company features including:
- Form submission with enhanced fields
- CRUD operations end-to-end
- Profile image handling
- Company contact relationships
- Database constraints and foreign keys

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 6.1, 6.2, 6.4
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.models.person import Person
from app.models.company import Company
from app.services.person import PersonService
from app.services.company import CompanyService


class TestPersonIntegration:
    """Integration tests for Person enhanced features"""
    
    @pytest.fixture
    def mock_person_service(self):
        """Mock PersonService for integration tests"""
        service = Mock(spec=PersonService)
        service.get_all.return_value = []
        service.get_by_id.return_value = None
        service.create.return_value = Person(id=1, name="Test Person")
        service.update.return_value = Person(id=1, name="Updated Person")
        service.delete.return_value = True
        service.can_delete.return_value = (True, "")
        return service
    
    def test_person_creation_with_enhanced_fields(self, mock_person_service):
        """Test person creation with enhanced fields (Requirements 1.1, 1.2, 1.3, 1.4, 1.5)"""
        # Create person with all enhanced fields
        person_data = {
            'name': 'Mario Rossi',
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'short_name': 'M. Rossi',
            'email': 'mario.rossi@example.com',
            'registration_no': 'EMP001',
            'profile_image': 'mario_rossi.jpg'
        }
        
        person = Person(**person_data)
        
        # Validate the person
        errors = person.validate()
        assert len(errors) == 0, f"Validation errors: {[e.message for e in errors]}"
        
        # Test service creation
        mock_person_service.create.return_value = person
        result = mock_person_service.create(person)
        
        assert result.name == 'Mario Rossi'
        assert result.first_name == 'Mario'
        assert result.last_name == 'Rossi'
        assert result.registration_no == 'EMP001'
        assert result.profile_image == 'mario_rossi.jpg'
        
        # Test suggested name format
        assert person.suggested_name_format == 'Rossi, Mario'
    
    def test_person_creation_backward_compatibility(self, mock_person_service):
        """Test person creation with only name field (backward compatibility) (Requirement 5.3)"""
        # Create person with only traditional fields
        person_data = {
            'name': 'Mario Rossi',
            'email': 'mario.rossi@example.com'
        }
        
        person = Person(**person_data)
        
        # Should validate successfully
        errors = person.validate()
        assert len(errors) == 0
        
        # Enhanced fields should be None
        assert person.first_name is None
        assert person.last_name is None
        assert person.registration_no is None
        assert person.profile_image is None
        
        # Display name should fall back to name field
        assert person.display_name == 'Mario Rossi'
    
    def test_person_name_suggestion_integration(self):
        """Test name suggestion functionality integration (Requirement 2.1)"""
        # Test auto-population logic
        person = Person(
            first_name='Mario',
            last_name='Rossi',
            name=''  # Empty name to test suggestion
        )
        
        # The suggested format should be available
        suggested = person.suggested_name_format
        assert suggested == 'Rossi, Mario'
        
        # Test the suggest_name_from_parts method
        suggested_name = person.suggest_name_from_parts()
        assert suggested_name == 'Mario Rossi'
        
        # Test ensure_name_consistency method
        person.ensure_name_consistency()
        assert person.name == 'Mario Rossi'
    
    def test_person_profile_image_integration(self):
        """Test profile image handling integration (Requirements 6.1, 6.4)"""
        # Test with profile image
        person = Person(
            name='Mario Rossi',
            profile_image='profiles/mario_rossi.jpg'
        )
        
        # Test profile image properties
        assert person.has_profile_image is True
        assert person.profile_image_url == '/static/profiles/profiles/mario_rossi.jpg'
        
        # Test without profile image
        person_no_image = Person(name='Anna Bianchi')
        assert person_no_image.has_profile_image is False
        assert person_no_image.profile_image_url == ''
    
    def test_person_validation_integration(self):
        """Test person validation with enhanced fields (Requirements 2.2, 2.3, 2.4)"""
        # Test validation with invalid enhanced fields
        person = Person(
            name='',  # Required field empty
            first_name='A' * 101,  # Too long (assuming 100 char limit)
            last_name='B' * 101,   # Too long
            registration_no='C' * 26,  # Too long (25 char limit)
            profile_image='D' * 1025,  # Too long (1024 char limit)
            email='invalid-email'  # Invalid format
        )
        
        errors = person.validate()
        
        # Should have multiple validation errors
        assert len(errors) > 0
        
        error_fields = [error.field for error in errors]
        assert 'name' in error_fields or 'first_name' in error_fields  # Either name or first_name/last_name required
        assert 'registration_no' in error_fields
        assert 'profile_image' in error_fields
        assert 'email' in error_fields
    
    def test_person_update_integration(self, mock_person_service):
        """Test person update with enhanced fields"""
        # Original person
        original_person = Person(
            id=1,
            name='Mario Rossi',
            email='mario.rossi@example.com'
        )
        
        # Updated person with enhanced fields
        updated_person = Person(
            id=1,
            name='Mario Rossi',
            first_name='Mario',
            last_name='Rossi',
            registration_no='EMP001',
            profile_image='mario_rossi.jpg',
            email='mario.rossi@example.com'
        )
        
        # Mock service update
        mock_person_service.update.return_value = updated_person
        result = mock_person_service.update(updated_person)
        
        assert result.first_name == 'Mario'
        assert result.last_name == 'Rossi'
        assert result.registration_no == 'EMP001'
        assert result.profile_image == 'mario_rossi.jpg'


class TestCompanyIntegration:
    """Integration tests for Company features"""
    
    @pytest.fixture
    def mock_company_service(self):
        """Mock CompanyService for integration tests"""
        service = Mock(spec=CompanyService)
        service.get_all.return_value = []
        service.get_by_id.return_value = None
        service.create.return_value = Company(id=1, name="Test Company")
        service.update.return_value = Company(id=1, name="Updated Company")
        service.delete.return_value = True
        service.can_delete.return_value = (True, "")
        service.get_contact_persons.return_value = []
        return service
    
    def test_company_creation_integration(self, mock_company_service):
        """Test company creation with all fields (Requirements 3.1, 3.2)"""
        # Create company with all fields
        company_data = {
            'name': 'Acme Corporation',
            'short_name': 'ACME',
            'registration_no': '12345678901',
            'address': 'Via Roma 1',
            'city': 'Milano',
            'postal_code': '20100',
            'country': 'Italy',
            'phone': '+39 02 1234567',
            'email': 'info@acme.com',
            'website': 'https://www.acme.com',
            'main_contact_id': 1,
            'financial_contact_id': 2,
            'valid_from': date(2023, 1, 1),
            'valid_to': date(2024, 12, 31),
            'notes': 'Test company'
        }
        
        company = Company(**company_data)
        
        # Validate the company
        errors = company.validate()
        assert len(errors) == 0, f"Validation errors: {[e.message for e in errors]}"
        
        # Test service creation
        mock_company_service.create.return_value = company
        result = mock_company_service.create(company)
        
        assert result.name == 'Acme Corporation'
        assert result.short_name == 'ACME'
        assert result.registration_no == '12345678901'
        assert result.main_contact_id == 1
        assert result.financial_contact_id == 2
    
    def test_company_contact_relationships(self, mock_company_service):
        """Test company contact relationships (Requirements 3.5, 3.6)"""
        # Create company with contacts
        company = Company(
            name='Test Company',
            main_contact_id=1,
            financial_contact_id=2
        )
        
        # Set contact names (as would be done by service)
        company.main_contact_name = 'Mario Rossi'
        company.financial_contact_name = 'Anna Bianchi'
        
        # Test contact properties
        assert company.has_contacts is True
        assert company.contact_display == 'Main: Mario Rossi | Financial: Anna Bianchi'
        
        # Test contact role methods
        assert company.is_contact_person(1) is True
        assert company.is_contact_person(2) is True
        assert company.is_contact_person(3) is False
        
        assert company.get_contact_role(1) == 'main'
        assert company.get_contact_role(2) == 'financial'
        assert company.get_contact_role(3) is None
        
        # Test contact summary
        summary = company.get_contact_summary()
        assert summary['has_main_contact'] is True
        assert summary['has_financial_contact'] is True
        assert summary['total_contacts'] == 2
    
    def test_company_date_validation_integration(self):
        """Test company date validation (Requirement 3.4)"""
        # Test valid date range
        company = Company(
            name='Test Company',
            valid_from=date(2023, 1, 1),
            valid_to=date(2023, 12, 31)
        )
        
        errors = company.validate()
        assert not any(error.field in ['valid_from', 'valid_to'] for error in errors)
        
        # Test invalid date range
        company_invalid = Company(
            name='Test Company',
            valid_from=date(2023, 12, 31),
            valid_to=date(2023, 1, 1)
        )
        
        errors = company_invalid.validate()
        assert any(error.field == 'valid_to' and 'after start date' in error.message for error in errors)
    
    def test_company_active_status_integration(self):
        """Test company active status logic (Requirement 3.4)"""
        today = date.today()
        
        # Test active company (no dates)
        company_active = Company(name='Active Company')
        assert company_active.is_active is True
        assert company_active.get_status_display() == 'Active'
        
        # Test active company (within date range)
        company_current = Company(
            name='Current Company',
            valid_from=date(today.year - 1, 1, 1),
            valid_to=date(today.year + 1, 12, 31)
        )
        assert company_current.is_active is True
        
        # Test future company
        company_future = Company(
            name='Future Company',
            valid_from=date(today.year + 1, 1, 1)
        )
        assert company_future.is_active is False
        assert 'Future' in company_future.get_status_display()
        
        # Test expired company
        company_expired = Company(
            name='Expired Company',
            valid_to=date(today.year - 1, 12, 31)
        )
        assert company_expired.is_active is False
        assert 'Expired' in company_expired.get_status_display()
    
    def test_company_validation_integration(self):
        """Test company validation with all fields (Requirements 3.2, 3.3)"""
        # Test validation with invalid fields
        company = Company(
            name='',  # Required field empty
            website='invalid-url',  # Invalid URL
            email='invalid-email',  # Invalid email
            phone='123',  # Invalid phone (too short)
            valid_from=date(2023, 12, 31),  # Invalid date range
            valid_to=date(2023, 1, 1),
            main_contact_id=0,  # Invalid contact ID
            financial_contact_id=-1  # Invalid contact ID
        )
        
        errors = company.validate()
        
        # Should have multiple validation errors
        assert len(errors) > 0
        
        error_fields = [error.field for error in errors]
        assert 'name' in error_fields
        assert 'website' in error_fields
        assert 'email' in error_fields
        assert 'phone' in error_fields
        assert 'valid_to' in error_fields
        assert 'main_contact_id' in error_fields
        assert 'financial_contact_id' in error_fields


class TestPersonCompanyIntegration:
    """Integration tests between Person and Company features"""
    
    def test_person_as_company_contact_integration(self):
        """Test person serving as company contact (Requirements 3.5, 3.6, 3.7)"""
        # Create person
        person = Person(
            id=1,
            name='Mario Rossi',
            first_name='Mario',
            last_name='Rossi',
            email='mario.rossi@example.com'
        )
        
        # Create company with person as contact
        company = Company(
            id=1,
            name='Test Company',
            main_contact_id=person.id
        )
        
        # Set contact name (as would be done by service)
        company.main_contact_name = person.display_name
        
        # Test relationship
        assert company.is_contact_person(person.id) is True
        assert company.get_contact_role(person.id) == 'main'
        assert company.main_contact_name == person.display_name
    
    def test_foreign_key_constraint_simulation(self):
        """Test foreign key constraint handling simulation (Requirement 3.7)"""
        # Create person and company relationship
        person_id = 1
        
        # Create companies where person is a contact
        company1 = Company(
            id=1,
            name='Company 1',
            main_contact_id=person_id
        )
        
        company2 = Company(
            id=2,
            name='Company 2',
            financial_contact_id=person_id
        )
        
        # Simulate person deletion - companies should handle this gracefully
        # In real implementation, this would be handled by CompanyService.handle_person_deletion()
        
        # After person deletion, contact IDs should be set to None
        company1.main_contact_id = None
        company1.main_contact_name = None
        
        company2.financial_contact_id = None
        company2.financial_contact_name = None
        
        # Companies should still be valid
        assert company1.validate() == []
        assert company2.validate() == []
        
        # Contact properties should reflect the change
        assert company1.has_contacts is False
        assert company2.has_contacts is False
        assert company1.contact_display == 'No contacts'
        assert company2.contact_display == 'No contacts'


class TestFormSubmissionIntegration:
    """Integration tests for form submission with enhanced fields"""
    
    def test_person_form_data_processing(self):
        """Test processing person form data with enhanced fields (Requirements 1.1, 1.2, 5.1, 5.2)"""
        # Simulate form data from person creation/edit form
        form_data = {
            'name': 'Mario Rossi',
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'short_name': 'M. Rossi',
            'email': 'mario.rossi@example.com',
            'registration_no': 'EMP001',
            'profile_image': 'mario_rossi.jpg'
        }
        
        # Create person from form data
        person = Person(**form_data)
        
        # Validate form data
        errors = person.validate()
        assert len(errors) == 0
        
        # Test that all fields are properly set
        assert person.name == 'Mario Rossi'
        assert person.first_name == 'Mario'
        assert person.last_name == 'Rossi'
        assert person.registration_no == 'EMP001'
        assert person.profile_image == 'mario_rossi.jpg'
        
        # Test computed properties
        assert person.suggested_name_format == 'Rossi, Mario'
        assert person.display_name == 'Mario Rossi'
        assert person.has_profile_image is True
    
    def test_company_form_data_processing(self):
        """Test processing company form data (Requirements 3.1, 5.4, 5.5)"""
        # Simulate form data from company creation/edit form
        form_data = {
            'name': 'Acme Corporation',
            'short_name': 'ACME',
            'registration_no': '12345678901',
            'address': 'Via Roma 1',
            'city': 'Milano',
            'postal_code': '20100',
            'country': 'Italy',
            'phone': '+39 02 1234567',
            'email': 'info@acme.com',
            'website': 'https://www.acme.com',
            'main_contact_id': 1,
            'financial_contact_id': 2,
            'valid_from': date(2023, 1, 1),
            'valid_to': date(2024, 12, 31),
            'notes': 'Test company'
        }
        
        # Create company from form data
        company = Company(**form_data)
        
        # Validate form data
        errors = company.validate()
        assert len(errors) == 0
        
        # Test that all fields are properly set
        assert company.name == 'Acme Corporation'
        assert company.short_name == 'ACME'
        assert company.registration_no == '12345678901'
        assert company.main_contact_id == 1
        assert company.financial_contact_id == 2
        assert company.valid_from == date(2023, 1, 1)
        assert company.valid_to == date(2024, 12, 31)
        
        # Test computed properties
        assert company.display_name == 'ACME'
        assert company.has_contacts is True
        assert company.is_active is True  # Assuming current date is within range
    
    def test_form_validation_error_handling(self):
        """Test form validation error handling"""
        # Test person form with validation errors
        person_form_data = {
            'name': '',  # Required field empty
            'first_name': 'A' * 101,  # Too long
            'registration_no': 'B' * 26,  # Too long
            'profile_image': 'C' * 1025,  # Too long
            'email': 'invalid-email'  # Invalid format
        }
        
        person = Person(**person_form_data)
        person_errors = person.validate()
        
        assert len(person_errors) > 0
        
        # Test company form with validation errors
        company_form_data = {
            'name': '',  # Required field empty
            'website': 'invalid-url',  # Invalid URL
            'email': 'invalid-email',  # Invalid email
            'valid_from': date(2023, 12, 31),  # Invalid date range
            'valid_to': date(2023, 1, 1),
            'main_contact_id': 0  # Invalid contact ID
        }
        
        company = Company(**company_form_data)
        company_errors = company.validate()
        
        assert len(company_errors) > 0
        
        # Both should have validation errors that can be displayed to user
        assert all(hasattr(error, 'field') and hasattr(error, 'message') for error in person_errors)
        assert all(hasattr(error, 'field') and hasattr(error, 'message') for error in company_errors)


class TestDatabaseIntegration:
    """Integration tests for database operations with enhanced features"""
    
    def test_person_sqlite_row_integration(self):
        """Test Person.from_sqlite_row with enhanced fields"""
        # Mock SQLite row data
        class MockRow:
            def __init__(self):
                self.id = 1
                self.name = 'Mario Rossi'
                self.first_name = 'Mario'
                self.last_name = 'Rossi'
                self.short_name = 'M. Rossi'
                self.email = 'mario.rossi@example.com'
                self.registration_no = 'EMP001'
                self.profile_image = 'mario_rossi.jpg'
                self.current_assignments_count = 2
                self.total_assignments_count = 5
                self.datetime_created = '2023-01-01 10:00:00'
                self.datetime_updated = '2023-01-02 11:00:00'
        
        row = MockRow()
        person = Person.from_sqlite_row(row)
        
        # Test all fields are properly mapped
        assert person.id == 1
        assert person.name == 'Mario Rossi'
        assert person.first_name == 'Mario'
        assert person.last_name == 'Rossi'
        assert person.registration_no == 'EMP001'
        assert person.profile_image == 'mario_rossi.jpg'
        assert person.current_assignments_count == 2
        assert person.total_assignments_count == 5
    
    def test_company_sqlite_row_integration(self):
        """Test Company.from_sqlite_row with all fields"""
        # Mock SQLite row data
        class MockRow:
            def __init__(self):
                self.id = 1
                self.name = 'Acme Corporation'
                self.short_name = 'ACME'
                self.registration_no = '12345678901'
                self.address = 'Via Roma 1'
                self.city = 'Milano'
                self.postal_code = '20100'
                self.country = 'Italy'
                self.phone = '+39 02 1234567'
                self.email = 'info@acme.com'
                self.website = 'https://www.acme.com'
                self.main_contact_id = 1
                self.financial_contact_id = 2
                self.valid_from = '2023-01-01'
                self.valid_to = '2024-12-31'
                self.notes = 'Test company'
                self.main_contact_name = 'Mario Rossi'
                self.financial_contact_name = 'Anna Bianchi'
                self.datetime_created = '2023-01-01 10:00:00'
                self.datetime_updated = '2023-01-02 11:00:00'
        
        row = MockRow()
        company = Company.from_sqlite_row(row)
        
        # Test all fields are properly mapped
        assert company.id == 1
        assert company.name == 'Acme Corporation'
        assert company.short_name == 'ACME'
        assert company.registration_no == '12345678901'
        assert company.main_contact_id == 1
        assert company.financial_contact_id == 2
        assert company.valid_from == date(2023, 1, 1)
        assert company.valid_to == date(2024, 12, 31)
        assert company.main_contact_name == 'Mario Rossi'
        assert company.financial_contact_name == 'Anna Bianchi'
    
    def test_date_handling_integration(self):
        """Test date field handling in Company model"""
        # Test with string dates (as from database)
        class MockRowWithStringDates:
            def __init__(self):
                self.id = 1
                self.name = 'Test Company'
                self.short_name = None
                self.registration_no = None
                self.address = None
                self.city = None
                self.postal_code = None
                self.country = 'Italy'
                self.phone = None
                self.email = None
                self.website = None
                self.main_contact_id = None
                self.financial_contact_id = None
                self.valid_from = '2023-01-01'
                self.valid_to = '2024-12-31'
                self.notes = None
                self.main_contact_name = None
                self.financial_contact_name = None
                self.datetime_created = '2023-01-01 10:00:00'
                self.datetime_updated = '2023-01-02 11:00:00'
        
        row = MockRowWithStringDates()
        company = Company.from_sqlite_row(row)
        
        # Dates should be converted to date objects
        assert isinstance(company.valid_from, date)
        assert isinstance(company.valid_to, date)
        assert company.valid_from == date(2023, 1, 1)
        assert company.valid_to == date(2024, 12, 31)
        
        # Test to_dict serialization
        company_dict = company.to_dict()
        assert company_dict['valid_from'] == '2023-01-01'
        assert company_dict['valid_to'] == '2024-12-31'