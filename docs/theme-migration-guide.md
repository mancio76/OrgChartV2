# Guida Migrazione - Sistema Temi Unità Organizzative

## Panoramica

Questa guida documenta il processo completo di migrazione dal sistema hardcoded al nuovo Sistema di Gestione Temi. Include procedure di migrazione, validazione e rollback per garantire una transizione sicura e controllata.

## Prerequisiti

### Requisiti Sistema

- **Database**: SQLite con supporto foreign keys abilitato
- **Python**: Versione 3.8 o superiore
- **Dipendenze**: FastAPI, Jinja2, SQLite3
- **Backup**: Backup completo del database esistente

### Preparazione Pre-Migrazione

1. **Backup Database:**
   ```bash
   # Backup completo database
   cp database/orgchart.db database/orgchart.db.backup_$(date +%Y%m%d_%H%M%S)
   
   # Verifica backup
   sqlite3 database/orgchart.db.backup_* ".tables"
   ```

2. **Verifica Integrità Database:**
   ```bash
   # Controllo integrità
   sqlite3 database/orgchart.db "PRAGMA integrity_check;"
   
   # Verifica foreign keys
   sqlite3 database/orgchart.db "PRAGMA foreign_key_check;"
   ```

3. **Documentazione Stato Attuale:**
   ```sql
   -- Documenta unit types esistenti
   SELECT id, name, description FROM unit_types ORDER BY id;
   
   -- Conta unità per tipo
   SELECT ut.name, COUNT(u.id) as unit_count 
   FROM unit_types ut 
   LEFT JOIN units u ON ut.id = u.unit_type_id 
   GROUP BY ut.id;
   ```

## Processo di Migrazione

### Fase 1: Creazione Struttura Database

#### 1.1 Creazione Tabella Temi

```sql
-- Script: database/schema/migration_002_unit_type_themes.sql
CREATE TABLE unit_type_themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    
    -- Proprietà Visive
    icon_class TEXT NOT NULL DEFAULT 'diagram-2',
    emoji_fallback TEXT NOT NULL DEFAULT '🏛️',
    
    -- Schema Colori
    primary_color TEXT NOT NULL DEFAULT '#0dcaf0',
    secondary_color TEXT NOT NULL DEFAULT '#f0fdff',
    text_color TEXT NOT NULL DEFAULT '#0dcaf0',
    border_color TEXT,
    
    -- Proprietà Layout
    border_width INTEGER NOT NULL DEFAULT 2,
    border_style TEXT NOT NULL DEFAULT 'solid',
    background_gradient TEXT,
    
    -- Generazione CSS
    css_class_suffix TEXT NOT NULL,
    hover_shadow_color TEXT,
    hover_shadow_intensity REAL DEFAULT 0.25,
    
    -- Proprietà Display
    display_label TEXT NOT NULL,
    display_label_plural TEXT,
    
    -- Accessibilità
    high_contrast_mode BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 1.2 Creazione Indici

```sql
-- Indici per performance
CREATE INDEX idx_unit_type_themes_active ON unit_type_themes(is_active);
CREATE INDEX idx_unit_type_themes_default ON unit_type_themes(is_default);
CREATE INDEX idx_unit_type_themes_name ON unit_type_themes(name);
```

#### 1.3 Modifica Tabella Unit Types

```sql
-- Aggiunta colonna theme_id
ALTER TABLE unit_types ADD COLUMN theme_id INTEGER REFERENCES unit_type_themes(id);

-- Indice per foreign key
CREATE INDEX idx_unit_types_theme_id ON unit_types(theme_id);
```

### Fase 2: Inserimento Dati Predefiniti

#### 2.1 Creazione Temi Predefiniti

```sql
-- Tema per Funzioni (ex unit_type_id = 1)
INSERT INTO unit_type_themes (
    name, description, icon_class, emoji_fallback,
    primary_color, secondary_color, text_color, border_color,
    border_width, border_style, css_class_suffix,
    hover_shadow_color, hover_shadow_intensity,
    display_label, display_label_plural,
    high_contrast_mode, is_default, is_active, created_by
) VALUES (
    'Tema Funzioni',
    'Tema per unità organizzative di tipo funzionale con stile distintivo',
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
    FALSE,
    FALSE,
    TRUE,
    'migration_system'
);

-- Tema per Unità Organizzative (ex unit_type_id = 2)
INSERT INTO unit_type_themes (
    name, description, icon_class, emoji_fallback,
    primary_color, secondary_color, text_color, border_color,
    border_width, border_style, css_class_suffix,
    hover_shadow_color, hover_shadow_intensity,
    display_label, display_label_plural,
    high_contrast_mode, is_default, is_active, created_by
) VALUES (
    'Tema Organizzativo',
    'Tema standard per unità organizzative generiche',
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
    TRUE,
    'migration_system'
);
```

#### 2.2 Assegnazione Temi a Unit Types Esistenti

```sql
-- Assegna tema funzioni a unit_type_id = 1
UPDATE unit_types 
SET theme_id = (SELECT id FROM unit_type_themes WHERE name = 'Tema Funzioni')
WHERE id = 1;

-- Assegna tema organizzativo a unit_type_id = 2
UPDATE unit_types 
SET theme_id = (SELECT id FROM unit_type_themes WHERE name = 'Tema Organizzativo')
WHERE id = 2;

-- Assegna tema predefinito a eventuali altri unit types
UPDATE unit_types 
SET theme_id = (SELECT id FROM unit_type_themes WHERE is_default = TRUE)
WHERE theme_id IS NULL;
```

### Fase 3: Esecuzione Script Migrazione

#### 3.1 Script Python di Migrazione

```python
#!/usr/bin/env python3
"""
Script di migrazione per Sistema Temi Unit Types
File: scripts/migrate_002_unit_type_themes.py
"""

import sqlite3
import sys
import os
from datetime import datetime

def execute_migration():
    """Esegue la migrazione completa al sistema temi."""
    
    print("=== MIGRAZIONE SISTEMA TEMI ===")
    print(f"Inizio migrazione: {datetime.now()}")
    
    # Connessione database
    db_path = "database/orgchart.db"
    if not os.path.exists(db_path):
        print(f"ERRORE: Database non trovato: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Fase 1: Creazione struttura
        print("\n1. Creazione struttura database...")
        create_theme_table(conn)
        create_indices(conn)
        add_theme_id_column(conn)
        
        # Fase 2: Inserimento dati
        print("\n2. Inserimento temi predefiniti...")
        insert_default_themes(conn)
        assign_themes_to_unit_types(conn)
        
        # Fase 3: Validazione
        print("\n3. Validazione migrazione...")
        validate_migration(conn)
        
        conn.commit()
        print("\n✓ MIGRAZIONE COMPLETATA CON SUCCESSO")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ ERRORE DURANTE MIGRAZIONE: {e}")
        print("Rollback eseguito. Database ripristinato allo stato precedente.")
        sys.exit(1)
    
    finally:
        conn.close()

def create_theme_table(conn):
    """Crea tabella unit_type_themes."""
    
    # Verifica se tabella esiste già
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='unit_type_themes'
    """)
    
    if cursor.fetchone():
        print("   - Tabella unit_type_themes già esistente")
        return
    
    # Leggi e esegui schema
    schema_path = "database/schema/migration_002_unit_type_themes.sql"
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    conn.executescript(schema_sql)
    print("   - Tabella unit_type_themes creata")

def create_indices(conn):
    """Crea indici per performance."""
    
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_unit_type_themes_active ON unit_type_themes(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_unit_type_themes_default ON unit_type_themes(is_default)",
        "CREATE INDEX IF NOT EXISTS idx_unit_type_themes_name ON unit_type_themes(name)"
    ]
    
    for index_sql in indices:
        conn.execute(index_sql)
    
    print("   - Indici creati")

def add_theme_id_column(conn):
    """Aggiunge colonna theme_id a unit_types."""
    
    # Verifica se colonna esiste già
    cursor = conn.execute("PRAGMA table_info(unit_types)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'theme_id' in columns:
        print("   - Colonna theme_id già esistente")
        return
    
    conn.execute("ALTER TABLE unit_types ADD COLUMN theme_id INTEGER REFERENCES unit_type_themes(id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_unit_types_theme_id ON unit_types(theme_id)")
    
    print("   - Colonna theme_id aggiunta a unit_types")

def insert_default_themes(conn):
    """Inserisce temi predefiniti."""
    
    # Verifica se temi esistono già
    cursor = conn.execute("SELECT COUNT(*) FROM unit_type_themes")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print("   - Temi predefiniti già esistenti")
        return
    
    themes = [
        {
            'name': 'Tema Funzioni',
            'description': 'Tema per unità organizzative di tipo funzionale',
            'icon_class': 'building',
            'emoji_fallback': '🏢',
            'primary_color': '#0d6efd',
            'secondary_color': '#f8f9ff',
            'text_color': '#0d6efd',
            'border_width': 4,
            'css_class_suffix': 'function',
            'display_label': 'Funzione',
            'display_label_plural': 'Funzioni',
            'is_default': False
        },
        {
            'name': 'Tema Organizzativo',
            'description': 'Tema standard per unità organizzative',
            'icon_class': 'diagram-2',
            'emoji_fallback': '🏛️',
            'primary_color': '#0dcaf0',
            'secondary_color': '#f0fdff',
            'text_color': '#0dcaf0',
            'border_width': 2,
            'css_class_suffix': 'organizational',
            'display_label': 'Unità Organizzativa',
            'display_label_plural': 'Unità Organizzative',
            'is_default': True
        }
    ]
    
    for theme in themes:
        conn.execute("""
            INSERT INTO unit_type_themes (
                name, description, icon_class, emoji_fallback,
                primary_color, secondary_color, text_color,
                border_width, css_class_suffix,
                display_label, display_label_plural,
                is_default, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            theme['name'], theme['description'], theme['icon_class'], theme['emoji_fallback'],
            theme['primary_color'], theme['secondary_color'], theme['text_color'],
            theme['border_width'], theme['css_class_suffix'],
            theme['display_label'], theme['display_label_plural'],
            theme['is_default'], 'migration_system'
        ))
    
    print(f"   - {len(themes)} temi predefiniti inseriti")

def assign_themes_to_unit_types(conn):
    """Assegna temi ai unit types esistenti."""
    
    # Mappa unit_type_id -> tema
    assignments = [
        (1, 'Tema Funzioni'),
        (2, 'Tema Organizzativo')
    ]
    
    for unit_type_id, theme_name in assignments:
        # Verifica che unit_type esista
        cursor = conn.execute("SELECT id FROM unit_types WHERE id = ?", (unit_type_id,))
        if not cursor.fetchone():
            print(f"   - Unit type {unit_type_id} non trovato, saltato")
            continue
        
        # Assegna tema
        conn.execute("""
            UPDATE unit_types 
            SET theme_id = (SELECT id FROM unit_type_themes WHERE name = ?)
            WHERE id = ?
        """, (theme_name, unit_type_id))
        
        print(f"   - Unit type {unit_type_id} assegnato a '{theme_name}'")
    
    # Assegna tema predefinito a unit types senza tema
    conn.execute("""
        UPDATE unit_types 
        SET theme_id = (SELECT id FROM unit_type_themes WHERE is_default = TRUE)
        WHERE theme_id IS NULL
    """)
    
    cursor = conn.execute("SELECT COUNT(*) FROM unit_types WHERE theme_id IS NULL")
    orphaned_count = cursor.fetchone()[0]
    
    if orphaned_count == 0:
        print("   - Tutti i unit types hanno un tema assegnato")
    else:
        print(f"   - ATTENZIONE: {orphaned_count} unit types senza tema")

def validate_migration(conn):
    """Valida il risultato della migrazione."""
    
    validations = []
    
    # 1. Verifica esistenza tabella temi
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='unit_type_themes'
    """)
    validations.append(("Tabella temi", cursor.fetchone() is not None))
    
    # 2. Verifica tema predefinito
    cursor = conn.execute("SELECT COUNT(*) FROM unit_type_themes WHERE is_default = TRUE")
    default_count = cursor.fetchone()[0]
    validations.append(("Tema predefinito", default_count == 1))
    
    # 3. Verifica colonna theme_id
    cursor = conn.execute("PRAGMA table_info(unit_types)")
    columns = [row[1] for row in cursor.fetchall()]
    validations.append(("Colonna theme_id", 'theme_id' in columns))
    
    # 4. Verifica assegnazioni temi
    cursor = conn.execute("SELECT COUNT(*) FROM unit_types WHERE theme_id IS NULL")
    orphaned_count = cursor.fetchone()[0]
    validations.append(("Unit types senza tema", orphaned_count == 0))
    
    # 5. Verifica integrità foreign keys
    cursor = conn.execute("PRAGMA foreign_key_check")
    fk_errors = cursor.fetchall()
    validations.append(("Integrità foreign keys", len(fk_errors) == 0))
    
    # Stampa risultati
    print("\n   Risultati validazione:")
    all_passed = True
    for check_name, passed in validations:
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    if not all_passed:
        raise Exception("Validazione migrazione fallita")
    
    print("   - Validazione completata con successo")

if __name__ == "__main__":
    execute_migration()
```

#### 3.2 Esecuzione Migrazione

```bash
# Esegui migrazione
python scripts/migrate_002_unit_type_themes.py

# Verifica risultato
python scripts/validate_migration_002.py
```

### Fase 4: Aggiornamento Codice Applicazione

#### 4.1 Modelli

```python
# app/models/unit_type_theme.py - Già implementato
# app/models/unit_type.py - Aggiornato con theme relationship
```

#### 4.2 Servizi

```python
# app/services/unit_type_theme.py - Nuovo servizio
# app/services/unit_type.py - Aggiornato con theme support
```

#### 4.3 Template

```python
# app/utils/template_helpers.py - Helper per temi
# templates/orgchart/*.html - Refactoring da hardcoded a theme-driven
```

#### 4.4 Route

```python
# app/routes/themes.py - Nuove route per gestione temi
# app/routes/orgchart.py - CSS dinamico
```

### Fase 5: Testing Post-Migrazione

#### 5.1 Test Funzionalità Base

```bash
# Test modelli
python -m pytest tests/test_unit_type_theme_comprehensive.py -v

# Test servizi
python -m pytest tests/test_services.py::TestUnitTypeThemeService -v

# Test template
python -m pytest tests/test_template_helpers.py -v

# Test integrazione
python -m pytest tests/test_integration.py -v
```

#### 5.2 Test Visuale

1. **Accedi all'applicazione**
2. **Verifica organigramma**: Controlla che le unità mostrino i temi corretti
3. **Testa gestione temi**: Crea, modifica, elimina temi
4. **Verifica CSS dinamico**: Accedi a `/css/themes.css`

#### 5.3 Test Performance

```python
# Script test performance
import time
from app.services.unit_type_theme import UnitTypeThemeService

def test_css_generation_performance():
    service = UnitTypeThemeService()
    
    start = time.time()
    css = service.generate_dynamic_css()
    duration = time.time() - start
    
    print(f"CSS generation: {duration:.3f}s ({len(css)} chars)")
    assert duration < 0.1, "CSS generation too slow"

def test_theme_query_performance():
    service = UnitTypeThemeService()
    
    start = time.time()
    themes = service.get_themes_with_usage_stats()
    duration = time.time() - start
    
    print(f"Theme query: {duration:.3f}s ({len(themes)} themes)")
    assert duration < 0.05, "Theme query too slow"
```

## Procedure di Rollback

### Rollback Completo

#### Script di Rollback

```python
#!/usr/bin/env python3
"""
Script di rollback per Sistema Temi
File: scripts/rollback_002_unit_type_themes.py
"""

import sqlite3
import sys
import os
from datetime import datetime

def execute_rollback():
    """Esegue rollback completo del sistema temi."""
    
    print("=== ROLLBACK SISTEMA TEMI ===")
    print(f"Inizio rollback: {datetime.now()}")
    
    # Conferma utente
    confirm = input("ATTENZIONE: Questo eliminerà tutti i dati dei temi. Continuare? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Rollback annullato.")
        sys.exit(0)
    
    db_path = "database/orgchart.db"
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Backup dati temi (opzionale)
        print("\n1. Backup dati temi...")
        backup_theme_data(conn)
        
        # Rimuovi colonna theme_id
        print("\n2. Rimozione colonna theme_id...")
        remove_theme_id_column(conn)
        
        # Elimina tabella temi
        print("\n3. Eliminazione tabella temi...")
        drop_theme_table(conn)
        
        # Validazione rollback
        print("\n4. Validazione rollback...")
        validate_rollback(conn)
        
        conn.commit()
        print("\n✓ ROLLBACK COMPLETATO CON SUCCESSO")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ ERRORE DURANTE ROLLBACK: {e}")
        sys.exit(1)
    
    finally:
        conn.close()

def backup_theme_data(conn):
    """Backup dati temi prima del rollback."""
    
    backup_file = f"theme_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        # Backup tabella temi
        cursor = conn.execute("SELECT * FROM unit_type_themes")
        columns = [desc[0] for desc in cursor.description]
        
        f.write("-- Backup unit_type_themes\n")
        f.write("CREATE TABLE unit_type_themes_backup (\n")
        f.write("    -- Schema originale qui\n")
        f.write(");\n\n")
        
        for row in cursor.fetchall():
            values = ', '.join([f"'{v}'" if v is not None else 'NULL' for v in row])
            f.write(f"INSERT INTO unit_type_themes_backup VALUES ({values});\n")
        
        # Backup assegnazioni
        cursor = conn.execute("SELECT id, theme_id FROM unit_types WHERE theme_id IS NOT NULL")
        f.write("\n-- Backup assegnazioni temi\n")
        for unit_type_id, theme_id in cursor.fetchall():
            f.write(f"-- Unit type {unit_type_id} -> Theme {theme_id}\n")
    
    print(f"   - Backup salvato in: {backup_file}")

def remove_theme_id_column(conn):
    """Rimuove colonna theme_id da unit_types."""
    
    # SQLite non supporta DROP COLUMN direttamente
    # Dobbiamo ricreare la tabella
    
    # 1. Crea tabella temporanea senza theme_id
    conn.execute("""
        CREATE TABLE unit_types_temp AS 
        SELECT id, name, description, parent_id, is_active, 
               datetime_created, datetime_updated
        FROM unit_types
    """)
    
    # 2. Elimina tabella originale
    conn.execute("DROP TABLE unit_types")
    
    # 3. Rinomina tabella temporanea
    conn.execute("ALTER TABLE unit_types_temp RENAME TO unit_types")
    
    # 4. Ricrea indici
    conn.execute("CREATE INDEX IF NOT EXISTS idx_unit_types_parent_id ON unit_types(parent_id)")
    
    print("   - Colonna theme_id rimossa da unit_types")

def drop_theme_table(conn):
    """Elimina tabella unit_type_themes."""
    
    # Rimuovi indici
    indices = [
        "idx_unit_type_themes_active",
        "idx_unit_type_themes_default", 
        "idx_unit_type_themes_name"
    ]
    
    for index in indices:
        try:
            conn.execute(f"DROP INDEX IF EXISTS {index}")
        except:
            pass
    
    # Elimina tabella
    conn.execute("DROP TABLE IF EXISTS unit_type_themes")
    
    print("   - Tabella unit_type_themes eliminata")

def validate_rollback(conn):
    """Valida il rollback."""
    
    validations = []
    
    # 1. Verifica tabella temi eliminata
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='unit_type_themes'
    """)
    validations.append(("Tabella temi eliminata", cursor.fetchone() is None))
    
    # 2. Verifica colonna theme_id rimossa
    cursor = conn.execute("PRAGMA table_info(unit_types)")
    columns = [row[1] for row in cursor.fetchall()]
    validations.append(("Colonna theme_id rimossa", 'theme_id' not in columns))
    
    # 3. Verifica integrità unit_types
    cursor = conn.execute("SELECT COUNT(*) FROM unit_types")
    unit_count = cursor.fetchone()[0]
    validations.append(("Unit types preservati", unit_count > 0))
    
    # Stampa risultati
    print("\n   Risultati validazione:")
    all_passed = True
    for check_name, passed in validations:
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    if not all_passed:
        raise Exception("Validazione rollback fallita")

if __name__ == "__main__":
    execute_rollback()
```

### Rollback Parziale

Per situazioni dove si vuole mantenere la struttura ma disabilitare le funzionalità:

```python
def partial_rollback():
    """Rollback parziale - mantiene dati ma disabilita funzionalità."""
    
    conn = sqlite3.connect("database/orgchart.db")
    
    try:
        # Disabilita tutti i temi
        conn.execute("UPDATE unit_type_themes SET is_active = FALSE")
        
        # Rimuovi assegnazioni temi (mantieni colonna)
        conn.execute("UPDATE unit_types SET theme_id = NULL")
        
        # Marca sistema come in modalità compatibilità
        conn.execute("""
            INSERT OR REPLACE INTO system_settings (key, value) 
            VALUES ('theme_system_enabled', 'false')
        """)
        
        conn.commit()
        print("Rollback parziale completato - sistema in modalità compatibilità")
        
    finally:
        conn.close()
```

## Validazione e Monitoraggio

### Script di Validazione Continua

```python
#!/usr/bin/env python3
"""
Script di validazione continua per sistema temi
File: scripts/validate_theme_system.py
"""

def continuous_validation():
    """Validazione continua del sistema temi."""
    
    checks = [
        check_theme_integrity,
        check_unit_type_assignments,
        check_css_generation,
        check_performance_metrics,
        check_data_consistency
    ]
    
    results = {}
    
    for check in checks:
        try:
            result = check()
            results[check.__name__] = {
                'status': 'pass',
                'details': result
            }
        except Exception as e:
            results[check.__name__] = {
                'status': 'fail',
                'error': str(e)
            }
    
    return results

def check_theme_integrity():
    """Verifica integrità dati temi."""
    conn = sqlite3.connect("database/orgchart.db")
    
    # Verifica tema predefinito unico
    cursor = conn.execute("SELECT COUNT(*) FROM unit_type_themes WHERE is_default = TRUE")
    default_count = cursor.fetchone()[0]
    
    if default_count != 1:
        raise Exception(f"Expected 1 default theme, found {default_count}")
    
    # Verifica colori validi
    cursor = conn.execute("""
        SELECT id, name, primary_color, secondary_color, text_color 
        FROM unit_type_themes WHERE is_active = TRUE
    """)
    
    import re
    color_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    
    for theme_id, name, primary, secondary, text in cursor.fetchall():
        for color_name, color_value in [('primary', primary), ('secondary', secondary), ('text', text)]:
            if not re.match(color_pattern, color_value):
                raise Exception(f"Invalid {color_name} color in theme '{name}': {color_value}")
    
    conn.close()
    return "All themes have valid data"

def check_unit_type_assignments():
    """Verifica assegnazioni temi a unit types."""
    conn = sqlite3.connect("database/orgchart.db")
    
    # Verifica unit types orfani
    cursor = conn.execute("""
        SELECT COUNT(*) FROM unit_types 
        WHERE theme_id IS NULL OR theme_id NOT IN (
            SELECT id FROM unit_type_themes WHERE is_active = TRUE
        )
    """)
    
    orphaned_count = cursor.fetchone()[0]
    
    if orphaned_count > 0:
        raise Exception(f"Found {orphaned_count} unit types without valid theme")
    
    conn.close()
    return "All unit types have valid theme assignments"
```

### Monitoraggio Performance

```python
def monitor_theme_performance():
    """Monitora performance del sistema temi."""
    
    import time
    from app.services.unit_type_theme import UnitTypeThemeService
    
    service = UnitTypeThemeService()
    metrics = {}
    
    # Test generazione CSS
    start = time.time()
    css = service.generate_dynamic_css()
    metrics['css_generation_time'] = time.time() - start
    metrics['css_size'] = len(css)
    
    # Test query temi
    start = time.time()
    themes = service.get_themes_with_usage_stats()
    metrics['theme_query_time'] = time.time() - start
    metrics['theme_count'] = len(themes)
    
    # Soglie performance
    if metrics['css_generation_time'] > 0.1:
        raise Exception(f"CSS generation too slow: {metrics['css_generation_time']:.3f}s")
    
    if metrics['theme_query_time'] > 0.05:
        raise Exception(f"Theme query too slow: {metrics['theme_query_time']:.3f}s")
    
    return metrics
```

## Checklist Migrazione

### Pre-Migrazione

- [ ] Backup database completo
- [ ] Verifica integrità database esistente
- [ ] Documentazione stato attuale
- [ ] Test ambiente di sviluppo
- [ ] Preparazione script rollback

### Durante Migrazione

- [ ] Esecuzione script migrazione
- [ ] Verifica creazione tabelle
- [ ] Controllo inserimento dati predefiniti
- [ ] Validazione assegnazioni temi
- [ ] Test funzionalità base

### Post-Migrazione

- [ ] Test completo applicazione
- [ ] Verifica performance
- [ ] Controllo CSS dinamico
- [ ] Test interfaccia gestione temi
- [ ] Validazione accessibilità
- [ ] Documentazione aggiornata
- [ ] Training utenti

### Rollback (se necessario)

- [ ] Backup dati temi
- [ ] Esecuzione script rollback
- [ ] Ripristino funzionalità hardcoded
- [ ] Validazione stato pre-migrazione
- [ ] Comunicazione agli utenti

## Troubleshooting Migrazione

### Problemi Comuni

1. **Errore Foreign Key Constraint**
   ```
   Soluzione: Verificare che PRAGMA foreign_keys = ON sia attivo
   ```

2. **Tema Predefinito Duplicato**
   ```sql
   -- Correzione
   UPDATE unit_type_themes SET is_default = FALSE;
   UPDATE unit_type_themes SET is_default = TRUE WHERE id = [PREFERRED_ID];
   ```

3. **Unit Types Orfani**
   ```sql
   -- Assegna tema predefinito
   UPDATE unit_types 
   SET theme_id = (SELECT id FROM unit_type_themes WHERE is_default = TRUE)
   WHERE theme_id IS NULL;
   ```

4. **CSS Non Generato**
   ```python
   # Verifica servizio
   from app.services.unit_type_theme import UnitTypeThemeService
   service = UnitTypeThemeService()
   css = service.generate_dynamic_css()
   print(len(css))  # Dovrebbe essere > 0
   ```

### Log e Debug

```python
# Configurazione logging per migrazione
import logging

migration_logger = logging.getLogger('migration')
migration_logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('migration.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
migration_logger.addHandler(handler)

# Uso durante migrazione
migration_logger.info("Starting theme system migration")
migration_logger.debug(f"Creating theme table: {table_created}")
migration_logger.error(f"Migration failed: {error_message}")
```

## Supporto e Contatti

### Escalation

1. **Problemi durante migrazione**: Contattare team sviluppo immediatamente
2. **Rollback necessario**: Seguire procedura rollback documentata
3. **Perdita dati**: Ripristinare da backup e contattare amministratore database

### Documentazione Aggiuntiva

- [Guida Utente Sistema Temi](theme-management-user-guide.md)
- [Guida Sviluppatore](theme-system-developer-guide.md)
- [Troubleshooting](theme-troubleshooting-guide.md)

---

*Questa guida migrazione è parte della documentazione completa del Sistema Temi. Mantenere aggiornata con eventuali modifiche al processo.*