#nome e cognome: Giuriato Simone
#matricola:

#path: $HOME/large-file-detector/app.py

import argparse
import os
import sys
import time

def walk(path_target, size,path_log):
    for filename in os.listdir(path_target):
        path=os.path.join(path_target,filename)
        if os.path.isfile(path):
            dim=os.path.getsize(path)
            if(dim>=size):
                with open(path_log,'a') as f:
                    f.write(f"{path}\n")
                print(f"Ho trovato un file grande: {path}")
        elif os.path.isdir(path):
            walk(path,size,path_log)

def main():
    parser=argparse.ArgumentParser('large-file-detector')

    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="indica il percorso assoluto della directory da controllare"
    )
    parser.add_argument(
        "--size",
        type=int,
        required=True,
        help="specifica la dimensione minima in byte (intero positivo) dei file da segnalare"
    )
    parser.add_argument(
        "--interval",
        type=int,
        required=True,
        help="definisce l'intervallo in secondi (intero positivo) tra ogni controllo"
    )
    parser.add_argument(
        "--log",
        type=str,
        required=True,
        help=" indica dove salvare il file di log"
    )

    #validazione
    args=parser.parse_args()

    if not os.path.isabs(args.target):
        print(f"errore: {args.target}  non è un path assoluto", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.target):
        print(f"errore: {args.target}  non è un path esistente", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(args.target):
        print(f"errore: {args.target}  non è un path di directory", file=sys.stderr)
        sys.exit(3)
    if args.size<=0:
        print(f"errore: {args.size}  non è intero positivo", file=sys.stderr)
        sys.exit(4)
    if args.interval<=0:
        print(f"errore: {args.interval}  non è intero positivo", file=sys.stderr)
        sys.exit(5)
    if not os.path.exists(args.log):
        print(f"errore: {args.log}  non è un path esistente", file=sys.stderr)
        sys.exit(6)
    if not os.path.isdir(args.log):
        print(f"errore: {args.log}  non è un path di directory", file=sys.stderr)
        sys.exit(7)

    
    path_log=os.path.join(args.log,'large-file-detector.log')
    

    while True:
        walk(args.target,args.size,path_log)
        time.sleep(args.interval)
    
    





if __name__ == "__main__":
    main()

