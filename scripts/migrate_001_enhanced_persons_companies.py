#!/usr/bin/env python3
"""
Migration 001: Enhanced Persons and Companies
Execute database migration to add enhanced fields to persons table and create companies table.

Usage:
    python scripts/migrate_001_enhanced_persons_companies.py [--rollback] [--dry-run]

Options:
    --rollback    Execute rollback instead of migration
    --dry-run     Show what would be executed without making changes
"""

import sqlite3
import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Migration001:
    """Migration 001: Enhanced Persons and Companies"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "database/orgchart.db"
        self.migration_file = "database/schema/migration_001_enhanced_persons_companies.sql"
        self.rollback_file = "database/schema/rollback_001_enhanced_persons_companies.sql"
        self.profiles_dir = "static/profiles"
        
    def create_profiles_directory(self):
        """Create profiles directory for profile images"""
        try:
            profiles_path = Path(self.profiles_dir)
            profiles_path.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep file to ensure directory is tracked
            gitkeep_path = profiles_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
            
            logger.info(f"Created profiles directory: {profiles_path.absolute()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create profiles directory: {e}")
            return False
    
    def backup_database(self):
        """Create a backup of the database before migration"""
        try:
            backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return None
    
    def verify_prerequisites(self):
        """Verify that prerequisites are met for migration"""
        try:
            # Check if database exists
            if not os.path.exists(self.db_path):
                logger.error(f"Database file not found: {self.db_path}")
                return False
            
            # Check if migration files exist
            if not os.path.exists(self.migration_file):
                logger.error(f"Migration file not found: {self.migration_file}")
                return False
                
            if not os.path.exists(self.rollback_file):
                logger.error(f"Rollback file not found: {self.rollback_file}")
                return False
            
            # Test database connection
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='persons'")
                if not cursor.fetchone():
                    logger.error("Persons table not found in database")
                    return False
            
            logger.info("Prerequisites verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Prerequisites verification failed: {e}")
            return False
    
    def check_migration_status(self):
        """Check if migration has already been applied"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if new columns exist in persons table
                cursor.execute("PRAGMA table_info(persons)")
                columns = [row[1] for row in cursor.fetchall()]
                
                has_new_columns = all(col in columns for col in ['first_name', 'last_name', 'registration_no', 'profile_image'])
                
                # Check if companies table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
                has_companies_table = cursor.fetchone() is not None
                
                if has_new_columns and has_companies_table:
                    return "applied"
                elif has_new_columns or has_companies_table:
                    return "partial"
                else:
                    return "not_applied"
                    
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return "unknown"
    
    def execute_sql_file(self, file_path: str, dry_run: bool = False):
        """Execute SQL file with proper error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            if dry_run:
                logger.info(f"DRY RUN - Would execute SQL from: {file_path}")
                logger.info("SQL Content:")
                logger.info("-" * 50)
                logger.info(sql_content)
                logger.info("-" * 50)
                return True
            
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Execute SQL content
                conn.executescript(sql_content)
                conn.commit()
                
            logger.info(f"Successfully executed SQL from: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute SQL file {file_path}: {e}")
            return False
    
    def migrate(self, dry_run: bool = False):
        """Execute the migration"""
        logger.info("Starting Migration 001: Enhanced Persons and Companies")
        
        # Verify prerequisites
        if not self.verify_prerequisites():
            return False
        
        # Check migration status
        status = self.check_migration_status()
        if status == "applied":
            logger.warning("Migration appears to already be applied")
            return True
        elif status == "partial":
            logger.error("Migration is partially applied - manual intervention required")
            return False
        
        # Create backup
        if not dry_run:
            backup_path = self.backup_database()
            if not backup_path:
                logger.error("Failed to create backup - aborting migration")
                return False
        
        # Create profiles directory
        if not dry_run:
            if not self.create_profiles_directory():
                logger.error("Failed to create profiles directory - aborting migration")
                return False
        
        # Execute migration
        if not self.execute_sql_file(self.migration_file, dry_run):
            logger.error("Migration failed")
            return False
        
        # Verify migration was successful
        if not dry_run:
            final_status = self.check_migration_status()
            if final_status != "applied":
                logger.error("Migration verification failed")
                return False
        
        logger.info("Migration 001 completed successfully")
        return True
    
    def rollback(self, dry_run: bool = False):
        """Execute the rollback"""
        logger.info("Starting Rollback 001: Enhanced Persons and Companies")
        
        # Verify prerequisites
        if not self.verify_prerequisites():
            return False
        
        # Check migration status
        status = self.check_migration_status()
        if status == "not_applied":
            logger.warning("Migration does not appear to be applied")
            return True
        
        # Create backup
        if not dry_run:
            backup_path = self.backup_database()
            if not backup_path:
                logger.error("Failed to create backup - aborting rollback")
                return False
        
        # Execute rollback
        if not self.execute_sql_file(self.rollback_file, dry_run):
            logger.error("Rollback failed")
            return False
        
        # Verify rollback was successful
        if not dry_run:
            final_status = self.check_migration_status()
            if final_status != "not_applied":
                logger.error("Rollback verification failed")
                return False
        
        logger.info("Rollback 001 completed successfully")
        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Migration 001: Enhanced Persons and Companies")
    parser.add_argument("--rollback", action="store_true", help="Execute rollback instead of migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be executed without making changes")
    parser.add_argument("--db-path", help="Path to database file (default: database/orgchart.db)")
    
    args = parser.parse_args()
    
    # Initialize migration
    migration = Migration001(args.db_path)
    
    # Execute migration or rollback
    if args.rollback:
        success = migration.rollback(args.dry_run)
    else:
        success = migration.migrate(args.dry_run)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()