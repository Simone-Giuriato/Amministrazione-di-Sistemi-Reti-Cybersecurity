#nome e cognome: SImone Giuriato
#matricola
#path: $HOME/dire-size-monitor/app.py

import argparse
from datetime import datetime
import os
import sys
import time

def walk(path_target):  #l'obiettivo è calcolare solo grandezza direcotry princiale, non di ogni sottodirectory
    counter=0
    for filename in os.listdir(path_target):
        path=os.path.join(path_target,filename)
        if os.path.isfile(path):
            counter=counter+ os.path.getsize(path)
        elif os.path.isdir(path):
            counter=counter+ walk(path)
    return counter

    
            
            


def main():
    parser=argparse.ArgumentParser('dir-size-monitor')

    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="indica il percorso assoluto della directory da monitorare"
    )

    parser.add_argument(
        "--threshold",
        type=int,
        required=True,
        help="indica la soglia in byte (intero positivo) oltre la quale deve essere registrato un avviso"
    )

    parser.add_argument(
        "--interval",
        type=int,
        required=True,
        help=" definisce l'intervallo in secondi (intero positivo) tra ogni controllo"
    )

    parser.add_argument(    #Il nome del file di log è sempre dir-size-monitor.log.
        "--log",
        type=str,
        required=True,
        help="indica il percorso assoluto della directory dove salvare il file di log."
    )

    args=parser.parse_args()

    #validazione

    if not os.path.isabs(args.target):
        print(f"errore: {args.target} non è un path assoluto", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.target):
        print(f"errore: {args.target} non è un path esistente", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(args.target):
        print(f"errore: {args.target} non è un path di directory", file=sys.stderr)
        sys.exit(3)
    if args.interval<=0:
        print(f"errore: {args.interval} non è un intero positivo",file=sys.stderr)
        sys.exit(4)
    if args.threshold<=0:
        print(f"errore: {args.threshold} non è un intero positivo",file=sys.stderr)
        sys.exit(5)
    if not os.path.isdir(args.log):
        print(f"errore: {args.log} non è un path di directory", file=sys.stderr)
        sys.exit(6)
    if not os.path.isabs(args.log):
        print(f"errore: {args.log} non è un path assoluto", file=sys.stderr)
        sys.exit(7)


    path_log= os.path.join(args.log,"dir-size-monitor.log")
    while True:
        size=walk(args.target)
        if(size>args.threshold):
            with open(path_log, "a") as log_file:
                log_file.write(f"{datetime.now()} {size}\n")
            print(f"Grandezza totale:{size}")
        time.sleep(args.interval)




if __name__ == "__main__":
    main()
