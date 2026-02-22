---
name: create-verification-skill
description: Generates new verification skills based on code patterns. Use when you need to add quality checks for a new domain. Triggers: "create verify skill", "add verification", "new check skill", "make verification".
allowed-tools: Glob, Grep, Read, Write, Bash
---

# Verification Skill Generator

## Purpose

Scaffold a new verification skill with proper structure and patterns.

## When to Use

- Adding checks for a new code domain
- Creating project-specific validation
- Building reusable verification rules

## Workflow

### Step 1: Gather Context

Ask user for:
1. **Domain** - What to verify (e.g., "auth", "api", "security")
2. **Patterns** - What patterns to check (code examples)
3. **Exceptions** - What should NOT trigger violations

### Step 2: Analyze Code Patterns

Read sample files to understand patterns:

```bash
# Find relevant files
glob: src/**/<domain>*

# Read samples
read: src/<domain>.ts
```

Identify:
- Common patterns (what GOOD looks like)
- Anti-patterns (what BAD looks like)
- Edge cases (what's acceptable)

### Step 3: Generate Skill

Create `.openclaw/skills/verify-<domain>/SKILL.md`:

```yaml
---
name: verify-<domain>
description: Verifies <domain> implementation follows project patterns
---

# Verification: <Domain>

## Purpose

Validates <domain> code quality:
1. Pattern consistency
2. Error handling
3. Type safety

## Checks

### Check 1: <Pattern Name>

**Pattern:** `<regex or code snippet>`

**Pass:** Code matches expected pattern
**Fail:** Code deviates from pattern

### Check 2: <Pattern Name>

**Pattern:** `<regex or code snippet>`

**Pass:** Proper implementation
**Fail:** Missing or incorrect

## Exceptions

1. Test files - `*.test.ts`, `*.spec.ts`
2. Mock implementations
3. Generated code

## Related Files

- `src/<domain>/*.ts`
- `src/<domain>.ts`
```

### Step 4: Validate

Verify the skill:
1. Syntax correct
2. Patterns match actual files
3. Exceptions cover edge cases

---

## Example: verify-auth

```yaml
---
name: verify-auth
description: Verifies authentication implementation follows security patterns
---

# Verification: Authentication

## Checks

### Check 1: Password Hashing

**Pattern:** `bcrypt|argon2|scrypt`

**Pass:** Passwords hashed with secure algorithm
**Fail:** Plaintext or weak hashing

### Check 2: Token Expiration

**Pattern:** `expiresIn|expir.*:\s*\d+`

**Pass:** Tokens have expiration
**Fail:** No expiration set

### Check 3: Auth Middleware

**Pattern:** `middleware|guard|decorator.*auth`

**Pass:** Protected routes use auth
**Fail:** Unprotected sensitive routes

## Exceptions

1. Test fixtures with "test" in path
2. Documentation files
3. Configuration files
```

---

## Output

Generated skill is ready to use:
- Can be run individually: `/verify-<domain>`
- Discovered by `/verify-implementation`
