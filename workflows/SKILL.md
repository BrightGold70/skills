---
name: workflows
description: Collection of workflow commands for common tasks. Use these patterns to invoke specific workflows. Triggers: any request matching workflow patterns below.
allowed-tools: Glob, Grep, Read, Write, Bash, task
---

# Workflow Commands

This skill provides patterns for common development workflows. Invoke these patterns based on user requests.

---

## Available Workflows

| Command | Description | Pattern Match |
|---------|-------------|--------------|
| `/plan` | Create project plan | "plan", "breakdown", "tasks" |
| `/create` | Create new feature/app | "create", "build", "implement" |
| `/debug` | Systematic debugging | "debug", "fix", "error", "bug", "issue" |
| `/enhance` | Improve existing code | "enhance", "improve", "optimize", "refactor" |
| `/test` | Generate/run tests | "test", "spec", "verify" |
| `/deploy` | Deploy application | "deploy", "release", "ship" |
| `/brainstorm` | Explore options | "brainstorm", "options", "approach" |
| `/preview` | Preview changes | "preview", "preview locally" |
| `/status` | Check project status | "status", "health", "state" |
| `/orchestrate` | Multi-agent coordination | "orchestrate", "coordinate", "multiple" |
| `/ui-ux` | Design UI/UX | "design", "UI", "UX", "interface" |

---

## /plan - Project Planning

**Pattern**: "plan", "breakdown", "task list", "how to"

**Behavior**:
1. Ask clarifying questions (Socratic gate)
2. Analyze requirements
3. Create task breakdown
4. Output to `docs/PLAN-{slug}.md`

**Example**: `/plan e-commerce cart`

---

## /create - Create New Feature

**Pattern**: "create", "build", "implement", "new feature"

**Behavior**:
1. Read project context
2. Generate code following project patterns
3. Verify implementation
4. Report results

**Example**: `/create login page`

---

## /debug - Systematic Debugging

**Pattern**: "debug", "fix", "error", "bug", "issue", "broken", "not working"

**Behavior**:
1. Gather error information
2. Form hypotheses
3. Investigate systematically
4. Apply fix with explanation
5. Add prevention measures

**Output Format**:
```markdown
## 🔍 Debug: [Issue]

### Symptom
[What's happening]

### Investigation
[Hypothesis testing]

### Root Cause
[Why it happened]

### Fix
[Code before/after]

### Prevention
[How to prevent]
```

**Example**: `/debug login not working`

---

## /enhance - Improve Code

**Pattern**: "enhance", "improve", "optimize", "refactor"

**Behavior**:
1. Analyze current implementation
2. Identify improvement areas
3. Apply changes
4. Verify no regressions

**Example**: `/enhance API performance`

---

## /test - Testing

**Pattern**: "test", "spec", "verify", "coverage"

**Behavior**:
1. Identify code to test
2. Generate test cases
3. Run tests
4. Report coverage

**Example**: `/test authentication`

---

## /deploy - Deployment

**Pattern**: "deploy", "release", "ship", "publish"

**Behavior**:
1. Check deployment readiness
2. Run build
3. Execute deployment
4. Verify deployment

**Example**: `/deploy to production`

---

## /brainstorm - Exploration

**Pattern**: "brainstorm", "options", "approach", "how to", "what's the best"

**Behavior**:
1. Explore multiple approaches
2. List pros/cons
3. Recommend options
4. Let user decide

**Example**: `/brainstorm auth options`

---

## /preview - Local Preview

**Pattern**: "preview", "run locally", "see changes"

**Behavior**:
1. Start dev server
2. Open browser
3. Show changes
4. Report URL

**Example**: `/preview landing page`

---

## /status - Project Status

**Pattern**: "status", "health", "state", "how's it going"

**Behavior**:
1. Check git status
2. Check build status
3. Check test status
4. Report overall health

**Example**: `/status`

---

## /orchestrate - Multi-Agent

**Pattern**: "orchestrate", "coordinate", "multiple agents", "parallel"

**Behavior**:
1. Break task into subtasks
2. Identify required expertise
3. Coordinate parallel execution
4. Synthesize results

**Example**: `/orchestrate full stack feature`

---

## /ui-ux - Design

**Pattern**: "design", "UI", "UX", "interface", "mockup"

**Behavior**:
1. Gather design requirements
2. Create component specs
3. Generate code
4. Apply styling

**Example**: `/ui-ux dashboard`

---

## Usage Notes

These are **workflow patterns**, not hard triggers. Match user intent and apply the appropriate workflow.

**Best Practices**:
- Ask clarifying questions before complex tasks
- Report progress as you go
- Verify results before completing
- Explain your reasoning
