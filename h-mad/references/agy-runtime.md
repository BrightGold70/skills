# Antigravity (agy) runtime adapter

Use this adapter only when the active host is the Antigravity CLI (`agy`). It overrides
host-specific mechanics in `../SKILL.md`; it does not change H-MAD's gates or evidence contract.

Everything below is derived from the host's own documentation
(`~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs/hooks.md`) and from observed
tool traces, not from renaming Claude paths. The distinction matters: agy's config root is
`~/.gemini/config`, **not** `~/.agy`, and its hook file is neither shaped nor named like Claude's.

## Package and project roots

agy discovers global customizations under `~/.gemini/config/` and workspace ones under `.agents/`
(walking up to the repository root). Set `HMAD_SKILL_ROOT` to the installed package containing this
reference, resolved from the loaded skill path — the operator-installed link
`~/.gemini/config/skills/h-mad` (§Install below), when it exists. Run scripts as `python3 "$HMAD_SKILL_ROOT/scripts/<script>.py"`
and the dispatcher as `"$HMAD_SKILL_ROOT/bin/hmad-dispatch"`. Never derive the package from a
user-specific checkout.

The project root is `git rev-parse --show-toplevel`. Project state and invariants remain
`docs/.bkit-memory.json` and `.h-mad/invariants.md` beneath that root, unchanged.

`scripts/h_mad_install_check.py` validates the **Claude** install shape (a symlink at
`~/.claude/skills/h-mad` plus the TDD-gate hook link) and will report `SKILL_NOT_INSTALLED` under
agy even when the package is correctly mounted. Do not run it as a gate here, and do not "fix" it
by repointing it at a `~/.agy` path — no such directory exists. Validate instead that
`$HMAD_SKILL_ROOT` contains `SKILL.md`, `scripts/`, `references/`, `hooks/`, and `agents/`.
Pass `--agy-skills-dir ~/.gemini/config/skills` to check this host's own installed skill root;
the host-specific command is in §Install.

## Hooks

Hooks live in `hooks.json` in a customization root — `~/.gemini/config/hooks.json` globally, or
`.agents/hooks.json` for a project. Three differences from Claude Code's `settings.json` are
load-bearing:

1. **Each top-level key is a hook NAME**, not an event. Events nest one level in, so entries from
   different names merge per event rather than colliding. A Claude-shaped `{"hooks": {...}}` block
   pasted here is silently inert.
2. **The event vocabulary is `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`,
   `Stop`.** There is **no `SessionStart`**. `PreInvocation` is the nearest thing and fires before
   *every* model call, not once per session — so a once-per-session advisory cannot be expressed
   faithfully, and must either become idempotent or be dropped rather than fired every turn.
3. **`matcher` targets agy tool names**, not Claude's `Write|Edit`. Observed write-capable tools
   are `write_to_file`, `replace_file_content`, `multi_replace_file_content`, and `run_command`
   (a shell can write anything). `PreToolUse`/`PostToolUse` wrap handlers in a `matcher` + `hooks`
   group; `PreInvocation`, `PostInvocation` and `Stop` take a flat handler list.

A handler runs via `sh -c` with its working directory set to the directory containing `hooks.json`,
receives a **camelCase** JSON payload on stdin, and must print a JSON object on stdout. For
`PreToolUse` that object carries `decision`: `"allow"`, `"deny"`, `"ask"`, or `"force_ask"`, with an
optional `reason` shown to the user and agent.

## The TDD gate

`hooks/h-mad-tdd-gate.sh` uses Claude Code's `permissionDecision` JSON deny on rc 0;
`hooks/h-mad-codex-tdd-gate.py` uses Codex's hook contract. **Neither speaks agy's stdout-JSON contract**, so
wiring either one here produces a hook that runs, emits nothing agy understands, and blocks
nothing. An agy gate must read the `toolCall.name`/`toolCall.args` payload and emit
`{"decision": "deny", "reason": "..."}` to refuse a production-code write during active `step5`,
matching on the four tools above.

Until such a gate exists and has been verified against a real refusal, **halt with
`step5:agy_tdd_hook_unverified`** rather than claiming mechanical enforcement. An unverified gate
is the one failure mode that makes a RED phase indistinguishable from a passing one.

## Author and reviewer roles

There is no `~/.gemini/config/agents/<name>.md`; agy has no file-based agent registry. Roles map to
its subagent tools — `define_subagent`, `invoke_subagent`, `manage_subagents` — so the author and
reviewer separation `../SKILL.md` requires is carried by distinct subagent definitions rather than
by distinct agent files. The project's `AGENTS.md` risk register applies in full: never issue
OVERRIDE-style prompts (F-02 fabrication), cap subagent recursion at two levels (F-09 quota
exhaustion), and verify a parallel-dispatch narrative against tool-call traces before believing it
(F-10 claim-execution divergence).

Because agy has no filesystem jail (P-10/P-11), prompt discipline is the only boundary: never name
a sensitive path in a prompt to agy, and diff `git status --short` — tracked **and** untracked —
after every dispatch.

## Memory index

The auto-memory index guard has nothing to check here. agy stores project records as flat JSON
under `~/.gemini/config/projects/*.json`; there is no per-project `memory/MEMORY.md` store, so
`scripts/h_mad_check_memory_index.py` correctly reports that none exists. Do not repoint it at
`~/.claude/projects` — that is a different host's store, and measuring it from agy would report
another host's caps as this one's.

## Install

Link both skills from the checkout into agy's skill directory:

```bash
ln -s /path/to/checkout/h-mad ~/.gemini/config/skills/h-mad
ln -s /path/to/checkout/handoff ~/.gemini/config/skills/handoff
```

For either link, an existing non-symlink at either path is an operator decision and is never overwritten.

Check the installed links with:

```bash
python3 "$HMAD_SKILL_ROOT/scripts/h_mad_install_check.py" --agy-skills-dir ~/.gemini/config/skills
```

## Context budget and claims

Use the explicit host flag for the budget and resume oracle. Replace `<HMAD_SKILL_ROOT>` with the literal absolute path of the resolved skill root before running: the codex TDD gate accepts only a literal absolute script path (it rejects `$` and `~`), and a checkout path must never be written into this file. The budget check is:

```bash
python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_context_budget.py" --host agy
```

`CTXBUDGET: UNKNOWN reason=host_unsupported` is expected, not an `OK` verdict. The
80% run ceiling is unenforced on agy; substitute: none. There is no context indicator
the orchestrator can read from this host.

agy has no documented session-id environment variable. Mint an id once at bootstrap
in the checkout's git directory, per feature. A second mint prints `SID: NOT_MINTED`:
the existing file belongs to another or earlier session, so halt for the operator. It is
never deleted or reused without the operator. Each subsequent command reads the id from
that file in its own shell invocation. Keep `<feature>` literal here and replace it with
the active feature name when executing these lines. The resume oracle decides the route
before any state write; use `--create --claim` only for its `start_fresh` verdict.

```bash
( set -C; python3 -c 'import uuid; print(uuid.uuid4())' > "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>" ) && echo "SID: MINTED" || echo "SID: NOT_MINTED"
python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_resume_decision.py" --host agy --state docs/.bkit-memory.json --feature "<feature>" --session-id-from-git-dir
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

The status and mapping below apply to the agy host. Sources identify the observations
and design references behind each mapping.

| construct | status | mapping | source |
|---|---|---|---|
| `subagent-call` | mapped | Use `define_subagent`, then `invoke_subagent` with the agent role and task. | Observed agy `init.tools` in `plan-audit-v1-p2-agy.log`. |
| `skill-call` | mapped | Load the installed agy skill under `~/.gemini/config/skills`. | agy `skills.md`. |
| `advisor` | not-applicable | agy has no advisor tool; use `hmad-dispatch exec` for codex\|grok, or `define_subagent` and `invoke_subagent` with review context in the prompt. | Observed agy tools; design D9.3. |
| `send-message` | not-applicable | `send_message` target semantics are undocumented; dispatch a fresh author with the previous report path. | Observed agy tools; design D9.3. |
| `hook-event` | mapped | Use `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, and `Stop`; there is no `SessionStart`. | agy `hooks.md`. |
| `session-id-env` | not-applicable | agy has no documented session id variable; mint the file id with `uuid.uuid4()` and pass it to the oracle, which may return `owned_elsewhere`. | F13; FR-9 minted-id procedure. |
| `claude-config-dir` | not-applicable | Claude's settings scope does not apply because agy's config root is `~/.gemini/config`. | agy `hooks.md`. |
| `claude-md` | mapped | Read workspace rules from `.agents/`. | agy `rules.md`. |
| `claude-skills-dir` | mapped | Resolve `$HMAD_SKILL_ROOT` from the loaded skill path under `~/.gemini/config/skills/h-mad`. | agy `skills.md`. |
| `claude-agents-dir` | not-applicable | agy has no file-based agent registry; define the role with `define_subagent`. | Observed agy tools. |
| `claude-hooks-dir` | not-applicable | agy hooks are configured in `hooks.json`, not in Claude's hook directory. | agy `hooks.md`. |
| `claude-settings` | not-applicable | agy does not read Claude's settings file; its global hooks live in `~/.gemini/config/hooks.json`. | agy `hooks.md`. |
| `claude-handoffs-dir` | mapped | Keep the plain handoff file store that every host reads and writes through its shell. | Observed handoff index file. |
| `claude-projects-store` | not-applicable | agy keeps project records under `~/.gemini/config/projects/*.json`, so Claude's project store is the wrong memory index. | Observed agy project records. |
| `claude-home-bare` | not-applicable | Claude's home is a different root; agy's configuration lives under `~/.gemini/config`. | agy `hooks.md`. |
| `session-reset-command` | not-applicable | agy has no documented reset command; start a fresh `agy` session. | agy documentation directory; design D9.3. |
| `skill-slash-invocation` | mapped | Invoke the installed agy skill by name. | agy `skills.md`. |

## What does not change

Phase gates, state tokens, evidence requirements, audit cycles and stop conditions are identical
across hosts. Only paths, hook mechanics, and role plumbing are overridden here.
