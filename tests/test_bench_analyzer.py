"""
Test bench management analyzer module.

This script tests the bench analyzer functions including:
1. Player health status detection
2. Bench position detection
3. IL position detection
4. Roster row parsing
5. Game checking logic
6. Full violation analysis workflow
"""

from unittest.mock import Mock, patch
from src.bench_analyzer import (
    _is_player_healthy,
    _is_benched,
    _is_on_il,
    _is_on_il_or_il_plus,
    check_player_had_game_today_legacy,
    analyze_bench_violations,
    analyze_il_violations,
    get_teams_with_bench_violations,
)
from src.data_models import Player, Team, League, SalarySource
from src.logger import get_logger

logger = get_logger(__name__)


def test_player_health_checks():
    """Test health status detection."""
    print("\n" + "=" * 80)
    print("TEST: Player Health Status Detection")
    print("=" * 80)

    # Test 1: Healthy player with no status
    player = Player(
        player_key="466.p.1",
        name="Healthy Player",
        position="PG",
        salary=50,
        source=SalarySource.DRAFT,
        status=None
    )
    assert _is_player_healthy(player) is True, "Player with no status should be healthy"
    print("✓ Test 1: Player with no status is healthy")

    # Test 2: Healthy player with empty status
    player = Player(
        player_key="466.p.1",
        name="Healthy Player",
        position="PG",
        salary=50,
        source=SalarySource.DRAFT,
        status=""
    )
    assert _is_player_healthy(player) is True, "Player with empty status should be healthy"
    print("✓ Test 2: Player with empty status is healthy")

    # Test 3: Injured player with INJ status
    player = Player(
        player_key="466.p.2",
        name="Injured Player",
        position="PG",
        salary=50,
        source=SalarySource.DRAFT,
        status="INJ"
    )
    assert _is_player_healthy(player) is False, "Player with INJ status should not be healthy"
    print("✓ Test 3: Player with INJ status is not healthy")

    # Test 4: OUT player
    player = Player(
        player_key="466.p.3",
        name="Out Player",
        position="SG",
        salary=40,
        source=SalarySource.DRAFT,
        status="OUT"
    )
    assert _is_player_healthy(player) is False, "Player with OUT status should not be healthy"
    print("✓ Test 4: Player with OUT status is not healthy")

    # Test 5: DTD player
    player = Player(
        player_key="466.p.4",
        name="DTD Player",
        position="SF",
        salary=30,
        source=SalarySource.DRAFT,
        status="DTD"
    )
    assert _is_player_healthy(player) is False, "Player with DTD status should not be healthy"
    print("✓ Test 5: Player with DTD status is not healthy")

    # Test 6: GTD player
    player = Player(
        player_key="466.p.5",
        name="GTD Player",
        position="PF",
        salary=20,
        source=SalarySource.DRAFT,
        status="GTD"
    )
    assert _is_player_healthy(player) is False, "Player with GTD status should not be healthy"
    print("✓ Test 6: Player with GTD status is not healthy")


def test_bench_detection():
    """Test bench position detection."""
    print("\n" + "=" * 80)
    print("TEST: Bench Position Detection")
    print("=" * 80)

    # Test 1: Player on bench
    player = Player(
        player_key="466.p.1",
        name="Benched Player",
        position="PG",
        salary=50,
        source=SalarySource.DRAFT,
        roster_position="BN"
    )
    assert _is_benched(player) is True, "Player in BN position should be benched"
    print("✓ Test 1: Player in BN position is benched")

    # Test 2: Player in active lineup
    player = Player(
        player_key="466.p.2",
        name="Active Player",
        position="PG",
        salary=50,
        source=SalarySource.DRAFT,
        roster_position="PG"
    )
    assert _is_benched(player) is False, "Player in active position should not be benched"
    print("✓ Test 2: Player in active position is not benched")

    # Test 3: Player with no roster position
    player = Player(
        player_key="466.p.3",
        name="No Position Player",
        position="SG",
        salary=40,
        source=SalarySource.DRAFT,
        roster_position=None
    )
    assert _is_benched(player) is False, "Player with no roster position should not be benched"
    print("✓ Test 3: Player with no roster position is not benched")


def test_il_detection():
    """Test IL position detection."""
    print("\n" + "=" * 80)
    print("TEST: IL Position Detection")
    print("=" * 80)

    # Test 1: Player on IL
    player = Player(
        player_key="466.p.1",
        name="IL Player",
        position="PG",
        salary=50,
        source=SalarySource.DRAFT,
        roster_position="IL"
    )
    assert _is_on_il(player) is True, "Player in IL position should be on IL"
    print("✓ Test 1: Player in IL position is on IL")

    # Test 2: Player on IL+
    player = Player(
        player_key="466.p.2",
        name="IL+ Player",
        position="SG",
        salary=40,
        source=SalarySource.DRAFT,
        roster_position="IL+"
    )
    assert _is_on_il(player) is True, "Player in IL+ position should be on IL"
    print("✓ Test 2: Player in IL+ position is on IL")

    # Test 3: Player not on IL
    player = Player(
        player_key="466.p.3",
        name="Benched Player",
        position="PG",
        salary=50,
        source=SalarySource.DRAFT,
        roster_position="BN"
    )
    assert _is_on_il(player) is False, "Player in BN position should not be on IL"
    print("✓ Test 3: Player in BN position is not on IL")


def test_game_checking():
    """Test game schedule checking (legacy stats-based approach)."""
    print("\n" + "=" * 80)
    print("TEST: Game Schedule Checking (Legacy)")
    print("=" * 80)

    # Test 1: Player had game (non-zero stats)
    mock_fetcher = Mock()
    mock_stat = Mock()
    mock_stat.stat = Mock()
    mock_stat.stat.value = 10.0  # Non-zero value (actual game)
    mock_stats = Mock()
    mock_stats.stats = [mock_stat]
    mock_player_data = Mock()
    mock_player_data.player_stats = mock_stats
    mock_fetcher.yahoo_query.get_player_stats_by_date.return_value = mock_player_data

    result = check_player_had_game_today_legacy(mock_fetcher, "466.p.1", "2026-01-24")
    assert result is True, "Player with non-zero stats should have had a game"
    print("✓ Test 1: Player with non-zero stats had a game")

    # Test 2: Player no game (empty stats)
    mock_stats.stats = []
    result = check_player_had_game_today_legacy(mock_fetcher, "466.p.1", "2026-01-24")
    assert result is False, "Player with empty stats should not have had a game"
    print("✓ Test 2: Player with empty stats had no game")

    # Test 3: Player no game (all zero stats)
    mock_stat_zero = Mock()
    mock_stat_zero.stat = Mock()
    mock_stat_zero.stat.value = 0.0  # Zero value (no game)
    mock_stats.stats = [mock_stat_zero, mock_stat_zero]
    result = check_player_had_game_today_legacy(mock_fetcher, "466.p.1", "2026-01-24")
    assert result is False, "Player with all zero stats should not have had a game"
    print("✓ Test 3: Player with all zero stats had no game")

    # Test 4: API failure gracefully returns False
    mock_fetcher.yahoo_query.get_player_stats_by_date.side_effect = Exception("API Error")
    result = check_player_had_game_today_legacy(mock_fetcher, "466.p.1", "2026-01-24")
    assert result is False, "API failure should gracefully return False"
    print("✓ Test 4: API failure gracefully returns False")


def test_violation_analysis():
    """Test full violation analysis workflow."""
    print("\n" + "=" * 80)
    print("TEST: Violation Analysis Workflow")
    print("=" * 80)

    # Test 1: Violation detected when all conditions met
    with patch('src.bench_analyzer.check_player_has_game_scheduled') as mock_game_check:
        mock_game_check.return_value = True

        player = Player(
            player_key="466.p.1",
            name="Benched Player",
            position="PG",
            salary=50,
            source=SalarySource.DRAFT,
            nba_team="OKC",
            roster_position="BN",  # Currently benched
            status=None  # Currently healthy
        )

        team = Team(
            team_id="1",
            team_key="466.l.1.t.1",
            team_name="Test Team",
            manager_name="Manager",
            roster=[player],
            total_salary=50,
            faab_remaining=100
        )

        league = League(
            league_id="1",
            league_key="466.l.1",
            league_name="Test League",
            season="2024",
            num_teams=1,
            teams=[team]
        )

        # Run analysis - no service or spreadsheet_id needed
        violations = analyze_bench_violations(
            league=league,
            fetcher=Mock(),
            check_date="2026-01-24"  # TODAY
        )

        assert "Test Team" in violations, "Violation should be detected for Test Team"
        assert len(violations["Test Team"]) == 1, "Should have exactly one violation"
        assert violations["Test Team"][0]['player_name'] == "Benched Player", "Player name should match"
        print("✓ Test 1: Violation detected when all conditions met")

    # Test 2: No violation when player injured
    with patch('src.bench_analyzer.check_player_has_game_scheduled') as mock_game_check:
        mock_game_check.return_value = True

        player = Player(
            player_key="466.p.1",
            name="Injured Player",
            position="PG",
            salary=50,
            source=SalarySource.DRAFT,
            roster_position="BN",  # Currently benched
            status="INJ"  # Currently injured
        )

        team.roster = [player]

        violations = analyze_bench_violations(
            league=league,
            fetcher=Mock(),
            check_date="2026-01-24"
        )

        assert len(violations) == 0, "No violation expected for injured player"
        print("✓ Test 2: No violation when player is injured")


def test_get_teams_with_violations():
    """Test team list extraction."""
    print("\n" + "=" * 80)
    print("TEST: Team List Extraction")
    print("=" * 80)

    # Test 1: Extract sorted team names
    violations = {
        "Team C": [{'player_name': 'Player 1', 'nba_team': 'LAL', 'position': 'PG'}],
        "Team A": [{'player_name': 'Player 2', 'nba_team': 'BOS', 'position': 'SG'}],
        "Team B": [{'player_name': 'Player 3', 'nba_team': 'GSW', 'position': 'SF'}],
    }

    result = get_teams_with_bench_violations(violations)
    assert result == ["Team A", "Team B", "Team C"], "Team names should be sorted"
    print("✓ Test 1: Team names extracted and sorted correctly")

    # Test 2: Empty violations
    violations = {}
    result = get_teams_with_bench_violations(violations)
    assert result == [], "Empty violations should return empty list"
    print("✓ Test 2: Empty violations returns empty list")


def test_is_on_il_or_il_plus():
    """Test IL/IL+ position detection."""
    print("\n" + "=" * 80)
    print("TEST: IL/IL+ Position Detection (New Helper)")
    print("=" * 80)

    # Test 1: Player on IL
    player_il = Player(
        player_key="466.p.1",
        name="Test Player",
        position="PG",
        salary=10,
        source=SalarySource.DRAFT,
        roster_position="IL"
    )
    assert _is_on_il_or_il_plus(player_il) is True, "Player in IL position should be detected"
    print("✓ Test 1: Player in IL position detected")

    # Test 2: Player on IL+
    player_il_plus = Player(
        player_key="466.p.2",
        name="Test Player 2",
        position="SG",
        salary=15,
        source=SalarySource.DRAFT,
        roster_position="IL+"
    )
    assert _is_on_il_or_il_plus(player_il_plus) is True, "Player in IL+ position should be detected"
    print("✓ Test 2: Player in IL+ position detected")

    # Test 3: Player on bench (not IL)
    player_bench = Player(
        player_key="466.p.3",
        name="Test Player 3",
        position="SF",
        salary=20,
        source=SalarySource.DRAFT,
        roster_position="BN"
    )
    assert _is_on_il_or_il_plus(player_bench) is False, "Player on bench should not be detected as IL"
    print("✓ Test 3: Player on bench is not IL/IL+")

    # Test 4: Player with no roster position
    player_no_position = Player(
        player_key="466.p.4",
        name="Test Player 4",
        position="PF",
        salary=25,
        source=SalarySource.DRAFT,
        roster_position=None
    )
    assert _is_on_il_or_il_plus(player_no_position) is False, "Player with no position should not be detected as IL"
    print("✓ Test 4: Player with no roster position is not IL/IL+")


def test_analyze_il_violations():
    """Test IL violation detection for healthy players in IL/IL+ slots."""
    print("\n" + "=" * 80)
    print("TEST: IL Violation Analysis")
    print("=" * 80)

    # Create test players
    healthy_on_il = Player(
        player_key="466.p.1",
        name="Healthy IL Player",
        position="PG",
        salary=10,
        source=SalarySource.DRAFT,
        nba_team="LAL",
        roster_position="IL",
        status=None  # Healthy
    )

    healthy_on_il_plus = Player(
        player_key="466.p.2",
        name="Healthy IL+ Player",
        position="SG",
        salary=15,
        source=SalarySource.DRAFT,
        nba_team="GSW",
        roster_position="IL+",
        status=None  # Healthy
    )

    injured_on_il = Player(
        player_key="466.p.3",
        name="Injured IL Player",
        position="SF",
        salary=20,
        source=SalarySource.DRAFT,
        nba_team="BOS",
        roster_position="IL",
        status="INJ"  # Injured (not a violation)
    )

    healthy_on_bench = Player(
        player_key="466.p.4",
        name="Healthy Bench Player",
        position="PF",
        salary=25,
        source=SalarySource.DRAFT,
        nba_team="MIA",
        roster_position="BN",
        status=None  # Healthy but on bench (not an IL violation)
    )

    # Create test team with violations
    team_with_violations = Team(
        team_id="1",
        team_key="466.l.12345.t.1",
        team_name="Team Alpha",
        manager_name="Manager A",
        roster=[healthy_on_il, healthy_on_il_plus, injured_on_il, healthy_on_bench],
        total_salary=70,
        faab_remaining=100
    )

    # Create test team without violations
    team_without_violations = Team(
        team_id="2",
        team_key="466.l.12345.t.2",
        team_name="Team Beta",
        manager_name="Manager B",
        roster=[injured_on_il, healthy_on_bench],
        total_salary=45,
        faab_remaining=100
    )

    # Create league
    league = League(
        league_id="12345",
        league_key="466.l.12345",
        league_name="Test League",
        season="2024-25",
        num_teams=2,
        teams=[team_with_violations, team_without_violations]
    )

    # Mock fetcher (not used but required by signature)
    fetcher = None

    # Run analysis
    violations = analyze_il_violations(league, fetcher)

    # Verify results
    assert "Team Alpha" in violations, "Team Alpha should have violations"
    assert len(violations["Team Alpha"]) == 2, "Team Alpha should have 2 violations (IL and IL+)"

    assert violations["Team Alpha"][0]['player_name'] == "Healthy IL Player", "First violation should be Healthy IL Player"
    assert violations["Team Alpha"][0]['roster_slot'] == "IL", "First violation should be in IL slot"

    assert violations["Team Alpha"][1]['player_name'] == "Healthy IL+ Player", "Second violation should be Healthy IL+ Player"
    assert violations["Team Alpha"][1]['roster_slot'] == "IL+", "Second violation should be in IL+ slot"

    assert "Team Beta" not in violations, "Team Beta should have no violations"
    print("✓ Test 1: IL violations detected correctly for Team Alpha")
    print("✓ Test 2: No violations detected for Team Beta")


def test_analyze_il_violations_empty_league():
    """Test IL violation analysis with no teams."""
    print("\n" + "=" * 80)
    print("TEST: IL Violation Analysis - Empty League")
    print("=" * 80)

    league = League(
        league_id="12345",
        league_key="466.l.12345",
        league_name="Empty League",
        season="2024-25",
        num_teams=0,
        teams=[]
    )

    violations = analyze_il_violations(league, None)
    assert violations == {}, "Empty league should return empty violations dict"
    print("✓ Test 1: Empty league returns no violations")


def main():
    """Run all bench analyzer tests."""
    print("\n" + "=" * 80)
    print("BENCH ANALYZER MODULE TEST SUITE")
    print("=" * 80)

    try:
        test_player_health_checks()
        test_bench_detection()
        test_il_detection()
        test_game_checking()
        test_violation_analysis()
        test_get_teams_with_violations()
        test_is_on_il_or_il_plus()
        test_analyze_il_violations()
        test_analyze_il_violations_empty_league()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("  • Player health status detection works correctly")
        print("  • Bench position detection works correctly")
        print("  • IL position detection works correctly")
        print("  • IL/IL+ helper function works correctly")
        print("  • IL violation analysis detects healthy players in IL/IL+ slots")
        print("  • Game checking handles API responses and failures")
        print("  • Violation analysis detects bench management issues")
        print("  • Team list extraction works correctly")
        print("\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    main()
