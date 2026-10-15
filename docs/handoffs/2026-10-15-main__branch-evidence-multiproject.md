# Handoff — h_mad_branch_evidence.py: cross-sub-project pytest run → UNREADABLE (rc 4)

**Date:** 2026-10-15
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · feature/204-synopsis-path-preflight · session b5c8fa27-a879-4f50-8b9e-fc037a13fd2e
**Taken-Over-By:** skills · main · session e442f689-c626-4664-a605-af3241c4a4af · 2026-10-15
**Supersedes:** none — first on this branch for this topic

## Session Summary

While gating HemaSuite `synopsis-path-preflight` Task 3, `h-mad/scripts/h_mad_branch_evidence.py` could not
return `COMPLETE` on a branch whose code was green. It printed `TESTS: UNREADABLE reason=pytest-rc4` and
`EVIDENCE-VERDICT: UNREADABLE reason=tests-pytest-rc4`. The cause is in the tool, not the branch. Two defects
compound. (1) Consumer-test selection is a whole-word text match on changed module stems, so a generic stem
(`eligibility`) pulls in unrelated tests from a sibling sub-project. (2) All selected tests run in ONE
`pytest` invocation from the repo root. In a monorepo where two sub-projects each have `tests/conftest.py`,
pytest dies at collection with `ValueError: Plugin already registered under a different name`, which is rc 4.
This work is unstarted. Ownership moves to the skills lane.

## Key Learnings

- **The rc-4 is a collection crash, not a test result.** It is reproducible with two files, no feature code involved:
  `cd <HemaSuite worktree> && <hpw-venv>/bin/python -m pytest -q hematology-paper-writer/tests/test_reference_pdf_eligibility.py clinical-statistics-analyzer/tests/test_so_scope_boundary.py`
  → `ValueError: Plugin already registered under a different name: …/clinical-statistics-analyzer/tests/conftest.py`.
  Each file alone passes (72 / 36 for the 3 CSA files under the CSA venv).
- **Consumer selection over-matches.** `_names()` (`h_mad_branch_evidence.py:295`) is `(?<![\w-])token(?!\w)` over test source text. A test is selected (`why[rel] = "names …"`, ~L376) when its text names any changed module stem. Stems from the HemaSuite change were `eligibility`, `knowledge_orchestrator`, `_ko_retrieval`. The bare word `eligibility` matched 3 CSA tests (`tests/datacollect/test_acquisition_plan.py`, `tests/test_script_select_mrd_shape.py`) and the comment-level mention `knowledge_orchestrator` matched `tests/test_so_scope_boundary.py`. None of them imports the changed module. HPW tests such as `tests/tables/test_models.py` and `tests/test_agent_http.py` also matched on the word `eligibility`, which inflates the set but is harmless.
- **One interpreter for all sub-projects.** `_pytest()` (`:247-250`) runs `[sys.executable, "-m", "pytest", "-q", *files]` with `cwd=top`. The interpreter is whatever launched the script, so CSA tests run under the HPW venv (or under system python3, which gives `pytest-missing` — also observed). HemaSuite's CSA suite needs its own venv (`clinical-statistics-analyzer/venv`).
- Task 2 of the same feature reached `COMPLETE` with the identical tool only because its changed stems matched no CSA test text. Any change whose stem is a common word will hit this.

## Next Steps

1. Reproduce with the two-file command above, from a HemaSuite worktree. Any HemaSuite checkout with both sub-projects works; the canonical clone is `/Users/kimhawk/orca/HemaSuite`. Use the HPW venv `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/.venv/bin/python`.
2. Fix the run shape in `h-mad/scripts/h_mad_branch_evidence.py::_pytest` / `collect`. Group selected test files by their nearest rootdir (the closest ancestor holding `conftest.py`/`pytest.ini`/`pyproject.toml`, or a sub-project dir), and run one pytest per group with that group as `cwd`. Ideally run each group with that sub-project's own interpreter when a venv is discoverable (`<sub>/.venv` or `<sub>/venv`). Aggregate the per-group counts into the single `TESTS:` token. A group that cannot run must stay `UNREADABLE` with its own reason, never a silent pass.
3. Tighten consumer selection in `_names`/`collect`. Prefer import-shaped matches (`import X`, `from … import X`, `from …X import`, `"…X"` monkeypatch targets) over bare-word mentions, or at minimum restrict cross-sub-project matches to import shapes. Keep the selection reason in the `why` lines.
4. Add tests in the skills repo:
   - a two-sub-project fixture repo, where each sub-project has a `tests/conftest.py`;
   - a fixture where a generic-word stem appears only in prose in the sibling sub-project.

   Assert `COMPLETE` (not `UNREADABLE`) for green code, and assert that the prose-only file is not selected.
5. After merge, notify the HemaSuite lane, since `git pull` in the skills checkout is the update. The HemaSuite Task 3 gate record carries a waiver that cites this brief, and the next HemaSuite task that hits this can re-run instead of waiving.

## Open / Blocked Items

- The tool defect itself has status **not started**. It is owned by skills@main from this handover.
  - Location: `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
  - Artifact: `h-mad/scripts/h_mad_branch_evidence.py` (last touched `ce8e2116`); `_pytest` at L247, `_names` at L295, the consumer-selection loop near L376.
  - Sender evidence lives in a session scratchpad and is volatile; the key lines are quoted above. The paths are `/private/tmp/claude-501/-Users-kimhawk-orca-workspaces-HemaSuite-synopsis-path-preflight/b5c8fa27-a879-4f50-8b9e-fc037a13fd2e/scratchpad/t3_evidence2.txt` and `t3_evidence.txt`, the run made with system python3, which gives `pytest-missing`.
- There is no h-mad claim to release or adopt. This was never a claimed feature in either repo. TAKEOVER should create a record from this brief's slug (`branch-evidence-multiproject`).
- The sender keeps HemaSuite `synopsis-path-preflight` Task 3. Its gate closes with a recorded waiver that cites this brief, backed by direct measurements at `374190058`/`9ccdc432f`: HPW full suite 15038 passed with 1 Task-3 regression, fixed in `9ccdc432f`; CSA consumer files 36/36; anchors 104/104.

## Context for Next Session

**Files touched this session (sender):** none in the skills repo. This brief is the only skills-repo write.

**Uncommitted changes in skills@main at handover time:** `docs/skill-monitoring.md` and `handoff/tests/test_skill_candidates_census.py` were modified by another session. They are not part of this brief, so leave them alone.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff takeover   # adopts this brief
sed -n 240,300p h-mad/scripts/h_mad_branch_evidence.py
```

**Related docs:** `h-mad/scripts/h_mad_branch_evidence.py` module docstring (L1-60, which describes the pytest-set and sequencing contract); HemaSuite `docs/03-analysis/synopsis-path-preflight.task3.final-review.md`, where the gate record that cites this will be appended.
