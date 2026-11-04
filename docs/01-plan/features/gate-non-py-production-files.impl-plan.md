# Implementation Plan: gate-non-py-production-files

> Source: docs/02-design/features/gate-non-py-production-files.design.md v1.4, following its §"Implementation Order"; spec v1.11; plan v1.6.
> Branch target: BrightGold70/gate-non-py-production-files
> Tree readings: taken at `26571a2d` from PROJECT_ROOT. Readings marked "prototype" ran on a throwaway scratch copy of the tree carrying this plan's edits, outside the repository, and it was removed after the run.
> Existing tests this feature moves, prototype reading at `26571a2d` with the Tasks 1 to 6 production edits and the two stub edits applied: the 34 test files that name an edited module read 9 failures, the 8 retired `ungated` nodes of Task 1 and `test_py_suffixes_match_bash_fold` of Task 6, and every other test passed. The whole suite was not run on the prototype: it was stopped at 5% (447 passed, 0 failed), because it would have taken hours. Each Task's gate runs it for real.

## Executive Summary
Eight Tasks in a chain: the parser widens `production` and retires `ungated` (Task 1), the doc/data definition lands in `h_mad_target_identity` (Task 2), the judge gains `_match_plans`, `listing` and the `listing` verb (Task 3), the codex, agy and Claude gates are wired to them in that order (Tasks 4, 5, 6), the prose states the shipped rule (Task 7), and the FR-9 driver takes the end-to-end proof and the whole mutation run (Task 8).

## How to read this plan
- **Task shapes.** Tasks 4, 5 and 6 are `wiring`. Tasks 1, 2, 3, 7 and 8 are `new-behaviour`.
- **Where each Task's commands live.** 5d cuts one Task's body out of this document, so every Task carries its own commands and literal text. The rules below are for the orchestrator and the reviewer.
- **Reading a result.** Read `MUTATION:`, `ANCHORS:` and `FR9-DRIVE:` tokens and pytest's summary line, never `$?`. Run pytest through `rtk proxy`, because RTK rewrites `pytest` output otherwise.
- **The gate after every Task's GREEN.** The full suite, `rtk proxy python3.11 -m pytest` from PROJECT_ROOT, scored on its summary line. Then each spec the Task names through `python3 h-mad/scripts/h_mad_mutation_harness.py`, requiring `MUTATION: ALL_CAUGHT` with `refused=0`. Then `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors` over every spec in `h-mad/tests/mutation-specs/`, requiring `ANCHORS: ANCHORS_OK`.
- **Spec shape.** A new spec under `h-mad/tests/mutation-specs/` has `"root": "../.."`, a `command` of `["python3.11", "-m", "pytest", THE_TASK_TEST_FILES, "-q"]`, and a `target_command` of `["python3.11", "-m", "pytest", "-q"]`. The `root` makes `h-mad/` the working directory, so the `test` keys in this plan read `tests/test_x.py::name` and the `file` keys read `scripts/x.py`. `WIRE-PIN` lines use the repository-relative form `h-mad/tests/test_x.py::name`, because 5f's registry collects from the repository root. Specs are written at GREEN, against source that exists. A shared spec's `command` gains a host's test file in that host's Task.
- **Symbols.** Every row in a `.py` file carries the `symbol` key this plan gives it. Rows in `h-mad/hooks/h-mad-tdd-gate.sh` carry none. "Module-level `symbol`" means the value the harness's `enclosing_symbol` returns for top-level code: the word `module` in angle brackets.

## Where this plan departs from or adds to design v1.4
Each item is stated again in its Task, with the reason.
1. **`non_py_gate_support.py` is not on a **Test file** line (Task 4).** The design lists it among Task 4's tests. `resolve` turns every `.py` token of that line into a judge candidate, and a support module collects no tests. The module has its own `**Test support**` line, which `_PATHS_FIELD_RE` does not match.
2. **Five existing rows are re-anchored, three beyond the design's two.** `--check-anchors` over all 192 specs on the prototype drifted 9 rows: `U1`, `U3`, `U4` and `U5` (rewritten or retired in Task 1), and five more. The design names `H11` and `CG-CANON` (Task 6). It does not name `declared-budget-not-read` (Task 3: the line moves from 20 spaces of indent to 12), `fr6-import-guard-dropped` (Task 4: it anchors codex's whole import block, which gains three names), or `fr4-t7-unreadable-dropped` (Task 5: agy's new line at 20 spaces contains that anchor's 16-space text, so the anchor matches twice). With the Task 3, 4 and 5 edits below applied, those three specs printed `ANCHORS_OK` on the prototype.
3. **The parser guard's killer asserts `production` too (Task 1).** With `if key == "production":` forced true, a `.json` token on a **Test file** line lands in `production`, not in `tests`, so an assertion on `tests` alone cannot kill it.
4. **`# M:H-LIST-INROOT`'s killer sits beside an unreadable state (Task 6).** On a readable state the mutant still reads ALLOW, because the matcher finds no out-of-root target (prototype reading in Task 6).
5. **Three Claude guards are killed on the reason, not the kind (Task 6).** `# M:H-LIST-UNREADABLE` is the design's. `# M:H-LIST-LINES` and `# M:H-DOCDATA-LINE` are this plan's: without the line guard the same output falls through to "no well-formed listing line", also `judge-error` (prototype reading in Task 6).
6. **Driver refusals get mutation rows (Task 8).** This settles the plan D11 and FR-9 mismatch with option (a); the reasoning is in Task 8.
7. **Added guard rows beyond the design's list.** `P-PYFILTER`, `DD-EXEMPT-DOCS`, `DD-EXEMPT-DIRS`, `DD-EXEMPT-PARENT`, `DD-EMIT`, `L-ABSENT`, `LV-NONE`, `LV-CHAIN-UNREADABLE`, `LV-RC`, `CX-NOT-CODE-LIKE`, `AG-NOT-CODE-LIKE`, and a second `# M:CX-DOCDATA` row with a verdict killer. AC-9.3 requires an entry for every new guard, and each of these is one.
8. **Test names the design leaves open are named here.** Spelled once and used exactly as spelled in ACs, RED splits and mutation rows.

The design's "mixed-plan fixture" (Components table) is the **two-record fixture** here, the name its §Test Strategy and Test Boundaries use.

## Task 1: parser-and-wire-pin

**Production file**: `h-mad/scripts/h_mad_wire_pin_gate.py`
**Test file**: `h-mad/tests/test_h_mad_parse_tasks_non_py.py`, `h-mad/tests/test_h_mad_wire_pin_gate.py`
**Task shape**: `new-behaviour`

**Description**: FR-1 widens `production` to hold every backticked non-`.py` path on a **Production file** line, and FR-2 retires the `ungated` surface. `_parse_tasks` is private, so its unit tests are supplementary; five consumer tests drive the real parser through the judge and wire-pin CLIs. The judge is the only reader of `production` (`git grep -n '"production"' -- h-mad/scripts` names `h_mad_tdd_judge.py` and `h_mad_wire_pin_gate.py` itself; `h_mad_assemble_tdd.py` and `h_mad_wire_registry.py` call `_parse_tasks` and read other keys).

**Code structure** (the edit) in `_parse_tasks`, replacing the `current["ungated"].extend(` statement under `if key == "production":`, on one line:

```python
current["production"].extend(token for token in _NON_PY_PATH_RE.findall(paths.group("value")) if not token.endswith(".py"))  # M:P-NONPY
```

The `.py` tokens of a line come first, as today, then its non-`.py` tokens in line order. A line without non-`.py` tokens is unchanged in items and order.

**Deleted**: the `"ungated": []` key and its comment, `_ungated_entries`, the `ungated` local in `check()`, both `"ungated": ungated` result entries, and the `for item in result["ungated"]:` print loop in `main`. The comments at `_NON_PY_PATH_RE` and at `path_labels` ("`production`/`tests` keep only `.py` tokens") are reworded: only `tests` is `.py`-only. `grep -n ungated h-mad/scripts/h_mad_wire_pin_gate.py` prints nothing after the edit.

**Retired from `h-mad/tests/test_h_mad_wire_pin_gate.py`** (six functions, eight collected nodes; regression provenance "stale contract": each asserted the `ungated` surface FR-2 retires), with the `# --- a non-.py production file is reported as ungated` comment block above them:
- `test_a_non_python_production_file_is_reported_ungated`
- `test_an_extensionless_script_path_is_ungated_too`
- `test_python_or_none_production_is_never_ungated` (three parameters)
- `test_a_non_python_test_file_is_not_ungated`
- `test_an_unshaped_plan_still_carries_the_ungated_key`
- `test_cli_prints_ungated_lines_and_keeps_the_token`

**New tests in `h-mad/tests/test_h_mad_wire_pin_gate.py`** (5 nodes, all RED):
- `test_a_shell_production_file_is_collected_in_production`: `_parse_tasks` on a line with `` `h-mad/scripts/hmad-dispatch.sh` `` and `` `h-mad/scripts/a.py` `` gives a `production` holding both. RED: `.sh` absent.
- `test_an_extensionless_production_path_is_collected_in_production`: `` `h-mad/bin/hmad-dispatch` `` is in `production`. RED: absent.
- `test_cli_prints_no_ungated_line`: AC-2.1's plan prints first line `WIREPIN: PASS tasks=1 wiring=0 unpinned=0 mislabeled=0` and no line containing `ungated:`. RED: the line is printed.
- `test_check_and_tasks_carry_no_ungated_key`: `check()` and `_parse_tasks` carry no `ungated` key. RED: key present.
- `test_an_unshaped_plan_with_a_non_python_token_stays_unshaped`: verdict `UNSHAPED`, and `set(result)` equals `{"verdict", "tasks", "wiring", "unpinned", "unshaped", "mislabeled", "unlabeled"}`. RED: the set holds `ungated`.

**New tests in `h-mad/tests/test_h_mad_parse_tasks_non_py.py`** (10 nodes). Each CLI runs under `sys.executable`, the suite's interpreter, which holds pytest.

RED (4 nodes):
- `test_mixed_production_line_collects_all_three` (AC-1.1, unit): RED reads `production == ['h-mad/scripts/a.py']`.
- `test_judge_cli_finds_each_token_of_a_mixed_production_line` (AC-1.1): on the AC-1.1 line, with `tests/test_t.py` named on the **Test file** line and absent on disk, each of the three targets reads `kind=test-missing`. RED: the `.sh` and the extensionless target read `kind=no-test-resolved`.
- `test_judge_cli_ignores_a_non_py_test_token` (AC-1.4): a listed `scripts/x.sh`, and an existing `h-mad/tests/mutation-specs/x.json` on the **Test file** line, reads `kind=test-missing` with no candidate. RED: `kind=no-test-resolved`. With `tests` widened it would read `kind=no-tests-ran`.
- `test_wire_pin_cli_output_ignores_a_non_py_token` (AC-1.5): `h_mad_wire_pin_gate.py PLAN --feature f --registry FILE` on a `wiring` Task, with and without a `.sh` token on its **Production file** line, prints the same stdout and writes the same registry record apart from `registered_ts`. RED: stdout differs by the `ungated:` line.

Controls, green before and after (6 nodes):
- `test_python_only_production_line_keeps_items_and_order` (AC-1.2, unit)
- `test_none_value_production_stays_empty` (AC-1.3, unit)
- `test_non_py_test_token_stays_out_of_tests_and_production` (AC-1.4, unit): `**Production file**: ` `` `src/m.py` `` and `**Test file**: ` `` `h-mad/tests/mutation-specs/x.json` `` give `tests == []` and `production == ['src/m.py']`.
- `test_other_task_fields_match_with_and_without_a_non_py_token` (AC-1.5, unit): `shape`, `wire`, `pin`, `wires`, `pins`, `path_labels`, `runner`, `runner_error` and `judge_budget`.
- `test_judge_cli_keeps_a_python_only_line` (AC-1.2): a listed `src/m.py` with a failing test reads `ALLOW kind=red-measured source=impl-plan test=tests/test_m.py`.
- `test_judge_cli_ignores_a_none_production_value` (AC-1.3): `docs/x/run.sh` reads `kind=no-test-resolved`.

**Stated residual of the consumer tests.** `resolve` uses `any(...)` over `production`, so AC-1.2's order is unobservable through the judge CLI, and `judge_budget` reaches neither wire-pin's stdout nor its registry record. The two unit tests `test_python_only_production_line_keeps_items_and_order` and `test_other_task_fields_match_with_and_without_a_non_py_token` hold those two properties, and they stay.

**RED split**: 9 failed, 6 passed, across the two files' new nodes. Every failure is an assertion.

**Acceptance Criteria**:
- [ ] AC-1.1: `test_mixed_production_line_collects_all_three` and `test_judge_cli_finds_each_token_of_a_mixed_production_line` pass.
- [ ] AC-1.2: `test_python_only_production_line_keeps_items_and_order` and `test_judge_cli_keeps_a_python_only_line` pass, and `test_paths_label_spelling`, `test_none_value_contributes_nothing`, `test_none_rule_keeps_a_real_path`, `test_label_lines_accumulate`, `test_existing_fields_unchanged` and `test_corpus_old_fields_unperturbed` in `h-mad/tests/test_h_mad_parse_tasks_paths.py` pass unmodified.
- [ ] AC-1.3: `test_none_value_production_stays_empty` and `test_judge_cli_ignores_a_none_production_value` pass.
- [ ] AC-1.4: `test_non_py_test_token_stays_out_of_tests_and_production` and `test_judge_cli_ignores_a_non_py_test_token` pass.
- [ ] AC-1.5: `test_other_task_fields_match_with_and_without_a_non_py_token` and `test_wire_pin_cli_output_ignores_a_non_py_token` pass.
- [ ] AC-2.1: `test_cli_prints_no_ungated_line` passes.
- [ ] AC-2.2: `test_check_and_tasks_carry_no_ungated_key` passes.
- [ ] AC-2.3: `test_an_unshaped_plan_with_a_non_python_token_stays_unshaped` passes.
- [ ] AC-2.4: `test_a_shell_production_file_is_collected_in_production` and `test_an_extensionless_production_path_is_collected_in_production` pass, and `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/wire_pin_ungated.json` prints `MUTATION: ALL_CAUGHT` with `mutations=2` and `refused=0`.

**Mutation rows** (5; `file` `scripts/h_mad_wire_pin_gate.py`; `symbol` is `_parse_tasks` unless stated). Each `find` matches one line.

`wire_pin_ungated.json` (2 rows; keeps its filename; U3, U4 and U5 are removed and `_why` records why: their guarantees assert the retired surface itself):
- `U1`: find `current["production"].extend(token for token in _NON_PY_PATH_RE.findall(paths.group("value")) if not token.endswith(".py"))  # M:P-NONPY`, replace `pass  # M:P-NONPY`. Test `tests/test_h_mad_wire_pin_gate.py::test_a_shell_production_file_is_collected_in_production`.
- `U2`: find `` _NON_PY_PATH_RE = re.compile(r"`([^`\s]*[/.][^`\s]*)`") ``, replace `` _NON_PY_PATH_RE = re.compile(r"`([^`\s]*\.[A-Za-z]+)`") ``, module-level `symbol`. Test `tests/test_h_mad_wire_pin_gate.py::test_an_extensionless_production_path_is_collected_in_production`.

`parse_tasks_non_py.json` (3 rows):
- `P-GUARD`: find `if key == "production":`, replace `if True:`. Test `tests/test_h_mad_parse_tasks_non_py.py::test_non_py_test_token_stays_out_of_tests_and_production`.
- `P-NONPY`: the same find as `U1`, replace `pass  # M:P-NONPY`. Test `tests/test_h_mad_parse_tasks_non_py.py::test_mixed_production_line_collects_all_three`.
- `P-PYFILTER`: find ` if not token.endswith(".py"))  # M:P-NONPY`, replace `)  # M:P-NONPY`. Test `tests/test_h_mad_parse_tasks_non_py.py::test_python_only_production_line_keeps_items_and_order`, because every `.py` token would then be collected twice.

`tdd_judge_resolution.json` (`P1`, `P1B`) anchors the `current[key].extend(_PY_TOKEN_RE.findall(` line, which this edit does not touch; it must stay `ALL_CAUGHT`.

**Note**: plan M5 and M12's parser probe read the `ungated` key and must not be re-run after this Task.

**Commands**:
```bash
rtk proxy python3.11 -m pytest h-mad/tests/test_h_mad_parse_tasks_non_py.py h-mad/tests/test_h_mad_wire_pin_gate.py h-mad/tests/test_h_mad_parse_tasks_paths.py -q
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/wire_pin_ungated.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/parse_tasks_non_py.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/tdd_judge_resolution.json
```
Then the full suite and `--check-anchors` over all of `h-mad/tests/mutation-specs/`.

**Dependencies on other tasks**: None.

---

## Task 2: doc-data-definition

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_doc_data.py`
**Task shape**: `new-behaviour`

**Description**: FR-11's single definition: one constant, one predicate, one emitter for the Claude gate's existing canonicalise process, plus the path half of `_is_production_python` as a helper. `_is_production_python` is not edited; it keeps `# M:G-DOCS` and its `target_identity.json` anchors. Neither the judge nor the parser applies this definition.

**Code structure**:
```python
DOC_DATA_SUFFIXES = (".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst", ".cfg", ".ini")
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")

def has_doc_data_suffix(name: str) -> bool:
    return any(name[-len(s):].translate(_ASCII_LOWER) == s for s in DOC_DATA_SUFFIXES)  # M:G-DOCDATA-CASE

def is_doc_data(names: Sequence[str]) -> bool:
    return all(has_doc_data_suffix(n) for n in names)  # M:G-DOCDATA-ALL

def emit_doc_data(identity: Identity) -> None:
    print("docdata yes" if is_doc_data(identity.names) else "docdata no")  # M:G-DOCDATA-EMIT

def _is_exempt_location(relative: str) -> bool:
    parents = Path(relative).parts[:-1]  # M:G-EXEMPT-PARENT
    if parents[:1] == ("docs",):  # M:G-EXEMPT-DOCS
        return True
    return "tests" in parents or "fixtures" in parents  # M:G-EXEMPT-DIRS
```
`str.lower()` is not used, because it folds non-ASCII letters too. `is_doc_data(())` is vacuously `True`: a directory is the only resolvable identity with no names, and no host's verdict for a directory changes (Tasks 4, 5, 6). `Sequence` joins the module's `from typing import Any, NamedTuple`.

**The tests reach the module by attribute** (`import h_mad_target_identity as identity`, then `identity.DOC_DATA_SUFFIXES`). `score` reads a collection error as `pytest-error`, a DENY, and an `AttributeError` inside a test body as `failed`, so a `from h_mad_target_identity import DOC_DATA_SUFFIXES` would make the gate refuse the very stubs below.

**RED, in two steps.** A missing attribute is not the accepted RED reason by itself. The Task first adds the names as stubs (`DOC_DATA_SUFFIXES = ()`, `has_doc_data_suffix` and `is_doc_data` and `_is_exempt_location` returning `False`, `emit_doc_data` printing nothing) and only then measures the split below, on assertions.

**New tests in `h-mad/tests/test_h_mad_doc_data.py`** (23 nodes).

RED against the stubs (14 nodes):
- `test_doc_data_suffixes_are_the_spec_nine`: pins `DOC_DATA_SUFFIXES` to the spec's nine strings, in order.
- `test_has_doc_data_suffix_accepts[lower]`, `[upper]`, `[mixed]`, `[tar-md]`, `[dotfile]`: `README.md`, `NOTES.MD`, `Config.Json`, `a.tar.md`, and a file named exactly `.md`.
- `test_is_doc_data_requires_every_name`: `("x.md", "x.sh")` is `False`, `("x.md", "y.json")` is `True`.
- `test_is_doc_data_is_vacuously_true_for_no_names`
- `test_emit_doc_data_prints_exactly_one_line[yes]`, `[no]`: stdout is exactly `docdata yes\n` or `docdata no\n`.
- `test_is_exempt_location_matches_is_production_python[docs]`, `[tests]`, `[a-tests-b]`, `[fixtures]`: `_is_production_python(d + "/m.py") == (not _is_exempt_location(d + "/m.py"))`.

Green against the stubs, and after (9 nodes):
- `test_has_doc_data_suffix_rejects[md-then-sh]`, `[mdx]`, `[jsonl]`, `[makefile]`, `[sh]`: `x.md.sh`, `x.mdx`, `x.jsonl`, `Makefile`, `x.sh`.
- `test_is_exempt_location_matches_is_production_python[src-docs]`, `[docs-py]`, `[root]`: `src/docs`, `docs.py`, and a bare `m.py`.
- `test_is_exempt_location_keeps_a_file_named_tests_non_exempt`: `scripts/tests` and `tests` as file names are not exempt.

**RED split**: 14 failed, 9 passed.

**Acceptance Criteria** (the definition half of FR-11; each host's half is in Tasks 4, 5 and 6):
- [ ] `DOC_DATA_SUFFIXES` is the spec's nine strings in order; `test_doc_data_suffixes_are_the_spec_nine` passes.
- [ ] The matching rule holds: end of basename, ASCII case-insensitive, a dotfile `.md` and `a.tar.md` qualify, `x.md.sh`, `x.mdx` and `x.jsonl` do not; `test_has_doc_data_suffix_accepts` and `test_has_doc_data_suffix_rejects` pass on every parameter.
- [ ] `test_is_doc_data_requires_every_name` and `test_is_doc_data_is_vacuously_true_for_no_names` pass.
- [ ] `test_emit_doc_data_prints_exactly_one_line` passes on both parameters.
- [ ] `test_is_exempt_location_matches_is_production_python` passes on all seven parameters, and `test_is_exempt_location_keeps_a_file_named_tests_non_exempt` passes.

**Mutation rows** (7, in `doc_data_definition.json`; `file` `scripts/h_mad_target_identity.py`; the spec's `command` starts as `tests/test_h_mad_doc_data.py`, and Tasks 4, 5 and 6 add their host files):
- `DD-CASE` (`symbol` `has_doc_data_suffix`): find `name[-len(s):].translate(_ASCII_LOWER) == s`, replace `name[-len(s):] == s`. Test `tests/test_h_mad_doc_data.py::test_has_doc_data_suffix_accepts[upper]`.
- `DD-SUFFIX` (`symbol` `has_doc_data_suffix`): the same find, replace `Path(name).suffix.translate(_ASCII_LOWER) == s`. Test `tests/test_h_mad_doc_data.py::test_has_doc_data_suffix_accepts[dotfile]`. `Path(".md").suffix` is empty and `Path("a.tar.md").suffix` is `.md`, so `a.tar.md` reads the same under both rules and kills nothing here.
- `DD-ALL` (`symbol` `is_doc_data`): find `return all(has_doc_data_suffix(n) for n in names)  # M:G-DOCDATA-ALL`, replace `return any(has_doc_data_suffix(n) for n in names)  # M:G-DOCDATA-ALL`. Test `tests/test_h_mad_doc_data.py::test_is_doc_data_requires_every_name`.
- `DD-EMIT` (`symbol` `emit_doc_data`): find `print("docdata yes" if is_doc_data(identity.names) else "docdata no")  # M:G-DOCDATA-EMIT`, replace `print("docdata no")  # M:G-DOCDATA-EMIT`. Test `tests/test_h_mad_doc_data.py::test_emit_doc_data_prints_exactly_one_line[yes]`.
- `DD-EXEMPT-DOCS` (`symbol` `_is_exempt_location`): find `if parents[:1] == ("docs",):  # M:G-EXEMPT-DOCS`, replace `if False:  # M:G-EXEMPT-DOCS`. Test `tests/test_h_mad_doc_data.py::test_is_exempt_location_matches_is_production_python[docs]`.
- `DD-EXEMPT-DIRS` (`symbol` `_is_exempt_location`): find `return "tests" in parents or "fixtures" in parents  # M:G-EXEMPT-DIRS`, replace `return False  # M:G-EXEMPT-DIRS`. Test `tests/test_h_mad_doc_data.py::test_is_exempt_location_matches_is_production_python[tests]`.
- `DD-EXEMPT-PARENT` (`symbol` `_is_exempt_location`): find `parents = Path(relative).parts[:-1]  # M:G-EXEMPT-PARENT`, replace `parents = Path(relative).parts  # M:G-EXEMPT-PARENT`. Test `tests/test_h_mad_doc_data.py::test_is_exempt_location_keeps_a_file_named_tests_non_exempt`.

**Commands**:
```bash
rtk proxy python3.11 -m pytest h-mad/tests/test_h_mad_doc_data.py h-mad/tests/test_h_mad_target_identity.py -q
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_data_definition.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/target_identity.json
```
Then the full suite and `--check-anchors` over all of `h-mad/tests/mutation-specs/`.

**Dependencies on other tasks**: None.

---

## Task 3: judge-listing

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`
**Test file**: `h-mad/tests/test_h_mad_tdd_judge_listing.py`
**Task shape**: `new-behaviour`

**Description**: FR-3's single matcher and FR-4's two Python-only shortcuts. `_match_plans` lifts the plan-path derivation, the read, `tasks = _parse_tasks(text)  # M:W3` (text unchanged, so `W3R` and `W3F` still match exactly once) and the ancestor walk with its realpath comparison out of `resolve`, verbatim. `resolve` and the new `listing` both consume it, so the comparison `os.path.realpath(base / entry) == str(real_target)` exists exactly once. `listing` applies no doc/data rule and no exemption: the gates choose which names to pass.

**Code structure**:
```python
class PlanMatch(NamedTuple):
    plan: Path
    status: str        # "absent" | "unreadable" | "read"
    error: str         # exception class name when status == "unreadable", else ""
    matches: tuple     # ((task, base), ...): every Task whose production lists the target, first base walking up

class Listing(NamedTuple):
    value: str                   # "listed" | "not-listed" | "unreadable"
    selected: Optional[Path]     # set iff value == "listed"
    error_file: Optional[Path]   # set iff value == "unreadable"
    error: str                   # exception class name iff value == "unreadable", else ""

def _match_plans(root: Path, target: Path, records: Sequence[Record]) -> Tuple[PlanMatch, ...]:
    # FileNotFoundError: result.append(PlanMatch(plan, "absent", "", ()))  # M:L-ABSENT
    # OSError, UnicodeDecodeError: PlanMatch(plan, "unreadable", type(exc).__name__, ())
    ...

def listing(root: Path, names: Sequence[Path], records: Sequence[Record]) -> Listing:
    per_name = [(name, _match_plans(root, name, records)) for name in names]
    listed = [name for name, plans in per_name if any(m.matches for m in plans)]
    if listed:  # M:L-LISTED
        return Listing("listed", min(listed, key=lambda p: p.name), None, "")  # M:L-SELECT
    bad = next((m for _, plans in per_name for m in plans if m.status == "unreadable"), None)
    if bad:  # M:L-UNREADABLE
        return Listing("unreadable", None, bad.plan, bad.error)
    return Listing("not-listed", None, None, "")
```

`resolve` keeps its signature and its `.py` output, notes in the same order (`absent`, `impl-plan unreadable: EXC`, `matched` or `matched none`) and the same candidates and budget. Its loop becomes:
```python
    for found in _match_plans(root, target, records):
        plan = found.plan
        if found.status == "absent":
            notes.append(f"{plan}: absent")
            continue
        if found.status == "unreadable":
            notes.append(f"{plan}: impl-plan unreadable: {found.error}")
            continue
        plan_matched = False
        for task, base in found.matches:
            matched = plan_matched = True
            if task.get("judge_budget") is not None:  # M:J-BUDGET-READ
                declared_budget = max(declared_budget or 0, task["judge_budget"])
            for entry in task["tests"]:
                ...  # the existing candidate block, unchanged in behaviour
        notes.append(f"{plan}: {'matched' if plan_matched else 'matched none'}")
```

**The precedence belongs to `listing`, not to `resolve`** (operator ruling R-D, spec §"Assumptions"). A target a readable plan lists is judged from that plan on every host, and FR-8's `kind=judge-error` applies only when no readable plan lists any of its names. `resolve` keeps noting an unreadable plan and continuing, and no gate calls `listing` on the `.py` path, so `test_unreadable_plan_is_named_in_test_missing` and `test_unreadable_plan_with_a_passing_name_map_test_is_test_passing` stay unmodified. Residual, accepted in R-D: an unreadable sibling can hide an earlier listed hard-link name whose Task has different tests. Residual: a plan that turns unreadable between `listing` and `judge` is noted and skipped by `resolve`, as on the `.py` path.

**FR-4.** The first statement of `target_module_names`:
```python
    if Path(fold_py_suffix(target.name)).suffix != ".py":  # M:K-IMPORT-NONPY
        return frozenset()
```
`fold_py_suffix` joins the existing `from h_mad_target_identity import TRUSTED_BIN_DIRS` import.

**The `listing` verb.** `python3 h_mad_tdd_judge.py listing --root DIR --name PATH [--name PATH]`. `--name` uses `action="append"` and `required=True`; each value is joined as `root / name`, as `--target` is today. It reads `read_chain(root, first name)`, then:

| Chain or listing outcome | Exact stdout line | exit |
|---|---|---|
| chain `none` | `TDD-LISTING: not-listed` (`# M:LV-NONE`) | 0 |
| chain `unreadable` (`# M:LV-CHAIN-UNREADABLE`) | `TDD-LISTING: unreadable file=` then `_enc(state file)` then ` error=` then `chain.error` | 0 |
| active, `not-listed` | `TDD-LISTING: not-listed` | 0 |
| active, `unreadable` | `TDD-LISTING: unreadable file=` then `_enc(impl-plan)` then ` error=` then the exception class name | 0 |
| active, `listed` | `TDD-LISTING: listed target=` then `_enc(str(selected))` | 0 |
| any exception | nothing on stdout, `EXC: MESSAGE` on stderr, `return 2  # M:LV-RC` | 2 |

The verb branch sits after the `implementer` branch and before `target = root / args.target`, and the marked lines are:
```python
line = "not-listed"  # M:LV-NONE
if chain.value == "unreadable":  # M:LV-CHAIN-UNREADABLE
return 2  # M:LV-RC
```
Every `error=` value is an identifier, the form `STATE_UNREADABLE_RE` accepts. `TDD-STATE:`, `TDD-JUDGE:` and `WIREPIN:` are untouched.

**New tests in `h-mad/tests/test_h_mad_tdd_judge_listing.py`** (23 nodes). They write their own plan files with `tdd_gate_support.write_state` and `write_plan`, invalid UTF-8 as bytes, and do not import `non_py_gate_support`, which arrives in Task 4. They reach the module by attribute (`judge.listing`, `judge.main`), so the first RED is an `AttributeError` inside the test body, which `score` reads as `failed`.

RED (18 nodes):
- `test_listing_selects_the_least_listed_name`
- `test_listing_any_canonical_name_lists_the_target`
- `test_listing_not_listed_when_no_name_matches`
- `test_listing_absent_plan_is_not_listed`
- `test_listing_listed_outranks_an_unreadable_sibling`: records `f` and `g` both active, `scripts/hard.sh` a hard link to `scripts/tool.sh`, `f.impl-plan.md` lists `scripts/tool.sh` with `tests/test_tool.py`, `g.impl-plan.md` holds invalid UTF-8. Expects `Listing("listed", the path of scripts/tool.sh, None, "")` for both names.
- `test_listing_unreadable_when_no_plan_lists_the_target`: the same two records with `f`'s plan listing another file. Expects `Listing("unreadable", None, the path of g's plan, "UnicodeDecodeError")`.
- `test_listing_residual_spellings_are_not_listed[plan-entry-case]`, `[absent-leaf-case]`, `[other-directory-hard-link]` (AC-3.5, judge side)
- `test_listing_cli_chain_none_prints_not_listed`
- `test_listing_cli_chain_unreadable_prints_unreadable`
- `test_listing_cli_active_not_listed_prints_not_listed`
- `test_listing_cli_active_unreadable_prints_unreadable`
- `test_listing_cli_listed_prints_the_encoded_target`
- `test_listing_cli_internal_exception_exits_2`: in process, `monkeypatch.setattr(judge, "read_chain", raiser)`, `judge.main(["listing", "--root", ROOT, "--name", "x.sh"]) == 2`, empty stdout, and stderr naming the exception. RED is argparse's `SystemExit`.
- `test_target_module_names_is_empty_for_a_non_py_target[sh]`, `[extensionless]` (AC-4.5): RED reads `{'scripts.tool', 'tool'}`.
- `test_non_py_module_not_found_scores_pytest_error` (AC-4.5): a listed `scripts/tool.sh`, absent on disk, and a `tests/test_tool.py` holding a module-level `import tool`, so the error is a **collection error**. `judge` reads DENY `kind=pytest-error`; RED reads ALLOW `kind=red-measured`. The collection form is required: a test body raising `ModuleNotFoundError` is `1 failed`, which `score` reads as `red-measured` with or without the guard, so that form would pass on a removed guard (prototype reading of both forms, with and without `# M:K-IMPORT-NONPY`).

Controls, green before and after (5 nodes; Task 1 already put the `.sh` in `production`):
- `test_judge_listed_non_py_failing_test_is_red_measured` (AC-4.1)
- `test_judge_listed_non_py_passing_test_is_test_passing` (AC-4.2)
- `test_judge_listed_non_py_absent_test_is_test_missing` (AC-4.3)
- `test_judge_listed_non_py_with_no_pytest_file_is_test_missing` (AC-4.4)
- `test_judge_unlisted_non_py_is_no_test_resolved` (AC-4.6)

**RED split**: 18 failed, 5 passed.

**Acceptance Criteria**:
- [ ] AC-3.5 (judge side): `test_listing_residual_spellings_are_not_listed` passes on all three parameters.
- [ ] AC-4.1: `test_judge_listed_non_py_failing_test_is_red_measured` passes: `Verdict("ALLOW", "red-measured", ...)` with source `impl-plan` and test `tests/test_tool.py`.
- [ ] AC-4.2: `test_judge_listed_non_py_passing_test_is_test_passing` passes.
- [ ] AC-4.3: `test_judge_listed_non_py_absent_test_is_test_missing` passes, and the reason names `tests/test_tool.py`.
- [ ] AC-4.4: `test_judge_listed_non_py_with_no_pytest_file_is_test_missing` passes.
- [ ] AC-4.5: `test_target_module_names_is_empty_for_a_non_py_target` and `test_non_py_module_not_found_scores_pytest_error` pass, and the existing `M:K-IMPORT-*` tests in `h-mad/tests/test_h_mad_tdd_judge.py` pass unmodified.
- [ ] AC-4.6: `test_judge_unlisted_non_py_is_no_test_resolved` passes.
- [ ] FR-3 matcher: `test_listing_selects_the_least_listed_name`, `test_listing_any_canonical_name_lists_the_target` and `test_listing_not_listed_when_no_name_matches` pass.
- [ ] FR-3 CLI value set: `test_listing_cli_chain_none_prints_not_listed`, `test_listing_cli_chain_unreadable_prints_unreadable`, `test_listing_cli_active_not_listed_prints_not_listed`, `test_listing_cli_active_unreadable_prints_unreadable`, `test_listing_cli_listed_prints_the_encoded_target` and `test_listing_cli_internal_exception_exits_2` pass.
- [ ] FR-8 judge side: `test_listing_listed_outranks_an_unreadable_sibling`, `test_listing_unreadable_when_no_plan_lists_the_target` and `test_listing_absent_plan_is_not_listed` pass.
- [ ] `.py` identity: `tdd_judge_resolution.json` and `tdd_judge_wiring.json` stay `MUTATION: ALL_CAUGHT` with `refused=0`.

**Mutation rows** (9; `file` `scripts/h_mad_tdd_judge.py`). `listing_matcher.json`, judge-level (8; `command` starts as `tests/test_h_mad_tdd_judge_listing.py`, and Tasks 4, 5 and 6 add their host files):
- `L-SELECT` (`symbol` `listing`): find `min(listed, key=lambda p: p.name), None, "")  # M:L-SELECT`, replace `max(listed, key=lambda p: p.name), None, "")  # M:L-SELECT`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_selects_the_least_listed_name`.
- `L-UNREADABLE` (`symbol` `listing`): find `if bad:  # M:L-UNREADABLE`, replace `if False:  # M:L-UNREADABLE`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_unreadable_when_no_plan_lists_the_target`.
- `L-LISTED` (`symbol` `listing`): find `if listed:  # M:L-LISTED`, replace `if listed and not any(m.status == "unreadable" for _, plans in per_name for m in plans):  # M:L-LISTED`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_listed_outranks_an_unreadable_sibling`.
- `L-ANY-NAME` (`symbol` `listing`): find `per_name = [(name, _match_plans(root, name, records)) for name in names]`, replace `per_name = [(name, _match_plans(root, name, records)) for name in names[:1]]`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_any_canonical_name_lists_the_target`.
- `L-ABSENT` (`symbol` `_match_plans`): find `result.append(PlanMatch(plan, "absent", "", ()))  # M:L-ABSENT`, replace `result.append(PlanMatch(plan, "unreadable", "FileNotFoundError", ()))  # M:L-ABSENT`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_absent_plan_is_not_listed`.
- `LV-NONE` (`symbol` `main`): find `line = "not-listed"  # M:LV-NONE`, replace `line = "unreadable file=x error=Mutant"  # M:LV-NONE`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_cli_chain_none_prints_not_listed`.
- `LV-CHAIN-UNREADABLE` (`symbol` `main`): find `if chain.value == "unreadable":  # M:LV-CHAIN-UNREADABLE`, replace `if False:  # M:LV-CHAIN-UNREADABLE`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_cli_chain_unreadable_prints_unreadable`.
- `LV-RC` (`symbol` `main`): find `return 2  # M:LV-RC`, replace `return 0  # M:LV-RC`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_cli_internal_exception_exits_2`.

`judge_non_py.json` (1):
- `K-IMPORT-NONPY` (`symbol` `target_module_names`): find `if Path(fold_py_suffix(target.name)).suffix != ".py":  # M:K-IMPORT-NONPY`, replace `if False:  # M:K-IMPORT-NONPY`. Test `tests/test_h_mad_tdd_judge_listing.py::test_target_module_names_is_empty_for_a_non_py_target[sh]`.

**Re-anchored existing row** (1, in `tdd_judge_resolution.json`): `declared-budget-not-read`'s find is 20 spaces of indent plus `if task.get("judge_budget") is not None:  # M:J-BUDGET-READ`, which no longer exists after the edit above. Its find becomes the same text at 12 spaces and its replace `            if False:  # M:J-BUDGET-READ`; its test `tests/test_h_mad_tdd_judge.py::test_a_declared_budget_lets_a_slow_red_finish` is unchanged. Regression provenance: the line moved, the mutant's meaning did not.

**Commands**:
```bash
rtk proxy python3.11 -m pytest h-mad/tests/test_h_mad_tdd_judge_listing.py h-mad/tests/test_h_mad_tdd_judge.py -q
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_matcher.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/judge_non_py.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/tdd_judge_resolution.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/tdd_judge_wiring.json
```
Then the full suite and `--check-anchors` over all of `h-mad/tests/mutation-specs/`.

**Dependencies on other tasks**: Task 1 (`production` holds non-`.py` tokens). `fold_py_suffix` already exists, so Task 2 is not a prerequisite; it runs first because Tasks 4, 5 and 6 need both.

---

## Task 4: codex-gate

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`
**Test support**: `h-mad/tests/non_py_gate_support.py` (new; `_dir_match` exempts it. It is not on the **Test file** line, because `resolve` would make it a judge candidate that collects no tests.)
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_judge_listed` → `h_mad_tdd_judge.listing`
**WIRE-PIN**: `h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_listed_absent_test_denies`

**Description**: FR-6, FR-8 and FR-11 on codex. A doc/data target is skipped first, and a code-like, non-exempt target reaches the judge when a readable plan lists it. The `.py` branch (`min(production)`, `# M:W5A`, `# M:W1`) is not edited, and exceptions still reach `# M:G2` as `kind=judge-error`. `test_codex_gate_keeps_no_private_resolver` stays green, because no banned token is introduced.

**WIRE-PIN RED**: at Task 4's RED the callee `h_mad_tdd_judge.listing` exists (Task 3), so no scaffold is needed and no import can fail. `test_codex_listed_absent_test_denies` drives the real hook and fails on an assertion about the caller: it reads ALLOW where DENY `kind=test-missing` is expected. A missing-symbol RED on this pin is a wrong-reason RED.

**Code structure**. Additions to the module-level `from h_mad_target_identity import (` block: `is_doc_data`, `_is_exempt_location`, `fold_py_suffix`. In the per-target loop (`# M:G5`), after the `# M:SA-GUARD` check and before `production = []`:
```python
        if is_doc_data(resolved.names):  # M:CX-DOCDATA
            continue
```
`if not production:` followed by `continue` becomes:
```python
        if not production:
            reason = _judge_listed(root, resolved)
            if reason:
                return _deny(reason)
            continue
```
A new module-level function:
```python
def _judge_listed(root: Path, resolved: Identity) -> str:
    """Return "" to skip or allow, else a deny reason."""
    if any(Path(fold_py_suffix(n)).suffix == ".py" for n in resolved.names):  # M:CX-NOT-CODE-LIKE
        return ""
    names = [Path(resolved.target).parent / n for n in resolved.names]
    if _is_exempt_location(names[0].relative_to(root).as_posix()):  # M:CX-LIST-EXEMPT
        return ""
    judge = _load_judge()
    chain = judge.read_chain(root, names[0])
    if chain.value == "unreadable":  # M:CX-CHAIN-UNREADABLE
        return f"H-MAD state governing this write is unreadable ({chain.error_file}: {chain.error}); refusing fail-closed. kind=judge-error"
    if chain.value != "active":
        return ""
    listed = judge.listing(root, names, chain.records)  # M:CX-LIST
    if listed.value == "unreadable":  # M:CX-LIST-UNREADABLE
        return f"H-MAD Phase 5 listing is undecidable ({listed.error_file}: {listed.error}); refusing fail-closed. kind=judge-error"
    if listed.value == "not-listed":
        return ""
    verdict = judge.judge(root, listed.selected, chain.records)
    if verdict.decision != "ALLOW":
        relative = listed.selected.relative_to(root).as_posix()
        return f"H-MAD Phase 5 requires a failing test before {relative}: kind={verdict.kind}; {verdict.reason}"
    return ""
```
The first check holds because a name that folds to `.py` with an empty `production` is test-shaped, so the target is not code-like (spec Terms). All names share one directory, so one exempt check covers them. `listed.selected` is one of `names`, whose parent `_relative_target` has placed under `root`, so `relative_to` cannot raise.

**Support module `h-mad/tests/non_py_gate_support.py`** (Task 4 creates it with these; Tasks 5 and 6 add their drivers):
- `build_fixture(root: Path, test_state: str) -> Path`: spec §"Fixture" exactly. `test_state` is one of `"absent"`, `"passing"`, `"failing"`. Creates `root/.agents`, agy's cwd.
- `selection_fixture(root: Path, state: str) -> Path`: the AC-6.5 fixture, `state` is `"S1"` or `"S2"`.
- `two_record_fixture(root: Path, listed: bool) -> Path`: records `f` and `g` both active, `scripts/hard.sh` a hard link to `scripts/tool.sh`, `g.impl-plan.md` invalid UTF-8; with `listed` true `f.impl-plan.md` lists `scripts/tool.sh` with `tests/test_tool.py`, otherwise another file.
- `newline_name_fixture(root: Path, test_state: str) -> Path`: `scripts/alias.sh` a symlink to `scripts/tool\n`, a name ending in a newline; `f.impl-plan.md` lists `scripts/alias.sh` with `tests/test_tool.py`.
- `member_fixture(root: Path, lower: str, upper: str) -> Path`: the AC-11.3 and AC-11.4 variants.
- Every fixture with a listed target and a failing test also gets `tdd_gate_support.build_venv(root / ".venv", with_pytest=True)`, so its ALLOW does not depend on the `python3` on `PATH`.
- `skip_unless_case_insensitive(directory: Path) -> None`: touches a probe file named `a`, calls `pytest.skip` unless `os.path.exists(directory / "A")`, and removes the probe. It uses `os.path.exists`, as `assert_case_insensitive` does: under a patched `os.path.exists`, `Path.exists` still returned `True` on python3.11, so a `Path.exists` helper would not see the patch (reading at `26571a2d`).
- `run_codex(root: Path, relative: str, env: dict) -> Outcome`: `python3` on the real hook by its worktree path, stdin `{"tool_name":"apply_patch","tool_input":{"command":"*** Begin Patch\n*** Update File: RELATIVE\n@@\n-x\n+y\n*** End Patch\n"},"cwd":"ROOT"}`, cwd the root.
- Environments drop every `GIT_*` name, as `test_h_mad_agy_tdd_gate.py`'s `_env` does: a dispatched worker can inherit git's worktree overrides and the fixtures must discover their own repositories.

**New tests in `h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`** (54 nodes). The file holds the RED nodes first, because the judge runs it with `pytest -x`.

RED (20 nodes), each an assertion on the verdict:
- `test_codex_listed_absent_test_denies` (the pin; AC-6.1)
- `test_codex_listed_passing_test_denies` (AC-6.2)
- `test_codex_multi_target_patch_denies_on_the_listed_target` (AC-6.4)
- `test_codex_selection_s2_denies` (AC-6.5)
- `test_codex_symlink_alias_denies` (AC-3.2)
- `test_codex_case_fold_spelling_denies` (AC-3.3; calls `skip_unless_case_insensitive` first)
- `test_codex_hard_link_denies` (AC-3.4)
- `test_codex_unreadable_plan_is_judge_error` (AC-8.1)
- `test_codex_unreadable_state_is_judge_error` (AC-8.2)
- `test_codex_listed_beside_unreadable_absent_test_denies` (FR-8, R-D)
- `test_codex_unlisted_beside_unreadable_is_judge_error` (FR-8, R-D)
- `test_codex_listed_symlink_to_a_newline_name[absent]`
- `test_codex_excluded_member_denies[a.bash]`, `[Makefile]`, `[Dockerfile]`, `[.gitignore]`, `[.dockerignore]`, `[x.md.sh]`, `[x.mdx]` (AC-11.4)
- `test_codex_mixed_hard_links_deny` (AC-11.5)

Controls and preservation, green before and after (34 nodes):
- `test_codex_listed_failing_test_allows` (AC-6.2)
- `test_codex_unlisted_code_like_allows`, `test_codex_unlisted_doc_data_allows` (AC-6.3)
- `test_codex_selection_s1_allows` (AC-6.5)
- `test_codex_residual_spellings_allow[plan-entry-case]`, `[absent-leaf-case]`, `[other-directory-hard-link]` (AC-3.5)
- `test_codex_absent_plan_allows` (AC-8.3)
- `test_codex_doc_data_allows_in_undecidable_states[plan-notes]`, `[plan-readme]`, `[state-notes]`, `[state-readme]` (AC-8.4)
- `test_codex_listed_beside_unreadable_failing_test_allows` (FR-8, R-D)
- `test_codex_listed_symlink_to_a_newline_name[failing]`
- `test_codex_listed_doc_data_allows` (AC-11.1)
- `test_codex_listed_upper_case_doc_data_allows[on-disk]`, `[case-variant]` (AC-11.2; `[case-variant]` calls `skip_unless_case_insensitive` first)
- `test_codex_doc_data_member_allows[.md]`, `[.yaml]`, `[.yml]`, `[.json]`, `[.toml]`, `[.txt]`, `[.rst]`, `[.cfg]`, `[.ini]` (AC-11.3; each lists `x` plus the suffix and `y` plus the upper-cased suffix, and writes both)
- `test_codex_listed_exempt_location_allows[tests]`, `[fixtures]`, `[docs]`
- `test_codex_listed_test_shaped_python_is_skipped`: a listed `scripts/test_helper.py` with the test absent stays ALLOW.
- `test_codex_directory_target_is_skipped`: the existing directory `scripts`, active record.
- `test_codex_no_state_file_allows_a_listed_target`, `test_codex_inactive_record_allows_a_listed_target`
- `test_skip_unless_case_insensitive_skips_on_a_case_sensitive_volume`: first calls the helper unpatched and asserts it returns, which on a case-sensitive volume correctly skips the node; then, under `monkeypatch.context()`, patches `os.path.exists` to return `False` and expects `pytest.raises(pytest.skip.Exception)`. A helper that always skips fails the first arm on this Mac. It lives here because this Task introduces the module.

Stated residual: on a case-sensitive volume the nodes that call the helper report as skipped, a mutant scored on them is not killed there, and the skip count in the summary line is the signal.

**RED split**: 20 failed, 34 passed. Gate on the pin's failure reason and the mutation rows, not on the count alone.

**Acceptance Criteria**:
- [ ] AC-3.1 (codex half): the three codex rows below are killed, each scored on its named test with the matcher intact in the two connection rows.
- [ ] AC-3.2: `test_codex_symlink_alias_denies` passes.
- [ ] AC-3.3: `test_codex_case_fold_spelling_denies` passes.
- [ ] AC-3.4: `test_codex_hard_link_denies` passes, reading `kind=test-missing`, not the `kind=no-test-resolved` a route through the name map would give.
- [ ] AC-3.5: `test_codex_residual_spellings_allow` passes on all three parameters.
- [ ] AC-6.1: `test_codex_listed_absent_test_denies` passes.
- [ ] AC-6.2: `test_codex_listed_passing_test_denies` and `test_codex_listed_failing_test_allows` pass.
- [ ] AC-6.3: `test_codex_unlisted_code_like_allows` and `test_codex_unlisted_doc_data_allows` pass.
- [ ] AC-6.4: `test_codex_multi_target_patch_denies_on_the_listed_target` passes.
- [ ] AC-6.5: `test_codex_selection_s1_allows` and `test_codex_selection_s2_denies` pass.
- [ ] AC-8.1: `test_codex_unreadable_plan_is_judge_error` passes.
- [ ] AC-8.2: `test_codex_unreadable_state_is_judge_error` passes.
- [ ] AC-8.3: `test_codex_absent_plan_allows` passes.
- [ ] AC-8.4: `test_codex_doc_data_allows_in_undecidable_states` passes on all four parameters.
- [ ] FR-8 (R-D): `test_codex_listed_beside_unreadable_failing_test_allows`, `test_codex_listed_beside_unreadable_absent_test_denies` and `test_codex_unlisted_beside_unreadable_is_judge_error` pass.
- [ ] AC-11.1: `test_codex_listed_doc_data_allows` passes.
- [ ] AC-11.2: `test_codex_listed_upper_case_doc_data_allows` passes on both parameters.
- [ ] AC-11.3: `test_codex_doc_data_member_allows` passes on all nine parameters.
- [ ] AC-11.4: `test_codex_excluded_member_denies` passes on all seven parameters.
- [ ] AC-11.5: `test_codex_mixed_hard_links_deny` passes.
- [ ] AC-11.6 (codex half): the nine `DD-CX-` rows are killed.
- [ ] FR-6 order: `test_codex_listed_exempt_location_allows` (all three parameters), `test_codex_listed_test_shaped_python_is_skipped`, `test_codex_directory_target_is_skipped`, `test_codex_no_state_file_allows_a_listed_target` and `test_codex_inactive_record_allows_a_listed_target` pass.
- [ ] `test_skip_unless_case_insensitive_skips_on_a_case_sensitive_volume` passes.
- [ ] The newline-ending name: `test_codex_listed_symlink_to_a_newline_name` passes on both parameters.

**Mutation rows** (19; `file` `hooks/h-mad-codex-tdd-gate.py` and `symbol` `_judge_listed` unless stated).

`codex_gate_listing.json` (6):
- `CX-DOCDATA-VERDICT` (`symbol` `_main_guarded`): find `if is_doc_data(resolved.names):  # M:CX-DOCDATA`, replace `if False:  # M:CX-DOCDATA`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_listed_doc_data_allows`.
- `CX-DOCDATA-DIRECTORY` (`symbol` `_main_guarded`): the same find and replace. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_directory_target_is_skipped`. The mutant makes `_judge_listed` raise `IndexError` on `names[0]`, which reaches `# M:G2` as `kind=judge-error`.
- `CX-NOT-CODE-LIKE`: find `if any(Path(fold_py_suffix(n)).suffix == ".py" for n in resolved.names):  # M:CX-NOT-CODE-LIKE`, replace `if False:  # M:CX-NOT-CODE-LIKE`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_listed_test_shaped_python_is_skipped`.
- `CX-LIST-EXEMPT`: find `if _is_exempt_location(names[0].relative_to(root).as_posix()):  # M:CX-LIST-EXEMPT`, replace `if False:  # M:CX-LIST-EXEMPT`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_listed_exempt_location_allows[tests]`.
- `CX-CHAIN-UNREADABLE`: find `if chain.value == "unreadable":  # M:CX-CHAIN-UNREADABLE`, replace `if False:  # M:CX-CHAIN-UNREADABLE`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_unreadable_state_is_judge_error`.
- `CX-LIST-UNREADABLE`: find `if listed.value == "unreadable":  # M:CX-LIST-UNREADABLE`, replace `if False:  # M:CX-LIST-UNREADABLE`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_unreadable_plan_is_judge_error`.

`listing_connections.json` (2; AC-3.1 connection mutants, matcher intact; the harness's landing check applies):
- `CX-REMOVE`: find `listed = judge.listing(root, names, chain.records)  # M:CX-LIST`, replace `listed = judge.Listing("not-listed", None, None, "")  # M:CX-LIST`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_listed_absent_test_denies`.
- `CX-FORCE`: the same find, replace `listed = judge.Listing("listed", min(names, key=lambda p: p.name), None, "")  # M:CX-LIST`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_unlisted_code_like_allows`.

`listing_matcher.json` (2; `file` `scripts/h_mad_tdd_judge.py`, `symbol` `listing`):
- `CX-CALLEE`: find `per_name = [(name, _match_plans(root, name, records)) for name in names]`, replace `return Listing("not-listed", None, None, "")`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_listed_absent_test_denies`.
- `CX-SELECT`: find `min(listed, key=lambda p: p.name), None, "")  # M:L-SELECT`, replace `max(listed, key=lambda p: p.name), None, "")  # M:L-SELECT`. Test `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_selection_s2_denies`.

`doc_data_definition.json` (9; AC-11.6, `file` `scripts/h_mad_target_identity.py`, module-level `symbol`). Each row's find is the whole `DOC_DATA_SUFFIXES = (` line, its replace removes one suffix, and it is scored on that suffix's node:
- `DD-CX-MD`, `DD-CX-YAML`, `DD-CX-YML`, `DD-CX-JSON`, `DD-CX-TOML`, `DD-CX-TXT`, `DD-CX-RST`, `DD-CX-CFG`, `DD-CX-INI`, removing `.md`, `.yaml`, `.yml`, `.json`, `.toml`, `.txt`, `.rst`, `.cfg`, `.ini` respectively. Tests `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_doc_data_member_allows[.md]`, `[.yaml]`, `[.yml]`, `[.json]`, `[.toml]`, `[.txt]`, `[.rst]`, `[.cfg]`, `[.ini]` respectively.

**Re-anchored existing row** (1, in `shared_gate_policy.json`): `fr6-import-guard-dropped` anchors the whole `_POLICY_IMPORT_ERROR` `try` block of `h-mad/hooks/h-mad-codex-tdd-gate.py`. After `_load_judge,` its find gains the three lines `        is_doc_data,`, `        _is_exempt_location,` and `        fold_py_suffix,`, and its replace gains the same three names at its own 4-space indent. Its test `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_gate_kind[judge-error]` is unchanged. Regression provenance: the block gained names, the mutant's meaning did not.

**Commands**:
```bash
rtk proxy python3.11 -m pytest h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py -q
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/shared_gate_policy.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/codex_gate_listing.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_connections.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_matcher.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_data_definition.json
```
Then the full suite and `--check-anchors` over all of `h-mad/tests/mutation-specs/`.

**Dependencies on other tasks**: Task 2 and Task 3.

---

## Task 5: agy-gate

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py`
**Test support**: `h-mad/tests/non_py_gate_support.py` (gains `run_agy`)
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `h_mad_tdd_judge.listing`
**WIRE-PIN**: `h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_listed_absent_test_denies`

**Description**: FR-7, FR-8 and FR-11 on agy, following FR-6's order and selection rule in the T6–T7 loop. T1–T5 are unchanged and run first. T2a decides a directory before this code, so no directory test is needed here.

**WIRE-PIN RED**: the callee exists (Task 3), so no scaffold is needed. `test_agy_listed_absent_test_denies` drives the real hook and reads `{"decision": "allow"}` where a deny ending `kind=test-missing` is expected: an assertion about the caller.

**Code structure**. One addition to the in-`main` import from `h_mad_target_identity`: `_is_exempt_location`. `is_doc_data` and `fold_py_suffix` go through `identity`, bound by `import h_mad_target_identity as identity`. After the `# T6–T7` comment and before `                production = []`:
```python
                if identity.is_doc_data(resolved.names):  # M:AG-DOCDATA
                    continue
```
`if not production:` followed by `continue` becomes:
```python
                if not production:
                    if any(Path(identity.fold_py_suffix(n)).suffix == ".py" for n in resolved.names):  # M:AG-NOT-CODE-LIKE
                        continue
                    names = [Path(resolved.target).parent / n for n in resolved.names]
                    if _is_exempt_location(names[0].relative_to(root).as_posix()):  # M:AG-LIST-EXEMPT
                        continue
                    chain = judge.read_chain(root, names[0])
                    if chain.value == "unreadable":  # M:AG-CHAIN-UNREADABLE
                        detail = f"{chain.error_file}: {chain.error}".replace("kind=", "kind:")
                        decision = {"decision": "deny", "reason": f"State governing the write is unreadable ({detail}). kind=judge-error"}
                        return 0
                    if chain.value != "active":
                        continue
                    listed = judge.listing(root, names, chain.records)  # M:AG-LIST
                    if listed.value == "unreadable":  # M:AG-LIST-UNREADABLE
                        detail = f"{listed.error_file}: {listed.error}".replace("kind=", "kind:")
                        decision = {"decision": "deny", "reason": f"Listing is undecidable ({detail}). kind=judge-error"}
                        return 0
                    if listed.value == "not-listed":
                        continue
                    verdict = judge.judge(root, listed.selected, chain.records)
                    if verdict.decision != "ALLOW":
                        relative = listed.selected.relative_to(root).as_posix()
                        detail = f"{relative}: {verdict.reason}".replace("kind=", "kind:")
                        decision = {"decision": "deny", "reason": f"Phase 5 requires a failing test before {detail} kind={verdict.kind}"}
                        return 0
                    continue
```
An exception in this block leaves `decision` as `None`, and the `finally` emits the existing `Gate could not reach a judgement. kind=judge-error`.

**Support addition**: `run_agy(root: Path, relative: str, env: dict) -> dict`: `python3` on the real hook by its worktree path, stdin `{"toolCall":{"name":"write_to_file","args":{"TargetFile":"ABSOLUTE"}},"workspacePaths":["ROOT"]}`, cwd `root / ".agents"`, returning the decoded `{"decision": ...}` object.

**New tests in `h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py`** (51 nodes), RED nodes first.

RED (19 nodes):
- `test_agy_listed_absent_test_denies` (the pin; AC-7.1)
- `test_agy_listed_passing_test_denies` (AC-7.2)
- `test_agy_selection_s2_denies` (AC-7.4)
- `test_agy_symlink_alias_denies` (AC-3.2)
- `test_agy_case_fold_spelling_denies` (AC-3.3)
- `test_agy_hard_link_denies` (AC-3.4)
- `test_agy_unreadable_plan_is_judge_error` (AC-8.1)
- `test_agy_unreadable_state_is_judge_error` (AC-8.2)
- `test_agy_listed_beside_unreadable_absent_test_denies` (FR-8, R-D)
- `test_agy_unlisted_beside_unreadable_is_judge_error` (FR-8, R-D)
- `test_agy_listed_symlink_to_a_newline_name[absent]`
- `test_agy_excluded_member_denies[a.bash]`, `[Makefile]`, `[Dockerfile]`, `[.gitignore]`, `[.dockerignore]`, `[x.md.sh]`, `[x.mdx]` (AC-11.4)
- `test_agy_mixed_hard_links_deny` (AC-11.5)

Controls, green before and after (32 nodes):
- `test_agy_listed_failing_test_allows` (AC-7.2)
- `test_agy_unlisted_code_like_allows`, `test_agy_unlisted_doc_data_allows` (AC-7.3)
- `test_agy_selection_s1_allows` (AC-7.4)
- `test_agy_residual_spellings_allow[plan-entry-case]`, `[absent-leaf-case]`, `[other-directory-hard-link]` (AC-3.5)
- `test_agy_absent_plan_allows` (AC-8.3)
- `test_agy_doc_data_allows_in_undecidable_states[plan-notes]`, `[plan-readme]`, `[state-notes]`, `[state-readme]` (AC-8.4)
- `test_agy_listed_beside_unreadable_failing_test_allows` (FR-8, R-D)
- `test_agy_listed_symlink_to_a_newline_name[failing]`
- `test_agy_listed_doc_data_allows` (AC-11.1)
- `test_agy_listed_upper_case_doc_data_allows[on-disk]`, `[case-variant]` (AC-11.2)
- `test_agy_doc_data_member_allows[.md]`, `[.yaml]`, `[.yml]`, `[.json]`, `[.toml]`, `[.txt]`, `[.rst]`, `[.cfg]`, `[.ini]` (AC-11.3)
- `test_agy_listed_exempt_location_allows[tests]`, `[fixtures]`, `[docs]`
- `test_agy_listed_test_shaped_python_is_skipped`
- `test_agy_no_state_file_allows_a_listed_target`, `test_agy_inactive_record_allows_a_listed_target`

**RED split**: 19 failed, 32 passed. Gate on the pin's failure reason and the mutation rows.

**Acceptance Criteria**:
- [ ] AC-3.1 (agy half): the three agy rows below are killed, each scored on its named test.
- [ ] AC-3.2: `test_agy_symlink_alias_denies` passes.
- [ ] AC-3.3: `test_agy_case_fold_spelling_denies` passes.
- [ ] AC-3.4: `test_agy_hard_link_denies` passes.
- [ ] AC-3.5: `test_agy_residual_spellings_allow` passes on all three parameters.
- [ ] AC-7.1: `test_agy_listed_absent_test_denies` passes: `{"decision": "deny", ...}` with a reason ending `kind=test-missing`.
- [ ] AC-7.2: `test_agy_listed_passing_test_denies` and `test_agy_listed_failing_test_allows` pass.
- [ ] AC-7.3: `test_agy_unlisted_code_like_allows` and `test_agy_unlisted_doc_data_allows` pass.
- [ ] AC-7.4: `test_agy_selection_s1_allows` and `test_agy_selection_s2_denies` pass.
- [ ] AC-8.1: `test_agy_unreadable_plan_is_judge_error` passes.
- [ ] AC-8.2: `test_agy_unreadable_state_is_judge_error` passes.
- [ ] AC-8.3: `test_agy_absent_plan_allows` passes.
- [ ] AC-8.4: `test_agy_doc_data_allows_in_undecidable_states` passes on all four parameters.
- [ ] FR-8 (R-D): `test_agy_listed_beside_unreadable_failing_test_allows`, `test_agy_listed_beside_unreadable_absent_test_denies` and `test_agy_unlisted_beside_unreadable_is_judge_error` pass.
- [ ] AC-11.1: `test_agy_listed_doc_data_allows` passes.
- [ ] AC-11.2: `test_agy_listed_upper_case_doc_data_allows` passes on both parameters.
- [ ] AC-11.3: `test_agy_doc_data_member_allows` passes on all nine parameters.
- [ ] AC-11.4: `test_agy_excluded_member_denies` passes on all seven parameters.
- [ ] AC-11.5: `test_agy_mixed_hard_links_deny` passes.
- [ ] AC-11.6 (agy half): the nine `DD-AG-` rows are killed.
- [ ] FR-7 order: `test_agy_listed_exempt_location_allows` (all three parameters), `test_agy_listed_test_shaped_python_is_skipped`, `test_agy_no_state_file_allows_a_listed_target` and `test_agy_inactive_record_allows_a_listed_target` pass.
- [ ] The newline-ending name: `test_agy_listed_symlink_to_a_newline_name` passes on both parameters.

**Mutation rows** (18; `file` `hooks/h-mad-agy-tdd-gate.py` and `symbol` `main` unless stated).

`agy_gate_listing.json` (5):
- `AG-DOCDATA`: find `if identity.is_doc_data(resolved.names):  # M:AG-DOCDATA`, replace `if False:  # M:AG-DOCDATA`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_listed_doc_data_allows`.
- `AG-NOT-CODE-LIKE`: find `if any(Path(identity.fold_py_suffix(n)).suffix == ".py" for n in resolved.names):  # M:AG-NOT-CODE-LIKE`, replace `if False:  # M:AG-NOT-CODE-LIKE`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_listed_test_shaped_python_is_skipped`.
- `AG-LIST-EXEMPT`: find `if _is_exempt_location(names[0].relative_to(root).as_posix()):  # M:AG-LIST-EXEMPT`, replace `if False:  # M:AG-LIST-EXEMPT`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_listed_exempt_location_allows[tests]`.
- `AG-CHAIN-UNREADABLE`: find `if chain.value == "unreadable":  # M:AG-CHAIN-UNREADABLE`, replace `if False:  # M:AG-CHAIN-UNREADABLE`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_unreadable_state_is_judge_error`.
- `AG-LIST-UNREADABLE`: find `if listed.value == "unreadable":  # M:AG-LIST-UNREADABLE`, replace `if False:  # M:AG-LIST-UNREADABLE`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_unreadable_plan_is_judge_error`.

`listing_connections.json` (2):
- `AG-REMOVE`: find `listed = judge.listing(root, names, chain.records)  # M:AG-LIST`, replace `listed = judge.Listing("not-listed", None, None, "")  # M:AG-LIST`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_listed_absent_test_denies`.
- `AG-FORCE`: the same find, replace `listed = judge.Listing("listed", min(names, key=lambda p: p.name), None, "")  # M:AG-LIST`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_unlisted_code_like_allows`.

`listing_matcher.json` (2; `file` `scripts/h_mad_tdd_judge.py`, `symbol` `listing`):
- `AG-CALLEE`: find `per_name = [(name, _match_plans(root, name, records)) for name in names]`, replace `return Listing("not-listed", None, None, "")`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_listed_absent_test_denies`.
- `AG-SELECT`: find `min(listed, key=lambda p: p.name), None, "")  # M:L-SELECT`, replace `max(listed, key=lambda p: p.name), None, "")  # M:L-SELECT`. Test `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_selection_s2_denies`.

`doc_data_definition.json` (9; `file` `scripts/h_mad_target_identity.py`, module-level `symbol`). Each row's find is the whole `DOC_DATA_SUFFIXES = (` line, its replace removes one suffix, and it is scored on that suffix's node:
- `DD-AG-MD`, `DD-AG-YAML`, `DD-AG-YML`, `DD-AG-JSON`, `DD-AG-TOML`, `DD-AG-TXT`, `DD-AG-RST`, `DD-AG-CFG`, `DD-AG-INI`, removing `.md`, `.yaml`, `.yml`, `.json`, `.toml`, `.txt`, `.rst`, `.cfg`, `.ini` respectively. Tests `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_doc_data_member_allows[.md]`, `[.yaml]`, `[.yml]`, `[.json]`, `[.toml]`, `[.txt]`, `[.rst]`, `[.cfg]`, `[.ini]` respectively.

**Re-anchored existing row** (1, in `agy_tdd_gate.json`): `fr4-t7-unreadable-dropped`'s find is 16 spaces of indent plus `if chain.value == "unreadable":`, a substring of the new block's 20-space line, so it would match twice and be refused. Its find and its replace each gain a leading newline, which pins the 16-space line, with `symbol` `main` and its test `tests/test_h_mad_agy_tdd_gate.py::test_unsearchable_chain_denies_although_the_scan_is_inactive` unchanged. Regression provenance: a new sibling line collided with the text, the mutant's meaning did not. `fr4-t6-t7-skipped-when-inactive` still matches once, because `# M:AG-DOCDATA` adds no `production = []`.

**Commands**:
```bash
rtk proxy python3.11 -m pytest h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py -q
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/agy_tdd_gate.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/agy_gate_listing.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_connections.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_matcher.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_data_definition.json
```
Then the full suite and `--check-anchors` over all of `h-mad/tests/mutation-specs/`.

**Dependencies on other tasks**: Task 2, Task 3 and Task 4 (the support module).

---

## Task 6: claude-gate

**Production file**: `h-mad/hooks/h-mad-tdd-gate.sh`
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_non_py.py`, `h-mad/tests/test_h_mad_target_identity.py`, `h-mad/tests/test_h_mad_tdd_gate_judge.py`
**Test support**: `h-mad/tests/non_py_gate_support.py` (gains the Claude drivers and environments)
**Task shape**: `wiring`
**Judge budget**: 120s
**WIRE**: `h-mad/hooks/h-mad-tdd-gate.sh:_read_listing` → `h_mad_tdd_judge.py listing`
**WIRE-PIN**: `h-mad/tests/test_h_mad_tdd_gate_non_py.py::test_claude_listed_absent_test_denies`

**Description**: FR-5, FR-8, FR-11 on Claude, and the NFR process count. Everything up to and including the path exemptions is unchanged, apart from the `# M:H11` tail and the docdata split. The hook stays runnable under macOS `/bin/bash` 3.2, and `test_claude_gate_is_bash_3_2_clean` stays green. `/bin/bash` is the gate's stated constraint, and no bash case-folding construct is added.

**Why a budget**: a real hook call read 0.31 s absent and up to 0.76 s with a listed failing test on the prototype, and this file holds 66 nodes, each with a fixture, so a run reaching its later nodes can pass the 40 s default. The budget only raises the ceiling. It binds this Task's writes on the codex host, whose hook has no `timeout` in `.codex/hooks.json`; agy's hook is capped at 60 in `.agents/hooks.json`.

**WIRE-PIN RED**: the verb exists (Task 3), so no scaffold is needed. `test_claude_listed_absent_test_denies` drives the real hook under the Claude-author arrangement and reads ALLOW where DENY `kind=test-missing` is expected, with `assert_authorship` passing, so the failure is the verdict and not the arrangement. `test_claude_listed_beside_unreadable_absent_test_denies` reads the same way. `test_claude_unlisted_beside_unreadable_is_judge_error` reads ALLOW too; it is unasserted, as an "Either" state.

**The gate does not guard its own edit here.** The installed hooks resolve to `/Users/kimhawk/orca/skills/h-mad` (`readlink ~/.claude/skills/h-mad`, reading at `26571a2d`), which do not judge a `.sh` until this feature lands. So the RED evidence for this one file is the dispatch report and the mutation run, not a gate refusal.

**Code structure.** The `# M:H11` line becomes (only the import list and the tail change):
```bash
CANON_RECORD=$(python3 -c 'import os,sys;sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[1]))),"scripts"));from h_mad_target_identity import canonicalise,emit_canon,emit_doc_data;i=canonicalise(sys.argv[2],sys.argv[3]);emit_canon(i);emit_doc_data(i)' "${BASH_SOURCE[0]}" "${CLAUDE_PROJECT_DIR:-.}" "$TARGET_PATH")  # M:H11
DOC_DATA_LINE=${CANON_RECORD##*$'\n'}; CANON_RECORD=${CANON_RECORD%$'\n'*}
_read_canon
case "$DOC_DATA_LINE" in "docdata yes") DOC_DATA=yes ;; "docdata no") DOC_DATA=no ;; *) _refuse judge-error "invalid docdata line" ;; esac  # M:H-DOCDATA-LINE
```
The guard runs after `_read_canon`, so CANON errors keep their own reasons. A one-line record yields itself on both sides of the split, which the strict parse then refuses.

**The whole `ALL_SUFFIX_NAMES` loop and its allow are replaced, at the same position** (after the path exemptions, before any state read), and the `ALL_NON_PY` loop stays byte-identical:
```bash
[ "$DOC_DATA" = yes ] && _allow  # M:H-DOCDATA
ALL_NON_PY=yes
PRODUCTION_TARGET=
for NAME in "${CANON_NAMES[@]}"; do
  # the existing loop, unchanged, with its != *.py test and its continue
done
if [ "$ALL_NON_PY" = yes ]; then
  [ "$IN_ROOT" = yes ] || _allow  # M:H-LIST-INROOT
  _find_judge
  _read_listing  # M:H-LIST
  TARGET_PATH=$LISTED_TARGET
else
  TARGET_PATH=$PRODUCTION_TARGET
fi
_find_judge
_read_state --target "$TARGET_PATH"  # M:H3
```
The second `_find_judge` starts nothing on the code-like branch: the function returns at once when `JUDGE` is set. `# M:W6` and the `.py` path are unchanged. `/bin/bash -n` must accept the file.

**`_read_listing`, defined beside `_read_state`**:
```bash
_read_listing() {
  local LARGS=() name LOUT LRC file
  for name in "${CANON_NAMES[@]}"; do LARGS[${#LARGS[@]}]=--name; LARGS[${#LARGS[@]}]=${CANON_TARGET%/*}/$name; done
  LOUT=$(python3 "$JUDGE" listing --root "$ROOT_ABS" ${LARGS[@]+"${LARGS[@]}"} 2>/dev/null; printf 'rc=%s' "$?")  # M:W7
  LRC=${LOUT##*rc=}; LOUT=${LOUT%rc=*}; LOUT=${LOUT%$'\n'}
  case "$LOUT" in *$'\n'*|"") _refuse judge-error "listing verb printed zero or several lines" ;; esac  # M:H-LIST-LINES
  [ "$LRC" = 0 ] || _refuse judge-error "listing verb exited rc=$LRC"  # M:H-LIST-RC
  if [ "$LOUT" = 'TDD-LISTING: not-listed' ]; then _allow; fi
  if [[ $LOUT =~ $LISTING_UNREADABLE_RE ]]; then
    file=$(_pct_decode "${BASH_REMATCH[1]}")
    _refuse judge-error "listing is undecidable ($file: ${BASH_REMATCH[2]})"  # M:H-LIST-UNREADABLE
  fi
  if [[ $LOUT =~ $LISTING_LISTED_RE ]]; then
    _pct_capture LISTED_TARGET "${BASH_REMATCH[1]}"  # M:H-LIST-DECODE
    for name in "${CANON_NAMES[@]}"; do
      if [ "$LISTED_TARGET" = "${CANON_TARGET%/*}/$name" ]; then return 0; fi
    done
    _refuse judge-error "listing verb named a target it was not given"  # M:H-LIST-NAME
  fi
  _refuse judge-error "listing verb printed no well-formed listing line"
}
```
The two patterns join the other `*_RE` assignments, each reachable before `_read_listing` runs:
```bash
LISTING_UNREADABLE_RE='^TDD-LISTING: unreadable file=([^ ]+) error=([A-Za-z_-][A-Za-z0-9_-]*)$'
LISTING_LISTED_RE='^TDD-LISTING: listed target=([^ ]+)$'
```
`_pct_capture` is the hook's existing decoder for canonical names; a bare `$(_pct_decode "${BASH_REMATCH[1]}")` strips trailing newlines, and a listed symlink can resolve to a name ending in one. The `${a[@]+...}` form expands nothing for an empty array under `set -u` on bash 3.2; the array cannot be empty here, because an empty name set never gets past the `ALL_TEST_NAMES` loop.

**FR-5 order, as shipped.** Steps 1 and 2 run in one process: the `listing` verb does the state read and then the listing decision (the spec NFR permits this). Step 3: for a listed target `_read_state --target` and the implementer, peer and fallback refusals run unchanged. Step 4: the judge receives the selected listed name. A listed target's chain is read twice by `listing` and `state`, and a third time by the `judge` verb, as for `.py`.

**NFR, as shipped.** An unlisted code-like write where state exists starts 2 extra short Python processes (`# M:W6`, `# M:W7`); the spec ceiling is 3. A doc/data write starts 0 extra in every state. An unlisted code-like write with no `docs/.bkit-memory.json` on the chain starts 0 extra. Prototype reading through a logging `python3` shim: 2, 4 and 2 launches for those three cases.

**Directory targets are unchanged.** Where the chain may hold state, an inactive record included, the unguarded `ALL_TEST_NAMES` loop stops the script under `set -u` on bash 3.2, the verdict is `kind=judge-error`, and `# M:H-DOCDATA` sits after that loop, so the `docdata yes` a directory prints is never read. Residual: a newer `/bin/bash` does not stop on that expansion and reads ALLOW, today as well.

**Support additions** to `h-mad/tests/non_py_gate_support.py`:
- `CLAUDE_AUTHOR_LINE = "TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env"` and `DEFAULT_AUTHOR_LINE = "TDD-IMPLEMENTER: codex chosen=codex switch=none"`.
- `claude_author_env(**extra) -> dict`: `hermetic_env(HMAD_CODEX_UNAVAILABLE="1", HMAD_AGY_UNAVAILABLE="1", **extra)` minus every `GIT_*` name. Every Claude-host case uses it except AC-5.5, including the "Either" rows.
- `default_authorship_env(bin_dir: Path, **extra) -> dict`: AC-5.5's: `hermetic_env(**extra)` with `HMAD_AGY_UNAVAILABLE` removed and a stub `codex` first on `PATH`. The removal is explicit because `DROPPED_ENV` holds `HMAD_CODEX_UNAVAILABLE` and not `HMAD_AGY_UNAVAILABLE`.
- `assert_authorship(env: dict, root: Path, key: str, expected: str = CLAUDE_AUTHOR_LINE) -> None`: runs `h_mad_tdd_judge.py implementer --root ROOT --feature KEY` under `env`, without `--record`, and asserts the whole stdout line equals `expected`. Called before the hook only for the spec's Claude-author and Default rows and for the listed-beside-unreadable and newline-name tests, both with key `f`. It is not called for the "Either" rows, where the line can be `no-record` or `unreadable`, nor for the directory or process-count tests.
- `run_claude(root: Path, target: Path, env: dict, hook: Path = HOOK) -> Outcome`: `/bin/bash` on the hook with stdin `{"tool_name":"Write","tool_input":{"file_path":"ABSOLUTE","content":"x"}}`, cwd the root, `CLAUDE_PROJECT_DIR` set to the root.
- `stub_tree(tmp: Path, listing_stdout: str, listing_rc: int, emit_doc_data_body: str = "") -> Path`: a copy of the hook with a stub `h_mad_tdd_judge.py` (the `listing` verb prints `listing_stdout` and exits `listing_rc`; `state` prints `TDD-STATE: none`) and the real `h_mad_target_identity.py` text with an appended `emit_doc_data` override when the body is non-empty. Returns the hook path.

**New tests in `h-mad/tests/test_h_mad_tdd_gate_non_py.py`** (66 nodes), RED nodes first.

RED (29 nodes):
- `test_claude_listed_absent_test_denies` (the pin; AC-5.1)
- `test_claude_listed_passing_test_denies` (AC-5.2)
- `test_claude_listed_extensionless_absent_test_denies` (AC-5.3)
- `test_claude_default_authorship_refuses_a_listed_target` (AC-5.5; DENY `kind=codex-authorship`)
- `test_claude_selection_s2_denies` (AC-5.8)
- `test_claude_symlink_alias_denies` (AC-3.2)
- `test_claude_case_fold_spelling_denies` (AC-3.3)
- `test_claude_hard_link_denies` (AC-3.4)
- `test_claude_unreadable_plan_is_judge_error` (AC-8.1; also asserts the reason contains `listing is undecidable`)
- `test_claude_unreadable_state_is_judge_error` (AC-8.2)
- `test_claude_listed_beside_unreadable_absent_test_denies` (FR-8, R-D)
- `test_claude_unlisted_beside_unreadable_is_judge_error` (FR-8, R-D)
- `test_claude_listed_symlink_to_a_newline_name[absent]`
- `test_claude_excluded_member_denies[a.bash]`, `[Makefile]`, `[Dockerfile]`, `[.gitignore]`, `[.dockerignore]`, `[x.md.sh]`, `[x.mdx]` (AC-11.4)
- `test_claude_mixed_hard_links_deny` (AC-11.5)
- `test_claude_listing_zero_lines_is_judge_error` (reason contains `zero or several lines`)
- `test_claude_listing_several_lines_is_judge_error` (reason contains `zero or several lines`)
- `test_claude_listing_nonzero_exit_is_judge_error`: stub prints `TDD-LISTING: not-listed` and exits 2.
- `test_claude_listing_unrecognised_line_is_judge_error`
- `test_claude_listing_foreign_target_is_judge_error`: stub prints `TDD-LISTING: listed target=%2Felsewhere`.
- `test_claude_malformed_docdata_line_is_judge_error`: override prints `docdata maybe`; stub prints `TDD-LISTING: not-listed`; reason contains `invalid docdata line`.
- `test_claude_missing_docdata_line_is_judge_error`: override prints nothing, so the split eats the last CANON line and `_read_canon` refuses on its own reason; kind only.
- `test_claude_process_count[unlisted-with-state]`: expected 4 launches; RED reads 2.

Controls and preservation, green before and after (37 nodes):
- `test_claude_listed_failing_test_allows` (AC-5.2)
- `test_claude_unlisted_code_like_allows`, `test_claude_unlisted_doc_data_allows` (AC-5.4)
- `test_claude_default_authorship_allows_unlisted_doc_data` (AC-5.5)
- `test_claude_no_state_file_allows_a_listed_target`, `test_claude_inactive_record_allows_a_listed_target` (AC-5.6)
- `test_claude_listed_exempt_location_allows[tests]`, `[fixtures]`, `[docs]` (AC-5.7 is `[tests]`)
- `test_claude_selection_s1_allows` (AC-5.8)
- `test_claude_residual_spellings_allow[plan-entry-case]`, `[absent-leaf-case]`, `[other-directory-hard-link]` (AC-3.5)
- `test_claude_absent_plan_allows` (AC-8.3)
- `test_claude_doc_data_allows_in_undecidable_states[plan-notes]`, `[plan-readme]`, `[state-notes]`, `[state-readme]` (AC-8.4)
- `test_claude_listed_beside_unreadable_failing_test_allows` (FR-8, R-D)
- `test_claude_listed_symlink_to_a_newline_name[failing]`: the real killer of `# M:H-LIST-DECODE`.
- `test_claude_listed_doc_data_allows` (AC-11.1)
- `test_claude_listed_upper_case_doc_data_allows[on-disk]`, `[case-variant]` (AC-11.2)
- `test_claude_doc_data_member_allows[.md]`, `[.yaml]`, `[.yml]`, `[.json]`, `[.toml]`, `[.txt]`, `[.rst]`, `[.cfg]`, `[.ini]` (AC-11.3)
- `test_claude_out_of_root_code_like_allows_beside_unreadable_state`: `CLAUDE_PROJECT_DIR` holds an unparsable `docs/.bkit-memory.json`, and the write targets a `.sh` in a second git repository outside the root.
- `test_claude_directory_stays_judge_error_where_state_may_exist`: skips when `/bin/bash` is not 3.2, on the residual above.
- `test_claude_directory_allows_where_no_state_can_exist`
- `test_claude_process_count[doc-data-with-state]` (2 launches), `[unlisted-without-state]` (2 launches)

**Modified existing tests**:
- `h-mad/tests/test_h_mad_target_identity.py::test_py_suffixes_match_bash_fold` (RED): `*.md|*.yaml` leaves the marker tuple, which keeps `# M:H6` and `!= *.py`, and the test gains two assertions: the `# M:H11` line contains `emit_doc_data(i)`, and `ALL_SUFFIX_NAMES` does not occur in the hook. Regression provenance: the marker pinned a per-name classification site that no longer exists, not a defect, and folding is irrelevant to doc/data (`fold_py_suffix` changes only `.py` spellings). The suffix pin is Task 2's.
- `h-mad/tests/test_h_mad_tdd_gate_judge.py` (no RED; no assertion changes): both stub `h_mad_target_identity.py` modules (the `_tree_b` helper and the CANON-variant test, census `git grep -n 'def emit_canon' -- h-mad/tests`, 2 matching lines) gain `def emit_doc_data(record):` printing `docdata no`. Provenance: a stub models the module the hook imports, and the hook now imports one more name. Any other stub without `emit_doc_data` makes the gate refuse `judge-error`.

**RED split**: 30 failed (29 in the new file, plus `test_py_suffixes_match_bash_fold`), 37 passed in the new file. Gate on the pin's failure reason and the mutation rows.

**Acceptance Criteria**:
- [ ] AC-3.1 (Claude half): the three Claude rows below are killed, each scored on its named test under the Claude-author arrangement, so no authorship refusal stands between the mutant and the judge.
- [ ] AC-3.2: `test_claude_symlink_alias_denies` passes.
- [ ] AC-3.3: `test_claude_case_fold_spelling_denies` passes.
- [ ] AC-3.4: `test_claude_hard_link_denies` passes.
- [ ] AC-3.5: `test_claude_residual_spellings_allow` passes on all three parameters.
- [ ] AC-5.1: `test_claude_listed_absent_test_denies` passes.
- [ ] AC-5.2: `test_claude_listed_passing_test_denies` and `test_claude_listed_failing_test_allows` pass.
- [ ] AC-5.3: `test_claude_listed_extensionless_absent_test_denies` passes.
- [ ] AC-5.4: `test_claude_unlisted_code_like_allows` and `test_claude_unlisted_doc_data_allows` pass.
- [ ] AC-5.5: `test_claude_default_authorship_refuses_a_listed_target` and `test_claude_default_authorship_allows_unlisted_doc_data` pass.
- [ ] AC-5.6: `test_claude_no_state_file_allows_a_listed_target` and `test_claude_inactive_record_allows_a_listed_target` pass.
- [ ] AC-5.7: `test_claude_listed_exempt_location_allows[tests]` passes.
- [ ] AC-5.8: `test_claude_selection_s1_allows` and `test_claude_selection_s2_denies` pass.
- [ ] AC-8.1: `test_claude_unreadable_plan_is_judge_error` passes.
- [ ] AC-8.2: `test_claude_unreadable_state_is_judge_error` passes.
- [ ] AC-8.3: `test_claude_absent_plan_allows` passes.
- [ ] AC-8.4: `test_claude_doc_data_allows_in_undecidable_states` passes on all four parameters.
- [ ] FR-8 (R-D): `test_claude_listed_beside_unreadable_failing_test_allows`, `test_claude_listed_beside_unreadable_absent_test_denies` and `test_claude_unlisted_beside_unreadable_is_judge_error` pass.
- [ ] AC-11.1: `test_claude_listed_doc_data_allows` passes.
- [ ] AC-11.2: `test_claude_listed_upper_case_doc_data_allows` passes on both parameters.
- [ ] AC-11.3: `test_claude_doc_data_member_allows` passes on all nine parameters.
- [ ] AC-11.4: `test_claude_excluded_member_denies` passes on all seven parameters.
- [ ] AC-11.5: `test_claude_mixed_hard_links_deny` passes.
- [ ] AC-11.6 (Claude half): the nine `DD-CL-` rows are killed.
- [ ] NFR: `test_claude_process_count` passes on all three parameters.
- [ ] FR-3 transport: `test_claude_listing_zero_lines_is_judge_error`, `test_claude_listing_several_lines_is_judge_error`, `test_claude_listing_nonzero_exit_is_judge_error`, `test_claude_listing_unrecognised_line_is_judge_error` and `test_claude_listing_foreign_target_is_judge_error` pass.
- [ ] FR-11 transport: `test_claude_malformed_docdata_line_is_judge_error` and `test_claude_missing_docdata_line_is_judge_error` pass.
- [ ] Scope: `test_claude_out_of_root_code_like_allows_beside_unreadable_state`, `test_claude_directory_stays_judge_error_where_state_may_exist` and `test_claude_directory_allows_where_no_state_can_exist` pass.
- [ ] The newline-ending name: `test_claude_listed_symlink_to_a_newline_name` passes on both parameters.
- [ ] `test_py_suffixes_match_bash_fold` and every existing test in `h-mad/tests/test_h_mad_tdd_gate_judge.py` pass, with no assertion changed in the latter.

**Mutation rows** (22; `file` `hooks/h-mad-tdd-gate.sh` unless stated). Rows in the hook carry no `symbol`.

`claude_gate_listing.json` (9):
- `H-DOCDATA`: find `[ "$DOC_DATA" = yes ] && _allow  # M:H-DOCDATA`, replace `:  # M:H-DOCDATA`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_listed_doc_data_allows`.
- `H-DOCDATA-LINE`: find `*) _refuse judge-error "invalid docdata line" ;; esac  # M:H-DOCDATA-LINE`, replace `*) DOC_DATA=no ;; esac  # M:H-DOCDATA-LINE`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_malformed_docdata_line_is_judge_error`.
- `H-LIST-LINES`: find `` case "$LOUT" in *$'\n'*|"") _refuse judge-error "listing verb printed zero or several lines" ;; esac  # M:H-LIST-LINES ``, replace `:  # M:H-LIST-LINES`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_listing_several_lines_is_judge_error`, killed on the reason: the prototype mutant still read `kind=judge-error`, with `listing verb printed no well-formed listing line`.
- `H-LIST-RC`: find `[ "$LRC" = 0 ] || _refuse judge-error "listing verb exited rc=$LRC"  # M:H-LIST-RC`, replace `:  # M:H-LIST-RC`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_listing_nonzero_exit_is_judge_error`.
- `H-LIST-UNREADABLE`: find `_refuse judge-error "listing is undecidable ($file: ${BASH_REMATCH[2]})"  # M:H-LIST-UNREADABLE`, replace `:  # M:H-LIST-UNREADABLE`. It falls through to the last refusal, also `judge-error`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_unreadable_plan_is_judge_error`, killed on the reason.
- `H-LIST-DECODE`: find `_pct_capture LISTED_TARGET "${BASH_REMATCH[1]}"  # M:H-LIST-DECODE`, replace `LISTED_TARGET=$(_pct_decode "${BASH_REMATCH[1]}")  # M:H-LIST-DECODE`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_listed_symlink_to_a_newline_name[failing]`.
- `H-LIST-NAME`: find `_refuse judge-error "listing verb named a target it was not given"  # M:H-LIST-NAME`, replace `return 0  # M:H-LIST-NAME`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_listing_foreign_target_is_judge_error`.
- `H-LIST-INROOT`: find `[ "$IN_ROOT" = yes ] || _allow  # M:H-LIST-INROOT`, replace `:  # M:H-LIST-INROOT`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_out_of_root_code_like_allows_beside_unreadable_state`. Prototype reading: on a readable state and on an unreadable plan with a readable state, the guarded hook reads ALLOW; the mutant reads ALLOW on the readable state and DENY `kind=judge-error` on either unreadable arrangement, so a test on a readable state could not kill it.
- `H-NO-DIR-ALLOW`: find `_chain_may_hold_state "$ROOT_ABS" "$TARGET_PATH" || _allow`, replace `[ "$DOC_DATA" = yes ] && _allow; _chain_may_hold_state "$ROOT_ABS" "$TARGET_PATH" || _allow`, the new allow path this feature forbids for a directory. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_directory_stays_judge_error_where_state_may_exist`.

`listing_connections.json` (2):
- `CL-REMOVE`: find `  _read_listing  # M:H-LIST`, replace `  _allow  # M:H-LIST`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_listed_absent_test_denies`.
- `CL-FORCE`: the same find, replace `  LISTED_TARGET=$CANON_TARGET  # M:H-LIST`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_unlisted_code_like_allows`, which asserts ALLOW; the mutant gives a DENY of any kind (P5-1: under the Claude-author arrangement it reaches the judge as `no-test-resolved`; under default authorship it would be a codex-authorship refusal), so the control asserts the decision, not a kind.

`listing_matcher.json` (2; `file` `scripts/h_mad_tdd_judge.py`, `symbol` `listing`):
- `CL-CALLEE`: find `per_name = [(name, _match_plans(root, name, records)) for name in names]`, replace `return Listing("not-listed", None, None, "")`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_listed_absent_test_denies`.
- `CL-SELECT`: find `min(listed, key=lambda p: p.name), None, "")  # M:L-SELECT`, replace `max(listed, key=lambda p: p.name), None, "")  # M:L-SELECT`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_selection_s2_denies`.

`doc_data_definition.json` (9; `file` `scripts/h_mad_target_identity.py`, module-level `symbol`). Each row's find is the whole `DOC_DATA_SUFFIXES = (` line, its replace removes one suffix, and it is scored on that suffix's node:
- `DD-CL-MD`, `DD-CL-YAML`, `DD-CL-YML`, `DD-CL-JSON`, `DD-CL-TOML`, `DD-CL-TXT`, `DD-CL-RST`, `DD-CL-CFG`, `DD-CL-INI`, removing `.md`, `.yaml`, `.yml`, `.json`, `.toml`, `.txt`, `.rst`, `.cfg`, `.ini` respectively. Tests `tests/test_h_mad_tdd_gate_non_py.py::test_claude_doc_data_member_allows[.md]`, `[.yaml]`, `[.yml]`, `[.json]`, `[.toml]`, `[.txt]`, `[.rst]`, `[.cfg]`, `[.ini]` respectively.

**Re-anchored existing rows** (2, in `claude_gate_judge_wiring.json`): `H11` and `CG-CANON` anchor the `# M:H11` line. Each find becomes the new line, and each replace keeps its existing `Identity(...)` construction, imports `Identity,emit_canon,emit_doc_data`, binds the record to `i`, and ends `;emit_canon(i);emit_doc_data(i)`, so the mutants still run. `H3` and `CG-PARENT` anchor lines this Task does not edit.

**Commands**:
```bash
rtk proxy python3.11 -m pytest h-mad/tests/test_h_mad_tdd_gate_non_py.py h-mad/tests/test_h_mad_target_identity.py h-mad/tests/test_h_mad_tdd_gate_judge.py -q
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/claude_gate_listing.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_connections.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_matcher.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_data_definition.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/claude_gate_judge_wiring.json
```
Then the full suite and `--check-anchors` over all of `h-mad/tests/mutation-specs/`.

**Dependencies on other tasks**: Task 2, Task 3 and Task 5 (the support module; the order is codex, agy, Claude, so that a CLI-only defect cannot be mistaken for a matcher defect).

---

## Task 7: prose

**Production file**: `h-mad/references/codex-implementer-prompt.md`, `h-mad/references/codex-runtime.md`, `h-mad/references/phase5-substeps.md`, `h-mad/references/helper-scripts.md`
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_docs.py`
**Task shape**: `new-behaviour`

**Description**: FR-10. Every prose surface that states which files the Phase-5 write gates judge, or whose writes the Claude-side authorship refusals cover, states the shipped five-part rule. All four production files are `.md`, so the gates allow them whatever Task lists them; the discipline here is the doc tests. Every sentence below avoids all eight swept branches.

**Code structure**: none; the deliverable is this literal text.

Surface 3, `h-mad/references/phase5-substeps.md`. The first sentence of the gate-scope paragraph is replaced by this anchor, on one line, which must occur exactly once in `doc_text(SKILL)`:

`The gates judge production `.py`, and a code-like file such as a `.sh` script or an extensionless launcher when a Task's **Production file** line lists it; test files, docs, doc/data files (`.md` `.yaml` `.yml` `.json` `.toml` `.txt` `.rst` `.cfg` `.ini`, listed or not) and unlisted code-like files are allowed.`

The docs-first sentences follow unchanged, so the four docs-first tokens stay in the paragraph after the anchor. `Both gates apply this same rule.` becomes `All three gates apply this same rule.`

Surface 4, the same file's `**FR-3 — Claude-side authorship.**` bullet: "refuses Claude's production-`.py` write", which wraps across two lines in the file, becomes "refuses Claude's write to production `.py` or to a listed code-like file".

Surface 2, `h-mad/references/codex-runtime.md` §"Trust boundary": "production-Python writes" becomes "writes to production `.py` and to listed code-like files (such as a `.sh` script a Task's **Production file** line names)".

Surface 1, `h-mad/references/codex-implementer-prompt.md`, the bullets under the `Hook: ` line:
- The test-file bullet: "Both gates judge a path by its resolved identity" becomes "All three gates judge a path by its resolved identity", and "a target neither gate can resolve" becomes "a target no gate can resolve".
- The doc/data bullet becomes: `- The path is a doc/data file — every resolved name ends in `.md`, `.yaml`, `.yml`, `.json`, `.toml`, `.txt`, `.rst`, `.cfg` or `.ini`, in any case — allowed, even when a Task lists it.`
- The production bullet opens: "For production `.py` (any case of the suffix, `.PY` included), ".
- A new bullet after it: `- For a code-like file — a `.sh` script, an extensionless launcher, any suffix outside the nine — that a Task's **Production file** line lists, the test comes from that Task only (there is no name map); allow the write only if it exists and pytest's summary shows `N failed`. An unlisted code-like file is allowed.`

All existing tokens of `test_hook_bullets_state_the_shipped_rule` remain, and no angle bracket is introduced into the bullets.

`h-mad/references/helper-scripts.md`, the `h_mad_tdd_judge.py` entry: its "`state` and `judge` verbs emit `TDD-STATE:` and `TDD-JUDGE:` verdict tokens" sentence gains the `listing` verb and its one-line `TDD-LISTING:` token with its three values, `listed`, `not-listed` and `unreadable`.

**Not edited, with the reason**: `allowed unconditionally` stays true for the test-file and docs-first bullets; `is not gated` in `phase5-substeps.md` states the unchanged docs-first exemption; `production-code write` and `production write` in `agy-runtime.md` and `grok-runtime.md` stay true, because a listed `.sh` is production code.

**Test edits in `h-mad/tests/test_h_mad_tdd_gate_docs.py`** (all RED):
- `test_gate_prose_has_no_retired_phrasing` (new; AC-10.1), parametrised with one node per branch, each with an explicit id:

  | id | branch |
  |---|---|
  | `production-python` | `production-Python` |
  | `suffix-in-any-case` | `a .\.py. suffix in any case` |
  | `never-gated` | `never gated` |
  | `only-production` | `only production` |
  | `production-dot-py` | `production-.\.py.` |
  | `markdown-yaml` | `markdown / yaml` |
  | `both-gates` | `Both gates` |
  | `neither-gate` | `neither gate` |

  Each node runs `git -C REPO_ROOT grep -n -E BRANCH -- h-mad/SKILL.md h-mad/references h-mad/agents h-mad/invariants.base.md` and asserts exit 1 with empty stdout, so a `git grep` error (128) fails rather than passes. **By design the test fails outside a git checkout**, for the same reason. The test file is outside the corpus, so its own needles cannot score. RED reading at `26571a2d`: the eight-branch command prints 7 matching lines in 3 files, and each node fails. Residual: a rule statement outside the four locators that uses none of the eight phrasings, and a phrasing split across a hard wrap.
- `test_hook_bullets_state_the_shipped_rule` (modified; AC-10.2): keeps today's tokens and adds each of the nine doc/data suffix spellings, `Production file` and `.sh`, eleven tokens, each matching 0 lines of the bullet block today.
- `test_skill_states_the_docs_first_component_rule` (modified; AC-10.3): the new anchor above replaces the old one, `text.count(anchor) == 1`, and the paragraph after it holds `FIRST component`, `relative to the project root`, `` `docs` ``, `` `src/docs/foo.py` `` and `All three gates`. RED on anchor count 0. Regression provenance: the anchor and `Both gates` are stale contracts (spec FR-10); the four docs-first tokens are current behaviour and stay unchanged.
- `test_helper_scripts_registers_the_judge` (modified): gains `listing` and `TDD-LISTING:`. RED on `TDD-LISTING:`.

**RED split**: 11 failed (8 phrasing nodes plus the 3 modified tests). No new controls. The module's other tests stay green.

**Acceptance Criteria**:
- [ ] AC-10.1: `test_gate_prose_has_no_retired_phrasing` passes on all eight nodes, and `git grep -n -E 'production-Python|a .\.py. suffix in any case|never gated|only production|production-.\.py.|markdown / yaml|Both gates|neither gate' -- h-mad/SKILL.md h-mad/references h-mad/agents h-mad/invariants.base.md` prints no line.
- [ ] AC-10.2: `test_hook_bullets_state_the_shipped_rule` passes, and the whole `test_h_mad_tdd_gate_docs.py` module passes.
- [ ] AC-10.3: `test_skill_states_the_docs_first_component_rule` passes.
- [ ] `test_helper_scripts_registers_the_judge` passes with the tokens `listing` and `TDD-LISTING:`.

**Mutation rows**: none. AC-9.3 covers FR-1, FR-3 to FR-8 and FR-11; each sentence here is pinned by a doc test, and the full suite carries the doc-derived tests other files hold.

**Commands**:
```bash
rtk proxy python3.11 -m pytest h-mad/tests/test_h_mad_tdd_gate_docs.py -q
git grep -n -E 'production-Python|a .\.py. suffix in any case|never gated|only production|production-.\.py.|markdown / yaml|Both gates|neither gate' -- h-mad/SKILL.md h-mad/references h-mad/agents h-mad/invariants.base.md
```
The `git grep` must print no line. Then the full suite and `--check-anchors` over all of `h-mad/tests/mutation-specs/`.

**Dependencies on other tasks**: Task 6 (the prose states what the gates do once all three ship).

---

## Task 8: fr9-driver

**Production file**: `docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py`
**Test file**: `h-mad/tests/test_h_mad_fr9_drive_refusals.py`
**Task shape**: `new-behaviour`

**Description**: FR-9. A committed probe, stdlib only, outside pytest's `testpaths` (`h-mad/tests handoff/tests handoff/scripts`) and exempt from all three gates as a root-`docs/` file. Usage: `python3.11 -I docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py --scenario fixture|replay --side after|before --host claude|codex|agy --out EVIDENCE_DIR`. One host per invocation, so no host's run can cover another's. The tree under test is the current directory's `git rev-parse --show-toplevel`, not the driver's location. The driver calls no agent CLI and does not run the `verify-hmad-gates` helper, whose installed paths resolve to another checkout.

**Code structure**:
```python
def main(argv: list[str] | None = None) -> int: ...
def _replay_base(top: Path) -> str: ...            # missing-base, base-is-head
def _check_hook_identity(top: Path, hook: Path) -> dict: ...  # dirty-hooks, hook-outside-tree, hook-blob-mismatch
def _copy_plan(top: Path, base: str, root: Path) -> dict: ...  # plan-blob-mismatch
def _check_authorship(judge: Path, root: Path, key: str, env: dict, out: Path) -> None: ...  # authorship-line
def _refuse(reason: str) -> int: ...               # prints FR9-DRIVE: UNREADABLE plus the reason, returns 2
```

**Hermetic environment.** `subprocess.run(env=...)` with `HOME`, `PATH`, `LANG` (default `en_US.UTF-8`) and `TMPDIR`, the method of `hermetic()` in `/Users/kimhawk/orca/skills/.claude/skills/verify-hmad-gates/bin/hmad-verify.sh`, a read-only reference. On the Claude host only, both sides, three additions, all recorded: `CLAUDE_PROJECT_DIR` set to the scratch root, `HMAD_CODEX_UNAVAILABLE=1` and `HMAD_AGY_UNAVAILABLE=1`.

**Authorship check.** Before each Claude-host verdict the driver runs that side's `h_mad_tdd_judge.py implementer --root ROOT --feature KEY`, without `--record`, in the hook's environment. `KEY` is `f` for the fixture and `exec-missing-report-recovery` for the replay. It stores the line as `implementer.txt` and requires exactly `TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env`. Any other line refuses `authorship-line`: spec §"Fixture" makes such a run invalid rather than failed.

**Real stdin entry points**: Claude, `/bin/bash HOOK`, stdin `{"tool_name":"Write","tool_input":{"file_path":"ABSOLUTE","content":"x"}}`, cwd the root. codex, `python3 HOOK`, stdin `{"tool_name":"apply_patch","tool_input":{"command":"*** Begin Patch\n*** Update File: RELATIVE\n@@\n-x\n+y\n*** End Patch\n"},"cwd":"ROOT"}`, cwd the root. agy, `python3 HOOK`, stdin `{"toolCall":{"name":"write_to_file","args":{"TargetFile":"ABSOLUTE"}},"workspacePaths":["ROOT"]}`, cwd `ROOT/.agents`, which the driver creates in every scratch root on both scenarios, because `subprocess.run` raises `FileNotFoundError` on a missing cwd.

**Refusal order.** Each prints `FR9-DRIVE: UNREADABLE` plus the reason, exit 2.
1. Arguments: `no-before-side`.
2. On `--scenario replay`, either side: `missing-base`, then `base-is-head`. These run before any hook check, so a replay with no base reports that.
3. On the after side, for the executed hook, in this order: `dirty-hooks` (`git status --porcelain -- h-mad` prints a line), then **`hook-outside-tree` (the realpath is not under `git rev-parse --show-toplevel`), then `hook-blob-mismatch` (`git hash-object` differs from `git rev-parse HEAD:PATH`)**. The realpath check must run first: a committed symlink to an outside file has an empty `git status`, a `git hash-object` that follows the link and a `HEAD:PATH` that is the link text, so the blob check would otherwise print `hook-blob-mismatch` on the `hook-outside-tree` fixture. Design v1.4 states them in the other order; this plan's order is the fix.
4. On `--scenario replay`, the copied plan: `plan-blob-mismatch`.
5. On the Claude host, before each verdict: `authorship-line`.

**Evidence is taken before the Phase 7 push.** Once this branch is on `origin/main`, `git merge-base HEAD origin/main` returns HEAD, so the before tree equals the after tree and AC-9.4's incident row reads DENY on both sides; hence `base-is-head`. Residual: a base other than HEAD whose `h-mad/` equals the commit under test passes this check, and its incident row then reads as a FAIL row.

**Before tree (D14, R15).** The base is `git merge-base HEAD origin/main`, re-derived at run time and recorded, never pinned here and never from the local `main` ref. Reading at `26571a2d`: `e097dfcb`. The driver materialises `git archive BASE h-mad | tar -x -C A_MKTEMP_DIR`, which only reads the repository, and records the before-side hook realpath and sha256 per host. Taking the whole `h-mad/` tree covers P5-2 and PF-1 by construction:
- **P5-2.** The judge's one lazy import of `h_mad_state_write` (`grep -n 'import h_mad_state_write' h-mad/scripts/h_mad_tdd_judge.py`, inside `main`'s `implementer --record` branch), and that module's module-level imports of `h_mad_bkit_guard`, `h_mad_state_ownership` and `h_mad_state_validate`.
- **PF-1.** `h_mad_wire_registry`'s `from h_mad_assemble_tdd import misrooted_candidates`, only inside its `register` CLI branch, which is not on any gate's path.
- **PF-2.** `grep -c 'h_mad_mutation_harness.py' h-mad/scripts/h_mad_target_identity.py` prints 2 matching lines, the `SAFE_HMAD_SCRIPT_OPTIONS` key and the comparison in `_safe_hmad_script`; no line imports it, and no AC-9.4 row writes through a shell command, so a harness change at the base does not move a before reading.

**Replay repo (AC-9.4, AC-9.5).** Built by `git init` in a mktemp dir, on both sides from the same base. It writes `docs/01-plan/features/exec-missing-report-recovery.impl-plan.md` from `git cat-file blob BASE:THAT_PATH` bytes, records the commit, `git rev-parse BASE:THAT_PATH` and the copy's sha256, and requires `git hash-object` of the copy to equal the blob id. Reading at `26571a2d`: base `e097dfcb`, blob `fef082989979cd8a7a1c0f896db4673a14e078e2`, the same blob the spec read. It writes `docs/.bkit-memory.json` with `orchestrator_state.exec-missing-report-recovery = {"phase": "step5"}`, the same record for all three hosts and with no `implementer` key. It creates `h-mad/scripts/hmad-dispatch.sh`, `h-mad/SKILL.md` and `h-mad/scripts/h_mad_derive_test_path.sh`, whose content does not affect the verdict. It runs `h-mad/tests/test_hmad_dispatch_exec.py` absent, then as `def test_red(): assert False`, and drives the four AC-9.4 rows.

OPEN-DECISION: a plan path absent at the base commit crashes the driver with no token — resolve in 5d. `git cat-file blob BASE:THAT_PATH` exits 128 on such a path (reading at `26571a2d` on a scratch repo), and today the path exists at the base, so this is reachable only if `origin/main` archives or renames that plan. Option A, the design's residual: exit 1 with no token, read as no verdict. Option B: a ninth refusal `FR9-DRIVE: UNREADABLE plan-absent-at-base`, a marker `# M:D-PLAN-ABSENT`, one more node in `test_fr9_driver_refuses`, and one more row in `fr9_drive_refusals.json`. Both satisfy AC-9.4 and AC-9.5, since neither produces a reading. This plan counts Option A; choosing B moves the refusal count from 8 to 9 and the mutation total from 88 to 89. Recommendation: B, because base invariant §"Audit-gate signal discipline" prefers a token, and it is cheap.

**Fixture scenario (AC-9.1).** Spec §"Fixture" verbatim, under the Claude-author arrangement on the Claude host: three rows per host, after side only.

**Interpreter.** Each scratch root gets `ROOT/.venv`, built with `sys.executable -I -m venv --without-pip --system-site-packages` on both sides and every host, and `provenance.json` records that interpreter. The judge's `select_interpreter` finds it by walking up from the test, so a listed-failing row does not depend on the `python3` the hermetic `PATH` offers. The driver must run under an interpreter whose site-packages hold pytest, hence `python3.11`; otherwise the listed-failing rows read `pytest-missing` and print `FR9-DRIVE: FAIL`, never a pass.

**Evidence folder.** One folder for the whole proof, chosen once before the first invocation and passed as `--out` to all nine: `OUT=docs/03-analysis/probes/gate-non-py-production-files/fr9/$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short=12 HEAD)`. It holds one `NNN-SCENARIO-SIDE-HOST-CASE/` directory per call, with `stdin.json`, `stdout`, `stderr`, `rc`, `argv.json`, `env.json`, `hook.json` (path, sha256, blob ids) and, on the Claude host, `implementer.txt`; `provenance.json`, one object appended per invocation (scenario, side, host, commit under test, base, plan blob, copy sha256, `python3` realpath and version); and `readings.tsv`, one row per call in the host's own verdict form. `NNN` continues across invocations.

**Verdict token.** The driver compares this invocation's rows against the AC-9.1 or AC-9.4 table and prints `FR9-DRIVE: PASS rows=N mismatched=0` or `FR9-DRIVE: FAIL rows=N mismatched=M`, exit 0 on either. A before reading other than ALLOW is a FAIL row, never a pass (spec AC-9.4).

**New tests in `h-mad/tests/test_h_mad_fr9_drive_refusals.py`** (8 nodes, all RED). `docs/` is outside `testpaths`, so these hold the driver. Each node runs the real driver by path under `sys.executable -I`, with the current directory in a throwaway `git init` repo holding committed copies of `h-mad/hooks` and `h-mad/scripts`, and asserts the token line and exit 2. The test names the probes directory, so `h_mad_archive_feature.py` keeps the directory in place. The test's environment drops every `GIT_*` name before adding its own.

RED: the Task first writes the driver as an argument parser that prints nothing and exits 0, so each node fails on the missing token line, not on a missing file. `test_fr9_driver_refuses`, parametrised with these ids and arguments:

| id | arguments | fixture |
|---|---|---|
| `no-before-side` | `--scenario fixture --side before --host claude` | none beyond the repo |
| `dirty-hooks` | `--scenario fixture --side after --host claude` | an uncommitted edit to `h-mad/hooks/h-mad-tdd-gate.sh` |
| `hook-outside-tree` | `--scenario fixture --side after --host claude` | that hook committed as a symlink to a file outside the repo |
| `hook-blob-mismatch` | `--scenario fixture --side after --host claude` | an edit to that hook hidden by `git update-index --assume-unchanged`, so `git status --porcelain` prints nothing and `git hash-object` differs from `HEAD:PATH` |
| `authorship-line` | `--scenario fixture --side after --host claude` | a committed `h_mad_tdd_judge.py` stub whose `implementer` verb prints `TDD-IMPLEMENTER: codex chosen=codex switch=none` |
| `missing-base` | `--scenario replay --side after --host claude` | no `refs/remotes/origin/main` |
| `base-is-head` | `--scenario replay --side after --host claude` | `refs/remotes/origin/main` at HEAD |
| `plan-blob-mismatch` | `--scenario replay --side after --host claude` | a base commit holding a CRLF plan, a later HEAD, and `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=core.autocrlf`, `GIT_CONFIG_VALUE_0=true` in the driver's environment, so `git hash-object` normalises the copy and differs from the blob id |

`plan-blob-mismatch` uses `--side after` only, by necessity: under that same configuration `git archive` converts the before tree to CRLF (reading at `26571a2d`: a scratch `x.sh` archived with `\r\n` line ends, shebang included), so a `--side before` node would run a broken hook rather than reach this refusal.

**RED split**: 8 failed, 0 passed. The FR-9 verdict rows have no RED: they are measurements, read from `FR9-DRIVE:`.

**Run order**, all before the Phase 7 push, on a commit holding Tasks 1 to 7 and the driver, with `git status --porcelain -- h-mad` printing nothing:
```bash
OUT=docs/03-analysis/probes/gate-non-py-production-files/fr9/$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short=12 HEAD)
D=docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py
python3.11 -I "$D" --scenario fixture --side after --host claude --out "$OUT"
python3.11 -I "$D" --scenario fixture --side after --host codex --out "$OUT"
python3.11 -I "$D" --scenario fixture --side after --host agy --out "$OUT"
python3.11 -I "$D" --scenario replay --side before --host claude --out "$OUT"
python3.11 -I "$D" --scenario replay --side before --host codex --out "$OUT"
python3.11 -I "$D" --scenario replay --side before --host agy --out "$OUT"
python3.11 -I "$D" --scenario replay --side after --host claude --out "$OUT"
python3.11 -I "$D" --scenario replay --side after --host codex --out "$OUT"
python3.11 -I "$D" --scenario replay --side after --host agy --out "$OUT"
```
Expected: `FR9-DRIVE: PASS rows=3 mismatched=0` on each of the three fixture lines and `FR9-DRIVE: PASS rows=4 mismatched=0` on each of the six replay lines, 33 rows in all.

**Expected rows.** AC-9.1, each host: listed `scripts/tool.sh` with the test absent reads DENY `test-missing`; the same with the test failing reads ALLOW; the unlisted `scripts/other.sh` with the test absent reads ALLOW. AC-9.4, each host:

| Write target | `h-mad/tests/test_hmad_dispatch_exec.py` | Before | After |
|---|---|---|---|
| `h-mad/scripts/hmad-dispatch.sh` | absent | ALLOW | DENY `kind=test-missing` |
| `h-mad/scripts/hmad-dispatch.sh` | failing on an assertion | ALLOW | ALLOW |
| `h-mad/scripts/h_mad_derive_test_path.sh` | absent | ALLOW | ALLOW |
| `h-mad/SKILL.md` | absent | ALLOW | ALLOW |

**Then the whole mutation run**, requiring `MUTATION: ALL_CAUGHT` with `refused=0` on each:
```bash
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/wire_pin_ungated.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/parse_tasks_non_py.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_data_definition.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_matcher.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/listing_connections.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/judge_non_py.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/claude_gate_listing.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/codex_gate_listing.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/agy_gate_listing.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/fr9_drive_refusals.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/claude_gate_judge_wiring.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/tdd_judge_resolution.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/tdd_judge_wiring.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/shared_gate_policy.json
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/agy_tdd_gate.json
```

**Acceptance Criteria**:
- [ ] AC-9.1: `readings.tsv` holds the three AC-9.1 rows per host as stated, with `FR9-DRIVE: PASS rows=3 mismatched=0`, and the Claude evidence holds the required `TDD-IMPLEMENTER:` line in `implementer.txt`.
- [ ] AC-9.2: each host's `hook.json` records the executed hook's realpath, sha256 and blob ids at the commit under test.
- [ ] AC-9.3: every spec above prints `MUTATION: ALL_CAUGHT` with `refused=0`.
- [ ] AC-9.4: `readings.tsv` holds the four AC-9.4 rows per host and per side as tabled, with `FR9-DRIVE: PASS rows=4 mismatched=0` on each of the six replay invocations.
- [ ] AC-9.5: `provenance.json` holds the source commit (the base), the plan blob, the copy's sha256, the base sha, and per host and per side the hook path and sha256, and the blob id equals `git hash-object` of the copy.
- [ ] The eight driver refusals: `test_fr9_driver_refuses` passes on all eight ids, each asserting the token line and exit 2.

**Mutation rows** (8, in `fr9_drive_refusals.json`; `root` `../..`, `file` `../docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py`, `command` `["python3.11", "-m", "pytest", "tests/test_h_mad_fr9_drive_refusals.py", "-q"]`).

**Choice on plan D11 and plan FR-9**: option (a), mutation rows, rather than narrowing the plan to "each refusal has a test node". Plan D11 and plan FR-9 promise an entry for each refusal; spec AC-9.3 does not require one, so either satisfies the spec. Option (a) is the one that leaves all three documents true without editing a round-capped plan, and the mechanism already exists: `h-mad/tests/mutation-specs/grok_audit_surface.json` targets `../docs/03-analysis/probes/grok-audit-surface/` from the same `root`, and `--check-anchors` on it printed `ANCHORS_OK` at `26571a2d`. A refusal is a guard, so a refusal no mutant has bitten carries the same risk any other unmutated guard does. Design v1.4's Components table and its Task 8 omit this spec.

Each guard is a one-line `if` carrying its marker, and each row's replace is `if False:` with the same marker:
- `D-NO-BEFORE-SIDE` (`symbol` `main`): marker `# M:D-NO-BEFORE-SIDE`. Test `tests/test_h_mad_fr9_drive_refusals.py::test_fr9_driver_refuses[no-before-side]`.
- `D-DIRTY-HOOKS` (`symbol` `_check_hook_identity`): marker `# M:D-DIRTY-HOOKS`. Test `tests/test_h_mad_fr9_drive_refusals.py::test_fr9_driver_refuses[dirty-hooks]`.
- `D-HOOK-OUTSIDE-TREE` (`symbol` `_check_hook_identity`): marker `# M:D-HOOK-OUTSIDE-TREE`. Test `tests/test_h_mad_fr9_drive_refusals.py::test_fr9_driver_refuses[hook-outside-tree]`.
- `D-HOOK-BLOB` (`symbol` `_check_hook_identity`): marker `# M:D-HOOK-BLOB`. Test `tests/test_h_mad_fr9_drive_refusals.py::test_fr9_driver_refuses[hook-blob-mismatch]`.
- `D-AUTHORSHIP` (`symbol` `_check_authorship`): marker `# M:D-AUTHORSHIP`. Test `tests/test_h_mad_fr9_drive_refusals.py::test_fr9_driver_refuses[authorship-line]`.
- `D-MISSING-BASE` (`symbol` `_replay_base`): marker `# M:D-MISSING-BASE`. Test `tests/test_h_mad_fr9_drive_refusals.py::test_fr9_driver_refuses[missing-base]`.
- `D-BASE-IS-HEAD` (`symbol` `_replay_base`): marker `# M:D-BASE-IS-HEAD`. Test `tests/test_h_mad_fr9_drive_refusals.py::test_fr9_driver_refuses[base-is-head]`.
- `D-PLAN-BLOB` (`symbol` `_copy_plan`): marker `# M:D-PLAN-BLOB`. Test `tests/test_h_mad_fr9_drive_refusals.py::test_fr9_driver_refuses[plan-blob-mismatch]`.

A mutant may kill through a later crash rather than a later token; the harness annotates that as `crash_kills`, and each node still fails for its own missing token.

**Commands**:
```bash
rtk proxy python3.11 -m pytest h-mad/tests/test_h_mad_fr9_drive_refusals.py -q
```
Then the run order and mutation run above, the full suite, and `--check-anchors` over all of `h-mad/tests/mutation-specs/`.

**Dependencies on other tasks**: Tasks 1 to 7.

---

## Mutation-row ledger
| Task | New rows | Breakdown | Re-anchored existing rows |
|---|---|---|---|
| 1 | 5 | `wire_pin_ungated.json` 2, `parse_tasks_non_py.json` 3 | none |
| 2 | 7 | `doc_data_definition.json` 7 | none |
| 3 | 9 | `listing_matcher.json` 8, `judge_non_py.json` 1 | `declared-budget-not-read` |
| 4 | 19 | `codex_gate_listing.json` 6, `listing_connections.json` 2, `listing_matcher.json` 2, `doc_data_definition.json` 9 | `fr6-import-guard-dropped` |
| 5 | 18 | `agy_gate_listing.json` 5, `listing_connections.json` 2, `listing_matcher.json` 2, `doc_data_definition.json` 9 | `fr4-t7-unreadable-dropped` |
| 6 | 22 | `claude_gate_listing.json` 9, `listing_connections.json` 2, `listing_matcher.json` 2, `doc_data_definition.json` 9 | `H11`, `CG-CANON` |
| 7 | 0 | none | none |
| 8 | 8 | `fr9_drive_refusals.json` 8 | none |
| **Total** | **88** | | **5** |

By spec, the `mutations=` each run must print: `wire_pin_ungated.json` 2, `parse_tasks_non_py.json` 3, `doc_data_definition.json` 34, `listing_matcher.json` 14, `listing_connections.json` 6, `judge_non_py.json` 1, `claude_gate_listing.json` 9, `codex_gate_listing.json` 6, `agy_gate_listing.json` 5, `fr9_drive_refusals.json` 8; these sum to 88. Design v1.4 states no overall total. The counts it does state hold here: six connection mutants (AC-3.1), three callee entries, and nine per-suffix mutants per host.

## Acceptance-criteria coverage
The spec's 55 ACs (`python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/gate-non-py-production-files.spec.md` prints `ACS: OK count=55 frs=11`, reading at `26571a2d`) land as follows. AC-1.1 to AC-1.5 and AC-2.1 to AC-2.4 in Task 1. AC-4.1 to AC-4.6 in Task 3. AC-3.1 to AC-3.5, AC-8.1 to AC-8.4 and AC-11.1 to AC-11.6 per host in Tasks 4, 5 and 6, with AC-3.5's judge side in Task 3 and the FR-11 definition in Task 2. AC-5.1 to AC-5.8 in Task 6. AC-6.1 to AC-6.5 in Task 4. AC-7.1 to AC-7.4 in Task 5. AC-10.1 to AC-10.3 in Task 7. AC-9.1 to AC-9.5 in Task 8.

## Phase 7 integration
The feature integrates into the local branch `main` via `--route merge`, and only on the operator's go-ahead. FR-9's evidence must already exist, because the driver refuses the replay with `base-is-head` after the push.

The plan step, run in the worktree that holds `main` when it is clean:
```bash
python3 h-mad/scripts/h_mad_phase7_integrate.py --feature gate-non-py-production-files --base main --route merge --branch BrightGold70/gate-non-py-production-files
```
Run from this feature's worktree the same command prints `BLOCKED reason=base_checked_out_elsewhere` with the path, and without `--branch` the line reads `BLOCKED reason=base_is_the_feature_branch:main`. `origin/main` is refused, because the script accepts a base only when `git rev-parse --verify --quiet refs/heads/NAME` succeeds. The `identity=` token decides at integration time; a `BLOCKED` line has no such token. `--apply` carries `--suite "python3.11 -m pytest"` unconditionally, because the script runs that command only when the merged tree differs from the branch tip. The apply prints `identity=y suite=covered`, `identity=n suite=PASS rc=0`, or `identity=n suite=FAIL` with an exit code or exception name, which means do not push. The replay base (`git merge-base HEAD origin/main`) and the integration target (local `main`) are different refs by design.

## Version History
- v1.0: Initial implementation plan draft (2026-11-04), from design v1.4, spec v1.11 and plan v1.6. Answers no audit cycle. Eight Tasks, three of them wiring, 88 new mutation rows and 5 re-anchored rows.
