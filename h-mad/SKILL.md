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

**Substrate preflight (Phase 5 + first audit dispatch).** Run `hmad-dispatch env`.
If it exits non-zero → halt `<phase>:no_substrate`. Record the printed substrate +
agent mapping via `scripts/h_mad_telemetry.py` so the run log states which environment
it dispatched under. This is the explicit environment check (cmux vs orca) — do it
before any `send`/`read`. See `references/agent-substrate.md`.

- **5a** — arm hook + generate impl-plan via inline impl-plan protocol (`references/inline-protocols.md §Phase 5`). Write `orchestrator_state.<feature>.phase = "step5"` + `autonomous_entry_ts = <now>`. Output: `docs/01-plan/features/<feature>.impl-plan.md`.
- **5b** — auto-audit impl-plan (same agy audit-prompt mechanism as Phases 3/4 — see §"Audit prompt assembly"). Write audit to `docs/01-plan/features/<feature>.impl-plan.audit.v<N>.md`. Run awk gate. If must-fix > 0 OR should-fix > 0, regenerate impl-plan with both must-fix AND should-fix bullets appended; cycle until **both must-fix = 0 AND should-fix = 0**. No cycle cap — same rationale as Phase 3 (known errors at any severity worth fixing > shipping). Operator escape at any cycle: author `.impl-plan.audit.v<N+1>.md` with `## Acknowledged-not-fixed` listing deferred should-fix items, commit `[audit-override]`, gate treats those as cleared.
- **5c** — baseline branch: `git checkout -b feature/NNN-<slug>`; commit impl-plan + audit files.
- **5d** — RED dispatch via `hmad-dispatch send` (see `references/codex-implementer-prompt.md`). Verify codex + agy alive (`hmad-dispatch alive codex` && `hmad-dispatch alive agy`); refuse if missing → halt `step5d:no_<agent>_pane`. **Immediately after confirming each pane is alive, clear its context** (see §"Agent-pane context hygiene") so no prior-feature/prior-cycle conversation bleeds into this feature's TDD. For each module, dispatch Codex for tests; dispatch agy for coverage review. Verify all tests FAIL. Halt `step5d:red_not_all_failing` if any test passes without implementation.
- **5e** — GREEN dispatch via `hmad-dispatch send` (`references/codex-implementer-prompt.md` + `references/agy-spec-reviewer-prompt.md`). Re-verify the Codex + agy panes alive and **clear each pane's context** (§"Agent-pane context hygiene") before the first GREEN dispatch of a feature. For each module, dispatch Codex for implementation; dispatch agy for spec-compliance review. If agy returns `VERDICT: DRIFT` → halt `step5e-review:spec_drift:<module>`. On 3rd consecutive GREEN failure → halt `step5e:green_unreachable:<module>`.
- **5f** — run full test suite: `pytest <project>/tests/ -v --tb=short`. All must pass (100%). Any failure → halt.
- **5g** — `git add -A && git commit -m "feat(<feature>): implement <module>"` per module. Write `phase = null` (disarms TDD gate hook). Emit `[H-MAD] <feature> phase5 complete`.

## Phase 5 parallel fanout (Orca only)

The serial Phase 5 path above remains the default and fallback. First partition the
impl-plan: a task with `Dependencies on other tasks: None` is independent; every
other task is dependent and remains serial in topological order on the shared tree.

Engage fanout IFF `hmad-dispatch env` shows `substrate=orca` (the command displays
`substrate: orca`) AND `orchestration: on` AND there are `≥2 independent` tasks.
If any condition is unmet, use the existing serial fallback.

For each independent task, run at most `HMAD_ORCA_MAX_WORKTREES` live worktrees
(default 4): `worktree-create <module> --base <feature-branch> --prompt-file
<staged-prompt>`; use Tier-2 `task-create` then `dispatch --to <selector>`; `await`
the worker; `git merge --no-ff <module-branch>`; then `worktree-rm <selector>`.
Tasks beyond the cap queue and log `[H-MAD] worktree_queued module=<module>`.

If `git merge --no-ff` fails or `git ls-files --unmerged` is non-empty, run
`git merge --abort`, emit `[H-MAD] merge_conflict module=<module>`, and re-dispatch
that module through the serial path after siblings merge. On any Phase-5 halt during
fanout, enumerate with `worktree-ps` and run `worktree-rm` for every worktree in the
fanout group. This teardown is idempotent: a gone selector logs and no-ops.

## Phase 6 (Verification) sub-steps

- **6a-prime** — architectural review via agy (`references/agy-architectural-reviewer-prompt.md`). Inputs: Phase 5 diff (BASE = 5c sha; HEAD = 5g sha) + audited design. **Clear the agy pane's context first** (§"Agent-pane context hygiene") — 6a-prime is a fresh architectural pass, not a continuation of the plan/design audit thread. Halt `step6a-prime:architectural_review_failed` on `WITH_FIXES` or `NO`.
- **6a** — run inline gap analysis. Parse match rate from `docs/03-analysis/<feature>.analysis.md`.
- **6b** — if < 90%, run inline iterate (5-cycle cap). Loop until ≥90% AND 100% test pass.

### Surfacing diffs at review gates (Orca only)

At Phase 3 plan approval, Phase 4 design approval, and Phase 6a verification, the
orchestrator MAY call `hmad-dispatch file-open-changed --mode diff` (or
`hmad-dispatch file-diff <path>`) to surface the diff in Orca's editor. This is
best-effort and non-blocking: a non-zero result (substrate≠orca or no editor) is
logged as `[H-MAD] <feature> diff_surface_skipped`, and the gate proceeds exactly
as today. Surfacing is never a gate precondition; the cmux review flow is unchanged.

HemaSuite may use `file-diff <manuscript.docx>` to surface a generated manuscript
DOCX; this is documented usage only, with no HemaSuite code in this feature.

## Agent-pane context hygiene

The codex and agy agents are **long-lived REPLs reused across every audit cycle, feature, and session**. Their conversation context accumulates: a plan-audit thread bleeds into the next design audit, one feature's TDD bleeds into the next feature's, and stale scrollback pollutes the `hmad-dispatch read` output you later grep for a verdict. Clear the context at the boundaries below so each fresh pass starts clean.

**When to clear (fresh pass) vs keep warm (continuation):**
- **Clear** at: the first cycle of each audit phase (Phase 3/4/5b cycle 1); 5d and the first 5e dispatch of a feature; 6a-prime; and whenever you confirm a pane is alive at the *start* of a new feature.
- **Keep warm** at: cycles 2..N of the *same* audit (the running revision thread — "here's the fix for your prior should-fix" — is exactly the context you want); a Codex GREEN retry within the same module.

**How to clear (per pane), then verify it took:**
```bash
# agy (Antigravity CLI) and codex both accept /clear:
hmad-dispatch clear codex
hmad-dispatch clear agy
# verify a clean prompt (no leftover input, not mid-run):
hmad-dispatch read <agent> --lines 6
```
If `/clear` is not honored or the pane is wedged (input box still shows queued text, or a 400/desync on agy), **restart the surface** instead: re-seed via the launch command (`agy --dangerously-skip-permissions` / the Codex CLI) per `AGENTS.md`, then re-confirm alive with `hmad-dispatch alive <agent>`. A restart is the hard reset; `/clear` is the cheap one. Never dispatch an audit/TDD prompt into a pane whose scrollback still shows the previous cycle's report — you will grep the wrong verdict.

**Cost note:** clearing is cheap and prevents two failure modes seen in practice — (a) an audit verdict influenced by an unrelated prior feature's discussion, and (b) `hmad-dispatch read` returning a stale prior-cycle report that the gate then parses as this cycle's result.

### Orchestration mode (Orca)

When `hmad-dispatch env` reports `orchestration: on` (Orca plus an `HMAD_ORCA_COORDINATOR_TERMINAL` pin), dispatch, verdict collection, and decision gates SHOULD use the structured orchestration verbs rather than screen scraping. The `send` / `read` / `wait` scrape flow remains the universal fallback for cmux or an unpinned coordinator. See `references/orchestration-mode.md`.

### Scheduling HemaSuite live-e2e as Orca automations (Orca only)

HemaSuite wiring is documented usage only: no HemaSuite code is changed by these lifecycle wrappers, and HemaSuite must execute in an Orca workspace. To schedule a nightly live-e2e, stage the prompt in a file and create the automation:

```bash
hmad-dispatch automation-create --name anemia-e2e --trigger cron --prompt-file <prompt-file> \
  --provider claude --precheck "hpw doctor" --repo HemaSuite
```

`--provider` must be a provider Orca recognizes — verified live-valid values are `claude`, `codex`, `gemini` (NOT `agent`; Orca rejects unknown providers with `invalid_argument`). Target the run with `--repo <name>` (or `--workspace`/`--project`). Note `--trigger` (`preset|cron|rrule`) and `--schedule` are mutually exclusive; a preset such as `daily` needs no `--schedule`.

Run one ad hoc with `hmad-dispatch automation-run <id>`, enumerate configured jobs with `hmad-dispatch automation-list`, and clean up with `hmad-dispatch automation-remove <id>`. The `<id>` is the automation id returned by `automation-create` (extracted from `.result.automation.id`), NOT the response envelope id.

## Halt protocol

See `references/failure-recovery.md` for per-phase routes + recovery hints.

1. Write `orchestrator_state[<feature>]`: `halt_reason = "<phase>:<sub-step>:<description>"`, `halt_ts = <now>`, `phase = null`. Pin `current_phase` + `last_completed_phase`.
2. Emit `[H-MAD] <feature> phase<N> halted reason=<reason>`.
3. `hmad-dispatch notify "/h-mad halted" "<reason>"`.
4. Print recovery hints.
5. Exit.

## What you NEVER do

- Never skip the gate (`h_mad_audit_gate.py`) after an audit.
- Never parse the gate via `$?`/exit code — parse the `GATE:` token; the gate exits 0 on a verdict by design.
- Never auto-merge on `WITH_FIXES` or `NO` from agy.
- Never write `phase = null` before Phase 5g completes (that disarms the TDD hook prematurely).
- Never run `git push --force`.
- Never invoke Codex or agy directly — always via `hmad-dispatch` file-indirection (see `references/agent-substrate.md`) per CLAUDE.md §F-12.

## Known interactions (coexisting plugins)

`/h-mad` has **zero runtime dependency** on any other plugin. It does, however, coexist with plugins that install Claude Code hooks. The notable one is **OMC** (`oh-my-claudecode`), whose `persistent-mode.mjs` produces two streams of noise during `/h-mad` runs:

- **Autopilot Stop-hook nag** — emits "Autopilot not complete" on most turns even with no autopilot state on disk (an unconditional nag, not state-driven).
- **Tool-error retry guidance** — `post-tool-use-failure.mjs` records any tool failure to `last-tool-error.json`; `persistent-mode.mjs` then injects `[TOOL ERROR - RETRY REQUIRED]` (escalating to "STOP RETRYING" at retry_count ≥ 5) on the next Stop.

The retry-guidance stream was historically triggered by the audit gate itself: the old gate used a non-zero exit (`awk … exit (c>0)`) as its FAIL signal, which the harness reported as a `PostToolUseFailure`. **This is fixed at the root** — the gate now signals via the `GATE:` token and exits 0 (Audit-gate signal discipline, base invariant), so a legitimate gate-FAIL no longer registers as a tool error. The retry-guidance noise during `/h-mad` is therefore resolved skill-side; OMC's behavior was correct given a real non-zero exit.

Workaround for the **separate** autopilot Stop-hook nag (not addressed by the gate fix): `export DISABLE_OMC=1` (or `OMC_SKIP_HOOKS=persistent-mode`) for the session. Never switch to the OMC autopilot skill mid-`/h-mad`.

## State schema

See `references/state-schema.md`. Validate with:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_validate.py docs/.bkit-memory.json
```

Validation is **two-tier**, because the v2.2 schema was never enforced at write
time and forbade extra properties, so established stores hold many one-off
shapes and a single-tier check always failed:

- `strict` — conforms to v2.2 (`h_mad_state_schema.json`).
- `historical` — conforms to `h_mad_state_schema_historical.json`: the three
  fields every observed record carries, extras allowed.
- `invalid` — neither. Genuinely broken; look at it.

Parse the **token**, not `$?` — same discipline as the audit gate, which
exits 0 on a verdict so a FAIL never registers as a tool failure:

- `STATE: PASS strict=N historical=M invalid=0` → proceed.
- `STATE: FAIL … invalid=K` → the named records are broken.

**After writing a record, verify it meets v2.2** — this is what stops the
drift that produced the historical tier:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_validate.py \
  docs/.bkit-memory.json --feature <feature> --strict-only
```

Never invent a key. If a run needs a field the schema lacks, add it to
`h_mad_state_schema.json` rather than writing it ad hoc — that is exactly how
the store accumulated five spellings of "merge sha".

## Audit prompt assembly

**Substrate preflight (once per H-MAD run — at Phase 5 start, or the first audit dispatch if earlier; skip if the substrate was already recorded this run).** Run `hmad-dispatch env`.
If it exits non-zero → halt `<phase>:no_substrate`. Record the printed substrate +
agent mapping via `scripts/h_mad_telemetry.py` so the run log states which environment
it dispatched under. This is the explicit environment check (cmux vs orca) — do it
before any `send`/`read`. See `references/agent-substrate.md`.

For each audit (Phase 3, 4, 5b), assemble the prompt as follows:

1. Start from `~/.claude/skills/h-mad/audit-prompt.template.md`.
2. Replace `<INLINE_TARGET_DOC>` with full text of the target doc (plan.md, design.md, or impl-plan.md).
3. Replace `<INLINE_BASE_INVARIANTS>` with full text of `~/.claude/skills/h-mad/invariants.base.md` (workflow-universal Axis B — always inlined, base before project, regardless of whether a project file exists).
4. Replace `<INLINE_PROJECT_INVARIANTS>` with full text of `<PROJECT_ROOT>/.h-mad/invariants.md` (domain Axis B). If the project file is absent/empty, leave the slot empty — the base layer still applies.
5. For design audits only: replace `<INLINE_PAIRED_PLAN>` with audited plan.md.
6. For impl-plan audits only: replace `<INLINE_PAIRED_DESIGN>` with audited design.md.
6.5. Replace `<AUDIT_SENTINEL>` with `AUDIT-<feature>-<phase>-v<N>` — the per-cycle stem step 9 extracts on. It must be unique per cycle; reusing a previous cycle's stem reopens the stale-scrollback trap it exists to close.
7. Stage: `cat > /tmp/audit_<feature>_<phase>_cycle<N>.txt`.
7.5. **On cycle 1 of each audit phase (and after confirming agy is alive via `hmad-dispatch alive agy`), clear agy's context** (see §"Agent-pane context hygiene") so a prior feature's/phase's transcript can't drift the verdict or pollute the scrollback you later grep. Later cycles of the SAME audit reuse the warm context (the running revision thread is wanted).
8. Dispatch via `hmad-dispatch` file-indirection:
   ```bash
   hmad-dispatch send agy /tmp/audit_<feature>_<phase>_cycle<N>.txt
   ```
9. Capture and extract — **never hand a raw scrape to the gate.** The scrape holds live scrollback, so the previous cycle's report is usually still above the prompt; extracting on the first `## Summary` scores the wrong cycle:
   ```bash
   hmad-dispatch read agy --lines 200 > /tmp/scrape_<feature>_<phase>_cycle<N>.txt
   python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_report.py \
     /tmp/scrape_<feature>_<phase>_cycle<N>.txt \
     --feature <feature> --phase <phase> --cycle <N> \
     > docs/01-plan/features/<feature>.<phase>.audit.v<N>.md
   ```
   The extractor takes the **last** complete `<AUDIT_SENTINEL>-BEGIN`/`-END` pair, so neither an older cycle nor a retry within this one can win. It exits 2 and writes nothing when the pair is missing or its body is empty — that is the "dispatched, went idle, produced nothing" case, and it must halt the cycle rather than be scored. On exit 2: re-read with a larger `--lines`, and if the report genuinely never arrived, `hmad-dispatch clear agy` and re-dispatch.
10. Design audits write to `docs/02-design/features/` instead; adjust the redirect above.
11. Run the gate — the verdict unit counts bullets in BOTH `## Must-fix` AND `## Should-fix` (excluding the bare-`None` sentinel, a stray `- None`, and any `## Acknowledged-not-fixed` items in the same file or a sidecar `.audit.v<N+1>.md` passed via `--ack-file`):
    ```bash
    python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py <audit-file>
    ```
    The gate **prints a verdict token and always exits 0** on a verdict (a non-zero exit is reserved for operational errors such as a missing file — never for a FAIL, so the gate never registers as a tool failure). Parse the **token**, not `$?`:
    - `GATE: PASS must=0 should=0` → gate passes (must-fix=0 AND should-fix=0). Proceed.
    - `GATE: FAIL must=N should=M` (N or M > 0) → gate fails. Surface the bullets, revise, re-audit.
    The gate emits a `[H-MAD] <feature> gate <verdict>` marker line. Nits never block. If the `GATE:` token is absent from stdout (unexpected), treat it as an operational error and halt `step<N>:gate_token_missing` with a `[H-MAD]` marker — never silently treat a missing token as PASS.

## Putting `hmad-dispatch` on PATH

This file spells the wrapper as a bare `hmad-dispatch <verb>`. Put the skill's
`bin/` on PATH once so those commands work verbatim instead of needing the
absolute path to `scripts/hmad-dispatch.sh` (which differs per install and per
checkout):

```bash
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
```

## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)

- `h_mad_extract_report.py` — pull the reviewer's report out of a pane scrape on the last `AUDIT-<feature>-<phase>-v<N>-BEGIN`/`-END` pair; exit 2 (writing nothing) when the pair is missing or empty
- `h_mad_audit_gate.py` — audit-gate verdict unit (single source of truth): `classify()` + CLI printing `GATE: PASS|FAIL` + `[H-MAD]` marker, exit 0 on verdict / 2 on operational error; `--must-only` for the `/h-mad do` precondition. Imported by `h_mad_do_preconditions.py`.
- `h_mad_resume_decision.py` — smart-resume decision
- `h_mad_do_preconditions.py` — `/h-mad do` prereq verifier (uses `h_mad_audit_gate.classify`)
- `h_mad_derive_test_path.sh` — production-path → test-path mapper
- `h_mad_emit_marker.sh` — `[H-MAD]` marker writer
- `h_mad_state_schema.json` — jsonschema for `orchestrator_state` (v2.2, strict tier)
- `h_mad_state_schema_historical.json` — permissive tier for pre-v2.2 records
- `h_mad_state_validate.py` — two-tier state validator: `classify()` + CLI printing `STATE: PASS|FAIL` + `[H-MAD]` marker, exit 0 on verdict / 2 on operational error; `--strict-only` enforces v2.2 on a record you just wrote
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
- `references/agent-substrate.md` — Agent dispatch substrate (cmux | orca) — hmad-dispatch verbs, detection, identity pins, pane launch
- `references/orchestration-mode.md` — Orca structured orchestration and Phase-5 worktree fanout protocol
- `references/codex-implementer-prompt.md` — Phase 5d/5e Codex dispatch template
- `references/agy-spec-reviewer-prompt.md` — Phase 5e-review agy dispatch template
- `references/agy-architectural-reviewer-prompt.md` — Phase 6a-prime agy dispatch template
