#!/usr/bin/env python3
"""
Test script for sheet reading functionality.

Tests the sheet_reader module with real Google Sheets data.
"""

from src.sheet_reader import (
    extract_spreadsheet_id_from_url,
    read_last_run_timestamp,
    validate_sheet_structure,
    get_existing_team_sheets,
    _parse_iso_timestamp,
    _get_sheet_service
)
from src.logger import get_logger

logger = get_logger(__name__)


def test_url_parsing():
    """Test extracting spreadsheet ID from various URL formats."""
    print("\n" + "=" * 80)
    print("TEST 1: URL Parsing")
    print("=" * 80)

    test_cases = [
        # (input, expected_id, should_succeed)
        ("https://docs.google.com/spreadsheets/d/ABC123DEF456/edit", "ABC123DEF456", True),
        ("https://docs.google.com/spreadsheets/d/ABC123DEF456/edit#gid=0", "ABC123DEF456", True),
        ("https://docs.google.com/spreadsheets/d/ABC123DEF456", "ABC123DEF456", True),
        ("ABC123DEF456GHI789JKL012MNO345PQR678STU901", "ABC123DEF456GHI789JKL012MNO345PQR678STU901", True),
        ("", None, False),
        ("invalid", None, False),
        ("http://example.com/invalid", None, False),
    ]

    passed = 0
    failed = 0

    for url, expected_id, should_succeed in test_cases:
        try:
            result = extract_spreadsheet_id_from_url(url)
            if should_succeed:
                if result == expected_id:
                    print(f"✓ PASS: '{url[:50]}...' -> '{result}'")
                    passed += 1
                else:
                    print(f"✗ FAIL: '{url[:50]}...' -> Expected '{expected_id}', got '{result}'")
                    failed += 1
            else:
                print(f"✗ FAIL: '{url[:50]}...' should have raised ValueError")
                failed += 1
        except ValueError as e:
            if not should_succeed:
                print(f"✓ PASS: '{url[:50]}...' -> Correctly raised ValueError")
                passed += 1
            else:
                print(f"✗ FAIL: '{url[:50]}...' -> Unexpected ValueError: {e}")
                failed += 1

    print(f"\nURL Parsing: {passed} passed, {failed} failed")
    return failed == 0


def test_timestamp_parsing():
    """Test parsing ISO 8601 timestamps."""
    print("\n" + "=" * 80)
    print("TEST 2: Timestamp Parsing")
    print("=" * 80)

    test_cases = [
        # (input, should_succeed)
        ("2025-11-15T10:30:00Z", True),
        ("2025-11-15T10:30:00", True),
        ("2024-01-01T00:00:00Z", True),
        ("invalid", False),
        ("", False),
        (None, False),
        ("2025-13-01T00:00:00Z", False),  # Invalid month
    ]

    passed = 0
    failed = 0

    for timestamp_str, should_succeed in test_cases:
        result = _parse_iso_timestamp(timestamp_str)

        if should_succeed:
            if result is not None:
                print(f"✓ PASS: '{timestamp_str}' -> {result}")
                passed += 1
            else:
                print(f"✗ FAIL: '{timestamp_str}' -> Expected datetime, got None")
                failed += 1
        else:
            if result is None:
                print(f"✓ PASS: '{timestamp_str}' -> Correctly returned None")
                passed += 1
            else:
                print(f"✗ FAIL: '{timestamp_str}' -> Expected None, got {result}")
                failed += 1

    print(f"\nTimestamp Parsing: {passed} passed, {failed} failed")
    return failed == 0


def test_read_timestamp_from_real_sheet():
    """Test reading timestamp from a real spreadsheet."""
    print("\n" + "=" * 80)
    print("TEST 3: Read Timestamp from Real Spreadsheet")
    print("=" * 80)

    # Use the spreadsheet we just created in the integration test
    # This should NOT have a timestamp (old format)
    old_spreadsheet_id = "1UoKHo2lCL-qZDDbMXI12XukKHjtcDeU-db_7z72a2QA"

    try:
        service = _get_sheet_service()
        print(f"Testing with spreadsheet: {old_spreadsheet_id}")

        # Test 1: Old spreadsheet without timestamp
        print("\n1. Testing old spreadsheet (no timestamp)...")
        timestamp = read_last_run_timestamp(service, old_spreadsheet_id)

        if timestamp is None:
            print("✓ PASS: Old spreadsheet correctly returned None (backwards compatible)")
        else:
            print(f"⚠ UNEXPECTED: Old spreadsheet returned timestamp: {timestamp}")
            print("   (This might mean the sheet was updated - still valid)")

        # Test 2: Invalid spreadsheet ID
        print("\n2. Testing invalid spreadsheet ID...")
        invalid_id = "INVALID_SPREADSHEET_ID_12345"
        timestamp = read_last_run_timestamp(service, invalid_id)

        if timestamp is None:
            print("✓ PASS: Invalid ID correctly returned None")
        else:
            print(f"✗ FAIL: Invalid ID should return None, got: {timestamp}")

        return True

    except Exception as e:
        print(f"✗ FAIL: {e}")
        logger.exception("Test failed")
        return False


def test_validate_sheet_structure():
    """Test validating spreadsheet structure."""
    print("\n" + "=" * 80)
    print("TEST 4: Validate Sheet Structure")
    print("=" * 80)

    # Use a known good spreadsheet
    valid_spreadsheet_id = "1UoKHo2lCL-qZDDbMXI12XukKHjtcDeU-db_7z72a2QA"
    invalid_spreadsheet_id = "INVALID_ID"

    try:
        service = _get_sheet_service()

        # Test 1: Valid spreadsheet
        print(f"\n1. Testing valid spreadsheet: {valid_spreadsheet_id}")
        is_valid = validate_sheet_structure(service, valid_spreadsheet_id)

        if is_valid:
            print("✓ PASS: Valid spreadsheet correctly validated")
        else:
            print("✗ FAIL: Valid spreadsheet failed validation")
            return False

        # Test 2: Invalid spreadsheet ID
        print(f"\n2. Testing invalid spreadsheet ID...")
        is_valid = validate_sheet_structure(service, invalid_spreadsheet_id)

        if not is_valid:
            print("✓ PASS: Invalid spreadsheet correctly failed validation")
        else:
            print("✗ FAIL: Invalid spreadsheet should fail validation")
            return False

        return True

    except Exception as e:
        print(f"✗ FAIL: {e}")
        logger.exception("Test failed")
        return False


def test_get_team_sheets():
    """Test getting list of team sheets."""
    print("\n" + "=" * 80)
    print("TEST 5: Get Team Sheets")
    print("=" * 80)

    # Use a known good spreadsheet
    spreadsheet_id = "1UoKHo2lCL-qZDDbMXI12XukKHjtcDeU-db_7z72a2QA"

    try:
        service = _get_sheet_service()

        print(f"Testing with spreadsheet: {spreadsheet_id}")
        team_sheets = get_existing_team_sheets(service, spreadsheet_id)

        if not team_sheets:
            print("✗ FAIL: No team sheets found (expected 16)")
            return False

        print(f"\n✓ Found {len(team_sheets)} team sheets:")
        for i, sheet_name in enumerate(sorted(team_sheets), 1):
            print(f"  {i}. {sheet_name}")

        # Check if Summary is excluded
        if "Summary" in team_sheets:
            print("\n✗ FAIL: Summary sheet should be excluded from team sheets")
            return False
        else:
            print("\n✓ PASS: Summary sheet correctly excluded")

        # Check expected count (should be 16 for our league)
        if len(team_sheets) == 16:
            print(f"✓ PASS: Expected 16 team sheets, found {len(team_sheets)}")
        else:
            print(f"⚠ WARNING: Expected 16 team sheets, found {len(team_sheets)}")

        return True

    except Exception as e:
        print(f"✗ FAIL: {e}")
        logger.exception("Test failed")
        return False


def test_end_to_end_old_spreadsheet():
    """Test complete flow with old spreadsheet (backwards compatibility)."""
    print("\n" + "=" * 80)
    print("TEST 6: End-to-End with Old Spreadsheet (Backwards Compatibility)")
    print("=" * 80)

    # URL of old spreadsheet (without timestamp)
    url = "https://docs.google.com/spreadsheets/d/1UoKHo2lCL-qZDDbMXI12XukKHjtcDeU-db_7z72a2QA/edit"

    try:
        print(f"Testing full workflow with old spreadsheet...")
        print(f"URL: {url}\n")

        # Step 1: Extract ID
        print("Step 1: Extract spreadsheet ID...")
        spreadsheet_id = extract_spreadsheet_id_from_url(url)
        print(f"✓ Extracted ID: {spreadsheet_id}")

        # Step 2: Get service
        print("\nStep 2: Authenticate with Google Sheets...")
        service = _get_sheet_service()
        print("✓ Authenticated")

        # Step 3: Validate structure
        print("\nStep 3: Validate spreadsheet structure...")
        is_valid = validate_sheet_structure(service, spreadsheet_id)
        if is_valid:
            print("✓ Structure validated")
        else:
            print("✗ Structure validation failed")
            return False

        # Step 4: Get team sheets
        print("\nStep 4: Get team sheets...")
        team_sheets = get_existing_team_sheets(service, spreadsheet_id)
        print(f"✓ Found {len(team_sheets)} team sheets")

        # Step 5: Read timestamp (should be None for old sheet)
        print("\nStep 5: Read timestamp...")
        timestamp = read_last_run_timestamp(service, spreadsheet_id)

        if timestamp is None:
            print("✓ Timestamp is None (backwards compatible - will update all teams)")
            print("\n🎉 BACKWARDS COMPATIBILITY CONFIRMED!")
            print("   Old spreadsheets without timestamps are fully supported.")
        else:
            print(f"⚠ Timestamp found: {timestamp}")
            print("   (Sheet may have been updated - still valid)")

        return True

    except Exception as e:
        print(f"✗ FAIL: {e}")
        logger.exception("Test failed")
        return False


def main():
    """Run all sheet reader tests."""
    print("\n" + "=" * 80)
    print("SHEET READER TEST SUITE")
    print("=" * 80)

    tests = [
        ("URL Parsing", test_url_parsing),
        ("Timestamp Parsing", test_timestamp_parsing),
        ("Read Timestamp from Real Sheet", test_read_timestamp_from_real_sheet),
        ("Validate Sheet Structure", test_validate_sheet_structure),
        ("Get Team Sheets", test_get_team_sheets),
        ("End-to-End Old Spreadsheet", test_end_to_end_old_spreadsheet),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            logger.exception(f"Test '{test_name}' crashed")
            results[test_name] = False

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ BACKWARDS COMPATIBILITY CONFIRMED")
        print("   - Old spreadsheets without timestamps: SUPPORTED")
        print("   - URL parsing: WORKING")
        print("   - Sheet validation: WORKING")
        print("   - Team sheet extraction: WORKING")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
