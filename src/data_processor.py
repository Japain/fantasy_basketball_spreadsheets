"""
Data processing and validation utilities.

Provides functions for validating, sorting, filtering, and transforming
fantasy basketball league data.
"""

from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from src.data_models import League, Team, Player, SalarySource
from src.logger import logger


class SortOrder(Enum):
    """Enum for sort order."""
    ASCENDING = "asc"
    DESCENDING = "desc"


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


# ==============================================================================
# VALIDATION FUNCTIONS
# ==============================================================================

def validate_league_data(league: League, strict: bool = True) -> Dict[str, Any]:
    """
    Validate complete league data structure.

    Args:
        league: League object to validate
        strict: If True, raises ValidationError on critical issues.
                If False, returns validation report without raising.

    Returns:
        Dictionary containing validation results and any issues found

    Raises:
        ValidationError: If strict=True and critical validation issues found
    """
    logger.info(f"Validating league data for: {league.league_name}")

    issues = []
    warnings = []

    # Check league has teams
    if not league.teams:
        issues.append("League has no teams")
    elif len(league.teams) != league.num_teams:
        warnings.append(
            f"Team count mismatch: expected {league.num_teams}, found {len(league.teams)}"
        )

    # Validate each team
    for team in league.teams:
        team_issues = validate_team_data(team, strict=False)
        if team_issues['errors']:
            issues.extend([f"Team {team.team_name}: {err}" for err in team_issues['errors']])
        if team_issues['warnings']:
            warnings.extend([f"Team {team.team_name}: {warn}" for warn in team_issues['warnings']])

    # Check for duplicate team IDs
    team_ids = [team.team_id for team in league.teams]
    if len(team_ids) != len(set(team_ids)):
        issues.append("Duplicate team IDs found")

    # Log validation results
    if issues:
        logger.warning(f"Validation found {len(issues)} issue(s)")
        for issue in issues:
            logger.warning(f"  - {issue}")

    if warnings:
        logger.info(f"Validation found {len(warnings)} warning(s)")
        for warning in warnings:
            logger.debug(f"  - {warning}")

    if not issues and not warnings:
        logger.info("✓ League data validation passed with no issues")

    validation_result = {
        'valid': len(issues) == 0,
        'errors': issues,
        'warnings': warnings,
        'num_teams': len(league.teams),
        'total_players': league.get_total_players(),
        'stats': league.get_league_stats()
    }

    # Raise exception if strict mode and issues found
    if strict and issues:
        error_msg = f"League validation failed with {len(issues)} error(s): {'; '.join(issues)}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    return validation_result


def validate_team_data(team: Team, strict: bool = True) -> Dict[str, Any]:
    """
    Validate team data structure.

    Args:
        team: Team object to validate
        strict: If True, raises ValidationError on critical issues

    Returns:
        Dictionary containing validation results

    Raises:
        ValidationError: If strict=True and critical validation issues found
    """
    errors = []
    warnings = []

    # Check team has roster
    if not team.roster:
        warnings.append("Team has empty roster")

    # Validate each player
    for player in team.roster:
        player_issues = validate_player_data(player, strict=False)
        if player_issues['errors']:
            errors.extend([f"Player {player.name}: {err}" for err in player_issues['errors']])

    # Check salary calculations
    calculated_total = team.calculate_total_salary()
    if calculated_total != team.total_salary:
        errors.append(
            f"Total salary mismatch: stored={team.total_salary}, calculated={calculated_total}"
        )

    # Check for duplicate player keys
    player_keys = [player.player_key for player in team.roster]
    if len(player_keys) != len(set(player_keys)):
        errors.append("Duplicate players found on roster")

    # Check FAAB balance is reasonable
    if team.faab_remaining < 0:
        errors.append(f"Negative FAAB balance: {team.faab_remaining}")

    validation_result = {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'roster_size': len(team.roster),
        'total_salary': team.total_salary,
        'faab_remaining': team.faab_remaining
    }

    if strict and errors:
        error_msg = f"Team validation failed: {'; '.join(errors)}"
        raise ValidationError(error_msg)

    return validation_result


def validate_player_data(player: Player, strict: bool = True) -> Dict[str, Any]:
    """
    Validate player data structure.

    Args:
        player: Player object to validate
        strict: If True, raises ValidationError on critical issues

    Returns:
        Dictionary containing validation results

    Raises:
        ValidationError: If strict=True and critical validation issues found
    """
    errors = []
    warnings = []

    # Check required fields
    if not player.player_key:
        errors.append("Missing player_key")

    if not player.name or player.name == "Unknown":
        warnings.append("Player has no name or name is 'Unknown'")

    if not player.position or player.position == "N/A":
        warnings.append("Player has no position or position is 'N/A'")

    # Check salary is valid
    if player.salary < 0:
        errors.append(f"Negative salary: {player.salary}")

    if not isinstance(player.salary, int):
        errors.append(f"Salary is not an integer: {type(player.salary)}")

    # Check source is valid
    if not isinstance(player.source, SalarySource):
        errors.append(f"Invalid salary source type: {type(player.source)}")

    validation_result = {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }

    if strict and errors:
        error_msg = f"Player validation failed: {'; '.join(errors)}"
        raise ValidationError(error_msg)

    return validation_result


# ==============================================================================
# SORTING FUNCTIONS
# ==============================================================================

def sort_teams(
    teams: List[Team],
    by: str = "name",
    order: SortOrder = SortOrder.ASCENDING
) -> List[Team]:
    """
    Sort teams by specified criteria.

    Args:
        teams: List of Team objects to sort
        by: Sort criteria - "name", "manager", "salary", "faab", or "roster_size"
        order: Sort order (ASCENDING or DESCENDING)

    Returns:
        Sorted list of teams
    """
    logger.debug(f"Sorting {len(teams)} teams by {by} ({order.value})")

    reverse = (order == SortOrder.DESCENDING)

    sort_keys = {
        'name': lambda t: t.team_name.lower(),
        'manager': lambda t: t.manager_name.lower(),
        'salary': lambda t: t.total_salary,
        'faab': lambda t: t.faab_remaining,
        'roster_size': lambda t: len(t.roster)
    }

    if by not in sort_keys:
        logger.warning(f"Unknown sort key '{by}', defaulting to 'name'")
        by = 'name'

    return sorted(teams, key=sort_keys[by], reverse=reverse)


def sort_players(
    players: List[Player],
    by: str = "name",
    order: SortOrder = SortOrder.ASCENDING
) -> List[Player]:
    """
    Sort players by specified criteria.

    Args:
        players: List of Player objects to sort
        by: Sort criteria - "name", "position", "salary", "source", or "nba_team"
        order: Sort order (ASCENDING or DESCENDING)

    Returns:
        Sorted list of players
    """
    logger.debug(f"Sorting {len(players)} players by {by} ({order.value})")

    reverse = (order == SortOrder.DESCENDING)

    sort_keys = {
        'name': lambda p: p.name.lower(),
        'position': lambda p: p.position,
        'salary': lambda p: p.salary,
        'source': lambda p: p.source.value,
        'nba_team': lambda p: p.nba_team or ""
    }

    if by not in sort_keys:
        logger.warning(f"Unknown sort key '{by}', defaulting to 'name'")
        by = 'name'

    return sorted(players, key=sort_keys[by], reverse=reverse)


# ==============================================================================
# FILTERING FUNCTIONS
# ==============================================================================

def filter_teams_by_criteria(
    teams: List[Team],
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
    min_roster_size: Optional[int] = None,
    max_roster_size: Optional[int] = None
) -> List[Team]:
    """
    Filter teams based on various criteria.

    Args:
        teams: List of Team objects to filter
        min_salary: Minimum total salary (inclusive)
        max_salary: Maximum total salary (inclusive)
        min_roster_size: Minimum roster size (inclusive)
        max_roster_size: Maximum roster size (inclusive)

    Returns:
        Filtered list of teams
    """
    filtered = teams

    if min_salary is not None:
        filtered = [t for t in filtered if t.total_salary >= min_salary]

    if max_salary is not None:
        filtered = [t for t in filtered if t.total_salary <= max_salary]

    if min_roster_size is not None:
        filtered = [t for t in filtered if len(t.roster) >= min_roster_size]

    if max_roster_size is not None:
        filtered = [t for t in filtered if len(t.roster) <= max_roster_size]

    logger.debug(f"Filtered teams: {len(teams)} -> {len(filtered)}")
    return filtered


def filter_players_by_source(
    players: List[Player],
    sources: List[SalarySource]
) -> List[Player]:
    """
    Filter players by their acquisition source.

    Args:
        players: List of Player objects to filter
        sources: List of SalarySource values to include

    Returns:
        Filtered list of players
    """
    filtered = [p for p in players if p.source in sources]
    logger.debug(f"Filtered players by source: {len(players)} -> {len(filtered)}")
    return filtered


def filter_players_by_salary_range(
    players: List[Player],
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None
) -> List[Player]:
    """
    Filter players by salary range.

    Args:
        players: List of Player objects to filter
        min_salary: Minimum salary (inclusive)
        max_salary: Maximum salary (inclusive)

    Returns:
        Filtered list of players
    """
    filtered = players

    if min_salary is not None:
        filtered = [p for p in filtered if p.salary >= min_salary]

    if max_salary is not None:
        filtered = [p for p in filtered if p.salary <= max_salary]

    logger.debug(f"Filtered players by salary: {len(players)} -> {len(filtered)}")
    return filtered


# ==============================================================================
# TRANSFORMATION FUNCTIONS
# ==============================================================================

def calculate_team_totals(team: Team) -> Dict[str, Any]:
    """
    Calculate various totals and statistics for a team.

    Args:
        team: Team object

    Returns:
        Dictionary with calculated statistics
    """
    salary_breakdown = team.get_salary_breakdown()

    return {
        'total_salary': team.total_salary,
        'faab_remaining': team.faab_remaining,
        'roster_size': len(team.roster),
        'avg_player_salary': team.total_salary / len(team.roster) if team.roster else 0,
        'salary_by_source': {
            source.value: amount
            for source, amount in salary_breakdown.items()
        },
        'players_by_source': {
            source.value: len([p for p in team.roster if p.source == source])
            for source in SalarySource
        }
    }


def get_league_summary(league: League) -> Dict[str, Any]:
    """
    Generate comprehensive summary statistics for the league.

    Args:
        league: League object

    Returns:
        Dictionary with league summary statistics
    """
    stats = league.get_league_stats()

    # Calculate additional statistics
    all_players = [player for team in league.teams for player in team.roster]

    # Salary statistics
    all_salaries = [p.salary for p in all_players if p.salary > 0]
    salary_stats = {
        'min': min(all_salaries) if all_salaries else 0,
        'max': max(all_salaries) if all_salaries else 0,
        'avg': sum(all_salaries) / len(all_salaries) if all_salaries else 0
    }

    # Players by source
    players_by_source = {}
    for source in SalarySource:
        count = len([p for p in all_players if p.source == source])
        players_by_source[source.value] = count

    # Team salary distribution
    team_salaries = [team.total_salary for team in league.teams]

    return {
        'league_info': {
            'name': league.league_name,
            'season': league.season,
            'num_teams': league.num_teams
        },
        'basic_stats': stats,
        'salary_stats': salary_stats,
        'players_by_source': players_by_source,
        'team_salary_range': {
            'min': min(team_salaries) if team_salaries else 0,
            'max': max(team_salaries) if team_salaries else 0,
            'avg': stats['avg_salary_per_team']
        }
    }


def normalize_player_data(player: Player) -> Dict[str, Any]:
    """
    Normalize player data to a dictionary format.

    Useful for serialization, display, or further processing.

    Args:
        player: Player object

    Returns:
        Dictionary with normalized player data
    """
    return {
        'player_key': player.player_key,
        'name': player.name,
        'position': player.position,
        'salary': player.salary,
        'source': player.source.value,
        'nba_team': player.nba_team or 'N/A'
    }


def normalize_team_data(team: Team) -> Dict[str, Any]:
    """
    Normalize team data to a dictionary format.

    Args:
        team: Team object

    Returns:
        Dictionary with normalized team data
    """
    return {
        'team_id': team.team_id,
        'team_key': team.team_key,
        'team_name': team.team_name,
        'manager_name': team.manager_name,
        'roster': [normalize_player_data(p) for p in team.roster],
        'total_salary': team.total_salary,
        'faab_remaining': team.faab_remaining,
        'roster_size': len(team.roster),
        'stats': calculate_team_totals(team)
    }


def normalize_league_data(league: League) -> Dict[str, Any]:
    """
    Normalize league data to a dictionary format.

    Args:
        league: League object

    Returns:
        Dictionary with normalized league data
    """
    return {
        'league_id': league.league_id,
        'league_key': league.league_key,
        'league_name': league.league_name,
        'season': league.season,
        'num_teams': league.num_teams,
        'teams': [normalize_team_data(t) for t in league.teams],
        'summary': get_league_summary(league)
    }


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def find_team_by_name(league: League, team_name: str) -> Optional[Team]:
    """
    Find a team by name (case-insensitive).

    Args:
        league: League object to search
        team_name: Name of the team to find

    Returns:
        Team object if found, None otherwise
    """
    team_name_lower = team_name.lower()
    for team in league.teams:
        if team.team_name.lower() == team_name_lower:
            return team
    return None


def find_player_by_name(team: Team, player_name: str) -> Optional[Player]:
    """
    Find a player by name (case-insensitive).

    Args:
        team: Team object to search
        player_name: Name of the player to find

    Returns:
        Player object if found, None otherwise
    """
    player_name_lower = player_name.lower()
    for player in team.roster:
        if player.name.lower() == player_name_lower:
            return player
    return None


def get_top_salaries(league: League, n: int = 10) -> List[Dict[str, Any]]:
    """
    Get the top N highest-paid players across the league.

    Args:
        league: League object
        n: Number of top players to return

    Returns:
        List of dictionaries with player info and team name
    """
    all_players = []
    for team in league.teams:
        for player in team.roster:
            all_players.append({
                'player': player,
                'team_name': team.team_name,
                'manager_name': team.manager_name
            })

    # Sort by salary descending
    sorted_players = sorted(all_players, key=lambda x: x['player'].salary, reverse=True)

    # Return top N
    return [
        {
            'name': item['player'].name,
            'position': item['player'].position,
            'salary': item['player'].salary,
            'source': item['player'].source.value,
            'nba_team': item['player'].nba_team,
            'fantasy_team': item['team_name'],
            'manager': item['manager_name']
        }
        for item in sorted_players[:n]
    ]
