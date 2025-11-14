# Investigation Scripts

This directory contains investigation and exploration scripts used during the development process to understand the Yahoo Fantasy API data structures and confirm salary data availability.

## Scripts

### 1. `investigate_salary_data.py`
**Purpose**: Systematic exploration of Yahoo Fantasy API endpoints to discover salary-related data.

**What it does**:
- Explores league info, metadata, teams, rosters, and draft results
- Searches for salary-related keywords across all data structures
- Identifies all potential sources of salary/cost information
- Documents findings for each API endpoint

**Usage**:
```bash
uv run python src/investigation/investigate_salary_data.py
```

**Key Findings**:
- Discovered `player.is_keeper` contains keeper costs
- Confirmed draft results contain auction prices
- Identified team FAAB balance field

---

### 2. `investigate_roster.py`
**Purpose**: Detailed analysis of team rosters and player salary data.

**What it does**:
- Examines roster structure and player objects
- Maps draft results to player costs
- Tests salary retrieval from keeper and draft data
- Calculates total team salary and validates against budget
- Demonstrates salary coverage (before FAAB integration: 82%)

**Usage**:
```bash
uv run python src/investigation/investigate_roster.py
```

**Key Findings**:
- Player objects contain detailed keeper information
- Keeper costs can be retrieved from `is_keeper` field
- Draft costs can be mapped via `player_key`
- Identified 3 players with missing salary data (later found via FAAB)

---

### 3. `investigate_transactions.py`
**Purpose**: Investigation of transaction history to find FAAB bid amounts for waiver acquisitions.

**What it does**:
- Analyzes all league transactions (192 total)
- Identifies transactions with FAAB bids
- Creates player-to-FAAB-cost mapping
- Tests complete 3-priority salary retrieval strategy
- Validates 100% salary coverage

**Usage**:
```bash
uv run python src/investigation/investigate_transactions.py
```

**Key Findings**:
- 88 transactions contain FAAB bids (46% of all transactions)
- 73 unique players acquired via FAAB
- FAAB bids range from $1 to $10+
- **Achieved 100% salary coverage** by integrating FAAB data
- Found the 3 previously missing players via transaction history

---

## Investigation Results Summary

### Data Sources Confirmed:

1. **Keeper Costs** (`player.is_keeper['cost']`)
   - 9 players on test team
   - Example: Shai Gilgeous-Alexander ($33)

2. **Draft Auction Prices** (`draft_results[].cost`)
   - 5 players on test team
   - 224 total draft picks across league
   - Example: Dylan Harper ($5)

3. **FAAB Bids** (`transactions[].faab_bid`)
   - 3 players on test team
   - 73 players league-wide
   - Example: Derrick Jones Jr. ($3)

### Coverage Achievement:
- **Before FAAB**: 14/17 players (82%)
- **After FAAB**: 17/17 players (100%) ✅

### Test Team Results:
- **Team**: "Historically Juiced"
- **Total Salary**: $199
- **FAAB Remaining**: $184
- **Coverage**: 100%

---

## Related Documentation

- **SALARY_DATA_FINDINGS.md** - Comprehensive documentation of all findings
- **FAAB_INVESTIGATION_SUMMARY.md** - Detailed FAAB investigation results
- **SESSION_NOTES.md** - Session progress and key discoveries

---

## Notes

These scripts were created during **Phase 1: Foundation & Discovery** to:
1. Confirm salary data availability through Yahoo Fantasy API
2. Understand data structures and field names
3. Test salary retrieval strategies
4. Validate 100% coverage is achievable

The scripts are kept for:
- **Reference** during implementation
- **Testing** if API structure changes
- **Documentation** of the investigation process
- **Debugging** if issues arise with production code

They should **not** be used in production but serve as valuable development resources and proof-of-concept code.

---

## Running All Investigations

To run all three investigations in sequence:

```bash
# Full investigation suite
uv run python src/investigation/investigate_salary_data.py
uv run python src/investigation/investigate_roster.py
uv run python src/investigation/investigate_transactions.py
```

Each script is independent and can be run separately. They all use the same Yahoo API authentication from the project's `.env` file.
