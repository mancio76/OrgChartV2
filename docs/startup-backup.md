# Startup Backup Documentation

## Overview

The Organigramma Web App includes an automatic startup backup feature that creates database backups when the application starts. This ensures that you always have a recent backup before the application begins processing data.

## Configuration

The startup backup feature is controlled by environment variables in the `.env` file:

### Basic Backup Control

```bash
# Enable/disable startup backup
DATABASE_BACKUP_ENABLED=true

# Backup directory
DATABASE_BACKUP_DIRECTORY=backups
```

### Backup Type Control

```bash
# Create schema backup on startup
DATABASE_BACKUP_SCHEMA=true

# Include data in schema backup
DATABASE_BACKUP_DATA=false
```

## Backup Types

### Schema Backup (`DATABASE_BACKUP_SCHEMA=true`)

- **Purpose**: Backs up database structure (tables, indexes, triggers, views)
- **Size**: ~14 KB (schema only) or ~43 KB (with data)
- **Format**: SQL file with complete schema definition
- **Location**: `database/schema/backups/schema_backup_YYYYMMDD_HHMMSS.sql`

### Database Backup (Always Created)

- **Purpose**: Complete database file backup with metadata
- **Size**: Variable based on database size
- **Format**: Compressed tar.gz archive
- **Location**: `backups/orgchart_backup_YYYYMMDD_HHMMSS.tar.gz`

## Configuration Examples

### Development Setup (Default)
```bash
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_SCHEMA=true
DATABASE_BACKUP_DATA=false
```

**Result**: Creates schema-only backup + full database backup on startup

### Production Setup
```bash
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_SCHEMA=true
DATABASE_BACKUP_DATA=true
DATABASE_BACKUP_DIRECTORY=/var/backups/orgchart
```

**Result**: Creates schema backup with data + full database backup on startup

### Minimal Setup
```bash
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_SCHEMA=false
DATABASE_BACKUP_DATA=false
```

**Result**: Creates only full database backup on startup

### Disabled Backup
```bash
DATABASE_BACKUP_ENABLED=false
```

**Result**: No backups created on startup

## Startup Output

### With Backup Enabled
```
============================================================
🏢 ORGANIGRAMMA WEB APP
============================================================
📋 Application: Organigramma Web App v1.0.0
🌍 Environment: DEVELOPMENT
🚀 Server: http://127.0.0.1:8000
📊 Debug mode: ON
📝 Log level: DEBUG
👥 Workers: 1
🔒 Security: HTTP
🔒 CSRF: OFF
============================================================
🔄 Performing startup database backup...
   📋 Creating schema backup...
   ✅ Schema backup completed successfully
      🗄️  Creating database schema backup...
      🗄️  Creating schema backup: schema_backup_20250807_213008.sql
      ✅ Schema backup created: database/schema/backups/schema_backup_20250807_213008.sql
      📦 Backup size: 14.0 KB
   📋 Creating database backup...
   ✅ Database backup completed successfully
      Creating database backup...
      ✅ Backup created: backups/orgchart_backup_20250807_213008.tar.gz
✅ Startup backup process completed
```

### With Backup Disabled
```
============================================================
🏢 ORGANIGRAMMA WEB APP
============================================================
📋 Application: Organigramma Web App v1.0.0
🌍 Environment: DEVELOPMENT
🚀 Server: http://127.0.0.1:8000
📊 Debug mode: ON
📝 Log level: DEBUG
👥 Workers: 1
🔒 Security: HTTP
🔒 CSRF: OFF
============================================================
```

## Implementation Details

### Backup Process Flow

1. **Check Configuration**: Verify if `DATABASE_BACKUP_ENABLED=true`
2. **Schema Backup**: If `DATABASE_BACKUP_SCHEMA=true`, create schema backup
   - Include data if `DATABASE_BACKUP_DATA=true`
3. **Database Backup**: Always create full database backup when backup is enabled
4. **Error Handling**: Continue startup even if backup fails

### Error Handling

The startup backup includes comprehensive error handling:

- **Timeout Protection**: Backup operations timeout after 60 seconds
- **Script Not Found**: Graceful handling if backup scripts are missing
- **Permission Errors**: Continues startup if backup directory is not writable
- **Database Locked**: Handles database lock situations

### Example Error Output
```
🔄 Performing startup database backup...
   📋 Creating schema backup...
   ⚠️  Schema backup failed (exit code: 1)
      Error: Database is locked
   📋 Creating database backup...
   ✅ Database backup completed successfully
✅ Startup backup process completed
```

## Performance Impact

### Backup Times
- **Schema Backup**: ~1-2 seconds
- **Database Backup**: ~2-3 seconds
- **Total Startup Delay**: ~3-5 seconds

### Disk Usage
- **Schema Backup**: 14 KB (schema only) / 43 KB (with data)
- **Database Backup**: Variable (typically 100-500 KB compressed)
- **Daily Growth**: ~50-100 KB per day with default settings

## Best Practices

### Development Environment
```bash
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_SCHEMA=true
DATABASE_BACKUP_DATA=false
```

**Rationale**: Quick schema backups for development, minimal disk usage

### Staging Environment
```bash
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_SCHEMA=true
DATABASE_BACKUP_DATA=true
```

**Rationale**: Full backups with data for testing scenarios

### Production Environment
```bash
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_SCHEMA=true
DATABASE_BACKUP_DATA=true
DATABASE_BACKUP_DIRECTORY=/var/backups/orgchart
```

**Rationale**: Complete backups with secure storage location

### High-Frequency Restart Environment
```bash
DATABASE_BACKUP_ENABLED=false
```

**Rationale**: Disable to avoid excessive backup creation during development

## Integration with Existing Backup System

The startup backup complements the existing backup scripts:

- **Startup Backup**: Automatic backup on application start
- **Scheduled Backup**: Regular backups via cron jobs
- **Manual Backup**: On-demand backups via scripts

### Recommended Combined Strategy

```bash
# Startup backup for immediate protection
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_SCHEMA=true
DATABASE_BACKUP_DATA=false

# Scheduled backups for regular protection
# Daily schema backup
0 1 * * * cd /path/to/app && python scripts/backup_schema.py create

# Weekly full backup
0 2 * * 0 cd /path/to/app && python scripts/backup_db.py create

# Monthly cleanup
0 3 1 * * cd /path/to/app && python scripts/backup_schema.py cleanup
```

## Troubleshooting

### Common Issues

**Backup Scripts Not Found**
```
⚠️  Schema backup script not found
```
**Solution**: Ensure `scripts/backup_schema.py` and `scripts/backup_db.py` exist

**Permission Denied**
```
⚠️  Schema backup failed (exit code: 1)
   Error: Permission denied
```
**Solution**: Ensure backup directories are writable

**Database Locked**
```
⚠️  Database backup failed (exit code: 1)
   Error: Database is locked
```
**Solution**: Ensure no other processes are using the database

**Timeout Issues**
```
⚠️  Schema backup timed out after 60 seconds
```
**Solution**: Check database size and disk performance

### Debugging

To debug startup backup issues:

1. **Test Backup Scripts Manually**:
   ```bash
   python scripts/backup_schema.py create
   python scripts/backup_db.py create
   ```

2. **Check Configuration**:
   ```bash
   python -c "from app.config import get_settings; s=get_settings(); print(f'Backup enabled: {s.database.backup_enabled}')"
   ```

3. **Test Startup Function**:
   ```bash
   python -c "from run import perform_startup_backup; from app.config import get_settings; perform_startup_backup(get_settings())"
   ```

## Security Considerations

1. **Backup Location**: Ensure backup directory has appropriate permissions
2. **Data Sensitivity**: Consider disabling data backup if database contains sensitive information
3. **Disk Space**: Monitor disk usage to prevent storage exhaustion
4. **Backup Retention**: Implement cleanup policies for old backups

## Future Enhancements

Potential improvements:
- **Conditional Backup**: Only backup if database has changed
- **Backup Verification**: Verify backup integrity after creation
- **Cloud Upload**: Automatic upload to cloud storage
- **Notification**: Email/Slack notifications for backup status
- **Incremental Backup**: Only backup changes since last backup