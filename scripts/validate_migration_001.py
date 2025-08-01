#!/usr/bin/env python3
"""
Validation script for Migration 001: Enhanced Persons and Companies
Validates that the migration was applied correctly.

Usage:
    python scripts/validate_migration_001.py [--db-path path/to/database.db]
"""

import sqlite3
import os
import sys
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Migration001Validator:
    """Validator for Migration 001"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "database/orgchart.db"
        self.profiles_dir = "static/profiles"
        
    def validate_persons_table(self):
        """Validate persons table structure and data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check table structure
                cursor.execute("PRAGMA table_info(persons)")
                columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                required_columns = {
                    'id': 'INTEGER',
                    'name': 'TEXT',
                    'short_name': 'TEXT',
                    'email': 'TEXT',
                    'first_name': 'TEXT',
                    'last_name': 'TEXT',
                    'registration_no': 'TEXT',
                    'profile_image': 'TEXT',
                    'datetime_created': 'DATETIME',
                    'datetime_updated': 'DATETIME'
                }
                
                missing_columns = []
                for col_name, col_type in required_columns.items():
                    if col_name not in columns:
                        missing_columns.append(col_name)
                
                if missing_columns:
                    logger.error(f"Missing columns in persons table: {missing_columns}")
                    return False
                
                # Check indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='persons'")
                indexes = [row[0] for row in cursor.fetchall()]
                
                required_indexes = [
                    'idx_persons_first_name',
                    'idx_persons_last_name', 
                    'idx_persons_registration_no',
                    'idx_persons_email'
                ]
                
                missing_indexes = [idx for idx in required_indexes if idx not in indexes]
                if missing_indexes:
                    logger.warning(f"Missing indexes on persons table: {missing_indexes}")
                
                # Check data migration
                cursor.execute("SELECT COUNT(*) FROM persons")
                total_persons = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM persons WHERE first_name IS NOT NULL")
                persons_with_first_name = cursor.fetchone()[0]
                
                logger.info(f"Persons table validation:")
                logger.info(f"  - Total persons: {total_persons}")
                logger.info(f"  - Persons with first_name: {persons_with_first_name}")
                logger.info(f"  - All required columns present: ✓")
                logger.info(f"  - Required indexes present: {'✓' if not missing_indexes else '⚠️'}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate persons table: {e}")
            return False
    
    def validate_companies_table(self):
        """Validate companies table structure"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
                if not cursor.fetchone():
                    logger.error("Companies table does not exist")
                    return False
                
                # Check table structure
                cursor.execute("PRAGMA table_info(companies)")
                columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                required_columns = {
                    'id': 'INTEGER',
                    'name': 'TEXT',
                    'short_name': 'TEXT',
                    'registration_no': 'TEXT',
                    'address': 'TEXT',
                    'city': 'TEXT',
                    'postal_code': 'TEXT',
                    'country': 'TEXT',
                    'phone': 'TEXT',
                    'email': 'TEXT',
                    'website': 'TEXT',
                    'main_contact_id': 'INTEGER',
                    'financial_contact_id': 'INTEGER',
                    'valid_from': 'DATE',
                    'valid_to': 'DATE',
                    'notes': 'TEXT',
                    'datetime_created': 'DATETIME',
                    'datetime_updated': 'DATETIME'
                }
                
                missing_columns = []
                for col_name, col_type in required_columns.items():
                    if col_name not in columns:
                        missing_columns.append(col_name)
                
                if missing_columns:
                    logger.error(f"Missing columns in companies table: {missing_columns}")
                    return False
                
                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_list(companies)")
                foreign_keys = cursor.fetchall()
                
                expected_fks = ['main_contact_id', 'financial_contact_id']
                actual_fks = [fk[3] for fk in foreign_keys]
                
                missing_fks = [fk for fk in expected_fks if fk not in actual_fks]
                if missing_fks:
                    logger.warning(f"Missing foreign keys in companies table: {missing_fks}")
                
                # Check indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='companies'")
                indexes = [row[0] for row in cursor.fetchall()]
                
                required_indexes = [
                    'idx_companies_name',
                    'idx_companies_registration_no',
                    'idx_companies_main_contact',
                    'idx_companies_financial_contact',
                    'idx_companies_valid_dates',
                    'idx_companies_email'
                ]
                
                missing_indexes = [idx for idx in required_indexes if idx not in indexes]
                if missing_indexes:
                    logger.warning(f"Missing indexes on companies table: {missing_indexes}")
                
                cursor.execute("SELECT COUNT(*) FROM companies")
                total_companies = cursor.fetchone()[0]
                
                logger.info(f"Companies table validation:")
                logger.info(f"  - Table exists: ✓")
                logger.info(f"  - All required columns present: ✓")
                logger.info(f"  - Foreign key constraints: {'✓' if not missing_fks else '⚠️'}")
                logger.info(f"  - Required indexes present: {'✓' if not missing_indexes else '⚠️'}")
                logger.info(f"  - Total companies: {total_companies}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate companies table: {e}")
            return False
    
    def validate_profiles_directory(self):
        """Validate profiles directory exists and is writable"""
        try:
            profiles_path = Path(self.profiles_dir)
            
            if not profiles_path.exists():
                logger.error(f"Profiles directory does not exist: {profiles_path}")
                return False
            
            if not profiles_path.is_dir():
                logger.error(f"Profiles path is not a directory: {profiles_path}")
                return False
            
            # Test write permissions
            test_file = profiles_path / ".test_write"
            try:
                test_file.touch()
                test_file.unlink()
                writable = True
            except:
                writable = False
            
            gitkeep_exists = (profiles_path / ".gitkeep").exists()
            
            logger.info(f"Profiles directory validation:")
            logger.info(f"  - Directory exists: ✓")
            logger.info(f"  - Directory writable: {'✓' if writable else '✗'}")
            logger.info(f"  - .gitkeep file present: {'✓' if gitkeep_exists else '⚠️'}")
            
            return writable
            
        except Exception as e:
            logger.error(f"Failed to validate profiles directory: {e}")
            return False
    
    def validate_database_integrity(self):
        """Run database integrity checks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                logger.info(f"Database integrity validation:")
                logger.info(f"  - Integrity check: {integrity_result}")
                logger.info(f"  - Foreign key violations: {len(fk_violations)}")
                
                if integrity_result != "ok":
                    logger.error(f"Database integrity check failed: {integrity_result}")
                    return False
                
                if fk_violations:
                    logger.error(f"Foreign key violations found: {fk_violations}")
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate database integrity: {e}")
            return False
    
    def validate_all(self):
        """Run all validation checks"""
        logger.info("Starting Migration 001 validation")
        
        checks = [
            ("Database file exists", lambda: os.path.exists(self.db_path)),
            ("Persons table", self.validate_persons_table),
            ("Companies table", self.validate_companies_table),
            ("Profiles directory", self.validate_profiles_directory),
            ("Database integrity", self.validate_database_integrity)
        ]
        
        results = []
        for check_name, check_func in checks:
            try:
                result = check_func()
                results.append((check_name, result))
                status = "✓" if result else "✗"
                logger.info(f"{check_name}: {status}")
            except Exception as e:
                results.append((check_name, False))
                logger.error(f"{check_name}: ✗ ({e})")
        
        # Summary
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        logger.info(f"\nValidation Summary: {passed}/{total} checks passed")
        
        if passed == total:
            logger.info("✓ Migration 001 validation PASSED")
            return True
        else:
            logger.error("✗ Migration 001 validation FAILED")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Validate Migration 001: Enhanced Persons and Companies")
    parser.add_argument("--db-path", help="Path to database file (default: database/orgchart.db)")
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = Migration001Validator(args.db_path)
    
    # Run validation
    success = validator.validate_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()