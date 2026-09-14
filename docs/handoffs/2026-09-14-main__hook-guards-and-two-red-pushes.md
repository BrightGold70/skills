# Handoff — four guards shipped, two premises refuted, two commits pushed red

**Date:** 2026-09-14
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-14-main__memory-index-precheck.md

## Session Summary

A `/loop` drain of the nine todos the previous handoff restored. **Eight are closed**; the ninth
(`docs/skill-candidates.md`) is a standing backlog: **seven rows closed with evidence**, and this closeout's own scout appended **three** new ones, so the net is **54 → 50** open. Nine commits,
all pushed, full suite **3826 passed / 0 failed** at `15f8569`. Two of the todos turned out to rest
on **false premises** and were refuted with measurement rather than implemented. Two of my own
commits were **pushed red** and are the most useful thing in this document.

## Key Learnings

- **A targeted slice plus ALL_CAUGHT mutations does not cover doc-derived tests in OTHER files.**
  Twice: `2b8c52f` was red on `test_every_committed_spec_resolves_within_its_own_skill` (a guard in a
  third file asserting a property of the committed *spec set*), and `b9e9d2a` was red on 25 tests
  because 28 lines of prose landed inside a section whose extractor owns its `###` subsections,
  pushing it 151 → 177 past a runaway detector at 160. **Commit → run the bare `pytest` → then push.**
  Both were already on the remote before they were known. Cheap pre-check when a parsed document is
  touched: `grep -rln "<doc basename>" --include='*.py' */tests/`.
- **The slash-command argument expander is `\$ARGUMENTS\[\d+\]|\$ARGUMENTS|\$\d+(?!\w)`** — decoded
  from the 2.1.270 binary. It contains no `@` and no `*`; a census of the whole image found `\$\*`
  **zero** times and `\$@` five, all inside C#/F# highlighting grammars. It is also a **MODE SWITCH**:
  a body containing a match gets its argument spliced inline and **no** `ARGUMENTS:` trailer, and both
  `handoff` and `h-mad` route their mode off that trailer. The alternation is **asymmetric** —
  `$ARGUMENTSX` is rewritten, `$1abc` is not.
- **The memory index cannot reach its own compaction target by shortening hooks.** Hooks were
  **7093 bytes of 24947**; deleting every one still left 15657 bytes and **164 lines** — under the
  byte target, over the line target. The bulk is the link text (~80–100 B/entry), so ~200 entries
  cannot fit at one line each. The lever is a split, not terser prose.
- **A calibration pass is worth more than the rule it checks.** The `$@`/`$*` lint and the
  self-matching *refusal* were both asked for and both refuted by measurement — the latter would have
  refused **21 of 874** committed mutations, every one a legitimate caught insertion.
- **EPERM means ALIVE.** `os.kill(pid, 0)` raising `PermissionError` proves the process exists;
  folding it in with `ESRCH` steals a live holder's lock. Same defect already recorded for
  `is_pid_alive` (#40).
- **Cut a block you inserted on its OWN last line, never on a structural boundary.** The first repair
  of `b9e9d2a` bounded my 28-line block on "the next `## ` heading" and swept 45 lines of the
  section's tail out with it. The boundary is what I broke, so it was not safe to measure with.
- **An unreachable mutation scores as a clean battery.** My first `blob()` mutation targeted the
  missing-binary branch, which never runs where the binary exists — it SURVIVED. A later one was an
  **equivalent mutant** (`pid: None` already blocked via `isinstance`). Both retargeted rather than
  shipped, per this repo's own `a mutation that can never fire reads as a passing battery`.

## Next Steps

1. **Decide the `run_spec` sibling-precheck widening** — `h_mad_mutation_harness.py:844` sweeps
   `spec_path.parent.glob("*.json")` only, and this session put committed specs in **two** directories
   by splitting `skill_body_renderer_args.json`. Deferred deliberately: widening it changes which runs
   return `PRECHECK_FAILED`, which wants its own measurement. Row at `docs/skill-candidates.md` §"sweep
   EVERY mutation-spec directory".
2. **Keep draining the backlog** — `python3.11 handoff/scripts/skill_candidates_census.py --list-open
   docs/skill-candidates.md` now NAMES all 50 with file:line and verdict (new this session). The three
   newest are this closeout's own and have never been re-probed.
3. `[suggested]` **Prune two stale worktrees** when that lane is idle:
   `git worktree remove --force /private/tmp/claude-501/-Users-kimhawk-orca-skills/d4352d63-*/scratchpad/{cleanwt,invwt}`
   then `git worktree prune`. They belong to session `d4352d63`, not this one.
4. `[suggested]` **Settle the `#56` residue off-by-one** — needs only the rank of `T6 r10`; see
   `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` §"RESIDUE ACCOUNTING".

## Open / Blocked Items

**Carried from the predecessor — every item accounted for:**

- **Auto-memory index over its cap** — **CLOSED.** Split into `MEMORY.md` (16404 B / 121 lines, **66%
  of cap, `OK`**) and a new `MEMORY-ARCHIVE.md` (9450 B, not auto-loaded, uncapped, greppable).
  **209/209 links preserved**, proven by comparing the `](*.md)` set before against the union after in
  the same script that did the move. Operator chose the split over dropping hooks or retiring entries.
  `repo: n/a (user-global) · path: ~/.claude/projects/-Users-kimhawk-orca-skills/memory/`
- **`docs/skill-candidates.md` rows open** — status: **54 → 50 net** — seven closed with evidence
  (`grep the ENFORCEMENT`, `a positional shell arg…`, `a mutation that can never fire…`, `re-grep a
  decoded constant…`, `a tree lock around the mutation harness`, `detect that ANOTHER session…`,
  `sweep EVERY mutation-spec directory`), and THREE appended by this closeout's scout, which are
  unverified by construction — they were written today. Census: `candidates=231 OPEN=50 LANDED=97`,
  coverage 237/237. The closing figure is deliberately the NET: a "54 → 47" that ignored the rows the
  same document added would be the kind of count this repo keeps catching.
- **19 `#56` DIFFERENT calls never adjudicated** — **CLOSED as a decision, not as work.** §Closure
  already said *"Nothing else. The count and the shipped-six are settled and should not be re-derived
  again."* They were being carried on the word "unadjudicated" rather than on anything the document
  says. The floor of seventeen is a deliberate publication decision.
- **`T1 r8` (rank 99) corroborated but unadjudicated** — **CLOSED**, same decision.
- **Sibling worktree `wsg-backlog-two-items-owed-here`** — status: **the worktree is GONE** (absent
  from `git worktree list` and Orca `worktree-list`; no such branch). Its DOC survives at
  `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md`.
  Still **not this lane's and not handed over**. `repo: /Users/kimhawk/orca/HemaSuite · branch: main ·
  worktree: none (removed)`
- **The `#56` brief may still carry the borrowed "202"** — **SWEPT.** Re-derived against both
  HemaSuite checkouts (byte-identical, `sha 8e21804d2028`): 6651 lines, **202 matching LINES, 341
  occurrences, 96 distinct**. Three real instances; two fixed here, the third is the originating brief
  in **another repo with an owner** and is reported, not edited (`…wsg-backlog-two-items-owed-here.md:36`).
- **A concurrent session shares this working tree** — status: **RECURRED and now GUARDED.**
  `4915206` landed *during* a full-suite run. `MUTATION: TREE_MOVED` now refuses a verdict measured
  across a commit, and `tree_lock()` serialises runs. Suite deltas still need attributing by hand:
  3769 + 24 mine + 3 theirs = 3796.
- **The index guard is not wired into anything automatic** — **CLOSED.** `memory-index-guard.sh` at
  `SessionStart` + `PreToolUse`.

**Open, new this session:**

- **`run_spec`'s sibling precheck sweeps ONE directory** — status: open by decision, see Next Step 1.
- **`~/.claude/settings.json` was edited and is OUTSIDE this repo** — two hook entries added
  (`SessionStart`, `PreToolUse Write|Edit`) plus a symlink at `~/.claude/hooks/memory-index-guard.sh`.
  The backup is in this session's scratchpad and **will not survive cleanup**; to unwire, delete the
  two entries whose command contains `memory-index-guard` and the symlink. Nothing else depends on it.
- **88 untracked `.done` audit artifacts + `lanestate/`** — status: standing, not this session's.
  `lanestate/` is **stale**: `wsg.phase=4` at `4b3de566` while WSG Phase 5 is closed, and
  `gateway.phase=5` while `#18` is shipped and archived.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_mutation_harness.py` (self-matching diagnosis, `tree_lock`, `TREE_MOVED`)
- `h-mad/hooks/memory-index-guard.sh` (new), `h-mad/tests/claudebinary.py` (new)
- `h-mad/tests/test_skill_body_renderer_args.py`, `test_memory_index_guard.py` (new)
- `h-mad/tests/mutation-specs/{skill_body_renderer_args,memory_index_guard}.json` (new),
  `mutation_harness.json`; `handoff/tests/mutation-specs/{skill_body_renderer_args,census_registry}.json`
- `handoff/scripts/skill_candidates_census.py` (`--list-open`), `h-mad/SKILL.md`,
  `handoff/references/auto-memories.md`, `docs/skill-candidates.md`
- `~/.claude/projects/.../memory/{MEMORY.md,MEMORY-ARCHIVE.md,feedback_*}` — **not in any git repo**

**Uncommitted changes:** none. `lanestate/` and the `.done` files remain untracked, not this session's.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                   # expect 15f8569 or later, in sync
python3.11 h-mad/scripts/h_mad_check_memory_index.py    # expect OK, ~66% of cap
python3.11 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors \
    h-mad/tests/mutation-specs/*.json handoff/tests/mutation-specs/*.json   # expect 961/961
python3.11 -m pytest -q                             # ~9.5 min from the REPO ROOT
# python3 here is 3.14 with NO pytest — use python3.11.
# Do NOT write "expect N passed": this doc's own commit adds doc-derived tests.
#   Measured 3826 at 15f8569. ANOTHER SESSION COMMITS INTO THIS TREE — check
#   `git log` first and attribute any delta before believing a count is yours.
# COMMIT, then run the bare pytest, THEN push. Two commits went out red this
#   session because a green targeted slice was treated as a green suite.
```

**Related docs:**
- `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` §"RESIDUE ACCOUNTING" — the
  decision and the off-by-one
- `h-mad/tests/test_skill_body_renderer_args.py` — the decoded expander, the mode switch, the `$@` negative
- `h-mad/tests/test_memory_index_guard.py` — why the hook advises rather than blocks
- `handoff/references/auto-memories.md` — what compaction actually costs, measured
