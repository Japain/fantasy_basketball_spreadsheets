# Fantasy Basketball Roster & Salary Report Generator - Implementation Plan

## Project Overview

Build a Python application that retrieves roster and salary information from a Yahoo Fantasy Basketball league using the yfpy library and Yahoo Fantasy API, then generates a formatted Google Document displaying each team's roster with player names, positions, and salaries.

## Quick Start

**For implementation steps**: See [TODO.md](./TODO.md) for a detailed, actionable checklist of all tasks.

**Critical First Step**: Before building anything, we must investigate whether salary data is available through the Yahoo Fantasy API. This will determine our entire data retrieval strategy (see Phase 1 in TODO.md).

## Key Challenges & Considerations

### 1. Salary Data Availability
**Challenge**: Yahoo Fantasy API documentation does not explicitly mention current player salary endpoints for salary cap leagues.

**Investigation Required**:
- Yahoo supports salary cap/auction leagues with budget tracking
- Draft results contain auction prices paid for players
- Team data includes `auction_budget_total` and `auction_budget_spent`
- Need to determine if current player salaries are available via:
  - Team roster endpoint with specific parameters
  - Player data with salary information
  - Draft analysis sub-resource
  - Transaction history (trades might show salary)

**Fallback Strategy**: If current salaries aren't available via API, we may need to:
- Use draft auction prices as "salary"
- Calculate from budget spent and player acquisitions
- Use external data sources (if acceptable)

### 2. Authentication Complexity
Both Yahoo and Google require OAuth 2.0 authentication, requiring credential management and token handling.

## Architecture Design

### Phase 1: Yahoo Fantasy API Integration

#### 1.1 Authentication Setup
**Components**:
- Yahoo OAuth 2.0 configuration
- Consumer key and secret from `.env`
- Token storage and refresh mechanism (yfpy handles this)
- Browser-based OAuth flow for initial authentication

**Implementation**:
```python
from yfpy.query import YahooFantasySportsQuery

# Configure authentication
yahoo_query = YahooFantasySportsQuery(
    league_dir="league_data",  # Cache directory
    game_code="nba",
    game_id="466",  # Current NBA season
    league_id="YOUR_LEAGUE_ID",
    yahoo_consumer_key=YAHOO_CONSUMER_KEY,
    yahoo_consumer_secret=YAHOO_CONSUMER_SECRET
)
```

#### 1.2 Data Discovery & Investigation
**Critical First Step**: Explore API responses to understand salary data structure

**Tasks**:
1. Retrieve league information and validate access
2. Get all teams in the league
3. For each team, retrieve roster data
4. Inspect player objects for salary/contract fields
5. Check team budget information
6. Examine draft results for auction prices
7. Document actual data structure found

**Key Methods to Explore**:
- `yahoo_query.get_league_info()`
- `yahoo_query.get_league_teams()`
- `yahoo_query.get_team_roster_by_week(team_id, week)`
- `yahoo_query.get_league_draft_results()`
- Player model fields inspection

#### 1.3 Data Retrieval Module
**File**: `src/yahoo_data_fetcher.py`

**Functions**:
- `get_league_teams()` → List of team objects
- `get_team_roster(team_id)` → List of players with details
- `get_player_salary(player_id)` → Salary value (if available)
- `extract_league_data()` → Complete league data structure

**Data Structure to Build**:
```python
league_data = {
    "league_name": str,
    "league_id": str,
    "season": str,
    "teams": [
        {
            "team_id": str,
            "team_name": str,
            "manager_name": str,
            "roster": [
                {
                    "player_name": str,
                    "position": str,
                    "salary": int,  # Player salary/cost
                    "source": str,  # "Keeper", "Draft", "FAAB Waiver", or "Free Agent"
                    "player_id": str
                }
            ],
            "total_salary": int,
            "faab_remaining": int  # Renamed from budget_remaining
        }
    ]
}
```

### Phase 2: Data Processing

#### 2.1 Data Transformation Module
**File**: `src/data_processor.py`

**Functions**:
- `normalize_player_data(player_obj)` → Standardized player dict
- `calculate_team_totals(roster)` → Aggregate salary info
- `sort_teams(teams, by="name")` → Ordered team list
- `validate_data(league_data)` → Check for missing/invalid data

**Validation Checks**:
- All teams have rosters
- All players have required fields
- Salary values are valid numbers
- Position data is present

### Phase 3: Google Docs Integration

#### 3.1 Google API Authentication
**Setup Requirements**:
1. Create Google Cloud Project
2. Enable Google Docs API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials JSON
5. Store in project (gitignored)

**Dependencies**:
```bash
uv add google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

**Implementation**:
**File**: `src/google_auth.py`

```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents']

def get_google_docs_service():
    """Authenticate and return Google Docs service object"""
    # Token storage and refresh logic
    # Return service object
```

#### 3.2 Document Generation Module
**File**: `src/document_generator.py`

**Functions**:
- `create_document(title)` → Document ID
- `add_title(doc_id, title_text)` → Format main title
- `add_team_section(doc_id, team_data)` → Add team roster table
- `format_table(doc_id, table_data)` → Apply styling
- `generate_league_report(league_data)` → Complete document

**Document Structure**:
```
[Title] League Name - Roster & Salary Report
[Subtitle] Season Year

[Team 1 Header] Team Name (Manager: Manager Name)
┌─────────────────────┬──────────┬──────────┬───────────────┐
│ Player Name         │ Position │ Salary   │ Source        │
├─────────────────────┼──────────┼──────────┼───────────────┤
│ LeBron James        │ SF       │ $45      │ Keeper        │
│ Anthony Davis       │ C        │ $38      │ Draft         │
│ Russell Westbrook   │ PG       │ $3       │ FAAB Waiver   │
│ ...                 │ ...      │ ...      │ ...           │
├─────────────────────┼──────────┼──────────┼───────────────┤
│ Total Salary        │          │ $200     │               │
│ FAAB Remaining      │          │ $184     │               │
└─────────────────────┴──────────┴──────────┴───────────────┘

[Team 2 Header] ...
```

**Formatting Considerations**:
- Use Google Docs API batch update requests
- Apply text styles (bold, font size) for headers
- Create tables with proper borders (4 columns: Player, Position, Salary, Source)
- Add color highlighting for headers
- Sort players by position or salary
- Source column provides transparency on salary origin:
  - "Keeper" - Retained from previous season
  - "Draft" - Acquired in auction draft
  - "FAAB Waiver" - Acquired via FAAB bid
  - "Free Agent" - Picked up at no cost

### Phase 4: Application Entry Point

#### 4.1 Main Application
**File**: `main.py`

**Flow**:
1. Load configuration from `.env`
2. Validate required credentials present
3. Authenticate with Yahoo API
4. Fetch league data
5. Process and validate data
6. Authenticate with Google API
7. Generate Google Doc
8. Return document URL

**Command-line Interface**:
```bash
# Basic usage
uv run main.py

# With options
uv run main.py --league-id 12345 --season 2024
```

#### 4.2 Configuration Management
**File**: `config.py`

**Environment Variables** (`.env`):
```bash
# Yahoo API
YAHOO_CONSUMER_KEY=your_key
YAHOO_CONSUMER_SECRET=your_secret

# Google API
GOOGLE_CREDENTIALS_PATH=path/to/credentials.json

# League Configuration
NBA_LEAGUE_ID=68958
NBA_GAME_ID=449  # 2024-2025 season

# Output
CACHE_DIR=./league_data
```

### Phase 5: Error Handling & Logging

#### 5.1 Error Scenarios
- Yahoo API authentication failure
- Invalid league ID
- Network timeouts
- Missing salary data
- Google API quota exceeded
- Document creation failure
- Partial data retrieval

#### 5.2 Logging Strategy
**File**: `src/logger.py`

- Use Python `logging` module
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log API responses for debugging
- Log data validation issues
- Track document generation steps

### Phase 6: Testing

#### 6.1 Unit Tests
**Test Files**: `tests/test_*.py`

**Test Coverage**:
- Data transformation functions
- Salary calculation logic
- Data validation
- Configuration loading

#### 6.2 Integration Tests
- Mock Yahoo API responses
- Test full data flow
- Validate document structure

#### 6.3 Manual Testing Checklist
- [ ] OAuth flows work correctly
- [ ] League data retrieves successfully
- [ ] All teams included in output
- [ ] Player data complete and accurate
- [ ] Salary information correct
- [ ] Google Doc properly formatted
- [ ] Error handling works as expected

## Implementation Sequence

**Note**: Detailed task breakdown available in [TODO.md](./TODO.md). The sequence below provides high-level phases.

### Phase 1: Foundation & Discovery (Sprint 1)
**Goal**: Understand the data landscape and set up project foundation

1. Set up project structure (directories, config files)
2. Configure Yahoo API authentication
3. **Critical**: Investigate salary data availability through API exploration
4. Create data models based on actual API responses
5. Build basic data fetcher

**Success Criteria**: Yahoo API authenticated, salary data availability confirmed, data structure documented

### Phase 2: Yahoo Integration (Sprint 2)
**Goal**: Complete implementation of Yahoo data retrieval and processing

1. Implement complete Yahoo data retrieval (all teams, rosters, salaries)
2. Build data processing and validation
3. Add error handling and logging
4. Test with real league data

**Success Criteria**: Can reliably fetch and process all league data with proper error handling

### Phase 3: Google Docs Integration (Sprint 3)
**Goal**: Implement document generation with proper formatting

1. Set up Google API authentication
2. Implement document creation and title/subtitle formatting
3. Build table generation and formatting
4. Test document output with sample data

**Success Criteria**: Can generate properly formatted Google Doc with sample data

### Phase 4: Integration & Polish (Sprint 4)
**Goal**: Complete end-to-end flow and ensure production readiness

1. Integrate all components in main.py
2. End-to-end testing with real data
3. Error handling refinement
4. Documentation and code quality improvements
5. Final testing with various league configurations

**Success Criteria**: Application runs successfully from start to finish, producing properly formatted documents

## Project Structure

```
fantasy_basketball/
├── .env                          # Environment variables (gitignored)
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
├── CLAUDE.md
├── PLAN.md
├── TODO.md
├── SESSION_NOTES.md              # Development session notes
├── SALARY_DATA_FINDINGS.md       # Salary investigation results
├── FAAB_INVESTIGATION_SUMMARY.md # FAAB investigation summary
├── main.py                       # Application entry point
├── config.py                     # Configuration management
├── src/
│   ├── __init__.py
│   ├── auth/                    # Authentication utilities
│   │   ├── __init__.py
│   │   ├── README.md           # Auth documentation
│   │   ├── auth_with_code.py   # OAuth completion script
│   │   ├── test_auth.py        # Interactive auth test
│   │   └── complete_auth.py    # OAuth helper
│   ├── investigation/           # Investigation & exploration scripts
│   │   ├── README.md           # Investigation documentation
│   │   ├── investigate_salary_data.py    # API exploration
│   │   ├── investigate_roster.py         # Roster analysis
│   │   └── investigate_transactions.py   # FAAB investigation
│   ├── yahoo_data_fetcher.py    # Yahoo API integration
│   ├── data_processor.py        # Data transformation
│   ├── google_auth.py           # Google authentication
│   ├── document_generator.py    # Google Docs creation
│   └── logger.py                # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_data_processor.py
│   ├── test_yahoo_fetcher.py
│   └── fixtures/
│       └── sample_responses.json
├── league_data/                 # Yahoo API cache (gitignored)
└── credentials/                 # Google credentials (gitignored)
    └── google_credentials.json
```

## Dependencies

```toml
[project.dependencies]
yfpy = ">=17.0.0"                    # Yahoo Fantasy API wrapper
google-auth = ">=2.0.0"              # Google authentication
google-auth-oauthlib = ">=1.0.0"     # OAuth flow
google-auth-httplib2 = ">=0.2.0"     # HTTP transport
google-api-python-client = ">=2.0.0" # Google Docs API client
python-dotenv = ">=1.0.0"            # Already included with yfpy
```

## Security Considerations

1. **Never commit credentials**:
   - Add to `.gitignore`: `.env`, `credentials/`, `league_data/`, `token.json`

2. **Token management**:
   - Store OAuth tokens securely
   - Implement token refresh logic
   - Handle expired credentials gracefully

3. **API rate limiting**:
   - Respect Yahoo API rate limits
   - Implement exponential backoff
   - Cache responses when possible

4. **Data privacy**:
   - League data may be private
   - Document sharing should be controlled
   - Consider adding access control options

## Future Enhancements

1. **Multi-league support**: Generate reports for multiple leagues
2. **Historical tracking**: Compare salaries across weeks/seasons
3. **Export formats**: PDF, Excel, CSV in addition to Google Docs
4. **Scheduling**: Automated weekly report generation
5. **Analytics**: Add team rankings, value analysis, budget utilization charts
6. **Web interface**: Flask/FastAPI frontend for easier use
7. **Email distribution**: Send reports to league members

## Success Criteria

- ✅ Successfully authenticate with both Yahoo and Google APIs
- ✅ Retrieve complete roster data for all teams in league
- ✅ Obtain salary information for all players
- ✅ Generate properly formatted Google Document
- ✅ Document includes all teams, players, positions, and salaries
- ✅ Application handles errors gracefully
- ✅ Code is well-documented and maintainable

---

## Document Relationships

- **PLAN.md** (this file): High-level architecture, design decisions, technical considerations, and overall strategy
- **TODO.md**: Granular, actionable checklist of specific tasks to implement the plan
- **CLAUDE.md**: Development setup, conventions, and guidance for Claude Code when working on this codebase
- **README.md**: User-facing documentation (to be created during implementation)
