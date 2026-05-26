---
name: h-mad
description: Orchestrate the 7-phase H-MAD (Hawk Multi-Agents Development) workflow end-to-end. Standalone — no external skill dependencies (spec-kit, b-mad, or pdca). All phase protocols are built-in. Project-agnostic; splices project-specific Axis B invariants from `<PROJECT_ROOT>/.h-mad/invariants.md` into audit prompts at dispatch time. Use when user invokes /h-mad "<feature>", /h-mad do "<feature>", /h-mad status, or /h-mad reset "<feature>".
---

# /h-mad — 7-phase H-MAD Orchestrator (v2.2, standalone)

## Activation surface

| Invocation | What you do |
|---|---|
| `/h-mad "<feature>"` | Auto-bootstrap if needed, then smart-resume via `h_mad_resume_decision.py`; act per the returned token. |
| `/h-mad do "<feature>"` | Auto-bootstrap if needed. Force-start Phase 5. Run `h_mad_do_preconditions.py` first; refuse if non-zero. |
| `/h-mad status [<feature>]` | Auto-bootstrap if needed. Read-only. Print state from `docs/.bkit-memory.json`. Surface stale `phase = "step5"` flags (heuristic: `autonomous_entry_ts > 60min` ago AND `halt_reason = null`). |
| `/h-mad reset "<feature>"` | Clear `orchestrator_state[<feature>]`. Do NOT delete docs or revert git. |
| `/h-mad bootstrap` | Explicit bootstrap (idempotent re-run). Not required as first step — feature invocations auto-bootstrap. |

## First-run auto-bootstrap

Before any feature-level operation, check:
1. Does `.h-mad/invariants.md` exist in the current working directory (project root)?
2. Does `docs/.bkit-memory.json` exist?

If either is missing → run bootstrap automatically, then continue with the requested operation.

## Bootstrap action

Run from current project root (`pwd` at invocation):

1. **Create docs structure**:
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

3. **Copy invariants example if missing**:
   ```bash
   [ -f .h-mad/invariants.md ] || cp ~/.claude/skills/h-mad/invariants.example.md .h-mad/invariants.md
   ```

4. **Surface customize-this notice**:
   > "Bootstrap complete. Customize `.h-mad/invariants.md` with your project's Axis B invariants (currently contains a worked example — replace with your own rules). The orchestrator inlines this file as the Axis B rubric for plan/design/impl-plan audits and the Phase 6a-prime architectural review."

5. **Optionally suggest** `.gitignore` additions if user wants `docs/.bkit-memory.json` out of git.

Bootstrap does NOT touch existing files, modify git config, or author plan/design/impl-plan docs.

## Decision routing (for `/h-mad "<feature>"`)

Run: `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature "<feature>"`

| Token | What you do |
|---|---|
| `start_fresh` | Initialize `orchestrator_state[<feature>]`. Enter Phase 1. |
| `resume_manual` | Print current phase + last marker. Ask "continue from phase <N>?" |
| `enter_autonomous` | Print "all manual checkpoints clear; entering autonomous block." Enter Phase 5. |
| `halted` | Print `halt_reason` + recovery hints (see `references/failure-recovery.md`). Ask "resume, retry, or reset?" |
| `complete` | Print "feature complete; see docs/archive/<YYYY-MM>/<feature>/". Exit. |

## Per-phase actions

See `references/phase-table.md` for the full gate table. Detailed inline protocols in `references/inline-protocols.md`.

1. **Brainstorm** — run inline brainstorm protocol (`references/inline-protocols.md §Phase 1`). Output: `docs/01-plan/features/<feature>-brainstorm.md`. Wait for user approval.
2. **Specify** — run inline spec protocol (`references/inline-protocols.md §Phase 2`). Output: `docs/01-plan/features/<feature>.spec.md`. Wait for user approval.
3. **Plan + Audit-Plan** — run inline plan generation (`references/inline-protocols.md §Phase 3`). Output: `docs/01-plan/features/<feature>.plan.md`. Wait for user-approved v1.0, then auto-cycle: audit-plan via agy → awk gate → if must-fix > 0 OR should-fix > 0, surface bullets + wait for user revision → re-audit. **Exit ONLY when both must-fix = 0 AND should-fix = 0.** No cycle cap — the rationale is that if errors are already known (whether breakage-level or improvement-level), shipping them is worse than burning more cycles. Operator escape at any cycle: author `.audit.v<N+1>.md` with `## Acknowledged-not-fixed` section listing the should-fix items the operator chooses to defer, commit `[audit-override]`, and the gate treats those items as cleared.
4. **Design + Audit-Design** — run inline design generation (`references/inline-protocols.md §Phase 4`). Output: `docs/02-design/features/<feature>.design.md`. Same audit cycle pattern as Phase 3. Back-propagation: if design revision invalidates a plan decision, return to Phase 3 to re-clean, then re-enter Phase 4 audit from cycle 1.
5. **Implementation (autonomous)** — see Phase 5 sub-section below.
6. **Verification (autonomous)** — run inline gap analysis (`references/inline-protocols.md §Phase 6`). If match rate < 90%, run inline iterate (`references/inline-protocols.md §Phase 6b`) — 5-cycle cap. Loop until ≥90% AND 100% test pass. Phase 6a-prime is an agy architectural review before gap analysis.
7. **Closure (autonomous)** — `h_mad_telemetry.py record`, then inline report + archive (`references/inline-protocols.md §Phase 7`), then `git add -A && git commit && git push origin main`.

## Phase 5 (Implementation) sub-steps

- **5a** — arm hook + generate impl-plan via inline impl-plan protocol (`references/inline-protocols.md §Phase 5`). Write `orchestrator_state.<feature>.phase = "step5"` + `autonomous_entry_ts = <now>`. Output: `docs/01-plan/features/<feature>.impl-plan.md`.
- **5b** — auto-audit impl-plan (same agy audit-prompt mechanism as Phases 3/4 — see §"Audit prompt assembly"). Write audit to `docs/01-plan/features/<feature>.impl-plan.audit.v<N>.md`. Run awk gate. If must-fix > 0 OR should-fix > 0, regenerate impl-plan with both must-fix AND should-fix bullets appended; cycle until **both must-fix = 0 AND should-fix = 0**. No cycle cap — same rationale as Phase 3 (known errors at any severity worth fixing > shipping). Operator escape at any cycle: author `.impl-plan.audit.v<N+1>.md` with `## Acknowledged-not-fixed` listing deferred should-fix items, commit `[audit-override]`, gate treats those as cleared.
- **5c** — baseline branch: `git checkout -b feature/NNN-<slug>`; commit impl-plan + audit files.
- **5d** — RED dispatch via cmux (see `references/codex-implementer-prompt.md`). Verify Codex + agy panes alive (`cmux tree --all`); refuse if missing → halt `step5d:no_<agent>_pane`. For each module, dispatch Codex for tests; dispatch agy for coverage review. Verify all tests FAIL. Halt `step5d:red_not_all_failing` if any test passes without implementation.
- **5e** — GREEN dispatch via cmux (`references/codex-implementer-prompt.md` + `references/agy-spec-reviewer-prompt.md`). For each module, dispatch Codex for implementation; dispatch agy for spec-compliance review. If agy returns `VERDICT: DRIFT` → halt `step5e-review:spec_drift:<module>`. On 3rd consecutive GREEN failure → halt `step5e:green_unreachable:<module>`.
- **5f** — run full test suite: `pytest <project>/tests/ -v --tb=short`. All must pass (100%). Any failure → halt.
- **5g** — `git add -A && git commit -m "feat(<feature>): implement <module>"` per module. Write `phase = null` (disarms TDD gate hook). Emit `[H-MAD] <feature> phase5 complete`.

## Phase 6 (Verification) sub-steps

- **6a-prime** — architectural review via agy (`references/agy-architectural-reviewer-prompt.md`). Inputs: Phase 5 diff (BASE = 5c sha; HEAD = 5g sha) + audited design. Halt `step6a-prime:architectural_review_failed` on `WITH_FIXES` or `NO`.
- **6a** — run inline gap analysis. Parse match rate from `docs/03-analysis/<feature>.analysis.md`.
- **6b** — if < 90%, run inline iterate (5-cycle cap). Loop until ≥90% AND 100% test pass.

## Halt protocol

See `references/failure-recovery.md` for per-phase routes + recovery hints.

1. Write `orchestrator_state[<feature>]`: `halt_reason = "<phase>:<sub-step>:<description>"`, `halt_ts = <now>`, `phase = null`. Pin `current_phase` + `last_completed_phase`.
2. Emit `[H-MAD] <feature> phase<N> halted reason=<reason>`.
3. `cmux notify --title "/h-mad halted" --subtitle <feature> --body <reason>`.
4. Print recovery hints.
5. Exit.

## What you NEVER do

- Never skip the awk gate after an audit.
- Never auto-merge on `WITH_FIXES` or `NO` from agy.
- Never write `phase = null` before Phase 5g completes (that disarms the TDD hook prematurely).
- Never run `git push --force`.
- Never invoke Codex or agy directly — always via cmux file-indirection per CLAUDE.md §F-12.

## State schema

See `references/state-schema.md`. Validate with:

```bash
python3 -c "
import json, jsonschema
schema = json.load(open('$HOME/.claude/skills/h-mad/scripts/h_mad_state_schema.json'))
state = json.load(open('docs/.bkit-memory.json'))
for feat, fs in state.get('orchestrator_state', {}).items():
    jsonschema.validate(fs, schema)
print('OK')
"
```

## Audit prompt assembly

For each audit (Phase 3, 4, 5b), assemble the prompt as follows:

1. Start from `~/.claude/skills/h-mad/audit-prompt.template.md`.
2. Replace `<INLINE_TARGET_DOC>` with full text of the target doc (plan.md, design.md, or impl-plan.md).
3. Replace `<INLINE_PROJECT_INVARIANTS>` with full text of `.h-mad/invariants.md`.
4. For design audits only: replace `<INLINE_PAIRED_PLAN>` with audited plan.md.
5. For impl-plan audits only: replace `<INLINE_PAIRED_DESIGN>` with audited design.md.
6. Stage: `cat > /tmp/audit_<feature>_<phase>_cycle<N>.txt`.
7. Dispatch via cmux file-indirection:
   ```bash
   cmux send --surface <agy-surface> "$(cat /tmp/audit_<feature>_<phase>_cycle<N>.txt)"
   cmux send-key --surface <agy-surface> Enter
   ```
8. Capture: `cmux read-screen --surface <agy-surface> --lines 50`.
9. Write audit output to `docs/01-plan/features/<feature>.<phase>.audit.v<N>.md` (or `docs/02-design/features/` for design audits).
10. Run awk gate — counts bullets in BOTH `## Must-fix` AND `## Should-fix` sections (Acknowledged-not-fixed override: items listed under `## Acknowledged-not-fixed` in a sidecar `.audit.v<N+1>.md` are excluded from the count by the operator):
    ```bash
    awk '/^## Must-fix/{f=1;next} /^## Should-fix/{f=1;next} /^## /{f=0} f && /^- /{c++} END{exit (c>0)}' <audit-file>
    ```
    Exit 0 = gate passes (must-fix=0 AND should-fix=0). Exit 1 = gate fails (at least one must-fix or should-fix item remains). Nits never block.

## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)

- `h_mad_resume_decision.py` — smart-resume decision
- `h_mad_do_preconditions.py` — `/h-mad do` prereq verifier
- `h_mad_derive_test_path.sh` — production-path → test-path mapper
- `h_mad_emit_marker.sh` — `[H-MAD]` marker writer
- `h_mad_state_schema.json` — jsonschema for `orchestrator_state` (v2.2)
- `h_mad_telemetry.py` — Phase 7 cycle count recorder + summary

## Telemetry

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_telemetry.py record \
  --feature <feature> \
  --state docs/.bkit-memory.json \
  --out .h-mad/telemetry.jsonl
```

Non-fatal: if record fails, emit warning and continue to report.

Ad-hoc summary: `python3 ~/.claude/skills/h-mad/scripts/h_mad_telemetry.py summary`

## References

- `references/inline-protocols.md` — **Inline protocols for all phases (standalone, no external skills)**
- `references/phase-table.md` — full phase gate table
- `references/failure-recovery.md` — halt routes + recovery hints
- `references/state-schema.md` — state schema details
- `references/codex-implementer-prompt.md` — Phase 5d/5e Codex dispatch template
- `references/agy-spec-reviewer-prompt.md` — Phase 5e-review agy dispatch template
- `references/agy-architectural-reviewer-prompt.md` — Phase 6a-prime agy dispatch template
