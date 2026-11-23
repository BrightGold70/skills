# Handoff — start /h-mad phase5-gate-feature-scope

**Date:** 2026-11-24
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-23-main__codex-skill-dups-gate-scope.md
**Next-Session Focus:** Run `/h-mad phase5-gate-feature-scope` from a fresh session on the clean tree (Next Step 1).
**Suggested-Skills:** h-mad (operator chose the full seven-phase route), verify-hmad-gates (drive every gate change end to end)

## Session Summary

The tree is clean and in sync with `origin/main`, so the gate-scope feature can start; it has no state record and the resume oracle reads `start_fresh`. Since the 2026-11-23 handoff was first written, the stray gate-policy edits were traced to the operator's own P14 codex session, the `--authors-test` rule was finished and pushed as `e506d871` (full suite 9326 passed, mutation 20/20, review must=0), and the P14-only gate exception was retired to a backup. One confirmed gate weakness that predates this work is still open (Next Step 2).

## Key Learnings

- **The arming defect is wider than first reported.** Read from source on 2026-11-24: the codex and agy gates both call `_any_phase5_status(root)`, which uses `root.rglob("docs/.bkit-memory.json")`. The per-file write judge is narrower on paths but not on features: `read_chain` (`h-mad/scripts/h_mad_tdd_judge.py:215`) walks only the target's ancestor directories, yet collects every record at `step5` in those state files (`_active_records`). The Claude gate goes through that judge.
- **`rglob` also reads state files that belong to nobody.** In this repo it finds 106 of them, nearly all copies inside the git-excluded `kimhawk@Hawui-Macmini.local/` audit roots. One such copy at `step5`, or one that will not parse, would arm or fail-close the gate here.
- **Attribute stray edits before calling them unknown.** `grep -rl <symbol> ~/.codex/sessions/<date>` found the authoring session, and its user messages showed what the operator had approved.
- **A deny test can pass because a different rule denies.** One new case was refused by the `/tmp` output rule rather than the rule it named; only the mutation run showed it.
- **A large decision diff is strong evidence for a policy change.** The reviewer compared about 2.2 million policy decisions between `HEAD` and the tree per interpreter; 10 differed, all intended.
- **This repository is public.** Keep a working bypass out of commits, handoffs and the skill-candidates file.

## Next Steps

1. **Run `/h-mad phase5-gate-feature-scope`.** Brief:
   - **Problem.** A session is shell-gated because some other feature in the same repository is at `step5`. Audit-phase commands are not in `SAFE_HMAD_SCRIPT_OPTIONS` or `SAFE_DISPATCH_VERBS`, and a gated agent may not write `.h-mad/phase5-shell-allow`, so a codex orchestrator lane hands the operator a `git apply` patch per audit cycle.
   - **Measured.** 2026-11-23, HemaSuite: `issue-187-file-root-move-refusal` at `step5` blocked the `csa-column-mapper-jev` plan audit; four patches in one day (`/private/tmp/p16-plan-*.patch`, `HemaSuite/.h-mad/phase5-shell-allow`, 18 exact-command lines).
   - **Premise re-checked 2026-11-24.** No HemaSuite feature is at `step5` now (#187 reads `phase: None`, `last_completed_phase: 5`), so the live symptom is gone and the defect in code is not. Reproduce it in a scratch repo with two features, one at `step5`, before specifying.
   - **Goal.** A session serving a feature that is not in Phase 5 is not shell-gated because a different feature is. A Phase-5 implementer must stay gated.
   - **Code.** `h-mad/scripts/h_mad_target_identity.py:322-344` (`_state_status`, `_any_phase5_status`), `h-mad/hooks/h-mad-codex-tdd-gate.py:310-362`, `h-mad/hooks/h-mad-agy-tdd-gate.py:120`, `h-mad/scripts/h_mad_tdd_judge.py:195-240`, `h-mad/hooks/h-mad-tdd-gate.sh`. Tests pinning arming: `test_h_mad_shared_gate_policy.py`, `test_h_mad_agy_tdd_gate.py`, `test_h_mad_agy_tdd_gate_differential.py`, `test_h_mad_target_identity.py`; spec `shared_gate_policy.json`.
   - **Design questions.** How the gate learns which feature a session serves (worktree, owner session id, a dispatch-time declaration) and why the gated agent cannot forge it; what a session with no declared feature gets; fail-closed behaviour when the mapping is missing or unreadable; whether the shell gate and the write judge should share one scoping rule; whether `rglob` should stop reading excluded and nested copies.
   - **Constraints.** `hmad-dispatch audit-cycle` runs an arbitrary `--suite-cmd`, so widening the safe list cannot cover it; the operator did not choose that route. The skill is symlinked live, so an uncommitted edit here is the running policy of every gate on this machine: work in a worktree.
2. **Fix the open Phase-5 policy finding** in the same file (`_option_value`, `_path_within`). Details, kept out of this public repo: `/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/open-gate-finding.md`. Recommended: land it as its own small change before the feature's Phase 5, or make it a requirement in the Phase 1 spec, so the two do not collide. The operator has not ruled.
3. **Re-pin or relaunch codex and agy before any dispatch.** `hmad-dispatch env` read `PREFLIGHT: FAIL stale=codex,agy` on 2026-11-24. Read each pane's tail before trusting a pin.
4. **Fold the memory-index trim into the next `/memory-dream`** (operator decision 2026-11-22; due about 2026-11-26). 2026-11-24: 18,658 B against the 17,500 target, `DANGLING=13` (10 are accepted markers, 3 are new and not examined), `hooks=1`, `last_dream=5d`.
5. **Before any OMC update:** `python3 docs/patches/omc-codex-mcp-no-type/upstream.py` (2026-11-22: `EMITS` on 5.8.4).
6. **After any OMC update:** in the new `~/.claude/plugins/cache/omc/oh-my-claudecode/<version>/` run `npm install --omit=dev --ignore-scripts`, then `npm rebuild better-sqlite3`. Never run `scripts/plugin-setup.mjs`.
7. **On the Macmini**, after `git pull`: copy `docs/patches/patch-verify-on-update.sh` to `~/.claude/hooks/`; `python3 docs/patches/codex-duplicate-handoff/verify.py --fix`; `python3 docs/patches/omc-codex-mcp-no-type/apply.py` then `verify.py`; `ln -s ~/orca/skills/memory-dream ~/.claude/skills/memory-dream`; probably the `npm install` from step 6 (not checked).
8. **Retire the OMC patch** once `upstream.py` reads `FIXED`.

## Open / Blocked Items

**Gate work:**
- **Phase-5 gate scope fix** — status: not started, unblocked (Next Step 1).
- **Open Phase-5 policy finding** — status: confirmed, not fixed, operator has not ruled (Next Step 2).
- **`--authors-test` rule (`e506d871`)** — status: pushed. The edits made after its last review were not re-reviewed. Accepted limits: a looped link resolves differently on Python 3.13+, and a project root spelled through an outside link is judged physically.
- **Retired P14 gate exception** — status: done. Backup `/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/` holds the five files, the diff, both review reports and the open finding.
- **HemaSuite P16 lane's allow lines** — status: live symptom gone while no HemaSuite feature is at `step5`; returns with the next one until Next Step 1 lands. Owned by that lane.

**Codex environment (outside the repo, unchanged since 2026-11-22):**
- **`~/.codex/AGENTS.md` Orca block, `gpt-6-luna` subagent defaults, `omx setup` on `~/.codex` and the Orca account home** — status: done, untested in a live codex turn. An OMX `PreToolUse` hook now runs in the codex pane h-mad dispatches to; no gate dispatch has been run with it, so check it in the feature's first dispatch. Backups: `~/.codex-backups/2026-11-22-pre-omx-setup/`, `~/.codex-backups/2026-11-22-pre-omx-setup-orca-home/`, `~/.codex/AGENTS.md.pre-orca-block-20261122`, `config.toml.pre-subagent-model-20261122` beside each config.
- **Orca may recreate the account home's `.omx` symlink** — open risk.
- **Duplicate codex skills (`ieumoffice`, stale `h-mad`) moved to backup** — done; IeumOffice may rewrite its copy, and the install check now reports it.
- **Duplicate-skill advisory limit** — accepted: pins matched by real path, codex's own rule unmeasured; last small edits not re-reviewed.
- **Codex `ai-memory` stdio bridge and serena timeout 180** — unchanged; a later `ai-memory setup` may write the bearer-token form back (open risk).
- **Codex `code_mode` warning; no ai-memory or serena tool called from inside codex; serena's slow start** — unchanged, not investigated.
- **Codex `[[skills.config]]` pins; Orca's `skills/handoff` copy deleted; pins break on every Matt Pocock plugin update; the copy may reappear on an OMX setup re-run** — unchanged.
- **Known limits of `codex-duplicate-handoff`** (flow-mapping name, scan depth, plain-file race, nested/BOM SKILL.md) — unchanged, accepted. `h_mad_install_check.py` is its second user.
- **Hand-started Codex session still ungated; another hook in `.codex/hooks.json` withholds the bypass; two unanchored hook-trust plumbing lines; hard-link kinds differ by host (all DENY)** — unchanged, accepted.

**OMC and Claude Code:**
- **OMC patch applied on MacStudio for 5.8.4; exists only there; `upstream.py` checks the tag and npm, not the marketplace build** — unchanged, accepted. **173 MB of `node_modules` in the 5.8.4 cache** lasts until the next update.
- **OMC `zod` advisory (GHSA-mrhx-c7xc-m3w5)** — examined 2026-11-20, not fixed, advisory text not read.
- **`.omc/notepad.md` trimmed; `.omc/notepad.md.bak-2026-11-22-pre-trim` is the only copy of the old entries** — done. OMC never prunes automatically.
- **Code mode blocks Remote Control on 2.1.330; setting stays `0`** — unchanged.
- **ai-memory calls resolve to `default/scratch`** — informational; pass `workspace=default`, `project=skills`.
- **`~/.claude.json` context7/sequential-thinking entries; edits outside the repo from 2026-11-09** — unchanged, expected.

**Memory store:**
- **Edits and backups under `~/.claude/memory-dream-backups/`; nothing prunes before 2026-12-19** — unchanged.
- **10 dangling links kept as deliberate markers** — unchanged; 3 further ones appeared (Next Step 4).
- **Deferred memory-dream ideas** (generic `split` subcommand; rejected hook-older-than-body check) — unchanged.

**Owned elsewhere:**
- **AC-7 live run (asset-legend-native-citations)** — handed over, HemaSuite session f9973721; not re-checked.
- **HemaSuite drafting quality without `CLAUDE.md`** — handed over, owned by HemaSuite, unchanged.

**Accepted or informational, unchanged:**
- The Macmini is unreachable by ssh from MacStudio (do not retry). Its untracked `GEMINI.md`, `.gemini/`, `.grok/` are not carried by operator choice; never stage them.
- Two timing-based tests kept as fixed sleeps; Pyright `timeout=None` warning at `test_hmad_dispatch_exec_stamp.py:458`; opencode `$schema` change (`bd6a47ca`).
- Rust toolchain `stable-aarch64-apple-darwin`; foreign PID 32561.
- Items since 2026-11-08: `argument_not_printable` NBSP/U+202F/ZWJ refusal; two unpinned `_enc` print sites; `unreadable-file` first; `crash_visible=0/0` on host specs; scout row `hand-applied-single-mutants`.
- Scratch, safe to lose: `/private/tmp/skilldup-r2.1KHJTb`, `/private/tmp/skilldup-r3.6QW6Y3`, `/private/tmp/h-mad-review.ezAjGl`, `/private/tmp/h-mad-rev2.DvFZsd`, older dirs under `/private/tmp/claude-501/` (`991d87bb…`, `a571186a…`, `b68348df…`, `013414ea…`, `f7b82980…`), 43 unreviewed scratch reports on another machine.

**Closed in the predecessor and not carried further:** OMC MCP connection, queue-note hook nits, stray gate edits, session `2fafec5c`, HemaSuite #178, the old pane-relaunch note, and the earlier closed list (scratch-dir deletion, Macmini sync #16, dispatch `NOT enforced` watch, heartbeat flake, codex `2 unrecognized configuration settings`).

## Context for Next Session

**Files touched since the 2026-11-23 handoff (committed in `e506d871`):**
- `h-mad/scripts/h_mad_target_identity.py`
- `h-mad/tests/test_h_mad_codex_runtime.py`
- `h-mad/tests/mutation-specs/gate_authoring_scope.json`

**Uncommitted changes:** none before this handoff's own files.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect clean, in sync with origin/main
hmad-dispatch env                  # re-pin or relaunch before any dispatch
# then: /h-mad phase5-gate-feature-scope
```

**Related docs:** `docs/handoffs/2026-11-23-main__codex-skill-dups-gate-scope.md`; `h-mad/references/codex-runtime.md`; `h-mad/references/agent-substrate.md`.
