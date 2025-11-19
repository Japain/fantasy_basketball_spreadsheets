# Changelog

All notable changes to the Fantasy Basketball application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

---

## [2.1.0] - 2025-11-19

### Added - Automated Daily Updates via GitHub Actions

**New feature**: Zero-cost automated daily spreadsheet updates using GitHub Actions

#### Overview
Added comprehensive GitHub Actions workflow for scheduling automatic daily updates of Google Sheets spreadsheets. This cloud-based solution eliminates the need for a local machine to be running, provides excellent monitoring and logging, and operates entirely within GitHub's free tier.

**Key Features**:
- 🤖 **Automated execution** - Runs daily at configurable time (currently 11:00 AM UTC)
- ☁️ **Cloud-based** - No local machine or server required
- 💰 **Zero cost** - Operates entirely within GitHub Actions free tier (~30 minutes/month usage)
- 📧 **Email notifications** - Automatic alerts on workflow failures
- 🎯 **Manual triggers** - Run updates on-demand via GitHub UI
- 📊 **Built-in monitoring** - Comprehensive logging and workflow run history (90-day retention)
- 🔐 **Secure** - OAuth tokens and credentials stored in encrypted GitHub Secrets

#### New Files
- `.github/workflows/daily-update.yml` - GitHub Actions workflow configuration
  - Automated daily schedule via cron syntax (`0 11 * * *`)
  - Manual trigger capability via `workflow_dispatch`
  - Python 3.12 environment setup
  - `uv` package manager installation and dependency sync
  - Yahoo OAuth token configuration (using `YAHOO_ACCESS_TOKEN_JSON`)
  - Google OAuth credentials and token setup
  - Verbose logging for detailed transaction information
  - Automatic log upload on failure for debugging

- `GITHUB_ACTIONS_SETUP.md` - Complete setup and troubleshooting guide
  - Step-by-step setup instructions
  - OAuth token extraction and configuration
  - GitHub Secrets setup guide
  - Workflow testing procedures
  - Monitoring and maintenance guidance
  - Comprehensive troubleshooting section
  - Security best practices

- `context/DEPLOYMENT_OPTIONS.md` - Deployment research and analysis
  - Evaluation of 5 deployment options (Cron, GitHub Actions, AWS Lambda, Google Cloud Run, Azure Functions)
  - Detailed technical feasibility analysis
  - Cost comparison and rankings
  - Implementation difficulty assessment
  - Recommendations with decision framework
  - Implementation guidance for each option

#### Authentication Improvements
- **Yahoo OAuth**: Implemented `YAHOO_ACCESS_TOKEN_JSON` approach
  - Workflow creates properly formatted JSON string with all token fields
  - Leverages yfpy's `env_var_fallback` feature for headless authentication
  - Eliminates "EOF when reading a line" errors in GitHub Actions
  - Automatic token refresh using refresh token

- **Google OAuth**: Base64-encoded token persistence
  - Google token pickle file encoded and stored in GitHub Secrets
  - Decoded at runtime for seamless authentication
  - Automatic token refresh via Google OAuth libraries

#### Documentation Updates
- Updated `README.md` with "Automated Daily Updates (GitHub Actions)" section
  - Quick start guide
  - Benefits and features overview
  - Reference to `GITHUB_ACTIONS_SETUP.md` for complete instructions

- Updated `CLAUDE.md` with GitHub Actions information
  - Added to development notes
  - Workflow file location documented

#### Workflow Features

**Scheduling**:
- Cron-based scheduling with customizable timing
- Current default: 11:00 AM UTC (6:00 AM EST, 3:00 AM PST)
- Easy timezone adjustment via cron syntax

**Environment Setup**:
- Ubuntu latest runner
- Python 3.12
- `uv` package manager for fast dependency installation
- All project dependencies synced automatically

**Secret Management**:
- 11 encrypted GitHub Secrets for credentials and configuration:
  - `YAHOO_CONSUMER_KEY`, `YAHOO_CONSUMER_SECRET`
  - `YAHOO_ACCESS_TOKEN`, `YAHOO_REFRESH_TOKEN`, `YAHOO_TOKEN_TIME`
  - `NBA_LEAGUE_ID`, `NBA_GAME_ID`, `INITIAL_AUCTION_BUDGET`
  - `GOOGLE_CREDENTIALS_JSON`, `GOOGLE_TOKEN_PICKLE_BASE64`
  - `SPREADSHEET_ID`

**Error Handling**:
- Automatic log and data artifact upload on failure
- 7-day retention for debugging
- Email notifications via GitHub Actions


#### Testing
- Manual workflow testing via GitHub Actions UI
- Verified scheduled execution
- Confirmed incremental update mode works correctly
- Validated verbose logging output
- Tested authentication with Yahoo and Google APIs
- Verified error handling and log upload on failure

#### Troubleshooting Addressed
- **Yahoo OAuth authentication errors**: Fixed via `YAHOO_ACCESS_TOKEN_JSON` JSON string approach
- **"EOF when reading a line" errors**: Resolved by creating `.env` file with properly formatted tokens
- **Token refresh**: Automatic refresh implemented using refresh tokens
- **Schedule timing**: Adjusted to 11:00 AM UTC for optimal timing

#### Commits
- c9a936c - Fix GitHub Actions authentication issue
- bb2d497 - Fix GitHub Actions OAuth authentication - create oauth2.json file
- 91c421e - Fix GitHub Actions authentication - use YAHOO_ACCESS_TOKEN_JSON env var
- 6847edb - Update documentation for YAHOO_ACCESS_TOKEN_JSON approach
- 085e4e1 - Update daily run time to 11am UTC

#### Usage
```bash
# Manual trigger from GitHub Actions UI
# 1. Go to Actions tab
# 2. Select "Daily Fantasy Basketball Update"
# 3. Click "Run workflow"

# Update workflow schedule
# Edit .github/workflows/daily-update.yml cron expression:
# - cron: '0 11 * * *'  # 11 AM UTC
```

#### Cost Analysis
- **Monthly usage**: ~30 minutes (1 min/day × 30 days)
- **Free tier**: 2,000 minutes/month (private repos), unlimited (public repos)
- **Actual cost**: $0/month (well within free tier)

**For complete setup instructions, see [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)**

**For deployment options analysis, see [context/DEPLOYMENT_OPTIONS.md](context/DEPLOYMENT_OPTIONS.md)**

---

## [2.0.0] - 2025-11-18

### Added - Incremental Sheet Updates Feature

**Major new feature**: Incremental update mode for efficient spreadsheet updates

#### Overview
Added comprehensive incremental update functionality that allows updating existing Google Sheets spreadsheets with only the teams that have had roster changes, dramatically improving efficiency and reducing API usage.

**Key Features**:
- ⚡ **75-100% efficiency** - Only updates teams with roster changes
- 🔄 **Transaction tracking** - Automatically identifies affected teams
- 📊 **Timestamp management** - Tracks last update time
- 🔍 **Enhanced logging** - Detailed transaction information in verbose mode
- ↩️ **Backwards compatible** - Works with spreadsheets created before v2.0

#### New CLI Arguments
- `--spreadsheet-url URL` - Update existing spreadsheet by URL
- `--spreadsheet-id ID` - Update existing spreadsheet by ID
- `--force-full-update` - Update all teams regardless of transactions
- `--create-new` - Force create new spreadsheet (override update mode)

#### New Modules
- `src/transaction_tracker.py` - Track Yahoo Fantasy transactions and identify affected teams
- `src/sheet_reader.py` - Read existing spreadsheets, extract timestamps, validate structure
- `src/sheet_updater.py` - Update existing sheets with new data

#### Modified Modules
- `main.py` - Enhanced with complete update workflow and mode detection
- `src/sheet_generator.py` - Refactored with timestamp management and reusable helpers
- `src/data_models.py` - Added TransactionType enum and TransactionInfo dataclass
- `src/yahoo_data_fetcher.py` - Added transaction retrieval methods

#### Testing
- **25+ automated tests** covering all incremental update functionality
- 5 new test files:
  - `tests/test_transaction_tracker.py` (5 tests)
  - `tests/test_sheet_reader.py` (6 tests)
  - `tests/test_sheet_updater.py` (5 tests)
  - `tests/test_incremental_update.py` (5 integration tests)
  - `tests/test_edge_cases.py` (6 edge case tests)
- Manual testing confirmed 75-100% update efficiency

#### Performance Impact
- **70-94% reduction** in API write requests for typical updates
- Example: 4 teams with transactions → Update 4/16 sheets (75% efficiency)
- Example: No transactions → Update 0/16 sheets (100% efficiency)

#### Documentation
- Updated `README.md` with v2.0 features and usage examples
- Updated `CLAUDE.md` with comprehensive incremental update section
- Created `INCREMENTAL_UPDATE_CHANGELOG.md` for detailed technical reference
- Updated `tests/README.md` with new test documentation

**For detailed technical information, see [INCREMENTAL_UPDATE_CHANGELOG.md](INCREMENTAL_UPDATE_CHANGELOG.md)**

**Commits**:
- 0a9b119 - Implement Phases 3-5: Complete incremental update feature
- 6f547c7 - Implement Phase 1: Transaction tracking for incremental updates
- 9ea832b - Implement Phase 2: Sheet reading for incremental updates
- b448050 - Implement Phase 6: Testing, edge cases, and enhanced logging

---

### Fixed

#### Team Name Display Encoding (2025-11-16)

- **Bug Fix**: Fixed team, league, manager, and player names displaying as byte strings
  - Names were appearing as `b'Team Name'` instead of proper strings
  - Added `_decode_and_clean_text()` helper function to properly handle Yahoo API text encoding
  - Now correctly decodes bytes objects to UTF-8 strings
  - Optional emoji stripping capability for compatibility (not currently enabled)

**Files Modified**:
- `src/yahoo_data_fetcher.py`
  - Added `_decode_and_clean_text()` function with UTF-8 decoding and optional emoji removal
  - Applied to league names in `extract_league_data()` (line 260)
  - Applied to team names in `_extract_team_data()` (line 432)
  - Applied to manager names in `_extract_team_data()` (line 438)
  - Applied to player names in `_extract_player_data()` (lines 516, 518)

**Technical Details**:
- Handles both bytes and string inputs gracefully
- Uses UTF-8 decoding with error replacement for invalid characters
- Includes regex pattern for emoji removal (currently unused but available)
- Emoji pattern covers: emoticons, symbols, pictographs, transport symbols, flags, dingbats

**Impact**:
- All spreadsheet names now display correctly without byte string prefixes
- Improved readability in both Summary and individual team sheets
- Better user experience when viewing generated reports

**Commit**: 4598290 (2025-11-16)

---

## [1.0.0] - 2025-11-15

### Initial Release

Complete fantasy basketball roster and salary report generator with Google Sheets integration.

**Core Features**:
- 📊 Complete league data extraction from Yahoo Fantasy Basketball API
- 💰 100% salary coverage tracking (keeper costs, draft prices, FAAB acquisitions)
- 📈 Professional Google Sheets reports with formatted output
- 🔐 OAuth 2.0 authentication for Yahoo and Google APIs
- 🔄 Automatic token refresh
- 💻 Command-line interface
- 🚀 Headless environment support (WSL, servers)

**Modules**:
- `main.py` - Application entry point
- `config.py` - Configuration management
- `src/yahoo_data_fetcher.py` - Yahoo API integration
- `src/data_models.py` - Data structures (Player, Team, League)
- `src/data_processor.py` - Data validation and processing
- `src/google_auth.py` - Google Sheets authentication
- `src/sheet_generator.py` - Google Sheets generation
- `src/logger.py` - Logging configuration

**Authentication**:
- Yahoo OAuth via `src/auth/auth_with_code.py`
- Google OAuth via `src/auth/google_auth_manual.py`

**Tests**:
- `tests/test_league_extraction.py` - Yahoo data extraction
- `tests/test_full_integration.py` - Full integration (Yahoo + Google)

### Added

#### Remaining Salary Column and Conditional Formatting (2025-11-15)

- **New Feature**: Added "Remaining Salary" column to spreadsheet output
  - Shows how much budget each team has left after roster spending
  - Calculated as: Initial Budget - Total Salary
  - Appears in both Summary sheet (team overview table) and individual team sheets
  - Renamed from "FAAB Remaining" to "Remaining Salary" for clarity

- **New Feature**: Conditional formatting for budget status visualization
  - **GREEN** (RGB: 0.7, 0.9, 0.7): Applied when Remaining Salary > $0 (budget available)
  - **RED** (RGB: 0.95, 0.7, 0.7): Applied when Remaining Salary ≤ $0 (at or over budget limit)
  - Automatically highlights budget violations for quick identification
  - Applied to Summary sheet Column E (Remaining Salary) and individual team sheet summary rows

#### Code Changes

**Sheet Generator** (`src/sheet_generator.py`):
- Updated `create_summary_sheet()` method
  - Added "Remaining Salary" column to team overview table (Column E)
  - Added conditional format rules for Remaining Salary column (rows 21+)
  - Green background for teams with budget remaining (> 0)
  - Red background for teams at or over budget limit (≤ 0)

- Updated `create_team_sheet()` method
  - Renamed "FAAB REMAINING" row to "REMAINING SALARY"
  - Added conditional format rules for the remaining salary value cell
  - Same color coding logic as summary sheet (green > 0, red ≤ 0)

- Added Google Sheets API conditional formatting using `addConditionalFormatRule` requests
  - `NUMBER_GREATER` condition for green formatting (> 0)
  - `NUMBER_LESS_THAN_EQ` condition for red formatting (≤ 0)

#### Benefits

- **Quick Visual Identification**: Instantly see which teams are over/at budget without reading numbers
- **Budget Management**: Helps managers track their remaining salary cap at a glance
- **League Monitoring**: Commissioners can quickly identify potential budget violations
- **Professional Presentation**: Clean, color-coded data visualization improves report readability

#### Testing

- Test spreadsheet created with sample teams
- Verified formatting with three scenarios:
  - Team with budget remaining ($75) → GREEN ✓
  - Team at limit ($0) → RED ✓
  - Team over budget (-$15) → RED ✓
- Confirmed conditional formatting appears correctly in both Summary and team sheets

#### Roster Position Tracking and IL/IL+ Exclusion

- **New Feature**: Added roster position column to output documents
  - Shows each player's current roster slot (PG, SG, BN, IL, IL+, Util, etc.)
  - Distinguishes between player eligibility (Position) and actual roster slot (Slot)

- **New Feature**: IL/IL+ players excluded from total salary calculation
  - Players on injured list (IL or IL+) no longer count toward team salary cap
  - Total salary now accurately reflects active roster spending
  - Document output includes note about IL/IL+ exclusion

#### Code Changes

**Data Models** (`src/data_models.py`):
- Added `roster_position` field to `Player` dataclass
  - Stores current roster slot from Yahoo API's `selected_position.position`
  - Optional field, defaults to None
- Updated `calculate_total_salary()` method in `Team` class
  - Excludes players with `roster_position` in ('IL', 'IL+')
  - Added documentation explaining IL/IL+ exclusion
- Updated `create_player_from_yahoo_data()` factory function
  - Added `roster_position` parameter
- Enhanced `Player.__str__()` method
  - Now includes roster position in square brackets (e.g., "[IL]")

**Data Fetcher** (`src/yahoo_data_fetcher.py`):
- Updated `_extract_player_data()` method
  - Extracts `selected_position.position` from Yahoo API player objects
  - Passes roster position to player factory function

**Document Generator** (`src/document_generator.py`):
- Updated table format to include "Slot" column
  - Added between "Pos" and "Salary" columns
  - Shows roster position or 'N/A' if not available
- Adjusted table width from 60 to 70 characters
- Updated test data to include roster positions

#### Documentation Updates

**PLAN.md**:
- Updated document structure diagram to show new 5-column table format
- Added column descriptions explaining Position vs. Slot
- Added note about IL/IL+ exclusion from total salary
- Updated data structure to include `roster_position` field

**SALARY_DATA_FINDINGS.md**:
- Enhanced Player object structure documentation
- Added note distinguishing `display_position` from `selected_position.position`
- Updated example roster table to include Slot column
- Added IL/IL+ exclusion note with example calculations
- Updated implementation example code to extract roster position

**README.md**:
- Added "Slot" column to output description
- Added note that total salary excludes IL/IL+ players
- Added "Roster Position Tracking" to key features
- Added "IL/IL+ Exclusion" to key features

#### Tests

- Created `tests/test_il_exclusion.py`
  - Verifies IL and IL+ players are excluded from salary calculation
  - Tests with mixed roster (active players, bench, IL, IL+)
  - ✓ All tests passing

- Created `tests/test_roster_position_output.py`
  - Demonstrates new output format with roster position column
  - Shows IL/IL+ exclusion in action
  - ✓ Output format validated

- **Reorganized Test Files**
  - Moved all test files to `tests/` directory
  - Updated test execution to use module syntax: `python -m tests.test_name`
  - Files moved:
    - `test_league_extraction.py` → `tests/test_league_extraction.py`
    - `test_full_integration.py` → `tests/test_full_integration.py`
    - `test_il_exclusion.py` → `tests/test_il_exclusion.py`
    - `test_roster_position_output.py` → `tests/test_roster_position_output.py`

### Example Output

**Before**:
```
Player Name                    Pos     Salary Source
--------------------------------------------------------------
Joel Embiid                    C     $     25 DRAFT
--------------------------------------------------------------
TOTAL SALARY                          $    321
```

**After**:
```
Player Name                    Pos   Slot     Salary Source
----------------------------------------------------------------------
Joel Embiid                    C     IL     $     25 DRAFT
----------------------------------------------------------------------
TOTAL SALARY                                $    296
```
*Note: Joel Embiid's $25 salary is excluded from total due to IL position*

### Impact

- **More Accurate Reporting**: Total salaries now reflect actual salary cap usage
- **Better Visibility**: Users can see which players are injured and not counting toward cap
- **Yahoo Fantasy Compliance**: Matches how Yahoo Fantasy calculates active roster salaries
- **Backward Compatible**: Existing data extraction and processing remains functional
