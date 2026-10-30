"""
Yahoo OAuth setup for headless environments (manual authorization-code flow).

Yahoo no longer supports the `oob` redirect, so this uses the registered
https://localhost:8080 redirect: the browser lands on a "site can't be reached"
page and the `code=` value is read from the address bar.

Usage:
    uv run python -m src.auth.auth_with_code                  # print authorize URL
    uv run python -m src.auth.auth_with_code <code>           # exchange code, save tokens to .env
    uv run python -m src.auth.auth_with_code --refresh-test   # verify the refresh path used by GitHub Actions
"""

import base64
import json
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlencode

import requests
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

REDIRECT_URI = "https://localhost:8080"
SCOPE = "openid fspt-r"
AUTHORIZE_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
PROBE_URL = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games?format=json"

# GitHub Actions secret names that mirror the .env token lines
GITHUB_SECRETS = [
    "YAHOO_CONSUMER_KEY",
    "YAHOO_CONSUMER_SECRET",
    "YAHOO_ACCESS_TOKEN",
    "YAHOO_REFRESH_TOKEN",
    "YAHOO_TOKEN_TIME",
]


class AuthError(Exception):
    """Raised when Yahoo rejects a token request."""


def build_authorize_url(client_id: str, nonce: Optional[str] = None) -> str:
    params = {
        "response_type": "code",
        "scope": SCOPE,
        "redirect_uri": REDIRECT_URI,
        "nonce": nonce or str(int(time.time())),
        "client_id": client_id,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params, quote_via=quote)}"


def guid_from_id_token(id_token: Optional[str]) -> Optional[str]:
    """Yahoo's token response has no GUID field; it is the `sub` claim of the id_token."""
    try:
        payload = id_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))["sub"]
    except (AttributeError, IndexError, KeyError, ValueError):
        return None


def _token_request(client_key: str, client_secret: str, data: dict) -> dict:
    response = requests.post(TOKEN_URL, auth=(client_key, client_secret), data=data, timeout=30)
    if response.status_code != 200:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise AuthError(f"Yahoo token request failed (HTTP {response.status_code}): {detail}")
    return response.json()


def exchange_code(client_key: str, client_secret: str, code: str) -> dict:
    return _token_request(client_key, client_secret, {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    })


def refresh_tokens(client_key: str, client_secret: str, refresh_token: str) -> dict:
    return _token_request(client_key, client_secret, {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": REDIRECT_URI,
    })


def update_env_file(path: Path, updates: dict) -> None:
    """Replace matching KEY= lines in place and append missing keys; other lines are untouched."""
    lines = path.read_text().splitlines() if path.exists() else []
    remaining = dict(updates)
    out = []
    for line in lines:
        key = line.split("=", 1)[0]
        if key in remaining:
            out.append(f"{key}={remaining.pop(key)}")
        else:
            out.append(line)
    out.extend(f"{key}={value}" for key, value in remaining.items())
    path.write_text("\n".join(out) + "\n")


def save_tokens(tokens: dict, previous_guid: Optional[str] = None) -> None:
    update_env_file(ENV_PATH, {
        "YAHOO_ACCESS_TOKEN": tokens["access_token"],
        "YAHOO_REFRESH_TOKEN": tokens["refresh_token"],
        "YAHOO_TOKEN_TIME": str(time.time()),
        "YAHOO_TOKEN_TYPE": tokens.get("token_type", "bearer"),
        "YAHOO_GUID": guid_from_id_token(tokens.get("id_token")) or previous_guid or "",
    })


def probe_api(access_token: str) -> int:
    response = requests.get(PROBE_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    return response.status_code


def _credentials() -> tuple:
    env = dotenv_values(ENV_PATH)
    key, secret = env.get("YAHOO_CONSUMER_KEY"), env.get("YAHOO_CONSUMER_SECRET")
    if not key or not secret:
        sys.exit("YAHOO_CONSUMER_KEY / YAHOO_CONSUMER_SECRET missing from .env")
    return key, secret, env


def run_authorize_url() -> None:
    key, _, _ = _credentials()
    print("Open this URL, approve access, then copy the `code=` value from the")
    print("address bar of the 'site can't be reached' page (single-use, expires in minutes):\n")
    print(build_authorize_url(key))
    print("\nThen run: uv run python -m src.auth.auth_with_code <code>")


def run_exchange(code: str) -> None:
    key, secret, _ = _credentials()
    tokens = exchange_code(key, secret, code)
    save_tokens(tokens)
    print("✓ Tokens saved to .env")
    status = probe_api(tokens["access_token"])
    print(f"{'✓' if status == 200 else '✗'} Fantasy API probe: HTTP {status}")
    if status == 403:
        print("  403 means the account/app lacks Fantasy API approval (see sports.yahoo.com/developer/access/)")
    print("\nTo use these in GitHub Actions, update these repository secrets from .env:")
    for name in GITHUB_SECRETS:
        print(f"  • {name}")


def run_refresh_test() -> None:
    """Verify the refresh path GitHub Actions relies on, and detect refresh-token rotation."""
    key, secret, env = _credentials()
    refresh_token = env.get("YAHOO_REFRESH_TOKEN")
    if not refresh_token:
        sys.exit("YAHOO_REFRESH_TOKEN missing from .env; run the code exchange first")

    rotated = False
    for attempt in (1, 2):
        tokens = refresh_tokens(key, secret, refresh_token)
        changed = tokens["refresh_token"] != refresh_token
        rotated = rotated or changed
        # Always persist what Yahoo returned, so a rotating refresh token is never lost
        save_tokens(tokens, previous_guid=env.get("YAHOO_GUID"))
        refresh_token = tokens["refresh_token"]
        status = probe_api(tokens["access_token"])
        print(f"Refresh #{attempt}: API probe HTTP {status}, refresh token "
              f"{'ROTATED' if changed else 'unchanged'}")
        if status != 200:
            sys.exit("✗ Refreshed token did not work against the Fantasy API")

    # Mirror what the GitHub Actions workflows do: expired token + refresh token, guid null
    from yfpy.query import YahooFantasySportsQuery
    token_json = {
        "access_token": "expired", "consumer_key": key, "consumer_secret": secret,
        "guid": None, "refresh_token": refresh_token, "token_time": 0, "token_type": "bearer",
    }
    query = YahooFantasySportsQuery(
        league_id=env.get("NBA_LEAGUE_ID", "0"), game_code="nba", game_id=int(env.get("NBA_GAME_ID", "478")),
        yahoo_access_token_json=token_json, browser_callback=False,
        save_token_data_to_env_file=True, env_file_location=BASE_DIR,
    )
    games = query.get_user_games()
    print(f"✓ yfpy Actions-style refresh worked ({len(games)} games returned)")

    if rotated:
        print("\n⚠ Yahoo rotates refresh tokens: GitHub secrets go stale after each run. "
              "The workflows would need to write the new token back.")
    else:
        print("\n✓ Refresh token is stable: static GitHub secrets will keep working across runs.")


def main() -> None:
    args = sys.argv[1:]
    try:
        if not args:
            run_authorize_url()
        elif args == ["--refresh-test"]:
            run_refresh_test()
        elif len(args) == 1 and not args[0].startswith("-"):
            run_exchange(args[0])
        else:
            sys.exit(__doc__)
    except AuthError as e:
        sys.exit(f"✗ {e}")


if __name__ == "__main__":
    main()
