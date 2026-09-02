# Design: doc-block-exec

## Executive Summary

A single stdlib-only module, `h-mad/scripts/h_mad_doc_block_exec.py`, exposing `extract` /
`substitute` / `run_block` / `main`, which selects a bash fence by (document, heading, `hmad:exec`
tag, optional ordinal), applies an explicit substitution map, and runs the block via
`subprocess.Popen(start_new_session=True)` in a `mkdtemp` cwd — printing one `DOCBLOCK:` verdict
line and refusing on every condition under which it would measure nothing.

## Overview

The design intent is that **selection is narrow and refusal is cheap**. Every branch that cannot
produce a real measurement returns before `bash` is ever spawned, so a caller can never receive a
plausible-looking zero from a run that did not happen. The two constraints that shape the code are
the opt-in tag (no API accepts a directory, glob, or all-blocks flag) and the ban on external
time-bounders (the bound is `Popen.communicate(timeout=…)` plus `os.killpg`).

One decision worth stating up front: `h-mad/tests/docsections.py` already contains a fence-aware
section bounder (`_fence_aware_end`), and this module **does not import it**. A `scripts/` module
importing from `tests/` inverts the dependency and would break a bare clone that ships without
tests.

**That choice does not come for free, and two drafts got the price wrong before this one.** v1.0
claimed self-containment while omitting any equivalence test — the violation the Single-source
contract names. v1.2 added a differential test, which is **not achievable**: `_fence_aware_end`
toggles on any ```-prefixed line, so on an unbalanced inner quote inside a four-backtick fence it
stops early, while AC-1.6 requires the new scanner not to. Measured on the real helper:

```
balanced   4-backtick : bound reaches the closing ````   (even toggle count masks the bug)
UNBALANCED 4-backtick : bound = '\n````bash\n```bash hmad:exec\n'   <-- cut at an IN-FENCE '## Not a heading'
```

Byte-identical bounds and AC-1.6 cannot both hold, so a differential test would have failed on the
very shape AC-1.6 exists for.

**Resolution: satisfy the invariant's FIRST branch — one authoritative implementation all surfaces
call.** This module owns the bounder; `h-mad/tests/docsections.py` imports it and keeps its
`titled_section`/`section_from` signatures. The dependency that was rejected was `scripts/` →
`tests/`; `tests/` → `scripts/` is the correct direction and was available all along. This also
fixes a latent bug in `docsections` rather than duplicating it, and no existing test pins the
early-exit behaviour (verified by grep before proposing the change).

## Architecture Overview

```
caller (test, or operator on the CLI)
        │
        │  (doc_path, heading, index?, subs?, timeout?)
        ▼
   extract()  ──────────►  [Block, …]          PURE SCAN, fence-aware
        │                    .text .shell .lineno .info
        ▼
   select(blocks, index) ─── POLICY: 0 ──► NOT_FOUND ; >1 no index ──► AMBIGUOUS
        ▼ exactly one
  substitute()  ─────────►  text'              literal replace, count each key
        │  every key present?  no ──► SUBST_MISSING
        ▼ yes
   run_block()
        ├── mkdtemp(0700) ──────────────── cwd
        ├── Popen(["bash", *flags, "-c", text'], start_new_session=True)
        ├── communicate(timeout) ─── TimeoutExpired ──► killpg(SIGKILL) ──► TIMEOUT
        └── finally: rmtree(cwd)
        ▼
     Result(rc, stdout, stderr, shell)
        ▼
   main() ─────────────►  one `DOCBLOCK:` line on stdout;  exit 0 (RAN) | 2 (else)
```

Refusals are ordered so that nothing irreversible happens before the last one: info-string
validation and stream-path writability are both checked **before** `bash` is spawned.

## Detailed Design

### Info-string grammar

An opening fence is `` ```bash `` optionally followed by whitespace-separated tokens:

```
```bash hmad:exec
```bash hmad:exec shell=plain
```

- The bare token `hmad:exec` is the opt-in marker. Its absence means the fence is invisible to
  `extract` — not an error, simply not a candidate.
- `shell=strict` (the default when absent) → `bash -euo pipefail -c`.
- `shell=plain` → `bash -c`, which is how an operator's paste actually runs.
- Any other token, or `shell=` with any other value, is `BAD_INFO` — but **only on a fence that
  carries `hmad:exec`**. Validation follows opt-in: an untagged fence is not a candidate, so its
  info string is never inspected and an unrelated ` ```bash --frozen ` elsewhere in the tree can
  never make this tool refuse. On a tagged fence it is **not** ignored: a typo'd key that silently
  falls back to a default runs the block under a mode nobody chose.

### Scanning (`extract`)

One pass over the lines, carrying `in_fence` **and the opening fence's backtick run length**. A
naive "any line starting with ``` toggles" is wrong and would corrupt the state on a document this
feature must handle: CommonMark opens a fence with a run of *N* ≥ 3 backticks and closes it only
with a run of ≥ *N*, so a fence opened with four backticks legitimately contains ``` lines as
body text. This design's own documents contain exactly that shape, because they quote fenced
examples. So:

- an opening fence records `n = len(run)`; while open, only a line whose leading run is ≥ `n`
  **and** carries no info string closes it;
- while `in_fence` is true, no line is examined as a heading or as an opener.

That is what makes AC-1.6 structural rather than a special case: a body quoting
` ```bash hmad:exec ` is inside a fence and is never read as an opener, and a *longer* enclosing
fence keeps it that way.

Heading bounding: locate the line equal to `heading` (exact match, stripped of trailing
whitespace); its level is the count of leading `#`. **If more than one line matches, `extract`
raises `AmbiguousHeading(n)` rather than taking the first** — duplicate headings are real in this
tree (`h-mad/invariants.example.md` has two of them), and picking one would execute a tagged block
from the wrong section. The opt-in tag guards *which block*; it cannot guard *which section*. **This is ATX-only by design and by
limitation**: a Setext heading (text underlined with `===`/`---`) is not recognised, so a document
using them would bound wrongly rather than loudly. Every document in these skills is ATX, and the
AC-1.8 differential test covers the assumption from the other side — `docsections.py` makes the
same one, so a divergence in either would surface there. The section ends at the next line that is a
heading of the **same or shallower** level *and* is not inside a fence. Candidates are the tagged
opening fences between those two offsets.

Candidate *counting* is where `extract` stops. Choosing among them is `select`'s job (see API):
`index` is 1-based and optional, and with no `index` zero candidates raise `BlockNotFound`, one
returns that block, and more than one raises `AmbiguousBlock(n)`. Ambiguity is never resolved by
taking the first, because a reordered document would then silently re-point the address at a
different block.

### Substitution

`str.replace` — literal, never regex, so a key containing `.` or `[` behaves (AC-2.4).

**Counting is per-key and immediately before that key's own replacement** (AC-2.6), not all counts
up front. Counting every key first is wrong whenever one substitution's *value* contains another
key's text: the reported number then describes a string that no longer exists by the time the
replacement runs. Sequential count-then-replace makes each reported count the number actually
replaced (AC-2.5).

**Overlapping keys refuse** (AC-2.7). If any key is a substring of another, the result depends on
iteration order, and a silently order-dependent answer is the failure class this whole feature
exists to catch. `SUBST_OVERLAP keys=<n>` with a detail line per offending pair, exit 2, nothing
executed — rather than picking an order and documenting it, which only moves the surprise.

Any key with a count of zero is collected; if the collection is non-empty nothing is executed and
every missing key gets its own detail line.

### Execution

`tempfile.mkdtemp()` (mode 0700 by construction) is the cwd. `start_new_session=True` puts the
child in its own process group, which is what makes the timeout path able to reap grandchildren
rather than orphaning them. That failure was observed in this repository this session and the
count is cited rather than recalled — four orphaned `hmad-dispatch exec-pane agy` processes, PIDs
`82161 85642 90677 91239`, PPID 1, elapsed 2d 13-15h, each a `sleep 1` poll loop surviving its
dead `pytest-9187/9132/9124/9102` run (`pgrep -fl 'exec-pane'`, reaped the same session). On
`TimeoutExpired`: **`os.killpg(proc.pid, signal.SIGKILL)`** — the pid directly, *not*
`os.getpgid(proc.pid)`. `start_new_session=True` calls `setsid()`, so the child is a group leader
and its pgid is numerically its pid; going through `getpgid` only adds a lookup that can fail.
Measured this session, and the failure is the very bug this path exists to prevent:

```
pgid == pid ?  38030 == 38030  -> True
getpgid after child exit: ProcessLookupError   <-- direct child gone, grandchild still alive
killpg(pid) after child exit: reached the group
grandchild 38032 alive_after=False
```

When the direct child has already exited but a grandchild holds the pipe open — exactly the
timeout shape — `getpgid` raises `ProcessLookupError`, the reap aborts, and the grandchild is
orphaned. `killpg(proc.pid, …)` still reaches the group. Then a second bounded `communicate` to
drain. `shutil.rmtree(cwd, ignore_errors=True)` runs in `finally`, so the temp
directory is removed on the normal path, the timeout path, and an exception path alike.

`stdout` and `stderr` are captured separately (`subprocess.PIPE` each) and never merged.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `h_mad_doc_block_exec` | `h-mad/scripts/h_mad_doc_block_exec.py` | new | extract / substitute / run / CLI |
| Helper suite | `h-mad/tests/test_h_mad_doc_block_exec.py` | new | FR-1..FR-5 ACs |
| Helper mutation spec | `h-mad/tests/mutation-specs/doc_block_exec.json` | new | guards for FR-1..FR-5 |
| Wire mutation spec | `h-mad/tests/mutation-specs/doc_block_exec_wire.json` | new | FR-6 connection, both directions |
| Registry entry | `h-mad/SKILL.md` (Helper scripts) | modify | contract + remedy rows (AC-4.5) |
| Tagged fence | `h-mad/SKILL.md` (Second surface) | modify | the one opt-in block (AC-6.1) |
| Migrated consumer | `h-mad/tests/test_h_mad_collect_report_docs.py` | modify | drop hand-rolled extraction (AC-6.2) |
| Delegating bounder | `h-mad/tests/docsections.py` | modify | import the authoritative bounder; drop the duplicate `_fence_aware_end` (AC-1.8) |

## Implementation Order

1. **Task 1 — scanner + info-string grammar.** `extract`, `Block`, fence-aware bounding, tag and
   key validation. Satisfies FR-1 and AC-3.7. New-behaviour shape.
2. **Task 2 — substitution.** `substitute` with occurrence counts and missing-key collection.
   Satisfies FR-2. Depends on Task 1 only for `Block`.
3. **Task 3 — execution and bounding.** `run_block`, temp cwd, shell modes, process-group timeout.
   Satisfies FR-3 and FR-5. Depends on Task 1.
4. **Task 4 — CLI and registry.** `main(argv)`, every verdict line in the table below, stream-path pre-check, and
   the `SKILL.md` registry entry pinned bidirectionally. Satisfies FR-4, AC-3.8/3.9. Depends on 1–3.
5. **Task 5 — the wire.** Tag the Second-surface gate fence **and** migrate the executing call
   site (`:270` plus `run_recipe`) in one task. `:412` is deliberately untouched: it selects a
   *different*, untagged block (`exec codex`) and only inspects it, so it neither breaks nor
   belongs behind an executor. Satisfies FR-6. **Wiring shape**, not new behaviour. Depends on
   1–4. Tag and migration cannot be split: tagging the gate fence makes `:270`'s `re.findall`
   match zero blocks.

## Data Model / Schema Changes

No persisted schema. Two in-memory frozen dataclasses:

```python
@dataclass(frozen=True)
class Block:
    text: str        # fence body, no trailing newline normalisation
    shell: str       # "strict" | "plain"
    lineno: int      # 1-based line of the opening fence
    info: str        # raw info string after the language word

@dataclass(frozen=True)
class RunResult:
    rc: int          # the BLOCK's exit code — never the tool's verdict
    stdout: str
    stderr: str
    shell: str
```

## API / Interface Changes

**Scanning and selection are separate functions, and that separation is the fix for a real
ambiguity in v1.0**: `extract` was typed `list[Block]` while the error contract had it raising on
0 or >1 candidates, which cannot both be true and left implementers unable to tell where refusal
lives. Split, each has one job:

```python
def extract(doc: str | Path, heading: str) -> list[Block]
    """Pure scan. Returns every tagged block under `heading`, possibly empty.
    Raises DocUnreadable or BadInfoString only — never on candidate count."""

def select(blocks: Sequence[Block], index: int | None = None) -> Block
    """Policy. Raises BlockNotFound (0, or index past the end) or
    AmbiguousBlock(n) (>1 with no index)."""

def substitute(text: str, subs: Mapping[str, str]) -> tuple[str, dict[str, int]]
def run_block(block: Block, *, subs: Mapping[str, str] | None = None,
              preamble: str | None = None, timeout: float = 30.0) -> RunResult
def main(argv: Sequence[str] | None = None) -> int
```

`main` is `select(extract(...), index)`. A caller that genuinely wants all candidates calls
`extract` alone — which is not a sweep, because it is still scoped to one document and one
heading and still returns only tagged blocks.

**`preamble` is the fixture boundary, and the feature does not work without it.** The block under
test is the doc's block, unmodified; a recipe that consumes a variable its surrounding prose sets
(the Second-surface gate block reads `COLLECT_OUT`) needs that value supplied from outside. The
preamble is shell text run in the same invocation immediately before the block, so a variable the
doc never claimed to define is bound before the recipe reads it — measured: without it the run still exits 0, still halts, and never reaches `GATE: PASS` — and it is deliberately a
separate parameter rather than string-concatenation by the caller, so the doc's text and the
fixture's text never blur. On the CLI it is `--preamble-file <path>`: a file, because the real
preamble contains command substitution and quoting an inline form would corrupt it.

`substitute` raises `MissingSubstitution(keys: list[str])`; `run_block` raises `BlockTimeout`.
The CLI converts each to a verdict line — exceptions are the API's contract, tokens are the CLI's.

CLI:

```
h_mad_doc_block_exec.py <doc> --heading <h> [--index N] [--subst K=V]...
                              [--shell-timeout SECONDS] [--stdout PATH] [--stderr PATH]
```

There is deliberately **no** `--all`, no `--dir`, and no glob-accepting argument. That absence is a
requirement, not an oversight, and is pinned by a test asserting the parser rejects such input.

Verdict lines, one per run:

| line | exit | when |
|---|---|---|
| `DOCBLOCK: RAN rc=<n> blocks=1 shell=<strict\|plain>` | 0 | the block ran (any `rc`) |
| `DOCBLOCK: NOT_FOUND heading=<h>` | 2 | no tagged block, or `--index` past the end |
| `DOCBLOCK: AMBIGUOUS blocks=<n> heading=<h>` | 2 | >1 tagged block, no `--index` |
| `DOCBLOCK: AMBIGUOUS_HEADING count=<n> heading=<h>` | 2 | >1 heading matches text+level |
| `DOCBLOCK: SUBST_MISSING key=<k>` + `missing_key: <k>` per key | 2 | a key is absent from the block |
| `DOCBLOCK: SUBST_OVERLAP keys=<n>` + `overlap: <a> <b>` per pair | 2 | one key is a substring of another |
| `DOCBLOCK: UNREADABLE reason=stream_paths_alias` | 2 | `--stdout` and `--stderr` resolve to one path |
| `DOCBLOCK: UNREADABLE reason=preamble_unreadable` | 2 | `--preamble-file` cannot be read |
| `DOCBLOCK: BAD_INFO key=<k>` | 2 | unrecognised info-string token |
| `DOCBLOCK: TIMEOUT seconds=<n>` | 2 | the block outran its bound |
| `DOCBLOCK: UNREADABLE reason=<r>` | 2 | `doc_unreadable`, `stream_path_unwritable` |

`RAN` is the only line carrying `rc=`; `AMBIGUOUS` is the only cannot-judge carrying `blocks=`.
`blocks=` and `seconds=` are diagnostic counts saying *why* judgement failed, which the count rule
permits — a measured-result count (`rc=`) is what it forbids.

## Error Handling Strategy

The API raises; the CLI returns codes. Every exception the module defines subclasses one base,
`DocBlockError`, and `main` maps the full set — **including the two IO-shaped ones the v1.0 draft
promised in its verdict table and then omitted here**, which would have let an unreadable document
or an unwritable stream path escape as a traceback rather than a token:

| exception | raised by | verdict line |
|---|---|---|
| `DocUnreadable` | `extract` (wraps `OSError`) | `UNREADABLE reason=doc_unreadable` |
| `BadInfoString(key)` | `extract` | `BAD_INFO key=<k>` |
| `BlockNotFound` | `select` | `NOT_FOUND heading=<h>` |
| `AmbiguousBlock(n)` | `select` | `AMBIGUOUS blocks=<n> heading=<h>` |
| `AmbiguousHeading(n)` | `extract` | `AMBIGUOUS_HEADING count=<n> heading=<h>` |
| `MissingSubstitution(keys)` | `substitute` | `SUBST_MISSING key=<k>` + a detail line per key |
| `OverlappingSubstitution(pairs)` | `substitute` | `SUBST_OVERLAP keys=<n>` + a detail line per pair |
| `StreamPathUnwritable` | `main`'s pre-check (wraps `OSError`) | `UNREADABLE reason=stream_path_unwritable` |
| `StreamPathsAlias` | `main`'s pre-check (resolved-path compare) | `UNREADABLE reason=stream_paths_alias` |
| `BlockTimeout(seconds)` | `run_block` | `TIMEOUT seconds=<n>` |

`main` catches `DocBlockError` and dispatches on type, so adding an exception without a verdict
line is a `KeyError` in the mapping table rather than a silent traceback — and a test asserts every
`DocBlockError` subclass appears in the table (which is also half of AC-4.5's bidirectional pin).

Nothing is logged; the verdict line and the streams are the whole output contract. A non-zero block
`rc` is **not** an error — it is the measurement.

## Test Strategy

Unit tests only, at the module boundary; no mocking of `subprocess`, because the behaviours under
test (strict vs plain, `-u`, `pipefail`, process-group reaping) are precisely what a mock would
stub out. Fixtures are markdown strings written to `tmp_path`, deliberately **hostile** rather than
tidy: headings at mixed levels, fences quoting fences, a path containing a space, a body with
CRLF, and a key containing regex metacharacters.

The CLI is exercised by `subprocess.run([sys.executable, SCRIPT, …])` so the exit codes under test
are the real process's, not a return value — the same shape `test_skill_candidates_census.py` uses.

## Test Plan

`h-mad/tests/test_h_mad_doc_block_exec.py`:

| ACs | Tests |
|---|---|
| AC-1.1–1.6 | tagged-vs-untagged selection; zero → `NOT_FOUND`; two → `AMBIGUOUS blocks=2`; `--index` 2 and 3; same/shallower-level bound; a fence quoting the tag |
| AC-1.8 | `docsections` delegates: no second bounder implementation remains (asserted on the source), its existing `test_docsections.py` still passes unchanged, and the shared bounder handles the unbalanced four-backtick case that the old toggle got wrong |
| AC-2.1–2.7 | path substitution; absent key refuses; two absent keys → two detail lines; metacharacter key; multi-occurrence count equals replacements; a value containing another key does not corrupt counts; overlapping keys refuse with `SUBST_OVERLAP` |
| AC-3.1–3.9 | `pwd` outside the repo and gone after; `git status --porcelain` byte-identical across a writing block; `-u` strict-vs-plain; bare `exit 3` → rc 3 with the harness alive; `pipefail` strict-vs-plain; streams unmerged; `shell=fish` → `BAD_INFO`; optional stream paths; unwritable stream path refuses **and the block leaves no side effect** |
| AC-4.1–4.5 | `RAN` exits 0 with a non-zero block rc; **every** cannot-judge in the verdict table exits 2 (the test enumerates the table rather than hardcoding a count, so adding a verdict cannot leave the test stale); no cannot-judge carries `rc=`; only `AMBIGUOUS` carries `blocks=`; registry ↔ detail-line bidirectional pin |
| AC-5.1–5.4 | sleeping block → `TIMEOUT`; no surviving descendant after reap; **no `timeout`/`gtimeout` INVOCATION** — an argv token or shell command word, never a substring, since the source legitimately contains `timeout=`, `TimeoutExpired`, `BlockTimeout` and `--shell-timeout`; temp cwd removed after timeout |
| AC-6.1–6.6 | tag present on the Second-surface fence; no `re.findall(r"```bash` left in the consumer; the four migrated behaviours still pass; **the full suite passes AND its count is >= the pre-change baseline plus this feature's added tests** (both halves — a passing suite that silently lost tests satisfies neither); and the two wire directions |

Verification commands:

```bash
python3.11 -m pytest h-mad/tests/test_h_mad_doc_block_exec.py -q
python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_block_exec.json
python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_block_exec_wire.json
python3.11 -m pytest -q          # full suite, run alone
```

AC-5.2 is measured, not asserted by inspection: the block records its own descendant's PID before
sleeping, and after the timeout the test requires `os.kill(pid, 0)` to raise `ProcessLookupError`.
A test that only checked the direct child would pass against the orphaning bug this AC exists to
prevent.

**The AC is scoped to the process GROUP, and that bound is real rather than cautious.** A
descendant that calls `os.setsid()` leaves the group and survives any `killpg`. Measured:

```
descendant in the group       -> survived killpg? False
descendant that called setsid -> survived killpg? True
```

A first attempt used the `setsid` **binary** and showed no escape — that probe was vacuous, since
macOS ships no such binary, and reading its null as a negative would have kept an over-claim in
the spec. So the test asserts no *in-group* descendant survives; claiming more would assert
containment nothing here implements.

**The PID file must be written OUTSIDE the temp cwd.** Writing it inside — the obvious choice —
destroys the evidence on exactly the path under test, because `run_block` removes that directory
in `finally` and AC-5.4 requires it to. The test therefore passes an absolute path under pytest's
`tmp_path` into the block via the substitution map. This works *because* the temp cwd is isolation
and not a sandbox: an absolute path escapes it, which the design states plainly under Architecture
Considerations rather than relying on it silently.

**The reaping claim is measured, not assumed.** Run this session, with a control that discriminates:

```
killpg   : grandchild 304 alive_after=False   (want False)
p.kill() : grandchild 516 alive_after=True    (want True = control discriminates)
VERDICT: CONFIRMED
```

A `bash -c 'sleep 300 & echo $! > f; sleep 300'` under `start_new_session=True`, timed out, then
reaped two ways. `os.killpg(os.getpgid(p.pid), SIGKILL)` removed the grandchild; `p.kill()` alone
left it running. The control is the load-bearing half — without it, "grandchild gone" could equally
mean the probe never created one.

## Invariant Compliance

- **Skill self-containment** — complies: stdlib only, no third-party import, no import of another
  skill's internals, and specifically **no import of `h-mad/tests/docsections.py`** despite the
  overlap, because `scripts/` must not depend on `tests/`.
- **Skill manifest integrity** — complies: `SKILL.md` gains a Helper-scripts registry entry in the
  same commit that adds the module, and AC-4.5 pins the entry to the emittable detail lines in
  both directions.
- **Audit-gate signal discipline** — complies: one `DOCBLOCK:` token, exit 0 on the verdict, exit 2
  only where nothing was measured; a caller reads the token, never `$?`.
- **No new external dependency** — complies: no new CLI, no package. `bash` is already assumed by
  every recipe in this skill.
- **Portable time bounds** — complies: the bound is Python's own (`Popen.communicate(timeout=…)`).
  AC-5.3 bans an **invocation**, not the substring: the source legitimately contains
  `timeout=`, `TimeoutExpired`, `BlockTimeout` and the `--shell-timeout` flag, and a substring ban
  would reject the very design that satisfies the invariant. The test asserts no `timeout`/
  `gtimeout` appears as an argv token or as a command word inside a shell string.
- **Mutation verification** — complies: every guard carries a mutation with a named `test` key, so
  a mutant killed by an unrelated assertion is reported as a survivor rather than a catch.
- **Connection enforcement** — complies: FR-6 is declared a wiring task with a `WIRE`/`WIRE-PIN`
  and two-direction discrimination (AC-6.5/AC-6.6); a whole-module revert is explicitly not
  sufficient, because it removes both sides at once.
- **Assumption verification** — complies: the plan's `## Measurements` section carries both cited
  commands with their observed output, and the design adds no uncited measured claim.

## Version History

- v1.0: Initial design draft.
- v1.1: Design audit v1 (8 findings, union of codex 7 + agy 1): split extract/select, complete the exception->verdict mapping, backtick-run-aware fence scanning, move the AC-5.2 PID file outside the temp cwd, cite the reaping probe and the orphan-process count, restate AC-5.3 as an invocation ban and AC-6.4 in full.
- v1.2: Design audit v2 (agy, 1 must + 2 should; codex clean): add the differential bounder test the Single-source contract requires, make substitution counting sequential and refuse overlapping keys, document the ATX-only heading assumption.
- v1.3: Design audit v3: killpg(proc.pid) rather than killpg(getpgid(pid)) — the getpgid race was reproduced and would orphan the grandchild; scope BAD_INFO to tagged fences; enumerate the verdict table instead of hardcoding counts.
- v1.4: Design audit v4: resolve the AC-1.6/AC-1.8 incompatibility by making this module the authoritative bounder and having docsections import it; narrow the Test Plan's AC-5.3 row to an invocation ban (its fourth surface).
- v1.5: Plan re-audit v5: only the executing call site migrates — :270 and :412 select different blocks (measured, 4 blocks in the section), so the earlier 'both extractors break' claim was false and AC-6.2 was unsatisfiable; add docsections.py to Deliverables.
- v1.6: Plan re-audit v7: scope AC-5.2 to the launched process group (a setsid descendant escapes, measured); refuse aliased --stdout/--stderr (AC-3.9); correct the risk row that still claimed both extractors break.
- v1.7: Plan re-audit v8: add the fixture preamble boundary (AC-3.11/AC-3.12) — without it the gate block's COLLECT_OUT is unbound under strict bash and the FR-6 migration cannot reach GATE: PASS.
- v1.8: Plan re-audit v9: refuse duplicate headings (AC-1.7) — invariants.example.md has two; cite the controlled preamble pair, which also narrows the earlier 'aborts on unbound variable' claim to 'cannot reach GATE: PASS'.
- v1.9: Narrow the preamble's set -u wording to what the controlled pair actually measured.
