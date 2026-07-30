# Gap Analysis: exec-missing-report-recovery

**Phase 6a — design-vs-implementation gap analysis.**
Base 5c `b302c9e` · Head 5g `2914900` · Branch `feature/211-exec-missing-report-recovery`.

## Match rate: 100% (24/24 ACs) · Test pass: 100%

Every acceptance criterion in the spec maps to a passing, discriminating test in `h-mad/tests/test_hmad_dispatch_exec.py`. Discrimination was proven by mutation (each guard disabled → ≥1 test RED).

| AC | Requirement | Evidence |
|---|---|---|
| AC-1.1 | clean+no-log → rc 0, auto-log deleted | test passes; auto-log `rm -f` on clean arm |
| AC-1.2 | empty → auto-log retained, path on stderr | test passes; retained on empty arm |
| AC-1.3 | caller `--log` honored, not deleted | test passes; `auto_log=""` guard |
| AC-1.4 | clean stdout+rc+stderr unchanged | pre-existing `test_codex_exec_stdout_is_last_message_not_transcript` green (drove the v1.2 back-prop) |
| AC-2.1/2.2 | codex/agy empty → recovery arm | both tests pass |
| AC-2.3 | non-empty → existing path | regression guards green |
| AC-3.1 | last `^(STATUS\|VERDICT):` to stdout, inline ignored | test passes; anchored grep |
| AC-3.2 | log-recovered marker on stderr | test passes |
| AC-3.3 | `h_mad_extract_verdict.py` resolves recovered stdout | e2e — exercised live (agy-timeout recovery + extract) |
| AC-3.4 | multiple verdict lines → last | `tail -1`; mutation `tail→head` → RED |
| AC-4.1/4.2/4.3 | tree-delta count / `--cd` dir / non-repo n/a | tests pass |
| AC-5.1 | empty+exit-0 → rc 3 | test passes; mutation disabling rc-3 → 7 RED |
| AC-5.2 | crash+empty → agent rc, not 3 | test passes; live-confirmed (agy rc=1 preserved) |
| AC-5.3 | watchdog → 124, not 3 | test passes |
| AC-5.4 | clean non-empty → rc 0 | regression guard green |
| AC-6.1/6.2/6.3 | SKILL.md rc 3 + terminal-mode + playbook retained | doc diff |
| AC-7.1 | skills suite 100% | 754/0 |
| AC-7.2 | HemaSuite coupled 100% | 54/0 |
| AC-7.3 | each guard mutation-tested RED | auto-log→24, rc3→7, tail→1 RED; restored 38 green |

## Live dogfood (bonus)
The feature verified itself in-flight: during the 5e-review dispatch, `exec agy` timed out (rc=1, empty output). The new recovery arm emitted `EMPTY final message — agent exited 1` (correctly NOT rc 3), `tree delta: 5 changed`, and preserved rc=1 — exactly the designed behavior on a real transport failure.

## 6a-prime architectural review
`ASSESSMENT: READY_TO_MERGE` (no Critical/Important issues; Axis B compliant; temp-file lifecycle + rc contract confirmed).

## Gaps
None. No open must-fix or should-fix; no test-coverage gap; no invariant violation.

## Version History
- v1.0: Phase 6a gap analysis — 100% match, 100% test pass, archreview READY_TO_MERGE.
