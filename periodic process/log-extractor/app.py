# nome e cognome: Simone Giuriato
# matricola: 197196
#
# path:$HOME/log-extractor/app.py
import argparse
import os
import sys

def find(path,pattern): #Funzione che trova le righe contenti la stringa indicata dall'utente
    with open(path,"r") as f:   #Apre il file filename in modalità lettura ("r"), Restituisce un oggetto file (qui chiamato f) che permette di leggere il contenuto
        lista_righe=f.readlines()    #Legge tutte le righe del file e metto tutte le righe lette dal file dentro lista_righe che poi sarà filtrata 
    lista_righe_pattern=[]      #creo lista vuota che conterrà le righe col pattern
    for riga in lista_righe:    #per ogni riga che fa parte della lista_righe
        if pattern in riga:     #serve a controllare se una stringa è contenuta in un’altra stringa.
            lista_righe_pattern.append(riga)  #aggiunge la riga alla lista filtrata
            print({riga})  #stampa la riga trovata (può essere utile per debug)
    
    return lista_righe_pattern  #ritorna la lista con solo le righe che contengono il pattern

def writeFile(backup_file,righe):
    with open(backup_file,"w") as f:        #apro il file dove devo scrivere in modalità scrittura
        f.writelines(righe)     #ci scrivo le righe filtrate che mi passano
        #ATTENZIONE: le righe devono già avere il "\n" finale per andare a capo correttamenten(lo hanno senza fare nulla)

def walk(log_dir,backup_dir,pattern):
    for filename in os.listdir(log_dir):        #per ogni file della directory
        path = os.path.join(log_dir, filename)  #costruisco il path del file in questione: percorsodir/nomefile
        if os.path.isfile(path) and filename.endswith(".log"):        #se è un file .log
            lista_righe=find(path,pattern)      #faccio una lista che contiene solo le righe con il pattern, mi appoggio alla funzione find
            print(f"Sono state trovate {len(lista_righe)} righe in {path}")  #stampa quante righe sono state trovate
            backup_filename=os.path.join(backup_dir,filename)       #creo il path del file di backup
            writeFile(backup_filename,lista_righe)  #scrivo le righe filtrate dentro il file backup
            print(f"Sono state scritte nel file backup {len(lista_righe)} righe in {backup_filename}")  #stampa conferma
        elif os.path.isdir(path):   #se è una directory allora richiamo la funzione stessa--> ricorsione
            walk(path,backup_dir,pattern)   #gli ripasso gli argomenti ma come path quello della sottodirectory da analizzare
            #questo permette di esplorare tutte le sottocartelle in modo ricorsivo

def main():
    #1)parsing degli argomenti (mi aspetto questi argomenti):
    parser=argparse.ArgumentParser(description='log-extractor')
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="percorso assoluto directory da analizzare"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        required=True,
        help="specifica la stringa da cercare nei file di log"
    )
    args=parser.parse_args() 

    #2)validazione argomenti ricevuti [se richiesto stampare su standard error]
    if not os.path.isabs(args.path):
        print(f"errors: {args.path} non è un path assoluto", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.path):
        print(f"errors:{args.path} non esiste", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.path):
        print(f"errors:{args.path} non è una directory", file=sys.stderr)
        sys.exit(1)
    if not args.pattern:
        print(f"errors:{args.pattern} non deve essere vuota", file=sys.stderr)
        sys.exit(1)

    # assicurati che la directory backup esista in ~ (os.path.expanduser, os.makedirs) 
    backup_path=os.path.expanduser("~/backup")   #creo una variabile backup_path=home/(user)/. os.path.expanduser() serve a trasformare ~ nella tua cartella home reale
    os.makedirs(backup_path,exist_ok=True)  #crea la cartella al percorso contenuto in backup_path. [exist_ok=True se la cartella esiste già  va avanti]

    #Esplora ricorsivamente l'albero di directory al path fornito
    walk(args.path, backup_path, args.pattern)
    #walk() esplora file e sottocartelle, filtra righe con pattern e le salva in backup

if __name__ == "__main__":
    main()  #esegue il programma principale