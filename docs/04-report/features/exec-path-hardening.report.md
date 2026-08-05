# Report: exec-path-hardening

**Branch:** `feature/213-exec-path-hardening` · **Base:** `c9ce526` · **Suite:** 1060 passed
**Audit cycles:** plan 6 · design 5 · impl-plan 3 · **Iterate cycles:** 1 (Phase 6b)
**6a-prime:** `READY_TO_MERGE` (after one `WITH_FIXES`) · **Match rate:** 100% (24/24)

## Executive Summary

`hmad-dispatch exec` — the default transport for one-shot 5d/5e and every audit dispatch — gained
mobile-visible worktree checkpoints, a liveness heartbeat, an exit notification, and a `--log`
append contract, under a mutation-verified invariant that no surface may perturb stdout or `rc`.

## What shipped

`hmad-dispatch exec` had no observability surface at all — no pane, no task row, no durable
trace — so a 900-second Phase-5 dispatch was indistinguishable from a dead one to an operator
away from the desk. It now stamps start / heartbeat / exit checkpoints onto the Orca worktree
card (the only genuinely mobile-visible channel), fires a desktop notification at exit, and
appends rather than truncates a caller-supplied `--log`.

Three helpers plus one restructure in `h-mad/scripts/hmad-dispatch.sh`:

| Helper | Role |
|---|---|
| `_exec_comment_compose` | Places the `h-mad: …⟦/h-mad⟧` span by **content**, not prefix |
| `_exec_wt_target` | One `worktree ps` payload → selector *and* current comment |
| `_exec_stamp` | Sole writer: substrate-gated, bounded, stdin-null, returns 0 always |
| `_run_with_timeout` → `_exec_run` | Optional deadline; explicit `--heartbeat` context group |

`HMAD_EXEC_HEARTBEAT_SEC` (default 120, `0` disables) is read only by `_cmd_exec`.

## The defects the process caught

**Unbounded comment growth (plan cycle 4).** The composition rule was prefix-based. On a human
comment, heartbeat 1 appends → the string no longer *starts with* the stamp → every later
heartbeat appends again, once per 120 s, on the field the feature exists to protect.

**The test that would have hidden it (same cycle).** `HMAD_STUB_ORCA_WT_PS_STDOUT` is static, so
every tick re-reads the same base comment and appends once — green suite, shipped defect. Forced
a stateful stub and an N≥3 idempotency assertion, because N=2 cannot discriminate.

**Infinite recursion (design cycle 4).** `_exec_run` owns the heartbeat hook and `_exec_stamp`
calls `_exec_run`, so any interval shorter than the stamp timeout recursed unbounded — reachable
by construction from any test using a 1 s interval. The heartbeat became opt-in.

**Shared-offset stdin corruption (design cycle 1).** A stamp inheriting the dispatch's stdin
shares the prompt file's *offset* with a concurrently-reading codex. Probe: stamp consumed
`AAAABBBB`, agent received `CCCCDDDD-AGENT-TAIL` — prompt silently truncated.

**Wrong-worktree clobber (design cycle 1).** `/x/repo` is a string prefix of `/x/repo-other`, so
a bare prefix match stamped over a worktree the run never touched.

**A hardcoded heartbeat (6a-prime).** `beat` emitted `running · 0m` always. It passed a
1055-green suite, a clean 5/5 mutation sweep and five wire-scoped reverts, because AC-2.2
asserted `values == sorted(values)` and `[0, 0, 0]` is sorted. Only the review that reasons
*outside* the pinned contract caught it.

## What was wrong in my own work

Recorded because the pattern matters more than the fixes:

- **My RED counts were self-inconsistent** (claimed 32, listed 31) and included tasks whose
  tests necessarily pass. Codex reported it rather than bending the tests.
- **Codex reported `BLOCKED` three times, correctly each time** — two test-harness defects it had
  written itself in RED, and one production-scope violation it refused to commit. Verifying each
  claim before accepting it was cheap and it was right every time.
- **Two spec amendments were forced by the plan audit.** The NFR bound was incompatible with
  read-before-write; AC-6.3's unconditional `active` fallback predated the no-clobber rule and
  would have overwritten an unread comment on the wrong worktree.
- **I wrote two vacuous tests in Phase 6b.** Env knobs that did not exist, then a missing
  `state=` that made the write path unreachable — it passed with *both* guard layers mutated
  out. Only the mutation check exposed either.

## Verification

- Suite **1060 passed**, `bash -n` clean, both symlink-coupled suites.
- `MUTATION: ALL_CAUGHT mutations=5 caught=5 survived=0 refused=0`.
- All five wires verified by wire-scoped revert (call site out → pin fails → restore → passes).
- Gap analysis: `docs/03-analysis/exec-path-hardening.analysis.md`.

## Carry

- ~~**Live e2e not run.**~~ **DONE 2026-08-06 — and it found two production defects the whole
  gate stack missed.** The real card had grown to **513 spans / 38,329 bytes**.
  (1) `prefix="${current%$rest}"` left `$rest` unquoted, so bash glob-matched it rather than
  stripping a literal suffix; production verdicts embed the agent's markdown (`[x](y)`, `**x**`),
  the strip failed, and every stamp emitted the comment **twice** — reproduced exactly by feeding
  the real card back through the composer (513 → 1026). Every unit test used short glob-free
  strings. (2) `verdict` was the agent's entire final message, making the card a transcript sink
  and — since that text can contain `⟦/h-mad⟧` — forging the span boundary the composer keys on.
  Both fixed in `63fca45`, mutation-verified. Re-run live: start → heartbeat (elapsed advancing)
  → exit with agent/rc/token, exactly one span, operator's handoff checkpoint preserved
  byte-for-byte, card bounded at 183 bytes.
- **6a-prime ran via `exec agy`, not a pane**, deviating from SKILL.md's pane preflight. Recording
  `SKIPPED_NO_PANE` would have been false — a real review ran and found a real defect. The
  mandate is arguably now mis-specified for the exec-default era.
- **The codex/agy pane pins are stale** (`PREFLIGHT: FAIL stale=codex,agy`) and were never
  repaired; the whole feature dispatched headless, which is the transport it is about.
- **`docs/skill-monitoring.md` stops at J18** (2026-07-23). J19–J23 shipped through handoffs and
  were never filed, so the registry no longer tracks exec defects. Deliberately out of scope
  here; worth its own pass.

## Version History

- v1.0: Phase 7 closure report.
- v1.1: Live e2e carry closed. Two production defects found and fixed (`63fca45`); the report's
  own prediction that only a live run could settle this held.
