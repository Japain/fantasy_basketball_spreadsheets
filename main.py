#!/usr/bin/env python3
"""
Fantasy Basketball Roster & Salary Report Generator

Main application entry point. Extracts fantasy basketball league data from Yahoo
and generates a formatted Google Sheets report with team rosters and salaries.
"""

import argparse
import sys
from datetime import datetime, timezone

from config import Config
from src.logger import get_logger
from src.yahoo_data_fetcher import YahooDataFetcher
from src.sheet_generator import generate_league_report, create_draft_picks_sheet
from src.sheet_reader import extract_spreadsheet_id_from_url, read_last_run_timestamp, validate_sheet_structure, batch_read_initial_data
from src.sheet_updater import update_team_sheet, update_summary_sheet, clear_draft_picks_sheet
from src.transaction_tracker import get_transactions_since, get_affected_team_ids
from src.google_auth import get_google_sheets_service
from src.discord_notifier import notify_update_complete, notify_error, notify_bench_violations
from src.bench_analyzer import (
    analyze_bench_violations,
    get_teams_with_bench_violations
)
import traceback

logger = get_logger(__name__)


def print_banner():
    """Print application banner."""
    print()
    print("=" * 80)
    print("Fantasy Basketball Roster & Salary Report Generator")
    print("=" * 80)
    print()


def print_summary(league_data):
    """Print summary of league data."""
    stats = league_data.get_league_stats()

    print()
    print("-" * 80)
    print(f"League: {league_data.league_name}")
    print(f"Season: {league_data.season}")
    print(f"Teams: {league_data.num_teams}")
    print(f"Total Players: {stats['total_players']}")
    print(f"Total Salary Spent: ${stats['total_salary_spent']}")
    print(f"Average Team Salary: ${stats['avg_salary_per_team']:.2f}")
    print(f"Average Roster Size: {stats['avg_roster_size']:.1f}")
    print("-" * 80)
    print()


def determine_mode(args):
    """
    Determine whether to create a new spreadsheet or update an existing one.

    Args:
        args: Parsed command-line arguments.

    Returns:
        tuple: (mode, spreadsheet_id) where mode is 'create' or 'update'
    """
    # Force create mode if --create-new flag is set
    if args.create_new:
        logger.info("Mode: CREATE (forced by --create-new)")
        return 'create', None

    # Update mode if URL or ID provided
    if args.spreadsheet_url:
        try:
            spreadsheet_id = extract_spreadsheet_id_from_url(args.spreadsheet_url)
            logger.info(f"Mode: UPDATE (spreadsheet ID from URL: {spreadsheet_id})")
            return 'update', spreadsheet_id
        except ValueError as e:
            print(f"✗ Error: Invalid spreadsheet URL: {e}")
            sys.exit(1)

    if args.spreadsheet_id:
        logger.info(f"Mode: UPDATE (spreadsheet ID: {args.spreadsheet_id})")
        return 'update', args.spreadsheet_id

    # Default: create mode
    logger.info("Mode: CREATE (default)")
    return 'create', None


def format_time_ago(timestamp):
    """
    Format a timestamp as a human-readable 'time ago' string.

    Args:
        timestamp: datetime object in UTC.

    Returns:
        str: Time ago string (e.g., "2 hours ago", "3 days ago")
    """
    if timestamp is None:
        return "never"

    now = datetime.now(timezone.utc)

    # Ensure timestamp is timezone-aware
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    delta = now - timestamp

    seconds = delta.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24

    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif minutes < 60:
        return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
    elif hours < 24:
        return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
    else:
        return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"


def main():
    """Main application function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate a Google Sheets report for your fantasy basketball league"
    )
    parser.add_argument(
        '--league-id',
        help='Yahoo league ID (default: from .env NBA_LEAGUE_ID)',
        default=None
    )
    parser.add_argument(
        '--game-id',
        help='Yahoo game ID (default: from .env NBA_GAME_ID)',
        default=None
    )
    parser.add_argument(
        '--title',
        help='Custom spreadsheet title (default: "{League Name} - Rosters & Salaries")',
        default=None
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--spreadsheet-url',
        help='URL of existing spreadsheet to update',
        default=None
    )
    parser.add_argument(
        '--spreadsheet-id',
        help='ID of existing spreadsheet to update (alternative to --spreadsheet-url)',
        default=None
    )
    parser.add_argument(
        '--force-full-update',
        action='store_true',
        help='Update all teams regardless of transactions (only applies in update mode)'
    )
    parser.add_argument(
        '--create-new',
        action='store_true',
        help='Force creation of new spreadsheet even if ID/URL provided'
    )
    parser.add_argument(
        '--bench-check',
        action='store_true',
        help='Run bench management analysis only (no spreadsheet operations)'
    )

    args = parser.parse_args()

    # Validate argument combinations
    if args.spreadsheet_url and args.spreadsheet_id:
        print("✗ Error: Cannot specify both --spreadsheet-url and --spreadsheet-id")
        return 1

    if args.create_new and (args.spreadsheet_url or args.spreadsheet_id):
        print("✗ Error: Cannot use --create-new with --spreadsheet-url or --spreadsheet-id")
        return 1

    if args.bench_check and (args.spreadsheet_url or args.spreadsheet_id or args.create_new):
        print("✗ Error: --bench-check cannot be combined with spreadsheet arguments")
        return 1

    if args.bench_check and args.force_full_update:
        print("✗ Error: --bench-check cannot be combined with --force-full-update")
        return 1

    if args.force_full_update and not (args.spreadsheet_url or args.spreadsheet_id):
        print("✗ Warning: --force-full-update has no effect without --spreadsheet-url or --spreadsheet-id")
        print()

    # Set log level
    if args.verbose:
        logger.setLevel('DEBUG')

    # Print banner
    print_banner()

    # Validate configuration
    print("Validating configuration...")
    is_valid, errors = Config.validate()
    if not is_valid:
        print("✗ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("Please check your .env file and ensure all required variables are set.")
        return 1

    print("✓ Configuration validated")
    print()

    # Determine mode (create or update)
    mode, spreadsheet_id = determine_mode(args)

    # Step 1: Extract league data from Yahoo
    print("Step 1: Extracting league data from Yahoo Fantasy API...")
    print("-" * 80)
    try:
        fetcher = YahooDataFetcher(
            league_id=args.league_id,
            game_id=args.game_id,
            browser_callback=False
        )

        logger.info("Starting league data extraction...")
        league_data = fetcher.extract_league_data()

        print("✓ League data extracted successfully")
        print_summary(league_data)

    except Exception as e:
        print(f"✗ Failed to extract league data: {e}")
        logger.exception("League data extraction failed")
        # Send Discord error notification
        try:
            notify_error(
                error_message=f"Failed to extract league data from Yahoo API: {str(e)}",
                error_type="Yahoo API Error",
                stack_trace=traceback.format_exc()
            )
        except Exception as discord_err:
            logger.warning(f"Discord error notification failed: {discord_err}")
        return 1

    # Mode 1: BENCH CHECK mode (standalone bench analysis)
    if args.bench_check:
        print("\n" + "=" * 80)
        print("MODE: BENCH MANAGEMENT CHECK")
        print("=" * 80)
        print()

        try:
            # Use TODAY's date
            today = datetime.now(timezone.utc)
            today_date = today.strftime('%Y-%m-%d')

            print(f"Checking bench violations for: {today_date}")
            print()

            # Analyze violations
            violations = analyze_bench_violations(
                league=league_data,
                fetcher=fetcher,
                check_date=today_date
            )

            # Get team list
            teams_with_violations = get_teams_with_bench_violations(violations)

            if teams_with_violations:
                print(f"⚠ Found {len(teams_with_violations)} team(s) with bench violations:")
                for team_name in teams_with_violations:
                    violation_count = len(violations[team_name])
                    print(f"  • {team_name} ({violation_count} player(s))")
                print()

                # Send Discord notification (no spreadsheet URL in this mode)
                notify_bench_violations(
                    teams_with_violations=teams_with_violations,
                    spreadsheet_url="",  # No spreadsheet in this mode
                    check_date=today_date
                )

                print("✓ Discord notification sent")
            else:
                print("✓ No bench violations found - all teams optimized their lineups!")

            print()
            print("=" * 80)
            print("✓ BENCH CHECK COMPLETE")
            print("=" * 80)
            print()
            return 0

        except Exception as e:
            logger.exception("Bench check failed")
            print(f"\n✗ Error: Bench check failed: {e}\n")
            notify_error(
                error_message=str(e),
                error_type="Bench Check Failed",
                stack_trace=traceback.format_exc()
            )
            return 1

    # Mode 2: CREATE mode or Mode 3: UPDATE mode
    if mode == 'create':
        # CREATE MODE: Generate new spreadsheet
        print("Step 2: Generating Google Sheets report...")
        print("-" * 80)
        try:
            logger.info("Starting spreadsheet generation...")
            sheet_url = generate_league_report(league_data, sheet_title=args.title)
            spreadsheet_id = sheet_url.split('/d/')[1].split('/')[0]

            print("✓ Google Sheets generated successfully")
            print()

        except Exception as e:
            print(f"✗ Failed to generate Google Sheets: {e}")
            logger.exception("Spreadsheet generation failed")
            # Send Discord error notification
            try:
                notify_error(
                    error_message=f"Failed to generate Google Sheets report: {str(e)}",
                    error_type="Google Sheets Error",
                    stack_trace=traceback.format_exc()
                )
            except Exception as discord_err:
                logger.warning(f"Discord error notification failed: {discord_err}")
            return 1

        # Print success message
        print("=" * 80)
        print("✓ SUCCESS! Report generated successfully")
        print("=" * 80)
        print()
        print(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        print()
        print("Summary:")
        print(f"  - {league_data.num_teams} teams processed")
        print(f"  - {league_data.get_total_players()} total players")
        stats = league_data.get_league_stats()
        print(f"  - ${stats['total_salary_spent']} total salary spent")
        print(f"  - ${stats['avg_salary_per_team']:.2f} average team salary")
        print()
        print("Open the URL above to view your league report!")
        print("=" * 80)
        print()

        # Send Discord notification for create mode
        try:
            notify_update_complete(
                teams_updated=league_data.num_teams,
                total_teams=league_data.num_teams,
                transactions_processed=0,  # Create mode doesn't process transactions
                spreadsheet_url=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
                last_update_hours=0.0  # First run
            )
        except Exception as e:
            logger.warning(f"Discord notification failed (non-critical): {e}")

    else:
        # UPDATE MODE: Update existing spreadsheet
        print("Step 2: Updating existing spreadsheet...")
        print("-" * 80)
        try:
            service = get_google_sheets_service()

            # Step 2a-2b: Batch read initial data (validation + timestamp)
            print("Step 2a-2b: Reading spreadsheet metadata and timestamp...")
            initial_data = batch_read_initial_data(service, spreadsheet_id)

            # Validate structure
            if not initial_data['valid_structure']:
                print("✗ Warning: Spreadsheet structure doesn't match expected format")
                print("  This may not be a spreadsheet created by this application.")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("Update cancelled.")
                    return 0

            print(f"✓ Spreadsheet validated: {initial_data['sheet_count']} sheets found")

            # Extract timestamp
            last_run_timestamp = initial_data['timestamp']

            if last_run_timestamp:
                time_ago = format_time_ago(last_run_timestamp)
                print(f"✓ Last update: {last_run_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')} ({time_ago})")
            else:
                print("⊘ No timestamp found. Treating as first update.")
            print()

            # Step 2b.5: Ensure Draft Picks sheet exists (migration support)
            print("Step 2b.5: Checking for Draft Picks sheet...")
            try:
                from src.sheet_updater import _find_sheet_id_by_name

                draft_picks_sheet_id = _find_sheet_id_by_name(service, spreadsheet_id, 'Draft Picks')

                if draft_picks_sheet_id is None:
                    print("→ Draft Picks sheet not found. Creating it...")
                    create_draft_picks_sheet(service, spreadsheet_id)
                    print("✓ Draft Picks sheet created")
                else:
                    print("✓ Draft Picks sheet exists")
            except Exception as e:
                logger.error(f"Failed to check/create Draft Picks sheet: {e}")
                print(f"⚠ Warning: Draft Picks sheet check failed: {e}")
                # Continue anyway - not critical
            print()

            # Step 2c: Get transactions since last run
            print("Step 2c: Checking for transactions since last run...")
            if last_run_timestamp and not args.force_full_update:
                # Convert datetime to Unix timestamp for transaction filtering
                last_run_unix = int(last_run_timestamp.timestamp())
                transactions = get_transactions_since(fetcher, last_run_unix)

                if transactions:
                    print(f"✓ Found {len(transactions)} transaction(s)")
                else:
                    print("⊘ No transactions found since last run")
            else:
                if args.force_full_update:
                    print("⊘ Skipping transaction check (--force-full-update enabled)")
                else:
                    print("⊘ Skipping transaction check (first update)")
                transactions = []
            print()

            # Step 2c.5: Cleanup orphaned sheets
            print("Step 2c.5: Checking for orphaned sheets...")
            current_team_ids = {team.team_id for team in league_data.teams}
            current_team_names = {team.team_name for team in league_data.teams}

            try:
                from src.sheet_updater import cleanup_orphaned_sheets, _build_sheet_metadata_cache

                # Build metadata cache once to avoid redundant API calls
                # This cache will be used by cleanup_orphaned_sheets to identify sheets
                # without making individual API calls for each sheet
                metadata_cache = _build_sheet_metadata_cache(service, spreadsheet_id)

                deleted_count = cleanup_orphaned_sheets(
                    service, spreadsheet_id, current_team_ids, current_team_names,
                    metadata_cache=metadata_cache
                )
                if deleted_count > 0:
                    print(f"✓ Deleted {deleted_count} orphaned sheet(s)")
                else:
                    print("✓ No orphaned sheets found")
            except Exception as e:
                logger.error(f"Failed to cleanup orphaned sheets: {e}")
                print(f"⚠ Warning: Orphan cleanup failed: {e}")
                # Continue anyway - not critical
            print()

            # Step 2c.6: Clear Draft Picks sheet if force full update
            if args.force_full_update:
                print("Step 2c.6: Clearing Draft Picks sheet (force full update)...")
                try:
                    clear_draft_picks_sheet(service, spreadsheet_id)
                    print("✓ Draft Picks sheet cleared")
                except Exception as e:
                    logger.error(f"Failed to clear Draft Picks sheet: {e}")
                    print(f"⚠ Warning: Draft Picks clear failed: {e}")
                    # Continue anyway - not critical
                print()

            # Step 2d: Identify affected teams
            print("Step 2d: Identifying teams to update...")
            if args.force_full_update or not last_run_timestamp:
                # Update all teams
                teams_to_update = league_data.teams
                print(f"→ Updating ALL {len(teams_to_update)} teams")
                if args.force_full_update:
                    print("  (forced by --force-full-update)")
                else:
                    print("  (first update)")
            elif transactions:
                # Update only affected teams
                affected_team_ids = get_affected_team_ids(transactions)
                teams_to_update = [t for t in league_data.teams if t.team_id in affected_team_ids]

                print(f"→ Updating {len(teams_to_update)} of {len(league_data.teams)} teams")
                for team in sorted(teams_to_update, key=lambda t: t.team_name):
                    team_transactions = [tx for tx in transactions if tx.team_id == team.team_id]
                    print(f"  • {team.team_name} ({len(team_transactions)} transaction(s))")

                    # Show transaction details in verbose mode
                    if args.verbose:
                        for tx in sorted(team_transactions, key=lambda t: t.timestamp, reverse=True):
                            tx_time = datetime.fromtimestamp(tx.timestamp).strftime('%m/%d %H:%M')
                            faab_info = f" (${tx.faab_bid})" if tx.faab_bid else ""
                            print(f"      - [{tx_time}] {tx.transaction_type.value.upper()}: {tx.player_name}{faab_info}")

                skipped = len(league_data.teams) - len(teams_to_update)
                if skipped > 0:
                    print(f"  ⊘ Skipped: {skipped} team(s) (no changes)")
            else:
                # No transactions, no teams to update
                teams_to_update = []
                print("→ No teams to update (no transactions)")
            print()

            # Step 2e: Update affected team sheets
            if teams_to_update:
                print(f"Step 2e: Updating {len(teams_to_update)} team sheet(s)...")
                for team in sorted(teams_to_update, key=lambda t: t.team_name):
                    update_team_sheet(service, spreadsheet_id, team)
                    print(f"  ✓ {team.team_name} ({len(team.roster)} players, ${team.total_salary})")
                print()

            # Step 2f: Update summary sheet
            print("Step 2f: Updating summary sheet...")
            update_summary_sheet(service, spreadsheet_id, league_data)
            print("✓ Summary sheet updated")
            print()

            # Print success message
            print("=" * 80)
            print("✓ SUCCESS! Spreadsheet updated successfully")
            print("=" * 80)
            print()
            print(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
            print()
            print("Summary:")
            print(f"  - Teams updated: {len(teams_to_update)} of {league_data.num_teams}")
            if transactions:
                print(f"  - Transactions processed: {len(transactions)}")
            if last_run_timestamp:
                print(f"  - Time since last update: {format_time_ago(last_run_timestamp)}")
            print()
            print("Open the URL above to view your updated league report!")
            print("=" * 80)
            print()

            # Send Discord notification for update mode
            try:
                # Calculate hours since last update
                hours_since_update = 0.0
                if last_run_timestamp:
                    now = datetime.now(timezone.utc)
                    if last_run_timestamp.tzinfo is None:
                        last_run_timestamp = last_run_timestamp.replace(tzinfo=timezone.utc)
                    time_delta = now - last_run_timestamp
                    hours_since_update = time_delta.total_seconds() / 3600

                # Format verbose transaction log if available
                verbose_log = None
                if transactions and args.verbose:
                    log_lines = []
                    teams_with_transactions = {}
                    for tx in transactions:
                        if tx.team_name not in teams_with_transactions:
                            teams_with_transactions[tx.team_name] = []
                        teams_with_transactions[tx.team_name].append(tx)

                    for team_name in sorted(teams_with_transactions.keys()):
                        team_txs = teams_with_transactions[team_name]
                        log_lines.append(f"• {team_name} ({len(team_txs)} transaction(s))")
                        for tx in sorted(team_txs, key=lambda t: t.timestamp, reverse=True):
                            tx_time = datetime.fromtimestamp(tx.timestamp).strftime('%m/%d %H:%M')
                            faab_info = f" (${tx.faab_bid})" if tx.faab_bid else ""
                            log_lines.append(f"    - [{tx_time}] {tx.transaction_type.value.upper()}: {tx.player_name}{faab_info}")

                    verbose_log = "\n".join(log_lines)

                notify_update_complete(
                    teams_updated=len(teams_to_update),
                    total_teams=league_data.num_teams,
                    transactions_processed=len(transactions) if transactions else 0,
                    spreadsheet_url=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
                    last_update_hours=hours_since_update,
                    verbose_transaction_log=verbose_log
                )
            except Exception as e:
                logger.warning(f"Discord notification failed (non-critical): {e}")

        except Exception as e:
            print(f"✗ Failed to update spreadsheet: {e}")
            logger.exception("Spreadsheet update failed")
            # Send Discord error notification
            try:
                notify_error(
                    error_message=f"Failed to update existing spreadsheet: {str(e)}",
                    error_type="Spreadsheet Update Error",
                    stack_trace=traceback.format_exc()
                )
            except Exception as discord_err:
                logger.warning(f"Discord error notification failed: {discord_err}")
            return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\n✗ Unexpected error: {e}")
        # Send Discord error notification for unexpected errors
        try:
            notify_error(
                error_message=f"Unexpected error in main application: {str(e)}",
                error_type="Unexpected Error",
                stack_trace=traceback.format_exc()
            )
        except Exception as discord_err:
            logger.warning(f"Discord error notification failed: {discord_err}")
        sys.exit(1)
