"""
Complete Yahoo OAuth authentication with verification code (non-interactive).
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Mock stdin to provide the verification code automatically
class MockStdin:
    def __init__(self, code):
        self.code = code
        self.used = False

    def readline(self):
        if not self.used:
            self.used = True
            return self.code + '\n'
        return ''

# Set up mock stdin with the verification code
verification_code = "mv77ebg"
sys.stdin = MockStdin(verification_code)

print("=" * 80)
print("Yahoo Fantasy API Authentication (Non-Interactive)")
print("=" * 80)
print(f"Using verification code: {verification_code}")
print()

try:
    from src.yahoo_data_fetcher import YahooDataFetcher
    from src.logger import logger

    print("Step 1: Initializing Yahoo API client...")
    print("(This will automatically use the verification code)")
    print()

    fetcher = YahooDataFetcher()
    print("✓ Yahoo API client initialized successfully!")
    print()

    print("Step 2: Testing API call (fetching league info)...")
    league_info = fetcher.get_league_info()
    print("✓ Successfully authenticated and retrieved league data!")
    print()

    # Display league information
    print("-" * 80)
    print("League Information:")
    print("-" * 80)
    if hasattr(league_info, 'name'):
        print(f"League Name: {league_info.name}")
    if hasattr(league_info, 'league_id'):
        print(f"League ID: {league_info.league_id}")
    if hasattr(league_info, 'season'):
        print(f"Season: {league_info.season}")
    if hasattr(league_info, 'num_teams'):
        print(f"Number of Teams: {league_info.num_teams}")

    print()
    print("=" * 80)
    print("✓ Authentication completed successfully!")
    print("=" * 80)

except Exception as e:
    print()
    print("=" * 80)
    print("✗ Authentication failed!")
    print("=" * 80)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
