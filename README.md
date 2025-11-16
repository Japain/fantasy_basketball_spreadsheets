# Fantasy Basketball Roster & Salary Report Generator

A Python application that extracts fantasy basketball league data from Yahoo Fantasy Sports and generates beautifully formatted Google Sheets reports with complete team rosters, player information, and salary data.

## Features

- 📊 **Complete League Data Extraction** - Pulls all teams, players, and roster information from Yahoo Fantasy Basketball
- 💰 **100% Salary Coverage** - Tracks player salaries from keeper costs, draft auction prices, and FAAB waiver acquisitions
- 📈 **Professional Google Sheets Reports** - Generates formatted spreadsheets with:
  - Summary sheet with league statistics
  - Individual team sheets with complete rosters
  - Currency formatting, frozen headers, and color-coded sections
  - Players sorted by salary (highest to lowest)
- 🔐 **OAuth 2.0 Authentication** - Secure authentication with both Yahoo and Google APIs
- 🔄 **Automatic Token Refresh** - Tokens refresh automatically, no repeated authentication needed
- 💻 **Command-Line Interface** - Easy-to-use CLI with customizable options
- 🚀 **Headless Environment Support** - Works in WSL and server environments without browser callbacks

## How It Works

1. **Connects to Yahoo Fantasy API** - Authenticates via OAuth 2.0 and extracts complete league data
2. **Processes Salary Data** - Determines each player's salary using a priority system:
   - FAAB Waiver acquisitions (most recent)
   - Keeper costs from previous seasons
   - Draft auction prices
   - Free agents ($0)
3. **Generates Google Sheets** - Creates a professionally formatted spreadsheet with:
   - A summary sheet showing league-wide statistics
   - Individual sheets for each team's roster
   - Complete player details including salary and acquisition source

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

### Generate a Report

```bash
# Generate report for your league
uv run python main.py
```

The application will:
1.  Validate configuration
2.  Extract league data from Yahoo Fantasy API
3.  Generate a Google Sheets report
4.  Print the spreadsheet URL

### Command-Line Options

```bash
# Custom spreadsheet title
uv run python main.py --title "Week 4 Salary Report"

# Different league
uv run python main.py --league-id 12345

# Verbose logging for debugging
uv run python main.py --verbose

# Show help
uv run python main.py --help
```

## Example Output

**Generated Spreadsheet Includes:**

- **Summary Sheet**:
  - League name, season, and team count
  - Total players and average roster size
  - Salary statistics (total, averages)
  - FAAB budget information
  - Complete team summary table

- **Team Sheets** (one per team):
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
- **Automatic Token Refresh** - OAuth tokens refresh automatically for both APIs
- **Professional Formatting** - Frozen headers, currency formatting, color-coded sections
- **Error Handling** - Comprehensive error messages and logging

## Development

### Running Tests

```bash
# Test Yahoo data extraction
uv run python -m tests.test_league_extraction

# Test full integration (Yahoo + Google Sheets)
uv run python -m tests.test_full_integration

# Test IL/IL+ exclusion logic
uv run python -m tests.test_il_exclusion

# Test roster position output format
uv run python -m tests.test_roster_position_output
```

### Dependencies

- **yfpy** - Yahoo Fantasy Sports Python library
- **google-api-python-client** - Google API client
- **google-auth** - Google authentication
- **google-auth-oauthlib** - OAuth 2.0 support
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

- **CLAUDE.md** - Developer documentation and project overview
- **context/TODO.md** - Complete task list and project status
- **context/SESSION_NOTES.md** - Detailed session history and implementation notes
- **context/SALARY_DATA_FINDINGS.md** - Salary data investigation results
- **context/FAAB_INVESTIGATION_SUMMARY.md** - FAAB transaction analysis

## License

[Add your license information here]

## Acknowledgments

- Built with [yfpy](https://github.com/uberfastman/yfpy) for Yahoo Fantasy Sports API integration
- Uses Google Sheets API for report generation
- Developed using [uv](https://github.com/astral-sh/uv) for fast Python package management

---

**Status**:  Production-ready and fully functional

For detailed technical documentation, see [CLAUDE.md](CLAUDE.md).
