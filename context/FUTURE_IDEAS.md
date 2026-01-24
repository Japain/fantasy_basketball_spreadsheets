# Future Feature Ideas

This document contains ideas for future enhancements to the Fantasy Basketball Roster & Salary Report Generator. These ideas are not committed for implementation but serve as a reference for potential improvements.

---

## 1. Automation & Deployment

### ✅ Scheduled Daily Updates - COMPLETED (v2.1.0)
**Priority**: High | **Complexity**: Medium | **Status**: ✅ Implemented November 2025

Deploy the application to run automatically on a schedule.

**✅ IMPLEMENTED: GitHub Actions**
- Implemented in v2.1.0 (November 19, 2025)
- Zero-cost automated daily updates using GitHub Actions
- Runs at 11:00 AM UTC daily (configurable via cron syntax)
- Manual trigger capability via GitHub UI
- Comprehensive setup guide: `GITHUB_ACTIONS_SETUP.md`
- Deployment options research: `context/DEPLOYMENT_OPTIONS.md`
- See `CHANGELOG.md` for full implementation details

**Implementation Files**:
- `.github/workflows/daily-update.yml` - GitHub Actions workflow
- `GITHUB_ACTIONS_SETUP.md` - Complete setup and troubleshooting guide
- `context/DEPLOYMENT_OPTIONS.md` - Deployment options analysis

**Implemented Features**:
- ✅ Automated execution on schedule (cron-based)
- ✅ Cloud-based (no local machine required)
- ✅ OAuth token refresh in headless environment (Yahoo + Google)
- ✅ Secure credential management (GitHub Secrets)
- ✅ Error handling and automatic log upload
- ✅ Email notifications on failure
- ✅ Built-in monitoring and logging (90-day retention)
- ✅ Manual trigger capability
- ✅ Verbose logging with transaction details

**Alternative Options Documented** (not implemented):
- **Cron Job** (Linux/WSL) - Simplest but requires always-on machine
- **AWS Lambda** (Serverless) - High complexity, unnecessary for this use case
- **Google Cloud Run** (Serverless) - Excellent Google integration, alternative option
- **Azure Functions** - Timer reliability concerns

**Benefits Achieved**:
- ✅ No manual intervention needed
- ✅ Always up-to-date data
- ✅ Consistent update times
- ✅ Zero cost (within GitHub Actions free tier)
- ✅ Excellent logging and debugging
- ✅ Easy updates via git push

---

### Deployment to Cloud Platform
**Priority**: Low | **Complexity**: High

Deploy application to cloud platform for always-available access.

**Options**:
- **Heroku** - Simple deployment with buildpacks
- **Railway** - Modern platform with easy Python support
- **Google Cloud Run** - Serverless containers, good Google API integration
- **AWS ECS/Fargate** - Container orchestration
- **DigitalOcean App Platform** - Simple PaaS

**Features**:
- Web interface for manual triggers
- Environment variable management
- Automatic scaling
- Logging and monitoring

---

### Automated Backups
**Priority**: Low | **Complexity**: Low

Automatically backup spreadsheet data before updates.

**Implementation**:
- Export spreadsheet to Google Drive folder before update
- Keep last N versions (e.g., 7 days of daily backups)
- Automatic cleanup of old backups
- Backup metadata tracking (date, transaction count, teams updated)

---

## 2. Notifications & Alerts

### Email Notifications
**Priority**: Medium | **Complexity**: Low

Send email notifications when updates occur or errors happen.

**Notification Types**:
- **Update Summary** - Email after successful update with stats
  - Teams updated
  - Transactions processed
  - Link to spreadsheet
  - Efficiency metrics

- **Error Alerts** - Email when update fails
  - Error details
  - Timestamp
  - Suggestions for resolution

- **Weekly Digest** - Summary of week's activity
  - Total transactions
  - Most active teams
  - Biggest FAAB spends

**Implementation**:
- SendGrid, Mailgun, or Amazon SES
- HTML email templates
- Configurable recipients
- Digest scheduling

---

### Slack Integration
**Priority**: Medium | **Complexity**: Low

Post updates to Slack channel.

**Features**:
- Post notification when update completes
- Rich message format with blocks
- Include key stats and link to spreadsheet
- Error notifications
- Interactive buttons (e.g., "Force Full Update")

**Example Message**:
```
📊 Fantasy Basketball Update Complete
✅ Updated 4 of 16 teams (75% efficiency)
📈 6 transactions processed
🔗 View Spreadsheet
⏱️ Last update: 15 hours ago
```

---

### ✅ Discord Integration - COMPLETED (v2.1.0)
**Priority**: High | **Complexity**: Low ✅ Implemented November 2025

Similar to Slack but for Discord servers.

**Features**:
- ✅ Post notification when update completes
- ✅ Rich message format with blocks
- ✅ Include key stats and link to spreadsheet
- ✅ Error notifications
- ✅ Role mentions for important updates

**Example Message**:
```
📊 Fantasy Basketball Update Complete
✅ Updated 4 of 16 teams (25% updated)
📈 6 transactions processed
🔗 View Spreadsheet
⏱️ Last update: 15 hours ago
```

---

### Push Notifications
**Priority**: Low | **Complexity**: Medium

Mobile push notifications via service like Pushover or Pushbullet.

---

## 3. Data Visualization & Analytics

### Transaction History Sheet
**Priority**: High | **Complexity**: Medium

Add a dedicated sheet showing all recent transactions.

**Columns**:
- Date/Time
- Team Name
- Player Name
- Transaction Type (Add/Drop/Trade)
- FAAB Bid (if applicable)
- Previous Owner (for trades/waivers)

**Features**:
- Sortable by date, team, player
- Filterable by transaction type
- Color coding by transaction type
- Link to player stats

---

### Team Transaction Summary
**Priority**: Medium | **Complexity**: Low

Show transaction activity per team.

**Metrics**:
- Total transactions this week/month/season
- Total FAAB spent
- Average FAAB per transaction
- Most added/dropped players
- Transaction activity chart

---

### Salary Cap Trends
**Priority**: Low | **Complexity**: Medium

Track how team salaries change over time.

**Features**:
- Historical salary data
- Line chart showing salary cap usage over time
- Identify teams approaching salary cap
- Predict future cap issues based on trends

---

### League Parity Score
**Priority**: Low | **Complexity**: Medium

Calculate metrics showing league competitiveness.

**Metrics**:
- Salary distribution (Gini coefficient)
- Roster strength variance
- FAAB spending patterns
- Transaction activity by team

---

### Visual Charts & Graphs
**Priority**: Medium | **Complexity**: High

Add charts directly in Google Sheets.

**Chart Types**:
- Salary distribution by team (bar chart)
- FAAB remaining (pie chart)
- Transaction activity over time (line chart)
- Roster size by team (bar chart)
- Position breakdown by team (stacked bar)

**Implementation**:
- Google Sheets API chart creation
- Update charts on each run
- Interactive/drill-down capability

---

## 4. Multi-League Support

### Multiple Leagues in One Run
**Priority**: Medium | **Complexity**: Medium

Update spreadsheets for multiple leagues with single command.

**Features**:
- Configure multiple league IDs in config file
- Process all leagues sequentially or in parallel
- Consolidated summary across all leagues
- Per-league spreadsheets or combined spreadsheet

**CLI Example**:
```bash
uv run python main.py --all-leagues
uv run python main.py --leagues 12345,67890,11111
```

---

### Cross-League Comparison
**Priority**: Low | **Complexity**: Medium

Compare stats across multiple leagues.

**Metrics**:
- Average team salary by league
- Transaction activity by league
- FAAB spending patterns
- League competitiveness scores

---

### League Templates
**Priority**: Low | **Complexity**: Low

Save and reuse configuration templates for different league types.

**Templates**:
- Keeper league with auction draft
- Redraft league with snake draft
- Dynasty league
- Different salary cap settings

---

## 5. Historical Data & Tracking

### Season History Archive
**Priority**: Medium | **Complexity**: Medium

Archive end-of-season data for historical reference.

**Features**:
- Snapshot of final rosters
- Final standings
- Season transaction summary
- Champion roster preservation
- Year-over-year comparisons

---

### Change Detection & Diff View
**Priority**: High | **Complexity**: Medium

Show exactly what changed between updates.

**Features**:
- Side-by-side comparison view
- Highlight added/dropped players
- Salary changes (e.g., player dropped and re-added)
- Roster position changes
- Conditional formatting for changes

**Implementation**:
- Store previous state
- Compare with current state
- Generate diff report
- Optional separate "Changes" sheet

---

### Transaction Replay
**Priority**: Low | **Complexity**: High

Replay transactions to see roster state at any point in time.

**Features**:
- Select date/time
- View roster as it was at that moment
- Transaction timeline
- "What if" scenarios

---

### Weekly Snapshot History
**Priority**: Medium | **Complexity**: Medium

Automatic weekly snapshots of all rosters.

**Features**:
- Weekly "checkpoint" sheets
- Compare rosters week-over-week
- Track roster evolution over season
- Identify trends and patterns

---

## 6. User Interface

### Web Dashboard
**Priority**: Medium | **Complexity**: High

Create a web interface for easier management.

**Features**:
- View current spreadsheet status
- Manual update trigger
- Configure settings (league ID, spreadsheet URL)
- View update history and logs
- User authentication
- Mobile-responsive design

**Tech Stack Options**:
- **Flask** + **Tailwind CSS** - Simple and lightweight
- **FastAPI** + **React** - Modern and performant
- **Streamlit** - Rapid development, data-focused
- **Django** - Full-featured framework

**Pages**:
- Dashboard (overview, quick stats)
- Update Manager (trigger updates, view history)
- Settings (configure leagues, spreadsheets)
- Logs (view update logs, errors)
- Analytics (charts and metrics)

---

### CLI Interactive Mode
**Priority**: Low | **Complexity**: Low

Add interactive CLI mode with prompts.

**Features**:
```
Fantasy Basketball Manager
1. Create new spreadsheet
2. Update existing spreadsheet
3. View update history
4. Configure settings
5. Run diagnostics
Select option:
```

**Benefits**:
- User-friendly for non-technical users
- Guided workflow
- Input validation
- Help text at each step

---

### Desktop Application
**Priority**: Low | **Complexity**: High

Create a desktop GUI application.

**Options**:
- **Electron** - Cross-platform web-based
- **PyQt/PySide** - Native Python GUI
- **Tauri** - Lightweight alternative to Electron

---

## 7. Advanced Features

### Trade Analyzer
**Priority**: Low | **Complexity**: High

Analyze proposed trades for fairness and value.

**Features**:
- Input proposed trade
- Calculate value for each side
- Show salary cap impact
- Roster balance analysis
- Historical player performance
- Recommendation (Accept/Reject/Counter)

**Metrics**:
- Player value based on stats and salary
- Position need analysis
- Short-term vs. long-term impact
- Injury risk assessment

---

### Waiver Wire Recommendations
**Priority**: Low | **Complexity**: High

Suggest waiver wire pickups based on team needs.

**Features**:
- Analyze current roster
- Identify weaknesses (positions, categories)
- Search available players
- Recommend top pickups
- Calculate suggested FAAB bid
- Compare to league average bids

**Considerations**:
- Team strategy (punt categories)
- Remaining salary cap
- Roster depth at positions
- Player schedule (upcoming games)
- Injury status

---

### Keeper Value Analysis
**Priority**: Low | **Complexity**: Medium

Help managers decide which players to keep.

**Features**:
- List all possible keepers with costs
- Project player value for next season
- Calculate value over replacement
- Suggest optimal keeper combination
- Salary cap implications
- Age/injury risk factors

---

### Auction Draft Helper
**Priority**: Medium | **Complexity**: High

Assist during auction draft.

**Features**:
- Track nominations and winning bids
- Show remaining budget by team
- Use provided projection data to project team performance during the draft.
- Suggest next nomination
- Real-time roster building strategy

---

### Offseason Support
**Priority**: High | **Complexity**: Medium

Support league specific changes and updates that happen after the fantasy basketball season is over.

**Features**:
- For each team allow a space that list all of their current picks and future picks (Yahoo has no concept of these).
- Add a column to team sheet that tracks the number of years each player was in the league.
- Peform custom off season price increases based on user supplied league rules.
- Provide way in spread sheet for users to mark which players should be keepers for next year.

---

## 8. Integration & Export

### Export to CSV/Excel
**Priority**: Low | **Complexity**: Low

Export data in additional formats.

**Formats**:
- CSV (roster data, transactions)
- Excel (.xlsx)
- JSON (API-friendly)
- PDF (printable reports)

---

### API Endpoints
**Priority**: Low | **Complexity**: High

Provide REST API for data access.

**Endpoints**:
- `GET /api/league/{id}/roster` - Get league rosters
- `GET /api/league/{id}/transactions` - Get transactions
- `GET /api/team/{id}/roster` - Get team roster
- `POST /api/update` - Trigger update
- `GET /api/status` - Get update status

**Use Cases**:
- Custom integrations
- Mobile apps
- Third-party tools
- Data analysis in other platforms

---

### Webhook Support
**Priority**: Low | **Complexity**: Medium

Send data to external services via webhooks.

**Events**:
- Update completed
- Transaction detected
- Error occurred
- Threshold exceeded (e.g., salary cap)

**Payload**:
- Event type
- Timestamp
- Relevant data
- Spreadsheet link

---

### ESPN/Sleeper Integration
**Priority**: Low | **Complexity**: High

Support other fantasy platforms besides Yahoo.

**Platforms**:
- ESPN Fantasy
- Sleeper
- CBS Sports
- NFL.com

**Challenges**:
- Different API structures
- Different authentication methods
- Platform-specific features
- Maintaining compatibility

---

## 9. Performance & Optimization

### Caching Layer
**Priority**: Low | **Complexity**: Medium

Cache frequently accessed data to reduce API calls.

**Cache Targets**:
- League metadata (name, teams, settings)
- Player information (names, positions)
- Historical transaction data
- Team rosters (short TTL)

**Implementation**:
- Redis for distributed caching
- SQLite for local caching
- Configurable TTL by data type
- Cache invalidation strategies

---

### Incremental Transaction Fetching
**Priority**: Medium | **Complexity**: Medium

Fetch only new transactions, not all transactions each time.

**Current**: Fetches all transactions, filters by timestamp
**Proposed**: Fetch only transactions since last run

**Benefits**:
- Faster API calls
- Reduced Yahoo API load
- Lower rate limit risk

**Challenges**:
- Yahoo API pagination
- Ensuring no transactions missed
- Edge cases (very old last update)

---

### Parallel Sheet Updates
**Priority**: Medium | **Complexity**: Medium

Update multiple team sheets in parallel.

**Implementation**:
- Use Python `concurrent.futures`
- ThreadPoolExecutor or ProcessPoolExecutor
- Careful rate limit management
- Error handling per team

**Benefits**:
- Faster updates for large leagues
- Better resource utilization

**Challenges**:
- API rate limits
- Error aggregation
- Sheet lock conflicts

---

### Database Backend
**Priority**: Low | **Complexity**: High

Store data in database instead of relying only on Google Sheets.

**Benefits**:
- Faster queries
- Historical data storage
- Complex analytics
- Offline access

**Schema**:
- Teams table
- Players table
- Transactions table
- Rosters table (with history)
- Updates table (audit log)

**Database Options**:
- SQLite (simple, file-based)
- PostgreSQL (robust, feature-rich)
- MongoDB (document-based)

---

## 10. Administrative & Management

### Configuration Management UI
**Priority**: Low | **Complexity**: Medium

Web interface for managing configuration.

**Settings**:
- League IDs
- Spreadsheet URLs
- Update schedule
- Notification preferences
- API credentials (securely)
- Feature flags

---

### User Access Control
**Priority**: Low | **Complexity**: High

Multi-user support with different permission levels.

**Roles**:
- **Admin** - Full access, can configure settings
- **Manager** - Can trigger updates, view data
- **Viewer** - Read-only access to reports

**Features**:
- User authentication
- Role-based permissions
- Audit logging
- Team-specific access

---

### Health Monitoring Dashboard
**Priority**: Medium | **Complexity**: Medium

Monitor application health and status.

**Metrics**:
- Last successful update time
- Update success/failure rate
- API rate limit usage
- Error frequency
- Average update duration
- Sheet size and performance

**Alerts**:
- Failed updates
- API quota near limit
- Errors exceeding threshold
- Stale data warning

---

### Rollback Capability
**Priority**: Medium | **Complexity**: Medium

Ability to revert to previous version of data.

**Features**:
- Automatic backup before each update
- List available backup versions
- One-click rollback to specific version
- Diff view showing what will change
- Rollback confirmation

**Implementation**:
- Version control for spreadsheet data
- Export/import functionality
- Metadata tracking (timestamp, user, reason)

---

### Migration Tools
**Priority**: Low | **Complexity**: Low

Tools to migrate between platforms or versions.

**Use Cases**:
- Migrate from v1.0 to v2.0 spreadsheets
- Migrate from Yahoo to ESPN
- Migrate from one Google account to another
- Bulk update spreadsheet IDs

---

## 11. Testing & Quality

### Integration Test Suite Expansion
**Priority**: Medium | **Complexity**: Medium

Expand automated testing coverage.

**Additional Tests**:
- Performance benchmarks
- Load testing (large leagues)
- API rate limit handling
- Error recovery scenarios
- Backwards compatibility tests
- Cross-platform testing (Windows/Mac/Linux)

---

### Simulation Mode
**Priority**: Low | **Complexity**: Low

Dry-run mode that shows what would happen without making changes.

**Features**:
```bash
uv run python main.py --simulate --spreadsheet-id ID
```
- Show which teams would be updated
- Display changes that would be made
- Estimate API calls and runtime
- Validate without modifying data

---

## 12. Mobile & Accessibility

### Progressive Web App (PWA)
**Priority**: Low | **Complexity**: High

Mobile-friendly web app that works offline.

**Features**:
- Installable on mobile devices
- Offline data viewing
- Push notifications
- Responsive design
- Touch-optimized interface

---

### Mobile App
**Priority**: Low | **Complexity**: Very High

Native mobile application.

**Platforms**:
- iOS (Swift/SwiftUI)
- Android (Kotlin)
- React Native (cross-platform)
- Flutter (cross-platform)

**Features**:
- View current rosters
- Trigger updates
- View transaction history
- Push notifications
- Quick stats at a glance

---

## Implementation Priority Matrix

### High Priority, Low-Medium Complexity
1. ~~Scheduled Daily Updates~~ ✅ **COMPLETED in v2.1.0**
2. ~~Discord Integration~~ ✅ **COMPLETED in v2.2.0** 
3. Transaction History Sheet
4. Offseason Support
5. Change Detection & Diff View
6. Email Notifications

### High Priority, High Complexity
1. 
2. 

### Medium Priority, Low-Medium Complexity
1. Export to CSV/Excel
2. Visual Charts & Graphs
3. Rollback CapabilityTeam Transaction Summary
4. Incremental Transaction Fetching

## Medium Priority, High Complexity

### Low Priority (Nice to Have)
- Everything else marked as Low Priority

---

## Getting Started with Implementation

If you want to implement any of these features:

1. **Start Small**: Pick one feature from "High Priority, Low-Medium Complexity"
2. **Create Feature Branch**: `git checkout -b feature/transaction-history`
3. **Plan Implementation**: Update TODO.md with phases
4. **Test Thoroughly**: Add tests before merging
5. **Document**: Update README.md and CHANGELOG.md
6. **Iterate**: Get feedback and improve

---

## Contributing Ideas

Have an idea not listed here? Consider:
- Is it useful for most users?
- Is it technically feasible?
- Does it fit the project's scope?
- What's the complexity vs. benefit?

Add your ideas to this document via pull request!

---

**Last Updated**: November 21, 2025
