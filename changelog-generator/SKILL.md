---
name: changelog-generator
description: Automatically creates user-facing changelogs from git commits by analyzing commit history, categorizing changes, and transforming technical commits into clear, customer-friendly release notes.
---

# Changelog Generator

This skill transforms technical git commits into polished, user-friendly changelogs.

## When to Use This Skill

- Preparing release notes for a new version
- Creating weekly or monthly product update summaries
- Documenting changes for customers
- Writing changelog entries for app store submissions
- Generating update notifications
- Creating internal release documentation

## Workflow

1. **Scan Git History**: Analyze commits from a specific time period or between versions
2. **Categorize Changes**: Group commits into logical categories:
   - Features (✨)
   - Improvements/Bug Fixes (🔧)
   - Breaking Changes (⚠️)
   - Security (🔒)
3. **Translate Technical → User-Friendly**: Convert developer commits into customer language
4. **Format Professionally**: Create clean, structured changelog entries
5. **Filter Noise**: Exclude internal commits (refactoring, tests, etc.)

## How to Use

### Basic Usage

```
Create a changelog from commits since last release
Generate changelog for all commits from the past week
Create release notes for version 2.5.0
```

### With Specific Date Range

```
Create a changelog for all commits between March 1 and March 15
```

## Example Output Format

```markdown
# Updates - Week of March 10, 2024

## ✨ New Features

- **Team Workspaces**: Create separate workspaces for different projects

## 🔧 Improvements

- **Faster Sync**: Files now sync 2x faster across devices
- **Better Search**: Search now includes file contents, not just titles
```

## Best Practices

- Use conventional commits format when possible
- Filter out refactoring and test-only commits
- Group by category for readability
- Keep descriptions concise but informative
- Include actionable language for users
