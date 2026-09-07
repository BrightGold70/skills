## Summary

The plan addresses every functional requirement at plan granularity, as the reconciliation table shows.  However, its FR-6 strategy cannot satisfy its own tag-only selection and exactly-one-tag constraints for both current extraction sites.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- FR-6’s two-call-site migration is internally impossible as written — the extractor at `test_h_mad_collect_report_docs.py:412` selects the `exec codex` fence, while AC-6.1 and the plan tag only the later Second-surface gate fence and require exactly one tag.  The helper is specified to return only `hmad:exec` blocks (FR-1), so it cannot resolve that untagged `exec codex` block; tagging it would violate the one-tag scope, and broadening the helper would violate the opt-in boundary.  The plan’s claim that both extractors break when the gate fence is tagged is also false: this extractor still finds the untagged `exec codex` block. Reconcile the spec and plan before implementation—e.g. retain/rework this non-executing inspection without the executor and narrow AC-6.2, or deliberately change the tagging/security contract.

## Should-fix
- Add `h-mad/tests/docsections.py` to the Deliverables table — the plan explicitly expands scope to replace its bounder, but the authoritative deliverables inventory omits that changed file, making the planned change easy to skip in task decomposition.

## Nit
None
