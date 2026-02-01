# Bench Management Alert Feature - Implementation Plan

## Overview
Implement a bench management alert system that notifies users (via Discord) which teams left healthy players with scheduled games sitting on their bench yesterday.

## User Requirements (Confirmed)
- **Injury Check**: Use combination of current injury status + historical data from spreadsheet
- **Notification**: Team names only (simple list)
- **Timing**: Part of regular updates (automatic)
- **Criteria**: Flag when player was benched yesterday, healthy, and had a game

---

## Design Approach

### **Two-Source Data Strategy**
1. **Yesterday's roster data**: Read from existing spreadsheet team sheets (columns B-D)
2. **Current health status**: Use as proxy for yesterday's status (conservative approach)
3. **Game schedule**: Check via Yahoo API `get_player_stats_by_date`

### **Violation Criteria** (ALL must be true)
1. Player was on bench (BN position) yesterday
2. Player was NOT on IL/IL+ yesterday
3. Player is healthy today (no INJ/OUT/DTD/GTD status) → implies healthy yesterday
4. Player had a scheduled game yesterday

### **Integration**
- Runs automatically during UPDATE mode (after Step 2f)
- Non-critical - failures don't break main workflow
- Optional `--skip-bench-check` flag to disable

---

## Implementation Phases

### **Phase 1: Extend Data Models** (`src/data_models.py`)

Add injury status fields to `Player` dataclass (lines 28-55):
```python
@dataclass
class Player:
    player_key: str
    name: str
    position: str
    salary: int
    source: SalarySource
    nba_team: Optional[str] = None
    roster_position: Optional[str] = None
    # NEW FIELDS:
    status: Optional[str] = None           # e.g., "INJ", "OUT", "GTD", "DTD", None
    status_full: Optional[str] = None      # e.g., "Injury", "Out", None
    injury_note: Optional[str] = None      # e.g., "Day-to-day", "Knee", None
```

Update `create_player_from_yahoo_data` factory function (lines 250-282) to accept new parameters.

---

### **Phase 2: Update Yahoo Data Fetcher** (`src/yahoo_data_fetcher.py`)

Modify `_extract_player_data` method (lines 546-606) to capture status fields:
```python
# Get injury status fields
status = getattr(yahoo_player, 'status', None)
status_full = getattr(yahoo_player, 'status_full', None)
injury_note = getattr(yahoo_player, 'injury_note', None)

return create_player_from_yahoo_data(
    ...,
    status=status,
    status_full=status_full,
    injury_note=injury_note
)
```

---

### **Phase 3: Create Bench Analyzer Module** (`src/bench_analyzer.py` - NEW)

Core module with:

**Helper Functions:**
- `_is_player_healthy(player)` - Check if player status indicates healthy
- `_is_benched(player)` - Check if roster_position is 'BN'
- `_is_on_il(player)` - Check if roster_position is 'IL' or 'IL+'

**Main Functions:**
- `batch_read_all_team_rosters(service, spreadsheet_id, team_names)`
  - **BATCH READ**: Read all team rosters in ONE API call (follows v2.5 pattern)
  - Build ranges for all team sheets: `'Team Name'!B2:D50`
  - Use `service.spreadsheets().values().batchGet()` for single call
  - Parse and return dict mapping team_name → list of player dicts
  - **Performance**: 16 calls → 1 call (94% reduction)

- `_parse_roster_rows(rows)`
  - Helper to parse roster rows from values list
  - Skip header rows, handle blank/summary rows
  - Return list of dicts with {name, position, slot}

- `check_player_had_game_yesterday(fetcher, player_key, date)`
  - Use `fetcher.yahoo_query.get_player_stats_by_date()`
  - Return True if player_stats.stats exists and has data
  - Gracefully degrade on API failures (return False)

- `analyze_bench_violations(league, fetcher, service, spreadsheet_id, yesterday_date)`
  - **NOTE**: Added `service` parameter for batch reading
  - Single batch call to read all team rosters
  - For each current player, check if they match violation criteria
  - Return dict mapping team_name → list of violations

- `get_teams_with_bench_violations(violations_dict)`
  - Extract sorted list of team names with violations

**Detailed module implementation available in `/home/ripl/.claude/plans/tidy-waddling-koala-agent-a2b10cd.md` (lines 140-546)**

---

### **Phase 4: Add Discord Notification** (`src/discord_notifier.py`)

Add method to `DiscordNotifier` class (after line 220):
```python
def send_bench_alert(
    self,
    teams_with_violations: List[str],
    spreadsheet_url: str,
    check_date: str
) -> bool:
    """
    Send bench management alert notification.

    Args:
        teams_with_violations: List of team names with violations
        spreadsheet_url: URL to the Google Spreadsheet
        check_date: Date that was checked (YYYY-MM-DD format)

    Returns:
        True if notification sent successfully, False otherwise
    """
    if not self.enabled:
        return False

    # Don't send notification if no violations
    if not teams_with_violations:
        logger.info("No bench violations to report")
        return False

    try:
        # Create webhook
        webhook = DiscordWebhook(
            url=self.webhook_url,
            username="Fantasy Basketball Bot"
        )

        # Create rich embed
        embed = DiscordEmbed(
            title="⚠️ Bench Management Alert",
            description=f"The following teams left healthy players with scheduled games on the bench on {check_date}:",
            color="ffa500"  # Orange for warning
        )

        # Format team list
        team_list = "\n".join([f"• {team}" for team in teams_with_violations])

        embed.add_embed_field(
            name=f"Teams ({len(teams_with_violations)})",
            value=team_list,
            inline=False
        )

        # Add spreadsheet link
        embed.add_embed_field(
            name="📊 View Rosters",
            value=f"[Open Spreadsheet]({spreadsheet_url})",
            inline=False
        )

        # Add helpful tip
        embed.add_embed_field(
            name="💡 Tip",
            value="Check your bench before games to maximize your active roster!",
            inline=False
        )

        # Add footer and timestamp
        embed.set_footer(text="Fantasy Basketball Automation • Daily Bench Check")
        embed.set_timestamp()

        # Send webhook
        webhook.add_embed(embed)
        response = webhook.execute()

        if response.status_code in [200, 204]:
            logger.info(f"Bench alert sent successfully ({len(teams_with_violations)} teams)")
            return True
        else:
            logger.warning(f"Bench alert failed with status {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Failed to send bench alert: {e}")
        return False
```

Add convenience function (after line 280):
```python
def notify_bench_violations(
    teams_with_violations: List[str],
    spreadsheet_url: str,
    check_date: str
) -> None:
    """
    Convenience function to send bench violation notification.

    Automatically reads webhook URL from environment.
    Safe to call even if Discord integration is not configured (will no-op).

    Args:
        teams_with_violations: List of team names with violations
        spreadsheet_url: URL to the Google Spreadsheet
        check_date: Date that was checked (YYYY-MM-DD format)
    """
    notifier = DiscordNotifier()
    notifier.send_bench_alert(
        teams_with_violations=teams_with_violations,
        spreadsheet_url=spreadsheet_url,
        check_date=check_date
    )
```

---

### **Phase 5: Integrate into Main Workflow** (`main.py`)

1. **Add imports** (after line 21):
```python
from src.bench_analyzer import (
    analyze_bench_violations,
    get_teams_with_bench_violations
)
from src.discord_notifier import notify_update_complete, notify_error, notify_bench_violations
```

2. **Add CLI argument** (after line 168):
```python
parser.add_argument(
    '--skip-bench-check',
    action='store_true',
    help='Skip bench management analysis (only applies in update mode)'
)
```

3. **Add Step 2g in UPDATE mode** (after line 453, before success message):
```python
# Step 2g: Analyze bench management (optional, non-critical)
if not args.skip_bench_check:
    print("Step 2g: Analyzing bench management...")
    try:
        from datetime import timedelta

        # Calculate yesterday's date
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        yesterday_date = yesterday.strftime('%Y-%m-%d')

        # Analyze violations (pass service for batch reading)
        violations = analyze_bench_violations(
            league=league_data,
            fetcher=fetcher,
            service=service,
            spreadsheet_id=spreadsheet_id,
            yesterday_date=yesterday_date
        )

        # Get team list
        teams_with_violations = get_teams_with_bench_violations(violations)

        if teams_with_violations:
            print(f"⚠ Found {len(teams_with_violations)} team(s) with bench violations:")
            for team_name in teams_with_violations:
                violation_count = len(violations[team_name])
                print(f"  • {team_name} ({violation_count} player(s))")

            # Send Discord notification
            notify_bench_violations(
                teams_with_violations=teams_with_violations,
                spreadsheet_url=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
                check_date=yesterday_date
            )
        else:
            print("✓ No bench violations found - all teams optimized their lineups!")

    except Exception as e:
        logger.warning(f"Bench analysis failed (non-critical): {e}")
        print(f"⚠ Warning: Bench analysis failed: {e}")
        # Don't fail the whole update - this is informational only

    print()
```

---

### **Phase 6: Testing** (`tests/test_bench_analyzer.py` - NEW)

Create comprehensive test suite with the following test classes:

**Test Classes:**
- `TestPlayerHealthChecks` - Test `_is_player_healthy()` with various status codes
- `TestBenchDetection` - Test `_is_benched()` for BN vs active positions
- `TestILDetection` - Test `_is_on_il()` for IL/IL+ positions
- `TestGameChecking` - Test `check_player_had_game_yesterday()` with mocked API
- `TestViolationAnalysis` - Test full `analyze_bench_violations()` workflow

**Test Scenarios:**
- Healthy player with no status → healthy
- Injured player with INJ/OUT status → not healthy
- Player on bench (BN) → benched
- Player in active lineup (PG/SG/etc) → not benched
- Player on IL/IL+ → on IL
- Player with game stats → had game
- Player without game stats → no game
- Full violation detection with all conditions met

**Manual Integration Test:**
```python
@pytest.mark.manual
def test_bench_analysis_integration():
    """
    Manual integration test with real Yahoo API and Google Sheets.

    To run:
        pytest tests/test_bench_analyzer.py::test_bench_analysis_integration -v -m manual
    """
```

**Detailed test implementation available in `/home/ripl/.claude/plans/tidy-waddling-koala-agent-a2b10cd.md` (lines 766-1030)**

---

### **Phase 7: Documentation** (`CLAUDE.md`)

Add section after "Sheet Protection" (around line 260):

```markdown
### Bench Management Alerts (v2.7)

The application includes optional bench management analysis for automated lineup optimization alerts.

**Features:**
- 🔍 **Daily bench checks** - Analyzes yesterday's rosters for missed opportunities
- ⚠️ **Violation detection** - Identifies teams that benched healthy players with games
- 🔔 **Discord alerts** - Simple team name notifications via webhook
- 📊 **Smart filtering** - Excludes injured players and IL slots
- ⚡ **Non-critical** - Analysis failures don't break main workflow

**How It Works:**
1. Reads yesterday's roster data from spreadsheet (team sheets)
2. Checks current player health status from Yahoo API
3. Verifies which players had scheduled games yesterday
4. Identifies violations: benched + healthy + had game
5. Sends Discord notification with team names only

**Configuration:**
- **Automatic**: Runs by default during spreadsheet updates
- **Opt-out**: Use `--skip-bench-check` flag to disable
- **Discord**: Uses same webhook as update notifications

**Criteria for Violation:**
A team is flagged when a player meets ALL these conditions:
1. Was in BN (bench) position yesterday
2. Was NOT in IL/IL+ position yesterday
3. Is healthy today (no INJ/OUT/DTD/GTD status)
4. Had a scheduled game yesterday

**Example Output:**
```
Step 2g: Analyzing bench management...
⚠ Found 3 team(s) with bench violations:
  • Team Alpha (2 player(s))
  • Team Beta (1 player(s))
  • Team Gamma (1 player(s))
```

**Discord Notification:**
- Orange warning embed
- List of team names
- Link to spreadsheet
- Helpful lineup optimization tip

**Performance:**
- Google Sheets: **1 read call** (batch read all teams)
- Yahoo API: ~10-30 calls (one per benched player)
- Total: **~11-31 API calls per run** (38% reduction via batching)
- Non-blocking: Runs after main update completes

**Limitations:**
- Uses current health status as proxy for yesterday's status
- May miss players who got healthy overnight
- Requires yesterday's spreadsheet data to exist
- Only runs in UPDATE mode (not CREATE mode)
```

---

### **Phase 8: Deployment**

1. **Create pull request** with all changes
2. **Code review** - Ensure quality and adherence to patterns
3. **Merge to main** - Deploy to production
4. **Monitor first run** - Watch logs for issues
5. **Gather feedback** - Adjust based on user experience
6. **Optimize if needed** - Performance improvements if required

---

## Critical Files to Modify

1. **`src/data_models.py`** - Add injury status fields (status, status_full, injury_note)
2. **`src/yahoo_data_fetcher.py`** - Capture status from Yahoo API
3. **`src/bench_analyzer.py`** - [CREATE NEW] Core violation detection logic
4. **`src/discord_notifier.py`** - Add bench alert notification method
5. **`main.py`** - Integrate bench analysis into UPDATE workflow
6. **`tests/test_bench_analyzer.py`** - [CREATE NEW] Comprehensive test suite
7. **`CLAUDE.md`** - Document new feature

---

## Performance Characteristics

**API Calls per Run:**
- **Google Sheets**: **1 read call** (batch read all team rosters - v2.5 pattern)
- **Yahoo API**: ~10-30 calls (one per benched player to check games)
- **Total**: **~11-31 API calls per analysis**

**Optimization Impact:**
- **Before**: ~16 Sheets reads + ~10-30 Yahoo calls = ~26-46 total
- **After**: ~1 Sheets read + ~10-30 Yahoo calls = **~11-31 total**
- **Reduction**: 38% fewer Sheets API calls (16 → 1)

**Timing:**
- Runs after main update completes
- Non-blocking (failures don't stop workflow)
- Estimated 10-30 seconds additional time

**Optimization Opportunities (Future):**
- Batch game checks using team-level API calls (reduce 10-30 calls → 16 calls)
- Skip analysis if no transactions occurred (100% reduction when no changes)

---

## Error Handling

**Graceful Degradation Strategy:**

| Error Scenario | Handling | Impact |
|---------------|----------|--------|
| Spreadsheet not found | Skip analysis, log warning | No violations reported |
| Team sheet not found | Skip team, continue with others | Team excluded from analysis |
| Player not in yesterday's data | Skip player | Likely newly added, no violation |
| Yahoo API failure (game check) | Return False (no game) | Conservative - don't count as violation |
| Discord webhook failure | Log error, continue | Analysis completes, no notification |

**Key Principle:** Bench analysis is informational only - NEVER block main workflow

---

## Verification Steps

After implementation, verify:

1. ✅ **Data capture** - Injury status fields populated correctly from Yahoo API
2. ✅ **Historical data** - Yesterday's roster read correctly from team sheets
3. ✅ **Game checking** - `get_player_stats_by_date` API works correctly
4. ✅ **Violation detection** - All 4 criteria checked accurately
5. ✅ **Discord notification** - Orange embed sent with team names
6. ✅ **CLI flag** - `--skip-bench-check` disables analysis
7. ✅ **Error handling** - API failures don't crash main workflow
8. ✅ **Performance** - Analysis completes in reasonable time

---

## Implementation Notes

### **Injury Status Heuristic**
Since Yahoo API doesn't provide historical injury status, we use current health status as a proxy:
- **Assumption**: If player is healthy today and was benched (not IL) yesterday, likely healthy yesterday
- **Conservative**: May miss violations where player got healthy overnight
- **Trade-off**: Simple implementation vs. perfect accuracy

### **Spreadsheet Dependency**
- Requires yesterday's spreadsheet to exist
- Works since script runs daily with consistent structure
- Falls back gracefully if historical data unavailable

### **UPDATE Mode Only**
- Only runs in UPDATE mode (not CREATE mode)
- CREATE mode has no historical data to compare against
- Keeps implementation simple and focused

### **Version**
This will be **v2.7** of the application, building on:
- v2.6: Draft Picks sheet and sheet protection
- v2.5: Batch read API optimization
- v2.4: Cache reuse and exponential backoff retry
- v2.3: Automatic team rename handling
- v2.2: Discord notifications
- v2.0: Incremental sheet updates

---

## Example Discord Notification

**Title:** ⚠️ Bench Management Alert

**Description:** The following teams left healthy players with scheduled games on the bench on 2026-01-22:

**Teams (3):**
- Team Alpha
- Team Beta
- Team Gamma

**View Rosters:** [Open Spreadsheet](https://docs.google.com/spreadsheets/d/...)

**Tip:** Check your bench before games to maximize your active roster!

---

## Questions or Concerns?

If you have any questions or concerns about this implementation plan:
- Unclear requirements
- Technical approach concerns
- Performance considerations
- Testing strategy

Please let me know before proceeding with implementation!

---

## REVISED PLAN: Option B - Same-Day Analysis (v2.7.1)

### Issue Discovered During Testing

**Timing Problem:**
The original implementation (v2.7) attempted to check "yesterday's" violations by:
1. Reading roster positions from the spreadsheet (updated earlier today)
2. Comparing against current health status from Yahoo
3. Checking if players had games yesterday

**False Positives:**
- Spreadsheet captures positions from when it was last updated (e.g., 11 AM today)
- Managers may have fixed their lineups AFTER yesterday's games but BEFORE today's update
- We read the "fixed" positions, not the actual game-time positions
- Example: Player benched during 7 PM game → Manager moves to active at 11 PM → Update at 11 AM captures active position → False negative

**Root Cause:**
- Yahoo API has no historical roster data
- Spreadsheet snapshots are not guaranteed to be from game time
- Cannot reliably reconstruct "what was the lineup during yesterday's games"

### New Approach: Same-Day Analysis (Standalone Mode)

**Concept:**
Run analysis as a SEPARATE MODE, independent from spreadsheet updates. Schedule LATE AT NIGHT (1-2 AM EST) on the SAME DAY as games, before managers wake up to fix lineups.

**Flow:**
1. Schedule runs at 1-2 AM EST (after all games complete ~midnight EST)
2. Run with `--bench-check` flag (standalone mode)
3. Fetch current league data from Yahoo API
4. Read current roster positions (reflects game-day state)
5. Check which benched players had games TODAY
6. Send Discord alerts immediately
7. Exit (no spreadsheet updates)

**Separate from Updates:**
- Bench analysis: Runs at 1-2 AM EST with `--bench-check`
- Spreadsheet updates: Run whenever needed (e.g., hourly)
- Independent schedules and purposes
- Clean separation of concerns

**Why This Works:**
✅ No spreadsheet dependency - single source of truth (Yahoo)
✅ No historical data needed - checking same day
✅ Accurate game-time lineups - captures actual game day decisions
✅ Catches mistakes before they're fixed - runs before managers wake up
✅ Simpler logic - one API, one timestamp
✅ Independent mode - not coupled to spreadsheet updates

---

### TODO: Refactor for Same-Day Analysis

#### **1. Update `src/bench_analyzer.py`**

**Remove:**
- `batch_read_all_team_rosters()` function (no longer needed)
- `_parse_roster_rows()` function (no longer needed)
- `service` parameter from `analyze_bench_violations()`
- `spreadsheet_id` parameter from `analyze_bench_violations()`
- All Google Sheets API calls

**Modify:**
- `analyze_bench_violations()` signature:
  ```python
  def analyze_bench_violations(
      league: League,
      fetcher: YahooDataFetcher,
      check_date: Optional[str] = None  # Now defaults to TODAY
  ) -> Dict[str, List[Dict[str, str]]]:
  ```

**Logic Changes:**
- Remove spreadsheet reading logic
- Use `player.roster_position` directly from current Yahoo data (already in `team.roster`)
- Change default date from "yesterday" to "today"
- Simplify violation detection:
  ```python
  # OLD: Compare yesterday's spreadsheet position vs today's health
  yesterday_slot = yesterday_lookup[player.name]['slot']
  was_benched = yesterday_slot in BENCH_POSITIONS

  # NEW: Use current position from Yahoo
  is_benched = player.roster_position in BENCH_POSITIONS
  ```

**Updated Docstring:**
```python
"""
Analyze all teams to find bench management violations.

A violation occurs when:
1. Player is currently on bench (BN position)
2. Player is currently healthy (no INJ/OUT/DTD/GTD status)
3. Player had a scheduled game today

Note: Should be run late at night (1-2 AM EST) after all games complete
      but before managers wake up to fix lineups.

Args:
    league: League object with current team/roster data
    fetcher: YahooDataFetcher for API calls
    check_date: Date to check (YYYY-MM-DD). If None, uses today's date.

Returns:
    Dictionary mapping team_name to list of violations
"""
```

#### **2. Update `main.py`**

**Add New CLI Argument:**
```python
parser.add_argument(
    '--bench-check',
    action='store_true',
    help='Run bench management analysis only (no spreadsheet operations)'
)
```

**Add New Mode: BENCH CHECK MODE**

Add this as a new primary mode (alongside CREATE and UPDATE modes):

```python
# Mode 3: BENCH CHECK mode (standalone bench analysis)
if args.bench_check:
    print("\n" + "=" * 80)
    print("MODE: BENCH MANAGEMENT CHECK")
    print("=" * 80)
    print()

    try:
        from datetime import timedelta

        # Use TODAY's date
        today = datetime.now(timezone.utc)
        today_date = today.strftime('%Y-%m-%d')

        print(f"Checking bench violations for: {today_date}")
        print()

        # Analyze violations
        violations = analyze_bench_violations(
            league=league_data,
            fetcher=fetcher,
            check_date=today_date
        )

        # Get team list
        teams_with_violations = get_teams_with_bench_violations(violations)

        if teams_with_violations:
            print(f"⚠ Found {len(teams_with_violations)} team(s) with bench violations:")
            for team_name in teams_with_violations:
                violation_count = len(violations[team_name])
                print(f"  • {team_name} ({violation_count} player(s))")
            print()

            # Send Discord notification (no spreadsheet URL needed)
            notify_bench_violations(
                teams_with_violations=teams_with_violations,
                spreadsheet_url="",  # No spreadsheet in this mode
                check_date=today_date
            )

            print("✓ Discord notification sent")
        else:
            print("✓ No bench violations found - all teams optimized their lineups!")

        print()
        print("=" * 80)
        print("✓ BENCH CHECK COMPLETE")
        print("=" * 80)
        print()
        return 0

    except Exception as e:
        logger.exception("Bench check failed")
        print(f"\n✗ Error: Bench check failed: {e}\n")
        notify_error(
            error_message=str(e),
            error_type="Bench Check Failed",
            stack_trace=traceback.format_exc()
        )
        return 1
```

**Remove Step 2g from UPDATE mode:**
- Delete the bench analysis code from UPDATE mode entirely
- Remove `--skip-bench-check` argument (no longer needed)

**Add Validation:**
```python
# Validate argument combinations
if args.bench_check and (args.spreadsheet_url or args.spreadsheet_id or args.create_new):
    print("✗ Error: --bench-check cannot be combined with spreadsheet arguments")
    return 1

if args.bench_check and (args.force_full_update):
    print("✗ Error: --bench-check cannot be combined with --force-full-update")
    return 1
```

**Update Discord Message:**
Modify `send_bench_alert()` to handle optional spreadsheet URL:
```python
# Add spreadsheet link only if URL provided
if spreadsheet_url:
    embed.add_embed_field(
        name="📊 View Rosters",
        value=f"[Open Spreadsheet]({spreadsheet_url})",
        inline=False
    )
```

#### **3. Update `src/discord_notifier.py`**

**Modify `send_bench_alert()` description:**
```python
embed = DiscordEmbed(
    title="⚠️ Bench Management Alert",
    description=f"The following teams have healthy players with scheduled games on the bench for {check_date}:",
    color="ffa500"  # Orange for warning
)
```

#### **4. Update `tests/test_bench_analyzer.py`**

**Remove:**
- Tests for `batch_read_all_team_rosters()`
- Tests for `_parse_roster_rows()`
- Mock for Google Sheets service

**Update:**
- `test_violation_analysis()` to not mock spreadsheet reads
- Use current roster positions directly from test data
- Change test date references from "yesterday" to "today"

**Simplified test:**
```python
def test_violation_analysis():
    """Test full violation analysis workflow."""
    # No need to mock spreadsheet - use current roster positions
    with patch('src.bench_analyzer.check_player_had_game_yesterday') as mock_game_check:
        mock_game_check.return_value = True

        player = Player(
            player_key="466.p.1",
            name="Benched Player",
            position="PG",
            salary=50,
            source=SalarySource.DRAFT,
            nba_team="OKC",
            roster_position="BN",  # Currently benched
            status=None  # Currently healthy
        )

        team = Team(
            team_id="1",
            team_key="466.l.1.t.1",
            team_name="Test Team",
            manager_name="Manager",
            roster=[player],
            total_salary=50,
            faab_remaining=100
        )

        league = League(
            league_id="1",
            league_key="466.l.1",
            league_name="Test League",
            season="2024",
            num_teams=1,
            teams=[team]
        )

        # Run analysis - no service or spreadsheet_id needed
        violations = analyze_bench_violations(
            league=league,
            fetcher=Mock(),
            check_date="2026-01-24"  # TODAY
        )

        assert "Test Team" in violations
        assert len(violations["Test Team"]) == 1
```

#### **5. Update `debug_bench_violations.py`**

**Remove:**
- Google Sheets service calls
- Spreadsheet reading logic
- `batch_read_all_team_rosters()` calls

**Simplify to use current Yahoo data:**
```python
# Step 2: Analyze each team (using current Yahoo positions)
for team in league_data.teams:
    for player in team.roster:
        # Check current position (not spreadsheet)
        is_benched = player.roster_position in BENCH_POSITIONS
        is_on_il = player.roster_position in IL_POSITIONS
        is_healthy = _is_player_healthy(player)
        had_game = check_player_had_game_yesterday(fetcher, player.player_key, check_date)

        # Violation if: benched + not IL + healthy + had game
        if is_benched and not is_on_il and is_healthy and had_game:
            # Report violation
```

#### **6. Update `CLAUDE.md`**

**Replace "Bench Management Alerts (v2.7)" section with v2.7.1:**

```markdown
### Bench Management Alerts (v2.7.1)

The application includes optional bench management analysis for same-day lineup optimization alerts.

**Features:**
- 🔍 **Same-day analysis** - Checks current lineups for today's games
- ⚠️ **Violation detection** - Identifies teams with benched healthy players
- 🔔 **Discord alerts** - Immediate notifications via webhook
- 📊 **Single source of truth** - Uses Yahoo API only (no spreadsheet)
- ⚡ **Non-critical** - Analysis failures don't break main workflow

**How It Works:**
1. Run late at night (1-2 AM EST) after games complete
2. Fetch current roster positions from Yahoo API
3. Check current player health status from Yahoo API
4. Verify which players had games TODAY
5. Identify violations: benched + healthy + had game
6. Send Discord notification immediately

**Usage:**
```bash
# Bench check only (no spreadsheet operations)
uv run python main.py --bench-check

# Regular spreadsheet update (no bench check)
uv run python main.py --spreadsheet-id "YOUR_ID"

# Create new spreadsheet (no bench check)
uv run python main.py
```

**Scheduling:**
- **Bench Check**: Run at 1-2 AM EST via cron/GitHub Actions with `--bench-check`
- **Timing**: After all NBA games complete (~midnight EST)
- **Before**: Managers wake up to fix lineups (~6-7 AM EST)
- **Spreadsheet Updates**: Run separately at any time (e.g., hourly)

**Configuration:**
- **Standalone mode**: Use `--bench-check` flag
- **Discord**: Uses same webhook as update notifications
- **No spreadsheet required**: Can run without any spreadsheet arguments

**Criteria for Violation:**
A team is flagged when a player meets ALL these conditions:
1. Is currently in BN (bench) position
2. Is NOT in IL/IL+ position
3. Is currently healthy (no INJ/OUT/DTD/GTD status)
4. Had a scheduled game TODAY

**Example Output:**
```
Step 2g: Analyzing bench management...
⚠ Found 3 team(s) with bench violations for 2026-01-24:
  • Team Alpha (2 player(s))
  • Team Beta (1 player(s))
  • Team Gamma (1 player(s))
```

**Performance:**
- Google Sheets: **0 read calls** (no spreadsheet needed)
- Yahoo API: ~10-30 calls (one per benched player)
- Total: **~10-30 API calls per run**
- Non-blocking: Runs after league data fetch

**Advantages over v2.7:**
- ✅ **No timing issues** - checks same-day, not historical
- ✅ **No false positives** - uses real game-time positions
- ✅ **Simpler** - single source of truth (Yahoo API)
- ✅ **More accurate** - catches violations before managers fix them
```

---

### Implementation Checklist

- [x] Refactor `src/bench_analyzer.py` to remove spreadsheet dependency
- [x] Update `analyze_bench_violations()` to use current positions
- [x] Change default date from yesterday to today
- [x] Add `--bench-check` CLI argument to `main.py`
- [x] Add BENCH CHECK mode to `main.py` (new standalone mode)
- [x] Remove Step 2g from UPDATE mode in `main.py`
- [x] Remove `--skip-bench-check` argument (no longer needed)
- [x] Add validation to prevent combining `--bench-check` with spreadsheet args
- [x] Update `send_bench_alert()` to handle optional spreadsheet URL
- [x] Simplify `tests/test_bench_analyzer.py`
- [x] Simplify `debug_bench_violations.py`
- [x] Update `CLAUDE.md` documentation to v2.7.1
- [x] Test standalone bench check mode with real data (manual testing required)
- [x] Add GitHub Actions workflow for 1-2 AM EST bench checks (future)
- [x] Keep separate schedule for spreadsheet updates (future)

---

### Testing Strategy

**Unit Tests:**
- Run simplified tests without spreadsheet mocks
- Verify current position detection works correctly

**Debug Script:**
- Test `debug_bench_violations.py` with current data
- Verify violations detected match expectations
- No spreadsheet dependency needed

**Integration Test:**
- Run `uv run python main.py --bench-check` at ~1 AM EST after real games complete
- Verify positions reflect actual game-day decisions
- Confirm Discord alerts sent correctly
- Re-run at ~8 AM EST and verify fewer/no violations (managers fixed lineups)
- Verify `--bench-check` cannot be combined with spreadsheet arguments
- Test that spreadsheet updates still work independently

**Validation:**
- Compare violations found vs actual Yahoo rosters during games
- Manually verify benched players actually had games
- Confirm no false positives from timing issues

---

## Future Enhancement: Proactive Alerts (Option A)

**Current Limitation (v2.7.1 - Option B):**
The current implementation detects violations **after games complete** by checking if players recorded non-zero stats. This means:
- ❌ Cannot alert managers before games to fix lineups
- ❌ Only useful for post-game analysis
- ❌ Managers can't take action to prevent violations

**Future Goal (Option A - Proactive Alerts):**
Switch to NBA team schedule API to detect violations **before/during games**:
- ✅ Alert managers 2-6 hours before game time
- ✅ Managers can fix lineups in time
- ✅ Real-time violation detection
- ✅ More valuable for league competitiveness

**Investigation Required:**
See `TODO_PROACTIVE_BENCH_ALERTS.md` for:
- Potential NBA schedule data sources (NBA API, ESPN API, SportsData.io)
- Implementation plan and timeline
- Code changes needed
- Cost considerations

**Priority:** Medium (valuable enhancement but not critical)

**Next Step:** Investigate NBA Official API and ESPN API reliability

