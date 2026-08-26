# Handoff — Five new tools via a self-paced /loop, backlog `candidate: yes` to zero

**Date:** 2026-08-26
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Resumed yesterday's handoff, cleared its four divergences, then ran a self-paced `/loop` over the
restored todo list — eight items, one per iteration, all shipped. Five new tools
(mutation-spec anchor precheck, post-edit identifier sweep, audit-gate content stamp + readback,
task-slicer heading/fence bound, controlled A/B dispatch harness), plus three reconciliation
passes over the backlog. **9 commits, all pushed. `docs/skill-candidates.md` OPEN 11 → 6 (→ 8 after the closing scout filed two rows), and
`candidate: yes` reached ZERO** — every remaining row is a `maybe` below the file's own promotion
bar. Suite 2206/0, anchors 231/231, every mutation killed by its named test.

## Key Learnings

- **The anchor precheck caught my own edits twice within hours of shipping it.** Task #4's slicer
  refactor and task #8's census edit each drifted an anchor in the very spec covering that file,
  and `--check-anchors` reported it before the run could return REFUSED. A tool whose failure mode
  is "the guard is silently unverified" pays back fastest on the person who just wrote it.
- **`survived` had three distinct causes again in one session, and a fourth outcome appeared.**
  A real wire gap (`--include-history` parsed but never reaching `sweep()`, because every test
  called `sweep()` directly), an **equivalent mutant** (a stem equal to the identifier makes its
  branch unreachable, so survival measured nothing), and two weak tests. Separately one mutation
  was **REFUSED** — it broke collection rather than the property — and was replaced rather than
  credited. Each needs a different fix; the verdict token collapses all of them.
- **Measuring before building changed the work three times, in three different directions.**
  Task #4's corpus said 19 of 20 impl-plans were affected (build it). Task #6's four rows were all
  `maybe` at recurrence 1–2, below the file's own promotion bar (re-check, do not build) — and
  re-checking produced better information than building would have. Task #7's premise was already
  mostly false: 20 of 23 `DECLINED` markers already named their bucket, so a fourth vocabulary word
  would have rewritten 22 rows to fix three.
- **A test pinned against the REAL file caught a bug a fixture would have passed.** The first
  `TRIAGE` regex required the bucket to follow the marker directly, but it usually sits after the
  date and closing bold (`**DECLINED 2026-08-25 (triage: …)**`). It matched 2 of 22 and called the
  other 20 unqualified. A fixture built from the tight form is green on that bug.
- **Live fire found two defects that tidy `tmp_path` fixtures structurally could not show.** The
  identifier sweep's first real run returned 26 hits of which 19 were unfixable noise (`.bkit`
  machine log, handoff/archive records), and its excerpt truncated 160 chars from the line START —
  so on a 900-char JSON line the printed text did not contain the identifier being swept for.
- **The emoji in `skill-monitoring.md` is SEVERITY, never lifecycle.** `F11`–`F13` are 🔴 *and*
  FIXED: once in the resolution table, again as bullets with their original detail. Reading 🔴 as
  "open" makes eleven closed rows look live — which is most of what made the 33 non-J rows look
  like unfinished work for a month.
- **`| tail` masks the exit code.** `--check-anchors … | tail -35; echo $?` printed `0` for a run
  that exited 2. Known, hit again; the unpiped re-run is what proved the verdict.
- **My own throwaway probes disagreed with the tested tool twice, and the tool was right both
  times** — a case-sensitive `\bFIXED\b` undercounted resolved rows, and a line-scoped open-row
  scan re-flagged LANDED rows because terminal markers sit on the *next* line. Re-derive against
  the thing that has tests before reporting a count.

## Next Steps

1. **Dogfood the five new tools in a real `/h-mad` cycle** — none has been exercised inside a live
   run, only against this repo by hand. `--gated`/`--verify-stamp` in particular changes an
   existing gate's call sites: `h-mad/SKILL.md` §Phase-6 step 11 documents it, nothing invokes it
   yet. This is the `dogfood-a-bundled-prompt-live` row's shape.
2. **Wire `--check-anchors` into Phase 5e rather than leaving it advisory** — it is documented in
   `h-mad/SKILL.md` (§Phase 5 sub-steps, the mutation-harness paragraph) and run by hand. It earned
   two catches today; a run that skips it still reports `ALL_CAUGHT` over drifted anchors.
3. **Consider the same for `h_mad_identifier_sweep.py` after a rename lands** — the row's whole
   claim is that the timing (after the LAST edit) is the property, and nothing enforces the timing.
4. Remaining 8 open rows, all `maybe` and all below the promotion bar — see
   `docs/skill-candidates.md`. Four were re-checked today with findings recorded; two
   (`build mutation-spec anchors FROM the file`, `probe a tool with its simplest invocation`) were
   not touched this session.
5. **DONE — the auto-memory index was compacted** (`24,957 B → 17,051 B`, all 108 entries and all
   145 links kept). Nine hooks carried facts absent from their topic file; those were relocated
   before any trimming. Two link-list lines were left alone because trimming them would have
   dropped entries — and the first verification pass caught exactly that failure anyway: two
   replacements silently swallowed a co-located link, restored before finishing.
6. `[suggested]` **`h_mad_ab_dispatch.py` has never run against a real agent dispatch** — only
   against stub runners and a shell stand-in. Its `--run` argv templating works, but the
   `hmad-dispatch exec` shape the row describes is unproven end to end.

## Open / Blocked Items

- **The five new tools are unexercised in a live `/h-mad` run** — status: deferred, not blocked.
  All five are unit-tested, mutation-covered and hand-run against this repo; none has been through
  a real phase gate. Next Step 1 is the closure.
- **8 candidate rows remain open, deliberately** (6 carried + 2 filed by this session's scout) —
  status: below the promotion bar (recurrence ≥3 with `candidate: yes`; all eight are `maybe`
  at 1–2). Not a backlog to drain — the file's own
  re-scout trigger says leave them. `live-e2e verb sweep` additionally has a measured ceiling:
  only 4 of the wrapper's 46 verbs are read-only and safely sweepable unattended.
- **The auto-memory index was past its read limit** — status: **RESOLVED after the handoff was
  first written.** 24,957 B → 17,051 B, all 108 entries and 145 links intact, no broken targets,
  headings preserved. Nine hooks held detail that existed nowhere else and were relocated into
  their topic files first. User-global state, so nothing here is a git item.
- **`--verify-stamp` has no caller** — status: documented in `h-mad/SKILL.md` §Phase-6 step 11,
  invoked by nothing. It is opt-in by construction (default gate output is byte-identical without
  `--gated`), so this is a wiring decision, not a defect.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_mutation_harness.py` (`anchor_status()`, `precheck_spec()`, `--check-anchors`)
- `h-mad/scripts/h_mad_identifier_sweep.py` (new), `h_mad_ab_dispatch.py` (new)
- `h-mad/scripts/h_mad_audit_gate.py` (`--gated`, `--verify-stamp`, `GATESTAMP:` token)
- `h-mad/scripts/h_mad_assemble_tdd.py` (`_body_end()`, `_heading_level()`)
- `h-mad/tests/test_h_mad_{mutation_harness,identifier_sweep,ab_dispatch,audit_gate,assemble_tdd}.py`
- `h-mad/tests/mutation-specs/{identifier_sweep,ab_dispatch,audit_gate_stamp}.json` (new);
  `{mutation_harness,assemble_tdd,context_budget,context_budget_docs,hook_wiring}.json` (re-anchored)
- `handoff/scripts/{test_handover_docs.py,skill_candidates_census.py}`,
  `handoff/tests/{test_skill_candidates_census.py,mutation-specs/census_registry.json}`
- `h-mad/SKILL.md` (three new paragraphs in the Phase-5/6 sections), `docs/skill-candidates.md`,
  `docs/skill-monitoring.md`

**Uncommitted changes:** none. 9 commits pushed to `origin/main` (`920d204`); this doc lands as the
10th.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
# The interpreter matters — bare python3 is 3.14 here and has no pytest:
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ handoff/ -q        # expect 2206 passed
/opt/anaconda3/bin/python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors \
  h-mad/tests/mutation-specs/*.json handoff/tests/mutation-specs/*.json # expect ANCHORS_OK 231/231
/opt/anaconda3/bin/python3.11 handoff/scripts/skill_candidates_census.py \
  docs/skill-candidates.md docs/skill-monitoring.md                     # expect OPEN=6, J 46/0
# NOTE: never read `$?` through a pipe — `| tail` reports tail's status, not the tool's.
```

**Related docs:**
- `docs/skill-candidates.md` — header now records the 2026-08-26 `DECLINED` decision
- `docs/skill-monitoring.md` — header now records that F/G/H/A/V/P are a historical log
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps" (anchor sweep, identifier sweep, A/B
  harness), §Phase-6 step 11 (`--gated` / `--verify-stamp`)
