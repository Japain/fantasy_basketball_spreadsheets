# Changelog

All notable changes to the Fantasy Basketball application will be documented in this file.

## [Unreleased]

### Added - 2025-11-15

#### Remaining Salary Column and Conditional Formatting

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
