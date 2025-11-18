# Tests

This directory contains all test scripts for the Fantasy Basketball application.

## Running Tests

All tests should be run as Python modules from the project root directory using `uv run python -m tests.<test_name>`.

### Available Tests

#### Integration Tests

**test_league_extraction.py** - Yahoo Data Extraction Test
```bash
uv run python -m tests.test_league_extraction
```
Tests complete league data extraction from Yahoo Fantasy API. Outputs detailed results to `league_extraction_results.txt` including:
- League validation
- Team rosters with salaries
- Top 20 highest salaries
- Complete statistics

**test_full_integration.py** - Full Integration Test
```bash
uv run python -m tests.test_full_integration
```
Tests end-to-end integration including Yahoo data extraction and Google Sheets generation.

#### Unit Tests

**test_il_exclusion.py** - IL/IL+ Exclusion Logic Test
```bash
uv run python -m tests.test_il_exclusion
```
Verifies that players in IL (Injured List) or IL+ positions are correctly excluded from total salary calculations.

**test_roster_position_output.py** - Roster Position Output Format Test
```bash
uv run python -m tests.test_roster_position_output
```
Demonstrates and validates the roster output format including the new "Slot" column showing each player's current roster position.

**test_remaining_salary.py** - Remaining Salary Calculation Test
```bash
uv run python tests/test_remaining_salary.py
```
Tests the remaining salary calculation feature (INITIAL_AUCTION_BUDGET - TOTAL_SALARY). Validates budget loading from config and accurate calculations with IL player exclusions.

**test_conditional_formatting.py** - Conditional Formatting Test
```bash
uv run python tests/test_conditional_formatting.py
```
Tests conditional formatting for Remaining Salary in Google Sheets. Creates a test spreadsheet with teams having positive, zero, and negative remaining salaries to verify green/red color highlighting.

#### Incremental Update Tests

**test_transaction_tracker.py** - Transaction Tracking Test
```bash
uv run python -m tests.test_transaction_tracker
```
Tests the transaction tracking functionality for incremental updates. Validates transaction retrieval, filtering by timestamp, and affected team identification. Runs 5 comprehensive test cases including edge cases.

**test_sheet_reader.py** - Sheet Reading Test
```bash
uv run python -m tests.test_sheet_reader
```
Tests reading existing Google Sheets for incremental updates. Validates timestamp extraction, URL parsing, and sheet structure validation. Tests backwards compatibility with old spreadsheets.

**test_sheet_updater.py** - Sheet Update Test
```bash
uv run python -m tests.test_sheet_updater
```
Tests updating existing Google Sheets. Creates a test spreadsheet and validates team sheet updates, summary updates, and timestamp-only updates.

**test_incremental_update.py** - Incremental Update Integration Test
```bash
uv run python -m tests.test_incremental_update
```
Comprehensive integration test for the complete incremental update workflow. Tests:
- Creating initial spreadsheet with timestamp
- Updating with no new transactions (summary only)
- Updating with transactions (only affected teams)
- Force full update mode
- Timestamp persistence

Note: May encounter Google Sheets API rate limits (60 write requests/minute) when updating many teams.

**test_edge_cases.py** - Edge Case Tests
```bash
uv run python -m tests.test_edge_cases
```
Tests edge cases and error handling for incremental updates:
- Invalid spreadsheet IDs
- No transactions scenarios
- URL extraction variations
- Empty transaction lists
- Future/past timestamps

## Test Organization

- **Integration Tests**: Test multiple components working together (Yahoo API, Google Sheets, data processing)
- **Unit Tests**: Test specific functionality in isolation (IL/IL+ exclusion, output formatting)
- **Incremental Update Tests**: Test the incremental update feature (transaction tracking, sheet reading, updating)

## Requirements

All tests require:
- Valid Yahoo API credentials in `.env`
- Authenticated Yahoo OAuth tokens
- For full integration test: Google API credentials and authenticated tokens

See main [README.md](../README.md) for setup instructions.
