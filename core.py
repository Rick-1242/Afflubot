# core.py
# This file contains the core functions for booking a library spot through the Affluences platform.

import email
import imaplib
import json
import os
import random
import re
import time
from email.header import decode_header

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()  # pyright: ignore[reportUnusedCallResult]

# Get credentials securely from environment variables
IMAP_SERVER = os.environ.get("IMAP_SERVER")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# --- Helper Functions ---


def get_random_user_agent():
    """Returns a random User-Agent string to mimic a real browser."""
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
    ]
    return random.choice(user_agent_list)


def create_reservation(
    library_id: str, date: str, start_time: str, end_time: str, email_address: str
) -> bool:
    """
    Sends the initial reservation request to the Affluences API.

    Args:
        library_id: The ID of the library. Found by inspecting network traffic on the library's booking page.
        date: The desired date in "YYYY-MM-DD" format.
        start_time: The desired start time in "HH:MM" format.
        end_time: The desired end time in "HH:MM" format.
        email_address: The email to send the confirmation link to.

    Returns:
        True if the request was sent successfully (HTTP 200), False otherwise.
    """
    url = f"https://reservation.affluences.com/api/reserve/{library_id}"
    payload = {
        "auth_type": None,
        "email": email_address,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "note": None,
        "user_firstname": None,
        "user_lastname": None,
        "user_phone": None,
        "person_count": 1,
    }
    headers = {
        "User-Agent": get_random_user_agent(),
        "Referer": "https://affluences.com/",
        "Origin": "https://affluences.com",
        "x-service-name": "website",
    }

    # --- Logging for debugging ---
    try:
        log_content = "--- Request Details ---\n"
        log_content += f"URL: {url}\n\n"
        log_content += f"Headers:\n{json.dumps(headers, indent=2)}\n\n"
        log_content += f"Payload:\n{json.dumps(payload, indent=2)}\n"
        with open("requests.log", "a") as f:
            _ = f.write(log_content)
        print("Request details have been written to request.log")
    except Exception as e:
        print(f"Error writing to log file: {e}")
    # --- End Logging ---

    print(f"Sending reservation request for {date} from {start_time} to {end_time}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        print(
            "Reservation request sent successfully. Please check your email for a confirmation link."
        )
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending reservation request: {e}")
        print(f"Response content: {e.response.text if e.response else 'No response'}")
        return False


# def find_confirmation_link(email_address: str, password: str, imap_server: str) -> str | None:
#     """
#     Logs into an email account, finds the latest Affluences confirmation email,
#     and extracts the confirmation link.

#     **SECURITY WARNING**: This function handles email credentials directly.
#     It is safer to use environment variables or other secrets management tools.

#     Args:
#         email_address: The user's email address.
#         password: The user's email password or an app-specific password.
#         imap_server: The IMAP server address for the email provider.

#     Returns:
#         The confirmation URL if found, otherwise None.
#     """
#     print("Connecting to email server to find confirmation link...")
#     try:
#         imap = imaplib.IMAP4_SSL(imap_server)
#         imap.login(email_address, password)
#         imap.select("INBOX")

#         # Search for unread emails from 'no-reply@affluences.com' with the subject "Confirm your reservation"
#         status, messages = imap.search(None, '(UNSEEN FROM "no-reply@affluences.com" SUBJECT "Confirm your reservation")')
#         if status != "OK":
#             print("Failed to search for emails.")
#             return None

#         message_ids = messages[0].split()
#         if not message_ids:
#             print("No new Affluences confirmation emails found.")
#             return None

#         # Fetch the most recent email
#         latest_id = message_ids[-1]
#         res, msg_data = imap.fetch(latest_id, "(RFC822)")

#         for response_part in msg_data:
#             if isinstance(response_part, tuple):
#                 msg = email.message_from_bytes(response_part[1])

#                 # Find the HTML part of the email
#                 if msg.is_multipart():
#                     for part in msg.walk():
#                         if part.get_content_type() == "text/html":
#                             body = part.get_payload(decode=True).decode()
#                             break
#                 else:
#                     body = msg.get_payload(decode=True).decode()

#                 # Parse the HTML and find the confirmation link
#                 soup = BeautifulSoup(body, 'html.parser')
#                 # The confirmation link is usually the first link in the email body
#                 for link in soup.findAll('a'):
#                     href = link.get('href')
#                     if href and "affluences.com/reservation/confirm?reservationToken=" in href:
#                         print("Found confirmation link.")
#                         return href

#         print("Could not find a confirmation link in the latest email.")
#         return None

#     except Exception as e:
#         print(f"An error occurred while fetching email: {e}")
#         return None
#     finally:
#         if 'imap' in locals() and imap.state == 'SELECTED':
#             imap.close()
#             imap.logout()

# def confirm_reservation(confirmation_url: str) -> bool:
#     """
#     Visits the confirmation URL and sends the final API request to confirm the booking.

#     Args:
#         confirmation_url: The full confirmation URL from the email.

#     Returns:
#         True if the confirmation was successful, False otherwise.
#     """
#     print("Attempting to confirm reservation...")
#     try:
#         # Extract the reservation token from the URL
#         token_match = re.search(r'reservationToken=([a-f0-9\-]+)', confirmation_url)
#         if not token_match:
#             print("Invalid confirmation URL: token not found.")
#             return False

#         token = token_match.group(1)

#         # The API endpoint for confirmation is different from the link in the email
#         api_confirm_url = f"https://reservation.affluences.com/api/reservations/{token}/confirmation"

#         headers = {
#             "Accept": "application/json, text/plain, */*",
#             "Content-Type": "application/json",
#             "Origin": "https://affluences.com",
#             "Referer": "https://affluences.com/",
#             "User-Agent": get_random_user_agent()
#         }

#         # The confirmation API requires a POST request with an empty JSON body
#         response = requests.post(api_confirm_url, json={}, headers=headers, timeout=10)
#         response.raise_for_status()

#         print("Reservation confirmed successfully!")
#         return True

#     except requests.exceptions.RequestException as e:
#         print(f"Error confirming reservation: {e}")
#         print(f"Response content: {e.response.text if e.response else 'No response'}")
#         return False

# --- Main Orchestration Function ---


def book_library_spot(library_id: str, date: str, start_time: str):
    """
    Main function to orchestrate the entire booking process for a 2-hour slot.

    1. Sends the initial reservation request.
    2. Waits and searches for the confirmation email.
    3. Follows the confirmation link to finalize the booking.
    """
    # The bot always books a 2-hour slot as per the requirements.
    hour, minute = map(int, start_time.split(":"))
    end_time = f"{hour + 2:02d}:{minute:02d}"

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print(
            "ERROR: Credentials not found. Make sure you have a .env file with EMAIL_ADDRESS and EMAIL_PASSWORD."
        )
        return

    # Step 1: Create the initial reservation
    if not create_reservation(library_id, date, start_time, end_time, EMAIL_ADDRESS):
        return  # Stop if the initial request fails

    # Step 2: Find the confirmation link in the email
    # It can take a minute for the email to arrive. We'll wait and retry.
    print("Waiting for confirmation email to arrive...")
    # confirmation_link = None
    # for i in range(5): # Retry 5 times over 50 seconds
    #     time.sleep(10)
    #     print(f"Checking for email (Attempt {i+1}/5)...")
    #     confirmation_link = find_confirmation_link(EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER)
    #     if confirmation_link:
    #         break

    # if not confirmation_link:
    #     print("Could not find confirmation email after several attempts. Please check your inbox manually.")
    #     return

    # # Step 3: Confirm the reservation
    # confirm_reservation(confirmation_link)


# --- Example Usage ---
if __name__ == "__main__":
    # This is an example of how to use the book_library_spot function.
    # You will need to replace the placeholder values with real ones.

    # IMPORTANT: To find the library_id:
    # 1. Go to your library's booking page on affluences.com.
    # 2. Open your browser's Developer Tools (F12 or Ctrl+Shift+I).
    # 3. Go to the "Network" tab.
    # 4. Complete a reservation manually.
    # 5. Look for a request to a URL like '.../api/reserve/12345'. The number is your library_id.

    EXAMPLE_LIBRARY_ID = (
        "69370"  # This is an example for Rimini, replace it with yours.
    )
    EXAMPLE_DATE = "2026-03-24"  # Replace with the desired date
    EXAMPLE_START_TIME = "09:00"  # Replace with the desired start time

    print("--- Starting Library Booking Bot ---")
    book_library_spot(
        library_id=EXAMPLE_LIBRARY_ID, date=EXAMPLE_DATE, start_time=EXAMPLE_START_TIME
    )
    print("--- Library Booking Bot Finished ---")
