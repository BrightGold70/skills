# Report: multi-host-runtime

## Executive Summary
The h-mad and handoff skills now run under Claude Code, OpenAI Codex, Antigravity (`agy`) and grok. Each host is declared or classified by one shared classifier, and each has its own runtime adapter. The install check covers every skill root, and a rehearsal harness pins how each host's smoke is scored. The feature merges last of three, at a 97% match rate, after two 6b fix cycles.

## Summary
The feature adds `h_mad_host.py` as the single host classifier. It feeds the context-budget and resume-decision verdicts, and fails closed on an unknown host. It also adds per-host runtime adapters, an install check across `~/.claude`, `~/.agents` and `~/.gemini`, and a V-11 smoke classifier with a 93-case rehearsal. It was rebased onto a main that had already merged the new TDD judge gate and the grok fallback. There, a fresh-context verifier reproduced four defects, and all four were resolved in 6b. D3 was kept as the design's stated residual and pinned by a rehearsal case. The main design decision in 6b was the `--host` flag: the codex TDD gate rejects an inline `HMAD_HOST=` assignment, so the adapters could not follow their own instructions under it.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 |
| Design audit cycles | 2 (plus the 6b `--host` paragraph, not re-audited) |
| Impl-plan audit cycles | 2 (round cap; v1.2 delta review 0 must) |
| Iterate cycles (Phase 6b) | 2. The telemetry row read 0 because the state write of `iterate_cycles` did not reach it; this was also seen on grok. |
| Final match rate | 97% |
| 6a-prime architectural review | `READY_TO_MERGE` (agy, tools=17; the dispatch hit rc=124 after its report had landed) |
| Tests | 4955 passing / 1 failing (the pre-existing live-binary baseline node) |
| Phases with back-propagation | Phase 4: design gained the `--host` paragraph in 6b cycle 2 |

## What Went Well
- The rebase onto two merged features replayed 36 commits with no conflict, and the registry verified 40 of 40 at 5f.
- The fresh-context verifier found four defects that the agy review did not. D2 was a real contradiction between an adapter and the gate that adapter names.
- A codex fix that exceeded its scope was caught before commit. It invented a log format that real codex never emits, and it would have made the live V-11.1 codex smoke unpassable. It was discarded, and the design's documented residual was pinned instead.

## What To Improve Next Time
- **When an adapter names a command, test it through the gate that will run it.** D2 existed because no test sent the documented command through the codex TDD gate.
- **A fix prompt must say "do not change the input format or the design".** The D3 dispatch did not, and codex rewrote 30 fixtures and the design to suit its fix.
- **Doc-derived tests that pin a measured fact must re-measure it.** D1's test hard-coded `exit1`, which went stale the moment the gate merged.
- **`iterate_cycles` does not reach the telemetry row.** File it against `h_mad_telemetry.py`.

## Carry Items
- **The documented resume call is still denied by the codex TDD gate.** `h_mad_resume_decision.py` is absent from `SAFE_HMAD_SCRIPT_OPTIONS`, and the `$(cat …)` session-id read fails the gate's shell rule. This predates the feature. It is latent while the codex gate is unarmed on this machine.
- **V-11.1..V-11.5 live smoke runs remain an operator step.** `live-smoke.md` is not yet written.
- **The replay-agy rehearsal verdict** is `FAIL V-11.1 no adapter read`, where the plan said "script ran before". Rated CHANGED/LOW: design §D10 contradicts itself, and both verdicts are FAIL.
- **D3 residual:** codex output that reproduces a whole exec event is read as an event. It is pinned by `codex-output-injection.log`. Real closure would need codex's structured `--json` stream.
- `iterate_cycles` is missing from telemetry (see above).

## Version History
- v1.0: Initial report draft (2026-09-29).
