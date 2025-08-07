# Database Schema Backup Documentation

## Overview

The `scripts/backup_schema.py` script provides comprehensive database schema backup capabilities for the Organigramma Web App. It creates detailed SQL backups of the database structure, metadata, and optionally data.

## Features

- ✅ **Complete Schema Export**: Tables, indexes, triggers, views
- ✅ **Metadata Inclusion**: Database statistics, pragmas, table counts
- ✅ **Optional Data Export**: Full table data as INSERT statements
- ✅ **Schema Validation**: Integrity and foreign key constraint checking
- ✅ **Schema Comparison**: Diff between different database versions
- ✅ **Retention Management**: Automatic cleanup of old backups
- ✅ **Detailed Reporting**: Comprehensive backup information

## Usage

### Create Schema Backup

```bash
# Create schema-only backup (default)
python scripts/backup_schema.py create

# Create backup with data included
python scripts/backup_schema.py create --include-data

# Create backup without metadata
python scripts/backup_schema.py create --no-metadata

# Specify custom database path
python scripts/backup_schema.py create --db-path /path/to/database.db
```

### List Available Backups

```bash
# List all schema backups
python scripts/backup_schema.py list
```

### Validate Database Schema

```bash
# Validate current database schema
python scripts/backup_schema.py validate
```

### Compare Schemas

```bash
# Create diff between current and another database
python scripts/backup_schema.py diff --compare-db /path/to/other.db
```

### Cleanup Old Backups

```bash
# Clean up backups older than 30 days, keep max 10
python scripts/backup_schema.py cleanup

# Custom retention policy
python scripts/backup_schema.py cleanup --retention-days 60 --max-backups 20
```

## Backup Structure

### Schema-Only Backup (Default)

```sql
-- =====================================================
-- Organigramma Web App - Database Schema Backup
-- =====================================================
-- Generated: 2025-08-07T21:16:17.127080
-- Database: database/orgchart.db
-- Include Data: No
-- Include Metadata: Yes
-- Application Version: 1.0.0
-- Environment: development
-- =====================================================

-- SQLite Configuration
PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- =====================================================
-- DATABASE METADATA
-- =====================================================

-- Database file size: 139264 bytes
-- Database modified: 2025-08-07T20:00:27.469925
-- Database pragmas:
--   user_version: 0
--   schema_version: 35
--   application_id: 0
--   page_size: 4096
--   cache_size: 2000
--   journal_mode: wal
--   synchronous: 1
--   foreign_keys: 1
-- Table statistics:
--   companies: 1 rows
--   job_titles: 21 rows
--   persons: 22 rows
--   units: 20 rows
--   [... other tables]

-- =====================================================
-- SCHEMA STRUCTURE
-- =====================================================

-- Tables
-- =====================================================

-- Table: companies
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    [... full table definition]
);

-- Table: persons
CREATE TABLE persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    [... full table definition]
);

-- [... all other tables]

-- Indexes
-- =====================================================

-- Index: idx_persons_email
CREATE INDEX idx_persons_email ON persons(email);

-- [... all other indexes]

-- Triggers
-- =====================================================

-- Trigger: update_persons_timestamp
CREATE TRIGGER update_persons_timestamp 
    AFTER UPDATE ON persons
    BEGIN
        UPDATE persons SET datetime_updated = CURRENT_TIMESTAMP 
        WHERE id = NEW.id;
    END;

-- [... all other triggers]

-- =====================================================
-- END OF BACKUP
-- =====================================================

COMMIT;
PRAGMA foreign_keys = ON;
```

### Backup with Data

When using `--include-data`, the backup also includes:

```sql
-- =====================================================
-- TABLE DATA
-- =====================================================

-- Data for table: companies
-- 1 rows
INSERT INTO companies (id, name, short_name, legal_name, vat_number, address, city, postal_code, country, phone, email, website, contact_person_id, start_date, end_date, datetime_created, datetime_updated) VALUES (1, 'Azienda Esempio', 'AE', 'Azienda Esempio S.r.l.', 'IT12345678901', 'Via Roma 123', 'Milano', '20100', 'Italia', '+39 02 1234567', 'info@azienda.it', 'https://www.azienda.it', NULL, '2024-01-01', NULL, '2025-08-05 16:47:11', '2025-08-05 16:47:11');

-- Data for table: persons
-- 22 rows
INSERT INTO persons (id, name, short_name, email, first_name, last_name, registration_no, profile_image, datetime_created, datetime_updated) VALUES (1, 'Mario Rossi', 'ROSSI M.', 'mario.rossi@azienda.it', 'Mario', 'Rossi', 'EMP001', NULL, '2025-08-05 16:47:11', '2025-08-05 16:47:11');
[... all other data rows]
```

## File Locations

- **Backup Directory**: `database/schema/backups/`
- **Backup Files**: `schema_backup_YYYYMMDD_HHMMSS.sql`
- **Diff Files**: `schema_diff_YYYYMMDD_HHMMSS.sql`

## Backup Types and Sizes

| Backup Type | Typical Size | Content |
|-------------|--------------|---------|
| Schema Only | ~14 KB | Structure, metadata, no data |
| Schema + Data | ~43 KB | Structure, metadata, all data |
| Schema Diff | ~2-5 KB | Differences between schemas |

## Validation Features

The script includes comprehensive schema validation:

### Integrity Checks
- **Foreign Key Constraints**: Validates all FK relationships
- **Database Integrity**: SQLite PRAGMA integrity_check
- **Table Statistics**: Row counts and empty table detection

### Example Validation Output
```bash
🔍 Validating database schema...
✅ Database schema is valid
⚠️  Warnings:
   Empty tables: job_title_assignable_units
📊 Schema info: 8 tables
```

## Schema Comparison

The diff feature compares two database schemas:

```bash
python scripts/backup_schema.py diff --compare-db database/old_version.db
```

### Diff Output Example
```sql
-- =====================================================
-- Database Schema Diff
-- =====================================================
-- Generated: 2025-08-07T21:20:00.000000
-- Current DB: database/orgchart.db
-- Compare DB: database/old_version.db
-- =====================================================

-- Tables only in current database:
-- + unit_type_themes

-- Tables only in comparison database:
-- - old_table

-- Tables with different definitions:
-- ~ persons
-- ~ units
```

## Integration with Other Backup Scripts

The schema backup complements other backup scripts:

1. **Database Backup** (`backup_db.py`): Full database file backup
2. **Project Backup** (`backup_project.py`): Complete project backup
3. **Schema Backup** (`backup_schema.py`): Schema structure backup

### Recommended Backup Strategy

```bash
# Daily schema backup
python scripts/backup_schema.py create

# Weekly full database backup
python scripts/backup_db.py create

# Monthly project backup
python scripts/backup_project.py create

# Quarterly cleanup
python scripts/backup_schema.py cleanup --retention-days 90
```

## Automation

### Cron Job Examples

```bash
# Daily schema backup at 1 AM
0 1 * * * cd /path/to/orgchart && python scripts/backup_schema.py create

# Weekly schema backup with data at 2 AM on Sundays
0 2 * * 0 cd /path/to/orgchart && python scripts/backup_schema.py create --include-data

# Monthly cleanup at 3 AM on the 1st
0 3 1 * * cd /path/to/orgchart && python scripts/backup_schema.py cleanup --retention-days 90
```

### Docker Integration

```dockerfile
# Add schema backup capability
COPY scripts/backup_schema.py /app/scripts/
RUN chmod +x /app/scripts/backup_schema.py

# Create backup volume
VOLUME ["/app/database/schema/backups"]

# Add cron job
RUN echo "0 1 * * * cd /app && python scripts/backup_schema.py create" | crontab -
```

## Use Cases

### Development
- **Schema Evolution**: Track schema changes during development
- **Migration Testing**: Compare schemas before/after migrations
- **Debugging**: Analyze schema structure for troubleshooting

### Production
- **Disaster Recovery**: Quick schema restoration
- **Compliance**: Schema documentation for audits
- **Monitoring**: Regular schema validation

### Migration
- **Version Control**: Track schema versions
- **Rollback Planning**: Schema snapshots before changes
- **Environment Sync**: Ensure consistent schemas across environments

## Best Practices

1. **Regular Backups**: Schedule daily schema backups
2. **Version Control**: Store schema backups in version control
3. **Validation**: Run validation before major changes
4. **Documentation**: Include schema backups in deployment docs
5. **Testing**: Test schema restoration procedures
6. **Monitoring**: Monitor backup success/failure
7. **Retention**: Implement appropriate retention policies

## Troubleshooting

### Common Issues

**Database Not Found**
```bash
# Specify database path explicitly
python scripts/backup_schema.py create --db-path /path/to/database.db
```

**Permission Denied**
```bash
# Ensure backup directory is writable
mkdir -p database/schema/backups
chmod 755 database/schema/backups
```

**Large Backup Files**
```bash
# Create schema-only backup (exclude data)
python scripts/backup_schema.py create
```

**Validation Errors**
```bash
# Check foreign key constraints
python scripts/backup_schema.py validate
```

### Debug Information

The script provides detailed error messages and can be debugged by:

1. Checking database file permissions
2. Verifying SQLite database integrity
3. Ensuring sufficient disk space
4. Validating database path configuration

## Performance

- **Schema Backup**: ~1-2 seconds for typical database
- **Data Backup**: ~3-5 seconds with full data
- **Validation**: ~1 second for integrity checks
- **Diff Generation**: ~2-3 seconds comparing schemas

## Security Considerations

1. **Sensitive Data**: Use schema-only backups to avoid data exposure
2. **File Permissions**: Secure backup directory permissions
3. **Storage**: Store backups in secure, encrypted storage
4. **Access Control**: Limit access to backup files
5. **Retention**: Implement secure deletion of old backups

## Future Enhancements

Potential improvements:
- **Incremental Schema Backups**: Track only schema changes
- **Cloud Storage Integration**: Direct upload to cloud storage
- **Email Notifications**: Backup success/failure alerts
- **Web Interface**: GUI for backup management
- **Compression**: Compress large schema backups
- **Encryption**: Encrypt sensitive schema backups