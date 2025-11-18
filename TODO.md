# Fantasy Basketball Application - TODO List

## Current Status

**Application State**: ✅ **PRODUCTION READY**
- Core application fully functional (Phases 1-5 complete from original plan)
- Successfully generates Google Sheets from Yahoo Fantasy data
- 100% salary coverage across all players
- Professional formatting and conditional formatting implemented

**Next Major Feature**: 🚧 **Incremental Sheet Updates** - Phases 1-5 Complete ✅
- Goal: Update existing sheets instead of creating new ones each time
- Detect transactions since last run
- Only update affected teams
- Preserve existing "create new" functionality

**Progress**: Phase 5 of 7 complete (Foundation, Sheet Reading, Sheet Generator, Sheet Updater & Main Orchestration)

---

## Implementation Roadmap - Incremental Updates Feature

### Phase 1: Foundation & Transaction Detection ✅ **COMPLETE**

**Goal**: Build the foundation for tracking transactions and identifying affected teams

**Completion Date**: 2025-11-17

#### Task 1.1: Add TransactionInfo Data Model ✅
- [x] Open `src/data_models.py`
- [x] Add `TransactionType` enum (add, drop, trade, add/drop)
- [x] Add `TransactionInfo` dataclass with fields:
  - `transaction_id: str`
  - `timestamp: int` (Unix timestamp)
  - `team_id: str`
  - `team_name: str`
  - `transaction_type: TransactionType`
  - `player_name: str`
  - `faab_bid: Optional[int]`
- [x] Add helper function: `create_transaction_from_yahoo()` factory function
- [x] Test the data model with sample transaction data

**Success Criteria**: ✅ Can create TransactionInfo objects from Yahoo API transaction data

#### Task 1.2: Enhance YahooDataFetcher with Transaction Methods ✅
- [x] Open `src/yahoo_data_fetcher.py`
- [x] Add method: `get_all_transactions() -> List[Any]`
  - Access via `self.yahoo_query.get_league_transactions()`
  - Return raw transaction list from Yahoo API
- [x] Add method: `get_transactions_since(since_timestamp: int) -> List[Any]`
  - Filter transactions by timestamp
  - Return only transactions after `since_timestamp`
- [x] Add comprehensive logging for transaction retrieval
- [x] Add error handling for API failures

**Success Criteria**: ✅ Can retrieve all transactions and filter by timestamp

#### Task 1.3: Create Transaction Tracker Module ✅
- [x] Create new file: `src/transaction_tracker.py`
- [x] Import required modules (data_models, logger)
- [x] Implement `get_transactions_since(fetcher, last_run_timestamp) -> List[TransactionInfo]`
  - Call fetcher.get_transactions_since()
  - Convert Yahoo objects to TransactionInfo objects
  - Handle edge cases (None timestamp, invalid data)
- [x] Implement `get_affected_team_ids(transactions: List[TransactionInfo]) -> Set[str]`
  - Extract team IDs from transactions
  - For each transaction, check if team added or dropped a player
  - Return unique set of affected team IDs
- [x] Implement `parse_transaction_timestamp(transaction) -> int`
  - Extract timestamp from Yahoo transaction object
  - Convert to Unix timestamp
  - Handle timezone conversions (UTC)
- [x] Add comprehensive docstrings and type hints
- [x] Add logging for debugging
- [x] Add helper functions: `_determine_transaction_type()`, `_extract_player_name()`, `_extract_team_name()`

**Success Criteria**: ✅ Can identify which teams were affected by transactions since a given timestamp

#### Task 1.4: Test Transaction Detection ✅
- [x] Create test file: `tests/test_transaction_tracker.py`
- [x] Test `get_transactions_since()` with real league data
- [x] Test `get_affected_team_ids()` with sample transactions
- [x] Verify correct team IDs are identified
- [x] Test edge cases:
  - Empty transaction list
  - Transactions with no FAAB bid
  - Trades involving multiple teams
  - Future timestamps
  - Very old timestamps
- [x] Document test results

**Success Criteria**: ✅ All transaction tracking tests pass (5/5 tests passed)

**Phase 1 Test Results**:
- Total Transactions: 310 transaction records
- Transaction Types: 170 adds, 131 drops, 9 trades
- FAAB Activity: 155 waiver claims, $519 total spent
- Recent Activity (last 14 days): 153 transactions affecting 15 teams
- All 5 comprehensive tests passed ✅

---

### Phase 2: Sheet Reading ✅ **COMPLETE**

**Goal**: Read existing spreadsheets to extract timestamp and validate structure

**Completion Date**: 2025-11-17

#### Task 2.1: Create Sheet Reader Module - Core Functions ✅
- [x] Create new file: `src/sheet_reader.py`
- [x] Import required modules (google_auth, logger, datetime)
- [x] Implement `extract_spreadsheet_id_from_url(url: str) -> str`
  - Parse Google Sheets URL to extract spreadsheet ID
  - Handle different URL formats:
    - `https://docs.google.com/spreadsheets/d/{ID}/edit`
    - `https://docs.google.com/spreadsheets/d/{ID}`
  - Raise ValueError for invalid URLs
  - Add comprehensive error handling
  - Also supports raw spreadsheet IDs
- [x] Implement `_get_sheet_service() -> Any`
  - Return authenticated Google Sheets service
  - Handle authentication errors
- [x] Add docstrings and type hints

**Success Criteria**: ✅ Can extract spreadsheet ID from various URL formats

#### Task 2.2: Implement Timestamp Reading ✅
- [x] In `src/sheet_reader.py`, implement `read_last_run_timestamp(service, spreadsheet_id) -> Optional[datetime]`
  - Read cell G1 from Summary sheet (ISO 8601 timestamp)
  - Parse timestamp string to datetime object
  - Handle missing timestamp (return None for first run)
  - Handle invalid timestamp format (return None with warning)
  - Add comprehensive error handling
  - Log timestamp found or not found
  - **Backwards compatible** with old spreadsheets (no timestamp)
- [x] Implement helper: `_parse_iso_timestamp(timestamp_str: str) -> Optional[datetime]`
  - Parse ISO 8601 format: "2025-11-15T10:30:00Z"
  - Handle timezone conversions
  - Return None for invalid formats
- [x] Add logging for debugging

**Success Criteria**: ✅ Can read and parse timestamp from existing sheets, handles missing/invalid timestamps gracefully

#### Task 2.3: Implement Sheet Validation ✅
- [x] In `src/sheet_reader.py`, implement `validate_sheet_structure(service, spreadsheet_id) -> bool`
  - Check if "Summary" sheet exists
  - Verify expected headers in Summary sheet
  - Check for team sheets (at least one exists)
  - Return True if valid, False otherwise
  - Log validation results
- [x] Implement `get_existing_team_sheets(service, spreadsheet_id) -> List[str]`
  - Get all sheet names in spreadsheet
  - Filter out "Summary" sheet
  - Return list of team sheet names
  - Handle API errors gracefully
- [x] Add comprehensive error handling

**Success Criteria**: ✅ Can validate spreadsheet structure and extract team sheet names

#### Task 2.4: Test Sheet Reader ✅
- [x] Create test file: `tests/test_sheet_reader.py`
- [x] Test `extract_spreadsheet_id_from_url()` with various URL formats
- [x] Test `read_last_run_timestamp()` with:
  - Existing spreadsheet with timestamp
  - Existing spreadsheet without timestamp (backwards compatibility)
  - Invalid spreadsheet ID
- [x] Test `validate_sheet_structure()` with:
  - Valid spreadsheet created by this app
  - Invalid spreadsheet ID
- [x] Test `get_existing_team_sheets()` with real data (16 teams found)
- [x] Document test results
- [x] Test end-to-end backwards compatibility

**Success Criteria**: ✅ All sheet reader tests pass (6/6 tests passed)

**Phase 2 Test Results**:
- URL Parsing: 7/7 test cases passed
- Timestamp Parsing: 7/7 test cases passed
- Real Spreadsheet Reading: PASSED
- Structure Validation: PASSED
- Team Sheet Extraction: PASSED (16 teams found)
- End-to-End Backwards Compatibility: PASSED ✅
- **Backwards compatibility confirmed** with old spreadsheets

---

### Phase 3: Refactor Sheet Generator ✅ **COMPLETE**

**Goal**: Add timestamp management and extract reusable functions for updating

**Completion Date**: 2025-11-17

#### Task 3.1: Add Timestamp Helper Functions ✅
- [x] Open `src/sheet_generator.py`
- [x] Add import: `from datetime import datetime, timezone`
- [x] Implement `_get_current_timestamp() -> str`
  - Get current UTC time
  - Format as ISO 8601: "2025-11-15T10:30:00Z"
  - Return timestamp string
- [x] Implement `_format_timestamp_for_display(timestamp: str) -> str`
  - Parse ISO 8601 timestamp
  - Format as human-readable: "November 15, 2025 at 10:30 AM UTC"
  - Handle parsing errors gracefully
- [x] Add docstrings and type hints

**Success Criteria**: ✅ Can generate and format timestamps correctly

#### Task 3.2: Update Summary Sheet with Timestamp ✅
- [x] In `create_summary_sheet()` function:
  - Add cells F1:G1 with timestamp label and value
    - F1: "Last Updated (Timestamp)"
    - G1: ISO 8601 timestamp from `_get_current_timestamp()`
  - Add human-readable timestamp to summary data rows
    - Add row: ["Last Updated", formatted timestamp]
  - Update formatting requests to style timestamp cells
  - Add to batch update requests
- [x] Test with sample data
- [x] Verify timestamp appears in both locations

**Success Criteria**: ✅ Summary sheets include both machine-readable and human-readable timestamps

#### Task 3.3: Extract Team Sheet Data Creation ✅
- [x] Create helper function: `_create_team_sheet_data(team: Team) -> List[List[Any]]`
  - Extract logic from `create_team_sheet()` that builds the data array
  - Include headers: ["Player Name", "Position", "Slot", "Salary", "Source"]
  - Include player rows
  - Include summary rows (Total Salary, FAAB Remaining, Remaining Salary)
  - Return 2D list of values
  - Add docstrings
- [x] Update `create_team_sheet()` to use this helper
- [x] Test to ensure no regression in sheet creation

**Success Criteria**: ✅ Team sheet data creation is in a reusable function, existing functionality works

#### Task 3.4: Extract Team Sheet Formatting ✅
- [x] Create helper function: `_create_team_sheet_formatting(sheet_id: int, num_players: int) -> List[dict]`
  - Extract all formatting requests from `create_team_sheet()`
  - Return list of format requests for batch update
  - Parameters: sheet_id, number of players (for dynamic range)
  - Include: frozen rows, column widths, header formatting, conditional formatting
  - Add docstrings
- [x] Update `create_team_sheet()` to use this helper
- [x] Test to ensure formatting still applies correctly

**Success Criteria**: ✅ Team sheet formatting is in a reusable function, existing functionality works

#### Task 3.5: Test Refactored Sheet Generator ✅
- [x] Run existing integration tests to ensure no regression
- [x] Create new spreadsheet with refactored code
- [x] Verify timestamp appears in Summary sheet (F1:G1 and in data)
- [x] Verify all team sheets still format correctly
- [x] Compare with old spreadsheet output to ensure consistency
- [x] Document any changes or improvements

**Success Criteria**: ✅ All tests pass, timestamps added, no regression in functionality

**Phase 3 Test Results**:
- Full integration test passed: 16 teams, 261 players processed ✅
- Generated spreadsheet: https://docs.google.com/spreadsheets/d/12ys55Vhxlxnv6tNyLWt7SuWPRAfp4SV0UWTqycujjXY/edit
- Timestamp successfully stored in F1:G1 (machine-readable)
- Human-readable timestamp displayed in League Information section
- All helper functions created and tested:
  - `_get_current_timestamp()` - ISO 8601 format
  - `_format_timestamp_for_display()` - Human-readable format
  - `_create_team_sheet_data()` - Reusable data generation
  - `_create_team_sheet_formatting()` - Reusable formatting
- No regressions in existing functionality ✅
- Code is now modular and ready for Phase 4 (Sheet Updater)

---

### Phase 4: Sheet Updater

**Goal**: Implement functions to update existing sheets rather than create new ones

#### Task 4.1: Create Sheet Updater Module - Core Structure
- [ ] Create new file: `src/sheet_updater.py`
- [ ] Import required modules (google_auth, sheet_generator helpers, data_models, logger)
- [ ] Add class/module-level docstring explaining purpose
- [ ] Add comprehensive imports and type hints

**Success Criteria**: Module structure created and ready for implementation

#### Task 4.2: Implement Team Sheet Update
- [ ] Implement `update_team_sheet(service, spreadsheet_id, team: Team) -> None`
  - Find sheet ID by team name using `_find_sheet_id_by_name()`
  - If sheet doesn't exist, call `create_team_sheet()` to create it
  - Clear existing data in sheet (keep sheet, delete contents)
    - Use `values().clear()` on range `'{team.team_name}'!A1:Z1000`
  - Generate new data using `_create_team_sheet_data(team)`
  - Write new data to sheet
  - Apply formatting using `_create_team_sheet_formatting()`
  - Log update completion
  - Add comprehensive error handling
- [ ] Implement helper: `_find_sheet_id_by_name(service, spreadsheet_id, sheet_name) -> Optional[int]`
  - Get spreadsheet metadata
  - Search for sheet by name
  - Return sheet ID if found, None otherwise
  - Handle API errors
- [ ] Add docstrings and type hints

**Success Criteria**: Can update an existing team sheet with new data and formatting

#### Task 4.3: Implement Summary Sheet Update
- [ ] Implement `update_summary_sheet(service, spreadsheet_id, league: League) -> None`
  - Find Summary sheet ID
  - Clear existing data
  - Generate new summary data (reuse `create_summary_sheet()` logic)
    - Include updated timestamp (current time)
    - Include current league statistics
  - Write new data
  - Apply formatting
  - Log update completion
  - Add comprehensive error handling
- [ ] Add docstrings and type hints

**Success Criteria**: Can update Summary sheet with current league statistics and new timestamp

#### Task 4.4: Implement Timestamp Update
- [ ] Implement `update_timestamp(service, spreadsheet_id) -> None`
  - Get current timestamp from `_get_current_timestamp()`
  - Update cell G1 in Summary sheet with new timestamp
  - Update human-readable timestamp in summary data
  - Log timestamp update
  - Add error handling
- [ ] Add docstrings and type hints

**Success Criteria**: Can update just the timestamp without regenerating entire sheet

#### Task 4.5: Test Sheet Updater
- [ ] Create test file: `tests/test_sheet_updater.py`
- [ ] Test `update_team_sheet()`:
  - Update existing team sheet
  - Create new team sheet if doesn't exist
  - Verify data is correct
  - Verify formatting is applied
- [ ] Test `update_summary_sheet()`:
  - Update with new league data
  - Verify statistics are updated
  - Verify timestamp is updated
- [ ] Test `update_timestamp()`:
  - Update timestamp only
  - Verify both machine and human timestamps updated
- [ ] Test edge cases:
  - Team with name change
  - Team with 0 players
  - Invalid spreadsheet ID
- [ ] Document test results

**Success Criteria**: All sheet updater tests pass

---

### Phase 5: Main Orchestration ✅ **COMPLETE**

**Goal**: Integrate update functionality into main.py with mode detection and orchestration

**Completion Date**: 2025-11-17

#### Task 5.1: Add CLI Arguments for Update Mode ✅
- [x] Open `main.py`
- [x] Add new command-line arguments to parser:
  - `--spreadsheet-url`: URL of existing spreadsheet to update
  - `--spreadsheet-id`: ID of existing spreadsheet to update (alternative to URL)
  - `--force-full-update`: Flag to update all teams regardless of transactions
  - `--create-new`: Flag to force creation of new spreadsheet even if ID provided
- [x] Add argument validation:
  - Can't specify both --spreadsheet-url and --spreadsheet-id
  - Can't specify both --create-new and --spreadsheet-url/id
- [x] Update help text with examples
- [x] Add docstrings

**Success Criteria**: ✅ CLI accepts new arguments with proper validation

#### Task 5.2: Implement Mode Detection Logic ✅
- [x] Add function: `determine_mode(args) -> tuple[str, str]`
  - If `--create-new` flag is set, return "create"
  - If `--spreadsheet-url` or `--spreadsheet-id` is provided, return "update"
  - Otherwise, return "create" (default behavior)
  - Log mode selection
- [x] Add spreadsheet ID extraction:
  - If URL provided, extract ID using `extract_spreadsheet_id_from_url()`
  - If ID provided directly, validate format
  - Store in variable for later use
- [x] Add `format_time_ago()` helper for human-readable timestamps

**Success Criteria**: ✅ Correctly detects create vs update mode based on arguments

#### Task 5.3-5.7: Implement Complete Update Flow ✅
- [x] Add imports for all required modules
- [x] Implement complete update flow (Steps 2a-2f):
  - Step 2a: Validate spreadsheet structure with user confirmation
  - Step 2b: Read last run timestamp with time-ago display
  - Step 2c: Fetch transactions since last run
  - Step 2d: Identify affected teams intelligently
  - Step 2e: Update only affected team sheets
  - Step 2f: Update summary sheet with new statistics
- [x] Add comprehensive logging for each step
- [x] Add error handling for update failures
- [x] Add user-friendly output for all steps
- [x] Implement smart team selection logic:
  - First update (no timestamp): Update all teams
  - No transactions: Update only summary
  - Transactions found: Update only affected teams
  - Force flag: Always update all teams

**Success Criteria**: ✅ Complete update flow orchestration implemented

#### Task 5.8: Update Success Messages ✅
- [x] Differentiate success messages for create vs update modes
- [x] Show relevant statistics for each mode:
  - Create mode: teams processed, total players, salary stats
  - Update mode: teams updated, transactions processed, time since last update
- [x] Show spreadsheet URL in both modes

**Success Criteria**: ✅ Success messages clearly indicate mode and show relevant statistics

#### Task 5.9: Test Main Orchestration ✅
- [x] Test create mode - PASSED ✅
  - Created new spreadsheet successfully
  - Timestamp stored in Summary sheet
  - All 16 teams processed
- [x] Test update mode with no transactions - PASSED ✅
  - Detected last update (51 seconds ago)
  - Found 0 transactions
  - Updated 0 teams (correctly skipped all)
  - Updated summary sheet only
- [x] Test force full update - PASSED ✅
  - Skipped transaction check
  - Updated ALL 16 teams as expected
  - Completed successfully

**Success Criteria**: ✅ All modes work correctly, proper team updates, timestamps managed

**Phase 5 Test Results**:
- Create Mode: PASSED ✅ (new spreadsheet with timestamp)
- Update Mode (no transactions): PASSED ✅ (summary only updated)
- Update Mode (force-full): PASSED ✅ (all 16 teams updated)
- CLI Argument Validation: PASSED ✅
- Mode Detection: PASSED ✅
- User-Friendly Output: PASSED ✅
- Error Handling: PASSED ✅

---

### Phase 6: Testing & Edge Cases

**Goal**: Comprehensive testing and handling of edge cases

#### Task 6.1: Create Integration Test for Update Flow
- [ ] Create test file: `tests/test_incremental_update.py`
- [ ] Test complete flow:
  - Create initial spreadsheet
  - Simulate time passing
  - Run update with no transactions
  - Verify summary updated but teams skipped
  - Simulate transaction
  - Run update with transaction
  - Verify only affected team updated
  - Verify timestamp updated both times
- [ ] Test force full update:
  - Run update with `--force-full-update`
  - Verify all teams updated
- [ ] Document test results

**Success Criteria**: Integration test covers full update workflow

#### Task 6.2: Test Edge Case - Team Name Change
- [ ] Manually change a team name in Yahoo Fantasy
- [ ] Run update mode
- [ ] Expected behavior:
  - Old team sheet remains unchanged
  - New team sheet created with new name
  - User may need to manually delete old sheet
- [ ] Document behavior in code comments
- [ ] Consider adding warning in logs

**Success Criteria**: Behavior documented and tested

#### Task 6.3: Test Edge Case - New Team Added to League
- [ ] Simulate scenario where league adds a team (if possible)
- [ ] Run update mode
- [ ] Expected behavior:
  - New team sheet created
  - Summary updated with new team count
- [ ] Document behavior

**Success Criteria**: New teams handled correctly

#### Task 6.4: Test Edge Case - Team Removed from League
- [ ] Simulate scenario where team leaves league (if possible)
- [ ] Run update mode
- [ ] Expected behavior:
  - Removed team's sheet remains in spreadsheet (not deleted)
  - Summary updated with current team count
  - Consider adding warning about orphaned sheets
- [ ] Document behavior

**Success Criteria**: Removed teams don't cause errors

#### Task 6.5: Test Edge Case - No Transactions Since Last Run
- [ ] Run update mode twice in quick succession (no transactions between)
- [ ] Expected behavior:
  - "⊘ No transactions found since last run"
  - Summary sheet updated (statistics may change)
  - Timestamp updated
  - No team sheets updated (logged as skipped)
- [ ] Verify output matches expected format from plan

**Success Criteria**: Handles no-transaction scenario gracefully

#### Task 6.6: Test Edge Case - Invalid Spreadsheet ID
- [ ] Run update mode with invalid spreadsheet ID
- [ ] Expected behavior:
  - Clear error message: "Invalid spreadsheet ID"
  - Program exits gracefully
  - Suggests checking the URL/ID
- [ ] Add user-friendly error handling

**Success Criteria**: Invalid IDs handled with clear error messages

#### Task 6.7: Test Edge Case - Spreadsheet from Different League
- [ ] Create spreadsheet for a different league
- [ ] Run update mode with that spreadsheet ID
- [ ] Expected behavior:
  - Warning: "Sheet structure doesn't match expected format"
  - Option to proceed or abort
  - If team names don't match, creates new sheets
- [ ] Add validation check in sheet_reader

**Success Criteria**: Handles mismatched leagues with warning

#### Task 6.8: Error Handling Review
- [ ] Review all new modules for error handling:
  - transaction_tracker.py
  - sheet_reader.py
  - sheet_updater.py
  - main.py (update flow)
- [ ] Ensure all API calls have try/except blocks
- [ ] Ensure all error messages are user-friendly
- [ ] Ensure all errors are logged appropriately
- [ ] Add recovery strategies where possible

**Success Criteria**: Comprehensive error handling in all modules

---

### Phase 7: Documentation & Polish

**Goal**: Update documentation and add final polish

#### Task 7.1: Update CLAUDE.md
- [ ] Add section on incremental update feature
- [ ] Update command examples with new flags
- [ ] Document update workflow
- [ ] Add troubleshooting section for update mode
- [ ] Update project structure with new files

**Success Criteria**: CLAUDE.md reflects new functionality

#### Task 7.2: Update README (Create if Doesn't Exist)
- [ ] Create user-facing README.md with:
  - Project description
  - Features list (including incremental updates)
  - Installation instructions
  - Usage examples (create and update modes)
  - Authentication setup guide
  - Troubleshooting section
  - Screenshots or examples
- [ ] Make it user-friendly for non-technical users

**Success Criteria**: Professional README for users

#### Task 7.3: Create INCREMENTAL_UPDATE_CHANGELOG.md
- [ ] Document all changes made for incremental update feature:
  - New modules created
  - Modified modules
  - New CLI arguments
  - New data models
  - Test coverage
- [ ] Include migration notes for users
- [ ] Include examples of new usage patterns

**Success Criteria**: Changes documented for future reference

#### Task 7.4: Add Inline Documentation
- [ ] Review all new functions for docstrings
- [ ] Add inline comments for complex logic
- [ ] Ensure type hints are comprehensive
- [ ] Add module-level docstrings
- [ ] Verify docstring format consistency (Google style)

**Success Criteria**: All code well-documented

#### Task 7.5: Create Example Usage Scripts
- [ ] Create `examples/` directory
- [ ] Add example script: `examples/update_existing_sheet.py`
  - Shows how to use update mode programmatically
- [ ] Add example script: `examples/create_new_sheet.py`
  - Shows how to use create mode programmatically
- [ ] Add example script: `examples/schedule_weekly_update.py`
  - Shows how to schedule automatic updates (cron example)

**Success Criteria**: Users have examples to follow

#### Task 7.6: Final Testing Checklist
- [ ] Test all CLI argument combinations
- [ ] Test with different league sizes
- [ ] Test with different transaction volumes
- [ ] Test error scenarios (network failures, API limits)
- [ ] Test on fresh installation (clean .env, no tokens)
- [ ] Test authentication flows for both APIs
- [ ] Verify all log messages are clear and helpful
- [ ] Verify all error messages are actionable

**Success Criteria**: Comprehensive testing complete, all scenarios covered

---

## Future Enhancements (Post-Implementation)

**Not part of current implementation, but ideas for future:**

### Potential Future Features
- [ ] **Change Detection Details**: Show exactly what changed per team (which players added/dropped)
- [ ] **History Tracking**: Archive previous versions or snapshots of team rosters
- [ ] **Scheduled Updates**: Automatic daily/weekly updates via cron or task scheduler
- [ ] **Notification System**: Email or Slack notifications when updates occur
- [ ] **Multi-League Support**: Update multiple leagues in one run
- [ ] **Web Interface**: Flask/FastAPI frontend for easier management
- [ ] **Differential View**: Side-by-side comparison of before/after updates
- [ ] **Transaction Summary Sheet**: Dedicated sheet showing all recent transactions
- [ ] **Performance Metrics**: Track and display update performance (time, API calls)
- [ ] **Rollback Capability**: Ability to revert to previous version

---

## Success Criteria for Complete Feature

**The incremental update feature is complete when:**

1. ⏳ All 7 phases implemented and tested (Phases 1-5 complete ✅)
2. ✅ Can create new spreadsheets (existing functionality preserved)
3. ✅ Can read existing spreadsheets via URL or ID (Phase 2 complete)
4. ✅ Transactions are tracked and teams identified correctly (Phase 1 complete)
5. ✅ Only affected teams are updated (efficiency) (Phase 5 complete)
6. ✅ Force full update option works (Phase 5 complete)
7. ✅ Timestamps managed in Summary sheet (machine + human readable) (Phase 3 complete)
8. ✅ Backwards compatibility with old spreadsheets (Phase 2 complete)
9. ✅ Comprehensive error handling and user-friendly messages (Phases 1-5 complete)
10. ✅ Full test coverage for transaction tracking & sheet reading (Phases 1-5)
11. ⏳ Documentation complete and up-to-date
12. ✅ Code quality maintained (docstrings, type hints, comments)

---

## Notes

**Dependencies Between Tasks:**
- Phase 2 depends on Phase 1 (need transaction tracking for update logic)
- Phase 4 depends on Phase 3 (need refactored helpers for update functions)
- Phase 5 depends on Phases 1-4 (orchestrates all components)
- Phase 6 can run in parallel with Phase 5 (testing as you build)
- Phase 7 should be done last (documents final implementation)

**Estimated Timeline:**
- Phase 1: ✅ **COMPLETE** (foundation + transaction tracking)
- Phase 2: ✅ **COMPLETE** (sheet reading + validation)
- Phase 3: ✅ **COMPLETE** (refactoring existing code)
- Phase 4: ✅ **COMPLETE** (sheet updating logic)
- Phase 5: ✅ **COMPLETE** (main orchestration + CLI)
- Phase 6: 2-3 hours (testing + edge cases)
- Phase 7: 1-2 hours (documentation + polish)
- **Total: 14-21 hours** (approximately 2-3 full work days)
- **Progress: Phase 5 of 7 complete** (~71% done)

**Testing Strategy:**
- Write unit tests for each module as you build
- Run integration tests after each phase
- Test with real league data frequently
- Keep a test spreadsheet for experimentation
- Document all test cases and results

**Key Principles:**
- **Backward Compatibility**: Existing create functionality must continue to work
- **User Experience**: Clear messages, helpful errors, progress indicators
- **Efficiency**: Only update what changed (core goal of feature)
- **Reliability**: Robust error handling, transaction safety
- **Maintainability**: Clean code, good documentation, clear structure
