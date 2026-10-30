"""
Test that team sheet writes retry on Google Sheets rate limits (429).

Simulates a 429 on the first values().clear() call and verifies that
update_team_sheet() retries and completes instead of aborting.
"""

from unittest.mock import Mock, patch
from googleapiclient.errors import HttpError

from src import sheet_updater
from src.data_models import Team


def create_http_error(status_code: int) -> HttpError:
    resp = Mock()
    resp.status = status_code
    return HttpError(resp=resp, content=b"rate limited")


def main():
    print("TEST: update_team_sheet retries write on 429")

    team = Team(team_id="1", team_key="478.l.1.t.1", team_name="Test Team", manager_name="Tester", roster=[], total_salary=0)

    clear_execute = Mock(side_effect=[create_http_error(429), {}])
    service = Mock()
    values = service.spreadsheets.return_value.values.return_value
    values.clear.return_value.execute = clear_execute

    with patch.object(sheet_updater, "_find_sheet_by_team_id", return_value=(5, "Test Team")), \
         patch.object(sheet_updater, "_apply_sheet_protection"), \
         patch("src.api_retry.time.sleep") as mock_sleep:
        sheet_updater.update_team_sheet(service, "sheet-id", team)

    assert clear_execute.call_count == 2, f"Expected 2 clear attempts, got {clear_execute.call_count}"
    assert mock_sleep.called, "Expected backoff sleep between attempts"
    values.update.return_value.execute.assert_called_once()
    print("✓ Test passed: 429 on clear was retried and update completed")


if __name__ == "__main__":
    main()
