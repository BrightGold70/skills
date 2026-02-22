---
name: pdca-workflow
description: |
  PDCA (Plan-Do-Check-Act) workflow methodology for structured project development.
  Provides comprehensive project management through the Plan → Design → Do → Check → Act cycle.
  
  Use when: user wants structured development workflow, planning, gap analysis, or iteration.
  Triggers: pdca, plan, design, analyze, iterate, report, status, gap, workflow, phases.
---

# PDCA Workflow Skill

> Structured project development methodology adapted for OpenCode

## Core Principle

PDCA (Plan-Do-Check-Act) is a continuous improvement cycle:

```
    ┌─────────┐
    │  PLAN   │ ← Define what to build and why
    └────┬────┘
         ↓
    ┌─────────┐
    │ DESIGN  │ ← Create detailed specification
    └────┬────┘
         ↓
    ┌─────────┐
    │   DO    │ ← Implement the feature
    └────┬────┘
         ↓
    ┌─────────┐
    │  CHECK  │ ← Verify implementation matches design
    └────┬────┘
         ↓
    ┌─────────┐
    │   ACT   │ ← Fix gaps, iterate, or complete
    └─────────┘
```

## When to Use

| Scenario | Recommended PDCA Phase |
|----------|----------------------|
| Starting new feature | Plan → Design |
| Unclear requirements | Plan (with clarification) |
| Implementation phase | Do |
| After implementation | Check (Gap Analysis) |
| Fixing issues | Act (iterate) |
| Feature complete | Report |

## Phase Details

### Phase 1: PLAN

**Purpose:** Define what to build and why

**Key Questions:**
- What problem does this solve?
- Who is the target user?
- What are the success criteria?
- What is the core contribution?

**Deliverable:** `docs/01-plan/{feature}.plan.md`

**Template:**
```markdown
# Plan: {Feature Name}

## Problem Statement
[What problem does this solve?]

## Target Users
[Who will use this?]

## Core Contribution
[What is the one sentence that describes the value?]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Key Requirements
1. Requirement 1
2. Requirement 2

## Timeline Estimate
[Optional: expected duration]
```

### Phase 2: DESIGN

**Purpose:** Create detailed specification

**Key Questions:**
- How will it work?
- What are the components?
- What is the data model?
- What are the APIs?

**Deliverable:** `docs/02-design/{feature}.design.md`

**Template:**
```markdown
# Design: {Feature Name}

## Architecture Overview
[High-level architecture]

## Components
| Component | Responsibility |
|-----------|---------------|
| Component1 | Does X |
| Component2 | Does Y |

## Data Model
[Database/schema design]

## API Design
[Endpoint definitions]

## User Flow
[How users interact with the feature]
```

### Phase 3: DO

**Purpose:** Implement the feature

**Key Actions:**
- Create necessary files
- Implement components
- Write tests
- Document code

**Implementation Order:**
1. [First file/component]
2. [Second file/component]
3. ...

**Verification:** Code compiles, tests pass

### Phase 4: CHECK

**Purpose:** Verify implementation matches design

**Gap Analysis Questions:**
- Does the implementation match the design document?
- Are all requirements fulfilled?
- Are there any deviations?

**Match Rate Calculation:**
```
Match Rate = (Matched Items / Total Design Items) × 100
```

**Output:** `docs/03-analysis/{feature}.analysis.md`

### Phase 5: ACT

**Purpose:** Fix gaps and iterate

**Actions:**
- Fix identified gaps
- Re-verify after fixes
- Complete or iterate

**Iteration Rules:**
- Maximum 5 iterations
- Stop when Match Rate >= 90%

## Usage Commands

### Plan a New Feature
```
Create a plan document for [feature name]
```

### Create Design
```
Create a design document for [feature name]
```

### Start Implementation
```
Start implementing [feature name]
```

### Run Gap Analysis
```
Analyze gaps between design and implementation for [feature]
```

### Fix Issues
```
Fix the gaps identified in [feature] analysis
```

### Generate Report
```
Generate completion report for [feature]
```

### Check Status
```
Show PDCA status
```

### Next Steps
```
What should I do next for [feature]?
```

## Gap Analysis Template

When running Check phase, evaluate:

| Design Item | Implementation Status | Gap |
|------------|---------------------|-----|
| Component A | Implemented | None |
| Component B | Partial | Missing X |
| API endpoint | Implemented | None |

**Gap Categories:**
- **Critical**: Missing core functionality
- **Major**: Important feature not complete
- **Minor**: Cosmetic/enhancement issues

## Best Practices

1. **Always Plan First**: Never start implementation without a plan
2. **Design Before Do**: Complete design before writing code
3. **Check Before Act**: Always verify gaps before fixing
4. **Document Everything**: Keep all PDCA documents for reference
5. **Iterate Small**: Make small, incremental improvements
6. **Know When to Stop**: 90% match rate is good enough for most features

## OpenCode Integration

This PDCA workflow integrates with OpenCode's:

- **Task System**: Track progress with todo items
- **LSP Diagnostics**: Verify code quality
- **Build Commands**: Verify implementation
- **Document Creation**: Generate plan/design documents

## Related Skills

- **code-review**: For detailed code quality analysis
- **testing-patterns**: For test-driven development
- **deployment-procedures**: For Phase 9 (Deployment)
- **architecture**: For technical decision making

---

*Adapted from bkit PDCA methodology for OpenCode*
