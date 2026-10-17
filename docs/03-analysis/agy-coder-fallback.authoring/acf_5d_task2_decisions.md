# agy-coder-fallback — 5d Task 2 decisions

## D5d-3 · RED fixture put the stub bin inside a ':'-bearing root (2026-10-17)
- **Found by:** Codex GREEN (`STATUS: BLOCKED`, `acf_5d_task2_green.report.md`); reproduced outside
  the sandbox: 6 verb tests failed (`switch-none`, `peer-switch`, phase, record-once,
  record-failed, switch-none-writes-nothing).
- **Defect (test, not production):** `_verb` built `controlled-bin` under `root " + HOSTILE"`;
  HOSTILE carries `:`, which splits a POSIX PATH entry, so `shutil.which` (FR-2's contract) can
  never see the stubs. Codex correctly refused to bend production discovery.
- **Fix (orchestrator, one line):** `bindir = root.parent / "controlled-bin"`; the hostile
  `--root`/`--feature` payload and every assertion are unchanged.
- **Gates (outside sandbox):** Task 2 file `47 passed`; revert probe (HEAD `h_mad_tdd_judge.py`)
  `47 failed`; `ANCHORS_OK` 9 specs 108/108; `tdd_judge_implementer.json` ALL_CAUGHT 4/4 (symbols
  set); re-anchored `tdd_gate_fallback_agent.json` (`g3-reads-another-feature`, same intent/test)
  ALL_CAUGHT 12/12; full suite `6205 passed` (6158 + 47). Verb lines = design FR-2 table.
