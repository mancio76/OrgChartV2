-- Migration 001: Enhanced Persons and Companies
-- Description: Add enhanced fields to persons table and create companies table
-- Date: 2025-08-01
-- Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.3

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Begin transaction for atomic migration
BEGIN TRANSACTION;

-- ============================================================================
-- PERSONS TABLE ENHANCEMENTS
-- ============================================================================

-- Add new columns to persons table
-- Note: SQLite doesn't support adding multiple columns in one statement
ALTER TABLE persons ADD COLUMN first_name TEXT;
ALTER TABLE persons ADD COLUMN last_name TEXT;
ALTER TABLE persons ADD COLUMN registration_no TEXT;
ALTER TABLE persons ADD COLUMN profile_image TEXT;

-- Create indexes for performance optimization on persons table
CREATE INDEX IF NOT EXISTS idx_persons_first_name ON persons(first_name);
CREATE INDEX IF NOT EXISTS idx_persons_last_name ON persons(last_name);
CREATE INDEX IF NOT EXISTS idx_persons_registration_no ON persons(registration_no);
CREATE INDEX IF NOT EXISTS idx_persons_email ON persons(email);

-- ============================================================================
-- COMPANIES TABLE CREATION
-- ============================================================================

-- Create companies table with all required fields
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    registration_no TEXT,
    address TEXT,
    city TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'Italy',
    phone TEXT,
    email TEXT,
    website TEXT,
    main_contact_id INTEGER,
    financial_contact_id INTEGER,
    valid_from DATE,
    valid_to DATE,
    notes TEXT,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (main_contact_id) REFERENCES persons(id) ON DELETE SET NULL,
    FOREIGN KEY (financial_contact_id) REFERENCES persons(id) ON DELETE SET NULL,
    
    -- Constraints
    UNIQUE(registration_no),
    CHECK(valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to),
    CHECK(length(name) > 0),
    CHECK(registration_no IS NULL OR length(registration_no) <= 50),
    CHECK(email IS NULL OR email LIKE '%@%'),
    CHECK(website IS NULL OR website LIKE 'http%')
);

-- Create indexes for performance optimization on companies table
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_registration_no ON companies(registration_no);
CREATE INDEX IF NOT EXISTS idx_companies_main_contact ON companies(main_contact_id);
CREATE INDEX IF NOT EXISTS idx_companies_financial_contact ON companies(financial_contact_id);
CREATE INDEX IF NOT EXISTS idx_companies_valid_dates ON companies(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_companies_email ON companies(email);

-- ============================================================================
-- DATA MIGRATION AND VALIDATION
-- ============================================================================

-- Update existing persons records to populate first_name and last_name from name field
-- This is a best-effort migration - manual cleanup may be needed
UPDATE persons 
SET 
    first_name = CASE 
        WHEN instr(name, ' ') > 0 THEN trim(substr(name, 1, instr(name, ' ') - 1))
        ELSE name
    END,
    last_name = CASE 
        WHEN instr(name, ' ') > 0 THEN trim(substr(name, instr(name, ' ') + 1))
        ELSE NULL
    END
WHERE first_name IS NULL AND last_name IS NULL;

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Verify persons table structure
SELECT 'Persons table columns:' as info;
PRAGMA table_info(persons);

-- Verify companies table structure  
SELECT 'Companies table columns:' as info;
PRAGMA table_info(companies);

-- Verify indexes were created
SELECT 'Persons indexes:' as info;
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='persons';

SELECT 'Companies indexes:' as info;
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='companies';

-- Check foreign key constraints
SELECT 'Foreign key constraints:' as info;
PRAGMA foreign_key_list(companies);

-- Commit transaction
COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================================

-- Count records to ensure no data loss
SELECT 'Total persons after migration:' as info, COUNT(*) as count FROM persons;

-- Check that first_name and last_name were populated
SELECT 'Persons with first_name populated:' as info, COUNT(*) as count 
FROM persons WHERE first_name IS NOT NULL;

SELECT 'Persons with last_name populated:' as info, COUNT(*) as count 
FROM persons WHERE last_name IS NOT NULL;

-- Verify companies table is empty but ready
SELECT 'Companies table ready:' as info, COUNT(*) as count FROM companies;

SELECT 'Migration 001 completed successfully' as status;