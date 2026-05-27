# nome e cognome: Giuriato Simone
# matricola:
#
# path:$HOME/old-file/detector/app.py

import argparse
import os
import sys
import time

def walk(path_target, days, log_file_path):
    for filename in os.listdir(path_target):
        path=os.path.join(path_target,filename)
        if os.path.isfile(path):
            last_mod=os.path.getmtime(path)
            if last_mod<(time.time() - days * 86400):
                with open(log_file_path,"a") as f:
                    f.write(f"{path}\n")
                print(f"file vecchio trovato con path:{path}\n")
                #os.remove(path)    #a commento perchè non voglio rimuova i file èer le prove
        elif os.path.isdir(path):
            walk(path,days,log_file_path)



def main():
    parser=argparse.ArgumentParser('old-file-detector')
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="indica il percorso assoluto della directory da controllare"
    )

    parser.add_argument(
        "--days",
        type=int,
        required=True,
        help=" il numero di giorni (intero positivo) oltre i quali un file è considerato vecchio"
    )

    parser.add_argument(
        "--interval",
        type=int,
        required=True,
        help=" definisce l'intervallo in secondi (intero positivo) tra ogni controllo"
    )

    parser.add_argument(
        "--log",
        type=str,
        required=True,
        help="indica dove salvare il file di log. Il nome del file di log è sempre old-file-detector.log."
    )

    args=parser.parse_args()

    #validazione
    if not os.path.isabs(args.target):
        print(f"errore: {args.target} non è un path assoluto", sys=file.stderr)
        sys.exit(1)
    if not os.path.exists(args.target):
        print(f"errore: {args.target} non è esiste", sys=file.stderr)
        sys.exit(1)
    if not os.path.isdir(args.target):
        print(f"errore: {args.target} non è una directory", sys=file.stderr)
        sys.exit(1)
    if args.interval<=0:
        print(f"errore: {args.interval} non è un intero positivo", sys=file.stderr)
    if args.days<=0:
        print(f"errore: {args.days} non è un intero positivo", sys=file.stderr)
    if not os.path.exists(args.log):
        print(f"errore: {args.log} non è esiste", sys=file.stderr)
        sys.exit(1)
    if not os.path.isdir(args.log):
        print(f"errore: {args.log} non è una directory", sys=file.stderr)
        sys.exit(1)
    
    log_file_path=os.path.join(args.log,"old-file-detector.log")

    while True:
        walk(args.target, args.days,log_file_path)
        time.sleep(args.interval)




if __name__ == "__main__":
    main()