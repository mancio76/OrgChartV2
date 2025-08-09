# Guida Rapida - Import/Export Organigramma

## Operazioni Comuni

### 🔄 Importazione Rapida
```
1. Menu → Importazione/Esportazione → Importa Dati
2. Seleziona file → Scegli formato (CSV/JSON)
3. Anteprima → Verifica errori → Conferma
4. Monitora stato → Verifica risultati
```

### 📤 Esportazione Rapida
```
1. Menu → Importazione/Esportazione → Esporta Dati
2. Seleziona formato → Scegli entità → Configura opzioni
3. Genera → Scarica file ZIP
```

### 👀 Anteprima Importazione
```
1. Carica file → Seleziona "Solo Anteprima"
2. Controlla errori rossi (bloccanti)
3. Rivedi avvisi gialli (non bloccanti)
4. Se OK → Procedi con importazione reale
```

## Formati File

### 📊 CSV - Campi Obbligatori

**Unit Types**: `name`, `short_name`
**Units**: `name`, `short_name`, `unit_type_id`, `start_date`
**Job Titles**: `name`, `short_name`, `start_date`
**Persons**: `name`, `short_name`, `email`
**Assignments**: `person_id`, `unit_id`, `job_title_id`, `valid_from`

### 📋 JSON - Struttura Base
```json
{
  "metadata": {"export_date": "2024-01-15T10:30:00Z"},
  "unit_types": [{"name": "...", "short_name": "..."}],
  "units": [{"name": "...", "unit_type_id": 1, "start_date": "2024-01-01"}]
}
```

## Risoluzione Conflitti

| Strategia | Quando Usare | Effetto |
|-----------|--------------|---------|
| **Ignora** | Dati stabili, evitare sovrascritture | Mantiene esistenti |
| **Aggiorna** | Correzioni, aggiornamenti struttura | Sovrascrive esistenti |
| **Nuova Versione** | Solo incarichi, mantenere storico | Crea versione |

## Ordine Importazione

```
1. Unit Types (Tipi Unità)
2. Unit Type Themes (Temi)
3. Units (Unità) 
4. Job Titles (Titoli)
5. Persons (Persone)
6. Assignments (Incarichi)
```

## Errori Comuni

### ❌ "Riferimento non trovato"
**Causa**: ID referenziato non esiste
**Soluzione**: Importa entità dipendenze prima

### ❌ "Formato data non valido"
**Causa**: Data non in formato YYYY-MM-DD
**Soluzione**: Correggi formato date

### ❌ "Email duplicata"
**Causa**: Stesso email per più persone
**Soluzione**: Usa strategia "Aggiorna" o correggi email

### ❌ "Encoding non valido"
**Causa**: File non in UTF-8
**Soluzione**: Salva file come UTF-8

## Limiti Sistema

| Parametro | Limite | Note |
|-----------|--------|------|
| Dimensione file | 100MB | Per singolo file |
| Record per batch | 100 | Configurabile |
| Operazioni simultanee | 3 | Import + Export |
| Timeout operazione | 5 min | Per operazioni normali |

## Backup Rapido

### 🔄 Backup Completo
```
Esporta → JSON → Tutte entità → Includi storico → Genera
```

### 📅 Backup Programmato
```
Menu → Esportazioni Programmate → Nuova → 
Frequenza: Giornaliera → Ora: 02:00 → Attiva
```

## Monitoraggio

### 📊 Stato Operazioni
```
Menu → Importazione/Esportazione → Operazioni Recenti
```

### 📈 Dashboard
- Operazioni in corso
- Statistiche successo/errore
- Utilizzo risorse

## Template Rapidi

### 📁 Scarica Template
```
docs/import-export-templates/
├── unit_types_template.csv
├── units_template.csv
├── persons_template.csv
├── assignments_template.csv
└── complete_template.json
```

## Comandi Utili

### 🔍 Verifica File CSV
```bash
# Controlla encoding
file -I filename.csv

# Conta righe
wc -l filename.csv

# Visualizza prime righe
head -5 filename.csv
```

### 🔧 Correzione Encoding
```bash
# Converti a UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
```

## Contatti Supporto

- **Supporto Tecnico**: supporto@azienda.com
- **Documentazione**: `/docs/import-export-user-guide.md`
- **Template**: `/docs/import-export-templates/`
- **Best Practices**: `/docs/import-export-best-practices.md`

---
*Ultima modifica: Gennaio 2024*