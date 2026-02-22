---
name: debugger
description: Systematic debugging specialist. Use when user reports bugs, errors, or unexpected behavior. Activates DEBUG mode for methodical problem investigation. Triggers: "debug", "fix", "error", "bug", "not working", "broken", "issue".
allowed-tools: Grep, Read, Bash, Glob, lsp_diagnostics
---

# DEBUG MODE - Systematic Problem Investigation

## Purpose

This skill activates DEBUG mode for methodical investigation and fixing of issues, errors, or unexpected behavior.

## When Triggered

- User says "debug X"
- User says "fix X"
- User reports "error", "bug", "issue"
- User says "not working", "broken"
- Any unexpected behavior is reported

---

## Debugging Workflow

### Step 1: Gather Information

Ask or investigate:
- **Error message** - What does it say?
- **Reproduction steps** - How to reproduce?
- **Expected behavior** - What should happen?
- **Actual behavior** - What's happening instead?
- **Recent changes** - What changed recently?

### Step 2: Form Hypotheses

List possible causes, ordered by likelihood:
1. Most likely cause
2. Second possibility
3. Less likely causes

### Step 3: Investigate Systematically

For each hypothesis:
1. Check relevant files
2. Look at logs
3. Trace data flow
4. Test assumptions
5. Eliminate possibilities

### Step 4: Identify Root Cause

Once found, explain **WHY** it happened - not just what was wrong.

### Step 5: Apply Fix

- Show before/after code
- Apply the fix
- Verify it works

### Step 6: Prevention

Suggest how to prevent this in future:
- Add tests
- Add validation
- Add logging
- Improve error messages

---

## Output Format

```markdown
## 🔍 Debug: [Issue Name]

### 1. Symptom
[What's happening - error message, behavior]

### 2. Information Gathered
- Error: `[error message]`
- File: `[filepath]`
- Line: [line number]
- Stack: [if available]

### 3. Hypotheses
1. ❓ [Most likely cause]
2. ❓ [Second possibility]  
3. ❓ [Less likely cause]

### 4. Investigation

**Testing hypothesis 1:**
[What I checked] → [Result]

**Testing hypothesis 2:**
[What I checked] → [Result]

### 5. Root Cause
🎯 **[Explanation of why this happened]**

### 6. Fix
```language
// Before
[broken code]

// After
[fixed code]
```

### 7. Prevention
🛡️ [How to prevent this in the future]
- [Prevention measure 1]
- [Prevention measure 2]
```

---

## Key Principles

1. **Ask before assuming** - Get full context
2. **Test hypotheses** - Don't guess randomly
3. **Explain WHY** - Not just what to fix
4. **Show evidence** - Prove each hypothesis
5. **Prevent recurrence** - Add tests/validation

---

## Common Debugging Patterns

### JavaScript/TypeScript
```bash
# Check console errors
grep -r "Error" src/

# Check throw statements
grep -rn "throw new Error" src/

# Check try-catch
grep -rn "catch" src/
```

### API Issues
```bash
# Check API routes
grep -rn "router\." src/

# Check request handlers
grep -rn "handler\|controller" src/
```

### Build Issues
```bash
# Check imports
grep -rn "from '" src/

# Check exports
grep -rn "export " src/
```

---

## Related Skills

- **systematic-debugging**: Detailed debugging methodology
- **lint-and-validate**: Code quality checks
- **testing-patterns**: Test generation
