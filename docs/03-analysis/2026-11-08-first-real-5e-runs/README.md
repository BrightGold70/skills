# First real runs of the 5e agy review and `--full-suite` — 2026-11-08

Closes handoff item #27. Both paths had never run against real tools. They were exercised by replaying a task that had already landed, so nothing live was touched and the expected answer was known in advance.

**Target:** gate-non-py-production-files Task 2 (`doc-data-definition`), landed at `2a3cc11d`. It ran in a throwaway detached worktree at that commit, with base `a17cd4c8^` (the commit before its RED).

## Run 1 — `h_mad_assemble_tdd.py --phase review` → `hmad-dispatch exec agy` (agy 1.5.3)

- Staging: `ASSEMBLE-TDD: PASS … 15454B phase=review task=Task 2 shape=new-behaviour`, with `--base-ref 'a17cd4c8^'` and `--codex-report`.
- `review_fence` worked: the BEGIN/END TASK and BEGIN/END REPORT blocks carry fence id `2f789700…` (see `agy-review-task2.prompt.txt`).
- Dispatch: `agy exec rc=0`. `h_mad_extract_verdict.py --key VERDICT` → **`VERDICT: COMPLIANT`**.
- The review was substantive: the log shows 12 `read_file`, 9 `run_command`, 1 `grep_search` and 1 `view_file` calls. agy re-ran the scoped tests (66 passed) and the anchor checks (7/7, 11/11). The worktree was left clean.
- `argument_not_printable` did not fire. No argv carried a non-printable character, so it is exercised only in the pass direction.

The implementer report is a **replay stand-in**: the original GREEN ran inline and left none. It is labelled as such and built from the commit message plus a scoped re-run.

Staging friction:
- `--report-file` is refused for review (`review_option_not_applicable`), which is by design.
- `--codex-report` is required for review (`codex_report_required`), but `--help` does not say so.

## Run 2 — `h_mad_branch_evidence.py --full-suite` after a code diff

`EVIDENCE: sha=2a3cc11d1 … ahead=2 dirty=0`, `TESTS: PASS files=9 passed=762`, `ANCHORS_OK 96/96`, 7 specs `ALL_CAUGHT`, **`FULL-SUITE: PASS passed=8372`**, `TREE: UNCHANGED`, `EVIDENCE-VERDICT: COMPLETE`. Full output: `branch-evidence-full-suite.txt`.

8372 is the suite at `2a3cc11d`, not at today's `main`, which reads 8958.
