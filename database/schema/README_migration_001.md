# Migration 001: Enhanced Persons and Companies

## Overview

This migration enhances the database structure to support:

1. **Enhanced Person Fields**: Adds `first_name`, `last_name`, `registration_no`, and `profile_image` fields to the persons table
2. **Companies Management**: Creates a new companies table with full contact management
3. **Performance Optimization**: Adds database indexes for improved query performance
4. **Profile Images**: Creates directory structure for storing profile images

## Requirements Addressed

- **1.1-1.5**: Enhanced person name handling with separate first/last name fields
- **2.1-2.4**: Person registration number and profile image support
- **3.1-3.8**: Complete company management with contact relationships
- **4.1-4.5**: Database structure enhancements with proper indexing
- **6.1-6.4**: Profile image support and storage

## Files Included

- `migration_001_enhanced_persons_companies.sql` - Main migration script
- `rollback_001_enhanced_persons_companies.sql` - Rollback script
- `migrate_001_enhanced_persons_companies.py` - Python migration executor
- `README_migration_001.md` - This documentation

## Database Changes

### Persons Table Enhancements

**New Columns Added:**
- `first_name TEXT` - Person's first name
- `last_name TEXT` - Person's last name  
- `registration_no TEXT` - Registration/employee number (max 25 chars)
- `profile_image TEXT` - Path to profile image file (max 1024 chars)

**New Indexes:**
- `idx_persons_first_name` - Index on first_name for search performance
- `idx_persons_last_name` - Index on last_name for search performance
- `idx_persons_registration_no` - Index on registration_no for lookups
- `idx_persons_email` - Index on email for search performance

### Companies Table Creation

**New Table:** `companies`

**Columns:**
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `name TEXT NOT NULL` - Company name
- `short_name TEXT` - Short/abbreviated name
- `registration_no TEXT UNIQUE` - Company registration number
- `address TEXT` - Street address
- `city TEXT` - City
- `postal_code TEXT` - Postal/ZIP code
- `country TEXT DEFAULT 'Italy'` - Country
- `phone TEXT` - Phone number
- `email TEXT` - Email address
- `website TEXT` - Website URL
- `main_contact_id INTEGER` - FK to persons table
- `financial_contact_id INTEGER` - FK to persons table
- `valid_from DATE` - Validity start date
- `valid_to DATE` - Validity end date
- `notes TEXT` - Additional notes
- `datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`

**Constraints:**
- Foreign keys to persons table with SET NULL on delete
- Unique constraint on registration_no
- Check constraints for data validation
- Date range validation (valid_from <= valid_to)

**Indexes:**
- `idx_companies_name` - Company name search
- `idx_companies_registration_no` - Registration number lookups
- `idx_companies_main_contact` - Main contact queries
- `idx_companies_financial_contact` - Financial contact queries
- `idx_companies_valid_dates` - Date range queries
- `idx_companies_email` - Email search

## Data Migration

The migration automatically attempts to populate `first_name` and `last_name` from the existing `name` field:

- **Single word names**: Moved to `first_name`, `last_name` set to NULL
- **Multiple word names**: First word to `first_name`, remaining words to `last_name`

**Note**: Manual cleanup may be needed for complex names or special cases.

## Directory Structure

Creates `static/profiles/` directory for storing profile images with appropriate permissions.

## Usage

### Execute Migration

```bash
# Dry run (preview changes)
python scripts/migrate_001_enhanced_persons_companies.py --dry-run

# Execute migration
python scripts/migrate_001_enhanced_persons_companies.py

# Execute with custom database path
python scripts/migrate_001_enhanced_persons_companies.py --db-path /path/to/database.db
```

### Execute Rollback

```bash
# Dry run rollback (preview changes)
python scripts/migrate_001_enhanced_persons_companies.py --rollback --dry-run

# Execute rollback
python scripts/migrate_001_enhanced_persons_companies.py --rollback
```

## Safety Features

1. **Automatic Backup**: Creates timestamped database backup before migration
2. **Transaction Safety**: All changes wrapped in transactions
3. **Prerequisite Checks**: Verifies database state before execution
4. **Status Verification**: Checks migration status to prevent double-application
5. **Rollback Support**: Complete rollback capability with data preservation
6. **Dry Run Mode**: Preview changes without executing them

## Verification

After migration, verify:

1. **Persons table** has new columns: `first_name`, `last_name`, `registration_no`, `profile_image`
2. **Companies table** exists with all required columns and constraints
3. **Indexes** are created for performance optimization
4. **Foreign key constraints** are properly configured
5. **Data integrity** - no data loss in existing persons records
6. **Profiles directory** exists and is writable

## Rollback Considerations

**⚠️ WARNING**: Rollback will permanently delete:
- All data in new person fields (`first_name`, `last_name`, `registration_no`, `profile_image`)
- Entire companies table and all company data
- Profile images directory (files remain but directory structure removed)

Ensure you have proper backups before executing rollback.

## Troubleshooting

### Common Issues

1. **Foreign key constraint errors**: Ensure foreign keys are enabled
2. **Permission errors**: Check database file and directory permissions
3. **Partial migration**: Use rollback first, then re-run migration
4. **Backup failures**: Ensure sufficient disk space and write permissions

### Recovery

If migration fails:
1. Restore from automatic backup created before migration
2. Check error logs for specific issues
3. Fix underlying problems
4. Re-run migration

## Testing

After migration, test:
1. Person creation with new fields
2. Company creation and management
3. Foreign key relationships
4. Profile image upload and display
5. Search functionality with new indexes
6. Backward compatibility with existing code

## Performance Impact

Expected performance improvements:
- Faster person name searches (indexed first_name/last_name)
- Efficient company lookups (indexed registration_no)
- Optimized contact relationship queries
- Better email-based searches

## Next Steps

After successful migration:
1. Update Person model to include new fields
2. Update PersonService for new field handling
3. Create Company model and CompanyService
4. Update person forms and templates
5. Create company management interface
6. Update tests for new functionality