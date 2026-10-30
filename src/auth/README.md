# Authentication Scripts

Utilities for Yahoo Fantasy Sports API OAuth.

## `auth_with_code.py`

Manual authorization-code flow for headless environments. Yahoo no longer supports
the `oob` redirect, so this uses the registered `https://localhost:8080` redirect.

```bash
# 1. Print the authorize URL
uv run python -m src.auth.auth_with_code

# 2. Open it, approve access. The browser lands on a "site can't be reached" page;
#    copy the code= value from the address bar (single-use, expires in minutes).

# 3. Exchange the code: saves tokens to .env and probes the Fantasy API
uv run python -m src.auth.auth_with_code <code>

# Verify the refresh path GitHub Actions relies on
uv run python -m src.auth.auth_with_code --refresh-test
```

Tests: `uv run python -m tests.test_yahoo_auth` (offline).

## Token storage

Written to `.env` (lines are replaced in place; other settings are untouched):
`YAHOO_ACCESS_TOKEN`, `YAHOO_REFRESH_TOKEN`, `YAHOO_TOKEN_TIME`, `YAHOO_TOKEN_TYPE`, `YAHOO_GUID`
(GUID is the `sub` claim of the returned `id_token`).

yfpy refreshes expired access tokens from the refresh token automatically.

## GitHub Actions

Workflows rebuild `.env` from repository secrets on every run and refresh the access
token from `YAHOO_REFRESH_TOKEN`. After re-authorizing, update these secrets:
`YAHOO_CONSUMER_KEY`, `YAHOO_CONSUMER_SECRET`, `YAHOO_ACCESS_TOKEN`,
`YAHOO_REFRESH_TOKEN`, `YAHOO_TOKEN_TIME`.

As of 2026-10-30 Yahoo does not rotate refresh tokens, so static secrets keep working.

## Troubleshooting

- **`KeyError: 'access_token'` from yfpy**: stale `YAHOO_*` token lines in `.env`; delete them and re-auth.
- **`invalid_grant`**: code expired or already used; get a new one.
- **403 "not authorized to perform this action"** with a valid token: the Yahoo account/app lacks Fantasy API approval.

## Google

`google_auth_manual.py` and `complete_google_auth.py` are for Google auth and are deprecated
(OOB flow blocked by Google). Use `uv run python main.py` for the browser flow.
