import logging
import os
from typing import Dict, Any

import colorlog
import yaml


# Global formatting for all loggers
log_colors = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white",
}

# Formatter for INFO and WARNING levels
simple_formatter = colorlog.ColoredFormatter(
    fmt="%(log_color)s[%(asctime)s, %(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors=log_colors,
)

# Formatter for DEBUG, ERROR, and CRITICAL levels
detailed_formatter = colorlog.ColoredFormatter(
    fmt="%(log_color)s%(asctime)s [%(levelname)s] %(message)s\n    ⤷ In %(module)s:%(lineno)d, %(funcName)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors=log_colors,
)


class CustomHandler(logging.StreamHandler):
    """
    Handles the different styles of logging messages with respect to their level.
    """

    def format(self, record) -> str:
        """
        Formats the data with respect to the level. Uses the simple format for INFO and WARNING messages,
        for all other levels, the detailed format is used.

        Args:
            record: record to be formatted

        Returns:
            formatted logging info
        """
        if record.levelno in (logging.INFO, logging.WARNING):
            return simple_formatter.format(record)
        return detailed_formatter.format(record)


def get_logger(module_name: str = "base") -> logging.Logger:
    """
    Creates or retrieves a logger for a specific module.

    Args:
        module_name (str): Name of the module (as defined in config.yaml)

    Returns:
        Configured logger for the module
    """
    logger = logging.getLogger(module_name)

    if logger.hasHandlers():
        logger.handlers.clear()

    # Prevent multiple handler additions
    if not logger.handlers:
        handler = CustomHandler()
        logger.addHandler(handler)

    # Default to base debug setting
    debug_enabled = False

    logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)

    return logger
