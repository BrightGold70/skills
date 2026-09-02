## Summary
The design faithfully translates the spec's requirements, correctly implementing the surface-aware collector, conflict-safe fallback rungs, and the transport path refusal. All acceptance criteria are addressed exactly as written. However, two file system operations in the CLI are performed outside the `try...except` block, risking traceback leaks that violate the audit-gate signal discipline.

| Spec AC | Classification |
|---|---|
| AC-1.1 to AC-1.6 | `implemented-as-written` |
| AC-2.1 to AC-2.12 | `implemented-as-written` |
| AC-3.1 to AC-3.7 | `implemented-as-written` |
| AC-4.1 to AC-4.3 | `implemented-as-written` |
| AC-5.1 to AC-5.4 | `implemented-as-written` |
| AC-6.1 to AC-6.5 | `implemented-as-written` |

## Must-fix
- Traceback leak on `same` derivation (Axis B: Audit-gate signal discipline) — In D2 step 3, `same = Path(RP).resolve() == _collected_path(...).resolve()` is computed outside the `try ... except OperationalError:` block. Because `resolve()` accesses the filesystem, it can raise `OSError` (e.g., `PermissionError`), allowing a traceback to escape and violating the signal discipline. Move the assignment inside the `try` block or handle its `OSError`.
- Traceback leak on directory validation (Axis B: Audit-gate signal discipline) — In D2 step 1, the semantic checks include "docs dir cannot be created (`mkdir` raises)". Because this check happens before the main `try ... except OperationalError:` block in step 4, any `OSError` raised by `mkdir()` will escape as a traceback. Wrap the check in a try-except block that exits 2 with the `operational_error` marker.

## Should-fix
None

## Nit
- In D3, the gate refusal emits `[H-MAD] {feature} gate INVALID`. Because `feature = args.audit_file.name.split(".")[0]`, a transport file like `audit_f_plan_...report.md` will result in the entire dot-free stem being printed as the feature name (e.g., `[H-MAD] audit_f_plan_... gate INVALID`). This is likely fine since the file is being refused outright, but it differs from the true feature name `f`.
