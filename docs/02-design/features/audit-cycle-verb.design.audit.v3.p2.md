## Summary
The design cleanly architects the `audit-cycle` verb, correctly isolating the shell orchestration from the Python-based text collection and gating. It provides thorough condition-creating test coverage for its guards and addresses the structural flaws of concatenation-based unions. There is one narrowing of the spec regarding `delivered=` fields on pre-dispatch halts.

## Must-fix
- **Spec AC-6.4 (restated)** — Spec AC-6.4 unconditionally requires: "On UNVERIFIED, the per-pass delivered= fields are still printed". The design routes pre-dispatch halts (`assemble_halt` and `prompt_divergence`) to a `no-pass form` of the Python helper that takes no pass arguments (`no --pass at all`), making it structurally impossible to print `delivered=` fields for these cases. This is logically correct (collection channels do not exist before dispatch), but it silently narrows the spec's unconditional rule. The divergence must be explicitly documented as a narrowing of AC-6.4.

## Should-fix
None

## Nit
- The `no-pass form` of `h_mad_audit_cycle.py` (`--halt-reason <r> --size-status <v>`) does not include a `--passes <K>` parameter in its signature. Since the `render` function expects `passes` as an argument, it is unclear how the no-pass mode provides this value to the renderer.
