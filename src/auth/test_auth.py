"""
Test script for Yahoo API authentication.

This script will:
1. Initialize the Yahoo API client
2. Trigger OAuth flow (manual authorization in browser)
3. Test a basic API call to confirm authentication works
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.yahoo_data_fetcher import YahooDataFetcher
from src.logger import logger

def test_authentication():
    """Test Yahoo API authentication and basic API call."""

    print("=" * 80)
    print("Yahoo Fantasy API Authentication Test")
    print("=" * 80)
    print()
    print("IMPORTANT: Manual OAuth Authorization Required")
    print("-" * 80)
    print()
    print("Since we're in a headless environment, you'll need to:")
    print("1. Copy the authorization URL that will be displayed")
    print("2. Open it in your browser")
    print("3. Log into Yahoo and authorize the application")
    print("4. Copy the verification code Yahoo provides")
    print("5. Paste it back when prompted")
    print()
    print("=" * 80)
    print()

    input("Press ENTER to continue and generate the authorization URL...")
    print()

    try:
        # Initialize the fetcher (this will trigger OAuth flow)
        print("Step 1: Initializing Yahoo API client...")
        fetcher = YahooDataFetcher()
        print("✓ Yahoo API client initialized successfully")
        print()

        # Test basic API call
        print("Step 2: Testing API call (fetching league info)...")
        league_info = fetcher.get_league_info()
        print("✓ Successfully authenticated and retrieved league data!")
        print()

        # Display league information
        print("-" * 60)
        print("League Information:")
        print("-" * 60)
        if hasattr(league_info, 'name'):
            print(f"League Name: {league_info.name}")
        if hasattr(league_info, 'league_id'):
            print(f"League ID: {league_info.league_id}")
        if hasattr(league_info, 'season'):
            print(f"Season: {league_info.season}")
        if hasattr(league_info, 'num_teams'):
            print(f"Number of Teams: {league_info.num_teams}")

        print()
        print("=" * 60)
        print("✓ Authentication test completed successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print("✗ Authentication test failed!")
        print("=" * 60)
        print(f"Error: {e}")
        logger.error(f"Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_authentication()
    exit(0 if success else 1)
