"""
Tests for import preview functionality.

This module tests the preview system implementation that allows users to
preview import data without persisting changes to the database.
"""

import pytest
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.import_export import ImportExportService
from app.models.import_export import (
    ImportOptions, PreviewResult, FileFormat, ConflictResolutionStrategy,
    ImportExportValidationError, ImportErrorType
)


class TestImportPreview:
    """Test cases for import preview functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ImportExportService()
    
    def test_preview_import_json_success(self):
        """Test successful JSON import preview."""
        # Create test JSON data
        test_data = {
            "unit_types": [
                {
                    "id": 1,
                    "name": "Test Unit Type",
                    "short_name": "TUT",
                    "aliases": [],
                    "level": 1,
                    "theme_id": 1
                }
            ],
            "units": [
                {
                    "id": 1,
                    "name": "Test Unit",
                    "short_name": "TU",
                    "aliases": [],
                    "unit_type_id": 1,
                    "parent_unit_id": None,
                    "start_date": "2024-01-01",
                    "end_date": None
                }
            ]
        }
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            # Create import options
            options = ImportOptions(
                entity_types=['unit_types', 'units'],
                conflict_resolution=ConflictResolutionStrategy.SKIP
            )
            
            # Mock the validation framework and other dependencies
            with patch.object(self.service.validation_framework, 'validate_records_batch') as mock_validate, \
                 patch.object(self.service.dependency_resolver, 'get_processing_order') as mock_order, \
                 patch.object(self.service.conflict_resolution_manager.detector, '_get_existing_records') as mock_existing:
                
                mock_validate.return_value = []
                mock_order.return_value = ['unit_types', 'units']
                mock_existing.return_value = []
                
                # Test preview
                result = self.service.preview_import(temp_file, FileFormat.JSON, options)
                
                # Assertions
                assert result.success is True
                assert result.total_records == 2
                assert 'unit_types' in result.preview_data
                assert 'units' in result.preview_data
                assert len(result.preview_data['unit_types']) == 1
                assert len(result.preview_data['units']) == 1
                assert result.dependency_order == ['unit_types', 'units']
                assert result.estimated_processing_time > 0
        
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_preview_import_csv_success(self):
        """Test successful CSV import preview."""
        # Create test CSV data
        csv_data = [
            ['id', 'name', 'short_name', 'aliases', 'level', 'theme_id'],
            ['1', 'Test Unit Type', 'TUT', '[]', '1', '1'],
            ['2', 'Another Unit Type', 'AUT', '[]', '2', '1']
        ]
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            temp_file = f.name
        
        try:
            # Create import options
            options = ImportOptions(
                entity_types=['unit_types'],
                conflict_resolution=ConflictResolutionStrategy.SKIP
            )
            
            # Mock dependencies
            with patch.object(self.service.validation_framework, 'validate_records_batch') as mock_validate, \
                 patch.object(self.service.dependency_resolver, 'get_processing_order') as mock_order, \
                 patch.object(self.service.conflict_resolution_manager.detector, '_get_existing_records') as mock_existing:
                
                mock_validate.return_value = []
                mock_order.return_value = ['unit_types']
                mock_existing.return_value = []
                
                # Test preview
                result = self.service.preview_import(temp_file, FileFormat.CSV, options)
                
                # Assertions
                assert result.success is True
                assert result.total_records == 2
                assert 'unit_types' in result.preview_data
                assert len(result.preview_data['unit_types']) == 2
                assert result.dependency_order == ['unit_types']
        
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_preview_import_validation_errors(self):
        """Test preview with validation errors."""
        # Create test JSON data with validation errors
        test_data = {
            "unit_types": [
                {
                    "id": 1,
                    "name": "",  # Missing required field
                    "short_name": "TUT",
                    "aliases": [],
                    "level": 1,  # Valid data type but will be flagged by validation
                    "theme_id": 999  # Foreign key violation
                }
            ]
        }
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            # Create import options
            options = ImportOptions(
                entity_types=['unit_types'],
                conflict_resolution=ConflictResolutionStrategy.SKIP
            )
            
            # Mock validation to return errors
            validation_errors = [
                ImportExportValidationError(
                    field="name",
                    message="Name is required",
                    error_type=ImportErrorType.MISSING_REQUIRED_FIELD,
                    entity_type="unit_types",
                    line_number=1
                ),
                ImportExportValidationError(
                    field="name",
                    message="Name cannot be empty",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                    entity_type="unit_types",
                    line_number=1
                ),
                ImportExportValidationError(
                    field="theme_id",
                    message="Referenced theme does not exist",
                    error_type=ImportErrorType.FOREIGN_KEY_VIOLATION,
                    entity_type="unit_types",
                    line_number=1
                )
            ]
            
            with patch.object(self.service.validation_framework, 'validate_records_batch') as mock_validate, \
                 patch.object(self.service.dependency_resolver, 'get_processing_order') as mock_order, \
                 patch.object(self.service.conflict_resolution_manager.detector, '_get_existing_records') as mock_existing:
                
                mock_validate.return_value = validation_errors
                mock_order.return_value = ['unit_types']
                mock_existing.return_value = []
                
                # Test preview
                result = self.service.preview_import(temp_file, FileFormat.JSON, options)
                
                # Assertions
                assert result.success is True  # Preview succeeds even with validation errors
                assert len(result.validation_results) >= 3  # At least the mocked errors
                assert result.total_records == 1
                assert 'unit_types' in result.preview_data
                
                # Check that our mocked errors are present
                error_messages = [error.message for error in result.validation_results]
                assert "Name is required" in error_messages
                assert "Referenced theme does not exist" in error_messages
                assert "Name cannot be empty" in error_messages
        
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_preview_import_file_format_error(self):
        """Test preview with file format errors."""
        # Create invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            temp_file = f.name
        
        try:
            # Create import options
            options = ImportOptions(
                entity_types=['unit_types'],
                conflict_resolution=ConflictResolutionStrategy.SKIP
            )
            
            # Test preview
            result = self.service.preview_import(temp_file, FileFormat.JSON, options)
            
            # Assertions
            assert result.success is False
            assert len(result.validation_results) > 0
            assert any(error.error_type == ImportErrorType.FILE_FORMAT_ERROR 
                      for error in result.validation_results)
        
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_preview_import_foreign_key_mappings(self):
        """Test foreign key relationship analysis in preview."""
        # Create test data with foreign key relationships
        test_data = {
            "unit_types": [
                {"id": 1, "name": "Type 1", "short_name": "T1", "aliases": [], "level": 1, "theme_id": 1}
            ],
            "units": [
                {"id": 1, "name": "Unit 1", "short_name": "U1", "aliases": [], "unit_type_id": 1, "parent_unit_id": None, "start_date": "2024-01-01", "end_date": None},
                {"id": 2, "name": "Unit 2", "short_name": "U2", "aliases": [], "unit_type_id": 999, "parent_unit_id": 1, "start_date": "2024-01-01", "end_date": None}  # Invalid foreign key
            ]
        }
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            # Create import options
            options = ImportOptions(
                entity_types=['unit_types', 'units'],
                conflict_resolution=ConflictResolutionStrategy.SKIP
            )
            
            # Mock dependencies
            with patch.object(self.service.validation_framework, 'validate_records_batch') as mock_validate, \
                 patch.object(self.service.dependency_resolver, 'get_processing_order') as mock_order, \
                 patch.object(self.service.conflict_resolution_manager.detector, '_get_existing_records') as mock_existing, \
                 patch('app.models.entity_mappings.get_entity_mapping') as mock_mapping:
                
                mock_validate.return_value = []
                mock_order.return_value = ['unit_types', 'units']
                mock_existing.return_value = []
                
                # Mock entity mapping for units
                mock_entity_mapping = Mock()
                mock_entity_mapping.foreign_keys = {'unit_type_id': 'unit_types', 'parent_unit_id': 'units'}
                mock_mapping.return_value = mock_entity_mapping
                
                # Test preview
                result = self.service.preview_import(temp_file, FileFormat.JSON, options)
                
                # Assertions
                assert result.success is True
                assert 'units' in result.foreign_key_mappings
                
                units_fk_analysis = result.foreign_key_mappings['units']
                assert units_fk_analysis['total_records'] == 2
                assert 'unit_type_id' in units_fk_analysis['relationships']
                assert 'parent_unit_id' in units_fk_analysis['relationships']
        
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_preview_import_processing_time_estimation(self):
        """Test processing time estimation."""
        # Create test data with varying complexity
        test_data = {
            "unit_types": [{"id": i, "name": f"Type {i}", "short_name": f"T{i}", "aliases": [], "level": 1, "theme_id": 1} for i in range(1, 101)],
            "units": [{"id": i, "name": f"Unit {i}", "short_name": f"U{i}", "aliases": [], "unit_type_id": 1, "parent_unit_id": None, "start_date": "2024-01-01", "end_date": None} for i in range(1, 201)]
        }
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            # Test with different options
            options_simple = ImportOptions(
                entity_types=['unit_types', 'units'],
                conflict_resolution=ConflictResolutionStrategy.SKIP,
                skip_validation=True
            )
            
            options_complex = ImportOptions(
                entity_types=['unit_types', 'units'],
                conflict_resolution=ConflictResolutionStrategy.UPDATE,
                skip_validation=False
            )
            
            # Mock dependencies
            with patch.object(self.service.validation_framework, 'validate_records_batch') as mock_validate, \
                 patch.object(self.service.dependency_resolver, 'get_processing_order') as mock_order, \
                 patch.object(self.service.conflict_resolution_manager.detector, '_get_existing_records') as mock_existing:
                
                mock_validate.return_value = []
                mock_order.return_value = ['unit_types', 'units']
                mock_existing.return_value = []
                
                # Test simple options
                result_simple = self.service.preview_import(temp_file, FileFormat.JSON, options_simple)
                
                # Test complex options
                result_complex = self.service.preview_import(temp_file, FileFormat.JSON, options_complex)
                
                # Assertions
                assert result_simple.success is True
                assert result_complex.success is True
                assert result_simple.estimated_processing_time > 0
                assert result_complex.estimated_processing_time > 0
                # Complex options should take longer
                assert result_complex.estimated_processing_time > result_simple.estimated_processing_time
        
        finally:
            # Clean up
            Path(temp_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__])