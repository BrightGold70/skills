## Spec-Compliance Review — `gate-non-py-production-files` Task 2 (`doc-data-definition`)

### Verification Summary

1. **Production code ([`h_mad_target_identity.py`](file:///private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/replay-t2/h-mad/scripts/h_mad_target_identity.py#L15-L50))**:
   - `Sequence` added to `from typing import Any, NamedTuple, Sequence` (line 15).
   - `DOC_DATA_SUFFIXES` (line 19) matches the nine specified suffixes in exact order: `(".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst", ".cfg", ".ini")`.
   - `_ASCII_LOWER` (line 20) uses `str.maketrans` for ASCII-only case folding (`str.lower()` is not used).
   - [`has_doc_data_suffix`](file:///private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/replay-t2/h-mad/scripts/h_mad_target_identity.py#L33-L34), [`is_doc_data`](file:///private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/replay-t2/h-mad/scripts/h_mad_target_identity.py#L37-L38), [`_is_exempt_location`](file:///private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/replay-t2/h-mad/scripts/h_mad_target_identity.py#L41-L45), and [`emit_doc_data`](file:///private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/replay-t2/h-mad/scripts/h_mad_target_identity.py#L48-L49) match the task specification and mutation anchor comments (`# M:G-DOCDATA-CASE`, `# M:G-DOCDATA-ALL`, `# M:G-EXEMPT-PARENT`, `# M:G-EXEMPT-DOCS`, `# M:G-EXEMPT-DIRS`, `# M:G-DOCDATA-EMIT`).
   - [`_is_production_python`](file:///private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/replay-t2/h-mad/scripts/h_mad_target_identity.py#L355-L371) is unedited and retains `# M:G-DOCS` and its `target_identity.json` anchors.

2. **Test suite ([`test_h_mad_doc_data.py`](file:///private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/replay-t2/h-mad/tests/test_h_mad_doc_data.py#L1-L94))**:
   - Reaches module attributes via the `identity` fixture (`importlib.import_module("h_mad_target_identity")`).
   - Defines all 23 test nodes specified in the task (14 RED against stubs, 9 GREEN against stubs and after).
   - All 66 tests across `test_h_mad_doc_data.py` and `test_h_mad_target_identity.py` pass.

3. **Mutation spec ([`doc_data_definition.json`](file:///private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/replay-t2/h-mad/tests/mutation-specs/doc_data_definition.json#L1-L81))**:
   - Contains all 7 required mutation rows (`DD-CASE`, `DD-SUFFIX`, `DD-ALL`, `DD-EMIT`, `DD-EXEMPT-DOCS`, `DD-EXEMPT-DIRS`, `DD-EXEMPT-PARENT`) with exact `symbol`, `find`, `replace`, and `test` pins.
   - Anchor checks pass (`ok=7/7` on `doc_data_definition.json`, `ok=11/11` on `target_identity.json`).

4. **Scope check**:
   - No extra features or out-of-scope modifications were introduced.

The implementation matches the task spec.

VERDICT: COMPLIANT
