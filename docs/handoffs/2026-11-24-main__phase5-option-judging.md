# Handoff — Phase-5 option-judging fix landed; gate scope next

**Date:** 2026-11-24
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-24-main__phase5-gate-feature-scope.md
**Next-Session Focus:** Run `/h-mad phase5-gate-feature-scope` (Next Step 1). The defect is live again in HemaSuite.
**Suggested-Skills:** h-mad (operator chose the full seven-phase route), verify-hmad-gates (drive every gate change end to end)

## Session Summary

The open Phase-5 policy finding is fixed, merged and pushed as `74ba0661`: the shell gate now judges every value of a repeated option and resolves a path from the directory the command runs in. Repo-root suite before the rebase: 9368 passed. On the combined tree: 782 targeted gate tests and all 3,240 mutation anchors. Two independent review passes; every must-fix closed. The fix's worktree and branch are removed. `/h-mad phase5-gate-feature-scope` has not been started.

## Key Learnings

- **A policy diff only checks the oracle it was given.** My old-versus-new comparison read "no new allows" while the first version had a regression: it assumed every relative value belongs to the command's directory, but the assembler only prints `--out`, `--log` and `--report-file` for a command run elsewhere. The reviewer found it by asking what uses the value.
- **A deny test can pass because an earlier rule denies.** The agy fixture root is named `repo Ω [*] 'q'`, which the lexical filter refuses, so a path built from it never reached the option rule. Two mutants survived until the bad value became a plain ASCII path.
- **Both hook gates fail closed on an exception**, so a hook-level "deny" does not prove the guard did it. Call the policy function directly to pin a guard.
- **`h-mad/tests` is not the repo suite.** 8674 of 9358 tests at the time; run pytest from the repo root.
- **The mutation harness edits the tree in place.** Review a frozen copy while it runs; after stopping it, compare the tree with that copy.
- **One state file can arm two checkouts.** HemaSuite's `issue-187-file-root-move-refusal/docs/.bkit-memory.json` is a symlink to the main checkout's file, so the `csa-column-mapper-jev` record arms both.

## Next Steps

1. **Run `/h-mad phase5-gate-feature-scope`** from a fresh session, in a worktree (the skill is symlinked live). Brief:
   - **Problem.** A session is shell-gated because some other feature in the same repository is at `step5`. Audit-phase commands are not safe-listed and a gated agent may not write `.h-mad/phase5-shell-allow`, so a codex orchestrator lane hands the operator a `git apply` patch per audit cycle (measured 2026-11-23, HemaSuite: four patches in one day, `/private/tmp/p16-plan-*.patch`).
   - **Live again, observed 2026-11-24 10:46.** `csa-column-mapper-jev` is at `step5` (owner `d26fd99c`, heartbeat 10:33 KST). `issue-187-file-root-move-refusal` is not (`phase: None`), yet its worktree is armed through the symlinked state file. Read it as evidence; reproduce in a scratch repo.
   - **Goal.** A session serving a feature that is not in Phase 5 is not shell-gated because a different feature is. A Phase-5 implementer must stay gated.
   - **Code (lines at `74ba0661`).** `h-mad/scripts/h_mad_target_identity.py:324` (`_state_status`), `:340` (`_any_phase5_status`, uses `root.rglob`); `h-mad/hooks/h-mad-codex-tdd-gate.py:310-362`; `h-mad/hooks/h-mad-agy-tdd-gate.py:120`; `h-mad/scripts/h_mad_tdd_judge.py:195-240`; `h-mad/hooks/h-mad-tdd-gate.sh`. Tests: `test_h_mad_shared_gate_policy.py`, `test_h_mad_agy_tdd_gate.py`, `test_h_mad_agy_tdd_gate_differential.py`, `test_h_mad_target_identity.py`; spec `shared_gate_policy.json`.
   - **Design questions.** How the gate learns which feature a session serves (worktree, owner session id, dispatch-time declaration) and why a gated agent cannot forge it; what a session with no declared feature gets; fail-closed behaviour when the mapping is missing or unreadable; whether the shell gate and the write judge share one scoping rule (the judge also collects every `step5` record in the governing files); whether `rglob` should stop reading excluded and nested copies (106 state files in this repo, nearly all under `kimhawk@Hawui-Macmini.local/`).
   - **Constraints.** `hmad-dispatch audit-cycle` runs an arbitrary `--suite-cmd`, so widening the safe list cannot cover it. Public repo: no working bypass in commits or docs.
2. **Rule on sub-project state writes (operator).** With a session at the HemaSuite root and workdir in a sub-project, a relative `h_mad_state_write.py docs/.bkit-memory.json` is now refused; `main` had judged the root's store while the script wrote the sub-project's. The absolute spelling was always refused. Left refused; can be a question in the Phase 1 spec.
3. **Decide the four private follow-ups (S4, S5, R2, R3).** `/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/open-gate-finding.md`; both review reports sit beside it. All pre-date the fix; none blocks Next Step 1.
4. **Re-pin or relaunch codex and agy before any dispatch.** `hmad-dispatch env` still reads `PREFLIGHT: FAIL stale=codex,agy`. Read each pane's tail before trusting a pin. Check the OMX `PreToolUse` hook in the first dispatch.
5. **Fold the memory-index trim into the next `/memory-dream`** (operator decision 2026-11-22; due about 2026-11-26). 2026-11-24: 18,686 B against the 17,500 target, `DANGLING=13` (10 accepted markers, 3 not examined), `hooks=1`, `orphans=0`, `last_dream=5d`.
6. **Before any OMC update:** `python3 docs/patches/omc-codex-mcp-no-type/upstream.py` (2026-11-22: `EMITS` on 5.8.4).
7. **After any OMC update:** in the new `~/.claude/plugins/cache/omc/oh-my-claudecode/<version>/` run `npm install --omit=dev --ignore-scripts`, then `npm rebuild better-sqlite3`. Never run `scripts/plugin-setup.mjs`.
8. **On the Macmini**, after `git pull`: copy `docs/patches/patch-verify-on-update.sh` to `~/.claude/hooks/`; `python3 docs/patches/codex-duplicate-handoff/verify.py --fix`; `python3 docs/patches/omc-codex-mcp-no-type/apply.py` then `verify.py`; `ln -s ~/orca/skills/memory-dream ~/.claude/skills/memory-dream`; probably the `npm install` from step 7 (not checked).
9. **Retire the OMC patch** once `upstream.py` reads `FIXED`.

## Open / Blocked Items

**Gate work:**
- **Phase-5 gate scope fix** — status: not started, unblocked (Next Step 1).
- **Option-judging fix (`74ba0661`)** — status: done, live. Two limits: the full suite ran before the rebase onto two skill-only commits, and the last test-only edit was not re-reviewed (the mutation spec reads 32/32 with it).
- **Policy follow-ups S4, S5, R2, R3** — status: open, pre-existing (Next Step 3). **Sub-project state writes** — status: operator ruling (Next Step 2).
- **`--authors-test` rule (`e506d871`)** — unchanged: the edits after its last review were not re-reviewed. Accepted limits: a looped link resolves differently on Python 3.13+, and a project root spelled through an outside link is judged physically.
- **Retired P14 gate exception** — done, unchanged; backup in the directory named in Next Step 3.
- **HemaSuite P16 lane's allow lines** — status: the symptom is live while `csa-column-mapper-jev` is at `step5`, until Next Step 1 lands. Owned by that lane.

**Owned elsewhere:**
- **`csa-column-mapper-jev` (P16)** — repo: `/Users/kimhawk/orca/HemaSuite` · branch: `main` · worktree: none. Reviewed read-only at the operator's request; not owned here. At 09:34 it had a recorded halt for dirty plan v3 and design v2 audits. The lane has since committed audit resolutions (`7b03d2258`, `558f7bb36`) and entered `step5`. At 10:46 `h_mad_do_preconditions.py` still read `FAIL issues=2` on the same two reports, because it scores reports and not documents; whether the lane's capped resolution covers that is its call. Two risks reported to the operator: that checkout was 346 behind `origin/main` (15 ahead now), and at 09:30 the spec and audit reports were untracked.
- **AC-7 live run (asset-legend-native-citations)** — handed over, HemaSuite session f9973721; not re-checked.
- **HemaSuite drafting quality without `CLAUDE.md`** — handed over, owned by HemaSuite, unchanged.

**Codex environment (outside the repo, unchanged since 2026-11-22):**
- **`~/.codex/AGENTS.md` Orca block, `gpt-6-luna` subagent defaults, `omx setup` on `~/.codex` and the Orca account home** — done, untested in a live codex turn; no gate dispatch has run with the OMX `PreToolUse` hook (Next Step 4). Backups: `~/.codex-backups/2026-11-22-pre-omx-setup/`, `~/.codex-backups/2026-11-22-pre-omx-setup-orca-home/`, `~/.codex/AGENTS.md.pre-orca-block-20261122`, `config.toml.pre-subagent-model-20261122` beside each config.
- **Orca may recreate the account home's `.omx` symlink** — open risk.
- **Duplicate codex skills (`ieumoffice`, stale `h-mad`) moved to backup** — done; IeumOffice may rewrite its copy, and the install check reports it.
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
- **10 dangling links kept as deliberate markers** — unchanged; 3 further ones not examined (Next Step 5).
- **Deferred memory-dream ideas** (generic `split` subcommand; rejected hook-older-than-body check) — unchanged.

**Accepted or informational, unchanged:**
- The Macmini is unreachable by ssh from MacStudio (do not retry). Its untracked `GEMINI.md`, `.gemini/`, `.grok/` are not carried by operator choice; never stage them.
- Two timing-based tests kept as fixed sleeps; Pyright `timeout=None` warning at `test_hmad_dispatch_exec_stamp.py:458`; opencode `$schema` change (`bd6a47ca`).
- Rust toolchain `stable-aarch64-apple-darwin`; foreign PID 32561.
- Items since 2026-11-08: `argument_not_printable` NBSP/U+202F/ZWJ refusal; two unpinned `_enc` print sites; `unreadable-file` first; `crash_visible=0/0` on host specs; scout row `hand-applied-single-mutants`.
- Local branch `fix/suite-timeout` is an ancestor of `main`; left in place.
- Scratch, safe to lose: this session's scratchpad `/private/tmp/claude-501/-Users-kimhawk-orca-skills/ccc6bb42-1db1-4236-9f9e-a100514d63b9/scratchpad` (includes `revopt.hjR5kO`, `snap2`), `/var/tmp/opt-_e5ie3l3`, `/var/tmp/opt-r7r__huv`, `/var/tmp/tmp9pf7vt56`, `/private/var/tmp/gdwc_ti4z3`. Five further `/var/tmp/opt-*` directories exist whose origin was not checked. Older: `/private/tmp/skilldup-r2.1KHJTb`, `/private/tmp/skilldup-r3.6QW6Y3`, `/private/tmp/h-mad-review.ezAjGl`, `/private/tmp/h-mad-rev2.DvFZsd`, dirs under `/private/tmp/claude-501/` (`991d87bb…`, `a571186a…`, `b68348df…`, `013414ea…`, `f7b82980…`), 43 unreviewed scratch reports on another machine.

**Closed this session:** the open Phase-5 policy finding (predecessor Next Step 2), fixed in `74ba0661`.

## Context for Next Session

**Files touched this session (committed in `74ba0661`):**
- `h-mad/scripts/h_mad_target_identity.py`
- `h-mad/hooks/h-mad-codex-tdd-gate.py`
- `h-mad/tests/test_h_mad_codex_runtime.py`, `test_h_mad_agy_tdd_gate.py`, `test_h_mad_shared_gate_policy.py`
- `h-mad/tests/mutation-specs/gate_option_judging.json` (new), `assemble_tdd_mutation_rows.json`, `codex_gate_judge_wiring.json`, `shared_gate_policy.json`

Outside the repo: `open-gate-finding.md` and two review reports in the private backup directory (Next Step 3).

**Uncommitted changes:** none before this handoff's own files.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect clean, in sync with origin/main
hmad-dispatch env                  # re-pin or relaunch before any dispatch
# then: /h-mad phase5-gate-feature-scope
```

**Related docs:** `docs/handoffs/2026-11-24-main__phase5-gate-feature-scope.md`; `h-mad/references/codex-runtime.md`; `h-mad/references/agent-substrate.md`.
