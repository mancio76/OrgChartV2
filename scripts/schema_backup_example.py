#!/usr/bin/env python3
"""
Example usage of the database schema backup system
Demonstrates common schema backup operations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.backup_schema import SchemaBackup, format_size

def main():
    """Demonstrate schema backup system usage"""
    print("🗄️  Organigramma Database Schema Backup Demo")
    print("=" * 55)
    
    try:
        # Initialize schema backup manager
        schema_backup = SchemaBackup()
        
        print(f"📁 Database path: {schema_backup.db_path}")
        print(f"💾 Backup directory: {schema_backup.backup_dir}")
        print()
        
        # Validate current schema
        print("🔍 Validating current database schema...")
        validation = schema_backup.validate_schema()
        
        if validation['valid']:
            print("✅ Database schema is valid")
        else:
            print("❌ Database schema has issues:")
            for error in validation['errors']:
                print(f"   ❌ {error}")
        
        if validation['warnings']:
            print("⚠️  Warnings:")
            for warning in validation['warnings']:
                print(f"   ⚠️  {warning}")
        
        if validation['info']:
            info = validation['info']
            print(f"📊 Schema contains {info.get('table_count', 0)} tables:")
            for table in info.get('tables', []):
                print(f"   📋 {table}")
        
        print()
        
        # Show existing backups
        existing_backups = schema_backup.list_schema_backups()
        print(f"💾 Existing schema backups: {len(existing_backups)}")
        
        if existing_backups:
            print("\n📋 Recent backups:")
            for backup in existing_backups[:3]:  # Show last 3
                print(f"   📦 {backup['name']}")
                print(f"      📅 Created: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"      📦 Size: {format_size(backup['size'])}")
                print()
        
        # Demonstrate backup creation
        print("🚀 Creating demonstration backups...")
        
        # Create schema-only backup
        print("   📋 Creating schema-only backup...")
        schema_backup_path = schema_backup.create_schema_backup(
            include_data=False, 
            include_metadata=True
        )
        schema_size = format_size(schema_backup_path.stat().st_size)
        print(f"   ✅ Schema backup: {schema_size}")
        
        # Create backup with data
        print("   📊 Creating backup with data...")
        data_backup_path = schema_backup.create_schema_backup(
            include_data=True, 
            include_metadata=True
        )
        data_size = format_size(data_backup_path.stat().st_size)
        print(f"   ✅ Data backup: {data_size}")
        
        # Calculate compression ratio
        if schema_backup_path.stat().st_size > 0:
            ratio = (data_backup_path.stat().st_size - schema_backup_path.stat().st_size) / schema_backup_path.stat().st_size * 100
            print(f"   📈 Data adds {ratio:.1f}% to backup size")
        
        print()
        
        # Show final backup list
        final_backups = schema_backup.list_schema_backups()
        print(f"📦 Total backups after demo: {len(final_backups)}")
        
        print("\n✅ Demo completed!")
        print("\nUseful commands:")
        print("   📋 Create schema backup:")
        print("      python scripts/backup_schema.py create")
        print("   📊 Create backup with data:")
        print("      python scripts/backup_schema.py create --include-data")
        print("   📋 List backups:")
        print("      python scripts/backup_schema.py list")
        print("   🔍 Validate schema:")
        print("      python scripts/backup_schema.py validate")
        print("   🧹 Cleanup old backups:")
        print("      python scripts/backup_schema.py cleanup")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()