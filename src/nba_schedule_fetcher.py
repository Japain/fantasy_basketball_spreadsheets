"""NBA schedule fetcher using ESPN API with fallback to NBA Official API.

This module provides schedule-based game checking for proactive bench alerts.
Instead of checking if a player recorded stats (retroactive), it checks if
a player's team has a scheduled game (proactive).

Features:
- ESPN API as primary source (free, no auth required)
- In-memory caching with 1-hour TTL
- NBA Official API fallback
- Exponential backoff retry logic
- Conservative error handling (returns empty set on failure)
"""

import time
import random
from datetime import datetime, timedelta
from typing import Set, Dict, Tuple, Optional
import requests

from src.logger import get_logger

logger = get_logger(__name__)

# Cache for schedule data: {date_str: (teams_set, timestamp)}
_schedule_cache: Dict[str, Tuple[Set[str], datetime]] = {}

# Cache time-to-live: 1 hour
CACHE_TTL_SECONDS = 3600

# ESPN API configuration
ESPN_API_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_API_TIMEOUT = 10  # seconds

# NBA Official API configuration (fallback)
NBA_API_BASE_URL = "https://stats.nba.com/stats/scoreboardv2"
NBA_API_TIMEOUT = 10  # seconds
NBA_API_DELAY = 2  # Conservative rate limiting

# Team abbreviation mapping: Yahoo API -> ESPN API
# Yahoo and ESPN use different abbreviations for some teams
# This mapping normalizes ESPN abbreviations to match Yahoo's format
ESPN_TO_YAHOO_TEAM_MAPPING = {
    'WSH': 'WAS',  # Washington Wizards
    'NY': 'NYK',   # New York Knicks
    'GS': 'GSW',   # Golden State Warriors
    'SA': 'SAS',   # San Antonio Spurs
    'NO': 'NOP',   # New Orleans Pelicans
    'UTAH': 'UTA', # Utah Jazz
}

def normalize_team_abbreviation(espn_abbr: str) -> str:
    """
    Normalize ESPN team abbreviation to Yahoo format.

    Args:
        espn_abbr: Team abbreviation from ESPN API

    Returns:
        Team abbreviation in Yahoo format
    """
    return ESPN_TO_YAHOO_TEAM_MAPPING.get(espn_abbr, espn_abbr)


def get_teams_with_games_today(date: str, use_cache: bool = True) -> Set[str]:
    """
    Get set of NBA team abbreviations with games on the specified date.

    This is the primary function for checking if a team has a scheduled game.
    Uses ESPN API as primary source with caching and fallback to NBA API.

    Args:
        date: Date in YYYY-MM-DD format (e.g., "2026-01-24")
        use_cache: Whether to use cached results (default: True)

    Returns:
        Set of team abbreviations (e.g., {"PHX", "LAL", "GSW"})
        Returns empty set if both APIs fail (conservative approach)

    Examples:
        >>> teams = get_teams_with_games_today("2026-01-24")
        >>> "PHX" in teams
        True
        >>> teams = get_teams_with_games_today("2026-06-01")  # Off-season
        >>> len(teams)
        0
    """
    # Check cache first
    if use_cache and date in _schedule_cache:
        cached_teams, cached_timestamp = _schedule_cache[date]
        if _is_cache_valid(cached_timestamp):
            logger.debug(f"Cache hit for {date}: {len(cached_teams)} teams with games")
            return cached_teams
        else:
            logger.debug(f"Cache expired for {date}")

    # Try ESPN API first
    try:
        teams = _fetch_from_espn(date)
        if teams:
            logger.info(f"ESPN API: Found {len(teams)} teams with games on {date}")
            _schedule_cache[date] = (teams, datetime.now())
            return teams
    except Exception as e:
        logger.warning(f"ESPN API failed: {e}")

    # Fallback to NBA Official API
    try:
        logger.info("Attempting NBA Official API fallback...")
        teams = _fetch_from_nba_official(date)
        if teams:
            logger.info(f"NBA API: Found {len(teams)} teams with games on {date}")
            _schedule_cache[date] = (teams, datetime.now())
            return teams
    except Exception as e:
        logger.warning(f"NBA Official API failed: {e}")

    # Both APIs failed - return empty set (conservative)
    logger.error(f"Both APIs failed for {date}. Returning empty set (no games assumed)")
    return set()


def _fetch_from_espn(date: str) -> Set[str]:
    """
    Fetch game schedule from ESPN API.

    Args:
        date: Date in YYYY-MM-DD format (e.g., "2026-01-24")

    Returns:
        Set of team abbreviations with games on this date

    Raises:
        Exception: If API call fails after retries

    ESPN API Response Structure:
        {
          "events": [
            {
              "competitions": [
                {
                  "competitors": [
                    {"team": {"abbreviation": "PHX", "displayName": "Phoenix Suns"}},
                    {"team": {"abbreviation": "LAL", "displayName": "Los Angeles Lakers"}}
                  ]
                }
              ]
            }
          ]
        }
    """
    # Convert YYYY-MM-DD to YYYYMMDD for ESPN API
    # Example: "2026-01-24" -> "20260124"
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    espn_date = date_obj.strftime("%Y%m%d")

    url = f"{ESPN_API_BASE_URL}?dates={espn_date}"

    # Retry with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.debug(f"ESPN API request (attempt {attempt + 1}/{max_retries}): {url}")
            response = requests.get(url, timeout=ESPN_API_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            # Parse events and extract team abbreviations
            teams = set()
            events = data.get("events", [])

            for event in events:
                competitions = event.get("competitions", [])
                for competition in competitions:
                    competitors = competition.get("competitors", [])
                    for competitor in competitors:
                        team = competitor.get("team", {})
                        team_abbr = team.get("abbreviation")
                        if team_abbr:
                            # Normalize ESPN abbreviation to Yahoo format
                            normalized_abbr = normalize_team_abbreviation(team_abbr)
                            teams.add(normalized_abbr)

            logger.debug(f"ESPN API parsed {len(teams)} teams: {sorted(teams)}")
            return teams

        except requests.exceptions.Timeout:
            logger.warning(f"ESPN API timeout (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.HTTPError as e:
            logger.warning(f"ESPN API HTTP error {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"ESPN API request failed: {e} (attempt {attempt + 1}/{max_retries})")
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"ESPN API response parsing failed: {e}")
            raise

        # Exponential backoff before retry
        if attempt < max_retries - 1:
            wait_time = min(2 ** attempt + random.uniform(0, 1), 8.0)
            logger.debug(f"Waiting {wait_time:.2f}s before retry...")
            time.sleep(wait_time)

    raise Exception(f"ESPN API failed after {max_retries} attempts")


def _fetch_from_nba_official(date: str) -> Set[str]:
    """
    Fetch game schedule from NBA Official API (fallback).

    IMPORTANT: This is an unofficial API and should only be used as fallback.
    Uses conservative rate limiting (2-second delay) to avoid IP bans.

    Args:
        date: Date in YYYY-MM-DD format (e.g., "2026-01-24")

    Returns:
        Set of team abbreviations with games on this date

    Raises:
        Exception: If API call fails after retries

    NBA API Response Structure (simplified):
        {
          "resultSets": [
            {
              "name": "GameHeader",
              "rowSet": [
                ["game_id", "date", ..., "HOME_TEAM_ID", "VISITOR_TEAM_ID", ...]
              ]
            }
          ]
        }
    """
    # Add conservative delay before calling unofficial API
    time.sleep(NBA_API_DELAY)

    # Convert date format for NBA API
    # NBA API expects MM/DD/YYYY format
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    nba_date = date_obj.strftime("%m/%d/%Y")

    params = {
        "GameDate": nba_date,
        "LeagueID": "00",  # NBA
        "DayOffset": "0"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.nba.com/",
        "Origin": "https://www.nba.com"
    }

    # Retry with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.debug(f"NBA API request (attempt {attempt + 1}/{max_retries}): {NBA_API_BASE_URL}")
            response = requests.get(
                NBA_API_BASE_URL,
                params=params,
                headers=headers,
                timeout=NBA_API_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Parse response
            # Note: NBA API returns team IDs, not abbreviations
            # We'll need to extract team info from the response
            teams = set()
            result_sets = data.get("resultSets", [])

            for result_set in result_sets:
                if result_set.get("name") == "GameHeader":
                    rows = result_set.get("rowSet", [])
                    headers_list = result_set.get("headers", [])

                    # Find indices for home and visitor team abbreviations
                    # This is a simplified approach - in production, you'd want
                    # to map team IDs to abbreviations
                    for row in rows:
                        # NBA API structure varies - this is a placeholder
                        # You may need to adjust based on actual response
                        logger.warning("NBA API fallback needs team abbreviation mapping")

            logger.debug(f"NBA API parsed {len(teams)} teams: {sorted(teams)}")
            return teams

        except requests.exceptions.Timeout:
            logger.warning(f"NBA API timeout (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.HTTPError as e:
            logger.warning(f"NBA API HTTP error {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"NBA API request failed: {e} (attempt {attempt + 1}/{max_retries})")
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"NBA API response parsing failed: {e}")
            raise

        # Exponential backoff before retry
        if attempt < max_retries - 1:
            wait_time = min(2 ** attempt + random.uniform(0, 1), 8.0)
            logger.debug(f"Waiting {wait_time:.2f}s before retry...")
            time.sleep(wait_time)

    raise Exception(f"NBA API failed after {max_retries} attempts")


def _is_cache_valid(cached_timestamp: datetime) -> bool:
    """
    Check if cache entry is still valid based on TTL.

    Args:
        cached_timestamp: Timestamp when cache entry was created

    Returns:
        True if cache is still valid, False if expired
    """
    elapsed = (datetime.now() - cached_timestamp).total_seconds()
    return elapsed < CACHE_TTL_SECONDS


def clear_schedule_cache() -> None:
    """
    Clear all cached schedule data.

    Useful for testing or forcing fresh API calls.
    """
    global _schedule_cache
    _schedule_cache.clear()
    logger.debug("Schedule cache cleared")


def get_cache_stats() -> Dict[str, any]:
    """
    Get statistics about the schedule cache.

    Returns:
        Dictionary with cache statistics:
        - size: Number of cached dates
        - dates: List of cached dates
        - oldest: Timestamp of oldest entry
        - newest: Timestamp of newest entry
    """
    if not _schedule_cache:
        return {
            "size": 0,
            "dates": [],
            "oldest": None,
            "newest": None
        }

    timestamps = [ts for _, ts in _schedule_cache.values()]
    return {
        "size": len(_schedule_cache),
        "dates": sorted(_schedule_cache.keys()),
        "oldest": min(timestamps) if timestamps else None,
        "newest": max(timestamps) if timestamps else None
    }
