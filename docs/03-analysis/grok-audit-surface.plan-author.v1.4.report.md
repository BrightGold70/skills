PLAN-AUTHOR: DONE version=v1.4 path=docs/01-plan/features/grok-audit-surface.plan.md lines=289 sha256=9915b23efb52b3d3c3b3cbfd3ed0b83f605e11c530ec91358f41160be87f4e9a

# Plan v1.4 (grok-audit-surface): propagation report

This revision only propagates changes. It applies spec v1.6 (`94a4fd2c`) and re-measured tree facts. Nothing was committed. The file was owned throughout: its mtime matched what I last read before each write, and its newest Version History line was v1.3 until my own bump.

## IMPORTANT: one brief "verified fact" is FALSE (RTK artifact)

The brief and the design-author v1.0 report both say "python3 (3.15) has pytest". That is false. In this shell the RTK hook rewrites `python3 -m pytest ...` to anaconda's `pytest` (`/opt/anaconda3/bin/pytest`, shebang `/opt/anaconda3/bin/python`), so the command reports pytest 9.1.1 whatever python3 is.
- `rtk proxy python3 -m pytest --version` → `/opt/homebrew/opt/python@3.15/bin/python3.15: No module named pytest`
- `rtk proxy python3 -c 'import sys;print(sys.executable)'` → `/opt/homebrew/opt/python@3.15/bin/python3.15`
- `rtk proxy python3 -m pytest --collect-only -q h-mad/tests` → No module named pytest. Without the proxy it showed "Pytest: No tests collected", which is the RTK filter.

The other premises hold:
- `command -v python3.11` → `/opt/anaconda3/bin/python3.11`
- `rtk proxy python3.11 -m pytest --version` → `pytest 9.1.1`
- `rtk proxy /opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest --version` → `No module named pytest`

So the only interpreter here with pytest is anaconda (python3.11 / python3 3.11.8). The plan now names `/opt/anaconda3/bin/python3.11` and states the RTK trap.

## Owed lines → what changed

Spec-author list:
1. Smoke component, "reads AUDITCYCLE: and COLLECT: lines". It now reads each S1 cycle's `AUDITCYCLE:` line (verdict word, `delivered=` and `Effort:`), the collected reports' `GATE:` tokens and the pass logs, and never a `COLLECT:` line. I swept every other `COLLECT:` site:
   - the "One authority" class member AC-1.3 now reads `delivered=` plus `GATE:`;
   - the "design pins" item on where lines are recorded no longer lists `COLLECT:`;
   - `COLLECT:` is dropped from the Convention Prerequisites token-consumer list, because no consumer in this feature reads it.
   - Three mentions remain, each saying the path prints none.
2. "What counts", "These lines carry no seed text". Rewritten to spec v1.6 AC-2.7's explicit list: reports (both copies), pass logs, kept prompts, captured agent output and `auditcycle.txt`. The wrapper stdout is calibration data because of the `Premise checklist:` that `render`/`premise_items` prints. The "(filed to the spec, Next Steps)" pointer is removed.
3. "Which list version" residual. Each root now records its list blob (AC-3.6). The re-score compares blobs and refuses `list_changed:<oid>` (AC-5.4), so this is a probe refusal and no longer an operator step. The S3 re-score bullet, the Leak-control order bullet, the Deliverables row and Success Criteria now name `list_changed`.
4. "The shas the measurement doc must cite". Added the smoke commit and the list blob id. The same sweep reached:
   - the S3 stage row ("both shas" replaced),
   - the measurement-doc Deliverables row,
   - the smoke-failure branch (it now cites the smoke commit and the list commit and blob, and says the main leak check runs against the smoke commit).
5. "SEEDSCORE: UNREADABLE" enumeration. Added `list_changed:<oid>` and `internal:<ExceptionName>`, and added both to Success Criteria.
6. Next Steps item 1. It now says the item is closed by spec v1.6.

Design-author list:
7. Convention Prerequisites interpreter. Covered in the section above.
8. R13 "absent". The row now reads the resolved path `/opt/anaconda3/bin/python3.11` at `94a4fd2c`, notes that the earlier reading was `absent`, and treats resolution as a drift axis. The "Interpreter constraint (R13)" bullet and the Risk row are reworded to say "absent, or has no pytest". The plan does not pick an interpreter for the mutation spec; it still says "the design pins".
9. S0b root count. Now "at least one per seeded document as spec AC-2.6 states, and the smoke document's root; the design names the count". Each root also records its list blob.
10. G4 force wording. The AC-9.4 force row now reads "always refuses with `legs_disagree:<phase>.v<N>`". I added a note that "treats every leg set as equal" is the same mutant as the remove row. Verified in `h-mad/scripts/h_mad_audit_gate.py` `exit_check`: the only refusal is `if len(distinct) > 1:`, so "treat all as equal" and "skip the comparison" both mean that refusal never fires.
11. Old shas. Restamped:
    - 611c299d → 2f7bf7ae: the AC-3.2 observation, with the old sha kept in parentheses; Version History v1.3, twice.
    - 946ffc5a → a0b41697: the Readings preamble, R12, and Version History v1.2, twice.
    - The `5b2df07` filename token is kept.
    - b085ad7a was not cited.

Spec-forced items not in either list, applied because spec v1.6 forces them:
- **Smoke commit as a stage step.** It is now an S1 step (S1 row, plus a new "S1, the smoke commit" bullet), because AC-2.7 creates it.
- **Score sha ancestry.** The score sha now descends from the smoke commit, per AC-2.7.
- **cycle_token triggers.** `cycle_token:<cycle>` now has the spec's seven triggers, with one AC-5.5 fixture per trigger. AC-5.5 says each branch gets its own fixture.

## Measurements re-run (2026-10-19, HEAD 94a4fd2c)
- `git diff --quiet 1a470339..94a4fd2c -- h-mad docs/archive` → exit 0. `a0b41697..94a4fd2c` also exit 0.
- R1: `rtk proxy /opt/anaconda3/bin/python3.11 -m pytest --collect-only -q h-mad/tests | tail -1` → `6733 tests collected`. The command's interpreter was changed from python3.14, which no longer has pytest.
- R12: the python3 json one-liner → 1 row, `shell-prompt-divergence-assertion-drop scripts/hmad-dispatch.sh None`.
- R13: the plan's command → `166 of 177`, resolving to `/opt/anaconda3/bin/python3.11`.
- R14: `git ls-remote origin 'refs/heads/calibration/*'` → empty, exit 0.
- R15: `git ls-files docs/03-analysis/probes/grok-audit-surface | wc -l` → 0.
- COLLECT:
  - `grep -c 'COLLECT:' h-mad/scripts/hmad-dispatch.sh` → 0.
  - `grep -n 'COLLECT:' h-mad/scripts/h_mad_audit_cycle.py` → 2 lines, a docstring and a comment.
  - `grep -ln '"COLLECT:'` over the scripts → only `h_mad_collect_report.py`.
- `grep -n 'def premise_items\|Premise checklist' h-mad/scripts/h_mad_audit_cycle.py` → `premise_items` and both `Premise checklist` render lines are present.
- Sha remap: none of the four old shas is reachable, and all four new ones resolve to the subjects in the remap table.

## Tools
- precheck → `PRECHECK: PASS issues=0`. Advisories kept:
  - PATH (measurement.md, twice): new file by design.
  - COUNT on the cycle_token bullet ("4 names beside a list of 5"): the sentence says seven = "these two" + five listed, which is correct.
- `h_mad_ac_census.py` spec plan → `ACS: OK count=51 frs=10`.
- `h_mad_version_history.py` → `VERSION-HISTORY: OK ... version=v1.4 line=289 placement=append`.

## Contradictions and owed elsewhere
- **Design / brief, interpreter:** "python3 (3.15) has pytest" is false; it is the RTK rewrite (see above). The design's choice of `/opt/anaconda3/bin/python3.11` is unaffected, but its premise line should be corrected.
- **Spec vs design, root count:** spec AC-2.6 says "one root per seeded document", while design decision 4 says "one fresh root per cycle (ten or more)". The plan defers the count to the design and does not choose. One of the two documents should align: spec author or orchestrator.
- **Spec vs design, `delivered=out`:** spec v1.6 AC-1.3 (D-g) counts `delivered=out` as delivery, but design v1.0 decision 8 counts it as `no_delivery`. The plan follows the spec. Owed to the design author, who may already be fixing this.
- **Optional heading rename:** the heading "Calibration data and its two shas" now also covers the smoke commit. I left it unrenamed for minimal scope; a later revision could rename it.

## Declines
- I did not rename the section heading (see above), to keep scope minimal.
- I did not choose the mutation-spec interpreter or the root count; both stay with the design.
