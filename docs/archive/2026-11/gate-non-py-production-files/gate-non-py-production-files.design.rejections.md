# Rejections ledger — gate-non-py-production-files design audits

One entry per rejected (or partly rejected) finding. Never passed to the gate as `--gated`.

## Cycle 1 — agy (`design.audit.v1.p2.md`), audited design v1.1 at `b9c705c3`

Four of this report's quotes occur in no document at that commit: `def _match_plans(rel: str, …) -> tuple[Path, ...]`, `# M:JL-UNLISTED`, `SimpleNamespace(listed=False, …)` and `NON-PY-GATE-PROBE-BASE`. Its version-history quotes (`| 1.7 | 2026-11-04 | …`, `| 1.4 | 2026-11-04 | …`) are also absent; both files use `- v1.N:` bullets.

- **Must 1 (rejected): listing conflates "listed" with "has `.py` tests".** Design D4 declares `_match_plans(root, target, records) -> Tuple[PlanMatch, ...]` and a `Listing` with `value`, `selected`, `error_file` and `error`. The quoted signature and return are not the design's.
- **Must 2 (rejected): `names[0]` raises `IndexError` on a directory.** The report assumes `is_doc_data(())` is `False`. Design line 110 defines it as vacuously `True`, and `# M:CX-DOCDATA` / `# M:AG-DOCDATA` skip before `_judge_listed` or the agy block runs.
- **Must 3 (partly rejected).** Kept: `_judge_listed` step 6 uses `{relative}`, which its steps never bind. Rejected: the agy half. The design gives agy its own deny form, and the quoted agy hook text does not match `h-mad/hooks/h-mad-agy-tdd-gate.py:192`.
- **Must 4 (rejected): the probe `h_mad_non_py_gate_probe.py` has no `git init`.** No such probe is in the design. The FR-9 driver's replay repo is built by `git init` (design §"FR-9 — the driver").
- **Should 1 (rejected): `CX-LIST`/`AG-LIST` use `SimpleNamespace`.** The design's mutants use `judge.Listing(...)`.
- **Kept:** Should 2 (agy `is_doc_data` import versus the `identity.is_doc_data` call), Should 3 (stale version citations), and the Nit, pending the design author's check.

## Cycle 1 — codex (`design.audit.v1.p1.md`), must 2: superseded by operator ruling

Design v1.2 and spec v1.9 applied this finding: unreadable outranks listed, with AC-8.5. The operator then ruled on 2026-11-04 that a listed code-like target is judged from the readable plan, accepting the residual that an unreadable sibling plan can hide an earlier listed hard-link name with different Task tests. Spec v1.10 and design v1.4 revert to listed-before-unreadable and remove AC-8.5. Do not re-raise without new evidence.
