--
-- File generated with SQLiteStudio v3.4.17 on gio lug 24 10:49:46 2025
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
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (1, 1, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (2, 2, 2, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (3, 3, 0, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (4, 3, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (5, 4, 3, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (6, 4, 4, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (7, 4, 5, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (8, 5, 6, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (9, 6, 5, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (10, 7, 18, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (11, 8, 18, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (12, 9, 18, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (13, 10, 16, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (14, 11, 18, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (15, 12, 9, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (16, 13, 19, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (17, 14, 20, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (18, 15, 21, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (19, 16, 8, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (20, 17, 8, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_title_assignable_units (id, job_title_id, unit_id, datetime_created, datetime_updated) VALUES (21, 18, 15, '2025-07-22 10:34:00', '2025-07-22 10:34:00');

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
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (1, 'Presidente', 'Pres', '[{"value": "President", "lang": "en-US"}, {"value": "Presidente CdA", "lang": "it-IT"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (2, 'Amministratore Delegato', 'AD', '[{"value": "Chief Executive Officer", "lang": "en-US"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (3, 'Socio', NULL, '[{"value": "Associate", "lang": "en-US"}, {"value": "Partner", "lang": "en-US"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (4, 'Membro', NULL, '[{"value": "Member", "lang": "en-US"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (5, 'Data Protection Officer', 'DPO', '[{"value": "Responsabile Protezione Dati", "lang": "it-IT"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (6, 'Internal Auditor', 'IA', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (7, 'Chief Information Officer', 'CIO', '[{"value": "Responsabile delle Informazioni", "lang": "it-IT"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (8, 'Chief Technology Officer', 'CTO', '[{"value": "Responsabile delle Tecnologie", "lang": "it-IT"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (9, 'Chief Information & Technology Officer', 'CIO/CTO', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (10, 'Chief Financial Officer', 'CFO', '[{"value": "Responsabile delle Finanze", "lang": "it-IT"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (11, 'Chief Information Security Officer', 'CISO', '[{"value": "Responsabile Sicurezza delle Informazioni", "lang": "it-IT"}]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (12, 'Chief Commercial Officer', 'CCO', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (13, 'Head Of Planning & Analysis', 'HEAD', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (14, 'Head Of Direct Sales', 'HEAD', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (15, 'Head Of Marketing', 'HEAD', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (16, 'Head Of Corporate Communication & Media Relations', 'HEAD', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (17, 'Media Relations Manager', '', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO job_titles (id, name, short_name, aliases, start_date, end_date, datetime_created, datetime_updated) VALUES (18, 'Chief Product Officer', 'CPO', '[]', '', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');

-- Table: person_job_assignments
CREATE TABLE IF NOT EXISTS person_job_assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, person_id INTEGER NOT NULL, unit_id INTEGER NOT NULL, job_title_id INTEGER NOT NULL, version INTEGER NOT NULL DEFAULT 1, percentage REAL NOT NULL DEFAULT 1.0 CHECK (percentage > 0 AND percentage <= 1), is_ad_interim BOOLEAN NOT NULL DEFAULT "FALSE", is_unit_boss BOOLEAN NOT NULL DEFAULT (0), notes TEXT, flags TEXT, valid_from DATE, valid_to DATE, is_current BOOLEAN NOT NULL DEFAULT "TRUE", datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (person_id) REFERENCES persons (id) ON DELETE CASCADE, FOREIGN KEY (unit_id) REFERENCES units (id), FOREIGN KEY (job_title_id) REFERENCES job_titles (id), UNIQUE (person_id, unit_id, job_title_id, is_current));
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (1, 1, 1, 1, 1, 1.0, 0, 0, '', '', NULL, '2025-07-24', 0, '2025-07-22 10:34:00', '2025-07-24 06:57:03');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (2, 2, 2, 1, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (3, 2, 1, 2, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (4, 3, 1, 2, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (5, 4, 3, 3, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (6, 5, 4, 3, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (7, 6, 6, 5, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (8, 7, 5, 6, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (9, 8, 8, 15, 1, 1.0, 1, 0, 'This in an interim assignment', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (10, 8, 21, 15, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (11, 9, 8, 17, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (12, 10, 9, 12, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (13, 10, 19, 13, 1, 1.0, 0, 0, '', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (14, 10, 20, 14, 1, 1.0, 1, 0, 'This is an interim assignement', '', NULL, NULL, 1, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (15, 1, 1, 1, 1, 1.0, 0, 0, 'Test assignment - version 1', NULL, '2025-07-24', NULL, 1, '2025-07-24 06:57:03', '2025-07-24 06:57:03');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (16, 2, 2, 2, 1, 1.0, 0, 0, 'Version 1', NULL, '2024-01-01', '2024-06-01', 0, '2025-07-24 06:57:03', '2025-07-24 06:57:03');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (17, 2, 2, 2, 2, 0.8, 0, 0, 'Version 2', NULL, '2024-06-01', NULL, 1, '2025-07-24 06:57:03', '2025-07-24 06:57:03');
INSERT INTO person_job_assignments (id, person_id, unit_id, job_title_id, version, percentage, is_ad_interim, is_unit_boss, notes, flags, valid_from, valid_to, is_current, datetime_created, datetime_updated) VALUES (18, 1, 2, 3, 1, 1.0, 0, 0, 'Test assignment - version 1', NULL, '2025-07-24', NULL, 1, '2025-07-24 07:02:08', '2025-07-24 07:02:08');

-- Table: persons
CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    email TEXT,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (1, 'Gianluca Calvosa', 'CALVOSA G.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (2, 'Raffaele Nardone', 'NARDONE R.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (3, 'Francesco Becchelli', 'BECCHELLI F.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (4, 'F. Orioli', 'ORIOLI F.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (5, 'C. Padovani', 'PADOVANI C.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (6, 'FINDATA Srl', 'FINDATA', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (7, 'Benedetto Verdino', 'VERDINO B.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (8, 'Martina Casani', 'CASANI M.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (9, 'Andrea Zanini', 'ZANINI A.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO persons (id, name, short_name, email, datetime_created, datetime_updated) VALUES (10, 'Giovanni Uboldi', 'UBOLDI G.', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');

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
INSERT INTO unit_types (id, name, short_name, level, aliases, datetime_created, datetime_updated) VALUES (1, 'Function', 'FN', 1, NULL, '2025-07-24 07:37:07', '2025-07-24 07:37:07');
INSERT INTO unit_types (id, name, short_name, level, aliases, datetime_created, datetime_updated) VALUES (2, 'OrganizationalUnit', 'OU', 2, NULL, '2025-07-24 07:37:33', '2025-07-24 07:37:33');

-- Table: units
CREATE TABLE IF NOT EXISTS units (id INTEGER PRIMARY KEY, name TEXT NOT NULL, short_name TEXT, aliases TEXT, unit_type_id INTEGER DEFAULT (1) NOT NULL, parent_unit_id INTEGER, start_date DATE, end_date DATE, datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (parent_unit_id) REFERENCES units (id));
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (0, 'Assemblea dei Soci', 'AdS', '[]', 1, NULL, '2013-01-01', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (1, 'Consiglio di Amministrazione', 'CdA', '[]', 1, 0, '2013-01-01', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (2, 'Amministratore Delegato', 'AD', '[]', 1, 1, '2013-01-01', '', '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (3, 'Sindaco', 'SINDA', '[]', 1, 0, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (4, 'Organo di Vigilanza', 'ODV', '[]', 1, 1, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (5, 'Internal Audit', 'IAUDIT', '[]', 1, 1, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (6, 'Data Protection Office', 'DPO', '[]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (7, 'Segreteria di Direzione', 'SEGDIR', '[]', 1, 1, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (8, 'Corporate Communication & Media Relations', 'CORPCOM', '[]', 1, 1, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (9, 'Commercial', 'COMMER', '[]', 1, 1, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (10, 'Segreteria Societaria', 'SEGSOC', '[]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (11, 'Operations', 'OPERAS', '[]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (12, 'Arrangement', 'ARRGMT', '[]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (13, 'Compliance', 'CMPLC', '[]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (14, 'Evaluation', 'EVAL', '[]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (15, 'Product Design & Delivery', 'PROD. D&D', '[]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (16, 'Amministrazione, Finanza & Controllo', 'AFC', '[{"value":"AFC","lang":"it-IT"}]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (17, 'Human Resources', 'HR', '[{"value":"People","lang":"it-IT"},{"value":"Risorse Umane","lang":"it-IT"},{"value":"People","lang":"en-US"}]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (18, 'IT & Security', 'IT&S', '[{"value":"ICT","lang":"it-IT"},{"value":"Information & Communication Technology","lang":"it-IT"}]', 1, 2, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (19, 'Planning & Analysis', NULL, '[]', 2, 9, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (20, 'Direct Sales', NULL, '[]', 2, 9, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');
INSERT INTO units (id, name, short_name, aliases, unit_type_id, parent_unit_id, start_date, end_date, datetime_created, datetime_updated) VALUES (21, 'Marketing', NULL, '[]', 2, 9, NULL, NULL, '2025-07-22 10:34:00', '2025-07-22 10:34:00');

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

-- View: unitd_hierarchy_stats
CREATE VIEW IF NOT EXISTS unitd_hierarchy_stats AS SELECT uh.id
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

-- View: units_types
CREATE VIEW IF NOT EXISTS units_types AS
SELECT u.id,
     u.name as unit_name,
     u.short_name as unit_short_name,
     ut.name as unit_type,
     ut.short_name as unit_type_short,
     u.aliases as unit_aliases,
     u.parent_unit_id,
     u.start_date,
     u.end_date
FROM units u
JOIN unit_types ut ON u.unit_type_id = ut.id;

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
