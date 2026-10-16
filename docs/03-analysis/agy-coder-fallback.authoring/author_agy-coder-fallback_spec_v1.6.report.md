SPEC-AUTHOR: DONE version=v1.6 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=953 sha256=e65dd606a138cca11b92335c5cebe63604788dff78d70cacf0d4e96253752d37

premises verified:
- Before writing, the spec was at sha 7324587e…, newest VH v1.5, and its mtime did not move between the read and the write.
- The joined reading vs the line grep, from a scratch probe at HEAD 5f72c2f3 (h-mad last changed at 083a8233):
  - joined reading 7 files, line grep 6 files, line grep minus joined reading 0 files, union 7 files;
  - `.py` comment-token hits 0 files, joined-comment hits 0 files, ast.parse failures 0.
  - The probe was deleted afterwards. A `mrows.py` that I did not create is still in the scratchpad, and I left it alone.
- `h_mad_assemble_tdd.py`:
  - the wiring header is split as `never a missing "` / `"symbol."` (`grep -n 'never a missing'`);
  - `fill_slots(template_text, …)` returns `filled` (`grep -n fill_slots`).
- `h_mad_mutation_harness.py` `anchor_status` counts with `source.count(find)` and refuses with "narrow the anchor until it is unique".
- Locators in `codex-implementer-prompt.md`: `**RED acceptance evidence`, then `1. For each FAILING test`; `**If the dispatch carries a \`WIRE:\``; `For GREEN phase (5e):` (`grep -n`).

findings applied:
- Should-fix 3 (FR-9):
  - New paragraph naming the axis "text in a .py file that is not a str constant", with three members:
    - comments: covered by joined `tokenize` comment text plus the line grep;
    - ast.parse rejects: reported as `unparsed=N`, the line-grep and comment readings still apply, and the file is read by hand;
    - bytes literals: residual when split across lines.
  - The sweep is now defined as the UNION of the line grep and the joined reading. The measurement is stamped at 5f72c2f3, and the comment zero is labelled incidental.
  - The Census-method sentence now says "joined reading" and points to the full sweep. The run-time residual sentence now says "no reading in the sweep sees it".
- AC-9.1: the shipped-tree re-run is the union and reports `unparsed=N`. A nonzero N fails the AC until those files are read by hand.
- Must-fix 1, spec side (AC-9.4):
  - The carve-out text is the whole three-sentence FR-9 block, and a check that binds only sentence 1 fails the AC.
  - Each copy is read from its own source location, and the span it reads holds no other copy. The AC rules out a contains-check over the assembled prompt and a file-level check over any file that holds more than one copy.
  - A locator that matches 0 spans, or more than one, makes the test fail. The design names the locators.
  - The control mutates exactly one copy. It runs once per copy (6 runs) and once per sentence in at least one copy.
  - Each row's `find` is unique in its file, and the `.py` find is written against the source bytes, including the literal split.
- Should-fix 4: the spec already said "carve-out text", so no narrowing was needed. AC-9.4 now names all three sentences explicitly.

values swept:
- I grepped the spec for `joined-literal|The sweep runs|canonical|three-sentence|assembled`. The two other sweep-describing sentences, at the Census method and the run-time residual, were updated. `canonical` hits only unrelated root-canonicalisation text.
- The 9c3b799d stamp on the joined-reading file list stays as it is. It is the same h-mad tree as 5f72c2f3, since h-mad last changed at 083a8233, so the file set is unchanged.
- No counts moved: still five surfaces plus the GREEN variant (six copies), and still 7 and 6 files.

contradictions found: none between spec and plan on these points. The spec does not prescribe locators. The plan/design must name them, and the review's options (a), (b) and (c) are all compatible with the new AC-9.4. Note that option (b), the ast constant, reads the source rather than the emitted output. AC-9.4 allows that.

placeholder scan:
- `PRECHECK: PASS issues=0`.
- Twelve PATH advisories are kept on purpose. They name new files this feature creates (`h-mad-agy-tdd-gate.py`, `.agents/hooks.json`), a `.codex/hooks.json` in another project, and a HemaSuite archive path that is relative to `/Users/kimhawk/orca/HemaSuite`.
- `ACS: OK count=19 frs=9`.

owed by other documents:
- Plan, being revised by the concurrent plan author:
  - the census paragraph and DO-7 adopt the union sweep, with comments, `unparsed=N` and the bytes-literal residual;
  - DO-7's last sentence gets the run-time residual (review Should-fix 5);
  - stage 6, DO-7 and the Design-owed line say "carve-out text (all three sentences)";
  - the AC-9.4 test locators are per copy, never assembled-prompt or file-level;
  - the example mutation row's `find` gets copy-specific context, and the `.py` row matches the literal split.
- Design: name each copy's locator and what it does not pin. Name the assembler-copy reading: a stub template with only the `<INLINE_TASK_FROM_IMPL_PLAN>` slot, a slice of `filled`, or the joined ast constant.
- Not spec-owned and left alone:
  - Should-fix 6, the prompt pin census entries for `test_h_mad_extract_verdict.py` and `test_h_mad_portable_timeout.py`, belongs to the plan. FR-9 rewrites the prompt, so those pins are placement constraints the plan census should list.
  - The nit on FR-10 and `agy-authorship`: the plan is stricter than the spec, and this round adds no new scope.
