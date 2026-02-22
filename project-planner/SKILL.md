---
name: project-planner
description: Project planning specialist. Use when user wants to plan a feature, break down tasks, or create a roadmap. Triggers: "plan", "breakdown", "roadmap", "task list", "how to approach".
allowed-tools: Read, Write, Glob, Grep
---

# PROJECT PLANNER MODE

## Purpose

Analyzes requirements, breaks down complex tasks, and creates structured plans with task breakdowns and agent assignments.

## When Triggered

- User says "plan X"
- User asks "how to approach X"
- User wants "task breakdown"
- User asks for "roadmap"

---

## Planning Workflow

### Phase -1: Context Check

Before planning, verify you understand the project:

1. **Check project structure**
   - What framework/tech stack?
   - What's the codebase structure?
   - Any existing patterns?

2. **Check constraints**
   - Deadline?
   - Budget/scope limits?
   - Dependencies?

### Phase 0: Socratic Gate

Ask clarifying questions before planning:

1. **Scope** - What's in scope? What's out?
2. **Priority** - What's most important?
3. **Constraints** - Any limitations?
4. **Success** - How will we know it's done?

### Phase 1: Requirements Analysis

Break down the request:

1. **Core functionality** - What must it do?
2. **User interactions** - How does user interact?
3. **Data requirements** - What needs to be stored?
4. **Integration points** - What does it connect to?
5. **Edge cases** - What could go wrong?

### Phase 2: Task Breakdown

Create hierarchical task list:

```
Level 1: Epic
  Level 2: Feature
    Level 3: Story
      Level 4: Task
```

### Phase 3: Technical Design

For each major task:
1. **Files affected**
2. **Dependencies**
3. **Approach** - How to implement
4. **Risks** - What could go wrong

### Phase 4: Agent Assignment

Assign tasks to expertise areas:
- Frontend tasks → frontend skill
- Backend tasks → backend skill
- Database tasks → database skill
- Security tasks → security skill

### Phase 5: Verification Checklist

Define how to verify each task:
- Tests to run
- Manual checks
- Acceptance criteria

---

## Output Format

```markdown
# Plan: [Project/Feature Name]

## Overview
[Brief description of what we're building]

## Scope
### In Scope
- [Item 1]
- [Item 2]

### Out of Scope
- [Item 1]
- [Item 2]

## Task Breakdown

### Phase 1: [Phase Name]
| Task | Description | Expertise | Files |
|------|-------------|-----------|-------|
| 1.1 | [Task] | [Frontend] | src/components/* |

### Phase 2: [Phase Name]
[...]

## Technical Notes
- [Note 1]
- [Note 2]

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk] | [High] | [Mitigation] |

## Verification Checklist
- [ ] [Check 1]
- [ ] [Check 2]
```

---

## Plan Naming Convention

When saving plans:
```
docs/PLAN-{slug}.md

Examples:
- PLAN-ecommerce-cart.md
- PLAN-user-auth.md  
- PLAN-api-migration.md
```

---

## Key Principles

1. **Ask before assuming** - Clarify requirements
2. **Break it down** - Hierarchical tasks
3. **Think dependencies** - What must happen first?
4. **Define done** - How to verify completion
5. **Be realistic** - Account for complexity

---

## Related Skills

- **plan-writing**: Structured task planning
- **brainstorming**: Explore options
- **orchestrator**: Coordinate execution
