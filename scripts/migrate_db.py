#!/usr/bin/env python3
"""
Database migration script for Organigramma Web App
Handles schema migrations and data transformations
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import argparse

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from scripts.backup_db import DatabaseBackup

class DatabaseMigration:
    """Database migration manager"""
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.db_path = Path(self.settings.database.url.replace("sqlite:///", ""))
        self.migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize migration tracking table
        self._init_migration_table()
    
    def _init_migration_table(self):
        """Initialize migration tracking table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT,
                    execution_time_ms INTEGER
                )
            """)
            conn.commit()
    
    def create_migration(self, name: str, description: str = "") -> Path:
        """Create a new migration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{name.lower().replace(' ', '_')}"
        migration_file = self.migrations_dir / f"{version}.sql"
        
        template = f"""-- Migration: {name}
-- Description: {description}
-- Created: {datetime.now().isoformat()}
-- Version: {version}

-- =============================================================================
-- UP MIGRATION
-- =============================================================================

-- Add your schema changes here
-- Example:
-- CREATE TABLE new_table (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- ALTER TABLE existing_table ADD COLUMN new_column TEXT;

-- =============================================================================
-- DATA MIGRATION (if needed)
-- =============================================================================

-- Add data transformation queries here
-- Example:
-- INSERT INTO new_table (name) SELECT name FROM old_table;

-- =============================================================================
-- ROLLBACK MIGRATION (optional)
-- =============================================================================

-- Add rollback queries here (commented out)
-- These will be used if migration needs to be rolled back
-- Example:
-- -- DROP TABLE new_table;
-- -- ALTER TABLE existing_table DROP COLUMN new_column;
"""
        
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"✅ Created migration: {migration_file}")
        return migration_file
    
    def list_migrations(self) -> List[Dict]:
        """List all available migrations"""
        migrations = []
        
        # Get applied migrations
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT version, name, applied_at, execution_time_ms 
                FROM schema_migrations 
                ORDER BY version
            """)
            applied_migrations = {row['version']: dict(row) for row in cursor.fetchall()}
        
        # Get all migration files
        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            version = migration_file.stem
            
            migration_info = {
                "version": version,
                "file": migration_file,
                "applied": version in applied_migrations,
                "applied_at": applied_migrations.get(version, {}).get("applied_at"),
                "execution_time_ms": applied_migrations.get(version, {}).get("execution_time_ms")
            }
            
            # Parse migration file for metadata
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for line in lines[:10]:  # Check first 10 lines
                        if line.startswith('-- Migration:'):
                            migration_info["name"] = line.replace('-- Migration:', '').strip()
                        elif line.startswith('-- Description:'):
                            migration_info["description"] = line.replace('-- Description:', '').strip()
            except Exception:
                pass
            
            migrations.append(migration_info)
        
        return migrations
    
    def apply_migration(self, version: str) -> bool:
        """Apply a specific migration"""
        migration_file = self.migrations_dir / f"{version}.sql"
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        # Check if already applied
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT version FROM schema_migrations WHERE version = ?", (version,))
            if cursor.fetchone():
                print(f"⚠️  Migration {version} already applied")
                return False
        
        # Create backup before migration
        backup_manager = DatabaseBackup(self.settings)
        backup_path = backup_manager.create_backup(compress=True)
        print(f"📦 Created backup: {backup_path}")
        
        # Read and execute migration
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        start_time = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Execute migration in transaction
                conn.executescript(migration_sql)
                
                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Record migration
                conn.execute("""
                    INSERT INTO schema_migrations (version, name, execution_time_ms, checksum)
                    VALUES (?, ?, ?, ?)
                """, (
                    version,
                    migration_file.stem,
                    int(execution_time),
                    self._calculate_checksum(migration_sql)
                ))
                
                conn.commit()
                
            print(f"✅ Applied migration {version} in {execution_time:.2f}ms")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print(f"💾 Backup available at: {backup_path}")
            raise
    
    def apply_pending_migrations(self) -> int:
        """Apply all pending migrations"""
        migrations = self.list_migrations()
        pending = [m for m in migrations if not m["applied"]]
        
        if not pending:
            print("✅ No pending migrations")
            return 0
        
        print(f"📋 Found {len(pending)} pending migrations")
        
        applied_count = 0
        for migration in pending:
            try:
                if self.apply_migration(migration["version"]):
                    applied_count += 1
            except Exception as e:
                print(f"❌ Failed to apply migration {migration['version']}: {e}")
                break
        
        return applied_count
    
    def rollback_migration(self, version: str):
        """Rollback a specific migration (if rollback queries are available)"""
        migration_file = self.migrations_dir / f"{version}.sql"
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        # Check if migration was applied
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT version FROM schema_migrations WHERE version = ?", (version,))
            if not cursor.fetchone():
                print(f"⚠️  Migration {version} was not applied")
                return False
        
        # Create backup before rollback
        backup_manager = DatabaseBackup(self.settings)
        backup_path = backup_manager.create_backup(compress=True)
        print(f"📦 Created backup: {backup_path}")
        
        # Extract rollback queries from migration file
        with open(migration_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find rollback section
        rollback_section = False
        rollback_queries = []
        
        for line in content.split('\n'):
            if "ROLLBACK MIGRATION" in line:
                rollback_section = True
                continue
            
            if rollback_section and line.strip().startswith('-- ') and not line.strip().startswith('-- --'):
                # This is a commented rollback query
                query = line.strip()[3:]  # Remove '-- '
                if query.strip():
                    rollback_queries.append(query)
        
        if not rollback_queries:
            print(f"⚠️  No rollback queries found for migration {version}")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Execute rollback queries
                for query in rollback_queries:
                    conn.execute(query)
                
                # Remove migration record
                conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
                
                conn.commit()
                
            print(f"✅ Rolled back migration {version}")
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            print(f"💾 Backup available at: {backup_path}")
            raise
    
    def _calculate_checksum(self, content: str) -> str:
        """Calculate checksum for migration content"""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_schema_version(self) -> Optional[str]:
        """Get current schema version (latest applied migration)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT version FROM schema_migrations 
                ORDER BY version DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            return result[0] if result else None
    
    def validate_migrations(self) -> List[Dict]:
        """Validate applied migrations against files"""
        issues = []
        migrations = self.list_migrations()
        
        for migration in migrations:
            if migration["applied"]:
                # Check if file still exists
                if not migration["file"].exists():
                    issues.append({
                        "type": "missing_file",
                        "version": migration["version"],
                        "message": f"Migration file missing: {migration['file']}"
                    })
                    continue
                
                # Check checksum if available
                try:
                    with open(migration["file"], 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    current_checksum = self._calculate_checksum(content)
                    
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.execute(
                            "SELECT checksum FROM schema_migrations WHERE version = ?",
                            (migration["version"],)
                        )
                        result = cursor.fetchone()
                        stored_checksum = result[0] if result else None
                    
                    if stored_checksum and current_checksum != stored_checksum:
                        issues.append({
                            "type": "checksum_mismatch",
                            "version": migration["version"],
                            "message": f"Migration file has been modified after application"
                        })
                
                except Exception as e:
                    issues.append({
                        "type": "validation_error",
                        "version": migration["version"],
                        "message": f"Error validating migration: {e}"
                    })
        
        return issues

def main():
    """Main migration script function"""
    parser = argparse.ArgumentParser(description="Organigramma Web App Database Migration Tool")
    parser.add_argument("action", choices=["create", "list", "apply", "apply-all", "rollback", "status", "validate"], 
                       help="Action to perform")
    parser.add_argument("--name", type=str, help="Migration name (for create action)")
    parser.add_argument("--description", type=str, default="", help="Migration description")
    parser.add_argument("--version", type=str, help="Migration version (for apply/rollback actions)")
    
    args = parser.parse_args()
    
    try:
        migration_manager = DatabaseMigration()
        
        if args.action == "create":
            if not args.name:
                print("❌ --name is required for create action")
                sys.exit(1)
            
            migration_file = migration_manager.create_migration(args.name, args.description)
            print(f"📝 Edit the migration file: {migration_file}")
            
        elif args.action == "list":
            print("Available migrations:")
            migrations = migration_manager.list_migrations()
            if not migrations:
                print("No migrations found.")
            else:
                for migration in migrations:
                    status = "✅ Applied" if migration["applied"] else "⏳ Pending"
                    name = migration.get("name", migration["version"])
                    print(f"{status} {migration['version']} - {name}")
                    if migration["applied"]:
                        print(f"   Applied: {migration['applied_at']}")
                        if migration["execution_time_ms"]:
                            print(f"   Execution time: {migration['execution_time_ms']}ms")
                    print()
        
        elif args.action == "apply":
            if not args.version:
                print("❌ --version is required for apply action")
                sys.exit(1)
            
            migration_manager.apply_migration(args.version)
        
        elif args.action == "apply-all":
            applied = migration_manager.apply_pending_migrations()
            print(f"✅ Applied {applied} migrations")
        
        elif args.action == "rollback":
            if not args.version:
                print("❌ --version is required for rollback action")
                sys.exit(1)
            
            migration_manager.rollback_migration(args.version)
        
        elif args.action == "status":
            current_version = migration_manager.get_schema_version()
            migrations = migration_manager.list_migrations()
            pending = [m for m in migrations if not m["applied"]]
            
            print(f"Current schema version: {current_version or 'None'}")
            print(f"Total migrations: {len(migrations)}")
            print(f"Applied migrations: {len(migrations) - len(pending)}")
            print(f"Pending migrations: {len(pending)}")
            
            if pending:
                print("\nPending migrations:")
                for migration in pending:
                    name = migration.get("name", migration["version"])
                    print(f"  - {migration['version']} - {name}")
        
        elif args.action == "validate":
            issues = migration_manager.validate_migrations()
            if not issues:
                print("✅ All migrations are valid")
            else:
                print(f"⚠️  Found {len(issues)} validation issues:")
                for issue in issues:
                    print(f"  - {issue['type']}: {issue['message']}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()