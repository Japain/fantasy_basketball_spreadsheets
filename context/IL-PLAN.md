# Implementation Plan: IL/IL+ Healthy Player Detection

## Overview
Extend bench analysis to detect and alert when healthy players are placed in IL or IL+ roster slots. This is a roster management inefficiency that wastes injured list spots.

## Requirements (Confirmed with User)
1. Check **both IL and IL+ positions** for healthy players
2. **No game schedule check** - flag any healthy player regardless of scheduled games
3. **Combined Discord alert** - show both bench violations and IL violations in one message
4. **No optimal lineup logic** - always flag healthy players in IL/IL+ slots

## Architecture Overview

### Current System (Bench Violations)
```
analyze_bench_violations() → violations dict → send_bench_alert() → Discord
```

### Extended System (Bench + IL Violations)
```
analyze_bench_violations() → bench_violations dict ─┐
                                                      ├→ send_combined_alert() → Discord
analyze_il_violations() → il_violations dict ────────┘
```

## Implementation Steps

### Step 1: Add IL Position Helper Function
**File:** `src/bench_analyzer.py`

Add new helper function after `_is_on_il()` (around line 112):

```python
def _is_on_il_or_il_plus(player: Player) -> bool:
    """
    Check if player is on IL or IL+ (either injured list slot).

    Args:
        player: Player object to check

    Returns:
        True if player is in IL or IL+ position, False otherwise
    """
    if not player.roster_position:
        return False
    return player.roster_position in IL_POSITIONS  # {'IL', 'IL+'}
```

**Note:** This is identical to existing `_is_on_il()` but more explicit in naming for the new feature.

---

### Step 2: Add IL Violation Analysis Function
**File:** `src/bench_analyzer.py`

Add new function after `analyze_bench_violations()` (around line 445):

```python
def analyze_il_violations(
    league: League,
    fetcher: YahooDataFetcher,
) -> Dict[str, List[Dict[str, str]]]:
    """
    Analyze teams for healthy players in IL/IL+ slots.

    A violation occurs when:
    1. Player is in IL or IL+ position
    2. Player is currently healthy (no injury status)

    Args:
        league: League object containing teams and rosters
        fetcher: YahooDataFetcher instance (kept for consistency, not used)

    Returns:
        Dictionary mapping team names to lists of violating players:
        {
            "Team Name": [
                {
                    'player_name': 'Player Name',
                    'nba_team': 'LAL',
                    'position': 'PG,SG',
                    'roster_slot': 'IL+'
                },
                ...
            ],
            ...
        }
    """
    violations = {}

    for team in league.teams:
        team_violations = []

        for player in team.roster:
            # Condition 1: Is player on IL or IL+?
            if not _is_on_il_or_il_plus(player):
                continue  # Not on IL, skip

            # Condition 2: Is player healthy?
            if not _is_player_healthy(player):
                continue  # Player is injured, no violation

            # VIOLATION FOUND: Healthy player in IL/IL+ slot
            team_violations.append({
                'player_name': player.name,
                'nba_team': player.nba_team or 'N/A',
                'position': player.position or 'N/A',
                'roster_slot': player.roster_position or 'N/A'
            })

        if team_violations:
            violations[team.name] = team_violations

    return violations
```

**Key Differences from Bench Violations:**
- ✅ No game schedule check (per requirements)
- ✅ No optimal lineup logic (per requirements)
- ✅ Simpler: just 2 conditions instead of 5
- ✅ Includes `roster_slot` field to show if IL or IL+

---

### Step 3: Update Discord Notification
**File:** `src/discord_notifier.py`

**3a. Rename and Extend `send_bench_alert()` method**

Current method signature (line 222):
```python
def send_bench_alert(
    self,
    teams_with_violations: list,
    spreadsheet_url: str,
    check_date: str
) -> bool:
```

Change to:
```python
def send_bench_alert(
    self,
    bench_teams: list,
    il_violations: Dict[str, List[Dict[str, str]]],
    spreadsheet_url: str,
    check_date: str
) -> bool:
    """
    Send bench management alert via Discord webhook.

    Shows both bench violations (healthy players on bench with games)
    and IL violations (healthy players in IL/IL+ slots) in a single alert.

    Args:
        bench_teams: List of team names with bench violations
        il_violations: Dict mapping team names to IL violation details (includes player names)
        spreadsheet_url: URL to the league spreadsheet
        check_date: Date string for the violations (YYYY-MM-DD)

    Returns:
        True if notification sent successfully, False otherwise
    """
```

**3b. Update message construction logic**

Around line 235-260, update to handle both violation types:

```python
# Count total violations
total_violations = len(bench_teams) + len(il_violations)

if total_violations == 0:
    logger.info("No bench or IL violations to report")
    return False

# Build title
title = "⚠️ Roster Management Alert"

# Build description
description_parts = []
if bench_teams:
    description_parts.append(
        f"**{len(bench_teams)} team(s) with bench violations**\n"
        "Healthy players on bench who have games today"
    )
if il_violations:
    description_parts.append(
        f"**{len(il_violations)} team(s) with IL violations**\n"
        "Healthy players in IL/IL+ slots"
    )

description = "\n\n".join(description_parts)

# Build team lists
bench_list = "\n".join(f"• {team}" for team in bench_teams) if bench_teams else "None"

# Build IL list with player details
if il_violations:
    il_list_parts = []
    for team_name, team_violations in il_violations.items():
        il_list_parts.append(f"• **{team_name}**")
        for player in team_violations:
            player_info = f"  - {player['player_name']} ({player['nba_team']} - {player['position']}) [{player['roster_slot']}]"
            il_list_parts.append(player_info)
    il_list = "\n".join(il_list_parts)
else:
    il_list = "None"

# Create embed
embed = {
    "title": title,
    "description": description,
    "color": int("ffa500", 16),  # Orange
    "fields": [
        {
            "name": "🏀 Bench Violations",
            "value": bench_list,
            "inline": False
        },
        {
            "name": "🏥 IL/IL+ Violations",
            "value": il_list,
            "inline": False
        },
        {
            "name": "📊 View Rosters",
            "value": f"[Open Spreadsheet]({spreadsheet_url})" if spreadsheet_url else "N/A",
            "inline": False
        },
        {
            "name": "💡 Tip",
            "value": (
                "**Bench**: Move healthy benched players to active roster\n"
                "**IL**: Activate healthy players from IL/IL+ slots"
            ),
            "inline": False
        }
    ],
    "footer": {
        "text": f"Check date: {check_date}"
    },
    "timestamp": datetime.now(timezone.utc).isoformat()
}
```

---

### Step 4: Update Convenience Function
**File:** `src/discord_notifier.py`

Update `notify_bench_violations()` function (around line 365):

```python
def notify_bench_violations(
    bench_violations: Dict[str, List[Dict[str, str]]],
    il_violations: Dict[str, List[Dict[str, str]]],
    spreadsheet_url: str = "",
    check_date: str = ""
) -> bool:
    """
    Convenience function to send bench and IL violation notifications.

    Args:
        bench_violations: Dict mapping team names to bench violation details
        il_violations: Dict mapping team names to IL violation details
        spreadsheet_url: Optional URL to the league spreadsheet
        check_date: Optional date string for the violations

    Returns:
        True if notification sent, False if Discord disabled or no violations
    """
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '').strip()

    if not webhook_url:
        logger.info("Discord notifications disabled (no webhook URL)")
        return False

    # Convert bench violations to team list
    bench_teams = get_teams_with_bench_violations(bench_violations)

    # Send combined alert (pass full IL violations dict for player details)
    notifier = DiscordNotifier(webhook_url)
    return notifier.send_bench_alert(
        bench_teams=bench_teams,
        il_violations=il_violations,
        spreadsheet_url=spreadsheet_url,
        check_date=check_date
    )
```

---

### Step 5: Update Main Execution Flow
**File:** `main.py`

Update bench check mode (around line 200-240):

```python
if args.bench_check:
    logger.info("="*80)
    logger.info("MODE: BENCH MANAGEMENT CHECK")
    logger.info("="*80)
    logger.info("")

    # Determine check date (Pacific timezone)
    pacific_tz = ZoneInfo("America/Los_Angeles")
    today = datetime.now(pacific_tz)
    check_date = today.strftime('%Y-%m-%d')

    logger.info(f"Checking violations for: {check_date}")
    logger.info("")

    # Analyze bench violations
    bench_violations = analyze_bench_violations(league, fetcher, check_date)
    bench_teams = get_teams_with_bench_violations(bench_violations)

    # Analyze IL violations (NEW)
    il_violations = analyze_il_violations(league, fetcher)
    il_teams = list(il_violations.keys())

    # Report findings
    total_violations = len(bench_teams) + len(il_teams)

    if total_violations > 0:
        logger.info(f"⚠ Found {total_violations} team(s) with violations:")

        if bench_teams:
            logger.info(f"\n  Bench Violations ({len(bench_teams)} team(s)):")
            for team_name in bench_teams:
                player_count = len(bench_violations[team_name])
                logger.info(f"    • {team_name} ({player_count} player(s))")

        if il_teams:
            logger.info(f"\n  IL/IL+ Violations ({len(il_teams)} team(s)):")
            for team_name in il_teams:
                player_count = len(il_violations[team_name])
                logger.info(f"    • {team_name} ({player_count} player(s))")

        logger.info("")

        # Send Discord notification
        success = notify_bench_violations(
            bench_violations=bench_violations,
            il_violations=il_violations,
            spreadsheet_url="",
            check_date=check_date
        )

        if success:
            logger.info("✓ Discord notification sent")
        else:
            logger.info("ℹ Discord notification skipped (disabled or failed)")
    else:
        logger.info("✓ No violations found")

    logger.info("")
    logger.info("="*80)
    logger.info("✓ BENCH CHECK COMPLETE")
    logger.info("="*80)
    sys.exit(0)
```

---

### Step 6: Add Tests
**File:** `tests/test_bench_analyzer.py`

Add new test cases after existing bench violation tests:

```python
def test_is_on_il_or_il_plus():
    """Test IL/IL+ position detection."""
    # Test IL position
    player_il = Player(
        player_key="466.p.1",
        name="Test Player",
        position="PG",
        salary=10,
        source=SalarySource.DRAFT,
        roster_position="IL"
    )
    assert _is_on_il_or_il_plus(player_il) is True

    # Test IL+ position
    player_il_plus = Player(
        player_key="466.p.2",
        name="Test Player 2",
        position="SG",
        salary=15,
        source=SalarySource.DRAFT,
        roster_position="IL+"
    )
    assert _is_on_il_or_il_plus(player_il_plus) is True

    # Test non-IL position
    player_bench = Player(
        player_key="466.p.3",
        name="Test Player 3",
        position="SF",
        salary=20,
        source=SalarySource.DRAFT,
        roster_position="BN"
    )
    assert _is_on_il_or_il_plus(player_bench) is False


def test_analyze_il_violations():
    """Test IL violation detection for healthy players in IL/IL+ slots."""
    # Create test players
    healthy_on_il = Player(
        player_key="466.p.1",
        name="Healthy IL Player",
        position="PG",
        salary=10,
        source=SalarySource.DRAFT,
        nba_team="LAL",
        roster_position="IL",
        status=None  # Healthy
    )

    healthy_on_il_plus = Player(
        player_key="466.p.2",
        name="Healthy IL+ Player",
        position="SG",
        salary=15,
        source=SalarySource.DRAFT,
        nba_team="GSW",
        roster_position="IL+",
        status=None  # Healthy
    )

    injured_on_il = Player(
        player_key="466.p.3",
        name="Injured IL Player",
        position="SF",
        salary=20,
        source=SalarySource.DRAFT,
        nba_team="BOS",
        roster_position="IL",
        status="INJ"  # Injured (not a violation)
    )

    healthy_on_bench = Player(
        player_key="466.p.4",
        name="Healthy Bench Player",
        position="PF",
        salary=25,
        source=SalarySource.DRAFT,
        nba_team="MIA",
        roster_position="BN",
        status=None  # Healthy but on bench (not an IL violation)
    )

    # Create test team with violations
    team_with_violations = Team(
        team_key="466.l.12345.t.1",
        name="Team Alpha",
        roster=[healthy_on_il, healthy_on_il_plus, injured_on_il, healthy_on_bench],
        total_salary=70,
        transactions=[],
        managers=[]
    )

    # Create test team without violations
    team_without_violations = Team(
        team_key="466.l.12345.t.2",
        name="Team Beta",
        roster=[injured_on_il, healthy_on_bench],
        total_salary=45,
        transactions=[],
        managers=[]
    )

    # Create league
    league = League(
        league_key="466.l.12345",
        league_id="12345",
        name="Test League",
        season="2024-25",
        teams=[team_with_violations, team_without_violations],
        current_week=10,
        total_teams=2
    )

    # Mock fetcher (not used but required by signature)
    fetcher = None

    # Run analysis
    violations = analyze_il_violations(league, fetcher)

    # Verify results
    assert "Team Alpha" in violations
    assert len(violations["Team Alpha"]) == 2  # Both IL and IL+ violations

    assert violations["Team Alpha"][0]['player_name'] == "Healthy IL Player"
    assert violations["Team Alpha"][0]['roster_slot'] == "IL"

    assert violations["Team Alpha"][1]['player_name'] == "Healthy IL+ Player"
    assert violations["Team Alpha"][1]['roster_slot'] == "IL+"

    assert "Team Beta" not in violations  # No violations


def test_analyze_il_violations_empty_league():
    """Test IL violation analysis with no teams."""
    league = League(
        league_key="466.l.12345",
        league_id="12345",
        name="Empty League",
        season="2024-25",
        teams=[],
        current_week=10,
        total_teams=0
    )

    violations = analyze_il_violations(league, None)
    assert violations == {}
```

---

## Critical Files to Modify

1. **`src/bench_analyzer.py`** (Primary changes)
   - Add `_is_on_il_or_il_plus()` helper function
   - Add `analyze_il_violations()` analysis function
   - Export new function in module

2. **`src/discord_notifier.py`** (Notification updates)
   - Update `send_bench_alert()` to accept both violation types
   - Update `notify_bench_violations()` convenience function
   - Modify embed structure for combined alerts

3. **`main.py`** (Execution flow)
   - Add IL violation analysis call in bench check mode
   - Update logging to show both violation types
   - Pass both violations to notification function

4. **`tests/test_bench_analyzer.py`** (Testing)
   - Add `test_is_on_il_or_il_plus()` test
   - Add `test_analyze_il_violations()` test
   - Add `test_analyze_il_violations_empty_league()` test

---

## Implementation Notes

### Simplifications
Since no game schedule check is needed:
- ✅ No dependency on `nba_schedule_fetcher.py`
- ✅ No ESPN/NBA API calls
- ✅ Zero additional API overhead
- ✅ Instant analysis (no network latency)

### Data Flow
```
League object
    ↓
analyze_il_violations()
    ├─ For each team
    │   ├─ For each player in roster
    │   │   ├─ Check: Is on IL/IL+?
    │   │   └─ Check: Is healthy?
    │   └─ Collect violations
    ↓
Return violations dict
    ↓
notify_bench_violations(bench_violations, il_violations)
    ↓
send_bench_alert(bench_teams, il_teams)
    ↓
Discord webhook (combined alert)
```

### Error Handling
- Follows existing patterns in `bench_analyzer.py`
- Graceful handling of missing player fields (nba_team, position)
- Non-blocking: IL analysis failure doesn't break bench check

---

## Testing & Verification

### Unit Tests
```bash
# Run specific tests
uv run python -m pytest tests/test_bench_analyzer.py::test_is_on_il_or_il_plus -v
uv run python -m pytest tests/test_bench_analyzer.py::test_analyze_il_violations -v

# Run all bench analyzer tests
uv run python -m pytest tests/test_bench_analyzer.py -v
```

### Integration Test
```bash
# Run bench check in real environment
uv run python main.py --bench-check

# Expected output:
# ================================================================================
# MODE: BENCH MANAGEMENT CHECK
# ================================================================================
#
# Checking violations for: 2026-01-31
#
# ⚠ Found 3 team(s) with violations:
#
#   Bench Violations (2 team(s)):
#     • Team Alpha (1 player(s))
#     • Team Beta (2 player(s))
#
#   IL/IL+ Violations (1 team(s)):
#     • Team Gamma (1 player(s))
#
# ✓ Discord notification sent
# ================================================================================
# ✓ BENCH CHECK COMPLETE
# ================================================================================
```

### Discord Alert Verification
Expected Discord embed format:
```
⚠️ Roster Management Alert

**2 team(s) with bench violations**
Healthy players on bench who have games today

**1 team(s) with IL violations**
Healthy players in IL/IL+ slots

🏀 Bench Violations
• Team Alpha
• Team Beta

🏥 IL/IL+ Violations
• **Team Gamma**
  - LeBron James (LAL - SF,PF) [IL+]
  - Steph Curry (GSW - PG,SG) [IL]

📊 View Rosters
[Open Spreadsheet](URL)

💡 Tip
Bench: Move healthy benched players to active roster
IL: Activate healthy players from IL/IL+ slots

Check date: 2026-01-31
```

---

## Edge Cases Handled

1. **No violations**: Returns empty dict, Discord alert not sent
2. **Only bench violations**: IL section shows "None"
3. **Only IL violations**: Bench section shows "None"
4. **Both violation types**: Both sections populated
5. **Missing player fields**: Defaults to 'N/A' for nba_team, position
6. **Empty league**: Returns empty dict (no crashes)
7. **No Discord webhook**: Graceful skip (logged, not sent)

---

## Backwards Compatibility

- ✅ Existing bench violation detection unchanged
- ✅ New parameters added to functions (not breaking changes)
- ✅ Discord webhook optional (can be disabled)
- ✅ Works with or without IL violations present

---

## Performance Impact

- **API Calls**: Zero additional API calls (no game schedule check)
- **Processing Time**: ~1-5ms per team (simple roster iteration)
- **Memory**: Minimal (one additional dict in memory)
- **Network**: Zero additional network requests

---

## Future Enhancements (Not in Scope)

- Verbose mode showing specific player names in logs
- Separate Discord alerts (configurable)
- Historical tracking of IL violations
- Suggestions for which players to activate
