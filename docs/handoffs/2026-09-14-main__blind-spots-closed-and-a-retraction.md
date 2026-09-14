# Handoff — both harness blind spots closed, and a claim of mine retracted

**Date:** 2026-09-14
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-14-main__backlog-cleared-and-the-hollow-kill.md

## Session Summary

Resumed the predecessor's five carried items and **closed four outright, advanced the fifth**.
Fifteen commits, all pushed; suite **3684 passed / 0 failed**. The two mutation-harness blind spots
the docstring called permanently unclassifiable are now classified in code; the `#56` enumeration is
exhaustive; the four borderline rows are adjudicated. The session's most useful output is not a fix
but a **retraction**: a claim I published earlier today with confident-sounding evidence was wrong,
and the way it was wrong — grepping the OLD symbol a backlog row named, which cannot see a NEW
symbol doing the job — is the reusable part.

## Key Learnings

- **Grepping the symbol a row names can only prove that symbol did not change.** I re-probed
  `a wrapped bold row name is not a row`, found `ROW` at `:30` still single-line, and published
  "STILL OPEN, both halves" at `7546914`. The fix had landed at `7cf6803` **a week earlier** — via
  `NAME` at `:40` (`re.S`) and a COVERAGE count that uses `OPENER`, not `ROW`. `ROW` is still
  there; it simply stopped being what answers the question. One fixture disproved me in one
  command. Retracted at `9d1a73e`, struck through rather than deleted.
- **Unattributable and unreportable are different**, and conflating them is what kept both harness
  blind spots open. pytest blames a `TimeoutExpired` on the test file that set the timeout, never on
  the module that hung — so no attribution is possible, and the old docstring stopped there. But
  *"something hung"* is knowable without knowing *what* hung. `timeout_kills=N` is published
  unattributed and never folded into `crash_kills`, whose every entry names a file.
- **A monotonic gradient beats "the knowns fall inside the cut-off" as calibration.** Seven readers,
  each blind to its band and to each other, returned `DIFFERENT` densities of 19, 7, 5, 1, 0, 1, 0
  against mean token-overlap 0.070 → 0.905. Knowns-inside-a-cutoff is equally consistent with a
  screen that merely fails to be *anti*-correlated; a gradient is not. It also doubles as a free
  negative control — a biased reader pool would produce a flat row.
- **My own instrument caught three defects in my own fix, on its first run.** `timeout_kills=2` was
  a FALSE POSITIVE matching `"subprocess.TimeoutExpired: …"` where it appears as a *fixture string*,
  because pytest echoes assertion source into failure blocks — the exact hazard I had written into
  the docstring one paragraph earlier. A second mutation survived correctly (nothing asserted the
  property it stripped). A third survived while **inert** — it could not restore the bug once the
  anchor moved into the pattern, which is "a mutation that can never fire reads as a passing
  battery" met in the wild.
- **A count borrowed from a different measurement propagates.** The `#56` probe doc says "202 test
  rows extracted"; the real count is **200**. 202 is `grep -c 'AC-x.y'` — the very figure that same
  document flags as mislabelled *in the brief*, reused one section later as its own row total. The
  load-bearing 177 is independently correct.
- **A line pin can be wrong from birth, and that reads identically to drift.** `h-mad/SKILL.md`'s
  only line pin cited `docs/skill-candidates.md:1277`; at the commit that wrote it the row was at
  **1319**. `PINDRIFT` exists for this class and names it, but the precheck runs on *phase
  documents* — never on SKILL.md. The pin was also not past-EOF, so no structural check could see it.
- **A label can propagate sideways between sibling rows rather than upward from a criterion.**
  `#56` Task 14 r24's own text names design v1.10's *"Structural, registry wire"* bullet as its
  source, so it inherited `ac_5_8` from Task 13's r6, not from AC-5.8. A prefix-vs-AC census
  structurally cannot see which direction a label travelled.
- **Two readers err in opposite directions on lexically-confusable rows.** An adjudicator called a
  known SWAP `SAME`, reasoning *"quorum value unmoved by the flag"* — misled by the word `quorum`,
  which appears in the row name only because `enforcing_site` lives in the `tools.grounding_quorum`
  module. A module-path token, not a subject. The second adjudicator got it right, so it is
  per-reader error, not bias — which is why `#56`'s count is published as a **floor**, not a total.

## Next Steps

1. **Decide whether the 19 unadjudicated `#56` DIFFERENT calls are worth resolving** — they sit at
   ranks 1–62, i.e. *inside* the band the earlier pass already read and judged, so this is two reads
   of the same rows disagreeing. Sample of 9 adjudicated: 2 confirmed, 5 refuted, 2 split. See
   `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` §"ADJUDICATION RETURNED".
2. `[suggested]` **Close the `$@`/`$*` half of the positional-arg lint** —
   `handoff/tests/test_handoff_takeover_mode.py:224` matches `\$[0-9]` only and reads exactly one
   file. `h-mad/SKILL.md`, the larger body of fenced blocks, is unguarded.
3. `[suggested]` **Add the self-matching-mutation refusal** — nothing refuses a mutation whose
   `find` occurs inside its own `replace`. `h_mad_mutation_harness.py`; the anchor-count half
   (`hits != 1`) already exists at `:958`.

## Open / Blocked Items

**Carried from the predecessor — every item accounted for:**

- **Four borderline `#56` rows awaiting a second opinion** — **CLOSED** (`129e543`, `edd7b91`).
  Three are `DIFFERENT`, one is a `GUARD`; the parked "each is probably a positive control" framing
  held for exactly one of four. Twelve → fifteen.
- **`#56` rows 71–177 unread** — **CLOSED** (`cf6c933`, `6e3fab6`). All 173 non-borderline rows read
  by seven blind readers. The tail held **2** findings in 107 rows against 31 in the 70 already
  read; `T1 r7` (rank 136) is confirmed by three independent readers. Calibration 12/12.
- **Hooks-validator replay lived only in the scratchpad** — **CLOSED** (`dfff6fd`). Recovered from
  the dead session's scratchpad and committed as `h-mad/scripts/h_mad_check_plugin_hooks.py` + 28
  tests + a 12-mutation spec (ALL_CAUGHT). Live run: 7 installed plugins, all CLEAN.
- **Two mutation-harness blind spots** — **CLOSED** (`64b3752`, `f9551bf`). Both classified in code.
  8 mutations, ALL_CAUGHT.
- **`docs/skill-candidates.md` 54 open rows, 2 reconciled** — **ADVANCED, not closed.** All 47
  previously-untouched rows verified against the tree: **33 OPEN, 11 PARTIAL, 3 LANDED**. Census
  **54 → 48 open**, LANDED 84 → 89. This closeout's own scout then appended **4 new rows**, so the
  live figure is **52 open / 225 candidates, coverage 231/231** — reconciliation moved it down 6 and
  the scout moved it up 4, and both numbers are real.
- **Inherited WSG brief attribution, preserved:** `**Handover-From:** HemaSuite-wsg ·
  feature/website-source-grounding · session 8574638e`. Claim
  `hmad-tooling-findings-from-the-wsg-lane` unchanged — still released, still unclaimed.

**Open, new this session:**

- **52 `docs/skill-candidates.md` rows remain open** (48 verified + 4 this closeout's scout added),
  and unlike the predecessor's framing the 48 are now *verified* open rather than unexamined: every
  one was read against the working tree this session. 11 carry a new PARTIAL note naming precisely
  which half shipped. The 4 new ones are unverified by construction — they were written today.
  Census: `python3.11 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md`.
- **19 `#56` DIFFERENT calls never adjudicated** — status: open by choice, deliberately uncounted.
  They fall at ranks 1–62, inside the already-read band, so they are a disagreement between two
  reads rather than new territory. The published figure is a **floor of seventeen**; the ceiling is
  not established.
- **`T1 r8` (rank 99) is corroborated but unadjudicated** — found by a fourth reader with the same
  mechanism as `T1 r7` after the adjudication set was already built.
- **Sibling worktree `wsg-backlog-two-items-owed-here` reports `item 1 open`** — status: **not this
  lane's, and not handed over.** `repo: /Users/kimhawk/orca/skills · branch: main · worktree: a
  sibling Orca worktree on main (seen in `worktree-ps`, comment `taken over:
  wsg-backlog-two-items-owed-here · item 2 falsified (root registry retired c8b0ed79), item 1
  open`)`. The predecessor's carried list closed item 2 and is silent on item 1. Recorded here so it
  does not leave the chain unmentioned; **no ownership moved** — it already has an owner.
- **The `#56` probe doc's "202 test rows" is corrected to 200 in `cf6c933`**, but the same borrowed
  figure may exist in the brief it came from — not swept.
- **The auto-memory index needs real compaction** — status: open, **but the silent loss is repaired
  and there is now a guard** (`ae7d9a7`). It was **over** the cap, not near it: 25254 bytes against
  25000, and it had been dropping its tail on every load — an h-mad skill note and the entire *"Orca
  orchestration needs a bound Run"* entry were invisible to every session. Repaired by shortening
  HOOKS only (no entry removed, no link changed): **25254 → 24966, dropped=254 → 0**, both entries
  loading again.
  **What is still open** is compaction to the 17500-byte target: the index sits at 100% of cap, so
  the next memory written pushes it back over. Not done here because it is a judgement call about
  which of ~120 entries merge or retire, and doing it badly drops the pointers that still matter.
  `repo: n/a (user-global local state, not a git repo) · path:
  ~/.claude/projects/-Users-kimhawk-orca-skills/memory/MEMORY.md · guard:
  python3.11 h-mad/scripts/h_mad_check_memory_index.py --show-dropped`

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_check_plugin_hooks.py` (new), `h_mad_mutation_harness.py`, `h-mad/SKILL.md`
- `h-mad/tests/test_h_mad_check_plugin_hooks.py` (new), `test_h_mad_mutation_harness.py`
- `h-mad/tests/mutation-specs/check_plugin_hooks.json` (new), `harness_blind_spots.json` (new)
- `docs/skill-candidates.md`, `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md`

**Uncommitted changes:** none. The standing untracked `lanestate/` remains, unchanged and not this
session's. (The `.done` audit markers the predecessor listed are gone from `git status` — not
removed by this session; noted because the predecessor named them.)

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                  # expect 01e2c87 or later, in sync
git status --short | grep -v '\.done$'             # expect only lanestate/
python3.11 -m pytest -q                            # expect 3684 passed, 0 failed — ~10 min
# python3 here is 3.14 with NO pytest — use python3.11
# Run from the REPO ROOT, not h-mad/: pytest.ini testpaths covers three dirs
#   (h-mad/tests handoff/tests handoff/scripts). `cd h-mad && pytest tests/` collects
#   3351 and is the narrower run the PREDECESSOR's resume line prescribed.
# NEVER run two full suites at once: concurrent runs manufacture phantom failures.
# A handoff doc's OWN commit adds doc-derived parametrized tests, so any "expect N"
#   written here is stale the moment this file lands. Measured: 3307 at 43c0cc6,
#   +2 from the predecessor's own commit.
```

**Related docs:**
- `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` — the exhaustive read, the
  monotonic-gradient calibration, the adjudication, and the floor-of-seventeen reasoning
- `h-mad/scripts/h_mad_mutation_harness.py` — `timeout_kill`, `untargeted=N/M`, and the
  unattributable-vs-unreportable rule in the module docstring
- `h-mad/tests/mutation-specs/harness_blind_spots.json` — the three defects the harness caught in
  its own repair, recorded as rows rather than quietly fixed
- `docs/handoffs/2026-09-14-main__backlog-cleared-and-the-hollow-kill.md` — the predecessor
