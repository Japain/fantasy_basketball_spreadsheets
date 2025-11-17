"""
Data models for Fantasy Basketball application.

Defines the structure for Player, Team, and League data extracted from Yahoo Fantasy API.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any


class SalarySource(Enum):
    """Enum representing how a player was acquired and their salary determined."""
    KEEPER = "Keeper"
    DRAFT = "Draft"
    FAAB_WAIVER = "FAAB Waiver"
    FREE_AGENT = "Free Agent"


class TransactionType(Enum):
    """Enum representing types of transactions."""
    ADD = "add"
    DROP = "drop"
    TRADE = "trade"
    ADD_DROP = "add/drop"


@dataclass
class Player:
    """
    Represents a player on a team's roster.

    Attributes:
        player_key: Yahoo's unique identifier for the player (e.g., '466.p.6022')
        name: Player's full name
        position: Current display position (e.g., 'PG', 'SG,SF', 'C')
        salary: Player's current salary/cost
        source: How the player was acquired (determines salary source)
        nba_team: Player's NBA team abbreviation (e.g., 'OKC', 'LAL')
        roster_position: Current roster slot (e.g., 'PG', 'BN', 'IL', 'IL+')
    """
    player_key: str
    name: str
    position: str
    salary: int
    source: SalarySource
    nba_team: Optional[str] = None
    roster_position: Optional[str] = None

    def __str__(self) -> str:
        """String representation of player."""
        team_str = f" ({self.nba_team})" if self.nba_team else ""
        slot_str = f" [{self.roster_position}]" if self.roster_position else ""
        return f"{self.name}{team_str}{slot_str} - {self.position} - ${self.salary} ({self.source.value})"


@dataclass
class TransactionInfo:
    """
    Represents a transaction that affects a team's roster.

    Used for tracking roster changes to determine which teams need updates
    in incremental sheet update mode.

    Attributes:
        transaction_id: Yahoo's unique identifier for the transaction
        timestamp: Unix timestamp of when the transaction occurred
        team_id: Yahoo team ID involved in the transaction
        team_name: Name of the team involved
        transaction_type: Type of transaction (add, drop, trade, add/drop)
        player_name: Name of the player involved
        faab_bid: FAAB bid amount for waiver claims (None for free agents or trades)
    """
    transaction_id: str
    timestamp: int
    team_id: str
    team_name: str
    transaction_type: TransactionType
    player_name: str
    faab_bid: Optional[int] = None

    def __str__(self) -> str:
        """String representation of transaction."""
        faab_str = f" (${self.faab_bid} FAAB)" if self.faab_bid is not None else ""
        return f"{self.team_name}: {self.transaction_type.value} {self.player_name}{faab_str}"


@dataclass
class Team:
    """
    Represents a fantasy basketball team.

    Attributes:
        team_id: Yahoo's team identifier
        team_key: Yahoo's full team key (e.g., '466.l.68958.t.1')
        team_name: Name of the fantasy team
        manager_name: Name of the team manager
        roster: List of players on the team
        total_salary: Sum of all player salaries on the roster
        faab_remaining: Remaining FAAB budget for waiver acquisitions
        initial_budget: Initial budget for auction draft (typically $200)
    """
    team_id: str
    team_key: str
    team_name: str
    manager_name: str
    roster: List[Player] = field(default_factory=list)
    total_salary: int = 0
    faab_remaining: int = 0
    initial_budget: int = 225

    def __str__(self) -> str:
        """String representation of team."""
        return f"{self.team_name} (Manager: {self.manager_name}) - {len(self.roster)} players, ${self.total_salary} spent, ${self.faab_remaining} FAAB remaining"

    def calculate_total_salary(self) -> int:
        """
        Calculate and return total salary of all players on roster.

        Excludes players in IL (Injured List) or IL+ positions as they
        don't count against the salary cap.
        """
        return sum(
            player.salary
            for player in self.roster
            if player.roster_position not in ('IL', 'IL+')
        )

    def add_player(self, player: Player) -> None:
        """
        Add a player to the roster and update total salary.

        Args:
            player: Player to add to the roster
        """
        self.roster.append(player)
        self.total_salary = self.calculate_total_salary()

    def get_salary_breakdown(self) -> dict:
        """
        Get breakdown of salaries by acquisition source.

        Returns:
            Dictionary mapping source type to total salary from that source
        """
        breakdown = {source: 0 for source in SalarySource}
        for player in self.roster:
            breakdown[player.source] += player.salary
        return breakdown

    def get_remaining_salary(self) -> int:
        """
        Calculate remaining salary budget.

        Returns:
            Remaining salary budget (initial_budget - total_salary)
        """
        return self.initial_budget - self.total_salary


@dataclass
class League:
    """
    Represents a fantasy basketball league.

    Attributes:
        league_id: Yahoo's league identifier
        league_key: Yahoo's full league key (e.g., '466.l.68958')
        league_name: Name of the league
        season: Season year
        num_teams: Number of teams in the league
        teams: List of all teams in the league
    """
    league_id: str
    league_key: str
    league_name: str
    season: str
    num_teams: int
    teams: List[Team] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation of league."""
        return f"{self.league_name} (Season {self.season}) - {self.num_teams} teams"

    def add_team(self, team: Team) -> None:
        """
        Add a team to the league.

        Args:
            team: Team to add to the league
        """
        self.teams.append(team)

    def get_team_by_id(self, team_id: str) -> Optional[Team]:
        """
        Get a team by its ID.

        Args:
            team_id: The team ID to search for

        Returns:
            Team object if found, None otherwise
        """
        for team in self.teams:
            if team.team_id == team_id:
                return team
        return None

    def get_team_by_name(self, team_name: str) -> Optional[Team]:
        """
        Get a team by its name.

        Args:
            team_name: The team name to search for

        Returns:
            Team object if found, None otherwise
        """
        for team in self.teams:
            if team.team_name == team_name:
                return team
        return None

    def get_total_players(self) -> int:
        """Get total number of players across all teams."""
        return sum(len(team.roster) for team in self.teams)

    def get_league_stats(self) -> dict:
        """
        Get aggregate statistics for the league.

        Returns:
            Dictionary with league-wide statistics
        """
        total_players = self.get_total_players()
        total_salary = sum(team.total_salary for team in self.teams)
        total_faab_remaining = sum(team.faab_remaining for team in self.teams)

        return {
            'num_teams': self.num_teams,
            'total_players': total_players,
            'avg_roster_size': total_players / self.num_teams if self.num_teams > 0 else 0,
            'total_salary_spent': total_salary,
            'avg_salary_per_team': total_salary / self.num_teams if self.num_teams > 0 else 0,
            'total_faab_remaining': total_faab_remaining,
            'avg_faab_remaining': total_faab_remaining / self.num_teams if self.num_teams > 0 else 0,
        }


def create_player_from_yahoo_data(
    player_key: str,
    name: str,
    position: str,
    salary: int,
    source: SalarySource,
    nba_team: Optional[str] = None,
    roster_position: Optional[str] = None
) -> Player:
    """
    Factory function to create a Player from Yahoo API data.

    Args:
        player_key: Yahoo's unique player identifier
        name: Player's full name
        position: Display position
        salary: Player salary/cost
        source: How the player was acquired
        nba_team: NBA team abbreviation (optional)
        roster_position: Current roster slot (e.g., 'PG', 'BN', 'IL', 'IL+') (optional)

    Returns:
        Player instance
    """
    return Player(
        player_key=player_key,
        name=name,
        position=position,
        salary=salary,
        source=source,
        nba_team=nba_team,
        roster_position=roster_position
    )


def create_team_from_yahoo_data(
    team_id: str,
    team_key: str,
    team_name: str,
    manager_name: str,
    faab_remaining: int = 0,
    initial_budget: int = 200
) -> Team:
    """
    Factory function to create a Team from Yahoo API data.

    Args:
        team_id: Yahoo's team identifier
        team_key: Yahoo's full team key
        team_name: Fantasy team name
        manager_name: Manager's name
        faab_remaining: Remaining FAAB budget
        initial_budget: Initial auction budget

    Returns:
        Team instance
    """
    return Team(
        team_id=team_id,
        team_key=team_key,
        team_name=team_name,
        manager_name=manager_name,
        faab_remaining=faab_remaining,
        initial_budget=initial_budget
    )


def create_league_from_yahoo_data(
    league_id: str,
    league_key: str,
    league_name: str,
    season: str,
    num_teams: int
) -> League:
    """
    Factory function to create a League from Yahoo API data.

    Args:
        league_id: Yahoo's league identifier
        league_key: Yahoo's full league key
        league_name: League name
        season: Season year
        num_teams: Number of teams in the league

    Returns:
        League instance
    """
    return League(
        league_id=league_id,
        league_key=league_key,
        league_name=league_name,
        season=season,
        num_teams=num_teams
    )


def create_transaction_from_yahoo(
    transaction_id: str,
    timestamp: int,
    team_id: str,
    team_name: str,
    transaction_type: TransactionType,
    player_name: str,
    faab_bid: Optional[int] = None
) -> TransactionInfo:
    """
    Factory function to create a TransactionInfo from Yahoo API data.

    Args:
        transaction_id: Yahoo's transaction identifier
        timestamp: Unix timestamp of transaction
        team_id: Yahoo team ID
        team_name: Team name
        transaction_type: Type of transaction
        player_name: Name of player involved
        faab_bid: FAAB bid amount (optional)

    Returns:
        TransactionInfo instance
    """
    return TransactionInfo(
        transaction_id=transaction_id,
        timestamp=timestamp,
        team_id=team_id,
        team_name=team_name,
        transaction_type=transaction_type,
        player_name=player_name,
        faab_bid=faab_bid
    )
