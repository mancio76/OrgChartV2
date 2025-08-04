# Guida Utente - Sistema di Gestione Temi

## Panoramica

Il Sistema di Gestione Temi permette di personalizzare l'aspetto visivo delle unità organizzative nell'organigramma. Attraverso un'interfaccia intuitiva, è possibile creare, modificare e assegnare temi personalizzati per diversi tipi di unità.

## Accesso al Sistema

Per accedere alla gestione temi:

1. Accedi all'applicazione con credenziali amministrative
2. Naviga nel menu principale e seleziona "Gestione Temi"
3. Verrai reindirizzato alla dashboard dei temi

## Gestione dei Temi

### Visualizzazione Temi Esistenti

La pagina principale mostra tutti i temi disponibili con:

- **Nome del tema**: Identificativo univoco
- **Descrizione**: Breve descrizione del tema
- **Anteprima visiva**: Esempio di come appare il tema
- **Statistiche di utilizzo**: Quanti tipi di unità utilizzano il tema
- **Stato**: Attivo/Inattivo

### Creazione di un Nuovo Tema

1. **Clicca su "Nuovo Tema"**
   - Si aprirà il modulo di creazione tema

2. **Compila i campi obbligatori:**
   - **Nome**: Nome univoco per il tema (es. "Tema Direzione")
   - **Descrizione**: Descrizione dettagliata del tema
   - **Etichetta Display**: Come apparirà nell'organigramma (es. "Direzione")
   - **Etichetta Plurale**: Forma plurale dell'etichetta (es. "Direzioni")

3. **Configura le proprietà visive:**
   - **Icona**: Seleziona un'icona Bootstrap (es. "building", "diagram-2")
   - **Emoji Fallback**: Emoji da usare come fallback (es. "🏢")
   - **Colore Primario**: Colore principale del tema (formato hex: #0d6efd)
   - **Colore Secondario**: Colore di sfondo (formato hex: #f8f9ff)
   - **Colore Testo**: Colore del testo (formato hex: #0d6efd)

4. **Configura le proprietà del bordo:**
   - **Larghezza Bordo**: Spessore in pixel (1-10)
   - **Stile Bordo**: solid, dashed, dotted
   - **Colore Bordo**: Se diverso dal colore primario

5. **Configura gli effetti:**
   - **Colore Ombra Hover**: Colore dell'ombra al passaggio del mouse
   - **Intensità Ombra**: Valore da 0.1 a 1.0

6. **Anteprima in tempo reale:**
   - L'anteprima si aggiorna automaticamente mentre modifichi i valori
   - Verifica che i colori siano leggibili e accessibili

7. **Salva il tema:**
   - Clicca "Salva" per creare il tema
   - Il sistema validerà automaticamente i dati inseriti

### Modifica di un Tema Esistente

1. **Seleziona il tema da modificare:**
   - Clicca sull'icona "Modifica" accanto al tema desiderato

2. **Modifica i campi necessari:**
   - Tutti i campi sono modificabili eccetto l'ID
   - L'anteprima si aggiorna in tempo reale

3. **Attenzione alle modifiche:**
   - Le modifiche si applicano immediatamente a tutti i tipi di unità che usano il tema
   - Verifica l'impatto prima di salvare

4. **Salva le modifiche:**
   - Clicca "Salva Modifiche"
   - Il sistema aggiornerà automaticamente l'organigramma

### Clonazione di un Tema

Per creare un tema simile a uno esistente:

1. **Clicca su "Clona" accanto al tema desiderato**
2. **Inserisci il nuovo nome** per il tema clonato
3. **Modifica le proprietà** secondo necessità
4. **Salva il nuovo tema**

### Eliminazione di un Tema

⚠️ **Attenzione**: L'eliminazione di un tema può influenzare l'organigramma.

1. **Verifica l'utilizzo:**
   - Controlla quanti tipi di unità utilizzano il tema
   - Se in uso, considera di riassegnare prima dell'eliminazione

2. **Elimina il tema:**
   - Clicca sull'icona "Elimina"
   - Conferma l'operazione
   - I tipi di unità orfani verranno assegnati al tema predefinito

## Assegnazione Temi ai Tipi di Unità

### Assegnazione Singola

1. **Vai alla gestione Tipi di Unità**
2. **Modifica il tipo di unità desiderato**
3. **Seleziona il tema** dal menu a tendina
4. **Salva le modifiche**

### Assegnazione Multipla

1. **Usa l'interfaccia "Assegna Temi"**
2. **Seleziona più tipi di unità** dalla lista
3. **Scegli il tema** da applicare
4. **Conferma l'assegnazione**

## Monitoraggio e Statistiche

### Dashboard Analitiche

La dashboard fornisce:

- **Utilizzo per tema**: Quanti tipi di unità usano ogni tema
- **Temi più popolari**: Classifica dei temi più utilizzati
- **Temi inutilizzati**: Temi creati ma non assegnati
- **Impatto delle modifiche**: Analisi dell'impatto delle modifiche recenti

### Report di Utilizzo

Genera report dettagliati su:

- **Distribuzione temi**: Come sono distribuiti i temi nell'organizzazione
- **Cronologia modifiche**: Storico delle modifiche ai temi
- **Analisi impatto**: Effetti delle modifiche sui tipi di unità

## Validazione e Controlli di Qualità

### Validazione Automatica

Il sistema valida automaticamente:

- **Formati colore**: Verifica che i colori siano in formato hex valido
- **Contrasto**: Controlla che il contrasto sia sufficiente per l'accessibilità
- **Icone**: Verifica che le icone Bootstrap esistano
- **Nomi univoci**: Impedisce la creazione di temi con nomi duplicati

### Controlli di Accessibilità

- **Contrasto colori**: Minimo 4.5:1 per testo normale, 3:1 per testo grande
- **Modalità alto contrasto**: Supporto automatico per utenti con esigenze speciali
- **Indicatori visivi**: Oltre al colore, usa icone e forme per distinguere elementi

## Risoluzione Problemi Comuni

### Tema non visualizzato correttamente

1. **Verifica la cache del browser**: Forza il refresh (Ctrl+F5)
2. **Controlla la validità dei colori**: Assicurati che siano in formato hex
3. **Verifica l'assegnazione**: Controlla che il tema sia assegnato al tipo di unità

### Colori non accessibili

1. **Usa il validatore di contrasto integrato**
2. **Testa con utenti reali** o strumenti di accessibilità
3. **Considera la modalità alto contrasto**

### Prestazioni lente

1. **Riduci il numero di temi attivi** se eccessivo
2. **Ottimizza i colori** evitando gradienti complessi
3. **Contatta l'amministratore** per ottimizzazioni del sistema

## Best Practices

### Creazione Temi

- **Usa nomi descrittivi**: "Tema Direzione Generale" invece di "Tema1"
- **Mantieni coerenza**: Usa palette di colori coerenti
- **Testa l'accessibilità**: Verifica sempre il contrasto
- **Documenta le scelte**: Aggiungi descrizioni dettagliate

### Gestione Temi

- **Pianifica le modifiche**: Le modifiche ai temi si applicano immediatamente
- **Backup prima di modifiche importanti**: Esporta la configurazione
- **Monitora l'utilizzo**: Rimuovi temi inutilizzati periodicamente
- **Forma gli utenti**: Assicurati che tutti conoscano il sistema

### Manutenzione

- **Revisione periodica**: Controlla i temi ogni 6 mesi
- **Aggiornamento icone**: Mantieni le icone aggiornate con Bootstrap
- **Feedback utenti**: Raccogli feedback sull'usabilità dei temi
- **Documentazione aggiornata**: Mantieni questa guida aggiornata

## Supporto e Assistenza

Per assistenza tecnica:

1. **Consulta questa guida** per problemi comuni
2. **Controlla i log di sistema** per errori tecnici
3. **Contatta l'amministratore di sistema** per problemi complessi
4. **Segnala bug** attraverso il sistema di ticketing aziendale

---

*Ultima modifica: Gennaio 2025*
*Versione: 1.0*