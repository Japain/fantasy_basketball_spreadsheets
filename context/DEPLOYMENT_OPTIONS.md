# Deployment Options for Scheduled Daily Updates

**Research Date**: November 19, 2025
**Project**: Fantasy Basketball Roster & Salary Report Generator
**Purpose**: Compare deployment options for automated daily spreadsheet updates

---

## Executive Summary

This document evaluates 5 deployment options for scheduling daily automated updates of the fantasy basketball application. The analysis considers technical feasibility, cost, implementation complexity, and maintenance requirements.

**Top Recommendation**: **GitHub Actions** - Zero cost, excellent reliability, no local machine dependency, great developer experience.

**Alternative**: **Google Cloud Run** - Perfect integration with Google ecosystem, zero cost within free tier.

---

## Table of Contents

1. [Project Requirements](#project-requirements)
2. [Deployment Options Analyzed](#deployment-options-analyzed)
3. [Detailed Analysis](#detailed-analysis)
4. [Comparison Matrix](#comparison-matrix)
5. [Rankings](#rankings)
6. [Recommendations](#recommendations)
7. [Implementation Guidance](#implementation-guidance)

---

## Project Requirements

### Application Characteristics
- **Runtime**: Python 3.12 with `uv` package manager
- **Execution Time**: 30-60 seconds per run
- **Frequency**: Once daily (e.g., 8 AM)
- **APIs Used**: Yahoo Fantasy Sports API, Google Sheets API
- **Authentication**: OAuth 2.0 for both APIs (requires token refresh)
- **Command**: `uv run python main.py --spreadsheet-id ID`

### Key Requirements
1. Headless OAuth support (Yahoo and Google APIs)
2. Secure credential storage
3. Scheduled execution (daily at specific time)
4. Error handling and monitoring
5. Cost-effectiveness (personal project)
6. Ease of setup and maintenance
7. Token caching and refresh automation

---

## Deployment Options Analyzed

1. **Cron Job** - Linux/WSL local machine scheduled task
2. **GitHub Actions** - Cloud-based CI/CD with scheduled workflows
3. **AWS Lambda** - AWS serverless compute service
4. **Google Cloud Run** - Google Cloud serverless container platform
5. **Azure Functions** - Microsoft Azure serverless compute

---

## Detailed Analysis

### 1. Cron Job (Linux/WSL)

#### Overview
Traditional scheduled task running on a local Linux machine or WSL environment.

#### Technical Feasibility
- **Python Support**: ✅ Native Python 3.12 support
- **Package Installation**: ✅ Direct `uv` installation
- **OAuth Handling**: ✅ Easy - tokens stored locally as files
- **Secrets Management**: File-based `.env` or environment variables
- **Execution Limits**: ❌ None - but requires always-on machine
- **File System**: ✅ Full file system access

#### Implementation Steps
1. Install dependencies: `uv sync`
2. Add cron entry: `crontab -e`
3. Example: `0 8 * * * cd /path/to/fantasy_basketball && uv run python main.py --spreadsheet-id ID >> logs/cron.log 2>&1`

#### Scheduling
- **Mechanism**: Standard cron syntax
- **Timezone**: Uses system timezone
- **Reliability**: Dependent on machine uptime

#### Cost
- **Free Tier**: N/A (local machine)
- **Monthly Cost**: $0 (assuming machine already running)
- **Hidden Costs**: Electricity, machine must run 24/7

#### Monitoring & Debugging
- **Logging**: Manual log file management
- **Error Alerting**: Custom solution required
- **Debugging**: Direct file system access
- **Tools**: Tail logs, system logs

#### Maintenance
- **Token Refresh**: Automatic via OAuth libraries
- **Updates**: Manual git pull and restart
- **Limitations**: Machine must be always-on
- **Vendor Lock-in**: None

#### Security
- **Credentials**: File-based `.env` file
- **Token Storage**: Local pickle/JSON files
- **Risks**: Physical machine access

#### Pros
✅ Simplest setup (5 minutes)
✅ Zero additional cost
✅ Full control over environment
✅ No cloud complexity
✅ Easy debugging with local file access
✅ No external dependencies

#### Cons
❌ Machine must run 24/7
❌ No redundancy (single point of failure)
❌ WSL on Windows may sleep/hibernate
❌ Manual monitoring required
❌ No built-in alerting
❌ Limited if traveling or machine offline

#### Showstoppers
- **WSL Limitation**: If using WSL on Windows, system sleep/hibernate will prevent execution
- **Always-On**: Requires dedicated machine or server

#### Use Cases
- Local development machine that's always on
- Home server or Raspberry Pi
- Quick testing before cloud deployment
- Maximum control and simplicity preferred

#### Implementation Difficulty
**Rating**: 1/5 (Easiest)
**Setup Time**: 5 minutes

#### Cost Rating
**Rating**: 1/5 (Cheapest)
**Monthly Cost**: $0

---

### 2. GitHub Actions

#### Overview
Cloud-based CI/CD platform with scheduled workflow support built into GitHub.

#### Technical Feasibility
- **Python Support**: ✅ Native Python 3.12 support
- **Package Installation**: ✅ `uv` can be installed in workflow
- **OAuth Handling**: ⚠️ Medium complexity - refresh tokens in secrets
- **Secrets Management**: GitHub Secrets (encrypted)
- **Execution Limits**: ✅ 6 hours max (more than sufficient)
- **File System**: ✅ Ephemeral but sufficient for token caching

#### Implementation Steps
1. Create `.github/workflows/daily-update.yml`
2. Add secrets to GitHub repo settings
3. Configure schedule and environment variables
4. Commit and push workflow file

#### Scheduling
- **Mechanism**: Cron syntax in workflow file
- **Timezone**: UTC (can be adjusted)
- **Reliability**: High - managed by GitHub infrastructure
- **Accuracy**: ±5 minutes (GitHub's documented variance)

#### Cost
- **Free Tier**: 2,000 minutes/month (private repos), unlimited (public repos)
- **Monthly Usage**: ~30 minutes (1 min/day × 30 days)
- **Monthly Cost**: $0 (well within free tier)
- **Overage**: $0.008/minute (unlikely to reach)

#### Monitoring & Debugging
- **Logging**: Built-in workflow logs (retained for 90 days)
- **Error Alerting**: Email notifications on failure
- **Debugging**: Workflow run history with full logs
- **Tools**: GitHub Actions UI, workflow annotations

#### Maintenance
- **Token Refresh**: Store refresh tokens in secrets, update on expiry
- **Updates**: Automatic on git push
- **Limitations**: 6-hour execution limit (not an issue)
- **Vendor Lock-in**: Low (workflow YAML is portable)

#### Security
- **Credentials**: GitHub Secrets (encrypted at rest)
- **Token Storage**: GitHub Secrets + workflow artifact caching
- **Access Control**: Repository permissions
- **Best Practice**: Use environment secrets, not repository secrets

#### Pros
✅ Zero cost (free tier sufficient)
✅ No local machine required
✅ Excellent logging and debugging
✅ Built-in CI/CD integration
✅ Email notifications on failure
✅ Easy to modify schedule
✅ Manual trigger available (workflow_dispatch)
✅ Great developer experience

#### Cons
⚠️ Token refresh requires secret updates (can automate)
⚠️ Schedule accuracy ±5 minutes
⚠️ OAuth setup more complex than local
❌ Public repos expose workflow file

#### Showstoppers
None identified. This is a well-suited solution.

#### Use Cases
- Code already in GitHub (this project)
- Want zero-cost cloud solution
- Need reliable scheduled execution
- Prefer integrated logging and monitoring
- Want to avoid managing infrastructure

#### Implementation Difficulty
**Rating**: 2/5 (Easy)
**Setup Time**: 30 minutes

#### Cost Rating
**Rating**: 1/5 (Free)
**Monthly Cost**: $0

---

### 3. AWS Lambda

#### Overview
AWS serverless compute service with event-driven and scheduled execution.

#### Technical Feasibility
- **Python Support**: ✅ Python 3.12 runtime available
- **Package Installation**: ⚠️ Complex - must package dependencies as Lambda layer
- **OAuth Handling**: ⚠️ Requires S3 or DynamoDB for token persistence
- **Secrets Management**: AWS Secrets Manager or SSM Parameter Store
- **Execution Limits**: ✅ 15 minutes max (sufficient)
- **File System**: ⚠️ Limited `/tmp` (512 MB), need S3 for persistence

#### Implementation Steps
1. Create Lambda function with Python 3.12 runtime
2. Package dependencies (complex with `uv`)
3. Set up EventBridge (CloudWatch Events) schedule
4. Configure environment variables and secrets
5. Set up S3 bucket for token storage
6. Configure IAM roles and permissions

#### Scheduling
- **Mechanism**: EventBridge rules (cron expressions)
- **Timezone**: UTC or custom
- **Reliability**: Very high
- **Accuracy**: High precision

#### Cost
- **Free Tier**: 1M requests/month, 400,000 GB-seconds compute
- **Monthly Usage**: 30 requests × 1 minute × 128 MB = minimal
- **Monthly Cost**: ~$0.05 (essentially free)
- **Additional**: Secrets Manager ($0.40/secret/month) or SSM (free)

#### Monitoring & Debugging
- **Logging**: CloudWatch Logs (automatic)
- **Error Alerting**: CloudWatch Alarms, SNS notifications
- **Debugging**: CloudWatch Insights, X-Ray tracing
- **Tools**: AWS Console, AWS CLI

#### Maintenance
- **Token Refresh**: Custom logic to persist to S3
- **Updates**: Deploy new Lambda package
- **Limitations**: Packaging complexity with `uv`
- **Vendor Lock-in**: High (AWS-specific)

#### Security
- **Credentials**: AWS Secrets Manager or SSM
- **Token Storage**: S3 with encryption
- **IAM**: Fine-grained permissions
- **VPC**: Optional VPC integration

#### Pros
✅ Highly reliable infrastructure
✅ Excellent monitoring via CloudWatch
✅ Scales automatically (not needed here)
✅ Fine-grained IAM permissions
✅ Very low cost
✅ Enterprise-grade features

#### Cons
❌ Complex packaging for Python dependencies
❌ Steeper learning curve
❌ OAuth token persistence requires S3 setup
❌ High vendor lock-in
❌ Overkill for simple scheduled task
⚠️ `uv` not natively supported (use pip in Lambda)

#### Showstoppers
- **Packaging Complexity**: `uv` requires custom build process for Lambda
- **Token Persistence**: Requires additional AWS services (S3, Secrets Manager)

#### Use Cases
- Already using AWS ecosystem
- Need enterprise-grade reliability
- Want fine-grained IAM controls
- Building larger AWS-based solution
- Team experienced with AWS

#### Implementation Difficulty
**Rating**: 4/5 (Hard)
**Setup Time**: 2-3 hours

#### Cost Rating
**Rating**: 2/5 (Very cheap)
**Monthly Cost**: ~$0.05-0.50 (depending on Secrets Manager usage)

---

### 4. Google Cloud Run

#### Overview
Google Cloud serverless container platform with scheduled execution via Cloud Scheduler.

#### Technical Feasibility
- **Python Support**: ✅ Full Python 3.12 via containers
- **Package Installation**: ✅ Standard Dockerfile with `uv`
- **OAuth Handling**: ✅ Excellent - same ecosystem as Google Sheets
- **Secrets Management**: Secret Manager (native integration)
- **Execution Limits**: ✅ 60 minutes max (more than sufficient)
- **File System**: ⚠️ Ephemeral, use Cloud Storage for persistence

#### Implementation Steps
1. Create `Dockerfile` with Python 3.12 and dependencies
2. Build and push container to Google Container Registry
3. Deploy to Cloud Run
4. Set up Cloud Scheduler to trigger endpoint
5. Configure secrets in Secret Manager
6. Set up service account with appropriate permissions

#### Scheduling
- **Mechanism**: Cloud Scheduler (cron syntax)
- **Timezone**: Any timezone supported
- **Reliability**: Very high
- **Accuracy**: High precision

#### Cost
- **Free Tier**: 2M requests/month, 360,000 GB-seconds compute
- **Monthly Usage**: 30 requests × 1 minute × 256 MB = minimal
- **Monthly Cost**: $0 (well within free tier)
- **Additional**: Cloud Scheduler $0.10/job/month (first 3 free)

#### Monitoring & Debugging
- **Logging**: Cloud Logging (automatic)
- **Error Alerting**: Cloud Monitoring alerts
- **Debugging**: Cloud Logging, Cloud Trace
- **Tools**: Google Cloud Console

#### Maintenance
- **Token Refresh**: Use Secret Manager, automatic refresh
- **Updates**: Deploy new container image
- **Limitations**: Container build required for updates
- **Vendor Lock-in**: Medium (containerized is portable)

#### Security
- **Credentials**: Secret Manager (encrypted)
- **Token Storage**: Secret Manager or Cloud Storage
- **Service Account**: Fine-grained IAM
- **Best Practice**: Same Google Cloud project as Sheets

#### Pros
✅ Perfect Google ecosystem integration
✅ Excellent OAuth support (same Google Cloud)
✅ Zero cost (free tier sufficient)
✅ Container flexibility
✅ Great logging and monitoring
✅ Service accounts for Google APIs
✅ Timezone-aware scheduling

#### Cons
⚠️ Requires Dockerfile creation
⚠️ Container build process
⚠️ More complex than GitHub Actions
❌ Learning curve for GCP services

#### Showstoppers
None identified. Excellent fit for Google Sheets integration.

#### Use Cases
- Heavy Google ecosystem integration
- Want zero-cost cloud solution
- Prefer containerized deployments
- Need flexible execution environment
- Already familiar with Google Cloud

#### Implementation Difficulty
**Rating**: 3/5 (Medium)
**Setup Time**: 1-2 hours

#### Cost Rating
**Rating**: 1/5 (Free)
**Monthly Cost**: $0

---

### 5. Azure Functions

#### Overview
Microsoft Azure serverless compute platform with timer trigger support.

#### Technical Feasibility
- **Python Support**: ✅ Python 3.11 (3.12 in preview)
- **Package Installation**: ⚠️ Use pip, `uv` not officially supported
- **OAuth Handling**: ⚠️ Requires Azure Storage for token persistence
- **Secrets Management**: Azure Key Vault
- **Execution Limits**: ✅ 10 minutes (consumption plan)
- **File System**: ⚠️ Limited local storage, use Blob Storage

#### Implementation Steps
1. Create Azure Function App
2. Set up timer trigger function
3. Configure application settings
4. Deploy code via Azure CLI or VS Code
5. Set up Azure Key Vault for secrets
6. Configure Azure Storage for token persistence

#### Scheduling
- **Mechanism**: Timer trigger (cron expressions)
- **Timezone**: UTC or custom
- **Reliability**: ⚠️ Known issues with timer reliability
- **Accuracy**: Can have delays

#### Cost
- **Free Tier**: 1M requests/month, 400,000 GB-seconds
- **Monthly Usage**: 30 requests × 1 minute × 256 MB = minimal
- **Monthly Cost**: ~$0.10
- **Additional**: Key Vault ($0.03/10K operations)

#### Monitoring & Debugging
- **Logging**: Application Insights (automatic)
- **Error Alerting**: Application Insights alerts
- **Debugging**: Azure Portal, Application Insights
- **Tools**: Azure CLI, VS Code extension

#### Maintenance
- **Token Refresh**: Custom logic with Blob Storage
- **Updates**: Deploy via Azure CLI or portal
- **Limitations**: Timer reliability concerns
- **Vendor Lock-in**: High (Azure-specific)

#### Security
- **Credentials**: Azure Key Vault
- **Token Storage**: Blob Storage with encryption
- **Managed Identity**: Azure AD integration
- **Best Practice**: Use system-assigned managed identity

#### Pros
✅ Low cost
✅ Good Azure ecosystem integration
✅ Application Insights monitoring
✅ Managed identity for Azure services

#### Cons
❌ Python 3.12 not generally available yet
❌ Known timer trigger reliability issues
❌ `uv` not officially supported
❌ Token persistence requires Blob Storage
⚠️ More complex than GitHub Actions
⚠️ Higher vendor lock-in

#### Showstoppers
- **Timer Reliability**: Documented issues with timer triggers missing scheduled executions
- **Python Version**: 3.12 not yet generally available

#### Use Cases
- Already using Azure ecosystem
- Need Azure-specific integrations
- Team experienced with Azure
- Acceptable reliability requirements

#### Implementation Difficulty
**Rating**: 3/5 (Medium)
**Setup Time**: 1-2 hours

#### Cost Rating
**Rating**: 2/5 (Very cheap)
**Monthly Cost**: ~$0.10

---

## Comparison Matrix

| Feature | Cron Job | GitHub Actions | AWS Lambda | Google Cloud Run | Azure Functions |
|---------|----------|----------------|------------|------------------|-----------------|
| **Python 3.12 Support** | ✅ Native | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Preview |
| **Setup Time** | 5 min | 30 min | 2-3 hrs | 1-2 hrs | 1-2 hrs |
| **Monthly Cost** | $0* | $0 | ~$0.05 | $0 | ~$0.10 |
| **Reliability** | Medium | High | Very High | Very High | Medium |
| **OAuth Complexity** | Low | Medium | High | Medium | High |
| **Maintenance** | Low | Low | Medium | Medium | Medium |
| **Cloud-based** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Logging Quality** | Manual | Excellent | Excellent | Excellent | Good |
| **Error Alerting** | Manual | Built-in | Configurable | Configurable | Configurable |
| **Token Persistence** | Easy | Medium | S3 Required | Storage | Blob Storage |
| **Scheduling Accuracy** | High | ±5 min | High | High | Medium |
| **Vendor Lock-in** | None | Low | High | Medium | High |
| **Learning Curve** | None | Low | Medium | Medium | Medium |
| **Debugging Ease** | Easy | Easy | Medium | Medium | Medium |
| **`uv` Support** | ✅ Native | ✅ Installable | ⚠️ Complex | ✅ Dockerfile | ❌ Use pip |

*Cron requires always-on machine

---

## Rankings

### By Implementation Difficulty (1=easiest, 5=hardest)

1. **Cron Job** - 1/5 (5 minutes)
   - Add one line to crontab, done

2. **GitHub Actions** - 2/5 (30 minutes)
   - Create workflow file, add secrets, commit

3. **Google Cloud Run** - 3/5 (1-2 hours)
   - Create Dockerfile, build container, deploy, configure scheduler

4. **Azure Functions** - 3/5 (1-2 hours)
   - Create function app, configure trigger, deploy code

5. **AWS Lambda** - 4/5 (2-3 hours)
   - Package dependencies, configure EventBridge, set up S3, IAM roles

### By Monthly Cost (1=cheapest, 5=most expensive)

1. **GitHub Actions** - $0/month (free tier sufficient)
2. **Cron Job** - $0/month (machine already running)
3. **Google Cloud Run** - $0/month (free tier sufficient)
4. **AWS Lambda** - ~$0.05/month (minimal usage)
5. **Azure Functions** - ~$0.10/month (minimal usage)

### By Reliability (1=best, 5=worst)

1. **AWS Lambda** - Very High (enterprise infrastructure)
2. **Google Cloud Run** - Very High (Google infrastructure)
3. **GitHub Actions** - High (±5 min accuracy acceptable)
4. **Cron Job** - Medium (depends on machine uptime)
5. **Azure Functions** - Medium (known timer issues)

### By Maintenance Burden (1=lowest, 5=highest)

1. **GitHub Actions** - Automatic updates on git push
2. **Cron Job** - Manual git pull and no cloud complexity
3. **Google Cloud Run** - Container rebuilds required
4. **Azure Functions** - Function deployments required
5. **AWS Lambda** - Package uploads and IAM management

### By OAuth Ease (1=easiest, 5=hardest)

1. **Cron Job** - Direct file-based token storage
2. **Google Cloud Run** - Same Google ecosystem
3. **GitHub Actions** - Secrets + artifact caching
4. **Azure Functions** - Blob Storage required
5. **AWS Lambda** - S3 + custom persistence logic

---

## Recommendations

### Primary Recommendation: GitHub Actions

**Best for**: Most users, especially if code is already in GitHub

**Why GitHub Actions wins:**
1. ✅ **Zero cost** - Free tier is more than sufficient
2. ✅ **No infrastructure** - No local machine or cloud setup needed
3. ✅ **Excellent DX** - Great logging, easy debugging, built-in notifications
4. ✅ **Easy updates** - Automatic on git push
5. ✅ **Low lock-in** - Workflow files are relatively portable
6. ✅ **Quick setup** - 30 minutes to get running

**Trade-offs:**
- Schedule accuracy is ±5 minutes (acceptable for daily runs)
- OAuth requires storing refresh tokens in secrets (standard practice)

**When to choose GitHub Actions:**
- Your code is in GitHub (already true for this project)
- You want minimal setup and maintenance
- Cost is a concern (free)
- You want integrated CI/CD capabilities
- You value developer experience and logging

### Alternative: Google Cloud Run

**Best for**: Google ecosystem integration, container flexibility

**Why consider Google Cloud Run:**
1. ✅ **Perfect Google fit** - Same ecosystem as Google Sheets API
2. ✅ **Zero cost** - Free tier is sufficient
3. ✅ **Container flexibility** - Full control over environment
4. ✅ **Service accounts** - Native Google Cloud authentication
5. ✅ **Timezone support** - Full timezone control

**Trade-offs:**
- Requires Dockerfile creation
- Container build process for updates
- Steeper learning curve than GitHub Actions

**When to choose Google Cloud Run:**
- You plan to add more Google Cloud features later
- You prefer containerized deployments
- You're already familiar with Google Cloud
- You want maximum Google API integration

### Budget-Conscious: Cron Job

**Best for**: Quick testing, local development, always-on home server

**Why consider Cron Job:**
1. ✅ **Fastest setup** - 5 minutes
2. ✅ **Zero cost** - No cloud expenses
3. ✅ **Simple** - No cloud complexity
4. ✅ **Easy OAuth** - File-based token storage

**Trade-offs:**
- Machine must run 24/7
- No redundancy or failover
- Manual monitoring required
- WSL users may face issues with system sleep

**When to choose Cron Job:**
- You have a home server or Raspberry Pi
- You want to test before cloud deployment
- You prefer maximum control and simplicity
- Your machine is always on anyway

### Avoid Unless...

**AWS Lambda**:
- ❌ Avoid unless already heavily invested in AWS
- ❌ Unnecessary complexity for this use case
- ⚠️ Consider only if: building larger AWS solution, need AWS-specific features

**Azure Functions**:
- ❌ Avoid due to timer reliability issues
- ❌ Python 3.12 not generally available yet
- ⚠️ Consider only if: already using Azure ecosystem, acceptable reliability requirements

---

## Implementation Guidance

### Quick Start: GitHub Actions (Recommended)

**Time Required**: 30 minutes
**Skill Level**: Beginner-Intermediate

**Steps**:

1. **Create Workflow File** (`.github/workflows/daily-update.yml`):
```yaml
name: Daily Fantasy Basketball Update

on:
  schedule:
    # Runs at 8:00 AM UTC daily
    - cron: '0 8 * * *'
  workflow_dispatch: # Allow manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run update
        env:
          YAHOO_CONSUMER_KEY: ${{ secrets.YAHOO_CONSUMER_KEY }}
          YAHOO_CONSUMER_SECRET: ${{ secrets.YAHOO_CONSUMER_SECRET }}
          NBA_LEAGUE_ID: ${{ secrets.NBA_LEAGUE_ID }}
          NBA_GAME_ID: ${{ secrets.NBA_GAME_ID }}
          INITIAL_AUCTION_BUDGET: ${{ secrets.INITIAL_AUCTION_BUDGET }}
          GOOGLE_CREDENTIALS_PATH: ${{ secrets.GOOGLE_CREDENTIALS_PATH }}
          SPREADSHEET_ID: ${{ secrets.SPREADSHEET_ID }}
        run: |
          uv run python main.py --spreadsheet-id $SPREADSHEET_ID --verbose
```

2. **Add Secrets to GitHub**:
   - Go to repository Settings → Secrets → Actions
   - Add each secret from your `.env` file
   - Include: `YAHOO_CONSUMER_KEY`, `YAHOO_CONSUMER_SECRET`, `NBA_LEAGUE_ID`, `NBA_GAME_ID`, `INITIAL_AUCTION_BUDGET`, `SPREADSHEET_ID`
   - For Google credentials, encode JSON as base64: `cat credentials/client_secret.json | base64`

3. **Handle OAuth Tokens**:
   - Initial run: Authenticate locally, get refresh tokens
   - Add refresh tokens to GitHub Secrets
   - Workflow uses refresh tokens for authentication

4. **Test**:
   - Push workflow file to GitHub
   - Go to Actions tab → Daily Fantasy Basketball Update
   - Click "Run workflow" to manually test
   - Check logs for success

5. **Monitor**:
   - Check Actions tab for daily runs
   - Enable email notifications for failures

### Alternative: Google Cloud Run

**Time Required**: 1-2 hours
**Skill Level**: Intermediate

**Steps**:

1. **Create Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Run the application
CMD ["uv", "run", "python", "main.py", "--spreadsheet-id", "$SPREADSHEET_ID", "--verbose"]
```

2. **Build and Deploy**:
```bash
# Authenticate with Google Cloud
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/fantasy-basketball

# Deploy to Cloud Run
gcloud run deploy fantasy-basketball \
  --image gcr.io/YOUR_PROJECT_ID/fantasy-basketball \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated
```

3. **Set Up Secrets**:
```bash
# Create secrets in Secret Manager
echo -n "YOUR_VALUE" | gcloud secrets create YAHOO_CONSUMER_KEY --data-file=-
# Repeat for all secrets
```

4. **Configure Cloud Scheduler**:
```bash
# Create scheduled job
gcloud scheduler jobs create http fantasy-basketball-daily \
  --schedule="0 8 * * *" \
  --uri="YOUR_CLOUD_RUN_URL" \
  --http-method=POST \
  --oidc-service-account-email=YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com
```

5. **Monitor**:
   - View logs in Cloud Logging
   - Set up alerts in Cloud Monitoring

### Quick Start: Cron Job (Testing)

**Time Required**: 5 minutes
**Skill Level**: Beginner

**Steps**:

1. **Open crontab**:
```bash
crontab -e
```

2. **Add cron entry**:
```bash
# Run daily at 8 AM
0 8 * * * cd /home/ripl/code/fantasy_basketball && uv run python main.py --spreadsheet-id YOUR_SPREADSHEET_ID --verbose >> logs/cron.log 2>&1
```

3. **Create log directory**:
```bash
mkdir -p logs
```

4. **Verify cron entry**:
```bash
crontab -l
```

5. **Monitor**:
```bash
tail -f logs/cron.log
```

---

## Decision Framework

Use this flowchart to choose your deployment option:

```
Is your code in GitHub?
├─ Yes → Use GitHub Actions ⭐
│
└─ No → Do you already use Google Cloud?
    ├─ Yes → Use Google Cloud Run
    │
    └─ No → Do you have an always-on machine?
        ├─ Yes → Use Cron Job (simplest)
        │
        └─ No → Set up GitHub Actions (best ROI)
```

**Special Cases**:
- **AWS ecosystem**: Use AWS Lambda (despite complexity)
- **Azure ecosystem**: Use Azure Functions (watch for timer issues)
- **Enterprise requirements**: AWS Lambda or Google Cloud Run
- **Maximum simplicity**: Cron Job (if machine available)
- **Best overall**: GitHub Actions (balanced across all factors)

---

## Next Steps

### Recommended Path (GitHub Actions)

1. ✅ Document findings (this file)
2. ⬜ Create `.github/workflows/daily-update.yml`
3. ⬜ Add secrets to GitHub repository
4. ⬜ Test manual workflow trigger
5. ⬜ Monitor first scheduled run
6. ⬜ Update `README.md` with deployment instructions
7. ⬜ Consider adding email notifications

### Future Enhancements

Once scheduled updates are working:
- Add Discord/Slack notifications (see `FUTURE_IDEAS.md`)
- Implement error alerting
- Add transaction summary emails
- Create health monitoring dashboard
- Implement backup strategy

---

## Conclusion

For this fantasy basketball project, **GitHub Actions** is the clear winner:
- Zero cost
- Minimal setup (30 minutes)
- Excellent reliability and logging
- No infrastructure to manage
- Perfect fit for code already in GitHub

**Google Cloud Run** is an excellent alternative if you want deeper Google ecosystem integration or plan to expand functionality later.

**Avoid** Azure Functions (reliability issues) and AWS Lambda (unnecessary complexity) unless you have specific ecosystem requirements.

The simplicity and effectiveness of GitHub Actions make it the best choice for automated daily updates of your fantasy basketball spreadsheets.

---

**Last Updated**: November 19, 2025
**Researched By**: Claude Code Researcher Agent
**Document Version**: 1.0
