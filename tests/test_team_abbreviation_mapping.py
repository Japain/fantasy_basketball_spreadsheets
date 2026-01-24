#!/usr/bin/env python3
"""
Test team abbreviation mapping between ESPN and Yahoo APIs.

Ensures that team abbreviations from ESPN API are correctly normalized
to match Yahoo API format for accurate game schedule checking.
"""

from src.nba_schedule_fetcher import (
    normalize_team_abbreviation,
    ESPN_TO_YAHOO_TEAM_MAPPING
)


def test_normalize_washington():
    """Test Washington Wizards abbreviation normalization."""
    result = normalize_team_abbreviation('WSH')
    assert result == 'WAS', f"Expected 'WAS', got '{result}'"
    print("✓ Washington Wizards: WSH -> WAS")


def test_normalize_new_york():
    """Test New York Knicks abbreviation normalization."""
    result = normalize_team_abbreviation('NY')
    assert result == 'NYK', f"Expected 'NYK', got '{result}'"
    print("✓ New York Knicks: NY -> NYK")


def test_normalize_golden_state():
    """Test Golden State Warriors abbreviation normalization."""
    result = normalize_team_abbreviation('GS')
    assert result == 'GSW', f"Expected 'GSW', got '{result}'"
    print("✓ Golden State Warriors: GS -> GSW")


def test_normalize_san_antonio():
    """Test San Antonio Spurs abbreviation normalization."""
    result = normalize_team_abbreviation('SA')
    assert result == 'SAS', f"Expected 'SAS', got '{result}'"
    print("✓ San Antonio Spurs: SA -> SAS")


def test_normalize_new_orleans():
    """Test New Orleans Pelicans abbreviation normalization."""
    result = normalize_team_abbreviation('NO')
    assert result == 'NOP', f"Expected 'NOP', got '{result}'"
    print("✓ New Orleans Pelicans: NO -> NOP")


def test_normalize_utah():
    """Test Utah Jazz abbreviation normalization."""
    result = normalize_team_abbreviation('UTAH')
    assert result == 'UTA', f"Expected 'UTA', got '{result}'"
    print("✓ Utah Jazz: UTAH -> UTA")


def test_normalize_unchanged():
    """Test that teams with matching abbreviations are unchanged."""
    unchanged_teams = [
        'LAL',  # Los Angeles Lakers
        'BOS',  # Boston Celtics
        'CHI',  # Chicago Bulls
        'MIA',  # Miami Heat
        'PHX',  # Phoenix Suns
        'DAL',  # Dallas Mavericks
        'PHI',  # Philadelphia 76ers
    ]

    for team in unchanged_teams:
        result = normalize_team_abbreviation(team)
        assert result == team, f"Expected '{team}', got '{result}'"

    print(f"✓ {len(unchanged_teams)} teams pass through unchanged")


def test_all_mappings_exist():
    """Test that all known ESPN-Yahoo differences are mapped."""
    known_differences = {
        'WSH': 'WAS',  # Washington Wizards
        'NY': 'NYK',   # New York Knicks
        'GS': 'GSW',   # Golden State Warriors
        'SA': 'SAS',   # San Antonio Spurs
        'NO': 'NOP',   # New Orleans Pelicans
        'UTAH': 'UTA', # Utah Jazz
    }

    assert ESPN_TO_YAHOO_TEAM_MAPPING == known_differences, \
        f"Mapping mismatch: expected {known_differences}, got {ESPN_TO_YAHOO_TEAM_MAPPING}"
    print("✓ All known ESPN-Yahoo differences are mapped")


def test_mapping_consistency():
    """Test that mapping values are all unique (no collisions)."""
    values = list(ESPN_TO_YAHOO_TEAM_MAPPING.values())
    unique_values = set(values)
    assert len(values) == len(unique_values), "Mapping contains duplicate values"
    print("✓ Mapping values are all unique (no collisions)")


def test_mapping_keys_not_in_values():
    """Test that no ESPN abbreviation is also a Yahoo abbreviation."""
    keys = set(ESPN_TO_YAHOO_TEAM_MAPPING.keys())
    values = set(ESPN_TO_YAHOO_TEAM_MAPPING.values())

    intersection = keys & values
    assert len(intersection) == 0, f"Ambiguous mappings found: {intersection}"
    print("✓ No ambiguous mappings (ESPN keys not in Yahoo values)")


def main():
    """Run all tests."""
    print("=" * 80)
    print("Testing Team Abbreviation Mapping")
    print("=" * 80)
    print()

    tests = [
        test_normalize_washington,
        test_normalize_new_york,
        test_normalize_golden_state,
        test_normalize_san_antonio,
        test_normalize_new_orleans,
        test_normalize_utah,
        test_normalize_unchanged,
        test_all_mappings_exist,
        test_mapping_consistency,
        test_mapping_keys_not_in_values,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    exit(main())
