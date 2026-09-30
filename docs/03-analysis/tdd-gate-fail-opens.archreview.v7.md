# Architectural Review: tdd-gate-fail-opens

## 1. Cross-module coupling violations
- **Status:** PASS
- **Details:** The new identity canonicaliser module (`h_mad_target_identity.py`) is appropriately structured as a standard library-only dependency (importing only `os`, `fcntl`, `stat`). The TDD gates access its functions safely: the Codex gate imports `_load_identity()` in process lazily (avoiding global side effects), and the Claude Bash hook invokes it in a single one-shot Python process via `# M:H11`. The judge (`h_mad_tdd_judge.py`) handles realpaths preserving the prior step 8 identities.

## 2. Pattern violations
- **Status:** PASS
- **Details:** 
  - The implementation uses `fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024))` within `canonical_directory` explicitly, mapping failures (and OSes without `F_GETPATH`) cleanly to fallbacks. 
  - The Bash hook's implementation of `_pct_capture` perfectly matches the pattern requirements: assigning via `printf -v`, injecting `0x01` inside the command substitution, and stripping it with `${_pct_v%$'\001'}`.
  - The `apply_patch` grammar logic within the Codex gate correctly identifies target headers without conflating whitespace or throwing unhandled parsing exceptions for payload parsing.
  - Proper extraction and retention of `os.fsencode()` and `os.fsdecode()` usage without asserting hard UTF-8.

## 3. Invariant compliance (Axis B)
- **Status:** PASS
- **Details:** 
  - **Single-source contract:** Enforced correctly. The Codex gate and Claude hook point to `h_mad_target_identity.py` for target path identity.
  - **Portable time bounds:** The `resume_decision` subprocess bounds execution with a fixed 10s variable (`GIT_DIR_BOUND_S = 10.0`), strictly adhering to `subprocess.run(timeout=...)` stdlib usage.
  - **No new external dependency:** Uses standard commands natively present or permitted (`git rev-parse`).
  - **Audit-gate signal discipline:** `compare_readings.py` prints the required string outputs (`COMPARE: PASS` or `COMPARE: FAIL`) and guarantees an exit `0`, matching the specification for pipeline reporting.

## 4. Dead code
- **Status:** PASS
- **Details:** No dead code identified in `h_mad_target_identity.py`, `h-mad-codex-tdd-gate.py`, or `h_mad_tdd_judge.py`. All newly introduced fields (e.g., `BoundedRun.reap_failed` and `CANON` keys) are effectively consumed by the gating conditionals.

## 5. Missing integration tests
- **Status:** PASS
- **Details:** Thorough tests exist. 
  - `test_h_mad_tdd_gate_judge.py` comprehensively exercises all `CANON` protocol parsing branches and failure states.
  - `test_h_mad_resume_decision.py` covers git session ID retrieval failure scenarios, timeouts, permissions, and non-repo boundary tests.

## 6. Security/safety
- **Status:** PASS
- **Details:** Safe execution logic in `_safe_shell_command` is explicitly documented and tightly coupled. The `--session-id-from-git-dir` parameter correctly overrides and mints bounded contexts, avoiding any unverified command injection.

ASSESSMENT: READY_TO_MERGE
