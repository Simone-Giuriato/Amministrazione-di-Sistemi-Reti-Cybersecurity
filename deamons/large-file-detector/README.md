# Large File Detector — Daemon con systemd

Esercizio pratico su demoni di sistema: script Python + unità di servizio systemd.

---

## Indice

1. [Cos'è un daemon](#1-cosè-un-daemon)
2. [Cos'è systemd](#2-cosè-systemd)
3. [Unit e unit file](#3-unit-e-unit-file)
4. [Struttura di un unit file `.service`](#4-struttura-di-un-unit-file-service)
5. [Dove mettere il file unit](#5-dove-mettere-il-file-unit)
6. [Comandi systemctl](#6-comandi-systemctl)
7. [Log con journalctl](#7-log-con-journalctl)
8. [Workflow completo](#8-workflow-completo)
9. [Lo script Python](#9-lo-script-python)
10. [Note pratiche dall'esercizio](#10-note-pratiche-dallesercizio)

---

## 1. Cos'è un daemon

Un **processo daemon** è un processo a lunga vita che:
- si avvia durante l'inizializzazione del sistema
- viene eseguito **in background** (nessun terminale di controllo — la colonna `TTY` mostra `?`)
- termina solo quando il sistema viene spento

I **daemon del kernel** (thread del kernel) hanno il nome racchiuso tra parentesi quadre, es. `[kthreadd]`, e hanno `PPID 0`. Sono parte del kernel stesso: non configurabili, non richiedono attenzione amministrativa.

I **daemon utente/di sistema** invece (es. `rsyslogd`, `systemd-journald`) sono processi normali avviati e gestiti da systemd.

```bash
$ ps -ef
PID  PPID  TTY   CMD
1    0     ?     /usr/lib/systemd/systemd     # systemd, unica eccezione con PID 1
2    0     ?     [kthreadd]                   # padre di tutti i daemon del kernel
700  1     ?     /usr/lib/systemd/systemd-logind
```

> `systemd` è l'**unica eccezione**: ha `PPID 0` ma `PID 1`, non è un daemon del kernel.

---

## 2. Cos'è systemd

`systemd` è il **gestore predefinito di sistema e servizi** per la maggior parte delle distribuzioni Linux.

- Viene eseguito con **PID 1** e avvia il resto del sistema
- Gestisce sia una **istanza di sistema** (PID 1, per tutti gli utenti) sia **istanze utente** (avviate al login, fermate al logout)
- Si controlla tramite `systemctl`

```bash
# istanza di sistema (richiede sudo)
systemctl status <unit>

# istanza utente (no sudo necessario)
systemctl --user status <unit>
```

> Per l'esercizio usiamo sempre `--user` perché nei lab non abbiamo privilegi sudo.

---

## 3. Unit e unit file

Una **unit** è un'entità gestita da systemd. Il suo comportamento è definito in un **unit file**:
- file di testo semplice in stile `.ini`
- il suffisso identifica il tipo (es. `.service`, `.target`, `.socket`)

**Tipi di unit rilevanti:**

| Tipo | Significato |
|------|-------------|
| `.service` | Rappresenta uno o più processi |
| `.target` | Rappresenta uno stato del sistema (es. modalità operativa) |

**Esempi di target:**

| Target | Modalità operativa |
|--------|-------------------|
| `rescue.target` | Utente singolo |
| `multi-user.target` | Server (tutti i servizi, no GUI) |
| `graphical.target` | Multi-utente con GUI |
| `default.target` | Target di avvio predefinito (per le unit utente) |
| `reboot.target` | Riavvio del sistema |

---

## 4. Struttura di un unit file `.service`

```ini
[Unit]
Description=Descrizione leggibile del servizio

[Service]
ExecStart=/path/assoluto/al/programma --argomenti
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target   # per unit utente
# WantedBy=multi-user.target  # per unit di sistema
```

### Sezione `[Unit]`

| Direttiva | Significato |
|-----------|-------------|
| `Description` | Descrizione leggibile |
| `After` | Avvia questa unit **dopo** quella indicata (ordinamento, non dipendenza) |
| `Requires` | Se l'unit richiesta fallisce, questa si ferma (dipendenza critica) |
| `Wants` | L'unit desiderata si avvia se disponibile, ma il fallimento non blocca (dipendenza opzionale) |
| `ConditionPathExists` | Avvia il servizio solo se il percorso indicato esiste |

> **Importante:** ordinamento (`After`) e dipendenza (`Requires`/`Wants`) sono **ortogonali**. `After=B` non implica `Requires=B` e viceversa.

### Sezione `[Service]`

| Direttiva | Significato |
|-----------|-------------|
| `ExecStart` | Comando usato per avviare il servizio — **deve essere un percorso assoluto** |
| `WorkingDirectory` | Directory di lavoro del processo (opzionale, ma utile) |
| `Environment` | Variabili d'ambiente per il processo |
| `Restart` | Politica di riavvio in caso di fallimento |
| `RestartSec` | Secondi di attesa prima di riavviare |

**Valori di `Restart`:**

| Valore | Quando riavvia |
|--------|---------------|
| `no` | Mai (default) |
| `on-failure` | Solo se il processo termina con errore |
| `always` | Sempre, anche se termina normalmente |

### Sezione `[Install]`

| Direttiva | Significato |
|-----------|-------------|
| `WantedBy` | Il sistema avvia questa unit quando raggiunge il target indicato (dipendenza opzionale al momento dell'installazione) |
| `RequiredBy` | Come `WantedBy` ma obbligatorio |

---

### Macro utili

| Macro | Espansione |
|-------|-----------|
| `%h` | Home directory dell'utente che esegue il servizio |

> **Attenzione:** `%h` non funziona sempre in `ExecStart`. Nel dubbio, usa sempre il **percorso assoluto**.

---

## 5. Dove mettere il file unit

systemd legge i file unit da diverse directory (in ordine di priorità decrescente):

| Directory | Significato |
|-----------|-------------|
| `/etc/systemd/system` | Unit di **sistema** create dall'amministratore ← priorità più alta |
| `/usr/lib/systemd/system` | Unit di sistema installate dal gestore dei pacchetti |
| `~/.config/systemd/user` | Unit **utente** create dall'utente ← **quella che usiamo** |
| `/etc/systemd/user` | Unit utente create dall'amministratore |
| `/usr/lib/systemd/user` | Unit utente installate dal gestore dei pacchetti |

### Per l'esercizio (unit utente, senza sudo)

```bash
# Creare la directory se non esiste
mkdir -p ~/.config/systemd/user

# Copiare il file unit
cp ~/large-file-detector/large-file-detector.service ~/.config/systemd/user/
```

---

## 6. Comandi systemctl

Aggiungere sempre **`--user`** per l'istanza utente.

### Comandi principali

| Comando | Significato |
|---------|-------------|
| `systemctl --user daemon-reload` | Ricaricare i file unit dopo creazione/modifica — **da eseguire sempre** |
| `systemctl --user list-unit-files --type=service` | Elencare i file unit installati |
| `systemctl --user list-units --type=service` | Elencare le unit attualmente in memoria |
| `systemctl --user status <unit>` | Stato della unit e log recenti |
| `systemctl --user start <unit>` | Avviare la unit subito |
| `systemctl --user stop <unit>` | Fermare la unit subito |
| `systemctl --user restart <unit>` | Riavviare la unit |
| `systemctl --user enable <unit>` | Abilitare l'avvio automatico al boot |
| `systemctl --user disable <unit>` | Disabilitare l'avvio automatico |
| `systemctl --user kill --signal=SIGKILL <unit>` | Terminare forzatamente (per testare il riavvio automatico) |

### Stati di un unit file (`STATE`)

| Stato | Significato |
|-------|-------------|
| `enabled` | Si avvierà all'avvio |
| `disabled` | Non si avvia all'avvio, ma può essere avviato manualmente |
| `masked` | Completamente disabilitato — non può essere avviato nemmeno manualmente |
| `static` | Nessuna sezione `[Install]`, avviato come dipendenza di un altro servizio |
| `bad` | Errore nell'unit file (es. sintassi errata) |

### Output di `systemctl status`

```
● large-file-detector.service - Large File Detector Service
     Loaded: loaded (/path/al/file; enabled; preset: enabled)
     Active: active (running) since ...
```

| Campo | Significato |
|-------|-------------|
| `Loaded: loaded` | Il file unit è stato letto correttamente |
| `enabled` / `disabled` | Se si avvia all'avvio |
| `Active: active (running)` | Il servizio è in esecuzione |
| `Active: inactive (dead)` | Il servizio è fermo |
| `Active: failed` | Il servizio è crashato |

---

## 7. Log con journalctl

`journalctl` interroga il **journal di systemd**. Aggiungere `--user` per leggere i log dell'istanza utente.

```bash
# Tutti i log del servizio
journalctl --user -u large-file-detector.service

# Log in tempo reale (follow)
journalctl --user -u large-file-detector.service -f

# Solo i log della sessione corrente
journalctl --user -u large-file-detector.service -b 0

# Ultimi N messaggi
journalctl --user -u large-file-detector.service -n 20

# Log dalla mezzanotte di oggi
journalctl --user --since=today

# Filtrare per severità (err e superiori)
journalctl --user -p err

# Elenco degli avvii del sistema
journalctl --list-boots
```

> **Nota:** aggiungere `Environment=PYTHONUNBUFFERED=1` nel `[Service]` fa sì che l'output di `print()` in Python appaia subito in journalctl senza buffering.

### Livelli di severità (dal più al meno urgente)

`emerg` → `alert` → `crit` → `err` → `warning` → `notice` → `info` → `debug`

---

## 8. Workflow completo

Questo è l'ordine corretto di operazioni ogni volta che si crea o modifica il file unit:

```bash
# 1. Copiare il file unit nella directory corretta
cp ~/large-file-detector/large-file-detector.service ~/.config/systemd/user/

# 2. (Opzionale) Verificare che il file sia presente
ls ~/.config/systemd/user/

# 3. Ricaricare systemd — OBBLIGATORIO dopo ogni modifica
systemctl --user daemon-reload

# 4. Verificare che systemd veda la unit
systemctl --user list-unit-files | grep large-file-detector

# 5. Abilitare il servizio (autostart al boot)
systemctl --user enable large-file-detector.service

# 6. Avviare il servizio subito
systemctl --user start large-file-detector.service

# 7. Controllare lo stato
systemctl --user status large-file-detector.service

# 8. Seguire i log in tempo reale
journalctl --user -u large-file-detector.service -f
```

### Per testare il riavvio automatico

```bash
# Terminare forzatamente il servizio
systemctl --user kill --signal=SIGKILL large-file-detector.service

# Verificare che systemd lo abbia riavviato
systemctl --user status large-file-detector.service
```

---

## 9. Lo script Python

### Struttura consigliata (`app.py`)

```python
import argparse
import os
import sys
import time

def walk(basepath, size, log_path):
    """Attraversamento ricorsivo della directory."""
    for filename in os.listdir(basepath):
        path = os.path.join(basepath, filename)
        if os.path.isfile(path):
            if os.path.getsize(path) >= size:
                with open(log_path, 'a') as f:
                    f.write(path + '\n')
        elif os.path.isdir(path):
            walk(path, size, log_path)

def main():
    # 1. Parsing degli argomenti
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--size',   required=True, type=int)
    parser.add_argument('--interval', required=True, type=int)
    parser.add_argument('--log',    required=True)
    args = parser.parse_args()

    # 2. Validazione
    if not os.path.isabs(args.target):
        sys.exit("--target deve essere un percorso assoluto")
    if not os.path.exists(args.target) or not os.path.isdir(args.target):
        sys.exit("--target non esiste o non è una directory")
    if args.size <= 0:
        sys.exit("--size deve essere un intero positivo")
    if args.interval <= 0:
        sys.exit("--interval deve essere un intero positivo")
    if not os.path.exists(args.log) or not os.path.isdir(args.log):
        sys.exit("--log non esiste o non è una directory")

    log_path = os.path.join(args.log, 'large-file-detector.log')

    # 3. Esecuzione periodica
    while True:
        walk(args.target, args.size, log_path)
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
```

### Argomenti richiesti

| Argomento | Tipo | Descrizione |
|-----------|------|-------------|
| `--target` | percorso assoluto | Directory da analizzare |
| `--size` | intero positivo | Dimensione minima in byte per segnalare un file |
| `--interval` | intero positivo | Secondi tra un controllo e il successivo |
| `--log` | percorso directory | Dove salvare `large-file-detector.log` |

### Funzioni Python utili

| Funzione | Uso |
|----------|-----|
| `os.path.isabs(path)` | Verifica che il percorso sia assoluto |
| `os.path.exists(path)` | Verifica che il percorso esista |
| `os.path.isdir(path)` | Verifica che sia una directory |
| `os.path.isfile(path)` | Verifica che sia un file |
| `os.path.getsize(path)` | Restituisce la dimensione del file in byte |
| `os.listdir(path)` | Elenca i contenuti di una directory |
| `os.path.join(a, b)` | Unisce componenti di percorso |
| `time.sleep(n)` | Attende `n` secondi |
| `open(path, 'a')` | Apre in modalità append |

---

## 10. Note pratiche dall'esercizio

- **`ExecStart` richiede percorso assoluto** dell'eseguibile: non si può scrivere solo `python3`, bisogna usare `/usr/bin/python3`. Per trovarlo: `which python3`.
- Se si specifica `WorkingDirectory`, in `ExecStart` si può usare il nome del file direttamente (es. `app.py`) invece del percorso assoluto.
- **`%h` non funziona sempre in `ExecStart`** — nel dubbio usare sempre il percorso assoluto (es. `/home/utente`).
- Dopo ogni modifica al file unit, eseguire sempre `systemctl --user daemon-reload` prima di `start`/`restart`.
- Stato `bad` in `list-unit-files` → c'è un errore di sintassi nel file unit.
- `enable` e `disable` si applicano solo alle unit con una sezione `[Install]`.
- Per le unit utente, usare `WantedBy=default.target` (non `multi-user.target`).

---

*Materiale teorico: note del corso di Amministrazione di Sistemi, Reti e Cybersecurity — Università di Ferrara.*
