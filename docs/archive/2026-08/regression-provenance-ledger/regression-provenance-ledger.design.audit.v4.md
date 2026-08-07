## Summary
The design provides a robust, pure-verifier architecture that resolves the A3 defect by separating pin resolution from execution, and thoughtfully places the FR-5 AST challenge at 5f where a production diff actually exists. Axis C reconciliation shows all ACs are covered as written. However, the design violates two Axis B invariants (Assumption verification for pytest batch output parsing, and Single-source contract for sidecar parsing), introduces contradictions around `load_base`'s return type and the exact mechanism for discovering changed files, and silently drifts from the plan's strict subprocess count constraint.

## Must-fix
- **Axis B (Assumption verification) — Missing output citation for pytest batch failures:** The design assumes it can run `pytest <ids> -q` and map the failed tests back to their node ids to report the `owning_feature` (per AC-2.2). Extracting exact failing node ids from `pytest -q` stdout is notoriously fragile and heavily formatted. The design does not cite the observed output of a batch failure run to prove this extraction is possible, nor does it specify using a machine-readable flag (e.g., `--junitxml`). An assumption asserted without evidence is a violation.
- **Axis B (Single-source contract) — Independent reimplementation of sidecar parsing:** The design specifies reading the impl-plan's audit sidecar for `## Acknowledged-not-fixed` entries. The orchestrator/audit gate already parses this section to exclude blocking items. If `h_mad_wire_registry.py` implements its own parsing without calling the authoritative parser or asserting byte-equivalence, it can silently diverge, violating the single-source contract.
- **Axis A (Gaps) — Missing mechanism to discover changed production files:** The AST challenge reports a changed file claimed by NO task as `unattributed`. To do this, the script must know the full set of changed `.py` files between `BASE` and `HEAD`. The design never specifies the git command (e.g., `git diff --name-only <base> HEAD`) required to retrieve this actual list of changed files.
- **Axis A (Cross-doc / Drift) — Violation of the strict subprocess count constraint:** The plan explicitly mandated as a success criterion: "Verifier cost is at most two subprocesses regardless of registry size...". The design introduces four additional git subprocess calls (`git check-ignore`, `git ls-files`, `git rev-parse`, `git show`). While functionally necessary for trackedness and BASE comparisons, this silently violates the plan's explicit performance constraint and must be reconciled.
- **Axis A (Contradiction) — `load_base` return type conflict:** The diagram and text state `load_base(sha, path)` returns `base_records` (parsed JSON records) for the registry comparison. However, the AST challenge states it reads the BASE `.py` files "through the same `load_base()` shell". If `load_base` parses its output as JSONL, it will crash on a `.py` file; if it returns a raw string, the diagram implying it returns `base_records` is a contradiction.

## Should-fix
None

## Nit
None

### Axis C Spec Reconciliation

| AC | Classification |
|---|---|
| AC-1.1 | `implemented-as-written` |
| AC-1.2 | `implemented-as-written` |
| AC-1.3 | `implemented-as-written` |
| AC-1.4 | `implemented-as-written` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `implemented-as-written` |
| AC-2.4 | `implemented-as-written` |
| AC-2.5 | `implemented-as-written` |
| AC-3.1 | `implemented-as-written` |
| AC-3.2 | `implemented-as-written` |
| AC-3.3 | `implemented-as-written` |
| AC-3.4 | `implemented-as-written` |
| AC-4.1 | `implemented-as-written` |
| AC-4.2 | `implemented-as-written` |
| AC-4.3 | `implemented-as-written` |
| AC-4.4 | `implemented-as-written` |
| AC-5.1 | `implemented-as-written` |
| AC-5.2 | `implemented-as-written` |
| AC-5.3 | `implemented-as-written` |
| AC-5.4 | `implemented-as-written` |
| AC-6.1 | `implemented-as-written` |
| AC-6.2 | `implemented-as-written` |
| AC-6.3 | `implemented-as-written` |
