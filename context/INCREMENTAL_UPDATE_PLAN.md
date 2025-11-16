# Incremental Sheet Update Feature - Implementation Plan

## Overview

**Goal**: Add ability to update existing Google Sheets by detecting new transactions and only updating affected teams.

**Key Changes**:
1. Store "last run" timestamp in Summary sheet
2. Read existing spreadsheet and extract timestamp
3. Query Yahoo API for transactions since last run
4. Identify and update only affected teams
5. Preserve existing "create new sheet" functionality

---

## Architecture Design

### New Modules

#### 1. `src/sheet_reader.py` - Read existing spreadsheets
- Extract last run timestamp from Summary sheet
- Validate sheet structure (confirm it was created by this program)
- Parse existing team names to validate against current league

**Key Functions**:
```python
def read_last_run_timestamp(service, spreadsheet_id) -> Optional[datetime]
def validate_sheet_structure(service, spreadsheet_id) -> bool
def get_existing_team_sheets(service, spreadsheet_id) -> List[str]
def extract_spreadsheet_id_from_url(url) -> str
```

#### 2. `src/transaction_tracker.py` - Track transactions
- Get all transactions from Yahoo API
- Filter transactions since last run timestamp
- Identify which teams were affected (added/dropped players)
- Return set of team IDs that need updates

**Key Functions**:
```python
def get_transactions_since(fetcher, last_run_timestamp) -> List[Transaction]
def get_affected_team_ids(transactions) -> Set[str]
def parse_transaction_timestamp(transaction) -> int
```

#### 3. `src/sheet_updater.py` - Update existing sheets
- Update specific team sheets (by team name/ID)
- Update summary sheet with new statistics
- Update last run timestamp after successful update

**Key Functions**:
```python
def update_team_sheet(service, spreadsheet_id, team) -> None
def update_summary_sheet(service, spreadsheet_id, league) -> None
def update_timestamp(service, spreadsheet_id, timestamp) -> None
```

### Refactored Modules

#### 4. `src/sheet_generator.py` - Refactor for reusability
- Extract team sheet creation logic into reusable function
- Add timestamp management to summary sheet
- Support both "create new" and "update existing" modes

**Changes**:
- Add timestamp to Summary sheet
- Extract `_create_team_sheet_data(team)` → List[List[Any]]
- Extract `_format_team_sheet(service, spreadsheet_id, sheet_id, num_players)`
- Add `_get_current_timestamp()` → str (ISO 8601)
- Add `_format_timestamp_for_display(timestamp)` → str

#### 5. `main.py` - Enhanced CLI
- Add `--spreadsheet-url` or `--spreadsheet-id` argument
- Add `--force-full-update` flag (ignore timestamp, update all)
- Auto-detect mode: create if no spreadsheet ID, update if provided

---

## Data Model Changes

### Last Run Timestamp Storage

**Location**: Summary sheet, cells F1:G1

```
| F1                        | G1                    |
|---------------------------|-----------------------|
| Last Updated (Timestamp)  | 2025-11-15T10:30:00Z |
```

**Format**: ISO 8601 timestamp (UTC)
- Machine-readable in G1: `2025-11-15T10:30:00Z`
- Human-readable label in F1: `Last Updated (Timestamp)`
- Also add human-readable version in summary data for user visibility

### Transaction Data Structure

```python
@dataclass
class TransactionInfo:
    """Represents a transaction that affects a team."""
    transaction_id: str
    timestamp: int  # Unix timestamp
    team_id: str
    team_name: str
    transaction_type: str  # "add", "drop", "trade"
    player_name: str
    faab_bid: Optional[int] = None
```

---

## Implementation Phases

### Phase 1: Foundation & Transaction Detection

**Tasks**:
1. Create `src/transaction_tracker.py`:
   - `get_transactions_since(last_run_timestamp)` → List[Transaction]
   - `get_affected_team_ids(transactions)` → Set[str]
   - `parse_transaction_timestamp(transaction)` → int

2. Add transaction methods to `YahooDataFetcher`:
   - `get_all_transactions()` → List[Transaction]
   - Already has `league_info.transactions`, just need to expose it

3. Create data models in `src/data_models.py`:
   - Add `TransactionInfo` dataclass
   - Add helper functions to parse Yahoo transactions

**Success Criteria**: Can retrieve transactions from Yahoo API and identify affected teams

---

### Phase 2: Sheet Reading

**Tasks**:
1. Create `src/sheet_reader.py`:
   - `read_last_run_timestamp(service, spreadsheet_id)` → Optional[datetime]
   - `validate_sheet_structure(service, spreadsheet_id)` → bool
   - `get_existing_team_sheets(service, spreadsheet_id)` → List[str]
   - `extract_spreadsheet_id_from_url(url)` → str

2. Handle edge cases:
   - Sheet doesn't have timestamp → return None (treat as first run)
   - Invalid spreadsheet ID → raise clear error
   - Sheet wasn't created by this program → warning + option to proceed

**Success Criteria**: Can read existing sheets and extract timestamp

---

### Phase 3: Refactor Sheet Generator

**Tasks**:
1. Add timestamp to Summary sheet in `create_summary_sheet()`:
   - Add "Last Updated" row with current timestamp
   - Store both human-readable and ISO 8601 format

2. Extract reusable functions:
   - `_create_team_sheet_data(team)` → List[List[Any]]
   - `_format_team_sheet(service, spreadsheet_id, sheet_id, num_players)`
   - `_update_team_sheet_data(service, spreadsheet_id, sheet_name, team)` → None

3. Add helper for timestamp:
   - `_get_current_timestamp()` → str (ISO 8601)
   - `_format_timestamp_for_display(timestamp)` → str

**Success Criteria**: Sheet generator creates sheets with timestamp; existing create functionality still works

---

### Phase 4: Sheet Updater

**Tasks**:
1. Create `src/sheet_updater.py`:
   - `update_team_sheet(service, spreadsheet_id, team)` → None
     - Finds existing sheet by team name
     - Overwrites with new data
     - Applies formatting

   - `update_summary_sheet(service, spreadsheet_id, league)` → None
     - Regenerates entire summary with current stats
     - Updates timestamp

   - `update_timestamp(service, spreadsheet_id, timestamp)` → None
     - Updates just the timestamp cell

2. Handle edge cases:
   - Team sheet doesn't exist → create it (new team)
   - Team name changed → need strategy (maybe use team_id mapping)

**Success Criteria**: Can update existing sheets without creating new spreadsheet

---

### Phase 5: Main Orchestration

**Tasks**:
1. Update `main.py` CLI arguments:
   ```python
   parser.add_argument('--spreadsheet-url', help='URL of existing spreadsheet to update')
   parser.add_argument('--spreadsheet-id', help='ID of existing spreadsheet to update')
   parser.add_argument('--force-full-update', action='store_true',
                      help='Update all teams regardless of transactions')
   parser.add_argument('--create-new', action='store_true',
                      help='Force creation of new spreadsheet')
   ```

2. Add mode detection logic:
   ```python
   if args.create_new or (not args.spreadsheet_url and not args.spreadsheet_id):
       mode = "create"
   else:
       mode = "update"
   ```

3. Implement update flow:
   ```python
   if mode == "update":
       # Read existing sheet
       last_run = read_last_run_timestamp(service, spreadsheet_id)

       # Get transactions since last run
       transactions = get_transactions_since(fetcher, last_run)

       # Identify affected teams
       if args.force_full_update:
           affected_teams = all_teams
       else:
           affected_team_ids = get_affected_team_ids(transactions)
           affected_teams = [t for t in league.teams if t.team_id in affected_team_ids]

       # Update affected teams
       for team in affected_teams:
           update_team_sheet(service, spreadsheet_id, team)

       # Update summary
       update_summary_sheet(service, spreadsheet_id, league)

       # Update timestamp
       update_timestamp(service, spreadsheet_id, current_timestamp)
   ```

4. Add logging for update operations:
   - Log number of transactions found
   - Log which teams are being updated
   - Log teams with no changes (skipped)

**Success Criteria**: Complete create and update flows working from CLI

---

### Phase 6: Testing & Edge Cases

**Tasks**:
1. Test create mode (existing functionality):
   - Verify new sheets still created correctly
   - Verify timestamp is stored

2. Test update mode:
   - First run (no timestamp) → update all teams
   - Subsequent run with transactions → update only affected teams
   - No transactions since last run → update summary only
   - Force full update flag → update all teams

3. Edge cases:
   - Invalid spreadsheet ID → clear error message
   - Sheet from different league → warning + abort
   - Team added to league since last run → create new sheet
   - Team removed from league → keep old sheet or delete?
   - Concurrent modifications to sheet → handle gracefully

4. Create integration test:
   - Run create mode
   - Make fake transaction
   - Run update mode
   - Verify only affected team updated

**Success Criteria**: All modes tested and working reliably

---

## Detailed Design Decisions

### 1. Timestamp Format

```python
# Storage in Summary sheet
Cell F1: "Last Updated (Timestamp)"  # Label
Cell G1: "2025-11-15T10:30:00Z"       # ISO 8601 UTC timestamp

# Also show in human-readable format in summary data:
Row 8: ["Last Updated", "November 15, 2025 at 10:30 AM UTC"]
```

### 2. Transaction Matching Logic

```python
def get_affected_team_ids(transactions: List[Any]) -> Set[str]:
    """
    Get set of team IDs affected by transactions.

    A team is affected if:
    - They added a player (waiver, free agent, trade)
    - They dropped a player (affects salary)
    - They were involved in a trade
    """
    affected_teams = set()

    for transaction in transactions:
        if hasattr(transaction, 'players'):
            for player in transaction.players:
                trans_data = getattr(player, 'transaction_data', None)
                if trans_data:
                    # Team adding player
                    if trans_data.destination_type == 'team':
                        affected_teams.add(trans_data.destination_team_key)
                    # Team dropping player
                    if trans_data.source_type == 'team':
                        affected_teams.add(trans_data.source_team_key)

    return affected_teams
```

### 3. Sheet Update Strategy

**Overwrite approach** (simpler, recommended):
- Delete all data in team sheet
- Regenerate from current roster data
- Reapply formatting

```python
def update_team_sheet(service, spreadsheet_id, team):
    # Find sheet ID by team name
    sheet_id = find_sheet_by_name(service, spreadsheet_id, team.team_name)

    # Clear existing data (except keep sheet itself)
    clear_range = f"'{team.team_name}'!A1:Z1000"
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=clear_range
    ).execute()

    # Write new data (reuse logic from create_team_sheet)
    create_team_sheet_data(service, spreadsheet_id, sheet_id, team)
```

### 4. Team Identification

Use team_name to match sheets (since sheet names are team names):
- If team name changed in Yahoo → will create new sheet (acceptable edge case)
- User can manually delete old sheet
- Alternative: could store team_id→sheet_name mapping in Summary sheet

---

## CLI Examples

```bash
# Create new spreadsheet (existing functionality)
uv run python main.py

# Update existing spreadsheet by URL
uv run python main.py --spreadsheet-url "https://docs.google.com/spreadsheets/d/ABC123/edit"

# Update by ID
uv run python main.py --spreadsheet-id "ABC123"

# Force full update of all teams
uv run python main.py --spreadsheet-id "ABC123" --force-full-update

# Create new even if ID provided
uv run python main.py --create-new

# Verbose logging for updates
uv run python main.py --spreadsheet-id "ABC123" --verbose
```

---

## Expected Output Examples

### Update mode with transactions:
```
Loading league data...
✓ League data extracted: 16 teams, 280 players

Reading existing spreadsheet...
✓ Found timestamp: 2025-11-14T08:00:00Z (1 day ago)

Checking for transactions since last run...
✓ Found 5 transactions affecting 3 teams:
  - Team: Business Centaur (2 transactions)
  - Team: Snake Draft (2 transactions)
  - Team: The Process (1 transaction)

Updating affected teams...
  ✓ Updated: Business Centaur (17 players, $202 total)
  ✓ Updated: Snake Draft (18 players, $215 total)
  ✓ Updated: The Process (16 players, $189 total)
  ⊘ Skipped: 13 teams (no changes)

Updating summary sheet...
✓ Summary updated

Spreadsheet updated successfully!
URL: https://docs.google.com/spreadsheets/d/ABC123/edit
Teams updated: 3 of 16
Last updated: November 15, 2025 at 10:30 AM UTC
```

### Update mode with no transactions:
```
Loading league data...
✓ League data extracted: 16 teams, 280 players

Reading existing spreadsheet...
✓ Found timestamp: 2025-11-15T09:00:00Z (30 minutes ago)

Checking for transactions since last run...
⊘ No transactions found since last run

Updating summary sheet...
✓ Summary updated (timestamp refreshed)

Spreadsheet updated successfully!
URL: https://docs.google.com/spreadsheets/d/ABC123/edit
Teams updated: 0 of 16
Last updated: November 15, 2025 at 10:30 AM UTC
```

---

## File Structure After Implementation

```
src/
├── yahoo_data_fetcher.py      # Existing - minor additions for transaction access
├── data_processor.py          # Existing - no changes needed
├── data_models.py             # Existing - add TransactionInfo dataclass
├── sheet_generator.py         # Refactored - extract reusable functions, add timestamp
├── sheet_reader.py            # NEW - read existing sheets
├── sheet_updater.py           # NEW - update existing sheets
├── transaction_tracker.py     # NEW - track and analyze transactions
├── google_auth.py             # Existing - no changes
├── logger.py                  # Existing - no changes
└── __init__.py                # Existing - no changes

main.py                        # Enhanced - add update mode orchestration
```

---

## Benefits of This Design

1. **Efficiency**: Only updates teams with actual changes
2. **Backward Compatible**: Existing create mode unchanged
3. **Simple**: Overwrite strategy avoids complex inline updates
4. **Robust**: Timestamp in sheet ensures sync even if script run on different machines
5. **Flexible**: Force-full-update flag for when needed
6. **User-Friendly**: Clear logging shows what's being updated and why

---

## Potential Future Enhancements

1. **Change Detection**: Show what changed per team (added/dropped players)
2. **History Tracking**: Keep archive of previous versions
3. **Scheduled Updates**: Run automatically via cron/scheduled task
4. **Notification**: Email/Slack notification when updates occur
5. **Multi-League**: Update multiple leagues in one run

---

## Implementation Sequence

The phases should be implemented in order:
1. Phase 1: Foundation & Transaction Detection
2. Phase 2: Sheet Reading
3. Phase 3: Refactor Sheet Generator
4. Phase 4: Sheet Updater
5. Phase 5: Main Orchestration
6. Phase 6: Testing & Edge Cases

Each phase should be completed and tested before moving to the next phase.
