# main.py
# This is the main execution point for the Afflubot application.
# It parses command-line arguments and orchestrates the booking process.

import argparse
import sys
import time
from datetime import datetime, timedelta

import core
from locations import LIBRARY_MAP

# --- Constants ---
# How many days you can book ahead from today based on library rules.
MAX_AHEAD_BOOKING_DAYS = 7
# The maximum number of hours in a booking chunk.
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

    args = parser.parse_args()

    # --- 1. Find the Spot ID ---
    library_map = LIBRARY_MAP.get(args.library_name)
    if not library_map:
        print(
            f"Error: Library '{args.library_name}' not found in locations.py. Please add it to LIBRARY_MAP."
        )
        sys.exit(1)

    spot_id = library_map.get(args.spot_number)
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
    for i in range(MAX_AHEAD_BOOKING_DAYS):
        current_date = booking_start_date + timedelta(days=i)
        current_date_str = current_date.strftime("%Y-%m-%d")
        print(f"--- Processing Date: {current_date_str} ---")

        current_time_dt = day_start_dt
        while current_time_dt < day_end_dt:
            remaining_time = day_end_dt - current_time_dt
            # Convert remaining time to total hours
            remaining_hours = remaining_time.total_seconds() / 3600

            if remaining_hours <= 0:
                break

            # Decide the duration for the current booking chunk
            if remaining_hours >= BOOKING_CHUNK_HOURS:
                duration = BOOKING_CHUNK_HOURS
            else:
                duration = remaining_hours

            start_time_str = current_time_dt.strftime("%H:%M")
            print(
                f"Attempting to book spot {args.spot_number} on {current_date_str} from {start_time_str} for {duration} hours."
            )

            print(f"spot_id: {spot_id}, current_date_str: {current_date_str}, start_time_str: {start_time_str}, duration: {duration}")
            # # Call the core booking function
            # core.book_library_spot(
            #     library_id=str(spot_id),
            #     date=current_date_str,
            #     start_time=start_time_str,
            #     duration_hours=duration,
            # )

            # Move to the next time slot
            current_time_dt += timedelta(hours=duration)

            # Add a small delay between bookings to avoid rate limiting
            time.sleep(5)


if __name__ == "__main__":
    main()
