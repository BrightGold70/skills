# Design: multi-host-runtime

## Executive Summary

A committed construct registry and a file-reading parity checker (`h-mad/tests/host_parity.py`)
gate every host adapter on mapping rows, not mentions. A shared host classifier
(`h-mad/scripts/h_mad_host.py`) makes the context budget and the resume oracle answer cannot-judge
under a declared non-Claude `HMAD_HOST`. `h_mad_install_check.py` checks two more skill roots by
reusing `check_siblings`. Two grok adapters and parity tables in the four existing adapters carry
the per-host mappings. A committed probe sidecar holds the calibration, the seed-coverage reading,
the byte-identity arms and the live-smoke assertions.

## Overview

The design implements spec v1.2 (FR-1 to FR-12) through plan v1.2 and keeps every plan decision,
with the exceptions listed in §"Supersedes the plan on". Each exception comes with its evidence and
a revert.

Three constraints shape it:
- **Existing mutation anchors must stay unique.** `h_mad_mutation_harness.py --check-anchors`
  refuses an anchor that matches twice. The three existing mutation specs over the touched
  scripts carry 17 anchors today: 16 in the three scripts (9 + 5 + 2) and one in
  `h-mad/SKILL.md`'s `cannot_judge` row. No new code or text may repeat any of them.
- **Tests must run from the skill alone.** Everything a test imports lives under `h-mad/`.
- **Hosts are reached only through `hmad-dispatch`,** and only by the operator's live smoke.

The key decisions:
- Host classification is one module, and both scripts call it.
- The agy-root check partitions `check_siblings` output. It does not classify a second time.
- The adapter table is located with the fence-aware helpers of `h_mad_doc_block_exec`.
- The smoke assertions read **input events** of each host's log format, never free text.

## Supersedes the plan on

Each item states the plan text it replaces, the evidence, and the revert. The owed spec and plan
wording is listed in the author's report, not here.

1. **V-11.1's grok clause reads the `available_commands` event, not a `system`/`init` line.**
   - What the plan and spec say: plan §"Convention Prerequisites" `v111`, and spec F11, expect a
     `system`/`init` line whose `skills` field holds `h-mad`.
   - What `exec grok` emits: grok-codex-fallback's `exec grok` arm passes
     `--output-format streaming-json` (its design §D3, the `gargs` line). In
     `~/.grok/docs/user-guide/14-headless-mode.md`, `streaming-json` is a `type`-tagged event
     stream. The `system`/`init` line belongs to the other format, §"streaming-messages-json".
   - Measured: the committed probe log `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson`
     holds no `system` event. It holds 9 `available_commands` events, each with 316 `commands`,
     and the names include `h-mad` and `handoff` (DP5).
   - Consequence: under the plan's form, every grok smoke prints `FAIL V-11.1`, and `recover`
     then reverts a good integration.
   - Revert: restore the plan's `init` check. That is correct only if `exec grok` is changed to
     `streaming-messages-json`, which is the sibling feature's decision.
2. **V-11.1 orders input events, never text matches over the whole log.**
   - What the plan does: `v111` greps the whole log for the first `h_mad_*.py` / `hmad-dispatch `
     line.
   - Why that fails: every host's log records **tool output** (DP6):
     - grok: `tool_call_update.rawOutput.FileContent.content`;
     - agy: `step_update.tool_info.output`;
     - codex: the lines after ` succeeded in`.
     A host that reads `SKILL.md` before the adapter therefore puts dozens of `h_mad_*.py`
     mentions into the log before the adapter read. The plan's `v111` reads the first mention as
     "a script ran first" and fails a correct run.
   - The rule over the class: an event counts only by what the host **asked for** (tool name plus
     input), never by what it **received** (output).
   - Revert: keep the plan's `v111`, and drop rehearsal case R4 below, which that form fails.
3. **`v111` and `v112` live in one committed probe file, `smoke_assert.py`.**
   - The smoke script and the Phase-6 rehearsal both call this file, which satisfies the plan's
     "the same definitions, not a copy" with one file instead of a sourced shell function.
   - The verdict is read as a stdout token, never as `$?`.
   - Revert: inline the Python back into the smoke script as shell functions.
4. **The rehearsal runs in Phase 6 and is recorded in the Phase-6 document.**
   - This reconciles the plan's own open item: 7c archives `docs/03-analysis/multi-host-runtime*`
     before 7f, so a record written "before 7f" but after 7c would land outside the archive.
   - The probe directory `docs/03-analysis/probes/multi-host-runtime/` is **not** matched by 7c's
     `mv docs/03-analysis/${FEATURE}*` glob (`h-mad/references/inline-protocols.md` §"7c —
     Archive"), so the smoke can still call `smoke_assert.py` after 7c.
5. **Fixture count: 36 disjunct fixtures plus 6 splits, 42 in total.**
   - The plan allows the design to split a disjunct and forbids merging two. §D2.6 lists the six
     splits.
   - Each split closes a type or shape case that a single fixture per disjunct leaves unpinned.
6. **The host value rule is one module, `h-mad/scripts/h_mad_host.py`.**
   - The plan requires "one value rule, shared by both readers" plus an agreement test.
   - A module is the single-source form (`invariants.base.md` §"Single-source contract"). The
     agreement test is kept, because it pins the two **call sites**.
7. **The agy root is classified by partitioning `check_siblings` output.**
   - Plan §Deliverables says "the name × state rule". A second classifier would duplicate
     `check_siblings`'s logic.
   - Refactoring `check_siblings` itself would move four of `install_check_siblings.json`'s five
     anchors (DP3).
8. **AC-12.2 is claimed on both byte-identity arms.**
   - The plan did not claim AC-12.2 at the real defaults "until the spec restates it".
   - Spec v1.2 restated it (spec Version History v1.2), so arm B's closed diff is now the AC.
9. **An unknown `HMAD_HOST` value is JSON-encoded in `host=`.**
   - Spec FR-8 writes `host=<value>`. A value holding a newline would otherwise print a second
     stdout line, and a value holding a space would split the token.
   - A declared host (`codex`, `agy`, `grok`) is printed bare, exactly as AC-8.1 requires.

## Architecture Overview

```text
                 tests (read files only)                       probes (operator / phase steps)
 ┌───────────────────────────────────────────────┐   ┌───────────────────────────────────────────┐
 │ test_host_construct_parity.py                 │   │ docs/03-analysis/probes/multi-host-runtime│
 │   └─ host_parity.check(ParityPaths, axes, ex) │◄──┤   calibrate.sh <sha>        (FR-4)        │
 │        ├─ registry  h-mad/references/         │   │   seed.json + seed_coverage.py (FR-1/P2b) │
 │        │            host-constructs.json      │   │   byte_identity.py --base   (FR-8/10/12)  │
 │        ├─ h-mad/SKILL.md, handoff/SKILL.md    │   │   smoke_assert.py v111|v112|rehearse      │
 │        └─ 6 adapters {h-mad,handoff}/         │   │     (FR-11; called by the Phase-7 smoke)  │
 │             references/{codex,agy,grok}-      │   └───────────────────────────────────────────┘
 │             runtime.md  (## Construct mapping)│
 │ test_host_runtime_docs.py  (section tokens)   │
 │ test_h_mad_host_declaration.py                │     scripts (runtime)
 │ test_h_mad_install_check_roots.py             │   ┌───────────────────────────────────────────┐
 │ conftest.py  (+ autouse hermetic roots)       │   │ h_mad_host.classify_host(environ)         │
 └───────────────────────────────────────────────┘   │   ├─ h_mad_context_budget.main  (W1)      │
                                                     │   └─ h_mad_resume_decision.decide (W2)    │
                                                     │ h_mad_install_check.main → check(...) (W3)│
                                                     │   └─ check_siblings(repo, <each root>)    │
                                                     └───────────────────────────────────────────┘
```

Nothing in the runtime column reads the registry, the probes or any `h-mad` test file. `handoff`
gains no runtime read of any `h-mad` file.

## Detailed Design

### D1 — Registry `h-mad/references/host-constructs.json` (FR-1)

- **Shape.**
  - Top level: `{"constructs": [ … ]}`. Other top-level keys are ignored; this residual lets the
    file carry a `"$comment"`.
  - Each element has exactly the keys `id`, `pattern`, `skills` and `description`.
  - Element order is the spec seed table's order, and failure lines follow it.
- **Content.** The 22 entries of spec §"Construct registry seed", written as follows:
  - `H` is expanded to `(?:~|\$HOME|\$\{HOME\})/\.claude`.
  - The table's `\|` is un-escaped to `|`.
  - `both` becomes `["h-mad", "handoff"]`.
  - In JSON every regex backslash is doubled.
  - `description` is one sentence naming the Claude construct.

  One element, as written:

  ```json
  {"id": "claude-settings",
   "pattern": "(?:~|\\$HOME|\\$\\{HOME\\})/\\.claude/settings(?:\\.local)?\\.json",
   "skills": ["h-mad", "handoff"],
   "description": "Claude Code's user settings file, including the .local variant."}
  ```
- **Where the seed lives before the registry exists.** The probe sidecar carries the same 22
  entries as `seed.json` (D11). That is a frozen copy of the spec seed at `6494b3c`, and its only
  job is to measure `<base>` at 5c, before the registry exists. The committed registry starts from
  it and may diverge by the AC-4.6 record. After 5c the registry is authoritative, and `seed.json`
  is never read by a test.
- **AC-1.2.** `test_host_construct_parity.py` holds `SEED_IDS`, a constant listing the 22 ids, and
  `RETIRED_IDS: dict[str, str]`, empty at v1.0. A test asserts that every seed id is in the
  registry, or is a `RETIRED_IDS` key with a non-empty reason. Any key added to `RETIRED_IDS` is
  also written into the Phase-6 AC-4.6 record, and review checks the two agree.

### D2 — Parity checker `h-mad/tests/host_parity.py` (FR-3)

**D2.1 Interface.** `host_parity.py` is a plain module. Pytest does not collect it, because
`pytest.ini` sets only `testpaths` and the default `python_files` patterns are `test_*.py` and
`*_test.py` (DP7).

```python
@dataclass(frozen=True)
class ParityPaths:
    root: Path                      # file= is relative to this when inside it
    registry: Path
    skills: Mapping[str, Path]      # {"h-mad": …/h-mad/SKILL.md, "handoff": …/handoff/SKILL.md}
    adapters: Mapping[Path, str]    # adapter path -> the skill it maps ("h-mad" | "handoff")

@dataclass(frozen=True)
class Failure:
    kind: str; file: str; id: str = "-"; reason: str | None = None; token: str | None = None
    def line(self) -> str: ...      # the PARITY grammar of plan §Implementation Strategy

def live_paths(root: Path) -> ParityPaths: ...
CATCH_ALL_AXES: Mapping[str, str]   # {"A1": …, "A2": …, "A3": …, "A4": …}
A4_BRANCHES: Mapping[str, str]      # {"tilde": r"~", "home": r"\$HOME", "home_braced": r"\$\{HOME\}"}
EXCLUSION_SUFFIXES: tuple[str, ...] # ("Error","Exception","Warning","Expired","Exit","Interrupt")
def a4_pattern(branches: Iterable[str]) -> str: ...   # "(?:" + "|".join(b) + r")/\.claude\b"
def expand_branches(pattern: str) -> list[str]: ...   # raises UnsupportedPattern

@dataclass(frozen=True)
class ParityResult:
    failures: list[Failure]
    stages: tuple[str, ...]         # stages that ran: "registry", "skill", "adapter"

def check(paths: ParityPaths, *, axes: Mapping[str, str] = CATCH_ALL_AXES,
          exclusion_suffixes: Sequence[str] = EXCLUSION_SUFFIXES) -> ParityResult: ...
```

`live_paths(REPO_ROOT)` is where the six adapter paths are named, with `REPO_ROOT` taken as
`Path(__file__).resolve().parents[2]`. Imports are `json`, `re`, `dataclasses`, `pathlib` and
`typing`, plus `h_mad_doc_block_exec`, reached through `sys.path.insert(0, <h-mad>/scripts)`, the
same way `h-mad/tests/docsections.py` reaches it.

**D2.2 Stages and output order.**
1. **Registry stage.** It runs in four steps:
   - **Structural.** The checks are `missing_file`, `invalid_json`, `not_object`,
     `no_constructs`, `constructs_not_array` and `element_not_object`. The first hit stops the
     run, because elements cannot be iterated safely.
   - **Per-element shape, in element order.** Missing keys come first: one `missing_key:<k>` line
     per key. Then extra keys: one `extra_key:<k>` line per key. If any key is missing, the
     element's field checks are skipped. Otherwise:
     - `id` must be a `str` matching `^[a-z][a-z0-9-]*$`, else `bad_id`;
     - `description` must be a `str` whose `.strip()` is non-empty, else `empty_description`;
     - `skills` must be a non-empty `list`, else `empty_skills` for `[]` and `bad_skill` for a
       non-list;
     - every member of `skills` must be one of the two names and appear once, else `bad_skill`.
   - **`DUPLICATE_ID`,** over the ids that passed `bad_id`. One line per id that occurs more than
     once.
   - **`BAD_PATTERN`,** for each element whose `pattern` is not a `str`, or whose
     `re.compile(pattern)` raises `re.error`.

   Suppression rule (a): if any `REGISTRY_UNREADABLE` line exists, `check()` returns after this
   stage.
2. **`SKILL.md` stage,** per skill in the order `h-mad`, `handoff`:
   - `STALE_ENTRY` and `UNDECLARED_SKILL`, in entry order, skipping `BAD_PATTERN` entries
     (rule b);
   - then `UNREGISTERED`, in hit-offset order. It is skipped entirely for a skill that any
     `BAD_PATTERN` entry declares (rule b).

   An unreadable `SKILL.md` raises. It is not a failure kind: both files are tracked, and a
   missing one is a harness fault.
3. **Adapter stage,** per adapter in sorted path order: the table kinds (D2.4), then the row kinds
   (D2.5).

**D2.3 Catch-all (FR-4).**
- **Per-axis matching.** Each axis in `axes` runs separately with `re.finditer` over the whole
  `SKILL.md` text, fences included, because the calibration counted the whole file.
- **Exclusion.** The suffix exclusion applies to A2 hits only (spec FR-4). A hit is excluded when
  its text matches `(?:<suffixes joined by |>)` followed by a backtick at its end.
- **Coverage.**
  - A remaining hit `(s, e)` is covered when some match span `(s2, e2)` of a pattern declared for
    that skill overlaps it (`s2 < e and s < e2`).
  - Declared patterns are compiled once, and their spans are computed once per skill.
  - An uncovered hit yields `UNREGISTERED file=<SKILL.md> id=- token=<hit text>`.
- **What per-axis matching changes.** Per-axis matching can report two overlapping hits where the
  spec's single alternation (`grep -o`) reports one. That is a difference in **count** only, and
  no verdict depends on the count. The calibration figures are produced by `calibrate.sh`, which
  runs the spec's command verbatim, and never by `check()`.
- **Parameters.**
  - `axes` is a parameter so AC-4.2 can pass one axis alone, or all but one.
  - `A4` is built by `a4_pattern(A4_BRANCHES.values())`, so a branch control passes
    `a4_pattern` over one branch, or over two of the three.
  - `exclusion_suffixes` is a parameter so AC-4.3 can remove one suffix.

**D2.4 Adapter table location and parsing (FR-2).**
1. The adapter text is read as UTF-8. A path that does not exist reads as `""`.
2. `found = h_mad_doc_block_exec.find_heading(text, "## Construct mapping")`, using the full form,
   so a `### Construct mapping` does not match.
   - A raised `AmbiguousHeading` gives `TABLE_MISSING reason=heading_twice`.
   - `None` gives `TABLE_MISSING reason=no_heading`.
   - Otherwise `found` is `(start, level)`, where `start` is the end of the heading line (DP4).
3. `end = h_mad_doc_block_exec.fence_aware_end(text, start, level)`.
4. The table is the first run of **consecutive-`lineno`** `_fence_events(text)` events of kind
   `prose` with `start <= event.start < end`, whose line, after up to three leading spaces, begins
   with `|`.
   - Fence bodies are `body`/`open`/`close` events, so a pipe line inside a fence is never the
     table.
   - Tests already call `h_mad_doc_block_exec._fence_events` (DP4), and
     `test_h_mad_doc_block_exec.py` pins fence recognition to that one function. Reusing it adds
     no second fence scanner.
   - No such run gives `TABLE_MISSING reason=no_table`.
5. **Cell split.**
   - Strip the line, drop one leading `|`, and drop one trailing `|` that is not escaped.
   - Split on `(?<!\\)\|`, un-escape `\|` to `|`, and strip each cell.
   - An adapter therefore writes a literal pipe inside a cell as `\|`, for example
     `exec codex\|agy`.
6. **Header and delimiter checks.**
   - Row 1's cells must equal `["construct", "status", "mapping", "source"]`.
   - Row 2 must have four cells, each matching `:?-+:?`.
   - Either failure, or a run shorter than two rows, gives `TABLE_MALFORMED reason=header`.
     Suppression rule (d) then drops every `ROW_*`, `STATUS_INVALID` and `CELL_EMPTY` line for
     that adapter.
7. **Body rows.** Each row from row 3 on must have 4 cells, else
   `TABLE_MALFORMED reason=cell_count id=<first cell if it matches the id rule, else ->`.
   Suppression rule (e) applies: such a row counts as present for its id and is not checked for
   any other kind.
8. The `construct` and `status` cells may carry one surrounding pair of backticks, which is
   removed before comparison.

**D2.5 Row kinds.** Every well-formed body row is checked against five kinds:
- `ROW_UNKNOWN_ID`: the id is not in the registry.
- `ROW_WRONG_SKILL`: the id is in the registry but not declared for the adapter's skill.
- `ROW_DUPLICATE`: one line for every second and later row with the same id.
- `STATUS_INVALID`: the status is neither `mapped` nor `not-applicable`.
- `CELL_EMPTY`: a `mapping` or `source` cell is empty, reported as
  `reason=<mapping|source>:<no_alnum|tbd|todo>`. `no_alnum` is tested first, then a
  case-insensitive exact match on the two tokens.

`ROW_MISSING` is then reported for every declared entry that has no row, cell-count rows
included. Ids with `DUPLICATE_ID` are excluded from every `ROW_*` kind (rule c).

**D2.6 The 42 kind fixtures.** Each fixture is one input. It asserts that its produced
`{(kind, reason)}` set equals exactly its own one pair. The set breaks down as follows:
- **36 disjunct fixtures** (plan inventory):
  - `REGISTRY_UNREADABLE`: 15;
  - `TABLE_MISSING`: 3;
  - `TABLE_MALFORMED`: 2;
  - `CELL_EMPTY`: 6;
  - each of the other 10 kinds: 1.
  The `ROW_MISSING` fixture **is** AC-3.2's: its adapter table lacks the `advisor` row, and its
  prose mentions `advisor` three times.
- **6 split fixtures** (§"Supersedes" item 5):
  - a non-`str` `pattern` → `BAD_PATTERN`;
  - a non-`str` `id` → `REGISTRY_UNREADABLE reason=bad_id`;
  - a non-list `skills` → `reason=bad_skill`;
  - a `skills` with the same name twice → `reason=bad_skill`;
  - a non-`str` `description` → `reason=empty_description`;
  - a bad delimiter row → `TABLE_MALFORMED reason=header`.
- **Residual.** A whitespace-only `description` is rejected by the `.strip()` predicate, but no
  fixture pins that. The `""` fixture takes the same predicate branch.

Every fixture is built from one shared **clean baseline**: a two-entry registry, two fixture
`SKILL.md` files, and six clean adapters in `tmp_path`. That baseline yields `[]`, and each fixture
applies one edit to it. A test asserts that the clean baseline yields `[]`. That test is the
precondition that makes each exact-set assertion mean "this edit alone".

The five suppression fixtures are (a) to (e). Each is built so that, without its rule, it yields
two pairs, and with the rule it yields exactly one pair.

**D2.7 Branch expansion (plan "Registry patterns").**
- **The grammar.** `expand_branches(pattern)` is a recursive descent over the pattern string with
  a closed grammar:
  - an escape `\x` is one atom;
  - a character class `[…]` is one atom (a leading `]` and `\]` inside are handled);
  - a lookaround `(?=…)`, `(?!…)`, `(?<=…)` or `(?<!…)` is one verbatim atom, never a branch;
  - a group `(?:…)` or `(…)` expands to its alternatives, and an immediately following `?` adds
    the empty alternative;
  - `|` separates alternatives at the current level;
  - any other character is one atom.

  The result is the cartesian product of those alternatives, as regex strings.
- **Refusal.** Any shape outside the grammar raises `UnsupportedPattern`. The shapes are:
  - `*`, `+` or `{` after a group;
  - `?`, `*`, `+` or `{` after a non-group atom;
  - an unbalanced group.

  The refusal is a test failure. A future registry pattern the expander cannot read therefore
  fails loudly, instead of being counted as one branch.
- **Validated before writing.** A scratch implementation of exactly this grammar, run over the
  spec seed at `6478b8b5` and then deleted, reproduced plan P2b's figures (DP2).
- **Samples.** `test_host_construct_parity.py` holds `BRANCH_SAMPLES: dict[str, list[str]]`: 54
  hand-written literal samples over the 22 entries, one per branch. Examples: `"Stop-hook"` for
  `hook-event`'s lookahead branch, and `"$HOME/.claude/settings.local.json"` for one of
  `claude-settings`' six branches. The test asserts, per entry:
  - the sample count equals `len(expand_branches(pattern))`;
  - each sample matches exactly one expanded branch (`re.search`);
  - the full pattern matches every sample.

### D3 — Host classifier `h-mad/scripts/h_mad_host.py` (FR-8, FR-9)

```python
HOST_ENV = "HMAD_HOST"
NON_CLAUDE_HOSTS = ("codex", "agy", "grok")

def classify_host(environ: Mapping[str, str] | None = None) -> tuple[str, str | None]:
    """('claude', value) | ('declared', value) | ('unknown', value); value None when unset."""
```

- **The value rule.** The comparison is exact, with no strip and no case fold:
  - unset, `""` or `"claude"` → `claude`;
  - a member of `NON_CLAUDE_HOSTS` → `declared`;
  - anything else → `unknown`. That includes `"Grok"`, `" grok"` and a value holding a newline.
- **Imports.** The module is stdlib only and imports nothing else from `scripts/`.
  - `h_mad_resume_decision.py` already puts its own directory on `sys.path`.
  - `h_mad_context_budget.py` is run as a script everywhere, including by
    `hooks/h-mad-advisor-warn.sh`, so its directory is `sys.path[0]`. Tests import it after
    `sys.path.insert(0, SCRIPT.parent)` (`test_h_mad_context_budget.py`).
- **The bare-timeout scan.** `test_h_mad_portable_timeout.py` globs `scripts/*.py` and applies
  `(?:^|[^-\w])timeout\s+\d+` (DP8). The new module carries no such text.

### D4 — Context budget host check, W1 (FR-8)

The check is placed immediately after `args = ap.parse_args(argv)` in `main`, before the ceiling
default and before the `--window` check:

```python
host_class, host_value = classify_host()
if host_class == "declared":
    print(f"ERROR: HMAD_HOST={host_value} has no Claude transcript to measure", file=sys.stderr)
    print(f"CTXBUDGET: UNKNOWN reason=host_unsupported host={host_value}")
    return 2
if host_class == "unknown":
    print("ERROR: HMAD_HOST is not a known host value", file=sys.stderr)
    print(f"CTXBUDGET: UNKNOWN reason=unknown_host host={json.dumps(host_value)}")
    return 2
```

- **What it guarantees.**
  - Stdout is exactly one line on both branches. `--transcript`, `--window` and `--mode` cannot
    change it.
  - With `HMAD_HOST` unset, `""` or `claude`, control falls through to today's code unchanged.
- **Anchor check.** The new text contains none of the nine `context_budget.json` anchors. The
  closest is `print("CTXBUDGET: UNKNOWN reason=no_usage")`, which is not a substring of either new
  line.
- **The advisor-warn hook.** It calls this script without `HMAD_HOST` (plan P15), so it keeps
  today's behaviour on every host. The grok adapter states that consequence (D9).

### D5 — Resume oracle host check, W2 (FR-9)

The host check is the **first statement** of `decide()`:

```python
    host_verdict = _host_verdict(session_id)
    if host_verdict is not None:
        return host_verdict
```

`_host_verdict(session_id)` is a new module-level function. It returns `None` when
`classify_host()` is `claude`, or when `session_id` is truthy. Otherwise it returns the module
constant `CANNOT_JUDGE_WITHOUT_SESSION = "cannot_judge"`.

- **Why the indirection.**
  - `resume_decision_cannot_judge.json` anchors on the substring `        return "cannot_judge"`
    (eight spaces). Neither new line contains it.
  - `resume_decision_cannot_judge.json`'s other anchor, `if not state_file.is_file():` followed
    by `return "start_fresh"`, is left untouched.
  - The rule over every touched script: after the change, `h_mad_mutation_harness.py
    --check-anchors` over the three existing specs must print `ANCHORS_OK`, 17 of 17. It prints
    that at `6478b8b5` (DP3).
- **An empty id is no id.** An empty `--session-id ""` is falsy, so it is treated as absent. That
  is the same truth test `_owned_elsewhere` uses.
- **Unknown values.** An unknown value is treated as declared (plan §Implementation Strategy): it
  gives `cannot_judge` without a session id.
- **Not changed.** `h_mad_state_write.py` is out of FR-9's scope.
  - Its `--claim` already takes the session id as its value (`--claim SESSION_ID`).
  - `--beat` already requires `--session-id`.
  - Residual: `--set` without `--session-id` still writes without refreshing the heartbeat, as
    it does today.

### D6 — Install check roots, W3 (FR-10)

New module-level names in `h_mad_install_check.py`:

```python
AGENTS_SKILLS_ENV = "HMAD_AGENTS_SKILLS_DIR"
AGY_SKILLS_ENV = "HMAD_AGY_SKILLS_DIR"
AGY_INSTALLED_NAMES = ("h-mad", "handoff")
SIBLING_KINDS = ("NOT_SYMLINK", "DANGLING", "WRONG_CHECKOUT")

def default_host_roots(environ: Mapping[str, str] | None = None) -> tuple[str, str]:
    """(agents_dir, agy_dir) resolved at CALL time: the env var when present (even empty),
    else Path.home()/".agents"/"skills" and Path.home()/".gemini"/"config"/"skills"."""

def split_agy_root(lines: list[str], skills_dir: Path, installed: Iterable[str]
                   ) -> tuple[list[str], list[str]]:
    """Partition check_siblings(repo, skills_dir) output into (issues, details)."""
```

- **`check()` signature.** It becomes
  `check(skills_link, hook_link, repo=None, *, agents_skills_dir=None, agy_skills_dir=None,
  details=None)`. Its return type is unchanged: a list of issues.
- **The new roots.** They are checked only when `sibling_repo` is not `None`, which is the same
  derivation as today:
  - `agents_skills_dir` → `issues += check_siblings(sibling_repo, Path(agents_skills_dir))`;
  - `agy_skills_dir` → `lines = check_siblings(sibling_repo, Path(agy_skills_dir))`, then
    `split_agy_root`. The issues are appended, and `details.extend(sorted details)` runs when
    `details` is not `None`.
  - Issue order: the Claude root first, then the agents root, then the agy root.
- **`split_agy_root`.** For each checkout skill name `n` and kind `K`, a line counts as that pair
  when it starts with `f"SIBLING_{K}:{skills_dir / n} "`. The trailing space separates `h-mad`
  from any longer name.
  - If `n` is in `installed`, the line stays an issue unchanged.
  - Otherwise it becomes the detail `AGY_SIBLING_COLLISION:{skills_dir / n} kind={K}`.
  - A line that matches no `(n, K)` pair stays an **issue**, which fails closed.
  - `check_siblings` stays the only classifier, and its body is byte-identical. So are its four
    anchors, and `check()`'s `checkout.parent if checkout is not None else None` anchor.
- **`main()`.**
  - Both new options default to `None`, and a `None` value is filled from
    `default_host_roots()`. An explicit option always wins.
  - After the existing UNREADABLE branch, which stays unchanged, a second branch handles an
    empty-after-strip `--agents-skills-dir` or `--agy-skills-dir`, including one supplied through
    an empty env var. It prints `ERROR: --agents-skills-dir and --agy-skills-dir must name a path`
    to stderr, `INSTALL: UNREADABLE` to stdout, and one explanatory stdout line, then returns 2.
  - The verdict block is unchanged. The detail lines are printed after it, after `OK` on `PASS`
    and after the issue lines on `FAIL`.
- **Byte-identity with the new roots absent.** A root path that does not exist makes
  `check_siblings` find no link: every `link` is absent, so the loop `continue`s. It adds nothing,
  which is AC-10.2's second clause.
- **`repo == skills_dir`.** Today's short-circuit applies to the new roots too, because it lives
  inside `check_siblings`.

### D7 — Hermetic roots in `h-mad/tests/conftest.py` (FR-10, FR-12)

One fixture is appended; no existing line changes:

```python
@pytest.fixture(autouse=True)
def _hermetic_host_skill_roots(monkeypatch, tmp_path):
    monkeypatch.setenv("HMAD_AGENTS_SKILLS_DIR", str(tmp_path / "absent-agents-skills"))
    monkeypatch.setenv("HMAD_AGY_SKILLS_DIR", str(tmp_path / "absent-agy-skills"))
```

- It creates nothing under `tmp_path`, so tests that list `tmp_path` see what they saw before.
- Residual (plan): a subprocess started with an explicit `env=` that drops both variables and
  keeps the real `HOME` would read the real roots. Only review catches that.

### D8 — Probe sidecar `docs/03-analysis/probes/multi-host-runtime/` (plan Deliverables)

| File | Invocation | Prints | Reads |
|---|---|---|---|
| `calibrate.sh` | `calibrate.sh <sha>` | the spec FR-4 command verbatim with `<sha>`: per file `sort \| uniq -c`, then totals in occurrences and distinct tokens | `git show <sha>:<skill>/SKILL.md` |
| `seed.json` | data | the 22 spec seed entries in the D1 format | — |
| `seed_coverage.py` | `seed_coverage.py --sha <sha> --registry <path>` | hits per entry × skill, each flagged against the declaration; with `--branches`, every branch × declared-skill cell and every zero cell listed | `git show`; for `--branches`, it imports `expand_branches` from `h-mad/tests/host_parity.py` |
| `byte_identity.py` | `byte_identity.py --base <sha> --arm {budget,decision,install-a,install-b}` | `BYTE-IDENTITY: PASS arm=<a> cases=N`, `FAIL arm=<a> case=<name>` plus a diff, or `UNREADABLE reason=<r>` | a detached `git worktree add` of `<base>` in a temp dir |
| `smoke_assert.py` | `smoke_assert.py v111 --host H --log L` · `v112 --out O --record JSON --feature F` · `rehearse` | `PASS V-11.1` / `FAIL V-11.1 <why>`; `PASS V-11.2` / `FAIL V-11.2 <why>`; one line per rehearsal case, then `REHEARSAL: PASS n=N` / `FAIL` | the given files; `rehearsal/` fixtures |
| `rehearsal/` | data | hand-made logs in each host's observed shape (D10) | — |

- **Exit codes.** Each probe exits 0 on a verdict and 2 on unreadable input. Callers read the
  token.
- **Time bounds.** `byte_identity.py` bounds each run with `subprocess.run(timeout=…)`. No probe
  writes a `timeout <n>` command.
- **Worktree removal is verified.** `byte_identity.py` removes its worktree with
  `git worktree remove --force`. It then re-reads `git worktree list --porcelain` and prints
  `UNREADABLE reason=worktree_left` if the path is still listed (`invariants.base.md`
  §"Mutation verification").
- **When the per-branch reading is taken.** At 5c `host_parity.py` does not exist, so
  `seed_coverage.py` at `<base>` gives the per-entry reading only. Its `--branches` reading is
  taken at the end of strand 1. It still measures `<base>`, because both `SKILL.md` files are read
  through `git show <base>:…`, whatever the working tree holds.
- **Byte-identity arms.** They follow plan §Implementation Strategy exactly.
  - Budget cases:
    - OK in advisor mode;
    - DENY in advisor mode;
    - `--mode run` OK and HALT;
    - `--window 0`;
    - a non-existent `--transcript` with `HOME` pointed at an empty temp dir;
    - a transcript with no usage record.

    The JSONL record shape is the one `test_h_mad_context_budget.py`'s `_turn` helper writes.
  - Decision cases:
    - absent file;
    - unreadable file;
    - absent feature;
    - a live foreign owner, with and without `--session-id`;
    - halted;
    - complete;
    - `last_completed_phase` 4 and 1.

    Each budget and decision case runs with `HMAD_HOST` unset, and again with `claude`.
  - Install arm A: the `test_h_mad_install_check.py` shapes, namely healthy, stale copy, missing
    hook, split, dangling, absent link, sibling copy, sibling in another checkout, and empty path.
    Both env overrides point at absent paths.
  - Install arm B:
    - precondition: `test -L` on the four links, else `UNREADABLE reason=links_absent`;
    - B1: the same fixture argv set;
    - B2: `--skills-link ~/.claude/skills/h-mad --repo /Users/kimhawk/orca/skills`;
    - the closed-diff rule as in the plan, with the `AGY_SIBLING_COLLISION:` names taken from the
      plan P8 `comm -12` reading run inside the probe.

### D9 — Adapters (FR-2, FR-5, FR-6, FR-8, FR-9, FR-10)

**D9.1 Section inventory.** "new" means a new file or section. Headings are the locators the doc
tests use (D12).

| Adapter | Sections added (in this order, before any closing `## What does not change` / `## Safety invariants`) | Existing text changed |
|---|---|---|
| `h-mad/references/grok-runtime.md` (new) | `# grok runtime adapter`; `## Version and compatibility`; `## Package and project roots`; `## Install`; `## Project trust`; `## Hooks`; `## The TDD gate`; `## Author and reviewer roles`; `## Context budget and claims`; `## Memory index`; `## Construct mapping`; `## What does not change` | — |
| `h-mad/references/codex-runtime.md` | `## Install`; `## Context budget and claims`; `## Construct mapping` (after `## State and halt discipline`) | none; `### Trust boundary` belongs to `codex-tdd-gate-defects` |
| `h-mad/references/agy-runtime.md` | `## Install`; `## Context budget and claims`; `## Construct mapping` (before `## What does not change`) | the "typically `~/.gemini/config/skills/h-mad`" sentence and the install-check paragraph in `## Package and project roots` (below) |
| `handoff/references/grok-runtime.md` (new) | `# grok runtime adapter`; `## Version and compatibility`; `## Resolve the skill package`; `## grok tool mapping`; `## Mode routing`; `## Construct mapping`; `## Safety invariants` | — |
| `handoff/references/codex-runtime.md` | `## Construct mapping` (before `## Safety invariants`) | none |
| `handoff/references/agy-runtime.md` | `## Construct mapping` (before `## Safety invariants`) | the "typically `~/.gemini/config/skills/handoff`" sentence |

**D9.2 Required content, by section.** Each item names the tokens the doc test pins.

- **`## Version and compatibility`** (both grok files). It names:
  - the version `grok 1.0.41`;
  - `compat.claude.skills` (and, in the h-mad file, `compat.claude.hooks`) with their env
    toggles (F6);
  - the verification command `grok inspect`, section "Harness Compatibility" (F5);
  - that a newer grok at smoke time is recorded, not assumed (A1).
- **`## Package and project roots`** (h-mad grok). `HMAD_SKILL_ROOT` resolves from the loaded
  skill path. Today that path is `~/.claude/skills/h-mad`, through `compat.claude.skills`. Once
  the operator links it, `~/.agents/skills/h-mad` serves the same checkout (F4, F5).
- **`## Install`** (h-mad codex, agy, grok; AC-10.4):
  - codex and grok: `ln -s /path/to/checkout/h-mad ~/.agents/skills/h-mad` and the matching
    `handoff` line;
  - agy: the same two commands under `~/.gemini/config/skills/`;
  - each file: "an existing non-symlink at either path is an operator decision and is never
    overwritten";
  - codex and grok: "creating the link does not re-arm HemaSuite's codex TDD gate: its tracked
    `.codex/hooks.json` reads `{"hooks": {}}`";
  - each file names the check: `python3 "$HMAD_SKILL_ROOT/scripts/h_mad_install_check.py"`, and
    `--agents-skills-dir` or `--agy-skills-dir` respectively.

  The checkout is written as a placeholder path, never as a user-specific path, to keep the
  existing "never derive the package from a user-specific checkout" rule.
- **agy install-check paragraph rewording.** It keeps "do not run it as a Phase gate here", and it
  keeps the `SKILL_NOT_INSTALLED` explanation for the Claude link. It adds that
  `--agy-skills-dir` checks this host's own root. The "typically" sentences (plan P10) become:
  "the operator-installed link `~/.gemini/config/skills/<skill>` (§Install), when it exists".
- **`## Project trust`** (h-mad grok; F7). The global `~/.claude/settings.json` hooks need no
  trust. A project Claude hook is silently skipped until `/hooks-trust` or `--trust`.
- **`## Hooks`** (h-mad grok; F8, F9). It covers:
  - the camelCase payload (`toolInput`, `sessionId`), and the two event-name fields;
  - the matcher aliases;
  - `exit 2` is the deny, and any other non-zero exit fails open;
  - the default handler time limit (5 s for `PreToolUse`), after which the handler fails open.
  - The advisor-warn note (plan P15): `h-mad-advisor-warn.sh` runs as a global `PostToolUse` hook
    without `HMAD_HOST`, so any `CTXBUDGET` text it injects on grok is a Claude transcript's
    reading, and it is ignored.
  - The prose never writes the word `timeout` directly before a number (DP8).
- **`## The TDD gate`** (h-mad grok; AC-5.2). It carries the halt token
  `step5:grok_tdd_hook_unverified`, and it states that Phase 5 halts with that token until a grok
  refusal of a production write has been observed. The three reasons are written from the
  **`<base>` reading** of plan P5 and the sibling's recorded FR-0 branch (plan Risks):
  - Reason (ii) holds in every branch: grok's `toolInput` supplies none of the gate's read paths.
  - Reason (iii) holds in every branch: a handler time limit fails open.
  - Reason (i) takes the branch's wording.

  The doc test therefore pins `step5:grok_tdd_hook_unverified`, `toolInput`, `fail-open` and
  `pytest`. The reason-(i) wording is left to review, because it depends on a sibling measurement
  not yet taken.
- **`## Author and reviewer roles`** (h-mad grok; F2). It states:
  - `spawn_subagent` cannot select an agent by name;
  - the role travels as the text of `$HMAD_SKILL_ROOT/agents/<name>.md` in `prompt`;
  - results come back through `get_command_or_subagent_output`;
  - nesting is capped at one level;
  - no filesystem jail: diff `git status --short`, tracked and untracked, after each dispatch
    (NFR Security).
- **`## Context budget and claims`** (h-mad codex, agy, grok; FR-8, FR-9, AC-8.4, AC-9.3). It
  covers four points:
  - **Inline declaration.** `HMAD_HOST=<host> python3 "$HMAD_SKILL_ROOT/scripts/…"` goes on every
    h-mad script call. It is inline so that it does not depend on the shell keeping exports.
  - **The budget.** `CTXBUDGET: UNKNOWN reason=host_unsupported` is expected and never read as
    `OK`. The 80% run ceiling is unenforced on this host. The substitute is named:
    - grok: the operator's `/context` (`04-slash-commands.md`; interactive only, and not
      reachable by the model);
    - codex and agy: "none".
  - **The session id.**
    - grok: `GROK_SESSION_ID`, documented for hook processes only (F10), and used only once the
      live smoke has recorded it present in the orchestrator's shell;
    - codex and agy: no documented variable (F13, F14).
  - **The minted-id procedure.** One `python3 -c 'import uuid; print(uuid.uuid4())'` at
    bootstrap. The id is passed as the value of `--claim` and as `--session-id` on every `--beat`,
    `--set` and `--release`, and on every `h_mad_resume_decision.py` call. The failure mode: a
    session that loses its id sees its own claim as `owned_elsewhere` until the staleness window
    lapses, and never gets a false clear.
- **`## Memory index`** (h-mad grok; AC-5.6). grok's store is `~/.grok/memory/` (F12). Never
  point `h_mad_check_memory_index.py` at `~/.claude/projects` from a grok session.
- **`## grok tool mapping`** (handoff grok). The rung-1 task sink is `todo_write`, whose todo pane
  is user-visible (`Ctrl+T`). Delegation is `spawn_subagent`. The handoff package root is
  `HANDOFF_SKILL_ROOT`, resolved from the loaded skill path.
- **Text constraints on every adapter cell and paragraph:**
  - The codex adapters must not contain `Agent(subagent_type:`, `AskUserQuestion` or `TodoWrite`,
    and the handoff one must not contain `Skill(skill:` (AC-6.6). Mapping cells therefore name
    constructs by kebab id.
  - A pipe inside a cell is written `\|`.

**D9.3 Construct matrix (FR-2 rows).** `M` means `mapped` and `N` means `not-applicable`. Each
cell gives the status and the mapping gist, and the bracket names the evidence the `source` cell
cites.

| construct (skills) | codex | agy | grok |
|---|---|---|---|
| `subagent-call` (h) | M: `collaboration.spawn_agent`, `fork_turns: "none"`, agent file text in the prompt [codex binary strings `spawn_agent`, `fork_turns` (DP11)] | M: `define_subagent` then `invoke_subagent` [observed: `init.tools` of `plan-audit-v1-p2-agy.log`] | M: `spawn_subagent` with the agent file text in `prompt` [`16-subagents.md`] |
| `skill-call` (both) | M: the installed codex skill by name, loaded from `~/.agents/skills` (A2; V-11.1 decides) [A2] | M: the installed agy skill under `~/.gemini/config/skills` [agy docs `skills.md`] | M: the skill's slash command, e.g. `/handoff` [`08-skills.md`] |
| `advisor` (h) | N: substitutes `hmad-dispatch exec agy\|grok`, or `collaboration.spawn_agent` with `fork_turns: "all"` (AC-6.3) [DP11] | N: substitutes `hmad-dispatch exec codex\|grok`, or `define_subagent`/`invoke_subagent` with the review context in the prompt (AC-6.3) [observed agy tools] | N: no advisor tool (F1); a child does not inherit the transcript (F2); substitutes `hmad-dispatch exec codex\|agy\|grok` or `spawn_subagent` with a self-contained prompt (AC-5.3) [`01-getting-started.md`, `16-subagents.md`] |
| `send-message` (h) | N: no documented message-to-running-agent tool; dispatch a fresh author with the prior report path [DP11: no such string checked] | N: `send_message` is in agy's tool list, but its target semantics are undocumented in agy's docs dir; dispatch a fresh author [observed agy tools] | N: `send_subagent_message` is off by default (F3); continue with `spawn_subagent` `resume_from` [`16-subagents.md`] |
| `hook-event` (h) | M: codex hook events via `hooks/h-mad-codex-tdd-gate.py` in the active codex hooks file [observed: `hook: PreToolUse` in `h-mad/tests/fixtures/codex-text-8-exec.log`] | M: `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`; no `SessionStart` [agy docs `hooks.md`] | M: Claude hooks from `~/.claude/settings.json` run under `compat.claude.hooks`, with camelCase payloads and exit-2 deny (F7–F9) [`10-hooks.md`] |
| `session-id-env` (h) | N: no documented variable; minted id (FR-9) [F14] | N: no documented variable; minted id [F13] | M: `GROK_SESSION_ID` once the smoke records it in the shell, else a minted id (AC-5.5) [`10-hooks.md`] |
| `claude-config-dir` (h) | N: the check it feeds reads Claude's settings scope; codex's config is its own [DP11] | N: agy's config root is `~/.gemini/config` [agy docs `hooks.md`] | N: grok reads `~/.claude/settings.json` by fixed path; honouring the variable is undocumented [`10-hooks.md`] |
| `claude-md` (both) | M: `AGENTS.md` project instructions [DP11: string `AGENTS.md`] | M: workspace rules under `.agents/` [agy docs `rules.md`] | M: grok reads `Claude.md`/`CLAUDE.md`/`AGENTS.md` [`12-project-rules.md`] |
| `claude-skills-dir` (both) | M: `$HMAD_SKILL_ROOT` / `$HANDOFF_SKILL_ROOT` from the loaded path, `~/.agents/skills/<skill>` [A2] | M: the same roots under `~/.gemini/config/skills/<skill>` [agy docs `skills.md`] | M: loaded straight from `~/.claude/skills` via `compat.claude.skills` [`grok inspect`] |
| `claude-agents-dir` (h) | N: no agent registry; the file text travels in the spawn prompt [DP11] | N: no file-based agent registry [observed agy tools] | N: grok lists `~/.claude/agents` but cannot select one by name (F2) [`16-subagents.md`] |
| `claude-hooks-dir` (h) | N: codex's gate is `hooks/h-mad-codex-tdd-gate.py`, wired from its hooks file [observed codex log] | N: hooks live in `hooks.json` [agy docs `hooks.md`] | M: Claude hook scripts run from their Claude paths under compat (F7) [`10-hooks.md`] |
| `claude-settings` (both) | N: codex hooks live in a hooks file; HemaSuite's is `.codex/hooks.json` [DP11: string `hooks.json`] | N: `~/.gemini/config/hooks.json` [agy docs `hooks.md`] | M (h-mad): read under compat (F7) [`10-hooks.md`]; N (handoff): `todo_write` needs no settings opt-in [`01-getting-started.md`] |
| `claude-handoffs-dir` (both) | M: unchanged; a plain file store every host reads and writes through its shell [observed: `test -f ~/.claude/handoffs/INDEX.md`] | M: unchanged [same] | M: unchanged [observed: same] |
| `claude-projects-store` (h) | N: no documented codex memory store; never point the memory-index check at `~/.claude/projects` [DP11] | N: `~/.gemini/config/projects/*.json` (existing §Memory index) [observed] | N: `~/.grok/memory/` (AC-5.6) [`13-memory.md`] |
| `claude-home-bare` (h) | N: Claude's home; nothing is relinked [DP11] | N: Claude's home; agy's root is `~/.gemini/config` [agy docs `hooks.md`] | N: grok's home is `~/.grok` [`05-configuration.md`] |
| `session-reset-command` (both) | M: codex `/new` or `/compact` [DP11: strings `/new`, `/compact`] | N: no documented reset command; start a fresh `agy` session [agy docs dir] | M: `/new` (alias `/clear`) and `/compact` [`04-slash-commands.md`] |
| `skill-slash-invocation` (both) | M: invoke the skill by name (A2) [A2] | M: invoke the installed agy skill by name [agy docs `skills.md`] | M: `/h-mad`, `/handoff` [observed: `available_commands` in the sibling probe log (DP5)] |
| `task-tools` (hand.) | N: no evidenced rung 1 (A3: `update_plan` is a lead); rung 2 `.omc/notepad.md`, then rung 3 inline (AC-6.4) [A3] | N: `manage_task` is a background-task manager, not a checklist; rung 2, then 3 (AC-6.4) [observed agy tools] | M: `todo_write`, user-visible pane (AC-5.4) [`01-getting-started.md`] |
| `tool-search` (hand.) | N: no deferred todo tool to load [A3] | N: [observed agy tools] | N: `todo_write` is built in, never deferred [`01-getting-started.md`] |
| `skill-root-env` (hand.) | M: `HANDOFF_SKILL_ROOT` from the loaded path [existing adapter rule; A2] | M: `HANDOFF_SKILL_ROOT` [agy docs `skills.md`] | M: `HANDOFF_SKILL_ROOT` [`08-skills.md`] |
| `todo-tools-optin` (hand.) | N: [A3] | N: [observed agy tools] | N: `todo_write` needs no opt-in [`01-getting-started.md`] |
| `claude-homunculus` (hand.) | M: unchanged; an optional file read when present [observed: `test -f`] | M: unchanged [same] | M: unchanged [observed: same] |

- **Row counts.** The matrix is derived from the registry: 17 h-mad rows per h-mad adapter and 12
  handoff rows per handoff adapter, 87 rows in all. If the AC-4.6 re-derivation changes the entry
  set, the matrix follows it, and no count in this document is carried past that record.
- **Codex evidence is the weakest.** This tree has no codex host document (F14), and a binary
  string is a lead, not documentation (A3's own rule). Codex rows marked `[DP11]` or `[A2]`
  therefore rest on the existing adapter's mappings and on V-11.1. Each such `source` cell says
  which one.
- **grok `source` cells** follow AC-5.7's format: a chapter file matching
  `\b\d\d-[a-z-]+\.md\b`, the literal `grok inspect`, or a cell beginning `observed:`.

### D10 — Live smoke assertions (FR-11; supersedes items 1–3)

`smoke_assert.py v111 --host H --log L` reads the log in H's shape (DP6) and reduces it to an
ordered list of **input events**, each a `(tool, input_text)` pair:

| host | log shape | event = | input_text = |
|---|---|---|---|
| grok | `streaming-json` NDJSON | each `{"type":"tool_call"}` | `toolName` + `json.dumps(rawInput, sort_keys=True)` |
| agy | NDJSON `{"event":"step_update","step_update":{…}}` | the first line per `step_index` with `step_type == "tool"` | `tool_name` + `json.dumps(tool_info.parameters, sort_keys=True)` |
| codex | text | the line after each line equal to `exec` | that command line |

The verdict is decided in this order:
1. **Adapter read.** `a` is the first event whose `input_text` contains `<H>-runtime.md`. If there
   is none: `FAIL V-11.1 no adapter read`.
2. **Script run.** `s` is the first event whose tool is the host's shell tool and whose
   `input_text` matches `h_mad_[a-z0-9_]+\.py|hmad-dispatch\b`. The shell tools are:
   - grok: `run_terminal_command`;
   - agy: `run_command`;
   - codex: every exec event.

   If `s` exists and `s < a`: `FAIL V-11.1 a script ran before the adapter was read`.
3. **Skill loaded.** For grok, some `available_commands` event's `commands[].name` must include
   `h-mad`, else `FAIL V-11.1 grok did not list h-mad`. For codex and agy, some event's
   `input_text` must name `h-mad/SKILL.md`, else `FAIL V-11.1 no SKILL.md load`.
4. Otherwise `PASS V-11.1`.

- **Residuals.**
  - A host that reads the adapter through a glob such as `references/*.md` fails, which is the
    conservative direction.
  - A codex or agy host that loads `SKILL.md` without a tool call naming it (for example,
    injected by the host's own skill loader, a shape no committed log shows) fails step 3. The
    first smoke on that host then halts to the operator. Widening step 3 to the observed shape is
    a design change with its own rehearsal case, never an in-place edit during Phase 7. That is a
    halt, never a pass.

`v112` is the plan's `v112`, unchanged in logic, moved into Python.

**Rehearsal cases.** They are committed under `rehearsal/` and run by `smoke_assert.py rehearse`
in Phase 6. Each case prints its verdict, and the Phase-6 document records them all.
- For each host (codex, agy, grok):
  - R1: adapter read, then a script run → `PASS`;
  - R2: a script run, then the adapter read → `FAIL`;
  - R3: no adapter read → `FAIL`;
  - R4: a `SKILL.md` read whose **output** mentions `h_mad_x.py`, then the adapter read, then a
    script run → `PASS`. This is the case that kills the text-matching form.
- grok only: R5, no `available_commands` naming `h-mad` → `FAIL`.
- `v112`: the plan's four cases.
- Replay on real artifacts (`invariants.base.md` §"Incident replay"): `v111` over the three
  committed real logs, which are the sibling grok probe log, the agy log and
  `codex-text-8-exec.log`. None of them is an h-mad status run, so each must print
  `FAIL V-11.1 no adapter read`, and must not crash.

The rehearsal fixtures are hand-made in the shapes those real logs show. A rehearsal case that does
not print its expected verdict blocks 7f. If `smoke_assert.py` changes after Phase 6, the
rehearsal is re-run, and the smoke record states that.

**Smoke script delta.** The plan's script is used with these changes:
- The `v111()`/`v112()` shell definitions are removed.
- Part 2's two calls become:

  ```bash
  P="$REPO/docs/03-analysis/probes/multi-host-runtime/smoke_assert.py"
  r=$(python3 "$P" v112 --out "$S/out" --record "$B_REC" --feature "$F"); test "$r" = "PASS V-11.2" || stop "$r"
  r=$(python3 "$P" v111 --host "$H" --log "$S/log"); test "$r" = "PASS V-11.1" || stop "$r"
  ```
- Part 1 gains `test -f "$P" || { echo "HALT smoke_assert.py absent from main"; exit 1; }`.

Every other line is as the plan wrote it: the preconditions, `recover`, the pinned prompt, and the
`AH` H1 read. The `AH` value is still used by the prompt-names-the-adapter precondition.

### D11 — `SKILL.md` edits (FR-7, AC-9.4)

**The `## Host runtime` sections.** In each file, located by `find_heading(text, "## Host
runtime")`, the first two sentences are replaced.

In h-mad:

> This package supports Claude Code, OpenAI Codex, the Antigravity CLI (`agy`) and the grok CLI
> (`grok`). In Codex, read [references/codex-runtime.md](references/codex-runtime.md) before
> bootstrap; in agy, read [references/agy-runtime.md](references/agy-runtime.md); in grok, read
> [references/grok-runtime.md](references/grok-runtime.md) before bootstrap.

In handoff, the same text, with "before acting" in place of "before bootstrap".

Everything else in both sections is byte-identical, including the "Adapt a new host by adding an
adapter beside these, never by rewriting the Claude spelling" rule. The new text has no A1 to A4
hit (FR-4 re-run, AC-7.2).

**The `cannot_judge` row.** The row is located in `## Decision routing (for `/h-mad
"<feature>"`)` by its first cell `` `cannot_judge` ``. One sentence is appended at the end of its
second cell, before the closing ` |`:

> **Second cause:** a declared or unknown non-Claude host (`HMAD_HOST` set to anything other than
> empty or `claude`) called without `--session-id` — the oracle cannot check ownership, so it
> refuses to route; pass the session id your adapter's §"Context budget and claims" names, do not
> repair the file.

- The row's opening text, `` | `cannot_judge` | The state file EXISTS and could not be read ``,
  is kept byte-identical, because it is `resume_decision_cannot_judge.json`'s
  `the-token-leaves-the-decision-table` anchor.
- The appended sentence has no catch-all hit.

### D12 — Doc tests `h-mad/tests/test_host_runtime_docs.py`

- **Locating.** Every test locates its section with `h_mad_doc_block_exec.find_heading(text,
  "<full heading>")` and bounds it with `fence_aware_end`. An absent or doubled heading fails with
  the heading named; nothing is skipped.
- **Discrimination.** Tokens are asserted **inside the located section or table row only**, so
  nearby prose cannot satisfy them (`invariants.base.md` §"Test discrimination").
- **Rows.** Table rows are read with `host_parity`'s table parser.

The pinned tokens, by AC:

| AC | file(s) · locator | asserted |
|---|---|---|
| AC-2.3, AC-5.3, AC-6.3 | 3 h-mad adapters · `advisor` row | status `not-applicable`; mapping contains `hmad-dispatch exec` and, per host, `collaboration.spawn_agent` + `fork_turns` (codex), `invoke_subagent` (agy), `spawn_subagent` (grok) |
| AC-2.4, AC-5.4, AC-6.4 | 3 handoff adapters · `task-tools` row | grok `mapped` + `todo_write` + `Ctrl+T`; agy `not-applicable` + `manage_task` + `.omc/notepad.md`; codex `not-applicable` + `.omc/notepad.md` + `update_plan` (as a lead) |
| AC-2.5, AC-5.5, AC-6.5, AC-9.3 | 3 h-mad adapters · `session-id-env` row | all: `uuid.uuid4()` and `owned_elsewhere`; grok also `GROK_SESSION_ID` and `hook processes` |
| AC-5.1 | both grok files · `## Version and compatibility` | `1.0.41`, `compat.claude.skills`; h-mad also `compat.claude.hooks` |
| AC-5.2 | h-mad grok · `## The TDD gate` | `step5:grok_tdd_hook_unverified`, `toolInput`, `fail-open`, `pytest` |
| AC-5.6 | h-mad grok · `claude-projects-store` row | `not-applicable`, `~/.grok/memory`, `h_mad_check_memory_index.py` |
| AC-5.7 | both grok tables · every `source` cell | matches `\b\d\d-[a-z-]+\.md\b`, or contains `grok inspect`, or starts `observed:` |
| AC-7.1, AC-7.3 | both `SKILL.md` · `## Host runtime` | contains all three `references/<host>-runtime.md` paths; a renamed or doubled heading fails loudly |
| AC-8.4 | 3 h-mad adapters · `## Context budget and claims` | `HMAD_HOST=<host>`, `CTXBUDGET: UNKNOWN`, `80%`, and `/context` (grok) or `none` (codex, agy) |
| AC-9.4 | h-mad `SKILL.md` · `cannot_judge` row in `## Decision routing …` | `HMAD_HOST` and `--session-id` |
| AC-10.4 | h-mad codex, grok · `## Install` | `~/.agents/skills/h-mad`, `~/.agents/skills/handoff`, `ln -s`, `never overwritten`, `.codex/hooks.json`, `does not re-arm` |
| AC-10.4 | h-mad agy · `## Install` | `~/.gemini/config/skills/h-mad`, `~/.gemini/config/skills/handoff`, `ln -s`, `never overwritten` |
| plan P15 note | h-mad grok · `## Hooks` | `h-mad-advisor-warn.sh`, `CTXBUDGET`, `ignore` |

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| Construct registry | `h-mad/references/host-constructs.json` | new | FR-1 (D1) |
| Parity checker | `h-mad/tests/host_parity.py` | new (not collected) | FR-3, FR-4 (D2) |
| Parity tests | `h-mad/tests/test_host_construct_parity.py` | new | FR-1, FR-3, FR-4 |
| Host classifier | `h-mad/scripts/h_mad_host.py` | new | FR-8, FR-9 (D3) |
| Budget host check | `h-mad/scripts/h_mad_context_budget.py` | modify | FR-8 (D4, W1) |
| Oracle host check | `h-mad/scripts/h_mad_resume_decision.py` | modify | FR-9 (D5, W2) |
| Install roots | `h-mad/scripts/h_mad_install_check.py` | modify | FR-10 (D6, W3) |
| Hermetic roots | `h-mad/tests/conftest.py` | modify (append) | FR-10, FR-12 (D7) |
| Host tests | `h-mad/tests/test_h_mad_host_declaration.py` | new | FR-8, FR-9 |
| Install root tests | `h-mad/tests/test_h_mad_install_check_roots.py` | new | FR-10 |
| Doc tests | `h-mad/tests/test_host_runtime_docs.py` | new | FR-5–FR-10 (D12) |
| Mutation specs | `h-mad/tests/mutation-specs/host_parity.json`, `host_declaration.json`, `install_check_roots.json` | new | Success Criteria |
| grok adapters | `h-mad/references/grok-runtime.md`, `handoff/references/grok-runtime.md` | new | FR-2, FR-5, FR-8–FR-10 (D9) |
| codex/agy adapters | `{h-mad,handoff}/references/{codex,agy}-runtime.md` | modify | FR-2, FR-6, FR-8–FR-10 (D9) |
| Routing | `h-mad/SKILL.md`, `handoff/SKILL.md` | modify | FR-7, AC-9.4 (D11) |
| Probe sidecar | `docs/03-analysis/probes/multi-host-runtime/{calibrate.sh,seed.json,seed_coverage.py,byte_identity.py,smoke_assert.py,rehearsal/}` | new | FR-1, FR-4, FR-11, FR-12 (D8, D10) |
| Phase-6 document | `docs/03-analysis/multi-host-runtime.analysis.md` | new | AC-4.5, AC-4.6, AC-6.1, rehearsal, byte-identity |
| Live-smoke record | `docs/archive/<YYYY-MM>/multi-host-runtime/multi-host-runtime.live-smoke.md` | new | FR-11 |

Deliberately untouched (plan): `h-mad/hooks/h-mad-tdd-gate.sh`,
`h-mad/hooks/h-mad-codex-tdd-gate.py`, `h-mad/hooks/h-mad-advisor-warn.sh`,
`h-mad/scripts/hmad-dispatch.sh`, `h-mad/references/agent-substrate.md`, the three existing
mutation specs, and `check_siblings`' body.

## Implementation Order

1. **Before the design audit** (plan Next Steps): commit `calibrate.sh`, `seed.json` and
   `seed_coverage.py` (per-entry mode). They need no feature code.
2. **5c** (plan "Rebase, then baseline"):
   - rebase;
   - record `<base>`;
   - run `calibrate.sh <base>` and `seed_coverage.py --sha <base> --registry seed.json`;
   - re-run P4, P5, P6, P9 and P15, and the suite baseline;
   - run `--check-anchors` on the three existing specs;
   - take the AC-6.1 gap table from `git show <base>:<adapter>`;
   - run the four-link gate;
   - write the AC-4.6 record.
3. **Strand 1.**
   - First, `test_host_construct_parity.py`, RED. The registry node is RED with
     `REGISTRY_UNREADABLE reason=missing_file`. Each adapter node is RED on its vacuity guard
     (§Test Strategy), because no adapter stage ran.
   - Then `host_parity.py`, then the registry.
   - Registry node GREEN; adapter nodes RED on `TABLE_MISSING reason=no_heading`.
   - Take the `seed_coverage.py --branches` reading at `<base>`.
4. **Strand 2** (three independent leaves):
   - `h_mad_host.py`, then the D4 and D5 wiring, with `test_h_mad_host_declaration.py` RED first;
   - `h_mad_install_check.py` D6 with `conftest.py` D7, with `test_h_mad_install_check_roots.py`
     RED first;
   - after each leaf, run `--check-anchors` on the existing specs.
5. **Strand 3.** One adapter at a time, in the order h-mad codex, h-mad agy, h-mad grok, handoff
   codex, handoff agy, handoff grok. Each adapter's live node and its D12 doc tests go from RED to
   GREEN.
6. **Strand 4.** The two D11 edits to the `SKILL.md` files, then the FR-4 re-run (AC-7.2) and
   `--check-anchors`.
7. **Mutation specs.** The three new specs, run to `ALL_CAUGHT`, with the W1–W3 wire-scoped
   reverts and force-fires.
8. **Sidecar.** `byte_identity.py` and `smoke_assert.py` plus `rehearsal/`.
9. **Phase 6.**
   - `byte_identity.py` over all four arms;
   - `smoke_assert.py rehearse`;
   - the calibration re-run at 5g;
   - the analysis document.
10. **Phase 7.** The plan's sequence. The smoke uses §D10's delta.

## Data Model / Schema Changes

- **Registry JSON** (`host-constructs.json`): `{"constructs": [{"id": str, "pattern": str,
  "skills": list[str], "description": str}, …]}`, with the constraints in D2.2.
- **Adapter table:** `| construct | status | mapping | source |`. `status` is one of `mapped` or
  `not-applicable`.
- **Failure line:**

  ```text
  PARITY <KIND> file=<path> id=<id|-> [reason=<r>] [token=<text>]
  ```

  The per-kind field rules are the plan's.
- **Environment variables:**
  - `HMAD_HOST`: exact values `claude`, `codex`, `agy` or `grok`. Unset or `""` means Claude.
  - `HMAD_AGENTS_SKILLS_DIR` and `HMAD_AGY_SKILLS_DIR`: paths. When present, even empty, they
    replace the option default.
- **New stdout tokens:**
  - `CTXBUDGET: UNKNOWN reason=host_unsupported host=<codex|agy|grok>`;
  - `CTXBUDGET: UNKNOWN reason=unknown_host host=<json string>`;
  - `AGY_SIBLING_COLLISION:<link> kind=<NOT_SYMLINK|DANGLING|WRONG_CHECKOUT>`;
  - `BYTE-IDENTITY: …`, `PASS|FAIL V-11.1|V-11.2 …`, `REHEARSAL: …` (probes).
- **Smoke line** (the plan's):
  `HMAD-STATUS feature=<f> last_completed_phase=<json> halt_reason=<json>`.

## API / Interface Changes

- `h_mad_host.classify_host(environ: Mapping[str, str] | None = None) -> tuple[str, str | None]`.
  It is new.
- `h_mad_context_budget.main(argv=None) -> int`. Its signature is unchanged. It has two new early
  returns (exit 2).
- `h_mad_resume_decision.decide(state_file, feature, session_id=None, now=None) -> str`. Its
  signature is unchanged. It has a new first statement. A new function,
  `_host_verdict(session_id) -> str | None`, is added.
- `h_mad_install_check`:
  - `check(skills_link, hook_link, repo=None, *, agents_skills_dir: str | Path | None = None,
    agy_skills_dir: str | Path | None = None, details: list[str] | None = None) -> list[str]`;
  - `default_host_roots(environ=None) -> tuple[str, str]`;
  - `split_agy_root(lines, skills_dir, installed) -> tuple[list[str], list[str]]`;
  - CLI `--agents-skills-dir PATH` and `--agy-skills-dir PATH`, whose defaults come from
    `default_host_roots()` at call time.
- `host_parity` (test-side): as in D2.1.
- Probe CLIs: as in D8.

## Error Handling Strategy

- **Verdicts are stdout tokens with exit 0; exit 2 means no verdict exists**
  (`invariants.base.md` §"Audit-gate signal discipline"):
  - `CTXBUDGET: UNKNOWN …` exits 2, as the three existing reasons do;
  - `INSTALL: FAIL` exits 0, and `INSTALL: UNREADABLE` exits 2;
  - `cannot_judge` is printed with exit 0, like every oracle token.
- **Callers read the token, never `$?`.** That covers the smoke script, rehearsal, byte-identity
  and the harness.
- **Parity failures** are returned as data by `check()` (`ParityResult.failures`). The live nodes
  assert that list is empty
  and print every line on failure. Only harness faults raise (an unreadable `SKILL.md`,
  `UnsupportedPattern`), and they surface as test errors.
- **Fail-closed choices:**
  - an unattributable `check_siblings` line under the agy root stays an issue;
  - an unknown `HMAD_HOST` makes the oracle refuse to route;
  - an unobserved host log shape fails V-11.1;
  - a probe that cannot remove its worktree prints `UNREADABLE`.

## Test Strategy

- **Unit, in process.** These run with no subprocess:
  - `host_parity.check` over `tmp_path` fixtures;
  - `classify_host`, `decide()`, `check()`, `split_agy_root` and `default_host_roots`.
- **CLI, subprocess.**
  - The budget and install-check CLIs, which cover AC-8.1, AC-8.2, AC-10.3 and AC-10.5, plus the
    override control.
  - `h_mad_resume_decision.py` via `main()`, one fixture per host, to pin that `main` reaches
    `decide()` with the environment intact.
- **Vacuity guards.**
  - **Adapter nodes.** Each live adapter node first asserts that `ParityResult.stages` contains
    `"adapter"` (D2.1), so this is checked directly rather than inferred from an empty failure
    list. A node whose adapter stage did not run fails with "registry unreadable; adapter not
    checked". Without this guard, rule (a) would turn every adapter node GREEN whenever the
    registry was broken.
  - **The registry node** also fails on any line whose `file=` names none of the nine files.
- **Controls whose properties are executed, not asserted:**
  - the clean baseline yields `[]`;
  - the stubbed-`PATH` AC-3.5 run carries a positive control: the same stubs, invoked on purpose
    through `subprocess.run(["grok"])`, write their marker;
  - the expander refuses `(?:a|b)+`, `a{2}` and `(a`;
  - the default-root control calls `default_host_roots({})` and compares it with
    `Path.home()`-derived paths, and never runs the CLI.
- **Mutation.** Every guard is mutation-verified with `h_mad_mutation_harness.py` (§Test Plan),
  and scored on its `MUTATION:` token.
- **Wires.** W1–W3 get a wire-scoped revert and a force-fire (plan §Connection enforcement).

## Test Plan

**`test_host_construct_parity.py`:**
- `test_live_registry_and_skill_files_are_clean`;
- `test_live_adapter_is_clean[<each of the six adapter paths>]`;
- `test_clean_baseline_yields_nothing`;
- `test_kind_fixture_reports_exactly_its_pair[<42 case ids>]`;
- `test_suppression_rule_leaves_one_pair[a|b|c|d|e]`;
- `test_absent_adapter_file_reads_as_no_heading`;
- `test_catch_all_axis_alone_reports_its_fixture[A1|A2|A3|A4-tilde|A4-home|A4-home-braced]`;
- `test_removing_an_axis_or_branch_clears_its_fixture[A1|A2|A3|A4|A4-tilde|A4-home|A4-home-braced]`;
- `test_exclusion_suffix_hides_its_fixture[<6>]` and
  `test_removed_exclusion_suffix_reports_its_fixture[<6>]`;
- `test_unregistered_teamcreate_then_registered_passes`;
- `test_registry_holds_every_seed_id`;
- `test_registry_branch_samples[<22 ids>]`;
- `test_branch_expander_refuses_unsupported_shapes`;
- `test_gate_runs_no_host_cli`, `test_host_cli_stub_control_fires` and
  `test_host_parity_has_no_direct_launcher_import`.

**`test_h_mad_host_declaration.py`:**
- `test_classify_host[<unset|""|claude|codex|agy|grok|zzz|Grok| grok>]`;
- `test_budget_and_decide_agree[<the same nine>]`;
- `test_budget_host_unsupported_valid_transcript[codex|agy|grok]` (a);
- `test_budget_host_check_precedes_transcript_lookup[…]` (b);
- `test_budget_host_check_precedes_usage_read[…]` (c);
- `test_budget_host_check_precedes_window_check[…]` (d);
- `test_budget_unknown_host[zzz|Grok| grok]`;
- `test_budget_unknown_host_newline_value_prints_one_line`;
- `test_decide_cannot_judge_without_session_id[<host> × <live-foreign-owner|no-owner|absent-file|unreadable-file|absent-feature>]`;
- `test_decide_routes_normally_with_session_id[codex|agy|grok]`, the control that kills an
  unconditional `cannot_judge`;
- `test_decide_unknown_host_without_session_id`;
- `test_resume_decision_cli_under_grok`.

**`test_h_mad_install_check_roots.py`:**
- `test_agents_root[<correct|copy|dangling|other-checkout|absent>]` (AC-10.1);
- `test_empty_root_option_is_unreadable[agents|agy]` (AC-10.3);
- `test_agy_root_cell[<12 AC-10.5 cells>]`;
- `test_claude_root_debugger_copy_still_fails` (AC-10.6);
- `test_absent_roots_add_no_line`;
- `test_env_override_is_read`;
- `test_default_roots_resolve_to_documented_paths`;
- `test_detail_lines_sorted_and_after_verdict`;
- `test_check_without_root_keywords_reads_no_new_root`;
- `test_unattributable_sibling_line_stays_an_issue`.

**`test_host_runtime_docs.py`:** one test per row of D12's table.

**Mutation specs.** Each is scored on `MUTATION: ALL_CAUGHT`, with anchors confirmed by
`--check-anchors`:

| Spec | Mutation classes (each one mutant per member) | Killed by |
|---|---|---|
| `host_parity.json` | each disjunct's detection disabled alone (42, incl. splits); each suppression rule (a)–(e) removed; each axis dropped from `CATCH_ALL_AXES`; each `A4_BRANCHES` entry dropped; each suffix replaced by `.*`; one expander alternative dropped; `CELL_EMPTY`'s case fold removed; the table search made fence-blind (a `^\|` scan over the raw section) | its own fixture; the sample-count assertion; the mixed-case fixtures; a fixture holding a pipe table inside a fence before the real one |
| `host_declaration.json` | `classify_host` given `.strip()`, `.lower()`, or `""`→unknown; W1 check moved after the transcript lookup, the usage read, the `--window` check; W2 check moved after the state read, after the feature lookup; `_host_verdict` ignoring `session_id`; the `cannot_judge` branch removed | fixtures ` grok`, `Grok`, `""`; (b), (c), (d); absent-file and absent-feature fixtures; `test_decide_routes_normally_with_session_id`; AC-9.1 |
| `install_check_roots.json` | the agy name split inverted; the split applied to the Claude root; the env override read dropped; the trailing space removed from `split_agy_root`'s prefix; detail lines printed before the verdict | AC-10.5 cells; AC-10.6; the override control; a fixture with skills `h-mad` and `h-mad-x`; the ordering test |

**Commands:**
- `python3 -m pytest -q h-mad/tests handoff/tests handoff/scripts`, the full coupled suite
  (AC-12.1), run with the interpreter the plan pins;
- `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json`;
- the plan's node-id floor and append-only `numstat` check.

## Invariant Compliance

**Base invariants (`h-mad/invariants.base.md`):**
- **Audit-gate signal discipline.** Complies. Every new verdict is a stdout token with exit 0,
  and exit 2 is reserved for no-verdict states, which the existing `UNKNOWN` and `UNREADABLE`
  precedents already use.
- **Single-source contract.** Complies:
  - host classification is one function;
  - agy-root classification reuses `check_siblings`;
  - the adapter table parser is shared by the gate and the doc tests;
  - `v111` and `v112` are one file used by the smoke and the rehearsal.
- **Standalone / no plugin dependency.** Complies. Only stdlib is used, and test-side reads of
  sibling-skill files have precedent (spec A5).
- **No new external dependency.** Complies. No test or script invokes codex, agy or grok. The
  smoke reaches them only through `hmad-dispatch exec`, and AC-3.5 is enforced by the stubbed
  `PATH`.
- **Portable time bounds.** Complies. There is no `timeout <n>` form. Probes bound runs with
  `subprocess.run(timeout=…)`, and the smoke with `hmad-dispatch exec --timeout`. The adapter
  prose avoids the scanned shape (DP8).
- **Doc-template superset compliance.** Complies. This document carries every Phase-4 template
  section and passes `h_mad_doc_shape_check.py`.
- **Operator-override preservation and backward compatibility.** Not touched: no audit gate
  changes.
- **Marker discipline.** Complies. The halts this design adds (`step5:grok_tdd_hook_unverified`,
  the smoke `HALT`s) go through the ordinary halt protocol, which emits `[H-MAD]` markers.
- **Mutation verification.** Complies. The byte-identity probe re-reads `git worktree list` after
  its removal, and the smoke's `recover` re-reads `HEAD^{tree}` (plan).
- **Test discrimination.** Complies:
  - every guard has a mutant and a named killing test;
  - vacuity guards on the adapter nodes;
  - positive controls on the stubbed `PATH`, the env override and the clean baseline;
  - the doc tests assert inside located sections only.
- **Guard narrowing.** Not applicable. No guard is loosened. The agy root's non-failing
  collision is a new root's rule, not a relaxation of `~/.claude/skills`, and that is pinned by
  AC-10.6.
- **Connection enforcement.** Complies. W1–W3 each get a wire-scoped revert and a force-fire, and
  the ordering mutants are killed by fixtures (b)–(d) and by the absent-file and absent-feature
  fixtures.
- **Incident replay.** Complies:
  - `v111` is replayed on the three committed real host logs;
  - the calibration is re-run on the real `SKILL.md` files at `<base>` and 5g;
  - the byte-identity arm B is run on the real install.
- **Assumption verification and behavioural premises.** Complies. See §"Verified premises
  (design-level)": every load-bearing assumption was executed, with its command.
- **Counts a dispatch reports.** Complies. Every count here was re-derived by the command beside
  it.
- **Wrapper–runtime reconciliation.** Not applicable. No wrapper verb is added, and `exec grok`
  is the sibling's.
- **Regression provenance.** Complies. No existing test is edited. The conftest change is an
  append.
- **Both halves of a doc change.** Complies. The agy "typically" sentence and the install-check
  paragraph are replaced by text naming the new install path and check. Nothing is removed without
  its replacement.
- **Reimplementation parity.** Not applicable.

**Project invariants (`.h-mad/invariants.md`):**
- **Skill self-containment.** Complies. The registry and checker are read only by `h-mad` tests.
  `handoff` gains no runtime read of `h-mad`. Adapter paths under `~/.agents` and `~/.gemini` are
  documented install locations of the same kind the rule already allows for `~/.claude`.
- **Skill manifest integrity.** Complies. Both `SKILL.md` contracts are updated where behaviour
  changes: routing names grok, and the `cannot_judge` row names its second cause. Frontmatter is
  untouched.

## Verified premises (design-level)

Each premise was run at `6478b8b5`, on the main checkout with a clean `h-mad`/`handoff` tree.
`git diff --name-only 2f262f8a 6478b8b5 -- h-mad handoff | wc -l` → 0 files, so plan v1.2's tree
premises stand. `main` advanced to `dfd5f02e` while this document was written, and
`git diff --name-only 6478b8b5 dfd5f02e -- h-mad handoff | wc -l` → 0 files, so every reading below
also holds there.

- **DP1 — calibration.** `git diff --stat 6494b3c HEAD -- h-mad/SKILL.md handoff/SKILL.md` → no
  output. The spec FR-4 command at `HEAD`, piped to `wc -l` and to `sort -u | wc -l`, gives:
  - `h-mad/SKILL.md`: 122 occurrences, 13 distinct tokens;
  - `handoff/SKILL.md`: 71 occurrences, 12 distinct tokens.

  **Moves** with either `SKILL.md`. It is re-derived by `calibrate.sh <base>`.
- **DP2 — the D2.7 grammar reproduces plan P2b.** A scratch script ran exactly D2.7's grammar over
  the spec seed table, with `H` expanded and `\|` un-escaped, using `re.finditer` on
  `git show 6478b8b5:<skill>/SKILL.md`. It was deleted after the run. The reading:
  - 22 entries: 17 declare `h-mad` and 12 declare `handoff`;
  - 0 entries whose presence contradicts their declaration;
  - 13 entries carry branches, with 45 branches between them, and 54 branches across all 22
    entries;
  - 61 branch × declared-skill cells, of which 25 are zero;
  - 14 branches have 0 occurrences in every skill that declares them.

  **Moves** with either `SKILL.md` and with any registry change. It is re-derived by
  `seed_coverage.py --branches`.
- **DP3 — existing anchors.** `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors
  h-mad/tests/mutation-specs/{context_budget,install_check_siblings,resume_decision_cannot_judge}.json`
  → `ANCHORS: ANCHORS_OK specs=3 mutations=17 ok=17`. By spec that is 9 + 5 + 3 mutations. By target `file`, it is 9 in
  `h_mad_context_budget.py`, 5 in `h_mad_install_check.py`, 2 in `h_mad_resume_decision.py` and 1
  in `SKILL.md` (a JSON walk over the three specs' `mutations[].file`).
  `resume_decision_cannot_judge.json` anchors `        return "cannot_judge"` and, in
  `SKILL.md`, `` | `cannot_judge` | The state file EXISTS and could not be read ``.
  `install_check_siblings.json` anchors four `check_siblings` lines and one `check()` line. The
  harness requires each anchor to occur exactly once (`anchor_status` in
  `h_mad_mutation_harness.py`: `hits == 1`).
- **DP4 — fence helpers.**
  - `find_heading` returns `(matches[0].end, matches[0].level)` or `None`, and raises
    `AmbiguousHeading(n)` on more than one match (`sed` over its definition in
    `h-mad/scripts/h_mad_doc_block_exec.py`).
  - `fence_aware_end(text, start, level)` stops at the next heading of level ≤ `level`.
  - `_fence_events` yields `open`/`body`/`close`/`heading`/`prose` events.
  - `grep -n '_fence_events' h-mad/tests/test_h_mad_doc_block_exec.py` → tests call it, and one
    asserts it is the only recognition site.
- **DP5 — grok's `streaming-json` has no init line and does list skills.** A JSON walk over
  `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson` counts event types:
  - 9 `available_commands`, each with 316 `commands`, whose names include `h-mad` and `handoff`;
  - 70 `thought`, 21 `text`, 2 `tool_call`, 4 `tool_call_update`, 3 `usage`, 1 `end`;
  - 0 `system`.

  `grep -n 'streaming-json\|stream-json' ~/.grok/docs/user-guide/14-headless-mode.md` places the
  `system`/`init` line under §"streaming-messages-json". The sibling design's `exec grok` argv line
  reads `--output-format streaming-json`.
- **DP6 — host logs carry tool output.**
  - grok: that log's `tool_call_update.rawOutput` holds `FileContent.content`.
  - agy: `docs/03-analysis/probes/grok-codex-fallback/plan-audit-v1-p2-agy.log` has tool steps
    shaped `step_update.{step_type:"tool", tool_name, tool_info:{parameters, output}}`, 16 ACTIVE
    and 16 DONE.
  - codex: `h-mad/tests/fixtures/codex-text-8-exec.log` shows `exec`, then the command line, then
    ` succeeded in …`, then the output lines.
- **DP7 — collection.** `pytest.ini` holds only `testpaths = h-mad/tests handoff/tests
  handoff/scripts`, and sets no `python_files`. `host_parity.py` is therefore not collected.
- **DP8 — the bare-timeout scan.** `test_h_mad_portable_timeout.py` scans `references/*.md`,
  `scripts/*.sh`, `scripts/*.py` and `hooks/*.sh` with `(?:^|[^-\w])timeout\s+\d+`.
- **DP9 — existing tests cited.**
  - `grep -c 'def test_' h-mad/tests/test_h_mad_install_check.py` → 23 matching lines, 7 of them
    inside `class TestSiblingSkills`.
  - `test_ok_below_the_ceiling`, `TestResumeDecisionSurfacesOwnership` and
    `test_no_session_id_preserves_legacy_behaviour` exist (`grep -n`).
  - `grep -rln 'agy-runtime.md' h-mad/tests handoff/tests | wc -l` → 0 files: no existing test
    reads either agy adapter. That zero is incidental, meaning no one wrote one. It is not
    load-bearing, and D12's tests are the first.
- **DP10 — the operator links are absent.** `ls -ld ~/.agents/skills/{h-mad,handoff}
  ~/.gemini/config/skills/{h-mad,handoff}` → 4 of 4 "No such file or directory". The design
  assumes none of them.
- **DP11 — codex evidence is binary strings only.** `strings "$(readlink -f "$(which codex)")" |
  grep -c -F -- '<t>'`, in matching lines, for codex-cli 0.157.1:

  | string | lines |
  |---|---|
  | `AGENTS.md` | 61 |
  | `/compact` | 25 |
  | `/new` | 8 |
  | `hooks.json` | 7 |
  | `SessionStart` | 49 |
  | `PreToolUse` | 39 |
  | `update_plan` | 42 |
  | `request_user_input` | 72 |
  | `spawn_agent` | 45 |
  | `fork_turns` | 9 |
  | `.agents/skills` | 1 |

  These are leads, not documentation.
- **DP12 — grok facts re-read.** `grok --version` → `grok 1.0.41 (4220f3b224a6) [stable]`.
  Matching-line counts under `~/.grok/docs/user-guide/`:

  | file | pattern | lines |
  |---|---|---|
  | `01-getting-started.md` | `todo_write` | 1 |
  | `22-permissions-and-safety.md` | `todo_write` | 1 |
  | `13-memory.md` | `\.grok/memory` | 12 |
  | `10-hooks.md` | `GROK_SESSION_ID` | 1 |
  | `16-subagents.md` | `Ctrl+T` | 1 |
  | `26-config-reference.md` | `compat\.claude\.(skills\|hooks)` | 2 |

  Also read:
  - `10-hooks.md`'s exit table: `2` is an explicit deny, and any other non-zero exit fails open.
  - Its `timeout` key defaults to 5 s, or 600 s for `Stop`, `SubagentStop` and `PostToolUse`
    gates.
  - `04-slash-commands.md` has `/new` (alias `/clear`), `/compact` and `/context`.
  - `12-project-rules.md` lists `Claude.md`, `CLAUDE.md` and `AGENTS.md`.

## Version History
- v1.0: Initial design draft (2026-09-28) from spec v1.2 (b51c5b2a) and plan v1.2 (e32ffe5c); premises executed at 6478b8b5 (tree unchanged at dfd5f02e). Registry, host_parity checker (find_heading/fence_aware_end/_fence_events table parse, closed branch-expansion grammar reproducing P2b), shared h_mad_host classifier, W1-W3 host/root checks keeping all 17 existing mutation anchors unique, agy root by partitioning check_siblings, 22x3 construct matrix, D12 doc-test token table, probe sidecar. Supersedes the plan on nine items: grok V-11.1 reads available_commands (exec grok emits streaming-json, no init line); v111 orders input events not log text (logs carry tool output); smoke_assert.py single file; rehearsal in Phase 6; 42 kind fixtures (6 splits); h_mad_host module; agy partition; AC-12.2 on both arms; unknown host JSON-encoded.
