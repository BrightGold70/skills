# Architectural Review Report: tdd-gate-fail-opens

## Findings

**1. Critical Pattern/Design Violation: Codex hook drops directory exclusions**
- **File:** `h-mad/hooks/h-mad-codex-tdd-gate.py`
- **Location:** `_is_production_python`
- **Description:** The implementation changed the final return statement to `return True`, completely removing the directory path parts check (`return "tests" not in path.parts and "fixtures" not in path.parts`). 
- **Why it matters:** The design explicitly states: "Directory parts are shared (`\"tests\"` and `\"fixtures\"` not in `path.parts`), so a `tests/` parent exempts every name." Removing this check breaks the exemption for files located inside test directories, incorrectly treating them as production code and subjecting them to TDD gate blocks.
- **How to fix:** Restore the `return "tests" not in path.parts and "fixtures" not in path.parts` check at the end of `_is_production_python`.

**2. Critical Pattern/Design Violation: Claude hook fails to filter out test files for production targets**
- **File:** `h-mad/hooks/h-mad-tdd-gate.sh`
- **Location:** The third per-name loop setting `PRODUCTION_TARGET` (around line 253).
- **Description:** When picking the production target, the loop only skips non-`.py` files (`if [[ "$FOLDED_NAME" != *.py ]]; then continue; fi`). It does NOT skip test names (e.g. `test_*.py`) when assigning the production target. 
- **Why it matters:** The design requires that "TARGET_PATH becomes the canonical parent joined with the lexicographically first name for which the production test holds". If a final referent has both a production name (`z.py`) and a test name (`test_a.py`), the lexicographically sorted `CANON_NAMES` processes `test_a.py` first. Since it ends in `.py`, the script sets `TARGET_PATH` to `test_a.py`. The judge will then attempt to evaluate it as a production file, failing to recognize it as a test alias and blocking the write incorrectly.
- **How to fix:** Inside the final per-name loop, add a `case` check that skips test names when selecting the `PRODUCTION_TARGET`.

**3. Critical Design Violation: Canonicaliser alters the spelled component on arm-2**
- **File:** `h-mad/scripts/h_mad_target_identity.py`
- **Location:** `_on_disk_component` and its call sites within `canonicalise`.
- **Description:** When `canonical_directory` throws an `OSError` (triggering an arm-2 unresolvable identity), the implementation calls a new helper function `_on_disk_component` which scans the parent directory and replaces the spelled component name with the exact casing found on disk. 
- **Why it matters:** The design explicitly defines the arm-2 component field as "component the spelled component that failed, or empty" and specifically states "When the failed component is the root, prefix, root, and component are all the spelled root". Replacing the spelled component with the on-disk name directly violates the data model for the arm-2 Identity record and alters the text printed to the judge output. 
- **How to fix:** Remove `_on_disk_component` completely. When constructing an arm-2 `Identity`, pass the exact spelled component strings directly into the tuple without trying to list the parent directory.

ASSESSMENT: WITH_FIXES
