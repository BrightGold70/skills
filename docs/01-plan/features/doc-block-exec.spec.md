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
    measured on markdown-it-py — through the committed grammar probe's interpreter named in
    §Assumptions, agreeing at `4.2.0` and at `2.2.0`, though this case is **not** among the probe's
    own printed lines and so is this AC's own measurement — and on GitHub's renderer, both of which emit it as a paragraph
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
    are duplicates. **The closing run counts as a closing run only when it is preceded by a space
    or a tab**, which CommonMark requires and which an unconditional right-strip of `#` gets wrong:
    measured on markdown-it-py in `commonmark` preset — through the committed grammar probe's
    interpreter named in §Assumptions, agreeing at `4.2.0` and at `2.2.0` — `## Text ##` → `Text`,
    `## Text\t##` →
    `Text`, and `## Text##` → `Text##`. **What the probe itself covers is stated so the citation is
    not read wider than it is**: its own printed lines include the closing-hash strip (`## x ##`)
    and the opening tab (`##\tx`), and they do **not** include the tab *before* a closing run or
    the no-space `Text##` form, so those two remain this AC's own measurement through the same
    interpreter. So `## Text##` is **not** a duplicate of `## Text` and
    stripping it as one would fire this refusal on two distinct headings. Nothing is executed:
    `DOCBLOCK: AMBIGUOUS_HEADING count=<n>
    heading="<h>"`, exit 0. Two identical headings share one address, and silently taking the first would run a
    tagged block from the wrong section — the same silent-wrong-answer shape the tag exists to
    prevent, one level up, and the tag cannot repair an ambiguous *section* selector. Not
    hypothetical: `h-mad/invariants.example.md` already carries `### Unified-facade routing` and
    `### Data-source priority` twice each — measured at `74e126f`, 16 headings, 2 of them
    duplicated:
    `git grep -hcE '^#{1,6} ' -- h-mad/invariants.example.md` → 16, and
    `git grep -hE '^#{1,6} ' -- h-mad/invariants.example.md | sort | uniq -d | wc -l` → 2, both at
    `74e126f`. That file holds no fences at all (`git grep -c '^```' -- h-mad/invariants.example.md`
    → no match at `74e126f`), so a raw line grep cannot mistake a `#` comment inside a fence for a
    heading here. Residual: those two commands compare raw lines rather than closing-hash-stripped
    text, so the 2 is a floor on duplicates under this AC's own comparison, never a ceiling.
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
    another module's `sys.path` side effect.
    **The collect-alone pin is collection-only, and that is a contract rather than an
    implementation detail.** It runs `[sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "h-mad/tests/test_docsections.py"]`
    from the repository root and requires exit 0, which proves the module imports and every test in
    the file collects when the file is collected alone — **while running none of them**. It must
    not run that file, because AC-6.4 adds a node to it (the delegation spy that pins the wire) and
    AC-6.5 requires that node to be the test that fails under a reverted delegation. A pin that ran
    the whole file would go red under the same revert, so the failure would not be wire-only and
    AC-6.5's discrimination claim would be false — a subprocess asserting exit 0 over a file this
    feature is adding a deliberately-failing-under-mutation test to is a contradiction, not a
    stronger check.
    **Residual, stated as a concrete category.** The pre-existing tests in `test_docsections.py`
    are no longer *run in isolation* by this AC. They still run: in the full suite whose floor
    AC-6.4 measures, and in the module-scoped Phase-5e run. So the most this AC and its siblings
    may claim about that file is that **its existing tests still collect when the file is collected
    alone and pass in the full suite** — never that it "still passes unchanged", which was never
    true of a file this feature adds a test to. What goes uncovered is exactly one thing: a test in
    that file that passes in the full suite and fails when the file runs alone, an inter-file
    ordering dependency. No AC here pins that, and none claims to.
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
  - AC-2.7: **Two keys whose replacements are not independent refuse rather than resolve by
    order** — one token, two clauses, because two different predicates are wanted and neither
    implies the other. **Clause (i), containment**: any key is a substring of another. **Clause
    (ii), intersecting spans**: any two *distinct* keys have match spans in the block text that
    share a character index. Under either, nothing is executed, the CLI prints
    `DOCBLOCK: SUBST_OVERLAP keys=<n>` with a detail line naming each offending pair, and exits 0.
    **The second clause is added beside the first, never in place of it, because the two are
    independent in both directions**: `ab`/`abc` over a block holding `ab` and no `abc` is refused
    by (i) and not by (ii), the spans never meeting; `ab`/`bc` over `abc` is refused by (ii) and
    not by (i), the map-static check `any(a != b and a in b)` being `False` for that pair.
    Measured on Python 3.11.8 with the prescribed escaped alternation and a recording replacement
    callback: `abc` under `ab→X, bc→Y` yields `Xc` while `text.count` reports `ab=1 bc=1` and the
    callback fired `ab=1 bc=0` — so AC-2.5's "the reported occurrence count equals the number
    replaced" is **false for `bc`**, a wrong count published beside a wrong result, which is
    exactly the silence this AC exists to break. The control `ab bc ab bc` yields `X Y X Y` with
    counts and firings both `2/2`.
    `<n>` is the number of **distinct keys implicated** across both clauses (three keys where one
    contains both others → `keys=3`, two pairs). The detail lines are
    `overlap: "<shorter>" "<longer>"` for clause (i), one per unordered pair, sorted
    lexicographically by `(shorter, longer)`; and `intersect: "<a>" "<b>" "<offset>"` for clause
    (ii), one per unordered pair, the lines sorted by `(offset, a, b)`. **The pair is unordered, so
    its two fields are ordered by a rule and not by discovery**: `<a>` is the lexicographically
    smaller of the two keys and `<b>` the larger, exactly as the containment line puts the shorter
    first. **`<offset>` is the smallest character index the two spans share**, a 0-based index into
    `block.text` — *not* the start of the earlier span, which is a different number: for `ab`/`bc`
    over `abc` the spans are `[0,2)` and `[1,3)`, they share only index `1`, and the line reads
    `intersect: "ab" "bc" "1"`. Both rules are written down because "the first intersecting
    occurrence" on its own admits two readings, and a diagnostic three documents must spell
    identically cannot have two. **The offset is quoted, and that spelling is
    derived rather than chosen**: FR-4's bare-field exemption is a closed list of seven governing
    the *verdict* line only, so a helper-produced number on a *detail* line is quoted like
    `seconds="<n>"`, which is the derivation v1.61 already applied to `pgid`. The intersection scan
    runs on the **original** `block.text` before any replacement — every match span of every key
    collected, two spans from different keys sharing an index being an intersection — so it cannot
    be confused by text a replacement introduced.
    **The class is "two keys' matches are not independent"; containment was one member and span
    intersection is the other. Residual, stated as a concrete category**: a key that intersects
    *itself* (`aa` in `aaa`) is not an intersection between two keys and is not refused —
    measured, `"aaa".count("aa")` is `1` and the regex finds `1` non-overlapping match, so the
    count still equals the number replaced and AC-2.5 holds over it.
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
    `fstat` identity and never unlinks a file it did not create. **That comparison is a
    discriminated guard, not an unpinned policy statement.** A stated non-goal does not exempt an
    implemented deletion guard from the base **Test discrimination** invariant, so the mismatch
    branch is reached through the ninth named injection of AC-5.5's list:
    `test_rollback_skips_unlink_on_identity_mismatch` patches `os.lstat`
    in the helper's namespace to return an `(st_dev, st_ino)` differing from the recorded `fstat`
    identity and patches `os.unlink` to record, then asserts the unlink is **not** called and the
    path is reported as `leftover:`. Removing the comparison alone makes the unlink
    unconditional and that test fail, which is what the mutation is for.
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
  value). **The bare-field exemption is a closed list of seven, and it governs the verdict line
  only**: `rc=<n>`, `blocks=<n>`, `count=<n>`, `keys=<n>`, `shell=`, `stage=` and `reason=` are
  ints or enums the helper itself constrains and stay bare, and that list is exhaustive **in both
  directions** — no other verdict-line field is bare, and none of the seven is quoted. A
  helper-produced *number* that is not on the list is therefore quoted like any other value
  (`seconds="<n>"`): quoting a number never enables a forgery and the grammar parses it either
  way, so membership of the seven, not the value's provenance, decides the spelling.
  **Detail lines are the other half of the grammar and carry no exemption at all**: every detail
  line the helper emits is `<key>: "<value>"`, quoted without exception. The keys as this list was
  written, in v1.63, are `os_error:`, `missing_key:`, `duplicate_key:`, `overlap:`, `intersect:`
  (AC-2.7, the twelfth and newest), `leftover:`,
  `verify:`, `written:`, `failed:`, `skipped:`, `stream:` and `pgid:` (AC-4.6) — the same set the
  helper **will expose** as `DETAIL_KEYS` for AC-4.5's registry walk, which is the authority a
  reader checks the list against rather than this sentence. **That authority does not exist in the
  tree yet, and this sentence says so rather than pointing at a symbol as if it did**: `DETAIL_KEYS`
  is specified in the impl-plan, inside the `Code structure` block of the task that builds
  `h-mad/scripts/h_mad_doc_block_exec.py`, where the tuple carries its own member-count comment;
  it becomes a *runnable* authority only when Phases 5d/5e build that module, and until then
  AC-4.5's walk is a specified test, not a passing one. **Locate it by the assignment, never by the
  name**: the definition is the one place `DETAIL_KEYS` is assigned a tuple of key spellings, and
  the bare name is referenced in this document and in the plan besides, so a name grep does not
  discriminate the definition from a reference. The residual is the self-quoting one this document
  has already paid for twice: a needle spelling the assignment form cannot be published *here*
  without this sentence becoming a second hit for it, which is why the locator is given in words.
  Once 5d/5e land, the assignment moves into the module and the module becomes the authority. A
  field's spelling is thus fixed by **which line it
  sits on**, not by what it is, and a value that moves from the verdict line to a detail line
  changes spelling with it. **Residual, a concrete category**: this rule fixes the spelling of
  every field and detail key this document names, and it does not fix one a later cycle *adds* —
  a new verdict-line field is bare only by being added to the seven named here, and a new detail
  key is quoted by construction with no decision to make; the membership of `DETAIL_KEYS` can grow
  without this list growing, which is a staleness the registry walk catches and this grammar does
  not. **The escaping rule this paragraph opened with** — not the exemption list and not the
  detail-key list — is
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
  - AC-4.2: **The exit-code partition is pinned, and the two AC bodies together are exhaustive over
    the verdict table.** `NOT_FOUND`, `AMBIGUOUS`, `AMBIGUOUS_HEADING`, `BAD_INDEX`, `BAD_TIMEOUT`,
    `BAD_ARGS`, `BAD_SUBST`, `SUBST_MISSING`, `SUBST_OVERLAP`, `BAD_INFO` and `TIMEOUT` each
    exit **0**; `UNREADABLE` (every `reason=`), `CLEANUP_FAILED` and `LAUNCH_FAILED` (every
    `stage=`) each exit **2**. A test
    enumerates the verdict table and asserts the code of every row, so a row cannot move between
    the two classes unnoticed. **Exhaustiveness is the requirement, not the list**: these eleven
    heads plus AC-4.1's `RAN` are every exit-0 head, and the three collapsed heads here — with
    `UNREADABLE` and `LAUNCH_FAILED` each standing for their whole family of `reason=`/`stage=`
    spellings — are every exit-2 head, so nothing the helper can print is outside one of the two
    classes. `BAD_ARGS` is on the list because an argparse grammar error is a *verdict*, not an
    operational error — FR-4's own description already lists it at exit 0 and AC-5.6 spells the
    rendered line — and it was omitted from this AC through v1.61 while three other surfaces
    carried it, which is what an illustrative list does once a reader takes it for an exhaustive
    one. The authority for the head set is the same shape as `DETAIL_KEYS`: the **assignment** of
    `VERDICT_TABLE` to a head→exit-code dict in the impl-plan's `Code structure` block for the CLI
    task, which does not exist in the tree until 5d/5e. **Locate it by the assignment, never by the
    name**: the name alone occurs in this document and in the plan as well, so a name grep does not
    discriminate the definition from a reference — the residual being that this sentence is itself
    one of those references. A head added to that dict without being added here is caught by this
    AC's own enumerating test, not by this sentence.
  - AC-4.3: No cannot-judge line carries `rc=`, so a caller grepping `rc=` cannot read a
    non-measurement as a measured zero.
  - AC-4.4: `AMBIGUOUS` carries `blocks=<n>`; no other cannot-judge carries `blocks=`.
  - AC-4.5: Every detail line the script can emit has a matching remedy row in the Helper-scripts
    registry entry in `h-mad/SKILL.md`, and every row there corresponds to an emittable line
    (pinned bidirectionally by a test).
  - AC-4.6: **The helper's own failures are verdicts too, never tracebacks.** Every exception the
    helper raises on its own behalf at a named stage — **not only `OSError`**, for the reason the
    NUL paragraph below gives — maps to
    `DOCBLOCK: LAUNCH_FAILED stage=<mkdtemp|spawn|reap|collect>` with a detail line carrying the error
    text, exit 2, and the cwd (if one was created) is still cleaned up. The `OSError` members are
    `tempfile.mkdtemp()` failing, `Popen` failing (`bash`
    absent from `PATH`), a `killpg` error other than `ProcessLookupError`, and an `OSError` from
    the helper's own read of the child's pipes (`communicate`), from the post-kill drain, or from
    closing the pipes or waiting on a signalled group (`stage=collect`, after which the child is
    killed and reaped exactly as a timed-out one).
    **A NUL in the payload is a `stage=spawn` member and it is not an `OSError`.** `bash -c`
    receives the composed text as one argv element, and CPython refuses an argv element holding
    U+0000 at the spawn call itself: measured on Python 3.11.8, `Popen(["bash", "-c", "true"])`
    returns rc 0 while `Popen(["bash", "-c", "true\x00"])` raises `ValueError: embedded null
    byte`. Nothing is executed — the spawn never happened — and **no upstream refusal catches it**,
    because `"true\x00"` is *valid UTF-8* and passes the strict decoding AC-3.12 applies to the
    document and to the preamble, so an uncaught `ValueError` would leave the CLI exiting through a
    traceback with no `DOCBLOCK:` line at all. The helper therefore catches `ValueError` at the
    spawn call and raises `LaunchFailed("spawn", err)` — the existing exception, the existing
    token, and the existing stage label, which the alternation above already carries, so **no
    enumeration and no count moves for this member**. Two document-side inputs can carry the byte
    and both are the same member, each with its own test:
    `test_nul_in_document_block_is_a_launch_failure` (the tagged fence's own text) and
    `test_nul_in_preamble_is_a_launch_failure` (the `--preamble-file` contents). A substitution
    *value* composed into the payload is the same member again, reachable through the API's `subs`
    rather than through the CLI, because a NUL cannot survive `execve`'s NUL-terminated argv and so
    cannot reach `--subst` in the first place.
    **The class is "the runtime rejects the argument vector at spawn"; the residual is a concrete
    category, not "and similar"**: `ValueError` is the only exception Python 3.11 raises for a
    `str` argv element it refuses, and the sibling `TypeError` raised for a *non-*`str` element is
    unreachable here because every element of the vector is composed as `str`. Tests: `communicate`
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
    carries `pgid: "<n>"` so the operator can act, and this is the one documented case in which a
    launched process may outlive the call. The spelling is **derived, not chosen**: `pgid` is not
    one of the seven bare verdict-line fields FR-4 closes, and it is emitted on a *detail* line,
    where FR-4's grammar is `<key>: "<value>"` with no exemption — the same shape as this
    verdict's own `os_error:` line.

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
    `PermissionError`-after-`poll()` case — one of exactly **nine** named fault injections this
    suite permits (`os.killpg`, `shutil.rmtree`, `tempfile.mkdtemp`, `os.chmod`, `os.unlink` for
    the reservation rollback's read-back, **`os.lstat` for AC-3.10's rollback identity guard**,
    the module's
    own `_final_write` seam for AC-3.8's post-run write failure, its `_close_stream` seam for
    the backstop close on a path where the final write never ran, and the recorded `Popen`
    instance's own `communicate`/`wait`/`poll` for AC-4.6's `collect` stage and AC-5.5's bounded
    post-kill wait — one instance-level injection, three methods, eight module seams beside it
    through the AC-5.6 recording pass-through, `subprocess.Popen` itself still real; the design's
    Test Strategy bounds the list, and `subprocess` is never mocked). **`os.lstat` is the ninth
    and newest**, and it is here for a reason the other eight state in their own ACs: without it
    AC-3.10's identity comparison is an implemented deletion guard whose mismatch branch no test
    can reach, which the base **Test discrimination** invariant does not exempt merely because the
    scenario it guards against is a stated non-goal.

### FR-6: Migrate the existing inline harness onto the helper

- **Description**: `h-mad/tests/test_h_mad_collect_report_docs.py` hand-writes extraction at
  `:270` and `:412` with `re.findall(r"```bash\n(.*?)```", …)`, and runs the block inline in
  `run_recipe` at `:309`. **The two extractors select different blocks** — measured at `a8e0372`
  and re-run unchanged at `335f535` and again at `74e126f`, with the extractor's own regex over the section the test
  itself bounds:

  ```
  # from the repository root. Deliberately ONE line and outer-single-quoted: a shell
  # continuation inside single quotes is literal, and inside DOUBLE quotes the fence
  # backticks would be command substitution. Copy it whole.
  $ python3.11 -c 'import sys,re; sys.path.insert(0,"h-mad/tests"); import test_h_mad_collect_report_docs as t; b=re.findall(r"```bash\n(.*?)```", t._second_surface(), re.S); print(len(b), [i for i,x in enumerate(b,1) if "h_mad_audit_gate.py" in x], [i for i,x in enumerate(b,1) if "exec codex" in x])'
  7 [4] [2]
  ```

  The Second-surface section holds **seven** bash blocks. **Both extractors select by content
  predicate; the predicate is the load-bearing part and the ordinals below are informational.**
  The two predicates differ in cardinality and are stated separately because they read as one:

  - `_gate_bash_block()` — which `:270` calls — filters the section's blocks on the literal
    `h_mad_audit_gate.py` and **asserts exactly one survives** (`assert len(gating) == 1`), so a
    second gating block is a loud test failure, never a silent wrong pick.
  - `:412` filters on the literal `exec codex` and takes the **first** hit, via `next(…, "")`
    followed by an assert that the result is non-empty. First-hit, not exactly-one: a second
    `exec codex` block would be passed over silently.

  The ordinals — block 4 for the gate recipe, block 2 for the exec dispatch — are 1-based over the
  extractor's own `re.findall(r"```bash\n(.*?)```", …)` applied to `_second_surface()`, which is
  the base they are meaningful against and outside which they mean nothing. They are cited as
  evidence that the section's shape has been stable, never as a selector any code reads.

  **The predicates split by era at FR-6.** `:270` stops using a content predicate entirely: after
  migration it addresses its block by heading plus the `hmad:exec` tag through
  `h_mad_doc_block_exec`, so `h_mad_audit_gate.py`-as-selector is retired at that consumer and only
  the tag and heading remain load-bearing there. `:412` keeps its content predicate permanently,
  because it must inspect a block that is deliberately untagged. Any document attributing FR-6's
  selection must attribute a predicate and an era, not an ordinal.

  The total was written as
  four in an earlier draft; running the same extraction over `git show <sha>:h-mad/SKILL.md` at the
  three points gives `6db8e50^` → 4 blocks / 1 `##` heading in the section, `6db8e50` → 7 blocks /
  2 headings, `a8e0372` → 7 blocks / 2 headings. So the drift is one commit's, `6db8e50`, which
  inserted a `##` heading between the two string anchors `_second_surface()` bounds on and widened
  the section; the gate block reads 4 and the exec-codex block 2 at **all three** shas (and at
  `335f535` and `74e126f`), because the arrivals land after block 4. That stability is why the ordinal looked
  safe enough to lean on, and is exactly why it is demoted here: an ordinal that has held is still
  an ordinal, and one insertion before block 4 would move it without moving the predicate.
  Only `:270`'s block is tagged, so only `:270` breaks when the tag lands, and only
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
    writes by hand. **Documents that attribute this membership rule address it by AC label anchored
    to the start of its own body line** — `grep -cE '^  - AC-6\.4:'` against this file → `1` at
    `74e126f` — never by a bare `AC-6.4`, which §Version History cites many times over. Every AC
    body anchor in this document is unique by the same form: at `74e126f`,
    `grep -oE '^  - AC-[0-9]+\.[0-9]+:' | sort | uniq -c | awk '$1>1'` prints nothing over 49
    anchors (`grep -cE '^  - AC-[0-9]+\.[0-9]+:'` → `49`). Residual: the anchor pins the AC, not
    the sub-clause inside it, so an attributing document that means the two-item list specifically
    must say so in words; and the anchor breaks if the AC list's two-space indentation changes,
    which is a whole-document reformat and would be visible in review, not silent.
      1. Nodes added directly to a consumer file — the wire and exemption tests in
         `test_h_mad_collect_report_docs.py` and the delegation spy test in `test_docsections.py`.
      2. **One node per glob-parametrised test, per new file this feature adds under
         `h-mad/scripts/`.** `test_h_mad_portable_timeout.py` globs `(SKILL / "scripts").glob("*.py")`
         into `_SCANNED` and parametrises over it twice — verified at `a8e0372`, re-run unchanged
         at `335f535` and again at `74e126f`, with
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
      `a8e0372` and re-run unchanged at `335f535` and `74e126f` that the two other `*.py` globs in the suite are
      of that second kind —
      `git grep -n 'glob("\*\.py")' -- 'h-mad/tests/*.py'` returns three hits, `_SCANNED` itself
      plus `test_h_mad_collect_report.py:287`, which loops but filters to two named writer modules
      so a new script is skipped, and `test_hmad_dispatch_audit_cycle.py:250`, which globs a
      `tmp_path` fixture directory rather than the real one.
    Every other new test, the collect-alone pins included, lives in the new module.
    `test_suite_floor_holds` asserts `full_collected >= 2748 + new_module + len(tuple)`
    from a `--collect-only` subprocess (collection never executes tests, so the suite does not
    recurse into itself; an env guard `DOCBLOCK_FLOOR_INNER=1` makes any inner instance skip, as a
    belt beside those braces). The *pass* half cannot live inside the suite it measures: it is the
    Phase-5f gate command, `( cd "$(git rev-parse --show-toplevel)" && hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider ) > /tmp/doc_block_exec_suite.log; RC=$?   # from the REPOSITORY ROOT: the 2748 baseline is a ROOT count and a run from h-mad/ collects strictly fewer, so a floor read there is not comparable; tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"   # bounded through the reachable dispatcher (base Portable time bounds); rc=124 is the wrapper's expiry, not a suite result`, run alone by the orchestrator and recorded in the report:
    the last line must read `N passed` with no failures **and** `SUITE: rc=0` — the exit status is
    captured before `tail`, because a bare pipe reports `tail`'s status and lets a red suite print
    as success.
    **Why that comment names no second number, stated as a rule rather than as this one repair.**
    Through v1.61 it carried `from h-mad/ the same command collects 2486`. That figure was
    superseded — at `fbc2ea0` the two collections are **2814** from the repository root and
    **2552** from `h-mad/`, each measured in its **own** shell invocation of
    `python3.11 -m pytest --collect-only -q -p no:cacheprovider` (a `cd h-mad` chained into the
    same invocation persists and makes both "controls" read the same tree, which is how the pair
    was mis-measured once already). Both are `+66` on the retired `2748`/`2486` pair, which the
    impl-plan publishes and the plan retires. The rule that closes the class: **a comment embedded
    in a command may name a constant that is stamped elsewhere in this document — `2748` is, at the
    AC body above, with its sha `e8eaf6f` and its re-measure-at-5c rule — and may never carry a
    fresh measurement of its own**, because a comment inside a command string is the one surface a
    value sweep of this document has already missed twice. `2809`/`2547` are stated here, in prose,
    with the command and the sha; they are a *scale* for the root-versus-`h-mad/` gap, not a floor,
    and the floor remains `2748` until 5c re-measures it.
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

- Any blanket or directory-wide sweep of bash fences. The corpus such a sweep would have to face —
  column-0 ` ```bash ` openers in tracked `*.md` under `h-mad/` and `handoff/` — is **73 openers**,
  measured over the tracked tree at `74e126f`:

  ```
  $ git grep -c '^```bash' -- 'h-mad/*.md' 'handoff/*.md' ':!*/archive/*' | awk -F: '{s+=$NF} END {print s}'   # -> 73  (at 74e126f; also 73 at 335f535)
  $ git ls-files 'h-mad/*' 'handoff/*' | grep -c archive                                                       # -> 0   (at 74e126f; also 0 at 335f535)
  ```

  This feature executes only tagged fences and adds exactly one tag. The `archive/` exclusion
  selects nothing at this sha — the second command is why that is stated rather than assumed — and
  it is kept so the corpus cannot silently widen when an archive lands. Residual, two categories.
  (1) This is a column-0 `git grep`, not FR-1's CommonMark scanner: openers legally indented by one
  to three spaces are outside it and are neither counted nor classified here. (2) It differs from
  AC-6.1's guard in **both** corpus and quantity, deliberately: this one is `git grep` over the
  tracked tree, AC-6.1's is a filesystem walk that must also catch a document written and not yet
  committed; and this one counts **all** ` ```bash ` openers (73) while AC-6.1 counts only the
  **tagged** ones and asserts exactly 1. Neither number checks the other, and a later attempt to
  reconcile them would break AC-6.1's purpose. This 73 was 68 at `e58ef3a` under the same command.
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
  CommonMark reference port agrees, and **the environment that reading was taken in is a committed
  file rather than a description** — which is the repair, not the adjective. The runnable surface is
  `/opt/anaconda3/bin/python3.11 docs/03-analysis/probes/doc-block-exec/grammar_corpus.2026-09-03.cd979362.py`,
  committed at `fbc2ea0`, which builds `markdown_it.MarkdownIt("commonmark")` and whose **fourteen
  printed lines** all read `OK` there. Re-run through that interpreter, the two facts above hold:
  `<code class="language-bash">` for the tagged fence, and the tilde-quoted tag rendered as body.
  **What the probe supplies here is the *interpreter*, not the cases, and the boundary is stated so
  the citation is read at its true width**: neither of those two facts is among its fourteen lines.
  The nearest line to the first renders ` ```bash ` with a bare info string, so it exercises the
  language class but never a *trailing* info-string word such as `hmad:exec`; the nearest to the
  second puts a tilde run *inside* a backtick fence, which is the reverse of a tilde fence quoting
  a backtick one. Both facts are therefore measured by this section, through the probe's
  interpreter, and are reproducible for that reason rather than because a probe line asserts them.
  **The version gap is published rather than papered over, and it is why the old wording was the
  defect.** Through v1.63 this sentence cited `markdown-it-py 4.2.0` in a disposable virtualenv
  that was never recorded — an environment a reader cannot reconstruct. The probe's interpreter carries **2.2.0**
  (`/opt/anaconda3/bin/python3.11 -c 'import markdown_it; print(markdown_it.__version__)'`), and
  `4.2.0` is not reachable here at all: of the interpreters this repository's tooling reaches,
  `/opt/anaconda3/bin/python3` and `/opt/anaconda3/bin/python3.11` import the module at `2.2.0`
  while `/usr/bin/python3` and `/opt/homebrew/bin/python3` do not have it. So rather than swap one
  version for another, **both readings are kept**: the original at `4.2.0` and a re-measurement at
  `2.2.0` that agrees on every claim this document draws from that renderer. Two major versions
  agreeing is a stronger warrant than either alone, which is the reason to keep the historical one
  rather than delete it. Residual, a concrete category: a claim that ever *disagrees* between the
  two must name the version it was taken at and stop being carried by the other; none does today,
  and the check is re-running the three cited claims through the probe's interpreter, not trusting
  this sentence. The
  Claude Code viewer has no headless renderer to probe; it is a CommonMark viewer and the one-line
  exposure is reversible, so it is confirmed by eye at Phase 5 after the tag lands.
- The two extractors named in FR-6 are the only in-repo consumers that anchor on a bare
  ` ```bash\n ` opener in a file this feature tags. **Measured over the tracked tree at `a8e0372`
  and re-run unchanged at `335f535` and `74e126f`** (`-E`, because git's default regex is not GNU BRE and `\|` is
  not portable here):

  ```
  $ git grep -n -E 'findall.*```bash|split.*```bash|re\.compile.*```bash' -- '*.py'
  h-mad/tests/test_h_mad_collect_report_docs.py:270:    blocks = re.findall(r"```bash\n(.*?)```", section, re.S)
  h-mad/tests/test_h_mad_collect_report_docs.py:412:        (b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b),
  ```

  A broader sweep for the bare literal, over the **tracked** tree so no gitignored or
  not-yet-committed artifact contaminates it, returns six hits at `a8e0372` and still six at
  `335f535`, at `74e126f` and at `dfae038` — and **eight hits** at `fbc2ea0`, this revision's
  freeze sha. **The freeze-sha closure below does not carry this census any more, and that is the
  finding, not a footnote**: the commit that committed this feature's own measurement probes added
  tracked `.py` files under `docs/03-analysis/probes/doc-block-exec/`, and this census's corpus is
  the whole tracked tree rather than `h-mad/` and `handoff/`, so a closure predicate scoped to
  `docs/` cannot certify it. It is re-executed at the freeze rather than inferred, and the two
  arrivals are rows of a probe fixture table, not extractors, so the census's conclusion is
  untouched. It is printed with `-n` and **without** `| wc -l`, so
  every location below is output the command as written gives back, not a pin retyped into prose —
  which is the form the round-seven predicate ruling asks for, and the reason this block replaced
  the counting form: a reader re-running a `| wc -l` census gets `6` and no locations, so the pins
  that used to sit in the prose underneath it could not be reproduced without editing the command.

  ```
  $ git grep -n '```bash' -- '*.py'
  docs/03-analysis/probes/doc-block-exec/grammar_corpus.2026-09-03.cd979362.py:5: ("opener at 3 spaces IS a fence",            "   ```bash\nX\n```\n",                      "code",   "<code"),
  docs/03-analysis/probes/doc-block-exec/grammar_corpus.2026-09-03.cd979362.py:6: ("opener at 4 spaces is NOT a fence",        "    ```bash\nX\n",                          "indented-code", "<pre><code>```bash"),
  h-mad/scripts/h_mad_precheck_doc.py:100:# "the section holds four ```bash fences, opening at `:1809`, `:1822` …" — and a
  h-mad/tests/test_docsections.py:27:```bash
  h-mad/tests/test_h_mad_assemble_tdd.py:489:```bash
  h-mad/tests/test_h_mad_assemble_tdd.py:551:        plan = "# P\n\n## Task 1: x\n\n```bash\necho hi\n\n## Version History\n\n- v1.0\n"
  h-mad/tests/test_h_mad_collect_report_docs.py:270:    blocks = re.findall(r"```bash\n(.*?)```", section, re.S)
  h-mad/tests/test_h_mad_collect_report_docs.py:412:        (b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b),
  ```

  **Eight** hits at `fbc2ea0`; the unit is matching lines, one match to a line. The last two hits
  are the narrow census's two extractors. The other six hits are not extractors: three are fixture
  literals, one is a comment quoting the literal inside a worked example, two are rows of a probe's
  fixture table, and each is identifiable as such from
  its own printed line above. This paragraph re-quotes **no** `path:line` from that block — the
  output is the locator, which is what makes these four self-repairing under a re-run rather than
  under a reader hunting a moved line. One fact the output does not carry is given as a command
  rather than as a pin: the `test_docsections.py` hit sits inside a **module-level** string
  constant, `grep -c '^FIXTURE = ' h-mad/tests/test_docsections.py` → `1`, and there is **no**
  enclosing test function to name — `grep -n '^def ' h-mad/tests/test_docsections.py | head -1`
  returns a `def` *below* that hit, not above it, so the file's first function begins after the
  fixture. That is why the reproduced-output form was taken here and not the enclosing-symbol form
  the ruling offers as its first option; the first option is unavailable for this member.
  Control that the narrow pattern is not under-matching:

  ```
  $ git grep -l '```' -- '*.py' | wc -l              # -> 24  (at a8e0372, re-run -> 24 at 335f535, 24 at 74e126f, 24 at dfae038, 25 at fbc2ea0)
  ```

  Twenty-four tracked `.py` files contain a fence literal at `74e126f`, and **twenty-five files**
  do at `fbc2ea0`; exactly two of them extract on a
  bare ` ```bash ` opener, which is the census's conclusion and the part that matters. The total
  itself has now moved three times (21 → 23 → 24 → 25) without that conclusion changing, because
  every arrival was a fixture, a comment or a probe and none was an extractor. One further consumer reads `SKILL.md` and was
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

  **Freeze-sha closure for this revision — and this revision is where the blanket form failed.**
  Through v1.62 this paragraph asserted that every *tree*-derived figure stamped `74e126f` is
  identical at the freeze sha because every intervening commit touches only `docs/`. **That
  predicate is false at `fbc2ea0`**, and the measurement that killed it is published here rather
  than the sentence quietly replaced:

  ```
  $ git diff --name-only 74e126f fbc2ea0 | grep -vc '^docs/'    # -> 2  (at fbc2ea0; it was 0 at dfae038)
  $ git diff --name-only 74e126f fbc2ea0 -- '*.py' | wc -l      # -> 6  (at fbc2ea0; the same command printed nothing at dfae038)
  ```

  The accounting, member by member, because a broken closure is replaced by an enumeration and not
  by a weaker sentence. The **two files** outside `docs/` are `h-mad/scripts/h_mad_assemble_audit.py`
  and its test: their *content* changed and their *membership* in every census here did not, both
  having been members already at `74e126f`. The **six files** the `*.py` scope prints are those two
  plus four new ones under `docs/03-analysis/probes/doc-block-exec/` — which are `docs/` paths, so
  the first command cannot see them, and are `*.py` files, so a `*.py` census sees them all.
  **That is the class**: a corpus predicate scoped to a *directory* cannot certify a census scoped
  to a *file type*, and a freeze that touches no document is not a freeze that touches no
  measurement. Two published figures moved because of it and both are corrected above: the
  bare-literal sweep is `8` at `fbc2ea0` where it was `6`, and the fence-literal file census is
  `25` where it was `24`. Residual, a concrete category rather than "and similar": this repair
  fixes the two `*.py` censuses named here and does not fix a future census whose corpus is wider
  still — such a census joins this paragraph by naming its own corpus in the same clause as its
  command, which is the rule stated above for every tree-derived count.

  Every other tree-derived figure was **re-executed at `fbc2ea0`** rather than inferred, and each
  returned the value printed beside it: the narrow extractor census's two hits, the `73` openers of
  §Out-of-Scope with its archive-exclusion `0`, AC-1.7's `16` headings and `2` duplicates, the
  `_SCANNED` parametrise-twice `2`, the three `*.py` globs, and the `^FIXTURE = ` constant's `1`.

  `fbc2ea0` is HEAD, and this document's working bytes were identical to it before this revision's
  first edit — `git diff --stat fbc2ea0 -- "$S"` empty — so the *committed* half of every published
  pair below moves from the v1.61 bytes at `dfae038` to the v1.62 bytes at `fbc2ea0`, and equals
  what v1.62 published as its *draft* half. The freeze sha is defined below as **the last commit**,
  which is not the same thing as the last commit that touched this file. That distinction is why
  v1.61's Version History entry named `b3be433` — a commit that never touched this file — while
  this paragraph still named `6f0ee85`, two revisions behind it: one revision, two freeze shas,
  neither of them HEAD. The rule that closes it: this paragraph and the entry both take the sha
  `git rev-parse --short HEAD` returns while the revision is being drafted, and the entry quotes
  this paragraph's sha rather than deriving its own.

  Nothing above covers figures measured over *this file*, which is one of the `docs/` paths that
  moved — `git log --oneline 74e126f..fbc2ea0 -- "$S"` lists `0aac0b7`, `6f0ee85`, `8909ec4`,
  `00b961f`, `59cc2ad` and `7b182b0`, so this file changed in six of them. That is two more than
  the four v1.62 published over its own shorter range, and the two arrivals are the commits that
  shipped v1.62 itself — the same under-reporting-its-own-churn shape v1.62 recorded when it
  corrected `two` to `four`, recurring one round later for the same reason: the range's right end
  moves every round and the count is a function of it, not a constant beside it.

  **Two shas, and a doc-scoped figure must carry the right one — the failure v1.59 shipped.**
  `fbc2ea0` is the freeze sha: the last commit, and the tree every *tree*-derived figure here is
  taken over. A figure measured over *this file* is **not** taken over that tree. It is taken over
  the **draft in hand**, which lands in the commit *after* the freeze sha, so the two can disagree
  and did: v1.59's opener census published the distribution its own draft had while carrying the
  stamp of the revision before it, and the audited value and the published value differed by more
  than a factor of two. The rule that closes the class, not the instance: **a doc-scoped figure is
  published as a pair** — `git show fbc2ea0:"$S" | <command>` for the committed value and
  `<command> "$S"` for the v1.63 draft — collapsed to one number only where the two agree and
  written as both where they do not. Every doc-scoped figure below is stated that way. **The
  committed half moves with the freeze sha**, which is the maintenance this rule costs and the
  half v1.61 did not pay: v1.61 restamped every *draft* half from "the v1.60 draft" to "the v1.61
  draft" and left every *committed* half at `6f0ee85`, so the pairs it published straddled two
  freezes. Each committed half below is re-measured at `fbc2ea0`, and a `6f0ee85` value is kept
  only where it is labelled as history — the census progression and the `no`-token scale — never
  as this revision's committed half. The residual
  is that the draft half cannot be re-run by a reader after this revision lands, because "the
  draft" becomes a commit; a reader re-runs it as `git show <the commit shipping v1.62>:"$S"`, and
  a figure that has drifted since then is a real drift, not a mis-stamp.

  `$S` throughout this section is the shell variable bound in the control block below to this
  document's path. Every command here that names it must be run with that binding: an unbound `$S`
  makes `grep -c` print `0` on stdout while the error goes to stderr, which is the null-read-as-
  absence failure this whole rule exists to prevent.

  **How the members are found — an enumeration, because a value sweep cannot find them all.** The
  v1.56 pass swept the values it was *changing*, and §Out-of-Scope's fence count survived it into
  v1.57 for a structural reason worth stating, and verified rather than assumed: `git log -S'There
  are 68' -- docs/01-plan/features/doc-block-exec.spec.md` returns exactly one commit, `e58ef3a`,
  so the number was written once and never edited; and §Out-of-Scope's command re-run at that same
  sha gives 68, and at `335f535` and `74e126f` gives 73. Same command, same corpus, different tree — it drifted in
  place while the tree moved under it. No sweep keyed on a *changed* value can reach a number that
  never changed, and it sat in a non-normative section a walk of the FR/AC bodies never visits. The
  rule therefore carries its own enumeration, run over the whole document body, keyed on shape
  rather than on what changed:

  ```
  $ awk '/^## Version History/{exit} {print FILENAME":"NR": "$0}' docs/01-plan/features/doc-block-exec.spec.md | grep -Ei 'measured|census|(\*\*)?([0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|(thir|four|fif|six|seven|eigh|nine)teen|(twen|thir|for|fif|six|seven|eigh|nine)ty(-(one|two|three|four|five|six|seven|eight|nine))?)(\*\*)? ([^ ]+ ){0,3}(\*\*)?(blocks?|headings?|hits?|files?|fences?|openers?|nodes?|seams?|consumers?|lines?|pins?)'
  ```

  It covers every section, normative or not, and stops at the Version History boundary because
  residual (1) exempts that region.

  **This enumeration is the single checker for this class rule, and the other documents of this
  feature attribute to it rather than re-word it — so it needs a stable address.** The address is
  the fenced block immediately above, and the needle is **line-anchored**, not a prose phrase:
  `grep -cE '^  \$ awk ' docs/01-plan/features/doc-block-exec.spec.md` → `1` at `74e126f`, `1` at
  `fbc2ea0` and `1` over the v1.63 draft, which is where uniqueness has to be checked because a
  sibling edit in the same commit can break it. The
  anchoring is the whole point. A plain-substring needle on the awk program itself was tried first
  and measured at `2` in this file at `74e126f`, because the sentence publishing the needle
  reproduced it — the same duplication a later §Version History entry would cause. The anchored
  form is immune: prose references sit mid-line, so quoting the needle cannot add a hit. Three
  residuals, all concrete. (1) It is **file-scoped**; an attributing document must grep this path,
  never the tree, and must not assume the same needle is unique in a sibling document. (2) A second
  fenced block in this file opening a line with two spaces and `$ awk ` would make it `2`. That is
  a specific and checkable risk, not a vague one, and it **materialised while v1.59 was being
  drafted**: the `path:line` shape grep added below was first written as an `awk` one-liner,
  which took the needle to `2` and, because the control block further down extracts its pattern
  through that same needle, silently broke the control as well. It was rewritten to open with `sed`
  for that reason alone. The slot census is published as a pair under the two-sha
  rule above, because it moved between the two trees and v1.59 published only the later value under
  the earlier stamp. Both halves from
  `grep -oE '^  \$ [a-zA-Z0-9._-]+' | sort | uniq -c`, run over `git show 35698f9:"$S"`,
  `git show 6f0ee85:"$S"`, `git show fbc2ea0:"$S"` and the draft respectively. **Two of those four
  are history and two are this revision's pair**, and they are labelled so that a later reviser
  cannot mistake a historical anchor for a committed half. History: at `35698f9`, **9 openers**
  over 5 distinct tokens — `awk` ×1, `curl` ×1, `git` ×5, `printf` ×1, `python3.11` ×1; at
  `6f0ee85`, the commit that shipped v1.59, **20 openers** over 11 distinct tokens — `awk` ×1,
  `curl` ×1, `git` ×7, `pairs` ×1, `printf` ×2, `python3.11` ×1, `RULE` ×1, `S` ×1, `sed` ×1,
  `split_only` ×3, `while` ×1. The pair, collapsed because the two halves agree: **21 openers**
  over 11 distinct tokens at `fbc2ea0` and the same over the v1.63 draft. The one change from
  `6f0ee85` to `dfae038` is `sed` ×2, which v1.60 introduced by adding a second `sed` command to
  the `path:line` shape-grep block
  below. The same command answers differently over each of those trees, and the pair rule is why
  that is visible here instead of arriving as a silent restamp. The unit is *occurrences of a
  line-opening command token*, and the distinct-token figure beside each is the second unit the
  same command yields; neither is a count of fenced blocks. v1.59 wrote the bare integer `20`
  beside the wrong sha, which is decision H and decision D failing together.
  `awk` is the sole holder of its slot at all three, so the conclusion the needle rests on survived
  both moves: a new `awk` command in a fence is still the one edit that breaks the needle. The
  census moved twice and the conclusion never did, which is why they are stated separately. (3) The needle pins the block, not any clause inside it; a
  document meaning the alternation specifically must say so in words.

  **It has been executed against controls, because a screen that never fires reads exactly like a
  clean document.** That is not hypothetical: a sibling screen for this same class shipped with
  `\btoday\b` inside an `awk` program, where `\b` is a backspace escape and not a word boundary,
  so that term matched nothing and its published before/after counts came from a screen blind to
  one of its own forms. **A positive control and a true negative control, both run at `fbc2ea0`
  and re-run over the v1.63 draft, against the form this revision ships.** **Eight** of the nine
  strings are present at `fbc2ea0` and return identical verdicts at both halves of the pair. The
  ninth is the sixth positive, and its "no committed half" caveat — discharged in v1.62 by moving
  the committed half to `dfae038`, where that string then existed — **returns in v1.63 for a
  different reason and is stated rather than hidden**: this revision's census repair moved both
  figures inside that string — the line total and the output half of its split — so the string as
  it now stands is new text and returns `0` at `fbc2ea0`. **It is described here and deliberately
  not reproduced**, because a paragraph that quotes a control string takes that string's own
  verbatimness count to `2`; that is not hypothetical, it is what the first draft of this sentence
  did and what the check below caught. The class is *a control string that quotes a figure this
  document publishes*:
  it loses its committed half in exactly the revision that moves the figure, and it regains one in
  the next. The residual is that a control quoting a figure can never be checked at both halves in
  the revision that changes it; the draft half is the one under test there, and the verdict below
  is what makes it admissible. A true negative is a *non-member the screen declines*; a
  member it fails to print is a false negative and is reported separately below, never as "the
  negative". The pattern is **not retyped** — it is extracted from the published block above by its
  own anchored needle, so a control cannot silently drift from the checker it tests, and an empty
  `$RULE` fails loud by turning every negative into a `MATCH`. Every one of the nine strings is a
  **verbatim substring of this document's body**, not a paraphrase of one — a paraphrased control
  proves only that the author can write a matching sentence:

  ```
  $ S=docs/01-plan/features/doc-block-exec.spec.md
  $ RULE=$(grep -E '^  \$ awk ' "$S" | sed "s/.*grep -Ei '//; s/'\$//")
  $ while IFS= read -r s; do printf '%s\n' "$s" | grep -qEi "$RULE" && v=MATCH || v='NO MATCH'; printf '%-58s %s\n' "$s" "$v"; done <<'EOF'
  is **73 openers**,
  The Second-surface section holds **seven** bash blocks.
  16 headings, 2 of them
  returns six hits at `a8e0372` and still six at
  Twenty-four tracked `.py` files contain a fence literal
  The split of the 13 lines is 10 + 3
  A block's declared shell mode is a property of the recipe
  the tag cannot repair an ambiguous *section* selector
  and exits 0 — a refusal is a verdict (FR-4).
  EOF
  is **73 openers**,                                         MATCH
  The Second-surface section holds **seven** bash blocks.    MATCH
  16 headings, 2 of them                                     MATCH
  returns six hits at `a8e0372` and still six at             MATCH
  Twenty-four tracked `.py` files contain a fence literal    MATCH
  The split of the 13 lines is 10 + 3                        MATCH
  A block's declared shell mode is a property of the recipe  NO MATCH
  the tag cannot repair an ambiguous *section* selector      NO MATCH
  and exits 0 — a refusal is a verdict (FR-4).               NO MATCH
  ```

  Six positives, each a verbatim member of this document, all printed. The sixth is new in v1.60
  and is the control on **v1.60's** widening of the closing noun alternation: under the v1.59
  form it was `NO MATCH`, because `lines` was not a counted noun the screen knew. Three true
  negatives, each
  a verbatim sentence fragment of this document that states no count the rule governs, all
  declined — and the third is the sharp one, because it carries a digit (`0`) and is declined on
  the *noun*, which is the only boundary the screen enforces on its right-hand side. Verbatimness
  is itself checked rather than asserted: deleting this fenced block from a copy and running
  `grep -cF` for each string returns `1` for **eight** of the nine at `fbc2ea0` — the sixth
  positive returning `0` there for the reason above — and `1` for all nine
  over the v1.63 draft —
  `sed '/^## Version History/,$d' "$S" | sed '/^  \$ S=docs/,/^  [^A-Za-z ]\{3\}$/d' > /tmp/nobody.md`,
  then `grep -cF "$s" /tmp/nobody.md`. **The Version History is cut first, and that is a v1.60
  repair, not decoration.** The claim under test is that each string is a verbatim substring of
  this document's *body*; a later §Version History entry quoting a control string makes the count
  `2` and turns a passing check red for a reason that is not a defect. That is not hypothetical —
  it happened while **v1.60** was drafted, when the v1.60 entry quoted the sixth positive and
  took its count to `2`. Cutting the region residual (1) already exempts from the enumeration makes
  the check agree with its own subject and closes the class for every future entry, rather than
  forbidding entries from quoting strings. The closing address is written as three non-letter
  characters rather than the fence literal so that publishing it here cannot close the code span it
  sits in; its residual is that it would also stop at any other three-character non-letter line
  inside the block, of which there is none.
  None of the nine contains `measured` or `census`, so none is matched by the screen's two
  free-standing alternatives — every verdict above exercises the cardinal-and-noun half, which is
  the half under test. The fifth positive was `NO MATCH` under the `([a-z]+ )?` form this document
  shipped through v1.57, which is how the gap defect was found: by executing the screen, not by
  comparing it to a weaker alternative.

  **Two blind forms, found rather than assumed, because "0 false negatives" from an unprobed screen
  is not a measurement.** (i) One genuine false negative: the sentence stating that
  `h-mad/invariants.example.md` *holds no fences at all* is a tree-derived zero carrying its own
  command and sha, and the screen declines it, because the quantifier `no` is not a cardinal in the
  alternation. Its locator is **line-anchored for the same reason the `awk` needle is**, and its
  pattern carries no backtick so that quoting it here cannot break the code span:
  `grep -cE '^ +.74e126f.\. That file holds' "$S"` → `1` at `fbc2ea0` and `1` over the draft. The
  unanchored needle `holds no fences at all` returns `3` here, because this paragraph reproduces it
  twice more — once describing the sentence, once publishing the needle. An author who publishes a
  prose needle manufactures its own duplicates; anchoring is the only defence, because a prose copy
  sits mid-line.
  (ii) One shape demonstration that is *not* a missed member: AC-1.2's `extraction yields zero` /
  `blocks` is design-derived and therefore outside this rule by the second exclusion below, but it
  exhibits both blind shapes at once — `zero` absent from the alternation, and the counted noun on
  the following line (anchored locator `grep -cE '^  - AC-1\.2:.*yields zero$' "$S"` → `1` at
  `fbc2ea0` and `1` over the draft). Both are recorded as residuals (2) and (3) below rather than
  patched, and the reason is stated there.

  **The line-split class was probed systematically, not by the one instance that happened to be
  noticed.** `grep` is line-scoped and this document hard-wraps at ~95 columns, so any cardinal
  ending a line with its noun beginning the next scores `0`. The probe joins each adjacent line
  pair, applies the same extracted `$RULE`, and prints only pairs where *neither* line matches
  alone. It is published with a positive control first, because a probe that cannot fire reads
  exactly like a document with nothing to find:

  ```
  $ pairs() { awk '/^## Version History/{exit} NR>1{print (NR-1)"+"NR": "prev" "$0} {prev=$0}' "$1"; }
  $ split_only() { pairs "$1" | grep -Ei "$RULE" | while IFS= read -r j; do n=${j%%:*}; a=${n%%+*}; b=${n##*+}; sed -n "${a}p;${b}p" "$1" | grep -qEi "$RULE" || printf '%s\n' "$j"; done; }
  $ printf 'a sentence ending in **seven**\ntagged openers\n## Version History\n' > /tmp/split_fixture.md
  $ split_only /tmp/split_fixture.md
  1+2: a sentence ending in **seven** tagged openers
  $ split_only "$S"
  ```

  The probe fires on the synthetic split and returns **nothing** on this document, at `fbc2ea0` and
  again over the v1.63 draft after every edit this revision makes: no
  member of this rule is currently split across a wrap. That null is admissible only because the
  positive control immediately above it is non-empty — an unproven probe's zero would be
  indistinguishable from a dead one. The probe inherits every residual of `$RULE` itself, so AC-1.2's
  `zero` / `blocks` pair is invisible to it too — it is a two-line window over the same alternation,
  not a wider screen.

  The fifth positive is why the gap between the cardinal and the counted noun is now
  `([^ ]+ ){0,3}` and was `([a-z]+ )?` through v1.57: one optional *lowercase* word cannot span
  `tracked` **and** the backticked `` `.py` ``, so the enumeration was blind to a member sitting
  in the very paragraph that defines it. Widening recovers three members, **named rather than
  counted** because the totals of both forms move on every edit to this document: the
  `Twenty-four tracked .py files` sentence here, and the two FR-6 sentences stating the gate
  ordinal 4 and the insertion-before-block-4 hazard. It also admits two lines that state no
  tree-derived count — AC-1.9's `one — a wrong block` and FR-3's `8 with errors="replace"` — and
  those are the correct trade: this enumeration is read by a human, so an extra line costs a
  glance and a miss costs a cycle. Re-verified at `fbc2ea0` and over the draft, and one correction to
  how it is read: a reader who diffs the two forms mechanically sees **more lines than members**,
  because the excess is this document quoting itself — the control block above reproduces the
  `Twenty-four tracked .py files` string twice, once as input and once as output, and this
  paragraph reproduces it and names the other four. The five named above are the members; the
  difference between the two forms is not a member count.

  **The cardinal alternation is deliberate**: this document states
  most of its counts as words — `**seven** bash blocks`, `Twenty-four tracked .py files`, `six
  hits` — so a digits-only enumeration would miss the majority of its own members, and a
  `grep -E '[0-9]'` fallback would miss them too. Residual on the enumeration itself, three
  concrete categories. (1) A counted noun outside the closing alternation — the axis is *countable
  things this feature measures*, in the tree or in this document, and the list is the finite set the
  document currently uses; a new noun must be added when it arrives, which is the enumeration's own
  maintenance cost and is accepted. **Two arrived in v1.60 and were added rather than recorded as a
  gap**: `lines?` and `pins?`, because **v1.60's** `path:line` figures are stated in exactly
  those units and the v1.59 alternation was blind to all of them. The trade is **reproducible rather
  than published as a number**, for the same reason the enumeration's own hit count is not stated:
  this paragraph is itself a member of both forms, so any figure written here inflates itself by
  the act of writing it and goes stale on the next edit. Re-run it — extract `$RULE` by the
  anchored needle, build the v1.59 form by deleting `|lines?|pins?` from it, and diff the two
  screens over this body. What the widening recovers, **named rather than counted**: the two
  sentences stating the three units for the `path:line` class, the sentence stating how those lines
  split, and the sentence naming the load-bearing pins. What it costs, named by *shape* rather than
  by tally: ordinary prose uses of `one … line`, `two things this pins` and `raw lines` — one
  bounded, readable class, and the accepted false-positive cost of a screen a human reads. Still
  outside and still accepted: nouns this feature does not yet count, of which `commits`, `tokens`
  and `values` are the concrete ones this document uses in passing without measuring.
  **A second, distinct sub-class arrived in v1.61 and v1.62 and is named rather than left implicit**:
  `fields` and `heads` — "a closed list of seven" in FR-4 and "the seven bare verdict-line fields"
  in AC-4.6, "these eleven heads" in AC-4.2 — *are* counted, so they do not belong on the
  un-measured list above; they sit
  outside the alternation under **exclusion (2)** instead, because both are counts of a helper that
  does not exist until 5d/5e and both move only when the design moves. The rule over the axis, so
  the next one does not need a ruling: a counted noun is added to the alternation when its count
  becomes **tree-derived**, and is named here under exclusion (2) while it is still design-derived.
  (2) A quantity written in a word form the opening alternation does not list. The
  axis is *word forms that stand where a cardinal stands*, and exactly three concrete categories sit
  outside it: `zero`; the bare quantifiers `no` and `none`; and cardinals of one hundred or more,
  which the alternation stops below. This is measured, not assumed — the `no` category has a live
  member in this document, blind form (i) above. It is left open deliberately, and the trade is
  measured rather than asserted: `no` is overwhelmingly an ordinary negation here (`no file` in
  AC-3.2, `no API` in §Non-Functional Requirements, `no node` in FR-6), and
  `awk '/^## Version History/{exit}{print}' "$S" | grep -oEi '\bno\b' | wc -l` → `89` at
  `fbc2ea0` and `101` over the v1.63 draft — the unit is *occurrences of the token*, not lines
  and not distinct sentences. The figure has risen every revision because each one adds prose that
  states exclusions in negatives: it was `75` at `6f0ee85` and `85` at `dfae038` (history, not this revision's committed
  half), `89` once v1.62's exclusion sub-class and AC-4.2's exhaustiveness clause landed, and it
  moves again here because v1.63's AC-2.7 second clause, AC-4.6 NUL paragraph, AC-1.8
  collection-only residual and the renderer-environment paragraph its reopen rewrote are all
  stated in negatives. The reason is
  given in that form deliberately rather than by quoting the clauses, since quoting them would move
  the figure inside the sentence stating it — so
  admitting `no`/`none` would put up to `101` candidate occurrences in front of a reader to
  recover the one known member. **That derived bound is a function of the figure above it, not a
  second statement of it**, so it moves whenever the scale is re-measured; both are a scale, not a
  contract. `zero` is the cheap half and is admitted to the alternation the
  first time a tree-derived zero is written that way; none is today. (3) A
  gap of more than three space-delimited tokens between the cardinal and its noun, which `{0,3}`
  stops below — **including a newline**, since `grep` is line-scoped and this document hard-wraps at
  ~95 columns, so a wrap between the two is an infinite gap and not a three-token one. Both halves
  are probed rather than asserted: the token bound is what the fifth positive above exercises, and
  the wrap half is what `split_only` above returns nothing for at `fbc2ea0` and over the draft. The widened gap admits
  false positives by design, so the bound is a readability limit and not a correctness one. The hit
  count is deliberately not stated: it is a procedure, not a measurement, and any
  edit to this document changes it, so a number here would falsify itself every cycle.

  Residual — three categories deliberately outside this rule, so their numbers are not swept.
  (1) Version History entries are a record of what was believed in their era and keep their
  era's numbers. (2) Counts of things that do not exist yet — the new module's collected count,
  the eight module seams of FR-5's injection list — are design-derived, not tree-derived, and move
  only when the design moves. (3) `path:line` locators are locators, not counts, so the count rule
  does not reach them. **The scope rule, stated over the class rather than over an instance list,
  because a value sweep only finds pins that already drifted:** every `path:line` pin in this
  document body is derived by a *shape* grep, not enumerated by hand.

  ```
  $ sed '/^## Version History/,$d' "$S" | grep -cE '\.py:[0-9]+'                      # -> 13
  $ sed '/^## Version History/,$d' "$S" | grep -oE '[A-Za-z0-9_./-]*\.py:[0-9]+' | sort -u | wc -l   # -> 11
  ```

  **Three units, three commands, because one `grep` over this class yields three different true
  numbers and v1.59 published one of them bare.** The first command counts **13 body lines
  carrying at least one pin**. The second counts **11 distinct fully-qualified `path.py:N`
  pins**; the two differ because a pin can repeat across surfaces and a line can carry more than
  one. The third unit is the one an auditor reads for the self-repair obligation — **bare pins
  standing in prose**, that is, pins not reproduced by a printed command — and it is
  **3**, down from **6** at `6f0ee85`, because **v1.60** rewrote §Assumptions' broad fence-literal
  census to print `-n` output instead of a `| wc -l` total, which turned three of the six into
  command output. **`6` and `three`, not the `7` and `four` v1.60 and v1.61 published**: this
  paragraph's own command counts *fully-qualified* pins, and a **continuation pin** — a bare `:N`
  on a line whose path was given by the preceding pin, of which `6f0ee85` carried one — has no
  `.py:` on it and so is not matched by `[A-Za-z0-9_./-]*\.py:[0-9]+`. Seven is what an eye counts
  and six is what the command counts; the published figure follows the command, because the whole
  point of the three-unit split below is that the stated unit and the command agree. The class,
  not the instance: **a continuation pin is invisible to both shape greps**, and the axis is any
  pin whose path is carried by an earlier line rather than repeated on its own — recorded here as
  residual (d) below rather than patched, because widening the shape to match a bare `:N` would
  match every ordinary colon-and-digit in prose. Verified at `fbc2ea0`: the bare-pin command
  returns `3` and the line command `11`; over the v1.63 draft they are `3` and `13`, the line
  figure moving with the two census output lines this revision adds and the pin figure not moving
  at all, which is the two units staying apart under a change that touches only one of them. The
  one continuation pin is gone from the body with the census lines that carried it. That block is located structurally, not by a line number: it is the only fenced
  block in this document opening with a quoted `git grep -n` command, and the anchored needle
  `grep -cE "^  [\$] git grep -n '" "$S"` returns `1` at `fbc2ea0` and `1` over the v1.63 draft. **The `[\$]` is
  load-bearing and was measured, not styled.** Every other needle in this document is
  single-quoted, where `\$` reaches the regex engine as an escaped literal; this one must be
  double-quoted so it can contain the `'`, and inside double quotes the shell collapses `\$` to a
  bare `$`, which ERE reads as an end-of-line anchor mid-pattern. Written that way the needle
  returns **`0`** — measured on this tree, an anchored locator silently reading as absence, which
  is the exact failure this document's locator rules exist to stop. The bracket expression is a
  literal `$` under every implementation. Residual on the needle — the form without the trailing
  quote, `grep -cE "^  [\$] git grep -n " "$S"`, returns `2`, because the narrow extractor census
  immediately above opens `git grep -n -E`; a reader must keep the quote, and a second quoted
  `git grep -n` block would make the needle `2` and require naming which one is meant.
  The bare-pin figure's own command is the first one above, minus the census output lines, counting
  pins rather than lines so the stated unit and the command agree:
  `sed '/^## Version History/,$d' "$S" | grep -oE '[A-Za-z0-9_./-]*\.py:[0-9]+:?' | grep -vc ':$'`
  → `3`. **It discriminates output from prose by the shape of `git grep -n` output itself — the
  second colon that follows the line number — and not by which directory the path starts in.**
  That is a `fbc2ea0` repair, and it was forced rather than tidied: the v1.62 form filtered on
  `^  h-mad/`, and the two probe lines that arrived in the broad census above open with `docs/`,
  so the old form counts them as prose and returns **`5`** over this same draft. The class is
  *any* discriminator keyed on a corpus's current directory names; the shape of the output it is
  reading is the invariant, and the residual is that a prose line quoting a pin with a colon
  immediately after it would be miscounted as output — screened below.

  This paragraph deliberately **re-quotes none of them** — restating a pin here would inflate every
  one of those figures by the act of describing it, which is the self-quoting hazard that already
  cost this document one needle. Read them off the commands. The obligation over the class, which
  is what makes a drifted pin cheap: **every pin either is reproduced command output, or carries a
  content predicate or an enclosing symbol on the same line**, so a drifted pin self-repairs under
  a re-run or under one `grep` of the predicate rather than under a reader hunting a moved line.
  The reproduced-output arm is the stronger of the two and was widened in **v1.60** precisely
  because the predicate arm has a failure mode the round-seven ruling names: *a predicate alone is
  not a needle*. The split of the 13 lines is 10 + 3 — 10 are output of the two
  `git grep` census commands above and re-quote nothing, and 3 are prose. Of the prose
  3, one is load-bearing (the `startswith` fence bound in §Assumptions, which carries the
  literal code token and greps to exactly one hit) and two are illustrative Phase-6 collectors,
  each beside a predicate that reproduces its candidate set; a drift in either changes no
  requirement. The other load-bearing pins — the two `re.findall` extractor assignments — are now
  printed output rather than prose. The fourth, the `run_recipe` signature FR-6 rests on, is
  written there as a bare ordinal beside the symbol name and is therefore **outside** both greps —
  residual (a) below. All four load-bearing pins were re-verified at `a8e0372`, at `335f535` and
  again at `74e126f`, and — the closure above no longer carrying anything by blanket — each was
  re-executed at `fbc2ea0` and returned what it returned before. Four
  residuals on the shape greps, all concrete. (a) Both require a `.py` suffix on the same line, so
  a bare-ordinal reference such as the one FR-6 prose uses for the `run_recipe` signature, and any
  pin into a non-`.py` file, is invisible to them; a bare ordinal is admissible only where the full
  pin appears on the same surface, and FR-6's does. (b) The first counts **lines carrying a pin,
  not pins**, which is the unit confusion this paragraph exists to prevent. (c) The bare-pin
  command discriminates output from prose by the *trailing colon* of `git grep -n` output, not by
  parsing fences, so a prose line quoting a pin with a colon straight after it would be miscounted
  as output. That absence is measured, not assumed:
  `sed '/^## Version History/,$d' "$S" | grep -oE '[A-Za-z0-9_./-]*\.py:[0-9]+:' | wc -l` → `10`,
  equal to the reproduced census output line count,
  `sed '/^## Version History/,$d' "$S" | grep -cE '^  [A-Za-z0-9_./-]+\.py:[0-9]+:'` → `10`, so
  every pin the discriminator treats as output *is* output and none is prose. **Both figures are
  published as a pair like every other**: `8` and `8` at `fbc2ea0`, `10` and `10` over the v1.63
  draft, the committed half being what the new commands return when run over the committed bytes.
  The equality, not the value, is the check. The absence is
  incidental, not load-bearing — nothing stops a future paragraph from quoting a pin that way — so
  the check is the equality of those two figures, re-run, and not the claim; a fence-parsing form
  is not worth its own bug here. **The superseded form is kept as the measured counter-example**:
  the v1.62 discriminator filtered on `^  h-mad/` and returns `5` over this same draft where the
  shape form returns `3`, because the broad census gained two output lines whose paths open with
  `docs/`. **(d) Neither reaches a *continuation pin*** — a bare `:N` on a line whose path was
  supplied by an earlier pin — because both require `.py:` on the matched text. That is the residual
  the `6`-versus-`7` correction above rests on, and it is left open deliberately: a shape admitting
  a bare `:N` would match ordinary colon-and-digit prose, so the cost of closing it exceeds the cost
  of the one member it would recover. It is screened rather than asserted, by its **distribution**
  and never by a total, because the total would read as sixteen defects. The screen is written
  inline, as the bare-pin command above is, so that publishing a residual's screen does not itself
  move the opener census:
  `sed '/^## Version History/,$d' "$S" | grep -oE '(^|[^0-9A-Za-z_/.]):[0-9]+' | grep -oE ':[0-9]+' | sort | uniq -c`.
  It returns 15 hits at `6f0ee85` and 16 at `fbc2ea0` and over this draft, and the *distribution*
  is the answer, not the total. Fourteen of them at every one of the three are FR-6's deliberate
  bare ordinals for the two extractors and the inline runner, which residual (a) already admits
  because the fully-qualified pin appears on the same surface. The two that arrive at `dfae038` sit
  inside **reproduced command output**, not prose. The one that leaves is the single continuation
  pin the `6f0ee85` body carried, in the §Assumptions prose the census rewrite replaced. So the
  member count is **1 → 0**, and the screen's own residual is that it cannot tell an FR-6 ordinal
  from a continuation pin — the reader does that, off the printed values. No `path:line` is
  re-quoted in this paragraph, for the reason the paragraph above gives. Every pin is still a line
  number and will still drift, and rewriting them as structural locators is owed by this document,
  the design and the plan **together** — done in one document alone it would read downstream as a
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
- v1.57: Round-four back-propagation of one plan finding (agy cycle 76) plus decision-sheet items B/C/D. Finding 1: Out-of-Scope's fence count was 68 and is 73 openers at 335f535, and it now carries both its generating command (git grep -c '^```bash' -- 'h-mad/*.md' 'handoff/*.md' ':!*/archive/*' | awk -F: '{s+=$NF} END {print s}') and the sha, plus the git ls-files ... | grep -c archive -> 0 that shows the archive exclusion selects nothing at this sha and is kept only against future widening. The interesting half is why the v1.56 sweep missed it: a value sweep fires on values that CHANGE, and 68 was never edited -- it drifted in place, in a non-normative section a walk of the FR/AC bodies never visits. The class rule therefore now carries its own ENUMERATION, independent of what changed, over the whole body up to the Version History boundary, keyed on SHAPE rather than on what changed, and its alternation covers spelled-out cardinals because this document states most of its counts as words (seven bash blocks, Twenty-four tracked .py files, six hits) so a digits-only enumeration would miss the majority of its own members. The drift story is verified, not asserted: git log -S'There are 68' returns exactly one commit, e58ef3a, so the number was written once and never edited, and the same command gives 68 at e58ef3a and 73 at 335f535 -- same command, same corpus, different tree. Two concrete residuals on the enumeration (a counted noun outside the closing alternation, and a cardinal of one hundred or more written as words) and a stated reason for carrying no hit count. AC-1.7's '16 headings, 2 duplicated' was the same class's second surviving member and now carries two commands and the sha, plus the evidence that invariants.example.md holds no fences so a raw line grep cannot miscount, and the residual that the commands compare raw lines so 2 is a floor. Decision B: FR-6 called the ordinals the load-bearing part; they are demoted to informational and the CONTENT PREDICATE is the contract, with the two predicates' differing cardinality stated separately (_gate_bash_block filters on h_mad_audit_gate.py and asserts exactly one; :412 filters on exec codex and takes the FIRST hit via next(..., '')), the ordinals' base named (1-based over the extractor's own re.findall on _second_surface()), and the era split stated: after FR-6 :270 addresses by heading plus tag and retires its predicate, :412 keeps its permanently. Decision C: the spec was SILENT on the closing-hash delimiter where the design has an oracle-backed rule, so AC-1.7 now states it, measured on markdown-it-py commonmark preset -- '## Text ##' -> 'Text', '## Text\t##' -> 'Text', '## Text##' -> 'Text##' -- the last being the case an unconditional right-strip of # gets wrong. Decision D: no seam ordinal exists in this document's body. Every count and path:line locator was re-derived at 335f535 and restamped: 6, 24, 7 [4] [2], the two-hit narrow extractor census, :270 :309 :412 docsections.py:37, the _SCANNED parametrise-twice 2, and the three *.py globs -- all unchanged.
- v1.58: Round-five decision-sheet items E and F; no finding this round landed in this file. E (one rule, one checker): the count-enumeration in Assumptions is now the CANONICAL checker for the tree-derived-count class rule across all four documents, and it was EXECUTED against controls rather than published unrun -- because a sibling screen for this same class shipped with a backspace escape where a word boundary was meant and matched nothing. The controls found the same defect class here: the gap between a cardinal and its counted noun was one optional lowercase word, which cannot span 'tracked' and a backticked '.py', so the enumeration was blind to a member sitting in the paragraph that defines it. The gap is widened to three space-delimited tokens; the recovered members are NAMED, not counted, because both forms' totals move on every edit. Positive and negative control results are published beside the enumeration. F (locator uniqueness is commit-scoped): every locator this document publishes is now LINE-ANCHORED and re-verified at 74e126f -- the enumeration's needle is an anchored command opener at exactly 1 hit, and the AC-6.4 membership rule is addressed by its anchored AC label at exactly 1 hit, with all 49 AC body anchors verified collision-free. A plain-substring needle was tried first and MEASURED at 2, because the sentence publishing it reproduced it; that measurement is recorded as the reason the anchored form was chosen. Every tree count was re-derived at 74e126f and restamped, all unchanged: 73 openers and 0 archive paths, 24 tracked .py with a fence literal, 6 broad literal hits with the same 2-hit narrow extractor census, 16 headings with 2 duplicated and no fences in invariants.example.md, the _SCANNED parametrise 2 and the three *.py globs, and 7 [4] [2] from the second-surface extraction. The four path:line locators were re-verified at 74e126f and now record what each resolves to.
- v1.59: Round six, decision A applied to this document's own enumeration at freeze sha 35698f9: the class-closure screen is now published with a positive control (5 members, all printed) and a true-negative control (3 non-members, all declined), both runnable, with the pattern extracted from the published block by its own anchored needle rather than retyped. Two blind forms named rather than a bare zero — the tree-derived zero written as 'no fences' (a genuine false negative) and AC-1.2's 'zero'/'blocks' wrap (design-derived, shape demonstration only) — and the line-split class probed systematically by split_only, which fires on a synthetic split and returns nothing here. Residuals restated over their axes and still three: (2) becomes word forms outside the alternation (zero, no/none, one hundred and above) with the trade measured at 75; (3) absorbs the newline as an infinite gap. Decision C closed as a class: path:line pins are now derived by a shape grep (7 lines) with the class obligation and two residuals stated, re-quoting none of them. Freeze-sha closure stated once (git diff --name-only 74e126f 35698f9 | grep -vc '^docs/' -> 0), and 6/24/73/0 nevertheless re-executed. Doc-scoped figures re-derived in this revision: awk needle 1, opener census 20, py-pin lines 7, no-tokens 75; [v1.60 correction, entry otherwise left as written: this whole list is stamped `35698f9` and every figure in it is the value over v1.59's own DRAFT, which landed as `6f0ee85`. At `35698f9` the same commands return awk needle 1, opener census 9 openers over 5 distinct tokens, py-pin lines 8, no-tokens 59 (`git show 35698f9:"$S"` piped into each). The audit found the census instance; re-deriving at both shas found that three of the four were mis-stamped the same way and only the awk needle, being 1 at both, was indistinguishable. v1.60 replaces the single-stamp habit with a pair rule -- a doc-scoped figure publishes the committed value and the draft value, collapsed only where they agree.] the awk-slot residual materialised during drafting (the shape grep was first written as an awk one-liner, took the needle to 2 and broke the control's pattern extraction) and is recorded rather than hidden. The 'widening recovers three members' claim is re-verified and now says how to read it: a mechanical diff of the two forms returns more lines than members because this document quotes its own members, so count members by reading them. Late self-review caught three of my own defects before shipping and all three are fixed in this entry's revision: (a) all eight control strings were paraphrases and are now verbatim substrings, checked by deleting the control block from a copy and running grep -cF, which returns 1 for each; (b) the closure paragraph claimed this file changed in both intervening commits when git log 74e126f..35698f9 on this path returns exactly one, 0aac0b7; (c) the commands here depend on $S, whose unbound form prints 0 on stdout, so the binding is now stated where the section starts.
- v1.60: Round seven back-propagation at freeze sha 6f0ee85; no audit cycle of this document's own, three items routed from the plan and design legs. (1) MIS-STAMP, and it was wider than the finding. v1.59 published the slot census as 20 openers over 11 distinct tokens under the stamp 35698f9, where the true value is 9 openers over 5 distinct tokens; 20 is the value at 6f0ee85, the commit that shipped v1.59, so the plan's figure was the correct one. Both verified here with git show 35698f9: and git show 6f0ee85: piped into grep -oE '^  $ [a-zA-Z0-9._-]+' | sort | uniq -c. Re-deriving v1.59's other three doc-scoped figures at both shas showed the same mis-stamp in all of them -- py-pin lines are 8 at 35698f9 and 7 at 6f0ee85, no-tokens are 59 at 35698f9 and 75 at 6f0ee85, and only the awk needle (1 at both) was indistinguishable. The class, not the instance: a figure measured over THIS file is taken over the draft in hand, which lands in the commit AFTER the freeze sha, so it is now published as a PAIR -- git show 6f0ee85:$S | <command> for the committed value and <command> $S for the draft -- collapsed to one number only where the two agree. The pair rule immediately earned itself: the census is 21 openers over 11 distinct tokens over this draft, because this revision adds a second sed command to the path:line block, and that third value would otherwise have shipped as a fourth silent restamp. awk holds its slot alone at all three shas, so the needle's conclusion never moved. (2) The predicate ruling, applied to the one pin that failed it. The broad fence-literal census in Assumptions was written 'git grep -n ...bash -- *.py | wc -l', so a reader re-running it as printed got 6 and no locations, and the three pins in the prose beneath it rested on the non-greppable predicate 'are fixture strings'. It now prints -n output spliced from the command rather than retyped, and the prose re-quotes no path:line from it. CONTRADICTION REPORTED, not silently resolved: the ruling's first option -- name the enclosing test function for the test_docsections.py hit -- is unavailable, because that hit sits inside a module-level FIXTURE string constant (grep -c '^FIXTURE = ' -> 1) and the file's first def is BELOW it, so the reproduced-output option was the only one open. The four pins the ruling passed are untouched. (3) Three units for the path:line class, because one grep over it yields three different true numbers and decision H says a bare integer is not a measurement: 11 body lines carrying a pin, 9 distinct fully-qualified path.py:N pins, and 3 bare pins standing in prose -- down from 7 at 6f0ee85 because four became command output -- each with its own command, and the bare-pin command counting pins rather than lines so the stated unit and the command agree. Freeze-sha closure extended: git diff --name-only 74e126f 6f0ee85 | grep -vc '^docs/' -> 0 and the same range with -- '*.py' prints nothing, so every tree-derived figure stamped 74e126f is unchanged at 6f0ee85; 6, 24, 73 and 0 were nevertheless re-executed there rather than inferred. Decision A re-run rather than carried, per the sheet: the positive control prints all five members and the true-negative control declines all three over this draft, the pattern still extracted from the published block by its own anchored needle, and all eight strings verified verbatim at grep -cF 1 with the control block deleted from a copy. split_only fires on its synthetic fixture and returns nothing on this draft. The v1.59 Version History entry is left as written with a bracketed correction, per the standing practice. (4) Decision A applied to the enumeration against THIS revision's own text, not only re-run against last revision's: the path:line figures above are stated in units -- lines and pins -- that the v1.59 closing noun alternation did not carry, so v1.60 would have shipped prose its own class-closure screen was blind to. lines? and pins? are added to the alternation, which is residual (1)'s stated maintenance path taken rather than deferred, and a SIXTH positive control is added covering exactly that widening: 'The split of the 11 lines is 8 + 3', verbatim from the body, NO MATCH under the v1.59 form and MATCH under this one, which is the before/after a widening needs and which v1.57's gap fix did not have. The controls are now nine strings -- six positives all printed, three true negatives all declined -- and all nine verify verbatim at grep -cF 1 with the control block deleted; the sixth is new text, so only the other eight have a 6f0ee85 half. The widening's cost is stated by SHAPE and deliberately NOT as a number: this paragraph and the residual that describes it are themselves members of both forms, so a published delta would inflate itself by the act of publishing it, which is the same self-quoting hazard that already cost this document one needle and the reason the enumeration has never published its own hit count. (5) The verbatimness check is now cut at the Version History boundary before the control block is cut. Its stated subject is 'a verbatim substring of this document's BODY', but it ran over the whole file, so a Version History entry quoting a control string took that string's count to 2 and turned a passing check red for something that is not a defect. That is measured, not foreseen: it happened while this entry was being written, because this entry quotes the sixth positive. Cutting the region residual (1) already exempts closes the class for every future entry instead of forbidding entries from quoting strings, and all nine return 1 again. Doc-scoped figures over this draft, each with its command in place: awk needle 1, git-grep-n needle 1, opener census 21 over 11 distinct tokens, py-pin lines 11, distinct pins 9, bare prose pins 3, no-tokens 81, split_only empty with its synthetic positive firing, nine control strings verbatim at 1. (6) One more locator defect, found by running the published string verbatim rather than the shell-escaped form I had tested with: the new git-grep-n needle is double-quoted so it can hold a single quote, and inside double quotes the shell collapses \$ to a bare $, which ERE reads as a mid-pattern end-of-line anchor -- so the needle as first written returned 0, an anchored locator reading as absence. It is now written [$], measured at 1 with the trailing quote and 2 without, and the reason is stated beside it. Every other needle in this document is single-quoted and was never exposed to this. Residual (c) on the bare-pin command also carried a bare 'there is none today'; it now carries sed '/^## Version History/,$d' | grep -c '^  h-mad/' -> 8, equal to the reproduced-output line count, and says the zero is incidental rather than load-bearing. [v1.62 correction, entry otherwise left as written: '3 bare pins standing in prose -- down from 7 at 6f0ee85 because four became command output' publishes two figures the entry's own command does not return. Re-run at 6f0ee85, `git show 6f0ee85:"$S" | sed '/^## Version History/,$d' | grep -v '^  h-mad/' | grep -oE '[A-Za-z0-9_./-]*\.py:[0-9]+' | wc -l` -> 6, and the drop is therefore three, not four. The 7 is the LINE count at that sha (`grep -cE '\.py:[0-9]+'` -> 7), so the sentence crossed the two units this same paragraph exists to keep apart. The one hit the pin command does not see is a CONTINUATION pin -- a bare :N whose path came from the preceding pin -- which is now residual (d) on the shape greps in the body.]
- v1.61: Round fourteen, ONE routed finding and no audit cycle of this document's own; freeze sha b3be433, working tree byte-identical to it before this revision. The finding, from the plan's gating leg (plan.audit.v85.teammate, must 3), was filed as "the spec's bare pgid=<n> against three siblings that agree on pgid: \"<n>\"". THE CHARACTERISATION IS WRONG AND THE CONCLUSION IS RIGHT, and the two are separated here rather than merged. Body-scoped counts at b3be433 (git show b3be433:<path> piped through a body cut and grepped for each form): spec bare 1 quoted 0; plan bare 0 quoted 0; design bare 2 quoted 3; impl-plan bare 0 quoted 1 -- there is no consensus to conform to, so the spelling is DERIVED FROM THE CONTRACT and not from a vote. Three sources, none of them a sibling's majority. (a) This document's own FR-4 grammar: bare is an EXEMPTION and pgid is not on it. (b) The emission site: AC-4.6 puts pgid on a DETAIL line, and every detail line in this document is <key>: "<value>" -- os_error, missing_key, duplicate_key, overlap, leftover, verify, written, failed, skipped, stream. (c) The design at b3be433 states the exemption is exhaustive and names this exact case in words -- 'including the helper-produced numbers seconds= and pgid: (seconds="1.0", pgid: "4242")' -- and design v1.79's own entry records closing it that way; the impl-plan's DETAIL_KEYS tuple carries "pgid:" as a member (counted in the tuple, 11 keys). So AC-4.6 now reads pgid: "<n>" and carries the derivation beside it. THE CLASS, NOT THE INSTANCE, because a single instance is how this survived four documents: the AXIS is every field name this document spells inside a verdict or a detail line, and the defect that let one member drift was FR-4's OPEN list -- it read 'helper-constrained fields SUCH AS rc=, blocks=, shell=, stage= stay bare', which fixes the spelling of no field at all. FR-4 now closes it: exactly seven bare fields (rc=, blocks=, count=, keys=, shell=, stage=, reason=), exhaustive IN BOTH DIRECTIONS, governing the VERDICT LINE ONLY; detail lines carry no exemption and are always quoted; a field's spelling follows WHICH LINE IT SITS ON, not what it is. A helper-produced number off the list is quoted (seconds="<n>"), so provenance does not decide the spelling and membership does. RESIDUAL, a concrete category: this fixes every field and detail key this document names and does not fix one a LATER cycle adds -- a new verdict-line field is bare only by joining the seven named here, and a new detail key is quoted by construction. THE SWEEP, run after the last edit landed and reported with its command: python3 classification of every backtick span in the body that holds a DOCBLOCK line or a field token, splitting key= from key: " -- the only bare-spelled field outside the seven was the AC-4.6 pgid, and every quoted field (heading, arg, index, key, message, path, seconds, value) is off the list, so the class had exactly one member and it is closed. DECISION-K SWEEP, every doc-scoped figure re-run over THIS draft after the last edit and re-stamped from the v1.60 draft to the v1.61 draft (nine sites, plus the reader-instruction naming the commit that ships this revision): awk needle 1; git-grep-n needle 1 with the trailing quote and 2 without; opener census 21 openers over 11 distinct tokens, unchanged because this revision adds no fenced command; py-pin lines 11, distinct pins 9, bare prose pins 3; nine control strings all verbatim at grep -cF 1 with the Version History and the control block cut, six positives MATCH and three true negatives NO MATCH under the pattern extracted from the published block by its own anchored needle; split_only empty on this draft with its synthetic positive firing; AC-1.2 anchor 1; reproduced-output lines 8, equal to the bare-pin discriminator. EXACTLY ONE FIGURE MOVED, and it is the one this revision's own prose moves: the no-token scale was 81 over the v1.60 draft and is 85 over this one, because the new exemption paragraph is stated in negatives; the figure DERIVED from it in the next clause ('up to N candidate occurrences') is moved with it rather than left at the old value, and the reason is given without reproducing the clauses, since quoting them would move the figure inside the sentence stating it. The class-closure enumeration is at 110 over this draft and 110 at b3be433 -- its hit count is not published, by the standing rule, and it is stated here only because the first draft of the FR-4 paragraph took it to 111 on the phrase 'between the two lines', a non-member; the phrase was rewritten to 'from the verdict line to a detail line', which is also the more precise sentence. OWED ELSEWHERE, reported and NOT edited: the design's AC-table row for AC-4.6 says 'pgid= in the detail' in its killpg-injection clause while the same row says 'pgid: in the detail' for the collect clause and the design's own grammar paragraph quotes it -- that is the design's internal inconsistency, and it is the ONLY bare form in that document that is a diagnostic spelling; its other bare pgid= occurrences are Python constructor syntax (LaunchFailed(stage, err, pgid=None)), correctly bare and NOT members of this class, which is the distinction the auditor's count did not draw. The plan's body carries NEITHER form, so its claim about an exhaustive bare list has no local member to check. NO gating claim, no second surface, no exit-gate claim is made by this entry; codex_status exhausted until 2026-09-07 11:28. [Appended after the entry landed, and the whole-file screens re-run after it: the detail-key enumeration in FR-4 is stated as THE KEYS AS OF THIS REVISION and attributed to DETAIL_KEYS as the authority a reader checks it against, because an enumeration written flat would read as exhaustive over a set this document does not own; the residual therefore names the specific staleness -- DETAIL_KEYS can gain a member without this list gaining one, which AC-4.5's bidirectional registry walk catches and this grammar does not. Post-edit re-run: awk needle 1, git-grep-n needle 1 with the quote and 2 without, opener census 21 over 11 distinct tokens, no-tokens 85, py-pin lines 11 / distinct 9 / bare prose 3, reproduced-output lines 8, AC-1.2 anchor 1, nine control strings verbatim at 1, six positives MATCH and three true negatives NO MATCH, split_only empty with its positive firing, class-closure enumeration 110, bare pgid= in the body 0, PRECHECK: PASS issues=0.] [v1.62 corrections, four of them, entry otherwise left as written. (1) The OWED ELSEWHERE item was FALSE WHEN IT WAS COMMITTED: 00b961f -- the commit carrying this entry -- repaired the design's AC-4.6 row in the same commit, so nothing was owed by the time a reader could read the sentence. Re-measured at HEAD: `grep 'AC-4.6' <design> | grep -o 'pgid[=:]' | sort | uniq -c` -> 2 pgid: and 0 bare at dfae038, against 1 pgid: + 1 pgid= at b3be433; the design's four surviving body pgid= are all LaunchFailed(...) constructor kwargs, which this entry already excluded by name. The class IS closed across the feature at dfae038. The structural lesson is not the instance: THREE of the four documents wrote an OWED-ELSEWHERE debt in this same commit and all three were discharged by it, because each author read siblings that were being revised concurrently -- so an OWED ELSEWHERE written during a parallel revision batch is a claim about a MOVING tree and must be re-measured after the batch lands, not before. (2) Derivation clause (b) lists ten detail keys as 'every detail line in this document' and includes `stream`, which was NOT in the document when the clause was written: `git show b3be433:"$S" | awk '/^## Version History$/{exit}{print}' | grep -c 'stream:'` -> 0, and the same at 8909ec4; it is 1 at dfae038, inside the FR-4 enumeration THIS revision added. The derivation stands on the other nine; the evidence sentence overstated its scope by one member and the member it overstated was one the same edit introduced. (3) 'ONE routed finding' is wrong: plan.audit.v85.teammate routed THREE items at this document -- the pgid must (answered), the 2486 figure in AC-6.4's gate command, and BAD_ARGS missing from AC-4.2's exit-0 enumeration. `grep -n -i 'spec' docs/01-plan/features/doc-block-exec.plan.audit.v85.teammate.md` shows all three. (4) The two unanswered items were not recorded as deferred either, which is why they survived a whole round; both are fixed in v1.62 and 2486 was the round's only wrong published figure in this document.]
- v1.62: Round fifteen delta-review revisions; freeze sha dfae038 (HEAD), which is byte-identical to 00b961f over this file (`git diff --stat 00b961f dfae038 -- "$S"` empty; the two intervening commits touch only docs/handoffs/, docs/learnings.md and docs/skill-candidates.md). ADVISORY, NOT A GATE: the delta pass answered here is one advisory reviewer, no second surface, no exit-gate claim; codex_status exhausted until 2026-09-07 11:28. THE FREEZE SHA IS RE-DERIVED, NOT INHERITED, AND THIS DISAGREES WITH BOTH THINGS I WAS HANDED. The delta report prescribed restamping to b3be433 and the round's decision sheet named 00b961f; this document's own definition -- 'the freeze sha: the last commit, and the tree every tree-derived figure here is taken over' -- makes it dfae038, and stamping either older sha would have re-shipped the same defect one revision later. b3be433 never touched this file at all (`git log --oneline 74e126f..dfae038 -- "$S"` lists 0aac0b7, 6f0ee85, 8909ec4, 00b961f and no b3be433), which is exactly how v1.61 came to carry TWO freeze shas at once -- b3be433 in its entry and 6f0ee85 in the body paragraph two revisions behind it. The rule that closes it is now in the body: both surfaces take `git rev-parse --short HEAD` at drafting time, and the entry quotes the body's sha rather than deriving its own. THE PRESCRIPTION WAS CORRECTED, NOT IGNORED, AND THE RECONCILIATION IS RECORDED HERE BECAUSE A READER WILL FIND b3be433 IN THE DELTA REPORT AND dfae038 IN THIS DOCUMENT. The delta report (docs/03-analysis/doc-block-exec.spec.delta-review.r15.md, must 1) prescribes restamping the four current-state sites to b3be433. That prescription is SUPERSEDED, and the orchestrator re-ran the three checks and confirmed it: b3be433 was the right answer to the question 'what should v1.61 have stamped', and this revision is v1.62. The distinction the round-fifteen decision sheet blurred, stated so it does not recur: 00b961f is the correct SUBJECT of the delta review -- it is the diff that was audited -- and it is NOT the value of a freeze sha a document stamps, which the 'Two shas' paragraph defines as the last commit its tree-derived figures were taken over. Round fourteen's convention CONFIRMS dfae038 rather than contradicting it: v1.61 stamped b3be433, which was HEAD when v1.61 was authored and the parent of its landing commit 00b961f; dfae038 is HEAD now and will be the parent of this batch's landing commit. Same rule, moved forward one round. The byte-identity is what makes a figure derived from the 00b961f diff legitimately re-usable at the stamped sha, which is why it is stated in the same clause as the stamp rather than left implicit. ONE FURTHER FIGURE MOVED WITH THE STAMP AND IT IS A DEFECT IN ITS OWN RIGHT, NOT A CONSEQUENCE: the closure paragraph published TWO commits for the range it named ('git log --oneline 74e126f..6f0ee85 -- "$S" lists 0aac0b7 and 6f0ee85, so this file changed in both'). At the honest range the count is FOUR -- `git log --oneline 74e126f..dfae038 -- "$S"` lists 0aac0b7, 6f0ee85, 8909ec4 and 00b961f -- and the sentence now reads 'in four of them'. The two extra commits are the ones that shipped v1.60 and v1.61, so the old figure was not merely stale at a new sha: it under-reported this file's own churn by half for two revisions, in the paragraph whose entire job is to say which figures the closure does NOT cover. (1) MUST, THE `this revision` CLASS, SWEPT PER SITE AND NOT BLANKET. The report named twelve body-scoped occurrences from a line-scoped grep; the true body figure is FOURTEEN, because two are split across a hard wrap and no single-line grep can see them -- `awk '/^## Version History$/{exit}{print}' "$S" | tr '\n' ' ' | grep -o 'this  *revision' | wc -l` -> 14 against `grep -c` -> 12 at dfae038. One of the two wrapped members was named by no surface: FR-4's detail-key list read 'The keys as of this / revision are', so the eleven-key enumeration was stamped to whichever revision happened to be reading it. THE DISPOSITION IS STATED AS ARITHMETIC OVER THE MEASURED 14, NOT AS A BARE COUNT OF WHAT I TOUCHED: 14 = 8 restamped + 1 rewritten away + 5 kept, and 3 new ones are added by this revision's own prose, so the body figure after the sweep is 5 + 3 = 8 and `grep -o 'this  *revision'` over the collapsed body returns 8. The 8 restamped are read out of the Version History entry that records each event rather than assumed: the awk-slot residual that materialised during drafting is v1.59's (its entry says so); SIX are v1.60's -- the second `sed` command, the sixth positive control on the alternation widening, the Version-History-cut repair to the verbatimness check, the `lines?`/`pins?` addition, the §Assumptions census rewrite and the widening of the reproduced-output arm; FR-4's detail-key list is v1.61's. The 1 rewritten away is the clause explaining why the no-token scale rose, which is now stated as a per-revision history instead. The 5 kept are GENERIC statements of a standing rule that remain true for v1.62 ('for this revision', 'this revision's freeze sha', 'after this revision lands', 'the form this revision ships', 'after every edit this revision makes'). The 3 new all name this revision's half of a published pair, which is what the phrase is for. PER SITE, NEVER BLANKET, and the same discrimination governs the sha: `6f0ee85` occurs on 24 lines / 36 occurrences at dfae038, and only the sites asserting a CURRENT state moved -- the freeze-sha closure and its two fenced commands, the `git log` range, the pair rule's committed half, the two closure-carries in §Assumptions and §Out-of-Scope, and every published pair's committed half. Every remaining `6f0ee85` is now explicitly labelled history ('the commit that shipped v1.59'), and the census progression 9 -> 20 -> 21 and the no-token history 75 -> 85 are kept as anchors, never as this revision's committed half. (2) THE COMMITTED HALF MOVES WITH THE FREEZE, WHICH IS THE HALF v1.61 DID NOT PAY. v1.61 restamped nine DRAFT halves from 'the v1.60 draft' to 'the v1.61 draft' and left every COMMITTED half at 6f0ee85, so its published pairs straddled two freezes. Each committed half is re-measured at dfae038 here, `git show dfae038:"$S" | <command>`, and the pair is collapsed where the halves agree: awk needle 1/1; git-grep-n needle 1 with the trailing quote and 2 without, at both; opener census 21 openers over 11 distinct tokens at both; py-pin lines 11, distinct pins 9, bare prose pins 3, reproduced-output lines 8, all at both; AC-1.2 anchor 1/1; blind-form needle 1/1; nine control strings verbatim at grep -cF 1 at BOTH halves -- which discharges the 'the sixth positive has no 6f0ee85 half' caveat v1.60 and v1.61 both carried, since that string exists at dfae038; six positives MATCH and three true negatives NO MATCH under the pattern extracted from the published block by its own anchored needle; split_only empty over the draft with its synthetic positive firing. EXACTLY ONE FIGURE MOVED and it is the one this revision's own prose moves: the no-token scale is 85 at dfae038 and 89 over this draft, because v1.62's exclusion-(2) sub-class and AC-4.2's exhaustiveness clause are both stated in negatives. THE DERIVED FIGURE MOVED WITH IT: 'up to N candidate occurrences' is a FUNCTION of that scale, not a second statement of it, and it is now written as 89 and labelled as derived so a later re-measure cannot leave it silently behind. The class-closure enumeration is 110 at dfae038 and 123 over this draft; its hit count is not published in the body by the standing rule and is stated here only because the eighteen new members were read individually to confirm every one carries its command. (3) MUST, 2486 -- THE ROUND'S ONLY WRONG PUBLISHED FIGURE IN THIS DOCUMENT, AND THE LAST DOCUMENT STILL ASSERTING IT. AC-6.4's Phase-5f gate command carried the comment 'from h-mad/ the same command collects 2486'. Measured at dfae038, each in its OWN shell invocation of `python3.11 -m pytest --collect-only -q -p no:cacheprovider`: 2809 from the repository root and 2547 from h-mad/, both +61 on the retired 2748/2486 pair the impl-plan already publishes and the plan already retires. THE CLASS, NOT THE INSTANCE: the number is not replaced with a fresher number, because a comment embedded in a command string is the one surface a value sweep of this document has already missed twice (v1.54's miss lived there). The rule now stated in the body is that such a comment may name a CONSTANT stamped elsewhere in this document -- 2748 is, at the AC body above, with its sha e8eaf6f and its re-measure-at-5c rule, which is why it stays -- and may never carry a fresh measurement of its own; 2809/2547 are stated in prose with their command and sha, as a scale for the root-versus-h-mad gap and not as a floor. (4) MUST, THE OWED-ELSEWHERE DISCHARGE, taken as a bracketed correction on the v1.61 entry per the standing practice, together with three further corrections to that entry that the delta pass surfaced: the `stream` key was not in this document when v1.61's derivation cited it, 'ONE routed finding' was three, and the two it did not answer were not recorded as deferred. The v1.60 entry takes a bracketed correction too, for a defect no report raised and my own re-run found: it published the bare-pin drop as '7 -> 3, four became command output' where its own command returns 6 -> 3 and three, because 7 is the LINE count and the pin command counts PINS. The gap is one CONTINUATION pin -- a bare :N whose path came from the preceding pin -- and that is now residual (d) on the shape greps, screened by distribution rather than by a total (14 of the 15/16 hits at every sha are FR-6's deliberate bare ordinals, which residual (a) already admits; the member count is 1 at 6f0ee85 and 0 at dfae038 and over this draft). (5) SHOULD-FIXES, all six addressed, none deferred. AC-4.2 gains BAD_ARGS and states EXHAUSTIVENESS rather than a list: its eleven exit-0 heads plus AC-4.1's RAN, and its three collapsed exit-2 heads with UNREADABLE and LAUNCH_FAILED standing for their reason=/stage= families, partition every head of the impl-plan's VERDICT_TABLE, so nothing the helper can print falls outside the two classes. FR-4's dangling 'It is tested with' now names its subject. FR-4 and AC-4.2 both say IN WORDS that DETAIL_KEYS and VERDICT_TABLE do not exist in the tree until 5d/5e and must be located by their ASSIGNMENT and never by their name -- and the needle for either is deliberately NOT published here, because publishing it would make this document a second hit for it, the same self-quoting hazard that has already cost this document one needle. `fields` and `heads` are named as a NEW sub-class of the enumeration's residual (1): they are counted, so they do not belong on the un-measured list beside `commits`/`tokens`/`values`; they sit outside the alternation under exclusion (2) as design-derived counts, and the rule over the axis is now stated -- a counted noun joins the alternation when its count becomes tree-derived. (6) OWED BY ANOTHER DOCUMENT, REPORTED AND NOT EDITED: the design's triage alternation for the constructor-form screen lists ten keys and omits duplicate_key, while DETAIL_KEYS has eleven, so that screen cannot raise the one key it is blind to. This document's own FR-4 list matches DETAIL_KEYS member-for-member, so the spec is not the document that drifted. Tree-derived figures re-executed at dfae038 rather than inferred, per the closure's own practice: 6, 24, 73, 0, and AC-1.7's 16/2 heading pair, each returning the value printed beside it.
- v1.63: Round seventeen. FOUR cross-document decisions reach this document and it has no audit report of its own; the decision sheet is docs/03-analysis/doc-block-exec.gating-decision-sheet.r17.md and the reports that raised them are docs/02-design/features/doc-block-exec.design.audit.v96.codex.md (musts 1, 2, 3) and docs/01-plan/features/doc-block-exec.impl-plan.audit.v47.codex.md (musts 1, 2). NO gating claim, NO second surface, NO exit-gate claim: this round is FAIL to revision and the gate is c97/c88/c48. Freeze sha fbc2ea0, which is HEAD and over which this file's working bytes are unchanged (git diff --stat fbc2ea0 -- $S is empty), so the committed half of every published pair below moves from the v1.61 bytes at dfae038 to the v1.62 bytes at fbc2ea0 and equals the value v1.62 published as its DRAFT half. (3a) AC-2.7 gains a SECOND CLAUSE beside the substring clause, not in place of it: any two DISTINCT keys whose match spans intersect in the block text refuse under the same SUBST_OVERLAP token. Reproduced here on Python 3.11.8, not carried: abc under {ab->X, bc->Y} with the prescribed escaped alternation and a recording callback returns Xc while text.count reads ab=1 bc=1 and the callback fired ab=1 bc=0, and the control ab bc ab bc returns X Y X Y with 2/2 fired 2/2; the map-static substring predicate any(a != b and a in b) is FALSE for {ab, bc}, which is why the existing clause does not reach it. The two predicates are independent in both directions, which is why neither replaces the other. THE DETAIL-LINE SPELLING DISAGREES WITH THE DECISION SHEET AND THE DISAGREEMENT IS REPORTED, NOT SILENTLY RESOLVED: the sheet prescribes intersect: "<a>" "<b>" at <offset>, whose bare <offset> this document's own FR-4 refuses, because the bare-field exemption is a closed list of seven governing the VERDICT LINE ONLY and every detail line is <key>: "<value>" without exception, with FR-4 already settling the precedent for a helper-produced number off the list (seconds="<n>", and the pgid case decided in v1.61). The conforming spelling intersect: "<a>" "<b>" "<offset>" is written here and the conflict was sent to the orchestrator before the edit landed. intersect: is the TWELFTH detail key and FR-4's enumeration moves from eleven to twelve with it. (3b) AC-4.6's launch-failure family names the spawn-time ValueError: embedded null byte. Reproduced on Python 3.11.8: Popen([bash, -c, true]) returns rc 0 and Popen([bash, -c, true + chr(0)]) raises ValueError, while the same text passes strict UTF-8 decoding, so no UNREADABLE refusal upstream catches it. The AC's class widens from Every OSError, which ValueError is not, to every exception the helper raises on its own behalf at a named stage. THE SHEET CALLS stage=spawn A NEW LABEL AND IT IS NOT: git grep over both documents at fbc2ea0 returns stage=<mkdtemp|spawn|reap|collect> in the spec and the same alternation in the design, so no enumeration and no count moves for 3b. (3c) The ninth module seam. This document DOES enumerate seams, in two places, and both move: AC-5.5's exactly eight named fault injections becomes nine and its seven module seams becomes eight, and the Assumptions residual (2) that names the seven module seams of FR-5 injection list becomes eight. os.lstat was verified absent from the eight before it was added (the eight are os.killpg, shutil.rmtree, tempfile.mkdtemp, os.chmod, os.unlink, _final_write, _close_stream and the recorded Popen instance) and it occurs exactly once in the body before this revision, in AC-3.10 as the rollback identity comparison, which is the guard the seam now discriminates. (3d) AC-1.8's collect-alone pin becomes COLLECTION-ONLY. THE SHEET ATTRIBUTES A PHRASE TO THIS DOCUMENT THAT IS NOT IN IT: passes unchanged returns 0 over the body collapsed with tr, and the phrase lives in the design AC-1.8 table row, which is the design author work. What this document did carry is the reason the phrase was never true anywhere: AC-6.4 already lists the delegation spy test in test_docsections.py as a node added to a pre-existing file, so a subprocess that RUNS that file cannot stay green under the docsections-delegation-reverted mutant the wire pin exists to fail. Residual stated exactly: the pre-existing tests in that file are no longer RUN in isolation by AC-1.8, and they run in the full suite under AC-6.4 floor and in the 5e module-scoped run. THE FREEZE MOVE IS NOT A RELABEL AND TWO PUBLISHED TREE-DERIVED FIGURES ARE WRONG AT THE NEW FREEZE, which is this revision own largest finding and belongs to no report. The closure paragraph asserts that every tree-derived figure stamped 74e126f is identical at the freeze because every intervening commit touches only docs/, and that predicate FAILS at fbc2ea0: git diff --name-only 74e126f fbc2ea0 | grep -vc ^docs/ returns 2, not 0, and the same diff scoped to *.py prints six paths, not nothing. The two h-mad members are h_mad_assemble_audit.py and its test, whose CONTENT changed without their MEMBERSHIP in any census here changing. The four docs/03-analysis/probes/doc-block-exec/ members are NEW tracked .py files, and this document *.py censuses are REPO-WIDE rather than h-mad-scoped, so the sheet FACT 7 closure (the probe commit does not touch h-mad, handoff, or git ls-files -- h-mad handoff) does not cover them. Re-measured at fbc2ea0, each in its own invocation: git grep -n '```bash' -- '*.py' returns EIGHT lines, not six, the two arrivals being rows 5 and 6 of grammar_corpus.2026-09-03.cd979362.py; git grep -l '```' -- '*.py' | wc -l returns 25, not 24, the one arrival being that same file. The census CONCLUSION is unchanged and is the part that matters: the narrow census still returns exactly the two extractors at :270 and :412, and both arrivals are probe fixture literals, not extractors, so the progression 21 -> 23 -> 24 -> 25 gains a fourth term for the same reason it gained its second and third. The other tree-derived figures were re-run at fbc2ea0 rather than inferred and are unchanged: 73 and its archive-exclusion 0, AC-1.7 16 and 2, the _SCANNED parametrise-twice 2, the three *.py globs, and the FIXTURE constant 1. The class, stated over the axis rather than over these two members: a freeze that touches no document is not a freeze that touches no measurement, and a corpus predicate scoped to docs/ cannot certify a census whose corpus is the whole tracked tree; the residual is that this rule fixes the *.py censuses named here and does not fix a future census whose corpus is wider still, which joins the closure by naming its own corpus in the same clause as its command. [Appended after the entry landed, and every screen this revision's own text can move re-run after the last edit. ONE DEFECT WAS FOUND BY MY OWN SCREEN AND FIXED BEFORE DONE, and it is the v1.60 failure recurring: the paragraph explaining why the sixth positive control lost its committed half REPRODUCED that control string verbatim, which took its own verbatimness count from 1 to 2; the sentence now describes the string instead of quoting it and the count is 1 again. Post-edit readings, committed half at fbc2ea0 and draft half over this revision's own body. awk needle 1/1; git-grep-n needle 1 with the trailing quote and 2 without, at both; opener census 21 openers over 11 distinct tokens at both, unchanged because this revision adds no new fenced command opener; AC body anchors 49 with 0 duplicates at both and the AC-6.4 anchor 1 at both; AC-1.2 anchor 1/1; blind-form needle 1/1; bare pgid= in the body 0/0; split_only empty over the draft with its synthetic positive firing. THE FIGURES THAT MOVED, each because this revision's own text moves it: py-pin lines 11 at fbc2ea0 and 13 over the draft, distinct pins 9 and 11, bare prose pins 3 at BOTH -- the two units staying apart under a change that touches only one of them; reproduced census output lines 8 and 10, equal at each half to the count of pins carrying a trailing colon, which is residual (c)'s equality check; the no-token scale 89 at fbc2ea0 and 100 over the draft, with the DERIVED 'up to N candidate occurrences' moved to 100 with it rather than left behind, since it is a function of the scale and not a second statement of it. Nine control strings: grep -cF returns 1 for EIGHT of them at fbc2ea0 and 1 for all nine over the draft, the sixth positive being new text this revision for the reason the body states; six positives MATCH and three true negatives NO MATCH under the pattern extracted from the published block by its own anchored needle, and the published verdict block was regenerated from that command rather than hand-padded. The collapsed 'this revision' body count is 12 over this draft against 8 at fbc2ea0; that figure has no body site and is stated only here. PRECHECK: PASS issues=0 (h_mad_precheck_doc.py --phase spec --root /Users/kimhawk/orca/skills), advisories read and all kept deliberately: the STALESHA lines on 74e126f and a8e0372 are historical stamps the freeze-sha paragraph explains and whose tree-derived figures this revision re-executed at fbc2ea0 one by one; the LINEPIN lines are FR-6's bare ordinals, residual (a) on the shape greps; the PATH lines name the module Phases 5d/5e build; the COUNT lines all sit in Version History entries, which residual (1) exempts. OWED BY OTHER DOCUMENTS, reported and NOT edited, and this is a claim about a MOVING tree that must be re-measured after the batch lands: BOTH SIBLING FIGURES WERE RE-MEASURED AT fbc2ea0 RATHER THAN CARRIED FROM v1.62, and one of the two carried premises was STALE. Measured, `git show fbc2ea0:<impl-plan> | tr '\n' ' ' | grep -o 'DETAIL_KEYS.{0,250}'`: the tuple is (missing_key:, overlap:, duplicate_key:, os_error:, pgid:, written:, failed:, skipped:, verify:, stream:, leftover:) with a trailing `# 11` comment, and the prose beside it says tests enumerate `all eleven`, so the impl-plan owes intersect: at THREE sites -- the tuple, the count comment and that prose word. Measured on the design at the same sha, its triage alternation reads missing_key|overlap|duplicate_key|os_error|pgid|written|failed|skipped|verify|stream|leftover, which is ELEVEN and complete: v1.62 reported it as ten and omitting duplicate_key, and THAT REPORT IS NOW STALE -- the gap was closed between then and the freeze, so what the design owes is a TWELFTH member and not the tenth v1.62 named. This is the OWED-ELSEWHERE-is-a-claim-about-a-moving-tree rule applying to my own document's previous entry; h-mad/SKILL.md's Helper-scripts registry gains an intersect: remedy row when 5d/5e land, which AC-4.5's bidirectional walk pins; and the design's AC-1.8 table row still says the existing test_docsections.py 'still passes unchanged', which is the half of decision 3d that belongs to the design author. ONE ITEM OWED BY THIS DOCUMENT AND DELIBERATELY NOT TAKEN THIS ROUND, because no routed decision reaches it and the brief scopes this revision to four: AC-1.8 says docsections.py reaches the module 'the way every test in h-mad/tests/ already reaches h-mad/scripts/', and the design's own codex leg filed that universal as false against the design (13 of 88 test files carry the exact sys.path.insert spelling), so the spec carries the same over-broad claim and it should be routed as spec debt rather than repaired unrouted.] [REOPEN after the first DONE, announced to the orchestrator before the edit per FACT 5, one item routed from the plan author's DONE, and every screen this reopen's own text can move re-run before the second DONE. THE ROUTED NEEDLE AND THE ACTUAL DEFECT WERE NOT THE SAME THING, and the difference changed the fix. The needle 'throwaway|heading_differential.py|grammar_corpus.py' returns 1 here, and the hit is a throwaway VENV, not a throwaway probe script: the two filename arms return 0, because this document never named an uncommitted probe by filename. The environment claim was the defect anyway, and re-probing it before writing found a second one the routing did not know about. THE VERSION THE CLAIM WAS TAKEN AT IS NOT REACHABLE. The sentence cited markdown-it-py 4.2.0 in a venv nobody can reconstruct; the committed probe's interpreter carries 2.2.0 (/opt/anaconda3/bin/python3.11 -c 'import markdown_it; print(markdown_it.__version__)'), and of the interpreters this repository's tooling reaches, /opt/anaconda3/bin/python3 and /opt/anaconda3/bin/python3.11 import it at 2.2.0 while /usr/bin/python3 and /opt/homebrew/bin/python3 do not have it at all. CITING THE PROBE'S INTERPRETER AS THE ENVIRONMENT FOR A 4.2.0 READING WOULD HAVE BEEN A FALSE SUBSTITUTION, so all six claims this document draws from that renderer were RE-MEASURED at 2.2.0 rather than restamped: the backtick-in-info-string case renders as a paragraph; '## Text ##' -> Text, '## Text\t##' -> Text, '## Text##' -> Text##; the tagged fence renders <code class="language-bash"> and the tilde-quoted tag renders as body. All six agree with the 4.2.0 reading, so BOTH are kept and the document now rests on two major versions agreeing rather than on one unreconstructable one. THREE SITES, not one, because the class is every markdown-it-py claim in this document and not the one word the needle matched: the Assumptions renderer paragraph now names the committed path docs/03-analysis/probes/doc-block-exec/grammar_corpus.2026-09-03.cd979362.py with its interpreter and its fourteen printed lines all reading OK at fbc2ea0 (run, not carried) AND states its own coverage boundary, because the orchestrator asked for the covered/uncovered split and that split belongs in the document rather than only in a report: NEITHER of the two facts that section draws is among those fourteen lines. The nearest line to the language-class fact renders a BARE ```bash info string, so it exercises the language class but never a TRAILING info-string word such as hmad:exec; the nearest to the tilde fact puts a tilde run INSIDE a backtick fence, which is the REVERSE of a tilde fence quoting a backtick one. Measured, both at 2.2.0: ```bash and ```bash hmad:exec shell=plain both render <code class="language-bash">, and the outer-tilde case renders the quoted backtick fence as body. ONE POINT OF DISAGREEMENT WITH THE ROUTING, recorded rather than silently followed: the orchestrator asked that uncovered claims name their environment as IRREPRODUCIBLE, and after this revision they are not irreproducible -- every one was re-measured at 2.2.0 through the committed probe's interpreter, which any reader can run. What is missing is a probe CASE, not a reproducible environment, and the two are different debts; writing 'irreproducible' would send r18 after the wrong one. The r18 debt is therefore stated as: add cases to the grammar probe for the backtick-in-info-string form, the tab-before-closing-run and no-space closing-hash forms, the trailing-info-string-word form, and the outer-tilde form; AC-1.6 and AC-1.7 each name that interpreter and, CRUCIALLY, each states what the probe does NOT cover, because a citation read wider than it is would be worse than the venv -- AC-1.6's backtick-in-info-string case is not among the probe's lines at all, and of AC-1.7's three forms the probe covers only the closing-hash strip, so the tab-before-closing and no-space forms stay each AC's own measurement. Residual, a concrete category: a claim that ever DISAGREES between the two versions must name which one it was taken at and stop being carried by the other; none does today. Post-reopen screens, all re-run after the last edit: nine control strings verbatim at 1 over the draft, six positives MATCH and three true negatives NO MATCH, split_only empty with its synthetic positive firing, awk needle 1, git-grep-n needle 1 with the quote and 2 without, opener census 21 over 11 distinct tokens (unchanged -- the probe path is inline, not a fenced command opener), py-pin lines 13 / distinct 11 / bare prose 3, census output lines 10, AC anchors 49 with 0 duplicates, and the routed needle now 0. The no-token scale moved with this reopen's own prose and is restated in the body with it. PRECHECK: PASS issues=0.]
