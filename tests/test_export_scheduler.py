"""
Tests for the export scheduler functionality.

This module tests the scheduled export system including the scheduler framework,
file management, and integration with the import/export service.
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.services.export_scheduler import (
    ExportScheduler, ScheduleConfig, ScheduleInterval, ScheduleStatus
)
from app.services.export_file_manager import (
    ExportFileManager, FileRetentionConfig, RetentionPolicy, CompressionType
)
from app.models.import_export import ExportOptions, ExportResult, FileFormat


class TestScheduleConfig(unittest.TestCase):
    """Test schedule configuration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.export_options = ExportOptions(
            entity_types=['units', 'persons'],
            include_historical=True
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_schedule_config_creation(self):
        """Test creating a schedule configuration."""
        schedule = ScheduleConfig(
            id="test-schedule",
            name="Test Schedule",
            description="Test daily export",
            interval=ScheduleInterval.DAILY,
            export_options=self.export_options,
            output_directory=self.temp_dir,
            file_format=FileFormat.JSON,
            run_time="02:30"
        )
        
        self.assertEqual(schedule.name, "Test Schedule")
        self.assertEqual(schedule.interval, ScheduleInterval.DAILY)
        self.assertEqual(schedule.run_time, "02:30")
        self.assertTrue(schedule.enabled)
    
    def test_calculate_next_run_daily(self):
        """Test calculating next run time for daily schedule."""
        schedule = ScheduleConfig(
            id="test-schedule",
            name="Test Schedule",
            description="Test daily export",
            interval=ScheduleInterval.DAILY,
            export_options=self.export_options,
            output_directory=self.temp_dir,
            file_format=FileFormat.JSON,
            run_time="02:00"
        )
        
        # Test from a specific time
        from_time = datetime(2024, 1, 15, 10, 30)  # 10:30 AM
        next_run = schedule.calculate_next_run(from_time)
        
        # Should be tomorrow at 2:00 AM
        expected = datetime(2024, 1, 16, 2, 0)
        self.assertEqual(next_run, expected)
    
    def test_calculate_next_run_weekly(self):
        """Test calculating next run time for weekly schedule."""
        schedule = ScheduleConfig(
            id="test-schedule",
            name="Test Schedule",
            description="Test weekly export",
            interval=ScheduleInterval.WEEKLY,
            export_options=self.export_options,
            output_directory=self.temp_dir,
            file_format=FileFormat.JSON,
            run_time="03:00",
            day_of_week=0  # Monday
        )
        
        # Test from a Wednesday (weekday 2)
        from_time = datetime(2024, 1, 17, 10, 30)  # Wednesday
        next_run = schedule.calculate_next_run(from_time)
        
        # Should be next Monday at 3:00 AM
        expected = datetime(2024, 1, 22, 3, 0)
        self.assertEqual(next_run, expected)
    
    def test_schedule_serialization(self):
        """Test schedule configuration serialization."""
        schedule = ScheduleConfig(
            id="test-schedule",
            name="Test Schedule",
            description="Test export",
            interval=ScheduleInterval.DAILY,
            export_options=self.export_options,
            output_directory=self.temp_dir,
            file_format=FileFormat.JSON
        )
        
        # Convert to dict and back
        schedule_dict = schedule.to_dict()
        restored_schedule = ScheduleConfig.from_dict(schedule_dict)
        
        self.assertEqual(schedule.id, restored_schedule.id)
        self.assertEqual(schedule.name, restored_schedule.name)
        self.assertEqual(schedule.interval, restored_schedule.interval)
        self.assertEqual(schedule.file_format, restored_schedule.file_format)


class TestExportScheduler(unittest.TestCase):
    """Test export scheduler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_schedules.json")
        
        # Mock the import/export service
        self.mock_import_export_service = Mock()
        self.mock_file_manager = Mock()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('app.services.export_scheduler.ImportExportService')
    @patch('app.services.export_scheduler.get_export_file_manager')
    def test_scheduler_initialization(self, mock_get_file_manager, mock_import_export):
        """Test scheduler initialization."""
        mock_get_file_manager.return_value = self.mock_file_manager
        mock_import_export.return_value = self.mock_import_export_service
        
        scheduler = ExportScheduler(self.config_file)
        
        self.assertFalse(scheduler.is_running)
        self.assertEqual(len(scheduler.schedules), 0)
        self.assertEqual(scheduler.config_file, self.config_file)
    
    @patch('app.services.export_scheduler.ImportExportService')
    @patch('app.services.export_scheduler.get_export_file_manager')
    def test_add_schedule(self, mock_get_file_manager, mock_import_export):
        """Test adding a schedule."""
        mock_get_file_manager.return_value = self.mock_file_manager
        mock_import_export.return_value = self.mock_import_export_service
        
        scheduler = ExportScheduler(self.config_file)
        
        export_options = ExportOptions(
            entity_types=['units', 'persons'],
            include_historical=True
        )
        
        schedule = ScheduleConfig(
            id="test-schedule",
            name="Test Schedule",
            description="Test export",
            interval=ScheduleInterval.DAILY,
            export_options=export_options,
            output_directory=self.temp_dir,
            file_format=FileFormat.JSON
        )
        
        scheduler.add_schedule(schedule)
        
        self.assertEqual(len(scheduler.schedules), 1)
        self.assertIn(schedule.id, scheduler.schedules)
        self.assertIsNotNone(scheduler.schedules[schedule.id].next_run)
    
    @patch('app.services.export_scheduler.ImportExportService')
    @patch('app.services.export_scheduler.get_export_file_manager')
    def test_remove_schedule(self, mock_get_file_manager, mock_import_export):
        """Test removing a schedule."""
        mock_get_file_manager.return_value = self.mock_file_manager
        mock_import_export.return_value = self.mock_import_export_service
        
        scheduler = ExportScheduler(self.config_file)
        
        export_options = ExportOptions(
            entity_types=['units'],
            include_historical=True
        )
        
        schedule = ScheduleConfig(
            id="test-schedule",
            name="Test Schedule",
            description="Test export",
            interval=ScheduleInterval.DAILY,
            export_options=export_options,
            output_directory=self.temp_dir,
            file_format=FileFormat.JSON
        )
        
        scheduler.add_schedule(schedule)
        self.assertEqual(len(scheduler.schedules), 1)
        
        result = scheduler.remove_schedule(schedule.id)
        self.assertTrue(result)
        self.assertEqual(len(scheduler.schedules), 0)
        
        # Test removing non-existent schedule
        result = scheduler.remove_schedule("non-existent")
        self.assertFalse(result)


class TestExportFileManager(unittest.TestCase):
    """Test export file manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = ExportFileManager(
            base_directory=self.temp_dir,
            metadata_file="test_files.json"
        )
        
        # Create test files
        self.test_files = []
        for i in range(3):
            test_file = os.path.join(self.temp_dir, f"test_export_{i}.json")
            with open(test_file, 'w') as f:
                f.write(f'{{"test": "data_{i}"}}')
            self.test_files.append(test_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_register_export_files(self):
        """Test registering export files."""
        registered_files = self.file_manager.register_export_files(
            file_paths=self.test_files,
            export_id="test-export-123",
            entity_types=['units', 'persons'],
            record_count=100,
            file_format="json"
        )
        
        self.assertEqual(len(registered_files), 3)
        self.assertEqual(len(self.file_manager.file_registry), 3)
        
        # Check file info
        file_info = registered_files[0]
        self.assertEqual(file_info.export_id, "test-export-123")
        self.assertEqual(file_info.entity_types, ['units', 'persons'])
        self.assertEqual(file_info.record_count, 100)
        self.assertEqual(file_info.file_format, "json")
    
    def test_file_cleanup_by_days(self):
        """Test file cleanup by days retention policy."""
        # Register files
        self.file_manager.register_export_files(
            file_paths=self.test_files,
            export_id="test-export-123",
            entity_types=['units'],
            record_count=50,
            file_format="json"
        )
        
        # Modify creation time to make files "old"
        for file_path in self.test_files:
            file_info = self.file_manager.file_registry[file_path]
            file_info.created_at = datetime.now() - timedelta(days=35)
        
        # Create retention config for 30 days
        retention_config = FileRetentionConfig(
            policy=RetentionPolicy.DAYS,
            value=30,
            compress_before_delete=False
        )
        
        # Run cleanup
        result = self.file_manager.cleanup_old_files(retention_config)
        
        self.assertTrue(result.success)
        self.assertEqual(result.files_deleted, 3)
        self.assertEqual(len(self.file_manager.file_registry), 0)
    
    def test_file_cleanup_by_count(self):
        """Test file cleanup by count retention policy."""
        # Register files
        self.file_manager.register_export_files(
            file_paths=self.test_files,
            export_id="test-export-123",
            entity_types=['units'],
            record_count=50,
            file_format="json"
        )
        
        # Create retention config to keep only 2 files
        retention_config = FileRetentionConfig(
            policy=RetentionPolicy.COUNT,
            value=2,
            compress_before_delete=False
        )
        
        # Run cleanup
        result = self.file_manager.cleanup_old_files(retention_config)
        
        self.assertTrue(result.success)
        self.assertEqual(result.files_deleted, 1)  # Should delete 1 file (oldest)
        self.assertEqual(len(self.file_manager.file_registry), 2)
    
    def test_get_file_statistics(self):
        """Test getting file statistics."""
        # Register files
        self.file_manager.register_export_files(
            file_paths=self.test_files,
            export_id="test-export-123",
            entity_types=['units', 'persons'],
            record_count=100,
            file_format="json"
        )
        
        stats = self.file_manager.get_file_statistics()
        
        self.assertEqual(stats['total_files'], 3)
        self.assertGreater(stats['total_size_mb'], 0)
        self.assertIn('json', stats['files_by_format'])
        self.assertEqual(stats['files_by_format']['json']['count'], 3)


if __name__ == '__main__':
    unittest.main()