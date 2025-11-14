#!/usr/bin/env python3
"""
Salary Data Investigation Script

This script systematically explores Yahoo Fantasy API data structures
to determine how to access player salary/auction price information.
"""

import json
from typing import Any
from src.yahoo_data_fetcher import YahooDataFetcher
from src.logger import logger


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def inspect_object(obj: Any, name: str, max_depth: int = 3, current_depth: int = 0):
    """
    Recursively inspect an object and print its attributes.

    Args:
        obj: Object to inspect
        name: Name of the object for display
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
    """
    indent = "  " * current_depth

    # Handle None
    if obj is None:
        print(f"{indent}{name}: None")
        return

    # Handle primitives
    if isinstance(obj, (str, int, float, bool)):
        print(f"{indent}{name}: {obj} ({type(obj).__name__})")
        return

    # Handle lists
    if isinstance(obj, list):
        print(f"{indent}{name}: List with {len(obj)} items")
        if current_depth < max_depth and len(obj) > 0:
            print(f"{indent}  [Showing first item]")
            inspect_object(obj[0], f"{name}[0]", max_depth, current_depth + 1)
        return

    # Handle dictionaries
    if isinstance(obj, dict):
        print(f"{indent}{name}: Dict with {len(obj)} keys")
        if current_depth < max_depth:
            for key, value in obj.items():
                inspect_object(value, f"{name}['{key}']", max_depth, current_depth + 1)
        return

    # Handle custom objects
    print(f"{indent}{name}: {type(obj).__name__} object")

    if current_depth >= max_depth:
        print(f"{indent}  ... (max depth reached)")
        return

    # Get all attributes (excluding private ones starting with _)
    attrs = [attr for attr in dir(obj) if not attr.startswith('_') and not callable(getattr(obj, attr, None))]

    if attrs:
        print(f"{indent}  Attributes ({len(attrs)}):")
        for attr in sorted(attrs):
            try:
                value = getattr(obj, attr)
                # For nested objects, limit depth
                if isinstance(value, (str, int, float, bool, type(None))):
                    print(f"{indent}    {attr}: {value}")
                elif isinstance(value, list):
                    print(f"{indent}    {attr}: List[{len(value)}]")
                elif isinstance(value, dict):
                    print(f"{indent}    {attr}: Dict[{len(value)}]")
                else:
                    print(f"{indent}    {attr}: {type(value).__name__}")
                    # Only recurse for important looking attributes
                    if current_depth < max_depth - 1 and attr in [
                        'team', 'teams', 'player', 'players', 'roster',
                        'draft_results', 'settings', 'auction', 'contract',
                        'salary', 'price', 'cost', 'budget'
                    ]:
                        inspect_object(value, f"{name}.{attr}", max_depth, current_depth + 1)
            except Exception as e:
                print(f"{indent}    {attr}: <Error accessing: {e}>")


def search_for_keywords(obj: Any, keywords: list[str], path: str = "root") -> list[str]:
    """
    Recursively search for attributes containing specific keywords.

    Args:
        obj: Object to search
        keywords: List of keywords to search for (case-insensitive)
        path: Current path in object tree

    Returns:
        List of paths where keywords were found
    """
    findings = []

    if obj is None or isinstance(obj, (str, int, float, bool)):
        return findings

    # Search in lists
    if isinstance(obj, list):
        for i, item in enumerate(obj[:5]):  # Check first 5 items
            findings.extend(search_for_keywords(item, keywords, f"{path}[{i}]"))
        return findings

    # Search in dicts
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Check if key matches any keyword
            if any(keyword.lower() in str(key).lower() for keyword in keywords):
                findings.append(f"{path}.{key} = {value}")
            findings.extend(search_for_keywords(value, keywords, f"{path}.{key}"))
        return findings

    # Search in custom objects
    try:
        attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
        for attr in attrs:
            # Check if attribute name matches any keyword
            if any(keyword.lower() in attr.lower() for keyword in keywords):
                try:
                    value = getattr(obj, attr)
                    findings.append(f"{path}.{attr} = {value}")
                except:
                    findings.append(f"{path}.{attr} = <error accessing>")

            # Recurse into the attribute
            try:
                value = getattr(obj, attr)
                if not callable(value):
                    findings.extend(search_for_keywords(value, keywords, f"{path}.{attr}"))
            except:
                pass
    except:
        pass

    return findings


def main():
    """Main investigation function."""
    print_section("YAHOO FANTASY API - SALARY DATA INVESTIGATION")

    print("Initializing Yahoo API client...")
    fetcher = YahooDataFetcher(browser_callback=False)

    # Keywords related to salary/money/auction
    salary_keywords = [
        'salary', 'salaries', 'auction', 'price', 'cost', 'budget',
        'contract', 'money', 'paid', 'spend', 'spent', 'keeper',
        'draft_price', 'draft_cost', 'bid', 'amount'
    ]

    all_findings = []

    # =========================================================================
    # 1. LEAGUE INFO
    # =========================================================================
    print_section("1. LEAGUE INFO")
    try:
        league_info = fetcher.get_league_info()
        print("League Info Object Structure:")
        inspect_object(league_info, "league_info", max_depth=3)

        print("\n--- Searching for salary-related keywords in league info ---")
        findings = search_for_keywords(league_info, salary_keywords, "league_info")
        if findings:
            for finding in findings:
                print(f"  ✓ {finding}")
                all_findings.append(("League Info", finding))
        else:
            print("  No salary-related fields found")
    except Exception as e:
        logger.error(f"Error fetching league info: {e}")

    # =========================================================================
    # 2. LEAGUE METADATA
    # =========================================================================
    print_section("2. LEAGUE METADATA")
    try:
        metadata = fetcher.get_league_metadata()
        print("League Metadata Object Structure:")
        inspect_object(metadata, "metadata", max_depth=3)

        print("\n--- Searching for salary-related keywords in metadata ---")
        findings = search_for_keywords(metadata, salary_keywords, "metadata")
        if findings:
            for finding in findings:
                print(f"  ✓ {finding}")
                all_findings.append(("Metadata", finding))
        else:
            print("  No salary-related fields found")
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}")

    # =========================================================================
    # 3. LEAGUE TEAMS
    # =========================================================================
    print_section("3. LEAGUE TEAMS")
    try:
        teams = fetcher.get_league_teams()
        print(f"Retrieved {len(teams) if hasattr(teams, '__len__') else '?'} teams")
        print("\nFirst Team Object Structure:")
        if teams and len(teams) > 0:
            first_team = teams[0]
            inspect_object(first_team, "team", max_depth=3)

            print("\n--- Searching for salary-related keywords in team data ---")
            findings = search_for_keywords(first_team, salary_keywords, "team")
            if findings:
                for finding in findings:
                    print(f"  ✓ {finding}")
                    all_findings.append(("Team", finding))
            else:
                print("  No salary-related fields found")
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")

    # =========================================================================
    # 4. TEAM ROSTER
    # =========================================================================
    print_section("4. TEAM ROSTER")
    try:
        # Get first team's roster
        teams = fetcher.get_league_teams()
        if teams and len(teams) > 0:
            first_team = teams[0]
            team_id = first_team.team_id if hasattr(first_team, 'team_id') else first_team.team_key
            print(f"Getting roster for team: {team_id}")

            roster = fetcher.get_team_roster(team_id)
            print(f"Retrieved roster with {len(roster) if hasattr(roster, '__len__') else '?'} players")

            print("\nFirst Player Object Structure:")
            if roster and len(roster) > 0:
                first_player = roster[0]
                inspect_object(first_player, "player", max_depth=4)

                print("\n--- Searching for salary-related keywords in player data ---")
                findings = search_for_keywords(first_player, salary_keywords, "player")
                if findings:
                    for finding in findings:
                        print(f"  ✓ {finding}")
                        all_findings.append(("Player/Roster", finding))
                else:
                    print("  No salary-related fields found")
    except Exception as e:
        logger.error(f"Error fetching team roster: {e}")

    # =========================================================================
    # 5. DRAFT RESULTS
    # =========================================================================
    print_section("5. DRAFT RESULTS")
    try:
        draft_results = fetcher.get_league_draft_results()
        print("Draft Results Object Structure:")
        inspect_object(draft_results, "draft_results", max_depth=3)

        print("\n--- Searching for salary-related keywords in draft results ---")
        findings = search_for_keywords(draft_results, salary_keywords, "draft_results")
        if findings:
            for finding in findings:
                print(f"  ✓ {finding}")
                all_findings.append(("Draft Results", finding))
        else:
            print("  No salary-related fields found")
    except Exception as e:
        logger.error(f"Error fetching draft results: {e}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("SUMMARY OF FINDINGS")

    if all_findings:
        print(f"Found {len(all_findings)} salary-related data points:\n")
        for source, finding in all_findings:
            print(f"[{source}] {finding}")
    else:
        print("❌ No salary-related fields found in any API responses")
        print("\nThis suggests that salary data may not be directly available through the Yahoo API.")
        print("Possible fallback strategies:")
        print("  1. Use draft auction prices as 'salary'")
        print("  2. Manually maintain salary data")
        print("  3. Use external data sources")

    print("\n" + "=" * 80)
    print("Investigation complete. Check output above for detailed findings.")
    print("=" * 80)


if __name__ == "__main__":
    main()
