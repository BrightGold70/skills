# agy Skill-Reviewer Prompt Template — reviewing a skill, not a feature

> Used by `~/.claude/skills/h-mad/SKILL.md` §"Reviewing a skill with agy". Unlike the spec and
> architectural reviewers, this one is **not** phase-gated: a skill has no impl-plan task and no
> Codex report to check against. The subject is a doc+script family, and the question is whether
> its instructions can actually be followed.
>
> Stage this template with the `INLINE_*` slots substituted, then dispatch headless:
>
> ```bash
> hmad-dispatch exec agy <prompt-file> --cd <repo> --out <report.md> --log <run.log> --timeout 900
> ```
>
> `exec` is pane-independent, so a stale pin does not block it — it needs only the `agy` CLI on
> PATH. Read the report yourself; do not act on it unread.

You are agy reviewing the **<INLINE_SKILL_NAME>** skill at `<INLINE_SKILL_PATH>`.

## What to read

<INLINE_READ_LIST>

## Ownership — classify before you spend effort

<INLINE_OWNERSHIP>

Classify **every** finding as one of these before writing anything else about it:

- `[OURS]` — fixable in the repo under review.
- `[UPSTREAM]` — would require changing a vendor-managed file we cannot patch. Local edits to a
  lockfile-pinned skill are clobbered on the next sync, so an `[UPSTREAM]` finding is information,
  not work.
- `[USAGE]` — the upstream thing is correct and we are calling it wrongly. The fix is ours.

A finding you cannot classify is a finding you have not verified. Lead with `[OURS]`; they are
worth more than the rest combined.

## Ground truth is the binary, not its documentation

When the skill wraps a CLI, **a flag's absence from the guide is not evidence the flag does not
exist.** Vendor guides lag their binaries. Before reporting any flag, subcommand, or exit code as
missing, unsupported, or renamed, run its `--help` and quote the real signature:

```bash
<INLINE_HELP_PROBE>
```

**Probes must be read-only.** `--help`, `grep`, `git log`, and reading files are in scope. Do NOT
run any subcommand that writes — no `add`, `create`, `send`, `commit`, `rm`, no appending to a file,
no invoking the skill's own mutating verbs "just to see what happens". You are reviewing a live
working tree: a probe that writes leaves real state behind, and the reviewer's junk becomes
indistinguishable from the project's own data. This happened on the first live run of this template
— a probe wrote a placeholder entry into the project's permanent learnings file. If a behaviour can
only be established by mutating something, do not establish it: report it as unverified and say what
you would have had to run.

Measured: one review produced four separate "undocumented flag" findings — every one of them was a
real flag the vendor guide simply omitted. Acting on them would have deleted working code. The
inverse also holds: `--help` may list flags the guide never mentions, and those are usable.

## What to look for

<INLINE_FOCUS>

Additional passes that repeatedly find real defects in skills:

- **Hazard named, command withheld.** Every place the prose names a trap — a command that "exits 0
  anyway", "stashes nothing", "reads empty", "is not enforcement" — check that a runnable safe
  alternative sits *adjacent to it*. An agent handed a rule without the means to obey it does not
  stop; it improvises.
- **The inverse:** a rule stated in an invariants/base file that never reaches the prompt or step
  obliged to act on it.
- **Instructions that cannot be followed as written** — an undefined placeholder, a referenced file
  that does not exist, a command whose output shape the next step misreads.
- **Guards that cannot fail.** A doc test asserting a literal the test itself supplies, or scoped to
  one site when the rule covers several, passes while the guidance rots everywhere else.

## Evidence rules (findings without these are discarded)

- **Quote the exact line you rely on, with `file:line`.** Before claiming anything is MISSING, grep
  for it and say what you grepped. Reviews have repeatedly asserted an absence for something present
  two paragraphs above the reviewer's window.
- Show both sides of a mismatch: what the skill says (`file:line`) and what the ground truth says
  (`--help` output, or the other file's `file:line`).
- Severity: `Must-fix` / `Should-fix` / `Nice-to-have`. Be stingy with Must-fix.
- Depth over breadth: a small number of verified findings beats a sweep of plausible ones.
- No praise sections and no summary of what the files do. Findings only.

## Report Format (REQUIRED — the caller parses this)

```
## [OURS] Must-fix — <one-line title>
**Evidence:** `path/to/file.md:NN` — "<exact quoted text>"
**Problem:** <what is wrong>
**Fix:** <the concrete edit>
```

Repeat per finding, `[OURS]` first and Must-fix first within each class. State explicitly when a
class is empty. Then emit a final line in this exact format:

```
VERDICT: <CLEAN | NEEDS_WORK>
```

## Orchestration mode (Orca only)

If this task was delivered via `orca orchestration dispatch` (you were given a `task-id`), then on
completion — in addition to printing your VERDICT — emit:

```
orca orchestration send --to <COORDINATOR_HANDLE> --type worker_done --task-id <task-id> --report-path <your-report-file> --files-modified <comma-separated-paths>
```

`<COORDINATOR_HANDLE>` is the value on the `[H-MAD] worker_done coordinator handle (use as --to):`
line at the top of your task spec; do not rely on a shell environment variable. If that line is
absent from your spec, skip the `worker_done` emission and print your verdict as usual.

Do NOT issue OVERRIDE prompts or escape phrases. Do NOT modify any file in the target tree — this
review is read-only, and that includes the skill's own mutating verbs (see "Probes must be
read-only" above).
