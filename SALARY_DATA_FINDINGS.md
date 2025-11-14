# Yahoo Fantasy Basketball - Salary Data Investigation Findings

**Date**: 2025-11-14
**League**: Squad Goals (ID: 68958)
**League Type**: Keeper League with Auction Draft

---

## Executive Summary

✅ **Salary data IS available** through the Yahoo Fantasy API via multiple sources.

This is a **keeper league** where player salaries are tracked through:
1. **Keeper costs** (players retained from previous seasons)
2. **Draft auction prices** (players drafted in current season)
3. **FAAB bids** (players acquired via waivers/free agency)

---

## Data Sources

### 1. Player Keeper Status (`player.is_keeper`)

Each player object in a roster has an `is_keeper` field with the following structure:

```python
is_keeper = {
    'status': True,      # Boolean - whether player is a keeper
    'cost': 33,          # Integer - keeper cost (salary)
    'kept': True         # Boolean - whether player was actually kept
}
```

**Examples:**
- Shai Gilgeous-Alexander: `{'status': True, 'cost': 33, 'kept': True}` → $33 salary
- Cam Thomas: `{'status': True, 'cost': 7, 'kept': True}` → $7 salary
- Derrick Jones Jr.: `{'status': False, 'cost': None, 'kept': False}` → Not a keeper

**Special Cases:**
- Dylan Harper: `{'status': True, 'cost': None, 'kept': True}` → Keeper with no cost (possibly rookie keeper or special league rule)

### 2. Draft Results (`get_league_draft_results()`)

Returns a list of `DraftResult` objects, each containing:

```python
DraftResult {
    'cost': 35,                          # Auction price paid
    'pick': 1,                           # Overall pick number
    'player_key': '466.p.4912',         # Player identifier
    'round': 1,                          # Draft round
    'team_key': '466.l.68958.t.11'      # Team that drafted player
}
```

**Sample Data (first 10 picks):**
1. `466.p.4912`: $35 (Pick 1, Round 1)
2. `466.p.5464`: $43 (Pick 2, Round 1)
3. `466.p.3704`: $39 (Pick 3, Round 1)
4. `466.p.5471`: $51 (Pick 4, Round 1)
5. `466.p.6218`: $29 (Pick 5, Round 1)

**Total Draft Picks**: 224 (14 rounds × 16 teams)

### 3. Team Budget Information

Each team object contains:

```python
team.faab_balance = 184  # Remaining FAAB budget for waiver acquisitions
```

This shows remaining budget but doesn't directly show how much was spent on specific waiver pickups.

### 4. Transaction History

Accessible via `league_info.transactions`, contains:

```python
transaction.faab_bid = 1  # FAAB amount bid for waiver claim
```

Can be used to track acquisition costs for players obtained via waivers/free agency.

---

## Salary Retrieval Strategy

For each player on a team's roster, determine salary using this **priority order**:

### Priority 1: Keeper Cost
```python
if player.is_keeper['status'] and player.is_keeper['cost'] is not None:
    salary = player.is_keeper['cost']
```

### Priority 2: Draft Auction Cost
```python
elif player.player_key in draft_results_map:
    salary = draft_results_map[player.player_key]['cost']
```

### Priority 3: Waiver/Free Agent Acquisition
```python
# Check transaction history for FAAB bid
# If found in transactions with faab_bid > 0:
    salary = faab_bid_amount
# else:
    salary = 0  # Free agent pickup (no cost)
```

### Priority 4: Unknown
```python
salary = None  # or 0, or mark as "N/A"
```

---

## Example Roster with Salaries

**Team**: Historically Juiced (Team ID: 1)
**FAAB Remaining**: $184

| Player Name                | Position | Salary | Source       |
|---------------------------|----------|--------|--------------|
| Shai Gilgeous-Alexander   | PG       | $33    | Keeper       |
| Dylan Harper              | PG,SG    | $5     | Draft        |
| Cam Thomas                | SG,SF    | $7     | Keeper       |
| Derrick Jones Jr.         | SF,PF    | N/A    | Waiver/FA    |
| Keldon Johnson            | SF,PF    | $21    | Keeper       |
| Shaedon Sharpe            | SG,SF    | $12    | Keeper       |
| Nic Claxton               | C        | $21    | Keeper       |
| Deandre Ayton             | C        | $21    | Keeper       |
| Isaiah Stewart            | PF,C     | N/A    | Waiver/FA    |
| Ajay Mitchell             | PG,SG    | N/A    | Waiver/FA    |
| Christian Braun           | SG,SF    | $4     | Draft        |
| Jase Richardson           | SG       | $2     | Draft        |
| Kelly Oubre Jr.           | SF,PF    | $1     | Draft        |
| Jaren Jackson Jr.         | PF,C     | $27    | Keeper       |
| De'Aaron Fox               | PG,SG    | $33    | Keeper       |
| Luguentz Dort             | SG,SF    | $1     | Draft        |
| Khris Middleton           | SF,PF    | $1     | Draft        |

**Total Salary**: $189 (excluding N/A players)

---

## Data Access Methods

### Get League Info with Embedded Data
```python
from src.yahoo_data_fetcher import YahooDataFetcher

fetcher = YahooDataFetcher()

# Get league info (includes draft_results, teams, transactions)
league_info = fetcher.get_league_info()

# Access draft results
draft_results = league_info.draft_results  # List[DraftResult]

# Access teams
teams = league_info.teams  # List[Team]
```

### Get Team Roster
```python
# Get specific team's roster
roster = fetcher.get_team_roster(team_id="1")

# Access players
players = roster.players  # List[Player]

# Access player details
for player in players:
    name = player.name.full  # or player.name.ascii_full
    player_key = player.player_key
    position = player.display_position
    is_keeper = player.is_keeper  # Dict with status, cost, kept
```

### Get Draft Results Directly
```python
# Get all draft results
draft_results = fetcher.get_league_draft_results()  # List[DraftResult]

# Create player_key -> cost mapping
draft_cost_map = {
    result.player_key: result.cost
    for result in draft_results
}
```

---

## Player Object Structure

Key attributes of a `Player` object:

```python
Player {
    'player_key': '466.p.6022',                    # Unique identifier
    'name': Name object {                          # Player name
        'full': 'Shai Gilgeous-Alexander',
        'ascii_full': 'Shai Gilgeous-Alexander',
        'first': 'Shai',
        'last': 'Gilgeous-Alexander'
    },
    'display_position': 'PG',                      # Current display position
    'eligible_positions': ['PG'],                   # Eligible positions
    'primary_position': 'PG',                      # Primary position
    'selected_position': SelectedPosition {        # Current roster slot
        'position': 'PG',
        'date': '2025-10-26',
        'coverage_type': 'date',
        'is_flex': 0
    },
    'is_keeper': {                                 # Keeper status & cost
        'status': True,
        'cost': 33,
        'kept': True
    },
    'editorial_team_abbr': 'OKC',                  # NBA team abbreviation
    'editorial_team_full_name': 'Oklahoma City Thunder',
    'uniform_number': '2',
    'headshot': HeadShot object,                   # Player photo
    # ... many other attributes
}
```

---

## Implementation Recommendations

### 1. Create Player-Salary Mapping Function

```python
def get_player_salary(player, draft_cost_map):
    """
    Get salary for a player.

    Args:
        player: Player object from roster
        draft_cost_map: Dict mapping player_key to draft cost

    Returns:
        int: Player salary, or None if not found
    """
    # Check keeper cost first
    if player.is_keeper.get('status') and player.is_keeper.get('cost') is not None:
        return player.is_keeper['cost']

    # Check draft cost
    if player.player_key in draft_cost_map:
        return draft_cost_map[player.player_key]

    # TODO: Check transaction history for FAAB bids

    # Unknown/Free agent
    return None
```

### 2. Build Complete League Data Structure

```python
def extract_league_data():
    """Extract complete league data with salaries."""
    fetcher = YahooDataFetcher()

    # Get league info
    league_info = fetcher.get_league_info()

    # Create draft cost mapping
    draft_cost_map = {
        result.player_key: result.cost
        for result in league_info.draft_results
    }

    # Process each team
    teams_data = []
    for team in league_info.teams:
        roster = fetcher.get_team_roster(team.team_id)

        players_data = []
        total_salary = 0

        for player in roster.players:
            salary = get_player_salary(player, draft_cost_map)

            players_data.append({
                'name': player.name.full,
                'position': player.display_position,
                'salary': salary,
                'player_key': player.player_key
            })

            if salary is not None:
                total_salary += salary

        teams_data.append({
            'team_id': team.team_id,
            'team_name': team.name,
            'manager_name': team.managers[0].nickname if team.managers else None,
            'roster': players_data,
            'total_salary': total_salary,
            'faab_remaining': team.faab_balance
        })

    return {
        'league_name': league_info.name,
        'league_id': league_info.league_id,
        'season': league_info.season,
        'teams': teams_data
    }
```

---

## Edge Cases & Considerations

### 1. Keeper with None Cost
- Example: Dylan Harper has `{'status': True, 'cost': None, 'kept': True}`
- Might be rookie keeper or special league rule
- Fallback: Check draft results or assign minimum ($1)

### 2. Waiver Wire Pickups
- Players not in draft results or keepers
- Check `league_info.transactions` for FAAB bids
- If no FAAB bid found, likely free agent ($0)

### 3. Dropped/Added Players
- Transaction history shows player movements
- A player might have been drafted by one team but currently on another
- Use current roster as source of truth, but get cost from original draft/keeper status

### 4. Mid-Season Trades
- Traded players might show different team in draft results vs. current roster
- Salary should remain the same (original draft/keeper cost)

### 5. Team Name Encoding
- Team names appear as bytes (e.g., `b'Historically Juiced'`)
- Decode as needed: `team.name.decode('utf-8')` or handle bytes in display

---

## Validation Checks

When implementing, verify:

1. ✅ All teams retrieved (should be 16 for this league)
2. ✅ All rosters have players (typically 13-17 per team)
3. ✅ Each player has required fields: name, position, player_key
4. ✅ Salary values are valid integers or None
5. ✅ Total salary per team is reasonable (should be ~$200 for auction draft with $200 budget)
6. ✅ FAAB balance + total salary is close to original budget

---

## Next Steps

1. ✅ **Investigation Complete** - Salary data availability confirmed
2. ⏭️ **Update Data Models** - Define data structures in `src/data_models.py`
3. ⏭️ **Implement Data Fetcher** - Complete `src/yahoo_data_fetcher.py` with salary logic
4. ⏭️ **Implement Data Processor** - Build `src/data_processor.py` for data transformation
5. ⏭️ **Testing** - Validate with real league data
6. ⏭️ **Google Docs Integration** - Begin Phase 3 implementation

---

## Success Criteria Met ✅

- ✅ Yahoo API authenticated
- ✅ Salary data availability confirmed
- ✅ Data structure documented
- ✅ Retrieval strategy defined
- ✅ Edge cases identified
- ✅ Implementation path clear

**Conclusion**: The project can proceed to Phase 2 (Yahoo Data Retrieval Implementation) with confidence that all required salary data is accessible through the Yahoo Fantasy API.
