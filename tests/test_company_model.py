"""
Unit tests for Company model.

This module tests the Company model including:
- All required fields validation
- Date range validation
- URL validation
- Contact person relationships
- Business logic and computed properties

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8
"""

import pytest
from datetime import date, datetime
from app.models.company import Company
from app.models.base import ValidationError


class TestCompanyModel:
    """Test Company model functionality"""
    
    def test_company_creation_with_all_fields(self):
        """Test Company creation with all fields (Requirement 3.1)"""
        company = Company(
            name="Acme Corporation",
            short_name="ACME",
            registration_no="12345678901",
            address="Via Roma 1",
            city="Milano",
            postal_code="20100",
            country="Italy",
            phone="+39 02 1234567",
            email="info@acme.com",
            website="https://www.acme.com",
            main_contact_id=1,
            financial_contact_id=2,
            valid_from=date(2023, 1, 1),
            valid_to=date(2024, 12, 31),
            notes="Test company"
        )
        
        assert company.name == "Acme Corporation"
        assert company.short_name == "ACME"
        assert company.registration_no == "12345678901"
        assert company.address == "Via Roma 1"
        assert company.city == "Milano"
        assert company.postal_code == "20100"
        assert company.country == "Italy"
        assert company.phone == "+39 02 1234567"
        assert company.email == "info@acme.com"
        assert company.website == "https://www.acme.com"
        assert company.main_contact_id == 1
        assert company.financial_contact_id == 2
        assert company.valid_from == date(2023, 1, 1)
        assert company.valid_to == date(2024, 12, 31)
        assert company.notes == "Test company"
    
    def test_company_required_fields_validation(self):
        """Test required fields validation (Requirement 3.2)"""
        # Test with missing name
        company = Company(
            name="",
            short_name="ACME",
            registration_no="12345"
        )
        errors = company.validate()
        assert any(error.field == "name" and "required" in error.message.lower() for error in errors)
        
        # Test with valid required fields
        company = Company(
            name="Acme Corporation",
            short_name="ACME",
            registration_no="12345"
        )
        errors = company.validate()
        assert not any(error.field == "name" for error in errors)
    
    def test_website_url_validation(self):
        """Test website URL validation (Requirement 3.3)"""
        # Valid URLs
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://subdomain.example.com/path",
            "http://localhost:8080"
        ]
        
        for url in valid_urls:
            company = Company(
                name="Test Company",
                website=url
            )
            errors = company.validate()
            assert not any(error.field == "website" for error in errors), f"URL {url} should be valid"
        
        # Invalid URLs
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "www.example.com",
            "example.com"
        ]
        
        for url in invalid_urls:
            company = Company(
                name="Test Company",
                website=url
            )
            errors = company.validate()
            assert any(error.field == "website" for error in errors), f"URL {url} should be invalid"
    
    def test_date_range_validation(self):
        """Test date range validation (Requirement 3.4)"""
        # Valid date range
        company = Company(
            name="Test Company",
            valid_from=date(2023, 1, 1),
            valid_to=date(2023, 12, 31)
        )
        errors = company.validate()
        assert not any(error.field in ["valid_from", "valid_to"] for error in errors)
        
        # Invalid date range (end before start)
        company = Company(
            name="Test Company",
            valid_from=date(2023, 12, 31),
            valid_to=date(2023, 1, 1)
        )
        errors = company.validate()
        assert any(error.field == "valid_to" and "after start date" in error.message for error in errors)
        
        # Same dates should be valid
        company = Company(
            name="Test Company",
            valid_from=date(2023, 6, 15),
            valid_to=date(2023, 6, 15)
        )
        errors = company.validate()
        assert not any(error.field in ["valid_from", "valid_to"] for error in errors)
    
    def test_contact_validation(self):
        """Test contact person validation (Requirements 3.5, 3.6)"""
        # Valid contact IDs
        company = Company(
            name="Test Company",
            main_contact_id=1,
            financial_contact_id=2
        )
        errors = company.validate()
        assert not any(error.field in ["main_contact_id", "financial_contact_id"] for error in errors)
        
        # Invalid contact IDs (negative or zero)
        company = Company(
            name="Test Company",
            main_contact_id=0,
            financial_contact_id=-1
        )
        errors = company.validate()
        assert any(error.field == "main_contact_id" for error in errors)
        assert any(error.field == "financial_contact_id" for error in errors)
        
        # Same person as both contacts (should be invalid)
        company = Company(
            name="Test Company",
            main_contact_id=1,
            financial_contact_id=1
        )
        errors = company.validate()
        assert any(error.field == "financial_contact_id" and "same as main contact" in error.message for error in errors)
    
    def test_display_name_property(self):
        """Test display_name property"""
        # With short_name
        company = Company(
            name="Acme Corporation",
            short_name="ACME"
        )
        assert company.display_name == "ACME"
        
        # Without short_name
        company = Company(
            name="Acme Corporation"
        )
        assert company.display_name == "Acme Corporation"
        
        # With empty short_name
        company = Company(
            name="Acme Corporation",
            short_name=""
        )
        assert company.display_name == "Acme Corporation"
    
    def test_is_active_property(self):
        """Test is_active property based on validity dates"""
        today = date.today()
        
        # No dates set (should be active)
        company = Company(name="Test Company")
        assert company.is_active is True
        
        # Valid date range (currently active)
        company = Company(
            name="Test Company",
            valid_from=date(today.year - 1, 1, 1),
            valid_to=date(today.year + 1, 12, 31)
        )
        assert company.is_active is True
        
        # Future start date (not yet active)
        company = Company(
            name="Test Company",
            valid_from=date(today.year + 1, 1, 1)
        )
        assert company.is_active is False
        
        # Past end date (no longer active)
        company = Company(
            name="Test Company",
            valid_to=date(today.year - 1, 12, 31)
        )
        assert company.is_active is False
    
    def test_has_contacts_property(self):
        """Test has_contacts property"""
        # No contacts
        company = Company(name="Test Company")
        assert company.has_contacts is False
        
        # Only main contact
        company = Company(
            name="Test Company",
            main_contact_id=1
        )
        assert company.has_contacts is True
        
        # Only financial contact
        company = Company(
            name="Test Company",
            financial_contact_id=2
        )
        assert company.has_contacts is True
        
        # Both contacts
        company = Company(
            name="Test Company",
            main_contact_id=1,
            financial_contact_id=2
        )
        assert company.has_contacts is True