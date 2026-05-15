---
name: financial-doc-architect
description: Automates the creation and updating of Confluence pages for trading strategies, deployment guides, and meeting notes. Use this to sync codebase documentation with Confluence.
---

# Financial Doc Architect

This skill ensures your Confluence documentation is always in sync with your code.

## Core Capabilities
1. **Strategy Docs**: Convert agent logic (prompts, schemas, strategies) into formatted Confluence pages.
2. **Deployment Guides**: Keep Docker and setup instructions updated on Confluence.
3. **Automated Reports**: Summarize backtest results and post them to the **PM** space.

## Usage Guide

### 1. Documenting an Agent
To document a specific agent (e.g., `trader`):
- Read the agent's Python file and its schema in `tradingagents/agents/schemas.py`.
- Call `createConfluencePage` in space **PM**.
- Use the **markdown** format for the body.

### 2. Updating Onboarding Docs
When `README.md` or `Dockerfile` changes:
- Read the local file.
- Find the corresponding page on Confluence using `searchConfluenceUsingCql`.
- Update the page with the latest instructions.

### 3. Syncing PRDs (Product Requirement Documents)
When code logic deviates or expands from the original PRD:
- Find the original PRD on Confluence via Jira ticket links.
- Use `updateConfluencePage` to append an "Implementation Notes" or "Technical Deviations" section.
- Ensure the Confluence page remains the Single Source of Truth by aligning code and doc.

### 3. Confluence Defaults
- **Space ID**: `131170` (Space Key: `PM`)
- **Cloud ID**: `aaa663cb-b14e-484f-9588-a74bcf4c218c`

## Examples

**Example 1: Documenting a new agent**
Input: "Document the new Sentiment Analyst agent on Confluence"
Steps:
1. Read `tradingagents/agents/analysts/sentiment_analyst.py`.
2. Generate a structured page title "Agent: Sentiment Analyst".
3. Create the page in the PM space with sections for "Purpose", "Input Schema", and "Strategy".
