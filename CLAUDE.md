# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fantasy basketball application using the Yahoo Fantasy Sports API (yfpy library) to interact with Yahoo Fantasy Basketball data.

## Development Setup

**Python Version**: 3.12

**Package Manager**: uv (modern Python package manager)

**Virtual Environment**: `.venv/` (automatically managed by uv)

**Environment Configuration**:
- `.env` file contains API credentials (NEVER commit this file)
- Required environment variables:
  - `YAHOO_CONSUMER_KEY`: Yahoo Fantasy Sports API credentials
  - `YAHOO_CONSUMER_SECRET`: Yahoo API secret
  - `NBA_LEAGUE_ID`: Your fantasy league ID
  - `NBA_GAME_ID`: Yahoo game ID (466 for 2024-25 season)
  - `INITIAL_AUCTION_BUDGET`: Initial auction budget for the league (e.g., 225)
  - `GOOGLE_CREDENTIALS_PATH`: Path to Google OAuth credentials JSON
- Optional environment variables:
  - `DISCORD_WEBHOOK_URL`: Discord webhook URL for notifications (optional, leave blank to disable)
  - `DISCORD_ALERT_ROLE_ID`: Discord role ID for error mentions (optional)
- `credentials/` directory contains:
  - Google OAuth credentials JSON file
  - `google_token.pickle`: Saved Google authentication token (auto-generated)

## Common Commands

### Running the Application

#### Create New Spreadsheet (Default Mode)
```bash
# Run with default settings from .env
uv run python main.py

# Run with custom league ID
uv run python main.py --league-id 12345

# Run with verbose logging
uv run python main.py --verbose

# Run with custom document title
uv run python main.py --title "My Custom Report Title"

# Force create new spreadsheet even if updating
uv run python main.py --create-new
```

#### Update Existing Spreadsheet (Incremental Update Mode)
```bash
# Update existing spreadsheet by URL
uv run python main.py --spreadsheet-url "https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit"

# Update existing spreadsheet by ID
uv run python main.py --spreadsheet-id "SPREADSHEET_ID"

# Force update all teams (ignore transactions)
uv run python main.py --spreadsheet-id "SPREADSHEET_ID" --force-full-update

# Update with detailed transaction logging
uv run python main.py --spreadsheet-id "SPREADSHEET_ID" --verbose

# Show help
uv run python main.py --help
```

### Authentication

**Yahoo OAuth:**
- Tokens are saved to `.env` automatically
- If tokens expire, use: `uv run python -m src.auth.auth_with_code`

**Google OAuth:**
- **IMPORTANT**: Ensure your OAuth app is in "Production" status (not "Testing")
  - Google Cloud Console → "APIs & Services" → "OAuth consent screen"
  - Testing mode causes tokens to expire every 7 days
  - Production mode tokens last indefinitely
- First-time authentication: `uv run python main.py` (will open browser for OAuth)
- Tokens are saved to `credentials/google_token.pickle`
- Tokens refresh automatically (access tokens expire every 1 hour, refresh tokens in Production mode last indefinitely)
- Note: `src.auth.google_auth_manual` is deprecated (uses OOB flow which Google blocked)

### Managing Dependencies
```bash
# Add a new dependency
uv add <package-name>

# Remove a dependency
uv remove <package-name>

# Sync dependencies from pyproject.toml
uv sync

# Show installed packages
uv pip list
```

### Python Environment
```bash
# Activate virtual environment (if needed)
source .venv/bin/activate

# Run Python scripts with uv
uv run python <script.py>
```

## Project Structure

```
fantasy_basketball/
├── config.py                      # Configuration management
├── main.py                        # Application entry point ✅
├── src/
│   ├── auth/                      # OAuth authentication utilities
│   │   ├── auth_with_code.py         # Yahoo auth for headless environments ✅
│   │   ├── test_auth.py              # Interactive Yahoo auth test ✅
│   │   ├── complete_auth.py          # Yahoo OAuth helper ✅
│   │   ├── google_auth_manual.py     # Google auth for headless environments ✅
│   │   ├── complete_google_auth.py   # Google OAuth helper ✅
│   │   └── README.md                 # Authentication documentation ✅
│   ├── investigation/             # Investigation scripts (archived)
│   │   ├── investigate_salary_data.py
│   │   ├── investigate_roster.py
│   │   └── investigate_transactions.py
│   ├── data_models.py             # Player, Team, League dataclasses ✅
│   ├── yahoo_data_fetcher.py      # Yahoo API integration ✅
│   ├── data_processor.py          # Data validation & processing ✅
│   ├── google_auth.py             # Google API authentication ✅
│   ├── sheet_generator.py         # Google Sheets generation ✅
│   ├── sheet_reader.py            # Read existing sheets (incremental updates) ✅
│   ├── sheet_updater.py           # Update existing sheets (incremental updates) ✅
│   ├── transaction_tracker.py     # Track transactions (incremental updates) ✅
│   ├── discord_notifier.py        # Discord webhook notifications ✅
│   ├── logger.py                  # Logging configuration ✅
│   └── __init__.py                # Package init ✅
├── tests/                         # Test suite
│   ├── test_league_extraction.py     # Yahoo data extraction test ✅
│   ├── test_full_integration.py      # Full integration test (Yahoo + Google) ✅
│   ├── test_il_exclusion.py          # IL/IL+ exclusion logic test ✅
│   ├── test_roster_position_output.py # Roster position output format test ✅
│   ├── test_transaction_tracker.py   # Transaction tracking test ✅
│   ├── test_sheet_reader.py          # Sheet reading test ✅
│   ├── test_sheet_updater.py         # Sheet updating test ✅
│   ├── test_incremental_update.py    # Incremental update integration test ✅
│   └── test_edge_cases.py            # Edge case and error handling test ✅
├── credentials/                   # API credentials (gitignored)
│   ├── client_secret_*.json          # Google OAuth credentials
│   └── google_token.pickle           # Saved Google token (auto-generated)
├── league_data/                   # Yahoo API cache (gitignored)
├── .env                           # Environment variables (gitignored)
├── pyproject.toml                 # Project metadata and dependencies
└── uv.lock                        # Locked dependency versions
```

## Key Dependencies

- **yfpy** (v17.0.0+): Yahoo Fantasy Sports Python library for accessing Yahoo Fantasy API
  - Handles OAuth authentication with Yahoo
  - Provides data models for fantasy sports data
  - Depends on: python-dotenv, requests, stringcase, yahoo-oauth

- **Google API Client Libraries**:
  - **google-api-python-client** (v2.187.0+): Main Google API client
  - **google-auth** (v2.43.0+): Google authentication library
  - **google-auth-httplib2** (v0.2.1+): HTTP library for Google auth
  - **google-auth-oauthlib** (v1.2.2+): OAuth 2.0 helpers for Google auth

- **discord-webhook**: Discord webhook integration for automated notifications (optional)
  - Sends rich embedded notifications with update summaries
  - Error alerts with role mentions
  - Zero cost, minimal setup required

## Development Notes

- This project uses `uv` instead of pip/poetry for faster dependency management
- The `.python-version` file pins Python to 3.12
- API credentials are stored in `.env` and loaded via python-dotenv (included with yfpy)

## Features

### Incremental Sheet Updates (v2.0)

The application supports two modes: **Create** (default) and **Update** (incremental).

**How It Works:**
1. **Create Mode**: Generates a new Google Sheet with current league data
   - Stores a timestamp in the Summary sheet (cell G1) for future updates
   - Use this for first-time setup or when you want a fresh snapshot

2. **Update Mode**: Updates existing sheet with only changed data
   - Reads last update timestamp from Summary sheet
   - Fetches Yahoo transactions since last update
   - Identifies which teams had roster changes
   - Updates ONLY affected team sheets (efficiency: 75-100%)
   - Always updates Summary sheet with new statistics and timestamp
   - Preserves all formatting and structure

**Update Efficiency:**
- If 4 teams had transactions, updates only those 4 sheets (skip 12 teams)
- If no transactions occurred, updates only Summary sheet (skip all teams)
- Force full update available via `--force-full-update` flag

**Timestamp Management:**
- Machine-readable: ISO 8601 timestamp stored in cell G1 (e.g., "2025-11-18T10:30:00Z")
- Human-readable: Displayed in Summary sheet (e.g., "November 18, 2025 at 10:30 AM UTC")
- Both updated with each run to track last update time

**Verbose Logging:**
When using `--verbose`, shows detailed transaction information:
```
  • Team Name (2 transaction(s))
      - [11/18 10:30] ADD: Player Name ($5)
      - [11/18 09:15] DROP: Player Name
```

**Edge Cases Handled:**
- Invalid spreadsheet IDs: Returns None, treated as first run
- No transactions: Updates only summary sheet
- Team name changes: Automatically renames sheet, removes orphaned sheets (v2.3)
- New teams: Automatically creates sheet for new team
- Removed teams: Orphaned sheets automatically deleted (v2.3)
- Backwards compatibility: Works with old spreadsheets without timestamps

### Automatic Team Rename Handling (v2.3)

The application now intelligently handles team renames and prevents duplicate sheets.

**How It Works:**
1. **ID-Based Sheet Tracking**: Each team sheet stores an invisible team_id in cell A1
   - Format: `TEAM_ID:{team_id}` (e.g., "TEAM_ID:1")
   - Invisible to users (white text on white background)
   - Enables reliable team identification even when names change

2. **Automatic Sheet Renaming**: When teams are renamed in Yahoo Fantasy:
   - Detects the rename by comparing sheet title with current Yahoo team name
   - Automatically updates the sheet title to match the new name
   - Preserves all data and formatting

3. **Orphaned Sheet Cleanup**: Removes old sheets from renamed/removed teams:
   - Identifies sheets with team_ids not in current league
   - Automatically deletes orphaned sheets during updates
   - User-friendly summary shows what was deleted

4. **Backwards Compatibility**: Works seamlessly with old spreadsheets:
   - First update automatically migrates old sheets (adds invisible team_id)
   - No manual intervention required
   - All existing data preserved

**What You'll See:**
```
Step 2c.5: Checking for orphaned sheets...
→ Found 2 orphaned sheet(s) from renamed/removed teams:
  • Old Team Name (team_id=3)
  • Another Old Name (team_id=7)
  Deleting orphaned sheets...
✓ Deleted 2 orphaned sheet(s)
```

**Technical Details:**
- **Column Layout Change**: Team sheets now have an extra column A with invisible metadata
- **Data Location**: All visible data shifted one column right (now in columns B-F instead of A-E)
- **Sheet Lookup**: Primary lookup by team_id, fallback to name-based for compatibility
- **Performance**: Efficient batch operations minimize API calls

**Note:** The team_id metadata in column A is system-managed. Do not manually edit this column.

### Discord Notifications (v2.2)

The application includes optional Discord webhook integration for automated notifications.

**Features:**
- 🔔 **Rich embedded notifications** - Professional update summaries with key metrics
- 📊 **Efficiency tracking** - Shows teams updated, transactions processed, and efficiency percentage
- 🚨 **Error alerts** - Automatic error notifications with stack traces
- 🔗 **Clickable links** - Direct links to spreadsheets and GitHub Actions logs
- ⏱️ **Time tracking** - Shows hours since last update
- 📝 **Transaction details** - Optional verbose logs with player names and FAAB bids
- 💰 **Zero cost** - No API keys, quotas, or billing required

**Configuration:**
1. Create webhook in Discord channel settings
2. Add `DISCORD_WEBHOOK_URL` to `.env` or GitHub Secrets
3. Optional: Add `DISCORD_ALERT_ROLE_ID` for error role mentions
4. Notifications automatically sent during updates

**Notification Types:**
- **Success notifications**: Update summaries with efficiency metrics
- **Error notifications**: Critical alerts with role mentions and stack traces
- **Verbose mode**: Includes detailed transaction logs when using `--verbose` flag

**Graceful Degradation:**
- Discord failures never break the main workflow
- Notifications are completely optional
- Leave webhook URL blank to disable

## IMPORTANT: Running Python Code

**ALWAYS use `uv run python` instead of `python3` or `python` directly.**

This project uses uv to manage the virtual environment. Running Python commands directly with `python3` will NOT have access to the project dependencies installed in `.venv/`.

Examples:
- ✓ Correct: `uv run python script.py`
- ✓ Correct: `uv run python -c "print('hello')"`
- ✗ Wrong: `python3 script.py` (will fail with ModuleNotFoundError)
- ✗ Wrong: `python script.py` (will fail with ModuleNotFoundError)

This applies to all Python execution including testing, running scripts, and executing inline Python code.
