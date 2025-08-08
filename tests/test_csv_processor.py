"""
Tests for CSV processor functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path

from app.services.csv_processor import CSVProcessor, CSVParseResult
from app.models.import_export import ImportOptions, ExportOptions, ImportErrorType


class TestCSVProcessor:
    """Test cases for CSVProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = CSVProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_valid_unit_types_csv(self):
        """Test parsing a valid unit types CSV file."""
        csv_content = """id,name,short_name,aliases,level,theme_id
1,"Direzione Generale","DG","[{""value"":""General Direction"",""lang"":""en-US""}]",1,1
2,"Ufficio","UFF","[]",2,
"""
        csv_file = os.path.join(self.temp_dir, "unit_types.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        result = self.processor.parse_csv_file(csv_file, "unit_types")
        
        assert result.success
        assert len(result.data) == 2
        assert result.processed_rows == 2
        assert len(result.errors) == 0
        
        # Check first record
        first_record = result.data[0]
        assert first_record['id'] == 1
        assert first_record['name'] == "Direzione Generale"
        assert first_record['short_name'] == "DG"
        assert isinstance(first_record['aliases'], list)
        assert len(first_record['aliases']) == 1
        assert first_record['level'] == 1
        assert first_record['theme_id'] == 1
    
    def test_parse_csv_with_missing_required_field(self):
        """Test parsing CSV with missing required field."""
        csv_content = """id,short_name,aliases,level,theme_id
1,"DG","[]",1,1
"""
        csv_file = os.path.join(self.temp_dir, "unit_types.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        result = self.processor.parse_csv_file(csv_file, "unit_types")
        
        assert not result.success
        assert len(result.errors) > 0
        assert any(error.error_type == ImportErrorType.MISSING_REQUIRED_FIELD 
                  for error in result.errors)
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        result = self.processor.parse_csv_file("/nonexistent/file.csv", "unit_types")
        
        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].error_type == ImportErrorType.FILE_FORMAT_ERROR
    
    def test_parse_invalid_entity_type(self):
        """Test parsing with invalid entity type."""
        csv_file = os.path.join(self.temp_dir, "test.csv")
        with open(csv_file, 'w') as f:
            f.write("id,name\n1,test\n")
        
        result = self.processor.parse_csv_file(csv_file, "invalid_entity")
        
        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].error_type == ImportErrorType.FILE_FORMAT_ERROR
    
    def test_generate_csv_file_unit_types(self):
        """Test generating CSV file for unit types."""
        data = [
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
                'name': 'Ufficio',
                'short_name': 'UFF',
                'aliases': [],
                'level': 2,
                'theme_id': None
            }
        ]
        
        output_file = os.path.join(self.temp_dir, "output_unit_types.csv")
        success = self.processor.generate_csv_file(data, "unit_types", output_file)
        
        assert success
        assert os.path.exists(output_file)
        
        # Verify content by parsing it back
        result = self.processor.parse_csv_file(output_file, "unit_types")
        assert result.success
        assert len(result.data) == 2
    
    def test_generate_empty_csv_file(self):
        """Test generating CSV file with no data."""
        output_file = os.path.join(self.temp_dir, "empty.csv")
        success = self.processor.generate_csv_file([], "unit_types", output_file)
        
        assert success
        assert os.path.exists(output_file)
        
        # Should have headers only
        with open(output_file, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            assert len(lines) == 1  # Header only
            assert 'id,name,short_name' in lines[0]
    
    def test_generate_csv_files_multiple_entities(self):
        """Test generating multiple CSV files."""
        data = {
            'unit_types': [
                {'id': 1, 'name': 'Test Unit Type', 'short_name': 'TUT', 'aliases': [], 'level': 1, 'theme_id': None}
            ],
            'persons': [
                {'id': 1, 'name': 'John Doe', 'short_name': 'J.Doe', 'email': 'john@example.com', 
                 'first_name': 'John', 'last_name': 'Doe', 'registration_no': 'EMP001', 'profile_image': None}
            ]
        }
        
        generated_files = self.processor.generate_csv_files(data, self.temp_dir)
        
        assert len(generated_files) == 2
        assert all(os.path.exists(f) for f in generated_files)
        
        # Check filenames
        filenames = [os.path.basename(f) for f in generated_files]
        assert 'unit_types.csv' in filenames
        assert 'persons.csv' in filenames
    
    def test_validate_csv_structure_valid(self):
        """Test CSV structure validation with valid file."""
        csv_content = """id,name,short_name,aliases,level,theme_id
1,"Test","T","[]",1,1
"""
        csv_file = os.path.join(self.temp_dir, "valid.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        errors = self.processor.validate_csv_structure(csv_file, "unit_types")
        assert len(errors) == 0
    
    def test_validate_csv_structure_missing_required(self):
        """Test CSV structure validation with missing required field."""
        csv_content = """id,short_name,aliases,level,theme_id
1,"T","[]",1,1
"""
        csv_file = os.path.join(self.temp_dir, "invalid.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        errors = self.processor.validate_csv_structure(csv_file, "unit_types")
        assert len(errors) > 0
        assert any(error.error_type == ImportErrorType.MISSING_REQUIRED_FIELD 
                  for error in errors)
    
    def test_parse_csv_with_column_mapping(self):
        """Test parsing CSV with alternative column names."""
        csv_content = """ID,Name,Short Name,Aliases,Level,Theme ID
1,"Direzione Generale","DG","[]",1,1
"""
        csv_file = os.path.join(self.temp_dir, "mapped.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        result = self.processor.parse_csv_file(csv_file, "unit_types")
        
        assert result.success
        assert len(result.data) == 1
        assert result.data[0]['name'] == "Direzione Generale"
    
    def test_parse_csv_with_json_aliases(self):
        """Test parsing CSV with JSON aliases field."""
        csv_content = """id,name,short_name,aliases,level,theme_id
1,"Test","T","[{""value"":""Test Unit"",""lang"":""en-US""},{""value"":""Unità Test"",""lang"":""it-IT""}]",1,1
"""
        csv_file = os.path.join(self.temp_dir, "aliases.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        result = self.processor.parse_csv_file(csv_file, "unit_types")
        
        assert result.success
        assert len(result.data) == 1
        aliases = result.data[0]['aliases']
        assert isinstance(aliases, list)
        assert len(aliases) == 2
        assert aliases[0]['value'] == "Test Unit"
        assert aliases[1]['lang'] == "it-IT"
    
    def test_csv_processor_with_options(self):
        """Test CSV processor with custom options."""
        options = ImportOptions(
            entity_types=['unit_types'],
            encoding='utf-8',
            csv_delimiter=';',
            csv_quote_char="'"
        )
        processor = CSVProcessor(options)
        
        csv_content = """id;name;short_name;aliases;level;theme_id
1;'Direzione Generale';'DG';'[]';1;1
"""
        csv_file = os.path.join(self.temp_dir, "semicolon.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        result = processor.parse_csv_file(csv_file, "unit_types")
        
        assert result.success
        assert len(result.data) == 1
        assert result.data[0]['name'] == "Direzione Generale"
    
    def test_export_to_csv_with_options(self):
        """Test exporting to CSV with export options."""
        from app.models.import_export import ExportOptions
        
        export_options = ExportOptions(
            entity_types=['unit_types', 'persons'],
            file_prefix='test_export',
            include_metadata=True,
            output_directory=self.temp_dir,
            encoding='utf-8'
        )
        
        processor = CSVProcessor(export_options)
        
        data = {
            'unit_types': [
                {'id': 1, 'name': 'Test Unit', 'short_name': 'TU', 'aliases': [], 'level': 1, 'theme_id': None}
            ],
            'persons': [
                {'id': 1, 'name': 'John Doe', 'short_name': 'J.Doe', 'email': 'john@example.com', 
                 'first_name': 'John', 'last_name': 'Doe', 'registration_no': 'EMP001', 'profile_image': None}
            ]
        }
        
        generated_files = processor.export_to_csv(data, export_options)
        
        assert len(generated_files) >= 2  # At least 2 CSV files
        assert any('unit_types.csv' in f for f in generated_files)
        assert any('persons.csv' in f for f in generated_files)
        
        # Check if metadata file was created
        metadata_files = [f for f in generated_files if 'metadata.json' in f]
        assert len(metadata_files) == 1
        
        # Verify all files exist
        for file_path in generated_files:
            assert os.path.exists(file_path)
    
    def test_csv_special_characters_escaping(self):
        """Test CSV generation with special characters."""
        data = [
            {
                'id': 1,
                'name': 'Test "Quoted" Name',
                'short_name': 'T"Q"N',
                'aliases': [{'value': 'Test, with comma', 'lang': 'en-US'}],
                'level': 1,
                'theme_id': None
            }
        ]
        
        output_file = os.path.join(self.temp_dir, "special_chars.csv")
        success = self.processor.generate_csv_file(data, "unit_types", output_file)
        
        assert success
        assert os.path.exists(output_file)
        
        # Read back and verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Should contain properly escaped quotes (doubled quotes in CSV)
            assert 'Test ""Quoted"" Name' in content
            assert 'T""Q""N' in content
    
    def test_get_export_statistics(self):
        """Test export statistics generation."""
        data = {
            'unit_types': [{'id': 1}, {'id': 2}],
            'persons': [{'id': 1}],
            'assignments': []  # Empty entity
        }
        
        stats = self.processor.get_export_statistics(data)
        
        assert stats['total_records'] == 3
        assert stats['entity_counts']['unit_types'] == 2
        assert stats['entity_counts']['persons'] == 1
        assert stats['entity_counts']['assignments'] == 0
        assert 'assignments' in stats['empty_entities']
        assert len(stats['entity_types']) == 3
    
    def test_generate_csv_files_with_prefix(self):
        """Test generating CSV files with filename prefix."""
        data = {
            'unit_types': [
                {'id': 1, 'name': 'Test', 'short_name': 'T', 'aliases': [], 'level': 1, 'theme_id': None}
            ]
        }
        
        generated_files = self.processor.generate_csv_files(data, self.temp_dir, "backup_20240101")
        
        assert len(generated_files) == 1
        filename = os.path.basename(generated_files[0])
        assert filename == "backup_20240101_unit_types.csv"
        assert os.path.exists(generated_files[0])


if __name__ == "__main__":
    pytest.main([__file__])