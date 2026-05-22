---
name: h-mad
description: Orchestrate the 7-phase H-MAD (Hawk Multi-Agents Development) workflow end-to-end. Project-agnostic methodology; splices project-specific Axis B invariants from `<PROJECT_ROOT>/.h-mad/invariants.md` into the audit-prompt template at dispatch time. Use when user invokes /h-mad "<feature>", /h-mad do "<feature>", /h-mad status, or /h-mad reset "<feature>".
---

# /h-mad — 7-phase H-MAD Orchestrator (v2.2)

Drive a feature through 7 B-MAD-style phases from one entry point.

- Phases 1–4: **manual checkpoints** (user approves between phases; audit cycles within Phases 3 and 4 are internal loops that pause for user revisions)
- Phases 5–7: **autonomous** (run end-to-end without user input)

H-MAD = **Hawk Multi-Agents Development** — reusable across all of Hawk's projects, not HemaSuite-specific. HemaSuite is the v2.2 pilot consumer.

## Activation surface

| Invocation | What you do |
|---|---|
| `/h-mad "<feature>"` | Auto-bootstrap if needed (see §"First-run auto-bootstrap"), then smart-resume via `h_mad_resume_decision.py`; act per the returned token. |
| `/h-mad do "<feature>"` | Auto-bootstrap if needed. Force-start Phase 5. Run `h_mad_do_preconditions.py` first; refuse if non-zero. |
| `/h-mad status [<feature>]` | Auto-bootstrap if needed. Read-only. Print state from `docs/.bkit-memory.json`. Surface stale `phase = "step5"` flags (heuristic: `autonomous_entry_ts > 60min` ago AND `halt_reason = null`). |
| `/h-mad reset "<feature>"` | Clear `orchestrator_state[<feature>]`. Do NOT delete docs or revert git. |
| `/h-mad bootstrap` | Explicit bootstrap (idempotent re-run, or inspect scaffold before invoking on a feature). Not required as a first step — feature invocations auto-bootstrap. |

## First-run auto-bootstrap

Before running any feature-level command (`/h-mad "<feature>"`, `/h-mad do "<feature>"`, `/h-mad status`), check whether the current project root has been bootstrapped:

- `<project>/.h-mad/invariants.md` exists
- `<project>/docs/.bkit-memory.json` exists

If **either** is missing, run the Bootstrap action below silently, then surface a single inline notice:

> "Project not bootstrapped for /h-mad — auto-bootstrapped now. Customize `.h-mad/invariants.md` with your project's Axis B invariants before Phase 3 audit-plan dispatches (currently contains the HemaSuite worked example as a starting point)."

Then proceed with the original command (resume_decision / preconditions / status). The user gets to Phase 1 brainstorm with zero extra steps; they have all of Phases 1–2 to edit `.h-mad/invariants.md` before Phase 3's audit cycles fire.

Auto-bootstrap is idempotent — re-running it on an already-bootstrapped project is a no-op (every step is `[ -f ... ] || ...` guarded). Skip the notice when nothing changed.

Refuse `/h-mad reset "<feature>"` if the project isn't bootstrapped — there's nothing to reset. Surface "Run /h-mad bootstrap or invoke /h-mad on a feature first."

## Bootstrap action

Bootstrap fires either explicitly (`/h-mad bootstrap`) or implicitly (first feature-level invocation on an unbootstrapped project — see §"First-run auto-bootstrap"). The skill is globally installed; each consuming project needs a few directories + a state file. Run from current project root (`pwd` at invocation):

1. **Create docs structure** (mkdir -p; safe to re-run):
   ```bash
   mkdir -p docs/01-plan/features docs/02-design/features docs/03-analysis docs/04-report/features docs/archive .h-mad
   ```

2. **Create `docs/.bkit-memory.json` if missing**:
   ```bash
   [ -f docs/.bkit-memory.json ] || cat > docs/.bkit-memory.json <<'EOF'
   {
     "version": 1,
     "orchestrator_state": {}
   }
   EOF
   ```

3. **Copy invariants example to `.h-mad/invariants.md` if missing**:
   ```bash
   [ -f .h-mad/invariants.md ] || cp ~/.claude/skills/h-mad/invariants.example.md .h-mad/invariants.md
   ```

4. **Surface customize-this notice**:
   > "Bootstrap complete. Customize `.h-mad/invariants.md` with your project's Axis B invariants (currently contains HemaSuite worked example — replace with your own rules). The orchestrator inlines this file as the Axis B rubric for plan/design/impl-plan audits and the Phase 6a-prime architectural review."

5. **Optionally suggest** `.gitignore` additions if user wants `docs/.bkit-memory.json` out of git (it contains in-flight orchestrator state).

Bootstrap does NOT touch existing files, modify git config, install the skill itself, or author plan/design/impl-plan docs (those are Phases 3, 4, 5a).

After bootstrap, the project is ready for `/h-mad "<feature>"` to begin Phase 1 brainstorm.

## Decision routing (for `/h-mad "<feature>"`)

Run: `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature "<feature>"`

| Token | What you do |
|---|---|
| `start_fresh` | Initialize `orchestrator_state[<feature>]`. Enter Phase 1. |
| `resume_manual` | Print current phase + last marker. Ask "continue from phase <N>?" |
| `enter_autonomous` | Print "all manual checkpoints clear; entering autonomous block." Enter Phase 5. |
| `halted` | Print `halt_reason` + recovery hints (see references/failure-recovery.md). Ask "resume, retry, or reset?" |
| `complete` | Print "feature complete; see docs/archive/<YYYY-MM>/<feature>/". Exit. |

## Per-phase actions

See `references/phase-table.md` for the full table. Summary:

1. **Brainstorm** — invoke `/brainstorm`; wait; advance prompt.
2. **Specify** — invoke `/speckit.specify`; wait; prompt.
3. **Plan + Audit-Plan** — invoke `/pdca plan`; wait for user-approved plan v1.0. Then auto-cycle: `/pdca audit-plan` → check awk gate → if must-fix > 0, surface bullets and wait for user to revise plan → re-audit. Exit when must-fix = 0 OR halt at 5-cycle cap.
4. **Design + Audit-Design** — invoke `/pdca design`; wait for v1.0. Auto-cycle `/pdca audit-design` (adversarial + cross-doc). Handle back-propagation: if design revision changes plan decision, return to Phase 3 to re-clean plan-audit, then re-enter Phase 4 audit from cycle 1.
5. **Implementation (autonomous)** — see Phase 5 sub-section below.
6. **Verification (autonomous)** — invoke `/pdca analyze`; if match < 90%, `/pdca iterate` (5-cycle cap); loop until ≥90% AND 100% test pass. Phase 6a-prime is an architectural review pass before /pdca analyze.
7. **Closure (autonomous)** — `/pdca report`, `/pdca archive`, `git add -A && git commit`, `git push origin main`.

## Phase 5 (Implementation) sub-steps

This phase is the only programmatic enforcement (orchestrator dispatch + PreToolUse hook gate). Sub-steps:

- **5a — arm hook + generate impl-plan via writing-plans**: write `orchestrator_state.<feature>.phase = "step5"` + `autonomous_entry_ts = <now>`. **Invoke `superpowers:writing-plans` skill** with the audited design as input. The skill produces `docs/01-plan/features/<feature>.impl-plan.md` (task-by-task with exact paths + code blocks). Replaces the legacy `/tasks` invocation.
- **5b — auto-audit impl-plan**: construct the audit prompt using the audit-prompt template's `impl-plan` role clause (extended in HemaSuite for v2.2). Dispatch agy via cmux file-indirection. Write the audit output to `docs/01-plan/features/<feature>.impl-plan.audit.v<N>.md`. Run the awk gate. If must-fix > 0, re-invoke writing-plans with the must-fix bullets appended; cycle until must-fix = 0 OR 5-cycle cap. On cap, halt with `step5b:impl_plan_audit_max_cycles`.
- **5c — baseline branch**: `git checkout -b feature/NNN-<slug>`; commit impl-plan + impl-plan-audit files as baseline.
- **5d — RED dispatch via cmux (parallel) — uses references/codex-implementer-prompt.md**: verify Codex + agy panes alive (`cmux tree --all`); refuse if missing (`halt_reason = step5d:no_<agent>_pane`). For each module in impl-plan, write prompt to `/tmp/h_mad_<feature>_red_<N>.txt` (file-indirection per CLAUDE.md §F-12). Dispatch Codex pane for tests; dispatch agy pane for coverage review. Capture via `cmux read-screen`; parse Codex response for status enum (`DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`); halt on BLOCKED/NEEDS_CONTEXT. Verify all test files committed AND `pytest -v` shows ALL FAIL.
- **5e — GREEN dispatch via cmux (per-module, sequential) — uses references/codex-implementer-prompt.md**: For each module: dispatch Codex with the prompt-template body. Hook layer actively gates each Write/Edit. After Codex reports done with status enum, run `pytest <test_path>`; verify GREEN. If status = BLOCKED / NEEDS_CONTEXT, halt with explicit reason. If FAILED after 3 codex retries, halt with `step5e:green_unreachable:<module>`.
- **5e-review (v2.1 NEW)** — Per-module spec-compliance review: Before committing the module from 5e, dispatch agy with `references/agy-spec-reviewer-prompt.md`. Inputs: impl-plan task block + diff of files Codex changed. If agy returns VERDICT: COMPLIANT → commit module + advance. If VERDICT: DRIFT → halt with `step5e-review:spec_drift:<module>` and surface findings.
- **5f** — (Optional) REFACTOR sub-phase per impl-plan guidance.
- **5g** — Set `orchestrator_state.phase = null` (disarms hook). Set `last_completed_phase = 5`. Emit `[H-MAD] <feature> phase5 gate_passed`.

## Phase 6 (Verification) sub-steps

- **6a-prime (v2.1 NEW)** — Final-implementation architectural review: Before `/pdca analyze`, dispatch agy with `references/agy-architectural-reviewer-prompt.md`. Inputs: full Phase 5 diff (BASE = 5c baseline; HEAD = 5g closure) + audited design.md. If agy returns ASSESSMENT: READY_TO_MERGE → advance to 6a. If WITH_FIXES or NO → halt with `step6a-prime:architectural_review_failed`.
- **6a** — Invoke `/pdca analyze`; parse match rate.
- **6b** — If < 90%, `/pdca iterate` (5-cycle cap); loop until ≥ 90% AND 100% test pass.

## Halt protocol

See `references/failure-recovery.md` for per-phase failure modes + recovery hints.

1. Write `orchestrator_state.<feature>`: `halt_reason = "<phase>:<sub-step>:<short-description>"`, `halt_ts = <now>`, `phase = null`. Pin `current_phase` + `last_completed_phase`.
2. Emit `[H-MAD] <feature> phase<N> halted reason=<reason>`.
3. `cmux notify --title "/h-mad halted" --subtitle <feature> --body <reason>`.
4. Print recovery hints.
5. Exit.

## What you NEVER do

- Auto-rollback (`git reset --hard`).
- Retry-with-different-prompt beyond 3-codex-retries-per-module.
- `--no-verify` on commit (global git safety rule).
- Force-push on non-FF (operator pull-rebases manually).
- Amend on commit failure (always create new commits).
- Spawn new Codex/agy panes (verify alive; refuse if missing — per HemaSuite verify-don't-spawn rule).

## State schema

See `references/state-schema.md` for the full `orchestrator_state.<feature>` shape (v2.2: `phase ∈ {step5, step6, step7, null}`; `audit_cycles` includes `impl_plan` key).

## Audit prompt assembly

At every audit dispatch (Phases 3, 4, 5b) and Phase 6a-prime architectural review, the orchestrator builds the agy prompt by splicing two files:

1. **Skeleton** (project-agnostic, lives in this skill): `~/.claude/skills/h-mad/audit-prompt.template.md`
2. **Project Axis B invariants** (project-specific, lives in the consuming repo): `<PROJECT_ROOT>/.h-mad/invariants.md`

Splice procedure:
1. Read both files.
2. Replace `<INLINE_TARGET_DOC>` with the target plan/design/impl-plan body.
3. Replace `<INLINE_PAIRED_PLAN>` / `<INLINE_PAIRED_DESIGN>` for design/impl-plan audits respectively (omit lines when not applicable).
4. Replace `<INLINE_PROJECT_INVARIANTS>` with the **body** of the project's `invariants.md` (drop the file's own header/frontmatter — keep just the rubric content).
5. Stage at `/tmp/audit_<feature>_<phase>_cycle<N>.txt`.
6. Dispatch agy via cmux file-indirection (`cmux send --surface <N> "Use view_file to read /tmp/audit_... and execute"` + `send-key enter`).

If `<PROJECT_ROOT>/.h-mad/invariants.md` is missing, halt with `<phase>:no_project_invariants` and surface `/h-mad bootstrap` as the recovery hint.

## Helper scripts (all in ~/.claude/skills/h-mad/scripts/)

- `h_mad_resume_decision.py` — smart-resume decision
- `h_mad_do_preconditions.py` — `/h-mad do` prereq verifier
- `h_mad_derive_test_path.sh` — production-path → test-path mapper
- `h_mad_emit_marker.sh` — `[H-MAD]` log marker writer
- `h_mad_state_schema.json` — jsonschema for `orchestrator_state` (v2.2)

## Prompt templates (all in ~/.claude/skills/h-mad/references/)

- `codex-implementer-prompt.md` — Phase 5d/5e Codex dispatch body (v2.1)
- `agy-spec-reviewer-prompt.md` — Phase 5e-review per-module spec-compliance body (v2.1)
- `agy-architectural-reviewer-prompt.md` — Phase 6a-prime full-diff architectural body (v2.1)
