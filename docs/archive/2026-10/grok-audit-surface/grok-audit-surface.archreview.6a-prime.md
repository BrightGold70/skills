# Architectural Review — `grok-audit-surface` (`f6820752..c018f177`)

## Summary of Scope Reviewed

Reviewed the Phase 5 implementation for feature `grok-audit-surface` across git range `f6820752..c018f177` against the audited design (`v1.15`), project invariants (`/Users/kimhawk/orca/skills/.h-mad/invariants.md`), and base invariants (`/Users/kimhawk/orca/skills/h-mad/invariants.base.md`).

### Inspected Files (by Absolute Worktree Path)
- **Invariants & Manifest**:
  - `/Users/kimhawk/orca/skills/.h-mad/invariants.md`
  - `/Users/kimhawk/orca/skills/h-mad/invariants.base.md`
  - `/Users/kimhawk/orca/skills/h-mad/SKILL.md`
- **Probe & Calibration Policy**:
  - `/Users/kimhawk/orca/skills/docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  - `/Users/kimhawk/orca/skills/docs/03-analysis/probes/grok-audit-surface/exclusions.txt`
- **Production Runtime & Hooks**:
  - `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_tool_calls.py`
  - `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_grok_containment.py`
  - `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_assemble_audit.py`
  - `/Users/kimhawk/orca/skills/h-mad/scripts/hmad-dispatch.sh`
  - `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-agy-tdd-gate.py`
- **Documentation & Measurement Artifacts**:
  - `/Users/kimhawk/orca/skills/docs/03-analysis/grok-audit-surface.s0c-live-roundtrip.md`
  - `/Users/kimhawk/orca/skills/docs/03-analysis/grok-audit-surface.measurement.md`
  - `/Users/kimhawk/orca/skills/h-mad/references/agent-substrate.md`
  - `/Users/kimhawk/orca/skills/h-mad/references/grok-runtime.md`
- **Test Modules, Fixtures & Mutation Spec**:
  - `/Users/kimhawk/orca/skills/h-mad/tests/grokauditfixtures.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_probe.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_smoke.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_gate_pins.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_wrapper.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_docs.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_containment.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_path_scope.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_assembler_pin.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_toolscan_pattern.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_fallback_docs.py`
  - `/Users/kimhawk/orca/skills/h-mad/tests/mutation-specs/grok_audit_surface.json`

---

## 1. Cross-Module Coupling

- **Probe-to-Runtime Boundary (D1)**: `/Users/kimhawk/orca/skills/docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (lines 25–37) prepends `Path(__file__).resolve().parents[4] / "h-mad" / "scripts"` to `sys.path` and imports only the Python 3 standard library plus the five declared `h-mad/scripts/` modules:
  1. `h_mad_audit_gate as _gate` (module-qualified calls to `_gate.classify`, `_gate.BLOCKING_SECTIONS`, `_gate._bullet_groups`, `_gate._collapses`, `_gate._flat_findings`, `_gate._bullet_remainder`, `_gate._payload`, `_gate._is_none_sentinel`)
  2. `h_mad_audit_cycle as _cycle` (`_cycle._gate_token`)
  3. `h_mad_audit_origins` (`ORIGINS`)
  4. `h_mad_review_evidence` (`_GROK_TYPES`)
  5. `h_mad_tool_calls` (`scan_log`)
- **Containment & Tool-Scan Boundaries (D18–D21)**:
  - `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_tool_calls.py` (lines 1–12) imports only Python stdlib modules (`argparse`, `json`, `os`, `posixpath`, `re`, `sys`, ` pathlib.Path`, `urllib.parse.quote`).
  - `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_grok_containment.py` (lines 1–21) imports only Python stdlib modules plus sibling modules in `/Users/kimhawk/orca/skills/h-mad/scripts/` (`h_mad_assemble_audit.PATH_SCOPE_CLAUSE`, `h_mad_review_evidence._GROK_TYPES`, `h_mad_tool_calls.named_paths`, `h_mad_tool_calls.scan_log`).
  - No `h-mad/` runtime script imports from `docs/03-analysis/`, preserving skill self-containment.
- **Pinned Production Functions**: `exit_check`, `round_check`, `combine`, and `scan_grok` are unedited and pinned by `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_gate_pins.py` (lines 1–112).

---

## 2. Pattern Compliance & Single-Source Authority

- **Single-Source Verdict & Classification Contract (D1, D10, D12, D13)**:
  - `grok_audit_probe.py` never re-derives a verdict computed by the wrapper or the audit gate. `smoke` runs `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py` via subprocess and parses its first line with `_cycle._gate_token` (lines 1152–1160), compares vocabulary sets between `h_mad_review_evidence._GROK_TYPES` and `hmad-dispatch.sh`'s `_GROK_TYPES_RE` (lines 1117–1133), and reads the recorded `AUDITCYCLE:` and `Effort:` blocks from `auditcycle.txt`.
  - `extract_report` (lines 1296–1311) walks sections using `_gate.BLOCKING_SECTIONS`, `_gate._bullet_groups`, `_gate._collapses`, `_gate._flat_findings`, `_gate._bullet_remainder`, `_gate._payload`, and `_gate._is_none_sentinel`, and compares `len(must)` / `len(should)` directly against `_gate.classify(text)`'s `must_count` and `should_count`.
  - `score` re-runs `h_mad_tool_calls.scan_log` on every recorded pass log and refuses if any grok pass (standing or non-standing) has `scan["word"] == "UNREADABLE"` or `scan["checkout"] > 0` (`out_of_root:d<k>.v<N>`, lines 1423–1445), while publishing observational `CONTAINMENT:` lines for every standing pass (lines 1775–1800).
- **Opt-In Path-Scope Clause (D21)**:
  - `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_assemble_audit.py` defines `PATH_SCOPE_CLAUSE` (line 222) and inserts it after `CONTRACT_SEPARATOR` only when `--path-scope` (`path_scope=True`) is supplied (lines 684–686, 738), keeping switch-off output byte-identical to revision `7e10f543237267643824c8d452b0415b10103d33`.
  - `/Users/kimhawk/orca/skills/h-mad/scripts/hmad-dispatch.sh` defines the matching `_HMAD_PATH_SCOPE_CLAUSE` (line 3582), passes `--path-scope` to every pass when `--pass-root` is given (lines 3845–3848), records `here=$_here` in `<stem>.here.txt` (lines 3849–3852), and verifies the clause appears as a full line in each assembled prompt before launching any agent (lines 3893–3906).
- **S4 Routing Update (D15)**:
  - `/Users/kimhawk/orca/skills/h-mad/SKILL.md` (lines 588–622, 650), `/Users/kimhawk/orca/skills/h-mad/references/grok-runtime.md` (lines 119–167), and `/Users/kimhawk/orca/skills/docs/03-analysis/grok-audit-surface.measurement.md` (lines 1–430) consistently record `SEEDSCORE: PASS calibration=ab2c85dc2e25fa5868621c1d3056f5cc087d2e78 score=05cc39359ef24d6ec3ba6c3f348bf757e27dd9ca` (`grok` recall `8/27`, fabrication `0/22` vs `agy` recall `6/27`, fabrication `0/14`), replacing the `unmeasured` warning while preserving `--surfaces agy,grok` as the teammate fallback leg when `codex` is unavailable.

---

## 3. Invariant Compliance

Checked against `/Users/kimhawk/orca/skills/.h-mad/invariants.md` and `/Users/kimhawk/orca/skills/h-mad/invariants.base.md`:

- **Audit-Gate Signal Discipline**:
  - `/Users/kimhawk/orca/skills/docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` exits `0` on all determined verdicts across all nine modes (`LEDGER: OK`, `ROOT: READY`, `RECORD: OK`, `COMMIT: OK`, `SMOKE: PASS|FAIL`, `FINDINGS: WRITTEN`, `SEEDSCORE: PASS|MISS|INCONCLUSIVE`, `MAINLEAK: CLEAN`) and exits `2` only on cannot-judge/refusal tokens (`UNREADABLE` / `REFUSED`, plus `PROBE: UNREADABLE reason=unknown_mode`), with no counts on cannot-judge lines and `_TokenArgumentParser(add_help=False, allow_abbrev=False)` routing usage errors through the mode's refusal token.
  - `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_tool_calls.py` exits `0` on `TOOLSCAN: CLEAN|OUT_OF_ROOT|UNMEASURED` and exits `2` only on `TOOLSCAN: UNREADABLE reason=<r>`.
  - `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_grok_containment.py` exits `0` on all determined verdicts (`QUARANTINE: VERIFIED|REFUSED` except `internal:*`, `REQUIRE: OK|STOP` except `internal:*`, `PLANT: READY`, `GROK-CANARY: PASS|REFUSED`, `ASSEMBLER-READING: sha=...`, `ASSEMBLER: PINNED|UNPINNED|NO_CLAUSE` except `internal:*`) and exits `2` on `internal:<ExcType>` / `UsageError`.
- **No New External Dependencies**:
  - All new and modified Python scripts use Python 3 stdlib only. Shell changes in `/Users/kimhawk/orca/skills/h-mad/scripts/hmad-dispatch.sh` use bash builtins, POSIX utilities, and `jq` (with explicit `nojq`/`jqfail` handling).
- **Portable Time Bounds**:
  - `_cmd_grok_canary` in `/Users/kimhawk/orca/skills/h-mad/scripts/hmad-dispatch.sh` (lines 3525–3579) delegates execution to `_cmd_exec`, which uses the portable `_exec_run` process-group watchdog; no `timeout` or `gtimeout` binary is invoked.
- **Hook Input Hygiene & Fail-Open Contract**:
  - `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-agy-tdd-gate.py` (line 19) adds `"read_file"` to `CLASS_A` without altering the hook's `sys.stdin` JSON parsing or fail-open exception handling.
- **Skill Self-Containment & Manifest Integrity**:
  - `/Users/kimhawk/orca/skills/h-mad/SKILL.md` YAML frontmatter (`name: h-mad`, `description: ...`) is intact and unmodified.

---

## 4. Dead Code & Unused Imports

- Inspected imports, helper functions, and constants across `/Users/kimhawk/orca/skills/docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`, `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_tool_calls.py`, `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_grok_containment.py`, `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_assemble_audit.py`, and `/Users/kimhawk/orca/skills/h-mad/scripts/hmad-dispatch.sh`.
- Every symbol, CLI subcommand (`check-ledger`, `build-root`, `record-cycle`, `commit-data`, `smoke`, `extract`, `score`, `rescore`, `main-leak`; `scan`; `quarantine`, `require`, `canary-plant`, `canary-judge`, `assembler-read`, `assembler-check`; `grok-canary`), and error class is reachable, wired into CLI dispatch, and exercised by unit/integration tests and mutation anchors. No dead code, orphaned helpers, or unused imports were found.

---

## 5. Integration Test & Mutation Coverage

- **Test Suite Breadth**:
  - Nine dedicated feature test modules (`/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_probe.py`, `test_grok_audit_surface_smoke.py`, `test_grok_audit_surface_gate_pins.py`, `test_grok_audit_surface_wrapper.py`, `test_grok_audit_surface_docs.py`, `test_grok_audit_surface_containment.py`, `test_grok_audit_surface_path_scope.py`, `test_grok_audit_surface_assembler_pin.py`, `test_grok_audit_surface_toolscan_pattern.py`) plus `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_fallback_docs.py` and `/Users/kimhawk/orca/skills/h-mad/tests/grokauditfixtures.py` exercise end-to-end CLI and function paths with hostile payloads (`HMAD_STUB_HOSTILE="all"`), real git repositories, symlink escape attempts, and subprocess stubs.
- **Mutation Coverage**:
  - `/Users/kimhawk/orca/skills/h-mad/tests/mutation-specs/grok_audit_surface.json` defines 445 targeted mutations across `grok_audit_probe.py`, `h_mad_tool_calls.py`, `h_mad_grok_containment.py`, `h_mad_assemble_audit.py`, `hmad-dispatch.sh`, `h-mad-agy-tdd-gate.py`, and documentation files, with all 445 mutations killed and all 7,497 tests passing.

---

## 6. Security, Containment & Safety

- **Sandbox & Environment Scrubbing (D16)**:
  - In `/Users/kimhawk/orca/skills/h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec`, lines 2847–2938, 3091–3210), `exec grok` defaults to `--sandbox strict`, rejects weaker or unknown profiles unless `--allow-weaker-sandbox` is explicitly passed, records `GROK-PROFILE: profile=<p> origin=default|override` to `<log>.profile`, and scrubs `GROK_SANDBOX` along with all `CLAUDE*` variables using NUL-delimited `env -0`.
  - Prompt files and `TMPDIR` are staged inside `<top>/.h-mad/tmp/hmad_exec_grok.XXXXXX` (when inside a git worktree after verifying `--cd` is top-level and `.h-mad/tmp/` is git-ignored, cleaned up via `EXIT` trap) or `<cd>/.tmp` (for non-git export roots), never in system temp (`/tmp` or `/var/folders`).
- **Per-Pass Export Roots & Halt Gate (D17, D19)**:
  - `_cmd_audit_cycle` (lines 3705–3798, 3882–3916) validates that `--pass-root` count equals `--passes`, each root is absolute, colon-free, an existing directory, physically distinct (`cd -P`), non-nesting in either direction, and `pass_root[1] == project_root`.
  - Per-pass reports are isolated in `<pass_root[i]>/.hmad-report/` (`chmod 700`), and `--halt-file` is checked before any agent launch (`REQUIRE: STOP reason=halt_file`).
  - `h_mad_grok_containment.py require` recovers `--halt-file` from raw `argv` even on `UsageError` or internal exceptions so `--verb toolscan` fails closed by appending `reason` with `O_WRONLY | O_CREAT | O_APPEND`.
- **Canary & Quarantine Safety (D18, D20)**:
  - `canary-plant` uses `O_CREAT | O_EXCL | O_WRONLY` (`0o600`) for `sentinel.txt`, `plant.txt`, and `prompt.txt`, storing only the SHA-256 hash of the 128-bit random token in `plant.txt`. `canary-judge` verifies word-bounded hex matches across raw log bytes, JSON text fields, and tool outputs, plus case-insensitive `operation not permitted` on updates matching the denied-write `toolCallId`.
  - `quarantine` uses `os.scandir` and `os.rename` (never `shutil.rmtree`, `os.unlink`, or `os.rmdir`) to move `gas-root-` session entries into an exclusively created `$HOME/.local/state/h-mad/grok-audit-surface/grok-quarantine-<timestamp>Z` directory without following symlinks.
- **No-Checkout Git Plumbing & Symlink Guards (D5, D6, D9)**:
  - `build-root` and `scan_root` reject symlinks and tar members escaping the root (`tarfile.data_filter` + `os.O_NOFOLLOW`), and `restore_expected` unlinks symlinked files or parent directories before writing.
  - `commit-data` reads source files with `os.O_NOFOLLOW`, verifies resolved paths stay inside `--src`, enforces add-only semantics on non-authoring calibration paths (`would_replace:<path>`), and commits via `GIT_INDEX_FILE` plumbing without touching any worktree or real index.

---

## Findings

### Blocking (Must-Fix)
None.

### Non-Blocking (Should-Fix / Observations)
None.

ASSESSMENT: READY_TO_MERGE
