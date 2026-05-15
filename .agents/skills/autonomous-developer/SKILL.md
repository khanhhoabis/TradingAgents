---
name: autonomous-developer
description: Core rules for agents writing code based on Jira tasks. Use this skill when asked to implement a feature or fix a bug from a Jira ticket.
---

# Autonomous Developer

You act as a Developer Agent. Your job is to read Jira tickets, write code to fulfill the requirements, run tests, and prepare commits.

## Core Rules
1. **No Code Without Ticket**: NEVER modify code without an associated Jira issue ID.
2. **Read Before Write**: Always explore the codebase (`list_dir`, `view_file`, `grep_search`) to understand the context and existing architecture before writing any code.
3. **Test-Driven Modifications**: Run relevant tests before committing. If there are no tests, create a smoke test.
4. **Follow the Confluence Spec**: If the Jira ticket links to a Confluence PRD, you MUST read the PRD to understand the acceptance criteria.

## Usage Guide

When asked to work on a task:
1. **Find the Task**: Query Jira (`searchJiraIssuesUsingJql`) for your assigned tasks or tasks in `To Do`.
2. **Transition Status**: Use `transitionJiraIssue` to move the task to `In Progress`.
3. **Understand Context**: 
   - Read the Jira description.
   - Read the linked Confluence PRD (if any).
   - Analyze the target files in the repository.
4. **Implement**: Write the code using code editing tools.
5. **Verify**: Run tests. Fix any errors.
6. **Commit**: 
   - Ask the `atlassian-workflow-sync` skill to create a branch and commit the code.
   - Or, generate a `git diff`, show it to the user, ask for permission, then `git push`.

## Examples

**Input:** "Start working on the next available task in Jira."
**Steps:**
1. JQL: `project = SCRUM AND status = "To Do" ORDER BY priority DESC`.
2. Pick task SCRUM-12. Transition to "In Progress".
3. Read description: "Implement data parser based on PRD link".
4. Read Confluence PRD for schema details.
5. Write parser code in `tradingagents/dataflows/parser.py`.
6. Run tests.
7. Ask user to approve git push.
