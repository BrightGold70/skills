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

The design implements spec v1.3 (FR-1 to FR-12) through plan v1.2 and keeps every plan decision,
with the exceptions listed in §"Supersedes the plan on". Each exception comes with its evidence and
a revert. Items 1, 2 and 5 there are now spec v1.3 text as well ("adopted by spec v1.3"); they stay
listed because the plan still carries the superseded form.

Three constraints shape it:
- **Existing mutation anchors must stay unique.** `h_mad_mutation_harness.py --check-anchors`
  refuses an anchor that matches twice. The class is every mutation spec whose `file` names a file
  this feature edits, in **both** spec directories, `h-mad/tests/mutation-specs/` and
  `handoff/tests/mutation-specs/` (DP3). Three of them anchor the three touched scripts, and many
  more anchor the two `SKILL.md` files that strand 4 edits. No new code or text may repeat any of
  their anchors, and the gate is `--check-anchors` over both directories printing `ANCHORS_OK`.
- **Tests must run from the skill alone.** Everything a test imports lives under `h-mad/`.
- **Hosts are reached only through `hmad-dispatch`,** and only by the operator's live smoke.

The key decisions:
- Host classification is one module, and both scripts call it.
- The agy-root check partitions `check_siblings` output. It does not classify a second time.
- The adapter table is located with the fence-aware helpers of `h_mad_doc_block_exec`.
- The smoke assertions read **input events** of each host's log format, never free text.

## Supersedes the plan on

Each item states the plan text it replaces, the evidence, and the revert. The spec sentences this
design depends on are listed in §"Spec restatements this design depends on", at the end of this
section, so a spec revision can be checked against a named set.

1. **V-11.1's grok clause reads the `available_commands` event, not a `system`/`init` line.**
   (Adopted by spec v1.3.)
   - What the plan says: plan §"Convention Prerequisites" `v111` (and spec F11 before v1.3)
     expects a `system`/`init` line whose `skills` field holds `h-mad`.
   - What `exec grok` emits: grok-codex-fallback's `exec grok` arm passes
     `--output-format streaming-json` (its design §D3, the `gargs` line). In
     `~/.grok/docs/user-guide/14-headless-mode.md`, `streaming-json` is a `type`-tagged event
     stream. The `system`/`init` line belongs to the other format, §"streaming-messages-json".
   - Measured: the committed probe log `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson`
     holds no `system` event. It holds 9 `available_commands` events, each with the keys
     `commands`, `tools` and `type`. `commands` is a list of 316 plain **strings**, and `"h-mad"`
     and `"handoff"` occur in it as bare strings (DP5). No element is an object, so there is no
     `.name` to read.
   - Consequence: under the plan's form, every grok smoke prints `FAIL V-11.1`, and `recover`
     then reverts a good integration.
   - **A listing is a precondition, not proof.** `available_commands` shows that the skill is
     *available*. The spec's V-11.1 also requires that the host *loaded* `SKILL.md`. For grok that
     is proved only by an observed successful content read of `h-mad/SKILL.md` (§D10), by the
     host's `read_file` tool or a shell content read. With no such read, the grok arm prints
     `UNVERIFIED`, which is a halt and never a pass. `~/.grok/docs/user-guide/08-skills.md` says grok *inlines* a skill body, so this halt
     may be the usual outcome (§D10 Residuals).
   - Revert: restore the plan's `init` check. That is correct only if `exec grok` is changed to
     `streaming-messages-json`, which is the sibling feature's decision.
2. **V-11.1 orders input events, never text matches over the whole log.** (Adopted by spec v1.3.)
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
   - The same class has a second axis inside the input. **A mention is neither an execution nor a
     read.** `grep -n x h-mad/scripts/h_mad_state_write.py` names a script without running it, and
     `test -f …/grok-runtime.md` names the adapter without reading it. §D10 therefore classifies
     each simple command by its argv: an **execution**, a **content read**, a known
     non-executing command, or **unclassified**. Only the first two count. An unclassified
     command that mentions a script halts as `UNVERIFIED` instead of being guessed.
   - Revert: keep the plan's `v111`, and drop rehearsal cases R4, R6 and R7 below, which that form
     fails.
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
5. **Fixture count: 36 disjunct fixtures plus 6 splits, 42 in total.** (Adopted by spec v1.3.)
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
     anchors (DP3a).
8. **AC-12.2 is claimed on both byte-identity arms.**
   - The plan did not claim AC-12.2 at the real defaults "until the spec restates it".
   - Spec v1.2 restated it (spec Version History v1.2), so arm B's closed diff is now the AC.
9. **An unknown `HMAD_HOST` value is printed bare only when it is safe; otherwise it is
   JSON-encoded in `host=`.**
   - Spec FR-8 writes `host=<value>`. A value holding a newline would otherwise print a second
     stdout line, and a value holding a space would split the token.
   - The rule: a value that **fully** matches `[A-Za-z0-9._-]+` (`re.fullmatch`) is printed bare,
     so `zzz` gives `host=zzz` and `Grok` gives `host=Grok`, the bytes the spec's form gives.
     Any other value is printed as `json.dumps(value)`, so `" grok"` gives `host=" grok"`.
   - `re.fullmatch` is load-bearing. `re.match(r"^[A-Za-z0-9._-]+$", v)` accepts `"zzz\n"`,
     because `$` matches before a trailing newline, and that would print two lines. A fixture
     pins it (§Test Plan).
   - A declared host (`codex`, `agy`, `grok`) is printed bare, exactly as AC-8.1 requires.
10. **The live-smoke record is written at the spec's path and archived by a re-run of 7c's `mv`.**
    - What the plan says: the record is written straight into
      `docs/archive/<YYYY-MM>/multi-host-runtime/multi-host-runtime.live-smoke.md`, "the directory
      7c created" (plan Deliverables row and the smoke's part 2).
    - What this design does (orchestrator decision OD-7): the smoke writes
      `docs/03-analysis/multi-host-runtime.live-smoke.md`, the spec FR-11 path. The docs-only step
      after the smoke then archives it with 7c's own command and commits it before 7e (§"When the
      smoke record is archived" under §Components). The record's final path is the plan's.
    - Revert: write the record straight into the archive directory, as the plan does, and owe the
      spec a restatement of FR-11's path.

**Decisions this design records.** The design used to cite two decisions, OD-a and OD-b, that no
committed document defined. They are defined here, and later text cites them by these names:
- **OD-a (unknown-host encoding)** is §"Supersedes" item 9: bare when the value fully matches
  `[A-Za-z0-9._-]+`, JSON-encoded otherwise. The rejected options were "always bare" (a newline
  splits the stdout line) and "always JSON" (`zzz` would print `host="zzz"`, not the spec's form).
- **OD-b (what an `UNVERIFIED V-11.1` does)** has two options: (1) it is a part-2 stop, so it calls
  `recover`, which reverts the integration (the plan's rule, kept here); (2) it halts without
  reverting. That would change the plan's part-2 rule, so this design does not make it. Under
  orchestrator decision OD-1, `UNVERIFIED` for a missing `SKILL.md` read is grok's alone; codex
  and agy get `FAIL` (§D10 step 5).

**Spec restatements this design depends on.** The design keeps its position on each item below.
A spec revision is complete for this design when it carries each sentence, or one with the same
content:
- **AC-3.3.** Replace "Fourteen kinds means fourteen fixtures." with: "Each disjunct of the
  fourteen kinds has its own fixture, and a disjunct may be split by type or shape but never
  merged: 36 disjunct fixtures plus 6 splits, 42 in total, each asserting exactly its own
  `(kind, reason)` pair."
- **AC-4.2.** Replace the single A4 fixture with: "A4 is exercised per branch, with
  `~/.claude/foo`, `$HOME/.claude/foo` and `${HOME}/.claude/foo` each alone, and removing one
  branch clears only that branch's fixture."
- **AC-5.2, reason (i).** "Reason (i) is written from the gate's refusal form measured at
  `<base>`: `exit 1` gives 'the gate refuses by `exit 1`, which grok treats as fail-open' (token
  `exit 1`); form (a), rc 2 (`exit 2`), gives no reason (i) (token `exit 2`); form (b),
  `hookSpecificOutput.permissionDecision`, gives no reason (i) (token `permissionDecision`); any
  other reading halts to the operator."
- **AC-5.2, reason (ii).** "grok's camelCase `toolInput` supplies none of the gate's read paths."
- **F11 and V-11.1, grok.** "For grok, the `streaming-json` `available_commands` event's
  `commands` list, a list of plain strings, contains `h-mad`. That is a precondition. The load
  itself is shown by an observed successful content read of `h-mad/SKILL.md`, by the same
  predicate as the adapter read (grok's `read_file` or a shell content read). Without that
  observed read, the grok arm halts as unverified and never passes."
- **V-11.1, every host.** "A read is an observed, successful content read: the host's file-read
  tool, or `cat`, `head`, `tail`, `nl` or a print-only `sed` with the file as an operand. Its event
  must show success, and its returned text must contain the file's first `# ` heading line. A
  command that only names the file, such as `test -f`, `echo`, `grep -l` or `ls`, is not a read. A
  script run is an interpreter invocation of the script, never a mention of its name. At least one
  script run carries the inline declaration `HMAD_HOST=<host>`."
- **V-11.1 verdict set.** "The verdict is exactly one of `PASS`, `FAIL` (with the failed clause),
  `UNVERIFIED` or `UNREADABLE`. `UNVERIFIED` is printed for grok's skill load and for a log the
  classifier cannot read as keeping or breaking the contract: an unparseable line or command, an
  unobserved input or output shape, or an unclassified command that mentions a script before the
  adapter read. `UNREADABLE` (exit 2) means that no verdict exists. Every token except `PASS`
  halts." This replaces spec v1.3's "exactly one of `PASS`, `FAIL` … or `UNVERIFIED` (grok skill
  load only)". The codex/agy skill-load clause (`FAIL`) already agrees with §D10 step 5.
- **FR-3 failure line.** "A kind with more than one disjunct carries `reason=`. A kind with one
  disjunct prints none, and its pair is `(kind, None)`." This replaces "Each failure line also
  carries a `reason=`".
- **AC-5.2 form (a) wording.** Where the spec writes "rc 2", it writes "rc 2 (`exit 2`)", so the
  adapter text that copies it carries the pinned token.
- **FR-8 unknown-host row.** "`<value>` is printed bare when it fully matches `[A-Za-z0-9._-]+`,
  and as a JSON string otherwise."
- **FR-8 order.** "The host check precedes the `--window` check, for a declared and an unknown
  value alike."
- **FR-9 unknown value.** "An unknown `HMAD_HOST` value is treated as declared: without a session
  id, the oracle answers `cannot_judge`."
- **AC-8.4, grok.** "grok has no context indicator the orchestrator can read, so the substitute
  is none. The operator's `/context` is a separate manual action, not an orchestrator gate."
- **FR-10 option defaults.** "An environment variable that is present, even empty, replaces the
  default; an explicit option always wins."

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
  entries as `seed.json` (D8). That is a frozen copy of the spec seed at `6494b3c`, and its only
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
class Row:
    id: str; status: str; mapping: str; source: str   # cells after D2.4 steps 5 and 7

@dataclass(frozen=True)
class Table:
    rows: list[Row]                  # well-formed body rows, in document order
    problems: list[tuple[str, str, str]]  # (kind, reason, id): TABLE_MISSING / TABLE_MALFORMED

def adapter_table(text: str) -> Table: ...   # D2.4, the ONE adapter table reader

@dataclass(frozen=True)
class ParityResult:
    failures: list[Failure]
    stages: tuple[str, ...]         # stages that ran: "registry", "skill", "adapter"

def check(paths: ParityPaths, *, axes: Mapping[str, str] = CATCH_ALL_AXES,
          exclusion_suffixes: Sequence[str] = EXCLUSION_SUFFIXES) -> ParityResult: ...
```

`adapter_table` is public because two callers need the same rows. `check()`'s adapter stage calls
it and turns each `problems` entry into a `Failure` with `file=` added. The doc tests (D12) call
it too, and read a row by id from `rows`. No other function in either module parses an adapter
table. `test_host_runtime_docs.py` imports `adapter_table` from `host_parity` and never splits a
table line itself.

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
   - **`BAD_PATTERN`,** for each element **whose field checks ran** (no `missing_key:*` line)
     and whose `pattern` is not a `str`, or whose `re.compile(pattern)` raises `re.error`.

   **The rule over the later steps.** A step after the per-element step reads a field only from
   elements whose field checks ran. Otherwise an absent key reads as `None` and is reported a
   second time: an absent `pattern` is "not a `str`". The class has exactly two members today:
   - `DUPLICATE_ID` reads `id`, and already filters on "passed `bad_id`", which implies the
     field checks ran.
   - `BAD_PATTERN` reads `pattern`, and takes the filter above.

   Residual: a registry step added later must take the same filter, and the
   `missing_key:pattern` fixture is the one that shows a step missing it. The filter hides an
   element's pattern and duplicate status until its keys are repaired. That costs one more repair
   cycle, and it is never a false clear, because the element already fails.

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
7. **Backticks.** The `construct` and `status` cells may carry one surrounding pair of
   backticks. They are removed **here, before any id is read**, by the one function `_cell_id`
   that every later step uses. D9.3 writes ids backticked, so an id read before this step would be
   `` `advisor` `` and would fail the id rule.
8. **Body rows.** Each row from row 3 on must have 4 cells, else
   `TABLE_MALFORMED reason=cell_count id=<_cell_id(first cell) if it matches the id rule, else ->`.
   Suppression rule (e) applies: such a row counts as present for its id and is not checked for
   any other kind. The `cell_count` fixture writes its id backticked, so a backtick strip moved
   after this step gives it two pairs (`cell_count` with `id=-`, and `ROW_MISSING`).

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
    shown = host_value if re.fullmatch(r"[A-Za-z0-9._-]+", host_value) else json.dumps(host_value)
    print(f"CTXBUDGET: UNKNOWN reason=unknown_host host={shown}")
    return 2
```

The script already imports both `json` and `re` at module level
(`grep -n '^import' h-mad/scripts/h_mad_context_budget.py`), so W1 adds no import beyond
`classify_host`.

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
  - The rule over every touched file: after the change, `h_mad_mutation_harness.py
    --check-anchors` over both spec directories must print `ANCHORS_OK` with `drifted=0` (the
    Anchors command in §Test Plan). It prints that today (DP3).
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

def checkout_skill_names(repo: Path) -> list[str]:
    """[p.parent.name for p in sorted(repo.glob("*/" + CHECKOUT_MARKER))] — the names
    check_siblings iterates, in its order."""

def split_agy_root(lines: list[str], skills_dir: Path, names: Iterable[str],
                   installed: Iterable[str]) -> tuple[list[str], list[str]]:
    """Partition check_siblings(repo, skills_dir) output into (issues, details)."""
```

`check()` passes `names=checkout_skill_names(sibling_repo)` and `installed=AGY_INSTALLED_NAMES`.
`check_siblings` enumerates names with the same glob expression inside its own body
(`h_mad_install_check.py`, the `for skill_md in sorted(repo.glob(...))` loop), and that body stays
byte-identical, so the expression exists twice. The two copies are held together by
`test_checkout_names_agree_with_check_siblings`. That test builds a checkout of three skills, each
installed as a copy under a temp root, and asserts that the set of names in `check_siblings`'
lines equals `set(checkout_skill_names(repo))`. If the copies drift, the partitioner's fail-closed
rule below still keeps every unattributed line an issue.

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
- **`split_agy_root`.** For each name `n` in `names` and kind `K`, a line counts as that pair
  when it starts with `f"SIBLING_{K}:{skills_dir / n} "`. The trailing space separates `h-mad`
  from any longer name. All three `check_siblings` line forms put a space right after the link:
  `… (expected`, `… -> …` for `DANGLING`, and `… -> …` for `WRONG_CHECKOUT`.
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
| `smoke_assert.py` | `smoke_assert.py v111 --host H --log L --root R` · `v112 --out O --record JSON --feature F` · `rehearse` | `PASS V-11.1` / `FAIL V-11.1 <why>` / `UNVERIFIED V-11.1 <why>` / `UNREADABLE V-11.1 reason=<r>` (D10); `PASS V-11.2` / `FAIL V-11.2 <why>` / `UNREADABLE V-11.2 reason=<r>`; one line per rehearsal case, then `REHEARSAL: PASS n=N` / `FAIL` | the given files; `rehearsal/` fixtures |
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

    Each budget and decision case runs with `HMAD_HOST` unset, and again with `claude`. This arm
    covers AC-8.3's "sample run's stdout is byte-identical" half only. Its other half, "every
    existing test passes", is owned by two runs of the whole existing
    `test_h_mad_context_budget.py` module (§Test Plan, Commands).
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
- **`## Install`** (h-mad codex, agy, grok; AC-10.4). The handoff adapters have no `## Install`
  section:
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
- **agy install-check paragraph rewording.** It keeps the tree's sentence "Do not run it as a
  gate here" byte-identical (located in `h-mad/references/agy-runtime.md` by that string; it
  occurs once), and it keeps the `SKILL_NOT_INSTALLED` explanation for the Claude link. It adds
  that `--agy-skills-dir` checks this host's own root.
- **The "typically" sentences (plan P10).** Each is located by the string "typically" inside its
  adapter's `## Package and project roots` (h-mad) or `## Resolve the skill package` (handoff).
  Each file holds the string once, so the locator is exact; if a second one appears, the edit
  stops and asks. They become:
  - h-mad: "the operator-installed link `~/.gemini/config/skills/h-mad` (§Install below), when it
    exists";
  - handoff: "the operator-installed link `~/.gemini/config/skills/handoff`, when it exists". It
    has no section reference, because `handoff/references/agy-runtime.md` has no `## Install`
    and handoff never points into an `h-mad` file.
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
  - Reason (i) is written from the gate's **refusal form measured at `<base>`** (5c), read from
    its refusal sites together with the sibling's recorded FR-0 branch:

    | refusal form at `<base>` | reason (i) as the adapter writes it | token the doc test pins |
    |---|---|---|
    | `exit 1` (today's form) | the gate refuses by `exit 1`, which grok treats as fail-open | `exit 1` |
    | (a) rc 2, reason on stderr | none: rc 2 (`exit 2`) is grok's documented `PreToolUse` deny; the halt rests on (ii) and (iii) | `exit 2` |
    | (b) rc 0, stdout `hookSpecificOutput.permissionDecision == "deny"` | none: `permissionDecision` is grok's canonical decision field (`10-hooks.md` §"Output (Blocking Hooks)"); the halt rests on (ii) and (iii) | `permissionDecision` |

    Any other reading, such as a mix of forms across refusal sites, halts to the operator before
    the grok adapter is written. It is never mapped to the nearest row.

    This table follows `10-hooks.md`, which documents `hookSpecificOutput.permissionDecision` as
    canonical (DP12). Plan §Risks calls form (b) "not a grok-documented deny form", and the tree
    contradicts that; the plan owes the correction.

  Every reason is pinned, so deleting any one of them turns the doc test RED. The test reads the
  measured form from the constant `REFUSAL_FORM_AT_BASE` (`"exit1"`, `"a"` or `"b"`) in
  `test_host_runtime_docs.py`, and step 5c writes that constant from its measurement. It has no
  default, so a missing 5c reading is a collection error, never a silently chosen row. The always-pinned tokens are
  `step5:grok_tdd_hook_unverified`, `toolInput` (reason ii), `fails open` (reason iii, the exact
  phrase above) and `pytest`.
- **`## Author and reviewer roles`** (h-mad grok; F2). It states:
  - `spawn_subagent` cannot select an agent by name;
  - the role travels as the text of `$HMAD_SKILL_ROOT/agents/<name>.md` in `prompt`;
  - results come back through `get_command_or_subagent_output`;
  - nesting is capped at one level;
  - no filesystem jail: diff `git status --short`, tracked and untracked, after each dispatch
    (NFR Security).
- **`## Context budget and claims`** (h-mad codex, agy, grok; FR-8, FR-9, AC-8.4, AC-9.3). It
  covers four points. Every command shape below sits in a fenced `bash` block inside the section,
  with the adapter's **concrete** host value, never a `<host>` placeholder. `<h>` below stands for
  `codex`, `agy` or `grok`, one per adapter.
  - **Fence placement.** In the adapter, each of these fences opens at indent 0 to 3 spaces,
    outside any list item. `_fence_events` recognises only an opener matching
    `^(?P<indent> {0,3})` (`h-mad/scripts/h_mad_doc_block_exec.py`, in `_fence_events`), so a
    fence nested 4 spaces under a bullet, as this design lays its examples out, reads as prose.
    D12's fenced-line tests then find 0 lines and fail loudly.
  - **Inline declaration.** Every h-mad script call carries `HMAD_HOST=<h>` inline, so it does not
    depend on the shell keeping exports. The section carries this runnable line, verbatim with the
    adapter's value:

    ```bash
    HMAD_HOST=<h> python3 "$HMAD_SKILL_ROOT/scripts/h_mad_context_budget.py"
    ```
  - **The budget.** `CTXBUDGET: UNKNOWN reason=host_unsupported` is expected and never read as
    `OK`. The 80% run ceiling is unenforced on this host. Each adapter states
    `substitute: none`: no host exposes a context indicator the orchestrator can read.
    - grok adds that the operator's `/context` (`04-slash-commands.md`) is interactive only and
      not reachable by the model. It is a separate manual action the operator may take, **not an
      orchestrator gate**. The adapter says so in those words.
    - codex and agy add nothing more.
  - **The session id.**
    - grok: `GROK_SESSION_ID` is documented for hook processes only (F10). It is used in place of
      a minted id **only after the live smoke records it present in the orchestrator's shell**,
      and the adapter carries that condition in those words.
    - codex and agy: no documented variable (F13, F14).
  - **The minted-id procedure (orchestrator decision OD-5).** The id is minted **once at
    bootstrap** and written to one file. Every later call reads it from that file, inline. No line
    relies on a shell variable surviving between two host tool calls, because a host may run each
    call in a fresh shell.
    - **The file** is `"$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>"`, called
      `<sid-file>` below. The adapter writes that expression out in full on every line. It sits
      inside the git directory, so `git status --short` never lists it, and V-11.3's read-only
      check is unaffected. It is per checkout, because a linked worktree has its own git
      directory, and per feature. It survives across tool calls, and it does not rely on the
      project's `.h-mad/` directory, which holds tracked files.
    - **Minting refuses to overwrite.** The mint runs under `set -C` (noclobber). If `<sid-file>`
      already exists, the redirect fails and the line prints `SID: NOT_MINTED`. The adapter says
      that this is a halt to the operator: the file belongs to another session, or to an earlier
      one, and it is never deleted or reused without the operator. Two sessions therefore never
      share an id without the operator's knowledge.
    - **Each use is its own fenced line**, so each can be pinned alone. `<sid-read>` below stands
      for `"$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"`, written
      out in full in the adapter. The oracle line comes first, because the oracle decides before
      the claim:

    ```bash
    ( set -C; python3 -c 'import uuid; print(uuid.uuid4())' > "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>" ) && echo "SID: MINTED" || echo "SID: NOT_MINTED"
    HMAD_HOST=<h> python3 "$HMAD_SKILL_ROOT/scripts/h_mad_resume_decision.py" --state docs/.bkit-memory.json --feature "<feature>" --session-id <sid-read>
    HMAD_HOST=<h> python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --create --claim <sid-read>
    HMAD_HOST=<h> python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --claim <sid-read>
    HMAD_HOST=<h> python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --beat --session-id <sid-read>
    HMAD_HOST=<h> python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --set current_phase=5 --session-id <sid-read>
    HMAD_HOST=<h> python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --release --session-id <sid-read>
    ```

    - The `--create --claim` line is for the oracle's `start_fresh` token. `h-mad/SKILL.md`'s
      claim block says that "`--claim` ALONE exits 2 here with `ERROR: no such feature`". The
      plain `--claim` line is for every other route.
    - `--claim` takes the id as its value, and `--beat`, `--set` and `--release` take it through
      `--session-id`, which is `h_mad_state_write.py`'s own argument shape (DP15).
    - The failure modes:
      - A session that loses its file sees its own claim as `owned_elsewhere` until the staleness
        window lapses. It never gets a false clear.
      - An unreadable `<sid-file>` makes `<sid-read>` expand to `""`. The oracle, which runs
        first, treats an empty id as no id and answers `cannot_judge` under a declared host
        (§D5), which is a halt.
    - Residual, stated exactly: an operator who deletes or rewrites `<sid-file>` while its
      session is live gives that session another session's id, or none. That is an operator
      action outside this guard.
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
| `subagent-call` (h) | M: `collaboration.spawn_agent`, `fork_turns: "none"`, agent file text in the prompt [observed: codex 0.144.1 rollout, the injected multi-agent instructions naming `spawn_agent` and `fork_turns` (DP16); `codex features list` at 0.157.1: `multi_agent stable true`] | M: `define_subagent` then `invoke_subagent` [observed: `init.tools` of `plan-audit-v1-p2-agy.log`] | M: `spawn_subagent` with the agent file text in `prompt` [`16-subagents.md`] |
| `skill-call` (both) | M: codex lists each installed skill in its `## Skills` instructions with the location of its `SKILL.md`, and the skill is used when named (`$h-mad` or plain text); V-11.1 at 0.157.1 decides the load (A2) [observed: codex 0.144.1 rollouts, `## Skills` entries under `~/.agents/skills/<name>/SKILL.md` and the "Trigger rules" text (DP16)] | M: the installed agy skill under `~/.gemini/config/skills` [agy docs `skills.md`] | M: the skill's slash command, e.g. `/handoff` [`08-skills.md`] |
| `advisor` (h) | N: codex has no advisor tool; substitutes `hmad-dispatch exec agy\|grok`, or `collaboration.spawn_agent` with `fork_turns: "all"` (AC-6.3) [observed: codex 0.144.1 multi-agent instructions (DP16); `codex --help` at 0.157.1 lists no advisor command] | N: substitutes `hmad-dispatch exec codex\|grok`, or `define_subagent`/`invoke_subagent` with the review context in the prompt (AC-6.3) [observed agy tools] | N: no advisor tool (F1); a child does not inherit the transcript (F2); substitutes `hmad-dispatch exec codex\|agy\|grok` or `spawn_subagent` with a self-contained prompt (AC-5.3) [`01-getting-started.md`, `16-subagents.md`] |
| `send-message` (h) | N: codex 0.144.1's injected instructions describe `send_message` to a running agent, but no rollout shows it called and 0.157.1 is unobserved, so it is a lead; dispatch a fresh author with the prior report path [observed: codex 0.144.1 multi-agent instructions; 0 `send_message` function calls across the rollouts (DP16)] | N: `send_message` is in agy's tool list, but its target semantics are undocumented in agy's docs dir; dispatch a fresh author [observed agy tools] | N: `send_subagent_message` is off by default (F3); continue with `spawn_subagent` `resume_from` [`16-subagents.md`] |
| `hook-event` (h) | M: codex hook events via `hooks/h-mad-codex-tdd-gate.py` in the active codex hooks file [observed: `hook: PreToolUse` in `h-mad/tests/fixtures/codex-text-8-exec.log`] | M: `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`; no `SessionStart` [agy docs `hooks.md`] | M: Claude hooks from `~/.claude/settings.json` run under `compat.claude.hooks`, with camelCase payloads and exit-2 deny (F7–F9) [`10-hooks.md`] |
| `session-id-env` (h) | N: no documented variable; minted id (FR-9) [F14] | N: no documented variable; minted id [F13] | M: `GROK_SESSION_ID` once the smoke records it in the shell, else a minted id (AC-5.5) [`10-hooks.md`] |
| `claude-config-dir` (h) | N: the check it feeds reads Claude's settings scope; codex's config is its own, `~/.codex/config.toml` [`codex --help` at 0.157.1, the `-c` option text] | N: agy's config root is `~/.gemini/config` [agy docs `hooks.md`] | N: grok reads `~/.claude/settings.json` by fixed path; honouring the variable is undocumented [`10-hooks.md`] |
| `claude-md` (both) | M: `AGENTS.md` project instructions [observed: codex 0.144.1 rollouts, `# AGENTS.md instructions for` blocks (DP16)] | M: workspace rules under `.agents/` [agy docs `rules.md`] | M: grok reads `Claude.md`/`CLAUDE.md`/`AGENTS.md` [`12-project-rules.md`] |
| `claude-skills-dir` (both) | M: `$HMAD_SKILL_ROOT` / `$HANDOFF_SKILL_ROOT` from the loaded path, `~/.agents/skills/<skill>` [observed: codex 0.144.1 rollouts list skills at `~/.agents/skills/<name>/SKILL.md` (DP16); V-11.1 at 0.157.1 decides (A2)] | M: the same roots under `~/.gemini/config/skills/<skill>` [agy docs `skills.md`] | M: loaded straight from `~/.claude/skills` via `compat.claude.skills` [`grok inspect`] |
| `claude-agents-dir` (h) | N: no agent registry; the file text travels in the spawn prompt [`codex --help` at 0.157.1: its `agents` command browses sessions, and no option names an agent file] | N: no file-based agent registry [observed agy tools] | N: grok lists `~/.claude/agents` but cannot select one by name (F2) [`16-subagents.md`] |
| `claude-hooks-dir` (h) | N: codex's gate is `hooks/h-mad-codex-tdd-gate.py`, wired from its hooks file [observed codex log] | N: hooks live in `hooks.json` [agy docs `hooks.md`] | M: Claude hook scripts run from their Claude paths under compat (F7) [`10-hooks.md`] |
| `claude-settings` (both) | N: codex hooks live in a hooks file, not in Claude's settings; HemaSuite's is `.codex/hooks.json` [observed: `~/.codex/hooks.json` present on this host (DP16); `codex --help` at 0.157.1, `--dangerously-bypass-hook-trust`] | N: agy does not read Claude's settings file; its hooks live in `~/.gemini/config/hooks.json` [agy docs `hooks.md`] | M (h-mad): read under compat (F7) [`10-hooks.md`]; N (handoff): `todo_write` needs no settings opt-in [`01-getting-started.md`] |
| `claude-handoffs-dir` (both) | M: unchanged; a plain file store every host reads and writes through its shell [observed: `test -f ~/.claude/handoffs/INDEX.md`] | M: unchanged [same] | M: unchanged [observed: same] |
| `claude-projects-store` (h) | N: codex's memory is its own feature, `memories`, stored under `~/.codex/`; never point the memory-index check at `~/.claude/projects` [`codex features list` at 0.157.1: `memories stable false`; observed: `~/.codex/memories` present (DP16)] | N: `~/.gemini/config/projects/*.json` (existing §Memory index) [observed] | N: grok keeps its own memory store, `~/.grok/memory/`, not Claude's projects store (AC-5.6) [`13-memory.md`] |
| `claude-home-bare` (h) | N: Claude's home; codex's is `~/.codex`, and nothing is relinked [`codex --help` at 0.157.1, the `-c` option text] | N: Claude's home; agy's root is `~/.gemini/config` [agy docs `hooks.md`] | N: grok's home is `~/.grok` [`05-configuration.md`] |
| `session-reset-command` (both) | N: no reset command is evidenced: `/new` and `/compact` are binary strings only, leads (DP11), and no rollout or history line shows either typed; start a fresh `codex exec` session [`codex --help` at 0.157.1: `exec`; observed: 0 of 840 `~/.codex/history.jsonl` prompts begin `/` (DP16)] | N: no documented reset command; start a fresh `agy` session [agy docs dir] | M: `/new` (alias `/clear`) and `/compact` [`04-slash-commands.md`] |
| `skill-slash-invocation` (both) | M: name the skill, `$h-mad` / `$handoff` or plain text [observed: codex 0.144.1 rollouts, the `## Skills` "Trigger rules" text "with `$SkillName` or plain text" (DP16)] | M: invoke the installed agy skill by name [agy docs `skills.md`] | M: `/h-mad`, `/handoff` [observed: `available_commands` in the sibling probe log (DP5)] |
| `task-tools` (hand.) | N: no rung 1 evidenced at 0.157.1 (A3: `update_plan` is a lead; it is observed only in rollouts of codex 0.142.0 and older); rung 2 `.omc/notepad.md`, then rung 3 inline (AC-6.4) [A3; observed: `update_plan` calls in 0.142.0 rollouts (DP16)] | N: `manage_task` is a background-task manager, not a checklist; rung 2 `.omc/notepad.md`, then rung 3 inline (AC-6.4) [observed agy tools] | M: `todo_write`, user-visible pane (AC-5.4) [`01-getting-started.md`] |
| `tool-search` (hand.) | N: no rung-1 todo tool is evidenced (A3), so none is deferred and none needs loading [A3; `codex features list` at 0.157.1: 0 lines match `todo`] | N: agy has no todo tool to load: its tool list is given whole at start and holds no todo tool (`manage_task` manages background tasks) [observed agy tools: `init.tools` of `plan-audit-v1-p2-agy.log`, 57 names] | N: `todo_write` is built in, never deferred [`01-getting-started.md`] |
| `skill-root-env` (hand.) | M: `HANDOFF_SKILL_ROOT` from the `SKILL.md` location codex lists [existing adapter rule; observed: codex 0.144.1 rollouts, `## Skills` entries carry each `SKILL.md` path (DP16)] | M: `HANDOFF_SKILL_ROOT` [agy docs `skills.md`] | M: `HANDOFF_SKILL_ROOT` [`08-skills.md`] |
| `todo-tools-optin` (hand.) | N: no rung-1 todo tool is evidenced (A3), so there is no opt-in to set [A3; `codex features list` at 0.157.1: 0 lines match `todo`] | N: agy has no todo tool, so there is no opt-in to set [observed agy tools: `init.tools` of `plan-audit-v1-p2-agy.log`] | N: `todo_write` needs no opt-in [`01-getting-started.md`] |
| `claude-homunculus` (hand.) | M: unchanged; an optional file read when present [observed: `test -f`] | M: unchanged [same] | M: unchanged [observed: same] |

- **Row counts.** The matrix is derived from the registry: 17 h-mad rows per h-mad adapter and 12
  handoff rows per handoff adapter, 87 rows in all. If the AC-4.6 re-derivation changes the entry
  set, the matrix follows it, and no count in this document is carried past that record.
- **Codex evidence (orchestrator decision OD-6).** This tree has no codex host document (F14), and
  a binary string or assumption A2 is a lead, not evidence. No `M` codex cell rests on either
  alone:
  - each `M` cell cites a `codex --help` / `codex features list` reading at 0.157.1, or an
    observed trace in this host's codex rollouts (DP16);
  - `session-reset-command`, whose only support was the strings `/new` and `/compact`, is `N`
    with the lead named.
  - The observed rollouts are from codex 0.144.1 and older; the host has 0 rollouts at 0.157.1
    (DP16). A row that rests on a rollout is re-verified by the live smoke at 0.157.1: V-11.1
    decides the skill rows (A2), and a newer or different reading is recorded, not assumed, as A1
    does for grok.
- **Not-applicable reasons (AC-2.2, orchestrator decision OD-9).** Every `N` cell above states in
  its mapping text why the construct does not apply; the bracket is the `source`, never the
  reason. D12's AC-2.2 row checks that mechanically in each adapter.
- **grok `source` cells** follow AC-5.7's format: a chapter file matching
  `\b\d\d-[a-z-]+\.md\b`, the literal `grok inspect`, or a cell beginning `observed:`.

### D10 — Live smoke assertions (FR-11; supersedes items 1–3)

**Verdict tokens.** `smoke_assert.py v111` prints exactly one line, and it is one of four:
- `PASS V-11.1`;
- `FAIL V-11.1 <why>`: the log shows the contract broken;
- `UNVERIFIED V-11.1 <why>`: the log cannot show the contract kept or broken;
- `UNREADABLE V-11.1 reason=<r>`, exit 2: the log could not be parsed at all.

Only `PASS` passes. The other three are halts (smoke delta below).

**Reading the log.** `smoke_assert.py v111 --host H --log L --root R` reads the log in H's shape
(DP6) and reduces it to an ordered list of **input events**. `R` is the checkout the host loaded
h-mad from (the smoke passes `$REPO`); it is read only for the two needles below:

| host | log shape | event = | command text / read tool | success = | returned text = |
|---|---|---|---|---|---|
| grok | `streaming-json` NDJSON | each `{"type":"tool_call"}` | `run_terminal_command`: `rawInput["command"]`; `read_file`: `rawInput["target_file"]` | a later `tool_call_update` with the same `toolCallId` and `status == "completed"` | every `str` value under that update's `rawOutput` (the observed read shape is `rawOutput.FileContent.content`, DP6) |
| agy | NDJSON `{"event":"step_update","step_update":{…}}` | the first line per `step_index` with `step_type == "tool"` | `run_command`: `tool_info.parameters["CommandLine"]`; `view_file`: every `str` value of `tool_info.parameters` | a later line with the same `step_index` and `state == "DONE"` | that `DONE` line's `tool_info.output`, when it is a `str` |
| codex | text | each line equal to `exec` whose next non-beat line has the observed command shape `^\S+ -lc .* in \S+$` | that next non-beat line | the first non-beat line after the command line begins ` succeeded in` | the lines after the ` succeeded in` line, up to the next event's `exec` line or the end of the log |

- **Returned text is read for one purpose only (orchestrator decision OD-2):** to confirm that a
  read returned the file's text. It is never searched for events, commands or mentions, so the
  "input, never output" rule of §"Supersedes" item 2 holds for ordering. A **needle** is the
  file's first line matching `^# `, read from `R` at run time: `R/h-mad/references/<H>-runtime.md`
  for the adapter, `R/h-mad/SKILL.md` for the skill. The run prints
  `UNREADABLE V-11.1 reason=no_needle` if either file has no such line. It prints
  `UNREADABLE V-11.1 reason=needle_not_unique` if the adapter's needle occurs in `SKILL.md`, or
  the skill's in the adapter, because a read of one file could then pass for a read of the other.
  (At HEAD, the two existing adapters' H1 lines and `SKILL.md`'s H1 line each occur 0 times in
  the other files, by `grep -c -F -x`; see DP16.)
- **An unobserved output shape halts.** A read event that has a success signal but whose
  returned text is missing or not a `str` prints `UNVERIFIED V-11.1 <host> output shape
  unobserved`. The agy `view_file` output is taken from no log (DP6), and the first live smoke
  tests it.
- **The codex command-line shape.** All 8 `exec` events in the committed codex log have a command
  line of the form `/bin/zsh -lc "…" in <cwd>` (DP6). An `exec` line followed by a non-beat line of
  any other shape prints `UNVERIFIED V-11.1 codex input shape unobserved`, and it is never read as
  an event. That covers an output line that happens to equal `exec`.
  - Residual, stated exactly: codex output that reproduces a whole event (an `exec` line, then a
    line of the command shape) is read as an event. That happens only when the host prints a codex
    log, and the smoke prompt asks for no such read.
- **Assumption about the NDJSON logs:** a fresh `$S/log` holds only host NDJSON lines and
  `#hmad-beat` lines. `hmad-dispatch` says its log may also carry "pre-existing caller content"
  (the comment above `_agy_ndjson_response` in `hmad-dispatch.sh`). The smoke writes a fresh
  `$S/log` per host, so there is none. Whether `exec grok` routes grok's stderr or dispatch text
  into `--log` is unobserved in this tree, because the `exec grok` arm is the sibling's and is
  unmerged. If it does, the first grok smoke prints `UNVERIFIED V-11.1 unparseable line <n>`, which
  halts. The first live smoke records which case holds.

- **Lines that are not events.** `hmad-dispatch` writes its own `#hmad-beat …` lines into the
  same `--log` (`hmad-dispatch.sh`, the `printf '#hmad-beat` line), and the committed agy log
  holds 2 of them (DP6).
  - A line matching `^#hmad-beat ` is skipped, on every host.
  - In the NDJSON hosts, any other line that is not a JSON object prints
    `UNVERIFIED V-11.1 unparseable line <n>`. `hmad-dispatch` states that a beat can land mid-line
    and corrupt one event. Skipping that line could drop the one script run that decides the
    verdict, so it halts instead.
  - In codex, a beat between `exec` and the command line is skipped by the "first non-beat line"
    rule above.
- **Unobserved keys.** The committed grok log has 0 `run_terminal_command` events, and the agy log
  has 0 `view_file` steps (DP6), so `rawInput["command"]` and `view_file`'s parameter names are
  taken from no log. An event whose expected key is missing or not a `str` prints
  `UNVERIFIED V-11.1 <host> input shape unobserved`. The first live smoke tests the key, and a
  wrong guess halts; it never passes.

**Classifying a command.** Each command text is split into **simple commands** with
`shlex.shlex(text, posix=True, punctuation_chars=";&|<>()\n")`, `whitespace = " \t\r"`,
`whitespace_split = True` and **`commenters = ""`**. shlex's default commenter is `#`, and with it
`echo x # c⏎<run>` loses the newline that separates the run, and `echo ${#x}; <run>` loses the run
entirely. So a `#` is always an ordinary character here.

The rule over the class (tokenizer configuration against shell grammar): every token that `bash`
or `zsh` treats as a metacharacter is either modelled below or makes its simple command
unclassified. The punctuation tokens are handled in this order:
- **Redirect operator:** a token that fully matches `[<>&|]*[<>][<>&|]*` and is not made only of
  `|` and `&`. Examples are `<`, `>`, `>>`, `<<`, `<<<`, `>|`, `&>`, `&>>`, `>&`, `<&` and `<>`. It
  drops the token after it, which is the redirect target or heredoc delimiter. A digit-only token
  directly before it is an fd number and is dropped too, so `python3 2>err h_mad_x.py` keeps
  `h_mad_x.py` as `python3`'s first operand (orchestrator decision OD-3). Dropping a digit-only
  token can never drop a script name.
- **Process substitution:** a token that fully matches `[<>]\(` (`<(` or `>(`) ends the current
  simple command and starts a new one, as `(` does. So `cat <(python3 h_mad_x.py)` yields the
  simple command `python3 h_mad_x.py`.
- **Separator:** a token made only of `;`, `&`, `|`, `(`, `)` or newline ends a simple command.
  That includes `&&`, `||`, `;;` and `|&`. A `$(` splits as `$` then `(`, so a command
  substitution's body is its own simple command.
- **Any other token made only of punctuation characters** makes its simple command unclassified.

A `ValueError` from `shlex` prints `UNVERIFIED V-11.1 unparseable command`. A simple command is
taken after its leading `NAME=value` tokens are dropped; the dropped tokens are kept as the
command's **assignments** for step 4 of the verdict. With `argv0` the basename of its first token,
the command falls in exactly one of the classes below, tested in the order written; the first that
matches wins:
- **shell wrapper**: `argv0` is `bash`, `sh` or `zsh`, and an option token matches
  `^-[A-Za-z]*c[A-Za-z]*$`, a single-dash cluster, so `--norc` does not match. The token after it
  is classified recursively, to depth 2; deeper nesting is unclassified. codex's
  `/bin/zsh -lc "…" in <cwd>` is this shape, and the tokens after the script are ignored.
- **execution**: either
  - `argv0` matches `^python(3(\.\d+)?)?$`, and the first operand not starting `-` has a basename
    matching `^h_mad_[a-z0-9_]+\.py$`;
  - `argv0` matches `^python(3(\.\d+)?)?$`, and an `-m` option's value (the next token, or the
    rest of a `-m<name>` token) has a last dotted component matching `^h_mad_[a-z0-9_]+$`, as in
    `python3 -m h_mad_state_write` (the interpreter module form, OD-3);
  - `argv0` matches `^h_mad_[a-z0-9_]+\.py$` or `^hmad-dispatch(\.sh)?$`;
  - `argv0` is `bash`, `sh` or `zsh`, and the first operand has a basename matching
    `^hmad-dispatch(\.sh)?$`.
- **non-executing**: `argv0` is one of `cat`, `head`, `tail`, `nl`, `sed`, `grep`, `rg`, `ls`,
  `test`, `[`, `echo`, `printf`, `wc` or `stat`, and it passes that name's exec screen:
  - `sed` must be **print-only** (OD-3). Every script it is given must fully match
    `(\d+|\$)?(,(\d+|\$))?p`: each `-e`/`--expression` value, or the first operand when there is
    no `-e`. Its options must be drawn from `-n`, `--quiet`, `--silent`, `-E`, `-r` and `-e`.
    Any other script or option makes the command unclassified. That includes the `e` command,
    the `s///e` flag, and `-f`/`--file`, whose script cannot be seen. So `sed -e 'e python3
    h_mad_x.py'` is unclassified, and because it mentions a script it gives `UNVERIFIED`.
    `sed -n 1,80p …/h_mad_state_write.py`, `sed -n '620,690p' …` and `sed -n p` pass the screen.
  - `rg` fails the screen with any option that starts `--pre`, equals `-z` or `--search-zip`, or
    is a single-dash cluster (`^-[A-Za-z]+$`) holding `z`. ripgrep's `--pre=COMMAND` "Search
    output of COMMAND for each PATH" (`rg -h`), and `-z` runs decompression programs.
  - The other twelve names pass with any options.

  Within this class, a **content read of a file `X`** is one whose `argv0` is `cat`, `head`,
  `tail`, `nl` or `sed` and some operand of which names `X` (below). A content read is still
  non-executing.
- **unclassified**: anything else, including a non-executing name that fails its exec screen.

A **mention** is a match of `(?<![A-Za-z0-9_])h_mad_[a-z0-9_]+\.py\b|(?<![\w-])hmad-dispatch\b`
anywhere in a simple command's tokens. The left guard keeps `test_h_mad_x.py` from counting. An
unclassified simple command matters only if it mentions a script.

**Which files count.** An operand or tool path **names** the adapter when it equals, or ends with
`/` plus, one of `h-mad/references/<H>-runtime.md`, `$HMAD_SKILL_ROOT/references/<H>-runtime.md`
or `${HMAD_SKILL_ROOT}/references/<H>-runtime.md`. It names `SKILL.md` by the same rule with
`h-mad/SKILL.md`, `$HMAD_SKILL_ROOT/SKILL.md` or `${HMAD_SKILL_ROOT}/SKILL.md`. A
`handoff/references/…` path never names the adapter. A **successful content read** of a file is:
- an event of the host's read tool (grok `read_file`, agy `view_file`) whose path names the file;
- or a shell event holding a content-read simple command of the file;

and in both cases (orchestrator decision OD-2):
- the event's success signal (table above) is present; **and**
- the event's returned text contains the file's needle as a substring. A read that failed,
  returned nothing, or returned something else is not a read. `cat A || true`, where `cat`
  failed, has a success signal on its event, but its returned text is `cat`'s error and not A's
  heading, so it is not a read. A tool read that completed with empty content is not a read
  either.

`test -f`, `echo`, `grep -l`, `grep <pattern>`, `rg` and `ls` are never reads.

**The verdict**, decided in this order:
1. **Walk to the adapter read.** Walk the simple commands of every event in order, and within an
   event in textual order, up to the first successful content read of the adapter. The first of
   these that occurs decides:
   - an execution: `FAIL V-11.1 a script ran before the adapter was read`. A run counts on its
     input event whether it succeeded or not;
   - an unclassified simple command that mentions a script:
     `UNVERIFIED V-11.1 unclassified command before the adapter read`.
2. **Adapter read.** If there was no successful content read of the adapter:
   `FAIL V-11.1 no adapter read`.
3. **Skill listed (grok only).** Some `available_commands` event's `commands` must be a list
   holding the `str` `"h-mad"`. Non-`str` members are ignored. Otherwise:
   `FAIL V-11.1 grok did not list h-mad`.
4. **Host declared (every host; orchestrator decision OD-4).** At least one execution simple
   command must have among its assignments exactly `HMAD_HOST=<H>`, with `<H>` the host under
   test, and it must run an `h_mad_*.py` script (the first two execution forms). Otherwise:
   `FAIL V-11.1 no script call declared HMAD_HOST=<H>`. An `export HMAD_HOST=…` statement does not
   count, because every adapter asks for the inline form (§D9.2).
5. **Skill loaded (every host).** There must be a successful content read of `SKILL.md`, in any
   position (orchestrator decision OD-1). Otherwise:
   - codex and agy: `FAIL V-11.1 no observed SKILL.md read`;
   - grok: `UNVERIFIED V-11.1 no observed SKILL.md read`, because grok may inline the skill body
     without a tool call (Residuals below).
6. Otherwise `PASS V-11.1`.

- **Residuals, each stated exactly.**
  - A host that reads the adapter through a glob (`cat references/*.md`), or by a path relative to
    the skill directory (`cat references/<H>-runtime.md` with cwd set to it), gets
    `FAIL V-11.1 no adapter read`. That direction is conservative.
  - A partial read counts as a content read: `head -n 5` and `sed -n 1,10p` both count. The design
    does not measure how much was read.
  - Success is judged per event, and the returned text is judged per event too. In
    `cat A B` where `A` succeeds, the event reads as a read of `A`, whatever happened to `B`.
  - The needle proves that the file's first heading was returned, not that the file was
    returned whole; this is the partial-read residual above.
  - A heredoc body is tokenized as commands. A body line that looks like an execution gives a
    `FAIL`, and one that mentions a script gives an `UNVERIFIED`. Neither is a pass. A body that
    holds an unpaired quote, such as an English apostrophe, raises `ValueError` and gives
    `UNVERIFIED V-11.1 unparseable command`, which halts.
  - A `#` comment is ordinary text (`commenters = ""`). A comment line that mentions a script has
    `argv0` `#`, so it is unclassified and gives `UNVERIFIED` before the adapter read. That is
    conservative.
  - A wrapper outside the shell-wrapper rule (`env`, `timeout`, `nohup`, `exec`, `command`,
    `time`, `xargs`, `eval`, backticks, `perl -e`, `uv run`) makes a mentioning command
    unclassified, which gives `UNVERIFIED`, never a pass.
  - **Executing options of the non-executing names.** The screens close the members this design
    knows: `sed`'s `e` command, its `s///e` flag and its script files, and `rg`'s `--pre` and
    `-z`. The residual, stated exactly, is an option of one of the other twelve names (`cat`,
    `head`, `tail`, `nl`, `grep`, `ls`, `test`, `[`, `echo`, `printf`, `wc`, `stat`) that runs a
    program on the platform the smoke uses. None is known to this design, and the first
    rehearsal failure that shows one adds a screen, with its own case.
  - **A script name assembled at run time.** A command that runs an h-mad script without any
    token matching the mention regex is invisible to every rule here: the name comes from a
    variable, string concatenation or a glob (`python3 "$S"`, `python3 h-mad/scripts/h_mad_*`).
    No input-event classifier can see it.
  - **`SKILL.md` loaded without a tool call.** `08-skills.md` says grok *inlines* a skill body (up
    to 25,000 tokens). None of that shows in the input events, so step 5 prints `UNVERIFIED` for
    grok and the smoke halts. That may be the usual outcome for grok, and what an `UNVERIFIED`
    does is decision OD-b (§"Supersedes", "Decisions this design records"). A codex or agy host
    that injects the skill the same way gets `FAIL` (OD-1). Widening step 5 to an observed
    injection shape is a design change with its own rehearsal case, never an in-place edit during
    Phase 7.

`v112` is the plan's `v112`, unchanged in logic, moved into Python.

**Rehearsal cases.** They are committed under `rehearsal/` and run by `smoke_assert.py rehearse`
in Phase 6. Each case prints its verdict, and the Phase-6 document records them all.
Each case holds, unless it says otherwise, a successful `SKILL.md` read first, and for grok the
verbatim `available_commands` line below. Every read in a case returns text holding the file's
needle, and every script run carries `HMAD_HOST=<H>` inline, unless the case says otherwise. The
rehearsal runs with `--root` set to the checkout, so the needles are the real files' headings;
the grok adapter's needle is its `# grok runtime adapter` heading (D9.1). Each case changes one
thing, so each branch of the classifier has its own fixture (`invariants.base.md` §"Test
discrimination"):
- For each host (codex, agy, grok):
  - R1: adapter read, then a script run → `PASS`;
  - R2: a script run, then the adapter read → `FAIL … a script ran before the adapter was read`;
  - R3: no adapter read → `FAIL … no adapter read`;
  - R4: a `SKILL.md` read whose **output** mentions `h_mad_x.py`, then the adapter read, then a
    script run → `PASS`. This is the case that kills the text-matching form.
  - R6, filename-only negatives, four cases per host, each alone: a mention of the adapter by
    `test -f`, by `echo`, by `grep -l x`, or by `ls`; then a script run; then a real adapter
    read → `FAIL … a script ran before the adapter was read`. Each proves that its form is not a
    read.
  - R7, mention-not-execution, two cases per host, each alone:
    `sed -n 1,80p …/h_mad_state_write.py` or `grep h_mad_resume_decision.py h-mad/SKILL.md`,
    then the adapter read, then a run → `PASS`.
  - R8: `eval "python3 …/h_mad_x.py"` before the adapter read →
    `UNVERIFIED … unclassified command before the adapter read`.
  - R9: R1 with a `#hmad-beat` line interleaved. In codex it sits between `exec` and the command
    line; in grok and agy it sits between two events. → `PASS`.
  - R10: an adapter read with no success signal, then a script run →
    `FAIL … a script ran before the adapter was read`.
  - R11: R1 with no `SKILL.md` read → codex and agy `FAIL … no observed SKILL.md read`; grok
    `UNVERIFIED … no observed SKILL.md read` (OD-1).
  - R12, the host declaration (OD-4), two cases, each alone:
    (a) R1 with the script run's `HMAD_HOST=<H>` removed → `FAIL … no script call declared
    HMAD_HOST=<H>`; (b) R1 with it spelled `HMAD_HOST=claude` → the same `FAIL`.
  - R13, failed or empty reads (OD-2), three cases, each alone:
    (a) the adapter read is `cat <adapter> || true` with a success signal but returned text that
    is `cat`'s "No such file or directory" error, then a script run, then a real adapter read →
    `FAIL … a script ran before the adapter was read`;
    (b) the adapter read has a success signal and empty returned text (for grok and agy, the
    read tool completed with an empty content string), then a script run, then a real adapter
    read → the same `FAIL`;
    (c) R1 with the `SKILL.md` read replaced by a `cat …/SKILL.md || true` whose returned text is
    the error → as R11 (codex and agy `FAIL`, grok `UNVERIFIED`).
  - R14, tokenizer and exec-form cases (OD-3 and the delta review), each alone, placed before the
    adapter read and followed by it and a run:
    (a) `echo x # c`, a newline, then a script run → `FAIL … a script ran before the adapter was
    read`;
    (b) `echo ${#x}; <run>` → the same `FAIL`;
    (c) `cat y >> <adapter>; <run>` → the same `FAIL`, since a `>>` target is not a read;
    (d) `python3 2>err h-mad/scripts/h_mad_state_write.py` → the same `FAIL`;
    (e) `python3 -m h_mad_state_write` → the same `FAIL`;
    (f) `cat <(python3 h-mad/scripts/h_mad_state_write.py)` → the same `FAIL`;
    (g) `sed -e 'e python3 h-mad/scripts/h_mad_state_write.py' x` →
    `UNVERIFIED … unclassified command before the adapter read`;
    (h) `rg --pre python3 x h-mad/scripts/h_mad_state_write.py` → the same `UNVERIFIED`.
  - R15, output shape: an adapter read whose success line carries no returned-text field (grok:
    no `rawOutput`; agy: no `tool_info.output`) → `UNVERIFIED … output shape unobserved`. For
    codex, an `exec` line followed by a line that is not of the command shape →
    `UNVERIFIED … codex input shape unobserved`.
- grok only:
  - R5: R1 with every `available_commands` line removed → `FAIL … grok did not list h-mad`.
  - **The verbatim line.** Every grok case except R5 carries the first `available_commands` line
    of `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson`, **copied
    verbatim** with `grep -m1 '"type": *"available_commands"' <log>`. No grok fixture holds a
    hand-written `available_commands` line, so a reader that expects `commands[].name` fails grok
    R1. If the `grep` returns nothing, the fixtures are unbuildable and the rehearsal prints
    `FAIL`.
  - Grok R1 is therefore the verbatim-listing case (`PASS`), and grok R11 is the case that shows
    the listing alone never passes (`UNVERIFIED … no observed SKILL.md read`).
  - The grok `read_file` events in these fixtures copy the shape of the `read_file` line in the
    same log (`toolName`, `rawInput.target_file`, then a `tool_call_update` carrying the same
    `toolCallId` and `"status": "completed"`), with only the path changed.
- `v112`: the plan's four cases.
- **Replay on real artifacts** (`invariants.base.md` §"Incident replay"): `v111` over the three
  committed real logs. None of them is an h-mad status run. The expected verdicts below are
  predicted from a scan of their input events (DP14), and none of them is `PASS`:
  - the sibling grok probe log: `FAIL V-11.1 no adapter read`. Its only tool calls are one
    `read_file` and one `search_replace` on scratch files;
  - the agy log `plan-audit-v1-p2-agy.log`: `FAIL V-11.1 a script ran before the adapter was
    read`. Its `grep … h_mad_state_write.py` steps are non-executing, and a later
    `python3 h-mad/scripts/h_mad_extract_verdict.py …` step is an execution. Its two
    `#hmad-beat` lines are skipped;
  - `codex-text-8-exec.log`: `FAIL V-11.1 no adapter read`. Its `sed -n … h_mad_*.py` commands
    are non-executing.

  A replay that prints a different verdict is investigated before 7f: either the classifier or
  the prediction is wrong, and the Phase-6 document says which.

The remaining rehearsal fixtures are hand-made in the shapes those real logs show. A rehearsal case that does
not print its expected verdict blocks 7f. If `smoke_assert.py` changes after Phase 6, the
rehearsal is re-run, and the smoke record states that.

**Smoke script delta.** The plan's script is used with these changes:
- The `v111()`/`v112()` shell definitions are removed.
- Part 2's two calls become:

  ```bash
  P="$REPO/docs/03-analysis/probes/multi-host-runtime/smoke_assert.py"
  r=$(python3 "$P" v112 --out "$S/out" --record "$B_REC" --feature "$F"); test "$r" = "PASS V-11.2" || stop "${r:-UNREADABLE V-11.2 reason=no_output}"
  r=$(python3 "$P" v111 --host "$H" --log "$S/log" --root "$REPO"); test "$r" = "PASS V-11.1" || stop "${r:-UNREADABLE V-11.1 reason=no_output}"
  ```
- The pinned prompt's "declare `HMAD_HOST`" item is proved from the log by step 4 of the verdict
  (OD-4), never taken on the host's word.
- Part 1 gains `test -f "$P" || { echo "HALT smoke_assert.py absent from main"; exit 1; }`.
- `FAIL`, `UNVERIFIED` and `UNREADABLE` all take the same path. They are part-2 stops, so each
  calls `recover` (plan: "a stop in part 2 … calls `recover`, the only path that reverts"). An
  `UNVERIFIED` grok arm is therefore a halt that reverts, never a pass, and 7e never runs. If the
  orchestrator wants `UNVERIFIED` to halt **without** reverting, that is a change to the plan's
  part-2 rule and is not made here.
- A crash that prints nothing still halts with a named reason, through the `${r:-…}` default.

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
- **Rows.** Table rows are read with `host_parity.adapter_table` (D2.1). The test asserts that
  `problems` is empty and that exactly one row carries the id, and then reads that row's cells.
- **Fenced lines.** A pinned command line is looked for among the `body` events of
  `_fence_events` inside the located section, so prose that quotes the line does not satisfy it.
- **Each alternative is its own assertion.** Where a row below lists several tokens, each token is
  a separate parametrized case, so a sibling token cannot cover a missing one.

The pinned tokens, by AC:

| AC | file(s) · locator | asserted |
|---|---|---|
| AC-2.3, AC-5.3, AC-6.3 | 3 h-mad adapters · `advisor` row | status `not-applicable`; mapping contains `hmad-dispatch exec` and, per host, `collaboration.spawn_agent` + `fork_turns` (codex), `invoke_subagent` (agy), `spawn_subagent` (grok) |
| AC-2.4, AC-5.4, AC-6.4 | 3 handoff adapters · `task-tools` row | grok `mapped` + `todo_write` + `Ctrl+T`; agy `not-applicable` + `manage_task` + `.omc/notepad.md`; codex `not-applicable` + `.omc/notepad.md` + `update_plan` (as a lead) |
| AC-2.5, AC-5.5, AC-6.5 | 3 h-mad adapters · `session-id-env` row | all: `uuid.uuid4()` and `owned_elsewhere`; grok also `GROK_SESSION_ID` and `hook processes` |
| AC-9.3 | 3 h-mad adapters · `## Context budget and claims`, fenced lines | with `<sid-read>` the literal text `"$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"`, six cases, each alone: a fenced line holding both `--create` and `--claim <sid-read>`; one holding `--claim <sid-read>` without `--create`; one holding both `--beat` and `--session-id <sid-read>`; one holding both `--set` and `--session-id <sid-read>`; one holding both `--release` and `--session-id <sid-read>`; one holding both `h_mad_resume_decision.py` and `--session-id <sid-read>`. Also a fenced line holding `set -C`, `uuid.uuid4()`, `h-mad-session-id.<feature>` and `SID: NOT_MINTED`; the resume-oracle line precedes every `h_mad_state_write.py` line; no fenced line in the section holds `$SID`; and the prose phrases `once at bootstrap` and `never deleted or reused without the operator` |
| AC-9.3, OD-5 (executable) | 3 h-mad adapters · `## Context budget and claims`, fenced lines | in a `tmp_path` `git init` repository, with `<feature>` replaced by a fixture slug, `HMAD_SKILL_ROOT` set to the checkout's `h-mad`, and each command in its **own** `subprocess.run(["bash", "-c", line], timeout=…)`: the mint line prints `SID: MINTED`; a second run of it prints `SID: NOT_MINTED` and leaves the file's bytes unchanged; the `--create --claim` line, run in a later separate invocation, claims the feature with the file's id (asserted by reading `docs/.bkit-memory.json` directly); the resume-oracle line, run in a further separate invocation, prints neither `cannot_judge` nor `owned_elsewhere`. Control: the same oracle line with `<sid-read>` replaced by `""` prints `cannot_judge` |
| AC-2.2 (OD-9) | 6 adapters · every `not-applicable` row | the `mapping` cell, trimmed and with backticked spans removed, holds at least three words of two or more letters; it does not fully match `(?i)(n/?a\|not[- ]applicable\|none)\.?`; and it differs from the row's `source` cell. Residual: a three-word non-reason passes, and review owns whether the text is a reason |
| AC-9.3, AC-5.5 | h-mad grok · `## Context budget and claims` | `GROK_SESSION_ID` and the phrase `only after the live smoke records it present in the orchestrator's shell` |
| AC-5.1 | both grok files · `## Version and compatibility` | `1.0.41`, `compat.claude.skills`; h-mad also `compat.claude.hooks` |
| AC-5.2 | h-mad grok · `## The TDD gate` | `step5:grok_tdd_hook_unverified`, `toolInput`, `fails open`, `pytest`, and the reason-(i) token of the `REFUSAL_FORM_AT_BASE` row (D9.2) |
| AC-5.6 | h-mad grok · `claude-projects-store` row | `not-applicable`, `~/.grok/memory`, `h_mad_check_memory_index.py` |
| AC-5.7 | both grok tables · every `source` cell | matches `\b\d\d-[a-z-]+\.md\b`, or contains `grok inspect`, or starts `observed:` |
| AC-7.1, AC-7.3 | both `SKILL.md` · `## Host runtime` | contains all three `references/<host>-runtime.md` paths; a renamed or doubled heading fails loudly |
| AC-8.4 | 3 h-mad adapters · `## Context budget and claims` | `CTXBUDGET: UNKNOWN`, `80%` and `substitute: none`; grok also `/context` and `not an orchestrator gate` |
| FR-8, AC-8.1 (executable) | 3 h-mad adapters · `## Context budget and claims`, fenced lines | exactly one fenced line matching `^HMAD_HOST=<h> python3 "\$HMAD_SKILL_ROOT/scripts/h_mad_context_budget\.py"$`, with `<h>` the adapter's own concrete value and never the text `<host>`. The test then **runs** that line with `bash -c`, `HMAD_SKILL_ROOT` set to the checkout's `h-mad`, `HOME` set to an empty `tmp_path` and `subprocess.run(timeout=…)`, and asserts stdout is exactly `CTXBUDGET: UNKNOWN reason=host_unsupported host=<h>` |
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
| Live-smoke record | written at `docs/03-analysis/multi-host-runtime.live-smoke.md` (the spec's path); committed at `docs/archive/<YYYY-MM>/multi-host-runtime/multi-host-runtime.live-smoke.md` (the plan's) | new | FR-11 |

**When the smoke record is archived (orchestrator decision OD-7; §"Supersedes" item 10).** 7c runs
before 7f, and the smoke runs after 7f, so 7c's `mv docs/03-analysis/${FEATURE}*` has already run
when the record is written. The plan's docs-only step between the smoke and 7e therefore runs, in
this order, on `main`:
1. `A=$(ls -d docs/archive/*/multi-host-runtime)`. This must name exactly one directory, the one
   7c created; otherwise it prints `HALT archive directory not unique` and stops. It reads the
   directory rather than recomputing `<YYYY-MM>`, so a month boundary between 7c and the smoke
   cannot split the archive.
2. `mv docs/03-analysis/multi-host-runtime* "$A"/`. This is 7c's own glob and target, without 7c's
   `2>/dev/null || true`, so a failed move is not masked. The glob does not match
   `docs/03-analysis/probes/` (§"Supersedes" item 4).
3. `test -f "$A/multi-host-runtime.live-smoke.md"` and
   `test ! -e docs/03-analysis/multi-host-runtime.live-smoke.md`. If either fails, it prints
   `HALT smoke record not archived` and stops.
4. The docs-only commit on `main`, holding the record at its archive path, before 7e pushes.

So the record is written at the spec's path and committed at the plan's path, in the same local
integration sequence and before the push. The plan's wording "written after 7f into the directory
7c created" is the one sentence this changes; the plan owes that restatement.

Deliberately untouched (plan): `h-mad/hooks/h-mad-tdd-gate.sh`,
`h-mad/hooks/h-mad-codex-tdd-gate.py`, `h-mad/hooks/h-mad-advisor-warn.sh`,
`h-mad/scripts/hmad-dispatch.sh`, `h-mad/references/agent-substrate.md`, the three existing
mutation specs, and `check_siblings`' body.

## Implementation Order

1. **Before the design gate clears** (plan Next Steps): commit `calibrate.sh`, `seed.json` and
   `seed_coverage.py` (per-entry mode). They need no feature code. This step is the
   orchestrator's, because this document's author writes only the design. It had not happened
   when design audit cycle 1 ran, so that cycle checked DP1 and DP2 against scratch readings.
   It had still not happened at `76e7af19`: `ls docs/03-analysis/probes/multi-host-runtime` →
   "No such file or directory". The design gate cannot clear under this order until it does.
2. **5c** (plan "Rebase, then baseline"):
   - rebase;
   - record `<base>`;
   - run `calibrate.sh <base>` and `seed_coverage.py --sha <base> --registry seed.json`;
   - re-run P4, P5, P6, P9 and P15, and the suite baseline;
   - from P5, record the gate's refusal form at `<base>` as `REFUSAL_FORM_AT_BASE` (D9.2), or halt
     on a reading outside its three rows;
   - run `--check-anchors` over both spec directories (the Anchors command in §Test Plan);
   - take the AC-6.1 gap table from `git show <base>:<adapter>`;
   - run the four-link gate;
   - write the AC-4.6 record.
3. **Strand 1.**
   - First, `test_host_construct_parity.py`. Its RED is a collection error:
     `ModuleNotFoundError: No module named 'host_parity'`. That is the only RED possible before the
     module exists, and it is recorded as such.
   - Then `host_parity.py`, with no registry yet. Now the stated reasons appear: the registry node
     is RED with `REGISTRY_UNREADABLE reason=missing_file`, and each adapter node is RED on its
     vacuity guard (§Test Strategy), because no adapter stage ran.
   - Then the registry. Registry node GREEN; adapter nodes RED on
     `TABLE_MISSING reason=no_heading`.
   - Take the `seed_coverage.py --branches` reading at `<base>`.
4. **Strand 2** (three independent leaves):
   - `h_mad_host.py`, then the D4 and D5 wiring, with `test_h_mad_host_declaration.py` RED first;
   - `h_mad_install_check.py` D6 with `conftest.py` D7, with `test_h_mad_install_check_roots.py`
     RED first;
   - after each leaf, run `--check-anchors` over both spec directories.
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
  - `CTXBUDGET: UNKNOWN reason=unknown_host host=<value>`, where `<value>` is bare when it fully
    matches `[A-Za-z0-9._-]+`, and a JSON string otherwise (§"Supersedes" item 9);
  - `AGY_SIBLING_COLLISION:<link> kind=<NOT_SYMLINK|DANGLING|WRONG_CHECKOUT>`;
  - `SID: MINTED` / `SID: NOT_MINTED` (the adapters' mint line, §D9.2);
  - `BYTE-IDENTITY: …`, `PASS|FAIL|UNVERIFIED|UNREADABLE V-11.1 …`,
    `PASS|FAIL|UNREADABLE V-11.2 …`, `REHEARSAL: …` (probes).
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
  - `checkout_skill_names(repo) -> list[str]`;
  - `split_agy_root(lines, skills_dir, names, installed) -> tuple[list[str], list[str]]`;
  - CLI `--agents-skills-dir PATH` and `--agy-skills-dir PATH`, whose defaults come from
    `default_host_roots()` at call time.
- `host_parity` (test-side): as in D2.1, including the public `adapter_table(text) -> Table`
  that both `check()` and `test_host_runtime_docs.py` use.
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
  - an unobserved host input or output shape, an unparseable line or command, an unclassified
    command that mentions a script, or a grok `SKILL.md` load with no observed read gives
    `UNVERIFIED V-11.1`, which halts and is never a pass; on codex and agy a missing `SKILL.md`
    read is `FAIL` (OD-1);
  - an existing session-id file makes the mint print `SID: NOT_MINTED`, a halt, and never an
    overwrite (§D9.2);
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
- `test_budget_unknown_host_encoding[zzz|Grok| grok|zzz-newline]`, pinning both forms of OD-a
  (§"Supersedes", "Decisions this design records"):
  `zzz` → `host=zzz` and `Grok` → `host=Grok` (bare); `" grok"` → `host=" grok"` and `"zzz\n"` →
  `host="zzz\n"` (JSON). Each case also asserts that stdout is exactly one line;
- `test_budget_unknown_host_precedes_window_check[zzz]` (AC-8.5 for an unknown value; fixture (d)
  covers the declared ones);
- `test_decide_cannot_judge_without_session_id[<host> × <live-foreign-owner|no-owner|absent-file|unreadable-file|absent-feature>]`;
- `test_decide_routes_normally_with_session_id[codex|agy|grok]`, the control that kills an
  unconditional `cannot_judge`;
- `test_decide_unknown_host_without_session_id[zzz × <live-foreign-owner|no-owner>]` (AC-9.1,
  orchestrator decision OD-10);
- `test_decide_empty_session_id_is_no_id[grok × <live-foreign-owner|no-owner>]`, each run with
  `session_id=""` (AC-9.1, OD-10);
- `test_resume_decision_cli_under_grok`.

**`test_h_mad_install_check_roots.py`:**
- `test_agents_root[<correct|copy|dangling|other-checkout|absent>]` (AC-10.1);
- `test_empty_root_option_is_unreadable[agents|agy]` (AC-10.3);
- `test_empty_env_override_is_unreadable[agents|agy]` (AC-10.3, OD-10): no option passed, and
  `HMAD_AGENTS_SKILLS_DIR=""` or `HMAD_AGY_SKILLS_DIR=""` respectively → `INSTALL: UNREADABLE`,
  exit 2;
- `test_explicit_option_beats_env_override[agents|agy]` (AC-10.3, OD-10): the option names a
  `tmp_path` root holding a copy of `h-mad`, and the override variable names a different
  `tmp_path` root holding a correct link. The run reports the option root's issue, so a resolver
  that lets the variable win reads the clean root and passes wrongly;
- `test_agy_root_cell[<12 AC-10.5 cells>]`;
- `test_claude_root_debugger_copy_still_fails` (AC-10.6);
- `test_absent_roots_add_no_line`;
- `test_env_override_is_read`;
- `test_default_roots_resolve_to_documented_paths`;
- `test_detail_lines_sorted_and_after_verdict`;
- `test_check_without_root_keywords_reads_no_new_root`;
- `test_unattributable_sibling_line_stays_an_issue`;
- `test_checkout_names_agree_with_check_siblings` (D6).

**`test_host_runtime_docs.py`:** one test per row of D12's table, parametrized per adapter and
per token wherever a row lists several.

**Mutation specs.** Each is scored on `MUTATION: ALL_CAUGHT`, with anchors confirmed by
`--check-anchors`:

| Spec | Mutation classes (each one mutant per member) | Killed by |
|---|---|---|
| `host_parity.json` | each disjunct's detection disabled alone (42, incl. splits); each suppression rule (a)–(e) removed; each axis dropped from `CATCH_ALL_AXES`; each `A4_BRANCHES` entry dropped; each suffix replaced by `.*`; one expander alternative dropped; `CELL_EMPTY`'s case fold removed; the table search made fence-blind (a `^\|` scan over the raw section); `BAD_PATTERN`'s field-checks-ran filter removed; the backtick strip moved after the `cell_count` id read | its own fixture; the sample-count assertion; the mixed-case fixtures; a fixture holding a pipe table inside a fence before the real one; the `missing_key:pattern` fixture; the backticked-id `cell_count` fixture |
| `host_declaration.json` | `classify_host` given `.strip()`, `.lower()`, or `""`→unknown; W1 check moved after the transcript lookup, the usage read, the `--window` check; W2 check moved after the state read, after the feature lookup; `_host_verdict` ignoring `session_id`; the `cannot_judge` branch removed; the unknown value always printed bare; always JSON-encoded; `re.fullmatch` replaced by `re.match` with `^…$` | fixtures ` grok`, `Grok`, `""`; (b), (c), (d); absent-file and absent-feature fixtures; `test_decide_routes_normally_with_session_id`; AC-9.1; the ` grok` encoding case; the `zzz` encoding case; the `zzz-newline` encoding case |
| `install_check_roots.json` | the agy name split inverted; the split applied to the Claude root; the env override read dropped; an empty override read as unset; the override preferred over an explicit option; the trailing space removed from `split_agy_root`'s prefix; detail lines printed before the verdict | AC-10.5 cells; AC-10.6; the override control; `test_empty_env_override_is_unreadable`; `test_explicit_option_beats_env_override`; a fixture with skills `h-mad` and `h-mad-x`; the ordering test |

**Commands:**
- `env -u HMAD_HOST python3 -m pytest -q h-mad/tests handoff/tests handoff/scripts`, the full
  coupled suite (AC-12.1), run with the interpreter the plan pins and with `HMAD_HOST` explicitly
  removed, so the operator's shell cannot decide which branch the suite exercises;
- **AC-8.3**, the whole existing module, twice, each read by its pytest summary line:
  - `env -u HMAD_HOST python3 -m pytest -q h-mad/tests/test_h_mad_context_budget.py`;
  - `HMAD_HOST=claude python3 -m pytest -q h-mad/tests/test_h_mad_context_budget.py`.

  Each run passes when its summary has no `failed` and no `error`, and both report the same
  `passed` count. A run that collects nothing fails. The module's `_run` helper starts the script
  with no `env=`, so `HMAD_HOST=claude` reaches every subprocess the module starts (DP13);
- **Anchors**, both spec directories:
  `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json`
  and `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors handoff/tests/mutation-specs/*.json`,
  each read by its `ANCHORS:` token. The token must be `ANCHORS_OK` with `drifted=0`;
- the plan's node-id floor and append-only `numstat` check.

## Invariant Compliance

**Base invariants (`h-mad/invariants.base.md`):**
- **Audit-gate signal discipline.** Complies. Every new verdict is a stdout token with exit 0,
  and exit 2 is reserved for no-verdict states, which the existing `UNKNOWN` and `UNREADABLE`
  precedents already use.
- **Single-source contract.** Complies:
  - host classification is one function;
  - agy-root classification reuses `check_siblings`;
  - the adapter table parser is one public function, `host_parity.adapter_table`, called by the
    gate and the doc tests;
  - `v111` and `v112` are one file used by the smoke and the rehearsal;
  - one exception, stated with its guard: `checkout_skill_names` repeats `check_siblings`' glob
    expression, because `check_siblings`' body must stay byte-identical for its anchors. The
    agreement test (D6) holds the two together.
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
  `handoff` gains no runtime read of `h-mad`. The new install paths `~/.agents/skills/...` (codex)
  and `~/.gemini/config/skills/...` (agy) were **not** allowed by the rule as it stood at design
  v1.1; its only exception then was `~/.claude/...`. The operator approved amending the exception
  (orchestrator decision OD-8), and the amended text in `.h-mad/invariants.md` §"Skill
  self-containment" now names `~/.claude/...` for Claude Code, `~/.agents/skills/...` for Codex
  and `~/.gemini/config/skills/...` for agy, "each overridable by its documented environment
  variable" (commit `76e7af19`, on `main` directly after `a83ed085`). The two new roots are
  overridable by `HMAD_AGENTS_SKILLS_DIR` and `HMAD_AGY_SKILLS_DIR` (D6), which is the amended
  rule's condition. The grok adapter's `~/.grok/...` paths are prose that names grok's own store
  and home; no script or test reads them.
- **Skill manifest integrity.** Complies. Both `SKILL.md` contracts are updated where behaviour
  changes: routing names grok, and the `cannot_judge` row names its second cause. Frontmatter is
  untouched.

## Verified premises (design-level)

Each premise was run at `6478b8b5`, on the main checkout with a clean `h-mad`/`handoff` tree.
`git diff --name-only 2f262f8a 6478b8b5 -- h-mad handoff | wc -l` → 0 files, so plan v1.2's tree
premises stand. `main` advanced to `dfd5f02e` while this document was written, and
`git diff --name-only 6478b8b5 dfd5f02e -- h-mad handoff | wc -l` → 0 files, so every reading below
also holds there. The v1.1 revision re-ran the readings it adds or changes at `1ef1a782`, and
`git diff --name-only 6478b8b5 1ef1a782 -- h-mad handoff | wc -l` → 0 files. The v1.2 revision
re-ran what it adds at `76e7af19`, and `git diff --name-only 1ef1a782 76e7af19 -- h-mad handoff |
wc -l` → 0 files.

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
  - branch × declared-skill cells, with the population named, because the two readings differ
    on scope alone:
    - over the 13 **branching** entries: 61 cells, of which 25 are zero;
    - over **all** 54 branches, which is what `seed_coverage.py --branches` prints: 72 cells, of
      which 25 are zero. The 9 non-branching entries add 11 cells: `skill-call` and `claude-md`
      declare both skills, and the other 7 declare one. None of those 11 is zero, per the spec
      seed table's hit columns;
  - 14 branches have 0 occurrences in every skill that declares them.

  The Phase-6 comparison uses the all-branches population.

  **Moves** with either `SKILL.md` and with any registry change. It is re-derived by
  `seed_coverage.py --branches`.
- **DP3 — existing anchors, both directories** (at `1ef1a782`). The class is every spec whose
  `file` names a file this feature edits, found by a JSON walk over `mutations[].file` matched by
  basename against the edited files:
  - `h-mad/tests/mutation-specs/`: 16 spec files, 14 of them naming `SKILL.md`. `--check-anchors`
    over all 99 spec files → `ANCHORS: ANCHORS_OK specs=99 mutations=907 ok=907 drifted=0`;
  - `handoff/tests/mutation-specs/`: 3 spec files naming `SKILL.md` (`read_auto_resolve.json`,
    `skill_body_renderer_args.json`, `takeover_mode.json`). `--check-anchors` over all 7 spec
    files → `ANCHORS: ANCHORS_OK specs=7 mutations=69 ok=69 drifted=0`.

  **Moves** with any spec added to either directory. The three specs over the touched scripts
  are read in detail below.
- **DP3a — the three script specs.** `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors
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
  - 9 `available_commands`. The first has the keys `commands`, `tools` and `type`, and its
    `commands` is a list of 316 elements, all of them `str`. The first element is `"compact"`,
    and `"h-mad"` is a member;
  - 70 `thought`, 21 `text`, 2 `tool_call`, 4 `tool_call_update`, 3 `usage`, 1 `end`;
  - 0 `system`, and 0 lines that are not JSON.

  The 2 `tool_call` events are one `read_file`, whose `rawInput` key is `target_file`, and one
  `search_replace`. Each is followed by a `tool_call_update` with the same `toolCallId` and
  `"status": "completed"`. There are 0 `run_terminal_command` events, because the probe asked
  only for a read and an edit. That zero is incidental, and it is why §D10 treats the shell key
  as unobserved.

  `grep -n 'streaming-json\|stream-json' ~/.grok/docs/user-guide/14-headless-mode.md` places the
  `system`/`init` line under §"streaming-messages-json". The sibling design's `exec grok` argv line
  reads `--output-format streaming-json`.
- **DP6 — host logs carry tool output.**
  - grok: that log's `tool_call_update.rawOutput` holds `FileContent.content`.
  - agy: `docs/03-analysis/probes/grok-codex-fallback/plan-audit-v1-p2-agy.log` has tool steps
    shaped `step_update.{step_type:"tool", tool_name, tool_info:{parameters, output}}`, with the
    lifecycle in the key `state`: 16 `ACTIVE` and 16 `DONE`. All 32 are `run_command`, with the
    command in `parameters["CommandLine"]`. There are 0 `view_file` steps, although `view_file`
    is in the log's `init.tools` list. The log also holds 2 lines that are not JSON, and both
    are `#hmad-beat … agy running …s` lines.
  - codex: `h-mad/tests/fixtures/codex-text-8-exec.log` has 8 lines equal to `exec`. Each is
    followed by a `/bin/zsh -lc "…" in <cwd>` command line and then a ` succeeded in …` line; the
    output lines come after that. It has 0 failed-command lines, so the failure form is
    unobserved, and §D10 counts anything other than ` succeeded in` as no success.
  - `hmad-dispatch.sh` writes the beat with `printf '#hmad-beat %s %s running %ss\n'` into the
    same log (`grep -n 'hmad-beat' h-mad/scripts/hmad-dispatch.sh`).
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
  | `send_message` | 39 (read at `1ef1a782`) |

  These are leads, not documentation. Since v1.2 no `M` cell rests on one alone (DP16).
- **DP16 — codex evidence beyond binary strings** (v1.2, orchestrator decision OD-6; read on this
  host with the tree at `76e7af19`; `~/.codex` is operator-local and uncommitted, so the readings are stamped
  here and re-verified at the live smoke):
  - `codex --version` → `codex-cli 0.157.1`. `codex --help` lists the commands `agents` ("Browse
    all agent sessions…"), `exec`, `resume`, `fork` and others, and its `-c` text names
    `~/.codex/config.toml`. It names no skill, `AGENTS.md`, slash command or todo tool.
    `grep -i 'skill\|AGENTS.md\|compact\|/new\|todo\|spawn'` over the `--help` of `codex`,
    `exec`, `review`, `features`, `plugin`, `debug`, `fork` and `resume` → 0 matching lines.
  - `codex features list` → `multi_agent stable true`, `memories stable false`,
    `hooks stable true`, `skill_search stable true`; `grep -ci 'todo\|update_plan\|task'` → 0
    matching lines.
  - `ls ~/.codex` holds `AGENTS.md`, `hooks.json`, `memories` and `skills`. There are no codex
    docs on disk under the cask's `codex-resources/`, which holds only `voice` and `zsh`.
  - Rollouts, `~/.codex/sessions/**/*.jsonl`: 161 files. Their `cli_version` values are 15
    distinct versions from 0.116.0 to 0.144.1; 0 files at 0.157.1
    (`grep -rhoE '"cli_version":"[0-9.]+"' | sort -u`).
    Counts are files, by `grep -rlF <needle> | wc -l`:
    - `fork_turns`: 41 files, newest at 0.144.1. The injected multi-agent instructions read "You
      can use `spawn_agent` to create a new agent, `followup_task` …, and `send_message` to pass a
      message to a running agent without triggering a turn" and name the `fork_turns`
      parameter; the same file carries `"namespace":"collaboration"`;
    - `"name":"spawn_agent"` as a call: 1 file, but 0 `function_call` events named
      `spawn_agent` or `send_message`. The `function_call` names across all rollouts are
      `exec_command` 7986, `write_stdin` 895, `update_plan` 25, `list_mcp_resources` 1,
      `list_mcp_resource_templates` 1 (occurrences);
    - `update_plan` calls: 9 files, newest at 0.142.0;
    - `<skills_instructions>`: 160 files. Their "How to use skills" text says a skill is used
      when the user names it "with `$SkillName` or plain text", and each entry gives its
      `SKILL.md` location. Skill paths under `/Users/kimhawk/.agents/skills/<name>/SKILL.md`:
      4249 occurrences in 122 files, newest at 0.144.1. Paths under `~/.codex/skills/`: 3219
      occurrences. 0 of them name `h-mad` or `handoff`, since neither link exists (DP10);
    - `# AGENTS.md instructions for`: 160 files, newest at 0.144.1;
    - `"type":"compacted"`: 27 files, newest at 0.144.1. This shows compaction happened, not
      that `/compact` was typed.
  - `~/.codex/history.jsonl`: 840 lines, 0 whose `text` begins `/`.
  - Why the zeros are zero, and whether that matters. The 0 rollouts at 0.157.1 are
    incidental: no codex session has run on this host since that upgrade. It is load-bearing for
    every `observed:` codex cell, which is why V-11.1 and the live smoke re-verify at 0.157.1. The
    0 `/` history lines may mean either that no slash command was typed or that history does not
    record them; neither reading is evidence for a reset command, so the row is `N`.
  - The needle premise of §D10: `grep -m1 '^# '` of `h-mad/SKILL.md`,
    `h-mad/references/codex-runtime.md` and `h-mad/references/agy-runtime.md` gives three H1
    lines. Each occurs 0 times, by `grep -c -F -x`, in the other two files.
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
  - `10-hooks.md` §"Output (Blocking Hooks)": "The canonical `permissionDecision` decides when
    present" (`grep -n permissionDecision`), which D9.2's form-(b) row rests on.
  - `08-skills.md`: "Grok inlines at most the first 25,000 tokens of a skill body", which D10's
    `SKILL.md` residual rests on. `01-getting-started.md` names `run_terminal_command` as the
    shell tool and `read_file` as the read tool.
- **DP13 — AC-8.3 runs today.** With `/opt/anaconda3/bin/python3`, at `1ef1a782`:
  `env -u HMAD_HOST … -m pytest -q h-mad/tests/test_h_mad_context_budget.py` → `31 passed`, and
  `HMAD_HOST=claude …` on the same module → `31 passed`. `_run` in that module is
  `subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)`, with no
  `env=`, so the variable reaches the script. **Moves** with the module; W1 must leave both
  readings equal.
- **DP14 — real-log input scan** (at `1ef1a782`). This is a scratch walk of the three replay logs'
  input events for script, adapter and `SKILL.md` names. It is the basis of D10's predicted replay
  verdicts, and the Phase-6 rehearsal re-derives them with `smoke_assert.py`:
  - agy: steps 8, 16 and 18 are `grep -n … h-mad/scripts/h_mad_*.py`, which is non-executing, and
    step 20 is `echo … ; python3 h-mad/scripts/h_mad_extract_verdict.py …`, which is an execution.
    No step names `agy-runtime.md`;
  - codex: two command lines mention an `h_mad_*.py` name, both as `sed -n` operands. The one at
    `sed -n '1,110p' h-mad/tests/test_h_mad_collect_report_docs.py` is excluded by the mention's
    left guard. No command names `codex-runtime.md`;
  - grok: no input names a script, an adapter or `SKILL.md`.
- **DP15 — `h_mad_state_write.py` argument shapes.** Its `add_argument` lines: `--claim`
  (`metavar="SESSION_ID"`), `--release` (`store_true`), `--beat` (`store_true`), `--set`
  (append, `KEY=VALUE`), and `--session-id`. The help text says `--session-id` is required with
  `--beat`, needed by `--release` to release a session's own live claim, and optional with
  `--set`, where it refreshes the heartbeat. `h_mad_resume_decision.py` is called with
  `--state … --feature … --session-id …` (`h-mad/SKILL.md`, the resume-oracle command).

## Version History
- v1.0: Initial design draft (2026-09-28) from spec v1.2 (b51c5b2a) and plan v1.2 (e32ffe5c); premises executed at 6478b8b5 (tree unchanged at dfd5f02e). Registry, host_parity checker (find_heading/fence_aware_end/_fence_events table parse, closed branch-expansion grammar reproducing P2b), shared h_mad_host classifier, W1-W3 host/root checks keeping all 17 existing mutation anchors unique, agy root by partitioning check_siblings, 22x3 construct matrix, D12 doc-test token table, probe sidecar. Supersedes the plan on nine items: grok V-11.1 reads available_commands (exec grok emits streaming-json, no init line); v111 orders input events not log text (logs carry tool output); smoke_assert.py single file; rehearsal in Phase 6; 42 kind fixtures (6 splits); h_mad_host module; agy partition; AC-12.2 on both arms; unknown host JSON-encoded.
- v1.1: Design audit cycle 1 repairs (2026-09-28; codex p1 9 must, teammate 8 must/19 should; premises re-run at 1ef1a782). V-11.1: grok commands is a list of plain strings (listing = precondition only); every host needs an observed successful content read of the adapter before the first execution and of SKILL.md, else FAIL/UNVERIFIED; simple commands classified by argv (execution/content read/non-executing/unclassified), beat lines skipped, unparseable lines halt; UNVERIFIED/UNREADABLE tokens; rehearsal R6-R11, every grok case carrying a verbatim probe-log available_commands line; real-log replay verdicts predicted. BAD_PATTERN reads only elements whose field checks ran; backtick strip before the cell_count id. adapter_table public and shared with doc tests. split_agy_root takes names (checkout_skill_names + agreement test). FR-8 unknown host bare on fullmatch [A-Za-z0-9._-]+ else JSON. AC-8.3 full module run unset and claude; AC-8.4 substitute: none, grok /context a manual action not a gate; AC-9.3 per-argument fenced lines pinned; FR-8 runnable HMAD_HOST=<h> line executed by the doc test; AC-5.2 reason (i) keyed on the refusal form at base (permissionDecision documented by 10-hooks.md, contradicting plan Risks). Anchors checked over both spec directories. Spec restatements listed in the design. DP2 population stated (61 branching / 72 all). Live-smoke record path aligned to spec (docs/03-analysis/multi-host-runtime.live-smoke.md; archiving after 7c left to the orchestrator).
- v1.2: Final corrective revision after design audit round 2 (2026-09-28; codex p1 v2 12 must/1 should, delta review v1.1 3 must/10 should; not re-audited; premises re-run at 76e7af19). V-11.1: skill-load miss is FAIL for codex/agy, UNVERIFIED for grok only (OD-1); a read counts only with a success signal AND returned text holding the file's first heading (needle from --root), so cat A || true and empty tool reads are not reads (OD-2); tokenizer commenters="", redirect operators incl. >> and fd digits, process substitution, python -m, print-only sed screen and rg --pre/-z screen, residuals stated exactly (OD-3); step 4 requires an execution carrying inline HMAD_HOST=<H> (OD-4); codex command-line shape check; rehearsal R11 split, R12-R15 added. Session id minted once under set -C into the git dir file h-mad-session-id.<feature> and read inline on every call, oracle line first, --create --claim for start_fresh, executable cross-invocation doc test (OD-5). Codex matrix cells re-sourced to codex --help / features list at 0.157.1 and observed 0.144.1 rollouts (DP16); session-reset-command codex now N (OD-6). Live-smoke record written at the spec path, archived by re-running 7c's mv and committed before 7e (OD-7, Supersedes item 10). Invariant compliance cites the amended path exception (OD-8). Every N cell states its reason, AC-2.2 reason doc test (OD-9). AC-9.1 zzz and empty-id pairs, AC-10.3 empty-env and option-over-env fixtures (OD-10). OD-a/OD-b defined; spec restatements for the V-11.1 verdict set, FR-3 reason field and AC-5.2 rc 2 (exit 2); fence indent rule; NDJSON log assumption; overview on spec v1.3.
