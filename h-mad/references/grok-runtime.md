# grok runtime adapter

Use this adapter when the active H-MAD host is grok. It supplies host mechanics for
`../SKILL.md`; the phase gates and evidence contract still apply.

## Version and compatibility

These mappings were checked against grok 1.0.41. Use `grok inspect`, especially its
Harness Compatibility section, to check the active installation. Record a newer
version at live smoke time instead of assuming it behaves the same way.
The Claude skill and hook bridges are `compat.claude.skills` and
`compat.claude.hooks`, with environment toggles `GROK_CLAUDE_SKILLS_ENABLED` and
`GROK_CLAUDE_HOOKS_ENABLED` respectively. Verify the active settings before relying
on either bridge.

## Package and project roots

Set `HMAD_SKILL_ROOT` from the loaded skill path. Today grok loads
`~/.claude/skills/h-mad` through `compat.claude.skills`; an operator-installed
`~/.agents/skills/h-mad` link can point to the same checkout. Run scripts from
`"$HMAD_SKILL_ROOT/scripts/"` and the dispatcher from
`"$HMAD_SKILL_ROOT/bin/hmad-dispatch"`. Never infer the package from a user-specific
checkout path.

The project root is `git rev-parse --show-toplevel`. Keep project state at
`docs/.bkit-memory.json` and invariants at `.h-mad/invariants.md` beneath that root.
Preserve the source walk-up and containment rules for nested projects.

## Install

Link both skills from the checkout into the shared agent skill directory:

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

## Project trust

Global hooks in `~/.claude/settings.json` need no project trust grant. A project
Claude hook is silently skipped until the operator grants `/hooks-trust` or launches
grok with `--trust`. Verify the active hook source and trust state before Phase 5.

## Hooks

Under `compat.claude.hooks`, grok sends camelCase fields such as `toolInput` and
`sessionId`. The `hook_event_name` field has Claude's PascalCase value;
`hookEventName` has grok's
snake_case value. Matcher aliases map `Edit`, `Write`, and `MultiEdit` to
`search_replace`, `Bash` to `run_terminal_command`, and `Task` to
`spawn_subagent`. For a blocking `PreToolUse` hook, `exit 2` denies the operation;
other non-zero exits fail open.
There is a 5 s handler limit, after which the handler fails open.

The global `PostToolUse` hook `h-mad-advisor-warn.sh` runs without `HMAD_HOST`.
Any `CTXBUDGET` text it injects on grok reflects a Claude transcript's reading;
ignore that text for grok's context budget decision.

## The TDD gate

Phase 5 halts with `step5:grok_tdd_hook_unverified` until a real grok refusal of
a production write has been observed. At rebased base `52a78ca8`, the gate refuses
with `permissionDecision: "deny"` and exit 0, falling back to `exit 2`; grok honors
both refusal forms. The gate still reads `tool_input.file_path`, not grok's
`toolInput` payload; in step 5 a `toolInput`-only write therefore has no identified
target and is refused ("could not identify the write target"), so that gap fails closed. A handler reaching the 5 s limit fails open. Running `pytest` in RED and GREEN
does not prove that the host hook blocked a production write. Verify the refusal
through the live smoke before claiming mechanical enforcement.

## Author and reviewer roles

`spawn_subagent` cannot select an agent by name. Carry the full role text from
`$HMAD_SKILL_ROOT/agents/<name>.md` in the `prompt`, along with the task, invariants,
and acceptance contract. Read the result through `get_command_or_subagent_output`.
Keep the author and reviewer in distinct contexts and cap nesting at one level.
There is no filesystem jail for a subagent: inspect `git status --short`, including
tracked and untracked changes, after each dispatch.

## Context budget and claims

Use the explicit host flag for the budget and resume oracle. Replace `<HMAD_SKILL_ROOT>` with the literal absolute path of the resolved skill root before running: the codex TDD gate accepts only a literal absolute script path (it rejects `$` and `~`), and a checkout path must never be written into this file. The budget check is:

```bash
python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_context_budget.py" --host grok
```

`CTXBUDGET: UNKNOWN reason=host_unsupported` is expected, never an `OK` verdict.
The 80% run ceiling is unenforced on grok; substitute: none. The operator can use
`/context` interactively, but the model cannot read that indicator. It is a manual
operator action, not an orchestrator gate.

`GROK_SESSION_ID` is documented for hook processes only. Use it in place of a
minted id only after the live smoke records it present in the orchestrator's shell.
Until then, mint an id once at bootstrap in the checkout's git directory, per
feature. A second mint prints `SID: NOT_MINTED`: the existing file belongs to
another or earlier session, so halt for the operator. It is never deleted or reused without the operator.
Every later command reads the id from that file in its own shell invocation.
Replace `<feature>` with the active feature name when executing these lines. The
resume oracle decides the route before any state write; use `--create --claim` only
for its `start_fresh` verdict, or to reconstruct a lost record after `state_lost` exactly as
the decision table in `SKILL.md` prescribes (restore the file from git first if it is tracked).
`state_lost` and `cannot_judge` otherwise STOP: neither is a free claim.

```bash
( set -C; python3 -c 'import uuid; print(uuid.uuid4())' > "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>" ) && echo "SID: MINTED" || echo "SID: NOT_MINTED"
python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_resume_decision.py" --host grok --state docs/.bkit-memory.json --feature "<feature>" --session-id-from-git-dir
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --create --claim "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --claim "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --beat --session-id "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --set current_phase=5 --session-id "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_state_write.py" docs/.bkit-memory.json --feature "<feature>" --release --session-id "$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"
```

If the id file becomes unreadable, the oracle cannot read the id and returns `cannot_judge`. If an operator deletes or rewrites
the file while its session is live, that session can receive another id or none.

## Memory index

grok keeps its memory under `~/.grok/memory/`. Do not point
`h_mad_check_memory_index.py` at `~/.claude/projects` from a grok session; that
would report a different host's memory store.

## Construct mapping

These mappings cover the current grok host. Each source cites a grok chapter,
`grok inspect`, or a direct observation.

| construct | status | mapping | source |
|---|---|---|---|
| `subagent-call` | mapped | Use `spawn_subagent` with the agent file text in `prompt`. | `16-subagents.md` |
| `skill-call` | mapped | Invoke the skill slash command, such as `/h-mad`. | `08-skills.md` |
| `advisor` | not-applicable | grok has no advisor tool and a child does not inherit the transcript; use `hmad-dispatch exec` for codex\|agy\|grok, or `spawn_subagent` with a self-contained review prompt. | `01-getting-started.md`; `16-subagents.md` |
| `send-message` | not-applicable | `send_subagent_message` is off by default; continue with `spawn_subagent` and `resume_from`. | `16-subagents.md` |
| `hook-event` | mapped | Run Claude hooks from `~/.claude/settings.json` through `compat.claude.hooks`; adapt to camelCase payloads and `exit 2` deny. | `10-hooks.md` |
| `session-id-env` | mapped | `GROK_SESSION_ID` is documented for hook processes; until observed in the orchestrator shell, mint the file id with `uuid.uuid4()` and let the oracle report `owned_elsewhere` when another session owns the claim. | `10-hooks.md` |
| `claude-config-dir` | not-applicable | grok reads `~/.claude/settings.json` at a fixed path; honoring `CLAUDE_CONFIG_DIR` is undocumented. | `10-hooks.md` |
| `claude-md` | mapped | Read `Claude.md`, `CLAUDE.md`, or `AGENTS.md` as project rules. | `12-project-rules.md` |
| `claude-skills-dir` | mapped | Load the skill from `~/.claude/skills` through `compat.claude.skills` and resolve `HMAD_SKILL_ROOT` from its loaded path. | grok inspect |
| `claude-agents-dir` | not-applicable | grok can list `~/.claude/agents` but cannot select an agent by name; place its role text in the prompt. | `16-subagents.md` |
| `claude-hooks-dir` | mapped | Claude hook scripts run from their Claude paths under compatibility mode. | `10-hooks.md` |
| `claude-settings` | mapped | Read `~/.claude/settings.json` hooks through `compat.claude.hooks` for H-MAD. | `10-hooks.md` |
| `claude-handoffs-dir` | mapped | Keep the plain handoff file store that every host reads and writes through its shell. | observed: handoff index file |
| `claude-projects-store` | not-applicable | grok keeps its own store at `~/.grok/memory/`; `h_mad_check_memory_index.py` must not measure Claude projects as grok memory. | `13-memory.md` |
| `claude-home-bare` | not-applicable | grok's own home is `~/.grok`, so Claude's home is not its host root. | `05-configuration.md` |
| `session-reset-command` | mapped | Use `/new` (alias `/clear`) or `/compact` for the documented session actions. | `04-slash-commands.md` |
| `skill-slash-invocation` | mapped | Invoke `/h-mad` or `/handoff` as installed skills. | observed: available_commands in the sibling probe log |

## What does not change

Phase gates, state tokens, evidence requirements, audit cycles, and stop conditions
remain those of `../SKILL.md`. This adapter supplies only grok-specific paths,
hook mechanics, and role plumbing.
