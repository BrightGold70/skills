# Fixture

Verbatim `## Version History` section from `../HemaSuite/docs/01-plan/features/crf-fragment-domain-tagging.impl-plan.md`,
copied 2026-08-25. Do not tidy it -- the awkward parts are the test.

## Version History
- v1.0: Initial impl-plan (4 slices, from audited design v1.1; LOCKED rules-draft v3.3).
- v1.1: Impl-plan audit v1 fixes from `crf-fragment-domain-tagging.impl-plan.audit.v1.md` — `ctx` build includes `"disease": disease` (inclusion resolver reads it); `propagate_gate_annotations` placed in `crf_gating.py` (both modules import it — no circular import); endpoint token uses `a.get("domain")`.
- v1.2: Impl-plan audit v2 nit — helper name consistently `propagate_gate_annotations` (public, in `crf_gating.py`) across impl-plan + design; design endpoint-token uses `.get("domain")`.
