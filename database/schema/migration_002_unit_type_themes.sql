-- Migration 002: Unit Type Themes System
-- Description: Create unit_type_themes table and add theme support to unit_types
-- Date: 2025-08-01
-- Requirements: 1.1, 5.2, 5.3

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Begin transaction for atomic migration
BEGIN TRANSACTION;

-- ============================================================================
-- UNIT_TYPE_THEMES TABLE CREATION
-- ============================================================================

-- Create unit_type_themes table with all theme configuration fields
CREATE TABLE IF NOT EXISTS unit_type_themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    
    -- Visual Properties
    icon_class TEXT NOT NULL DEFAULT 'diagram-2',
    emoji_fallback TEXT NOT NULL DEFAULT '🏛️',
    
    -- Color Scheme
    primary_color TEXT NOT NULL DEFAULT '#0dcaf0',
    secondary_color TEXT NOT NULL DEFAULT '#f0fdff',
    text_color TEXT NOT NULL DEFAULT '#0dcaf0',
    border_color TEXT,
    
    -- Layout Properties
    border_width INTEGER NOT NULL DEFAULT 2,
    border_style TEXT NOT NULL DEFAULT 'solid',
    background_gradient TEXT,
    
    -- CSS Generation
    css_class_suffix TEXT NOT NULL,
    hover_shadow_color TEXT,
    hover_shadow_intensity REAL DEFAULT 0.25,
    
    -- Display Properties
    display_label TEXT NOT NULL,
    display_label_plural TEXT,
    
    -- Accessibility
    high_contrast_mode BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK(length(name) > 0),
    CHECK(length(icon_class) > 0),
    CHECK(length(emoji_fallback) > 0),
    CHECK(length(primary_color) >= 4),
    CHECK(length(secondary_color) >= 4),
    CHECK(length(text_color) >= 4),
    CHECK(border_width > 0),
    CHECK(length(css_class_suffix) > 0),
    CHECK(length(display_label) > 0),
    CHECK(hover_shadow_intensity >= 0 AND hover_shadow_intensity <= 1)
);

-- Create indexes for performance optimization on unit_type_themes table
CREATE INDEX IF NOT EXISTS idx_unit_type_themes_name ON unit_type_themes(name);
CREATE INDEX IF NOT EXISTS idx_unit_type_themes_is_default ON unit_type_themes(is_default);
CREATE INDEX IF NOT EXISTS idx_unit_type_themes_is_active ON unit_type_themes(is_active);
CREATE INDEX IF NOT EXISTS idx_unit_type_themes_css_class_suffix ON unit_type_themes(css_class_suffix);

-- ============================================================================
-- UNIT_TYPES TABLE ENHANCEMENT
-- ============================================================================

-- Check if theme_id column already exists before adding it
-- SQLite doesn't have IF NOT EXISTS for ALTER TABLE ADD COLUMN, so we use a workaround
-- First, check if the column exists
SELECT CASE 
    WHEN COUNT(*) > 0 THEN 'Column theme_id already exists, skipping...'
    ELSE 'Adding theme_id column...'
END as column_check
FROM pragma_table_info('unit_types') 
WHERE name = 'theme_id';

-- Add theme_id foreign key column to unit_types table (only if it doesn't exist)
-- Note: This will fail gracefully if column already exists, which is handled by the Python script
-- ALTER TABLE unit_types ADD COLUMN theme_id INTEGER REFERENCES unit_type_themes(id);

-- Create index for the new foreign key
CREATE INDEX IF NOT EXISTS idx_unit_types_theme_id ON unit_types(theme_id);

-- ============================================================================
-- DEFAULT THEME DATA INSERTION
-- ============================================================================

-- Insert default themes matching current hardcoded styling
-- Theme 1: Function Theme (for unit_type_id = 1)
INSERT INTO unit_type_themes (
    name, 
    description, 
    icon_class, 
    emoji_fallback, 
    primary_color, 
    secondary_color, 
    text_color, 
    border_color,
    border_width, 
    border_style,
    css_class_suffix, 
    hover_shadow_color,
    hover_shadow_intensity,
    display_label, 
    display_label_plural, 
    is_default,
    is_active,
    created_by
) VALUES (
    'Function Theme', 
    'Bold styling for organizational functions with primary blue colors',
    'building', 
    '🏢', 
    '#0d6efd', 
    '#f8f9ff', 
    '#0d6efd', 
    '#0d6efd',
    4, 
    'solid',
    'function', 
    '#0d6efd',
    0.4,
    'Funzione', 
    'Funzioni', 
    TRUE,
    TRUE,
    'system_migration'
);

-- Theme 2: Organizational Theme (for unit_type_id = 2)
INSERT INTO unit_type_themes (
    name, 
    description, 
    icon_class, 
    emoji_fallback, 
    primary_color, 
    secondary_color, 
    text_color, 
    border_color,
    border_width, 
    border_style,
    css_class_suffix, 
    hover_shadow_color,
    hover_shadow_intensity,
    display_label, 
    display_label_plural, 
    is_default,
    is_active,
    created_by
) VALUES (
    'Organizational Theme',
    'Standard styling for organizational units with info cyan colors', 
    'diagram-2', 
    '🏛️', 
    '#0dcaf0', 
    '#f0fdff', 
    '#0dcaf0', 
    '#0dcaf0',
    2,
    'solid',
    'organizational', 
    '#0dcaf0',
    0.25,
    'Unità Organizzativa', 
    'Unità Organizzative', 
    FALSE,
    TRUE,
    'system_migration'
);

-- ============================================================================
-- ASSIGN THEMES TO EXISTING UNIT TYPES
-- ============================================================================

-- Assign Function Theme to unit_type_id = 1 (Function)
UPDATE unit_types 
SET theme_id = (SELECT id FROM unit_type_themes WHERE name = 'Function Theme')
WHERE id = 1;

-- Assign Organizational Theme to unit_type_id = 2 (OrganizationalUnit)
UPDATE unit_types 
SET theme_id = (SELECT id FROM unit_type_themes WHERE name = 'Organizational Theme')
WHERE id = 2;

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Verify unit_type_themes table structure
SELECT 'Unit Type Themes table columns:' as info;
PRAGMA table_info(unit_type_themes);

-- Verify unit_types table has theme_id column
SELECT 'Unit Types table columns (showing theme_id):' as info;
PRAGMA table_info(unit_types);

-- Verify indexes were created
SELECT 'Unit Type Themes indexes:' as info;
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='unit_type_themes';

SELECT 'Unit Types indexes (including theme_id):' as info;
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='unit_types';

-- Check foreign key constraints
SELECT 'Foreign key constraints on unit_types:' as info;
PRAGMA foreign_key_list(unit_types);

-- Commit transaction
COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================================

-- Verify themes were created
SELECT 'Total themes created:' as info, COUNT(*) as count FROM unit_type_themes;

-- Verify theme assignments
SELECT 'Unit types with theme assignments:' as info, COUNT(*) as count 
FROM unit_types WHERE theme_id IS NOT NULL;

-- Show theme assignments
SELECT 'Theme assignments:' as info;
SELECT ut.id, ut.name as unit_type_name, utt.name as theme_name, utt.display_label
FROM unit_types ut
LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id;

-- Verify default theme exists
SELECT 'Default theme:' as info;
SELECT name, display_label FROM unit_type_themes WHERE is_default = TRUE;

-- Test theme data integrity
SELECT 'Theme data validation:' as info;
SELECT 
    name,
    CASE WHEN length(primary_color) >= 4 THEN 'OK' ELSE 'INVALID' END as primary_color_check,
    CASE WHEN border_width > 0 THEN 'OK' ELSE 'INVALID' END as border_width_check,
    CASE WHEN length(display_label) > 0 THEN 'OK' ELSE 'INVALID' END as display_label_check
FROM unit_type_themes;

SELECT 'Migration 002 completed successfully' as status;