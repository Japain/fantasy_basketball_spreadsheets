"""
Test the pure helpers in src/auth/auth_with_code.py (offline, no Yahoo calls).

Covers:
1. Authorize URL contains the registered localhost redirect and scopes
2. GUID extraction from an id_token JWT
3. Token exchange sends Basic auth + the same redirect_uri, and surfaces errors
4. .env update replaces token lines in place and preserves everything else
"""

import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from src.auth import auth_with_code as auth


def make_id_token(claims: dict) -> str:
    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    return ".".join([b64(b'{"alg":"none"}'), b64(json.dumps(claims).encode()), "sig"])


def test_authorize_url():
    print("\nTest 1: authorize URL")
    url = auth.build_authorize_url("CLIENT123", nonce="n1")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.netloc == "api.login.yahoo.com"
    assert query["client_id"] == ["CLIENT123"]
    assert query["redirect_uri"] == ["https://localhost:8080"]
    assert query["scope"] == ["openid fspt-r"]
    assert query["response_type"] == ["code"]
    print("  ✓ URL has client id, localhost redirect, and scopes")


def test_guid_from_id_token():
    print("\nTest 2: GUID from id_token")
    assert auth.guid_from_id_token(make_id_token({"sub": "ABC123"})) == "ABC123"
    # Padding edge cases: payload lengths not divisible by 4
    for sub in ("A", "AB", "ABC", "ABCD"):
        assert auth.guid_from_id_token(make_id_token({"sub": sub})) == sub
    assert auth.guid_from_id_token(None) is None
    assert auth.guid_from_id_token("not-a-jwt") is None
    print("  ✓ extracts sub; tolerates padding, missing and malformed tokens")


def test_exchange_code():
    print("\nTest 3: token exchange")
    ok = Mock(status_code=200, json=lambda: {"access_token": "a", "refresh_token": "r"})
    with patch.object(auth.requests, "post", return_value=ok) as post:
        tokens = auth.exchange_code("K", "S", "CODE")
    assert tokens["access_token"] == "a"
    args, kwargs = post.call_args
    assert kwargs["auth"] == ("K", "S")
    assert kwargs["data"]["grant_type"] == "authorization_code"
    assert kwargs["data"]["code"] == "CODE"
    assert kwargs["data"]["redirect_uri"] == "https://localhost:8080"

    bad = Mock(status_code=400, json=lambda: {"error": "invalid_grant"}, text="invalid_grant")
    with patch.object(auth.requests, "post", return_value=bad):
        try:
            auth.exchange_code("K", "S", "OLD")
        except auth.AuthError as e:
            assert "invalid_grant" in str(e)
        else:
            raise AssertionError("expected AuthError on 400")
    print("  ✓ sends Basic auth + redirect_uri; raises AuthError on failure")


def test_refresh_tokens():
    print("\nTest 4: token refresh")
    ok = Mock(status_code=200, json=lambda: {"access_token": "a2", "refresh_token": "r"})
    with patch.object(auth.requests, "post", return_value=ok) as post:
        tokens = auth.refresh_tokens("K", "S", "r")
    assert tokens["access_token"] == "a2"
    assert post.call_args.kwargs["data"]["grant_type"] == "refresh_token"
    assert post.call_args.kwargs["data"]["refresh_token"] == "r"
    print("  ✓ uses refresh_token grant")


def test_update_env_file():
    print("\nTest 5: .env update")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ".env"
        path.write_text("A=1\nYAHOO_ACCESS_TOKEN=old\n# comment\nB=two=2\n")
        auth.update_env_file(path, {"YAHOO_ACCESS_TOKEN": "new", "YAHOO_GUID": "G"})
        lines = path.read_text().splitlines()
    assert lines == ["A=1", "YAHOO_ACCESS_TOKEN=new", "# comment", "B=two=2", "YAHOO_GUID=G"], lines
    print("  ✓ replaced in place, appended new keys, preserved other lines")


def main():
    print("=" * 80)
    print("YAHOO AUTH HELPER TESTS")
    print("=" * 80)
    test_authorize_url()
    test_guid_from_id_token()
    test_exchange_code()
    test_refresh_tokens()
    test_update_env_file()
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
