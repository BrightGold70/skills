## Summary
The design covers the main components, and the existing precheck and document-shape checks pass. Two acceptance criteria are restated, and the proposed veto also bypasses a supported acknowledgement path.

Evidence: 16 files opened, 5 greps run.

| Acceptance criterion | Classification | Basis |
|---|---|---|
| AC-1.1 | implemented-as-written | Template table and superset test update. |
| AC-1.2 | implemented-as-written | Seven mirrored headings remain unchanged. |
| AC-1.3 | implemented-as-written | Author check and deferred self-bootstrap test. |
| AC-2.1 | restated | Default root changes from cwd to path inference. |
| AC-2.2 | implemented-as-written | Section, table and AC-cell validation. |
| AC-2.3 | implemented-as-written | Placeholder checks and mocked-none exception. |
| AC-2.4 | implemented-as-written | Closed lexical oracle checks. |
| AC-3.1 | implemented-as-written | Active/retired extraction, coverage and unknown IDs. |
| AC-3.2 | implemented-as-written | Verification kinds and artifact indicators. |
| AC-4.1 | implemented-as-written | Frozen exemptions and strict override. |
| AC-4.2 | restated | Existing directory candidates are discarded before activation. |
| AC-4.3 | implemented-as-written | PASS/EXEMPT handling and isolated-loading parity. |
| AC-4.4 | implemented-as-written | Import isolation, anchors and two-direction mutations. |
| AC-5.1 | implemented-as-written | Matching design-only auditor rubrics. |
| AC-6.1 | implemented-as-written | Archived calibration and runtime assertions. |
| AC-6.2 | implemented-as-written | Seeded defect rejection. |
| AC-6.3 | implemented-as-written | Pinned checker and connection mutations. |

🌱 graft saved ~69,066 tokens this turn, 1 call.

## Must-fix
- AC-2.1 is restated: reconcile the default project root with the spec before implementation. The spec defaults `--root` to cwd; the design infers the canonical design's ancestor and tests lookup from another cwd without `--root`. These rules can select different specs for the same invocation. Either preserve the documented default or explicitly update the source contract to authorize inference, with a test distinguishing the two.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › `optional repository root directory (defaults to current working directory).`
  quote: docs/02-design/features/hmad-test-boundaries.design.md › ``if `len(abs_design.parts) >= 4` and `abs_design.parts[-4:-1] == ("docs", "02-design", "features")`, returns `abs_design.parents[3]` ``
- AC-4.2 is restated: existing directory-valued design candidates silently bypass enforcement. The spec activates existing canonical candidates; both the gate's candidate filter and the activation helper instead require `is_file()`. With a report-only invocation whose co-located canonical `<feature>.design.md` is a directory, the proposed helper returns success without invoking the checker, allowing a clean report to pass instead of exposing the unreadable design. Route existing invalid candidates to UNREADABLE and add a positional-report regression test; address both filters.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › ``For **each** candidate `<design_path>` in the deduplicated candidate list that exists on disk``; ``1. `<design_path>` resides under `docs/02-design/features/` (or `docs/archive/`), OR``
  quote: docs/02-design/features/hmad-test-boundaries.design.md › `candidates = [p for p in _candidate_design_paths(audit_file, gated) if p.is_file()]`; ``If `not Path(design_path).is_file()`, returns `False`.``
- Preserve supported acknowledgements when introducing the auxiliary veto. Leaving report classification untouched does not preserve the override when the checker independently blocks the acknowledged defect. In an in-memory controlled comparison using the current gate and the exact proposed pre-stamp block, an acknowledged untagged boundary finding changed from `GATE: PASS must=0 should=0` to `GATE: FAIL must=0 should=0` when the auxiliary result was FAIL. Define how eligible acknowledgements apply to deterministic issues and test that path, retaining the existing refusal of explicitly build-tagged must-fixes.
  class: build
  quote: docs/02-design/features/hmad-test-boundaries.design.md › `tb_ok, tb_lines = _run_design_boundaries_checks(args.audit_file, args.gated)`; ``Complies because `## Acknowledged-not-fixed` handling in `h-mad/scripts/h_mad_audit_gate.py` is untouched``
  quote: h-mad/invariants.base.md › ``The `## Acknowledged-not-fixed` sidecar override mechanism MUST remain functional for all``; `blocking, or that ignores the sidecar, is a violation.`

## Should-fix
None

## Nit
None
