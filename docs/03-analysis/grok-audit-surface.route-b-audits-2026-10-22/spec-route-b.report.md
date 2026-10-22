SPEC-AUTHOR: DONE version=v1.21 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.spec.md lines=540 sha256=f02dfa34452ad4f3790f05230a70ca8d32a6748dd07ec717dd69605d2f4f395e

This revises v1.20 to v1.21 at HEAD be702c08, answering the spec items of audit2-spec-design.md. I edited only the spec and did not commit. Before writing, the file matched my v1.20 digest (a982b58e…), and its last Version History entry was v1.20.

premises verified (python extract of the design D21 section on disk):
- The wrapper writes `${stem}.here.txt` with one `here=<$here>` line (`# M:PATH-SCOPE-HERE`). The design on disk currently places this "before the clause check". The spec says "before assembly" per the coordinator, citing design v1.15. **Rests on design v1.15 landing that move.**
- `here_unrecorded`: a cycle directory does not hold exactly one well-formed `*.here.txt`.
- `here_mismatch`: that line's value is not the readings' `here`.
- `here_not_self`: the readings' `here` is not `SELF_DIR`.
- An unrecognised `--path-scope` makes argparse exit 2 with no prompt. The wrapper's `[ "$arc" -eq 0 ] || exit 4` path follows, there is no AUDITCYCLE: line, and `record-cycle` refuses `no_auditcycle_line:<file>`.
- `grep -n 'here.txt' h-mad/scripts/hmad-dispatch.sh` gives 0 matches. The record is design-only and not yet built, which is expected.

findings applied:
- AC-6.2: the AC-3.9 phrase is pinned on PASS, MISS and INCONCLUSIVE only. The AC-1.8 smoke-failure text carries no phrase, because it is not a measurement, and the doc test asserts none on that branch.
- AC-3.6 assembler bullet:
  - the h-mad directory is recorded both in the two run-level readings and in the per-cycle `${stem}.here.txt`, which is written before assembly, so an assembly-halted cycle has it;
  - the gloss now names `here_changed`, `here_not_self` (the reading's directory is not the checker's), `here_unrecorded`, `here_mismatch` (which takes over "not the wrapper's own script directory") and `dirty:unknown`;
  - the list is still single-sourced in D21.
- Nit: the Delivery row and "Where each form appears" now say the incident carries the `ASSEMBLER: UNPINNED`/`NO_CLAUSE` token line, or the `path_scope_missing` line for a path-scope halt. No `assembler=unpinned` stamp is written anywhere.
- Nit: AC-3.9 fail-closed now says an unrecognised switch has the same outcome but a different signal: exit 4, no AUDITCYCLE:, no REQUIRE: STOP and no halt-file line, and record-cycle refuses the cycle.
- Version History v1.21 has one entry (VERSION-HISTORY: OK).

values swept:
- `grep -n -o '.{50}assembler=unpinned.{80}'` gives 2 lines, both in Version History (v1.18, v1.20) and both historical. The body now has 1 occurrence, in the sentence that says no such stamp is written.
- "not the wrapper's own script directory" gives 0 after the edit.
- "AC-3.9 phrase" is now scoped in AC-6.2 only.

contradictions found: none in the spec. One dependency: "before assembly" needs design v1.15. The design on disk still says "before the clause check".

placeholder scan: `PRECHECK: PASS issues=0`. Advisories are only PATH `s2/run.txt` and `measurement.md`, both planned files.

owed by other documents:
- Design v1.15: move the here.txt write before assembly; carry the AC-6.1/AC-6.2 phrase and residual (round-2 must 2); D8 step 4 smoke-failure end reading. These are the design-author's.
