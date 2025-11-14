#!/usr/bin/env python3
"""
Transaction & FAAB Investigation Script

Investigate recent transactions to understand FAAB bid amounts
and how to match waiver acquisitions to player costs.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, Optional
from src.yahoo_data_fetcher import YahooDataFetcher
from src.logger import logger


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def inspect_transaction(transaction, index: int):
    """Inspect a single transaction object."""
    print(f"\n--- Transaction {index} ---")

    # Get transaction type
    trans_type = getattr(transaction, 'type', 'Unknown')
    print(f"Type: {trans_type}")

    # Get status
    status = getattr(transaction, 'status', 'Unknown')
    print(f"Status: {status}")

    # Get timestamp
    timestamp = getattr(transaction, 'timestamp', 'Unknown')
    print(f"Timestamp: {timestamp}")

    # Get FAAB bid
    faab_bid = getattr(transaction, 'faab_bid', None)
    print(f"FAAB Bid: {faab_bid}")

    # Get players involved
    if hasattr(transaction, 'players'):
        print(f"Players involved: {len(transaction.players)}")
        for i, player in enumerate(transaction.players, 1):
            # Get player name
            name = "Unknown"
            if hasattr(player, 'name'):
                name_obj = player.name
                if hasattr(name_obj, 'full'):
                    name = name_obj.full
                elif hasattr(name_obj, 'ascii_full'):
                    name = name_obj.ascii_full

            # Get transaction data for this player
            trans_data = getattr(player, 'transaction_data', None)
            if trans_data:
                source_type = getattr(trans_data, 'source_type', 'N/A')
                dest_type = getattr(trans_data, 'destination_type', 'N/A')
                trans_type = getattr(trans_data, 'type', 'N/A')

                print(f"  Player {i}: {name}")
                print(f"    Transaction Type: {trans_type}")
                print(f"    Source: {source_type}")
                print(f"    Destination: {dest_type}")
            else:
                print(f"  Player {i}: {name} (no transaction_data)")

    # Print all attributes for debugging
    attrs = [attr for attr in dir(transaction) if not attr.startswith('_') and not callable(getattr(transaction, attr, None))]
    print(f"\nAll attributes: {', '.join(attrs)}")


def main():
    """Main investigation function."""
    print_section("TRANSACTION & FAAB BID INVESTIGATION")

    print("Initializing Yahoo API client...")
    fetcher = YahooDataFetcher(browser_callback=False)

    # Get league info (includes transactions)
    print("\nFetching league info with transactions...")
    league_info = fetcher.get_league_info()

    transactions = league_info.transactions
    print(f"Total transactions: {len(transactions)}")

    # =========================================================================
    # 1. ANALYZE RECENT TRANSACTIONS
    # =========================================================================
    print_section("RECENT TRANSACTIONS (First 20)")

    for i, transaction in enumerate(transactions[:20], 1):
        inspect_transaction(transaction, i)

    # =========================================================================
    # 2. FILTER WAIVER TRANSACTIONS WITH FAAB BIDS
    # =========================================================================
    print_section("WAIVER TRANSACTIONS WITH FAAB BIDS")

    waiver_transactions = []
    for transaction in transactions:
        # Check if it's a waiver transaction with a FAAB bid
        trans_type = getattr(transaction, 'type', '')
        faab_bid = getattr(transaction, 'faab_bid', None)
        status = getattr(transaction, 'status', '')

        if faab_bid is not None and faab_bid >= 0:
            waiver_transactions.append(transaction)

    print(f"Found {len(waiver_transactions)} transactions with FAAB bids > 0")

    if waiver_transactions:
        print("\nTransactions with FAAB bids:")
        for i, transaction in enumerate(waiver_transactions[:10], 1):
            faab_bid = transaction.faab_bid
            timestamp = getattr(transaction, 'timestamp', 'Unknown')
            trans_type = getattr(transaction, 'type', 'Unknown')
            status = getattr(transaction, 'status', 'Unknown')

            print(f"\n{i}. FAAB Bid: ${faab_bid}")
            print(f"   Type: {trans_type}, Status: {status}")
            print(f"   Timestamp: {timestamp}")

            if hasattr(transaction, 'players'):
                for player in transaction.players:
                    name = "Unknown"
                    if hasattr(player, 'name'):
                        name_obj = player.name
                        if hasattr(name_obj, 'full'):
                            name = name_obj.full

                    trans_data = getattr(player, 'transaction_data', None)
                    if trans_data:
                        source_type = getattr(trans_data, 'source_type', 'N/A')
                        dest_type = getattr(trans_data, 'destination_type', 'N/A')
                        print(f"   Player: {name} ({source_type} → {dest_type})")

    # =========================================================================
    # 3. BUILD PLAYER -> FAAB COST MAPPING
    # =========================================================================
    print_section("PLAYER ACQUISITION COST MAPPING")

    # Build mapping of player_key -> acquisition cost (FAAB bid)
    player_faab_map: Dict[str, int] = {}

    for transaction in transactions:
        faab_bid = getattr(transaction, 'faab_bid', None)
        status = getattr(transaction, 'status', '')

        # Only count successful transactions
        if status != 'successful':
            continue

        if faab_bid is not None and faab_bid > 0:
            # Find the player being added
            if hasattr(transaction, 'players'):
                for player in transaction.players:
                    trans_data = getattr(player, 'transaction_data', None)
                    if trans_data:
                        # Check if this player is being added (not dropped)
                        dest_type = getattr(trans_data, 'destination_type', '')
                        source_type = getattr(trans_data, 'source_type', '')

                        if dest_type == 'team' and source_type in ['waivers', 'freeagents']:
                            player_key = getattr(player, 'player_key', None)
                            if player_key:
                                # Keep the most recent/highest FAAB bid for this player
                                if player_key not in player_faab_map or faab_bid > player_faab_map[player_key]:
                                    player_faab_map[player_key] = faab_bid

    print(f"Found {len(player_faab_map)} players acquired via FAAB bids")

    if player_faab_map:
        print("\nSample player FAAB costs (first 20):")
        for i, (player_key, cost) in enumerate(list(player_faab_map.items())[:20], 1):
            # Try to get player name from transactions
            player_name = "Unknown"
            for transaction in transactions:
                if hasattr(transaction, 'players') and transaction.players:
                    for player in transaction.players:
                        if getattr(player, 'player_key', None) == player_key:
                            if hasattr(player, 'name'):
                                name_obj = player.name
                                if hasattr(name_obj, 'full'):
                                    player_name = name_obj.full
                                break
            print(f"  {i}. {player_key}: ${cost} - {player_name}")

    # =========================================================================
    # 4. TEST WITH ACTUAL ROSTER
    # =========================================================================
    print_section("TESTING SALARY RETRIEVAL WITH FAAB DATA")

    # Get first team's roster
    teams = fetcher.get_league_teams()
    first_team = teams[0]
    team_id = first_team.team_id
    team_name = first_team.name

    roster = fetcher.get_team_roster(team_id)

    # Create draft cost mapping
    draft_results = fetcher.get_league_draft_results()
    draft_cost_map = {
        result.player_key: result.cost
        for result in draft_results
    }

    print(f"Team: {team_name}")
    print(f"Roster size: {len(roster.players)}")
    print("\nPlayer Salaries (with FAAB integration):\n")
    print(f"{'Player Name':<30} {'Position':<10} {'Salary':<10} {'Source':<15}")
    print("-" * 70)

    total_salary = 0
    players_with_salary = 0
    players_no_salary = 0

    for player in roster.players:
        # Get player name
        name = "Unknown"
        if hasattr(player, 'name'):
            name_obj = player.name
            if hasattr(name_obj, 'full'):
                name = name_obj.full

        # Get position
        position = getattr(player, 'display_position', 'N/A')

        # Get player key
        player_key = getattr(player, 'player_key', None)

        # Determine salary using priority order
        salary: Optional[int] = None
        source = "Unknown"

        # Priority 1: Keeper cost
        if hasattr(player, 'is_keeper'):
            keeper = player.is_keeper
            if isinstance(keeper, dict) and keeper.get('status'):
                keeper_cost = keeper.get('cost')
                if keeper_cost is not None:
                    salary = keeper_cost
                    source = "Keeper"

        # Priority 2: Draft cost
        if salary is None and player_key in draft_cost_map:
            salary = draft_cost_map[player_key]
            source = "Draft"

        # Priority 3: FAAB bid
        if salary is None and player_key in player_faab_map:
            salary = player_faab_map[player_key]
            source = "FAAB Waiver"

        # Priority 4: Free agent (no cost)
        if salary is None:
            salary = 0
            source = "Free Agent"
            players_no_salary += 1
        else:
            players_with_salary += 1

        # Display
        salary_str = f"${salary}" if salary is not None else "N/A"
        print(f"{name:<30} {position:<10} {salary_str:<10} {source:<15}")

        if salary is not None:
            total_salary += salary

    print("-" * 70)
    print(f"{'TOTAL SALARY':<30} {'':10} ${total_salary:<10}")
    print(f"{'FAAB Remaining':<30} {'':10} ${first_team.faab_balance:<10}")
    print(f"\nPlayers with assigned salary: {players_with_salary}")
    print(f"Players assumed free agent ($0): {players_no_salary}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("SUMMARY")

    print(f"✅ Total transactions in league: {len(transactions)}")
    print(f"✅ Transactions with FAAB bids > 0: {len(waiver_transactions)}")
    print(f"✅ Players acquired via FAAB: {len(player_faab_map)}")
    print(f"\n📊 Salary Retrieval Coverage for {team_name}:")
    print(f"   - Players with salary data: {players_with_salary}")
    print(f"   - Players assumed free agent: {players_no_salary}")
    print(f"   - Total roster size: {len(roster.players)}")
    print(f"   - Coverage: {(players_with_salary / len(roster.players) * 100):.1f}%")

    print("\n" + "=" * 80)
    print("Investigation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
