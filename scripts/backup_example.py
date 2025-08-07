#!/usr/bin/env python3
"""
Example usage of the project backup system
Demonstrates common backup operations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.backup_project import ProjectBackup, format_size

def main():
    """Demonstrate backup system usage"""
    print("🚀 Organigramma Project Backup System Demo")
    print("=" * 50)
    
    # Initialize backup manager
    backup_manager = ProjectBackup()
    
    print(f"📁 Project root: {backup_manager.project_root}")
    print(f"💾 Backup directory: {backup_manager.backup_dir}")
    print()
    
    # Show current .gitignore patterns
    print("🚫 Excluded patterns from .gitignore:")
    for pattern in sorted(backup_manager.gitignore_patterns):
        print(f"   - {pattern}")
    print()
    
    print("🚫 Additional excluded patterns:")
    for pattern in sorted(backup_manager.additional_excludes):
        print(f"   - {pattern}")
    print()
    
    # Show files that would be backed up
    files_to_backup = backup_manager._get_project_files()
    print(f"📄 Files to backup: {len(files_to_backup)}")
    
    # Analyze file types
    file_types = {}
    total_size = 0
    for file_path in files_to_backup:
        if file_path.exists():
            suffix = file_path.suffix.lower() or 'no_extension'
            file_types[suffix] = file_types.get(suffix, 0) + 1
            total_size += file_path.stat().st_size
    
    print(f"📦 Total size: {format_size(total_size)}")
    print()
    
    print("📊 File type breakdown:")
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {ext}: {count} files")
    print()
    
    # List existing backups
    existing_backups = backup_manager.list_backups()
    print(f"💾 Existing backups: {len(existing_backups)}")
    
    if existing_backups:
        print("\n📋 Recent backups:")
        for backup in existing_backups[:3]:  # Show last 3
            print(f"   📦 {backup['name']}")
            print(f"      📅 Created: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      📦 Size: {format_size(backup['size'])}")
            print(f"      📁 Type: {backup['type'].title()}")
            
            if backup['metadata']:
                metadata = backup['metadata']
                if 'total_files' in metadata:
                    print(f"      📄 Files: {metadata['total_files']}")
            print()
    
    print("✅ Demo completed!")
    print("\nTo create a backup, run:")
    print("   python scripts/backup_project.py create")
    print("\nTo list backups, run:")
    print("   python scripts/backup_project.py list")

if __name__ == "__main__":
    main()