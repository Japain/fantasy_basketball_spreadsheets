"""Google Sheets reading module for incremental updates.

This module provides functions to read existing Google Sheets spreadsheets,
extract timestamps, and validate structure for incremental update mode.
"""

import re
from typing import Optional, List, Any
from datetime import datetime
from googleapiclient.errors import HttpError

from src.logger import get_logger
from src.google_auth import get_google_sheets_service
from src.api_retry import api_call_with_retry

logger = get_logger(__name__)


def extract_spreadsheet_id_from_url(url: str) -> str:
    """
    Extract spreadsheet ID from a Google Sheets URL.

    Supports multiple URL formats:
    - https://docs.google.com/spreadsheets/d/{ID}/edit
    - https://docs.google.com/spreadsheets/d/{ID}/edit#gid=0
    - https://docs.google.com/spreadsheets/d/{ID}
    - {ID} (if just the ID is provided)

    Args:
        url: Google Sheets URL or spreadsheet ID

    Returns:
        Spreadsheet ID as a string

    Raises:
        ValueError: If URL format is invalid or ID cannot be extracted

    Examples:
        >>> extract_spreadsheet_id_from_url("https://docs.google.com/spreadsheets/d/ABC123/edit")
        'ABC123'
        >>> extract_spreadsheet_id_from_url("ABC123")
        'ABC123'
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    url = url.strip()

    # Pattern to match Google Sheets URLs
    # Matches: /spreadsheets/d/{ID}/ or /spreadsheets/d/{ID}
    pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
    match = re.search(pattern, url)

    if match:
        spreadsheet_id = match.group(1)
        logger.debug(f"Extracted spreadsheet ID from URL: {spreadsheet_id}")
        return spreadsheet_id

    # If no match, check if the input is already a spreadsheet ID
    # Spreadsheet IDs are typically alphanumeric with hyphens/underscores, ~44 chars
    if re.match(r'^[a-zA-Z0-9-_]{20,}$', url):
        logger.debug(f"Input appears to be a spreadsheet ID: {url}")
        return url

    # If we get here, the format is invalid
    raise ValueError(
        f"Invalid Google Sheets URL or ID: '{url}'. "
        f"Expected format: https://docs.google.com/spreadsheets/d/{{ID}}/... or just the ID"
    )


def _get_sheet_service() -> Any:
    """
    Get authenticated Google Sheets API service.

    Returns:
        Google Sheets API service object

    Raises:
        Exception: If authentication fails
    """
    try:
        service = get_google_sheets_service()
        logger.debug("Google Sheets service authenticated successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to authenticate Google Sheets service: {e}")
        raise


def _parse_iso_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse ISO 8601 timestamp string to datetime object.

    Expected format: "2025-11-15T10:30:00Z"

    Args:
        timestamp_str: ISO 8601 formatted timestamp string

    Returns:
        datetime object if parsing succeeds, None otherwise

    Examples:
        >>> _parse_iso_timestamp("2025-11-15T10:30:00Z")
        datetime(2025, 11, 15, 10, 30, 0)
    """
    if not timestamp_str or not isinstance(timestamp_str, str):
        return None

    try:
        # Try parsing ISO 8601 format with Z suffix (UTC)
        if timestamp_str.endswith('Z'):
            # Remove Z and parse
            dt = datetime.fromisoformat(timestamp_str[:-1])
            logger.debug(f"Parsed ISO timestamp: {timestamp_str} -> {dt}")
            return dt
        else:
            # Try parsing without Z
            dt = datetime.fromisoformat(timestamp_str)
            logger.debug(f"Parsed ISO timestamp: {timestamp_str} -> {dt}")
            return dt

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return None


def read_last_run_timestamp(service: Any, spreadsheet_id: str) -> Optional[datetime]:
    """
    Read last run timestamp from Summary sheet cell G1.

    Backwards compatible: Returns None for old spreadsheets without timestamps.

    Args:
        service: Google Sheets API service object
        spreadsheet_id: Spreadsheet ID

    Returns:
        datetime object if timestamp found and valid, None otherwise
        (None indicates first run or old spreadsheet format)

    Note:
        Returns None in these cases (backwards compatible):
        - Cell G1 doesn't exist (old spreadsheet)
        - Cell G1 is empty (old spreadsheet)
        - Cell G1 has invalid timestamp format (corrupted)
        - Summary sheet doesn't exist
    """
    logger.info(f"Reading timestamp from spreadsheet {spreadsheet_id}...")

    try:
        # Try to read cell G1 from Summary sheet with retry logic
        result = api_call_with_retry(
            lambda: service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Summary!G1'
            ).execute(),
            operation_name="read timestamp"
        )

        # Case 1: No values returned (cell doesn't exist or is empty)
        if 'values' not in result or not result['values']:
            logger.info("No timestamp found in G1 (old spreadsheet format - will update all teams)")
            return None

        # Case 2: Cell exists but is empty
        timestamp_str = result['values'][0][0] if result['values'][0] else None
        if not timestamp_str or str(timestamp_str).strip() == '':
            logger.info("Timestamp cell G1 is empty (old spreadsheet format - will update all teams)")
            return None

        # Case 3: Parse the timestamp
        timestamp = _parse_iso_timestamp(str(timestamp_str).strip())
        if timestamp is None:
            logger.warning(
                f"Invalid timestamp format in G1: '{timestamp_str}' "
                f"(treating as first run - will update all teams)"
            )
            return None

        logger.info(f"✓ Found timestamp: {timestamp_str}")
        return timestamp

    except HttpError as e:
        if e.resp.status == 404:
            logger.info("Summary sheet not found (treating as first run - will update all teams)")
            return None
        else:
            logger.warning(f"Error reading timestamp (treating as first run): {e}")
            return None

    except Exception as e:
        logger.warning(f"Unexpected error reading timestamp (treating as first run): {e}")
        return None


def validate_sheet_structure(service: Any, spreadsheet_id: str) -> bool:
    """
    Validate that the spreadsheet has the expected structure from this application.

    Checks:
    - Summary sheet exists
    - At least one other sheet exists (team sheet)

    Args:
        service: Google Sheets API service object
        spreadsheet_id: Spreadsheet ID

    Returns:
        True if structure is valid, False otherwise
    """
    logger.info(f"Validating spreadsheet structure for {spreadsheet_id}...")

    try:
        # Get spreadsheet metadata with retry logic
        spreadsheet = api_call_with_retry(
            lambda: service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute(),
            operation_name="validate sheet structure"
        )

        # Get all sheet names
        sheets = spreadsheet.get('sheets', [])
        sheet_names = [sheet['properties']['title'] for sheet in sheets]

        logger.debug(f"Found {len(sheet_names)} sheets: {sheet_names}")

        # Check if Summary sheet exists
        if 'Summary' not in sheet_names:
            logger.warning("Validation failed: Summary sheet not found")
            return False

        # Check if at least one other sheet exists (team sheet)
        if len(sheet_names) < 2:
            logger.warning("Validation failed: No team sheets found (expected at least 1)")
            return False

        logger.info(f"✓ Spreadsheet structure validated: {len(sheet_names)} sheets found")
        return True

    except HttpError as e:
        logger.error(f"HTTP error validating spreadsheet: {e}")
        return False

    except Exception as e:
        logger.error(f"Error validating spreadsheet structure: {e}")
        return False


def batch_read_initial_data(service: Any, spreadsheet_id: str) -> dict:
    """
    Batch read initial spreadsheet data in optimized way (v2.5+).

    Combines multiple operations into minimal API calls:
    - Gets spreadsheet metadata (sheet list, properties)
    - Reads timestamp from Summary!G1

    This replaces making separate calls to:
    - read_last_run_timestamp() (1 API call)
    - validate_sheet_structure() (1 API call)
    - get_existing_team_sheets() (1 API call)

    Args:
        service: Google Sheets API service object
        spreadsheet_id: Spreadsheet ID

    Returns:
        dict with keys:
            - 'timestamp': datetime object or None
            - 'has_summary': bool (True if Summary sheet exists)
            - 'sheet_count': int (total number of sheets)
            - 'team_sheets': List[str] (team sheet names, excludes Summary)
            - 'valid_structure': bool (True if structure is valid)

    Performance:
        - Before (v2.4): 3 API calls (timestamp + validation + team sheets)
        - After (v2.5): 2 API calls (1 metadata + 1 value read)
        - Reduction: 33% fewer calls

    Example:
        >>> data = batch_read_initial_data(service, spreadsheet_id)
        >>> if data['valid_structure']:
        >>>     timestamp = data['timestamp']
        >>>     team_sheets = data['team_sheets']
    """
    logger.info(f"Batch reading initial data from {spreadsheet_id}...")

    result = {
        'timestamp': None,
        'has_summary': False,
        'sheet_count': 0,
        'team_sheets': [],
        'valid_structure': False
    }

    try:
        # CALL 1: Get spreadsheet metadata (sheet list, properties)
        spreadsheet = api_call_with_retry(
            lambda: service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute(),
            operation_name="batch read spreadsheet metadata"
        )

        # Process sheet metadata
        sheets = spreadsheet.get('sheets', [])
        sheet_names = [sheet['properties']['title'] for sheet in sheets]
        result['sheet_count'] = len(sheet_names)
        result['has_summary'] = 'Summary' in sheet_names
        result['team_sheets'] = [name for name in sheet_names if name != 'Summary']

        # Validate structure
        result['valid_structure'] = result['has_summary'] and len(sheet_names) >= 2

        logger.debug(
            f"Metadata read: {result['sheet_count']} sheets, "
            f"Summary={'Yes' if result['has_summary'] else 'No'}, "
            f"Team sheets={len(result['team_sheets'])}"
        )

        # CALL 2: Read timestamp from Summary!G1 (only if Summary exists)
        if result['has_summary']:
            try:
                timestamp_result = api_call_with_retry(
                    lambda: service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range='Summary!G1'
                    ).execute(),
                    operation_name="batch read timestamp"
                )

                # Parse timestamp if found
                if 'values' in timestamp_result and timestamp_result['values']:
                    timestamp_str = timestamp_result['values'][0][0] if timestamp_result['values'][0] else None
                    if timestamp_str and str(timestamp_str).strip():
                        result['timestamp'] = _parse_iso_timestamp(str(timestamp_str).strip())
                        if result['timestamp']:
                            logger.info(f"✓ Found timestamp: {timestamp_str}")
                        else:
                            logger.warning(f"Invalid timestamp format: '{timestamp_str}'")
                    else:
                        logger.info("Timestamp cell G1 is empty (old format)")
                else:
                    logger.info("No timestamp found in G1 (old format)")

            except HttpError as e:
                logger.warning(f"Could not read timestamp: {e}")
                # Non-critical - continue with None timestamp

        logger.info(
            f"✓ Batch read complete: {result['sheet_count']} sheets, "
            f"valid={'Yes' if result['valid_structure'] else 'No'}, "
            f"timestamp={'Found' if result['timestamp'] else 'None'}"
        )
        return result

    except HttpError as e:
        logger.error(f"HTTP error in batch read: {e}")
        return result

    except Exception as e:
        logger.error(f"Error in batch read: {e}")
        return result


def get_existing_team_sheets(service: Any, spreadsheet_id: str) -> List[str]:
    """
    Get list of existing team sheet names from the spreadsheet.

    Excludes the Summary sheet.

    ⚠️ NOTE: Consider using batch_read_initial_data() instead for better performance
    if you also need timestamp or validation data (reduces API calls).

    Args:
        service: Google Sheets API service object
        spreadsheet_id: Spreadsheet ID

    Returns:
        List of team sheet names (empty list if error occurs)
    """
    logger.info(f"Getting existing team sheets from {spreadsheet_id}...")

    try:
        # Get spreadsheet metadata with retry logic
        spreadsheet = api_call_with_retry(
            lambda: service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute(),
            operation_name="get existing team sheets"
        )

        # Get all sheet names
        sheets = spreadsheet.get('sheets', [])
        all_sheet_names = [sheet['properties']['title'] for sheet in sheets]

        # Filter out Summary sheet
        team_sheets = [name for name in all_sheet_names if name != 'Summary']

        logger.info(f"✓ Found {len(team_sheets)} team sheets: {team_sheets}")
        return team_sheets

    except HttpError as e:
        logger.error(f"HTTP error getting team sheets: {e}")
        return []

    except Exception as e:
        logger.error(f"Error getting team sheets: {e}")
        return []
