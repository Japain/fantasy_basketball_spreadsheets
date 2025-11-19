#!/bin/bash
# Script to extract secrets from .env for GitHub Actions setup
# This makes it easy to copy/paste values into GitHub Secrets

set -e

echo "========================================================================"
echo "GitHub Actions Secrets - Ready to Copy"
echo "========================================================================"
echo ""
echo "Copy these values to GitHub repository Settings → Secrets → Actions"
echo ""
echo "------------------------------------------------------------------------"

# Function to safely extract and display secret
extract_secret() {
    local key=$1
    local value=$(grep "^${key}=" .env 2>/dev/null | cut -d'=' -f2-)
    if [ -n "$value" ] && [ "$value" != "None" ]; then
        echo "SECRET NAME: $key"
        echo "VALUE:"
        echo "$value"
        echo ""
        echo "------------------------------------------------------------------------"
    else
        echo "⚠️  WARNING: $key not found or empty in .env"
        echo "------------------------------------------------------------------------"
    fi
}

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please make sure you're running this from the project root directory."
    exit 1
fi

echo ""
echo "1️⃣  YAHOO API CREDENTIALS"
echo "------------------------------------------------------------------------"
extract_secret "YAHOO_CONSUMER_KEY"
extract_secret "YAHOO_CONSUMER_SECRET"

echo ""
echo "2️⃣  YAHOO OAUTH TOKENS"
echo "------------------------------------------------------------------------"
extract_secret "YAHOO_ACCESS_TOKEN"
extract_secret "YAHOO_REFRESH_TOKEN"
extract_secret "YAHOO_TOKEN_TIME"

echo ""
echo "3️⃣  LEAGUE CONFIGURATION"
echo "------------------------------------------------------------------------"
extract_secret "NBA_LEAGUE_ID"
extract_secret "NBA_GAME_ID"
extract_secret "INITIAL_AUCTION_BUDGET"

echo ""
echo "4️⃣  GOOGLE CREDENTIALS (JSON file content)"
echo "------------------------------------------------------------------------"
GOOGLE_CREDS_PATH=$(grep "^GOOGLE_CREDENTIALS_PATH=" .env 2>/dev/null | cut -d'=' -f2-)
if [ -n "$GOOGLE_CREDS_PATH" ] && [ -f "$GOOGLE_CREDS_PATH" ]; then
    echo "SECRET NAME: GOOGLE_CREDENTIALS_JSON"
    echo "VALUE:"
    cat "$GOOGLE_CREDS_PATH"
    echo ""
    echo "------------------------------------------------------------------------"
else
    echo "⚠️  WARNING: Google credentials file not found at: $GOOGLE_CREDS_PATH"
    echo "------------------------------------------------------------------------"
fi

echo ""
echo "5️⃣  GOOGLE TOKEN (base64 encoded)"
echo "------------------------------------------------------------------------"
GOOGLE_TOKEN_PATH="credentials/google_token.pickle"
if [ -f "$GOOGLE_TOKEN_PATH" ]; then
    echo "SECRET NAME: GOOGLE_TOKEN_PICKLE_BASE64"
    echo "VALUE:"
    base64 -w 0 "$GOOGLE_TOKEN_PATH"
    echo ""
    echo ""
    echo "------------------------------------------------------------------------"
else
    echo "⚠️  WARNING: Google token file not found at: $GOOGLE_TOKEN_PATH"
    echo "Please run: uv run python -m src.auth.google_auth_manual"
    echo "------------------------------------------------------------------------"
fi

echo ""
echo "6️⃣  SPREADSHEET ID (you need to provide this)"
echo "------------------------------------------------------------------------"
echo "SECRET NAME: SPREADSHEET_ID"
echo "VALUE: <YOUR_SPREADSHEET_ID_HERE>"
echo ""
echo "Get this from your Google Sheets URL:"
echo "https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit"
echo "------------------------------------------------------------------------"

echo ""
echo "========================================================================"
echo "✅ All secrets extracted!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "1. Go to your GitHub repository"
echo "2. Navigate to Settings → Secrets and variables → Actions"
echo "3. Click 'New repository secret'"
echo "4. Copy each SECRET NAME and VALUE from above"
echo "5. Save each secret"
echo ""
echo "For detailed instructions, see: GITHUB_ACTIONS_SETUP.md"
echo "========================================================================"
