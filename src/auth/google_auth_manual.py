"""Manual Google OAuth authentication for headless/WSL environments.

⚠️ DEPRECATION WARNING ⚠️
This script uses Google's Out-of-Band (OOB) OAuth flow, which was deprecated
by Google in 2022 and no longer works. You will get a "400: invalid_request"
error stating "The out-of-band (OOB) flow has been blocked."

RECOMMENDED ALTERNATIVE:
Instead of this script, use the standard OAuth flow via main.py:
    uv run python main.py

This will open a browser window for authentication and works in WSL environments.
If you're in a truly headless environment (no browser access), consider using
Workload Identity Federation for GitHub Actions instead.

Usage (DEPRECATED):
    uv run python -m src.auth.google_auth_manual
"""

import os
import pickle
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

# Google API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def authenticate_google_manual():
    """
    Manually authenticate with Google OAuth in a headless environment.

    This function:
    1. Generates an OAuth URL
    2. Prompts user to visit the URL in a browser
    3. Prompts user to paste the authorization code
    4. Exchanges the code for credentials
    5. Saves credentials for future use
    """
    # Get credentials path from environment
    credentials_path = os.getenv(
        'GOOGLE_CREDENTIALS_PATH',
        'credentials/client_secret_244271698600-19dd7prtef55t0845qibik3l0t1mo0pn.apps.googleusercontent.com.json'
    )

    if not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at: {credentials_path}")
        print("Please ensure your Google OAuth credentials file is in the credentials/ directory")
        return False

    print("=" * 80)
    print("Google OAuth Manual Authentication")
    print("=" * 80)
    print()

    # Create flow
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)

    # Generate authorization URL
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # Use out-of-band flow
    auth_url, _ = flow.authorization_url(prompt='consent')

    print("STEP 1: Visit this URL in your browser:")
    print()
    print(auth_url)
    print()
    print("-" * 80)
    print()
    print("STEP 2: After authorizing, Google will show you an authorization code.")
    print("        Copy the authorization code and paste it below.")
    print()

    # Prompt for authorization code
    auth_code = input("Enter the authorization code: ").strip()

    if not auth_code:
        print("\nERROR: No authorization code provided!")
        return False

    print()
    print("Exchanging authorization code for credentials...")

    try:
        # Exchange code for credentials
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
        print("You can now use the Google Docs API in your application.")
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
        print("Common issues:")
        print("  - Authorization code has expired (they expire quickly)")
        print("  - Authorization code was already used (they're single-use)")
        print("  - Network connectivity issues")
        print()
        print("Please try running this script again and use a fresh authorization code.")
        print()

        return False


if __name__ == "__main__":
    success = authenticate_google_manual()
    exit(0 if success else 1)
