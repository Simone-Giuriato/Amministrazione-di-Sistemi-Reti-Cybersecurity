#nome e cogonome: Simone Giuriato
#matricola:

#path:$HOME/file-compressor/app.py

import argparse
import os
import sys
import zipfile
import time

def walk(path_target,soglia,path_zip):
    for filename in os.listdir(path_target):
        path=os.path.join(path_target,filename)
        if os.path.isfile(path):
            dim=os.path.getsize(path)
            if dim>=soglia:
                print(f"Il file {path} supera la soglia")  
                with zipfile.ZipFile(path_zip,'a') as zipf: #vuole il path compelto dello zip (timestamp.zip)
                    zipf.write(path,arcname=filename)   #qui il path del file da mettere dento lo zip
                os.remove(path)
        elif os.path.isdir(path):
            walk(path,soglia,path_zip)

def main():
    parser=argparse.ArgumentParser('file-compressor')

    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="stringa che indica il percorso assoluto della directory da scansionare"
    )

    parser.add_argument(
        "--size",
        type=int,
        required=True,
        help="intero che specifica la soglia di dimensione in byte oltre la quale i file devono essere compressi"
    )

    #Validazione
    args=parser.parse_args()

    if not os.path.isabs(args.path):
        print(f"errore: {args.path} non è un path assoluto", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.path):
        print(f"errore: {args.path} non è un path di directory", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.path):
        print(f"errore: {args.path} non è un path esistente", file=sys.stderr)
        sys.exit(1)
    if args.size<=0:
        print(f"errore: {args.size} non è un intero positivo", file=sys.stderr)
        sys.exit(1)

    #cartella destinazione
    archives_path=os.path.expanduser('~/archives')      #creo path
    os.makedirs(archives_path,exist_ok=True)    #creo la cartella, se esiste non da errore


    #processo periodico
    timestamp=time.time() #mi calcolo il timestamp , lo calcolo qui così non cambia 
    path_zip=os.path.join(archives_path,f"{int(timestamp)}.zip")  #importante, ho un float, converto in intero, e converto in stirnga con f{ [path.join accetta solo stringhe]}

    walk(args.path,args.size,path_zip)


if __name__=="__main__":
    main()
