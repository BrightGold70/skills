# Inline Protocols — H-MAD Phases 1–7

Standalone replacements for all external skill calls. No spec-kit, b-mad, or pdca required.

---

## Phase 1 — Brainstorm

**Goal**: Establish shared understanding of the problem before writing any spec.

**Steps**:

1. Ask 3–5 clarifying questions about the feature. Focus on:
   - What's the user pain or system gap being addressed?
   - What failure mode are we preventing?
   - What constraints exist (performance, compatibility, scope)?
   - What's explicitly out of scope?
   - Any prior attempts that failed?

2. Based on user answers, draft the brainstorm doc:

   ```markdown
   # Brainstorm: <feature>

   ## Problem Statement
   <1-2 sentences: what's broken or missing and for whom>

   ## Proposed Approach
   <The primary solution approach — why this over alternatives>

   ## Alternatives Considered
   - **<Alt A>**: <what it is> — rejected because <reason>
   - **<Alt B>**: <what it is> — rejected because <reason>

   ## Risks & Mitigations
   | Risk | Likelihood | Mitigation |
   |---|---|---|
   | <risk> | H/M/L | <mitigation> |

   ## Dependencies
   <External systems, teams, or other features this depends on. "None" if standalone.>

   ## Open Questions
   - <question that needs resolution before or during spec>
   ```

3. Save to `docs/01-plan/features/<feature>-brainstorm.md`.
4. Show summary. Ask: "Anything to add or change before I write the spec?"

**Advance gate**: User explicitly approves or provides corrections (apply + re-confirm).

---

## Phase 2 — Specify

**Goal**: Turn the approved brainstorm into a precise, testable specification.

**Steps**:

1. Read `docs/01-plan/features/<feature>-brainstorm.md`.
2. Draft the spec. Every FR must have at least one testable AC:

   ```markdown
   # Spec: <feature>

   ## Goal
   <One sentence: what this feature achieves for the user or system>

   ## Functional Requirements

   ### FR-1: <requirement name>
   - **Description**: <what the system must do>
   - **Acceptance Criteria**:
     - AC-1.1: <specific, observable, testable condition>
     - AC-1.2: <specific, observable, testable condition>

   ### FR-2: <requirement name>
   - **Description**: ...
   - **Acceptance Criteria**: ...

   ## Non-Functional Requirements
   - Performance: <if applicable; "N/A" otherwise>
   - Security: <if applicable; "N/A" otherwise>
   - Compatibility: <if applicable; "N/A" otherwise>

   ## Out-of-Scope
   - <explicit exclusion — prevents scope creep during audit cycles>

   ## Assumptions
   - <things assumed true for this spec to hold>
   ```

3. Save to `docs/01-plan/features/<feature>.spec.md`.
4. Show. Ask: "Does this capture what you need? Approve to move to planning."

**Advance gate**: User explicitly approves. No vague ACs ("works correctly" is not an AC).

---

## Phase 3 — Plan

**Goal**: Derive an implementation-agnostic plan from the approved spec.

**Steps**:

1. Read `docs/01-plan/features/<feature>.spec.md`.
2. Draft the plan — focus on WHAT and WHY, not HOW (that's Phase 4):

   ```markdown
   # Plan: <feature>

   ## Overview
   <2-3 sentences: what we're building and why it matters now>

   ## Goals
   - <goal 1 — maps to FR-N in spec>
   - <goal 2 — maps to FR-N in spec>

   ## Implementation Strategy
   <Which layers change, what patterns we'll follow, what we deliberately won't touch>

   ## Deliverables
   | Deliverable | Type | Satisfies |
   |---|---|---|
   | <name> | module / API / schema / CLI flag / UI | FR-N |

   ## Risks
   | Risk | Impact | Mitigation |
   |---|---|---|

   ## Success Criteria
   - All ACs in spec pass automated tests
   - <any additional measurable criteria>

   ## Out-of-Scope (confirmed from spec)
   - <carry over the spec's out-of-scope list>
   ```

3. Save to `docs/01-plan/features/<feature>.plan.md`.
4. Prompt: "Plan v1.0 ready. Review and approve, then I'll run the audit cycle."

**Advance gate**: User explicitly marks v1.0 approved. Then audit cycle begins (see SKILL.md §Audit prompt assembly).

---

## Phase 4 — Design

**Goal**: Translate the audited plan into a concrete technical design.

**Steps**:

1. Read audited plan (`docs/01-plan/features/<feature>.plan.md` + latest `.plan.audit.vN.md`).
2. Read `.h-mad/invariants.md` — every design decision must comply with Axis B before the audit catches it.
3. Draft the design:

   ```markdown
   # Design: <feature>

   ## Architecture Overview
   <Prose or ASCII diagram: how components interact at the boundary level>

   ## Components Changed / Added
   | Component | File path | Change type | Purpose |
   |---|---|---|---|
   | <name> | `relative/path.py` | new / modify | <why> |

   ## Data Model / Schema Changes
   <New or modified models, fields, tables, config keys, or serialization formats.
   Include field names and types. "None" if no schema change.>

   ## API / Interface Changes
   <Function signatures, CLI flags, config keys, HTTP endpoints — include types and defaults.
   "None" if no interface change.>

   ## Error Handling Strategy
   <How errors surface (exceptions vs. return codes), how they propagate,
   how they're logged, what the caller contract is>

   ## Test Strategy
   <Which layers get unit tests (mock at what boundary?), which get integration tests,
   what fixtures or test data are needed>

   ## Invariant Compliance
   <Explicit statement for each Axis B rule: "complies because..." or
   "this design requires an invariant update: [proposed change]">
   ```

4. Save to `docs/02-design/features/<feature>.design.md`.
5. Prompt: "Design v1.0 ready. Review and approve, then I'll run the audit cycle."

**Advance gate**: User explicitly marks v1.0 approved. Then audit cycle begins.

**Back-propagation rule**: If an audit finding requires changing a decision that the plan stated, return to Phase 3 to re-clean the plan (re-audit until must-fix=0), then re-enter Phase 4 audit from cycle 1. Cap at 3 round-trips → halt `step4:back_prop_max`.

---

## Phase 5a — Impl-Plan

**Goal**: Generate a task-by-task implementation plan from the audited design.

**Steps**:

1. Read audited design + audited plan. Read `.h-mad/invariants.md`.
2. Decompose into tasks — each task is one cohesive module (typically one production file + its tests). Order tasks so dependencies resolve before dependents:

   ````markdown
   # Implementation Plan: <feature>

   > Source: docs/02-design/features/<feature>.design.md (post-audit)
   > Branch target: feature/NNN-<feature-slug>

   ## Task 1: <module-name>

   **Production file**: `<relative/path/to/module.py>`
   **Test file**: `<relative/path/to/test_module.py>`

   **Description**: <what this module does — one focused paragraph>

   **Code structure**:
   ```python
   # Key signatures — not implementations, just contracts
   def function_name(param: Type) -> ReturnType:
       """One-line docstring."""
       ...

   class ClassName:
       def method(self, arg: Type) -> ReturnType: ...
   ```

   **Acceptance Criteria**:
   - [ ] AC-N.M: <testable — Codex can write a pytest assertion for this>
   - [ ] AC-N.M: <testable>

   **Dependencies on other tasks**: Task N (must complete first) / None

   ---

   ## Task 2: <module-name>
   ...
   ````

3. Save to `docs/01-plan/features/<feature>.impl-plan.md`.
4. Proceed to Phase 5b audit (do not wait for user — this is autonomous).

**Quality bar** (the audit will catch violations, but pre-empt them):
- No TBD placeholders anywhere
- Every AC is specific and Codex-testable (not "works correctly")
- Exact file paths (not approximate — the TDD gate hook matches on these)
- Code structure blocks show real signatures that match the design's interface section
- Tasks are ordered (dependency graph is a DAG, not a cycle)

---

## Phase 6 — Gap Analysis

**Goal**: Measure what fraction of the design's FRs the implementation covers.

**Steps**:

1. Read `docs/01-plan/features/<feature>.spec.md` — extract the full FR list.
2. Read `docs/02-design/features/<feature>.design.md` — note the components/interfaces that implement each FR.
3. Get the implementation diff:
   ```bash
   # Get baseline SHA (Phase 5c commit) and head SHA (Phase 5g commit) from git log
   git log --oneline feature/NNN-<feature-slug> | head -20
   git diff <baseline-sha>..<head-sha> --stat
   git diff <baseline-sha>..<head-sha>
   ```
4. For each FR: read the relevant production files and check each AC against actual code.
5. Draft the analysis:

   ```markdown
   # Analysis: <feature>

   ## Match Rate: <N>%

   ## FR Coverage

   | FR | ACs Total | ACs Met | Status | Evidence |
   |---|---|---|---|---|
   | FR-1: <name> | 3 | 3 | ✅ Complete | `path/module.py:L42` |
   | FR-2: <name> | 2 | 1 | ⚠️ Partial | Missing AC-2.2 |
   | FR-3: <name> | 2 | 0 | ❌ Missing | Not in diff |

   ## Gaps

   ### Gap 1: <AC or FR not covered>
   - **Missing**: <what AC or behavior>
   - **Where it should be**: `<file path>`
   - **Fix**: <specific change needed>

   ## Test Results
   ```
   pytest <project>/tests/ -v --tb=short
   <paste last 20 lines of output>
   ```

   ## Verdict
   Match rate: <N>% (threshold: 90%). Tests: <N>/N passing.
   → <Advance to Phase 7 | Iterate — N gaps to close>
   ```

6. Save to `docs/03-analysis/<feature>.analysis.md`.
7. Parse match rate. If ≥90% AND tests 100%: advance. Else: Phase 6b iterate.

**Match rate formula**: `(FRs where all ACs are met) / (total FRs) × 100`.
An FR counts only if every one of its ACs passes — partial credit = 0 for that FR.

---

## Phase 6b — Iterate

**Goal**: Close gaps until match rate ≥90% AND tests 100% pass.

**Steps** (per cycle):

1. Read §Gaps from `docs/03-analysis/<feature>.analysis.md`.
2. For each gap:
   - Read the relevant production file
   - Implement the missing behavior
   - Run `pytest <test_path> -v` — confirm tests pass
   - Do NOT weaken existing tests or delete assertions to force green
3. Re-run full gap analysis (Phase 6 steps 1–7).
4. If ≥90% AND tests 100%: done — advance to Phase 7.
5. Else: repeat. Cap at 5 cycles total → halt `step6:iterate_max_cycles`.

**Rule**: Each iterate cycle must close at least one gap. If a cycle closes zero gaps, halt with `step6:iterate_no_progress` rather than spinning.

---

## Phase 7 — Report + Archive

### 7b — Report

Draft and save to `docs/04-report/features/<feature>.report.md`:

```markdown
# Report: <feature>

## Summary
<2-3 sentences: what was built, key decisions made, overall outcome>

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | N |
| Design audit cycles | N |
| Impl-plan audit cycles | N |
| Iterate cycles (Phase 6b) | N |
| Final match rate | N% |
| Tests | N passing / 0 failing |
| Phases with back-propagation | Phase N: <reason> / None |

## What Went Well
- <observation — specific, not generic>

## What To Improve Next Time
- <observation — specific enough to act on>

## Carry Items
- <anything deferred, explicitly out-of-scope, or left for follow-up work>
  "None" if nothing deferred.
```

### 7c — Archive

```bash
YYYYMM=$(date +%Y-%m)
FEATURE="<feature-slug>"
mkdir -p docs/archive/$YYYYMM/$FEATURE

# Move all feature artifacts (|| true silences mv errors for missing files)
mv docs/01-plan/features/${FEATURE}* docs/archive/$YYYYMM/$FEATURE/ 2>/dev/null || true
mv docs/02-design/features/${FEATURE}* docs/archive/$YYYYMM/$FEATURE/ 2>/dev/null || true
mv docs/03-analysis/${FEATURE}* docs/archive/$YYYYMM/$FEATURE/ 2>/dev/null || true
mv docs/04-report/features/${FEATURE}* docs/archive/$YYYYMM/$FEATURE/ 2>/dev/null || true
```

After archive: commit + push per SKILL.md §Phase 7 sub-steps 7d–7e.
