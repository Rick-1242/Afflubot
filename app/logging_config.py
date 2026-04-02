import logging
import logging.handlers
import json
import os
import sys
from typing import Any

# Ensure the logs directory exists
log_dir = '../logs/'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

class JsonFormatter(logging.Formatter):
    """
    Custom formatter to output log records as JSON.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Create a log record dictionary
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Add extra context if it exists
        if hasattr(record, 'context'):
            log_record['context'] = getattr(record, 'context')

        # Add exception info if it exists
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        # Add stack info if it exists
        if record.stack_info:
            log_record['stack_info'] = self.formatStack(record.stack_info)

        return json.dumps(log_record)

def setup_logging() -> logging.Logger:
    """
    Sets up the 'afflubot' logger with a JSON file handler and a
    simple stream handler for console output.
    """
    logger = logging.getLogger('afflubot')
    # Prevent messages from being propagated to the root logger
    logger.propagate = False

    # Set the lowest level for the logger to handle
    logger.setLevel(logging.INFO)

    # If handlers are already configured, don't add them again
    if logger.hasHandlers():
        return logger

    # --- 1. File Handler (JSON) ---
    log_file = os.path.join(log_dir, 'events.log')
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=7
    )
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # --- 2. Console Handler (Human-readable) ---
    console_handler = logging.StreamHandler(sys.stdout)
    # Use a simple formatter for the console
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger
