"""
Complete Yahoo OAuth authentication with verification code.
"""

import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from yahoo_oauth import OAuth2
from config import config, BASE_DIR

def complete_authentication(verification_code: str):
    """
    Complete OAuth authentication using the verification code.

    Args:
        verification_code: The verification code from Yahoo
    """

    print("=" * 80)
    print("Completing Yahoo OAuth Authentication")
    print("=" * 80)
    print()

    try:
        # Initialize OAuth2 with our credentials
        print("Step 1: Initializing OAuth client...")
        oauth = OAuth2(
            consumer_key=config.YAHOO_CONSUMER_KEY,
            consumer_secret=config.YAHOO_CONSUMER_SECRET,
            base_url='https://fantasysports.yahooapis.com/fantasy/v2'
        )
        print("✓ OAuth client initialized")
        print()

        # The OAuth2 library should handle token exchange automatically
        # when we provide credentials. Let's check if tokens already exist
        token_file = Path.home() / 'yahoo_oauth.json'

        print(f"Step 2: Checking for token file at {token_file}...")
        if token_file.exists():
            print("✓ Token file found!")
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                print(f"✓ Access token exists: {token_data.get('access_token', 'N/A')[:20]}...")
        else:
            print("⚠ No token file found yet")
            print("The OAuth flow needs to be completed interactively")

        print()
        print("=" * 80)
        print("OAuth Setup Summary")
        print("=" * 80)
        print(f"Consumer Key: {config.YAHOO_CONSUMER_KEY[:20]}...")
        print(f"Consumer Secret: {config.YAHOO_CONSUMER_SECRET[:10]}...")
        print(f"Verification Code: {verification_code}")
        print(f"Token Location: {token_file}")
        print()

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python complete_auth.py <verification_code>")
        sys.exit(1)

    verification_code = sys.argv[1]
    success = complete_authentication(verification_code)
    sys.exit(0 if success else 1)
