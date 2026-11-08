---
title: "Both 2026-11-08 closeout scout rows accepted: append-row pointer and codex hook-trust install advisory"
author: Hawk
date: 2026-11-08
branch: main
cost: { minutes: 5, tokens: 172898 }
id: l-6415d299
scope: repo
status: active
src: agent
touches:
  - docs/skill-candidates.md
  - h-mad/references/phase5-substeps.md
  - h-mad/scripts/h_mad_install_check.py
  - h-mad/scripts/hmad-dispatch.sh
---

## Decided
- `hand-inserted-mutation-rows` → yes. Add a pointer to the existing append-row mode at the Phase 5e step that tells GREEN to append rows. Recurrence was 6 in one session, at the exact point of use.
- `codex-hook-trust-unseen-by-install-check` → yes, despite recurrence 1. The operator wants the install check to warn when a hand-started codex would run ungated, rather than relying on the accepted residual being remembered.

## Tried and ruled out
- Declining row 1 like `hand-applied-single-mutants` (a navigation pointer, declined at recurrence 3): ruled out because 6 recurrences, and the doc read at that moment already describes appending rows without naming the tool.
- Keeping row 2 at maybe until a second sighting: operator chose to build it now.

## Watch out
- Don't edit docs or skill-candidates while a failure-diff run measures the live checkout: tests read phase5-substeps.md and docs/skill-candidates.md, so a mid-run edit contaminates the subject side.

In the code:
- pointer site: h-mad/references/phase5-substeps.md:147 (5e); tool: `h_mad_mutation_harness.py <spec> --append-row <row.json>`
- advisory: h-mad/scripts/h_mad_install_check.py, an `INSTALL:` line when .codex/hooks.json has the gate but no `[hooks.state]` trust record; see `_codex_hook_trust_arg` in h-mad/scripts/hmad-dispatch.sh (09c36baf, 1d92ef9c)
- rows: docs/skill-candidates.md §2026-11-08 carries-closed-codex-gate-armed
