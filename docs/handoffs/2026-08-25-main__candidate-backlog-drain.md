# Handoff — Skill-candidate backlog drain, five tools, four adversarial reviews

**Date:** 2026-08-25
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Drained `docs/skill-candidates.md` from **46 open rows to 8**, all remaining ones codable (the scout then filed 3 more — **11 open**). Built
five tools (version-history bump helper, mutation-harness targeting upgrade, Phase-5d/5e dispatch
assembler, pane janitor, verdict-token gate scaffold), landed seven backlog rules as documented
invariants, and fixed the census tool that had been reading a 1946-line registry as three
candidates. Then ran adversarial agy reviews over everything shipped — **all four found real
defects**, including two false verdicts in the mutation harness that gates every other gate. 17
commits, all pushed. Suite 1993/0, every mutation spec ALL_CAUGHT.

## Key Learnings

- **I called agy "down" for most of the session and it was healthy the whole time.** Both failed
  dispatches were `hmad-dispatch exec agy … &` run INSIDE an already-backgrounded shell, so the
  parent exited and killed them. The evidence matched exactly — first run died after init plus one
  `step_update`, second before writing anything, both exit 0 — and I read the corpse as the tool
  being broken. Background the BLOCKING form and let the harness signal completion; never add `&`
  inside it. This cost five things shipping without review.
- **`ALL_CAUGHT` was satisfied by mutants that never ran.** A mutation breaking collection exits 2
  before the named test's assertion, and was credited as `killed by its named test`. Separately,
  `@pytest.mark.skip` exits 0, so the pre-check called a DISABLED test green. Both measured. Scoring
  now reads the pytest summary, not the exit code — which immediately reclassified a real fake kill
  that had been counted for a day.
- **A byte-size-identical mutation inside the same filesystem-mtime second reuses the stale `.pyc`**
  and never executes, while the file on disk IS mutated so the did-it-land check passes. Measured 4
  false survivors in 6 trials. That is a fourth cause of `survived` beyond the three this backlog
  already records: the mutant never ran at all.
- **Subtraction cannot identify a target.** The pane janitor's `Live − Baseline − Self` closes an
  operator's pane opened after the snapshot. Neither guard saw it: `--max` only bounds how many,
  the self-handle protects only the shell it runs in. `worker-list` gives positive identification
  and is the fix.
- **A guard can be rigged to hide its own gap.** The census coverage line hardcoded `J` in its
  denominator, filtering out the 33 non-J rows the reader missed — reporting clean while dropping
  all of them.
- **Weak tests, not missing guards, explain most survivors.** Of ~10 mutations that survived across
  the session, the large majority were my own fixtures failing to discriminate — a baseline that
  quietly supplied the `self` key the test claimed to check, a fixture whose sub-heading trivially
  failed the regex, a substring assertion a `_test_`-renamed method still satisfies.
- **A row that believes it duplicates an existing rule never gets implemented.**
  `verify-review-finding-against-tests` claimed to be "already an Axis-B rule"; grep found 0 hits
  across all 20 sections. It sat open for that reason alone.
- **One row's prescription was inverted and would have written a false rule.**
  `exec-terminal-mode-audit` (recurrence 20+) asked for a note that `exec agy` audits use the
  sentinel scrape "not report-file"; SKILL.md deliberately says the opposite, with both channels
  confirmed honoured 8/8 at 266 KB. Facts true, concern empty, prescription harmful.

## Next Steps

1. **post-edit identifier sweep** — highest-recurrence open row (3, already failed 1-in-3 by hand;
   `a311385` shipped 3 stale refs). Grep-and-classify after the last edit of a rename, plus an
   allowlist. Mutation-spec anchors are the surface most often missed.
2. **re-gate-after-edit guard** — record the gated content hash beside the verdict in
   `h-mad/scripts/h_mad_audit_gate.py`; 4 of 9 findings on a twice-clean design came from the edits
   fixing the previous cycle.
3. **task-slicer heading awareness** — `h-mad/scripts/h_mad_assemble_tdd.py:82` `task_body()`; stop
   at any equal-or-higher heading and track fences (copy `section_bounds` from
   `h_mad_version_history.py`). Measure the corpus first: how many impl-plans have trailing sections
   after their last task.
4. **controlled A/B dispatch harness** — two prompts differing in one variable, diff an observable
   that is not the exit code.
5. Remaining open rows, lower value: `live-e2e verb sweep`, `frozen-tree guard`,
   `stale-clone push guard`, `install-path suite verification`. See `docs/skill-candidates.md`.
6. **`re-anchor a mutation spec after editing the code it mutates`** — filed by the scout this
   session at recurrence **8**, the highest of any open row. Run the harness's own anchor
   precheck over ALL specs without applying anything; it would have caught six of this session's
   eight drifts before a run. Check first whether it subsumes item 1 rather than shipping two greps.
7. `[suggested]` **Decide whether `DECLINED` should stay overloaded.** It now means both "rejected"
   and "useful but not codable"; the header documents the convention, but a real fourth vocabulary
   word would read better and costs a header + census + tests change.

## Open / Blocked Items

- **`DECLINED` is doing double duty** — status: deliberate, documented in the file header. 14 rows
  are DECLINED meaning "no tool will be built", not "idea rejected". A reader who skims the marker
  without the note will misread them.
- **33 non-J rows in `docs/skill-monitoring.md` carry no `Status:` line** — status: filed as a
  candidate, editorial not mechanical. F 18, G 6, H 5, A 2, V 1, P 1. The census now REPORTS them
  (`parsed=46 row-shaped=79`). Do NOT answer by widening the parser — that silently reclassifies 33
  rows as open.
- **`handoff/scripts/test_handover_docs.py` — 2 failures** — status: pre-existing, NOT from this
  session. Verified identical at clean HEAD in a throwaway worktree:
  `test_takeover_runs_before_the_todos_are_restored`,
  `test_orca_is_only_ever_reached_through_the_wrapper`.
- **The four agy reviews' unfixed findings** — status: deferred deliberately, both filed as
  candidate rows rather than half-fixed. See `docs/skill-candidates.md` §"2026-08-25 — candidate-batch
  review sweep".

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_version_history.py` (new), `h_mad_assemble_tdd.py` (new),
  `h_mad_pane_janitor.py` (new), `h_mad_new_gate.py` (new), `h_mad_mutation_harness.py` (upgraded)
- `h-mad/tests/test_h_mad_{version_history,assemble_tdd,pane_janitor,new_gate,batch_doc_rules}.py` (new)
- `h-mad/tests/mutation-specs/{version_history,assemble_tdd,pane_janitor,new_gate,mutation_harness,batch_doc_rules}.json`
- `h-mad/invariants.base.md` (4 sections), `h-mad/SKILL.md` (registry + 5d/5e/audit-assembly wiring)
- `handoff/scripts/skill_candidates_census.py`, `handoff/tests/test_skill_candidates_census.py`,
  `handoff/tests/mutation-specs/census_registry.json` (new)
- `docs/skill-candidates.md`

**Uncommitted changes:** none. 17 feature commits pushed to `origin/main` (`8643b0d`) before this
handoff; this doc + learnings + the scout's candidate rows land as the 18th.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
# The interpreter matters — bare python3 is 3.14 here and has no pytest:
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q          # expect 1993 passed
/opt/anaconda3/bin/python3.11 handoff/scripts/skill_candidates_census.py \
  docs/skill-candidates.md docs/skill-monitoring.md              # expect OPEN=11, J-entries=46 OPEN=0
```

**Related docs:**
- `docs/skill-candidates.md` — the backlog; header documents the 2026-08-25 triage convention
- `docs/skill-monitoring.md` — the J registry, 46 entries, 0 open
- `h-mad/invariants.base.md` — four sections added this session
- `h-mad/SKILL.md` §"Audit prompt assembly", §"Phase 5 (Implementation) sub-steps"
