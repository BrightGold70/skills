---
name: file-organizer
description: Intelligently organizes files and folders by understanding context, finding duplicates, suggesting better structures, and automating cleanup tasks.
---

# File Organizer

This skill helps maintain a clean, logical file structure without manual effort.

## When to Use This Skill

- Downloads folder is a chaotic mess
- Can't find files because they're scattered
- Have duplicate files taking up space
- Folder structure doesn't make sense
- Starting a new project and need a good structure
- Cleaning up before archiving old projects

## What This Skill Does

1. **Analyzes Current Structure**: Reviews folders and files to understand what exists
2. **Finds Duplicates**: Identifies duplicate files (by content hash or name)
3. **Suggests Organization**: Proposes logical folder structures based on content
4. **Automates Cleanup**: Moves, renames, and organizes files with user approval
5. **Maintains Context**: Makes smart decisions based on file types, dates, and content
6. **Reduces Clutter**: Identifies old files not touched in 6+ months

## How to Use

### Common Requests

```
Help me organize my Downloads folder
Find duplicate files in my Documents folder
Review my project directories and suggest improvements
Organize these downloads into proper folders
Find duplicate files and help me decide which to keep
Clean up old files I haven't touched in 6+ months
Create a better folder structure for my work/projects
```

## Instructions

1. **Understand the Scope**
   - Which directory needs organization?
   - What's the main problem? (Can't find things, duplicates, too messy)
   - Any files or folders to avoid?
   - How aggressively to organize? (Conservative vs. comprehensive)

2. **Analyze Before Acting**
   - List files and understand the content
   - Identify patterns and categories
   - Find duplicates using hash comparison

3. **Propose Before Doing**
   - Show proposed organization structure
   - Get explicit approval before moving files
   - Provide rollback option

4. **Execute Safely**
   - Move files in batches
   - Keep a log of changes for undo capability
   - Verify after each batch

## Safety Guidelines

- Always ask before deleting files
- Never delete system files
- Ask about sensitive data (passwords, credentials)
- Offer undo/rollback capability
- Consider archive instead of delete for old files
