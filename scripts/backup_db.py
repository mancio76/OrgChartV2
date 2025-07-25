#!/usr/bin/env python3
"""
Database backup script for Organigramma Web App
Supports automated backups with retention policies and cloud storage
"""

import os
import sys
import shutil
import sqlite3
import gzip
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import argparse

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

class DatabaseBackup:
    """Database backup manager with retention policies"""
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.backup_dir = Path(self.settings.database.backup_directory)
        self.db_path = Path(self.settings.database.url.replace("sqlite:///", ""))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, compress: bool = True, include_metadata: bool = True) -> Path:
        """Create a database backup with optional compression"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"orgchart_backup_{timestamp}"
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        
        # Create backup directory for this backup
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Copy database file
        db_backup_path = backup_path / "orgchart.db"
        shutil.copy2(self.db_path, db_backup_path)
        
        # Create metadata
        if include_metadata:
            metadata = self._create_metadata()
            metadata_path = backup_path / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
        
        # Create SQL dump
        sql_dump_path = backup_path / "orgchart_dump.sql"
        self._create_sql_dump(sql_dump_path)
        
        # Compress if requested
        if compress:
            compressed_path = self._compress_backup(backup_path)
            shutil.rmtree(backup_path)  # Remove uncompressed version
            return compressed_path
        
        return backup_path
    
    def _create_metadata(self) -> Dict:
        """Create backup metadata"""
        # Get database statistics
        stats = self._get_database_stats()
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(self.db_path)
        
        return {
            "backup_timestamp": datetime.now().isoformat(),
            "database_path": str(self.db_path),
            "database_size": self.db_path.stat().st_size,
            "database_hash": file_hash,
            "application_version": self.settings.application.version,
            "environment": self.settings.application.environment,
            "statistics": stats,
            "backup_type": "full",
            "compression": "gzip"
        }
    
    def _get_database_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get table counts
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    stats[f"{table_name}_count"] = count
                
                # Get database info
                cursor.execute("PRAGMA database_list")
                db_info = cursor.fetchall()
                stats["database_info"] = db_info
                
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _create_sql_dump(self, output_path: Path):
        """Create SQL dump of database"""
        with sqlite3.connect(self.db_path) as conn:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"-- Organigramma Web App Database Dump\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {self.db_path}\n\n")
                
                # Enable foreign keys
                f.write("PRAGMA foreign_keys = ON;\n\n")
                
                # Dump schema and data
                for line in conn.iterdump():
                    f.write(f"{line}\n")
    
    def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup directory"""
        compressed_path = backup_path.with_suffix('.tar.gz')
        
        import tarfile
        with tarfile.open(compressed_path, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        return compressed_path
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith('orgchart_backup_'):
                # Uncompressed backup
                metadata_path = item / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    backups.append({
                        "path": item,
                        "type": "directory",
                        "metadata": metadata
                    })
            elif item.is_file() and item.name.startswith('orgchart_backup_') and item.suffix == '.gz':
                # Compressed backup
                backups.append({
                    "path": item,
                    "type": "compressed",
                    "size": item.stat().st_size,
                    "created": datetime.fromtimestamp(item.stat().st_ctime)
                })
        
        return sorted(backups, key=lambda x: x.get("metadata", {}).get("backup_timestamp", x.get("created", "")), reverse=True)
    
    def cleanup_old_backups(self, retention_days: int = 30, max_backups: int = 10):
        """Clean up old backups based on retention policy"""
        backups = self.list_backups()
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        removed_count = 0
        
        # Remove backups older than retention period
        for backup in backups:
            backup_date = None
            if backup["type"] == "directory" and "metadata" in backup:
                backup_date = datetime.fromisoformat(backup["metadata"]["backup_timestamp"])
            elif backup["type"] == "compressed":
                backup_date = backup["created"]
            
            if backup_date and backup_date < cutoff_date:
                self._remove_backup(backup["path"])
                removed_count += 1
        
        # Keep only max_backups most recent backups
        remaining_backups = self.list_backups()
        if len(remaining_backups) > max_backups:
            for backup in remaining_backups[max_backups:]:
                self._remove_backup(backup["path"])
                removed_count += 1
        
        return removed_count
    
    def _remove_backup(self, backup_path: Path):
        """Remove a backup (directory or file)"""
        if backup_path.is_dir():
            shutil.rmtree(backup_path)
        else:
            backup_path.unlink()
    
    def restore_backup(self, backup_path: Path, target_path: Optional[Path] = None):
        """Restore database from backup"""
        if target_path is None:
            target_path = self.db_path
        
        # Create backup of current database
        if target_path.exists():
            backup_current = target_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            shutil.copy2(target_path, backup_current)
            print(f"Current database backed up to: {backup_current}")
        
        if backup_path.is_dir():
            # Restore from directory backup
            source_db = backup_path / "orgchart.db"
            if source_db.exists():
                shutil.copy2(source_db, target_path)
            else:
                raise FileNotFoundError(f"Database file not found in backup: {source_db}")
        elif backup_path.suffix == '.gz':
            # Extract and restore from compressed backup
            import tarfile
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(path=self.backup_dir / "temp_restore")
                
                # Find the database file
                temp_dir = self.backup_dir / "temp_restore"
                for item in temp_dir.rglob("orgchart.db"):
                    shutil.copy2(item, target_path)
                    break
                else:
                    raise FileNotFoundError("Database file not found in compressed backup")
                
                # Cleanup temp directory
                shutil.rmtree(temp_dir)
        else:
            raise ValueError(f"Unsupported backup format: {backup_path}")
        
        print(f"Database restored from: {backup_path}")
        print(f"Restored to: {target_path}")

def main():
    """Main backup script function"""
    parser = argparse.ArgumentParser(description="Organigramma Web App Database Backup Tool")
    parser.add_argument("action", choices=["create", "list", "cleanup", "restore"], 
                       help="Action to perform")
    parser.add_argument("--compress", action="store_true", default=True,
                       help="Compress backup (default: True)")
    parser.add_argument("--no-compress", action="store_true",
                       help="Don't compress backup")
    parser.add_argument("--retention-days", type=int, default=30,
                       help="Retention period in days (default: 30)")
    parser.add_argument("--max-backups", type=int, default=10,
                       help="Maximum number of backups to keep (default: 10)")
    parser.add_argument("--backup-path", type=str,
                       help="Path to backup for restore operation")
    parser.add_argument("--target-path", type=str,
                       help="Target path for restore operation")
    
    args = parser.parse_args()
    
    # Handle compression flags
    compress = args.compress and not args.no_compress
    
    try:
        backup_manager = DatabaseBackup()
        
        if args.action == "create":
            print("Creating database backup...")
            backup_path = backup_manager.create_backup(compress=compress)
            print(f"✅ Backup created: {backup_path}")
            
        elif args.action == "list":
            print("Available backups:")
            backups = backup_manager.list_backups()
            if not backups:
                print("No backups found.")
            else:
                for i, backup in enumerate(backups, 1):
                    if backup["type"] == "directory":
                        metadata = backup["metadata"]
                        print(f"{i}. {backup['path'].name}")
                        print(f"   Created: {metadata['backup_timestamp']}")
                        print(f"   Size: {metadata['database_size']} bytes")
                        print(f"   Environment: {metadata['environment']}")
                    else:
                        print(f"{i}. {backup['path'].name}")
                        print(f"   Created: {backup['created']}")
                        print(f"   Size: {backup['size']} bytes")
                        print(f"   Type: Compressed")
                    print()
        
        elif args.action == "cleanup":
            print(f"Cleaning up backups older than {args.retention_days} days...")
            removed = backup_manager.cleanup_old_backups(
                retention_days=args.retention_days,
                max_backups=args.max_backups
            )
            print(f"✅ Removed {removed} old backups")
        
        elif args.action == "restore":
            if not args.backup_path:
                print("❌ --backup-path is required for restore operation")
                sys.exit(1)
            
            backup_path = Path(args.backup_path)
            target_path = Path(args.target_path) if args.target_path else None
            
            print(f"Restoring database from: {backup_path}")
            backup_manager.restore_backup(backup_path, target_path)
            print("✅ Database restored successfully")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()