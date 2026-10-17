# agy-coder-fallback — 5d Task 8 (gate) record

## D5d-4 · `git status` corpus-control oracle was wrong; the gates agree (2026-10-17)
- Codex's first run: `2 failed, 49 passed` (`DONE_WITH_CONCERNS`, `acf_5d_task8.report.md`). Both
  failing cells — `test_shell_differential[git-status-absent]` and `[git-status-unreadable]` —
  show **both gates denying**; the cells failed only on the test's extra absolute
  "corpus control" (`codex.decision == expected`), which listed `git status` as an allow.
- `git` is not in `READ_ONLY_COMMANDS` (`h_mad_target_identity.py`), a pre-existing Codex-gate
  policy this feature does not change; refusing it unless the operator lists it is correct for
  both gates. Kinds: the Codex deny carries none, so the plan's "same kind wherever the Codex deny
  carries one" is satisfied.
- **Not a Task 6/7 or design finding.** Orchestrator corrected the oracle only: `git status`
  joins `rm -rf build` (allow only when the allowance file lists it). No gate edit.
- Result: `51 passed`.
- Positive control (the corpus must be able to fail): the agy gate's
  `if not _safe_shell_command(...)` forced to `if False:` → `10 failed, 41 passed`; restored → `51 passed`.
