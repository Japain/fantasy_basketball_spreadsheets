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
