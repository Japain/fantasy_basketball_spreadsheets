# Fantasy Basketball Roster & Salary Report - TODO List

## Phase 1: Foundation & Discovery

### Project Setup
- [x] Create `src/` directory structure
- [x] Create `tests/` directory structure
- [x] Create `credentials/` directory (gitignored)
- [x] Update `.gitignore` to include:
  - `league_data/`
  - `credentials/`
  - `token.json`
  - `*.token`
- [x] Create `src/__init__.py`
- [x] Create `tests/__init__.py`
- [x] Create `config.py` for centralized configuration

### Yahoo API Setup & Investigation
- [x] Set up Yahoo OAuth credentials in `.env`
  - [x] Add `YAHOO_CONSUMER_SECRET` (key already exists)
  - [x] Add `NBA_LEAGUE_ID` (already exists)
  - [x] Add `NBA_GAME_ID` (already exists)
- [x] Create `src/logger.py` with basic logging configuration
- [x] Create initial `src/yahoo_data_fetcher.py` with authentication setup
- [x] Test Yahoo API authentication (initial OAuth flow)
- [x] Reorganize authentication scripts into `src/auth/` folder
  - [x] Create `src/auth/__init__.py`
  - [x] Move auth scripts to `src/auth/`
  - [x] Create `src/auth/README.md` with documentation
  - [x] Update imports to work from new location
  - [x] Update PLAN.md and CLAUDE.md with new structure
- [x] **CRITICAL**: Investigate salary data availability
  - [x] Retrieve and inspect league info (`get_league_info()`)
  - [x] Inspect league teams (`get_league_teams()`)
  - [x] Examine team roster data structure (`get_team_roster_by_week()`)
  - [x] Check draft results for auction prices (`get_league_draft_results()`)
  - [x] Inspect player model for salary/contract fields
  - [x] Check team budget fields (found `faab_balance` on teams)
  - [x] Document findings on how to obtain salary data
  - [x] Determine fallback strategy (not needed - data available!)

### Data Model Definition
- [x] Based on API investigation, define data structures in `src/data_models.py`:
  - [x] Player data model (with player_key, name, position, salary, source, nba_team)
  - [x] Team data model (with team_id, team_name, manager_name, roster, total_salary, faab_remaining)
  - [x] League data model (with league_id, league_name, season, num_teams, teams)
- [x] Document actual field names from Yahoo API (included in data models with factory functions)

## Phase 2: Yahoo Data Retrieval Implementation

### Yahoo Data Fetcher Module
- [x] Implement `get_league_teams()` function
- [x] Implement `get_team_roster(team_id)` function
- [x] Implement `_get_player_salary_and_source()` function with priority logic
- [x] Implement `extract_league_data()` for complete data retrieval
- [x] Implement `_build_draft_cost_map()` for draft auction prices
- [x] Implement `_build_faab_cost_map()` for FAAB waiver costs (most recent)
- [x] Implement `_extract_team_data()` for team processing
- [x] Implement `_extract_player_data()` for player processing
- [x] Add error handling for API failures
- [ ] Add retry logic with exponential backoff
- [x] Implement response caching (leverage yfpy's built-in caching)
- [x] Add logging for all API calls

### Data Processing Module
- [x] Create `src/data_processor.py`
- [x] Implement validation functions:
  - [x] `validate_league_data()` - Comprehensive league validation
  - [x] `validate_team_data()` - Team-level validation
  - [x] `validate_player_data()` - Player-level validation
  - [x] All teams have rosters check
  - [x] All players have required fields check
  - [x] Salary values are valid check
  - [x] Position data is present check
- [x] Implement sorting functions:
  - [x] `sort_teams()` - Sort by name, manager, salary, faab, or roster_size
  - [x] `sort_players()` - Sort by name, position, salary, source, or nba_team
- [x] Implement filtering functions:
  - [x] `filter_teams_by_criteria()` - Filter teams by salary/roster size
  - [x] `filter_players_by_source()` - Filter by acquisition source
  - [x] `filter_players_by_salary_range()` - Filter by salary range
- [x] Implement transformation functions:
  - [x] `normalize_player_data()` - Convert Player to dict
  - [x] `normalize_team_data()` - Convert Team to dict
  - [x] `normalize_league_data()` - Convert League to dict
  - [x] `calculate_team_totals()` - Calculate team statistics
  - [x] `get_league_summary()` - Generate league summary
- [x] Implement utility functions:
  - [x] `find_team_by_name()` - Find team by name
  - [x] `find_player_by_name()` - Find player by name
  - [x] `get_top_salaries()` - Get highest-paid players
- [x] Add logging for validation errors
- [x] Add error handling for missing/invalid data (ValidationError exception)

### Testing Yahoo Integration
- [ ] Create `tests/fixtures/sample_responses.json` with mock data
- [ ] Create `tests/test_yahoo_fetcher.py`
- [ ] Create `tests/test_data_processor.py`
- [x] Test with real league data (manual test) - `test_league_extraction.py`
- [x] Verify all teams and players are retrieved correctly (16 teams, 268 players)
- [x] Verify salary data is accurate (100% coverage, validation passed)

# Verify Team Rosters Align with Yahoo

## Phase 3: Google Docs Integration

### Google API Setup
- [ ] Add Google API dependencies:
  ```bash
  uv add google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
  ```
- [ ] Create Google Cloud Project
- [ ] Enable Google Docs API in Google Cloud Console
- [ ] Create OAuth 2.0 credentials (Desktop app)
- [ ] Download credentials JSON to `credentials/` directory
- [ ] Add `GOOGLE_CREDENTIALS_PATH` to `.env`
- [ ] Update CLAUDE.md with Google credentials information

### Google Authentication Module
- [ ] Create `src/google_auth.py`
- [ ] Implement `get_google_docs_service()` function
- [ ] Implement token storage logic
- [ ] Implement token refresh logic
- [ ] Add error handling for authentication failures
- [ ] Test OAuth flow manually

### Document Generation Module
- [ ] Create `src/document_generator.py`
- [ ] Implement `create_document(title)` function
- [ ] Implement `add_title(doc_id, title_text)` with formatting
- [ ] Implement `add_subtitle(doc_id, subtitle_text)` function
- [ ] Implement `add_team_section(doc_id, team_data)` function
- [ ] Implement table creation with proper structure:
  - [ ] Headers: Player Name | Position | Salary
  - [ ] Player rows
  - [ ] Total row with aggregated salary
  - [ ] Budget remaining row
- [ ] Implement table formatting:
  - [ ] Apply borders
  - [ ] Style headers (bold, background color)
  - [ ] Align salary values (right-aligned)
  - [ ] Format salary as currency
- [ ] Implement `generate_league_report(league_data)` orchestrator function
- [ ] Add error handling for API quota limits
- [ ] Add error handling for document creation failures
- [ ] Add logging for document generation steps

### Testing Google Docs Integration
- [ ] Test document creation
- [ ] Test table formatting
- [ ] Verify document structure matches design
- [ ] Test with sample league data
- [ ] Verify all teams appear in document
- [ ] Verify formatting is correct

## Phase 4: Main Application & Configuration

### Configuration Management
- [ ] Update `config.py` with:
  - [ ] Environment variable loading
  - [ ] Configuration validation
  - [ ] Default values
  - [ ] Helper functions for accessing config
- [ ] Ensure all required environment variables are documented in CLAUDE.md

### Main Application Flow
- [ ] Update `main.py` with complete flow:
  - [ ] Load and validate configuration
  - [ ] Initialize logger
  - [ ] Authenticate with Yahoo API
  - [ ] Fetch league data
  - [ ] Process and validate data
  - [ ] Authenticate with Google API
  - [ ] Generate Google Doc
  - [ ] Print document URL
  - [ ] Handle errors gracefully with user-friendly messages
- [ ] Add command-line argument parsing (optional: league-id, season)
- [ ] Add progress indicators for long-running operations
- [ ] Add summary output (teams processed, players included, etc.)

### Error Handling & Logging
- [ ] Review and enhance error handling across all modules
- [ ] Ensure all errors are logged appropriately
- [ ] Add user-friendly error messages
- [ ] Test error scenarios:
  - [ ] Invalid credentials
  - [ ] Network failures
  - [ ] Missing salary data
  - [ ] API quota exceeded
  - [ ] Invalid league ID

## Phase 5: Testing & Polish

### Integration Testing
- [ ] Create end-to-end test with real APIs (manual)
- [ ] Test with different league configurations
- [ ] Verify error handling in production-like scenarios
- [ ] Test OAuth token refresh flows

### Code Quality
- [ ] Add docstrings to all functions
- [ ] Add type hints where appropriate
- [ ] Review code for DRY violations
- [ ] Ensure consistent code style
- [ ] Add comments for complex logic

### Documentation
- [ ] Update README.md with:
  - [ ] Project description
  - [ ] Setup instructions
  - [ ] Usage examples
  - [ ] Troubleshooting guide
  - [ ] Screenshots/examples of generated documents
- [ ] Update CLAUDE.md if any development practices changed
- [ ] Document any API quirks or limitations discovered

### Final Testing Checklist
- [ ] Yahoo OAuth flow works correctly
- [ ] Google OAuth flow works correctly
- [ ] League data retrieves successfully
- [ ] All teams included in output
- [ ] Player data complete and accurate
- [ ] Salary information correct
- [ ] Google Doc properly formatted
- [ ] Error handling works as expected
- [ ] Application runs end-to-end without manual intervention
- [ ] Token refresh works for both APIs

## Phase 6: Future Enhancements (Optional)

- [ ] Add command-line options for output format
- [ ] Implement CSV export option
- [ ] Add player sorting options (by position, salary, name)
- [ ] Add league statistics summary section
- [ ] Implement multi-league support
- [ ] Add scheduling/automation capabilities

---

## Current Status

**Phase**: Phase 2: Yahoo Data Retrieval Implementation ✅ **COMPLETE**
**Last Updated**: 2025-11-14
**Completed**:
- ✅ **Phase 1: Foundation & Discovery COMPLETE**
  - ✅ Project Setup (directories, config, .gitignore)
  - ✅ Yahoo OAuth Authentication Setup & Testing
  - ✅ Authentication Code Organization (moved to src/auth/)
  - ✅ Successfully authenticated with Yahoo API
  - ✅ Retrieved basic league info (Squad Goals, League ID: 68958, 16 teams, Season 2025)
  - ✅ **CRITICAL Salary Data Investigation COMPLETE**
    - ✅ Salary data IS available through Yahoo API
    - ✅ Found three sources: keeper costs, draft auction prices, FAAB bids
    - ✅ Comprehensive findings documented in SALARY_DATA_FINDINGS.md
    - ✅ Implementation strategy defined (FAAB → Keeper → Draft → Free Agent)
- ✅ **Phase 2: Yahoo Data Retrieval Implementation COMPLETE**
  - ✅ Created `src/data_models.py` with Player, Team, League dataclasses
  - ✅ Added SalarySource enum for tracking acquisition source
  - ✅ Added factory functions for creating instances from Yahoo API data
  - ✅ Enhanced `src/yahoo_data_fetcher.py` with complete salary retrieval logic
    - ✅ Implemented `extract_league_data()` orchestration function
    - ✅ Implemented `_build_draft_cost_map()` and `_build_faab_cost_map()`
    - ✅ Implemented `_get_player_salary_and_source()` with priority logic
    - ✅ Implemented `_extract_team_data()` and `_extract_player_data()`
  - ✅ Built `src/data_processor.py` with comprehensive utilities
    - ✅ Validation functions (league, team, player)
    - ✅ Sorting and filtering functions
    - ✅ Transformation and normalization functions
    - ✅ Summary statistics and utility functions
  - ✅ **SUCCESSFULLY TESTED WITH REAL LEAGUE DATA**
    - ✅ Extracted all 16 teams, 268 players
    - ✅ **100% salary coverage** ($3,164 total)
    - ✅ Validation passed with no errors
    - ✅ Results output to `league_extraction_results.txt`

**Next**: Phase 3 - Google Docs Integration
- Set up Google API authentication
- Implement document generation module
- Create formatted Google Doc with league data

**Blockers**: None

**Notes**:
- This is a **keeper league** - players have keeper costs from previous seasons
- Salary = keeper cost (priority 1) OR draft cost (priority 2) OR FAAB bid (priority 3)
- See SALARY_DATA_FINDINGS.md for complete documentation
- Investigation scripts: `investigate_salary_data.py` and `investigate_roster.py`

## Notes

- Start with Phase 1 salary data investigation - this is CRITICAL to project success
- Yahoo API caching is handled by yfpy automatically in `league_data/` directory
- Both APIs require OAuth - expect browser-based authentication flows initially
- Google Docs API uses batch update requests - minimize API calls where possible
- Keep sensitive credentials out of git repository at all times
