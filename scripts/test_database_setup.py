#!/usr/bin/env python3
"""
Test script to verify database setup and initialization
"""

import sys
import logging
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_database, get_database_info, get_db_manager

def main():
    """Test database setup"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting database setup test...")
        
        # Test database initialization
        logger.info("Testing database initialization...")
        init_database()
        
        # Get database info
        logger.info("Getting database information...")
        info = get_database_info()
        
        # Display results
        print("\n" + "="*50)
        print("DATABASE SETUP TEST RESULTS")
        print("="*50)
        print(f"Tables: {len(info.get('table_names', []))}")
        print(f"Table names: {', '.join(info.get('table_names', []))}")
        print(f"Database size: {info.get('file_size_mb', 0)} MB")
        print(f"Foreign keys enabled: {info.get('foreign_keys_enabled', False)}")
        print(f"Connection pool: {info.get('connection_pool_size', 0)}/{info.get('max_connections', 0)}")
        
        # Test basic queries
        logger.info("Testing basic database queries...")
        db_manager = get_db_manager()
        
        # Test units query
        units = db_manager.fetch_all("SELECT COUNT(*) as count FROM units")
        unit_count = units[0]['count']
        print(f"Units in database: {unit_count}")
        
        # Test persons query
        persons = db_manager.fetch_all("SELECT COUNT(*) as count FROM persons")
        person_count = persons[0]['count']
        print(f"Persons in database: {person_count}")
        
        # Test assignments query
        assignments = db_manager.fetch_all("SELECT COUNT(*) as count FROM person_job_assignments WHERE is_current = 1")
        assignment_count = assignments[0]['count']
        print(f"Current assignments: {assignment_count}")
        
        print("="*50)
        print("✅ All database tests passed!")
        print("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        print(f"\n❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)