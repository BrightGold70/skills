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
tag convention on bash fences; the tagging of exactly one existing fence; the migration of the
**one executing** call site that hand-rolls this today in
`h-mad/tests/test_h_mad_collect_report_docs.py` (`:270` plus `run_recipe` at `:309`); and — the
scope increase the design audit forced, tagged AC-1.8 — `h-mad/tests/docsections.py` dropping its
duplicate bounder to delegate to the authoritative one, with the three deliverables that carries
(`docsections.py`, `mutation-specs/docsections.json`, `test_docsections.py`). §Deliverables and
§Implementation Strategy carry it too, and a scope increase absent from §Scope is the surface a
downstream reader — or a 5c task split — reads first.

User-visible behaviour: an operator can run a documented recipe under test by hand with a single
command; a fence carrying the tag is executable and every other fence in the tree is not.

**Transport of the three reported values.** Every invocation that judges input prints exactly one
`DOCBLOCK:` verdict line — one *physical* line whatever the inputs, with `--help` alone excepted
(it keeps argparse's exit-0 help text and emits **zero** `DOCBLOCK:` lines; the carve-out is stated
in full in the CLI-contract paragraph below): every dynamic field (`heading=`, `arg=`, `index=`, keys,
paths, OS-error text, `leftover:`) is rendered through one escaper, `_field`, as a double-quoted
JSON string (`json.dumps(str(value), ensure_ascii=False)` plus a second pass escaping every
remaining `Cc`/`Zl`/`Zp` character — DEL, the C1 range with U+0085, U+2028/U+2029 — which
`json.dumps` leaves literal and `splitlines()` breaks on; everything else verbatim), so a caller- or document-controlled value can neither start a
second `DOCBLOCK:` line nor forge a field token inside it — `--heading 'x rc=0'` renders as
`heading="x rc=0"`, one quoted value, never a bare `rc=` on a refusal line (AC-4.3); the bare
list is exhaustive and exactly the design's — `rc=`, `blocks=`, `count=`, `keys=`, `shell=`, `stage=`,
`reason=` — and every other field, the helper-produced numbers `seconds=` and `pgid:` included, is
JSON-quoted (design v1.79 §Verdict lines; `test_newline_in_dynamic_fields_cannot_forge_a_verdict_line` drives
a newline-bearing `--heading`, `--subst` and a newline-named created `--stdout` artifact on the
AC-3.10 rollback fixture, `test_dynamic_field_cannot_forge_a_token` drives `--heading 'x rc=0'`;
mutations `field-escape-removed`, `field-quoting-removed`) — that contract is not weakened. `rc` is a field on that line. The block's `stdout` and `stderr` are
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
`K=` is an empty value); no `=`, an empty key, or a repeated key is `BAD_SUBST arg="<raw>"` (exit 0,
`duplicate_key:` detail for the repeat), judged before anything is reserved (AC-2.8). There are
**no abbreviated spellings**: the parser is built with
`allow_abbrev=False`, so `--shell-t` or `--pre` are rejected rather than silently accepted as
undocumented aliases (test: `test_parser_rejects_all_dir_and_abbreviations`). Argument *values* are
validated by `main` and map to verdict lines — `--index` non-integer or below 1 → `BAD_INDEX`,
`--shell-timeout` non-numeric, non-finite or not positive → `BAD_TIMEOUT value="<v>"` (AC-5.6), both
before any spawn; argparse grammar errors (unknown option, missing value) are routed through the
parser's overridden `error()` to `DOCBLOCK: BAD_ARGS message="<m>"`, exit 0 — there is no
non-`DOCBLOCK` exit (`--help` alone excepted: it keeps argparse's exit-0 help text and emits no
`DOCBLOCK:` line, which is why the contract is stated with that carve-out in spec AC-5.6, design
§API and impl-plan §Conventions; this document was the one of the four the v1.31 sweep missed).
**The carve-out has three surfaces in this plan, and the sweep is by claim rather than by phrase**:
this paragraph, the transport paragraph's "one *physical* line whatever the inputs" above, and
§Implementation Strategy's "the CLI prints exactly one verdict line" — every sentence that
quantifies over inputs or over emitted lines is a surface of it, which is why the v1.84 fix
grepping one phrasing landed on one of the three. The residual: `--help` is the **only** such
exception, and a second one would need the same three-surface edit.
**`exit_on_error` stays at argparse's default `True`** — an earlier draft said `False`, which
suppresses argparse's own `except ArgumentError: self.error(...)` so a *missing option value*
raised `argparse.ArgumentError` past the override and out of `main` as a non-`DOCBLOCK` traceback;
measured on python 3.11.8, the default routes all five grammar shapes to the override (design
§API carries the table) (design v1.85; `test_malformed_invocation_is_a_verdict`, mutation
`argparse-error-unrouted`). `--preamble-file` is the CLI face of AC-3.11/3.12: `main` reads the file
**before** any spawn, and an unreadable path maps to `UNREADABLE reason=preamble_unreadable`, exit
2, block not run — for a path that cannot be read **and** for a file that is not valid UTF-8,
since the preamble is read strictly and text that will execute is never silently repaired (tests:
`test_unreadable_preamble_path_refuses` and
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
ownership; `FileExistsError` → open the existing file *without* `O_CREAT` **and with
`O_NONBLOCK`**, so a reader-less FIFO fails at once with `ENXIO` instead of blocking before any
`DOCBLOCK:` line or timeout can exist; `ENOENT` there → restart the exclusive create, so every file
this call creates is recorded as created; every reserved descriptor is then `fstat`ed and must be
a **regular file** — a FIFO, socket, device or directory refuses `stream_path_unwritable`, judged
on the descriptor so there is no check-to-open race — tests
`test_stream_path_fifo_without_reader_refuses_bounded` (an `os.mkfifo` `--stdout`, refusal within
a second, block never run), mutations `nonregular-stream-accepted` and `stream-open-blocking`),
the handles held, and only then compared for aliasing on their descriptors — append creates a missing file
and never empties an existing one. The truncation is the final write itself — `seek(0);
truncate(); write; flush(); close()`, all five inside the module's `_final_write(handle, text)` — the `close()` in a `finally`, so an `OSError` from any earlier step still releases the descriptor before the exception is mapped, and `main`'s own `try`/`finally` around both reservations closes, through the one closure primitive `_close_stream(handle)`, whatever `_final_write` never reached — a backstop close that fails is recorded, never raised from the `finally`, and selected afterwards as `UNREADABLE reason=stream_close_failed` (exit 2, `os_error:` line) unless an exit-2 error is already pending, which wins with the close error as its `__context__` (tests `test_backstop_close_failure_on_timeout_is_mapped`, `test_backstop_close_failure_does_not_outrank_a_refusal`; mutations `backstop-close-unmapped`, `backstop-close-outranks-error`) —
because a buffered `TextIOWrapper` may defer the OS write until `flush()`/`close()` and an error
surfacing at a close outside the mapped region would be a traceback rather than
`stream_write_failed` — on those held handles after a successful run. Writes are ordered stdout
then stderr; a failure on stdout skips stderr (`failed: "stdout"` / `skipped: "stderr"`), a failure on
stderr leaves stdout as written (`written: "stdout"` / `failed: "stderr"`), and every one of those
detail lines has a registry row. **After every close the artifact is read back** and compared to
the stream text — a missing or mismatching file is `stream_write_failed` with a `verify: "<stream>"`
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
seam is fault-injected to raise `OSError` — the fifth named injection (the sixth is the `_close_stream` seam for the backstop close), because a held
descriptor cannot be made to fail deterministically on macOS, which has no `/dev/full` — and the
verdict is `UNREADABLE reason=stream_write_failed`), and
`test_second_stream_write_failure_leaves_the_first_as_written` (only the stderr write fails; the
stdout artifact is current and the detail lines say `written: "stdout"` / `failed: "stderr"`), and
`test_stream_path_under_a_regular_file_refuses` (AC-3.10 — a real `ENOTDIR`, no injection; mutation
`stream-open-oserror-unwrapped`).

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
spec, `h-mad/SKILL.md` gains a Helper-scripts registry entry and one tagged fence, one existing
test file loses its hand-rolled extraction, and `h-mad/tests/docsections.py` loses its duplicate
bounder (with its own mutation spec and test file) — the AC-1.8 scope increase the paragraph
below states in full.

The patterns to follow are already established in this repository and are not being invented here:
a helper exposes importable functions plus a thin CLI; the CLI prints exactly one verdict line for
every invocation that judges input (`--help` alone excepted — see the CLI contract under §Scope);
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
at `level` or shallower whose line starts at an offset `>= start` (the line adjacent to a heading `find_heading` returned is included; a line that began before a mid-line `start` is not — design v1.60, `adjacent-heading-skipped`), ignoring fenced blocks with CommonMark backtick-run
tracking — exported in the module's `__all__` beside `extract`/`select`/`substitute`/`run_block`,
and the same function `extract` uses to bound its own section. The two call sites replace
one-for-one: `titled_section` computes `(start, level) = _dbe.find_heading(text, heading)`
(keeping its own loud failure when that returns `None`) and returns
`text[start:_dbe.fence_aware_end(text, start, level)]` — its local heading `re.search` is deleted with
`_fence_aware_end` — and `section_from` returns
`text[offset:_dbe.fence_aware_end(text, offset, level)]` — module-qualified, as the paragraph
below requires; `_fence_aware_end` is deleted. **The replacement is one-for-one at the call site,
not byte-for-byte in the returned body, and the difference is a decision rather than a 5d
discovery**: today's `(?m)^(?P<marks>#+) {heading}\s*$` ends its match *before* the heading line's
newline whenever a non-blank line follows immediately (with a blank line after the heading the two
agree), while `find_heading` returns the offset *past* the heading line — so the returned section
loses one leading `\n` in that case. The leading newline is intentionally dropped: all five
`titled_section`/`section_from` assertions in `h-mad/tests/test_docsections.py` are
`in`/`not in`/`raises` and none pins bytes, which is what "no existing test pins the old
behaviour" above rests on. Two tests pin it: `pytest h-mad/tests/test_docsections.py -q` run as a subprocess from the
repo root (collected **alone**), and an isolated `python3 -c "import docsections"` with the tests
directory on `sys.path` and an unrelated cwd. **The existing mutation spec moves with the code:**
`h-mad/tests/mutation-specs/docsections.json` anchors **two** of its four mutations
(`fence-tracking-removed`, `section-no-longer-owns-its-subsections`) on lines that leave
`tests/docsections.py`; the other two (`offset-anchored-bound-runs-to-end-of-file`, which mutates
`section_from`'s call, and `missing-heading-returns-empty-instead-of-failing`) anchor on lines
that remain there; the
first two re-point to the authoritative bounder in `scripts/h_mad_doc_block_exec.py` — at its
fence-state update and its heading match respectively, the same two guards they mutate today —
the other two stay where they are, and the harness's exact-once
anchor rule makes a missed re-point a refusal rather than a silent survivor. **All four convert to
the harness's named-test form at the same time**: today the spec carries only `command` and an
informational `_killed_by` per mutation, which the harness does not execute — it scores "did the
suite go red", the form this repo has already seen ship a wrong-catcher as `ALL_CAUGHT`. The
conversion adds `"target_command": ["python3.11", "-m", "pytest", "-q"]` and moves each
`_killed_by` value — already a **full node ID**, `tests/test_docsections.py::<name>` for the four rows and the delegation row, the only
form the harness can run as `target_command + [test]` (the sixth row's key names the new module's `test_docsections_imports_from_an_unrelated_cwd`) — into that mutation's `test` key
(`tests/test_docsections.py::test_a_fenced_comment_does_not_end_the_section`,
`…::test_a_section_owns_its_subsections`, `…::test_section_from_bounds_an_offset_anchored_pin`,
`…::test_a_missing_heading_fails_loudly`), so every mutation is credited only when *its* named
test goes RED. **A fifth mutation pins the wire itself**: `docsections-delegation-reverted` is **connection-only** —
the shared `import h_mad_doc_block_exec as _dbe` line is replaced by a private instance of the
same file loaded through `importlib.util.spec_from_file_location` + `exec_module` (registered in
`sys.modules` only under its private spec name `_h_mad_doc_block_exec_private` — dataclass
processing needs `sys.modules[cls.__module__]` under `from __future__ import annotations` — and
never under the name the import system resolves), the callee untouched and no local bounder restored, so
the helper still does the real work through a second, byte-identical instance. It is killed by
`tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`, which
installs a recording fake as `sys.modules["h_mad_doc_block_exec"]`, runs
`importlib.reload(docsections)` so the module-level import re-binds `docsections._dbe` to that
fake, then calls `titled_section(...)` and `section_from(...)` and asserts the recorded call
sequence, restoring the `sys.modules` entry and reloading `docsections` again in a `finally` so
`_dbe` re-binds to the real module before any later test (pytest restores neither on its own) —
a `monkeypatch.setattr(docsections._dbe, …)` spy would not do, because it patches
whatever object `_dbe` holds, the private copy included, and so cannot see this revert. Every
other test stays green under it — the helper's own behaviour tests, the two docsections-side
hostile tests and the source guard `test_docsections_has_no_second_bounder`, whose source
predicate still holds — which is the half proving the test pins the wire and not the callee
(design audit v58: the earlier local-restore revert also failed the two hostile tests, so its
kill was confounded with behaviour). **An eighth row keeps that local-restore revert**,
`docsections-local-bounder-restored` — the old `_fence_aware_end` toggle and `_find_heading`
regex restored in `tests/docsections.py`, both call sites re-pointed, `_dbe` still imported —
bound to `tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder`, so the
source guard has a named RED of its own (the WIRE-PIN and the two hostile tests also go red
under it; its `test` key is the guard, whose file imports `docsections` only inside test
functions and so still collects under the mutant). The re-pointed callee mutations are the behaviour half;
this row is the connection half, and the invariant requires both. **Ordering, since the
source does not exist yet:** the module and its mutation specs are authored *together* in Phase 5 — the same task that lands `fence_aware_end` re-points `docsections.json`, re-reads the landed
lines to set each `find` to an exact-once anchor, runs `h_mad_mutation_harness.py` on both specs,
and records the named RED test in every mutation's `test` key before the task closes. A mutation
without a `test` key, or a harness run that is deferred to "later", is the silent no-op this
invariant forbids, and the 5e gate scores `ALL_CAUGHT` on the pytest summary, not on the harness's
exit code.

**A seventh, `docsections-heading-lookup-reverted`, pins the START of the section the same way** — `titled_section`'s own `re.search(r"(?m)^(?P<marks>#+) …")` restored while `find_heading` stays intact — and is killed by the same delegation spy, which records `find_heading` as well as `fence_aware_end`. **A sixth pins the import that carries the wire**: `docsections-syspath-setup-removed` deletes the `sys.path.insert` that makes `docsections.py`'s delegating import self-contained, and is killed by `tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd` — a fresh `python3 -c "import docsections"` with only the tests dir on `sys.path` and `cwd=tmp_path` — so collection can never depend on another module's `sys.path` side effect.

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

**Task-level API, and how the caller changes.** The importable surface is 29 names (`BadArgs` included) in
`__all__` — the seven functions `extract`, `select`, `substitute`, `run_block`, `fence_aware_end`,
`find_heading` and `main`, plus `Block`, `RunResult` and **the whole `DocBlockError` hierarchy — the
base class and its 19 subclasses** (7 + 2 + 20 = 29; the seven-plus-two-plus-*subclasses* reading
gives 28 and is the error the design names, in `docs/02-design/features/doc-block-exec.design.md`
under `## API / Interface Changes`, in the `__all__` paragraph that follows the `find_heading`
docstring — located by text and never by line, because that citation was a line pin and went stale
by 34 lines across the single design revision v1.92 → v1.93 at b68ef48; re-find it with
`grep -n 'seven-plus-two-plus' docs/02-design/features/doc-block-exec.design.md`, exactly one hit at
HEAD 048ef1f — and omitting the base costs callers the umbrella `except dbe.DocBlockError`), so callers
catch `dbe.BlockNotFound` through the public surface (design v1.85) — of which the functions and the two
frozen dataclasses (the design carries the full signatures; this is the contract the wire is
planned against):

| symbol | signature | returns / raises |
|---|---|---|
| `extract` | `(doc: str \| Path, heading: str) -> list[Block]` — `doc` is always a **path** (`str` accepted and converted with `Path`), read strictly as UTF-8; document *text* is never accepted, so `DocUnreadable` is deterministic for every caller | every tagged block under the heading, possibly empty; raises `DocUnreadable`, `BadInfoString`, `AmbiguousHeading` — never on count |
| `select` | `(blocks: Sequence[Block], index: int \| None = None) -> Block` | raises `BlockNotFound` (0, or past the end), `AmbiguousBlock(n)` (>1, no index), `BadIndex(n)` (index < 1) |
| `substitute` | `(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]` | a new `Block` with the substituted text (frozen dataclass, `dataclasses.replace`), plus per-key counts; raises `BadSubstArg("")` for an empty key (the API guard for in-process callers; `main` refuses the CLI's empty key itself while building the map, with the raw argument, and never reaches this one — AC-2.8, design v1.77), `MissingSubstitution`, `OverlappingSubstitution` |
| `run_block` | `(block: Block, *, preamble: str \| None = None, timeout: float = 30.0) -> RunResult` | `RunResult(rc, stdout, stderr, shell)` with `str` streams decoded UTF-8 `errors="replace"`; raises `BadTimeout` (before spawn), `LaunchFailed` (mkdtemp/chmod, spawn, reap, collect — the helper's own communicate/drain/close/wait on the child), `BlockTimeout`, `CleanupFailed` |
| `extract` body normalisation | *(rule on `extract`, not a function)* | a selected fence's body is de-indented by **up to the opener's indentation** per line, as CommonMark specifies — an opener indented 1–3 spaces yields body text with those leading spaces removed and no more; recognising the fence correctly but returning un-normalised text is the gap this row closes. Test `test_indented_fence_body_is_deindented` (exact-text fixture at 1, 2 and 3 spaces, and a body line indented *less* than the opener, which is left as is); mutation `body-indent-not-stripped` |
| `find_heading` | `(text: str, heading: str) -> tuple[int, int] \| None` | offset just past the matching ATX heading line and its level, found among the scanner's heading events only — never inside a fence; `None` when absent; `AmbiguousHeading(n)` on more than one. **`heading` takes one of two forms, told apart by the request itself, full form first**: a request that parses as an ATX line by the scanner's own predicate — 0–3 spaces, 1–6 `#`, then a space, a tab or end of line (`## Text`, `##\tText`, a title-less `##`; what `extract` and the CLI `--heading` pass) matches on normalized title **and** level; any other request (`Text`, what `docsections.titled_section` passes) is the bare form and matches the title at any level. A title that itself begins with an ATX prefix is reachable only in full form — the one exclusion, harmless to every live caller (design §Scanning; `test_heading_form_precedence_full_wins`, mutation `form-precedence-bare-first`) |
| `fence_aware_end` | `(text: str, start: int, level: int) -> int` | offset of the next ATX heading at `level` or shallower whose line starts at an offset `>= start` (an adjacent heading bounds the section at `start` itself), skipping fenced blocks under the full CommonMark fence rule — **backtick and tilde** runs of ≥3, closed only by the same character at ≥ the opening length **followed by nothing but spaces or tabs**, a backtick opener voided by any backtick in its info string (CommonMark; measured on both renderers — `backtick-in-info-accepted` / `test_backtick_in_info_string_is_not_an_opener`) (a ```` ```trailing ```` line is body text, not a closer — otherwise a quoting fence closes on paper and its quoted `hmad:exec` is read as executable; hostile fixture `test_closer_with_trailing_text_does_not_close`, mutation `closer-trailing-text-accepted`), opener and closer indented **0–3 spaces** (4+ is an indented code block, not a fence) — so a heading inside a `~~~` block never ends a section and an indented literal fence never opens one; **fence state is established over complete source lines through the line containing `start` — never a `text[:start]` slice, which can cut a line after its marker run and fake a closer — and boundaries are considered only at line starts after `start`**, so `start` may lie inside an open fence (the arbitrary offsets `docsections.section_from` passes) and a fenced `#` after it is never a boundary (`test_bounder_from_an_offset_inside_a_fence`, mutation `prefix-fence-state-skipped`); the bounder `extract` uses and `docsections` delegates to (AC-1.8). **The fence grammar has one home**: a private generator `_fence_events(text)` that both `extract` and `fence_aware_end` consume, so the two surfaces cannot diverge by construction; the fence-grammar mutations anchor in it, `test_fence_events_trace_on_every_hostile_fixture` asserts its exact event trace over every hostile fixture, and `scanner-duplicated-in-consumer` (a private fence toggle regrown inside `extract`) is killed by `test_extract_has_no_fence_state_of_its_own`, a source assertion. Bound to `test_bounder_ignores_a_heading_inside_a_tilde_fence` and `test_bounder_ignores_an_indented_literal_fence`, and to the design's `tilde-fence-not-tracked` and `indented-opener-accepted` mutations |

`h-mad/tests/test_h_mad_collect_report_docs.py` changes in the resolver and the runner only —
**stated as what does not move rather than as a count**, since the paragraph's own list runs to
five edit regions and Success Criteria adds six new test functions to the same file, so any
bare count contradicts its own enumeration. What does not move is the load-bearing claim, and it
is what makes the two text-pin callers safe: the three `_gate_bash_block()` callers (`:281`,
`:310`, `:368`, measured) keep their types, `:412` keeps its `re.findall` text scan, and
`.returncode` is read nowhere in the file (measured), so nothing maps to `.rc`. And **every call
is module-qualified**: the file adds `import h_mad_doc_block_exec as dbe` after its existing
`sys.path.insert(0, str(SCRIPT_DIR))` and never `from h_mad_doc_block_exec import …`, because a
pre-bound alias is invisible to a spy installed on the module (`monkeypatch.setattr(dbe,
"extract", spy)` observes `dbe.extract(...)` and observes nothing through a bare `extract`). A
test asserts the consumer's source carries no `from h_mad_doc_block_exec import`, so the
discrimination cannot be lost by a later tidy-up. **The resolver splits in two so the file's
three existing callers keep their types**: a new `_gate_block() -> dbe.Block` returns
`dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))`, and the existing
`_gate_bash_block() -> str` becomes `return _gate_block().text` — so the two text-pin callers
(`:281`'s `.index`/slicing and `:368`'s `.splitlines()`, measured) are untouched, and "nothing else
in the file moves" stays true;
`run_recipe(...)`, hoisted to the module-level `_run_recipe(...)` so a pin can spy it, stops returning `subprocess.CompletedProcess[str]` and returns the helper's
`RunResult`, deriving its two script paths itself — `collector = SCRIPT_DIR / "h_mad_collect_report.py"`
and `gate = SCRIPT_DIR / "h_mad_audit_gate.py"`, the locals today's nested `run_recipe` computes
the same way, so the hoist leaves no unbound name and "nothing else in the file moves" still holds
(`SCRIPT_DIR` is already module-level) — calling `_gate_block()` and then `dbe.substitute(block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py":
shlex.quote(str(gate))})` — bound as `substituted_block, _counts = dbe.substitute(…)`, since it returns `(Block, counts)` and only the `Block` reaches the runner — and then
`dbe.run_block(substituted_block, preamble=<the COLLECT_OUT line it builds today>, timeout=60.0)` — substitution is a separate step that returns a new `Block`, so `run_block` never
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
| `wire-revert-extract` | `_gate_block` resolves its block with a local `re.findall(r"```bash[^\n]*\n(.*?)```")` over `_second_surface()` instead of `dbe.extract`/`dbe.select` (and `_gate_bash_block` returns that string) (the pre-migration regex made **tag-tolerant** with `[^\n]*` — the literal pre-migration `re.findall(r"```bash\n(.*?)```")` would simply fail on the tagged fence, and the wire, not the regex, is what this mutant must discriminate; helper untouched) | `test_gate_block_resolves_through_doc_block_exec` — `monkeypatch.setattr(dbe, "extract", spy)` on the consumer's module-qualified alias, and the spy must have been called (AC-6.5) |
| `wire-revert-select` | `_gate_block` keeps `dbe.extract` but takes `blocks[0]` (or raises locally) instead of `dbe.select`, callee intact | `test_gate_block_resolves_through_doc_block_exec` — the pin also spies `dbe.select` (one call, the extracted list, `index=None`) |
| `wire-revert-run` | `_run_recipe` runs `subprocess.run(["bash", "-c", preamble + script])` inline instead of `dbe.run_block` | `test_recipe_runs_through_run_block` — the returned value is the helper's `RunResult`, and `monkeypatch.setattr(dbe, "run_block", spy)` fires (AC-6.5) |
| `wire-revert-substitute` | `_run_recipe` rewrites the installed gate path with `str.replace` instead of `dbe.substitute`, callee intact | `test_recipe_runs_through_run_block` — the pin also spies `dbe.substitute` (one call, the gate block, the one-key map) |
| `wire-unconditional` | the call site grows a fallback, `extract(...) or <legacy regex>`, so an untagged gate block is still resolved — the only way a call site can become tag-blind, since no helper API accepts untagged fences | `test_gate_block_refuses_an_untagged_recipe` — a fixture section whose gating block lacks the tag must raise `BlockNotFound` (AC-6.6) |
| `exec-scan-executes` | the `:412` text scan is made to run its block through `dbe.run_block` | `test_exec_block_scan_performs_no_execution` — `:412` asserted to call neither `run_block` nor `subprocess` (AC-6.2's exemption, pinned by a mutant that breaks it) |
| `consumer-from-import` | the consumer gains `from h_mad_doc_block_exec import extract, select, run_block, substitute` beside its alias and every helper call goes bare — one contiguous replacement at the call region, the alias line untouched (the harness applies one `str.replace` per row) | `test_consumer_calls_the_helper_module_qualified` — the source carries no `from h_mad_doc_block_exec import`, so the spies above stay observable (AC-6.5's precondition, pinned) |
| `hand-rolled-extraction-widened` | a second `re.findall(r"```bash…")` is introduced on the executing path (`_gate_bash_block` falls back to it) | `test_only_the_exec_scan_hand_rolls_extraction` — exactly one `re.findall(r"```bash` remains in the file, the `:412` scan (AC-6.2's exemption cannot widen) |
| (bound in `docsections.json`, not here) | `docsections-heading-lookup-reverted` | `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder` — `titled_section`'s local heading `re.search` restored with `find_heading` untouched; the spy's `find_heading` recorder sees no call |
| (bound in `docsections.json`, not here) | `docsections-syspath-setup-removed` | `tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd` — the delegating import's own `sys.path.insert` deleted; a fresh process with only the tests dir on `sys.path` must still import `docsections` (not a floor-tuple node: it lives in the new module) |
| (bound in `docsections.json`, not here) | `docsections-delegation-reverted` | `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder` — listed here so the FR-6 table names all **seven** node IDs the AC-6.4 floor tuple counts |
| (bound in `docsections.json`, not here) | `docsections-local-bounder-restored` | `tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder` — the old local toggle and heading regex restored with `_dbe` still imported; the source guard's own named RED (not a floor-tuple node: it lives in the new module) |

Under `wire-revert-extract` and `wire-revert-run` the helper's own suite
(`test_h_mad_doc_block_exec.py`) still passes — that is the half that proves the failing test pins
the wire and not the callee, and the mutation harness records both runs.

The ordering constraint that shapes the work: the tag and the migration must land together.
Tagging the gate fence makes `:270`'s `re.findall` — which requires `\n` immediately after
` ```bash ` — match **3 of the section's 4 blocks instead of 4** (measured at `e8eaf6f`: before the
tag 4 blocks, 1 of them gating; after, 3 blocks, 0 gating). What goes to zero is the
`h_mad_audit_gate.py` filter on the next line, so the loud failure is `_gate_bash_block`'s
`assert gating`, not an empty `findall` — an implementer looking for the latter will not find it.
It fails loudly rather than silently, which is the good case, but it is still a broken suite if the
two are separated across tasks.

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
| `h-mad/tests/mutation-specs/doc_block_exec.json` | mutation spec | FR-1..FR-5 — 81 mutations with a full-node-ID `test` binding each — **80 of the helper's source and 1 of `h-mad/SKILL.md`**. The split is not carried: it is re-derived from the matrix's own mechanism column, by counting the rows that name `SKILL.md` as **the mutation target**, so a row added later re-derives instead of drifting. Today exactly one does — `registry-row-removed`, "one remedy row deleted from the `SKILL.md` Helper-scripts entry (the mutation targets `SKILL.md`)". The AC-4.5 pin still has two directions and therefore two rows, but only one of them mutates the registry: the other, `detail-line-undocumented`, mutates the **helper** ("the helper renames one emitted detail line (`missing_key:` → `absent_key:`)"), so its `file` key is the helper's source, not `SKILL.md` — an implementer who writes `"file": "h-mad/SKILL.md"` there gets an anchor that cannot match, which the harness refuses. Each row's `test` binding is enumerated row by row — mutation name, mechanism, `tests/test_h_mad_doc_block_exec.py::<name>` — in the design's §"Test Plan", under the bolded lead-in "Helper mutation spec — `h-mad/tests/mutation-specs/doc_block_exec.json`, entry by entry" (a lead-in paragraph inside the `## Test Plan` heading, not a heading of its own), which is the authoritative matrix this row points at |
| Wire mutations for the migrated call site (both directions), in `h-mad/tests/mutation-specs/doc_block_exec_wire.json` | mutation spec | FR-6 |
| Helper-scripts registry entry in `h-mad/SKILL.md` | docs | FR-4 |
| Tag on the Second-surface gate fence in `h-mad/SKILL.md` | docs | FR-6 |
| Migrated `h-mad/tests/test_h_mad_collect_report_docs.py` (executing path only) | tests | FR-6 |
| `h-mad/tests/docsections.py` — drop its duplicate bounder, import the authoritative one | tests | FR-1 (AC-1.8) |
| `h-mad/tests/mutation-specs/docsections.json` — re-point the two bounder mutations at the authoritative module, convert every row to the named-test form (`target_command` + a full-node-ID `test` key), and add the four connection rows `docsections-delegation-reverted`, `docsections-syspath-setup-removed`, `docsections-heading-lookup-reverted`, `docsections-local-bounder-restored` — 8 rows | mutation spec | FR-1 (AC-1.8) |
| `h-mad/tests/test_docsections.py` — gains the delegation spy test that kills `docsections-delegation-reverted` | tests | FR-1 (AC-1.8), AC-6.4 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Tagging the gate fence breaks the bare-opener extractor at `:270` | High — certain if separated | Land the tag and the migration in one task; the existing assertion on a non-empty block list makes the breakage loud if they are not. **`:412` is NOT affected** — measured, it selects a different, untagged block (`exec codex`), so it keeps matching and deliberately stays a non-executing text scan |
| A later convenience flag turns opt-in into a sweep | High | No API accepts a directory or glob; the exclusion is written into the spec's out-of-scope list and pinned by a test asserting the CLI rejects such input |
| A substitution anchor drifts and the replace silently no-ops | High | An absent key is a refusal naming the key; this is the single most load-bearing guard and gets its own mutation |
| A recipe's side effects reach the working tree | Medium | Every run in a fresh `tempfile.mkdtemp()` cwd **passed to the launch as `Popen(…, cwd=cwd, …)`** — creating the directory does nothing to the child's cwd by itself, so the keyword is the guarantee (mutation `cwd-not-passed`, test `test_block_runs_in_the_temp_cwd`) — removed afterwards; pinned by asserting the tree is byte-identical across a run that writes files |
| "Run under `mktemp -d`" is read as the shell utility, acquiring an external dependency | Medium | The phrase came verbatim from the candidate row and is a stdlib call here: AC-3.13 asserts `tempfile.mkdtemp()`, mode `0o700`, and no `mktemp` invocation in the source |
| A timeout leaves orphan processes, as four `exec-pane` dispatches did in this repo | Medium | The full sequence, because `killpg(proc.pid, …)` only reaches a group the launch actually created: `Popen(…, start_new_session=True)` makes the child a group leader so its pgid **is** its pid → `communicate(timeout=…)` → on `TimeoutExpired`, **`proc.poll()` first** (a leader that already exited is a zombie, and on macOS `killpg` on a zombie-only group raises `PermissionError` — measured under §Measurements — whereas after `poll()` it raises `ProcessLookupError`, the one exception read as "already reaped") → `killpg(proc.pid, SIGKILL)` (never via `getpgid`, which races once the direct child has exited) → a second bounded `communicate` to drain → `rmtree(cwd)` in `finally`. Pinned by asserting no **in-group** descendant survives; a descendant that calls `os.setsid()` escapes any group kill — measured — so AC-5.2 is scoped to the group rather than claiming containment this design cannot deliver. Two races on that path are handled, not hoped away (AC-5.5): `killpg` on a group that already emptied raises `ProcessLookupError` (measured) and is read as "already reaped"; a drain `communicate` that an escapee keeps open is itself bounded, after which the pipes are closed and the leader reaped |
| Cleanup fails and the run still reports success | Medium | `rmtree` without `ignore_errors`, a read-back that the cwd is absent, and `CLEANUP_FAILED path="<p>"` exit 2 on failure — with an `os_error: "<text>"` detail line whenever an `OSError` was recorded, so the diagnostic is never lost (AC-3.14); the fixture is an unreadable subdirectory, on which `rmtree` raises and `ignore_errors=True` retains the tree — command and output under Measurements. The permission fixture is skipped under root (`euid == 0`, where mode bits do not bind) and a deterministic fault injection runs everywhere: `shutil.rmtree` monkeypatched in the helper's namespace to raise `OSError`, and separately to silently do nothing, so both guards — the recorded error and the read-back — each have a mutation only they kill |
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

**This census is corpus-invariant, and that was measured rather than assumed.** The script above
walks a filesystem glob, which returns the 30 `*.md` files rather than the tracked 25 (§Scanning's
corpus, stated with the heading measurements below). Re-run at `1861157` over both: `68 across 10
files`, control `83`, **identical on each** — the five `.pytest_cache/README.md` artifacts carry no
fence at all, so unlike the heading counts this one never depended on which corpus was walked.

**AC-6.1's tree sweep is deliberately NOT this filter, and must not be harmonised with it.** The
spec reaches AC-6.1's scope by reference to this census ("the same sweep as the plan's fence
census"), so the distinction has to be stated here or the reference imports the wrong one: the
census is a one-off human measurement and may use `git ls-files`, but AC-6.1's sweep is a **test**
that must still count a newly written, not-yet-tracked `.md` under the two roots — precisely the
document a `git ls-files` sweep would miss and the guard exists to catch. It therefore excludes
build output by excluding any path with a **dot-directory component** instead (design v1.93
§AC-6.1). Two realisations of one exclusion, on purpose.

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
(`test_docsections.py:27`, `test_h_mad_assemble_tdd.py:489` and `:551`), not extractors. Control —
**the command, not just the number**, because this was the one figure in this plan carried without
one, and that is what let it drift unnoticed:

```
$ git grep -l '```' -- '*.py' | wc -l
23
```

**23** `.py` files contain **a fence literal of any language** (measured at `1861157`; the quantity
is deliberately the broad one — `git grep -l '```bash' -- '*.py' | wc -l` returns **3**, the *bash*
fence literal, a different and narrower measurement, and either serves the argument, so the one
meant is named). So the narrow pattern is not under-matching. The number was carried as a bare
`21`: that was its true value at `6b4df35`, and `b59e05e` — the same commit that
moved the suite floor from 2747 to 2748 — moved this control to 23 too, and only the floor was
re-measured. Re-run the command rather than trusting the number. One further
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

**The reader-less FIFO (AC-3.10).** The reservation's existing-file arm opens with `O_NONBLOCK`
because a blocking open of a FIFO with no reader never returns; the claim that the non-blocking
open fails *at once* with `ENXIO`, and that a FIFO which does have a reader is still refused by
the regular-file check, was measured on the supported interpreter:

```
$ python3.11 -u - <<'PY'
import os, stat, sys, tempfile, time, errno
d = tempfile.mkdtemp(); p = os.path.join(d, "out.fifo"); os.mkfifo(p)
t0 = time.monotonic()
try:
    fd = os.open(p, os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK); os.close(fd); print("O_NONBLOCK open on a reader-less FIFO: SUCCEEDED (unexpected)")
except OSError as e:
    print("O_NONBLOCK open on a reader-less FIFO: %s errno=%d (%s) after %.4fs" % (type(e).__name__, e.errno, errno.errorcode[e.errno], time.monotonic() - t0))
r = os.open(p, os.O_RDONLY | os.O_NONBLOCK)      # a reader now exists, so the writer open succeeds -> the S_ISREG check must refuse it
fd = os.open(p, os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK); st = os.fstat(fd)
print("with a reader present: open succeeds; S_ISREG=%s S_ISFIFO=%s -> refused by the regular-file check" % (stat.S_ISREG(st.st_mode), stat.S_ISFIFO(st.st_mode)))
os.close(fd); os.close(r); os.unlink(p); os.rmdir(d); print("python", sys.version.split()[0], sys.platform)
PY
O_NONBLOCK open on a reader-less FIFO: OSError errno=6 (ENXIO) after 0.0000s
with a reader present: open succeeds; S_ISREG=False S_ISFIFO=True -> refused by the regular-file check
python 3.11.8 darwin
```

**The naturally emptied group (AC-5.5), and why `poll()` comes first.** The race the design
handles — the group is already gone when the reap runs — was assumed to surface as
`ProcessLookupError`. Measured, it does not on macOS unless the leader is reaped first: a leader
that has exited is a zombie, and `killpg` on a zombie-only group raises `PermissionError`; after
`proc.poll()` reaps it the same call raises `ProcessLookupError`. The fixture is a leader that
starts an `os.setsid()` descendant holding stdout and exits at once — no mock — and the same run
shows the drain timing out on the escapee's pipe and `wait()` returning immediately (the probe's
bare `p.wait()` is the measurement; the helper's own call is `wait(timeout=DRAIN_SECONDS)`, below):

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
pipes → `wait(timeout=DRAIN_SECONDS)`, taken only when the group was signalled: a delivered
`SIGKILL` is not a completion deadline, so the wait is bounded like the drain, and its
`TimeoutExpired` becomes `LAUNCH_FAILED stage=reap` with the pending `BlockTimeout` as
`__context__` — the helper's wall time is at most `timeout + 2 * DRAIN_SECONDS` plus teardown
(`test_wait_after_kill_is_bounded`; mutations `wait-unbounded`, `wait-expiry-unmapped` — design
v1.73). Without the `poll()` the natural race reports `LAUNCH_FAILED stage=reap` instead
of `TIMEOUT`, which is the mutation `poll-before-killpg-removed` and the test that kills it.

**That measurement stands and is no longer the whole story:** a later design cycle found the same
toggle mis-tracks an unbalanced inner quote inside a four-backtick fence, which is why
`docsections.py` now appears under Deliverables and Implementation Strategy — it drops its
duplicate bounder and imports the authoritative one. The tag was never the reason to change it;
the duplicate bounder is.

- **The corpus for every `*.md`-scoped measurement below is the tracked one**, defined as design
  v1.93 §Scanning defines it — `git ls-files -- h-mad handoff` filtered to `*.md` with `archive/`
  excluded, **25 files** — and not a filesystem glob. The glob returns **30**: the five extra are
  untracked, gitignored `.pytest_cache/README.md` artifacts, which exist only on a tree where
  pytest has run and each carry `# pytest cache directory #`. Those five are build output, they are
  not documents this feature reads, and they made the heading measurements irreproducible on a
  clean clone. Every figure below is therefore given on both corpora, so the contamination is
  visible rather than assumed away:

  ```
  $ git ls-files -- h-mad handoff | grep '\.md$' | grep -v '/archive/' | wc -l
  25
  ```

- **Heading selector differential** — the old `docsections.titled_section` regex
  (`^(?P<marks>#+) …\s*$`) against the CommonMark ATX selector `find_heading` implements, fence-aware
  on the new side (throwaway `heading_differential.py`, one `re.match` per line per selector),
  re-derived at `1861157` over both corpora:

  ```
  $ python3.11 heading_differential.py
  --- TRACKED (git ls-files)
  files=25 both=263 old_only=76 new_only=0
  softening shapes: closing_hash=0 tab_form=0 titleless=0
  --- GLOB (filesystem)
  files=30 both=268 old_only=76 new_only=0
  softening shapes: closing_hash=5 tab_form=0 titleless=0
  OLD-ONLY h-mad/SKILL.md 83 # WIRING: PASS
  OLD-ONLY h-mad/SKILL.md 84 # WIRING: FAIL issues=1  +  detail lines
  OLD-ONLY h-mad/SKILL.md 85 # WIRING: UNKNOWN reason=no_settings      (exit 2 — nothing was read)
  ```

  `new_only=0` and `old_only=76` hold on **both** corpora, so the differential's two load-bearing
  conclusions never depended on the contamination. `old_only=76`: all 76 are `#` comment lines
  inside fenced code the old regex read as headings; the migration narrows the guard.

  **The `new_only=0` justification did depend on it, and is restated correctly.** The base
  Guard-narrowing invariant's "every softened outcome" set is about heading *identity*, not about
  which lines are recognised — a `## x ##` line is a heading to both selectors and lands in `both`,
  never in `new_only`, while only the new selector strips the closing run and so answers a request
  for `x`. Counted as identities: over the tracked 25 the softened shapes are `closing_hash=0
  tab_form=0 titleless=0`, so the set is genuinely empty. Over the glob 30 `closing_hash=5` — the
  five `# pytest cache directory #` lines, one per `.pytest_cache/README.md`. The old text claimed
  `## x ##` "occurs nowhere" while measuring a corpus in which it occurred five times; the claim is
  true of the corpus this feature actually reads, and was false of the corpus that was measured.

  **`both` moved 266 → 268 on the glob (261 → 263 tracked), and nothing is wrong with either.**
  The `266` was correct when recorded at `1f5b30e`; `h-mad/SKILL.md` has since gained exactly two
  `###` headings — "Close the class, never the instance" (`e8eaf6f`) and "Record a rejected finding
  in the rejections ledger, never in a gated document" (`ff0a278`/`11a7db7`) — measured by diffing
  the heading lines between the two revisions. `both` is not a conclusion this plan rests on; it
  drifts with any documentation edit under the two roots, which is why the command is recorded
  beside it and the number is not to be carried.
- **Setext census** — the ATX-only assumption measured directly rather than through the selector
  differential (both of whose selectors ignore Setext): a fence-aware scan for a `===`/`---`
  underline line immediately after a paragraph line (CommonMark §4.3; YAML front matter skipped;
  list, table, blockquote and indented-code lines are not paragraphs) over the same corpus, run in
  the same script as the differential above and re-derived at `1861157` on both readings of it:

  ```
  $ python3.11 heading_differential.py
  --- TRACKED (git ls-files)
  files=25 setext_headings=0
  --- GLOB (filesystem)
  files=30 setext_headings=0
  ```

  So no document `docsections` or the helper reads today bounds wrongly under the ATX-only grammar;
  a Setext heading that arrives later is still unrecognised silently, which the design carries as a
  limitation rather than a guard.
- **Scanner grammar corpus** — every fence and ATX rule the scanner implements, rendered through
  markdown-it-py 2.2.0 (interpreter-local) AND 4.2.0 (the spec's throwaway-venv version, installed
  with `pip install --target` for this run), CommonMark preset on both, 14 of 14 agreeing on each; the
  script is a throwaway (`grammar_corpus.py`, one `md.render(src)` per case, a needle asserted on
  the HTML), and its output is what the design's §Scanning cites:

  ```
  $ python3.11 -c "import markdown_it; print(markdown_it.__version__)"
  2.2.0
  $ python3.11 grammar_corpus.py
  OK  opener at 3 spaces IS a fence                | '<pre><code class="language-bash">X\n</code></pre>'
  OK  opener at 4 spaces is NOT a fence            | '<pre><code>```bash\n</code></pre>\n<p>X</p>'
  OK  closer shorter than opener does not close    | '<pre><code>X\n```\nY\n</code></pre>'
  OK  closer with trailing text does not close     | '<pre><code>X\n``` trailing\nY\n</code></pre>'
  OK  closer at 4 spaces does not close            | '<pre><code>X\n    ```\nY\n</code></pre>'
  OK  tilde does not close a backtick fence        | '<pre><code>X\n~~~\nY\n</code></pre>'
  OK  body de-indented by opener indent (2)        | '<pre><code>a\nb\n c\n</code></pre>'
  OK  #hashtag is not a heading                    | '<p>#hashtag</p>'
  OK  seven hashes is not a heading                | '<p>####### x</p>'
  OK  4-space-indented ## is not a heading         | '<pre><code>## x\n</code></pre>'
  OK  3-space-indented ## IS a heading             | '<h2>x</h2>'
  OK  closing hashes are stripped                  | '<h2>x</h2>'
  OK  tab after hashes IS a heading                | '<h2>x</h2>'
  OK  heading inside a fence is not a heading      | '<pre><code>## x\n</code></pre>'
  ```

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

- Every AC in the spec passes an automated test — **49**, re-derived at spec v1.53 by
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
  **The baseline is cited, not remembered, and it is cited WITH the commit it was measured at,
  because it drifts.** Re-measured at `e8eaf6f`, before any implementation commit, from the repo
  root:

  ```
  $ python3.11 -m pytest --collect-only -q | tail -1
  2748 tests collected in 0.40s
  $ python3.11 -m pytest -q -p no:cacheprovider | tail -1
  2748 passed in 383.05s (0:06:23)
  ```

  It was `2747` at `6b4df35`; `b59e05e` then added one test to
  `h-mad/tests/test_h_mad_assemble_audit.py` and the plan was not re-measured, so for a while the
  floor asserted `>= 2747 + …` against a real 2748 — which let **exactly one** pre-existing test be
  deleted with the floor still green, falsifying the no-hidden-deletion guarantee this bullet
  exists to make. That is the failure mode of a remembered number, and it recurs by construction:
  **any** commit landing a test outside this feature moves it again. So the number here is the
  value at the named commit and nothing more, and the residual is stated rather than implied — the
  floor MUST be re-measured at 5c branch time and the two numbers below updated in the same commit
  that creates the branch. A floor carried across an unmeasured interval proves nothing.

  The second command is quoted as it was run for the baseline; as a **gate** it is written so the
  exit status survives — a bare pipe reports `tail`'s status and would let a red suite print as
  success:

  ```
  ( cd "$(git rev-parse --show-toplevel)" && hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider ) > /tmp/doc_block_exec_suite.log; RC=$?   # from the REPOSITORY ROOT, as the spec's AC-6.4 spells it
  tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"      # gate on BOTH lines; rc=124 is the wrapper's expiry, not a suite result
  ```

  **Every 5f command is bounded** through `hmad-dispatch run --timeout <s> -- …` (the base Portable
  time bounds invariant; `timeout`/`gtimeout` are not macOS components): the wrapper propagates
  the wrapped command's exit status and reports 124 on expiry — measured 2026-09-03,
  `run --timeout 5 -- sh -c 'exit 3'` → rc 3, `run --timeout 1 -- sleep 3` → `run_timeout`, rc 124 —
  so the captured status and the `SUITE:`/`MUTATION:` tokens survive it. Bounds: 1200 s for the
  full suite (three times the **383 s** baseline quoted above at `e8eaf6f` — `2748 passed in
  383.05s`; the bound was written as "three times the 397 s baseline" when the baseline was
  `2747 passed in 397.40s` at `6b4df35`, and the v1.84 re-measurement updated the quoted output
  without sweeping this sentence, which is exactly the number-corrected-in-prose-but-stale-beside-
  its-command class the floor fix set out to close — re-derive it from the quoted output at 5c
  rather than carrying it), 600 s for the scoped run and for each mutation-harness
  invocation (the impl-plan's Phase 5f block carries the wrapped commands; it carries the stale
  `397 s` too, which is the author's to sweep).

  So AC-6.4's floor is 2748 collected and the same number passing (at `e8eaf6f`; re-measure at 5c), plus every test this feature
  adds — and "every test this feature adds" is computed, not estimated: the collected count of
  `h-mad/tests/test_h_mad_doc_block_exec.py` run through the collector alone (the floor test itself
  runs `pytest --collect-only -q` in a subprocess with `cwd=REPO_ROOT`, the repository root the
  baseline was measured from — from `h-mad/` the same command collects 2486, a different tree), plus a fixed tuple
  of the named node IDs added to existing files — **exactly these seven**, six in
  `h-mad/tests/test_h_mad_collect_report_docs.py`: `test_gate_block_resolves_through_doc_block_exec`, `test_recipe_runs_through_run_block`, `test_gate_block_refuses_an_untagged_recipe`, `test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`, `test_only_the_exec_scan_hand_rolls_extraction` — and, in `h-mad/tests/test_docsections.py`, `test_docsections_delegates_to_the_authoritative_bounder` (it must live beside the module it spies on, which is where `docsections.json` binds it)
  (each asserted to exist). Every other new test — FR-1..5, AC-1.8's source assertion and
  collect-alone pins, the CLI table walk — lives in the new module and is counted by the collector.
  `test_suite_floor_holds` asserts `full_collected >= 2748 + new_module + 7` from a
  `--collect-only` subprocess, which never executes tests and so cannot recurse (an env guard
  `DOCBLOCK_FLOOR_INNER=1` also makes any inner instance skip); the *pass* half is the Phase-5f
  gate command run alone, outside the suite, and recorded in the report. A deleted pre-existing
  test cannot hide behind the additions.
- `git status --porcelain` is unchanged across a run of a block that writes files.
- No hand-written ` ```bash ` extraction remains on the **executing** path of
  `h-mad/tests/test_h_mad_collect_report_docs.py` — `:270` and `run_recipe` (hoisted to `_run_recipe`) both route through
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
- v1.45: Plan re-audit v31 (both surfaces clean) + design audit v36 back-propagation: the bounder's prefix state is built from complete lines through the line containing start; 49 mutations.
- v1.46: Plan re-audit v32 (codex must 1; agy clean): the resolver splits into _gate_block() -> Block and _gate_bash_block() -> str (= .text), so the file's two text-pin callers keep their type and nothing else moves; the wire mutation targets _gate_block.
- v1.47: Design audit v38 back-propagation: the bounder rule names the backtick-in-info prohibition; 50 mutations.
- v1.48: Design audit v39 back-propagation: 52 mutations (50 + 2).
- v1.49: Plan re-audit v35 (codex must 1; agy see report): the reservation paragraph carries O_NONBLOCK on the existing-file arm and the regular-file check with its FIFO test and two mutations; the stale 'third stays' fragment removed; 54 mutations.
- v1.50: Plan re-audit v36 (codex must 2; agy clean): the launch passes cwd=cwd with its mutation; the one-private-scanner rule (_fence_events) with its trace test and mutation; the reader-less-FIFO probe cited; 55 mutations.
- v1.51: Design audit v43 back-propagation (spec v1.38): _close_stream backstop with the stream_close_failed selection and its two tests/mutations; the ENOTDIR reservation test; 59 mutations (57 + 2).
- v1.52: Design audit v44 back-propagation: 60 mutations (58 + 2).
- v1.53: Design v1.51 back-propagation: 61 mutations (59 + 2).
- v1.54: Plan re-audit v40 (codex must 1; agy clean): docsections.json gains docsections-syspath-setup-removed bound to test_docsections_imports_from_an_unrelated_cwd (six rows).
- v1.55: Design v1.53 back-propagation: docsections.json binding sentence; eight wire mutations (wire-revert-select, wire-revert-substitute).
- v1.56: Plan re-audit v42 (codex must 1 should 1, both answered by impl-plan v1.3; agy clean) + design v1.54 back-propagation: _run_recipe naming.
- v1.57: Design v1.56 back-propagation: 62 mutations (60 + 2).
- v1.58: Design v1.58 back-propagation: scanner grammar corpus in §Measurements (markdown-it-py 2.2.0, 14/14); find_heading (seven public names); docsections.json seventh row.
- v1.59: Plan re-audit v45 (codex must 1) + design v1.59 back-propagation: titled_section's replacement calls find_heading for (start, level); find_heading in the API table.
- v1.60: Plan re-audit v46 (codex must 1 should 1; agy clean): heading selector differential in §Measurements (30 files, new_only=0, old_only=76); run_block timeout=60.0 in the migration; 63 mutations.
- v1.61: Plan re-audit v47 (codex must 2; agy clean): the bounder wording and its API row carry the >= start predicate; the delegation-revert claim names the source-guard exception.
- v1.62: Plan re-audit v48 (codex must 1 should 1; agy clean) + design v1.61 back-propagation: 67 mutations; test_parser_rejects_all_dir_and_abbreviations named on both surfaces; corpus on both renderer versions.
- v1.63: Design v1.62 back-propagation (design audit v58 codex must 1): docsections-delegation-reverted is connection-only (a private spec_from_file_location instance replaces the shared import); the WIRE-PIN's mechanism is stated as the impl-plan has it — a sys.modules fake bound by importlib.reload, since a setattr spy on docsections._dbe cannot see this revert; eighth row docsections-local-bounder-restored bound to the source guard.
- v1.64: Plan re-audit v50 clean (both surfaces) + design v1.63 back-propagation: the WIRE-PIN's finally-path restoration of sys.modules and the docsections reload is stated here too.
- v1.65: Design v1.64 back-propagation: Setext census added to §Measurements (files=30 setext_headings=0); the connection-only revert's private sys.modules registration stated.
- v1.66: Plan re-audit v52 (codex clean; agy should 1): the docsections.json deliverables row names the named-test conversion and the four connection rows (8 rows).
- v1.67: Plan re-audit v53 clean (both surfaces) + design v1.65 back-propagation: 69 mutations (67 of the helper's source) after the two collect-stage rows.
- v1.68: Plan re-audit v54 clean (both surfaces) + design v1.67 back-propagation: run_block's API row lists the collect stage; 70 mutations (68 of the helper's source).
- v1.69: Impl-plan v1.15 back-propagation: consumer-from-import stated as one contiguous replacement at the call region, alias line untouched.
- v1.70: Plan re-audit v55 (codex must 1; agy clean): every 5f command is bounded through hmad-dispatch run --timeout (rc propagates, 124 on expiry — measured); 71 mutations (69 of the helper's source) after the rollback read-back row.
- v1.71: Plan re-audit v56 (codex should 1; agy clean) + design v1.71 back-propagation: the hoisted _run_recipe derives collector/gate from SCRIPT_DIR itself; 72 mutations (70 of the helper's source).
- v1.72: Plan re-audit v57 clean (both surfaces) + design v1.73 back-propagation: 74 mutations (72 of the helper's source) after the bounded-wait rows.
- v1.73: Plan re-audit v58 (codex must 1) + impl-plan audit v18 back-propagation: the reap sequence and its probe prose carry the bounded wait(timeout=DRAIN_SECONDS) and its stage=reap expiry; 75 mutations (73 of the helper's source) with the field-escape row.
- v1.74: Plan re-audit v60 (codex must 1): FR-4's transport paragraph carries the one-physical-line escaping rule, its test and mutation from design v1.75; 76 mutations (74 of the helper's source).
- v1.75: Plan re-audit v61 (codex must 3 nit 1): the substitute API row and FR-4 carry the two-layer empty-key rule; FR-4 carries the quoted-JSON field rule with test_dynamic_field_cannot_forge_a_token and field-quoting-removed; AC-6.4's floor test runs with cwd=REPO_ROOT; the __all__ seven are listed; 77 mutations (75 of the helper's source).
- v1.76: Plan re-audit v62 (codex must 2; agy clean) + design audit v71 nit: the bare-field list is the design's exhaustive seven (reason= included; seconds=/pgid: quoted); the docsections ordering paragraph is un-spliced (the sixth/seventh-row sentences now follow it as their own paragraph).
- v1.77: Design v1.80 back-propagation: verdict/detail examples rewritten in the quoted-field grammar.
- v1.78: Design v1.81 back-propagation: `key=` and both `overlap:` elements quoted.
- v1.79: Plan re-audit v64 clean (both surfaces) + design v1.82 back-propagation: _field's second escaping pass; 78 mutations (76 of the helper's source).
- v1.80: Plan re-audit v66 (codex must 1; agy clean): find_heading's API row states both input forms and their precedence; 79 mutations (77 of the helper's source).
- v1.81: Plan re-audit v67 (codex must 1; agy must 1): BAD_ARGS routing; __all__ is 28 names; find_heading's request predicate is the scanner's; the AC-6.4 gate block runs from the repository root as the spec spells it; 81 mutations (79 of the helper's source).
- v1.82: __all__ is 29 names (BadArgs included).
- v1.83: Plan re-audit v69 (codex must 1; agy clean) + impl-plan audit v29: FR-6's caller pseudocode binds substituted_block from substitute's tuple; the unreadable-preamble test is test_unreadable_preamble_path_refuses.
- v1.84: Plan audit v73 (teammate surface, advisory). MUST 1: the AC-6.4 suite-floor baseline was stale by one — 2747/2485 measured at 6b4df35, but b59e05e added a test and the real counts at e8eaf6f are 2748/2486, so the floor asserted >= 2747 + … against a real 2748 and exactly one pre-existing test could be deleted with the floor green, falsifying the bullet's own no-hidden-deletion guarantee. Re-measured, and the drift is now closed as a class rather than a number: the count travels with the commit it was measured at and MUST be re-measured at 5c branch time. MUST 2: this was the one document of four stating the exit-code contract without the --help carve-out (the impl-plan swept it at v1.31, the plan was not swept with it); carve-out added, plus exit_on_error at the default per design v1.91. Also: 'tagging makes re.findall match zero blocks' is measured false — 4 blocks before, 3 after, and what empties is the h_mad_audit_gate.py filter, so the loud failure is _gate_bash_block's assert gating.
- v1.85: Plan audit v74 (teammate surface; the agy leg returned PASS at tools=2, the report-file floor, so it contributed nothing). MUST 1: the doc_block_exec.json deliverable row split its 81 rows 79 helper-source + 2 SKILL.md, but the design matrix it names as the authoritative list has exactly ONE row whose mechanism names SKILL.md as the mutation target (registry-row-removed at design :1256) — counted independently: 81 data rows at design :1178-1258, 1 naming SKILL.md. The second AC-4.5 direction, detail-line-undocumented, mutates the HELPER ('the helper renames one emitted detail line'), so its file key is the helper's source and "h-mad/SKILL.md" there is an anchor the harness refuses. Split corrected to 80 + 1, and the split is now re-derived from the matrix's mechanism column rather than carried. The design's own summary paragraph under the matrix still says 79 + 2 and contradicts its matrix; the impl-plan carries the same pair at :1234/:1268 — reported to the orchestrator, not edited here. MUST 2 (rule 7, this document's own instance): the 5f bound cited 'three times the 397 s baseline' while the baseline quoted eleven lines above had been re-measured at v1.84 to '2748 passed in 383.05s' — 397.40s was the value at 6b4df35, so the number was corrected in the quoted command output and left stale in the prose that derives from it. Now 383 s with the drift named; the impl-plan carries the same stale 397 s at :1796. CENSUS (rule 2): the extractor-census control was the one figure in this plan with no command; it is now cited as `git grep -l '```' -- '*.py' | wc -l` -> 23 at 1861157 (21 at 6b4df35; b59e05e, the same commit that moved the suite floor, moved this too), with the narrower bash-literal reading (3) named so the quantity meant is unambiguous. SHOULD: 'changes at exactly two points' replaced by what does NOT move (the three _gate_bash_block callers keep their types, :412 keeps re.findall, .returncode is read nowhere), since the paragraph's own list runs to five regions; Scope names the AC-1.8 docsections scope increase and its three deliverables, and the Implementation Strategy opening sentence carried the same omission and is fixed with it; __all__'s enumeration reads 'the whole DocBlockError hierarchy — the base class and its 19 subclasses' per design :689, since the seven-plus-two-plus-subclasses reading gives 28; the --help carve-out swept by claim to all three surfaces (transport, CLI contract, Implementation Strategy) with the residual stated. NITS: titled_section's replacement is one-for-one at the call site and intentionally drops one leading newline; the design's matrix is a bolded lead-in, not a heading. Also re-derived: AC count 49 at spec v1.53, fence census 68/10 with control 83, extractor census 2 hits / 5 bare-literal hits — all unchanged.
- v1.86: Design v1.93 back-propagation (raised by design-author-1, verified by the orchestrator): every *.md-scoped heading measurement in Measurements cited a 30-file corpus that is 25 tracked files plus 5 untracked, gitignored .pytest_cache/README.md artifacts — build output that exists only where pytest has run, so files=30/both=266/setext_headings=0 were not reproducible on a clean clone, and the plan contradicted the design from v1.93 on. The corpus is now defined as the design's: git ls-files -- h-mad handoff filtered to *.md with archive/ excluded, 25 files, with the command cited. Re-derived independently at 1861157 (throwaway heading_differential.py, one re.match per line per selector, fence-aware on the new side), both corpora reported side by side so the contamination stays visible: TRACKED files=25 both=263 old_only=76 new_only=0 setext_headings=0, softening closing_hash=0 tab_form=0 titleless=0; GLOB files=30 both=268 old_only=76 new_only=0 setext_headings=0, softening closing_hash=5 tab_form=0 titleless=0. So the two load-bearing conclusions (new_only=0, old_only=76) hold on BOTH corpora and never depended on the contamination — but the new_only=0 JUSTIFICATION did: the old text said '## x ##' occurs nowhere while measuring a corpus holding five of them ('# pytest cache directory #', one per README). Restated correctly: the Guard-narrowing 'softened outcome' set is about heading IDENTITY, not line recognition — a '## x ##' line is a heading to both selectors and lands in both, never new_only, and only the new selector strips the closing run; counted as identities the set is empty over the tracked 25 and is 5 over the glob 30. The both=266 -> 268 delta chased rather than carried: 266 was correct at 1f5b30e, and h-mad/SKILL.md has since gained exactly two ### headings, 'Close the class, never the instance' (e8eaf6f) and 'Record a rejected finding in the rejections ledger, never in a gated document' (ff0a278/11a7db7), measured by diffing the heading lines between the revisions; both is not a conclusion this plan rests on and drifts with any doc edit, so its command travels with it. Also swept by value rather than fixing the two named instances: the fence census (68 across 10 files, control 83) is the third *.md-scoped count and was re-run on both corpora — identical on each, because the five artifacts carry no fence, so it is corpus-invariant and that is now measured rather than assumed. NOT harmonised, deliberately: AC-6.1's tree sweep is not git ls-files — the spec reaches its scope by reference to this census, so the plan now states why the two realisations differ, namely that a test must still count a newly written, not-yet-tracked .md under the two roots (exactly what git ls-files misses and the guard exists to catch), and excludes build output by a dot-directory component instead.
- v1.87: Pre-dispatch precheck repair before the round-three audit, raised by h_mad_precheck_doc.py (hard, PINDRIFT), re-verified here against the tree. The plan's one cross-document line pin into the design — the citation for the seven-plus-two-plus-subclasses reading — resolved to a blank line: sed on the pinned line printed empty, grep for the phrase found it 34 lines lower, and the shift came from the design's revision to v1.93 at b68ef48, after the sha this plan measured at. NOT re-pinned to the new line, and that is the point: the precheck scores PINDRIFT at FILE level, so any design.md line pin fires while the design has changed since this plan's provenance 1861157 — a scratch copy re-pinned to the new line still returned PRECHECK FAIL issues=1, proving the number was never the defect. The citation is now a structural locator (the design's API / Interface Changes heading, the __all__ paragraph after the find_heading docstring, plus the grep that finds it, one hit at HEAD 048ef1f), so the class is closed and no future design revision can stale it. Sweep, rule 7: grep -nE for a path:line form over the whole plan returns exactly one design pin (this one, fixed) and one .py pin, the docsections fence-prefix consumer — that one is verified UNCHANGED since 1861157 and correct at HEAD, so it is advisory, left alone and reported to the orchestrator with the bare :NNN pins into the collect-report test module. No measurement sha re-pinned: 1861157, a469493 and e8eaf6f stand because no measurement behind them was re-run, and a behind-HEAD measurement sha is the normal condition the precheck scores as advisory.
