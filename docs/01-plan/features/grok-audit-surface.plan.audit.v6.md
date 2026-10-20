# grok-audit-surface — plan audit v6 (operator acknowledgement sidecar)

This is not an audit pass. It records measurement-class findings from the plan audit cycles v4 and v5 that the operator defers. The gating-round cap of two rounds per revision line has been reached: c4 was round 1 and c5 round 2. Every build-class finding of c5 was fixed in the corrective revisions plan v1.10 and v1.11, which were not re-audited (SKILL.md §"Document-audit round cap").

## Must-fix
None

## Should-fix
None

## Acknowledged-not-fixed
- [prompt-divergence-repro] The observed three-shape prompt-divergence premise has no exact runnable reproduction command. It is measurement-class: fixing it changes no code or test. The scratch probe that produced it was deleted, and the plan labels the observation as recorded but not reproducible. Re-run command: re-derive it at Phase 5 by assembling the same document's audit prompt for p1 and p3 with `python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py --feature <f> --phase <p> --cycle <N> --project-root . --report-file <abs>.report.md --out <abs>.txt` (one run per pass, each with a fresh report path), then `diff` the two prompts.
