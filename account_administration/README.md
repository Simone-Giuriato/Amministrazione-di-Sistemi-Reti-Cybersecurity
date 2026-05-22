# Guida: Amministrazione degli account con `sudo`

> Questa guida copre i due esercizi di **account administration**:
> 1. L'esercizio del file `account-administration.pdf` (host: `web01`, `web02`, `db01`, `db02`)
> 2. Il secondo esercizio del `mock-exam.md` (host: `cache01`, `cache02`, `cache03`, `gateway01`)

---

## Indice

- [1. Teoria: cos'è `sudo` e come funziona](#1-teoria-cosè-sudo-e-come-funziona)
- [2. Teoria: struttura di un file sudoers](#2-teoria-struttura-di-un-file-sudoers)
  - [2.1 Alias](#21-alias)
  - [2.2 Righe di permesso](#22-righe-di-permesso)
  - [2.3 Parole chiave speciali](#23-parole-chiave-speciali)
- [3. Teoria: dove mettere il file](#3-teoria-dove-mettere-il-file)
- [4. Teoria: come verificare la sintassi](#4-teoria-come-verificare-la-sintassi)
- [5. Esercizio 1 — account-administration.pdf](#5-esercizio-1--account-administrationpdf)
  - [5.1 Analisi delle regole](#51-analisi-delle-regole)
  - [5.2 Soluzione commentata](#52-soluzione-commentata)
- [6. Esercizio 2 — mock-exam.md](#6-esercizio-2--mock-exammd)
  - [6.1 Analisi delle regole](#61-analisi-delle-regole)
  - [6.2 Soluzione commentata](#62-soluzione-commentata)
- [7. Come testare con Podman](#7-come-testare-con-podman)
- [8. Errori comuni](#8-errori-comuni)

---

## 1. Teoria: cos'è `sudo` e come funziona

`sudo` ("superuser do") è un comando che permette a un utente normale di eseguire comandi come
un altro utente (di solito `root`), **solo se esplicitamente autorizzato** da un amministratore.

Senza `sudo`, per fare operazioni privilegiate dovresti usare `su -` (diventare root). `sudo` è
preferibile perché:

- ogni azione viene loggata
- ogni utente può avere permessi granulari (non tutto o niente)
- non è necessario condividere la password di `root`

Quando esegui `sudo <comando>`, il sistema consulta i file di configurazione (`/etc/sudoers` e i file
in `/etc/sudoers.d/`) per decidere se quell'utente, su quell'host, può eseguire quel comando.

---

## 2. Teoria: struttura di un file sudoers

Un file sudoers ha due tipi di contenuto: **alias** e **righe di permesso**.

### 2.1 Alias

Gli alias sono "scorciatoie" per evitare di ripetere liste lunghe. Esistono quattro tipi:

| Tipo | Sintassi | Cosa rappresenta |
|------|----------|-----------------|
| `Host_Alias` | `Host_Alias NOME = host1, host2` | Un insieme di hostname |
| `Cmnd_Alias` | `Cmnd_Alias NOME = /percorso/cmd1, /percorso/cmd2` | Un insieme di comandi |
| `User_Alias` | `User_Alias NOME = utente1, utente2` | Un insieme di utenti |
| `Runas_Alias` | `Runas_Alias NOME = utente1, utente2` | Un insieme di utenti "target" |

> **Convenzione:** i nomi degli alias sono sempre in **MAIUSCOLO**.

### 2.2 Righe di permesso

La forma generale è:

```
<chi>    <dove> = (<come_chi>) [NOPASSWD:] <cosa>
```

| Campo | Significato | Esempio |
|-------|-------------|---------|
| `<chi>` | utente o `%gruppo` | `alice`, `%ops` |
| `<dove>` | hostname o alias | `ALL`, `WEB`, `db01` |
| `(<come_chi>)` | utente target (opzionale, default: `root`) | `(ALL)`, `(nobody)`, omesso |
| `NOPASSWD:` | esegue senza richiedere password | facoltativo |
| `<cosa>` | comando/i o alias | `ALL`, `SHELLS`, `/usr/bin/id` |

> **Attenzione:** il campo `(<come_chi>)` è opzionale. Se omesso, il target è `root` implicitamente.
> Esempio: `%ops CACHE = NETMGM` significa "il gruppo ops può eseguire NETMGM **come root** su CACHE".

### 2.3 Parole chiave speciali

| Keyword | Significato |
|---------|-------------|
| `ALL` | Tutto (utenti, host, comandi) |
| `NOPASSWD:` | Il blocco di comandi che segue non richiede password |
| `!COMANDO` | Nega un comando (il comando è **vietato**) |
| `%gruppo` | Il `%` indica un gruppo Unix, non un utente |

> **Nota su `!` (negazione):** la negazione in sudo è fragile — un utente smaliziato può aggirarla.
> Non usarla come meccanismo di sicurezza critico, ma è comunque richiesta negli esercizi.

---

## 3. Teoria: dove mettere il file

Il file principale è `/etc/sudoers`. **Non modificarlo mai direttamente.**

La directory `/etc/sudoers.d/` è pensata per file aggiuntivi: ogni file al suo interno viene incluso
automaticamente in ordine lessicografico. In entrambi gli esercizi il file va in:

```
/etc/sudoers.d/local
```

> **Permessi obbligatori:** il file deve essere di proprietà di `root:root` e avere permessi `0440`
> (leggibile da root e dal gruppo root, non scrivibile da nessuno). `sudo` rifiuta file con
> permessi troppo permissivi.

```bash
sudo chown root:root /etc/sudoers.d/local
sudo chmod 0440 /etc/sudoers.d/local
```

---

## 4. Teoria: come verificare la sintassi

Prima di installare il file, verifica sempre la sintassi con `visudo`:

```bash
# Controlla un file senza installarlo né aprire un editor
visudo -c -f /percorso/del/tuo/file

# Output atteso se tutto va bene:
# /percorso/del/tuo/file: parsed OK
```

> Se c'è un errore, `visudo` indica la riga problematica. Un file sudoers con sintassi errata
> può bloccare completamente l'accesso sudo sull'intero sistema.

---

## 5. Esercizio 1 — account-administration.pdf

### Scenario

- **Host:** `web01`, `web02`, `db01`, `db02`
- **Utenti e gruppi:**

  | Utente | Gruppo primario | Gruppi aggiuntivi |
  |--------|----------------|-------------------|
  | `alice` | `alice` | — |
  | `bob` | `bob` | — |
  | `carol` | `carol` | `ops` |
  | `dave` | `dave` | `devs` |

### 5.1 Analisi delle regole

Leggi ogni regola e traducila mentalmente prima di scrivere il codice.

**Alias richiesti:**

- `Host_Alias WEB = web01, web02` → raggruppa i due web server
- `Host_Alias DB = db01, db02` → raggruppa i due database server
- `Cmnd_Alias SHELLS = /bin/sh, /bin/dash, /bin/bash` → le shell interattive
- `Cmnd_Alias USERMGM = /usr/sbin/useradd, /usr/sbin/userdel, /usr/sbin/usermod` → gestione utenti
- `Cmnd_Alias PKGINFO = /usr/bin/dpkg` → informazioni pacchetti

**Permessi — traduzione riga per riga:**

| Regola testuale | Traduzione sudoers |
|-----------------|--------------------|
| `alice` può eseguire qualsiasi comando come qualsiasi utente su qualsiasi host | `alice ALL = (ALL) ALL` |
| `bob` può eseguire qualsiasi comando eccetto SHELLS | `bob ALL = (ALL) ALL, !SHELLS` |
| `%ops` può eseguire USERMGM come `root` su WEB | `%ops WEB = USERMGM` |
| `%devs` può eseguire PKGINFO come `root` su DB, senza password | `%devs DB = NOPASSWD: PKGINFO` |
| `carol` può eseguire `/usr/bin/cat /etc/shadow` come `root` su qualsiasi host, senza password | `carol ALL = NOPASSWD: /usr/bin/cat /etc/shadow` |
| `dave` può eseguire `/usr/bin/id` come `nobody` su DB | `dave DB = (nobody) /usr/bin/id` |
| `%ops, %devs` può eseguire `/usr/sbin/reboot` come `root` su qualsiasi host, senza password | `%ops, %devs ALL = NOPASSWD: /usr/sbin/reboot` |

> **Nota su `%ops WEB = USERMGM`:** non c'è `(ALL)` perché il target è `root` di default.
> Scrivere `(root)` esplicito sarebbe equivalente ma ridondante.

> **Nota su `carol`:** il comando include un argomento (`/etc/shadow`). In sudoers, quando
> il percorso del comando è specificato con argomenti, viene verificato esattamente così.
> `carol` NON potrà eseguire `/usr/bin/cat /etc/passwd` — solo `/usr/bin/cat /etc/shadow`.

### 5.2 Soluzione commentata

```sudoers
# nome e cognome: [tuo nome]
# matricola: [tua matricola]
#
# path: /etc/sudoers.d/local

# --- ALIAS HOST ---
# Raggruppa i web server in un unico alias
Host_Alias  WEB = web01, web02

# Raggruppa i database server in un unico alias
Host_Alias  DB = db01, db02

# --- ALIAS COMANDI ---
# Le shell interattive (da vietare a bob)
Cmnd_Alias  SHELLS  = /bin/sh, /bin/dash, /bin/bash

# Comandi per la gestione degli utenti di sistema
Cmnd_Alias  USERMGM = /usr/sbin/useradd, /usr/sbin/userdel, /usr/sbin/usermod

# Comando per interrogare i pacchetti installati
Cmnd_Alias  PKGINFO = /usr/bin/dpkg

# --- PERMESSI ---

# alice: accesso totale su tutti gli host come qualsiasi utente
alice       ALL     = (ALL) ALL

# bob: accesso totale, MA non può aprire shell interattive
# Il ! nega SHELLS; il resto (ALL ALL) è permesso
bob         ALL     = (ALL) ALL, !SHELLS

# Il gruppo ops può gestire utenti (USERMGM) come root sui web server
# Nessun (runas) esplicito = root di default; richiede password
%ops        WEB     = USERMGM

# Il gruppo devs può interrogare i pacchetti su DB come root, senza password
%devs       DB      = NOPASSWD: PKGINFO

# carol può leggere /etc/shadow su qualsiasi host senza password
# ATTENZIONE: solo questo comando esatto, con questo argomento esatto
carol       ALL     = NOPASSWD: /usr/bin/cat /etc/shadow

# dave può eseguire `id` come utente nobody (non root!) sui DB
# Utile per verificare l'identità in un contesto a basso privilegio
dave        DB      = (nobody) /usr/bin/id

# ops e audit possono riavviare qualsiasi host senza password
# La virgola nella lista "chi" unisce due gruppi nella stessa regola
%ops, %devs ALL     = NOPASSWD: /usr/sbin/reboot
```

---

## 6. Esercizio 2 — mock-exam.md

### Scenario

- **Host:** `cache01`, `cache02`, `cache03`, `gateway01`
- **Utenti e gruppi:**

  | Utente | Gruppo primario | Gruppi aggiuntivi |
  |--------|----------------|-------------------|
  | `liam` | `liam` | — |
  | `mia` | `mia` | `ops` |
  | `noah` | `noah` | `ops` |
  | `olivia` | `olivia` | `audit` |

### 6.1 Analisi delle regole

**Alias richiesti:**

- `Host_Alias CACHE = cache01, cache02, cache03` → raggruppa i cache server
- `Cmnd_Alias SHELLS = /bin/sh, /bin/dash, /bin/bash`
- `Cmnd_Alias NETMGM = /usr/bin/ss, /usr/bin/ip` → strumenti di rete
- `Cmnd_Alias BACKUP = /usr/bin/rsync, /usr/bin/tar` → strumenti di backup

**Permessi — traduzione riga per riga:**

| Regola testuale | Traduzione sudoers |
|-----------------|--------------------|
| `liam` può eseguire qualsiasi comando come qualsiasi utente su qualsiasi host | `liam ALL = (ALL) ALL` |
| `mia` può eseguire qualsiasi comando eccetto SHELLS | `mia ALL = (ALL) ALL, !SHELLS` |
| `%ops` può eseguire NETMGM come `root` su CACHE | `%ops CACHE = NETMGM` |
| `%audit` può eseguire BACKUP come `root` su `gateway01`, senza password | `%audit gateway01 = NOPASSWD: BACKUP` |
| `noah` può eseguire `/usr/bin/tail -f /var/log/syslog` come `root` su qualsiasi host, senza password | `noah ALL = NOPASSWD: /usr/bin/tail -f /var/log/syslog` |
| `olivia` può eseguire `/usr/bin/id` come `mia` su CACHE | `olivia CACHE = (mia) /usr/bin/id` |
| `%ops, %audit` può eseguire `/usr/sbin/reboot` come `root` su qualsiasi host, senza password | `%ops, %audit ALL = NOPASSWD: /usr/sbin/reboot` |

> **Nota su `noah`:** il comando include l'argomento `-f /var/log/syslog`. Questo significa che
> `noah` può eseguire **solo** `tail -f /var/log/syslog`, non `tail` con altri argomenti o su
> altri file.

> **Nota su `olivia`:** il runas è `(mia)`, non `(root)`. `olivia` non ottiene privilegi di
> root, ma può "fingersi" l'utente `mia`. Utile per audit: può verificare cosa vede `mia`
> senza conoscerne la password.

> **Confronto con l'esercizio 1:** la struttura è identica, cambiano solo gli alias e gli utenti.
> Riconoscere questo pattern è la chiave per risolvere qualsiasi esercizio di questo tipo.

### 6.2 Soluzione commentata

```sudoers
# nome e cognome: [tuo nome]
# matricola: [tua matricola]
#
# path: /etc/sudoers.d/local

# --- ALIAS HOST ---
# I tre cache server (gateway01 non è in questo alias: ha regole proprie)
Host_Alias  CACHE = cache01, cache02, cache03

# --- ALIAS COMANDI ---
# Shell interattive (da negare a mia)
Cmnd_Alias  SHELLS  = /bin/sh, /bin/dash, /bin/bash

# Strumenti di monitoraggio/configurazione della rete
Cmnd_Alias  NETMGM  = /usr/bin/ss, /usr/bin/ip

# Strumenti di backup e archiviazione
Cmnd_Alias  BACKUP  = /usr/bin/rsync, /usr/bin/tar

# --- PERMESSI ---

# liam: amministratore totale, nessuna restrizione
liam            ALL       = (ALL) ALL

# mia: tutto permesso tranne aprire shell interattive
mia             ALL       = (ALL) ALL, !SHELLS

# Il gruppo ops può monitorare la rete sui cache server (come root, con password)
%ops            CACHE     = NETMGM

# Il gruppo audit può fare backup dal gateway (come root, senza password)
# Solo su gateway01, non su CACHE
%audit          gateway01 = NOPASSWD: BACKUP

# noah può seguire il log di sistema su qualsiasi host, senza password
# Comando con argomenti fissi: NON può usare tail su altri file
noah            ALL       = NOPASSWD: /usr/bin/tail -f /var/log/syslog

# olivia può eseguire `id` come l'utente mia (non root!) sui cache server
# Permette di verificare l'identità/gruppi di mia senza la sua password
olivia          CACHE     = (mia) /usr/bin/id

# ops e audit possono riavviare qualsiasi host senza password
%ops, %audit    ALL       = NOPASSWD: /usr/sbin/reboot
```

---

## 7. Come testare con Podman

Il workflow di test consigliato usa container per simulare gli host reali.

### Step 1 — Scarica l'immagine

```bash
podman pull fglmtt/admin
```

### Step 2 — Avvia i container (uno per hostname)

```bash
# Esempio per l'esercizio 2 (mock-exam): avvia tutti e 4 gli host
podman run -d --name cache01 --hostname cache01 \
    -v /percorso/tuo/sudoers:/tmp/local:ro \
    fglmtt/admin sleep infinity

podman run -d --name cache02 --hostname cache02 \
    -v /percorso/tuo/sudoers:/tmp/local:ro \
    fglmtt/admin sleep infinity

podman run -d --name cache03 --hostname cache03 \
    -v /percorso/tuo/sudoers:/tmp/local:ro \
    fglmtt/admin sleep infinity

podman run -d --name gateway01 --hostname gateway01 \
    -v /percorso/tuo/sudoers:/tmp/local:ro \
    fglmtt/admin sleep infinity
```

### Step 3 — Entra in un container e configura

```bash
podman exec -it cache01 bash
```

Una volta dentro:

```bash
# Installa il file sudoers
sudo cp /tmp/local /etc/sudoers.d/local
sudo chmod 0440 /etc/sudoers.d/local

# Verifica la sintassi nell'ambiente reale
visudo -c

# Crea gli utenti e i gruppi necessari
sudo groupadd ops
sudo groupadd audit

sudo useradd -m liam
sudo useradd -m mia
sudo useradd -m noah
sudo useradd -m olivia

# Imposta una password (necessaria per su -l)
sudo passwd liam     # digita una password di test

# Aggiungi ai gruppi supplementari
sudo usermod -aG ops mia
sudo usermod -aG ops noah
sudo usermod -aG audit olivia
```

### Step 4 — Verifica le regole

```bash
# Diventa un utente e controlla le sue regole
su -l noah
sudo -l          # mostra i permessi di noah sull'host corrente

# Prova un comando consentito
sudo /usr/bin/tail -f /var/log/syslog

# Prova un comando NON consentito (deve essere rifiutato)
sudo /usr/bin/tail -f /etc/passwd
```

> **Suggerimento:** tra un test e l'altro, esegui `sudo -k` per cancellare le credenziali
> in cache di sudo. Così potrai vedere il comportamento della richiesta di password ogni volta.

---

## 8. Errori comuni

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `sudo: /etc/sudoers.d/local is world writable` | Permessi troppo aperti | `chmod 0440 /etc/sudoers.d/local` |
| `sudo: /etc/sudoers.d/local is owned by uid X, not uid 0` | Proprietario sbagliato | `chown root:root /etc/sudoers.d/local` |
| `parse error in /etc/sudoers.d/local near line N` | Errore di sintassi | Controlla la riga N con `visudo -c -f` |
| La regola non compare in `sudo -l` | Hostname del container sbagliato | Verifica con `hostname`; deve corrispondere all'alias |
| `!SHELLS` non funziona come atteso | L'utente usa un percorso alternativo | La negazione è fragile per design in sudo |
| `%gruppo` non riconosciuto | Il gruppo non esiste sul sistema | Crea il gruppo con `groupadd` prima di testare |

---

*Guida basata su: `user-management.pdf`, `account-administration.pdf`, `mock-exam.md`*
