# Handoff — duplicate-skill advisory shipped; Phase-5 gate scope fix queued for /h-mad

**Date:** 2026-11-23
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-20-main__read-dream-step-mcp-fixes.md
**Next-Session Focus:** Fix the open Phase-5 policy finding (Next Step 1), then start `/h-mad phase5-gate-feature-scope` in a fresh session.
**Suggested-Skills:** h-mad (the operator chose the full seven-phase route for the gate fix), verify-hmad-gates (prove any gate change end to end)

## Session Summary

Resumed from the 2026-11-20 handoff and closed its top item: the OMC MCP server connects in a live session. The session then replaced the cmux block in the codex `AGENTS.md` with an Orca block, ran `omx setup` on both codex homes, and removed two duplicate codex skills. The one repo change is `8977ca86` (pushed): `h_mad_install_check.py` now reports a skill name duplicated between a codex home and the agents root, verified by a full suite of 9300 passed, a 32/32 mutation run and three independent review rounds. Last, the session traced why a codex planning lane in HemaSuite keeps asking the operator to `git apply` allow-list patches; the operator chose to fix that in h-mad through `/h-mad`, which has not started.

## Key Learnings

- **The codex Phase-5 gate is armed repo-wide by any one feature at `step5`.** `_any_phase5_status` (`h-mad/scripts/h_mad_target_identity.py:338`) scans every `docs/.bkit-memory.json` under the root. HemaSuite's `issue-187-file-root-move-refusal` sat at `step5`, so a codex session planning a different feature (`csa-column-mapper-jev`) had every non-safe shell command denied. Audit-phase commands are not in `SAFE_HMAD_SCRIPT_OPTIONS` or `SAFE_DISPATCH_VERBS`, and codex may not write `.h-mad/phase5-shell-allow`, so it hands the operator a patch each cycle (four on 2026-11-23).
- **`Path.is_dir()` changed meaning for an unreadable directory.** Up to Python 3.13 it raises `PermissionError`; from 3.14 it returns False. The suite runs on 3.11 and production `python3` here is 3.15, so one code path crashed in tests and read "absent" in production. Use `os.stat` and separate ENOENT/ENOTDIR from other errors.
- **`/clear` does not respawn MCP servers.** A "failed to connect" notice after `/clear` is the attempt from process start. `/mcp reconnect <name>` tests a fix without a restart; the MCP log under `~/Library/Caches/claude-cli-nodejs/<project>/mcp-logs-<server>/` shows whether a new attempt happened.
- **`omx setup` refuses a codex home whose `.omx` is a symlink.** Orca links an account home's `.omx` to `~/.codex/.omx`. Running against `~/.codex` works and refreshes the shared `agents/` and `AGENTS.md`; the Orca home's own `config.toml` and `hooks.json` need the link replaced by a real directory first.
- **A new line in a script can break another feature's mutation spec.** A second `Path(agents_skills_dir).expanduser()` made `install_check_roots.json` D4a match twice and the harness answered `PRECHECK_FAILED` for every spec. Run `h_mad_mutation_harness.py --check-anchors` after adding code to a file that already has specs.
- **A shared tree changes under a long session.** Between verification and commit another lane left uncommitted edits in this repo. Staging by explicit path and comparing the `git diff -- <my files>` checksum with the verified one kept the commit to the verified content.
- **Code mode still blocks Remote Control on Claude Code 2.1.330** (read from the binary's strings, not from a live refusal).

## Next Steps

1. **Fix the output-path check in the Phase-5 shell policy** (`h-mad/scripts/h_mad_target_identity.py`, `_option_value`, `_path_within`). A gate weakness already on `main` before this session, found by review and confirmed. Details are kept out of this public repo: session task #10 and `/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/open-gate-finding.md`. Small fix with tests, mutations and a review; the operator has not yet said whether to start it.
2. **Run `/h-mad phase5-gate-feature-scope`** in a fresh session on a clean tree. Brief:
   - Problem: the Key Learnings entry above. Evidence: `HemaSuite/.h-mad/phase5-shell-allow` (18 lines, all exact commands), patches `/private/tmp/p16-plan-*.patch`, state `HemaSuite/docs/.bkit-memory.json` (`issue-187-file-root-move-refusal` at `step5`, `csa-column-mapper-jev` with no phase).
   - Goal: a codex session working on a feature that is not in Phase 5 is not shell-gated because a different feature is.
   - Open design questions: how the gate learns which feature a session serves (worktree path, owner session, an explicit declaration); whether the agy and Claude gates share the defect; what happens to a session that serves no declared feature; fail-closed behaviour when the mapping is unreadable.
   - Constraint: `hmad-dispatch audit-cycle` runs an arbitrary `--suite-cmd`, so widening the safe list cannot cover it. The operator rejected the narrow safe-list fix as the main route.
   - Re-run the premise first: `python3 - <<'EOF'` reading `orchestrator_state` phases in `/Users/kimhawk/orca/HemaSuite/docs/.bkit-memory.json`; if #187 has left `step5` the live symptom is gone but the defect is not.
3. **Re-pin or relaunch the codex and agy panes** before any dispatch: `hmad-dispatch env` reads `PREFLIGHT: FAIL stale=codex,agy`. Read each pane's tail before trusting a pin.
4. **Fold the memory-index trim into the next `/memory-dream`** (operator decision 2026-11-22). The index was 18,127 B on 2026-11-22 against a 17,500 B target; no hand trim.
5. **Before any OMC update:** `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/upstream.py`. Read 2026-11-22: `UPSTREAM: EMITS tag=v5.8.4 npm=5.8.4`.
6. **After any OMC update:** in the new `~/.claude/plugins/cache/omc/oh-my-claudecode/<version>/` run `npm install --omit=dev --ignore-scripts`, then `npm rebuild better-sqlite3`. Never run `scripts/plugin-setup.mjs`.
7. **On the Macmini**, after `git pull`: the catch-up list in the superseded handoff's Next Step 5, unchanged.
8. **Retire the OMC patch** once `upstream.py` reads `FIXED`.

## Open / Blocked Items

**From this session:**
- **Phase-5 gate scope fix** — status: not started; route chosen by the operator is `/h-mad` (Next Step 2).
- **Foreign uncommitted edits in this tree** — status: settled 2026-11-23. Their author was the operator's P14 codex session (HemaSuite, 2026-11-22). The `--authors-test` rule was finished and pushed as `e506d871` (full suite 9326 passed, mutation 20/20, review must=0; the last small edits not re-reviewed). The P14-only gate exception and its three files were retired: P14 shipped in HemaSuite PR #202. Backup: `/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/`.
- **`authors-test` limits noted by review, not fixed** — status: accepted for now. A looped link resolves differently on Python 3.13+, and a project root spelled through an outside link is judged physically.
- **HemaSuite P16 lane still needs an allow line per audit cycle** — status: unchanged until the gate fix lands or #187 leaves `step5`. Owned by the HemaSuite lane; `/private/tmp/p16-plan-rounds3-4.patch` is already applied there.
- **Codex `AGENTS.md` and both codex homes changed outside the repo** — status: done, untested in a live codex turn. `~/.codex/AGENTS.md` has an Orca block in place of the cmux block and `gpt-6-luna` in Subagent Defaults. `omx setup` ran on `~/.codex` and on the Orca account home, adding OMX hooks, a notify dispatcher (the Computer Use notifier is kept as `previousNotify`) and `developer_instructions` to each. An OMX `PreToolUse` hook now runs in the codex pane h-mad dispatches to; no TDD-gate dispatch has been run with it. Backups: `~/.codex-backups/2026-11-22-pre-omx-setup/`, `~/.codex-backups/2026-11-22-pre-omx-setup-orca-home/`, `~/.codex/AGENTS.md.pre-orca-block-20261122`, `config.toml.pre-subagent-model-20261122` beside each config.
- **Orca may recreate the `.omx` symlink in the account home** — status: open risk; `omx setup` would refuse again, the config entries stay.
- **Two duplicate codex skills moved to backup** — status: done. `ieumoffice` from `~/.codex/skills` and the stale `h-mad` from the Orca home's `skills/` are under `~/.codex-backups/2026-11-22-pre-omx-setup/`. IeumOffice may rewrite its copy on update; the install check now reports that.
- **Duplicate-skill advisory, stated limit** — status: accepted. Pins are matched by real path; whether codex canonicalises a `[[skills.config]]` path is unmeasured. The last small edits (empty `--codex-home` line, absolute homes, newline-safe parse, doc wording) were not re-reviewed.
- **`.omc/notepad.md` trimmed from 455,802 B to 300 B** — status: done. Backup `.omc/notepad.md.bak-2026-11-22-pre-trim` is the only copy of the old entries. OMC never prunes automatically; only the `notepad_prune` tool does.
- **OMC dependency advisory** — status: examined, not fixed. `zod` 3.25.76 in the 5.8.4 cache; `npm audit` cites GHSA-mrhx-c7xc-m3w5, fix is a major bump inside a vendor cache. The advisory text was not read.
- **ai-memory calls resolve to `default/scratch`** from this project's sessions — status: informational; pass `workspace=default`, `project=skills` (a later notice named `brightgold70-skills`; not re-checked).
- **Scratch dirs** `/private/tmp/skilldup-r2.1KHJTb`, `/private/tmp/skilldup-r3.6QW6Y3` and this session's scratchpad (review reports `review-skilldups-round{1,2,3}.md`, suite and mutation logs) — temporary, safe to lose.

**Carried from 2026-11-20 (read-dream-step-mcp-fixes):**
- **Next Step 1, confirm the OMC MCP server connects:** closed — connected after `/mcp reconnect plugin:oh-my-claudecode:t` on 2026-11-20, 50 tools, `notepad_stats` answered. The cause was only the missing `node_modules`.
- **Next Step 2, queue-note hook nits:** closed — the HemaSuite lane rewrote the hook on 2026-11-20 (`dream_lint hooks=0`); the index trim moved to Next Step 4.
- **Next Steps 3–6 (`upstream.py`, post-update `npm install`, Macmini catch-up, retire the patch):** unchanged (Next Steps 5–8).
- **OMC fix adds 173 MB of `node_modules` to the 5.8.4 cache and lasts until the next OMC update:** unchanged.
- **Codex config edits from 2026-11-20** (`ai-memory` stdio bridge, serena `startup_timeout_sec = 180`): unchanged and still present after `omx setup` (checked 2026-11-22).
- **A later `ai-memory setup` may write the bearer-token form back:** unchanged, open risk.
- **Codex `code_mode` warning; no ai-memory or serena tool called from inside codex; serena's slow start:** unchanged, not investigated.
- **Codex pane relaunch note and old Orca pins:** closed — superseded; pins are stale again (Next Step 3).
- **ai-memory never-ended session `2fafec5c`:** closed — read on 2026-11-20; it is the memory-dream session and its last prompt produced the memory-dream handoff.
- **Memory-store edits and backups under `~/.claude/memory-dream-backups/`; nothing prunes before 2026-12-19:** unchanged.
- **10 dangling memory links kept as deliberate markers:** unchanged, accepted (`dream_lint` 2026-11-22: `DANGLING=10`, `orphans=0`, `last_dream=3d ago`).
- **AC-7 live run (asset-legend-native-citations):** handed over, owned by HemaSuite session f9973721. Not ours; not re-checked.
- **HemaSuite #178 test leak:** closed — fixed by their PR #184, merged 2026-11-20.
- **Deferred memory-dream ideas** (generic `split` subcommand; rejected hook-older-than-body check): unchanged.
- **Older scratch dirs under `/private/tmp/claude-501/`:** unchanged, temporary.

**Carried from 2026-11-18 (omc-update-check), via the predecessors:**
- **OMC patch applied on MacStudio for 5.8.4:** unchanged, `VERIFY: OK files=4` on 2026-11-22.
- **`upstream.py` checks the GitHub tag and npm, not the marketplace cache build:** unchanged, accepted.
- **Codex `[[skills.config]]` pins from 2026-11-18; Orca's `skills/handoff` copy deleted:** unchanged; `codex-duplicate-handoff/verify.py` read `VERIFY: OK` after both `omx setup` runs.
- **Orca copy may reappear if OMX setup re-runs:** closed for this run — it did not reappear; the risk stands for future runs. **Pins break on every Matt Pocock plugin update:** unchanged.
- **Known limits of `codex-duplicate-handoff`** (flow-mapping name, scan depth, plain-file race, nested/BOM SKILL.md): unchanged, accepted. Its `verify.py` now has a second user (`h_mad_install_check.py`), recorded in its README §Retiring.
- **OMC patch exists only on MacStudio; the Macmini is unreachable by ssh from MacStudio** (do not retry): unchanged.
- **Older scratch artifacts** (`991d87bb…`, `a571186a…`, `b68348df…`, `013414ea…`, `f7b82980…`, 43 unreviewed scratch reports on another machine): unchanged, temporary.
- **`~/.claude.json` context7/sequential-thinking entries; edits outside the repo from 2026-11-09:** unchanged, expected.
- **Two timing-based tests kept as fixed sleeps; Pyright `timeout=None` warning at `test_hmad_dispatch_exec_stamp.py:458`; opencode `$schema` change (`bd6a47ca`):** unchanged, accepted.
- **Hand-started Codex session still ungated; another hook in `.codex/hooks.json` withholds the bypass; two unanchored hook-trust plumbing lines; hard-link kinds differ by host (all DENY):** unchanged, accepted. The Orca home's `hooks.json` now also carries OMX hooks; this repo's `.codex/hooks.json` was not changed.
- **Rust toolchain `stable-aarch64-apple-darwin`; foreign PID 32561:** unchanged, informational.
- **Accepted items unchanged since 2026-11-08** (`argument_not_printable` NBSP/U+202F/ZWJ refusal; two unpinned `_enc` print sites; `unreadable-file` first; `crash_visible=0/0` on host specs; scout row `hand-applied-single-mutants`): unchanged.
- **Items closed in predecessors** (scratch-dir deletion `6df9db7a…`, `899d9bdf`/`cd885d09`, Macmini sync #16, dispatch `NOT enforced` watch, heartbeat flake + mutation row, codex `ignoring 2 unrecognized configuration settings`): unchanged.
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over, owned by HemaSuite, unchanged.
- **Macmini untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.
- **Orca worktree comment:** this WRITE restamps it.

## Context for Next Session

**Also committed, in `e506d871`:** `h-mad/scripts/h_mad_target_identity.py`, `h-mad/tests/test_h_mad_codex_runtime.py`, `h-mad/tests/mutation-specs/gate_authoring_scope.json`.

**Files touched this session (committed in `8977ca86`):**
- `h-mad/scripts/h_mad_install_check.py`
- `h-mad/tests/test_h_mad_install_check_codex_skill_dups.py`
- `h-mad/tests/mutation-specs/install_check_codex_skill_dups.json`
- `h-mad/tests/conftest.py`
- `h-mad/references/helper-scripts.md`
- `h-mad/references/codex-runtime.md`
- `docs/patches/codex-duplicate-handoff/README.md`

**Outside the repo:** `~/.codex/AGENTS.md`, both codex `config.toml` and `hooks.json` files, `~/.codex/agents/*.toml`, `~/.codex/skills/` and `prompts/` (OMX install), the Orca home's `.omx/`, `.omc/notepad.md`, one memory note (`reference_code_mode_off_for_remote_control.md`).

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect clean, in sync with origin/main
hmad-dispatch env                  # expect PREFLIGHT: FAIL stale=codex,agy until re-pinned
python3 h-mad/scripts/h_mad_install_check.py   # expect INSTALL: PASS and no CODEX_SKILL_ line
```

**Related docs:** `docs/handoffs/2026-11-20-main__read-dream-step-mcp-fixes.md`; `h-mad/references/codex-runtime.md` (hook trust and duplicate-skill advisories); `h-mad/hooks/h-mad-codex-tdd-gate.py` and `h-mad/scripts/h_mad_target_identity.py` (the gate and its policy); `docs/patches/codex-duplicate-handoff/README.md`.
