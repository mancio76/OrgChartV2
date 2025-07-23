# Organigramma Web App

Sistema web per la gestione dell'organigramma aziendale con storicizzazione degli incarichi, costruito con FastAPI, SQLite e Bootstrap.

## 🚀 Caratteristiche

- **CRUD completo** per tutte le entità (Units, Job Titles, Persons, Assignments)
- **Versioning automatico** degli incarichi con storico completo
- **Visualizzazione ad albero** dell'organigramma
- **Interfaccia responsive** con Bootstrap 5
- **Database SQLite** con integrità referenziale
- **Architettura modulare** con servizi separati
- **JavaScript vanilla** per massima portabilità

## 🏗️ Architettura

### Backend
- **FastAPI** - Framework web moderno e veloce
- **SQLite** - Database embedded con schema v3
- **Jinja2** - Template engine per HTML
- **Uvicorn** - Server ASGI ad alte prestazioni

### Frontend  
- **Bootstrap 5** - Framework CSS responsive
- **Bootstrap Icons** - Set di icone
- **Vanilla JavaScript** - Senza dipendenze esterne
- **CSS modulare** - Stili organizzati per componenti

### Database
- **Schema con versioning** - Storico completo degli incarichi
- **Trigger automatici** - Gestione versioni e audit trail
- **Views ottimizzate** - Per gerarchia e statistiche
- **Foreign keys** - Integrità referenziale

## 📋 Prerequisiti

- Python 3.8+
- pip
- Browser moderno (Chrome, Firefox, Safari, Edge)

## 🛠️ Installazione

### 1. Clona/Crea il progetto

```bash
# Crea la struttura cartelle come da folder_structure.txt
mkdir orgchart_webapp
cd orgchart_webapp
```

### 2. Installa le dipendenze

```bash
# Crea ambiente virtuale (opzionale ma consigliato)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate     # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 3. Inizializza il database

```bash
# Copia prima i file SQL nella cartella database/
cp orgchart_sqlite_schema_v3.sql database/schema.sql
cp orgchart_data_migration.sql database/migration_data.sql

# Esegui script di inizializzazione
python scripts/init_db.py
```

### 4. Avvia l'applicazione

```bash
python run.py
```

L'applicazione sarà disponibile su: **http://localhost:8000**

## 📁 Struttura del Progetto

```
orgchart_webapp/
├── app/                    # Codice applicazione
│   ├── models/            # Dataclass models
│   ├── services/          # Business logic
│   ├── routes/            # FastAPI routes
│   └── utils/             # Utility functions
├── static/                # File statici
│   ├── css/              # Fogli di stile modulari
│   ├── js/               # JavaScript per sezione
│   └── images/           # Immagini e icone
├── templates/             # Template HTML
│   ├── base/             # Layout base
│   ├── components/       # Componenti riusabili
│   └── [sections]/       # Template per sezione
├── database/              # Database e script SQL
├── scripts/               # Script di utilità
└── config/                # Configurazioni
```

## 🔧 Configurazione

### File .env

```bash
DEBUG=true
HOST=0.0.0.0  
PORT=8000
LOG_LEVEL=info
DATABASE_URL=database/organigramma.db
SECRET_KEY=your-secret-key-here
```

### Impostazioni Database

- **Database**: SQLite con foreign keys abilitati
- **Encoding**: UTF-8
- **Backup automatico**: Configurabile
- **Logging**: Query e errori tracciati

## 📊 Utilizzo

### Dashboard
- Statistiche in tempo reale
- Azioni rapide per entità principali
- Overview della struttura organizzativa

### Gestione Unità
- Creazione unità con gerarchia
- Tipi: function / OrganizationalUnit
- Validazione parent-child

### Gestione Persone
- Anagrafica completa
- Validazione email
- Collegamento agli incarichi

### Gestione Ruoli
- Definizione job titles
- Supporto multilingua
- Associazione a unità

### Gestione Incarichi
- **Creazione**: Nuovo incarico automaticamente versione 1
- **Modifica**: Crea nuova versione, mantiene storia
- **Terminazione**: Imposta data fine
- **Storico**: Visualizzazione completa versioni

### Organigramma
- Visualizzazione ad albero
- Statistiche per unità
- Navigazione interattiva

## 🔄 Versioning degli Incarichi

Il sistema gestisce automaticamente le versioni degli incarichi:

1. **Nuovo incarico**: Versione 1, `is_current = TRUE`
2. **Modifica incarico**: Nuova versione, precedente `is_current = FALSE`
3. **Terminazione**: `valid_to` impostato, `is_current = FALSE`

### Esempio SQL

```sql
-- Nuovo incarico
INSERT INTO person_job_assignments 
(person_id, unit_id, job_title_id, percentage, valid_from)
VALUES (1, 5, 7, 1.0, '2025-01-01');
-- Crea automaticamente versione 1

-- Modifica (nuovo incarico)
INSERT INTO person_job_assignments 
(person_id, unit_id, job_title_id, percentage, valid_from)
VALUES (1, 5, 7, 0.8, '2025-06-01');
-- Crea automaticamente versione 2, versione 1 diventa storica
```

## 🎨 CSS e JavaScript

### CSS Modulare
- `base.css` - Stili globali e utilities
- `components.css` - Componenti riusabili  
- `[section].css` - Stili specifici per sezione

### JavaScript Modulare
- `base.js` - Funzioni globali e utilities
- `components.js` - Componenti UI (modal, alert)
- `[section].js` - Logica specifica per sezione

## 🚦 API Endpoints

### Units
- `GET /units` - Lista unità
- `GET /units/{id}` - Dettaglio unità  
- `POST /units/new` - Crea unità
- `POST /units/{id}/edit` - Modifica unità
- `POST /units/{id}/delete` - Elimina unità

### Persons
- `GET /persons` - Lista persone
- `GET /persons/{id}` - Dettaglio persona
- `POST /persons/new` - Crea persona
- `POST /persons/{id}/edit` - Modifica persona

### Job Titles
- `GET /job-titles` - Lista ruoli
- `GET /job-titles/{id}` - Dettaglio ruolo
- `POST /job-titles/new` - Crea ruolo

### Assignments  
- `GET /assignments` - Lista incarichi correnti
- `GET /assignments/history` - Storico completo
- `POST /assignments/new` - Crea incarico
- `POST /assignments/{id}/terminate` - Termina incarico

### Orgchart
- `GET /orgchart/tree` - Vista ad albero
- `GET /orgchart/stats` - Statistiche

## 🧪 Testing

```bash
# Installa dipendenze di test
pip install pytest pytest-asyncio httpx

# Esegui test
pytest tests/
```

## 📝 Logging

I log sono salvati in:
- **Console**: Tutti i messaggi
- **File app.log**: Errori e info importanti
- **Database**: Query e operazioni CRUD

## 🔒 Sicurezza

- **Input validation**: Validazione lato server
- **SQL injection**: Prepared statements
- **XSS protection**: Template escaping  
- **CSRF**: Token nelle form (da implementare)

## 🚀 Deploy in Produzione

### 1. Configurazione

```bash
# .env per produzione
DEBUG=false
SECRET_KEY=your-strong-secret-key
LOG_LEVEL=warning
```

### 2. Server Web

```bash
# Con Gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Con Docker (opzionale)
docker build -t orgchart-app .
docker run -p 8000:8000 orgchart-app
```

### 3. Database

- **Backup regolare** di `database/organigramma.db`
- **Monitor dimensioni** database
- **Indici ottimizzati** per performance

## 🛠️ Sviluppo

### Aggiungere nuove funzionalità

1. **Modello**: Crea dataclass in `app/models/`
2. **Servizio**: Implementa business logic in `app/services/`  
3. **Route**: Aggiungi endpoints in `app/routes/`
4. **Template**: Crea HTML in `templates/`
5. **CSS/JS**: Aggiungi stili e logica in `static/`

### Convenzioni

- **Python**: PEP 8, type hints, docstrings
- **HTML**: Semantic HTML5, accessibility
- **CSS**: BEM methodology, mobile-first
- **JavaScript**: ES6+, camelCase, JSDoc

## 🤝 Contribuire

1. Fork del progetto
2. Crea feature branch (`git checkout -b feature/nuova-funzionalita`)
3. Commit modifiche (`git commit -m 'Aggiunge nuova funzionalità'`)
4. Push branch (`git push origin feature/nuova-funzionalita`) 
5. Apri Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 📞 Supporto

Per supporto e domande:
- Apri un issue su GitHub
- Consulta la documentazione nel codice
- Controlla i log per errori specifici

---

**Organigramma Web App** - Sistema moderno per la gestione dell'organigramma aziendale 🏢