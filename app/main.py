# main.py
# This is the main entry point for the Afflubot application.
# It parses command-line arguments and orchestrates the booking process.

import argparse
import sys
import time
from datetime import datetime, timedelta

from . import core
from .locations import LIBRARY_DATA
from .logging_config import setup_logging

logger = setup_logging()

def main():
    """
    The main function to parse arguments and run the booking loops.
    """
    parser = argparse.ArgumentParser(
        description="Automated booking bot for Affluences library spots."
    )
    _ = parser.add_argument(
        "library_name",
        type=str,
        help="The name of the library (e.g., 'Meneghetti'). Must match a key in locations.py.",
    )
    _ = parser.add_argument("spot_number", type=int, help="The desired spot number.")
    _ = parser.add_argument(
        "start_date", type=str, help="The first date to book, in YYYY-MM-DD format."
    )
    _ = parser.add_argument(
        "day_start_time",
        type=str,
        help="The time to start booking from each day, in HH:MM format.",
    )
    _ = parser.add_argument(
        "day_end_time",
        type=str,
        help="The time to end booking at each day, in HH:MM format.",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the booking process without making real requests.",
    )

    args = parser.parse_args()

    # Create a context dictionary for logging
    log_context = {
        "library_name": args.library_name,
        "spot_number": args.spot_number,
        "start_date": args.start_date,
        "day_start_time": args.day_start_time,
        "day_end_time": args.day_end_time,
        "dry_run": args.dry_run,
    }
    logger.info("Application starting.", extra={'context': log_context})

    if args.dry_run:
        logger.info("*** DRY RUN MODE ENABLED: No actual bookings will be made. ***")

    try:
        # --- 1. Find the Library Data and Spot ID ---
        library_data = LIBRARY_DATA.get(args.library_name)
        if not library_data:
            logger.error(
                f"Library '{args.library_name}' not found in locations.py. Please add it to LIBRARY_DATA.",
                extra={'context': log_context}
            )
            sys.exit(1)

        # --- 1a. Validate Library Data Structure ---
        required_keys = ["spots", "hours", "max_ahead_booking_days", "booking_chunk_hours"]
        for key in required_keys:
            if key not in library_data:
                logger.error(
                    f"Library data for '{args.library_name}' is missing required key: '{key}' in locations.py.",
                    extra={'context': log_context}
                )
                sys.exit(1)

        if not isinstance(library_data["spots"], dict):
            logger.error(f"'spots' for library '{args.library_name}' should be a dictionary.", extra={'context': log_context})
            sys.exit(1)

        if not isinstance(library_data["hours"], dict):
            logger.error(f"'hours' for library '{args.library_name}' should be a dictionary.", extra={'context': log_context})
            sys.exit(1)

        if not isinstance(library_data["max_ahead_booking_days"], int):
            logger.error(f"'max_ahead_booking_days' for '{args.library_name}' should be an integer.", extra={'context': log_context})
            sys.exit(1)

        if not isinstance(library_data["booking_chunk_hours"], int):
            logger.error(f"'booking_chunk_hours' for '{args.library_name}' should be an integer.", extra={'context': log_context})
            sys.exit(1)

        spot_id = library_data["spots"].get(args.spot_number)
        if not spot_id:
            logger.error(
                f"Spot number {args.spot_number} not found for library '{args.library_name}' in locations.py.",
                extra={'context': log_context}
            )
            sys.exit(1)

        # Extract library-specific constants
        max_ahead_booking_days = library_data["max_ahead_booking_days"]
        booking_chunk_hours = library_data["booking_chunk_hours"]

        log_context['spot_id'] = spot_id
        logger.info(f"Successfully validated library and spot.", extra={'context': log_context})

        # --- 2. Set up Date and Time Loops ---
        booking_start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        day_start_dt = datetime.strptime(args.day_start_time, "%H:%M")
        day_end_dt = datetime.strptime(args.day_end_time, "%H:%M")

        # --- 3. Run the Booking Loops ---
        today = datetime.now().date()
        max_allowed_date = today + timedelta(days=max_ahead_booking_days)

        current_date = booking_start_date
        while current_date <= max_allowed_date:
            # Skip dates that are in the past
            if current_date < today:
                current_date += timedelta(days=1)
                continue

            current_date_str = current_date.strftime("%Y-%m-%d")
            day_of_week = current_date.weekday()  # Monday is 0 and Sunday is 6
            date_context = {**log_context, 'process_date': current_date_str}
            logger.info(f"---------------- Processing date: {current_date_str} ----------------", extra={'context': date_context})

            # --- Opening Hours Validation ---
            library_hours_today = library_data["hours"].get(day_of_week)
            if not library_hours_today:
                logger.warning("Library is closed on this day, skipping.", extra={'context': date_context})
                current_date += timedelta(days=1)
                continue

            open_time_str, close_time_str = library_hours_today
            open_time_dt = datetime.strptime(open_time_str, "%H:%M")
            close_time_dt = datetime.strptime(close_time_str, "%H:%M")

            if day_start_dt < open_time_dt or day_end_dt > close_time_dt:
                hours_context = {**date_context, 'opening_hours': f"{open_time_str}-{close_time_str}"}
                logger.warning(
                    "Requested time window is outside of opening hours, skipping.",
                    extra={'context': hours_context}
                )
                current_date += timedelta(days=1)
                continue
            # --- End Validation ---

            current_time_dt = day_start_dt
            while current_time_dt < day_end_dt:
                remaining_time = day_end_dt - current_time_dt
                remaining_hours = remaining_time.total_seconds() / 3600

                if remaining_hours <= 0:
                    break

                duration = min(remaining_hours, booking_chunk_hours)
                start_time_str = current_time_dt.strftime("%H:%M")
                end_time_dt = current_time_dt + timedelta(hours=duration)
                end_time_str = end_time_dt.strftime("%H:%M")

                booking_context = {
                    **date_context,
                    "start_time": start_time_str,
                    "end_time": end_time_str
                }

                if args.dry_run:
                    logger.info("[DRY RUN] Would attempt to book spot.", extra={'context': booking_context})
                else:
                    core.book_library_spot(
                        library_id=str(spot_id),
                        date=current_date_str,
                        start_time=start_time_str,
                        end_time=end_time_str,
                        booking_context=booking_context # Pass context to core
                    )

                current_time_dt = end_time_dt

                if not args.dry_run:
                    time.sleep(3)

            current_date += timedelta(days=1)

    except (ValueError, KeyError) as e:
        logger.error(f"Configuration or input error: {e}", extra={'context': log_context})
        sys.exit(1)
    except Exception as e:
        logger.exception("An unhandled exception occurred during main execution.", extra={'context': log_context})
        sys.exit(1)
    finally:
        logger.info("Application finished.", extra={'context': log_context})


if __name__ == "__main__":
    main()
