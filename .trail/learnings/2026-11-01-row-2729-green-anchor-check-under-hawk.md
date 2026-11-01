---
title: "Row 2729: GREEN anchor check under a gate-trusted interpreter"
author: Hawk
date: 2026-11-01
branch: main
cost: { minutes: 38, tokens: 133514 }
touches:
  - docs/skill-candidates.md
  - h-mad/references/codex-verifier-prompt.md
  - h-mad/scripts/h_mad_assemble_tdd.py
  - h-mad/scripts/h_mad_target_identity.py
  - h-mad/tests/mutation-specs/anchor_check_python.json
  - h-mad/tests/test_h_mad_assemble_tdd.py
  - h-mad/tests/test_grok_audit_surface_docs.py
  - h-mad/SKILL.md
  - h-mad/references/agent-substrate.md
  - h-mad/scripts/hmad-dispatch.sh
---

## Decided
GREEN's `--check-anchors` line uses `anchor_check_python(python, project_root)` in h_mad_assemble_tdd.py: keep --python if its dir is in STATIC_TRUSTED_BIN_DIRS or the gate's _contained_venv_executable admits it; else first runnable python3 from ANCHOR_CHECK_PYTHONS (derived from the gate set, Homebrew first). The assembler must predict against STATIC_TRUSTED_BIN_DIRS, not TRUSTED_BIN_DIRS, which also trusts the CURRENT process's interpreter dir.

## Tried and ruled out
os.access(X_OK) as the candidate check: an xcode-select stub passes it and cannot run. Name-only `.venv/bin` keep: the gate refuses a venv outside the root.

## Watch out
Tests that pick "a trusted interpreter not first in the candidate list" are host-dependent; monkeypatch ANCHOR_CHECK_PYTHONS with fake runnable scripts instead. Reordering candidates after a mutation run silently invalidates its verdict: re-measure. A peer session moving HEAD mid-run gives MUTATION: TREE_MOVED; re-run once HEAD is stable.
