"""
Bench Management Analyzer Module

Analyzes team rosters to identify teams that have healthy players with
scheduled games currently on the bench. Used for same-day automated alerts
to help managers optimize their lineup decisions.

CURRENT IMPLEMENTATION (v2.7.1 - Option B):
- Retroactive analysis based on player stats
- Detects violations AFTER games complete
- Run at 1-2 AM EST after all games finish
- Checks if players recorded non-zero stats (actually played)

LIMITATION:
- Cannot alert managers BEFORE games to fix lineups
- Only useful for post-game analysis

TODO: See TODO_PROACTIVE_BENCH_ALERTS.md for future enhancement (Option A)
- Proactive alerts using NBA team schedule API
- Real-time detection before/during games
- Allow managers to fix lineups in time
"""

from typing import List, Optional, Dict
from datetime import datetime, timezone

from src.logger import get_logger
from src.data_models import League, Player
from src.yahoo_data_fetcher import YahooDataFetcher

logger = get_logger(__name__)


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


def check_player_had_game_today(
    fetcher: YahooDataFetcher,
    player_key: str,
    check_date: str
) -> bool:
    """
    Check if a player had a game and recorded stats on a specific date.

    CURRENT IMPLEMENTATION (Option B - Retroactive):
    - Uses player stats to determine if they played
    - Requires non-zero stat values (player actually played)
    - Can only detect violations AFTER games complete
    - Useful for post-game analysis

    LIMITATION:
    - Cannot detect violations before/during games
    - If player's team had a game but player DNP'd, returns False
    - Not suitable for real-time proactive alerts

    TODO: Investigate Option A (Proactive Alerts)
    - Use NBA team schedule API instead of player stats
    - Detect violations before games start
    - Enable real-time alerts for managers to fix lineups
    - See TODO_PROACTIVE_BENCH_ALERTS.md for details

    Args:
        fetcher: YahooDataFetcher instance
        player_key: Yahoo player key (e.g., "466.p.6022")
        check_date: Date string in YYYY-MM-DD format (e.g., "2026-01-24")

    Returns:
        True if player recorded non-zero stats that day, False otherwise

    Note:
        - Returns False if API call fails (graceful degradation)
        - Checks for non-zero stat values to verify actual game (not just placeholder stats)
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
    3. Player had a scheduled game today

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

    # Use today's date if not provided
    if not check_date:
        today = datetime.now(timezone.utc)
        check_date = today.strftime('%Y-%m-%d')

    logger.info(f"Analyzing for date: {check_date}")

    violations_by_team: Dict[str, List[Dict[str, str]]] = {}

    for team in league.teams:
        logger.info(f"Analyzing team: {team.team_name}")

        team_violations = []

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
            had_game = check_player_had_game_today(
                fetcher,
                player.player_key,
                check_date
            )

            if not had_game:
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
