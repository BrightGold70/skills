---
title: "Resume 2026-10-31 handoff: skill-candidates row numbers drift"
author: Hawk
date: 2026-10-31
branch: main
cost: { minutes: 2, tokens: 144368 }
touches:
  - docs/skill-candidates.md
---

## Decided
Handoff row numbers for docs/skill-candidates.md are line numbers and drift when scout appends rows (2847→2854, 2846→2853, 2809→2816, 2726→2729, 2852→2859). Re-derive from `skill_candidates_census.py --list-open` and match by title before restoring todos.

## Tried and ruled out
Bare `hmad-dispatch` — not on PATH on Hawui-Macmini; use `h-mad/bin/hmad-dispatch` from repo root.

## Watch out
Task tool can carry stale tasks from a prior session (ids continue); TaskList and dedupe before/after restore. Orca worktree comment may still hold an older handoff stamp — prior WRITE stamp did not land.
