# Brainstorm: tdd-gate-fail-opens

## Executive Summary
Close the five TDD-gate fail-opens (D1–D5) that the codex-tdd-gate-defects 6a verifier reproduced after that feature merged. The approach: both gates resolve the target before any exemption check, both case-fold the `.py` suffix, the Codex gate trims patch headers the way Codex's own parser does, the symlinked-root spelling is canonicalised, and the judge bounds its post-kill wait.

## Problem Statement
The merged Claude gate (`h-mad/hooks/h-mad-tdd-gate.sh`) and Codex gate (`h-mad/hooks/h-mad-codex-tdd-gate.py`) allow a governed production write during `step5`, with no measured failing test, when the target is spelled unusually. Every repro is in `docs/archive/2026-09/codex-tdd-gate-defects/codex-tdd-gate-defects.gap.v1.md` §"Defects (reproduced)":
- **D1 (HIGH, both gates).** On case-insensitive APFS, `src/prod.PY` is `src/prod.py`, but both gates compare the suffix case-sensitively and allow the write. Codex's `apply_patch` then writes `prod.py`.
- **D2 (HIGH, Codex gate).** `PATCH_TARGET` keeps a trailing space or `\r` in the header path. The suffix becomes `.py ` or `.py\r`, so the file is not seen as production. Codex trims the header and writes the real file.
- **D3 (MED, Claude gate).** With a symlinked `CLAUDE_PROJECT_DIR` spelling under `tests/`, `ROOT_ABS` is physical but the target is only `normpath`ed. So `IN_ROOT=no`, and `_dir_match` exempts the write on the root's ancestry. This is the §D9 fix left incomplete.
- **D4 (MED, both gates).** A `tests/` symlink to a production directory is exempted lexically by the Claude gate but governed by the Codex gate, which resolves first. The two gates disagree about the same write.
- **D5 (LOW, judge).** After a kill, `_run_bounded` calls `communicate()` a second time with no timeout. A setsid grandchild holding the pipe keeps the judge waiting past its 40 s budget.

D1, D2, D4 and D5 were inherited from the pre-feature gates. D3 is a gap in the merged fix.

## Proposed Approach
Operator decisions (2026-09-29): scope **D1–D5 all**; D4 **resolve first** in both gates; D1 **case-fold** the suffix.
- **One target-normalisation rule, applied identically by both gates:**
  - realpath the target, and canonicalise the root (physical, as `ROOT_ABS` already is);
  - decide inside-root on the resolved pair;
  - run the directory and basename exemptions on the resolved target;
  - treat any-case `.py` as production.
  - This closes D1, D3 and D4 with one rule rather than three patches.
- **Codex gate header parsing (D2):** match Codex's own `apply_patch` grammar. Strip trailing whitespace and `\r` from each `*** Add/Update/Delete File:` / `Move to:` path, and refuse (judge-error) any header path that still carries a control byte.
- **Judge (D5):** give the post-kill `communicate()` a bounded timeout, then close the pipes, so the judge returns inside its budget. Report the reap failure rather than waiting.
- Tests: every repro in the gap report becomes a pinned test on both gates. Add a shared differential (both gates, same spellings, same decision) so D4's class cannot come back. Mutation rows cover each new guard.

## Alternatives Considered
- **Lexical exemption in both gates (D4)**: rejected. A `tests/` symlink into production escapes both gates.
- **Filesystem-aware case folding (D1)**: rejected. It needs a per-target filesystem probe, and case-folding everywhere is fail-closed and simpler. A case-sensitive filesystem only gains refusals for files literally named `*.PY`.
- **Patching each defect at its site**: rejected. D1, D3 and D4 are one class (the target's *spelling* decides the verdict instead of its *identity*), so fixing them one member at a time is how the next member arrives.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| realpath of a not-yet-existing target (a new file) | H | Resolve the deepest existing ancestor, then append the remainder, and test new-file targets. |
| Resolving first changes verdicts pinned by the merged feature's tests and its DD-7 differential | M | Run the committed differential probes; any changed cell is a stated, reviewed delta. |
| Case-fold breaks a legitimate `*.PY` data file | L | Refuse only; the operator can rename the file. State it as a residual. |
| Codex's `apply_patch` trims differently than assumed | M | Pin the trim against the real codex 0.157.x parser behaviour, as the verifier did. |

## Dependencies
Merged `codex-tdd-gate-defects` (main `8ef6009f`), the shared judge `h-mad/scripts/h_mad_tdd_judge.py`, and grok-codex-fallback's fold (`52a78ca8`). Codex must be available for Phase 5 authorship.

## Open Questions
- Should an unresolvable symlink (a dangling link, or a loop) as the target be refused (judge-error) or treated as not-a-file? Proposed: refuse.
- Should D5's reap failure surface as a distinct DENY kind (for example `judge-timeout`), or fold into `timeout`?

## Version History
- v1.0: Initial brainstorm draft (2026-09-29), from the codex-tdd-gate-defects gap report v1 and three operator decisions.
