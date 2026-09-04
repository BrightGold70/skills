# Spec: doc-block-exec

## Executive Summary

`h_mad_doc_block_exec.py` addresses an **explicitly tagged** fenced bash block in a markdown
document, substitutes caller-supplied placeholders into it, runs it in a disposable cwd under a
per-block-declared shell mode, and reports rc + stdout + stderr — refusing, rather than silently
proceeding, on every condition under which it would measure nothing.

## Goal

Make the paste-along bash recipes in these skills executable as tests, so that a recipe defect is
caught by the suite instead of by an operator pasting it, without ever executing a block that has
not opted in.

## Functional Requirements

### FR-1: Address a block by document, heading, and explicit tag

- **Description**: A block is executable only if its opening fence carries the info-string tag
  `hmad:exec`. The address is (document, heading, tag), with an optional 1-based ordinal for the
  case where a heading holds more than one tagged block. An untagged fence is never returned and
  never executed, whatever its content or position.
- **Acceptance Criteria**:
  - AC-1.1: Given a document whose section `## H` contains one ` ```bash hmad:exec ` fence and one
    plain ` ```bash ` fence, `extract(doc, heading="## H")` returns a list of exactly one block and
    its text is the tagged fence's body; `select()` on that list returns that block. Scanning and
    selection are separate functions — `extract` never raises on candidate count, `select` owns
    that policy — because a single function typed to return one block while also handling 0 and
    many is the contradiction the design audit surfaced.
  - AC-1.2: Given a section containing only untagged ` ```bash ` fences, extraction yields zero
    blocks and the CLI prints `DOCBLOCK: NOT_FOUND heading="<h>"` and exits 0 — a refusal is a verdict (FR-4).
  - AC-1.3: Given a section with two tagged blocks and no ordinal supplied, the CLI prints
    `DOCBLOCK: AMBIGUOUS blocks=2 heading="<h>"` and exits 0, executing nothing.
  - AC-1.4: With the same document, `--index 2` selects the second tagged block; `--index 3`
    prints `DOCBLOCK: NOT_FOUND heading="<h>"` and exits 0.
  - AC-1.5: The section boundary is the next **ATX** heading (`#`-prefixed) at the same or
    shallower level; a tagged fence under a *later* heading is not returned for the earlier
    heading. **Setext headings (underlined with `===`/`---`) are explicitly out of scope and not
    recognised** — every document in these skills is ATX, `h-mad/tests/docsections.py` makes the
    same assumption, and after AC-1.8 both call the one authoritative bounder, so the assumption
    has exactly one home rather than two that could drift. Stated here so the
    limitation is accepted rather than discovered.
  - AC-1.6: A tag appearing inside a fence body (a fence that quotes ` ```bash hmad:exec ` as
    text) is not treated as an opening fence, **including when the enclosing fence uses a longer
    backtick run** — a four-backtick fence legitimately contains ``` lines as body text — **and
    including when the enclosing fence is a tilde fence** (`~~~`), which CommonMark defines as a
    fence too and which can quote a backtick fence verbatim. Tilde fences are tracked for bounding
    only; a candidate is always a backtick fence with `bash` as its first info-string word.
    **A backtick fence whose info string contains a backtick is not a fence** (CommonMark §4.5),
    so ```` ```bash hmad:exec `x` ```` is inert prose — never a candidate and never `BAD_INFO` —
    measured on markdown-it-py and on GitHub's renderer, both of which emit it as a paragraph
    (tilde fences have no such rule). **Indentation follows CommonMark too**: a fence opener may be indented by at most three
    spaces; a line indented four or more spaces is an indented code block, never a fence, so a
    literal `    ```bash hmad:exec` (four spaces) is body text of an indented code block and is
    never a candidate — a hostile fixture pins it. A closer obeys the same 0–3 rule, and the
    opener's indentation is stripped from body lines only up to that count, as CommonMark
    specifies.
    Measured through GitHub's own renderer (`POST /markdown`, below): a `~~~` block quoting
    ` ```bash hmad:exec ` renders as a plain code block, not as an opened bash fence.
  - AC-1.7: **Duplicate headings refuse.** If the document contains more than one heading whose
    text and level both match — text compared after the CommonMark closing hash run and trailing
    whitespace are stripped, so `## Text ##` and `## Text` are the same heading and two such lines
    are duplicates — nothing is executed: `DOCBLOCK: AMBIGUOUS_HEADING count=<n>
    heading="<h>"`, exit 0. Two identical headings share one address, and silently taking the first would run a
    tagged block from the wrong section — the same silent-wrong-answer shape the tag exists to
    prevent, one level up, and the tag cannot repair an ambiguous *section* selector. Not
    hypothetical: `h-mad/invariants.example.md` already carries `### Unified-facade routing` and
    `### Data-source priority` twice each (measured this session, 16 headings, 2 duplicated).
  - AC-1.8: **One authoritative bounder, which `docsections` delegates to.** A differential test
    was specified first and is not achievable: `docsections._fence_aware_end` toggles on any
    ```-prefixed line, so on an unbalanced inner quote inside a four-backtick fence it stops early
    (measured: bound `'\n````bash\n```bash hmad:exec\n'`, cut at an in-fence `## Not a heading`),
    while AC-1.6 requires the new scanner *not* to. Byte-identical bounds and AC-1.6 cannot both
    hold. So the Single-source contract is satisfied by its FIRST branch instead: this module owns
    the bounder, and `h-mad/tests/docsections.py` imports it — `tests/` depending on `scripts/` is
    the correct direction. The test asserts `docsections` delegates (no second implementation
    remains) and that the shared bounder handles the four-backtick case both ways round.
    **The import is self-contained**: `docsections.py` reaches the module the way every test in
    `h-mad/tests/` already reaches `h-mad/scripts/` — a `sys.path.insert(0, …/scripts)` of its
    own, immediately before the import — so the delegation holds when `test_docsections.py` is
    collected alone and when `docsections` is imported from an unrelated cwd, never through
    another module's `sys.path` side effect. A test collects it alone to prove that.
  - AC-1.9: **An ordinal below 1 refuses.** `--index 0` and `--index -1` print
    `DOCBLOCK: BAD_INDEX index="<n>"` and exit 0, executing nothing; `select(blocks, 0)` raises
    `BadIndex(0)`. Left to a conventional `blocks[index - 1]`, `0` silently addresses the *last*
    tagged block and a negative value some other one — a wrong block run without a word, the
    shape the explicit address exists to prevent. Past-the-end stays `NOT_FOUND` (AC-1.4): that
    ordinal names a block that does not exist; this one is not an ordinal at all.

### FR-2: Substitute an explicit map, and refuse a substitution that would not apply

- **Description**: The caller supplies substitutions as an explicit key→value map. Every key must
  be present in the block text. A key that is absent is a refusal, never a no-op.
- **Acceptance Criteria**:
  - AC-2.1: Given a block containing `~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py` and a map
    substituting that string for a local path, the executed block contains the local path and not
    the original.
  - AC-2.2: Given a map whose key does not occur in the block, nothing is executed, the CLI prints
    `DOCBLOCK: SUBST_MISSING keys=<n>` — `<n>` the number of absent keys, the same shape as
    `SUBST_OVERLAP keys=<n>`, so the verdict line never has to pick one key to name — and exits 0.
    An **empty** map is a no-op, not a refusal: `substitute(block, {})` returns an equivalent
    `Block` and `{}` without compiling any alternation (a zero-key alternation would match the
    empty string), and a CLI invocation with no `--subst` takes that path.
  - AC-2.3: The refusal names every offending key, one `missing_key: "<k>"` detail line each, in
    the **map's insertion order** (an absent key has no position in the block, so the map is the
    only order that exists; on the CLI that is `--subst` argument order); with two absent keys,
    `keys=2` and both are named in that order, pinned by a multi-key test.
  - AC-2.4: Substitution is literal, not regex — a key containing regex metacharacters
    (`.`, `*`, `[`) is matched and replaced literally.
  - AC-2.5: A key occurring more than once in the block is replaced at **every** occurrence, and
    the reported occurrence count equals the number replaced.
  - AC-2.6: **Substitution is simultaneous and counts are taken on the original text.** Every
    key is counted against the block as written, and all replacements happen in one pass that
    never re-scans replaced text, so a value that contains another key's text is neither
    re-substituted nor counted: with `A→B` and `B→C` on a block containing `A B`, the result is
    `B C` **in both map orders** (a sequential implementation yields `C C` when `A` is replaced
    first — the discriminating case — and both keys are present, so no missing-key precheck can
    mask the difference). (An earlier draft prescribed
    sequential count-then-replace, which made the outcome depend on iteration order — the very
    class AC-2.7 refuses overlapping keys to avoid.)
  - AC-2.7: Overlapping keys refuse rather than resolve by order — if any key is a substring of
    another, nothing is executed and the CLI prints `DOCBLOCK: SUBST_OVERLAP keys=<n>` with a
    detail line naming each overlapping pair, and exits 0. `<n>` is the number of **distinct keys
    implicated** (three keys where one contains both others → `keys=3`, two pairs); the detail
    lines are `overlap: "<shorter>" "<longer>"`, one per unordered pair, sorted lexicographically by
    `(shorter, longer)`, so the diagnostic is deterministic and the registry can pin it.
    Order-dependent substitution is the silent-wrong-answer shape this feature exists to avoid.
  - AC-2.8: **`--subst` has a parser contract.** Each value is split **once, on the first `=`**:
    the key is everything before it, the value everything after (so a value may itself contain
    `=`, and `K=` is a legal empty value). A value with no `=`, or an empty key (`=V`), refuses with
    `DOCBLOCK: BAD_SUBST arg="<raw>"`; the same key given twice refuses with
    `DOCBLOCK: BAD_SUBST arg="<raw>"` plus a `duplicate_key: "<k>"` detail line, never a last-wins
    overwrite. Both exit 0 (a refusal of readable input), execute nothing, and are judged before
    any artifact is reserved. Tests: `--subst K`, `--subst =V`, `--subst K=a --subst K=b`, and
    `--subst K=a=b` (value `a=b`). **The empty-key rule lives in the API, not only the CLI:**
    `substitute(block, subs)` raises `BadSubstArg("")` for an empty key — `str.replace("", v)`
    would insert `v` at every character boundary — so an in-process caller cannot bypass the
    refusal the CLI enforces. **`main` does not reach it through `substitute`**: it refuses the
    empty key itself while building the map, so the verdict carries the raw argument
    (`arg="=V"`, quoted like every dynamic field), and `substitute`'s refusal is the separate API guard — the same predicate in two
    places, each with its own test and mutation (design audit v69/v70).

### FR-3: Execute in a disposable cwd under a declared shell mode

- **Description**: Every run happens in a fresh disposable directory created by Python's
  **`tempfile.mkdtemp()`** — the stdlib call, *not* the `mktemp -d` shell utility. The candidate
  row that motivated this feature said "run under `mktemp -d`" and that wording was carried here
  verbatim; taken literally it is a shell invocation, i.e. a new external dependency, which the
  stdlib-only and no-new-dependency invariants both forbid. The directory is removed afterwards.
  The shell mode comes from the fence's info string: absent means strict (`bash -euo pipefail`); `shell=plain`
  means a bare `bash -c`, which is how an operator's paste actually runs.
- **Acceptance Criteria**:
  - AC-3.1: A block executing `pwd` reports a cwd that is neither the repository root nor the
    document's directory, and that path does not exist after the call returns.
  - AC-3.2: A block that creates a file leaves no file in the repository working tree; `git status
    --porcelain` is byte-identical before and after.
  - AC-3.3: A block tagged ` ```bash hmad:exec ` that references an unset variable returns a
    non-zero rc (strict `-u`); the same block tagged `shell=plain` returns rc 0.
  - AC-3.4: A block tagged `shell=plain` whose body contains a bare `exit 3` returns rc 3, and the
    calling Python process is still alive and continues (the operator's shell-kill defect is
    observable, not fatal to the harness).
  - AC-3.5: A block whose pipeline fails mid-pipe returns non-zero under the strict default
    (`pipefail`) and rc 0 under `shell=plain`.
  - AC-3.6: The returned value carries `rc`, `stdout`, and `stderr` as separate fields; stdout and
    stderr are not merged. Both are `str`, decoded as UTF-8 with `errors="replace"`: a block that
    prints non-ASCII text round-trips it, and a block that emits an undecodable byte
    (`printf '\xff'`) yields U+FFFD in that position rather than a `UnicodeDecodeError` escaping
    as a traceback. Stream artifact files are written UTF-8 the same way.
  - AC-3.7: An unrecognised info-string key (e.g. `shell=fish`, `mode=x`) on a fence that
    **carries `hmad:exec`** is a refusal — `DOCBLOCK: BAD_INFO key="<k>"` — and exits 0, rather than
    being ignored as a default; so is a **duplicated** recognised token — `hmad:exec hmad:exec`
    or `shell=strict shell=plain` — because a parser that silently kept the first or the last
    would run the block under a mode nobody unambiguously chose (`BAD_INFO key="<k>"` naming the
    repeated token; tested both ways). A fence **without** the tag is never a candidate and its info
    string is never validated: an untagged ` ```bash --frozen `, or any other prose-y info string
    elsewhere in the tree, must not make this tool refuse. Validation follows opt-in.
  - AC-3.8: `--stdout <path>` and `--stderr <path>` are **optional**; given, each receives that
    stream verbatim, and the two files differ for a block writing different text to each. Omitted,
    no stream file is written and the run still succeeds. An existing file at either path is
    **overwritten** — truncated at the final write, as a shell `>` would — never appended; and a
    write that fails *after* the run (the artifact was reserved, the write itself failed) refuses
    with `DOCBLOCK: UNREADABLE reason=stream_write_failed`, exit 2, rather than reporting `RAN`
    over an artifact that does not exist. Streams are written stdout first, then stderr. A failure
    on the **first** skips the second (`failed: "stdout"` / `skipped: "stderr"` — the stderr artifact
    keeps its previous contents untouched); a failure on the **second** leaves the first as
    written (`written: "stdout"` / `failed: "stderr"`) — no rollback, because the old artifact was
    truncated in place and there is nothing to roll back to. The detail lines name the state of
    each artifact so the operator knows which is current, and each of `written:`, `failed:` and
    `skipped:` has a registry row (tested by failing the first write only, and the second only). A close of a held
    handle that fails on a path where the final write never ran (a timeout, a refusal, a launch
    failure) is `DOCBLOCK: UNREADABLE reason=stream_close_failed` with an `os_error:` detail line,
    exit 2 — an operational error outranks the `TIMEOUT` verdict, and an exit-2 error already
    pending outranks it (first error wins, the close error chained as `__context__`); never a
    traceback. The final write goes through
    one named module function, `_final_write(handle, text)` — which seeks, truncates, writes,
    **flushes and closes** the handle inside the region mapped to `stream_write_failed` — and after
    the close each requested artifact is **read back and compared byte-for-byte to the stream
    text**, a missing or mismatching artifact refusing with `stream_write_failed` and a
    `verify: "<stream>"` detail line, so a write that silently did nothing cannot be reported as
    `RAN` — because a
    buffered `TextIOWrapper` may not hit the OS until `flush()`/`close()` and an error surfacing
    at a close outside that region would be a traceback — and which is the seam the test
    fault-injects; no other mechanism can make a held descriptor fail deterministically on this
    platform (macOS has no `/dev/full`). **No open ever truncates.** After every other refusal
    has passed — including substitution — both paths are opened for *append* and the handles
    held; the truncation is the final write itself (`seek(0); truncate(); write`) on those held
    handles, after a successful run. So a failure to reserve the second path finds the first
    untouched (a file this call *created* while reserving — known atomically, because creation
    happens only through an exclusive-create open and an existing file is opened without
    `O_CREAT` — is unlinked again, a pre-existing one keeps every byte; every held handle is
    closed on every exit path of the run, so no descriptor outlives a refusal or a failure), and a run that ends in `TIMEOUT` or `CLEANUP_FAILED` leaves pre-existing
    artifacts exactly as they were, because nothing is written on those paths. Tests: a
    pre-existing `--stdout` file is byte-identical after `--stderr` fails to reserve, and after a
    timeout.
  - AC-3.9: `--stdout` and `--stderr` naming the **same path** refuses with
    `DOCBLOCK: UNREADABLE reason=stream_paths_alias`, exits 2, and **does not run the block** —
    one file cannot hold two streams verbatim, so the alternative is silently merging or
    truncating an artifact the caller was promised. **Compared on the opened descriptors** —
    `(st_dev, st_ino)` from `os.fstat` of the two reserved handles, after reservation and before
    anything is written — so a symlink, a `./x` versus `x` spelling **and a hard link** are all
    caught, and there is no check-to-open window in which two distinct strings can come to name
    one inode. A refusal here closes both handles (unlinking one this call created) and touches
    no bytes. Tests: symlink, spelling, and `os.link` alias.
  - AC-3.10: A `--stdout`/`--stderr` path that cannot be written refuses with
    `DOCBLOCK: UNREADABLE reason=stream_path_unwritable` and exits 2, **and the block does not
    run** — observable because a block with a side effect leaves none. When the second
    reservation fails after the first created a file, the first is closed and unlinked and the
    helper reads back that the path is gone; if the rollback left it behind, the same verdict
    carries a `leftover: "<path>"` detail line (tested by fault-injecting `os.unlink`), so a
    refusal never silently leaves a new artifact. Concurrent replacement of the caller's own artifact
    path between the two reservations is outside the threat model (the paths are the caller's
    scratch paths); the rollback compares the path's `lstat` identity with the created descriptor's
    `fstat` identity and never unlinks a file it did not create.
  - AC-3.11: **Fixture preamble.** `run_block` accepts an optional `preamble` — shell text run in
    the *same* invocation immediately before the block. It is fixture setup, never doc content:
    the block's own text is unchanged and is what the doc says. **Composition is
    `preamble.rstrip("\n") + "\n" + text′`, where `text′` is the block's text *after* FR-2
    substitution** — the preamble is prepended to what will actually run, never to the unsubstituted
    fence body, so a substituted path is still substituted when a preamble is present (a test
    drives both together). A newline boundary is always inserted, so a
    preamble file without a trailing newline cannot fuse with the recipe's first token, and a
    preamble that ends in one does not gain a blank line; a test drives the no-final-newline case.
    Without it the executing migration
    is impossible — the Second-surface gate block reads `COLLECT_OUT`, which today's `run_recipe`
    supplies by running the real collector first. Measured on the real block, one variable changed:

    ```
    WITHOUT preamble: rc=0
        [H-MAD] <feature> <phase> halted reason=report_not_collected
        bash: line 1: COLLECT_OUT: unbound variable
    WITH preamble:    rc=0
        [H-MAD] <feature> <phase> halted reason=report_not_collected
    ```

    Note what the pair actually shows, which is narrower than "it aborts": both runs exit 0 and
    both take the halt branch, so the unbound variable is a diagnostic rather than a hard abort.
    The consequence that matters is that without a supplied `COLLECT_OUT` the block can never
    reach the delivered-report `GATE: PASS` branch — which is precisely what AC-6.3 requires.
  - AC-3.12: A run with a preamble reports `rc`/`stdout`/`stderr` for the combined invocation —
    **`RunResult.rc` is always the exit code of the one `bash -c` the helper spawned**, which is
    the block's own code when there is no preamble and the combined code when there is; a strict
    preamble that fails before the block runs is that `rc`, there being no separate block code to
    report — and
    a preamble that itself fails is visible as that `rc` rather than being swallowed. On the CLI the
    preamble comes from `--preamble-file <path>`, a file rather than an inline string, so quoting
    cannot corrupt it; an unreadable preamble file — unreadable as a file, **or not valid UTF-8**,
    since it is read strictly and text that will be executed is never silently repaired — refuses
    with `DOCBLOCK: UNREADABLE reason=preamble_unreadable` and does not run the block. The document
    itself is read the same way, so a malformed document is `UNREADABLE reason=doc_unreadable`, not
    a traceback; a test feeds each an invalid byte.
  - AC-3.13: The temp directory is created by `tempfile.mkdtemp()` **followed by
    `os.chmod(cwd, 0o700)`**, and its mode is `0o700` (`stat.S_IMODE(os.stat(d).st_mode) == 0o700`),
    observed from inside the running block **under a hostile umask**: `mkdtemp` alone yields
    `0o700 & ~umask` — measured, `umask 0777` gives mode `0o0` — so the chmod is what makes the AC
    true rather than environment-dependent. The test sets `os.umask(0o777)` around the call and
    restores it in `finally`. A chmod that fails is `LAUNCH_FAILED stage=mkdtemp` (AC-4.6) after
    the directory is removed — through the same recorded-error-plus-read-back cleanup selection as
    every other path, so a rollback whose removal itself fails is `CLEANUP_FAILED` (with the
    `LaunchFailed` as `__cause__`), never a traceback (tested by injecting both) — tested by fault-injecting `os.chmod` to raise and asserting the
    verdict, the `os_error:` detail, and that the just-created directory is gone; the guard has
    its own mutation. The
    source contains no `mktemp` invocation — the same argv-token/shell-command-word test AC-5.3
    uses, so satisfying the prose by shelling out is caught rather than assumed away.
  - AC-3.14: **Cleanup is verified, not assumed.** After every run — normal, timeout, or
    exception — the temp cwd is removed *and read back absent*. **One rule selects the failure:
    `CleanupFailed` is raised if a cleanup `OSError` was recorded OR the read-back finds the
    directory present** — either alone suffices, so an `rmtree` that raised *after* removing
    everything is still a failure (tested: a fault-injected `rmtree` that removes the tree and
    then raises) and a silent retention is still a failure. On that rule the API raises
    `CleanupFailed(path, cleanup_error)` — the `cleanup_error` attribute is the `OSError` when
    one was raised, `None` when only the read-back caught a silent retention; `__cause__` is the
    pending outcome when there was one — the `BlockTimeout`, or a `LaunchFailed` from the reap
    stage — else `cleanup_error` — and the CLI prints `DOCBLOCK: CLEANUP_FAILED path="<p>"`, plus an
    `os_error: "<text>"` detail line whenever `cleanup_error` is set, and exits 2
    (a timeout that also leaves an unremovable cwd reports `CLEANUP_FAILED`, tested as one case) —
    no `rc=`, because a run that left state behind is not the disposable measurement this FR
    promises. The fixture is a block that leaves an unreadable subdirectory
    (`mkdir keep && chmod 000 keep`); measured on this machine, `shutil.rmtree` raises
    `PermissionError` on it and `ignore_errors=True` retains the whole tree with no signal. A
    cleanup failure outranks a timeout on the same run: a retained directory is state the
    operator must act on; it is also the operational error (exit 2) where a timeout is a verdict
    (exit 0), so the exit code follows the precedence rather than contradicting it.

### FR-4: Verdict-token CLI following the established gate contract

- **Description**: The CLI prints one `DOCBLOCK:` line — one physical line, whatever the inputs:
  every dynamic field (`heading=`, `arg=`, keys, paths, OS-error text) is rendered as a
  double-quoted JSON string — `"`, `\`, every C0 and C1 control (U+0085 included), DEL and the
  Unicode line/paragraph separators U+2028/U+2029 escaped (anything `str.splitlines()` would
  break on), everything else
  verbatim — so a caller- or document-controlled value can never start a second `DOCBLOCK:` line
  nor forge a field token such as ` rc=0` inside the line (`heading="x rc=0"` is one quoted
  value; helper-constrained fields such as `rc=<n>`, `blocks=<n>`, `shell=`, `stage=` stay bare);
  tested with newline-bearing and token-bearing `--heading`, `--subst` and `--stdout` values — and
  the exit code follows the base
  **Audit-gate signal discipline** invariant exactly: **every verdict exits 0** — `RAN`, and every
  refusal that judged a readable input and declined to run it (`NOT_FOUND`, `AMBIGUOUS`,
  `AMBIGUOUS_HEADING`, `BAD_INDEX`, `BAD_TIMEOUT`, `BAD_ARGS`, `BAD_INFO`, `BAD_SUBST`, `SUBST_MISSING`,
  `SUBST_OVERLAP`),
  and `TIMEOUT`, which is a measured fact about the block (it did not finish) rather than a fault
  of the tool. **Exit 2 is reserved for genuine operational errors**, the invariant's own words:
  `UNREADABLE` (a document, preamble or stream path that could not be read, written or reserved,
  or a stream write that failed) and `CLEANUP_FAILED` (the helper could not honour its own
  disposable-cwd contract). A non-zero exit for a refusal would register as a tool failure in the
  orchestrator's harness — the failure mode the invariant names — so the earlier draft, which exited
  2 on every refusal after `ANCHORS_DRIFTED`/`MUTATION: PRECHECK_FAILED`, followed the minority
  precedent; the gate and the assembler (`GATE: FAIL`, `ASSEMBLE: HALT`, both exit 0) are the rule.
  A refusal carries no count that could be read as a **measured result** — never `rc=` — but may
  carry a *diagnostic* count saying why it declined, which is why `AMBIGUOUS` carries `blocks=<n>`
  (AC-4.4). Callers read the token, never `$?`.
- **Acceptance Criteria**:
  - AC-4.1: A successful run prints `DOCBLOCK: RAN rc=<n> blocks=1 shell=<strict|plain>` and exits
    **0**, including when the block's own `rc` is non-zero — the block's rc is data, not the tool's
    verdict.
  - AC-4.2: **The exit-code partition is pinned.** `NOT_FOUND`, `AMBIGUOUS`, `AMBIGUOUS_HEADING`,
    `BAD_INDEX`, `BAD_TIMEOUT`, `BAD_SUBST`, `SUBST_MISSING`, `SUBST_OVERLAP`, `BAD_INFO` and `TIMEOUT` each
    exit **0**; `UNREADABLE` (every `reason=`), `CLEANUP_FAILED` and `LAUNCH_FAILED` each exit **2**. A test
    enumerates the verdict table and asserts the code of every row, so a row cannot move between
    the two classes unnoticed.
  - AC-4.3: No cannot-judge line carries `rc=`, so a caller grepping `rc=` cannot read a
    non-measurement as a measured zero.
  - AC-4.4: `AMBIGUOUS` carries `blocks=<n>`; no other cannot-judge carries `blocks=`.
  - AC-4.5: Every detail line the script can emit has a matching remedy row in the Helper-scripts
    registry entry in `h-mad/SKILL.md`, and every row there corresponds to an emittable line
    (pinned bidirectionally by a test).
  - AC-4.6: **The helper's own failures are verdicts too, never tracebacks.** Every `OSError` the
    helper can raise on its own behalf — `tempfile.mkdtemp()` failing, `Popen` failing (`bash`
    absent from `PATH`), a `killpg` error other than `ProcessLookupError`, and an `OSError` from
    the helper's own read of the child's pipes (`communicate`), from the post-kill drain, or from
    closing the pipes or waiting on a signalled group (`stage=collect`, after which the child is
    killed and reaped exactly as a timed-out one) — maps to
    `DOCBLOCK: LAUNCH_FAILED stage=<mkdtemp|spawn|reap|collect>` with a detail line carrying the OS error
    text, exit 2, and the cwd (if one was created) is still cleaned up. Tests: `communicate`
    fault-injected on the recorded `Popen` instance → `stage=collect`, cwd gone, group reaped;
    `wait` fault-injected under a timed-out, signalled block → `stage=collect`; `mkdtemp`
    fault-injected to raise; `PATH` set to an empty directory so `bash` cannot be found (real, no
    mock); `os.killpg` fault-injected to raise `PermissionError` under a timed-out block — **and
    that test reaps what it launched**: `run_block` owns its `Popen` and exposes no handle, so the
    test wraps `subprocess.Popen` in a recording pass-through (the real constructor, its instance
    recorded — an observation, not a fault injection, the same seam AC-5.6 uses), and its
    `finally` sends the real `SIGKILL` to the recorded pgid, calls `wait()` on the recorded
    handle to reap the zombie leader, then asserts the group is gone, so the test
    cannot recreate the orphan-process incident this feature cites. For a *genuinely*
    unsignalable group the helper's policy is diagnostic, not containment: the verdict's detail
    carries `pgid=<n>` so the operator can act, and this is the one documented case in which a
    launched process may outlive the call.

### FR-5: Bounded execution without an external time-bounder

- **Description**: Every run is time-bounded. `timeout`/`gtimeout` are forbidden by the skill's own
  rules and are not used; the bound is Python's own.
- **Acceptance Criteria**:
  - AC-5.1: A block that sleeps past the bound returns `DOCBLOCK: TIMEOUT seconds="<n>"` and exits 0
    — the hang is a measured fact about the recipe, like a non-zero `rc`, not a tool fault.
  - AC-5.2: After a timeout, **no descendant remaining in the launched process group** is alive —
    the whole group is reaped, not just the direct child. The claim is bounded deliberately: a
    descendant that leaves the group (`os.setsid()`, or a `setsid` binary where one exists) is
    outside what a group kill can reach. Measured this session — an in-group `sleep` died,
    a descendant that called `os.setsid()` **survived** — so "no descendant survives" would assert
    containment this design does not implement. A first probe using the `setsid` **binary** showed
    no escape and was **vacuous**: that binary is absent on macOS, so it measured nothing.
  - AC-5.3: The source contains no invocation of `timeout` or `gtimeout`.
  - AC-5.4: The temp cwd is removed after a timeout, exactly as after a normal run.
  - AC-5.6: **The bound is validated before anything is spawned.** `timeout` must be a finite
    number greater than zero: `0`, a negative value, `nan`, `inf` and a non-numeric
    `--shell-timeout` argument all refuse with `DOCBLOCK: BAD_TIMEOUT value="<v>"`, exit 0, block
    not run — `run_block` raises `BadTimeout(value)` before `Popen`. Left to `argparse` and
    `communicate`, a negative value raises `ValueError` *after* the spawn and `inf` makes the
    promised bound unbounded. On the CLI the value is taken as a string and validated by `main`,
    so a non-numeric argument reaches the `DOCBLOCK:` contract rather than argparse's usage path;
    the same policy makes a non-integer `--index` a `BAD_INDEX`. argparse's own usage path is routed too: the parser is built with `allow_abbrev=False`, `exit_on_error` left at argparse's default `True` (with `False` a missing option value raises `argparse.ArgumentError` past the override — measured), and its
    `error()` raises `BadArgs(message)`, rendered as `DOCBLOCK: BAD_ARGS message="<m>"`, exit 0, so an
    unknown option or a missing value is a verdict and there is no non-`DOCBLOCK` exit (`--help`
    alone keeps argparse's exit-0 help text).
  - AC-5.5: **The timeout path has no unhandled race.** Two windows, both specified and both
    tested: (a) the group has already emptied by the time `killpg` runs. **The helper calls
    `proc.poll()` before `killpg`**, because a leader that exited is a zombie until reaped and,
    measured on macOS, `killpg` on a zombie-only group raises `PermissionError`, not
    `ProcessLookupError`; after `poll()` reaps it the same call raises `ProcessLookupError`, which
    is treated as "already reaped", never a traceback. **The test needs no fake**: a leader that
    starts an `os.setsid()` descendant holding stdout and exits at once produces exactly this
    state (plan §Measurements cites the probe), and the same fixture drives (b); (b) the
    post-kill drain `communicate` itself times out because an out-of-group descendant (AC-5.2's
    escapee) still holds the pipes — the helper closes both pipes, reaps the leader, and reports
    `TIMEOUT`. Either way the verdict is `DOCBLOCK: TIMEOUT`, exit 0, and the cwd is gone. Total
    wall time is bounded by `timeout` plus a fixed drain allowance (`2 * DRAIN_SECONDS`: the drain
    and the bounded post-kill `wait(timeout=DRAIN_SECONDS)`, whose expiry is `LAUNCH_FAILED
    stage=reap`), so FR-5's "every run is
    bounded" holds against an escapee too. Both (a) and (b) are driven by one real
    `os.setsid()` fixture, no mock; `os.killpg` is monkeypatched only for AC-4.6's
    `PermissionError`-after-`poll()` case — one of exactly **eight** named fault injections this
    suite permits (`os.killpg`, `shutil.rmtree`, `tempfile.mkdtemp`, `os.chmod`, `os.unlink` for
    the reservation rollback's read-back, the module's
    own `_final_write` seam for AC-3.8's post-run write failure, its `_close_stream` seam for
    the backstop close on a path where the final write never ran, and the recorded `Popen`
    instance's own `communicate`/`wait`/`poll` for AC-4.6's `collect` stage and AC-5.5's bounded
    post-kill wait — one instance-level injection, three methods, seven module seams beside it
    through the AC-5.6 recording pass-through, `subprocess.Popen` itself still real; the design's
    Test Strategy bounds the list, and `subprocess` is never mocked).

### FR-6: Migrate the existing inline harness onto the helper

- **Description**: `h-mad/tests/test_h_mad_collect_report_docs.py` hand-writes extraction at
  `:270` and `:412` with `re.findall(r"```bash\n(.*?)```", …)`, and runs the block inline in
  `run_recipe` at `:309`. **The two extractors select different blocks** — measured at `a8e0372`
  with the extractor's own regex over the section the test itself bounds:

  ```
  # from the repository root. Deliberately ONE line and outer-single-quoted: a shell
  # continuation inside single quotes is literal, and inside DOUBLE quotes the fence
  # backticks would be command substitution. Copy it whole.
  $ python3.11 -c 'import sys,re; sys.path.insert(0,"h-mad/tests"); import test_h_mad_collect_report_docs as t; b=re.findall(r"```bash\n(.*?)```", t._second_surface(), re.S); print(len(b), [i for i,x in enumerate(b,1) if "h_mad_audit_gate.py" in x], [i for i,x in enumerate(b,1) if "exec codex" in x])'
  7 [4] [2]
  ```

  The Second-surface section holds **seven** bash blocks; `:270` takes the one containing
  `h_mad_audit_gate.py` (block 4, the gate recipe), `:412` takes the one containing `exec codex`
  (block 2). The **ordinals are the load-bearing part and are unchanged.** The total was written as
  four in an earlier draft; running the same extraction over `git show <sha>:h-mad/SKILL.md` at the
  three points gives `6db8e50^` → 4 blocks / 1 `##` heading in the section, `6db8e50` → 7 blocks /
  2 headings, `a8e0372` → 7 blocks / 2 headings. So the drift is one commit's, `6db8e50`, which
  inserted a `##` heading between the two string anchors `_second_surface()` bounds on and widened
  the section; the gate block reads 4 and the exec-codex block 2 at **all three** shas, because the
  arrivals land after block 4. Only `:270`'s block is tagged, so only `:270` breaks when the tag lands, and only
  `:270` migrates. `:412` never executes anything — it asserts the exec recipe carries
  `--out`/`--log`/`--timeout` — and running that block would dispatch a real agent, so it stays a
  text inspection deliberately. The executing migration and the first tag land together.
- **Acceptance Criteria**:
  - AC-6.1: The Second-surface gate block in `h-mad/SKILL.md` carries the `hmad:exec` tag, **and
    it is the only fence in the tree that does**: a test counts opening fences carrying the tag
    and asserts exactly one, so a second opt-in fence cannot arrive by accident. **The sweep is
    stated here rather than by reference**: `*.md` files under `h-mad/` and `handoff/`, excluding
    any `archive/` path and any dot-directory. Two things this pins that a reference could not.
    The `*.md` restriction is load-bearing — the scanner is a markdown scanner, and the feature's
    own test module carries column-0 tagged fences inside triple-quoted fixtures, which an
    unrestricted sweep counts as openers and which would make this AC unpassable at GREEN. And the
    dot-directory exclusion is **deliberately not `git ls-files`**, which is what §Scanning's
    measurement corpus uses: a measurement should describe the tracked tree, but this guard must
    still catch a tagged fence in a document that has been written and not yet committed — that is
    precisely the accident it exists to refuse. Earlier drafts reached this scope only by pointing
    at "the plan's fence census", which at the time was a filesystem glob contaminated by
    gitignored `.pytest_cache/README.md` artifacts; a reference inherits whatever the referent
    becomes, so both halves are spelled out. Residual: a generated `.md` written inside these roots
    outside a dot-directory is counted, and a tagged fence in a non-`.md` file is not.
  - AC-6.2: The **executing** path resolves its block through `h_mad_doc_block_exec`: `:270`'s
    hand-rolled `re.findall` and `run_recipe`'s inline `subprocess` are both gone. `:412` keeps a
    text scan and that is correct, not a leftover — it inspects an untagged block it must never
    run, so routing it through an executor that returns only tagged blocks is impossible by
    construction and undesirable besides. A test asserts `:412` still performs no execution.
  - AC-6.3: The four behaviours the existing tests pin — the `COLLECT: OK` guard before gating, the
    delivered-report `GATE: PASS`, the undelivered-report `report_not_collected` halt without
    reaching the gate, and the absence of a shell-killing bare `exit` — all still pass after the
    migration. Both the delivered and the missing paths are driven **through the preamble boundary
    of AC-3.11**, which is what supplies `COLLECT_OUT` by running the real collector; a migration
    that cannot supply it cannot reach the `GATE: PASS` branch at all.
  - AC-6.4: The full suite passes, and the count is no lower than the pre-change count plus the
    tests this feature adds. **The floor is mechanical, not prose**: the baseline is the constant
    `2748` (collected and passing at `e8eaf6f`, cited in the plan with its commands and its re-measure-at-5c rule; it was `2747` at `6b4df35` and `b59e05e` moved it, which is why the commit travels with the number); the
    feature's additions are the collected count of the new module
    `h-mad/tests/test_h_mad_doc_block_exec.py` (derived by running the collector on that file
    alone) plus a fixed tuple of the named new node IDs added to **pre-existing** files, each of
    which the test asserts exists. **This spec deliberately carries no total for that tuple**; the
    floor uses `len(tuple)`, so a number restated here would be a second authority that drifts
    against the plan's enumeration and buys nothing. What the spec fixes instead is the
    **membership rule**, because the tuple has two sources and only one of them is a test anyone
    writes by hand:
      1. Nodes added directly to a consumer file — the wire and exemption tests in
         `test_h_mad_collect_report_docs.py` and the delegation spy test in `test_docsections.py`.
      2. **One node per glob-parametrised test, per new file this feature adds under
         `h-mad/scripts/`.** `test_h_mad_portable_timeout.py` globs `(SKILL / "scripts").glob("*.py")`
         into `_SCANNED` and parametrises over it twice — verified at `a8e0372` with
         `grep -c 'parametrize("path", _SCANNED' h-mad/tests/test_h_mad_portable_timeout.py` -> `2`
         — so Task 1's `h-mad/scripts/h_mad_doc_block_exec.py` adds exactly two nodes:
         `test_no_document_or_script_emits_a_bare_timeout_command[h_mad_doc_block_exec.py]` and
         `test_no_document_or_script_rests_on_an_unconditional_absence_claim[h_mad_doc_block_exec.py]`.
         These must **pass**, not merely be counted: the new script carries no bare `timeout <n>`
         form and no unconditional absence claim. Omitting them makes the floor tolerate two
         silent deletions of pre-existing tests — the exact weakening this AC exists to prevent.
      Residual, stated as categories rather than "and similar": a second new script from this
      feature adds two more nodes by the same rule; a third glob-parametrised test over the same
      directory would add one per new script; and a glob that loops **inside** one test body rather
      than parametrising adds coverage but no node, so it is out of the tuple — verified at
      `a8e0372` that the two other `*.py` globs in the suite are of that second kind —
      `git grep -n 'glob("\*\.py")' -- 'h-mad/tests/*.py'` returns three hits, `_SCANNED` itself
      plus `test_h_mad_collect_report.py:287`, which loops but filters to two named writer modules
      so a new script is skipped, and `test_hmad_dispatch_audit_cycle.py:250`, which globs a
      `tmp_path` fixture directory rather than the real one.
    Every other new test, the collect-alone pins included, lives in the new module.
    `test_suite_floor_holds` asserts `full_collected >= 2748 + new_module + len(tuple)`
    from a `--collect-only` subprocess (collection never executes tests, so the suite does not
    recurse into itself; an env guard `DOCBLOCK_FLOOR_INNER=1` makes any inner instance skip, as a
    belt beside those braces). The *pass* half cannot live inside the suite it measures: it is the
    Phase-5f gate command, `( cd "$(git rev-parse --show-toplevel)" && hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider ) > /tmp/doc_block_exec_suite.log; RC=$?   # from the REPOSITORY ROOT: the 2748 baseline is the root count; from h-mad/ the same command collects 2486; tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"   # bounded through the reachable dispatcher (base Portable time bounds); rc=124 is the wrapper's expiry, not a suite result`, run alone by the orchestrator and recorded in the report:
    the last line must read `N passed` with no failures **and** `SUITE: rc=0` — the exit status is
    captured before `tail`, because a bare pipe reports `tail`'s status and lets a red suite print
    as success.
    A deleted pre-existing test lowers the collected count below the floor and cannot hide behind
    the additions.
  - AC-6.5: **Connection discrimination.** Reverting the connection alone — the import of
    `h_mad_doc_block_exec` and the call to it in `test_h_mad_collect_report_docs.py`, leaving the
    helper and its own tests intact — makes a named test in that file fail. The helper's own suite
    still passes under that revert, which is what proves the failing test is pinning the *wire*
    and not the callee.
  - AC-6.6: The opposite direction: making the migrated call site unconditional — resolving the
    block without regard to the tag — also makes a named test fail. Without this, a wire that
    fires always is indistinguishable from one that fires correctly.

## Non-Functional Requirements

- **Performance**: N/A. Each call runs one bash block; the bound in FR-5 is the only timing
  contract.
- **Security**: The helper executes shell text out of a document, so the opt-in tag is the security
  boundary and must remain the only way a block is selected. No API accepts a directory, a glob, or
  an "all blocks" flag. Temp dirs are created with `mkdtemp` (0700) and removed.
- **Compatibility**: Stdlib-only, consistent with every other `h-mad/scripts/` helper. Must run on
  the repository's pinned interpreter without third-party packages. Tagged fences must continue to
  render as bash in ordinary markdown viewers.

## Out-of-Scope

- Any blanket or directory-wide sweep of bash fences. There are 68 under `h-mad/` and `handoff/`
  (re-measured this session, excluding archive); this feature executes only tagged ones and adds
  exactly one tag.
- Tagging fences beyond the Second-surface gate block. Further tagging is a separate, deliberate
  decision per block — that is the point of an opt-in marker.
- A `name=` addressing key on the info string. Ordinal addressing suffices at one consumer; `name=`
  is additive later without breaking anything specified here.
- A `--list` mode enumerating tagged blocks. Cheap and plausible, but nothing in this feature needs
  it, and `grep -n '```bash hmad:exec'` already answers the question.
- Languages other than bash. The tag is defined on ` ```bash ` fences only.
- Executing blocks in any other repository, or in the installed `~/.claude/skills` copy rather than
  the checkout under test.

## Assumptions

- `bash` is on PATH. Every recipe in these skills already assumes it.
- The `hmad:exec` info string is inert to the markdown renderers in use. **Specification-backed,
  measured on GitHub's real renderer and on the CommonMark reference port** — the repository
  itself contains no multi-word info string to point at (`grep -rn '^```bash [^ ]' h-mad handoff`
  excluding `archive/` → 0), so the renderers were probed directly. GitHub's `POST /markdown`
  endpoint is the renderer github.com uses:

  ```
  $ printf '%s' '{"text":"# T\n\n```bash hmad:exec shell=plain\necho hi\n```\n\n~~~\n```bash hmad:exec\nquoted\n```\n~~~\n","mode":"gfm"}' > /tmp/gh_md.json
  $ curl -s -X POST -H "Accept: application/vnd.github+json" -H "Content-Type: application/json" --data @/tmp/gh_md.json https://api.github.com/markdown
  <h1>T</h1>
<div class="highlight highlight-source-shell"><pre class="notranslate"><span class="pl-c1">echo</span> hi</pre></div>
<pre class="notranslate"><code class="notranslate">```bash hmad:exec
quoted
```
</code></pre>
  ```

  The tagged fence is highlighted as shell (`highlight-source-shell`), and the `~~~` block quoting
  the tag is a plain code block — the two facts AC-1.6 and the info-string grammar rest on. The
  CommonMark reference port agrees (`markdown-it-py 4.2.0`, throwaway venv:
  `<code class="language-bash">` for the tagged fence, the tilde-quoted tag rendered as body). The
  Claude Code viewer has no headless renderer to probe; it is a CommonMark viewer and the one-line
  exposure is reversible, so it is confirmed by eye at Phase 5 after the tag lands.
- The two extractors named in FR-6 are the only in-repo consumers that anchor on a bare
  ` ```bash\n ` opener in a file this feature tags. **Measured over the tracked tree at
  `a8e0372`** (`-E`, because git's default regex is not GNU BRE and `\|` is not portable here):

  ```
  $ git grep -n -E 'findall.*```bash|split.*```bash|re\.compile.*```bash' -- '*.py'
  h-mad/tests/test_h_mad_collect_report_docs.py:270:    blocks = re.findall(r"```bash\n(.*?)```", section, re.S)
  h-mad/tests/test_h_mad_collect_report_docs.py:412:        (b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b),
  ```

  A broader sweep for the bare literal, over the **tracked** tree so no gitignored or
  not-yet-committed artifact contaminates it, returns six hits at `a8e0372`; the four that are
  not extractors are inline fixture strings and one prose comment:

  ```
  $ git grep -n '```bash' -- '*.py' | wc -l          # -> 6   (at a8e0372)
  ```

  — `test_docsections.py:27`, `test_h_mad_assemble_tdd.py:489` and `:551` are fixture strings, and
  `h-mad/scripts/h_mad_precheck_doc.py:100` is a comment quoting the literal inside a worked
  example. Control that the narrow pattern is not under-matching:

  ```
  $ git grep -l '```' -- '*.py' | wc -l              # -> 24  (at a8e0372)
  ```

  Twenty-four tracked `.py` files contain a fence literal and exactly two of them extract on a
  bare ` ```bash ` opener, which is the census's conclusion and the part that matters; the total
  itself has moved twice (21 → 23 → 24) without that conclusion changing, because the arrivals
  were fixtures and comments, not extractors. One further consumer reads `SKILL.md` and was
  checked directly — `h-mad/tests/docsections.py:37` bounds fences with
  `stripped.startswith("```")`, a **prefix** match, so an info-string tag does not disturb it.

  **Rule for every tree-derived count in this document, stated once here rather than beside each
  number.** A count taken from the tree is written with (a) the exact runnable command that
  generates it and (b) the sha it was observed at, in that order, on the same surface as the
  number — including inside fenced blocks, table cells and comments embedded in commands, which is
  where this document's v1.54 miss lived (the `21` here, by contrast, sat in plain prose, so the
  surface is not the discriminator; the missing command is). A count without its command is the defect, not
  merely stale: the reason `21` survived two drifts unnoticed is that no reader could re-run it.
  Prefer `git grep`/`git ls-files` over a filesystem walk so the corpus is the tracked tree; if a
  filesystem walk is genuinely wanted, say so in the same clause. Where a count is only a control
  on a conclusion, state the conclusion separately so a drifted total cannot be read as a defect
  in the conclusion. Re-verify at implementation time rather than trusting these blocks; the point
  of citing them is that a reviewer can re-run them, not that they never go stale.

  Residual — three categories deliberately outside this rule, so their numbers are not swept.
  (1) Version History entries are a record of what was believed in their era and keep their
  era's numbers. (2) Counts of things that do not exist yet — the new module's collected count,
  the seven module seams of FR-5's injection list — are design-derived, not tree-derived, and move
  only when the design moves. (3) `path:line` locators (`:270`, `:309`, `:412`, `docsections.py:37`)
  are locators, not counts; all four were re-verified at `a8e0372`. They are still line numbers and
  will still drift, and rewriting them as structural locators is owed by this document, the design
  and the plan **together** — done in one document alone it would read downstream as a
  disagreement about which block is meant.
- A block's declared shell mode is a property of the recipe, not of the caller, so it belongs on
  the fence rather than in the test.

## Version History

- v1.0: Initial specification draft.
- v1.1: Add AC-6.5/AC-6.6 connection discrimination for the FR-6 wire; cite the extractor census command and output (plan audit v1: codex must-fix, agy p2 should-fix).
- v1.2: Add AC-3.8/AC-3.10 for the optional stdout/stderr path arguments and their pre-run refusal (plan audit v2 codex should-fix).
- v1.3: Value sweep of the audit v2 count-rule finding: FR-4's own description carried the same loose phrasing; reorder AC-3.7..3.9 into sequence.
- v1.4: Design audit v2: AC-1.8 differential bounder test (Single-source contract), AC-2.6/AC-2.7 sequential counting and overlapping-key refusal.
- v1.5: Design audit v3: AC-1.1 reflects the extract/select split, AC-1.5 accepts ATX-only bounding explicitly, AC-3.7 scopes BAD_INFO to tagged fences only.
- v1.6: Design audit v4 back-propagation: AC-1.8 becomes single-authoritative-bounder with docsections delegating, because the differential test it previously specified is unachievable against AC-1.6.
- v1.7: Plan re-audit v5: only the executing call site migrates — :270 and :412 select different blocks (measured, 4 blocks in the section), so the earlier 'both extractors break' claim was false and AC-6.2 was unsatisfiable; add docsections.py to Deliverables.
- v1.8: Plan re-audit v6: name tempfile.mkdtemp() explicitly rather than the carried 'mktemp -d' wording, which reads as a shell invocation; add AC-3.13 pinning the stdlib call, 0o700 mode and the absence of a mktemp invocation.
- v1.9: Plan re-audit v7: scope AC-5.2 to the launched process group (a setsid descendant escapes, measured); refuse aliased --stdout/--stderr (AC-3.9); correct the risk row that still claimed both extractors break.
- v1.10: Renumber FR-3 acceptance criteria contiguously after inserting the aliased-stream refusal (3.8b becomes 3.9); 40 ACs.
- v1.11: Plan re-audit v8: add the fixture preamble boundary (AC-3.11/AC-3.12) — without it the gate block's COLLECT_OUT is unbound under strict bash and the FR-6 migration cannot reach GATE: PASS.
- v1.12: Plan re-audit v9: refuse duplicate headings (AC-1.7) — invariants.example.md has two; cite the controlled preamble pair, which also narrows the earlier 'aborts on unbound variable' claim to 'cannot reach GATE: PASS'.
- v1.13: Plan audit v11 + design audit v5 (codex must 2+4, agy must 9): AC-1.9 ordinal-below-1 refusal (BAD_INDEX), AC-3.14 verified cleanup (CLEANUP_FAILED), AC-5.5 timeout races (killpg ProcessLookupError, bounded drain against an escapee); AC-1.8 names the self-contained sys.path import and its collect-alone test; AC-4.2 lists every exit-2 verdict. 46 ACs.
- v1.14: Plan re-audit v13 back-propagation: AC-3.8 states overwrite semantics and the post-run stream_write_failed refusal; AC-3.14's CleanupFailed carries its cause.
- v1.15: Plan re-audit v14: AC-3.11 states the preamble/block composition rule (one newline boundary, always) and its no-trailing-newline test.
- v1.16: Design audit v6 (agy must 1, codex must 2 should 2): AC-3.11 composes the preamble with the substituted text; AC-5.6 validates the bound before spawn (BAD_TIMEOUT) and states the values-vs-grammar CLI policy; AC-3.6 pins UTF-8/replace str streams; AC-6.1 asserts tree-wide tag cardinality 1; AC-3.8 probes stream paths without truncation and reserves after every check. 47 ACs.
- v1.17: Design audit v7 (codex must 4 should 1; agy clean): AC-3.8 reserves both streams in append mode after every refusal and truncates only at the final write; AC-6.4's floor is computed (2747 + new module + named tuple); AC-2.7 defines keys= as distinct keys and orders the overlap lines.
- v1.18: Design audit v8 (codex must 3 should 1, agy must 2): exit codes follow the Audit-gate signal discipline invariant — every verdict incl. refusals and TIMEOUT exits 0, only UNREADABLE and CLEANUP_FAILED exit 2 (FR-4, AC-4.2 pins the partition row by row); AC-3.14 names the timeout-plus-cleanup case; AC-6.4's collected floor is in-suite via collect-only and the pass half is the out-of-suite gate command.
- v1.19: Design audit v9 (codex must 3 should 1; agy clean): AC-4.6 maps the helper's own mkdtemp/Popen/killpg failures to LAUNCH_FAILED; AC-3.9 compares (st_dev, st_ino) on the opened descriptors so hard links are caught with no check-to-open window; AC-3.14 names cleanup_error and the __cause__ rule; AC-6.4's gate command captures pytest's status before tail. 48 ACs.
- v1.20: Design audit v10 (codex must 2 should 1, agy must 1): AC-3.12 reads the preamble and the document as strict UTF-8 and maps a decode failure to UNREADABLE.
- v1.21: Design audit v11 (codex must 3; agy must 1): AC-2.8 gives --subst a parser contract (split once on the first '=', empty key and repeat refused as BAD_SUBST); AC-3.13 adds os.chmod(cwd, 0o700) because mkdtemp alone is 0700 & ~umask (measured 0o0 under umask 0777) and tests under a hostile umask; AC-4.6's reap test reaps what it launched and the unsignalable-group policy is stated. 49 ACs.
- v1.22: Design audit v12 (codex must 2; agy must 3): AC-5.5 names the three permitted fault injections instead of 'the one'; AC-3.14's __cause__ rule includes a reap-stage LaunchFailed; AC-6.4's tuple is the five consumer-file tests only.
- v1.23: Design audit v14 (codex must 5; agy must 2): the renderer-inertness assumption is marked specification-backed but unmeasured (no multi-word fence in the tree, no local renderer) with a Phase-5 operator check; AC-5.5 names four permitted fault injections (os.chmod added); AC-3.13's chmod failure is tested and mutation-covered.
- v1.24: Design audit v15 (codex must 5 should 2; agy clean + 1 nit): AC-1.6 covers tilde fences; AC-3.14's failure rule is 'recorded error OR read-back present'; the renderer assumption is now MEASURED on GitHub's POST /markdown and on markdown-it-py, command and output cited; AC-3.8 orders the writes, reports partial state, and names the _final_write seam (fifth injection); AC-2.8's empty-key rule lives in substitute; AC-1.7 carries heading=.
- v1.25: Design audit v16 (codex must 3; agy clean): AC-5.5's killpg fake really empties the group before raising; AC-3.13's chmod rollback goes through the ordinary cleanup selection so a failing removal is CLEANUP_FAILED.
- v1.26: Design audit v17 (codex must 1; agy pass UNVERIFIED, dispatch rc=1): AC-1.6 states the CommonMark 0-3 space indentation rule for openers and closers; a four-space-indented literal tag is never a candidate.
- v1.27: Design audit v21 (codex must 1): AC-5.5(a) is reproduced by a real fixture — a leader that exits behind an os.setsid() escapee — and the helper polls before killpg, because killpg on a zombie-only group raises PermissionError on macOS (measured); os.killpg is injected only for AC-4.6.
- v1.28: Design audit v23 (codex should 1; agy must 2 should 2): AC-1.5 no longer names the impossible differential test; _final_write flushes and closes inside the mapped region; CLEANUP_FAILED carries an os_error detail line.
- v1.29: Design audit v24 (codex must 1 should 1; agy nit): AC-3.8 specifies the stdout-first failure branch (failed/skipped detail lines with registry rows); AC-4.6's reap test obtains its handle through the recording Popen pass-through and states the teardown order.
- v1.30: Design audit v25 (codex must 1 should 1; agy clean): AC-3.8 names the atomic create-or-open ownership rule and the single closure path for held handles.
- v1.31: Design audit v26 (agy must 4 should 1; codex must 1): AC-2.6 makes substitution simultaneous with counts on the original text, closing the map-order dependency sequential replacement had; AC-6.4's tuple is six tests.
- v1.32: Design audit v27 (codex must 2; agy must 2 should 2): AC-2.6's discriminating fixture (A B -> B C in both orders); AC-3.8 read-back verification of every written artifact; AC-6.4's tuple is seven across two files.
- v1.33: Design audit v28 (codex must 1 should 2; agy must 2 should 1): SUBST_MISSING carries keys=<n> like SUBST_OVERLAP; an empty map is a no-op; duplicated info-string tokens refuse as BAD_INFO.
- v1.34: Design audit v29 back-propagation: FR-4's exit-0 list names BAD_SUBST.
- v1.35: Design audit v31 (codex must 2; agy UNVERIFIED, dispatch timeout): AC-2.3 orders missing keys by map insertion; AC-3.12 defines rc as the exit code of the one spawned bash -c.
- v1.36: Design audit v33 back-propagation (nits): NOT_FOUND and AMBIGUOUS examples carry heading=<h>.
- v1.37: Design audit v38 (codex must 1; agy clean): AC-1.6 — a backtick fence whose info string contains a backtick is not a fence (CommonMark; measured on markdown-it-py and GitHub).
- v1.38: Design audit v43 back-propagation: AC-3.8 adds the backstop-close failure verdict stream_close_failed with its precedence; the named-injection list is six with the _close_stream seam.
- v1.39: Design audit v62 back-propagation: AC-4.6 covers an OSError from the helper's own communicate/drain/close/wait on the child as LAUNCH_FAILED stage=collect, tested by fault-injecting the recorded Popen instance.
- v1.40: Design v1.66 back-propagation: seven named fault injections (the recorded Popen instance's communicate/wait for the collect stage).
- v1.41: Design v1.67 back-propagation: AC-1.7 states heading text is compared after the CommonMark closing hash run is stripped (`## Text ##` == `## Text`).
- v1.42: Design v1.69 back-propagation: AC-3.10's failed-second-reservation rollback is read back and reports `leftover: <path>`; eight named fault injections (os.unlink added).
- v1.43: Design v1.73 back-propagation: the drain allowance is 2·DRAIN_SECONDS (drain + bounded post-kill wait, expiry = LAUNCH_FAILED stage=reap); the instance-level injection names communicate/wait/poll.
- v1.44: Design v1.75 back-propagation: FR-4's one-line contract holds for every input — dynamic fields are control-character-escaped.
- v1.45: Design v1.78 back-propagation: AC-2.8 authorizes the two-layer empty-key rule (main refuses with the raw argument; substitute is the API guard); FR-4's dynamic fields are quoted JSON strings so no value forges a token.
- v1.46: Design v1.80 back-propagation: verdict/detail examples rewritten in the quoted-field grammar; _field stringifies before json.dumps.
- v1.47: Design v1.81 back-propagation: `key=` and both `overlap:` elements quoted.
- v1.48: Design v1.82 back-propagation: FR-4's escape set names C1 controls, DEL and U+2028/U+2029.
- v1.49: Plan audit v65 agy back-propagation: AC-6.4's gate command is bounded through hmad-dispatch run --timeout 1200 (1 occurrence(s) rewritten), as the plan and design already state.
- v1.50: Impl-plan v1.26 back-propagation: AC-6.4's gate command runs from the repository root in a subshell (from h-mad/ it collects 2485, not the 2747 baseline); the subshell propagates the wrapped status (measured).
- v1.51: Design v1.84 back-propagation: the empty-key CLI refusal prints arg="=V" (quoted).
- v1.52: Design v1.85 back-propagation: BAD_ARGS verdict for argparse grammar errors (no non-DOCBLOCK exit); AC-3.10 states the concurrent-replacement non-goal and the identity check.
- v1.53: Plan audit v73 / design audit v82 back-propagation (teammate surface, advisory). AC-6.4's floor baseline re-measured to 2748 at e8eaf6f (was 2747 at 6b4df35; b59e05e moved it), with the commit now travelling with the number. AC-5.6 states exit_on_error at argparse's default True — with False a missing option value raises argparse.ArgumentError past the overridden error() and escapes main as a non-DOCBLOCK exit.
- v1.54: Plan audit v74 back-propagation. AC-6.4's embedded Phase-5f gate command still carried the pre-fix 2747/2485 pair in its comment while the AC body around it said 2748/2486 — so the same AC stated both. My v1.53 sweep updated the prose and missed the number inside the command comment, which is the sixth instance this session of a value swept in one surface and not another; the plan's rule 7 (sweep every surface that states a value, including inside embedded commands and table cells) is the general form.
- v1.55: Design v1.93 back-propagation. AC-6.1 states its own sweep instead of reaching it by reference to the plan's fence census: *.md under h-mad/ and handoff/, excluding archive/ and any dot-directory. The reference was the defect, not the scope — that census was a filesystem glob contaminated by gitignored .pytest_cache/README.md artifacts, and a reference inherits whatever its referent becomes. Both halves are now pinned here with their reasons: the *.md restriction, because the feature's own test module carries column-0 tagged fences in triple-quoted fixtures that an unrestricted sweep would count; and the dot-directory exclusion rather than git ls-files, deliberately different from the measurement corpus, because this guard must still catch a tagged fence in a document written but not yet committed. Residual stated.
- v1.56: Round-three back-propagation of four findings raised against the plan (v75), design (v84) and impl-plan (v35), all of which land here. Findings 1+2 are one class, not two edits: every tree-derived count in this document now carries the exact runnable command that generates it AND the sha it was observed at, on the same surface as the number. The extractor census's control was 21 .py files with a fence literal and is 24 at a8e0372 (git grep -l '```' -- '*.py' | wc -l); it had already drifted through 23 unnoticed precisely because no generating command travelled with it, and the corpus is now git grep rather than a filesystem walk so gitignored and uncommitted artifacts cannot contaminate it. The broad literal sweep was five hits with three non-extractors and is six with four at a8e0372, the arrival being a prose comment in h_mad_precheck_doc.py. Neither total touches the census's conclusion, which is that exactly two consumers extract on a bare bash opener, so the conclusion is now stated apart from the control. Residual: Version History entries keep their era's numbers, design-derived counts of things that do not exist yet are out of class, and path:line locators are locators not counts. FR-6's Description carried the same stale block census the design carried: the Second-surface section holds seven bash blocks at a8e0372, not four, because 6db8e50 inserted a ## heading between the two string anchors _second_surface() bounds on. The ordinals are unchanged and are the load-bearing part -- the gate block is still 4 and the exec-codex block still 2, because the arrivals came after block 4. AC-6.4 no longer carries a total for its node tuple. The old 'seven enumerated in the plan' was nine, because Task 1's h-mad/scripts/h_mad_doc_block_exec.py adds one node to each of the two tests that parametrise over _SCANNED, and a floor short by two tolerates two invisible deletions. Rather than restate a number that drifts on any script add, the AC now fixes the membership rule over the axis -- consumer-file nodes, plus one node per glob-parametrised test per new h-mad/scripts file -- requires those nodes to pass and not merely be counted, and states the residual, including that a glob looping inside one test body adds coverage but no node.
