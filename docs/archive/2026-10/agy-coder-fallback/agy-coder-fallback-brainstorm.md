# Brainstorm: agy-coder-fallback

> **Slug note.** The slug predates the v1.1 decision and is kept because the state record and
> the v1.0 commit carry it. Since v1.1 agy is a **peer implementer** with the same standing as
> Codex, not a fallback.

## Executive Summary
Make agy a first-class Phase-5 RED/GREEN implementer with the same standing as Codex. Each
feature records `implementer=codex|agy` (default `codex`). If the chosen implementer is
unavailable, the other takes over automatically and the switch is recorded. agy gets the same
enforcement Codex has: a Claude-side authorship gate and an agy-native write-time TDD gate. A
live tracer task proves the path before the feature closes.

## Problem Statement
Codex is the only implementer h-mad treats as authoritative. It has an authorship gate that keeps
Claude out of production code, a write-time TDD gate on its own writes, and a staged dispatch.
grok and Claude exist only as reduced-trust fallbacks. agy is installed on every h-mad machine and
already runs headless through `exec agy`. The operator judges it about as capable as Codex or more,
yet h-mad cannot use it to write code. Nothing in the state record, the gates, the TDD judge,
`h_mad_assemble_tdd.py --agent` or the docs accepts it as an implementer.

## Operator decisions (2026-10-16)
- **agy has the same standing as Codex** (v1.1). It is a peer implementer, not a fallback, so it
  carries no reduced-trust caveat beyond what the tracer measures.
- **Selection is per feature.** `implementer=codex|agy` is recorded on the feature, defaulting to
  `codex`. When the chosen implementer is unavailable, the other takes over automatically and the
  switch is written to state, so it is visible and auditable. The existing `fallback_agent`
  (`grok|claude|null`) applies only when **both** peers are unavailable.
- **agy keeps its reviewer roles** (5e spec review, 6a-prime, the audit leg) even when it wrote the
  code, including when Codex is available. Every review of agy-written code by agy is **flagged
  non-independent** in its record and in the Phase-7 report. It never blocks.
- **An agy-side write gate is built**, at parity with `h-mad-codex-tdd-gate.py`.
- **A live tracer is in scope.** One real RED+GREEN by agy through `exec agy` before the feature
  closes, measuring file writes, the `STATUS:` line and the counts.
- **Process:** full H-MAD, with TDD in Phase 5.

## Proposed Approach
Generalise every Codex-specific Phase-5 seam to "the implementer" (codex or agy), so the two
paths share one code path rather than becoming two parallel ones that drift.

1. **Implementer selection and availability.**
   - State gains `implementer` (`codex|agy`, absent = `codex`) and a per-agent status:
     `agy_status` beside `codex_status` (`available|unavailable|exhausted`).
   - Resolution: use the chosen implementer if available, else the other peer (record the
     switch), else `fallback_agent`.
2. **Authorship gate (Claude side).** `hooks/h-mad-tdd-gate.sh` refuses Claude's production write
   whenever the resolved implementer is available. Codex today yields `codex-authorship`; agy
   adds `agy-authorship`. Folding stays chain-wide across every `step5` record, as it is today.
   The judge (`h_mad_tdd_judge.py`) learns the field once, as the single source both gates read.
3. **Staging.** `h_mad_assemble_tdd.py --agent agy` emits a backgrounded `hmad-dispatch exec agy`
   implementer command with an agy-specific default timeout (measured in the tracer). Its
   verdict path is the same as Codex's: `STATUS:` extraction, independent scoped re-run, revert
   test, mutation pass. The prompt file stays agent-independent.
   `references/codex-implementer-prompt.md` either becomes implementer-neutral or gains a
   reviewed agy variant.
4. **agy write gate, at parity with Codex's.**
   - A new hook speaks agy's contract (`agy-runtime.md` §"Hooks"): it reads the camelCase
     `toolCall.name`/`toolCall.args` payload, matches `write_to_file`, `replace_file_content` and
     `multi_replace_file_content`, and prints `{"decision": "deny", "reason": …}` when the shared
     test-first judge refuses a production `.py` write during an active `step5`.
   - It is wired in `hooks.json` under a hook name and verified against a real refusal before
     `step5:agy_tdd_hook_unverified` is lifted.
5. **Non-independent review flag.** When the 5e spec review or 6a-prime reviewer is the same agent
   as the module's implementer, the record carries the flag and the Phase-7 report surfaces it. No
   existing verdict word changes.
6. **Tracer.** A small real task staged with `--agent agy`, dispatched headless, then checked with
   the independent re-run, revert test and mutation pass, exactly as for Codex.

## Alternatives Considered
- **agy as a grok-style fallback (`fallback_agent=agy`, v1.0):** superseded by the operator. It
  ranks agy below Codex and gives it no write-time gate, which does not match its capability.
- **Codex first, agy second, with no per-feature choice:** declined. agy would never be chosen
  on purpose.
- **Per-task implementer in the impl-plan:** declined as scope. Per-feature selection covers the
  need; per-task can come later on the same field.
- **Codex reviews agy's code when available (role swap):** offered and declined. agy keeps
  reviewing, and the flag makes the lost independence visible.
- **Reuse `h-mad-tdd-gate.sh` or `h-mad-codex-tdd-gate.py` as the agy gate:** rejected. Neither
  speaks agy's stdout-JSON contract (`agy-runtime.md` §"The TDD gate").
- **Automatic chain by CLI presence alone:** rejected. Selection is recorded per feature, and an
  automatic switch is written to state, never inferred silently.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| `run_command` can write any file and bypass the write-tool matcher | H | State it as the gate's exact residual, the same class Codex's shell has. The revert test, independent re-run and mutation pass still apply. Spec decides between a command-shape rule and a stated residual. |
| A hook that runs but emits nothing agy understands blocks nothing, silently | M | Verify against a real refusal in the tracer; keep the `agy_tdd_hook_unverified` halt until it is observed. |
| Generalising "codex" across gates breaks an existing Codex path | M | One shared resolution function, existing Codex tests kept green, and full suite per task. Every `codex-authorship` and `fallback-grok` behaviour stays byte-compatible. |
| A non-independent review reads as a clean pass | M | Flag recorded beside the verdict and surfaced in Phase 7. |
| agy narrates work it did not do (F-10) or reports false counts | M | The tree delta, independent re-run and revert test are the evidence, never the `STATUS:` line. |
| agy's headless writes land outside `--cd`, e.g. its scratch dir (seen for audit reports, J30) | M | The tracer checks where files land; the prompt cites absolute paths. |
| An automatic peer switch hides a misconfigured agent | L | The switch is written to state and printed on the dispatch; the operator sees which agent ran. |
| Hook wiring lives outside the repo (`~/.gemini/config/hooks.json`) | M | Document it by value; the install and wiring checks report it. |
| Editing h-mad while a run is in flight (live symlink) | M | Phase 5 code in a worktree, merged when clean. |

## Dependencies
- agy CLI ≥ 1.3.6 headless `--print` with `--dangerously-skip-permissions` (`exec agy` already uses it).
- agy's `hooks.json` PreToolUse contract (`agy-runtime.md` §"Hooks").
- `h_mad_tdd_judge.py` as the shared test-first verdict source.
- Existing seams: `hooks/h-mad-tdd-gate.sh`, `hooks/h-mad-codex-tdd-gate.py`,
  `h_mad_assemble_tdd.py --agent`, `h_mad_state_write.py` and the state schema, SKILL.md
  §"Codex authors Phase 5", `references/codex-implementer-prompt.md`.

## Open Questions
- Does agy's PreToolUse payload carry enough to resolve the target path and the project root? The
  handler's cwd is the `hooks.json` directory, not the project.
- Should the agy gate be global (`~/.gemini/config/hooks.json`) or per-project (`.agents/hooks.json`)?
  A global gate must stand down outside an h-mad `step5`.
- Is `run_command` matched by command shape, or declared the stated residual (parity with Codex's shell)?
- What default `exec agy` timeout fits an implementer turn? Measure in the tracer.
- How is agy's availability detected: CLI on PATH plus `agy_status`, or a cheap liveness probe?
  Codex uses CLI-on-PATH plus the declaration.
- Should `implementer` live on the feature record only, or also as a project default in
  `.h-mad/` so a repo can prefer agy without setting every feature?
- Where is the non-independent flag recorded: a state field beside `archreview`, a field on the
  extracted verdict, or both? No existing verdict word may change.
- Audit legs in Phases 3/4/5b are unchanged by this feature (codex + agy when Codex is
  available). Confirm in spec.

## Version History
- v1.1: Operator correction 2026-10-16: agy is a peer implementer with Codex's standing, not a
  fallback. Per-feature `implementer=codex|agy` with an automatic, recorded peer switch; Claude
  authorship gate and an agy write gate at Codex parity; agy keeps reviewing, flagged
  non-independent, even when Codex is available. `fallback_agent` now applies only when both
  peers are out.
- v1.0: Initial brainstorm draft (operator decisions 2026-10-16 recorded).
