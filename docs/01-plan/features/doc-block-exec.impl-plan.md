# Implementation Plan: doc-block-exec

> Source: docs/02-design/features/doc-block-exec.design.md (post-audit, v1.66 — design cycle 62 / impl-plan cycle 13 back-propagation, commit 41c3789)
> Paired spec: docs/01-plan/features/doc-block-exec.spec.md (v1.40) · paired plan: docs/01-plan/features/doc-block-exec.plan.md (v1.67)
> Branch target: feature/doc-block-exec

## Executive Summary

One new module, `h-mad/scripts/h_mad_doc_block_exec.py`, lands in five tasks. Task 1 (`wiring`)
creates the scanner, the public bounder, extraction and selection **and, in the same task,
re-points `docsections.py` at that bounder** (the design's author-together order; the
single-source contract never has an intermediate commit with two bounders). Tasks 2–4
(`new-behaviour`) add substitution; execution + bounding; CLI + registry. Task 5 (`wiring`) tags
the Second-surface gate fence and migrates `test_h_mad_collect_report_docs.py`'s executing path.
Every guard the design names carries a mutation row bound to one named test; the three specs
(`doc_block_exec.json` 69 rows, `doc_block_exec_wire.json` 8, `docsections.json` 8) must report `ALL_CAUGHT`.

## Conventions binding every task

- **Interpreter**: `python3.11` (the pinned interpreter with pytest). Every command below runs
  from `h-mad/` unless stated. Never invoke `timeout`/`gtimeout` anywhere (AC-5.3 scans the source).
- **Test file for Tasks 1–4, plus Task 5's two tree-level tests**: `h-mad/tests/test_h_mad_doc_block_exec.py`
  (new in Task 1, extended by later tasks). API tests import the module as
  `import h_mad_doc_block_exec as dbe` with `h-mad/scripts` on `sys.path` (the same arrangement
  `test_h_mad_collect_report_docs.py` uses at its `:22` `sys.path.insert(0, str(SCRIPT_DIR))`).
- **CLI transport split** (design §Test Strategy, last paragraph): every verdict a **real input or
  a real fault** can produce is exercised through
  `subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)` where
  `REPO_ROOT = Path(__file__).resolve().parents[2]` and `SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_doc_block_exec.py"`,
  so exit codes are the real process's — marked `(subprocess)` in the ACs. A verdict that needs
  one of the six seam injections (`_final_write`, `_close_stream`, `tempfile.mkdtemp`, `os.chmod`,
  `shutil.rmtree`, `os.killpg`) **or the instance-level `Popen` wrapper below**
  calls `dbe.main(argv)` **in-process** — its return value is the
  exit code and `capsys` captures the `DOCBLOCK:` and detail lines — because a `monkeypatch`
  cannot cross an exec boundary; marked `(in-process main)`. Two subprocess tests in Task 4
  (`test_cli_exit_zero_propagates`, `test_cli_exit_two_propagates`) pin that `sys.exit(main())`
  turns the return value into the process exit, so the in-process code is the real code.
- **Fixtures are hostile**: markdown strings written to `tmp_path`, with mixed heading levels,
  fences quoting fences, a path containing a space, a body with CRLF, and a key containing regex
  metacharacters.
- **Fault injections — six module-level seams, all via `monkeypatch`, `subprocess` never mocked**:
  `os.killpg` (AC-4.6 reap only), `shutil.rmtree` (in the helper's namespace), `tempfile.mkdtemp`,
  `os.chmod`, the module's `_final_write(handle, text)` seam, and the module's
  `_close_stream(handle)` seam. Recording pass-throughs of `subprocess.Popen` and `os.open` are
  observations, not injections, and are allowed.
- **The seventh injection form — instance-level, not a module seam** (design v1.65 §Execution, the
  two `stage=collect` tests): the recording `subprocess.Popen` pass-through itself shadows one bound
  method on the instance it is about to return. The test binds `real_popen = subprocess.Popen`
  **before** `monkeypatch.setattr(dbe.subprocess, "Popen", recording_popen)` — the same rule the
  `real_rmtree` and `real_killpg` bindings follow, and without it the pass-through recurses, because
  `dbe.subprocess` is the process-global module. Then
  `inst = real_popen(*a, **kw); inst.communicate = _raise_once(inst.communicate); return inst`
  (an instance attribute shadows the class method; `Popen` defines no `__slots__`), where
  `_raise_once(bound)` raises `OSError(errno.EIO, "Input/output error")` on its **first** call and
  delegates to `bound` on every later call. The wrap must happen inside the pass-through, because
  `run_block` calls `communicate` immediately after `Popen` returns and the test never holds the
  instance before that. `wait` is wrapped the same way for
  `test_drain_wait_oserror_is_launch_failed_collect`. This form is **not** one of the six named
  seams and is not a `monkeypatch.setattr` on the helper's namespace; design v1.65 §Test Strategy
  and spec v1.39 both still say "exactly six named fault injections", which their own new §Execution
  paragraph contradicts — flagged for design cycle 63, not resolved here.
- **Mutation spec** `h-mad/tests/mutation-specs/doc_block_exec.json`: `root` is `../..`,
  `command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_doc_block_exec.py", "-q"]`,
  `target_command` is `["python3.11", "-m", "pytest", "-q"]`, every mutation has a `test` key that is
  the **full node ID** `tests/test_h_mad_doc_block_exec.py::<name>` — exactly ONE `test` key per
  row, even where a second test also goes red on the mutant (that test stays a regression test,
  never the spec's key: for `final-write-close-not-in-finally` the canonical key is
  `tests/test_h_mad_doc_block_exec.py::test_final_write_failure_before_close_still_closes` and
  `test_final_write_close_failure_is_mapped` is the regression test; a sweep of every other row
  bound in this document — the docsections rows to the WIRE-PIN / their `_killed_by` /
  `test_docsections_imports_from_an_unrelated_cwd`, the wire rows to one pin each — found no
  other row naming two tests) — and every `find` anchor
  matches the landed source exactly once (the harness applies one `find`/`replace` pair per row
  via `str.replace` — `h_mad_mutation_harness.py:645` — so a multi-site revert must be expressed
  as one replacement). Each task appends its rows; the file is created in Task 1. Run
  `python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec.json`
  and read the `MUTATION:` token — `ALL_CAUGHT` is required before the task is GREEN.
- **Single source of the fence grammar**: marker-run **recognition** — the literals ```` ``` ```` and
  `~~~`, the run-length regex, and any `in_fence` toggle — lives in exactly one function body,
  `_fence_events`, and so does ATX heading recognition (the `heading` event kind); `extract` and
  `fence_aware_end` are thin consumers that read only the event's
  `kind`/`marker`/`run`/`indent`/`info`/`candidate`/`level`/`text` fields (Task 1, mutation `scanner-duplicated-in-consumer`).
- **Exit-code partition** (AC-4.2): every verdict of readable input and `TIMEOUT` exit 0;
  `UNREADABLE`, `CLEANUP_FAILED`, `LAUNCH_FAILED` exit 2; argparse usage errors are the only
  non-`DOCBLOCK:` exit 2. No refusal line ever carries `rc=`.

---

## Task 1: scanner, selection, info-string grammar, and the bounder's second consumer

**Production file**: `h-mad/scripts/h_mad_doc_block_exec.py` (new) and `h-mad/tests/docsections.py` (modified)
**Test file**: `h-mad/tests/test_h_mad_doc_block_exec.py` (new; includes the five docsections-side tests `test_docsections_has_no_second_bounder`, `test_docsections_unbalanced_four_backtick_fence`, `test_titled_section_ignores_a_heading_inside_a_fence`, `test_docsections_imports_when_collected_alone`, `test_docsections_imports_from_an_unrelated_cwd`) and `h-mad/tests/test_docsections.py` (gains exactly one test: the WIRE-PIN)
**Mutation spec**: `h-mad/tests/mutation-specs/doc_block_exec.json` (new) and `h-mad/tests/mutation-specs/docsections.json` (modified)
**Task shape**: `wiring`
**WIRE**: `h-mad/tests/docsections.py:titled_section` → `_dbe.find_heading(text, heading)` AND `_dbe.fence_aware_end(text, start, level)`; `h-mad/tests/docsections.py:section_from` → `_dbe.fence_aware_end(text, offset, level)` (imported as `import h_mad_doc_block_exec as _dbe`; `titled_section` passes the `(start, level)` `find_heading` returned, `section_from` passes its own `offset`)
**WIRE-PIN**: `h-mad/tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`

**Description — new behaviour**: Create the module with its **complete** exception hierarchy —
`DocBlockError` and its 18 subclasses (19 exception classes) with their constructors, listed in the code structure, so
`__all__` is complete and `from h_mad_doc_block_exec import *` works at Task 1 GREEN; Tasks 2–4
only reference them — the frozen `Block`
dataclass (`RunResult` is Task 3's, beside `run_block`, per the design's Implementation Order), the private fence scanner `_fence_events`, the public bounder `fence_aware_end`, the public
heading lookup `find_heading`, the pure scan `extract`, and the ordinal policy `select`. `extract` reads a **path** as strict UTF-8
(a `str` is converted with `Path`; `OSError` and `UnicodeDecodeError` both become
`DocUnreadable`), locates the heading through the public
`find_heading(text: str, heading: str) -> tuple[int, int] | None` — the offset just past the
heading line (the heading event's `end`) and its level; `None` when absent; `AmbiguousHeading(n)`
when more than one matches; found **among the scanner's `heading` events only**, so a line inside
any fence is never a heading match and a fenced example quoting the requested heading cannot become
the section start (design v1.61 §Scanning). **`heading` has two accepted forms, and each real caller
uses one**: the **full line form** `## Text` — matches a heading event whose text after the hash run
(closing hashes stripped, trailing whitespace stripped) equals `Text` AND whose level equals the hash
count; this is what `extract`, the CLI `--heading`, and Task 5's `_gate_block` pass — and the **bare
form** `Text` — matches on text at any level; this is `docsections.titled_section`'s unchanged
contract. `extract` maps `None` to an empty candidate list and never raises on absence — bounds the section at the next
`heading` event of the same or shallower level, and
returns every **tagged** fence between those offsets — an event with `candidate` true (a backtick
opener whose first info word is `bash`; `extract` never reads `marker`) whose info string carries the
tag — possibly an empty list,
never raising on candidate count. **A heading is recognised by the CommonMark ATX rule (§4.2) and
nothing looser**: 0–3 leading spaces, a run of 1–6 `#`, then a space, a tab or end of line; an
optional closing `#` run preceded by a space is stripped before the text is compared; so `#hashtag`,
a seven-`#` run and a four-space-indented `## x` are prose; the level is the run length of the
opening hashes. That predicate is implemented **once**, in `_fence_events`, which reports such a
line (outside any fence) as a `heading` event carrying `level` and the compared text — both the
heading match in `extract` and the section boundary in `fence_aware_end` consume the scanner's
verdict rather than re-recognising headings, so the single-source rule holds for headings as it
does for fences. The scanner event model is the design v1.58's exactly: `_fence_events(text)` is a
generator yielding one event per line of **five kinds** — fence `open`, fence `close`, fence
`body`, ATX `heading` (with its `level`), or `prose` — together with the line's `start`/`end`
character offsets (populated by `_fence_events` from its own cursor, so CRLF and any line width are
exact; `find_heading` returns the heading event's `end`, `fence_aware_end` tests `event.start >= start`,
and neither consumer walks lines a second time), the opener's marker character, run length,
indentation and info string, and the scanner-derived `candidate` flag. Every rule below was
rendered through markdown-it-py — both 2.2.0 (interpreter-local) and 4.2.0 (the spec's throwaway
venv) — before it was written down, 14 of 14 agreeing on each (plan §Measurements, "Scanner grammar
corpus"): a backtick or tilde run of ≥ 3
preceded by 0–3 spaces opens; a backtick opener whose info string contains a backtick is not a
fence at all (inert prose); while open, only a line whose leading run is the same character, ≥
the opening length, preceded by 0–3 spaces, and followed by nothing but spaces/tabs closes; a
marker run at 4+ spaces inside a fence is body text; no line inside a fence is examined as a
heading or opener. `fence_aware_end(text, start, level)` feeds the scanner **complete lines from
the document start through the line containing `start`** (never `text[:start]`) and considers a
boundary at every line whose start offset is **≥ `start`** — the line beginning exactly at `start`
(the line adjacent to the heading `find_heading` returned) IS a candidate, while a line that began
before a mid-line `start` is not (design v1.60 §Scanning; a `>` predicate would skip an adjacent
same-level heading and hand its tagged block to the wrong address). `extract` de-indents each body line by up
to the opener's indentation (a line indented less loses only what it has) and validates the info
string **only on a tagged fence**: tokens after `bash` are whitespace-separated; `hmad:exec` is
the tag; `shell=strict` (default) / `shell=plain`; any other token, any other `shell=` value, or
a **duplicated** recognised token raises `BadInfoString(key)` with the offending/repeated token.
An untagged fence's info string is never inspected. `select(blocks, index=None)` validates
`index < 1` → `BadIndex(n)` **before any lookup**; then 0 candidates or index past the end →
`BlockNotFound`; > 1 with no index → `AmbiguousBlock(n)`; else the block.

**Description — the wire**: In the same task, delete the private `_fence_aware_end` from
`h-mad/tests/docsections.py` (today at `docsections.py:31`, a `startswith("```")` toggle) **and**
`titled_section`'s local heading regex — today `docsections.py:53`,
`match = re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text)`, a second, looser
heading grammar that would pick the section start independently of the scanner — measured as
guard-narrowing evidence in plan §Measurements "Heading selector differential": over 30 files
(`archive/` excluded) the old regex and `find_heading` agree on 266 headings, `new_only=0` (nothing
the old guard refused is newly accepted) and `old_only=76`, every one a `#` comment line inside
fenced code the old regex read as a heading. `titled_section(text: str, heading: str)`
now calls `found = _dbe.find_heading(text, heading)`, keeps its own loud failure
(`assert found, f"missing section {heading!r}"` — `test_a_missing_heading_fails_loudly` still
passes), unpacks `start, level = found`, and returns `text[start:_dbe.fence_aware_end(text, start, level)]`;
`section_from(text: str, offset: int, level: int = 2)` is unchanged except that it calls
`_dbe.fence_aware_end(text, offset, level)`. The import
must work when `test_docsections.py` is collected alone (nothing else puts `h-mad/scripts` on
`sys.path`; `tests/conftest.py` does not) and when `docsections` is imported from an unrelated cwd
with only the tests dir on `sys.path`, so `docsections.py` inserts the directory containing
`docsections.py` joined with `../scripts` into `sys.path` itself (resolved from `__file__`) before
the import. Re-point `docsections.json`: `fence-tracking-removed` and
`section-no-longer-owns-its-subsections` anchor in `scripts/h_mad_doc_block_exec.py` (the
scanner's state transition and the bounder's heading match); the other two anchors
(`offset-anchored-bound-runs-to-end-of-file`, `missing-heading-returns-empty-instead-of-failing`)
stay in `tests/docsections.py`; the spec gains `"target_command": ["python3.11", "-m", "pytest", "-q"]`
and **all eight** rows gain a `test` key (the full node ID, copied from `_killed_by`, which stays);
the two anchors that stay in `tests/docsections.py` are re-spelled to the delegating lines they now
mutate (`offset-anchored-bound-runs-to-end-of-file` finds `return text[offset:_dbe.fence_aware_end(text, offset, level)]`;
`missing-heading-returns-empty-instead-of-failing` finds `assert found, f"missing section {heading!r}"`).
Add a fifth row `docsections-delegation-reverted`, a **connection-only** revert: the callee is
untouched and no local bounder is restored. `find` is the one line
`import h_mad_doc_block_exec as _dbe  # noqa: E402` (it matches exactly once); `replace` is
```python
import importlib.util as _ilu  # noqa: E402
_spec = _ilu.spec_from_file_location("_h_mad_doc_block_exec_private", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "h_mad_doc_block_exec.py"))
_dbe = _ilu.module_from_spec(_spec); sys.modules[_spec.name] = _dbe; _spec.loader.exec_module(_dbe)
```
(`os` and `sys` are already imported at the top of the delta) — the same file, loaded as a private
instance registered in `sys.modules` only under `_h_mad_doc_block_exec_private`, a name the import
system never resolves for `h_mad_doc_block_exec`. The registration is required, not cosmetic:
under `from __future__ import annotations` dataclass processing dereferences
`sys.modules[cls.__module__]` (`dataclasses._is_type`), so an unregistered instance of a module
with a frozen `@dataclass` raises `AttributeError: 'NoneType' object has no attribute '__dict__'`
at load — measured on 3.11.8 (impl-plan audit v11); registered under the private name it loads
and the WIRE-PIN still records `[]`. So
`titled_section` and `section_from` still do the real work through a second, byte-identical
bounder. Under it the WIRE-PIN fails because its recording fake sits in `sys.modules` and the
reload re-binds `_dbe` to the private instance, not the fake — neither recorder is ever called;
**every other test stays green**: the helper's own behaviour tests
(`extract`/`select`/`fence_aware_end`/`find_heading`), the two docsections-side hostile tests
(`test_docsections_unbalanced_four_backtick_fence`, `test_titled_section_ignores_a_heading_inside_a_fence`)
and the source guard `test_docsections_has_no_second_bounder` (the source still defines no
`_fence_aware_end` and scans no marker run). The row's `test` key is the WIRE-PIN. Measured
2026-09-03 on a two-module scratch pair with the scaffold below and a frozen-dataclass callee under
`from __future__ import annotations`: the shared-import caller records
`['find_heading', 'fence_aware_end']`, the file-path caller records `[]`, both return the same
section. Add a sixth row
`docsections-syspath-setup-removed`: `find` is the `sys.path.insert` line shown in the delta below, `replace` is the
comment `# sys.path setup removed`; killed by
`tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd` (the `import` then
fails with `ModuleNotFoundError` in the subprocess). Add a seventh row
`docsections-heading-lookup-reverted`: `find` is the `found = _dbe.find_heading(text, heading)` line,
`replace` restores the local regex on that one line, carrying its own import because the delta no longer imports `re` (`import re; match = re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text); found = (match.end(), len(match.group("marks"))) if match else None`),
`find_heading` untouched — killed by the WIRE-PIN, whose `find_heading` record then stays empty
(the harness's single `find`/`replace` per row fits: one line becomes one line). Add an eighth row
`docsections-local-bounder-restored`, the behaviour-restoring revert the source guard exists to
refuse, as one contiguous replacement: `find` is the source from
`def titled_section(text: str, heading: str) -> str:` through `section_from`'s
`return text[offset:_dbe.fence_aware_end(text, offset, level)]` (both call sites, docstrings
verbatim — it matches exactly once); `replace` is that same text with `import re` and two local
definitions inserted before `def titled_section` — `def _fence_aware_end(text, start, level)`
(the old `startswith("```")` toggle from today's `:31`) and `def _find_heading(text, heading)`
(today's `:53` regex, returning `(match.end(), len(match.group("marks")))` or `None`) — and the
three `_dbe.` references at the two call sites re-pointed at them (`found = _find_heading(text, heading)`,
`_fence_aware_end(text, start, level)`, `_fence_aware_end(text, offset, level)`); the
`import h_mad_doc_block_exec as _dbe` line is not in the `find` and stays. Its `test` key is
`tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder`, which goes red on
the restored `_fence_aware_end` definition; the WIRE-PIN and the two hostile tests also go red
under it, which is why this row cannot serve as the isolated-wire proof and the fifth row can
(design audit v58). The killer of the sixth row must live in a file that still
**collects** under the mutant: `test_docsections.py` imports `docsections` at module level, so
there the mutant is a collection error, which the harness scores as a refusal, not a kill
(`h_mad_mutation_harness.py:660–669`); `test_h_mad_doc_block_exec.py` imports only `dbe` and
never imports `docsections` at module level (it reads that file's source as text), so its named
test reaches its assertion; the eighth row's killer lives in the same file for the same reason.

**Code structure**:
```python
# h-mad/scripts/h_mad_doc_block_exec.py
from __future__ import annotations
import argparse, dataclasses, io, math, os, re, shutil, signal, stat, subprocess, sys, tempfile
# ^ complete for every module-level name used across the five tasks' module code: argparse (main),
#   dataclasses.replace (substitute), io (handle annotations), math.isfinite, os, re, shutil.rmtree,
#   signal.SIGKILL, stat.S_ISREG, subprocess.Popen/PIPE, sys.exit, tempfile.mkdtemp. The test-file
#   deltas carry their own (`os, re, sys` in docsections.py; `importlib, sys, types` in the
#   test_docsections.py scaffold; the consumer already imports `re, shlex, sys, Path` at its :10–:13).
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Mapping, Sequence

# `__all__` names only what is DEFINED at each task's GREEN, so a star-import works at every
# task boundary: Task 1 lists Block, extract, select, fence_aware_end, find_heading and the 19
# exception classes (24 names); Task 2 appends "substitute"; Task 3 appends "RunResult",
# "run_block"; Task 4 appends "main" — 28 names when complete: the seven public functions
# (extract, select, substitute, run_block, main, fence_aware_end, find_heading — "all seven",
# design §API) + Block + RunResult + 19 exceptions.
__all__ = [
    "Block", "extract", "select", "fence_aware_end", "find_heading",
    "DocBlockError", "DocUnreadable", "BadInfoString", "BlockNotFound", "AmbiguousBlock",
    "AmbiguousHeading", "BadIndex",
    "BadSubstArg", "MissingSubstitution", "OverlappingSubstitution",
    "BadTimeout", "BlockTimeout", "CleanupFailed", "LaunchFailed",
    "StreamPathUnwritable", "StreamPathsAlias", "PreambleUnreadable", "StreamWriteFailed",
    "StreamCloseFailed",
]

DRAIN_SECONDS = 5.0            # Task 3 uses it; declared here so the constant has one home

# The complete hierarchy: DocBlockError + 18 subclasses (6 + 3 + 4 + 5), every one defined HERE (Task 1).
class DocBlockError(Exception): ...
# raised by extract / select (Task 1)                                         — 6
class DocUnreadable(DocBlockError): ...
class BadInfoString(DocBlockError):
    def __init__(self, key: str): ...
class BlockNotFound(DocBlockError): ...
class AmbiguousBlock(DocBlockError):
    def __init__(self, n: int): ...
class AmbiguousHeading(DocBlockError):
    def __init__(self, n: int): ...
class BadIndex(DocBlockError):
    def __init__(self, n: object): ...
# raised by substitute (Task 2) and the CLI's --subst parsing (Task 4)         — 3
class BadSubstArg(DocBlockError):
    def __init__(self, raw: str, duplicate_key: str | None = None): ...
class MissingSubstitution(DocBlockError):
    def __init__(self, keys: list[str]): ...                 # insertion order preserved
class OverlappingSubstitution(DocBlockError):
    def __init__(self, pairs: list[tuple[str, str]]): ...   # sorted (shorter, longer)
# raised by run_block (Task 3)                                                 — 4
class BadTimeout(DocBlockError):
    def __init__(self, value: object): ...
class BlockTimeout(DocBlockError):
    def __init__(self, seconds: float): ...
class CleanupFailed(DocBlockError):
    def __init__(self, path: str, cleanup_error: OSError | None): ...
class LaunchFailed(DocBlockError):
    def __init__(self, stage: str, err: OSError, pgid: int | None = None): ...
    # attributes: .stage, .err, .pgid — all three are read by tests and by main's renderer
    # stage in {"mkdtemp", "spawn", "reap", "collect"}; pgid is set on the "reap" and "collect"
    # stages and stays None on "mkdtemp"/"spawn" (design v1.65 exception table + verdict table)
# raised by main's stream and preamble handling (Task 4)                       — 5
class StreamPathUnwritable(DocBlockError): ...
class StreamPathsAlias(DocBlockError): ...
class PreambleUnreadable(DocBlockError): ...
class StreamWriteFailed(DocBlockError):
    def __init__(self, written: list[str], failed: str, skipped: list[str], verify: str | None = None): ...
class StreamCloseFailed(DocBlockError):
    def __init__(self, stream: str, close_error: OSError): ...

@dataclass(frozen=True)
class Block:
    text: str        # de-indented fence body, no trailing-newline normalisation
    shell: str       # "strict" | "plain"
    lineno: int      # 1-based line of the opening fence
    info: str        # raw info string after the language word

@dataclass(frozen=True)
class _FenceEvent:
    lineno: int; kind: str            # "open" | "close" | "body" | "prose" | "heading"
    marker: str | None; run: int; indent: int; info: str
    start: int; end: int              # character offsets of the line [start, end) incl. its newline —
                                      # the scanner's own cursor, CRLF-safe; find_heading returns a
                                      # heading event's `end`, fence_aware_end tests `start >= start`
    level: int                        # heading events only (1–6, the opening-run length); 0 otherwise
    text: str                         # heading events only: the compared text (closing-run stripped)
    candidate: bool                   # scanner-derived: True only for a BACKTICK opener whose first
                                      # info word is "bash" — extract never inspects `marker` itself

def _fence_events(text: str) -> Iterator[_FenceEvent]:
    """The ONLY function that inspects marker runs. Yields one event per line."""

def fence_aware_end(text: str, start: int, level: int) -> int:
    """`event.start` of the next `heading` event at `level` or shallower with
    `event.start >= start` (the line adjacent to a heading is included;
    a line that began before a mid-line `start` is not); fence state built over
    complete lines through the line containing `start`; heading recognition is
    the scanner's, never re-derived here."""

def find_heading(text: str, heading: str) -> tuple[int, int] | None:
    """(the heading event's `end` offset, its level) for the matching heading event; None when
    absent; AmbiguousHeading(n) when more than one matches. `heading` is either the full line
    form '## Text' (text AND level must match) or the bare 'Text' (any level —
    docsections.titled_section's contract). Searches the scanner's `heading` events only."""

def extract(doc: str | Path, heading: str) -> list[Block]: ...   # calls find_heading, then bounds
def select(blocks: Sequence[Block], index: int | None = None) -> Block: ...
```

```python
# h-mad/tests/docsections.py  (delta)
import os, sys                                        # `re` goes with the local regex it served
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import h_mad_doc_block_exec as _dbe  # noqa: E402

def titled_section(text: str, heading: str) -> str:
    found = _dbe.find_heading(text, heading)          # replaces the local re.search at :53
    assert found, f"missing section {heading!r}"      # the loud failure stays local
    start, level = found
    return text[start:_dbe.fence_aware_end(text, start, level)]

def section_from(text: str, offset: int, level: int = 2) -> str:
    return text[offset:_dbe.fence_aware_end(text, offset, level)]
# `_fence_aware_end` and the local heading regex are deleted; `__all__ = ["titled_section", "section_from"]` is unchanged.
```

```python
# h-mad/tests/test_docsections.py  (delta — the RED-safe WIRE-PIN scaffold)
import importlib, sys, types
import docsections

FENCED = "## Section\n```\n# not a heading\n```\nanchor text\n## Next\n"

def test_docsections_delegates_to_the_authoritative_bounder() -> None:
    calls: list[tuple] = []
    try:
        import h_mad_doc_block_exec as _real      # importable from GREEN on (docsections put scripts on sys.path)
    except ImportError:
        _real = None                              # RED: the module does not exist yet
    def rec_find(text: str, heading: str) -> tuple[int, int] | None:
        calls.append(("find_heading", text, heading))
        return _real.find_heading(text, heading) if _real is not None else (len(text), 2)
    def rec_end(text: str, offset: int, level: int) -> int:
        calls.append(("fence_aware_end", text, offset, level))
        return _real.fence_aware_end(text, offset, level) if _real is not None else len(text)
    fake = types.ModuleType("h_mad_doc_block_exec")
    fake.find_heading = rec_find
    fake.fence_aware_end = rec_end
    saved = sys.modules.get("h_mad_doc_block_exec")
    sys.modules["h_mad_doc_block_exec"] = fake
    try:
        importlib.reload(docsections)             # re-runs the module-level import: binds the fake at GREEN; a no-op at RED
        docsections.titled_section(FENCED, "Section")   # bare form: titled_section's contract
        docsections.section_from(FENCED, FENCED.index("anchor"), 2)
    finally:
        if saved is None:
            sys.modules.pop("h_mad_doc_block_exec", None)
        else:
            sys.modules["h_mad_doc_block_exec"] = saved
        importlib.reload(docsections)             # `_dbe` rebinds to the real module; no later test sees the fake
    assert [c[0] for c in calls] == ["find_heading", "fence_aware_end", "fence_aware_end"], (
        f"docsections did not delegate both the section start and its end: {calls!r}")
    assert calls[0] == ("find_heading", FENCED, "Section")             # titled_section: start lookup
    assert calls[1][1] == FENCED and calls[1][3] == 2                  # titled_section: (text, start, level)
    assert calls[2] == ("fence_aware_end", FENCED, FENCED.index("anchor"), 2)  # section_from
```
`importlib.reload` is required because `docsections` is already imported by the time the test
body runs (the test module's own `from docsections import section_from, titled_section`), so a plain `import` would not
re-execute the module-level `import h_mad_doc_block_exec as _dbe` line. At RED (`docsections.py`
unchanged, stdlib-only) the reload is harmless and neither recorder is ever called, so the test
fails on the call-sequence assertion — never an `ImportError`/`AttributeError`. At GREEN the reload
re-executes the delegating import, which finds the fake in `sys.modules` first, so `titled_section`
hits `find_heading` then `fence_aware_end`, and `section_from` hits `fence_aware_end`.

**Acceptance Criteria** (each is one named test; in `test_h_mad_doc_block_exec.py` unless stated):
- [ ] AC-1.1 `test_tagged_fence_under_heading_is_extracted`: a section with one tagged and one untagged fence yields exactly the tagged block, `shell == "strict"`, `lineno` = the opener's 1-based line, `text` = the body verbatim.
- [ ] AC-1.2 `test_untagged_fence_is_not_a_candidate`: a section with only untagged fences yields `[]`.
- [ ] AC-1.3 `test_two_tagged_blocks_without_index_are_ambiguous`: `select` on two blocks with no index raises `AmbiguousBlock` with `n == 2`.
- [ ] AC-1.4 `test_index_selects_and_past_end_is_not_found`: `select(blocks, 2)` returns the second; `select(blocks, 3)` on two raises `BlockNotFound`.
- [ ] AC-1.5 `test_section_owns_deeper_headings`: a `##` section containing `###` sub-headings with a tagged fence under one of them yields that fence; the next `##` (and a `#`) ends it.
- [ ] AC-1.5 `test_find_heading_accepts_full_and_bare_forms`: on a document with `## Text`, `find_heading(text, "## Text")` (full form) and `find_heading(text, "Text")` (bare form) return the same `(end, 2)`; on a document whose only `Text` heading is `### Text`, `find_heading(text, "## Text")` is `None` while the bare form returns `(end, 3)`.
- [ ] AC-1.5 `test_adjacent_heading_bounds_the_section`: `## A` immediately followed by `## B` whose section holds a tagged block — `extract(doc, "## A")` (full form) is `[]`, and with `start, level = find_heading(text, "## A")`, `fence_aware_end(text, start, level) == start` (the adjacent heading's line starts exactly at `start` and is a boundary).
- [ ] AC-1.5 `test_heading_lookalikes_are_not_headings`: a fixture placing `#hashtag`, `#######` (seven) and `    ## x` (four-space-indented) where each would end the requested section or start one — the block under the real heading is still the only candidate (the section owns the block past every lookalike), and a lookalike never matches the requested heading (asking for `# hashtag`, `## x` or the seven-run line in the full form yields no heading match; every `extract`/`find_heading` argument in this file's ACs is the full form unless it says bare).
- [ ] AC-1.5/1.6 `test_requested_heading_quoted_inside_a_fence_is_not_a_section_start`: the requested heading appears first inside a ```` ```markdown ```` fence with a tagged block under that quoted copy, then for real with a tagged block under it; `extract` returns only the block under the real heading (the fenced copy is a `body` line, never a heading match, and the tagged block under it is never a candidate).
- [ ] AC-1.6 `test_quoted_tag_inside_longer_fence_is_not_an_opener`: a four-backtick fence whose body contains ` ```bash hmad:exec ` yields no candidate from the quoted line; `test_tag_quoted_inside_a_tilde_fence_is_not_an_opener`: same inside `~~~`; `test_indented_literal_tag_is_not_a_candidate`: `    ```bash hmad:exec` (four spaces) is never a candidate; `test_backtick_in_info_string_is_not_an_opener`: ```` ```bash hmad:exec `x` ```` is inert — not a candidate, not `BadInfoString`, and the following ``` line opens a fence; `test_closer_with_trailing_text_does_not_close`: a ```` ```trailing ```` line inside a quoting fence does not close it; `test_indented_closer_does_not_close`: a ```` ``` ```` line at four spaces inside a bash fence stays in the body and the fence ends at the next 0–3-space closer; `test_indented_fence_body_is_deindented`: openers at 1, 2 and 3 spaces yield bodies with that indentation stripped, and a body line indented less than the opener loses only what it has.
- [ ] AC-1.7 `test_duplicate_headings_refuse`: two identical `###` headings (fixture mirrors `h-mad/invariants.example.md`), requested in the full form → `AmbiguousHeading` with `n == 2`; `test_bare_form_duplicate_headings_refuse`: `## Text` and `### Text` in one document, `find_heading(text, "Text")` (bare form) → `AmbiguousHeading` with `n == 2` — the deliberate tightening over the old `re.search` first-match (design §Scanning; both live `titled_section` targets in `h-mad/SKILL.md` measured unique, so no caller acquires the refusal).
- [ ] AC-1.8 (bounder's own contract) `test_bounder_ignores_a_heading_inside_a_tilde_fence`, `test_bounder_ignores_an_indented_literal_fence`, `test_bounder_from_an_offset_inside_a_fence` (`start` inside an open fence; a fenced `#` after it does not end the section), `test_bounder_offset_after_a_marker_run_on_a_non_closing_line` (`start` immediately after the three backticks of a ```` ```trailing ```` body line; the next fenced `#` still does not end the section), `test_fence_events_trace_on_every_hostile_fixture` (exact event trace — kind, marker, run, indent, info, candidate, level AND the `start`/`end` offsets of every line, on LF and CRLF copies of each fixture — over: balanced and unbalanced four-backtick, tilde-quoted backtick, backtick-in-info, indented literal, trailing-text closer, offset-inside-a-fence), `test_extract_has_no_fence_state_of_its_own` (source assertion on marker-run **recognition**: the literals ```` ``` ```` and `~~~`, the run-length regex, any `in_fence` toggle, and the ATX heading regex (a `#{1,6}` pattern or any `startswith("#")` test) appear in exactly one function body, `_fence_events`; consumers may read `_FenceEvent.kind`/`.marker`/`.run`/`.indent`/`.info`/`.candidate`, and `extract` selects on `.candidate`, never on `.marker`).
- [ ] AC-1.8 (the wire) `test_docsections_delegates_to_the_authoritative_bounder` (WIRE-PIN, in `test_docsections.py`, scaffold above): on the fenced fixture `titled_section` records exactly one `find_heading` call with `(text, heading)` and one `fence_aware_end` call with `(text, start, level)`, and `section_from` records one `fence_aware_end` call with `(text, offset, level)` on the `sys.modules` fake; its RED reason is the assertion on the call record, never an import error.
- [ ] AC-1.8 `test_titled_section_ignores_a_heading_inside_a_fence` (in `test_h_mad_doc_block_exec.py`, function-local `import docsections`): a document whose requested heading first appears quoted inside a ```` ``` ```` fence and then for real — `titled_section(doc, heading)` (bare form, `titled_section`'s contract) returns the real section's body (the old `re.search` at `docsections.py:53` picked the fenced copy).
- [ ] AC-1.8 `test_docsections_has_no_second_bounder`: the source of `docsections.py` defines no function named `_fence_aware_end` and contains no marker-run scanning (the same source predicate as `test_extract_has_no_fence_state_of_its_own`, applied to that file).
- [ ] AC-1.8 `test_docsections_imports_when_collected_alone`: `subprocess.run([sys.executable, "-m", "pytest", "h-mad/tests/test_docsections.py", "-q"], cwd=REPO_ROOT)` exits 0 (nothing but `docsections.py` itself puts `h-mad/scripts` on `sys.path` in that run); `test_docsections_imports_from_an_unrelated_cwd`: `subprocess.run([sys.executable, "-c", "import docsections"], env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "h-mad" / "tests")}, cwd=tmp_path)` exits 0. Both live in `test_h_mad_doc_block_exec.py`, which never imports `docsections` at module level.
- [ ] AC-1.8 the existing `test_docsections.py` tests pass unchanged, and the shared bounder handles the unbalanced four-backtick case the old toggle got wrong (`test_docsections_unbalanced_four_backtick_fence`, in `test_h_mad_doc_block_exec.py`, calling `docsections.titled_section` on the fixture through a function-local `import docsections`: a ```` ```` ```` opener followed by a ```` ``` ```` line and a `# comment` at column 0 — the toggle ends the section at the comment; the bounder does not).
- [ ] AC-1.9 `test_index_zero_refuses`: `select(blocks, 0)` and `select(blocks, -1)` raise `BadIndex` carrying the value, and no lookup happened (the blocks list may be empty).
- [ ] AC-3.7 `test_unknown_info_key_refuses` (`shell=fish`, `mode=x` → `BadInfoString` with that token) and `test_duplicate_info_tokens_refuse` (`hmad:exec hmad:exec`, `shell=strict shell=plain` → `BadInfoString` naming the repeated token); `test_untagged_fence_info_string_is_never_inspected` (` ```bash --frozen ` untagged raises nothing).
- [ ] AC-3.12 `test_invalid_utf8_document_is_unreadable`: a document file containing byte `0xff` → `DocUnreadable` (and, once Task 4 lands, `UNREADABLE reason=doc_unreadable` on the CLI — the CLI half is added in Task 4).
- [ ] `docsections.json` reports `ALL_CAUGHT` with eight rows, each with a `test` key, under `target_command` (`docsections-heading-lookup-reverted` is killed by the WIRE-PIN's empty `find_heading` record, `find_heading` itself untouched); under `docsections-delegation-reverted` the WIRE-PIN fails and **every** other test stays green — all of `test_docsections.py`'s pre-existing tests and all of `test_h_mad_doc_block_exec.py`, the source guard `test_docsections_has_no_second_bounder` and the two docsections-side hostile tests `test_docsections_unbalanced_four_backtick_fence` and `test_titled_section_ignores_a_heading_inside_a_fence` included (the mutation's `test` key is the WIRE-PIN); under `docsections-local-bounder-restored` the source guard goes red (its `test` key), as do the WIRE-PIN and the two hostile tests.

**Mutation rows added to `doc_block_exec.json`** (mechanism per the design's Test Plan table):
`tag-check-removed`, `fence-run-length-ignored`, `section-bound-ignores-level`,
`duplicate-heading-takes-first`, `select-first-on-ambiguous`, `index-below-one-accepted`,
`duplicate-info-token-last-wins`, `unknown-info-key-ignored`, `scanner-duplicated-in-consumer`,
`doc-decode-error-unwrapped`, `closer-trailing-text-accepted`, `body-indent-not-stripped`,
`indented-opener-accepted`, `indented-closer-accepted`, `prefix-state-truncated-mid-line`,
`prefix-fence-state-skipped`, `backtick-in-info-accepted`, `tilde-fence-not-tracked`,
`heading-match-ignores-fence-state`, `heading-lookalike-accepted` (grammar loosened to
`line.lstrip().startswith("#")`), `adjacent-heading-skipped` (boundary predicate `>` instead of
`≥`), `heading-level-pin-ignored` (the full form matching on text alone, ignoring the hash count)
— 22 rows.
**Rows in `docsections.json`** after this task: the four existing (two re-anchored) plus
`docsections-delegation-reverted`, `docsections-syspath-setup-removed`,
`docsections-heading-lookup-reverted` and `docsections-local-bounder-restored` — 8 rows.

**Dependencies on other tasks**: None.

**Expected RED split** (stated in prose; the assembler does not require counts for a wiring task):
- Every test in `test_h_mad_doc_block_exec.py` fails at RED — the module does not exist, so the file's own `import h_mad_doc_block_exec as dbe` raises `ModuleNotFoundError` at collection. That includes `test_docsections_has_no_second_bounder` (which would also fail on its source assertion), `test_docsections_unbalanced_four_backtick_fence` and `test_titled_section_ignores_a_heading_inside_a_fence` (which would also fail because the old toggle mis-bounds and the old regex picks a fenced heading) and the two import tests, which are **insensitive to the docsections delta** (they pass against the unchanged, stdlib-only `docsections.py` as soon as their file collects) and are carried as **regression guards** for the import arrangement the delegating import introduces; their teeth are the `docsections-syspath-setup-removed` mutation, not RED.
- In `test_docsections.py`: the WIRE-PIN — its only new test — fails on its call-sequence assertion (no recorder was ever called: the unchanged caller still uses its local `re.search` and its private `_fence_aware_end`).
- All pre-existing `test_docsections.py` tests are regression guards and must pass at RED.
Wire-scoped revert at 5e: apply `docsections-delegation-reverted` (the one-line replacement above:
the shared import swapped for a private `spec_from_file_location` instance of the same file, no
local bounder restored), leave the helper and the tests intact — the WIRE-PIN must fail (its
`sys.modules` fake is never bound, so no call reaches it) and **every other test stays green**,
`test_docsections_has_no_second_bounder` and the two docsections-side hostile tests included; the
mutation's `test` key stays the WIRE-PIN. The local-restore revert is the separate eighth row,
`docsections-local-bounder-restored`, and is not the 5e wire revert.

---

## Task 2: substitution

**Production file**: `h-mad/scripts/h_mad_doc_block_exec.py`
**Test file**: `h-mad/tests/test_h_mad_doc_block_exec.py`
**Task shape**: `new-behaviour`

**Description**: `substitute(block, subs)` returns a **new** `Block` (`dataclasses.replace`) and a
per-key count dict. An empty map short-circuits to `(dataclasses.replace(block), {})` before any
regex is built. Otherwise: an empty key raises `BadSubstArg("")`; if any key is a substring of
another, raise `OverlappingSubstitution(pairs)` where `pairs` is the sorted list of unordered
`(shorter, longer)` tuples and the CLI's `keys=` counts **distinct keys implicated**; counts are
taken on the original `block.text` (`text.count(key)` per key); every key with count 0 is
collected **in the map's insertion order** and, if any, `MissingSubstitution(keys)` is raised;
replacement is one simultaneous pass — `re.sub("|".join(map(re.escape, keys)), lambda m: subs[m.group(0)], text)` —
so replaced text is never re-scanned and the result is independent of map order.

**Code structure**:
```python
# raises BadSubstArg, MissingSubstitution, OverlappingSubstitution — defined in Task 1
# __all__ += ["substitute"]
def substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]: ...
```

**Acceptance Criteria** (nine tests):
- [ ] AC-2.1 `test_path_substitution_replaces_the_key`: `{"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": "/tmp/x y/gate.py"}` on a block containing the key yields text with the value (a path with a space) and count 1.
- [ ] AC-2.2 `test_absent_key_refuses`: a key not in the block → `MissingSubstitution` with `keys == [key]`; `test_empty_substitution_map_is_a_no_op`: `substitute(block, {})` returns an equal `Block` that is not the same object and `{}`.
- [ ] AC-2.3 `test_two_missing_keys_are_listed_in_map_order`: `{"B": "1", "A": "2"}` both absent → `keys == ["B", "A"]`.
- [ ] AC-2.4 `test_metacharacter_key_is_literal`: key `a.[b]*` replaces only the literal occurrence.
- [ ] AC-2.5 `test_multi_occurrence_count_equals_replacements`: a key occurring 3 times → count 3 and 3 replacements.
- [ ] AC-2.6 `test_value_containing_another_key_is_not_rescanned`: `{"A": "B", "B": "C"}` and `{"B": "C", "A": "B"}` on `A B` both yield `B C` with counts `{"A": 1, "B": 1}`.
- [ ] AC-2.7 `test_overlapping_keys_refuse`: keys `a`, `ab`, `abc` → `OverlappingSubstitution` with `pairs == [("a","ab"),("a","abc"),("ab","abc")]` and three distinct keys implicated.
- [ ] AC-2.8 `test_empty_key_is_refused_by_the_api`: `substitute(block, {"": "v"})` → `BadSubstArg` with `raw == ""`.

**Mutation rows added here**: `missing-key-silently-skipped`, `overlap-resolved-by-order`,
`replacement-sequential`, `empty-map-not-short-circuited`, `empty-key-accepted-by-api` — 5 rows.

**Dependencies on other tasks**: Task 1 (for `Block`).

**Expected RED split**: all nine tests fail with `AttributeError` (`substitute` absent; its three
exceptions already exist from Task 1); expected passing = 0; the Task 1 tests are regression guards and stay green.

---

## Task 3: execution and bounding

**Production file**: `h-mad/scripts/h_mad_doc_block_exec.py`
**Test file**: `h-mad/tests/test_h_mad_doc_block_exec.py`
**Task shape**: `new-behaviour`

**Description**: `run_block(block, *, preamble=None, timeout=30.0)` calls the shared module-level
`_validate_timeout(timeout)` first thing (`float()` conversion, `math.isfinite`, `> 0`; else
`BadTimeout(value)` carrying the raw value — before `mkdtemp`, so nothing is created; the same
validator is `main`'s pre-reservation check in Task 4, so one mutation row,
`timeout-validation-removed`, covers both call sites); then `cwd = None`; inside a `try`: `cwd = tempfile.mkdtemp()`, `os.chmod(cwd, 0o700)`
(a failure of either records `LaunchFailed("mkdtemp", err)` as the pending outcome — for `chmod`
the cwd is set, so cleanup runs), composes the script as `preamble.rstrip("\n") + "\n" + block.text`
when `preamble` is given else `block.text`, and launches **one** `bash` with
`subprocess.Popen(["bash", "-euo", "pipefail", "-c", script] if block.shell == "strict" else ["bash", "-c", script], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", start_new_session=True)`
(a `Popen` `OSError` records `LaunchFailed("spawn", err)`). `communicate(timeout=timeout)`; on
`TimeoutExpired`: `proc.poll()` **then** `os.killpg(proc.pid, signal.SIGKILL)` — `ProcessLookupError`
means already reaped; any other `OSError` records `LaunchFailed("reap", err, pgid=proc.pid)`;
then a bounded drain `communicate(timeout=DRAIN_SECONDS)`, on whose own `TimeoutExpired` the helper
closes `proc.stdout`/`proc.stderr` itself and calls `proc.wait()` **only** if the group was
signalled or already gone (never on the `reap` branch); the post-kill drain — finished or timed out
— **records** `BlockTimeout(timeout)` as the pending outcome exactly as the ordinary timeout path
does, unless a `LaunchFailed("reap")` was recorded (design v1.61 §Execution).

**The helper's own I/O on the child is mapped by the same taxonomy** (design v1.65 §Execution,
design audit v62). The first `communicate(timeout=timeout)` is guarded by `except OSError as err`
beside its `except subprocess.TimeoutExpired`: the guard records
`LaunchFailed("collect", err, pgid=proc.pid)` as the pending outcome and then runs **the same
sequence the timeout path runs** — `proc.poll()`, `os.killpg(proc.pid, signal.SIGKILL)` with
`ProcessLookupError` meaning already reaped, the bounded drain `communicate(timeout=DRAIN_SECONDS)`,
and on that drain's `TimeoutExpired` the pipe closes plus `proc.wait()` **iff** the group was
signalled or already gone. Three precedence rules govern what those later steps may do to the
pending outcome, and each `__context__` below is **assigned explicitly** (`err.__context__ = pending`),
because nothing is ever raised inside the handler and Python's implicit chaining therefore never
fires:
(a) an `OSError` from any later step under a pending `collect` is attached as that pending error's
`__context__` and does **not** replace it;
(b) a non-`ESRCH` `killpg` error is the `reap` stage and **replaces** the pending `collect`, the
`collect` error becoming the new `LaunchFailed("reap", err, pgid=proc.pid)`'s `__context__`;
(c) under an **ordinary** timeout, an `OSError` from the drain `communicate`, from either pipe
close, or from `proc.wait()` **replaces** the pending `BlockTimeout(timeout)` with
`LaunchFailed("collect", err, pgid=proc.pid)` whose `__context__` is that `BlockTimeout`.
`stage=collect` ranks with `stage=reap` in the precedence (both exit 2, one rank, below
`CleanupFailed`), so cleanup and the read-back still run as usual and a removal that fails is still
`CleanupFailed` with the `LaunchFailed` as `__cause__`. Nothing raises
inside the handler; the pending outcome is raised only by the selection after the `finally`. The `finally`
runs `shutil.rmtree(cwd)` (no `ignore_errors`) when `cwd is not None`, recording an `OSError` as
`cleanup_error` and never raising. **After** the `try`/`finally`, select: if `cwd is not None` and
(`cleanup_error is not None` or `os.path.lexists(cwd)`) → raise `CleanupFailed(cwd, cleanup_error)`
`from pending` (so `__cause__` is the pending `BlockTimeout`/`LaunchFailed` when there is one, else
`cleanup_error`); elif `pending is not None` → raise it; else return
`RunResult(rc=proc.returncode, stdout=stdout, stderr=stderr, shell=block.shell)`. `run_block` never substitutes.

**Code structure**:
```python
# raises BadTimeout, BlockTimeout, CleanupFailed, LaunchFailed — defined in Task 1
# __all__ += ["RunResult", "run_block"]
@dataclass(frozen=True)
class RunResult:     # lands here, beside run_block (design §Implementation Order, Task 3)
    rc: int
    stdout: str
    stderr: str
    shell: str

def _validate_timeout(value: object) -> float:
    """Shared by run_block (first thing) and main (before _reserve): float(value),
    math.isfinite, > 0; else BadTimeout(value) carrying the raw value."""

def _compose(preamble: str | None, text: str) -> str: ...
def run_block(block: Block, *, preamble: str | None = None, timeout: float = 30.0) -> RunResult: ...
```

**Acceptance Criteria** (every test here calls `dbe.run_block` in-process at the API — none goes
through the CLI; the ten that inject a fault are marked `(in-process, injected: ` + the seam`)` so the
transport split in the Conventions is visible per test — eight of the ten patch one of the six
module-level seams, and the two `stage=collect` tests use the instance-level `Popen` wrapper the
Conventions describe. **Every test that patches
`dbe.shutil.rmtree` binds `real_rmtree = shutil.rmtree` BEFORE `monkeypatch.setattr(dbe.shutil, "rmtree", fake)`**
— `dbe.shutil` is the process-global module, so without the binding the teardown would call the
fake — **and removes a retained cwd with `real_rmtree(cwd)` in its `finally`**, the same pattern
as AC-4.6's `real_killpg`; the five such tests are named with `real_rmtree` below):
- [ ] AC-3.1 `test_block_runs_in_the_temp_cwd`: a `pwd` block reports a directory that is neither the repo root nor the document's directory and is gone afterwards.
- [ ] AC-3.2 `test_block_leaves_the_working_tree_untouched`: a block that creates a file leaves `git status --porcelain` byte-identical.
- [ ] AC-3.3 `test_unset_variable_fails_under_strict`: `echo $UNSET_X` → rc ≠ 0 strict, rc 0 plain.
- [ ] AC-3.4 `test_bare_exit_in_plain_mode_returns_rc`: `exit 3` under `shell=plain` → `rc == 3`, and the test process is alive.
- [ ] AC-3.5 `test_pipefail_strict_vs_plain`: `false | true` → rc ≠ 0 strict, 0 plain.
- [ ] AC-3.6 `test_streams_are_separate_str`: stdout/stderr unmerged; `é` round-trips; `printf '\xff'` yields U+FFFD.
- [ ] AC-3.11 `test_preamble_binds_a_variable_and_leaves_text_unchanged`; `test_preamble_and_substitution_compose` (preamble + a substituted key: the executed text carries the value); `test_preamble_without_trailing_newline_still_precedes_the_block`.
- [ ] AC-3.12 `test_failing_preamble_is_visible_as_the_combined_rc`: preamble `false` under strict → rc ≠ 0 and its stderr.
- [ ] AC-3.13 `test_cwd_mode_is_0700_under_hostile_umask`: with `os.umask(0o777)` around the call (restored in `finally`), a block running `stat -f %Lp .` (darwin) / `stat -c %a .` (GNU) prints `700`; `test_chmod_failure_is_a_verdict_and_removes_the_cwd` (in-process, injected: `os.chmod` injected to raise → `LaunchFailed("mkdtemp")` and the created directory is gone); `test_chmod_rollback_failure_is_cleanup_failed` (in-process, injected: `os.chmod` and `shutil.rmtree` both injected → `CleanupFailed` whose `__cause__` is the `LaunchFailed`; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_no_mktemp_invocation_in_source`.
- [ ] AC-3.14 `test_cleanup_failure_is_reported` (`mkdir keep && chmod 000 keep` → `CleanupFailed` with `cleanup_error` a `PermissionError`; skipped when `euid == 0`; the test `chmod 700`s and removes the tree in its `finally`); `test_cleanup_failure_carries_the_os_error` (in-process, injected: `rmtree` injected to raise; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_cleanup_readback_catches_silent_retention` (in-process, injected: `rmtree` injected as a no-op; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_cleanup_error_after_successful_removal_is_still_a_failure` (in-process, injected: the fake calls `real_rmtree` — bound before the patch — then raises; `finally` calls `real_rmtree` under `ignore_errors=True` since the tree is already gone); `test_cleanup_failure_outranks_timeout_injected` (in-process, injected: `rmtree` raising under `sleep 300`, `timeout=1` → `CleanupFailed`, `__cause__` is the `BlockTimeout`, `cleanup_error` is the injected error, cwd read back present, removed in `finally` by `real_rmtree`, bound before the patch); `test_cleanup_failure_outranks_timeout` (real `chmod 000` fixture, skipped under root); `test_normal_run_reads_back_absent`.
- [ ] AC-4.6 `test_mkdtemp_failure_is_a_verdict` (in-process, injected: `tempfile.mkdtemp` injected → `LaunchFailed("mkdtemp")`, nothing to clean); `test_spawn_failure_is_a_verdict` (`PATH` = empty dir → `LaunchFailed("spawn")`, cwd gone); `test_reap_failure_is_a_verdict_within_the_drain_bound` (in-process, injected: `os.killpg`): `real_killpg = os.killpg` bound **before** `monkeypatch.setattr(dbe.os, "killpg", fake)`; `fake` records the pgid and raises `PermissionError`; `Popen` wrapped in a recording pass-through; `sleep 300` under `timeout=1` → `LaunchFailed("reap", pgid=proc.pid)` raised within `1 + DRAIN_SECONDS + 2` s; teardown in `finally`: `real_killpg(pgid, SIGKILL)`, `recorded.wait()`, then assert `real_killpg(pgid, 0)` raises `ProcessLookupError`.
- [ ] AC-4.6 `test_communicate_oserror_is_launch_failed_collect` (in-process, injected: the recorded `Popen` instance's bound `communicate`): the test binds `real_killpg = os.killpg` **before** anything is patched, then installs the recording `Popen` pass-through with `monkeypatch.setattr(dbe.subprocess, "Popen", recording_popen)`, where `recording_popen` calls the real `subprocess.Popen`, appends the instance to a list the test holds, shadows `inst.communicate` with a wrapper that raises `OSError(errno.EIO, "Input/output error")` on its **first** call and delegates to the saved bound method afterwards, and returns the instance (the wrap happens inside the pass-through because `run_block` calls `communicate` immediately after `Popen` returns; the test file imports `errno`). Under a block that would otherwise `RAN` (`echo hi`, default `timeout`), `dbe.run_block` raises `LaunchFailed` with `stage == "collect"`, `err.errno == errno.EIO`, `pgid == recorded.pid` and no `RunResult` returned; the cwd — read from the pass-through's recorded `cwd` keyword argument — is gone; and the group is gone — `real_killpg(pgid, 0)` raises `ProcessLookupError`, because the helper killed and reaped the child as a timed-out one — which is the test's last substantive assertion, with a `finally` that sends `real_killpg(pgid, signal.SIGKILL)` ignoring `ProcessLookupError` so a surviving group is never left behind when the assertion fails.
- [ ] AC-4.6 `test_drain_wait_oserror_is_launch_failed_collect` (in-process, injected: the recorded `Popen` instance's bound `wait`): the same pass-through, wrapping `inst.wait` instead — first call raises `OSError(errno.EIO, "Input/output error")`, later calls delegate, so the teardown's own `recorded.wait()` passes through. The **escapee fixture is required, not optional**: `Popen.communicate()` calls `self.wait()` internally after a successful read, so under a plain `sleep 300` the wrapper would fire from inside the drain rather than from the helper's own `proc.wait()`. The block is AC-5.5's `python3 ESC_PATH PID_PATH & sleep 300` with `esc.py` and the pid path delivered through the substitution map, run at `timeout=1`: the leader is signalled, the `os.setsid()` escapee holds the pipes, the drain `communicate(timeout=DRAIN_SECONDS)` raises `TimeoutExpired` before reaching its internal wait, the helper closes both pipes and calls `proc.wait()` on the signalled branch, and that call trips the wrapper — precedence rule (c). The raised error is a `LaunchFailed` with `stage == "collect"`, `pgid == recorded.pid`, and `__context__` an instance of `dbe.BlockTimeout`, returned within `1 + DRAIN_SECONDS + 2` s wall time, with the block's cwd gone; in `finally` the test reads the pid file, sends `os.kill(pid, signal.SIGKILL)` ignoring `ProcessLookupError`, then calls `recorded.wait()`.
- [ ] AC-5.1 `test_sleeping_block_times_out`: `sleep 300`, `timeout=1` → `BlockTimeout` within `1 + DRAIN_SECONDS + 2` s.
- [ ] AC-5.2 `test_in_group_descendant_is_reaped`: block text `sleep 300 & echo $! > PID_PATH; sleep 300`, run as `dbe.run_block(dbe.substitute(block, {"PID_PATH": str(pid_file)})[0], timeout=1)` where `pid_file` is under the test's `tmp_path` — the substitution map is how the absolute path reaches the block, because the child's cwd is a fresh private directory nothing can be placed in beforehand → after the timeout the pid read from `pid_file` is gone: `os.kill(pid, 0)` raises `ProcessLookupError`; `finally` reads the pid file if present and sends `os.kill(pid, signal.SIGKILL)` ignoring `ProcessLookupError`.
- [ ] AC-5.3 `test_no_timeout_invocation_in_source`: no argv token or shell command word `timeout`/`gtimeout` in the module source (a substring match on `timeout=`/`TimeoutExpired`/`BlockTimeout`/`--shell-timeout` must not trip it).
- [ ] AC-5.4 `test_temp_cwd_removed_after_timeout`.
- [ ] AC-5.5 both escapee tests share one fixture construction: the test writes `esc.py` under its own `tmp_path` (`os.setsid()`; write `os.getpid()` to the PID path given as `sys.argv[1]`; `time.sleep(300)` holding stdout) and passes BOTH absolute paths through the substitution map — `dbe.run_block(dbe.substitute(block, {"ESC_PATH": str(esc), "PID_PATH": str(pid_file)})[0], timeout=1)` — because the child's cwd is a fresh private directory, so `esc.py` cannot be placed there and only the substituted absolute paths make the block executable. `test_timeout_survives_a_group_that_already_emptied`: block text `python3 ESC_PATH PID_PATH & exit 0` (the leader exits at once; the group is empty when `killpg` runs) → `BlockTimeout`, no traceback, and the block's cwd is gone. `test_timeout_drain_is_bounded_against_an_escapee`: block text `python3 ESC_PATH PID_PATH & sleep 300` → `BlockTimeout` within `1 + DRAIN_SECONDS + 2` s wall time, cwd gone. Teardown for both, in `finally`: read the pid file, `os.kill(pid, signal.SIGKILL)` ignoring `ProcessLookupError`, then assert the block's cwd (captured through a recording `Popen` pass-through's `cwd` kwarg) no longer exists.
- [ ] AC-5.6 `test_nonpositive_timeout_refuses_before_spawn`: `timeout=0`, `-1`, `math.nan`, `math.inf` → `BadTimeout` and the recording `Popen` pass-through was never called and no directory was created.

**Mutation rows added here**: `strict-flags-dropped`, `preamble-separator-dropped`,
`preamble-composed-with-unsubstituted-text`, `cwd-not-passed`, `chmod-0700-removed`,
`cleanup-errors-ignored`, `cleanup-readback-removed`, `precedence-timeout-raised-in-handler`,
`launch-oserror-unwrapped`, `killpg-replaced-by-kill`, `poll-before-killpg-removed`,
`killpg-esrch-uncaught`, `drain-unbounded`, `timeout-validation-removed`,
`chmod-failure-unwrapped`, `chmod-rollback-unguarded`, `cleanup-error-ignored-when-tree-gone`,
`timeout-invocation-planted`, `mktemp-invocation-planted` (`tempfile.mkdtemp()` replaced by
`subprocess.run(["mktemp", "-d"], capture_output=True, text=True).stdout.strip()` — valid Python and
exactly the forbidden invocation; killed by `test_no_mktemp_invocation_in_source`),
`collect-oserror-unmapped` (the `except OSError` around the first `communicate(timeout)` removed, so
a pipe-read failure escapes as a traceback with the child unreaped; killed by
`tests/test_h_mad_doc_block_exec.py::test_communicate_oserror_is_launch_failed_collect`),
`drain-oserror-unmapped` (the guard around the post-kill drain, the two pipe closes and the `wait()`
removed, so a failure there escapes past the pending `BlockTimeout`; killed by
`tests/test_h_mad_doc_block_exec.py::test_drain_wait_oserror_is_launch_failed_collect`) — 21 rows.
The two `collect` rows discriminate mutually: under `collect-oserror-unmapped` the drain test still
sees a `TimeoutExpired` from its first `communicate`, not an `OSError`, so it stays green; under
`drain-oserror-unmapped` the communicate test's later steps raise nothing (the child is already
killed and reaped, so the drain returns), so it stays green.

**Dependencies on other tasks**: Task 1 (`Block`); Task 2 only for the two
compose-with-substitution tests, which call `substitute` first.

**Expected RED split**: every test in this task fails (`run_block`, `RunResult` and
`_validate_timeout` absent; the four exceptions already exist from Task 1)
except `test_no_timeout_invocation_in_source` and `test_no_mktemp_invocation_in_source`, which are
**regression guards** that pass from the first run (the source scan finds nothing in a module that
does not yet spawn); expected passing = 2; Tasks 1–2 tests stay green.

---

## Task 4: CLI, stream artifacts, and the registry entry

**Production file**: `h-mad/scripts/h_mad_doc_block_exec.py` and `h-mad/SKILL.md` (Helper-scripts registry entry)
**Test file**: `h-mad/tests/test_h_mad_doc_block_exec.py`
**Task shape**: `new-behaviour`

**Description**: `main(argv)` parses with `argparse.ArgumentParser(allow_abbrev=False)`:
positional `doc`, `--heading` (required), `--index` (`type=str`), `--subst` (`action="append"`),
`--preamble-file`, `--shell-timeout` (`type=str`, default `"30"`), `--stdout`, `--stderr`; no
`--all`/`--dir`/glob argument exists. Order: `extract` → `select` (a non-integer `--index` is
`BadIndex(raw)`; parsed ints go to `select`) → build the map from `--subst` (split once on the
first `=`; no `=` or empty key → `BadSubstArg(raw)`; repeated key → `BadSubstArg(raw, duplicate_key=k)`)
→ `substitute` → `_validate_timeout(args.shell_timeout)` (the shared validator from Task 3:
`float()` conversion, `math.isfinite`, `> 0`, else `BadTimeout(raw)` — **before** `_reserve`, so no
artifact exists for any input-only refusal; `run_block` re-validates the float it receives, and the
existing `timeout-validation-removed` row covers both call sites — no new row) → `--preamble-file`
read as strict UTF-8 (`OSError`/`UnicodeDecodeError` → `PreambleUnreadable`) → **reserve** stdout
then stderr → alias check → `run_block` → final writes.
Reservation, per path, is a two-arm loop bounded to three round trips: `os.open(path, os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_EXCL, 0o644)`
(created=True) else on `FileExistsError` `os.open(path, os.O_WRONLY|os.O_APPEND|os.O_NONBLOCK)`
(created=False; `FileNotFoundError` here restarts the loop); the descriptor must `fstat` as
`S_ISREG` else it is closed and refused; the handle is `os.fdopen(fd, "a", encoding="utf-8")`. If the
second reservation fails, the first handle is closed and unlinked **only if** created. The whole
stage — both loops, the `fstat` checks, the rollback — is one `try/except OSError` mapped to
`StreamPathUnwritable`; loop exhaustion maps there too. Alias: `os.fstat` on both handles,
equal `(st_dev, st_ino)` → unlink the files **this call created** and raise `StreamPathsAlias`;
the alias check does **not** close the handles itself — closing is the backstop `finally`'s job
through `_close_stream`, because a close inside the reservation's mapped region would turn an
injected close failure into `stream_path_unwritable`, while
`test_backstop_close_failure_does_not_outrank_a_refusal` asserts `stream_paths_alias` (design
v1.58, stream artifacts). The rollback when the SECOND reservation fails is unchanged: it still
closes and unlinks the first handle inside the region. Both handles are
held in a `try`/`finally` spanning the alias check, `run_block` and the final writes. On the `RAN`
path: for stdout then stderr, `_final_write(handle, text)` — `seek(0); truncate(); write(text); flush()`
inside a `try` whose `finally` calls `_close_stream(handle)`, the whole thing inside the mapped
region (first error wins; a close error is chained as `__context__`) — then **immediately** verify:
`Path(path).read_bytes() == text.encode("utf-8", errors="replace")`; a mismatch, missing file or
`OSError` on the read is `StreamWriteFailed(written, failed, skipped, verify=stream)`. A stdout
failure (write or verify) skips stderr: `failed: stdout` / `skipped: stderr`; a stderr failure
leaves stdout written: `written: stdout` / `failed: stderr`. The backstop `finally` calls
`_close_stream` on each handle not already closed under `except OSError`, recording the first
`(stream, error)` as `close_error` and never raising; after the `try`/`finally`, select: pending
exit-2 `DocBlockError` → raise it with `close_error` attached as `__context__`; else if
`close_error` → raise `StreamCloseFailed(stream, error)` `from pending` (pending is a
`BlockTimeout` or `None`), printed as `UNREADABLE reason=stream_close_failed` plus a `stream:` line carrying the
stream name and an `os_error:` line carrying the error text, so the operator learns which stream's close failed; else the pending outcome / the result. `main` catches `DocBlockError`
and prints one `DOCBLOCK:` line per the verdict table plus detail lines, returning 0 or 2 per the
partition; it never lets a `DocBlockError` or an `OSError` of its own escape. The verdict mapping
is two module-level objects: `VERDICT_TABLE: dict[str, int]`, keyed by the **emitted line head at
full granularity** (22 heads: `RAN`, `NOT_FOUND`, `AMBIGUOUS`, `AMBIGUOUS_HEADING`, `BAD_INDEX`,
`BAD_TIMEOUT`, `BAD_SUBST`, `SUBST_MISSING`, `SUBST_OVERLAP`, `BAD_INFO`, `TIMEOUT`,
`CLEANUP_FAILED`, `LAUNCH_FAILED stage=mkdtemp`, `LAUNCH_FAILED stage=spawn`,
`LAUNCH_FAILED stage=reap`, `LAUNCH_FAILED stage=collect`, `UNREADABLE reason=doc_unreadable`, `UNREADABLE reason=preamble_unreadable`,
`UNREADABLE reason=stream_paths_alias`, `UNREADABLE reason=stream_path_unwritable`,
`UNREADABLE reason=stream_write_failed`, `UNREADABLE reason=stream_close_failed`) → exit code, and
`_VERDICT_FOR: dict[type[DocBlockError], Callable[[DocBlockError], str]]`, mapping each exception
class to the function that renders its head (so `LaunchFailed` renders `stage=` from its `stage`
field and each `UNREADABLE` class its own `reason=`); `main` renders the head with `_VERDICT_FOR`,
looks the exit code up in `VERDICT_TABLE`, and appends the verdict's variable fields after the
head — the complete list, derived from the design's verdict table (one entry per variable slot in a
`DOCBLOCK:` line): `rc=`/`blocks=`/`shell=` (`RAN`), `blocks=` and `heading=` (`AMBIGUOUS`),
`count=` and `heading=` (`AMBIGUOUS_HEADING`), `index=` (`BAD_INDEX`), `value=` (`BAD_TIMEOUT`),
`arg=` (`BAD_SUBST`), `keys=` (`SUBST_MISSING`, `SUBST_OVERLAP`), `key=` (`BAD_INFO`), `seconds=`
(`TIMEOUT`), `path=` (`CLEANUP_FAILED`), `stage=` (`LAUNCH_FAILED`), `reason=` (`UNREADABLE`) —
14 field names. The emittable detail keys are a module-level tuple `DETAIL_KEYS`, so tests can
enumerate all three. `StreamWriteFailed`'s `written`/`skipped` lists are joined with a space
before printing (`written: stdout`, never Python list syntax).
The `h-mad/SKILL.md` Helper-scripts entry for `h_mad_doc_block_exec.py` states the CLI contract
and carries a table with one row per emittable line — every `DOCBLOCK:` token and every detail
key, `stream:` included — each with a remedy; because AC-4.5 matches **`VERDICT_TABLE` keys**, the
table carries one row per `LAUNCH_FAILED stage=` head, `LAUNCH_FAILED stage=collect` included, not a
single generic row with a placeholder stage (design v1.65's verdict table shows the generic
spelling; the per-stage rows are what the impl-plan's head-granular table requires); the entry starts at the bullet ``- `h_mad_doc_block_exec.py` —`` and its
table rows are the lines beginning `| \`` up to the next `- ` bullet.

**Code structure**:
```python
# raises StreamPathUnwritable, StreamPathsAlias, PreambleUnreadable, StreamWriteFailed,
# StreamCloseFailed — defined in Task 1
# __all__ += ["main"]
VERDICT_TABLE: dict[str, int] = {          # emitted line head → exit code; 22 entries, listed in the description
    "RAN": 0, "NOT_FOUND": 0, "AMBIGUOUS": 0, "AMBIGUOUS_HEADING": 0, "BAD_INDEX": 0, "BAD_TIMEOUT": 0,
    "BAD_SUBST": 0, "SUBST_MISSING": 0, "SUBST_OVERLAP": 0, "BAD_INFO": 0, "TIMEOUT": 0,
    "CLEANUP_FAILED": 2, "LAUNCH_FAILED stage=mkdtemp": 2, "LAUNCH_FAILED stage=spawn": 2, "LAUNCH_FAILED stage=reap": 2,
    "LAUNCH_FAILED stage=collect": 2,
    "UNREADABLE reason=doc_unreadable": 2, "UNREADABLE reason=preamble_unreadable": 2,
    "UNREADABLE reason=stream_paths_alias": 2, "UNREADABLE reason=stream_path_unwritable": 2,
    "UNREADABLE reason=stream_write_failed": 2, "UNREADABLE reason=stream_close_failed": 2,
}
_VERDICT_FOR: dict[type[DocBlockError], Callable[[DocBlockError], str]] = {...}   # class → head renderer (every DocBlockError subclass)
DETAIL_KEYS: tuple[str, ...] = ("missing_key:", "overlap:", "duplicate_key:", "os_error:", "pgid:",
                                "written:", "failed:", "skipped:", "verify:", "stream:")   # 10

def _reserve(path: str) -> tuple[io.TextIOWrapper, bool]:       # (handle, created)
def _final_write(handle: io.TextIOWrapper, text: str) -> None:  # seam: seek/truncate/write/flush, close in finally
def _close_stream(handle: io.TextIOWrapper) -> None:            # seam: the one closure primitive
def _verify(path: str, text: str) -> bool: ...
def main(argv: Sequence[str] | None = None) -> int: ...
if __name__ == "__main__": sys.exit(main())
```

**Acceptance Criteria**:
- [ ] AC-1.3/1.4/1.7/1.9 CLI halves (subprocess): `test_cli_ambiguous_prints_blocks_and_heading` (`AMBIGUOUS blocks=2 heading=` followed by the `--heading` argument verbatim, exit 0), `test_cli_index_past_end_is_not_found`, `test_cli_duplicate_headings_refuse` (`AMBIGUOUS_HEADING count=2`, nothing executed), `test_cli_index_zero_and_negative_are_bad_index` (`BAD_INDEX index=0`/`-1`, exit 0, no side effect), `test_non_integer_index_is_bad_index`.
- [ ] AC-2.2/2.3/2.7/2.8 CLI halves (subprocess): `test_cli_missing_keys_list_in_argument_order`, `test_cli_overlap_counts_distinct_keys`, `test_cli_no_subst_runs` (zero `--subst`), `test_subst_without_equals_is_bad_subst`, `test_subst_empty_key_is_bad_subst`, `test_duplicate_substitution_key_refuses` (`duplicate_key: K`), `test_subst_value_may_contain_equals` — each refusal executes nothing and reserves nothing (no artifact created).
- [ ] AC-3.7 (subprocess) `test_cli_unknown_info_key_is_bad_info`; AC-3.12 (subprocess) `test_invalid_utf8_document_is_unreadable` CLI half (`UNREADABLE reason=doc_unreadable`, exit 2) and `test_invalid_utf8_preamble_is_unreadable`, `test_unreadable_preamble_path_refuses` (`preamble_unreadable`, exit 2, no side effect); `test_cli_preamble_file_reaches_the_block`.
- [ ] AC-3.8 (subprocess) `test_stream_paths_receive_the_streams` (two files differ for a block writing different text); `test_streams_optional`; `test_stream_paths_truncate_an_existing_file`; `test_streams_untouched_after_a_timeout`; (in-process main, each) `test_stream_write_failure_after_the_run_is_a_refusal` (`_final_write` injected to raise → `UNREADABLE reason=stream_write_failed`, exit 2, no `rc=`); `test_first_stream_write_failure_skips_the_second` (`_final_write` injected to raise on the first handle: `failed: stdout` / `skipped: stderr`, stderr bytes unchanged); `test_second_stream_write_failure_leaves_the_first_as_written` (`_final_write` injected to raise on the second handle: `written: stdout` / `failed: stderr`); `test_final_write_close_failure_is_mapped` (seam patched to call the real `_final_write` with a recording proxy whose `close` alone raises → `stream_write_failed`, `failed: stdout`, exit 2, no traceback; a regression test for `final-write-close-not-in-finally`, not its `test` key); `test_final_write_failure_before_close_still_closes` (proxy's `flush` and `close` both raise → same verdict and the proxy's `close` was called; the canonical `test` key of `final-write-close-not-in-finally`); `test_final_write_readback_catches_a_silent_no_op` (`_final_write` injected as a no-op → `stream_write_failed` with `verify: stdout`, `failed: stdout` / `skipped: stderr`, stderr bytes unchanged); `test_backstop_close_failure_on_timeout_is_mapped` (`_close_stream` injected to raise under `sleep 300`, `--shell-timeout 1`, `--stdout` given → `UNREADABLE reason=stream_close_failed`, a `stream: stdout` line and an `os_error:` line, exit 2, no traceback, cwd gone); `test_backstop_close_failure_does_not_outrank_a_refusal` (same injection under an aliased pair → still `stream_paths_alias`, exit 2, no traceback); `test_stream_handles_are_closed_on_every_path` (recording `os.open` pass-through, `_final_write` injected for the first-write-failure leg; after `TIMEOUT` and after a first-write failure, `os.fstat` on each recorded fd raises `OSError`).
- [ ] AC-3.9 (subprocess) `test_symlinked_stream_paths_refuse`, `test_dot_slash_spelling_refuses`, `test_hard_linked_stream_paths_refuse` (`os.link`): `UNREADABLE reason=stream_paths_alias`, exit 2, block not run, both handles closed (by the backstop `finally`), a created file unlinked.
- [ ] AC-3.10 (subprocess) `test_stream_path_under_a_regular_file_refuses` (parent is a regular file → `stream_path_unwritable`, exit 2, no traceback, side-effect block left nothing); `test_stream_path_fifo_without_reader_refuses_bounded` (`os.mkfifo` path, CLI run with `timeout=5` in the test's `subprocess.run`, refusal within 1 s); `test_stdout_survives_a_failed_stderr_reservation` (pre-existing stdout byte-identical; a created stdout unlinked).
- [ ] AC-4.1 (subprocess) `test_ran_line_and_exit_zero_with_nonzero_rc`: `DOCBLOCK: RAN rc=3 blocks=1 shell=plain`, exit 0.
- [ ] AC-4.2 `test_verdict_table_exit_codes`: parametrised over the 22 `VERDICT_TABLE` heads with one producer each — a subprocess producer for the 16 heads a real input or real fault yields (`RAN`, `NOT_FOUND`, `AMBIGUOUS`, `AMBIGUOUS_HEADING`, `BAD_INDEX`, `BAD_TIMEOUT`, `BAD_SUBST`, `SUBST_MISSING`, `SUBST_OVERLAP`, `BAD_INFO`, `TIMEOUT`, `LAUNCH_FAILED stage=spawn` via an empty `PATH`, `UNREADABLE reason=doc_unreadable`, `UNREADABLE reason=preamble_unreadable`, `UNREADABLE reason=stream_paths_alias`, `UNREADABLE reason=stream_path_unwritable`) and an in-process `main(argv)` producer for the 6 that need a fault injection (`CLEANUP_FAILED` via `shutil.rmtree` — `real_rmtree` bound first, retained cwd removed in `finally`, `LAUNCH_FAILED stage=mkdtemp` via `tempfile.mkdtemp`, `LAUNCH_FAILED stage=reap` via `os.killpg`, `LAUNCH_FAILED stage=collect` via the instance-level `Popen` wrapper of `test_communicate_oserror_is_launch_failed_collect` — the same `echo hi` block, the same `real_killpg` teardown, `UNREADABLE reason=stream_write_failed` via `_final_write`, `UNREADABLE reason=stream_close_failed` via `_close_stream`); either way the assertion compares the produced exit code (process exit or `main`'s return) with `VERDICT_TABLE[head]` and the emitted line starts with `DOCBLOCK: ` followed by the head; **for the `LAUNCH_FAILED stage=reap` and `LAUNCH_FAILED stage=collect` producers the captured output also carries a `pgid:` detail line** (the two stages on which `LaunchFailed` sets `pgid`; this is the only place `pgid:` is asserted at the CLI, the design's AC-4.6 row expecting it there); one assertion that `set(params) == set(VERDICT_TABLE)`; `test_every_docblockerror_subclass_has_a_verdict` (walk `DocBlockError.__subclasses__()` recursively; each is a `_VERDICT_FOR` key, and each renderer's head for a representative instance is a `VERDICT_TABLE` key).
- [ ] AC-4.2 exit propagation (subprocess): `test_cli_exit_zero_propagates` (a document whose section has no tagged fence → `DOCBLOCK: NOT_FOUND`, process exit 0) and `test_cli_exit_two_propagates` (a document containing byte `0xff` → `DOCBLOCK: UNREADABLE reason=doc_unreadable`, process exit 2) — both compare the process exit with `VERDICT_TABLE[head]`, pinning that `sys.exit(main())` propagates `main`'s return value.
- [ ] AC-4.3 (subprocess) `test_no_refusal_carries_rc`; AC-4.4 (subprocess) `test_only_ambiguous_carries_blocks`.
- [ ] AC-4.5 `test_every_emittable_line_has_a_registry_row` (every `VERDICT_TABLE` key and every `DETAIL_KEYS` entry appears as the first backtick token of a row in the SKILL.md entry) and `test_registry_rows_cover_only_emittable_lines` (every row's first token is in that union).
- [ ] AC-4.6 CLI halves: `test_cli_launch_failed_lines` — the `stage=spawn` leg (subprocess, empty `PATH`) and the `stage=mkdtemp` leg (in-process main, `tempfile.mkdtemp` injected), each its own `LAUNCH_FAILED stage=` head with an `os_error:` line, exit 2, no `rc=` — reap and collect are covered in Task 3 at the API and here by the table test, which is where their `pgid:` detail line is asserted at the CLI.
- [ ] AC-5.6 (subprocess) `test_cli_bad_timeout_values`: `0`, `-1`, `nan`, `inf`, `abc` → `BAD_TIMEOUT value=` followed by the argument verbatim, exit 0, no side effect, **and with `--stdout`/`--stderr` given: a path that did not exist is still absent afterwards, and a pre-existing file keeps its bytes** (validation ran before `_reserve`); `test_non_numeric_timeout_is_bad_timeout`.
- [ ] Parser (subprocess): `test_parser_rejects_all_dir_and_abbreviations` (`--all`, `--dir x`, `--shell-t 5` → argparse usage error, exit 2, no `DOCBLOCK:` line).

**Mutation rows added here**: `subst-split-on-every-equals`, `subst-duplicate-key-last-wins`,
`index-nonint-unmapped`, `timeout-nonnumeric-unmapped`, `preamble-decode-error-unwrapped`,
`stream-reserved-with-truncation`, `final-write-close-not-in-finally`,
`verify-deferred-past-second-write`, `final-write-not-verified`, `nonregular-stream-accepted`,
`stream-open-blocking`, `stream-alias-check-removed`, `exit-partition-flipped`,
`rc-leaked-into-refusal`, `stream-open-oserror-unwrapped`, `backstop-close-unmapped`,
`backstop-close-outranks-error`, `registry-row-removed` (targets `h-mad/SKILL.md`),
`detail-line-undocumented`, `allow-abbrev-restored` (the parser built with `allow_abbrev=True`, so
`--shell-t 5` aliases `--shell-timeout`; killed by `test_parser_rejects_all_dir_and_abbreviations`),
`stream-write-oserror-unwrapped` (the `except OSError` mapping around `_final_write` and its
read-back removed, so a write failure escapes as a traceback; killed by
`test_stream_write_failure_after_the_run_is_a_refusal`) — 21 rows. With Tasks 1, 2, 3 that is
22 + 5 + 21 + 21 = **69 rows**, 67 of the helper's source and 2 of `SKILL.md`, matching design v1.65.

**Dependencies on other tasks**: Tasks 1, 2, 3.

**Expected RED split**: every test in this task fails (`main` absent → the subprocess tests see the
CLI exit 1 with a traceback, the in-process `main` tests and the API tests raise `AttributeError`); expected passing = 0; Tasks 1–3 tests are
regression guards and stay green. `doc_block_exec.json` must report `ALL_CAUGHT` over all 69 rows
before this task is GREEN.

---

## Task 5: tag the gate fence and migrate the executing consumer

**Production file**: `h-mad/SKILL.md` (Second-surface gate fence) and `h-mad/tests/test_h_mad_collect_report_docs.py`
**Test file**: `h-mad/tests/test_h_mad_collect_report_docs.py` (gains six tests) and `h-mad/tests/test_h_mad_doc_block_exec.py` (gains two)
**Mutation spec**: `h-mad/tests/mutation-specs/doc_block_exec_wire.json` (new)
**Task shape**: `wiring`
**WIRE 1**: `h-mad/tests/test_h_mad_collect_report_docs.py:_gate_block` → `dbe.extract` AND `dbe.select`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_resolves_through_doc_block_exec`
**WIRE 2**: `h-mad/tests/test_h_mad_collect_report_docs.py:_run_recipe` → `dbe.substitute` AND `dbe.run_block`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_collect_report_docs.py::test_recipe_runs_through_run_block`

**Description**: Change the Second-surface gate fence opener in `h-mad/SKILL.md` from ` ```bash `
to ` ```bash hmad:exec ` (the block containing `h_mad_audit_gate.py` under §"Second surface — the
codex leg" — the heading is at `h-mad/SKILL.md:1804`; the section holds four ```bash fences, opening at `:1809`, `:1822`, `:1832` and `:1845`, and the gating one — the only block containing `h_mad_audit_gate.py` (its gate line is `:1850`) — opens at `:1845`; the `exec codex` block stays untagged). In the consumer, add
`import h_mad_doc_block_exec as dbe` (module-qualified; never `from h_mad_doc_block_exec import`) after the existing
`sys.path.insert(0, str(SCRIPT_DIR))` at `:22`; replace the `:270` `re.findall` inside
`_gate_bash_block` with `_gate_block() -> dbe.Block` = `dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))` (the full line form, level-pinned — `extract`'s form),
reduce `_gate_bash_block() -> str` to `_gate_block().text` so its two text-pin callers (`:281`,
`:368`) keep their string. **Hoist** the `run_recipe` closure — today nested at `:309` inside
`test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`, returning
`subprocess.CompletedProcess[str]` from an inline `subprocess.run(["bash", "-c", preamble + script])`
and rewriting the installed gate path with `str.replace` at `:312` — to a module-level
`_run_recipe(*, phase: str, cycle: int, report: Path, root: Path) -> dbe.RunResult`. Its body:
`collector = SCRIPT_DIR / "h_mad_collect_report.py"` and `gate = SCRIPT_DIR / "h_mad_audit_gate.py"`
(the two locals the closure captured from the test, now derived from the module-level
`SCRIPT_DIR`); `block = _gate_block()`;
`subbed, _ = dbe.substitute(block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(gate))})`
(the checkout-path rewrite, now through the helper); the existing `preamble` f-string unchanged
(a `COLLECT_OUT=$(` command substitution running the real collector with `--surface codex`, the phase, cycle, report and project root, every path through `shlex.quote`; shown verbatim in the code structure); `return dbe.run_block(subbed, preamble=preamble, timeout=60.0)`.
The existing test's two callers (`:340`, `:346`) keep working unchanged: they read only
`.stdout` and `.stderr` (grep over `:294–:362` finds no `.returncode`, `.args` or `.check` read),
and `dbe.RunResult` carries both as `str`. The tagged fence defaults to `shell=strict`; the
recipe survives `-euo pipefail` because `h_mad_collect_report.py` returns 0 on `MISSING`
(`scripts/h_mad_collect_report.py:102–111`) and the gate block's own branch is `if ! printf '%s\n' "$COLLECT_OUT" | grep -q '^COLLECT: OK '`.
The `:412` text scan is untouched. Write `doc_block_exec_wire.json` (`command` =
`["python3.11", "-m", "pytest", "tests/test_h_mad_collect_report_docs.py", "-q"]`,
`target_command` = `["python3.11", "-m", "pytest", "-q"]`, `root` = `../..`) with the eight rows below
(design v1.53 §Test Plan wire table). The two pins each spy **both** callees of their wire, so a
caller that keeps one callee and re-implements the other locally is a killed mutant, not a pass.

**Code structure**:
```python
# h-mad/tests/test_h_mad_collect_report_docs.py  (delta)
import h_mad_doc_block_exec as dbe  # noqa: E402  (after the existing sys.path.insert)

def _gate_block() -> dbe.Block:
    return dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))

def _gate_bash_block() -> str:
    return _gate_block().text

def _run_recipe(*, phase: str, cycle: int, report: Path, root: Path) -> dbe.RunResult:
    collector = SCRIPT_DIR / "h_mad_collect_report.py"
    gate = SCRIPT_DIR / "h_mad_audit_gate.py"
    block = _gate_block()
    # the doc addresses the installed skill; point the snippet at this tree
    subbed, _ = dbe.substitute(
        block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(gate))}
    )
    q = shlex.quote
    preamble = (
        f'COLLECT_OUT=$({q(sys.executable)} {q(str(collector))} --surface codex '
        f'--feature f --phase {phase} --cycle {cycle} '
        f'--report {q(str(report))} --project-root {q(str(root))})\n'
    )
    return dbe.run_block(subbed, preamble=preamble, timeout=60.0)

# test_documented_gate_recipe_halts_instead_of_gating_an_empty_path loses its nested
# `run_recipe` and calls `_run_recipe` with the same keyword arguments at the two former call sites; its assertions
# on `.stdout`/`.stderr` are unchanged.
```

**Acceptance Criteria**:
- [ ] AC-6.1 `test_exactly_one_tagged_fence_in_the_tree` (in `test_h_mad_doc_block_exec.py`): opening fences carrying `hmad:exec` across `h-mad/` and `handoff/` excluding any `archive/` path, counted with the module's own `_fence_events`, equal exactly 1.
- [ ] AC-6.2 `test_exec_block_scan_performs_no_execution` (a spy on `dbe.run_block` records no call while the `:412` assertions run) and `test_only_the_exec_scan_hand_rolls_extraction` (exactly one `re.findall(r"```bash` in the file's source, and it is not inside `_gate_block`/`_gate_bash_block`/`_run_recipe`).
- [ ] AC-6.3 the four existing behaviours — `COLLECT: OK` guard before gating, delivered-report `GATE: PASS`, undelivered `report_not_collected` halt without reaching the gate, no shell-killing bare `exit` — still pass, driven through the preamble boundary.
- [ ] AC-6.4 `test_suite_floor_holds` (in `test_h_mad_doc_block_exec.py`): `subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=REPO_ROOT, env={**os.environ, "DOCBLOCK_FLOOR_INNER": "1"})` — **from the repository root**, the cwd the baseline was measured in (`python3.11 -m pytest --collect-only -q -p no:cacheprovider | tail -1` → `2747 tests collected`, re-measured 2026-09-03; the same command from `h-mad/` reports 2485, a different rootdir and a different number) — with `DOCBLOCK_FLOOR_INNER=1` making the inner instance of this test skip; asserts the collected count ≥ `2747` + the collected count of `h-mad/tests/test_h_mad_doc_block_exec.py` alone (a second `--collect-only` from the same cwd) + 7, and that each of the seven named node IDs is present: the six consumer tests in `h-mad/tests/test_h_mad_collect_report_docs.py` (`test_gate_block_resolves_through_doc_block_exec`, `test_recipe_runs_through_run_block`, `test_gate_block_refuses_an_untagged_recipe`, `test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`, `test_only_the_exec_scan_hand_rolls_extraction`) plus `h-mad/tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`. Seven is exact: those are the only node IDs this feature adds to pre-existing files — every other new test, including the docsections-side ones, lives in the new module and is counted by its own collect (plan §Measurements).
- [ ] AC-6.5 WIRE-PIN 1 (`test_gate_block_resolves_through_doc_block_exec`): `monkeypatch.setattr(dbe, "extract", spy_extract)` and `monkeypatch.setattr(dbe, "select", spy_select)`, each a recording pass-through to the real function (bound before patching) — calling `_gate_block()` must record exactly one `extract` call with `(SKILL_MD, "## Second surface — the codex leg")` and exactly one `select` call whose first argument **is** the list `extract` returned (identity, `is`) and whose `index` is `None`; the returned block is the one `select` returned. WIRE-PIN 2 (`test_recipe_runs_through_run_block`): `monkeypatch.setattr(dbe, "substitute", spy_substitute)` (a recording pass-through to the real `substitute`) and `monkeypatch.setattr(dbe, "run_block", spy_run)` where `spy_run` records `(block, kwargs)` and returns `dbe.RunResult(rc=0, stdout="", stderr="", shell="strict")` — calling `_run_recipe(phase="plan", cycle=3, report=tmp_path / "r.md", root=tmp_path)` must record exactly one `substitute` call with the gate block (`text` equal to `_gate_bash_block()`) and the one-key map `{"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(SCRIPT_DIR / "h_mad_audit_gate.py"))}`, and exactly one `run_block` call whose block **is** the block `substitute` returned, whose `preamble` contains `COLLECT_OUT=$(`, and whose `timeout == 60.0`. `test_consumer_calls_the_helper_module_qualified`: the consumer's source has no `from h_mad_doc_block_exec import`.
- [ ] AC-6.6 `test_gate_block_refuses_an_untagged_recipe`: with `dbe.extract` monkeypatched to return `[]`, `_gate_block()` raises `dbe.BlockNotFound` (no legacy fallback).
- [ ] `doc_block_exec_wire.json` reports `ALL_CAUGHT` over eight rows. **The four revert rows carry
  type-correct replacement bodies** (impl-plan audit v13): each mutant's only failure is the named
  WIRE-PIN's call record — never a `NameError`, `AttributeError` or `TypeError` — and each leaves
  the three recipe regression tests green (`test_gate_block_guards_on_the_collect_token_before_gating`,
  `test_gate_block_does_not_exit_the_operators_shell`,
  `test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`). Every `find` below is the
  code-structure text verbatim, indentation included, and matches the landed source exactly once
  (the harness applies one `str.replace` pair per row). `dbe.Block` has **four** fields with no
  defaults (`text`, `shell`, `lineno`, `info`) and `dbe.RunResult` four (`rc`, `stdout`, `stderr`,
  `shell`), so every constructed value names all four.
  - `wire-revert-extract` — `_gate_block` resolves its block with a local, tag-tolerant regex
    instead of `dbe.extract`/`dbe.select`, the callee untouched. `find` is the one line
    `    return dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))`; `replace` is
    ```python
        _bodies = re.findall(r"```bash[^\n]*\n(.*?)```", _second_surface(), re.S)
        _gating = [b for b in _bodies if "h_mad_audit_gate.py" in b]
        return dbe.Block(text=_gating[0], shell="strict", lineno=0, info="hmad:exec")
    ```
    The consumer already imports `re` at its `:10` and defines `_second_surface()` at its `:49`, so
    the replacement carries no import. The regex is the pre-migration one made tag-tolerant with
    `[^\n]*`, because the literal pre-migration `re.findall(r"```bash\n(.*?)```")` would simply fail
    on the tagged fence and the wire, not the regex, is what this mutant must discriminate; the
    `"h_mad_audit_gate.py" in b` filter is the pre-migration one too and is **required** — the
    section holds four ```bash fences and a bare `[0]` would return the wrong body and break
    `test_gate_block_guards_on_the_collect_token_before_gating` on its
    `block.index("h_mad_audit_gate.py")`. Returning
    a `dbe.Block` is what keeps `_gate_bash_block() -> _gate_block().text` a `str` for its two text
    pins and keeps the first argument of `_run_recipe`'s `dbe.substitute` call a `Block`. Killed by WIRE-PIN 1's
    empty `extract` record. **Two other tests go red under it by construction**, and both stay
    regression tests rather than the row's `test` key: `test_only_the_exec_scan_hand_rolls_extraction`
    (a second `re.findall(r"```bash` now exists — hand-rolled extraction is exactly what that guard
    forbids) and `test_gate_block_refuses_an_untagged_recipe` (a call site that no longer consults
    `dbe.extract` cannot honour a patched `dbe.extract` returning `[]`). No revert of this wire can
    avoid either, since both assert the absence of the thing the revert restores.
  - `wire-revert-select` — `_gate_block` keeps `dbe.extract` but applies the ordinal policy locally,
    the callee untouched. `find` is the same one line; `replace` is
    ```python
        _blocks = dbe.extract(SKILL_MD, "## Second surface — the codex leg")
        if not _blocks:
            raise dbe.BlockNotFound()
        if len(_blocks) > 1:
            raise dbe.AmbiguousBlock(len(_blocks))
        return _blocks[0]
    ```
    `BlockNotFound` takes no constructor arguments (Task 1 defines it as a bare `DocBlockError`
    subclass) and `AmbiguousBlock(n: int)` takes the count, so both raises are well-formed; mirroring
    `select`'s no-index policy is what keeps `test_gate_block_refuses_an_untagged_recipe` green
    under this row. Killed by WIRE-PIN 1's empty `select` record, and by nothing else.
  - `wire-revert-run` — `_run_recipe` runs `bash` inline instead of calling `dbe.run_block`, the
    callee untouched. `find` is the one line
    `    return dbe.run_block(subbed, preamble=preamble, timeout=60.0)`; `replace` is
    ```python
        import subprocess
        p = subprocess.run(
            ["bash", "-c", preamble + subbed.text],
            capture_output=True, text=True, timeout=60.0,
        )
        return dbe.RunResult(rc=p.returncode, stdout=p.stdout, stderr=p.stderr, shell=subbed.shell)
    ```
    The `import subprocess` is function-local because the hoisted `_run_recipe` has no module-level
    one — the current file imports `subprocess` only inside the old test at `:304`, and that body is
    replaced by `_run_recipe` calls at GREEN. The composed script is `subbed.text`, not a bare
    `script` name that does not exist in the hoisted function, and the return value is a
    `dbe.RunResult` with all four fields, so the two `.stdout`/`.stderr` reads at `:340` and `:346`
    keep working and the recipe regression stays green; the explicit `timeout=60.0` keeps the
    mutant bounded now that WIRE-PIN 2's `spy_run` no longer short-circuits the run. Killed by
    WIRE-PIN 2's empty `run_block` record.
  - `wire-revert-substitute` — `_run_recipe` rewrites the checkout path with `str.replace` instead
    of `dbe.substitute`, the callee untouched. `find` is the three lines
    ```python
        subbed, _ = dbe.substitute(
            block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(gate))}
        )
    ```
    `replace` is
    ```python
        subbed = dbe.Block(
            text=block.text.replace(
                "~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py", shlex.quote(str(gate))
            ),
            shell=block.shell,
            lineno=block.lineno,
            info=block.info,
        )
    ```
    Building a `dbe.Block` rather than assigning the replaced `str` is what keeps the following
    `dbe.run_block(subbed, preamble=preamble, timeout=60.0)` type-correct; the other three fields are carried from `block`, so the
    executed shell mode is unchanged and the recipe regression stays green. Killed by WIRE-PIN 2's
    empty `substitute` record.
  The remaining four rows keep their v1.13 mechanisms; the two that spelled their body as an
  ellipsis are made concrete here for the same reason the four reverts were.
  - `wire-unconditional` — the call site grows a fallback, so an untagged gate block is still
    resolved; the only way a call site can become tag-blind, since no helper API accepts untagged
    fences. `find` is the one line
    `    return dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))`; `replace` is
    ```python
        _blocks = dbe.extract(SKILL_MD, "## Second surface — the codex leg")
        if _blocks:
            return dbe.select(_blocks)
        _bodies = re.findall(r"```bash[^\n]*\n(.*?)```", _second_surface(), re.S)
        _gating = [b for b in _bodies if "h_mad_audit_gate.py" in b]
        return dbe.Block(text=_gating[0], shell="strict", lineno=0, info="hmad:exec")
    ```
    Killed by `test_gate_block_refuses_an_untagged_recipe`: with `dbe.extract` patched to return
    `[]` the fallback resolves the block instead of raising `dbe.BlockNotFound`. Both WIRE-PINs stay
    green, because on the real tree `extract` returns the tagged block and `select` is still called.
    `test_only_the_exec_scan_hand_rolls_extraction` goes red with it, by construction — the fallback
    is a second `re.findall(r"```bash` — and stays a regression test, not this row's `test` key.
  - `hand-rolled-extraction-widened` — a second hand-rolled extraction appears on the executing
    path. `find` is the two lines of the landed `_gate_bash_block`
    (`def _gate_bash_block() -> str:` and `    return _gate_block().text`) — the landed function
    carries **no docstring**, unlike today's `:267` version, which is what makes that two-line
    anchor match exactly once; `replace` is
    ```python
    def _gate_bash_block() -> str:
        try:
            return _gate_block().text
        except dbe.DocBlockError:
            _bodies = re.findall(r"```bash[^\n]*\n(.*?)```", _second_surface(), re.S)
            return [b for b in _bodies if "h_mad_audit_gate.py" in b][0]
    ```
    Killed by `test_only_the_exec_scan_hand_rolls_extraction` — two `re.findall(r"```bash` now
    remain in the file rather than the one `:412` scan. Both WIRE-PINs stay green, because the
    `try` arm succeeds on the real tree.
  - `exec-scan-executes` — the `:412` text scan is made to run its block through `dbe.run_block`;
    killed by `test_exec_block_scan_performs_no_execution`, which asserts `:412` calls neither
    `run_block` nor `subprocess`.
  - `consumer-from-import` — the consumer's `import h_mad_doc_block_exec as dbe` becomes
    `from h_mad_doc_block_exec import extract, select, run_block` with bare calls; killed by
    `test_consumer_calls_the_helper_module_qualified`, since the source must carry no
    `from h_mad_doc_block_exec import` for the spies to stay observable.

  All eight mechanisms are the plan's FR-6 table's, and under each of the four reverts
  `test_h_mad_doc_block_exec.py` stays green. The eight rows bind to the same six named tests as
  before (both new rows re-use the two existing pins); no new test name is introduced, so the
  seven-node floor tuple in AC-6.4 is unchanged.

**Dependencies on other tasks**: Tasks 1–4.

**Expected RED split** (in prose): the RED commit adds `import h_mad_doc_block_exec as dbe` to the
consumer (the six new tests need the alias; the import alone wires nothing). Both WIRE-PINs then
fail with `NameError` — `_gate_block` and `_run_recipe` are new module-level names that do not
exist until GREEN; the callee `dbe.run_block`/`dbe.extract` exists, so this is never an import
error. `test_gate_block_refuses_an_untagged_recipe` fails the same way; `test_consumer_calls_the_helper_module_qualified`
passes at RED only if the alias import was written module-qualified (it is a regression guard on
the spelling); `test_only_the_exec_scan_hand_rolls_extraction` fails (two `re.findall(r"```bash`
remain, `:270` and `:412`); `test_exactly_one_tagged_fence_in_the_tree` fails (zero tagged fences);
`test_exec_block_scan_performs_no_execution` and `test_suite_floor_holds` are **regression guards**
expected to pass at RED (the scan never executed, and the floor counts collected tests, which RED
already adds); the four AC-6.3 behaviours are regression guards too. The call-record assertion
of each WIRE-PIN is the failure mode of the 5e wire-scoped revert, not of RED. Four revert
directions, applied one at a time with helper and tests intact, each with the replacement body
spelled out in the eight-row bullet above and each type-correct at the consumer's boundary:
(1) `wire-revert-extract` — restore the tag-tolerant `re.findall` plus the `h_mad_audit_gate.py`
filter in `_gate_block`, returning the gating body wrapped as
`dbe.Block(text=_gating[0], shell="strict", lineno=0, info="hmad:exec")`
so the consumer still receives a `Block` (WIRE-PIN 1 fails on its `extract` record; the source-shape
guard and the untagged-refusal test go red with it, by construction, and stay regression tests);
(2) `wire-revert-select` — keep `dbe.extract` in `_gate_block` but apply the ordinal policy locally,
raising `dbe.BlockNotFound()` on none and `dbe.AmbiguousBlock(len(_blocks))` on more than one before
taking `_blocks[0]` (WIRE-PIN 1 fails on its `select` record, and nothing else does); (3)
`wire-revert-run` — restore the inline
`subprocess.run(["bash", "-c", preamble + subbed.text], capture_output=True, text=True, timeout=60.0)`
in `_run_recipe` under a function-local `import subprocess`, returning
`dbe.RunResult(rc=p.returncode, stdout=p.stdout, stderr=p.stderr, shell=subbed.shell)` (WIRE-PIN 2 fails on its `run_block`
record); (4) `wire-revert-substitute` — restore `str.replace` in `_run_recipe`, wrapped back into a
`dbe.Block` carrying `block`'s `shell`, `lineno` and `info` (WIRE-PIN 2 fails on its `substitute`
record). Under every one of the four, `test_h_mad_doc_block_exec.py` stays green and the three
recipe regression tests in the consumer stay green;
then the opposite direction (`wire-unconditional`) must fail `test_gate_block_refuses_an_untagged_recipe`.

---

## Verification (Phase 5f)

```bash
cd h-mad
python3.11 -m pytest tests/test_h_mad_doc_block_exec.py -q
python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec.json        # MUTATION: ALL_CAUGHT mutations=69
python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec_wire.json   # MUTATION: ALL_CAUGHT mutations=8
python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/docsections.json           # MUTATION: ALL_CAUGHT mutations=8
python3.11 -m pytest -q -p no:cacheprovider > /tmp/doc_block_exec_suite.log; RC=$?
tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"                                  # gate on both
```

## Version History
- v1.0: Initial implementation plan draft from design v1.50 / plan v1.52 / spec v1.38.
- v1.1: Impl-plan audit v1 (codex must 5 should 1; agy must 2 should 1): docsections delegation merged into Task 1 as a wiring task with a sys.modules-fake WIRE-PIN scaffold; run_recipe hoisted to _run_recipe with dbe.substitute and timeout=60.0; section_from signature; __all__ exports the exceptions; docsections.json gains a syspath mutation (6 rows); counts corrected.
- v1.2: Impl-plan audit v2 (codex must 4; agy clean): transport split — seam-injected verdicts through main(argv) in-process, real-input verdicts through the subprocess, two exit-propagation tests; VERDICT_TABLE at emitted-head granularity (21 heads) plus _VERDICT_FOR by class; fence-aware heading match with its test and mutation (61 rows, design v1.51); suite floor measured from the repository root, the three collect-alone/unbalanced tests moved to the new module so the seven-node tuple stands.
- v1.3: Impl-plan audit v3 (codex must 1 should 1; agy clean): the two consumer pins also spy dbe.select and dbe.substitute, with wire-revert-select and wire-revert-substitute (eight wire mutations, design v1.53); the full exception hierarchy lands in Task 1 so __all__ is complete at its GREEN.
- v1.4: Impl-plan audit v4 (codex must 2 should 1; agy must 1) + design audit v49 (codex must 1, about Task 4): RunResult lands in Task 3 per the design; real_rmtree bound before every rmtree injection; the single-source predicate names marker-run recognition and _FenceEvent gains candidate; argparse imported; _validate_timeout runs before reservation in main and first in run_block, with the artifact-absence assertion in the bad-timeout CLI test.
- v1.5: Impl-plan audit v5 (codex must 1 should 1; agy clean) + design audit v50 (codex must 1, about Task 3): the escapee and in-group fixtures reach esc.py and the pid file through the substitution map (ESC_PATH/PID_PATH), never the child's fresh cwd; the delegation-revert mutant is stated to trip the docsections source guard; the gate-fence locator re-measured.
- v1.6: Impl-plan audit v6 (codex should 2; agy clean): provenance header at design v1.56 / plan v1.57; the ATX heading grammar stated and recognised once in _fence_events as a heading event, with test_heading_lookalikes_are_not_headings and heading-lookalike-accepted (62 rows).
- v1.7: Impl-plan audit v7 (codex must 1 should 1; agy clean) + design audit v53: find_heading is public and titled_section delegates the section start (WIRE-PIN records both calls; docsections.json seventh row); scanner event model stated as the design v1.58 does; the alias refusal leaves closing to the backstop; provenance at design/plan v1.58, grammar corpus cited.
- v1.8: Impl-plan audit v8 (codex must 2 should 1; agy clean): boundary predicate >= start with test_adjacent_heading_bounds_the_section and adjacent-heading-skipped (63 rows); the delegation-revert shim restores both local functions in one replacement; one canonical test key per row; heading differential cited; provenance at design/plan v1.60.
- v1.9: Impl-plan audit v9 (codex must 2 should 1; agy must 1 should 1) + design v1.61: find_heading's two input forms with heading-level-pin-ignored; _FenceEvent start/end offsets; complete variable-field list; stream: detail on stream_close_failed; mktemp/allow-abbrev/stream-write mutations (67 rows); wire-revert-run imports subprocess; the drain records, never raises.
- v1.10: Design audit v58 back-propagation (codex must 1): docsections-delegation-reverted is connection-only — find = the shared import line, replace = a private spec_from_file_location instance of the callee (measured on a scratch pair: recorders [] under the mutant, behaviour unchanged) — with every other test green, the source guard included; the old local-restore shim becomes the eighth row docsections-local-bounder-restored bound to the source guard (docsections.json 8 rows); the docsections delta drops the unused re import.
- v1.11: Impl-plan audit v10 (codex must 2 nit 1; agy clean): docsections-heading-lookup-reverted's one-line replace carries its own `import re;` (the delta dropped the import, so the restored regex would have raised NameError — a fix-introduced defect); 5f expects mutations=8 for docsections.json; version history back in ascending order.
- v1.12: Impl-plan audit v11 (codex must 1; agy must 1) + design v1.64: docsections-delegation-reverted registers its private instance as sys.modules['_h_mad_doc_block_exec_private'] before exec_module (a frozen dataclass under from __future__ annotations fails to load unregistered — reproduced on 3.11.8); RunResult built with keyword arguments; AC-1.7 gains test_bare_form_duplicate_headings_refuse.
- v1.13: Impl-plan audit v12 (codex clean; agy must 2, 44 tool calls): Task 5's wire-row bullet carries the exact tag-tolerant regex for wire-revert-extract and the mechanisms of wire-unconditional, exec-scan-executes, consumer-from-import and hand-rolled-extraction-widened inline, as the plan's FR-6 table states them.
- v1.14: Impl-plan audit v13 (codex must 1; agy clean) + design audit v62 back-propagation (design v1.65): the four Task 5 wire-revert rows carry type-correct replacement bodies with their exact find/replace text — a four-field dbe.Block from the tag-tolerant regex, a local BlockNotFound/AmbiguousBlock ordinal policy, an inline subprocess.run over subbed.text returning a four-field dbe.RunResult under a function-local import, and a str.replace wrapped back into a Block — so each mutant fails only on its WIRE-PIN's call record and the recipe regressions stay green; Task 3 gains the stage=collect mapping for the helper's own communicate/drain/close/wait with its three precedence rules and explicit __context__ assignment, the tests test_communicate_oserror_is_launch_failed_collect and test_drain_wait_oserror_is_launch_failed_collect (instance-level Popen wrapper, escapee fixture for the wait leg) and the rows collect-oserror-unmapped / drain-oserror-unmapped (Task 3 21 rows; 22 + 5 + 21 + 21 = 69, 67 of the helper's source); VERDICT_TABLE gains LAUNCH_FAILED stage=collect (22 heads, 16 subprocess + 6 in-process producers) and SKILL.md a per-stage registry row.
