# Handoff — the Phase 3–4 audit loop never runs the repo's own test suite, so a repo test enforcing the audit loop's own invariant stayed red for 91+ cycles

**Date:** 2026-09-05
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session `9d8394fb-13d7-46e3-b161-9aafa8fb047e`
**Supersedes:** none — first on this topic

## Session Summary

Ownership of one h-mad defect moves to this lane. Measured on HemaSuite `#18 gateway-consolidation`
Phase 4, a dual-surface design audit that has now run **95 cycles** without meeting its
two-consecutive-both-clean exit gate. **The defect**: h-mad's Phase 3–4 audit cycle never executes
the project's test suite, so a repo test can be red for the entire life of a feature and every
cycle still scores clean. It happened, and the test that stayed red was
`tests/test_audit_phase_inline_summary_sync.py::test_real_features_synced` — whose guard is
*"for a real plan/design whose deepest audit is cycle N, every earlier cycle that recorded a FAIL
(or whose verdict is unparseable) must be cited in the Version History."* That is the audit loop's
own invariant, enforced by a test the audit loop never ran. It went green for the first time in the
feature's life on 2026-09-04, after 91+ cycles. **The fix is proposed, not written; nothing in this
repo has been touched.**

## Key Learnings

- **The gate has no execution path at all.** `h-mad/scripts/h_mad_audit_gate.py` is 407 lines and
  contains **zero** occurrences of `subprocess`, `pytest`, `check_call`, or `os.system`
  (`grep -nE 'subprocess|pytest|check_call|run\(|os.system'` → no output). It hashes each `--gated`
  path (`_digest`, `:257`; `verify_stamp`, `:266`) and counts bullets per section
  (`_count_section_findings`, `:147`; `classify`, `:196`). It is a document scorer. Nothing in it
  runs anything.

- **The correct framing is NOT "h-mad never runs the suite" — it does, at 5f, and only there.**
  `h-mad/SKILL.md:463` (step 5f) ends with *"Then run the full test suite:
  `pytest <project>/tests/ -v --tb=short`. All must pass (100%). Any failure → halt."* Step 5e runs
  a scoped pytest per module. **Phases 3 and 4 — plan audit and design audit — have no suite run in
  the protocol and no execution in the gate.** A brief that overstates this as "the gate never runs
  tests" sends you to fix a thing that is half-working; the gap is specifically the audit-cycle
  phases. Verify this yourself: `grep -rn -i 'pytest' h-mad/SKILL.md` returns hits at 437 (5e), 463
  (5f), 597, 832, 1787 and 2350 — none in a Phase 3 or Phase 4 step.

- **Why this is worse than an ordinary missing check: the audit loop was blind to a gate on
  itself.** The red test was not incidental to the feature — it enforces the audit trail the audit
  loop produces. Ninety-one cycles of a gated loop ran past a red assertion about those very
  cycles, and no surface, no gate and no operator saw it, because nothing in Phase 4 ever executes.

- **A design-phase suite run is cheap and the objection to it is weaker than it looks.** The
  documents under audit are markdown, so "the tests can't have changed" is the intuition that keeps
  this gap open. It is wrong twice over: repos carry tests *about their documents* (this is exactly
  such a test), and a long audit loop runs for days across many commits to the surrounding tree, so
  the suite's state at cycle N is not the state at cycle 1. On this feature the suite takes ~3
  minutes for 9,549 tests.

- **Beware the concurrency trap when you measure this.** `docs/skill-candidates.md:1277` records
  that two pytest runs over one working tree produced 6 and 3 failures in *different* sets, and 0
  when the file ran alone. Run the repo suite alone before believing any figure you get from it.

## Next Steps

1. **Decide where the check belongs** — in `h_mad_audit_gate.py` (which would give it an execution
   path it has never had, and needs a project-test-root argument it does not currently take), or as
   a step in the Phase 3/4 protocol in `h-mad/SKILL.md` beside the assemble/dispatch/score sequence.
   The 5f precedent is protocol-level, not gate-level, which argues for SKILL.md; the counter-argument
   is that a protocol step is an instruction an orchestrator can skip, and 91 cycles is evidence
   about what gets skipped.
2. **Decide the verdict semantics, which is the real design question.** A red suite during a design
   audit is not the same as a must-fix in a document. Options: it blocks the cycle's clean verdict;
   it is reported as a separate non-blocking line; or it blocks only the two-consecutive-clean
   **exit** gate rather than each cycle. Getting this wrong in the blocking direction makes every
   audit cycle hostage to an unrelated flaky test — see the concurrency trap above.
3. **Consider folding into `hmad-audit-evidence-gate`** (feature record present in
   `docs/.bkit-memory.json`, `current_phase=0`, unclaimed) rather than filing a new feature. That
   brief — `docs/handoffs/2026-09-03-main__hmad-audit-evidence-gate.md`, taken over by session
   `ca259110` — already owns two defects in the same file: the gate scores bullets without checking
   that a finding's quoted evidence exists, and a rejection-only cycle destroys the streak because
   it edits a gated file. All three are "the gate scores documents and never checks reality".
   **This is a judgement for you, not a conclusion from here.**
4. Whichever you choose, **the check needs a scoped test root**. `h-mad/SKILL.md:463` already
   documents why: an unscoped pytest from this repository root collects sibling-project import
   mismatches. HemaSuite has two suites (`hematology-paper-writer/tests`,
   `clinical-statistics-analyzer/tests`) and a monorepo root above both.

## Open / Blocked Items

- **This defect** — status: proposed, not written. `repo: /Users/kimhawk/orca/skills · branch: main ·
  worktree: none`. Artifacts: `h-mad/scripts/h_mad_audit_gate.py` (the scorer),
  `h-mad/SKILL.md:437`/`:463` (the 5e/5f suite runs that show the protocol-level precedent).
- **No claim was released, because none existed.** HemaSuite's
  `hematology-paper-writer/docs/.bkit-memory.json` holds exactly one feature record,
  `gateway-consolidation`, which stays with the sending session and is **not** part of this handover.
  There is nothing for you to inherit and nothing to force.
- **The evidence lives in HemaSuite and this brief changes nothing there.** Read-only pointers:
  `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/tests/test_audit_phase_inline_summary_sync.py:295`
  (the guard, with its docstring); the audit artifacts
  `…/docs/02-design/features/gateway-consolidation.design.audit.v{1..95}.*.md`; the commit that
  turned it green is on HemaSuite `main` in the 2026-09-04 session's seven-commit range
  `58a9ebd4..bf161591`.

## Context for Next Session

**Files touched this session:** none in this repo. This brief is the only file written here.

**Uncommitted changes:** this brief, untracked until committed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
grep -nE 'subprocess|pytest|check_call|os.system' h-mad/scripts/h_mad_audit_gate.py   # expect: no output
grep -rn -i 'pytest' h-mad/SKILL.md | cut -c1-80                                     # expect: 5e/5f only
```

**Related docs:**
- `docs/handoffs/2026-09-03-main__hmad-audit-evidence-gate.md` — the sibling brief, two defects in
  the same file, taken over by session `ca259110`. Read before deciding Next Step 3.
- `docs/skill-candidates.md:1277` — the concurrent-suite-runs trap that will corrupt your
  measurement if you run two suites over one tree.
