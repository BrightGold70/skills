## Summary
The design provides a robust, byte-identical codex-leg collection mechanism that prevents un-persisted reports from scoring. The implementation strategy securely couples transport refusal in the gate with identical-byte assertions, enforcing the single-source contract. I've mapped every AC to the design (39 implemented as written, 1 restated) and identified two implementation gaps where exception scoping would leak operational errors into Python tracebacks instead of the mandated contract exits.

| AC | Classification | AC | Classification | AC | Classification |
|---|---|---|---|---|---|
| AC-1.1 | implemented-as-written | AC-2.6a | implemented-as-written | AC-3.5 | implemented-as-written |
| AC-1.2 | implemented-as-written | AC-2.6b | implemented-as-written | AC-3.5a | restated |
| AC-1.3 | implemented-as-written | AC-2.7 | implemented-as-written | AC-3.6 | implemented-as-written |
| AC-1.4 | implemented-as-written | AC-2.8 | implemented-as-written | AC-3.7 | implemented-as-written |
| AC-1.5 | implemented-as-written | AC-2.9 | implemented-as-written | AC-4.1 | implemented-as-written |
| AC-1.6 | implemented-as-written | AC-2.10 | implemented-as-written | AC-4.2 | implemented-as-written |
| AC-2.1 | implemented-as-written | AC-2.11 | implemented-as-written | AC-4.3 | implemented-as-written |
| AC-2.2 | implemented-as-written | AC-2.12 | implemented-as-written | AC-5.1 | implemented-as-written |
| AC-2.3 | implemented-as-written | AC-3.1 | implemented-as-written | AC-5.2 | implemented-as-written |
| AC-2.4 | implemented-as-written | AC-3.2 | implemented-as-written | AC-5.3 | implemented-as-written |
| AC-2.5 | implemented-as-written | AC-3.3 | implemented-as-written | AC-5.4 | implemented-as-written |
| AC-2.6 | implemented-as-written | AC-3.4 | implemented-as-written | AC-6.1 - 6.5| implemented-as-written |

## Must-fix
- **Python Exception Scoping for Retry** — In D2 (CLI) step 4, the retry logic `collect(..., overwrite=True)` under `--force` is placed inside the `except CollectConflict:` block. If this forced retry raises an `OperationalError` (e.g., a readback mismatch), it escapes the sibling `except OperationalError:` block. This causes a Python traceback (exit 1) and skips the required `readback_failed` marker, violating the Audit-gate signal discipline.
- **Unhandled `OSError` in File Operations** — The design claims "OSError → OperationalError", but D1's `_copy_collected_report` and `_write_collected_report` use `unlink()` and `write_bytes()` without catching `OSError`, and D2 only catches `OperationalError`. A file operation failure (e.g., `PermissionError` on an unwritable file) will crash the script with a traceback (exit 1) instead of triggering the required exit 2, violating the Audit-gate signal discipline.
- **AC-3.5a Restated (Missing 6.6 literal assertion)** — The Spec requires "The stem the wrapper stages is pinned ... and the SKILL.md 6.6 literal is asserted to match it too." The Design (Test Plan / D3) asserts the wrapper's staged `--report-file` matches `TRANSPORT_RE` but drops the assertion that the `SKILL.md` 6.6 literal also matches it. This creates a gap where the recipe could silently drift from the regex.

## Should-fix
None

## Nit
- In D3, when extracting the feature name from a transport file (`args.audit_file.name.split(".")[0]`), the gate uses the entire stem (e.g., `audit_f_plan_cycle3_codex`) instead of just `f` for the `[H-MAD]` marker. While this doesn't break the downstream consumer (which keys on `GATE: INVALID`), it makes the marker slightly misaligned with standard `<feature>` logging.
