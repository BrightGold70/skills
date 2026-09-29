# Brainstorm: grok-codex-fallback

## Executive Summary

When codex is out of quota, route h-mad's Phase-5 implementer role and the independent audit leg to **grok** (xAI, a model family different from both Claude and codex), selected by a new optional `fallback_agent` state field, dispatched through a new `hmad-dispatch exec grok` backend that emits a parseable NDJSON transcript.

## Problem Statement

h-mad's two codex fallbacks both collapse onto the orchestrator's own model family. In Phase 5, `codex_status=exhausted` lets Claude write the production code itself. In audits, a `doc-auditor` teammate stands in for codex. That breaks the separation the workflow exists for: the author of the fix is the reviewer's twin, and their blind spots overlap by construction. Handed over from HemaSuite (`docs/handoffs/2026-09-28-main__grok-codex-fallback.md`), where grok 1.0.41 correctly executed one RED dispatch (HemaSuite #28 Task 2, 543 s, 5 fail / 1 pass as planned).

## Proposed Approach

Operator decisions from this brainstorm (2026-09-28) are marked **[D1]**–**[D4]**.

1. **Routing [D1]: a new optional `fallback_agent` field** (`grok | claude`) on `orchestrator_state.<feature>`. `codex_status` keeps its enum (`available|unavailable|exhausted`, `h-mad/scripts/h_mad_state_schema.json`) and its single meaning, *why codex is out*. `fallback_agent` says *who covers*. When the field is absent, behaviour is exactly as today (Claude is the fallback), so every existing record and caller stays valid.
   - TDD gate (`h-mad/hooks/h-mad-tdd-gate.sh`, the codex-authorship block): Claude's production write is blocked when codex is available **or** when `fallback_agent=grok`. With `fallback_agent=grok`, the BLOCK message names `hmad-dispatch exec grok`. Grok writes through its own process, so it never reaches the hook, the same as codex.
2. **Transport: `hmad-dispatch exec grok`**, parallel to `exec codex` / `exec agy` in `_cmd_exec`.
   - Invocation: `grok --cwd <dir> --always-approve --prompt-file <prompt> --output-format streaming-json`. The prompt goes in by file; `-p` cannot be combined with `--prompt-file` (argparse rc=2).
   - The inherited `CLAUDE_*` session markers are stripped, and `HPW_AGENT_BACKEND` gets an explicit default. Without both, HPW's resolver raises `Conflicting agent backend markers`.
   - It shares `exec`'s `--out`/`--log`/`--timeout`/heartbeat/atomic-`--out` machinery and verdict recovery. The OVERSIZE guard needs a grok-specific bound: `--prompt-file` is a file, so ARG_MAX does not apply.
3. **Transcript [D3]: `--output-format streaming-json`** (NDJSON, one ACP session update per line; the value is in grok's own `--help`).
   - `exec` lifts the final message out of the stream into `--out`, as it does for agy.
   - `hmad-dispatch progress` learns a `grok-ndjson` format: tool names/args digest and liveness.
   - `h_mad_review_evidence.py` learns to count grok tool calls, so a grok review can pass the "read something" gate. It must not return a false `NONE` the way codex-text did in #154.
4. **Assembler**: `h_mad_assemble_tdd.py` can target grok for its printed command block, via `--agent grok` or by reading `fallback_agent`.
5. **Audit leg [D2]**: in SKILL.md §"Never gate on one audit pass" / §"Teammate audit leg", document grok as the preferred **independent** stand-in when `codex_status≠available` and `fallback_agent=grok`. It replaces the same-family `doc-auditor` gating leg. The docs are explicit that its precision is **unmeasured**.
6. **Measurement [D4] is a separate follow-up.** This feature ships plumbing plus documentation, and states that grok is measured only on one RED. GREEN, mutation-kill, wiring-pin and audit precision stay open as their own item.

## Alternatives Considered

- **`codex_status=grok` enum value.** Rejected [D1]: it conflates availability with substitution, it cannot express "exhausted AND grok", and every enum reader would have to learn a non-status value.
- **`implementer: codex|grok|claude` rename.** Rejected [D1]: it is a migration touching every `codex_status` reader and the audit-leg prose, too much blast radius for this benefit.
- **Plain-text transcript like codex.** Rejected [D3]: `progress` would be tail-only and the evidence gate would return `UNREADABLE unsupported_format` for every grok review. That would make the audit-leg role ([D2]) ungateable.
- **Keep the doc-auditor teammate as the only audit fallback.** Rejected [D2]: it is the same model family as the orchestrator, the exact overlap this feature exists to break.
- **grok via the pane path (`send`).** Not in scope: the brief and the trial are headless-only, and `exec` avoids identity resolution entirely.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| grok's `streaming-json` event schema is unknown to us; a parser written from docs misreads it (e.g. a false `EVIDENCE: NONE`) | H | Capture a **real** grok stream-json transcript as a committed fixture before writing the parser; a positive control asserts non-zero tool count on it |
| grok ends a run with `rc=0` and no `STATUS:` line, or with a prompt-echo `STATUS:` | M | Reuse exec's boundary marker and last-match verdict recovery; a test puts a prompt-echoed contract line in the stream and asserts it is not recovered |
| `fallback_agent=grok` silently loosens the TDD gate (Claude writes pass) | M | The gate test matrix covers every combination (codex_status × fallback_agent × env override); mutation spec on the new predicate |
| `HMAD_CODEX_UNAVAILABLE=1` env override meaning under `fallback_agent=grok` is ambiguous | M | Decide in spec (open question 1) |
| HPW backend markers: grok is not an HPW backend; defaulting `HPW_AGENT_BACKEND=claude` needs `claude` on PATH | M | Default only with `:=`; document; spec decides the value (open question 2) |
| grok latency (9 min for a small RED) blows default timeouts | M | The printed command block uses a grok-specific default timeout (trial: 1500 s) |
| Cost/quota of xAI unknown; a fallback that is itself exhausted | L | Out of scope (D4 follow-up); `fallback_agent` is a declaration, so an operator can flip it back to `claude` |

## Dependencies

- `grok` CLI ≥ 1.0.41 on PATH and `XAI_API_KEY` set (both verified 2026-09-28).
- Files expected to change: `h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec`, `progress`), `h-mad/scripts/h_mad_state_schema.json`, `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/scripts/h_mad_assemble_tdd.py`, `h-mad/scripts/h_mad_review_evidence.py`, `h-mad/SKILL.md`, `h-mad/references/agent-substrate.md`, `h-mad/references/state-schema.md`.
- Trial artifacts (read-only): `/Users/kimhawk/orca/HemaSuite/docs/03-analysis/grok-tracer-2026-09-28/`.

## Open Questions

1. Under `fallback_agent=grok`, does `HMAD_CODEX_UNAVAILABLE=1` still let Claude write? The env var predates the field. Proposal: no. The env var means "codex out", `fallback_agent` still decides who covers, and a one-off Claude escape needs `fallback_agent=claude`.
2. The `HPW_AGENT_BACKEND` default for `exec grok`: `claude` (as in the trial), or leave it unset and only strip `CLAUDE_*`?
3. What is grok's stream-json final-message event, and does grok's `--sandbox <PROFILE>` have a workspace-write profile equal to codex's default? Probe with one small live dispatch during spec.
4. Should `h_mad_assemble_tdd.py` read `fallback_agent` from state automatically, or require an explicit `--agent grok`? Explicit is more auditable; automatic removes a step.
5. Does `resolved-model` need a grok branch, for the "which model actually ran" evidence? Probably yes, since `-m` exists. Scope it in the spec.

## Version History
- v1.0: Initial brainstorm draft (operator decisions D1–D4, 2026-09-28).
