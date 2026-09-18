# Antigravity (agy) runtime adapter

Use this adapter only when the active host is the Antigravity CLI (`agy`). It overrides
host-specific mechanics in `../SKILL.md`; it does not weaken the handoff protocol.

Everything below is derived from the host's own customization docs and observed tool traces, not
from renaming Claude paths. agy's config root is `~/.gemini/config`, **not** `~/.agy`.

## Resolve the skill package

Set `HANDOFF_SKILL_ROOT` to the installed package containing this reference, resolved from the
loaded skill path — typically `~/.gemini/config/skills/handoff` — never from a user-specific
checkout. All bundled commands then live under `$HANDOFF_SKILL_ROOT/scripts/`. If the package is
incomplete, stop and report the missing path.

Do not use a Claude-specific skill-root variable or home-directory path in agy commands.

## agy tool mapping

- **Task sink: agy has no todo tool.** Its `manage_task` is a *background-task* manager keyed by
  `TaskId` (`Action: "status"`), not a checklist, so it is not a restoration sink and must not be
  used as one. The ladder therefore starts one rung down: write `.omc/notepad.md` when it is
  writable, otherwise return an inline checklist. READ must name the sink it used and must never
  silently skip restoration.
- Read with `view_file`, search with `grep_search` and `find_by_name`, and list with `list_dir` in
  preference to shelling out — agy's own guidance prefers the specific tool over `run_command`.
- Edit handoff and learning files with `replace_file_content` (or `multi_replace_file_content` for
  several edits in one file); use `write_to_file` only for a genuinely new file. Preserve unrelated
  worktree changes.
- For a short required choice, ask one concise prose question and stop; agy has no
  request-user-input tool.
- Delegate only through `define_subagent` / `invoke_subagent` and only for an independent
  verification or delivery the mode actually calls for — never merely to read a file. Cap recursion
  at two levels (F-09), never issue OVERRIDE-style prompts (F-02), and verify any dispatch
  narrative against tool-call traces before believing it (F-10).
- When the source protocol names another skill, invoke the matching installed agy skill if present;
  otherwise perform the bounded step inline. Never invent a skill or silently omit it.

## Mode routing

Modes, ordering and stop conditions are unchanged from `../SKILL.md`. Two host facts bear on them:

- **READ requires a fresh session, and agy has no `/clear`.** The source rule — halt and print the
  clear-and-re-invoke sequence rather than reconciling into a loaded session — is unchanged, but the
  instruction given to the user must name agy's own way of starting a new conversation, not
  `/clear`. Never reconcile into a loaded session because clearing is inconvenient here.
- **WRITE's store is project-local and host-neutral**: `docs/handoffs/` under
  `git rev-parse --show-toplevel`. Keep the canonical main-worktree store, branch-qualified
  filename, `Supersedes` chain, carry-forward rules, preflight, scoped commit, sync, push and
  post-push verification exactly as written. Orca checkpointing remains best-effort.
- **LEARN** writes through `scripts/learn.py` to the project-local learnings file; nothing about it
  is host-specific. agy has no per-project auto-memory store (`~/.gemini/config/projects/` holds
  flat JSON records), so do not attempt to mirror a lesson into one, and do not write into
  `~/.claude/projects` — that is a different host's store.

## Safety invariants

Keep the source fail-closed rules: never choose a different branch's newest handoff without user
confirmation; never repair ambiguous divergence; never claim or release anonymously; never stage
the whole repository for a scoped handoff commit; and never report delivery, takeover, push, or
restoration without checking the observable result.

Because agy has no filesystem jail (P-10/P-11), `.geminiignore` protects nothing: never name a
sensitive path in a prompt, and diff `git status --short` — tracked **and** untracked — after every
delegated dispatch.
