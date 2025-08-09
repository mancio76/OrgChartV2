"""
Comprehensive unit tests for the export file manager.

This module tests the export file management functionality including
file generation, storage, cleanup, and metadata handling.
"""

import os
import tempfile
import pytest
import json
import shutil
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.services.export_file_manager import (
    ExportFileManager, ExportFileInfo, ExportFileManagerException,
    FileCleanupPolicy, ExportMetadata
)
from app.models.import_export import ExportOptions, FileFormat


class TestExportFileManager:
    """Test cases for ExportFileManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ExportFileManager(base_directory=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test that the manager initializes correctly."""
        assert self.manager.base_directory == self.temp_dir
        assert os.path.exists(self.temp_dir)
        assert isinstance(self.manager.cleanup_policies, dict)
    
    def test_initialization_creates_directory(self):
        """Test that initialization creates base directory if it doesn't exist."""
        new_temp_dir = os.path.join(self.temp_dir, 'new_export_dir')
        assert not os.path.exists(new_temp_dir)
        
        manager = ExportFileManager(base_directory=new_temp_dir)
        assert os.path.exists(new_temp_dir)
        assert manager.base_directory == new_temp_dir
    
    def test_generate_export_directory_name(self):
        """Test export directory name generation."""
        options = ExportOptions(
            entity_types=['unit_types', 'persons'],
            file_prefix='test_export',
            output_format=FileFormat.JSON
        )
        
        dir_name = self.manager._generate_export_directory_name(options)
        
        assert 'test_export' in dir_name
        assert 'json' in dir_name
        # Should contain timestamp
        assert len(dir_name) > len('test_export_json')
    
    def test_generate_export_directory_name_no_prefix(self):
        """Test export directory name generation without prefix."""
        options = ExportOptions(
            entity_types=['unit_types'],
            output_format=FileFormat.CSV
        )
        
        dir_name = self.manager._generate_export_directory_name(options)
        
        assert 'export' in dir_name
        assert 'csv' in dir_name
    
    def test_create_export_directory(self):
        """Test creating export directory."""
        options = ExportOptions(
            entity_types=['unit_types'],
            file_prefix='test_create',
            output_format=FileFormat.JSON
        )
        
        export_dir = self.manager.create_export_directory(options)
        
        assert os.path.exists(export_dir)
        assert os.path.isdir(export_dir)
        assert export_dir.startswith(self.temp_dir)
        assert 'test_create' in os.path.basename(export_dir)
    
    def test_create_export_directory_with_custom_path(self):
        """Test creating export directory with custom output directory."""
        custom_dir = os.path.join(self.temp_dir, 'custom_exports')
        options = ExportOptions(
            entity_types=['unit_types'],
            output_directory=custom_dir,
            file_prefix='custom_test'
        )
        
        export_dir = self.manager.create_export_directory(options)
        
        assert os.path.exists(export_dir)
        assert export_dir.startswith(custom_dir)
        assert 'custom_test' in os.path.basename(export_dir)
    
    def test_save_export_file(self):
        """Test saving export file."""
        # Create export directory
        export_dir = os.path.join(self.temp_dir, 'test_export')
        os.makedirs(export_dir)
        
        # Test data
        test_data = {'unit_types': [{'id': 1, 'name': 'Test Unit'}]}
        filename = 'test_export.json'
        
        file_path = self.manager.save_export_file(export_dir, filename, test_data, FileFormat.JSON)
        
        assert os.path.exists(file_path)
        assert file_path == os.path.join(export_dir, filename)
        
        # Verify file content
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == test_data
    
    def test_save_export_file_csv_format(self):
        """Test saving export file in CSV format."""
        export_dir = os.path.join(self.temp_dir, 'test_csv_export')
        os.makedirs(export_dir)
        
        # CSV data as string
        csv_data = "id,name,short_name\n1,Test Unit,TU\n"
        filename = 'unit_types.csv'
        
        file_path = self.manager.save_export_file(export_dir, filename, csv_data, FileFormat.CSV)
        
        assert os.path.exists(file_path)
        
        # Verify file content
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == csv_data
    
    def test_save_export_file_invalid_directory(self):
        """Test error handling when saving to invalid directory."""
        invalid_dir = '/nonexistent/directory'
        test_data = {'test': 'data'}
        
        with pytest.raises(ExportFileManagerException) as exc_info:
            self.manager.save_export_file(invalid_dir, 'test.json', test_data, FileFormat.JSON)
        
        assert 'Failed to save export file' in str(exc_info.value)
    
    def test_create_export_metadata(self):
        """Test creating export metadata."""
        options = ExportOptions(
            entity_types=['unit_types', 'persons'],
            file_prefix='metadata_test',
            include_metadata=True
        )
        
        export_stats = {
            'total_records': 150,
            'entity_counts': {'unit_types': 50, 'persons': 100},
            'export_duration': 2.5
        }
        
        generated_files = [
            '/path/to/unit_types.csv',
            '/path/to/persons.csv'
        ]
        
        metadata = self.manager.create_export_metadata(options, export_stats, generated_files)
        
        assert isinstance(metadata, ExportMetadata)
        assert metadata.total_records == 150
        assert metadata.entity_counts == {'unit_types': 50, 'persons': 100}
        assert metadata.export_duration == 2.5
        assert len(metadata.generated_files) == 2
        assert metadata.file_prefix == 'metadata_test'
        assert isinstance(metadata.export_timestamp, datetime)
    
    def test_save_export_metadata(self):
        """Test saving export metadata to file."""
        export_dir = os.path.join(self.temp_dir, 'metadata_export')
        os.makedirs(export_dir)
        
        metadata = ExportMetadata(
            export_timestamp=datetime.now(),
            total_records=100,
            entity_counts={'unit_types': 100},
            generated_files=['unit_types.csv'],
            export_duration=1.5,
            file_prefix='test_metadata'
        )
        
        metadata_file = self.manager.save_export_metadata(export_dir, metadata)
        
        assert os.path.exists(metadata_file)
        assert metadata_file.endswith('metadata.json')
        
        # Verify metadata content
        with open(metadata_file, 'r', encoding='utf-8') as f:
            saved_metadata = json.load(f)
        
        assert saved_metadata['total_records'] == 100
        assert saved_metadata['entity_counts']['unit_types'] == 100
        assert saved_metadata['file_prefix'] == 'test_metadata'
        assert 'export_timestamp' in saved_metadata
    
    def test_get_export_file_info(self):
        """Test getting export file information."""
        # Create test export file
        export_dir = os.path.join(self.temp_dir, 'info_test')
        os.makedirs(export_dir)
        
        test_file = os.path.join(export_dir, 'test_export.json')
        test_data = {'test': 'data'}
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        file_info = self.manager.get_export_file_info(test_file)
        
        assert isinstance(file_info, ExportFileInfo)
        assert file_info.file_path == test_file
        assert file_info.filename == 'test_export.json'
        assert file_info.file_size > 0
        assert file_info.format == FileFormat.JSON
        assert isinstance(file_info.created_at, datetime)
    
    def test_get_export_file_info_csv(self):
        """Test getting export file information for CSV files."""
        export_dir = os.path.join(self.temp_dir, 'csv_info_test')
        os.makedirs(export_dir)
        
        csv_file = os.path.join(export_dir, 'test_export.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('id,name\n1,test\n')
        
        file_info = self.manager.get_export_file_info(csv_file)
        
        assert file_info.format == FileFormat.CSV
        assert file_info.filename == 'test_export.csv'
    
    def test_get_export_file_info_nonexistent(self):
        """Test error handling for non-existent files."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.json')
        
        with pytest.raises(ExportFileManagerException) as exc_info:
            self.manager.get_export_file_info(nonexistent_file)
        
        assert 'File not found' in str(exc_info.value)
    
    def test_list_export_directories(self):
        """Test listing export directories."""
        # Create several export directories
        export_dirs = []
        for i in range(3):
            export_dir = os.path.join(self.temp_dir, f'export_{i}_20240101_120000')
            os.makedirs(export_dir)
            export_dirs.append(export_dir)
        
        # Create a non-export directory (should be ignored)
        other_dir = os.path.join(self.temp_dir, 'not_an_export')
        os.makedirs(other_dir)
        
        listed_dirs = self.manager.list_export_directories()
        
        assert len(listed_dirs) == 3
        for export_dir in export_dirs:
            assert any(listed_dir.endswith(os.path.basename(export_dir)) for listed_dir in listed_dirs)
    
    def test_list_export_directories_with_pattern(self):
        """Test listing export directories with pattern filtering."""
        # Create export directories with different prefixes
        json_dir = os.path.join(self.temp_dir, 'json_export_20240101_120000')
        csv_dir = os.path.join(self.temp_dir, 'csv_export_20240101_120000')
        os.makedirs(json_dir)
        os.makedirs(csv_dir)
        
        # List only JSON exports
        json_dirs = self.manager.list_export_directories(pattern='json_*')
        assert len(json_dirs) == 1
        assert 'json_export' in json_dirs[0]
        
        # List only CSV exports
        csv_dirs = self.manager.list_export_directories(pattern='csv_*')
        assert len(csv_dirs) == 1
        assert 'csv_export' in csv_dirs[0]
    
    def test_cleanup_old_exports_by_age(self):
        """Test cleanup of old export directories by age."""
        # Create old and new export directories
        old_dir = os.path.join(self.temp_dir, 'old_export_20240101_120000')
        new_dir = os.path.join(self.temp_dir, 'new_export_20240201_120000')
        os.makedirs(old_dir)
        os.makedirs(new_dir)
        
        # Modify timestamps to simulate age
        old_time = datetime.now() - timedelta(days=10)
        new_time = datetime.now() - timedelta(days=1)
        
        old_timestamp = old_time.timestamp()
        new_timestamp = new_time.timestamp()
        
        os.utime(old_dir, (old_timestamp, old_timestamp))
        os.utime(new_dir, (new_timestamp, new_timestamp))
        
        # Set cleanup policy to remove exports older than 5 days
        policy = FileCleanupPolicy(
            max_age_days=5,
            max_count=None,
            max_size_mb=None
        )
        
        cleaned_count = self.manager.cleanup_old_exports(policy)
        
        assert cleaned_count == 1
        assert not os.path.exists(old_dir)
        assert os.path.exists(new_dir)
    
    def test_cleanup_old_exports_by_count(self):
        """Test cleanup of old export directories by count."""
        # Create multiple export directories
        export_dirs = []
        for i in range(5):
            export_dir = os.path.join(self.temp_dir, f'export_{i}_20240101_12000{i}')
            os.makedirs(export_dir)
            export_dirs.append(export_dir)
            
            # Set different timestamps
            timestamp = (datetime.now() - timedelta(days=i)).timestamp()
            os.utime(export_dir, (timestamp, timestamp))
        
        # Set cleanup policy to keep only 3 most recent exports
        policy = FileCleanupPolicy(
            max_age_days=None,
            max_count=3,
            max_size_mb=None
        )
        
        cleaned_count = self.manager.cleanup_old_exports(policy)
        
        assert cleaned_count == 2  # Should remove 2 oldest
        
        # Check that 3 most recent directories remain
        remaining_dirs = self.manager.list_export_directories()
        assert len(remaining_dirs) == 3
    
    def test_cleanup_old_exports_by_size(self):
        """Test cleanup of old export directories by total size."""
        # Create export directories with files
        export_dirs = []
        for i in range(3):
            export_dir = os.path.join(self.temp_dir, f'size_export_{i}_20240101_12000{i}')
            os.makedirs(export_dir)
            export_dirs.append(export_dir)
            
            # Create files of different sizes
            test_file = os.path.join(export_dir, f'data_{i}.json')
            test_data = {'data': 'x' * (1024 * 100 * (i + 1))}  # 100KB, 200KB, 300KB
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            # Set different timestamps (oldest first)
            timestamp = (datetime.now() - timedelta(days=3-i)).timestamp()
            os.utime(export_dir, (timestamp, timestamp))
        
        # Set cleanup policy to limit total size to ~400KB
        policy = FileCleanupPolicy(
            max_age_days=None,
            max_count=None,
            max_size_mb=0.4  # 400KB
        )
        
        cleaned_count = self.manager.cleanup_old_exports(policy)
        
        # Should remove oldest directories until under size limit
        assert cleaned_count >= 1
        
        # Verify remaining size is under limit
        remaining_dirs = self.manager.list_export_directories()
        total_size = 0
        for export_dir in remaining_dirs:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
        
        assert total_size <= 0.4 * 1024 * 1024  # Under 400KB
    
    def test_get_export_statistics(self):
        """Test getting export statistics."""
        # Create several export directories with files
        for i in range(3):
            export_dir = os.path.join(self.temp_dir, f'stats_export_{i}_20240101_12000{i}')
            os.makedirs(export_dir)
            
            # Create test files
            for j in range(2):
                test_file = os.path.join(export_dir, f'file_{j}.json')
                with open(test_file, 'w', encoding='utf-8') as f:
                    json.dump({'test': 'data'}, f)
        
        stats = self.manager.get_export_statistics()
        
        assert 'total_exports' in stats
        assert 'total_files' in stats
        assert 'total_size_mb' in stats
        assert 'oldest_export' in stats
        assert 'newest_export' in stats
        
        assert stats['total_exports'] == 3
        assert stats['total_files'] == 6  # 3 dirs * 2 files each
        assert stats['total_size_mb'] > 0
    
    def test_get_export_statistics_empty_directory(self):
        """Test getting export statistics for empty directory."""
        # Remove all contents from temp directory
        for item in os.listdir(self.temp_dir):
            item_path = os.path.join(self.temp_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        
        stats = self.manager.get_export_statistics()
        
        assert stats['total_exports'] == 0
        assert stats['total_files'] == 0
        assert stats['total_size_mb'] == 0
        assert stats['oldest_export'] is None
        assert stats['newest_export'] is None
    
    def test_validate_export_directory(self):
        """Test export directory validation."""
        # Valid directory
        valid_dir = os.path.join(self.temp_dir, 'valid_export')
        os.makedirs(valid_dir)
        
        assert self.manager._validate_export_directory(valid_dir) == True
        
        # Non-existent directory
        nonexistent_dir = os.path.join(self.temp_dir, 'nonexistent')
        assert self.manager._validate_export_directory(nonexistent_dir) == False
        
        # File instead of directory
        test_file = os.path.join(self.temp_dir, 'not_a_directory.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        assert self.manager._validate_export_directory(test_file) == False
    
    def test_calculate_directory_size(self):
        """Test directory size calculation."""
        test_dir = os.path.join(self.temp_dir, 'size_test')
        os.makedirs(test_dir)
        
        # Create files of known sizes
        file1 = os.path.join(test_dir, 'file1.txt')
        file2 = os.path.join(test_dir, 'file2.txt')
        
        with open(file1, 'w') as f:
            f.write('x' * 1000)  # 1000 bytes
        
        with open(file2, 'w') as f:
            f.write('y' * 2000)  # 2000 bytes
        
        total_size = self.manager._calculate_directory_size(test_dir)
        assert total_size == 3000  # 1000 + 2000 bytes
    
    def test_calculate_directory_size_nonexistent(self):
        """Test directory size calculation for non-existent directory."""
        nonexistent_dir = os.path.join(self.temp_dir, 'nonexistent')
        size = self.manager._calculate_directory_size(nonexistent_dir)
        assert size == 0


class TestExportFileInfo:
    """Test cases for ExportFileInfo dataclass."""
    
    def test_export_file_info_creation(self):
        """Test creating ExportFileInfo instances."""
        file_path = '/path/to/export.json'
        filename = 'export.json'
        file_size = 1024
        file_format = FileFormat.JSON
        created_at = datetime.now()
        
        file_info = ExportFileInfo(
            file_path=file_path,
            filename=filename,
            file_size=file_size,
            format=file_format,
            created_at=created_at
        )
        
        assert file_info.file_path == file_path
        assert file_info.filename == filename
        assert file_info.file_size == file_size
        assert file_info.format == file_format
        assert file_info.created_at == created_at
    
    def test_export_file_info_size_mb_property(self):
        """Test file size in MB property."""
        file_info = ExportFileInfo(
            file_path='/test.json',
            filename='test.json',
            file_size=1024 * 1024,  # 1 MB
            format=FileFormat.JSON,
            created_at=datetime.now()
        )
        
        assert file_info.size_mb == 1.0
        
        # Test with fractional MB
        file_info.file_size = 1024 * 512  # 0.5 MB
        assert file_info.size_mb == 0.5


class TestExportMetadata:
    """Test cases for ExportMetadata dataclass."""
    
    def test_export_metadata_creation(self):
        """Test creating ExportMetadata instances."""
        export_timestamp = datetime.now()
        total_records = 100
        entity_counts = {'unit_types': 50, 'persons': 50}
        generated_files = ['file1.csv', 'file2.csv']
        export_duration = 2.5
        file_prefix = 'test_export'
        
        metadata = ExportMetadata(
            export_timestamp=export_timestamp,
            total_records=total_records,
            entity_counts=entity_counts,
            generated_files=generated_files,
            export_duration=export_duration,
            file_prefix=file_prefix
        )
        
        assert metadata.export_timestamp == export_timestamp
        assert metadata.total_records == total_records
        assert metadata.entity_counts == entity_counts
        assert metadata.generated_files == generated_files
        assert metadata.export_duration == export_duration
        assert metadata.file_prefix == file_prefix
    
    def test_export_metadata_to_dict(self):
        """Test converting ExportMetadata to dictionary."""
        metadata = ExportMetadata(
            export_timestamp=datetime(2024, 1, 1, 12, 0, 0),
            total_records=100,
            entity_counts={'unit_types': 100},
            generated_files=['test.csv'],
            export_duration=1.5,
            file_prefix='test'
        )
        
        metadata_dict = metadata.to_dict()
        
        assert metadata_dict['total_records'] == 100
        assert metadata_dict['entity_counts']['unit_types'] == 100
        assert metadata_dict['generated_files'] == ['test.csv']
        assert metadata_dict['export_duration'] == 1.5
        assert metadata_dict['file_prefix'] == 'test'
        assert 'export_timestamp' in metadata_dict


class TestFileCleanupPolicy:
    """Test cases for FileCleanupPolicy dataclass."""
    
    def test_file_cleanup_policy_creation(self):
        """Test creating FileCleanupPolicy instances."""
        policy = FileCleanupPolicy(
            max_age_days=30,
            max_count=10,
            max_size_mb=100.0
        )
        
        assert policy.max_age_days == 30
        assert policy.max_count == 10
        assert policy.max_size_mb == 100.0
    
    def test_file_cleanup_policy_defaults(self):
        """Test FileCleanupPolicy with default values."""
        policy = FileCleanupPolicy()
        
        assert policy.max_age_days is None
        assert policy.max_count is None
        assert policy.max_size_mb is None
    
    def test_file_cleanup_policy_validation(self):
        """Test FileCleanupPolicy validation."""
        # Valid policies
        assert FileCleanupPolicy(max_age_days=30).is_valid()
        assert FileCleanupPolicy(max_count=10).is_valid()
        assert FileCleanupPolicy(max_size_mb=100.0).is_valid()
        
        # Invalid policy (all None)
        assert not FileCleanupPolicy().is_valid()


if __name__ == '__main__':
    pytest.main([__file__])