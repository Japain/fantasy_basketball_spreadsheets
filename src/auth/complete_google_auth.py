"""Complete Google OAuth authentication with an authorization code.

Usage:
    uv run python src/auth/complete_google_auth.py <authorization_code>
"""

import os
import sys
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def complete_authentication(auth_code: str) -> bool:
    """Complete Google OAuth authentication with the provided authorization code."""

    # Get credentials path
    credentials_path = os.getenv(
        'GOOGLE_CREDENTIALS_PATH',
        'credentials/client_secret_244271698600-19dd7prtef55t0845qibik3l0t1mo0pn.apps.googleusercontent.com.json'
    )

    if not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at: {credentials_path}")
        return False

    print("Completing Google OAuth authentication...")
    print(f"Using credentials file: {credentials_path}")
    print()

    try:
        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

        # Generate auth URL to set up state (required)
        flow.authorization_url(prompt='consent')

        # Exchange code for credentials
        print("Exchanging authorization code for credentials...")
        flow.fetch_token(code=auth_code)
        creds = flow.credentials

        # Save credentials
        token_file = 'credentials/google_token.pickle'
        os.makedirs(os.path.dirname(token_file), exist_ok=True)

        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

        print()
        print("=" * 80)
        print("✓ SUCCESS! Google authentication completed.")
        print("=" * 80)
        print()
        print(f"Credentials saved to: {token_file}")
        print()

        # Test the credentials by importing and using the service
        print("Testing credentials by creating Google Sheets service...")
        from googleapiclient.discovery import build
        service = build('sheets', 'v4', credentials=creds)
        print("✓ Google Sheets service created successfully!")
        print()
        print("You can now use the Google Sheets API in your application.")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print("✗ FAILED! Authentication failed.")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python src/auth/complete_google_auth.py <authorization_code>")
        sys.exit(1)

    auth_code = sys.argv[1]
    success = complete_authentication(auth_code)
    sys.exit(0 if success else 1)
