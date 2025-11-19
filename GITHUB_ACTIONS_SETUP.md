# GitHub Actions Setup Guide

This guide walks you through setting up automated daily updates for your fantasy basketball spreadsheet using GitHub Actions.

## Overview

The GitHub Actions workflow will:
- Run automatically every day at 8:00 AM UTC (configurable)
- Update your Google Sheets with the latest roster and salary data
- Use only the free tier (zero cost)
- Send notifications if updates fail
- Allow manual triggering from GitHub UI

## Prerequisites

Before setting up GitHub Actions, you must:
1. Have completed local authentication for both Yahoo and Google APIs
2. Have a working `.env` file with all credentials
3. Have successfully run `uv run python main.py` locally at least once
4. Have your code pushed to a GitHub repository

## Setup Steps

### Step 1: Get Your OAuth Tokens

#### Yahoo OAuth Tokens

Your Yahoo tokens are already saved in your `.env` file. You need to extract them:

```bash
# View your .env file and copy these values:
cat .env | grep YAHOO
```

You should see:
- `YAHOO_CONSUMER_KEY`
- `YAHOO_CONSUMER_SECRET`
- `YAHOO_ACCESS_TOKEN`
- `YAHOO_REFRESH_TOKEN`
- `YAHOO_TOKEN_TIME`

**Note:** The `YAHOO_REFRESH_TOKEN` is the most important - it allows GitHub Actions to automatically refresh expired access tokens.

#### Google OAuth Tokens

You need to prepare two files:

1. **Google Credentials JSON** (client secret):
```bash
# View your credentials file
cat credentials/client_secret_*.json
```

2. **Google Token Pickle** (authentication token):
```bash
# Encode the token file as base64
base64 -w 0 credentials/google_token.pickle > google_token_base64.txt
cat google_token_base64.txt
```

### Step 2: Add Secrets to GitHub

Navigate to your GitHub repository:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add each of the following secrets:

#### Required Secrets

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `YAHOO_CONSUMER_KEY` | Yahoo API app key | From `.env` file |
| `YAHOO_CONSUMER_SECRET` | Yahoo API app secret | From `.env` file |
| `YAHOO_ACCESS_TOKEN` | Yahoo access token | From `.env` file |
| `YAHOO_REFRESH_TOKEN` | Yahoo refresh token | From `.env` file |
| `YAHOO_TOKEN_TIME` | Yahoo token timestamp | From `.env` file |
| `NBA_LEAGUE_ID` | Your Yahoo league ID | From `.env` file |
| `NBA_GAME_ID` | Yahoo game ID (e.g., 466) | From `.env` file |
| `INITIAL_AUCTION_BUDGET` | League auction budget | From `.env` file |
| `GOOGLE_CREDENTIALS_JSON` | Google OAuth client secret | Contents of `credentials/client_secret_*.json` |
| `GOOGLE_TOKEN_PICKLE_BASE64` | Google auth token (base64) | Output from `base64` command above |
| `SPREADSHEET_ID` | Google Sheets ID to update | From your spreadsheet URL |

#### Getting the Spreadsheet ID

From your Google Sheets URL:
```
https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit
                                    ^^^^^^^^^^^^^^^^^^^^
                                    This is your SPREADSHEET_ID
```

### Step 3: Verify the Workflow File

The workflow file should already exist at `.github/workflows/daily-update.yml`. Verify it's there:

```bash
cat .github/workflows/daily-update.yml
```

If you want to change the schedule time, edit the cron expression:
```yaml
on:
  schedule:
    # Current: 8:00 AM UTC (3:00 AM EST, 12:00 AM PST)
    - cron: '0 8 * * *'
```

**Cron schedule examples:**
- `'0 8 * * *'` = 8:00 AM UTC daily
- `'0 12 * * *'` = 12:00 PM UTC daily
- `'30 15 * * *'` = 3:30 PM UTC daily
- `'0 0 * * *'` = Midnight UTC daily

**Timezone conversion:**
- UTC to EST: subtract 5 hours (4 during DST)
- UTC to PST: subtract 8 hours (7 during PDT)

### Step 4: Push the Workflow to GitHub

Commit and push the workflow file:

```bash
git add .github/workflows/daily-update.yml
git commit -m "Add GitHub Actions workflow for daily updates"
git push origin main
```

### Step 5: Test the Workflow

Test the workflow manually before waiting for the scheduled run:

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Daily Fantasy Basketball Update** workflow
4. Click **Run workflow** dropdown
5. Click **Run workflow** button

Monitor the workflow run:
- You should see a new workflow run appear
- Click on it to see real-time logs
- The run should complete in 1-2 minutes
- Check your Google Sheets to verify it was updated

### Step 6: Verify Scheduled Runs

After your first manual test succeeds:

1. Wait for the next scheduled run (based on your cron schedule)
2. Check the **Actions** tab to see the automated run
3. Verify your spreadsheet was updated
4. Check for any errors in the workflow logs

## Monitoring and Maintenance

### Viewing Workflow Runs

- Go to **Actions** tab in your repository
- See all workflow runs (manual and scheduled)
- Click any run to see detailed logs
- Logs are retained for 90 days

### Email Notifications

GitHub automatically sends email notifications when workflows fail:
- Go to **Settings** → **Notifications**
- Ensure "Actions" notifications are enabled
- You'll receive emails if the update fails

### Manual Triggers

You can manually trigger an update anytime:
1. Go to **Actions** → **Daily Fantasy Basketball Update**
2. Click **Run workflow**
3. Select branch (usually `main`)
4. Click **Run workflow** button

### Token Refresh

**Yahoo tokens:**
- The workflow automatically refreshes Yahoo tokens using `YAHOO_REFRESH_TOKEN`
- Refresh tokens typically last 1 year
- If you get authentication errors, re-run `uv run python -m src.auth.auth_with_code` locally and update the secrets

**Google tokens:**
- Google tokens refresh automatically via the `google_token.pickle` file
- If you get Google auth errors, delete the secret and re-authenticate:
  ```bash
  # Re-authenticate locally
  uv run python -m src.auth.google_auth_manual

  # Re-encode the token
  base64 -w 0 credentials/google_token.pickle > google_token_base64.txt

  # Update the GOOGLE_TOKEN_PICKLE_BASE64 secret on GitHub
  ```

### Troubleshooting

#### Workflow fails with "Authentication failed"

**Yahoo authentication:**
1. Check that all Yahoo secrets are set correctly
2. Verify `YAHOO_REFRESH_TOKEN` is present
3. Re-run authentication locally: `uv run python -m src.auth.auth_with_code`
4. Update the secrets on GitHub

**Google authentication:**
1. Verify `GOOGLE_CREDENTIALS_JSON` contains the full JSON content
2. Verify `GOOGLE_TOKEN_PICKLE_BASE64` is properly base64-encoded
3. Re-run authentication locally: `uv run python -m src.auth.google_auth_manual`
4. Re-encode and update the token secret

#### Workflow doesn't run at scheduled time

- GitHub Actions schedules can be delayed by ±5 minutes during high load
- Check if the workflow is disabled (Actions tab → enable workflow)
- Verify the cron syntax is correct
- Try a manual trigger to ensure the workflow works

#### Workflow runs but spreadsheet doesn't update

1. Check the workflow logs for errors
2. Verify `SPREADSHEET_ID` secret is correct
3. Ensure the Google service account has edit access to the spreadsheet
4. Test locally: `uv run python main.py --spreadsheet-id YOUR_ID --verbose`

#### "Resource not accessible by integration" error

- Ensure workflow file is on the default branch (usually `main`)
- Check that Actions are enabled for your repository
- Verify secrets are set in the correct repository

## Security Best Practices

1. **Never commit secrets to git**
   - Always use GitHub Secrets for sensitive data
   - Double-check `.env` is in `.gitignore`

2. **Use environment-level secrets** (optional)
   - For better security, use environment secrets instead of repository secrets
   - Settings → Environments → Create environment → Add secrets

3. **Rotate tokens periodically**
   - Yahoo refresh tokens expire after ~1 year
   - Consider re-authenticating every 6 months

4. **Limit workflow permissions**
   - The workflow only needs read access to code
   - No write permissions to repository required

## Updating the Workflow

To modify the workflow:

1. Edit `.github/workflows/daily-update.yml` locally
2. Commit and push changes
3. GitHub automatically uses the updated workflow
4. Test with manual trigger to verify changes

## Cost

GitHub Actions is **completely free** for this use case:
- **Public repositories**: Unlimited minutes
- **Private repositories**: 2,000 minutes/month free tier
- **This workflow**: Uses ~1 minute/day = ~30 minutes/month
- **Cost**: $0/month

## Next Steps

Once your daily updates are working:

1. Consider adding Slack/Discord notifications (see `FUTURE_IDEAS.md`)
2. Set up email alerts for specific events
3. Create a backup workflow for critical updates
4. Monitor workflow efficiency and optimize if needed

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Pricing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
- [Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

---

**Questions or Issues?**

If you encounter any problems:
1. Check the workflow logs in the Actions tab
2. Review this guide's troubleshooting section
3. Test the same command locally to isolate the issue
4. Check if secrets are set correctly on GitHub
