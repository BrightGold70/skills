# Implementation Plan: exec-missing-report-recovery

> Source: docs/02-design/features/exec-missing-report-recovery.design.md (post-audit)
> Branch target: feature/NNN-exec-missing-report-recovery

## Executive Summary
A single task: rework the tail of `_cmd_exec` in `hmad-dispatch.sh` into an empty-vs-nonempty fork (auto-log default, verdict recovery, tree delta, reserved rc 3) and cover it in `test_hmad_dispatch_exec.py`; no other module is touched.

## Task 1: exec-empty-output-recovery

**Production files**: `h-mad/scripts/hmad-dispatch.sh` (function `_cmd_exec`) and `h-mad/SKILL.md` (exec-dispatch docs — FR-6)
**Test file**: `h-mad/tests/test_hmad_dispatch_exec.py`

**Description**: Modify `_cmd_exec` so that (a) an omitted `--log` is defaulted to a `mktemp` transcript that is deleted on clean success and retained on empty output; (b) the existing final-message emptiness test forks: the non-empty arm is unchanged, the empty arm reserves rc 3 over a clean exit, recovers the last line matching `^(STATUS|VERDICT):` from the log to stdout, and prints a `git status --porcelain` change count for the `--cd` dir. All diagnostics go to stderr; only the recovered verdict goes to stdout. No new flags, no new dependency (bash 3.2, POSIX `git`/`grep`/`mktemp`). Both codex and agy branches get the fork.

**Code structure** (shell contracts, not implementations):
```sh
_cmd_exec() {
  # ... existing flag parse, cd_dir default ...
  local auto_log=""
  if [ -z "$log" ]; then log="$(mktemp -t hmad_exec_log.XXXXXX)" || return 1; auto_log=1
    echo "hmad-dispatch: exec: transcript -> $log" >&2; fi

  # ... run agent, transcript always -> "$log" 2>&1, rc captured via `|| rc=$?` ...
  # codex: final message in "$last"; agy: resp="$(cat "$log")"

  if <final message non-empty>; then
    <existing behavior: [--out] cp/echo; cat/printf to stdout>
    [ -n "$auto_log" ] && rm -f "$log"
  else
    local msg
    if [ "$rc" -eq 0 ]; then rc=3; msg="reporting channel failed (agent exited 0, no final message)"
    else msg="agent exited ${rc} with no final message"; fi
    echo "hmad-dispatch: exec: EMPTY final message — ${msg}; transcript: $log" >&2
    local recovered; recovered="$(grep -aE '^(STATUS|VERDICT):' "$log" 2>/dev/null | tail -1)"
    if [ -n "$recovered" ]; then
      echo "hmad-dispatch: exec: verdict recovered from log ($log)" >&2
      printf '%s\n' "$recovered"; [ -n "$out" ] && printf '%s\n' "$recovered" > "$out"; fi
    if git -C "$cd_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      echo "hmad-dispatch: exec: tree delta: $(git -C "$cd_dir" status --porcelain 2>/dev/null | grep -c . || true) changed in $cd_dir" >&2
    else echo "hmad-dispatch: exec: tree delta: n/a ($cd_dir not a git repo)" >&2; fi
  fi
  # ... existing "$agent exec rc=$rc" >&2; return "$rc"
}
```

**Acceptance Criteria**:
- [ ] AC-1.1: `--log` omitted + non-empty final message → rc 0, auto-log deleted.
- [ ] AC-1.2: `--log` omitted + empty final message → auto-log retained, path on stderr.
- [ ] AC-1.3: caller `--log <path>` honored, never auto-deleted.
- [ ] AC-1.4: clean-success stdout + rc unchanged vs pre-change (regression).
- [ ] AC-2.1: codex empty `--output-last-message` (exit 0) → recovery arm.
- [ ] AC-2.2: agy empty response (exit 0) → recovery arm.
- [ ] AC-2.3: non-empty final message → existing path, not treated as empty.
- [ ] AC-3.1: last line matching `^(STATUS|VERDICT):` emitted to stdout; inline mention ignored.
- [ ] AC-3.2: stderr marker identifies the line as log-recovered.
- [ ] AC-3.3: `h_mad_extract_verdict.py` on the recovered stdout resolves the value.
- [ ] AC-3.4: multiple verdict lines → last emitted.
- [ ] AC-4.1: empty output → stderr `git status --porcelain` change count.
- [ ] AC-4.2: delta uses `--cd` dir.
- [ ] AC-4.3: non-repo cwd → n/a line, dispatch still returns 3, no error.
- [ ] AC-5.1: empty + agent exit 0 → rc 3.
- [ ] AC-5.2: agent crash (exit 2) + empty → rc 2, not 3.
- [ ] AC-5.3: watchdog timeout → rc 124, not 3.
- [ ] AC-5.4: clean non-empty → rc 0.
- [ ] AC-6.1: `h-mad/SKILL.md` documents rc 3 and its meaning in the exec-dispatch section.
- [ ] AC-6.2: `h-mad/SKILL.md` states exec dispatches use terminal/last-message mode (empty `REPORT_FILE_PATH` slot), pointing report-file mode at the pane/`report-wait` path.
- [ ] AC-6.3: the existing "A missing report on the `exec` path" playbook section remains present.
- [ ] AC-7.1: full `h-mad/tests/` suite passes 100%.
- [ ] AC-7.2: HemaSuite `test_h_mad_*` + `test_audit_phase_frontmatter` set passes 100% (symlink coupling).
- [ ] AC-7.3: each guard (auto-log default, rc-3-over-0, `tail -1`, empty-arm fork) mutation-tested RED.

**Regression guards** (must pass from the first run, pre-existing behavior): AC-1.4, AC-2.3, AC-5.4, and the whole existing `test_hmad_dispatch_exec.py` / `test_hmad_dispatch.py` suite. These are labelled guards for the 5d RED dispatch — they are expected to PASS immediately; do not manufacture failures for them.

**New-behavior tests** (expected to FAIL in RED, pass after GREEN): AC-1.2, AC-3.1, AC-3.4, AC-4.1, AC-4.3, AC-5.1, AC-5.2.

**Dependencies on other tasks**: None.

## Version History
- v1.0: Initial implementation plan draft.
- v1.1: Impl-plan audit cycle 1 fixes — (must-fix) added `h-mad/SKILL.md` to production files + AC-6.1/6.2/6.3 for FR-6; (must-fix) added AC-7.1/7.2 full-suite + HemaSuite regression ACs; (should-fix) added `|| true` to the `grep -c .` tree-delta command.
