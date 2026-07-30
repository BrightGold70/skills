# Brainstorm: exec-missing-report-recovery

## Executive Summary
Harden `hmad-dispatch exec` so that when the agent's primary verdict channel (report file / `--output-last-message` / stdout) comes back empty while the work actually landed, the wrapper always retains the surviving `--log` transcript, auto-recovers the `STATUS:`/`VERDICT:` line from it, reports the working-tree delta, and signals the channel failure with a distinct exit code — instead of exiting 0 with empty stdout that reads as either a false pass or a false `no_verdict` halt.

## Problem Statement
On the `exec` path a real 5e GREEN (measured 2026-07-30) finished correct work — the working tree held a production edit plus a new test module — but the agent wrote **no report file, no `.done` marker**, and `--output-last-message` came back empty; only `--log` survived. `_cmd_exec` swallows an empty final message silently (`if [ -s "$last" ]`) and exits 0, so the orchestrator cannot distinguish "done" from "produced nothing." The merged `feat/exec-missing-report` branch documented a **manual** recovery playbook; this feature makes the wrapper do it.

## Proposed Approach
Channels-only hardening of `_cmd_exec` (codex and agy branches):
1. **Always retain a transcript.** When `--log` is omitted, default it to a wrapper-owned `mktemp` file; delete it on clean success, **retain it and print its path** when the final message was empty.
2. **Detect an empty final message** (codex `$last` / agy `$resp`) and, instead of silent exit 0:
   - print a stderr diagnostic naming the retained log,
   - `grep -E 'STATUS:|VERDICT:'` the log tail and, if found, **emit the recovered line to stdout tagged as log-recovered** so `h_mad_extract_verdict.py` still works,
   - print the `git -C <cd> status --porcelain` delta count ("N files changed, no report → reporting-channel failure, not a crash"),
   - **return a distinct rc (3)** so callers branch on it and never read empty-as-pass or empty-as-silent-halt.
3. **Doc alignment.** SKILL 5d/5e exec examples keep the `REPORT_FILE_PATH` slot empty (terminal/last-message mode) so exec has one expected channel; the merged recovery playbook stays as the human procedure (the wrapper now automates its steps 1–2; step 3 "verify from code" remains the verifier discipline).

## Alternatives Considered
- **Always halt for human eyes (no auto-emit)**: safest but blocks every autonomous run on a transport hiccup — rejected; the distinct rc + tree-delta already prevent a silent false pass.
- **Emit recovered verdict with rc=0**: simplest but erases the signal that the primary channel failed — rejected; masks a real problem.
- **Also add a dirty-tree re-dispatch guard on exec/send**: broader, heuristic, higher regression surface — deferred; the playbook's "do not re-dispatch before step 2" stays a documented human rule for now.
- **Report-file polling on exec (like `report-wait`)**: duplicates the pane transport; rejected in favor of terminal/last-message mode for exec.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| A legitimately-empty clean run (no work, no verdict) now returns rc 3 and reads as failure | M | rc 3 is reserved for "empty final message" specifically; a clean run that DID emit its `STATUS:` on stdout keeps rc 0. Document rc 3 as "no verdict on primary channel — check log/tree", distinct from crash (non-zero≠3) and success (0). |
| Auto-log temp files litter `/tmp` on every success | L | delete the auto-log on clean success; retain only on empty-output. |
| `grep` recovers a STALE `STATUS:` from earlier in the transcript | M | take the LAST matching line (same discipline as `h_mad_extract_verdict.py`); the log is a single fresh subprocess run, so no prior-cycle scrollback exists (unlike the pane path). |
| Symlink coupling breaks a HemaSuite suite | M | `hmad-dispatch.sh` is reached by HemaSuite tests via the symlink; run BOTH suites before merge (per skills-symlink-couples-repos). |
| Mutating the wrapper masks a guard (vacuous test) | M | mutation-test each new guard (disable → test RED), both directions. |

## Dependencies
None. Standalone change to `h-mad/scripts/hmad-dispatch.sh` + `h-mad/tests/test_hmad_dispatch_exec.py` + doc alignment in `h-mad/SKILL.md`. No new external dependency.

## Open Questions
- **Rollout ordering** (not a spec blocker): local `main` is 2 commits ahead of origin (the already-merged docs `68c9f22` + `53807f1`), unpushed. Decide whether to push the docs now or bundle with this fix at Phase 7. Carried to closure, not blocking Phase 1–6.
- Exact reserved rc value (3 proposed) — confirm no existing `_cmd_exec` caller already treats 3 specially (none known; codex uses 0/124/crash).

## Version History
- v1.0: Initial brainstorm draft. Decisions locked via clarifying Q&A 2026-07-30: emit-recovered-verdict-+-distinct-rc; channels-only scope; wrapper-owned temp log kept on failure.
