#nome e cognome: Giuriato Simone
#Matricola: 197196

#path:/home/simone/large-file-detector/app.py o $HOME/large-file-detector/app.py  (mi dice la consegna che deve essere in $HOME)

#Questo path e il path di working directory+ app.py in Exec nel file unit dovrebbero coincidere, lui controlla questo [%h=$HOME]

# esempio esecuzione python3 app.py --target /home/simone/Scrivania/prova --size 15 --interval 5 --log /home/simone
import argparse
import time
import os
import sys

#funzione ricorsiva, attraversa ricorsivamente l'albero di directory, trovando i file piu grandi del size in argomento
def walk(base_path, size, log_path): # parametri: directory da analizzare, soglia in byte, path del file di log
    for filename in os.listdir(base_path):  # scorro tutti i nomi di file/dir dentro base_path
        path = os.path.join(base_path, filename)  # costruisco il path completo: directory + nome file

        if os.path.isfile(path):              # se è un file:
            file_size = os.path.getsize(path) # ne leggo la dimensione in byte
            if file_size >= size:             # se supera la soglia:
                print(f"Trovato un file grande: {path} ({file_size} bytes)")  # lo stampo
                #modo standard per aprire file in python: (non chiede di chiuderlo)
                with open(log_path, "a") as log_file:  # apro il log in append (senza sovrascrivere, se non esiste lo crea) [apre il file di log in modalità append e lo assegna alla variabile log_file.]
                    log_file.write(f"{path}\n")         #scrive il path del file grande nel log, con \n per andare a capo e dopo scrivere il path del file successivo

        elif os.path.isdir(path):      # se invece è una directory:
            walk(path, size, log_path) # mi richiamo ricorsivamente su di essa, scendendo di un livello




def main():

    #1)parsing degli argomenti (mi aspettto questi argomenti):
    parser=argparse.ArgumentParser(description='large-file-detector') #creo un oggetto Argument Parser 
    parser.add_argument(    #aggiunge un argomento al parser
        "--target",     #nome argomento (dato dalla consegna)
        type=str,       #il valore passato convertito in stringa [mi aspetto un path] (lo è già visto che è argomento), è utile specificare quando serve un intero
        required=True,  #la consegna mi dice che deve essere obbligatorio, se non lo è mi dà errore
        help="path assoluto della directory"    #messaggio da mostrare quando invoco programma con --help (python app.py --help) [me lo dice la consegna cosa fa il comando --target]
    )

    parser.add_argument(
        "--size",       #nome argomento
        type=int,       #converto in int 
        required=True,  #obbligatorio
        help="dimensione minima dei file in bytes, intero positivo"
    )

    parser.add_argument(
        "--interval",
        type=int,
        required=True,
        help="intervallo in secondi (intero positivo) tra ogni controllo"
    )

    parser.add_argument(
        "--log",
        type=str,
        required=True,
        help="dove salvare il file di log"
    )

    args=parser.parse_args()    #legge e verifica che gli argomenti rispettino i vincoli messi dentro add_argument, e posso fare args.argomento passato da utente

    #2)validazione argomenti ricevuti [se richiesto stamapre su standrd error]

    #verifico che percorso ricevuto da target sia assoluto
    if not os.path.isabs(args.target):  #se NON è verificata:
        print(f"errors:{args.target} non è un path assoluto", file=sys.stderr)
        sys.exit(1)
    
    #verifico che path ricevuto da target esista
    if not os.path.exists(args.target):
        print(f"errors:{args.target} non esiste", file=sys.stderr)
        sys.exit(1)

    #verifico sia una directory
    if not os.path.isdir(args.target):
        print(f"errors: {args.target} non è una directory", file=sys.stderr)
        sys.exit(1)

    #verifico che valore fornito da --size sia intero positivo
    if args.size <=0:
        print(f"errors: {args.size} non è un intero positivo", file=sys.stderr)
        sys.exit(1)
    
    #verifico che valore fornito da --interval sia intero positivo
    if args.interval<=0:
        print(f"errors: {args.interval} non è un intero positivo", file=sys.stderr)
        sys.exit(1)
    
    #verifico che percorso indicato da log esista
    if not os.path.exists(args.log):
        print(f"errors: {args.log} non esiste", file=sys.stderr)
        sys.exit(1)
    
    #verifico che percorso indicato da log sia una direcotry
    if not os.path.isdir(args.log):
        print(f"errors: {args.log} non è una directory", file=sys.stderr)
        sys.exit(1)

    #Ora che gli argomenti son corretti: costruisco il path del file di log (percorso passato da log + nome file): nome del file di log è sempre large-file-detector.log .
    log_path=os.path.join(args.log,"large-file-detector.log") #chiaramente non serve che sia assoluto, ed è piu comodo di unire con le stringhe
    
    #3)esecuzione periodica
    while True: #while infinito perchè non deve concludersi mai dall'avvio del sistema
        walk(args.target, args.size, log_path)  #log_path e non args.log perchè il percorso completo è percorso+nome file
        time.sleep(args.interval)   #aspetto N secondo dopo ogni scansione, prima di rieseguirla

    #se voglio far sparire il codice d'errore quando mando il segnale di terminazione con Ctrl C:
    """try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            break"""



if __name__ == "__main__":
    main()