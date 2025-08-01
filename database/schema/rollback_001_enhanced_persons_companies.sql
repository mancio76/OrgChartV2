-- Rollback 001: Enhanced Persons and Companies
-- Description: Rollback migration 001 - remove enhanced fields and companies table
-- Date: 2025-08-01
-- WARNING: This will permanently delete data in the new columns and companies table

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Begin transaction for atomic rollback
BEGIN TRANSACTION;

-- ============================================================================
-- ROLLBACK COMPANIES TABLE
-- ============================================================================

-- Drop companies table and all its data
DROP TABLE IF EXISTS companies;

-- ============================================================================
-- ROLLBACK PERSONS TABLE ENHANCEMENTS
-- ============================================================================

-- SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
-- Create temporary table with original structure
CREATE TABLE persons_backup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    email TEXT,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from current persons table to backup (only original columns)
INSERT INTO persons_backup (id, name, short_name, email, datetime_created, datetime_updated)
SELECT id, name, short_name, email, datetime_created, datetime_updated
FROM persons;

-- Drop the current persons table
DROP TABLE persons;

-- Rename backup table to persons
ALTER TABLE persons_backup RENAME TO persons;

-- Recreate original indexes
CREATE INDEX IF NOT EXISTS idx_persons_email_original ON persons(email);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify persons table structure is back to original
SELECT 'Persons table columns after rollback:' as info;
PRAGMA table_info(persons);

-- Verify companies table is gone
SELECT 'Companies table exists:' as info, 
       CASE WHEN COUNT(*) > 0 THEN 'YES - ROLLBACK FAILED' ELSE 'NO - ROLLBACK SUCCESS' END as status
FROM sqlite_master WHERE type='table' AND name='companies';

-- Count records to ensure no data loss in core fields
SELECT 'Total persons after rollback:' as info, COUNT(*) as count FROM persons;

-- Commit rollback transaction
COMMIT;

SELECT 'Rollback 001 completed' as status;