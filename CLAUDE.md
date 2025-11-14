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
  - Additional API keys may be present for other services
- `client_secret_244271698600-19dd7prtef55t0845qibik3l0t1mo0pn.apps.googleusercontent.com.json` file contains google doc api credentials

## Common Commands

### Running the Application
```bash
uv run main.py
```

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
├── config.py                 # Configuration management
├── main.py                   # Application entry point
├── src/
│   ├── auth/                # OAuth authentication utilities
│   │   ├── auth_with_code.py   # Primary auth script for headless environments
│   │   ├── test_auth.py        # Interactive auth test
│   │   └── complete_auth.py    # OAuth helper
│   ├── yahoo_data_fetcher.py   # Yahoo API integration
│   ├── logger.py               # Logging configuration
│   └── (future modules: data_processor, google_auth, document_generator)
├── tests/                   # Test suite
├── credentials/             # API credentials (gitignored)
├── league_data/             # Yahoo API cache (gitignored)
├── .env                     # Environment variables (gitignored)
├── pyproject.toml           # Project metadata and dependencies
└── uv.lock                  # Locked dependency versions
```

## Key Dependencies

- **yfpy** (v17.0.0+): Yahoo Fantasy Sports Python library for accessing Yahoo Fantasy API
  - Handles OAuth authentication with Yahoo
  - Provides data models for fantasy sports data
  - Depends on: python-dotenv, requests, stringcase, yahoo-oauth

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
