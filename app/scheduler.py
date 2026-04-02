import os
import sys
import time
import schedule
import subprocess
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Ensure the app module can be found from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.locations import LIBRARY_DATA
from app.logging_config import setup_logging

logger = setup_logging()

def run_bot() -> None:
    logger.info("Starting scheduled bot run...")

    library = os.getenv("LIBRARY")
    spot = os.getenv("SPOT")
    time_start = os.getenv("TIME_START")
    time_end = os.getenv("TIME_END")
    imap_server = os.getenv("IMAP_SERVER")
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not all([library, spot, time_start, time_end, imap_server, email_address, email_password]):
        logger.error("Missing required environment variables. Ensure LIBRARY, SPOT, TIME_START, TIME_END, IMAP_SERVER, EMAIL_ADDRESS, and EMAIL_PASSWORD are set.")
        return

    library_data = LIBRARY_DATA.get(library) # ignore mypy/pyright its crazy
    if not library_data:
        logger.error(f"Library '{library}' not found in locations.py.")
        return

    max_ahead_days = library_data.get("max_ahead_booking_days")

    # Calculate target date: today + max_ahead_booking_days
    target_date = (datetime.now() + timedelta(days=max_ahead_days)).strftime("%Y-%m-%d")

    logger.info(f"Scheduler running booking job for {library} spot {spot} on {target_date} from {time_start} to {time_end}")

    cmd = [
        sys.executable,
        "-m", "app.main",
        str(library),
        str(spot),
        target_date,
        str(time_start),
        str(time_end)
    ]

    try:
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            logger.info(f"Subprocess stdout:\n{result.stdout}")
        if result.stderr.strip():
            logger.warning(f"Subprocess stderr:\n{result.stderr}")
        logger.info("Subprocess finished successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess failed with exit code {e.returncode}:\n{e.stderr}\nOutput:\n{e.stdout}")
    except Exception as e:
        logger.exception("An error occurred while running the subprocess.")

if __name__ == "__main__":
    check = load_dotenv()
    if not check:
        logger.error("Failed to load .env file. Exiting.")
        sys.exit(1)

    logger.info("---------------- Scheduler started ----------------")

    # Read the scheduled time from environment, default to 04:00
    schedule_time = os.getenv("SCHEDULE_TIME", "04:00")
    logger.info(f"Configuring daily run at {schedule_time}...")

    _ = schedule.every().day.at(schedule_time).do(run_bot)

    # Optional: run immediately on start for testing if configured
    if os.getenv("RUN_ON_STARTUP", "false").lower() == "true":
        logger.info("RUN_ON_STARTUP is set. Running job now...")
        run_bot()

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped manually.")
