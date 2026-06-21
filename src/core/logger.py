"""
logger.py

Custom logging setup with a SOLVE level for solver success messages
and colorized console output using colorama.
"""

import logging
import os
import time

import colorama
from colorama import Fore, Style

colorama.init()

SOLVE_LEVEL_NUM = 25
logging.addLevelName(SOLVE_LEVEL_NUM, "SOLVE")


class CustomLogger(logging.Logger):
    """Custom logger with a SOLVE method for solver success messages."""

    def solve(self, token: str, start_time: float, *args, **kwargs):
        """
        Log a solver success message with token and elapsed time.

        Args:
            token: The captcha token (first 100 chars will be shown)
            start_time: Time when solving started (time.time() timestamp)
        """
        elapsed = round(time.time() - start_time, 2)
        msg = f"{token[:100]} [ {elapsed}s ]"
        self.log(SOLVE_LEVEL_NUM, msg, *args, **kwargs)


logging.setLoggerClass(CustomLogger)


class Formatter(logging.Formatter):
    """Custom logging formatter with dynamic coloring."""

    RED = Fore.RED + Style.BRIGHT
    GREEN = Fore.GREEN + Style.BRIGHT
    GREY = Fore.BLACK + Style.BRIGHT
    RESET = Style.RESET_ALL

    FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

    def format(self, record):
        levelname = record.levelname

        if levelname == "INFO":
            record.levelname = f"{self.GREY}{levelname}{self.RESET}"
        elif levelname == "SOLVE":
            record.levelname = f"{self.GREEN}{levelname}{self.RESET}"
        elif levelname == "WARNING":
            record.levelname = f"{Fore.YELLOW}{levelname}{self.RESET}"
        elif levelname == "ERROR":
            record.levelname = f"{self.RED}{levelname}{self.RESET}"
        elif levelname == "CRITICAL":
            record.levelname = f"{self.RED}{Style.BRIGHT}{levelname}{self.RESET}"

        record.name = f"{self.RED}{record.name}{self.RESET}"

        return super().format(record)


def setup_logger(name="Turnstile", level="INFO", log_file=None):
    """
    Initialize a logger with optional file output and configurable level.

    Args:
        name: Logger name (shown in output)
        level: Log level (DEBUG, INFO, SOLVE, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to also write logs to

    Returns:
        CustomLogger instance
    """
    logger = logging.getLogger(name)

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(Formatter(Formatter.FORMAT))
        logger.addHandler(console_handler)

        if log_file:
            try:
                if os.path.dirname(log_file):
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
                    )
                )
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"Failed to setup file logging: {e}")

    return logger
