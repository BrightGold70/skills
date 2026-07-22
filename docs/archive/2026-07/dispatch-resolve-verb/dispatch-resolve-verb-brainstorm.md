# Brainstorm: dispatch-resolve-verb

## Executive Summary
Add a `hmad-dispatch resolve <agent>` verb that resolves a single agent (codex|agy) to its concrete terminal/surface handle on stdout — a scriptable, single-agent form of the resolution `env` already performs for both agents.

## Problem Statement
`hmad-dispatch env` is the only surface that reports agent→handle resolution, and it always prints BOTH agents in a human-formatted block (`codex -> <handle>` / `agy -> UNRESOLVED`). A script that needs just one agent's handle — to pin it, to pass it to another `orca` call, or to gate on resolvability — has to run `env` and parse a specific line out of prose. There is no clean machine-readable single-agent lookup, even though the underlying `_resolve_target` function already computes exactly that.

## Proposed Approach
Expose `_resolve_target` directly as a first-class verb: `resolve <agent>`.

- On success: print the resolved handle to stdout, exit 0.
- On UNRESOLVED: print nothing to stdout; the existing `_orca_find`/`_cmux_find` diagnostic (candidate count + pin hint) already goes to stderr; exit 1.
- On unknown agent: stderr message, exit 2.

`_resolve_target` already returns this exact 0/1/2 contract and already emits the stderr diagnostics and pin/env-var overrides — so the verb is a thin, faithful wrapper with an explicit `codex|agy` argument guard. No resolution logic is duplicated; `env` and `resolve` compute identically because they call the same function.

## Decisions (from Phase-1 clarification)
- **UNRESOLVED → stderr diagnostic** (stdout empty). Mirrors `_orca_find`'s existing message so a caller capturing stdout still sees *why* on stderr.
- **Exit codes mirror `_resolve_target`**: `0` resolved · `1` unresolved (no/ambiguous pane) · `2` unknown agent.
- **Argument restricted to `codex|agy`** — an unknown token exits 2 with a stderr message (consistent with `_resolve_target`'s own `*)` branch and `env`'s agent loop).

## Alternatives Considered
- **`env --agent <a>` flag**: overloads `env` (whose job is the full environment snapshot: substrate + both agents + orchestration). A dedicated verb is clearer and keeps `env` a single-purpose snapshot.
- **`env --json` then `jq`**: heavier for callers, requires a JSON surface `env` doesn't currently emit, and still forces the caller to parse. Out of scope.
- **Silent-on-unresolved** (no stderr): rejected in Phase 1 — loses the actionable candidate-count/pin hint that makes an ambiguous resolution debuggable.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Verb diverges from `env`'s resolution over time | L | Both call the SAME `_resolve_target`; a test asserts `resolve <a>` handle == the handle `env` prints for `<a>`. |
| Unknown-agent token silently resolves to nothing (exit 1 vs 2 confusion) | L | Explicit `codex\|agy` guard → exit 2 before calling `_resolve_target`; test covers a bad token. |
| stderr diagnostic leaks into a caller's captured stdout | L | Diagnostic stays on stderr (fd 2); stdout carries only the handle. Test captures streams separately. |

## Dependencies
None. Self-contained change to `h-mad/scripts/hmad-dispatch.sh` + its test suite. No new files, no other skill, no HemaSuite.

## Open Questions
- None outstanding — the three Phase-1 decisions close the contract.

## Version History
- v1.0: Initial brainstorm draft.
