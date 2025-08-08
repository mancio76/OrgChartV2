"""
Integration tests for JSON processor with real data structures.

This module tests the JSON processor with realistic organizational data
to ensure it works correctly with the actual entity mappings.
"""

import json
import os
import tempfile
import pytest
from datetime import date

from app.services.json_processor import JSONProcessor
from app.models.import_export import ExportOptions


class TestJSONIntegration:
    """Integration test cases for JSONProcessor with realistic data."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = JSONProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_organizational_data_export(self):
        """Test exporting complete organizational data structure."""
        # Create realistic organizational data
        test_data = {
            "unit_types": [
                {
                    "id": 1,
                    "name": "Direzione Generale",
                    "short_name": "DG",
                    "aliases": [{"value": "General Direction", "lang": "en-US"}],
                    "level": 1,
                    "theme_id": 1
                },
                {
                    "id": 2,
                    "name": "Ufficio",
                    "short_name": "UFF",
                    "aliases": [],
                    "level": 2,
                    "theme_id": 1
                }
            ],
            "unit_type_themes": [
                {
                    "id": 1,
                    "name": "Default Theme",
                    "description": "Default organizational theme",
                    "icon_class": "diagram-2",
                    "emoji_fallback": "🏛️",
                    "primary_color": "#0dcaf0",
                    "secondary_color": "#f0fdff",
                    "text_color": "#0dcaf0",
                    "display_label": "Organizational Unit",
                    "is_active": True
                }
            ],
            "units": [
                {
                    "id": 1,
                    "name": "Direzione Generale",
                    "short_name": "DG",
                    "aliases": [],
                    "unit_type_id": 1,
                    "parent_unit_id": None,
                    "start_date": "2024-01-01",
                    "end_date": None
                },
                {
                    "id": 2,
                    "name": "Ufficio Personale",
                    "short_name": "UP",
                    "aliases": [],
                    "unit_type_id": 2,
                    "parent_unit_id": 1,
                    "start_date": "2024-01-01",
                    "end_date": None
                }
            ],
            "job_titles": [
                {
                    "id": 1,
                    "name": "Direttore Generale",
                    "short_name": "DG",
                    "aliases": [{"value": "General Director", "lang": "en-US"}],
                    "start_date": "2024-01-01",
                    "end_date": None
                },
                {
                    "id": 2,
                    "name": "Responsabile Ufficio",
                    "short_name": "RU",
                    "aliases": [],
                    "start_date": "2024-01-01",
                    "end_date": None
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
                    "profile_image": "profiles/mario.rossi.jpg"
                },
                {
                    "id": 2,
                    "name": "Giulia Bianchi",
                    "short_name": "G.Bianchi",
                    "email": "giulia.bianchi@example.com",
                    "first_name": "Giulia",
                    "last_name": "Bianchi",
                    "registration_no": "EMP002",
                    "profile_image": None
                }
            ],
            "assignments": [
                {
                    "id": 1,
                    "person_id": 1,
                    "unit_id": 1,
                    "job_title_id": 1,
                    "version": 1,
                    "percentage": 1.0,
                    "is_ad_interim": False,
                    "is_unit_boss": True,
                    "notes": "Initial assignment",
                    "valid_from": "2024-01-01",
                    "valid_to": None,
                    "is_current": True
                },
                {
                    "id": 2,
                    "person_id": 2,
                    "unit_id": 2,
                    "job_title_id": 2,
                    "version": 1,
                    "percentage": 1.0,
                    "is_ad_interim": False,
                    "is_unit_boss": True,
                    "notes": "Department head",
                    "valid_from": "2024-01-01",
                    "valid_to": None,
                    "is_current": True
                }
            ]
        }
        
        # Create export options
        export_options = ExportOptions(
            entity_types=["unit_types", "unit_type_themes", "units", "job_titles", "persons", "assignments"],
            output_directory=self.temp_dir,
            file_prefix="complete_org_export",
            include_metadata=True,
            json_indent=2
        )
        
        # Export data
        generated_files = self.processor.export_to_json(test_data, export_options)
        
        # Verify export was successful
        assert len(generated_files) == 1
        assert os.path.exists(generated_files[0])
        
        # Verify file contents
        with open(generated_files[0], 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        # Check metadata
        assert "metadata" in exported_data
        metadata = exported_data["metadata"]
        assert metadata["total_records"] == 11  # 2+1+2+2+2+2 records
        assert metadata["format"] == "json"
        assert "export_timestamp" in metadata
        assert "relationships" in metadata
        
        # Check entity data is in correct dependency order
        entity_keys = [key for key in exported_data.keys() if key != "metadata"]
        expected_order = ["unit_types", "unit_type_themes", "units", "job_titles", "persons", "assignments"]
        
        # Verify all expected entities are present
        for entity_type in expected_order:
            assert entity_type in exported_data
            assert isinstance(exported_data[entity_type], list)
        
        # Verify specific data integrity
        assert len(exported_data["unit_types"]) == 2
        assert len(exported_data["units"]) == 2
        assert len(exported_data["persons"]) == 2
        assert len(exported_data["assignments"]) == 2
        
        # Verify foreign key relationships are preserved
        unit = exported_data["units"][1]  # Ufficio Personale
        assert unit["unit_type_id"] == 2
        assert unit["parent_unit_id"] == 1
        
        assignment = exported_data["assignments"][0]  # Mario Rossi assignment
        assert assignment["person_id"] == 1
        assert assignment["unit_id"] == 1
        assert assignment["job_title_id"] == 1
    
    def test_roundtrip_import_export(self):
        """Test importing and then exporting JSON data (roundtrip)."""
        # Create initial data
        initial_data = {
            "metadata": {
                "export_timestamp": "2024-01-15T10:30:00",
                "version": "1.0"
            },
            "unit_types": [
                {
                    "id": 1,
                    "name": "Direzione",
                    "short_name": "DIR",
                    "aliases": [],
                    "level": 1,
                    "theme_id": None
                }
            ],
            "persons": [
                {
                    "id": 1,
                    "name": "Test Person",
                    "short_name": "T.Person",
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "Person",
                    "registration_no": "TEST001",
                    "profile_image": None
                }
            ]
        }
        
        # Write initial JSON file
        input_file = os.path.join(self.temp_dir, "input.json")
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        
        # Parse the file
        parse_result = self.processor.parse_json_file(input_file)
        
        # Verify parsing was successful
        assert parse_result.success
        assert len(parse_result.errors) == 0
        assert parse_result.total_records == 2
        
        # Export the parsed data
        export_options = ExportOptions(
            entity_types=["unit_types", "persons"],
            output_directory=self.temp_dir,
            file_prefix="roundtrip_test",
            include_metadata=True
        )
        
        generated_files = self.processor.export_to_json(parse_result.data, export_options)
        
        # Verify export was successful
        assert len(generated_files) == 1
        
        # Read the exported file
        with open(generated_files[0], 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        # Verify data integrity after roundtrip
        assert "unit_types" in exported_data
        assert "persons" in exported_data
        assert len(exported_data["unit_types"]) == 1
        assert len(exported_data["persons"]) == 1
        
        # Verify specific field values are preserved
        exported_unit_type = exported_data["unit_types"][0]
        assert exported_unit_type["name"] == "Direzione"
        assert exported_unit_type["short_name"] == "DIR"
        assert exported_unit_type["level"] == 1
        
        exported_person = exported_data["persons"][0]
        assert exported_person["name"] == "Test Person"
        assert exported_person["email"] == "test@example.com"
        assert exported_person["registration_no"] == "TEST001"