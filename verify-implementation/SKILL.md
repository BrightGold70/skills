---
name: verify-implementation
description: Runs all registered verification skills sequentially to perform unified code quality checks. Use after implementing features, before PRs, or during code reviews. Triggers: "run all verifications", "verify implementation", "check code quality", "run verification suite".
allowed-tools: Glob, Grep, Read, Bash, session_list, session_search
---

# Unified Verification Runner

## Purpose

Discovers and runs all registered verification skills to perform comprehensive code quality checks:
- Runs each verification skill in sequence
- Aggregates results into unified report
- Offers fix recommendations with auto-apply option
- Re-verifies after fixes

## When to Run

- After implementing a new feature
- Before creating a pull request
- During code review
- When auditing codebase quality
- When checking if implementation matches project rules

## Discovery Mechanism

This skill auto-discovers verification skills by scanning for:
- Skills starting with `verify-` prefix in skill directories
- Skills with `verification` or `lint` or `quality` in description

## Workflow

### Step 1: Discover Verification Skills

Scan for available verification skills:

```bash
# Find skills with verify- prefix
glob: .openclaw/skills/verify-*

# Also check for other quality-related skills
grep: "verification\|lint\|quality\|code.?review" in skill descriptions
```

Build a table of discovered skills:

```markdown
## Available Verification Skills

| # | Skill | Description |
|---|-------|-------------|
| 1 | verify-auth | Authentication patterns |
| 2 | verify-api | API endpoint validation |
| 3 | lint-and-validate | General linting |
```

**If no verification skills found:**

```markdown
No verification skills registered.

To add verification skills:
1. Create skill with `verify-` prefix
2. Define verification checks in SKILL.md
3. Register in CLAUDE.md
```

### Step 2: Run Each Verification Skill

For each discovered skill:

1. Read the skill's SKILL.md
2. Execute the verification workflow defined in the skill
3. Collect results (pass/fail/issues)

**Output format per skill:**

```markdown
### Running: verify-<name>

[Verification checks running...]

**Results:**
- Checks: 5
- Passed: 4
- Failed: 1
- Issues: 
  - Line 42: Missing error handling
```

### Step 3: Aggregate Results

After all verifications complete:

```markdown
## Verification Report

### Summary

| Skill | Status | Issues |
|-------|--------|--------|
| verify-auth | ✅ PASS | 0 |
| verify-api | ⚠️ 2 issues | 2 |
| lint-and-validate | ✅ PASS | 0 |

**Total: 2 issues found**
```

### Step 4: Offer Fix Options

If issues found, present options:

```markdown
### Issues Found

| # | Skill | File | Issue | Fix |
|---|-------|------|-------|-----|
| 1 | verify-api | src/api.ts:42 | Missing try-catch | Add error handling |
| 2 | verify-api | src/api.ts:55 | Type any used | Add proper type |

---

**Options:**
1. **Auto-fix all** - Apply recommended fixes
2. **Fix individually** - Review each fix before applying
3. **Skip** - Exit without changes
```

### Step 5: Apply Fixes (if requested)

**Auto-fix all:**
```markdown
Applying fixes...

[1/2] Added try-catch to src/api.ts:42
[2/2] Added proper type to src/api.ts:55

Done. 2 fixes applied.
```

**Fix individually:** Present each fix with approval prompt.

### Step 6: Re-verify

After fixes, re-run verification on affected skills:

```markdown
## Re-verification

| Skill | Before | After |
|-------|--------|-------|
| verify-api | 2 issues | ✅ PASS |

All issues resolved!
```

---

## Verification Skill Template

For creating new verification skills:

```yaml
---
name: verify-<domain>
description: Verifies <domain> implementation follows project patterns
---

# Verification: <Domain>

## Checks

### Check 1: <Description>
- Pattern: <grep/regex>
- Pass: <condition>
- Fail: <condition>

### Check 2: <Description>
- Pattern: <grep/regex>
- Pass: <condition>
- Fail: <condition>

## Exceptions

1. <Pattern that is NOT a violation>
2. <Another exception>

## Related Files

- `src/<domain>.ts`
- `tests/<domain>.test.ts`
```

---

## Example Verification Skills

### verify-code-quality
- Type safety checks (no `any`, `@ts-ignore`)
- Error handling presence
- Consistent naming conventions

### verify-security
- No hardcoded secrets
- Proper authentication checks
- Input validation

### verify-performance
- No blocking operations in loops
- Proper memoization
- Efficient data structures

---

## Related Skills

- **code-review-checklist**: General code review guidelines
- **lint-and-validate**: General linting patterns
- **create-verification-skill**: Helper to generate new verify skills
