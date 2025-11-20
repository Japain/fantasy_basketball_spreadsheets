# Discord Integration TODO

This document tracks the implementation of Discord webhook notifications for the Fantasy Basketball automation project.

**Approach**: Discord Webhooks with `discord-webhook` Python library
**Reference**: See `context/DISCORD_INTEGRATION.md` for detailed research and implementation guide
**Estimated Total Effort**: 6-11 hours
**Cost**: $0 forever

---

## Phase 1: Basic Webhook Integration (1-2 hours)

**Goal**: Send simple success/failure notifications

### Setup
- [ ] Create Discord webhook in target channel
  - Open Discord server → Select channel → Channel Settings → Integrations
  - Click "Create Webhook" or "View Webhooks"
  - Click "New Webhook" → Name it "Fantasy Basketball Bot"
  - Copy webhook URL
- [ ] Add `DISCORD_WEBHOOK_URL` to GitHub Secrets
  - GitHub repository → Settings → Secrets and variables → Actions
  - Click "New repository secret"
  - Name: `DISCORD_WEBHOOK_URL`, Value: webhook URL
- [ ] Install `discord-webhook` library
  - Run: `uv add discord-webhook`

### Implementation
- [ ] Create `src/discord_notifier.py` module
  - Add module docstring
  - Import required modules (discord_webhook, os, logging, datetime)
  - Create `DiscordNotifier` class
- [ ] Implement `DiscordNotifier.__init__()` method
  - Accept optional webhook_url parameter
  - Read from environment if not provided
  - Add enabled flag for toggling notifications
- [ ] Implement `send_update_summary()` method
  - Accept parameters: teams_updated, total_teams, transactions_processed, spreadsheet_url, last_update_hours
  - Create DiscordWebhook instance
  - Create basic DiscordEmbed with title and description
  - Add embed fields for key metrics
  - Send webhook and return success/failure
  - Add error handling
- [ ] Implement `send_error_notification()` method
  - Accept parameters: error_message, error_type, stack_trace (optional), role_id (optional)
  - Create DiscordWebhook instance
  - Add role mention if provided
  - Create error embed (red color)
  - Include error details and timestamp
  - Send webhook and return success/failure
  - Add error handling
- [ ] Add convenience functions
  - `notify_update_complete()` - Quick wrapper for update notifications
  - `notify_error()` - Quick wrapper for error notifications

### Integration with main.py
- [ ] Import discord notifier in main.py
  - Add: `from src.discord_notifier import notify_update_complete, notify_error`
- [ ] Add Discord notification after successful update
  - Extract metrics (teams_updated, total_teams, transactions_processed)
  - Calculate hours since last update
  - Call `notify_update_complete()` with metrics
- [ ] Add Discord notification in error handler
  - Wrap main logic in try/except
  - Call `notify_error()` with exception details in except block

### GitHub Actions Integration
- [ ] Update `.github/workflows/daily-update.yml`
  - Add `DISCORD_WEBHOOK_URL` to env section
  - Add `DISCORD_ALERT_ROLE_ID` to env section (for Phase 3)
  - Ensure environment variables are passed to Python script
- [ ] Add fallback error notification
  - Add step that runs if: failure()
  - Use curl to send simple error message directly to webhook
  - Include link to GitHub Actions logs

### Testing
- [ ] Test locally with sample data
  - Set DISCORD_WEBHOOK_URL environment variable
  - Run: `DISCORD_WEBHOOK_URL="your_url" uv run python main.py --verbose`
  - Verify notification appears in Discord
- [ ] Test error notification locally
  - Trigger an error condition
  - Verify error notification appears
- [ ] Test in GitHub Actions (manual trigger)
  - Push changes to GitHub
  - Manually trigger workflow
  - Verify notifications appear in Discord
- [ ] Verify notifications appear in Discord
  - Check formatting is readable
  - Check all required information is present

**Deliverables**:
- `src/discord_notifier.py` (basic functionality)
- Updated `main.py` with Discord integration
- Updated `.github/workflows/daily-update.yml`
- Basic documentation in README.md

---

## Phase 2: Rich Formatting & Metrics (2-3 hours)

**Goal**: Professional-looking notifications with all required data

### Enhanced Embed Formatting
- [ ] Add efficiency percentage calculation
  - Calculate: (teams_updated / total_teams * 100)
  - Display in Teams Updated field: "4 of 16 (75% efficiency)"
- [ ] Add last update time calculation
  - Calculate hours since last update
  - Display as: "15.5 hours ago"
- [ ] Create rich embed with multiple fields
  - Use DiscordEmbed.add_embed_field() for each metric
  - Use inline parameter strategically for layout
  - Add emojis for visual appeal: ✅ 📈 ⏱️ 🔗
- [ ] Add clickable spreadsheet link
  - Format as: `[View Spreadsheet](url)`
  - Use markdown link in embed field
- [ ] Add color coding
  - Success notifications: Blue (0x03b2f8)
  - Error notifications: Red (0xff0000)
  - Warning notifications: Yellow (0xffd700)
- [ ] Add timestamp to embeds
  - Use `embed.set_timestamp()` for automatic Discord time rendering
  - Shows in user's local timezone
- [ ] Add custom footer with branding
  - Use `embed.set_footer()` with branding text
  - Example: "Fantasy Basketball Automation • Powered by Yahoo API"

### Data Extraction from main.py
- [ ] Extract metrics from update flow
  - Capture teams_updated count
  - Capture total_teams count
  - Capture transactions_processed count
- [ ] Calculate hours since last update
  - Read last_update_time from sheet reader
  - Calculate difference from current time
  - Convert to hours as float
- [ ] Pass all metrics to Discord notifier
  - Update notify_update_complete() call with all parameters
  - Ensure all data is available before calling

### Verbose Transaction Logging (Optional)
- [ ] Format transaction log for Discord
  - Create formatted string with transaction details
  - Format: "• Team Name (2 transaction(s))\n    - [11/18 10:30] ADD: Player Name ($5)"
  - Limit length to 1000 characters (Discord field limit)
  - Truncate with "..." if too long
- [ ] Add transaction log to embed
  - Add as separate field
  - Use code block formatting: ```log text```
  - Only include if verbose mode enabled

### Testing Different Scenarios
- [ ] Test with 0 teams updated (no transactions)
  - Verify message shows "0 of 16 (0% efficiency)"
  - Verify appropriate messaging
- [ ] Test with all teams updated (force full update)
  - Verify message shows "16 of 16 (100%)"
  - Verify appropriate messaging
- [ ] Test with partial update (4-8 teams)
  - Verify message shows correct counts and percentage
  - Verify efficiency calculation is correct
- [ ] Test with long transaction log
  - Verify truncation works correctly
  - Verify "..." appears at end when truncated

**Deliverables**:
- Enhanced `discord_notifier.py` with full formatting
- Integration with `main.py` to extract metrics
- Example notification screenshots (save to `docs/` or `context/`)

---

## Phase 3: Advanced Features (2-4 hours)

**Goal**: Role mentions, error details, conditional notifications

### Role Mentions for Alerts
- [ ] Create role in Discord for bot notifications
  - Discord server → Server Settings → Roles
  - Create new role: "Bot Alerts" or similar
  - Enable "Allow anyone to @mention this role"
  - Copy role ID (right-click role → Copy ID, requires Developer Mode)
- [ ] Add `DISCORD_ALERT_ROLE_ID` to GitHub Secrets
  - Format: just the numeric ID (e.g., "123456789012345678")
- [ ] Update `send_error_notification()` to use role mention
  - Format mention as: `<@&{role_id}>`
  - Add to webhook content (not embed)
  - Example: `<@&123456789> 🚨 **Fantasy Basketball Update Failed**`
- [ ] Test role mention functionality
  - Trigger error notification
  - Verify role is mentioned and users are notified

### Detailed Error Messages
- [ ] Add stack trace support to error notifications
  - Accept optional stack_trace parameter
  - Format as code block: ```python traceback```
  - Truncate to 1000 characters if needed
  - Add as separate embed field
- [ ] Add suggestion/action items to errors
  - Include helpful hints for common errors
  - Example: "Check GitHub Actions logs for details"
  - Add link to GitHub Actions logs
- [ ] Format GitHub Actions log link
  - Use GitHub context variables
  - Format: `${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}`
  - Include in embed field

### Configuration Options
- [ ] Add `DISCORD_NOTIFICATIONS_ENABLED` environment variable
  - Default: true if webhook URL is set
  - Allows disabling without removing webhook URL
  - Check in DiscordNotifier.__init__()
- [ ] Add verbosity level configuration (optional)
  - Environment variable: DISCORD_NOTIFICATION_VERBOSITY
  - Options: "minimal", "normal", "detailed"
  - Controls how much info is included in notifications

### Logging
- [ ] Add logging for notification attempts
  - Log before sending: "Sending Discord notification..."
  - Log after sending: "Discord notification sent successfully" or "Failed to send"
  - Include response status code
- [ ] Add structured logging for debugging
  - Log webhook URL (masked)
  - Log notification type (success/error)
  - Log response details on failure

### Fallback Mechanism
- [ ] Implement graceful failure
  - Wrap all Discord calls in try/except
  - Never let Discord errors crash main workflow
  - Log errors but continue execution
- [ ] Add warning when Discord is unavailable
  - Check if webhook URL is 404 (deleted webhook)
  - Log clear message: "Discord webhook not found. Update DISCORD_WEBHOOK_URL secret."
  - Continue without Discord notifications

**Deliverables**:
- Full-featured `discord_notifier.py`
- Configuration options in `.env.example`
- Comprehensive error handling
- Role mention functionality

---

## Phase 4: Documentation & Polish (1-2 hours)

**Goal**: Complete documentation and user guide

### Setup Guide
- [ ] Create `DISCORD_SETUP.md` guide
  - Overview of Discord integration
  - Benefits and features
  - Prerequisites
  - Step-by-step setup instructions:
    1. Create Discord webhook
    2. Add to GitHub Secrets
    3. Install discord-webhook library
    4. Configure environment variables
  - Testing instructions
  - Troubleshooting section
  - FAQ

### Update Existing Documentation
- [ ] Update `README.md` with Discord features
  - Add Discord integration to features list
  - Add section on automated notifications
  - Add command examples showing Discord integration
  - Add link to DISCORD_SETUP.md
  - Add Discord notification screenshots
- [ ] Update `CHANGELOG.md` with Discord integration
  - Add version entry (e.g., v2.1.0)
  - List new features
  - List new dependencies
  - List new configuration options
  - Breaking changes (if any)
- [ ] Update `CLAUDE.md` with Discord integration
  - Add discord_notifier.py to project structure
  - Document Discord environment variables
  - Add to key dependencies section

### Environment Variables Documentation
- [ ] Update `.env.example`
  - Add DISCORD_WEBHOOK_URL with example
  - Add DISCORD_ALERT_ROLE_ID with explanation
  - Add DISCORD_NOTIFICATIONS_ENABLED with default
  - Add comments explaining each variable
- [ ] Document environment variables in DISCORD_SETUP.md
  - Create table listing all Discord-related variables
  - Explain purpose and format of each
  - Mark which are required vs optional

### Visual Documentation
- [ ] Add screenshots of Discord notifications
  - Screenshot: Success notification
  - Screenshot: Error notification with role mention
  - Screenshot: Notification with transaction details
  - Save to `docs/discord/` or similar
  - Reference in documentation
- [ ] Create example notification gallery
  - Show different scenarios
  - Show different formatting options
  - Include captions explaining each

### Operational Documentation
- [ ] Document how to create/rotate webhook URLs
  - Step-by-step for creating webhook
  - Step-by-step for rotating webhook (if compromised)
  - How to update GitHub Secret
  - Zero-downtime rotation process
- [ ] Document how to set up role mentions
  - How to create role in Discord
  - How to enable mentions for role
  - How to get role ID
  - How to test role mentions
- [ ] Create troubleshooting guide in DISCORD_SETUP.md
  - Common issue: Webhook URL not working
  - Common issue: Role mentions not working
  - Common issue: Notifications not appearing
  - Common issue: Formatting issues
  - How to debug each issue
- [ ] Add FAQ section to DISCORD_SETUP.md
  - Q: Do I need Discord for the app to work?
  - Q: Can I use multiple webhooks?
  - Q: What happens if Discord is down?
  - Q: Can I disable notifications temporarily?
  - Q: How do I test notifications without spamming?
  - Q: What are the rate limits?

**Deliverables**:
- `DISCORD_SETUP.md` (comprehensive setup guide)
- Updated `README.md`
- Updated `CHANGELOG.md`
- Updated `CLAUDE.md`
- Updated `.env.example`
- Screenshots and examples
- Troubleshooting documentation

---

## Testing Checklist

### Basic Testing
- [ ] Test success notification with various update scenarios
  - 0 teams updated (no transactions)
  - Partial update (4-8 teams)
  - Full update (all teams)
- [ ] Test error notification with different error types
  - Yahoo API error
  - Google Sheets API error
  - General Python exception
- [ ] Test role mention functionality
  - Verify role is mentioned
  - Verify users with role are notified
  - Verify notification shows correctly

### Configuration Testing
- [ ] Test with Discord webhook disabled
  - Set DISCORD_NOTIFICATIONS_ENABLED=false
  - Verify app works without errors
  - Verify no Discord calls made
- [ ] Test webhook URL rotation
  - Delete webhook in Discord
  - Create new webhook
  - Update GitHub Secret
  - Verify new webhook works

### Edge Cases
- [ ] Test notification with very long transaction logs
  - Create scenario with many transactions
  - Verify truncation works (1024 char limit)
  - Verify "..." appears when truncated
- [ ] Test invalid webhook URL
  - Use invalid/malformed URL
  - Verify graceful error handling
  - Verify app continues without crashing

### Environment Testing
- [ ] Test in GitHub Actions environment
  - Verify secrets are passed correctly
  - Verify notifications sent from Actions
  - Verify fallback curl notification works
- [ ] Test notification formatting on mobile
  - View notification in Discord mobile app
  - Verify formatting is readable
  - Verify embeds display correctly
- [ ] Test notification formatting on desktop
  - View notification in Discord desktop app
  - Verify formatting is professional
  - Verify all elements display correctly

---

## Notes

### Security Considerations
- Discord webhook URL should be treated as a secret (never commit to repo)
- If webhook URL is exposed, delete webhook and create new one (takes 10 seconds)
- Webhook compromise only allows message spam, no data access or destructive actions
- Store webhook URL in GitHub Secrets for automated workflows

### Rate Limits
- Per webhook: 5 requests per 2 seconds
- Per channel: 30 messages per minute
- Global invalid requests: 10,000 per 10 minutes = 24-hour ban
- This project: ~1-2 messages per day (well under limits)
- Rate limits not a concern for this use case

### Discord Embed Limits
- Title: 256 characters
- Description: 4096 characters
- Field value: 1024 characters
- Footer: 2048 characters
- Author name: 256 characters
- Total embed: 6000 characters

### Key Principles
- **Graceful Degradation**: Discord failures should never break main workflow
- **User Experience**: Clear messages, helpful errors, professional formatting
- **Reliability**: Robust error handling, comprehensive logging
- **Maintainability**: Clean code, good documentation, modular structure
- **Cost**: Zero cost forever (no API keys, no quotas, no billing)

---

## Progress Tracking

**Phase 1**: ⬜ Not Started (0%)
**Phase 2**: ⬜ Not Started (0%)
**Phase 3**: ⬜ Not Started (0%)
**Phase 4**: ⬜ Not Started (0%)

**Overall Progress**: 0% Complete

---

*Mark items as complete with [x] as you finish them, and update the progress indicators above to track overall completion.*
