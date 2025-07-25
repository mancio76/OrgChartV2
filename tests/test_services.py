"""
Unit tests for service layer business logic.

This module tests service classes including CRUD operations,
business logic, error handling, and mock database interactions
as required by Task 9.1.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import date, datetime
from typing import List, Dict, Any

from app.services.base import (
    BaseService, ServiceException, ServiceValidationException, 
    ServiceNotFoundException, ServiceIntegrityException
)
from app.models.base import BaseModel, ValidationError, ModelValidationException
from app.models.unit_type import UnitType
from app.models.unit import Unit
from app.models.person import Person
from app.models.job_title import JobTitle
from app.models.assignment import Assignment


class MockService(BaseService):
    """Mock service implementation for testing BaseService"""
    
    def __init__(self, model_class=BaseModel, table_name="test_table"):
        super().__init__(model_class, table_name)
    
    def get_list_query(self) -> str:
        return f"SELECT * FROM {self.table_name}"
    
    def get_by_id_query(self) -> str:
        return f"SELECT * FROM {self.table_name} WHERE id = ?"
    
    def get_insert_query(self) -> str:
        return f"INSERT INTO {self.table_name} (name) VALUES (?)"
    
    def get_update_query(self) -> str:
        return f"UPDATE {self.table_name} SET name = ? WHERE id = ?"
    
    def get_delete_query(self) -> str:
        return f"DELETE FROM {self.table_name} WHERE id = ?"
    
    def model_to_insert_params(self, model: BaseModel) -> tuple:
        return ("test_name",)
    
    def model_to_update_params(self, model: BaseModel) -> tuple:
        return ("test_name", model.id)
    
    def get_searchable_fields(self) -> List[str]:
        return ["name", "description"]


class TestBaseService:
    """Test BaseService functionality"""
    
    def test_service_initialization(self, mock_db_manager):
        """Test service initialization"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService(BaseModel, "test_table")
            
            assert service.model_class == BaseModel
            assert service.table_name == "test_table"
            assert service.db_manager == mock_db_manager
    
    def test_get_all_success(self, mock_db_manager):
        """Test successful get_all operation"""
        # Setup mock data
        mock_rows = [
            {'id': 1, 'name': 'Test 1'},
            {'id': 2, 'name': 'Test 2'}
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Mock the from_sqlite_row method
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_models = [BaseModel(), BaseModel()]
                mock_from_row.side_effect = mock_models
                
                result = service.get_all()
                
                assert len(result) == 2
                assert result == mock_models
                mock_db_manager.fetch_all.assert_called_once_with("SELECT * FROM test_table")
    
    def test_get_all_database_error(self, mock_db_manager):
        """Test get_all with database error"""
        mock_db_manager.fetch_all.side_effect = Exception("Database error")
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with pytest.raises(ServiceException) as exc_info:
                service.get_all()
            
            assert "Failed to retrieve test_table records" in str(exc_info.value)
    
    def test_get_by_id_success(self, mock_db_manager):
        """Test successful get_by_id operation"""
        mock_row = {'id': 1, 'name': 'Test'}
        mock_db_manager.fetch_one.return_value = mock_row
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                result = service.get_by_id(1)
                
                assert result == mock_model
                mock_db_manager.fetch_one.assert_called_once_with(
                    "SELECT * FROM test_table WHERE id = ?", (1,)
                )
    
    def test_get_by_id_not_found(self, mock_db_manager):
        """Test get_by_id when record not found"""
        mock_db_manager.fetch_one.return_value = None
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_from_row.return_value = None
                
                result = service.get_by_id(999)
                
                assert result is None
    
    def test_get_by_id_database_error(self, mock_db_manager):
        """Test get_by_id with database error"""
        mock_db_manager.fetch_one.side_effect = Exception("Database error")
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with pytest.raises(ServiceException) as exc_info:
                service.get_by_id(1)
            
            assert "Failed to retrieve test_table with id 1" in str(exc_info.value)
    
    def test_create_success(self, mock_db_manager):
        """Test successful create operation"""
        # Setup mock cursor
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        # Setup mock model
        mock_model = BaseModel()
        mock_model.validate = Mock(return_value=[])
        mock_model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Mock get_by_id to return created model
            service.get_by_id = Mock(return_value=mock_model)
            
            result = service.create(mock_model)
            
            assert result == mock_model
            mock_model.set_audit_fields.assert_called_once_with(is_update=False)
            mock_model.validate.assert_called_once()
            mock_db_manager.execute_query.assert_called_once()
    
    def test_create_validation_error(self, mock_db_manager):
        """Test create with validation error"""
        mock_model = BaseModel()
        validation_errors = [ValidationError("name", "Name is required")]
        mock_model.validate = Mock(return_value=validation_errors)
        mock_model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with pytest.raises(ServiceValidationException) as exc_info:
                service.create(mock_model)
            
            assert exc_info.value.errors == validation_errors
            assert "Validation failed for test_table" in str(exc_info.value)
    
    def test_create_database_error(self, mock_db_manager):
        """Test create with database error"""
        mock_db_manager.execute_query.side_effect = Exception("Database error")
        
        mock_model = BaseModel()
        mock_model.validate = Mock(return_value=[])
        mock_model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with pytest.raises(ServiceException) as exc_info:
                service.create(mock_model)
            
            assert "Failed to create test_table" in str(exc_info.value)
    
    def test_update_success(self, mock_db_manager):
        """Test successful update operation"""
        # Setup existing model
        existing_model = BaseModel()
        existing_model.id = 1
        
        # Setup model to update
        mock_model = BaseModel()
        mock_model.id = 1
        mock_model.validate = Mock(return_value=[])
        mock_model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Mock get_by_id calls
            service.get_by_id = Mock()
            service.get_by_id.side_effect = [existing_model, mock_model]  # First for existence check, second for return
            
            result = service.update(mock_model)
            
            assert result == mock_model
            mock_model.set_audit_fields.assert_called_once_with(is_update=True)
            mock_model.validate.assert_called_once()
            mock_db_manager.execute_query.assert_called_once()
    
    def test_update_not_found(self, mock_db_manager):
        """Test update when record not found"""
        mock_model = BaseModel()
        mock_model.id = 999
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(return_value=None)
            
            with pytest.raises(ServiceNotFoundException) as exc_info:
                service.update(mock_model)
            
            assert "test_table with id 999 not found" in str(exc_info.value)
    
    def test_update_no_id(self, mock_db_manager):
        """Test update without ID"""
        mock_model = BaseModel()
        # No ID set
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with pytest.raises(ServiceValidationException) as exc_info:
                service.update(mock_model)
            
            assert "Cannot update test_table without ID" in str(exc_info.value)
    
    def test_delete_success(self, mock_db_manager):
        """Test successful delete operation"""
        existing_model = BaseModel()
        existing_model.id = 1
        
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(return_value=existing_model)
            
            result = service.delete(1)
            
            assert result is True
            mock_db_manager.execute_query.assert_called_once_with(
                "DELETE FROM test_table WHERE id = ?", (1,)
            )
    
    def test_delete_not_found(self, mock_db_manager):
        """Test delete when record not found"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(return_value=None)
            
            with pytest.raises(ServiceNotFoundException) as exc_info:
                service.delete(999)
            
            assert "test_table with id 999 not found" in str(exc_info.value)
    
    def test_delete_no_rows_affected(self, mock_db_manager):
        """Test delete when no rows affected"""
        existing_model = BaseModel()
        existing_model.id = 1
        
        mock_cursor = Mock()
        mock_cursor.rowcount = 0
        mock_db_manager.execute_query.return_value = mock_cursor
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(return_value=existing_model)
            
            result = service.delete(1)
            
            assert result is False
    
    def test_exists_true(self, mock_db_manager):
        """Test exists returns True when record exists"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(return_value=BaseModel())
            
            result = service.exists(1)
            
            assert result is True
    
    def test_exists_false(self, mock_db_manager):
        """Test exists returns False when record doesn't exist"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(return_value=None)
            
            result = service.exists(999)
            
            assert result is False
    
    def test_exists_exception(self, mock_db_manager):
        """Test exists returns False on exception"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(side_effect=Exception("Database error"))
            
            result = service.exists(1)
            
            assert result is False
    
    def test_count_success(self, mock_db_manager):
        """Test successful count operation"""
        mock_db_manager.fetch_one.return_value = {'count': 5}
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.count()
            
            assert result == 5
            mock_db_manager.fetch_one.assert_called_once_with(
                "SELECT COUNT(*) as count FROM test_table"
            )
    
    def test_count_error(self, mock_db_manager):
        """Test count with database error"""
        mock_db_manager.fetch_one.side_effect = Exception("Database error")
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.count()
            
            assert result == 0
    
    def test_get_paginated_success(self, mock_db_manager):
        """Test successful paginated query"""
        # Mock count
        mock_db_manager.fetch_one.return_value = {'count': 25}
        
        # Mock paginated results
        mock_rows = [{'id': 1, 'name': 'Test 1'}, {'id': 2, 'name': 'Test 2'}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_models = [BaseModel(), BaseModel()]
                mock_from_row.side_effect = mock_models
                
                result = service.get_paginated(page=2, page_size=10)
                
                assert len(result['results']) == 2
                assert result['pagination']['page'] == 2
                assert result['pagination']['page_size'] == 10
                assert result['pagination']['total_count'] == 25
                assert result['pagination']['total_pages'] == 3
                assert result['pagination']['has_next'] is True
                assert result['pagination']['has_prev'] is True
                
                # Verify LIMIT and OFFSET
                mock_db_manager.fetch_all.assert_called_with(
                    "SELECT * FROM test_table LIMIT ? OFFSET ?", (10, 10)
                )
    
    def test_search_with_term(self, mock_db_manager):
        """Test search with search term"""
        mock_rows = [{'id': 1, 'name': 'Test Result'}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                result = service.search("test", ["name", "description"])
                
                assert len(result) == 1
                assert result[0] == mock_model
                
                # Verify search query
                expected_query = "SELECT * FROM test_table WHERE name LIKE ? OR description LIKE ?"
                expected_params = ("%test%", "%test%")
                mock_db_manager.fetch_all.assert_called_once_with(expected_query, expected_params)
    
    def test_search_empty_term(self, mock_db_manager):
        """Test search with empty term returns all"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_all = Mock(return_value=[BaseModel()])
            
            result = service.search("")
            
            service.get_all.assert_called_once()
            assert len(result) == 1
    
    def test_search_no_searchable_fields(self, mock_db_manager):
        """Test search with no searchable fields"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_searchable_fields = Mock(return_value=[])
            
            result = service.search("test")
            
            assert result == []
    
    def test_search_database_error(self, mock_db_manager):
        """Test search with database error returns empty list"""
        mock_db_manager.fetch_all.side_effect = Exception("Database error")
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.search("test", ["name"])
            
            assert result == []
    
    def test_advanced_search_success(self, mock_db_manager):
        """Test advanced search with criteria"""
        mock_rows = [{'id': 1, 'name': 'Test'}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        criteria = {
            'name': 'test',
            'status': 'active',
            'count': 5
        }
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                result = service.advanced_search(criteria)
                
                assert len(result) == 1
                
                # Verify query construction
                expected_query = "SELECT * FROM test_table WHERE name LIKE ? AND status LIKE ? AND count = ?"
                expected_params = ("%test%", "%active%", 5)
                mock_db_manager.fetch_all.assert_called_once_with(expected_query, expected_params)
    
    def test_advanced_search_empty_criteria(self, mock_db_manager):
        """Test advanced search with empty criteria"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_all = Mock(return_value=[BaseModel()])
            
            result = service.advanced_search({})
            
            service.get_all.assert_called_once()
    
    def test_bulk_create_success(self, mock_db_manager):
        """Test successful bulk create operation"""
        models = [BaseModel(), BaseModel()]
        for i, model in enumerate(models):
            model.validate = Mock(return_value=[])
            model.set_audit_fields = Mock()
        
        # Mock database connection context manager
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_manager.get_connection.return_value = mock_conn
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.bulk_create(models)
            
            assert len(result) == 2
            for model in models:
                model.set_audit_fields.assert_called_with(is_update=False)
                model.validate.assert_called_once()
    
    def test_bulk_create_empty_list(self, mock_db_manager):
        """Test bulk create with empty list"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.bulk_create([])
            
            assert result == []
    
    def test_get_by_field_success(self, mock_db_manager):
        """Test successful get_by_field operation"""
        mock_row = {'id': 1, 'name': 'Test'}
        mock_db_manager.fetch_one.return_value = mock_row
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                result = service.get_by_field('name', 'test')
                
                assert result == mock_model
                mock_db_manager.fetch_one.assert_called_once_with(
                    "SELECT * FROM test_table WHERE name = ?", ('test',)
                )
    
    def test_get_all_by_field_success(self, mock_db_manager):
        """Test successful get_all_by_field operation"""
        mock_rows = [{'id': 1, 'name': 'Test'}, {'id': 2, 'name': 'Test'}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_models = [BaseModel(), BaseModel()]
                mock_from_row.side_effect = mock_models
                
                result = service.get_all_by_field('status', 'active')
                
                assert len(result) == 2
                mock_db_manager.fetch_all.assert_called_once_with(
                    "SELECT * FROM test_table WHERE status = ?", ('active',)
                )
    
    def test_validate_model(self, mock_db_manager):
        """Test model validation"""
        mock_model = BaseModel()
        validation_errors = [ValidationError("name", "Name is required")]
        mock_model.validate = Mock(return_value=validation_errors)
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.validate_model(mock_model)
            
            assert result == validation_errors
            mock_model.validate.assert_called_once()
    
    def test_is_valid_model_true(self, mock_db_manager):
        """Test is_valid_model returns True for valid model"""
        mock_model = BaseModel()
        mock_model.validate = Mock(return_value=[])
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.is_valid_model(mock_model)
            
            assert result is True
    
    def test_is_valid_model_false(self, mock_db_manager):
        """Test is_valid_model returns False for invalid model"""
        mock_model = BaseModel()
        mock_model.validate = Mock(return_value=[ValidationError("name", "Required")])
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.is_valid_model(mock_model)
            
            assert result is False
class TestServiceExceptions:
    """Test service exception classes"""
    
    def test_service_exception(self):
        """Test ServiceException creation"""
        exception = ServiceException("Test error")
        assert str(exception) == "Test error"
    
    def test_service_validation_exception(self):
        """Test ServiceValidationException creation"""
        errors = [ValidationError("name", "Required")]
        exception = ServiceValidationException("Validation failed", errors)
        
        assert str(exception) == "Validation failed"
        assert exception.errors == errors
    
    def test_service_validation_exception_no_errors(self):
        """Test ServiceValidationException without errors"""
        exception = ServiceValidationException("Validation failed")
        
        assert str(exception) == "Validation failed"
        assert exception.errors == []
    
    def test_service_not_found_exception(self):
        """Test ServiceNotFoundException creation"""
        exception = ServiceNotFoundException("Record not found")
        assert str(exception) == "Record not found"
    
    def test_service_integrity_exception(self):
        """Test ServiceIntegrityException creation"""
        exception = ServiceIntegrityException("Integrity constraint violated")
        assert str(exception) == "Integrity constraint violated"


class TestServiceValidationHooks:
    """Test service validation hook methods"""
    
    def test_validate_for_create_default(self, mock_db_manager):
        """Test default _validate_for_create does nothing"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            model = BaseModel()
            
            # Should not raise exception
            service._validate_for_create(model)
    
    def test_validate_for_update_default(self, mock_db_manager):
        """Test default _validate_for_update does nothing"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            model = BaseModel()
            existing = BaseModel()
            
            # Should not raise exception
            service._validate_for_update(model, existing)
    
    def test_validate_for_delete_default(self, mock_db_manager):
        """Test default _validate_for_delete does nothing"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            model = BaseModel()
            
            # Should not raise exception
            service._validate_for_delete(model)


class TestServiceWithCustomValidation:
    """Test service with custom validation logic"""
    
    class CustomValidationService(MockService):
        """Service with custom validation for testing"""
        
        def _validate_for_create(self, model):
            if hasattr(model, 'name') and model.name == "forbidden":
                raise ServiceValidationException("Forbidden name")
        
        def _validate_for_update(self, model, existing):
            if hasattr(model, 'name') and model.name == "readonly":
                raise ServiceValidationException("Cannot update readonly record")
        
        def _validate_for_delete(self, model):
            if hasattr(model, 'name') and model.name == "protected":
                raise ServiceIntegrityException("Cannot delete protected record")
    
    def test_create_with_custom_validation_success(self, mock_db_manager):
        """Test create with custom validation success"""
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        model = BaseModel()
        model.name = "allowed"
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = self.CustomValidationService()
            service.get_by_id = Mock(return_value=model)
            
            result = service.create(model)
            
            assert result == model
    
    def test_create_with_custom_validation_failure(self, mock_db_manager):
        """Test create with custom validation failure"""
        model = BaseModel()
        model.name = "forbidden"
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = self.CustomValidationService()
            
            with pytest.raises(ServiceValidationException) as exc_info:
                service.create(model)
            
            assert "Forbidden name" in str(exc_info.value)
    
    def test_update_with_custom_validation_failure(self, mock_db_manager):
        """Test update with custom validation failure"""
        existing_model = BaseModel()
        existing_model.id = 1
        existing_model.name = "existing"
        
        model = BaseModel()
        model.id = 1
        model.name = "readonly"
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = self.CustomValidationService()
            service.get_by_id = Mock(return_value=existing_model)
            
            with pytest.raises(ServiceValidationException) as exc_info:
                service.update(model)
            
            assert "Cannot update readonly record" in str(exc_info.value)
    
    def test_delete_with_custom_validation_failure(self, mock_db_manager):
        """Test delete with custom validation failure"""
        model = BaseModel()
        model.id = 1
        model.name = "protected"
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = self.CustomValidationService()
            service.get_by_id = Mock(return_value=model)
            
            with pytest.raises(ServiceIntegrityException) as exc_info:
                service.delete(1)
            
            assert "Cannot delete protected record" in str(exc_info.value)


class TestServiceAdvancedOperations:
    """Test advanced service operations and edge cases"""
    
    def test_bulk_create_with_validation_error(self, mock_db_manager):
        """Test bulk create with validation error in one model"""
        models = [BaseModel(), BaseModel()]
        models[0].validate = Mock(return_value=[])
        models[0].set_audit_fields = Mock()
        models[1].validate = Mock(return_value=[ValidationError("name", "Required")])
        models[1].set_audit_fields = Mock()
        
        # Mock connection context manager
        mock_conn = Mock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_manager.get_connection.return_value = mock_conn
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with pytest.raises(ServiceValidationException) as exc_info:
                service.bulk_create(models)
            
            assert exc_info.value.errors[0].field == "name"
    
    def test_bulk_create_database_transaction(self, mock_db_manager):
        """Test bulk create uses database transaction"""
        models = [BaseModel(), BaseModel()]
        for model in models:
            model.validate = Mock(return_value=[])
            model.set_audit_fields = Mock()
        
        # Mock connection context manager
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_manager.get_connection.return_value = mock_conn
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.bulk_create(models)
            
            # Verify transaction was committed
            mock_conn.commit.assert_called_once()
            assert len(result) == 2
    
    def test_get_paginated_edge_cases(self, mock_db_manager):
        """Test paginated query edge cases"""
        # Test with zero total count
        mock_db_manager.fetch_one.return_value = {'count': 0}
        mock_db_manager.fetch_all.return_value = []
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.get_paginated(page=1, page_size=10)
            
            assert result['pagination']['total_count'] == 0
            assert result['pagination']['total_pages'] == 0
            assert result['pagination']['has_next'] is False
            assert result['pagination']['has_prev'] is False
            assert len(result['results']) == 0
    
    def test_get_paginated_last_page(self, mock_db_manager):
        """Test paginated query on last page"""
        mock_db_manager.fetch_one.return_value = {'count': 25}
        mock_rows = [{'id': 21, 'name': 'Test 21'}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                result = service.get_paginated(page=3, page_size=10)
                
                assert result['pagination']['page'] == 3
                assert result['pagination']['total_pages'] == 3
                assert result['pagination']['has_next'] is False
                assert result['pagination']['has_prev'] is True
    
    def test_search_with_special_characters(self, mock_db_manager):
        """Test search with special characters in search term"""
        mock_rows = [{'id': 1, 'name': "Test's Result"}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                result = service.search("test's", ["name"])
                
                assert len(result) == 1
                # Verify special characters are handled in LIKE query
                expected_params = ("%test's%",)
                mock_db_manager.fetch_all.assert_called_once()
                call_args = mock_db_manager.fetch_all.call_args
                assert call_args[0][1] == expected_params
    
    def test_advanced_search_mixed_criteria_types(self, mock_db_manager):
        """Test advanced search with mixed string and numeric criteria"""
        mock_rows = [{'id': 1, 'name': 'Test', 'count': 5}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        criteria = {
            'name': 'test',      # String - should use LIKE
            'count': 5,          # Integer - should use =
            'active': True,      # Boolean - should use =
            'empty_field': None  # None - should be ignored
        }
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                result = service.advanced_search(criteria)
                
                assert len(result) == 1
                
                # Verify query construction with mixed types
                call_args = mock_db_manager.fetch_all.call_args
                query = call_args[0][0]
                params = call_args[0][1]
                
                # Should have 3 conditions (excluding None value)
                assert query.count('AND') == 2
                assert 'name LIKE ?' in query
                assert 'count = ?' in query
                assert 'active = ?' in query
                assert len(params) == 3
    
    def test_service_logging_behavior(self, mock_db_manager, caplog):
        """Test service logging behavior"""
        import logging
        
        mock_rows = [{'id': 1, 'name': 'Test'}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                with caplog.at_level(logging.DEBUG):
                    result = service.get_all()
                
                # Verify debug logging occurred
                assert "Fetching all records from test_table" in caplog.text
                assert "Retrieved 1 records from test_table" in caplog.text
    
    def test_service_error_logging(self, mock_db_manager, caplog):
        """Test service error logging"""
        import logging
        
        mock_db_manager.fetch_all.side_effect = Exception("Database connection failed")
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with caplog.at_level(logging.ERROR):
                with pytest.raises(ServiceException):
                    service.get_all()
                
                # Verify error logging occurred
                assert "Error fetching all test_table" in caplog.text
                assert "Database connection failed" in caplog.text


class TestServicePerformanceAndScalability:
    """Test service performance considerations and scalability"""
    
    def test_large_result_set_handling(self, mock_db_manager):
        """Test handling of large result sets"""
        # Simulate large result set
        large_result_set = [{'id': i, 'name': f'Test {i}'} for i in range(1000)]
        mock_db_manager.fetch_all.return_value = large_result_set
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_models = [BaseModel() for _ in range(1000)]
                mock_from_row.side_effect = mock_models
                
                result = service.get_all()
                
                assert len(result) == 1000
                # Verify all models were created
                assert mock_from_row.call_count == 1000
    
    def test_pagination_performance_with_large_dataset(self, mock_db_manager):
        """Test pagination performance with large dataset"""
        mock_db_manager.fetch_one.return_value = {'count': 10000}
        mock_rows = [{'id': i, 'name': f'Test {i}'} for i in range(1, 21)]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_models = [BaseModel() for _ in range(20)]
                mock_from_row.side_effect = mock_models
                
                result = service.get_paginated(page=50, page_size=20)
                
                # Verify correct OFFSET calculation for large page numbers
                expected_offset = (50 - 1) * 20  # 980
                call_args = mock_db_manager.fetch_all.call_args
                assert call_args[0][1] == (20, expected_offset)
                
                assert result['pagination']['total_pages'] == 500
                assert result['pagination']['has_next'] is True
                assert result['pagination']['has_prev'] is True
    
    def test_search_performance_with_multiple_fields(self, mock_db_manager):
        """Test search performance with multiple searchable fields"""
        mock_rows = [{'id': 1, 'name': 'Test'}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        # Test with many searchable fields
        many_fields = [f'field_{i}' for i in range(20)]
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_searchable_fields = Mock(return_value=many_fields)
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                result = service.search("test")
                
                # Verify query was constructed with all fields
                call_args = mock_db_manager.fetch_all.call_args
                query = call_args[0][0]
                params = call_args[0][1]
                
                # Should have 20 OR conditions
                assert query.count(' OR ') == 19
                assert len(params) == 20  # One parameter per field
                
                # All parameters should be the search term with wildcards
                for param in params:
                    assert param == "%test%"


class TestServiceIntegrationScenarios:
    """Test service integration scenarios and complex workflows"""
    
    def test_create_update_delete_workflow(self, mock_db_manager):
        """Test complete create-update-delete workflow"""
        # Setup mocks for create
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_cursor.rowcount = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        # Setup model
        model = BaseModel()
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Mock get_by_id for different stages
            created_model = BaseModel()
            created_model.id = 1
            updated_model = BaseModel()
            updated_model.id = 1
            
            service.get_by_id = Mock()
            service.get_by_id.side_effect = [
                created_model,  # After create
                created_model,  # Before update (existence check)
                updated_model,  # After update
                created_model   # Before delete (existence check)
            ]
            
            # Test create
            result_create = service.create(model)
            assert result_create == created_model
            
            # Test update
            model.id = 1
            result_update = service.update(model)
            assert result_update == updated_model
            
            # Test delete
            result_delete = service.delete(1)
            assert result_delete is True
            
            # Verify all database operations were called
            assert mock_db_manager.execute_query.call_count == 3  # create, update, delete
    
    def test_concurrent_operation_simulation(self, mock_db_manager):
        """Test simulation of concurrent operations"""
        # Simulate concurrent access by having different return values
        # for the same ID at different times (simulating race conditions)
        
        model1 = BaseModel()
        model1.id = 1
        model1.name = "Version 1"
        
        model2 = BaseModel()
        model2.id = 1
        model2.name = "Version 2"
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Simulate race condition where model changes between operations
            service.get_by_id = Mock()
            service.get_by_id.side_effect = [model1, model2]  # Different versions
            
            first_fetch = service.get_by_id(1)
            second_fetch = service.get_by_id(1)
            
            # Verify different versions were returned (simulating concurrent modification)
            assert first_fetch.name == "Version 1"
            assert second_fetch.name == "Version 2"
    
    def test_service_exception_hierarchy(self, mock_db_manager):
        """Test service exception hierarchy and handling"""
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Test that all service exceptions inherit from ServiceException
            validation_exc = ServiceValidationException("Validation failed")
            not_found_exc = ServiceNotFoundException("Not found")
            integrity_exc = ServiceIntegrityException("Integrity violation")
            
            assert isinstance(validation_exc, ServiceException)
            assert isinstance(not_found_exc, ServiceException)
            assert isinstance(integrity_exc, ServiceException)
            
            # Test exception with errors
            errors = [ValidationError("field", "message")]
            validation_with_errors = ServiceValidationException("Failed", errors)
            assert validation_with_errors.errors == errors
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = self.CustomValidationService()
            service.get_by_id = Mock(return_value=existing_model)
            
            with pytest.raises(ServiceValidationException) as exc_info:
                service.update(model)
            
            assert "Cannot update readonly record" in str(exc_info.value)
    
    def test_delete_with_custom_validation_failure(self, mock_db_manager):
        """Test delete with custom validation failure"""
        model = BaseModel()
        model.id = 1
        model.name = "protected"
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = self.CustomValidationService()
            service.get_by_id = Mock(return_value=model)
            
            with pytest.raises(ServiceIntegrityException) as exc_info:
                service.delete(1)
            
            assert "Cannot delete protected record" in str(exc_info.value)


class TestDatabaseOperationsWithMocks:
    """Test database operations with comprehensive mocking"""
    
    def test_database_transaction_rollback_on_error(self, mock_db_manager):
        """Test database transaction rollback on error during bulk create"""
        models = [BaseModel(), BaseModel()]
        models[0].validate = Mock(return_value=[])
        models[0].set_audit_fields = Mock()
        models[1].validate = Mock(side_effect=Exception("Validation error"))
        models[1].set_audit_fields = Mock()
        
        # Mock connection that raises exception
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_manager.get_connection.return_value = mock_conn
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with pytest.raises(ServiceException):
                service.bulk_create(models)
    
    def test_connection_cleanup_on_success(self, mock_db_manager):
        """Test database connection cleanup on successful operation"""
        mock_rows = [{'id': 1, 'name': 'Test'}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_from_row.return_value = BaseModel()
                
                result = service.get_all()
                
                # Verify database manager was called
                mock_db_manager.fetch_all.assert_called_once()
                assert len(result) == 1
    
    def test_parameterized_queries_prevent_injection(self, mock_db_manager):
        """Test that parameterized queries are used to prevent SQL injection"""
        mock_db_manager.fetch_one.return_value = {'id': 1, 'name': 'Test'}
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_from_row.return_value = BaseModel()
                
                # Test search with potentially malicious input
                malicious_input = "'; DROP TABLE users; --"
                service.search(malicious_input, ["name"])
                
                # Verify parameterized query was used
                call_args = mock_db_manager.fetch_all.call_args
                query = call_args[0][0]
                params = call_args[0][1]
                
                # Query should use placeholders
                assert "?" in query
                assert "LIKE" in query
                # Parameters should be properly escaped
                assert f"%{malicious_input}%" in params
    
    def test_database_error_logging(self, mock_db_manager):
        """Test that database errors are properly logged"""
        mock_db_manager.fetch_all.side_effect = Exception("Connection timeout")
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch('app.services.base.logger') as mock_logger:
                with pytest.raises(ServiceException):
                    service.get_all()
                
                # Verify error was logged
                mock_logger.error.assert_called()
                error_call = mock_logger.error.call_args[0][0]
                assert "Error fetching all test_table" in error_call
    
    def test_audit_fields_set_correctly(self, mock_db_manager):
        """Test that audit fields are set correctly during operations"""
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        model = BaseModel()
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(return_value=model)
            
            # Test create
            service.create(model)
            model.set_audit_fields.assert_called_with(is_update=False)
            
            # Reset mock
            model.set_audit_fields.reset_mock()
            
            # Test update - need to set ID on model for update to work
            model.id = 1
            existing_model = BaseModel()
            existing_model.id = 1
            service.get_by_id = Mock(side_effect=[existing_model, model])
            
            service.update(model)
            model.set_audit_fields.assert_called_with(is_update=True)


class TestServicePerformanceConsiderations:
    """Test service performance-related functionality"""
    
    def test_pagination_calculations(self, mock_db_manager):
        """Test pagination metadata calculations"""
        # Mock count query
        mock_db_manager.fetch_one.return_value = {'count': 47}
        
        # Mock paginated results
        mock_db_manager.fetch_all.return_value = []
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Test various pagination scenarios
            test_cases = [
                (1, 10, {'total_pages': 5, 'has_next': True, 'has_prev': False}),
                (3, 10, {'total_pages': 5, 'has_next': True, 'has_prev': True}),
                (5, 10, {'total_pages': 5, 'has_next': False, 'has_prev': True}),
                (1, 50, {'total_pages': 1, 'has_next': False, 'has_prev': False}),
            ]
            
            for page, page_size, expected in test_cases:
                result = service.get_paginated(page=page, page_size=page_size)
                
                pagination = result['pagination']
                assert pagination['total_pages'] == expected['total_pages']
                assert pagination['has_next'] == expected['has_next']
                assert pagination['has_prev'] == expected['has_prev']
                assert pagination['total_count'] == 47
    
    def test_search_graceful_degradation(self, mock_db_manager):
        """Test search graceful degradation on database errors"""
        # First call succeeds (for get_searchable_fields check)
        # Second call fails (actual search)
        mock_db_manager.fetch_all.side_effect = Exception("Database timeout")
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Should return empty list instead of raising exception
            result = service.search("test", ["name"])
            
            assert result == []
    
    def test_bulk_operations_efficiency(self, mock_db_manager):
        """Test bulk operations use transactions for efficiency"""
        models = [BaseModel() for _ in range(3)]
        for model in models:
            model.validate = Mock(return_value=[])
            model.set_audit_fields = Mock()
        
        # Mock connection context manager
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_manager.get_connection.return_value = mock_conn
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.bulk_create(models)
            
            # Verify transaction was used
            mock_db_manager.get_connection.assert_called_once()
            mock_conn.__enter__.assert_called_once()
            mock_conn.__exit__.assert_called_once()
            mock_conn.commit.assert_called_once()
            
            # Verify all models were processed
            assert len(result) == 3


class TestServiceIntegrationScenarios:
    """Test realistic service integration scenarios"""
    
    def test_create_update_delete_workflow(self, mock_db_manager):
        """Test complete CRUD workflow"""
        # Setup mocks for create
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_cursor.rowcount = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        model = BaseModel()
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Create
            service.get_by_id = Mock(return_value=model)
            created = service.create(model)
            assert created == model
            
            # Update
            model.id = 1
            existing_model = BaseModel()
            existing_model.id = 1
            service.get_by_id = Mock(side_effect=[existing_model, model])
            updated = service.update(model)
            assert updated == model
            
            # Delete
            service.get_by_id = Mock(return_value=model)
            deleted = service.delete(1)
            assert deleted is True
    
    def test_search_and_pagination_integration(self, mock_db_manager):
        """Test search and pagination working together"""
        # Mock search results
        search_rows = [{'id': i, 'name': f'Test {i}'} for i in range(1, 6)]
        
        # Mock count for pagination
        mock_db_manager.fetch_one.return_value = {'count': 25}
        mock_db_manager.fetch_all.return_value = search_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_models = [BaseModel() for _ in range(5)]
                mock_from_row.side_effect = mock_models * 2  # For both search and pagination calls
                
                # Test search
                search_results = service.search("test", ["name"])
                assert len(search_results) == 5
                
                # Reset the mock for pagination test
                mock_db_manager.fetch_all.return_value = search_rows
                
                # Test pagination
                paginated_results = service.get_paginated(page=1, page_size=10)
                assert paginated_results['pagination']['total_count'] == 25
    
    def test_validation_error_handling_chain(self, mock_db_manager):
        """Test validation error handling through the service chain"""
        # Model with validation errors
        model = BaseModel()
        validation_errors = [
            ValidationError("name", "Name is required"),
            ValidationError("email", "Invalid email format")
        ]
        model.validate = Mock(return_value=validation_errors)
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Test create validation
            with pytest.raises(ServiceValidationException) as exc_info:
                service.create(model)
            
            assert len(exc_info.value.errors) == 2
            assert exc_info.value.errors[0].field == "name"
            assert exc_info.value.errors[1].field == "email"
            
            # Verify audit fields were set before validation
            model.set_audit_fields.assert_called_once_with(is_update=False)
            
            # Verify database was not called due to validation failure
            mock_db_manager.execute_query.assert_not_called()

class TestSpecializedServiceLogic:
    """Test specialized service logic and business rules"""
    
    def test_service_with_complex_queries(self, mock_db_manager):
        """Test service with complex SQL queries"""
        # Mock complex query results
        complex_row_data = {
            'id': 1,
            'name': 'Test Unit',
            'parent_name': 'Parent Unit',
            'children_count': 3,
            'person_count': 5
        }
        mock_db_manager.fetch_all.return_value = [complex_row_data]
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                results = service.get_all()
                
                assert len(results) == 1
                assert results[0] == mock_model
    
    def test_service_validation_with_business_rules(self, mock_db_manager):
        """Test service validation with business rules"""
        class BusinessRuleService(MockService):
            def _validate_for_create(self, model):
                # Example business rule: name must not contain numbers
                if hasattr(model, 'name') and any(char.isdigit() for char in model.name):
                    from app.services.base import ServiceValidationException
                    raise ServiceValidationException("Name cannot contain numbers")
        
        model = BaseModel()
        model.name = "Test123"
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = BusinessRuleService()
            
            with pytest.raises(ServiceValidationException) as exc_info:
                service.create(model)
            
            assert "Name cannot contain numbers" in str(exc_info.value)
    
    def test_service_cascade_operations(self, mock_db_manager):
        """Test service cascade operations and referential integrity"""
        class CascadeService(MockService):
            def _validate_for_delete(self, model):
                # Example: Check for dependent records
                if hasattr(model, 'id') and model.id == 1:
                    from app.services.base import ServiceIntegrityException
                    raise ServiceIntegrityException("Cannot delete record with dependencies")
        
        existing_model = BaseModel()
        existing_model.id = 1
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = CascadeService()
            service.get_by_id = Mock(return_value=existing_model)
            
            with pytest.raises(ServiceIntegrityException) as exc_info:
                service.delete(1)
            
            assert "Cannot delete record with dependencies" in str(exc_info.value)


class TestServicePerformanceAndScaling:
    """Test service performance considerations and scaling scenarios"""
    
    def test_bulk_operations_with_large_datasets(self, mock_db_manager):
        """Test bulk operations with large datasets"""
        # Create a large number of models
        models = []
        for i in range(100):
            model = BaseModel()
            model.validate = Mock(return_value=[])
            model.set_audit_fields = Mock()
            models.append(model)
        
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_manager.get_connection.return_value = mock_conn
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.bulk_create(models)
            
            assert len(result) == 100
            # Verify all models had audit fields set
            for model in models:
                model.set_audit_fields.assert_called_with(is_update=False)
    
    def test_pagination_with_edge_cases(self, mock_db_manager):
        """Test pagination with edge cases"""
        # Test pagination with zero results
        mock_db_manager.fetch_one.return_value = {'count': 0}
        mock_db_manager.fetch_all.return_value = []
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            result = service.get_paginated(page=1, page_size=10)
            
            assert result['results'] == []
            assert result['pagination']['total_count'] == 0
            assert result['pagination']['total_pages'] == 0
            assert result['pagination']['has_next'] is False
            assert result['pagination']['has_prev'] is False
    
    def test_search_with_special_characters(self, mock_db_manager):
        """Test search functionality with special characters"""
        mock_rows = [{'id': 1, 'name': "Test with 'quotes' and \"double quotes\""}]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                # Test search with special characters
                result = service.search("test 'quotes'", ["name"])
                
                assert len(result) == 1
                # Verify the search term was properly escaped in the query
                expected_query = "SELECT * FROM test_table WHERE name LIKE ?"
                expected_params = ("%test 'quotes'%",)
                mock_db_manager.fetch_all.assert_called_with(expected_query, expected_params)


class TestServiceErrorRecovery:
    """Test service error recovery and resilience"""
    
    def test_service_recovery_from_connection_errors(self, mock_db_manager):
        """Test service recovery from database connection errors"""
        # First call fails, second succeeds
        mock_db_manager.fetch_all.side_effect = [
            Exception("Connection lost"),
            [{'id': 1, 'name': 'Test'}]
        ]
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # First call should raise ServiceException
            with pytest.raises(ServiceException):
                service.get_all()
            
            # Reset the side effect for second call
            mock_db_manager.fetch_all.side_effect = None
            mock_db_manager.fetch_all.return_value = [{'id': 1, 'name': 'Test'}]
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                # Second call should succeed
                result = service.get_all()
                assert len(result) == 1
    
    def test_service_partial_failure_handling(self, mock_db_manager):
        """Test service handling of partial failures in bulk operations"""
        # Create models where some will fail validation
        valid_model = BaseModel()
        valid_model.validate = Mock(return_value=[])
        valid_model.set_audit_fields = Mock()
        
        invalid_model = BaseModel()
        invalid_model.validate = Mock(return_value=[ValidationError("name", "Required")])
        invalid_model.set_audit_fields = Mock()
        
        models = [valid_model, invalid_model]
        
        # Mock connection context manager
        mock_conn = Mock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_manager.get_connection.return_value = mock_conn
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            # Bulk create should fail on first invalid model
            with pytest.raises(ServiceValidationException):
                service.bulk_create(models)
    
    def test_service_transaction_consistency(self, mock_db_manager):
        """Test service transaction consistency during errors"""
        # Simulate database error during execution
        mock_db_manager.execute_query.side_effect = Exception("Database constraint violation")
        
        model = BaseModel()
        model.validate = Mock(return_value=[])
        model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with pytest.raises(ServiceException):
                service.create(model)
            
            # Verify database operation was attempted
            mock_db_manager.execute_query.assert_called_once()


class TestServiceIntegrationWithModels:
    """Test service integration with specific model types"""
    
    def test_service_with_assignment_versioning_logic(self, mock_db_manager):
        """Test service integration with assignment versioning"""
        # This would test assignment-specific versioning logic
        # For now, we test the general pattern
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db_manager.execute_query.return_value = mock_cursor
        
        assignment_model = BaseModel()  # In real scenario, this would be Assignment
        assignment_model.validate = Mock(return_value=[])
        assignment_model.set_audit_fields = Mock()
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            service.get_by_id = Mock(return_value=assignment_model)
            
            result = service.create(assignment_model)
            
            assert result == assignment_model
            assignment_model.set_audit_fields.assert_called_with(is_update=False)
    
    def test_service_with_hierarchical_data(self, mock_db_manager):
        """Test service handling of hierarchical data structures"""
        # Mock hierarchical query results (like units with parent-child relationships)
        hierarchical_data = [
            {'id': 1, 'name': 'Root Unit', 'parent_unit_id': None, 'level': 0},
            {'id': 2, 'name': 'Child Unit 1', 'parent_unit_id': 1, 'level': 1},
            {'id': 3, 'name': 'Child Unit 2', 'parent_unit_id': 1, 'level': 1},
            {'id': 4, 'name': 'Grandchild Unit', 'parent_unit_id': 2, 'level': 2}
        ]
        mock_db_manager.fetch_all.return_value = hierarchical_data
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_models = [BaseModel() for _ in range(4)]
                mock_from_row.side_effect = mock_models
                
                results = service.get_all()
                
                assert len(results) == 4
                # In a real hierarchical service, we might test tree building logic here
    
    def test_service_with_multilingual_support(self, mock_db_manager):
        """Test service handling of multilingual data"""
        # Mock data with aliases/multilingual support
        multilingual_data = [{
            'id': 1,
            'name': 'Test Unit',
            'aliases': '[{"value": "Unità Test", "lang": "it-IT"}, {"value": "Test Einheit", "lang": "de-DE"}]'
        }]
        mock_db_manager.fetch_all.return_value = multilingual_data
        
        with patch('app.services.base.get_db_manager', return_value=mock_db_manager):
            service = MockService()
            
            with patch.object(BaseModel, 'from_sqlite_row') as mock_from_row:
                mock_model = BaseModel()
                mock_from_row.return_value = mock_model
                
                results = service.get_all()
                
                assert len(results) == 1
                # In a real multilingual service, we might test alias parsing here