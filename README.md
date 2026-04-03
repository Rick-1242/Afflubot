# 📚 Afflubot
[![Build and Push](https://github.com/Rick-1242/Afflubot/actions/workflows/docker-ci.yml/badge.svg)](https://github.com/Rick-1242/Afflubot/actions/workflows/docker-ci.yml) [![Python](https://img.shields.io/badge/Python-3.10-yellow?logo=python&logoColor=white)](https://python.org) [![License: GPL v3](https://img.shields.io/badge/License-GPLv2-blue.svg)](https://www.gnu.org/licenses/gpl-2.0) [![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://docker.com) [![Docker Pulls](https://img.shields.io/docker/pulls/rick1242/afflubot)](https://hub.docker.com/r/rick1242/afflubot) [![Docker Image Size](https://img.shields.io/docker/image-size/rick1242/afflubot/latest)](https://hub.docker.com/r/rick1242/afflubot)


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
- [Biblioteca Santa Marta](https://affluences.com/it/sites/biblioteca-santa-marta) - Università di Verona in Via Cantarane 24
  - [Mappa Biblioteca Santa Marta](assets/mappa_santa_marta.pdf) ONLY SALA STUDIO SCIENZE GIUDRIDICHE
- [Biblioteca Meneghetti](https://affluences.com/it/sites/biblioteca-meneghetti-1) - Università di Verona in Strada le Grazie 8
  - [Mappa Biblioteca Meneghetti](assets/mappa_meneghetti.pdf)

### Not yet supported Libraries
- [Biblioteca Frinzi](https://affluences.com/it/sites/universita-di-verona) - Università di Verona in Via San Francesco 20
  - [Mappa Biblioteca Finzi](assets/mappa_frinzi.pdf)

---

## ⚙️ Getting Started

Before running the bot in any mode, you need to configure your credentials.

**Step 1: Create a `.env` file**
```bash
cp .env.example .env
```

**Step 2: Configure your `.env` file**  
Open the newly created `.env` file and fill in your details:
* **For Manual (CLI) use:** Only the "Core Configuration" section is required.
* **For Docker use:** Fill out BOTH the "Core Configuration" and "Automated Scheduler Configuration" sections.

---

## 🚀 Execution Modes

There are two primary ways to run Afflubot: manually via the Python CLI or continuously via Docker.

### 1. Manual Execution (CLI)

Ideal for manual bookings or setting up your own `cron` jobs on a Linux machine. *(Requires Python 3.10+)*

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Navigate to the source directory:**
> **⚠️ Important:** You *must* run the application from within the `src` directory so relative paths resolve correctly!
```bash
cd src
```

**3. Run the bot:**
```bash
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

### 2. Automated Execution 🐳

For a fully hands-off experience. The built-in scheduler reads your `.env` configuration and triggers the booking script daily at the scheduled time.

**1. Pull or Build the Image:**
```bash
docker pull rick1242/afflubot
# OR build it locally: docker build -t afflubot .
```

**2. Run the Container in the Background:**
Using the `.env` (Recommended) file you created in Step 1:
```bash
docker run -d --name my-afflubot --env-file .env afflubot
```
*Alternatively*, if you prefer not to use a `.env` file, you can pass the variables directly inline:
```bash
docker run -d --name my-afflubot \
  -e IMAP_SERVER=imap.gmail.com \
  -e EMAIL_ADDRESS=your.email@gmail.com \
  -e EMAIL_PASSWORD=your-16-char-app-password \
  -e LIBRARY=Meneghetti \
  -e SPOT=141 \
  -e TIME_START=09:00 \
  -e TIME_END=18:00 \
  afflubot
```

**3. (Recommended) Run with Log Persistence:**  
If you want the bot's log files to be saved directly to your host machine so you can read them easily:
```bash
docker run -d --name my-afflubot --env-file .env -v $(pwd)/src/logs:/app/src/logs afflubot
```

Helpful Docker Commands

* **View live stdout and stderr:** `docker logs -f my-afflubot`
* **Stop the bot:** `docker stop my-afflubot`
* **Delete the container:** `docker rm my-afflubot`

---

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
