## Summary
Reviewed the implementation plan v1.6 against the paired design v1.15 and the current helper contracts. The main feature decomposition is coherent, but one required checkpoint is not executable as written, and a few traceability details need tightening before implementation.

## Must-fix
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:169-179` requires the AC-2.9 hand replay outputs to be recorded "verbatim" as "the four lines" through `h_mad_version_history.py --text`, but `h-mad/scripts/h_mad_version_history.py:157-160` refuses any newline-bearing entry as `multiline_text` (verified by dry-run). This makes the incident-replay checkpoint impossible if implemented literally and violates the Incident replay / Assumption verification invariant because Task 4 is gated on evidence the mandated helper cannot write.

## Should-fix
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:252` says the SKILL.md `RP=/tmp/audit_...report.md` literal "matches `TRANSPORT_RE`", but the gate grammar is applied to `Path.name`; matching the full `/tmp/...` string against `^audit_[^.]+\.report\.md$` is false. Specify `is_transport_path(Path(instantiated))` or `TRANSPORT_RE.match(Path(instantiated).name)` so the docs-half test is exact.
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:165` and `:169` both use `AC-2.9`, while `:339` claims the duplicate AC label was removed. Renumber the suite replay and hand replay distinctly to keep acceptance-criterion references unambiguous.
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:337-344` has mixed Version History ordering; `h_mad_version_history.py --dry-run ... --version v1.7` refuses it as `mixed_order`. That does not block the named AC-2.9 checkpoint artifact, but it will block helper-based future revisions to this impl-plan.

## Nit
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:213` names the "line-3 verb list"; locating the `# Verbs:` header is less brittle if the wrapper header gains or loses lines.
