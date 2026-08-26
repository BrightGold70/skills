## Summary
The design provides a robust implementation of the spec, addressing edge cases like load-failing siblings and accurately enforcing the single-source rule for paths. However, there are gaps in output formatting and skipped file reporting on the success path.

| AC | Classification | AC | Classification |
|---|---|---|---|
| AC-1.1 | implemented-as-written | AC-4.4 | implemented-as-written |
| AC-1.2 | implemented-as-written | AC-4.5 | implemented-as-written |
| AC-1.3 | implemented-as-written | AC-4.6 | implemented-as-written |
| AC-1.4 | implemented-as-written | AC-5.1 | implemented-as-written |
| AC-1.5 | implemented-as-written | AC-5.2 | implemented-as-written |
| AC-2.1 | implemented-as-written | AC-5.3 | implemented-as-written |
| AC-2.2 | restated | AC-5.4 | implemented-as-written |
| AC-2.3 | implemented-as-written | AC-5.5 | implemented-as-written |
| AC-2.4 | implemented-as-written | AC-6.1 | implemented-as-written |
| AC-2.5 | implemented-as-written | AC-6.2 | implemented-as-written |
| AC-2.6 | implemented-as-written | AC-6.3 | implemented-as-written |
| AC-3.1 | implemented-as-written | AC-6.4 | restated |
| AC-3.2 | implemented-as-written | AC-6.5 | implemented-as-written |
| AC-3.3 | implemented-as-written | AC-6.6 | implemented-as-written |
| AC-3.4 | implemented-as-written | AC-7.1 | implemented-as-written |
| AC-3.5 | implemented-as-written | AC-7.2 | implemented-as-written |
| AC-4.1 | implemented-as-written | AC-7.3 | implemented-as-written |
| AC-4.2 | implemented-as-written | AC-7.4 | implemented-as-written |
| AC-4.3 | implemented-as-written | AC-7.5 | implemented-as-written |

## Must-fix
- AC-6.4 restated/dropped on success path — The spec states: "Skipped and unclassifiable files are always named in the output, so 'the sweep covered fewer specs than you think' is always visible." The design restates this as: "Detail lines name ... every skipped or unclassifiable file" but only documents this output in the `PRECHECK_FAILED` branch. If the precheck is clean (no drift), `run_spec` proceeds to the baseline and returns the standard `ALL_CAUGHT` dict without passing along the `skipped` files from the precheck sweep. This means malformed JSON files will be silently ignored on successful runs, directly violating AC-6.4 and creating a blind spot.
- AC-2.2 restated (missing counts) — The spec states: "returns `ANCHORS_OK specs=16 mutations=213 ok=213 drifted=0 unreadable=0`". The design restates this as: "expecting `ANCHORS_OK specs=16 mutations=213`." This is narrower because it drops the extended counts (`ok=`, `drifted=`, `unreadable=`) from the expectation string. If `--check-anchors` is expected to output these counts per the spec, the test plan must assert them exactly as written; if the spec is wrong because `--check-anchors` is unmodified (F2 deferred), the spec must be updated.

## Should-fix
- FR-5 suite assertion unclassifiable crash risk — The design says the suite assertion "globs its own tests/mutation-specs/ ... and calls precheck_spec() per spec". It should explicitly state that the globed files are filtered through `classify_spec_file()` first. Otherwise, a `.json` file that is `not-a-spec` will be passed directly to `precheck_spec()`, causing the test to crash with `SpecError` instead of correctly skipping it as intended.

## Nit
- Data model contradiction — In 'Precheck inside run_spec()', the `PRECHECK_FAILED` verdict dict correctly includes an `unreadable` key. However, in 'Data Model / Schema Changes', the dict shape is summarized as `{verdict, specs, drifted[], skipped[]}`, accidentally omitting the `unreadable` key.
