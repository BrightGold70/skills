---
title: "h-mad bootstrap: vendor skill collisions and mid-session agent registration"
author: Hawk
date: 2026-10-18
branch: main
cost: { minutes: 7, tokens: 278830 }
touches:
  - docs/01-plan/features/grok-audit-surface-brainstorm.md
  - docs/skill-candidates.md
---

## Decided
- grok-audit-surface: grok becomes a standing third audit leg (codex+agy+grok) on a document's first gating cycle only, gated on a seeded-defect calibration that must beat agy on recall and fabrication rate. Brainstorm at docs/01-plan/features/grok-audit-surface-brainstorm.md.
- `h_mad_install_check.py` SIBLING_NOT_SYMLINK on ~/.agents/skills/pdf and skill-creator is a false positive: they are anthropics/skills vendor installs pinned in ~/.agents/.skill-lock.json that share a name with this repo's OpenCode variants. Keep the vendor copies; backlog row filed at the end of docs/skill-candidates.md.
- grok audit-leg log scanning already exists in h_mad_audit_cycle.py (scan_grok, shapes grok/grok-truncated); the remaining work is calibration and routing doctrine, not driver plumbing.

## Tried and ruled out
- Relinking every SIBLING_NOT_SYMLINK copy blindly: diff each copy against the checkout first. Identical copies are safe to relink; divergent ones may be vendor installs, so check .skill-lock.json.
- Agent(subagent_type: "spec-author") right after registering the agents in ~/.claude/agents: agent types load at session start, so it fails with "not found". Use general-purpose with the agents/<name>.md role text as its contract.

## Watch out
- docs/.bkit-memory.json is untracked and has vanished before, leaving only its .lock file. Earlier feature records are unrecoverable; the resume oracle returns start_fresh only when no phase docs exist.
- The first-gate leg set (codex+agy+grok) differs from the revision-cycle leg set (codex), so --exit-check legs_changed can reset the exit streak. The spec must define the rule.
