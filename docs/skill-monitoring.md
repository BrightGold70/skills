# Skill Monitoring — bugs & improvement points (standing)

Live registry of known bugs and improvement points in the `h-mad` / `handoff` skills, surfaced during real `/h-mad` runs. **Not auto-fixed** — each entry is under monitoring until deliberately actioned. Action a batch as its own `/h-mad` feature when priority warrants.

**Severity:** 🔴 bug (correctness) · 🟡 process/robustness · 🟢 improvement/opt

**The `F`/`G`/`H`/`A`/`V`/`P` rows are a HISTORICAL findings log, not the standing registry**
(decided 2026-08-26, after reading all 33). They predate the `Status:` lifecycle and deliberately do
not carry it. Three things a reader needs, because each has already misled one:

- **The emoji is SEVERITY at the time of filing, never lifecycle.** `F11`–`F13` are 🔴 *and* FIXED —
  they appear once in the resolution table below and again as bullets with their original detail.
  Reading 🔴 as "open" makes eleven closed rows look live.
- **`F1`–`F13` have their own `Status` column** in the table below, which states "All F1–F13
  resolved". `F14`–`F18`, `G`, `H`, `A` record resolution inline instead; `G5`, `H5` and `V1` are a
  mechanism note, a root-cause explanation and a verification record rather than work; `P1` was
  explicitly declined as pre-existing. **Re-read on 2026-08-26: none of the 33 is live open work.**
- **To make something trackable, promote it to a `J` entry** — that is what the standing registry is
  for. Do **not** answer this by widening the census parser: it would silently reclassify all 33
  closed rows as open, which is the opposite of what reading them shows.

**Lifecycle** — every `J` entry ends with exactly one machine-readable status line, written as
the word `Status:` followed by one of these in backticks:

| word | meaning |
|---|---|
| `MONITORING` | tracked, still unfixed — the only word that means open work |
| `PLANNED` | scheduled, not yet started |
| `FIXED` | remedied in code; link the commit |
| `WONTFIX` | deliberately not built, with the reason — kept so it is not re-proposed |
| `RESOLVED` | closed without a fix here: upstream, or by another entry's feature |
| `DISPROVEN` | the filed behaviour does not occur. **Note J9**: a disproven *cause* is not a disproven *symptom*, and the entry must say which was refuted |
| `SUPERSEDED` | absorbed by a later entry that reproduced it and named the mechanism |

**Count `MONITORING`, not the absence of a word.** Before 2026-08-22 only 9 of 40 entries carried a
`Status:` line, so any census over this file measured the convention rather than the backlog — and
one did: a regex sweep reported J18 as open when its own body said "Fixed", because the note that
follows it contains the word MONITORING. `grep -c` also exits 1 on no match, which reads as a clean
zero if the exit code is ignored. All 40 are now classified.

**Numbering gaps (J31–J33) are deliberate and must stay:** J-ids are referenced from
commit messages, handoffs and `[[J2]]`-style cross-links, and renumbering would silently repoint
every one of them at a real, wrong entry.

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
| F8 | 🟡 | **FIXED** (via J4) | jsonschema missing — closed by bundling a stdlib validator; the state scripts no longer need a third-party package |
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
- 🟡 **F8 — `python3` (homebrew 3.14) lacks `jsonschema`; state writer errors `ERROR: jsonschema is required`.** PEP-668 blocks `pip install`. ~~Worked around with `/opt/anaconda3/bin/python3` (jsonschema 4.25.1 + pytest 8.3.5).~~ **The recorded workaround is dead: `/opt/anaconda3/bin/python3` does not exist on this machine (2026-08-09).** An interpreter survey found only homebrew 3.14.6 and system 3.9.6, so any doc or habit pointing at the anaconda path is stale. Re-confirmed the same day from the consumer side: `jsonschema` is also an **undeclared test dependency** of HemaSuite's h-mad consumer suite — `tests/test_h_mad_state_schema.py:8` imports it and no manifest declares it, so collection fails on a clean venv until it is installed by hand. **Fix (unchanged, now with a second consumer arguing for it):** h-mad state scripts need a documented interpreter/venv, or a graceful degrade + install hint when jsonschema is absent.
- 🟡 **F9 — Codex Orca terminal title is the worktree name** (`skills`), so `_orca_find codex` can't title-match; must pin `HMAD_ORCA_CODEX_TERMINAL`. (Already known: `project_orca_adaptation_backlog`; re-confirmed live.)

## handoff

- 🟡 **F10 — `~/.claude/skills/handoff` was a real dir, NOT a symlink to the repo** (unlike `h-mad`). `FIXED` 2026-07-22: replaced with a symlink → `/Users/kimhawk/orca/skills/handoff` (pre-install backup at `~/.claude/handoff-preinstall-backup-2026-07-22`). Repo changes are now live in the installed skill.

- 🔴 **F15 — HANDOVER Step 2's state-file locator silently failed open.** `FIXED` `f104cc4`. The documented `ls <repo>/**/docs/.bkit-memory.json` relies on `globstar`, which **bash leaves off by default** — `**` collapses to a single `*`, so a real state file two directories down was not matched. `$STATE` came back empty, Step 2 concluded "nothing is claimed", and the release was skipped entirely — in the step the skill itself calls "the one whose absence is silent", producing the exact deadlock it exists to prevent, with no error. Measured in both shells: bash misses the depth-2 file; zsh finds it but on *no* match prints `no matches found` past `2>/dev/null`, because the failure is the shell's own glob expansion. Replaced with `find`; pinned by `test_no_recursive_glob_in_any_fenced_block`.
- 🟡 **F16 — fenced blocks used shell variables no longer in scope.** `FIXED` `f104cc4`. Shell state does not survive between tool calls, so `$HP`/`$FILE`/`$LEARN` in §Commit and `$STATE` in Step 3.5 / HANDOVER Step 2 were all empty at execution. Worst case measured: an empty `HP` makes `ROOT` empty, `ROOT` then never equals the toplevel, and §Commit takes the "linked worktree" branch that **deliberately skips committing** — on the main worktree, reporting the skip as correct. Blocks are self-contained or take literal paths now; pinned by `test_every_fenced_block_defines_the_shell_vars_it_uses`.
- 🟡 **F17 — two steps prescribed `orca worktree list` against the skill's own rule.** `FIXED` `f104cc4`. The skill states twice that all Orca access goes through `hmad-dispatch`, but `childWorktreeIds` lives only in `orca worktree list` and **no wrapper verb exposed it** (`worktree-ps` is a different orca subcommand — a compact orchestration summary). The rule was unsatisfiable rather than merely broken. Added `hmad-dispatch worktree-list` (4 tests, RED first; live-smoked against the real CLI: 4 worktrees, `childWorktreeIds` present) and repointed both steps; pinned by `test_orca_is_only_ever_reached_through_the_wrapper`.
- 🟢 **F18 — example handoff filenames omitted the `__` branch separator.** `FIXED` `f104cc4`. The resume report and the INDEX entry both showed the pre-`__` shape, teaching a filename READ's exact-branch match cannot find. Pinned by `test_example_handoff_filenames_carry_the_branch_separator`.

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
  - **Feature request (Orca-side; not fixable in this repo)**: make Codex reliably auto-identifiable — EITHER surface the tab/custom title (what `terminal rename` sets) in `terminal list --json`, OR add a field naming the running command/process per terminal. Either would let `_orca_find` identify Codex without a manual pin. **Filed at `stablyai/orca`** (2026-07-22): https://github.com/stablyai/orca/issues/9870 — source draft: `docs/orca-feature-request-terminal-identity.md` (repro + both API options). **SUPERSEDED — issue CLOSED 2026-07-23 as completed:** the second option (a field naming the running program per pane) already existed in `orca worktree ps` as `agents[].agentType` keyed by `paneKey`. `_orca_find` Pass 0 now joins it, so Codex IS auto-identifiable without a manual pin. See J16. `pin`/`pin-agents` remain the most durable path for a long run, but they are no longer the only one.
  - **Launch-owned path — SHIPPED** (`608a7da`+): `hmad-dispatch launch <codex|agy>` runs `orca terminal create --command … --json` and captures `.result.terminal.handle` from the **create response**, pinning it at spawn — identity at t=0, never title/preview. Live-verified end-to-end (create → capture → pin → `resolve` reads it). This is the zero-manual durable fix when h-mad owns the launch; reuse of an operator-launched pane still uses `pin`/`pin-agents`. The Orca feature request (below) remains the fix for the auto-detect-an-existing-pane case.

## Surfaced by the cycle-telemetry-fidelity `/h-mad` run (2026-07-23)

Found by **using** the skill on a real feature (Waves 1 of the h-mad remediation sequence, run in
`~/orca/skills` from a coordinator session whose cwd was a *different* repo), not by reviewing it.
All are unfixed. One candidate finding was investigated and **disproven** — recorded below so it
is not re-filed.

| ID | Sev | Status | One-line |
|---|---|---|---|
| J1 | 🔴 | **FIXED** | `launch <agent>` pins the create-response handle, which is NOT the handle the pane ends up with — reproduced 2× |
| J2 | 🟡 | **FIXED** | pin file is cwd-relative, so a cross-repo run silently reads another project's pins and reports UNRESOLVED |
| J3 | 🟡 | **FIXED** | `read --lines N` on a TUI can render a minutes-stale frame; only `--from-start` was truthful |
| J4 | 🟡 | **FIXED** | F8 re-opened: the jsonschema *remedy message* shipped, the dependency gap did not close |
| J5 | 🟢 | **FIXED** | `state_write --claim` on a fresh feature fails without `--create`; SKILL's `start_fresh` route omits it |
| J6 | — | **DISPROVEN** | "`clear <agent>` exits the Antigravity pane" — it does not; the observed exit was an operator closing the tab |
| J7 | 🟢 | **RESOLVED** | F13 residual: the pin **file** leaked into `test_hmad_dispatch.py`. Fixed by Wave 2 (`787aecf`) — `run()` injects a per-invocation never-created path; suite 530 passed identical with and without the pin file |
| J8 | 🟡 | **FIXED** `ab3657e` | `elapsed_min` in every telemetry row is ~56 years (`29744612.6`). Root cause: `h_mad_state_write.py:138` defaults `started_ts` to a hardcoded `1970-01-01T00:00:00Z` sentinel |
| J9 | ⬜ | **DISPROVEN** | `test_alive_cmux_true` failed once then passed on two consecutive full runs — probes the real `cmux` binary, so it is environment-dependent |
| J10 | 🟡 | **FIXED** `ab3657e` | A Codex dispatch returned `STATUS: DONE_WITH_CONCERNS` while naming no concern anywhere in its report — a verdict declaring doubt without stating it is unactionable |

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

  **FIXED 2026-07-23 -- reproduced a third time first, which characterised it.** A direct probe
  matching `launch`'s exact call shape: create said `term_d1f7a348...`, the pane that materialised
  was `term_f0966e2b...`, and **the create-response handle never appeared in `terminal list` at
  all**, at any point. So it is not a race and not a rename -- it is a pre-adoption placeholder,
  the second of the two hypotheses above.

  The same probe showed the fix: `.result.terminal.paneKey` **is** present in the create response
  and **is** the `<tabId>:<leafId>` that J16 joins on, and it resolved the live handle in under 5
  seconds. `launch` now creates, polls `terminal list` for that key (`HMAD_LAUNCH_RESOLVE_TIMEOUT`,
  default 20s), and pins the handle it finds. Identity is still owned at spawn -- it is just read
  from the field that survives adoption.

  Both failure paths refuse rather than guess: no `paneKey` in the response, or the key never
  appearing. Guessing by worktree+recency could pin a bystander pane, and the old behaviour already
  proved what a wrong pin costs -- every later dispatch vanishes into a handle that does not exist.

  **The existing test asserted the create-response handle was pinned** -- it encoded J1 as correct
  behaviour, exactly as J17's tests did. Rewritten.

  Mutation testing caught one more: deleting the missing-`paneKey` guard left the test passing,
  because the poll loop then timed out and *its* message also contains "paneKey". The test now
  asserts the specific branch -- 21.9s of wasted polling had been wearing a green test as a
  disguise.

  **Dogfooded live:** `hmad-dispatch launch codex` pinned `term_2ff2ec1f...`, which `terminal list`
  confirms and `hmad-dispatch alive codex` reports live. H5's "launch owns the spawn" claim holds
  for the first time. [[J16]]
  Status: `FIXED` 2026-07-23 — see the FIXED note in this entry.
- 🟡 **J2 — the session pin file is cwd-relative.** `${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}`
  resolves against the *current directory*, so driving a `/h-mad` run in repo A from a coordinator
  session sitting in repo B reads B's pin file. Observed: `hmad-dispatch read agy` from the wrong
  cwd reported `orca terminal for 'agy' resolved to 0 candidates in worktree
  /Users/kimhawk/orca/HemaSuite; pin HMAD_ORCA_AGY_TERMINAL` — two wrong assumptions compounding,
  since H1's coordinator-worktree scoping also anchors on the *coordinator's* worktree, not the
  target repo's. Cross-repo runs are a normal mode (this whole feature was one). **Fix direction:**
  resolve the pin file against the project root the run is operating on, and/or make `env` print
  which pin file it read. Workaround today: export `HMAD_ORCA_*_TERMINAL` explicitly.

  **FIXED 2026-07-23.** `_pin_file` now resolves in three branches: an explicit `HMAD_ORCA_PIN_FILE`
  wins outright; otherwise the default anchors to the **enclosing git repository**
  (`git rev-parse --show-toplevel`), which is where `.h-mad/` lives by convention; outside a repo it
  keeps the old cwd-relative behaviour rather than inventing a location. And `env` now prints
  `pin file: <path>` — J2's core complaint was that the wrong file was read *silently*, so naming it
  on the line an operator already reads is half the fix.

  **Blast radius was larger than filed.** `_receipt_file` derives from `dirname(_pin_file)`, so the
  Wave-3 preflight *receipt* moved with the cwd too: `env` in one directory and `send` in another
  could disagree about whether a receipt existed. Both now follow the repo root.

  **A pre-existing test asserted the literal `${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}` as
  AC-6.5** — the defect encoded as an acceptance criterion, the third instance of that pattern in
  one day (see J17, J1). Its intent (pin resolution must not change silently) was right, so it was
  re-aimed at the three branches rather than deleted.

  Verified live from three cwds: repo root, a subdirectory (no stray second file), and the sibling
  `HemaSuite` checkout — which now reads *its own* pins and says so. [[J18]]
  Status: `FIXED` 2026-07-23 — `_pin_file` resolves in three branches; see this entry.
- 🟡 **J3 — a tail read of a TUI is not evidence of pane state.** `hmad-dispatch read agy
  --lines 12..40` showed a boot screen (`You are currently not signed in`, spinner) unchanged
  across two minutes and three polls; I was one step from declaring the CLI wedged and relaunching
  it. `read --from-start` showed the truth: a ready `>` prompt, `Gemini 3.1 Pro (High)`, cwd
  `~/orca/skills`. The tail was rendering an overdrawn region of the frame. This is F5's mechanism
  with a new and more dangerous symptom — F5 is written up as "scrollback < report length" (you
  lose the *end* of a report), but here the tail was stale about the pane's *readiness*, which
  drives a relaunch decision. **Fix direction:** SKILL's readiness/liveness checks should specify
  `--from-start` (or a full-buffer read) rather than `read --lines N`. [[F5]]

  **FIXED 2026-07-23 — and the doc half was the smaller half.**

  The dangerous surface was **machinery, not advice**: `_snapshot` read a **6-line tail**, and
  `_wait_stable` returns idle the moment two snapshots match. Two identical *stale* tails are
  therefore accepted as proof of idleness — precisely the state J3 observed for three consecutive
  polls. `hmad-dispatch wait` could report idle for a pane mid-generation, after which the
  orchestrator reads a report that has not been written yet. The J13 probes showed the same shape
  from the other side: a pane sat unchanged at `Thought for 5s, 305 tokens` for minutes and then
  produced output.

  Measured on the live agy pane: the old snapshot saw **676 of 47,711 bytes — 1.4% of the buffer**,
  and decided readiness from it.

  A bigger tail is not the fix (J3's was already 40 lines; a tail is a slice of one frame however
  deep). `_snapshot` now reads `--cursor 0` on Orca and a much deeper screen on cmux, which has no
  cursor addressing. Verified live: `wait` still confirms idle in 6s, and two consecutive
  full-buffer snapshots of an idle pane are identical, so the stability signal is intact.

  Docs followed: the `/clear` readiness check uses `--from-start`, and the five *"re-read with a
  larger `--lines`"* remedies across `SKILL.md` and `references/failure-recovery.md` now say
  `--from-start` — that advice was actively wrong, since a larger tail does not escape an overdrawn
  region.

  One test initially passed for the wrong reason: a whole-file search for the readiness string
  matched the unrelated J13 size guidance added to `SKILL.md` earlier the same day. Scoped to the
  context-hygiene block. [[F5]] [[J13]]
  Status: `FIXED` 2026-07-23.
- 🟡 **J4 — F8 re-opened.** The actionable remedy message shipped and works, but the gap it
  describes is unchanged: `python3` on this machine (homebrew 3.14) has no `jsonschema`, so every
  `h_mad_state_write.py` / `h_mad_state_validate.py` / `h_mad_state_staleness.py` call in a run
  exits 2 until the operator manually substitutes `/opt/anaconda3/bin/python3`. Hit twice in the
  first five minutes of this run. A better error message is not a fix for a missing dependency.
  **Fix direction:** vendor a minimal validator, degrade gracefully to the historical tier when
  `jsonschema` is absent, or document a required interpreter in the SKILL preflight so it is a
  stated prerequisite rather than a per-call surprise.

  **FIXED 2026-07-23 — by the first option, not the cheap one.**

  "Degrade to the historical tier when `jsonschema` is absent" was rejected outright: silently
  validating against a weaker schema is the same defect class as an unenforced guard, and it would
  fail open exactly when the operator is least likely to notice. Documenting a required interpreter
  keeps the friction J4 measures ("hit twice in the first five minutes").

  So `h_mad_state_validate.py` now bundles `_MiniDraft7`, a stdlib validator covering **exactly** the
  ten constructs the two schema files use — enumerated from the schemas rather than guessed — with
  unknown keywords ignored, as Draft-07 requires. `jsonschema` still wins when importable; the
  bundled path only carries a run when it is not.

  **A hand-rolled validator is worth exactly what its differential test catches**, so that is the
  shape of the tests: under an interpreter that HAS `jsonschema`, both backends must return the same
  verdict on a corpus covering every construct, on `classify()` as well as the leaf check, and on
  the **live records on disk** (§"Incident replay" — the corpus was authored beside the validator
  and shares its assumptions; those records were not).

  Two traps worth recording:

  * **`format` must NOT be enforced.** Draft-07 treats it as an annotation unless a format checker
    is supplied, and the production path supplies none — so `started_ts: "not-a-date"` is valid
    today. A validator that "helpfully" enforced date-time would reject records the real one
    accepts: a regression dressed as an improvement. Verified against `jsonschema` before writing it.
  * **`bool` is not an `integer` in JSON Schema**, but `bool` subclasses `int` in Python. Mutation
    testing caught this: deleting the guard left the suite 5/5 green because no corpus case passed a
    boolean where an integer was expected. Three cases added; the mutation now fails 3 tests.

  **Verified end to end on the interpreter J4 is about.** A stock `python3` (no `jsonschema`) now
  runs `h_mad_state_validate.py`, `h_mad_state_write.py --create/--set` and `h_mad_state_staleness.py`,
  and both interpreters return byte-identical verdicts on the live store
  (`STATE: PASS strict=6 historical=0 invalid=0`, `STALENESS: CLEAN findings=0`).

  **Correction, recorded because the mistake is instructive.** I first wrote that the full suite
  passes under both interpreters. It does not — the stock `python3` has no `pytest` either, so the
  suite cannot run there at all, and the "650 passed" I read back had been produced by a rewritten
  invocation under a different interpreter. The suite runs under anaconda (650); what is verified
  under stock `python3` is the thing J4 is actually about: `h_mad_state_validate.py`,
  `h_mad_state_write.py --create/--set` and `h_mad_state_staleness.py` all run and agree with
  jsonschema's verdicts on the live store. Reading a command's output without confirming which
  binary produced it is §"Mutation verification" applied to my own evidence. [[F8]]
  Status: `FIXED` 2026-07-23 — by the first option, not the cheap one.
- 🟢 **J5 — `--claim` cannot create.** SKILL's `start_fresh` route prints
  `h_mad_state_write.py … --feature <f> --claim "<session-id>"`, but on a feature that does not
  exist yet that exits 2 with `ERROR: no such feature`. Every first-time claim — i.e. every
  `start_fresh` — fails as documented. `--create --claim <id>` works. **Fix direction:** either
  make `--claim` imply `--create`, or correct the SKILL snippet.

  **FIXED 2026-07-23 — by correcting the snippet, deliberately not by making `--claim` imply
  `--create`.** That error is a real typo guard on every other route: `resume_manual`,
  `enter_autonomous` and `halted` all claim a feature that already exists, so a misspelled name
  should fail rather than silently fork a second empty record and run against it. Verified today:
  `--feature realfeatt --claim` refuses, and nothing is written. Auto-creating would have traded a
  documented failure for a silent one.

  `SKILL.md` now shows both routes explicitly — `--create --claim` for `start_fresh`, `--claim`
  alone elsewhere — with a note not to reach for `--create` on a resume route to make the error go
  away. `--started-ts` is no longer needed either, since J8 made `--create` default it.

  **Found while mutation-testing the guard: `release`'s copy was unenforced.** `set_fields` and
  `claim` both had their `no such feature` guard covered, but deleting `release`'s left **653 tests
  passing**. A release against a misspelled name would silently no-op, leaving an operator believing
  they let go of a feature they still hold. Covered now; the mutation fails a test.
  Status: `FIXED` 2026-07-23 — by correcting the snippet, deliberately not by making `--claim` imply create.
- ⬜ **J6 — DISPROVEN: `clear <agent>` does not exit the Antigravity pane.** Initially filed from
  an observation that `hmad-dispatch clear agy` was followed within 15s by `status: exited` on
  that handle. The operator then reported having closed that tab manually. Verified with a
  throwaway pane: created a fresh agy terminal, ran `hmad-dispatch clear agy` against it, and 15s
  later the pane was still `status: running` with the cursor advanced 37→61 (the `/clear` was
  processed and the frame redrawn). **`clear` behaves as documented.** Recorded so the
  correlation is not re-filed as causation by a future run. Method note: the throwaway-probe
  pattern (`docs/skill-candidates.md`, recurrence 2) is what settled it.
  Status: `DISPROVEN` — the filed behaviour does not occur; kept so it is not re-filed.

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
  Status: `FIXED` — **re-verified live 2026-08-22**, which is the only reason this row can be closed: the entry recorded no fix. J7's repro was `18 failed / 459 passed` with `.h-mad/orca-pins.env` present. Re-run with a pin file deliberately created: the 31 tests it named all pass, and the **full suite is 1601 passed / 0 failed**. The pin file came back byte-identical, so the isolation the fix direction asked for is real and not merely arranged around an absent file.

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
  Status: `FIXED` — shipped in Wave 4a (`ab3657e`); see the status-row audit note below this section.
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
  Status: `FIXED` — shipped in Wave 4a (`ab3657e`); see the status-row audit note below this section.

- 🟢 **J9 — `test_alive_cmux_true` is environment-dependent.** Failed once during a Phase-5f full
  run, then passed on two consecutive full runs of the identical suite with no change in between.
  It probes the real `cmux` binary, so its result depends on machine state rather than on the code
  under test. Not order-dependence — it passes in isolation and in the same 498-test set that
  failed it once. **Fix direction:** stub the substrate probe as the neighbouring tests do, so the
  suite does not have a test whose verdict depends on whether a terminal multiplexer happens to be
  responsive.

  **DISPROVEN 2026-07-23 — the failure was real, the attributed cause was not.**

  The filed premise is that the test "probes the real `cmux` binary". It does not, and did not when
  filed:

  * The test already stubs it — `_bindir(tmp_path, ["cmux"])`, exactly as the neighbouring tests do,
    so the filed fix direction was **already satisfied** and there was nothing to change.
  * `run()` builds `PATH = f"{bindir}:/usr/bin:/bin"`, so the real binary (present on this machine at
    `/opt/homebrew/bin/cmux`) is unreachable from the test. `git log -S` dates that PATH construction
    to **2026-07-20**, which *predates* the Phase-5f run that observed the failure.

  Reproduction attempts: **0 failures in 200 consecutive runs** of the named test, and three
  consecutive clean full-suite runs (654 each).

  An alternative mechanism was hypothesised and also killed rather than filed: `_cmd_alive`'s
  `cmux tree --all | grep -q` runs under `set -euo pipefail`, so an early-exiting `grep -q` could in
  principle SIGPIPE the emitter and make `alive` report a live pane as dead. Measured: **0/40** with
  a 200,000-line subprocess emitter. Not a real hazard here.

  **What remains true:** one full run did fail once, and that observation stands. Its cause is
  unknown and has not recurred across the many suite runs since — including after the F13, J7, J2
  and conftest isolation work, any of which could have removed a contributing condition. Recorded as
  disproven-cause rather than fixed, so a future observer re-derives the cause instead of re-applying
  a remedy that was already in place. Method mirrors [[J6]].

**Also observed (evidence for existing entries, not new IDs):** `orca terminal create --title
"agy-probe"` does not stick — `terminal list` reports `title: agy`, the program's own OSC title.
Independent confirmation of H5's core claim that `.title` reflects what the program emits and that
caller-supplied titles are not surfaced. Filed upstream as stablyai/orca#9870 — **closed 2026-07-23**;
the identity it asked for turned out to live in `worktree ps`, not `terminal list` (see J16).

**In flight, not a monitoring item:** `audit_cycles`/`iterate_cycles` are seeded and never
incremented (both drift warnings dead). Being fixed by the `cycle-telemetry-fidelity` feature —
see `docs/01-plan/h-mad-remediation-sequence.md` Wave 1.

---
  Status: `DISPROVEN` 2026-07-23 — the attributed cause was refuted. **The observation stands**: one full run did fail once, cause unknown. A disproven diagnosis is not a disproven symptom.

## Surfaced by the preflight-read-enforcement `/h-mad` run (2026-07-23, Wave 3 dogfood)

Found by **running** Waves 1–2 through a real 7-phase feature in `~/orca/skills` — the Wave-3
dogfood whose purpose is exactly this (`docs/01-plan/h-mad-remediation-sequence.md` §Wave 3,
closing G-b/G-d). All three are prose-vs-tooling mismatches: each instruction was doc-verified and
had never been executed. All unfixed.

| ID | Sev | Status | One-line |
|---|---|---|---|
| J11 | 🟡 | **FIXED** | `SKILL.md` twice orders "record the substrate + agent mapping via `h_mad_telemetry.py`"; the script has no such argument and the row schema has no such field |
| J12 | 🟡 | **FIXED** | `h_mad_assemble_audit.py` returns `ASSEMBLE: PASS` for a prompt it simultaneously predicts will fail — the oversize warning is an unread line beside a passing token |
| J13 | 🟢 | **FIXED** | The "split by FR group" remedy does not divide the fixed terms — AND the 49 KB cliff it defended against was never reproduced for the delivery mode h-mad actually uses |

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

  **FIXED 2026-07-23.** Took the first branch, not the cheap one: the capability was worth having,
  and deleting the sentence would have removed the instruction while leaving the gap it named.

  Made **state the carrier and telemetry the reporter**, which is what §"Single-source contract"
  wants anyway. Phase 5 writes the field with the writer's existing generic `--set` — no new flag —
  and `record` copies it onto the Phase-7 row it *already* builds from that same record:

  ```bash
  h_mad_state_write.py docs/.bkit-memory.json --feature "<f>" \
    --set substrate='{"name":"orca","agents":{"codex":"term_…","agy":"term_…"}}'
  ```

  The blocker was never the writer — it was that the strict schema is `additionalProperties: false`,
  so the Phase-5 instruction had nowhere to write even if someone had tried. `substrate` is now an
  **optional, additive** property with `required` unchanged, so every pre-existing record stays valid
  (§"Backward compatibility"). No version bump: the skill's "v2.2" appears in ~8 places and denotes
  the skill, not the schema; a partial bump would be worse than none.

  The row carries an explicit `null` when unrecorded rather than omitting the key, so a reader can
  distinguish "dispatched under an unrecorded substrate" from "row predates the field".

  **Dogfooded end to end against the live runtime** — `hmad-dispatch env` → parse → `--set` →
  `record` — producing the first telemetry row in this repo's history that names its substrate
  (`orca`, with both agent handles). Both instruction sites in SKILL.md corrected; a doc test
  asserts the impossible call is gone **and** that the executable one replaced it, since deleting
  the sentence alone would pass a naive "is it gone" check while losing the capability.
  Status: `FIXED` 2026-07-23 — took the first branch, not the cheap one.
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

  **FIXED 2026-07-23 — but neither option in the fix direction above survived contact.**

  *Option `ASSEMBLE: HALT <phase>:oversize`* is contradicted by evidence. J13 measured five
  file-indirection prompts spanning 53-61 KB, all answered. Halting on a size that demonstrably
  works trades a missed signal for a false stop.

  *Option `ASSEMBLE: PASS_OVERSIZE`* **reproduces this very defect.** Tested before adopting:
  `"ASSEMBLE: PASS_OVERSIZE ..."` satisfies `grep "ASSEMBLE: PASS"` *and*
  `startswith("ASSEMBLE: PASS")` -- which is how every consumer reads the token, including this
  repo's own tests. A PASS-grepping orchestrator would sail past it exactly as it sails past the
  adjacent `!` line today. The suggestion looked right and was wrong in the direction that
  mattered; one command found that out.

  **Shipped instead:** a required machine-readable field *on the verdict line* --
  `ASSEMBLE: PASS <path> <size> sentinel=<s> size_status=verified|unverified` -- with the verdict
  token left exactly `PASS`/`HALT` so existing consumers keep working. "Proceed" stays correct;
  what changes is that the size can no longer be *missed* by anything parsing the line the mandated
  read already parses. `SKILL.md` now requires reading the field and states what `unverified`
  changes: it is a **diagnosis** hint, not a stop -- on an empty reply, re-read the full buffer
  first (a tail-grep reports SILENT for replies the TUI reflowed, per J13), then apply step 5.5.

  Note what this does *not* claim to be: machinery. Nothing forces the read, because unlike the
  Wave-3 `send` receipt there is no irreversible step to guard -- proceeding is correct in both
  states. Putting the signal inside the line the contract already mandates is the honest ceiling
  here, and strictly better than a sibling line nothing must parse. [[J13]]
  Status: `FIXED` 2026-07-23 — shipped a required machine-readable field on the verdict line; neither option in the original fix direction survived contact.
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

  **FIXED 2026-07-23 — and the premise turned out to be wrong too, which changed the fix.**

  Applying §"Verifying a review finding before acting on it" to this entry: the remedy was
  defending against a **49 KB reviewer cliff that has never reproduced for the delivery mode this
  skill uses**. `hmad-dispatch send` inlines only up to `HMAD_SEND_INLINE_MAX` (8192 B); above that
  it stages the file and the agent reads it. Audit prompts are 32–61 KB, so **every one goes by file
  indirection and none is ever pasted**. The 2026-07-21 session that produced the 49 KB figure
  recorded sizes but not delivery mode.

  Measured live 2026-07-23 via file indirection: **56,349 B answered, 61,493 B answered.** With the
  three already on record (52,997 / 53,058 / 58,536 B) that is **five file-indirection observations
  spanning 53–61 KB, all answered, and zero file-indirection silences**.

  **A methodology error inside this very investigation is the most transferable part.** *Three*
  independent pollers tailing 40 lines for the sentinel reported `RESULT=SILENT after ~5min` (two
  for the 61,493 B probe, one for 56,349 B), and I nearly wrote "the cliff reproduces" into the docs
  on that basis. A full-buffer read found the tokens: the TUI had reflowed the reply across redraw frames
  (`J13OK J1` first, the full line later; the other probe's token split into `J13-FIFTYFIVE-4` and
  `D8E`). A tail-grep cannot distinguish "emitted nothing" from "emitted something the viewport
  reflowed" — and **that is plausibly how the original 49 KB boundary was recorded in the first
  place.** F5 already documented the fragmentation; I used an ad-hoc grep anyway because it was
  "just a probe".

  **Shipped:** `h_mad_assemble_audit.py` thresholds re-anchored to the largest size *confirmed
  answered* (61,493 B) instead of a predicted failure point, with wording that says "unverified,
  not known-bad" — the old text predicted a silent failure at sizes since measured as fine and had
  already cost a design audit an unnecessary trim. `agent-substrate.md` §"Prompt size" rewritten
  with the delivery-mode distinction, the full table, and the do-not-tail-grep rule. `SKILL.md`
  step 5.5 now carries the fixed-vs-divisible arithmetic and the options that actually work
  (FR-only spec inline → shorten the design → **split the feature** → trim the rubric last).

  **Knock-on for J12:** its "an orchestrator dispatches a prompt the script itself expects to come
  back empty" premise is now false — the script no longer predicts failure there. J12's structural
  point (a warning beside `PASS` that nothing must read) still stands and is still worth fixing,
  but it is no longer urgent. [[J12]] [[F5]]

**Also measured (evidence, not a new ID):** the ~49 KB reviewer cliff did **not** reproduce on this
host. `references/agent-substrate.md` records 49,273 B emitted normally and 53,066 B silent, and
asks that the boundary be re-measured per host. A 52,168 B design audit delivered by **file
indirection** (`send` stages the path; the agent `Read`s it itself, twice) was answered normally by
Antigravity CLI 1.1.5 / Gemini 3.1 Pro. The original measurements may have been of a different agent
build, or the cliff may be a property of TUI paste rather than of agent-side file reads — the two
delivery modes were not distinguished when the number was recorded. Worth re-measuring deliberately
before anyone trims a design to satisfy it.
  Status: `FIXED` 2026-07-23 — and the premise was wrong too, which changed the fix.

## Surfaced by the first live Phase-5 worktree fanout (2026-07-23, same Wave 3 run)

The fanout path (`worktree-create → dispatch → await → merge → rm`) had been stub-tested only;
this is its first real Orca-hosted-agent run. It **worked** — two Codex workers implemented
independent modules in isolated worktrees, both merged clean, suite went 530 → 539 — but the
protocol has two gaps that only running it could expose. Both unfixed.

| ID | Sev | Status | One-line |
|---|---|---|---|
| J14 | 🟡 | **FIXED** `ab3657e` | The fanout protocol lists `worktree-create --prompt-file` and `task-create`+`dispatch`+`await` as one sequence; they are alternatives, and the documented one cannot produce the task-id the other half needs |
| J15 | 🔴 | **FIXED** `ab3657e` | Nothing in the fanout protocol or the Codex prompt tells a worker to commit, so the merge gate would merge an empty branch and report success |

- 🟡 **J14 — the fanout dispatch and wait paths are mutually exclusive but documented as
  sequential.** `SKILL.md` §"Phase 5 parallel fanout" and `references/orchestration-mode.md` §"Phase
  5 parallel fanout" both read: "`worktree-create <module> --base <feature-branch> --prompt-file
  <staged-prompt>`; use Tier-2 `task-create` then `dispatch --to <selector>`; `await` the worker".
  Measured: `worktree-create --prompt-file` starts the agent **immediately** (both workers were
  `state: working` on the staged prompt seconds after creation), so a following `dispatch --to`
  would deliver a second prompt into a busy agent. They are alternatives. The consequence is not
  cosmetic: only the `task-create` path yields a task-id, and **both `await` and `gate-create`
  require one** (`_cmd_await` `--task`, `_cmd_gate_create` `--task`). Taking the documented
  create-with-prompt route therefore forfeits the documented wait mechanism *and* the merge gate's
  record — this run had to fall back to polling report files and then create a worker-less task
  purely to hang the gates on. **Fix direction:** present them as two explicit modes (prompt-at-
  create vs task-dispatch) and state which verbs each supports; if `await`/`gate-create` are meant
  to work in both, `worktree-create` should return a task-id too. Related: the protocol says
  "merge `<module-branch>`" without saying how to derive it — Orca names the branch
  `BrightGold70/<name>`, not `<name>`. [[J1]]
  Status: `FIXED` — shipped in Wave 4a (`ab3657e`); see the status-row audit note below this section.
- 🔴 **J15 — a fanout worker is never told to commit, so the merge gate can merge nothing and call
  it clean.** The winner-merge gate runs `git merge --no-ff <module-branch>` and treats "zero exit
  AND `git ls-files --unmerged` empty" as a clean merge worth auto-recording. But nothing instructs
  the worker to commit: `references/codex-implementer-prompt.md` never mentions `git commit`, and
  the fanout protocol has no equivalent of the serial path's Phase-5g "`git add -A && git commit`
  per module". Measured on this run: **both** workers reported `STATUS: DONE` with green suites
  (536 and 533 passed) and left **every change uncommitted** — `git log 1aaf3c4..HEAD` empty,
  `git status --short` showing two modified files in each worktree. Had the gate run as written it
  would have merged an up-to-date branch, exited 0, found no unmerged paths, auto-recorded `yes`,
  and then `worktree-rm` would have **destroyed the only copy of the work** — a total, silent loss
  reported as a successful merge. This run committed on the workers' behalf before merging.
  **Fix direction:** add an explicit commit step to the fanout protocol (either the worker commits
  as its final action before writing the report, or the orchestrator commits after reading a
  `DONE`), and make the gate refuse a merge whose diff against the base is empty — "nothing to
  merge" must be a halt, never a clean verdict. [[J12]]
  Status: `FIXED` — shipped in Wave 4a (`ab3657e`); its guards fired live during the J17 work the same day.

## Surfaced by the fanout-integrity-and-defects `/h-mad` run (2026-07-23, Wave 4)

| ID | Sev | Status | One-line |
|---|---|---|---|
| J16 | 🟢 | **RESOLVED** | `worktree ps` carries `agents[].agentType` keyed by `paneKey`, which maps to `terminal list`'s `tabId:leafId` — a reliable identity source that `_orca_find`'s heuristics do not use |

- 🟢 **J16 — agent identity IS available, just not from `terminal list`.** H5 and
  [orca#9870](https://github.com/stablyai/orca/issues/9870) record that Orca "exposes no field naming
  the running program", which is true of `orca terminal list`: `.title` is the enclosing tab's title
  (shared by every leaf) and `.preview` decays once the agent works. But `orca worktree ps --json`
  returns `.result.worktrees[].agents[]` with an explicit **`agentType`** (`codex`, `antigravity`,
  `claude`) and a **`paneKey`** of the form `<tabId>:<leafId>` — and `terminal list` returns
  `.tabId` and `.leafId` per terminal. Joining the two gives an exact, title-independent,
  preview-independent handle for each agent.

  Measured live during this run, at the point where both pinned handles had gone stale and **two
  panes both reported `title: "Codex - skills repo"` with empty previews** — the exact ambiguity H5
  documents, where one of them was agy. Content probing could not separate them either (both
  buffers had been reset to cursor 0). The paneKey join resolved them unambiguously:

  | agent | paneKey leaf | handle |
  |---|---|---|
  | antigravity | `9374f1b5…` | `term_0a2de455…` |
  | codex | `df01b396…` | `term_294ce89e…` |

  **Fix direction:** add a `worktree ps`-based resolution step to `_orca_find`, ahead of the
  title/preview heuristics, joining `agents[].paneKey` to `terminals[].tabId + ":" + leafId` and
  matching on `agentType`. That is not a workaround for the missing field — it is the field, in a
  different call. Worth attempting **before** Wave 5 continues waiting on #9870, and worth reporting
  upstream since it may make the issue moot. Note `agentType` is `antigravity`, not `agy`, so the
  mapping needs an alias. [[H5]] [[J1]]

  **SHIPPED 2026-07-23.** `_orca_find_by_pane` + `_orca_agent_type` in `hmad-dispatch.sh`, wired as
  **Pass 0** of `_orca_find` ahead of both heuristics; 8 tests. It holds, and the join is now the
  primary identity mechanism — the title and preview passes are the fallback, not the other way round.

  - **Live before/after, same runtime, same listing, pins bypassed.** Before: `codex -> UNRESOLVED`
    and `agy -> UNRESOLVED` — *both* passes resolved 0 candidates, so the whole run depended on the
    pin file. After: both resolve, and both match the pinned handles exactly, on a listing where the
    agy pane's `.title` literally reads `"Codex - skills repo"`.
  - **Scoped truncation is safe; unscoped is not.** `worktree ps --limit` drops whole *worktrees*,
    never agents within one, so a same-worktree rival can never be hidden from a scoped match. With
    no coordinator and no enclosing worktree, matching is global and a dropped worktree could hide
    the rival that makes it ambiguous — so the join refuses a truncated listing only in that case.
  - **Two independent scope layers, and only mutation showed one was untested.** The caller already
    scopes *terminals* by `.worktreePath`, so deleting the join's own worktree filter broke nothing.
    The filter is not redundant — it pins which source decides when the two calls disagree about a
    pane's worktree — but it needed a test that isolates it (`…_trusts_ps_worktree_grouping`).
  - **Ambiguity declines rather than falls through to guessing.** Two agents of one type in scope →
    UNRESOLVED → pin. Weaker evidence resolving what stronger evidence called ambiguous is guessing
    with extra steps.
  - **Reported upstream and CLOSED 2026-07-23 as completed**
    ([#9870](https://github.com/stablyai/orca/issues/9870)). The field existed all along; the
    original report had inventoried only `terminal list` and `terminal show`. Residual gap stated in
    the closing comment, not tracked: a plain `terminal create` shell is absent from `agents[]`
    (verified), but whether a **human-adopted** pane registers there is unestablished.

**Also observed (evidence, not new IDs):**
  Status: `RESOLVED` — reported upstream and closed there as completed 2026-07-23; the capability already existed in `worktree ps`.
- **Handle rotation happened twice in one run**, and the Wave-3 receipt caught both:
  `PREFLIGHT: FAIL stale=agy`, then later `PREFLIGHT: FAIL stale=codex,agy`. Under the pre-Wave-3
  protocol each was an advisory line nothing was obliged to read, and each dispatch would have gone
  into a dead pane and vanished. Both halted the run instead. This is the strongest evidence so far
  that the mandated-read-to-machinery conversion was worth doing.
- **`orca terminal read` takes `--limit`, not `--lines`** (unlike `hmad-dispatch read`, which uses
  `--lines`). Passing `--lines` returns an `invalid_argument` envelope; combined with `2>/dev/null`
  in a probe, that error was silently rendered as an empty pane and briefly read as "the agent is
  gone". A reminder that suppressing stderr on an Orca call converts a loud error into a wrong
  conclusion.
- **The ~49 KB reviewer cliff did not reproduce, again.** Prompts of 52,997 B, 53,058 B and
  **58,536 B** were all answered normally by Antigravity 1.1.5 / Gemini 3.1 Pro via file
  indirection. `references/agent-substrate.md` still records 53,066 B as silent, and that number is
  now actively costing work — a design audit was trimmed on the strength of it. See J13.

  **RESOLVED 2026-07-23 — see J13.** The threshold was re-measured: five file-indirection prompts
  spanning 52,997–61,493 B all answered, and every audit prompt is file-delivered. The rubric's
  "size budget" was measured against a boundary that does not apply to it. Original note follows.

  **New evidence 2026-07-23 (Wave 4c):** the threshold now costs work in a second, structural way.
  `invariants.base.md` is inlined **verbatim into every audit prompt**, so each rule added to the
  base rubric spends headroom in *all* of them — Waves 4b+4c added four rules and moved a calibrated
  test fixture from 47.4 KB to 52.0 KB, failing `test_size_warning_fires_before_the_cliff`. The
  fixture was recalibrated rather than the threshold retuned (that is J13's decision, not a test's),
  but the implication stands: **if the 49 KB cliff is real, the Axis-B rubric has a size budget and
  is already consuming it; if it is not real, the budget is imaginary and the warning is noise.**
  Either way the number needs re-measuring before the rubric grows again.

---

## Surfaced by the post-Wave-4 branch cleanup (2026-07-23)

| ID | Sev | Status | One-line |
|---|---|---|---|
| J17 | 🔴 | **FIXED** `b0662cc` | `worktree-rm` forwarded the caller's selector raw (`repo::<path>` → `selector_not_found`), AND skipped its guards entirely for every *documented* selector form — `path:<p>` silently destroyed a worktree holding an unmerged commit |

- 🔴 **J17 — `worktree-rm`'s guarded selector form is rejected by the real runtime.** Removing the
  merged `auto-hmad-e2e-auto-run-1-…` worktree failed:

  ```
  hmad-dispatch worktree-rm "repo::/Users/kimhawk/orca/workspaces/skills/auto-hmad-e2e-…" --base main
  → [H-MAD] worktree-rm failed selector=repo::… rc=1
  ```

  The **guards passed** — `_worktree_path` resolved the path and `_worktree_holds_work` cleared it
  (no guard message was printed). The failure is one line later, at the `orca` call itself, and the
  wrapper sends its stdout to `/dev/null`, so the actual cause never reaches the operator:

  ```json
  {"ok": false, "error": {"code": "selector_not_found", …}}
  ```

  `orca worktree rm --worktree "<repoId>::<path>"` succeeds (`removed: true`, and it deletes the
  branch too). So the `::` *shape* is right, but the left side must be the real **repoId** —
  `_worktree_path` accepts `*::*` and keeps only the right side, which is why any prefix satisfies
  the guard while only one satisfies Orca.

  **The suite cannot catch this: 8 `worktree-rm` tests pass `repo::<path>`, and 4 assert the exact
  forwarded string `orca worktree rm --worktree repo::<path> --json`.** The stub accepts any argv,
  so a green suite pins a command a real runtime refuses — the same shape as [[B5]] (`safe_child`
  rejecting every absolute path while its tests passed). The tests are not merely silent here; they
  actively encode the broken form as correct.

  **Fix direction:** resolve the selector to a canonical `worktreeId` inside `_cmd_worktree_rm`
  before forwarding (join `worktree ps` on `.path`/`.displayName`/`.branch` — `_worktree_path`
  already does this lookup for the guard and discards the id), and stop discarding `orca`'s stdout
  on failure so `selector_not_found` reaches stderr instead of a bare `rc=1`. Re-point the 8 tests
  at the resolved form. Note the reason `--force` would NOT have helped: it skips the guards, not
  the selector, so a forced run fails identically — an operator reaching for `--force` here (the
  reflex [[J15]] exists to prevent) gets the same opaque `rc=1`. [[J15]] [[B5]]

  **The filing above understates it. Fixed `b0662cc` (feature/195); a second, worse defect was
  found while fixing the first.**

  `_worktree_path` understood only *bare* selectors, so every **documented** form — `path:`,
  `name:`, `branch:`, `issue:`, `active`/`current` — failed to resolve. And the caller treated
  "cannot resolve" as "no guard needed": the guard block was wrapped in `if path="$(_worktree_path
  "$sel")"; then`, so an unresolvable selector fell straight through to the removal. Its own
  contract comment says *"Empty is 'cannot check', never 'safe to destroy'"*; the caller inverted it.

  **Proven live 2026-07-23 before fixing**, on a throwaway worktree holding one unmerged commit and
  a clean tree:

  | selector | guard | outcome |
  |---|---|---|
  | `repo::<p>` | ran, refused | worktree survived (the filed bug — noisy but SAFE) |
  | `path:<p>` | **skipped** | **worktree destroyed, silently** — no message, no error, exit 0 |

  So the forms that worked were the unguarded ones, and the form the tests pinned was the
  guarded-but-broken one. Orca's own refusal covers a **dirty working tree only** (`runtime_error:
  Failed to delete worktree … ?? PRECIOUS.txt`) and never an unmerged branch, so h-mad's guard is
  the sole protection for precisely the case [[J15]] exists to prevent. Data loss was averted here
  only because Orca retains an unmerged branch — but the *worktree* went, with no signal, where the
  protocol promises a refusal.

  **A prediction I got wrong, worth recording:** I first assumed the documented selectors would
  bypass straight into data loss. The probe disproved that — Orca's dirty-tree check caught the
  uncommitted case. Only after committing the file (clean tree, unmerged branch) did the hole open.
  The narrow window is the whole finding; asserting the broad version would have been wrong.

  **Shipped:** `_worktree_path` learns the full grammar from `worktree rm --help` (incl.
  `active`/`current` via `worktree current`); an unresolvable selector **refuses**
  (`worktree_selector_unresolvable`) with `--force` as the escape hatch; the resolved path is
  forwarded as `path:<p>` so guard and removal cannot disagree; orca's stdout is captured so the
  failure reason reaches the operator, and an `ok:false` envelope with exit 0 now fails (F11 class —
  this verb had been missed). Suite 600 → 604; all five guards mutation-tested. Live after: `path:`,
  `name:` and `repo::` all refuse an unmerged worktree, and `repo::` now *succeeds* on a clean one.

---

_Append new findings below as later runs surface them. Flip Status + link the commit when actioned._
  Status: `FIXED` `b0662cc` (feature/195) — and the filing understated it; a second, worse defect was found while fixing the first.

## Pre-existing: silent flag-drop (closed 2026-07-23)

| ID | Sev | Status | One-line |
|---|---|---|---|
| P1 | 🟡 | **FIXED** | Eleven arg loops ended in `*) shift ;;`, so a misspelled flag was silently discarded and the verb answered a question nobody asked |

- 🟡 **P1 — `*) shift ;;` at 11 sites.** Wave 4a declined this as pre-existing and out of scope,
  noting that if it changed, all eleven should change together. Done as its own feature.

  **The cost, measured rather than argued:** `hmad-dispatch wait agy --timeut 2` (one character
  wrong) **blocked for the 300s default instead of 2s** — reproduced with a bounded probe, and it
  is what made the first RED run of these tests time out. The same shape elsewhere is worse than
  slow: `worktree-rm <sel> --bse main` drops the base, so the unmerged check runs against the wrong
  ref — the J15/J17 failure family reached by a spelling mistake — and `read <agent> --form-start`
  returns a 50-line tail while the caller believes it asked for the whole buffer (J3). In every case
  the operator gets a plausible answer to a question they did not ask.

  **Why failing is safe here:** every one of the eleven loops consumes its **positionals before the
  loop begins**, so anything still present when the loop runs is meant to be a flag. Checked all
  eleven before changing any, rather than assuming it. Exit 2, not a verdict token — a malformed
  request is an operational error per §"Audit-gate signal discipline", not a statement about the
  world.

  Single shared `_unknown_opt` helper (§"Single-source contract") naming both the verb and the
  offending token, so the operator re-reads their own command line rather than `--help`. Swept the
  docs for invocations that would newly be rejected: the only two flagged (`automation-create
  --name`, `file-open-changed --mode`) are both real flags in their loops. Live-verified against the
  runtime: typos rejected, `--limit` and `--from-start` still work. Suite 654 → 666.


## Surfaced by the J2 fix (2026-07-23)

| ID | Sev | Status | One-line |
|---|---|---|---|
| J18 | 🟡 | **FIXED** | Mutation-testing a path-resolution function disabled the suite's own isolation and overwrote live session state, while the run reported 642 passed |

- 🟡 **J18 — mutation testing can clobber real state, silently.** `invariants.base.md`
  §"Test discrimination" mandates stubbing a guard to its permissive value and re-running. Applied
  to `_pin_file`'s explicit-override branch — the branch every test relies on to point
  `HMAD_ORCA_PIN_FILE` at a temp path — it redirected **the whole suite's pin writes onto the
  developer's live `<repo>/.h-mad/orca-pins.env`**, replacing two real agent handles with the test
  fixtures `term_live` / `term_explicit`. The run reported **642 passed** throughout: from the
  tests' point of view nothing was wrong, because they assert what the file contains and never
  where it is *not*.

  Caught only because the next live `hmad-dispatch env` showed two handles that had never existed.
  Confirmed by re-running the same mutation with the file watched, and the real handles restored
  from a backup.

  **Fixed** by `h-mad/tests/conftest.py`: a session-scoped autouse fixture snapshots the live pin
  file, restores it if the session moved it, and fails loudly naming the likely cause. Verified by
  deliberately re-introducing the leak — the fixture fired, restored the handles, and the suite went
  red instead of green. The `## Test discrimination` rule now carries the caveat: before mutating
  anything that decides *where* state is written, snapshot the target or sandbox the cwd.

  The general shape is worth remembering: **a suite's isolation is itself implemented by branches,
  and mutation testing deletes branches.** The safety property most likely to be disabled by a
  mutation is the one keeping the tests off your real machine. [[J2]]

  **Re-verified 2026-08-22, and the re-verification found the gap the original fix left.** The
  guard exists and behaves correctly — but it had **no test of its own**. Its younger sibling
  `_protect_live_wire_registry`, written later and modelled directly on it, carries *both* a fixture
  test and a harness mutation in `test_h_mad_wire_registry.py`; the original carried neither, and
  nothing in the suite so much as referenced `_protect_live_pin_file`.

  That asymmetry is the finding. **A session-scoped autouse fixture that nothing tests is one
  deletion away from being gone, and its absence is silent by construction** — the suite is green
  whether the guard is there or not, which is the very property that made J18 invisible the first
  time. "Verified by deliberately re-introducing the leak" was a manual one-off in 2026-07; nothing
  carried it forward.

  Closed with `h-mad/tests/test_h_mad_pin_file_guard.py`, four tests giving the guard what its
  sibling already had:

  - it fires on a modified live file **and restores the real handles** (reporting a leak without
    repairing it is half a guard);
  - it **deletes** a pin file the suite invented when none existed before — the inverted repair, and
    the live case on this machine, where `.h-mad/orca-pins.env` is currently absent, so a guard
    handling only the overwrite branch would leave a fabricated file behind on exactly the machines
    with no agents pinned;
  - it stays **silent on a clean run**, without which the two above are satisfied by a fixture that
    always fails;
  - and a harness mutation (`if True: return` at a new pin-file-specific anchor) proves it bites.
    The anchor comment is load-bearing: `if after == before:` occurs once per guard, and the harness
    refuses any anchor it cannot match exactly once.

  Independently checked by deleting the fixture outright — all four tests fail. Live state verified
  byte-identical throughout, per this entry's own rule.
  Status: `FIXED` — guard shipped 2026-07, its coverage 2026-08-22.


> **Status-row audit 2026-07-23.** J8, J10, J14 and J15 shipped in Wave 4a (`ab3657e`) but their rows still read `SCHEDULED`/`MONITORING` — verified against the code before flipping (J15's guards fired live during the J17 work the same day). This registry's own lifecycle line says *"Flip Status + link the commit when actioned"*; a stale row is a coverage hole, because the next reader treats a solved problem as open work and an open one as solved.



> **Adjudication 2026-08-03 — `#68` and `#86` closed, from the HemaSuite handover.**
>
> **`#68` — closed as covered elsewhere; the shipped spec is deliberately NOT amended.** The
> question was whether `docs/01-plan/features/tdd-dispatch-verification-discipline.spec.md` should
> gain the dispatch-prompt size finding (`92,055B`, the `ARG_MAX`/size-ceiling frontier). Verified:
> `grep -c '92,055\|size ceiling\|size_status\|ARG_MAX'` against that spec returns **0**, so the
> premise was correct — it genuinely is not there.
>
> It should not be. That spec is about **verification discipline** — whether RED tests can fail,
> whether GREEN is established by a revert test, whether verification actually verified; its FR-1..
> FR-4 are all prompt/protocol changes to `codex-implementer-prompt.md` and SKILL.md Phase 5e. The
> size finding is about **transport capacity** — how large a prompt the dispatch path can carry
> (`exec` on stdin is mechanically uncapped; a live agy pane answered a 92,055B file-indirection
> prompt). Orthogonal axis. Adding it would make the spec less coherent, not more complete, and
> retroactively editing a shipped record to insert a fact that was never in its scope is worse than
> leaving it out.
>
> The finding is already recorded in three places — `docs/learnings.md` (×2), its own handoff
> `docs/handoffs/2026-07-30-main__dispatch-prompt-size-frontier-92kb.md` (×5), and the
> `size_status=verified|unverified` contract above. That is better coverage than most findings get.
> If the size frontier ever needs enforcing rather than remembering, it wants its own spec.
>
> **`#86` — closed as a duplicate** of `#67`/`#66`/`#68`. It was a rollup adding only two
> verification notes, both discharged by the inbound handover brief
> (`docs/handoffs/2026-08-03-main__five-hmad-items-handover.md`) before any work started.
>
> Dispositions of the rest of that handover: `#67` shipped (TDD gate resolved its state file at repo
> root and stood down silently in sub-project layouts — the gate was off for a whole Phase 5).
> `#66` item (1) needed no work, closed by PR #22 the same day; item (2) shipped
> (`phase_counter_behind` fired on healthy mid-Phase-5 records). `#40` remains open as a judgement
> call — its close criterion was met by a *different* feature's run, and absence of the
> `Waiting for background terminal` string is evidence the pane path was never exercised, not that
> the guard works.

> **Adjudication 2026-08-03 — `#40` re-scoped; `#38`'s guard kept, on better evidence than the one proposed.**
>
> `#40` planned to instrument a Phase-5 run and count pane-path vs `exec` dispatches, with the stated
> criterion: *"zero pane-path dispatches across a full Phase 5 → close #38."* The
> `grounding-shadow-measurement` Phase 5 (Tasks 3–4, 2026-08-01→03) then ran **entirely on `exec`** —
> zero pane dispatches, zero `wait --not-while-regex` invocations, so `Waiting for background
> terminal` never had an opportunity to appear.
>
> **That criterion is unsound and should not be used.** Absence of the string is evidence the pane
> path was never *exercised*, not evidence the guard *works* — the same fallacy the mutation
> discipline exists to prevent (zero failures is itself a finding). Closing a guard because it never
> fired is precisely backwards, and it would have been closed on a run of a *different* feature than
> the one `#40` named.
>
> **The guard needs none of that evidence, because it is directly verified.**
> `test_hmad_dispatch.py:1316` pins it — "a pane parked on `Waiting for background terminal` is
> stable but NOT done" — and that test is discriminating, confirmed by mutation on 2026-08-03:
> disabling `--not-while-regex` in `_wait_stable` (`h-mad/scripts/hmad-dispatch.sh:1575`) turns the
> suite red. So `#38`'s correctness was never resting on the evidence run.
>
> **Disposition.** `#40`'s instrumentation plan is **closed as overtaken**: it existed to decide
> whether the pane path still mattered, and `exec` becoming the documented default for one-shot
> 5d/5e answered that by construction, with the live run confirming it in practice. `#38`'s guard
> and its test **stay**. The pane path is now a *fallback* rather than the primary path, and a
> rarely-exercised fallback is exactly the kind whose correctness must come from a unit test rather
> than from production traffic — production will not exercise it, which is the whole point.
>
> The conclusion ("the guard is fine") and the proposed reasoning ("it never fired") are different
> things, and only one of them is worth keeping.

---

## Orchestration correctness + exec verdict integrity (2026-08-03 → 2026-08-06)

Backfilled 2026-08-06. J19–J23 were assigned in code comments and tests as they were fixed but
never filed here, so the registry stopped tracking the exec/orchestration path after J18. J24–J27
are the findings from `exec-path-hardening`'s live e2e and from `gate-blindness-hardening`.

| ID | Sev | Status | One-line |
|---|---|---|---|
| J19 | 🔴 | **FIXED** `7929470` | `ok:true` is not delivery — a dispatch can return `injected:false` and exit 0; and acking a delivery to advance the queue DISCARDS every sibling report in it |
| J20 | 🔴 | **FIXED** `f33dda1` | Orca still DELIVERS a `worker_done` it lifecycle-rejected — matching on taskId alone launders a rejection into a completion |
| J21 | 🟡 | **FIXED** `1052c33` | a lifecycle rejection was acked off the queue and the await then timed out silently, discarding the only explanation of why that module would never report |
| J22 | 🟢 | **WONTFIX (decided)** `1134192` | a wrapper-side dispatch pane-readiness pre-flight was considered and deliberately rejected |
| J23 | 🔴 | **FIXED** `c5f6084`, `49cfc9f` | `exec` recovery read the prompt's own echoed contract block as the agent's verdict, and the tree-delta counter was whole-repo rather than `--cd`-scoped |
| J24 | 🔴 | **FIXED** `63fca45` | worktree-comment span replacement was glob-unsafe (`${current%$rest}` unquoted), so agent markdown made the strip silently fail and doubled the card |
| J25 | 🔴 | **FIXED** `379b881` | the Phase-7 `archreview` ladder had no `else`, so a record that never wrote the field returned `PHASE7: READY blockers=0` |
| J26 | 🟢 | **FIXED** `e3213d6` | `h_mad_extract_verdict.py` printed its `[H-MAD]` marker to **stdout**, so a `$(...)` capture yielded two lines and any writer fed that value refused it. Marker now on stderr; stdout carries only the verdict |
| J27 | 🟡 | **FIXED** `733a5f8` | doc tests sliced a magic 1600-char window; the section had already outgrown it, so a guard's scope depended on prose length |
| J30 | 🔴 | **CLOSED** `e2986fd` (+ `b6529c7`) | two halves, opposite outcomes. **Size premise DISPROVEN**: filed as `exec agy` dropping BOTH output contracts 5/5 at ~260 KB (2026-08-11); re-probed 2026-08-22 against agy 1.1.18 under `--output-format stream-json` and **8 of 8 honoured both**, with an 87,095 B control identical — the variable that moved was the TRANSPORT, not the size. The probe that settled it was work-shaped: a 260 KB requirements document with five contradictions planted end to end, all five found, which proves the whole prompt arrives AND is read; a trivial 260 KB prompt would only have proven argv is big enough. SKILL.md §"Prompt size" carries the measurement. **Off-contract write FIXED**: the surviving half — *"the failure is not that the work was skipped, it is that the artifact is unfindable"* — is closed by `h_mad_offcontract_scan.py`. Row was left stale for 5 days after the fix merged; see [[J42]] |
| J31 | 🔴 | **FIXED** `9eb47ae` (issue #39) | `h_mad_do_preconditions` reached past `has_gate_sections` into `classify()`, so an audit report with **no** gate headings scored `must_count=0` and CLEARED the Phase-5 gate — failing open, while the audit-gate CLI returned `GATE: INVALID` on the same file. New `INVALID:` detail line, distinct from `DIRTY:` |
| J32 | 🟡 | **FIXED** `f789315` | the doc-superset contract was enforced on the **template** only. A saved plan whose *authored body* mentions `plan-plus` / `Plan-Plus` / `Plan Plus` / `Brainstorming-Enhanced` / `Intent Discovery` is reclassified by bkit's `isPlanPlus` into a 13-section type the h-mad template cannot satisfy — ordinary prose, invisible to the template tests. New `h_mad_doc_shape_check.py` guards the saved document at Phase 3/4/7; base rate in this repo was 0/7 plans, so this is a trap that had not sprung yet |
| J33 | 🟡 | **FIXED** `f789315` | `test_h_mad_doc_templates.py` carried its own hardcoded copy of bkit's `REQUIRED_SECTIONS` and trigger literals, free to drift from both the checker and the live validator while staying green — and it **had** drifted: the trigger list was missing the lowercase `plan-plus`, which JS `includes` tests as a distinct string. Both tables now single-sourced from the checker, and `TestMirrorFidelity` diffs tables, literals, and verdicts against the live validator, failing on drift instead of skipping |
| J34 | 🟡 | MONITORING | `h_mad_assemble_tdd.py` composes `--out`/`--log` from the `--module` path verbatim, so a module in a subdirectory yields a path containing separators that names a non-existent directory. EVERY h-mad module lives under `h-mad/scripts/`, so every command block it prints for this repo carries it. Survivable because it prints commands rather than running them, but pasted verbatim it takes out `--out` AND `--log` at once, and that signature is indistinguishable from a dispatch that never ran — whose documented remedy is to re-dispatch onto a tree the agent may already have written. Fix: slugify the module, or key the filename on the task id. Found on the first live 5e use (F18 in the anchor-precheck dogfood ledger) |
| J35 | 🟡 | MONITORING | `hmad-dispatch progress` exited **1** on a normal LIVE poll during the anchor-precheck run. SKILL.md states it "is 0 for every observable state by design", precisely so nobody writes `progress … && continue`. Either the doc or the wrapper is wrong; the doc's reasoning is the one worth keeping, so the wrapper likely needs the fix. Not load-bearing here only because the contract says never to branch on it |
| J36 | 🟡 | MONITORING | An `exec codex` report stated the anchor sweep as `mutations=238` when the tree held **244**, every spec byte-identical to HEAD — a fabricated count inside an otherwise-correct report whose other figures checked out. Re-derive every count a dispatch reports; a report that is right about its actions can still be wrong about its numbers. Observed 2026-08-26 on the 6a-prime cycle-6 fix |
| J37 | 🔴 | MONITORING | `--check-anchors` and `run_spec` still collapse two distinct cannot-judges: `ANCHORS_DRIFTED` absorbs drifted-and-unreadable, and `REFUSED` absorbs a drifted anchor and an unreadable TARGET file. Raised independently by 6a-prime cycle 4 and matching the pre-existing F2 filing; deferred by operator decision as out of scope for the anchor-precheck feature, which introduced `PRECHECK_FAILED` and `ANCHORS_NOTHING_SWEPT` rather than widening to this. An operator's next action differs — re-anchor vs restore a deleted file |
| J38 | 🟡 | MONITORING | `h_mad_ab_dispatch.py --run` rejects any argv token beginning with `-` in the space-separated form SKILL.md documents: `--run --model` fails while `--run=--model` works. The documented invocation is the one that breaks (F6 in the anchor-precheck dogfood ledger) |
| J39 | 🔴 | MONITORING | `h_mad_ab_dispatch.py::_observe` takes the **FIRST** regex match where every other extractor in this skill takes the **LAST**. A prompt echo or a prior line therefore wins over the agent's actual observable — the same class as the `--after-marker` trap, in a tool built to measure causality (F4) |
| J40 | 🟢 | MONITORING | `h_mad_ab_dispatch.py` substitutes only `{prompt}` and `{log}`, so any other per-arm path collides between the A and B arms (F5); and it controls the prompt but has no notion of controlling the ENVIRONMENT, so an arm difference outside the declared variable is invisible (F3) |
| J41 | 🟢 | **FIXED** | The state schema has no field for the 5c baseline sha, though SKILL.md's 6a-prime (`BASE = 5c sha`) and 5f (`--base <5c sha>`) both take it. `h_mad_state_write.py` correctly REFUSED the invented key rather than letting it reach disk — the guard behaving exactly as designed is the point worth recording. **The row's own reason for not adding the field was false:** it claimed the value is derivable because `git merge-base main <branch>` "returned the exact commit". It does not. 5c is `git checkout -b …; commit impl-plan + audit files`, so the 5c commit is the branch's FIRST commit and the merge-base is its PARENT. Measured on the feature that filed this row: merge-base `b5c8f41`, real 5c `730cc16`, 313 lines apart — the impl-plan (249 lines) and its three audits, which the wrong base feeds into the 6a-prime diff as newly-added content when the contract makes them a separate INPUT. The verification was **circular**: the sha was confirmed by re-running the same command that produced it, with no control. **RESOLVED AS DERIVE, NOT STORE** — `h_mad_baseline_sha.py --branch <b> [--trunk main]`, reading the `BASELINE:` token. Both arguments cut the same way: a stored sha does not survive a rebase (it points at the old orphaned commit while the derivation recomputes and finds the new first commit, still 5c semantically), and a stored sha **cannot tell you it is wrong** — whereas "the branch's first commit is 5c" is a protocol invariant with an observable consequence, that the commit touches an impl-plan, so a violated assumption surfaces as `UNVERIFIED` instead of a confident wrong answer. That asymmetry decided it: the original defect was a wrong value indistinguishable from a right one, and storing would have preserved exactly that shape. **Only `OK` carries `sha=`**; `UNVERIFIED` reports the unvouched value as `candidate=` so a caller scraping `sha=` cannot receive something nothing stands behind. No schema change, no migration. Verified live against the real archived branch (returns `730cc16`, not `b5c8f41`) plus controls; 13 tests, `baseline_sha.json` 7/7 mutants caught, full suite 2212 passed. Documented at BOTH consumption sites and the doc test counts both — 5f and 6a-prime are read in isolation, so a warning at only one leaves the `merge-base` reflex intact wherever the reader lands (caught by an anchor that matched twice). |
| J43 | 🔴 | **FIXED** | **The wire registry silently performed the exact removal its own schema forces you to declare.** `register` upserted on `record["id"]` alone and `compare` keyed on the same bare `id`; `id` is the impl-plan task number `"Task N"`, which restarts at 1 for every feature, so any two features that both register a Task N collided by construction — and the successor MASKED the eviction, so `step5f:undeclared_removal` structurally could not fire. The schema meanwhile requires `status`/`removal_provenance`/`removed_by_feature` for a declared removal: the whole apparatus the upsert walked around. Measured over the full history of this repo's `.h-mad/wires.jsonl`: 7 distinct `(owning_feature, id)` pairs ever registered, 6 at HEAD, `audit-cycle-verb :: Task 4` (pin `test_fail_in_either_pass_fails_cycle`) GONE and `masked_by_same_id_at_HEAD=True`. It was also **unrestorable** — probed on a scratch copy, re-registering it evicted the successor, because the registry could hold exactly one `"Task 4"` across all features, ever. **FIX:** identity is now `(owning_feature, id)` via `_record_key()`, used by both `register` and `compare`; halt reasons carry `_record_label()` = `<feature>::<id>`, because a bare id names no single wire once two features have run and two simultaneous removals would otherwise emit the same line twice. `owning_feature` was already a required field, so no data migration was needed. The evicted record was restored **through the fixed write path** (6 → 7 records, both Task 4s coexisting), which is itself the proof: the same call that used to destroy is now correct. SKILL.md's halt-reason contract updated, and `step5f:wire_pin_ambiguous` — emitted but **undocumented**, a gap the fidelity scraper omitted on both sides and so could never see — is now documented and scraped. 7 new tests (RED first), 10 pre-existing format assertions updated to the scoped form, `wire_registry_key.json` mutation spec 5/5 caught, full suite 2197 passed. `challenge`/`partition` were audited this time: their `task['id']` comes from `_parse_tasks(impl_plan)`, where ids are unique within one plan, so they were never exposed. **6a-prime run 2026-08-27 (out of band, post-ship): `ASSESSMENT: READY_TO_MERGE`, evidence gate `PASS tools=12 ok=12 failed=0`** — `docs/05-review/features/wire-registry-feature-scoped-key.archreview.md`. The prompt stated there was no audited design rather than letting the reviewer invent one, and named the three low-confidence points; the reviewer independently re-audited `challenge`/`partition` and confirmed both were never exposed (their ids come from `_parse_tasks(impl_plan)`, unique within one plan), and backed `(owning_feature, id)` over redefining `id` — a UUID would sever traceability to the impl-plan numbering, and folding the feature into the `id` payload would force a migration of every `wires.jsonl`. See J44 for the sibling-repo restoration. |
| J44 | 🔴 | **FIXED** `c7c9a767` (HemaSuite, unpushed) | HemaSuite's HPW wire registry had lost 7 of 19 records to the J43 collision — a 37% loss rate, all masked. The J43 fix ships through the skills symlink (verified: HemaSuite carries no vendored copy of `h_mad_wire_registry.py`), so further losses stop everywhere automatically; records already gone do NOT self-heal. **All 7 restored 2026-08-27** through the fixed `register()` path — `hematology-paper-writer/.h-mad/wires.jsonl` 12 → 19 records, re-walk reports `LOST=0`, 0 duplicate keys, and **all 7 pins run green** (with the HPW venv — the repo interpreter fails collection on `ModuleNotFoundError: frontmatter`, which reads as a broken pin rather than a wrong interpreter). Restored: `article-path-ledger-wipe::Task 3` (orig ts 2026-08-15T13:33:12Z), `guideline-seeder-manuscript-path::Task 3` (2026-08-09T06:10:39Z), `knowledge-orchestrator-config-propagation::Task 4` (2026-08-13T04:55:48Z), `::Task 7`, `::Task 11`, `::Task 12` (same batch), `run-report-seam-restoration::Task 3` (2026-08-19T01:46:24Z). Original timestamps are recorded HERE because `register()` re-stamps `registered_ts` unconditionally; restoring via a hand-edit to preserve them would have bypassed the sanctioned write path and its readback check, and inventing a `restored_from_ts` field would repeat the ad-hoc-key mistake J41 records. The collision was worse than the count suggests: `Task 3` is now held by FOUR features and `Task 4`/`7`/`11`/`12` by two each — under the old bare-id key every one of those was queued to evict the last. HemaSuite's ROOT `.h-mad/wires.jsonl` was clean (6/6/0). **COMMITTED 2026-08-27 as `c7c9a767`** on `feature/clgcc-claim-like-guideline-citation-coverage`, scoped to the registry file alone — the rest of that working tree is another session's in-flight Phase-5 work (`claim-like-guideline-citation-coverage`, `phase: step5`) and was left untouched. Re-verified immediately before the commit because that tree kept moving: 19 records / 19 distinct keys, walk `LOST=0`, 7 pins green. Unpushed — HemaSuite carries its own `scripts/git-hooks/pre-push`, so a push there runs its own anchor sweep, and the branch is not this session's to publish. Backup of the pre-restoration file kept at the session scratchpad. |
| J45 | 🟡 | MONITORING | **`--release` has no ownership guard, so `--release` + `--claim` takes a LIVE owner's feature with no `--force` anywhere.** `claim()` refuses a live owner (exit 2, *"still live... pass force to take over"*) and its own docstring says `force` is *"the verb for taking a feature from a session that is still RUNNING"*, warning that routing routine cases through it *"teaches an operator to pass it by reflex, which is how the guard stops protecting the case it exists for"*. `release()` — one function below — clears `owner_session_id`/`owner_heartbeat_ts` unconditionally; its docstring says only *"Safe to call when unowned"*, which is true and is not the question. Measured on a scratch state file with the heartbeat set to NOW: (1) claim without force → REFUSED exit 2; (2) `--release` → OK exit 0, no guard, no warning; (3) claim without force → OK exit 0. Final owner is the second session and `phase` is still `step5`. The guard is advisory by design, so this is coordination rather than security — but the bypass is reachable by ACCIDENT, which is the realistic path: an operator tidying a stale claim releases the wrong feature, the tool says OK, and a third session then claims it with no friction and no signal to anyone. Found while releasing `gate-blindness-hardening`, whose 21-day claim was safe to release only because the oracle said `complete` and git confirmed the merge — the tool itself would have said OK either way. Note the handoff brief that opened this session wrote *"Releasing someone else's claim was not part of this transfer"*: the convention exists precisely because nothing enforces it. Fix shape, as HYPOTHESIS: give `release()` the same ownership window `claim()` uses (`h_mad_state_ownership`) — a stale claim releases freely (the routine case, no force reflex), a live one needs the same deliberate `--force`. That keeps both halves reading one window, which is the property `claim()`'s docstring says was already fixed once for exactly this reason. |
| J42 | 🟡 | **FIXED** | `h_mad_offcontract_scan.py` was tested and mutation-pinned but absent from SKILL.md's §"Helper scripts" registry, its verdict token `OFFCONTRACT:` scoring zero hits in SKILL.md and `references/` (positive control: `h_mad_wire_registry.py` twice) — so no orchestrator following the protocol could reach the tool that closes J30, which is J30's own finding reproduced in its own remedy. Registry entry added, describing the contract as PROBED LIVE rather than as assumed: `NONE`/`FOUND` both exit **0** — it reports and never decides — and only `UNREADABLE reason=no_workspace` exits 2. Pinned in the existing batch doc-rule harness, whose companion guard also requires the phrase be unique file-wide, so a deleted rule cannot pass on unrelated prose; mutation `drop-the-offcontract-token-from-the-registry` is killed by its own named test |

- 🔴 **J19 — `ok:true` is not delivery, and `--ack` is destructive.** Two defects in one fix.
  Measured 2026-08-03: `orchestration dispatch` can return `ok:true`, `status:"dispatched"`,
  `injected:false` and exit 0 — the task row is created and the worker is never told, so `await`
  sits until timeout with no diagnostic. Separately, one Orca Delivery holds **all** pending
  messages and `--ack` destroys the whole batch: a 2-message batch acked to `count: 0`, and
  `await <the other task>` then timed out for a module that had genuinely reported. In a fanout,
  modules finish in one order and are awaited in another, so that is the normal path, not an edge
  case. Fixed by an `injected=false` guard plus `_await_cache_put`, which parks every `worker_done`
  in a delivery before acking. The guard's own first implementation used jq's `//`, which treats
  `false` as null-ish and so never fired on exactly the value it hunted — caught by its own test,
  and the reason it now uses `has()`.
  Status: `FIXED` — `injected=false` guard plus `_await_cache_put`.

- 🔴 **J20 — a lifecycle-REJECTED report is not a completion.** Orca validates `worker_done` and
  can reject one (`missing_dispatch_id`, `sender_not_assignee`) while **still delivering it**, with
  `_orcaLifecycleRejection` in the payload. Matching on `taskId` alone therefore accepts a report
  the runtime itself refused — a false completion, which is the worst possible failure for a gate
  whose entire job is to decide whether work finished. Now parked separately, never as valid.
  Status: `FIXED` — a lifecycle-rejected report is now parked separately, never as valid.

- 🟡 **J21 — the rejection is the explanation, so do not discard it.** Once J20 stopped treating a
  rejected report as success, the naive fix (drop it) made `await` time out with no reason given,
  and whoever awaited first would have acked the only explanation off the queue permanently.
  `await` now surfaces the rejection and stops, rather than waiting out the clock. [[J20]]
  Status: `FIXED` — `await` surfaces the rejection and stops rather than waiting out the clock.

- 🟢 **J22 — deciding NOT to build a guard, recorded so it is not re-proposed.** A pane-readiness
  pre-flight before `dispatch` looks obviously right and is wrong on three counts, all measured:
  Orca refuses `--inject` into an agentless pane **atomically** (non-zero exit, empty stdout,
  `dispatch: null` afterwards — no row, no binding, nothing to clean up); a wrapper check would open
  a TOCTOU window the atomic path does not have; and it would have to re-derive "is an agent here"
  from signals separately proven unreliable — `terminal read` yields 0 lines for an idle
  restart-surviving pane, and hand-started panes are absent from `worktree ps`'s `agents[]`. It
  would false-refuse healthy panes. Kept as a row because the absence of a guard is invisible, and
  the next reader will otherwise propose it again.
  Status: `WONTFIX` — a deliberate decision NOT to build the guard, measured on three counts. Kept as a row precisely because the absence of a guard is invisible and would otherwise be re-proposed.

- 🔴 **J23 — `exec` laundered its own prompt into a verdict.** `codex exec … -` echoes the piped
  prompt into its transcript, so a recovery that greps the whole log reads the prompt's own output
  contract. Shipped a real false verdict on 2026-08-03: a dispatch that died on revoked auth
  returned `STATUS: NEEDS_CONTEXT` — the last option of its own contract block — and wrote it to
  `--out`, where the extractor accepted it. `agy --print` does **not** echo (the prompt is an arg),
  so the two backends genuinely need different recovery rules. Fixed by appending the same
  `===HMAD-DISPATCH-BOUNDARY===` that `send` uses and recovering only past its last occurrence;
  for codex a transcript with no boundary recovers **nothing** rather than guessing. The second
  half of the same fix: `git -C <subdir> status --porcelain` reports the **entire** work tree, so
  the "tree delta" that was supposed to prove work landed in `--cd` silently counted dirt from
  elsewhere in the repo. Found by replaying the real incident log against the fix — a different
  test from the unit tests, and the one that exposed a residual no-boundary hole that had passed
  RED. [[J26]]
  Status: `FIXED` — `exec` appends the same boundary `send` does and recovers only from after its last occurrence.

- 🔴 **J24 — tidy fixtures made a defect class unreachable.** `prefix="${current%$rest}"` left
  `$rest` **unquoted**, so bash glob-matched it instead of stripping a literal suffix. Production
  verdicts embed the agent's markdown (`[x](y)`, `**bold**`), so the strip failed and every stamp
  emitted the whole comment twice; the real worktree card reached **513 spans / 38,329 bytes**, and
  feeding it back through the composer reproduced it exactly (513 → 1026). This survived **1063
  tests, a clean 5/5 mutation sweep, five wire-scoped reverts and a clean architectural review**,
  and was found only by a live run — because every fixture used short glob-free ASCII. The bug was
  not under-tested; it was **unreachable**. The general shape: a fixture corpus is itself a
  coverage boundary, and one made entirely of tidy ASCII silently excludes whole defect classes.
  Closed on the fixture side by J25's feature (`HMAD_STUB_HOSTILE`). [[J25]]
  Status: `RESOLVED` — closed on the fixture side by J25's `HMAD_STUB_HOSTILE` feature. [[J25]]

- 🔴 **J25 — the architectural review was optional by OMISSION.** `h_mad_phase7_preconditions.py`
  branched on `WITH_FIXES`/`NO` and `SKIPPED_NO_PANE` with **no `else`**, so a record that never
  wrote `archreview` returned `PHASE7: READY blockers=0`. The documented `SKIPPED_NO_PANE` escape
  was not even needed to close a feature with no architectural review — simply never recording one
  was enough, and nothing marked the omission. Compounding it, §6a-prime's preflight required a
  resolved reviewer *pane*, which fails in the ordinary `exec`-default session, so the protocol
  steered runs straight into the hole. Fixed by `gate-blindness-hardening` (`379b881`): the ladder
  is now total, a skip blocks, a deliberate operator override closes with a warning, and 6a-prime
  is satisfied headlessly and records its own verdict. Proven on the identical record with the
  field removed — the old gate returned `READY`, the new one blocks. [[J24]] [[J26]] [[J27]]
  Status: `FIXED` — `gate-blindness-hardening` (`379b881`).

- 🟡 **J26 — `h_mad_extract_verdict.py` prints its marker to stdout.** `h_mad_extract_verdict.py:232`
  emits `[H-MAD] <feature> phase<N> <key>_<value>` with a plain `print()`, on the line directly
  after the verdict. Every consumer until now read the token by eye or grepped it, so this never
  bit; §6a-prime's new auto-record step is the first that **captures** the output into a variable
  and feeds it to `h_mad_state_write.py`, and the obvious `$(… | sed 's/^ASSESSMENT: //')` yields
  two lines. Observed live 2026-08-06 on `gate-blindness-hardening`'s own 6a-prime: the writer
  refused the malformed value and the read-back check reported `None`.

  **FIXED 2026-08-07.** The marker now goes to `sys.stderr`; stdout carries only `KEY: value`.

  **The sweep this row was blocked on is done, and it found nothing to break.** Across both repos,
  **no code captures this script's stdout at all** — every `h_mad_extract_verdict.py` mention in
  `hmad-dispatch.sh` (`:1677`, `:1766`, `:2017`) is a *comment*, and there is no `$(...)` or
  backtick capture of it anywhere in `.sh` or `.py`. The only consumer that captures is a human or
  orchestrator following §6a-prime — which is exactly the one that got bitten.

  **This row's stated fix direction was wrong about its own justification, and that is worth
  recording.** It said to route the marker to stderr "as the gate scripts already do". They do not.
  Every sibling prints its `[H-MAD]` marker to **stdout** — `h_mad_audit_gate.py:179`,
  `h_mad_mutation_harness.py:301`, `h_mad_phase7_preconditions.py:168`,
  `h_mad_state_staleness.py:210`, `h_mad_state_validate.py:235`, `h_mad_state_write.py:283`,
  `h_mad_wire_pin_gate.py:371`, `h_mad_wire_registry.py:500`. So `h_mad_extract_verdict.py` was
  *consistent*, not anomalous, and the filed remedy would have made it the only outlier.

  The fix is still right, on different grounds: this script differs in **kind** from its siblings.
  Their stdout is a report to be READ (`GATE: PASS must=0 should=0`); its stdout is a value to be
  CAPTURED — extracting a verdict for programmatic use is the whole job. That asymmetry justifies
  the inconsistency. Anyone later "harmonising" the markers should read this paragraph first.

  Two tests pinned the defect as an acceptance criterion and were corrected rather than deleted
  (regression provenance): `test_emits_hmad_marker_when_asked` asserted the marker was in
  `r.stdout`, and `test_extraction_capture_is_line_scoped` asserted `SKILL.md` *says* the marker is
  on stdout. Both now assert the fixed behaviour, and the new
  `test_stdout_is_only_the_verdict_so_a_bare_capture_is_safe` uses exact single-line equality —
  `in r.stdout` cannot catch this defect, because the bug was an EXTRA line.

  §6a-prime keeps the `sed -n 's/^ASSESSMENT: //p'` prescription: a bare `$(...)` is now safe, but
  a line-scoped capture cannot be broken by anything a future version adds to stdout.

  Mutations: `ALL_CAUGHT mutations=3 caught=3 survived=0 refused=0` (marker back on stdout; both
  doc guards). Dogfooded end-to-end — bare capture → `h_mad_state_write.py` → read-back, the exact
  path that returned `None` on gate-blindness-hardening.
  Status: `FIXED` 2026-08-07 — the marker goes to stderr; stdout carries only `KEY: value`.

- 🟡 **J27 — a doc test's scope depended on prose length.** The §6a-prime doc tests sliced a magic
  `s[idx : idx + 1600]` window. The section had already grown to **1707** characters, so its last
  107 sat outside every assertion, and the nearest required phrase had **76 characters of margin**.
  Two consequences, both real: a fix that added 299 characters would have pushed three unrelated
  guards out of scope and broken them for a reason having nothing to do with their subject; and a
  ban on the substring `h_mad_state_validate.py` passed **only because** the sentence warning
  against that validator fell past the cliff. Fixed in `733a5f8` by slicing at the real bullet
  boundary via a `section_6a_prime()` helper, and by replacing the blanket ban with a positive
  assertion of the warning — a string ban forbids naming an anti-pattern in order to warn about it.
  Mutation-verified including a mutation that reverts the boundary slicing. [[J25]]
  Status: `FIXED` `733a5f8` — slices at the real bullet boundary rather than a magic line count.

- 🔴 **J30 — `exec agy` drops its output contract on ~260 KB prompts, and writes the report
  somewhere you did not ask for.** This is **[[J28]] reproduced, with the missing variable named**:
  J28 recorded a single `exec agy` returning exit 0 having produced nothing and closed as
  unreproduced. It reproduces 5/5 once prompt size is controlled for, which is why one-off attempts
  at ordinary size did not repeat it — the anomaly was never random, it was size-gated. Treat J28 as
  the first sighting and this row as its mechanism.
  Measured across the `guideline-seeder-config-plumbing` design
  audits (2026-08-11): **5 of 5** dispatches at ~260 KB returned `rc=0` having honoured *neither*
  transport — no `--report-file`, no `<AUDIT_SENTINEL>` pair — while narrating that the audit was
  complete. This is the same claim-execution divergence catalogued as **F-10** in `AGENTS.md`, at a
  prompt size an order of magnitude past the ~92 KB pane frontier and ~88 KB assembled-audit
  maximum the skill documents, so no current guidance covers it.

  **The failure is not that the work was skipped — it is that the artifact is unfindable.** agy
  wrote a real report each time, at a path of its own choosing: once as a workspace **dotfile**
  (`.design.audit.v14.md`), which is invisible to the `*audit.v14*` glob the orchestrator searches —
  this is exactly how cycle 13 concluded "no file was written" and re-dispatched over completed
  work — and once into `~/.gemini/antigravity-cli/scratch/` while narrating "the current workspace".

  Two consequences for the gate. First, `h_mad_extract_report.py` exits 2 and the cycle halts, which
  is the *correct* failure (silence never scores as a clean gate) but sends you to the documented
  `no_verdict` remedy — `clear` and re-dispatch — which is wrong here: the audit already ran, and
  re-dispatching a ~260 KB prompt costs another full cycle to reproduce the same drop. Second, the
  §"A missing report on the `exec` path" recovery is explicitly scoped to *implementer* dispatches
  and disclaims audits ("the same bytes twice"), so an audit at this size currently has **no**
  documented recovery path at all.

  Recovery that worked: search for the artifact before re-dispatching — include dotfiles
  (`ls -a`, and a glob that does not assume the `audit.vN` stem) and `~/.gemini/antigravity-cli/
  scratch/` — then transcribe it into the gate's schema by hand and **falsify every premise against
  the source** (§"Verifying a review finding before acting on it"); a report recovered from an
  off-contract path has had no schema enforcement applied to it whatsoever.

  Related but distinct from the already-documented intermittent empty-slot case (2026-08-01, 358 B
  of narration at ordinary prompt size): that one is intermittent and cured by filling the
  report-file slot, whereas this reproduced **5/5 with the slot filled**. Size is the discriminator,
  and the fix direction is therefore a size ceiling on audit dispatch, not another transport.
  **Unverified:** the exact threshold between the ~88 KB known-good assembled audit and the ~260 KB
  known-bad, and whether the drop is agy-side or a `--print` truncation. [[J23]]

  **Re-probed 2026-08-22, and the size half did not survive it.** Eight `exec agy` dispatches at
  **266,342 B** (260.1 KB — matched to the known-bad size), against agy **1.1.18** under
  `--output-format stream-json`: **8 of 8 honoured BOTH transports**, writing the report to the exact
  `--report-file` absolute path *and* emitting the sentinel pair in the last message, with **no
  off-contract stray in any workspace**. A 87,095 B control passed identically. Five were trivial
  (write one file, echo it back); **three were work-shaped** — a 260 KB requirements document with
  five contradictions planted from one end to the other — and each of those three found **all five**.
  So the whole prompt arrives and is read: the drop is **neither** agy-side **nor** a `--print`
  truncation, which answers the Unverified question above by dissolving it. The 2026-08-11 5-of-5 was
  measured on an older agy build under the **text-mode** transport, which is the variable that moved.
  **The exact threshold was deliberately not bisected** — there is no known-bad size left to bisect
  toward, and spending dispatches on one would price a number nothing consumes.

  **What did NOT dissolve is the half the entry itself calls the real defect** — "the failure is not
  that the work was skipped, it is that the artifact is unfindable". Off-contract writes still happen:
  a second artifact, `~/.gemini/antigravity-cli/scratch/audit_report.md`, a real plan audit naming
  `EngineResult`/`grounding_totals`, was written **2026-08-22 14:57** — eleven days after the first,
  and not by any dispatch in this session (attribution unresolved; a live HemaSuite session was
  running). Two artifacts, two different names, neither matching an `audit.vN` glob, one of them a
  dotfile. That is what is now closed in code rather than in prose: `h_mad_offcontract_scan.py`
  searches the workspace **and** agy's scratch root, dotfiles included, assuming no stem, floored by
  mtime — `OFFCONTRACT: FOUND` lists candidates newest-and-most-report-shaped first, and `NONE` vs
  `UNREADABLE` are separate tokens so "I could not search" can never print what "I searched and found
  nothing" prints. It deliberately does **not** feed the gate: a report recovered from an off-contract
  path has had no schema enforcement applied to it, so transcription stays manual and every premise
  gets falsified against the source. `failure-recovery.md`'s audit no-report row now sends you to the
  scan **before** any re-dispatch, which is the step whose absence made a cycle re-dispatch over
  completed work.
  Status: `FIXED` — the unfindability is closed by `h_mad_offcontract_scan.py` + the recovery row; the size premise is **refuted at agy 1.1.18** (8/8 clean at the known-bad size), so re-probe before re-filing it against a future build rather than treating the 2026-08-11 measurement as standing.

> **Registry-hygiene note, 2026-08-06.** J19–J23 were fixed between 2026-08-03 and 2026-08-05 and
> referenced by ID in code comments and test docstrings the whole time, but never filed here — so
> for two weeks this registry read as though the exec/orchestration path had no known findings
> after J18. The IDs were reconstructed from those in-code references rather than reassigned, so
> every `J19`–`J23` mention already in the tree still resolves. The lesson is the one the J18 audit
> already recorded from the other direction: **a row that is never written is the same coverage
> hole as a row that is never flipped.**

## Surfaced by the agy skill review of the install-check work (2026-08-09)

- 🟡 **J28 — an `exec agy` dispatch returned exit 0 having produced nothing, and has not
  reproduced.** Observed once, live: `hmad-dispatch exec agy <7,539 B prompt> --cd <repo> --out
  <report> --log <run.log> --timeout 900`, launched backgrounded, completed with **exit 0, empty
  stdout, and neither `--out` nor `--log` created**. The identical command re-run in the foreground
  produced a full report in ~5 min. **Not filed as a diagnosis, because three plausible ones were
  tested and all failed**, and the registry-hygiene note above cuts both ways — a row asserting a
  wrong cause is worse than no row:
  - *No controlling terminal breaks `_exec_run`'s `set -m`.* **Refuted.** Extracted the real
    function and drove it with a trivial child under no TTY (`[ -t 0 ]` false, `[ -t 1 ]` false):
    `set -m` returns 0, the child runs, and the exit code propagates (`rc=7` for an `exit 7` child,
    `rc=0` with `--heartbeat`).
  - *Backgrounding the dispatch breaks it.* **Refuted.** The same verb backgrounded with a 65 B
    prompt completed in ~20 s and wrote both files.
  - *Two dispatches racing on one `--out`/`--log` starve one of them.* **Refuted** — see J29; both
    completed and both printed their own verdict.
  The original run had one confounder not present in any replication: a second `exec agy` was
  started in the foreground against the **same** `--out`/`--log` while it was still running, so its
  artefacts cannot be attributed to either run. **Under monitoring.** If it recurs, capture the
  transcript before re-running anything, since re-running is what destroyed the evidence the first
  time. Do not "fix" this without a reproduction.
  Status: `SUPERSEDED` by [[J30]], which reproduced it 5/5 once prompt size was controlled for and named the missing variable. Not unresolved — absorbed. J28 remains the first sighting. **That size mechanism was itself refuted on re-probing** — 8 of 8 clean at the same 266,342 B against agy 1.1.18 on 2026-08-22 — so do not read this line as a standing explanation; see J30's close for what survived (the off-contract write) and what did not (the size gate).

- 🟢 **J29 — `--out` is last-writer-wins across concurrent dispatches, silently; `--log` is not.**
  Verified deliberately while testing J28: two `exec agy` dispatches run concurrently against the
  same `--out` and `--log` both succeeded, but `--out` ended up holding **only the second
  responder's** answer while `--log` held both (it appends by design —
  `hmad-dispatch.sh` documents "Both backends append their transcript to a caller-supplied log,
  preserving its existing content"). So a caller who reads `--out` after a concurrent pair silently
  loses one verdict, and — because both dispatches exit 0 — nothing distinguishes that from a
  dispatch that was never run. **Lesson/opt:** give every dispatch its own `--out`, or have `exec`
  refuse to overwrite a non-empty `--out` it did not create. The cheap guard is the refusal; the
  cheap discipline is one path per dispatch.
  `GUARDED` 2026-08-09 — `exec` now fingerprints `--out` before dispatch and refuses to overwrite it
  at all three write sites (codex `cp`, agy `printf`, and the empty-final-message recovery) when the
  content changed in between. The refusal is keyed on **change**, not on non-emptiness: the literal
  reading above ("refuse a non-empty `--out`") would have refused h-mad's own documented recovery,
  since `references/failure-recovery.md`'s `no_verdict` remedy re-dispatches to a path templated per
  feature+module (`/tmp/rev_<feature>_<module>.txt`) that the failed attempt already filled with its
  short narration. A mutation run confirms the distinction is load-bearing — swapping the change
  check for `[ -s "$out" ]` kills only `test_exec_still_overwrites_a_stale_out_left_by_a_previous_attempt`.
  `rc` is deliberately untouched (it answers "did the CLI run"); the cure for a silent loss is the
  stderr line plus the preserved file, not a new exit code. The *discipline* half stands unchanged:
  one `--out` per dispatch. `hmad-dispatch.sh` `_out_clobber_ok`, SKILL.md §"Give every dispatch its
  own `--out`", 6 tests in `test_hmad_dispatch_exec.py`.
  Status: `FIXED` (`GUARDED` 2026-08-09) — `exec` fingerprints `--out` and refuses to overwrite it when the content changed in between, keyed on **change** rather than non-emptiness so h-mad's own documented `no_verdict` re-dispatch still works.

## Surfaced by the audit-cycle-verb Task 5 `/h-mad` run (2026-08-21)

- 🔴 **J34 — `h_mad_wire_registry.py verify` can never verify ANY wire: it compares bare pin names
  against full pytest node ids.** `collect()` (line ~370) builds `node_ids` from `pytest
  --collect-only -q` output, i.e. strings shaped `h-mad/tests/test_x.py::test_name`. `partition()`
  (line ~350) then tests `if record["pin"] in collected` — and `pin` is the **bare test name**,
  because that is what the impl-plan's `WIRE-PIN:` line carries and what 5b's auto-register writes
  into `.h-mad/wires.jsonl`. Exact set membership between the two forms can never hold, so every
  active pin partitions to `missing` and `verified` is structurally pinned at 0.
  **Measured on this tree**, with all six rows registered by 5b and four of their pins present and
  passing:

  ```text
  WIREREG: UNTRACKED registered=6 verified=0 broken=0 missing=6 …
  [H-MAD] step5f:wire_pin_missing:Task 5        # its pin exists and PASSES
  ```

  ```python
  collected = R.collect(Path("/Users/kimhawk/orca/skills"), [Path("h-mad/tests")])
  "test_verb_assemble_halt_no_dispatch" in collected                      # -> False
  [n for n in collected if n.endswith("::test_verb_assemble_halt_no_dispatch")]
  # -> ['h-mad/tests/test_hmad_dispatch_audit_cycle.py::test_verb_assemble_halt_no_dispatch']
  ```

  The failure direction is the safe one — it halts rather than passing a broken wire — but the
  consequence is that **5f has never actually verified a wire on any feature**; it has only ever
  reported `wire_pin_missing` or been skipped. A green 5f is not currently evidence of anything.
  Likely fix: match on suffix `::<pin>` (and require exactly one match, so an ambiguous bare name
  is a distinct verdict rather than a silent first-wins). Do not "fix" it by writing full node ids
  into the registry at register time — 5b learns the pin from a document that names a bare test,
  and the file it lives in can move.
  Status: **FIXED** 2026-08-21. `partition()` now resolves each pin by node-id **segment** suffix
  (`node_id.endswith("::" + pin)`), returning a 4-tuple `(resolving, missing, ambiguous,
  unverified_renames)`: exactly one candidate resolves and carries the full id in a new `node_id`
  key, zero is missing, and **two or more is `ambiguous`** — a new bucket with its own
  `step5f:wire_pin_ambiguous:<id>` driver and an `ambiguous=` field on the token, because two files
  may define the same test name and silently taking the first would verify a wire against a test in
  the wrong file. `run_pins()` now runs `record.get("node_id") or record["pin"]`, closing the same
  root cause one function downstream — it had been handing bare names to `pytest` as file paths, and
  had simply never been reached.

  **Why 60 green tests never saw it.** `test_collect_returns_pytest_node_ids` asserted node ids
  while all four `partition()` tests passed **bare names** as the collected set. Each was
  self-consistent, they contradicted each other across the seam, and nothing composed
  `collect()` -> `partition()`. Those four tests encoded the defect as their premise and were
  rewritten; a seam test over a real throwaway repo now covers the composition.

  **A mutation caught what the tests, the live token and review all missed.** With the fix in and 80
  tests green, dropping the `::` from the matcher changed nothing observable — `MUTATION: SURVIVED
  mutations=1 caught=0 survived=1`. The existing near-miss test pins the opposite direction (a pin
  *shorter* than the test name), where the delimiter is irrelevant. The discriminating shape is a
  pin that is a tail-substring of a test name: `wire` against `::test_wire` resolves wrongly without
  the `::`. That test now exists and the mutation is caught.

  Live proof, same command that produced the broken reading above:
  `WIREREG: UNTRACKED registered=6 verified=5 broken=0 missing=1 ambiguous=0` — Tasks 2-6 verified,
  Task 7 correctly missing because it is not implemented. First time 5f has verified a wire.
  Status: `FIXED` 2026-08-21 — `partition()` resolves each pin by node-id segment suffix.

- 🟡 **J35 — `h_mad_wire_registry.py` shells pytest via `sys.executable`, so a bare `python3`
  invocation cannot collect on a box whose `python3` lacks pytest.** Running the documented command
  as `python3 h_mad_wire_registry.py verify …` on this machine yields
  `RegistryError: pytest collection failed with exit code 1 … No module named pytest`
  (`/opt/homebrew/opt/python@3.14/bin/python3.14`), reported as `WIREREG: UNREADABLE`. Correct —
  it is a cannot-judge, not a verdict — but the remedy is undiscoverable from the message, which
  names the missing module rather than the interpreter choice. Invoking the *script* with
  `/opt/anaconda3/bin/python3.11` fixes it. Status: **FIXED** 2026-08-21 — both remedies shipped.
  `verify` takes `--python <path>` (default `sys.executable`), threaded into **both** `collect()`
  and `run_pins()`, and the collection-failure message now names the interpreter it used:
  `pytest collection failed with /opt/homebrew/opt/python@3.14/bin/python3.14 exit code 1 … No
  module named pytest`. Verified live both ways from a bare `python3` invocation.
  Status: `FIXED` 2026-08-21 — both remedies shipped.


## Surfaced by the audit-cycle-verb Phase 7 close-out (2026-08-22)

- 🔴 **J43 — Phase 7's archive step silently retired a test, because an empty `parametrize` SKIPS.**
  `test_premise_items_match_gate_count_real_artifacts` runs the premise extractor against a corpus
  of **real** collected audit reports — a Reimplementation-parity requirement added by design v1.19
  specifically so the check is not run only against synthetic fixtures. Its corpus,
  `REAL_AUDIT_REPORTS`, globbed the two **live** feature directories.

  Archiving this feature moved all 105 artifacts under `docs/archive/2026-08/`, and the corpus went
  from 8 files to **0**. pytest's response to an empty parameter set is not a failure:

  ```text
  SKIPPED [1] got empty parameter set ['report'] -- test_premise_items_match_gate_count_real_artifacts
  ```

  In a `-q` suite run that is one `s` among 1580 dots. The guard was gone and every gate stayed
  green.

  **This was not bad luck, it was scheduled.** Phase 7 archives *every* feature, so any corpus
  globbing only live directories is guaranteed to empty out — the only question was which feature
  would be the one to do it. Per-pass naming (`.p<i>`) is new with this verb, so this feature's
  artifacts were the entire corpus, and archiving them took it to exactly zero.

  Fixed two ways, because widening the glob alone would leave the same trap armed for the next
  structural change: `REAL_AUDIT_REPORTS` now also globs `docs/archive/*/*/*.audit.v*.p*.md`
  (96 candidates, capped at 8), **and** `test_real_audit_report_corpus_is_not_empty` asserts the
  corpus is non-empty so a future emptying fails loudly instead of skipping. Mutation-checked:
  removing the archive glob yields `1 failed, 1 skipped` — the guard fires, and the skip it exists
  to catch is visible right beside it.

  Sibling of the `pytest -k` selection trap already recorded on this machine: an empty selection
  exits 0. **Test the empty input for a non-empty body.**
  Status: `FIXED` — `h-mad/tests/test_h_mad_audit_cycle.py`.

- 🔴 **J42 — `audit-cycle` broke the telemetry cycle counter for every feature it audits, and the
  breakage reports as `0`.** `h_mad_cycle_counts.py:15` matched `_VERSION_RE = r"\.v(\d+)\.md$"`,
  while the verb writes one artifact **per pass**: `<feature>.<phase>.audit.v<N>.p<i>.md`. The glob
  `{feature}.{segment}.audit.v*.md` still matched those files — `v*` happily spans `9.p1` — so
  nothing errored; the regex then failed on every one of them and the count came back **0**.

  Measured at this feature's own Phase 7: `audit_cycles={'plan': 0, 'design': 0, 'impl_plan': 0}`
  for a feature carrying **plan v14, design v24, impl-plan v10**. After the fix, the same command
  reports `{'plan': 14, 'design': 24, 'impl_plan': 10}`.

  **A silent zero is worse than a missing number.** `0` reads as "no audits were run" — a claim
  about the work — where an error would have read as "the counter is broken". SKILL.md moved these
  counts to disk-derived precisely because the state fields never incremented and read `0/0/0`
  forever; this reintroduced the same symptom one layer down, and it would have been recorded into
  `.h-mad/telemetry.jsonl` as the permanent story of a 48-cycle feature.

  Fixed: `_VERSION_RE = r"\.v(\d+)(?:\.p\d+)?\.md$"`. Callers key results by the captured int,
  so two passes of one cycle collapse to one cycle with no further change. Both namings coexist,
  which matters because pre-verb features wrote `.v<N>.md`. Mutation-checked in both directions:
  reverting the regex fails the three per-pass tests, and making `.p<i>` **required** fails 16,
  including `test_live_repo_audit_cycles`, which pins real counts for older features.

  **Why no earlier gate caught it.** The 6a-prime diff never touched `h_mad_cycle_counts.py`, so a
  diff-scoped architectural review could not see it; the file is downstream of the feature, not part
  of it. It surfaced only when Phase 7 actually ran the reporter against real artifacts — the first
  moment anything read those filenames for meaning rather than writing them.
  Status: `FIXED` — `h_mad_cycle_counts.py`, with three regression tests.

## Surfaced by the audit-cycle-verb Phase 6 gap analysis (2026-08-22)

- 🟢 **J41 — the standing "real concurrency is untested by every lane" gap was overstated, and had
  been carried across three handoffs without once being probed.** The claim named four shapes and
  asserted the suite was "structurally blind" to all four because "the stub records under an `fcntl`
  lock". Probed this cycle:

  - **The suite does fork.** `_bindir()` symlinks a real `agy` stub onto an isolated PATH, so the
    dispatch loop forks real subprocesses and `wait` reaps real pids. The `fcntl` lock governs the
    stub's *recording*, not the forking. Those two were conflated when the gap was filed.
  - **Two shapes already have direct tests**: `test_verb_passes_one` (empty `pids` at `--passes 1`)
    and `test_verb_nonzero_exec_rc_is_forwarded_but_not_fatal`, which forces `HMAD_STUB_AGY_RC=17`
    and asserts the rc reaches the `--pass` payload verbatim while the cycle still returns PASS.
  - **The other two are not defects**, per a throwaway probe of the exact construct: a child dead
    before its reap still yields its status (`rc=[0 0]` — bash retains it until waited), a signalled
    child yields `128+n` (`rc=[143 143]`), and the shared fd carries only unscored stderr (6/6 lines,
    none lost).

  The probe also caught a defect **in itself** worth recording: `kill -TERM $$` inside `( … ) &`
  signals the **parent**, because `$$` is not re-set in a bash subshell — the probe killed its own
  script and exited 143. `$BASHPID` is the subshell's pid. A probe that appears to prove a violent
  failure may only be documenting its own bug.

  **The lesson is not about concurrency.** A plausible, specific, well-written gap survived three
  handoffs as established fact because each session restated it rather than ran it. A carried repro
  is not evidence.
  Status: `RESOLVED` — no code change; the analysis records the evidence.

## Surfaced by the audit-cycle-verb Phase 6a-prime dispatch (2026-08-22)

- 🔴 **J40 — an `exec agy` run that read NOTHING returned `ASSESSMENT: READY_TO_MERGE`, and every
  gate in the chain accepted it.** Measured on the first 6a-prime dispatch for `audit-cycle-verb`
  (log `/tmp/arch_acv.log`, conversation `179f6b21`). The run made exactly one tool call, a
  `view_file`, which **errored**; the result event carried `status: "ERROR"`; the response was a
  confident 1510-byte review asserting "No Critical or Important issues were found" about files it
  had never opened. `exec` returned rc 0 and `h_mad_extract_verdict.py` returned
  `ASSESSMENT: READY_TO_MERGE` with exit 0.

  **The path failure is the interesting half.** The dispatch's `--cd` was correct and the stream's
  `init.cwd` confirms it: `/Users/kimhawk/orca/skills`. But the prompt cited files repo-relatively,
  and agy resolved those against its own scratch directory instead of cwd:

  ```text
  view_file AbsolutePath=/Users/kimhawk/.gemini/antigravity-cli/scratch/h-mad/tests/test_h_mad_audit_cycle.py
    -> TOOL_ERROR ... no such file or directory
  ```

  So a correct `--cd` is **not** sufficient: cite absolute paths in any prompt that asks agy to read
  files, or the reads fail and the review proceeds on the inlined text alone.

  **This is NOT a wrapper bug, and fixing it there would reintroduce a defect.**
  `_agy_ndjson_response` (`hmad-dispatch.sh:1727`) reads `.response` regardless of `.status`
  *deliberately*, and its comment names the measured case: a single denied tool call yields
  `status: ERROR` alongside a complete, correct answer, so dropping that response would manufacture
  a `no_verdict` halt out of a run that answered. That reasoning is sound. The two situations are
  **indistinguishable at the transport layer** — one errored tool call out of many versus one
  errored tool call out of one — and only the consumer knows which it needed.

  The gap is therefore in the **6a-prime protocol**, which says to read the `ASSESSMENT:` with
  `h_mad_extract_verdict.py` and says nothing about the stream. A verdict-shaped line from a run
  that read nothing is exactly the "silence reads as approval" family the extractor exists to close,
  one level up: it is not silence, it is a *fluent* answer with no evidence under it.

  Proposed obligation for 6a-prime, stated as a rule the orchestrator can execute: after extracting
  the `ASSESSMENT:`, read the run's `--log` and require **at least one successful tool call** before
  recording a `READY_TO_MERGE`. `hmad-dispatch progress <log>` already prints tool events with their
  `ACTIVE`/`ERROR` state and a `RESULT status=` line, so this costs one call and no new script.
  A review that inspected nothing must not be able to clear the gate that exists to catch what
  document audits and code-level gap analysis miss by construction.

  **Fixed 2026-08-22 — the obligation is now mechanical.** `h_mad_review_evidence.py` reads the
  dispatch transcript and prints `EVIDENCE: PASS|NONE tools=N ok=K failed=J [status=…]`, exit 0 on a
  verdict and 2 on `UNREADABLE` (no `--log`, or empty), which carries **no counts** so a cannot-judge
  cannot read as a zero. 6a-prime must read it before recording an `ASSESSMENT:`; `NONE` halts
  `step6a-prime:review_read_nothing`.

  Validated against the two real transcripts from the incident itself:

  ```text
  arch_acv.log   (the blind review)  EVIDENCE: NONE tools=1  ok=0  failed=1 status=ERROR
  arch_acv3.log  (the real one)      EVIDENCE: PASS tools=26 ok=26 failed=0 status=SUCCESS
  ```

  Three properties are load-bearing and each is pinned by a test *and* a mutation:

  - **It gates on successes, not attempts.** Mutating `ok >= 1` to `tools >= 1` makes the real blind
    log report `EVIDENCE: PASS tools=1 ok=0` — the defect restored exactly.
  - **It knows no tool names.** The first probe of this very defect hardcoded
    `view_file|grep_search` from an earlier dispatch and returned a false zero when agy switched to
    `run_command`. Any tool reaching `DONE` counts.
  - **It does not gate on `result.status`.** `hmad-dispatch` ignores that field deliberately, and
    its comment names the sound reason; gating on it here would re-create the false `no_verdict`
    halt that reasoning exists to prevent. Status is reported for triage and never decides.

  The prompt-side cause is documented too, in SKILL.md and in the reviewer template: **a correct
  `--cd` is not sufficient** — cite files by absolute path, and instruct the reviewer to return
  `ASSESSMENT: NO` when its reads fail, so a blind review declares itself.
  Status: `FIXED` — `h_mad_review_evidence.py` + 16 tests, wired into SKILL.md and failure-recovery.

## Surfaced by the audit-cycle-verb Task 9 docs write (2026-08-21)

- 🔴 **J36 — the `audit-cycle-verb` spec, design AND impl-plan all state a measurement that the
  artifacts on disk contradict.** All three say the report-file slot was measured **"empty on 8 of 8
  impl-plan cycles"** (`…spec.md:238`, `…design.md:327`, `…impl-plan.md:840` — and, found later by
  the value sweep, `…impl-plan.md:854`, `…plan.md:397`, spelled `8-of-8`), and Task 9's AC-9.2
  asked for that sentence to be copied into `h-mad/SKILL.md`. Measured instead, from the staged
  artifacts of the feature's own impl-plan audit:

  ```text
  17 of 18 pass report files exist, non-empty, with 17 .done markers
  the ONLY absent one is cycle7_p1
  ```

  Cycle 7 pass 1 is exactly the case the impl-plan's own architecture constraint 2b describes —
  "`delivered=out,report-file` — the mixed case". So the plan contradicts itself: constraint 2b
  records one pass falling back to `--out` while AC-9.2 generalises that single pass into all
  cycles. The count is wrong twice over: there were **9** impl-plan cycles, not 8, and the
  measurement was per-pass, not per-cycle.

  **The claim is load-bearing in the safe direction, which is why it survived three gates.** It
  justifies always arming the `--out` fallback — a conclusion the real 1-in-18 measurement supports
  just as well, so nothing downstream is wrong; only the stated evidence is. That is precisely the
  shape an audit does not catch: a true conclusion resting on a false premise reads as correct to a
  reviewer checking whether the conclusion follows.

  Operator ruling 2026-08-21: SKILL.md carries the **measured** figure (shipped — see §6.6, "across
  the 18 impl-plan audit passes, 17 delivered via the report file"), and the three planning
  documents are corrected separately rather than silently amended, per the v1.15 precedent that an
  unaudited edit to a gated doc is an ungated doc.
  **Corrected 2026-08-21.** Spec v1.18, plan v1.12, design v1.22, impl-plan v1.9 — each carries a
  Version History entry naming the correction, so the edit is on the record rather than silent.
  The premise was re-verified independently before any edit, straight from the staged artifacts:

  ```text
  cycle{1..6,8,9}_p{1,2} + cycle7_p2 : report present, non-empty, .done written   (17)
  cycle7_p1                          : no report file, no .done marker             (1)
  ```

  **This finding under-scoped itself, in the way the value-sweep rule predicts.** It named three
  documents and three lines; the sweep found **six live sites across four documents** — the two
  extra in `impl-plan.md` (Task 9's description *and* its AC-9.2 checkbox) and one in `plan.md:397`,
  a success criterion that no reader of the three cited lines would have reached. The bare string
  `8 of 8` also misses `8-of-8`, which is how two of those three hid. Grep the **value in every
  spelling**, not the sentence you remember writing.

  Not edited, deliberately: `…design.md` v1.11 and the `design.audit.v8.p2` / `v12.p2` reports quote
  the old figure as a record of what that cycle found at the time. A revision log is append-only;
  rewriting it would erase the evidence that three gates passed over this.

  **Re-gated 2026-08-21** with the feature's own verb — plan c12, design c24, impl-plan c10, two
  passes each, all six delivered via the report file (`delivered=report-file,report-file` ×3). The
  correction itself gated clean: design p2 returned `must=0 should=0` over all 57 ACs with **AC-9.2
  `implemented-as-written`**, and not one of the 15 must-fixes across the three cycles mentions the
  measurement, AC-9.2, or any line this correction touched.

  Status: `FIXED` — corrected and re-gated.

- 🔴 **J37 — 14 of the 15 must-fixes from the J36 re-gate falsify against the shipped code.** The
  three cycles returned `FAIL must=5/3/7`, and triaging each against the implementation rather than
  against the prose it was written from:

  | claimed | shipped reality |
  |---|---|
  | plan drops the `.done` marker from the collection fast-path → torn-write race | `h_mad_audit_cycle.py:63` checks `_done_path(report_path).exists()` |
  | AC-4.4's "verified by re-reading" is unimplemented | both `_copy_collected_report:71` and `_write_collected_report:148` re-read and raise `OperationalError` |
  | Task 2 omits `collected_path.unlink(missing_ok=True)` | present at `:69` **and** `:146` |
  | `test_collected_write_failure_is_operational_error` missing | exists, `test_h_mad_audit_cycle.py` |
  | `test_gate_count_mismatch_is_operational_error` missing | exists, same file |
  | `test_premise_items_formats_{no_citation,supplied_path_line}` missing | both exist |
  | `test_premise_items_match_gate_count` lacks the real-artifact corpus | true of *that* test; the requirement is met by its sibling `test_premise_items_match_gate_count_real_artifacts:1555`, parametrized over the 8 reports `REAL_AUDIT_REPORTS:15` globs from `docs/0{1,2}-*/features/*.audit.v*.p*.md` |
  | no fixture for the delivered-but-no-`GATE:`-token guard | guard `:289`, test `test_combine_raises_when_delivered_pass_has_no_gate_token:635` |
  | no test for `size_status` worst-of aggregation | `test_verb_two_pass_dispatch_uses_distinct_per_pass_artifacts_and_worst_size_status:1142` |
  | `test_verb_unremovable_path` can't reach the post-removal guard because `set -e` aborts at `rm -f` | `rm -f … \|\| true` at `:2607` — the `\|\| true` is right there; the test asserts exit 3 **and** `channel not cleared`, which only the guard emits |
  | Task 5 omits `--passes` default 2 → bash crashes with `[: : integer expression expected` | **this one does not falsify — see J38.** The predicted *symptom* is wrong (`_need "$passes" --passes` exits 2 cleanly, no bash error), but the *concern* is right and the prescription restores documented behaviour rather than changing it: spec AC-3.1 says "Default pass count is 2" |

  **One survives**: `plan.md` states "five composed call sites" at `:278`, `:389` and `:424`, while
  `impl-plan.md:902` says "six call sites, six `wiring` tasks, six WIRE-PINs, twelve caller-side
  [mutations]" and `audit_cycle_connections.mutation.json` carries **12 rows**. Six is right; the
  plan's success criterion could be met while the shell→helper boundary went unverified.

  **Fixed 2026-08-22 (plan v1.13), and the count was the smaller half of it.** `.h-mad/wires.jsonl`
  enumerates the six pins outright, so nothing here needed inferring:

  ```text
  hmad-dispatch.sh:audit-cycle  -> h_mad_assemble_audit.py
  hmad-dispatch.sh:audit-cycle  -> exec agy
  hmad-dispatch.sh:audit-cycle  -> h_mad_audit_cycle.py     <- the one the plan dropped
  h_mad_audit_cycle.py:collect  -> h_mad_report_wait.py
  h_mad_audit_cycle.py:collect  -> h_mad_extract_report.py
  h_mad_audit_cycle.py:gate     -> h_mad_audit_gate.py
  ```

  The plan's list enumerated **callee scripts**, and the sixth call site is the only one whose callee
  is this feature's own new code rather than a pre-existing script — so a by-callee enumeration
  structurally cannot see it. That same list also **misattributed** three of its five:
  `h_mad_report_wait.py`, `h_mad_extract_report.py` and `h_mad_audit_gate.py` are called by the
  helper, not by the verb. Correcting only the number — which is all the finding asked for — would
  have left the process boundary described backwards, with the shell credited for three calls it
  does not make. **A count finding can be the visible edge of an attribution defect; fix what makes
  the count wrong, not the count.**

  Replaced with an explicit caller→callee table, and the success criterion now **derives** the number
  (`wc -l < .h-mad/wires.jsonl`, cross-checked against `h_mad_wire_registry.py verify`'s `verified=`)
  instead of restating it. That cure is the house pattern, already applied one bullet above in the
  same document for the AC count after a literal went stale twice (49→50→52).

  Not touched: `plan.md:5`, `:11`, `:14`, `:49` say the **hand-run** cycle is five calls, and
  `spec.md:12` says the same. Those are correct and must stay — the sixth call site exists only
  because the verb introduces its own helper, which the hand-run cycle had no equivalent of. A blind
  five→six sweep would have corrupted all five.

  **The lesson is the audit's reading surface, not its competence.** These passes read the planning
  prose and inferred what the code must therefore do. Most of the findings are *true about the
  document* — the docs really are thinner than the implementation — and false about the program. It
  is the claimed **consequence** that falsifies, not usually the fact: "missing test", "unenforced
  guard", "will crash" are each contradicted by shipped code.

  That distinction changes what the prescriptions cost. Thirteen of them are **doc** edits: harmless
  in themselves, merely unnecessary, but each one re-opens the re-gate obligation this cycle just
  discharged. Exactly **one** is a code change — arming a `--passes` default — and **it was the one
  finding here that is real** (J38). Falsify against the code **before** applying, every time; and
  when a finding names a test, grep the **file-scoped** name, not the bare one — the real-corpus row
  above reads as a genuine gap right up until the sibling test is found.

  **The correction to this entry is its most useful part.** A finding has three separable parts —
  facts, concern, prescription — and they fail independently. The `--passes` row arrived with a
  *fabricated symptom* (a bash error that does not occur), that symptom falsified cleanly against
  the code, and the falsification was then allowed to discharge the whole finding. It should have
  discharged only the symptom. Fourteen rows here survive re-examination; the fifteenth was thrown
  out for being wrong about something it did not need to be right about. **Falsify the claim the
  finding is actually making, not the story it tells about it.**
  Status: `FIXED` — five-vs-six corrected in plan v1.13 and re-gated at cycle 13, which raised no
  finding against it. Of the other 14, thirteen need no action and one is now J38.

- 🔴 **J38 — `--passes` has no default, and spec AC-3.1 says it must.** Spec AC-3.1: "Default pass
  count is 2." Design `:20` (`[--passes K=2]`) and `:368` (`# default 2, K>=1`) and plan `:33`
  (`[--passes <K>]  # default 2`) all agree. The shipped verb disagrees:
  `hmad-dispatch.sh:2562` declares `local passes=""` and the validation block calls
  `_need "$passes" --passes`, so omitting the flag exits 2 with `missing required argument:
  --passes` and no cycle runs. Three gated documents describe an optional flag; the code requires it.

  **Why 1560 tests never saw it.** The test helper `dispatch_args` is declared
  `def dispatch_args(*, feature=…, phase=…, cycle="7", passes="2", root)` and unconditionally emits
  `--passes` into every argv it builds. All 44 call sites therefore supply the flag. **The fixture's
  own default is a copy of the AC's default**, so the suite reads as though it covers AC-3.1 while
  no test ever exercises the path where the flag is absent. A default that only the fixture supplies
  is indistinguishable, from inside the suite, from one the program supplies.

  Sibling of the strawman-mutation class already recorded on this feature: the check appears to fire
  and is testing something else. Here the *fixture* appears to exercise a default and is supplying
  it instead.

  **Fixed 2026-08-22 by operator ruling** (code, not docs — three gated documents already promised
  the default). `hmad-dispatch.sh:2562` is now `local passes="2"` and its `_need` line is gone.
  Dropping `_need` costs no coverage: the `case "$passes" in ''|*[!0-9]*)` guard immediately below
  still rejects `--passes ""` with `must be >= 1`, verified live.

  RED first — `test_verb_passes_defaults_to_two_when_flag_is_omitted` failed with exactly the
  reported defect (`missing required argument: --passes`, rc=2) before the fix. The test helper
  `dispatch_args` gained a `passes=None` branch that **omits the flag**, which is the part worth
  keeping: the absent-flag path was previously unreachable from the suite at all.

  Mutation-checked both directions, and both are caught by that one test while the other three
  `passes` tests stay green — so it discriminates the value, not merely the presence:

  ```text
  local passes=""   (revert the default)  -> FAIL  1 failed, 3 passed
  local passes="1"  (wrong default)       -> FAIL  1 failed, 3 passed
  local passes="2"  (shipped)             -> PASS  4 passed
  ```
  Status: `FIXED`.

- 🟡 **J39 — `plan.md` is systematically narrower than `spec.md`, and it is a class, not a defect.**
  Plan re-audit cycles 13 and 14 each returned `FAIL` after every finding from the previous cycle
  was fixed, and cycle 14's six must-fixes are all one shape: the plan's "User-visible behaviour"
  summary omits a detail the spec mandates — the `reports:` line (AC-4.4/4.4b), the active rejection
  of `--passes N<1` (AC-3.1), the printed double-count warning (AC-5.4), and the `(no citation)`
  marker (AC-7.3). Cycle 13's two findings were the same shape and were fixed as plan v1.14.

  **The loop converges on the findings but not on the class.** Each cycle's findings are real about
  the document and each fix is correct; the next cycle simply reaches the next omission, because a
  summary document is *by construction* narrower than the spec it summarises. Chasing this one
  finding at a time re-opens a full re-gate per cycle and has no natural stopping point.

  **Resolved 2026-08-22 by reading what the document already does, and the answer inverts the
  finding.** `plan.md` has an established house pattern for exactly this: its `## Requirements`
  section (`:78`) lists the ten FRs **by title only**, restating no ACs, and its Risks table
  (`:400`) writes "per-pass counts printed alongside (AC-5.3) and the inflation stated (AC-5.4)" —
  it **cites** AC numbers rather than reproducing their text. The same document derives its AC count
  (`grep -c '^\s*- AC-'`) and, since v1.13, its call-site count (`wc -l < .h-mad/wires.jsonl`),
  both after a literal went stale.

  So the plan is *meant* to point at the spec, and cycle 14's prescription — add four more
  restatements of `reports:`, `--passes N<1`, the double-count warning and `(no citation)` — would
  have made the document worse: four more literals to drift, in a document whose own history is
  three separate corrections of exactly that. The drift it found is incidental prose paraphrase in
  Architecture Considerations, not a missing requirement.

  **And all four are present in the code** — `h_mad_audit_cycle.py:387` (`reports:`), `:389`
  (double-count note), `:339` (`(no citation)`), and `hmad-dispatch.sh` `--passes` (J38). So this
  was never an implementation gap; Phase 6a classifies it `design-vs-spec` and it does not reduce
  the match rate.
  Status: `RESOLVED` — no document edit made. Where prose paraphrases an AC, cite the AC; the
  pattern is already the document's own.

## Surfaced by the advisor-gate / run-cap live-fire (2026-08-24)

- 🔴 **J44 — the `advisor` PreToolUse hook does not fire on a real `advisor()` call.** The gate wired
  2026-08-19 (`h-mad/hooks/h-mad-advisor-gate.sh`, matcher `advisor`) has, on this evidence, never
  engaged in practice. It fails **open** and silently: an ungated `advisor()` costs a second full copy
  of the transcript, which is the exact overflow the hook exists to prevent, and nothing at the call
  site says the hook was skipped.

  **Measured twice, with a self-tested detector.** The hook was temporarily instrumented to append a
  line to a scratch file on entry; a real `advisor()` call was then made from this session.

  | run | marker position | detector self-test | real `advisor()` call | marker after |
  |---|---|---|---|---|
  | 1 | after the `tool_name` filter | writes when driven directly | made | **absent** |
  | 2 | **line 1**, before every branch incl. the override | writes when driven directly | made | **absent** |

  Run 2 is the one that settles it: the marker preceded the `HMAD_ADVISOR_OVERRIDE` early-exit, so
  "disarmed by an env var" and "never entered" are no longer the same observation — and the file was
  still empty. Absence is a real zero here, not a broken probe: the identical hook, instrumented, wrote
  the marker every time it was driven by hand (this is the [[J42]] / mode-15 discipline — assert the
  detector before believing its zero).

  **Everything else in the chain is individually verified, which is what isolates the defect to
  routing.** Registration present in `~/.claude/settings.json` at session start with matcher literally
  `advisor`; `$HOME` expansion and command dispatch proven by the sibling `Bash` and `Write|Edit`
  hooks, which use the identical `bash $HOME/…` form and fire on every call; the command path resolves
  through the skills symlink to the repo file; `HMAD_ADVISOR_OVERRIDE` unset. And the gate's own logic
  is correct on **every** branch when driven directly — DENY at a shrunk window against the real
  transcript, allow at the true window (the control, without which "it denied" proves nothing),
  override honoured, non-`advisor` tool ignored, and all three cannot-judge paths (checker absent,
  checker silent, checker exiting 2) allowing rather than blocking blind.

  **Leading hypothesis, untested:** `advisor` does not traverse `PreToolUse` at all — a harness-special
  tool rather than an ordinary one. Consistent with the transcript, where `Bash`/`Write`/`Edit` calls
  carry hook feedback on every invocation and the `advisor` calls carry none.

  **Next probe** (one fresh session; it subsumes the `HMAD_CONTEXT_WINDOW=1000` relaunch test that was
  carried for three handoffs): register a temporary `*`-matcher `PreToolUse` hook that logs `tool_name`
  to a file, relaunch, make one `advisor()` call. A logged line under some other name means the matcher
  string is wrong and the fix is one word; no line at all means `advisor` bypasses hooks entirely and
  the gate needs a different attachment point. Do **not** re-probe by making more `advisor()` calls
  from an already-instrumented session — two are enough and each bills a doubled turn.
  **ROOT CAUSE FOUND 2026-08-24, and the leading hypothesis was right: `advisor` does not traverse
  `PreToolUse` at all — no matcher string can attach to it.** It is a **`server_tool_use`**, executed
  server-side, so it never enters the harness's local tool-dispatch path where tool-scoped hooks run.
  The next-probe above (a `*`-matcher logger + relaunch + one `advisor()` call) is **subsumed, not
  skipped**: it was designed to distinguish "wrong matcher string" from "bypasses hooks entirely", and
  two cheaper measurements answer it decisively without another billed advisor turn.

  | evidence | what it shows |
  |---|---|
  | 2.1.241 binary: `"Advisor model for the server-side advisor tool."` and `"Enable the server-side advisor tool …"` | the harness itself calls it server-side |
  | binary emits `server_tool_use` / `advisor_tool_result` blocks beside `mcp_tool_use` and `tool_use` | it is a distinct block kind with its own render path |
  | binary hook-event table: the only tool-scoped events are `PermissionRequest`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure` | all four are local-dispatch events |
  | **live transcript**, 3 real `advisor()` calls: recorded as `server_tool_use` name=`advisor`; the 101 hooked calls are `tool_use` | in-situ proof, not strings-archaeology |

  **Fixed as an ADVISORY, because enforcement is structurally impossible.** `PreToolUse` could have
  denied the call; nothing can. `hooks/h-mad-advisor-warn.sh` rides **`PostToolUse`** — the event whose
  firing rate tracks the risk, since tool results are what grow a transcript — and injects the budget
  verdict as `additionalContext`, reaching the model in the orientation window where it decides. The
  dead `{"matcher": "advisor"}` PreToolUse registration is **removed from `~/.claude/settings.json`**;
  that registration WAS the harm, because a hook that cannot fire reads as protection. `h-mad-advisor-gate.sh`
  is deleted rather than left on disk for an install to re-wire. `h_mad_hook_wiring.py` now knows the two
  h-mad hooks live under different events and reports `HOOK_NOT_WIRED` for an advisory registered under
  `PreToolUse` — J44's exact shape, now caught by the checker.
  No override env var: an advisory has nothing to escape, and shipping an escape hatch tells the reader
  it blocks. Throttled to one emission per 60 s — not for cost (~60 ms) but because a warning reprinted
  on every tool call is the context bloat it exists to prevent.

  **Two mutants proved EQUIVALENT and were dropped from the spec rather than left as false coverage:**
  `set -euo pipefail` (every rc-producing command in the advisory is guarded, so nothing propagates —
  it was the CENTRAL defect for the gate, where exit 2 meant block, and is inert here) and the
  missing-checker guard (without it `python3 <missing>` fails, the verdict is empty, and the hook exits
  silently anyway). The remaining 12 mutants are all caught. The mutation harness also caught a
  **weak test of mine**: `hostile-session-id-builds-a-path` survived because my first version created
  the wrong parent directory, so the unguarded write failed for a reason unrelated to the guard.

  **VERIFIED LIVE, INCLUDING HARNESS INVOCATION — and that closed a second, unrelated wrong belief.**
  First driven by hand through the `~/.claude/skills/h-mad` symlink: silent at `CTXBUDGET: OK`
  (30.4%), emitting the documented `hookSpecificOutput` JSON at 76.2% with the window shrunk to 400k,
  silent again on the immediate second call. I recorded the harness half as *owed to the next
  session*, on the standing rule that hooks are snapshotted at session start — **and then the harness
  fired it in THIS session, ~13 minutes after the registration was written**, injecting
  `[H-MAD] Context budget: 63.4% …` as `additionalContext` on an ordinary `Bash` call. Not a
  look-alike: the throttle stamp it left is keyed by this session's real id
  (`h-mad-advisor-warn.c426d098-….stamp`, written 22 s earlier) and the percentage tracked the live
  transcript, which also confirms PostToolUse payloads carry both `session_id` and `transcript_path`.
  **So "hooks are snapshotted at session start" is false on 2.1.241 for at least PostToolUse
  registration.** SKILL.md now tells the reader to VERIFY rather than to assume either direction —
  an unverifiable claim about hook arming is precisely what let J44's dead hook look installed for
  days. Nothing is owed.
  Status: `FIXED` — `hooks/h-mad-advisor-warn.sh` + wiring swap; suite 1651 passed, 12/12 mutants
  caught, live harness invocation observed in-session.

- 🟢 **J45 — `--mode run`'s HALT cannot trip the advisor hook's DENY glob; proven mechanically.** The
  two ceilings were given different verdict words on purpose (`DENY` at 45% for `--mode advisor`,
  `HALT` at 80% for `--mode run`) so a dying run cannot be matched by the advisor hook's
  `*"CTXBUDGET: DENY"*` case. Verified rather than asserted: a checker emitting a real
  `CTXBUDGET: HALT mode=run …` line, driven through the advisor hook, exits **0** (falls through to
  allow). Across windows 100k/300k/550k/1M no `--mode advisor` output ever contains `HALT` and no
  `--mode run` output ever contains `DENY`, and at 550k the two disagree as designed (advisor `DENY`,
  run `OK`) — which is the case that proves they are separate questions and not one threshold with two
  names.
  Status: `FIXED` — property confirmed live; no code change needed. Recorded so the word choice is not
  "simplified" later by someone who reads the two tokens as duplicates.

- 🔴 **J46 — the output contract at the TAIL of an audit prompt is dropped, and the audit becomes
  unscoreable.** On `grounding-evidence-coverage` impl-plan cycle 21 BOTH passes ignored the entire
  output-framing block — no sentinels, no `## Summary`/`## Must-fix`/`## Should-fix`/`## Nit` schema,
  no report file, no `.done` — and each invented its own verdict line (`GATE: PASS must=0 …` /
  `GATE: FAIL must=1`), so `h_mad_audit_gate.py` returned `GATE: INVALID` on both. Both had done real
  work (100 s / 11,230 thinking; 193 s / 15,786 thinking / 34 tool calls) and pass B's content held a
  genuine must-fix. It was simply unscoreable.
  **This is PLACEMENT, not size, and a LARGER prompt succeeding is what proves it** — do not re-file
  it as a size effect ([[J30]]'s size premise was refuted 8/8 separately). Re-measured 2026-08-24
  through the real assembler: tail-only at **223.6 KB** wrote no report file and no `.done` and
  emitted the literal `<AUDIT_SENTINEL>` placeholder instead of this pass's substituted value, so
  `h_mad_extract_report.py` exited 2 — a *sharper* mechanism than cycle 21's wholesale drop, same
  outcome. Head-duplicated at **234.3 KB** it wrote the report file, wrote `.done`, used the real
  sentinel and the exact schema; `extract_report` exited 0.
  The head copy is SLICED from the assembled text after slot fill, never hand-written — a
  hand-written copy would hardcode a report path and schema that drift from the template's — and an
  anchor-miss is a preflight HALT, not an exception, so a custom `--template` is rejected as a
  verdict rather than a crash.
  Status: `FIXED` — `97cb07f` (`h_mad_assemble_audit.py::prepend_output_contract`), 4/4 mutants
  killed, full suite 1639 passed.

- 🔴 **J47 — the audit gate's empty-section sentinel was punctuation-intolerant and false-FAILed.**
  `_count_section_findings` compared `p.lower() == "none"`. A reviewer writing `None.` — with the
  trailing period agy writes — missed the sentinel, fell through the fail-safe branch ("non-`None`
  content with no countable bullet → count 1") and **manufactured one phantom finding per section**.
  Observed live: `grounding-evidence-coverage` impl-plan cycle 23 pass B wrote `Must-fix: None.` /
  `Should-fix: None.` and scored `GATE: FAIL must=1 should=1` with nothing behind it. This is the
  mirror of [[J40]] — that one was a false PASS, this one a false FAIL — and both make the gate's
  output a claim about the *scorer*, not the work.
  The fail-safe *direction* is right and is untouched; only the sentinel comparison is normalised,
  in one helper used at BOTH call sites (the `all(...)` check and the bullet filter — the second
  matters only in a mixed section, a real finding beside a `- None.` bullet). The comparison stays a
  full-string match after trimming, never a prefix match, so a finding that merely begins with the
  word None still counts.
  Status: `FIXED` — `7df6ab6`, 4/4 mutants killed.

- 🟡 **J48 — `result.status` must never gate an audit, and the `.tmp`+`mv` staging advice that first
  exposed it is gone.** The audit template told the reviewer to stage its report through
  `<path>.tmp` and `mv` it into place "for a hard atomicity guarantee". The `.done` marker ordering
  in the very next clause already IS that guarantee, so staging only added two tool calls to the
  delivery path. Removed.
  **The premise correction matters more than the removal.** The handover brief attributed a specific
  cycle-22 `status: ERROR` to agy's artifact sandbox refusing the `.tmp` write. A direct probe of
  that premise on 2026-08-24 did **not** reproduce it — the `.tmp` `write_to_file` and the `mv` both
  reached `DONE`. So the refusal is nondeterministic, not a property of the surface, and the advice
  is removed for redundancy and cost, not for a mechanism this repo can demonstrate on demand.
  What IS confirmed, three times with three unrelated causes, is the consequence: **any** failed or
  refused tool call makes a run report `status: ERROR` beside a complete, correct report. (1) the
  refused `.tmp` write from the brief, on a report carrying two independently-verified real findings;
  (2) a `find_by_name` timeout plus a `view_file` on a nonexistent path — 31 tool calls, 29 ok,
  schema-correct report; (3) a `write_to_file` rejected for a missing `CodeContent` argument that the
  agent immediately retried successfully. `h_mad_review_evidence.py` has followed this rule for
  6a-prime since it was written; the audit path now says so too.
  Status: `FIXED` — `81d956b` (template + SKILL.md step 9 + references/orchestration-mode.md), pinned
  by a test so the advice cannot creep back.

- 🟢 **J49 — an audit pass that made no tool calls audited the PROMPT, not the codebase, and nothing
  surfaces that.** Across the 8 passes of cycles 21–24, *every* substantive finding came from a pass
  with either high thinking tokens or ~34 tool calls. Cycle 21 pass A ran **0** tool calls and
  returned "CLEAN PASS" on a plan pass B proved defective. Cycle 24 returned a double-clean with
  thinking collapsed to 6.2 k / 4.4 k (vs 11–23 k in all six earlier passes) and exactly 2 tool calls
  each — the `write_to_file` and the `.done` marker, i.e. no reads at all. A hollow pass is
  indistinguishable from a real clean pass at the gate line; today it is only visible by opening the
  NDJSON. `h_mad_review_evidence.py` already computes `tools=N ok=K failed=J` for 6a-prime and knows
  no tool names, so the counts exist — they are simply not surfaced beside an audit verdict.
  Note this is a *scoring caveat*, not a defect in any script: a pass with 2 tool calls honoured the
  contract exactly as asked.
  **FIXED 2026-08-24.** `h_mad_review_evidence.scan()` now also sums `usage.thinking_tokens` over
  completed `agent_response` steps (`EVIDENCE: … thinking=T`), `hmad-dispatch audit-cycle` threads
  each pass's NDJSON log to the combiner as an optional 5th `--pass` field
  (`i:<report>:<out>:<rc>[:<log>]`), and `h_mad_audit_cycle.py` renders an **`Effort:`** block beside
  the verdict with per-pass `tools=/ok=/failed=/thinking=`.

  **The `low-evidence` marker is derived from the CONTRACT, not from tool names.** The report-file
  delivery contract itself costs two successful calls — write the report, create the `.done` marker —
  so `ok <= 2` means the pass cannot have successfully read anything. Classifying calls as
  reads-vs-writes would have re-created [[J40]]'s first-probe defect, where a hardcoded
  `view_file|grep_search` reported a false zero the moment agy switched to `run_command`;
  `scan()` knows no tool names on purpose and still does not.

  **It reports; it never decides, and the tests pin that both ways.** `combine()` cannot see the
  block, the `AUDITCYCLE:` line is byte-identical whether a pass was hollow or exhaustive, and the
  same clean report yields the same verdict either way. This is the same discipline as `result.status`
  ([[J48]]): a caveat that can move a verdict is a gate wearing a caveat's name. The caution is
  earned rather than theoretical — **a pass in this very repo scored 5,356 thinking / 2 tool calls,
  the exact hollow signature, and still returned a real finding** (the D-1 post-fix dispatch). Treat
  `low-evidence` on a clean pass as a reason to re-dispatch that pass, never as a verdict.

  A log that was named but could not be read renders `unreadable`, never zeros — `tools=0` is
  precisely what a genuinely hollow pass looks like, so zeros from an unread file would manufacture
  the finding. The mutation harness caught the sharp form of that: an **empty but existing** log
  survived until a discriminating test was written (assert existence and content as two columns).

  Verified end-to-end on two REAL agy logs from this session's dispatches — one hollow
  (2 tools / 5,356 thinking, flagged) and one deep (31 tools / 8,339 thinking, unflagged) — both
  gating `PASS`, with one identical `AUDITCYCLE:` line above them.
  Status: `FIXED` — suite 1668 passed, 12/12 mutants caught (`tests/mutation-specs/audit_effort.json`).
