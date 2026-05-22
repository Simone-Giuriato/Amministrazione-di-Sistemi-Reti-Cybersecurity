# Guida al Testing del Packet Filtering con `iptables` su Ubuntu

> Questa guida accompagna l'esercizio di configurazione del firewall Linux con `iptables`.
> Copre setup dell'ambiente virtuale, verifica della topologia e test sistematici delle regole.

---

## Indice

1. [Architettura di riferimento](#1-architettura-di-riferimento)
2. [Requisiti](#2-requisiti)
3. [Setup dell'ambiente](#3-setup-dellambiente)
4. [Verifica della topologia](#4-verifica-della-topologia)
5. [Comandi utili per le regole](#5-comandi-utili-per-le-regole)
6. [Esempi di test](#6-esempi-di-test)
   - [6.1 Regola INPUT — SSH su eth1](#61-regola-input--ssh-su-eth1)
   - [6.2 Regola INPUT — ICMP su eth1](#62-regola-input--icmp-su-eth1)
   - [6.3 Regola FORWARD — HTTP/HTTPS](#63-regola-forward--httphttps)
   - [6.4 Regola FORWARD — ESTABLISHED/RELATED](#64-regola-forward--establishedrelated)
   - [6.5 NAT POSTROUTING — MASQUERADE](#65-nat-postrouting--masquerade)
   - [6.6 NAT PREROUTING — DNAT HTTP](#66-nat-prerouting--dnat-http)
   - [6.7 NAT PREROUTING — DNAT HTTPS](#67-nat-prerouting--dnat-https)
7. [Riferimento rapido ai comandi](#7-riferimento-rapido-ai-comandi)

---

## 1. Architettura di riferimento

Il firewall ha due interfacce di rete (NIC):

| NIC    | Indirizzo di rete | IP firewall   | Ambito  |
|--------|-------------------|---------------|---------|
| `eth0` | `203.0.113.0/24`  | `203.0.113.1` | Pubblico |
| `eth1` | `10.20.30.0/24`   | `10.20.30.1`  | Privato  |

- Gli host nella rete `10.20.30.0/24` usano il firewall come **gateway predefinito**.
- Il web server `10.20.30.100` espone:
  - **HTTP** sulla porta `8080`
  - **HTTPS** sulla porta `8443`
- Il client si trova nella rete pubblica (`203.0.113.0/24`), con IP ad esempio `203.0.113.50`.

> **Concetto chiave — Chain e tabelle:**
> In `iptables`, le *chain* (`INPUT`, `FORWARD`, `OUTPUT`, `PREROUTING`, `POSTROUTING`) sono punti
> dello stack di rete in cui i pacchetti vengono intercettati. Le *tabelle* raggruppano chain per tipo di
> elaborazione: `filter` decide se accettare o scartare, `nat` modifica indirizzi e porte.
> La precedenza tipica è `nat` → `filter`.

---

## 2. Requisiti

- **Podman** versione 4.x.x (testato con 4.9.3)
- Immagine Docker del professore:

```sh
$ podman pull docker.io/fglmtt/admin
```

- File `up.sh` e `down.sh` dalla repository del professore (`fglmtt/admin`)
- Permessi di esecuzione sui file:

```sh
$ chmod +x up.sh down.sh
```

---

## 3. Setup dell'ambiente

### 3.1 Modificare `up.sh` — Variabili da configurare

Apri `up.sh` e imposta le variabili seguenti con i valori forniti dalla consegna:

```sh
PUBLIC_SUBNET=203.0.113.0/24       # Rete pubblica fornita dalla consegna
PUBLIC_GATEWAY=203.0.113.254       # Rete pubblica + host 254 → x.y.z.254
FIREWALL_PUBLIC_IP=203.0.113.1     # IP pubblico del firewall (interfaccia eth0), dalla consegna
CLIENT_IP=203.0.113.50             # IP del client di test nella rete pubblica

PRIVATE_SUBNET=10.20.30.0/24      # Rete privata fornita dalla consegna
PRIVATE_GATEWAY=10.20.30.254      # Rete privata + host 254 → x.y.z.254
FIREWALL_PRIVATE_IP=10.20.30.1    # IP privato del firewall (interfaccia eth1), dalla consegna
WEB_IP=10.20.30.100               # IP privato del web server, dalla consegna
```

> **Schema logico:**
> - `PUBLIC_GATEWAY` e `PRIVATE_GATEWAY` si ricavano dalla rete prendendo sempre l'host `.254`
>   (es. `203.0.113.0/24` → gateway `203.0.113.254`)
> - `FIREWALL_PUBLIC_IP` e `FIREWALL_PRIVATE_IP` sono gli IP assegnati alle due NIC del firewall
>   e sono specificati direttamente nella consegna
> - `CLIENT_IP` e `WEB_IP` sono gli host di test nelle rispettive subnet

### 3.2 Avviare la topologia

```sh
$ ./up.sh
```

### 3.3 Aprire tre terminali separati — uno per container

```sh
# Terminale 1 — Firewall
$ podman exec -it firewall bash

# Terminale 2 — Client (rete pubblica)
$ podman exec -it client bash

# Terminale 3 — Web server (rete privata)
$ podman exec -it web bash
```

### 3.4 Smontare la topologia

```sh
$ ./down.sh
```

> **Attenzione:** Le regole `iptables` di un container vivono nel suo *network namespace* e vengono
> eliminate quando il container viene rimosso. Rieseguire `./up.sh` dopo `./down.sh` fornisce un
> firewall pulito senza regole preesistenti.

---

## 4. Verifica della topologia

Prima di scrivere qualsiasi regola, verifica che la topologia sia configurata correttamente.

### 4.1 Interfacce del firewall

```sh
ubuntu@firewall:~$ ip a
```

L'output atteso mostra `eth0` con `203.0.113.1/24` e `eth1` con `10.20.30.1/24`.

### 4.2 Tabelle di routing

```sh
ubuntu@firewall:~$ ip r
ubuntu@client:~$  ip r
ubuntu@web:~$     ip r
```

Output atteso:
- `client`: gateway predefinito `203.0.113.1` via `eth0`
- `web`: gateway predefinito `10.20.30.1` via `eth0`

### 4.3 Verifica IP forwarding

```sh
ubuntu@firewall:~$ cat /proc/sys/net/ipv4/ip_forward
```

Deve restituire `1` — il firewall è abilitato all'inoltro dei pacchetti.

### 4.4 Test di connettività base (prima delle regole)

Verifica che la topologia sia collegata correttamente pingando tra host:

```sh
ubuntu@web:~$ ping 203.0.113.50
```

Per osservare il traffico in transito sul firewall:

```sh
ubuntu@firewall:~$ tcpdump -i any icmp
```

> `tcpdump` bufferizza l'output prima di stamparlo — se non vedi subito i pacchetti, attendi un momento.

---

## 5. Comandi utili per le regole

### Visualizzare le regole attive

```sh
# Tabella filter
ubuntu@firewall:~$ iptables -S

# Tabella nat
ubuntu@firewall:~$ iptables -t nat -S

# Elenco leggibile con policy
ubuntu@firewall:~$ iptables -L
ubuntu@firewall:~$ iptables -L -t nat
```

### Applicare le regole

Incolla i comandi `iptables` direttamente nella shell del container `firewall`. Puoi incollare l'intero blocco di regole in una volta sola.

### Eliminare tutte le regole (reset pulito)

```sh
ubuntu@firewall:~$ iptables -F
ubuntu@firewall:~$ iptables -t nat -F
```

> Questo riporta il firewall alla politica di default (`ACCEPT` su tutto). Non resetta le *policy* delle chain — per farlo usa `iptables -P INPUT ACCEPT` ecc.

---

## 6. Esempi di test

> **Concetto chiave — Default deny:**
> La strategia più sicura è scartare tutto il traffico non esplicitamente consentito.
> Si ottiene svuotando le chain (`-F`) e impostando la policy di `INPUT` e `FORWARD` su `DROP`.
> La chain `OUTPUT` rimane `ACCEPT` perché il firewall è considerato affidabile per il traffico generato localmente.

---

### 6.1 Regola INPUT — SSH su eth1

**Regola testata:**
```sh
iptables -A INPUT -i eth1 -p tcp --dport 22 -j ACCEPT
```

Questa regola accetta pacchetti TCP sulla porta 22 (SSH) in arrivo **solo da `eth1`** (rete privata).

**Test:**

1. Metti in ascolto il firewall sulla porta 22:
```sh
ubuntu@firewall:~$ nc -l 22
```

2. Dal **web server** (che è sulla rete privata `eth1`), connettiti al gateway `10.20.30.1`:
```sh
ubuntu@web:~$ nc 10.20.30.1 22
```

3. Digita del testo: deve apparire sul terminale del firewall. ✅

4. **Verifica che il client NON passi** (la regola filtra su `eth1`, non su `eth0`):
```sh
ubuntu@client:~$ nc 203.0.113.1 22
```
Nessuna risposta — la connessione viene scartata. ✅

---

### 6.2 Regola INPUT — ICMP su eth1

**Regola testata:**
```sh
iptables -A INPUT -i eth1 -p icmp -j ACCEPT
```

Questa regola consente il traffico ICMP (ping) verso il firewall solo dall'interfaccia privata `eth1`.

**Test:**

1. Esegui il ping dal web server verso il gateway privato:
```sh
ubuntu@web:~$ ping 10.20.30.1
```

2. Osserva il traffico sul firewall:
```sh
ubuntu@firewall:~$ tcpdump -i any icmp
```

Dovresti vedere le richieste ICMP su `eth1` e le risposte. ✅

3. **Verifica che il client NON riceva risposta** al ping verso `203.0.113.1` (regola su `eth1` soltanto):
```sh
ubuntu@client:~$ ping 203.0.113.1
```
Nessuna risposta. ✅

---

### 6.3 Regola FORWARD — HTTP/HTTPS

**Regole testate:**
```sh
iptables -A FORWARD -i eth0 -o eth1 -p tcp --dport 80  -j ACCEPT
iptables -A FORWARD -i eth0 -o eth1 -p tcp --dport 443 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -p tcp --dport 80  -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -p tcp --dport 443 -j ACCEPT
```

> **Concetto chiave — FORWARD:**
> La chain `FORWARD` intercetta i pacchetti che *transitano* attraverso il firewall (non destinati
> al firewall stesso). Specifica l'interfaccia di ingresso (`-i`) e di uscita (`-o`) per controllare
> la direzione del flusso.

**Test — dal client verso il web (porta 80):**

1. Metti in ascolto `web` sulla porta 80:
```sh
ubuntu@web:~$ nc -l 80
```

2. Connettiti dal client all'IP privato del web server:
```sh
ubuntu@client:~$ nc 10.20.30.100 80
```

3. Digita del testo: deve apparire sul web server. ✅

---

### 6.4 Regola FORWARD — ESTABLISHED/RELATED

**Regola testata:**
```sh
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

> **Concetto chiave — Stateful firewall:**
> Una singola regola che consente `tcp/80` in una direzione non è sufficiente: copre i pacchetti
> in andata, ma non il traffico di ritorno. La soluzione è una regola *con stato* (stateful) che
> usa il modulo `conntrack` per tenere traccia delle connessioni già stabilite e accettare
> automaticamente i pacchetti di risposta (`ESTABLISHED`) e quelli correlati (`RELATED`).

**Test:**

Con le regole di FORWARD per `tcp/80` e la regola `ESTABLISHED,RELATED`:

1. Metti in ascolto `web` sulla porta 80:
```sh
ubuntu@web:~$ nc -l 80
```

2. Connettiti dal client:
```sh
ubuntu@client:~$ nc 10.20.30.100 80
```

3. Digita dal lato `web` e verifica che `client` riceva la risposta — questo funziona grazie alla
   regola `ESTABLISHED,RELATED` che permette il traffico di ritorno. ✅

---

### 6.5 NAT POSTROUTING — MASQUERADE

**Regola testata:**
```sh
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

> **Concetto chiave — MASQUERADE:**
> Gli host della rete privata (`10.20.30.0/24`) usano indirizzi IP non routable su Internet.
> `MASQUERADE` è una variante di SNAT eseguita in `POSTROUTING`: riscrive l'indirizzo sorgente
> dei pacchetti uscenti da `eth0` con l'IP pubblico del firewall (`203.0.113.1`), così le risposte
> torneranno al firewall che le ritradurrà verso l'host privato corretto.

**Test:**

Con MASQUERADE attivo e le regole FORWARD appropriate:

1. Dal web server, prova a raggiungere il client (simulando traffico verso Internet):
```sh
ubuntu@web:~$ ping 203.0.113.50
```

2. Osserva sul firewall che i pacchetti in uscita da `eth0` hanno come sorgente `203.0.113.1`
   e non `10.20.30.100`:
```sh
ubuntu@firewall:~$ tcpdump -i eth0 icmp
```
✅

---

### 6.6 NAT PREROUTING — DNAT HTTP

**Regole testate:**
```sh
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 10.20.30.100:8080
iptables -A FORWARD -i eth0 -o eth1 -p tcp -d 10.20.30.100 --dport 8080 -j ACCEPT
```

> **Concetto chiave — DNAT e ordine di elaborazione:**
> DNAT viene eseguito in `PREROUTING`, *prima* della decisione di routing e *prima* di `FORWARD`.
> Quindi il pacchetto entra nella chain `FORWARD` con la destinazione già riscritta (porta `8080`,
> non `80`). Per questo motivo la regola `FORWARD` deve consentire la porta **post-DNAT** (`8080`),
> altrimenti il pacchetto riscritto incappa nel `DROP` predefinito.

**Test:**

1. Metti in ascolto il web server sulla porta `8080`:
```sh
ubuntu@web:~$ nc -l 10.20.30.100 8080
```

2. Dal client, connettiti all'interfaccia **pubblica** del firewall sulla porta `80`:
```sh
ubuntu@client:~$ nc 203.0.113.1 80
```

3. Il firewall esegue la DNAT: trasforma la destinazione da `203.0.113.1:80` a `10.20.30.100:8080`.

4. Digita del testo dal client — deve apparire sul web server. ✅

---

### 6.7 NAT PREROUTING — DNAT HTTPS

**Regole testate:**
```sh
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 -j DNAT --to-destination 10.20.30.100:8443
iptables -A FORWARD -i eth0 -o eth1 -p tcp -d 10.20.30.100 --dport 8443 -j ACCEPT
```

**Test (analogo al DNAT HTTP):**

1. Metti in ascolto il web server sulla porta `8443`:
```sh
ubuntu@web:~$ nc -l 10.20.30.100 8443
```

2. Dal client, connettiti all'interfaccia pubblica sulla porta `443`:
```sh
ubuntu@client:~$ nc 203.0.113.1 443
```

3. Digita del testo dal client — deve apparire sul web server. ✅

---

## 7. Riferimento rapido ai comandi

| Azione | Comando |
|--------|---------|
| Avviare la topologia | `./up.sh` |
| Smontare la topologia | `./down.sh` |
| Shell nel firewall | `podman exec -it firewall bash` |
| Shell nel client | `podman exec -it client bash` |
| Shell nel web server | `podman exec -it web bash` |
| Vedere interfacce | `ip a` |
| Vedere routing | `ip r` |
| Vedere regole filter | `iptables -S` |
| Vedere regole nat | `iptables -t nat -S` |
| Eliminare regole filter | `iptables -F` |
| Eliminare regole nat | `iptables -t nat -F` |
| Ascolto su porta TCP | `nc -l <porta>` |
| Connessione TCP | `nc <ip> <porta>` |
| Sniff ICMP | `tcpdump -i any icmp` |
| Sniff su interfaccia | `tcpdump -i eth0` |
| Sniff TCP porta | `tcpdump -i any tcp port <porta>` |

---

*Licenza testo: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International*
