SPEC-AUTHOR: DONE version=v1.9 path=docs/01-plan/features/agy-coder-fallback.spec.md lines=1206 sha256=ebc20f730eecb3c92894945a7db3b10e9dc4a44845812aac2a09501d36f8dd69

Start state checked before any write: sha 1d2a3442... matched, newest VH line was v1.8. HEAD is 3ad735f7.

premises verified:
- Field not yet in the tree: `grep -n 'implementation_authors\|review_independence\|"--append"'` over h_mad_state_schema.json, h_mad_state_write.py and state-schema.md gave 0 hits. That is expected, because FR-1 is additive.
- `_MiniDraft7` supports type, enum, required, properties, additionalProperties, items and minLength: sed of its docstring (`Deliberately supports ONLY`) in h_mad_state_validate.py, plus a grep of the `"enum"`, `minLength` and `"items"` branches in `_ok`.
- The assembler's `--module` is `required=True`: `grep -n '"--module"' h-mad/scripts/h_mad_assemble_tdd.py`. That is why `module` is a non-empty string, never null.
- Design DO-3 `--append KEY=JSON` is the Record mechanism: grep in the design, §"FR-7 — the review_independence add". The spec still names no mechanism; it only says that the same one serves both keys.

findings applied:
- D-15 / OD-E2 (a):
  - FR-1 table row and a new `implementation_authors` bullet. It covers the entry schema, duplicates and order, when the orchestrator appends, the mechanism, and the failure modes.
  - FR-1 §"Failure modes": a malformed or non-array field establishes no author set.
  - FR-7 Attribution reads the set from the field on every leg. The unrecoverable cases are closed to three (absent / no entry for the module / malformed), and each gives no entry. S5's "latest" now means array order.
  - FR-7 Record: the same mechanism applies to both keys.
  - New AC-1.3.
  - AC-7.3: the source is named, and a pre-field fixture is added.
  - D-15 entry, and the Open-questions line.
- Judgement calls (no explicit brief, flagged here for the orchestrator):
  1. `agent=claude` is appended when FR-2 resolves claude and Claude writes the code itself. That write counts as the accepted dispatch.
  2. A post-field feature with no entry for a module gets the same "no entry" outcome, named as a record-step defect. The record cannot tell this case from a pre-field feature, for the same reason D-11 gives.
  3. I added the AC-7.3 pre-field fixture, its mutant being "absent field read as an empty set". It pins the new absent rule. Revert it if you consider it out of scope.
  4. I added an FR-10 SKILL.md Phase-5 step bullet.
  5. AC-7.2 "the only FR-1 field that takes them" became "routing field". The old wording became false once `implementation_authors.agent` takes grok and claude.

values swept:
- `grep -n -i 'only FR-1 field|four field|four FR-1|FR-1 fields|no new field|adds none|kept in the procedure|dispatch order|dispatch list|cannot be recovered|each FR-1 field'` over the whole spec, fences and tables included.
  - Fixed: AC-7.2, and the Owed "adds none".
  - Kept as correct: line "FR-1 fields are therefore never inserted between", and AC-1.1's "each FR-1 field", which is generic and now covers the new field.
- AC count: `grep -o '^- \*\*AC-[0-9]*\.[0-9]*' | sort -u | wc -l` gives 21 distinct ACs. This agrees with `ACS: OK count=21 frs=9`.
- "three closed unrecoverable cases" in the Owed section: I counted the bullets under FR-7 §"The cases, closed" and got 3.

contradictions found: none in the spec. One concurrency note: `git diff --numstat` shows the design document is ALSO modified in the working tree (142+/53-). That is not my file, and another author is presumably writing it now. Every deletion in the spec's diff is mine; I checked this by listing the diff's `-` lines.

placeholder scan: clean. `PRECHECK: PASS issues=0`. There are 13 advisories, all on lines I did not touch:
- 12 PATH advisories: new files (`h-mad-agy-tdd-gate.py`, `.agents/hooks.json`, `.codex/hooks.json`) and an archive path.
- 1 COUNT advisory, inside an older VH entry.
`h_mad_ac_census.py`: `ACS: OK count=21 frs=9`. VH: `VERSION-HISTORY: OK ... version=v1.9 line=1206 placement=append`.

owed by other documents:
- Design (v1.3):
  - Add `implementation_authors` with FR-1's entry schema to the schema JSON, and add a state-schema.md row.
  - Retire "the complete set is kept in the procedure" and OD-E2.
  - DO-3 `--append` must accept the new key with the same guarantees.
  - Replace "When the dispatch list is lost" with FR-7's three unrecoverable cases.
  - Add the orchestrator append step (5e GREEN / fix acceptance) to the SKILL.md FR-10 surface.
- Impl-plan: AC-1.3's fixtures (both validator paths); AC-7.3's surface, now including the pre-field fixture.
- Plan: mirror the new field, AC-1.3 and the pre-field fixture, if the plan carries FR-1's field list or AC-7.3's fixtures. Plan stage 7 carries only the first of AC-7.3's fixtures (design v1.2 report).
