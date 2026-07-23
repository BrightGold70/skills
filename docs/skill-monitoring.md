# Skill Monitoring — bugs & improvement points (standing)

Live registry of known bugs and improvement points in the `h-mad` / `handoff` skills, surfaced during real `/h-mad` runs. **Not auto-fixed** — each entry is under monitoring until deliberately actioned. Action a batch as its own `/h-mad` feature when priority warrants.

**Status:** 🔴 bug (correctness) · 🟡 process/robustness · 🟢 improvement/opt
**Lifecycle:** `MONITORING` (tracked, unfixed) · `PLANNED` (scheduled) · `FIXED` (link commit) · `WONTFIX` (with reason)

Origin run: `orca-git-native-checkpoints-and-merge-gate` (shipped main `2b95476`, 2026-07-22).
**All F1–F13 resolved on `feature/186-skill-monitoring-fixes` (2026-07-22)** — h-mad suite 355/0 with session pins present. Fixes below; each entry's Status flipped to FIXED.

| ID | Sev | Status | One-line |
|---|---|---|---|
| F1 | 🔴 | FIXED | audit gate false-passes on agy/Gemini-TUI output (indent + `•` bullets) — gate now dedents + accepts `-`/`*`/`•` |
| F2 | 🔴 | FIXED | empty extract output false-passes the gate — `GATE: INVALID` + exit 2 when Must-fix/Should-fix headers absent |
| F3 | 🟡 | FIXED | `tui-idle` unreliable for Gemini — documented: poll for `<sentinel>-END` (agent-substrate.md) |
| F4 | 🟡 | FIXED | no safe nudge — added `hmad-dispatch interrupt` (Ctrl-C) + freeze-capture recipe |
| F5 | 🟡 | FIXED | scrollback < report — added `read --cursor N` / `--from-start` full-buffer read |
| F6 | 🟡 | FIXED | agy homebrew self-upgrade — documented version/trust preflight |
| F7 | 🟢 | FIXED | default substrate was cmux when both present → flipped to orca (`9cdd455`) |
| F8 | 🟡 | **RE-OPENED** | jsonschema missing — remedy *message* shipped, dependency gap unchanged; every run still needs a manual interpreter (see J4) |
| F9 | 🟡 | FIXED | Codex Orca title = worktree name — pin `HMAD_ORCA_CODEX_TERMINAL` (documented in agent-substrate.md identity) |
| F10 | 🟡 | FIXED | `~/.claude/skills/handoff` was a real dir → symlinked to repo 2026-07-22 |
| F11 | 🔴 | FIXED | verbs swallow `ok:false` — shared `_orca_json` guard (`.ok != false`) on all extract verbs |
| F12 | 🔴 | FIXED | `autonomous_entry_ts` schema — now `["string","integer","null"]`, epoch int validates |
| F13 | 🔴 | FIXED | dispatch-test `run()` leaks pins — now strips every `HMAD_ORCA_*` |

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

## Surfaced by the F1–F13 fix review (subagent code-review, 2026-07-22)

- 🟡 **F14 — audit gate only counted bullet-prefixed findings; prose/numbered/blockquote findings scored PASS.** `FIXED` 2026-07-22. `classify()` now decides per section on the line *payload* (bullet remainder, else the line itself): a section is clean ONLY if every payload is the `None` sentinel; otherwise it has findings — counted as the number of `-`/`*`/`•` bullets, or 1 when the content is non-`None` but bullet-less (prose / `1.` numbered / `> blockquote` / stray note). A wrapped multi-line bullet still counts once (continuation lines aren't bullets, so they don't add). This is fail-safe: an off-template finding now FAILs the gate (human reformats) instead of silently passing. Trade-off: an off-template *reassurance* note under a section also FAILs — reviewers must write `None` for a clean section, per the template contract. Supersedes the earlier bullet-space-only handling of markdown emphasis.

## Handoff/merge-gate Orca-wiring audit (2026-07-22, post-ship review)

Found by auditing the shipped handoff + merge-gate against the **real** Orca payload/CLI (the reconcile was verified by mocked unit tests + doc review, never run live — [[feedback_tracer_bullet_before_ceremony]]). All FIXED on `feature/187-orca-reconcile-and-gate-fixes`.

| ID | Sev | Status | One-line |
|---|---|---|---|
| G1 | 🔴 | FIXED | handoff READ read wrong JSON path — payload is `{"worktree":{…}}`, prose said `.branch`/`.comment` → now `.worktree.branch` etc. |
| G2 | 🔴 | FIXED | branch-format mismatch — `worktree-current` returns `refs/heads/main`, doc uses `main` → prose now strips `refs/heads/` before compare |
| G3 | 🟡 | FIXED | `worktree-ps` shape `{"worktrees":[…],"truncated"}` + truncation now documented (iterate `.worktrees[]`, surface `truncated`, `--limit`) |
| G4 | 🟡 | FIXED | merge-gate blocking path had no wait mechanism — added `hmad-dispatch gate-wait <id>` (polls `gate-list`); orchestration-mode blocking paths now use it, not `await` |
| G5 | 🟡 | FIXED | orchestration needed a manual coordinator pin — `_coordinator()` now auto-detects from `ORCA_PANE_KEY` leafId → `terminal list`; `orchestration: on` with no setup |
| G6 | 🟢 | FIXED | WRITE stamp clobbered a foreign worktree comment — prose now reads `.worktree.comment` first and appends to a non-skill note instead of overwriting |

- 🔴 **G1** — `worktree-current` payload is `{"worktree":{branch,path,comment,…}}`; the handoff READ reconcile read `.branch`/`.path`/`.comment` (one level too shallow). Fixed to `.worktree.*`. Live-confirmed shape.
- 🔴 **G2** — `.worktree.branch` is a full ref (`refs/heads/main`); the handoff doc's Branch field + `git rev-parse --abbrev-ref` use the short name → naive compare = permanent phantom divergence. Prose now strips `refs/heads/`.
- 🟡 **G3** — `worktree-ps` returns `{"worktrees":[…],"totalCount","truncated"}`; prose now iterates `.worktrees[]`, strips `refs/heads/`, and surfaces `truncated` (cap raised via `--limit`).
- 🟡 **G4** — only `gate-create`/`gate-resolve` existed; a "blocking" gate could be opened but not waited on (`await` waits for `worker_done`, not gates). Added `gate-wait <id> [--timeout][--interval]` polling `orchestration gate-list`. **Fails closed** (review hardening): resolves only on `.resolution` present OR `.status == "resolved"` — any other status (`open`/`created`/`waiting`/`pending`) keeps polling, so a blocking merge gate never proceeds on an ambiguous state (worst case = spurious timeout, the correct bias). Live-verified clean timeout; `test_gate_wait_fails_closed_on_non_resolved_status` locks it. **Resolved-gate shape now confirmed against a live runtime** (2026-07-22): a full lifecycle — `task-create → gate-create → gate-resolve → gate-wait` — showed pending = `{status:"pending", resolution:null, resolved_at:null}` and resolved = `{status:"resolved", resolution:"yes", resolved_at:"…"}`, and `gate-wait` returned `yes`. The fail-closed jq (`.resolution` present OR `.status=="resolved"`) matches the real field names exactly. No caveat remains.
- 🟡 **G5** — `_coordinator()` auto-detects from `ORCA_PANE_KEY="<tabId>:<leafId>"` → matches a terminal's `.leafId` in `terminal list`. Live-verified: `orchestration: on` with no `HMAD_ORCA_COORDINATOR_TERMINAL`. Pin still overrides.
- 🟢 **G6** — WRITE stamp now reads the current comment first; a foreign (non-`handoff:`/`h-mad`) note is appended to, not clobbered.

## Architecture: report-file transport (root fix for the scrape-fragility class)

- 🟢 **A1 — audit/TDD verdict collection moved from TUI-scrape to file-drop under Orca.** `FIXED` 2026-07-22 (feature/188). New `hmad-dispatch report-wait <path>` verb: the dispatched agent writes its full report to `<path>` and creates `<path>.done`; the coordinator polls the marker and reads the file — no `tui-idle` guess, no screen scrape, no `BEGIN/END` sentinel, no dedent/`•`-normalize. Substrate-agnostic (shared fs; scrape stays the cmux/unpinned fallback). The audit-prompt + codex-implementer templates carry a `<REPORT_FILE_PATH>` contract slot; SKILL §Audit-assembly + orchestration-mode.md document report-file as the default under Orca. **Live e2e verified**: agy wrote clean markdown to the file + `.done`, `report-wait` read it, and `h_mad_audit_gate.py` scored `GATE: PASS` directly with zero normalization. This addresses the *root cause* of F1–F6 (all were TUI-scrape fragility): on the report-file path those failure modes cannot arise. F1's gate tolerance + F3/F4/F5 scrape guards remain as the fallback-path hardening.

- 🟢 **A2 — handoff/learnings scoping made repo-canonical + branch-disambiguated (Orca multi-worktree).** `FIXED` 2026-07-22 (feature/189). Under Orca a repo runs in several linked worktrees at once; the old `git rev-parse --show-toplevel` anchor fragmented `docs/handoffs/` + `docs/learnings.md` per-worktree (invisible to siblings, lost on worktree removal), and READ picked "newest by date" with no session/worktree identity (concurrent sessions loaded the wrong handoff). New `handoff/scripts/handoff_paths.py` (single-source, stdlib-only) resolves the **canonical main-worktree root** via `git rev-parse --git-common-dir` → parent, so every worktree reads/writes ONE shared store that survives worktree removal; handoffs are named `YYYY-MM-DD-<branch-slug>-<slug>.md` and READ prefers the current branch's newest (then repo-newest, flagged). `learn.py` now anchors `docs/learnings.md` to that canonical root. Orca-worktree detection added via `worktree-current.isMainWorktree`/`git-common-dir` (not just `.claude/worktrees/`). **Live-proven**: a learning added from a linked worktree landed in the MAIN `docs/learnings.md`; the worktree kept none. 8 new tests (incl. a real `git worktree add`); h-mad suite 373/0 no regression. Granularity = per-repo store + per-worktree/branch identity (NOT per-session, NOT global). **Review-hardened**: the branch filter used a `-{branch}-` substring that false-matched prefix siblings (resuming `feat` grabbed a `feat-ab` handoff — defeating the whole safety property); fixed with a `__` branch|slug separator (branch slugs drop `_`) + anchored match + mtime tiebreak for same-day discriminators; Commit step + Filename-rules updated for the canonical/branch-named path (old cwd-relative `git add` silently no-op'd under a linked worktree); `<skill>` placeholder → resolvable `${CLAUDE_SKILLS_ROOT:-…}`. 10 tests (incl. `feat` vs `feat-ab` regression), suite 383/0.

## Live end-to-end verification sweep (2026-07-22)

- 🟢 **V1 — full handoff + h-mad Orca surface verified against the live `orca` runtime** (not the test stub). All `hmad-dispatch` verbs exercised live: `env` (orchestration on via **auto-detect, no pin**), worktree create→comment→ps→rm lifecycle, `task-create→dispatch→await` (codex emitted a real `worker_done` to the auto-detected coordinator), gate create/resolve/wait lifecycle, `report-wait` file-drop (both agy AND codex), send/read/`--from-start`/alive/clear/interrupt/notify/file-diff/file-open-changed. handoff: `handoff_paths` dir/root/branch-slug/learnings/latest on the real repo, a WRITE→`latest --branch`→find branch-scoped cycle, old-format backward-compat (repo-newest finds it, `--branch` correctly doesn't). h-mad scripts (audit_gate/state_validate/phase7/telemetry) run on real python. A full 7-phase `/h-mad` also ran live this session.
  - **Gap 1 (automations) CLOSED:** `automation-create→list→run→remove` full lifecycle live (create returned id, list found it, run OK, remove OK, gone after). Provider `claude`, `--trigger daily`, `--repo name:skills`.
  - **Gap 2 (report-file audit cycle) CLOSED:** drove a real audit — assembled `audit-prompt.template.md` with `<REPORT_FILE_PATH>` filled, agy did an Axis-A/B/C review (FR-1/FR-2 `implemented-as-written`), wrote CLEAN markdown to the file, `report-wait` read it, `h_mad_audit_gate.py` scored `GATE: PASS` **directly** — no extract, no dedent, no `•`-normalize. Report-file confirmed as the default audit path in a live cycle.
  - **Gap 3 (`wait` reliability) CLOSED:** `hmad-dispatch wait codex` returned rc=0 in 4s (stability check detected idle, not a timeout) on a stable-TUI agent; the Gemini-only `tui-idle` unreliability is structurally covered by report-file's `.done`-marker completion (Gap 2), so the audit path no longer depends on idle-detection.

## Worktree-scoped identity resolution (2026-07-22, post-handoff)

Surfaced live while preparing follow-on #1 (a `/h-mad` report-file run): `hmad-dispatch env` reported **both** `codex -> UNRESOLVED` and `agy -> UNRESOLVED` despite live agy + Codex panes present. Root-caused via systematic debugging against the real `orca terminal list --json`. Both FIXED (h-mad suite 386/0, +3 RED→GREEN tests; live `env` now resolves both).

| ID | Sev | Status | One-line |
|---|---|---|---|
| H1 | 🔴 | FIXED | `_orca_find` matched title/preview across ALL worktrees → 2 panes titled "agy" (skills + HemaSuite) → n=2 → UNRESOLVED; couldn't self-exclude coordinator without a pin |
| H2 | 🔴 | FIXED | Codex pane title = worktree name, preview banner carries NO "codex" literal (only `gpt-5.6-terra`/"Sol") → token match found nothing → UNRESOLVED |

- 🔴 **H1 — resolution not scoped to the coordinator's worktree.** Orca runs one agent set per worktree; with a HemaSuite pane also titled "agy", the global anchored-title match returned 2 candidates → ambiguous → UNRESOLVED. Self-exclusion also required a manual `HMAD_ORCA_COORDINATOR_TERMINAL` (`$self` was empty otherwise, so the coordinator's own pane could match). Fixed: `_orca_find` now resolves the coordinator via `_coordinator` (pin or `ORCA_PANE_KEY` leafId), scopes candidates to that pane's `worktreePath`, and excludes self in BOTH passes. No pane context (manual/tests) → empty scope → global fallback, backward compatible. Live-verified: `agy -> term_92396979` (skills agy, not the HemaSuite one).
- 🔴 **H2 — Codex has no "codex" literal in its Orca metadata.** A user-launched Codex pane is titled after its worktree ("skills") and its preview shows only the model id (`gpt-5.6-terra`) + persona ("Sol") — never "codex". Title Pass-1 misses, and the Pass-2 preview fallback grepped for the bare token. Fixed: per-agent preview signature set in Pass-2 — `codex` → `codex|gpt-[0-9]`, `agy` → `agy|gemini|antigravity`. A collision yields n>1 → UNRESOLVED (safe; never a mis-dispatch). Live-verified: `codex -> term_41f3e488`. **Supersedes F9's workaround** — the `HMAD_ORCA_CODEX_TERMINAL` pin is no longer required for a worktree-local Codex (still overrides).

## Surfaced by the dispatch-resolve-verb `/h-mad` run (2026-07-22, report-file transport validation)

A full 7-phase `/h-mad` (feature `dispatch-resolve-verb`, merged main `7cfb331`) exercised report-file transport for every verdict (4 audit cycles + Codex RED/GREEN + agy 5e + agy 6a-prime) — the mechanism worked end-to-end with zero scrape. Two operational findings surfaced; **both FIXED 2026-07-22** (h-mad suite 408/0, live-verified against the real Orca runtime).

| ID | Sev | Status | One-line |
|---|---|---|---|
| H3 | 🟡 | FIXED | `report-wait` hit a transient `syntax error` polling `hmad-dispatch.sh` while Codex was mid-save on that same wrapper — extracted the poll loop to standalone `scripts/h_mad_report_wait.py`; poll it directly to stay wrapper-independent |
| H4 | 🟡 | FIXED (mitigated) | Codex auto-detect decays mid-run (banner scrolls off preview) — added `pin-agents` verb + session pin file + env→file→detect precedence; `pin-agents` **fails loud** if it can't resolve. RESIDUAL: Codex has no stable auto-identity in Orca (title=worktree, preview volatile), so the durable path is an explicit pin captured at launch — auto-detect is convenience-only, not solved. |

- 🟡 **H3 — poll-vs-edit race on the dispatch wrapper.** During Phase 5e GREEN, Codex was editing `h-mad/scripts/hmad-dispatch.sh` to add `_cmd_resolve`; a concurrent `hmad-dispatch report-wait …` (which sources that wrapper) fired while the file was mid-save and printed `line 620: syntax error near unexpected token ')'` (rc=2). `bash -n` was clean seconds later — the report file + `.done` marker were correct; only the poller's own wrapper was momentarily unparseable. Harmless here (retry succeeded) but a real hazard whenever the implemented module IS the coordinator's transport. **FIXED**: the poll loop is now the standalone stdlib script `h-mad/scripts/h_mad_report_wait.py`; `_cmd_report_wait` delegates to it, and when the dispatched implementer is editing `hmad-dispatch.sh` itself the coordinator polls `python3 h_mad_report_wait.py <path> …` directly — never re-parsing a half-saved wrapper. 6 dedicated tests (`test_h_mad_report_wait.py`) + a guard that the script shells out to nothing. Live-verified (direct + delegated).

- 🟡 **H4 — Codex identity by preview is not durable.** `env`/`resolve` resolved `codex -> term_41f3e488` at Phase-5 start (preview carried `gpt-5.6-terra`), but mid-run `resolve codex` returned UNRESOLVED: after Codex did work, its preview window showed report/output text and the model-id banner had scrolled off, so H2's `codex|gpt-[0-9]` preview alias matched nothing. H2 remains correct for a *fresh* Codex pane; it cannot survive banner decay. The run pinned `HMAD_ORCA_CODEX_TERMINAL` and proceeded. **FIXED (mitigated, not a true auto-fix)**: added a `pin-agents` verb that resolves codex+agy once and freezes the handles into a session pin file (`${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}`, gitignored); `_resolve_target`'s orca branch reads it with precedence **env pin → pin file → auto-detect**, so a frozen handle survives banner decay while an explicit env pin overrides. Crucially `pin-agents` now **fails loud (rc=1)** naming any unresolved agent + the env var to set — the earlier silent rc=0 partial was itself a bug (a run could proceed believing Codex was addressable when it wasn't). 5 tests; live-verified both the frozen-handle read AND the fail-loud path.
  **RESIDUAL — Codex auto-detection is NOT solved (Orca limitation).** `pin-agents` can only freeze a handle it can resolve *at pin time*; if Codex's banner has already decayed and no env pin is set, `pin-agents` fails to resolve it too (verified live: preview `"sol"`, `env` → `codex -> UNRESOLVED`, `pin-agents` pinned agy only + rc=1). Orca's `terminal list` exposes no field naming the running program, and Codex's title (=worktree) and preview (volatile) carry no stable `codex` signal — so there is no reliable post-hoc auto-identity. **The durable path is an explicit `HMAD_ORCA_CODEX_TERMINAL` pin captured while identity is known (right after launching Codex, before it works).** SKILL Phase-5 preflight + `agent-substrate.md` now say this explicitly. A genuine auto-fix would need Orca to expose the running command/process per terminal (feature request), or h-mad to own the Codex launch and record its handle at spawn. [[F9]] [[H2]]

## H5 — Codex has no resolvable identity in Orca; `terminal rename` does not help (2026-07-22)

Investigating why a **manual tab rename to "Codex - skills repo"** (set at session start) did not make `resolve codex` work.

| ID | Sev | Status | One-line |
|---|---|---|---|
| H5 | 🟡 | MITIGATED + FEATURE-REQUEST | `orca terminal rename` sets a tab-title layer that `terminal list --json .title` does NOT surface; `.title` is the OSC title the running program emits (Codex → cwd basename `skills`, agy → `agy`), so no rename yields a `codex` signal. Mitigation: `pin <agent> <handle>` verb + explicit-pin workflow. True fix needs an Orca API change. |

- 🟡 **H5** — **Root cause of the whole Codex-identity class.** `_orca_find` matches `.title` from `orca terminal list --json`. That field is the terminal's OSC/derived title emitted by the *running program*: agy emits `agy` (resolvable), Codex emits its cwd basename `skills` (not resolvable), and the preview banner decays (H2/H4). A user's `orca terminal rename --terminal <h> --title "Codex …"` returns `{"ok":true}` but **`.title` stays `skills`** and `resolve codex` still finds 0 candidates — verified live this session. So rename operates on a *different* (tab-UI) layer that the JSON never exposes. **Consequence**: there is no title- or preview-based signal that reliably or durably identifies Codex.
  - **Mitigation shipped**: `hmad-dispatch pin <codex|agy> <handle>` records a handle in the session pin file in one command (+ `pin-agents` fail-loud, H4). The operator captures Codex's handle from `orca terminal list` (ideally at launch, before decay) and pins it; resolution then reads it deterministically. This is the durable path today.
  - **Feature request (Orca-side; not fixable in this repo)**: make Codex reliably auto-identifiable — EITHER surface the tab/custom title (what `terminal rename` sets) in `terminal list --json`, OR add a field naming the running command/process per terminal. Either would let `_orca_find` identify Codex without a manual pin. Until then, `pin`/`pin-agents` + explicit handle is the contract. **Filed at `stablyai/orca`** (2026-07-22): https://github.com/stablyai/orca/issues/9870 — source draft: `docs/orca-feature-request-terminal-identity.md` (repro + both API options).
  - **Launch-owned path — SHIPPED** (`608a7da`+): `hmad-dispatch launch <codex|agy>` runs `orca terminal create --command … --json` and captures `.result.terminal.handle` from the **create response**, pinning it at spawn — identity at t=0, never title/preview. Live-verified end-to-end (create → capture → pin → `resolve` reads it). This is the zero-manual durable fix when h-mad owns the launch; reuse of an operator-launched pane still uses `pin`/`pin-agents`. The Orca feature request (below) remains the fix for the auto-detect-an-existing-pane case.

## Surfaced by the cycle-telemetry-fidelity `/h-mad` run (2026-07-23)

Found by **using** the skill on a real feature (Waves 1 of the h-mad remediation sequence, run in
`~/orca/skills` from a coordinator session whose cwd was a *different* repo), not by reviewing it.
All are unfixed. One candidate finding was investigated and **disproven** — recorded below so it
is not re-filed.

| ID | Sev | Status | One-line |
|---|---|---|---|
| J1 | 🔴 | MONITORING | `launch <agent>` pins the create-response handle, which is NOT the handle the pane ends up with — reproduced 2× |
| J2 | 🟡 | MONITORING | pin file is cwd-relative, so a cross-repo run silently reads another project's pins and reports UNRESOLVED |
| J3 | 🟡 | MONITORING | `read --lines N` on a TUI can render a minutes-stale frame; only `--from-start` was truthful |
| J4 | 🟡 | MONITORING | F8 re-opened: the jsonschema *remedy message* shipped, the dependency gap did not close |
| J5 | 🟢 | MONITORING | `state_write --claim` on a fresh feature fails without `--create`; SKILL's `start_fresh` route omits it |
| J6 | — | **DISPROVEN** | "`clear <agent>` exits the Antigravity pane" — it does not; the observed exit was an operator closing the tab |
| J7 | 🟢 | **RESOLVED** | F13 residual: the pin **file** leaked into `test_hmad_dispatch.py`. Fixed by Wave 2 (`787aecf`) — `run()` injects a per-invocation never-created path; suite 530 passed identical with and without the pin file |
| J8 | 🟡 | **SCHEDULED — Wave 4** | `elapsed_min` in every telemetry row is ~56 years (`29744612.6`). Root cause: `h_mad_state_write.py:138` defaults `started_ts` to a hardcoded `1970-01-01T00:00:00Z` sentinel |
| J9 | 🟢 | MONITORING | `test_alive_cmux_true` failed once then passed on two consecutive full runs — probes the real `cmux` binary, so it is environment-dependent |
| J10 | 🟡 | **SCHEDULED — Wave 4** | A Codex dispatch returned `STATUS: DONE_WITH_CONCERNS` while naming no concern anywhere in its report — a verdict declaring doubt without stating it is unactionable |

- 🔴 **J1 — `launch` captures a handle the created pane never has.** `hmad-dispatch launch agy
  --worktree path:…/skills` read `term_01f69e2d…` from the `orca terminal create` response and
  tried to pin it; the pane that materialized was `term_56c103c5…`. The pin was **correctly**
  refused (`no such terminal in 'orca terminal list'`) — the 912b93a liveness check caught a
  genuinely wrong handle, not a race. Reproduced independently a second time the same session via
  a direct `orca terminal create`: response said `term_cb30d7a7…`, actual pane was
  `term_e46dc00d…`. **Consequence:** H5's "launch owns the spawn, so identity is captured at t=0,
  never title/preview" does not hold — the create-response handle is not the pane's handle, so
  `launch` currently cannot pin at all and always fails loud. The only working identification was
  content-verification against `terminal list` (`Welcome to the Antigravity CLI`), which is
  exactly what H5 set out to eliminate. **Fix direction:** after `create`, resolve the handle from
  `terminal list` (by `worktreePath` + recency, or by matching the created tab/leaf id) rather than
  trusting `.result.terminal.handle`; or determine why the two differ and whether one is a
  pre-adoption placeholder. [[H5]] [[F9]]
- 🟡 **J2 — the session pin file is cwd-relative.** `${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}`
  resolves against the *current directory*, so driving a `/h-mad` run in repo A from a coordinator
  session sitting in repo B reads B's pin file. Observed: `hmad-dispatch read agy` from the wrong
  cwd reported `orca terminal for 'agy' resolved to 0 candidates in worktree
  /Users/kimhawk/orca/HemaSuite; pin HMAD_ORCA_AGY_TERMINAL` — two wrong assumptions compounding,
  since H1's coordinator-worktree scoping also anchors on the *coordinator's* worktree, not the
  target repo's. Cross-repo runs are a normal mode (this whole feature was one). **Fix direction:**
  resolve the pin file against the project root the run is operating on, and/or make `env` print
  which pin file it read. Workaround today: export `HMAD_ORCA_*_TERMINAL` explicitly.
- 🟡 **J3 — a tail read of a TUI is not evidence of pane state.** `hmad-dispatch read agy
  --lines 12..40` showed a boot screen (`You are currently not signed in`, spinner) unchanged
  across two minutes and three polls; I was one step from declaring the CLI wedged and relaunching
  it. `read --from-start` showed the truth: a ready `>` prompt, `Gemini 3.1 Pro (High)`, cwd
  `~/orca/skills`. The tail was rendering an overdrawn region of the frame. This is F5's mechanism
  with a new and more dangerous symptom — F5 is written up as "scrollback < report length" (you
  lose the *end* of a report), but here the tail was stale about the pane's *readiness*, which
  drives a relaunch decision. **Fix direction:** SKILL's readiness/liveness checks should specify
  `--from-start` (or a full-buffer read) rather than `read --lines N`. [[F5]]
- 🟡 **J4 — F8 re-opened.** The actionable remedy message shipped and works, but the gap it
  describes is unchanged: `python3` on this machine (homebrew 3.14) has no `jsonschema`, so every
  `h_mad_state_write.py` / `h_mad_state_validate.py` / `h_mad_state_staleness.py` call in a run
  exits 2 until the operator manually substitutes `/opt/anaconda3/bin/python3`. Hit twice in the
  first five minutes of this run. A better error message is not a fix for a missing dependency.
  **Fix direction:** vendor a minimal validator, degrade gracefully to the historical tier when
  `jsonschema` is absent, or document a required interpreter in the SKILL preflight so it is a
  stated prerequisite rather than a per-call surprise.
- 🟢 **J5 — `--claim` cannot create.** SKILL's `start_fresh` route prints
  `h_mad_state_write.py … --feature <f> --claim "<session-id>"`, but on a feature that does not
  exist yet that exits 2 with `ERROR: no such feature`. Every first-time claim — i.e. every
  `start_fresh` — fails as documented. `--create --claim <id>` works. **Fix direction:** either
  make `--claim` imply `--create`, or correct the SKILL snippet.
- ⬜ **J6 — DISPROVEN: `clear <agent>` does not exit the Antigravity pane.** Initially filed from
  an observation that `hmad-dispatch clear agy` was followed within 15s by `status: exited` on
  that handle. The operator then reported having closed that tab manually. Verified with a
  throwaway pane: created a fresh agy terminal, ran `hmad-dispatch clear agy` against it, and 15s
  later the pane was still `status: running` with the cursor advanced 37→61 (the `/clear` was
  processed and the frame redrawn). **`clear` behaves as documented.** Recorded so the
  correlation is not re-filed as causation by a future run. Method note: the throwaway-probe
  pattern (`docs/skill-candidates.md`, recurrence 2) is what settled it.

- 🔴 **J7 — F13 is only half closed: the pin FILE leaks where the env vars no longer do.** F13 added
  every `HMAD_ORCA_*` env var to the strip-list in `test_hmad_dispatch.py::run()`. The session pin
  file (`.h-mad/orca-pins.env`) is a **second** leak channel that the strip does not touch: it lives
  in the repo working directory, and the resolver reads it with precedence env → file → auto-detect.
  Measured on the `cycle-telemetry-fidelity` Phase-5f suite run: **18 failed / 459 passed**. Moving
  `.h-mad/orca-pins.env` aside and re-running: **477 passed / 0 failed**. Seventeen of the eighteen
  were pin-file leakage — `test_orca_identity_*`, `test_resolve_agy_*`, `test_agy_does_not_take_a_pane_running_codex`,
  `test_codex_never_resolves_from_an_inherited_title`, and the agent-signature tests.
  **Why this is worse than a test nuisance:** SKILL.md Phase 5 preflight *requires*
  `hmad-dispatch pin-agents` ("a run must not proceed with Codex unpinned"), and Phase 5f *requires*
  running the full suite. Following the protocol therefore guarantees 17 failures at 5f, on every
  run, in the repo whose own tests they are. An orchestrator that trusts the suite reads a real
  regression signal as noise, or worse, deletes its pins to get green and dispatches into nothing.
  **Fix direction:** point the pin file at a per-session path outside the repo (or honour a
  `HMAD_ORCA_PIN_FILE` override in the test harness and set it to a tmp path in `run()`), so pinning
  and testing stop being mutually exclusive. Workaround used this session: keep the pin file absent
  and pass `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL` as env vars, which the resolver
  prefers anyway. [[F13]] [[J2]]

- 🟡 **J8 — `elapsed_min` is nonsense in every recorded row.** Surfaced while verifying the
  cycle-telemetry-fidelity feature against the real `.h-mad/telemetry.jsonl`: all three rows carry
  `elapsed_min` ≈ `29744612.6`, i.e. about **56 years**, so `started_ts` is being parsed as roughly
  the epoch rather than the feature's real start. Pre-existing and untouched by that feature (it
  changed only the two cycle counters). Two consequences: the elapsed column is meaningless, and at
  11 characters it overflows its `:>9` field so the summary table's last two columns visibly
  misalign. **ROOT CAUSE FOUND (2026-07-23, Wave 2).** Not a parse failure — the reader is fine and the
  stored value is literally the epoch. `h_mad_state_write.py:138` reads

  ```python
  record["started_ts"] = started_ts or "1970-01-01T00:00:00Z"
  ```

  so every feature created without an explicit `--started-ts` is stamped with a hardcoded epoch
  sentinel. Confirmed against `.h-mad/telemetry.jsonl`: the four pre-Wave-2 rows all carry
  `started_ts='1970-01-01T00:00:00Z'` / `elapsed_min≈29744612`, while `preflight-signal-discipline`
  — the one feature created with `--started-ts` passed explicitly — carries
  `started_ts='2026-07-23T01:07:14Z'` / `elapsed_min=110.3`.

  **Fix direction:** default to the current UTC time rather than the epoch (`started_ts or
  datetime.now(timezone.utc).isoformat()`). A sentinel that is a *valid* timestamp cannot be
  distinguished from real data downstream — which is why this survived as "the reader must be
  broken" for as long as it did. Optionally also have `cmd_record` render an implausible elapsed as
  `?m`, but that treats the symptom. Existing rows stay wrong; they are append-only history.
  **Scheduled: Wave 4** (`docs/01-plan/h-mad-remediation-sequence.md` §Wave 4, "Defects → scripts").
- 🟡 **J10 — `DONE_WITH_CONCERNS` with no concerns stated.** Observed twice during Wave 2
  (`preflight-signal-discipline` Tasks 1 and 2). `references/codex-implementer-prompt.md` defines the
  verdict as "work is complete but you have doubts", and the report format asks for
  "Concerns / blockers / context needed (if any)". Task 1's report did name its concern (unrelated
  working-tree files, correctly flagged rather than assumed). Task 2's did not: the body contained
  only positive verification facts, so the orchestrator was handed a doubt it could not act on and
  could not distinguish from `DONE`.

  **Why it matters:** the verdict is machine-parsed and gates the module. `DONE_WITH_CONCERNS` is
  the designed middle rung — a worker that reaches for it conservatively, without content, degrades
  it to noise, and the safe response (verify everything independently) is exactly the cost the
  verdict exists to avoid. In this instance independent verification was done anyway and found
  nothing, so no defect shipped.

  **Fix direction:** make the concern mandatory in the template — "if you report
  `DONE_WITH_CONCERNS` you MUST list at least one concern; if you cannot name one, report `DONE`" —
  and consider having `h_mad_extract_verdict.py` treat a `DONE_WITH_CONCERNS` whose report carries no
  concerns section as an operational error rather than a verdict, so silence cannot masquerade as
  nuance. **Scheduled: Wave 4** (`docs/01-plan/h-mad-remediation-sequence.md` §Wave 4,
  "Defects → scripts"). [[J9]]

- 🟢 **J9 — `test_alive_cmux_true` is environment-dependent.** Failed once during a Phase-5f full
  run, then passed on two consecutive full runs of the identical suite with no change in between.
  It probes the real `cmux` binary, so its result depends on machine state rather than on the code
  under test. Not order-dependence — it passes in isolation and in the same 498-test set that
  failed it once. **Fix direction:** stub the substrate probe as the neighbouring tests do, so the
  suite does not have a test whose verdict depends on whether a terminal multiplexer happens to be
  responsive.

**Also observed (evidence for existing entries, not new IDs):** `orca terminal create --title
"agy-probe"` does not stick — `terminal list` reports `title: agy`, the program's own OSC title.
Independent confirmation of H5's core claim that `.title` reflects what the program emits and that
caller-supplied titles are not surfaced. Filed upstream as stablyai/orca#9870.

**In flight, not a monitoring item:** `audit_cycles`/`iterate_cycles` are seeded and never
incremented (both drift warnings dead). Being fixed by the `cycle-telemetry-fidelity` feature —
see `docs/01-plan/h-mad-remediation-sequence.md` Wave 1.

---

## Surfaced by the preflight-read-enforcement `/h-mad` run (2026-07-23, Wave 3 dogfood)

Found by **running** Waves 1–2 through a real 7-phase feature in `~/orca/skills` — the Wave-3
dogfood whose purpose is exactly this (`docs/01-plan/h-mad-remediation-sequence.md` §Wave 3,
closing G-b/G-d). All three are prose-vs-tooling mismatches: each instruction was doc-verified and
had never been executed. All unfixed.

| ID | Sev | Status | One-line |
|---|---|---|---|
| J11 | 🟡 | MONITORING | `SKILL.md` twice orders "record the substrate + agent mapping via `h_mad_telemetry.py`"; the script has no such argument and the row schema has no such field |
| J12 | 🟡 | MONITORING | `h_mad_assemble_audit.py` returns `ASSEMBLE: PASS` for a prompt it simultaneously predicts will fail — the oversize warning is an unread line beside a passing token |
| J13 | 🟢 | MONITORING | The documented remedy for an oversize audit prompt ("split by FR group") does not reduce size when the design is the dominant term |

- 🟡 **J11 — the mandated substrate record is unexecutable.** `SKILL.md` says, in *both* §"Phase 5
  (Implementation) sub-steps" and §"Audit prompt assembly": "Record the printed substrate + agent
  mapping via `scripts/h_mad_telemetry.py` so the run log states which environment it dispatched
  under." `h_mad_telemetry.py record` accepts only `--feature`, `--state`, `--out`, `--docs-root`,
  and the row it writes (`h_mad_telemetry.py:62-76`) has keys `schema_version`, `feature`,
  `recorded_ts`, `completed_ts`, `started_ts`, `last_completed_phase`, `audit_cycles`,
  `iterate_cycles`, `halt_reason`, `elapsed_min` — no substrate, no agent mapping. The command also
  refuses a feature absent from state and is shaped as a Phase-7 close-out recorder, so it cannot
  serve a Phase-5-start instruction even in principle. **Consequence:** no run log has ever recorded
  which substrate it dispatched under, and nothing surfaced that, because an orchestrator either
  skips the step or calls `record` and reads its cycle-count output as success. **Fix direction:**
  either add a `substrate`/`agents` field plus the arguments to write it, or — cheaper and honest —
  delete the instruction from both places and state that substrate is captured in the phase report.
  Do not leave prose ordering an impossible call. [[J8]]
- 🟡 **J12 — `ASSEMBLE: PASS` is returned for a prompt predicted to fail.** Assembling this
  feature's design audit printed
  `ASSEMBLE: PASS /tmp/…_design_cycle1.txt 54766B (53.5 KB)` followed by a separate warning line:
  `! 53.5 KB is past the measured 49 KB reviewer cliff … a silent empty reply is the expected
  failure`. `SKILL.md` §"Audit prompt assembly" mandates asserting **`ASSEMBLE: PASS`** before
  dispatch — and that assertion succeeds here. An orchestrator following the documented contract
  exactly dispatches a prompt the script itself expects to come back empty. This is the *same defect
  class* the `PREFLIGHT:` token was created to fix in Wave 2: a correct signal that nothing is
  obliged to consume, sitting beside a token that is. **Fix direction:** fold size into the verdict
  rather than beside it — either `ASSEMBLE: HALT <phase>:oversize` (consistent with the script's
  existing refuse-to-emit stance for preflight failures, and it already declines to write a halted
  prompt), or a distinct third token such as `ASSEMBLE: PASS_OVERSIZE` that the mandated read must
  branch on. A warning adjacent to PASS is worth exactly what the unread `STALE` line was worth.
  [[J7]]
- 🟢 **J13 — "split by FR group" does not shrink an oversize design audit.** `SKILL.md` step 5.5
  prescribes, for a prompt past the reviewer cliff: "split the audit by FR group and run Axis C over
  each group in turn." Measured on this feature's design audit: total 50.9 KB, of which design
  22.4 KB + plan 10.3 KB + template 8.0 KB + base/project invariants 5.5 KB = **46.2 KB is fixed
  cost carried by every split**. Only the spec (4.7 KB after the documented FR-only trim) divides,
  so a two-way split yields ~48.5 KB per half — roughly 2 KB of relief for two dispatches, two audit
  files and two gate runs. The remedy silently assumes the *spec* is the marginal term; whenever the
  design dominates (the normal case for a detailed design) it does not work. Note the same step
  correctly forbids the reduction that would work — trimming the design — because `absent` becomes
  undetectable and that is what Axis C exists to catch. **Fix direction:** state the real options
  (shorten the design, or split the *feature*), and give the fixed-vs-divisible arithmetic so the
  reader can tell which applies. [[J12]]

**Also measured (evidence, not a new ID):** the ~49 KB reviewer cliff did **not** reproduce on this
host. `references/agent-substrate.md` records 49,273 B emitted normally and 53,066 B silent, and
asks that the boundary be re-measured per host. A 52,168 B design audit delivered by **file
indirection** (`send` stages the path; the agent `Read`s it itself, twice) was answered normally by
Antigravity CLI 1.1.5 / Gemini 3.1 Pro. The original measurements may have been of a different agent
build, or the cliff may be a property of TUI paste rather than of agent-side file reads — the two
delivery modes were not distinguished when the number was recorded. Worth re-measuring deliberately
before anyone trims a design to satisfy it.

---

_Append new findings below as later runs surface them. Flip Status + link the commit when actioned._
