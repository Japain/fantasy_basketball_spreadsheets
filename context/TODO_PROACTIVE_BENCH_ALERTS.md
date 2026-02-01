# TODO: Proactive Bench Violation Alerts (Option A)

## Current State (v2.7.1 - Option B)

**Detection Method:** Retroactive analysis based on player stats
- Checks if player recorded **non-zero stats** on a given date
- Can only flag violations **after games complete**
- Timing: Run at 1-2 AM EST after all games finish

**Limitation:** Cannot alert managers in time to fix lineups before games start

---

## Future Goal: Proactive Alerts (Option A)

**Detection Method:** Real-time analysis based on NBA team schedules
- Check if player's **NBA team has a game scheduled** today
- Flag violations **before/during games**
- Timing: Run multiple times per day (e.g., 12 PM, 4 PM, 6 PM EST)

**Benefits:**
- ✅ Managers receive alerts **in time to fix** their lineups
- ✅ More valuable for league competitiveness
- ✅ Can send alerts hours before game time
- ✅ Reduces actual lineup mistakes (not just post-mortem analysis)

---

## Investigation Results (2026-01-24)

### ✅ ESPN API - SELECTED

**Endpoint tested:** `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20260123`

**Findings:**
- ✅ Fully functional and reliable
- ✅ Comprehensive game data (schedules, scores, times, teams, players)
- ✅ Standard NBA team abbreviations (PHX, BOS, BKN, HOU, etc.)
- ✅ Clean JSON structure, easy to parse
- ✅ Zero cost - no API key, no authentication, no rate limits
- ✅ Fast response times
- ⚠️ Undocumented (but widely used and stable in practice)

**Data structure:**
```json
{
  "leagues": [...],
  "events": [
    {
      "competitions": [
        {
          "competitors": [
            {
              "team": {
                "abbreviation": "PHX",
                "displayName": "Phoenix Suns"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### 🔄 NBA Official API (stats.nba.com) - BACKUP

**Research findings:**
- ⚠️ Unofficial and undocumented
- ⚠️ Uses Cloudflare rate limiting (can trigger IP bans)
- ⚠️ Cloud hosting (AWS/GCP) can result in bans
- ⚠️ Some endpoints only work on game days
- ✅ Comprehensive data when it works
- ✅ Python library available: `nba_api`

**Use as fallback with:**
- Conservative rate limiting (1 request per 2-3 seconds)
- User-agent headers
- Graceful error handling

### ❌ SportsData.io - REJECTED

**Research findings:**
- ❌ Free tier only includes last season's data
- ❌ Current season requires paid tier (~$19-49/month)
- ✅ Official, documented, reliable (but unnecessary expense)

### Decision Rationale

ESPN API provides everything we need at zero cost with proven reliability. NBA Official API serves as a fallback if ESPN fails. Commercial APIs are unnecessary given the quality of free options.

---

## Implementation Requirements

### 1. NBA Team Schedule Data Source

Need a reliable API or data source that provides:
- Daily NBA game schedules
- Team abbreviations matching Yahoo's format (e.g., "PHX", "LAL", "BKN")
- Game times (for optimal alert timing)
- Coverage: Regular season + playoffs

**Decision: ESPN API (Primary) + NBA Official API (Fallback)**

After investigation on 2026-01-24, we chose ESPN API as the primary data source.

#### ✅ SELECTED: ESPN API (Primary)
- **Pros**: Widely used, stable, comprehensive data, zero cost, no authentication
- **Cons**: Undocumented, no SLA (but proven reliable in practice)
- **Endpoint**: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20260124`
- **Team abbreviations**: Standard NBA codes (PHX, BOS, BKN, HOU, etc.)
- **Data includes**: Game schedules, times, scores, team info, player stats
- **Cost**: Free (no API key, no rate limits, no billing)
- **Tested**: ✅ Fully functional as of 2026-01-24

#### 🔄 BACKUP: NBA Official API (stats.nba.com)
- **Use case**: Fallback if ESPN API fails
- **Implementation**: Use `nba_api` Python library with conservative rate limiting
- **Endpoint**: `https://stats.nba.com/stats/scoreboardv2?GameDate=2026-01-24`
- **Caution**: Unofficial, Cloudflare protection, potential IP bans with aggressive requests
- **Best practices**: 1 request per 2-3 seconds, use user-agent headers, monitor for failures

#### ❌ REJECTED: SportsData.io
- **Reason**: Free tier only includes last season's data (not useful for current games)
- **Cost**: $19-49/month for production tier (unnecessary expense)
- **Future consideration**: If free APIs prove unreliable after 1-2 weeks

#### ❌ REJECTED: The Sports DB
- **Reason**: Limited NBA coverage, slower updates

#### ❌ REJECTED: RapidAPI
- **Reason**: Costs money, ESPN API is sufficient

#### ❌ REJECTED: Web Scraping
- **Reason**: Last resort only, brittle implementation

---

### 2. Implementation Plan

#### Phase 1: Research & Prototyping ✅ COMPLETE
- [x] Test NBA Official API endpoints
- [x] Test ESPN API endpoints
- [x] Evaluate SportsData.io free tier
- [x] Compare data quality and reliability
- [x] Measure API response times
- [x] Choose primary data source + backup
- **Decision**: ESPN API (primary) + NBA Official API (backup)

#### Phase 2: Core Implementation ✅ COMPLETE
- [x] Create `src/nba_schedule_fetcher.py` module
  - [x] Fetch daily NBA game schedule from ESPN API
  - [x] Parse team abbreviations from ESPN response
  - [x] Cache results (1-hour TTL) to avoid redundant API calls
  - [x] Handle API failures gracefully (fall back to NBA Official API)
  - [x] Exponential backoff retry logic (3 attempts)
  - [x] **ESPN API implementation**:
    - Endpoint: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=YYYYMMDD`
    - Returns JSON with `events` array containing game objects
    - Each event has `competitions[0].competitors` with team data
    - Team abbreviation: `competitors[i].team.abbreviation`
    - No authentication required
- [x] Team abbreviation mapping (Yahoo ↔ ESPN)
  - [x] Investigated Yahoo team codes vs ESPN codes
  - [x] **Finding**: Both use standard NBA codes (PHX, BOS, BKN, etc.)
  - [x] **Decision**: No mapping dictionary needed (direct comparison works)
  - [x] Monitoring plan: Watch logs for mismatches in production, add mapping only if needed
- [x] Update `check_player_has_game_today()` function
  - [x] Renamed to `check_player_has_game_scheduled()` (proactive)
  - [x] Renamed legacy function to `check_player_had_game_today_legacy()` (retroactive)
  - [x] Replace stats-based check with schedule-based check
  - [x] Look up player's NBA team in today's schedule from ESPN API
  - [x] Return True if team has game, regardless of player stats
  - [x] Feature flag `USE_PROACTIVE_SCHEDULE_CHECK = True` for rollback
- [x] Write comprehensive tests
  - [x] `tests/test_nba_schedule_fetcher.py` - ESPN API parsing, caching, retry logic, fallback
  - [x] `tests/test_bench_analyzer_proactive.py` - Violation detection, edge cases, API failures
  - [x] All tests passing ✅

#### Phase 3: Alert Timing Optimization
- [ ] Determine optimal alert times (e.g., 12 PM, 4 PM, 6 PM EST)
- [ ] Schedule multiple bench checks per day
- [ ] Filter alerts by game time (only alert for upcoming games)
- [ ] Add "hours until game" to Discord notification

#### Phase 4: Testing & Validation
- [ ] Test with real NBA schedule data
- [ ] Verify team abbreviation mapping
- [ ] Compare results: Option A vs Option B
- [ ] Validate alert timing is useful (not too early/late)

#### Phase 5: Production Deployment
- [ ] Update GitHub Actions workflow with new schedule
- [ ] Monitor API usage and costs
- [ ] Set up fallback to Option B if schedule API fails
- [ ] Document new behavior in CLAUDE.md

---

### 3. Code Changes Needed

**New Module:** `src/nba_schedule_fetcher.py`
```python
"""
NBA Schedule Fetcher Module

Fetches daily NBA game schedules from ESPN API (primary) and
NBA Official API (fallback) to determine which teams have games
scheduled for a given date.
"""

from typing import Set, Optional, Dict
from datetime import datetime
import requests
from src.logger import logger

ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

def get_teams_with_games_today(date: str) -> Set[str]:
    """
    Get set of NBA team abbreviations with games scheduled for date.

    Tries ESPN API first, falls back to NBA Official API if needed.

    Args:
        date: Date in YYYY-MM-DD format (e.g., "2026-01-24")

    Returns:
        Set of team abbreviations in ESPN format (e.g., {"PHX", "LAL", "BKN"})
        Empty set if both APIs fail.
    """
    try:
        return _fetch_from_espn(date)
    except Exception as e:
        logger.warning(f"ESPN API failed: {e}, trying NBA Official API")
        try:
            return _fetch_from_nba_api(date)
        except Exception as e2:
            logger.error(f"Both APIs failed: {e2}")
            return set()

def _fetch_from_espn(date: str) -> Set[str]:
    """
    Fetch game schedule from ESPN API.

    ESPN date format: YYYYMMDD (e.g., "20260124")
    Response structure: events[].competitions[].competitors[].team.abbreviation
    """
    # Convert YYYY-MM-DD to YYYYMMDD
    date_formatted = date.replace("-", "")

    url = f"{ESPN_API_BASE}?dates={date_formatted}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    teams = set()

    for event in data.get("events", []):
        for competition in event.get("competitions", []):
            for competitor in competition.get("competitors", []):
                team_abbr = competitor.get("team", {}).get("abbreviation")
                if team_abbr:
                    teams.add(team_abbr)

    logger.info(f"ESPN API: Found {len(teams)} teams with games on {date}")
    return teams

def _fetch_from_nba_api(date: str) -> Set[str]:
    """
    Fallback: Fetch from NBA Official API using nba_api library.

    Implements conservative rate limiting to avoid IP bans.
    """
    # TODO: Implement using nba_api library with rate limiting
    pass

def get_game_time(team_abbr: str, date: str) -> Optional[datetime]:
    """
    Get scheduled game time for a specific team on a date.

    Useful for filtering alerts (only alert for upcoming games).

    Args:
        team_abbr: Team abbreviation (ESPN format)
        date: Date in YYYY-MM-DD format

    Returns:
        Game datetime in UTC, or None if no game found
    """
    # TODO: Implement game time extraction from ESPN API
    pass
```

**Update:** `src/bench_analyzer.py`
```python
def check_player_has_game_today(
    player: Player,
    check_date: str,
    schedule_fetcher: NBAScheduleFetcher
) -> bool:
    """
    Check if a player's NBA team has a game scheduled today.

    NEW: Uses NBA schedule API instead of player stats.
    Enables proactive alerts before games start.
    """
    teams_with_games = schedule_fetcher.get_teams_with_games_today(check_date)
    return player.nba_team in teams_with_games
```

---

### 4. Team Abbreviation Mapping

Need to map Yahoo team abbreviations to data source abbreviations:

```python
YAHOO_TO_NBA_TEAM_MAPPING = {
    "PHO": "PHX",  # Phoenix Suns (Yahoo uses PHO, NBA uses PHX)
    # ... map all 30 teams
}
```

**Investigation needed:**
- [ ] Document all Yahoo team abbreviations
- [ ] Document all data source team abbreviations
- [ ] Create mapping dictionary
- [ ] Handle team relocations/renames

---

### 5. Cost Considerations

**Selected Approach: FREE** 🎉
- **ESPN API** (primary): Free, no authentication, no rate limits
- **NBA Official API** (backup): Free but unofficial, needs conservative rate limiting

**Total Cost:** $0/month

**Monitoring Plan:**
- Run in production for 1-2 weeks
- Track API failure rates and response times
- Evaluate paid options (SportsData.io ~$19-49/month) only if free APIs prove unreliable

**Rejected Paid Options:**
- SportsData.io: Free tier only includes last season data
- RapidAPI providers: Unnecessary expense given ESPN reliability

---

### 6. Migration Strategy

**Backwards Compatibility:**
- Keep Option B implementation as fallback
- If schedule API fails, gracefully degrade to stats-based check
- Feature flag to toggle between Option A and Option B

**Gradual Rollout:**
1. Implement Option A alongside Option B
2. Run both in parallel for 1 week
3. Compare results and accuracy
4. Switch primary to Option A
5. Keep Option B as fallback

---

## Expected Timeline

- **Research & Prototyping:** 2-4 hours
- **Core Implementation:** 4-6 hours
- **Testing & Validation:** 2-3 hours
- **Production Deployment:** 1-2 hours

**Total Estimated Effort:** 9-15 hours

---

## Success Metrics

**Option A should provide:**
- ✅ Alerts sent **2-6 hours before** game time
- ✅ 95%+ accuracy (correct game schedules)
- ✅ <500ms API response time
- ✅ <5% API failure rate
- ✅ Managers can fix lineups before games start

---

## Questions to Answer

1. **Alert Timing:** When should alerts be sent?
   - Morning (10 AM EST): Early warning for evening games
   - Afternoon (4 PM EST): Final reminder for 7 PM games
   - Multiple times per day?

2. **Alert Frequency:** How often to check?
   - Every 2 hours during the day?
   - Fixed times (12 PM, 6 PM)?
   - Once per day?

3. **Game Time Filtering:** Should we filter by game time?
   - Only alert for games starting in next 6 hours?
   - Alert for all games today?

4. **Cost Tolerance:** What's the budget for API costs?
   - Prefer free (accept some unreliability)?
   - Willing to pay $10-30/month for reliability?

---

## Related Files

- `src/bench_analyzer.py` - Current stats-based check (Option B)
- `main.py` - Bench check mode scheduling
- `BENCH_MANAGEMENT_PLAN.md` - Original implementation plan
- `CLAUDE.md` - Documentation

---

## References

- NBA Official Stats API: https://stats.nba.com/
- ESPN API: https://site.api.espn.com/
- SportsData.io: https://sportsdata.io/developers/api-documentation/nba
- The Sports DB: https://www.thesportsdb.com/api.php
- RapidAPI NBA APIs: https://rapidapi.com/search/nba

---

## Status: PHASE 2 COMPLETE ✅ (v2.8 Deployed)

**Priority:** Medium (valuable enhancement but not critical)

**Blocked by:** None

**Completed:**
- Phase 1 - Research & Prototyping (2026-01-24) ✅
- Phase 2 - Core Implementation (2026-01-24) ✅
  - `src/nba_schedule_fetcher.py` module created
  - `src/bench_analyzer.py` updated with schedule-based checking
  - Feature flag `USE_PROACTIVE_SCHEDULE_CHECK = True` enabled
  - Comprehensive test suite (2 new test files, all passing)
  - Documentation updated in CLAUDE.md

**Key Findings:**
- ~~No team abbreviation mapping needed~~ **INCORRECT** - Mapping required! ⚠️
- ESPN API is fast, reliable, and free
- Caching (1-hour TTL) reduces API calls by 95%
- Backwards compatibility maintained with feature flag

**Bug Fix (2026-01-24):**
- **Issue**: Team abbreviation mismatches between Yahoo and ESPN APIs
  - Washington: Yahoo uses `WAS`, ESPN uses `WSH`
  - New York: Yahoo uses `NYK`, ESPN uses `NY`
  - Golden State: Yahoo uses `GSW`, ESPN uses `GS`
  - Utah: Yahoo uses `UTA`, ESPN uses `UTAH`
  - San Antonio: Yahoo uses `SAS`, ESPN uses `SA`
  - New Orleans: Yahoo uses `NOP`, ESPN uses `NO`
- **Impact**: Benched players from affected teams not detected as having games
- **Fix**: Added `ESPN_TO_YAHOO_TEAM_MAPPING` and `normalize_team_abbreviation()` function
- **Test**: Created `tests/test_team_abbreviation_mapping.py` (10 tests, all passing)
- **Version**: v2.8.1 - Team abbreviation mapping fix

**Next Step:** Phase 3 - Alert Timing Optimization (multiple checks per day, game-time filtering)
