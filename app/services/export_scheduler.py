"""
Export Scheduling Framework for automated data exports.

This module implements a cron-like scheduling system for automated exports
with support for daily, weekly, and monthly intervals. It provides background
task processing and configuration management for scheduled export operations.

Implements Requirements 6.1, 6.2, 6.3.
"""

import logging
import os
import threading
import time
import uuid
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import json

from ..database import get_db_manager
from ..models.import_export import ExportOptions, ExportResult, FileFormat
from ..utils.error_handler import get_error_logger, ErrorSeverity, ErrorCategory
from .import_export import ImportExportService
from .export_file_manager import get_export_file_manager, FileRetentionConfig, NotificationConfig

logger = logging.getLogger(__name__)


class ScheduleInterval(Enum):
    """Supported scheduling intervals."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ScheduleStatus(Enum):
    """Status of scheduled export jobs."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RUNNING = "running"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled export."""
    id: str
    name: str
    description: str
    interval: ScheduleInterval
    export_options: ExportOptions
    output_directory: str
    file_format: FileFormat
    enabled: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    last_status: ScheduleStatus = ScheduleStatus.INACTIVE
    last_error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Schedule-specific options
    run_time: str = "02:00"  # HH:MM format for daily/weekly/monthly runs
    day_of_week: int = 0  # 0=Monday for weekly schedules
    day_of_month: int = 1  # Day of month for monthly schedules
    
    def __post_init__(self):
        """Validate schedule configuration after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.output_directory:
            raise ValueError("Output directory must be specified")
        
        # Validate run_time format
        try:
            time.strptime(self.run_time, "%H:%M")
        except ValueError:
            raise ValueError("run_time must be in HH:MM format")
        
        # Validate day_of_week for weekly schedules
        if self.interval == ScheduleInterval.WEEKLY and not (0 <= self.day_of_week <= 6):
            raise ValueError("day_of_week must be between 0 (Monday) and 6 (Sunday)")
        
        # Validate day_of_month for monthly schedules
        if self.interval == ScheduleInterval.MONTHLY and not (1 <= self.day_of_month <= 31):
            raise ValueError("day_of_month must be between 1 and 31")
    
    def calculate_next_run(self, from_time: Optional[datetime] = None) -> datetime:
        """
        Calculate the next scheduled run time.
        
        Args:
            from_time: Base time to calculate from (defaults to now)
            
        Returns:
            Next scheduled run datetime
        """
        if from_time is None:
            from_time = datetime.now()
        
        # Parse run time
        run_hour, run_minute = map(int, self.run_time.split(':'))
        
        if self.interval == ScheduleInterval.DAILY:
            # Next run is tomorrow at the specified time
            next_run = from_time.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
            if next_run <= from_time:
                next_run += timedelta(days=1)
            return next_run
        
        elif self.interval == ScheduleInterval.WEEKLY:
            # Next run is on the specified day of week at the specified time
            days_ahead = self.day_of_week - from_time.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_run = from_time + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
            return next_run
        
        elif self.interval == ScheduleInterval.MONTHLY:
            # Next run is on the specified day of month at the specified time
            next_run = from_time.replace(day=self.day_of_month, hour=run_hour, minute=run_minute, second=0, microsecond=0)
            
            # If the target day has already passed this month, move to next month
            if next_run <= from_time:
                if from_time.month == 12:
                    next_run = next_run.replace(year=from_time.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=from_time.month + 1)
            
            # Handle months with fewer days (e.g., February 30th -> February 28th)
            try:
                next_run = next_run.replace(day=self.day_of_month)
            except ValueError:
                # Day doesn't exist in target month, use last day of month
                if next_run.month == 2:
                    # February - handle leap years
                    if next_run.year % 4 == 0 and (next_run.year % 100 != 0 or next_run.year % 400 == 0):
                        next_run = next_run.replace(day=29)
                    else:
                        next_run = next_run.replace(day=28)
                elif next_run.month in [4, 6, 9, 11]:
                    # Months with 30 days
                    next_run = next_run.replace(day=30)
                else:
                    # Months with 31 days
                    next_run = next_run.replace(day=31)
            
            return next_run
        
        else:
            raise ValueError(f"Unsupported interval: {self.interval}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule config to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'interval': self.interval.value,
            'export_options': {
                'entity_types': self.export_options.entity_types,
                'include_historical': self.export_options.include_historical,
                'date_range': [self.export_options.date_range[0].isoformat(), 
                              self.export_options.date_range[1].isoformat()] if self.export_options.date_range else None,
                'format_options': self.export_options.format_options,
                'output_directory': self.export_options.output_directory,
                'file_prefix': self.export_options.file_prefix,
                'include_metadata': self.export_options.include_metadata,
                'compress_output': self.export_options.compress_output,
                'split_by_entity': self.export_options.split_by_entity,
                'encoding': self.export_options.encoding,
                'csv_delimiter': self.export_options.csv_delimiter,
                'csv_quote_char': self.export_options.csv_quote_char,
                'json_indent': self.export_options.json_indent,
                'include_empty_fields': self.export_options.include_empty_fields
            },
            'output_directory': self.output_directory,
            'file_format': self.file_format.value,
            'enabled': self.enabled,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_status': self.last_status.value,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'run_time': self.run_time,
            'day_of_week': self.day_of_week,
            'day_of_month': self.day_of_month
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleConfig':
        """Create schedule config from dictionary."""
        # Parse export options
        export_opts_data = data['export_options']
        date_range = None
        if export_opts_data.get('date_range'):
            date_range = (
                date.fromisoformat(export_opts_data['date_range'][0]),
                date.fromisoformat(export_opts_data['date_range'][1])
            )
        
        export_options = ExportOptions(
            entity_types=export_opts_data['entity_types'],
            include_historical=export_opts_data.get('include_historical', True),
            date_range=date_range,
            format_options=export_opts_data.get('format_options', {}),
            output_directory=export_opts_data.get('output_directory'),
            file_prefix=export_opts_data.get('file_prefix', 'orgchart_export'),
            include_metadata=export_opts_data.get('include_metadata', True),
            compress_output=export_opts_data.get('compress_output', False),
            split_by_entity=export_opts_data.get('split_by_entity', True),
            encoding=export_opts_data.get('encoding', 'utf-8'),
            csv_delimiter=export_opts_data.get('csv_delimiter', ','),
            csv_quote_char=export_opts_data.get('csv_quote_char', '"'),
            json_indent=export_opts_data.get('json_indent', 2),
            include_empty_fields=export_opts_data.get('include_empty_fields', False)
        )
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            interval=ScheduleInterval(data['interval']),
            export_options=export_options,
            output_directory=data['output_directory'],
            file_format=FileFormat(data['file_format']),
            enabled=data.get('enabled', True),
            next_run=datetime.fromisoformat(data['next_run']) if data.get('next_run') else None,
            last_run=datetime.fromisoformat(data['last_run']) if data.get('last_run') else None,
            last_status=ScheduleStatus(data.get('last_status', 'inactive')),
            last_error=data.get('last_error'),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            run_time=data.get('run_time', '02:00'),
            day_of_week=data.get('day_of_week', 0),
            day_of_month=data.get('day_of_month', 1)
        )


@dataclass
class ScheduleExecutionResult:
    """Result of a scheduled export execution."""
    schedule_id: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    export_result: Optional[ExportResult] = None
    error_message: Optional[str] = None
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate execution duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None


class ExportScheduler:
    """
    Export scheduling framework with cron-like functionality.
    
    This class provides comprehensive scheduling capabilities for automated exports
    with support for daily, weekly, and monthly intervals. It manages background
    task processing and maintains schedule configurations.
    
    Implements Requirements 6.1, 6.2, 6.3.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the export scheduler.
        
        Args:
            config_file: Path to schedule configuration file
        """
        self.config_file = config_file or "config/export_schedules.json"
        self.schedules: Dict[str, ScheduleConfig] = {}
        self.running_jobs: Dict[str, threading.Thread] = {}
        self.scheduler_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.check_interval = 60  # Check for due jobs every 60 seconds
        
        # Services
        self.import_export_service = ImportExportService()
        self.file_manager = get_export_file_manager()
        self.error_logger = get_error_logger()
        
        # Execution history
        self.execution_history: List[ScheduleExecutionResult] = []
        self.max_history_size = 1000
        
        logger.info("ExportScheduler initialized")
        
        # Load existing schedules
        self.load_schedules()
    
    def add_schedule(self, schedule: ScheduleConfig) -> None:
        """
        Add a new export schedule.
        
        Args:
            schedule: Schedule configuration to add
        """
        try:
            # Validate schedule
            if not schedule.id:
                schedule.id = str(uuid.uuid4())
            
            # Calculate next run time
            schedule.next_run = schedule.calculate_next_run()
            schedule.updated_at = datetime.now()
            
            # Ensure output directory exists
            os.makedirs(schedule.output_directory, exist_ok=True)
            
            # Add to schedules
            self.schedules[schedule.id] = schedule
            
            # Save schedules
            self.save_schedules()
            
            logger.info(f"Added export schedule: {schedule.name} ({schedule.id})")
            logger.debug(f"Next run scheduled for: {schedule.next_run}")
        
        except Exception as e:
            logger.error(f"Error adding schedule {schedule.name}: {e}")
            raise
    
    def remove_schedule(self, schedule_id: str) -> bool:
        """
        Remove an export schedule.
        
        Args:
            schedule_id: ID of schedule to remove
            
        Returns:
            True if schedule was removed, False if not found
        """
        try:
            if schedule_id in self.schedules:
                schedule_name = self.schedules[schedule_id].name
                del self.schedules[schedule_id]
                self.save_schedules()
                logger.info(f"Removed export schedule: {schedule_name} ({schedule_id})")
                return True
            else:
                logger.warning(f"Schedule not found for removal: {schedule_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error removing schedule {schedule_id}: {e}")
            raise
    
    def update_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing export schedule.
        
        Args:
            schedule_id: ID of schedule to update
            updates: Dictionary of fields to update
            
        Returns:
            True if schedule was updated, False if not found
        """
        try:
            if schedule_id not in self.schedules:
                logger.warning(f"Schedule not found for update: {schedule_id}")
                return False
            
            schedule = self.schedules[schedule_id]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(schedule, field):
                    setattr(schedule, field, value)
            
            # Recalculate next run if interval or timing changed
            if any(field in updates for field in ['interval', 'run_time', 'day_of_week', 'day_of_month']):
                schedule.next_run = schedule.calculate_next_run()
            
            schedule.updated_at = datetime.now()
            
            # Save schedules
            self.save_schedules()
            
            logger.info(f"Updated export schedule: {schedule.name} ({schedule_id})")
            return True
        
        except Exception as e:
            logger.error(f"Error updating schedule {schedule_id}: {e}")
            raise
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduleConfig]:
        """
        Get a schedule by ID.
        
        Args:
            schedule_id: ID of schedule to retrieve
            
        Returns:
            Schedule configuration or None if not found
        """
        return self.schedules.get(schedule_id)
    
    def list_schedules(self, enabled_only: bool = False) -> List[ScheduleConfig]:
        """
        List all schedules.
        
        Args:
            enabled_only: If True, only return enabled schedules
            
        Returns:
            List of schedule configurations
        """
        schedules = list(self.schedules.values())
        if enabled_only:
            schedules = [s for s in schedules if s.enabled]
        return schedules
    
    def start_scheduler(self) -> None:
        """Start the background scheduler thread."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Export scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the background scheduler thread."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.is_running = False
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
        
        # Wait for running jobs to finish
        for job_id, thread in list(self.running_jobs.items()):
            if thread.is_alive():
                logger.info(f"Waiting for job {job_id} to finish...")
                thread.join(timeout=30)
                if thread.is_alive():
                    logger.warning(f"Job {job_id} did not finish within timeout")
        
        logger.info("Export scheduler stopped")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop that checks for due jobs."""
        logger.info("Scheduler loop started")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check each schedule for due jobs
                for schedule_id, schedule in list(self.schedules.items()):
                    if not schedule.enabled:
                        continue
                    
                    if schedule.next_run and current_time >= schedule.next_run:
                        # Job is due - execute it
                        if schedule_id not in self.running_jobs:
                            logger.info(f"Starting scheduled export: {schedule.name} ({schedule_id})")
                            self._execute_scheduled_export(schedule)
                        else:
                            logger.warning(f"Skipping scheduled export {schedule.name} - previous execution still running")
                
                # Clean up finished jobs
                self._cleanup_finished_jobs()
                
                # Sleep until next check
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(self.check_interval)
        
        logger.info("Scheduler loop stopped")
    
    def _execute_scheduled_export(self, schedule: ScheduleConfig) -> None:
        """
        Execute a scheduled export in a background thread.
        
        Args:
            schedule: Schedule configuration to execute
        """
        def run_export():
            execution_id = str(uuid.uuid4())
            execution_result = ScheduleExecutionResult(
                schedule_id=schedule.id,
                execution_id=execution_id,
                start_time=datetime.now()
            )
            
            try:
                logger.info(f"Executing scheduled export: {schedule.name}")
                
                # Update schedule status
                schedule.last_status = ScheduleStatus.RUNNING
                schedule.last_run = datetime.now()
                
                # Create timestamped output directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join(schedule.output_directory, f"export_{timestamp}")
                os.makedirs(output_dir, exist_ok=True)
                
                # Update export options with timestamped directory
                export_options = schedule.export_options
                export_options.output_directory = output_dir
                
                # Execute export
                if schedule.file_format == FileFormat.JSON:
                    export_result = self.import_export_service.export_data_json(export_options)
                else:  # CSV
                    export_result = self.import_export_service.export_data_csv(export_options)
                
                # Update execution result
                execution_result.success = export_result.success
                execution_result.export_result = export_result
                execution_result.end_time = datetime.now()
                
                if export_result.success:
                    schedule.last_status = ScheduleStatus.COMPLETED
                    schedule.last_error = None
                    
                    # Register files with file manager
                    try:
                        registered_files = self.file_manager.register_export_files(
                            file_paths=export_result.exported_files,
                            export_id=execution_id,
                            schedule_id=schedule.id,
                            entity_types=export_options.entity_types,
                            record_count=export_result.total_exported,
                            file_format=schedule.file_format.value
                        )
                        
                        # Organize files if needed
                        if len(registered_files) > 0:
                            self.file_manager.organize_export_files(
                                export_result.exported_files,
                                organization_pattern="{date}/{schedule_id}"
                            )
                        
                        # Send success notification
                        self.file_manager.send_export_notification(export_result)
                        
                        logger.info(f"Scheduled export completed successfully: {schedule.name}")
                        logger.info(f"Exported {export_result.total_exported} records to {len(export_result.exported_files)} files")
                        
                    except Exception as file_mgmt_error:
                        logger.warning(f"Export succeeded but file management failed: {file_mgmt_error}")
                else:
                    schedule.last_status = ScheduleStatus.ERROR
                    error_msg = f"Export failed with {len(export_result.errors)} errors"
                    schedule.last_error = error_msg
                    execution_result.error_message = error_msg
                    
                    # Send error notification
                    try:
                        self.file_manager.send_export_notification(export_result)
                    except Exception as notification_error:
                        logger.warning(f"Failed to send error notification: {notification_error}")
                    
                    logger.error(f"Scheduled export failed: {schedule.name} - {error_msg}")
            
            except Exception as e:
                execution_result.success = False
                execution_result.error_message = str(e)
                execution_result.end_time = datetime.now()
                
                schedule.last_status = ScheduleStatus.ERROR
                schedule.last_error = str(e)
                
                logger.error(f"Error executing scheduled export {schedule.name}: {e}")
                
                # Log error for monitoring
                self.error_logger.log_error(
                    error=e,
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.SYSTEM,
                    context={
                        'operation': 'scheduled_export',
                        'schedule_id': schedule.id,
                        'schedule_name': schedule.name,
                        'execution_id': execution_id
                    }
                )
            
            finally:
                # Calculate next run time
                schedule.next_run = schedule.calculate_next_run()
                
                # Save updated schedule
                self.save_schedules()
                
                # Add to execution history
                self.execution_history.append(execution_result)
                if len(self.execution_history) > self.max_history_size:
                    self.execution_history = self.execution_history[-self.max_history_size:]
                
                # Remove from running jobs
                if schedule.id in self.running_jobs:
                    del self.running_jobs[schedule.id]
        
        # Start export in background thread
        thread = threading.Thread(target=run_export, daemon=True)
        self.running_jobs[schedule.id] = thread
        thread.start()
    
    def _cleanup_finished_jobs(self) -> None:
        """Clean up finished job threads."""
        finished_jobs = []
        for job_id, thread in self.running_jobs.items():
            if not thread.is_alive():
                finished_jobs.append(job_id)
        
        for job_id in finished_jobs:
            del self.running_jobs[job_id]
    
    def load_schedules(self) -> None:
        """Load schedules from configuration file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for schedule_data in data.get('schedules', []):
                    try:
                        schedule = ScheduleConfig.from_dict(schedule_data)
                        self.schedules[schedule.id] = schedule
                    except Exception as e:
                        logger.error(f"Error loading schedule {schedule_data.get('id', 'unknown')}: {e}")
                
                logger.info(f"Loaded {len(self.schedules)} export schedules from {self.config_file}")
            else:
                logger.info(f"No existing schedule configuration found at {self.config_file}")
        
        except Exception as e:
            logger.error(f"Error loading schedules from {self.config_file}: {e}")
    
    def save_schedules(self) -> None:
        """Save schedules to configuration file."""
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Prepare data for serialization
            data = {
                'schedules': [schedule.to_dict() for schedule in self.schedules.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            # Write to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(self.schedules)} export schedules to {self.config_file}")
        
        except Exception as e:
            logger.error(f"Error saving schedules to {self.config_file}: {e}")
            raise
    
    def get_execution_history(self, schedule_id: Optional[str] = None, 
                            limit: Optional[int] = None) -> List[ScheduleExecutionResult]:
        """
        Get execution history for schedules.
        
        Args:
            schedule_id: Filter by specific schedule ID (optional)
            limit: Maximum number of results to return (optional)
            
        Returns:
            List of execution results
        """
        history = self.execution_history
        
        if schedule_id:
            history = [r for r in history if r.schedule_id == schedule_id]
        
        # Sort by start time (most recent first)
        history = sorted(history, key=lambda r: r.start_time, reverse=True)
        
        if limit:
            history = history[:limit]
        
        return history
    
    def run_file_cleanup(self, retention_config: Optional[FileRetentionConfig] = None) -> Dict[str, Any]:
        """
        Run file cleanup operation manually.
        
        Args:
            retention_config: Custom retention configuration (optional)
            
        Returns:
            Dictionary containing cleanup results
        """
        try:
            logger.info("Starting manual file cleanup operation")
            
            cleanup_result = self.file_manager.cleanup_old_files(retention_config)
            
            result = {
                'success': cleanup_result.success,
                'files_deleted': cleanup_result.files_deleted,
                'files_archived': cleanup_result.files_archived,
                'space_freed_mb': cleanup_result.space_freed_mb,
                'errors': cleanup_result.errors,
                'warnings': cleanup_result.warnings
            }
            
            logger.info(f"Manual file cleanup completed: {cleanup_result.files_deleted} files deleted, "
                       f"{cleanup_result.space_freed_mb:.2f} MB freed")
            
            return result
        
        except Exception as e:
            logger.error(f"Error in manual file cleanup: {e}")
            return {
                'success': False,
                'files_deleted': 0,
                'files_archived': 0,
                'space_freed_mb': 0.0,
                'errors': [str(e)],
                'warnings': []
            }
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about managed export files.
        
        Returns:
            Dictionary containing file statistics
        """
        try:
            return self.file_manager.get_file_statistics()
        except Exception as e:
            logger.error(f"Error getting file statistics: {e}")
            return {
                'total_files': 0,
                'total_size_mb': 0.0,
                'error': str(e)
            }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status information.
        
        Returns:
            Dictionary containing scheduler status
        """
        file_stats = self.get_file_statistics()
        
        return {
            'is_running': self.is_running,
            'total_schedules': len(self.schedules),
            'enabled_schedules': len([s for s in self.schedules.values() if s.enabled]),
            'running_jobs': len(self.running_jobs),
            'check_interval': self.check_interval,
            'execution_history_size': len(self.execution_history),
            'file_statistics': file_stats,
            'next_scheduled_runs': [
                {
                    'schedule_id': s.id,
                    'schedule_name': s.name,
                    'next_run': s.next_run.isoformat() if s.next_run else None
                }
                for s in sorted(self.schedules.values(), key=lambda x: x.next_run or datetime.max)
                if s.enabled and s.next_run
            ][:5]  # Next 5 scheduled runs
        }


# Global scheduler instance
_scheduler_instance: Optional[ExportScheduler] = None


def get_export_scheduler() -> ExportScheduler:
    """Get the global export scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ExportScheduler()
    return _scheduler_instance


def initialize_export_scheduler(config_file: Optional[str] = None, 
                              auto_start: bool = True) -> ExportScheduler:
    """
    Initialize the global export scheduler.
    
    Args:
        config_file: Path to schedule configuration file
        auto_start: Whether to automatically start the scheduler
        
    Returns:
        Initialized scheduler instance
    """
    global _scheduler_instance
    _scheduler_instance = ExportScheduler(config_file)
    
    if auto_start:
        _scheduler_instance.start_scheduler()
    
    return _scheduler_instance