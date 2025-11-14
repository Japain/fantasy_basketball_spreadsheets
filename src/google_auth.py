"""Google API authentication module for Google Sheets integration.

This module handles OAuth 2.0 authentication with Google APIs and provides
a service object for interacting with Google Sheets.
"""

import os
import pickle
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.logger import get_logger

logger = get_logger(__name__)

# Google API scopes - we need full access to Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Token storage location
TOKEN_FILE = 'credentials/google_token.pickle'


class GoogleAuthError(Exception):
    """Exception raised for Google authentication errors."""
    pass


def get_google_sheets_service(credentials_path: Optional[str] = None, token_file: Optional[str] = None):
    """
    Authenticate with Google API and return a Google Sheets service object.

    This function handles the complete OAuth 2.0 flow:
    1. Check if valid tokens exist and use them
    2. If tokens are expired, refresh them
    3. If no valid tokens, initiate OAuth flow
    4. Save tokens for future use

    Args:
        credentials_path: Path to the Google OAuth credentials JSON file.
                         If None, uses GOOGLE_CREDENTIALS_PATH from config.
        token_file: Path to store/retrieve the authentication token.
                   If None, uses default TOKEN_FILE location.

    Returns:
        A Google Sheets API service object.

    Raises:
        GoogleAuthError: If authentication fails or credentials are invalid.
        FileNotFoundError: If credentials file doesn't exist.
    """
    logger.info("Initializing Google Sheets authentication...")

    # Use provided paths or defaults
    if credentials_path is None:
        from config import Config
        credentials_path = Config.GOOGLE_CREDENTIALS_PATH

    if token_file is None:
        token_file = TOKEN_FILE

    # Validate credentials file exists
    if not os.path.exists(credentials_path):
        error_msg = f"Google credentials file not found at: {credentials_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.debug(f"Using credentials file: {credentials_path}")
    logger.debug(f"Token file location: {token_file}")

    creds = None

    # Try to load existing tokens
    if os.path.exists(token_file):
        logger.info("Found existing token file, attempting to load...")
        try:
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
            logger.info("Successfully loaded existing credentials")
        except Exception as e:
            logger.warning(f"Failed to load existing token: {e}")
            creds = None

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired credentials
            logger.info("Credentials expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                logger.info("Successfully refreshed credentials")
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                logger.info("Will attempt to re-authenticate...")
                creds = None

        if not creds:
            # No valid credentials - initiate OAuth flow
            logger.info("Starting OAuth 2.0 authentication flow...")
            logger.info("A browser window will open for authentication.")

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)

                # Run local server for OAuth callback
                # This will open a browser window for user authentication
                creds = flow.run_local_server(port=0)
                logger.info("Successfully authenticated with Google")

            except Exception as e:
                error_msg = f"OAuth flow failed: {e}"
                logger.error(error_msg)
                raise GoogleAuthError(error_msg) from e

        # Save credentials for future use
        logger.info(f"Saving credentials to {token_file}...")
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(token_file), exist_ok=True)

            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Credentials saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")
            # Non-fatal - we can still proceed with the current session

    # Build and return the service
    try:
        logger.info("Building Google Sheets API service...")
        service = build('sheets', 'v4', credentials=creds)
        logger.info("Google Sheets service created successfully")
        return service

    except HttpError as e:
        error_msg = f"Failed to build Google Sheets service: {e}"
        logger.error(error_msg)
        raise GoogleAuthError(error_msg) from e


def test_authentication(credentials_path: Optional[str] = None) -> bool:
    """
    Test Google authentication by creating a service object.

    Args:
        credentials_path: Path to Google OAuth credentials JSON file.

    Returns:
        True if authentication successful, False otherwise.
    """
    try:
        service = get_google_sheets_service(credentials_path)
        logger.info("✓ Google authentication test PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Google authentication test FAILED: {e}")
        return False


if __name__ == "__main__":
    # Test authentication when run directly
    print("Testing Google Sheets authentication...")
    success = test_authentication()

    if success:
        print("\n✓ Authentication successful!")
        print("You can now use the Google Sheets API.")
    else:
        print("\n✗ Authentication failed!")
        print("Please check your credentials and try again.")
