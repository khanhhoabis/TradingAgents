---
name: atlassian-workflow-sync
description: Syncs development progress with Jira and GitHub. Automatically detects TODOs in the codebase and proposes Jira issue creation. Helps track project status across Atlassian tools. Use this whenever the user mentions Jira, syncing tasks, or tracking development progress.
---

# Atlassian Workflow Sync

This skill automates the connection between your local development and Jira.

## Core Capabilities
1. **Sync TODOs**: Scan the codebase for `TODO`, `FIXME`, or `BUG` comments and propose creating corresponding Jira issues.
2. **Issue Management**: Link code changes to Jira keys and update status (To Do, In Progress, Done).
3. **Daily Summary**: Generate a summary of git commits and propose a Jira worklog or status update.

## Usage Guide

### 1. Scanning for TODOs
To find and sync TODOs, run the scanner script:
```bash
python .agents/skills/atlassian-workflow-sync/scripts/scan_todos.py .
```
After scanning, review the results and use `createJiraIssue` to track them in project **SCRUM**.

### 2. Updating Jira Status
When you complete a task:
- Find the Jira issue key (e.g., SCRUM-123).
- Use `transitionJiraIssue` to move it to "Done".
- Use `addCommentToJiraIssue` to link the relevant git commit hash.

### 3. Creating Jira Issues
ALWAYS use these defaults unless specified otherwise:
- **Project Key**: `SCRUM`
- **Issue Types**: `Task`, `Bug`, `Feature`
- **Cloud ID**: `aaa663cb-b14e-484f-9588-a74bcf4c218c`

## Examples

**Example 1: Syncing a new TODO**
Input: "Sync any new TODOs to Jira"
Steps:
1. Run `scan_todos.py`.
2. For each new item, call `createJiraIssue`.
3. Inform the user of the new issue keys.

**Example 2: Closing a task**
Input: "I've finished the checkpointer logic, close the Jira task"
Steps:
1. Search for issues using JQL: `project = SCRUM AND summary ~ "checkpointer"`
2. If found (e.g., SCRUM-45), transition to "Done".
3. Add a comment: "Task completed in commit [hash]".
