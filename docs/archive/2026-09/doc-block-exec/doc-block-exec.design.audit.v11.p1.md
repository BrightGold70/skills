## Summary
The design meticulously addresses all 48 Acceptance Criteria from the specification, providing a robust architecture for executing and verifying documentation blocks with strict adherence to the base invariants. A contradiction exists in the specified validation order for stream aliases, and there is a slight type mismatch in the pseudo-code for `substitute`, but the core design correctly implements the specified bounded execution, process-group reaping, and overwrite semantics. All ACs are `implemented-as-written`.

| Acceptance Criterion | Classification |
|---|---|
| AC-1.1 to AC-1.9 | `implemented-as-written` |
| AC-2.1 to AC-2.7 | `implemented-as-written` |
| AC-3.1 to AC-3.14 | `implemented-as-written` |
| AC-4.1 to AC-4.6 | `implemented-as-written` |
| AC-5.1 to AC-5.6 | `implemented-as-written` |
| AC-6.1 to AC-6.6 | `implemented-as-written` |

## Must-fix
- **Validation order contradiction (Axis A)** — The design explicitly requires `StreamPathsAlias` to be judged on the **opened descriptors** via `os.fstat` (which means it must happen *after* `open()` reserves the handles). However, the stated execution order in `main` lists `stream-path alias` among "the remaining validations that belong to no earlier step" that occur *before* `reserve both stream handles -> spawn`. You cannot validate the alias on reserved descriptors before you reserve them. Update the sequence in `main` to place the alias check after reservation.

## Should-fix
None

## Nit
- **Signature mismatch in pseudo-code** — The design describes the preamble composition as `text′ is substitute(block.text, subs)`. However, the API signature for `substitute` correctly takes the `Block` object itself, not its text string (`substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]`).
- **Omitted exception in `run_block` API table** — The API table entry for `run_block` lists `BadTimeout`, `BlockTimeout`, and `CleanupFailed` in its `raises` clause, but accidentally omits `LaunchFailed`, though the text immediately following the table correctly names it.
