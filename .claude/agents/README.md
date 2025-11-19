# Specialized Agents for Fantasy Basketball Application

This directory contains specialized agent configurations to assist with development, testing, and maintenance of the Fantasy Basketball Roster & Salary Report Generator.

## Available Agents

### 1. Researcher Agent (`researcher-agent.md`)
**Focus**: Investigation, architectural analysis, and implementation strategy comparison

**Responsibilities**:
- Research multiple approaches for implementing new features
- Analyze pros and cons of different architectural patterns
- Evaluate third-party libraries and tools
- Compare implementation complexity vs. benefits
- Assess technical constraints and trade-offs
- Review existing codebase patterns for consistency
- Investigate best practices and industry standards
- Provide recommendations with detailed justification
- Consider maintainability, scalability, and cost implications
- Research API capabilities and limitations

**When to Use**:
- Before implementing a major new feature
- When multiple implementation approaches are possible
- For architectural decisions that affect multiple modules
- When evaluating new dependencies or libraries
- Before choosing a deployment strategy
- When planning refactoring efforts
- To investigate API limitations or capabilities

**Example Tasks**:
- "Research 3 different approaches for implementing scheduled daily updates (cron, GitHub Actions, cloud functions)"
- "Compare database options (SQLite, PostgreSQL, MongoDB) for historical data storage"
- "Investigate best patterns for implementing a web dashboard (Flask+React, FastAPI+Vue, Streamlit)"
- "Research how to handle Yahoo API rate limiting - compare exponential backoff vs. request queuing vs. caching"
- "Analyze pros/cons of adding a transaction history sheet vs. a separate database"

**Key Skills**:
- Research and analytical thinking
- Understanding of software architecture patterns
- Knowledge of deployment platforms and their trade-offs
- Ability to evaluate technical complexity
- Cost-benefit analysis
- Understanding of the existing codebase structure

---

### 2. Testing Agent (`testing-agent.md`)
**Focus**: Code verification, test creation, and quality assurance

**Responsibilities**:
- Write comprehensive unit tests for new features
- Create integration tests that verify end-to-end workflows
- Validate edge cases and error handling
- Ensure test coverage for API interactions (Yahoo + Google)
- Review existing tests and suggest improvements
- Run test suites and analyze results
- Generate test reports with coverage metrics
- Create test data and fixtures
- Debug failing tests
- Implement test automation

**When to Use**:
- After implementing a new feature
- When refactoring existing code
- Before deploying to production
- When debugging test failures
- To improve test coverage
- For regression testing

**Example Tasks**:
- "Create comprehensive tests for the new transaction history feature"
- "Review test coverage and identify gaps in the sheet updater module"
- "Debug why test_incremental_update is failing with rate limit errors"
- "Create integration tests for the new multi-league support feature"

**Key Skills**:
- Understanding of pytest and Python testing patterns
- Knowledge of mocking API calls (Yahoo Fantasy API, Google Sheets API)
- Experience with data validation and edge case testing
- Familiarity with test organization and best practices

---

### 3. Integration Agent (`integration-agent.md`)
**Focus**: Yahoo and Google API integrations, authentication, and data exchange

**Responsibilities**:
- Maintain and enhance Yahoo Fantasy API integration
- Manage Google Sheets API interactions
- Handle OAuth 2.0 authentication flows
- Debug API-related issues and rate limiting
- Optimize API call efficiency
- Implement new API endpoints or features
- Handle API version updates and breaking changes
- Ensure error handling for network/API failures
- Implement batch operations and request optimization
- Monitor API usage and quotas

**When to Use**:
- When adding new Yahoo API data sources
- When enhancing Google Sheets functionality
- For authentication or token refresh issues
- When API rate limits need optimization
- To implement new data retrieval strategies
- For debugging API errors

**Example Tasks**:
- "Add support for fetching player projections from Yahoo API"
- "Optimize Google Sheets batch updates to reduce API calls"
- "Debug OAuth token refresh issues in headless environment"
- "Implement retry logic with exponential backoff for API failures"

**Key Skills**:
- Deep knowledge of yfpy library and Yahoo Fantasy API
- Expertise in Google Sheets API (spreadsheets service)
- OAuth 2.0 authentication patterns
- API error handling and retry logic
- Rate limiting and batch request optimization

---

### 4. Data Pipeline Agent (`data-pipeline-agent.md`)
**Focus**: Data flow, transformations, validation, and business logic

**Responsibilities**:
- Manage data models (Player, Team, League, Transaction)
- Implement salary calculation logic and strategies
- Handle data transformations between Yahoo API → internal models → Google Sheets
- Validate data integrity and completeness
- Process transactions and track roster changes
- Implement new data processing features
- Optimize data processing performance
- Handle complex business logic (salary caps, keeper costs, FAAB)
- Implement data aggregation and statistics

**When to Use**:
- When adding new data fields or attributes
- For implementing new salary calculation strategies
- When processing complex transaction logic
- To add new data validation rules
- For optimizing data transformation performance
- When implementing analytics features

**Example Tasks**:
- "Add support for tracking player value analysis (salary per fantasy point)"
- "Implement keeper value calculation logic for next season"
- "Create transaction aggregation for weekly summary statistics"
- "Add validation for negative salary scenarios"

**Key Skills**:
- Understanding of fantasy basketball domain logic
- Proficiency with Python dataclasses and type hints
- Data validation and error handling
- Complex data transformation patterns
- Knowledge of salary cap and auction draft mechanics

---

### 5. Sheet Design Agent (`sheet-design-agent.md`)
**Focus**: Google Sheets formatting, layout, and visual presentation

**Responsibilities**:
- Design and implement sheet layouts
- Apply formatting (colors, fonts, borders, alignment)
- Implement conditional formatting rules
- Create charts and visualizations
- Ensure professional appearance
- Optimize sheet performance and readability
- Handle dynamic ranges and formulas
- Implement new visual features from FUTURE_IDEAS.md
- Design intuitive user interfaces within sheets
- Ensure accessibility and mobile compatibility

**When to Use**:
- When designing new sheet types (e.g., Transaction History)
- For improving visual presentation
- When implementing charts or graphs
- To add conditional formatting rules
- For layout optimization
- When creating new visualization features

**Example Tasks**:
- "Design a Transaction History sheet with sortable columns and color-coded transaction types"
- "Add charts showing salary distribution across teams"
- "Implement conditional formatting for teams approaching salary cap"
- "Redesign team sheets for better readability on mobile devices"

**Key Skills**:
- Google Sheets API formatting expertise
- Understanding of batch update patterns
- Visual design and UX principles
- Color theory and accessibility
- Dynamic range management

---

### 6. Configuration Agent (`configuration-agent.md`)
**Focus**: Configuration management, deployment settings, and environment setup

**Responsibilities**:
- Manage environment variables and .env configuration
- Handle credential management (Yahoo + Google)
- Configure deployment settings for different environments
- Implement feature flags and settings
- Set up automation (cron jobs, scheduled tasks)
- Manage CI/CD pipeline configuration
- Document configuration requirements
- Handle multi-environment deployments
- Implement secrets management
- Configure monitoring and logging

**When to Use**:
- When adding new configuration options
- For deployment to new environments
- When setting up automation/scheduling
- To implement multi-league support
- For configuration validation and error messages
- When setting up CI/CD

**Example Tasks**:
- "Set up GitHub Actions workflow for automated daily updates"
- "Configure environment variables for production deployment on Railway"
- "Implement feature flags for beta features"
- "Set up credential rotation for OAuth tokens"

**Key Skills**:
- Environment configuration best practices
- Credential management and security
- Deployment automation (cron, GitHub Actions, cloud platforms)
- Configuration validation patterns
- Documentation of setup requirements

---

### 7. Documentation Agent (`documentation-agent.md`)
**Focus**: Maintaining comprehensive and up-to-date documentation

**Responsibilities**:
- Update README.md with new features
- Maintain CLAUDE.md developer documentation
- Create and update CHANGELOG entries
- Write inline code documentation (docstrings)
- Create usage examples and tutorials
- Document API changes and breaking changes
- Generate architecture diagrams
- Update FUTURE_IDEAS.md with new enhancement ideas
- Create user guides and troubleshooting docs
- Document deployment procedures

**When to Use**:
- After implementing a new feature
- When refactoring code
- For documenting complex logic
- To create user guides
- When updating development workflows
- After architectural changes

**Example Tasks**:
- "Update README with instructions for the new transaction history feature"
- "Add docstrings to all functions in the new keeper_analyzer.py module"
- "Create a troubleshooting guide for common API authentication issues"
- "Document the architecture of the new notification system"

**Key Skills**:
- Technical writing and clarity
- Markdown formatting
- Code documentation standards (Google style docstrings)
- Architecture documentation
- User-facing vs developer-facing documentation

---

## Agent Usage Patterns

### Single Agent Workflows
```bash
# Example: Use Researcher Agent before implementation
"Researcher Agent, compare approaches for implementing scheduled daily updates"

# Example: Use Testing Agent to verify a new feature
"Testing Agent, create comprehensive tests for the transaction history feature"

# Example: Use Integration Agent for API work
"Integration Agent, optimize the Yahoo API transaction fetching to reduce rate limiting"
```

### Multi-Agent Sequential Workflows
```bash
# Example: Implement a new feature with multiple agents
1. Researcher Agent: "Compare approaches for adding a transaction history sheet"
2. Data Pipeline Agent: "Add TransactionHistory data model based on chosen approach"
3. Integration Agent: "Implement transaction data fetching from Yahoo API"
4. Sheet Design Agent: "Design and implement transaction history sheet layout"
5. Testing Agent: "Create comprehensive tests for transaction history feature"
6. Documentation Agent: "Document the new transaction history feature"
```

### Parallel Agent Workflows
```bash
# Example: Multiple agents working on different aspects simultaneously
- Integration Agent: "Enhance error handling for Yahoo API calls"
- Testing Agent: "Improve test coverage for sheet_generator.py"
- Documentation Agent: "Update outdated docstrings in data_models.py"
```

### Research-Driven Workflows
```bash
# Example: Using Researcher Agent to guide implementation
1. Researcher Agent: "Research and compare 3 approaches for adding player value analysis"
2. [Review research results and choose approach]
3. Data Pipeline Agent: "Implement player value analysis using the chosen approach"
4. Sheet Design Agent: "Create visual presentation for player value metrics"
5. Testing Agent: "Add tests for value analysis calculations"
```

---

## Agent Coordination

For complex features that span multiple domains:

1. **Start with Research**: Use Researcher Agent to explore options
2. **Make Decisions**: Review research and choose approach
3. **Identify Agents**: Which agents are needed for implementation?
4. **Define Sequence**: What order should agents work in?
5. **Coordinate Handoffs**: Ensure each agent has context from previous agents
6. **Test & Document**: Testing Agent verifies, Documentation Agent records
7. **Final Review**: Have multiple agents review the complete solution

### Example: Implementing "Scheduled Daily Updates" (from FUTURE_IDEAS.md)

**Phase 1: Research**
- Researcher Agent: "Compare cron jobs, GitHub Actions, AWS Lambda, and Google Cloud Run for scheduled updates. Consider cost, complexity, maintenance, and OAuth token handling."

**Phase 2: Implementation** (based on chosen approach)
- Configuration Agent: "Set up GitHub Actions workflow with secrets management"
- Integration Agent: "Ensure OAuth token refresh works in headless CI environment"
- Testing Agent: "Create tests for scheduled execution and error handling"

**Phase 3: Documentation**
- Documentation Agent: "Document setup, configuration, and troubleshooting for scheduled updates"

---

## Creating New Agents

To create a new specialized agent:

1. **Identify the Domain**: What specific area of the codebase does it focus on?
2. **Define Responsibilities**: What tasks should it handle?
3. **Specify Expertise**: What knowledge and skills does it need?
4. **Create Agent File**: Add `<agent-name>-agent.md` in this directory
5. **Document Usage**: Add examples of when and how to use it
6. **Update This README**: Add the agent to the list above

---

## Agent File Structure Template

Each agent file should contain:

```markdown
# [Agent Name] Agent

## Overview
Brief description of the agent's purpose and focus area

## Core Responsibilities
Detailed list of what this agent handles

## Key Files
List of files this agent primarily works with

## Common Tasks
Examples of typical tasks this agent performs

## Knowledge Base
Specific knowledge this agent needs about:
- Codebase structure
- Domain concepts
- Best practices
- Common patterns
- Related technologies

## Interaction with Other Agents
Which other agents this agent commonly works with and how

## Examples
Concrete examples of agent usage with expected outputs

## Best Practices
Guidelines for getting the best results from this agent
```

---

## Best Practices

1. **Use the Right Agent**: Choose the agent that best matches your task domain
2. **Start with Research**: For major features, begin with Researcher Agent
3. **Clear Instructions**: Provide specific, detailed instructions with context
4. **Provide Context**: Give agents relevant background about goals and constraints
5. **Combine Agents**: For complex features, orchestrate multiple agents
6. **Review Output**: Always review agent work for quality and correctness
7. **Iterate**: Agents can refine their work based on feedback
8. **Document Decisions**: Use Documentation Agent to capture important decisions

---

## Agent Benefits

### Development Efficiency
- **Specialized Focus**: Each agent deeply understands its domain
- **Parallel Work**: Multiple agents can work on different aspects simultaneously
- **Consistent Patterns**: Agents follow established codebase patterns
- **Reduced Context Switching**: Focus on one domain at a time

### Code Quality
- **Expert-Level Work**: Agents apply domain-specific best practices
- **Thorough Testing**: Testing Agent ensures comprehensive coverage
- **Better Documentation**: Documentation Agent maintains consistency
- **Informed Decisions**: Researcher Agent provides analysis before implementation

### Maintainability
- **Clear Ownership**: Each agent owns specific modules/concerns
- **Consistent Updates**: Agents maintain consistency across related files
- **Knowledge Preservation**: Agent knowledge base captures domain expertise
- **Easier Onboarding**: New developers can use agents to understand domains

---

## Quick Reference

| Task Type | Primary Agent | Supporting Agents |
|-----------|---------------|-------------------|
| Planning new feature | Researcher Agent | Documentation Agent |
| API integration | Integration Agent | Testing Agent |
| Data modeling | Data Pipeline Agent | Testing Agent |
| UI/Visual design | Sheet Design Agent | Documentation Agent |
| Writing tests | Testing Agent | Integration Agent, Data Pipeline Agent |
| Deployment setup | Configuration Agent | Documentation Agent |
| Bug investigation | Integration/Data Pipeline Agent | Testing Agent |
| Performance optimization | Researcher Agent | Integration/Data Pipeline Agent |
| Documentation updates | Documentation Agent | All relevant domain agents |

---

Last Updated: November 18, 2025
