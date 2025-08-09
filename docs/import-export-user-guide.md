# Guida Utente - Sistema di Importazione ed Esportazione Dati

## Panoramica

Il sistema di importazione ed esportazione dati permette di gestire in modo efficiente i dati dell'organigramma aziendale. È possibile importare dati da file CSV o JSON e esportare i dati esistenti per backup o migrazione.

## Funzionalità Principali

- **Importazione dati**: Caricamento di dati da file CSV o JSON
- **Esportazione dati**: Generazione di file di backup in formato CSV o JSON
- **Anteprima importazione**: Verifica dei dati prima dell'importazione definitiva
- **Risoluzione conflitti**: Gestione automatica dei record duplicati
- **Monitoraggio operazioni**: Tracciamento dello stato delle operazioni
- **Esportazioni programmate**: Backup automatici su base periodica

## Accesso al Sistema

1. Accedere all'applicazione web dell'organigramma
2. Navigare nel menu principale e selezionare "Importazione/Esportazione"
3. Scegliere l'operazione desiderata dal dashboard

## Importazione Dati

### Preparazione dei File

Prima di importare i dati, assicurarsi che i file rispettino il formato corretto:

#### Formato CSV
- Un file separato per ogni tipo di entità
- Encoding UTF-8
- Separatore: virgola (,)
- Intestazioni obbligatorie nella prima riga

#### Formato JSON
- Un singolo file con struttura gerarchica
- Encoding UTF-8
- Formato JSON valido

### Procedura di Importazione

1. **Selezione File**
   - Cliccare su "Importa Dati"
   - Selezionare il formato (CSV o JSON)
   - Caricare il file o i file necessari

2. **Configurazione Opzioni**
   - Selezionare i tipi di entità da importare
   - Scegliere la strategia di risoluzione conflitti:
     - **Ignora duplicati**: Mantiene i dati esistenti
     - **Aggiorna esistenti**: Sovrascrive con i nuovi dati
     - **Crea nuova versione**: Per gli incarichi, crea una nuova versione

3. **Anteprima (Raccomandato)**
   - Cliccare su "Anteprima" per verificare i dati
   - Controllare eventuali errori o avvisi
   - Verificare le relazioni tra entità

4. **Conferma Importazione**
   - Se l'anteprima è soddisfacente, cliccare "Conferma Importazione"
   - Monitorare il progresso nella pagina di stato

### Ordine di Importazione

Il sistema importa automaticamente le entità nel seguente ordine per rispettare le dipendenze:

1. **Tipi di Unità** (Unit Types)
2. **Temi Tipi di Unità** (Unit Type Themes)
3. **Unità Organizzative** (Units)
4. **Titoli Lavorativi** (Job Titles)
5. **Persone** (Persons)
6. **Incarichi** (Assignments)

## Esportazione Dati

### Procedura di Esportazione

1. **Configurazione Esportazione**
   - Cliccare su "Esporta Dati"
   - Selezionare il formato di output (CSV o JSON)
   - Scegliere i tipi di entità da esportare

2. **Opzioni Avanzate**
   - **Includi storico**: Esporta anche le versioni precedenti degli incarichi
   - **Intervallo date**: Limita l'esportazione a un periodo specifico
   - **Filtri entità**: Seleziona solo specifiche unità o persone

3. **Generazione File**
   - Cliccare "Genera Esportazione"
   - Attendere la generazione dei file
   - Scaricare il file ZIP contenente tutti i dati

### Formati di Esportazione

#### CSV
- File separati per ogni tipo di entità
- Facile da importare in Excel o altri sistemi
- Ideale per analisi dati

#### JSON
- File singolo con struttura completa
- Mantiene le relazioni tra entità
- Ideale per backup completi

## Gestione Conflitti

### Tipi di Conflitto

1. **Record Duplicati**: Stesso email per persone, stesso nome per unità
2. **Riferimenti Mancanti**: Riferimenti a entità non esistenti
3. **Violazioni Regole Business**: Dati che non rispettano le regole aziendali

### Strategie di Risoluzione

#### Ignora Duplicati
- Mantiene i dati esistenti nel sistema
- Salta i record duplicati durante l'importazione
- Genera un report dei record ignorati

#### Aggiorna Esistenti
- Sovrascrive i dati esistenti con quelli nuovi
- Mantiene l'ID originale del record
- Aggiorna tutti i campi modificati

#### Crea Nuova Versione (Solo Incarichi)
- Crea una nuova versione dell'incarico
- Mantiene lo storico completo
- Termina automaticamente la versione precedente

## Monitoraggio Operazioni

### Dashboard Operazioni

Il dashboard mostra:
- Operazioni in corso
- Storico operazioni recenti
- Statistiche di successo/errore
- Tempo di esecuzione

### Stati Operazione

- **In Attesa**: Operazione in coda
- **In Corso**: Elaborazione in corso
- **Completata**: Operazione terminata con successo
- **Fallita**: Operazione terminata con errori
- **Annullata**: Operazione annullata dall'utente

### Dettagli Operazione

Per ogni operazione è possibile visualizzare:
- Numero di record elaborati
- Record creati, aggiornati, ignorati
- Lista dettagliata degli errori
- Tempo di esecuzione
- File utilizzati

## Esportazioni Programmate

### Configurazione Backup Automatici

1. **Accesso Configurazione**
   - Navigare in "Esportazioni Programmate"
   - Cliccare "Nuova Programmazione"

2. **Impostazioni Programmazione**
   - **Frequenza**: Giornaliera, settimanale, mensile
   - **Orario**: Ora di esecuzione preferita
   - **Formato**: CSV o JSON
   - **Entità**: Tipi di dati da includere

3. **Gestione File**
   - **Cartella destinazione**: Dove salvare i backup
   - **Rotazione file**: Numero massimo di backup da mantenere
   - **Notifiche**: Email di conferma o errore

### Monitoraggio Backup

- Visualizzazione calendario esecuzioni
- Stato ultima esecuzione
- Dimensione file generati
- Log errori eventuali

## Formati File Supportati

### Struttura CSV

#### Tipi di Unità (unit_types.csv)
```csv
id,name,short_name,aliases,level,theme_id
1,"Direzione Generale","DG","[{""value"":""General Direction"",""lang"":""en-US""}]",1,1
2,"Ufficio","UFF","[]",2,1
```

**Campi Obbligatori:**
- `name`: Nome del tipo di unità
- `short_name`: Nome abbreviato

**Campi Opzionali:**
- `id`: Identificativo (auto-generato se vuoto)
- `aliases`: Alias multilingua in formato JSON
- `level`: Livello gerarchico
- `theme_id`: Riferimento al tema

#### Temi Tipi di Unità (unit_type_themes.csv)
```csv
id,name,description,icon_class,emoji_fallback,primary_color,secondary_color,text_color,display_label,is_active
1,"Tema Predefinito","Tema organizzativo predefinito","diagram-2","🏛️","#0dcaf0","#f0fdff","#0dcaf0","Unità Organizzativa",true
```

**Campi Obbligatori:**
- `name`: Nome del tema
- `primary_color`: Colore primario (formato hex)

#### Unità Organizzative (units.csv)
```csv
id,name,short_name,aliases,unit_type_id,parent_unit_id,start_date,end_date
1,"Direzione Generale","DG","[]",1,,2024-01-01,
2,"Ufficio Personale","UP","[]",2,1,2024-01-01,
```

**Campi Obbligatori:**
- `name`: Nome dell'unità
- `short_name`: Nome abbreviato
- `unit_type_id`: Riferimento al tipo di unità
- `start_date`: Data di inizio (formato YYYY-MM-DD)

#### Titoli Lavorativi (job_titles.csv)
```csv
id,name,short_name,aliases,start_date,end_date
1,"Direttore Generale","DG","[{""value"":""General Director"",""lang"":""en-US""}]",2024-01-01,
```

**Campi Obbligatori:**
- `name`: Nome del titolo
- `short_name`: Nome abbreviato
- `start_date`: Data di inizio

#### Persone (persons.csv)
```csv
id,name,short_name,email,first_name,last_name,registration_no,profile_image
1,"Mario Rossi","M.Rossi","mario.rossi@example.com","Mario","Rossi","EMP001","profiles/mario.rossi.jpg"
```

**Campi Obbligatori:**
- `name`: Nome completo
- `short_name`: Nome visualizzato
- `email`: Indirizzo email (univoco)

#### Incarichi (assignments.csv)
```csv
id,person_id,unit_id,job_title_id,version,percentage,is_ad_interim,is_unit_boss,notes,valid_from,valid_to,is_current
1,1,1,1,1,1.0,false,true,"Incarico iniziale",2024-01-01,,true
```

**Campi Obbligatori:**
- `person_id`: Riferimento alla persona
- `unit_id`: Riferimento all'unità
- `job_title_id`: Riferimento al titolo lavorativo
- `valid_from`: Data inizio incarico

### Struttura JSON

```json
{
  "metadata": {
    "export_date": "2024-01-15T10:30:00Z",
    "version": "1.0",
    "total_records": 150
  },
  "unit_types": [
    {
      "id": 1,
      "name": "Direzione Generale",
      "short_name": "DG",
      "aliases": [{"value": "General Direction", "lang": "en-US"}],
      "level": 1,
      "theme_id": 1
    }
  ],
  "units": [
    {
      "id": 1,
      "name": "Direzione Generale",
      "short_name": "DG",
      "unit_type_id": 1,
      "parent_unit_id": null,
      "start_date": "2024-01-01"
    }
  ]
}
```

## Risoluzione Problemi Comuni

### Errori di Formato File

**Problema**: "Formato CSV non valido"
**Soluzione**: 
- Verificare che il file sia codificato in UTF-8
- Controllare che la prima riga contenga le intestazioni
- Assicurarsi che il separatore sia la virgola

**Problema**: "Errore parsing JSON"
**Soluzione**:
- Validare la sintassi JSON con un validatore online
- Verificare che tutte le parentesi siano chiuse correttamente
- Controllare che non ci siano virgole finali

### Errori di Validazione Dati

**Problema**: "Campo obbligatorio mancante"
**Soluzione**:
- Verificare che tutti i campi obbligatori siano presenti
- Controllare che i valori non siano vuoti
- Consultare la documentazione per i campi richiesti

**Problema**: "Riferimento non trovato"
**Soluzione**:
- Importare le entità nell'ordine corretto
- Verificare che gli ID referenziati esistano
- Utilizzare l'anteprima per identificare i riferimenti mancanti

### Problemi di Performance

**Problema**: "Importazione troppo lenta"
**Soluzione**:
- Ridurre la dimensione del batch nelle opzioni avanzate
- Dividere file molto grandi in più parti
- Importare un tipo di entità alla volta

**Problema**: "Memoria insufficiente"
**Soluzione**:
- Ridurre la dimensione del file
- Utilizzare il formato CSV invece di JSON per file grandi
- Contattare l'amministratore per aumentare i limiti

## Best Practices

### Preparazione Dati

1. **Backup Preventivo**: Eseguire sempre un backup prima di importazioni massive
2. **Validazione Offline**: Controllare i dati in Excel prima dell'importazione
3. **Test su Ambiente**: Testare l'importazione su dati di prova
4. **Importazione Graduale**: Importare piccoli lotti per verificare il processo

### Gestione Errori

1. **Anteprima Obbligatoria**: Utilizzare sempre l'anteprima prima dell'importazione
2. **Log degli Errori**: Salvare e analizzare i log degli errori
3. **Correzione Iterativa**: Correggere gli errori e ripetere l'importazione
4. **Documentazione Modifiche**: Tenere traccia delle modifiche apportate

### Sicurezza Dati

1. **Accesso Limitato**: Solo utenti autorizzati possono importare/esportare
2. **Audit Trail**: Tutte le operazioni sono registrate
3. **Backup Regolari**: Configurare backup automatici periodici
4. **Verifica Integrità**: Controllare l'integrità dei dati dopo l'importazione

### Performance

1. **Orari Ottimali**: Eseguire importazioni massive fuori orario lavorativo
2. **Monitoraggio Risorse**: Verificare l'utilizzo di CPU e memoria
3. **Batch Sizing**: Ottimizzare la dimensione dei batch per il sistema
4. **Pulizia Temporanea**: Eliminare file temporanei dopo le operazioni

## Supporto e Assistenza

### Contatti

- **Supporto Tecnico**: supporto@azienda.com
- **Documentazione**: Consultare la documentazione tecnica completa
- **Training**: Richiedere sessioni di formazione per nuovi utenti

### Risorse Aggiuntive

- **Video Tutorial**: Disponibili nel portale aziendale
- **FAQ**: Domande frequenti e risposte
- **Community**: Forum interno per condividere esperienze
- **Aggiornamenti**: Newsletter con nuove funzionalità e miglioramenti

Questa guida fornisce tutte le informazioni necessarie per utilizzare efficacemente il sistema di importazione ed esportazione dati dell'organigramma aziendale.