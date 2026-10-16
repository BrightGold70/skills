PLAN-AUTHOR: DONE version=v1.4 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.plan.md lines=914 sha256=d6766d45758baff8eace81df27d94509ab577f9accf13d16a6fe2cd5c2a4542e

Pre-write assertion: sha256 a6493546... and newest VH v1.3 matched the file at start (608e4302 was the last commit to touch it; HEAD 5f72c2f3). Not committed.

## Changes (all answer the delta review, no new scope)
- Must-fix 1 + Should-fix 1 (stage 6 AC-9.4 paragraph and DO-7): the plan no longer says "read from the assembled wiring prompt". Each copy is read from its own source location: each template copy located individually, the .py copy from its joined str constant in assemble(). The reason is stated: the prompt holds 3 copies and the assembled prompt holds 4, so a contains-check over either passes while one copy is sick. The locators are a DO-7 design obligation, and the plan states only what they must achieve: a single-copy mutation fails the test. Mutation rows: each `find` carries context unique in its file, because `h_mad_mutation_harness.py` `anchor_status` refuses a find with count != 1 (verified: `hits = source.count(find)` and "narrow the anchor until it is unique"). The `.py` row is written against the source bytes, including the adjacent-literal split (verified: `"...never a missing "` / `"symbol."`). The unrunnable example (dropping `the callee resolves at the RED base`) is removed. The Design-owed line now names the per-copy locators.
- Should-fix 2: "canonical carve-out sentence" becomes "canonical carve-out block (all three sentences of spec FR-9's quoted block)" at stage 6, DO-7 and the Design-owed line. Swept newline-collapsed: no "carve-out sentence" or "canonical ... sentence" remains.
- Should-fix 3: the FR-9 census paragraph now states that the joined-literal reading cannot see .py comments and has no stated ast.parse-failure behaviour. The AC-9.1 re-run takes the UNION of the two readings, and a parse failure is reported, never skipped. Owed/Spec no longer says "nothing is owed": it lists the FR-9 residual as owed and notes that a concurrent spec revision is adding it. The spec was not edited, and at 5f72c2f3 it had no such text (`grep -n comment` on the spec → no hits).
- Should-fix 4: DO-7's last sentence now matches the census. A str-constant or non-.py surface is found by re-running the sweep (the union). A run-time-built surface is found only by reading the code that builds the dispatch text.
- Should-fix 5: the doc-pin census files `test_h_mad_extract_verdict.py` `test_both_codex_prompts_spell_the_label` and `test_h_mad_portable_timeout.py` (3 tests: `test_the_rule_reaches_every_surface_that_can_improvise`, `test_every_rule_surface_keeps_the_halt`, `test_every_rule_surface_accounts_for_the_coreutils_present_case`) under the prompt entry. The count goes from "Nine carry a pin" to "Eleven" (9 from the matcher, 2 from reading). Three files stay unclassified: assemble_tdd_agent, install_check, verifier_prompt.
- Nit 1 taken, because it sits in the edited paragraph and feeds the locator choice: "three formats" is restated as four markdown shapes (ordered-list item, two paragraphs, bullet, table cell) plus adjacent Python literals. Verified by grep of codex-implementer-prompt.md (item `1. For each FAILING test`, `**If the dispatch carries a `WIRE:`` paragraph, `For GREEN phase (5e):` paragraph). Nits 2 and 3 were not taken (the reviewer said no change is needed in the plan).

## Measurements re-run (HEAD 5f72c2f3)
- Joined vs line sweep. A scratch script (since deleted) used regex `missing.symbol|tests the callee|ImportError.*AttributeError|AttributeError.*ImportError`, case-insensitive, over `git ls-files h-mad`. It read ast.walk str constants for .py files with whitespace collapsed, and collapsed whitespace in every other file. The line grep was `git ls-files -z h-mad | xargs -0 grep -liE '<regex>'`. Results: joined 7 files, line 6 files, union 7 files, line minus joined 0 files, ast.parse failures 0 files, .py files with a matching tokenize COMMENT 0 files. Both zeros are incidental, not load-bearing, and the plan says so.
- Pin test names were confirmed by `grep -n` on both test files. extract_verdict is parametrized over codex-implementer-prompt.md and codex-verifier-prompt.md. portable_timeout has 3 parametrize lists that name `references/codex-implementer-prompt.md`.
- Spec FR-9 block: the three sentences were confirmed with `grep -n 'only\*\* when\|must name both\|wire-cut' docs/01-plan/features/agy-coder-fallback.spec.md`.
- Precheck: `PRECHECK: PASS issues=0`. Advisories kept: STALESHA/PATH/COUNT on pre-existing lines are unchanged from v1.3. One new PATH advisory is on my text: `references/codex-implementer-prompt.md`. That is the test's literal parametrize value (relative to h-mad/), and the file exists at h-mad/references/. It is deliberate.
- VERSION-HISTORY: OK version=v1.4 placement=append.

## Tree contradictions
- None against the review. Every premise reproduced.

## Owed by other documents
- Spec FR-9 (concurrent spec author): add the comment/parse-failure residual and the union re-run for AC-9.1. The plan mirrors it.
- Spec AC-9.4: no change is needed if the spec's "carve-out text" already means the whole block. The plan now binds all three sentences.
- Design DO-7: the per-copy locators (each template copy individually, the .py copy via its joined constant), the canonical block text, and mutation-row finds unique in each file.

## Housekeeping
- The scratchpad has a pre-existing `mrows.py` that is not mine. I left it alone.
