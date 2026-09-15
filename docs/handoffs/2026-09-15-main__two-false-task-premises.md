# Handoff — five backlog items closed, two of them by refuting their own premise

**Date:** 2026-09-15
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-14-main__hook-guards-and-two-red-pushes.md

## Session Summary

A resume plus a drain of five of the seven todos the predecessor left. **Five closed** (#25, #26,
#27, #28, #30), three commits, all pushed after a full green suite each time — **3826 passed / 0
failed** at each of `1313751`, `eba6d80`, `632ecde`. Two of the five turned out to rest on **false
premises stated in the task itself** and were settled by refuting them rather than doing the work
asked for. The working tree is now **completely clean** — `git status --porcelain` returns 0 lines
for the first time in seven handoffs. Two items remain open: the `docs/skill-candidates.md` backlog
(51) and one HemaSuite-owned row.

## Key Learnings

- **A task's own "what would settle this" is a claim, not a spec — re-derive the discriminator
  before fetching the datum it names.** `#56`'s RESIDUE ACCOUNTING ended *"Settling it needs the
  rank of `T6 r10` and nothing else."* The rank enters the in-band arithmetic **twice with opposite
  sign**: moving `T6 r10` past rank 70 removes one row from the in-band new calls AND one from the
  in-band adjudicated set, so 19−8 = 18−7 = **11** either way. The document's own option (a) was
  arithmetically unreachable. The real defect was `T1 r8` counted twice — named separately in the
  same sentence that said *"12 further"*, where `21 − 9 = 12` already included it.
- **"Widen this narrow sweep" can be a spec reversal wearing a bug's clothes.** `run_spec`'s
  single-directory sibling precheck is **AC-3.5** of `anchor-precheck-phase-5e-wiring`, pinned by
  `test_drifted_spec_in_a_different_directory_does_not_affect_run`, and the design calls
  sibling-only *"the single decision that shapes everything else"*. Two tasks in a row therefore had
  false premises; in both cases re-deriving the question was the entire win.
- **A gate you are about to lean on must be shown to discriminate, not just to be green.**
  `test_committed_mutation_harness_anchor_sweep_is_ok` is the tree-wide anchor gate. Proving that
  meant drifting `combine-rc-guard-drop` in `h-mad/tests/specs/` — RED — and restoring it
  byte-identical — GREEN. Without that, "it sweeps everything" is indistinguishable from "it sweeps
  an empty set".
- **`test_committed_mutation_specs_are_not_drifted` is NOT the tree-wide guard**, and looked like
  the gap for half an hour. It goes through `_own_committed_mutation_specs(project_root)`, a
  per-skill `tests/mutation-specs/` glob. The tree-wide one is `_committed_mutation_specs()` (`git
  ls-files` + classifier), used by AC-4.5's sweep and the two portability tests. Adjacent helpers,
  nearly identical names, opposite scopes.
- **The audit-cycle bespoke anchor test covers 2 of 7 gating mutations, not 7.**
  `test_audit_cycle_gating_spec_covers_shell_guards_with_landed_anchors` filters to the two shell
  guards; the other five (`combine-*-guard-drop`, all in `scripts/h_mad_audit_cycle.py`) are covered
  only by the tree-wide sweep above. Harmless today, but a count taken from that test would be wrong.
- **A 22-hour orphan can sit on a dev machine with nothing to surface it.** PID 97466, **PPID 1**,
  `hmad-dispatch.sh exec-pane agy`, 0.0% CPU, `sleep 1` children, its prompt and `--cd` both naming
  a **pytest tmpdir that no longer existed**. A test run leaked a wrapper that outlived its session,
  its target directory, and the tmpdir GC. Found only because #30 asked whether a worktree was safe
  to remove.
- **`pgrep` matched it and `rtk` swallowed the argv.** `pgrep -af d4352d63` printed two bare PIDs
  with the command lines stripped; the finding only appeared after a separate `ps -o command=`.
  A bare-PID `pgrep` result is not "nothing interesting" — read the argv on a second surface.
- **The candidates census reads a row's CONTINUATION lines for its verdict, so prose quoting
  `candidate:` + a verdict word scores as that row's verdict.** This closeout's own scout block hit
  it: a paragraph saying *"the remaining 27 open `candidate: yes` rows were not reconciled"* sat
  under a bulleted note, and the census scored that note as an open `yes` row —
  `candidates=234 OPEN=52 yes=30` against the true `233 / 51 / 29`. The file's fallback-grep comment
  already warns that prose quoting the phrase matches; the row-scoped reader inherits the same
  hazard one level up. Caught only because the delta was +2 rows for 1 row added. Fixed by
  de-bulleting the note and writing "open `yes` rows".
- **My own ad-hoc counts were wrong twice, and the tool's were right both times.** `grep -c "^
  orca/skills:"` over the census's `--list-open` returned **6** against the census's own **50** — it
  counted the bump-rows block. A first orphan-marker probe reported one report ABSENT because it
  looked in `docs/01-plan/features/` when `doc-block-exec`'s markers live in
  `docs/archive/2026-09/doc-block-exec/`. Both self-corrected only because the number looked wrong.

## Next Steps

1. **Keep draining the backlog** — `python3.11 handoff/scripts/skill_candidates_census.py
   --list-open docs/skill-candidates.md` names all **51** with file:line and verdict. The newest is
   this session's own scout row and has never been re-probed. **Read the count off the census
   summary line, never off a grep** (see Key Learnings).
2. **Close the `exec-pane` wrapper leak at its source** — a conftest session-finalizer that reaps
   wrappers rooted in the run's own `tmp_path`. Row at `docs/skill-candidates.md` §"reap LEAKED
   `exec-pane` wrapper processes". It is explicitly **not** a `live-e2e-pane-janitor` recurrence:
   that landed as `h_mad_pane_janitor.py`, which identifies panes positively via `worker-list`, and
   a local bash wrapper has no worker row for it to find.
3. `[suggested]` **Tell HemaSuite that its brief's Next Step 1 is already answered here** — a
   one-line pointer into
   `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md`
   naming `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md`. See the Open Item.

## Open / Blocked Items

**Carried from the predecessor — every item accounted for:**

- **`docs/skill-candidates.md` rows open** — status: **50 → 51**, unchanged in kind. No row was
  drained; the +1 is this session's own `exec-pane` wrapper-leak row, unverified by construction
  because it was written today. This closeout's scout then **reconciled three rows against source
  and flipped none** — `2180` (name the tests that PARSE a document) and `1429` (a measured value
  carries its commit) are both still open with a fresh instance each, and the 2026-09-02 preamble's
  stated reason for the frozen-tree guard is stale (`memory-index-guard.sh` IS a `PreToolUse` hook
  now). It also filed one `candidate: no`. **The other 27 open `yes` rows were not reconciled** and
  the scout block says so in the file. Census after the scout:
  `candidates=233 OPEN(yes+maybe)=51 yes=29 maybe=22 LANDED=97 DECLINED=37 no=38 SUPERSEDED=9`,
  coverage 239/239, `unqualified=0`.
- **Sibling brief `wsg-backlog-two-items-owed-here`** — status: **the predecessor's framing was
  WRONG and is corrected here.** It said *"not this lane's and not handed over"*. The doc carries
  **both** markers: `**Handover-From:** skills · main · session d4352d63` and `**Taken-Over-By:**
  HemaSuite · main · session efbc446c-ae09-4611-a3f5-52e3c7628d41 · 2026-09-14`. It **was** handed
  over and it **was** adopted, so it is owned and there is nothing to route from here — which is why
  no HANDOVER ran. What is genuinely owed is one-directional information: its **Next Step 1**
  ("re-derive `#56`'s enumeration once, against the spec") has since been answered *in this repo* by
  `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md`, and its owner has no way to
  know that. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none (removed)` ·
  `brief: docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md`. Its second item (two
  divergent `.h-mad/wires.jsonl` registries) is a HemaSuite data question and stays theirs.
- **A concurrent session shares this working tree** — status: **unchanged since 2026-09-14, guard
  still in place.** `MUTATION: TREE_MOVED` refuses a verdict measured across a commit and
  `tree_lock()` serialises runs. No recurrence this session: `git log` was checked before and after
  each of the three full-suite runs and did not move, so all three 3826 counts are attributable.
- **`run_spec`'s sibling precheck sweeps ONE directory** — **CLOSED by decision, `1313751`.** Do not
  widen: AC-3.5 pins it, the hazard is closed tree-wide twice (pre-push `git ls-files`; the
  suite's AC-4.5 sweep, proven discriminating by mutation), and `--check-anchors` over all three
  directories is `ANCHORS_OK 980/980` so widening changes **zero** verdicts. The residue is recorded
  at `_sibling_specs`'s docstring and on the row that deferred it.
- **`~/.claude/settings.json` was edited and is OUTSIDE this repo** — **CLOSED, `632ecde`.**
  `h-mad/SKILL.md` §`hooks/memory-index-guard.sh` now names both places (the two settings entries,
  the `~/.claude/hooks/` symlink), gives a locator that finds them **by value not index**, and says
  how to unwire and how to reinstall. The locator was executed verbatim before being documented.
- **88 untracked `.done` artifacts + `lanestate/`** — **CLOSED, `632ecde`.** Both gitignored on the
  operator's call, on measured evidence: all 88 markers have a **tracked** report and **0** are
  orphans, and `lanestate/` has no reader or writer anywhere in this repo. J36's comment in
  `hmad-dispatch.sh`, which hardcoded *"this repo carries 88"*, was reworded — that is a property of
  one tree at one moment, and gitignoring made it wrong immediately.
- **Two stale worktrees under session `d4352d63`** — **CLOSED, removed.** Both clean and detached at
  `404377d`, an ancestor of HEAD, so nothing was lost. `git worktree list` is now the main tree alone.
- **Auto-memory index over its cap** · **19 `#56` DIFFERENT calls** · **`T1 r8`** · **the borrowed
  "202"** · **the index guard's automatic trigger** — all **CLOSED by the predecessor**, re-checked
  here only for carry-forward completeness; nothing reopened.

**Open, new this session:**

- **`#56`'s published residue figure is corrected but the source document's own trichotomy is still
  wrong** — status: deliberate. `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md`
  §"SETTLED 2026-09-14" states that option (a) is arithmetically unreachable, but §RESIDUE
  ACCOUNTING above it still offers all three options as live. Left as written on the document's own
  convention — *"recorded rather than quietly corrected"*, *"left as written rather than rewritten"* —
  with an inline pointer at the "12" so a reader lands on the correction. Not a defect to fix; a
  convention to know about before re-reading that section.
- **`T6 r10`'s rank was never derived and deliberately will not be** — status: closed as
  not-load-bearing. The token-overlap screen's scoring formula is recorded nowhere in the document
  or either repo, so reproducing it would be a different instrument on a corpus that document twice
  warns against reading a third time, for a number that changes nothing.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_mutation_harness.py` (`_sibling_specs` docstring — the widening decision)
- `h-mad/scripts/hmad-dispatch.sh` (J36 comment — dropped the hardcoded 88)
- `h-mad/SKILL.md` (§`hooks/memory-index-guard.sh` — the unwire path and the by-value locator)
- `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` (§"SETTLED 2026-09-14")
- `docs/skill-candidates.md` (the `exec-pane` wrapper-leak row), `docs/learnings.md`, `.gitignore`

**Uncommitted changes:** none. `git status --porcelain` returns **0 lines** — no untracked entries
either, for the first time in seven handoffs.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                   # expect 632ecde or later, in sync
python3.11 h-mad/scripts/h_mad_check_memory_index.py    # expect OK
python3.11 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors \
    h-mad/tests/mutation-specs/*.json handoff/tests/mutation-specs/*.json \
    h-mad/tests/specs/*.json                        # expect 980/980 across ALL THREE dirs
python3.11 -m pytest -q                             # ~10 min from the REPO ROOT
# python3 here is 3.14 with NO pytest — use python3.11.
# Do NOT write "expect N passed" as a pin: doc-derived tests move it. Measured 3826 at 632ecde.
# ANOTHER SESSION COMMITS INTO THIS TREE — check `git log` before AND after a suite run and
#   attribute any delta before believing a count is yours.
# COMMIT, then run the bare pytest, THEN push. Two commits went out red on 2026-09-14 because a
#   green targeted slice was treated as a green suite; three went out green this session.
```

**Related docs:**
- `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` §"SETTLED 2026-09-14" — the
  residue arithmetic and why the named discriminator was inert
- `h-mad/scripts/h_mad_mutation_harness.py` `_sibling_specs` — the widening decision and its residue
- `docs/archive/2026-08/anchor-precheck-phase-5e-wiring/` — AC-3.5 and the sibling-only design
- `h-mad/SKILL.md` §`hooks/memory-index-guard.sh` — the wiring, the unwiring, the by-value locator
