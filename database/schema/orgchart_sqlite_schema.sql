--
-- File generated with SQLiteStudio v3.4.17 on ven ago 1 12:09:10 2025
--
-- Text encoding used: UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: job_title_assignable_units
CREATE TABLE IF NOT EXISTS job_title_assignable_units (
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
CREATE TABLE IF NOT EXISTS job_titles (
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
CREATE TABLE IF NOT EXISTS person_job_assignments (
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
CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    email TEXT,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: unit_types
CREATE TABLE IF NOT EXISTS unit_types (
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

-- Table: units
CREATE TABLE IF NOT EXISTS units (
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

-- View: assignment_history
CREATE VIEW IF NOT EXISTS assignment_history AS SELECT p.id AS person_id,
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
CREATE VIEW IF NOT EXISTS current_assignments AS SELECT pja.id,
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
CREATE VIEW IF NOT EXISTS get_complete_tree AS WITH RECURSIVE unit_tree AS
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
CREATE VIEW IF NOT EXISTS unit_get_list_query AS SELECT u.*,
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
CREATE VIEW IF NOT EXISTS units_hierarchy AS WITH RECURSIVE unit_tree AS (-- Nodi radice (parent_unit_id = -1 o NULL)
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
CREATE VIEW IF NOT EXISTS units_hierarchy_stats AS SELECT uh.id
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
CREATE VIEW IF NOT EXISTS units_types AS SELECT u.id,
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

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
