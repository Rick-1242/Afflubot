# Bibliobot

Bot progettato per essere eseguito in autonomo attraverso Cron da una macchina linux. Tramite il sito web affluences prenota un posto in una biblioteca di uniVR per tutto il girono, in fascie da 2 ore l'una. 

BIBLIOTECHE SUPPORTATE:
 - [Biblioteca Frinzi](https://affluences.com/it/sites/universita-di-verona) - Università di Verona in Via San Francesco 20
 - [Biblioteca Santa Marta](https://affluences.com/it/sites/biblioteca-santa-marta) - Università di Verona in Via Cantarane 24
 - [Biblioteca Meneghetti](https://affluences.com/it/sites/biblioteca-meneghetti-1) - Università di Verona in Strada le Grazie 8

## Requirements

*   Python 3.10 or newer

## Usage

The script is run from the command line and accepts five arguments to schedule bookings.

### Command

```bash
python main.py library_name spot_number start_date day_start_time day_end_time
```

### Arguments

1.  `library_name`: The name of the library (e.g., `"Meneghetti"`). This must match a key in the `LIBRARY_MAP` in `locations.py`.
2.  `spot_number`: The specific spot number you want to book.
3.  `start_date`: The first date for which to attempt booking (format: `YYYY-MM-DD`).
4.  `day_start_time`: The time to start booking from each day (format: `HH:MM`).
5.  `day_end_time`: The time to end booking at each day (format: `HH:MM`).

### Example

To book spot #141 at Biblioteca Meneghetti from 09:00 to 18:00, starting on April 8th, 2026, you would run:

```bash
python main.py Meneghetti 141 2026-04-08 09:00 18:00
```

The bot will then attempt to book 3-hour slots for that spot for the next 7 days, starting from the specified date.

<!--Su ubuntu è possibile lanciare in automatico il file a mezzanotte tramite crontab.
Per farlo usare il comando crontab -e da terminale e inserire  
1 0 * * 1,2,3,4,5 /percorsoPython/python3 /percorsoFile/prenotaX.py-->
