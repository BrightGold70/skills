# Handoff — `h_mad_do_preconditions.py` bypasses `has_gate_sections`, so the Phase-5 gate fails open

**Date:** 2026-08-10
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · feature/78-guideline-seeder-config-plumbing · session f0151733-b79e-406d-93b5-2706576e6b3d
**Taken-Over-By:** skills · main · session unknown · backfilled 2026-09-01 — fixed and merged as `379b881` gate-blindness-hardening; `_audit_issue` routes through `has_gate_sections` in `h_mad_do_preconditions.py` at HEAD

## Session Summary

Found while running `/h-mad do` on HemaSuite #78: **`h_mad_do_preconditions.py` never calls
`has_gate_sections`**, so any audit report lacking a literal `## Must-fix` / `## Should-fix`
heading is scored `must=0` and clears the Phase-5 precondition. The guard exists in
`h_mad_audit_gate.py`, is documented there as load-bearing, and this consumer skips it. It fails
**open**. Nothing is claimed and no code was changed in this repo — this is a filed finding, not
work in progress.

## Key Learnings

- The two code paths give opposite answers on the same file. Measured on a real audit report
  (`guideline-seeder-config-plumbing.design.audit.v10.md`, which states `GATE: FAIL must=2` in
  its own first line):

  | path | verdict |
  |---|---|
  | `h_mad_audit_gate.py <file>` (guarded) | `GATE: INVALID must=0 should=0`, exit 2 |
  | `h_mad_do_preconditions.py` (Phase-5 gate) | `must=0` → **PRECONDITION: PASS** |

- `has_gate_sections`'s own docstring names this exact failure: *"An extract that lacks them is
  not a clean audit — it is no audit at all… The gate must refuse to score it rather than report
  the absent findings as zero findings."* The CLI honours it; `check()` does not.
- Real-world impact, not hypothetical: four consecutive design-audit cycles on HemaSuite #78
  false-passed the design axis. Every one of those reports declared `GATE: FAIL` in its headline
  while the precondition read them as clean. The reports were honest; the gate could not read them.
- Blast radius is every feature in every repo using this skill whose reviewer emits findings under
  a heading other than the two literals — which is the default for an agent given the audit
  template's prose rather than its schema.

## Next Steps

1. **Add the guard to the precondition path** — `~/.claude/skills/h-mad/scripts/h_mad_do_preconditions.py`,
   in `_count_must_fix` (or in `check()` before it), mirroring the CLI at
   `h_mad_audit_gate.py`'s `main()`:
   ```python
   from h_mad_audit_gate import classify, _acknowledged_from_text, has_gate_sections

   def _count_must_fix(path: Path) -> int:
       text = path.read_text()
       if not has_gate_sections(text):
           raise GateUnreadable(path)      # -> a distinct token, NOT must=0
       ...
   ```
2. **Decide the verdict token for the unreadable case.** `PRECONDITION: FAIL` with a
   `UNSCORABLE:<path>` detail line is probably right — it must not be `MISSING:` (the file exists)
   and must not be silently `DIRTY:` (nothing was measured). Keep signal discipline: exit 0 on a
   verdict, non-zero only for operational errors.
3. **TDD it** — a fixture audit file with findings under `### [MUST-FIX 1]` and no literal
   `## Must-fix`. RED: today it returns 0. Then mutation-verify by deleting the new guard and
   confirming the test fails.
4. **Sweep for sibling consumers** — `grep -rn "classify(" ~/.claude/skills/h-mad/scripts/` and
   check each caller applies `has_gate_sections` first. The defect is "a guard exists and one
   consumer skips it"; there may be more than one.

## Open / Blocked Items

- **Not filed as a GitHub issue** — status: deferred to the operator. Sanitize before filing
  (§"Filing to a public tracker"): the reproducing paths are absolute and contain a username and
  a private project name.
- **No fix attempted here** — status: deliberate. The finding came out of a HemaSuite run; the
  sender did not want to edit a live skill mid-run (`~/.claude/skills/h-mad` is a symlink into
  this repo, so editing the working tree edits the skill the in-flight run is reading).

## Context for Next Session

**Files to change:**
- `h-mad/scripts/h_mad_do_preconditions.py` — the bypass
- `h-mad/scripts/h_mad_audit_gate.py` — read-only reference (`has_gate_sections`, its docstring)

**Uncommitted changes:** none by this handover.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
# reproduce the divergence on any report lacking the literal headings:
python3 h-mad/scripts/h_mad_audit_gate.py <report.md>          # INVALID, exit 2
python3 -c "
import sys; sys.path.insert(0,'h-mad/scripts')
from h_mad_do_preconditions import _count_must_fix
print(_count_must_fix(__import__('pathlib').Path('<report.md>')))   # 0
"
```

**Related:**
- Evidence lives in the sender's repo: HemaSuite
  `hematology-paper-writer/docs/02-design/features/guideline-seeder-config-plumbing.design.audit.v11.md`
  carries a "Gate-blindness note" recording the four false passes.
- Sender's handoff: HemaSuite `docs/handoffs/2026-08-10-feature-78-guideline-seeder-config-plumbing__phase5-t15-t16-t1-shipped.md`
