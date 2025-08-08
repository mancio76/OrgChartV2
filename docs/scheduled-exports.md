# Scheduled Export System

The scheduled export system provides automated data export functionality with comprehensive file management, retention policies, and notification capabilities.

## Features

### Export Scheduling Framework
- **Cron-like scheduling**: Support for daily, weekly, and monthly intervals
- **Flexible timing**: Configure specific run times and days
- **Background processing**: Non-blocking execution of export operations
- **Status tracking**: Monitor schedule status and execution history

### File Management System
- **Automatic organization**: Structured directory layout for exported files
- **File registration**: Track all exported files with metadata
- **Integrity verification**: Checksum validation for file integrity
- **Statistics reporting**: Comprehensive file usage statistics

### Retention and Cleanup
- **Multiple policies**: Retention by days, file count, or total size
- **Archive before delete**: Optional compression and archiving
- **Automatic cleanup**: Scheduled cleanup of old export files
- **Space management**: Monitor and control disk usage

### Notification System
- **Export completion**: Notifications for successful and failed exports
- **Cleanup reports**: Notifications for file cleanup operations
- **Multiple channels**: Support for email and webhook notifications
- **Configurable levels**: Control notification types and verbosity

## Requirements Implementation

This system implements the following requirements:

### Requirement 6.1, 6.2, 6.3 (Scheduled Exports)
- ✅ Daily, weekly, and monthly scheduling intervals
- ✅ Automatic file generation and storage
- ✅ Background task processing
- ✅ Error logging and administrator notifications
- ✅ File rotation and cleanup policies

## Usage

### Command Line Interface

The system includes a comprehensive CLI for managing scheduled exports:

```bash
# Show scheduler status
python scripts/manage_export_scheduler.py status

# Create a daily export schedule
python scripts/manage_export_scheduler.py create \
    "Daily Backup" daily exports/ \
    --format json \
    --entity-types "units,persons,assignments" \
    --run-time "02:00" \
    --include-historical

# List all schedules
python scripts/manage_export_scheduler.py list

# Start the scheduler
python scripts/manage_export_scheduler.py start

# Run file cleanup
python scripts/manage_export_scheduler.py cleanup \
    --policy days --value 30 --compress

# Show execution history
python scripts/manage_export_scheduler.py history --limit 10
```

### Programmatic Usage

```python
from app.services.export_scheduler import get_export_scheduler, ScheduleConfig, ScheduleInterval
from app.services.export_file_manager import get_export_file_manager
from app.models.import_export import ExportOptions, FileFormat

# Initialize scheduler
scheduler = get_export_scheduler()
scheduler.start_scheduler()

# Create export options
export_options = ExportOptions(
    entity_types=['units', 'persons', 'assignments'],
    include_historical=True,
    file_prefix='automated_backup'
)

# Create schedule
schedule = ScheduleConfig(
    name="Daily Organizational Backup",
    description="Daily export of all organizational data",
    interval=ScheduleInterval.DAILY,
    export_options=export_options,
    output_directory="exports/daily",
    file_format=FileFormat.JSON,
    run_time="02:00"
)

# Add schedule
scheduler.add_schedule(schedule)

# Get file manager
file_manager = get_export_file_manager()

# Get file statistics
stats = file_manager.get_file_statistics()
print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
```

## Configuration

### Schedule Configuration

```python
@dataclass
class ScheduleConfig:
    name: str                    # Human-readable schedule name
    description: str             # Schedule description
    interval: ScheduleInterval   # DAILY, WEEKLY, or MONTHLY
    export_options: ExportOptions # Export configuration
    output_directory: str        # Base output directory
    file_format: FileFormat      # JSON or CSV
    enabled: bool = True         # Whether schedule is active
    run_time: str = "02:00"     # Time to run (HH:MM format)
    day_of_week: int = 0        # Day for weekly (0=Monday)
    day_of_month: int = 1       # Day for monthly schedules
```

### File Retention Configuration

```python
@dataclass
class FileRetentionConfig:
    policy: RetentionPolicy           # DAYS, COUNT, or SIZE
    value: int                        # Retention value
    compress_before_delete: bool      # Archive before deletion
    compression_type: CompressionType # ZIP, TAR_GZ, or NONE
    archive_directory: str            # Archive location
```

### Notification Configuration

```python
@dataclass
class NotificationConfig:
    enabled: bool = True
    notification_types: List[NotificationType]  # SUCCESS, ERROR, WARNING, CLEANUP
    email_recipients: List[str]                 # Email addresses
    webhook_url: Optional[str]                  # Webhook endpoint
    include_file_details: bool = True           # Include file information
    include_statistics: bool = True             # Include export statistics
```

## File Organization

The system organizes exported files in a structured directory layout:

```
exports/
├── 2024-01-15/
│   ├── daily-backup/
│   │   ├── orgchart_export_20240115_020000.json
│   │   └── metadata.json
│   └── weekly-backup/
│       ├── units_20240115_030000.csv
│       ├── persons_20240115_030000.csv
│       └── assignments_20240115_030000.csv
├── 2024-01-16/
│   └── daily-backup/
│       └── orgchart_export_20240116_020000.json
└── archive/
    ├── old_export_20240101_120000.tar.gz
    └── old_export_20240102_120000.tar.gz
```

## Monitoring and Maintenance

### Status Monitoring

```bash
# Check scheduler status
python scripts/manage_export_scheduler.py status

# View execution history
python scripts/manage_export_scheduler.py history

# Get file statistics
python scripts/manage_export_scheduler.py status
```

### Maintenance Operations

```bash
# Run manual cleanup (keep files for 30 days)
python scripts/manage_export_scheduler.py cleanup --policy days --value 30

# Run cleanup by file count (keep 100 most recent files)
python scripts/manage_export_scheduler.py cleanup --policy count --value 100

# Run cleanup by size (keep total under 1GB)
python scripts/manage_export_scheduler.py cleanup --policy size --value 1024
```

### Log Files

The system logs all operations to the application log:

- Export execution status
- File management operations
- Cleanup operations
- Error conditions
- Performance metrics

## Error Handling

The system provides comprehensive error handling:

1. **Export Failures**: Logged with detailed error information
2. **File System Errors**: Graceful handling of disk space and permission issues
3. **Schedule Conflicts**: Prevention of overlapping export operations
4. **Recovery**: Automatic retry mechanisms for transient failures

## Performance Considerations

- **Memory Usage**: Streaming processing for large datasets
- **Disk Space**: Automatic cleanup and compression
- **CPU Usage**: Background processing with configurable intervals
- **Concurrency**: Thread-safe operations with proper locking

## Security

- **File Permissions**: Proper file system permissions for export directories
- **Path Validation**: Prevention of path traversal attacks
- **Access Control**: Integration with application authentication
- **Audit Trail**: Complete logging of all operations

## Integration

The scheduled export system integrates with:

- **Import/Export Service**: Core data export functionality
- **Validation Framework**: Data integrity validation
- **Audit Trail**: Operation logging and tracking
- **Error Handling**: Centralized error management
- **Configuration System**: Application-wide configuration management