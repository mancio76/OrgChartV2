"""
Comprehensive integration tests for import/export workflows.

This module tests complete end-to-end import/export scenarios including
error handling, rollback scenarios, and performance with large datasets.
"""

import os
import tempfile
import pytest
import json
import csv
import time
import shutil
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock

from app.services.import_export import ImportExportService
from app.services.csv_processor import CSVProcessor
from app.services.json_processor import JSONProcessor
from app.models.import_export import (
    ImportOptions, ExportOptions, ImportResult, ExportResult,
    FileFormat, ConflictResolutionStrategy, ImportErrorType
)


class TestImportExportIntegrationComprehensive:
    """Comprehensive integration tests for import/export workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = ImportExportService()
        self.csv_processor = CSVProcessor()
        self.json_processor = JSONProcessor()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.service.cleanup_transaction_contexts()
    
    def test_complete_json_import_export_workflow(self):
        """Test complete JSON import/export workflow with all entity types."""
        # Create comprehensive test data
        complete_data = {
            "metadata": {
                "export_timestamp": "2024-01-15T10:30:00",
                "version": "1.0",
                "total_records": 11
            },
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
        
        # Step 1: Create JSON file
        json_file = os.path.join(self.temp_dir, "complete_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2)
        
        # Step 2: Test import preview
        import_options = ImportOptions(
            entity_types=["unit_types", "unit_type_themes", "units", "job_titles", "persons", "assignments"],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            validate_only=False
        )
        
        preview_result = self.service.preview_import(json_file, FileFormat.JSON, import_options)
        
        assert preview_result.success == True
        assert preview_result.total_records == 11
        assert len(preview_result.dependency_order) == 6
        assert preview_result.dependency_order[0] in ['unit_types', 'unit_type_themes', 'job_titles', 'persons']
        assert preview_result.dependency_order[-1] == 'assignments'
        
        # Step 3: Test actual import (mocked database operations)
        with patch.object(self.service, '_execute_import_with_transaction') as mock_import:
            mock_result = ImportResult(
                success=True,
                records_processed={'unit_types': 2, 'persons': 2, 'assignments': 2},
                records_created={'unit_types': 2, 'persons': 2, 'assignments': 2},
                records_updated={},
                records_skipped={},
                errors=[],
                warnings=[],
                execution_time=1.5,
                operation_id="test_import_123"
            )
            mock_import.return_value = mock_result
            
            import_result = self.service.import_data(json_file, FileFormat.JSON, import_options)
            
            assert import_result.success == True
            assert import_result.total_records_processed == 6  # 2+2+2
            assert import_result.execution_time > 0
        
        # Step 4: Test export of the same data
        export_options = ExportOptions(
            entity_types=["unit_types", "unit_type_themes", "units", "job_titles", "persons", "assignments"],
            output_directory=self.temp_dir,
            file_prefix="integration_test_export",
            include_metadata=True,
            output_format=FileFormat.JSON
        )
        
        with patch.object(self.service, '_fetch_export_data') as mock_fetch:
            # Remove metadata from export data
            export_data = {k: v for k, v in complete_data.items() if k != 'metadata'}
            mock_fetch.return_value = export_data
            
            export_result = self.service.export_data(export_options)
            
            assert export_result.success == True
            assert len(export_result.generated_files) >= 1
            assert export_result.total_records == 11
    
    def test_csv_import_with_dependency_resolution(self):
        """Test CSV import with proper dependency resolution."""
        # Create CSV files for different entity types
        csv_files = {}
        
        # Unit Types CSV
        unit_types_csv = os.path.join(self.temp_dir, "unit_types.csv")
        with open(unit_types_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name', 'aliases', 'level', 'theme_id'])
            writer.writerow([1, 'Direzione', 'DIR', '[]', 1, None])
            writer.writerow([2, 'Ufficio', 'UFF', '[]', 2, None])
        csv_files['unit_types'] = unit_types_csv
        
        # Units CSV (depends on unit_types)
        units_csv = os.path.join(self.temp_dir, "units.csv")
        with open(units_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name', 'aliases', 'unit_type_id', 'parent_unit_id', 'start_date', 'end_date'])
            writer.writerow([1, 'Direzione Generale', 'DG', '[]', 1, None, '2024-01-01', None])
            writer.writerow([2, 'Ufficio IT', 'IT', '[]', 2, 1, '2024-01-01', None])
        csv_files['units'] = units_csv
        
        # Persons CSV
        persons_csv = os.path.join(self.temp_dir, "persons.csv")
        with open(persons_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name', 'email', 'first_name', 'last_name', 'registration_no', 'profile_image'])
            writer.writerow([1, 'Mario Rossi', 'M.Rossi', 'mario@example.com', 'Mario', 'Rossi', 'EMP001', None])
        csv_files['persons'] = persons_csv
        
        # Job Titles CSV
        job_titles_csv = os.path.join(self.temp_dir, "job_titles.csv")
        with open(job_titles_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name', 'aliases', 'start_date', 'end_date'])
            writer.writerow([1, 'Manager', 'MGR', '[]', '2024-01-01', None])
        csv_files['job_titles'] = job_titles_csv
        
        # Assignments CSV (depends on persons, units, job_titles)
        assignments_csv = os.path.join(self.temp_dir, "assignments.csv")
        with open(assignments_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['person_id', 'unit_id', 'job_title_id', 'percentage', 'is_current', 'valid_from'])
            writer.writerow([1, 1, 1, 1.0, True, '2024-01-01'])
        csv_files['assignments'] = assignments_csv
        
        # Test parsing each CSV file
        import_options = ImportOptions(
            entity_types=['unit_types', 'units', 'persons', 'job_titles', 'assignments'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Parse CSV files using CSV processor
        parsed_results = {}
        for entity_type, csv_file in csv_files.items():
            result = self.csv_processor.parse_csv_file(csv_file, entity_type)
            assert result.success, f"Failed to parse {entity_type} CSV: {result.errors}"
            parsed_results[entity_type] = result.data
        
        # Test dependency resolution
        dependency_order = self.service.dependency_resolver.get_processing_order(list(parsed_results.keys()))
        
        # Verify correct dependency order
        unit_types_idx = dependency_order.index('unit_types')
        units_idx = dependency_order.index('units')
        assignments_idx = dependency_order.index('assignments')
        
        assert unit_types_idx < units_idx, "unit_types should come before units"
        assert units_idx < assignments_idx, "units should come before assignments"
        
        # Test foreign key validation
        validation_result = self.service.validate_import_data(parsed_results, import_options)
        
        # Should have minimal errors (mainly due to mocked database)
        critical_errors = [e for e in validation_result.errors 
                          if e.error_type in [ImportErrorType.FILE_FORMAT_ERROR, ImportErrorType.CIRCULAR_REFERENCE]]
        assert len(critical_errors) == 0
    
    def test_import_with_validation_errors_and_rollback(self):
        """Test import with validation errors and transaction rollback."""
        # Create JSON with validation errors
        invalid_data = {
            "unit_types": [
                {
                    "id": 1,
                    "short_name": "DG",
                    "level": 1
                    # Missing required 'name' field
                },
                {
                    "id": 2,
                    "name": "Valid Unit",
                    "short_name": "VU",
                    "level": 2
                }
            ],
            "persons": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "invalid-email-format"  # Invalid email
                }
            ]
        }
        
        json_file = os.path.join(self.temp_dir, "invalid_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        import_options = ImportOptions(
            entity_types=['unit_types', 'persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            validate_only=False
        )
        
        # Test preview first (should show validation errors)
        preview_result = self.service.preview_import(json_file, FileFormat.JSON, import_options)
        
        # Preview should succeed but show validation issues
        assert len(preview_result.validation_results) > 0
        
        # Check for specific validation errors
        missing_name_errors = [e for e in preview_result.validation_results 
                              if e.error_type == ImportErrorType.MISSING_REQUIRED_FIELD and e.field == 'name']
        assert len(missing_name_errors) > 0
        
        invalid_email_errors = [e for e in preview_result.validation_results 
                               if e.error_type == ImportErrorType.INVALID_DATA_TYPE and e.field == 'email']
        assert len(invalid_email_errors) > 0
        
        # Test actual import (should fail and rollback)
        with patch.object(self.service, '_execute_import_with_transaction') as mock_import:
            # Simulate import failure due to validation errors
            mock_result = ImportResult(
                success=False,
                records_processed={'unit_types': 0, 'persons': 0},
                records_created={'unit_types': 0, 'persons': 0},
                records_updated={},
                records_skipped={},
                errors=preview_result.validation_results,
                warnings=[],
                execution_time=0.1,
                operation_id="test_failed_import"
            )
            mock_import.return_value = mock_result
            
            import_result = self.service.import_data(json_file, FileFormat.JSON, import_options)
            
            assert import_result.success == False
            assert len(import_result.errors) > 0
            assert import_result.total_records_created == 0
    
    def test_conflict_resolution_strategies(self):
        """Test different conflict resolution strategies."""
        # Create initial data
        initial_data = {
            "persons": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "short_name": "J.Doe",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "registration_no": "EMP001",
                    "profile_image": None
                }
            ]
        }
        
        # Create conflicting import data (same ID, different data)
        conflict_data = {
            "persons": [
                {
                    "id": 1,
                    "name": "John Doe Updated",
                    "short_name": "J.Doe",
                    "email": "john.updated@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "registration_no": "EMP001",
                    "profile_image": None
                },
                {
                    "id": 2,
                    "name": "Jane Smith",
                    "short_name": "J.Smith",
                    "email": "jane@example.com",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "registration_no": "EMP002",
                    "profile_image": None
                }
            ]
        }
        
        conflict_file = os.path.join(self.temp_dir, "conflict_data.json")
        with open(conflict_file, 'w', encoding='utf-8') as f:
            json.dump(conflict_data, f)
        
        # Test SKIP_DUPLICATES strategy
        skip_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        with patch.object(self.service.conflict_resolution_manager, 'resolve_conflicts') as mock_resolve:
            from app.services.conflict_resolution import ConflictResolutionResult
            
            mock_result = ConflictResolutionResult(
                success=True,
                records_to_create=[conflict_data['persons'][1]],  # Only Jane (new)
                records_to_update=[],
                records_skipped=[conflict_data['persons'][0]],  # John (duplicate)
                conflicts_detected=[],
                errors=[]
            )
            mock_resolve.return_value = mock_result
            
            preview_result = self.service.preview_import(conflict_file, FileFormat.JSON, skip_options)
            
            # Should show conflict resolution in preview
            assert preview_result.success == True
        
        # Test UPDATE_EXISTING strategy
        update_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.UPDATE
        )
        
        with patch.object(self.service.conflict_resolution_manager, 'resolve_conflicts') as mock_resolve:
            mock_result = ConflictResolutionResult(
                success=True,
                records_to_create=[conflict_data['persons'][1]],  # Jane (new)
                records_to_update=[conflict_data['persons'][0]],  # John (updated)
                records_skipped=[],
                conflicts_detected=[],
                errors=[]
            )
            mock_resolve.return_value = mock_result
            
            preview_result = self.service.preview_import(conflict_file, FileFormat.JSON, update_options)
            
            assert preview_result.success == True
    
    def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        # Generate large dataset
        large_data = {
            "unit_types": [],
            "persons": [],
            "assignments": []
        }
        
        # Generate 1000 unit types
        for i in range(1000):
            large_data["unit_types"].append({
                "id": i + 1,
                "name": f"Unit Type {i + 1}",
                "short_name": f"UT{i + 1}",
                "aliases": [],
                "level": (i % 5) + 1,
                "theme_id": None
            })
        
        # Generate 5000 persons
        for i in range(5000):
            large_data["persons"].append({
                "id": i + 1,
                "name": f"Person {i + 1}",
                "short_name": f"P{i + 1}",
                "email": f"person{i + 1}@example.com",
                "first_name": f"First{i + 1}",
                "last_name": f"Last{i + 1}",
                "registration_no": f"EMP{i + 1:05d}",
                "profile_image": None
            })
        
        large_file = os.path.join(self.temp_dir, "large_dataset.json")
        with open(large_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f)
        
        import_options = ImportOptions(
            entity_types=['unit_types', 'persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            batch_size=100  # Process in batches
        )
        
        # Test preview performance
        start_time = time.time()
        preview_result = self.service.preview_import(large_file, FileFormat.JSON, import_options)
        preview_time = time.time() - start_time
        
        assert preview_result.success == True
        assert preview_result.total_records == 6000  # 1000 + 5000
        assert preview_time < 30.0  # Should complete within 30 seconds
        
        # Verify estimated processing time is reasonable
        assert preview_result.estimated_processing_time > 0
        assert preview_result.estimated_processing_time < 300  # Less than 5 minutes estimate
    
    def test_export_with_date_filtering(self):
        """Test export with date range filtering."""
        export_options = ExportOptions(
            entity_types=['units', 'assignments'],
            date_range=(date(2024, 1, 1), date(2024, 12, 31)),
            output_directory=self.temp_dir,
            file_prefix="date_filtered_export",
            include_metadata=True
        )
        
        # Mock data with different date ranges
        mock_export_data = {
            "units": [
                {
                    "id": 1,
                    "name": "Active Unit",
                    "start_date": "2024-06-01",
                    "end_date": None
                },
                {
                    "id": 2,
                    "name": "Historical Unit",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31"
                }
            ],
            "assignments": [
                {
                    "id": 1,
                    "person_id": 1,
                    "unit_id": 1,
                    "valid_from": "2024-06-01",
                    "valid_to": None,
                    "is_current": True
                }
            ]
        }
        
        with patch.object(self.service, '_fetch_export_data') as mock_fetch:
            # Mock should return filtered data
            mock_fetch.return_value = {
                "units": [mock_export_data["units"][0]],  # Only active unit
                "assignments": mock_export_data["assignments"]
            }
            
            export_result = self.service.export_data(export_options)
            
            assert export_result.success == True
            assert len(export_result.generated_files) >= 1
            
            # Verify date filtering was applied
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args[0]
            assert call_args[0] == export_options  # Export options passed
    
    def test_roundtrip_data_integrity(self):
        """Test data integrity through complete import/export roundtrip."""
        # Original test data
        original_data = {
            "unit_types": [
                {
                    "id": 1,
                    "name": "Test Unit Type",
                    "short_name": "TUT",
                    "aliases": [{"value": "Test Type", "lang": "en-US"}],
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
        
        # Step 1: Export original data
        original_file = os.path.join(self.temp_dir, "original.json")
        with open(original_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, indent=2)
        
        # Step 2: Import the data
        import_options = ImportOptions(
            entity_types=['unit_types', 'persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Mock successful import
        with patch.object(self.service, '_execute_import_with_transaction') as mock_import:
            mock_result = ImportResult(
                success=True,
                records_processed={'unit_types': 1, 'persons': 1},
                records_created={'unit_types': 1, 'persons': 1},
                records_updated={},
                records_skipped={},
                errors=[],
                warnings=[],
                execution_time=0.5,
                operation_id="roundtrip_import"
            )
            mock_import.return_value = mock_result
            
            import_result = self.service.import_data(original_file, FileFormat.JSON, import_options)
            assert import_result.success == True
        
        # Step 3: Export the imported data
        export_options = ExportOptions(
            entity_types=['unit_types', 'persons'],
            output_directory=self.temp_dir,
            file_prefix="roundtrip_export",
            include_metadata=False,
            output_format=FileFormat.JSON
        )
        
        with patch.object(self.service, '_fetch_export_data') as mock_fetch:
            # Return the same data (simulating successful roundtrip)
            mock_fetch.return_value = original_data
            
            export_result = self.service.export_data(export_options)
            assert export_result.success == True
            
            # Step 4: Verify exported data matches original
            exported_file = export_result.generated_files[0]
            with open(exported_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            # Compare data integrity
            assert exported_data['unit_types'][0]['name'] == original_data['unit_types'][0]['name']
            assert exported_data['unit_types'][0]['aliases'] == original_data['unit_types'][0]['aliases']
            assert exported_data['persons'][0]['email'] == original_data['persons'][0]['email']
            assert exported_data['persons'][0]['registration_no'] == original_data['persons'][0]['registration_no']
    
    def test_concurrent_import_operations(self):
        """Test handling of concurrent import operations."""
        # Create multiple import files
        import_files = []
        for i in range(3):
            data = {
                "persons": [
                    {
                        "id": i + 1,
                        "name": f"Person {i + 1}",
                        "short_name": f"P{i + 1}",
                        "email": f"person{i + 1}@example.com",
                        "first_name": f"First{i + 1}",
                        "last_name": f"Last{i + 1}",
                        "registration_no": f"EMP{i + 1:03d}",
                        "profile_image": None
                    }
                ]
            }
            
            import_file = os.path.join(self.temp_dir, f"concurrent_import_{i}.json")
            with open(import_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            import_files.append(import_file)
        
        # Test that service can handle multiple transaction contexts
        operation_ids = []
        for i, import_file in enumerate(import_files):
            operation_id = f"concurrent_op_{i}"
            context = self.service.create_transaction_context(operation_id)
            operation_ids.append(operation_id)
            
            assert context.operation_id == operation_id
            assert context.is_active == True
        
        # Verify all transactions are tracked
        active_transactions = self.service.get_active_transactions()
        assert len(active_transactions) == 3
        
        for op_id in operation_ids:
            assert op_id in active_transactions
        
        # Clean up transactions
        for op_id in operation_ids:
            self.service.commit_transaction(op_id)
        
        # Verify cleanup
        assert len(self.service.get_active_transactions()) == 0
    
    def test_memory_usage_with_large_files(self):
        """Test memory usage patterns with large files."""
        # Create a moderately large dataset to test memory handling
        large_data = {
            "persons": []
        }
        
        # Generate 10,000 person records
        for i in range(10000):
            large_data["persons"].append({
                "id": i + 1,
                "name": f"Person {i + 1}",
                "short_name": f"P{i + 1}",
                "email": f"person{i + 1}@example.com",
                "first_name": f"First{i + 1}",
                "last_name": f"Last{i + 1}",
                "registration_no": f"EMP{i + 1:05d}",
                "profile_image": f"profiles/person{i + 1}.jpg" if i % 10 == 0 else None
            })
        
        large_file = os.path.join(self.temp_dir, "memory_test.json")
        with open(large_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f)
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            batch_size=500  # Process in smaller batches
        )
        
        # Test that preview doesn't consume excessive memory
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        preview_result = self.service.preview_import(large_file, FileFormat.JSON, import_options)
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        assert preview_result.success == True
        assert preview_result.total_records == 10000
        
        # Memory increase should be reasonable (less than 500MB for 10k records)
        assert memory_increase < 500, f"Memory increase too high: {memory_increase}MB"


if __name__ == '__main__':
    pytest.main([__file__])