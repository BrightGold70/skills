# Design: exec-missing-report-recovery

## Executive Summary
Rework the emptiness test at the tail of `_cmd_exec` (both agent branches) into an explicit empty-vs-nonempty fork: the non-empty arm is today's behavior unchanged, and the empty arm recovers the verdict from an always-present log, reports the tree delta, and reserves rc 3 — with `--log` defaulted to a wrapper-owned temp so the log always exists.

## Overview
The change is confined to `h-mad/scripts/hmad-dispatch.sh` `_cmd_exec`. Design intent: additive on the empty-output branch, byte-identical stdout/rc on the clean-success branch, no new flags, no new dependency (POSIX `git`/`grep`, bash 3.2). Key decision: default `--log` to a temp file so the recovery step always has a source; on a clean run that temp is deleted, so a successful exec leaves no litter and behaves as before except that a bare (no-`--log`) exec now routes its transcript to a printed temp path instead of streaming to stderr.

## Architecture Overview
```
_cmd_exec <agent> <promptfile> [flags]
  ├─ resolve flags; cd_dir defaults to git toplevel|pwd
  ├─ auto-log: if --log omitted → log=$(mktemp); auto_log=1; print "transcript: $log" to stderr
  ├─ run agent (codex: stdin + --output-last-message="$last"; agy: --print arg)
  │     transcript ALWAYS → "$log" (2>&1); rc captured via `|| rc=$?`
  ├─ final message = codex:"$last" | agy:"$resp"(<- cat "$log")
  ├─ if final message NON-EMPTY:              # unchanged contract
  │     [--out] cp/echo it; cat/printf to stdout; if auto_log → rm "$log"
  └─ else (EMPTY final message):              # NEW recovery arm
        if rc==0 → rc=3, msg="reporting channel failed…" else msg="agent exited $rc…"
        stderr: "EMPTY final message — $msg; transcript: $log"   # truthful for a crash too
        recovered = grep -aE 'STATUS:|VERDICT:' "$log" | tail -1
        if recovered: stderr "verdict recovered from log"; stdout <- recovered; [--out] <- recovered
        stderr: "tree delta: <N> changed"  (or "n/a (not a git repo)")
        # auto_log is RETAINED here (recovery artifact)
  └─ stderr "hmad-dispatch: <agent> exec rc=$rc"; return "$rc"
```

## Detailed Design

### Auto-log defaulting (FR-1)
Immediately after flag parsing and the `cd_dir` default, before the agent runs:
```sh
local auto_log=""
if [ -z "$log" ]; then
  log="$(mktemp -t hmad_exec_log.XXXXXX)" || return 1
  auto_log=1
  echo "hmad-dispatch: exec: transcript -> $log" >&2
fi
```
Because `$log` is now always set, the codex `if [ -n "$log" ]` redirect branch is always taken and the two former `>&2`-only sub-branches become unreachable; they are removed. agy likewise always uses its `> "$log"` path and reads `resp="$(cat "$log")"`. A caller-supplied `--log` sets `auto_log=""`, so it is never deleted.

### Empty-vs-nonempty fork (FR-2)
- codex: emptiness is `[ -s "$last" ]` (the `--output-last-message` file), as today.
- agy: emptiness is `[ -n "$resp" ]` where `resp="$(cat "$log" 2>/dev/null)"`.
Non-empty arm = current code verbatim, plus `[ -n "$auto_log" ] && rm -f "$log"`. Empty arm = the recovery block below.

### Verdict recovery from log (FR-3)
```sh
local recovered
recovered="$(grep -aE '^(STATUS|VERDICT):' "$log" 2>/dev/null | tail -1)"
if [ -n "$recovered" ]; then
  echo "hmad-dispatch: exec: verdict recovered from log ($log)" >&2
  printf '%s\n' "$recovered"
  [ -n "$out" ] && printf '%s\n' "$recovered" > "$out"
fi
```
`tail -1` takes the LAST match (extractor discipline). `grep -a` guards against a transcript with non-text bytes. The regex is **anchored** (`^(STATUS|VERDICT):`): the log is a plain redirect, not a TUI render, so verdict lines start clean, and anchoring drops an inline mention (e.g. a prompt fragment `reply with STATUS: DONE`) that an unanchored match would wrongly recover.

**Reconciliation with spec AC-3.1 (design-audit cycle 1):** the spec said "when the log *contains* `STATUS:`/`VERDICT:`". The design narrows that to *lines beginning with* the marker; spec AC-3.1 has been updated to the anchored wording so the contract and implementation agree.

### Tree-delta report (FR-4)
```sh
if git -C "$cd_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  local delta; delta="$(git -C "$cd_dir" status --porcelain 2>/dev/null | grep -c . || true)"
  echo "hmad-dispatch: exec: tree delta: ${delta} changed in $cd_dir" >&2
else
  echo "hmad-dispatch: exec: tree delta: n/a ($cd_dir not a git repo)" >&2
fi
```
Non-fatal: a git failure never changes `rc`.

### Reserved rc 3 + a truthful empty-arm notice (FR-5)
```sh
local msg
if [ "$rc" -eq 0 ]; then
  rc=3; msg="reporting channel failed (agent exited 0, no final message)"
else
  msg="agent exited ${rc} with no final message"
fi
echo "hmad-dispatch: exec: EMPTY final message — ${msg}; transcript: $log" >&2
```
rc 3 is set **only** when the agent process itself exited 0; a crash (`rc` already non-zero) and a watchdog timeout (`rc=124`) are preserved, so 3 uniquely means "process exited 0 but produced no final message." The notice is conditioned on `rc` so a crash is not mislabelled "reporting channel failed" — it reports the non-zero exit instead.

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_cmd_exec` recovery fork | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-1..FR-5 |
| exec-dispatch docs | `h-mad/SKILL.md` | modify | FR-6 (rc 3 + terminal-mode note) |
| exec recovery tests | `h-mad/tests/test_hmad_dispatch_exec.py` | modify | FR-2..FR-5, FR-7 (+FR-1 via clean-path) |

## Implementation Order
1. Auto-log defaulting + non-empty-arm teardown (FR-1); confirm clean-path stdout/rc unchanged.
2. Empty-arm fork skeleton + rc 3 (FR-2, FR-5).
3. Verdict recovery grep (FR-3).
4. Tree-delta reporter (FR-4).
5. SKILL.md doc update (FR-6).
6. Tests + mutation checks (FR-7).

## Data Model / Schema Changes
None.

## API / Interface Changes
- No new/changed flags. `_cmd_exec` exit codes gain one reserved value: **3 = "agent exited 0 but final message empty; verdict recovered from log if present."** `0` (success), `124` (watchdog), and the agent's own crash rc are unchanged.
- Behavior change (documented): when `--log` is omitted, the transcript now goes to an auto-created temp file (path printed to stderr) instead of streaming to stderr; the file is deleted on clean success and retained on empty output.

## Error Handling Strategy
Diagnostics (auto-log path, empty-message notice, recovery notice, tree delta) all go to **stderr**; the recovered verdict is the only thing written to **stdout**, preserving `stdout = payload` for `h_mad_extract_verdict.py`. `rc` is the machine signal: 0 clean, 3 empty-output, 124 timeout, else agent crash. git/grep failures in the recovery arm are swallowed (`2>/dev/null`, `|| true`) and never alter `rc`.

## Test Strategy
Unit-level, mocking at the **CLI boundary**: a PATH-shimmed fake `codex`/`agy` script whose behavior is scripted per case (exit code, whether it writes a non-empty `--output-last-message`, what it writes to the transcript, whether it touches a tree file). No real model calls. cwd/tree assertions run in a `tmp_path` git repo. Mutation checks disable each guard and assert a test flips RED.

## Test Plan
`h-mad/tests/test_hmad_dispatch_exec.py` (verify: `/opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_hmad_dispatch_exec.py -q`):
- **clean success, no --log** → rc 0, stdout = final message, auto-log deleted (AC-1.1, 1.4, 2.3, 5.4).
- **empty last-message, log has `STATUS: DONE`, codex exit 0** → rc 3, stdout carries `STATUS: DONE`, stderr names retained log + tree delta (AC-2.1, 3.1, 3.2, 4.1, 5.1); auto-log retained (AC-1.2).
- **empty, log has two `STATUS:` lines** → stdout = the last (AC-3.4).
- **empty, agy `$resp` empty, log has `VERDICT: COMPLIANT`** → rc 3, stdout `VERDICT: COMPLIANT` (AC-2.2, 3.1).
- **caller --log honored + not deleted** (AC-1.3).
- **agent crash (exit 2), empty** → rc 2, not 3 (AC-5.2). **watchdog** → rc 124, not 3 (AC-5.3).
- **empty, cwd not a git repo** → tree-delta reports n/a, dispatch still returns 3 (AC-4.3).
- **e2e extractor**: pipe recovered stdout to `h_mad_extract_verdict.py` → resolves the value (AC-3.3).
- **mutation**: remove `auto_log` default / remove `[ "$rc" -eq 0 ] && rc=3` / change `tail -1`→`head -1` / skip the empty-arm → each makes ≥1 test RED (AC-7.3).
- Full skills suite + HemaSuite coupled set (AC-7.1, 7.2).

## Invariant Compliance
- **Skill self-containment** (Axis B): complies — change is inside `hmad-dispatch.sh`, no cross-skill import, no path outside the skill dir; `git`/`grep`/`mktemp` are OS tools.
- **Skill manifest integrity** (Axis B): complies — no change to `SKILL.md` frontmatter or entry behavior; SKILL.md edit is documentation of an exec exit code, not a contract-name change.
- **Base — audit-gate signal discipline**: N/A to this feature (no gate/exit semantics for a Claude tool call are changed; rc 3 is `_cmd_exec`'s own return read by the orchestrator, not a hook exit).
- **Base — single-source contract**: the emptiness test stays the single fork point; recovery hangs off its else, not a parallel code path.
- **Base — backward compatibility**: clean-success stdout/rc byte-identical; rc 3 is a new value in a previously-unused slot (verified: `grep 'return 3|exit 3'` → none); the only behavior change (bare-exec transcript destination) is documented and asserted.
- **Base — no-plugin-dependency / no new external dependency**: only `git`, `grep`, `mktemp`.
- **Base — mutation / test-discrimination**: every guard mutation-tested (Test Plan).

## Assumption verification (evidence, 2026-07-30)
Throwaway run of the design's load-bearing commands, per the base Assumption-verification invariant:
```
$ git -C <repo> rev-parse --is-inside-work-tree          → true
$ git -C /tmp   rev-parse --is-inside-work-tree          → fatal: not a git repository  (rc≠0, guard takes the n/a branch)
$ (2 untracked) git -C <repo> status --porcelain | grep -c .   → 2
$ printf 'STATUS: WRONG inline\nSTATUS: DONE\nSTATUS: BLOCKED\n' | grep -aE '^(STATUS|VERDICT):' | tail -1   → STATUS: BLOCKED
$ printf 'reply with STATUS: DONE as your line\n'          | grep -aE '^(STATUS|VERDICT):'          → (no match — inline echo correctly ignored)
```
Confirms: the git guard cleanly splits repo/non-repo (FR-4.3), the porcelain count is the change count (FR-4.1), `tail -1` returns the last verdict (AC-3.4), and anchoring ignores an inline contract-echo (AC-3.1).

## Version History
- v1.0: Initial design draft.
- v1.1: Design-audit cycle 1 fixes — (must-fix) reconciled spec AC-3.1 to the anchored `^(STATUS|VERDICT):` match; (must-fix) added the Assumption-verification evidence block for the git/grep commands; (nit) empty-arm notice now conditioned on `rc` so a crash is not mislabelled "reporting channel failed".
