#!/usr/bin/env python3
"""
Project backup script for Organigramma Web App
Creates compressed backups of the entire project while respecting .gitignore rules
"""

import os
import sys
import shutil
import gzip
import json
import hashlib
import tarfile
import fnmatch
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Set
import argparse

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.config import get_settings
except ImportError:
    # Fallback if app is not available
    get_settings = None

class ProjectBackup:
    """Project backup manager with .gitignore support and compression"""
    
    def __init__(self, project_root: Optional[Path] = None, settings=None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.settings = settings or (get_settings() if get_settings else None)
        self.backup_dir = self.project_root / "backups" / "project"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load .gitignore patterns
        self.gitignore_patterns = self._load_gitignore_patterns()
        
        # Additional patterns to exclude from backup
        self.additional_excludes = {
            '.git',
            '.venv',
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.pytest_cache',
            '.coverage',
            'htmlcov',
            '.tox',
            '.cache',
            'node_modules',
            '.DS_Store',
            'Thumbs.db',
            '*.tmp',
            '*.temp',
            '*.log',
            'backups/project',  # Don't backup the backup directory itself
        }
    
    def _load_gitignore_patterns(self) -> Set[str]:
        """Load patterns from .gitignore file"""
        patterns = set()
        gitignore_path = self.project_root / ".gitignore"
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.add(line)
        
        return patterns
    
    def _should_exclude(self, path: Path, relative_path: Path) -> bool:
        """Check if a path should be excluded based on .gitignore and additional rules"""
        path_str = str(relative_path)
        path_name = path.name
        
        # Check additional excludes
        for pattern in self.additional_excludes:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_name, pattern):
                return True
        
        # Check .gitignore patterns
        for pattern in self.gitignore_patterns:
            # Handle directory patterns
            if pattern.endswith('/'):
                if path.is_dir() and (fnmatch.fnmatch(path_str + '/', pattern) or 
                                    fnmatch.fnmatch(path_name + '/', pattern)):
                    return True
            else:
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_name, pattern):
                    return True
                # Check if any parent directory matches
                for parent in relative_path.parents:
                    if fnmatch.fnmatch(str(parent), pattern):
                        return True
        
        return False
    
    def _get_project_files(self) -> List[Path]:
        """Get list of files to include in backup"""
        files_to_backup = []
        
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            relative_root = root_path.relative_to(self.project_root)
            
            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_exclude(
                root_path / d, relative_root / d
            )]
            
            # Add files
            for file in files:
                file_path = root_path / file
                relative_file_path = relative_root / file
                
                if not self._should_exclude(file_path, relative_file_path):
                    files_to_backup.append(file_path)
        
        return sorted(files_to_backup)
    
    def create_backup(self, compress: bool = True, include_metadata: bool = True) -> Path:
        """Create a project backup with optional compression"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"orgchart_project_{timestamp}"
        
        print(f"🚀 Starting project backup: {backup_name}")
        
        # Get files to backup
        files_to_backup = self._get_project_files()
        print(f"📁 Found {len(files_to_backup)} files to backup")
        
        if compress:
            # Create compressed backup directly
            backup_path = self.backup_dir / f"{backup_name}.tar.gz"
            self._create_compressed_backup(backup_path, files_to_backup, include_metadata)
        else:
            # Create directory backup
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            self._create_directory_backup(backup_path, files_to_backup, include_metadata)
        
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    
    def _create_compressed_backup(self, backup_path: Path, files: List[Path], include_metadata: bool):
        """Create compressed tar.gz backup"""
        with tarfile.open(backup_path, 'w:gz') as tar:
            # Add metadata first
            if include_metadata:
                metadata = self._create_metadata(files)
                metadata_json = json.dumps(metadata, indent=2, default=str)
                
                # Create tarinfo for metadata
                metadata_info = tarfile.TarInfo(name='backup_metadata.json')
                metadata_info.size = len(metadata_json.encode('utf-8'))
                metadata_info.mtime = int(datetime.now().timestamp())
                
                # Add metadata to archive
                tar.addfile(metadata_info, fileobj=tarfile.io.BytesIO(metadata_json.encode('utf-8')))
            
            # Add project files
            for file_path in files:
                relative_path = file_path.relative_to(self.project_root)
                print(f"  📄 Adding: {relative_path}")
                tar.add(file_path, arcname=relative_path)
    
    def _create_directory_backup(self, backup_path: Path, files: List[Path], include_metadata: bool):
        """Create directory-based backup"""
        # Create metadata
        if include_metadata:
            metadata = self._create_metadata(files)
            metadata_path = backup_path / "backup_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
        
        # Copy files maintaining directory structure
        for file_path in files:
            relative_path = file_path.relative_to(self.project_root)
            target_path = backup_path / relative_path
            
            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"  📄 Copying: {relative_path}")
            shutil.copy2(file_path, target_path)
    
    def _create_metadata(self, files: List[Path]) -> Dict:
        """Create backup metadata"""
        total_size = sum(f.stat().st_size for f in files if f.exists())
        
        # Get project statistics
        file_types = {}
        for file_path in files:
            suffix = file_path.suffix.lower() or 'no_extension'
            file_types[suffix] = file_types.get(suffix, 0) + 1
        
        # Calculate project hash (hash of all file hashes)
        project_hash = self._calculate_project_hash(files)
        
        metadata = {
            "backup_timestamp": datetime.now().isoformat(),
            "backup_type": "project_full",
            "project_root": str(self.project_root),
            "total_files": len(files),
            "total_size": total_size,
            "project_hash": project_hash,
            "file_types": file_types,
            "gitignore_patterns": list(self.gitignore_patterns),
            "excluded_patterns": list(self.additional_excludes),
            "compression": "gzip"
        }
        
        # Add application info if available
        if self.settings:
            metadata.update({
                "application_version": getattr(self.settings.application, 'version', 'unknown'),
                "environment": getattr(self.settings.application, 'environment', 'unknown'),
            })
        
        # Add database info if available
        db_path = self.project_root / "database" / "orgchart.db"
        if db_path.exists():
            metadata["database"] = {
                "path": str(db_path.relative_to(self.project_root)),
                "size": db_path.stat().st_size,
                "hash": self._calculate_file_hash(db_path)
            }
        
        return metadata
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return "error_calculating_hash"
    
    def _calculate_project_hash(self, files: List[Path]) -> str:
        """Calculate hash representing the entire project state"""
        hash_sha256 = hashlib.sha256()
        
        for file_path in sorted(files):
            # Add file path to hash
            hash_sha256.update(str(file_path.relative_to(self.project_root)).encode('utf-8'))
            
            # Add file content hash
            file_hash = self._calculate_file_hash(file_path)
            hash_sha256.update(file_hash.encode('utf-8'))
        
        return hash_sha256.hexdigest()
    
    def list_backups(self) -> List[Dict]:
        """List all available project backups"""
        backups = []
        
        if not self.backup_dir.exists():
            return backups
        
        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith('orgchart_project_'):
                # Directory backup
                metadata_path = item / "backup_metadata.json"
                metadata = {}
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except Exception:
                        pass
                
                backups.append({
                    "path": item,
                    "name": item.name,
                    "type": "directory",
                    "size": self._get_directory_size(item),
                    "created": datetime.fromtimestamp(item.stat().st_ctime),
                    "metadata": metadata
                })
            
            elif item.is_file() and item.name.startswith('orgchart_project_') and item.suffix == '.gz':
                # Compressed backup
                metadata = self._extract_metadata_from_archive(item)
                
                backups.append({
                    "path": item,
                    "name": item.name,
                    "type": "compressed",
                    "size": item.stat().st_size,
                    "created": datetime.fromtimestamp(item.stat().st_ctime),
                    "metadata": metadata
                })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory"""
        total_size = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def _extract_metadata_from_archive(self, archive_path: Path) -> Dict:
        """Extract metadata from compressed backup"""
        try:
            with tarfile.open(archive_path, 'r:gz') as tar:
                try:
                    metadata_member = tar.getmember('backup_metadata.json')
                    metadata_file = tar.extractfile(metadata_member)
                    if metadata_file:
                        return json.loads(metadata_file.read().decode('utf-8'))
                except KeyError:
                    pass
        except Exception:
            pass
        return {}
    
    def restore_backup(self, backup_path: Path, target_path: Optional[Path] = None):
        """Restore project from backup"""
        if target_path is None:
            target_path = self.project_root / "restored_project"
        
        target_path = Path(target_path)
        target_path.mkdir(parents=True, exist_ok=True)
        
        print(f"🔄 Restoring project from: {backup_path}")
        print(f"🎯 Target directory: {target_path}")
        
        if backup_path.is_dir():
            # Restore from directory backup
            self._restore_from_directory(backup_path, target_path)
        elif backup_path.suffix == '.gz':
            # Restore from compressed backup
            self._restore_from_archive(backup_path, target_path)
        else:
            raise ValueError(f"Unsupported backup format: {backup_path}")
        
        print(f"✅ Project restored successfully to: {target_path}")
    
    def _restore_from_directory(self, backup_path: Path, target_path: Path):
        """Restore from directory backup"""
        for item in backup_path.rglob('*'):
            if item.is_file() and item.name != 'backup_metadata.json':
                relative_path = item.relative_to(backup_path)
                target_file = target_path / relative_path
                
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_file)
                print(f"  📄 Restored: {relative_path}")
    
    def _restore_from_archive(self, backup_path: Path, target_path: Path):
        """Restore from compressed backup"""
        with tarfile.open(backup_path, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.name != 'backup_metadata.json':
                    print(f"  📄 Extracting: {member.name}")
                    tar.extract(member, target_path)
    
    def cleanup_old_backups(self, retention_days: int = 30, max_backups: int = 5) -> int:
        """Clean up old backups based on retention policy"""
        backups = self.list_backups()
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        removed_count = 0
        
        # Remove backups older than retention period
        for backup in backups:
            if backup["created"] < cutoff_date:
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
            print(f"🗑️  Removed directory backup: {backup_path.name}")
        else:
            backup_path.unlink()
            print(f"🗑️  Removed compressed backup: {backup_path.name}")
    
    def get_backup_info(self, backup_path: Path) -> Dict:
        """Get detailed information about a backup"""
        if backup_path.is_dir():
            metadata_path = backup_path / "backup_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        elif backup_path.suffix == '.gz':
            return self._extract_metadata_from_archive(backup_path)
        
        return {}

def format_size(size_bytes: int) -> str:
    """Format size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def main():
    """Main backup script function"""
    parser = argparse.ArgumentParser(description="Organigramma Web App Project Backup Tool")
    parser.add_argument("action", choices=["create", "list", "cleanup", "restore", "info"], 
                       help="Action to perform")
    parser.add_argument("--compress", action="store_true", default=True,
                       help="Compress backup (default: True)")
    parser.add_argument("--no-compress", action="store_true",
                       help="Don't compress backup")
    parser.add_argument("--retention-days", type=int, default=30,
                       help="Retention period in days (default: 30)")
    parser.add_argument("--max-backups", type=int, default=5,
                       help="Maximum number of backups to keep (default: 5)")
    parser.add_argument("--backup-path", type=str,
                       help="Path to backup for restore/info operation")
    parser.add_argument("--target-path", type=str,
                       help="Target path for restore operation")
    parser.add_argument("--project-root", type=str,
                       help="Project root directory (default: script parent directory)")
    
    args = parser.parse_args()
    
    # Handle compression flags
    compress = args.compress and not args.no_compress
    
    # Set project root
    project_root = Path(args.project_root) if args.project_root else None
    
    try:
        backup_manager = ProjectBackup(project_root=project_root)
        
        if args.action == "create":
            print("🚀 Creating project backup...")
            backup_path = backup_manager.create_backup(compress=compress)
            
            # Show backup info
            if backup_path.exists():
                size = format_size(backup_path.stat().st_size if backup_path.is_file() 
                                 else backup_manager._get_directory_size(backup_path))
                print(f"📦 Backup size: {size}")
            
        elif args.action == "list":
            print("📋 Available project backups:")
            backups = backup_manager.list_backups()
            if not backups:
                print("   No backups found.")
            else:
                for i, backup in enumerate(backups, 1):
                    print(f"\n{i}. {backup['name']}")
                    print(f"   📅 Created: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   📦 Size: {format_size(backup['size'])}")
                    print(f"   📁 Type: {backup['type'].title()}")
                    
                    if backup['metadata']:
                        metadata = backup['metadata']
                        if 'total_files' in metadata:
                            print(f"   📄 Files: {metadata['total_files']}")
                        if 'application_version' in metadata:
                            print(f"   🏷️  Version: {metadata['application_version']}")
        
        elif args.action == "cleanup":
            print(f"🧹 Cleaning up backups older than {args.retention_days} days...")
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
            
            backup_manager.restore_backup(backup_path, target_path)
        
        elif args.action == "info":
            if not args.backup_path:
                print("❌ --backup-path is required for info operation")
                sys.exit(1)
            
            backup_path = Path(args.backup_path)
            info = backup_manager.get_backup_info(backup_path)
            
            if info:
                print(f"📋 Backup Information: {backup_path.name}")
                print(f"   📅 Created: {info.get('backup_timestamp', 'Unknown')}")
                print(f"   📄 Total Files: {info.get('total_files', 'Unknown')}")
                print(f"   📦 Total Size: {format_size(info.get('total_size', 0))}")
                print(f"   🏷️  App Version: {info.get('application_version', 'Unknown')}")
                print(f"   🌍 Environment: {info.get('environment', 'Unknown')}")
                print(f"   🔐 Project Hash: {info.get('project_hash', 'Unknown')[:16]}...")
                
                if 'file_types' in info:
                    print(f"   📊 File Types:")
                    for ext, count in sorted(info['file_types'].items()):
                        print(f"      {ext}: {count}")
            else:
                print("❌ Could not read backup metadata")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()