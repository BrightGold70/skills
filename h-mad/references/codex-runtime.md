# Codex runtime adapter

Use this adapter only when the active host is OpenAI Codex. It overrides host-specific mechanics
in `../SKILL.md`; it does not change H-MAD's gates or evidence contract.

## Package and project roots

Set `HMAD_SKILL_ROOT` to the installed package containing this reference. Resolve it from the
loaded skill path. Run scripts as `python3 "$HMAD_SKILL_ROOT/scripts/<script>.py"` and the dispatcher
as `"$HMAD_SKILL_ROOT/bin/hmad-dispatch"`. Never derive the package from a user-specific checkout.

The project root is `git rev-parse --show-toplevel`. Project state and invariants remain
`docs/.bkit-memory.json` and `.h-mad/invariants.md` beneath that root. A nested project may own its
own state; preserve the source walk-up and containment rules.

Codex installation does not run Claude agent-registration or install checks. Validate that
`$HMAD_SKILL_ROOT` contains `SKILL.md`, `scripts/`, `references/`, `hooks/`, and `agents/`. Project
hook wiring uses `hooks/h-mad-codex-tdd-gate.py` through the active Codex `hooks.json`. Before
Phase 5, run `python3 "$HMAD_SKILL_ROOT/hooks/h-mad-codex-tdd-gate.py" --self-check` and require
`CODEX-TDD-GATE: PASS`; this checks the installed parser and shell policy, not host activation.
Separately verify the hooks file matches `apply_patch` and the host's canonical shell tool name.
Hook configuration is snapshotted when a Codex session starts, so restart the session after
installing or changing the hook. If activation or trust cannot be established, halt with
`step5:codex_tdd_hook_unverified` instead of claiming mechanical enforcement.

### Trust boundary

The hook is a **workflow guard, not an OS security sandbox**. It prevents accidental or direct
production-Python writes through recognized Codex file tools and refuses unrecognized shell
execution during active `step5`. RED/GREEN necessarily executes pytest, so test modules and the
exact H-MAD control-script allowlist are trusted code. A malicious test can mutate the worktree at
import time; do not run unreviewed or adversarial tests under this contract. Use an OS/container
sandbox with production paths mounted read-only when executing untrusted test code. The hook's
`--self-check` establishes parser and policy behavior only; it does not strengthen this boundary.

## Collaboration mapping

- Replace a named teammate author with `collaboration.spawn_agent` using `fork_turns: "none"`.
  Give it the matching file from `$HMAD_SKILL_ROOT/agents/`, the one document it owns, the project
  invariant path, and its acceptance contract. The root orchestrator retains state ownership.
- Replace a context-inheriting fork with `collaboration.spawn_agent` using `fork_turns: "all"`.
- Keep authoring and approval separate. A writer never approves its own artifact. Use a fresh
  reviewer or verifier lane for every approval pass.
- Two independent audit surfaces still means two independent contexts. Run both when slots permit;
  if capacity prevents the required second surface, record the halt instead of treating one review
  as two. Verify findings against files before acting on them.
- Use `request_user_input` only for the manual Phase 1 through Phase 4 checkpoints when available.
  If unavailable, present one focused approval question in the final response and pause.
- Do not recursively spawn subagents unless the active project policy explicitly permits it.

## Seven phases

1. **Phase 1 — Brainstorm.** Ground assumptions in the repository, write the brainstorm artifact,
   and obtain user approval.
2. **Phase 2 — Specify.** Dispatch the spec author in fresh context, validate Given/When/Then
   behavior, run the required audit surfaces, and obtain approval.
3. **Phase 3 — Plan.** Author FRs, NFRs, success criteria, scope, risks, and affected files; precheck,
   audit through the required rounds and acknowledgements, then obtain approval.
4. **Phase 4 — Design.** Produce interfaces, schemas, and genuinely distinct architecture options;
   precheck and audit through the same evidence gates, then obtain approval.
5. **Phase 5 — Implementation.** Author the implementation plan in fresh context and audit it before
   the baseline. Write tests first and prove **RED**. Only then write minimal production code to reach
   **GREEN**, refactor, and run a separate module-level compliance review. The Codex hook enforces
   recognized file writes during an active `step5`; shell calls are fail-closed except for a small
   allowlist of test, read-only, and H-MAD control commands. Keep claims alive during long dispatches.
6. **Phase 6 — Verification.** Run the independent architectural review first, then gap analysis and
   iteration. Exit only at at least **90%** design match and **100%** relevant test pass, with review
   findings verified against the actual diff.
7. **Phase 7 — Closure.** Run phase preconditions, produce the report and archive, reconcile the
   feature branch through the recorded integration route, run any required post-integration suite,
   commit, push when authorized by the workflow, verify reachability, release the claim, and stop.

## State and halt discipline

Use the canonical state scripts and parse their verdict tokens, never only process exit status.
Create or claim with the current session id, refresh the heartbeat on writes and long waits, and
release only as the owner. On a failed gate, write the exact `halt_reason`, preserve the artifacts,
and stop. `/h-mad status` remains read-only; `/h-mad reset` clears only the selected orchestrator
record and never deletes docs or reverts git.

The main `SKILL.md` remains authoritative for audit rounds, origin-tagged findings, delta
self-review, measurement discipline, mutation verification, wire pins, report-file verdicts,
integration, and telemetry. Where an example uses a host-specific tool name, apply this adapter's
mapping while preserving the surrounding invariant.
