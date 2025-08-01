"""
Unit tests for CompanyService.

This module tests the CompanyService class including:
- CRUD operations for companies
- Contact person relationships
- Active company filtering
- Foreign key constraint handling
- Search and validation functionality

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from typing import List, Dict, Any

from app.services.company import CompanyService
from app.services.base import ServiceException, ServiceValidationException, ServiceNotFoundException, ServiceIntegrityException
from app.models.company import Company
from app.models.base import ValidationError


class TestCompanyService:
    """Test CompanyService functionality"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager for testing"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = []
        mock_db.fetch_one.return_value = None
        mock_db.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
        return mock_db
    
    @pytest.fixture
    def company_service(self, mock_db_manager):
        """CompanyService instance with mocked database"""
        with patch('app.database.get_db_manager', return_value=mock_db_manager):
            return CompanyService()
    
    def test_service_initialization(self, company_service):
        """Test CompanyService initialization"""
        assert company_service.model_class == Company
        assert company_service.table_name == "companies"
    
    def test_get_list_query_includes_contact_information(self, company_service):
        """Test that list query includes contact information (Requirements 3.5, 3.6)"""
        query = company_service.get_list_query()
        
        # Should join with persons table for contacts
        assert "LEFT JOIN persons p1 ON c.main_contact_id = p1.id" in query
        assert "LEFT JOIN persons p2 ON c.financial_contact_id = p2.id" in query
        
        # Should select contact names
        assert "p1.name as main_contact_name" in query
        assert "p2.name as financial_contact_name" in query
        
        # Should order by company name
        assert "ORDER BY c.name" in query
    
    def test_get_by_id_query_includes_contact_information(self, company_service):
        """Test that by_id query includes contact information"""
        query = company_service.get_by_id_query()
        
        # Should join with persons table for contacts
        assert "LEFT JOIN persons p1 ON c.main_contact_id = p1.id" in query
        assert "LEFT JOIN persons p2 ON c.financial_contact_id = p2.id" in query
        
        # Should include WHERE clause
        assert "WHERE c.id = ?" in query
    
    def test_get_insert_query_includes_all_fields(self, company_service):
        """Test that insert query includes all company fields (Requirement 3.1)"""
        query = company_service.get_insert_query()
        
        expected_fields = [
            "name", "short_name", "registration_no", "address", "city", 
            "postal_code", "country", "phone", "email", "website",
            "main_contact_id", "financial_contact_id", "valid_from", "valid_to", "notes"
        ]
        
        for field in expected_fields:
            assert field in query
        
        # Should have correct number of placeholders
        assert query.count("?") == len(expected_fields)
    
    def test_get_update_query_includes_all_fields(self, company_service):
        """Test that update query includes all company fields"""
        query = company_service.get_update_query()
        
        expected_fields = [
            "name", "short_name", "registration_no", "address", "city",
            "postal_code", "country", "phone", "email", "website", 
            "main_contact_id", "financial_contact_id", "valid_from", "valid_to", "notes"
        ]
        
        for field in expected_fields:
            assert f"{field} = ?" in query
        
        assert "WHERE id = ?" in query
    
    def test_model_to_insert_params(self, company_service):
        """Test model_to_insert_params conversion (Requirement 3.1)"""
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
        
        params = company_service.model_to_insert_params(company)
        
        expected_params = (
            "Acme Corporation",
            "ACME",
            "12345678901",
            "Via Roma 1",
            "Milano",
            "20100",
            "Italy",
            "+39 02 1234567",
            "info@acme.com",
            "https://www.acme.com",
            1,
            2,
            "2023-01-01",  # Date converted to ISO format
            "2024-12-31",  # Date converted to ISO format
            "Test company"
        )
        
        assert params == expected_params
    
    def test_model_to_update_params(self, company_service):
        """Test model_to_update_params conversion"""
        company = Company(
            id=1,
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
        
        params = company_service.model_to_update_params(company)
        
        expected_params = (
            "Acme Corporation",
            "ACME", 
            "12345678901",
            "Via Roma 1",
            "Milano",
            "20100",
            "Italy",
            "+39 02 1234567",
            "info@acme.com",
            "https://www.acme.com",
            1,
            2,
            "2023-01-01",
            "2024-12-31",
            "Test company",
            1  # ID at the end for WHERE clause
        )
        
        assert params == expected_params
    
    def test_create_company(self, company_service, mock_db_manager):
        """Test creating a company (Requirements 3.1, 3.2)"""
        # Setup mock
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        # Create company
        company = Company(
            name="Acme Corporation",
            short_name="ACME",
            registration_no="12345678901",
            email="info@acme.com",
            website="https://www.acme.com"
        )
        
        # Mock get_by_id to return created company
        company_service.get_by_id = Mock(return_value=company)
        
        result = company_service.create(company)
        
        assert result == company
        mock_db_manager.execute_query.assert_called_once()
        
        # Verify the query includes all fields
        call_args = mock_db_manager.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO companies" in query
        assert "Acme Corporation" in params
        assert "ACME" in params
        assert "12345678901" in params
    
    def test_get_active_companies(self, company_service, mock_db_manager):
        """Test get_active_companies method (Requirement 3.4)"""
        # Mock database response
        mock_rows = [
            {
                'id': 1,
                'name': 'Active Company',
                'short_name': 'ACTIVE',
                'registration_no': '123',
                'address': None,
                'city': None,
                'postal_code': None,
                'country': 'Italy',
                'phone': None,
                'email': None,
                'website': None,
                'main_contact_id': 1,
                'financial_contact_id': None,
                'valid_from': '2023-01-01',
                'valid_to': '2024-12-31',
                'notes': None,
                'main_contact_name': 'Mario Rossi',
                'financial_contact_name': None,
                'datetime_created': '2023-01-01 10:00:00',
                'datetime_updated': '2023-01-02 11:00:00'
            }
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        # Mock Company.from_sqlite_row
        with patch.object(Company, 'from_sqlite_row') as mock_from_row:
            mock_company = Company(id=1, name='Active Company')
            mock_from_row.return_value = mock_company
            
            result = company_service.get_active_companies()
            
            assert len(result) == 1
            assert result[0] == mock_company
            
            # Verify query filters by date
            call_args = mock_db_manager.fetch_all.call_args
            query = call_args[0][0]
            params = call_args[0][1]
            
            assert "valid_from IS NULL OR valid_from <= ?" in query
            assert "valid_to IS NULL OR valid_to >= ?" in query
            assert len(params) == 2  # Two date parameters
    
    def test_get_active_companies_with_custom_date(self, company_service, mock_db_manager):
        """Test get_active_companies with custom as_of_date"""
        mock_db_manager.fetch_all.return_value = []
        
        custom_date = date(2023, 6, 15)
        company_service.get_active_companies(as_of_date=custom_date)
        
        # Verify custom date is used in query
        call_args = mock_db_manager.fetch_all.call_args
        params = call_args[0][1]
        
        assert "2023-06-15" in params
    
    def test_get_companies_by_contact(self, company_service, mock_db_manager):
        """Test get_companies_by_contact method (Requirement 3.5)"""
        # Mock database response
        mock_rows = [
            {
                'id': 1,
                'name': 'Company 1',
                'short_name': 'COMP1',
                'registration_no': '123',
                'address': None,
                'city': None,
                'postal_code': None,
                'country': 'Italy',
                'phone': None,
                'email': None,
                'website': None,
                'main_contact_id': 1,
                'financial_contact_id': None,
                'valid_from': None,
                'valid_to': None,
                'notes': None,
                'main_contact_name': 'Mario Rossi',
                'financial_contact_name': None,
                'datetime_created': '2023-01-01 10:00:00',
                'datetime_updated': '2023-01-02 11:00:00'
            }
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch.object(Company, 'from_sqlite_row') as mock_from_row:
            mock_company = Company(id=1, name='Company 1')
            mock_from_row.return_value = mock_company
            
            result = company_service.get_companies_by_contact(1)
            
            assert len(result) == 1
            assert result[0] == mock_company
            
            # Verify query searches both contact fields
            call_args = mock_db_manager.fetch_all.call_args
            query = call_args[0][0]
            params = call_args[0][1]
            
            assert "main_contact_id = ? OR" in query
            assert "financial_contact_id = ?" in query
            assert params == (1, 1)  # Person ID used twice
    
    def test_can_delete_company(self, company_service, mock_db_manager):
        """Test can_delete method (Requirement 3.7)"""
        # Mock existing company
        company_service.get_by_id = Mock(return_value=Company(id=1, name="Test Company"))
        
        can_delete, message = company_service.can_delete(1)
        
        assert can_delete is True
        assert message == ""
    
    def test_can_delete_company_not_found(self, company_service, mock_db_manager):
        """Test can_delete when company not found"""
        # Mock company not found
        company_service.get_by_id = Mock(return_value=None)
        
        can_delete, message = company_service.can_delete(999)
        
        assert can_delete is False
        assert "not found" in message
    
    def test_get_contact_persons(self, company_service, mock_db_manager):
        """Test get_contact_persons method (Requirement 3.6)"""
        # Mock database response
        mock_rows = [
            {
                'id': 1,
                'display_name': 'Rossi, Mario',
                'email': 'mario.rossi@example.com'
            },
            {
                'id': 2,
                'display_name': 'Bianchi, Anna',
                'email': 'anna.bianchi@example.com'
            }
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        result = company_service.get_contact_persons()
        
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[0]['display_name'] == 'Rossi, Mario'
        assert result[1]['id'] == 2
        assert result[1]['display_name'] == 'Bianchi, Anna'
        
        # Verify query uses proper name formatting
        call_args = mock_db_manager.fetch_all.call_args
        query = call_args[0][0]
        
        assert "COALESCE" in query
        assert "last_name || ', ' || first_name" in query
        assert "ORDER BY display_name" in query
    
    def test_get_company_statistics(self, company_service, mock_db_manager):
        """Test get_company_statistics method"""
        # Mock various database responses
        mock_responses = [
            {'count': 50},     # companies_with_main_contact
            {'count': 40},     # companies_with_financial_contact
            {'count': 10},     # companies_without_contacts
            [{'country': 'Italy', 'count': 30}, {'country': 'USA', 'count': 20}]  # companies_by_country
        ]
        
        # Mock the count method and get_active_companies
        company_service.count = Mock(return_value=100)
        company_service.get_active_companies = Mock(return_value=[Company() for _ in range(80)])
        
        mock_db_manager.fetch_one.side_effect = mock_responses[:3]
        mock_db_manager.fetch_all.return_value = mock_responses[3]
        
        stats = company_service.get_company_statistics()
        
        assert stats['total_companies'] == 100
        assert stats['active_companies'] == 80
        assert stats['inactive_companies'] == 20
        assert stats['companies_with_main_contact'] == 50
        assert stats['companies_with_financial_contact'] == 40
        assert stats['companies_without_contacts'] == 10
        assert len(stats['companies_by_country']) == 2
        assert stats['companies_by_country'][0]['country'] == 'Italy'
        assert stats['companies_by_country'][0]['count'] == 30
    
    def test_search_companies(self, company_service, mock_db_manager):
        """Test search_companies method"""
        # Mock database response
        mock_rows = [
            {
                'id': 1,
                'name': 'Acme Corporation',
                'short_name': 'ACME',
                'registration_no': '123',
                'address': None,
                'city': None,
                'postal_code': None,
                'country': 'Italy',
                'phone': None,
                'email': 'info@acme.com',
                'website': None,
                'main_contact_id': None,
                'financial_contact_id': None,
                'valid_from': None,
                'valid_to': None,
                'notes': None,
                'main_contact_name': None,
                'financial_contact_name': None,
                'datetime_created': '2023-01-01 10:00:00',
                'datetime_updated': '2023-01-02 11:00:00'
            }
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch.object(Company, 'from_sqlite_row') as mock_from_row:
            mock_company = Company(id=1, name='Acme Corporation')
            mock_from_row.return_value = mock_company
            
            result = company_service.search_companies("Acme")
            
            assert len(result) == 1
            assert result[0] == mock_company
            
            # Verify search query includes multiple fields
            call_args = mock_db_manager.fetch_all.call_args
            query = call_args[0][0]
            params = call_args[0][1]
            
            assert "c.name LIKE ?" in query
            assert "c.short_name LIKE ?" in query
            assert "c.registration_no LIKE ?" in query
            assert "c.email LIKE ?" in query
            assert "p1.name LIKE ?" in query  # main contact
            assert "p2.name LIKE ?" in query  # financial contact
            assert params == ("%Acme%",) * 6  # Search term repeated for each field
    
    def test_search_companies_empty_term(self, company_service, mock_db_manager):
        """Test search_companies with empty search term"""
        result = company_service.search_companies("")
        
        assert result == []
        mock_db_manager.fetch_all.assert_not_called()
    
    def test_get_searchable_fields(self, company_service):
        """Test get_searchable_fields method"""
        fields = company_service.get_searchable_fields()
        
        expected_fields = ["name", "short_name", "registration_no", "email", "city", "country"]
        
        for field in expected_fields:
            assert field in fields
    
    def test_validate_for_create_duplicate_registration_no(self, company_service, mock_db_manager):
        """Test _validate_for_create with duplicate registration number"""
        # Mock existing company with same registration number
        mock_db_manager.fetch_one.return_value = {'id': 2}
        
        company = Company(
            name="Test Company",
            registration_no="12345678901"
        )
        
        with pytest.raises(ServiceValidationException) as exc_info:
            company_service._validate_for_create(company)
        
        assert "already exists" in str(exc_info.value)
    
    def test_validate_for_create_invalid_main_contact(self, company_service, mock_db_manager):
        """Test _validate_for_create with invalid main contact (Requirement 3.6)"""
        # Mock no duplicate registration number, but invalid contact
        mock_db_manager.fetch_one.side_effect = [
            None,  # No duplicate registration
            None   # Contact person doesn't exist
        ]
        
        company = Company(
            name="Test Company",
            registration_no="12345678901",
            main_contact_id=999
        )
        
        with pytest.raises(ServiceValidationException) as exc_info:
            company_service._validate_for_create(company)
        
        assert "does not exist" in str(exc_info.value)
    
    def test_validate_for_create_invalid_financial_contact(self, company_service, mock_db_manager):
        """Test _validate_for_create with invalid financial contact (Requirement 3.6)"""
        # Mock no duplicate registration number, valid main contact, invalid financial contact
        mock_db_manager.fetch_one.side_effect = [
            None,      # No duplicate registration
            {'id': 1}, # Main contact exists
            None       # Financial contact doesn't exist
        ]
        
        company = Company(
            name="Test Company",
            registration_no="12345678901",
            main_contact_id=1,
            financial_contact_id=999
        )
        
        with pytest.raises(ServiceValidationException) as exc_info:
            company_service._validate_for_create(company)
        
        assert "Financial contact person with ID 999 does not exist" in str(exc_info.value)
    
    def test_validate_for_update_duplicate_registration_no(self, company_service, mock_db_manager):
        """Test _validate_for_update with duplicate registration number"""
        # Mock existing company with same registration number (different ID)
        mock_db_manager.fetch_one.return_value = {'id': 2}
        
        company = Company(
            id=1,
            name="Test Company",
            registration_no="12345678901"
        )
        existing = Company(id=1, name="Test Company")
        
        with pytest.raises(ServiceValidationException) as exc_info:
            company_service._validate_for_update(company, existing)
        
        assert "already exists" in str(exc_info.value)
    
    def test_handle_person_deletion(self, company_service, mock_db_manager):
        """Test handle_person_deletion method (Requirement 3.7)"""
        company_service.handle_person_deletion(1)
        
        # Verify both update queries were executed
        assert mock_db_manager.execute_query.call_count == 2
        
        # Check the queries
        calls = mock_db_manager.execute_query.call_args_list
        
        # First call should update main_contact_id
        query1 = calls[0][0][0]
        params1 = calls[0][0][1]
        assert "main_contact_id = NULL" in query1
        assert "main_contact_id = ?" in query1
        assert params1 == (1,)
        
        # Second call should update financial_contact_id
        query2 = calls[1][0][0]
        params2 = calls[1][0][1]
        assert "financial_contact_id = NULL" in query2
        assert "financial_contact_id = ?" in query2
        assert params2 == (1,)
    
    def test_handle_person_deletion_error(self, company_service, mock_db_manager):
        """Test handle_person_deletion with database error"""
        mock_db_manager.execute_query.side_effect = Exception("Database error")
        
        with pytest.raises(ServiceIntegrityException) as exc_info:
            company_service.handle_person_deletion(1)
        
        assert "Failed to handle person deletion" in str(exc_info.value)
    
    def test_get_companies_expiring_soon(self, company_service, mock_db_manager):
        """Test get_companies_expiring_soon method"""
        # Mock database response
        mock_rows = [
            {
                'id': 1,
                'name': 'Expiring Company',
                'short_name': 'EXP',
                'registration_no': '123',
                'address': None,
                'city': None,
                'postal_code': None,
                'country': 'Italy',
                'phone': None,
                'email': None,
                'website': None,
                'main_contact_id': None,
                'financial_contact_id': None,
                'valid_from': None,
                'valid_to': '2024-01-15',
                'notes': None,
                'main_contact_name': None,
                'financial_contact_name': None,
                'datetime_created': '2023-01-01 10:00:00',
                'datetime_updated': '2023-01-02 11:00:00'
            }
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch.object(Company, 'from_sqlite_row') as mock_from_row:
            mock_company = Company(id=1, name='Expiring Company')
            mock_from_row.return_value = mock_company
            
            result = company_service.get_companies_expiring_soon(30)
            
            assert len(result) == 1
            assert result[0] == mock_company
            
            # Verify query filters by expiration date
            call_args = mock_db_manager.fetch_all.call_args
            query = call_args[0][0]
            
            assert "valid_to IS NOT NULL" in query
            assert "valid_to <= ?" in query
            assert "valid_to >= ?" in query
            assert "ORDER BY c.valid_to, c.name" in query
    
    def test_get_companies_by_status_active(self, company_service, mock_db_manager):
        """Test get_companies_by_status with 'active' status"""
        mock_db_manager.fetch_all.return_value = []
        
        company_service.get_companies_by_status("active")
        
        # Verify query filters for active companies
        call_args = mock_db_manager.fetch_all.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "valid_from IS NULL OR valid_from <= ?" in query
        assert "valid_to IS NULL OR valid_to >= ?" in query
        assert len(params) == 2  # Two date parameters
    
    def test_get_companies_by_status_expired(self, company_service, mock_db_manager):
        """Test get_companies_by_status with 'expired' status"""
        mock_db_manager.fetch_all.return_value = []
        
        company_service.get_companies_by_status("expired")
        
        # Verify query filters for expired companies
        call_args = mock_db_manager.fetch_all.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "valid_to IS NOT NULL AND valid_to < ?" in query
        assert len(params) == 1  # One date parameter
    
    def test_get_companies_by_status_future(self, company_service, mock_db_manager):
        """Test get_companies_by_status with 'future' status"""
        mock_db_manager.fetch_all.return_value = []
        
        company_service.get_companies_by_status("future")
        
        # Verify query filters for future companies
        call_args = mock_db_manager.fetch_all.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "valid_from IS NOT NULL AND valid_from > ?" in query
        assert len(params) == 1  # One date parameter
    
    def test_get_companies_by_status_invalid(self, company_service, mock_db_manager):
        """Test get_companies_by_status with invalid status returns all"""
        company_service.get_all = Mock(return_value=[Company()])
        
        result = company_service.get_companies_by_status("invalid")
        
        company_service.get_all.assert_called_once()
        assert len(result) == 1
    
    def test_error_handling_in_statistics(self, company_service, mock_db_manager):
        """Test error handling in get_company_statistics"""
        # Mock database error
        mock_db_manager.fetch_one.side_effect = Exception("Database error")
        
        stats = company_service.get_company_statistics()
        
        # Should return empty dict on error
        assert stats == {}
    
    def test_error_handling_in_search(self, company_service, mock_db_manager):
        """Test error handling in search_companies"""
        # Mock database error
        mock_db_manager.fetch_all.side_effect = Exception("Database error")
        
        result = company_service.search_companies("test")
        
        # Should return empty list on error
        assert result == []