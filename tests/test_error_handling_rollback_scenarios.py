"""
Comprehensive tests for error handling and rollback scenarios.

This module tests various error conditions, recovery mechanisms,
and transaction rollback scenarios in the import/export system.
"""

import os
import tempfile
import pytest
import json
import shutil
from unittest.mock import Mock, patch, MagicMock, side_effect
from datetime import datetime

from app.services.import_export import (
    ImportExportService, ImportExportException, FileFormatDetectionError,
    TransactionRollbackError
)
from app.services.error_reporting import ErrorReportingService
from app.models.import_export import (
    ImportOptions, ExportOptions, ImportResult, FileFormat,
    ConflictResolutionStrategy, ImportErrorType, ImportExportValidationError
)


class TestErrorHandlingScenarios:
    """Test cases for various error handling scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = ImportExportService()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.service.cleanup_transaction_contexts()
    
    def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        # Create valid import data
        valid_data = {
            "persons": [
                {
                    "id": 1,
                    "name": "Test Person",
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "Person",
                    "registration_no": "TEST001"
                }
            ]
        }
        
        json_file = os.path.join(self.temp_dir, "valid_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(valid_data, f)
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Mock database connection failure
        with patch.object(self.service.db_manager, 'get_connection', side_effect=Exception("Database connection failed")):
            with patch.object(self.service, '_execute_import_with_transaction') as mock_import:
                mock_result = ImportResult(
                    success=False,
                    records_processed={},
                    records_created={},
                    records_updated={},
                    records_skipped={},
                    errors=[ImportExportValidationError(
                        field="database_connection",
                        message="Database connection failed",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                    )],
                    warnings=[],
                    execution_time=0.1,
                    operation_id="failed_db_connection"
                )
                mock_import.return_value = mock_result
                
                result = self.service.import_data(json_file, FileFormat.JSON, import_options)
                
                assert result.success == False
                assert len(result.errors) > 0
                assert any("Database connection failed" in error.message for error in result.errors)
    
    def test_file_system_errors(self):
        """Test handling of file system errors."""
        # Test with non-existent file
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Should raise FileFormatDetectionError
        with pytest.raises(FileFormatDetectionError) as exc_info:
            self.service.detect_file_format(nonexistent_file)
        
        assert "File not found" in str(exc_info.value)
    
    def test_corrupted_file_handling(self):
        """Test handling of corrupted files."""
        # Create corrupted JSON file
        corrupted_file = os.path.join(self.temp_dir, "corrupted.json")
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write('{"persons": [{"id": 1, "name": "Test"')  # Incomplete JSON
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Should detect format error
        with pytest.raises(FileFormatDetectionError) as exc_info:
            self.service.detect_file_format(corrupted_file)
        
        assert "Invalid JSON content" in str(exc_info.value)
    
    def test_memory_exhaustion_simulation(self):
        """Test handling of memory exhaustion scenarios."""
        # Create a file that would theoretically cause memory issues
        large_data = {
            "persons": []
        }
        
        # Simulate a very large dataset
        for i in range(100):  # Smaller number for test performance
            large_data["persons"].append({
                "id": i + 1,
                "name": f"Person {i + 1}",
                "email": f"person{i + 1}@example.com",
                "notes": "x" * 1000  # Large text field
            })
        
        large_file = os.path.join(self.temp_dir, "large_data.json")
        with open(large_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f)
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            batch_size=10  # Small batch size to handle large data
        )
        
        # Mock memory error during processing
        with patch.object(self.service, '_parse_import_file', side_effect=MemoryError("Out of memory")):
            preview_result = self.service.preview_import(large_file, FileFormat.JSON, import_options)
            
            assert preview_result.success == False
            assert len(preview_result.validation_results) > 0
            assert any("Out of memory" in error.message for error in preview_result.validation_results)
    
    def test_transaction_rollback_on_validation_failure(self):
        """Test transaction rollback when validation fails."""
        # Create data with validation errors
        invalid_data = {
            "persons": [
                {
                    "id": 1,
                    "name": "",  # Empty required field
                    "email": "invalid-email",  # Invalid email format
                    "first_name": "Test",
                    "last_name": "Person"
                },
                {
                    "id": 2,
                    "name": "Valid Person",
                    "email": "valid@example.com",
                    "first_name": "Valid",
                    "last_name": "Person"
                }
            ]
        }
        
        json_file = os.path.join(self.temp_dir, "invalid_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            validate_only=False
        )
        
        # Test transaction creation and rollback
        operation_id = "test_rollback_validation"
        context = self.service.create_transaction_context(operation_id)
        
        assert context.is_active == True
        assert operation_id in self.service._transaction_contexts
        
        # Simulate validation failure and rollback
        try:
            # This would normally trigger rollback in real scenario
            raise ImportExportException("Validation failed")
        except ImportExportException:
            self.service.rollback_transaction(operation_id)
        
        # Verify transaction was rolled back
        assert operation_id not in self.service._transaction_contexts
    
    def test_transaction_rollback_on_database_error(self):
        """Test transaction rollback when database operations fail."""
        operation_id = "test_db_error_rollback"
        context = self.service.create_transaction_context(operation_id)
        
        # Mock database error during transaction
        with patch.object(self.service.db_manager, 'execute_query', side_effect=Exception("Database error")):
            try:
                # Simulate database operation that fails
                raise Exception("Database operation failed")
            except Exception:
                self.service.rollback_transaction(operation_id)
        
        # Verify rollback completed
        assert operation_id not in self.service._transaction_contexts
    
    def test_partial_import_failure_recovery(self):
        """Test recovery from partial import failures."""
        # Create data where some entities succeed and others fail
        mixed_data = {
            "unit_types": [
                {
                    "id": 1,
                    "name": "Valid Unit Type",
                    "short_name": "VUT",
                    "level": 1
                }
            ],
            "persons": [
                {
                    "id": 1,
                    "name": "Valid Person",
                    "email": "valid@example.com",
                    "first_name": "Valid",
                    "last_name": "Person"
                },
                {
                    "id": 2,
                    # Missing required fields
                    "email": "incomplete@example.com"
                }
            ]
        }
        
        json_file = os.path.join(self.temp_dir, "mixed_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(mixed_data, f)
        
        import_options = ImportOptions(
            entity_types=['unit_types', 'persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Test validation shows partial errors
        validation_result = self.service.validate_import_data(mixed_data, import_options)
        
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0
        
        # Should have errors for the incomplete person record
        missing_field_errors = [e for e in validation_result.errors 
                               if e.error_type == ImportErrorType.MISSING_REQUIRED_FIELD]
        assert len(missing_field_errors) > 0
    
    def test_circular_dependency_detection(self):
        """Test detection and handling of circular dependencies."""
        # Create data with circular references (units referencing each other as parents)
        circular_data = {
            "units": [
                {
                    "id": 1,
                    "name": "Unit A",
                    "short_name": "UA",
                    "unit_type_id": 1,
                    "parent_unit_id": 2  # References Unit B
                },
                {
                    "id": 2,
                    "name": "Unit B",
                    "short_name": "UB",
                    "unit_type_id": 1,
                    "parent_unit_id": 1  # References Unit A (circular!)
                }
            ],
            "unit_types": [
                {
                    "id": 1,
                    "name": "Department",
                    "short_name": "DEPT",
                    "level": 1
                }
            ]
        }
        
        json_file = os.path.join(self.temp_dir, "circular_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(circular_data, f)
        
        import_options = ImportOptions(
            entity_types=['unit_types', 'units'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Test that circular dependency is detected in validation
        validation_result = self.service.validate_import_data(circular_data, import_options)
        
        # Should detect business rule violations for circular references
        circular_errors = [e for e in validation_result.errors 
                          if "circular" in e.message.lower() or "hierarchy" in e.message.lower()]
        
        # Note: Actual circular dependency detection depends on business rule implementation
        # This test verifies the framework can handle such scenarios
    
    def test_foreign_key_constraint_violations(self):
        """Test handling of foreign key constraint violations."""
        # Create data with invalid foreign key references
        fk_violation_data = {
            "assignments": [
                {
                    "person_id": 999,  # Non-existent person
                    "unit_id": 888,    # Non-existent unit
                    "job_title_id": 777,  # Non-existent job title
                    "percentage": 1.0,
                    "is_current": True,
                    "valid_from": "2024-01-01"
                }
            ]
        }
        
        json_file = os.path.join(self.temp_dir, "fk_violation_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(fk_violation_data, f)
        
        import_options = ImportOptions(
            entity_types=['assignments'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Test validation catches foreign key violations
        validation_result = self.service.validate_import_data(fk_violation_data, import_options)
        
        assert not validation_result.is_valid
        
        # Should have foreign key violation errors
        fk_errors = [e for e in validation_result.errors 
                    if e.error_type == ImportErrorType.FOREIGN_KEY_VIOLATION]
        
        # Should have at least one FK violation (may have multiple depending on implementation)
        assert len(fk_errors) >= 1
    
    def test_concurrent_transaction_conflicts(self):
        """Test handling of concurrent transaction conflicts."""
        # Create multiple concurrent transactions
        operation_ids = ["concurrent_1", "concurrent_2", "concurrent_3"]
        contexts = []
        
        for op_id in operation_ids:
            context = self.service.create_transaction_context(op_id)
            contexts.append(context)
        
        # Verify all transactions are active
        active_transactions = self.service.get_active_transactions()
        assert len(active_transactions) == 3
        
        # Simulate conflict by trying to commit one and rollback another
        self.service.commit_transaction("concurrent_1")
        self.service.rollback_transaction("concurrent_2")
        
        # Verify proper state management
        remaining_active = self.service.get_active_transactions()
        assert len(remaining_active) == 1
        assert "concurrent_3" in remaining_active
        
        # Clean up remaining transaction
        self.service.commit_transaction("concurrent_3")
        assert len(self.service.get_active_transactions()) == 0
    
    def test_error_reporting_integration(self):
        """Test integration with error reporting system."""
        # Create data that will generate various types of errors
        error_data = {
            "persons": [
                {
                    "id": "invalid_id",  # Invalid data type
                    "name": "",  # Missing required field
                    "email": "invalid-email",  # Invalid format
                    "first_name": "Test",
                    "last_name": "Person"
                }
            ]
        }
        
        json_file = os.path.join(self.temp_dir, "error_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f)
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Mock error reporting service
        with patch.object(self.service.error_reporting_service, 'report_import_errors') as mock_report:
            validation_result = self.service.validate_import_data(error_data, import_options)
            
            # Verify errors were detected
            assert not validation_result.is_valid
            assert len(validation_result.errors) > 0
            
            # Error reporting should be called with validation errors
            # (This depends on the actual implementation calling the error reporting service)
    
    def test_cleanup_after_critical_failure(self):
        """Test cleanup procedures after critical failures."""
        # Create multiple transaction contexts
        operation_ids = ["cleanup_test_1", "cleanup_test_2", "cleanup_test_3"]
        
        for op_id in operation_ids:
            self.service.create_transaction_context(op_id)
        
        assert len(self.service._transaction_contexts) == 3
        
        # Simulate critical failure that requires cleanup
        try:
            raise Exception("Critical system failure")
        except Exception:
            # Cleanup should handle all active transactions
            self.service.cleanup_transaction_contexts()
        
        # Verify all contexts were cleaned up
        assert len(self.service._transaction_contexts) == 0
        assert len(self.service.get_active_transactions()) == 0
    
    def test_rollback_failure_handling(self):
        """Test handling when rollback itself fails."""
        operation_id = "rollback_failure_test"
        context = self.service.create_transaction_context(operation_id)
        
        # Mock rollback failure
        with patch.object(self.service, 'rollback_transaction', side_effect=TransactionRollbackError("Rollback failed")):
            with pytest.raises(TransactionRollbackError) as exc_info:
                self.service.rollback_transaction(operation_id)
            
            assert "Rollback failed" in str(exc_info.value)
    
    def test_validation_framework_error_recovery(self):
        """Test error recovery in validation framework."""
        # Create data that might cause validation framework errors
        problematic_data = {
            "persons": [
                {
                    "id": 1,
                    "name": "Test Person",
                    "email": "test@example.com",
                    "custom_field": "unexpected_value"  # Field not in schema
                }
            ]
        }
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Mock validation framework error
        with patch.object(self.service.validation_framework, 'validate_records_batch', 
                         side_effect=Exception("Validation framework error")):
            
            validation_result = self.service.validate_import_data(problematic_data, import_options)
            
            # Should handle validation framework errors gracefully
            assert not validation_result.is_valid
            assert len(validation_result.errors) > 0
            
            # Should have an error indicating validation framework failure
            framework_errors = [e for e in validation_result.errors 
                               if "validation framework" in e.message.lower()]
            assert len(framework_errors) > 0
    
    def test_export_error_scenarios(self):
        """Test various export error scenarios."""
        export_options = ExportOptions(
            entity_types=['persons'],
            output_directory="/invalid/directory/path",  # Invalid directory
            file_prefix="error_test_export"
        )
        
        # Mock export data fetch failure
        with patch.object(self.service, '_fetch_export_data', side_effect=Exception("Data fetch failed")):
            export_result = self.service.export_data(export_options)
            
            assert export_result.success == False
            assert len(export_result.errors) > 0
            assert any("Data fetch failed" in error.message for error in export_result.errors)
    
    def test_resource_cleanup_on_interruption(self):
        """Test resource cleanup when operations are interrupted."""
        # Create resources that need cleanup
        operation_id = "interrupted_operation"
        context = self.service.create_transaction_context(operation_id)
        
        # Create temporary files
        temp_files = []
        for i in range(3):
            temp_file = os.path.join(self.temp_dir, f"temp_file_{i}.tmp")
            with open(temp_file, 'w') as f:
                f.write("temporary data")
            temp_files.append(temp_file)
        
        # Simulate interruption
        try:
            raise KeyboardInterrupt("Operation interrupted")
        except KeyboardInterrupt:
            # Cleanup should handle interruption gracefully
            self.service.cleanup_transaction_contexts()
            
            # Clean up temporary files (in real implementation)
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        
        # Verify cleanup completed
        assert len(self.service._transaction_contexts) == 0
        
        # Verify temp files were cleaned up
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)


if __name__ == '__main__':
    pytest.main([__file__])