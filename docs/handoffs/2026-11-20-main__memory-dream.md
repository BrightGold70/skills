# Handoff — memory-dream: built, adopted, and run on the memory store

**Date:** 2026-11-20
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-18-main__omc-update-check.md
**Next-Session Focus:** Run the full suite on the uncommitted READ dream-age step and commit it.
**Suggested-Skills:** memory-dream (next judgment pass once last_dream is over 7 days)

## Session Summary

This session started as a resume on 2026-11-12 (OMC todo #4 checked: no release past 5.8.4) and wrote the 11-18 handoff. It then adopted the "dreaming" pattern from Anthropic's components-of-agent-memory research. It built the `memory-dream` skill (link linter with safe repair, judgment-pass procedure, hook checks, backup retention) and ran it on the auto-memory store. Six commits are pushed: `a39d1e91`, `9ad0df42`, `06fd2b8e`, `a6de600d`, `fdb0b262`, `fb071853`. Each followed a full suite run read from its log; the last one passed 9246. Store results:
- 24 Active entries → 11, 9 orphans → 0;
- links 897 → 1022 resolving (10 deliberate markers);
- 14 oversized notes split into hubs and linked files;
- `MEMORY.md` compacted to ~70%.

Side work: HemaSuite #162's CSA `./~` follow-up was verified closed by PR #175 (a comment was posted). The asset-legend AC-7 live run was handed over to HemaSuite, which took it over.

## Key Learnings

- **Calibrate a new check on real data before shipping it.** The hook-older-than-body date check gave 3 false positives out of 3 on the live store and was dropped. Every real stale hook found needed judgment, so it became a SKILL.md step. The citation checks found 0 on both real snapshots and are kept only as invariants.
- **A "full snapshot" must be link-closed, not "holds MEMORY.md".** Partial backups often hold the index an edit touched. The first prune version would have kept a 6-file backup and deleted the only 299-file one.
- **Concurrent lanes edit `MEMORY.md` and notes mid-operation.** The hash-before-write guard aborted correctly twice (index grew 17436 → 17579 B overnight, queue-note hook rewritten while I checked GitHub). Re-read before every write; never batch-read then batch-write.
- **Mutation runs found three test-design traps:** test order masking a writing lint (fixed by linting a fresh copy per test); a guard made redundant by another (bracket regex vs re-parse, so the re-parse was dropped); and a guard unreachable by the fixture (a symlink outside the root never reaches `is_symlink`).
- **A zsh glob with no match aborts the whole command**, so `ls a/* b/*` returning nothing is not absence. Use `find` and a positive control.
- **Only 4 of 88 Feedback rules are mechanically enforced** (labeller sweep, 2026-11-19). The rest live only in memory prose.

## Next Steps

1. **Commit the READ dream-age step.** It is uncommitted in the working tree: `handoff/references/read-mode.md` (Step 3 bullet "Memory dream age" + Step 5 `**Memory:**` line) and `handoff/tests/test_handoff_dream_lint_step.py` (+4 READ tests). Run `rtk proxy python3.11 -m pytest -q -p no:cacheprovider > <log> 2>&1; echo RUN_RC=$?` (≈50 min, read the summary from the log), then commit and push. Scoped: 38 passed; six positive controls caught (apply, wrong encoding, unprinted line, threshold drift, dropped report line, dropped allowlist exclusion).
2. **Queue-note hook nits, once the HemaSuite lane is quiet:** the hook cites `main 37efbefeb` (real: their 11-20 07:23 handoff commit) that the note body lacks, so `dream_lint` reports `hooks=1`. The index is at 17,579 B, 79 over the 17,500 target, after their hook rewrite. Add the sha to their status line and trim the hook by ~80 B.
3. **Before any OMC update:** `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/upstream.py`. Last read 2026-11-18: `EMITS` on 5.8.4, latest npm 5.8.4. Not re-checked since.
4. **On the Macmini**, after `git pull`: copy `docs/patches/patch-verify-on-update.sh` to `~/.claude/hooks/`; `python3 docs/patches/codex-duplicate-handoff/verify.py --fix`; `python3 docs/patches/omc-codex-mcp-no-type/apply.py` then `verify.py`. The memory-dream skill also needs `ln -s ~/orca/skills/memory-dream ~/.claude/skills/memory-dream` there.
5. **Retire the OMC patch** once `upstream.py` reads `FIXED` (README §Retiring).

## Open / Blocked Items

**From this session:**
- **READ dream-age step uncommitted** — status: done, awaiting full suite (Next Step 1). Scratch copy also at `/private/tmp/claude-501/readdream-175416/` (temporary; the repo working tree is the durable copy).
- **Memory-store edits are outside the repo** (`~/.claude/projects/-Users-kimhawk-orca-skills/memory/`). Every edit was backed up under `~/.claude/memory-dream-backups/` (19 timestamped dirs). The newest full snapshot is `20261119-105940-judgment`, which `prune_backups.py` protects. Nothing prunes until 2026-12-19.
- **`dream_lint` at closeout:** `links total=1032 RESOLVED=1022 DANGLING=10`, `orphans=0`, `hooks=1` (queue note, Next Step 2), `last_dream=1d ago`, `index OK bytes=17579 frac=70%`.
- **10 dangling links kept as deliberate markers** (review-comment-dedup, wsg_task15_shipped, exec_missing_report_recovery, task12_m3_anchor_migration, sapphire_g_revision, unified_subsystem_consolidation_audit, asset-legend-native-citations, synopsis_resource_consumption, f6_quality_checker, bmad) — status: accepted. Each was checked: no note exists under any name, and the history lives in repo docs or the link is conditional.
- **AC-7 live run (asset-legend-native-citations)** — handed over to HemaSuite. Brief `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-11-19-main__asset-legend-ac7-live-run.md`, `**Taken-Over-By:** HemaSuite · main · session f9973721 · 2026-11-20`. Not committed in HemaSuite yet (their lane owns that). No longer ours.
- **HemaSuite #178 test leak** (writes `evidence_presentations/<section>.json` into the HPW source tree; FAILDIFF reads `UNREADABLE`) — owned by the HemaSuite lane and recorded in their queue note. FYI only: no issue tracks it; the writer is an indirect caller.
- **Deferred memory-dream ideas:** a generic `split` subcommand (the split script was hand-written 7 times; filed in skill-candidates), and a hook-older-than-body check (rejected: 3/3 false positives).
- **Scratch dirs** under `/private/tmp/claude-501/` (`hookdev-*`, `prunedev-*`, `bkctl-*`, `dl-copy`, `readdream-*`, `readctl-*`, `hdl*`) — temporary, safe to lose.

**Carried from 2026-11-18 (omc-update-check):**
- **Next Step 1, run `upstream.py` before any OMC update:** unchanged (Next Step 3).
- **Next Step 2, Macmini catch-up:** unchanged (Next Step 4), plus the memory-dream symlink.
- **Next Step 3, retire the OMC patch:** still blocked on upstream (Next Step 5).
- **OMC MCP server `plugin:oh-my-claudecode:t` "Connection closed":** unchanged, not investigated; seen again at each session start.
- **OMC patch applied on MacStudio for 5.8.4** (4 runtime files, `*.pre-omc-codex-mcp-no-type` backups): unchanged since 11-18 (`VERIFY: OK files=4` then).
- **`upstream.py` checks the GitHub tag and npm, not the marketplace cache build:** unchanged, accepted.
- **Codex config edits outside the repo** (`[[skills.config]]` pins in `~/.codex/config.toml` and `$CODEX_HOME/config.toml`; Orca's `skills/handoff` copy deleted; backups in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/a571186a-8d52-49d8-a61e-ac4740e2ac73/scratchpad/backup/`): unchanged.
- **Orca copy may reappear if OMX setup re-runs; pins break on every Matt Pocock plugin update:** unchanged; DUPLICATE/STALE checks warn, `--fix` repoints.
- **Known limits of `codex-duplicate-handoff`** (flow-mapping `{name: handoff}`, scan depth, plain-file race, nested/BOM SKILL.md): unchanged, accepted.
- **OMC patch exists only on MacStudio; the Macmini is unreachable by ssh from MacStudio** (do not retry): unchanged.
- **Older scratch artifacts** (`991d87bb…`, `a571186a…`, `b68348df…`, `013414ea…`, `f7b82980…`, 43 unreviewed scratch reports on another machine): unchanged, temporary.
- **`~/.claude.json` context7/sequential-thinking entries; edits outside the repo from 2026-11-09 (0 `type` lines):** unchanged, expected.
- **Two timing-based tests kept as fixed sleeps; Pyright `timeout=None` warning at `test_hmad_dispatch_exec_stamp.py:458`; opencode `$schema` change (`bd6a47ca`):** unchanged, accepted/informational.
- **Hand-started Codex session still ungated; another hook in `.codex/hooks.json` withholds the bypass; two unanchored hook-trust plumbing lines; hard-link kinds differ by host (all DENY):** unchanged, accepted. The codex-gate memory entry was moved to the archive on 11-19 as settled.
- **Rust toolchain `stable-aarch64-apple-darwin`; foreign PID 32561:** unchanged, informational.
- **Accepted items unchanged since 2026-11-08** (`argument_not_printable` NBSP/U+202F/ZWJ refusal; two unpinned `_enc` print sites; `unreadable-file` first; `crash_visible=0/0` on host specs; scout row `hand-applied-single-mutants`): unchanged.
- **Items closed in predecessors** (scratch-dir deletion `6df9db7a…`, `899d9bdf`/`cd885d09`, Macmini sync #16, dispatch `NOT enforced` watch, heartbeat flake + mutation row, codex `ignoring 2 unrecognized configuration settings`): unchanged.
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over, owned by HemaSuite, unchanged.
- **Macmini untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.
- **Orca worktree comment:** this WRITE restamps it.

## Context for Next Session

**Files touched this session (committed):** `memory-dream/` (SKILL.md, `scripts/dream_lint.py`, `scripts/prune_backups.py`, tests, two mutation specs), `handoff/references/auto-memories.md`, `handoff/tests/test_handoff_dream_lint_step.py`, `pytest.ini`.
**Uncommitted:** `handoff/references/read-mode.md`, `handoff/tests/test_handoff_dream_lint_step.py` (READ dream-age step).
**Outside the repo:** the memory store and its backups (above); `~/.claude/skills/memory-dream` symlink; the HemaSuite AC-7 brief; a comment on HemaSuite #162 (`issuecomment-6997525212`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect the 2 READ-step files modified
python3 memory-dream/scripts/dream_lint.py ~/.claude/projects/-Users-kimhawk-orca-skills/memory
python3 memory-dream/scripts/prune_backups.py   # dry run; deletes nothing before 2026-12-19
```

**Related docs:** `memory-dream/SKILL.md`; Anthropic research "components of agent memory" and its dreaming cookbook (platform.claude.com/cookbook/managed-agents-cma-dreaming-with-a-dynamic-workflow); `docs/handoffs/2026-11-18-main__omc-update-check.md`.
