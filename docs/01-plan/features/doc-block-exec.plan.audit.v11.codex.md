## Summary

All six functional requirements are covered by the plan as written; the only reconciliation issue is implementation precision, not a silent narrowing of the source spec. The plan nevertheless leaves the proposed single-source import path unbuildable from the current test import topology and records a load-bearing process-group claim without the required cited experiment.

| FR | Classification | Plan coverage |
|---|---|---|
| FR-1 | implemented-as-written | Explicit tag/addressing, scanner ownership, and `docsections.py` delegation are stated. |
| FR-2 | implemented-as-written | Literal substitution, missing-key refusal, counts, and overlap refusal are planned. |
| FR-3 | implemented-as-written | `tempfile.mkdtemp()`, declared shell modes, separate stream artifacts, and preamble are stated. |
| FR-4 | implemented-as-written | One `DOCBLOCK:` verdict line, result/non-measurement distinction, and registry pin are stated. |
| FR-5 | implemented-as-written | `communicate(timeout=...)`, process-group cleanup, and no external time-bounder are stated. |
| FR-6 | implemented-as-written | The tagged gate block, executing-path migration, retained non-executing scan, and two-way wire mutations are stated. |

## Must-fix

- `h-mad/tests/docsections.py` is required to import the authoritative helper in `h-mad/scripts/h_mad_doc_block_exec.py`, but the plan gives no import/loading mechanism for that cross-directory edge — today `test_docsections.py` imports `docsections` as a top-level module and does not add `h-mad/scripts` to `sys.path`; a direct import therefore fails during collection, leaving AC-1.8's single-source contract unimplemented. Specify the exact self-contained import arrangement (and its collection test) rather than leaving the crucial edge implicit.
- The timeout design relies on the claim that the stated `start_new_session=True`/`killpg(proc.pid, ...)` sequence kills all in-group descendants while a `setsid()` child escapes, but it only says “measured” and supplies neither command nor observed output — this violates the Assumption verification invariant for a load-bearing isolation boundary. Add the controlled in-group and escaped-group probes, with their observed outcomes, before treating AC-5.2's scope as established.

## Should-fix

- Add a task-level API and caller-type map: exact `extract`, `select`, and `run_block` signatures/result type, plus how `test_h_mad_collect_report_docs.py` replaces its current `run_recipe(...) -> subprocess.CompletedProcess[str]` contract — the current plan says only “importable API” and “distinct fields,” which leaves return-type and assertion migration vague despite making that call site a deliverable.
- Name the concrete caller wire tests and the mutations each kills in `doc_block_exec_wire.json` — “a named test” and `WIRE`/`WIRE-PIN` describe the intent, but not an implementation-ready, independently auditable mapping for AC-6.5 and AC-6.6.

## Nit

None
