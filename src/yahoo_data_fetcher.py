"""
Yahoo Fantasy Sports API data fetcher.

Handles authentication and data retrieval from Yahoo Fantasy Basketball API using yfpy.
"""

from typing import Optional, Any
from pathlib import Path
from yfpy.query import YahooFantasySportsQuery
from config import config, BASE_DIR
from src.logger import logger


class YahooDataFetcher:
    """
    Yahoo Fantasy Sports API data fetcher.

    Handles OAuth authentication and provides methods to retrieve
    league, team, and player data.
    """

    def __init__(
        self,
        league_id: Optional[str] = None,
        game_id: Optional[str] = None,
        browser_callback: bool = True
    ):
        """
        Initialize Yahoo Fantasy Sports API client.

        Args:
            league_id: Yahoo league ID (defaults to NBA_LEAGUE_ID from config)
            game_id: Yahoo game ID (defaults to NBA_GAME_ID from config)
            browser_callback: Whether to use browser-based OAuth callback (default: True)
        """
        self.league_id = league_id or config.NBA_LEAGUE_ID
        self.game_id = game_id or config.NBA_GAME_ID
        self.game_code = config.GAME_CODE

        if not self.league_id:
            raise ValueError("League ID must be provided or set in NBA_LEAGUE_ID config")

        if not config.YAHOO_CONSUMER_KEY or not config.YAHOO_CONSUMER_SECRET:
            raise ValueError(
                "Yahoo API credentials not found. "
                "Please set YAHOO_CONSUMER_KEY and YAHOO_CONSUMER_SECRET in .env"
            )

        # Ensure cache directory exists
        config.ensure_directories()

        logger.info(f"Initializing Yahoo API client for league {self.league_id}")
        logger.debug(f"Game ID: {self.game_id}, Game Code: {self.game_code}")
        logger.debug(f"Cache directory: {config.CACHE_DIR}")

        try:
            # Initialize Yahoo Fantasy Sports Query client
            # Note: yfpy will store token data in the project root or use env_file_location
            self.yahoo_query = YahooFantasySportsQuery(
                league_id=self.league_id,
                game_code=self.game_code,
                game_id=self.game_id,
                yahoo_consumer_key=config.YAHOO_CONSUMER_KEY,
                yahoo_consumer_secret=config.YAHOO_CONSUMER_SECRET,
                browser_callback=browser_callback,
                save_token_data_to_env_file=True,  # Save token for reuse
                env_file_location=BASE_DIR  # Directory where .env file is located
            )
            logger.info("Yahoo API client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Yahoo API client: {e}")
            raise

    def get_league_info(self) -> Any:
        """
        Retrieve league information.

        Returns:
            League information object from Yahoo API
        """
        logger.info("Fetching league information...")
        try:
            league_info = self.yahoo_query.get_league_info()
            logger.info(f"Successfully retrieved league info: {league_info.name if hasattr(league_info, 'name') else 'Unknown'}")
            return league_info
        except Exception as e:
            logger.error(f"Failed to retrieve league info: {e}")
            raise

    def get_league_teams(self) -> Any:
        """
        Retrieve all teams in the league.

        Returns:
            List of team objects from Yahoo API
        """
        logger.info("Fetching league teams...")
        try:
            teams = self.yahoo_query.get_league_teams()
            team_count = len(teams) if hasattr(teams, '__len__') else 'unknown'
            logger.info(f"Successfully retrieved {team_count} teams")
            return teams
        except Exception as e:
            logger.error(f"Failed to retrieve league teams: {e}")
            raise

    def get_team_roster(self, team_id: str, week: Optional[int] = None) -> Any:
        """
        Retrieve roster for a specific team.

        Args:
            team_id: Yahoo team ID
            week: Week number (optional, defaults to current week)

        Returns:
            Team roster object from Yahoo API
        """
        logger.info(f"Fetching roster for team {team_id}" + (f" week {week}" if week else ""))
        try:
            if week:
                roster = self.yahoo_query.get_team_roster_by_week(team_id, week)
            else:
                roster = self.yahoo_query.get_team_roster_by_week(team_id, chosen_week=1)

            player_count = len(roster) if hasattr(roster, '__len__') else 'unknown'
            logger.info(f"Successfully retrieved roster with {player_count} players")
            return roster
        except Exception as e:
            logger.error(f"Failed to retrieve team roster: {e}")
            raise

    def get_league_draft_results(self) -> Any:
        """
        Retrieve league draft results.

        Returns:
            Draft results object from Yahoo API
        """
        logger.info("Fetching league draft results...")
        try:
            draft_results = self.yahoo_query.get_league_draft_results()
            logger.info("Successfully retrieved draft results")
            return draft_results
        except Exception as e:
            logger.error(f"Failed to retrieve draft results: {e}")
            raise

    def get_league_metadata(self) -> Any:
        """
        Retrieve league metadata.

        Returns:
            League metadata object from Yahoo API
        """
        logger.info("Fetching league metadata...")
        try:
            metadata = self.yahoo_query.get_league_metadata()
            logger.info("Successfully retrieved league metadata")
            return metadata
        except Exception as e:
            logger.error(f"Failed to retrieve league metadata: {e}")
            raise


def create_fetcher(
    league_id: Optional[str] = None,
    game_id: Optional[str] = None
) -> YahooDataFetcher:
    """
    Factory function to create a YahooDataFetcher instance.

    Args:
        league_id: Yahoo league ID (optional)
        game_id: Yahoo game ID (optional)

    Returns:
        Initialized YahooDataFetcher instance
    """
    return YahooDataFetcher(league_id=league_id, game_id=game_id)
