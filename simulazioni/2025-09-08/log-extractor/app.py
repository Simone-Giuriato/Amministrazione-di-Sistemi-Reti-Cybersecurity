#nome e cognome: Giuriato Simone
#matricola:

#path: $HOME/log-extractor/app.py

import argparse
import os
import sys


def walk(path_target,pattern,path_backup):
    for filename in os.listdir(path_target):
        path=os.path.join(path_target,filename)
        if os.path.isfile(path) and path.endswith('.log'):
            righe_trovate=[]
            righe=[]
            with open(path,'r') as f:
                righe=f.readlines()
                for riga in righe:
                    if pattern in riga:
                        righe_trovate.append(riga)
            log_dest= os.path.join(path_backup,filename)
            with open(log_dest,'w') as log:
                log.writelines(righe_trovate)
            print(f"Sono state trovate {len(righe_trovate)} e scritte nel file:{log_dest}")
        elif os.path.isdir(path):
            walk(path,pattern,path_backup)



def main():
    parser=argparse.ArgumentParser('log-extractor')

    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="specifica il percorso assoluto della directory da analizzare"
    )

    parser.add_argument(
        "--pattern",
        type=str,
        required=True,
        help="pecifica il pattern da cercare all'interno dei file di log"
    )

    #validazione
    args=parser.parse_args()

    if not os.path.isabs(args.path):
        print(f"errore {args.path} non è un path assoluto",file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.path):
        print(f"errore {args.path} non è un path esistente",file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(args.path):
        print(f"errore {args.path} non è un path di directory",file=sys.stderr)
        sys.exit(3)
    if not args.pattern:
        print(f"errore {args.pattern} non deve essere una stringa vuota", file=sys.stderr)
        sys.exit(4)

    
    backup_path=os.path.expanduser("~/bakcup")  #creo il path
    os.makedirs(backup_path, exist_ok=True)

    walk(args.path,args.pattern,backup_path)




if __name__=="__main__":
    main()