#!/usr/bin/env python3
"""
Migration 002: Unit Type Themes System
Description: Create unit_type_themes table and add theme support to unit_types
Date: 2025-08-01
Requirements: 1.1, 5.2, 5.3
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db_manager


def run_migration():
    """Execute the unit type themes migration"""
    
    # Get database manager
    db_manager = get_db_manager()
    
    try:
        print("Starting Migration 002: Unit Type Themes System...")
        
        # Check if migration has already been run
        migration_status = check_migration_status(db_manager)
        
        if migration_status['complete']:
            print("✅ Migration 002 has already been run completely. Skipping...")
            verify_migration(db_manager)
            return
        
        # Handle partial migration - add theme_id column if missing
        if not migration_status['theme_id_exists']:
            print("📝 Adding theme_id column to unit_types table...")
            try:
                db_manager.execute_query("ALTER TABLE unit_types ADD COLUMN theme_id INTEGER REFERENCES unit_type_themes(id)")
                print("✅ theme_id column added successfully")
            except Exception as e:
                if "duplicate column name" in str(e):
                    print("✅ theme_id column already exists")
                else:
                    raise e
        
        # Use the idempotent migration script
        migration_file = Path(__file__).parent.parent / "database" / "schema" / "migration_002_unit_type_themes_idempotent.sql"
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        # Execute the idempotent migration
        db_manager.execute_script(migration_file)
        
        print("✅ Migration 002 completed successfully!")
        
        # Verify the migration
        verify_migration(db_manager)
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


def check_migration_status(db_manager):
    """Check the status of the migration components"""
    
    status = {
        'themes_table_exists': False,
        'theme_id_exists': False,
        'themes_created': False,
        'themes_assigned': False,
        'complete': False
    }
    
    try:
        # Check if unit_type_themes table exists
        table_exists = db_manager.fetch_one("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='unit_type_themes'
        """)
        status['themes_table_exists'] = bool(table_exists)
        
        # Check if theme_id column exists in unit_types table
        columns_result = db_manager.fetch_all("PRAGMA table_info(unit_types)")
        columns = [row[1] for row in columns_result]
        status['theme_id_exists'] = 'theme_id' in columns
        
        # Check if default themes exist
        if status['themes_table_exists']:
            theme_count_result = db_manager.fetch_one("SELECT COUNT(*) FROM unit_type_themes")
            theme_count = theme_count_result[0] if theme_count_result else 0
            status['themes_created'] = theme_count >= 2
            
            # Check if themes are assigned to unit types
            if status['theme_id_exists']:
                assigned_count_result = db_manager.fetch_one("SELECT COUNT(*) FROM unit_types WHERE theme_id IS NOT NULL")
                assigned_count = assigned_count_result[0] if assigned_count_result else 0
                status['themes_assigned'] = assigned_count >= 2
        
        # Migration is complete if all components are in place
        status['complete'] = (
            status['themes_table_exists'] and 
            status['theme_id_exists'] and 
            status['themes_created'] and 
            status['themes_assigned']
        )
        
        return status
        
    except Exception as e:
        print(f"Warning: Could not check migration status: {e}")
        return status


def verify_migration(db_manager):
    """Verify that the migration was successful"""
    
    print("\n🔍 Verifying migration...")
    
    # Check if unit_type_themes table exists
    result = db_manager.fetch_one("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='unit_type_themes'
    """)
    if not result:
        raise Exception("unit_type_themes table was not created")
    print("✅ unit_type_themes table created")
    
    # Check if theme_id column was added to unit_types
    columns_result = db_manager.fetch_all("PRAGMA table_info(unit_types)")
    columns = [row[1] for row in columns_result]
    if 'theme_id' not in columns:
        raise Exception("theme_id column was not added to unit_types table")
    print("✅ theme_id column added to unit_types table")
    
    # Check if default themes were created
    theme_count_result = db_manager.fetch_one("SELECT COUNT(*) FROM unit_type_themes")
    theme_count = theme_count_result[0]
    if theme_count < 2:
        raise Exception(f"Expected at least 2 themes, found {theme_count}")
    print(f"✅ {theme_count} themes created")
    
    # Check if themes were assigned to unit types
    assigned_count_result = db_manager.fetch_one("SELECT COUNT(*) FROM unit_types WHERE theme_id IS NOT NULL")
    assigned_count = assigned_count_result[0]
    if assigned_count < 2:
        raise Exception(f"Expected at least 2 unit types with themes, found {assigned_count}")
    print(f"✅ {assigned_count} unit types assigned themes")
    
    # Check if default theme exists
    default_count_result = db_manager.fetch_one("SELECT COUNT(*) FROM unit_type_themes WHERE is_default = TRUE")
    default_count = default_count_result[0]
    if default_count != 1:
        raise Exception(f"Expected exactly 1 default theme, found {default_count}")
    print("✅ Default theme configured")
    
    # Show theme assignments
    print("\n📋 Theme assignments:")
    assignments = db_manager.fetch_all("""
        SELECT ut.name as unit_type, utt.name as theme_name, utt.display_label
        FROM unit_types ut
        LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
        ORDER BY ut.id
    """)
    for row in assignments:
        unit_type, theme_name, display_label = row
        print(f"  • {unit_type} → {theme_name} ({display_label})")
    
    print("\n✅ Migration verification completed successfully!")


def rollback_migration():
    """Rollback the unit type themes migration"""
    
    # Get database manager
    db_manager = get_db_manager()
    
    try:
        print("Starting Rollback 002: Unit Type Themes System...")
        
        # Read and execute the rollback SQL
        rollback_file = Path(__file__).parent.parent / "database" / "schema" / "rollback_002_unit_type_themes.sql"
        
        if not rollback_file.exists():
            raise FileNotFoundError(f"Rollback file not found: {rollback_file}")
        
        # Execute the rollback using the database manager
        db_manager.execute_script(rollback_file)
        
        print("✅ Rollback 002 completed successfully!")
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Unit Type Themes Migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        run_migration()