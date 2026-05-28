# Design Audit v1 — h-mad-audit-surfaces-reconcile

> Reviewer: agy (Reviewer.adversarial_consistency + Analyzer.cross_doc_consistency). Cycle 1. Target: design.md v1.0. Paired: plan.md v1.3 (gate-clean).

## Summary

The design is detailed and structurally sound. It resolves all plan-level deferred decisions (D-b…D-f), enforces python-only single-sourcing for the audit gate (no platform-dependent awk), and complies with all Axis B invariants. No cross-doc drift from the paired plan. Two minor gaps remain in specifying Phase-7 / dependency deliverables and test portability.

## Must-fix

None

## Should-fix

- Missing design details for the Phase-7 sidecar and dependency-inventory note — both appear in the Deliverables table (FR-5 upstream-note sidecar; FR-6 dependency-inventory note) but the design does not specify their file paths, format, or generation logic in the Detailed Design or Components sections. Define them explicitly so they are not left to developer discretion.
- Test-suite dependency on the external bkit validator — `test_h_mad_doc_templates.py` calls the bkit validator via a node subprocess. To preserve test-suite portability and the standalone invariant, the design should mandate these template-validation tests gracefully SKIP (not fail) when the bkit validator is not installed in the test environment.

## Nit

None
