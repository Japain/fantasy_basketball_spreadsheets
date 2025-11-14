# Authentication Scripts

This directory contains utilities for Yahoo Fantasy Sports API OAuth authentication.

## Scripts

### `auth_with_code.py`
**Primary authentication script** - Use this for initial OAuth setup in headless/WSL environments.

**Usage:**
```bash
# Run from project root
uv run python src/auth/auth_with_code.py
```

**What it does:**
1. Generates Yahoo OAuth authorization URL
2. Accepts verification code (edit the `verification_code` variable in the script)
3. Exchanges code for access/refresh tokens
4. Saves tokens to `.env` file
5. Tests authentication with a league info API call

**Note:** Update the `verification_code` variable in the script before running.

### `test_auth.py`
Interactive authentication test script (requires terminal with stdin support).

**Usage:**
```bash
# Run from project root
uv run python src/auth/test_auth.py
```

**What it does:**
1. Prompts for manual OAuth authorization
2. Waits for user to paste verification code
3. Completes authentication and tests API call

**Note:** Not suitable for headless environments - use `auth_with_code.py` instead.

### `complete_auth.py`
Helper script for OAuth exploration (development/debugging purposes).

## OAuth Flow

1. **First Time Setup:**
   - Edit `src/auth/auth_with_code.py` and set the `verification_code` variable
   - Get verification code by visiting: https://api.login.yahoo.com/oauth2/request_auth?redirect_uri=oob&response_type=code&client_id=[YOUR_KEY]
   - Run: `uv run python src/auth/auth_with_code.py`

2. **Subsequent API Calls:**
   - Tokens are automatically loaded from `.env`
   - Refresh tokens are used to renew expired access tokens
   - No manual intervention needed

## Token Storage

Tokens are automatically saved to `.env` file:
- `YAHOO_ACCESS_TOKEN` - Used for API requests
- `YAHOO_REFRESH_TOKEN` - Used to renew expired tokens
- `YAHOO_TOKEN_TIME` - Token expiration timestamp
- `YAHOO_TOKEN_TYPE` - Token type (bearer)

## Troubleshooting

**"KeyError: 'access_token'"**
- Verification code expired or already used
- Get a new verification code and try again

**"ModuleNotFoundError: No module named 'dotenv'"**
- Make sure to use `uv run python` instead of `python` or `python3`

**"[Errno 20] Not a directory"**
- Check that `env_file_location` parameter points to directory, not file
