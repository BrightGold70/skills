---
title: Census --apply misplaced lines past U+2028/U+2029; backlog_cycle driver
author: Hawk
date: 2026-10-18
branch: main
cost: { minutes: 33, tokens: 160560 }
touches:
  - h-mad/SKILL.md
  - h-mad/scripts/h_mad_backlog_cycle.py
  - h-mad/tests/mutation-specs/backlog_cycle.json
  - h-mad/tests/test_h_mad_backlog_cycle.py
  - docs/skill-candidates.md
  - handoff/scripts/skill_candidates_census.py
  - handoff/tests/mutation-specs/census_registry.json
  - handoff/tests/test_skill_candidates_census.py
  - docs/01-plan/features/backlog-row-cycle.plan.md
---

## Decided
- skill_candidates_census.py apply_table now splits with re.findall(r"[^\n]*\n|[^\n]+\Z") because _rows numbers by "\n" and str.splitlines() also breaks on U+2028/U+2029 (present in docs/skill-candidates.md ~line 2570). Symptom: APPLY prints OPEN N→N and the status line sits above its row.
- h_mad_backlog_cycle.py records each cycle's own commits in .h-mad/backlog-cycles/<slug>.json; land diffs only those, never red^..HEAD, so concurrent cycles don't run each other's consumers/specs.

## Tried and ruled out
- Restoring the store with `git checkout -- path` after a failed commit: commit() already staged the edit, so the index restores the edited file. Use `git checkout HEAD -- path` (safe only because land refuses a dirty store first).

## Watch out
- Always read the APPLY OPEN delta after census --apply; an unchanged count means the line landed in the wrong place.
- Mutation specs hardcode python3.11; on hosts without it run a temp copy with the command swapped to a pytest-bearing interpreter (delete the copy after).
