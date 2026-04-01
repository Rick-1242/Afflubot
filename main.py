# main.py
# This is the main entry point for the Afflubot application.
# It parses command-line arguments and orchestrates the booking process.

import argparse
import sys
import time
from datetime import datetime, timedelta

import core
from locations import LIBRARY_DATA

# --- Constants ---
# How many days ahead to book from today.
MAX_AHEAD_BOOKING_DAYS = 7
# The size of the primary booking chunks in hours.
BOOKING_CHUNK_HOURS = 3


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

    if args.dry_run:
        print("*** DRY RUN MODE ENABLED: No actual bookings will be made. ***")

    # --- 1. Find the Library Data and Spot ID ---
    library_data = LIBRARY_DATA.get(args.library_name)
    if not library_data:
        print(
            f"Error: Library '{args.library_name}' not found in locations.py. Please add it to LIBRARY_DATA."
        )
        sys.exit(1)

    spot_id = library_data["spots"].get(args.spot_number)
    if not spot_id:
        print(
            f"Error: Spot number {args.spot_number} not found for library '{args.library_name}' in locations.py."
        )
        sys.exit(1)

    print(
        f"Found Spot ID: {spot_id} for Library: {args.library_name}, Spot: {args.spot_number}"
    )

    # --- 2. Set up Date and Time Loops ---
    try:
        booking_start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        day_start_dt = datetime.strptime(args.day_start_time, "%H:%M")
        day_end_dt = datetime.strptime(args.day_end_time, "%H:%M")
    except ValueError as e:
        print(f"Error: Invalid date or time format. {e}")
        sys.exit(1)

    # --- 3. Run the Booking Loops ---
    today = datetime.now().date()
    max_allowed_date = today + timedelta(days=MAX_AHEAD_BOOKING_DAYS)

    current_date = booking_start_date
    while current_date <= max_allowed_date:
        # Skip dates that are in the past
        if current_date < today:
            current_date += timedelta(days=1)
            continue

        current_date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.weekday()  # Monday is 0 and Sunday is 6

        print(f"\n--- Processing Date: {current_date_str} ---")

        # --- Opening Hours Validation ---
        library_hours_today = library_data["hours"].get(day_of_week)
        if not library_hours_today:
            print(f"Skipping: Library is closed on this day.")
            current_date += timedelta(days=1)
            continue

        # Validate the data structure from locations.py before unpacking
        if not isinstance(library_hours_today, tuple) or len(library_hours_today) != 2:
            print(f"!!! DATA ERROR in locations.py !!!")
            print(f"On {current_date_str} (day {day_of_week}), the hours data is invalid.")
            print(f"Expected a format like ('HH:MM', 'HH:MM'), but got: {library_hours_today}")
            sys.exit(1)

        open_time_str, close_time_str = library_hours_today
        open_time_dt = datetime.strptime(open_time_str, "%H:%M")
        close_time_dt = datetime.strptime(close_time_str, "%H:%M")

        if day_start_dt < open_time_dt or day_end_dt > close_time_dt:
            print(
                f"Skipping: Requested time window {args.day_start_time}-{args.day_end_time} is outside of " +
                f"opening hours ({open_time_str}-{close_time_str})."
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

            duration = min(remaining_hours, BOOKING_CHUNK_HOURS)
            start_time_str = current_time_dt.strftime("%H:%M")
            end_time_dt = current_time_dt + timedelta(hours=duration)
            end_time_str = end_time_dt.strftime("%H:%M")

            if args.dry_run:
                print(f"[DRY RUN] Would book spot {args.spot_number} on {current_date_str}:")
                print(f"  - Library ID: {spot_id}")
                print(f"  - Start: {start_time_str}")
                print(f"  - End:   {end_time_str}")
            else:
                print(
                    f"Attempting to book spot {args.spot_number} on {current_date_str} from {start_time_str} to {end_time_str}."
                )
                core.book_library_spot(
                    library_id=str(spot_id),
                    date=current_date_str,
                    start_time=start_time_str,
                    end_time=end_time_str,
                )

            current_time_dt = end_time_dt

            if not args.dry_run:
                time.sleep(5)

        current_date += timedelta(days=1)


if __name__ == "__main__":
    main()
