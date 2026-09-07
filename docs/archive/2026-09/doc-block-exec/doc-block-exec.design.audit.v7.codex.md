## Summary

Axis C reconciliation is implemented-as-written for all 47 acceptance criteria; no spec criterion is restated or absent. The design nevertheless has three blocking internal verification/ordering gaps.

| Spec AC identifiers | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix

- AC-3.8's probe-then-reserve algorithm cannot provide its stated preservation guarantee: after successful append probes it opens `--stdout` with `"w"` before opening `--stderr` with `"w"`; a failure or race on the second open has already truncated the first artifact. The ordering also never explicitly puts substitution refusal before reservation. Acquire both non-truncating descriptors only after *all* refusals (including substitution) pass, then truncate/write only once both are held; add a race/fault test proving the first pre-existing artifact survives failure to reserve the second.
- The architecture says exactly two exit-2 verdicts can follow spawn (`TIMEOUT` and `CLEANUP_FAILED`), but its own stream-artifact contract says a post-run held-descriptor write failure returns `UNREADABLE reason=stream_write_failed`, a third post-spawn exit-2 outcome. This is a direct operational-state contradiction; correct the claim and make the post-spawn error/precedence model explicit.
- AC-6.4's required suite-count proof has no executable threshold. The documents cite a 2747 baseline but define the increment only as “this feature's added tests,” without naming a number or a mechanically derived set, so a test cannot distinguish deleted existing tests from a compliant result. Commit a fixed, reviewed expected collection delta (or a deterministic collector for the named new tests) and assert the resulting floor.
- The planned `docsections.json` migration merely re-points two legacy mutations while leaving all four with `_killed_by` and no `target_command`/`test`; the harness only executes and credits the per-mutation discriminator through the latter fields. That conflicts with the design's promise that every guard has a named `test` key and violates mutation/test-discrimination evidence for the moved authoritative bounder. Convert every affected mutation to the supported named-test form and run the discriminating REDs after re-pointing.

## Should-fix

- Define whether `SUBST_OVERLAP keys=<n>` counts distinct implicated keys or overlapping pairs, and require a deterministic pair/detail ordering; the current wording permits unstable diagnostics and an ambiguous registry pin.

## Nit

None
