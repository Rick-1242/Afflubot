# core.py
# This file contains the core function for booking a library spot through the Affluences platform. See below

import os
import re
import time
import email
import imaplib
import logging
import requests
from typing import Any
from random import choice
from dotenv import load_dotenv

# Get the logger instance from the logging_config
logger = logging.getLogger('afflubot')

# Get credentials securely from environment variables
_ = load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def get_random_user_agent() -> str:
    """Returns a random User-Agent string to mimic a real browser."""
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
    ]
    return choice(user_agent_list)


def create_reservation(
    library_id: str, date: str, start_time: str, end_time: str, email_address: str, booking_context: dict[str, Any]
) -> bool:
    """
    Sends the initial reservation request to the Affluences API.
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

    api_context = {**booking_context, 'api_url': url, 'api_payload': payload}
    logger.info("Sending reservation request.", extra={'context': api_context})

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)

        logger.info("Reservation request sent successfully.", extra={'context': api_context})
        return True
    except requests.exceptions.RequestException as e:
        error_context = {
            **api_context,
            'response_text': e.response.text if e.response else 'No response',
            'status_code': e.response.status_code if e.response else None
        }
        logger.error(f"Error sending reservation request: {e}", extra={'context': error_context})
        return False


def find_confirmation_link(
    email_address: str, password: str, imap_server: str, booking_context: dict[str, Any]
) -> str | None:
    """
    Logs into an email account, finds the latest Affluences confirmation email,
    and extracts the confirmation link.
    """
    imap = None
    email_context = {**booking_context, 'imap_server': imap_server, 'email_address': email_address}
    logger.info("Connecting to IMAP server.", extra={'context': email_context})
    try:
        imap = imaplib.IMAP4_SSL(imap_server)
        _ = imap.login(email_address, password)
        _ = imap.select("INBOX")
        logger.info("Successfully connected and logged into IMAP server.", extra={'context': email_context})

        status, messages_data = imap.search(
            None,
            '(UNSEEN FROM "no-reply@affluences.com" SUBJECT "Confirm your reservation")',
        )
        if status != "OK":
            logger.error("Failed to search for emails.", extra={'context': email_context})
            return None

        message_ids = messages_data[0].split()
        if not message_ids:
            logger.info("No new Affluences confirmation emails found.", extra={'context': email_context})
            return None

        latest_id = message_ids[-1]
        _status, msg_data = imap.fetch(latest_id, "(RFC822)")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                body: str = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

                if not body:
                    continue

                match = re.search(
                    r"(https://affluences\.com/reservation/confirm\?reservationToken=[a-f0-9\-]+)",
                    body,
                )

                if match:
                    confirmation_link = match.group(0)
                    logger.info("Found confirmation link in email.", extra={'context': {**email_context, 'confirmation_link': confirmation_link}})
                    return confirmation_link

        logger.warning("Could not find a confirmation link in the latest email.", extra={'context': email_context})
        return None

    except Exception as e:
        logger.exception("An error occurred while fetching email.", extra={'context': email_context})
        return None
    finally:
        if imap and imap.state == "SELECTED":
            _ = imap.close()
            _ = imap.logout()
            logger.info("IMAP connection closed.", extra={'context': email_context})


def confirm_reservation(confirmation_url: str, booking_context: dict[str, Any]) -> bool:
    """
    Visits the confirmation URL to finalize the booking.
    """
    confirm_context = {**booking_context, 'confirmation_url': confirmation_url}
    logger.info("Attempting to confirm reservation.", extra={'context': confirm_context})
    try:
        token_match = re.search(r"reservationToken=([a-f0-9\-]+)", confirmation_url)
        if not token_match:
            logger.error("Invalid confirmation URL: token not found.", extra={'context': confirm_context})
            return False

        token = token_match.group(1)
        api_confirm_url = f"https://reservation.affluences.com/api/reservations/{token}/confirmation"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://affluences.com",
            "Referer": "https://affluences.com/",
            "User-Agent": get_random_user_agent(),
        }

        response = requests.post(api_confirm_url, json={}, headers=headers, timeout=10)
        response.raise_for_status()

        logger.info("Reservation confirmed successfully!", extra={'context': confirm_context})
        return True

    except requests.exceptions.RequestException as e:
        error_context = {
            **confirm_context,
            'response_text': e.response.text if e.response else 'No response',
            'status_code': e.response.status_code if e.response else None
        }
        logger.error(f"Error confirming reservation: {e}", extra={'context': error_context})
        return False


# --- Main Orchestration Function ---


def book_library_spot(
    library_id: str, date: str, start_time: str, end_time: str, booking_context: dict[str, Any]
) -> None:
    """
    Main function to orchestrate the entire booking process for a library spot.
    """
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD or not IMAP_SERVER:
        logger.error(
            "Email credentials/server not found in .env file (EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER).",
            extra={'context': booking_context}
        )
        return

    if not create_reservation(library_id, date, start_time, end_time, EMAIL_ADDRESS, booking_context):
        logger.warning("Stopping process because initial reservation request failed.", extra={'context': booking_context})
        return

    logger.info("Waiting for confirmation email to arrive...", extra={'context': booking_context})
    confirmation_link = None
    for i in range(5):  # Retry 5 times over ~50 seconds
        time.sleep(5)
        logger.info(f"Checking for email (Attempt {i + 1}/5)...", extra={'context': booking_context})

        confirmation_link = find_confirmation_link(
            EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER, booking_context
        )
        if confirmation_link:
            break

    if not confirmation_link:
        logger.error(
            "Could not find confirmation email after several attempts. Please check inbox manually.",
            extra={'context': booking_context}
        )
        return

    _ = confirm_reservation(confirmation_link, booking_context)


# --- Example Usage ---
if __name__ == "__main__":
    # This block is for direct execution, setting up a basic logger for that case.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("You are running the the core library booking script, please run the main script to start booking.")
