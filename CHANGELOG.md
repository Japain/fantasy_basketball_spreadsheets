# Changelog

All notable changes to the Fantasy Basketball application will be documented in this file.

## [Unreleased]

### Added - 2025-11-15

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
