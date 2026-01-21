# Fantasy Basketball Roster & Salary Report Generator

A Python application that extracts fantasy basketball league data from Yahoo Fantasy Sports and generates beautifully formatted Google Sheets reports with complete team rosters, player information, and salary data.

## Features

- 📊 **Complete League Data Extraction** - Pulls all teams, players, and roster information from Yahoo Fantasy Basketball
- 💰 **100% Salary Coverage** - Tracks player salaries from keeper costs, draft auction prices, and FAAB waiver acquisitions
- 📈 **Professional Google Sheets Reports** - Generates formatted spreadsheets with:
  - Summary sheet with league statistics
  - Draft Picks sheet for manual tracking (unprotected)
  - Individual team sheets with complete rosters
  - Currency formatting, frozen headers, and color-coded sections
  - Players sorted by salary (highest to lowest)
- 🔒 **Sheet Protection** - Automatic protection for data integrity
  - Summary and team sheets protected (owner-only edit access)
  - Draft Picks sheet unprotected for collaborative editing
  - Prevents accidental changes to league data
- ⚡ **Incremental Updates** - Efficiently update existing spreadsheets
  - Only updates teams with roster changes (75-100% efficiency)
  - Tracks transactions since last update
  - Preserves all formatting and structure
  - Automatic team rename handling (v2.3)
  - Orphaned sheet cleanup (v2.3)
  - Force full update option available
- 🔐 **OAuth 2.0 Authentication** - Secure authentication with both Yahoo and Google APIs
- 🔄 **Automatic Token Refresh** - Tokens refresh automatically, no repeated authentication needed
- 💻 **Command-Line Interface** - Easy-to-use CLI with customizable options
- 🚀 **Headless Environment Support** - Works in WSL and server environments without browser callbacks
- 🔔 **Discord Notifications** - Optional Discord webhook integration for automated updates
  - Rich embedded notifications with update summaries
  - Error alerts with role mentions
  - Efficiency metrics and transaction details
  - Zero cost, minimal setup required

## How It Works

1. **Connects to Yahoo Fantasy API** - Authenticates via OAuth 2.0 and extracts complete league data
2. **Processes Salary Data** - Determines each player's salary using a priority system:
   - FAAB Waiver acquisitions (most recent)
   - Keeper costs from previous seasons
   - Draft auction prices
   - Free agents ($0)
3. **Generates Google Sheets** - Creates a professionally formatted spreadsheet with:
   - A summary sheet showing league-wide statistics (protected)
   - A Draft Picks sheet for manual tracking (unprotected, blank)
   - Individual sheets for each team's roster (tracked by team ID, not name, protected)
   - Complete player details including salary and acquisition source
   - Automatic handling of team renames (sheets update to match current names)
   - Sheet protection to prevent accidental edits (optional)

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Yahoo Fantasy Sports account with a fantasy basketball league
- Google account for Google Sheets access

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd fantasy_basketball

# Install dependencies
uv sync
```

### Configuration

1. **Yahoo API Credentials**:
   - Create an app at [Yahoo Developer Network](https://developer.yahoo.com/apps/)
   - Add credentials to `.env`:
     ```
     YAHOO_CONSUMER_KEY=your_key_here
     YAHOO_CONSUMER_SECRET=your_secret_here
     NBA_LEAGUE_ID=your_league_id
     NBA_GAME_ID=466
     ```

2. **Google API Credentials**:
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Google Sheets API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials JSON to `credentials/` directory
   - Add to `.env`:
     ```
     GOOGLE_CREDENTIALS_PATH=credentials/client_secret_*.json
     ```

3. **Sheet Protection (Optional)**:
   - To protect all sheets except Draft Picks from accidental edits, add to `.env`:
     ```
     OWNER_EMAIL=youremail@gmail.com
     ```
   - Only the specified email can edit protected sheets
   - Leave blank to disable sheet protection (all sheets editable by anyone with access)

4. **Discord Notifications (Optional)**:
   - Open your Discord server → Select channel → Channel Settings → Integrations
   - Click "Create Webhook" → Name it "Fantasy Basketball Bot"
   - Copy webhook URL and add to `.env`:
     ```
     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
     ```
   - *Optional*: For error role mentions, create a role in Discord, enable mentions, and add:
     ```
     DISCORD_ALERT_ROLE_ID=123456789012345678
     ```
   - Leave blank to disable Discord notifications

### Authentication

**First-time setup:**

```bash
# Authenticate with Yahoo
uv run python -m src.auth.auth_with_code

# Authenticate with Google
uv run python -m src.auth.google_auth_manual
```

Follow the prompts to complete OAuth authentication for each service.

## Usage

### Generate a New Report (Create Mode)

```bash
# Generate new report for your league
uv run python main.py

# Custom spreadsheet title
uv run python main.py --title "Week 4 Salary Report"

# Different league
uv run python main.py --league-id 12345
```

The application will:
1. Validate configuration
2. Extract league data from Yahoo Fantasy API
3. Generate a new Google Sheets report with:
   - Summary sheet (protected)
   - Draft Picks sheet (unprotected)
   - Team sheets (protected)
4. Print the spreadsheet URL

### Update an Existing Report (Incremental Update Mode)

```bash
# Update existing spreadsheet (by URL)
uv run python main.py --spreadsheet-url "https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit"

# Update existing spreadsheet (by ID)
uv run python main.py --spreadsheet-id "SPREADSHEET_ID"

# Force update all teams (ignore transactions)
uv run python main.py --spreadsheet-id "SPREADSHEET_ID" --force-full-update

# Update with detailed transaction logging
uv run python main.py --spreadsheet-id "SPREADSHEET_ID" --verbose
```

The application will:
1. Read the last update timestamp from the existing spreadsheet
2. Ensure Draft Picks sheet exists (create if missing)
3. Fetch transactions since last update
4. Update **only teams with roster changes** (or all teams with `--force-full-update`)
5. Clear Draft Picks sheet (only with `--force-full-update`)
6. Update Summary sheet with current statistics
7. Apply sheet protection (if configured)
8. Print efficiency metrics

**Update Efficiency Examples:**
- 4 teams had transactions → Updates 4/16 teams (75% efficiency), Draft Picks preserved
- No transactions → Updates 0/16 teams, summary only (100% efficiency), Draft Picks preserved
- Force full update → Updates all 16 teams, **Draft Picks cleared**

### Command-Line Options

```bash
# Verbose logging for debugging
uv run python main.py --verbose

# Force create new spreadsheet
uv run python main.py --create-new

# Show help
uv run python main.py --help
```

## Automated Daily Updates (GitHub Actions)

You can schedule automatic daily updates of your spreadsheet using GitHub Actions (zero cost):

1. **Complete local setup first** - Authenticate with both Yahoo and Google APIs locally
2. **Follow the setup guide** - See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for detailed instructions
3. **Configure GitHub Secrets** - Add your API credentials and tokens to GitHub
4. **Enable the workflow** - Push the workflow file to GitHub
5. **Test and monitor** - Trigger manually first, then monitor scheduled runs

**Benefits:**
- Runs automatically every day at your chosen time
- No local machine needed (cloud-based)
- Free tier is more than sufficient
- Email notifications on failure
- Discord notifications for updates and errors (optional)
- Easy to monitor via GitHub Actions UI

**Quick Start:**
```bash
# 1. Ensure local authentication works
uv run python main.py --spreadsheet-id YOUR_ID

# 2. Push workflow to GitHub
git add .github/workflows/daily-update.yml
git commit -m "Add daily update workflow"
git push origin main

# 3. Add secrets to GitHub (see GITHUB_ACTIONS_SETUP.md)

# 4. Test via GitHub Actions UI
# Go to Actions tab → Daily Fantasy Basketball Update → Run workflow
```

For complete setup instructions, troubleshooting, and maintenance guide, see **[GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)**.

## Example Output

**Generated Spreadsheet Includes:**

- **Summary Sheet** (protected):
  - League name, season, and team count
  - Total players and average roster size
  - Salary statistics (total, averages)
  - FAAB budget information
  - Complete team summary table

- **Draft Picks Sheet** (unprotected):
  - Blank sheet for manual tracking of draft picks
  - Content preserved during normal updates
  - Cleared during force full updates
  - Position: Right after Summary tab

- **Team Sheets** (one per team, protected):
  - Team name and manager
  - Player roster table with columns:
    - Player Name
    - Position (eligible positions)
    - Slot (current roster position: PG, BN, IL, IL+, etc.)
    - NBA Team
    - Salary
    - Acquisition Source (Keeper/Draft/FAAB Waiver/Free Agent)
  - Total salary for the team (excludes players in IL/IL+ positions)
  - Remaining FAAB budget

**Sample Statistics from Real League:**
- 16 teams processed
- 280 players with complete data
- 100% salary coverage
- $3,490 total league salary
- $218.12 average team salary

## Project Structure

```
fantasy_basketball/
   main.py                    # Main application entry point
   config.py                  # Configuration management
   src/
      auth/                  # OAuth authentication utilities
      yahoo_data_fetcher.py  # Yahoo Fantasy API integration
      data_models.py         # Data structures (Player, Team, League)
      data_processor.py      # Data validation and processing
      google_auth.py         # Google Sheets authentication
      sheet_generator.py     # Google Sheets generation
      sheet_reader.py        # Read existing sheets (incremental updates)
      sheet_updater.py       # Update existing sheets (incremental updates)
      transaction_tracker.py # Track transactions (incremental updates)
      discord_notifier.py    # Discord webhook notifications
      logger.py              # Logging configuration
   credentials/               # API credentials (gitignored)
   tests/                     # Test suite
   .env                       # Environment variables (gitignored)
```

## Technical Details

### Salary Retrieval Strategy

For keeper leagues with auction drafts, the application determines player salaries using a priority system:

1. **FAAB Waiver Acquisitions** (highest priority) - Most recent FAAB bid
2. **Keeper Costs** - Salary from previous season for kept players
3. **Draft Auction Prices** - Initial draft cost for newly drafted players
4. **Free Agents** - $0 for players picked up without FAAB

This ensures accurate current salaries, even for players who were dropped and re-acquired.

### Key Features

- **Current Week Rosters** - Fetches rosters from the current week, not historical data
- **100% Coverage** - Successfully retrieves salary data for all players
- **Roster Position Tracking** - Shows each player's current roster slot (starting lineup, bench, IL, etc.)
- **IL/IL+ Exclusion** - Players on injured list are excluded from total salary calculations
- **Draft Picks Tracking** - Dedicated unprotected sheet for manual draft pick tracking
- **Sheet Protection** - Automatic protection prevents accidental edits to league data
- **Automatic Token Refresh** - OAuth tokens refresh automatically for both APIs
- **Professional Formatting** - Frozen headers, currency formatting, color-coded sections
- **Error Handling** - Comprehensive error messages and logging

## Development

### Running Tests

```bash
# Core functionality tests
uv run python -m tests.test_league_extraction        # Yahoo data extraction
uv run python -m tests.test_full_integration         # Full integration (Yahoo + Google)
uv run python -m tests.test_il_exclusion             # IL/IL+ exclusion logic
uv run python -m tests.test_roster_position_output   # Roster position output

# Incremental update tests
uv run python -m tests.test_transaction_tracker      # Transaction tracking (5 tests)
uv run python -m tests.test_sheet_reader             # Sheet reading (6 tests)
uv run python -m tests.test_sheet_updater            # Sheet updating (5 tests)
uv run python -m tests.test_incremental_update       # Integration (5 tests)
uv run python -m tests.test_edge_cases               # Edge cases (6 tests)
```

**Test Coverage:** 25+ automated tests covering all incremental update functionality

### Dependencies

- **yfpy** - Yahoo Fantasy Sports Python library
- **google-api-python-client** - Google API client
- **google-auth** - Google authentication
- **google-auth-oauthlib** - OAuth 2.0 support
- **discord-webhook** - Discord webhook notifications (optional)
- **python-dotenv** - Environment variable management

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

```bash
# Re-authenticate with Yahoo
uv run python -m src.auth.auth_with_code

# Re-authenticate with Google
uv run python -m src.auth.google_auth_manual
```

### Common Issues

- **ModuleNotFoundError**: Always use `uv run python` instead of `python3` or `python`
- **Token Expired**: Tokens refresh automatically, but can be manually regenerated using auth scripts
- **WSL/Headless Environment**: Use the manual authentication scripts (`auth_with_code.py`, `google_auth_manual.py`)

## Documentation

### Current Documentation
- **CHANGELOG.md** - Complete version history and release notes
- **INCREMENTAL_UPDATE_CHANGELOG.md** - Detailed technical reference for v2.0 incremental updates
- **CLAUDE.md** - Developer documentation and project overview
- **README.md** - This file - User guide and quick start
- **TODO.md** - Complete task list and project status
- **tests/README.md** - Test suite documentation
- **GITHUB_ACTIONS_SETUP.md** - Complete guide for setting up automated daily updates
- **DEPLOYMENT_OPTIONS.md** - Research and analysis of deployment options

### Planning Documents
- **context/INCREMENTAL_UPDATE_PLAN.md** - Incremental update feature implementation plan (v2.0)
- **context/PLAN.md** - Original implementation plan (v1.0)

### Historical Documentation (Archived)
- **context/archive/** - Historical documentation from earlier development phases
  - See [context/archive/README.md](context/archive/README.md) for details

## License

[Add your license information here]

## Acknowledgments

- Built with [yfpy](https://github.com/uberfastman/yfpy) for Yahoo Fantasy Sports API integration
- Uses Google Sheets API for report generation
- Developed using [uv](https://github.com/astral-sh/uv) for fast Python package management

---

**Status**: ✅ Production-ready with Draft Picks tracking and sheet protection (v2.6)

**Recent Updates:**
- **v2.6** - Draft Picks sheet and sheet protection
  - Draft Picks sheet automatically created for manual tracking
  - Sheet protection prevents accidental edits (owner-only access)
  - Draft Picks remains unprotected for collaborative editing
  - Protection applied during sheet creation and updates
- **v2.5** - Rate limit optimization with batch read API (82% API call reduction)
- **v2.4** - Automatic retry with exponential backoff for rate limits
- **v2.3** - Automatic team rename handling and orphaned sheet cleanup
  - Sheet renaming when teams change names in Yahoo Fantasy
  - Automatic deletion of orphaned sheets from renamed/removed teams
  - ID-based sheet tracking (invisible metadata in column A)
  - Backwards compatible with existing spreadsheets (auto-migration)
- **v2.2** - Discord webhook integration for automated notifications
  - Rich embedded notifications with update summaries and error alerts
  - Optional role mentions for critical errors
- **v2.0** - Incremental update mode with transaction tracking
  - 75-100% efficiency by only updating changed teams

For detailed technical documentation, see [CLAUDE.md](CLAUDE.md).
