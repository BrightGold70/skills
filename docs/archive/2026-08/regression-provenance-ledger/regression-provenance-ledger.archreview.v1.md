## Architectural Review: Phase 5 `regression-provenance-ledger`

The implementation fundamentally fulfills the requirements and is well-tested. However, there are two Critical violations (one invariant violation leading to a false pass, and one API contract violation) that must be fixed before this can be merged, along with two Important pattern/coupling issues.

### Critical Issues

1. **`run_pins` regex ignores `ERROR`, `XFAIL`, `SKIPPED`, causing False Passes (Invariant Violation)**
   - **File:** `h-mad/scripts/h_mad_wire_registry.py:228-229`
   - **What's wrong:** `re.match(r"^(PASSED|FAILED)\s+(\S+)", line.strip())` explicitly ignores tests that error in setup (`ERROR`), skip (`SKIPPED`), or `XFAIL`. These pins drop to the `else` block (`INTERNAL INCONSISTENCY`) and are *not* added to `broken`.
   - **Why it matters:** A test that breaks due to a setup exception (a very common regression mode) will not be counted as `broken`, resulting in `broken=0` and a `PASS` verdict. A broken wire silently evades the regression ledger guard, violating the invariant "A cannot-judge must never look like a pass".
   - **How to fix:** Any pin passed to `run_pins` in `resolving` that does not explicitly appear as `PASSED` in the output should be treated as `broken`. (e.g., in the `for record in resolving:` loop, simply `if pin in passed: verified.append(...) else: broken.append(...)`).
   - **Operator override reasonable:** No. False passes defeat the entire purpose of the ledger.

2. **`register` CLI command is an empty stub (API / Interface violation)**
   - **File:** `h-mad/scripts/h_mad_wire_registry.py:534` (and `main` logic)
   - **What's wrong:** The CLI subparser for `register` is added without any arguments (`--id`, `--caller`, etc.), and `main()` explicitly returns `0` for `args.command != "verify"` (excluding `challenge`) without executing any registration logic.
   - **Why it matters:** The design document explicitly specifies `h_mad_wire_registry.py register --id … --caller … --callee … --pin … --feature …` as a public interface. Any external caller using the CLI will receive a silent `0` success code while registering nothing, creating a silent no-op.
   - **How to fix:** Implement the `register` CLI command in `main()` to parse the required arguments, construct the record dictionary, and call the `register()` function.
   - **Operator override reasonable:** No. Shipped API contracts must be functional.

### Important Issues

3. **`--registry` flag overrides HEAD path but not BASE path**
   - **File:** `h-mad/scripts/h_mad_wire_registry.py:279`
   - **What's wrong:** `verify()` loads HEAD from the `registry` argument, but `base_records = load_base(base, DEFAULT_REGISTRY, repo)` hardcodes `DEFAULT_REGISTRY` (`.h-mad/wires.jsonl`).
   - **Why it matters:** If an operator uses `--registry path/to/custom.jsonl`, `compare()` will incorrectly diff the custom HEAD against the default BASE, generating false `undeclared_removals` or missing real ones.
   - **How to fix:** Derive the repo-relative path of the `registry` argument (e.g., `registry.relative_to(repo).as_posix()`) and pass that to `load_base()` instead of `DEFAULT_REGISTRY` (falling back safely if not relative to repo).
   - **Operator override reasonable:** Yes, if custom registries are out of scope for the current rollout, but it's a small fix.

4. **Hardcoded `--testpath h-mad/tests` in `SKILL.md` for generic projects**
   - **File:** `h-mad/SKILL.md` (Step 5f instructions)
   - **What's wrong:** Step 5f instructs the operator to run `h_mad_wire_registry.py verify ... --testpath h-mad/tests`, but then says `pytest <project>/tests/`.
   - **Why it matters:** When this skill is applied to a project other than H-MAD itself, hardcoding `h-mad/tests` will result in zero collected tests and every pin falsely reporting as `missing`.
   - **How to fix:** Update the `SKILL.md` documentation to use `--testpath <project>/tests/` to match the generic `pytest` command.
   - **Operator override reasonable:** Yes, documentation fix can be deferred, but highly recommended now to prevent operator confusion.

ASSESSMENT: WITH_FIXES
