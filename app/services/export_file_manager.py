"""
Export File Management System for automated file storage, rotation, and cleanup.

This module provides comprehensive file management capabilities for scheduled exports
including automatic storage organization, file rotation policies, cleanup of old files,
and notification system for export completion.

Implements Requirements 6.3, 6.4, 6.5.
"""

import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import json
import zipfile
import tarfile

from ..utils.error_handler import get_error_logger, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)


class RetentionPolicy(Enum):
    """File retention policies for export cleanup."""
    DAYS = "days"
    COUNT = "count"
    SIZE = "size"


class CompressionType(Enum):
    """Supported compression types for file archiving."""
    NONE = "none"
    ZIP = "zip"
    TAR_GZ = "tar.gz"


class NotificationType(Enum):
    """Types of notifications for export events."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    CLEANUP = "cleanup"


@dataclass
class FileRetentionConfig:
    """Configuration for file retention and cleanup policies."""
    policy: RetentionPolicy
    value: int  # Number of days, files, or MB depending on policy
    compress_before_delete: bool = False
    compression_type: CompressionType = CompressionType.TAR_GZ
    archive_directory: Optional[str] = None
    
    def __post_init__(self):
        """Validate retention configuration."""
        if self.value <= 0:
            raise ValueError("Retention value must be positive")
        
        if self.compress_before_delete and not self.archive_directory:
            raise ValueError("Archive directory must be specified when compression is enabled")


@dataclass
class NotificationConfig:
    """Configuration for export completion notifications."""
    enabled: bool = True
    notification_types: List[NotificationType] = field(default_factory=lambda: [NotificationType.SUCCESS, NotificationType.ERROR])
    email_recipients: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    log_level: str = "INFO"
    include_file_details: bool = True
    include_statistics: bool = True
    
    def __post_init__(self):
        """Validate notification configuration."""
        if self.enabled and not self.email_recipients and not self.webhook_url:
            logger.warning("Notifications enabled but no recipients or webhook configured")


@dataclass
class ExportFileInfo:
    """Information about an exported file."""
    file_path: str
    file_name: str
    file_size: int
    created_at: datetime
    export_id: str
    schedule_id: Optional[str] = None
    entity_types: List[str] = field(default_factory=list)
    record_count: int = 0
    file_format: str = "unknown"
    compressed: bool = False
    checksum: Optional[str] = None
    
    @property
    def age_days(self) -> int:
        """Calculate file age in days."""
        return (datetime.now() - self.created_at).days
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat(),
            'export_id': self.export_id,
            'schedule_id': self.schedule_id,
            'entity_types': self.entity_types,
            'record_count': self.record_count,
            'file_format': self.file_format,
            'compressed': self.compressed,
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportFileInfo':
        """Create from dictionary."""
        return cls(
            file_path=data['file_path'],
            file_name=data['file_name'],
            file_size=data['file_size'],
            created_at=datetime.fromisoformat(data['created_at']),
            export_id=data['export_id'],
            schedule_id=data.get('schedule_id'),
            entity_types=data.get('entity_types', []),
            record_count=data.get('record_count', 0),
            file_format=data.get('file_format', 'unknown'),
            compressed=data.get('compressed', False),
            checksum=data.get('checksum')
        )


@dataclass
class CleanupResult:
    """Result of a file cleanup operation."""
    files_deleted: int = 0
    files_archived: int = 0
    space_freed_mb: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Check if cleanup was successful."""
        return len(self.errors) == 0


class ExportFileManager:
    """
    Comprehensive file management system for export operations.
    
    This class provides automatic file storage organization, rotation policies,
    cleanup of old files, and notification system for export completion.
    
    Implements Requirements 6.3, 6.4, 6.5.
    """
    
    def __init__(self, base_directory: str = "exports", 
                 metadata_file: str = "export_files.json"):
        """
        Initialize the export file manager.
        
        Args:
            base_directory: Base directory for export file storage
            metadata_file: File to store export file metadata
        """
        self.base_directory = Path(base_directory)
        self.metadata_file = self.base_directory / metadata_file
        self.file_registry: Dict[str, ExportFileInfo] = {}
        self.error_logger = get_error_logger()
        
        # Default configurations
        self.default_retention_config = FileRetentionConfig(
            policy=RetentionPolicy.DAYS,
            value=30,  # Keep files for 30 days
            compress_before_delete=True,
            archive_directory=str(self.base_directory / "archive")
        )
        
        self.default_notification_config = NotificationConfig(
            enabled=True,
            notification_types=[NotificationType.SUCCESS, NotificationType.ERROR]
        )
        
        # Ensure base directory exists
        self.base_directory.mkdir(parents=True, exist_ok=True)
        
        # Load existing file registry
        self.load_file_registry()
        
        logger.info(f"ExportFileManager initialized with base directory: {self.base_directory}")
    
    def register_export_files(self, file_paths: List[str], export_id: str,
                            schedule_id: Optional[str] = None,
                            entity_types: List[str] = None,
                            record_count: int = 0,
                            file_format: str = "unknown") -> List[ExportFileInfo]:
        """
        Register exported files in the file management system.
        
        Args:
            file_paths: List of exported file paths
            export_id: Unique identifier for the export operation
            schedule_id: ID of the schedule that created the files (if applicable)
            entity_types: List of entity types included in the export
            record_count: Total number of records exported
            file_format: Format of the exported files
            
        Returns:
            List of registered file information objects
        """
        registered_files = []
        
        try:
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    logger.warning(f"File not found for registration: {file_path}")
                    continue
                
                # Calculate file checksum for integrity verification
                checksum = self._calculate_file_checksum(file_path)
                
                # Create file info
                file_info = ExportFileInfo(
                    file_path=file_path,
                    file_name=os.path.basename(file_path),
                    file_size=os.path.getsize(file_path),
                    created_at=datetime.now(),
                    export_id=export_id,
                    schedule_id=schedule_id,
                    entity_types=entity_types or [],
                    record_count=record_count,
                    file_format=file_format,
                    checksum=checksum
                )
                
                # Register in file registry
                self.file_registry[file_path] = file_info
                registered_files.append(file_info)
                
                logger.debug(f"Registered export file: {file_path} ({file_info.size_mb:.2f} MB)")
            
            # Save updated registry
            self.save_file_registry()
            
            logger.info(f"Registered {len(registered_files)} export files for operation {export_id}")
            return registered_files
        
        except Exception as e:
            logger.error(f"Error registering export files for {export_id}: {e}")
            raise
    
    def organize_export_files(self, file_paths: List[str], 
                            organization_pattern: str = "{date}/{schedule_id}") -> Dict[str, str]:
        """
        Organize export files into a structured directory layout.
        
        Args:
            file_paths: List of file paths to organize
            organization_pattern: Pattern for directory organization
                                Available variables: {date}, {schedule_id}, {export_id}, {format}
            
        Returns:
            Dictionary mapping original paths to new organized paths
        """
        organized_files = {}
        
        try:
            for file_path in file_paths:
                if file_path not in self.file_registry:
                    logger.warning(f"File not in registry, cannot organize: {file_path}")
                    continue
                
                file_info = self.file_registry[file_path]
                
                # Build organization path
                date_str = file_info.created_at.strftime("%Y-%m-%d")
                
                # Replace pattern variables
                org_path = organization_pattern.format(
                    date=date_str,
                    schedule_id=file_info.schedule_id or "manual",
                    export_id=file_info.export_id,
                    format=file_info.file_format
                )
                
                # Create target directory
                target_dir = self.base_directory / org_path
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file to organized location
                target_path = target_dir / file_info.file_name
                
                if file_path != str(target_path):
                    shutil.move(file_path, target_path)
                    
                    # Update registry with new path
                    del self.file_registry[file_path]
                    file_info.file_path = str(target_path)
                    self.file_registry[str(target_path)] = file_info
                    
                    organized_files[file_path] = str(target_path)
                    logger.debug(f"Organized file: {file_path} -> {target_path}")
            
            # Save updated registry
            self.save_file_registry()
            
            logger.info(f"Organized {len(organized_files)} export files")
            return organized_files
        
        except Exception as e:
            logger.error(f"Error organizing export files: {e}")
            raise
    
    def cleanup_old_files(self, retention_config: Optional[FileRetentionConfig] = None) -> CleanupResult:
        """
        Clean up old export files based on retention policy.
        
        Args:
            retention_config: Retention configuration (uses default if not provided)
            
        Returns:
            CleanupResult with cleanup statistics
        """
        if retention_config is None:
            retention_config = self.default_retention_config
        
        result = CleanupResult()
        
        try:
            logger.info(f"Starting file cleanup with policy: {retention_config.policy.value}={retention_config.value}")
            
            # Get files to clean up based on policy
            files_to_cleanup = self._identify_files_for_cleanup(retention_config)
            
            if not files_to_cleanup:
                logger.info("No files identified for cleanup")
                return result
            
            # Create archive directory if compression is enabled
            if retention_config.compress_before_delete:
                archive_dir = Path(retention_config.archive_directory)
                archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each file for cleanup
            for file_info in files_to_cleanup:
                try:
                    if not os.path.exists(file_info.file_path):
                        logger.warning(f"File not found during cleanup: {file_info.file_path}")
                        # Remove from registry
                        if file_info.file_path in self.file_registry:
                            del self.file_registry[file_info.file_path]
                        continue
                    
                    file_size_mb = file_info.size_mb
                    
                    if retention_config.compress_before_delete:
                        # Archive file before deletion
                        archive_path = self._archive_file(file_info, retention_config)
                        if archive_path:
                            result.files_archived += 1
                            logger.debug(f"Archived file: {file_info.file_path} -> {archive_path}")
                    
                    # Delete original file
                    os.remove(file_info.file_path)
                    result.files_deleted += 1
                    result.space_freed_mb += file_size_mb
                    
                    # Remove from registry
                    if file_info.file_path in self.file_registry:
                        del self.file_registry[file_info.file_path]
                    
                    logger.debug(f"Deleted file: {file_info.file_path} ({file_size_mb:.2f} MB)")
                
                except Exception as e:
                    error_msg = f"Error cleaning up file {file_info.file_path}: {str(e)}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Save updated registry
            self.save_file_registry()
            
            # Send cleanup notification
            self._send_cleanup_notification(result, retention_config)
            
            logger.info(f"Cleanup completed: {result.files_deleted} files deleted, "
                       f"{result.files_archived} files archived, "
                       f"{result.space_freed_mb:.2f} MB freed")
            
            return result
        
        except Exception as e:
            error_msg = f"Error during file cleanup: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result
    
    def _identify_files_for_cleanup(self, retention_config: FileRetentionConfig) -> List[ExportFileInfo]:
        """
        Identify files that should be cleaned up based on retention policy.
        
        Args:
            retention_config: Retention configuration
            
        Returns:
            List of files to clean up
        """
        files_to_cleanup = []
        
        if retention_config.policy == RetentionPolicy.DAYS:
            # Clean up files older than specified days
            cutoff_date = datetime.now() - timedelta(days=retention_config.value)
            files_to_cleanup = [
                file_info for file_info in self.file_registry.values()
                if file_info.created_at < cutoff_date
            ]
        
        elif retention_config.policy == RetentionPolicy.COUNT:
            # Keep only the most recent N files
            sorted_files = sorted(
                self.file_registry.values(),
                key=lambda f: f.created_at,
                reverse=True
            )
            if len(sorted_files) > retention_config.value:
                files_to_cleanup = sorted_files[retention_config.value:]
        
        elif retention_config.policy == RetentionPolicy.SIZE:
            # Clean up oldest files until total size is under limit
            total_size_mb = sum(f.size_mb for f in self.file_registry.values())
            limit_mb = retention_config.value
            
            if total_size_mb > limit_mb:
                # Sort by creation date (oldest first)
                sorted_files = sorted(
                    self.file_registry.values(),
                    key=lambda f: f.created_at
                )
                
                current_size_mb = total_size_mb
                for file_info in sorted_files:
                    if current_size_mb <= limit_mb:
                        break
                    files_to_cleanup.append(file_info)
                    current_size_mb -= file_info.size_mb
        
        return files_to_cleanup
    
    def _archive_file(self, file_info: ExportFileInfo, 
                     retention_config: FileRetentionConfig) -> Optional[str]:
        """
        Archive a file before deletion.
        
        Args:
            file_info: Information about the file to archive
            retention_config: Retention configuration
            
        Returns:
            Path to the archived file or None if archiving failed
        """
        try:
            archive_dir = Path(retention_config.archive_directory)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if retention_config.compression_type == CompressionType.ZIP:
                archive_name = f"{file_info.export_id}_{timestamp}.zip"
                archive_path = archive_dir / archive_name
                
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(file_info.file_path, file_info.file_name)
            
            elif retention_config.compression_type == CompressionType.TAR_GZ:
                archive_name = f"{file_info.export_id}_{timestamp}.tar.gz"
                archive_path = archive_dir / archive_name
                
                with tarfile.open(archive_path, 'w:gz') as tarf:
                    tarf.add(file_info.file_path, arcname=file_info.file_name)
            
            else:
                # No compression - just copy to archive directory
                archive_name = f"{file_info.export_id}_{timestamp}_{file_info.file_name}"
                archive_path = archive_dir / archive_name
                shutil.copy2(file_info.file_path, archive_path)
            
            return str(archive_path)
        
        except Exception as e:
            logger.error(f"Error archiving file {file_info.file_path}: {e}")
            return None
    
    def send_export_notification(self, export_result, notification_config: Optional[NotificationConfig] = None):
        """
        Send notification about export completion.
        
        Args:
            export_result: Result of the export operation
            notification_config: Notification configuration (uses default if not provided)
        """
        if notification_config is None:
            notification_config = self.default_notification_config
        
        if not notification_config.enabled:
            return
        
        try:
            # Determine notification type
            if export_result.success:
                notification_type = NotificationType.SUCCESS
            else:
                notification_type = NotificationType.ERROR
            
            if notification_type not in notification_config.notification_types:
                return
            
            # Build notification message
            message = self._build_notification_message(export_result, notification_type, notification_config)
            
            # Send notification
            self._send_notification(message, notification_type, notification_config)
            
            logger.info(f"Sent export notification: {notification_type.value}")
        
        except Exception as e:
            logger.error(f"Error sending export notification: {e}")
    
    def _send_cleanup_notification(self, cleanup_result: CleanupResult, 
                                 retention_config: FileRetentionConfig):
        """Send notification about cleanup operation."""
        try:
            notification_type = NotificationType.CLEANUP
            
            message = {
                'type': 'cleanup',
                'timestamp': datetime.now().isoformat(),
                'files_deleted': cleanup_result.files_deleted,
                'files_archived': cleanup_result.files_archived,
                'space_freed_mb': cleanup_result.space_freed_mb,
                'retention_policy': retention_config.policy.value,
                'retention_value': retention_config.value,
                'errors': cleanup_result.errors,
                'warnings': cleanup_result.warnings
            }
            
            # Log cleanup result
            if cleanup_result.success:
                logger.info(f"File cleanup completed: {cleanup_result.files_deleted} files deleted, "
                           f"{cleanup_result.space_freed_mb:.2f} MB freed")
            else:
                logger.warning(f"File cleanup completed with errors: {len(cleanup_result.errors)} errors")
        
        except Exception as e:
            logger.error(f"Error sending cleanup notification: {e}")
    
    def _build_notification_message(self, export_result, notification_type: NotificationType,
                                  notification_config: NotificationConfig) -> Dict[str, Any]:
        """Build notification message content."""
        message = {
            'type': notification_type.value,
            'timestamp': datetime.now().isoformat(),
            'success': export_result.success,
            'execution_time': export_result.execution_time
        }
        
        if notification_config.include_statistics:
            message.update({
                'total_exported': export_result.total_exported,
                'records_exported': export_result.records_exported,
                'error_count': len(export_result.errors),
                'warning_count': len(export_result.warnings)
            })
        
        if notification_config.include_file_details:
            message.update({
                'exported_files': export_result.exported_files,
                'file_sizes': export_result.file_sizes,
                'total_file_size': export_result.total_file_size
            })
        
        if not export_result.success:
            message['errors'] = [str(error) for error in export_result.errors[:5]]  # Limit error details
        
        return message
    
    def _send_notification(self, message: Dict[str, Any], notification_type: NotificationType,
                         notification_config: NotificationConfig):
        """Send notification via configured channels."""
        # For now, just log the notification
        # In a real implementation, this would send emails, webhooks, etc.
        
        log_level = getattr(logging, notification_config.log_level.upper(), logging.INFO)
        logger.log(log_level, f"Export notification ({notification_type.value}): {json.dumps(message, indent=2)}")
        
        # TODO: Implement actual email/webhook notifications
        if notification_config.email_recipients:
            logger.debug(f"Would send email to: {notification_config.email_recipients}")
        
        if notification_config.webhook_url:
            logger.debug(f"Would send webhook to: {notification_config.webhook_url}")
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum for file integrity verification."""
        import hashlib
        
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    def load_file_registry(self):
        """Load file registry from metadata file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for file_path, file_data in data.get('files', {}).items():
                    try:
                        file_info = ExportFileInfo.from_dict(file_data)
                        self.file_registry[file_path] = file_info
                    except Exception as e:
                        logger.warning(f"Error loading file info for {file_path}: {e}")
                
                logger.info(f"Loaded {len(self.file_registry)} files from registry")
            else:
                logger.info("No existing file registry found")
        
        except Exception as e:
            logger.error(f"Error loading file registry: {e}")
    
    def save_file_registry(self):
        """Save file registry to metadata file."""
        try:
            data = {
                'files': {
                    file_path: file_info.to_dict()
                    for file_path, file_info in self.file_registry.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved file registry with {len(self.file_registry)} files")
        
        except Exception as e:
            logger.error(f"Error saving file registry: {e}")
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """Get statistics about managed export files."""
        if not self.file_registry:
            return {
                'total_files': 0,
                'total_size_mb': 0.0,
                'oldest_file': None,
                'newest_file': None,
                'files_by_format': {},
                'files_by_schedule': {}
            }
        
        files = list(self.file_registry.values())
        
        # Calculate statistics
        total_size_mb = sum(f.size_mb for f in files)
        oldest_file = min(files, key=lambda f: f.created_at)
        newest_file = max(files, key=lambda f: f.created_at)
        
        # Group by format
        files_by_format = {}
        for file_info in files:
            format_name = file_info.file_format
            if format_name not in files_by_format:
                files_by_format[format_name] = {'count': 0, 'size_mb': 0.0}
            files_by_format[format_name]['count'] += 1
            files_by_format[format_name]['size_mb'] += file_info.size_mb
        
        # Group by schedule
        files_by_schedule = {}
        for file_info in files:
            schedule_id = file_info.schedule_id or 'manual'
            if schedule_id not in files_by_schedule:
                files_by_schedule[schedule_id] = {'count': 0, 'size_mb': 0.0}
            files_by_schedule[schedule_id]['count'] += 1
            files_by_schedule[schedule_id]['size_mb'] += file_info.size_mb
        
        return {
            'total_files': len(files),
            'total_size_mb': total_size_mb,
            'oldest_file': {
                'path': oldest_file.file_path,
                'created_at': oldest_file.created_at.isoformat(),
                'age_days': oldest_file.age_days
            },
            'newest_file': {
                'path': newest_file.file_path,
                'created_at': newest_file.created_at.isoformat(),
                'age_days': newest_file.age_days
            },
            'files_by_format': files_by_format,
            'files_by_schedule': files_by_schedule
        }
    
    def verify_file_integrity(self) -> Dict[str, Any]:
        """Verify integrity of all managed files."""
        verification_result = {
            'total_files': len(self.file_registry),
            'verified_files': 0,
            'missing_files': 0,
            'corrupted_files': 0,
            'errors': []
        }
        
        for file_path, file_info in self.file_registry.items():
            try:
                if not os.path.exists(file_path):
                    verification_result['missing_files'] += 1
                    verification_result['errors'].append(f"Missing file: {file_path}")
                    continue
                
                # Verify file size
                current_size = os.path.getsize(file_path)
                if current_size != file_info.file_size:
                    verification_result['corrupted_files'] += 1
                    verification_result['errors'].append(
                        f"Size mismatch for {file_path}: expected {file_info.file_size}, got {current_size}"
                    )
                    continue
                
                # Verify checksum if available
                if file_info.checksum:
                    current_checksum = self._calculate_file_checksum(file_path)
                    if current_checksum != file_info.checksum:
                        verification_result['corrupted_files'] += 1
                        verification_result['errors'].append(f"Checksum mismatch for {file_path}")
                        continue
                
                verification_result['verified_files'] += 1
            
            except Exception as e:
                verification_result['errors'].append(f"Error verifying {file_path}: {str(e)}")
        
        return verification_result


# Global file manager instance
_file_manager_instance: Optional[ExportFileManager] = None


def get_export_file_manager() -> ExportFileManager:
    """Get the global export file manager instance."""
    global _file_manager_instance
    if _file_manager_instance is None:
        _file_manager_instance = ExportFileManager()
    return _file_manager_instance


def initialize_export_file_manager(base_directory: str = "exports",
                                 metadata_file: str = "export_files.json") -> ExportFileManager:
    """
    Initialize the global export file manager.
    
    Args:
        base_directory: Base directory for export file storage
        metadata_file: File to store export file metadata
        
    Returns:
        Initialized file manager instance
    """
    global _file_manager_instance
    _file_manager_instance = ExportFileManager(base_directory, metadata_file)
    return _file_manager_instance