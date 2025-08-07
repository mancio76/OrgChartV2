#!/usr/bin/env python3
"""
Database schema backup script for Organigramma Web App
Creates SQL schema backups with structure, indexes, triggers, and metadata
"""

import os
import sys
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import argparse

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.config import get_settings
except ImportError:
    get_settings = None

class SchemaBackup:
    """Database schema backup manager"""
    
    def __init__(self, db_path: Optional[Path] = None, settings=None):
        self.settings = settings or (get_settings() if get_settings else None)
        
        # Determine database path
        if db_path:
            self.db_path = Path(db_path)
        elif self.settings:
            db_url = self.settings.database.url
            if db_url.startswith("sqlite:///"):
                self.db_path = Path(db_url.replace("sqlite:///", ""))
            else:
                self.db_path = Path("database/orgchart.db")
        else:
            self.db_path = Path("database/orgchart.db")
        
        # Set backup directory
        self.backup_dir = Path("database/schema/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
    
    def create_schema_backup(self, include_data: bool = False, include_metadata: bool = True) -> Path:
        """Create a complete schema backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"schema_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_name
        
        print(f"🗄️  Creating schema backup: {backup_name}")
        
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign keys for consistency
            conn.execute("PRAGMA foreign_keys = ON")
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                # Write header
                self._write_header(f, include_data, include_metadata)
                
                # Write metadata if requested
                if include_metadata:
                    self._write_metadata(f, conn)
                
                # Write schema structure
                self._write_schema_structure(f, conn)
                
                # Write data if requested
                if include_data:
                    self._write_data(f, conn)
                
                # Write footer
                self._write_footer(f)
        
        print(f"✅ Schema backup created: {backup_path}")
        return backup_path
    
    def _write_header(self, f, include_data: bool, include_metadata: bool):
        """Write SQL file header"""
        f.write("-- =====================================================\n")
        f.write("-- Organigramma Web App - Database Schema Backup\n")
        f.write("-- =====================================================\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write(f"-- Database: {self.db_path}\n")
        f.write(f"-- Include Data: {'Yes' if include_data else 'No'}\n")
        f.write(f"-- Include Metadata: {'Yes' if include_metadata else 'No'}\n")
        
        if self.settings:
            f.write(f"-- Application Version: {getattr(self.settings.application, 'version', 'unknown')}\n")
            f.write(f"-- Environment: {getattr(self.settings.application, 'environment', 'unknown')}\n")
        
        f.write("-- =====================================================\n\n")
        
        # SQLite pragmas
        f.write("-- SQLite Configuration\n")
        f.write("PRAGMA foreign_keys = OFF;\n")
        f.write("BEGIN TRANSACTION;\n\n")
    
    def _write_metadata(self, f, conn: sqlite3.Connection):
        """Write database metadata as SQL comments"""
        f.write("-- =====================================================\n")
        f.write("-- DATABASE METADATA\n")
        f.write("-- =====================================================\n\n")
        
        # Database file info
        db_stat = self.db_path.stat()
        f.write(f"-- Database file size: {db_stat.st_size} bytes\n")
        f.write(f"-- Database modified: {datetime.fromtimestamp(db_stat.st_mtime).isoformat()}\n")
        
        # Database pragmas
        pragmas = [
            'user_version', 'schema_version', 'application_id', 'page_size',
            'cache_size', 'journal_mode', 'synchronous', 'foreign_keys'
        ]
        
        f.write("-- Database pragmas:\n")
        for pragma in pragmas:
            try:
                result = conn.execute(f"PRAGMA {pragma}").fetchone()
                if result:
                    f.write(f"--   {pragma}: {result[0]}\n")
            except sqlite3.Error:
                pass
        
        # Table statistics
        f.write("-- Table statistics:\n")
        tables = self._get_tables(conn)
        for table_name in tables:
            try:
                count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                count = count_result[0] if count_result else 0
                f.write(f"--   {table_name}: {count} rows\n")
            except sqlite3.Error:
                f.write(f"--   {table_name}: error counting rows\n")
        
        f.write("\n")
    
    def _write_schema_structure(self, f, conn: sqlite3.Connection):
        """Write complete database schema structure"""
        f.write("-- =====================================================\n")
        f.write("-- SCHEMA STRUCTURE\n")
        f.write("-- =====================================================\n\n")
        
        # Get all schema objects
        schema_objects = self._get_schema_objects(conn)
        
        # Group by type
        tables = [obj for obj in schema_objects if obj['type'] == 'table']
        indexes = [obj for obj in schema_objects if obj['type'] == 'index']
        triggers = [obj for obj in schema_objects if obj['type'] == 'trigger']
        views = [obj for obj in schema_objects if obj['type'] == 'view']
        
        # Write tables
        if tables:
            f.write("-- Tables\n")
            f.write("-- =====================================================\n\n")
            for table in tables:
                f.write(f"-- Table: {table['name']}\n")
                f.write(f"{table['sql']};\n\n")
        
        # Write indexes
        if indexes:
            f.write("-- Indexes\n")
            f.write("-- =====================================================\n\n")
            for index in indexes:
                if not index['name'].startswith('sqlite_autoindex'):
                    f.write(f"-- Index: {index['name']}\n")
                    f.write(f"{index['sql']};\n\n")
        
        # Write triggers
        if triggers:
            f.write("-- Triggers\n")
            f.write("-- =====================================================\n\n")
            for trigger in triggers:
                f.write(f"-- Trigger: {trigger['name']}\n")
                f.write(f"{trigger['sql']};\n\n")
        
        # Write views
        if views:
            f.write("-- Views\n")
            f.write("-- =====================================================\n\n")
            for view in views:
                f.write(f"-- View: {view['name']}\n")
                f.write(f"{view['sql']};\n\n")
    
    def _write_data(self, f, conn: sqlite3.Connection):
        """Write table data as INSERT statements"""
        f.write("-- =====================================================\n")
        f.write("-- TABLE DATA\n")
        f.write("-- =====================================================\n\n")
        
        tables = self._get_tables(conn)
        
        for table_name in tables:
            f.write(f"-- Data for table: {table_name}\n")
            
            try:
                # Get column info
                columns_info = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                column_names = [col[1] for col in columns_info]
                
                # Get data
                cursor = conn.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                if rows:
                    f.write(f"-- {len(rows)} rows\n")
                    
                    for row in rows:
                        # Format values
                        formatted_values = []
                        for value in row:
                            if value is None:
                                formatted_values.append("NULL")
                            elif isinstance(value, str):
                                # Escape single quotes
                                escaped_value = value.replace("'", "''")
                                formatted_values.append(f"'{escaped_value}'")
                            elif isinstance(value, (int, float)):
                                formatted_values.append(str(value))
                            else:
                                formatted_values.append(f"'{str(value)}'")
                        
                        values_str = ", ".join(formatted_values)
                        columns_str = ", ".join(column_names)
                        
                        f.write(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});\n")
                else:
                    f.write("-- No data\n")
                
            except sqlite3.Error as e:
                f.write(f"-- Error reading data: {e}\n")
            
            f.write("\n")
    
    def _write_footer(self, f):
        """Write SQL file footer"""
        f.write("-- =====================================================\n")
        f.write("-- END OF BACKUP\n")
        f.write("-- =====================================================\n\n")
        f.write("COMMIT;\n")
        f.write("PRAGMA foreign_keys = ON;\n")
    
    def _get_schema_objects(self, conn: sqlite3.Connection) -> List[Dict]:
        """Get all schema objects from sqlite_master"""
        cursor = conn.execute("""
            SELECT type, name, tbl_name, sql 
            FROM sqlite_master 
            WHERE sql IS NOT NULL 
            ORDER BY type, name
        """)
        
        objects = []
        for row in cursor.fetchall():
            objects.append({
                'type': row[0],
                'name': row[1],
                'table_name': row[2],
                'sql': row[3]
            })
        
        return objects
    
    def _get_tables(self, conn: sqlite3.Connection) -> List[str]:
        """Get list of user tables"""
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        return [row[0] for row in cursor.fetchall()]
    
    def create_schema_diff(self, other_db_path: Path) -> Path:
        """Create a diff between current schema and another database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        diff_name = f"schema_diff_{timestamp}.sql"
        diff_path = self.backup_dir / diff_name
        
        print(f"🔍 Creating schema diff: {diff_name}")
        
        # Get schemas from both databases
        current_schema = self._get_database_schema(self.db_path)
        other_schema = self._get_database_schema(other_db_path)
        
        with open(diff_path, 'w', encoding='utf-8') as f:
            f.write("-- =====================================================\n")
            f.write("-- Database Schema Diff\n")
            f.write("-- =====================================================\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n")
            f.write(f"-- Current DB: {self.db_path}\n")
            f.write(f"-- Compare DB: {other_db_path}\n")
            f.write("-- =====================================================\n\n")
            
            # Compare tables
            self._write_schema_diff(f, current_schema, other_schema)
        
        print(f"✅ Schema diff created: {diff_path}")
        return diff_path
    
    def _get_database_schema(self, db_path: Path) -> Dict:
        """Get schema information from a database"""
        schema = {'tables': {}, 'indexes': {}, 'triggers': {}, 'views': {}}
        
        with sqlite3.connect(db_path) as conn:
            # Get all schema objects
            objects = self._get_schema_objects(conn)
            
            for obj in objects:
                obj_type = obj['type']
                if obj_type in schema:
                    schema[obj_type][obj['name']] = obj['sql']
        
        return schema
    
    def _write_schema_diff(self, f, current: Dict, other: Dict):
        """Write schema differences"""
        for obj_type in ['tables', 'indexes', 'triggers', 'views']:
            current_objects = current.get(obj_type, {})
            other_objects = other.get(obj_type, {})
            
            # Objects only in current
            only_current = set(current_objects.keys()) - set(other_objects.keys())
            if only_current:
                f.write(f"-- {obj_type.title()} only in current database:\n")
                for name in sorted(only_current):
                    f.write(f"-- + {name}\n")
                f.write("\n")
            
            # Objects only in other
            only_other = set(other_objects.keys()) - set(current_objects.keys())
            if only_other:
                f.write(f"-- {obj_type.title()} only in comparison database:\n")
                for name in sorted(only_other):
                    f.write(f"-- - {name}\n")
                f.write("\n")
            
            # Objects with different definitions
            common = set(current_objects.keys()) & set(other_objects.keys())
            different = []
            for name in common:
                if current_objects[name] != other_objects[name]:
                    different.append(name)
            
            if different:
                f.write(f"-- {obj_type.title()} with different definitions:\n")
                for name in sorted(different):
                    f.write(f"-- ~ {name}\n")
                f.write("\n")
    
    def validate_schema(self) -> Dict:
        """Validate database schema integrity"""
        print("🔍 Validating database schema...")
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
                
                if fk_check:
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Foreign key violations: {len(fk_check)}")
                    for violation in fk_check:
                        validation_results['errors'].append(f"  Table {violation[0]}, row {violation[1]}")
                
                # Check integrity
                integrity_check = conn.execute("PRAGMA integrity_check").fetchone()
                if integrity_check and integrity_check[0] != "ok":
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Integrity check failed: {integrity_check[0]}")
                
                # Get schema statistics
                tables = self._get_tables(conn)
                validation_results['info']['table_count'] = len(tables)
                validation_results['info']['tables'] = tables
                
                # Check for empty tables
                empty_tables = []
                for table in tables:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    if count == 0:
                        empty_tables.append(table)
                
                if empty_tables:
                    validation_results['warnings'].append(f"Empty tables: {', '.join(empty_tables)}")
                
        except sqlite3.Error as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Database error: {e}")
        
        return validation_results
    
    def list_schema_backups(self) -> List[Dict]:
        """List all available schema backups"""
        backups = []
        
        if not self.backup_dir.exists():
            return backups
        
        for file_path in self.backup_dir.glob("schema_backup_*.sql"):
            stat = file_path.stat()
            backups.append({
                'name': file_path.name,
                'path': file_path,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime)
            })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def cleanup_old_backups(self, retention_days: int = 30, max_backups: int = 10) -> int:
        """Clean up old schema backups"""
        backups = self.list_schema_backups()
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        removed_count = 0
        
        # Remove backups older than retention period
        for backup in backups:
            if backup['created'] < cutoff_date:
                backup['path'].unlink()
                print(f"🗑️  Removed old backup: {backup['name']}")
                removed_count += 1
        
        # Keep only max_backups most recent backups
        remaining_backups = self.list_schema_backups()
        if len(remaining_backups) > max_backups:
            for backup in remaining_backups[max_backups:]:
                backup['path'].unlink()
                print(f"🗑️  Removed excess backup: {backup['name']}")
                removed_count += 1
        
        return removed_count

def format_size(size_bytes: int) -> str:
    """Format size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def main():
    """Main schema backup script function"""
    parser = argparse.ArgumentParser(description="Organigramma Web App Schema Backup Tool")
    parser.add_argument("action", choices=["create", "list", "cleanup", "validate", "diff"], 
                       help="Action to perform")
    parser.add_argument("--include-data", action="store_true",
                       help="Include table data in backup")
    parser.add_argument("--no-metadata", action="store_true",
                       help="Don't include metadata in backup")
    parser.add_argument("--db-path", type=str,
                       help="Database file path (default: from config)")
    parser.add_argument("--compare-db", type=str,
                       help="Database to compare with for diff operation")
    parser.add_argument("--retention-days", type=int, default=30,
                       help="Retention period in days (default: 30)")
    parser.add_argument("--max-backups", type=int, default=10,
                       help="Maximum number of backups to keep (default: 10)")
    
    args = parser.parse_args()
    
    try:
        # Initialize schema backup manager
        db_path = Path(args.db_path) if args.db_path else None
        schema_backup = SchemaBackup(db_path=db_path)
        
        if args.action == "create":
            print("🗄️  Creating database schema backup...")
            backup_path = schema_backup.create_schema_backup(
                include_data=args.include_data,
                include_metadata=not args.no_metadata
            )
            
            # Show backup info
            if backup_path.exists():
                size = format_size(backup_path.stat().st_size)
                print(f"📦 Backup size: {size}")
        
        elif args.action == "list":
            print("📋 Available schema backups:")
            backups = schema_backup.list_schema_backups()
            if not backups:
                print("   No backups found.")
            else:
                for i, backup in enumerate(backups, 1):
                    print(f"\n{i}. {backup['name']}")
                    print(f"   📅 Created: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   📦 Size: {format_size(backup['size'])}")
        
        elif args.action == "cleanup":
            print(f"🧹 Cleaning up schema backups older than {args.retention_days} days...")
            removed = schema_backup.cleanup_old_backups(
                retention_days=args.retention_days,
                max_backups=args.max_backups
            )
            print(f"✅ Removed {removed} old backups")
        
        elif args.action == "validate":
            validation = schema_backup.validate_schema()
            
            if validation['valid']:
                print("✅ Database schema is valid")
            else:
                print("❌ Database schema validation failed")
                for error in validation['errors']:
                    print(f"   Error: {error}")
            
            if validation['warnings']:
                print("⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"   {warning}")
            
            if validation['info']:
                info = validation['info']
                print(f"📊 Schema info: {info.get('table_count', 0)} tables")
        
        elif args.action == "diff":
            if not args.compare_db:
                print("❌ --compare-db is required for diff operation")
                sys.exit(1)
            
            compare_db_path = Path(args.compare_db)
            if not compare_db_path.exists():
                print(f"❌ Comparison database not found: {compare_db_path}")
                sys.exit(1)
            
            diff_path = schema_backup.create_schema_diff(compare_db_path)
            size = format_size(diff_path.stat().st_size)
            print(f"📦 Diff size: {size}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()