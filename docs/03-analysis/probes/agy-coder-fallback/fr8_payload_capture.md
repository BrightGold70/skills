# FR-8 step 1 — payload capture record (impl-plan Task 20, v1.3 scope)

**sha at capture:** `2dcb58c6` · **agy --version:** `1.4.0` · **date:** 2026-10-17
**fixture:** `/Users/kimhawk/orca/agy-fr8-fixture` (throwaway git repo beside this checkout;
`docs/.bkit-memory.json` `fixture-calc` at `phase=step5`; `.agents/hooks.json` = FR-5's exact
entry + the temporary `fr8-capture` hook). Full attempt log, raw stream-json and every captured
envelope: `docs/03-analysis/agy-coder-fallback.authoring/fr8_capture_attempts/`.

Scope narrowed by operator decision 2026-10-17 (D-FR8-1, impl-plan Task 20 v1.3): agy 1.4.0
declares only three of the six inventory tools to the model. The other three
(`multi_replace_file_content`, `sed_file`, `notebook_edit`) were not capturable across the initial
instruction and three re-instructions, on three model families.

| tool | instruction that produced the call | stream-json evidence | `workspacePaths` | keys |
|---|---|---|---|---|
| `write_to_file` | `capture1.txt` step 1 | `capture1.log`, `tool_call` `write_to_file` | present | path `TargetFile` |
| `replace_file_content` | `capture2.txt` step 1 | `capture2.log`, `tool_call` `replace_file_content` | present | path `TargetFile` |
| `run_command` | `capture1.txt` step 6 | `capture1.log`, `tool_call` `run_command` | present | command `CommandLine`, workdir `Cwd` |

Samples are the hook's whole stdin, unedited (`cmp` against the attempt copy), committed under
`h-mad/tests/fixtures/agy-payloads/` with `capture.json`.

## `init.tools` re-inventory

`class_inventory.py <2026-10-01 log> fr8_capture_attempts/capture1.log` → second log `total=60`
(expected 58, MOVED): class a 11 (unchanged), b 5, c 1, d 43 — `d: added=['list_plugin_accounts',
'search_marketplace']`, nothing removed. New names fall to class (d) (deny under active), so the
partition change is fail-closed. `PROBE: FAIL` is the expected total drift, not a class-(a) loss.

## Capture hook removed (probe-then-delete)

```
$ ls -la /Users/kimhawk/orca/agy-fr8-fixture/.agents
.rw-r--r--@ 322 kimhawk 17 Oct 22:12 hooks.json
$ python3 -c "import json;print(list(json.load(open('.agents/hooks.json'))))"
['h-mad-agy-tdd-gate']
$ h_mad_hook_wiring.py --agy --project-root .
AGY-GATE: WIRED
```
