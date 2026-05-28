# Brainstorm: h-mad-audit-surfaces-reconcile

## Problem Statement

The `/h-mad` orchestrator skill (`github.com/BrightGold70/skills/h-mad/`) defines its audit-gate empty-section contract in **three independent places** that disagree, producing false gate-FAILs and recurring hook/audit warnings during real feature runs. The audit-prompt template tells the agy reviewer "empty section → write None", but the two gate readers count *any* `- `-prefixed line inside `## Must-fix`/`## Should-fix` — so a reviewer who writes `- None` (a natural bullet form) is scored as 1 blocking item and a clean audit falsely fails the gate. This was the highest-priority item in the `nlm-source-dedup-ledger` friction log and cost real audit cycles.

## Proposed Approach

Lock all three audit-gate surfaces to **one shared, explicitly-specified empty-section contract**, then cover the contract with tests so the three readers can never silently drift again. Bundle a small auxiliary deliverable for the OMC autopilot Stop-hook false-positive that nags every turn during `/h-mad` runs (workaround + upstream issue), since it is part of the same "hook warnings during /h-mad" pain the user reported.

The three surfaces:

1. **Template** — `audit-prompt.template.md:43,47,51` — the `*(empty section: write "None")*` guidance the agy reviewer follows when authoring an audit doc.
2. **Awk-gate** — `SKILL.md:149` — `awk '/^## Must-fix/{f=1;next} /^## Should-fix/{f=1;next} /^## /{f=0} f && /^- /{c++} END{exit (c>0)}'` — counts `- ` bullets in **Must-fix AND Should-fix**.
3. **Preconditions parser** — `scripts/h_mad_do_preconditions.py:24-36` (`_count_must_fix`) — counts `- ` bullets in **Must-fix only** (confirmed same-class: same `- ` bullet-counting logic).

Three distinct discrepancy/defect axes surfaced during investigation:

- **Axis 1 — empty-sentinel**: `- None` is counted as a blocking bullet by both gates; the template never forbids the leading dash. (The reported correctness bug.)
- **Axis 2 — section scope**: the awk-gate blocks on Must-fix **+** Should-fix; preconditions.py blocks on Must-fix **only**. The two "must-fix=0" gates are not equivalent — a clean awk-gate pass and a clean preconditions pass can mean different things.
- **Axis 3 — exit-code-as-signal → OMC retry noise (root cause of "many OMC re-trying errors")**: the awk-gate uses `END{exit (c>0)}`, i.e. the **process exit code is the PASS/FAIL signal**. A gate-FAIL is the *normal* mid-audit-cycle case, but run as a Bash tool it returns exit 1, which the Claude Code harness reports as a tool failure (`PostToolUseFailure`). OMC's `post-tool-use-failure.mjs` then writes `last-tool-error.json` (awk is not in its suppression list) with an incrementing `retry_count`; at the next Stop, `persistent-mode.mjs` injects `[TOOL ERROR - RETRY REQUIRED]`, and at `retry_count >= 5` the `[TOOL ERROR - ALTERNATIVE APPROACH NEEDED]` "STOP RETRYING" variant. Every legitimately-failing gate cycle thus surfaces as a retried tool error.

**Convergence**: Axis-1 and Axis-3 are the *same* awk-gate line. A single fix — make the gate **print an explicit `GATE: PASS|FAIL` token and always `exit 0`**, with the orchestrator parsing the token instead of the exit code — eliminates the empty-section brittleness (the token-printer becomes the single shared parser all three surfaces call) *and* stops the gate from looking like a tool failure to the harness/OMC. This reframes the OMC side: OMC is arguably *correct* to flag a genuine non-zero exit, so the durable fix is h-mad-side; the OMC deliverable shrinks to documentation + an informational (not bug) upstream note.

## Alternatives Considered

- **Shared token-printing parser, always `exit 0` (front-runner — addresses Axis 1 + 2 + 3)**: extract one parser (Python, or a single sourced shell function) that classifies an audit doc and prints `GATE: PASS`/`GATE: FAIL` plus a structured count; both the orchestrator gate-step and `h_mad_do_preconditions.py` call it; it never uses the exit code as the signal. Collapses surfaces 2+3 into one implementation, makes empty-sentinel handling defined in exactly one place, and stops gate-FAILs from registering as tool failures. Heaviest change but the only option that closes all three axes; deferred to design for the exact shape.
- **Fix template only (mandate bare `None`)**: smallest change — instruct the reviewer to emit bare `None` (no dash). Rejected as *sole* fix because it leaves the gates brittle to any future/human-authored audit that writes `- None`, and does nothing for Axis 3 (exit-code noise). (Kept open as half of the Axis-1 decision — see Open Questions.)
- **Fix gates only (exclude `- None`)**: make awk + preconditions skip a bullet whose text is exactly `None`. Rejected as *sole* fix because the template would still emit ambiguous guidance, and the awk `exit (c>0)` Axis-3 noise persists. (Also kept open — see Open Questions.)
- **Keep awk one-liner but stop using its exit code** (`awk ... ; print token`): minimal Axis-3 patch without restructuring. Viable middle ground if the shared-parser refactor is judged too heavy in design.
- **Do nothing / keep manual workaround** ("always write bare `None` by hand" + `DISABLE_OMC=1`): rejected — that is the status quo that produced the friction log; relies on operator memory every run.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Changing the awk-gate breaks the Acknowledged-not-fixed override semantics | M | Test matrix must include the `## Acknowledged-not-fixed` sidecar case; preserve current override behavior exactly |
| Aligning preconditions.py scope (Must-only → Must+Should) changes `/h-mad do` gating for existing in-flight features | L | Treat Axis-2 alignment as an explicit design decision; if changed, document the behavior delta; no in-flight features in this repo |
| Bash-level gate hard to unit-test portably | M | Wrap awk in a tested shape (script or python equivalent) OR drive bats/python-subprocess tests against the literal one-liner |
| Changing the gate from `exit 0/1` to token-printing breaks existing callers that read the exit code | M | Inventory every caller (SKILL.md:147-150 orchestrator step; `h_mad_do_preconditions.py` uses its own in-process count, not the exit code) before changing the contract; update SKILL.md gate-step text in lockstep; tests assert token output |
| Scope creep into the other 4 friction-log items | M | Explicit Out-of-Scope list below; audit cycles will flag FRs that leak |
| OMC retry-noise re-verification: behavior tied to a specific OMC version (`post-tool-use-failure.mjs` suppression list may change) | L | Document the observed mechanism with the OMC version pinned; frame upstream note as informational (non-zero exit correctly flagged), not a bug report |

## Dependencies

Self-contained within the `BrightGold70/skills` repo for this feature's deliverables. Full h-mad dependency inventory (verified this session) — relevant because the user requires the skill to carry **no external plugin dependency like OMC**:

- **Plugin dependencies: NONE.**
  - `omc` — **0 references** in the skill. OMC is a purely passive runtime *conflict* (retry-noise + Stop-nag), never a dependency.
  - `bkit` — 5 references, all filename-only: the state file is `docs/.bkit-memory.json` and state-schema notes "pre-existing bkit fields preserved". This is a coexistence accommodation (shared file), **not** a runtime dependency on the bkit plugin. (Renaming the state file = separate concern, out of scope — see below.)
  - `spec-kit` / `b-mad` / `pdca` — references are disclaimers only ("no X required"). Not dependencies.
- **External CLI dependencies (intrinsic, cannot be internalized): `cmux`, `agy`, `codex`** — the multi-agent dispatch substrate used in Phases 3/4/5/6. These *are* H-MAD's mechanism (Hawk **Multi-Agents** Development); removing them is meaningless. Out of scope.
- **Tool dependencies: `jq`** (h-mad-tdd-gate.sh; already fails open if absent), **`jsonschema`** (state-validate snippet — absent from system python; real fragility, friction item 4 — but out of scope here), **`pytest`** (Phase 5f).

**Feature-relevant self-containment goal**: the Axis-3 fix *internalizes the audit-gate PASS/FAIL signal*. Today the gate's correctness implicitly depends on the Claude Code harness interpreting its non-zero exit code (and that interpretation leaks to OMC via `PostToolUseFailure`). Printing a `GATE: PASS|FAIL` token and always exiting 0 makes the gate's verdict self-described and independent of any external hook's reading of the exit code. The feature must also introduce **no new** external dependency in its own deliverables (parser/template/tests).

OMC upstream note is an informational draft artifact only (no code dependency on the OMC repo).

## Out-of-Scope (explicit — from the 6-item friction log, only items 1 + 6 are in scope)

- **Phase-7 merge-to-main step** (friction item 2) — separate skill-flow gap, not an audit-surface discrepancy.
- **agy/Codex dispatch helper** (friction item 3) — execution-ergonomics feature, separate.
- **State-init schema friction** (friction item 4) — separate init-UX fix.
- **Rotting infra tests on baseline** (friction item 5) — overlaps the HemaSuite "2 cheap test failures" task; handled separately, not here.
- Redesigning the audit rubric / severity taxonomy itself — only the empty-section + section-scope contract is in scope, not what counts as Must vs Should.
- **Renaming the `docs/.bkit-memory.json` state file** to drop the `bkit` filename coupling — the only soft external-name coupling found, but renaming touches every script + hook + doc reference and is unrelated to the audit-gate; separate concern.
- Internalizing/replacing the intrinsic `cmux`/`agy`/`codex` dispatch CLIs or the `jsonschema`/`jq`/`pytest` tool deps — not "external like OMC" in the dependency sense; they are the multi-agent substrate and standard tooling.

## Open Questions

1. **Axis-1 fix shape (defer to Phase 4 design):** mandate bare `None` in the template, *or* make the gates exclude `- None`, *or* both (defense-in-depth)? Not pre-decided here.
2. **Axis-2 alignment (defer to design):** should preconditions.py be brought to Must+Should parity with the awk-gate, or is "Must-fix only" intentional for the `/h-mad do` precondition (a deliberately looser bar to *enter* autonomous mode)? Need the intended semantics before changing it.
3. **Axis-3 fix depth (defer to design):** full shared token-printing parser called by both the orchestrator gate and preconditions.py (closes 1+2+3 in one place), *or* the minimal patch (awk prints token + `exit 0`, leave preconditions.py independent)? Trade-off: convergence/maintainability vs blast radius. Tied to Q1+Q2.
4. **OMC deliverable, now reframed by the Axis-3 root cause** (naming only here): (a) a SKILL.md "Known interactions" subsection documenting the `DISABLE_OMC=1` / `OMC_SKIP_HOOKS=persistent-mode` workaround **and** the gate-exit-code root cause — a Phase-5 `.md` edit; (b) an *informational* upstream note to OMC (the retry guidance fires correctly on a real non-zero exit; the durable fix is h-mad-side) — a Phase-7 report sidecar, not a bug report. Confirm both still wanted given the reframe.
5. **Does fixing Axis-3 (gate stops emitting non-zero exits) make the OMC workaround unnecessary?** If the gate no longer triggers `PostToolUseFailure`, the retry-noise source is removed at the root — the `DISABLE_OMC=1` workaround may then only be needed for the *separate* autopilot Stop-hook nag (friction item 6). Worth deciding whether the workaround doc still leads with `DISABLE_OMC=1` or demotes it to "only for the Stop-hook nag".
