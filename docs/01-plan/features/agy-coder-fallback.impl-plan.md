# Implementation Plan: agy-coder-fallback

> Source: `docs/02-design/features/agy-coder-fallback.design.md` v1.3 (`4e4b5ded`), spec v1.9
> (`4bef0e76`), plan v1.6 (`8e242d06`).
> Branch target: `feature/agy-coder-fallback` (Phase 5c names the branch).
> Implementer for THIS feature: Codex (`implementer=codex`). agy as an implementer is what this
> feature builds, not how it is built.

Every `path:symbol`, test name, mutation-row name and count below was read from the tree at
`4e4b5ded`. `h-mad/` is unchanged since `a8d9ba99` (`git diff --stat a8d9ba99 4e4b5ded -- h-mad`
prints nothing), so the design's readings at `29ae3e7b`, `200ffd52` and `cff71b49` still describe
the code. Node IDs are written relative to `h-mad/`, the `root` every mutation spec uses.

## Executive Summary

Twenty-three Tasks. Tasks 0–19 run in the Phase-5 worktree and merge; Tasks 20–22 run on main
after the merge (spec D-13), and the feature is recorded COMPLETE only after Task 22.

| Task | Shape | What lands | Design |
|---|---|---|---|
| 0 | gate | committed census probes (M-2, M-3, the FR-3 region census, M-4, DO-1a, doc-pin, class inventory) | Owed list |
| 1 | new-behaviour | five schema properties, `rfc3339_datetime`, `_semantic_ok` in `classify`, `property_valid`, the four description rewrites | FR-1 |
| 2 | new-behaviour | `Record` fields, `_implementer_tag`, `Implementer`, `resolve_implementer`, the `implementer` verb | FR-2 |
| 3 | wiring | the author field on `TDD-STATE:`, the hook's FR-3 precedence, the stub re-shape, re-anchoring | FR-3 |
| 4 | new-behaviour | the 25 names move into `h_mad_target_identity.py`; the guarded import; 31 rows re-pointed; the Codex `--self-check` verdicts `FAIL parser` and `FAIL shell-policy` on stdout with exit 0 | FR-6 |
| 5 | new-behaviour | agy gate: contract, payload, root, activity, step 5, classes (a) and (d), `--self-check` | FR-4 |
| 6 | new-behaviour | agy gate: class (b), T1–T7 | FR-4 |
| 7 | new-behaviour | agy gate: class (c) | FR-4, FR-6 |
| 8 | gate | the target differential and the shell differential | FR-4 |
| 9 | new-behaviour | `check_agy` and `--agy` | FR-5 |
| 10 | wiring | assembler `--agent agy`, the timeout table, the check run, the docstring | FR-5, AC-9.1 |
| 11 | new-behaviour | writer `--append`, `APPEND_ONLY` | FR-7 |
| 12 | new-behaviour | the three Phase-7 warnings | FR-7 |
| 13 | new-behaviour | the six carve-out copies, the equivalence test, 8 control rows | FR-9 |
| 14 | gate | the differential corpus and its 2 control rows | FR-9 |
| 15 | new-behaviour | the implementer-neutral prompt opening and `Hook:` line | FR-9, FR-10 |
| 16 | new-behaviour | SKILL.md authorship surfaces, `agy-runtime.md` | FR-10 |
| 17 | new-behaviour | SKILL.md review-independence procedure, the author append, AC-7.3's surface | FR-7, FR-10 |
| 18 | gate | AC-9.1 union sweep re-run; census re-runs on the shipped tree | FR-9, Owed |
| 19 | gate | the HemaSuite incident replay | FR-9 (AC-9.3) |
| 20 | new-behaviour | post-merge: payload capture, `PATH_KEYS`, inventory re-take | FR-8 step 1 |
| 21 | operational | post-merge: FR-8 steps 2, 2a and 3 in a fixture project | FR-8 |
| 22 | new-behaviour | post-merge: this repository's `.agents/hooks.json`, the derived timeout, the AC-8.1 formula probe | FR-8 steps 4–5 |

Shapes: `wiring` 2 (Tasks 3, 10); `new-behaviour` 15 (Tasks 1, 2, 4, 5, 6, 7, 9, 11, 12, 13,
15, 16, 17, 20, 22); `gate` 5 (Tasks 0, 8, 14, 18, 19); `operational` 1 (Task 21).
2 + 15 + 5 + 1 = 23.

**Rules every Task follows.**
- **Full suite per Task**, never a scoped selection: `rtk proxy /opt/anaconda3/bin/python3 -m
  pytest h-mad/tests -q -p no:cacheprovider`, in the foreground, gated on the summary line, never
  `$?`. The floor is the 5c collection reading (plan M-1), plus the tests the Task adds.
- **RED counts are pytest node IDs.** A parametrised test counts once per id. `F` = fails at RED,
  `P` = passes at RED.
- **Working directory.** A command whose paths start `h-mad/` or `docs/` runs from the repository
  root. The mutation harness runs from `h-mad/`, the `root` every spec uses, with paths relative to
  it: `python3 scripts/h_mad_mutation_harness.py …` and specs as
  `tests/mutation-specs/<name>.json`. From `h-mad/`, `python3 h-mad/scripts/…` names
  `h-mad/h-mad/scripts/…`, which does not exist ("can't open file", exit 2).
- **Anchors (design §"Existing rows the edits move", E7).** After each Task's GREEN, run
  `python3 scripts/h_mad_mutation_harness.py --check-anchors tests/mutation-specs/<spec>.json …`
  from `h-mad/`, over every spec naming a file the Task edited, and require
  `ANCHORS: ANCHORS_OK`. A row the edit breaks is re-anchored in that Task, to the same intent and
  the same `test`. A row whose `replace` names a symbol the edit removes from that file is
  rewritten in the same Task, even when its `find` still matches. Every new row sets `symbol`.
  Each Task below names the existing rows its edits touch, or says it touches none. Those lists
  come from one sweep at `4e4b5ded`: each row's `find` was located in its file and mapped to its
  enclosing `def` (or `.md` section), then compared with the spans each Task edits.
- **Mutation verdicts.** Each spec a Task adds or re-anchors is run alone, from `h-mad/`, as
  `python3 scripts/h_mad_mutation_harness.py tests/mutation-specs/<spec>.json`, and gated on
  `MUTATION: ALL_CAUGHT`, read from the token line.
- **Verdict exits.** Every script and probe this plan adds or changes prints its verdict as a
  token and exits 0 on a normal `FAIL`, `UNWIRED` or `HALT` verdict, unless a Task states another
  exit for that verdict and the design table it cites gives that exit (the base invariant on
  audit-gate signal discipline). A nonzero exit means an operational error: the input could not
  be read, or a module could not be imported.
- **Halt markers.** Every new halt prints an `[H-MAD]` marker line at the transition, after its
  machine-read token line (`invariants.base.md` §"Marker discipline"). The tests on that halt
  assert the marker.
- **New mutation specs** copy the header shape of `tests/mutation-specs/heartbeat_beat.json`
  (`root`, `command`, `target_command`, `mutations`). Each row's `find` is written at GREEN
  against the committed bytes; the row's intent and `test` are fixed here.
- **Doc pins (plan R-8).** A Task that edits a doc keeps every pinned literal of the plan's doc-pin
  census, or changes that test's literal in the same commit. Its RED report names each census
  entry it moves; the expected value is "none" for every doc Task below.

## Task 0: census probes

**Production files**: none
**Test files**: none
**Task shape**: `gate`

**Description**: Commit the probes the design and the plan owe, under
`docs/03-analysis/probes/agy-coder-fallback/`, before any code moves. Each probe prints
`PROBE: PASS` or `PROBE: FAIL` and exits 0 on both, stamps `git rev-parse HEAD`, states its
invocation and working directory in its docstring, and carries a control that makes it print
`PROBE: FAIL`. Tasks 3, 4 and 18 re-run them.

- `census_mutation_rows.py` — from `h-mad/`, over `git ls-files 'tests/mutation-specs/*.json'`:
  - **M-2**, rows per file and specs per file, for `hooks/h-mad-tdd-gate.sh`,
    `scripts/h_mad_tdd_judge.py`, `hooks/h-mad-codex-tdd-gate.py`, `scripts/h_mad_assemble_tdd.py`,
    `scripts/h_mad_phase7_preconditions.py`, `scripts/h_mad_hook_wiring.py`,
    `scripts/h_mad_state_write.py` and `scripts/h_mad_target_identity.py`;
  - **M-3**, the plan's pattern `TDD-STATE:|STATE_ACTIVE_RE|codex-escape|ESCAPE_STATUSES|command -v codex|HMAD_CODEX_UNAVAILABLE`
    over `find + "\n" + replace` of rows naming the two FR-3 files;
  - **the FR-3 region census**: rows whose `find` starts inside `_read_state` (the shell function
    body), the authorship block (from the `_read_state --target "$TARGET_PATH"  # M:H3` line to
    the closing `fi` of the `codex-authorship` refusal), `_active_records` or
    `format_state_line` (their `ast` spans);
  - **M-4**, rows naming `hooks/h-mad-codex-tdd-gate.py` whose `find` starts inside the `ast`
    span of one of the 25 moved names, plus the absent-anchor and non-unique-anchor counts.
- `census_state_line.py` — the DO-1a line census: `git ls-files -z h-mad | xargs -0 grep -l
  'TDD-STATE: active'` and the plan's four-pattern variant (`-e 'codex-escape=' -e ' record=' -e
  'STATE_ACTIVE_RE' -e 'format_state_line'`), units: files.
- `census_doc_pins.py` — the plan's doc-pin census: string constants of at least 16 characters
  containing a space, from each `git ls-files 'h-mad/tests/*.py'` file that names the doc,
  matched verbatim inside each section FR-9/FR-10 rewrites (plan §"Architecture Considerations").
  It prints its hits and states its residual (short, space-free and run-time-built literals; the
  plan's hand-found pins are listed beside it, not derived).
- `class_inventory.py` — the first `init` event's `tools` of
  `docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log`, partitioned into
  the design's classes (a), (b), (c) and the remainder (d). Takes an optional second log path
  (Task 20's capture) and prints both partitions and their difference.

One reading of each at `4e4b5ded`, taken for this plan with scratch code since deleted; each
probe reproduces it or reports why not:
- M-2 (rows, specs): `h-mad-tdd-gate.sh` 56, 5; `h_mad_tdd_judge.py` 36, 8;
  `h-mad-codex-tdd-gate.py` 62, 5; `h_mad_assemble_tdd.py` 60, 6;
  `h_mad_phase7_preconditions.py` 12, 2; `h_mad_hook_wiring.py` 10, 1; `h_mad_state_write.py`
  21, 4; `h_mad_target_identity.py` 15, 2.
- M-3: 8 rows in 3 specs (`claude_gate_judge_wiring.json` 5, `tdd_judge_chain.json` 2,
  `tdd_gate_fallback_agent.json` 1).
- FR-3 region census: 13 rows. Hook 8 (`_read_state` 7: `H17`, `W5BR`, `W5BF`, `W5BF2`, `W5BF3`,
  `wr12-2-gate-never-reads-the-fold`, `g9-fallback-position-unchecked`; authorship block 1: `H3`).
  Judge 5 (`_active_records` 1: `g3-reads-another-feature`; `format_state_line` 4: `C3G`,
  `wr12-1-state-line-never-folds`, `C3`, `C5`). This reproduces the design's 13 only when the
  authorship block starts at the `# M:H3` line; a block that starts at the `if` gives 12.
- M-4: 31 of 62 rows in 4 specs (`codex_gate_judge_wiring.json` 21,
  `codex_gate_shell_allowance.json` 6, `assemble_tdd_mutation_rows.json` 2,
  `tdd_gate_differential.json` 2); 0 absent anchors, 0 non-unique.
- DO-1a: 6 files; the four-pattern variant 7 files.
- Class inventory: 58 distinct names; (a) 11, (b) 5, (c) 1, (d) 41.

**Acceptance Criteria**:
- [ ] Each probe prints `PROBE: PASS` at the 5c sha with the readings above, or prints
  `PROBE: FAIL` naming the figure that moved; a moved figure goes back to the design before
  Task 3.
- [ ] Each probe's control (a doctored input it is given on its command line) prints
  `PROBE: FAIL`.

**Dependencies on other tasks**: None.

---

## Task 1: state fields and the timestamp refusal

**Production files**: `h-mad/scripts/h_mad_state_schema.json`, `h-mad/scripts/h_mad_state_validate.py`, `h-mad/references/state-schema.md`
**Test files**: `h-mad/tests/test_h_mad_state_validate_fallback.py`, `h-mad/tests/test_h_mad_state_schema_fr1_docs.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §"FR-1". Append `implementer`, `agy_status`, `implementer_switch`,
`review_independence` and `implementation_authors`, in that order, after `fallback_agent` (today
the last property: `list(properties)` ends `…, 'codex_status', 'fallback_agent'`). `required` and
`additionalProperties: false` do not change. `h_mad_state_validate.py` gains `rfc3339_datetime`,
a private `_semantic_ok`, and `property_valid`. `classify` keeps its first statement
(`if not isinstance(record, dict): return "invalid"`), then returns `"invalid"` when
`_semantic_ok(record)` is false, before either schema tier. The writer refuses through `_mutate`'s
existing `classify(record) != "strict"` test and needs no change. `property_valid` is placed here,
as the design's Implementation Order step 1 places it, though FR-7 is its reader.
The `fallback_agent` and `codex_status` schema descriptions and their `state-schema.md` rows are
rewritten to FR-2's condition; `state-schema.md` gains one row per new field.

**Code structure**:
```python
def rfc3339_datetime(value: object) -> bool:
    """re.fullmatch(..., re.ASCII) over design FR-1's pattern, then datetime(...) must
    construct, then offset hours <= 23 and minutes <= 59; a non-str is False."""

def _semantic_ok(record: object) -> bool:
    """False exactly when record is a dict whose implementer_switch is a dict whose ts fails
    rfc3339_datetime; True otherwise. Never raises."""

def property_valid(name: str, value: object) -> bool:
    """value against _schema(STRICT_SCHEMA)["properties"][name] through _make_validator, built
    per call so the _FORCE_FALLBACK seam selects the path; for implementer_switch, also
    _semantic_ok({"implementer_switch": value}). Never raises."""
```
`property_valid` builds its validator per call rather than through `_validators`, because the
existing seam (`test_classify_matches_between_backends_on_the_corpus`) clears `_validators` around
`_FORCE_FALLBACK`; a cached per-property validator would keep the first path's backend.

**Tests**. Each `path` parameter takes `library` and `bundled`: `bundled` sets
`SV._FORCE_FALLBACK = True` with `SV._validators.clear()` before and after, as
`test_classify_matches_between_backends_on_the_corpus` does; `library` first asserts
`SV._Draft7Validator is not None`, so it cannot silently run the bundled path. A refused record's
test asserts `SV.undeclared_keys(record) == []` as well as the refusal, so it cannot pass at RED
on the undeclared key.

In `h-mad/tests/test_h_mad_state_validate_fallback.py`:
1. `tests/test_h_mad_state_validate_fallback.py::test_fr1_value_accepted` — path × 11 values:
   `implementer-codex`, `implementer-agy`, `implementer-null`, `agy_status-available`,
   `agy_status-unavailable`, `agy_status-exhausted`, `agy_status-null`, `implementer_switch-null`,
   `implementer_switch-object`, `review_independence-empty`, `review_independence-one-entry`;
   `classify == "strict"`. 22 nodes, F.
2. `tests/test_h_mad_state_validate_fallback.py::test_fr1_value_refused` — path × 12 values:
   `implementer-grok`, `implementer-empty-string`, `agy_status-quota`,
   `implementer_switch-missing-ts`, `implementer_switch-extra-key`,
   `implementer_switch-reason-unknown`, `implementer_switch-to-gemini`,
   `review_independence-not-array`, `review_independence-leg-unknown`,
   `review_independence-missing-independent`, `review_independence-independent-string`,
   `review_independence-extra-key`. 24 nodes, F.
3. `tests/test_h_mad_state_validate_fallback.py::test_fr1_record_without_new_fields_unchanged` —
   path × 1; a record with none of the five fields is `strict` (AC-1.1, and AC-1.3's "no
   `implementation_authors`" bullet). 2 nodes, P.
4. `tests/test_h_mad_state_validate_fallback.py::test_switch_ts_refused` — path × 6 values:
   `not-a-date`, `date-only` (`2026-10-16`), `feb-30` (`2026-02-30T00:00:00Z`), `zjunk`
   (`2026-10-16T00:00:00Zjunk`), `leap-60` (`2016-12-31T23:59:60Z`), `offset-24`
   (`2026-10-16T00:00:00+24:00`); `classify == "invalid"`. 12 nodes, F.
5. `tests/test_h_mad_state_validate_fallback.py::test_switch_ts_accepted` — path × 5 values:
   `writer-form` (from `h_mad_state_write._utc_now()`), `leap-59` (`2016-12-31T23:59:59Z`),
   `zone-upper-z` (`2026-10-16T07:05:09Z`), `zone-lower-z` (`2026-10-16T07:05:09z`),
   `zone-offset` (`2026-10-16T07:05:09+09:00`); `classify == "strict"`. Each zone alternative is
   its own fixture, run with that branch alone. 10 nodes, F.
6. `tests/test_h_mad_state_validate_fallback.py::test_rfc3339_datetime_refuses_non_strings_and_lookalikes`
   — 4 values: `int-5`, `none`, `trailing-newline` (the writer form plus `\n`), `fullwidth-digits`;
   `rfc3339_datetime(value) is False`. 4 nodes, F.
7. `tests/test_h_mad_state_validate_fallback.py::test_implementation_authors_accepted` — path × 6:
   `empty`, `agent-codex`, `agent-agy`, `agent-grok`, `agent-claude`, `three-entry-log`
   (`[m/agy, m/codex, m/agy]`, duplicates and order kept). 12 nodes, F.
8. `tests/test_h_mad_state_validate_fallback.py::test_implementation_authors_refused` — path × 7:
   `agent-gemini`, `missing-agent`, `missing-module`, `module-empty`, `extra-key`,
   `non-object-entry`, `non-array`. 14 nodes, F.
9. `tests/test_h_mad_state_validate_fallback.py::test_property_valid_implementer_switch_none_does_not_raise`
   — path × 1; returns `True`. 2 nodes, F.
10. `tests/test_h_mad_state_validate_fallback.py::test_property_valid_applies_the_ts_predicate` —
    path × `bad-ts` (`False`), `good-ts` (`True`). 4 nodes, F.
11. `tests/test_h_mad_state_validate_fallback.py::test_property_valid_review_independence_entry` —
    path × `well-formed` (`True`), `bad-leg` (`False`). 4 nodes, F.

In `h-mad/tests/test_h_mad_state_schema_fr1_docs.py` (new):
12. `tests/test_h_mad_state_schema_fr1_docs.py::test_codex_status_schema_description_states_the_resolution`
    — the description lacks `permitting Claude to write the fallback` and `One switch, both
    effects`, and names `h_mad_tdd_judge.py implementer`. F.
13. `tests/test_h_mad_state_schema_fr1_docs.py::test_codex_status_reference_row_states_the_resolution`
    — the `state-schema.md` `codex_status` row lacks `permits a Phase-5 authoring fallback` and
    names `h_mad_tdd_judge.py implementer`. F.
14. `tests/test_h_mad_state_schema_fr1_docs.py::test_fallback_agent_schema_description_names_both_peers`
    — contains `agy is out too`. F.
15. `tests/test_h_mad_state_schema_fr1_docs.py::test_fallback_agent_reference_row_names_both_peers`
    — the row contains `agy`. F.
16. `tests/test_h_mad_state_schema_fr1_docs.py::test_reference_rows_exist_for_the_five_fields` —
    one table row per new field. F.
17. `tests/test_h_mad_state_schema_fr1_docs.py::test_new_properties_follow_fallback_agent_in_order`
    — `list(properties)[-5:]` is the five in order. F.

**RED split**: 116 nodes; 114 F, 2 P (item 3). Sum: 22 + 24 + 2 + 12 + 10 + 4 + 12 + 14 + 2 + 4
+ 4 + 6 = 116.

**Regression guards** (pass at RED and GREEN):
`tests/test_h_mad_state_fallback_agent.py::test_fallback_agent_description_states_the_four_facts`
keeps its four substrings and its index assertion; the rest of
`tests/test_h_mad_state_validate_fallback.py`; `tests/test_h_mad_state_write.py`. The rewrite
re-runs `git ls-files -z h-mad/tests | xargs -0 grep -l 'permitting Claude to write the fallback\|permits a Phase-5 authoring fallback\|One switch, both effects\|blocked when Codex is available'`
(0 files at `4e4b5ded`) before editing; a file it lists is a pin to keep or move.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/state_fr1_fields.json`, 4 rows:
| name | mutant | test |
|---|---|---|
| `fr1-semantic-check-dropped` | the `_semantic_ok` call removed from `classify` | `tests/test_h_mad_state_validate_fallback.py::test_switch_ts_refused` |
| `fr1-datetime-construction-dropped` | the `datetime(...)` construction removed | `tests/test_h_mad_state_validate_fallback.py::test_switch_ts_refused` |
| `fr1-fullmatch-to-match` | `re.fullmatch` → `re.match` | `tests/test_h_mad_state_validate_fallback.py::test_switch_ts_refused` |
| `fr7-property-valid-dict-guard-dropped` | the predicate applied to `value["ts"]` unguarded | `tests/test_h_mad_state_validate_fallback.py::test_property_valid_implementer_switch_none_does_not_raise` |

The fourth row is design §"Mutation rows" FR-7's dict-guard row, placed with the code it bites.
`h_mad_state_validate.py` and `h_mad_state_schema.json` carry no existing rows (M-2 reading: 0),
and no row names `references/state-schema.md`, so this Task touches no existing row.

**Acceptance Criteria**:
- [ ] AC-1.1: items 1–3 and 12–17 pass; the regression guards pass.
- [ ] AC-1.2: items 4–6 pass, each value once per path. The package-absent fixture is not owed
  (no library format checker is used; design §"FR-1").
- [ ] AC-1.3: items 3, 7 and 8 pass, each once per path. Its store-unchanged bullet is Task 11
  item 8.
- [ ] AC-X: `state_fr1_fields.json` → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 0.

---

## Task 2: the resolver and the `implementer` verb

**Production files**: `h-mad/scripts/h_mad_tdd_judge.py`
**Test files**: `h-mad/tests/test_h_mad_tdd_judge_implementer.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §"FR-2". `Record` gains `implementer: str = "absent"` and
`agy_status: str = "available"` as trailing defaulted fields, so the positional four-argument
construction in `codex_gate_judge_wiring.json`'s `replace` text stays valid (`git ls-files -z
h-mad | xargs -0 grep -l 'Record('` → `h_mad_tdd_judge.py` and that spec, 2 files).
`_active_records` fills both through `_implementer_tag(state)` and the `codex_status` reading rule.
`resolve_implementer` is the only resolver. `main` gains an `implementer` subparser (`--root`,
`--feature`, `--record`) that reads `<root>/docs/.bkit-memory.json` through `_state_at`, looks up
`orchestrator_state[feature]` whatever its phase, prints exactly one `TDD-IMPLEMENTER:` line from
design FR-2's six-row table, and exits 0. With `--record`, a switch other than `none` calls
`h_mad_state_write.merge_fields(state_file, feature, {"implementer_switch": {...}})` with
`ts=_utc_now()`, skipped when the stored `from`, `to` and `reason` already match; a
`StateWriteError` or `OSError` appends ` record=failed`.

The design's Test Plan puts AC-2.1/AC-2.2 in `test_h_mad_tdd_judge.py`. This plan uses a new file,
because AC-3.2 requires `ACTIVE_RE` to be the only changed literal in `test_h_mad_tdd_judge.py`
against `a8d9ba99`; added tests there would add literals to the file that diff checks.

**Code structure**:
```python
class Record(NamedTuple):
    key: str
    codex_status: str
    state_file: Path
    fallback: str
    implementer: str = "absent"
    agy_status: str = "available"

class Implementer(NamedTuple):
    resolved: str        # codex|agy|grok|claude|invalid
    chosen: Optional[str]
    reason: Optional[str]
    invalid_field: Optional[str]
    invalid_value: str

def _implementer_tag(state: dict) -> str: ...
def resolve_implementer(record: Record, env=None, which=None) -> Implementer: ...
```

**Tests** (all in `h-mad/tests/test_h_mad_tdd_judge_implementer.py`; `env` and `which` are
injected in-process; the verb runs as `sys.executable h_mad_tdd_judge.py implementer …` with a
controlled `PATH`):
1. `tests/test_h_mad_tdd_judge_implementer.py::test_resolve_implementer_matrix` — `implementer`
   {absent, codex, agy, invalid} × codex available {yes, no} × agy available {yes, no}, fallback
   tag `absent`; `resolved` and `reason` per FR-2. 16 nodes.
2. `tests/test_h_mad_tdd_judge_implementer.py::test_each_cause_alone` — `chosen=codex`, agy
   available, only one cause present. The ids are fixture names, not reason values: `env`
   expects `reason == "env"`; `status-unavailable` (`codex_status` `unavailable`) and
   `status-exhausted` (`codex_status` `exhausted`) both expect `reason == "status"`; `cli-absent`
   expects `reason == "cli-absent"`. `reason` takes only the design's enum `env`, `status`,
   `cli-absent`. 4 nodes.
3. `tests/test_h_mad_tdd_judge_implementer.py::test_peers_out_fallback_tag_decides` — tags
   `absent`, `null`, `claude` → `claude`; `grok` → `grok`; an invalid tag →
   `invalid_field="fallback_agent"`. 5 nodes.
4. `tests/test_h_mad_tdd_judge_implementer.py::test_record_defaults_keep_positional_construction`. 1 node.
5. `tests/test_h_mad_tdd_judge_implementer.py::test_implementer_tag` — `absent`, `null`, `codex`,
   `agy`, `invalid-string` (`"grok"`), `invalid-number`. 6 nodes.
6. `tests/test_h_mad_tdd_judge_implementer.py::test_agy_status_read_like_codex_status` — key
   absent → `available`, `null` → `available`, `exhausted` → `exhausted`. 3 nodes.
7. `tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_line` — `file-absent`,
   `key-absent`, `unreadable`, `not-an-object`, `invalid-field`, `switch-none`, `peer-switch`,
   `peers-out`; exactly one stdout line equal to FR-2's row, exit 0. 8 nodes.
8. `tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_reads_the_record_whatever_its_phase`. 1 node.
9. `tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_record_writes_switch_once` —
   the first `--record` run writes `implementer_switch` whose `ts` passes `rfc3339_datetime`; an
   identical second run leaves the store byte-identical. 1 node.
10. `tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_record_failed` — a store the
    writer refuses; the line ends ` record=failed`, exit 0. 1 node.
11. `tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_switch_none_writes_nothing` —
    `--record` with `switch=none` leaves the store byte-identical. 1 node.

**RED split**: 47 nodes, 47 F, 0 P (16 + 4 + 5 + 1 + 6 + 3 + 8 + 1 + 1 + 1 + 1 = 47). The RED
reason is the missing symbol or the missing subparser; this is new behaviour, not a wire.

**Regression guards**: `tests/test_h_mad_tdd_judge.py`, `tests/test_h_mad_tdd_gate_judge.py`,
`tests/test_h_mad_tdd_gate_fallback_agent.py`, unmodified; the line shape does not change in this
Task.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/tdd_judge_implementer.json`, 4 rows:
| name | mutant | test |
|---|---|---|
| `fr2-cause-env-dropped` | the `env` branch of `_cause` removed | `tests/test_h_mad_tdd_judge_implementer.py::test_each_cause_alone` |
| `fr2-cause-status-dropped` | the `status` branch removed | `tests/test_h_mad_tdd_judge_implementer.py::test_each_cause_alone` |
| `fr2-cause-cli-absent-dropped` | the `cli-absent` branch removed | `tests/test_h_mad_tdd_judge_implementer.py::test_each_cause_alone` |
| `fr2-other-peer-dropped` | the other-peer step removed | `tests/test_h_mad_tdd_judge_implementer.py::test_resolve_implementer_matrix` |

**Anchors**: `--check-anchors` over the 8 specs naming `scripts/h_mad_tdd_judge.py`
(`claude_gate_judge_wiring.json`, `grok_wire_reverts.json`, `tdd_gate_fallback_agent.json`,
`tdd_judge_chain.json`, `tdd_judge_resolution.json`, `tdd_judge_scoring.json`,
`tdd_judge_venv.json`, `tdd_judge_wiring.json`). The candidate this Task moves is
`tdd_gate_fallback_agent.json` `g3-reads-another-feature`, whose `find` sits in `_active_records`,
which this Task edits; it is re-anchored here if it drifts, with its `test`
(`tests/test_h_mad_tdd_gate_fallback_agent.py::test_gate_matrix`) unchanged. It is the only
existing row whose `find` sits in a span this Task edits: no row sits in `Record` or in `main`'s
subparser block.

**Acceptance Criteria**:
- [ ] AC-2.1: items 1–3 pass.
- [ ] AC-2.2: items 7–11 pass.
- [ ] AC-X: `tdd_judge_implementer.json` → `MUTATION: ALL_CAUGHT`; `ANCHORS: ANCHORS_OK` over the 8
  judge specs.

**Dependencies on other tasks**: Task 1 (`--record` writes a field the schema must declare).

---

## Task 3: the author field and the Claude hook's precedence

**Production files**: `h-mad/scripts/h_mad_tdd_judge.py`, `h-mad/hooks/h-mad-tdd-gate.sh`
**Test files**: `h-mad/tests/test_h_mad_tdd_gate_peers.py` (new), `h-mad/tests/test_h_mad_tdd_gate_judge.py`, `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py`, `h-mad/tests/test_h_mad_tdd_judge.py`
**Task shape**: `wiring` — the author field's value must come from Task 2's resolver, and the hook
must read it rather than re-derive it. The kinds this Task adds are new behaviour; the RED split
below states which tests are which.
**WIRE 1**: `h-mad/scripts/h_mad_tdd_judge.py:format_state_line` → `resolve_implementer`
**WIRE-PIN 1**: `tests/test_h_mad_tdd_gate_peers.py::test_format_state_line_takes_the_author_from_resolve_implementer`
**WIRE 2**: `h-mad/hooks/h-mad-tdd-gate.sh:_read_state` → the author field of the `TDD-STATE:` line
**WIRE-PIN 2**: `tests/test_h_mad_tdd_gate_peers.py::test_hook_reads_authorship_from_the_state_line_not_the_environment`

**Description**: Design §"FR-3". `format_state_line` emits a fifth comma field per record, between
the state file and the fallback tag, computed through `resolve_implementer` with `env` and `which`
evaluated once per call: `codex`, `agy`, `peers-out` or `invalid:` plus the percent-encoded JSON.
The header does not change; `_fallback_fold` is untouched. The hook's `STATE_ACTIVE_RE` (the one
literal matching `^STATE_ACTIVE_RE='(.*)'$`) becomes design FR-3's grammar:

```
^TDD-STATE: active codex-escape=(yes|no) blocker=(0|[1-9][0-9]*) records=([1-9][0-9]*) fallback=(none|(grok|invalid):([1-9][0-9]*))( record=[^ ,]+,[^ ,]+,[^ ,]+,(codex|agy|peers-out|invalid:[^ ,]+),(absent|null|grok|claude|invalid:[^ ,]+))+$
```

In `_read_state`'s record loop the author is taken by stripping three leading fields; the loop
sets `INVALID_RECORD` (the first author starting `invalid:`) and `PEER_RECORD`/`PEER` (the first
author `codex` or `agy`). The `BLOCKER_RECORD` capture is removed; the header checks stay. The
block at today's `if [ -z "${HMAD_CODEX_UNAVAILABLE:-}" ] && [ "$ESCAPE" = no ] && command -v codex`
is replaced by FR-3's precedence: `implementer-invalid` (new text), then
`codex-authorship`/`agy-authorship` (the `codex-authorship` literal byte for byte, its
`BLOCKER_KEY`/`BLOCKER_FILE` renamed `PEER_KEY`/`PEER_FILE`; `agy-authorship` new, naming
`hmad-dispatch exec agy` with `h_mad_assemble_tdd.py --agent agy`, `--set agy_status=exhausted`,
`export HMAD_AGY_UNAVAILABLE=1 for a one-off` and `h_mad_tdd_judge.py implementer`), then the
existing `fallback_agent` block unchanged, its comment rewritten to name both peers.

**The three fixture-consequence literals land in the GREEN commit, with the production change**
(AC-3.2's exception; design §"Fixture consequence"): `_tree_b`'s default `state_line` gains
`,peers-out` before `,absent`; `RECORD` becomes
`" record=feat,exhausted,/x/docs/.bkit-memory.json,peers-out,"`; `ACTIVE_RE` becomes the grammar
above. Each states the new contract that producer and consumer change together, so committing it
at RED would fail every stub test for the shape alone and hide the RED reasons that matter. No
other line of those three files changes; the 5e verifier diffs each against `a8d9ba99`.

The agy stub for `agy-authorship` is written into the test's own `bin_dir` by the new file;
`_bin` in `test_h_mad_tdd_gate_judge.py` is not edited.

**Tests** (all in `h-mad/tests/test_h_mad_tdd_gate_peers.py`, which imports `HOOK`, `TARGET`,
`_bin`, `_gate`, `_root` and `_tree_b` from `test_h_mad_tdd_gate_judge` as
`test_h_mad_tdd_gate_fallback_agent.py` does; real-judge tests use `path_tail="/usr/bin:/bin"`):
1. `tests/test_h_mad_tdd_gate_peers.py::test_format_state_line_takes_the_author_from_resolve_implementer`
   — WIRE-PIN 1. In-process: `monkeypatch.setattr(judge, "resolve_implementer", fake)` where
   `fake` records each call and returns `Implementer("agy", "agy", None, None, "")`; assert the
   fourth comma field of each record is `agy` and `fake` was called once per record. F: at the
   RED base `resolve_implementer` exists (Task 2) and the line has no author field, so the
   assertion on the field fails; no import fails.
2. `tests/test_h_mad_tdd_gate_peers.py::test_hook_reads_authorship_from_the_state_line_not_the_environment`
   — WIRE-PIN 2. A `_tree_b` stub line whose one record carries `codex_status` `available`,
   author `peers-out` and tag `absent`, with a `codex` stub on `PATH`, `HMAD_CODEX_UNAVAILABLE`
   unset and the judge stub answering ALLOW; assert `allow`. F: the RED hook rejects the new
   grammar and denies `judge-error`, an assertion on the caller's decision.
3. `tests/test_h_mad_tdd_gate_peers.py::test_agy_authorship_refused_when_agy_resolves` — real
   judge, record `implementer=agy`, `agy` stub on `PATH` → `agy-authorship`. F.
4. `tests/test_h_mad_tdd_gate_peers.py::test_codex_authorship_refused_when_codex_resolves`. P.
5. `tests/test_h_mad_tdd_gate_peers.py::test_implementer_invalid_refused` — `implementer="gpt"` →
   `implementer-invalid`, reason names the value and the `--set implementer=codex|agy|null` fix. F.
6. `tests/test_h_mad_tdd_gate_peers.py::test_fallback_grok_refused_when_peers_out`. P.
7. `tests/test_h_mad_tdd_gate_peers.py::test_fallback_invalid_refused_when_peers_out`. P.
8. `tests/test_h_mad_tdd_gate_peers.py::test_implementer_invalid_outranks_codex_authorship` —
   records `[codex-available, invalid]` → `implementer-invalid`. F.
9. `tests/test_h_mad_tdd_gate_peers.py::test_peer_refusal_outranks_fallback_invalid`. P.
10. `tests/test_h_mad_tdd_gate_peers.py::test_chain_fold_blocks_on_the_first_eligible_record` —
    records `[agy, codex]`, both stubs on `PATH` → `agy-authorship` naming the first key. F.
11. `tests/test_h_mad_tdd_gate_peers.py::test_today_shape_state_line_is_judge_error` — AC-3.2's
    new fixture. F.
12. `tests/test_h_mad_tdd_gate_peers.py::test_unknown_author_field_is_judge_error` — author
    `grok`. P (the RED grammar also rejects the extra field; it pins the closed author set at
    GREEN).
13. `tests/test_h_mad_tdd_gate_peers.py::test_agy_authorship_message_names_the_dispatch_and_the_switches`. F.
14. `tests/test_h_mad_tdd_gate_peers.py::test_three_message_bodies_match_a8d9ba99` — reads
    `git show a8d9ba99:h-mad/hooks/h-mad-tdd-gate.sh`, extracts the `codex-authorship`,
    `fallback-grok` and `fallback-invalid` refusal literals from both texts, normalises
    `PEER_` to `BLOCKER_` on both sides, and asserts equality. P.

**RED split**: 14 nodes; 8 F (items 1, 2, 3, 5, 8, 10, 11, 13), 6 P (items 4, 6, 7, 9, 12, 14).
Both WIRE-PINs fail on an assertion about the caller. Items 4, 6, 7, 9 and 14 are regression
guards on existing kinds and bytes.

**Regression guards**: every existing `tests/test_h_mad_tdd_gate_*.py` and
`tests/test_h_mad_tdd_judge.py`, with only the three literals above changed. The design's stub
enumeration holds at `4e4b5ded`: `_tree_b(` matches 9 lines in `test_h_mad_tdd_gate_judge.py`
(1 `def`, 8 call sites) and `_stub_outcome(` 6 lines in `test_h_mad_tdd_gate_fallback_agent.py`
(1 `def`, 5 call sites). `test_h_mad_tdd_gate_fallback_agent.py::test_absent_null_claude_match_the_base_hook`
is the `shutil.which` equivalence check.

**The grammar probe.** `docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py` was
updated with this revision of the plan (it is not a file this Task edits). The `fc6b497e` version
derived the new grammar by splicing the author group in front of `OLD_TAIL`. `NEW_TAIL` ends with
`OLD_TAIL`, so on the hook after GREEN it spliced a second author group and printed
`PROBE: FAIL`. The updated probe picks its mode from the literal it reads. `derived` is a literal
ending with `OLD_TAIL`: the probe derives the grammar, as before. `shipped` is a literal ending
with `NEW_TAIL`: the probe checks the literal as written, and checks that it equals the grammar
derived from `git show a8d9ba99:h-mad/hooks/h-mad-tdd-gate.sh`. A literal ending with neither is
drift and prints `PROBE: FAIL`. `--control` drops `peers-out|` from the grammar under test and
must print `PROBE: FAIL`. `--hook PATH` reads another copy of the hook. Readings at `fc6b497e`
plus the update, from the repository root, under `/bin/bash` and `/opt/homebrew/bin/bash`:
the tree's hook gives `mode=derived` and `PROBE: PASS`, and `--control` gives `PROBE: FAIL`. A
scratch copy of the hook carrying this Task's grammar (the block above) gives `mode=shipped`,
`shipped literal == grammar derived from a8d9ba99` and `PROBE: PASS`, and `--control` gives
`PROBE: FAIL`. A drifted literal gives `PROBE: FAIL` with exit 0, and an unreadable `--hook`
exits 2. After GREEN, from the repository root:
`python3 docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py /bin/bash /opt/homebrew/bin/bash`
must print `mode=shipped` and `PROBE: PASS`, and the same command with `--control` must print
`PROBE: FAIL`.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/tdd_gate_peers.json`, 7 rows:
| name | mutant | test |
|---|---|---|
| `fr3-implementer-invalid-dropped` | the `implementer-invalid` branch removed | `tests/test_h_mad_tdd_gate_peers.py::test_implementer_invalid_refused` |
| `fr3-invalid-scan-first-record-only` | the `INVALID_RECORD` scan stops at the first record | `tests/test_h_mad_tdd_gate_peers.py::test_implementer_invalid_outranks_codex_authorship` |
| `fr3-agy-arm-dropped` | the `agy` arm removed | `tests/test_h_mad_tdd_gate_peers.py::test_agy_authorship_refused_when_agy_resolves` |
| `fr3-peers-out-alternative-dropped` | `peers-out` removed from the grammar's author alternation | `tests/test_h_mad_tdd_gate_peers.py::test_hook_reads_authorship_from_the_state_line_not_the_environment` |
| `wire1-author-not-from-resolver` (wire-cut) | `format_state_line` writes `codex` for every record instead of calling `resolve_implementer` | `tests/test_h_mad_tdd_gate_peers.py::test_format_state_line_takes_the_author_from_resolve_implementer` |
| `wire2-hook-rederives-from-env` (wire-cut) | the author-field read replaced by today's `HMAD_CODEX_UNAVAILABLE`/`command -v codex` test | `tests/test_h_mad_tdd_gate_peers.py::test_hook_reads_authorship_from_the_state_line_not_the_environment` |
| `wire2-every-author-is-a-peer` (converse) | the loop's author test replaced so the first record sets `PEER_RECORD` with `PEER=codex` whatever its author, and `codex-authorship` fires unconditionally | `tests/test_h_mad_tdd_gate_peers.py::test_hook_reads_authorship_from_the_state_line_not_the_environment` |

**Both directions.** WIRE 2's cut is `wire2-hook-rederives-from-env`, and its converse is
`wire2-every-author-is-a-peer`. In item 2 the record's author is `peers-out`, so the converse
mutant denies `codex-authorship` where GREEN allows. A mutant that sets `PEER=peers-out` would
match neither refusal arm and survive, so the row's `replace` sets `PEER=codex`. WIRE 1 has no converse mutant: `format_state_line` calls
`resolve_implementer` for every record unconditionally by design, so no fall-through exists for a
mutant to force. Its one direction is `wire1-author-not-from-resolver`.

**Re-anchoring (R-1)**: read every row whose `file` is `hooks/h-mad-tdd-gate.sh` (56 rows) or
`scripts/h_mad_tdd_judge.py` (36 rows plus Task 2's 4), not only the 13 the region census lists.
Re-anchor each drifted row to the same intent and `test`, then `--check-anchors` over every spec
naming either file and require `ANCHORS: ANCHORS_OK`, and run each such spec alone for
`MUTATION: ALL_CAUGHT`: `claude_gate_judge_wiring.json`, `grok_wire_reverts.json`,
`tdd_gate_differential.json`, `tdd_gate_fallback_agent.json`, `tdd_gate_scratchpad.json`,
`tdd_judge_chain.json`, `tdd_judge_resolution.json`, `tdd_judge_scoring.json`,
`tdd_judge_venv.json`, `tdd_judge_wiring.json`, `tdd_judge_implementer.json`, `tdd_gate_peers.json`.
Re-run Task 0's `census_mutation_rows.py` and record the post-Task M-3 reading (the fix adds rows
to the class M-3 counts, so it moves by construction).

**Acceptance Criteria**:
- [ ] AC-3.1: items 3–10 pass.
- [ ] AC-3.2: item 11 and item 14 pass; the three diffs against `a8d9ba99` show only the three
  literals; every other `test_h_mad_tdd_gate_*.py` is unmodified.
- [ ] WIRE-PIN 1 and WIRE-PIN 2 each fail when only their wire is cut (the two wire-cut rows), and
  WIRE-PIN 2 fails when its wire is forced (`wire2-every-author-is-a-peer`).
- [ ] The grammar probe prints `mode=shipped` and `PROBE: PASS` under both bashes, and
  `PROBE: FAIL` under `--control`.
- [ ] AC-X: the 12 specs above → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 2.

---

## Task 4: the shared gate policy

**Production files**: `h-mad/scripts/h_mad_target_identity.py`, `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test files**: `h-mad/tests/test_h_mad_shared_gate_policy.py` (new)
**Task shape**: `new-behaviour` — a move with no change to the Codex gate's hook decisions, plus
one behaviour correction to its `--self-check` (the `FAIL parser` and `FAIL shell-policy` verdicts, below; orchestrator
decision I4, impl-plan audit cycle 2). The move's binding is pinned by the existing Codex gate
tests, unmodified, and by the location tests below; there is no WIRE because the callee and the
caller are the same code before and after.

**Description**: Design §"FR-6". Move the 17 functions (`_contained_venv_executable`,
`_cwd_escapes_root`, `_load_judge`, `_option_value`, `_path_within`, `_payload_cwd_base`,
`_safe_argv`, `_safe_hmad_script`, `_safe_shell_command`, `_trusted_executable`,
`_shell_allowance`, `_operator_allowed`, `_is_shell_allowance`, `_read_regular_text`,
`_state_status`, `_any_phase5_status`, `_is_production_python`) and the 8 constants
(`SIMPLE_SHELL_COMMAND`, `READ_ONLY_COMMANDS`, `SAFE_DISPATCH_VERBS`, `SAFE_HMAD_SCRIPT_OPTIONS`,
`TEMP_OUTPUT_OPTIONS`, `SHELL_ALLOW_FILE`, `TRUSTED_BIN_DIRS`, `MALFORMED_WORKDIR`) byte for byte,
except `_is_production_python`'s `_load_identity().fold_py_suffix` call, which becomes the module's
own `fold_py_suffix`. All 25 exist as module-level definitions in the Codex gate at `4e4b5ded`
(checked with `ast`). Not moved: `_load_identity`, `_relative_target`, `_tmp_report_target`,
`_command_cwd`, `_main_guarded`'s composition, and `main`'s `unsafe` tuple. The module docstring
(`Canonical filesystem identity shared by the H-MAD TDD gates.`) is widened to say it also holds
the policy both write gates apply.

The Codex gate inserts its `scripts` directory into `sys.path` and imports all 25 names at module
level inside a `try:` block whose `except Exception as exc:` handler assigns
`_POLICY_IMPORT_ERROR = exc` (`_POLICY_IMPORT_ERROR = None` before it). The first statement of
`_main_guarded` re-raises it, so `main`'s `except Exception as exc:  # M:G2` answers. No early
return is added between `main`'s entry and that `try`. The `--self-check` branch prints
`CODEX-TDD-GATE: FAIL policy-import` to stderr and returns 2 when `_POLICY_IMPORT_ERROR` is set,
before it calls `_safe_shell_command`. Exit 2 is the operational-error exit: the gate cannot import
its policy (design §"FR-6").

**The two self-check FAILs (orchestrator decision I4; design v1.4's class rule: a verdict FAIL
prints its token on stdout and exits 0, a could-not-run FAIL exits 2).** At `84ec2133` the Codex
gate's `--self-check` branch in `main` has two FAILs, both `print(..., file=sys.stderr)` followed
by `return 2`:
- `CODEX-TDD-GATE: FAIL parser`, when `_patch_header_paths` returns anything but
  `(["src/prod.py"], "")` for one of its three fixed headers. **A verdict**: the self-check ran its
  probe and found the header parser wrong, the same class as `shell-policy`. Read in-process at
  `84ec2133` with `_patch_header_paths` forced to return `(["wrong.py"], "")`: `rc=2`, stdout
  empty, stderr `CODEX-TDD-GATE: FAIL parser`.
- `CODEX-TDD-GATE: FAIL shell-policy`, when `_safe_shell_command` admits one of the four `unsafe`
  commands. **A verdict.** Read in-process at `84ec2133` with `_safe_shell_command` forced to
  return `True`: `rc=2`, stdout empty, stderr `CODEX-TDD-GATE: FAIL shell-policy`; unforced:
  `rc=0`, stdout `CODEX-TDD-GATE: PASS`.

This Task changes both branches to print the token on stdout (no `file=sys.stderr`) followed by
`return 0`, the contract Task 5 gives the agy gate's verdict FAILs. `FAIL policy-import` keeps
stderr and exit 2: the gate could not import its policy, so the self-check could not run.
Regression provenance: no existing test pins exit 2 for either verdict. At `84ec2133`,
`grep -rn 'FAIL parser' h-mad/tests` gives 0 matching lines, and `grep -rn 'shell-policy'
h-mad/tests` gives 3 (in `test_h_mad_codex_tdd_gate_judge.py` lines 787 and 953 and
`tdd_gate_support.py` line 195), all naming the shell-policy differential corpus and none the
`--self-check` branch. The one existing `--self-check` test,
`tests/test_h_mad_codex_runtime.py::test_codex_hook_self_check_reports_machine_readable_pass`,
pins the `PASS` path and stays unmodified. The defect was unpinned, not pinned, and no existing
test changes. No existing mutation row anchors on either branch (`grep -n 'CODEX-TDD-GATE'
h-mad/tests/mutation-specs/*.json`: 0 matching lines).

**Tests** (all in `h-mad/tests/test_h_mad_shared_gate_policy.py`):
1. `tests/test_h_mad_shared_gate_policy.py::test_each_moved_function_has_one_definition_in_the_identity_module`
   — one id per moved function (17); exactly one `def` of it across the `.py` files of
   `git ls-files h-mad`, and that file is `h-mad/scripts/h_mad_target_identity.py`. 17 nodes, F
   (the one definition is in the Codex gate today).
2. `tests/test_h_mad_shared_gate_policy.py::test_each_moved_constant_is_assigned_in_the_identity_module`
   — one id per constant (8), same rule for a module-level assignment. 8 nodes, F.
3. `tests/test_h_mad_shared_gate_policy.py::test_codex_gate_binds_every_moved_name_to_the_identity_module`
   — the gate loaded from its path; for each of the 25 names, `getattr(gate, name) is
   getattr(identity, name)`. 1 node, F.
4. `tests/test_h_mad_shared_gate_policy.py::test_codex_gate_self_check_reports_a_policy_import_failure`
   — the gate copied beside a real judge and no identity module; `--self-check` prints
   `CODEX-TDD-GATE: FAIL policy-import` on stderr and exits 2. 1 node, F.
5. `tests/test_h_mad_shared_gate_policy.py::test_codex_gate_self_check_shell_policy_fail_is_a_verdict_with_exit_0`
   — the gate loaded in-process from its path with `importlib` (as item 3 loads it);
   `monkeypatch.setattr(gate, "_safe_shell_command", lambda *a, **k: True)` and
   `monkeypatch.setattr(sys, "argv", ["h-mad-codex-tdd-gate.py", "--self-check"])`; `rc =
   gate.main()`, then `capsys.readouterr()`. Asserts, separately, stdout stripped equals
   `CODEX-TDD-GATE: FAIL shell-policy`, stderr is empty, and `rc == 0`. `main` reads
   `_safe_shell_command` from the gate's globals both before the move (its own `def`) and after
   (the imported binding), so the patch reaches it at RED and at GREEN. 1 node, F: at RED the
   reading above gives stdout empty and `rc=2`, an assertion failure, not an import error.
6. `tests/test_h_mad_shared_gate_policy.py::test_codex_gate_self_check_parser_fail_is_a_verdict_with_exit_0`
   — as item 5, with `monkeypatch.setattr(gate, "_patch_header_paths", lambda patch:
   (["wrong.py"], ""))` instead (`_patch_header_paths` is not moved, so it stays the gate's own
   global). Asserts, separately, stdout stripped equals `CODEX-TDD-GATE: FAIL parser`, stderr is
   empty, and `rc == 0`. 1 node, F: at RED the reading above gives stdout empty and `rc=2`.

**RED split**: 29 nodes, 29 F, 0 P (17 + 8 + 1 + 1 + 1 + 1).

**Regression guards**: every existing Codex gate test unmodified, notably
`tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_gate_kind[judge-error]` (the import-failure
fixture: its tree has no identity module),
`tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_gate_judge_timeout_reason`, the
`module._safe_shell_command`, `module._payload_cwd_base` and `SIMPLE_SHELL_COMMAND` reads in
`tests/test_h_mad_codex_tdd_gate_judge.py`, and `hook.SAFE_HMAD_SCRIPT_OPTIONS` in
`tests/test_h_mad_codex_runtime.py`. The committed probe
`docs/03-analysis/probes/agy-coder-fallback/fr6_import_failure_pair.py` is re-run after GREEN and
must print `PROBE: PASS`.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/shared_gate_policy.json`, 4 rows:
| name | mutant | test |
|---|---|---|
| `fr6-import-guard-dropped` | the guarded import replaced by a bare top-level import | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_gate_kind[judge-error]` |
| `fr6-self-check-policy-import-branch-dropped` | the `FAIL policy-import` branch removed | `tests/test_h_mad_shared_gate_policy.py::test_codex_gate_self_check_reports_a_policy_import_failure` |
| `codex-selfcheck-shell-policy-exits-2` (signal discipline, I4) | the `FAIL shell-policy` branch's `return 0` → `return 2` | `tests/test_h_mad_shared_gate_policy.py::test_codex_gate_self_check_shell_policy_fail_is_a_verdict_with_exit_0` |
| `codex-selfcheck-parser-exits-2` (signal discipline, I4) | the `FAIL parser` branch's `return 0` → `return 2` | `tests/test_h_mad_shared_gate_policy.py::test_codex_gate_self_check_parser_fail_is_a_verdict_with_exit_0` |

Row `G2` stays killed through the re-raise; no row removes the re-raise (design: an equivalent
mutant in decision).

**Re-pointing (R-3, AC-6.1)**: the 31 rows Task 0's M-4 lists get `file`
`scripts/h_mad_target_identity.py`. Then `--check-anchors` and a lone `MUTATION: ALL_CAUGHT` run
over every spec naming either edited file: `codex_gate_judge_wiring.json`,
`codex_gate_shell_allowance.json`, `codex_gate_tmp_reports.json`,
`assemble_tdd_mutation_rows.json`, `tdd_gate_differential.json`, `target_identity.json`,
`shared_gate_policy.json`. A `find` of `target_identity.json` that the moved code makes non-unique
is re-anchored here. Re-run `census_mutation_rows.py`; the post-move reading is 0 Codex-gate rows
inside a moved span.

**Rows whose text the move changes** (sweep at `4e4b5ded`: the `find` and `replace` of each of
the 31 rows, checked for names the identity module will not define). Two of the 31 need more than
the `file` change:
- `codex_gate_judge_wiring.json` `CX-FOLD` (`find`
  `    path = Path(_load_identity().fold_py_suffix(relative))`, in `_is_production_python`): the
  move rewrites that line, so `find` becomes `    path = Path(fold_py_suffix(relative))`.
  `replace` (`    path = Path(relative)`) and `test` are unchanged. Re-pointing `file` alone leaves 0
  matches, and that fails `--check-anchors` and
  `tests/test_h_mad_mutation_harness.py::test_committed_mutation_specs_are_not_drifted`.
- `codex_gate_judge_wiring.json` `CX-FORCE-SCRIPT` (`find` in `_safe_argv`, a moved function): its
  `find` moves byte for byte, but its `replace` calls `_load_identity().canonical_directory`,
  and `_load_identity` stays in the Codex gate. Run from the identity module, that mutant raises
  `NameError` instead of forcing the canonical spelling, so its `test`
  (`tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_safe_shell_script_keeps_path_resolve_spelling`)
  would be killed by a crash. `replace` becomes the same line with `_load_identity().` removed, so
  it calls the module's own `canonical_directory`.
No other row among the 31 names a symbol outside the moved set. `G3`'s `replace` names `Path`,
which the moved code also uses, so the identity module imports `Path` and every other name the
moved code uses. Codex-gate rows outside the moved spans that sit near this Task's other edits are
`G2` (`    except Exception as exc:  # M:G2`, in `main`) and `CX-ROOT-ENTER` (in `_main_guarded`).
The `--self-check` branch and the re-raise are inserted beside them and leave both `find` texts
unique. `codex_gate_tmp_reports.json` `python-under-tmp-admitted` and
`the-name-check-reads-the-link-not-its-target` call `_load_identity()` inside `_tmp_report_target`,
which does not move, so both stay valid.

**Acceptance Criteria**:
- [ ] AC-6.1 (one definition): items 1–2 pass.
- [ ] AC-6.1 (existing shell tests unmodified): the regression guards pass.
- [ ] AC-6.1 (re-pointed rows): each of the 7 specs → `MUTATION: ALL_CAUGHT` against
  `h_mad_target_identity.py`; `CX-FOLD` and `CX-FORCE-SCRIPT` each killed by an assertion of its
  `test`, not by an exception.
- [ ] Signal discipline (I4): items 5 and 6 pass; `test_codex_hook_self_check_reports_machine_readable_pass`
  passes unmodified.
- [ ] AC-X: `shared_gate_policy.json` (4 rows) → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 3 (both re-anchor rows of `tdd_gate_differential.json`,
which names the Claude hook, the Codex gate and the identity module; Task 4 starts from Task 3's
anchors).

---

## Task 5: the agy gate — contract, root, activity, classes (a) and (d)

**Production files**: `h-mad/hooks/h-mad-agy-tdd-gate.py` (new)
**Test files**: `h-mad/tests/test_h_mad_agy_tdd_gate.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §"FR-4", steps 1–6 and classes (a) and (d). `main` reads stdin with a 2 s
bound, builds the decision inside one `try`, and prints exactly one JSON object from a `finally`
that emits a `judge-error` deny when nothing was decided; exit 0 always. The judge, the identity
module and the policy names are imported inside that `try`. Class (a) (the 11 names) is allowed
before any state is read. The root is `git -C <handler cwd>/.. rev-parse --show-toplevel`,
canonicalised with `canonical_directory`; then `os.chdir(root)` once.
`phase5_status = _any_phase5_status(root)`. Step 5's `workspacePaths` cross-check fires only under
`S` (`phase5_status in {"active", "unknown"}`). Class (d) denies `tool-not-admitted` under
`active`, `judge-error` under `unknown`, and allows under `inactive`.

**Classes (b) and (c) take class (d)'s rule in this Task** (deny under `S`, allow under
`inactive`): fail-closed, and replaced by Tasks 6 and 7. The class table itself is complete here:
`CLASS_A` (11 names), `CLASS_B` (5 names), `run_command`, and everything else.

`--self-check` runs the design's four checks and prints exactly one line on stdout:
- `AGY-TDD-GATE: PASS`, exit 0, when all four hold;
- `AGY-TDD-GATE: FAIL policy-import`, exit 2, when the judge, the identity module or the policy
  names do not import, or `JUDGE_BUDGET_S` cannot be read. The gate cannot run, so this is an
  operational error;
- `AGY-TDD-GATE: FAIL classification` (`view_file` not in class (a), or `call_mcp_tool` not in
  class (d)) or `AGY-TDD-GATE: FAIL shell-policy` (`_safe_shell_command` admits
  `python3 -c "open('x','w').write('x')"`), each with **exit 0**. These are ordinary verdicts, and
  the token carries them (the base invariant on audit-gate signal discipline).
The exit 0 on the two verdict `FAIL`s is the orchestrator's cycle-1 decision, recorded in design
v1.4 (`2cd5d7f1`) §"FR-4" `--self-check` as the rule: a verdict FAIL exits 0, a could-not-run
FAIL exits 2. Task 9's check is unaffected: it requires the exact line
`AGY-TDD-GATE: PASS` and exit 0, so a `FAIL` line with exit 0 reads as `self-check-failed`.

**Code structure**:
```python
CLASS_A: frozenset[str]          # the 11 names of design FR-4
CLASS_B: frozenset[str]          # the 5 names
PATH_KEYS: dict[str, tuple[str, ...]]   # {"write_to_file": ("TargetFile",)}
GATE_KINDS: frozenset[str]       # judge-error, tool-not-admitted, target-outside-root,
                                 # allowance-file-write, shell-not-admitted
def classify_tool(name: str) -> str: ...   # "a" | "b" | "c" | "d"
def main() -> int: ...
```

**Test harness**: `_root(tmp_path, status)` builds a git repository whose
`docs/.bkit-memory.json` reads `active` (a `step5` record), `inactive` (no `step5` record) or
`unknown` (not JSON). `_decide(root, payload, cwd=None)` runs the gate with `sys.executable`,
`cwd=<root>/.agents` by default, and asserts exactly one JSON object on stdout and exit 0. On every
deny it asserts the reason ends with exactly one `kind=` token whose value is in `GATE_KINDS` or in
`h_mad_tdd_judge.KINDS` (12 names at `4e4b5ded`): AC-4.2's scan of every deny the suite produces.

**Tests** (all in `h-mad/tests/test_h_mad_agy_tdd_gate.py`):
1. `tests/test_h_mad_agy_tdd_gate.py::test_every_exit_prints_one_json_object` — `not-json`,
   `json-array`, `toolcall-not-object`, `name-not-str`; deny `kind=judge-error`. 4 nodes.
2. `tests/test_h_mad_agy_tdd_gate.py::test_class_a_allowed_before_state_is_read` — one id per
   class-(a) name (11), run from a directory outside any git repository with an `unknown` state
   file beside it; allow. 11 nodes.
3. `tests/test_h_mad_agy_tdd_gate.py::test_unknown_tool_is_class_d` — `call_mcp_tool-inactive`
   (allow), `unlisted-name-active` (`brand_new_tool`, deny `tool-not-admitted`). 2 nodes.
4. `tests/test_h_mad_agy_tdd_gate.py::test_workspace_paths_cross_check` — tool `call_mcp_tool`:
   `unknown-denies` (`workspacePaths=["/elsewhere"]`, `judge-error`), `inactive-stands-down`
   (same paths, allow), `naming-root-passes` (`active`, `workspacePaths=[root]`,
   `tool-not-admitted`). 3 nodes.
5. `tests/test_h_mad_agy_tdd_gate.py::test_deny_row_kind` — one id per row of design §"FR-4"
   "Every deny" this Task owns: `malformed-payload`, `root-unresolvable`,
   `exception-after-step-2` (in-process: `_any_phase5_status` patched to raise), `workspace-paths`
   (`active`), `class-d-active`, `class-d-unknown`; each asserts its row's kind. 6 nodes.
6. `tests/test_h_mad_agy_tdd_gate.py::test_self_check_passes`. 1 node.
7. `tests/test_h_mad_agy_tdd_gate.py::test_self_check_fails_on_a_policy_import_failure` — the gate
   copied beside a real judge and no identity module; stdout is exactly
   `AGY-TDD-GATE: FAIL policy-import` and the exit is 2. 1 node.
8. `tests/test_h_mad_agy_tdd_gate.py::test_classification_table_is_the_recorded_inventory` —
   every `CLASS_A` and `CLASS_B` name and `run_command` is in the committed log's first `init`
   `tools`; the remainder is 41 names. 1 node.
9. `tests/test_h_mad_agy_tdd_gate.py::test_self_check_policy_fail_is_a_verdict_with_exit_0` —
   in-process, the gate loaded from its path and `sys.argv` patched to `--self-check`:
   `classification` (`CLASS_A` patched to drop `view_file`) and `shell-policy`
   (`_safe_shell_command` patched to return `True`). Each id asserts that stdout is exactly
   `AGY-TDD-GATE: FAIL classification` or `AGY-TDD-GATE: FAIL shell-policy`, and separately that
   `main()` returns 0. The fixture imports the policy, so it is not item 7's import failure. 2 nodes.

**RED split**: 31 nodes, 31 F, 0 P (4 + 11 + 2 + 3 + 6 + 1 + 1 + 1 + 2). The file does not exist.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/agy_tdd_gate.json`, 5 rows here (4
design rows and 1 signal-discipline row):
| name | mutant | test |
|---|---|---|
| `selfcheck-verdict-fail-exits-2` (signal discipline) | the `FAIL shell-policy` branch returns 2 | `tests/test_h_mad_agy_tdd_gate.py::test_self_check_policy_fail_is_a_verdict_with_exit_0` |
| `fr4-class-a-name-moved` | `view_file` moved from `CLASS_A` to the class-(d) default | `tests/test_h_mad_agy_tdd_gate.py::test_class_a_allowed_before_state_is_read` |
| `fr4-class-d-default-allows` | the class-(d) default replaced by allow | `tests/test_h_mad_agy_tdd_gate.py::test_unknown_tool_is_class_d` |
| `fr4-finally-deny-dropped` | the `finally` deny removed | `tests/test_h_mad_agy_tdd_gate.py::test_every_exit_prints_one_json_object` |
| `fr4-step5-s-dropped` | step 5's `S` condition removed | `tests/test_h_mad_agy_tdd_gate.py::test_workspace_paths_cross_check` |

The design's fixture for the step-5 row is `run_command` `ls` with `workspacePaths=[]` under
`inactive`, which needs class (c); Task 7 adds it as a second killer. Here the row is killed by
`test_workspace_paths_cross_check[inactive-stands-down]`.

**Acceptance Criteria**:
- [ ] AC-4.1 (inactive allows, class (a) and (d) members, unknown tool, `workspacePaths` under
  `unknown`): items 2–4 pass.
- [ ] AC-4.2 (one JSON object on every exit; this Task's 6 deny rows each with its kind): items
  1, 5 and 7 pass, and `_decide`'s kind assertion holds on every deny.
- [ ] Signal discipline: item 9 passes, each verdict `FAIL` with exit 0, and item 7 passes with
  exit 2.
- [ ] AC-X: the 5 rows above → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 4 (policy names), Task 2 (judge).

---

## Task 6: the agy gate — class (b), T1–T7

**Production files**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test files**: `h-mad/tests/test_h_mad_agy_tdd_gate.py`
**Task shape**: `new-behaviour`

**Description**: Design §"FR-4" class (b). Targets are the values of `PATH_KEYS[name]` keys that
are present and are a non-empty `str`; no target → `judge-error` under `S`, allow under
`inactive`. Each target runs T1 canonicalise (base = root), T2 unresolvable, T3 containment, T4
outside the root (`artifact = Path(adp) if isinstance(adp, str) and adp else None`, computed
before `S` is read; every name in `resolved.names` tested for `.py` through `fold_py_suffix`),
T5 the allowance file, T6 production over every name (`min` of the collected tuples), T7 the chain
(`read_chain`, `unreadable` → `judge-error`, not `active` → allow, else `judge`; a non-ALLOW
passes the judge's kind through). T6–T7 run whatever `phase5_status` is.

**OD-2, decided (operator, 2026-10-16): a directory target is refused under `S`.** A class-(b)
target whose `resolved.target` is an existing directory (`TargetFile` `.`, `src/`, or any other
existing directory, a symlink to one included) denies `judge-error` under `S` and is allowed under
`inactive`. Without this check the T1–T7 sequence allows such a target under `active`. Read at
`4e4b5ded` on a scratch root: `canonicalise(root, ".", root)`, `canonicalise(root, "src/", root)`,
`canonicalise(root, "src", root)` and `canonicalise(root, root, root)` each return
`unresolvable=False` and `names=()`, so T2 does not fire, T3 and T5 pass, and T6 has no name to
judge. The check is **T2a**, right after T2: `Path(resolved.target).is_dir()` → `judge-error` under
`S` (the reason names the directory target), allow under `inactive`. It runs before T3, so an
out-of-root directory under `S` also denies `judge-error`. Residual: a target ending in `/` that
names no existing directory is not covered by T2a and goes through T3–T7 as a file name. Spec v1.10
(`c283bb63`) records OD-2 as D-16 and design v1.4 (`2cd5d7f1`) as T2a, between T2 and T3.

**Tests** (in `h-mad/tests/test_h_mad_agy_tdd_gate.py`):
1. `tests/test_h_mad_agy_tdd_gate.py::test_class_b_no_target` — `no-key-unknown`,
   `no-key-inactive`, `empty-active`, `empty-unknown`, `empty-inactive`, `null-active`,
   `number-active`, `list-active`, `number-inactive` (`TargetFile: 5`), `list-inactive`
   (`TargetFile: ["x"]`); deny `judge-error` under `S`, allow under `inactive`. 10 nodes: 6 P (the
   two `unknown` and four `inactive` ids match class (d)'s rule), 4 F.
   The two truthy non-`str` `inactive` ids are the discriminators for row
   `fr4-class-b-target-presence-only` (audit cycle 2, I1). Under that mutant the value reaches T1,
   and `canonicalise(root, 5, root)` raises `TypeError` (`os.path.isabs(5)`; also without the
   `cwd` argument), which design §"FR-4" "Every deny" row "an exception after step 2" denies
   `judge-error` whatever the status; the correct gate has no target and allows under `inactive`.
   The other eight ids cannot separate the two: `""`, `None` and an absent key are falsy, and
   `canonicalise`'s `if not target:` returns the root directory, which T2a refuses under `S` and
   allows under `inactive`, the same as the no-target rule; the truthy non-`str` `active` ids
   raise into the same `judge-error` deny. `null-inactive` (the cycle-2 report's suggestion) does
   not discriminate for that reason. Controlled pair, run at `84ec2133` on a scratch model (the
   class-(b) target selection, T1 with the live `canonicalise`, T2, T2a, and the exception row),
   value guard against key presence over the 8 ids above plus `null-inactive`, `number-inactive`
   and `list-inactive`: 9 same, 2 differ (`number-inactive` and `list-inactive`: value guard
   `allow`, key presence `deny judge-error` from `TypeError`). The scratch was deleted.
2. `tests/test_h_mad_agy_tdd_gate.py::test_class_b_tools_without_a_recorded_key_deny_under_active`
   — `replace_file_content`, `multi_replace_file_content`, `sed_file`, `notebook_edit`; deny
   `judge-error`. 4 nodes, F.
3. `tests/test_h_mad_agy_tdd_gate.py::test_production_py_with_failing_test_allows`. 1 node, F.
4. `tests/test_h_mad_agy_tdd_gate.py::test_artifact_directory_path` — `non-py-allowed` (`active`),
   `py-denied` (`active`, `target-outside-root`), `non-str-inactive` (`artifactDirectoryPath: 5`,
   a non-`.py` target outside `/tmp` and the root, allow). 3 nodes: 1 P (`non-str-inactive`), 2 F.
5. `tests/test_h_mad_agy_tdd_gate.py::test_tmp_non_py_write_allowed_under_active`. 1 node, F.
6. `tests/test_h_mad_agy_tdd_gate.py::test_hardlinked_production_name_is_judged` —
   `src/test_a.py` hard-linked to `src/z.py`, no failing test → deny with the judge's kind. 1 node, F.
7. `tests/test_h_mad_agy_tdd_gate.py::test_unsearchable_chain_denies_although_the_scan_is_inactive`
   — a production `.py` whose chain holds a `chmod 000` `docs/`. 1 node, F.
8. `tests/test_h_mad_agy_tdd_gate.py::test_out_of_root_py_denies_under_unknown` →
   `target-outside-root`. 1 node, F.
9. `tests/test_h_mad_agy_tdd_gate.py::test_deny_row_kind` gains 7 ids: `class-b-no-target`,
   `t2-unresolvable`, `t2a-directory` (`TargetFile` `.`; design v1.4's seventeenth row),
   `t4-outside-root`, `t5-allowance-file`, `t7-chain-unreadable`, `t7-judge-non-allow`, all under
   `active`. 7 nodes, F (`t2a-directory` at RED gets class (d)'s `tool-not-admitted`).
10. `tests/test_h_mad_agy_tdd_gate.py::test_class_b_directory_target` — OD-2. `write_to_file` with
    `TargetFile` `.` and with `src/` (an existing directory in the fixture root), each under
    `active`, `unknown` and `inactive`: ids `dot-active`, `dot-unknown`, `dot-inactive`,
    `src-active`, `src-unknown`, `src-inactive`. Each id asserts deny `kind=judge-error` under
    `active` and `unknown`, and allow under `inactive`. 6 nodes: 2 F (the two `active` ids: class
    (d)'s rule denies `tool-not-admitted` there), 4 P (class (d)'s rule already gives `judge-error`
    under `unknown` and allow under `inactive`; these pin T2a at GREEN).

**RED split**: 35 nodes; 24 F, 11 P (10 + 4 + 1 + 3 + 1 + 1 + 1 + 1 + 7 + 6 = 35; P = 6 in item 1,
1 in item 4 and 4 in item 10). At the RED base class (b) takes class (d)'s rule (Task 5), which
fixes every value above.

**Mutation rows** — `agy_tdd_gate.json`, 11 rows here, all design rows (design v1.4 lists the
OD-2 row `od2-directory-target-check-dropped` as its "T2a removed" bullet):
| name | mutant | test |
|---|---|---|
| `od2-directory-target-check-dropped` (OD-2) | T2a removed | `tests/test_h_mad_agy_tdd_gate.py::test_class_b_directory_target` |
| `fr4-no-path-key-deny-dropped` | the no-target deny removed | `tests/test_h_mad_agy_tdd_gate.py::test_class_b_tools_without_a_recorded_key_deny_under_active` |
| `fr4-artifact-py-refusal-dropped` | T4's `.py` refusal removed for `artifactDirectoryPath` | `tests/test_h_mad_agy_tdd_gate.py::test_artifact_directory_path` |
| `fr4-t3-after-t5` | the allowance check moved before containment | `tests/test_h_mad_agy_tdd_gate.py::test_tmp_non_py_write_allowed_under_active` |
| `fr4-t6-target-only` | T6 judges `resolved.target` alone | `tests/test_h_mad_agy_tdd_gate.py::test_hardlinked_production_name_is_judged` |
| `fr4-t6-t7-skipped-when-inactive` | T6–T7 skipped when `phase5_status == "inactive"` | `tests/test_h_mad_agy_tdd_gate.py::test_unsearchable_chain_denies_although_the_scan_is_inactive` |
| `fr4-t7-unreadable-dropped` | T7's `unreadable` branch removed | `tests/test_h_mad_agy_tdd_gate.py::test_unsearchable_chain_denies_although_the_scan_is_inactive` |
| `fr4-t4-artifact-str-check` | `isinstance(adp, str) and adp` → `adp is not None` | `tests/test_h_mad_agy_tdd_gate.py::test_artifact_directory_path` |
| `fr4-class-b-target-presence-only` | the non-empty-`str` test weakened to key presence | `tests/test_h_mad_agy_tdd_gate.py::test_class_b_no_target` |
| `fr4-kind-target-outside-root` | `target-outside-root` replaced by `judge-error` at its site | `tests/test_h_mad_agy_tdd_gate.py::test_deny_row_kind` |
| `fr4-kind-allowance-file-write` | `allowance-file-write` replaced by `judge-error` at its site | `tests/test_h_mad_agy_tdd_gate.py::test_deny_row_kind` |

T4's empty-string arm has no row: the design declares it an equivalent mutant at the full gate
(step 3's `chdir`), and it stays unpinned (design residual).

**Acceptance Criteria**:
- [ ] AC-4.1 (class (b) no key and `""` under each status, production `.py` with and without a
  failing test, `/tmp` and `artifactDirectoryPath`, the `chmod 000` chain, out-of-root `.py`
  under `unknown`): items 1–8 pass.
- [ ] AC-4.2 (this Task's 7 deny rows): item 9 passes.
- [ ] OD-2: item 10 passes, and under `od2-directory-target-check-dropped` its `active` ids fail.
- [ ] I1: under `fr4-class-b-target-presence-only`, item 1's `number-inactive` and `list-inactive`
  ids fail by assertion (deny `judge-error` where allow is expected).
- [ ] AC-X: the 11 rows → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 5.

---

## Task 7: the agy gate — class (c)

**Production files**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test files**: `h-mad/tests/test_h_mad_agy_tdd_gate.py`
**Task shape**: `new-behaviour`

**Description**: Design §"FR-4" class (c). `args.CommandLine` missing or not a `str` →
`judge-error` under `S`, allow under `inactive`. `cwd` is computed as the Codex gate's
`_command_cwd` computes it, with the root for the session (`Cwd` non-`str` →
`MALFORMED_WORKDIR`; absent, `None` or `""` → the root; relative → `str(root /
Path(Cwd).expanduser())`; absolute → `str(Path(Cwd).expanduser())`). When `cwd` names an existing
directory the gate calls `os.chdir(cwd)`; otherwise it stays in the root and still judges with that
`cwd`; no case denies `judge-error`. The composition: `unknown` → `judge-error`; `active` →
`_safe_shell_command(command, root, cwd)`, then `_shell_allowance` (a `str` result →
`judge-error`), then `_operator_allowed` (false → `shell-not-admitted`, the reason naming the
class-(b) tools and `SHELL_ALLOW_FILE`); `inactive` → allow.

**Tests** (in `h-mad/tests/test_h_mad_agy_tdd_gate.py`):
1. `tests/test_h_mad_agy_tdd_gate.py::test_run_command_missing_command_line` — `absent-inactive`,
   `nonstr-inactive` (allow), `absent-unknown` (`judge-error`). 3 nodes, P.
2. `tests/test_h_mad_agy_tdd_gate.py::test_run_command_ls_with_empty_workspace_paths` —
   `inactive-allows`, `active-denies`, `unknown-denies` (`judge-error`). 3 nodes, P (step 5 and
   class (d)'s rule already give these at the RED base).
3. `tests/test_h_mad_agy_tdd_gate.py::test_run_command_read_only_command_allowed_under_active` —
   `ls`. 1 node, F.
4. `tests/test_h_mad_agy_tdd_gate.py::test_unsafe_tuple_parity` — `ast` locates the tuple
   assigned to `unsafe` inside the Codex gate's `main` (exactly one; 4 members at `4e4b5ded`), and
   the agy gate denies each member under `active` with `kind=shell-not-admitted`. 1 node, F.
5. `tests/test_h_mad_agy_tdd_gate.py::test_cwd_outside_the_root_refuses_a_relative_venv_interpreter`
   — `outside-absolute`, `dotdot-escape`, `absent` (`str(root / "no-such-dir")`); deny
   `shell-not-admitted`. 3 nodes, F.
6. `tests/test_h_mad_agy_tdd_gate.py::test_root_venv_interpreter_is_admitted` — the positive
   control. 1 node, F.
7. `tests/test_h_mad_agy_tdd_gate.py::test_malformed_cwd_fails_closed` — `zero`, `list`, `dict`,
   `true`; deny `shell-not-admitted`. 4 nodes, F.
8. `tests/test_h_mad_agy_tdd_gate.py::test_empty_cwd_behaves_as_absent` — the root's relative
   `.venv` interpreter with `Cwd=""` is admitted. 1 node, F.
9. `tests/test_h_mad_agy_tdd_gate.py::test_ls_under_each_bad_cwd_is_allowed` —
   `outside-absolute`, `dotdot-escape`, `absent`, `zero`, `list`, `dict`, `true`. 7 nodes, F.
10. `tests/test_h_mad_agy_tdd_gate.py::test_relative_cwd_is_joined_against_the_root` — a relative
    `Cwd` naming a sub-project whose `.venv` interpreter the command uses. 1 node, F.
11. `tests/test_h_mad_agy_tdd_gate.py::test_deny_row_kind` gains 4 ids: `class-c-no-command`
    (`active`), `class-c-unknown`, `class-c-allowance-unreadable`, `class-c-policy-refusal`.
    4 nodes: 1 P (`class-c-unknown`: class (d)'s `unknown` rule gives the same kind), 3 F.
12. `tests/test_h_mad_agy_tdd_gate.py::test_operator_allowance_admits_a_listed_command` — a
    command the policy refuses, listed in `SHELL_ALLOW_FILE`, is allowed under `active`. 1 node, F.

**RED split**: 30 nodes; 23 F, 7 P (3 + 3 + 1 + 1 + 3 + 1 + 4 + 1 + 7 + 1 + 4 + 1 = 30; P = 3 in
item 1, 3 in item 2, 1 in item 11).

**Mutation rows** — `agy_tdd_gate.json`, 4 rows here:
| name | mutant | test |
|---|---|---|
| `fr4-class-c-command-s-dropped` | the missing-`CommandLine` deny fires whatever the status | `tests/test_h_mad_agy_tdd_gate.py::test_run_command_missing_command_line` |
| `fr4-kind-shell-not-admitted` | `shell-not-admitted` replaced by `judge-error` at its site | `tests/test_h_mad_agy_tdd_gate.py::test_deny_row_kind` |
| `fr4-class-c-bad-cwd-judge-error` | a `cwd` that is not an existing directory denies `judge-error` | `tests/test_h_mad_agy_tdd_gate.py::test_ls_under_each_bad_cwd_is_allowed` |
| `fr4-class-c-cwd-joined-to-handler-dir` | a relative `Cwd` joined against the handler's directory | `tests/test_h_mad_agy_tdd_gate.py::test_relative_cwd_is_joined_against_the_root` |

`agy_tdd_gate.json` holds 5 + 11 + 4 = 20 rows after this Task: the design's FR-4 count of 19
(4 + 11 + 4, design v1.4), plus Task 5's signal-discipline row. The step-5 row (Task 5)
also bites item 2's `inactive-allows`.

**Acceptance Criteria**:
- [ ] AC-4.1 (class (c) member, `run_command` refused under `unknown`, the `workspacePaths=[]`
  trio): items 1–3, 9 and 11 pass.
- [ ] AC-4.2 (this Task's 4 deny rows): item 11 passes; `test_deny_row_kind` now has 17 ids
  (6 + 7 + 4), one per row of design v1.4 §"FR-4" "Every deny" (17 rows).
- [ ] AC-6.1 (`unsafe` parity): item 4 passes.
- [ ] AC-X: `agy_tdd_gate.json` (20 rows) → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 6.

---

## Task 8: the agy gate differentials

**Production files**: none
**Test files**: `h-mad/tests/test_h_mad_agy_tdd_gate_differential.py` (new)
**Task shape**: `gate` — a verdict over code Tasks 5–7 built; it writes no production file.

**Description**: Two corpora, each judged by both gates, asserting the same admit/deny in every
cell outside design §"FR-4" "Deliberate differences", and the same kind wherever the Codex deny
carries one. The Codex gate gets `Write` with `file_path` (no payload `cwd`) or its shell tool; the
agy gate gets `write_to_file` with `TargetFile` or `run_command` with `CommandLine`.

1. `tests/test_h_mad_agy_tdd_gate_differential.py::test_target_differential` — 11 shapes ×
   `active`, `inactive`, `unknown`: `in-root-production`, `test-file`, `hardlink-test-to-production`,
   `allowance-file-lower`, `allowance-file-upper`, `docs-py`, `tmp-non-py`, `tmp-py`,
   `outside-non-tmp`, `unresolvable`, `chmod000-chain`. 33 nodes.
2. `tests/test_h_mad_agy_tdd_gate_differential.py::test_shell_differential` — 6 commands (`ls`,
   `git status`, `python3 -c "open('x','w').write('x')"`, `rm -rf build`,
   `.venv/bin/python -m pytest -q`, `cat a > b`) × 3 allowance-file states (`absent`,
   `lists-the-command`, `unreadable`), under `active`. 18 nodes.

**RED split**: 51 nodes, 0 F, 51 P (33 + 18). Any cell that fails is not fixed in this Task: it is
a finding against Task 6 or 7, or, when the cell is outside the stated differences and both gates
behave as designed, against the design.

**Mutation rows**: none (the corpora pin agreement; the guards' rows are in Tasks 5–7).

Neither corpus holds a directory target. OD-2's T2a (Task 6) is a difference from the Codex gate,
which this feature does not change. It is pinned by Task 6 item 10, not here.

**Acceptance Criteria**:
- [ ] AC-4.1 (the target differential): item 1 passes.
- [ ] Design §"FR-4" class (c) residual (the shell differential): item 2 passes.

**Dependencies on other tasks**: Task 7.

---

## Task 9: the agy wiring check

**Production files**: `h-mad/scripts/h_mad_hook_wiring.py`
**Test files**: `h-mad/tests/test_h_mad_hook_wiring_agy.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §"FR-5". `main` gains `--agy`, which calls `check_agy(project_root)`,
prints its one line and exits with its code; without `--agy` behaviour is unchanged (today's
`main` takes only `--project-root`). Reasons in FR-5's order: `no-hooks-file` (exit 0; a present
file that is not JSON or not an object → `AGY-GATE: UNREADABLE` with `file=` the
percent-encoded path and `error=` the exception name, or `not-an-object`; exit 2),
`no-entry`, `disabled`, `matcher-narrow`, `bad-command` (the `shlex.split` must equal
`["python3", "~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py"]`),
`timeout-below-floor` (floor `math.ceil(JUDGE_BUDGET_S + 20)`, 60 at `JUDGE_BUDGET_S = 40.0`; an
absent timeout reads as agy's 30), `self-check-failed` (the gate's `--self-check` must print exactly
`AGY-TDD-GATE: PASS` and exit 0 within 30 s). Otherwise `AGY-GATE: WIRED`, exit 0.

**Code structure**:
```python
AGY_HOOK_COMMAND = ["python3", "~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py"]
def check_agy(project_root: Path) -> tuple[str, int]: ...
```
`check_agy` reads the budget at call time as an attribute of the module imported by name,
`import h_mad_tdd_judge` (the scripts directory is already on `sys.path` beside
`h_mad_hook_wiring.py`), then `math.ceil(h_mad_tdd_judge.JUDGE_BUDGET_S + 20)`. It does not copy
the value at import (`from h_mad_tdd_judge import JUDGE_BUDGET_S`) and does not load the judge
by path under another module name. Either would leave item 4's patched budget unread.

**Tests** (all in `h-mad/tests/test_h_mad_hook_wiring_agy.py`; `HOME` points at a fixture holding
`.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py` as a symlink to the gate under test):
1. `tests/test_h_mad_hook_wiring_agy.py::test_unwired_reason` — `no-hooks-file`, `no-entry`,
   `entry-not-object`, `disabled`, `matcher-narrow`, `pretooluse-absent`, `bad-command`,
   `timeout-below-floor`, `timeout-absent`, `self-check-failed`; stdout
   `AGY-GATE: UNWIRED reason=` plus the reason, asserted separately from exit 0. 10 nodes.
2. `tests/test_h_mad_hook_wiring_agy.py::test_unreadable_hooks_file` — `not-json`,
   `not-an-object`. Each id asserts that stdout is the one line `AGY-GATE: UNREADABLE file=` plus
   the percent-encoded path plus ` error=` plus `JSONDecodeError` or `not-an-object`, and,
   separately, exit 2. Exit 2 alone would pass at RED, because argparse refuses the absent `--agy`
   with exit 2. 2 nodes.
3. `tests/test_h_mad_hook_wiring_agy.py::test_wired`. 1 node.
4. `tests/test_h_mad_hook_wiring_agy.py::test_timeout_floor_is_derived_from_the_judge_budget` —
   in-process: `import h_mad_hook_wiring as hw` and `import h_mad_tdd_judge` (as
   `test_h_mad_hook_wiring.py` imports `hw`), `hw.check_agy(root)` called directly and its line's
   reason asserted. Ids: `budget-40-timeout-59` (`timeout-below-floor`), `budget-40-timeout-60`
   (`WIRED`), and, with `monkeypatch.setattr(h_mad_tdd_judge, "JUDGE_BUDGET_S", 41.1)` (floor
   `math.ceil(61.1)` = 62), `budget-41.1-timeout-61` (`timeout-below-floor`) and
   `budget-41.1-timeout-62` (`WIRED`). 4 nodes. The two `budget-41.1` ids are the connection pin
   (audit cycle 2, I3): a floor hardcoded to 60 gives `WIRED` at timeout 61. Controlled pair, run at
   `84ec2133` on a scratch model (the formula reading `h_mad_tdd_judge.JUDGE_BUDGET_S` live against
   a hardcoded 60, timeouts 59–62, budgets 40.0 and 41.1): at 40.0 all four timeouts agree; at 41.1
   timeouts 60 and 61 differ (formula `timeout-below-floor`, hardcoded `WIRED`), 59 and 62 agree.
   The scratch was deleted.
5. `tests/test_h_mad_hook_wiring_agy.py::test_empty_matcher_counts_as_wide`. 1 node.

**RED split**: 18 nodes, 18 F, 0 P (10 + 2 + 1 + 4 + 1). Item 4 fails at RED because
`hw.check_agy` does not exist (`AttributeError` inside the test body; a `new-behaviour` Task, not a
WIRE-PIN).

**Regression guards**: the existing `h_mad_hook_wiring.py` tests, unmodified.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/hook_wiring_agy.json`: 7 rows, one per
reason check removed (`fr5-no-hooks-file`, `fr5-no-entry`, `fr5-disabled`, `fr5-matcher-narrow`,
`fr5-bad-command`, `fr5-timeout-below-floor`, `fr5-self-check-failed`), each with `test`
`tests/test_h_mad_hook_wiring_agy.py::test_unwired_reason`, plus 1 connection row (I3), 8 rows in
all:

| name | mutant | test |
|---|---|---|
| `fr5-timeout-floor-hardcoded-60` (connection, I3) | `math.ceil(h_mad_tdd_judge.JUDGE_BUDGET_S + 20)` → `60` | `tests/test_h_mad_hook_wiring_agy.py::test_timeout_floor_is_derived_from_the_judge_budget` |

`--check-anchors` also over
`hook_wiring.json`, which holds 12 rows: the 10 Task 0's M-2 counts for
`scripts/h_mad_hook_wiring.py`, plus 2 on `SKILL.md` (`docs-lose-the-no-halt-rule`,
`docs-lose-a-detail-line`). The `--agy` branch is added to `main` before its `root =` line. The
one row in `main`, `unknown-exits-0` (`find` from `print("WIRING: UNKNOWN reason=no_settings")`),
is left byte for byte. That makes it the only existing row near this Task's edit.

**Acceptance Criteria**:
- [ ] AC-5.1 (each reason from its own fixture): item 1 passes.
- [ ] AC-5.2 (the check's half of each row): items 1–3 pass.
- [ ] AC-X: `hook_wiring_agy.json` (8 rows) → `MUTATION: ALL_CAUGHT`; `ANCHORS: ANCHORS_OK` over
  `hook_wiring.json`.

**Dependencies on other tasks**: Task 7 (a `WIRED` reading runs the gate's real `--self-check`).

---

## Task 10: the assembler runs the check

**Production files**: `h-mad/scripts/h_mad_assemble_tdd.py`
**Test files**: `h-mad/tests/test_h_mad_assemble_tdd_agent.py`
**Task shape**: `wiring` — the deliverable is the assembler's call to Task 9's check. The timeout
table and the docstring are new behaviour; the RED split states which tests are which.
**WIRE**: `h-mad/scripts/h_mad_assemble_tdd.py:main` → `h-mad/scripts/h_mad_hook_wiring.py:check_agy` (the `AGY_WIRING_CHECK --agy --project-root` subprocess)
**WIRE-PIN**: `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_runs_the_wiring_check_before_assembling`

**Description**: Design §"FR-5", "The assembler". The choices line becomes
`ap.add_argument("--agent", choices=("codex", "grok", "agy"), default="codex")`; the timeout line
becomes `timeout = args.timeout if args.timeout is not None else TIMEOUT_DEFAULTS[args.agent]`
with `TIMEOUT_DEFAULTS = {"codex": 900, "grok": 1500, "agy": 1500}` (agy's 1500 is provisional
until Task 22). For `--agent agy`, `main` runs
`[sys.executable, AGY_WIRING_CHECK, "--agy", "--project-root", <root>]` with a bound of
`AGY_WIRING_TIMEOUT_S = 60` before `assemble`. `AGY_WIRING_CHECK` is the module constant
`str(Path(__file__).resolve().parent / "h_mad_hook_wiring.py")`, the tests' seam. The check runs
only when `args.agent == "agy"`. `WIRED` → continue. `UNWIRED` → print
`ASSEMBLE-TDD: HALT agy_tdd_hook_unverified`, then the check line indented two spaces, then the
marker line, write no prompt, exit 0. `UNREADABLE` → the same three lines, exit 2. No
`AGY-GATE:` line, or a timeout → `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified check=no-token`,
then the marker line, exit 2. The marker line is
`print(f"[H-MAD] {args.feature} tdd-assemble halt agy_tdd_hook_unverified {args.task}")`. It is
built like the PASS path's `print(f"[H-MAD] {args.feature} tdd-assemble {args.phase} {meta['task']}")`,
with the literal `halt agy_tdd_hook_unverified` in place of the phase, and with `args.task`
because `meta` does not exist yet. It always comes after the token line, so the token stays the first line. The verdict branch
does not raise `Halt`, and the existing `Halt` branches are not changed. The module docstring's `exit 0 on PASS, 2 on any HALT` (line 50 at `4e4b5ded`)
becomes `exit 0 on PASS and on HALT agy_tdd_hook_unverified after AGY-GATE: UNWIRED; 2 on every
other HALT`. The check run must not repeat the line `        agent=args.agent,` (1 occurrence at
`4e4b5ded`), which `wr3-assembler-drops-agent` anchors on.

`run_cli` gains an `env` override parameter so a subprocess run sees the fixture `HOME`. The
**WIRED fixture** is a `HOME` holding the gate symlink (Task 9) plus a `<root>/.agents/hooks.json`
holding FR-5's exact entry.

**Tests** (in `h-mad/tests/test_h_mad_assemble_tdd_agent.py`):
1. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_runs_the_wiring_check_before_assembling`
   — WIRE-PIN. In-process. Scaffold: `monkeypatch.setattr(assemble_mod, "AGY_WIRING_CHECK",
   str(stub), raising=False)`, where `stub` is a script that writes its argv to a record file and
   prints `AGY-GATE: UNWIRED reason=no-entry`; `main` is called through a helper that catches
   `SystemExit` and returns its code. Asserts the record file holds `--agy --project-root` and the
   root, stdout is the HALT line, then `  AGY-GATE: UNWIRED reason=no-entry`, then the marker line
   `f"[H-MAD] {FEATURE} tdd-assemble halt agy_tdd_hook_unverified Task 1"` (the file's `FEATURE`
   constant and the task the helper passes), no prompt file, and return 0. F: at the RED base `check_agy` exists (Task 9) and argparse refuses `agy`, so the
   record file is absent and the assertion that the check ran fails; `raising=False` keeps the
   absent constant from raising `AttributeError`.
2. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_unwired_halts_with_exit_0` — one id per
   reason (7), through `run_cli` with the fixture `HOME` and a `hooks.json` built to give that
   reason; the HALT line, the indented check line, the marker line and exit 0 asserted
   separately, no prompt. 7 nodes, F.
3. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_unreadable_halts_with_exit_2` — a
   `hooks.json` that is not JSON; the HALT line, the indented `  AGY-GATE: UNREADABLE` line and
   the marker line asserted, then exit 2 separately. 1 node, F.
4. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_no_token_halts_with_exit_2` — in-process
   stub that prints nothing; stdout holds `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified check=no-token`
   and the marker line, then exit 2 separately. 1 node, F.
5. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_check_timeout_halts_with_exit_2` —
   in-process, `AGY_WIRING_TIMEOUT_S` patched to `1` with `raising=False`, a stub that sleeps 5 s;
   the same two lines as item 4, then exit 2. 1 node, F.

Items 3–5 assert the HALT line, not only the exit. At RED, argparse refuses `--agent agy` with
exit 2, so an exit-only assertion would pass for the wrong reason.
6. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_wired_writes_the_prompt` — the WIRED
   fixture; PASS, exit 0, the command block names `hmad-dispatch exec agy` and `--timeout 1500`.
   1 node, F.
7. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_default_timeouts` — `codex-900`,
   `grok-1500`, `agy-1500`. 3 nodes: 2 P (`codex-900`, `grok-1500`), 1 F.
8. `tests/test_h_mad_assemble_tdd_agent.py::test_docstring_states_the_agy_halt_exit_rule`. 1 node, F.
9. `tests/test_h_mad_assemble_tdd_agent.py::test_docstring_drops_the_any_halt_rule`. 1 node, F.
10. `tests/test_h_mad_assemble_tdd_agent.py::test_prompt_file_is_agent_independent` (existing,
    extended for AC-9.1): the WIRED fixture is provisioned in its `tmp_path` root once before the
    loop; the loop becomes `("codex", "grok", "agy")`; the assertion becomes
    `len(hashes) == 3 and len(set(hashes)) == 1` (today it asserts `hashes[0] == hashes[1]`).
    1 node, F.

**RED split**: 18 nodes; 16 F, 2 P (1 + 7 + 1 + 1 + 1 + 1 + 3 + 1 + 1 + 1 = 18). The WIRE-PIN
fails on an assertion that the check was not run; items 2–10 fail for the absent `agy` choice,
table and docstring, which is new behaviour.

**Regression guards**: `tests/test_h_mad_assemble_tdd_agent.py::test_agent_grok_explicit_timeout_wins`
(the test of row `t1-timeout-judged-by-value`),
`tests/test_h_mad_assemble_tdd_agent.py::test_agent_grok_block_names_exec_grok_with_1500` (row
`wr3-assembler-drops-agent`),
`tests/test_h_mad_assemble_tdd.py::TestCli::test_a_clean_assembly_prints_pass_and_the_command_block`
(row `w10a-grok-by-default`), and the rest of `tests/test_h_mad_assemble_tdd.py`.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/assemble_tdd_agy.json`, 4 rows:
| name | mutant | test |
|---|---|---|
| `fr5-unwired-exits-2` | the `UNWIRED` verdict branch returns 2 | `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_unwired_halts_with_exit_0` |
| `wire-check-not-run` (wire-cut) | the check subprocess call deleted, the check and `assemble` kept | `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_runs_the_wiring_check_before_assembling` |
| `wire-check-runs-for-every-agent` (converse) | the `args.agent == "agy"` condition on the check run replaced by `True` | `tests/test_h_mad_assemble_tdd_agent.py::test_agent_grok_block_names_exec_grok_with_1500` |
| `halt-marker-dropped` (marker discipline) | the `[H-MAD]` marker print removed from the `UNWIRED` branch | `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_unwired_halts_with_exit_0` |

**Both directions.** `wire-check-not-run` cuts the wire, and `wire-check-runs-for-every-agent`
forces it. The converse's killer is an existing regression guard. It runs
`run_cli(..., "--agent", "grok")` with `root = tmp_path`, which holds no `.agents/hooks.json`. Under
the mutant the real check runs, prints `AGY-GATE: UNWIRED reason=no-hooks-file` (FR-5's first
reason, whatever `HOME` holds), and the assembler halts with no command block, so the test's
`hmad-dispatch exec grok` assertion fails.
`tests/test_h_mad_assemble_tdd_agent.py::test_agent_codex_default_timeout_is_900` fails the same
way for codex. Neither test changes, so the RED counts do not move.

**Anchors (E7)**: `assemble_tdd_agent.json` `w10a-grok-by-default` is re-anchored in this Task:
`find` `ap.add_argument("--agent", choices=("codex", "grok", "agy"), default="codex")`, `replace`
the same with `default="grok"`, `test` unchanged. `t1-timeout-judged-by-value` (`find`
`args.timeout is not None`) and `wr3-assembler-drops-agent` (`find` `        agent=args.agent,`)
need no re-anchor if the line forms above are kept. No other row among the 60 naming the
assembler holds the docstring line (`2 on any HALT`), the `--agent` line or the timeout line, so
these three are the only existing rows this Task's edits touch. `--check-anchors` over the 6 specs naming the
assembler (`assemble_tdd.json`, `assemble_tdd_agent.json`, `assemble_tdd_env_known.json`,
`assemble_tdd_mutation_rows.json`, `fill_slots.json`, `grok_wire_reverts.json`) plus
`assemble_tdd_agy.json`.

**Acceptance Criteria**:
- [ ] AC-5.1 (`--agent agy` halts with no prompt on each reason): item 2 passes.
- [ ] AC-5.2 (the assembler's half of each row, token and exit asserted separately; a mutant
  returning 2 on `UNWIRED` killed): items 2–6 pass and `fr5-unwired-exits-2` is caught.
- [ ] AC-9.1 (`test_prompt_file_is_agent_independent` covers `codex`, `grok`, `agy`): item 10
  passes.
- [ ] The WIRE-PIN fails when only the wire is cut (`wire-check-not-run`), and the codex/grok
  regression guards fail when the wire is forced (`wire-check-runs-for-every-agent`).
- [ ] Marker discipline: every new halt path prints the `[H-MAD]` marker after its token, as
  items 1–5 assert; `halt-marker-dropped` is caught.
- [ ] AC-X: `assemble_tdd_agy.json` → `MUTATION: ALL_CAUGHT`; `ANCHORS: ANCHORS_OK` over the 7
  assembler specs.

**Dependencies on other tasks**: Task 9.

---

## Task 11: the writer's `--append`

**Production files**: `h-mad/scripts/h_mad_state_write.py`
**Test files**: `h-mad/tests/test_h_mad_state_write.py`
**Task shape**: `new-behaviour`

**Description**: Design §"FR-7", "The add". `--append KEY=JSON` is repeatable and decoded with
`json.loads`, no string fallback (a failure prints the writer's `ERROR:` line, exit 2). `--set` fields and
`--append` entries apply inside one `_mutate` call through `merge_fields`, which gains an
`appends` keyword. `apply` keeps its existing statements byte for byte (`record =
{**records[feature], **fields}`, then the owner-heartbeat `if` and its assignment) and runs the
appends after them, each reading `current = record.get(key, [])` from the updated `record`. A key
named by both `--set` and `--append` is refused (`--set and --append name the same key: <key>`).
`APPEND_ONLY = ("review_independence", "implementation_authors")`; a key of `fields` in it raises
`StateWriteError` (`<key> is append-only: use --append`) in a check at the top of `merge_fields`,
before `def apply`. An existing non-list value is refused (`cannot append to a non-array value`).
The `STATE-WRITE: OK` line lists appended keys with set keys.

**Code structure**:
```python
APPEND_ONLY = ("review_independence", "implementation_authors")
def merge_fields(state_file: Path, feature: str, fields: dict[str, Any], *,
                 session_id: str | None = None, now: str | None = None,
                 appends: list[tuple[str, Any]] | None = None) -> dict: ...
```

**Tests** (in `h-mad/tests/test_h_mad_state_write.py`, new class `TestAppend`, using the file's
`run` helper):
1. `tests/test_h_mad_state_write.py::TestAppend::test_append_keeps_both_earlier_entries` — a
   record holding two `review_independence` entries; one append; both earlier entries compared as
   `json.dumps` text.
2. `tests/test_h_mad_state_write.py::TestAppend::test_two_appends_in_one_call_keep_order`.
3. `tests/test_h_mad_state_write.py::TestAppend::test_set_and_append_on_the_same_key_are_refused`
   — the key is `production_paths_needing_red_tests` (a schema `array` of strings, not in
   `APPEND_ONLY`, so the `APPEND_ONLY` check cannot refuse it first and mask a removed same-key
   guard): `--set production_paths_needing_red_tests=[] --append production_paths_needing_red_tests=["a"]`.
   Asserts stderr carries the exact diagnostic
   `--set and --append name the same key: production_paths_needing_red_tests`, stderr does not carry
   `unrecognized arguments`, exit 2, and the store is byte-identical. Read at `4e4b5ded` on a
   scratch store: the current writer exits 2 with
   `error: unrecognized arguments: --append production_paths_needing_red_tests=["a"]` and leaves the
   store unchanged. So a key-and-exit-only assertion passes at RED, and the exact diagnostic is
   what makes this item fail there.
4. `tests/test_h_mad_state_write.py::TestAppend::test_append_only_key_refuses_set` —
   `review_independence`, `implementation_authors`, each alone: `--set <key>=[]` exits 2 with the
   append-only message and the store unchanged. 2 nodes.
5. `tests/test_h_mad_state_write.py::TestAppend::test_append_only_refusal_applies_to_library_callers`
   — `merge_fields` raises `StateWriteError`.
6. `tests/test_h_mad_state_write.py::TestAppend::test_append_value_is_strict_json` — a value that
   is not JSON; stderr starts with the writer's `ERROR: ` line naming the `--append` item and does
   not carry `unrecognized arguments`; exit 2; store unchanged.
7. `tests/test_h_mad_state_write.py::TestAppend::test_append_to_non_array_refused` — stderr
   carries `cannot append to a non-array value`; exit 2; store unchanged.
8. `tests/test_h_mad_state_write.py::TestAppend::test_refused_entry_leaves_store_byte_identical` —
   `review-independence-bad-leg`, `implementation-authors-gemini`. Each id asserts that stderr
   carries the writer's schema refusal (`would not validate`, from `_refusal`) and not
   `unrecognized arguments`, that the exit is 2, and that the store is byte-identical. 2 nodes.

Items 3 and 6–8 each assert the refusal's own text. At RED every `--append` run exits 2 on
argparse's `unrecognized arguments` with the store unchanged, so the exit and the store alone
would pass there.
9. `tests/test_h_mad_state_write.py::TestAppend::test_ok_line_lists_appended_keys`.
10. `tests/test_h_mad_state_write.py::TestAppend::test_owner_append_refreshes_the_heartbeat`.
11. `tests/test_h_mad_state_write.py::TestAppend::test_append_implementation_authors_entry`.

**RED split**: 13 nodes, 13 F, 0 P (1 + 1 + 1 + 2 + 1 + 1 + 1 + 2 + 1 + 1 + 1). Items 3 and 6–8
assert the refusal's message. Item 4 runs against Task 1's schema, which accepts
`--set review_independence=[]` at RED. So none of them passes at RED on argparse's own refusal.

**Regression guards**: the rest of `tests/test_h_mad_state_write.py`, including
`tests/test_h_mad_state_write.py::TestHeartbeatBeats::test_a_set_by_the_owner_refreshes_the_heartbeat`
and `tests/test_h_mad_state_write.py::TestHeartbeatBeats::test_a_set_by_a_bystander_does_not_manufacture_liveness`.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/state_write_append.json`, 5 rows:
| name | mutant | test |
|---|---|---|
| `fr7-append-from-empty` | each appended value built from `[]` | `tests/test_h_mad_state_write.py::TestAppend::test_append_keeps_both_earlier_entries` |
| `fr7-append-reads-prior` | accumulation reads `prior[key]` instead of the updated `record` | `tests/test_h_mad_state_write.py::TestAppend::test_two_appends_in_one_call_keep_order` |
| `fr7-same-key-refusal-dropped` | the same-key `--set`/`--append` refusal removed | `tests/test_h_mad_state_write.py::TestAppend::test_set_and_append_on_the_same_key_are_refused` |
| `fr7-append-only-drops-review-independence` | `review_independence` removed from `APPEND_ONLY` | `tests/test_h_mad_state_write.py::TestAppend::test_append_only_key_refuses_set[review_independence]` |
| `fr7-append-only-drops-implementation-authors` | `implementation_authors` removed from `APPEND_ONLY` | `tests/test_h_mad_state_write.py::TestAppend::test_append_only_key_refuses_set[implementation_authors]` |

**Anchors (E7)**: `heartbeat_beat.json` `the-owners-set-no-longer-beats` and
`a-bystanders-set-beats-too` anchor on `merge_fields`' owner-heartbeat `if` and its assignment,
which stay byte for byte, so no re-anchor. These are the only rows inside `merge_fields`. The
writer's other rows sit in the nested `apply` functions of the beat, release, lane and
drop-undeclared paths, and none of them sits in `main`'s argument parsing. `--check-anchors` over the 4 specs naming the writer
(`heartbeat_beat.json`, `lane_liveness.json`, `release_ownership_guard.json`,
`state_undeclared_keys.json`) plus `state_write_append.json`.

**Acceptance Criteria**:
- [ ] AC-7.1 (an add keeps both earlier entries; a refused entry leaves the store unchanged):
  items 1, 2 and 8 pass.
- [ ] AC-1.3 (a refused `--append implementation_authors=` entry leaves the store byte-identical):
  item 8 `implementation-authors-gemini` passes.
- [ ] Design `APPEND_ONLY` fixtures: item 4, once per key, passes.
- [ ] AC-X: `state_write_append.json` → `MUTATION: ALL_CAUGHT`; `ANCHORS: ANCHORS_OK` over the 5
  writer specs.

**Dependencies on other tasks**: Task 1.

---

## Task 12: the Phase-7 review-independence warnings

**Production files**: `h-mad/scripts/h_mad_phase7_preconditions.py`
**Test files**: `h-mad/tests/test_h_mad_phase7_preconditions.py`
**Task shape**: `new-behaviour`

**Description**: Design §"FR-7", "The warnings". `check` (today `def check(record, analysis_path,
spec_dirs=None, …)`, returning `{"ready": not blockers, "blockers": …, "warnings": …}`) calls a
new `_review_independence_warnings(record)` and extends `warnings`; it never touches `blockers`.
Well-formed is `property_valid("review_independence", [entry])` and `entry["independent"] ==
(entry["reviewer"] != entry["implementer"])`. `review_independence_malformed` per malformed entry
and once for a non-list field; `review_non_independent` per well-formed `independent=false` entry,
naming leg, module and agent; `review_independence_unrecorded` when `record.get("archreview")` is in
`{"READY_TO_MERGE", "WITH_FIXES", "NO"}` and no well-formed entry has `leg == "6a-prime"`, with no
implementer condition, reading neither `implementer`, `implementer_switch` nor
`implementation_authors`; its detail names the sorted distinct `implementer` values of the
well-formed 5e entries, or `authors=unrecorded`. `main`'s existing `  WARNING <code>: <detail>`
loop prints them.

**Tests** (in `h-mad/tests/test_h_mad_phase7_preconditions.py`, new class
`TestReviewIndependence`):
1. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_non_independent_entry_warns`. F.
2. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_malformed_entry_warns` —
   `bad-leg`, `lying-boolean`, `field-not-a-list`. 3 nodes, F.
3. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_fires_for_each_implementer`
   — `codex-field-absent`, `codex`, `agy` (through `implementer`), `grok`, `claude` (through
   `implementer_switch.to`). 5 nodes, F.
4. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_fires_for_each_archreview_value`
   — `READY_TO_MERGE`, `WITH_FIXES`, `NO`. 3 nodes, F.
5. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_is_quiet` —
   `has-6a-prime-entry`, `archreview-absent`, `SKIPPED_NO_PANE`, `SKIPPED_OPERATOR_OVERRIDE`.
   4 nodes, P (the warning does not exist at RED; these pin its silence at GREEN).
6. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_malformed_6a_prime_entry_is_not_recorded`
   — both warnings. F.
7. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_detail_names_entry_authors_not_routing`
   — `implementer_switch.to == "agy"`, one well-formed 5e entry with `implementer` `codex`; the
   detail names `codex` and not `agy`. F.
8. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_detail_without_5e_entries_says_unrecorded`. F.
9. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_warnings_never_move_ready`. P.
10. `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_warning_lines_print_through_main`. F.

**RED split**: 21 nodes; 16 F, 5 P (1 + 3 + 5 + 3 + 4 + 1 + 1 + 1 + 1 + 1 = 21; P = 4 in item 5
and item 9).

**Mutation rows** — new spec `h-mad/tests/mutation-specs/phase7_review_independence.json`, 4 rows:
| name | mutant | test |
|---|---|---|
| `fr7-consistency-check-dropped` | the `independent` consistency check removed | `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_malformed_entry_warns` |
| `fr7-unrecorded-agy-only` | the trigger restricted to `implementer == "agy"` | `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_fires_for_each_implementer` |
| `fr7-malformed-6a-prime-counted` | a malformed 6a-prime entry counted as recorded | `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_malformed_6a_prime_entry_is_not_recorded` |
| `fr7-detail-reads-switch` | the detail text reads `implementer_switch.to` | `tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_detail_names_entry_authors_not_routing` |

**Anchors**: `--check-anchors` over `phase7_analysis_anchor.json`,
`phase7_preconditions_gates.json` and `phase7_review_independence.json`. Existing rows touched:
none. The call is added immediately before `check`'s line starting `return {"ready": not blockers`,
on which no row sits. The 4 rows inside `check` and the 3 inside `main` are not on the edited
lines.

**Acceptance Criteria**:
- [ ] AC-7.1 (each warning from its own fixture; none moves `ready`): items 1, 2, 3 and 9 pass.
- [ ] AC-7.2: items 3, 4 and 5 pass.
- [ ] Design switch/recovery fixture: item 7 passes.
- [ ] AC-X: `phase7_review_independence.json` → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 1 (`property_valid`).

---

## Task 13: the six carve-out copies

**Production files**: `h-mad/references/codex-implementer-prompt.md`, `h-mad/SKILL.md`, `h-mad/references/failure-recovery.md`, `h-mad/scripts/h_mad_assemble_tdd.py`
**Test files**: `h-mad/tests/test_h_mad_new_caller_carveout_copies.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §"FR-9". The canonical block (spec FR-9's quoted block, three sentences)
is appended after six context sentences, each occurring once in its file at `4e4b5ded` (Python
`str.count`): prompt RED item 1 after `Say which case each failing test is.`; the prompt's WIRE-PIN
paragraph after `report that and stop rather than accepting it.`; the SKILL.md 5d bullet after
``halt `step5d:red_wrong_reason:<module>`.``; the `failure-recovery.md` 5d row inside the remedy
cell's quotes after `only the failure mode can.`; `h_mad_assemble_tdd.py` `assemble()` inside the
wiring branch's `lines.append(...)` holding `The WIRE-PIN is this task's single load-bearing test.`
(the literal `"symbol."` becomes `"symbol. "` and the block follows as adjacent literals;
`never a missing` stays); the prompt's GREEN paragraph after `keeping tests green.`.

The test holds `CANONICAL` once and compares `collapse(span).count(collapse(CANONICAL)) == 1` with
`collapse(s) = " ".join(s.split())`, through the design's six locators L1–L6. Each locator raises
when its anchor matches zero spans or more than one. All six locators select exactly one span on
the `4e4b5ded` tree, and each span contains its context sentence (checked for this plan with
scratch code since deleted).

**Tests** (all in `h-mad/tests/test_h_mad_new_caller_carveout_copies.py`):
1. `tests/test_h_mad_new_caller_carveout_copies.py::test_copy_carries_the_canonical_block` — `L1`
   … `L6`. 6 nodes, F.
2. `tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans` — each
   locator × `zero` and `two`, over doctored copies of its source text. 12 nodes, P (they exercise
   the test's own locators, which exist at RED).

**RED split**: 18 nodes; 6 F, 12 P.

**Regression guards (doc-pin census)**:
`tests/test_h_mad_agent_definitions.py::test_implementer_scopes_the_import_error_red_rule_to_wiring_tasks`
(RED item 1's sentences), `tests/test_h_mad_wiring_task_shape_docs.py` (`HALT_TOKENS`, the
wiring-bullet anchor and `failure mode per test, not only the count`),
`tests/test_h_mad_assemble_tdd.py::TestWiringShape::test_the_pin_is_told_what_its_red_must_be`
(`never a missing`), and every other census pin on the prompt. Expected pins moved: none.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/new_caller_carveout_copies.json`, 8 rows
here, each with `symbol` (the enclosing heading for a `.md` file, `assemble` for the `.py` file)
and `test` `tests/test_h_mad_new_caller_carveout_copies.py::test_copy_carries_the_canonical_block`,
each run alone:
- 6 per-copy rows (`fr9-copy-L1` … `fr9-copy-L6`): `valid **only** when` → `valid when` in that
  copy, with a `find` that starts at the copy's context sentence; the `L5` row's `find` is written
  against the committed source bytes, including the adjacent-literal split.
- 2 per-sentence rows on the `failure-recovery.md` copy: `fr9-L4-sentence-2` deletes
  `The RED report must name both. `; `fr9-L4-sentence-3` changes `delete the call only, keep the
  caller and the callee` to `delete the callee only, keep the caller`.

**Anchors**: `--check-anchors` over every spec naming `SKILL.md` (16 specs, 57 rows at
`4e4b5ded`), `references/failure-recovery.md` (`archreview_done_marker_recovery.json`) and the 7
assembler specs. Existing rows touched: none. No row's `find` holds any of the six context
sentences, the `"symbol."` literal or `never a missing`. No row names
`references/codex-implementer-prompt.md`. The 2 `failure-recovery.md` rows sit outside the 5d row.

**Acceptance Criteria**:
- [ ] AC-9.1 (the rule on all six surfaces; the three pin files green): item 1 and the
  regression guards pass.
- [ ] AC-9.4: item 1 passes and the 8 rows → `MUTATION: ALL_CAUGHT`, each run alone.

**Dependencies on other tasks**: Task 10 (both edit `h_mad_assemble_tdd.py`).

---

## Task 14: the FR-9 differential corpus

**Production files**: none
**Test files**: `h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py` (new)
**Task shape**: `gate` — a verdict over the rule text Task 13 placed; it writes no production file.

**Description**: Design §"FR-9", "The differential corpus". Five cases (`new-caller`,
`missing-callee`, `both-missing`, `unrelated-import`, `other-symbol`), each a fixture repository in
`tmp_path` with a real pytest RED run by `sys.executable`. Callee resolution is executed (a
subprocess runs `import` and `getattr` at the RED base), never parsed. `old_rule` and `new_rule`
transcribe the two texts. The spec's AC-9.2 names four cases; the fifth is the plan's, and the pass
condition is over all five. The module exposes `run_corpus(base: Path) -> list[dict]`, which the
committed probe `docs/03-analysis/probes/agy-coder-fallback/fr9_corpus_reading.py` imports from
`h-mad/tests` to print the cases' exception lines and verdicts, stamped with the sha; the probe
carries one reading.

**Tests**:
1. `tests/test_h_mad_wire_pin_new_caller_corpus.py::test_corpus_case_red_is_real` — one id per case;
   the exception line names the declared missing symbol, and callee resolution is recorded.
   5 nodes.
2. `tests/test_h_mad_wire_pin_new_caller_corpus.py::test_changed_verdicts_are_exactly_new_caller`. 1 node.
3. `tests/test_h_mad_wire_pin_new_caller_corpus.py::test_transcription_is_tied_to_the_canonical_words`
   — `CANONICAL`, imported from the equivalence test, contains `the missing symbol is the caller
   the task creates` and `the callee resolves at the RED base`. 1 node.

**RED split**: 7 nodes, 0 F, 7 P (5 + 1 + 1). A failure is a finding against Task 13's text or the
transcription, not something to fix here.

**Mutation rows** — `new_caller_carveout_copies.json`, 2 rows here (`file`
`tests/test_h_mad_wire_pin_new_caller_corpus.py`, `test`
`tests/test_h_mad_wire_pin_new_caller_corpus.py::test_changed_verdicts_are_exactly_new_caller`,
each run alone): `fr9-corpus-drops-callee-condition` (then `both-missing` changes) and
`fr9-corpus-drops-caller-condition` (then `other-symbol` and `unrelated-import` change). The spec
then holds 8 + 2 = 10 rows.

**Acceptance Criteria**:
- [ ] AC-9.2: items 1–2 pass; the changed set is exactly `{new-caller}`.
- [ ] The probe prints its reading and is committed with one reading at one sha.
- [ ] AC-X: `new_caller_carveout_copies.json` (10 rows) → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 13.

---

## Task 15: the implementer-neutral prompt

**Production files**: `h-mad/references/codex-implementer-prompt.md`
**Test files**: `h-mad/tests/test_h_mad_implementer_neutral_prompt.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §"FR-10", "The prompt". The opening sentence (`You are Codex implementing
module …` at `4e4b5ded`, pinned by no test: `git ls-files 'h-mad/tests/*.py' | xargs grep -ln
'You are Codex implementing'` prints nothing) names "the Phase-5 implementer" and no implementer
by name (spec FR-9, first bullet). Line 9 at `4e4b5ded` reads ``You are Codex implementing module
`<INLINE_MODULE_NAME>` for feature `<INLINE_FEATURE>`.``. Its two template slots stay.

The one `Hook: ` line (line 19 at `4e4b5ded`) names each gate by implementer, as spec FR-9's
second bullet requires:
- Codex: `h-mad-codex-tdd-gate.py`, guarding `apply_patch` and shell writes;
- agy: `h-mad-agy-tdd-gate.py`. For agy the line states that the class-(b) tools are how writes are
  made, naming all five: `write_to_file`, `replace_file_content`, `multi_replace_file_content`,
  `sed_file`, `notebook_edit` (design §"FR-4" class (b));
- grok: no write-time gate, in those words;
- Claude: `h-mad-tdd-gate.sh`, guarding `Write` and `Edit` (kept from today's line).
The line keeps every token `test_hook_line_names_both_gates` pins (`h-mad-codex-tdd-gate.py`,
`apply_patch`, `shell`, `h-mad-tdd-gate.sh`, `Write`, `Edit`). It introduces no `<`, `>` or `->` on
the line or its bullets, so the spec's `→` is written as a colon or as words. The filename stays
(plan "Tradeoffs kept").

**Tests**:
1. `tests/test_h_mad_implementer_neutral_prompt.py::test_prompt_opening_names_no_implementer` — the
   first line starting `You are` contains `the Phase-5 implementer` and none of `Codex`, `agy`,
   `grok`, `Claude` (case-insensitive). F.
2. `tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_names_the_agy_gate` — the `Hook: `
   line names `h-mad-agy-tdd-gate.py`. F.
3. `tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_names_the_agy_write_tools` — the
   `Hook: ` line contains `agy` and each of the five class-(b) names. F.
4. `tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_says_grok_has_no_write_time_gate`
   — the `Hook: ` line contains `grok` and `no write-time gate`. F.

Each test reads the `Hook: ` line through `test_h_mad_tdd_gate_docs._hook_block`'s rule (the one
line starting `Hook: `), so a clause moved onto a bullet fails items 2–4.

**RED split**: 4 nodes, 4 F.

**Regression guards (doc-pin census, the prompt)**: `tests/test_h_mad_tdd_gate_docs.py`
(`_hook_block`: exactly one `Hook: ` line; `test_hook_line_names_both_gates`;
`test_hook_bullets_state_the_shipped_rule`; both forbid `<` and `>`),
`tests/test_h_mad_extract_verdict.py::test_both_codex_prompts_spell_the_label`,
`tests/test_h_mad_portable_timeout.py`, and the 23 literals across the 8 files the census lists.
Expected pins moved: none.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/implementer_neutral_prompt.json`, 4 rows
(doc pins, plan §"Success Criteria"), each with `symbol` the prompt's enclosing heading:
- `fr10-prompt-opening-names-codex` (the opening restored to `You are Codex implementing`) →
  `tests/test_h_mad_implementer_neutral_prompt.py::test_prompt_opening_names_no_implementer`;
- `fr10-hook-line-drops-agy-gate` (the `h-mad-agy-tdd-gate.py` name deleted) →
  `tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_names_the_agy_gate`;
- `fr10-hook-line-drops-agy-write-tools` (the class-(b) clause deleted) →
  `tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_names_the_agy_write_tools`;
- `fr10-hook-line-drops-grok` (the grok clause deleted) →
  `tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_says_grok_has_no_write_time_gate`.

**Acceptance Criteria**:
- [ ] AC-9.1 and spec FR-9 first bullet (the opening names "the Phase-5 implementer" and no
  implementer): item 1 passes.
- [ ] Spec FR-9 second bullet and FR-10 (the `Hook:` line: Codex, agy with its class-(b) tools,
  grok with no write-time gate): items 2–4 and the regression guards pass.
- [ ] The 4 rows → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 13 (both edit the prompt).

---

## Task 16: SKILL.md authorship surfaces and `agy-runtime.md`

**Production files**: `h-mad/SKILL.md`, `h-mad/references/agy-runtime.md`
**Test files**: `h-mad/tests/test_h_mad_agy_authorship_docs.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §"FR-10". SKILL.md §"Codex authors Phase 5 — enforced, not just
instructed" becomes implementer-neutral, states FR-2 and FR-3, and names `agy-authorship`,
`implementer-invalid` and `h_mad_tdd_judge.py implementer`; the heading and the sentence
`Phase 5 implementation is **Codex's job**` stay (or `_phase_5e_text` and `PHASE5_HEADING` move in
the same commit). It also states the re-run trigger: after any agy upgrade, re-run FR-8 step 2 and
step 2a and re-take the class-(a) inventory. §"Exit-code dispatch for 5d/5e (`hmad-dispatch exec`)
— default for one-shot" gains a line holding both `exec agy` and "implement", plus the
`TDD-IMPLEMENTER:` staging step below. The teammate-audit bullet starting
`- **It does not license Claude to write Phase 5 production code` separates audit-leg selection
from resolved authorship, keeping its anchor prefix and the tokens `ACTIVE`, `every`,
`unavailable` and `exhausted`. `agy-runtime.md` §"The TDD gate" names `h-mad-agy-tdd-gate.py` and
`AGY-GATE:` and keeps the halt. Its two `SessionStart` surfaces (2 matching lines at `4e4b5ded`,
one under §"Hooks" and one in the §"Construct mapping" `hook-event` row) are re-checked against
the installed agy (`agy --version` prints `1.4.0` at `4e4b5ded`; its bundled `hooks.md` has 3
lines naming `SessionStart`) and corrected together, stamping that version.

**The staging step** (spec FR-2 "CLI verb", design §"FR-2" "The `implementer` verb"). It is one
bullet that starts `- **Stage the implementer.**`, which occurs once in SKILL.md after this Task
and nowhere at `4e4b5ded`. It states:
- the command, run before every 5d and 5e dispatch, from the project root:
  `python3 ~/.claude/skills/h-mad/scripts/h_mad_tdd_judge.py implementer --root . --feature "$FEATURE" --record`.
  Read the `TDD-IMPLEMENTER:` token, never `$?`, because the verb always exits 0;
- a line that ends ` record=failed`, whatever comes before it: **do not dispatch.** Halt
  `step5:implementer_switch_unrecorded` and print the marker
  `[H-MAD] <feature> halt step5:implementer_switch_unrecorded`, because a switch that is not in
  state is the silent switch the operator decision forbids (spec FR-2). This branch is checked
  first, before the token's other fields are read;
- `switch=none`: stage `h_mad_assemble_tdd.py --agent` with the resolved peer (`codex` or `agy`);
- a peer switch (`switch=codex->agy` or `switch=agy->codex`, with `reason=`): stage the resolved
  peer, and print the token line on the dispatch;
- `switch=peers-out`: today's fallback path (grok or Claude), unchanged;
- `invalid field=`: fix the record and never dispatch. Halt `step5:implementer_invalid` and print
  its `[H-MAD]` marker;
- `no-record` or `unreadable`: halt `step5:implementer_unresolved` and print its `[H-MAD]`
  marker. The feature name or root is wrong, or the state file cannot be read.
The names `step5:implementer_invalid` and `step5:implementer_unresolved` originated in this plan;
spec v1.10 (`c283bb63`) FR-2 and design v1.4 (`2cd5d7f1`) §"FR-2" adopt them.

**Tests** (all in `h-mad/tests/test_h_mad_agy_authorship_docs.py`; section locators are
`docsections.titled_section`, and the bullet locator is `test_h_mad_tdd_gate_docs.py`
`_skill_gate_bullet`'s split):
1. `tests/test_h_mad_agy_authorship_docs.py::test_phase5_authorship_section_names_the_resolver_and_agy_authorship`. F.
2. `tests/test_h_mad_agy_authorship_docs.py::test_phase5_authorship_section_states_the_agy_upgrade_trigger`. F.
3. `tests/test_h_mad_agy_authorship_docs.py::test_exit_code_dispatch_section_lists_exec_agy_as_an_implementer`
   — a line holding `exec agy` and, case-insensitively, `implement`; and `TDD-IMPLEMENTER:`. F.
4. `tests/test_h_mad_agy_authorship_docs.py::test_teammate_bullet_separates_audit_selection_from_authorship`
   — names `h_mad_tdd_judge.py implementer` and `agy-authorship`. F.
5. `tests/test_h_mad_agy_authorship_docs.py::test_agy_runtime_tdd_gate_names_the_agy_gate_and_keeps_the_halt`
   — `h-mad-agy-tdd-gate`, `AGY-GATE` and `step5:agy_tdd_hook_unverified`. F.
6. `tests/test_h_mad_agy_authorship_docs.py::test_agy_runtime_sessionstart_claim_is_rechecked_and_stamped`
   — neither surface still says there is no `SessionStart`, and both stamp `1.4.0`. F.
7. `tests/test_h_mad_agy_authorship_docs.py::test_staging_step_runs_the_verb_with_record_and_names_every_branch`
   — the bullet starting `- **Stage the implementer.**` (exactly one) contains
   `h_mad_tdd_judge.py implementer`, `--record`, one sentence holding both `never` and `$?`, and
   each branch token: `record=failed`, `switch=none`, `switch=peers-out`, `invalid field=`,
   `no-record`, `unreadable`. F.
8. `tests/test_h_mad_agy_authorship_docs.py::test_staging_step_halts_on_record_failed_before_any_dispatch`
   — runs the module's `record_failed_branch_refuses_dispatch(bullet)` on the staging bullet and
   asserts `True`. That function takes the branch span: the text from the bullet's first
   `record=failed` to the first `switch=none` after it, with whitespace collapsed. A bullet where
   `switch=none` does not follow `record=failed` returns `False`, so the `record=failed` branch must
   be listed first. The span must hold `do not dispatch` (case-insensitive),
   `step5:implementer_switch_unrecorded`, `[H-MAD]` and `first`. F.
9. `tests/test_h_mad_agy_authorship_docs.py::test_record_failed_check_rejects_a_procedure_that_dispatches`
   — the discriminating control. `record_failed_branch_refuses_dispatch` returns `False` on four
   doctored bullets: one whose `record=failed` branch says to stage the resolved peer and
   dispatch; one with the halt sentence deleted; one that keeps the halt but drops `[H-MAD]`; and
   one that lists the `record=failed` branch after `switch=none`. P (it exercises the test's own
   function, which exists at RED).

**RED split**: 9 nodes, 8 F, 1 P (item 9).

**Regression guards (doc-pin census)**: `tests/test_grok_fallback_docs.py` (`PHASE5_HEADING`,
`TEAMMATE_HEADING`, the exit-code heading and tokens),
`tests/test_h_mad_mutation_harness.py::test_skill_documents_the_precheck_is_automatic`
(`_phase_5e_text`'s two `str.index` anchors), `tests/test_h_mad_tdd_gate_docs.py` (the anchor
sentence and tokens, `_skill_gate_bullet`, §"The TDD gate" tokens, `rc 0`, no `exit-code protocol`),
`tests/test_h_mad_context_budget_docs.py` (`hmad-dispatch exec agy`), `tests/test_h_mad_assemble_tdd.py`
(`hmad-dispatch exec codex`). Expected pins moved: none.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/agy_authorship_docs.json`, 8 rows (doc
pins), one per F item, each deleting the pinned sentence: `fr10-authorship-section`,
`fr10-upgrade-trigger`, `fr10-exit-code-exec-agy`, `fr10-teammate-bullet`,
`fr10-agy-runtime-tdd-gate`, `fr10-sessionstart-stamp`, `fr10-staging-drops-record-flag` (the
`--record` flag deleted from the staging command) and `fr10-staging-dispatches-after-record-failed`
(the `record=failed` halt sentence replaced by "stage the resolved peer"). Each `test` is its
item's node ID, items 1–8 in that order.

**Anchors**: `--check-anchors` over the 16 specs naming `SKILL.md`; `agy-runtime.md` has no rows.
Existing rows touched: none. No SKILL.md row's `find` lies in §"Codex authors Phase 5", in
§"Exit-code dispatch for 5d/5e" or in the teammate-audit bullet (sweep at `4e4b5ded`, by offset
span).

**Acceptance Criteria**:
- [ ] Plan §"Success Criteria" FR-10 baselines (0 at `d90decc6`/`9c3b799d`) are non-zero: items
  1, 3, 4 and 5 pass.
- [ ] Spec §"Owed" `SessionStart`: item 6 passes.
- [ ] Spec FR-2 "CLI verb" (the caller halts `step5:implementer_switch_unrecorded` on
  `record=failed` and never dispatches): items 7–9 pass, and
  `fr10-staging-dispatches-after-record-failed` is caught.
- [ ] The 8 rows → `MUTATION: ALL_CAUGHT`; `ANCHORS: ANCHORS_OK` over the SKILL.md specs.

**Dependencies on other tasks**: Task 13 (both edit SKILL.md).

---

## Task 17: the review-independence procedure and AC-7.3's surface

**Production files**: `h-mad/SKILL.md`
**Test files**: `h-mad/tests/test_h_mad_review_attribution_docs.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §"FR-7" (the orchestrator's step, attribution, the author append) and
§"FR-10". SKILL.md Phase-7 closure item 7 (located by the `str.index` slice from
`7. **Closure (autonomous)**` to the next `\n## Phase 5`) carries every `WARNING` line
`h_mad_phase7_preconditions.py` prints and adds the `--append review_independence=` step after
each 5e-review, 5e-verify and 6a-prime leg, for every implementer. The attribution text states that
an entry's `implementer` comes from the dispatch, never from `implementer_switch.to` or
`implementer`, and that a module's author set is read from `implementation_authors` only, with the
three closed no-entry cases. The 5e bullet (`- **5e** — GREEN dispatch`, to the next `- **5f** —`)
appends an `--append implementation_authors=` entry holding the module and the accepted
dispatch's agent (design FR-7's JSON form) at GREEN acceptance and at each
accepted 5e fix dispatch, before the leg that reviews the code. The 6a-prime bullet (`- **6a-prime**
— architectural review via agy`) does the same for a fix after `WITH_FIXES`. The 5d bullet
(`- **5d** — RED dispatch`) gains none. Each of these four prefixes occurs once in SKILL.md at
`4e4b5ded`.

**OD-1, decided (operator, 2026-10-16): option (A).** AC-7.3 is met by the transcription test
below, not by a script surface. The text that follows records the reasoning.
Attribution is orchestrator prose (design FR-7),
and spec FR-1 says `implementation_authors` "is read by the orchestrator's FR-7 attribution step
only; no script reads it". A production function that computes an entry's `implementer` and
`independent` from `implementation_authors` would therefore contradict spec FR-1 and design
FR-7 ("The writer does not check attribution").
- **(A), decided and built here:** a transcription test, on
  the FR-9 corpus precedent. A test-local `attribute(record, leg, module, reviewer)` transcribes
  the SKILL.md step; each AC-7.3 fixture runs it on a durable record, and also runs that fixture's
  named mutant transcription, asserting the mutant gives the wrong outcome (so the fixture is RED
  against it). One test ties the transcription to the SKILL.md words. Residual: this shows what the
  rule's text selects, not that any orchestrator applies it.
- **(B), not chosen:** a script surface, for example a writer operation that derives `implementer`
  and `independent` from `implementation_authors` before appending. It would need spec FR-1 and
  design FR-7 revised first.

**Tests** (all in `h-mad/tests/test_h_mad_review_attribution_docs.py`):
1. `tests/test_h_mad_review_attribution_docs.py::test_closure_step_carries_every_warning_line` —
   `review_non_independent`, `review_independence_unrecorded`, `review_independence_malformed`. F.
2. `tests/test_h_mad_review_attribution_docs.py::test_closure_step_appends_review_independence_for_every_implementer`. F.
3. `tests/test_h_mad_review_attribution_docs.py::test_attribution_step_names_the_dispatch_as_the_source`. F.
4. `tests/test_h_mad_review_attribution_docs.py::test_5e_bullet_appends_the_author_at_green_acceptance`. F.
5. `tests/test_h_mad_review_attribution_docs.py::test_6a_prime_fix_appends_the_author`. F.
6. `tests/test_h_mad_review_attribution_docs.py::test_5d_bullet_appends_no_author`. P (a negative
   pin; it bites at GREEN).
7. `tests/test_h_mad_review_attribution_docs.py::test_attribution_transcription` — AC-7.3's five
   fixtures: `routing-is-not-authorship` (the entry it yields is fed to `h_mad_phase7_preconditions.check`,
   and `review_non_independent` fires), `multi-author-recovered`, `pre-field-feature`,
   `red-is-not-authorship`, `unaccepted-dispatches-author-nothing`. 5 nodes, P (the transcription
   lives in the test).
8. `tests/test_h_mad_review_attribution_docs.py::test_transcription_is_tied_to_the_skill_text` —
   the SKILL.md step contains `implementation_authors`, `implementer_switch.to` in a "never"
   clause, and the no-entry rule. F.

**RED split**: 12 nodes; 6 F (items 1–5, 8), 6 P (item 6, and item 7's 5).

**Regression guards (doc-pin census)**: `tests/test_h_mad_archreview_pane_halt.py` (the item-7
slice and its `SKIPPED_NO_PANE` sentence), `tests/test_h_mad_phase7_integrate_docs.py`
(`must name a LOCAL branch`, `git branch main origin/main`),
`tests/test_h_mad_wiring_task_shape_docs.py` (the 5d wiring bullet). Expected pins moved: none.
`phase7_integrate_blockers_documented.json`'s three rows sit inside item 7, which this Task only
adds to. They are the only rows in the four spans this Task edits (sweep at `4e4b5ded`, by offset
span). `baseline_sha.json` `skill-stops-naming-the-wrong-command` has a `find` that starts exactly
at `- **5f** —`. The 5e bullet's addition therefore goes before the newline that ends the 5e
bullet, and that `find` stays unique.

**Mutation rows** — new spec `h-mad/tests/mutation-specs/review_attribution_docs.json`, 6 rows (doc
pins), one per F item, each deleting the pinned sentence: `fr7-docs-warning-lines`,
`fr7-docs-review-append`, `fr7-docs-dispatch-source`, `fr7-docs-5e-author-append`,
`fr7-docs-6a-prime-author-append`, `fr7-docs-transcription-words`; each `test` is its item's node
ID.

**Acceptance Criteria**:
- [ ] Plan §"Success Criteria" (Phase-7 closure `WARNING`, baseline 0): item 1 passes.
- [ ] Design AC-7.1 row (the dispatch as the source): item 3 passes.
- [ ] Design §"Owed" (the author append at 5e GREEN acceptance and at each accepted fix): items
  4–6 pass.
- [ ] AC-7.3, under OD-1 (A): items 7 and 8 pass.
- [ ] The 6 rows → `MUTATION: ALL_CAUGHT`.

**Dependencies on other tasks**: Task 12 (item 7's first fixture runs `check`), Task 16 (both edit
SKILL.md).

---

## Task 18: pre-merge re-measurement

**Production files**: none
**Test files**: none
**Task shape**: `gate`

**Description**: On the shipped tree, before the merge:
- `docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py` — AC-9.1's sweep: the line grep
  over every tracked file under `h-mad/` and the joined reading (`ast` `str` constants with
  whitespace collapsed, plus `tokenize` `COMMENT` tokens of each `.py`), with the plan's regex
  `missing.symbol|tests the callee|ImportError.*AttributeError|AttributeError.*ImportError`
  (case-insensitive), reporting the union and `unparsed=N`. Every hit file is read by hand and
  listed with whether it states the rule with the carve-out.
- Re-run Task 0's probes. M-2 and M-3 move by construction (Tasks 1–17 add rows); the readings
  are recorded, not compared with Task 0's. M-4 must read 0 Codex-gate rows inside a moved span.
- `git grep -n 'review_independence_unrecorded'` over the files this feature edited; each hit is
  read by hand to confirm none states the trigger as agy-only (plan §"Success Criteria").

**Acceptance Criteria**:
- [ ] AC-9.1: the sweep hits no file that states the rule without the carve-out; `unparsed=0`, or
  each unparsed file read by hand.
- [ ] The census readings are committed with the sha.

**Dependencies on other tasks**: Tasks 1–17.

---

## Task 19: the incident replay

**Production files**: none
**Test files**: none
**Task shape**: `gate`

**Description**: Design §"FR-9", "The incident replay"; plan stage 6. A committed probe,
`docs/03-analysis/probes/agy-coder-fallback/fr9_incident_replay.py`, replays HemaSuite
`notebooklm-integration-interface` T4 WIRE-PIN 1 (`test_notebooklm_resolver.py` at `531a6296b`),
T5 WIRE-PIN 1 (`test_notebooklm_initialize.py` at `7aa0d9dec`) and T6 WIRE-PIN 2
(`test_notebooklm_status_report.py` at `c2d671f6b`) through `git archive` exports, so the live
clone is never checked out. At `4e4b5ded` HemaSuite `HEAD` is `02d52e4e7`, and each of the three
commits is an ancestor of it (`git merge-base --is-ancestor`). For each case the probe records the
direct-call form's RED at the task commit's parent with the callee resolving by import, the old
verdict (halt) and the new verdict (valid) using Task 14's `old_rule`/`new_rule`; for T5 and T6 the
committed scaffolded pin's `AssertionError` RED and the old verdict on it (valid); a wire-cut
re-run at the task commit in which the committed pin fails; and the citation (M4.1, M5.1, the
WIRE 2 revert). It stamps both repositories' shas. A case that cannot be reproduced is recorded
with its failing command and counted.

**Acceptance Criteria**:
- [ ] AC-9.3: all three cases reproduced, each with the five records above; a non-reproduced
  case is counted and fails the AC.

**Dependencies on other tasks**: Task 14.

---

## Task 20: post-merge payload capture

**Production files**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test files**: `h-mad/tests/test_h_mad_agy_tdd_gate.py`
**Task shape**: `new-behaviour`

**v1.3 amendment (D-FR8-1, operator decision 2026-10-17) — supersedes the six-tool scope below.**
The capture gate stopped at 3 of 6: on agy `1.4.0`, `multi_replace_file_content`, `sed_file` and
`notebook_edit` are listed in `init.tools` but were never declared to the model across the initial
instruction and three re-instructions on three model families
(`docs/03-analysis/agy-coder-fallback.authoring/fr8_capture_attempts/README.md`, `b7d34327`).
The required set becomes the three captured tools: `write_to_file`, `replace_file_content`,
`run_command`. The three uncaptured class-(b) tools keep no `PATH_KEYS` entry, so under active
step5 they still deny `kind=judge-error` (fail-closed); a later agy that declares them reopens
the capture. Tests, as amended:
- item 1: one id per captured tool (3 nodes);
- item 2: one id per captured class-(b) tool, `write_to_file` and `replace_file_content` (2 nodes);
- item 3: unchanged (2 nodes); item 4: unchanged (1 node).
Total 8 nodes. Captured keys: `write_to_file` → `TargetFile`, `replace_file_content` →
`TargetFile`, `run_command` → `CommandLine` / `Cwd`. **RED split: 1 F, 7 P** — the
`replace_file_content` item-2 id is F (its key is not in `PATH_KEYS` at the RED base); the rest P.
GREEN adds `"replace_file_content": ("TargetFile",)` to `PATH_KEYS`. AC-8.1 reads "all three
samples" for "all six samples".

**Description**: Design §"FR-8" step 1, on main after the merge. In a throwaway fixture project
created beside this checkout (never under `/tmp`), with its own `docs/.bkit-memory.json` step5
record and FR-5's exact `.agents/hooks.json` entry, a temporary capture hook records one real
`toolCall` envelope **for each of the six required tools**: the five class-(b) tools
(`write_to_file`, `replace_file_content`, `multi_replace_file_content`, `sed_file`,
`notebook_edit`) and `run_command` (spec FR-8 step 1: "one real `toolCall` per class-(b) tool and
per `run_command`"). It also records `init.tools` and `agy --version`. Each sample is the hook's
whole stdin as received, unedited, committed under `h-mad/tests/fixtures/agy-payloads/` as six
files named by the tool: `write_to_file.json`, `replace_file_content.json`,
`multi_replace_file_content.json`, `sed_file.json`, `notebook_edit.json`, `run_command.json`.
Beside them, `h-mad/tests/fixtures/agy-payloads/capture.json` holds the metadata the suite reads
(audit cycle 2, I5): one object per tool, keyed by tool name, with `workspacePaths_present`
(`true` or `false`), `path_keys` (the class-(b) key or keys naming the target, for the five
class-(b) tools), and, for `run_command`, `command_key` and `workdir_key` (the envelope keys
naming the command and its working directory). The human-readable capture record
`docs/03-analysis/probes/agy-coder-fallback/fr8_payload_capture.md` holds, per tool: the
instruction given to agy that produced the call, the stream-json line showing it, and whether
`workspacePaths` is present in the envelope. No suite test reads the probe directory, so
archiving it cannot break the suite (as Task 22 keeps its formula probe out of the suite). It also holds the sha, `agy --version`, and the
`ls` reading showing the capture hook removed (probe-then-delete). The fixture project's
`notebook_edit` sample needs an `.ipynb` file in the project, which the fixture creates.

**Capture gate.** All six samples must exist before the RED dispatch. A missing sample (agy
refuses the instruction, or never routes the edit through that tool) is not dropped: re-instruct
up to three times, then stop the Task and report which tool could not be captured, with its three
instructions. The capture does not pass on a subset.

`PATH_KEYS` gains each class-(b) key the capture shows that it does not already hold. If
`run_command`'s envelope names its command or workdir under a key other than `CommandLine` or
`Cwd`, class (c)'s reads change to the captured keys, and that is a finding against design
§"FR-4", reported before GREEN. If the `run_command` sample carries no workdir key at all,
`capture.json`'s `workdir_key` is `null`, item 3's `workdir-outside` id cannot be built, and that
is reported as a finding against design §"FR-4" before the RED dispatch. `class_inventory.py` (Task 0) is re-run with the capture as its
second log.

**Tests**:
1. `tests/test_h_mad_agy_tdd_gate.py::test_capture_holds_every_required_sample` — one id per
   required tool (6): the fixture file exists, parses as JSON, names that tool in its `toolCall`,
   and `h-mad/tests/fixtures/agy-payloads/capture.json` holds a boolean `workspacePaths_present`
   for it that agrees with the sample (the key is in the envelope exactly when it is `true`).
   6 nodes.
2. `tests/test_h_mad_agy_tdd_gate.py::test_captured_payload_is_judged_by_its_recorded_key` — one id
   per class-(b) tool (5): the captured payload, with its path values aimed at a production `.py`
   without a failing test under `active`, denies with the judge's kind (not `judge-error`). 5 nodes.
3. `tests/test_h_mad_agy_tdd_gate.py::test_captured_run_command_is_judged_by_its_recorded_keys` —
   the captured `run_command` envelope, `active`, in a fixture root holding `.venv/bin/python` (a
   regular file) and `.venv/pyvenv.cfg` (Task 7 item 6's root-venv fixture), and an existing
   directory `elsewhere` beside the root, outside it. The value under the captured `command_key`
   is set to `.venv/bin/python -m pytest tests/test_x.py`; the value under the captured
   `workdir_key` is set per id (audit cycle 2, I2):
   - `workdir-root`: `str(root)` → allowed;
   - `workdir-outside`: `str(elsewhere)` → deny `kind=shell-not-admitted` (a relative venv
     interpreter under a `cwd` outside the root, design §"FR-4" class (c), `M:F2-ESCAPE`).
   2 nodes. A reader that misses the captured workdir key falls back to the root, so
   `workdir-outside` allows and fails; a reader that misses the captured command key denies
   `judge-error` (`CommandLine` missing), so both ids fail. `ls` (v1.1's fixture) cannot do this:
   the shared policy admits `ls` under every `cwd`. Controlled pair, run at `84ec2133` against the
   live `_safe_shell_command` loaded from `h-mad/hooks/h-mad-codex-tdd-gate.py`, on a scratch root
   with that `.venv` and an outside directory, a reader on the captured key against one that
   ignores it (`cwd` defaulting to the root): the venv command under `workdir-outside` gives
   `False` read against `True` ignored, the other three cells (venv under `workdir-root`, `ls`
   under both) agree at `True`. The scratch was deleted.
4. `tests/test_h_mad_agy_tdd_gate.py::test_class_a_names_are_in_the_recaptured_inventory`. 1 node.

**RED split**, derived from the committed capture before the RED dispatch, and stated in it:
- item 1: 6 P. The capture is committed first; this item is the capture gate's regression pin;
- item 2: an id fails at RED exactly when its captured path key is not in `PATH_KEYS` at the RED
  base. Only `write_to_file` → `TargetFile` is there, from Task 5. So `write_to_file` is P when
  its captured key is `TargetFile`, and F otherwise; each of the other four is F when its captured
  key is new and P when the capture shows a key already mapped;
- item 3: both ids P when the captured `command_key` and `workdir_key` are `CommandLine` and
  `Cwd` (Task 7's reads). When `command_key` differs, both F. When only `workdir_key` differs,
  `workdir-outside` F and `workdir-root` P;
- item 4: P, unless the re-capture drops a class-(a) name, which is a finding for the design.
Total 14 nodes (6 + 5 + 2 + 1). F is the number of item-2 and item-3 ids the rules above mark F, and P is 14 minus F.
When F is 0, the Task is **capture-only**: no production change, the RED dispatch's gate is
"0 F, 14 P", and GREEN is the RED tree.

**Mutation rows**: none new. A `PATH_KEYS` entry is data: removing one fails its own item-2 node,
and the no-target guard keeps its Task 6 row.

**Acceptance Criteria**:
- [ ] AC-8.1 (the payload capture, stamped with the sha and `agy --version`): all six samples and
  `capture.json` are committed under `h-mad/tests/fixtures/agy-payloads/`, and the capture record,
  with the capture hook's removal, under `docs/03-analysis/probes/agy-coder-fallback/`. Item 1
  passes.
- [ ] Items 2–4 pass; the inventory partition and its difference from Task 0's are recorded.

**Dependencies on other tasks**: the merge of Tasks 0–19.

---

## Task 21: post-merge tracer

**Production files**: none
**Test files**: none
**Task shape**: `operational` — it runs the gate, the check and the assembler that Tasks 5–10
built.

**Description**: Design §"FR-8" step 3, spec FR-8 steps 2, 2a and 3, in Task 20's fixture project.
Step 2: a real forbidden write through `hmad-dispatch exec agy` with the operator's global
`~/.gemini/config/hooks.json` loaded is refused. Step 2a: a delay handler (matcher `*`, `timeout`
T, sleeping at least 2T, then printing a `deny`) is added to the fixture's `.agents/hooks.json`,
with `shasum -a 256 .agents/hooks.json` recorded before; agy is told to write one named non-test
file; the file's existence, the wall time and agy's message are read independently; one outcome
from step 2a's table (`timeout-blocks`, `timeout-allows`, `timeout-not-enforced`,
`session-error`) is named; the delay handler is removed and the after-hash compared. Step 3: the
RED/GREEN readings with re-run, revert and mutation results, and where agy's files landed. Every
reading is committed under `docs/03-analysis/probes/agy-coder-fallback/`, stamped with the sha and
`agy --version`.

**Acceptance Criteria**:
- [ ] AC-8.1 (the real refusal; the RED/GREEN readings with re-run, revert and mutation results):
  committed and stamped.
- [ ] AC-8.2: the step-2a reading names exactly one outcome consistent with its three readings,
  shows the delay hook removed and the before and after hashes equal; `session-error` is re-run
  and never counts. On `timeout-allows`, `agy-runtime.md` §"The TDD gate" carries the fail-open
  residual and the operator question is raised before the gate is called verified.

**Dependencies on other tasks**: Task 20.

---

## Task 22: post-merge adoption and the derived timeout

**Production files**: `h-mad/scripts/h_mad_assemble_tdd.py`, `.agents/hooks.json` (new)
**Test files**: `h-mad/tests/test_h_mad_assemble_tdd_agent.py`
**Task shape**: `new-behaviour`

**Description**: Design §"FR-8" steps 4–5. This repository's `.agents/hooks.json` holding FR-5's
exact entry is committed only after Task 21's refusal passed (`git check-ignore -v
.agents/hooks.json` prints nothing at `4e4b5ded`, so no `git add -f` is needed; the file is absent
today), and step 2 is re-run once here. The assembler's `TIMEOUT_DEFAULTS["agy"]` becomes
`max(900, 3 × slower turn)` rounded up to a multiple of 60, over the readings Task 21 committed.
The committed probe `docs/03-analysis/probes/agy-coder-fallback/fr8_timeout_formula.py` recomputes
the figure from those readings and asserts the assembler's default equals it (a probe, not a suite
test, so archiving the probe directory cannot break the suite).

**Tests**:
1. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_default_timeouts[agy-1500]` is re-pointed:
   its id becomes `agy-` followed by the figure the formula probe prints, and its expected value
   becomes that figure.
2. `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_wired_writes_the_prompt` (Task 10 item 6)
   pins `--timeout 1500` in the command block. Its expected `--timeout` becomes the same figure.

Both expectations change in the RED commit. Task 10's `TIMEOUT_DEFAULTS["agy"]` is still `1500`
at RED, so both nodes fail there.

**RED split**: when the derived figure is not 1500, 2 F: the re-pointed `test_agent_default_timeouts`
id and `test_agent_agy_wired_writes_the_prompt`. When it is 1500, 0 F: this Task changes no code
and no test, and records that.

**Anchors**: the edit touches only the `"agy"` value of `TIMEOUT_DEFAULTS`, on which no row sits
(Task 10 adds `assemble_tdd_agy.json`, and none of its rows anchors on that value).
`--check-anchors` over the 8 specs naming the assembler by then: Task 10's 7, plus
`new_caller_carveout_copies.json`, whose `fr9-copy-L5` row names it (Task 13).

**Acceptance Criteria**:
- [ ] AC-8.1 (the default timeout equals FR-8's formula over the readings): the formula probe
  prints `PROBE: PASS`.
- [ ] This repository's step-2 re-run is committed and stamped.
- [ ] The feature is recorded COMPLETE only after AC-8.1 and AC-8.2 pass (spec D-13).

**Dependencies on other tasks**: Task 21.

---

## Mutation-row ledger

Design v1.4 (`2cd5d7f1`) §"Mutation rows (AC-X)" lists 60 new rows, counted from its list: FR-1 3;
FR-2 4 (3 `_cause` branches and the other-peer step); FR-3 4; FR-6 2; FR-4 19 (14 single bullets,
v1.4's "T2a removed" among them, 3 kinds, 2 class-(c) `cwd` rows); FR-5 8 (7 reasons and `UNWIRED`
returning 2); FR-7 10 (3 append rows, 2 `APPEND_ONLY`, 5 warning and `property_valid` rows); FR-9
10 (8 + 2). 3 + 4 + 4 + 2 + 19 + 8 + 10 + 10 = 60.

| Task | design rows | wire rows (cut + converse) | doc-pin rows (plan §"Success Criteria") | discipline and decision rows |
|---|---|---|---|---|
| 1 | 4 (FR-1 3, FR-7 1) | 0 | 0 | 0 |
| 2 | 4 | 0 | 0 | 0 |
| 3 | 4 | 3 (2 + 1) | 0 | 0 |
| 4 | 2 | 0 | 0 | 2 (signal discipline, I4) |
| 5 | 4 | 0 | 0 | 1 (signal discipline) |
| 6 | 11 | 0 | 0 | 0 |
| 7 | 4 | 0 | 0 | 0 |
| 9 | 7 | 0 | 0 | 1 (connection, I3) |
| 10 | 1 | 2 (1 + 1) | 0 | 1 (marker discipline) |
| 11 | 5 | 0 | 0 | 0 |
| 12 | 4 | 0 | 0 | 0 |
| 13 | 8 | 0 | 0 | 0 |
| 14 | 2 | 0 | 0 | 0 |
| 15 | 0 | 0 | 4 | 0 |
| 16 | 0 | 0 | 8 | 0 |
| 17 | 0 | 0 | 6 | 0 |
| total | 60 | 5 | 18 | 5 |

Design rows: 4 + 4 + 4 + 2 + 4 + 11 + 4 + 7 + 1 + 5 + 4 + 8 + 2 = 60, equal to the design's
list. Wire rows: 3 + 2 = 5. Doc-pin rows: 4 + 8 + 6 = 18. Discipline and connection rows:
2 + 1 + 1 + 1 = 5, none of them in the design's list (Task 4's two Codex self-check verdict rows
and Task 9's budget-connection row from audit cycle 2, Task 5's signal-discipline and Task 10's
marker rows from cycle 1). OD-2's row is now a design row (design v1.4). All new rows:
60 + 5 + 18 + 5 = 88. Existing rows
changed, not new: the 31 re-pointed in Task 4, of which `CX-FOLD` also takes a new `find` and
`CX-FORCE-SCRIPT` a new `replace`; and the re-anchors of Tasks 2, 3 and 10 (`w10a-grok-by-default`
named; the others as `--check-anchors` finds them). Each Task states which existing rows its
edits touch.

## Decisions (closed)

- **OD-1 (Task 17)**, closed 2026-10-16. Operator: option (A), a transcription test over the
  written procedure. Spec FR-1 and design FR-7 stand unchanged.
- **OD-2 (Task 6)**, closed 2026-10-16. Operator: a class-(b) target naming an existing directory
  is refused with `kind=judge-error` under `S` (`active`, `unknown`) and allowed under `inactive`.
  Task 6 implements it as T2a, with item 10 and row `od2-directory-target-check-dropped`. Spec v1.10
  (`c283bb63`) records it as D-16, design v1.4 (`2cd5d7f1`) as T2a.

No decision is open.

## Residuals carried from the design

Each stays where the design states it (design §"Residuals"); the Tasks above add no fixture that
claims to close one. The ones a Task touches: the `which` matrix (Task 3's regression guard); the
verb reads the root only (Task 2); the class-(a) judgement and the six-line shell composition
(Tasks 5, 7, 8); a sibling `overwrite`, the review-leg agy, worktree state (Task 21 observes, does
not settle); an equivalent command spelling (Task 9); a writer that bypasses `_mutate` (Task 11);
prose application, a seventh surface (Tasks 13, 18); a later `KINDS` member (Task 5's kind scan
reads `KINDS` live); T4's empty-string arm (Task 6); the author-before-review ordering (Task 17).

Added by this plan, not by the design:
- OD-2's T2a covers an existing directory only. A target ending in `/` that names no existing
  directory goes through T3–T7 as a file name (Task 6).
- The staging step is prose that the orchestrator follows. Task 16's tests pin its words, not its
  execution (the same residual as AC-7.3 under OD-1 (A)).

## Version History
- v1.0: Initial implementation plan draft (2026-10-16), Phase 5a, from design v1.3 (4e4b5ded), spec v1.9 (4bef0e76), plan v1.6 (8e242d06); tree read at 4e4b5ded. 23 Tasks (0-19 pre-merge, 20-22 post-merge per D-13); wiring Tasks 3 and 10 with WIRE/WIRE-PIN; 59 design mutation rows plus 3 wire-cut and 14 doc-pin rows; OD-1 (AC-7.3 surface vs spec FR-1 "no script reads it") and OD-2 (directory target).
- v1.1: Impl-plan audit cycle 1 (2026-10-16), answering codex p1 (9 must, 3 should) and agy p2 (2 must, 2 should) against v1.0 (fc6b497e), tree at 683777df. Grammar probe fr3_state_line_grammar.py updated (derived/shipped modes, --control, --hook) so Task 3's post-GREEN re-run passes. Harness cwd convention (scripts/ from h-mad/). agy --self-check: verdict FAILs exit 0, policy-import exit 2. Task 16 staging step with record=failed halt step5:implementer_switch_unrecorded and its discriminating control. Task 20 requires all six samples (5 class-(b) + run_command), RED split derived from captured keys, capture-only gate. Task 10 converse wire row, [H-MAD] halt marker. Task 3 converse wire row. Task 11, 9, 10 RED assertions on refusal text, not argparse exit 2. Task 2 status fixtures expect reason=status. Task 22 two timeout tests. Task 4 CX-FOLD find and CX-FORCE-SCRIPT replace. Task 15 FR-9 prompt bullets. hook_wiring.json 12 rows. OD-1 closed (A); OD-2 closed: directory target judge-error under S (Task 6 T2a). Rows: 59 design + 5 wire + 18 doc-pin + 3 discipline/decision = 85.
- v1.2: Impl-plan audit cycle 2, final corrective revision, not re-audited (2026-10-16), answering codex p1 (4 must, 1 should; agy p2 clean) against v1.1 (fc92becf), tree at 84ec2133, design v1.4 (2cd5d7f1), spec v1.10 (c283bb63). I1: Task 6 item 1 gains number-inactive and list-inactive, the discriminators for fr4-class-b-target-presence-only (null-inactive does not discriminate: canonicalise treats a falsy target as the root); 34->35 nodes with the t2a-directory deny-row id. I2: Task 20 item 3 uses the root .venv interpreter under the captured workdir key, workdir-root and workdir-outside (ls cannot discriminate); 14 nodes. I3: Task 9 item 4 patches h_mad_tdd_judge.JUDGE_BUDGET_S to 41.1 (timeouts 61 and 62), check_agy reads the module attribute at call time, row fr5-timeout-floor-hardcoded-60; 18 nodes. I4: Task 4 fixes both Codex --self-check verdict FAILs (parser, shell-policy) to stdout with exit 0, policy-import keeps exit 2; no existing test pinned exit 2; 2 tests, 2 rows; Task 4 shape new-behaviour; residual removed. I5: Task 20 suite metadata in h-mad/tests/fixtures/agy-payloads/capture.json. Design v1.4 alignment: FR-4 19 design rows (T2a), deny table 17 rows, owed lines marked recorded. Rows: 60 design + 5 wire + 18 doc-pin + 5 discipline/connection = 88.
