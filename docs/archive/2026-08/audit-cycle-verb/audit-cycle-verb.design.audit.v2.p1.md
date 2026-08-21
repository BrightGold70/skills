## Summary
The design correctly architects the split between shell (assembly, dispatch, reaping) and Python (collection, gating, reporting) without modifying the underlying scripts. However, there are significant type consistency errors in the signature boundaries between the CLI and Python helper, and a logical flaw where successful `report-file` deliveries are never copied to the final `docs/` destination, directly contradicting the spec and the intended output.

| Spec AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-3.1 | absent |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.3b | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.1b | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | restated |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-5.7 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-7.1 | implemented-as-written |
| AC-7.2 | implemented-as-written |
| AC-7.3 | implemented-as-written |
| AC-7.4 | implemented-as-written |
| AC-7.5 | implemented-as-written |
| AC-8.1 | implemented-as-written |
| AC-8.2 | implemented-as-written |
| AC-8.3 | implemented-as-written |
| AC-8.4 | implemented-as-written |
| AC-9.1 | implemented-as-written |
| AC-9.2 | implemented-as-written |
| AC-9.3 | implemented-as-written |
| AC-9.4 | implemented-as-written |
| AC-9.5 | implemented-as-written |
| AC-10.1 | implemented-as-written |
| AC-10.2 | implemented-as-written |
| AC-10.2b | implemented-as-written |
| AC-10.2c | implemented-as-written |
| AC-10.3 | implemented-as-written |
| AC-10.4 | implemented-as-written |
| AC-10.5 | implemented-as-written |
| AC-10.5b | implemented-as-written |

## Must-fix
- AC-4.4 restated/contradicted (collected path copy gap) — The spec requires "Each pass's collected report is written to `<audit-dir>/...`", but the design's `collect` ladder explicitly returns `("report-file", report_path)` for successful primary deliveries, leaving the file in `/tmp`. This breaks the `reports:` output line which points to `docs/...`, and violates the spec's artifact location requirement. The file must be copied/moved to `collected`.
- Type consistency / CLI signature mismatch — The `PassSpec` definition (`index report_path out_path log_path rc`) fundamentally contradicts the CLI `--pass` format (`1:<report_1>:<out_1>:<rc_1>:<collected_1>`). The CLI provides `collected_1` but `PassSpec` defines `log_path` instead. Because `collected` is missing from the spec object, `collect()` has no way to know where to write the fallback extraction.
- AC-3.1 absent (`--passes < 1` validation) — The spec explicitly requires `--passes N for N<1 is rejected as an operational error`, but the design omits this validation entirely. Without an explicit check and exit, a value of `<= 0` could result in zero runs or arbitrary shell loop behavior, silently bypassing the audit.

## Should-fix
None

## Nit
- Unexplained `findings` field in `PassResult` — `PassResult` includes a `findings` field, but the `gate` function signature `tuple[str | None, int, int]` only returns the verdict, must count, and should count. It is left implicit how or where `findings` is populated.
