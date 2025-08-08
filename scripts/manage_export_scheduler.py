#!/usr/bin/env python3
"""
CLI script for managing the export scheduler.

This script provides command-line interface for managing scheduled exports,
including creating schedules, monitoring status, and running cleanup operations.
"""

import argparse
import json
import sys
from datetime import datetime, date
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.export_scheduler import (
    get_export_scheduler, initialize_export_scheduler,
    ScheduleConfig, ScheduleInterval, ScheduleStatus
)
from app.services.export_file_manager import (
    get_export_file_manager, FileRetentionConfig, RetentionPolicy, CompressionType
)
from app.models.import_export import ExportOptions, FileFormat


def create_schedule(args):
    """Create a new export schedule."""
    try:
        # Parse entity types
        entity_types = args.entity_types.split(',') if args.entity_types else ['units', 'persons', 'assignments']
        
        # Create export options
        export_options = ExportOptions(
            entity_types=entity_types,
            include_historical=args.include_historical,
            file_prefix=args.file_prefix or "scheduled_export",
            include_metadata=True,
            compress_output=args.compress,
            split_by_entity=args.split_by_entity
        )
        
        # Create schedule config
        schedule = ScheduleConfig(
            id="",  # Will be auto-generated
            name=args.name,
            description=args.description or f"Scheduled {args.interval} export",
            interval=ScheduleInterval(args.interval),
            export_options=export_options,
            output_directory=args.output_dir,
            file_format=FileFormat(args.format),
            enabled=not args.disabled,
            run_time=args.run_time,
            day_of_week=args.day_of_week,
            day_of_month=args.day_of_month
        )
        
        # Add schedule
        scheduler = get_export_scheduler()
        scheduler.add_schedule(schedule)
        
        print(f"✓ Created schedule '{schedule.name}' with ID: {schedule.id}")
        print(f"  Next run: {schedule.next_run}")
        
    except Exception as e:
        print(f"✗ Error creating schedule: {e}")
        sys.exit(1)


def list_schedules(args):
    """List all export schedules."""
    try:
        scheduler = get_export_scheduler()
        schedules = scheduler.list_schedules(enabled_only=args.enabled_only)
        
        if not schedules:
            print("No schedules found.")
            return
        
        print(f"Found {len(schedules)} schedule(s):")
        print()
        
        for schedule in schedules:
            status_icon = "✓" if schedule.enabled else "✗"
            print(f"{status_icon} {schedule.name} ({schedule.id})")
            print(f"   Interval: {schedule.interval.value}")
            print(f"   Format: {schedule.file_format.value}")
            print(f"   Entities: {', '.join(schedule.export_options.entity_types)}")
            print(f"   Output: {schedule.output_directory}")
            print(f"   Next run: {schedule.next_run}")
            print(f"   Last run: {schedule.last_run}")
            print(f"   Status: {schedule.last_status.value}")
            if schedule.last_error:
                print(f"   Last error: {schedule.last_error}")
            print()
        
    except Exception as e:
        print(f"✗ Error listing schedules: {e}")
        sys.exit(1)


def delete_schedule(args):
    """Delete an export schedule."""
    try:
        scheduler = get_export_scheduler()
        
        if scheduler.remove_schedule(args.schedule_id):
            print(f"✓ Deleted schedule: {args.schedule_id}")
        else:
            print(f"✗ Schedule not found: {args.schedule_id}")
            sys.exit(1)
        
    except Exception as e:
        print(f"✗ Error deleting schedule: {e}")
        sys.exit(1)


def show_status(args):
    """Show scheduler status."""
    try:
        scheduler = get_export_scheduler()
        status = scheduler.get_scheduler_status()
        
        print("Export Scheduler Status:")
        print(f"  Running: {'Yes' if status['is_running'] else 'No'}")
        print(f"  Total schedules: {status['total_schedules']}")
        print(f"  Enabled schedules: {status['enabled_schedules']}")
        print(f"  Running jobs: {status['running_jobs']}")
        print(f"  Check interval: {status['check_interval']} seconds")
        print()
        
        # File statistics
        file_stats = status.get('file_statistics', {})
        if file_stats:
            print("File Statistics:")
            print(f"  Total files: {file_stats.get('total_files', 0)}")
            print(f"  Total size: {file_stats.get('total_size_mb', 0):.2f} MB")
            
            if file_stats.get('oldest_file'):
                oldest = file_stats['oldest_file']
                print(f"  Oldest file: {oldest['age_days']} days old")
            
            if file_stats.get('files_by_format'):
                print("  Files by format:")
                for fmt, info in file_stats['files_by_format'].items():
                    print(f"    {fmt}: {info['count']} files ({info['size_mb']:.2f} MB)")
            print()
        
        # Next scheduled runs
        if status.get('next_scheduled_runs'):
            print("Next Scheduled Runs:")
            for run in status['next_scheduled_runs']:
                next_run = run['next_run']
                if next_run:
                    next_run_dt = datetime.fromisoformat(next_run)
                    print(f"  {run['schedule_name']}: {next_run_dt.strftime('%Y-%m-%d %H:%M')}")
        
    except Exception as e:
        print(f"✗ Error getting status: {e}")
        sys.exit(1)


def start_scheduler(args):
    """Start the export scheduler."""
    try:
        scheduler = get_export_scheduler()
        scheduler.start_scheduler()
        print("✓ Export scheduler started")
        
    except Exception as e:
        print(f"✗ Error starting scheduler: {e}")
        sys.exit(1)


def stop_scheduler(args):
    """Stop the export scheduler."""
    try:
        scheduler = get_export_scheduler()
        scheduler.stop_scheduler()
        print("✓ Export scheduler stopped")
        
    except Exception as e:
        print(f"✗ Error stopping scheduler: {e}")
        sys.exit(1)


def run_cleanup(args):
    """Run file cleanup operation."""
    try:
        # Create retention config
        retention_config = FileRetentionConfig(
            policy=RetentionPolicy(args.policy),
            value=args.value,
            compress_before_delete=args.compress,
            compression_type=CompressionType(args.compression_type),
            archive_directory=args.archive_dir
        )
        
        scheduler = get_export_scheduler()
        result = scheduler.run_file_cleanup(retention_config)
        
        if result['success']:
            print("✓ File cleanup completed successfully")
            print(f"  Files deleted: {result['files_deleted']}")
            print(f"  Files archived: {result['files_archived']}")
            print(f"  Space freed: {result['space_freed_mb']:.2f} MB")
        else:
            print("✗ File cleanup completed with errors")
            for error in result['errors']:
                print(f"  Error: {error}")
        
        if result['warnings']:
            print("Warnings:")
            for warning in result['warnings']:
                print(f"  Warning: {warning}")
        
    except Exception as e:
        print(f"✗ Error running cleanup: {e}")
        sys.exit(1)


def show_history(args):
    """Show execution history."""
    try:
        scheduler = get_export_scheduler()
        history = scheduler.get_execution_history(
            schedule_id=args.schedule_id,
            limit=args.limit
        )
        
        if not history:
            print("No execution history found.")
            return
        
        print(f"Execution History ({len(history)} entries):")
        print()
        
        for execution in history:
            status_icon = "✓" if execution.success else "✗"
            duration = execution.duration.total_seconds() if execution.duration else 0
            
            print(f"{status_icon} {execution.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Schedule: {execution.schedule_id}")
            print(f"   Duration: {duration:.1f} seconds")
            
            if execution.export_result:
                result = execution.export_result
                print(f"   Records: {result.total_exported}")
                print(f"   Files: {len(result.exported_files)}")
            
            if execution.error_message:
                print(f"   Error: {execution.error_message}")
            
            print()
        
    except Exception as e:
        print(f"✗ Error showing history: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Manage export scheduler")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create schedule command
    create_parser = subparsers.add_parser('create', help='Create a new export schedule')
    create_parser.add_argument('name', help='Schedule name')
    create_parser.add_argument('interval', choices=['daily', 'weekly', 'monthly'], help='Schedule interval')
    create_parser.add_argument('output_dir', help='Output directory for exports')
    create_parser.add_argument('--description', help='Schedule description')
    create_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    create_parser.add_argument('--entity-types', help='Comma-separated list of entity types')
    create_parser.add_argument('--run-time', default='02:00', help='Run time (HH:MM format)')
    create_parser.add_argument('--day-of-week', type=int, default=0, help='Day of week for weekly schedules (0=Monday)')
    create_parser.add_argument('--day-of-month', type=int, default=1, help='Day of month for monthly schedules')
    create_parser.add_argument('--file-prefix', help='File prefix for exports')
    create_parser.add_argument('--include-historical', action='store_true', help='Include historical data')
    create_parser.add_argument('--compress', action='store_true', help='Compress output files')
    create_parser.add_argument('--split-by-entity', action='store_true', default=True, help='Split CSV by entity type')
    create_parser.add_argument('--disabled', action='store_true', help='Create schedule as disabled')
    create_parser.set_defaults(func=create_schedule)
    
    # List schedules command
    list_parser = subparsers.add_parser('list', help='List export schedules')
    list_parser.add_argument('--enabled-only', action='store_true', help='Show only enabled schedules')
    list_parser.set_defaults(func=list_schedules)
    
    # Delete schedule command
    delete_parser = subparsers.add_parser('delete', help='Delete an export schedule')
    delete_parser.add_argument('schedule_id', help='Schedule ID to delete')
    delete_parser.set_defaults(func=delete_schedule)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show scheduler status')
    status_parser.set_defaults(func=show_status)
    
    # Start scheduler command
    start_parser = subparsers.add_parser('start', help='Start the export scheduler')
    start_parser.set_defaults(func=start_scheduler)
    
    # Stop scheduler command
    stop_parser = subparsers.add_parser('stop', help='Stop the export scheduler')
    stop_parser.set_defaults(func=stop_scheduler)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Run file cleanup')
    cleanup_parser.add_argument('--policy', choices=['days', 'count', 'size'], default='days', help='Retention policy')
    cleanup_parser.add_argument('--value', type=int, default=30, help='Retention value')
    cleanup_parser.add_argument('--compress', action='store_true', help='Compress files before deletion')
    cleanup_parser.add_argument('--compression-type', choices=['zip', 'tar.gz', 'none'], default='tar.gz', help='Compression type')
    cleanup_parser.add_argument('--archive-dir', default='exports/archive', help='Archive directory')
    cleanup_parser.set_defaults(func=run_cleanup)
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show execution history')
    history_parser.add_argument('--schedule-id', help='Filter by schedule ID')
    history_parser.add_argument('--limit', type=int, default=10, help='Limit number of results')
    history_parser.set_defaults(func=show_history)
    
    # Parse arguments and execute command
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize scheduler
    initialize_export_scheduler(auto_start=False)
    
    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()