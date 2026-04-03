# 📚 Afflubot

> *Automated library spot booking for the Affluences platform.*

## 🌟 Highlights
- 🚀 **Automated Booking:** Books your favorite library spot automatically via the Affluences REST API.
- 🕒 **Smart Scheduling:** Respects library opening hours and maximum advance booking days.
- 🐳 **Docker Support:** Ready to be deployed as a background service with a built-in scheduler.
- 📧 **Auto-Confirmation:** Connects to your email via IMAP to automatically confirm the reservation link.
- 🛡️ **Safe Testing:** Includes a `--dry-run` mode for safe testing and debugging without making actual bookings.

## ℹ️ Overview

Afflubot is a robust Python CLI application designed to automate the tedious process of booking library spots through the Affluences platform. It is built to run autonomously, ensuring you never miss a spot at your favorite university library. 

The bot books a spot for the entire day by breaking the daily time window into smaller, bookable chunks (typically 2-hour or 3-hour slots depending on the library). 

### Supported Libraries (UniVR)
- [Biblioteca Frinzi](https://affluences.com/it/sites/universita-di-verona) - Università di Verona in Via San Francesco 20
  - [Mappa Biblioteca Finzi](assets/mappa_frinzi.pdf)
- [Biblioteca Santa Marta](https://affluences.com/it/sites/biblioteca-santa-marta) - Università di Verona in Via Cantarane 24
  - [Mappa Biblioteca Santa Marta](assets/mappa_santa_marta.pdf)
- [Biblioteca Meneghetti](https://affluences.com/it/sites/biblioteca-meneghetti-1) - Università di Verona in Strada le Grazie 8
  - [Mappa Biblioteca Meneghetti](assets/mappa_meneghetti.pdf)

## 🚀 Usage instructions

There are two primary ways to run Afflubot: manually via the Python CLI or continuously via Docker.

### 1. Manual Execution (CLI)

You can run the application directly using Python. This is ideal for manual bookings or setting up your own `cron` jobs on a Linux machine to run automatically at midnight.

**⚠️ Important:** You *must* run the application from within the `src` directory so that relative imports and environment variables resolve correctly.

```bash
cd src
python -m afflubot <library_name> <spot_number> <start_date> <day_start_time> <day_end_time>
```

**Arguments:**
1. `library_name`: The name of the library (e.g., `Meneghetti`). Must match a key in `locations.py`.
2. `spot_number`: The specific spot number you want to book.
3. `start_date`: The first date for which to attempt booking (format: `YYYY-MM-DD`).
4. `day_start_time`: The time to start booking from each day (format: `HH:MM`).
5. `day_end_time`: The time to end booking at each day (format: `HH:MM`).

**Example:**
To book spot #141 at Biblioteca Meneghetti from 09:00 to 18:00, starting on April 8th, 2026:
```bash
python -m afflubot Meneghetti 141 2026-04-08 09:00 18:00
```
*Tip: On linux, you can easily automate this by adding the command to your `crontab`.*

### 2. Automated Execution (Docker & Scheduler)

For a fully hands-off experience, you can use the built-in scheduler via Docker. The `scheduler.py` script acts as an entry point, reading your configuration from `.env` environment variables and automatically triggering the main booking script every day at 04:00 for the maximum allowed booking date ahead.

```bash
docker pull afflubot .
docker run -d --env-file .env afflubot
```

## ⬇️ Installation instructions

To run the project locally without Docker, you will need Python 3.10 or newer.

1. Clone the repository and navigate into it.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory. You must include your sensitive credentials (email, IMAP settings, and Affluences password) here. It is also used to configure the daily scheduler variables if using Docker.

## 🏗️ Core Architecture

The application is designed with a clear separation of concerns:

1. **`cli.py` - The Control Layer:**
   - The primary user-facing entry point.
   - Parses command-line arguments and handles the date/time looping logic.
   - Breaks down the daily time window into smaller chunks and calls the execution engine.
   - Includes validation against library opening hours to avoid unnecessary API calls.
2. **`core.py` - The Execution Engine:**
   - Contains the low-level functions that interact directly with the Affluences API via `requests`.
   - Handles the entire flow: `create_reservation()`, `find_confirmation_link()`, and `confirm_reservation()`.
3. **`locations.py` - The Data Store:**
   - Isolates all environment-specific data.
   - Maps human-readable spot numbers to the internal integer IDs required by the Affluences API.
   - Stores library opening hours for validation.
4. **`scheduler.py` - The Automated Entry Point:**
   - A cron-like scheduler leveraging the `schedule` library, suitable for Docker deployments.
   - Calculates the target booking date based on the library's `max_ahead_booking_days` and triggers `cli.py` as a subprocess daily.

## 💭 Contributing

Issues and Pull Requests are welcome. Please ensure that your contributions align with the existing architectural principles and separation of concerns outlined above.
