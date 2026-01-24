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

## Implementation Requirements

### 1. NBA Team Schedule Data Source

Need a reliable API or data source that provides:
- Daily NBA game schedules
- Team abbreviations matching Yahoo's format (e.g., "PHX", "LAL", "BKN")
- Game times (for optimal alert timing)
- Coverage: Regular season + playoffs

**Potential Data Sources:**

#### Option 1: NBA Official API (stats.nba.com)
- **Pros**: Official, comprehensive, free
- **Cons**: Unofficial/undocumented, rate limits, may break
- **Endpoint**: `https://stats.nba.com/stats/scoreboardv2?GameDate=2026-01-24`
- **Investigation needed**: Test reliability, rate limits, data format

#### Option 2: ESPN API (Unofficial)
- **Pros**: Widely used, stable
- **Cons**: Undocumented, no SLA
- **Endpoint**: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20260124`
- **Investigation needed**: Test endpoint, parse team names

#### Option 3: SportsData.io (Commercial)
- **Pros**: Official API, documented, reliable, SLA
- **Cons**: Costs money (varies by tier)
- **Free tier**: 1,000 API calls/month (may be sufficient)
- **Endpoint**: `/v3/nba/scores/json/GamesByDate/{date}`
- **Investigation needed**: Test free tier limits, pricing

#### Option 4: The Sports DB (Free)
- **Pros**: Free, documented
- **Cons**: Limited NBA coverage, slower updates
- **Endpoint**: `https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=2026-01-24&l=4387`
- **Investigation needed**: Verify NBA coverage

#### Option 5: RapidAPI - NBA API
- **Pros**: Consolidated marketplace, multiple providers
- **Cons**: Costs money, varies by provider
- **Investigation needed**: Compare providers, pricing

#### Option 6: Scrape NBA.com Schedule Page
- **Pros**: Always available, no API limits
- **Cons**: Brittle (HTML changes), slower, less reliable
- **Last resort option**

---

### 2. Implementation Plan

#### Phase 1: Research & Prototyping
- [ ] Test NBA Official API endpoints
- [ ] Test ESPN API endpoints
- [ ] Evaluate SportsData.io free tier
- [ ] Compare data quality and reliability
- [ ] Measure API response times
- [ ] Choose primary data source + backup

#### Phase 2: Core Implementation
- [ ] Create `src/nba_schedule_fetcher.py` module
  - Fetch daily NBA game schedule
  - Parse team abbreviations
  - Cache results (avoid redundant API calls)
  - Handle API failures gracefully
- [ ] Create team abbreviation mapping (Yahoo ↔ Data Source)
  - Yahoo uses specific formats (e.g., "PHO" vs "PHX")
  - Need mapping dictionary for compatibility
- [ ] Update `check_player_has_game_today()` function
  - Replace stats-based check with schedule-based check
  - Look up player's NBA team in today's schedule
  - Return True if team has game, regardless of player stats

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

Fetches daily NBA game schedules from external API to determine
which teams have games scheduled for a given date.
"""

def get_teams_with_games_today(date: str) -> Set[str]:
    """
    Get set of NBA team abbreviations with games scheduled for date.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        Set of team abbreviations (e.g., {"PHX", "LAL", "BKN"})
    """
    pass

def get_game_time(team_abbr: str, date: str) -> Optional[datetime]:
    """
    Get scheduled game time for a specific team on a date.

    Useful for filtering alerts (only alert for upcoming games).
    """
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

**Free Options:**
- NBA Official API: Free but unofficial
- ESPN API: Free but unofficial
- The Sports DB: Free but limited

**Paid Options:**
- SportsData.io: ~$19-49/month depending on tier
- RapidAPI providers: ~$10-30/month

**Recommendation:** Start with free options (NBA/ESPN API), monitor reliability for 1-2 weeks, then evaluate paid options if needed.

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

## Status: TODO (Not Started)

**Priority:** Medium (valuable enhancement but not critical)

**Blocked by:** None (can start investigation anytime)

**Next Step:** Investigate NBA Official API and ESPN API reliability
