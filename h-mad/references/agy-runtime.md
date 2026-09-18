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
reference, resolved from the loaded skill path — typically
`~/.gemini/config/skills/h-mad`. Run scripts as `python3 "$HMAD_SKILL_ROOT/scripts/<script>.py"`
and the dispatcher as `"$HMAD_SKILL_ROOT/bin/hmad-dispatch"`. Never derive the package from a
user-specific checkout.

The project root is `git rev-parse --show-toplevel`. Project state and invariants remain
`docs/.bkit-memory.json` and `.h-mad/invariants.md` beneath that root, unchanged.

`scripts/h_mad_install_check.py` validates the **Claude** install shape (a symlink at
`~/.claude/skills/h-mad` plus the TDD-gate hook link) and will report `SKILL_NOT_INSTALLED` under
agy even when the package is correctly mounted. Do not run it as a gate here, and do not "fix" it
by repointing it at a `~/.agy` path — no such directory exists. Validate instead that
`$HMAD_SKILL_ROOT` contains `SKILL.md`, `scripts/`, `references/`, `hooks/`, and `agents/`.

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

`hooks/h-mad-tdd-gate.sh` is written to Claude Code's exit-code protocol and
`hooks/h-mad-codex-tdd-gate.py` to Codex's; **neither speaks agy's stdout-JSON contract**, so
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

## What does not change

Phase gates, state tokens, evidence requirements, audit cycles and stop conditions are identical
across hosts. Only paths, hook mechanics, and role plumbing are overridden here.
