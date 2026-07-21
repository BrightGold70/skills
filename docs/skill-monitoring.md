# Skill Monitoring — bugs & improvement points (standing)

Live registry of known bugs and improvement points in the `h-mad` / `handoff` skills, surfaced during real `/h-mad` runs. **Not auto-fixed** — each entry is under monitoring until deliberately actioned. Action a batch as its own `/h-mad` feature when priority warrants.

**Status:** 🔴 bug (correctness) · 🟡 process/robustness · 🟢 improvement/opt
**Lifecycle:** `MONITORING` (tracked, unfixed) · `PLANNED` (scheduled) · `FIXED` (link commit) · `WONTFIX` (with reason)

Origin run: `orca-git-native-checkpoints-and-merge-gate` (shipped main `2b95476`, 2026-07-22).

| ID | Sev | Status | One-line |
|---|---|---|---|
| F1 | 🔴 | MONITORING | audit gate false-passes on agy/Gemini-TUI output (indent + `•` bullets) |
| F2 | 🔴 | MONITORING | empty extract output false-passes the gate (`must=0`) |
| F3 | 🟡 | MONITORING | `orca terminal wait --for tui-idle` unreliable for Gemini spinner |
| F4 | 🟡 | MONITORING | no safe nudge/interrupt verb; bare-Enter submits a blank agy turn |
| F5 | 🟡 | MONITORING | Orca scrollback retention < report length; TUI redraw fragments sentinels |
| F6 | 🟡 | MONITORING | agy self-upgrades via homebrew mid-run → re-auth/trust reset |
| F7 | 🟢 | FIXED | default substrate was cmux when both present → flipped to orca (`9cdd455`) |
| F8 | 🟡 | MONITORING | `python3` (brew 3.14) lacks jsonschema; state scripts need documented interp/venv |
| F9 | 🟡 | MONITORING | Codex Orca terminal title = worktree name → must pin `HMAD_ORCA_CODEX_TERMINAL` |
| F10 | 🟡 | FIXED | `~/.claude/skills/handoff` was a real dir → symlinked to repo 2026-07-22 |
| F11 | 🔴 | MONITORING | existing worktree/file verbs swallow `ok:false` (exit-0 error envelope) |
| F12 | 🔴 | MONITORING | `autonomous_entry_ts` schema rejects the epoch value the SKILL writes |
| F13 | 🔴 | MONITORING | dispatch-test `run()` leaks `HMAD_ORCA_*` pins → spurious failures in-session |

---

## h-mad audit pipeline (scripts)

- 🔴 **F1 — audit gate false-passes on agy/Gemini-TUI output.** `h_mad_audit_gate.py` requires `## Must-fix` at column 0 and counts only `- ` bullets. agy (Antigravity/Gemini) emits every line indented ~2 spaces and uses `•` bullets, so a real Must-fix scored `GATE: PASS must=0 should=0` (plan audit cycle 1). **Fix:** dedent + normalize `•`→`-` at the source — in `h_mad_extract_report.py` (extraction) so the written audit file is already clean, and/or make the gate tolerant of leading whitespace + `•`. See [[feedback_hmad_agy_gemini_tui_capture]] and prior `feedback_finalizer_hang_guard` (`•` known since 2026-06).
- 🔴 **F2 — empty extract output false-passes the gate.** `h_mad_extract_report.py` exits 2 and writes nothing when the sentinel pair is absent; piping that empty file into `h_mad_audit_gate.py` yields `GATE: PASS must=0`. An empty audit must be un-gateable. **Fix:** gate should error (exit 2 / `GATE: INVALID`) on input lacking the schema's `## Must-fix`/`## Should-fix` headers, so "no report" can never read as "clean report". Orchestrator must treat extractor exit-2 as no-verdict (never gate).
- 🟡 **F3 — `orca terminal wait --for tui-idle` is unreliable for Gemini.** Fooled by the spinner: reports `satisfied:false` with stale `blockedReason: codex-trust-workspace` when done, or idle mid-generation. `hmad-dispatch wait` inherits this. **Lesson/opt:** for the Orca+agy path, poll the tail for the `<sentinel>-END` line as the completion signal instead of trusting tui-idle.

## hmad-dispatch (agy/Orca capture)

- 🔴 **F4 — no safe "flush/nudge" for a done-but-unrendered agy REPL.** A bare Enter (`--enter`) submits a BLANK turn to Antigravity and starts junk generation. There is no `hmad-dispatch` verb to reliably force a final render or to interrupt. **Lesson:** Ctrl-C (`$'\x03'`) exits the agy REPL to the shell and FREEZES scrollback → clean `orca terminal read --limit 200` capture; then re-seed agy. Consider a `hmad-dispatch interrupt <agent>` verb + a documented capture-via-freeze recipe.
- 🟡 **F5 — retained scrollback < report length + per-frame redraw fragments sentinels.** Live `orca terminal read` tail can miss a clean BEGIN…END pair mid-generation. Mitigated by the freeze-capture in F4. **Opt:** `hmad-dispatch read` could grow a `--cursor 0 --all` full-buffer mode.
- 🟡 **F6 — agy self-upgraded via homebrew mid-run** (1.1.1→1.1.5), dropping to welcome + trust-workspace prompt and interrupting the dispatch. **Lesson:** pin/preflight the agy version, or re-confirm trust before each dispatch block.

## Environment / bootstrap

- 🟢 **F7 — default substrate was cmux when both binaries present.** `FIXED` — FR-2 of the origin feature flipped the default to orca (`9cdd455`). Kept here for provenance.
- 🟡 **F8 — `python3` (homebrew 3.14) lacks `jsonschema`; state writer errors `ERROR: jsonschema is required`.** PEP-668 blocks `pip install`. Worked around with `/opt/anaconda3/bin/python3` (jsonschema 4.25.1 + pytest 8.3.5). **Fix:** h-mad state scripts need a documented interpreter/venv, or a graceful degrade + install hint when jsonschema is absent.
- 🟡 **F9 — Codex Orca terminal title is the worktree name** (`skills`), so `_orca_find codex` can't title-match; must pin `HMAD_ORCA_CODEX_TERMINAL`. (Already known: `project_orca_adaptation_backlog`; re-confirmed live.)

## handoff

- 🟡 **F10 — `~/.claude/skills/handoff` was a real dir, NOT a symlink to the repo** (unlike `h-mad`). `FIXED` 2026-07-22: replaced with a symlink → `/Users/kimhawk/orca/skills/handoff` (pre-install backup at `~/.claude/handoff-preinstall-backup-2026-07-22`). Repo changes are now live in the installed skill.

## h-mad verbs / state / tests

- 🔴 **F11 — existing worktree/file verbs swallow `ok:false`.** `_cmd_worktree_ps`, `_cmd_worktree_create`, `_cmd_file_diff`, `_cmd_file_open_changed`, `_cmd_task_create`, `_cmd_gate_create` all pipe `orca … --json | _json_extract '…'`. With `set -o pipefail` a non-zero orca *exit* propagates, but an exit-0 `"ok":false` error envelope passes silently as empty/garbage. The NEW `worktree-comment`/`worktree-current` verbs capture-then-check `.ok`; the existing verbs still have the latent bug. **Fix:** give all `orca`-calling verbs the capture-then-`jq -e '.ok==true'` guard (or a shared `_orca_json` helper — single-source per base invariant).
- 🔴 **F12 — `autonomous_entry_ts` can't hold the value the SKILL writes.** Phase-5a spec: write `phase="step5"` + `autonomous_entry_ts=<now>`. But `h_mad_state_write.py` refuses any non-null `autonomous_entry_ts` (`classified historical`) — the strict schema evidently types it null-only. Result: `phase=step5` writes fine, the timestamp stays `null`, and `status`'s stale-`step5` heuristic (`autonomous_entry_ts > 60min ago`) can never fire. **Fix:** make the schema field `["integer","null"]` so the prescribed write validates.
- 🔴 **F13 — dispatch-test `run()` helper leaks live `HMAD_ORCA_*` pins.** `test_hmad_dispatch.py::run()` strips `CMUX`/`CMUX_PANE`/`ORCA_SESSION`/`ORCA_TERMINAL_ID`/`HMAD_SUBSTRATE`, but NOT `HMAD_ORCA_COORDINATOR_TERMINAL` / `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL`. Running the suite from inside a live h-mad Orca session (exactly when Phase-5/6 runs it) leaks those pins and 8 `orca_identity`/`task`/`await` tests fail spuriously. Verified: they pass with pins stripped (`env -u …`). **Fix:** add the three `HMAD_ORCA_*_TERMINAL` pins (and any `HMAD_ORCA_*`) to the pop-list in `run()`.

---

_Append new findings below as later runs surface them. Flip Status + link the commit when actioned._
