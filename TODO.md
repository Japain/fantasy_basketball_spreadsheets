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
- [ ] Set up Yahoo OAuth credentials in `.env`
  - [ ] Add `YAHOO_CONSUMER_SECRET` (key already exists)
  - [ ] Add `NBA_LEAGUE_ID` (already exists)
  - [ ] Add `NBA_GAME_ID` (already exists)
- [ ] Create `src/logger.py` with basic logging configuration
- [ ] Create initial `src/yahoo_data_fetcher.py` with authentication setup
- [ ] Test Yahoo API authentication (initial OAuth flow)
- [ ] **CRITICAL**: Investigate salary data availability
  - [ ] Retrieve and inspect league info (`get_league_info()`)
  - [ ] Inspect league teams (`get_league_teams()`)
  - [ ] Examine team roster data structure (`get_team_roster_by_week()`)
  - [ ] Check draft results for auction prices (`get_league_draft_results()`)
  - [ ] Inspect player model for salary/contract fields
  - [ ] Check team budget fields (`auction_budget_total`, `auction_budget_spent`)
  - [ ] Document findings on how to obtain salary data
  - [ ] Determine fallback strategy if needed

### Data Model Definition
- [ ] Based on API investigation, define data structures in `src/data_models.py`:
  - [ ] Player data model
  - [ ] Team data model
  - [ ] League data model
- [ ] Document actual field names from Yahoo API

## Phase 2: Yahoo Data Retrieval Implementation

### Yahoo Data Fetcher Module
- [ ] Implement `get_league_teams()` function
- [ ] Implement `get_team_roster(team_id)` function
- [ ] Implement `get_player_salary(player_id)` or equivalent based on investigation
- [ ] Implement `extract_league_data()` for complete data retrieval
- [ ] Add error handling for API failures
- [ ] Add retry logic with exponential backoff
- [ ] Implement response caching (leverage yfpy's built-in caching)
- [ ] Add logging for all API calls

### Data Processing Module
- [ ] Create `src/data_processor.py`
- [ ] Implement `normalize_player_data(player_obj)` function
- [ ] Implement `calculate_team_totals(roster)` function
- [ ] Implement `sort_teams(teams, by="name")` function
- [ ] Implement `validate_data(league_data)` function with checks for:
  - [ ] All teams have rosters
  - [ ] All players have required fields
  - [ ] Salary values are valid
  - [ ] Position data is present
- [ ] Add logging for validation errors
- [ ] Add error handling for missing/invalid data

### Testing Yahoo Integration
- [ ] Create `tests/fixtures/sample_responses.json` with mock data
- [ ] Create `tests/test_yahoo_fetcher.py`
- [ ] Create `tests/test_data_processor.py`
- [ ] Test with real league data (manual test)
- [ ] Verify all teams and players are retrieved correctly
- [ ] Verify salary data is accurate

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

**Phase**: Phase 1: Foundation & Discovery (In Progress)
**Last Updated**: 2025-11-14
**Completed**: Project Setup
**Next**: Yahoo API Setup & Investigation
**Blockers**: None

## Notes

- Start with Phase 1 salary data investigation - this is CRITICAL to project success
- Yahoo API caching is handled by yfpy automatically in `league_data/` directory
- Both APIs require OAuth - expect browser-based authentication flows initially
- Google Docs API uses batch update requests - minimize API calls where possible
- Keep sensitive credentials out of git repository at all times
