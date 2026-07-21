# Skill-upgrade findings ledger — collected during `orca-git-native-checkpoints-and-merge-gate`

Running list of bugs + lessons surfaced while running `/h-mad` on this feature. **Action these into the h-mad / handoff skills AFTER Phase 7** (they are out of scope for the feature's own diff). Grouped by target.

Status legend: 🔴 bug (needs code fix) · 🟡 process/doc lesson · 🟢 resolved-in-this-feature (no follow-up).

---

## h-mad audit pipeline (scripts)

- 🔴 **F1 — audit gate false-passes on agy/Gemini-TUI output.** `h_mad_audit_gate.py` requires `## Must-fix` at column 0 and counts only `- ` bullets. agy (Antigravity/Gemini) emits every line indented ~2 spaces and uses `•` bullets, so a real Must-fix scored `GATE: PASS must=0 should=0` (plan audit cycle 1). **Fix:** dedent + normalize `•`→`-` at the source — in `h_mad_extract_report.py` (extraction) so the written audit file is already clean, and/or make the gate tolerant of leading whitespace + `•`. See [[feedback_hmad_agy_gemini_tui_capture]] and prior [[feedback_finalizer_hang_guard]] (`•` known since 2026-06).
- 🔴 **F2 — empty extract output false-passes the gate.** `h_mad_extract_report.py` exits 2 and writes nothing when the sentinel pair is absent; piping that empty file into `h_mad_audit_gate.py` yields `GATE: PASS must=0`. An empty audit must be un-gateable. **Fix:** gate should error (exit 2 / `GATE: INVALID`) on an input lacking the schema's `## Must-fix`/`## Should-fix` headers, so "no report" can never read as "clean report". Orchestrator must treat extractor exit-2 as no-verdict (never gate).
- 🟡 **F3 — `orca terminal wait --for tui-idle` is unreliable for Gemini.** Fooled by the spinner: reports `satisfied:false` with stale `blockedReason: codex-trust-workspace` when done, or idle mid-generation. `hmad-dispatch wait` inherits this. **Lesson/opt:** for the Orca+agy path, poll the tail for the `<sentinel>-END` line as the completion signal instead of trusting tui-idle.

## hmad-dispatch (agy/Orca capture)

- 🔴 **F4 — no safe "flush/nudge" for a done-but-unrendered agy REPL.** A bare Enter (`--enter`) submits a BLANK turn to Antigravity and starts junk generation. There is no `hmad-dispatch` verb to reliably force a final render or to interrupt. **Lesson:** Ctrl-C (`$'\x03'`) exits the agy REPL to the shell and FREEZES scrollback → clean `orca terminal read --limit 200` capture; then re-seed agy. Consider a `hmad-dispatch interrupt <agent>` verb + a documented capture-via-freeze recipe.
- 🟡 **F5 — retained scrollback < report length + per-frame redraw fragments sentinels.** Live `orca terminal read` tail can miss a clean BEGIN…END pair mid-generation. Mitigated by the freeze-capture in F4. **Opt:** `hmad-dispatch read` could grow a `--cursor 0 --all` full-buffer mode.
- 🟡 **F6 — agy self-upgraded via homebrew mid-run** (1.1.1→1.1.5), dropping to welcome + trust-workspace prompt and interrupting the dispatch. **Lesson:** pin/preflight the agy version, or re-confirm trust before each dispatch block.

## Environment / bootstrap

- 🟡 **F7 — default substrate was cmux when both binaries present.** Required manual `HMAD_SUBSTRATE=orca`. (This feature's FR-2 fixes the default flip.)
- 🟡 **F8 — `python3` (homebrew 3.14) lacks `jsonschema`; state writer errors `ERROR: jsonschema is required`.** PEP-668 blocks `pip install`. Worked around by using `/opt/anaconda3/bin/python3` (has jsonschema 4.25.1 + pytest 8.3.5). **Lesson:** h-mad state scripts need a documented interpreter/venv, or a graceful degrade + install hint when jsonschema is absent.
- 🟡 **F9 — Codex Orca terminal title is the worktree name** (`skills`), so `_orca_find codex` can't title-match; had to pin `HMAD_ORCA_CODEX_TERMINAL`. (Already known: [[project_orca_adaptation_backlog]]; re-confirmed live.)

## handoff (two-copy hazard)

- 🟡 **F10 — `~/.claude/skills/handoff` is a real dir, NOT a symlink to the repo** (unlike `h-mad`, which is symlinked). Repo edits to `handoff/` do NOT reach the installed skill. **Action:** after Phase 7, re-sync the install copy (or symlink it like h-mad).

---

- 🔴 **F11 — existing worktree/file verbs swallow `ok:false`.** `_cmd_worktree_ps`, `_cmd_worktree_create`, `_cmd_file_diff`, `_cmd_file_open_changed`, `_cmd_task_create`, `_cmd_gate_create` all pipe `orca … --json | _json_extract '…'`. With `set -o pipefail` a non-zero orca *exit* propagates, but an exit-0 response with `"ok":false` (an error envelope) passes through silently as empty/garbage. Surfaced by the design audit (AC-1.5) for the new verbs, which now capture-then-check `.ok`; the **existing** verbs still have the latent bug. **Action:** after Phase 7, give all `orca`-calling verbs the capture-then-`jq -e '.ok==true'` guard (or a shared `_orca_json <args…>` helper — single-source per base invariant).

- 🔴 **F12 — `autonomous_entry_ts` can't hold the value the SKILL writes.** Phase-5a spec: write `phase="step5"` + `autonomous_entry_ts=<now>`. But `h_mad_state_write.py` refuses any non-null `autonomous_entry_ts` (`classified historical`) — the strict `h_mad_state_schema.json` evidently types it null-only (or lacks an integer branch), so the record won't validate with an epoch int. Result: `phase=step5` writes fine, the timestamp stays `null`, and `status`'s stale-`step5` heuristic (`autonomous_entry_ts > 60min ago`) can never fire. **Fix:** make the schema field `["integer","null"]` (or whatever the SKILL intends) so the prescribed write validates. Confirmed live 2026-07-22.

- 🔴 **F13 — dispatch-test `run()` helper leaks live `HMAD_ORCA_*` pins.** `test_hmad_dispatch.py::run()` strips `CMUX`/`CMUX_PANE`/`ORCA_SESSION`/`ORCA_TERMINAL_ID` and `HMAD_SUBSTRATE`, but NOT `HMAD_ORCA_COORDINATOR_TERMINAL` / `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL`. Running the suite from inside a live h-mad Orca session (exactly when Phase-5/6 runs it) leaks those pins into the subprocess and 8 `orca_identity`/`task`/`await` tests fail spuriously (they assume an unpinned env). Verified: they pass with pins stripped (`env -u …`). **Fix:** add the three `HMAD_ORCA_*_TERMINAL` pins (and any `HMAD_ORCA_*`) to the pop-list in `run()`.

_Append new findings below as later phases surface them._
