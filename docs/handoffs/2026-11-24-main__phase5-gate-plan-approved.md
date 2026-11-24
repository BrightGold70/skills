# Handoff — phase5-gate-feature-scope: plan approved, audits next

**Date:** 2026-11-24
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-24-main__phase5-option-judging.md
**Next-Session Focus:** `/h-mad phase5-gate-feature-scope` resumes at Phase 3, plan audit cycle 1.
**Suggested-Skills:** h-mad (resume the feature), verify-hmad-gates (drive every gate change end to end)

## Session Summary

`/h-mad phase5-gate-feature-scope` ran Phases 1 and 2 and the plan-authoring half of Phase 3. The brainstorm (v1.3), spec (v1.2, 88 ACs) and plan (v1.1) are approved by the operator and verified by hash; the plan audit has not started and no gate code has changed. The three documents are untracked in the main checkout, with a copy in the private backup directory. The claim is released; the record reads `phase: null`, `current_phase: 3`, `last_completed_phase: 2`, and the oracle answers `resume_manual`.

## Key Learnings

- **Checkout scoping needs the field at 5a, not 5c.** The gate arms at 5a, and a record without the field must arm everywhere, so a field written at 5c would leave a sibling checkout armed through 5b.
- **Protecting a gate's inputs needs an exit designed with it.** A codex or agy owner id is a random UUID in the git directory that no hook payload carries, so identity cannot decide it. The approved exit is an ungated session.
- **A state write through a symlinked `docs/.bkit-memory.json` replaces the link with a copy.** Reproduced in scratch. The checkouts then disagree with no error. The spec fixes it (AC-1.7); until then write to the real file.
- **A feature's own orchestrator hits the gate too.** At 12:09 the P16 record carried `halt_reason: step5c:isolated_worktree_command_blocked_by_shell_allowlist`. Arming the shell from 5d (FR-9) is meant to cover this.
- **"Set" is not "effective" for a git environment variable.** Whether one moves `rev-parse --show-toplevel` depends on the variable and the spelling, so a test must assert that its value moved the answer.
- **An author's "no tests pin this" needs a positive control.** The plan's census instrumented the gates, ran 72 test files, and proved each detector fires in a second clone.

## Next Steps

1. **Run `/h-mad phase5-gate-feature-scope`** in a fresh session. Claim the feature, then:
   - Read `h-mad/references/audit-prompt-assembly.md`, and the opening part and dispatch-channels section of `references/phase5-substeps.md`.
   - Decide the four items under "Spec items owed" below. Route them to `spec-author` (v1.3), then `plan-author` if the plan's text moves.
   - Precheck, then the first gating cycle: `hmad-dispatch audit-cycle --feature phase5-gate-feature-scope --phase plan --cycle 1 --project-root /Users/kimhawk/orca/skills --passes 3 --surfaces codex,agy,grok`, with the suite flags SKILL.md requires. Documents are capped at two gating rounds.
   - This feature's own record is armed and cleared only by the installed writer; never point a worktree's newer writer at a live store.
2. **Settle the documents' home.** Brainstorm, spec and plan are untracked in a shared checkout; 5c commits them. Commit earlier only if the operator asks. Public repository: they were written to name no present weakness, and the author reports must not be committed.
3. **Probe codex again before dispatch.** The pinned pane `term_39f30d1a` was restarted (Codex 0.172.0, new process) after the 10:55 probe; `hmad-dispatch env` reads `PREFLIGHT: PASS` but prints no identity line for codex. Read its tail, then `hmad-dispatch probe codex`. agy (`term_5b5cf986`) answered at 10:55. Check the OMX `PreToolUse` hook in the first codex dispatch; the pane shows two warnings nobody has opened.
4. **Decide the private follow-ups** S4, S5, R2, R3 and T1: `/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/open-gate-finding.md`. Which parts of T1 the feature covers is stated there and in the private author reports.
5. **Fold the memory-index trim into the next `/memory-dream`** (operator decision 2026-11-22; due about 2026-11-26). 2026-11-24: 18,743 B against the 17,500 target, `DANGLING=13` (10 accepted markers, 3 not examined), `orphans=0`, `last_dream=5d`.
6. **Before any OMC update:** `python3 docs/patches/omc-codex-mcp-no-type/upstream.py` (2026-11-22: `EMITS` on 5.8.4).
7. **After any OMC update:** in the new `~/.claude/plugins/cache/omc/oh-my-claudecode/<version>/` run `npm install --omit=dev --ignore-scripts`, then `npm rebuild better-sqlite3`. Never run `scripts/plugin-setup.mjs`.
8. **On the Macmini**, after `git pull`: copy `docs/patches/patch-verify-on-update.sh` to `~/.claude/hooks/`; `python3 docs/patches/codex-duplicate-handoff/verify.py --fix`; `python3 docs/patches/omc-codex-mcp-no-type/apply.py` then `verify.py`; `ln -s ~/orca/skills/memory-dream ~/.claude/skills/memory-dream`; probably the `npm install` from step 7 (not checked).
9. **Retire the OMC patch** once `upstream.py` reads `FIXED`.

## Open / Blocked Items

**phase5-gate-feature-scope** (repo: `/Users/kimhawk/orca/skills` · branch: main · worktree: none yet, the plan requires one before 5a):
- **Documents** — `docs/01-plan/features/phase5-gate-feature-scope-brainstorm.md` (v1.3), `.spec.md` (v1.2, sha256 `14c66d81…`), `.plan.md` (v1.1, sha256 `b3cc9c0b…`). Author reports and copies: `/Users/kimhawk/orca/_worktree-backups/2026-11-24/phase5-gate-feature-scope/` (private).
- **Operator rulings** — scope by checkout; protect the arming fields; root and sub-project state files only; one rule for every gate; shell gate from 5d; an ungated session performs the exit; moved-checkout residual accepted; git environment variables ignored in the codex and agy root lookups (D7); FR-6 covers the session's and the target's own checkout; listed Pythons, and Linux simulated and reported as such; a landing report before landing. All are in the documents.
- **Orchestrator rulings the operator may reverse** — spec elaborations a to i accepted; AC-2.8's fixture avoids git rather than changing the judge's environment.
- **Spec items owed** (wording in `author_phase5-gate-feature-scope_plan_v2.report.md`) — status: not decided. (1) The AC-2.8 residual sentence. (2) AC-2.8: a value that changes what git answers. (3) NFR: the 2 s bound covers git calls this feature adds. (4) Assumptions: record the v1.2 approval. Also one design question: FR-6 in the Claude hook for an off-chain sub-project's linked state file whose real file has another name; pay for discovery or take a residual. The plan's old/new file mixture corpus was narrowed by its author; reverting it is described in the report.
- **Landing** — blocked on the feature. Before it: run the landing report and show it to the operator. A codex or agy orchestrator at `step5` then needs an ungated exit.

**Gate work, earlier:**
- **Option-judging fix (`74ba0661`)** — done, live, unchanged. The full suite ran before the rebase onto two skill-only commits, and the last test-only edit was not re-reviewed (mutation 32/32 with it).
- **Sub-project relative state writes** — status: refused today; the operator has not ruled separately. FR-2 and FR-5 change the surrounding rules, so re-ask after the feature.
- **`--authors-test` rule (`e506d871`)** — unchanged: the edits after its last review were not re-reviewed. Accepted limits: a looped link resolves differently on Python 3.13+, and a project root spelled through an outside link is judged physically.
- **Retired P14 gate exception** — done, unchanged; backup in the directory of Next Step 4.

**Owned elsewhere:**
- **`csa-column-mapper-jev` (P16)** — repo: `/Users/kimhawk/orca/HemaSuite` · branch: `main` · worktree: none. Owned by session `d26fd99c` (heartbeat 11:53 KST). At 12:09: `step5`, marker `step5c_worktree_creation_retry`, halt as quoted in Key Learnings. The operator's allow lines in `HemaSuite/.h-mad/phase5-shell-allow` are that lane's route until this feature lands. Its recorded risk of being 346 commits behind `origin/main` was not re-checked.
- **HemaSuite #187 worktree** — repo: `/Users/kimhawk/orca/HemaSuite` · branch: `feature/187-file-root-move-refusal` · worktree: `/Users/kimhawk/orca/workspaces/HemaSuite/issue-187-file-root-move-refusal`. Armed by the P16 record through its symlinked state file; the link was intact at 12:09. That lane should write state to `/Users/kimhawk/orca/HemaSuite/docs/.bkit-memory.json`, not through the link. Operator told; the lane was not messaged.
- **AC-7 live run (asset-legend-native-citations)** — handed over, HemaSuite session f9973721; not re-checked.
- **HemaSuite drafting quality without `CLAUDE.md`** — handed over, owned by HemaSuite, unchanged.

**Codex environment (outside the repo, unchanged since 2026-11-22):**
- **`~/.codex/AGENTS.md` Orca block, `gpt-6-luna` subagent defaults, `omx setup` on `~/.codex` and the Orca account home** — done, untested in a live codex turn; no gate dispatch has run with the OMX `PreToolUse` hook (Next Step 3). Backups: `~/.codex-backups/2026-11-22-pre-omx-setup/`, `~/.codex-backups/2026-11-22-pre-omx-setup-orca-home/`, `~/.codex/AGENTS.md.pre-orca-block-20261122`, `config.toml.pre-subagent-model-20261122` beside each config.
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
- Scratch, safe to lose: `/var/tmp/arm*` and `/var/tmp/symw.*` (18 directories), `planv11` in this session's scratchpad, `/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T/tmp.lkm6V6tJyr`. Also from the earlier handoff: this session's scratchpad `/private/tmp/claude-501/-Users-kimhawk-orca-skills/ccc6bb42-1db1-4236-9f9e-a100514d63b9/scratchpad` (includes `revopt.hjR5kO`, `snap2`), `/var/tmp/opt-_e5ie3l3`, `/var/tmp/opt-r7r__huv`, `/var/tmp/tmp9pf7vt56`, `/private/var/tmp/gdwc_ti4z3`. Five further `/var/tmp/opt-*` directories exist whose origin was not checked. Older: `/private/tmp/skilldup-r2.1KHJTb`, `/private/tmp/skilldup-r3.6QW6Y3`, `/private/tmp/h-mad-review.ezAjGl`, `/private/tmp/h-mad-rev2.DvFZsd`, dirs under `/private/tmp/claude-501/` (`991d87bb…`, `a571186a…`, `b68348df…`, `013414ea…`, `f7b82980…`), 43 unreviewed scratch reports on another machine.

**Closed this session:** re-pinning codex and agy (both pinned and probed 10:55; see Next Step 3 for what moved since).

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/phase5-gate-feature-scope-brainstorm.md`, `.spec.md`, `.plan.md` (untracked)
- `docs/.bkit-memory.json` (git-ignored): the feature's record
- Outside the repository: the two private directories named above; `.h-mad/orca-pins.env` pins

**Uncommitted changes:** the three untracked feature documents.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect the three untracked documents, in sync with origin/main
shasum -a 256 docs/01-plan/features/phase5-gate-feature-scope.{spec,plan}.md   # 14c66d81…, b3cc9c0b…
# then: /h-mad phase5-gate-feature-scope
```

**Related docs:** `docs/handoffs/2026-11-24-main__phase5-option-judging.md`; `h-mad/references/audit-prompt-assembly.md`; `h-mad/references/teammate-authors.md`.
