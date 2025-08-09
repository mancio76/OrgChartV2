# Best Practices e Workflow - Sistema Importazione/Esportazione

## Panoramica

Questo documento fornisce le migliori pratiche per l'utilizzo efficace del sistema di importazione ed esportazione dati dell'organigramma aziendale.

## Workflow Raccomandati

### 1. Workflow di Importazione Completa

#### Fase di Preparazione
1. **Analisi Dati Esistenti**
   - Esportare i dati attuali come backup
   - Analizzare la struttura organizzativa esistente
   - Identificare eventuali inconsistenze nei dati

2. **Preparazione File di Importazione**
   - Utilizzare i template forniti
   - Validare i dati offline (Excel, editor JSON)
   - Verificare l'encoding UTF-8
   - Controllare i formati data e i riferimenti

3. **Test su Ambiente di Sviluppo**
   - Testare l'importazione su un ambiente di test
   - Verificare l'integrità dei dati importati
   - Controllare le relazioni tra entità

#### Fase di Esecuzione
1. **Backup Preventivo**
   ```bash
   # Eseguire backup completo prima dell'importazione
   Esportazione → Formato JSON → Tutte le entità → Includi storico
   ```

2. **Importazione Graduale**
   - Importare un tipo di entità alla volta
   - Utilizzare sempre l'anteprima prima della conferma
   - Monitorare i log per eventuali errori

3. **Verifica Post-Importazione**
   - Controllare i conteggi dei record
   - Verificare le relazioni tra entità
   - Testare la visualizzazione dell'organigramma

### 2. Workflow di Migrazione Sistema

#### Preparazione Migrazione
1. **Mappatura Dati**
   - Creare una mappatura tra il sistema sorgente e destinazione
   - Identificare i campi obbligatori e opzionali
   - Definire le regole di trasformazione dati

2. **Estrazione Dati**
   - Esportare dati dal sistema sorgente
   - Trasformare i dati nel formato richiesto
   - Validare la completezza dell'estrazione

3. **Preparazione Ambiente**
   - Configurare l'ambiente di destinazione
   - Creare utenti e permessi necessari
   - Preparare le cartelle per i file temporanei

#### Esecuzione Migrazione
1. **Migrazione Pilota**
   - Migrare un sottoinsieme rappresentativo di dati
   - Verificare l'accuratezza della migrazione
   - Documentare eventuali problemi riscontrati

2. **Migrazione Completa**
   - Eseguire la migrazione completa fuori orario lavorativo
   - Monitorare continuamente il processo
   - Mantenere log dettagliati di tutte le operazioni

3. **Verifica e Validazione**
   - Confrontare i dati migrati con quelli originali
   - Eseguire test funzionali completi
   - Ottenere l'approvazione degli utenti finali

### 3. Workflow di Backup e Ripristino

#### Backup Regolari
1. **Configurazione Backup Automatici**
   ```
   Frequenza: Giornaliera (ore notturne)
   Formato: JSON (per completezza)
   Entità: Tutte
   Storico: Incluso
   Rotazione: 30 giorni
   ```

2. **Backup Manuali Pre-Modifiche**
   - Prima di importazioni massive
   - Prima di modifiche strutturali
   - Prima di aggiornamenti sistema

#### Procedura di Ripristino
1. **Valutazione Danno**
   - Identificare l'estensione del problema
   - Determinare il punto di ripristino ottimale
   - Valutare l'impatto sugli utenti

2. **Ripristino Dati**
   - Arrestare le operazioni in corso
   - Ripristinare dal backup più recente valido
   - Verificare l'integrità dei dati ripristinati

## Best Practices per Tipo di Operazione

### Importazione Dati

#### Preparazione File
1. **Validazione Offline**
   ```excel
   # Controlli Excel raccomandati:
   - Verifica duplicati (email, codici)
   - Controllo formati data
   - Validazione riferimenti incrociati
   - Controllo caratteri speciali
   ```

2. **Struttura Dati**
   - Mantenere coerenza nei nomi
   - Utilizzare convenzioni di naming uniformi
   - Evitare caratteri speciali nei nomi file
   - Documentare eventuali abbreviazioni

3. **Gestione Encoding**
   ```bash
   # Verifica encoding file
   file -I filename.csv
   
   # Conversione a UTF-8 se necessario
   iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
   ```

#### Strategie di Importazione
1. **Importazione Incrementale**
   - Importare prima le entità base (unit_types, job_titles)
   - Procedere con le entità dipendenti (units, persons)
   - Concludere con gli incarichi (assignments)

2. **Gestione Errori**
   - Utilizzare sempre l'anteprima
   - Correggere gli errori uno alla volta
   - Mantenere log delle correzioni apportate

3. **Risoluzione Conflitti**
   ```
   Strategia per entità:
   - Unit Types: Update (raramente cambiano)
   - Units: Update (struttura può evolversi)
   - Persons: Skip (evitare sovrascritture accidentali)
   - Assignments: Create Version (mantenere storico)
   ```

### Esportazione Dati

#### Pianificazione Export
1. **Frequenza Backup**
   - Giornaliera: Per dati critici in produzione
   - Settimanale: Per ambienti di sviluppo
   - Mensile: Per archivi storici

2. **Formato Selezione**
   ```
   CSV: 
   - Analisi dati in Excel
   - Integrazione con sistemi esterni
   - File di dimensioni ridotte
   
   JSON:
   - Backup completi
   - Migrazione sistemi
   - Mantenimento relazioni
   ```

#### Gestione File Export
1. **Naming Convention**
   ```
   orgchart_export_YYYYMMDD_HHMMSS.zip
   orgchart_backup_YYYYMMDD.json
   orgchart_partial_units_YYYYMMDD.csv
   ```

2. **Archiviazione**
   - Cartelle organizzate per data
   - Compressione per file grandi
   - Backup su storage esterno

## Ottimizzazione Performance

### File di Grandi Dimensioni

#### Preparazione
1. **Suddivisione File**
   ```
   Limiti raccomandati:
   - CSV: Max 10,000 righe per file
   - JSON: Max 50MB per file
   - Batch import: 100-500 record per batch
   ```

2. **Ottimizzazione Formato**
   - Rimuovere colonne non necessarie
   - Utilizzare abbreviazioni per campi ripetitivi
   - Comprimere file prima dell'upload

#### Esecuzione
1. **Monitoraggio Risorse**
   - Verificare utilizzo memoria
   - Monitorare spazio disco temporaneo
   - Controllare connessioni database

2. **Batch Processing**
   ```python
   # Configurazione ottimale per file grandi
   import_options = {
       "batch_size": 100,
       "memory_limit": "256MB",
       "timeout": 600  # 10 minuti
   }
   ```

### Operazioni Concorrenti

#### Limitazioni
1. **Operazioni Simultanee**
   - Max 2 importazioni contemporanee
   - Max 1 esportazione grande contemporanea
   - Evitare import/export simultanei

2. **Scheduling**
   - Importazioni: Orari di basso traffico
   - Esportazioni: Fuori orario lavorativo
   - Backup: Ore notturne

## Sicurezza e Compliance

### Controllo Accessi

#### Permessi Utente
1. **Ruoli Definiti**
   ```
   Administrator: Tutte le operazioni
   HR Manager: Import/Export persone e incarichi
   Unit Manager: Export solo unità di competenza
   Viewer: Solo visualizzazione
   ```

2. **Audit Trail**
   - Log di tutte le operazioni
   - Tracciamento modifiche dati
   - Retention log per compliance

#### Protezione Dati
1. **Dati Sensibili**
   - Crittografia file temporanei
   - Pulizia automatica file upload
   - Mascheramento dati in log

2. **Backup Security**
   - Crittografia backup
   - Accesso limitato ai file backup
   - Verifica integrità periodica

### Compliance GDPR

#### Gestione Dati Personali
1. **Minimizzazione Dati**
   - Importare solo dati necessari
   - Evitare campi sensibili non richiesti
   - Documentare finalità trattamento

2. **Diritto Cancellazione**
   - Procedura per rimozione dati
   - Backup senza dati cancellati
   - Log delle cancellazioni

## Troubleshooting Avanzato

### Problemi Comuni e Soluzioni

#### Errori di Memoria
```bash
# Sintomi
- "Out of memory" durante import
- Processo che si blocca
- Timeout operazioni

# Soluzioni
1. Ridurre batch_size a 50
2. Dividere file in parti più piccole
3. Aumentare memoria sistema
4. Utilizzare formato CSV invece di JSON
```

#### Errori di Integrità Referenziale
```sql
-- Verifica integrità dopo import
SELECT 'units' as table_name, COUNT(*) as orphaned
FROM units u 
LEFT JOIN unit_types ut ON u.unit_type_id = ut.id 
WHERE ut.id IS NULL

UNION ALL

SELECT 'assignments', COUNT(*)
FROM assignments a
LEFT JOIN persons p ON a.person_id = p.id
WHERE p.id IS NULL;
```

#### Performance Degradation
```python
# Monitoraggio performance
import psutil
import time

def monitor_import():
    start_time = time.time()
    start_memory = psutil.virtual_memory().used
    
    # Esegui importazione
    result = import_service.import_data(...)
    
    end_time = time.time()
    end_memory = psutil.virtual_memory().used
    
    print(f"Tempo: {end_time - start_time:.2f}s")
    print(f"Memoria: {(end_memory - start_memory) / 1024 / 1024:.2f}MB")
```

### Procedure di Recovery

#### Recovery da Importazione Fallita
1. **Identificazione Problema**
   - Analizzare log errori
   - Identificare punto di fallimento
   - Valutare dati parzialmente importati

2. **Rollback Procedure**
   ```sql
   -- Rollback manuale se necessario
   BEGIN TRANSACTION;
   
   DELETE FROM assignments WHERE created_date > 'YYYY-MM-DD HH:MM:SS';
   DELETE FROM persons WHERE created_date > 'YYYY-MM-DD HH:MM:SS';
   -- ... altri rollback
   
   COMMIT; -- Solo se tutto OK
   ```

3. **Ripristino Stato**
   - Ripristinare da backup se necessario
   - Verificare integrità dati
   - Riavviare servizi se richiesto

## Checklist Operative

### Pre-Importazione
- [ ] Backup dati esistenti completato
- [ ] File validati offline
- [ ] Encoding UTF-8 verificato
- [ ] Anteprima eseguita e approvata
- [ ] Strategia conflitti definita
- [ ] Utenti informati dell'operazione

### Durante Importazione
- [ ] Monitoraggio attivo del processo
- [ ] Log errori controllati in tempo reale
- [ ] Risorse sistema monitorate
- [ ] Backup procedure di rollback pronte

### Post-Importazione
- [ ] Conteggi record verificati
- [ ] Relazioni entità controllate
- [ ] Test funzionali eseguiti
- [ ] Utenti informati del completamento
- [ ] Documentazione operazione aggiornata

### Pre-Esportazione
- [ ] Spazio disco sufficiente verificato
- [ ] Formato export selezionato
- [ ] Filtri e opzioni configurati
- [ ] Orario ottimale pianificato

### Post-Esportazione
- [ ] File generati verificati
- [ ] Integrità backup controllata
- [ ] File archiviati correttamente
- [ ] Pulizia file temporanei eseguita

Questo documento fornisce una guida completa per l'utilizzo ottimale del sistema di importazione ed esportazione, garantendo operazioni sicure, efficienti e conformi alle best practices aziendali.