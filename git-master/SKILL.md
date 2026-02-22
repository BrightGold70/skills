---
name: git-master
description: Expert git operations including commits, branches, merging, rebasing, history analysis, and troubleshooting. Use for any git operations, history search, or resolving merge conflicts.
---

# Git Master

Expert git operations for version control workflows.

## When to Use This Skill

- Creating commits with proper messages
- Managing branches (create, delete, rename)
- Merging and rebasing branches
- Analyzing git history
- Resolving merge conflicts
- Finding when/why code was changed
- Undoing changes

## Common Operations

### Commits

```bash
# Stage and commit with message
git add -A && git commit -m "description"

# Amend last commit
git commit --amend

# Interactive rebase for cleaning up commits
git rebase -i HEAD~n
```

### Branches

```bash
# Create and switch to new branch
git checkout -b branch-name

# Delete local branch
git branch -d branch-name

# Delete remote branch
git push origin --delete branch-name

# List merged branches
git branch --merged
```

### History

```bash
# Search commit messages
git log --oneline --grep="keyword"

# Find when file was changed
git log -p --follow filename

# Who changed this line
git blame filename

# Find commit that introduced bug
git bisect start
```

### Merging & Rebasing

```bash
# Merge branch
git merge branch-name

# Rebase onto main
git rebase main

# Abort rebase
git rebase --abort

# Continue after resolving conflicts
git rebase --continue
```

### Undoing Changes

```bash
# Discard unstaged changes
git checkout -- filename

# Unstage files
git reset HEAD filename

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Revert a commit
git revert commit-sha
```

## Best Practices

1. **Commits**: Use conventional commits format
2. **Branches**: Keep main/master clean, use feature branches
3. **Review**: Check diff before committing
4. **Test**: Ensure tests pass before pushing

## Conflict Resolution

1. Identify conflicting files: `git status`
2. Open and edit each file
3. Look for `<<<<<<<`, `=======`, `>>>>>>>`
4. Choose/merge changes
5. `git add` resolved files
6. `git commit`
