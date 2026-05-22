# h-mad — Hawk Multi-Agents Development

7-phase B-MAD-style orchestrator skill for Hawk's projects.

**Methodology**: H-MAD (Hawk Multi-Agents Development) — cross-project; HemaSuite is the v2.2 pilot consumer.

**Activation**: `/h-mad "<feature>"` (smart-resume) · `/h-mad do "<feature>"` (force Phase 5) · `/h-mad status` · `/h-mad reset "<feature>"`

**Phase structure** (1–4 manual checkpoints, 5–7 autonomous):

1. Brainstorm
2. Specify
3. Plan + Audit-Plan (auto-cycle agy audit between user revisions)
4. Design + Audit-Design (auto-cycle agy audit + cross-doc; back-prop to Phase 3 if needed)
5. **Implementation** (writing-plans for impl-plan → impl-plan audit → baseline branch → cmux Codex+agy TDD with PreToolUse hook gate)
6. **Verification** (architectural review → /pdca analyze → /pdca iterate to ≥90%)
7. **Closure** (/pdca report → /pdca archive → commit → push to main)

**Installation** (per project, one-time):

```bash
ln -s ~/Coding/skills/h-mad ~/.claude/skills/h-mad
ln -s ~/Coding/skills/h-mad/hooks/h-mad-tdd-gate.sh ~/.claude/hooks/h-mad-tdd-gate.sh
# Then register the hook in ~/.claude/settings.json under PreToolUse:
#   {"matcher": "Write|Edit", "command": "~/.claude/hooks/h-mad-tdd-gate.sh"}
```

**Project-specific layer**: each consuming project provides its own Axis B invariants (the rubric the audit phases use). HemaSuite's invariants are inlined in `references/codex-implementer-prompt.md` for v2.2 pilot; future spec revision will load `<PROJECT_ROOT>/.h-mad/invariants.md` per-project.

**Source of truth** (spec + plan): `https://github.com/BrightGold70/HemaSuite/blob/main/docs/superpowers/specs/2026-05-22-workflow-orchestrator-design.md` (v2.2, commit `6e5c160`).

**Layout** (this directory):

```
h-mad/
├── README.md            # this file
├── SKILL.md             # written by Plan Task 8
├── references/          # phase-table, failure-recovery, state-schema, 3 prompt templates
├── scripts/             # h_mad_*.sh, h_mad_*.py, h_mad_state_schema.json
└── hooks/               # h-mad-tdd-gate.sh
```
