# Bibliobot

Bot progettato per essere eseguito in autonomo attraverso Cron da una macchina linux. Tramite il sito web affluences prenota un posto in una biblioteca di uniVR per tutto il girono, in fascie da 2 ore l'una. 

BIBLIOTECHE SUPPORTATE:
 - [Biblioteca Frinzi](https://affluences.com/it/sites/universita-di-verona) - Università di Verona in Via San Francesco 20
 - [Biblioteca Santa Marta](https://affluences.com/it/sites/biblioteca-santa-marta) - Università di Verona in Via Cantarane 24
 - [Biblioteca Meneghetti](https://affluences.com/it/sites/biblioteca-meneghetti-1) - Università di Verona in Strada le Grazie 8

## Requirements

*   Python 3.10 or newer

## Usage

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
python -m app.main Meneghetti 141 2026-04-08 09:00 18:00
```

The bot will then attempt to book 3-hour slots for that spot for the next 7 days, starting from the specified date. Su ubuntu è possibile lanciare in automatico il file a mezzanotte tramite crontab.

---
## Supported Library Maps
- [Mappa Biblioteca Meneghetti](assets/mappa_meneghetti.pdf)
---

## Core Architecture

The application is designed with a clear separation of concerns, dividing the logic into three main files:

1.  **`main.py` - The Control Layer:**
    *   **Purpose:** This is the primary user-facing entry point. It's responsible for the high-level orchestration of the booking process.
    *   **Responsibilities:**
        *   Parsing command-line arguments (`library_name`, `spot_number`, date/time info, `--dry-run`) using `argparse`.
        *   Translating the human-readable `library_name` and `spot_number` into a specific `spot_id` by looking it up in `locations.py`.
        *   Implementing the date and time looping logic. It iterates through the specified days and breaks down the daily time window into smaller, bookable chunks.
        *   Calculating the `start_time` and `end_time` for each individual booking.
        *   Calling the `core.py` functions to execute the booking for each chunk.
        *   Contains a `--dry-run` mode for safe testing and debugging.

2.  **`core.py` - The Execution Engine:**
    *   **Purpose:** This file contains the low-level functions that perform the actual work. It knows *how* to perform actions but is not concerned with *what* or *when* to perform them.
    *   **Responsibilities:**
        *   `create_reservation()`: Makes the direct API call to the Affluences server to request a reservation.
        *   `find_confirmation_link()`: Connects to an IMAP email server, searches for the specific confirmation email, and parses it to find the confirmation URL.
        *   `confirm_reservation()`: Visits the confirmation URL to finalize the booking.
        *   `book_library_spot()`: A wrapper function that orchestrates the sequence of `create` -> `find` -> `confirm` for a single booking slot.

3.  **`locations.py` - The Data Store:**
    *   **Purpose:** This file isolates all environment-specific data (the spot mappings) from the application logic.
    *   **Responsibilities:**
        *   Contains dictionaries that map human-readable spot numbers to the internal integer IDs required by the Affluences API.
        *   Provides a master `LIBRARY_MAP` to allow `main.py` to easily select the correct set of spots based on the `library_name` argument.

## Key Design Decisions & Rationale

*   **API-First Approach:** We interact directly with the Affluences REST API via the `requests` library.
    *   **Reason:** This is significantly faster, more reliable, and less resource-intensive than browser automation (e.g., Selenium).
*   **Separation of Credentials:** Sensitive information (email, password) is stored in a `.env` file and loaded via `python-dotenv`.
    *   **Reason:** This is a security best practice. The `.env` file is included in `.gitignore` to prevent credentials from ever being committed to version control.
*   **Orchestration in `main.py`:** The logic for looping through dates and calculating time chunks was deliberately placed in `main.py`. The `core.py` `book_library_spot` function only knows how to book a single, specific slot.
    *   **Reason:** This follows the single-responsibility principle. `core.py` is a simple "engine," while `main.py` is the "driver" that makes complex decisions. It makes the core logic easier to test and reuse.
*   **Robust Email Parsing (`text/plain`):** The `find_confirmation_link` function was refactored to parse the `text/plain` part of the confirmation email using a regular expression.
    *   **Reason:** The initial approach of parsing the HTML failed because the links were wrapped in tracking URLs by the email sending service (Mailjet). The plain text version contains the direct, stable link.
*   **Robust IMAP Connection Handling:** The `imap` connection logic in `find_confirmation_link` is wrapped in a `try...finally` block, with the connection variable initialized to `None` before the `try`.
    *   **Reason:** This is a best practice that guarantees the `imap.close()` and `imap.logout()` commands are always executed, even if an error occurs during the process. This prevents resource leaks.
*   **Date Logic Constrained by Today's Date:** The booking loop in `main.py` respects the `MAX_AHEAD_BOOKING_DAYS` as a hard limit calculated from the current date, not just as a simple counter.
    *   **Reason:** This correctly models the library's real-world rule that bookings can only be made a certain number of days into the future.
