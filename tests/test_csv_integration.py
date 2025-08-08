"""
Integration tests for CSV import/export workflow.
"""

import os
import tempfile
import pytest
from pathlib import Path

from app.services.csv_processor import CSVProcessor
from app.models.import_export import ImportOptions, ExportOptions


class TestCSVIntegration:
    """Integration tests for complete CSV workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_csv_workflow(self):
        """Test complete CSV import/export workflow."""
        # Create sample data
        original_data = {
            'unit_types': [
                {
                    'id': 1,
                    'name': 'Direzione Generale',
                    'short_name': 'DG',
                    'aliases': [{'value': 'General Direction', 'lang': 'en-US'}],
                    'level': 1,
                    'theme_id': 1
                },
                {
                    'id': 2,
                    'name': 'Ufficio Personale',
                    'short_name': 'UP',
                    'aliases': [],
                    'level': 2,
                    'theme_id': None
                }
            ],
            'persons': [
                {
                    'id': 1,
                    'name': 'Mario Rossi',
                    'short_name': 'M.Rossi',
                    'email': 'mario.rossi@example.com',
                    'first_name': 'Mario',
                    'last_name': 'Rossi',
                    'registration_no': 'EMP001',
                    'profile_image': None
                }
            ]
        }
        
        # Step 1: Export data to CSV
        export_options = ExportOptions(
            entity_types=['unit_types', 'persons'],
            file_prefix='test_workflow',
            include_metadata=True,
            output_directory=self.temp_dir
        )
        
        export_processor = CSVProcessor(export_options)
        exported_files = export_processor.export_to_csv(original_data, export_options)
        
        # Verify export
        assert len(exported_files) >= 2  # At least CSV files + metadata
        csv_files = [f for f in exported_files if f.endswith('.csv')]
        assert len(csv_files) == 2
        
        # Step 2: Import the exported CSV files
        import_options = ImportOptions(
            entity_types=['unit_types', 'persons'],
            encoding='utf-8'
        )
        
        import_processor = CSVProcessor(import_options)
        
        # Create file path mapping for import
        file_paths = {}
        for csv_file in csv_files:
            filename = os.path.basename(csv_file)
            if 'unit_types' in filename:
                file_paths['unit_types'] = csv_file
            elif 'persons' in filename:
                file_paths['persons'] = csv_file
        
        # Parse the CSV files
        import_results = import_processor.parse_csv_files(file_paths)
        
        # Verify import results
        assert 'unit_types' in import_results
        assert 'persons' in import_results
        
        unit_types_result = import_results['unit_types']
        persons_result = import_results['persons']
        
        assert unit_types_result.success
        assert persons_result.success
        
        # Verify data integrity
        assert len(unit_types_result.data) == 2
        assert len(persons_result.data) == 1
        
        # Check specific data values
        imported_unit_type = unit_types_result.data[0]
        assert imported_unit_type['name'] == 'Direzione Generale'
        assert imported_unit_type['short_name'] == 'DG'
        assert isinstance(imported_unit_type['aliases'], list)
        assert len(imported_unit_type['aliases']) == 1
        assert imported_unit_type['aliases'][0]['value'] == 'General Direction'
        
        imported_person = persons_result.data[0]
        assert imported_person['name'] == 'Mario Rossi'
        assert imported_person['email'] == 'mario.rossi@example.com'
        assert imported_person['registration_no'] == 'EMP001'
    
    def test_csv_roundtrip_with_special_characters(self):
        """Test CSV roundtrip with special characters and edge cases."""
        # Data with various edge cases
        test_data = {
            'unit_types': [
                {
                    'id': 1,
                    'name': 'Unit with "quotes" and, commas',
                    'short_name': 'U"Q,C',
                    'aliases': [
                        {'value': 'Alias with "quotes"', 'lang': 'en-US'},
                        {'value': 'Alias, with comma', 'lang': 'it-IT'}
                    ],
                    'level': 1,
                    'theme_id': None
                }
            ]
        }
        
        # Export
        export_options = ExportOptions(
            entity_types=['unit_types'],
            output_directory=self.temp_dir
        )
        
        processor = CSVProcessor()
        exported_files = processor.export_to_csv(test_data, export_options)
        
        csv_file = [f for f in exported_files if f.endswith('.csv')][0]
        
        # Import back
        result = processor.parse_csv_file(csv_file, 'unit_types')
        
        assert result.success
        assert len(result.data) == 1
        
        imported_data = result.data[0]
        assert imported_data['name'] == 'Unit with "quotes" and, commas'
        assert imported_data['short_name'] == 'U"Q,C'
        assert len(imported_data['aliases']) == 2
        assert imported_data['aliases'][0]['value'] == 'Alias with "quotes"'
        assert imported_data['aliases'][1]['value'] == 'Alias, with comma'
    
    def test_csv_export_statistics(self):
        """Test export statistics functionality."""
        data = {
            'unit_types': [{'id': 1}, {'id': 2}, {'id': 3}],
            'persons': [{'id': 1}],
            'assignments': []
        }
        
        processor = CSVProcessor()
        stats = processor.get_export_statistics(data)
        
        assert stats['total_records'] == 4
        assert stats['entity_counts']['unit_types'] == 3
        assert stats['entity_counts']['persons'] == 1
        assert stats['entity_counts']['assignments'] == 0
        assert 'assignments' in stats['empty_entities']
        assert len(stats['entity_types']) == 3


if __name__ == "__main__":
    pytest.main([__file__])