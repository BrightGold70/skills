# H-MAD Project Invariants — Axis B (BrightGold70/skills repo, domain layer)

> Inlined by `/h-mad` as the **project (domain)** portion of Axis B, AFTER the
> workflow-universal `invariants.base.md`. The base layer already enforces the
> universal rules (audit-gate signal discipline, single-source contract,
> no-plugin-dependency, doc-template superset compliance, operator-override
> preservation, backward-compatibility, marker discipline) — they are NOT repeated
> here. This file holds only rules specific to this repository (a collection of
> Claude Code skills: `SKILL.md` + `references/*.md` + `scripts/*.py` + `hooks/*.sh`).

## Skill self-containment
- A skill MUST remain runnable from a bare clone: no import of another skill's
  internals, no hardcoded path outside the skill's own directory (except documented
  `~/.claude/...` install locations). Cross-skill coupling is a violation.

## Skill manifest integrity
- Every skill's `SKILL.md` MUST carry valid frontmatter with `name` and `description`.
  A skill whose entry behavior is changed without updating its `SKILL.md` contract is
  a violation.

---

## How agy uses this file
agy reads this as the domain portion of Axis B, after the base layer. Domain-rule
violations are `## Must-fix`. If this repo has no domain-specific concern for a given
feature, this layer may legitimately add nothing beyond the base rules.
