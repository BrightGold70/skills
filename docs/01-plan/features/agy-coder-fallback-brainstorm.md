# Brainstorm: agy-coder-fallback

## Executive Summary
When Codex is unavailable, let an explicit `fallback_agent=agy` make agy the Phase-5 RED/GREEN
implementer through headless `exec agy`. Guard its production writes with an agy-native
PreToolUse TDD gate. Keep agy in its reviewer roles but flag those reviews as non-independent,
and prove the whole path on one live tracer task before relying on it.

## Problem Statement
Phase 5 has two implementer routes when Codex is out: grok (`fallback_agent=grok`) and Claude
(`claude`/`null`). agy is installed on every h-mad machine and already runs headless through
`exec agy`, but it cannot be chosen as the coder. The state value, the TDD write gate, the TDD
judge, `h_mad_assemble_tdd.py --agent` and the docs all accept only `codex|grok` / `grok|claude|null`.
An operator with Codex exhausted and no grok has only Claude, which the TDD gate exists to keep
out of production code.

## Operator decisions (2026-10-16)
- **Selection is explicit.** `fallback_agent=agy` is set by hand alongside `grok|claude|null`.
  There is no automatic codex→agy→grok chain, so a wrong choice stays visible in the state record.
- **agy keeps its reviewer roles** (5e spec review, 6a-prime, the audit leg) when it is also the
  coder. Every such review is **flagged non-independent**, in the review's own record and in the
  Phase-7 report, never silently treated as an independent pass.
- **An agy-side write gate is built**, not deferred. Grok has no write-time gate; agy will.
- **A live tracer is in scope.** One real RED+GREEN by agy via `exec agy` before the feature
  closes, measuring file writes, the `STATUS:` line and the counts. Grok's coding precision was
  left unmeasured (D4); agy's will not be.
- **Process:** full H-MAD, with TDD in Phase 5.

## Proposed Approach
Follow the grok fallback's seams, since they are the tested shape for a second implementer, and
add the two things grok lacks.

1. **State and selection.** `fallback_agent` accepts `agy`. The Claude TDD gate folds every
   `step5` record the way it does for grok: any `agy` blocks Claude's production write as
   `fallback-agy`, and `HMAD_CODEX_UNAVAILABLE` does not override it. The judge's
   `_fallback_tag`/`_fallback_fold` learn the value.
2. **Staging.** `h_mad_assemble_tdd.py --agent agy` emits a backgrounded `hmad-dispatch exec agy`
   command block with its own default timeout (grok uses 1500 s; agy's is to be measured). The
   prompt file stays agent-independent, as `test_prompt_file_is_agent_independent` already pins.
3. **The agy write gate.** A new hook speaks agy's contract (`agy-runtime.md` §"Hooks"): it reads
   the camelCase `toolCall.name`/`toolCall.args` payload, matches `write_to_file`,
   `replace_file_content` and `multi_replace_file_content`, and prints
   `{"decision": "deny", "reason": …}` for a production `.py` write during an active `step5` that
   the shared test-first judge would refuse. It reuses `h_mad_tdd_judge.py`, the single source
   both existing gates already use, so the rules cannot drift between hosts. Wired through
   `~/.gemini/config/hooks.json` under a hook name, verified against a real refusal before
   `step5:agy_tdd_hook_unverified` is lifted.
4. **Non-independent reviews.** When the implementer of the module under review is agy, the 5e
   spec review and 6a-prime records carry an explicit non-independent flag. The Phase-7 report
   surfaces it, and it never blocks.
5. **Tracer.** A small real task, staged by `--agent agy` and dispatched headless, with the
   independent re-run, revert test and mutation pass applied exactly as for Codex.

## Alternatives Considered
- **Automatic fallback chain** (codex → agy → grok → claude by CLI presence): rejected by the
  operator. The coder would change without a decision, and a missing CLI on one machine would
  silently route the same feature to different models.
- **No agy write gate, like grok:** rejected by the operator. Test-first would then rest only on
  the dispatch and the post-hoc checks.
- **Reuse `h-mad-tdd-gate.sh` or `h-mad-codex-tdd-gate.py` for agy:** rejected. Neither speaks
  agy's stdout-JSON contract, so it would run, emit nothing agy understands and block nothing
  (`agy-runtime.md` §"The TDD gate").
- **Move agy's reviewer roles to a Claude teammate when agy codes:** offered and declined. agy
  keeps reviewing, and the flag makes the lost independence visible instead.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| `run_command` can write any file and bypass the write-tool matcher | H | State it as the exact residual of the gate; the post-hoc revert test, independent re-run and mutation pass still apply. Spec decides whether `run_command` is matched by a command-shape rule or declared out of scope. |
| An agy hook that runs but emits nothing agy understands blocks nothing, silently | M | Verify against a real refusal in the tracer; keep the `agy_tdd_hook_unverified` halt until that refusal is observed. |
| A non-independent review reads as a clean pass | M | Flag recorded beside the verdict and surfaced in Phase 7. |
| agy narrates work it did not do (F-10) or reports false counts | M | Counts are re-derived by the independent re-run; tree delta and revert test are the evidence, never the `STATUS:` line. |
| agy's headless writes land outside `--cd`, e.g. its scratch dir (seen for audit reports, J30) | M | The tracer checks where files land; the prompt cites absolute paths, as 6a-prime already requires. |
| Hook wiring lives in `~/.gemini/config/hooks.json`, outside the repo, like the memory guard | M | Document the install by value, and extend the install/wiring checks to report it. |
| Editing h-mad while a run is in flight (live symlink) | M | Phase 5 code in a worktree, merged when clean. |

## Dependencies
- agy CLI ≥ 1.3.6 headless `--print` with `--dangerously-skip-permissions` (`exec agy` already uses it).
- agy's `hooks.json` PreToolUse contract (`agy-runtime.md` §"Hooks").
- `h_mad_tdd_judge.py` as the shared test-first verdict source.
- Existing grok fallback seams: `h_mad_assemble_tdd.py --agent`, `hooks/h-mad-tdd-gate.sh`,
  `h_mad_state_write.py` / state schema, SKILL.md §"Codex authors Phase 5".

## Open Questions
- Does agy's PreToolUse payload carry enough to resolve the target path and the project root
  (cwd semantics: the handler runs with cwd = the `hooks.json` directory, not the project)?
- Should the gate be global (`~/.gemini/config/hooks.json`) or per-project (`.agents/hooks.json`)?
  A global gate must stand down outside an h-mad `step5`, as the Claude gate does.
- Is `run_command` matched (command-shape heuristics) or declared the stated residual?
- What default `exec agy` timeout fits an implementer turn? Measure in the tracer, not by analogy with grok.
- Where exactly is the non-independent flag recorded: a state field next to `archreview`, a token
  field on the extracted verdict, or both? It must not change any existing verdict word, since
  consumers parse them by substring.
- When `fallback_agent=agy`, which audit legs run in Phases 3/4/5b? Proposed: `agy` + `doc-auditor`,
  unchanged from the Claude path. Grok stays available as a leg only when it is separately chosen.

## Version History
- v1.0: Initial brainstorm draft (operator decisions 2026-10-16 recorded).
