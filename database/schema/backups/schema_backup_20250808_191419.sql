-- =====================================================
-- Organigramma Web App - Database Schema Backup
-- =====================================================
-- Generated: 2025-08-08T19:14:19.608683
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

-- Database file size: 184320 bytes
-- Database modified: 2025-08-08T14:40:12.539145
-- Database pragmas:
--   user_version: 0
--   schema_version: 44
--   application_id: 0
--   page_size: 4096
--   cache_size: 2000
--   journal_mode: wal
--   synchronous: 1
--   foreign_keys: 1
-- Table statistics:
--   audit_data_changes: 11 rows
--   audit_operation_files: 0 rows
--   audit_operations: 5 rows
--   companies: 1 rows
--   job_title_assignable_units: 0 rows
--   job_titles: 21 rows
--   person_job_assignments: 28 rows
--   persons: 22 rows
--   unit_type_themes: 4 rows
--   unit_types: 4 rows
--   units: 20 rows

-- =====================================================
-- SCHEMA STRUCTURE
-- =====================================================

-- Tables
-- =====================================================

-- Table: audit_data_changes
CREATE TABLE audit_data_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            change_type TEXT NOT NULL,
            old_values TEXT,    -- JSON object
            new_values TEXT,    -- JSON object
            line_number INTEGER,
            timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (operation_id) REFERENCES audit_operations (operation_id)
        );

-- Table: audit_operation_files
CREATE TABLE audit_operation_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,  -- 'input' or 'output'
            file_size INTEGER,
            file_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (operation_id) REFERENCES audit_operations (operation_id)
        );

-- Table: audit_operations
CREATE TABLE audit_operations (
            operation_id TEXT PRIMARY KEY,
            operation_type TEXT NOT NULL,
            status TEXT NOT NULL,
            user_id TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            file_path TEXT,
            file_format TEXT,
            entity_types TEXT,  -- JSON array
            options TEXT,       -- JSON object
            results TEXT,       -- JSON object
            error_count INTEGER DEFAULT 0,
            warning_count INTEGER DEFAULT 0,
            records_processed TEXT,  -- JSON object
            records_created TEXT,    -- JSON object
            records_updated TEXT,    -- JSON object
            records_skipped TEXT,    -- JSON object
            metadata TEXT,      -- JSON object
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

-- Table: companies
CREATE TABLE companies (
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

-- Table: job_title_assignable_units
CREATE TABLE job_title_assignable_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title_id INTEGER NOT NULL,
    unit_id INTEGER NOT NULL,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_title_id) REFERENCES job_titles(id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE,
    UNIQUE(job_title_id, unit_id)
);

-- Table: job_titles
CREATE TABLE job_titles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT,
    aliases TEXT, -- JSON array degli alias multilingua
    start_date DATE,
    end_date DATE,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: person_job_assignments
CREATE TABLE person_job_assignments (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
  person_id INTEGER NOT NULL, 
  unit_id INTEGER NOT NULL, 
  job_title_id INTEGER NOT NULL, 
  version INTEGER NOT NULL DEFAULT 1, 
  percentage REAL NOT NULL DEFAULT 1.0 CHECK (percentage > 0 AND percentage <= 1), 
  is_ad_interim BOOLEAN NOT NULL DEFAULT "FALSE", 
  is_unit_boss BOOLEAN NOT NULL DEFAULT (0), 
  notes TEXT, 
  flags TEXT, 
  valid_from DATE, 
  valid_to DATE, 
  is_current BOOLEAN NOT NULL DEFAULT "TRUE", 
  datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
  datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
  
  FOREIGN KEY (person_id) REFERENCES persons (id) ON DELETE CASCADE, 
  FOREIGN KEY (unit_id) REFERENCES units (id), 
  FOREIGN KEY (job_title_id) REFERENCES job_titles (id)
);

-- Table: persons
CREATE TABLE persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    email TEXT,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
, first_name TEXT, last_name TEXT, registration_no TEXT, profile_image TEXT);

-- Table: sqlite_sequence
CREATE TABLE sqlite_sequence(name,seq);

-- Table: unit_type_themes
CREATE TABLE unit_type_themes (
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

-- Table: unit_types
CREATE TABLE unit_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT,
	level INTEGER NOT NULL DEFAULT 1,
    aliases TEXT, -- JSON array degli alias
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, theme_id INTEGER REFERENCES unit_type_themes(id),

    UNIQUE(name),
    UNIQUE(short_name)
);

-- Table: units
CREATE TABLE units (
  id INTEGER PRIMARY KEY, 
  name TEXT NOT NULL, 
  short_name TEXT, 
  aliases TEXT, 
  unit_type_id INTEGER DEFAULT (1) NOT NULL, 
  parent_unit_id INTEGER, 
  start_date DATE, 
  end_date DATE, 
  datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
  datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
  
  FOREIGN KEY (parent_unit_id) REFERENCES units (id)
);

-- Indexes
-- =====================================================

-- Index: idx_audit_data_changes_entity_type
CREATE INDEX idx_audit_data_changes_entity_type ON audit_data_changes (entity_type);

-- Index: idx_audit_data_changes_operation_id
CREATE INDEX idx_audit_data_changes_operation_id ON audit_data_changes (operation_id);

-- Index: idx_audit_operation_files_operation_id
CREATE INDEX idx_audit_operation_files_operation_id ON audit_operation_files (operation_id);

-- Index: idx_audit_operations_start_time
CREATE INDEX idx_audit_operations_start_time ON audit_operations (start_time);

-- Index: idx_audit_operations_status
CREATE INDEX idx_audit_operations_status ON audit_operations (status);

-- Index: idx_audit_operations_user_id
CREATE INDEX idx_audit_operations_user_id ON audit_operations (user_id);

-- Index: idx_companies_email
CREATE INDEX idx_companies_email ON companies(email);

-- Index: idx_companies_financial_contact
CREATE INDEX idx_companies_financial_contact ON companies(financial_contact_id);

-- Index: idx_companies_main_contact
CREATE INDEX idx_companies_main_contact ON companies(main_contact_id);

-- Index: idx_companies_name
CREATE INDEX idx_companies_name ON companies(name);

-- Index: idx_companies_registration_no
CREATE INDEX idx_companies_registration_no ON companies(registration_no);

-- Index: idx_companies_valid_dates
CREATE INDEX idx_companies_valid_dates ON companies(valid_from, valid_to);

-- Index: idx_persons_email
CREATE INDEX idx_persons_email ON persons(email);

-- Index: idx_persons_first_name
CREATE INDEX idx_persons_first_name ON persons(first_name);

-- Index: idx_persons_last_name
CREATE INDEX idx_persons_last_name ON persons(last_name);

-- Index: idx_persons_registration_no
CREATE INDEX idx_persons_registration_no ON persons(registration_no);

-- Index: idx_unit_type_themes_css_class_suffix
CREATE INDEX idx_unit_type_themes_css_class_suffix ON unit_type_themes(css_class_suffix);

-- Index: idx_unit_type_themes_is_active
CREATE INDEX idx_unit_type_themes_is_active ON unit_type_themes(is_active);

-- Index: idx_unit_type_themes_is_default
CREATE INDEX idx_unit_type_themes_is_default ON unit_type_themes(is_default);

-- Index: idx_unit_type_themes_name
CREATE INDEX idx_unit_type_themes_name ON unit_type_themes(name);

-- Index: idx_unit_types_theme_id
CREATE INDEX idx_unit_types_theme_id ON unit_types(theme_id);

-- Views
-- =====================================================

-- View: assignment_history
CREATE VIEW assignment_history AS SELECT p.id AS person_id,
       p.name AS person_name,
       u.name AS unit_name,
       jt.name AS job_title_name,
       pja.version,
       pja.percentage,
       pja.is_ad_interim,
       pja.is_unit_boss,
       pja.valid_from,
       pja.valid_to,
       pja.is_current,
       pja.datetime_created,
       pja.datetime_updated,
       CASE WHEN pja.is_current THEN 'CURRENT' WHEN pja.valid_to IS NOT NULL THEN 'TERMINATED' ELSE 'HISTORICAL' END AS status
  FROM person_job_assignments pja
       JOIN
       persons p ON pja.person_id = p.id
       JOIN
       units u ON pja.unit_id = u.id
       JOIN
       job_titles jt ON pja.job_title_id = jt.id
 ORDER BY p.name,
          u.name,
          jt.name,
          pja.version DESC;

-- View: current_assignments
CREATE VIEW current_assignments AS SELECT pja.id,
p.id AS person_id,
   p.name AS person_name,
   p.short_name AS person_short_name,
   u.id AS unit_id,
   u.unit_name AS unit_name,
   u.unit_short_name AS unit_short_name,
   jt.id AS job_title_id,
   jt.name AS job_title_name,
   jt.short_name AS job_title_short_name,
   pja.percentage,
   pja.is_ad_interim,
   pja.is_unit_boss,
   pja.notes,
   pja.flags,
   pja.valid_from,
   pja.valid_to,
   pja.version,
   pja.datetime_created,
   pja.datetime_updated
FROM person_job_assignments pja
   JOIN
   persons p ON pja.person_id = p.id
   JOIN
   units_types u ON pja.unit_id = u.id
   JOIN
   job_titles jt ON pja.job_title_id = jt.id
 WHERE pja.is_current = 1;

-- View: get_complete_tree
CREATE VIEW get_complete_tree AS WITH RECURSIVE unit_tree AS
(
SELECT u.id,
   u.unit_name AS name,
   u.unit_short_name AS short_name,
   u.unit_type_id,
   u.parent_unit_id,
   0 AS level,
   CAST (u.id AS TEXT) AS path,
   ifnull(unit_short_name,unit_name) AS short_path,
   unit_name AS full_path
FROM units_types u
WHERE u.parent_unit_id IS NULL OR
  u.parent_unit_id = -1
UNION ALL
SELECT u.id,
   u.unit_name AS name,
   u.unit_short_name AS short_name,
   u.unit_type_id,
   u.parent_unit_id,
   ut.level + 1,
   ut.path || '/' || CAST (u.id AS TEXT),
   ut.short_path || ' > ' || ifnull(u.unit_short_name,u.unit_name),
   ut.full_path || ' > ' || u.unit_name
FROM units_types u
 JOIN
 unit_tree ut ON u.parent_unit_id = ut.id
)
SELECT ut.*,
 COUNT(DISTINCT pja.person_id) AS person_count,
 COUNT(DISTINCT child_units.id) AS children_count
FROM unit_tree ut
LEFT JOIN
person_job_assignments pja ON ut.id = pja.unit_id AND
                             pja.is_current = 1
LEFT JOIN
units child_units ON child_units.parent_unit_id = ut.id
GROUP BY ut.id,
   ut.name,
   ut.short_name,
   ut.unit_type_id,
   ut.parent_unit_id,
   ut.level,
   ut.path
  ORDER BY ut.path;

-- View: unit_get_list_query
CREATE VIEW unit_get_list_query AS SELECT u.*,
    ut.name AS unit_type,
    ut.short_name AS unit_type_short,
    p.name AS parent_name,
    COUNT(DISTINCT c.id) AS children_count,
    COUNT(DISTINCT ca.id) AS person_count
FROM units u
LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
LEFT JOIN units p ON u.parent_unit_id = p.id
LEFT JOIN units c ON c.parent_unit_id = u.id
LEFT JOIN current_assignments ca ON ca.unit_id = u.id
GROUP BY u.id,
   u.name,
   u.short_name,
   u.unit_type_id,
   u.parent_unit_id,
   u.start_date,
   u.end_date,
   u.aliases,
   u.datetime_created,
   u.datetime_updated,
   p.name
ORDER BY u.unit_type_id,
   u.name;

-- View: units_hierarchy
CREATE VIEW units_hierarchy AS WITH RECURSIVE unit_tree AS (-- Nodi radice (parent_unit_id = -1 o NULL)
    SELECT id,
           unit_name name,
           unit_short_name AS short_name,
           unit_type,
           unit_type_short,
           parent_unit_id,
           0 AS level,
           CAST (id AS TEXT) AS path,
           ifnull(unit_short_name, unit_name) AS short_path,
           unit_name AS full_path
      FROM units_types
     WHERE parent_unit_id IS NULL OR
           parent_unit_id = -1
    UNION ALL-- Nodi figli
    SELECT u.id,
           u.unit_name,
           u.unit_short_name,
           u.unit_type,
           u.unit_type_short,
           u.parent_unit_id,
           ut.level + 1,
           ut.path || '/' || CAST (u.id AS TEXT),
           ut.short_path || ' > ' || ifnull(u.unit_short_name, u.unit_name),
           ut.full_path || ' > ' || u.unit_name
      FROM units_types u
           JOIN
           unit_tree ut ON u.parent_unit_id = ut.id
)
SELECT *
  FROM unit_tree
 ORDER BY path;

-- View: units_hierarchy_stats
CREATE VIEW units_hierarchy_stats AS SELECT uh.id
    , uh.name
    , uh.short_name
    , uh.unit_type
    , uh.unit_type_short
    , uh.parent_unit_id
    , uh.level
    , uh.path
    , uh.full_path
    , count(pja.id) person_count
    , ifnull(max(pja.is_unit_boss), 0) has_boss
FROM units_hierarchy uh
LEFT OUTER JOIN person_job_assignments pja ON uh.id=pja.unit_id
GROUP BY uh.id
    , uh.name
    , uh.short_name
    , uh.unit_type
    , uh.unit_type_short
    , uh.parent_unit_id
    , uh.level
    , uh.path
    , uh.full_path;

-- View: units_types
CREATE VIEW units_types AS SELECT u.id,
    u.name AS unit_name,
    u.short_name AS unit_short_name,
    u.unit_type_id,
    ut.name AS unit_type,
    ut.short_name AS unit_type_short,
    u.aliases AS unit_aliases,
    u.parent_unit_id,
    u.start_date,
    u.end_date
FROM units u
JOIN unit_types ut ON u.unit_type_id = ut.id;

-- =====================================================
-- END OF BACKUP
-- =====================================================

COMMIT;
PRAGMA foreign_keys = ON;
