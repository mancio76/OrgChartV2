-- =====================================================
-- Organigramma Web App - Database Schema Backup
-- =====================================================
-- Generated: 2025-08-07T21:20:05.389558
-- Database: database/orgchart.db
-- Include Data: Yes
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
-- TABLE DATA
-- =====================================================

-- Data for table: companies
-- 1 rows
INSERT INTO companies (id, name, short_name, registration_no, address, city, postal_code, country, phone, email, website, main_contact_id, financial_contact_id, valid_from, valid_to, notes, datetime_created, datetime_updated) VALUES (1, 'OpenEconomics Srl', 'OE', NULL, NULL, NULL, NULL, 'Italy', NULL, 'info@openeconomics.eu', 'https://www.openeconomics.eu', NULL, NULL, NULL, NULL, NULL, '2025-08-06 13:45:45', '2025-08-06 13:45:45');

-- Data for table: job_title_assignable_units
-- No data

-- Data for table: job_titles
-- 21 rows
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (1, 'Socio', 'SOC', '[]', NULL, NULL, '2025-08-06 14:13:22', '2025-08-06 14:13:22');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (2, 'Membro', 'MEM', '[]', NULL, NULL, '2025-08-06 14:13:38', '2025-08-06 14:13:38');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (3, 'Internal Auditor', 'IA', '[]', NULL, NULL, '2025-08-06 14:14:10', '2025-08-06 14:14:10');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (4, 'Presidente', 'PRES', '[]', NULL, NULL, '2025-08-06 14:19:25', '2025-08-06 14:19:25');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (5, 'Amministratore Delegato', 'AD', '[]', NULL, NULL, '2025-08-06 14:27:44', '2025-08-06 14:27:44');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (6, 'Data Protection Officer', 'DPO', '[]', NULL, NULL, '2025-08-06 14:29:29', '2025-08-06 14:29:29');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (7, 'Staff', 'STAFF', '[]', NULL, NULL, '2025-08-06 14:37:49', '2025-08-06 14:37:49');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (8, 'Head', 'HEAD', '[]', NULL, NULL, '2025-08-06 15:07:22', '2025-08-06 15:07:22');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (9, 'Media Relations Manager', 'MRM', '[]', NULL, NULL, '2025-08-06 15:09:40', '2025-08-06 15:09:40');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (10, 'Chief', 'CHIEF', '[]', NULL, NULL, '2025-08-06 15:14:12', '2025-08-06 15:14:12');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (11, 'Chief Information Officer / Chief Technology Officer', 'CIO/CTO', '[]', NULL, NULL, '2025-08-07 07:59:41', '2025-08-07 07:59:41');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (12, 'Chief Financial Officer', 'CFO', '[]', NULL, NULL, '2025-08-07 08:06:30', '2025-08-07 08:06:30');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (13, 'Chief Product Officer', 'CPO', '[]', NULL, NULL, '2025-08-07 08:12:38', '2025-08-07 08:12:38');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (14, 'Program Management Officer', 'PMO', '[]', NULL, NULL, '2025-08-07 13:41:41', '2025-08-07 13:41:41');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (15, 'UX Designer', 'UXD', '[]', NULL, NULL, '2025-08-07 13:48:26', '2025-08-07 13:48:26');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (16, 'UI Designer', 'UID', '[]', NULL, NULL, '2025-08-07 13:48:41', '2025-08-07 13:48:41');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (17, 'Product Owner Analytics', 'POA', '[]', NULL, NULL, '2025-08-07 14:00:49', '2025-08-07 14:00:49');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (18, 'Manager', 'MGR', '[]', NULL, NULL, '2025-08-07 14:09:28', '2025-08-07 14:09:28');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (19, 'Product Operations Senior Expert', 'POSE', '[]', NULL, NULL, '2025-08-07 14:48:18', '2025-08-07 14:48:18');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (20, 'Product Operations Expert', 'POE', '[]', NULL, NULL, '2025-08-07 14:49:02', '2025-08-07 14:49:02');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (21, 'Team Investor Relations And M-A Manager', 'TIRMAM', '[]', NULL, NULL, '2025-08-07 16:48:12', '2025-08-07 16:48:12');

-- Data for table: person_job_assignments
-- 28 rows
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (1, 1, 4, 3, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:15:14', '2025-08-06 14:15:14');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (2, 2, 2, 2, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:16:55', '2025-08-06 14:16:55');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (3, 3, 5, 2, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:18:21', '2025-08-06 14:18:21');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (4, 4, 3, 4, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:20:16', '2025-08-06 14:20:16');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (5, 5, 3, 2, 1, 1.0, 0, 0, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:21:11', '2025-08-06 14:21:11');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (6, 6, 3, 2, 1, 1.0, 0, 0, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:22:09', '2025-08-06 14:22:09');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (7, 5, 7, 5, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:28:07', '2025-08-06 14:28:07');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (8, 7, 6, 6, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:29:49', '2025-08-06 14:29:49');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (9, 8, 8, 7, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 14:39:25', '2025-08-06 14:39:25');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (10, 9, 9, 2, 1, 1.0, 0, 1, NULL, NULL, NULL, '2025-07-01', 0, '2025-08-06 15:06:17', '2025-08-06 15:08:49');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (11, 9, 9, 8, 1, 1.0, 1, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 15:07:46', '2025-08-06 15:07:46');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (12, 10, 9, 9, 1, 1.0, 0, 0, NULL, NULL, NULL, NULL, 1, '2025-08-06 15:10:41', '2025-08-06 15:10:41');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (13, 11, 10, 10, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-06 15:14:39', '2025-08-06 15:14:39');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (14, 12, 11, 11, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 08:00:32', '2025-08-07 08:00:32');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (15, 13, 12, 8, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 08:02:42', '2025-08-07 08:02:42');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (16, 14, 13, 12, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 08:06:57', '2025-08-07 08:06:57');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (17, 15, 14, 13, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 08:13:35', '2025-08-07 08:13:35');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (18, 16, 15, 14, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 13:42:15', '2025-08-07 13:42:15');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (19, 15, 16, 8, 1, 1.0, 0, 1, NULL, NULL, NULL, '2025-08-07', 0, '2025-08-07 13:44:06', '2025-08-07 13:44:06');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (20, 17, 17, 8, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 13:46:44', '2025-08-07 13:46:44');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (21, 19, 17, 15, 1, 1.0, 0, 0, NULL, NULL, NULL, NULL, 1, '2025-08-07 13:57:58', '2025-08-07 13:57:58');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (22, 15, 16, 8, 2, 1.0, 1, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 13:58:42', '2025-08-07 13:58:42');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (23, 15, 14, 17, 1, 1.0, 1, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 14:01:44', '2025-08-07 14:01:44');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (24, 18, 17, 16, 1, 1.0, 0, 0, NULL, NULL, NULL, NULL, 1, '2025-08-07 14:02:51', '2025-08-07 14:02:51');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (25, 20, 18, 18, 1, 1.0, 0, 1, NULL, NULL, NULL, '2025-08-07', 0, '2025-08-07 14:11:12', '2025-08-07 14:11:12');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (26, 20, 18, 18, 2, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 14:25:39', '2025-08-07 14:25:39');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (27, 21, 19, 21, 1, 1.0, 0, 0, NULL, NULL, NULL, NULL, 1, '2025-08-07 16:51:50', '2025-08-07 16:51:50');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (28, 22, 20, 18, 1, 1.0, 0, 1, NULL, NULL, NULL, NULL, 1, '2025-08-07 17:50:32', '2025-08-07 17:50:32');

-- Data for table: persons
-- 22 rows
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (1, 'Benedetto Verdino', 'VERDINO B.', NULL, '2025-08-06 14:14:53', '2025-08-06 14:14:53', 'Benedetto', 'Verdino', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (2, 'C Padovani', 'PADOVANI C.', NULL, '2025-08-06 14:16:30', '2025-08-06 14:16:30', 'C', 'Padovani', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (3, 'F Orioli', 'ORIOLI F.', NULL, '2025-08-06 14:17:46', '2025-08-06 14:17:46', 'F', 'Orioli', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (4, 'Gianluca Calvosa', 'CALVOSA C.', NULL, '2025-08-06 14:19:58', '2025-08-06 14:19:58', 'Gianluca', 'Calvosa', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (5, 'Raffaele Nardone', 'NARDONE R.', NULL, '2025-08-06 14:20:56', '2025-08-06 14:20:56', 'Raffaele', 'Nardone', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (6, 'Francesco Becchelli', 'BECCHELLI F.', NULL, '2025-08-06 14:21:51', '2025-08-06 14:21:51', 'Francesco', 'Becchelli', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (7, 'FINDATA Srl', 'FINDATA', NULL, '2025-08-06 14:28:59', '2025-08-06 14:28:59', 'FINDATA Srl', NULL, NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (8, 'Alessia Zanini', 'ZANINI A.', NULL, '2025-08-06 14:38:13', '2025-08-06 14:38:13', 'Alessia', 'Zanini', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (9, 'Martina Casani', 'CASANI M.', NULL, '2025-08-06 15:05:42', '2025-08-06 15:05:42', 'Martina', 'Casani', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (10, 'Andrea Zanini', 'ZANINI A.', NULL, '2025-08-06 15:10:20', '2025-08-06 15:10:20', 'Andrea', 'Zanini', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (11, 'Giovanni Uboldi', 'UBOLDI G.', NULL, '2025-08-06 15:13:10', '2025-08-06 15:13:10', 'Giovanni', 'Uboldi', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (12, 'Paolo Mancini', 'MANCINI P.', 'paolo.mancini@openeconomics.eu', '2025-08-07 07:55:51', '2025-08-07 07:55:51', 'Paolo', 'Mancini', NULL, 'profiles/mancini.paolo.png');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (13, 'Silvio Longo', 'LONGO S.', NULL, '2025-08-07 08:02:22', '2025-08-07 08:02:22', 'Silvio', 'Longo', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (14, 'Daniele Nardone', 'NARDONE D.', NULL, '2025-08-07 08:05:17', '2025-08-07 08:05:17', 'Daniele', 'Nardone', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (15, 'Fabrizio Ferrara', 'FERRARA F.', NULL, '2025-08-07 08:13:11', '2025-08-07 08:13:11', 'Fabrizio', 'Ferrara', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (16, 'Valentina Frisotti', 'FRISOTTI V.', NULL, '2025-08-07 13:40:18', '2025-08-07 13:40:18', 'Valentina', 'Frisotti', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (17, 'Erica Prato', 'PRATO E.', NULL, '2025-08-07 13:46:12', '2025-08-07 13:46:12', 'Erica', 'Prato', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (18, 'Lorenzo Stalfieri', 'STALFIERI L.', NULL, '2025-08-07 13:49:12', '2025-08-07 13:49:12', 'Lorenzo', 'Stalfieri', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (19, 'Mohamad Bey El Merhabi', 'BEY EL MERHABI M.', NULL, '2025-08-07 13:51:26', '2025-08-07 13:51:26', 'Mohamad', 'Bey El Merhabi', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (20, 'Guido Di Toro Mammarella', 'DI TORO G.', NULL, '2025-08-07 14:09:08', '2025-08-07 14:09:08', 'Guido', 'Di Toro Mammarella', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (21, 'Alfredo Scermino', 'SCERMINO A.', NULL, '2025-08-07 16:48:40', '2025-08-07 16:48:40', 'Alfredo', 'Scermino', NULL, NULL);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated, first_name, last_name, registration_no, profile_image) VALUES (22, 'Monica Nardone', 'NARDONE M.', NULL, '2025-08-07 17:49:55', '2025-08-07 17:49:55', 'Monica', 'Nardone', NULL, NULL);

-- Data for table: unit_type_themes
-- 4 rows
INSERT INTO unit_type_themes (id, name, description, icon_class, emoji_fallback, primary_color, secondary_color, text_color, border_color, border_width, border_style, background_gradient, css_class_suffix, hover_shadow_color, hover_shadow_intensity, display_label, display_label_plural, high_contrast_mode, is_default, is_active, created_by, datetime_created, datetime_updated) VALUES (1, 'Function Theme', 'Bold styling for organizational functions with primary blue colors', 'building', '🏢', '#a6cbff', '#f8f9ff', '#193983', '#0d6efd', 3, 'solid', NULL, 'function', '#0d6efd', 0.4, 'Funzione', 'Funzioni', 0, 1, 1, 'system_migration', '2025-08-05 16:47:30', '2025-08-06 13:35:28');
INSERT INTO unit_type_themes (id, name, description, icon_class, emoji_fallback, primary_color, secondary_color, text_color, border_color, border_width, border_style, background_gradient, css_class_suffix, hover_shadow_color, hover_shadow_intensity, display_label, display_label_plural, high_contrast_mode, is_default, is_active, created_by, datetime_created, datetime_updated) VALUES (2, 'Organizational Theme', 'Standard styling for organizational units with info cyan colors', 'diagram-2', '🏛️', '#d3f6fb', '#c9ebef', '#447187', '#0dcaf0', 2, 'solid', NULL, 'organizational', '#0dcaf0', 0.3, 'Unità Organizzativa', 'Unità Organizzative', 0, 0, 1, 'system_migration', '2025-08-05 16:47:30', '2025-08-06 13:26:43');
INSERT INTO unit_type_themes (id, name, description, icon_class, emoji_fallback, primary_color, secondary_color, text_color, border_color, border_width, border_style, background_gradient, css_class_suffix, hover_shadow_color, hover_shadow_intensity, display_label, display_label_plural, high_contrast_mode, is_default, is_active, created_by, datetime_created, datetime_updated) VALUES (3, 'Company Unit Theme', 'Company Unit Theme - Bold styling for organizational functions with primary blue colors', 'bag', '🧳​', '#dec5ff', '#f5f4fa', '#402378', '#9441da', 3, 'solid', NULL, 'company', '#9441da', 0.5, 'Unità', 'Unità', 0, 0, 1, 'system', '2025-08-05 17:56:38', '2025-08-06 13:35:11');
INSERT INTO unit_type_themes (id, name, description, icon_class, emoji_fallback, primary_color, secondary_color, text_color, border_color, border_width, border_style, background_gradient, css_class_suffix, hover_shadow_color, hover_shadow_intensity, display_label, display_label_plural, high_contrast_mode, is_default, is_active, created_by, datetime_created, datetime_updated) VALUES (4, 'Team Theme', 'Copia di Company Unit Theme - Company Unit Theme - Bold styling for organizational functions with primary blue colors', 'bookmark-tabs', '📑', '#fac65f', '#f9f2d8', '#b2563a', '#d23b33', 3, 'solid', NULL, 'team', '#d23b33', 0.5, 'Team', 'Team', 0, 0, 1, 'system', '2025-08-07 17:36:26', '2025-08-07 17:46:29');

-- Data for table: unit_types
-- 4 rows
INSERT INTO unit_types (id, name, short_name, level, aliases, datetime_created, datetime_updated, theme_id) VALUES (1, 'Unità', 'U', 1, '[]', '2025-08-06 05:42:04', '2025-08-06 05:42:04', 3);
INSERT INTO unit_types (id, name, short_name, level, aliases, datetime_created, datetime_updated, theme_id) VALUES (2, 'Funzione', 'FN', 2, '[]', '2025-08-06 05:42:44', '2025-08-06 05:42:44', 1);
INSERT INTO unit_types (id, name, short_name, level, aliases, datetime_created, datetime_updated, theme_id) VALUES (3, 'Unità Organizzativa', 'UO', 3, '[]', '2025-08-06 05:43:43', '2025-08-06 05:43:43', 2);
INSERT INTO unit_types (id, name, short_name, level, aliases, datetime_created, datetime_updated, theme_id) VALUES (4, 'Team', 'TEAM', 3, '[]', '2025-08-07 17:47:19', '2025-08-07 17:47:19', 4);

-- Data for table: units
-- 20 rows
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (1, 'Assemblea Dei Soci', 'ADS', '[]', 1, NULL, NULL, NULL, '2025-08-06 13:37:11', '2025-08-06 13:37:11');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (2, 'Organo Di Vigilanza', 'ODV', '[]', 1, 3, NULL, NULL, '2025-08-06 13:38:42', '2025-08-06 13:38:42');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (3, 'Consiglio Di Amministrazione', 'CDA', '[]', 1, 1, NULL, NULL, '2025-08-06 13:41:24', '2025-08-06 13:41:24');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (4, 'Internal Auditing', 'IA', '[]', 1, 3, NULL, NULL, '2025-08-06 13:55:22', '2025-08-06 13:55:22');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (5, 'Sindaco', 'SIN', '[]', 1, 1, NULL, NULL, '2025-08-06 13:56:37', '2025-08-06 13:56:37');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (6, 'Data Protection Office', 'DPO', '[]', 1, 3, NULL, NULL, '2025-08-06 14:26:14', '2025-08-06 14:26:14');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (7, 'Amministrazione Aziendale', 'AA', '[]', 1, 3, NULL, NULL, '2025-08-06 14:27:12', '2025-08-06 14:27:12');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (8, 'Segreteria Di Direzione', 'SDD', '[]', 2, 3, NULL, NULL, '2025-08-06 14:39:02', '2025-08-06 14:39:02');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (9, 'Corporate Communications And Media Relations', 'CCMR', '[]', 2, 3, NULL, NULL, '2025-08-06 14:50:54', '2025-08-06 14:50:54');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (10, 'Commercial', 'SELLS', '[]', 2, 3, NULL, NULL, '2025-08-06 15:12:39', '2025-08-06 15:12:39');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (11, 'IT And Security', 'IAS', '[]', 2, 7, NULL, NULL, '2025-08-07 07:55:11', '2025-08-07 07:55:11');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (12, 'Human Resources', 'HR', '[]', 2, 7, NULL, NULL, '2025-08-07 08:01:59', '2025-08-07 08:01:59');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (13, 'Amministrazione Finanza E Controllo', 'AFC', '[]', 2, 7, NULL, NULL, '2025-08-07 08:04:47', '2025-08-07 08:04:47');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (14, 'Product Design And Delivery', 'PDD', '[]', 2, 7, NULL, NULL, '2025-08-07 08:07:52', '2025-08-07 08:07:52');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (15, 'Program Management Office', 'PMO', '[]', 3, 14, NULL, NULL, '2025-08-07 13:36:07', '2025-08-07 13:36:07');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (16, 'Product Strategy', 'PS', '[]', 3, 14, NULL, NULL, '2025-08-07 13:43:39', '2025-08-07 13:43:39');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (17, 'Service And UX-UI Design', 'SUD', '[]', 3, 14, NULL, NULL, '2025-08-07 13:45:50', '2025-08-07 13:45:50');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (18, 'Product Owner Public Funding', 'POPF', '[]', 3, 14, NULL, NULL, '2025-08-07 14:07:51', '2025-08-07 14:07:51');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (19, 'Team Investor Relations And M-A', 'TIRMA', '[]', 3, 13, NULL, NULL, '2025-08-07 16:51:18', '2025-08-07 16:51:18');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (20, 'Amministrazione Finanza And Procurement', 'AFP', '[]', 4, 13, NULL, NULL, '2025-08-07 16:53:12', '2025-08-07 16:53:12');

-- =====================================================
-- END OF BACKUP
-- =====================================================

COMMIT;
PRAGMA foreign_keys = ON;
