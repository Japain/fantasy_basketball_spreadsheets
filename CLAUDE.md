# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fantasy basketball application using the Yahoo Fantasy Sports API (yfpy library) to interact with Yahoo Fantasy Basketball data.

## Development Setup

**Python Version**: 3.12

**Package Manager**: uv (modern Python package manager)

**Virtual Environment**: `.venv/` (automatically managed by uv)

**Environment Configuration**:
- `.env` file contains API credentials (NEVER commit this file)
- Required environment variables:
  - `YAHOO_CONSUMER_KEY`: Yahoo Fantasy Sports API credentials
  - `YAHOO_CONSUMER_SECRET`: Yahoo API secret
  - `NBA_LEAGUE_ID`: Your fantasy league ID
  - `NBA_GAME_ID`: Yahoo game ID (466 for 2024-25 season)
  - `GOOGLE_CREDENTIALS_PATH`: Path to Google OAuth credentials JSON
- `credentials/` directory contains:
  - Google OAuth credentials JSON file
  - `google_token.pickle`: Saved Google authentication token (auto-generated)

## Common Commands

### Running the Application
```bash
# Run with default settings from .env
uv run python main.py

# Run with custom league ID
uv run python main.py --league-id 12345

# Run with verbose logging
uv run python main.py --verbose

# Run with custom document title
uv run python main.py --title "My Custom Report Title"

# Show help
uv run python main.py --help
```

### Authentication

**Yahoo OAuth:**
- Tokens are saved to `.env` automatically
- If tokens expire, use: `uv run python -m src.auth.auth_with_code`

**Google OAuth:**
- First-time authentication: `uv run python -m src.auth.google_auth_manual`
- Tokens are saved to `credentials/google_token.pickle`
- Tokens refresh automatically

### Managing Dependencies
```bash
# Add a new dependency
uv add <package-name>

# Remove a dependency
uv remove <package-name>

# Sync dependencies from pyproject.toml
uv sync

# Show installed packages
uv pip list
```

### Python Environment
```bash
# Activate virtual environment (if needed)
source .venv/bin/activate

# Run Python scripts with uv
uv run python <script.py>
```

## Project Structure

```
fantasy_basketball/
├── config.py                      # Configuration management
├── main.py                        # Application entry point ✅
├── src/
│   ├── auth/                      # OAuth authentication utilities
│   │   ├── auth_with_code.py         # Yahoo auth for headless environments ✅
│   │   ├── test_auth.py              # Interactive Yahoo auth test ✅
│   │   ├── complete_auth.py          # Yahoo OAuth helper ✅
│   │   ├── google_auth_manual.py     # Google auth for headless environments ✅
│   │   ├── complete_google_auth.py   # Google OAuth helper ✅
│   │   └── README.md                 # Authentication documentation ✅
│   ├── investigation/             # Investigation scripts (archived)
│   │   ├── investigate_salary_data.py
│   │   ├── investigate_roster.py
│   │   └── investigate_transactions.py
│   ├── data_models.py             # Player, Team, League dataclasses ✅
│   ├── yahoo_data_fetcher.py      # Yahoo API integration ✅
│   ├── data_processor.py          # Data validation & processing ✅
│   ├── google_auth.py             # Google API authentication ✅
│   ├── document_generator.py      # Google Docs generation ✅
│   ├── logger.py                  # Logging configuration ✅
│   └── __init__.py                # Package init ✅
├── tests/                         # Test suite
│   ├── test_league_extraction.py     # Yahoo data extraction test ✅
│   ├── test_full_integration.py      # Full integration test (Yahoo + Google) ✅
│   ├── test_il_exclusion.py          # IL/IL+ exclusion logic test ✅
│   └── test_roster_position_output.py # Roster position output format test ✅
├── credentials/                   # API credentials (gitignored)
│   ├── client_secret_*.json          # Google OAuth credentials
│   └── google_token.pickle           # Saved Google token (auto-generated)
├── league_data/                   # Yahoo API cache (gitignored)
├── .env                           # Environment variables (gitignored)
├── pyproject.toml                 # Project metadata and dependencies
└── uv.lock                        # Locked dependency versions
```

## Key Dependencies

- **yfpy** (v17.0.0+): Yahoo Fantasy Sports Python library for accessing Yahoo Fantasy API
  - Handles OAuth authentication with Yahoo
  - Provides data models for fantasy sports data
  - Depends on: python-dotenv, requests, stringcase, yahoo-oauth

- **Google API Client Libraries**:
  - **google-api-python-client** (v2.187.0+): Main Google API client
  - **google-auth** (v2.43.0+): Google authentication library
  - **google-auth-httplib2** (v0.2.1+): HTTP library for Google auth
  - **google-auth-oauthlib** (v1.2.2+): OAuth 2.0 helpers for Google auth

## Development Notes

- This project uses `uv` instead of pip/poetry for faster dependency management
- The `.python-version` file pins Python to 3.12
- API credentials are stored in `.env` and loaded via python-dotenv (included with yfpy)
- The project is in early stages with minimal implementation

## IMPORTANT: Running Python Code

**ALWAYS use `uv run python` instead of `python3` or `python` directly.**

This project uses uv to manage the virtual environment. Running Python commands directly with `python3` will NOT have access to the project dependencies installed in `.venv/`.

Examples:
- ✓ Correct: `uv run python script.py`
- ✓ Correct: `uv run python -c "print('hello')"`
- ✗ Wrong: `python3 script.py` (will fail with ModuleNotFoundError)
- ✗ Wrong: `python script.py` (will fail with ModuleNotFoundError)

This applies to all Python execution including testing, running scripts, and executing inline Python code.
