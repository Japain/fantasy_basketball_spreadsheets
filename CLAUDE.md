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
  - `OWNER_EMAIL`: Email address for sheet protection - only this user can edit sheets (optional, e.g., "user@gmail.com")
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
│   ├── api_retry.py               # API retry with exponential backoff ✅
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
│   ├── test_edge_cases.py            # Edge case and error handling test ✅
│   └── test_api_retry.py             # API retry logic test ✅
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

### Sheet Protection

The application can automatically protect all sheets (except Draft Picks) to prevent accidental edits.

**How It Works:**
- **Protected Sheets**: Summary sheet and all team sheets are protected
- **Editable Sheet**: Draft Picks sheet remains unprotected for manual data entry
- **Owner-Only Access**: Only the configured owner email can edit protected sheets
- **Automatic Application**: Protection is applied during sheet creation and updates

**Configuration:**
1. Add `OWNER_EMAIL` to `.env` file with your Google account email
   ```
   OWNER_EMAIL=youremail@gmail.com
   ```
2. Protection is automatically applied when creating or updating sheets
3. If `OWNER_EMAIL` is not set, sheets remain unprotected (legacy behavior)

**Features:**
- ✅ **Summary sheet protected** - Prevents accidental changes to league statistics
- ✅ **Team sheets protected** - Prevents unauthorized roster modifications
- ✅ **Draft Picks unprotected** - Allows collaborative manual data entry
- ✅ **Automatic updates** - Protection reapplied during every update
- ✅ **Backwards compatible** - Works with existing spreadsheets

**Note:** The owner email must match the Google account that has access to the spreadsheet. Other users with view access will see a lock icon and cannot edit protected sheets.

### Bench Management Alerts (v2.7.1)

The application includes optional bench management analysis for same-day lineup optimization alerts.

**Features:**
- 🔍 **Same-day analysis** - Checks current lineups for today's games
- ⚠️ **Violation detection** - Identifies teams with benched healthy players
- 🔔 **Discord alerts** - Immediate notifications via webhook
- 📊 **Single source of truth** - Uses Yahoo API only (no spreadsheet)
- ⚡ **Non-critical** - Analysis failures don't break main workflow

**How It Works:**
1. Run late at night (1-2 AM EST) after games complete
2. Fetch current roster positions from Yahoo API
3. Check current player health status from Yahoo API
4. Verify which players had games TODAY
5. Identify violations: benched + healthy + had game
6. Send Discord notification immediately

**Usage:**
```bash
# Bench check only (no spreadsheet operations)
uv run python main.py --bench-check

# Regular spreadsheet update (no bench check)
uv run python main.py --spreadsheet-id "YOUR_ID"

# Create new spreadsheet (no bench check)
uv run python main.py
```

**Scheduling:**
- **Bench Check**: Run at 1-2 AM EST via cron/GitHub Actions with `--bench-check`
- **Timing**: After all NBA games complete (~midnight EST)
- **Before**: Managers wake up to fix lineups (~6-7 AM EST)
- **Spreadsheet Updates**: Run separately at any time (e.g., hourly)

**Configuration:**
- **Standalone mode**: Use `--bench-check` flag
- **Discord**: Uses same webhook as update notifications
- **No spreadsheet required**: Can run without any spreadsheet arguments

**Criteria for Violation (Optimal Lineup Logic):**
A team is flagged when:
1. Team has active roster spots that could be better utilized:
   - Active player whose team has NO game today, OR
   - Empty active roster spot (< 10 active players)
2. AND a benched player meets ALL these conditions:
   - Currently in BN (bench) position
   - NOT in IL/IL+ position
   - Currently healthy (no INJ/OUT/DTD/GTD status)
   - Team HAS a scheduled game TODAY

**Important:** If all 10 active roster spots are filled with players who have games today,
then benched players are NOT flagged as violations (lineup is optimally configured).

**Example Violation:**
- Active: Player A (team has NO game today)
- Bench: Player B (team HAS game today, healthy)
- Action: Should swap A and B to optimize lineup

**Example Output:**
```
MODE: BENCH MANAGEMENT CHECK
================================================================================

Checking bench violations for: 2026-01-24

⚠ Found 3 team(s) with bench violations:
  • Team Alpha (2 player(s))
  • Team Beta (1 player(s))
  • Team Gamma (1 player(s))

✓ Discord notification sent
================================================================================
✓ BENCH CHECK COMPLETE
================================================================================
```

**Performance:**
- Google Sheets: **0 read calls** (no spreadsheet needed)
- Yahoo API: ~10-30 calls (one per benched player)
- Total: **~10-30 API calls per run**
- Non-blocking: Runs after league data fetch

**Advantages over v2.7:**
- ✅ **No timing issues** - checks same-day, not historical
- ✅ **No false positives** - uses real game-time positions
- ✅ **Simpler** - single source of truth (Yahoo API)
- ✅ **More accurate** - catches violations before managers fix them

### Proactive Bench Alerts (v2.8) - NEW

**Feature:** Schedule-based violation detection with optimal lineup logic enables alerts BEFORE games start

The v2.8 update replaces the retroactive stats-based checking with a proactive schedule-based approach using ESPN API.

**Key Changes:**
- **Before (v2.7.1)**: Checked if player recorded stats → alerts AFTER games
- **Now (v2.8)**: Checks if player's team has scheduled game → alerts BEFORE games

#### Bug Fix (v2.8.1) - Team Abbreviation Mapping

**Issue Found (2026-01-24):** ESPN API and Yahoo API use different team abbreviations for some teams, causing benched players from affected teams to not be detected as having games.

**Affected Teams:**
- Washington Wizards: Yahoo `WAS` vs ESPN `WSH`
- New York Knicks: Yahoo `NYK` vs ESPN `NY`
- Golden State Warriors: Yahoo `GSW` vs ESPN `GS`
- Utah Jazz: Yahoo `UTA` vs ESPN `UTAH`
- San Antonio Spurs: Yahoo `SAS` vs ESPN `SA`
- New Orleans Pelicans: Yahoo `NOP` vs ESPN `NO`

**Fix:** Added team abbreviation normalization in `nba_schedule_fetcher.py`:
- `ESPN_TO_YAHOO_TEAM_MAPPING` dictionary maps ESPN codes to Yahoo codes
- `normalize_team_abbreviation()` function normalizes ESPN abbreviations before comparison
- All ESPN team abbreviations converted to Yahoo format when checking schedules

**Testing:** Created `tests/test_team_abbreviation_mapping.py` with 10 comprehensive tests (all passing)

**How It Works:**
1. Fetches NBA game schedules from ESPN API (free, no authentication)
2. Checks if benched player's team has a game scheduled TODAY
3. Caches schedule data (1-hour TTL) to minimize API calls
4. Falls back to NBA Official API if ESPN fails
5. Sends Discord alerts immediately when violations detected

**Benefits over v2.7.1:**
- ✅ **Proactive alerts** - Can send alerts 2-6 hours before games (Phase 3)
- ✅ **95% fewer API calls** - 1 schedule fetch vs 10-30 stat fetches per run
- ✅ **Better caching** - 1-hour TTL on schedule data (reused across multiple checks)
- ✅ **Zero Yahoo API usage** - Game checking moved to ESPN API
- ✅ **Zero cost** - ESPN API is free, no authentication required
- ✅ **More reliable** - Works even if player DNP'd (team schedule matters, not player stats)
- ✅ **Optimal lineup logic** (v2.8.1) - No false positives when lineup is properly filled with players who have games

**Technical Details:**
- **Module**: `src/nba_schedule_fetcher.py` - ESPN API integration with caching
- **Modified**: `src/bench_analyzer.py` - Uses schedule-based checking (feature flag enabled)
- **Feature Flag**: `USE_PROACTIVE_SCHEDULE_CHECK = True` (set to False to rollback)
- **Cache TTL**: 1 hour (configurable in `CACHE_TTL_SECONDS`)
- **Retry Logic**: 3 attempts with exponential backoff
- **Fallback Chain**: ESPN API → NBA Official API → Empty set (conservative)

**API Performance:**
- **ESPN API**: Primary source, ~500ms response time (p95)
- **Cache Hit**: 0 API calls, instant response
- **Cache Miss**: 1 API call for all benched players (vs 10-30 in v2.7.1)

**Rollback:**
Set `USE_PROACTIVE_SCHEDULE_CHECK = False` in `src/bench_analyzer.py` to use legacy stats-based checking.

**Usage:**
Same as v2.7.1 - no changes to command-line interface:
```bash
# Bench check with proactive schedule-based detection
uv run python main.py --bench-check
```

**Future Enhancements (Phase 3):**
- Multiple checks per day (e.g., 10 AM, 2 PM, 6 PM EST)
- Game-time filtering (alert only for upcoming games, not completed)
- Configurable alert timing (X hours before game start)

### Rate Limit Optimization (v2.4 + v2.5) ✅ Production Ready

The application includes comprehensive rate limit handling to work within Google Sheets API quotas.

**Rate Limits:**
- Google Sheets API: 60 read requests per minute per user
- Google Sheets API: 60 write requests per minute per user
- Quotas refill every minute

**Optimization Features (v2.5):**
- 🚀 **Batch read API** - Read all metadata in single call instead of individual reads
- ⚡ **82% API call reduction** - Reduced from ~39 to ~7 read requests per update
- 🔄 **Cache reuse** - Metadata read once and shared between functions
- 🔁 **Automatic retry** - Exponential backoff for rate limits (429) and server errors (5xx)
- 📊 **API monitoring** - Built-in call counter for tracking usage
- 🚫 **No crashes** - Graceful handling of rate limit errors
- 🎯 **Production ready** - Enables 8+ updates per minute (up from 1-2)

**How It Works:**

1. **Batch Read Pattern (v2.5 - NEW)**:
   ```python
   # Batch read all team metadata in ONE API call
   # Before: 17 calls (1 + 16 individual reads)
   # After: 2 calls (1 + 1 batch read)
   metadata_cache = _build_sheet_metadata_cache(service, spreadsheet_id)

   # Batch read initial data in TWO API calls
   # Before: 3 calls (timestamp + validation + team sheets)
   # After: 2 calls (1 metadata + 1 timestamp)
   initial_data = batch_read_initial_data(service, spreadsheet_id)
   ```

2. **Cache Reuse Pattern (v2.4)**:
   ```python
   # Metadata read once and reused
   metadata_cache = _build_sheet_metadata_cache(service, spreadsheet_id)
   cleanup_orphaned_sheets(..., metadata_cache=metadata_cache)
   ```

3. **Automatic Retry with Exponential Backoff (v2.4)**:
   - All critical read/write operations wrapped with retry logic
   - Retries on 429 (rate limit) and 5xx (server errors)
   - Non-retryable errors (4xx) fail immediately
   - Formula: `min((2^n + random_ms), max_backoff)`
   - Default: max 5 retries with 64s max backoff

4. **API Call Monitoring** (Optional):
   ```python
   from src.api_retry import APICallCounter

   with APICallCounter() as counter:
       # Make API calls
       counter.increment("read")
       # Summary logged automatically at end
   ```

**Performance Impact:**
- **Before (v2.3)**: ~39 read requests per update (1-2 updates/minute max)
- **Phase 1 (v2.4)**: ~23 read requests per update (2-3 updates/minute)
- **Phase 2 (v2.5)**: **~7 read requests per update (8+ updates/minute)** ✅
- **Total Improvement**: **82% reduction in API calls** ✅

**Breakdown by Component:**
- Metadata cache: 32 → 2 calls (94% reduction)
- Initial reads: 3 → 2 calls (33% reduction)
- Overall: 39 → 7 calls (82% reduction)

**Automatic Features:**
- No configuration needed - works out of the box
- Rate limits handled transparently
- Retry attempts logged for monitoring
- Failures after max retries bubble up as exceptions
- Legacy functions kept for rollback if needed

**Rollback Options:**
- `_build_sheet_metadata_cache_legacy()` available as fallback
- Original `read_last_run_timestamp()` and `validate_sheet_structure()` still work independently
- Batch functions tested to return identical results to legacy versions

See `RATE_LIMIT_SOLUTIONS.md` and `RATE_LIMIT_TODO.md` for technical details.

## IMPORTANT: Running Python Code

**ALWAYS use `uv run python` instead of `python3` or `python` directly.**

This project uses uv to manage the virtual environment. Running Python commands directly with `python3` will NOT have access to the project dependencies installed in `.venv/`.

Examples:
- ✓ Correct: `uv run python script.py`
- ✓ Correct: `uv run python -c "print('hello')"`
- ✗ Wrong: `python3 script.py` (will fail with ModuleNotFoundError)
- ✗ Wrong: `python script.py` (will fail with ModuleNotFoundError)

This applies to all Python execution including testing, running scripts, and executing inline Python code.
