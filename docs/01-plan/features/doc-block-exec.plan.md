# Plan: doc-block-exec

## Executive Summary

Add a stdlib-only helper that runs an explicitly tagged bash block out of a markdown document, and
migrate the one existing hand-written harness onto it, so that paste-along recipes in these skills
are covered by the suite instead of by an operator discovering their defects.

## Overview

These skills document operator recipes as fenced bash blocks. Prose review and a green suite both
passed over four real defects in one such recipe — a phase-hardcoded path, an unimplemented halt,
whitespace truncation, and a bare `exit` that kills an interactive shell — and all four surfaced
only when the block was extracted and executed against fixtures. That extract-substitute-run
harness exists exactly once, inline in a test, so the next recipe worth covering pays to rewrite
it. This matters now because the recurrence counter on the candidate row reached 4, and because
the migration is cheapest while there is a single consumer to migrate.

## Scope

In scope: one new helper module with an importable API and a verdict-token CLI; one info-string
tag convention on bash fences; the tagging of exactly one existing fence; and the migration of the
**one executing** call site that hand-rolls this today in
`h-mad/tests/test_h_mad_collect_report_docs.py` (`:270` plus `run_recipe` at `:309`).

User-visible behaviour: an operator can run a documented recipe under test by hand with a single
command; a fence carrying the tag is executable and every other fence in the tree is not.

**Transport of the three reported values.** The CLI prints exactly one `DOCBLOCK:` verdict line —
that contract is not weakened. `rc` is a field on that line. The block's `stdout` and `stderr` are
**separate artifacts, not part of the verdict line**: returned as distinct fields from the
importable API, and on the CLI written to paths given by **optional** `--stdout <path>` /
`--stderr <path>` arguments. Omitted, the streams are simply not written — the API is the primary
consumer and the suite reads the fields, so requiring the flags would make every in-process caller
invent a path it never reads. A path that cannot be written is a refusal,
`DOCBLOCK: UNREADABLE reason=stream_path_unwritable`, exit 2 — checked **before** the block runs,
so a recipe is never executed only for its output to be discarded.

Left unstated, an implementation can satisfy "one verdict line" while dropping the streams, or
print the streams inline and break every consumer that parses the verdict line.

**The CLI contract, in full.** `h_mad_doc_block_exec.py <doc> --heading <h> [--index N]
[--subst K=V]... [--preamble-file PATH] [--shell-timeout SECONDS] [--stdout PATH]
[--stderr PATH]`, and nothing else — no `--all`, `--dir` or glob argument, pinned by a
parser-rejection test. `--subst` values are split once on the first `=` (a value may contain `=`;
`K=` is an empty value); no `=`, an empty key, or a repeated key is `BAD_SUBST arg=<raw>` (exit 0,
`duplicate_key:` detail for the repeat), judged before anything is reserved (AC-2.8). There are
**no abbreviated spellings**: the parser is built with
`allow_abbrev=False`, so `--shell-t` or `--pre` are rejected rather than silently accepted as
undocumented aliases (test: `test_cli_rejects_abbreviated_options`). Argument *values* are
validated by `main` and map to verdict lines — `--index` non-integer or below 1 → `BAD_INDEX`,
`--shell-timeout` non-numeric, non-finite or not positive → `BAD_TIMEOUT value=<v>` (AC-5.6), both
before any spawn; argparse's own usage error covers only *grammar* (unknown option, missing
value) and is the documented single non-`DOCBLOCK` exit. `--preamble-file` is the CLI face of AC-3.11/3.12: `main` reads the file
**before** any spawn, and an unreadable path maps to `UNREADABLE reason=preamble_unreadable`, exit
2, block not run — for a path that cannot be read **and** for a file that is not valid UTF-8,
since the preamble is read strictly and text that will execute is never silently repaired (tests:
`test_cli_unreadable_preamble_refuses_before_running` and
`test_invalid_utf8_preamble_is_unreadable` — the node ID the design's `preamble-decode-error-unwrapped` mutation binds, one name on every surface — each with a block whose side effect the
test asserts is absent; the document gets the same treatment under `doc_unreadable`). The preamble and the block are composed as
`preamble.rstrip("\n") + "\n" + text′`, with `text′` the block text *after* substitution, so the
preamble precedes what actually runs — one newline boundary, always — so a preamble file
that lacks a trailing newline cannot fuse with the recipe's first line
(test: `test_preamble_without_trailing_newline_still_precedes_the_block`, whose preamble sets a
variable and ends without `\n`, and whose block's first line reads it). The registry entry carries a detail row for that reason
like every other emittable line (AC-4.5). **Stream artifacts have overwrite semantics and are
reserved after every check, and no open ever truncates**: after extraction, selection,
substitution and every remaining pre-spawn validation (timeout, preamble readability — the info
string was validated inside `extract` and the ordinal inside `select`) have passed, both paths are
reserved with the atomic create-or-open protocol the design specifies (exclusive create records
ownership; `FileExistsError` → open the existing file *without* `O_CREAT`; `ENOENT` there →
restart the exclusive create, so every file this call creates is recorded as created), the
handles held, and only then compared for aliasing on their descriptors — append creates a missing file
and never empties an existing one. The truncation is the final write itself — `seek(0);
truncate(); write; flush(); close()`, all five inside the module's `_final_write(handle, text)` — the `close()` in a `finally`, so an `OSError` from any earlier step still releases the descriptor before the exception is mapped, and `main`'s own `try`/`finally` around both reservations closes whatever `_final_write` never reached —
because a buffered `TextIOWrapper` may defer the OS write until `flush()`/`close()` and an error
surfacing at a close outside the mapped region would be a traceback rather than
`stream_write_failed` — on those held handles after a successful run. Writes are ordered stdout
then stderr; a failure on stdout skips stderr (`failed: stdout` / `skipped: stderr`), a failure on
stderr leaves stdout as written (`written: stdout` / `failed: stderr`), and every one of those
detail lines has a registry row. **After every close the artifact is read back** and compared to
the stream text — a missing or mismatching file is `stream_write_failed` with a `verify: <stream>`
detail line (registry row), so a writer that silently did nothing cannot be reported as `RAN`
(mutation `final-write-not-verified`, test `test_final_write_readback_catches_a_silent_no_op`).
Tests: `test_stream_write_failure_after_the_run_is_a_refusal`,
`test_first_stream_write_failure_skips_the_second`,
`test_second_stream_write_failure_leaves_the_first_as_written`. So a failure to reserve the
second path finds the first untouched (a file this call created is unlinked again; a pre-existing
one keeps every byte), a refusal anywhere earlier touches neither, and a run ending in `TIMEOUT`
or `CLEANUP_FAILED` writes nothing to either. "Reserved, then failed the write" can therefore only
mean a write error on an already-open descriptor (disk full, I/O error), which maps to
`UNREADABLE reason=stream_write_failed`, exit 2, after the run — the block's `rc` is lost with the
artifact, which is the honest outcome, since the artifact the caller was promised does not exist.
Two paths naming one file are refused on the *opened* descriptors — `(st_dev, st_ino)` of the
two reserved handles compared before anything is written, so a hard link is caught as well as a
symlink or a spelling, and there is no check-to-open window (AC-3.9). A refusal there closes both
handles, unlinks one the call created, and touches no bytes. Tests:
`test_stream_paths_truncate_an_existing_file` (a pre-existing file is overwritten, not appended),
`test_stdout_survives_a_failed_stderr_reservation` (pre-existing `--stdout` bytes are identical
after `--stderr` names an unwritable path, and a `--stdout` file the call created is gone),
`test_streams_untouched_after_a_timeout`, and
`test_stream_write_failure_after_the_run_is_a_refusal` (the module's `_final_write(handle, text)`
seam is fault-injected to raise `OSError` — the fifth and last named injection, because a held
descriptor cannot be made to fail deterministically on macOS, which has no `/dev/full` — and the
verdict is `UNREADABLE reason=stream_write_failed`), and
`test_second_stream_write_failure_leaves_the_first_as_written` (only the stderr write fails; the
stdout artifact is current and the detail lines say `written: stdout` / `failed: stderr`).

**The fixture preamble is load-bearing, not a convenience.** A documented recipe may consume a
variable the surrounding prose sets rather than the block itself — the Second-surface gate block
reads `COLLECT_OUT`, supplied today by a preamble that runs the real collector. Measured (AC-3.11
carries the full pair): without the preamble the run still exits 0 and still takes the
`report_not_collected` halt branch, emitting only a `COLLECT_OUT: unbound variable` diagnostic. So
it does **not** abort — an earlier draft of this paragraph said it did, and the measurement says
otherwise. The limitation that matters is narrower and sufficient: without a supplied
`COLLECT_OUT` the block can never reach the delivered-report `GATE: PASS` branch, which AC-6.3
requires, so the FR-6 migration is impossible without a preamble parameter.

## Goals

- Address a block unambiguously and only by explicit opt-in — FR-1
- Make a substitution that would not apply a refusal rather than a silent no-op — FR-2
- Execute in a disposable cwd from `tempfile.mkdtemp()` — the stdlib call, never the `mktemp -d`
  shell utility — so a recipe's **ordinary relative** writes cannot reach the repository, under
  the shell mode the recipe declares — FR-3
- Report through the same verdict-token contract every other helper here uses — FR-4
- Bound every run without introducing an external time-bounder — FR-5
- Leave no hand-written copy of the harness behind — FR-6

## Requirements

- FR-1: Address a block by document, heading, and explicit tag
- FR-2: Substitute an explicit map, and refuse a substitution that would not apply
- FR-3: Execute in a disposable cwd under a declared shell mode
- FR-4: Verdict-token CLI following the established gate contract
- FR-5: Bounded execution without an external time-bounder
- FR-6: Migrate the existing inline harness onto the helper

## Implementation Strategy

One layer changes: `h-mad/scripts/` gains a module, `h-mad/tests/` gains its suite and a mutation
spec, `h-mad/SKILL.md` gains a Helper-scripts registry entry and one tagged fence, and one existing
test file loses its hand-rolled extraction.

The patterns to follow are already established in this repository and are not being invented here:
a helper exposes importable functions plus a thin CLI; the CLI prints exactly one verdict line;
every verdict — `RAN` and every refusal that judged readable input, `TIMEOUT` included — exits 0,
and exit 2 is reserved for the operational-error class the base invariant reserves non-zero for
— "missing/unreadable input" is its example; `UNREADABLE`, `CLEANUP_FAILED` and `LAUNCH_FAILED`
are this feature's members of that class; the registry entry and the emittable detail lines
are pinned to each other bidirectionally; and every guard gets a mutation that must be caught by a
named test.

**The count rule, stated precisely — the loose form contradicts AC-4.4.** A cannot-judge must
carry no count that could be read as a **measured result**: never an `rc=`, never a findings count,
because that is how "nothing was measured" gets read as "measured, and clean". It **may** carry a
*diagnostic* count explaining why it could not judge. The distinction is already load-bearing
elsewhere in this skill rather than being invented for this feature: `ANCHORS_DRIFTED` and
`ANCHORS_UNREADABLE` both carry `drifted=`/`unreadable=`, and `MUTATION: PRECHECK_FAILED` carries
`specs=`/`drifted=`/`unreadable=` — in each case so the verdict word chooses the first action
without hiding the other finding. (Those helpers also exit 2 on a cannot-judge; this feature does
**not** copy that, because the base Audit-gate signal discipline invariant reserves non-zero for
unreadable input, and the gate and assembler — the documented rule — exit 0 on a rejection. FR-4
states the partition.) `AMBIGUOUS blocks=<n>`
is that same shape: `n` is the number of candidate blocks that *made* the address ambiguous and is
the datum the operator needs to pass `--index`, not a result. So AC-4.4 stands and this sentence
was the error; AC-4.3 (no cannot-judge carries `rc=`) is the invariant that actually matters.

Deliberately untouched: the 67 bash fences that will not carry the tag, and the installed copy
under `~/.claude/skills` — the helper is exercised against the checkout.

**One further test file does change, and it is a scope increase the design audit forced.**
`h-mad/tests/docsections.py` currently carries its own `_fence_aware_end`. Keeping both was going
to require a differential test the Single-source contract demands, and that test is unachievable:
the existing toggle stops early inside an unbalanced four-backtick fence, which AC-1.6 forbids the
new scanner from doing. So `docsections.py` imports the authoritative bounder instead — `tests/`
depending on `scripts/` is the correct direction, it removes the duplicate rather than testing
around it, and it fixes a latent bug there. Its public signatures are unchanged and no existing
test pins the old behaviour (three files import it — `test_docsections.py`,
`test_h_mad_review_evidence.py` and `test_h_mad_wire_registry.py`, measured with
`grep -rln 'from docsections import' --include='*.py' h-mad handoff` — and all three use only
`titled_section`/`section_from`).

**The cross-directory import is specified, not implied.** `docsections.py` is imported as a
top-level module by test files that never touch `sys.path` for `scripts/`, so a bare
`from h_mad_doc_block_exec import …` inside it fails at collection. The arrangement is the one
every test in `h-mad/tests/` already uses for `SCRIPT_DIR`
(`test_h_mad_collect_report_docs.py:22`): `docsections.py` itself does
`sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))` immediately before
`import h_mad_doc_block_exec as _dbe`, so it is self-contained and never relies on another module
having inserted the path first — and the call is **module-qualified**, `_dbe.fence_aware_end(…)`,
for the same reason the FR-6 consumer's calls are: the delegation is a *connection*, and the
Connection-enforcement invariant wants it discriminated by an isolated wire mutation with the
callee intact, which needs a spy that a pre-bound alias would hide. **The bounder has a name and a contract**:
`fence_aware_end(text: str, start: int, level: int) -> int` — the offset of the next ATX heading
at `level` or shallower after `start`, ignoring fenced blocks with CommonMark backtick-run
tracking — exported in the module's `__all__` beside `extract`/`select`/`substitute`/`run_block`,
and the same function `extract` uses to bound its own section. The two call sites replace
one-for-one: `titled_section` returns
`text[match.end():_dbe.fence_aware_end(text, match.end(), level)]` and `section_from` returns
`text[offset:_dbe.fence_aware_end(text, offset, level)]` — module-qualified, as the paragraph
below requires; `_fence_aware_end` is deleted. Two tests pin it: `pytest h-mad/tests/test_docsections.py -q` run as a subprocess from the
repo root (collected **alone**), and an isolated `python3 -c "import docsections"` with the tests
directory on `sys.path` and an unrelated cwd. **The existing mutation spec moves with the code:**
`h-mad/tests/mutation-specs/docsections.json` anchors **two** of its four mutations
(`fence-tracking-removed`, `section-no-longer-owns-its-subsections`) on lines that leave
`tests/docsections.py`; the other two (`offset-anchored-bound-runs-to-end-of-file`, which mutates
`section_from`'s call, and `missing-heading-returns-empty-instead-of-failing`) anchor on lines
that remain there; the
first two re-point to the authoritative bounder in `scripts/h_mad_doc_block_exec.py` — at its
fence-state update and its heading match respectively, the same two guards they mutate today —
the third stays (it mutates `section_from`'s call, which remains), and the harness's exact-once
anchor rule makes a missed re-point a refusal rather than a silent survivor. **All four convert to
the harness's named-test form at the same time**: today the spec carries only `command` and an
informational `_killed_by` per mutation, which the harness does not execute — it scores "did the
suite go red", the form this repo has already seen ship a wrong-catcher as `ALL_CAUGHT`. The
conversion adds `"target_command": ["python3.11", "-m", "pytest", "-q"]` and moves each
`_killed_by` value — already a **full node ID**, `tests/test_docsections.py::<name>`, the only
form the harness can run as `target_command + [test]` — into that mutation's `test` key
(`tests/test_docsections.py::test_a_fenced_comment_does_not_end_the_section`,
`…::test_a_section_owns_its_subsections`, `…::test_section_from_bounds_an_offset_anchored_pin`,
`…::test_a_missing_heading_fails_loudly`), so every mutation is credited only when *its* named
test goes RED. **A fifth mutation pins the wire itself**: `docsections-delegation-reverted` restores a
local `_fence_aware_end` in `tests/docsections.py` and calls it — the callee untouched — and is
killed by `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`
(`monkeypatch.setattr(docsections._dbe, "fence_aware_end", spy)` — the alias is
`docsections.py`'s own module attribute, so the spy is installed on *that* reference, not on a
second `import h_mad_doc_block_exec` in the test — then `titled_section(...)`; the spy must
fire), while the helper's own suite stays green under that revert, which is the half proving the
test pins the wire and not the callee. The re-pointed callee mutations are the behaviour half;
this row is the connection half, and the invariant requires both. **Ordering, since the
source does not exist yet:** the module and its mutation specs are authored *together* in Phase 5
— the same task that lands `fence_aware_end` re-points `docsections.json`, re-reads the landed
lines to set each `find` to an exact-once anchor, runs `h_mad_mutation_harness.py` on both specs,
and records the named RED test in every mutation's `test` key before the task closes. A mutation
without a `test` key, or a harness run that is deferred to "later", is the silent no-op this
invariant forbids, and the 5e gate scores `ALL_CAUGHT` on the pytest summary, not on the harness's
exit code.

**FR-6 is a wiring task, not a new-behaviour task, and is planned as one.** Its deliverable is a
*connection* — the migrated call sites reaching `h_mad_doc_block_exec` — and the Connection
enforcement invariant applies: a callee suite that passes proves nothing about whether the caller
still reaches the callee. The helper's own tests could stay green while
`test_h_mad_collect_report_docs.py` quietly kept its hand-rolled extraction, and every gate
downstream of 5b would report success. So FR-6 carries a `WIRE`/`WIRE-PIN` at impl-plan time, and
discrimination is required in **both** directions: reverting the connection alone (import + call
site, helper untouched) must fail a named test in the caller while the helper's own suite still
passes, and making the call site unconditional — resolving a block regardless of the tag — must
also fail a named test. Only the pair distinguishes a wire that works from one that fires always,
and neither is visible to a whole-module revert, which removes both sides at once.

**Task-level API, and how the caller changes.** The importable surface is five functions plus
`main` (all six in `__all__`) and two
frozen dataclasses (the design carries the full signatures; this is the contract the wire is
planned against):

| symbol | signature | returns / raises |
|---|---|---|
| `extract` | `(doc: str \| Path, heading: str) -> list[Block]` — `doc` is always a **path** (`str` accepted and converted with `Path`), read strictly as UTF-8; document *text* is never accepted, so `DocUnreadable` is deterministic for every caller | every tagged block under the heading, possibly empty; raises `DocUnreadable`, `BadInfoString`, `AmbiguousHeading` — never on count |
| `select` | `(blocks: Sequence[Block], index: int \| None = None) -> Block` | raises `BlockNotFound` (0, or past the end), `AmbiguousBlock(n)` (>1, no index), `BadIndex(n)` (index < 1) |
| `substitute` | `(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]` | a new `Block` with the substituted text (frozen dataclass, `dataclasses.replace`), plus per-key counts; raises `BadSubstArg` (empty key — the rule lives here, AC-2.8), `MissingSubstitution`, `OverlappingSubstitution` |
| `run_block` | `(block: Block, *, preamble: str \| None = None, timeout: float = 30.0) -> RunResult` | `RunResult(rc, stdout, stderr, shell)` with `str` streams decoded UTF-8 `errors="replace"`; raises `BadTimeout` (before spawn), `LaunchFailed` (mkdtemp/chmod, spawn, reap), `BlockTimeout`, `CleanupFailed` |
| `extract` body normalisation | *(rule on `extract`, not a function)* | a selected fence's body is de-indented by **up to the opener's indentation** per line, as CommonMark specifies — an opener indented 1–3 spaces yields body text with those leading spaces removed and no more; recognising the fence correctly but returning un-normalised text is the gap this row closes. Test `test_indented_fence_body_is_deindented` (exact-text fixture at 1, 2 and 3 spaces, and a body line indented *less* than the opener, which is left as is); mutation `body-indent-not-stripped` |
| `fence_aware_end` | `(text: str, start: int, level: int) -> int` | offset of the next ATX heading at `level` or shallower, skipping fenced blocks under the full CommonMark fence rule — **backtick and tilde** runs of ≥3, closed only by the same character at ≥ the opening length **followed by nothing but spaces or tabs** (a ```` ```trailing ```` line is body text, not a closer — otherwise a quoting fence closes on paper and its quoted `hmad:exec` is read as executable; hostile fixture `test_closer_with_trailing_text_does_not_close`, mutation `closer-trailing-text-accepted`), opener and closer indented **0–3 spaces** (4+ is an indented code block, not a fence) — so a heading inside a `~~~` block never ends a section and an indented literal fence never opens one; **fence state is established over `text[:start]` before scanning**, so `start` may lie inside an open fence (the arbitrary offsets `docsections.section_from` passes) and a fenced `#` after it is never a boundary (`test_bounder_from_an_offset_inside_a_fence`, mutation `prefix-fence-state-skipped`); the bounder `extract` uses and `docsections` delegates to (AC-1.8). Bound to `test_bounder_ignores_a_heading_inside_a_tilde_fence` and `test_bounder_ignores_an_indented_literal_fence`, and to the design's `tilde-fence-not-tracked` and `indented-opener-accepted` mutations |

`h-mad/tests/test_h_mad_collect_report_docs.py` changes at exactly two points, and **every call
is module-qualified**: the file adds `import h_mad_doc_block_exec as dbe` after its existing
`sys.path.insert(0, str(SCRIPT_DIR))` and never `from h_mad_doc_block_exec import …`, because a
pre-bound alias is invisible to a spy installed on the module (`monkeypatch.setattr(dbe,
"extract", spy)` observes `dbe.extract(...)` and observes nothing through a bare `extract`). A
test asserts the consumer's source carries no `from h_mad_doc_block_exec import`, so the
discrimination cannot be lost by a later tidy-up. `_gate_bash_block` becomes
`dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))` and returns a `Block`;
`run_recipe(...)` stops returning `subprocess.CompletedProcess[str]` and returns the helper's
`RunResult`, calling `dbe.substitute(block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py":
shlex.quote(str(gate))})` — which returns `(Block, counts)` — and then
`dbe.run_block(substituted_block, preamble=<the COLLECT_OUT line it builds today>)` — substitution is a separate step that returns a new `Block`, so `run_block` never
substitutes and `main` can refuse a bad map before it reserves any artifact. Its four assertions
migrate field-for-field — `.stdout`/`.stderr` keep their names, `.returncode` is not read today so
nothing maps to `.rc` — and the `subprocess` import inside the test goes. Nothing else in the file
moves; `:412` keeps `re.findall` on purpose.

**Binding, for both new mutation specs — the harness executes `target_command + [test]`, so a
bare function name is not runnable and a `test` key without `target_command` is a spec error.**
`root` is `../..` (commands run from `h-mad/`, as `docsections.json` does), `target_command` is
`["python3.11", "-m", "pytest", "-q"]`, and every `test` key is a full node ID:
`tests/test_h_mad_doc_block_exec.py::<name>` for every row of `doc_block_exec.json` (whose
`command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_doc_block_exec.py", "-q"]`), and
`tests/test_h_mad_collect_report_docs.py::<name>` for every row of `doc_block_exec_wire.json`
(whose `command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_collect_report_docs.py",
"-q"]`). The names in the tables below and in the design are the `<name>` half; the impl-plan
carries them fully qualified.

**FR-6 wire tests and the mutations each kills** — `h-mad/tests/mutation-specs/doc_block_exec_wire.json`:

| mutation | mechanism | killed by |
|---|---|---|
| `wire-revert-extract` | `_gate_bash_block` resolves its block with a local `re.findall(r"```bash[^\n]*\n(.*?)```")` over `_second_surface()` instead of `dbe.extract`/`dbe.select` (the pre-migration regex made **tag-tolerant** with `[^\n]*` — the literal pre-migration `re.findall(r"```bash\n(.*?)```")` would simply fail on the tagged fence, and the wire, not the regex, is what this mutant must discriminate; helper untouched) | `test_gate_block_resolves_through_doc_block_exec` — `monkeypatch.setattr(dbe, "extract", spy)` on the consumer's module-qualified alias, and the spy must have been called (AC-6.5) |
| `wire-revert-run` | `run_recipe` runs `subprocess.run(["bash", "-c", preamble + script])` inline instead of `dbe.run_block` | `test_recipe_runs_through_run_block` — the returned value is the helper's `RunResult`, and `monkeypatch.setattr(dbe, "run_block", spy)` fires (AC-6.5) |
| `wire-unconditional` | the call site grows a fallback, `extract(...) or <legacy regex>`, so an untagged gate block is still resolved — the only way a call site can become tag-blind, since no helper API accepts untagged fences | `test_gate_block_refuses_an_untagged_recipe` — a fixture section whose gating block lacks the tag must raise `BlockNotFound` (AC-6.6) |
| `exec-scan-executes` | the `:412` text scan is made to run its block through `dbe.run_block` | `test_exec_block_scan_performs_no_execution` — `:412` asserted to call neither `run_block` nor `subprocess` (AC-6.2's exemption, pinned by a mutant that breaks it) |
| `consumer-from-import` | the consumer's `import h_mad_doc_block_exec as dbe` becomes `from h_mad_doc_block_exec import extract, select, run_block` with bare calls | `test_consumer_calls_the_helper_module_qualified` — the source carries no `from h_mad_doc_block_exec import`, so the spies above stay observable (AC-6.5's precondition, pinned) |
| `hand-rolled-extraction-widened` | a second `re.findall(r"```bash…")` is introduced on the executing path (`_gate_bash_block` falls back to it) | `test_only_the_exec_scan_hand_rolls_extraction` — exactly one `re.findall(r"```bash` remains in the file, the `:412` scan (AC-6.2's exemption cannot widen) |
| (bound in `docsections.json`, not here) | `docsections-delegation-reverted` | `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder` — listed here so the FR-6 table names all **seven** node IDs the AC-6.4 floor tuple counts |

Under `wire-revert-extract` and `wire-revert-run` the helper's own suite
(`test_h_mad_doc_block_exec.py`) still passes — that is the half that proves the failing test pins
the wire and not the callee, and the mutation harness records both runs.

The ordering constraint that shapes the work: the tag and the migration must land together.
Tagging the gate fence makes `:270`'s `re.findall` — which requires `\n` immediately after
` ```bash ` — match zero blocks. It fails loudly rather than silently, which is the good case, but
it is still a broken suite if the two are separated across tasks.

**Only `:270` is affected, and an earlier draft of this plan claimed otherwise.** Measured: the
Second-surface section holds four bash blocks; `:270` selects block 4 (containing
`h_mad_audit_gate.py`), `:412` selects block 2 (containing `exec codex`). Only block 4 is tagged,
so `:412` keeps matching and keeps working. It is also the wrong thing to migrate — it inspects a
recipe it must never run, since running it would dispatch a real agent — so it stays a text scan
by decision rather than by omission.

## Architecture Considerations

- **The temp cwd is isolation, not a sandbox — and the plan must not claim otherwise.** A fresh
  `tempfile.mkdtemp()` cwd stops a recipe's *ordinary relative* writes from reaching the repository, and
  that is the whole of the guarantee this feature tests. A block containing an absolute path, or
  an explicit `cd`, escapes it, and no cwd choice could prevent that. Claiming "side effects
  cannot reach the repository" would assert a containment property nothing here enforces; the
  tests assert the narrower, true one.
- **The tag is the security boundary.** This helper executes shell text taken from a document, so
  the property that keeps it safe is that selection is explicit and cannot be widened. That
  constrains the API shape as much as any requirement: no parameter may accept a directory, a
  glob, or an all-blocks flag, because such a parameter is how an opt-in mechanism becomes the
  blanket sweep it was built to prevent.
- **The block's exit code and the tool's verdict are different questions**, and conflating them
  would make a recipe that correctly returns non-zero indistinguishable from a harness failure.
  This mirrors the existing split between a dispatch's rc and its status token.
- **Refusal is the default response to anything unmeasured.** Absent block, ambiguous address,
  inapplicable substitution, unknown info-string key, timeout — each returns nothing rather than a
  plausible-looking zero. The failure this repository keeps re-encountering is a measurement that
  did not happen reading as a measurement that came back clean.
- **Shell mode belongs on the fence, not in the caller.** Whether a recipe is meant to be pasted
  into an interactive shell is a property of the recipe; putting it in the test would let two
  callers disagree about one block.
- **Self-containment**: stdlib only, no import of another skill's internals, no path outside this
  skill's own directory. The helper must work from a bare clone.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| `h-mad/scripts/h_mad_doc_block_exec.py` | module + CLI | FR-1, FR-2, FR-3, FR-4, FR-5 |
| `hmad:exec` fence info-string tag convention | convention | FR-1 |
| `h-mad/tests/test_h_mad_doc_block_exec.py` | tests | FR-1..FR-5 |
| `h-mad/tests/mutation-specs/doc_block_exec.json` | mutation spec | FR-1..FR-5 — 48 mutations with a full-node-ID `test` binding each — 46 of the helper's source and 2 of `h-mad/SKILL.md`'s registry rows (the AC-4.5 pin has two directions); re-derived by counting the design's matrix rows, which is the authoritative list, each with its `test` binding, enumerated row by row — mutation name, mechanism, `tests/test_h_mad_doc_block_exec.py::<name>` — in the design's §"Test Plan" under the heading "Helper mutation spec — `h-mad/tests/mutation-specs/doc_block_exec.json`, entry by entry", which is the authoritative matrix this row points at |
| Wire mutations for the migrated call site (both directions), in `h-mad/tests/mutation-specs/doc_block_exec_wire.json` | mutation spec | FR-6 |
| Helper-scripts registry entry in `h-mad/SKILL.md` | docs | FR-4 |
| Tag on the Second-surface gate fence in `h-mad/SKILL.md` | docs | FR-6 |
| Migrated `h-mad/tests/test_h_mad_collect_report_docs.py` (executing path only) | tests | FR-6 |
| `h-mad/tests/docsections.py` — drop its duplicate bounder, import the authoritative one | tests | FR-1 (AC-1.8) |
| `h-mad/tests/mutation-specs/docsections.json` — re-point the two bounder mutations at the authoritative module | mutation spec | FR-1 (AC-1.8) |
| `h-mad/tests/test_docsections.py` — gains the delegation spy test that kills `docsections-delegation-reverted` | tests | FR-1 (AC-1.8), AC-6.4 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Tagging the gate fence breaks the bare-opener extractor at `:270` | High — certain if separated | Land the tag and the migration in one task; the existing assertion on a non-empty block list makes the breakage loud if they are not. **`:412` is NOT affected** — measured, it selects a different, untagged block (`exec codex`), so it keeps matching and deliberately stays a non-executing text scan |
| A later convenience flag turns opt-in into a sweep | High | No API accepts a directory or glob; the exclusion is written into the spec's out-of-scope list and pinned by a test asserting the CLI rejects such input |
| A substitution anchor drifts and the replace silently no-ops | High | An absent key is a refusal naming the key; this is the single most load-bearing guard and gets its own mutation |
| A recipe's side effects reach the working tree | Medium | Every run in a fresh `tempfile.mkdtemp()` cwd, removed afterwards; pinned by asserting the tree is byte-identical across a run that writes files |
| "Run under `mktemp -d`" is read as the shell utility, acquiring an external dependency | Medium | The phrase came verbatim from the candidate row and is a stdlib call here: AC-3.13 asserts `tempfile.mkdtemp()`, mode `0o700`, and no `mktemp` invocation in the source |
| A timeout leaves orphan processes, as four `exec-pane` dispatches did in this repo | Medium | The full sequence, because `killpg(proc.pid, …)` only reaches a group the launch actually created: `Popen(…, start_new_session=True)` makes the child a group leader so its pgid **is** its pid → `communicate(timeout=…)` → on `TimeoutExpired`, **`proc.poll()` first** (a leader that already exited is a zombie, and on macOS `killpg` on a zombie-only group raises `PermissionError` — measured under §Measurements — whereas after `poll()` it raises `ProcessLookupError`, the one exception read as "already reaped") → `killpg(proc.pid, SIGKILL)` (never via `getpgid`, which races once the direct child has exited) → a second bounded `communicate` to drain → `rmtree(cwd)` in `finally`. Pinned by asserting no **in-group** descendant survives; a descendant that calls `os.setsid()` escapes any group kill — measured — so AC-5.2 is scoped to the group rather than claiming containment this design cannot deliver. Two races on that path are handled, not hoped away (AC-5.5): `killpg` on a group that already emptied raises `ProcessLookupError` (measured) and is read as "already reaped"; a drain `communicate` that an escapee keeps open is itself bounded, after which the pipes are closed and the leader reaped |
| Cleanup fails and the run still reports success | Medium | `rmtree` without `ignore_errors`, a read-back that the cwd is absent, and `CLEANUP_FAILED path=<p>` exit 2 on failure — with an `os_error: <text>` detail line whenever an `OSError` was recorded, so the diagnostic is never lost (AC-3.14); the fixture is an unreadable subdirectory, on which `rmtree` raises and `ignore_errors=True` retains the tree — command and output under Measurements. The permission fixture is skipped under root (`euid == 0`, where mode bits do not bind) and a deterministic fault injection runs everywhere: `shutil.rmtree` monkeypatched in the helper's namespace to raise `OSError`, and separately to silently do nothing, so both guards — the recorded error and the read-back — each have a mutation only they kill |
| The strict default hides the very defect class that motivated the feature | Medium | `shell=plain` is declarable per fence, and the shell-killing `exit` case is pinned as an explicit acceptance criterion |
| An unknown info-string key silently falls back to a default mode | Medium | Unknown keys refuse rather than default |
| The carried "68 fences" figure is stale | Low | Re-measured this session; command and output cited below under Measurements |

## Measurements

Both figures below shape this plan's scope and success criteria, so the command and its observed
output are recorded here rather than only in the author's terminal — a cited output is checkable
by a reviewer, "I verified this" is not. Re-run them at implementation time; citing them makes
staleness detectable, it does not prevent it.

**The fence census (68).** Counted over `h-mad/` and `handoff/`, excluding `archive/`, matching
opening fences only (a line *starting* ` ```bash `, so a closing fence or an indented mention is
not counted). Tests and hidden files are **not** excluded — a broad grep re-run by a reviewer will
therefore agree with this number:

```
$ python3 - <<'PY'
from pathlib import Path
tot=0; files=0
for p in sorted(Path('.').glob('*/**/*.md')):
    if 'archive' in p.parts or p.parts[0] not in ('h-mad','handoff'): continue
    n=sum(1 for l in p.read_text(encoding='utf-8',errors='replace').split('\n')
          if l.startswith('```bash'))
    if n: tot+=n; files+=1
print(f"bash fences: {tot} across {files} files")
PY
bash fences: 68 across 10 files
```

Control, to show the counter is not under-matching — the same sweep counting opening fences of
*every* language must return a strictly larger number, and does: **83** — the same script with
the counting line replaced by
`if l.startswith('```') and len(l) > 3 and l[3].isalpha()` (an opener with any language word).

**Re-measured 2026-09-03 at `a469493`, from the repository root: `68 across 10 files`, control
`83` — unchanged.** A plan audit reported `49 across 2 files` (27 in `h-mad/SKILL.md`, 22 in
`handoff/SKILL.md`); that is the count the script returns when run from a **subdirectory**, where
`p.parts[0]` is no longer `h-mad`/`handoff` for the nested references and only the two top-level
`SKILL.md` files survive the filter. The script is correct from the root, which is where its
`Path('.')` assumes it runs; a reviewer re-running it must do so from the root.

**The extractor census (2).** The consumers that would break when a fence is tagged:

```
$ grep -rn 'findall.*```bash\|split.*```bash\|re\.compile.*```bash' --include='*.py' .
h-mad/tests/test_h_mad_collect_report_docs.py:270:    blocks = re.findall(r"```bash\n(.*?)```", section, re.S)
h-mad/tests/test_h_mad_collect_report_docs.py:412:        (b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b),
```

A broader grep for the bare literal returns five hits; the other three are inline fixture strings
(`test_docsections.py:27`, `test_h_mad_assemble_tdd.py:489` and `:551`), not extractors. Control:
21 `.py` files contain a fence literal, so the narrow pattern is not under-matching. One further
consumer reads `SKILL.md` and was checked directly rather than inferred — `h-mad/tests/docsections.py:37`
bounds fences with `stripped.startswith("```")`, a **prefix** match, so an info-string tag does not
disturb it.

**The process-group reap (AC-5.2), both legs and a control.** The claim the timeout design rests
on is that `killpg(proc.pid, SIGKILL)` reaches every descendant still in the launched group, and
that a descendant which leaves the group escapes it — so AC-5.2 is scoped to the group. Both
halves were measured with the script below, which also proves the descendant existed before the
kill (the control that stops "gone" from meaning "never started") and refuses with
`PROBE VACUOUS` rather than reading a null as a negative. The last two lines are the two facts the
design's race handling (AC-5.5) depends on: macOS ships no `setsid` binary, so a binary-based
escape probe measures nothing, and `killpg` on a group that has already emptied raises
`ProcessLookupError`:

```
$ python3 -u - <<'PY'
import os, signal, subprocess, sys, tempfile, time
def alive(pid):
    try: os.kill(pid, 0); return True
    except ProcessLookupError: return False
def leg(escape):
    d = tempfile.mkdtemp(); pidf = os.path.join(d, "pid"); child = os.path.join(d, "child.py")
    open(child, "w").write("import os,time\n" + ("os.setsid()\n" if escape else "")
                           + f"open({pidf!r},'w').write(str(os.getpid()))\ntime.sleep(300)\n")
    p = subprocess.Popen(["bash", "-c", f"{sys.executable} {child} & sleep 300"],
                         start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(200):
        if os.path.exists(pidf) and open(pidf).read().strip(): break
        time.sleep(0.05)
    else: raise SystemExit("PROBE VACUOUS: descendant never wrote its pid")
    gc = int(open(pidf).read()); assert alive(gc), "control: descendant alive before the kill"
    try: p.communicate(timeout=0.5)
    except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL)
    time.sleep(0.3); survived = alive(gc)
    if survived: os.kill(gc, signal.SIGKILL)
    return gc, survived
p = subprocess.Popen(["sleep", "5"], start_new_session=True)
print("pgid == pid under start_new_session:", os.getpgid(p.pid) == p.pid); p.kill(); p.wait()
print("in-group descendant %d: survived killpg? %s   (want False)" % leg(False))
print("os.setsid() descendant %d: survived killpg? %s   (want True: escapes the group)" % leg(True))
print("setsid binary on PATH:", subprocess.run(["which", "setsid"], capture_output=True, text=True).stdout.strip() or "NONE")
p = subprocess.Popen(["true"], start_new_session=True); p.wait()
try: os.killpg(p.pid, signal.SIGKILL); print("killpg on an already-reaped group: no error")
except ProcessLookupError: print("killpg on an already-reaped group: ProcessLookupError")
PY
pgid == pid under start_new_session: True
in-group descendant 51254: survived killpg? False   (want False)
os.setsid() descendant 51694: survived killpg? True   (want True: escapes the group)
setsid binary on PATH: NONE
killpg on an already-reaped group: ProcessLookupError
```

**The cleanup fixture (AC-3.14).** The fixture block is `mkdir keep && chmod 000 keep`, and the
claim the AC rests on is that `shutil.rmtree` raises on the result while `ignore_errors=True`
retains it silently. Measured on the supported interpreter, as an unprivileged user:

```
$ python3.11 -u - <<'PY'
import os, shutil, subprocess, sys, tempfile
d = tempfile.mkdtemp()
r = subprocess.run(["bash", "-euo", "pipefail", "-c", "mkdir keep && chmod 000 keep"], cwd=d)
print("fixture block rc:", r.returncode, "| euid:", os.geteuid(), "| python:", sys.version.split()[0], "|", sys.platform)
try:
    shutil.rmtree(d); print("rmtree(d): removed with no error")
except OSError as e:
    print("rmtree(d) raised:", type(e).__name__, "on", os.path.basename(e.filename))
print("retained after the raise:", os.path.lexists(d))
shutil.rmtree(d, ignore_errors=True)
print("retained after rmtree(d, ignore_errors=True):", os.path.lexists(d), "<- silent")
os.chmod(os.path.join(d, "keep"), 0o700); shutil.rmtree(d); print("cleaned by the test's finally:", not os.path.lexists(d))
PY
fixture block rc: 0 | euid: 501 | python: 3.11.8 | darwin
rmtree(d) raised: PermissionError on keep
retained after the raise: True
retained after rmtree(d, ignore_errors=True): True <- silent
cleaned by the test's finally: True
```

Under root the mode bits do not bind and the raise does not occur, so the test skips the
permission fixture there and the fault-injected variants carry the AC (Risks table).

**The naturally emptied group (AC-5.5), and why `poll()` comes first.** The race the design
handles — the group is already gone when the reap runs — was assumed to surface as
`ProcessLookupError`. Measured, it does not on macOS unless the leader is reaped first: a leader
that has exited is a zombie, and `killpg` on a zombie-only group raises `PermissionError`; after
`proc.poll()` reaps it the same call raises `ProcessLookupError`. The fixture is a leader that
starts an `os.setsid()` descendant holding stdout and exits at once — no mock — and the same run
shows the drain timing out on the escapee's pipe and `wait()` returning immediately:

```
$ python3.11 -u - <<'PY'
import os, signal, subprocess, sys, tempfile, time
d = tempfile.mkdtemp(); child = os.path.join(d, "esc.py"); pidf = os.path.join(d, "pid")
open(child, "w").write(f"import os,time\nos.setsid()\nopen({pidf!r},'w').write(str(os.getpid()))\ntime.sleep(300)\n")
p = subprocess.Popen(["bash", "-c", f"{sys.executable} {child} & exit 0"], start_new_session=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
for _ in range(200):
    if os.path.exists(pidf) and open(pidf).read().strip(): break
    time.sleep(0.05)
esc = int(open(pidf).read())
try: p.communicate(timeout=1.0)
except subprocess.TimeoutExpired:
    print("TimeoutExpired (escapee %d holds the pipe; leader exited)" % esc)
    try: os.killpg(p.pid, signal.SIGKILL); print("killpg BEFORE poll: no error")
    except OSError as e: print("killpg BEFORE poll:", type(e).__name__)
    rc = p.poll(); print("poll() reaped the zombie leader, rc =", rc)
    try: os.killpg(p.pid, signal.SIGKILL); print("killpg AFTER poll: no error")
    except OSError as e: print("killpg AFTER poll:", type(e).__name__, "<- group empty")
    t0 = time.monotonic()
    try: p.communicate(timeout=1.0); print("drain finished")
    except subprocess.TimeoutExpired:
        p.stdout.close(); p.stderr.close(); p.wait(); print("drain timed out at %.1fs -> pipes closed, wait() returned rc %s at once" % (time.monotonic()-t0, p.returncode))
os.kill(esc, signal.SIGKILL); print("escapee reaped by the probe; python", sys.version.split()[0], sys.platform)
PY
TimeoutExpired (escapee 96921 holds the pipe; leader exited)
killpg BEFORE poll: PermissionError
poll() reaped the zombie leader, rc = 0
killpg AFTER poll: ProcessLookupError <- group empty
drain timed out at 1.0s -> pipes closed, wait() returned rc 0 at once
escapee reaped by the probe; python 3.11.8 darwin
```

So the reap sequence is `poll()` → `killpg` (catch `ProcessLookupError`) → bounded drain → close
pipes → `wait()`; without the `poll()` the natural race reports `LAUNCH_FAILED stage=reap` instead
of `TIMEOUT`, which is the mutation `poll-before-killpg-removed` and the test that kills it.

**That measurement stands and is no longer the whole story:** a later design cycle found the same
toggle mis-tracks an unbalanced inner quote inside a four-backtick fence, which is why
`docsections.py` now appears under Deliverables and Implementation Strategy — it drops its
duplicate bounder and imports the authoritative one. The tag was never the reason to change it;
the duplicate bounder is.

## Convention Prerequisites

- Feature branch created at Phase 5c before any implementation commit.
- Verdict-token discipline: read the token, never `$?`; every verdict exits 0 and only
  `UNREADABLE`/`CLEANUP_FAILED`/`LAUNCH_FAILED` exit 2 (FR-4, AC-4.2); a refusal carries no count readable
  as a **measured result** (never `rc=`), though it may carry a diagnostic count saying why it
  could not judge — see the count rule under Implementation Strategy, and AC-4.3/AC-4.4.
- Every guard mutation-tested with a per-mutation named test, scored on the pytest summary.
- Registry entry and emittable detail lines pinned bidirectionally.
- Full suite run alone before the Phase 5f gate; scoped green is not suite green.
- **Portable time bounds, and why `hmad-dispatch run --timeout` is not the mechanism here.** The
  invariant forbids the shell forms `timeout <s> <cmd>` / `gtimeout <s> <cmd>`, because both rest
  on coreutils that macOS does not ship, and prescribes `hmad-dispatch run --timeout` as the
  replacement **for a shell-command time bound**. This helper is not a shell command: it is a
  stdlib Python module whose bound is `Popen.communicate(timeout=…)` — neither forbidden form, and
  no external CLI. Routing it through `hmad-dispatch` would make a module the design requires to
  run from a bare clone depend on a wrapper script, which is the very dependency the same
  invariant family exists to prevent (§"Skill self-containment", §"No new external dependency").
  So the invariant is satisfied, not waived. Recorded explicitly because the plan previously said
  only "the bound is Python's own", which cannot be distinguished from having overlooked the rule.
- No new external dependency; no `timeout`/`gtimeout` **invocation** — the source legitimately
  contains `timeout=`, `TimeoutExpired`, `BlockTimeout` and `--shell-timeout`, and a substring
  ban would reject the design that satisfies the invariant (AC-5.3).

## Success Criteria

- Every AC in the spec passes an automated test — **49**, re-derived at spec v1.35 by
  `grep -cE '^  - AC-[0-9]+\.[0-9]+:' docs/01-plan/features/doc-block-exec.spec.md`. **The grep is
  the assertion, not this sentence**: the count went stale three times when it was carried as a
  bare number, so it is re-derived on every spec bump — but a spec bump that leaves the count at
  49 does not stale this line, which records the last version at which the re-derivation was
  done and the command that does it.
- FR-6's wire is discriminated in both directions: reverting the connection alone fails a named
  caller test while the helper's own suite still passes, and an unconditional call site fails a
  named test too.
- All three mutation specs (`doc_block_exec.json`, `doc_block_exec_wire.json`, `docsections.json`)
  report `ALL_CAUGHT`, each mutation killed by its own named `test`, scored on the pytest summary.
- The full suite passes at no lower a count than the pre-change baseline plus this feature's tests.
  **The baseline is cited, not remembered** — measured at `6b4df35`, before any implementation
  commit, from the repo root:

  ```
  $ python3.11 -m pytest --collect-only -q | tail -1
  2747 tests collected in 2.03s
  $ python3.11 -m pytest -q -p no:cacheprovider | tail -1
  2747 passed in 397.40s (0:06:37)
  ```

  The second command is quoted as it was run for the baseline; as a **gate** it is written so the
  exit status survives — a bare pipe reports `tail`'s status and would let a red suite print as
  success:

  ```
  python3.11 -m pytest -q -p no:cacheprovider > /tmp/doc_block_exec_suite.log; RC=$?
  tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"      # gate on BOTH lines
  ```

  So AC-6.4's floor is 2747 collected and the same number passing, plus every test this feature
  adds — and "every test this feature adds" is computed, not estimated: the collected count of
  `h-mad/tests/test_h_mad_doc_block_exec.py` run through the collector alone, plus a fixed tuple
  of the named node IDs added to existing files — **exactly these seven**, six in
  `h-mad/tests/test_h_mad_collect_report_docs.py`: `test_gate_block_resolves_through_doc_block_exec`, `test_recipe_runs_through_run_block`, `test_gate_block_refuses_an_untagged_recipe`, `test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`, `test_only_the_exec_scan_hand_rolls_extraction` — and, in `h-mad/tests/test_docsections.py`, `test_docsections_delegates_to_the_authoritative_bounder` (it must live beside the module it spies on, which is where `docsections.json` binds it)
  (each asserted to exist). Every other new test — FR-1..5, AC-1.8's source assertion and
  collect-alone pins, the CLI table walk — lives in the new module and is counted by the collector.
  `test_suite_floor_holds` asserts `full_collected >= 2747 + new_module + 7` from a
  `--collect-only` subprocess, which never executes tests and so cannot recurse (an env guard
  `DOCBLOCK_FLOOR_INNER=1` also makes any inner instance skip); the *pass* half is the Phase-5f
  gate command run alone, outside the suite, and recorded in the report. A deleted pre-existing
  test cannot hide behind the additions.
- `git status --porcelain` is unchanged across a run of a block that writes files.
- No hand-written ` ```bash ` extraction remains on the **executing** path of
  `h-mad/tests/test_h_mad_collect_report_docs.py` — `:270` and `run_recipe` both route through
  the helper. `:412` keeps its text scan **by decision**: it selects a different, untagged block
  (`exec codex`) that must never be run, so an executor which returns only tagged blocks cannot
  serve it. A test asserts `:412` performs no execution, so the exemption is pinned rather than
  assumed.
- Exactly one fence in the tree carries the tag at the end of this feature.

## Out-of-Scope (confirmed from spec)

- Any blanket or directory-wide sweep of the 68 bash fences under `h-mad/` and `handoff/`.
- Tagging any fence beyond the Second-surface gate block.
- A `name=` addressing key on the info string.
- A `--list` mode enumerating tagged blocks.
- Languages other than bash.
- Executing blocks in another repository or in the installed skills copy rather than the checkout.

## Next Steps

This plan and the paired design are audited together, each cycle on both surfaces (codex reads
the tree; agy reads for contradiction), until **both** documents gate `must=0 should=0` on the
**same** commit — the plan is a gated document of the design's stamp, so a plan edit re-opens the
design and vice versa. When both stamps read `CURRENT`, Phase 5 begins with the impl-plan (5a),
which pins the exact mutation anchors and node IDs this plan and the design's matrix name.

## Version History

- v1.0: Initial plan draft.
- v1.1: Audit v1 fixes: cite both measurements in a Measurements section, plan FR-6 as a wiring task with two-direction discrimination, state the stdout/stderr transport, narrow the temp-cwd isolation claim.
- v1.2: Audit v2 fixes: state the count rule precisely so it no longer contradicts AC-4.4, and specify the stdout/stderr arguments as optional with a pre-run refusal.
- v1.3: Audit v3 fixes: the count rule's third surface in Convention Prerequisites (my v1.2 sweep grepped one phrasing and missed it); name the FR-6 wire mutation spec path.
- v1.4: Track the spec's AC count to 38 after design audit v2 added AC-1.8, AC-2.6 and AC-2.7.
- v1.5: Design audit v3: the paired-plan surface of the AC-5.3 invocation-versus-substring fix.
- v1.6: Design audit v4 back-propagation: docsections.py is now in scope, replacing its duplicate bounder with an import of the authoritative one.
- v1.7: Plan re-audit v5: only the executing call site migrates — :270 and :412 select different blocks (measured, 4 blocks in the section), so the earlier 'both extractors break' claim was false and AC-6.2 was unsatisfiable; add docsections.py to Deliverables.
- v1.8: Plan re-audit v6: same, plus a risk row recording where the mktemp-d wording came from.
- v1.9: Plan re-audit v7: the AC count went stale a third time; anchor it to the spec version and record how to re-derive it.
- v1.10: Plan re-audit v7: scope AC-5.2 to the launched process group (a setsid descendant escapes, measured); refuse aliased --stdout/--stderr (AC-3.9); correct the risk row that still claimed both extractors break.
- v1.11: Plan re-audit v8: the Success Criteria still demanded removal of every hand-written extraction, contradicting the FR-6 decision that :412 keeps its non-executing text scan.
- v1.12: Plan re-audit v8: add the fixture preamble boundary (AC-3.11/AC-3.12) — without it the gate block's COLLECT_OUT is unbound under strict bash and the FR-6 migration cannot reach GATE: PASS.
- v1.13: Plan re-audit v9: track the AC count to 43 after the duplicate-heading refusal.
- v1.14: Plan re-audit v10: state why the portable-time-bounds prescription does not transfer to a stdlib module (its premise about this helper does not hold); name the full launch/reap/cleanup sequence; correct the preamble causal claim on its seventh surface.
- v1.15: Plan re-audit v10 (agy): reconcile the docsections measurement with the later decision to change that file — the tag was never the reason, the duplicate bounder is.
- v1.16: Plan re-audit v11: specify the tests/->scripts/ import (self-contained sys.path insert, collect-alone test, docsections.json re-point); cite the AC-5.2 in-group/escape/ProcessLookupError probe with its command and output; add the task-level API and caller map; name the FR-6 wire tests and the mutation each kills; track the AC count to 46 (spec v1.13); add the cleanup-verification risk row.
- v1.17: Plan re-audit v12 (codex must 2 should 1; agy clean): name the bounder fence_aware_end(text, start, level) -> int and its two call replacements in docsections; make every consumer call module-qualified (dbe.*) so the wire spies observe it, pinned by a no-from-import test; cite the collected and passing baseline (2747/2747 at 6b4df35) with commands.
- v1.18: Plan re-audit v13 (codex must 3 should 1; agy clean): state the full CLI contract including --preamble-file and its pre-spawn refusal; cite the AC-3.14 cleanup probe (python3.11, euid 501) and add the root-skip plus fault-injected fallbacks; replace 'anchors pinned at impl-plan time' with the author-together / re-read / harness / named-RED ordering; define stream overwrite and reservation semantics (stream_write_failed).
- v1.19: Plan re-audit v14 (codex must 1 should 1; agy clean): preamble/block composition rule with its no-final-newline test; allow_abbrev=False with an abbreviated-option rejection test.
- v1.20: Design audit v6 back-propagation: composition with the substituted text; probe-then-reserve stream artifacts; BAD_TIMEOUT and the values-vs-grammar CLI policy; RunResult streams are UTF-8/replace str.
- v1.21: Design audit v7 back-propagation: append-mode reservation after every check with truncation at the final write, and its four tests; docsections.json converts all four mutations to the named-test form; the AC-6.4 floor is computed by test_suite_floor_holds.
- v1.22: Design audit v8 back-propagation: exit-code partition per the base invariant; substitute returns a new Block and run_block takes no subs; the five named consumer-file tests enumerated; floor test topology (collect-only subprocess, env guard, pass half outside the suite); main's order corrected (info string in extract, ordinal in select).
- v1.23: Design audit v9 back-propagation: descriptor-level alias check; the suite gate command captures the exit status; AC count 48 (spec v1.19).
- v1.24: Design audit v11 back-propagation: --subst contract in the CLI paragraph; alias check after reservation; LaunchFailed in the run_block row; AC count 49 (spec v1.21).
- v1.25: Design audit v13 back-propagation: Deliverables and Success Criteria name all three mutation specs and point at the design's enumeration; the FR-6 pseudocode unpacks substitute's (Block, counts) tuple (agy nit).
- v1.26: Design audit v14 back-propagation: helper mutation spec is 28 mutations plus the AC-5.3 self-check.
- v1.27: Design audit v15 back-propagation: LAUNCH_FAILED named in both partition summaries; the stream-write-failure tests name the _final_write seam and the partial-write case; 31 mutations plus the self-check.
- v1.28: Design audit v16 back-propagation: 33 mutations plus the self-check.
- v1.29: Design audit v17 back-propagation: 34 mutations plus the self-check.
- v1.30: Design audit v18 (codex must 2 should 1 nit 1; agy clean): docsections delegates through a module-qualified alias and carries its own wire mutation (docsections-delegation-reverted); importer census corrected to three files with the command; 36 mutations plus the self-check.
- v1.31: Plan re-audit v16 (codex clean + 1 nit; agy must 1 + 1 nit): substitute's row names BadSubstArg; five functions, not four; AC anchor cites spec v1.26.
- v1.32: Plan re-audit v17 (codex must 2 should 1; agy clean) + design audit v21: fence_aware_end's contract names tilde runs and the 0-3 indentation rule with its tests and mutations; mutation-spec binding rule (root, command, target_command, full node IDs) for both new specs; extract's doc is a path; the naturally-emptied-group probe cited with poll()-first; five functions plus main; 37 mutations.
- v1.33: Plan re-audit v18 (codex must 1; agy clean): docsections.json test keys are full node IDs; 38 source mutations; FR-4 summary states the invariant's class rather than claiming it names the tokens.
- v1.34: Plan re-audit v19 (both surfaces clean; agy nit): the delegation spy is installed on docsections._dbe.
- v1.35: Plan re-audit v20 (codex must 2; agy clean): the body de-indentation rule on extract with its test and mutation; _final_write flushes and closes inside the mapped region; both stream-failure branches; invalid-UTF-8 preamble test; CLEANUP_FAILED os_error detail; 39 mutations.
- v1.36: Plan re-audit v21 (codex must 2 should 1, one must REFUTED — the census re-measures 68/10 from the root, the reported 49/2 is a subdirectory run; agy clean + nit): the reservation protocol carried into the plan; the mutation matrix pointed at by section; _dbe. prefix in the docsections pseudocode.
- v1.37: Plan re-audit v22 (codex should 1 + nit; agy clean): closer must be followed only by blanks, with its fixture and mutation; control census command cited; docsections.json is two-leave-two-stay; six consumer-file tests; 40 mutations.
- v1.38: Plan re-audit v23 (both surfaces clean) + design audit v27 back-propagation: seven-test floor tuple incl. the docsections delegation spy; the wire-revert-extract regex is tag-tolerant by intent; 41 mutations.
- v1.39: Plan re-audit v24 (codex must 1; agy clean): the post-close read-back verification carried into the stream paragraph; mutation accounting names the two SKILL.md rows.
- v1.40: Plan re-audit v25 (codex must 1 should 1; agy nit) + design audit v29 (codex must 1; agy must 3): the mutation count is re-derived from the design's matrix (43 = 41 + 2); the FR-6 table names all seven floor-tuple node IDs; Next Steps state the dual-surface same-commit gate; AC anchor at spec v1.34.
- v1.41: Plan re-audit v26 (codex must 1; agy clean) + design audit v30 back-propagation: fence_aware_end establishes fence state over the prefix; 48 mutations (46 + 2) after the four main/I-O rows and the prefix row.
- v1.42: Plan re-audit v28 (codex must 1 should 2; agy should 1): the timeout risk row requires poll() before killpg; _final_write closes in a finally; the AC count line records its re-derivation (49 at spec v1.35) and no longer stales on a count-preserving spec bump.
- v1.43: Plan re-audit v29 (both surfaces clean) + design audit v33 (agy must 1 + nits): the invalid-UTF-8 preamble test carries the matrix's node ID on every surface; select's Sequence[Block] hint; PATH placeholder.
- v1.44: Plan re-audit v30 (both surfaces clean) + design audit v34 (codex must 1; agy must 1 + nits): the three wire guards get mutants (six wire mutations); test_docsections.py in Deliverables; run_block's keyword type hints.
