#nome e cognome: SImone Giuriato
#matricola:

#path: $HOME/disk-usage-monitor


import argparse
from datetime import datetime
import os
import shutil
import sys

def main():
    
    parser=argparse.ArgumentParser('disk-isage-monitor')

    parser.add_argument(
        "--partition",
        type=str,
        required=True,
        help="indica il percorso assoluto della partizione da monitorare"


    )

    parser.add_argument(
        "--threshold",
        required=True,
        type=int,
        help="a soglia in percentuale (%) oltre la quale deve essere segnalato l'utilizzo"

    )

    #validazione
    args=parser.parse_args()

    if not os.path.isabs(args.partition):
        print(f"errore: {args.partition} non è un path assoluto", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.partition):
        print(f"errore: {args.partion} non è un path esistente", file=sys.stderr)
        sys.exit(2)
    if args.threshold<0 or args.threshold>100:
        print(f"errore:{args.threshold} deve essere compreso tra 0 e 100", file=sys.stderr)
        sys.exit(3)
    
    total,usage,_=shutil.disk_usage(args.partition) #resitusice totale, usato e libero
    utilizzo_perc=(usage*100)/total #calcolo la percentuale


    if(utilizzo_perc>=args.threshold):
        log_dir=os.path.expanduser("~/disk-usage-monitor")  #creo path direcotry desitnazione
        os.makedirs(log_dir,exist_ok=True)  #creo directory

        path=os.path.join(log_dir,"disk-usage-monitor.log") #creo path del file di log
        with open(path, 'a') as f:
            timestamp=datetime.now()
            f.writelines(f"{timestamp} {utilizzo_perc}\n")
        print(f"Uso partizione:{args.partition}, supera la soglia con: {utilizzo_perc:.2f}%")   
    else:
        print("La partizione non supera la soglia in %\n")

    

 
    









if __name__=="__main__":
    main()