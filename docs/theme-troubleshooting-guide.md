# Guida alla Risoluzione Problemi - Sistema Temi

## Panoramica

Questa guida fornisce soluzioni per i problemi più comuni del Sistema di Gestione Temi. È organizzata per categoria di problema con soluzioni step-by-step.

## Problemi di Visualizzazione

### Tema Non Visualizzato Correttamente

**Sintomi:**
- Le unità nell'organigramma non mostrano i colori/icone del tema assegnato
- Vengono visualizzati stili predefiniti invece del tema personalizzato
- Alcune unità mostrano il tema, altre no

**Diagnosi:**

1. **Verifica assegnazione tema:**
   ```sql
   SELECT ut.name, ut.theme_id, utt.name as theme_name 
   FROM unit_types ut 
   LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id 
   WHERE ut.id = [ID_UNIT_TYPE];
   ```

2. **Controlla validità tema:**
   ```sql
   SELECT * FROM unit_type_themes WHERE id = [THEME_ID] AND is_active = 1;
   ```

3. **Verifica CSS generato:**
   - Accedi a `/css/themes.css`
   - Controlla che contenga le regole CSS per il tema

**Soluzioni:**

1. **Riassegna tema:**
   ```python
   # Via interfaccia admin o direttamente nel database
   UPDATE unit_types SET theme_id = [VALID_THEME_ID] WHERE id = [UNIT_TYPE_ID];
   ```

2. **Rigenera CSS:**
   ```python
   # Forza rigenerazione CSS
   from app.services.unit_type_theme import UnitTypeThemeService
   service = UnitTypeThemeService()
   css_content = service.generate_dynamic_css()
   ```

3. **Pulisci cache browser:**
   - Forza refresh: `Ctrl+F5` (Windows/Linux) o `Cmd+Shift+R` (Mac)
   - Svuota cache browser completamente

### Colori Non Corretti

**Sintomi:**
- I colori visualizzati non corrispondono a quelli configurati nel tema
- Alcuni elementi mantengono colori vecchi
- Colori appaiono "sbiaditi" o con opacità ridotta

**Diagnosi:**

1. **Verifica formato colori:**
   ```sql
   SELECT name, primary_color, secondary_color, text_color 
   FROM unit_type_themes 
   WHERE id = [THEME_ID];
   ```

2. **Controlla CSS custom properties:**
   - Ispeziona elemento nel browser
   - Verifica che le variabili CSS siano definite correttamente

3. **Verifica conflitti CSS:**
   - Controlla se altri CSS sovrascrivono le regole del tema
   - Usa strumenti sviluppatore per identificare regole in conflitto

**Soluzioni:**

1. **Correggi formato colori:**
   ```sql
   -- Assicurati che i colori siano in formato hex valido
   UPDATE unit_type_themes 
   SET primary_color = '#0d6efd' 
   WHERE primary_color NOT LIKE '#%';
   ```

2. **Aumenta specificità CSS:**
   ```css
   /* Aggiungi !important se necessario */
   .unit-themed.unit-function {
       border-color: var(--theme-1-primary) !important;
   }
   ```

3. **Rigenera CSS dinamico:**
   - Modifica e salva nuovamente il tema per forzare rigenerazione

### Icone Non Visualizzate

**Sintomi:**
- Icone mancanti o mostrano caratteri strani
- Icone predefinite invece di quelle del tema
- Errori console relativi a Bootstrap Icons

**Diagnosi:**

1. **Verifica classe icona:**
   ```sql
   SELECT name, icon_class FROM unit_type_themes WHERE id = [THEME_ID];
   ```

2. **Controlla Bootstrap Icons:**
   - Verifica che Bootstrap Icons sia caricato
   - Controlla che la classe icona esista in Bootstrap Icons

3. **Ispeziona HTML generato:**
   ```html
   <!-- Dovrebbe essere così -->
   <i class="bi bi-building" aria-hidden="true"></i>
   ```

**Soluzioni:**

1. **Correggi classe icona:**
   ```sql
   -- Usa solo il nome dell'icona senza prefisso 'bi-'
   UPDATE unit_type_themes 
   SET icon_class = 'building' 
   WHERE icon_class = 'bi-building';
   ```

2. **Verifica caricamento Bootstrap Icons:**
   ```html
   <!-- Assicurati che sia presente nel layout -->
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
   ```

3. **Usa emoji fallback:**
   ```sql
   -- Imposta emoji fallback appropriato
   UPDATE unit_type_themes 
   SET emoji_fallback = '🏢' 
   WHERE icon_class = 'building';
   ```

## Problemi di Performance

### CSS Lento da Caricare

**Sintomi:**
- Pagina impiega molto tempo a caricare gli stili
- Ritardo nella visualizzazione dei temi
- Timeout nella generazione CSS

**Diagnosi:**

1. **Controlla tempo generazione CSS:**
   ```python
   import time
   from app.services.unit_type_theme import UnitTypeThemeService
   
   start = time.time()
   service = UnitTypeThemeService()
   css = service.generate_dynamic_css()
   print(f"CSS generation took: {time.time() - start:.2f} seconds")
   ```

2. **Verifica numero temi attivi:**
   ```sql
   SELECT COUNT(*) FROM unit_type_themes WHERE is_active = 1;
   ```

3. **Controlla dimensione CSS generato:**
   - Accedi a `/css/themes.css`
   - Verifica dimensione del file

**Soluzioni:**

1. **Ottimizza numero temi:**
   ```sql
   -- Disattiva temi inutilizzati
   UPDATE unit_type_themes 
   SET is_active = 0 
   WHERE id NOT IN (
       SELECT DISTINCT theme_id FROM unit_types WHERE theme_id IS NOT NULL
   );
   ```

2. **Implementa cache CSS:**
   ```python
   # Verifica che la cache CSS sia attiva
   from app.utils.css_cache import css_cache
   print(f"Cache hit rate: {css_cache.get_hit_rate()}")
   ```

3. **Comprimi CSS:**
   ```python
   # Abilita compressione gzip per CSS
   # Nel server web (nginx/apache) o nell'applicazione
   ```

### Database Lento

**Sintomi:**
- Query sui temi impiegano molto tempo
- Timeout nelle operazioni CRUD sui temi
- Interfaccia admin lenta nel caricamento temi

**Diagnosi:**

1. **Analizza query lente:**
   ```sql
   EXPLAIN QUERY PLAN 
   SELECT ut.*, utt.* 
   FROM unit_types ut 
   LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id;
   ```

2. **Verifica indici:**
   ```sql
   SELECT name FROM sqlite_master 
   WHERE type = 'index' 
   AND tbl_name IN ('unit_types', 'unit_type_themes');
   ```

3. **Controlla dimensione tabelle:**
   ```sql
   SELECT COUNT(*) FROM unit_type_themes;
   SELECT COUNT(*) FROM unit_types;
   ```

**Soluzioni:**

1. **Crea indici mancanti:**
   ```sql
   CREATE INDEX IF NOT EXISTS idx_unit_types_theme_id ON unit_types(theme_id);
   CREATE INDEX IF NOT EXISTS idx_unit_type_themes_active ON unit_type_themes(is_active);
   CREATE INDEX IF NOT EXISTS idx_unit_type_themes_default ON unit_type_themes(is_default);
   ```

2. **Ottimizza query:**
   ```sql
   -- Usa query più specifiche invece di SELECT *
   SELECT ut.id, ut.name, utt.primary_color, utt.icon_class
   FROM unit_types ut 
   LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
   WHERE ut.is_active = 1;
   ```

3. **Implementa paginazione:**
   ```python
   # Per liste lunghe di temi
   def get_themes_paginated(page=1, per_page=20):
       offset = (page - 1) * per_page
       query = f"""
       SELECT * FROM unit_type_themes 
       ORDER BY name 
       LIMIT {per_page} OFFSET {offset}
       """
   ```

## Problemi di Validazione

### Errori di Validazione Colori

**Sintomi:**
- Errore "Invalid hex color format"
- Colori non salvati correttamente
- Validazione fallisce per colori validi

**Diagnosi:**

1. **Verifica formato colori:**
   ```python
   import re
   
   def validate_hex_color(color):
       pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
       return bool(re.match(pattern, color))
   
   # Test colori problematici
   colors = ['#ff0000', '#FF0000', '#f00', 'red', 'rgb(255,0,0)']
   for color in colors:
       print(f"{color}: {validate_hex_color(color)}")
   ```

2. **Controlla input utente:**
   - Verifica che l'interfaccia invii colori nel formato corretto
   - Controlla se ci sono spazi o caratteri extra

**Soluzioni:**

1. **Normalizza formato colori:**
   ```python
   def normalize_hex_color(color):
       # Rimuovi spazi
       color = color.strip()
       
       # Aggiungi # se mancante
       if not color.startswith('#'):
           color = '#' + color
       
       # Converti a minuscolo
       color = color.lower()
       
       # Espandi formato corto (#f00 -> #ff0000)
       if len(color) == 4:
           color = '#' + ''.join([c*2 for c in color[1:]])
       
       return color
   ```

2. **Migliora validazione client-side:**
   ```javascript
   function validateHexColor(color) {
       const hexPattern = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
       return hexPattern.test(color);
   }
   
   // Validazione in tempo reale
   document.getElementById('primary_color').addEventListener('input', function(e) {
       const isValid = validateHexColor(e.target.value);
       e.target.classList.toggle('is-invalid', !isValid);
   });
   ```

### Problemi di Contrasto Accessibilità

**Sintomi:**
- Avviso "Insufficient color contrast"
- Testo difficile da leggere
- Fallimento test accessibilità

**Diagnosi:**

1. **Calcola rapporto contrasto:**
   ```python
   def calculate_contrast_ratio(color1, color2):
       # Converti hex a RGB
       def hex_to_rgb(hex_color):
           hex_color = hex_color.lstrip('#')
           return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
       
       # Calcola luminanza relativa
       def relative_luminance(rgb):
           def linearize(c):
               c = c / 255.0
               return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
           
           r, g, b = [linearize(c) for c in rgb]
           return 0.2126 * r + 0.7152 * g + 0.0722 * b
       
       rgb1 = hex_to_rgb(color1)
       rgb2 = hex_to_rgb(color2)
       
       l1 = relative_luminance(rgb1)
       l2 = relative_luminance(rgb2)
       
       lighter = max(l1, l2)
       darker = min(l1, l2)
       
       return (lighter + 0.05) / (darker + 0.05)
   
   # Test contrasto
   text_color = "#0d6efd"
   bg_color = "#f0fdff"
   ratio = calculate_contrast_ratio(text_color, bg_color)
   print(f"Contrast ratio: {ratio:.2f} (minimum: 4.5)")
   ```

2. **Usa strumenti online:**
   - WebAIM Contrast Checker
   - Colour Contrast Analyser

**Soluzioni:**

1. **Migliora contrasto automaticamente:**
   ```python
   def improve_contrast(text_color, bg_color, target_ratio=4.5):
       current_ratio = calculate_contrast_ratio(text_color, bg_color)
       
       if current_ratio >= target_ratio:
           return text_color, bg_color
       
       # Scurisci il testo o schiarisci lo sfondo
       # Implementazione semplificata
       if is_light_color(bg_color):
           return darken_color(text_color, 0.3), bg_color
       else:
           return text_color, lighten_color(bg_color, 0.3)
   ```

2. **Suggerisci colori alternativi:**
   ```python
   def suggest_accessible_colors(base_color):
       suggestions = []
       
       # Genera variazioni con contrasto sufficiente
       for lightness in [0.2, 0.3, 0.4, 0.6, 0.7, 0.8]:
           variant = adjust_lightness(base_color, lightness)
           if calculate_contrast_ratio(variant, "#ffffff") >= 4.5:
               suggestions.append(variant)
       
       return suggestions
   ```

## Problemi di Migrazione

### Migrazione Fallita

**Sintomi:**
- Errore durante esecuzione script migrazione
- Dati inconsistenti dopo migrazione
- Unit types senza tema assegnato

**Diagnosi:**

1. **Verifica stato migrazione:**
   ```sql
   -- Controlla se tabella temi esiste
   SELECT name FROM sqlite_master WHERE type='table' AND name='unit_type_themes';
   
   -- Controlla se colonna theme_id esiste
   PRAGMA table_info(unit_types);
   
   -- Controlla temi predefiniti
   SELECT * FROM unit_type_themes WHERE is_default = 1;
   ```

2. **Verifica integrità dati:**
   ```sql
   -- Unit types senza tema
   SELECT * FROM unit_types WHERE theme_id IS NULL;
   
   -- Riferimenti tema non validi
   SELECT ut.* FROM unit_types ut 
   LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id 
   WHERE ut.theme_id IS NOT NULL AND utt.id IS NULL;
   ```

**Soluzioni:**

1. **Esegui migrazione manuale:**
   ```python
   # Script di migrazione manuale
   def manual_migration():
       # 1. Crea tabella temi
       create_theme_table_sql = """
       CREATE TABLE IF NOT EXISTS unit_type_themes (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           name TEXT NOT NULL UNIQUE,
           -- ... altri campi
       );
       """
       
       # 2. Inserisci temi predefiniti
       insert_default_themes()
       
       # 3. Aggiungi colonna theme_id
       add_theme_id_column()
       
       # 4. Assegna temi esistenti
       assign_default_themes()
   ```

2. **Ripara dati inconsistenti:**
   ```sql
   -- Assegna tema predefinito a unit types orfani
   UPDATE unit_types 
   SET theme_id = (SELECT id FROM unit_type_themes WHERE is_default = 1 LIMIT 1)
   WHERE theme_id IS NULL;
   
   -- Rimuovi riferimenti non validi
   UPDATE unit_types 
   SET theme_id = NULL 
   WHERE theme_id NOT IN (SELECT id FROM unit_type_themes);
   ```

### Rollback Necessario

**Sintomi:**
- Sistema instabile dopo migrazione
- Perdita funzionalità critiche
- Errori diffusi nell'applicazione

**Diagnosi:**

1. **Valuta impatto rollback:**
   ```sql
   -- Controlla dati creati dopo migrazione
   SELECT COUNT(*) FROM unit_type_themes 
   WHERE datetime_created > '[MIGRATION_DATE]';
   
   -- Verifica modifiche ai unit types
   SELECT COUNT(*) FROM unit_types WHERE theme_id IS NOT NULL;
   ```

**Soluzioni:**

1. **Esegui rollback controllato:**
   ```python
   def controlled_rollback():
       # 1. Backup dati temi (se necessario conservarli)
       backup_theme_data()
       
       # 2. Rimuovi colonna theme_id
       remove_theme_id_column()
       
       # 3. Elimina tabella temi
       drop_theme_table()
       
       # 4. Ripristina template hardcoded
       restore_hardcoded_templates()
       
       # 5. Valida rollback
       validate_rollback()
   ```

2. **Rollback parziale:**
   ```python
   def partial_rollback():
       # Mantieni struttura database ma disabilita funzionalità
       # Utile se alcuni dati devono essere conservati
       
       # Disabilita tutti i temi
       disable_all_themes()
       
       # Ripristina logica hardcoded nei template
       restore_template_logic()
       
       # Mantieni dati per futuro retry
       mark_migration_as_failed()
   ```

## Problemi di Configurazione

### Tema Predefinito Mancante

**Sintomi:**
- Errore "No default theme found"
- Unit types mostrano stili inconsistenti
- Errori nell'interfaccia admin

**Diagnosi:**

1. **Verifica tema predefinito:**
   ```sql
   SELECT * FROM unit_type_themes WHERE is_default = 1;
   ```

2. **Controlla configurazione:**
   ```python
   from app.services.unit_type_theme import UnitTypeThemeService
   service = UnitTypeThemeService()
   try:
       default_theme = service.get_default_theme()
       print(f"Default theme: {default_theme.name}")
   except Exception as e:
       print(f"Error: {e}")
   ```

**Soluzioni:**

1. **Crea tema predefinito:**
   ```sql
   INSERT INTO unit_type_themes (
       name, description, icon_class, emoji_fallback,
       primary_color, secondary_color, text_color,
       border_width, css_class_suffix, display_label,
       is_default, is_active
   ) VALUES (
       'Default Theme', 'Sistema tema predefinito',
       'diagram-2', '🏛️', '#0dcaf0', '#f0fdff', '#0dcaf0',
       2, 'default', 'Unità', 1, 1
   );
   ```

2. **Ripara configurazione tema predefinito:**
   ```sql
   -- Assicurati che ci sia solo un tema predefinito
   UPDATE unit_type_themes SET is_default = 0;
   UPDATE unit_type_themes SET is_default = 1 WHERE id = [PREFERRED_DEFAULT_ID];
   ```

### Configurazione CSS Errata

**Sintomi:**
- CSS non caricato nelle pagine
- Stili parzialmente applicati
- Errori 404 per `/css/themes.css`

**Diagnosi:**

1. **Verifica route CSS:**
   ```python
   # Controlla che la route sia registrata
   from app.main import app
   for route in app.routes:
       if 'themes.css' in str(route.path):
           print(f"CSS route found: {route.path}")
   ```

2. **Testa generazione CSS:**
   ```python
   from app.services.unit_type_theme import UnitTypeThemeService
   service = UnitTypeThemeService()
   try:
       css = service.generate_dynamic_css()
       print(f"CSS generated successfully: {len(css)} characters")
   except Exception as e:
       print(f"CSS generation failed: {e}")
   ```

**Soluzioni:**

1. **Registra route CSS:**
   ```python
   # In app/routes/themes.py
   @router.get("/css/themes.css", response_class=PlainTextResponse)
   async def dynamic_theme_css():
       service = UnitTypeThemeService()
       css_content = service.generate_dynamic_css()
       return PlainTextResponse(
           css_content,
           media_type="text/css"
       )
   ```

2. **Includi CSS nei template:**
   ```html
   <!-- In templates/base/layout.html -->
   <link rel="stylesheet" href="/css/themes.css">
   ```

## Strumenti di Diagnostica

### Script di Controllo Salute Sistema

```python
#!/usr/bin/env python3
"""
Script per verificare la salute del sistema temi.
Uso: python check_theme_health.py
"""

def check_theme_system_health():
    """Esegue controlli completi del sistema temi."""
    
    print("=== CONTROLLO SALUTE SISTEMA TEMI ===\n")
    
    # 1. Verifica struttura database
    print("1. Controllo struttura database...")
    check_database_structure()
    
    # 2. Verifica temi predefiniti
    print("\n2. Controllo temi predefiniti...")
    check_default_themes()
    
    # 3. Verifica integrità dati
    print("\n3. Controllo integrità dati...")
    check_data_integrity()
    
    # 4. Verifica generazione CSS
    print("\n4. Controllo generazione CSS...")
    check_css_generation()
    
    # 5. Verifica performance
    print("\n5. Controllo performance...")
    check_performance()
    
    print("\n=== CONTROLLO COMPLETATO ===")

def check_database_structure():
    """Verifica struttura tabelle database."""
    # Implementazione controlli database
    pass

def check_default_themes():
    """Verifica esistenza e validità temi predefiniti."""
    # Implementazione controlli temi predefiniti
    pass

def check_data_integrity():
    """Verifica integrità riferimenti e dati."""
    # Implementazione controlli integrità
    pass

def check_css_generation():
    """Verifica generazione CSS dinamico."""
    # Implementazione controlli CSS
    pass

def check_performance():
    """Verifica performance sistema."""
    # Implementazione controlli performance
    pass

if __name__ == "__main__":
    check_theme_system_health()
```

### Script di Riparazione Automatica

```python
#!/usr/bin/env python3
"""
Script per riparazione automatica problemi comuni.
Uso: python repair_theme_system.py [--dry-run]
"""

import argparse

def repair_theme_system(dry_run=False):
    """Ripara automaticamente problemi comuni."""
    
    print("=== RIPARAZIONE SISTEMA TEMI ===\n")
    
    if dry_run:
        print("MODALITÀ DRY-RUN: Nessuna modifica verrà effettuata\n")
    
    repairs = []
    
    # 1. Ripara tema predefinito mancante
    if needs_default_theme_repair():
        repairs.append(("default_theme", repair_default_theme))
    
    # 2. Ripara unit types orfani
    orphaned_count = count_orphaned_unit_types()
    if orphaned_count > 0:
        repairs.append(("orphaned_units", repair_orphaned_unit_types))
    
    # 3. Ripara colori non validi
    invalid_colors = find_invalid_colors()
    if invalid_colors:
        repairs.append(("invalid_colors", repair_invalid_colors))
    
    # Esegui riparazioni
    for repair_name, repair_func in repairs:
        print(f"Eseguendo riparazione: {repair_name}")
        if not dry_run:
            try:
                repair_func()
                print(f"✓ {repair_name} completata")
            except Exception as e:
                print(f"✗ {repair_name} fallita: {e}")
        else:
            print(f"→ {repair_name} (simulata)")
    
    print(f"\n=== RIPARAZIONE COMPLETATA ({len(repairs)} operazioni) ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", 
                       help="Simula riparazioni senza modificare dati")
    args = parser.parse_args()
    
    repair_theme_system(dry_run=args.dry_run)
```

## Contatti e Supporto

### Escalation dei Problemi

1. **Livello 1 - Utente finale:**
   - Consulta questa guida
   - Prova soluzioni base (cache, refresh)
   - Contatta amministratore locale

2. **Livello 2 - Amministratore sistema:**
   - Usa script diagnostici
   - Applica soluzioni avanzate
   - Consulta log applicazione

3. **Livello 3 - Sviluppatore:**
   - Analizza codice sorgente
   - Debug approfondito
   - Modifica codice se necessario

### Log e Monitoraggio

```python
# Configurazione logging per temi
import logging

theme_logger = logging.getLogger('theme_system')
theme_logger.setLevel(logging.INFO)

# Handler per file log dedicato
handler = logging.FileHandler('theme_system.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
theme_logger.addHandler(handler)

# Uso nei servizi
def create_theme(self, theme):
    theme_logger.info(f"Creating theme: {theme.name}")
    try:
        result = self._create_theme_in_db(theme)
        theme_logger.info(f"Theme created successfully: {result.id}")
        return result
    except Exception as e:
        theme_logger.error(f"Failed to create theme {theme.name}: {e}")
        raise
```

---

*Questa guida viene aggiornata regolarmente. Per problemi non coperti, contatta il team di sviluppo con dettagli specifici del problema e log di errore.*