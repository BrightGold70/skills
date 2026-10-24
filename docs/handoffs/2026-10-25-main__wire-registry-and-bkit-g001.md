# Handoff — wire-registry verify reports everything missing; bkit G-001 blocks heredoc text

**Date:** 2026-10-25
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · BrightGold70/hemasuite-document-workbench · session c1e6df26-e11b-4175-9102-d8ab139aa3de
**Taken-Over-By:** skills · main · session 40f31cca-a4e3-46e1-ab66-84c2fb302b3b · 2026-10-25
**Supersedes:** none — first on this branch for this topic

## Session Summary

While closing H-MAD feature `document-intake-source-review` in HemaSuite (PR BrightGold70/HemaSuite#52), two tooling defects surfaced. Neither is a HemaSuite bug. The feature was closed without relying on either tool: its wires were proven by a direct wire-cut, and the hook was worked around with the Write tool. Both defects are handed here for fixing under TDD. Nothing is claimed in any state file.

## Key Learnings

- `WIREREG: FAIL ... missing=268` across **every** feature in a repo is the signature of a broken instrument, not of 268 cut wires. A gate that fails every record cannot tell a cut wire from an intact one.
- A Playwright (e2e) pin cannot be represented in a pytest-collection-based registry at all, so any `wiring` task whose WIRE-PIN is a browser test is unverifiable at 5f by construction.

## Next Steps

1. **Reproduce the registry defect.** Run in HemaSuite worktree `/Users/kimhawk/orca/workspaces/HemaSuite/hemasuite-document-workbench`, read-only:
   ```bash
   python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_registry.py verify \
     --base efcaae522e206826dab9a832dee718504f54c416 --rootdir "$PWD" \
     --testpath hemasuite/tests --python "$PWD/.venv/bin/python"
   # observed 2026-10-24: WIREREG: FAIL registered=268 verified=0 broken=0 missing=268 ...
   ```
   Control showing the pins exist:
   ```bash
   .venv/bin/python -m pytest --collect-only -q \
     "hemasuite/tests/test_api.py::test_quit_stops_new_work_preserves_data_and_marks_interrupted_run"
   # observed: 7 tests collected (parametrized) ; full hemasuite/tests collects 475
   ```
   Hypotheses, none verified:
   - (a) the resolver does an exact node-id match while the pin is the unparametrized base id, so every parametrized test reads "missing";
   - (b) pins from other sub-projects (e.g. hematology-paper-writer/tests) are resolved only against `--testpath`, so they read "missing" rather than "out of scope";
   - (c) the collect subprocess fails and its failure is scored as absence.

   Also measured: an independent run without `--testpath` failed collection with exit 4, `file or directory not found: h-mad/tests`, so the default testpath is skills-repo-shaped. The default `python3` (3.15) has no pytest, giving `UNREADABLE interpreter-has-no-pytest`, which is correct. Script: `h-mad/scripts/h_mad_wire_registry.py`.
2. **Decide how a non-pytest WIRE-PIN is represented.** HemaSuite record `document-intake-source-review::Task 6` has pin `hemasuite/workbench/web/e2e/source-review.spec.ts::opens_every_fragment_on_original_rotated_or_cropped_page`. Options:
   - a `runner` field (pytest | playwright) with a per-runner resolver;
   - an explicit `unverifiable-by-registry` status that 5f reports as cannot-judge rather than missing.

   A FAIL is wrong either way.
3. **bkit G-001 false positive.** This is the bkit plugin, not skills code, and is a candidate for a local patch beside `docs/patches/bkit-enh310-quoted-heredoc-body/` plus an upstream issue. Repro: a Bash tool command whose quoted heredoc BODY (`cat > file <<'EOF' … EOF`) merely contains the Python identifier for a recursive directory removal (shutil plus the `rmtree` name) is refused with "bkit Destructive Detector: this command matches rule G-001 (Recursive delete) and is blocked as critical". The command deletes nothing; the text was a prompt for an agent. Rule sources: `~/.claude/plugins/cache/bkit-marketplace/bkit/2.1.38/` (tests in `test/unit/destructive-detector.test.js`; grep `G-001`). This is the same failure class as ENH-310: matching raw command text rather than shell structure.

## Open / Blocked Items

- Wire-registry verify reports all records missing. Status: not started. repo: `/Users/kimhawk/orca/skills` · branch: main · worktree: `/Users/kimhawk/orca/skills`. Artifacts: the HemaSuite registry `/Users/kimhawk/orca/workspaces/HemaSuite/hemasuite-document-workbench/.h-mad/wires.jsonl` (268 records), read-only.
- No representation for an e2e WIRE-PIN. Status: needs a design decision; same location.
- bkit G-001 heredoc-body false positive. Status: not started. Upstream: popup-studio-ai/bkit-claude-code; a local patch goes under `docs/patches/`.

## Context for Next Session

**Files touched this session (in skills):** this brief only.

**Uncommitted changes:** this brief (untracked when written; the sender commits it).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff takeover
```

**Related docs:**
- HemaSuite completion report: `/Users/kimhawk/orca/workspaces/HemaSuite/hemasuite-document-workbench/docs/archive/2026-10/document-intake-source-review/document-intake-source-review.report.md` (tooling findings section).
