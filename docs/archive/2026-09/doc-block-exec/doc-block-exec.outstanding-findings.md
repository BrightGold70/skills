# doc-block-exec — outstanding audit findings at Phase 4 handoff

Phase 4 is **NOT gated**. Both surfaces still return must-fixes. These six are verified
present in the documents and are the next session's first work; each is quoted verbatim
from the audit report named, so nothing needs re-deriving.

## Plan — cycle 11 (`GATE: FAIL must=2 should=2`, codex; agy PASS 0/0)

## Must-fix

- `h-mad/tests/docsections.py` is required to import the authoritative helper in `h-mad/scripts/h_mad_doc_block_exec.py`, but the plan gives no import/loading mechanism for that cross-directory edge — today `test_docsections.py` imports `docsections` as a top-level module and does not add `h-mad/scripts` to `sys.path`; a direct import therefore fails during collection, leaving AC-1.8's single-source contract unimplemented. Specify the exact self-contained import arrangement (and its collection test) rather than leaving the crucial edge implicit.
- The timeout design relies on the claim that the stated `start_new_session=True`/`killpg(proc.pid, ...)` sequence kills all in-group descendants while a `setsid()` child escapes, but it only says “measured” and supplies neither command nor observed output — this violates the Assumption verification invariant for a load-bearing isolation boundary. Add the controlled in-group and escaped-group probes, with their observed outcomes, before treating AC-5.2's scope as established.

## Should-fix

- Add a task-level API and caller-type map: exact `extract`, `select`, and `run_block` signatures/result type, plus how `test_h_mad_collect_report_docs.py` replaces its current `run_recipe(...) -> subprocess.CompletedProcess[str]` contract — the current plan says only “importable API” and “distinct fields,” which leaves return-type and assertion migration vague despite making that call site a deliverable.
- Name the concrete caller wire tests and the mutations each kills in `doc_block_exec_wire.json` — “a named test” and `WIRE`/`WIRE-PIN` describe the intent, but not an implementation-ready, independently auditable mapping for AC-6.5 and AC-6.6.

## Nit

## Design — cycle 5 (`GATE: FAIL must=4 should=1`, codex; agy must=9)

## Must-fix
- Zero and negative ordinal handling is unspecified — the design calls `index` 1-based but only defines not-found for an index past the end. A conventional `blocks[index - 1]` implementation turns `--index 0` into the final tagged block and negative values into other unintended blocks, violating the unambiguous address/security boundary. Define validation and its mapped refusal, then test 0 and a negative ordinal.
- Cleanup is deliberately unverified — `shutil.rmtree(cwd, ignore_errors=True)` suppresses deletion failures and performs no read-back. This breaches the base mutation-verification invariant and can report a completed run while retaining its supposedly disposable cwd; remove the silent suppression or handle it, re-check that the directory is absent, and surface a genuine cleanup operational error.
- The timeout path has unhandled races — `os.killpg(proc.pid, SIGKILL)` can raise `ProcessLookupError` if the group exits between `TimeoutExpired` and the kill, and the stated second bounded `communicate` has no action if it itself times out. Either case escapes the declared `BlockTimeout` to a traceback instead of the required `DOCBLOCK: TIMEOUT`, despite FR-5 requiring every run be bounded; specify the races, final pipe/cleanup behavior, and tests that exercise them.
- The Test Plan omits planned enforcement for AC-1.7 and AC-3.11 through AC-3.13 — its scanner row names AC-1.1–1.6 and AC-1.8, while its execution row stops at AC-3.9. There is no stated test for duplicate-heading refusal, the preamble failure/unreadable-file contract, or `mkdtemp` mode plus no-`mktemp` invocation, leaving the specs promise that every AC pass an automated test unenforced.

## Should-fix
- The authoritative-bounder import is not executable as designed — `h-mad/tests/docsections.py` currently imports from the tests directory, while the new authoritative module is under `h-mad/scripts/`; a direct import will fail when `test_docsections.py` is collected alone because it does not add `scripts` to `sys.path`. State the exact intra-skill import/loading arrangement and add an isolated collection/import test, rather than relying on another test modules path side effect.

## Nit

## agy design cycle 5 — must=9, and read the size caveat first

`AUDITCYCLE: FAIL must=9 should=0 ... size_status=unverified`. The assembled design prompt
has outgrown the confirmed-answered frontier, so this pass's volume is not comparable with
earlier ones — triage it against source before acting, and consider inlining only the spec's
Functional Requirements section (SKILL.md §Audit prompt assembly step 5.5) to bring it back
under. Reports:

### doc-block-exec.design.audit.v5.p1.md

## Must-fix
- Axis A / Internal Contradiction (extract signature) — The `Scanning` section correctly states that `extract` "raises AmbiguousHeading(n) rather than taking the first". However, the `API / Interface Changes` section provides a docstring for `extract` that explicitly claims it "Raises DocUnreadable or BadInfoString only — never on candidate count", contradicting the earlier section and precluding the `AmbiguousHeading` exception.
- Axis A / Missing Error Mapping — The `API` and `Verdict lines` sections specify that an unreadable preamble file refuses with `DOCBLOCK: UNREADABLE reason=preamble_unreadable`. However, the `Error Handling Strategy` mapping table omits any exception to map to this verdict. Since `main` dispatches based on exception type, this missing mapping will cause a preamble read failure to surface as an unhandled traceback rather than the contracted verdict token.
- Axis C / Spec Restatements and Absent Tests (AC-1.7, AC-3.11, AC-3.12, AC-3.13) — The Test Plan table stops AC enumerations at AC-3.9, entirely omitting test coverage for duplicate heading rejection (AC-1.7), preamble bounds and execution (AC-3.11/3.12), and the `mkdtemp` isolation guarantees (AC-3.13). An AC is not satisfied if its test coverage is dropped. Additionally, the design explicitly narrows the spec by:
  - Spec AC-3.12 requires "A run with a preamble reports rc/stdout/stderr for the combined invocation"; the design states the preamble is run in the same invocation but omits the explicit contract that the combined streams are captured and reported.
  - Spec AC-3.13 requires asserting that the temp dir mode is "observed from inside the running block" and that "The source contains no mktemp invocation"; the design drops these explicit test assertions entirely.

## Should-fix
None

## Nit

### doc-block-exec.design.audit.v5.p2.md

## Must-fix
- Missing Tests for Preamble and mkdtemp (AC-3.11–3.13) — The Test Plan table for `FR-3` stops at `AC-3.1-3.9`, leaving `AC-3.11` (fixture preamble), `AC-3.12` (preamble errors), and `AC-3.13` (mkdtemp constraints) completely untested. This creates a hard gap where these critical boundaries could fail silently. (Axis C `absent`).
- Missing Test for Duplicate Headings (AC-1.7) — `AC-1.7` (Duplicate headings refuse) is described in the design text but is completely absent from the Test Plan table, leaving a load-bearing refusal unverified. (Axis C `absent`).
- Contradictory `extract` API docstring — The `extract` docstring states "Raises DocUnreadable or BadInfoString only", which directly contradicts the "Scanning (`extract`)" section and Error Handling table that both require `extract` to raise `AmbiguousHeading(n)`. This creates an ambiguous contract for implementers.
- Incomplete Exception Mapping for Preamble Errors — The Verdict Lines table requires `DOCBLOCK: UNREADABLE reason=preamble_unreadable`, but the "Error Handling Strategy" table defines no corresponding exception class. This gap will cause a `KeyError` traceback in `main`'s mapping dispatcher instead of the required clean exit 2.

## Should-fix
None

## Nit

