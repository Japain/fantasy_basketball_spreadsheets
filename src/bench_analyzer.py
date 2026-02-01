"""
Bench Management Analyzer Module

Analyzes team rosters to identify teams that have healthy players with
scheduled games currently on the bench. Used for proactive automated alerts
to help managers optimize their lineup decisions.

CURRENT IMPLEMENTATION (v2.8 - Option A):
- Proactive analysis based on NBA game schedules
- Detects violations BEFORE games start
- Uses ESPN API to check if player's team has scheduled game
- Can run multiple times per day for early alerts

FEATURES:
- Schedule-based checking (not stats-based)
- Proactive alerts 2-6 hours before games
- 95% fewer API calls (caching + single schedule fetch)
- Fallback to NBA Official API if ESPN fails
- Rollback option via USE_PROACTIVE_SCHEDULE_CHECK flag

LEGACY IMPLEMENTATION (v2.7.1 - Option B):
- Retroactive analysis based on player stats
- Available via check_player_had_game_today_legacy()
- Set USE_PROACTIVE_SCHEDULE_CHECK = False to rollback
"""

from typing import List, Optional, Dict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.logger import get_logger
from src.data_models import League, Player
from src.yahoo_data_fetcher import YahooDataFetcher
from src.nba_schedule_fetcher import get_teams_with_games_today

logger = get_logger(__name__)

# Feature flag: Set to False to rollback to legacy stats-based checking
USE_PROACTIVE_SCHEDULE_CHECK = True


# Injury status codes that indicate a player should NOT be counted as "healthy"
INJURED_STATUS_CODES = {
    'INJ',      # Injured
    'OUT',      # Out
    'DTD',      # Day-to-day (questionable)
    'GTD',      # Game-time decision
    'NA',       # Not active
    'O',        # Out (short form)
    'SUSP',     # Suspended
}

# Roster positions that indicate a player is benched
BENCH_POSITIONS = {
    'BN',       # Bench
}

# Roster positions for injured players (should be excluded)
IL_POSITIONS = {
    'IL',       # Injured List
    'IL+',      # Injured List Plus
}


def _is_player_healthy(player: Player) -> bool:
    """
    Check if a player is considered healthy (not injured/out).

    Args:
        player: Player object with status fields

    Returns:
        True if player is healthy, False if injured/out/questionable
    """
    # If no status field or status is None, player is healthy
    if not player.status:
        return True

    # Check if status code indicates injury
    return player.status.upper() not in INJURED_STATUS_CODES


def _is_benched(player: Player) -> bool:
    """
    Check if a player is on the bench (not in an active lineup slot).

    Args:
        player: Player object with roster_position

    Returns:
        True if player is benched, False if in active lineup
    """
    if not player.roster_position:
        return False

    return player.roster_position in BENCH_POSITIONS


def _is_on_il(player: Player) -> bool:
    """
    Check if a player is on IL/IL+ (injured list).

    Args:
        player: Player object with roster_position

    Returns:
        True if player is on IL/IL+, False otherwise
    """
    if not player.roster_position:
        return False

    return player.roster_position in IL_POSITIONS


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


def _count_active_spots_without_games(roster: List[Player], check_date: str) -> int:
    """
    Count the number of active roster spots that DON'T have games scheduled today.

    This includes:
    - Active players whose teams don't have games today
    - Empty active roster spots (if roster < 10 active players)

    Args:
        roster: List of players on a team's roster
        check_date: Date to check in YYYY-MM-DD format

    Returns:
        Number of active roster spots without games (available for swaps)
    """
    active_count = 0
    active_with_games = 0

    for player in roster:
        if not player.roster_position:
            continue

        # Skip bench positions
        if player.roster_position in BENCH_POSITIONS:
            continue

        # Skip injured list positions
        if player.roster_position in IL_POSITIONS:
            continue

        # This player is in an active position
        active_count += 1

        # Check if this active player has a game today
        if USE_PROACTIVE_SCHEDULE_CHECK:
            has_game = check_player_has_game_scheduled(player, check_date)
        else:
            # For legacy mode, we can't easily check without fetcher
            # Just count all active players as having games (conservative)
            has_game = True

        if has_game:
            active_with_games += 1

    # Total spots without games = (10 total active spots) - (spots with games)
    # This includes both filled spots without games AND empty spots
    spots_without_games = 10 - active_with_games

    return spots_without_games


def check_player_has_game_scheduled(
    player: Player,
    check_date: str
) -> bool:
    """
    Check if a player's team has a scheduled game on a specific date.

    NEW IMPLEMENTATION (v2.8 - Option A - Proactive):
    - Uses ESPN API to fetch NBA game schedules
    - Checks if player's NBA team has a game scheduled
    - Enables proactive alerts BEFORE games start
    - 95% fewer API calls (caching + single schedule fetch)

    ADVANTAGES over legacy approach:
    - Can detect violations hours before games start
    - Single API call for all players (vs one call per player)
    - Zero Yahoo API quota usage for game checking
    - Works even if player DNP'd (team schedule matters, not player stats)

    Args:
        player: Player object with nba_team field
        check_date: Date string in YYYY-MM-DD format (e.g., "2026-01-24")

    Returns:
        True if player's team has a scheduled game that day, False otherwise

    Note:
        - Returns False if player has no nba_team (free agent)
        - Returns False if API call fails (graceful degradation)
        - Uses cached schedule data (1-hour TTL)
        - Fallback to NBA Official API if ESPN fails
    """
    # Check if player has an NBA team
    if not player.nba_team:
        logger.debug(f"Player {player.name} has no NBA team (free agent?)")
        return False

    try:
        # Get teams with games on this date (cached)
        teams_with_games = get_teams_with_games_today(check_date)

        # Check if player's team has a game
        has_game = player.nba_team in teams_with_games

        if has_game:
            logger.debug(f"Player {player.name} ({player.nba_team}) has game on {check_date}")
        else:
            logger.debug(f"Player {player.name} ({player.nba_team}) has NO game on {check_date}")

        return has_game

    except Exception as e:
        logger.warning(f"Failed to check schedule for {player.name} ({player.nba_team}): {e}")
        # Gracefully degrade - don't count as violation if we can't verify
        return False


def check_player_had_game_today_legacy(
    fetcher: YahooDataFetcher,
    player_key: str,
    check_date: str
) -> bool:
    """
    LEGACY IMPLEMENTATION (v2.7.1 - Option B - Retroactive):
    Check if a player had a game and recorded stats on a specific date.

    This is the old stats-based approach. Use check_player_has_game_scheduled()
    for the new proactive schedule-based approach.

    LIMITATION:
    - Cannot detect violations before/during games
    - Requires one Yahoo API call per benched player (~10-30 calls)
    - If player DNP'd, returns False even if team had a game
    - Only useful for post-game analysis

    ROLLBACK:
    Set USE_PROACTIVE_SCHEDULE_CHECK = False to use this function.

    Args:
        fetcher: YahooDataFetcher instance
        player_key: Yahoo player key (e.g., "466.p.6022")
        check_date: Date string in YYYY-MM-DD format (e.g., "2026-01-24")

    Returns:
        True if player recorded non-zero stats that day, False otherwise

    Note:
        - Returns False if API call fails (graceful degradation)
        - Checks for non-zero stat values to verify actual game
        - Returns False if player DNP'd even if team had a game
    """
    try:
        logger.debug(f"Checking game for {player_key} on {check_date}")

        # Get player stats for the specific date
        player_data = fetcher.yahoo_query.get_player_stats_by_date(
            player_key,
            chosen_date=check_date
        )

        # Check if player has stats for this date
        if hasattr(player_data, 'player_stats'):
            player_stats = player_data.player_stats

            # Check if stats object has actual stat data
            if player_stats and hasattr(player_stats, 'stats'):
                stats = player_stats.stats

                # Yahoo API returns stats array even when no game (all zeros)
                # We need to check if any stat has a non-zero value
                if stats and len(stats) > 0:
                    for stat in stats:
                        if hasattr(stat, 'stat') and hasattr(stat.stat, 'value'):
                            value = stat.stat.value
                            # Check for non-zero value (could be int or float)
                            try:
                                if float(value) != 0.0:
                                    logger.debug(f"Player {player_key} had game on {check_date} (non-zero stat found)")
                                    return True
                            except (ValueError, TypeError):
                                # Skip stats we can't convert to float
                                continue

                    # All stats are zero - no game played
                    logger.debug(f"Player {player_key} had NO game on {check_date} (all stats are zero)")
                    return False

        logger.debug(f"Player {player_key} had NO game on {check_date} (no stats data)")
        return False

    except Exception as e:
        logger.warning(f"Failed to check game for {player_key} on {check_date}: {e}")
        # Gracefully degrade - don't count as violation if we can't verify
        return False


def analyze_bench_violations(
    league: League,
    fetcher: YahooDataFetcher,
    check_date: Optional[str] = None
) -> Dict[str, List[Dict[str, str]]]:
    """
    Analyze all teams to find bench management violations.

    A violation occurs when:
    1. Player is currently on bench (BN position)
    2. Player is currently healthy (no INJ/OUT/DTD/GTD status)
    3. Player is NOT on IL/IL+ (injured list)
    4. Player had a scheduled game today
    5. Team has active roster spots that could be better utilized:
       - Either empty active spots (roster < 10 active players)
       - OR active players whose teams don't have games today

    Optimal lineup logic:
    - If all 10 active roster spots are filled with players who have games today,
      then benched players are NOT flagged (lineup is optimally filled)
    - If any active spot is empty OR has a player without a game, and there's
      a benched healthy player with a game, that's a violation (suboptimal lineup)

    Example violation:
    - Active: Player A (no game today)
    - Bench: Player B (has game today, healthy)
    - Action: Should swap A and B to optimize lineup

    Note: Should be run late at night (1-2 AM EST) after all games complete
          but before managers wake up to fix lineups.

    Args:
        league: League object with current team/roster data
        fetcher: YahooDataFetcher for API calls
        check_date: Date to check (YYYY-MM-DD). If None, uses today's date.

    Returns:
        Dictionary mapping team_name to list of violations:
        {
            "Team Name": [
                {
                    'player_name': 'Player Name',
                    'nba_team': 'LAL',
                    'position': 'PG,SG'
                },
                ...
            ],
            ...
        }
    """
    logger.info("Starting bench management violation analysis...")

    # Use today's date if not provided (Pacific timezone to avoid rollover issues)
    # Running late at night after games finish (e.g., 1 AM EST = 10 PM PST)
    # ensures we check the correct game day
    if not check_date:
        pacific_tz = ZoneInfo("America/Los_Angeles")
        today = datetime.now(pacific_tz)
        check_date = today.strftime('%Y-%m-%d')

    logger.info(f"Analyzing for date: {check_date}")

    violations_by_team: Dict[str, List[Dict[str, str]]] = {}

    for team in league.teams:
        logger.info(f"Analyzing team: {team.team_name}")

        team_violations = []

        # Count how many active roster spots don't have games today
        # This includes both:
        # 1. Active players whose teams don't have games today
        # 2. Empty active roster spots (if roster < 10 active players)
        spots_without_games = _count_active_spots_without_games(team.roster, check_date)
        logger.info(f"  Active roster spots without games today: {spots_without_games}/10")

        # If all 10 active spots have games today, benched players are acceptable
        # (lineup is optimally filled - no room to improve by swapping)
        if spots_without_games == 0:
            logger.info(f"  All active spots optimally filled (all have games) - skipping bench violation check")
            continue

        # There are active spots that could be better utilized (either empty or
        # filled with players who don't have games). Check for benched players
        # who have games and could fill these spots.
        logger.info(f"  Found {spots_without_games} active spot(s) that could be optimized")

        # Check each current player
        for player in team.roster:
            # Check condition 1: Is player currently benched?
            is_benched = _is_benched(player)
            if not is_benched:
                continue  # Player is in active lineup, no violation

            # Check condition 2a: Is player on IL/IL+?
            is_on_il = _is_on_il(player)
            if is_on_il:
                continue  # Player is on IL, no violation

            # Check condition 2b: Is player currently healthy?
            is_healthy = _is_player_healthy(player)
            if not is_healthy:
                continue  # Player is injured, no violation

            # Check condition 3: Did player have a game today?
            if USE_PROACTIVE_SCHEDULE_CHECK:
                # NEW: Schedule-based checking (proactive)
                has_game = check_player_has_game_scheduled(player, check_date)
            else:
                # LEGACY: Stats-based checking (retroactive)
                has_game = check_player_had_game_today_legacy(
                    fetcher,
                    player.player_key,
                    check_date
                )

            if not has_game:
                continue  # No game scheduled, no violation

            # All conditions met - this is a violation!
            violation = {
                'player_name': player.name,
                'nba_team': player.nba_team or "UNK",
                'position': player.position
            }

            team_violations.append(violation)
            logger.info(
                f"  VIOLATION: {player.name} ({player.nba_team}) is benched "
                f"but had a game on {check_date}"
            )

        # Add to results if team has violations
        if team_violations:
            violations_by_team[team.team_name] = team_violations

    logger.info(
        f"Analysis complete: {len(violations_by_team)} team(s) with violations, "
        f"{sum(len(v) for v in violations_by_team.values())} total violations"
    )

    return violations_by_team


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
            violations[team.team_name] = team_violations

    return violations


def get_teams_with_bench_violations(
    violations_by_team: Dict[str, List[Dict[str, str]]]
) -> List[str]:
    """
    Extract simple list of team names with violations.

    Args:
        violations_by_team: Dictionary mapping team names to violations

    Returns:
        Sorted list of team names that have violations
    """
    return sorted(violations_by_team.keys())
