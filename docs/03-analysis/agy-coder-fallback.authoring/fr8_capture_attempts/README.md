# FR-8 step 1 (impl-plan Task 20) — capture gate STOPPED, 2026-10-17

**sha:** `2dcb58c6` (main) · **agy:** `1.4.0` · **fixture:** `/Users/kimhawk/orca/agy-fr8-fixture`
(throwaway git repo beside this checkout; `docs/.bkit-memory.json` holds `fixture-calc` at
`phase=step5`; `.agents/hooks.json` = FR-5's exact entry + a temporary `fr8-capture` hook, copied
here as `fixture-hooks.json` / `fr8_capture_hook.py`). `h_mad_hook_wiring.py --agy` read
`AGY-GATE: WIRED` on the fixture before the first dispatch.

Dispatch: `hmad-dispatch exec agy <prompt> --cd <fixture>` (`permission_mode: always-proceed` in
every init event). Raw stream-json logs, final responses and stdout are in this directory.

## Attempts (initial instruction + three re-instructions, per Task 20's capture gate)

| # | prompt | model | captured |
|---|---|---|---|
| 1 | `capture1.txt` (all six tools) | default | `write_to_file`, `run_command`; `replace_file_content` denied by the gate and **not** captured (gate was first in `hooks.json`) |
| 2 | `capture2.txt` (four missing; capture hook moved first) | default | `replace_file_content` (+ `view_file`) |
| 3 | `capture3.txt` (three missing; list callable tools first) | `gemini-4-argon-high` | none |
| 4 | `capture3.txt` | `claude-opus-5-5-high` | none (+ one `run_command`) |

## Result: 3 of 6 required samples; the capture does not pass on a subset → Task 20 stops

Not capturable: **`multi_replace_file_content`, `sed_file`, `notebook_edit`**. All three appear in
`init.tools` (60 names in every attempt), and in all three re-instructions — across three model
families — agy answered that they are not in its declared function schemas. Notebook editing is
exposed only through `call_mcp_tool` on the `notebooks` MCP server (class (d) in the design).

## Findings

1. **`replace_file_content` names its target `TargetFile`** (sample in `captures/`). `PATH_KEYS`
   holds only `write_to_file`, so under active step5 every `replace_file_content` call is denied
   `kind=judge-error` — fail-closed, but an agy implementer cannot edit an existing file except by
   whole-file `write_to_file`. Task 20 item 2's `replace_file_content` id would be F at RED.
2. **`run_command`**: `command_key=CommandLine`, `workdir_key=Cwd` — Task 7's reads hold; item 3
   would be 2 P.
3. **`workspacePaths` is present** in every captured envelope (list holding the fixture root).
4. **Handler order is load-bearing**: with the gate first, its `deny` short-circuited the later
   `fr8-capture` handler (attempt 1). Relevant to design §"Overwrite residual" — a sibling after a
   deny does not run.
5. **`init.tools` ≠ declared tools.** The class-(b) inventory (5 names, from `init.tools`) over-counts
   what the model can call in agy 1.4.0. `class_inventory.py` second-log re-run still owed.
