"""Transaction tracking module for incremental updates.

This module provides functions to track and analyze Yahoo Fantasy transactions
to identify which teams have had roster changes since the last update.
"""

from typing import List, Set, Optional, Any
from datetime import datetime

from src.logger import get_logger
from src.data_models import TransactionInfo, TransactionType, create_transaction_from_yahoo

logger = get_logger(__name__)


def parse_transaction_timestamp(transaction: Any) -> int:
    """
    Extract Unix timestamp from a Yahoo transaction object.

    Args:
        transaction: Yahoo API transaction object

    Returns:
        Unix timestamp (seconds since epoch)

    Raises:
        ValueError: If timestamp cannot be extracted or is invalid
    """
    try:
        timestamp = getattr(transaction, 'timestamp', None)

        if timestamp is None:
            raise ValueError("Transaction has no timestamp attribute")

        # Yahoo API returns timestamps as Unix timestamps (seconds since epoch)
        if not isinstance(timestamp, int):
            timestamp = int(timestamp)

        # Validate timestamp is reasonable (between 2000 and 2100)
        if timestamp < 946684800 or timestamp > 4102444800:
            raise ValueError(f"Timestamp {timestamp} is outside reasonable range")

        logger.debug(f"Parsed timestamp: {timestamp} ({datetime.fromtimestamp(timestamp)})")
        return timestamp

    except (AttributeError, ValueError, TypeError) as e:
        logger.error(f"Failed to parse transaction timestamp: {e}")
        raise ValueError(f"Invalid transaction timestamp: {e}") from e


def _determine_transaction_type(transaction: Any, player_trans_data: Any) -> TransactionType:
    """
    Determine the type of transaction from Yahoo API data.

    Args:
        transaction: Yahoo API transaction object
        player_trans_data: Transaction data for a specific player

    Returns:
        TransactionType enum value
    """
    # Get transaction type from Yahoo
    trans_type = getattr(transaction, 'type', '').lower()

    # Check source and destination
    source_type = getattr(player_trans_data, 'source_type', '')
    dest_type = getattr(player_trans_data, 'destination_type', '')

    # Determine transaction type based on Yahoo data
    if trans_type == 'trade':
        return TransactionType.TRADE
    elif source_type == 'team' and dest_type in ['waivers', 'freeagents']:
        return TransactionType.DROP
    elif source_type in ['waivers', 'freeagents'] and dest_type == 'team':
        return TransactionType.ADD
    elif source_type == 'team' and dest_type == 'team':
        # This is an add/drop in the same transaction
        return TransactionType.ADD_DROP
    else:
        # Default to ADD for unknown cases
        logger.warning(f"Unknown transaction type: {trans_type}, source: {source_type}, dest: {dest_type}")
        return TransactionType.ADD


def _extract_player_name(player: Any) -> str:
    """
    Extract player name from Yahoo API player object.

    Args:
        player: Yahoo API player object

    Returns:
        Player name as string
    """
    name = "Unknown Player"

    if hasattr(player, 'name'):
        name_obj = player.name
        if hasattr(name_obj, 'full'):
            name = str(name_obj.full)
        elif hasattr(name_obj, 'ascii_full'):
            name = str(name_obj.ascii_full)

    return name


def _extract_team_name(transaction: Any, team_key: str) -> str:
    """
    Extract team name from transaction for a given team key.

    Args:
        transaction: Yahoo API transaction object
        team_key: Yahoo team key to find

    Returns:
        Team name as string
    """
    # Try to get team name from transaction players
    if hasattr(transaction, 'players'):
        for player in transaction.players:
            trans_data = getattr(player, 'transaction_data', None)
            if trans_data:
                # Check destination team
                if hasattr(trans_data, 'destination_team_key'):
                    if str(trans_data.destination_team_key) == team_key:
                        if hasattr(trans_data, 'destination_team_name'):
                            return str(trans_data.destination_team_name)

                # Check source team
                if hasattr(trans_data, 'source_team_key'):
                    if str(trans_data.source_team_key) == team_key:
                        if hasattr(trans_data, 'source_team_name'):
                            return str(trans_data.source_team_name)

    # If we can't find the name, return a placeholder
    return f"Team {team_key}"


def get_transactions_since(
    fetcher: Any,
    last_run_timestamp: Optional[int] = None
) -> List[TransactionInfo]:
    """
    Get all transactions since a specific timestamp, converting to TransactionInfo objects.

    Args:
        fetcher: YahooDataFetcher instance
        last_run_timestamp: Unix timestamp of last update (None = get all transactions)

    Returns:
        List of TransactionInfo objects representing transactions since last run

    Raises:
        Exception: If transaction retrieval fails
    """
    logger.info("Retrieving transactions from Yahoo API...")

    try:
        # Get transactions from Yahoo API
        if last_run_timestamp is not None:
            yahoo_transactions = fetcher.get_transactions_since(last_run_timestamp)
            logger.info(f"Retrieved {len(yahoo_transactions)} transactions since timestamp {last_run_timestamp}")
        else:
            yahoo_transactions = fetcher.get_all_transactions()
            logger.info(f"Retrieved all {len(yahoo_transactions)} transactions")

        # Convert to TransactionInfo objects
        transaction_infos: List[TransactionInfo] = []

        for transaction in yahoo_transactions:
            try:
                # Only process successful transactions
                status = getattr(transaction, 'status', '')
                if status != 'successful':
                    logger.debug(f"Skipping transaction with status: {status}")
                    continue

                # Parse timestamp
                timestamp = parse_transaction_timestamp(transaction)

                # Get transaction ID
                transaction_id = str(getattr(transaction, 'transaction_id', 'unknown'))

                # Get FAAB bid (if applicable)
                faab_bid = getattr(transaction, 'faab_bid', None)
                if faab_bid is not None and faab_bid < 0:
                    faab_bid = None  # Treat negative bids as None

                # Process each player in the transaction
                if hasattr(transaction, 'players') and transaction.players:
                    for player in transaction.players:
                        trans_data = getattr(player, 'transaction_data', None)
                        if not trans_data:
                            continue

                        # Get player name
                        player_name = _extract_player_name(player)

                        # Get transaction type
                        trans_type = _determine_transaction_type(transaction, trans_data)

                        # Get team involved (either source or destination)
                        team_key = None
                        team_name = None

                        # For adds, use destination team
                        if trans_type in [TransactionType.ADD, TransactionType.ADD_DROP]:
                            dest_type = getattr(trans_data, 'destination_type', '')
                            if dest_type == 'team':
                                team_key = getattr(trans_data, 'destination_team_key', None)
                                if team_key:
                                    team_name = _extract_team_name(transaction, str(team_key))

                        # For drops, use source team
                        elif trans_type == TransactionType.DROP:
                            source_type = getattr(trans_data, 'source_type', '')
                            if source_type == 'team':
                                team_key = getattr(trans_data, 'source_team_key', None)
                                if team_key:
                                    team_name = _extract_team_name(transaction, str(team_key))

                        # For trades, process both teams (this is simplified - trades are complex)
                        elif trans_type == TransactionType.TRADE:
                            # For now, just get destination team
                            team_key = getattr(trans_data, 'destination_team_key', None)
                            if team_key:
                                team_name = _extract_team_name(transaction, str(team_key))

                        # Only create TransactionInfo if we have team data
                        if team_key and team_name:
                            # Extract team_id from team_key (format: "466.l.68958.t.1" -> "1")
                            team_id = str(team_key).split('.')[-1] if '.' in str(team_key) else str(team_key)

                            trans_info = create_transaction_from_yahoo(
                                transaction_id=transaction_id,
                                timestamp=timestamp,
                                team_id=team_id,
                                team_name=team_name,
                                transaction_type=trans_type,
                                player_name=player_name,
                                faab_bid=faab_bid
                            )

                            transaction_infos.append(trans_info)
                            logger.debug(f"Parsed transaction: {trans_info}")

            except Exception as e:
                logger.warning(f"Failed to parse transaction: {e}")
                continue

        logger.info(f"Successfully parsed {len(transaction_infos)} transaction records")
        return transaction_infos

    except Exception as e:
        logger.error(f"Failed to retrieve transactions: {e}")
        raise


def get_affected_team_ids(transactions: List[TransactionInfo]) -> Set[str]:
    """
    Extract unique team IDs affected by the given transactions.

    Args:
        transactions: List of TransactionInfo objects

    Returns:
        Set of team IDs (as strings) that were affected by transactions
    """
    logger.info(f"Identifying affected teams from {len(transactions)} transactions...")

    if not transactions:
        logger.info("No transactions provided, no teams affected")
        return set()

    # Extract unique team IDs
    affected_teams = {trans.team_id for trans in transactions}

    logger.info(f"Found {len(affected_teams)} affected teams: {sorted(affected_teams)}")

    # Log transaction breakdown by team
    for team_id in sorted(affected_teams):
        team_transactions = [t for t in transactions if t.team_id == team_id]
        team_name = team_transactions[0].team_name if team_transactions else "Unknown"
        logger.debug(f"  Team {team_id} ({team_name}): {len(team_transactions)} transactions")

    return affected_teams
