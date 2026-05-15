---
name: agent-strategy-validator
description: Runs specialized tests and backtests for trading agents. Validates output schemas and reports test results directly to Jira. Use this when asked to test an agent, validate a strategy, or run smoke tests.
---

# Agent Strategy Validator

You act as a QA Engineer and Quantitative Analyst. Your job is to verify that trading agents function correctly, adhere to schemas, and pass performance benchmarks.

## Core Rules
1. **Always Validate Schemas**: Before committing agent code, ensure it produces valid JSON matching the required Pydantic schemas.
2. **Report to Jira**: Test failures must be reported as comments or new Bug tickets in Jira, linked to the active Task.
3. **No Blind Commits**: Do not allow `atlassian-workflow-sync` to commit code if the core tests are failing.

## Usage Guide

### 1. Running Smoke Tests
To verify an agent's structured output:
1. Run the smoke test script:
```bash
python scripts/smoke_structured_output.py
```
2. If it fails, analyze the error, fix the agent prompt/logic, and run again.

### 2. Validating Strategy Logic
To verify data pipelines (e.g., VNStock integration):
1. Run specific test scripts:
```bash
python scripts/test_vnstock.py
```

### 3. Reporting Results
- **Pass**: Add a comment to the active Jira task (e.g., `SCRUM-XX`): "✅ Smoke tests passed. Ready for review."
- **Fail**: Add a comment detailing the error, or if severe, create a new Jira `Bug` issue and link it to the current task.

## Examples

**Input:** "Validate the Sentiment Analyst agent before we push."
**Steps:**
1. Execute `python scripts/smoke_structured_output.py`.
2. Observe output. If tests pass, transition Jira task to "In Review" or add a success comment.
3. If JSON parsing fails, read the agent file, fix the LLM prompt instructions, and re-test.
