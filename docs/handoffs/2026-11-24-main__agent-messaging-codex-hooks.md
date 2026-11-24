# Handoff — agent-messaging, Reason Network pilot and Codex hook repair

**Date:** 2026-11-24
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-24-main__phase5-gate-plan-approved.md
**Next-Session Focus:** two independent lanes. (A) `/h-mad phase5-gate-feature-scope` resumes at Phase 3, plan audit cycle 1 (inherited, unchanged). (B) Finish the Codex idle-wake test once the Reason Network hooks are trusted.
**Suggested-Skills:** h-mad (lane A), verify-hmad-gates (lane A gate changes), agent-messaging and reason-network (lane B), orca-cli (disposable Codex terminal for lane B)

## Session Summary

Reviewed `reason-machines/reason-network` v0.12.17 and published two skills: `agent-messaging` (new, `85232de4`) and the Codex lane's `reason-network` (`47e5f87b`, committed unchanged). Then found and repaired the Codex "hook exited with code 127" failures: oh-my-codex (OMX) had stored a versioned Homebrew Node path. Upstream issue #4153 was filed and fixed on their `dev` within the day, so our PR was not submitted. Codex idle wake over Reason Network is **not working yet**: the first test returned `pull` with no wake, the missing hooks were restored, and they now wait for the operator's trust in `/hooks`.

The inherited phase5 lane was not touched. Every open item of its handoff is carried below.

## Key Learnings

- **Orca rebuilds the account home's `hooks.json` when it starts Codex.** The result is exactly `~/.codex/hooks.json` plus Orca's own hooks (measured: 0 missing, 9 extra, all Orca's). A hook added only to the Orca account home disappears at the next start. Add it to `~/.codex/hooks.json`.
- **Codex's hook trust covers the command text.** Changing only the Node path turned 14 trusted hooks to `modified`. `codex app-server` method `hooks/list` reports the live trust status. Append new groups at the end of an event, because trust is keyed by position.
- **OMX refuses `setup` and `uninstall` while its hooks are edited but not re-trusted** ("Refusing to replace existing Codex hook trust state"). Reproduced on upstream code in throwaway homes, not on the installed 0.21.5.
- **"No code 127 in the pane" is not evidence while the hooks are untrusted,** because they do not run. The valid check was a fresh `codex exec` plus the session files the hooks write.
- **Reason Network's `[inbound] default = "hold"` screens other machines only.** Same-machine sessions deliver directly (`src/daemon/mail.rs:966` is the only policy call, on the remote path).
- **Skill tests need a no-skill control.** Baseline runs already handled peer authority, secrets and pleasantries, so the skill spends its words on recipient choice, retry keys, stage wording and refusals.
- **Process slip:** `agent-messaging` was pushed on a 19/20 regression plus an untested wording change. The exact text later passed 20/20 twice (Haiku and Sonnet). Run the regression before the push.

## Next Steps

**Lane B — Codex and Reason Network**

1. **Operator: trust the 5 Reason Network hooks** in a new Orca Codex (`/hooks`, or the "5 hooks are new or changed" screen; each command is `reason-network hook codex …`). Plain Codex has its own separate trust. At 12:55 both homes read 5 `untrusted`, 7 OMX `trusted`.
2. **Re-run the idle-wake test** after that. Check trust: `python3 -I /Users/kimhawk/orca/_worktree-backups/2026-11-24/agent-messaging-codex-hooks/trust.py "$CODEX_HOME"`. Then start a disposable Codex with `orca terminal create --worktree path:/Users/kimhawk/orca/skills --command "codex --no-daemon -s read-only -a never '<setup prompt>'"`, wait for `tui-idle`, confirm `reason-network who` shows it as `push`, send a nonce from `reason-network listen --as wake-probe`, and require a new turn **and** the reply with nothing typed. Close the terminal. The control run (hooks absent) gave `pull` and no turn in about 78 s.
3. **Confirm the interactive pane.** The pinned codex pane was restarted after this repair (Codex 0.172.0 per the other lane). Look for new "code 127" lines after a turn that runs a command.
4. **When OMX ships the release after 0.22.19:** update, then run `omx setup` once. It should succeed in `~/.codex` while the hooks are trusted. The Orca account home may refuse because its `.omx` is a symlink to `~/.codex/.omx` (observed 2026-11-24).
5. **Before anyone else joins the Reason Network team:** turn private folders off with `reason-network folder <path> off`. `reason-network who` already lists this machine's Claude sessions by folder and title.

**Lane A — phase5-gate-feature-scope (inherited)**

6. **Run `/h-mad phase5-gate-feature-scope`** in a fresh session. Claim the feature, then read `h-mad/references/audit-prompt-assembly.md` and the opening part and dispatch-channels section of `references/phase5-substeps.md`. Decide the four "Spec items owed" below and route them to `spec-author` (v1.3), then `plan-author` if the plan's text moves. Precheck, then: `hmad-dispatch audit-cycle --feature phase5-gate-feature-scope --phase plan --cycle 1 --project-root /Users/kimhawk/orca/skills --passes 3 --surfaces codex,agy,grok`, with the suite flags SKILL.md requires. Two gating rounds at most. The feature's own record is armed and cleared only by the installed writer.
7. **Settle the documents' home.** Brainstorm, spec and plan are untracked in this shared checkout; 5c commits them, earlier only if the operator asks. Never commit the author reports.
8. **Probe codex before dispatch** (`hmad-dispatch probe codex`). `hmad-dispatch env` read `PREFLIGHT: PASS` at 12:55. Check the OMX `PreToolUse` hook in the first dispatch: OMX hooks run again since this session, but only SessionStart and Stop were seen to run.
9. **Decide the private follow-ups** S4, S5, R2, R3 and T1: `/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/open-gate-finding.md`.
10. **Fold the memory-index trim into the next `/memory-dream`** (due about 2026-11-26). After this closeout: 19,032 B against 17,500, `DANGLING=13`, `orphans=0`, `last_dream=5d`, one `HOOK_UNSUPPORTED`.
11. **Before any OMC update:** `python3 docs/patches/omc-codex-mcp-no-type/upstream.py`. **After one:** in the new `~/.claude/plugins/cache/omc/oh-my-claudecode/<version>/`, `npm install --omit=dev --ignore-scripts`, then `npm rebuild better-sqlite3`; never run `scripts/plugin-setup.mjs`. **Retire the OMC patch** once `upstream.py` reads `FIXED`.
12. **On the Macmini**, after `git pull`: copy `docs/patches/patch-verify-on-update.sh` to `~/.claude/hooks/`; `python3 docs/patches/codex-duplicate-handoff/verify.py --fix`; `python3 docs/patches/omc-codex-mcp-no-type/apply.py` then `verify.py`; `ln -s ~/orca/skills/memory-dream ~/.claude/skills/memory-dream`; probably the `npm install` of step 11. New: `agent-messaging` needs its own links in `~/.claude/skills` and `~/.agents/skills`, and an OMX setup there may carry the same versioned Node path.

## Open / Blocked Items

**This session:**
- **Codex idle wake** — blocked on the operator's hook trust (Next Step 1). Never observed working.
- **Code 127 repair** — done and verified in fresh `codex exec` runs for both homes (0 occurrences; SessionStart and Stop hook files written). Not verified in an interactive turn; the other OMX events were not seen to run; no broken-path control was run through `codex exec`.
- **Edits outside the repo:** Node path in `~/.codex/hooks.json` and the Orca account home (backup `~/.codex-backups/2026-11-24-pre-node-path-fix/`); 5 Reason hooks appended to `~/.codex/hooks.json` (backup `~/.codex-backups/2026-11-24-pre-reason-hooks/`, includes config files, mode 600). The second edit reformatted the file. Trust of 19 hooks was written by Codex at the operator's request (11:51); the 5 Reason entries in it were then lost with their hooks.
- **Plain `~/.codex` now has the Reason hooks but no Reason MCP server** — accepted for now; not tested.
- **One hook-trust observation kept private** — memory `project_reason_network_pilot.md`. Not for this public repo.
- **OMX upstream** — issue https://github.com/Yeachan-Heo/oh-my-codex/issues/4153 closed by #4155 (`2518b49` on `dev`), not released at 12:55 (npm 0.22.19). Remaining upstream gaps, not reported: `node@NN` formulas, and the plugin launcher's `process.execPath` (`src/cli/plugin-marketplace.ts:3747`).
- **Our OMX PR** — withdrawn as redundant; nothing forked or pushed. Patch kept in the evidence directory. Its full suite showed 646 of 9,544 failing in an isolated environment, cause unknown because the `dev` baseline was stopped. Do not reuse the patch without that comparison.
- **`agent-messaging` limits** — scored by its author from dry runs on Claude models; no live message and no Codex model tested. Minor open review points: `request-show` after a silent Orca timeout, ai-memory static-client scope, Reason file rules (`review2.md`). One soft tension in section 3 (repo-only match for new work).
- **`reason-network` skill** — no independent review. Codex reported a live round trip, retry de-duplication and Claude idle wake; not repeated here.
- **Reason Network pilot** — one machine, one member, team `orca-pilot`, `auto_update = false`, daemon started by hand, no login service. `doctor` lists other agents as not wired, by choice.
- **Evidence (private):** `/Users/kimhawk/orca/_worktree-backups/2026-11-24/agent-messaging-codex-hooks/` — scenarios, two reviews, trust probe, migration harness, issue text, unsubmitted patch.

**phase5-gate-feature-scope** (inherited, unchanged; repo: `/Users/kimhawk/orca/skills` · branch: main · worktree: none yet, the plan requires one before 5a):
- **State observed 12:56** — `phase: null`, `current_phase: 3`, `last_completed_phase: 2`, no owner, no halt reason.
- **Documents** — `docs/01-plan/features/phase5-gate-feature-scope-brainstorm.md` (v1.3), `.spec.md` (v1.2, `14c66d81…`), `.plan.md` (v1.1, `b3cc9c0b…`); both hashes re-checked. Author reports and copies: `/Users/kimhawk/orca/_worktree-backups/2026-11-24/phase5-gate-feature-scope/` (private).
- **Operator rulings** — scope by checkout; protect the arming fields; root and sub-project state files only; one rule for every gate; shell gate from 5d; an ungated session performs the exit; moved-checkout residual accepted; git environment variables ignored in the codex and agy root lookups (D7); FR-6 covers the session's and the target's own checkout; listed Pythons, Linux simulated and reported as such; a landing report before landing. All in the documents.
- **Orchestrator rulings the operator may reverse** — spec elaborations a to i accepted; AC-2.8's fixture avoids git rather than changing the judge's environment.
- **Spec items owed** (wording in `author_phase5-gate-feature-scope_plan_v2.report.md`) — not decided. (1) The AC-2.8 residual sentence. (2) AC-2.8: a value that changes what git answers. (3) NFR: the 2 s bound covers git calls this feature adds. (4) Assumptions: record the v1.2 approval. Plus one design question: FR-6 in the Claude hook for an off-chain sub-project's linked state file whose real file has another name. The old/new mixture corpus was narrowed by its author; reverting it is described in the report.
- **Landing** — blocked on the feature. Run the landing report first and show it to the operator. A codex or agy orchestrator at `step5` then needs an ungated exit.
- **Lessons that still bind** (details in the superseded handoff) — write state to the real file, never through a symlinked `docs/.bkit-memory.json`; a "no tests pin this" claim needs a positive control.

**Gate work, earlier (inherited, unchanged):**
- **Option-judging fix (`74ba0661`)** — live. The full suite ran before the rebase; the last test-only edit was not re-reviewed (mutation 32/32 with it).
- **Sub-project relative state writes** — refused today; re-ask after the feature.
- **`--authors-test` rule (`e506d871`)** — edits after its last review not re-reviewed; limits accepted (looped link on Python 3.13+; a root spelled through an outside link judged physically).
- **Retired P14 gate exception** — done; backup in the directory of Next Step 9.

**Owned elsewhere (inherited, not re-checked):**
- **`csa-column-mapper-jev` (P16)** — repo: `/Users/kimhawk/orca/HemaSuite` · branch: `main` · worktree: none. Owned by session `d26fd99c`; at 12:09 `step5`, marker `step5c_worktree_creation_retry`, halt `step5c:isolated_worktree_command_blocked_by_shell_allowlist`. The allow lines in `HemaSuite/.h-mad/phase5-shell-allow` are that lane's route until the feature lands. Its recorded 346-commit lag behind `origin/main` was not re-checked.
- **HemaSuite #187 worktree** — repo: `/Users/kimhawk/orca/HemaSuite` · branch: `feature/187-file-root-move-refusal` · worktree: `/Users/kimhawk/orca/workspaces/HemaSuite/issue-187-file-root-move-refusal`. Armed by the P16 record through its symlinked state file; that lane should write to `/Users/kimhawk/orca/HemaSuite/docs/.bkit-memory.json`. Operator told; lane not messaged.
- **AC-7 live run (asset-legend-native-citations)** — handed over, HemaSuite session f9973721.
- **HemaSuite drafting quality without `CLAUDE.md`** — handed over, owned by HemaSuite.

**Codex environment (inherited, updated where noted):**
- **`~/.codex/AGENTS.md` Orca block, `gpt-6-luna` subagent defaults, `omx setup` on both homes** — **updated:** OMX hooks ran in live codex turns today; no gate dispatch has run with the OMX `PreToolUse` hook. Backups: `~/.codex-backups/2026-11-22-pre-omx-setup/`, `~/.codex-backups/2026-11-22-pre-omx-setup-orca-home/`, `~/.codex/AGENTS.md.pre-orca-block-20261122`, `config.toml.pre-subagent-model-20261122` beside each config.
- **Orca may recreate the account home's `.omx` symlink** — **confirmed:** it is a symlink again.
- **Duplicate codex skills (`ieumoffice`, stale `h-mad`) moved to backup** — done; IeumOffice may rewrite its copy.
- **Duplicate-skill advisory limit** — accepted: pins matched by real path, codex's own rule unmeasured; last small edits not re-reviewed.
- **Codex `ai-memory` stdio bridge and serena timeout 180** — unchanged; a later `ai-memory setup` may write the bearer-token form back.
- **Codex `code_mode` warning; no ai-memory or serena tool called inside codex; serena's slow start** — not investigated.
- **Codex `[[skills.config]]` pins; Orca's `skills/handoff` copy deleted; pins break on every Matt Pocock plugin update; the copy may reappear on an OMX setup re-run** — unchanged.
- **Known limits of `codex-duplicate-handoff`** (flow-mapping name, scan depth, plain-file race, nested/BOM SKILL.md) — accepted; `h_mad_install_check.py` is its second user.
- **Hand-started Codex session still ungated; another hook in `.codex/hooks.json` withholds the bypass; two unanchored hook-trust plumbing lines; hard-link kinds differ by host (all DENY)** — accepted.

**OMC and Claude Code (inherited, unchanged):**
- OMC patch applied on MacStudio for 5.8.4 only; `upstream.py` checks the tag and npm, not the marketplace build. 173 MB of `node_modules` in the 5.8.4 cache until the next update.
- OMC `zod` advisory (GHSA-mrhx-c7xc-m3w5) — examined 2026-11-20, not fixed, advisory text not read.
- `.omc/notepad.md` trimmed; `.omc/notepad.md.bak-2026-11-22-pre-trim` is the only copy of the old entries.
- Code mode blocks Remote Control on 2.1.330; setting stays `0`. (This session ran on 2.1.331; not re-tested.)
- ai-memory calls resolve to `default/scratch`; pass `workspace=default`, `project=skills`.
- `~/.claude.json` context7/sequential-thinking entries; edits outside the repo from 2026-11-09 — expected.

**Memory store (inherited, unchanged):**
- Edits and backups under `~/.claude/memory-dream-backups/`; nothing prunes before 2026-12-19.
- 10 dangling links kept as deliberate markers; 3 more not examined (Next Step 10).
- Deferred memory-dream ideas (generic `split` subcommand; rejected hook-older-than-body check).

**Accepted or informational (inherited, unchanged):**
- The Macmini is unreachable by ssh from MacStudio (do not retry). Its untracked `GEMINI.md`, `.gemini/`, `.grok/` are not carried by operator choice; never stage them.
- Two timing-based tests kept as fixed sleeps; Pyright `timeout=None` warning at `test_hmad_dispatch_exec_stamp.py:458`; opencode `$schema` change (`bd6a47ca`).
- Rust toolchain `stable-aarch64-apple-darwin`; foreign PID 32561.
- Items since 2026-11-08: `argument_not_printable` NBSP/U+202F/ZWJ refusal; two unpinned `_enc` print sites; `unreadable-file` first; `crash_visible=0/0` on host specs; scout row `hand-applied-single-mutants`.
- Local branch `fix/suite-timeout` is an ancestor of `main`; left in place.
- Scratch, safe to lose: the list in the superseded handoff, plus this session's scratchpad `/private/tmp/claude-501/-Users-kimhawk-orca-skills/618cbdc7-a9e7-4b46-aecc-39fe40ecaded/scratchpad` (OMX clone, builds, throwaway Codex homes). The superseded handoff also lists older dirs and 43 unreviewed scratch reports on another machine.

**Closed this session:** `reason-network/` left uncommitted by the Codex lane (committed `47e5f87b`); PR to OMX (withdrawn, fixed upstream).

## In-Flight Processes

| PID | Command | Log | Started | Elapsed @ handoff | ETA | What to check on exit |
|---|---|---|---|---|---|---|
| 27220 | `reason-network daemon` | `~/.reason/network/daemon.log` | 09:38 | 3h 17m | stays up | `reason-network doctor`; not a login service, so a reboot stops it |
| none found by `ps` | hook-trust watcher (session task, polls every 10 s) | session task output only | about 11:57 | about 1h | ends about 15:57 or with this session | prints `REASON_TRUSTED`; re-check trust by hand instead of relying on it |

## Context for Next Session

**Files touched this session:**
- `agent-messaging/SKILL.md`, `reason-network/SKILL.md` (pushed)
- `docs/handoffs/2026-11-24-main__agent-messaging-codex-hooks.md`, `docs/learnings.md`, `docs/skill-candidates.md`
- Outside the repo: both Codex `hooks.json` files; symlinks `~/.claude/skills/agent-messaging`, `~/.agents/skills/agent-messaging`; auto-memory; the private evidence directory

**Uncommitted changes:** the three untracked `phase5-gate-feature-scope` documents, which belong to lane A. Do not stage them.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect the three untracked documents
python3 -I /Users/kimhawk/orca/_worktree-backups/2026-11-24/agent-messaging-codex-hooks/trust.py "$CODEX_HOME"   # lane B: 5 "reason … trusted"?
shasum -a 256 docs/01-plan/features/phase5-gate-feature-scope.{spec,plan}.md   # lane A: 14c66d81…, b3cc9c0b…
```

**Related docs:** `docs/handoffs/2026-11-24-main__phase5-gate-plan-approved.md`; `agent-messaging/SKILL.md`; `reason-network/SKILL.md`; `h-mad/references/audit-prompt-assembly.md`.
