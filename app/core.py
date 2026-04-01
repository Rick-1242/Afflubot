# core.py
# This file contains the core function for booking a library spot through the Affluences platform. See below

import os
import re
import json
import time
import email
import random
import imaplib
import requests
from dotenv import load_dotenv


# Get credentials securely from environment variables
_ = load_dotenv()
IMAP_SERVER = os.environ.get("IMAP_SERVER")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")


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
        with open("./logs/requests.log", "a") as f:
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


def find_confirmation_link(
    email_address: str, password: str, imap_server: str
) -> str | None:
    """
    Logs into an email account, finds the latest Affluences confirmation email,
    and extracts the confirmation link from the plain text part of the email.

    **SECURITY WARNING**: This function handles email credentials directly.
    It is safer to use environment variables or other secrets management tools.

    Args:
        email_address: The user's email address.
        password: The user's email password or an app-specific password.
        imap_server: The IMAP server address for the email provider.

    Returns:
        The confirmation URL if found, otherwise None.
    """
    imap = None  # Initialize imap to None before the try block
    print("Connecting to email server to find confirmation link...")
    try:
        imap = imaplib.IMAP4_SSL(imap_server)
        _ = imap.login(email_address, password)
        _ = imap.select("INBOX")

        # Search for unread emails from 'no-reply@affluences.com' with the subject "Confirm your reservation"
        status, messages_data = imap.search(
            None,
            '(UNSEEN FROM "no-reply@affluences.com" SUBJECT "Confirm your reservation")',
        )
        if status != "OK":
            print("Failed to search for emails.")
            return None

        # messages_data[0] is a bytes object containing space-separated message IDs
        message_ids = messages_data[0].split()
        if not message_ids:
            print("No new Affluences confirmation emails found.")
            return None

        # Fetch the most recent email
        latest_id = message_ids[-1]
        # Change 'res' to '_' as it's not used
        _status, msg_data = imap.fetch(latest_id, "(RFC822)")

        # The email is multipart (text and html), we need to find the right part
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                body: str = "" # Initialize body as str

                # Prefer the plain text version as it's more reliable
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            # Decode the payload from quoted-printable or base64
                            payload = part.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                try:
                                    body = payload.decode(
                                        part.get_content_charset() or "utf-8", errors="replace"
                                    )
                                    break  # Found plain text, stop looking
                                except UnicodeDecodeError:
                                    continue
                else:
                    # Not multipart, just get the payload
                    payload = msg.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        try:
                            body = payload.decode(
                                msg.get_content_charset() or "utf-8", errors="replace"
                            )
                        except UnicodeDecodeError:
                            pass

                if not body:
                    print("Could not extract a readable body from the email.")
                    continue

                # Use regex to find the confirmation link in the decoded body
                # This is more robust than parsing HTML with tracking links
                match = re.search(
                    r"(https://affluences\.com/reservation/confirm\?reservationToken=[a-f0-9\-]+)",
                    body,
                )

                if match:
                    confirmation_link = match.group(0)
                    print("Found confirmation link.")
                    return confirmation_link

        print("Could not find a confirmation link in the latest email.")
        return None

    except Exception as e:
        print(f"An error occurred while fetching email: {e}")
        return None
    finally:
        # This check is now cleaner. It will only run if 'imap' was successfully assigned.
        if imap and imap.state == "SELECTED":
            _ = imap.close()
            _ = imap.logout()


def confirm_reservation(confirmation_url: str) -> bool:
    """
    Visits the confirmation URL and sends the final API request to confirm the booking.

    Args:
        confirmation_url: The full confirmation URL from the email.

    Returns:
        True if the confirmation was successful, False otherwise.
    """
    print("Attempting to confirm reservation...")
    try:
        # Extract the reservation token from the URL
        token_match = re.search(r"reservationToken=([a-f0-9\-]+)", confirmation_url)
        if not token_match:
            print("Invalid confirmation URL: token not found.")
            return False

        token = token_match.group(1)

        # The API endpoint for confirmation is different from the link in the email
        api_confirm_url = (
            f"https://reservation.affluences.com/api/reservations/{token}/confirmation"
        )

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://affluences.com",
            "Referer": "https://affluences.com/",
            "User-Agent": get_random_user_agent(),
        }

        # The confirmation API requires a POST request with an empty JSON body
        response = requests.post(api_confirm_url, json={}, headers=headers, timeout=10)
        response.raise_for_status()

        print("Reservation confirmed successfully!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error confirming reservation: {e}")
        print(f"Response content: {e.response.text if e.response else 'No response'}")
        return False


# --- Main Orchestration Function ---


def book_library_spot(
    library_id: str, date: str, start_time: str, end_time: str
):
    """
    Main function to orchestrate the entire booking process for a library spot.

    1. Sends the initial reservation request.
    2. Waits and searches for the confirmation email.
    3. Follows the confirmation link to finalize the booking.
    """
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
    confirmation_link = None
    for i in range(5):  # Retry 5 times over 50 seconds
        time.sleep(5)
        print(f"Checking for email (Attempt {i + 1}/5)...")
        if not IMAP_SERVER or not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            print("Email credentials not configured in .env file.")
            return
        confirmation_link = find_confirmation_link(
            EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER
        )
        if confirmation_link:
            break

    if not confirmation_link:
        print(
            "Could not find confirmation email after several attempts. Please check your inbox manually."
        )
        return

    # Step 3: Confirm the reservation
    _ = confirm_reservation(confirmation_link)


# --- Example Usage ---
if __name__ == "__main__":
    print("You are running the the core library booking script, please run the main script to start booking.")
    # IMPORTANT: To find the library_id:
    # 1. Go to your library's booking page on affluences.com.
    # 2. Open your browser's Developer Tools (F12 or Ctrl+Shift+I).
    # 3. Go to the "Network" tab.
    # 4. Complete a reservation manually.
    # 5. Look for a request to a URL like '.../api/reserve/12345'. The number is your library_id.

    # EXAMPLE_LIBRARY_ID = "5350"
    # EXAMPLE_DATE = "2026-04-03"
    # EXAMPLE_START_TIME = "15:00"
    # EXAMPLE_END_TIME = "17:00"
    #
    # print("--- Starting Library Booking Bot ---")
    # book_library_spot(
    #     library_id=EXAMPLE_LIBRARY_ID,
    #     date=EXAMPLE_DATE,
    #     start_time=EXAMPLE_START_TIME,
    #     end_time=EXAMPLE_END_TIME,
    # )
    # print("--- Library Booking Bot Finished ---")
