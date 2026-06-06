#nome e cognome: Giuriato Simone
#matricola

#path: $HOME/file-archiver/app.py

import argparse
import os
import sys
import shutil
import time

def walk(target_path,soglia, dir_archive):
    for filename in os.listdir(target_path):
        path=os.path.join(target_path,filename)
        if os.path.isfile(path):
            last_mod=os.path.getmtime(path)
            timestemp=time.time()
            diff=timestemp-last_mod
            if diff>=soglia:
                shutil.move(path,dir_archive)
                print(f"Il file {path} è stato spostato in {dir_archive} perchè vecchio {diff} secondi")
        elif os.path.isdir(path):
            walk(path,soglia,dir_archive)

def main():
    parser=argparse.ArgumentParser('file-archiver')

    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="indica il percorso assoluto della directory da controllare"
    )

    parser.add_argument(
        "--seconds",
        type=int,
        required=True,
        help="specifica l’età massima (in secondi) oltre la quale i file devono essere spostati"
    )

    args=parser.parse_args()

    if not os.path.isabs(args.path):
        print(f"errore: {args.path} non è un path assoluto", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.path):
        print(f"errore: {args.path} non è un path esistente", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(args.path):
        print(f"errore: {args.path} non è un path di directory", file=sys.stderr)
        sys.exit(3)
    if args.seconds<=0:
        print(f"errore:{args.seconds} non è un intero positivo", file=sys.stderr)
        sys.exit(4)

    path_archive=os.path.expanduser("~/archive")

    os.makedirs(path_archive,exist_ok=True)

    walk(args.path,args.seconds,path_archive)


if __name__ == "__main__":
    main()