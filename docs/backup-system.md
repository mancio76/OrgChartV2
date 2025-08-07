# Backup System Documentation

## Overview

The Organigramma Web App includes a comprehensive backup system with two specialized scripts:

1. **Database Backup** (`scripts/backup_db.py`) - Focused on database backups with retention policies
2. **Project Backup** (`scripts/backup_project.py`) - Complete project backup respecting `.gitignore` rules

## Project Backup Script

### Features

- ✅ **Respects .gitignore**: Automatically excludes files based on `.gitignore` patterns
- ✅ **Compression**: Creates compressed `.tar.gz` archives by default
- ✅ **Metadata**: Includes comprehensive backup metadata
- ✅ **File Type Analysis**: Analyzes and reports file types in backup
- ✅ **Project Hash**: Generates unique hash for backup verification
- ✅ **Retention Policy**: Automatic cleanup of old backups
- ✅ **Restore Capability**: Full project restoration from backups

### Excluded Files/Directories

The script automatically excludes:

**From .gitignore:**
- `app.log`
- `__pycache__`
- `orgchart.db`
- `database\orgchart.db`
- `*.db-shm`
- `*.db-wal`
- `.DS_Store`
- `*.exclude`

**Additional exclusions:**
- `.git` directory
- `.venv` virtual environment
- `*.pyc`, `*.pyo`, `*.pyd` compiled Python files
- `.pytest_cache`, `.coverage`, `htmlcov` test artifacts
- `node_modules` if present
- `backups/project` (prevents recursive backup)
- Temporary files (`*.tmp`, `*.temp`)

### Usage

#### Create Backup
```bash
# Create compressed backup (default)
python scripts/backup_project.py create

# Create uncompressed backup
python scripts/backup_project.py create --no-compress

# Specify custom project root
python scripts/backup_project.py create --project-root /path/to/project
```

#### List Backups
```bash
# List all available backups
python scripts/backup_project.py list
```

#### Get Backup Information
```bash
# Get detailed information about a specific backup
python scripts/backup_project.py info --backup-path "backups/project/orgchart_project_20250807_210052.tar.gz"
```

#### Restore Backup
```bash
# Restore to default location (./restored_project)
python scripts/backup_project.py restore --backup-path "backups/project/orgchart_project_20250807_210052.tar.gz"

# Restore to specific location
python scripts/backup_project.py restore --backup-path "backups/project/orgchart_project_20250807_210052.tar.gz" --target-path "/path/to/restore"
```

#### Cleanup Old Backups
```bash
# Clean up backups older than 30 days, keep max 5 backups
python scripts/backup_project.py cleanup

# Custom retention policy
python scripts/backup_project.py cleanup --retention-days 60 --max-backups 10
```

### Backup Structure

#### Compressed Backup (.tar.gz)
```
orgchart_project_20250807_210052.tar.gz
├── backup_metadata.json          # Backup metadata
├── .env                          # Environment file
├── .gitignore                    # Git ignore rules
├── app/                          # Application code
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── ...
├── static/                       # Static assets
├── templates/                    # HTML templates
├── scripts/                      # Utility scripts
├── docs/                         # Documentation
└── ...                          # Other project files
```

#### Metadata Structure
```json
{
  "backup_timestamp": "2025-08-07T21:00:52.192275",
  "backup_type": "project_full",
  "project_root": "/path/to/project",
  "total_files": 244,
  "total_size": 3567890,
  "project_hash": "63fa21c6f43bff5f...",
  "file_types": {
    ".py": 90,
    ".html": 62,
    ".md": 26,
    ".js": 10,
    ".css": 6
  },
  "gitignore_patterns": ["app.log", "__pycache__", "*.db"],
  "excluded_patterns": [".git", ".venv", "*.pyc"],
  "compression": "gzip",
  "application_version": "1.0.0",
  "environment": "development",
  "database": {
    "path": "database/orgchart.db",
    "size": 139264,
    "hash": "abc123..."
  }
}
```

### Backup Statistics

A typical project backup includes:
- **~244 files** from the project
- **~3.4 MB** uncompressed size
- **~716 KB** compressed size (79% compression ratio)
- **File types**: Python (90), HTML (62), Markdown (26), JavaScript (10), CSS (6), etc.

### Integration with Existing Database Backup

The project backup complements the existing database backup:

- **Database Backup**: Focused on database files with SQL dumps and metadata
- **Project Backup**: Complete project snapshot excluding temporary/generated files

Both can be used together for comprehensive backup coverage:

```bash
# Create database backup
python scripts/backup_db.py create

# Create project backup
python scripts/backup_project.py create
```

### Automation

#### Cron Job Example
```bash
# Daily project backup at 2 AM
0 2 * * * cd /path/to/orgchart && python scripts/backup_project.py create

# Weekly cleanup
0 3 * * 0 cd /path/to/orgchart && python scripts/backup_project.py cleanup --retention-days 30 --max-backups 5
```

#### Docker Integration
```dockerfile
# Add backup capability to Docker image
COPY scripts/backup_project.py /app/scripts/
RUN chmod +x /app/scripts/backup_project.py

# Create backup volume
VOLUME ["/app/backups"]
```

### Security Considerations

1. **Sensitive Files**: The script respects `.gitignore` to avoid backing up sensitive files
2. **Environment Variables**: `.env` files are included but should be handled carefully
3. **Database Files**: Database files are excluded (use database backup script instead)
4. **Permissions**: Ensure backup directory has appropriate permissions
5. **Storage**: Store backups in secure, encrypted storage for production

### Troubleshooting

#### Common Issues

**Permission Denied**
```bash
chmod +x scripts/backup_project.py
```

**Large Backup Size**
- Check if temporary files are being included
- Verify `.gitignore` patterns are working
- Use `--no-compress` to debug file inclusion

**Missing Files in Backup**
- Check if files match `.gitignore` patterns
- Verify file permissions
- Use `info` command to see what was included

**Restore Issues**
- Ensure target directory exists and is writable
- Check available disk space
- Verify backup file integrity

#### Debug Mode
```bash
# Add verbose output (modify script to include debug prints)
python scripts/backup_project.py create --compress
```

### Best Practices

1. **Regular Backups**: Schedule daily or weekly backups
2. **Test Restores**: Periodically test backup restoration
3. **Multiple Locations**: Store backups in multiple locations
4. **Retention Policy**: Implement appropriate retention policies
5. **Monitoring**: Monitor backup success/failure
6. **Documentation**: Keep backup procedures documented
7. **Security**: Encrypt backups containing sensitive data

### Performance

- **Backup Speed**: ~244 files in ~2 seconds
- **Compression**: ~79% size reduction with gzip
- **Memory Usage**: Minimal memory footprint
- **Disk I/O**: Optimized for sequential file operations

### Future Enhancements

Potential improvements:
- Incremental backups
- Cloud storage integration (AWS S3, Google Cloud)
- Email notifications
- Web interface for backup management
- Backup verification and integrity checks
- Parallel compression for large projects