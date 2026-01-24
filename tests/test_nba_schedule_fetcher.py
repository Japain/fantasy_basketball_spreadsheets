"""
Test NBA schedule fetcher module.

Tests the schedule-based game checking for proactive bench alerts,
including ESPN API parsing, caching, fallback logic, and error handling.
"""

from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import requests

from src import nba_schedule_fetcher
from src.nba_schedule_fetcher import (
    get_teams_with_games_today,
    _fetch_from_espn,
    _is_cache_valid,
    clear_schedule_cache,
    get_cache_stats,
    CACHE_TTL_SECONDS
)
from src.logger import get_logger

logger = get_logger(__name__)

# Sample ESPN API response
SAMPLE_ESPN_RESPONSE = {
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
                        },
                        {
                            "team": {
                                "abbreviation": "LAL",
                                "displayName": "Los Angeles Lakers"
                            }
                        }
                    ]
                }
            ]
        },
        {
            "competitions": [
                {
                    "competitors": [
                        {
                            "team": {
                                "abbreviation": "GSW",
                                "displayName": "Golden State Warriors"
                            }
                        },
                        {
                            "team": {
                                "abbreviation": "BOS",
                                "displayName": "Boston Celtics"
                            }
                        }
                    ]
                }
            ]
        }
    ]
}


def test_espn_api_parsing():
    """Test ESPN API response parsing."""
    print("\n" + "=" * 80)
    print("TEST: ESPN API Response Parsing")
    print("=" * 80)

    clear_schedule_cache()

    # Test 1: Successful fetch and parsing
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_ESPN_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        teams = _fetch_from_espn("2026-01-24")
        assert teams == {"PHX", "LAL", "GSW", "BOS"}, "Should parse all team abbreviations"
        assert len(teams) == 4, "Should find 4 teams"
        print("✓ Test 1: Successfully parsed ESPN API response")

    # Test 2: No games scheduled (empty events)
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"events": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        teams = _fetch_from_espn("2026-06-01")
        assert teams == set(), "Should return empty set for no games"
        print("✓ Test 2: Correctly handles empty events array")

    # Test 3: Malformed response (missing events key)
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        teams = _fetch_from_espn("2026-01-24")
        assert teams == set(), "Should handle missing events key gracefully"
        print("✓ Test 3: Gracefully handles malformed response")

    # Test 4: Duplicate teams (should only appear once)
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        duplicate_response = {
            "events": [
                {
                    "competitions": [
                        {
                            "competitors": [
                                {"team": {"abbreviation": "PHX"}},
                                {"team": {"abbreviation": "LAL"}}
                            ]
                        }
                    ]
                },
                {
                    "competitions": [
                        {
                            "competitors": [
                                {"team": {"abbreviation": "PHX"}},  # Duplicate
                                {"team": {"abbreviation": "GSW"}}
                            ]
                        }
                    ]
                }
            ]
        }
        mock_response = Mock()
        mock_response.json.return_value = duplicate_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        teams = _fetch_from_espn("2026-01-24")
        assert teams == {"PHX", "LAL", "GSW"}, "Should deduplicate team abbreviations"
        assert len(teams) == 3, "PHX should only appear once"
        print("✓ Test 4: Correctly deduplicates team abbreviations")


def test_caching():
    """Test schedule caching functionality."""
    print("\n" + "=" * 80)
    print("TEST: Schedule Caching")
    print("=" * 80)

    clear_schedule_cache()

    # Test 1: Cache hit within TTL
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_ESPN_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # First call - should hit API
        teams1 = get_teams_with_games_today("2026-01-24")
        assert mock_get.call_count == 1, "First call should hit API"

        # Second call - should use cache
        teams2 = get_teams_with_games_today("2026-01-24")
        assert mock_get.call_count == 1, "Second call should use cache"
        assert teams1 == teams2, "Cached data should match original"
        print("✓ Test 1: Cache hit works correctly")

    clear_schedule_cache()

    # Test 2: Cache miss for different dates
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_ESPN_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        teams1 = get_teams_with_games_today("2026-01-24")
        assert mock_get.call_count == 1

        teams2 = get_teams_with_games_today("2026-01-25")
        assert mock_get.call_count == 2, "Different date should hit API again"
        print("✓ Test 2: Different dates trigger new API calls")

    clear_schedule_cache()

    # Test 3: Cache expiration
    old_timestamp = datetime.now() - timedelta(seconds=CACHE_TTL_SECONDS + 1)
    assert not _is_cache_valid(old_timestamp), "Old timestamp should be invalid"

    fresh_timestamp = datetime.now()
    assert _is_cache_valid(fresh_timestamp), "Fresh timestamp should be valid"
    print("✓ Test 3: Cache expiration logic works correctly")

    # Test 4: Cache bypass with use_cache=False
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_ESPN_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        teams1 = get_teams_with_games_today("2026-01-24", use_cache=True)
        assert mock_get.call_count == 1

        teams2 = get_teams_with_games_today("2026-01-24", use_cache=False)
        assert mock_get.call_count == 2, "use_cache=False should bypass cache"
        print("✓ Test 4: Cache bypass works correctly")

    # Test 5: Cache clearing
    clear_schedule_cache()
    nba_schedule_fetcher._schedule_cache["2026-01-24"] = ({"PHX"}, datetime.now())
    stats = get_cache_stats()
    assert stats["size"] == 1, "Cache should have one entry"

    clear_schedule_cache()
    stats = get_cache_stats()
    assert stats["size"] == 0, "Cache should be empty after clear"
    assert stats["dates"] == [], "Dates list should be empty"
    print("✓ Test 5: Cache clearing works correctly")


def test_date_formatting():
    """Test date format conversions."""
    print("\n" + "=" * 80)
    print("TEST: Date Format Conversion")
    print("=" * 80)

    clear_schedule_cache()

    # Test 1: YYYY-MM-DD to YYYYMMDD conversion
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"events": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        _fetch_from_espn("2026-01-24")
        call_args = mock_get.call_args[0][0]
        assert "20260124" in call_args, "Date should be formatted as YYYYMMDD"
        print("✓ Test 1: Date conversion to YYYYMMDD works")

    # Test 2: Leading zeros preserved
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"events": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        _fetch_from_espn("2026-03-05")
        call_args = mock_get.call_args[0][0]
        assert "20260305" in call_args, "Leading zeros should be preserved"
        print("✓ Test 2: Leading zeros preserved in date conversion")


def test_retry_logic():
    """Test exponential backoff retry logic."""
    print("\n" + "=" * 80)
    print("TEST: Retry Logic")
    print("=" * 80)

    clear_schedule_cache()

    # Test 1: Retry with eventual success
    with patch('src.nba_schedule_fetcher.time.sleep'):
        with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
            # Mock 2 failures then success
            mock_get.side_effect = [
                requests.exceptions.Timeout("Timeout 1"),
                requests.exceptions.Timeout("Timeout 2"),
                Mock(json=lambda: SAMPLE_ESPN_RESPONSE, raise_for_status=Mock())
            ]

            teams = _fetch_from_espn("2026-01-24")
            assert mock_get.call_count == 3, "Should retry until success"
            assert len(teams) == 4, "Should return teams after retries"
            print("✓ Test 1: Retry logic works with eventual success")

    clear_schedule_cache()

    # Test 2: Max retries exceeded
    with patch('src.nba_schedule_fetcher.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Persistent timeout")

        try:
            _fetch_from_espn("2026-01-24")
            assert False, "Should raise exception after max retries"
        except Exception as e:
            assert "ESPN API failed after" in str(e), "Should mention max retries"
            assert mock_get.call_count == 3, "Should attempt max retries"
            print("✓ Test 2: Max retries exceeded raises exception")


def test_fallback_logic():
    """Test fallback to NBA Official API."""
    print("\n" + "=" * 80)
    print("TEST: API Fallback Logic")
    print("=" * 80)

    clear_schedule_cache()

    # Test 1: Fallback attempted on ESPN failure
    with patch('src.nba_schedule_fetcher._fetch_from_espn') as mock_espn:
        with patch('src.nba_schedule_fetcher._fetch_from_nba_official') as mock_nba:
            mock_espn.side_effect = Exception("ESPN failed")
            mock_nba.return_value = {"PHX", "LAL"}

            teams = get_teams_with_games_today("2026-01-24")
            assert mock_espn.call_count == 1, "ESPN should be tried first"
            assert mock_nba.call_count == 1, "NBA API should be tried as fallback"
            print("✓ Test 1: Fallback to NBA API on ESPN failure")

    clear_schedule_cache()

    # Test 2: NBA API not called on ESPN success
    with patch('src.nba_schedule_fetcher._fetch_from_espn') as mock_espn:
        with patch('src.nba_schedule_fetcher._fetch_from_nba_official') as mock_nba:
            mock_espn.return_value = {"PHX", "LAL"}

            teams = get_teams_with_games_today("2026-01-24")
            assert mock_espn.call_count == 1, "ESPN should be tried"
            assert mock_nba.call_count == 0, "NBA API should not be called"
            print("✓ Test 2: NBA API not called when ESPN succeeds")

    clear_schedule_cache()

    # Test 3: Both APIs fail - returns empty set
    with patch('src.nba_schedule_fetcher._fetch_from_espn') as mock_espn:
        with patch('src.nba_schedule_fetcher._fetch_from_nba_official') as mock_nba:
            mock_espn.side_effect = Exception("ESPN failed")
            mock_nba.side_effect = Exception("NBA failed")

            teams = get_teams_with_games_today("2026-01-24")
            assert teams == set(), "Should return empty set when both fail"
            print("✓ Test 3: Returns empty set when both APIs fail")


def test_cache_stats():
    """Test cache statistics functionality."""
    print("\n" + "=" * 80)
    print("TEST: Cache Statistics")
    print("=" * 80)

    clear_schedule_cache()

    # Test 1: Empty cache stats
    stats = get_cache_stats()
    assert stats["size"] == 0, "Size should be 0"
    assert stats["dates"] == [], "Dates should be empty list"
    assert stats["oldest"] is None, "Oldest should be None"
    assert stats["newest"] is None, "Newest should be None"
    print("✓ Test 1: Empty cache stats are correct")

    # Test 2: Populated cache stats
    now = datetime.now()
    nba_schedule_fetcher._schedule_cache["2026-01-24"] = ({"PHX"}, now)
    nba_schedule_fetcher._schedule_cache["2026-01-25"] = ({"LAL"}, now - timedelta(hours=1))
    nba_schedule_fetcher._schedule_cache["2026-01-26"] = ({"GSW"}, now + timedelta(hours=1))

    stats = get_cache_stats()
    assert stats["size"] == 3, "Size should be 3"
    assert len(stats["dates"]) == 3, "Should have 3 dates"
    assert "2026-01-24" in stats["dates"], "Should contain cached date"
    assert stats["oldest"] is not None, "Oldest should be set"
    assert stats["newest"] is not None, "Newest should be set"
    print("✓ Test 2: Populated cache stats are correct")

    clear_schedule_cache()


def main():
    """Run all NBA schedule fetcher tests."""
    print("\n" + "=" * 80)
    print("NBA SCHEDULE FETCHER MODULE TEST SUITE")
    print("=" * 80)

    try:
        test_espn_api_parsing()
        test_caching()
        test_date_formatting()
        test_retry_logic()
        test_fallback_logic()
        test_cache_stats()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("  • ESPN API parsing works correctly")
        print("  • Caching with 1-hour TTL works correctly")
        print("  • Date format conversion works correctly")
        print("  • Retry logic with exponential backoff works")
        print("  • Fallback to NBA API works correctly")
        print("  • Cache statistics are accurate")
        print("\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    main()
