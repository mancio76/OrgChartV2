--
-- File generated with SQLiteStudio v3.4.17 on mar lug 22 14:52:17 2025
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
    is_ad_interim BOOLEAN NOT NULL DEFAULT FALSE,
    is_unit_boss BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    flags TEXT,
    valid_from DATE,
    valid_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES units(id),
    FOREIGN KEY (job_title_id) REFERENCES job_titles(id),
    
    -- Constraint per garantire che ci sia solo un record current per person+unit+job_title
    UNIQUE(person_id, unit_id, job_title_id, is_current) -- WHERE is_current = TRUE
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

-- Table: units
CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT,
    aliases TEXT, -- JSON array degli alias
    type TEXT NOT NULL CHECK (type IN ('function', 'OrganizationalUnit')),
    parent_unit_id INTEGER,
    start_date DATE,
    end_date DATE,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_unit_id) REFERENCES units(id)
);

-- Index: idx_assignments_current
CREATE INDEX IF NOT EXISTS idx_assignments_current ON person_job_assignments(is_current) WHERE is_current = TRUE;

-- Index: idx_assignments_job_title
CREATE INDEX IF NOT EXISTS idx_assignments_job_title ON person_job_assignments(job_title_id);

-- Index: idx_assignments_person
CREATE INDEX IF NOT EXISTS idx_assignments_person ON person_job_assignments(person_id);

-- Index: idx_assignments_unit
CREATE INDEX IF NOT EXISTS idx_assignments_unit ON person_job_assignments(unit_id);

-- Index: idx_assignments_version
CREATE INDEX IF NOT EXISTS idx_assignments_version ON person_job_assignments(person_id, unit_id, job_title_id, version);

-- Index: idx_units_parent
CREATE INDEX IF NOT EXISTS idx_units_parent ON units(parent_unit_id);

-- Index: idx_units_type
CREATE INDEX IF NOT EXISTS idx_units_type ON units(type);

-- Index: unique_current_assignment
CREATE UNIQUE INDEX IF NOT EXISTS unique_current_assignment 
ON person_job_assignments (person_id, unit_id, job_title_id) 
WHERE is_current = 1;

-- View: assignment_history
CREATE VIEW IF NOT EXISTS assignment_history AS
SELECT p.id AS person_id,
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
CREATE VIEW IF NOT EXISTS current_assignments AS SELECT p.id AS person_id,
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

-- View: units_hierarchy
CREATE VIEW IF NOT EXISTS units_hierarchy AS WITH RECURSIVE unit_tree AS (-- Nodi radice (parent_unit_id = -1 o NULL)
    SELECT id,
           name,
           short_name,
           type,
           parent_unit_id,
           0 AS level,
           CAST (id AS TEXT) AS path,
           name AS full_path
      FROM units
     WHERE parent_unit_id IS NULL OR
           parent_unit_id = -1
    UNION ALL-- Nodi figli
    SELECT u.id,
           u.name,
           u.short_name,
           u.type,
           u.parent_unit_id,
           ut.level + 1,
           ut.path || '/' || CAST (u.id AS TEXT),
           ut.full_path || ' > ' || u.name
      FROM units u
           JOIN
           unit_tree ut ON u.parent_unit_id = ut.id
)
SELECT *
  FROM unit_tree
 ORDER BY path;

-- Trigger: manage_assignment_versioning
CREATE TRIGGER IF NOT EXISTS manage_assignment_versioning
                      BEFORE INSERT
                          ON person_job_assignments
                        WHEN NEW.is_current = 1
BEGIN-- Imposta is_current = 0 per tutti i record precedenti della stessa combinazione
    UPDATE person_job_assignments
       SET is_current = 0,
           valid_to = COALESCE(NEW.valid_from, DATE('now') ),
           datetime_updated = CURRENT_TIMESTAMP
     WHERE person_id = NEW.person_id AND
           unit_id = NEW.unit_id AND
           job_title_id = NEW.job_title_id AND
           is_current = 1;-- Calcola la prossima versione
    UPDATE person_job_assignments
       SET version = (
               SELECT COALESCE(MAX(version), 0) + 1
                 FROM person_job_assignments
                WHERE person_id = NEW.person_id AND
                      unit_id = NEW.unit_id AND
                      job_title_id = NEW.job_title_id
           )
     WHERE ROWID = NEW.ROWID;
END;

-- Trigger: update_assignable_units_timestamp
CREATE TRIGGER IF NOT EXISTS update_assignable_units_timestamp AFTER UPDATE ON job_title_assignable_units WHEN NEw.datetime_updated <> OLD.datetime_updated BEGIN UPDATE job_title_assignable_units SET datetime_updated = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

-- Trigger: update_assignments_timestamp
CREATE TRIGGER IF NOT EXISTS update_assignments_timestamp AFTER UPDATE ON person_job_assignments WHEN NEw.datetime_updated <> OLD.datetime_updated BEGIN UPDATE person_job_assignments SET datetime_updated = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

-- Trigger: update_job_titles_timestamp
CREATE TRIGGER IF NOT EXISTS update_job_titles_timestamp AFTER UPDATE ON job_titles WHEN NEw.datetime_updated <> OLD.datetime_updated BEGIN UPDATE job_titles SET datetime_updated = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

-- Trigger: update_persons_timestamp
CREATE TRIGGER IF NOT EXISTS update_persons_timestamp AFTER UPDATE ON persons WHEN NEw.datetime_updated <> OLD.datetime_updated BEGIN UPDATE persons SET datetime_updated = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

-- Trigger: update_units_timestamp
CREATE TRIGGER IF NOT EXISTS update_units_timestamp AFTER UPDATE ON units WHEN NEw.datetime_updated <> OLD.datetime_updated BEGIN UPDATE units SET datetime_updated = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
