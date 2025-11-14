"""
Configuration management for Fantasy Basketball application.

Loads configuration from environment variables and provides defaults.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Base directory (project root)
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """
    Application configuration class.

    Loads settings from environment variables with sensible defaults.
    """

    # Yahoo API Configuration
    YAHOO_CONSUMER_KEY: Optional[str] = os.getenv("YAHOO_CONSUMER_KEY")
    YAHOO_CONSUMER_SECRET: Optional[str] = os.getenv("YAHOO_CONSUMER_SECRET")

    # League Configuration
    NBA_LEAGUE_ID: Optional[str] = os.getenv("NBA_LEAGUE_ID")
    NBA_GAME_ID: str = os.getenv("NBA_GAME_ID", "449")  # Default to 2024-2025 season
    GAME_CODE: str = "nba"

    # Google API Configuration
    GOOGLE_CREDENTIALS_PATH: str = os.getenv(
        "GOOGLE_CREDENTIALS_PATH",
        str(BASE_DIR / "credentials" / "google_credentials.json")
    )

    # Application Directories
    CACHE_DIR: str = os.getenv("CACHE_DIR", str(BASE_DIR / "league_data"))
    CREDENTIALS_DIR: str = str(BASE_DIR / "credentials")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate that all required configuration is present.

        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []

        if not cls.YAHOO_CONSUMER_KEY:
            errors.append("YAHOO_CONSUMER_KEY is not set in .env")

        if not cls.YAHOO_CONSUMER_SECRET:
            errors.append("YAHOO_CONSUMER_SECRET is not set in .env")

        if not cls.NBA_LEAGUE_ID:
            errors.append("NBA_LEAGUE_ID is not set in .env")

        return (len(errors) == 0, errors)

    @classmethod
    def get_yahoo_auth_dir(cls) -> str:
        """Get the directory for Yahoo OAuth token storage."""
        return cls.CACHE_DIR

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        Path(cls.CACHE_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.CREDENTIALS_DIR).mkdir(parents=True, exist_ok=True)


# Create a default config instance
config = Config()
