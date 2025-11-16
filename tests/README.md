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

## Test Organization

- **Integration Tests**: Test multiple components working together (Yahoo API, Google Sheets, data processing)
- **Unit Tests**: Test specific functionality in isolation (IL/IL+ exclusion, output formatting)

## Requirements

All tests require:
- Valid Yahoo API credentials in `.env`
- Authenticated Yahoo OAuth tokens
- For full integration test: Google API credentials and authenticated tokens

See main [README.md](../README.md) for setup instructions.
