#!/usr/bin/env python3
"""
Initialize the export scheduler with default configuration.

This script sets up the export scheduler with sensible defaults and
can be run during application startup or deployment.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.export_scheduler import initialize_export_scheduler
from app.services.export_file_manager import initialize_export_file_manager


def main():
    """Initialize the export scheduler and file manager."""
    try:
        print("Initializing export scheduler...")
        
        # Ensure directories exist
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        archive_dir = export_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        # Initialize file manager
        file_manager = initialize_export_file_manager(
            base_directory=str(export_dir),
            metadata_file="export_files.json"
        )
        print(f"✓ File manager initialized with base directory: {export_dir}")
        
        # Initialize scheduler
        scheduler = initialize_export_scheduler(
            config_file=str(config_dir / "export_schedules.json"),
            auto_start=True
        )
        print(f"✓ Scheduler initialized and started")
        
        # Show status
        status = scheduler.get_scheduler_status()
        print(f"✓ Scheduler running: {status['is_running']}")
        print(f"✓ Total schedules: {status['total_schedules']}")
        
        print("\nExport scheduler initialization completed successfully!")
        print("\nUsage:")
        print("  python scripts/manage_export_scheduler.py --help")
        print("  python scripts/manage_export_scheduler.py status")
        print("  python scripts/manage_export_scheduler.py create 'Daily Backup' daily exports/")
        
    except Exception as e:
        print(f"✗ Error initializing export scheduler: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()