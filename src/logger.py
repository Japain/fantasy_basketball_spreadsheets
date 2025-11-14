"""
Logging configuration for Fantasy Basketball application.

Provides a centralized logger with console and file output.
"""

import logging
import sys
from pathlib import Path
from config import config


def setup_logger(name: str = "fantasy_basketball") -> logging.Logger:
    """
    Set up and configure application logger.

    Args:
        name: Logger name (default: "fantasy_basketball")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    # Set log level from config
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    simple_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s"
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (if we want to add file logging later)
    # Uncomment to enable file logging
    # log_dir = Path(config.BASE_DIR) / "logs"
    # log_dir.mkdir(exist_ok=True)
    # file_handler = logging.FileHandler(log_dir / "fantasy_basketball.log")
    # file_handler.setLevel(log_level)
    # file_handler.setFormatter(detailed_formatter)
    # logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Create default logger instance
logger = setup_logger()


def get_logger(name: str = "fantasy_basketball") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
