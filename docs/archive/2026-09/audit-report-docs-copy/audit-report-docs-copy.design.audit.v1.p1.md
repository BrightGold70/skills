## Summary
The design fully implements all spec requirements without narrowing, mapping each acceptance criterion to test coverage and mutation cases (Axis C table below shows full compliance). However, there is a critical logic gap in the collector implementation: the `AC-2.11` short-circuit inadvertently catches the `AC-2.8` same-file case, skipping the required marker check and removal.

| Spec Requirement | Classification |
|---|---|
| FR-1 (AC-1.1–1.6) | `implemented-as-written` |
| FR-2 (AC-2.1–2.12) | `implemented-as-written` |
| FR-3 (AC-3.1–3.7) | `implemented-as-written` |
| FR-4 (AC-4.1–4.3) | `implemented-as-written` |
| FR-5 (AC-5.1–5.4) | `implemented-as-written` |
| FR-6 (AC-6.1–6.5) | `implemented-as-written` |

## Must-fix
- Logic contradiction in `collect()` short-circuit — In D1, the AC-2.11 short-circuit (`if collected_path.is_file() and spec.report_path.is_file() and collected_path.read_bytes() == spec.report_path.read_bytes():`) evaluates to True instantly when `--report` is the derived docs path (the AC-2.8 same-file case). This bypasses `_has_complete_report` and `_copy_collected_report`, meaning the same-file case will return `OK` even if the `.done` marker is missing, and will never remove the `.done` marker, breaking FR-2 and AC-2.8. The short-circuit must explicitly exclude the same-file case (e.g. `if not same_file and ...`).

## Should-fix
None

## Nit
- Imprecise phrasing in CLI marker logic — In D2, step 6 says "if same and the marker is gone print `marker: removed <RP>.done`". Because `_copy_collected_report` raises an `OperationalError` if it fails to remove the marker, the CLI doesn't need to check if the marker is gone itself; if execution reaches step 6 and `same` is True, the marker has definitely been removed.
