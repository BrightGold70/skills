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
line before `import h_mad_doc_block_exec as _dbe`, so the import holds when `test_docsections.py`
is collected alone and never depends on a sibling test module having inserted the path first
(the plan names the two tests that pin this); the call is module-qualified,
`_dbe.fence_aware_end(text, start, level)`, so the delegation *wire* can be discriminated by a spy
under an isolated revert of the connection (`docsections.json`'s
`docsections-delegation-reverted`, killed by
`test_docsections_delegates_to_the_authoritative_bounder`). This also
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
        ├── Popen(["bash", *flags, "-c", preamble ⊕ text'], cwd=cwd, start_new_session=True,
        │         text=True, encoding="utf-8", errors="replace")   # cwd=cwd is what makes the
        │                                                            # temp dir the block's cwd
        ├── communicate(timeout) ─── TimeoutExpired ──► poll() ──► killpg(SIGKILL) [ESRCH = already reaped;
        │                                                 poll() first, else a zombie-only group is EPERM on macOS]
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
before a successful run. **Exactly five non-`RAN` outcomes can follow a spawn, in this
precedence:** `CLEANUP_FAILED` (exit 2 — selected after cleanup and read-back have run, so it
outranks everything), then `LAUNCH_FAILED stage=reap` (exit 2 — a timed-out block whose group
could not be signalled; it outranks the timeout it implies because an unkillable child is the
more urgent finding), then `UNREADABLE reason=stream_close_failed` (exit 2 — `main`'s backstop
close of a held stream handle failed after the block's outcome was already decided; it is selected
by `main` after its reservation `try`/`finally`, so it can only ever replace the exit-0 `TIMEOUT`
below it — the two exit-2 outcomes above it are already-pending errors and win, with the close
error chained as `__context__`), then `TIMEOUT` (exit 0 — a measured fact about the block), then
`UNREADABLE reason=stream_write_failed` (exit 2 — only reachable on the path that would otherwise
print `RAN`, because streams are written only after a successful, cleaned-up run). The `mkdtemp`
and `spawn` stages of `LAUNCH_FAILED` are pre-spawn by definition and sit outside this list, and so
are the pre-spawn refusals. None
of the five carries `rc=`, and on the first four nothing is written to any artifact; nothing that ran is reported as a
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
- Any other token, or `shell=` with any other value, is `BAD_INFO` — and so is a **duplicated**
  recognised token (`hmad:exec hmad:exec`, `shell=strict shell=plain`), refused deterministically
  as `BAD_INFO key=<the repeated token>` rather than resolved first-wins or last-wins, because a
  mode nobody unambiguously chose must not run (`test_duplicate_info_tokens_refuse`, mutation
  `duplicate-info-token-last-wins`) — but **only on a fence that carries `hmad:exec`**. Validation follows opt-in: an untagged fence is not a candidate, so its
  info string is never inspected and an unrelated ` ```bash --frozen ` elsewhere in the tree can
  never make this tool refuse. On a tagged fence it is **not** ignored: a typo'd key that silently
  falls back to a default runs the block under a mode nobody chose.

### Scanning (`extract`)

**One private scanner, two consumers.** The fence grammar below is implemented exactly once, as
a private generator `_fence_events(text)` that walks the document and yields, per line, one of
five kinds — fence `open`, fence `close`, fence `body`, ATX `heading` (with its `level`), or
`prose` — together with the opener's marker character, run length, indentation and info string,
and a scanner-derived `candidate` flag (a backtick opener whose first info word is `bash`), so
no consumer re-recognises a fence or a heading. **The `titled_section` migration was measured as a differential before it was prescribed** — the old
`re.search` heading regex against the new selector over every `*.md` under `h-mad/` and `handoff/`
(30 files, `archive/` excluded): `new_only=0` (nothing the old guard refused is newly accepted; the
theoretical softenings `##\tx` and `## x ##` have zero instances) and `old_only=76`, every one a `#`
comment line inside a fence the old regex mistook for a heading — the migration narrows the guard
(plan §Measurements, "Heading selector differential"). **Every grammar rule the scanner implements was
rendered through markdown-it-py 2.2.0 (CommonMark preset) before it was written down — 14 of 14
agree with the renderer; the corpus and its output are in the plan's §Measurements ("Scanner
grammar corpus").** `extract` consumes it to find candidates and
`fence_aware_end` consumes it to bound a section — feeding the scanner **complete source lines
from the top of the document through the line that contains `start`**, then considering a
boundary at every line whose start offset is **≥ `start`** — a line that began before a
mid-line `start` is excluded, and the line beginning exactly at `start` is included, which is the
line adjacent to a heading `find_heading` returned (`test_adjacent_heading_bounds_the_section`: a
heading immediately followed by a same-level heading that owns a tagged block yields no candidate
for the first, and the bounder returns `start` itself; mutation `adjacent-heading-skipped`, the
predicate `>` instead of `≥`, which would hand the next section's block to the wrong address);
never a `text[:start]` slice, which can cut a
line right after its marker run and make a ```` ```trailing ```` body line look like a blank-tailed
closer (hostile fixture: `start` placed immediately after the three backticks of that line inside
an open fence; the next fenced `#` must still not end the section) — and neither function carries
fence state of its own. That is what
makes the two surfaces unable to disagree by construction — a change to marker kind, run length,
indentation, the closer rule or prefix state lands in one place — and it is where every
fence-grammar mutation row anchors (`fence-run-length-ignored`, `tilde-fence-not-tracked`,
`indented-opener-accepted`, `indented-closer-accepted`, `closer-trailing-text-accepted`, `prefix-fence-state-skipped`), so
each mutant is observed by both consumers' tests. The parity guard is observable at the scanner, not through the two public APIs (which expose
only tagged candidates and one boundary offset): `test_fence_events_trace_on_every_hostile_fixture`
runs every hostile fixture (balanced and unbalanced four-backtick, tilde-quoted backtick,
backtick-in-info, indented literal, trailing-text closer, offset-inside-a-fence) through
`_fence_events` and asserts the exact event trace — which lines open, which close, which are body —
and two per-consumer tests then assert `extract`'s candidates and `fence_aware_end`'s boundary on
the same fixtures; a second scanner could not pass the trace test by accident, and the mutation
`scanner-duplicated-in-consumer` (a private fence toggle re-introduced inside `extract`) is killed
by `test_extract_has_no_fence_state_of_its_own`, a source assertion that only `_fence_events`
mentions the marker runs. The scanner carries
`in_fence`, **the opening fence's marker character (backtick or tilde) and its run length**. CommonMark fences come in both flavours, `~~~` closes only a `~~~`
fence, and a tilde fence can quote a backtick fence verbatim — measured through GitHub's renderer
in the spec's Assumptions: a `~~~` block containing ` ```bash hmad:exec ` renders as a plain code
block. Tilde fences are tracked for bounding only; a **candidate** is always a backtick fence whose
first info-string word is `bash`. A
naive "any line starting with ``` toggles" is wrong and would corrupt the state on a document this
feature must handle: CommonMark opens a fence with a run of *N* ≥ 3 backticks and closes it only
with a run of ≥ *N*, so a fence opened with four backticks legitimately contains ``` lines as
body text. This design's own documents contain exactly that shape, because they quote fenced
examples. So:

- a **backtick** opener whose info string contains a backtick is not a fence at all (CommonMark
  §4.5: "the info string of a backtick fence may not contain backticks"), so ```` ```bash hmad:exec `x` ````
  is inert prose — neither a candidate nor a `BAD_INFO` — and the next ``` line opens a fence
  rather than closing one; tilde fences carry no such rule. Measured on both renderers used for
  AC-1.6 (markdown-it-py: `<p>```bash hmad:exec <code>x</code>…`; GitHub `POST /markdown`: the same
  paragraph, with the following line opening a fence that swallowed a tilde block after it);
- an opener is recognised only when its marker run is preceded by **0–3 spaces** (CommonMark
  §4.5): four or more spaces make the line an indented code block, so a literal
  `    ```bash hmad:exec` is never an opener and never a candidate — the security boundary AC-1.6
  states, restated for indentation; the same 0–3 rule applies to a closer — a marker run preceded by
  four or more spaces inside a fence is body text, never the closer (`test_indented_closer_does_not_close`:
  a ```` ```` ```` line at four spaces inside a bash fence stays in the body and the fence ends at the
  next 0–3-space closer; mutation `indented-closer-accepted`) — and **`extract`
  normalises the body**: up to the opener's indentation is stripped from each body line (a line
  indented less than the opener loses only what it has), so the `Block.text` returned is the
  CommonMark content of the fence, not its source bytes — recognising the fence but returning
  un-normalised text is its own defect, with its own test and mutation (`body-indent-not-stripped`);
- an opening fence records its marker character and `n = len(run)`; while open, only a line
  whose leading run is of the **same character** and ≥ `n` **and** is followed by nothing but
  spaces or tabs (CommonMark: a closing fence carries no info string and no other text) closes
  it;
- while `in_fence` is true, no line is examined as a heading or as an opener.

That is what makes AC-1.6 structural rather than a special case: a body quoting
` ```bash hmad:exec ` is inside a fence and is never read as an opener, and a *longer* enclosing
fence keeps it that way.

Heading bounding: locate the line equal to `heading` (exact match, stripped of trailing
whitespace) **among the scanner's `heading` events** — a line inside any fence is never a
heading event, and this lookup is the public `find_heading(text, heading) -> tuple[int, int] | None`
(the offset just past the heading line and its level; `None` when absent; `AmbiguousHeading` on
more than one) that `extract` and `docsections.titled_section` both call, so the section START is
found by one implementation exactly as its END is — so a fenced example that quotes `## <the requested heading>` cannot become the
section start and hand a later real tagged block to the wrong address
(`test_requested_heading_quoted_inside_a_fence_is_not_a_section_start`: the requested heading
appears first inside a ```` ```markdown ```` fence, then for real; the only candidate is the block
under the real heading; mutation `heading-match-ignores-fence-state`); its level is the count of
leading `#`. **A heading line is recognised by the CommonMark ATX rule (§4.2) and nothing looser**: 0–3 leading spaces, a run of 1–6 `#`, then a space, a tab or end of line, with an optional closing `#` run (preceded by a space) stripped before the text is compared — so `#hashtag`, a seven-`#` run, and a four-space-indented `## x` are prose, and the level is the run length of the opening hashes (`test_heading_lookalikes_are_not_headings`: each lookalike placed where it would end or start the section changes nothing; mutation `heading-lookalike-accepted`, the grammar loosened to `line.lstrip().startswith("#")`). **If more than one line matches, `extract`
raises `AmbiguousHeading(n)` rather than taking the first** — duplicate headings are real in this
tree (`h-mad/invariants.example.md` has two of them), and picking one would execute a tagged block
from the wrong section. The opt-in tag guards *which block*; it cannot guard *which section*. **This is ATX-only by design and by
limitation**: a Setext heading (text underlined with `===`/`---`) is not recognised, so a document
using them would bound wrongly rather than loudly. Every document in these skills is ATX, and the
after AC-1.8 `docsections.py` calls this same bounder, so the assumption has exactly one home
and cannot drift between two implementations (the differential test an earlier draft named here
is the one this document explains is not achievable). The section ends at the next line that is a
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

**Replacement is simultaneous, and counts are taken on the original text** (AC-2.6). Every key is
counted against `block.text` as written, and the replacement is one pass over that text — a
single compiled alternation of the escaped keys, `re.sub("|".join(map(re.escape, keys)), lambda
m: subs[m.group(0)], text)` — so replaced text is never re-scanned. **An empty map short-circuits
before that line**: `substitute(block, {})` returns `(dataclasses.replace(block), {})` — a
zero-key alternation is `""`, which matches the empty string at every position and would raise
`KeyError("")` from the callback — and this is the ordinary path for a CLI invocation with no
`--subst`, so it is covered by both an API test and a zero-`--subst` CLI test
(`test_empty_substitution_map_is_a_no_op`, mutation `empty-map-not-short-circuited`). That is what makes the result
order-independent: with `A→B` and `B→C` on a block containing `A B`, the outcome is `B C`
whatever the map's iteration order, whereas the sequential count-then-replace an earlier draft
prescribed yields `C C` when `A` is replaced first and `B C` when `B` is — an outcome that
depends on dict order, exactly the surprise AC-2.7 refuses overlapping keys to avoid,
re-created one step later. Overlap refusal (below) is what makes the alternation unambiguous, so
no key can match inside another. Each reported count is the number of matches in the original
text, which is the number replaced (AC-2.5).

**Overlapping keys refuse** (AC-2.7). If any key is a substring of another, the result depends on
iteration order, and a silently order-dependent answer is the failure class this whole feature
exists to catch. `SUBST_OVERLAP keys=<n>` with a detail line per offending pair, exit 0, nothing
executed — rather than picking an order and documenting it, which only moves the surprise. `<n>`
counts the **distinct keys implicated**, not the pairs (`a`, `ab`, `abc` → `keys=3`, three pairs);
each unordered pair appears once as `overlap: <shorter> <longer>`, and the lines are sorted by
`(shorter, longer)`, so the same map always produces the same diagnostic.

Any key with a count of zero is collected; if the collection is non-empty nothing is executed and
every missing key gets its own detail line, **in the map's insertion order** — an absent key has
no position in the block, so the map (on the CLI, `--subst` argument order) is the only
deterministic order there is; `test_two_missing_keys_are_listed_in_map_order` pins it. **An empty
key is refused here, in the API** —
`BadSubstArg("")` — not only by the CLI parser: `str.replace("", v)` inserts `v` at every character
boundary, and an in-process caller must meet the same wall `main` does.

### Execution

`tempfile.mkdtemp()` **followed by `os.chmod(cwd, 0o700)`** is the cwd. `mkdtemp` alone gives
`0o700 & ~umask` — probed: under `umask 0777` it yields mode `0o0` — so "0700 by construction",
which an earlier draft claimed, was only true under the default umask; the chmod makes AC-3.13
true everywhere. **`cwd` is `None` until `mkdtemp` returns**, and cleanup and read-back run only
when it is not `None`: a `mkdtemp` that raises records `LaunchFailed("mkdtemp", err)` with no
directory to remove, so the `finally` and the read-back are skipped rather than tripping over an
unbound name (a literal "always `rmtree(cwd)`" is an `UnboundLocalError` on that path, which is a
traceback where AC-4.6 promises a verdict). **A chmod that fails is not a special rollback path**:
by then `cwd` is set, the chmod runs inside the same `try` whose `finally` removes the cwd, so a failure records `LaunchFailed("mkdtemp", err)`
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

1. **The group empties between `TimeoutExpired` and `killpg`.** The helper first calls
   `proc.poll()` — non-blocking, it reaps the leader if it has already exited — and only then
   `os.killpg(proc.pid, SIGKILL)`, catching `ProcessLookupError` as "already reaped". **The
   `poll()` is load-bearing, not tidiness**: a leader that exited is a zombie until reaped, and
   measured on macOS, `killpg` on a zombie-only group raises `PermissionError`, not
   `ProcessLookupError` (plan §Measurements, the naturally-emptied-group probe); after `poll()`
   the same call raises `ProcessLookupError`. Without the `poll()` the natural race would be
   misreported as `LAUNCH_FAILED stage=reap` (the `poll-before-killpg-removed` mutation).
   **The test needs no fake**: `test_timeout_survives_a_group_that_already_emptied` runs a leader
   that starts an `os.setsid()` descendant holding stdout and exits at once; `communicate` times
   out on the escapee's pipe, `poll()` reaps the zombie, `killpg` raises `ProcessLookupError`, the
   drain times out, the pipes close, `wait()` returns at once, and the verdict is `TIMEOUT` with
   the cwd gone — the test kills the escapee from its pid file in `finally`. That one real fixture
   drives both AC-5.5 races. Any other `OSError` from `killpg` *after* `poll()` (a
   `PermissionError` on a genuinely live child one cannot signal) is **not** allowed to escape as a
   traceback: the helper
   still runs the bounded drain and closes the pipes, does **not** `wait()` (a child it could not
   signal is not something to wait on unboundedly), records `LaunchFailed("reap", err)` as the
   pending outcome with `pgid=<n>` in its detail, and lets cleanup and the read-back run as usual
   (AC-4.6). **Policy for a genuinely unsignalable group is diagnostic, not containment**: the
   helper has no signal that would work where `SIGKILL` to the group did not, so it reports the
   pgid and returns bounded rather than pretending; this is the one documented case in which a
   launched process may outlive the call. **The test for it must not become that case**: its fake
   `killpg` (the AC-4.6 injection, the only remaining use of the `os.killpg` seam) records the pgid
   and raises `PermissionError`. **`run_block` owns its `Popen` and exposes no handle**, so the
   test obtains one through the same recording pass-through AC-5.6 uses: `monkeypatch.setattr(dbe.subprocess, "Popen", recording_popen)`,
   where `recording_popen(*a, **kw)` calls the real
   `subprocess.Popen`, appends the instance to a list the test holds, and returns it unchanged —
   an observation of the real call, not a fault injection, restored by `monkeypatch` on exit. The
   teardown order in the test's `finally` is then exact: (1) real `os.killpg(pgid, SIGKILL)` on
   the recorded pgid; (2) `recorded.wait()` on the recorded handle, which reaps the zombie leader
   (measured: `os.kill(pid, 0)` succeeds on a zombie, so no assertion can pass before this step);
   (3) assert `os.killpg(pgid, 0)` raises `ProcessLookupError`. CPython's `Popen.__del__` never
   kills a live child, so without that teardown the fault-injected test would leave a `sleep`
   running after it returned.
2. **The post-kill drain does not finish.** After `killpg` a second `communicate` collects what
   the group wrote before dying; but a descendant that left the group (AC-5.2's `os.setsid()`
   escapee) still holds the inherited pipes, so that `communicate` can block for as long as the
   escapee lives. It is therefore bounded too — `communicate(timeout=DRAIN_SECONDS)`, a module
   constant of 5 s — and on its own `TimeoutExpired` the helper closes `proc.stdout` and
   `proc.stderr` itself, calls `proc.wait()` **only on the branch where `killpg` succeeded or
   raised `ProcessLookupError`** — the leader is then SIGKILLed or gone, so this returns at once —
   and **never on the `LaunchFailed("reap")` branch**, where the child could not be signalled and a
   `wait()` would be unbounded (the state machine is: drain-with-timeout → close pipes → `wait()`
   iff the group was signalled; the AC-4.6 reap test asserts the bounded return, which is what
   proves that branch skips the wait),
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
launch names the cwd explicitly** — `Popen(…, cwd=cwd, …)`: creating and chmodding the directory
does nothing to the child's working directory by itself, and without the keyword the block runs
wherever the caller does, which is the repository (AC-3.1/3.2 fail silently); the
`cwd-not-passed` mutation pins it. **The launch is text-mode, and the policy is explicit**: `Popen(…, text=True, encoding="utf-8",
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
| Helper mutation spec | `h-mad/tests/mutation-specs/doc_block_exec.json` | new | guards for FR-1..FR-5 — 63 mutations (63 rows: 61 of the helper's source, 2 of `h-mad/SKILL.md`'s registry rows), each bound to its RED test, enumerated under Test Plan |
| Wire mutation spec | `h-mad/tests/mutation-specs/doc_block_exec_wire.json` | new | FR-6 connection, both directions — eight mutations: `wire-revert-extract`, `wire-revert-select`, `wire-revert-run`, `wire-revert-substitute`, `wire-unconditional`, `exec-scan-executes`, `consumer-from-import`, `hand-rolled-extraction-widened`, each bound to its `tests/test_h_mad_collect_report_docs.py::<name>` (table under Test Plan) |
| Registry entry | `h-mad/SKILL.md` (Helper scripts) | modify | contract + remedy rows (AC-4.5) |
| Tagged fence | `h-mad/SKILL.md` (Second surface) | modify | the one opt-in block (AC-6.1) |
| Migrated consumer | `h-mad/tests/test_h_mad_collect_report_docs.py` | modify | drop hand-rolled extraction (AC-6.2); calls are module-qualified (`import h_mad_doc_block_exec as dbe` → `dbe.extract`/`dbe.select`/`dbe.run_block`) so the wire spies observe them |
| Delegating bounder | `h-mad/tests/docsections.py` | modify | import the authoritative module; drop the duplicate `_fence_aware_end` **and** the local heading regex in `titled_section` — both the section start (`_dbe.find_heading`) and its end (`_dbe.fence_aware_end`) come from the scanner (AC-1.8) |
| Delegation spy test | `h-mad/tests/test_docsections.py` | modify | gains `test_docsections_delegates_to_the_authoritative_bounder`, which spies BOTH `_dbe.find_heading` and `_dbe.fence_aware_end`, the killer of `docsections.json`'s two wire mutations and one of the seven floor-tuple node IDs (AC-1.8, AC-6.4); the hostile `test_titled_section_ignores_a_heading_inside_a_fence` lives in the new module beside the other docsections-side tests |
| Bounder mutation spec | `h-mad/tests/mutation-specs/docsections.json` | modify | re-point `fence-tracking-removed` and `section-no-longer-owns-its-subsections` at `scripts/h_mad_doc_block_exec.py`; the other two anchors stay in `tests/docsections.py`; all four gain a `test` key (from their `_killed_by`) under a `target_command`; a fifth, `docsections-delegation-reverted` (local bounder restored, callee intact), is the Connection-enforcement wire mutation, killed by `test_docsections_delegates_to_the_authoritative_bounder` with the helper's behaviour tests still green — the one designed exception being the source guard `test_docsections_has_no_second_bounder`, which goes red on exactly this mutant because restoring a local toggle is the second bounder it exists to refuse; a sixth, `docsections-syspath-setup-removed` (the `sys.path.insert` that makes the delegating import self-contained is deleted), is killed by `tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd` — a fresh `python3 -c "import docsections"` with only the tests dir on `sys.path` and `cwd=tmp_path`, a process that has imported nothing else — so the wire's import cannot ride another module's `sys.path` side effect; a seventh, `docsections-heading-lookup-reverted` (the local heading `re.search` restored, `find_heading` untouched), is killed by the same delegation spy, whose `find_heading` recorder then sees no call |

## Implementation Order

1. **Task 1 — scanner, selection, info-string grammar, and the bounder's second consumer.** In
   `h-mad/scripts/h_mad_doc_block_exec.py` (new): `Block`, the private `_fence_events` scanner,
   `fence_aware_end` with the full fence rule, `find_heading`, `extract`, **`select`** (the ordinal policy — `BlockNotFound`, `AmbiguousBlock`,
   `BadIndex` — without which `main` has no specified way from `list[Block]` to the one `Block`
   `substitute` and `run_block` take), tag and key validation; tests in
   `h-mad/tests/test_h_mad_doc_block_exec.py` (new) and the matching rows of
   `h-mad/tests/mutation-specs/doc_block_exec.json` (new). **In the same task**,
   `h-mad/tests/docsections.py` drops `_fence_aware_end` and its local heading regex and delegates through
   `_dbe.find_heading` and `_dbe.fence_aware_end`, `h-mad/tests/test_docsections.py` gains the delegation spy test, and
   `h-mad/tests/mutation-specs/docsections.json` is re-pointed, converted to named-test form and
   run to `ALL_CAUGHT` (the author-together ordering the plan requires). Satisfies FR-1 (incl. AC-1.8/1.9) and AC-3.7. New-behaviour shape, plus one wire.
2. **Task 2 — substitution.** `substitute` in `h-mad/scripts/h_mad_doc_block_exec.py`: simultaneous
   replacement, counts on the original text, missing-key collection, overlap and empty-key
   refusal, the empty-map no-op; its tests and mutation rows in the same two files as Task 1.
   Satisfies FR-2. Depends on Task 1 only for `Block`.
3. **Task 3 — execution and bounding.** `run_block` and **`RunResult`** in
   `h-mad/scripts/h_mad_doc_block_exec.py`: temp cwd (`mkdtemp` + `chmod`, `cwd` `None` until
   created), shell modes, preamble composition, the `poll()`-then-`killpg` process-group timeout,
   bounded drain, pending-outcome cleanup selection, and the exceptions those paths raise —
   `BadTimeout`, `BlockTimeout`, `LaunchFailed`, `CleanupFailed`; tests and mutation rows as
   above. Satisfies FR-3 and FR-5. Depends on Task 1.
4. **Task 4 — CLI and registry.** `main(argv)` in `h-mad/scripts/h_mad_doc_block_exec.py`: every
   verdict line in the table below, argument-value validation (`--index`, `--shell-timeout`,
   `--subst` syntax), the strict-UTF-8 pre-spawn read of `--preamble-file` (`PreambleUnreadable`),
   the two-arm stream reservation,
   descriptor alias check, `_final_write` with read-back verification, one closure path; and the
   Helper-scripts registry entry in `h-mad/SKILL.md` pinned bidirectionally (the two `SKILL.md`
   mutation rows land here). Satisfies FR-4, AC-3.8/3.9. Depends on 1–3.
5. **Task 5 — the wire.** Tag the Second-surface gate fence in `h-mad/SKILL.md` **and** migrate
   the executing call site in `h-mad/tests/test_h_mad_collect_report_docs.py` — a new
   `_gate_block() -> dbe.Block` resolving through `dbe.extract`/`dbe.select`, `_gate_bash_block() ->
   str` reduced to `_gate_block().text` so its two text-pin callers keep their string, and
   `run_recipe`, hoisted out of its enclosing test to a module-level
   `_run_recipe(*, phase, cycle, report, root) -> dbe.RunResult` — calling `dbe.run_block(subbed, preamble=preamble, timeout=60.0)`, an explicit bound the wire pin asserts — so a wire pin can call and spy it
   (its two call sites read only `.stdout`/`.stderr`, which `RunResult` carries) — in one task, with
   `h-mad/tests/mutation-specs/doc_block_exec_wire.json`
   (new) and the six named tests in that file — **and, authored here rather than in Tasks 1–4
   because they assert post-Task-5 state, `test_exactly_one_tagged_fence_in_the_tree` (the tag
   exists only after this task) and `test_suite_floor_holds` (its seven-node tuple exists only
   after this task), both still living in `h-mad/tests/test_h_mad_doc_block_exec.py`**. `:412` in
   the same file is deliberately untouched:
   it selects a *different*, untagged block (`exec codex`) and only inspects it, so it neither
   breaks nor belongs behind an executor. Satisfies FR-6. **Wiring shape**, not new behaviour.
   Depends on 1–4. Tag and migration cannot be split: tagging the gate fence makes `:270`'s
   `re.findall` match zero blocks.

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
    rc: int          # exit code of the ONE `bash -c` spawned (block alone, or
                     # preamble+block combined) — never the tool's verdict
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
def extract(doc: str | Path, heading: str) -> list[Block]:
    """Pure scan. `doc` is a PATH (a str is converted with Path), read as
    strict UTF-8 — never document text. Returns every tagged block under `heading`, possibly empty.
    Raises DocUnreadable, BadInfoString or AmbiguousHeading — never on candidate count."""

def select(blocks: Sequence[Block], index: int | None = None) -> Block:
    """Policy. Raises BadIndex(n) (index given and < 1 — validated BEFORE any
    lookup, so 0 can never reach `blocks[index - 1]` and alias the last block),
    BlockNotFound (0 candidates, or index past the end) or AmbiguousBlock(n)
    (>1 with no index)."""

def substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]:
    """Returns a NEW Block (dataclasses.replace) whose text has every key replaced,
    plus the per-key counts. run_block never substitutes: main calls this first,
    so a bad map is refused before any stream artifact is reserved."""

def run_block(block: Block, *, preamble: str | None = None,
              timeout: float = 30.0) -> RunResult
def main(argv: Sequence[str] | None = None) -> int

def fence_aware_end(text: str, start: int, level: int) -> int:
    """Offset of the next ATX heading at `level` or shallower after `start`,
    skipping fenced blocks under the full CommonMark fence rule: backtick AND
    tilde runs of >= 3, closed only by the same character at >= the opening
    length, opener and closer indented 0-3 spaces (4+ is an indented code
    block, never a fence). Fence state is established over COMPLETE lines
    from the document start through the line containing `start` (never a
    text[:start] slice, which can truncate a line after its marker run and
    fake a closer); a line is a candidate boundary iff its start offset is
    >= `start` (the line adjacent to a heading is included; a line that began
    before a mid-line `start` is not). So `start` may lie anywhere -- inside an open fence included -- and a
    fenced `#` after an arbitrary offset is never read as a heading; that is
    the contract `docsections.section_from` needs for its symbol-anchored
    offsets. The bounder `extract` uses, exported so
    `h-mad/tests/docsections.py` can delegate to it (AC-1.8)."""
```

```python
def find_heading(text: str, heading: str) -> tuple[int, int] | None:
    """Offset just past the ATX heading line equal to `heading` (stripped) and its
    level, found among the scanner's heading events only — never inside a fence.
    None when absent; raises AmbiguousHeading(n) when more than one matches."""
```

`__all__` names all seven. `fence_aware_end` and `find_heading` are public on purpose:
`docsections.titled_section` calls `find_heading` in place of its own `re.search` heading regex
and then `fence_aware_end` in place of the deleted `_fence_aware_end`; `docsections.section_from`
calls `fence_aware_end` with the same `(text, start, level)` arguments. A heading `find_heading`
reports absent keeps `docsections`' own loud failure (`test_a_missing_heading_fails_loudly`). Both it and `extract` are thin consumers of the private
`_fence_events(text)` generator (§Scanning), the single home of the fence grammar; the two
re-pointed `docsections.json` mutations therefore target `_fence_events`'s state transition and
`fence_aware_end`'s heading match, and every fence-grammar row of `doc_block_exec.json` anchors in
`_fence_events` too, where one mutant is seen by both consumers.

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

`substitute` raises `MissingSubstitution(keys)`, `OverlappingSubstitution(pairs)` or `BadSubstArg("")`;
`run_block` raises `BadTimeout(value)`, `BlockTimeout(seconds)`, `CleanupFailed(path, cleanup_error)`
or `LaunchFailed(stage, err, pgid=None)`.
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
other is still unreserved. **Creation is detected atomically, not by an `exists()` check**: the
reservation is a two-arm loop: try `os.open(path, O_WRONLY | O_APPEND | O_CREAT | O_EXCL)` —
success means this call created the file and records `created=True`; on `FileExistsError` try
`os.open(path, O_WRONLY | O_APPEND | O_NONBLOCK)` **without `O_CREAT`** — success means a
pre-existing file (`created=False`). **The whole reservation stage is one mapped region**: the
two-arm loop, the `fstat` regular-file and alias checks on the descriptors, and the rollback of a
first reservation when the second fails (close, and unlink only if this call created it) sit inside
one `try`/`except OSError` mapped to `StreamPathUnwritable`, so no `OSError` from any of those calls
can escape as a traceback. `test_stream_path_under_a_regular_file_refuses` gives `--stdout` a path
whose parent is a regular file (`ENOTDIR` on both arms — a real fault, no injection, no permission
dependence) and asserts `UNREADABLE reason=stream_path_unwritable`, exit 2, no traceback, and a
side-effect block that left nothing; mutation `stream-open-oserror-unwrapped` (the region's `except
OSError` removed) turns that refusal into a traceback. `O_NONBLOCK` is what keeps the open **bounded**: on a FIFO
with no reader a blocking open never returns (no `DOCBLOCK:` line, no timeout — the block has not
even been spawned), whereas with `O_NONBLOCK` it fails at once with `ENXIO` — measured on the
supported interpreter (plan §Measurements cites the command): `OSError errno=6 (ENXIO) after
0.0000s` on python 3.11.8 / darwin, and with a reader present the open succeeds and `fstat`
reports `S_ISREG=False S_ISFIFO=True`, which is the case the regular-file check below refuses. Every descriptor from
either arm is then `fstat`ed and must be a **regular file** (`stat.S_ISREG`); a FIFO, socket,
device or directory is closed and refused as `StreamPathUnwritable`
(`UNREADABLE reason=stream_path_unwritable`), checked on the descriptor rather than the path so
there is no check-to-open race, and a file this call created that turns out non-regular cannot
exist (an exclusive create makes a regular file). `test_stream_path_fifo_without_reader_refuses_bounded`
makes a `os.mkfifo` path the `--stdout` and asserts the refusal arrives within a second and the
block ran nothing; mutation `nonregular-stream-accepted` (the `S_ISREG` check removed) and
`stream-open-blocking` (`O_NONBLOCK` dropped, which the same FIFO test catches by timing out its
own bounded wait); on `FileNotFoundError` there (the file vanished between the two opens) go back
to the exclusive-create arm. Because the second arm can never create, every file this call
creates is created by the exclusive arm and recorded as such — a plain retry with `O_CREAT`
would create a fresh file and mis-record it as pre-existing, which is exactly what a later refusal
must not leave behind. The loop is bounded (three round trips, then `StreamPathUnwritable`), and
`O_NOFOLLOW` is not used: a symlinked artifact path is legitimate and the alias check below judges
what it resolves to. The descriptor is wrapped with `os.fdopen(fd, "a", encoding="utf-8")`. If the second reservation fails, the first
handle is closed and — only if `O_EXCL` succeeded for it — unlinked, so a pre-existing artifact
keeps every byte, a refusal leaves no new empty file, and there is no window in which another
process's file could be mistaken for one this call created. The truncation is the final write itself:
on the `RAN` path, after cleanup succeeded, each held handle gets `seek(0); truncate(); write(…);
flush(); close()` — all five inside `_final_write`, **with the `close()` in a `finally`**: if
`seek`, `truncate`, `write` or `flush` raises, the handle is still closed before the exception is
mapped, and an error from that close is caught in the same region and mapped too (the first error
wins, the close error is chained as `__context__`), so no descriptor and no traceback can escape
past `stream_write_failed` — `main`'s outer `finally` is a backstop for the alias-refusal and
timeout paths, never the mapping for a write failure. Two tests pin this, and neither can be
satisfied by the outer `finally` closing the handle later. Both go through the **fifth named
injection** — the `_final_write` seam — and add no sixth: the patched seam calls the real
`_final_write` with a recording proxy around the held handle (every attribute forwarded, only
`flush`/`close` overridden as the test directs, `close` marking the proxy closed and recording
the call), so `main`'s outer `finally` still closes the *real* handle and never sees the proxy.
`test_final_write_close_failure_is_mapped` makes the proxy's `close` alone raise `OSError`
(`flush` succeeds) and asserts `main` returns 2, the verdict is `stream_write_failed` with
`failed: stdout`, and no traceback reaches stderr — a `close()` outside the mapped region lets
that error escape as a traceback. `test_final_write_failure_before_close_still_closes` makes
**both** the proxy's `flush` and `close` raise and asserts the same verdict, no traceback, and
that the proxy's `close` **was called** — which only `_final_write`'s own `finally` can do,
because the outer `finally` holds the real handle. A `close()` moved out of the `finally` skips
the close when `flush` raises: the verdict still maps, the outer `finally` closes the real
handle, and the proxy's `close` is never called, so the assertion fails. Both tests are the kill
for mutation `final-write-close-not-in-finally`; Phase 5e runs that mutant and records its RED
in the mutation spec. It is all inside `_final_write` because a buffered `TextIOWrapper` may defer
the OS write (and even the truncate) until `flush()` or `close()`, and an `OSError` surfacing at a
close *outside* the mapped region would escape as a traceback instead of `stream_write_failed` —
so an existing artifact is overwritten, never appended. **The write is then verified, not
trusted, per stream and before the next stream is written**: immediately after a stream's
`_final_write` returns — and before stderr's write is attempted — `main` re-reads that artifact
(`Path(path).read_bytes()`) and compares those bytes to the exact bytes it wrote,
`text.encode("utf-8", errors="replace")` — byte-for-byte, never a decoded `str` comparison, so a
changed or malformed byte is a mismatch rather than a `UnicodeDecodeError` escaping the mapped
region; a missing file, an `OSError` on the read, or a mismatch is `StreamWriteFailed` with
`verify: <stream>` in its detail, so a writer that silently
did nothing — or an artifact that vanished between close and verdict — can never be reported as
`RAN` (the base mutation-verification rule, applied to the helper's own output; mutation
`final-write-not-verified`). Because verification is per stream, a stdout verification failure
takes the first-stream rule below exactly as a stdout write failure does: `failed: stdout` /
`skipped: stderr`, and the stderr artifact keeps its previous bytes untouched —
`test_final_write_readback_catches_a_silent_no_op` asserts both detail lines and the untouched
stderr bytes; mutation `verify-deferred-past-second-write` (both writes run, then both
verifications) writes stderr before stdout's silent no-op is diagnosed and is killed by that
assertion. On `TIMEOUT` or `CLEANUP_FAILED` nothing is
written to either handle and pre-existing artifacts are untouched. A failure *in* that final write
can therefore only be an error on an open descriptor (disk full, I/O error) and maps to
`StreamWriteFailed` → `UNREADABLE reason=stream_write_failed`, exit 2; the `rc` is not reported,
because the artifact the caller was promised does not exist. **The writes are ordered and the
partial state is reported, not rolled back**: stdout is written first, then stderr; if the second
fails, the first stays as written (its old contents were truncated in place, so there is nothing
to restore) and the detail lines read `written: stdout` / `failed: stderr`; **if the first
(stdout) fails, the second is not attempted** — its artifact keeps its previous contents, since
nothing has touched it — and the detail lines read `failed: stdout` / `skipped: stderr`. All
three detail keys (`written:`, `failed:`, `skipped:`) have registry rows (AC-4.5), and each branch
has its test (`test_first_stream_write_failure_skips_the_second`,
`test_second_stream_write_failure_leaves_the_first_as_written`). **Both writes go
through one module function, `_final_write(handle, text)`** — the seam the AC-3.8 tests
fault-inject, since no real mechanism makes a held descriptor fail deterministically on macOS
(no `/dev/full`). **Every held handle has exactly one closure primitive, `_close_stream(handle)`**, called by
`_final_write`'s `finally` and by `main`'s backstop alike: `main` holds the two
reservations in a `try`/`finally` that spans the alias check, `run_block` and the final writes,
and the `finally` closes, through `_close_stream`, any handle `_final_write` has not already closed
(closing an already-closed handle is a no-op). **The backstop never raises from the `finally`**: each
close runs under `except OSError`, the first close error is recorded as `close_error` together with
the stream name, and — exactly as `run_block` selects after its own `try`/`finally` — `main` selects
the outcome after the block has completed. **Precedence, the same rule as cleanup: an operational
error outranks a verdict, and the first operational error wins.** If a `close_error` was recorded
and the pending outcome is a `BlockTimeout` (exit 0) — or there is no pending exception at all —
`StreamCloseFailed(stream, close_error)` is raised `from` the pending outcome and printed as
`DOCBLOCK: UNREADABLE reason=stream_close_failed` + `os_error: <text>`, exit 2; if the pending
outcome is already an exit-2 `DocBlockError` (`CleanupFailed`, `LaunchFailed`, `StreamPathsAlias`,
`StreamWriteFailed`), that error is raised unchanged and the close error is attached as its
`__context__`. (On the `RAN` path `_final_write` has closed both handles inside its own mapped
region, so the backstop is a no-op there.) Two tests, both through the `_close_stream` seam (the
sixth named injection, Test Strategy): `test_backstop_close_failure_on_timeout_is_mapped` patches
`_close_stream` to raise `OSError` under `sleep 300` / `timeout=1` with `--stdout` given and asserts
`UNREADABLE reason=stream_close_failed`, exit 2, the `os_error:` line, no traceback and the cwd gone
(mutation `backstop-close-unmapped`: the `except OSError` around the backstop removed, so the
timeout run prints a traceback); `test_backstop_close_failure_does_not_outrank_a_refusal` patches
the same seam under an aliased `--stdout`/`--stderr` pair and asserts the verdict is still
`stream_paths_alias`, exit 2, no traceback (mutation `backstop-close-outranks-error`: the
selection prefers the close error over a pending exit-2 error). **This closes the class, with the
residual stated:** every OS call `main` makes on its own behalf falls in exactly one of three
mapped regions — reservation (`os.open`, `fstat`, rollback close/unlink → `stream_path_unwritable`),
final write (`seek`/`truncate`/`write`/`flush`/`close`/read-back → `stream_write_failed`), and
backstop close (→ `stream_close_failed`, or chained under the pending exit-2 error); the calls
`run_block` makes are AC-4.6's (`mkdtemp`/`chmod`/`Popen`/`killpg`/`rmtree`), and nothing else in
`main` touches the OS. So `TIMEOUT`, `CLEANUP_FAILED`, `LAUNCH_FAILED`, an alias
refusal, and an exception inside the first `_final_write` all release both descriptors before
`main` returns — a repeated CLI use in one process cannot leak descriptors and turn a later
reservation into `stream_path_unwritable`. `test_stream_handles_are_closed_on_every_path` drives
`TIMEOUT` and the first-write failure and asserts both descriptors are closed (via the recording
`os.open` count and `fstat` raising `OSError` on the closed fds). **Aliasing is judged on the opened
descriptors** (AC-3.9): once both handles are held, `os.fstat` on each gives `(st_dev, st_ino)`,
and equality is `StreamPathsAlias` — a symlink, a `./x`/`x` spelling and a **hard link** all
collapse to one inode, and because the comparison is on the descriptors there is no
check-to-open window in which two distinct strings can come to name one file. The refusal unlinks a
file this call created (an `OSError` there maps to `stream_path_unwritable`, the region's verdict)
and raises `StreamPathsAlias`; **it does not close the handles itself** — closing is the backstop
`finally`'s job through `_close_stream`, which is what lets
`test_backstop_close_failure_does_not_outrank_a_refusal` inject a failing close and still see
`stream_paths_alias` (a close inside the reservation region would map that injected error to
`stream_path_unwritable` instead). Nothing has been written. (A string-level pre-check is
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
| `DOCBLOCK: SUBST_MISSING keys=<n>` + `missing_key: <k>` per key, map insertion order | 0 | one or more keys are absent from the block (`n` counts them, so the line never has to pick one) |
| `DOCBLOCK: SUBST_OVERLAP keys=<n>` + `overlap: <a> <b>` per pair | 0 | one key is a substring of another |
| `DOCBLOCK: UNREADABLE reason=stream_paths_alias` | 2 | `--stdout` and `--stderr` name one inode (`fstat` on the reserved handles) |
| `DOCBLOCK: UNREADABLE reason=preamble_unreadable` | 2 | `--preamble-file` cannot be read |
| `DOCBLOCK: BAD_INFO key=<k>` | 0 | unrecognised info-string token |
| `DOCBLOCK: TIMEOUT seconds=<n>` | 0 | the block outran its bound (either race in AC-5.5 included) |
| `DOCBLOCK: CLEANUP_FAILED path=<p>` + `os_error: <text>` when `cleanup_error` is set | 2 | the temp cwd could not be removed, or was read back present |
| `DOCBLOCK: LAUNCH_FAILED stage=<s>` + `os_error: <text>` (+ `pgid: <n>` when `stage=reap`) | 2 | the helper's own `mkdtemp`/`Popen`/`killpg` raised — never a traceback |
| `DOCBLOCK: UNREADABLE reason=<r>` (+ `written:`/`failed:`/`skipped:` detail lines and `verify: <stream>` when the read-back disagreed, for `r=stream_write_failed`; + `os_error: <text>` when `r=stream_close_failed`) | 2 | `doc_unreadable`, `stream_path_unwritable`, `stream_write_failed`, `stream_close_failed` (a backstop close of a held handle failed on a path where the final write never ran; an exit-2 error already pending wins instead) |

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
three operational classes the invariant's non-zero rule covers: `UNREADABLE` (input that could not
be read, a path that could not be written or reserved, a write that failed), `CLEANUP_FAILED` and
`LAUNCH_FAILED`. AC-4.2 pins that
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
| `BadSubstArg(raw, duplicate_key=None)` | `main`, building the map (split once on the first `=`; repeat refused) **and `substitute`, for an empty key** — the one rule lives in the API | `BAD_SUBST arg=<raw>` + `duplicate_key: <k>` when it is a repeat |
| `MissingSubstitution(keys)` | `substitute` | `SUBST_MISSING keys=<n>` + a `missing_key:` detail line per key |
| `OverlappingSubstitution(pairs)` | `substitute` | `SUBST_OVERLAP keys=<n>` + a detail line per pair |
| `StreamPathUnwritable` | `main`'s stream reservation — the two-arm `os.open` create-or-open loop itself (wraps `OSError`, and its bounded-retry exhaustion) | `UNREADABLE reason=stream_path_unwritable` |
| `StreamPathsAlias` | `main`, after reserving both handles — `os.fstat` `(st_dev, st_ino)` equal | `UNREADABLE reason=stream_paths_alias` |
| `PreambleUnreadable` | `main`'s pre-spawn read of `--preamble-file` (wraps `OSError` **and `UnicodeDecodeError`** — strict UTF-8, because text that will be executed is never silently repaired) | `UNREADABLE reason=preamble_unreadable` |
| `StreamWriteFailed(written, failed, skipped, verify=None)` | `main`, writing a stream to its held handle after the run, or verifying it by read-back | `UNREADABLE reason=stream_write_failed` + `written:`/`failed:`/`skipped:` detail lines from its fields, and `verify: <stream>` when the read-back disagreed |
| `StreamCloseFailed(stream, close_error)` | `main`, selected after its reservation `try`/`finally` when the backstop `_close_stream` raised and no exit-2 error was pending (a pending `BlockTimeout` becomes `__cause__`) | `UNREADABLE reason=stream_close_failed` + `os_error: <text>` |
| `BlockTimeout(seconds)` | `run_block` (both AC-5.5 races end here) | `TIMEOUT seconds=<n>` |
| `CleanupFailed(path, cleanup_error)` | `run_block`, after the `finally` read-back | `CLEANUP_FAILED path=<p>` + `os_error: <text>` when `cleanup_error` is set |
| `LaunchFailed(stage, err, pgid=None)` | `run_block` — `mkdtemp`, `Popen`, or a non-`ESRCH` `killpg` error, wrapped; `pgid` set on the `reap` stage | `LAUNCH_FAILED stage=<mkdtemp\|spawn\|reap>` + `os_error: <text>` (+ `pgid: <n>` on `reap`) |

`main` catches `DocBlockError` and dispatches on type, so adding an exception without a verdict
line is a `KeyError` in the mapping table rather than a silent traceback — and a test asserts every
`DocBlockError` subclass appears in the table (which is also half of AC-4.5's bidirectional pin).

Nothing is logged; the verdict line and the streams are the whole output contract. A non-zero block
`rc` is **not** an error — it is the measurement.

## Test Strategy

Unit tests only, at the module boundary; no mocking of `subprocess`, because the behaviours under
test (strict vs plain, `-u`, `pipefail`, process-group reaping) are precisely what a mock would
stub out. **Six named exceptions, all fault injections on a call whose *failure* is under test,
all via pytest's `monkeypatch` (restored on exit), all leaving `subprocess` real:** the AC-5.5
`killpg` seam is patched only for AC-4.6's `reap` stage (`PermissionError` after `poll()`), since
the AC-5.5 race itself is reproduced by a real fixture (a leader that exits at once behind an
`os.setsid()` escapee) and needs no mock; the AC-3.14 cleanup guards are exercised by patching `shutil.rmtree`
in the helper's namespace — once to raise `OSError`, once to do nothing — because a real
permission failure is skipped under root and the two guards need mutants only one of them kills;
and AC-4.6's `mkdtemp` stage patches `tempfile.mkdtemp` to raise and, separately, `os.chmod` to
raise (AC-3.13's post-creation failure, which must remove the directory it just created). The
`spawn` stage needs no mock: the test sets `PATH` to an empty directory and `bash` is genuinely
not found. The fifth is the module's own `_final_write(handle, text)` seam, patched to raise
`OSError` for AC-3.8's post-run write failure — the one call for which no real fault exists on
this platform — or patched to call the real `_final_write` with a recording proxy around the held
handle whose `flush`/`close` raise (the close-in-`finally` tests), which is the same seam and the
same injection, not a new one. The sixth is the module's own `_close_stream(handle)` seam — the one
closure primitive — patched to raise `OSError` for the backstop-close tests on paths where the final
write never ran (a timeout, an alias refusal), because a held descriptor cannot be made to fail at
close deterministically either. The drain race needs no mock, because a real
`os.setsid()` descendant holds the pipes open; the real permission fixture still runs wherever
`euid != 0`. Fixtures are markdown strings written to `tmp_path`, deliberately **hostile** rather than
tidy: headings at mixed levels, fences quoting fences, a path containing a space, a body with
CRLF, and a key containing regex metacharacters.

The CLI is exercised by `subprocess.run([sys.executable, SCRIPT, …])` so the exit codes under test
are the real process's, not a return value — the same shape `test_skill_candidates_census.py` uses —
**for every verdict a real input or a real fault can produce**. A verdict that needs one of the six
seam injections (`_final_write`, `_close_stream`, `tempfile.mkdtemp`, `os.chmod`, `shutil.rmtree`,
`os.killpg`) is driven in-process through `main(argv)` instead — its return value is the exit code
and `capsys` holds the lines — because a `monkeypatch` cannot cross an exec boundary; two
subprocess tests (`NOT_FOUND` → 0, an unreadable document → 2) pin that `sys.exit(main(...))` turns
that return value into the process exit, so the in-process code is the real code.

## Test Plan

`h-mad/tests/test_h_mad_doc_block_exec.py`:

| ACs | Tests |
|---|---|
| AC-1.1–1.7 | tagged-vs-untagged selection; a document containing an invalid UTF-8 byte → `UNREADABLE reason=doc_unreadable`, never a traceback; zero → `NOT_FOUND`; two → `AMBIGUOUS blocks=2 heading=<h>`; `--index` 2 and 3; same/shallower-level bound; a fence quoting the tag, a `~~~` fence quoting the tag, and a four-space-indented literal tag (an indented code block, never an opener); **a document with two identical headings → `AMBIGUOUS_HEADING count=2`, nothing executed** (fixture mirrors `invariants.example.md`'s duplicated `###`) |
| AC-1.8 | `docsections` delegates: no second bounder implementation remains (asserted on the source), its existing `test_docsections.py` still passes unchanged, and the shared bounder handles the unbalanced four-backtick case that the old toggle got wrong, **and its own contract is pinned directly** — `test_bounder_ignores_a_heading_inside_a_tilde_fence` and `test_bounder_ignores_an_indented_literal_fence` call `fence_aware_end` on hostile text and assert the section does not end at a heading quoted inside a `~~~` block or at a four-space-indented literal fence, since `docsections` consumes it as a section bounder, not through the extractor. **The import arrangement is pinned twice**: `test_docsections_imports_when_collected_alone` runs `pytest h-mad/tests/test_docsections.py -q` as a subprocess from the repo root, and `test_docsections_imports_from_an_unrelated_cwd` runs `python3 -c "import docsections"` with only the tests dir on `sys.path` and `cwd=tmp_path` — both would fail if `docsections.py` relied on another module's `sys.path` insert |
| AC-1.9 | `--index 0` and `--index -1` → `BAD_INDEX index=<n>`, exit 0, and the block a naive `blocks[-1]` would have chosen leaves no side effect; `select(blocks, 0)` raises `BadIndex` |
| AC-2.1–2.7 | path substitution; absent key refuses; two absent keys → two detail lines; metacharacter key; multi-occurrence count equals replacements; a value containing another key is neither re-substituted nor mis-counted, in both map orders; overlapping keys refuse with `SUBST_OVERLAP`, `keys=` counts distinct keys (`a`/`ab`/`abc` → 3) and the `overlap:` lines are one per pair in `(shorter, longer)` order |
| AC-3.1–3.10 | `pwd` outside the repo and gone after; `git status --porcelain` byte-identical across a writing block; `-u` strict-vs-plain; bare `exit 3` → rc 3 with the harness alive; `pipefail` strict-vs-plain; streams unmerged, and `str` — a block printing `é` round-trips it, a block running `printf '\xff'` yields U+FFFD (AC-3.6); `shell=fish` → `BAD_INFO`; optional stream paths; aliased `--stdout`/`--stderr` (a symlink, `./x` vs `x`, **and an `os.link` hard link**) refuse after reservation and before running, with both handles closed and a created file unlinked; unwritable stream path refuses **and the block leaves no side effect**; a pre-existing stream file is truncated, not appended; **a failed `--stderr` reservation leaves a pre-existing `--stdout` file byte-identical, and removes a `--stdout` file the call itself created**; **a timeout leaves pre-existing artifacts byte-identical** (nothing is written on that path); `_final_write` fault-injected → `UNREADABLE reason=stream_write_failed`; failing only the stderr write leaves the stdout artifact current with `written: stdout` / `failed: stderr` detail lines |
| AC-3.11–3.12 | a block reading `$FIXTURE_VAR` runs with `preamble="FIXTURE_VAR=…"` and its text is unchanged (the `Block.text` the API returns is byte-identical to the fence body); preamble **and** `subs` together — the executed text carries the substituted value, proving the preamble is composed with `text′`; the same with a preamble that has **no trailing newline**, proving the composition inserts the boundary; a preamble that fails (`false`) under strict mode is visible as the combined `rc` and stderr; `--preamble-file` on the CLI; an unreadable preamble path **and a preamble file containing an invalid UTF-8 byte** → `UNREADABLE reason=preamble_unreadable`, and the block leaves no side effect |
| AC-2.8 | `--subst K`, `--subst =V` → `BAD_SUBST arg=<raw>`; `--subst K=a --subst K=b` → `BAD_SUBST` with `duplicate_key: K`; `--subst K=a=b` substitutes the value `a=b`; each refusal executes nothing and reserves nothing |
| AC-3.13 | the block itself runs `stat -f %Lp .` (macOS) / `stat -c %a .` (GNU) and the test asserts `700` **from the block's stdout**, so the mode is observed from inside the running block, not inferred from the API — **with `os.umask(0o777)` set around the call and restored in `finally`**, which is what proves the chmod rather than the umask produced it; the source contains no `mktemp` invocation — argv token or shell command word, the same predicate as AC-5.3 |
| AC-3.14 | a block running `mkdir keep && chmod 000 keep` → `run_block` raises `CleanupFailed(path, cleanup_error)` with `cleanup_error` the `PermissionError` and the CLI prints `CLEANUP_FAILED path=<p>`, exit 2, no `rc=` (skipped when `euid == 0`); the test then `chmod 700`s and removes the tree in its own `finally`; `test_cleanup_failure_carries_the_os_error` and `test_cleanup_readback_catches_silent_retention` fault-inject `rmtree` (raising / no-op) and run everywhere; a normal run reads back absent (also AC-3.1) |
| AC-4.6 | `mkdtemp` fault-injected → `LAUNCH_FAILED stage=mkdtemp`, exit 2; `os.chmod` fault-injected → `LAUNCH_FAILED stage=mkdtemp` and the directory `mkdtemp` created is gone; `PATH=<empty dir>` → `LAUNCH_FAILED stage=spawn` and the cwd is gone; `os.killpg` raising `PermissionError` under a timed-out block → `LAUNCH_FAILED stage=reap` within the drain bound, cwd gone, `pgid=` in the detail — the fake records the pgid; because `dbe.os` is the process-global `os` module, the test binds `real_killpg = os.killpg` **before** `monkeypatch.setattr(dbe.os, "killpg", fake)` and its `finally` uses that bound original to send `SIGKILL` to the recorded pgid and to assert the group is gone (`real_killpg(pgid, 0)` raising `ProcessLookupError`), so neither the teardown nor the assertion goes through the fake; each carries an `os_error:` detail line and no `rc=` |
| AC-4.1–4.5 | `RAN` exits 0 with a non-zero block rc; **every** row of the verdict table exits with the code the table states — 0 for `RAN`, every refusal and `TIMEOUT`, 2 for `UNREADABLE`, `CLEANUP_FAILED` and `LAUNCH_FAILED` (the test enumerates the table rather than hardcoding a count, so adding or re-classing a verdict cannot leave the test stale); no cannot-judge carries `rc=`; only `AMBIGUOUS` carries `blocks=`; registry ↔ detail-line bidirectional pin; the parser rejects `--all`/`--dir` and abbreviated long options (`allow_abbrev=False`) |
| AC-5.1–5.4 | sleeping block → `TIMEOUT`; no surviving descendant after reap; **no `timeout`/`gtimeout` INVOCATION** — an argv token or shell command word, never a substring, since the source legitimately contains `timeout=`, `TimeoutExpired`, `BlockTimeout` and `--shell-timeout`; temp cwd removed after timeout |
| AC-5.6 | `--shell-timeout` `0`, `-1`, `nan`, `inf` and `abc` each → `BAD_TIMEOUT value=<v>`, exit 0, and a block with a side effect leaves none; `run_block(block, timeout=0)` raises `BadTimeout` with no child spawned (asserted by wrapping `subprocess.Popen` in a recording pass-through that must not have been called — an observation of the real call, not a fault injection, so the named-fault-injection list in Test Strategy stands) |
| AC-5.5 | `test_timeout_survives_a_group_that_already_emptied`, **no mock**: the block is `python3 ESC_PATH & exit 0` where `ESC_PATH` is replaced through the substitution map with the absolute path of an `esc.py` the test writes under its own `tmp_path` (the AC-5.2 idiom — the child's cwd is a fresh private directory, so nothing can be placed in it beforehand; the substituted absolute path is what makes the fixture executable) and `esc.py` calls `os.setsid()`, writes its pid to an absolute path outside the cwd, and sleeps holding stdout — `communicate` times out, `poll()` reaps the zombie leader, `killpg` raises `ProcessLookupError`, the drain times out, pipes close, `wait()` returns at once → `TIMEOUT`, cwd absent, no traceback; the test kills the escapee in `finally`; `test_timeout_drain_is_bounded_against_an_escapee`: the block starts an `os.setsid()` python child that writes its pid to an absolute path (outside the cwd, via the substitution map — the AC-5.2 idiom) and sleeps holding stdout, then the leader sleeps; `run_block(timeout=1)` raises `BlockTimeout` within `1 + DRAIN_SECONDS + 2` s wall time, the cwd is absent, and the test kills the escapee from the pid file in its `finally` |
| AC-6.1–6.6 | tag present on the Second-surface fence **and exactly one tagged opener across `h-mad/` and `handoff/` excluding `archive/`** (`test_exactly_one_tagged_fence_in_the_tree`, the plan's census sweep asserting cardinality 1); no `re.findall(r"```bash` left on the **executing** path (`_gate_bash_block` and `run_recipe`), and **exactly one** remaining in the file — the `:412` text scan, which `test_exec_block_scan_performs_no_execution` pins as non-executing and `test_only_the_exec_scan_hand_rolls_extraction` pins as the only occurrence, so the exemption cannot silently widen; the four migrated behaviours still pass; **the full suite passes AND its collected count is >= the pre-change baseline plus this feature's added tests** (both halves — a passing suite that silently lost tests satisfies neither): `test_suite_floor_holds` runs `pytest --collect-only -q` in a subprocess (collection executes nothing, so the suite cannot recurse; `DOCBLOCK_FLOOR_INNER=1` makes an inner instance skip regardless) and asserts collected >= `2747` + the collected count of `test_h_mad_doc_block_exec.py` alone + 7, the seven being the named node IDs added to existing files — six in `test_h_mad_collect_report_docs.py` (`test_gate_block_resolves_through_doc_block_exec`, `test_recipe_runs_through_run_block`, `test_gate_block_refuses_an_untagged_recipe`, `test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`, `test_only_the_exec_scan_hand_rolls_extraction`) and `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder` — each asserted present; the pass half is the Phase-5f gate command run alone outside the suite — `pytest … > log; RC=$?; tail -1 log; echo "SUITE: rc=$RC"`, gated on both the `passed` line and `rc=0`, never a bare `| tail -1` whose status is `tail`'s; and the two wire directions — the AC-6.5 spies are installed with `monkeypatch.setattr(dbe, …)` on the consumer's module alias, which is why the consumer must call `dbe.extract`/`dbe.run_block` and a test pins that it has no `from h_mad_doc_block_exec import` |


**Helper mutation spec — `h-mad/tests/mutation-specs/doc_block_exec.json`, entry by entry.** Every
guard below carries one mutation and the one named test that must go RED under it; the spec's
`command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_doc_block_exec.py", "-q"]` and its
`target_command` is `["python3.11", "-m", "pytest", "-q"]`, `root` is `../..` (commands run from
`h-mad/`, as `docsections.json` does), and **every `test` key is the full node ID**
`tests/test_h_mad_doc_block_exec.py::<name>` — the harness runs `target_command + [test]`, and a
bare `test_*` name is a nonexistent path to pytest, so the names in the table below are the
`<name>` half and the spec carries them qualified. The same rule binds the other two specs:
`tests/test_h_mad_collect_report_docs.py::<name>` in `doc_block_exec_wire.json` (whose `command`
is `["python3.11", "-m", "pytest", "tests/test_h_mad_collect_report_docs.py", "-q"]`) and
`tests/test_docsections.py::<name>` in `docsections.json` for the five rows killed there, while its sixth and seventh rows —
`docsections-syspath-setup-removed`, bound to `tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd`, and
`docsections-heading-lookup-reverted` (the local `re.search` heading regex restored in `titled_section`, `find_heading` untouched), bound to the delegation spy in `tests/test_docsections.py` —
(a `test` key is a full node ID and may name any collectable file; the harness runs `target_command + [test]`). Exact `find` anchors are set from the
landed source in the same task that lands it (the author-together ordering the plan states for
`docsections.json`), each exact-once; the mechanism column is what the anchor must express.
`ALL_CAUGHT` is required for all three.

**Wire mutation spec — `h-mad/tests/mutation-specs/doc_block_exec_wire.json`** (the plan's FR-6
table, restated here so the design enumerates every spec it names):

| mutation | mechanism | killed by (`test` key, under `tests/test_h_mad_collect_report_docs.py::`) |
|---|---|---|
| `wire-revert-extract` | `_gate_block` resolves its block with a local, tag-tolerant `re.findall(r"```bash[^\n]*\n(.*?)```")` instead of `dbe.extract`/`dbe.select` (tag-tolerant so the mutant still resolves the tagged block and the wire, not the regex, is what fails), helper untouched | `test_gate_block_resolves_through_doc_block_exec` (AC-6.5) |
| `wire-revert-select` | `_gate_block` keeps `dbe.extract` but picks `blocks[0]` (or raises locally) instead of calling `dbe.select`, callee intact | `test_gate_block_resolves_through_doc_block_exec` (AC-6.5 — the same pin also spies `dbe.select` and asserts one call with the extracted list and `index=None`) |
| `wire-revert-run` | `_run_recipe` runs `subprocess.run(["bash", "-c", preamble + script])` inline instead of `dbe.run_block` | `test_recipe_runs_through_run_block` (AC-6.5) |
| `wire-revert-substitute` | `_run_recipe` rewrites the checkout path with `str.replace` instead of `dbe.substitute`, callee intact | `test_recipe_runs_through_run_block` (AC-6.5 — the same pin also spies `dbe.substitute` and asserts one call with the gate block and the `{installed gate path: quoted checkout path}` map) |
| `wire-unconditional` | the call site grows `dbe.extract(...) or <legacy regex>`, so an untagged gate block is still resolved | `test_gate_block_refuses_an_untagged_recipe` (AC-6.6) |
| `exec-scan-executes` | the `:412` text scan is made to run its block through `dbe.run_block` | `test_exec_block_scan_performs_no_execution` (AC-6.2) |
| `consumer-from-import` | `import h_mad_doc_block_exec as dbe` becomes a bare `from … import` with unqualified calls | `test_consumer_calls_the_helper_module_qualified` (AC-6.5 precondition) |
| `hand-rolled-extraction-widened` | a second `re.findall(r"```bash…")` appears on the executing path | `test_only_the_exec_scan_hand_rolls_extraction` (AC-6.2) |

Under the two reverts the helper's own suite must stay green — the half that proves the failing
test pins the wire, not the callee — and the harness records both runs. The three guard rows
that were once listed as "(no mutation)" now carry mutants, because a guard without a mutant is
exactly what the base Mutation verification invariant forbids.

| mutation | guard it removes (mechanism) | killed by (`test` key) |
|---|---|---|
| `tag-check-removed` | `extract` returns every ```bash fence, tagged or not | `test_untagged_fence_is_not_a_candidate` (AC-1.1/1.2) |
| `fence-run-length-ignored` | any ``` line closes a fence, regardless of run length | `test_quoted_tag_inside_longer_fence_is_not_an_opener` (AC-1.6) |
| `section-bound-ignores-level` | the section ends at the next heading of *any* level | `test_section_owns_deeper_headings` (AC-1.5) |
| `heading-lookalike-accepted` | heading recognition is loosened to `line.lstrip().startswith("#")`, so `#hashtag`, a 7-`#` run or a 4-space-indented `## x` bounds or starts a section | `test_heading_lookalikes_are_not_headings` (AC-1.5 — the section under the real heading still owns the block past each lookalike, and a lookalike never matches the requested heading) |
| `adjacent-heading-skipped` | the boundary predicate becomes `>` `start` instead of `≥`, so a same-or-shallower heading on the very next line after the requested heading is not a boundary and its tagged block is extracted under the wrong address | `test_adjacent_heading_bounds_the_section` (AC-1.5 — the first section has no candidate and `fence_aware_end(text, start, level) == start`) |
| `heading-match-ignores-fence-state` | the heading search runs over every line instead of the scanner's `prose` lines, so a fenced `## <heading>` starts the section | `test_requested_heading_quoted_inside_a_fence_is_not_a_section_start` (AC-1.5/1.6 — the candidate must be the block under the real heading, and a tagged block under the fenced copy is never selected) |
| `duplicate-heading-takes-first` | `AmbiguousHeading` never raised; first match wins | `test_duplicate_headings_refuse` (AC-1.7) |
| `select-first-on-ambiguous` | `select` returns `blocks[0]` when >1 and no index | `test_two_tagged_blocks_without_index_are_ambiguous` (AC-1.3) |
| `index-below-one-accepted` | `index < 1` reaches `blocks[index - 1]` | `test_index_zero_refuses` (AC-1.9) |
| `missing-key-silently-skipped` | a zero-count key is not collected | `test_absent_key_refuses` (AC-2.2) |
| `overlap-resolved-by-order` | substring keys proceed in iteration order | `test_overlapping_keys_refuse` (AC-2.7) |
| `replacement-sequential` | replacement becomes a per-key `str.replace` loop in map order, so a value containing another key is re-scanned | `test_value_containing_another_key_is_not_rescanned` (AC-2.6 — `A→B`, `B→C` on `A B` must yield `B C` for **both** map orders; the sequential mutant yields `C C` in the `A`-first order, and both keys occur so a missing-key precheck cannot mask it) |
| `subst-split-on-every-equals` | `--subst` split on every `=` | `test_subst_value_may_contain_equals` (AC-2.8) |
| `subst-duplicate-key-last-wins` | a repeated `--subst` key overwrites instead of refusing | `test_duplicate_substitution_key_refuses` (AC-2.8) |
| `empty-map-not-short-circuited` | the empty-map guard is removed, so `{}` compiles a `""` alternation | `test_empty_substitution_map_is_a_no_op` (AC-2.2) |
| `duplicate-info-token-last-wins` | a repeated recognised token overwrites instead of refusing | `test_duplicate_info_tokens_refuse` (AC-3.7) |
| `index-nonint-unmapped` | `main` lets a non-integer `--index` raise `ValueError` instead of `BAD_INDEX` | `test_non_integer_index_is_bad_index` (AC-1.9/5.6 — values are the contract's, grammar is argparse's) |
| `timeout-nonnumeric-unmapped` | `main` lets a non-numeric `--shell-timeout` raise instead of `BAD_TIMEOUT` | `test_non_numeric_timeout_is_bad_timeout` (AC-5.6) |
| `doc-decode-error-unwrapped` | the document read drops `UnicodeDecodeError` from the `DocUnreadable` wrap (or reads with `errors="replace"`) | `test_invalid_utf8_document_is_unreadable` (AC-3.12) |
| `preamble-decode-error-unwrapped` | the preamble read drops `UnicodeDecodeError` from the `PreambleUnreadable` wrap | `test_invalid_utf8_preamble_is_unreadable` (AC-3.12) |
| `unknown-info-key-ignored` | an unrecognised token falls back to strict | `test_unknown_info_key_refuses` (AC-3.7) |
| `cwd-not-passed` | `cwd=cwd` is dropped from the `Popen` call, so the block runs in the caller's cwd | `test_block_runs_in_the_temp_cwd` (AC-3.1 — `pwd` is neither the repo root nor the document's directory, and is gone afterwards) |
| `scanner-duplicated-in-consumer` | `extract` regrows a private fence toggle instead of consuming `_fence_events` | `test_extract_has_no_fence_state_of_its_own` (AC-1.8 single-source) |
| `strict-flags-dropped` | `bash -c` always, never `-euo pipefail` | `test_unset_variable_fails_under_strict` (AC-3.3) |
| `preamble-separator-dropped` | composition is `preamble + text′`, no newline | `test_preamble_without_trailing_newline_still_precedes_the_block` (AC-3.11) |
| `preamble-composed-with-unsubstituted-text` | composition uses `block.text`, not `text′` | `test_preamble_and_substitution_compose` (AC-3.11) |
| `stream-reserved-with-truncation` | the reservation's `os.open` flags gain `O_TRUNC` (or the loop is replaced by `open(path, "w")`), so reserving empties a pre-existing artifact | `test_stdout_survives_a_failed_stderr_reservation` (AC-3.8) |
| `final-write-close-not-in-finally` | `_final_write`'s `close()` is moved out of its `finally` (a plain statement after the `try`), so a failing `flush` skips the close inside the mapped region and a failing close's error escapes | `test_final_write_failure_before_close_still_closes` (AC-3.8 — the canonical `test` key: the proxy's `flush` and `close` both raise; the mutant never calls the proxy's `close` from `_final_write`, and the outer `finally` closes the real handle, not the proxy; `test_final_write_close_failure_is_mapped` — `close` alone raises, the mutant prints a traceback — also goes red and stays as a regression test on the same mutant, but the spec's one `test` key names the former) |
| `verify-deferred-past-second-write` | `main` verifies both artifacts only after both `_final_write` calls, so stderr is truncated and written before a stdout verification failure is diagnosed | `test_final_write_readback_catches_a_silent_no_op` (AC-3.8 — the detail lines must read `failed: stdout` / `skipped: stderr` and the stderr artifact's bytes must be unchanged) |
| `final-write-not-verified` | the post-close read-back and comparison of each artifact is removed | `test_final_write_readback_catches_a_silent_no_op` (AC-3.8 — `_final_write` injected as a no-op that returns normally; the verdict must still be `stream_write_failed` with `verify: stdout`) |
| `closer-trailing-text-accepted` | a line whose marker run is followed by non-blank text closes the fence | `test_closer_with_trailing_text_does_not_close` (AC-1.6 — a ```` ```trailing ```` line inside a quoting fence must not close it) |
| `nonregular-stream-accepted` | the `S_ISREG` check on the reserved descriptor is removed, so a FIFO/device/socket is accepted as an artifact | `test_stream_path_fifo_without_reader_refuses_bounded` (AC-3.10) |
| `stream-open-blocking` | `O_NONBLOCK` is dropped from the existing-file arm, so a reader-less FIFO blocks the open forever | `test_stream_path_fifo_without_reader_refuses_bounded` (AC-3.10 — the test's own bounded wait is what makes this mutant RED rather than a hang; it runs the CLI in a subprocess with `timeout=5` and treats expiry as failure) |
| `stream-alias-check-removed` | the `fstat` `(st_dev, st_ino)` comparison is gone | `test_hard_linked_stream_paths_refuse` (AC-3.9) |
| `chmod-0700-removed` | `os.chmod(cwd, 0o700)` after `mkdtemp` is gone | `test_cwd_mode_is_0700_under_hostile_umask` (AC-3.13) |
| `cleanup-errors-ignored` | `ignore_errors=True` restored | `test_cleanup_failure_carries_the_os_error` (AC-3.14) |
| `cleanup-readback-removed` | the `lexists` read-back is gone | `test_cleanup_readback_catches_silent_retention` (AC-3.14) |
| `precedence-timeout-raised-in-handler` | `BlockTimeout` raised inside the handler instead of recorded as pending | `test_cleanup_failure_outranks_timeout_injected` (AC-3.14) |
| `exit-partition-flipped` | refusals exit 2 | `test_verdict_table_exit_codes` (AC-4.2) |
| `rc-leaked-into-refusal` | a refusal line carries `rc=` | `test_no_refusal_carries_rc` (AC-4.3) |
| `launch-oserror-unwrapped` | `mkdtemp`/`Popen` `OSError` propagates as a traceback | `test_mkdtemp_failure_is_a_verdict` (AC-4.6) |
| `killpg-replaced-by-kill` | `proc.kill()` instead of `os.killpg(proc.pid, …)` | `test_in_group_descendant_is_reaped` (AC-5.2) |
| `poll-before-killpg-removed` | `proc.poll()` before `killpg` is gone, so the natural race reports `LAUNCH_FAILED stage=reap` (EPERM on a zombie-only group) instead of `TIMEOUT` | `test_timeout_survives_a_group_that_already_emptied` (AC-5.5) |
| `killpg-esrch-uncaught` | `ProcessLookupError` from `killpg` propagates | `test_timeout_survives_a_group_that_already_emptied` (AC-5.5) |
| `drain-unbounded` | the post-kill `communicate` has no timeout | `test_timeout_drain_is_bounded_against_an_escapee` (AC-5.5) |
| `timeout-validation-removed` | `math.isfinite(t) and t > 0` is gone | `test_nonpositive_timeout_refuses_before_spawn` (AC-5.6) |
| `chmod-failure-unwrapped` | a failing `os.chmod` propagates and the created cwd is left behind | `test_chmod_failure_is_a_verdict_and_removes_the_cwd` (AC-3.13/4.6) |
| `chmod-rollback-unguarded` | the chmod failure removes the cwd outside the `finally` selection, so a failing removal is a traceback | `test_chmod_rollback_failure_is_cleanup_failed` (AC-3.13/3.14) |
| `body-indent-not-stripped` | `extract` returns fence body lines with the opener's indentation still on them | `test_indented_fence_body_is_deindented` (AC-1.6 — exact text at 1, 2 and 3 spaces, plus a body line indented less than the opener) |
| `indented-opener-accepted` | a run preceded by 4+ spaces is treated as an opener | `test_bounder_ignores_an_indented_literal_fence` (AC-1.8 — the bounder's own contract; `test_indented_literal_tag_is_not_a_candidate` pins the extractor side of the same rule under AC-1.6) |
| `prefix-state-truncated-mid-line` | the prefix is fed as `text[:start]` instead of whole lines through the line containing `start`, so a ```` ```trailing ```` line cut after its run reads as a closer | `test_bounder_offset_after_a_marker_run_on_a_non_closing_line` (AC-1.8) |
| `prefix-fence-state-skipped` | `fence_aware_end` starts its fence state at `start` instead of scanning the lines before it | `test_bounder_from_an_offset_inside_a_fence` (AC-1.8 — `section_from` anchored inside a fenced block must not end at a fenced `#`) |
| `backtick-in-info-accepted` | `_fence_events` treats a backtick-fence line whose info string contains a backtick as an opener | `test_backtick_in_info_string_is_not_an_opener` (AC-1.6 — the line must be inert: not a candidate, not `BAD_INFO`, and the following ``` line opens a fence) |
| `tilde-fence-not-tracked` | `~~~` fences are not tracked, so a heading inside one ends a section and a quoted ```bash opener inside one is a candidate | `test_bounder_ignores_a_heading_inside_a_tilde_fence` (AC-1.8 — the bounder's own contract; `test_tag_quoted_inside_a_tilde_fence_is_not_an_opener` pins the extractor side under AC-1.6) |
| `cleanup-error-ignored-when-tree-gone` | `CleanupFailed` only when `lexists`, a recorded error alone is dropped | `test_cleanup_error_after_successful_removal_is_still_a_failure` (AC-3.14) |
| `empty-key-accepted-by-api` | `substitute` accepts `""` and calls `str.replace("", v)` | `test_empty_key_is_refused_by_the_api` (AC-2.8) |
| `indented-closer-accepted` | the scanner closes a fence on a marker run preceded by four or more spaces | `test_indented_closer_does_not_close` (AC-1.6 — the four-space ```` ```` ```` line stays body text and the fence ends at the next 0–3-space closer) |
| `stream-open-oserror-unwrapped` | the reservation region's `except OSError` is removed, so an `ENOTDIR`/`EACCES` on `os.open` (or an `OSError` from `fstat` or the rollback) escapes as a traceback | `test_stream_path_under_a_regular_file_refuses` (AC-3.10 — a real `ENOTDIR`, no injection; the verdict must be `stream_path_unwritable`, exit 2, no traceback) |
| `backstop-close-unmapped` | the `except OSError` around `main`'s backstop `_close_stream` is removed, so a failing close on the timeout path escapes as a traceback | `test_backstop_close_failure_on_timeout_is_mapped` (AC-3.8 — `_close_stream` injected to raise under `TIMEOUT`; the verdict must be `stream_close_failed`, exit 2) |
| `backstop-close-outranks-error` | the post-`finally` selection raises `StreamCloseFailed` even when an exit-2 error is already pending | `test_backstop_close_failure_does_not_outrank_a_refusal` (AC-3.8 — an aliased pair plus an injected close failure must still report `stream_paths_alias`) |
| `registry-row-removed` | one remedy row deleted from the `SKILL.md` Helper-scripts entry (the mutation targets `SKILL.md`) | `test_every_emittable_line_has_a_registry_row` (AC-4.5) |
| `detail-line-undocumented` | the helper renames one emitted detail line (`missing_key:` → `absent_key:`) so an emittable line has no row | `test_registry_rows_cover_only_emittable_lines` (AC-4.5) |
| `timeout-invocation-planted` | the real argv construction `["bash", *flags, "-c", script]` becomes `["timeout", "5", "bash", *flags, "-c", script]` — valid Python, valid argv, and exactly the forbidden invocation | `test_no_timeout_invocation_in_source` (AC-5.3) — the source scan goes RED on the real helper |

Sixty-three rows, sixty-three mutations — sixty-one of the helper's source (the AC-5.3 row, once
described as a fixture-copy self-check, is a real argv mutation the source scan must catch) and
**two of `h-mad/SKILL.md`**, the registry document, which the harness mutates exactly as it
mutates source; those two AC-4.5 rows are the
manifest-integrity guard's own, one per direction of the bidirectional pin; a guard added later without a
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
- v1.25: Design audit v17 (codex must 1): 0-3 space indentation rule in the scanner, its hostile fixture and mutation (35 rows).
- v1.26: Design audit v18 (codex must 2 should 1 nit 1; agy clean): AC-4.5 gets two mutations (registry row removed, detail line undocumented); the delegation wire is module-qualified and mutation-pinned; the reap-failure branch is stated never to wait (37 rows).
- v1.27: Design audit v19 (codex must 1; agy see report): the AC-6 test row scopes the no-re.findall assertion to the executing path and pins the :412 scan as the single remaining occurrence.
- v1.28: Design audit v21 (codex must 1; agy should 3): poll() before killpg, the AC-5.5 race driven by a real fixture with no mock, the AC-4.6 reap test's teardown waits on the handle it holds; poll-before-killpg-removed mutation (38 rows); FR-4 summary names three operational classes; extract's doc is a path.
- v1.29: Design audit v22 (codex must 2; agy clean + 2 nits): the binding rule (root, command, target_command, full node IDs) stated for all three specs; the AC-5.3 row is a real argv mutation; the wire spec's three mutations enumerated.
- v1.30: Design audit v23 (codex should 1; agy must 2 should 2): the two bounder-contract tests bind the tilde and indentation mutations; fence_aware_end's docstring states the full rule; _final_write flushes and closes inside the mapped region; O_EXCL creation detection; CLEANUP_FAILED os_error detail; the stale differential-test phrase removed.
- v1.31: Design audit v24 (codex must 1 should 1; agy nit): the AC-4.6 reap test's handle seam (recording Popen pass-through) and exact teardown order; stdout-first write-failure branch; body de-indentation in extract with body-indent-not-stripped (39 rows); the three-classes sentence lists three.
- v1.32: Design audit v25 (codex must 1 should 1; agy clean): two-arm create-or-open loop (exclusive create, else open without O_CREAT, ENOENT restarts) so every created file is recorded; one closure path for both reservations across every exit, with its test.
- v1.33: Design audit v26 (codex must 1; agy must 4 should 1): cwd is None until mkdtemp returns; simultaneous single-pass substitution with the replacement-sequential mutation; os.open wording in the exception and mutation tables; closer-trailing-text rule and mutation; docsections migration assigned to Task 1; six consumer-file tests; 40 rows.
- v1.34: Design audit v27 (codex must 2; agy must 2 should 2): substitution fixture discriminates the sequential mutant; artifacts are read back and compared after close (final-write-not-verified, 41 rows); StreamWriteFailed and LaunchFailed carry the fields the dispatcher prints; pgid on the reap verdict; seven-test floor tuple.
- v1.35: Design audit v28 (codex must 1 should 2; agy must 2 should 1 + nit): empty-map short-circuit with its mutation; duplicate info tokens refused; SUBST_MISSING keys=<n>; mutation accounting (41 source + 2 SKILL.md = 43 rows); Implementation Order names select, RunResult and every exact file path.
- v1.36: Design audit v30 (codex must 1 should 1; agy must 1 should 1 + nit): read-back compares bytes, never decoded text; fence_aware_end's prefix-state contract with test and mutation; test_docsections.py tracked in Components and Task 1; Task 3 names its exceptions, Task 4 the preamble read; four main/I-O mutation rows (48 rows).
- v1.37: Design audit v31 (codex must 2): missing keys listed in map insertion order with a multi-key test; RunResult.rc is the spawned invocation's exit code.
- v1.38: Design audit v32 (both surfaces clean; agy nit): the AC-6.1 cardinality test is named.
- v1.39: Design audit v33 (codex clean; agy must 1 + nits): the API prose lists BadSubstArg and BadTimeout.
- v1.40: Design audit v34 (codex must 1; agy must 1 + nits): exec-scan-executes, consumer-from-import and hand-rolled-extraction-widened added to the wire spec (six); stray line break in the setattr call joined.
- v1.41: Design audit v35 (codex must 1; agy clean): one private fence scanner, _fence_events, consumed by both extract and fence_aware_end — the fence-grammar mutations anchor in it and a construct-complete parity test runs every hostile fixture through both consumers.
- v1.42: Design audit v36 (codex must 1; agy clean): prefix fence state from whole lines through the line containing start, boundaries only after start; hostile mid-line fixture and the prefix-state-truncated-mid-line mutation (49 rows).
- v1.43: Plan re-audit v32 back-propagation: Task 5 and the wire-revert-extract row name _gate_block.
- v1.44: Design audit v38 (codex must 1; agy clean): backtick-in-info prohibition in _fence_events, measured on both renderers, with its mutation (50 rows).
- v1.45: Design audit v39 (codex must 1; agy must 1 should 1): the existing-file reservation arm opens O_NONBLOCK and every reserved descriptor must be a regular file (a reader-less FIFO refuses bounded), with two mutations (52 rows); the two post-Task-5 tests are authored in Task 5; the wire-revert-extract row names the tag-tolerant regex.
- v1.46: Design audit v40 (codex must 2; agy clean + nits): Popen passes cwd=cwd, with the cwd-not-passed mutation; the parity guard becomes a scanner event-trace test plus a no-fence-state source assertion on extract (54 rows); _gate_block returns dbe.Block.
- v1.47: Design audit v41 (codex must 2; agy clean): _final_write closes in a finally with the close error mapped in the same region, plus its mutation (55 rows); the reader-less-FIFO ENXIO behaviour is cited from a probe on python 3.11.8/darwin.
- v1.48: Design audit v42 (codex must 1; agy clean): final-write-close-not-in-finally is killed by an injected close failure — test_final_write_close_failure_is_mapped (close alone raises → mapped, no traceback) and test_final_write_failure_before_close_still_closes now injects flush AND close on a recording proxy handed through the _final_write seam and asserts the proxy's close was called, which the outer finally (holding the real handle) cannot produce; fifth injection reused, 55 rows unchanged.
- v1.49: Design audit v43 (codex must 1; agy must 1 should 1): _close_stream(handle) is the one closure primitive and the sixth named injection; main's backstop close records instead of raising and selects afterwards — StreamCloseFailed → UNREADABLE reason=stream_close_failed (exit 2, os_error:) outranks TIMEOUT, a pending exit-2 error outranks it (__context__); the three mapped OS-call regions of main stated as the class with its residual; indented-closer-accepted and stream-open-oserror-unwrapped mutations with their tests; 59 rows (57 + 2).
- v1.50: Design audit v44 (codex must 2 should 1; agy clean, low-evidence): the post-spawn taxonomy is five outcomes with stream_close_failed between LAUNCH_FAILED stage=reap and TIMEOUT; the AC-4.6 reap test binds real_killpg before patching the process-global os; artifact verification is per stream before the next write, with verify-deferred-past-second-write and the extended read-back test; 60 rows (58 + 2).
- v1.51: Impl-plan audit v2 back-propagation (codex must 4): the heading match runs over the scanner's prose lines only, with test_requested_heading_quoted_inside_a_fence_is_not_a_section_start and mutation heading-match-ignores-fence-state (61 rows: 59 + 2); Test Strategy states the transport split — seam-injected verdicts through main(argv) in-process, every real-input verdict through the subprocess, two subprocess tests pinning sys.exit(main()).
- v1.52: Plan re-audit v40 back-propagation (codex must 1): docsections.json carries a sixth row, docsections-syspath-setup-removed, killed by test_docsections_imports_from_an_unrelated_cwd in the new module.
- v1.53: Design audit v47 (codex should 1; agy must 1) + impl-plan audit v3 back-propagation (codex must 1): the docsections.json binding sentence names the sixth row's cross-file key; the wire spec has eight mutations — wire-revert-select and wire-revert-substitute killed by the existing pins, which now also spy dbe.select and dbe.substitute.
- v1.54: Design audit v48 (codex should 1; agy clean): run_recipe is hoisted to the module-level _run_recipe in the migration, named consistently in Implementation Order and the wire table.
- v1.55: Design audit v50 (codex must 1; agy clean) + impl-plan audit v5 back-propagation: the AC-5.5 escapee fixture is an esc.py under the test's tmp_path reached through the substitution map (ESC_PATH), never a file in the child's fresh cwd; the docsections-delegation-reverted mutant is expected to trip the docsections source guard, which is stated instead of 'helper suite still green'.
- v1.56: Impl-plan audit v6 back-propagation (codex should): the ATX heading grammar is stated (CommonMark 4.2 — 0–3 spaces, 1–6 hashes, space/tab/EOL, optional closing run), with test_heading_lookalikes_are_not_headings and mutation heading-lookalike-accepted (62 rows: 60 + 2).
- v1.57: Design audit v52 (codex clean; agy should 2): the AC-4.1–4.5 test row names LAUNCH_FAILED in the exit-2 class; the CleanupFailed row carries its os_error: detail line.
- v1.58: Design audit v53 (codex must 1 should 1; agy must 1) + impl-plan audit v7 back-propagation (codex must 1 should 1): scanner event model is open/close/body/heading/prose with level and candidate; the grammar is verified against markdown-it-py 2.2.0 (14/14, plan §Measurements); find_heading is public and docsections delegates the section start as well as its end (seven public names; docsections.json seventh row docsections-heading-lookup-reverted); the alias refusal leaves closing to the backstop so the injected-close test can hold.
- v1.59: Design audit v54 (codex must 2; agy must 1 should 1): the UNREADABLE verdict row carries stream_write_failed's detail lines; Implementation Order Task 1 lists _fence_events and find_heading.
- v1.60: Plan re-audit v46 (codex must 1 should 1) + impl-plan audit v8 back-propagation (codex must 2 should 1): the boundary predicate is start-offset >= start so an adjacent heading bounds the section (test_adjacent_heading_bounds_the_section, adjacent-heading-skipped; 63 rows: 61 + 2); the titled_section migration cited as a measured differential (new_only=0, old_only=76 fenced comments); one canonical test key for final-write-close-not-in-finally; _run_recipe passes timeout=60.0.
