## Summary
Operator sidecar for the design audit of phase5-gate-feature-scope. Phase 4 is not exited and this file records no approval of wording.
Two gating rounds are spent (cycle 1 unverified, cycle 2 FAIL); no third round is run. Cycle 2's findings on AC-3.5, AC-8.1, row 17 and the streaming process bound were answered in design v1.7 to v1.9, and the one on a git failure in the middle of a scan in v1.8 and v1.9, without a re-audit.
The other build findings of cycle 2 are carried as open decisions into the implementation plan (operator, 2026-11-25).

## Must-fix
None

## Should-fix
None

## Acknowledged-not-fixed
- The design’s prototype readings cannot be re-derived at this gate — the named probe directory is absent in the reviewed tree. For example, the command for the 38-case stub comparison depends on an unavailable script. Include the runnable probe text or an accessible, pinned artifact with its invocation for the readings used to choose the design. The scheduled S6 and S11 whole-hook measurements are separate.
- [prototype-readings] Acknowledged as measurement: the probe scripts are not in the tree until step S0 commits them as the parts of `discovery_probe.py`; from S0 the command is `python3.11 docs/03-analysis/probes/phase5-gate-feature-scope/discovery_probe.py disc <repository> 5` for the discovery readings, and the parts named in design §2 and §12 for the rest. Until then those readings constrain no decision; the rows marked as not re-runnable from this repository stay unverified.

## Nit
None
