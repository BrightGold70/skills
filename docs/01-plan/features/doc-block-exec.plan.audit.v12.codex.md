## Summary

The plan addresses every functional requirement as written, but two stated implementation mechanisms are not precise enough to establish the required authoritative-bounder and caller-wire enforcement. Axis C reconciliation is otherwise complete.

| FR | Classification | Plan coverage |
|---|---|---|
| FR-1 | implemented-as-written | Tagged, heading-scoped extraction; explicit scan/select split; and `docsections.py` delegation are planned. |
| FR-2 | implemented-as-written | Literal substitution, absent-key refusal, counts, and overlap refusal are planned. |
| FR-3 | implemented-as-written | Disposable `tempfile.mkdtemp()` cwd, declared shell modes, stream artifacts, preamble, and cleanup are planned. |
| FR-4 | implemented-as-written | The one-line `DOCBLOCK:` verdict contract, exit distinction, and registry pin are planned. |
| FR-5 | implemented-as-written | `communicate(timeout=...)`, process-group handling, bounded drain, and no external time-bounder are planned. |
| FR-6 | implemented-as-written | The single tag, executing-path migration, retained non-executing scan, and two-direction wire mutations are planned. |

## Must-fix

- The AC-1.8 delegation is still a placeholder rather than an implementation-ready contract: the plan says `docsections.py` imports an “authoritative bounder” from `scripts/h_mad_doc_block_exec.py`, while its declared module surface lists only `extract`, `select`, `substitute`, and `run_block`; it names neither the bounder symbol nor its `(text, start, level) -> int` contract. This leaves the required single source unbuildable without inventing an API and prevents the two re-pointed mutations from having exact anchors; name the exported/private bounder and its exact call replacement in `titled_section` and `section_from`.
- The required FR-6 wire spies conflict with the described caller shape: `_gate_bash_block` “becomes `select(extract(SKILL_MD, ...)`” and `run_recipe` calls `run_block(...)`, which implies directly imported aliases, but the named mutations require spies on `h_mad_doc_block_exec.extract` and `.run_block`. Monkeypatching the module attributes does not observe calls through pre-bound direct aliases, so those tests can pass/fail without proving the connection — a base **Connection enforcement/Test discrimination** breach. Require either module-qualified calls (`h_mad_doc_block_exec.extract/run_block`) or spies on the consumer module’s exact aliases, and state that choice in the wire mutation/test map.

## Should-fix

- Capture and cite the pre-change full-suite collected-test baseline before implementation, including the exact command and observed count — “no lower than baseline plus added tests” is otherwise not reproducible and cannot distinguish a lost test from a passing suite.

## Nit

None
