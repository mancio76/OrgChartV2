"""
Unit tests for PersonService with enhanced fields support.

This module tests the PersonService class including:
- CRUD operations with enhanced fields
- Name suggestion functionality
- Profile image handling
- Search and filtering capabilities
- Validation and error handling

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 6.1, 6.2, 6.4
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from typing import List, Dict, Any

from app.services.person import PersonService
from app.services.base import ServiceException, ServiceValidationException, ServiceNotFoundException
from app.models.person import Person
from app.models.base import ValidationError


class TestPersonService:
    """Test PersonService functionality with enhanced fields"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager for testing"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = []
        mock_db.fetch_one.return_value = None
        mock_db.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
        return mock_db
    
    @pytest.fixture
    def person_service(self, mock_db_manager):
        """PersonService instance with mocked database"""
        with patch('app.database.get_db_manager', return_value=mock_db_manager):
            return PersonService()
    
    def test_service_initialization(self, person_service):
        """Test PersonService initialization"""
        assert person_service.model_class == Person
        assert person_service.table_name == "persons"
    
    def test_get_list_query_includes_enhanced_fields(self, person_service):
        """Test that list query includes enhanced fields (Requirements 1.3, 1.4, 1.5, 6.1)"""
        query = person_service.get_list_query()
        
        # Should include enhanced fields in SELECT
        assert "first_name" in query
        assert "last_name" in query
        assert "registration_no" in query
        assert "profile_image" in query
        
        # Should include assignment counts
        assert "current_assignments_count" in query
        assert "total_assignments_count" in query
        
        # Should order by last_name first, then first_name
        assert "ORDER BY COALESCE(p.last_name, p.name), COALESCE(p.first_name, '')" in query
    
    def test_get_by_id_query_includes_enhanced_fields(self, person_service):
        """Test that by_id query includes enhanced fields"""
        query = person_service.get_by_id_query()
        
        # Should include enhanced fields
        assert "first_name" in query
        assert "last_name" in query
        assert "registration_no" in query
        assert "profile_image" in query
        
        # Should include WHERE clause
        assert "WHERE p.id = ?" in query
    
    def test_get_insert_query_includes_enhanced_fields(self, person_service):
        """Test that insert query includes enhanced fields (Requirements 1.3, 1.4, 1.5, 6.1)"""
        query = person_service.get_insert_query()
        
        expected_fields = [
            "name", "short_name", "email", 
            "first_name", "last_name", "registration_no", "profile_image"
        ]
        
        for field in expected_fields:
            assert field in query
        
        # Should have correct number of placeholders
        assert query.count("?") == len(expected_fields)
    
    def test_get_update_query_includes_enhanced_fields(self, person_service):
        """Test that update query includes enhanced fields"""
        query = person_service.get_update_query()
        
        expected_fields = [
            "name", "short_name", "email",
            "first_name", "last_name", "registration_no", "profile_image"
        ]
        
        for field in expected_fields:
            assert f"{field} = ?" in query
        
        assert "WHERE id = ?" in query
    
    def test_model_to_insert_params_with_enhanced_fields(self, person_service):
        """Test model_to_insert_params with enhanced fields (Requirements 1.3, 1.4, 1.5, 6.1)"""
        person = Person(
            name="Mario Rossi",
            short_name="M. Rossi",
            email="mario.rossi@example.com",
            first_name="Mario",
            last_name="Rossi",
            registration_no="EMP001",
            profile_image="mario_rossi.jpg"
        )
        
        params = person_service.model_to_insert_params(person)
        
        expected_params = (
            "Mario Rossi",
            "M. Rossi", 
            "mario.rossi@example.com",
            "Mario",
            "Rossi",
            "EMP001",
            "mario_rossi.jpg"
        )
        
        assert params == expected_params
    
    def test_model_to_update_params_with_enhanced_fields(self, person_service):
        """Test model_to_update_params with enhanced fields"""
        person = Person(
            id=1,
            name="Mario Rossi",
            short_name="M. Rossi",
            email="mario.rossi@example.com",
            first_name="Mario",
            last_name="Rossi",
            registration_no="EMP001",
            profile_image="mario_rossi.jpg"
        )
        
        params = person_service.model_to_update_params(person)
        
        expected_params = (
            "Mario Rossi",
            "M. Rossi",
            "mario.rossi@example.com", 
            "Mario",
            "Rossi",
            "EMP001",
            "mario_rossi.jpg",
            1  # ID at the end for WHERE clause
        )
        
        assert params == expected_params
    
    def test_create_person_with_enhanced_fields(self, person_service, mock_db_manager):
        """Test creating person with enhanced fields (Requirements 1.1, 1.2)"""
        # Setup mock
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        # Create person with enhanced fields
        person = Person(
            name="Mario Rossi",
            first_name="Mario",
            last_name="Rossi",
            registration_no="EMP001",
            profile_image="mario_rossi.jpg",
            email="mario.rossi@example.com"
        )
        
        # Mock get_by_id to return created person
        person_service.get_by_id = Mock(return_value=person)
        
        result = person_service.create(person)
        
        assert result == person
        mock_db_manager.execute_query.assert_called_once()
        
        # Verify the query includes enhanced fields
        call_args = mock_db_manager.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "first_name" in query
        assert "last_name" in query
        assert "registration_no" in query
        assert "profile_image" in query
        
        assert "Mario" in params
        assert "Rossi" in params
        assert "EMP001" in params
        assert "mario_rossi.jpg" in params
    
    def test_update_person_with_enhanced_fields(self, person_service, mock_db_manager):
        """Test updating person with enhanced fields"""
        # Setup existing person
        existing_person = Person(id=1, name="Mario Rossi")
        
        # Setup updated person
        updated_person = Person(
            id=1,
            name="Mario Rossi",
            first_name="Mario",
            last_name="Rossi",
            registration_no="EMP001",
            profile_image="mario_rossi.jpg"
        )
        
        # Mock database calls
        person_service.get_by_id = Mock()
        person_service.get_by_id.side_effect = [existing_person, updated_person]
        
        result = person_service.update(updated_person)
        
        assert result == updated_person
        mock_db_manager.execute_query.assert_called_once()
        
        # Verify the query includes enhanced fields
        call_args = mock_db_manager.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "first_name = ?" in query
        assert "last_name = ?" in query
        assert "registration_no = ?" in query
        assert "profile_image = ?" in query
        
        assert "Mario" in params
        assert "Rossi" in params
        assert "EMP001" in params
        assert "mario_rossi.jpg" in params
    
    def test_get_all_persons_with_enhanced_fields(self, person_service, mock_db_manager):
        """Test getting all persons includes enhanced fields"""
        # Mock database response
        mock_rows = [
            {
                'id': 1,
                'name': 'Mario Rossi',
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'registration_no': 'EMP001',
                'profile_image': 'mario_rossi.jpg',
                'email': 'mario.rossi@example.com',
                'short_name': 'M. Rossi',
                'current_assignments_count': 2,
                'total_assignments_count': 5,
                'datetime_created': '2023-01-01 10:00:00',
                'datetime_updated': '2023-01-02 11:00:00'
            }
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        # Mock Person.from_sqlite_row
        with patch.object(Person, 'from_sqlite_row') as mock_from_row:
            mock_person = Person(
                id=1,
                name='Mario Rossi',
                first_name='Mario',
                last_name='Rossi',
                registration_no='EMP001',
                profile_image='mario_rossi.jpg'
            )
            mock_from_row.return_value = mock_person
            
            result = person_service.get_all()
            
            assert len(result) == 1
            assert result[0] == mock_person
            
            # Verify from_sqlite_row was called with enhanced fields
            mock_from_row.assert_called_once_with(mock_rows[0])
    
    def test_can_delete_person_with_current_assignments(self, person_service, mock_db_manager):
        """Test can_delete returns False for person with current assignments"""
        # Mock current assignments exist
        mock_db_manager.fetch_one.return_value = {'count': 2}
        
        can_delete, message = person_service.can_delete(1)
        
        assert can_delete is False
        assert "2 incarichi correnti" in message
    
    def test_can_delete_person_with_historical_assignments_only(self, person_service, mock_db_manager):
        """Test can_delete returns True for person with only historical assignments"""
        # Mock no current assignments, but historical ones exist
        mock_db_manager.fetch_one.side_effect = [
            {'count': 0},  # No current assignments
            {'count': 3}   # Historical assignments exist
        ]
        
        can_delete, message = person_service.can_delete(1)
        
        assert can_delete is True
        assert "3 incarichi storici" in message
    
    def test_can_delete_person_no_assignments(self, person_service, mock_db_manager):
        """Test can_delete returns True for person with no assignments"""
        # Mock no assignments at all
        mock_db_manager.fetch_one.side_effect = [
            {'count': 0},  # No current assignments
            {'count': 0}   # No historical assignments
        ]
        
        can_delete, message = person_service.can_delete(1)
        
        assert can_delete is True
        assert message == ""
    
    def test_get_person_statistics(self, person_service, mock_db_manager):
        """Test get_person_statistics method"""
        # Mock database responses for various statistics queries
        mock_responses = [
            {'count': 2},      # current_assignments
            {'count': 5},      # total_assignments  
            {'count': 3},      # units_worked
            {'count': 4},      # job_titles_held
            {'total_percentage': 1.2},  # current_workload
            {'count': 1},      # interim_assignments
            {'avg_duration': 365.5},    # avg_assignment_duration
            {'first_assignment': '2022-01-01T10:00:00'}  # first_assignment_date
        ]
        
        mock_db_manager.fetch_one.side_effect = mock_responses
        
        stats = person_service.get_person_statistics(1)
        
        assert stats['current_assignments'] == 2
        assert stats['total_assignments'] == 5
        assert stats['units_worked'] == 3
        assert stats['job_titles_held'] == 4
        assert stats['current_workload'] == 1.2
        assert stats['interim_assignments'] == 1
        assert stats['avg_assignment_duration'] == 366  # rounded
        assert stats['first_assignment_date'] == date(2022, 1, 1)
        assert stats['tenure_days'] > 0
    
    def test_search_persons_with_enhanced_fields(self, person_service, mock_db_manager):
        """Test search includes enhanced fields (Requirements 1.3, 1.4, 6.1)"""
        # Mock search results
        mock_rows = [
            {
                'id': 1,
                'name': 'Mario Rossi',
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'registration_no': 'EMP001',
                'profile_image': 'mario_rossi.jpg',
                'email': 'mario.rossi@example.com',
                'short_name': 'M. Rossi'
            }
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch.object(Person, 'from_sqlite_row') as mock_from_row:
            mock_person = Person(id=1, name='Mario Rossi', first_name='Mario', last_name='Rossi')
            mock_from_row.return_value = mock_person
            
            # Test search by first name
            result = person_service.search("Mario", ["first_name", "last_name"])
            
            assert len(result) == 1
            assert result[0] == mock_person
            
            # Verify search query includes enhanced fields
            call_args = mock_db_manager.fetch_all.call_args
            query = call_args[0][0]
            params = call_args[0][1]
            
            assert "first_name LIKE ?" in query
            assert "last_name LIKE ?" in query
            assert "%Mario%" in params
    
    def test_get_searchable_fields_includes_enhanced_fields(self, person_service):
        """Test get_searchable_fields includes enhanced fields"""
        fields = person_service.get_searchable_fields()
        
        expected_fields = ["name", "short_name", "email", "first_name", "last_name", "registration_no"]
        
        for field in expected_fields:
            assert field in fields
    
    def test_validation_error_handling_with_enhanced_fields(self, person_service, mock_db_manager):
        """Test validation error handling for enhanced fields (Requirements 2.2, 2.3, 6.2)"""
        # Create person with validation errors
        person = Person(
            name="",  # Required field empty
            first_name="A" * 101,  # Too long
            registration_no="B" * 26,  # Too long
            profile_image="C" * 1025,  # Too long
            email="invalid-email"  # Invalid format
        )
        
        with pytest.raises(ServiceValidationException) as exc_info:
            person_service.create(person)
        
        # Should have multiple validation errors
        errors = exc_info.value.errors
        assert len(errors) >= 4
        
        error_fields = [error.field for error in errors]
        assert "name" in error_fields
        assert "first_name" in error_fields
        assert "registration_no" in error_fields
        assert "profile_image" in error_fields
        assert "email" in error_fields
    
    def test_backward_compatibility_with_name_field(self, person_service, mock_db_manager):
        """Test backward compatibility with existing name field (Requirement 5.3)"""
        # Create person with only name field (old way)
        person = Person(name="Mario Rossi", email="mario.rossi@example.com")
        
        # Mock successful creation
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        person_service.get_by_id = Mock(return_value=person)
        
        result = person_service.create(person)
        
        assert result == person
        
        # Verify query parameters handle None values for enhanced fields
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        
        # Should have None values for enhanced fields
        assert None in params  # first_name should be None
        assert None in params  # last_name should be None
        assert None in params  # registration_no should be None
        assert None in params  # profile_image should be None
    
    def test_profile_image_handling(self, person_service, mock_db_manager):
        """Test profile image handling (Requirements 6.1, 6.4)"""
        # Test with profile image
        person = Person(
            name="Mario Rossi",
            profile_image="profiles/mario_rossi.jpg"
        )
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        person_service.get_by_id = Mock(return_value=person)
        
        result = person_service.create(person)
        
        assert result == person
        
        # Verify profile image is included in parameters
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        
        assert "profiles/mario_rossi.jpg" in params
    
    def test_name_suggestion_functionality(self, person_service):
        """Test name suggestion from first_name and last_name (Requirement 2.1)"""
        # This would typically be tested in the model, but we can test
        # that the service properly handles the suggested_name_format property
        person = Person(
            first_name="Mario",
            last_name="Rossi",
            name=""  # Empty name to test suggestion
        )
        
        # The model should provide the suggested format
        assert person.suggested_name_format == "Rossi, Mario"
        
        # Service should be able to work with this
        assert person.suggested_name_format != ""
    
    def test_error_handling_in_statistics(self, person_service, mock_db_manager):
        """Test error handling in get_person_statistics"""
        # Mock database error
        mock_db_manager.fetch_one.side_effect = Exception("Database error")
        
        stats = person_service.get_person_statistics(1)
        
        # Should return empty dict on error
        assert stats == {}
    
    def test_comprehensive_statistics(self, person_service, mock_db_manager):
        """Test get_comprehensive_statistics method"""
        # Mock various database responses
        mock_responses = [
            {'count': 100},    # total_persons (from count method)
            {'count': 80},     # persons_with_assignments
            {'single_assignment': 30, 'dual_assignment': 25, 'multiple_assignment': 25},  # assignment distribution
            {'avg_workload': 0.85, 'max_workload': 1.5, 'overloaded_count': 5},  # workload stats
            {'count': 15}      # persons_with_interim
        ]
        
        # Mock the count method
        person_service.count = Mock(return_value=100)
        mock_db_manager.fetch_one.side_effect = mock_responses
        
        stats = person_service.get_comprehensive_statistics()
        
        assert stats['total_persons'] == 100
        assert stats['persons_with_assignments'] == 80
        assert stats['persons_without_assignments'] == 20
        assert stats['single_assignment_persons'] == 30
        assert stats['dual_assignment_persons'] == 25
        assert stats['multiple_assignment_persons'] == 25
        assert stats['avg_workload'] == 85  # Converted to percentage
        assert stats['max_workload'] == 150  # Converted to percentage
        assert stats['overloaded_persons'] == 5
        assert stats['persons_with_interim'] == 15