"""
Tests for JSON processor functionality.

This module tests the JSON file parsing and generation capabilities
of the JSONProcessor class.
"""

import json
import os
import tempfile
import pytest
from datetime import date, datetime
from pathlib import Path

from app.services.json_processor import JSONProcessor, JSONParseResult
from app.models.import_export import ImportOptions, ExportOptions, ImportErrorType


class TestJSONProcessor:
    """Test cases for JSONProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = JSONProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_valid_json_file(self):
        """Test parsing a valid JSON file."""
        # Create test JSON data
        test_data = {
            "metadata": {
                "export_timestamp": "2024-01-15T10:30:00",
                "version": "1.0",
                "total_records": 2
            },
            "unit_types": [
                {
                    "id": 1,
                    "name": "Direzione Generale",
                    "short_name": "DG",
                    "aliases": [],
                    "level": 1,
                    "theme_id": 1
                }
            ],
            "persons": [
                {
                    "id": 1,
                    "name": "Mario Rossi",
                    "short_name": "M.Rossi",
                    "email": "mario.rossi@example.com",
                    "first_name": "Mario",
                    "last_name": "Rossi",
                    "registration_no": "EMP001",
                    "profile_image": None
                }
            ]
        }
        
        # Write test file
        test_file = os.path.join(self.temp_dir, "test_data.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Parse the file
        result = self.processor.parse_json_file(test_file)
        
        # Verify results
        assert result.success
        assert len(result.errors) == 0
        assert result.total_records == 2
        assert result.processed_records == 2
        assert "unit_types" in result.data
        assert "persons" in result.data
        assert len(result.data["unit_types"]) == 1
        assert len(result.data["persons"]) == 1
        assert result.metadata["version"] == "1.0"
    
    def test_parse_invalid_json_file(self):
        """Test parsing an invalid JSON file."""
        # Create invalid JSON file
        test_file = os.path.join(self.temp_dir, "invalid.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json}')  # Invalid JSON syntax
        
        # Parse the file
        result = self.processor.parse_json_file(test_file)
        
        # Verify results
        assert not result.success
        assert len(result.errors) > 0
        assert result.errors[0].error_type == ImportErrorType.FILE_FORMAT_ERROR
        assert "Invalid JSON format" in result.errors[0].message
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        
        # Parse the file
        result = self.processor.parse_json_file(nonexistent_file)
        
        # Verify results
        assert not result.success
        assert len(result.errors) > 0
        assert result.errors[0].error_type == ImportErrorType.FILE_FORMAT_ERROR
        assert "File not found" in result.errors[0].message
    
    def test_generate_json_file(self):
        """Test generating a JSON file."""
        # Prepare test data
        test_data = {
            "unit_types": [
                {
                    "id": 1,
                    "name": "Direzione Generale",
                    "short_name": "DG",
                    "aliases": [],
                    "level": 1,
                    "theme_id": 1
                }
            ],
            "persons": [
                {
                    "id": 1,
                    "name": "Mario Rossi",
                    "short_name": "M.Rossi",
                    "email": "mario.rossi@example.com",
                    "first_name": "Mario",
                    "last_name": "Rossi",
                    "registration_no": "EMP001",
                    "profile_image": None
                }
            ]
        }
        
        # Generate JSON file
        output_file = os.path.join(self.temp_dir, "output.json")
        success = self.processor.generate_json_file(test_data, output_file, include_metadata=True)
        
        # Verify file was created
        assert success
        assert os.path.exists(output_file)
        
        # Verify file contents
        with open(output_file, 'r', encoding='utf-8') as f:
            generated_data = json.load(f)
        
        assert "metadata" in generated_data
        assert "unit_types" in generated_data
        assert "persons" in generated_data
        assert len(generated_data["unit_types"]) == 1
        assert len(generated_data["persons"]) == 1
        assert generated_data["metadata"]["total_records"] == 2
    
    def test_export_to_json_with_options(self):
        """Test exporting data to JSON with export options."""
        # Prepare test data
        test_data = {
            "unit_types": [
                {
                    "id": 1,
                    "name": "Direzione Generale",
                    "short_name": "DG",
                    "aliases": [],
                    "level": 1,
                    "theme_id": 1
                }
            ],
            "persons": [
                {
                    "id": 1,
                    "name": "Mario Rossi",
                    "short_name": "M.Rossi",
                    "email": "mario.rossi@example.com",
                    "first_name": "Mario",
                    "last_name": "Rossi",
                    "registration_no": "EMP001",
                    "profile_image": None
                }
            ]
        }
        
        # Create export options
        export_options = ExportOptions(
            entity_types=["unit_types", "persons"],
            output_directory=self.temp_dir,
            file_prefix="test_export",
            include_metadata=True,
            json_indent=4
        )
        
        # Export data
        generated_files = self.processor.export_to_json(test_data, export_options)
        
        # Verify results
        assert len(generated_files) == 1
        assert os.path.exists(generated_files[0])
        assert "test_export" in generated_files[0]
        assert generated_files[0].endswith(".json")
        
        # Verify file contents
        with open(generated_files[0], 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        assert "metadata" in exported_data
        assert "unit_types" in exported_data
        assert "persons" in exported_data
    
    def test_validate_json_structure(self):
        """Test JSON structure validation."""
        # Create valid JSON file
        test_data = {
            "unit_types": [
                {"id": 1, "name": "Test Unit", "short_name": "TU"}
            ]
        }
        
        test_file = os.path.join(self.temp_dir, "valid.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Validate structure
        errors = self.processor.validate_json_structure(test_file)
        
        # Should have no errors
        assert len(errors) == 0
    
    def test_validate_invalid_json_structure(self):
        """Test validation of invalid JSON structure."""
        # Create JSON with invalid structure (entity as non-list)
        test_data = {
            "unit_types": {"id": 1, "name": "Test Unit"}  # Should be a list
        }
        
        test_file = os.path.join(self.temp_dir, "invalid_structure.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Validate structure
        errors = self.processor.validate_json_structure(test_file)
        
        # Should have errors
        assert len(errors) > 0
        assert any("must be a list" in error.message for error in errors)
    
    def test_date_serialization(self):
        """Test proper date/datetime serialization."""
        # Prepare test data with dates
        test_data = {
            "units": [
                {
                    "id": 1,
                    "name": "Test Unit",
                    "short_name": "TU",
                    "start_date": date(2024, 1, 1),
                    "end_date": None
                }
            ]
        }
        
        # Generate JSON file
        output_file = os.path.join(self.temp_dir, "dates.json")
        success = self.processor.generate_json_file(test_data, output_file, include_metadata=False)
        
        # Verify file was created
        assert success
        
        # Verify date serialization
        with open(output_file, 'r', encoding='utf-8') as f:
            generated_data = json.load(f)
        
        assert generated_data["units"][0]["start_date"] == "2024-01-01"
    
    def test_get_export_statistics(self):
        """Test export statistics calculation."""
        test_data = {
            "unit_types": [{"id": 1}, {"id": 2}],
            "persons": [{"id": 1}],
            "units": []
        }
        
        stats = self.processor.get_export_statistics(test_data)
        
        assert stats["total_records"] == 3
        assert stats["entity_counts"]["unit_types"] == 2
        assert stats["entity_counts"]["persons"] == 1
        assert stats["entity_counts"]["units"] == 0
        assert "units" in stats["empty_entities"]
        assert stats["format"] == "json"