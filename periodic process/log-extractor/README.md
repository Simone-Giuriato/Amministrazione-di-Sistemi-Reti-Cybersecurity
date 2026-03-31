# Processi Periodici — Teoria per l'Esame

---

## Indice
1. [Cos'è un processo periodico](#1-cosè-un-processo-periodico)
2. [Struttura di un timer systemd](#2-struttura-di-un-timer-systemd)
3. [Il file unit .timer](#3-il-file-unit-timer)
4. [Il file unit .service (attivato dal timer)](#4-il-file-unit-service-attivato-dal-timer)
5. [Espressioni temporali OnCalendar](#5-espressioni-temporali-oncalendar)
6. [Dove mettere i file unit](#6-dove-mettere-i-file-unit)
7. [Comandi systemctl per i timer](#7-comandi-systemctl-per-i-timer)
8. [Lo script Python](#8-lo-script-python)
9. [Workflow completo](#9-workflow-completo)
10. [Note pratiche dall'esercizio](#10-note-pratiche-dallesercizio)

---

## 1. Cos'è un processo periodico

È spesso utile avere un programma eseguito automaticamente secondo una pianificazione predefinita, senza intervento umano.

**Due strumenti principali in Linux:**
- `cron` — strumento tradizionale, ancora presente nella maggior parte delle distro
- `systemd timer` — alternativa moderna; alcune distro hanno abbandonato cron del tutto

Per l'esercizio usiamo sempre **systemd timer** con l'istanza utente (`--user`).

Un timer systemd è composto da **due unit file**:
- un `.timer` → descrive la pianificazione e quale service attivare
- un `.service` → descrive cosa eseguire

---

## 2. Struttura di un timer systemd

```
log-extractor.timer   ──attiva──►  log-extractor.service  ──esegue──►  python3 app.py
```

- Il timer **non esegue direttamente** nessun comando: si limita ad attivare il service
- Il service deve essere di tipo **oneshot** implicito (esegue il task e termina — non ha `Restart=`)
- Se timer e service hanno lo stesso nome base, la direttiva `Unit=` nel timer può essere omessa: systemd la ricava automaticamente

---

## 3. Il file unit `.timer`

```ini
# path: ~/.config/systemd/user/log-extractor.timer
#
# comando per abilitare il timer:  systemctl --user enable log-extractor.timer
# comando per avviare il timer:    systemctl --user start  log-extractor.timer

[Unit]
Description=Log extractor timer

[Timer]
Unit=log-extractor.service
OnCalendar=Mon,Fri 02:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Sezione `[Timer]` — direttive

| Direttiva | Significato |
|---|---|
| `Unit=` | Service da attivare. Se omesso, systemd cerca `stessonome.service` |
| `OnCalendar=` | Pianificazione a data/ora specifica (vedere §5) |
| `OnBootSec=` | Relativo al momento dell'avvio del sistema |
| `OnUnitActiveSec=` | Relativo all'ultima volta che la unit era attiva |
| `Persistent=true` | Se il sistema era spento all'orario previsto, esegue al riavvio |

### Sezione `[Install]`

| Direttiva | Valore per timer utente |
|---|---|
| `WantedBy=` | `timers.target` |

`timers.target` è un target dedicato che raccoglie tutti i timer e si attiva durante il boot. È preferibile a `default.target` per i timer.

---

## 4. Il file unit `.service` (attivato dal timer)

```ini
# path: ~/.config/systemd/user/log-extractor.service

[Unit]
Description=Log extractor service

[Service]
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=%h/log-extractor
ExecStart=/usr/bin/python3 app.py --path %h/logs --pattern ERROR
```

**Differenze rispetto a un service standalone:**
- **Nessuna sezione `[Install]`** → il service non si abilita da solo; è il timer che lo attiva
- Lo stato sarà `static` in `list-unit-files` (normale e corretto)
- Non usare `Restart=` per i service attivati da timer: il timer stesso gestisce la periodicità

### Sezione `[Service]` — direttive principali

| Direttiva | Significato |
|---|---|
| `ExecStart=` | Comando da eseguire — percorso assoluto dell'eseguibile |
| `WorkingDirectory=` | Directory di lavoro del processo |
| `Environment=VAR=val` | Imposta variabile d'ambiente |
| `PYTHONUNBUFFERED=1` | Forza Python a stampare subito l'output (visibile in `journalctl`) |

### Macro (specifier)

| Macro | Espansione |
|---|---|
| `%h` | Home directory dell'utente (`/home/utente`) |
| `%u` | Nome utente |

---

## 5. Espressioni temporali `OnCalendar`

### Sintassi generale
```
[GiornoSettimana] [Anno-]Mese-Giorno [Ora:Minuto[:Secondo]]
```

### Esempi pratici

| Espressione | Quando scatta |
|---|---|
| `Mon,Fri 02:00` | Lunedì e venerdì alle 02:00 |
| `Mon..Fri 09:00` | Da lunedì a venerdì alle 09:00 |
| `Sat,Sun 10:30` | Sabato e domenica alle 10:30 |
| `*-*-* 03:00` | Ogni giorno alle 03:00 |
| `weekly` | Ogni lunedì alle 00:00 |
| `monthly` | Il 1° del mese alle 00:00 |
| `*:0/10` | Ogni 10 minuti |
| `Mon..Fri *-7-4 12:30:00` | 4 luglio di ogni anno alle 12:30, solo lun–ven |

### Verifica della sintassi prima di distribuire

```bash
systemd-analyze calendar 'Mon,Fri 02:00' --iterations=3
```

Output esempio:
```
Original form: Mon,Fri 02:00
Normalized form: Mon,Fri *-*-* 02:00:00
Next elapse: Mon 2025-09-08 02:00:00 UTC
```

---

## 6. Dove mettere i file unit

Per l'esercizio (istanza utente, senza sudo):

```
~/.config/systemd/user/
```

Se la directory non esiste:
```bash
mkdir -p ~/.config/systemd/user
```

Copia di entrambi i file:
```bash
cp ~/log-extractor/log-extractor.service ~/.config/systemd/user/
cp ~/log-extractor/log-extractor.timer   ~/.config/systemd/user/
```

---

## 7. Comandi systemctl per i timer

Aggiungere sempre `--user` per l'istanza utente.

### Comandi principali

| Comando | Significato |
|---|---|
| `systemctl --user daemon-reload` | Ricaricare i file unit dopo creazione/modifica — **sempre obbligatorio** |
| `systemctl --user list-unit-files` | Elencare le unit installate (con stato) |
| `systemctl --user list-timers` | Elencare i timer attivi e quando scatteranno |
| `systemctl --user status <unit>` | Stato della unit e log recenti |
| `systemctl --user start <unit>` | Avviare subito |
| `systemctl --user stop <unit>` | Fermare |
| `systemctl --user enable <unit>` | Abilitare l'avvio automatico al login |
| `systemctl --user disable <unit>` | Disabilitare l'avvio automatico |

### Stati di un unit file

| Stato | Significato |
|---|---|
| `enabled` | Si avvierà all'avvio/login |
| `disabled` | Non si avvia automaticamente |
| `static` | Nessuna sezione `[Install]` — attivato come dipendenza (es. dal timer) |
| `bad` | Errore di sintassi nel file unit |

### Output di `list-timers`

```
NEXT                         LEFT     LAST                         PASSED   UNIT                    ACTIVATES
Mon 2025-09-08 02:00:00 UTC  6h left  Fri 2025-09-05 02:00:00 UTC  2 days   log-extractor.timer     log-extractor.service
```

### Log con journalctl

```bash
# tutti i log del service
journalctl --user -u log-extractor.service

# log in tempo reale
journalctl --user -u log-extractor.service -f
```

---

## 8. Lo script Python

### Struttura consigliata (esercizio log-extractor)

```python
import argparse
import os
import sys

def find(path, pattern):
    """Legge il file e restituisce le righe che contengono pattern."""
    with open(path, "r") as f:
        righe = f.readlines()
    return [riga for riga in righe if pattern in riga]

def writeFile(backup_file, righe):
    """Scrive le righe filtrate nel file di backup."""
    with open(backup_file, "w") as f:
        f.writelines(righe)

def walk(log_dir, backup_dir, pattern):
    """Esplora ricorsivamente log_dir e salva le righe filtrate in backup_dir."""
    for filename in os.listdir(log_dir):
        path = os.path.join(log_dir, filename)
        if os.path.isfile(path) and filename.endswith(".log"):
            righe = find(path, pattern)
            print(f"Trovate {len(righe)} righe in {path}")
            backup_file = os.path.join(backup_dir, filename)
            writeFile(backup_file, righe)
            print(f"Scritte {len(righe)} righe in {backup_file}")
        elif os.path.isdir(path):
            walk(path, backup_dir, pattern)   # ricorsione

def main():
    # 1. Parsing degli argomenti
    parser = argparse.ArgumentParser(description='log-extractor')
    parser.add_argument("--path",    type=str, required=True,
                        help="percorso assoluto directory da analizzare")
    parser.add_argument("--pattern", type=str, required=True,
                        help="stringa da cercare nei file .log")
    args = parser.parse_args()

    # 2. Validazione
    if not os.path.isabs(args.path):
        print(f"errore: {args.path} non è un path assoluto", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.path):
        print(f"errore: {args.path} non esiste", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.path):
        print(f"errore: {args.path} non è una directory", file=sys.stderr)
        sys.exit(1)
    if not args.pattern:
        print("errore: il pattern non deve essere vuoto", file=sys.stderr)
        sys.exit(1)

    # 3. Assicurarsi che la directory di backup esista
    backup_path = os.path.expanduser("~/backup")
    os.makedirs(backup_path, exist_ok=True)

    # 4. Scansione ricorsiva
    walk(args.path, backup_path, args.pattern)

if __name__ == "__main__":
    main()
```

### Funzioni `os` essenziali

| Funzione | Uso |
|---|---|
| `os.path.isabs(path)` | Verifica che il percorso sia assoluto |
| `os.path.exists(path)` | Verifica che il percorso esista |
| `os.path.isdir(path)` | Verifica che sia una directory |
| `os.path.isfile(path)` | Verifica che sia un file |
| `os.path.join(a, b)` | Costruisce `a/b` |
| `os.listdir(path)` | Lista i contenuti di una directory |
| `os.path.expanduser("~")` | Espande `~` nella home reale |
| `os.makedirs(path, exist_ok=True)` | Crea directory (e intermedie); no errore se esiste già |

---

## 9. Workflow completo

Questo è l'ordine corretto ogni volta che si crea o modifica un file unit.

```bash
# 1. Creare la directory se non esiste
mkdir -p ~/.config/systemd/user

# 2. Copiare i file unit
cp ~/log-extractor/log-extractor.service ~/.config/systemd/user/
cp ~/log-extractor/log-extractor.timer   ~/.config/systemd/user/

# 3. Ricaricare systemd — OBBLIGATORIO dopo ogni modifica
systemctl --user daemon-reload

# 4. Verificare che systemd veda le unit
systemctl --user list-unit-files | grep log-extractor
# service → static (corretto, non ha [Install])
# timer   → disabled (da abilitare)

# 5. Avviare e testare il service manualmente
systemctl --user start log-extractor.service
systemctl --user status log-extractor.service
journalctl --user -u log-extractor.service

# 6. Avviare il timer
systemctl --user start log-extractor.timer
systemctl --user status log-extractor.timer

# 7. Verificare il prossimo scatto
systemctl --user list-timers

# 8. Abilitare il timer (avvio automatico al login)
systemctl --user enable log-extractor.timer

# 9. Riavviare il sistema e verificare che il timer sopravviva
systemctl --user status log-extractor.timer
```

---

## 10. Note pratiche dall'esercizio

- **`ExecStart` richiede il percorso assoluto** dell'eseguibile: non `python3` ma `/usr/bin/python3`. Per trovarlo: `which python3`.
- Se si specifica `WorkingDirectory=%h/log-extractor`, in `ExecStart` si può usare solo `app.py` invece del percorso assoluto.
- **`%h` in `ExecStart` non funziona sempre** — nel dubbio, usare il percorso assoluto (`/home/utente/...`).
- Dopo ogni modifica al file unit, eseguire **sempre** `daemon-reload` prima di `start`/`restart`.
- Il service attivato da un timer ha stato **`static`** in `list-unit-files`: è normale e corretto.
- `enable` e `disable` si applicano solo alle unit con una sezione `[Install]` → solo il **timer** va abilitato, non il service.
- `Persistent=true` nel timer è utile per non perdere esecuzioni se il sistema era spento all'orario previsto.
- **`PYTHONUNBUFFERED=1`** è necessario affinché l'output di `print()` appaia immediatamente in `journalctl`.
- Per verificare la sintassi di un'espressione `OnCalendar` **prima** di distribuire il timer: `systemd-analyze calendar 'espressione'`.
