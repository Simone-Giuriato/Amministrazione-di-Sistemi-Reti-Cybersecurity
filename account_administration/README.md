# Guida: Amministrazione degli account con `sudo`

> Questa guida copre i due esercizi di **account administration**:

---

## Indice

- [1. Teoria: cos'è `sudo` e come funziona](#1-teoria-cosè-sudo-e-come-funziona)
- [2. Teoria: struttura di un file sudoers](#2-teoria-struttura-di-un-file-sudoers)
  - [2.1 Alias](#21-alias)
  - [2.2 Righe di permesso](#22-righe-di-permesso)
  - [2.3 Parole chiave speciali](#23-parole-chiave-speciali)
- [3. Teoria: dove mettere il file](#3-teoria-dove-mettere-il-file)
- [4. Teoria: come verificare la sintassi](#4-teoria-come-verificare-la-sintassi)
- [5. Come testare con Podman](#7-come-testare-con-podman)
- [6. Errori comuni](#8-errori-comuni)

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
<chi>    <dove> = (<utente_target[:gruppo_target]>) [NOPASSWD:] <cosa>


```
ES: qualsiasi comando come qualsiasi utente/gruppo su qualsiasi host--> alice ALL = (ALL:ALL) ALL

ATTENZIONE!
In sudoers la parte tra parentesi è:

(runas_user:runas_group)

Quindi puoi avere:

(ALL) → qualsiasi utente
(root) → solo root
(:devs) → qualsiasi utente del gruppo devs
(root:devs) → utente + gruppo 

👉 Ma non esiste la forma (utente:%devs) come combinazione valida/utile in quel contesto [non ci va il %]

| Campo | Significato | Esempio |
|-------|-------------|---------|
| `<chi>` | utente o `%gruppo` | `alice`, `%ops` |
| `<dove>` | hostname o alias | `ALL`, `WEB`, `db01` |
| `(<utente_target[:gruppo_target]>)` | utente target (opzionale, default: `root`) | `(ALL)`, `(nobody)`, omesso |
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

## 5. Come testare con Podman

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

## 6. Errori comuni

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `sudo: /etc/sudoers.d/local is world writable` | Permessi troppo aperti | `chmod 0440 /etc/sudoers.d/local` |
| `sudo: /etc/sudoers.d/local is owned by uid X, not uid 0` | Proprietario sbagliato | `chown root:root /etc/sudoers.d/local` |
| `parse error in /etc/sudoers.d/local near line N` | Errore di sintassi | Controlla la riga N con `visudo -c -f` |
| La regola non compare in `sudo -l` | Hostname del container sbagliato | Verifica con `hostname`; deve corrispondere all'alias |
| `!SHELLS` non funziona come atteso | L'utente usa un percorso alternativo | La negazione è fragile per design in sudo |
| `%gruppo` non riconosciuto | Il gruppo non esiste sul sistema | Crea il gruppo con `groupadd` prima di testare |

---

*Guida basata su: `user-management.pdf`, `account-administration.pdf`*
