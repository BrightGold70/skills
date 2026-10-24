# Handoff — h-mad gap: a gate task cannot author a test

**Date:** 2026-10-24
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · feature/207-review-banner-gateway · session 245c1f4a-5fb4-45b9-866f-bcd52e815dd1
**Taken-Over-By:** skills · main · session 40f31cca-a4e3-46e1-ab66-84c2fb302b3b · 2026-10-24
**Supersedes:** none — first on this branch

## Session Summary

HemaSuite's review-banner-gateway (#207) shipped and merged to HemaSuite `main` (`5471a6593`). Its Phase 5 ran into an
h-mad defect three times (Tasks 20, 21 and 22). An impl-plan task whose **Task shape** is `gate` but whose deliverable
is a **new test file** cannot be staged. `h_mad_assemble_tdd.py --phase gate` writes a banner that forbids test edits,
and codex obeyed it: Task 20 attempt 1 refused to write the file. The fix belongs in this repo. Nothing has been changed
here yet.

## Key Learnings

- **The prohibition text is `h-mad/scripts/h_mad_assemble_tdd.py:475-479`** (at `b5683b27`). The phase banner for
  `"gate"` reads: "Do not modify production code or tests. Run every probe… Measure, never tune… Do not commit."
  `:406-410` also refuses `--expect-fail/--expect-pass` for gate tasks, so no gate dispatch can carry a pass count for a
  test it authors.
- **The workaround used in HemaSuite** was `--phase red --expect-fail 0 --expect-pass N --guard …` plus an
  orchestrator note naming the deliverable. It worked, but it mislabels the dispatch as RED and gives up the
  gate-specific `PROBE:` contract (`M:AT-GATE-PROBE-HANDOFF`, `:483`).
- **Codex's refusal was correct behaviour.** The fix is to the instruction, not to codex. Per the operator's standing
  rule, fix the instruction and never loosen a gate.

## Next Steps

1. Decide the shape of the fix before writing code. Two candidates:
   - (a) A distinct `Task shape` (for example `gate-authoring`) that permits creating test files only, and keeps
     production code forbidden and the measure-never-tune rule.
   - (b) A `--authors-test <path>` flag on `--phase gate` that relaxes the banner for exactly the named new paths
     and requires their pass count.
   - Either way the TDD hook needs no change: test paths are already allowed unconditionally
     (`h-mad/references/codex-implementer-prompt.md:20`).
2. Write the failing test first, under `h-mad/tests/`, for `h_mad_assemble_tdd.py` staging a test-authoring gate task.
   - Positive control: the staged prompt permits creating the named test file.
   - Negative control: a plain `--phase gate` still forbids test edits.
3. Update the gate section of `h-mad/references/codex-implementer-prompt.md` and the impl-plan task-shape vocabulary
   in `h-mad/SKILL.md` so that planners can emit the new shape.

## Open / Blocked Items

- **This item** — status: not started; nothing claimed (no `orchestrator_state` record).
  - Origin: repo /Users/kimhawk/orca/HemaSuite · branch feature/207-review-banner-gateway (merged into HemaSuite
    main) · worktree: none.
  - Evidence: the original refusal output `t20_gate.attempt1.out` lived in a session scratchpad and is gone.
  - Durable references:
    - the HemaSuite handoff `docs/handoffs/2026-10-24-feature-207-review-banner-gateway__phase5-tasks-20-23.md`
      §"Staging a gate task";
    - impl-plan Tasks 20–22 in
      `/Users/kimhawk/orca/HemaSuite/docs/archive/2026-10/review-banner-gateway/review-banner-gateway.impl-plan.md`.
- **Related, FYI (not handed over):** h-mad 5f's documented
  `h_mad_wire_registry.py verify --rootdir <repo-root> --testpath <project>/tests` read `verified=0` (all 253 pins
  "ABSENT FROM PYTEST OUTPUT") in HemaSuite.
  - Cause: the verifier runs `pytest <pins>` with cwd = `--rootdir`, while the pins are rooted at the sub-project.
  - `--rootdir <repo>/hematology-paper-writer --testpath tests` read `verified=283 broken=0`. The SKILL.md 5f wording
    (`SKILL.md:527`) is wrong for nested projects. Record: HemaSuite
    `docs/archive/2026-10/review-banner-gateway/probes/phase5f_close.md`.

## Context for Next Session

**Files touched this session (in this repo):** this brief only.

**Uncommitted changes:** this repo's tree belongs to an active lane. The worktree comment names grok-audit-surface
Task 14i, and `h_mad_grok_containment.py` and the `grok_audit_surface.json` spec are modified there. Do not stage
those files. Edit in a git worktree while that run is in flight, since `~/.claude/skills/h-mad` is a live symlink into
this checkout.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git worktree add ../skills-gate-authoring -b fix/gate-task-authors-test main
sed -n 400,485p h-mad/scripts/h_mad_assemble_tdd.py
```

**Related docs:**
- `h-mad/scripts/h_mad_assemble_tdd.py:406-483`
- `h-mad/references/codex-implementer-prompt.md`
