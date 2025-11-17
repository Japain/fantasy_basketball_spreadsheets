"""
Yahoo Fantasy Sports API data fetcher.

Handles authentication and data retrieval from Yahoo Fantasy Basketball API using yfpy.
Implements the salary retrieval strategy: FAAB → Keeper → Draft → Free Agent.
"""

import re
from typing import Optional, Any, Dict, List, Tuple
from pathlib import Path
from yfpy.query import YahooFantasySportsQuery
from config import config, BASE_DIR
from src.logger import logger
from src.data_models import (
    League,
    Team,
    Player,
    SalarySource,
    create_league_from_yahoo_data,
    create_team_from_yahoo_data,
    create_player_from_yahoo_data,
)


def _decode_and_clean_text(value: Any, strip_emojis: bool = False) -> str:
    """
    Decode bytes to string and optionally strip emojis.

    Handles various text encoding scenarios from Yahoo API:
    - Bytes objects (e.g., b'Team Name') are decoded to UTF-8
    - Regular strings are passed through
    - Emojis can be optionally removed for compatibility

    Args:
        value: Text value to decode/clean (can be bytes, str, or other)
        strip_emojis: If True, removes emoji characters from the result

    Returns:
        Cleaned string value
    """
    # First, decode bytes to string if needed
    if isinstance(value, bytes):
        text = value.decode('utf-8', errors='replace')
    else:
        text = str(value)

    # Strip emojis if requested
    if strip_emojis:
        # Remove emoji characters using regex
        # This pattern matches most emoji ranges in Unicode
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text).strip()

    return text


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
            week: Week number (optional). If provided, gets roster for that week.
                  If None, yfpy will use the current week by default.

        Returns:
            Team roster object from Yahoo API
        """
        logger.info(f"Fetching roster for team {team_id}" + (f" week {week}" if week else " (current week)"))
        try:
            if week:
                roster = self.yahoo_query.get_team_roster_by_week(team_id, chosen_week=week)
            else:
                # When week is None, yfpy uses current week by default
                roster = self.yahoo_query.get_team_roster_by_week(team_id)

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

    def get_all_transactions(self) -> List[Any]:
        """
        Retrieve all transactions for the league.

        Returns:
            List of transaction objects from Yahoo API

        Raises:
            Exception: If transaction retrieval fails
        """
        logger.info("Fetching all league transactions...")
        try:
            transactions = self.yahoo_query.get_league_transactions()
            transaction_count = len(transactions) if hasattr(transactions, '__len__') else 'unknown'
            logger.info(f"Successfully retrieved {transaction_count} transactions")
            logger.debug(f"Transaction types: {type(transactions)}")
            return transactions
        except Exception as e:
            logger.error(f"Failed to retrieve league transactions: {e}")
            raise

    def get_transactions_since(self, since_timestamp: int) -> List[Any]:
        """
        Retrieve transactions that occurred after a specific timestamp.

        Args:
            since_timestamp: Unix timestamp to filter transactions (only return transactions after this time)

        Returns:
            List of transaction objects from Yahoo API that occurred after the timestamp

        Raises:
            Exception: If transaction retrieval fails
        """
        logger.info(f"Fetching transactions since timestamp {since_timestamp}...")
        try:
            # Get all transactions
            all_transactions = self.get_all_transactions()

            # Filter transactions by timestamp
            filtered_transactions = []
            for transaction in all_transactions:
                trans_timestamp = getattr(transaction, 'timestamp', None)
                if trans_timestamp is not None and trans_timestamp > since_timestamp:
                    filtered_transactions.append(transaction)

            logger.info(f"Found {len(filtered_transactions)} transactions since timestamp {since_timestamp}")
            logger.debug(f"Total transactions: {len(all_transactions)}, Filtered: {len(filtered_transactions)}")

            return filtered_transactions

        except Exception as e:
            logger.error(f"Failed to retrieve transactions since timestamp: {e}")
            raise


    def extract_league_data(self) -> League:
        """
        Extract complete league data with all teams, rosters, and salaries.

        Implements the salary retrieval strategy:
        1. FAAB waiver acquisition (most recent) - takes priority
        2. Keeper cost
        3. Draft auction cost
        4. Free agent ($0)

        Returns:
            League object with complete data including all teams and player salaries
        """
        logger.info("Starting complete league data extraction...")

        # Get league info (includes draft results and transactions)
        league_info = self.get_league_info()

        # Get current week
        current_week = getattr(league_info, 'current_week', None)
        if current_week:
            logger.info(f"Current week: {current_week}")
        else:
            logger.warning("Could not determine current week, will use default")

        # Create draft cost mapping
        logger.info("Building draft cost mapping...")
        draft_cost_map = self._build_draft_cost_map(league_info.draft_results)
        logger.debug(f"Draft cost map contains {len(draft_cost_map)} players")

        # Create FAAB cost mapping
        logger.info("Building FAAB cost mapping from transactions...")
        faab_cost_map = self._build_faab_cost_map(league_info.transactions)
        logger.debug(f"FAAB cost map contains {len(faab_cost_map)} players")

        # Create League object
        league = create_league_from_yahoo_data(
            league_id=str(league_info.league_id),
            league_key=str(league_info.league_key),
            league_name=_decode_and_clean_text(league_info.name),
            season=str(league_info.season),
            num_teams=int(league_info.num_teams)
        )

        logger.info(f"Processing {league.num_teams} teams...")

        # Process each team
        for yahoo_team in league_info.teams:
            try:
                team = self._extract_team_data(
                    yahoo_team,
                    draft_cost_map,
                    faab_cost_map,
                    current_week
                )
                league.add_team(team)
                logger.info(f"  ✓ {team.team_name}: {len(team.roster)} players, ${team.total_salary} total")
            except Exception as e:
                logger.error(f"  ✗ Failed to extract team {yahoo_team.team_id}: {e}")
                raise

        # Log summary statistics
        stats = league.get_league_stats()
        logger.info("League data extraction complete!")
        logger.info(f"  Total players: {stats['total_players']}")
        logger.info(f"  Average roster size: {stats['avg_roster_size']:.1f}")
        logger.info(f"  Total salary spent: ${stats['total_salary_spent']}")
        logger.info(f"  Average salary per team: ${stats['avg_salary_per_team']:.2f}")

        return league

    def _build_draft_cost_map(self, draft_results: List[Any]) -> Dict[str, int]:
        """
        Build mapping of player_key to draft auction cost.

        Args:
            draft_results: List of DraftResult objects from Yahoo API

        Returns:
            Dictionary mapping player_key to draft cost
        """
        draft_map = {}
        for result in draft_results:
            player_key = getattr(result, 'player_key', None)
            cost = getattr(result, 'cost', None)

            if player_key and cost is not None:
                draft_map[player_key] = cost

        return draft_map

    def _build_faab_cost_map(self, transactions: List[Any]) -> Dict[str, int]:
        """
        Build mapping of player_key to FAAB acquisition cost.

        For players with multiple acquisitions, keeps only the MOST RECENT one
        (highest timestamp).

        Note: Yahoo API returns faab_bid=None for $0 waiver claims. We treat
        these as $0 FAAB acquisitions.

        Args:
            transactions: List of Transaction objects from league_info.transactions

        Returns:
            Dictionary mapping player_key to FAAB cost
        """
        player_faab_map: Dict[str, Tuple[int, int]] = {}  # player_key -> (cost, timestamp)

        for transaction in transactions:
            status = getattr(transaction, 'status', '')
            timestamp = getattr(transaction, 'timestamp', 0)

            # Only process successful transactions
            if status != 'successful':
                continue

            # Find players being added
            if hasattr(transaction, 'players') and transaction.players:
                for player in transaction.players:
                    trans_data = getattr(player, 'transaction_data', None)
                    if not trans_data:
                        continue

                    # Check if player is being added from waivers/free agents to a team
                    dest_type = getattr(trans_data, 'destination_type', '')
                    source_type = getattr(trans_data, 'source_type', '')

                    if dest_type == 'team' and source_type in ['waivers', 'freeagents']:
                        player_key = getattr(player, 'player_key', None)
                        if player_key:
                            # Get FAAB bid (treat None as 0 for waiver acquisitions)
                            faab_bid = getattr(transaction, 'faab_bid', None)
                            if faab_bid is None:
                                faab_bid = 0  # Yahoo returns None for $0 waiver claims

                            # Skip invalid negative values
                            if faab_bid < 0:
                                continue

                            # Keep most recent FAAB bid (highest timestamp)
                            if player_key not in player_faab_map or timestamp > player_faab_map[player_key][1]:
                                player_faab_map[player_key] = (faab_bid, timestamp)

        # Return simplified map with just the FAAB cost (remove timestamp)
        return {player_key: cost for player_key, (cost, _) in player_faab_map.items()}

    def _get_player_salary_and_source(
        self,
        player: Any,
        draft_cost_map: Dict[str, int],
        faab_cost_map: Dict[str, int]
    ) -> Tuple[int, SalarySource]:
        """
        Get salary and source for a player using priority strategy.

        Priority order (most recent acquisition takes precedence):
        1. FAAB waiver acquisition (most recent)
        2. Keeper cost
        3. Draft auction cost
        4. Free agent ($0)

        Args:
            player: Player object from Yahoo API
            draft_cost_map: Dictionary mapping player_key to draft cost
            faab_cost_map: Dictionary mapping player_key to FAAB cost (most recent)

        Returns:
            Tuple of (salary, source)
        """
        player_key = getattr(player, 'player_key', None)

        # Priority 1: Check FAAB waiver acquisition FIRST (most recent takes priority)
        if player_key and player_key in faab_cost_map:
            return (faab_cost_map[player_key], SalarySource.FAAB_WAIVER)

        # Priority 2: Check keeper cost
        is_keeper = getattr(player, 'is_keeper', {})
        if isinstance(is_keeper, dict):
            if is_keeper.get('status') and is_keeper.get('cost') is not None:
                return (is_keeper['cost'], SalarySource.KEEPER)

        # Priority 3: Check draft cost
        if player_key and player_key in draft_cost_map:
            return (draft_cost_map[player_key], SalarySource.DRAFT)

        # Priority 4: Free agent (no cost)
        return (0, SalarySource.FREE_AGENT)

    def _extract_team_data(
        self,
        yahoo_team: Any,
        draft_cost_map: Dict[str, int],
        faab_cost_map: Dict[str, int],
        current_week: Optional[int] = None
    ) -> Team:
        """
        Extract complete team data including roster with salaries.

        Args:
            yahoo_team: Team object from Yahoo API
            draft_cost_map: Dictionary mapping player_key to draft cost
            faab_cost_map: Dictionary mapping player_key to FAAB cost
            current_week: Current week number (optional, for getting current roster)

        Returns:
            Team object with complete roster and salary information
        """
        # Get team basic info
        team_id = str(yahoo_team.team_id)
        team_key = str(yahoo_team.team_key)
        team_name = _decode_and_clean_text(yahoo_team.name)

        # Get manager name
        manager_name = "Unknown"
        if hasattr(yahoo_team, 'managers') and yahoo_team.managers:
            first_manager = yahoo_team.managers[0]
            if hasattr(first_manager, 'nickname'):
                manager_name = _decode_and_clean_text(first_manager.nickname)

        # Get FAAB balance
        faab_remaining = getattr(yahoo_team, 'faab_balance', 0)

        # Create Team object
        team = create_team_from_yahoo_data(
            team_id=team_id,
            team_key=team_key,
            team_name=team_name,
            manager_name=manager_name,
            faab_remaining=faab_remaining,
            initial_budget=config.INITIAL_AUCTION_BUDGET
        )

        # Get roster (use current week if available)
        roster = self.get_team_roster(team_id, week=current_week)

        # Process each player
        # Filter out players with no assigned roster position
        # These are players in a transitional state and should not be counted
        if hasattr(roster, 'players') and roster.players:
            for yahoo_player in roster.players:
                # Check if player has an assigned roster position
                selected_pos_obj = getattr(yahoo_player, 'selected_position', None)

                # Check if selected_position is None or if position attribute is None
                if selected_pos_obj is None:
                    player_name = "Unknown"
                    if hasattr(yahoo_player, 'name') and hasattr(yahoo_player.name, 'full'):
                        player_name = str(yahoo_player.name.full)
                    logger.debug(f"Skipping player '{player_name}' - selected_position is None")
                    continue

                # Check if the position value within selected_position is None
                position_value = getattr(selected_pos_obj, 'position', None)
                if position_value is None or str(position_value).upper() == 'NONE':
                    player_name = "Unknown"
                    if hasattr(yahoo_player, 'name') and hasattr(yahoo_player.name, 'full'):
                        player_name = str(yahoo_player.name.full)
                    logger.debug(f"Skipping player '{player_name}' - no assigned roster slot (position is {position_value})")
                    continue

                player = self._extract_player_data(
                    yahoo_player,
                    draft_cost_map,
                    faab_cost_map
                )
                team.add_player(player)

        return team

    def _extract_player_data(
        self,
        yahoo_player: Any,
        draft_cost_map: Dict[str, int],
        faab_cost_map: Dict[str, int]
    ) -> Player:
        """
        Extract player data with salary from Yahoo API player object.

        Args:
            yahoo_player: Player object from Yahoo API
            draft_cost_map: Dictionary mapping player_key to draft cost
            faab_cost_map: Dictionary mapping player_key to FAAB cost

        Returns:
            Player object with salary information
        """
        # Get player basic info
        player_key = str(yahoo_player.player_key)

        # Get player name
        name = "Unknown"
        if hasattr(yahoo_player, 'name'):
            name_obj = yahoo_player.name
            if hasattr(name_obj, 'full'):
                name = _decode_and_clean_text(name_obj.full)
            elif hasattr(name_obj, 'ascii_full'):
                name = _decode_and_clean_text(name_obj.ascii_full)

        # Get position
        position = str(getattr(yahoo_player, 'display_position', 'N/A'))

        # Get roster position (actual roster slot like PG, BN, IL, IL+)
        roster_position = None
        selected_pos_obj = getattr(yahoo_player, 'selected_position', None)
        if selected_pos_obj:
            position_value = getattr(selected_pos_obj, 'position', None)
            if position_value:
                roster_position = str(position_value)

        # Get NBA team
        nba_team = getattr(yahoo_player, 'editorial_team_abbr', None)
        if nba_team:
            nba_team = str(nba_team)

        # Get salary and source using priority strategy
        salary, source = self._get_player_salary_and_source(
            yahoo_player,
            draft_cost_map,
            faab_cost_map
        )

        return create_player_from_yahoo_data(
            player_key=player_key,
            name=name,
            position=position,
            salary=salary,
            source=source,
            nba_team=nba_team,
            roster_position=roster_position
        )


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
