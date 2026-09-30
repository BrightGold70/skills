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

For pytest, the judge walks from the test file toward the project root and chooses the nearest
`.venv` with `.venv/bin/python`. Before using it, the judge requires realpath containment of both
`.venv` and `.venv/bin` within the root and a regular, non-symlink `pyvenv.cfg`; a candidate that
fails these checks is DENY `venv-escapes-root`. With no candidate, it uses the fallback interpreter.
These checks leave the interpreter itself, installed packages, and test code trusted: a Python
executable can still be a symlink outside the root. The verdict is scored from pytest's
summary line (`N failed` or other summary counts), never its rc.

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

## Install

Link both skills from the checkout into Codex's skill directory:

```bash
ln -s /path/to/checkout/h-mad ~/.agents/skills/h-mad
ln -s /path/to/checkout/handoff ~/.agents/skills/handoff
```

For either link, an existing non-symlink at either path is an operator decision and is never overwritten.
Creating the link does not re-arm HemaSuite's codex TDD gate by itself. The gate fires because
HemaSuite's tracked `.codex/hooks.json` registers `h-mad-codex-tdd-gate.py` under `PreToolUse` and
Codex has trusted that entry (`hooks.state` in `$CODEX_HOME/config.toml`). Verified live 2026-09-29:
a `codex exec` in HemaSuite logged `hook: PreToolUse Blocked` while a feature there was in `step5`.

Check the installed links with:

```bash
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_install_check.py" --agents-skills-dir ~/.agents/skills
```

## Context budget and claims

Use the explicit host flag for the budget and resume oracle. Replace `<HMAD_SKILL_ROOT>` with the literal absolute path of the resolved skill root before running: the codex TDD gate accepts only a literal absolute script path (it rejects `$` and `~`), and a checkout path must never be written into this file. The budget check is:

```bash
python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_context_budget.py" --host codex
```

`CTXBUDGET: UNKNOWN reason=host_unsupported` is expected, not an `OK` verdict. The
80% run ceiling is unenforced on Codex; substitute: none. There is no context indicator
the orchestrator can read from this host.

Codex has no documented session-id environment variable. Mint an id once at bootstrap
in the checkout's git directory, per feature. A second mint prints `SID: NOT_MINTED`:
the existing file belongs to another or earlier session, so halt for the operator. It is
never deleted or reused without the operator. Each subsequent command reads the id from
that file in its own shell invocation. Keep `<feature>` literal here and replace it with
the active feature name when executing these lines. The resume oracle decides the route
before any state write; use `--create --claim` only for its `start_fresh` verdict.

```bash
( set -C; python3 -c 'import uuid; print(uuid.uuid4())' > "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>" ) && echo "SID: MINTED" || echo "SID: NOT_MINTED"
python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_resume_decision.py" --host codex --state docs/.bkit-memory.json --feature "<feature>" --session-id-from-git-dir
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --create --claim "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --claim "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --beat --session-id "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --set current_phase=5 --session-id "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --release --session-id "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
```

If the id file becomes unreadable, the oracle cannot read the id and returns `cannot_judge`. An operator
who deletes or rewrites the file while the session is live can give it another session's
id or none.

## Construct mapping

The status and mapping below apply to the current Codex host. Sources identify the
observations and design references behind each mapping.

| construct | status | mapping | source |
|---|---|---|---|
| `subagent-call` | mapped | Use `collaboration.spawn_agent` with `fork_turns: "none"`; include the agent file text in the prompt. | Observed Codex multi-agent instructions; `codex features list` (DP16). |
| `skill-call` | mapped | Codex lists installed skills and their `SKILL.md` paths in its Skills instructions; name `$h-mad` or the skill in plain text. | Observed Codex skill entries (DP16); V-11.1 load check. |
| `advisor` | not-applicable | Codex has no advisor tool; use `hmad-dispatch exec` for agy\|grok, or `collaboration.spawn_agent` with `fork_turns: "all"` for an independent review. | Observed Codex multi-agent instructions; `codex --help` (DP16). |
| `send-message` | not-applicable | The observed Codex rollouts have no message call; dispatch a fresh author with the prior report path. | Codex rollout observations (DP16). |
| `hook-event` | mapped | Codex hook events run `hooks/h-mad-codex-tdd-gate.py` through the active hooks file. | Observed Codex hook event fixture. |
| `session-id-env` | not-applicable | Codex has no documented session id variable; mint the file id with `uuid.uuid4()` and pass it to the oracle, which can return `owned_elsewhere`. | F14; FR-9 minted-id procedure. |
| `claude-config-dir` | not-applicable | Codex uses its own configuration scope, so Claude settings paths do not apply here. | `codex --help` configuration option (DP16). |
| `claude-md` | mapped | Read `AGENTS.md` for project instructions. | Observed Codex rollout instruction blocks (DP16). |
| `claude-skills-dir` | mapped | Resolve `$HMAD_SKILL_ROOT` from the loaded skill path under `~/.agents/skills/<skill>`. | Observed Codex skill paths (DP16); V-11.1 load check. |
| `claude-agents-dir` | not-applicable | Codex has no file based agent registry; put the agent file text into the spawn prompt. | `codex --help` agents command (DP16). |
| `claude-hooks-dir` | not-applicable | Codex wires its gate from the active hooks file, so Claude's hook directory is not used. | Observed Codex hook fixture. |
| `claude-settings` | not-applicable | Codex hooks use a hooks file rather than Claude settings; this project's file is `.codex/hooks.json`. | Observed Codex hooks file; `codex --help` (DP16). |
| `claude-handoffs-dir` | mapped | Keep the plain handoff file store that every host reads and writes through its shell. | Observed handoff index file. |
| `claude-projects-store` | not-applicable | Codex memory lives under its own home; do not point the memory index check at Claude's project store. | `codex features list`; observed Codex memories directory (DP16). |
| `claude-home-bare` | not-applicable | Codex uses its own home directory, so nothing is relinked from Claude's home. | `codex --help` configuration option (DP16). |
| `session-reset-command` | not-applicable | No Codex reset command is evidenced; start a fresh `codex exec` session instead. | `codex --help`; rollout history check (DP16). |
| `skill-slash-invocation` | mapped | Name `$h-mad` or `$handoff`, or use the skill name in plain text. | Observed Codex Skills trigger rules (DP16). |
