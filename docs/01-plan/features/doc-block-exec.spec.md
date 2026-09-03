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
    blocks and the CLI prints `DOCBLOCK: NOT_FOUND` and exits 2.
  - AC-1.3: Given a section with two tagged blocks and no ordinal supplied, the CLI prints
    `DOCBLOCK: AMBIGUOUS blocks=2` and exits 2, executing nothing.
  - AC-1.4: With the same document, `--index 2` selects the second tagged block; `--index 3`
    prints `DOCBLOCK: NOT_FOUND` and exits 2.
  - AC-1.5: The section boundary is the next **ATX** heading (`#`-prefixed) at the same or
    shallower level; a tagged fence under a *later* heading is not returned for the earlier
    heading. **Setext headings (underlined with `===`/`---`) are explicitly out of scope and not
    recognised** — every document in these skills is ATX, `h-mad/tests/docsections.py` makes the
    same assumption, and AC-1.8's differential test covers it from both sides. Stated here so the
    limitation is accepted rather than discovered.
  - AC-1.6: A tag appearing inside a fence body (a fence that quotes ` ```bash hmad:exec ` as
    text) is not treated as an opening fence, **including when the enclosing fence uses a longer
    backtick run** — a four-backtick fence legitimately contains ``` lines as body text.
  - AC-1.7: **Duplicate headings refuse.** If the document contains more than one heading whose
    text and level both match, nothing is executed: `DOCBLOCK: AMBIGUOUS_HEADING count=<n>`,
    exit 2. Two identical headings share one address, and silently taking the first would run a
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
    `DOCBLOCK: BAD_INDEX index=<n>` and exit 2, executing nothing; `select(blocks, 0)` raises
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
    `DOCBLOCK: SUBST_MISSING key=<key>` and exits 2.
  - AC-2.3: The refusal names the offending key; with two absent keys, both are named on their own
    detail lines.
  - AC-2.4: Substitution is literal, not regex — a key containing regex metacharacters
    (`.`, `*`, `[`) is matched and replaced literally.
  - AC-2.5: A key occurring more than once in the block is replaced at **every** occurrence, and
    the reported occurrence count equals the number replaced.
  - AC-2.6: Counts are exact under sequential replacement: each key's count is taken immediately
    before that key's own replacement, so a value that happens to contain another key's text
    cannot inflate or deflate a reported count.
  - AC-2.7: Overlapping keys refuse rather than resolve by order — if any key is a substring of
    another, nothing is executed and the CLI prints `DOCBLOCK: SUBST_OVERLAP keys=<n>` with a
    detail line naming each overlapping pair, and exits 2. Order-dependent substitution is the
    silent-wrong-answer shape this feature exists to avoid.

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
    stderr are not merged.
  - AC-3.7: An unrecognised info-string key (e.g. `shell=fish`, `mode=x`) on a fence that
    **carries `hmad:exec`** is a refusal — `DOCBLOCK: BAD_INFO key=<k>` — and exits 2, rather than
    being ignored as a default. A fence **without** the tag is never a candidate and its info
    string is never validated: an untagged ` ```bash --frozen `, or any other prose-y info string
    elsewhere in the tree, must not make this tool refuse. Validation follows opt-in.
  - AC-3.8: `--stdout <path>` and `--stderr <path>` are **optional**; given, each receives that
    stream verbatim, and the two files differ for a block writing different text to each. Omitted,
    no stream file is written and the run still succeeds.
  - AC-3.9: `--stdout` and `--stderr` naming the **same path** refuses with
    `DOCBLOCK: UNREADABLE reason=stream_paths_alias`, exits 2, and **does not run the block** —
    one file cannot hold two streams verbatim, so the alternative is silently merging or
    truncating an artifact the caller was promised. Compared after resolution, so a symlink or a
    `./x` versus `x` spelling is caught rather than passing on a string mismatch.
  - AC-3.10: A `--stdout`/`--stderr` path that cannot be written refuses with
    `DOCBLOCK: UNREADABLE reason=stream_path_unwritable` and exits 2, **and the block does not
    run** — observable because a block with a side effect leaves none.
  - AC-3.11: **Fixture preamble.** `run_block` accepts an optional `preamble` — shell text run in
    the *same* invocation immediately before the block. It is fixture setup, never doc content:
    the block's own text is unchanged and is what the doc says. Without it the executing migration
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
  - AC-3.12: A run with a preamble reports `rc`/`stdout`/`stderr` for the combined invocation, and
    a preamble that itself fails is visible as that `rc` rather than being swallowed. On the CLI the
    preamble comes from `--preamble-file <path>`, a file rather than an inline string, so quoting
    cannot corrupt it; an unreadable preamble file refuses with
    `DOCBLOCK: UNREADABLE reason=preamble_unreadable` and does not run the block.
  - AC-3.13: The temp directory is created by `tempfile.mkdtemp()` and its mode is `0o700`
    (`stat.S_IMODE(os.stat(d).st_mode) == 0o700`), observed from inside the running block. The
    source contains no `mktemp` invocation — the same argv-token/shell-command-word test AC-5.3
    uses, so satisfying the prose by shelling out is caught rather than assumed away.
  - AC-3.14: **Cleanup is verified, not assumed.** After every run — normal, timeout, or
    exception — the temp cwd is removed *and read back absent*. If removal fails, the API raises
    `CleanupFailed(path)` and the CLI prints `DOCBLOCK: CLEANUP_FAILED path=<p>` and exits 2 —
    no `rc=`, because a run that left state behind is not the disposable measurement this FR
    promises. The fixture is a block that leaves an unreadable subdirectory
    (`mkdir keep && chmod 000 keep`); measured on this machine, `shutil.rmtree` raises
    `PermissionError` on it and `ignore_errors=True` retains the whole tree with no signal. A
    cleanup failure outranks a timeout on the same run: a retained directory is state the
    operator must act on, and both exit 2 anyway.

### FR-4: Verdict-token CLI following the established gate contract

- **Description**: The CLI prints one `DOCBLOCK:` line. Running the block successfully is the only
  verdict; everything that measured nothing is a cannot-judge. A cannot-judge carries no count
  that could be read as a **measured result** — never `rc=` — but may carry a *diagnostic* count
  saying why it could not judge, which is why `AMBIGUOUS` carries `blocks=<n>` (AC-4.4). Same shape
  as this skill's existing `ANCHORS_DRIFTED`/`MUTATION: PRECHECK_FAILED`, which exit 2 carrying
  counts so the verdict word chooses the first action without hiding the other finding.
- **Acceptance Criteria**:
  - AC-4.1: A successful run prints `DOCBLOCK: RAN rc=<n> blocks=1 shell=<strict|plain>` and exits
    **0**, including when the block's own `rc` is non-zero — the block's rc is data, not the tool's
    verdict.
  - AC-4.2: `NOT_FOUND`, `AMBIGUOUS`, `AMBIGUOUS_HEADING`, `BAD_INDEX`, `SUBST_MISSING`,
    `SUBST_OVERLAP`, `BAD_INFO`, `TIMEOUT`, `CLEANUP_FAILED` and `UNREADABLE` each exit 2.
  - AC-4.3: No cannot-judge line carries `rc=`, so a caller grepping `rc=` cannot read a
    non-measurement as a measured zero.
  - AC-4.4: `AMBIGUOUS` carries `blocks=<n>`; no other cannot-judge carries `blocks=`.
  - AC-4.5: Every detail line the script can emit has a matching remedy row in the Helper-scripts
    registry entry in `h-mad/SKILL.md`, and every row there corresponds to an emittable line
    (pinned bidirectionally by a test).

### FR-5: Bounded execution without an external time-bounder

- **Description**: Every run is time-bounded. `timeout`/`gtimeout` are forbidden by the skill's own
  rules and are not used; the bound is Python's own.
- **Acceptance Criteria**:
  - AC-5.1: A block that sleeps past the bound returns `DOCBLOCK: TIMEOUT seconds=<n>` and exits 2.
  - AC-5.2: After a timeout, **no descendant remaining in the launched process group** is alive —
    the whole group is reaped, not just the direct child. The claim is bounded deliberately: a
    descendant that leaves the group (`os.setsid()`, or a `setsid` binary where one exists) is
    outside what a group kill can reach. Measured this session — an in-group `sleep` died,
    a descendant that called `os.setsid()` **survived** — so "no descendant survives" would assert
    containment this design does not implement. A first probe using the `setsid` **binary** showed
    no escape and was **vacuous**: that binary is absent on macOS, so it measured nothing.
  - AC-5.3: The source contains no invocation of `timeout` or `gtimeout`.
  - AC-5.4: The temp cwd is removed after a timeout, exactly as after a normal run.
  - AC-5.5: **The timeout path has no unhandled race.** Two windows, both specified and both
    tested: (a) the group has already emptied by the time `killpg` runs — `ProcessLookupError`,
    reproduced on a reaped leader — is treated as "already reaped", never a traceback; (b) the
    post-kill drain `communicate` itself times out because an out-of-group descendant (AC-5.2's
    escapee) still holds the pipes — the helper closes both pipes, reaps the leader, and reports
    `TIMEOUT`. Either way the verdict is `DOCBLOCK: TIMEOUT`, exit 2, and the cwd is gone. Total
    wall time is bounded by `timeout` plus a fixed drain allowance, so FR-5's "every run is
    bounded" holds against an escapee too. (a) is a timing window no fixture can hold open, so
    its test injects the fault by monkeypatching `os.killpg` — the one permitted mock in this
    suite, named as such; (b) is driven by a real `os.setsid()` descendant.

### FR-6: Migrate the existing inline harness onto the helper

- **Description**: `h-mad/tests/test_h_mad_collect_report_docs.py` hand-writes extraction at
  `:270` and `:412` with `re.findall(r"```bash\n(.*?)```", …)`, and runs the block inline in
  `run_recipe` at `:309`. **The two extractors select different blocks** — measured: the
  Second-surface section holds four bash blocks, `:270` takes the one containing
  `h_mad_audit_gate.py` (block 4, the gate recipe), `:412` takes the one containing `exec codex`
  (block 2). Only `:270`'s block is tagged, so only `:270` breaks when the tag lands, and only
  `:270` migrates. `:412` never executes anything — it asserts the exec recipe carries
  `--out`/`--log`/`--timeout` — and running that block would dispatch a real agent, so it stays a
  text inspection deliberately. The executing migration and the first tag land together.
- **Acceptance Criteria**:
  - AC-6.1: The Second-surface gate block in `h-mad/SKILL.md` carries the `hmad:exec` tag.
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
    tests this feature adds.
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
- The `hmad:exec` info string is inert to the markdown renderers in use — GitHub and the Claude
  Code viewer both take the first info-string word as the language and ignore the remainder.
- The two extractors named in FR-6 are the only in-repo consumers that anchor on a bare
  ` ```bash\n ` opener in a file this feature tags. **Measured this session, tree-wide:**

  ```
  $ grep -rn 'findall.*```bash\|split.*```bash\|re\.compile.*```bash' --include='*.py' .
  h-mad/tests/test_h_mad_collect_report_docs.py:270:    blocks = re.findall(r"```bash\n(.*?)```", section, re.S)
  h-mad/tests/test_h_mad_collect_report_docs.py:412:        (b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b),
  ```

  A broader grep for the bare literal returns five hits; the other three
  (`test_docsections.py:27`, `test_h_mad_assemble_tdd.py:489` and `:551`) are inline fixture
  strings, not extractors. Control: 21 `.py` files contain a fence literal, so the narrow pattern
  is not under-matching. One further consumer reads `SKILL.md` and was checked directly —
  `h-mad/tests/docsections.py:37` bounds fences with `stripped.startswith("```")`, a **prefix**
  match, so an info-string tag does not disturb it.

  Re-verify at implementation time rather than trusting this block; the point of citing it is
  that a reviewer can re-run it, not that it never goes stale.
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
