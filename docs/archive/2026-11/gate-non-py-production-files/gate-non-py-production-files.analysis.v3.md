# Analysis: gate-non-py-production-files

Change review — 57e4f9fc..246531ba — GATING. Phase 6 gap analysis, third measurement, at 246531ba against spec v1.15, design v1.10 and impl-plan v1.9. Files opened: 25, plus every JSON under `h-mad/tests/mutation-specs/` loaded by script (see Evidence).

## Executive Summary
AC-9.3 still does not hold at 246531ba. v2's three arms now have rows, but a census that can see unmarked code finds 16 more verdict-deciding lines with no row, and for 3 of them no test fails either. Every gate verdict the spec names still reads correctly on all three hosts, so this is a gap in the mutation record and, for the 3, in the tests. No verdict is wrong today.

## Match Rate: 91%

FR level: 10 of 11 FRs have every AC met (10/11 = 90.9, stated as 91). AC level: 54 of 55 met, 1 unmet (AC-9.3). The number is the same as v2's, but the gap under it has changed: v2's three arms closed and this census found more.

## Evidence
- read: 25 files. Spec; design; impl-plan; `inline-protocols.md`; analysis.v2; the 6 production files (`h-mad-tdd-gate.sh`, `h-mad-codex-tdd-gate.py`, `h-mad-agy-tdd-gate.py`, `h_mad_tdd_judge.py`, `h_mad_target_identity.py`, `h_mad_wire_pin_gate.py`); `h_mad_mutation_harness.py`; `non_py_gate_support.py`; `tdd_gate_support.py`; test modules `test_h_mad_tdd_gate_non_py.py`, `test_h_mad_codex_tdd_gate_non_py.py`, `test_h_mad_agy_tdd_gate_non_py.py`, `test_h_mad_codex_gate_tmp_reports.py`, `test_h_mad_codex_tdd_gate_judge.py`, `test_h_mad_tdd_gate_docs.py`, `test_h_mad_tdd_gate_differential.py`; `listing_matcher.json`, `doc_data_definition.json`, `codex_gate_judge_wiring.json`; analysis.md by grep only. Rows of the 13 feature specs were printed and read; every spec JSON was loaded by the census script for anchors.
- ran: 59 commands, all on scratch copies except reads. tests run: `test_h_mad_tdd_judge_listing.py`, `test_h_mad_tdd_gate_non_py.py`, `test_h_mad_codex_tdd_gate_non_py.py`, `test_h_mad_agy_tdd_gate_non_py.py` (baseline `239 passed`, then once per mutant, 28 mutants); `test_h_mad_codex_gate_tmp_reports.py`, `test_h_mad_doc_data.py` and the two docdata nodes (`45 passed`); 24 named nodes under the sampled rows; 41 gate-related modules on the baseline and on the three chain-read mutants combined.
- Harness: `h_mad_mutation_harness.py listing_matcher.json --isolate --python <abs> --only LV-UNREADABLE-ARM --only LV-LISTED-ARM --only L-UNREADABLE-RECORD` printed `MUTATION: ALL_CAUGHT mutations=3 caught=3 survived=0 refused=0 ... hollow_kills=0`. Whole-commit archive, committed once in a throwaway repository.
- The repository was not modified: `git status --short` printed nothing after the runs, and HEAD stayed 246531ba.
- Confirmed as asked: `git diff --name-only 57e4f9fc 246531ba -- h-mad/hooks h-mad/scripts` printed nothing. Also `git diff --name-only e524b58a 246531ba -- h-mad/hooks h-mad/scripts <fr9_drive.py>` printed nothing, and `git merge-base 246531ba origin/main` is still `e097dfcb`, so the FR-9 evidence's commit and base still stand.
- Three false starts of mine, stated so they are not read as findings. A `ls` in my setup command was aliased to `eza` and hung until I killed it. My first codex probe of the relative dangling target set no `CODEX_PROJECT_DIR`, and my second placed the root so `../e/` was also root-relative; the third copied the geometry of `test_a_relative_dangling_tmp_report_from_outside_root_is_refused` and read as the spec says. My first census matched `find` lines loosely, which attached rows such as `fr6-import-guard-dropped` to unrelated lines; the table below anchors each row by the exact span of its `find` in the file at 246531ba.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: parser records every backticked production path | 5 | 5 | Complete | carried from v2; `wp:247` has rows U1, P-NONPY, P-PYFILTER |
| FR-2: `ungated` retired | 4 | 4 | Complete | carried from v2 |
| FR-3: one listing matcher | 5 | 5 | Complete | carried from v2; AC-3.4 spot-read at head |
| FR-4: judge by the Task's tests only | 6 | 6 | Complete | carried from v2 |
| FR-5: Claude gate | 8 | 8 | Complete | carried from v2; AC-5.1, 5.2, 5.4, 5.8 spot-read at head |
| FR-6: codex gate | 5 | 5 | Complete | carried from v2; AC-6.1, 6.2, 6.3, 6.5 spot-read at head |
| FR-7: agy gate | 4 | 4 | Complete | carried from v2; description changed, all 4 ACs spot-read at head |
| FR-8: undecidable listing fails closed | 4 | 4 | Complete | carried from v2; description changed, AC-8.1, 8.3 spot-read at head |
| FR-9: end-to-end proof | 5 | 4 | Partial | Missing AC-9.3 |
| FR-10: prose | 3 | 3 | Complete | carried from v2 |
| FR-11: doc/data allowed | 6 | 6 | Complete | carried from v2; AC-11.1 spot-read at head |

## Question 1: AC-9.3 on a census that can see unmarked code

AC-9.3 has three clauses (spec:221). Clause 2 and clause 3 hold on what I sampled. Clause 1 does not.

**Clause 1, "every new guard ... has a mutation-spec entry": not met.** The full census is in §"Census". Of 158 changed lines that carry a condition, loop, return, recorded value or assignment, 60 are anchored by a row, 29 are arms of a guard that has a row, 52 are excluded (§"Exclusions"), 2 were measured and excluded, and 15 decide a verdict with no row. One of the 60, `sh:269`, has a row on only one arm, and its `"docdata no"` arm is the sixteenth item below.

The 16 were each driven on a scratch copy of 246531ba: up to 11 scenarios through the real hooks, and the four non-Python gate modules, 239 tests. The verdict columns read Claude, codex, agy with the test absent, unless the scenario says otherwise. Unmutated, the same driver reads what the spec requires.

| # | Line | Decision the line makes | Mutant | Verdict moved (expected → read) | Tests failing (of 239) | Killer a row could name |
|---|---|---|---|---|---|---|
| 1 | `judge:737` | the listing verb enters only on an active chain; same role as CX-ACTIVE, AG-ACTIVE | `elif False:` | listed `tool.sh`: Claude DENY test-missing → **ALLOW**; unreadable plan: Claude DENY judge-error → **ALLOW** | 22 | JL::test_listing_cli_listed_prints_the_encoded_target |
| 2 | `sh:269` `"docdata no"` arm | a code-like target stays on the listing path; the row H-DOCDATA-LINE anchors only the `*)` arm | `"docdata no") DOC_DATA=yes ;;` | listed, hard link, S2, unreadable plan, second plan: Claude → **ALLOW** | 37 | CL::test_claude_listed_absent_test_denies |
| 3 | `judge:341` | a target is listed if ANY plan lists it | `any` → `all` | two active plans, the second lists it: **ALLOW** on 3 hosts | 7 | JL::test_listing_listed_outranks_an_unreadable_sibling |
| 4 | `judge:335` | records the plan's matches; the sibling of L-UNREADABLE-RECORD and L-ABSENT | `tuple(matches)` → `()` | listed, hard link, S2, second plan: **ALLOW** on 3 hosts | 67 | JL::test_listing_any_canonical_name_lists_the_target |
| 5 | `judge:330` | records a match | `pass` | as row 4 | 67 | JL::test_listing_any_canonical_name_lists_the_target |
| 6 | `judge:347` | the not-listed verdict itself | return `unreadable` | unlisted and absent plan: ALLOW → DENY judge-error on 3 hosts (fail-closed direction) | 23 | JL::test_listing_not_listed_when_no_name_matches |
| 7 | `judge:732` | Claude's transport of every canonical name | first name only | hard link: Claude → **ALLOW** | 5 | CL::test_claude_hard_link_denies |
| 8 | `sh:198` | Claude's names on the verb's argv | `LARGS=(--name "$CANON_TARGET")` | hard link: Claude → **ALLOW** | 4 | CL::test_claude_hard_link_denies |
| 9 | `cx:289` | codex's names for the listing | `[Path(resolved.target)]` | hard link: codex → **ALLOW** | 4 | CX::test_codex_hard_link_denies |
| 10 | `ag:185` | agy's names for the listing | `[Path(resolved.target)]` | hard link: agy → **ALLOW** | 4 | AG::test_agy_hard_link_denies |
| 11 | `cx:303` | judges the selected name; L-SELECT and CX-SELECT mutate only the callee | `max(names, ...)` | S1 ALLOW → DENY, S2 DENY → **ALLOW**, codex only | 2 | CX::test_codex_selection_s2_denies |
| 12 | `ag:202` | same on agy | `max(names, ...)` | S1 ALLOW → DENY, S2 DENY → **ALLOW**, agy only | 2 | AG::test_agy_selection_s2_denies |
| 13 | `sh:344` | same on Claude | last canonical name | S1 ALLOW → DENY, S2 DENY → **ALLOW**, Claude only | 2 | CL::test_claude_selection_s2_denies |
| 14 | `judge:733` | Claude's chain is read for the target, per spec Terms *Active chain* | `read_chain(root, None)` | nested state: Claude DENY test-missing → **ALLOW** | **0** | **none** |
| 15 | `cx:293` | same on codex, spec:159 | `read_chain(root, None)` | nested state: codex → **ALLOW** | **0** | **none** |
| 16 | `ag:188` | same on agy | `read_chain(root, None)` | nested state: agy → **ALLOW** | **0** | **none** |

Rows 1 to 13 have the same shape as v2's Gap 1: no row, an existing test kills it. Rows 14 to 16 are worse. The driver's nested scenario removes the root state, writes `sub/docs/.bkit-memory.json` with an active record and a plan in `sub/` listing `scripts/s.sh`, then writes `sub/scripts/s.sh`. Unmutated it reads DENY test-missing on all three hosts. Mutated, the host's verdict is ALLOW and 239 of 239 pass. Across the 41 modules that name a gate, the judge or a mutation spec, the combined mutant newly fails no node: baseline `20 failed, 2348 passed, 48 errors`, mutant `19 failed, 2349 passed, 48 errors`, and the mutant's failing set is a subset of the baseline's. The orchestrator's full run passes those nodes at 246531ba, so their failure comes from my scratch repository, which I did not diagnose further. 60 of them still fail with a default temp directory, and they cannot discriminate either way. The rest of the suite was not run against these mutants. On the four modules as the spec's `command`, the harness printed `MUTATION: SURVIVED mutations=3 caught=0 survived=3`. `grep -l 'nested\|sub/docs\|subproject'` over the four modules prints nothing. The `.py` path has this property pinned: `codex_gate_judge_wiring.json` rows W5AR and W5AF anchor `judge.read_chain(root, absolute)` with the tests `test_root_step5_governs_a_subproject_with_its_own_state` and `test_codex_hook_scopes_nested_state_to_the_target_project`. So adding a row alone will not do: it would report SURVIVED until a test exists.

How firm the count is. I used v2's standard: the line decides a fail-open against a fail-closed verdict, as the rubric states. A narrower reading, conditional arms only, keeps rows 1, 2 and 3 and the clause still fails. A reading that a transport or argument line is not a guard removes rows 7 to 16 and still leaves 1 to 6. `judge:737` is the plainest: an `elif` one line above the two arms v2 reported, with the same effect when driven. Row 6 is the softest, since only its fail-closed direction exists; I keep it because L-ABSENT and LV-NONE are rows of the same kind. If the operator rules that "guard" means a marked guard, the clause closes and rows 14 to 16 remain a test gap under no AC.

Classification per step 4.5: `both`. design:613 lists the 17 rows of `listing_matcher.json` and the host specs at design:619 name the rest, and neither document argues for omitting these lines. The design states the rule these lines implement at design:374 (`judge.read_chain(root, names[0])`), so nothing has been narrowed on purpose. No code change is needed.

**Clause 2, "killed by a test that fails for the guard's own reason": met on 24 sampled rows.** I applied each row's own `find` and `replace` to a scratch copy, confirmed one landing, ran its named node, and read the `E` line. All 24 failed on the property the guard states.

| Row | Named node | Why it failed |
|---|---|---|
| LV-UNREADABLE-ARM (new) | test_listing_cli_active_unreadable_prints_unreadable | stdout `TDD-LISTING: not-listed`, expected `unreadable file=...` |
| LV-LISTED-ARM (new) | test_listing_cli_listed_prints_the_encoded_target | stdout `TDD-LISTING: not-listed`, expected `listed target=...` |
| L-UNREADABLE-RECORD (new) | test_listing_unreadable_when_no_plan_lists_the_target | `Listing(value='not-listed')`, expected unreadable with UnicodeDecodeError |
| L-UNREADABLE | same node | same |
| L-LISTED | test_listing_listed_outranks_an_unreadable_sibling | reads unreadable where a readable plan lists it |
| L-ABSENT | test_listing_absent_plan_is_not_listed | an absent plan read as unreadable |
| LV-RC | test_listing_cli_internal_exception_exits_2 | `assert 0 == 2` |
| H-LIST-UNREADABLE | test_claude_unreadable_plan_is_judge_error | reason lacks `listing is undecidable`; verdict stays DENY through the fall-through refusal |
| H-DOCDATA-LINE | test_claude_malformed_docdata_line_is_judge_error | `allow`, expected DENY judge-error |
| H-LIST-CONTEXT | test_claude_selection_s2_denies | reason lacks `scripts/hard.sh` |
| H-NOT-LISTED | test_claude_unlisted_code_like_allows | DENY judge-error, expected ALLOW |
| H-CODE-LIKE | test_claude_listed_absent_test_denies | `no-test-resolved`, expected `test-missing` |
| CX-ACTIVE | test_codex_listed_absent_test_denies | `allow`, expected DENY |
| CX-NOT-CODE-LIKE | test_codex_listed_test_shaped_python_is_skipped | DENY test-missing, expected ALLOW |
| CX-LIST-UNREADABLE | test_codex_unreadable_plan_is_judge_error | reason is the generic `TypeError` refusal, expected `listing is undecidable` |
| AG-LIST-UNREADABLE | test_agy_unreadable_plan_is_judge_error | generic refusal, expected `Listing is undecidable` |
| AG-ACTIVE | test_agy_listed_absent_test_denies | `allow`, expected DENY |
| DD-CX-MD | test_codex_doc_data_member_allows[.md] | DENY test-missing, expected ALLOW |
| DD-EXEMPT-DOCS | test_is_exempt_location_matches_is_production_python[docs] | the exemption disagrees with `_is_production_python` for `docs/m.py` |
| P-PYFILTER | test_python_only_production_line_keeps_items_and_order | 3 extra items |
| K-IMPORT-NONPY | test_non_py_module_not_found_scores_pytest_error | `red-measured`, expected `pytest-error` |
| G-PY-NAME | test_codex_dot_py_unlisted_denies[scripts/.py] | `allow`, expected DENY no-test-resolved |
| W7R | test_claude_listed_absent_test_denies | `allow`, expected DENY |
| U2 | test_an_extensionless_production_path_is_collected_in_production | `[]`, expected the path |

Three rows (H-LIST-UNREADABLE, CX-LIST-UNREADABLE, AG-LIST-UNREADABLE) are killed on the reason only, because a second layer still refuses. That is the guard's own reason and the verdict stays fail-closed, so I read them as met.

**Clause 3, "scored on the pytest summary, not on `$?`": met.** `h_mad_mutation_harness.py:489` `outcome()` reads the summary, and its docstring states that a kill requires the test to have run and failed. The harness printed `killed by its named test` for the three new rows.

### Exclusions
- *Formats or names:* `judge:736`, `:740`, `:742`, `cx:305`, `ag:190`, `:197`, `:204`, `:205`. They build a message from a decision already made.
- *Parses:* `sh:200`, `:267`, `:280`, `:281`. They split or match; the next guard decides, and an unparsed value reaches a refusal.
- *Containers, setup, dispatch:* `judge:312`, `:323`, `:336`, `:682`, `:730`, `:738`, `:747`, `cx:292`, `cx:352`, `sh:196`, `:342`, `:345`, `:346`, `id:20`. `judge:738` passes the names of row 7 and the chain's records, so it has no separate decision.
- *`judge:351-376`, the body of `resolve`.* The diff shows it as added, but it is the old body re-homed on `_match_plans`. Two of its new conditions were measured: `if found.status == "unreadable":` and `if found.status == "absent":` → `if False:` moved no verdict and failed 0 of 239, because they only choose a note. `for task, base in found.matches:` → `in ()` moved every listed row to DENY no-test-resolved with 71 failures, so it has only a fail-closed direction, and I do not count it.
- *Measured, not counted:* `sh:204` → `if false`: the verdict stays DENY judge-error and only the reason moves, 4 tests fail. `sh:208` → `if false`: listed targets read DENY judge-error on Claude and never ALLOW, 23 tests fail. `sh:269` `"docdata yes"` arm → `DOC_DATA=no`: listed doc/data reads DENY test-missing on Claude, which is the fail-closed direction the row H-DOCDATA already mutates, 17 tests fail.
- *A weaker form of rows 11 to 13:* judging `Path(resolved.target)` or `$CANON_TARGET` instead of the selection moved only the hard-link scenario, to DENY no-test-resolved, because the canonical target is already the least name in the fixture. So I drove the `max` form, which flips S1 and S2.
- *Arms:* the `return`, `continue` and deny lines under a guard that has a row. The table names the row. `judge:344` and `:346` are the same decision as L-UNREADABLE: their mutants move the unreadable-plan scenario to ALLOW on 3 hosts and fail 8 tests.

## Question 2: staleness, and v2's items

**AC readings.** No AC bullet changed in this range: the spec diff touches the Terms, FR-7's description, FR-8's closing sentence, the Security NFR, resolved question (d), Out-of-Scope and Version History, and no `AC-` line. `test_claude_missing_docdata_line_is_judge_error` was the only test renamed, and v2's AC table cites it for no AC. So only AC-9.3's reading moves.

**Spec v1.15, executed.** Hooks ran under `python3` 3.15.2, the fixture from `non_py_gate_support.py`, with the same runners on 246531ba and 3489f86b (the two support modules copied into the older tree, as the plan describes). `git diff e097dfcb 3489f86b -- h-mad/hooks h-mad/scripts` is empty, so the older reading also stands for the merge base. Every reading matches the spec and design. No row moved DENY to ALLOW.

| Case, test absent | Claude | codex | agy | codex, agy at 3489f86b |
|---|---|---|---|---|
| In root: `.py`, `.PY`, `scripts/.py`, `src/docs/.py`, `scripts/..py`, `scripts/...py`, absent `scripts/.Py`, `scripts/x.sh` hard-linked to `scripts/.py` | DENY no-test-resolved | same | same | ALLOW, ALLOW |
| Exempt: `tests/.py`, `docs/.py` | ALLOW | ALLOW | ALLOW | no move |
| `/tmp`: `.py`, absent `.py`, `hl2.md` linked to `.py`, `a.txt` linked to `.Py` | DENY no-test-resolved | DENY, no `kind=` | DENY target-outside-root | ALLOW, ALLOW |
| `/tmp`: `hl.txt` linked to `x.py` | DENY no-test-resolved | DENY, no `kind=` | DENY target-outside-root | ALLOW, DENY (agy already refused) |
| agy artifact directory: `.py`, `.PY` | not driven | n/a | DENY target-outside-root | n/a, ALLOW |
| agy artifact directory control: `note.txt` ALLOW, `x.py` DENY | not driven | n/a | as stated | n/a, same |
| codex, relative `../e/n.txt` (dangling) and a looped link, payload `cwd` outside the root | not driven | "outside or unreadable" | n/a | ALLOW, n/a |
| Controls under `/tmp`: `note.txt`, absent `new.txt`, absent `nope/report.md`, absent `a/b/c/report.md` | ALLOW | ALLOW | ALLOW | no move |
| Same-directory residual: `scripts/tool.sh` linked to `test_t.py`, `t_test.py`, `conftest.py`, `test_.py`, `conftest_x.py`, `test_t.PY`, `t_test.PY` | DENY no-test-resolved | **ALLOW** | **ALLOW** | no move |
| Same, test failing and test passing (`test_t.py`, `t_test.py`, `conftest.py`), and a write through the link's own name `scripts/test_t.py` in all three states | DENY no-test-resolved | **ALLOW** | **ALLOW** | no move |
| Control: linked to `scripts/t.py` | DENY no-test-resolved | same | same | no move |
| Control: linked to `other/test_t.py`; no link | DENY test-missing | same | same | ALLOW, ALLOW |
| Cross-directory residual, `/tmp`: `note.txt` linked to `elsewhere/x.py` and `elsewhere/.py`, `note.md` linked to `elsewhere/x.py` | **ALLOW** | **ALLOW** | **ALLOW** | no move |

The design's guard attribution also holds. With `# M:CX-NOT-CODE-LIKE` replaced by `if False:`, codex reads DENY test-missing for `test_t.py`, `t_test.py` and `conftest.py` while agy stays ALLOW; with `# M:AG-NOT-CODE-LIKE` replaced, the reverse. The `t.py` and no-link rows do not move. A `git grep` for `os.link`, `hardlink_to` and `.link_to` under `h-mad/tests/` finds one test-shaped link target, `test_h_mad_tdd_gate_differential.py:182`, paired with `prod.py`, which agrees with the design's "No test drives it". I did not separately drive the spec's per-commit statement about `b0ebb116` and `e524b58a` in §(d), since the rows it names read correctly at head.

**The ledger.** `listing_matcher.json` holds 17 rows: 11 judge-level and 6 host, as design:613 says. The 10 feature specs sum to 105, as plan:1311 says. The remaining `102`s in the plan are dated history or say "departure 15 later takes it to 105". The old test name survives only in version-history and analysis prose that names the rename.

**v2's items.**

| v2 item | Status | Evidence |
|---|---|---|
| Must-fix: AC-9.3, three arms without a row | **closed for the three, moved for the AC** | `LV-UNREADABLE-ARM`, `LV-LISTED-ARM`, `L-UNREADABLE-RECORD` in `listing_matcher.json`; harness `ALL_CAUGHT mutations=3`. AC-9.3 remains unmet on the 16 above |
| SF 1: three spec sentences false | closed | spec:172 now states `outside_allowed` moved; spec:293 lists the refusals; §(d) states what changed. All executed above |
| SF 2: listed `.sh` with a `test_*.py` link splits the hosts | moved: closed as an unnamed residual, open as behaviour by operator decision | Out-of-Scope and design §"The name test" name it; the decision is dated 2026-11-06; readings above match |
| SF 3: `test_claude_missing_docdata_line_is_judge_error` passes through another guard | closed | Renamed `test_claude_empty_docdata_output_is_a_canon_field_count_mismatch`; asserts `CANON field count mismatch`; node passes on the archive |
| SF 4, `unverified`: primary record of the ninth-refusal ruling | open | `grep -n 'plan-absent\|absent at the base\|ninth\|nine refusals'` on the spec prints nothing; plan:29 is still the only statement |
| Nit 1: codex `kind=` token after a path | open | production unchanged |
| Nit 2: `sh:2` and `test_hook_line_names_both_gates` | open | `sh:2` reads `gate for production Python writes`; DOC:71 keeps the name |
| Nit 3: two spellings of the `.py` rule | open | `cx:287`, `ag:183`, `judge:492` keep `Path.suffix` |
| Nit 4: M5 reach figures | open | not re-derived; no AC names them |

## Census

Every line of `git diff 3489f86b..246531ba` under `h-mad/hooks` and `h-mad/scripts` that carries a decision form: AST for Python, reading plus a pattern pass for the shell hook. "Row(s)" means a row's `find` covers that line at 246531ba. Code abbreviations are v2's: `sh`, `cx`, `ag`, `judge`, `id`, `wp`. `wp`'s deletions are retired code, not guards.

| Line | Kind | FR | Row(s) | Classification | Text |
|---|---|---|---|---|---|
| `wp:247` | comp-if,extend | FR-1 | P-NONPY, P-PYFILTER, U1 | guard, row | `current["production"].extend(token for token in _NON_PY_PATH_RE.findall(paths.group("val` |
| `id:19` | assign | FR-11 | DD-CX/AG/CL-<suffix> (27) | guard, row | `DOC_DATA_SUFFIXES = (".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst", ".cfg", "` |
| `id:20` | assign | FR-11 | - | excluded: table used by DD-CASE | `_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")` |
| `id:34` | any,return | FR-11 | DD-CASE, DD-SUFFIX | guard, row | `return any(name[-len(s):].translate(_ASCII_LOWER) == s for s in DOC_DATA_SUFFIXES)  # M:` |
| `id:38` | all,return | FR-11 | DD-ALL | guard, row | `return all(has_doc_data_suffix(n) for n in names)  # M:G-DOCDATA-ALL` |
| `id:42` | assign | FR-11 | DD-EXEMPT-PARENT | guard, row | `parents = Path(relative).parts[:-1]  # M:G-EXEMPT-PARENT` |
| `id:43` | if | FR-11 | DD-EXEMPT-DOCS | guard, row | `if parents[:1] == ("docs",):  # M:G-EXEMPT-DOCS` |
| `id:44` | return | FR-11 | - | arm of DD-EXEMPT-DOCS | `return True` |
| `id:45` | return | FR-11 | DD-EXEMPT-DIRS | guard, row | `return "tests" in parents or "fixtures" in parents  # M:G-EXEMPT-DIRS` |
| `id:49` | ifexp | FR-11 | DD-EMIT | guard, row | `print("docdata yes" if is_doc_data(identity.names) else "docdata no")  # M:G-DOCDATA-EMI` |
| `id:358` | if | FR-11 | G-PY-NAME | guard, row | `if not name.endswith(".py"):  # M:G-PY-NAME` |
| `judge:312` | assign | FR-3/FR-4/FR-8 | - | excluded: container | `result = []` |
| `judge:317` | PlanMatch,append | FR-3/FR-4/FR-8 | L-ABSENT | guard, row | `result.append(PlanMatch(plan, "absent", "", ()))  # M:L-ABSENT` |
| `judge:320` | PlanMatch,append | FR-3/FR-4/FR-8 | L-UNREADABLE-RECORD | guard, row | `result.append(PlanMatch(plan, "unreadable", type(exc).__name__, ()))` |
| `judge:323` | assign | FR-3/FR-4/FR-8 | - | excluded: container | `matches = []` |
| `judge:330` | append | FR-3/FR-4/FR-8 | - | **guard, NO ROW** | `matches.append((task, base))` |
| `judge:335` | PlanMatch,append | FR-3/FR-4/FR-8 | - | **guard, NO ROW** | `result.append(PlanMatch(plan, "read", "", tuple(matches)))` |
| `judge:336` | return | FR-3/FR-4/FR-8 | - | excluded: returns the container | `return tuple(result)` |
| `judge:340` | _match_plans,assign | FR-3/FR-4/FR-8 | AG-CALLEE, CL-CALLEE, CX-CALLEE, L-ANY-NAME | guard, row | `per_name = [(name, _match_plans(root, name, records)) for name in names]` |
| `judge:341` | any,assign,comp-if | FR-3/FR-4/FR-8 | - | **guard, NO ROW** | `listed = [name for name, plans in per_name if any(m.matches for m in plans)]` |
| `judge:342` | if | FR-3/FR-4/FR-8 | L-LISTED | guard, row | `if listed:  # M:L-LISTED` |
| `judge:343` | Listing,min,return | FR-3/FR-4/FR-8 | AG-SELECT, CL-SELECT, CX-SELECT, L-SELECT | guard, row | `return Listing("listed", min(listed, key=lambda p: p.name), None, "")  # M:L-SELECT` |
| `judge:344` | assign,comp-if,next | FR-3/FR-4/FR-8 | - | same decision as L-UNREADABLE: mutant gives the same verdict moves | `bad = next((m for _, plans in per_name for m in plans if m.status == "unreadable"), None` |
| `judge:345` | if | FR-3/FR-4/FR-8 | L-UNREADABLE | guard, row | `if bad:  # M:L-UNREADABLE` |
| `judge:346` | Listing,return | FR-3/FR-4/FR-8 | - | same decision as L-UNREADABLE: mutant gives the same verdict moves | `return Listing("unreadable", None, bad.plan, bad.error)` |
| `judge:347` | Listing,return | FR-3/FR-4/FR-8 | - | **guard, NO ROW** | `return Listing("not-listed", None, None, "")` |
| `judge:351` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `real_root = Path(os.path.realpath(root))` |
| `judge:352` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `real_target = Path(os.path.realpath(target))` |
| `judge:353` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `notes = []` |
| `judge:354` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `candidates = []` |
| `judge:355` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `seen_candidates = set()` |
| `judge:356` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `matched = False` |
| `judge:357` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `declared_budget = None` |
| `judge:358` | _match_plans,loop | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `for found in _match_plans(root, target, records):` |
| `judge:359` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `plan = found.plan` |
| `judge:360` | if | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `if found.status == "absent":` |
| `judge:361` | append | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `notes.append(f"{plan}: absent")` |
| `judge:362` | continue | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `continue` |
| `judge:363` | if | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `if found.status == "unreadable":` |
| `judge:364` | append | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `notes.append(f"{plan}: impl-plan unreadable: {found.error}")` |
| `judge:365` | continue | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `continue` |
| `judge:366` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `plan_matched = False` |
| `judge:367` | loop | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `for task, base in found.matches:` |
| `judge:368` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `matched = plan_matched = True` |
| `judge:369` | if | FR-3/FR-4/FR-8 | declared-budget-not-read | excluded: moved from the old `resolve`, not new (see §Exclusions) | `if task.get("judge_budget") is not None:  # M:J-BUDGET-READ` |
| `judge:370` | assign,max | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `declared_budget = max(declared_budget or 0, task["judge_budget"])` |
| `judge:371` | loop | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `for entry in task["tests"]:` |
| `judge:372` | assign | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `candidate = Path(os.path.realpath(base / entry))` |
| `judge:373` | if | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `if not _inside(str(candidate), str(real_root)):` |
| `judge:374` | append | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `notes.append(f"candidate outside root dropped: {entry}")` |
| `judge:375` | if | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `elif candidate not in seen_candidates:` |
| `judge:376` | append | FR-3/FR-4/FR-8 | - | excluded: moved from the old `resolve`, not new (see §Exclusions) | `candidates.append((candidate, base))` |
| `judge:492` | if | FR-3/FR-4/FR-8 | K-IMPORT-NONPY | guard, row | `if Path(fold_py_suffix(target.name)).suffix != ".py":  # M:K-IMPORT-NONPY` |
| `judge:493` | return | FR-3/FR-4/FR-8 | - | arm of K-IMPORT-NONPY | `return frozenset()` |
| `judge:682` | assign | FR-3/FR-4/FR-8 | - | excluded: argparse | `listing_command = commands.add_parser("listing")` |
| `judge:730` | if | FR-3/FR-4/FR-8 | - | excluded: verb dispatch | `if args.command == "listing":` |
| `judge:732` | assign | FR-3/FR-4/FR-8 | - | **guard, NO ROW** | `names = [root / name for name in args.name]` |
| `judge:733` | assign,read_chain | FR-3/FR-4/FR-8 | - | **guard, NO ROW, NO TEST** | `chain = read_chain(root, names[0])` |
| `judge:734` | assign | FR-3/FR-4/FR-8 | LV-NONE | guard, row | `line = "not-listed"  # M:LV-NONE` |
| `judge:735` | if | FR-3/FR-4/FR-8 | LV-CHAIN-UNREADABLE | guard, row | `if chain.value == "unreadable":  # M:LV-CHAIN-UNREADABLE` |
| `judge:736` | assign | FR-3/FR-4/FR-8 | - | excluded: formats the line | `line = f"unreadable file={_enc(str(chain.error_file))} error={chain.error}"` |
| `judge:737` | if | FR-3/FR-4/FR-8 | - | **guard, NO ROW** | `elif chain.value == "active":` |
| `judge:738` | assign,listing | FR-3/FR-4/FR-8 | - | excluded: call with the names of judge:732 | `result = listing(root, names, chain.records)` |
| `judge:739` | if | FR-3/FR-4/FR-8 | LV-LISTED-ARM | guard, row | `if result.value == "listed":` |
| `judge:740` | assign | FR-3/FR-4/FR-8 | - | excluded: formats the line | `line = f"listed target={_enc(str(result.selected))}"` |
| `judge:741` | if | FR-3/FR-4/FR-8 | LV-UNREADABLE-ARM | guard, row | `elif result.value == "unreadable":` |
| `judge:742` | assign | FR-3/FR-4/FR-8 | - | excluded: formats the line | `line = f"unreadable file={_enc(str(result.error_file))} error={result.error}"` |
| `judge:743` | except | FR-3/FR-4/FR-8 | - | arm of LV-RC | `except Exception as exc:` |
| `judge:745` | return | FR-3/FR-4/FR-8 | LV-RC | guard, row | `return 2  # M:LV-RC` |
| `judge:747` | return | FR-3/FR-4/FR-8 | - | excluded: exit after print | `return 0` |
| `cx:213` | assign | FR-6/FR-8 | CX-TMP-RELATIVE | guard, row | `canonical = _load_identity().canonicalise(str(root), str(path))` |
| `cx:214` | if | FR-6/FR-8 | CX-TMP-PY-UNRESOLVABLE | guard, row | `if canonical.unresolvable:` |
| `cx:215` | return | FR-6/FR-8 | CX-TMP-PY-UNRESOLVABLE | guard, row | `return False  # M:CX-TMP-PY-UNRESOLVABLE` |
| `cx:216` | any,if | FR-6/FR-8 | CX-TMP-PY-ALLNAMES, CX-TMP-PY-NAME, python-under-tmp-admitted, the-name-check-reads-the-link-not-its-target | guard, row | `if any(_load_identity().fold_py_suffix(name).endswith(".py") for name in (Path(canonical` |
| `cx:218` | return | FR-6/FR-8 | any-out-of-root-path-admitted, tmp-reports-refused-again | guard, row | `return _path_within(canonical.target, Path("/tmp"))  # M:G-TMP` |
| `cx:287` | any,if | FR-6/FR-8 | CX-NOT-CODE-LIKE | guard, row | `if any(Path(fold_py_suffix(n)).suffix == ".py" for n in resolved.names):  # M:CX-NOT-COD` |
| `cx:288` | return | FR-6/FR-8 | - | arm of CX-NOT-CODE-LIKE | `return ""` |
| `cx:289` | assign | FR-6/FR-8 | - | **guard, NO ROW** | `names = [Path(resolved.target).parent / n for n in resolved.names]` |
| `cx:290` | if | FR-6/FR-8 | CX-LIST-EXEMPT | guard, row | `if _is_exempt_location(names[0].relative_to(root).as_posix()):  # M:CX-LIST-EXEMPT` |
| `cx:291` | return | FR-6/FR-8 | - | arm of CX-LIST-EXEMPT | `return ""` |
| `cx:292` | assign | FR-6/FR-8 | - | excluded: loader | `judge = _load_judge()` |
| `cx:293` | assign,read_chain | FR-6/FR-8 | - | **guard, NO ROW, NO TEST** | `chain = judge.read_chain(root, names[0])` |
| `cx:294` | if | FR-6/FR-8 | CX-CHAIN-UNREADABLE | guard, row | `if chain.value == "unreadable":  # M:CX-CHAIN-UNREADABLE` |
| `cx:295` | return | FR-6/FR-8 | - | arm of CX-CHAIN-UNREADABLE | `return f"H-MAD state governing this write is unreadable ({chain.error_file}: {chain.erro` |
| `cx:296` | if | FR-6/FR-8 | CX-ACTIVE | guard, row | `if chain.value != "active":  # M:CX-ACTIVE` |
| `cx:297` | return | FR-6/FR-8 | - | arm of CX-ACTIVE | `return ""` |
| `cx:298` | assign,listing | FR-6/FR-8 | CX-FORCE, CX-REMOVE | guard, row | `listed = judge.listing(root, names, chain.records)  # M:CX-LIST` |
| `cx:299` | if | FR-6/FR-8 | CX-LIST-UNREADABLE | guard, row | `if listed.value == "unreadable":  # M:CX-LIST-UNREADABLE` |
| `cx:300` | return | FR-6/FR-8 | - | arm of CX-LIST-UNREADABLE | `return f"H-MAD Phase 5 listing is undecidable ({listed.error_file}: {listed.error}); ref` |
| `cx:301` | if | FR-6/FR-8 | CX-NOT-LISTED | guard, row | `if listed.value == "not-listed":  # M:CX-NOT-LISTED` |
| `cx:302` | return | FR-6/FR-8 | - | arm of CX-NOT-LISTED | `return ""` |
| `cx:303` | assign,judge | FR-6/FR-8 | - | **guard, NO ROW** | `verdict = judge.judge(root, listed.selected, chain.records)` |
| `cx:304` | if | FR-6/FR-8 | CX-VERDICT | guard, row | `if verdict.decision != "ALLOW":  # M:CX-VERDICT` |
| `cx:305` | assign | FR-6/FR-8 | - | excluded: formats the reason | `relative = listed.selected.relative_to(root).as_posix()` |
| `cx:306` | return | FR-6/FR-8 | - | arm of CX-VERDICT | `return f"H-MAD Phase 5 requires a failing test before {relative}: kind={verdict.kind}; {` |
| `cx:307` | return | FR-6/FR-8 | - | arm of CX-VERDICT | `return ""` |
| `cx:352` | if | FR-6/FR-8 | - | excluded: signature change, the guard is inside `_tmp_report_target` | `if _tmp_report_target(root, raw, payload.get("cwd")):` |
| `cx:363` | if | FR-6/FR-8 | CX-DOCDATA-DIRECTORY, CX-DOCDATA-VERDICT | guard, row | `if is_doc_data(resolved.names):  # M:CX-DOCDATA` |
| `cx:364` | continue | FR-6/FR-8 | - | arm of CX-DOCDATA-VERDICT | `continue` |
| `cx:372` | assign | FR-6/FR-8 | - | arm of CX-DENY | `reason = _judge_listed(root, resolved)` |
| `cx:373` | if | FR-6/FR-8 | CX-DENY | guard, row | `if reason:  # M:CX-DENY` |
| `cx:374` | return | FR-6/FR-8 | - | arm of CX-DENY | `return _deny(reason)` |
| `ag:161` | any | FR-7/FR-8 | AG-TMP-PY-NAME, fr4-artifact-py-refusal-dropped, fr4-t3-after-t5 | guard, row | `not any(identity.fold_py_suffix(name).endswith(".py") for name in resolved.names)  # M:A` |
| `ag:174` | if | FR-7/FR-8 | AG-DOCDATA | guard, row | `if identity.is_doc_data(resolved.names):  # M:AG-DOCDATA` |
| `ag:175` | continue | FR-7/FR-8 | - | arm of AG-DOCDATA | `continue` |
| `ag:183` | any,if | FR-7/FR-8 | AG-NOT-CODE-LIKE | guard, row | `if any(Path(identity.fold_py_suffix(n)).suffix == ".py" for n in resolved.names):  # M:A` |
| `ag:184` | continue | FR-7/FR-8 | - | arm of AG-NOT-CODE-LIKE | `continue` |
| `ag:185` | assign | FR-7/FR-8 | - | **guard, NO ROW** | `names = [Path(resolved.target).parent / n for n in resolved.names]` |
| `ag:186` | if | FR-7/FR-8 | AG-LIST-EXEMPT | guard, row | `if _is_exempt_location(names[0].relative_to(root).as_posix()):  # M:AG-LIST-EXEMPT` |
| `ag:187` | continue | FR-7/FR-8 | - | arm of AG-LIST-EXEMPT | `continue` |
| `ag:188` | assign,read_chain | FR-7/FR-8 | - | **guard, NO ROW, NO TEST** | `chain = judge.read_chain(root, names[0])` |
| `ag:189` | if | FR-7/FR-8 | AG-CHAIN-UNREADABLE | guard, row | `if chain.value == "unreadable":  # M:AG-CHAIN-UNREADABLE` |
| `ag:190` | assign | FR-7/FR-8 | - | excluded: formats the reason | `detail = f"{chain.error_file}: {chain.error}".replace("kind=", "kind:")` |
| `ag:191` | assign | FR-7/FR-8 | - | arm of AG-CHAIN-UNREADABLE | `decision = {"decision": "deny", "reason": f"State governing the write is unreadable ({de` |
| `ag:192` | return | FR-7/FR-8 | - | arm of AG-CHAIN-UNREADABLE | `return 0` |
| `ag:193` | if | FR-7/FR-8 | AG-ACTIVE | guard, row | `if chain.value != "active":  # M:AG-ACTIVE` |
| `ag:194` | continue | FR-7/FR-8 | - | arm of AG-ACTIVE | `continue` |
| `ag:195` | assign,listing | FR-7/FR-8 | AG-FORCE, AG-REMOVE | guard, row | `listed = judge.listing(root, names, chain.records)  # M:AG-LIST` |
| `ag:196` | if | FR-7/FR-8 | AG-LIST-UNREADABLE | guard, row | `if listed.value == "unreadable":  # M:AG-LIST-UNREADABLE` |
| `ag:197` | assign | FR-7/FR-8 | - | excluded: formats the reason | `detail = f"{listed.error_file}: {listed.error}".replace("kind=", "kind:")` |
| `ag:198` | assign | FR-7/FR-8 | - | arm of AG-LIST-UNREADABLE | `decision = {"decision": "deny", "reason": f"Listing is undecidable ({detail}). kind=judg` |
| `ag:199` | return | FR-7/FR-8 | - | arm of AG-LIST-UNREADABLE | `return 0` |
| `ag:200` | if | FR-7/FR-8 | AG-NOT-LISTED | guard, row | `if listed.value == "not-listed":  # M:AG-NOT-LISTED` |
| `ag:201` | continue | FR-7/FR-8 | - | arm of AG-NOT-LISTED | `continue` |
| `ag:202` | assign,judge | FR-7/FR-8 | - | **guard, NO ROW** | `verdict = judge.judge(root, listed.selected, chain.records)` |
| `ag:203` | if | FR-7/FR-8 | AG-VERDICT | guard, row | `if verdict.decision != "ALLOW":  # M:AG-VERDICT` |
| `ag:204` | assign | FR-7/FR-8 | - | excluded: formats the reason | `relative = listed.selected.relative_to(root).as_posix()` |
| `ag:205` | assign | FR-7/FR-8 | - | excluded: formats the reason | `detail = f"{relative}: {verdict.reason}".replace("kind=", "kind:")` |
| `ag:206` | assign | FR-7/FR-8 | - | arm of AG-VERDICT | `decision = {"decision": "deny", "reason": f"Phase 5 requires a failing test before {deta` |
| `ag:207` | return | FR-7/FR-8 | - | arm of AG-VERDICT | `return 0` |
| `sh:196` | call | FR-5/FR-8/FR-11 | - | excluded: function header | `_read_listing() {` |
| `sh:198` | kw | FR-5/FR-8/FR-11 | - | **guard, NO ROW** | `for name in "${CANON_NAMES[@]}"; do LARGS[${#LARGS[@]}]=--name; LARGS[${#LARGS[@]}]=${CA` |
| `sh:199` | assign | FR-5/FR-8/FR-11 | W7F, W7R | guard, row | `LOUT=$(python3 "$JUDGE" listing --root "$ROOT_ABS" ${LARGS[@]+"${LARGS[@]}"} 2>/dev/null` |
| `sh:200` | assign | FR-5/FR-8/FR-11 | - | excluded: parses rc from output; H-LIST-RC decides | `LRC=${LOUT##*rc=}; LOUT=${LOUT%rc=*}; LOUT=${LOUT%$'\n'}` |
| `sh:201` | case,verdict | FR-5/FR-8/FR-11 | H-LIST-LINES | guard, row | `case "$LOUT" in *$'\n'*\|"") _refuse judge-error "listing verb printed zero or several li` |
| `sh:202` | [,verdict,// | FR-5/FR-8/FR-11 | H-LIST-RC | guard, row | `[ "$LRC" = 0 ] \|\| _refuse judge-error "listing verb exited rc=$LRC"  # M:H-LIST-RC` |
| `sh:203` | [,kw,verdict | FR-5/FR-8/FR-11 | H-NOT-LISTED | guard, row | `if [ "$LOUT" = 'TDD-LISTING: not-listed' ]; then _allow; fi  # M:H-NOT-LISTED` |
| `sh:204` | [[,kw | FR-5/FR-8/FR-11 | - | measured, excluded: `SH204` moves the reason only, verdict stays DENY judge-error | `if [[ $LOUT =~ $LISTING_UNREADABLE_RE ]]; then` |
| `sh:206` | verdict | FR-5/FR-8/FR-11 | H-LIST-UNREADABLE | guard, row | `_refuse judge-error "listing is undecidable ($file: ${BASH_REMATCH[2]})"  # M:H-LIST-UNR` |
| `sh:208` | [[,kw | FR-5/FR-8/FR-11 | - | measured, excluded: `SH208` fails closed only, never ALLOW | `if [[ $LOUT =~ $LISTING_LISTED_RE ]]; then` |
| `sh:210` | kw | FR-5/FR-8/FR-11 | - | arm of H-LIST-NAME | `for name in "${CANON_NAMES[@]}"; do` |
| `sh:211` | [,kw,verdict | FR-5/FR-8/FR-11 | - | arm of H-LIST-NAME | `if [ "$LISTED_TARGET" = "${CANON_TARGET%/*}/$name" ]; then return 0; fi` |
| `sh:213` | verdict | FR-5/FR-8/FR-11 | H-LIST-NAME | guard, row | `_refuse judge-error "listing verb named a target it was not given"  # M:H-LIST-NAME` |
| `sh:215` | verdict | FR-5/FR-8/FR-11 | H-LIST-UNRECOGNISED | guard, row | `_refuse judge-error "listing verb printed no well-formed listing line"  # M:H-LIST-UNREC` |
| `sh:266` | assign | FR-5/FR-8/FR-11 | CG-CANON, H11 | guard, row | `CANON_RECORD=$(python3 -c 'import os,sys;sys.path.insert(0,os.path.join(os.path.dirname(` |
| `sh:267` | assign | FR-5/FR-8/FR-11 | - | excluded: splits the record | `DOC_DATA_LINE=${CANON_RECORD##*$'\n'}; CANON_RECORD=${CANON_RECORD%$'\n'*}` |
| `sh:269` | case,verdict | FR-5/FR-8/FR-11 | H-DOCDATA-LINE | guard, row on the `*)` arm only; **the `"docdata no"` arm has NO ROW** | `case "$DOC_DATA_LINE" in "docdata yes") DOC_DATA=yes ;; "docdata no") DOC_DATA=no ;; *) ` |
| `sh:280` | assign | FR-5/FR-8/FR-11 | - | excluded: parse pattern | `LISTING_UNREADABLE_RE='^TDD-LISTING: unreadable file=([^ ]+) error=([A-Za-z_-][A-Za-z0-9` |
| `sh:281` | assign | FR-5/FR-8/FR-11 | - | excluded: parse pattern | `LISTING_LISTED_RE='^TDD-LISTING: listed target=([^ ]+)$'` |
| `sh:328` | &&,[,verdict | FR-5/FR-8/FR-11 | H-DOCDATA | guard, row | `[ "$DOC_DATA" = yes ] && _allow  # M:H-DOCDATA` |
| `sh:340` | [,kw | FR-5/FR-8/FR-11 | H-CODE-LIKE | guard, row | `if [ "$ALL_NON_PY" = yes ]; then  # M:H-CODE-LIKE` |
| `sh:341` | [,verdict,// | FR-5/FR-8/FR-11 | H-LIST-INROOT | guard, row | `[ "$IN_ROOT" = yes ] \|\| _allow  # M:H-LIST-INROOT` |
| `sh:342` | call | FR-5/FR-8/FR-11 | - | excluded: setup; absent judge refuses through H-LIST-RC | `_find_judge` |
| `sh:343` | call | FR-5/FR-8/FR-11 | CL-FORCE, CL-REMOVE | guard, row | `_read_listing  # M:H-LIST` |
| `sh:344` | assign | FR-5/FR-8/FR-11 | - | **guard, NO ROW** | `TARGET_PATH=$LISTED_TARGET` |
| `sh:345` | kw | FR-5/FR-8/FR-11 | - | excluded: `else` of H-CODE-LIKE | `else` |
| `sh:346` | assign | FR-5/FR-8/FR-11 | - | excluded: existing assignment re-indented | `TARGET_PATH=$PRODUCTION_TARGET` |
| `sh:406` | &&,[,[[,kw,verdict | FR-5/FR-8/FR-11 | H-LIST-CONTEXT | guard, row | `if [[ $JOUT =~ $JUDGE_DENY_RE ]] && [ "$ALL_NON_PY" = yes ]; then _refuse "${BASH_REMATC` |

## Acceptance Criteria

Re-read at 246531ba: AC-9.3 only, because it is the only AC whose reading the range touches. 16 more rows were also spot-read by the driver, and the Basis column names them; their verdicts match. All other rows are carried from v2 at 57e4f9fc, unread here. Test and code abbreviations are v2's: CL, CX, AG, JL, PT, PP, WP, DD, DOC, FR9T under `h-mad/tests/`; E = `docs/03-analysis/probes/gate-non-py-production-files/fr9/20261106T014611Z-e524b58a6e47/`; drive = `docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py`. v2's line numbers hold, because production did not change.

| AC | Verdict | Basis | Code | Test (what it asserts) | What v2 executed |
|---|---|---|---|---|---|
| AC-1.1 | MET | carried from v2 at 57e4f9fc | `wp:245-247` | PT::test_mixed_production_line_collects_all_three (list equality on the AC's three strings) | Unit on the literal line: the three strings, `.py` first, then line order |
| AC-1.2 | MET | carried from v2 at 57e4f9fc | `wp:245-247` | PP::test_paths_label_spelling, ::test_none_value_contributes_nothing, ::test_none_rule_keeps_a_real_path, ::test_label_lines_accumulate, ::test_existing_fields_unchanged, ::test_corpus_old_fields_unperturbed; PT::test_python_only_production_line_keeps_items_and_order | PP not in the range's diff; 23 passed. Unit: `['b.py','a.py','c.py']` |
| AC-1.3 | MET | carried from v2 at 57e4f9fc | `wp:243` | PT::test_none_value_production_stays_empty | Unit: `[]`; driver: none-valued line leaves `scripts/tool.sh` ALLOW on 3 hosts |
| AC-1.4 | MET | carried from v2 at 57e4f9fc | `wp:244-247` | PT::test_non_py_test_token_stays_out_of_tests_and_production (asserts both lists) | Unit: `tests == []` |
| AC-1.5 | MET | carried from v2 at 57e4f9fc | `wp:247` touches `production` only | PT::test_other_task_fields_match_with_and_without_a_non_py_token (real values, budget 37) | Unit: every other key equal, same key set |
| AC-2.1 | MET | carried from v2 at 57e4f9fc | `wp` `main`, print loop deleted | WP::test_cli_prints_no_ungated_line | CLI: first line `WIREPIN: PASS tasks=1 wiring=0 unpinned=0 mislabeled=0`, no `ungated:` line |
| AC-2.2 | MET | carried from v2 at 57e4f9fc | `wp:295` | WP::test_check_and_tasks_carry_no_ungated_key | Unit: key absent from `check()` and the task dict |
| AC-2.3 | MET | carried from v2 at 57e4f9fc | `wp:295` | WP::test_an_unshaped_plan_with_a_non_python_token_stays_unshaped | Unit: `verdict: UNSHAPED`, other keys retained |
| AC-2.4 | MET | carried from v2 at 57e4f9fc | `wire_pin_ungated.json` | U1 → WP::test_a_shell_production_file_is_collected_in_production; U2 → WP::test_an_extensionless_production_path_is_collected_in_production | Harness: `ALL_CAUGHT mutations=2 survived=0`. U3 to U5 retired |
| AC-3.1 | MET | carried from v2 at 57e4f9fc | `judge:339`; `cx:298`; `ag:195`; `sh:199`, `sh:343` | CX-CALLEE, AG-CALLEE, CL-CALLEE; CX/AG/CL-REMOVE and -FORCE naming each host's own node | Harness: `listing_connections` `ALL_CAUGHT mutations=6 refused=0`. Driver with the callee mutated: tool.sh ALLOW on 3 hosts. Connection mutants flip one host only (see below) |
| AC-3.2 | MET | carried from v2 at 57e4f9fc | `id` canonicalise; `sh:343`; `cx:298`; `ag:195` | CL/CX/AG::test_*_symlink_alias_denies | Driver: `test-missing` on 3 hosts |
| AC-3.3 | MET | carried from v2 at 57e4f9fc | same | CL/CX/AG::test_*_case_fold_spelling_denies | Driver on APFS: `test-missing` on 3 hosts |
| AC-3.4 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (hard link), same verdict | `judge:339-343`, `judge:381` | CL/CX/AG::test_*_hard_link_denies | Driver: `test-missing` on 3 hosts; `test-missing` proves the impl-plan branch, since a non-`.py` name map gives `no-test-resolved` (AC-4.6) |
| AC-3.5 | MET | carried from v2 at 57e4f9fc | realpath compare inside `_match_plans` | CL/CX/AG::test_*_residual_spellings_allow; JL::test_listing_residual_spellings_are_not_listed | Driver: all three spellings ALLOW on 3 hosts, including plan `new.sh` written as `New.SH` |
| AC-4.1 | MET | carried from v2 at 57e4f9fc | `judge:381` | JL::test_judge_listed_non_py_failing_test_is_red_measured (whole Verdict equality) | Unit: `ALLOW red-measured`, source `impl-plan`, `tests/test_tool.py` |
| AC-4.2 | MET | carried from v2 at 57e4f9fc | same | JL::test_judge_listed_non_py_passing_test_is_test_passing | Unit: `DENY test-passing` |
| AC-4.3 | MET | carried from v2 at 57e4f9fc | `judge:381-382` | JL::test_judge_listed_non_py_absent_test_is_test_missing | Unit: `DENY test-missing`, reason names `tests/test_tool.py` |
| AC-4.4 | MET | carried from v2 at 57e4f9fc | `judge:381-382` | JL::test_judge_listed_non_py_with_no_pytest_file_is_test_missing (literal `tests/tool.bats`) | Unit: `DENY test-missing`, resolution `('impl-plan', ())`; driver: `test-missing` on 3 hosts |
| AC-4.5 | MET | carried from v2 at 57e4f9fc | `judge:492` | JL::test_target_module_names_is_empty_for_a_non_py_target; JL::test_non_py_module_not_found_scores_pytest_error (asserts `1 error`, the exact E line, score and verdict) | Unit, collection form: guard on `DENY pytest-error`; guard replaced by the old body `ALLOW red-measured`. Harness: K-IMPORT-NONPY caught. `.py` control `ALLOW red-measured` |
| AC-4.6 | MET | carried from v2 at 57e4f9fc | name-map branch of `resolve` | JL::test_judge_unlisted_non_py_is_no_test_resolved | Unit: `DENY no-test-resolved` |
| AC-5.1 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (listed absent), same verdict | `sh:340-349`, `sh:402-407` | CL::test_claude_listed_absent_test_denies | Driver: `test-missing`, arrangement line correct; E row 001 |
| AC-5.2 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (listed failing), same verdict | same | CL::test_claude_listed_passing_test_denies; CL::test_claude_listed_failing_test_allows | Driver: `test-passing`, ALLOW |
| AC-5.3 | MET | carried from v2 at 57e4f9fc | same | CL::test_claude_listed_extensionless_absent_test_denies | Driver: `test-missing` |
| AC-5.4 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (unlisted), same verdict | `sh:203`, `sh:328` | CL::test_claude_unlisted_code_like_allows; CL::test_claude_unlisted_doc_data_allows | Driver: ALLOW, ALLOW |
| AC-5.5 | MET | carried from v2 at 57e4f9fc | `sh:358-369` | CL::test_claude_default_authorship_refuses_a_listed_target; CL::test_claude_default_authorship_allows_unlisted_doc_data | Driver with a codex stub on PATH: `codex-authorship`; ALLOW |
| AC-5.6 | MET | carried from v2 at 57e4f9fc | `sh:301`, `sh:203` | CL::test_claude_no_state_file_allows_a_listed_target; CL::test_claude_inactive_record_allows_a_listed_target | Driver: ALLOW in both arms |
| AC-5.7 | MET | carried from v2 at 57e4f9fc | `sh:313` | CL::test_claude_listed_exempt_location_allows | Driver: `tests/helper.sh` ALLOW; `fixtures/` and `docs/` too, on all hosts |
| AC-5.8 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (S1, S2), same verdict | `judge:343`, `sh:344` | CL::test_claude_selection_s1_allows; CL::test_claude_selection_s2_denies (also asserts `hard.sh` and `test_hard.py` in the reason) | Driver: S1 ALLOW, S2 `test-missing` |
| AC-6.1 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (listed absent), same verdict | `cx:298-306`, `cx:372` | CX::test_codex_listed_absent_test_denies | Driver: `test-missing`; E row 012 |
| AC-6.2 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (listed failing), same verdict | same | CX::test_codex_listed_passing_test_denies; CX::test_codex_listed_failing_test_allows | Driver: `test-passing`, ALLOW |
| AC-6.3 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (unlisted), same verdict | `cx:301`, `cx:363` | CX::test_codex_unlisted_code_like_allows; CX::test_codex_add_file_doc_data_allows | Driver including the literal `*** Add File: notes.md`: ALLOW, ALLOW |
| AC-6.4 | MET | carried from v2 at 57e4f9fc | `cx:372` inside the `M:G5` loop | CX::test_codex_multi_target_patch_denies_on_the_listed_target | Driver: DENY `test-missing` |
| AC-6.5 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (S1, S2), same verdict | `judge:343`, `cx:303` | CX::test_codex_selection_s1_allows; CX::test_codex_selection_s2_denies | Driver: S1 ALLOW, S2 `test-missing` |
| AC-7.1 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (listed absent), same verdict | `ag:195-206` | AG::test_agy_listed_absent_test_denies | Driver: deny; reason ends `kind=test-missing` per `ag:206`; E row 023 |
| AC-7.2 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (listed failing), same verdict | same | AG::test_agy_listed_passing_test_denies; AG::test_agy_listed_failing_test_allows | Driver: `test-passing`, `{"decision": "allow"}` |
| AC-7.3 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (unlisted), same verdict | `ag:174`, `ag:200` | AG::test_agy_unlisted_code_like_allows; AG::test_agy_unlisted_doc_data_allows | Driver: allow, allow |
| AC-7.4 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (S1, S2), same verdict | `judge:343`, `ag:202` | AG::test_agy_selection_s1_allows; AG::test_agy_selection_s2_denies | Driver: S1 allow, S2 deny `test-missing` |
| AC-8.1 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (unreadable plan), same verdict | `judge:320`, `judge:345`, `cx:299`, `ag:196`, `sh:206` | CL/CX/AG::test_*_unreadable_plan_is_judge_error | Driver: `judge-error` on 3 hosts; also mode 000, a directory, and a symlink loop in place of the plan |
| AC-8.2 | MET | carried from v2 at 57e4f9fc | `judge:735`, `cx:294`, `ag:189`, `sh:206` | CL/CX/AG::test_*_unreadable_state_is_judge_error, parametrised on `scripts/other.sh` | Driver with `{not json`: `judge-error` on 3 hosts |
| AC-8.3 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (absent plan), same verdict | `judge:317` | CL/CX/AG::test_*_absent_plan_allows; JL::test_listing_absent_plan_is_not_listed | Driver: ALLOW on 3 hosts |
| AC-8.4 | MET | carried from v2 at 57e4f9fc | `sh:328`, `cx:363`, `ag:174` | CL/CX/AG::test_*_doc_data_allows_in_undecidable_states | Driver: 12 readings, all ALLOW |
| AC-9.1 | MET | carried from v2 at 57e4f9fc | drive:139-141, drive:217-219, drive:257 | FR9T::test_fr9_driver_refuses[authorship-line] for the check | E rows 001-003, 012-014, 023-025 read as required; the Claude rows' `implementer.txt` holds the required line |
| AC-9.2 | MET | carried from v2 at 57e4f9fc | drive:82-95 | FR9T::test_fr9_driver_refuses[dirty-hooks, hook-outside-tree, hook-blob-mismatch] | Provenance sha256 prefixes `73b0dbc5bd41`, `f13b0042ec69`, `183baa59b299` equal `git show 57e4f9fc:<hook> \| shasum -a 256`. Evidence commit is e524b58a; `git diff --name-only e524b58a 57e4f9fc -- h-mad/hooks h-mad/scripts` printed nothing |
| AC-9.3 | **UNMET** (`both`) | **re-read at 246531ba** | 16 lines, §"Question 1" | Clauses 2 and 3 met on 24 sampled rows; 13 of the 16 are killed by a named test, 3 by none | See Question 1 and Must-fix |
| AC-9.4 | MET | carried from v2 at 57e4f9fc | drive:142-150, drive:203-214 | none (evidence is the proof) | E rows 004-011, 015-022, 026-033: all 12 before rows ALLOW; each host's after row DENY `test-missing` on the listed-absent row and ALLOW on the others; PASS on 33 of 33 |
| AC-9.5 | MET | carried from v2 at 57e4f9fc | drive:72-79, drive:98-111 | FR9T::test_fr9_driver_refuses[missing-base, base-is-head, plan-absent-at-base, plan-blob-mismatch] | Provenance base `e097dfcb`; `git merge-base 57e4f9fc origin/main` prints the same; `git rev-parse e097dfcb:<plan>` prints `fef082989979…`, equal to `plan_blob` and `copy_blob`; before-side hook shas recorded per host |
| AC-10.1 | MET | carried from v2 at 57e4f9fc | prose | DOC::test_gate_prose_has_no_retired_phrasing (8 branches) | Ran the five-branch `git grep` at 57e4f9fc: no line, rc=1 |
| AC-10.2 | MET | carried from v2 at 57e4f9fc | `codex-implementer-prompt.md:19-24` | DOC::test_hook_bullets_state_the_shipped_rule | Module passes. Node on the e4979ecd prose: fails `Hook bullets must state '.md'` |
| AC-10.3 | MET | carried from v2 at 57e4f9fc | `phase5-substeps.md:230`, `:235` | DOC::test_skill_states_the_docs_first_component_rule | Passes. Node on the e4979ecd prose: fails `assert 0 == 1` on the anchor count |
| AC-11.1 | MET | carried from v2 at 57e4f9fc; spot-read at 246531ba by driver (listed doc/data), same verdict | `id:38`, `sh:328`, `cx:363`, `ag:174` | CL/CX/AG::test_*_listed_doc_data_allows | Driver: ALLOW on 3 hosts; the control reads DENY `test-missing` |
| AC-11.2 | MET | carried from v2 at 57e4f9fc | `id:33-34` | CL/CX/AG::test_*_listed_upper_case_doc_data_allows | Driver: `CHANGES.MD` and `changes.md` ALLOW on 3 hosts |
| AC-11.3 | MET | carried from v2 at 57e4f9fc | `id:19`, `id:33-34` | CL/CX/AG::test_*_doc_data_member_allows (9 parameters each) | Driver: 54 readings, all ALLOW |
| AC-11.4 | MET | carried from v2 at 57e4f9fc | `id:33-38`, gates | CL/CX/AG::test_*_excluded_member_denies (7 parameters each) | Driver: 21 readings, all `test-missing` |
| AC-11.5 | MET | carried from v2 at 57e4f9fc | `id:38` | CL/CX/AG::test_*_mixed_hard_links_deny | Driver: `test-missing` on 3 hosts |
| AC-11.6 | MET | carried from v2 at 57e4f9fc | `id:19`, `sh:266` (no bash copy) | DD-CX-*, DD-AG-*, DD-CL-* naming each host's `[<suffix>]` parameter | Driver with `.md` removed: `x.md` DENY `test-missing` on 3 hosts. The 34-row spec's score is the orchestrator's measurement |

## Gaps

### Gap 1: AC-9.3, 16 lines that decide a verdict have no mutation-spec entry, and 3 of them no test
- **Missing**: an entry for each of the 16 lines in §"Question 1", and a test for `judge:733`, `cx:293` and `ag:188`.
- **Classification**:

  | AC | Classification | Why | Action |
  |---|---|---|---|
  | AC-9.3 | `both` | neither the design's row lists nor the specs carry these lines, and neither document argues for omitting them | amend the design and the plan, add the rows and 3 tests; no production change |

- **Why v2 did not report these**: it read by eye and named three. This table comes from the diff, so a reader did not have to notice the line. The code has not changed since v2.
- **Where it should be**: `h-mad/tests/mutation-specs/listing_matcher.json` for the `judge` lines; the host specs for the rest. `listing_connections.json` is pinned at six rows by AC-3.1, so rows 7 to 13 belong in `codex_gate_listing.json`, `agy_gate_listing.json` and `claude_gate_listing.json`.
- **Fix**:
  1. Add three nodes, one per host, using the nested scenario above: state and plan under `sub/`, none at the root, write `sub/scripts/s.sh`, test absent, expect DENY `test-missing`.
  2. Add the 16 rows. The Mutant column gives each `replace`, and the Killer column gives a node each mutant already failed in my run, except rows 14 to 16, which name the new nodes.
     A scratch spec holding rows 1 to 13 and `judge:733`, on the harness and an archive, printed `MUTATION: SURVIVED mutations=14 caught=13 survived=1`, and the survivor was `judge:733`. So the 13 rows land as written and their killers score.
  3. Update design:613, the plan's departures and the ledger at plan:1311.
  4. Re-derive the census afterwards, since a hand list has now been incomplete twice.
- **Refutation path**: an operator ruling that "guard" means a marked guard closes the clause. Rows 14 to 16 would still need a home, as a test gap on `.py`-parity.

## Test Results
```
.venv/bin/python -m pytest -q   (at 246531ba, measured by the orchestrator; not re-run)
8636 passed, 3 warnings in 2391.97s
```
Orchestrator's mutation figures, each `ALL_CAUGHT survived=0 refused=0`, not re-run: `wire_pin_ungated` 2, `parse_tasks_non_py` 3, `doc_data_definition` 34, `listing_matcher` 17 (three rows re-run, `ALL_CAUGHT mutations=3`), `listing_connections` 6, `judge_non_py` 1, `claude_gate_listing` 15, `codex_gate_listing` 10, `agy_gate_listing` 8, `fr9_drive_refusals` 9, `shared_gate_policy` 5, `codex_gate_tmp_reports` 9, `agy_tdd_gate` 23. `--check-anchors`: `ANCHORS_OK specs=214 mutations=3024`. FR-9 evidence: 33 of 33 PASS at e524b58a.

Scoped runs by this analysis on scratch archives of 246531ba: the four non-Python gate modules, `239 passed in 45.97s`; `test_h_mad_codex_gate_tmp_reports.py`, `test_h_mad_doc_data.py` and the two docdata nodes, `45 passed in 24.46s`. The 41-module comparison is in §"Question 1".

## Verdict
Match rate: 91% (threshold: 90%). Tests: 8636/8636 passing, per the orchestrator's measurement.
→ The formula alone would advance. This pass is GATING, so iterate first: 1 gap to close, or refute it by the path in Gap 1. It needs 3 new tests, 16 rows and document lines, and no production change. Re-measure afterwards.

## Must-fix
- AC-9.3 is unmet: 13 lines that decide a verdict have no mutation-spec row, though existing tests kill them. Failure scenario: a change turns `judge:737` into `elif False:`, so the Claude gate reads ALLOW on a listed `scripts/tool.sh` with its test absent and on an unreadable plan, where AC-5.1 and AC-8.1 require DENY. Or `sh:269`'s `"docdata no"` arm sets `yes`, and every code-like write on Claude is allowed. The harness cannot report either, because it has no row to run. The module's tests catch both today, so the protection exists and the AC's required record does not.
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:221 › `Every new guard in FR-1, FR-3 to FR-8 and FR-11 has a mutation-spec entry.`
  quote: h-mad/scripts/h_mad_tdd_judge.py:737 › `elif chain.value == "active":`
  quote: h-mad/hooks/h-mad-tdd-gate.sh:269 › `"docdata no") DOC_DATA=no ;;`
  quote: h-mad/scripts/h_mad_tdd_judge.py:335 › `result.append(PlanMatch(plan, "read", "", tuple(matches)))`
- The chain read on each host's non-`.py` path is bound to the target by no row and no test. Failure scenario: `sub/docs/.bkit-memory.json` holds an active record whose plan lists `scripts/s.sh`, the root holds no state, and `read_chain(root, names[0])` is changed to `read_chain(root, None)`. A write to `sub/scripts/s.sh` with its test absent then reads ALLOW on that host instead of DENY `test-missing`. The combined mutant newly fails no node in the 41 gate-related modules, and the harness printed `MUTATION: SURVIVED mutations=3 caught=0 survived=3`, so a row alone would not help. The rest of the suite was not run against these mutants. The `.py` path pins the same property with rows W5AR and W5AF.
  quote: h-mad/scripts/h_mad_tdd_judge.py:733 › `chain = read_chain(root, names[0])`
  quote: h-mad/hooks/h-mad-codex-tdd-gate.py:293 › `chain = judge.read_chain(root, names[0])`
  quote: h-mad/hooks/h-mad-agy-tdd-gate.py:188 › `chain = judge.read_chain(root, names[0])`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:10 › `The judge's `read_chain(root, target)` returns `value == "active"` for the target.`

## Should-fix
- `unverified`: the operator ruling behind the ninth driver refusal still has no primary record I could find. Carried from v1 and v2. A grep of the spec for `plan-absent`, `absent at the base`, `ninth` and `nine refusals` prints nothing, and the ruling is visible only through the impl-plan. FR-9's AC-9.5 does not depend on it.
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md:29 › `This plan follows the operator ruling of 2026-11-04 instead`

## Nit
- Carried from v2: codex's refusal puts the target path before `kind=`, so a listed `scripts/kind=x.sh` carries two `kind=` tokens. I did not re-drive it, since production has not changed.
- Carried from v2: `sh:2` still says "gate for production Python writes", and `DOC::test_hook_line_names_both_gates` keeps its old name.
- Carried from v2: `# M:CX-NOT-CODE-LIKE`, `# M:AG-NOT-CODE-LIKE` and `# M:K-IMPORT-NONPY` keep `Path.suffix` beside the `.endswith` form used at `id:358`, `cx:216` and `ag:161`.
- Carried from v2: spec FR-11's M5 reach figures remain un-re-derived. No AC names them.
- The newly named same-directory residual has no test, as the design says, so its ALLOW on codex and agy can change without a test failing. This is consistent with the operator's decision to name it. If a later fix is planned, a pin would show it moving.

## Version History
- v1.0: Initial gap analysis draft, Phase 6a, first measurement at 7584ace9 (100 at FR level, AC-9.3 read as met by a marker census).
- v2.0: Second gap analysis at 57e4f9fc against spec v1.14 (91 at FR level, 54 of 55 ACs). AC-9.3 moves to UNMET on three unmarked judge arms.
- v3.0: Third gap analysis at 246531ba against spec v1.15, design v1.10 and impl-plan v1.9 (91 at FR level, 54 of 55 ACs). v2's three arms are closed. A census of 158 changed decision lines finds 16 with no row, 3 of which no test kills, so AC-9.3 stays UNMET. Spec v1.15's refusals and both residuals executed as written on all three hosts. v2's Should-fix 1 and 3 closed, 2 moved to a named residual, 4 and all four Nits open. 54 AC rows carried from v2, AC-9.3 re-read.
