---
name: github-automation
description: Automate GitHub repositories, issues, pull requests, branches, CI/CD via GitHub CLI (gh). Manage code workflows, review PRs, search code, and handle deployments programmatically.
requires:
  tool: gh
---

# GitHub Automation via GitHub CLI

Automate GitHub repository management, issue tracking, pull request workflows, branch operations, and CI/CD through GitHub CLI (`gh`).

## Prerequisites

- GitHub CLI (`gh`) must be installed
- Run `gh auth status` to verify authentication
- Already authenticated as BrightGold70

## Setup

Check authentication:
```bash
gh auth status
```

## Core Workflows

### 1. List Repositories

```bash
gh repo list [owner] --limit N
gh repo view [owner/repo]
```

### 2. Manage Issues

```bash
# List issues
gh issue list [owner/repo] --state all|open|closed

# Create issue
gh issue create --title "Issue title" --body "Description" --label bug

# View issue
gh issue view N

# Close/reopen issue
gh issue close N
gh issue reopen N

# Add comment
gh issue comment N --body "Comment"
```

### 3. Manage Pull Requests

```bash
# List PRs
gh pr list --state all|open|closed

# View PR
gh pr view N
gh pr view --web  # Open in browser

# Create PR
gh pr create --title "PR title" --body "Description" --base main --head branch

# Checkout PR
gh pr checkout N

# Merge PR (requires confirmation)
gh pr merge N --admin --squash

# Review PR
gh pr review N --approve --body "LGTM"
```

### 4. Manage Branches

```bash
# List branches
gh repo view [owner/repo] --json branches

# Create branch
git checkout -b new-branch
git push -u origin new-branch

# Delete branch (local)
git branch -d branch

# Delete branch (remote)
gh repo delete-branch --branch branch
```

### 5. Manage CI/CD

```bash
# List workflows
gh workflow list

# View workflow runs
gh run list
gh run view N

# Trigger workflow
gh workflow run workflow.yml --ref branch

# Download artifacts
gh run download N --dir ./downloads
```

### 6. Search

```bash
# Search code
gh search code "query" --owner owner

# Search repos
gh search repos "query"

# Search issues
gh search issues "query"
```

### 7. Gists

```bash
# List gists
gh gist list

# Create gist
gh gist create file.txt --description "Description"

# View gist
gh gist view ID
```

## Quick Reference

| Task | Command |
|------|---------|
| List repos | `gh repo list` |
| Clone repo | `gh repo clone owner/repo` |
| View repo | `gh repo view [owner/repo]` |
| Create issue | `gh issue create --title "..."` |
| List issues | `gh issue list` |
| View issue | `gh issue view N` |
| Create PR | `gh pr create --title "..."` |
| List PRs | `gh pr list` |
| Merge PR | `gh pr merge N --squash` |
| Checkout PR | `gh pr checkout N` |
| List runs | `gh run list` |
| Trigger workflow | `gh workflow run workflow.yml` |
| Search code | `gh search code "query"` |

## Tips

- Use `--json` flag for machine-readable output
- Use `--web` to open in browser
- Use `-F` flag for file input (e.g., `--body-file`)
- Use `--limit` for pagination
