-- Rollback 002: Unit Type Themes System
-- Description: Rollback unit_type_themes table and theme support from unit_types
-- Date: 2025-08-01

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Begin transaction for atomic rollback
BEGIN TRANSACTION;

-- ============================================================================
-- ROLLBACK UNIT_TYPES TABLE CHANGES
-- ============================================================================

-- Note: SQLite doesn't support DROP COLUMN, so we need to recreate the table
-- First, create a backup of the current unit_types table
CREATE TABLE unit_types_backup AS SELECT * FROM unit_types;

-- Drop the current unit_types table
DROP TABLE unit_types;

-- Recreate unit_types table without theme_id column
CREATE TABLE unit_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT,
    level INTEGER NOT NULL DEFAULT 1,
    aliases TEXT, -- JSON array degli alias
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(name),
    UNIQUE(short_name)
);

-- Restore data without theme_id column
INSERT INTO unit_types (id, name, short_name, level, aliases, datetime_created, datetime_updated)
SELECT id, name, short_name, level, aliases, datetime_created, datetime_updated
FROM unit_types_backup;

-- Drop the backup table
DROP TABLE unit_types_backup;

-- ============================================================================
-- DROP UNIT_TYPE_THEMES TABLE
-- ============================================================================

-- Drop indexes first
DROP INDEX IF EXISTS idx_unit_type_themes_name;
DROP INDEX IF EXISTS idx_unit_type_themes_is_default;
DROP INDEX IF EXISTS idx_unit_type_themes_is_active;
DROP INDEX IF EXISTS idx_unit_type_themes_css_class_suffix;

-- Drop the unit_type_themes table
DROP TABLE IF EXISTS unit_type_themes;

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Verify unit_types table structure (should not have theme_id)
SELECT 'Unit Types table columns after rollback:' as info;
PRAGMA table_info(unit_types);

-- Verify unit_type_themes table is gone
SELECT 'Unit Type Themes table exists:' as info, 
       CASE WHEN COUNT(*) > 0 THEN 'YES (ERROR)' ELSE 'NO (OK)' END as status
FROM sqlite_master WHERE type='table' AND name='unit_type_themes';

-- Verify data integrity
SELECT 'Unit types count after rollback:' as info, COUNT(*) as count FROM unit_types;

-- Commit transaction
COMMIT;

SELECT 'Rollback 002 completed successfully' as status;