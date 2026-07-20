# Plan Audit v1 — orca-automations-scheduled-e2e

Reviewer: agy (Gemini 3.1 Pro High). Cycle 1.

## Summary
The plan cleanly specifies a wrapper for Orca automations to enable scheduled E2E runs without new dependencies or gate coupling, reusing existing guards/extractors and maintaining the single-source contract. A schema-reference wording issue and two implementation nits need correction.

## Must-fix
None

## Should-fix
- Goal G5 refers to reconciling against the `agent-context --json` schema v1. Since this feature wraps `orca automations`, it should reference the orca automations schema (the `agent-context` phrasing reads as a copy-paste from a prior Orca integration plan). Clarify.

## Nit
- The create strategy builds argv as `args+=(--prompt "$(cat "$f")")`. This protects hmad-dispatch from a bare argv blob but still passes the full file content as a bare argv string to `orca`; if the `orca` CLI has a native file-input flag it should be used (ARG_MAX). If not, note that explicitly.
- The create flag-parsing loop passes targeting flags (`--repo`/`--workspace`/`--project`) opaquely; ensure the `while` loop captures these value-taking flags with explicit 2-arg cases rather than choking on them as unrecognized.
