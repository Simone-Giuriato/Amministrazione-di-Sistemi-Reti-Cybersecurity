# iptables — Guida Operativa & Manuale di Studio

> Guida completa per comprendere, configurare e risolvere esercizi su firewall Linux con `iptables`.

---

## Indice

1. [Introduzione](#1-introduzione)
2. [Struttura generale di iptables](#2-struttura-generale-di-iptables)
3. [Concetti fondamentali](#3-concetti-fondamentali)
4. [Sintassi base iptables](#4-sintassi-base-iptables)
5. [Targets](#5-targets)
6. [Flusso del pacchetto](#6-flusso-del-pacchetto)
7. [Metodo per risolvere esercizi](#7-metodo-per-risolvere-esercizi)
8. [Esempi tipici](#8-esempi-tipici)
9. [Errori comuni da evitare](#9-errori-comuni-da-evitare)
10. [Consigli da esame](#10-consigli-da-esame)

---

## 1. Introduzione

**iptables** è l'utility in spazio utente che permette agli amministratori di sistema di configurare **Netfilter**, il framework del kernel Linux per il filtraggio dei pacchetti di rete.

In un contesto di networking/firewall, `iptables` serve a:

- **Filtrare** il traffico in ingresso, uscita e inoltro (packet filtering)
- **Modificare** indirizzi IP e porte dei pacchetti (NAT — Network Address Translation)
- **Proteggere** reti private da accessi non autorizzati
- **Esporre** selettivamente servizi interni verso l'esterno (port forwarding)

Un firewall Linux con `iptables` ha tipicamente due interfacce di rete:

| Interfaccia | Rete | Ambito |
|-------------|------|--------|
| `eth0` | `203.0.113.0/24` | Pubblica (Internet) |
| `eth1` | `10.20.30.0/24` | Privata (LAN) |

Gli host della LAN usano il firewall come **gateway predefinito** e dipendono da esso per accedere a Internet.

---

## 2. Struttura generale di iptables

`iptables` organizza le regole in **tabelle**, ciascuna composta da **chain** (catene di regole).

### 2.1 Tabelle e Chain

| Tabella | Chain disponibili | Scopo principale |
|---------|-------------------|-----------------|
| `filter` | `INPUT`, `FORWARD`, `OUTPUT` | Decidere se i pacchetti sono consentiti o bloccati |
| `nat` | `PREROUTING`, `OUTPUT`, `POSTROUTING` | Modificare indirizzi IP sorgente/destinazione e porte |
| `mangle` | tutte e 5 | Modificare campi dell'intestazione IP (TTL, TOS, ecc.) |

> **Nota:** Se non viene specificata una tabella con `-t`, il default è `filter`.

### 2.2 Le 5 Chain principali

| Chain | Traffico | Quando viene attraversata |
|-------|----------|--------------------------|
| `PREROUTING` | In entrata | **Prima** della decisione di routing |
| `INPUT` | In entrata | Dopo il routing, per pacchetti **destinati al sistema locale** |
| `FORWARD` | In transito | Dopo il routing, per pacchetti **da inoltrare** ad altri host |
| `OUTPUT` | In uscita | Per pacchetti **generati localmente** |
| `POSTROUTING` | In uscita | **Dopo** la decisione di routing, appena prima che i pacchetti lascino il sistema |

---

## 3. Concetti fondamentali

### 3.1 Packet Filtering vs NAT

| Aspetto | Packet Filtering | NAT |
|---------|-----------------|-----|
| **Tabella** | `filter` | `nat` |
| **Scopo** | Permettere o bloccare pacchetti | Riscrivere indirizzi/porte |
| **Chain usate** | `INPUT`, `FORWARD`, `OUTPUT` | `PREROUTING`, `POSTROUTING` |
| **Quando usarlo** | Per controllare chi può comunicare con chi | Per tradurre indirizzi privati↔pubblici |

### 3.2 INPUT vs OUTPUT vs FORWARD

```
[ Internet ] ──────────────────────────────────── [ LAN ]

  Pacchetto → firewall → DESTINAZIONE = firewall stesso  → chain INPUT
  Pacchetto → firewall → DESTINAZIONE = host sulla LAN   → chain FORWARD
  Pacchetto ← firewall ← GENERATO dal firewall           → chain OUTPUT
```

- **INPUT**: il firewall **è il destinatario finale** (es. SSH al firewall stesso)
- **OUTPUT**: il firewall **genera** il pacchetto (es. firewall che fa ping)
- **FORWARD**: il firewall **inoltra** il pacchetto tra due host (es. LAN → Internet)

### 3.3 PREROUTING vs POSTROUTING

| Chain | Tabella | Quando | Uso tipico |
|-------|---------|--------|------------|
| `PREROUTING` | `nat` | **Prima** del routing | DNAT — riscrivere la destinazione prima che il kernel decida dove mandare il pacchetto |
| `POSTROUTING` | `nat` | **Dopo** il routing | SNAT/MASQUERADE — riscrivere la sorgente prima che il pacchetto esca |

> **Regola d'oro:** DNAT in PREROUTING, SNAT/MASQUERADE in POSTROUTING.

### 3.4 Conntrack — Connection Tracking

Il modulo `conntrack` tiene traccia dello stato delle connessioni. Permette di scrivere regole **stateful** (con stato), fondamentali per consentire il traffico di risposta.

| Stato | Significato |
|-------|-------------|
| `NEW` | Primo pacchetto di una nuova connessione |
| `ESTABLISHED` | Pacchetto che appartiene a una connessione già vista in entrambe le direzioni |
| `RELATED` | Pacchetto correlato a una connessione esistente (es. FTP data, ICMP error) |
| `INVALID` | Pacchetto che non appartiene a nessuna connessione nota |

**La regola fondamentale per il traffico di ritorno:**

```bash
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

Senza questa regola, le risposte alle connessioni avviate dalla LAN vengono scartate.

---

## 4. Sintassi base iptables

```bash
iptables [-t tabella] COMANDO chain [opzioni di match] -j TARGET
```

### 4.1 Comandi principali

| Comando | Significato | Esempio |
|---------|-------------|---------|
| `-A chain` | **Append** — aggiunge una regola in fondo alla chain | `-A FORWARD` |
| `-I chain [n]` | **Insert** — inserisce una regola in posizione `n` (default: 1) | `-I INPUT 1` |
| `-D chain n` | **Delete** — elimina la regola numero `n` | `-D INPUT 3` |
| `-P chain TARGET` | **Policy** — imposta il target di default per la chain | `-P INPUT DROP` |
| `-F [chain]` | **Flush** — svuota tutte le regole (di una chain o di tutte) | `-F` |
| `-L [chain]` | **List** — elenca le regole | `-L -v` |
| `-S [chain]` | **Show** — mostra le regole in formato iptables-save | `-S` |

### 4.2 Opzioni di match

| Opzione | Significato | Esempio |
|---------|-------------|---------|
| `-t tabella` | Seleziona la tabella (default: `filter`) | `-t nat` |
| `-i interfaccia` | Interfaccia di **ingresso** | `-i eth0` |
| `-o interfaccia` | Interfaccia di **uscita** | `-o eth1` |
| `-p protocollo` | Protocollo (`tcp`, `udp`, `icmp`) | `-p tcp` |
| `--dport porta` | Porta di **destinazione** (richiede `-p`) | `--dport 80` |
| `--sport porta` | Porta **sorgente** (richiede `-p`) | `--sport 1024` |
| `-s indirizzo` | Indirizzo IP **sorgente** | `-s 10.0.0.0/8` |
| `-d indirizzo` | Indirizzo IP **destinazione** | `-d 192.168.1.1` |
| `-m modulo` | Carica un modulo di match esteso | `-m conntrack` |
| `--ctstate stati` | Stato della connessione (richiede `-m conntrack`) | `--ctstate ESTABLISHED,RELATED` |
| `-j TARGET` | Target da applicare al pacchetto | `-j ACCEPT` |

### 4.3 Comandi di gestione rapida

```bash
# Elencare regole con numeri di riga
iptables -L --line-numbers -v

# Elencare regole tabella nat
iptables -t nat -L -v

# Mostrare regole in formato script
iptables -S
iptables -t nat -S

# Svuotare tutto (filter e nat)
iptables -F
iptables -t nat -F
```

---

## 5. Targets

### 5.1 Tabella `filter`

| Target | Cosa fa | Quando usarlo |
|--------|---------|---------------|
| `ACCEPT` | Lascia passare il pacchetto | Traffico esplicitamente consentito |
| `DROP` | Scarta il pacchetto **silenziosamente** | Policy di default; blocco stealth |
| `REJECT` | Scarta il pacchetto e invia un errore ICMP | Quando si vuole notificare il mittente |
| `LOG` | Registra il pacchetto nel log (la valutazione continua) | Debug e auditing |
| `RETURN` | Torna alla chain chiamante | Nelle chain utente personalizzate |

**Esempio DROP vs REJECT:**

```bash
# DROP: il mittente non riceve risposta (timeout)
iptables -A INPUT -p tcp --dport 23 -j DROP

# REJECT: il mittente riceve "Connection refused" immediatamente
iptables -A INPUT -p tcp --dport 23 -j REJECT
```

### 5.2 Tabella `nat`

| Target | Cosa fa | Chain | Quando usarlo |
|--------|---------|-------|---------------|
| `DNAT` | Riscrive l'IP/porta di **destinazione** | `PREROUTING` | Port forwarding verso host interni |
| `SNAT` | Riscrive l'IP/porta **sorgente** (IP statico) | `POSTROUTING` | NAT con IP pubblico fisso |
| `MASQUERADE` | SNAT dinamico (usa l'IP dell'interfaccia) | `POSTROUTING` | NAT con IP pubblico dinamico (DHCP) |
| `REDIRECT` | Redirige verso una porta locale | `PREROUTING` | Proxy trasparente |

**SNAT vs MASQUERADE:**

```bash
# SNAT: IP pubblico noto e fisso
iptables -t nat -A POSTROUTING -o eth0 -j SNAT --to-source 203.0.113.1

# MASQUERADE: IP dell'interfaccia rilevato automaticamente (preferibile con DHCP)
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

**DNAT con FORWARD obbligatorio:**

```bash
# DNAT: riscrive destinazione prima del routing
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 10.20.30.100:8080

# FORWARD: deve consentire il pacchetto sulla porta POST-DNAT (8080, non 80!)
iptables -A FORWARD -d 10.20.30.100 -p tcp --dport 8080 -j ACCEPT
```

> ⚠️ **Critico:** Ogni regola DNAT deve essere accompagnata da una regola FORWARD sulla porta **post-DNAT**, non su quella originale.

---

## 6. Flusso del pacchetto

### 6.1 Schema completo

```
                        ┌─────────────────────────────────────────────────────┐
                        │                    FIREWALL/ROUTER                  │
                        │                                                     │
Internet ──► eth0 ──►  PREROUTING  ──► [routing] ──►  FORWARD  ──►  POSTROUTING ──► eth1 ──► LAN
                        │  (DNAT)                      (FILTER)      (SNAT/MASQ)              │
                        │                    │                                                │
                        │                    ▼                                                │
                        │                  INPUT                                              │
                        │                (al firewall)                                        │
                        │                    │                                                │
                        │                  OUTPUT                                             │
                        │               (dal firewall)                                        │
                        │                    │                                                │
                        │                    ▼                                                │
                        │               POSTROUTING ────────────────────────────────────────►│
                        └─────────────────────────────────────────────────────┘
```

### 6.2 Percorso dei pacchetti per caso d'uso

**Caso 1: Client Internet → Web server interno (DNAT)**

```
Internet → eth0 → PREROUTING (DNAT: :80 → 10.20.30.100:8080)
         → FORWARD (ACCEPT tcp dport 8080)
         → POSTROUTING → eth1 → 10.20.30.100
```

**Caso 2: Host LAN → Internet (MASQUERADE)**

```
10.20.30.x → eth1 → PREROUTING (nessuna regola NAT)
           → FORWARD (ACCEPT o conntrack ESTABLISHED)
           → POSTROUTING (MASQUERADE: sorgente → 203.0.113.1)
           → eth0 → Internet
```

**Caso 3: Traffico verso il firewall stesso (INPUT)**

```
10.20.30.x → eth1 → PREROUTING → INPUT (ACCEPT icmp / tcp dport 22)
```

### 6.3 Ordine di elaborazione (priorità)

```
nat PREROUTING → routing → filter FORWARD → nat POSTROUTING
```

> Il DNAT avviene **prima** del routing e **prima** del FORWARD: la chain FORWARD vede già l'indirizzo riscritto.

---

## 7. Metodo per risolvere esercizi

Segui questi passi nell'ordine indicato ogni volta che devi configurare un firewall con `iptables`.

### Step 1 — Analizza la topologia

Identifica:
- Quante interfacce ha il firewall e a che rete appartengono
- Quali host ci sono sulla rete privata e quali servizi espongono
- Qual è il gateway predefinito degli host

### Step 2 — Svuota e imposta la policy di default

```bash
# Svuota tutte le regole esistenti
iptables -F
iptables -t nat -F

# Default deny su INPUT e FORWARD (mai su OUTPUT)
iptables -P INPUT DROP
iptables -P FORWARD DROP
# OUTPUT rimane ACCEPT (il firewall è considerato affidabile)
```

### Step 3 — Regole INPUT (accesso al firewall stesso)

Aggiungi solo ciò che è necessario per gestire il firewall:

```bash
# ICMP dalla rete privata (ping verso il gateway)
iptables -A INPUT -i eth1 -p icmp -j ACCEPT

# SSH dalla rete privata (gestione remota)
iptables -A INPUT -i eth1 -p tcp --dport 22 -j ACCEPT
```

### Step 4 — Regole NAT PREROUTING (DNAT — port forwarding)

```bash
# Inoltra HTTP esterno → web server interno
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -j DNAT --to-destination 10.20.30.100:8080

# Inoltra HTTPS esterno → web server interno
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 \
    -j DNAT --to-destination 10.20.30.100:8443
```

### Step 5 — Regole FORWARD (filtraggio del traffico in transito)

```bash
# Consenti HTTP e HTTPS verso il web server (porte POST-DNAT!)
iptables -A FORWARD -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -p tcp --dport 8443 -j ACCEPT

# Conntrack: consenti traffico di risposta (FONDAMENTALE)
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

### Step 6 — Regole NAT POSTROUTING (MASQUERADE/SNAT)

```bash
# MASQUERADE: gli host privati appaiono con l'IP pubblico del firewall
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

### Step 7 — Verifica logica

Per ogni flusso di traffico richiesto, traccia mentalmente il percorso:

```
[ PREROUTING ] → [ routing ] → [ FORWARD ] → [ POSTROUTING ]
```

Chiediti:
- Il DNAT è presente e corretto?
- La regola FORWARD usa la porta post-DNAT?
- C'è una regola conntrack per il traffico di ritorno?
- Il MASQUERADE è sull'interfaccia corretta (`-o eth0`, non `-o eth1`)?

---

## 8. Esempi tipici

### 8.1 Accesso SSH al firewall

**Problema:** Permettere SSH (`tcp/22`) solo dalla rete privata (`eth1`).

```bash
iptables -A INPUT -i eth1 -p tcp --dport 22 -j ACCEPT
```

**Spiegazione:** Il traffico SSH è diretto al firewall stesso → chain `INPUT`. Si limita all'interfaccia interna (`-i eth1`) per sicurezza.

---

### 8.2 Port forwarding HTTP/HTTPS (DNAT)

**Problema:** Il web server `10.20.30.100` è sulla LAN con porte `8080` (HTTP) e `8443` (HTTPS). I client esterni devono raggiungerlo sulle porte standard `80` e `443`.

```bash
# DNAT: riscrive la destinazione prima del routing
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -j DNAT --to-destination 10.20.30.100:8080

iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 \
    -j DNAT --to-destination 10.20.30.100:8443

# FORWARD: consenti i pacchetti riscritti (porta POST-DNAT)
iptables -A FORWARD -d 10.20.30.100 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -d 10.20.30.100 -p tcp --dport 8443 -j ACCEPT

# Conntrack: consenti il traffico di risposta
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

**Spiegazione:** Il DNAT avviene in `PREROUTING` prima che il kernel decida il routing. La chain `FORWARD` vede già il pacchetto con destinazione `10.20.30.100:8080`, quindi la regola FORWARD deve usare la porta **8080**, non **80**.

---

### 8.3 NAT per accesso a Internet (MASQUERADE)

**Problema:** Gli host della rete privata (`10.20.30.0/24`) devono poter navigare su Internet, ma usano indirizzi privati non routable.

```bash
# MASQUERADE: sostituisce l'IP sorgente privato con l'IP pubblico di eth0
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# FORWARD: consenti il traffico dalla LAN verso Internet
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

# FORWARD: consenti il traffico di ritorno
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

**Spiegazione:** `MASQUERADE` riscrive l'IP sorgente dei pacchetti in uscita da `eth0` con l'IP pubblico del firewall, così Internet può rispondere. Il conntrack gestisce il traffico di ritorno.

---

### 8.4 Schema completo — Esercizio tipico da esame

**Scenario:** firewall con `eth0` pubblica e `eth1` privata; web server interno su `10.20.30.100:8080/8443`.

```bash
# nome e cognome:
# matricola:

# ── FLUSH ────────────────────────────────────────────
iptables -F
iptables -t nat -F

# ── DEFAULT POLICY ───────────────────────────────────
iptables -P INPUT DROP
iptables -P FORWARD DROP

# ── INPUT: accesso al firewall ────────────────────────
iptables -A INPUT -i eth1 -p icmp -j ACCEPT
iptables -A INPUT -i eth1 -p tcp --dport 22 -j ACCEPT

# ── FORWARD: traffico HTTP/HTTPS ──────────────────────
iptables -A FORWARD -i eth0 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -i eth1 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -i eth0 -p tcp --dport 8443 -j ACCEPT
iptables -A FORWARD -i eth1 -p tcp --dport 8443 -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# ── NAT: MASQUERADE per LAN → Internet ───────────────
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# ── NAT: DNAT per port forwarding ────────────────────
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -j DNAT --to-destination 10.20.30.100:8080

iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 \
    -j DNAT --to-destination 10.20.30.100:8443
```

---

## 9. Errori comuni da evitare

### ❌ Dimenticare la regola FORWARD dopo un DNAT

```bash
# SBAGLIATO: il DNAT c'è ma il pacchetto riscritto viene droppato da FORWARD
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 10.20.30.100:8080
# manca: iptables -A FORWARD -d 10.20.30.100 -p tcp --dport 8080 -j ACCEPT
```

**Regola:** Ogni DNAT **deve** avere una regola FORWARD corrispondente.

---

### ❌ Usare la porta sbagliata dopo DNAT

```bash
# SBAGLIATO: si usa la porta originale (80) invece di quella post-DNAT (8080)
iptables -A FORWARD -d 10.20.30.100 -p tcp --dport 80 -j ACCEPT  # ← ERRATO

# CORRETTO: si usa la porta dopo la riscrittura DNAT
iptables -A FORWARD -d 10.20.30.100 -p tcp --dport 8080 -j ACCEPT
```

**Regola:** La chain FORWARD vede il pacchetto **già riscritto** dal DNAT.

---

### ❌ Dimenticare conntrack (ESTABLISHED,RELATED)

```bash
# SBAGLIATO: il client può mandare richieste ma non riceve risposte
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
# manca: iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

**Regola:** Senza conntrack, il traffico di risposta viene droppato dalla policy DROP.

---

### ❌ Confondere DNAT e SNAT

| Errore | Corretto |
|--------|----------|
| DNAT in POSTROUTING | DNAT in **PREROUTING** |
| SNAT/MASQUERADE in PREROUTING | SNAT/MASQUERADE in **POSTROUTING** |
| MASQUERADE su interfaccia interna (`-o eth1`) | MASQUERADE su interfaccia **esterna** (`-o eth0`) |

---

### ❌ Non specificare le interfacce

```bash
# RISCHIOSO: accetta SSH da qualunque interfaccia, anche da Internet
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# SICURO: accetta SSH solo dalla rete privata
iptables -A INPUT -i eth1 -p tcp --dport 22 -j ACCEPT
```

---

### ❌ Impostare DROP su OUTPUT

```bash
# SBAGLIATO: blocca anche le risposte generate dal firewall
iptables -P OUTPUT DROP
```

**Regola:** Lasciare sempre `OUTPUT` a `ACCEPT`. Il firewall è considerato affidabile per il traffico generato localmente.

---

### ❌ Flush solo `filter` e dimenticare `nat`

```bash
# INCOMPLETO: rimangono regole NAT residue
iptables -F

# CORRETTO
iptables -F
iptables -t nat -F
```

---

## 10. Consigli da esame

### 10.1 Come ragionare velocemente

**Domanda chiave 1:** Il pacchetto è destinato al firewall stesso o deve essere inoltrato?
- Destinato al firewall → `INPUT`
- Deve passare attraverso il firewall → `FORWARD`

**Domanda chiave 2:** L'indirizzo deve cambiare?
- Cambio di destinazione (forwarding verso LAN) → `DNAT` in `PREROUTING`
- Cambio di sorgente (LAN → Internet) → `MASQUERADE` in `POSTROUTING`

**Domanda chiave 3:** Sto usando porte non standard sul server interno?
- Sì → Il DNAT riscrive la porta, e FORWARD usa la porta **interna** (post-DNAT)

---

### 10.2 Schema mentale rapido

```
Leggi il requisito → Chiedi: chi parla con chi?
│
├─ Traffico VERSO il firewall → INPUT
│   └─ Specifica: interfaccia (-i), protocollo (-p), porta (--dport)
│
├─ Traffico ATTRAVERSO il firewall → FORWARD
│   ├─ Se c'è DNAT → usa porta POST-DNAT
│   └─ Aggiungi sempre conntrack ESTABLISHED,RELATED
│
└─ Indirizzo da modificare?
    ├─ Destinazione → DNAT in PREROUTING (-i interfaccia esterna)
    └─ Sorgente → MASQUERADE in POSTROUTING (-o interfaccia esterna)
```

---

### 10.3 Trucchi per non confondersi

| Mnemonico | Regola |
|-----------|--------|
| **PRE**routing → **PRE**-routing → **prima** del routing → DNAT | DNAT sempre in PREROUTING |
| **POST**routing → **dopo** → MASQUERADE (dopo che il routing ha deciso l'uscita) | SNAT/MASQUERADE in POSTROUTING |
| FORWARD vede pacchetti **già riscritti** dal DNAT | Usare porta interna in FORWARD |
| `-i` = **i**ngresso, `-o` = **o**uscita | MASQUERADE usa `-o eth0` (interfaccia di uscita) |
| `filter` è il **default** se non specifichi `-t` | Ometti `-t` per le regole filter |

---

### 10.4 Checklist finale prima di consegnare

```
[ ] iptables -F eseguito
[ ] iptables -t nat -F eseguito
[ ] iptables -P INPUT DROP impostato
[ ] iptables -P FORWARD DROP impostato
[ ] OUTPUT lasciato a ACCEPT (non modificato)
[ ] Ogni DNAT ha una regola FORWARD sulla porta post-DNAT
[ ] conntrack ESTABLISHED,RELATED presente in FORWARD
[ ] MASQUERADE su -o eth0 (interfaccia pubblica), non su eth1
[ ] Interfacce specificate nelle regole INPUT (-i eth1)
[ ] Porte corrette (interne vs esterne) nelle regole FORWARD
```

---

### 10.5 Comandi di verifica rapida

```bash
# Visualizza tutte le regole filter con policy
iptables -L -v --line-numbers

# Visualizza tutte le regole nat
iptables -t nat -L -v --line-numbers

# Formato script (utile per confronto)
iptables -S
iptables -t nat -S
```

---

*Riferimenti: iptables(8), iptables-extensions(8) — `man 8 iptables`*
