"""
Test proactive bench analyzer functionality.

Tests the new schedule-based game checking for proactive bench alerts (v2.8),
including violation detection, no-game scenarios, free agents, and API failures.
"""

from unittest.mock import Mock, patch
from src.bench_analyzer import (
    check_player_has_game_scheduled,
    analyze_bench_violations,
    _count_active_spots_without_games,
    USE_PROACTIVE_SCHEDULE_CHECK,
)
from src.data_models import Player, Team, League, SalarySource
from src.logger import get_logger

logger = get_logger(__name__)


def test_schedule_based_game_checking():
    """Test the new schedule-based game checking function."""
    print("\n" + "=" * 80)
    print("TEST: Schedule-Based Game Checking")
    print("=" * 80)

    # Test 1: Player's team has game
    with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
        mock_get_teams.return_value = {"PHX", "LAL", "GSW"}

        player = Player(
            player_key="466.p.6022",
            name="Kevin Durant",
            position="SF,PF",
            salary=50,
            source=SalarySource.DRAFT,
            status=None,
            nba_team="PHX",
            roster_position="BN"
        )

        has_game = check_player_has_game_scheduled(player, "2026-01-24")
        assert has_game is True, "Player's team has game, should return True"
        mock_get_teams.assert_called_once_with("2026-01-24")
        print("✓ Test 1: Correctly detects when player's team has game")

    # Test 2: Player's team has NO game
    with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
        mock_get_teams.return_value = {"LAL", "GSW", "BOS"}  # PHX not in list

        player = Player(
            player_key="466.p.6022",
            name="Kevin Durant",
            position="SF,PF",
            salary=50,
            source=SalarySource.DRAFT,
            status=None,
            nba_team="PHX",
            roster_position="BN"
        )

        has_game = check_player_has_game_scheduled(player, "2026-01-24")
        assert has_game is False, "Player's team has no game, should return False"
        print("✓ Test 2: Correctly detects when player's team has no game")

    # Test 3: Free agent (no NBA team)
    with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
        player = Player(
            player_key="466.p.9999",
            name="Free Agent",
            position="PG",
            salary=0,
            source=SalarySource.FREE_AGENT,
            status=None,
            nba_team=None,  # Free agent
            roster_position="BN"
        )

        has_game = check_player_has_game_scheduled(player, "2026-01-24")
        assert has_game is False, "Free agent should return False"
        mock_get_teams.assert_not_called()  # Should not call API
        print("✓ Test 3: Correctly handles free agents (no API call)")

    # Test 4: API failure - graceful degradation
    with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
        mock_get_teams.side_effect = Exception("API connection failed")

        player = Player(
            player_key="466.p.6022",
            name="Kevin Durant",
            position="SF,PF",
            salary=50,
            source=SalarySource.DRAFT,
            status=None,
            nba_team="PHX",
            roster_position="BN"
        )

        has_game = check_player_has_game_scheduled(player, "2026-01-24")
        assert has_game is False, "API failure should gracefully return False"
        print("✓ Test 4: Gracefully handles API failures")

    # Test 5: Empty schedule (off-season)
    with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
        mock_get_teams.return_value = set()  # No games

        player = Player(
            player_key="466.p.6022",
            name="Kevin Durant",
            position="SF,PF",
            salary=50,
            source=SalarySource.DRAFT,
            status=None,
            nba_team="PHX",
            roster_position="BN"
        )

        has_game = check_player_has_game_scheduled(player, "2026-06-01")
        assert has_game is False, "Empty schedule should return False"
        print("✓ Test 5: Correctly handles empty schedules (off-season)")


def test_proactive_violation_detection():
    """Test full violation detection workflow with schedule-based checking."""
    print("\n" + "=" * 80)
    print("TEST: Proactive Violation Detection")
    print("=" * 80)

    mock_fetcher = Mock()

    # Test 1: Violation detected
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX", "LAL"}

            team = Team(
                team_id="1",
                team_key="466.l.12345.t.1",
                team_name="Test Team",
                manager_name="Test Manager",
                roster=[
                    Player(
                        player_key="466.p.6022",
                        name="Kevin Durant",
                        position="SF,PF",
                        salary=50,
                        source=SalarySource.DRAFT,
                        status=None,  # Healthy
                        nba_team="PHX",  # Has game
                        roster_position="BN"  # Benched
                    )
                ]
            )

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 1, "Should detect one team with violation"
            assert "Test Team" in violations, "Violation should be for Test Team"
            assert len(violations["Test Team"]) == 1, "Should have one violation"
            assert violations["Test Team"][0]["player_name"] == "Kevin Durant"
            print("✓ Test 1: Violation detected with schedule-based approach")

    # Test 2: No violation when team has no game
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"LAL", "GSW"}  # PHX not playing

            team = Team(
                team_id="1",
                team_name="Test Team",
                team_key="466.l.12345.t.1",
                manager_name="Test Manager",
                roster=[
                    Player(
                        player_key="466.p.6022",
                        name="Kevin Durant",
                        position="SF,PF",
                        salary=50,
                        source=SalarySource.DRAFT,
                        status=None,  # Healthy
                        nba_team="PHX",  # NO game
                        roster_position="BN"  # Benched
                    )
                ])

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 0, "Should not detect violation when no game"
            print("✓ Test 2: No violation when team has no game")

    # Test 3: No violation when player injured
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX", "LAL"}

            team = Team(
                team_id="1",
                team_name="Test Team",
                team_key="466.l.12345.t.1",
                manager_name="Test Manager",
                roster=[
                    Player(
                        player_key="466.p.6022",
                        name="Kevin Durant",
                        position="SF,PF",
                        salary=50,
                        source=SalarySource.DRAFT,
                        status="INJ",  # Injured
                        nba_team="PHX",  # Has game
                        roster_position="BN"  # Benched
                    )
                ])

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 0, "Should not detect violation when injured"
            print("✓ Test 3: No violation when player is injured")

    # Test 4: No violation when player on IL
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX", "LAL"}

            team = Team(
                team_id="1",
                team_name="Test Team",
                team_key="466.l.12345.t.1",
                manager_name="Test Manager",
                roster=[
                    Player(
                        player_key="466.p.6022",
                        name="Kevin Durant",
                        position="SF,PF",
                        salary=50,
                        source=SalarySource.DRAFT,
                        status=None,  # Healthy
                        nba_team="PHX",  # Has game
                        roster_position="IL"  # On IL
                    )
                ])

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 0, "Should not detect violation when on IL"
            print("✓ Test 4: No violation when player on IL")

    # Test 5: No violation when player in active lineup
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX", "LAL"}

            team = Team(
                team_id="1",
                team_name="Test Team",
                team_key="466.l.12345.t.1",
                manager_name="Test Manager",
                roster=[
                    Player(
                        player_key="466.p.6022",
                        name="Kevin Durant",
                        position="SF,PF",
                        salary=50,
                        source=SalarySource.DRAFT,
                        status=None,  # Healthy
                        nba_team="PHX",  # Has game
                        roster_position="SF"  # Active
                    )
                ])

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 0, "Should not detect violation when active"
            print("✓ Test 5: No violation when player in active lineup")


def test_multiple_violations():
    """Test multiple violations for one team and across teams."""
    print("\n" + "=" * 80)
    print("TEST: Multiple Violations")
    print("=" * 80)

    mock_fetcher = Mock()

    # Test 1: Multiple violations for one team
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX", "LAL", "GSW"}

            team = Team(
                team_id="1",
                team_name="Test Team",
                team_key="466.l.12345.t.1",
                manager_name="Test Manager",
                roster=[
                    Player(
                        player_key="466.p.6022",
                        name="Kevin Durant",
                        position="SF,PF",
                        salary=50,
                        source=SalarySource.DRAFT,
                        status=None,
                        nba_team="PHX",
                        roster_position="BN"
                    ),
                    Player(
                        player_key="466.p.5007",
                        name="LeBron James",
                        position="SF,PF",
                        salary=55,
                        source=SalarySource.DRAFT,
                        status=None,
                        nba_team="LAL",
                        roster_position="BN"
                    ),
                    Player(
                        player_key="466.p.5992",
                        name="Stephen Curry",
                        position="PG,SG",
                        salary=60,
                        source=SalarySource.DRAFT,
                        status=None,
                        nba_team="GSW",
                        roster_position="BN"
                    )
                ])

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 1, "Should have one team with violations"
            assert "Test Team" in violations
            assert len(violations["Test Team"]) == 3, "Should have 3 violations"

            player_names = {v["player_name"] for v in violations["Test Team"]}
            assert player_names == {"Kevin Durant", "LeBron James", "Stephen Curry"}
            print("✓ Test 1: Multiple violations detected for one team")

    # Test 2: Violations across multiple teams
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX", "LAL"}

            team1 = Team(
                team_id="1",
                team_name="Team Alpha",
                team_key="466.l.12345.t.1",
                manager_name="Manager 1",
                roster=[
                    Player(
                        player_key="466.p.6022",
                        name="Kevin Durant",
                        position="SF,PF",
                        salary=50,
                        source=SalarySource.DRAFT,
                        status=None,
                        nba_team="PHX",
                        roster_position="BN"
                    )
                ])

            team2 = Team(
                team_id="2",
                team_name="Team Beta",
                team_key="466.l.12345.t.2",
                manager_name="Manager 2",
                roster=[
                    Player(
                        player_key="466.p.5007",
                        name="LeBron James",
                        position="SF,PF",
                        salary=55,
                        source=SalarySource.DRAFT,
                        status=None,
                        nba_team="LAL",
                        roster_position="BN"
                    )
                ])

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team1, team2]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 2, "Should have violations for both teams"
            assert "Team Alpha" in violations
            assert "Team Beta" in violations
            assert violations["Team Alpha"][0]["player_name"] == "Kevin Durant"
            assert violations["Team Beta"][0]["player_name"] == "LeBron James"
            print("✓ Test 2: Violations detected across multiple teams")


def test_active_roster_spots():
    """Test active roster spot counting and optimal lineup logic."""
    print("\n" + "=" * 80)
    print("TEST: Active Roster Spots")
    print("=" * 80)

    mock_fetcher = Mock()

    # Test 1: Count active roster spots without games
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"BOS", "PHX"}  # Only BOS and PHX have games

            roster = [
                Player(player_key="1", name="PG", position="PG", salary=50, source=SalarySource.DRAFT,
                       nba_team="BOS", roster_position="PG"),  # Has game
                Player(player_key="2", name="SG", position="SG", salary=50, source=SalarySource.DRAFT,
                       nba_team="LAL", roster_position="SG"),  # No game
                Player(player_key="3", name="SF", position="SF", salary=50, source=SalarySource.DRAFT,
                       nba_team="BOS", roster_position="SF"),  # Has game
                Player(player_key="4", name="PF", position="PF", salary=50, source=SalarySource.DRAFT,
                       nba_team="GSW", roster_position="PF"),  # No game
                Player(player_key="5", name="C", position="C", salary=50, source=SalarySource.DRAFT,
                       nba_team="BOS", roster_position="C"),  # Has game
                # Only 5 active players (5 empty spots)
                Player(player_key="11", name="Bench 1", position="PF", salary=50, source=SalarySource.DRAFT,
                       nba_team="PHX", roster_position="BN"),
            ]

            spots_without_games = _count_active_spots_without_games(roster, "2026-01-24")
            # 3 active with games (BOS players), so 10 - 3 = 7 spots without games
            assert spots_without_games == 7, f"Should count 7 spots without games, got {spots_without_games}"
            print("✓ Test 1: Correctly counts active spots without games (3 with games, 7 without)")

    # Test 2: No violation when all 10 active spots have games (optimal lineup)
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"BOS", "PHX", "LAL"}  # All teams have games

            team = Team(
                team_id="1",
                team_key="466.l.12345.t.1",
                team_name="Optimal Lineup Team",
                manager_name="Test Manager",
                roster=[
                    # 10 active players - ALL with games today
                    Player(player_key="1", name="PG", position="PG", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="PG"),  # Has game
                    Player(player_key="2", name="SG", position="SG", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="SG"),  # Has game
                    Player(player_key="3", name="SF", position="SF", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="SF"),  # Has game
                    Player(player_key="4", name="PF", position="PF", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="PF"),  # Has game
                    Player(player_key="5", name="C", position="C", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="C"),  # Has game
                    Player(player_key="6", name="G", position="G", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="G"),  # Has game
                    Player(player_key="7", name="F", position="F", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="F"),  # Has game
                    Player(player_key="8", name="UTIL1", position="PG", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="UTIL"),  # Has game
                    Player(player_key="9", name="UTIL2", position="SG", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="UTIL"),  # Has game
                    Player(player_key="10", name="UTIL3", position="SF", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="UTIL"),  # Has game
                    # Benched players with games (should NOT be violations - all active spots have games)
                    Player(player_key="11", name="Benched Player 1", position="PF", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="PHX", roster_position="BN"),  # Has game
                    Player(player_key="12", name="Benched Player 2", position="C", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="LAL", roster_position="BN"),  # Has game
                ]
            )

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 0, "Should not flag violations when all active spots have games"
            print("✓ Test 2: No violation when all 10 active spots have games (optimal lineup)")

    # Test 3: Violation when active player has no game but benched player does
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX", "BOS"}

            team = Team(
                team_id="1",
                team_key="466.l.12345.t.1",
                team_name="Suboptimal Lineup Team",
                manager_name="Test Manager",
                roster=[
                    # 10 active players - but some don't have games
                    Player(player_key="1", name="PG", position="PG", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="PG"),  # Has game
                    Player(player_key="2", name="SG", position="SG", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="LAL", roster_position="SG"),  # NO game
                    Player(player_key="3", name="SF", position="SF", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="SF"),  # Has game
                    Player(player_key="4", name="PF", position="PF", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="GSW", roster_position="PF"),  # NO game
                    Player(player_key="5", name="C", position="C", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="C"),  # Has game
                    Player(player_key="6", name="G", position="G", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="G"),  # Has game
                    Player(player_key="7", name="F", position="F", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="F"),  # Has game
                    Player(player_key="8", name="UTIL1", position="PG", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="UTIL"),  # Has game
                    Player(player_key="9", name="UTIL2", position="SG", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="UTIL"),  # Has game
                    Player(player_key="10", name="UTIL3", position="SF", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="BOS", roster_position="UTIL"),  # Has game
                    # Benched player with game (SHOULD be violation - could swap with LAL or GSW players)
                    Player(player_key="11", name="Benched Player", position="PF", salary=50, source=SalarySource.DRAFT,
                           status=None, nba_team="PHX", roster_position="BN"),  # Has game
                ]
            )

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 1, "Should flag violation when active players lack games but benched player has game"
            assert "Suboptimal Lineup Team" in violations
            assert len(violations["Suboptimal Lineup Team"]) == 1
            print("✓ Test 3: Violation detected when active player has no game but benched player does")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 80)
    print("TEST: Edge Cases")
    print("=" * 80)

    mock_fetcher = Mock()

    # Test 1: Empty roster
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX"}

            team = Team(
                team_id="1",
                team_name="Test Team",
                team_key="466.l.12345.t.1",
                manager_name="Test Manager",
                roster=[],  # Empty
                
            )

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 0, "Empty roster should not crash"
            print("✓ Test 1: Empty roster handled correctly")

    # Test 2: Free agent on bench
    with patch('src.bench_analyzer.USE_PROACTIVE_SCHEDULE_CHECK', True):
        with patch('src.bench_analyzer.get_teams_with_games_today') as mock_get_teams:
            mock_get_teams.return_value = {"PHX"}

            team = Team(
                team_id="1",
                team_name="Test Team",
                team_key="466.l.12345.t.1",
                manager_name="Test Manager",
                roster=[
                    Player(
                        player_key="466.p.9999",
                        name="Free Agent",
                        position="PG",
                        salary=0,
                        source=SalarySource.FREE_AGENT,
                        status=None,
                        nba_team=None,  # No team
                        roster_position="BN"
                    )
                ])

            league = League(
                league_id="12345",
                league_key="466.l.12345",
                league_name="Test League",
                season="2024",
                num_teams=1,
                teams=[team]
            )

            violations = analyze_bench_violations(league, mock_fetcher, "2026-01-24")
            assert len(violations) == 0, "Free agent should not trigger violation"
            print("✓ Test 2: Free agent on bench handled correctly")


def main():
    """Run all proactive bench analyzer tests."""
    print("\n" + "=" * 80)
    print("PROACTIVE BENCH ANALYZER MODULE TEST SUITE")
    print("=" * 80)

    try:
        test_schedule_based_game_checking()
        test_proactive_violation_detection()
        test_multiple_violations()
        test_active_roster_spots()
        test_edge_cases()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("  • Schedule-based game checking works correctly")
        print("  • Proactive violation detection works correctly")
        print("  • Multiple violations detected accurately")
        print("  • Optimal lineup logic works correctly")
        print("    - No violations when all active spots have games")
        print("    - Violations when active spots lack games but bench has games")
        print("  • Edge cases handled gracefully")
        print("  • Free agents and API failures handled properly")
        print("\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    main()
