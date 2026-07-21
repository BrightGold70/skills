# Spec: orca-git-native-checkpoints-and-merge-gate

## Executive Summary
Add a shared `hmad-dispatch worktree-comment` verb, flip the substrate-detection default to Orca, stamp durable Orca worktree checkpoints from `handoff` and `h-mad`, and gate the Phase-5 winner-merge as a conflict/ambiguity safety valve — all substrate-detected so non-Orca environments keep today's exact pure-git behavior.

## Goal
Give both skills git-native, cross-session, mobile-visible progress state and a safe merge decision record when running under Orca, with zero behavior change when Orca is absent.

## Functional Requirements

### FR-1: `worktree-comment` and `worktree-current` wrapper verbs
- **Description**: Two new `hmad-dispatch` verbs give both skills a wrapper-mediated Orca surface so no raw `orca` call lands in a skill body (the chokepoint invariant). `worktree-comment <selector> <text>` sets an Orca worktree's free-text comment via `orca worktree set --worktree <selector> --comment <text> --json`. `worktree-current` returns the active worktree JSON via `orca worktree current --json`, for the READ-mode reconcile (FR-4); sibling enumeration reuses the existing `worktree-ps` verb.
- **Acceptance Criteria**:
  - AC-1.1: With `substrate=orca`, `worktree-comment <sel> "<text>"` invokes `orca worktree set --worktree <sel> --comment "<text>" --json` exactly once and exits 0 when Orca returns `ok:true`.
  - AC-1.2: `<selector>` accepts the same selector forms the other worktree verbs accept (`active`, `id:<id>`); `active` is the default when selector is omitted or given as `active`.
  - AC-1.3: Missing `<text>` argument to `worktree-comment` exits non-zero (code 2) with a `missing required argument` message on stderr and invokes no `orca` command.
  - AC-1.4: With `substrate≠orca`, both `worktree-comment` and `worktree-current` exit non-zero with a message naming the required substrate and invoke no `orca` command (mirrors `_require_orca`).
  - AC-1.5: When the underlying `orca` call returns `ok:false` or non-zero, the verb propagates a non-zero exit and surfaces Orca's error text on stderr; it never prints `OK`/success.
  - AC-1.6: Both new verbs are listed in the wrapper's header verb catalogue and `main()` dispatch alongside the existing `worktree-create|worktree-ps|worktree-rm`.
  - AC-1.7: With `substrate=orca`, `worktree-current` invokes `orca worktree current --json` exactly once and emits the worktree JSON payload on stdout; it issues no mutating `orca` call.

### FR-2: Substrate-detection default flip (cmux → orca)
- **Description**: When both `cmux` and `orca` binaries are present and no override/marker applies, `_detect_substrate` resolves to `orca` (was `cmux`).
- **Acceptance Criteria**:
  - AC-2.1: Both binaries present, no `HMAD_SUBSTRATE`, no session markers → detection returns `orca`.
  - AC-2.2: Only `cmux` present → returns `cmux`. Only `orca` present → returns `orca`. Neither present → non-zero (unchanged).
  - AC-2.3: `HMAD_SUBSTRATE=cmux` forces `cmux` even with both present; `HMAD_SUBSTRATE=orca` forces `orca` (override precedence unchanged).
  - AC-2.4: Session-marker precedence is unchanged: `CMUX`/`CMUX_PANE` set → `cmux`; `ORCA_TERMINAL_ID`/`ORCA_SESSION` set → `orca`; markers outrank binary presence, `HMAD_SUBSTRATE` outranks markers.

### FR-3: `handoff` WRITE-mode checkpoint stamp (H1)
- **Description**: In WRITE mode, after writing the handoff markdown, `handoff` stamps a structured Orca worktree comment on the active worktree.
- **Acceptance Criteria**:
  - AC-3.1: Under Orca, a successful WRITE stamps the active worktree comment in the form `handoff: <slug> · <status> · next: <next-step>`, where `<slug>` is the handoff doc slug.
  - AC-3.2: The stamp goes through `hmad-dispatch worktree-comment active "<text>"` (not a raw `orca` call in the skill body).
  - AC-3.3: A failed/absent stamp (non-orca, no runtime) is non-blocking: WRITE still completes and writes the markdown; the skill notes the skip and never errors the handoff on it.
  - AC-3.4: `handoff`'s `SKILL.md` frontmatter and body document the WRITE-mode stamp behavior (manifest integrity: behavior change reflected in contract).

### FR-4: `handoff` READ-mode worktree reconcile (H2)
- **Description**: In READ (resume) mode, `handoff` reconciles the loaded doc against live Orca worktree state in addition to the existing git/PID reconcile.
- **Acceptance Criteria**:
  - AC-4.1: Under Orca, READ runs `hmad-dispatch worktree-current` (which wraps `orca worktree current --json`) and verifies the current worktree matches the doc's branch/worktree context; a mismatch is surfaced as a divergence (not silently ignored).
  - AC-4.2: Under Orca, READ enumerates sibling worktrees via `hmad-dispatch worktree-ps` (existing verb, wraps `orca worktree ps --json`) and surfaces in-flight siblings (all worktrees, each labeled with its branch + comment) so the resumer sees parallel work.
  - AC-4.3: The worktree reconcile augments, does not replace, the existing Step-0/Step-3 git+PID reconciliation; with Orca absent, READ behaves exactly as today.
  - AC-4.4: The reconcile is read-only: it goes only through the read-only wrapper verbs (`worktree-current`, `worktree-ps`) and issues no `worktree-comment`/`worktree-create`/`worktree-rm`.
  - AC-4.5: The reconcile issues no raw `orca` call from the skill body — it routes exclusively through `hmad-dispatch` verbs (chokepoint invariant), consistent with FR-3's stamp.

### FR-5: Substrate-gated graceful degradation (H3)
- **Description**: All Orca-specific behavior in FR-3/FR-4 (and callers of FR-1) is gated on detected substrate; a non-Orca environment produces byte-identical behavior to the pre-feature skill.
- **Acceptance Criteria**:
  - AC-5.1: With no `orca` runtime, `handoff` WRITE produces the same markdown output it produces today and emits no fatal error from the (skipped) stamp.
  - AC-5.2: With no `orca` runtime, `handoff` READ performs the same git/PID reconcile it performs today and skips the worktree reconcile silently (one log line, not an error).
  - AC-5.3: Every skipped Orca enrichment emits a single, greppable non-fatal marker (e.g. `[handoff] worktree_comment_skipped` / `[handoff] worktree_reconcile_skipped`), never a stack trace or non-zero skill exit.

### FR-6: Phase-5 winner-merge decision gate (M2)
- **Description**: The Phase-5 fanout winner-merge (`git merge --no-ff <module-branch>`) is wrapped in a decision gate that auto-resolves on the clean path and blocks for a human on conflict/ambiguity.
- **Acceptance Criteria**:
  - AC-6.1: When the module's audit/verdict is clean AND `git merge --no-ff` succeeds with no unmerged paths, the orchestrator records a `gate-create`/`gate-resolve` `yes` decision for the merge (audit trail) without pausing for human input, and logs a `[H-MAD] merge_gate auto-resolved module=<module>` marker.
  - AC-6.2: When `git merge --no-ff` fails or `git ls-files --unmerged` is non-empty, the orchestrator runs `git merge --abort`, opens a **blocking** `gate-create` with the question naming the module + conflict, and waits for `gate-resolve` before proceeding (no auto-merge).
  - AC-6.3: When the module verdict is `DRIFT`/non-clean, the merge is not attempted; a blocking gate is opened for the human decision.
  - AC-6.4: The gate path is Orca-orchestration-only (`orchestration: on`); when orchestration is off, Phase-5 uses the existing serial/`git merge --no-ff` fallback unchanged (no gate), and this fallback is documented.
  - AC-6.5: The gate wrap is documented in `references/orchestration-mode.md` (the Phase-5 fanout section) so the merge-gate contract is discoverable, not implicit.

### FR-7: Phase-5 progress checkpoints (M1, follow-on)
- **Description**: Fanned Phase-5 workers stamp worktree comments at RED/GREEN/audit boundaries.
- **Acceptance Criteria**:
  - AC-7.1: At each of RED-verified, GREEN-verified, and audit-complete for a fanned module, the orchestrator calls `worktree-comment <module-selector> "h-mad <feature> · <module> · <RED|GREEN|audit> · <n>/<total>"`.
  - AC-7.2: The checkpoint call is non-blocking (FR-5 degradation rules apply); a failed stamp never halts the fanout.
  - AC-7.3: Documented in `references/orchestration-mode.md`.

### FR-8: Diff-anchored review-gate surfacing (M3, follow-on)
- **Description**: Review-gate diff surfacing prefers the worktree's recorded start-from ref over `HEAD~n`.
- **Acceptance Criteria**:
  - AC-8.1: The existing `hmad-dispatch file-open-changed`/`file-diff` review surfacing is documented to anchor against the worktree base ref (start-from) when under Orca, and this remains best-effort/non-blocking per the existing SKILL rule.
  - AC-8.2: No regression to the existing cmux review flow (surfacing stays optional, never a gate precondition).

### FR-9: Orca ship-path documentation (M4, follow-on)
- **Description**: Document that the post-merge ship path (commit/push/PR) uses Orca's Source Control actions with `--force-with-lease` safety, rather than a new automated verb.
- **Acceptance Criteria**:
  - AC-9.1: `references/orchestration-mode.md` documents the Orca ship path (commit → push with `--force-with-lease` → hosted-review PR) as the recommended post-merge flow under Orca.
  - AC-9.2: No new push/force-push automation is added to `hmad-dispatch`; the existing `Never run git push --force` invariant is preserved.

## Non-Functional Requirements
- Performance: N/A (per-call overhead is a single `orca` CLI invocation at human-scale checkpoints; no hot path).
- Security: No new credentials or network surface. Force-push safety preserved (FR-9 AC-9.2). Skill self-containment preserved — no cross-skill internal imports (repo Axis B).
- Compatibility: Non-Orca environments MUST be byte-identical to pre-feature behavior (FR-5). `HMAD_SUBSTRATE`/marker override precedence unchanged (FR-2). Existing `hmad-dispatch` verbs unchanged.

## Out-of-Scope
- Replacing the markdown handoff doc with Orca comments (comment augments, never replaces).
- Syncing the `~/.claude/skills/handoff` install copy from the repo copy — flagged as a manual closure step, not code in this feature.
- A new automated commit/push/PR verb (FR-9 is document-only).
- Any HemaSuite code change (agent-substrate wiring is documented usage only).
- Gating merges when orchestration is off (serial fallback stays gate-free).

## Assumptions
- `orca` CLI is on PATH and `orca status --json` reports a reachable runtime when `substrate=orca`.
- The `hmad-dispatch` wrapper is the sole Orca-invocation surface for both skills (repo Axis B: self-containment).
- `handoff` is developed in the repo copy (`/Users/kimhawk/orca/skills/handoff`); install-copy sync is out of scope.
- Selector semantics (`active`, `id:<id>`) match the existing worktree verbs.

## Version History
- v1.0: Initial specification draft.
- v1.1: Plan-audit cycle-1 must-fix resolved — FR-4 READ reconcile now routes through `hmad-dispatch worktree-current` (new) + `worktree-ps` (existing) instead of raw `orca` calls, preserving the chokepoint invariant; FR-1 extended to add the `worktree-current` verb (AC-1.7) and FR-4 gains AC-4.5.
