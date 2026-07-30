# Spec: exec-missing-report-recovery

## Executive Summary
`hmad-dispatch exec` must never turn an empty primary verdict channel into a silent exit-0: when the agent's final message is empty it retains the `--log` transcript, recovers the verdict line from it, reports the working-tree delta, and returns a distinct exit code — while leaving the clean-success path byte-for-byte unchanged.

## Goal
Make an `exec` dispatch whose reporting channel failed (report file / `--output-last-message` / stdout all empty) recoverable and unambiguous to the orchestrator, without manual pane forensics.

## Functional Requirements

### FR-1: A transcript is always retained
- **Description**: When the caller omits `--log`, `_cmd_exec` defaults it to a wrapper-owned temp file so the survivor-of-last-resort channel always exists. Applies to both the `codex` and `agy` branches.
- **Acceptance Criteria**:
  - AC-1.1: With `--log` omitted and the agent producing a non-empty final message, `exec` returns rc 0 and the auto-created temp log is **deleted** (no litter on clean success).
  - AC-1.2: With `--log` omitted and the agent producing an **empty** final message, the auto-created temp log is **retained** and its absolute path is printed to stderr.
  - AC-1.3: A caller-supplied `--log <path>` is honored unchanged (written to `<path>`, never auto-deleted).
  - AC-1.4: The default-log mechanism does not alter the stdout verdict or the process exit code on the clean-success path (regression guard: existing `exec` stdout/rc behavior is preserved when a final message is present).

### FR-2: An empty final message is detected, never silently swallowed
- **Description**: On both branches, `_cmd_exec` distinguishes "empty final message" (codex `$last` empty/absent, agy `$resp` empty) from a non-empty one and enters the recovery path instead of the current silent no-op.
- **Acceptance Criteria**:
  - AC-2.1: codex branch — an exit-0 run whose `--output-last-message` file is empty triggers recovery, not a silent `rc=0` with empty stdout.
  - AC-2.2: agy branch — an exit-0 run whose captured response is empty triggers recovery.
  - AC-2.3: A non-empty final message on either branch takes the existing path (cat to stdout, copy to `--out`) and is NOT treated as empty (regression guard).

### FR-3: The verdict line is recovered from the log
- **Description**: On empty output, the wrapper greps the retained log for a verdict line and emits the recovered line to stdout so `h_mad_extract_verdict.py` still resolves a verdict.
- **Acceptance Criteria**:
  - AC-3.1: When the log has a **line beginning with** `STATUS:` (codex) or `VERDICT:` (agy), the **last** such line is emitted to stdout. The match is anchored to line-start so an inline mention (e.g. a prompt fragment "reply with STATUS: DONE") is not wrongly recovered.
  - AC-3.2: The recovered line is accompanied by a stderr marker identifying it as log-recovered (e.g. `hmad-dispatch: exec: verdict recovered from log`), so a reader can tell it did not come from the primary channel.
  - AC-3.3: `h_mad_extract_verdict.py` run against the recovered stdout resolves the same `STATUS:`/`VERDICT:` value that was in the log (end-to-end).
  - AC-3.4: When the log contains multiple verdict lines, only the last is emitted (no stale earlier line).

### FR-4: The working-tree delta is reported on empty output
- **Description**: On empty output the wrapper reports the count of changed paths in the dispatch cwd, distinguishing "work landed, channel failed" from "nothing happened".
- **Acceptance Criteria**:
  - AC-4.1: On empty output, stderr includes a `git -C <cd_dir> status --porcelain` change count (e.g. `tree delta: N changed`).
  - AC-4.2: The delta uses the `--cd` directory (or the resolved default cwd), not the caller's unrelated cwd.
  - AC-4.3: When git is unavailable or the cwd is not a repo, the delta line reports that fact rather than erroring the whole dispatch (non-fatal).

### FR-5: Empty output returns a distinct exit code
- **Description**: An empty final message returns a reserved rc (3) so callers branch on it and never read empty-as-pass or empty-as-crash.
- **Acceptance Criteria**:
  - AC-5.1: Empty final message with the agent process having exited 0 → `exec` returns rc **3**.
  - AC-5.2: A genuine agent crash/abort (non-zero agent exit) still surfaces the agent's own rc, NOT 3 (regression guard: rc 3 is reserved for the exit-0-but-empty case).
  - AC-5.3: A watchdog timeout still returns 124 (regression guard), not 3.
  - AC-5.4: A clean run with a non-empty final message returns rc 0 (regression guard).

### FR-6: Documentation reflects the exec verdict channel
- **Description**: SKILL.md 5d/5e exec guidance states that exec dispatches leave the `REPORT_FILE_PATH` slot empty (terminal/last-message mode), and that rc 3 means "empty primary channel — verdict recovered from log if present, check tree". The merged human recovery playbook is retained.
- **Acceptance Criteria**:
  - AC-6.1: `h-mad/SKILL.md` documents rc 3 and its meaning in the exec-dispatch section.
  - AC-6.2: `h-mad/SKILL.md` states exec dispatches use terminal/last-message mode (empty `REPORT_FILE_PATH` slot), pointing report-file mode at the pane/`report-wait` path.
  - AC-6.3: The existing "A missing report on the `exec` path" playbook section remains present (not deleted by this change).

### FR-7: Both coupled suites pass
- **Description**: The change is verified against both the skills suite and the HemaSuite suite that reaches `hmad-dispatch.sh` through the symlink.
- **Acceptance Criteria**:
  - AC-7.1: `h-mad/tests/` passes 100%.
  - AC-7.2: The HemaSuite `test_h_mad_*` + `test_audit_phase_frontmatter` set passes 100%.
  - AC-7.3: Each new guard is mutation-tested: disabling it (default-log, empty-detect, distinct-rc, last-line recovery) makes at least one test fail.

## Non-Functional Requirements
- Performance: N/A (per-dispatch overhead is one `grep` + one `git status` only on the empty-output path).
- Security: no secret handling; the retained log may contain diffs — it is a local temp file, not transmitted.
- Compatibility: no change to `_cmd_exec`'s public flags or the clean-success stdout/rc contract; purely additive on the empty-output path. `bash` 3.2 (macOS) + POSIX `git`/`grep`.

## Out-of-Scope
- Dirty-tree re-dispatch guard on `exec`/`send` (deferred; stays a documented human rule).
- Report-file polling on the exec path (report-file mode remains pane/`report-wait` only).
- Any change to the pane path (`send`/`ask`/`report-wait`) verdict handling.
- Pushing the already-merged doc commits (`68c9f22`/`53807f1`) — a Phase-7 rollout decision, not a code requirement.

## Assumptions
- codex `exec` exits 0 on a completed run even when `--output-last-message` is empty (the measured incident).
- No existing `_cmd_exec` caller assigns special meaning to rc 3 (codex path uses 0 / 124 / crash rc).
- The log transcript, when present, contains the agent's `STATUS:`/`VERDICT:` line even when the last-message file does not (observed: `--log` outlived `--out` and the report file).

## Version History
- v1.0: Initial specification draft. Decisions locked 2026-07-30 (emit-recovered-verdict + distinct rc 3; channels-only; wrapper-owned temp log kept on failure).
- v1.1: AC-3.1 reconciled to the anchored `^(STATUS|VERDICT):` match (design-audit cycle 1 back-propagation).
