"""
Comprehensive unit tests for the ImportExportService class.

This module tests the core import/export service functionality including
file format detection, validation, transaction management, and orchestration.
"""

import os
import tempfile
import pytest
import json
import csv
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime

from app.services.import_export import (
    ImportExportService, ImportExportException, FileFormatDetectionError,
    TransactionRollbackError, TransactionContext
)
from app.models.import_export import (
    ImportOptions, ExportOptions, ImportResult, ExportResult, PreviewResult,
    ValidationResult, FileFormat, ConflictResolutionStrategy, ImportErrorType,
    ImportExportValidationError
)


class TestImportExportService:
    """Test cases for ImportExportService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ImportExportService()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clean up any remaining transaction contexts
        self.service.cleanup_transaction_contexts()
    
    def test_initialization(self):
        """Test that the service initializes correctly with all components."""
        assert self.service.db_manager is not None
        assert self.service.dependency_resolver is not None
        assert self.service.foreign_key_resolver is not None
        assert self.service.validation_framework is not None
        assert self.service.conflict_resolution_manager is not None
        assert self.service.error_logger is not None
        assert self.service.audit_manager is not None
        assert self.service.error_reporting_service is not None
        assert isinstance(self.service._transaction_contexts, dict)
        assert len(self.service._transaction_contexts) == 0
    
    def test_detect_file_format_json(self):
        """Test JSON file format detection."""
        # Create valid JSON file
        json_data = {"unit_types": [{"id": 1, "name": "Test"}]}
        json_file = os.path.join(self.temp_dir, "test.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)
        
        format_detected = self.service.detect_file_format(json_file)
        assert format_detected == FileFormat.JSON
    
    def test_detect_file_format_csv(self):
        """Test CSV file format detection."""
        # Create valid CSV file
        csv_file = os.path.join(self.temp_dir, "test.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name'])
            writer.writerow([1, 'Test Unit', 'TU'])
        
        format_detected = self.service.detect_file_format(csv_file)
        assert format_detected == FileFormat.CSV
    
    def test_detect_file_format_nonexistent_file(self):
        """Test error handling for non-existent files."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        
        with pytest.raises(FileFormatDetectionError) as exc_info:
            self.service.detect_file_format(nonexistent_file)
        
        assert "File not found" in str(exc_info.value)
    
    def test_detect_file_format_invalid_json(self):
        """Test error handling for invalid JSON files."""
        # Create invalid JSON file
        invalid_json_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json}')  # Invalid JSON syntax
        
        with pytest.raises(FileFormatDetectionError) as exc_info:
            self.service.detect_file_format(invalid_json_file)
        
        assert "Invalid JSON content" in str(exc_info.value)
    
    def test_detect_file_format_content_based(self):
        """Test content-based format detection for files without extensions."""
        # Create JSON file without extension
        json_file = os.path.join(self.temp_dir, "test_no_ext")
        json_data = {"unit_types": [{"id": 1, "name": "Test"}]}
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)
        
        format_detected = self.service.detect_file_format(json_file)
        assert format_detected == FileFormat.JSON
        
        # Create CSV file without extension
        csv_file = os.path.join(self.temp_dir, "test_csv_no_ext")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('id,name,short_name\n1,Test Unit,TU\n')
        
        format_detected = self.service.detect_file_format(csv_file)
        assert format_detected == FileFormat.CSV
    
    def test_detect_file_format_unsupported(self):
        """Test error handling for unsupported file formats."""
        # Create unsupported file type
        unsupported_file = os.path.join(self.temp_dir, "test.txt")
        with open(unsupported_file, 'w', encoding='utf-8') as f:
            f.write("This is plain text")
        
        with pytest.raises(FileFormatDetectionError) as exc_info:
            self.service.detect_file_format(unsupported_file)
        
        assert "Unable to detect file format" in str(exc_info.value)
    
    def test_validate_file_structure_json_valid(self):
        """Test JSON file structure validation with valid file."""
        # Create valid JSON file
        json_data = {
            "unit_types": [{"id": 1, "name": "Test Unit"}],
            "persons": [{"id": 1, "name": "John Doe"}]
        }
        json_file = os.path.join(self.temp_dir, "valid.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)
        
        errors = self.service.validate_file_structure(json_file, FileFormat.JSON)
        assert len(errors) == 0
    
    def test_validate_file_structure_csv_valid(self):
        """Test CSV file structure validation with valid file."""
        # Create valid CSV file
        csv_file = os.path.join(self.temp_dir, "valid.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name', 'aliases', 'level', 'theme_id'])
            writer.writerow([1, 'Test Unit Type', 'TUT', '[]', 1, None])
        
        errors = self.service.validate_file_structure(csv_file, FileFormat.CSV, 'unit_types')
        assert len(errors) == 0
    
    def test_validate_file_structure_csv_missing_entity_type(self):
        """Test CSV validation error when entity type is not specified."""
        csv_file = os.path.join(self.temp_dir, "test.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('id,name\n1,test\n')
        
        errors = self.service.validate_file_structure(csv_file, FileFormat.CSV)
        assert len(errors) == 1
        assert errors[0].error_type == ImportErrorType.FILE_FORMAT_ERROR
        assert "Entity type must be specified" in errors[0].message
    
    def test_validate_import_data_valid(self):
        """Test comprehensive data validation with valid data."""
        # Create valid import data
        valid_data = {
            'unit_types': [
                {
                    'id': 1,
                    'name': 'Test Unit Type',
                    'short_name': 'TUT',
                    'aliases': [],
                    'level': 1,
                    'theme_id': None
                }
            ],
            'persons': [
                {
                    'id': 1,
                    'name': 'John Doe',
                    'short_name': 'J.Doe',
                    'email': 'john@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'registration_no': 'EMP001',
                    'profile_image': None
                }
            ]
        }
        
        options = ImportOptions(
            entity_types=['unit_types', 'persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        result = self.service.validate_import_data(valid_data, options)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.validated_records == 2
    
    def test_validate_import_data_invalid(self):
        """Test comprehensive data validation with invalid data."""
        # Create invalid import data (missing required fields)
        invalid_data = {
            'unit_types': [
                {
                    'id': 1,
                    'short_name': 'TUT',
                    'level': 1
                    # Missing required 'name' field
                }
            ]
        }
        
        options = ImportOptions(
            entity_types=['unit_types'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        result = self.service.validate_import_data(invalid_data, options)
        
        assert isinstance(result, ValidationResult)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any(error.error_type == ImportErrorType.MISSING_REQUIRED_FIELD 
                  for error in result.errors)
    
    def test_create_transaction_context(self):
        """Test transaction context creation."""
        operation_id = "test_operation_123"
        
        context = self.service.create_transaction_context(operation_id)
        
        assert isinstance(context, TransactionContext)
        assert context.operation_id == operation_id
        assert context.is_active == True
        assert context.start_time > 0
        assert operation_id in self.service._transaction_contexts
    
    def test_commit_transaction(self):
        """Test transaction commit."""
        operation_id = "test_commit_123"
        
        # Create transaction context
        context = self.service.create_transaction_context(operation_id)
        assert context.is_active == True
        
        # Commit transaction
        self.service.commit_transaction(operation_id)
        
        # Verify transaction is no longer active and context is cleaned up
        assert operation_id not in self.service._transaction_contexts
    
    def test_commit_nonexistent_transaction(self):
        """Test error handling when committing non-existent transaction."""
        with pytest.raises(ImportExportException) as exc_info:
            self.service.commit_transaction("nonexistent_operation")
        
        assert "No active transaction" in str(exc_info.value)
    
    def test_rollback_transaction(self):
        """Test transaction rollback."""
        operation_id = "test_rollback_123"
        
        # Create transaction context
        context = self.service.create_transaction_context(operation_id)
        assert context.is_active == True
        
        # Rollback transaction
        self.service.rollback_transaction(operation_id)
        
        # Verify transaction is no longer active and context is cleaned up
        assert operation_id not in self.service._transaction_contexts
    
    def test_rollback_nonexistent_transaction(self):
        """Test rollback of non-existent transaction (should not raise error)."""
        # Should not raise an exception
        self.service.rollback_transaction("nonexistent_operation")
    
    def test_cleanup_transaction_contexts(self):
        """Test cleanup of all transaction contexts."""
        # Create multiple transaction contexts
        operation_ids = ["op1", "op2", "op3"]
        for op_id in operation_ids:
            self.service.create_transaction_context(op_id)
        
        assert len(self.service._transaction_contexts) == 3
        
        # Cleanup all contexts
        self.service.cleanup_transaction_contexts()
        
        # Verify all contexts are cleaned up
        assert len(self.service._transaction_contexts) == 0
    
    def test_get_transaction_status_existing(self):
        """Test getting status for existing transaction."""
        operation_id = "test_status_123"
        context = self.service.create_transaction_context(operation_id)
        
        status = self.service.get_transaction_status(operation_id)
        
        assert status["exists"] == True
        assert status["is_active"] == True
        assert status["operation_id"] == operation_id
        assert status["duration"] >= 0
    
    def test_get_transaction_status_nonexistent(self):
        """Test getting status for non-existent transaction."""
        status = self.service.get_transaction_status("nonexistent")
        
        assert status["exists"] == False
        assert status["is_active"] == False
        assert status["duration"] == 0.0
    
    def test_get_active_transactions(self):
        """Test getting list of active transactions."""
        # Initially no active transactions
        active = self.service.get_active_transactions()
        assert len(active) == 0
        
        # Create some transactions
        op1 = self.service.create_transaction_context("op1")
        op2 = self.service.create_transaction_context("op2")
        
        active = self.service.get_active_transactions()
        assert len(active) == 2
        assert "op1" in active
        assert "op2" in active
        
        # Commit one transaction
        self.service.commit_transaction("op1")
        
        active = self.service.get_active_transactions()
        assert len(active) == 1
        assert "op2" in active
    
    def test_get_supported_formats(self):
        """Test getting list of supported file formats."""
        formats = self.service.get_supported_formats()
        
        assert isinstance(formats, list)
        assert FileFormat.JSON in formats
        assert FileFormat.CSV in formats
    
    @patch('app.services.import_export.ImportExportService._parse_import_file')
    def test_preview_import_success(self, mock_parse):
        """Test successful import preview."""
        # Mock parsed data
        mock_data = {
            'unit_types': [
                {'id': 1, 'name': 'Test Unit', 'short_name': 'TU', 'level': 1}
            ]
        }
        mock_parse.return_value = mock_data
        
        # Create test file
        json_file = os.path.join(self.temp_dir, "preview_test.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f)
        
        options = ImportOptions(
            entity_types=['unit_types'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        result = self.service.preview_import(json_file, FileFormat.JSON, options)
        
        assert isinstance(result, PreviewResult)
        assert result.success == True
        assert result.preview_data == mock_data
        assert result.estimated_processing_time > 0
        assert len(result.dependency_order) > 0
    
    @patch('app.services.import_export.ImportExportService._parse_import_file')
    def test_preview_import_validation_errors(self, mock_parse):
        """Test import preview with validation errors."""
        # Mock parsed data with validation issues
        mock_data = {
            'unit_types': [
                {'id': 1, 'short_name': 'TU', 'level': 1}  # Missing required 'name'
            ]
        }
        mock_parse.return_value = mock_data
        
        # Create test file
        json_file = os.path.join(self.temp_dir, "preview_invalid.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f)
        
        options = ImportOptions(
            entity_types=['unit_types'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        result = self.service.preview_import(json_file, FileFormat.JSON, options)
        
        assert isinstance(result, PreviewResult)
        # Should still be successful for preview (warnings don't prevent preview)
        assert len(result.validation_results) > 0
        assert any(error.error_type == ImportErrorType.MISSING_REQUIRED_FIELD 
                  for error in result.validation_results)
    
    def test_preview_import_file_not_found(self):
        """Test import preview with non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        
        options = ImportOptions(
            entity_types=['unit_types'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        result = self.service.preview_import(nonexistent_file, FileFormat.JSON, options)
        
        assert isinstance(result, PreviewResult)
        assert result.success == False
        assert len(result.validation_results) > 0
        assert any(error.error_type == ImportErrorType.FILE_FORMAT_ERROR 
                  for error in result.validation_results)


class TestTransactionContext:
    """Test cases for TransactionContext dataclass."""
    
    def test_transaction_context_creation(self):
        """Test creating TransactionContext instances."""
        operation_id = "test_operation"
        
        context = TransactionContext(operation_id=operation_id)
        
        assert context.operation_id == operation_id
        assert context.is_active == True
        assert context.start_time > 0
    
    def test_transaction_context_with_start_time(self):
        """Test creating TransactionContext with explicit start time."""
        operation_id = "test_operation"
        start_time = 1234567890.0
        
        context = TransactionContext(
            operation_id=operation_id,
            is_active=False,
            start_time=start_time
        )
        
        assert context.operation_id == operation_id
        assert context.is_active == False
        assert context.start_time == start_time


if __name__ == '__main__':
    pytest.main([__file__])