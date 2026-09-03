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
`tests/`; `tests/` → `scripts/` is the correct direction and was available all along. **The
mechanism is the one every test in `h-mad/tests/` already uses** for `SCRIPT_DIR`: `docsections.py`
does `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))` itself, on the
line before `from h_mad_doc_block_exec import fence_aware_end`, so the import holds when
`test_docsections.py` is collected alone and never depends on a sibling test module having
inserted the path first (the plan names the two tests that pin this). This also
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
   select(blocks, index) ─── POLICY: index<1 ──► BAD_INDEX ; 0 ──► NOT_FOUND ; >1 no index ──► AMBIGUOUS
        ▼ exactly one
  substitute()  ─────────►  Block'             literal replace, count each key; a NEW Block
        │  every key present?  no ──► SUBST_MISSING
        ▼ yes
   run_block()
        ├── validate timeout: finite, > 0 ──► else BAD_TIMEOUT  (BEFORE mkdtemp: nothing to clean up)
        ├── mkdtemp() + chmod(0o700) ────── cwd   (mkdtemp alone is 0700 & ~umask;
        │                                          chmod fails ──► pending LAUNCH_FAILED stage=mkdtemp,
        │                                          then the SAME finally-cleanup + read-back selection)
        ├── Popen(["bash", *flags, "-c", preamble ⊕ text'], start_new_session=True,
        │         text=True, encoding="utf-8", errors="replace")
        ├── communicate(timeout) ─── TimeoutExpired ──► killpg(SIGKILL) [ESRCH = already reaped]
        │                                                 ──► drain communicate(DRAIN_SECONDS)
        │                                                     [expired: close pipes, wait()] ──► TIMEOUT
        └── finally: rmtree(cwd) ──► read back: lexists? ──► CLEANUP_FAILED (outranks TIMEOUT)
        ▼
     Result(rc, stdout, stderr, shell)
        ▼
   main() ─────────────►  one `DOCBLOCK:` line on stdout;  exit 0 on every verdict (RAN, every
                          refusal, TIMEOUT) | 2 only on UNREADABLE / CLEANUP_FAILED / LAUNCH_FAILED
```

Refusals are ordered so that nothing irreversible happens before the last one: info-string
validation, ordinal validation, timeout validation, preamble readability and stream-path
writability are all checked **before** `bash` is spawned, and no stream artifact is truncated
before a successful run. **Exactly four non-`RAN` outcomes can follow a spawn, in this
precedence:** `CLEANUP_FAILED` (exit 2 — selected after cleanup and read-back have run, so it
outranks everything), then `LAUNCH_FAILED stage=reap` (exit 2 — a timed-out block whose group
could not be signalled; it outranks the timeout it implies because an unkillable child is the
more urgent finding), then `TIMEOUT` (exit 0 — a measured fact about the block), then
`UNREADABLE reason=stream_write_failed` (exit 2 — only reachable on the path that would otherwise
print `RAN`, because streams are written only after a successful, cleaned-up run). The `mkdtemp`
and `spawn` stages of `LAUNCH_FAILED` are pre-spawn by definition and sit outside this list. None
of the four carries `rc=`, and on the first three nothing is written to any artifact; nothing that ran is reported as a
measurement unless the cwd is gone *and* every promised artifact exists. **The precedence is a
control-flow design, not a hope:** `run_block` never raises from inside the timeout handler. It
records a *pending* outcome — `pending = BlockTimeout(timeout)` after the reap, or the `RunResult`
— runs cleanup in `finally` (which records an `OSError` and never raises), then, after the
`try`/`finally` has completed, reads the cwd back and **selects** the final outcome: `CleanupFailed(cwd,
cleanup_error)` raised `from pending` **if a cleanup `OSError` was recorded OR the directory
persists** — either alone (`__cause__` is the pending `BlockTimeout`/`LaunchFailed` when there is
one, else `cleanup_error`), else the pending outcome re-raised, else the result returned. The
"OR" is the rule: an `rmtree` that removed everything and then raised is still a failure
(`test_cleanup_error_after_successful_removal_is_still_a_failure` injects exactly that), because
"the tree is gone" and "the removal reported success" are different facts and the helper does not
guess which one to believe. A `raise` inside the handler would propagate straight past the
read-back — Python runs `finally` and then continues unwinding — which is exactly the ordering
bug this paragraph replaces. **Two tests drive the combined case, and the one that carries the
guard runs everywhere:** `test_cleanup_failure_outranks_timeout_injected` patches `shutil.rmtree`
to raise `OSError` under a block that is only `sleep 300` (`timeout=1`) and asserts the final
exception is `CleanupFailed`, its `__cause__` is the `BlockTimeout`, its `cleanup_error` is the
injected `OSError`, and the cwd is read back present (the test removes it in `finally`); it needs
no permissions and is the mutation's named killer. `test_cleanup_failure_outranks_timeout` is its
real-fixture sibling (`mkdir keep && chmod 000 keep && sleep 300`, `timeout=1`, `cleanup_error`
the `PermissionError`) and is skipped under `euid == 0` — the precedence guard is therefore never
undiscriminated on a root runner, because the injected test does not skip.

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

One pass over the lines, carrying `in_fence`, **the opening fence's marker character (backtick
or tilde) and its run length**. CommonMark fences come in both flavours, `~~~` closes only a `~~~`
fence, and a tilde fence can quote a backtick fence verbatim — measured through GitHub's renderer
in the spec's Assumptions: a `~~~` block containing ` ```bash hmad:exec ` renders as a plain code
block. Tilde fences are tracked for bounding only; a **candidate** is always a backtick fence whose
first info-string word is `bash`. A
naive "any line starting with ``` toggles" is wrong and would corrupt the state on a document this
feature must handle: CommonMark opens a fence with a run of *N* ≥ 3 backticks and closes it only
with a run of ≥ *N*, so a fence opened with four backticks legitimately contains ``` lines as
body text. This design's own documents contain exactly that shape, because they quote fenced
examples. So:

- an opening fence records its marker character and `n = len(run)`; while open, only a line
  whose leading run is of the **same character** and ≥ `n` **and** carries no info string closes
  it;
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
different block. **An `index` below 1 is validated before any lookup and raises `BadIndex(n)`**
(AC-1.9): the obvious `blocks[index - 1]` turns `0` into the *last* tagged block and a negative
value into some other one — a wrong block executed without a word, which is the failure the
explicit address exists to prevent. Past-the-end stays `BlockNotFound` (AC-1.4); that ordinal
names a block that does not exist, whereas `0` is not an ordinal at all.

### Substitution

`str.replace` — literal, never regex, so a key containing `.` or `[` behaves (AC-2.4).

**Counting is per-key and immediately before that key's own replacement** (AC-2.6), not all counts
up front. Counting every key first is wrong whenever one substitution's *value* contains another
key's text: the reported number then describes a string that no longer exists by the time the
replacement runs. Sequential count-then-replace makes each reported count the number actually
replaced (AC-2.5).

**Overlapping keys refuse** (AC-2.7). If any key is a substring of another, the result depends on
iteration order, and a silently order-dependent answer is the failure class this whole feature
exists to catch. `SUBST_OVERLAP keys=<n>` with a detail line per offending pair, exit 0, nothing
executed — rather than picking an order and documenting it, which only moves the surprise. `<n>`
counts the **distinct keys implicated**, not the pairs (`a`, `ab`, `abc` → `keys=3`, three pairs);
each unordered pair appears once as `overlap: <shorter> <longer>`, and the lines are sorted by
`(shorter, longer)`, so the same map always produces the same diagnostic.

Any key with a count of zero is collected; if the collection is non-empty nothing is executed and
every missing key gets its own detail line. **An empty key is refused here, in the API** —
`BadSubstArg("")` — not only by the CLI parser: `str.replace("", v)` inserts `v` at every character
boundary, and an in-process caller must meet the same wall `main` does.

### Execution

`tempfile.mkdtemp()` **followed by `os.chmod(cwd, 0o700)`** is the cwd. `mkdtemp` alone gives
`0o700 & ~umask` — probed: under `umask 0777` it yields mode `0o0` — so "0700 by construction",
which an earlier draft claimed, was only true under the default umask; the chmod makes AC-3.13
true everywhere. **A chmod that fails is not a special rollback path**: the chmod runs inside the
same `try` whose `finally` removes the cwd, so a failure records `LaunchFailed("mkdtemp", err)`
as the pending outcome and falls through to the ordinary cleanup, read-back and selection —
`CleanupFailed` (with the `LaunchFailed` as `__cause__`) if the removal fails or the directory
persists, else the `LaunchFailed`. `test_chmod_rollback_failure_is_cleanup_failed` injects both
(`os.chmod` raising, `shutil.rmtree` raising) and asserts that chain. `start_new_session=True` puts the
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
orphaned. `killpg(proc.pid, …)` still reaches the group.

**Two races remain on that path, and both are handled rather than left to a traceback** (AC-5.5):

1. **The group empties between `TimeoutExpired` and `killpg`.** `os.killpg` then raises
   `ProcessLookupError` — measured on an already-reaped leader (plan §Measurements, last line).
   The helper catches exactly that exception and treats it as "already reaped" — and the test
   that injects it models that state rather than merely asserting it: its fake `killpg` calls
   the real `os.killpg(pgid, SIGKILL)`, polls `os.kill(pgid, 0)` until `ProcessLookupError`, and
   only then raises `ProcessLookupError` itself, so the drain sees a genuinely empty group and
   nothing is left running (a fake that only raised would leave the timed-out `sleep` alive and
   the drain or `wait()` hanging on it — the stub would not model the state production consumes).
   "Already reaped" is the
   state the kill wanted. Any other `OSError` (a `PermissionError`, in practice unreachable on
   one's own child but not impossible) is **not** allowed to escape as a traceback: the helper
   still runs the bounded drain and closes the pipes, does **not** `wait()` (a child it could not
   signal is not something to wait on unboundedly), records `LaunchFailed("reap", err)` as the
   pending outcome with `pgid=<n>` in its detail, and lets cleanup and the read-back run as usual
   (AC-4.6). **Policy for a genuinely unsignalable group is diagnostic, not containment**: the
   helper has no signal that would work where `SIGKILL` to the group did not, so it reports the
   pgid and returns bounded rather than pretending; this is the one documented case in which a
   launched process may outlive the call. **The test for it must not become that case**: its fake
   `killpg` records the pgid and raises, and the test's `finally` sends the real
   `os.killpg(pgid, SIGKILL)` and asserts `ProcessLookupError` on a follow-up `os.kill(pgid, 0)`
   — CPython's `Popen.__del__` never kills a live child, so without that teardown the
   fault-injected test would leave a `sleep` running after it returned.
2. **The post-kill drain does not finish.** After `killpg` a second `communicate` collects what
   the group wrote before dying; but a descendant that left the group (AC-5.2's `os.setsid()`
   escapee) still holds the inherited pipes, so that `communicate` can block for as long as the
   escapee lives. It is therefore bounded too — `communicate(timeout=DRAIN_SECONDS)`, a module
   constant of 5 s — and on its own `TimeoutExpired` the helper closes `proc.stdout` and
   `proc.stderr` itself, calls `proc.wait()` (the leader is SIGKILLed, so this returns at once),
   and raises `BlockTimeout` as it would have anyway. The escapee is outside the reap by AC-5.2's
   stated scope; what this bounds is the *helper's* wall time, which is now at most
   `timeout + DRAIN_SECONDS` plus process teardown, so FR-5's "every run is bounded" holds against
   an escapee rather than only against a well-behaved block. Partial output from a timed-out
   block is discarded in both cases — `TIMEOUT` is a cannot-judge and carries no streams.

**Cleanup is verified, never suppressed** (AC-3.14). `shutil.rmtree(cwd)` — *without*
`ignore_errors` — runs in `finally`, so the temp directory is removed on the normal path, the
timeout path, and an exception path alike; its `OSError`, if any, is caught and recorded there
rather than raised from inside `finally` (which would replace whatever exception was in flight).
Because the timeout handler *records* `BlockTimeout` as a pending outcome rather than raising it
(see the precedence paragraph under Architecture Overview), control always reaches the statement
after the `try`/`finally`, where the helper reads the directory back: `os.path.lexists(cwd)` must be
false. If it is not — **or** an `OSError` was recorded, whichever alone —
`CleanupFailed(cwd, cleanup_error)` is raised and `main` prints `DOCBLOCK: CLEANUP_FAILED path=<p>`,
exit 2. **Its causal data is two named things, never one overloaded slot:** the `cleanup_error`
attribute is the recorded `OSError`, or `None` when nothing was raised and the read-back alone
caught it; `__cause__` is the *pending outcome* when there was one (the `BlockTimeout`, or a
`LaunchFailed`), else `cleanup_error`. So: normal run + cleanup failure → `__cause__ is
cleanup_error`; timeout + cleanup failure → `__cause__` is the `BlockTimeout` and `cleanup_error`
still carries the `OSError`; read-back-only retention → `cleanup_error is None`. **The
two guards are separately mutation-tested, because the read-back makes `ignore_errors` look
redundant:** `cleanup-errors-ignored` (restore `ignore_errors=True`) is killed by
`test_cleanup_failure_carries_the_os_error`, which fault-injects an `rmtree` that raises and
asserts `cleanup_error` is that error — under the mutation nothing is recorded, the read-back
trips, and `cleanup_error` is `None`; `cleanup-readback-removed` (drop the `lexists` check) is killed by
`test_cleanup_readback_catches_silent_retention`, which fault-injects an `rmtree` that does
nothing and raises nothing — under the mutation the run reports `RAN` over a retained directory. The failure is real and cheap to produce: a block that runs `mkdir keep && chmod 000 keep`
leaves a subdirectory `rmtree` cannot list, on which `rmtree` measurably raises `PermissionError`
and `rmtree(…, ignore_errors=True)` measurably retains the whole tree with no signal (probed on
the supported interpreter — python 3.11.8, darwin, euid 501; command and output in the plan's
§Measurements). That silent retention is the mutation-verification invariant's
"a completed run reported over an unverified mutation", and it is what the old `ignore_errors=True`
did. **Precedence:** a cleanup failure outranks a `BlockTimeout` on the same run — the pending
`BlockTimeout` becomes `CleanupFailed`'s `__cause__` — because a retained directory is state the
operator must act on (exit 2, an operational error) whereas the timeout is a verdict about the
block (exit 0) already implied by the retained directory's partial contents; neither carries
`rc=`. The fixture test
restores the subdirectory's mode and removes the tree in its own `finally`, so the suite does not
leak what it just proved the helper cannot remove.

`stdout` and `stderr` are captured separately (`subprocess.PIPE` each) and never merged. **The
launch is text-mode, and the policy is explicit**: `Popen(…, text=True, encoding="utf-8",
errors="replace")`, so `communicate()` returns `str` (which is what `RunResult` promises and what
the held artifact handles — opened `encoding="utf-8"` — accept), non-ASCII output round-trips, and
an undecodable byte becomes U+FFFD instead of a `UnicodeDecodeError` escaping the helper (AC-3.6).
**The bound is validated before the spawn — and before `mkdtemp`** (AC-5.6): `timeout` must
satisfy `math.isfinite(t) and t > 0`, else `BadTimeout(value)`, raised while there is nothing to
clean up, so the refusal can neither leak a directory nor need the read-back — `communicate(timeout=-1)` raises
`ValueError` only after the child exists, and `inf` is no bound at all.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `h_mad_doc_block_exec` | `h-mad/scripts/h_mad_doc_block_exec.py` | new | extract / substitute / run / CLI |
| Helper suite | `h-mad/tests/test_h_mad_doc_block_exec.py` | new | FR-1..FR-5 ACs |
| Helper mutation spec | `h-mad/tests/mutation-specs/doc_block_exec.json` | new | guards for FR-1..FR-5 — 33 mutations plus the AC-5.3 self-check (34 rows), each bound to its RED test, enumerated under Test Plan |
| Wire mutation spec | `h-mad/tests/mutation-specs/doc_block_exec_wire.json` | new | FR-6 connection, both directions |
| Registry entry | `h-mad/SKILL.md` (Helper scripts) | modify | contract + remedy rows (AC-4.5) |
| Tagged fence | `h-mad/SKILL.md` (Second surface) | modify | the one opt-in block (AC-6.1) |
| Migrated consumer | `h-mad/tests/test_h_mad_collect_report_docs.py` | modify | drop hand-rolled extraction (AC-6.2); calls are module-qualified (`import h_mad_doc_block_exec as dbe` → `dbe.extract`/`dbe.select`/`dbe.run_block`) so the wire spies observe them |
| Delegating bounder | `h-mad/tests/docsections.py` | modify | import the authoritative bounder; drop the duplicate `_fence_aware_end` (AC-1.8) |
| Bounder mutation spec | `h-mad/tests/mutation-specs/docsections.json` | modify | re-point `fence-tracking-removed` and `section-no-longer-owns-its-subsections` at `scripts/h_mad_doc_block_exec.py`; the other two anchors stay in `tests/docsections.py`; all four gain a `test` key (from their `_killed_by`) under a `target_command`, so the harness credits each only through its named RED |

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
    Raises DocUnreadable, BadInfoString or AmbiguousHeading — never on candidate count."""

def select(blocks: Sequence[Block], index: int | None = None) -> Block
    """Policy. Raises BadIndex(n) (index given and < 1 — validated BEFORE any
    lookup, so 0 can never reach `blocks[index - 1]` and alias the last block),
    BlockNotFound (0 candidates, or index past the end) or AmbiguousBlock(n)
    (>1 with no index)."""

def substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]
    """Returns a NEW Block (dataclasses.replace) whose text has every key replaced,
    plus the per-key counts. run_block never substitutes: main calls this first,
    so a bad map is refused before any stream artifact is reserved."""

def run_block(block: Block, *, preamble: str | None = None,
              timeout: float = 30.0) -> RunResult
def main(argv: Sequence[str] | None = None) -> int

def fence_aware_end(text: str, start: int, level: int) -> int
    """Offset of the next ATX heading at `level` or shallower after `start`,
    skipping fenced blocks with backtick-run tracking. The bounder `extract`
    uses, exported so `h-mad/tests/docsections.py` can delegate to it (AC-1.8)."""
```

`__all__` names all six. `fence_aware_end` is public on purpose: `docsections.titled_section`
and `docsections.section_from` call it in place of the deleted `_fence_aware_end` with the same
`(text, start, level)` arguments, so the two re-pointed `docsections.json` mutations target this
function's fence-state update and heading match.

`main` is `select(extract(...), index)`. A caller that genuinely wants all candidates calls
`extract` alone — which is not a sweep, because it is still scoped to one document and one
heading and still returns only tagged blocks.

**`preamble` is the fixture boundary, and the feature does not work without it.** The block under
test is the doc's block, unmodified; a recipe that consumes a variable its surrounding prose sets
(the Second-surface gate block reads `COLLECT_OUT`) needs that value supplied from outside. The
preamble is shell text run in the same invocation immediately before the block, so a variable the
doc never claimed to define is bound before the recipe reads it — measured: without it the run still exits 0, still halts, and never reaches `GATE: PASS` — and it is deliberately a
separate parameter rather than string-concatenation by the caller, so the doc's text and the
fixture's text never blur. **Composition is `preamble.rstrip("\n") + "\n" + text′`** when a
preamble is given, and `text′` alone otherwise — where `text′` is the `.text` of the `Block`
that `substitute(block, subs)` returns,
the text that will actually run, never the unsubstituted fence body (the diagram's `text'`): the
preamble is prepended *after* substitution, so a substituted path stays substituted when a preamble
is present. Exactly one newline separates them, so a
preamble file without a trailing newline cannot fuse with the recipe's first token and one with a
trailing newline gains no blank line. **The combined invocation is what is measured** (AC-3.12): `rc`,
`stdout` and `stderr` on the returned `RunResult` describe preamble-plus-block as one `bash -c`,
so a preamble that fails is visible as that `rc` and its stderr rather than being swallowed — the
helper does not, and cannot, attribute a line to one half or the other. On the CLI it is
`--preamble-file <path>`: a file, because the real preamble contains command substitution and
quoting an inline form would corrupt it; a path that cannot be read raises `PreambleUnreadable`
in `main`'s pre-check, before the block runs.

`substitute` raises `MissingSubstitution(keys)` or `OverlappingSubstitution(pairs)`; `run_block` raises
`BlockTimeout(seconds)`, `CleanupFailed(path, cleanup_error)` or `LaunchFailed(stage, err)`.
The CLI converts each to a verdict line — exceptions are the API's contract, tokens are the CLI's.

CLI:

```
h_mad_doc_block_exec.py <doc> --heading <h> [--index N] [--subst K=V]...
                              [--preamble-file PATH] [--shell-timeout SECONDS]
                              [--stdout PATH] [--stderr PATH]
```

There is deliberately **no** `--all`, no `--dir`, and no glob-accepting argument. That absence is a
requirement, not an oversight, and is pinned by a test asserting the parser rejects such input. The
parser is `argparse.ArgumentParser(allow_abbrev=False)`, so the documented spellings are the only
spellings — `--shell-t` is an error, not an alias — and a test asserts that too. **Argument values
are the contract's, argument grammar is argparse's**: `--index` and `--shell-timeout` are declared
`type=str` and validated by `main` (`BAD_INDEX` / `BAD_TIMEOUT`), so a malformed value still gets
one `DOCBLOCK:` line; only an unknown option or a missing value reaches argparse's usage error,
the documented single non-`DOCBLOCK` exit 2.

**Stream artifacts: reserved last, never truncated by an open, written through the held handle.**
The order in `main` is `extract` → `select` → `substitute` → the remaining validations (timeout,
preamble readability — the info string is validated inside `extract`, the ordinal inside
`select`, and `--subst` syntax before `substitute` is called) → **reserve** → **alias check on the
reserved descriptors** → spawn. Reservation opens `--stdout` then `--stderr` with
`open(path, "a", encoding="utf-8")` and holds both handles: append creates a missing file and
never empties an existing one, so there is no moment at which one artifact is truncated while the
other is still unreserved. If the second open fails, the first handle is closed and — only if this
call created the file (it did not exist before the open) — unlinked, so a pre-existing artifact
keeps every byte and a refusal leaves no new empty file. The truncation is the final write itself:
on the `RAN` path, after cleanup succeeded, each held handle gets `seek(0); truncate(); write(…)`,
so an existing artifact is overwritten, never appended. On `TIMEOUT` or `CLEANUP_FAILED` nothing is
written to either handle and pre-existing artifacts are untouched. A failure *in* that final write
can therefore only be an error on an open descriptor (disk full, I/O error) and maps to
`StreamWriteFailed` → `UNREADABLE reason=stream_write_failed`, exit 2; the `rc` is not reported,
because the artifact the caller was promised does not exist. **The writes are ordered and the
partial state is reported, not rolled back**: stdout is written first, then stderr; if the second
fails, the first stays as written (its old contents were truncated in place, so there is nothing
to restore) and the detail lines read `written: stdout` / `failed: stderr`. **Both writes go
through one module function, `_final_write(handle, text)`** — the seam the AC-3.8 tests
fault-inject, since no real mechanism makes a held descriptor fail deterministically on macOS
(no `/dev/full`). **Aliasing is judged on the opened
descriptors** (AC-3.9): once both handles are held, `os.fstat` on each gives `(st_dev, st_ino)`,
and equality is `StreamPathsAlias` — a symlink, a `./x`/`x` spelling and a **hard link** all
collapse to one inode, and because the comparison is on the descriptors there is no
check-to-open window in which two distinct strings can come to name one file. The refusal closes
both handles, unlinks one this call created, and has written nothing. (A string-level pre-check is
therefore not needed and is not performed; the earlier resolved-path comparison was both weaker
and racy.)

Verdict lines, one per run:

| line | exit | when |
|---|---|---|
| `DOCBLOCK: RAN rc=<n> blocks=1 shell=<strict\|plain>` | 0 | the block ran (any `rc`) |
| `DOCBLOCK: NOT_FOUND heading=<h>` | 0 | no tagged block, or `--index` past the end |
| `DOCBLOCK: AMBIGUOUS blocks=<n> heading=<h>` | 0 | >1 tagged block, no `--index` |
| `DOCBLOCK: AMBIGUOUS_HEADING count=<n> heading=<h>` | 0 | >1 heading matches text+level |
| `DOCBLOCK: BAD_INDEX index=<n>` | 0 | `--index` below 1, or not an integer |
| `DOCBLOCK: BAD_TIMEOUT value=<v>` | 0 | `--shell-timeout` non-numeric, non-finite, or not > 0 |
| `DOCBLOCK: BAD_SUBST arg=<raw>` (+ `duplicate_key: <k>`) | 0 | a `--subst` value with no `=` or an empty key, or a key given twice |
| `DOCBLOCK: SUBST_MISSING key=<k>` + `missing_key: <k>` per key | 0 | a key is absent from the block |
| `DOCBLOCK: SUBST_OVERLAP keys=<n>` + `overlap: <a> <b>` per pair | 0 | one key is a substring of another |
| `DOCBLOCK: UNREADABLE reason=stream_paths_alias` | 2 | `--stdout` and `--stderr` name one inode (`fstat` on the reserved handles) |
| `DOCBLOCK: UNREADABLE reason=preamble_unreadable` | 2 | `--preamble-file` cannot be read |
| `DOCBLOCK: BAD_INFO key=<k>` | 0 | unrecognised info-string token |
| `DOCBLOCK: TIMEOUT seconds=<n>` | 0 | the block outran its bound (either race in AC-5.5 included) |
| `DOCBLOCK: CLEANUP_FAILED path=<p>` | 2 | the temp cwd could not be removed, or was read back present |
| `DOCBLOCK: LAUNCH_FAILED stage=<s>` + `os_error: <text>` | 2 | the helper's own `mkdtemp`/`Popen`/`killpg` raised — never a traceback |
| `DOCBLOCK: UNREADABLE reason=<r>` | 2 | `doc_unreadable`, `stream_path_unwritable`, `stream_write_failed` |

The order in `main` is `extract` (which validates the info string and refuses a duplicate heading)
→ `select` (which validates the ordinal) → `--subst` syntax → `substitute` → the remaining
validations that belong to no earlier step (timeout, preamble readability) → reserve both stream
handles → alias check on the reserved descriptors (`os.fstat`, the only place it *can* happen) →
spawn. Nothing is reserved until every refusal that can be made from the inputs alone has been
made; the alias refusal is the one that needs the reservation, and it still precedes the spawn.

`RAN` is the only line carrying `rc=`; `AMBIGUOUS` is the only refusal carrying `blocks=`.
`blocks=`, `count=`, `index=`, `value=` and `seconds=` are diagnostic values saying *why* the tool
declined or the block did not finish, which the count rule permits — a measured-result count
(`rc=`) is what it forbids. **The exit column follows the base Audit-gate signal discipline
invariant**: every verdict — `RAN`, every refusal of readable input, and `TIMEOUT` — exits 0, so no
refusal ever registers as a tool failure in the orchestrator's harness; exit 2 is reserved for the
two operational classes the invariant names, `UNREADABLE` (input that could not be read, a path
that could not be written or reserved, a write that failed) and `CLEANUP_FAILED`. AC-4.2 pins that
partition row by row, and the test that walks this table is what keeps the two from drifting.

## Error Handling Strategy

The API raises; the CLI returns codes. Every exception the module defines subclasses one base,
`DocBlockError`, and `main` maps the full set — **including the two IO-shaped ones the v1.0 draft
promised in its verdict table and then omitted here**, which would have let an unreadable document
or an unwritable stream path escape as a traceback rather than a token:

| exception | raised by | verdict line |
|---|---|---|
| `DocUnreadable` | `extract` (wraps `OSError` **and `UnicodeDecodeError`** — the document is read as strict UTF-8) | `UNREADABLE reason=doc_unreadable` |
| `BadInfoString(key)` | `extract` | `BAD_INFO key=<k>` |
| `BlockNotFound` | `select` | `NOT_FOUND heading=<h>` |
| `AmbiguousBlock(n)` | `select` | `AMBIGUOUS blocks=<n> heading=<h>` |
| `AmbiguousHeading(n)` | `extract` | `AMBIGUOUS_HEADING count=<n> heading=<h>` |
| `BadIndex(n)` | `select`, and `main` for a non-integer argument | `BAD_INDEX index=<n>` |
| `BadTimeout(value)` | `run_block` before `Popen`, and `main` for a non-numeric argument | `BAD_TIMEOUT value=<v>` |
| `BadSubstArg(raw, duplicate_key=None)` | `main`, building the map (split once on the first `=`; empty key or repeat refused) | `BAD_SUBST arg=<raw>` + `duplicate_key: <k>` when it is a repeat |
| `MissingSubstitution(keys)` | `substitute` | `SUBST_MISSING key=<k>` + a detail line per key |
| `OverlappingSubstitution(pairs)` | `substitute` | `SUBST_OVERLAP keys=<n>` + a detail line per pair |
| `StreamPathUnwritable` | `main`'s stream reservation — the `open(path, "a")` itself (wraps `OSError`) | `UNREADABLE reason=stream_path_unwritable` |
| `StreamPathsAlias` | `main`, after reserving both handles — `os.fstat` `(st_dev, st_ino)` equal | `UNREADABLE reason=stream_paths_alias` |
| `PreambleUnreadable` | `main`'s pre-spawn read of `--preamble-file` (wraps `OSError` **and `UnicodeDecodeError`** — strict UTF-8, because text that will be executed is never silently repaired) | `UNREADABLE reason=preamble_unreadable` |
| `StreamWriteFailed` | `main`, writing a stream to its held handle after the run | `UNREADABLE reason=stream_write_failed` |
| `BlockTimeout(seconds)` | `run_block` (both AC-5.5 races end here) | `TIMEOUT seconds=<n>` |
| `CleanupFailed(path, cleanup_error)` | `run_block`, after the `finally` read-back | `CLEANUP_FAILED path=<p>` |
| `LaunchFailed(stage, err)` | `run_block` — `mkdtemp`, `Popen`, or a non-`ESRCH` `killpg` error, wrapped | `LAUNCH_FAILED stage=<mkdtemp\|spawn\|reap>` + `os_error: <text>` |

`main` catches `DocBlockError` and dispatches on type, so adding an exception without a verdict
line is a `KeyError` in the mapping table rather than a silent traceback — and a test asserts every
`DocBlockError` subclass appears in the table (which is also half of AC-4.5's bidirectional pin).

Nothing is logged; the verdict line and the streams are the whole output contract. A non-zero block
`rc` is **not** an error — it is the measurement.

## Test Strategy

Unit tests only, at the module boundary; no mocking of `subprocess`, because the behaviours under
test (strict vs plain, `-u`, `pipefail`, process-group reaping) are precisely what a mock would
stub out. **Five named exceptions, all fault injections on a call whose *failure* is under test,
all via pytest's `monkeypatch` (restored on exit), all leaving `subprocess` real:** the AC-5.5
`killpg` race is a timing window between `TimeoutExpired` and the kill that no fixture can hold
open, so its test patches `os.killpg` to raise `ProcessLookupError` (and, for AC-4.6's `reap`
stage, `PermissionError`); the AC-3.14 cleanup guards are exercised by patching `shutil.rmtree`
in the helper's namespace — once to raise `OSError`, once to do nothing — because a real
permission failure is skipped under root and the two guards need mutants only one of them kills;
and AC-4.6's `mkdtemp` stage patches `tempfile.mkdtemp` to raise and, separately, `os.chmod` to
raise (AC-3.13's post-creation failure, which must remove the directory it just created). The
`spawn` stage needs no mock: the test sets `PATH` to an empty directory and `bash` is genuinely
not found. The fifth is the module's own `_final_write(handle, text)` seam, patched to raise
`OSError` for AC-3.8's post-run write failure — the one call for which no real fault exists on
this platform. The drain race needs no mock, because a real
`os.setsid()` descendant holds the pipes open; the real permission fixture still runs wherever
`euid != 0`. Fixtures are markdown strings written to `tmp_path`, deliberately **hostile** rather than
tidy: headings at mixed levels, fences quoting fences, a path containing a space, a body with
CRLF, and a key containing regex metacharacters.

The CLI is exercised by `subprocess.run([sys.executable, SCRIPT, …])` so the exit codes under test
are the real process's, not a return value — the same shape `test_skill_candidates_census.py` uses.

## Test Plan

`h-mad/tests/test_h_mad_doc_block_exec.py`:

| ACs | Tests |
|---|---|
| AC-1.1–1.7 | tagged-vs-untagged selection; a document containing an invalid UTF-8 byte → `UNREADABLE reason=doc_unreadable`, never a traceback; zero → `NOT_FOUND`; two → `AMBIGUOUS blocks=2`; `--index` 2 and 3; same/shallower-level bound; a fence quoting the tag, and a `~~~` fence quoting the tag; **a document with two identical headings → `AMBIGUOUS_HEADING count=2`, nothing executed** (fixture mirrors `invariants.example.md`'s duplicated `###`) |
| AC-1.8 | `docsections` delegates: no second bounder implementation remains (asserted on the source), its existing `test_docsections.py` still passes unchanged, and the shared bounder handles the unbalanced four-backtick case that the old toggle got wrong. **The import arrangement is pinned twice**: `test_docsections_imports_when_collected_alone` runs `pytest h-mad/tests/test_docsections.py -q` as a subprocess from the repo root, and `test_docsections_imports_from_an_unrelated_cwd` runs `python3 -c "import docsections"` with only the tests dir on `sys.path` and `cwd=tmp_path` — both would fail if `docsections.py` relied on another module's `sys.path` insert |
| AC-1.9 | `--index 0` and `--index -1` → `BAD_INDEX index=<n>`, exit 0, and the block a naive `blocks[-1]` would have chosen leaves no side effect; `select(blocks, 0)` raises `BadIndex` |
| AC-2.1–2.7 | path substitution; absent key refuses; two absent keys → two detail lines; metacharacter key; multi-occurrence count equals replacements; a value containing another key does not corrupt counts; overlapping keys refuse with `SUBST_OVERLAP`, `keys=` counts distinct keys (`a`/`ab`/`abc` → 3) and the `overlap:` lines are one per pair in `(shorter, longer)` order |
| AC-3.1–3.10 | `pwd` outside the repo and gone after; `git status --porcelain` byte-identical across a writing block; `-u` strict-vs-plain; bare `exit 3` → rc 3 with the harness alive; `pipefail` strict-vs-plain; streams unmerged, and `str` — a block printing `é` round-trips it, a block running `printf '\xff'` yields U+FFFD (AC-3.6); `shell=fish` → `BAD_INFO`; optional stream paths; aliased `--stdout`/`--stderr` (a symlink, `./x` vs `x`, **and an `os.link` hard link**) refuse after reservation and before running, with both handles closed and a created file unlinked; unwritable stream path refuses **and the block leaves no side effect**; a pre-existing stream file is truncated, not appended; **a failed `--stderr` reservation leaves a pre-existing `--stdout` file byte-identical, and removes a `--stdout` file the call itself created**; **a timeout leaves pre-existing artifacts byte-identical** (nothing is written on that path); `_final_write` fault-injected → `UNREADABLE reason=stream_write_failed`; failing only the stderr write leaves the stdout artifact current with `written: stdout` / `failed: stderr` detail lines |
| AC-3.11–3.12 | a block reading `$FIXTURE_VAR` runs with `preamble="FIXTURE_VAR=…"` and its text is unchanged (the `Block.text` the API returns is byte-identical to the fence body); preamble **and** `subs` together — the executed text carries the substituted value, proving the preamble is composed with `text′`; the same with a preamble that has **no trailing newline**, proving the composition inserts the boundary; a preamble that fails (`false`) under strict mode is visible as the combined `rc` and stderr; `--preamble-file` on the CLI; an unreadable preamble path **and a preamble file containing an invalid UTF-8 byte** → `UNREADABLE reason=preamble_unreadable`, and the block leaves no side effect |
| AC-2.8 | `--subst K`, `--subst =V` → `BAD_SUBST arg=<raw>`; `--subst K=a --subst K=b` → `BAD_SUBST` with `duplicate_key: K`; `--subst K=a=b` substitutes the value `a=b`; each refusal executes nothing and reserves nothing |
| AC-3.13 | the block itself runs `stat -f %Lp .` (macOS) / `stat -c %a .` (GNU) and the test asserts `700` **from the block's stdout**, so the mode is observed from inside the running block, not inferred from the API — **with `os.umask(0o777)` set around the call and restored in `finally`**, which is what proves the chmod rather than the umask produced it; the source contains no `mktemp` invocation — argv token or shell command word, the same predicate as AC-5.3 |
| AC-3.14 | a block running `mkdir keep && chmod 000 keep` → `run_block` raises `CleanupFailed(path, cleanup_error)` with `cleanup_error` the `PermissionError` and the CLI prints `CLEANUP_FAILED path=<p>`, exit 2, no `rc=` (skipped when `euid == 0`); the test then `chmod 700`s and removes the tree in its own `finally`; `test_cleanup_failure_carries_the_os_error` and `test_cleanup_readback_catches_silent_retention` fault-inject `rmtree` (raising / no-op) and run everywhere; a normal run reads back absent (also AC-3.1) |
| AC-4.6 | `mkdtemp` fault-injected → `LAUNCH_FAILED stage=mkdtemp`, exit 2; `os.chmod` fault-injected → `LAUNCH_FAILED stage=mkdtemp` and the directory `mkdtemp` created is gone; `PATH=<empty dir>` → `LAUNCH_FAILED stage=spawn` and the cwd is gone; `os.killpg` raising `PermissionError` under a timed-out block → `LAUNCH_FAILED stage=reap` within the drain bound, cwd gone, `pgid=` in the detail — the fake records the pgid and the test's `finally` sends the real `SIGKILL` to it and asserts the group is gone; each carries an `os_error:` detail line and no `rc=` |
| AC-4.1–4.5 | `RAN` exits 0 with a non-zero block rc; **every** row of the verdict table exits with the code the table states — 0 for `RAN`, every refusal and `TIMEOUT`, 2 for `UNREADABLE` and `CLEANUP_FAILED` (the test enumerates the table rather than hardcoding a count, so adding or re-classing a verdict cannot leave the test stale); no cannot-judge carries `rc=`; only `AMBIGUOUS` carries `blocks=`; registry ↔ detail-line bidirectional pin; the parser rejects `--all`/`--dir` and abbreviated long options (`allow_abbrev=False`) |
| AC-5.1–5.4 | sleeping block → `TIMEOUT`; no surviving descendant after reap; **no `timeout`/`gtimeout` INVOCATION** — an argv token or shell command word, never a substring, since the source legitimately contains `timeout=`, `TimeoutExpired`, `BlockTimeout` and `--shell-timeout`; temp cwd removed after timeout |
| AC-5.6 | `--shell-timeout` `0`, `-1`, `nan`, `inf` and `abc` each → `BAD_TIMEOUT value=<v>`, exit 0, and a block with a side effect leaves none; `run_block(block, timeout=0)` raises `BadTimeout` with no child spawned (asserted by wrapping `subprocess.Popen` in a recording pass-through that must not have been called — an observation of the real call, not a fault injection, so the two-exception rule in Test Strategy stands) |
| AC-5.5 | `test_timeout_survives_a_group_that_already_emptied`: `os.killpg` monkeypatched with a fake that **really kills the group, waits for it to empty, then** raises `ProcessLookupError` → still `TIMEOUT`, cwd absent, no traceback, nothing left running (asserted with `os.kill(pgid, 0)` in `finally`); `test_timeout_drain_is_bounded_against_an_escapee`: the block starts an `os.setsid()` python child that writes its pid to an absolute path (outside the cwd, via the substitution map — the AC-5.2 idiom) and sleeps holding stdout, then the leader sleeps; `run_block(timeout=1)` raises `BlockTimeout` within `1 + DRAIN_SECONDS + 2` s wall time, the cwd is absent, and the test kills the escapee from the pid file in its `finally` |
| AC-6.1–6.6 | tag present on the Second-surface fence **and exactly one tagged opener across `h-mad/` and `handoff/` excluding `archive/`** (the plan's census sweep, asserting cardinality 1); no `re.findall(r"```bash` left in the consumer; the four migrated behaviours still pass; **the full suite passes AND its collected count is >= the pre-change baseline plus this feature's added tests** (both halves — a passing suite that silently lost tests satisfies neither): `test_suite_floor_holds` runs `pytest --collect-only -q` in a subprocess (collection executes nothing, so the suite cannot recurse; `DOCBLOCK_FLOOR_INNER=1` makes an inner instance skip regardless) and asserts collected >= `2747` + the collected count of `test_h_mad_doc_block_exec.py` alone + 5, the five being the named node IDs added to `test_h_mad_collect_report_docs.py` (`test_gate_block_resolves_through_doc_block_exec`, `test_recipe_runs_through_run_block`, `test_gate_block_refuses_an_untagged_recipe`, `test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`), each asserted present; the pass half is the Phase-5f gate command run alone outside the suite — `pytest … > log; RC=$?; tail -1 log; echo "SUITE: rc=$RC"`, gated on both the `passed` line and `rc=0`, never a bare `| tail -1` whose status is `tail`'s; and the two wire directions — the AC-6.5 spies are installed with `monkeypatch.setattr(dbe, …)` on the consumer's module alias, which is why the consumer must call `dbe.extract`/`dbe.run_block` and a test pins that it has no `from h_mad_doc_block_exec import` |


**Helper mutation spec — `h-mad/tests/mutation-specs/doc_block_exec.json`, entry by entry.** Every
guard below carries one mutation and the one named test that must go RED under it; the spec's
`command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_doc_block_exec.py", "-q"]` and its
`target_command` is `["python3.11", "-m", "pytest", "-q"]`, so the harness credits a mutation only
through its `test` key. Exact `find` anchors are set from the landed source in the same task that
lands it (the author-together ordering the plan states for `docsections.json`), each exact-once;
the mechanism column is what the anchor must express. `ALL_CAUGHT` is required.

| mutation | guard it removes (mechanism) | killed by (`test` key) |
|---|---|---|
| `tag-check-removed` | `extract` returns every ```bash fence, tagged or not | `test_untagged_fence_is_not_a_candidate` (AC-1.1/1.2) |
| `fence-run-length-ignored` | any ``` line closes a fence, regardless of run length | `test_quoted_tag_inside_longer_fence_is_not_an_opener` (AC-1.6) |
| `section-bound-ignores-level` | the section ends at the next heading of *any* level | `test_section_owns_deeper_headings` (AC-1.5) |
| `duplicate-heading-takes-first` | `AmbiguousHeading` never raised; first match wins | `test_duplicate_headings_refuse` (AC-1.7) |
| `select-first-on-ambiguous` | `select` returns `blocks[0]` when >1 and no index | `test_two_tagged_blocks_without_index_are_ambiguous` (AC-1.3) |
| `index-below-one-accepted` | `index < 1` reaches `blocks[index - 1]` | `test_index_zero_refuses` (AC-1.9) |
| `missing-key-silently-skipped` | a zero-count key is not collected | `test_absent_key_refuses` (AC-2.2) |
| `overlap-resolved-by-order` | substring keys proceed in iteration order | `test_overlapping_keys_refuse` (AC-2.7) |
| `counts-taken-up-front` | all counts computed before any replacement | `test_value_containing_another_key_does_not_corrupt_counts` (AC-2.6) |
| `subst-split-on-every-equals` | `--subst` split on every `=` | `test_subst_value_may_contain_equals` (AC-2.8) |
| `subst-duplicate-key-last-wins` | a repeated `--subst` key overwrites instead of refusing | `test_duplicate_substitution_key_refuses` (AC-2.8) |
| `unknown-info-key-ignored` | an unrecognised token falls back to strict | `test_unknown_info_key_refuses` (AC-3.7) |
| `strict-flags-dropped` | `bash -c` always, never `-euo pipefail` | `test_unset_variable_fails_under_strict` (AC-3.3) |
| `preamble-separator-dropped` | composition is `preamble + text′`, no newline | `test_preamble_without_trailing_newline_still_precedes_the_block` (AC-3.11) |
| `preamble-composed-with-unsubstituted-text` | composition uses `block.text`, not `text′` | `test_preamble_and_substitution_compose` (AC-3.11) |
| `stream-reserved-with-truncation` | reservation opens `"w"` instead of `"a"` | `test_stdout_survives_a_failed_stderr_reservation` (AC-3.8) |
| `stream-alias-check-removed` | the `fstat` `(st_dev, st_ino)` comparison is gone | `test_hard_linked_stream_paths_refuse` (AC-3.9) |
| `chmod-0700-removed` | `os.chmod(cwd, 0o700)` after `mkdtemp` is gone | `test_cwd_mode_is_0700_under_hostile_umask` (AC-3.13) |
| `cleanup-errors-ignored` | `ignore_errors=True` restored | `test_cleanup_failure_carries_the_os_error` (AC-3.14) |
| `cleanup-readback-removed` | the `lexists` read-back is gone | `test_cleanup_readback_catches_silent_retention` (AC-3.14) |
| `precedence-timeout-raised-in-handler` | `BlockTimeout` raised inside the handler instead of recorded as pending | `test_cleanup_failure_outranks_timeout_injected` (AC-3.14) |
| `exit-partition-flipped` | refusals exit 2 | `test_verdict_table_exit_codes` (AC-4.2) |
| `rc-leaked-into-refusal` | a refusal line carries `rc=` | `test_no_refusal_carries_rc` (AC-4.3) |
| `launch-oserror-unwrapped` | `mkdtemp`/`Popen` `OSError` propagates as a traceback | `test_mkdtemp_failure_is_a_verdict` (AC-4.6) |
| `killpg-replaced-by-kill` | `proc.kill()` instead of `os.killpg(proc.pid, …)` | `test_in_group_descendant_is_reaped` (AC-5.2) |
| `killpg-esrch-uncaught` | `ProcessLookupError` from `killpg` propagates | `test_timeout_survives_a_group_that_already_emptied` (AC-5.5) |
| `drain-unbounded` | the post-kill `communicate` has no timeout | `test_timeout_drain_is_bounded_against_an_escapee` (AC-5.5) |
| `timeout-validation-removed` | `math.isfinite(t) and t > 0` is gone | `test_nonpositive_timeout_refuses_before_spawn` (AC-5.6) |
| `chmod-failure-unwrapped` | a failing `os.chmod` propagates and the created cwd is left behind | `test_chmod_failure_is_a_verdict_and_removes_the_cwd` (AC-3.13/4.6) |
| `chmod-rollback-unguarded` | the chmod failure removes the cwd outside the `finally` selection, so a failing removal is a traceback | `test_chmod_rollback_failure_is_cleanup_failed` (AC-3.13/3.14) |
| `tilde-fence-not-tracked` | `~~~` fences are not tracked, so a quoted ```bash opener inside one is a candidate | `test_tag_quoted_inside_a_tilde_fence_is_not_an_opener` (AC-1.6) |
| `cleanup-error-ignored-when-tree-gone` | `CleanupFailed` only when `lexists`, a recorded error alone is dropped | `test_cleanup_error_after_successful_removal_is_still_a_failure` (AC-3.14) |
| `empty-key-accepted-by-api` | `substitute` accepts `""` and calls `str.replace("", v)` | `test_empty_key_is_refused_by_the_api` (AC-2.8) |
| `no-timeout-invocation-guard-removed` | *(not a mutation of the helper — the AC-5.3 source scan is a test of the source, so its "mutation" is the test itself failing on a planted `timeout 5 bash` token in a fixture copy)* | `test_no_timeout_invocation_in_source` (AC-5.3) |

Thirty-four rows: thirty-three mutations plus the AC-5.3 self-check; a guard added later without a
row here is what the base Mutation verification invariant forbids, and the impl-plan audit reads
this table against the landed spec.

Verification commands:

```bash
python3.11 -m pytest h-mad/tests/test_h_mad_doc_block_exec.py -q
python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_block_exec.json
python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_block_exec_wire.json
python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/docsections.json   # re-pointed anchors, named-test form: ALL_CAUGHT required
python3.11 -m pytest -q -p no:cacheprovider > /tmp/doc_block_exec_suite.log; RC=$?   # full suite, run alone
tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"                           # gate on both lines
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
- **Audit-gate signal discipline** — complies, on the invariant's own partition: one `DOCBLOCK:`
  token; **exit 0 on every verdict**, refusals and `TIMEOUT` included, so a declined run never
  registers as a tool failure; exit 2 only for genuine operational errors — `UNREADABLE` (input
  that could not be read, an artifact path that could not be written or reserved, a write that
  failed), `CLEANUP_FAILED` and `LAUNCH_FAILED` (the helper's own `mkdtemp`/`Popen`/`killpg`
  raised). A caller reads the token, never `$?`. An earlier draft exited 2 on
  every refusal after `MUTATION: PRECHECK_FAILED`; that copied the minority precedent, and the
  gate and assembler (`GATE: FAIL` / `ASSEMBLE: HALT`, both exit 0) are the rule.
- **No new external dependency** — complies: no new CLI, no package. `bash` is already assumed by
  every recipe in this skill.
- **Portable time bounds** — complies: the bound is Python's own (`Popen.communicate(timeout=…)`).
  AC-5.3 bans an **invocation**, not the substring: the source legitimately contains
  `timeout=`, `TimeoutExpired`, `BlockTimeout` and the `--shell-timeout` flag, and a substring ban
  would reject the very design that satisfies the invariant. The test asserts no `timeout`/
  `gtimeout` appears as an argv token or as a command word inside a shell string.
- **Mutation verification** — complies: every guard carries a mutation with a named `test` key, so
  a mutant killed by an unrelated assertion is reported as a survivor rather than a catch. The
  helper's own cleanup is held to the same rule: `rmtree` is read back rather than trusted, and
  restoring `ignore_errors=True` is itself a mutation the AC-3.14 test must kill.
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
- v1.10: Design audit v5 (codex must 4 + agy must 9, union): BAD_INDEX for ordinals below 1; verified cleanup with CLEANUP_FAILED and read-back, precedence over TIMEOUT; both timeout races specified (ProcessLookupError on killpg, bounded drain against an escapee, DRAIN_SECONDS); extract docstring no longer contradicts AmbiguousHeading; PreambleUnreadable mapped; AC-3.12 combined-invocation contract stated; Test Plan covers AC-1.7, 1.9, 3.11-3.14, 5.5 and the collect-alone import; docsections.json re-point; the one permitted monkeypatch named.
- v1.11: Plan re-audit v12 back-propagation: fence_aware_end signature in the API block and __all__; consumer calls module-qualified for the wire spies (Components + Test Plan).
- v1.12: Plan re-audit v13 back-propagation: --preamble-file in the CLI line; stream artifacts reserved at pre-check with overwrite semantics and StreamWriteFailed; CleanupFailed carries its cause, with the two cleanup mutations and the tests that kill them; the second named fault injection (rmtree).
- v1.13: Plan re-audit v14 back-propagation: composition rule in the preamble paragraph; allow_abbrev=False on the parser; Test Plan rows for both.
- v1.14: Design audit v6 (agy must 1, codex must 2 should 2): composition uses text-prime (substituted); Popen text=True utf-8 replace; timeout validated finite and positive before spawn (BadTimeout/BAD_TIMEOUT); stream artifacts probed for append then reserved after every check; tree-wide single-tag cardinality test; Test Plan rows for each.
- v1.15: Design audit v7 (codex must 4 should 1; agy clean): reservation last, append-mode, truncate at the final write, created-file unlink on a failed second reservation; three post-spawn exit-2 verdicts with explicit precedence; SUBST_OVERLAP keys= and ordering defined; docsections.json named-test form; computed AC-6.4 floor.
- v1.16: Design audit v8 (codex must 3 should 1, agy must 2): exit-code partition per the base invariant in the verdict table, diagram and Invariant Compliance; pending-outcome control flow so CLEANUP_FAILED really outranks TIMEOUT, with the combined test; substitute returns a new Block and run_block never substitutes; main's order corrected; floor test runs collect-only in a subprocess with an env guard and the pass half is the out-of-suite gate command; the five consumer-file node IDs enumerated.
- v1.17: Design audit v9 (codex must 3 should 1; agy clean): LaunchFailed for mkdtemp/Popen/non-ESRCH killpg with a reap stage that never waits unboundedly; alias judged on fstat of the reserved handles; CleanupFailed carries cleanup_error separately from __cause__; three named fault injections plus the real empty-PATH spawn failure; the suite gate captures RC before tail.
- v1.18: Design audit v10 (codex must 2 should 1, agy must 1): four post-spawn outcomes with LAUNCH_FAILED stage=reap placed in the precedence; the exception table names descriptor-level alias detection and the reservation open, matching the Detailed Design; DocUnreadable and PreambleUnreadable wrap UnicodeDecodeError under strict UTF-8.
- v1.19: Design audit v11 (codex must 3; agy must 1 + 2 nits): chmod 0o700 after mkdtemp with the umask probe; reap-failure policy and the test teardown that reaps the launched group; BAD_SUBST parser contract with BadSubstArg; main's order puts the alias check after reservation; substitute wording and the API raises list corrected.
- v1.20: Design audit v12 (codex must 2; agy must 3): verification commands run the docsections.json harness and the status-preserving suite gate; Invariant Compliance names LAUNCH_FAILED among the exit-2 classes.
- v1.21: Design audit v13 (codex must 2; agy clean): the helper mutation spec is enumerated — 27 entries with mechanism and the named RED test each — and the timeout-vs-cleanup precedence is carried by an injected test that runs everywhere, with the permission fixture as its root-skipped sibling.
- v1.22: Design audit v14 (codex must 5; agy must 2): timeout validated before mkdtemp in the diagram and prose; LAUNCH_FAILED in the diagram's partition; chmod-failure test and mutation (29 rows); invalid-UTF-8 document and preamble cases in the Test Plan; four named fault injections.
- v1.23: Design audit v15 (codex must 5 should 2; agy clean): tilde fences tracked with the marker character; cleanup failure on recorded error OR read-back; _final_write seam as the fifth injection with ordered writes and reported partial state; empty key refused in substitute; alias row worded on inodes; three new mutations (32 rows).
- v1.24: Design audit v16 (codex must 3; agy clean): the killpg fake models an empty group (kill, wait, then raise); duplicate-key gets its own mutation; the chmod rollback runs inside the same try/finally selection with its own mutation and test (34 rows).
