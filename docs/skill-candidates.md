# Skill Candidates

## 2026-07-20 — orca-adaptation-tiers

- **agy/codex poll-until-idle dispatch**: assemble prompt -> hmad-dispatch send -> background poll on idle marker ("? for shortcuts" present, "esc to cancel" absent) + schema token -> parse verdict — recurrence: 12+ (every audit/TDD/arch-review this session) — candidate: yes
- **H-MAD phase-doc + agy-audit-gate loop**: write phase doc -> assemble audit prompt (template+doc+invariants) -> dispatch agy -> gate -> fix -> re-audit — recurrence: 9 (3 features x 3 phases) — candidate: maybe (already the /h-mad skill; a helper to stage+dispatch+gate in one call would cut ~40 tool calls)
