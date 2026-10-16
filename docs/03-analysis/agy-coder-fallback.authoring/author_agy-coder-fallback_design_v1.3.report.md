DESIGN-AUTHOR: DONE version=v1.3 path=/Users/kimhawk/orca/skills/docs/02-design/features/agy-coder-fallback.design.md lines=1432 sha256=22a8dee8a97f2b9d7ec392e8e0da3b0e2f5cc048fb50db7b916641167ca9dd1a

## Pre-write assertion
At the start the doc was sha256 499e7719…14ddc1, 1325 lines, newest VH v1.2. That matched the brief. No other writer touched it during the run (re-checked the VH lines and mtime before later edits).

## What changed (OD-E2 option (a), aligned to spec v1.9 D-15)
- **Header:** v1.3 note added, premises read at 3ad735f7.
- **FR-1:** "Four properties" is now "Five". Added `implementation_authors`: an array of `{module: string, minLength 1; agent: enum codex|agy|grok|claude}`. Both keys are required, `additionalProperties` is false, duplicates are kept and order is preserved. It goes after `review_independence`, so the `fallback_agent` index assertion is untouched. `minLength` was added to the list of supported constructs. Added a zero-record reading for the fifth key.
- **FR-7, author record:** entries go in through the existing `--append`, with no new writer code. The append happens at each accepted 5e GREEN and each accepted fix dispatch, never at 5d RED. Ordering rule: the append comes before any review leg of that code runs (spec D-15). The author set and the latest author are read only from the field. v1.2's "kept in the procedure" text is retired.
- **FR-7, when no entry is written:** exactly three cases. (1) The field is absent, which happens only for records written before the field existed. (2) The module has no well-formed entry. (3) The field is malformed. A resumed orchestrator is explicitly not one of these cases.
- **FR-7, AC-7.3:** the multi-author recovered fixture and the pre-field fixture are now derived from durable state.
- **Operator decisions:** OD-E2 is closed. Executive summary and Overview updated.
- **Test Plan:** AC-1.3 row added, matching spec v1.9's fixture list. The AC-7 row now says the fixtures are derivable from the record. Their code surface is still owed by the impl-plan.
- **Other sections:** Residuals (3 new, 1 rewritten), the Components table, FR-10 (a SKILL.md 5e/fix-dispatch append step) and the Owed list are updated.

## Override, announced (revert offered)
I added an `APPEND_ONLY` refusal for `--set`, placed in `merge_fields` before `def apply`. It covers two keys, `review_independence` and `implementation_authors`, and comes with a per-key mutation row and two fixtures.
- **Why:** the operator's rule is "never removed/altered", but `--set` (and library `set_fields`, which calls `merge_fields`) would replace the whole array.
- **The other writer operations were checked and cannot do this:** `create_feature` is idempotent, and `drop_undeclared` only drops undeclared keys.
- **Residual:** writes that bypass `_mutate`, and future history arrays not added to the tuple.
- **To revert:** delete the "append-only keys refuse `--set`" bullet in FR-7, the matching mutation row, the APPEND_ONLY clause in the AC-7 test row, the Components cell, the Residuals line and the Spec-owed sentence.

## Premises verified (command → result)
- Schema last property is `fallback_agent`, with no `review_independence` or `implementation_authors` yet. Checked with `python3 -c json.load(...)`: `[..., 'codex_status', 'fallback_agent']`, False False.
- `_MiniDraft7` supports `minLength`. `sed -n 28,60p h_mad_state_validate.py` shows it in the docstring; `grep -n minLength` hits lines 101-102 inside `_ok`, and the schema already uses it twice.
- The test `test_fallback_agent_description_states_the_four_facts` and its index assertion exist. Checked with `grep -rn`.
- Writer flags are beat, claim, create, drop-undeclared, feature, force, release, session-id, set, started-ts; there is no `--append` today. `merge_fields` and `create_feature` bodies read with `sed -n 181,226p`.
- `h_mad_assemble_tdd.py`: `--module` is `required=True`; `--agent` choices are `("codex","grok")` today (agy is added by FR-5).
- SKILL.md has `STATUS:` DONE|DONE_WITH_CONCERNS, `step5e:green_unreachable:<module>` and `step5e:verify_failed:<module>`. Checked with grep and `sed` over the 5e bullet.
- `git diff --stat cff71b49 3ad735f7 -- h-mad | wc -l` prints 0.
- Live records: each file's `orchestrator_state` holds 54 records here (at 3ad735f7) and 8 in HemaSuite (at 02d52e4e7). 0 of those records carry any of the five keys. The file is gitignored (`.gitignore:21`). The scratch scan was inline and left no file.
- Spec AC-7.3 has 5 fixture bullets. Counted with `sed -n '/AC-7.3 (v1/,/^- \*\*AC-8.1/p' | grep -c '^  - \*\*'`, which gives 5. The design's Owed bullet says "five".

## Sweeps
- `grep -n -i 'four\b|five'` found 76/82 (fixed), 149 (a historical four-key reading, kept with the fifth appended) and the Components cell (fixed).
- `grep -n 'dispatch list|in the procedure|durable|OD-E2|lost'` found no stale "kept in procedure" or "dispatch list lost" text. The remaining hits are v1.3 text or VH.
- `grep -n "four fixtures|AC-7.3's four|other four"` was fixed to five, or "three v1.8 … plus pre-field".

## Precheck / VH
- `VERSION-HISTORY: OK … version=v1.3 line=1432 placement=append`.
- `PRECHECK: PASS issues=0`. There are 28 advisories, all on lines that existed before this revision (path-not-yet-exists items for new files, plus COUNT items on VH v1.0–v1.2 and older body lines). None is on v1.3 text.

## Tree / spec contradictions
- The brief did not suggest a `minLength` on `module`; spec v1.9 adds it. I followed the spec.
- The spec says the append happens "before any review leg of that code runs". My draft said "before its review_independence entry". Aligned to the spec.

## Owed by other documents
- **Spec:** state the APPEND_ONLY `--set` refusal in FR-7 §"Record" (or reject it, and I revert).
- **Impl-plan:** the FR-1 Task carries AC-1.3. The FR-7 Task carries the APPEND_ONLY fixtures and row, plus AC-7.3's pre-field fixture. The FR-10 Task carries the SKILL.md author-append step. AC-7.3's code surface stays an open decision: OD-E2 made the fixtures' inputs durable, not executable.
- **Plan:** per spec v1.9 Owed, it gains `implementation_authors`, AC-1.3 and the pre-field fixture if it carries those lists.
- **Open question:** should the Phase-7 `unrecorded` detail text name authors from `implementation_authors`? I left it unchanged because spec FR-1 says no script reads the field.
