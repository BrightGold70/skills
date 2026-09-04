## Summary

Audited the v1.38→v1.39 delta first, then the document, against the frozen tree at `74e126f`. All
four claims the brief asked me to attack HOLD. (a) The sibling-assertion sweep is clean: the
document's own `grep -n 'owed\|spec\.md:\|design\.md:\|plan\.md:'` returns only the Conventions rule
quoting itself, changelog history, and the word "followed"; a separate modal/present-tense heuristic
(`the (spec|design|plan)('s)? (must|should|needs|carries|states|says|holds|reads|already|still|now)`)
returns only the two lines of the rule's own text. No weaker sibling-assertion survives anywhere.
(b) The refusal to state a cardinality is HONEST, not evasive: I ran the document's AST sweep
verbatim and it printed exactly 22, including `traced_bindir`, `run_with_bindir` and two `main`s
(`h_mad_audit_gate.py:305`, `h_mad_wire_pin_gate.py:350`), and it does NOT print
`test_h_mad_collect_report_docs.py:40 _section` — over-count and under-count both reproduce exactly
as written. (c) The new behavioural claim is TRUE: `run_recipe` is at
`h-mad/tests/test_h_mad_collect_report_docs.py:309`, nested inside the test at `:294`, and its
`subprocess.run(["bash", "-c", preamble + script], capture_output=True, text=True)` carries no
`timeout=`, so the hoist does ADD `timeout=60.0`. (d) Decision C's oracle reproduces on
markdown-it-py 2.2.0 CommonMark: `'## Text\t##\n'` → `<h2>Text</h2>`; both prose sites, the
docstring and both legs of the fixture carry spaces-or-tabs; the 0-in-corpus residual is TRUE (I
re-derived it portably: 30 files, 0 matches). Also re-derived and holding: all eight
`_second_surface()` call sites (`:118 :154 :225 :248 :269 :389 :409 :431`) with `:269` inside
`_gate_bash_block` (`def` at `:267`); `_titled_section` at `:69` with eight call sites `:301`–`:372`;
`SKILL.md:1606` `## Run-context ceiling — halt the run at 80%`; every `test_h_mad_portable_timeout.py`
pin (`:40 :151 :153 :154 :158-:161 :165 :211 :295`); the module-level glob AST sweep printing
`module-level 7` at the exact seven lines named and `in-body 21`; `pytest.ini:14` `testpaths`;
30/30/35/0 and `hmad:exec` = 0; the design's mutation matrix at exactly 81 data rows with exactly
one `registry`-named row; the AC-6.4 tuple at exactly 9 enumerated node IDs with no total written
for it; and the Second-surface window at 4 bash fences, exec-codex 2nd of 4 and gating 4th of 4,
1-based. Two must-fixes remain, both class-level.

Evidence: 15 files opened, 38 greps run (plus 4 AST sweeps and 2 markdown-it-py oracle runs
executed against the frozen tree).

## Must-fix
- The Single-source residual closes only the FENCE-BLIND half of its own axis; the FENCE-AWARE half is
  unswept, unnamed and unguarded, and the invariant sentence above it is therefore false as written.
  The bullet asserts that any `in_fence` toggle lives in exactly one function body, `_fence_events`;
  the residual then excuses `##`-slicers that "perform none of it", and names three, all explicitly
  fence-blind. But the complement of that set is non-empty and I enumerated it by AST over `h-mad`
  and `handoff` (function bodies holding a backtick-fence literal AND an `in_fence`/`fenced`
  toggle): `h-mad/scripts/h_mad_assemble_tdd.py:96` `_body_end` (toggle `:114`/`:118`),
  `h-mad/scripts/h_mad_precheck_doc.py:270` `scan` (`:301`/`:304`),
  `h-mad/scripts/h_mad_version_history.py:86` `section_bounds` (`:94`/`:98`),
  `h-mad/tests/test_h_mad_context_budget_docs.py:35` `_section` (`:48`/`:51`),
  `h-mad/tests/test_h_mad_hook_wiring.py:288` `_wiring_section` (`:293`/`:296`) and
  `h-mad/tests/test_h_mad_pane_visible_dispatch_docs.py:26` `_section` (`:50`/`:53`) — six live
  bodies, three of them in `h-mad/scripts/` production code, none of them `_fence_events`, and
  `test_docsections_has_no_second_bounder` is scoped to `docsections.py` so nothing guards any of
  them. This is not the same class the v1.39 repair closed: the sweep the document shipped selects
  on `'## ' in seg` plus a `find`/`index`/`split`/`startswith` call — the `##`-SLICER axis — which
  cannot see a marker-run recogniser that never slices on `## ` (`h_mad_precheck_doc.py:270` and
  `h_mad_assemble_tdd.py:96` are both absent from its 22). So the document has a rule and a sweep for
  the members that are outside its invariant, and neither for the members that are inside it.
  Prescription, closing the class rather than the instance: state the invariant's SCOPE explicitly —
  "within `h_mad_doc_block_exec.py` and `docsections.py`", which is what `scanner-duplicated-in-consumer`
  and `test_docsections_has_no_second_bounder` actually enforce — and add a second residual on the
  complementary axis, with the toggle-based AST sweep beside it, recording that N pre-existing
  hand-rolled fence-state scanners live outside that scope, that they are out of migration scope for
  this feature, and that no guard covers them. The residual to state exactly: after Task 1 the tree
  holds one authoritative scanner and N unguarded hand-rolled ones; the number is not the contract,
  the scope sentence is.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `toggle — lives in exactly one function body,`

- The document's ONLY detector for its own Conventions form (a) fires at the audited commit:
  `grep -n 'both halves of' docs/02-design/features/doc-block-exec.design.md` returns **2** hits at
  `74e126f`, not one. The site is `docs/01-plan/features/doc-block-exec.impl-plan.md:1304`, which
  annotates the locator "(one hit, verified)" with no commit stamp. I ran the locator at both
  commits: at `335f535` it returned exactly one hit (`design.md:1677`, the v1.81 changelog line); at
  `74e126f` the design's own round-four revision added `design.md:904` — "ordinal must always name
  both halves of its base" — so the needle now matches two lines. This is the FIFTH recurrence of the
  class the Conventions rule was written to close, and it is the first one inside the form the rule
  prescribes as SAFE: a locator whose needle is a common English phrase is exactly as perishable as a
  line pin, and it drifted here inside a single commit under the same concurrent-authorship axis the
  rule names. Under the document's own admissibility condition the citation is inadmissible as it
  stands. Prescription, and the class not the instance: (i) re-point this needle to
  ``both halves of `overlap:` `` — I verified it returns exactly 1 hit at `74e126f`; (ii) add to the
  Conventions rule that a locator needle must be chosen to be *lexically specific to its target row*
  (carry a backticked identifier or a verdict token), not a bare prose phrase, because the one-hit
  property is a property of the whole sibling document and not of the sentence being cited; and
  (iii) state the residual exactly — the one-hit condition is only true at the commit it was run at,
  so every locator must be re-run in the revision that ships, and I swept all thirteen distinct
  locators in this document at `74e126f`: twelve return exactly one hit, this one returns two.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `verified **in the same pass** to return exactly one hit`

## Should-fix
- AC-1.5/1.7's tab-arm residual command is not runnable on this repository's own target platform.
  It uses `grep -cP`, and `/usr/bin/grep` on macOS rejects it: `grep: invalid option -- P`, rc=2 (I
  ran the exact pipeline as written; it errors and prints nothing). The stated RESULT is correct — I
  re-derived it portably in Python over the same 30-file corpus and got 0 matches — so this is a
  broken evidence command, not a false claim. It matters here more than it would elsewhere, because
  this feature's own Task 1 inherits `_TIMEOUT_CMD`/`_ABSENCE_CLAIMS`, guards that exist precisely
  because the stock macOS toolchain is not GNU. Class, swept: I checked this document for
  GNU-vs-BSD-divergent invocations (`grep -P`, `sed -i`, `readlink -f`, `date -d`, `xargs -r`,
  `stat -c`) and found exactly two sites — `:1072`, which already writes BOTH forms
  (`stat -f %Lp .` (darwin) / `stat -c %a .` (GNU)), and `:824`, which does not. So the document
  already knows this axis and missed one member. Prescription: replace the `-P` pipeline with a
  stdlib-Python one-liner (the same shape AC-6.1 already uses for its corpus relation), or write both
  forms as `:1072` does; and state the rule that every runnable command this document ships must run
  under the stock macOS toolchain, with the residual that nothing detects a GNU-only flag in a
  document — only this sweep does.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `xargs grep -cP '^ {0,3}#{1,6}[ \t].*\t#+[ \t]*$'`

- Decision C names its class as "*both* `#`-run delimiters in ATX take spaces-or-tabs" and closes it,
  but one whitespace position on the same CommonMark axis is still written as space-only and pinned
  by a space-only fixture: the leading indentation, stated at `:317` as "0–3 leading spaces" and
  exercised at `:826` by `test_heading_lookalikes_are_not_headings` with only `    ## x` (four
  SPACES). Oracle, same version and preset as Decision C's (markdown-it-py 2.2.0, CommonMark):
  `'\t## x\n'`, `' \t## x\n'` and `'   \t## x\n'` all render `<pre><code>## x`, i.e. indented code
  and NOT a heading, while `'   ## x\n'` renders `<h2>x</h2>` — indentation is counted in COLUMNS
  with a tab advancing to the next 4-column stop, which is a different rule from "0–3 leading
  spaces". A literal implementation of the document's predicate happens to reject all three tab cases
  (the char after the spaces is `\t`, not `#`), so this is a latent divergence rather than a live
  contradiction — but nothing in the document says so, no fixture pins it, and the mutation matrix has
  no row that would notice, so a 5d implementer who reaches for `line.lstrip()` before matching the
  hash run lands a heading where CommonMark has a code block and every gate stays green. Prescription:
  state the indent rule in columns (tab = 4) or state outright that a tab-indented `##` line is not a
  heading, and add `\t## x` to the lookalike fixture beside `    ## x`; then state the residual — the
  fence opener's 0–3-space indent is the same axis and is likewise unpinned (oracle: `'\t```bash'`
  renders as code, `'   ```bash'` opens a fence), so the rule is "ATX and fence indentation are
  measured in columns", with the residual that no corpus instance exercises either arm.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `0–3 leading spaces, a run of 1–6`

## Nit
- Decision C's first prose site (`:304`–`:308`) opens a parenthesis after "the optional closing hash
  run (preceded by", then runs four lines of class argument and oracle before closing it and
  resuming "and trailing whitespace stripped" — the main clause's verb is ~60 words from its subject,
  and the sentence reads as broken on first pass. The second prose site (`:318`) and the docstring
  (`:713`) both state the same correction in one clause each. Split the oracle out into its own
  sentence after the definition.
