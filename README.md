# Bibliobot

Bot progettato per essere eseguito in autonomo attraverso Cron da una macchina linux. Tramite il sito web affluences prenota un posto in una biblioteca di uniVR per tutto il girono, in fascie da 2 ore l'una. 

BIBLIOTECHE SUPPORTATE:
 - [Biblioteca Frinzi](https://affluences.com/it/sites/universita-di-verona) - Università di Verona in Via San Francesco 20
 - [Biblioteca Santa Marta](https://affluences.com/it/sites/biblioteca-santa-marta) - Università di Verona in Via Cantarane 24
 - [Biblioteca Meneghetti](https://affluences.com/it/sites/biblioteca-meneghetti-1) - Università di Verona in Strada le Grazie 8

## Requirements

*   Python 3.10 or newer

USAGE: To define

<!--Su ubuntu è possibile lanciare in automatico il file a mezzanotte tramite crontab.
Per farlo usare il comando crontab -e da terminale e inserire  
1 0 * * 1,2,3,4,5 /percorsoPython/python3 /percorsoFile/prenotaX.py-->
