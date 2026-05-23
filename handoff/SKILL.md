---
name: handoff
description: Use this skill in three modes. WRITE mode — create a session handoff document, end-of-session summary, session closeout, wrap-up doc, or notes for the next session — produces a project-local markdown handoff at docs/handoffs/YYYY-MM-DD-<slug>.md capturing session summary, key learnings, next steps, open/blocked items, and resume context, aimed at future-you opening a fresh Claude Code session. READ mode — resume work after /clear or at the start of a fresh session by loading the most recent handoff, reconciling its state with the working tree, and restoring the TodoList. LEARN mode — record a single durable cross-session learning to <project>/docs/learnings.md via the bundled scripts/learn.py (no external skill or plugin dependency); also exposes a search command for grep-style retrieval across past learnings. Invoke for WRITE whenever the user says /handoff, "handoff", "session summary", "wrap up session", "close out session", "document what we did", "leave notes for next time"; invoke for READ whenever the user says "read handoff", "/handoff resume", "load handoff", "resume from handoff", "where did we leave off", "pick up where we left off", "continue from last session", or any variant about loading prior session state — especially right after /clear; invoke for LEARN whenever the user says "save this learning", "remember this for next time", "log this gotcha", "capture this pattern", "add to learnings", "this is a recurring issue, save it", "what learnings do we have on X", "search past learnings for Y", or any variant about recording or retrieving durable cross-session knowledge outside a full handoff. Use this skill whether or not the exact word "handoff" appears, and prefer LEARN mode for single-shot lesson capture, READ mode when phrasing is about *picking up* prior state, and WRITE mode when *closing out* a session.
---

# Handoff

## Mode routing — decide first

Before doing anything else, identify which mode applies:

| Phrase / context | Mode |
|---|---|
| `/handoff`, "wrap up", "session summary", "close out", "document what we did", "leave notes" | **WRITE** |
| "read handoff", "resume", "where did we leave off", "pick up where we left off", "continue from last session", invoked right after `/clear` | **READ** |
| "save this learning", "remember this", "log this gotcha", "capture this pattern", "add to learnings", "search past learnings" | **LEARN** |

If ambiguous, default to **WRITE** for session-end invocations and **READ** for session-start ones.

---

## WRITE mode flags

Parse flags from the invocation before doing anything else. Flags apply only to WRITE mode.

| Flag | Default | Effect |
|---|---|---|
| `--dry-run` | off | Draft the doc and print to stdout; do not save, commit, or run scout. Stop after drafting. |
| `--skip-scout` | off | Skip the automation-scout phase entirely. |
| `--skip-learnings` | off | Skip the "Persist durable learnings" phase. |

---

## Reading a handoff (resume mode)

### Step 1: Locate the doc

Check, in order:

1. **Explicit path in the user's message** — if they paste or type a path, use it.
2. **`docs/handoffs/` in the current project** — list files, sort by name (ISO date prefix), take the newest. Confirm with the user if there are multiple candidates with different slugs.
3. **`~/.claude/handoffs/INDEX.md`** — grep for the current project name / path; take the newest matching entry's path.

If no handoff is found after these checks, tell the user ("No handoff found for this project — nothing to resume from") and stop. Don't fabricate a handoff.

### Step 2: Read it

Read the handoff file in full. Do not summarize or paraphrase — internalize it. The relevant sections are:
- **Session Summary** — what was in flight
- **Next Steps** — the ordered action queue
- **Open / Blocked Items** — unresolved state
- **In-Flight Processes** — any live PIDs or background jobs
- **Context for Next Session** — branch, files, resume commands

### Step 3: Reconcile with reality (silent verification)

The doc is a snapshot; the world has moved on. Run a quick reconciliation pass and surface only the divergences. Don't narrate the checks themselves.

In parallel:

- `git rev-parse --abbrev-ref HEAD` — does the current branch match the doc's "Branch" field?
- `git status --short` — does the working-tree state match the doc's "Uncommitted changes" claim? (Doc says "none" but tree is dirty → flag. Doc lists specific files but tree is clean → flag, the work was probably committed since.)
- For each file path cited in Next Steps and Files Touched, check existence. If a path no longer exists (renamed/moved/deleted), flag it — that Next Step needs adjusting before the user picks it up.
- `git log --oneline -5` — has anything new landed since the handoff was written? If the doc references commits that aren't in `git log`, the branch may have been rebased; mention it.
- **In-flight processes** — for each PID cited in In-Flight Processes / Open Items / Next Steps, run `ps -p <PID> -o pid,etime,stat`. For each cited log path, `ls -la <log>` to read size + mtime. Surface one of: "still running, N min elapsed (matches handoff trajectory)" / "exited" / "log unchanged for N hours — likely dead, treat as historical". This is the single most load-bearing reconciliation when the handoff hands off live work; never skip it. If the doc is days old, treat all in-flight claims as historical without bothering to check `ps` (the PID has been recycled and reporting on a stranger's process is worse than silence).
- **Worktree split** — if the handoff path is inside `.claude/worktrees/<name>/`, the doc was written from a worktree. Run `git -C <worktree-root> rev-parse --abbrev-ref HEAD` AND `git -C <parent-repo> rev-parse --abbrev-ref HEAD` — both trees have independent state and both matter. The handoff's "Branch:" field usually refers to the *worktree*; the parent repo may be on a deferred-cleanup branch (the handoff often calls this out). State each tree's branch on its own divergence line if they disagree with the doc.

A divergence is not a failure — it's just information the user needs before acting. State each one as a single sentence.

### Step 4: Restore the TodoList

Use the TodoList tool (TaskCreate or equivalent) to repopulate todos from the doc's **Next Steps** and **Open / Blocked Items**. Each Next Step becomes a `pending` task with the cited path/command in the description. Each Open/Blocked Item becomes a `pending` task tagged with its blocker if any. Do this even if Next Steps is short — the point is that the user can start on item 1 without re-typing the list.

If the doc's Next Steps reference a file that the reconciliation pass flagged as missing or moved, mark that task with an inline note (e.g., "[verify path — file moved since handoff]") rather than dropping it.

**Dedupe overlapping items.** It's normal for an in-flight piece of work to appear in both Next Steps ("monitor PID N") and Open Items ("PID N still running") — same thing, two framings. Make one Todo, not two. Same for "verify the 14 placeholder dates" appearing in both lists. Combine the descriptions and merge.

### Step 5: Report back and stop

After reconciliation and TodoList restore, give the user a brief resume report:

```
## Session resumed

**Handoff:** docs/handoffs/2026-04-30-lightrag-guideline-rag.md
**Branch:** main (matches)
**Uncommitted changes:** 2 files (matches handoff)

**Divergences:**
- PID 37219 (compile_guidelines_db): exited — log mtime 3h ago. Treat as complete; verify output.
- `protocol/sections/background.md` cited in Next Steps — file not found (may have been renamed).

**Todos restored:** 4 items. Starting at:
1. Verify compile_guidelines_db output (`yq '.documents | length' MANIFEST.yaml` ≥ 55)
```

Then stop. Don't start executing tasks — the user reads the report and decides what to do first.

### Read-mode don'ts

- Don't rewrite or update the handoff doc in read mode — it's a historical record.
- Don't run tests or builds as part of reconciliation.
- Don't assume the in-flight process is still running if the doc is >4h old.

---

## LEARN mode — single-shot durable learning

Capture a single non-obvious finding, pattern, or gotcha so it survives future `/clear` calls and new sessions. This is lighter than a full handoff — one learning, one command, done.

### Step 1: Distill the kernel

From the user's description (or the conversation context if they invoked LEARN without a message), extract:

- The **pattern** — a ≤200-character statement of the reusable finding. It should read like a fact, not a story ("qwen3-embedding NaN's on long inputs — substitute random unit vector, not zero vector; L2-norm poisons downstream embeddings").
- The **category**: `gotcha` (failure pattern with diagnostic value) / `solution` (working fix that codifies a pattern) / `pattern` (architectural shape worth remembering).
- **Tags**: comma-separated lowercase. Include `handoff:<date>-<slug>` if a handoff was written this session; `session:<date>` otherwise. Add domain tags to make future grep searches find it.

If the user gave enough detail to fill all three, skip to Step 3. If not, ask one clarifying question (category or the exact pattern — whichever is ambiguous).

### Step 2: Pick category + tags

- **Category** is one of `gotcha` / `solution` / `pattern` (script enforces):
  - `gotcha` — failure pattern with reusable diagnostic value ("X reproduces deterministically when Y; misdiagnosed as Z")
  - `solution` — working fix that codifies a pattern ("use singleton + reload on NaN" — the pattern, not "fixed today")
  - `pattern` — architectural shape worth remembering ("OrderedDict + popitem(last=False) for LRU eviction")
- **Tags** are comma-separated, lowercase, hyphenated. Convention: include
  `handoff:<date>-<slug>` to cross-reference the originating session's
  handoff doc if one exists; use `session:<date>` if no handoff was written.
  Add domain tags (`lightrag`, `auth`, `migrations`, etc.) to make future
  topical searches grep-friendly.

### Step 3: Invoke the bundled script

```bash
# Capture
python "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/learn.py" add \
  "<≤200-char kernel>" \
  --category gotcha|solution|pattern \
  --tags "domain1,domain2,handoff:2026-04-30-foo"

# Search
python "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/learn.py" search "<term>"
```

Same-day exact-pattern duplicates are silently skipped (idempotent — safe
to re-invoke). The script writes to `<project>/docs/learnings.md` (newest
on top, one line per entry, tags backtick-quoted for grep cleanliness).

### Step 4: Report and stop

```
Learning saved to docs/learnings.md:
  2026-04-30 · gotcha · `lightrag,nan-embed` — qwen3-embedding NaN's on long inputs; substitute random unit vector not zero (L2-norm poisons)
```

Then stop — this is a single-shot operation, not a gateway to more work.

### LEARN-mode don'ts

- Don't write learnings inline into the handoff doc (that's WRITE mode's job with the "Persist durable learnings" step — LEARN mode writes *only* to `docs/learnings.md`).
- Don't add more than one learning per LEARN invocation — if the user has several, tell them and invoke LEARN once per learning.
- Don't pad the kernel past 200 characters to sound thorough — shorter is better.

---

## Audience

Write as if future-you is the reader: someone who knows the project deeply but has zero memory of this specific session. They've just typed `/clear`, opened a new Claude Code window, and are about to ask "where were we?". The handoff is their only briefing.

---

## Where to save

### Filename rules

```
docs/handoffs/YYYY-MM-DD-<slug>.md
```

- `YYYY-MM-DD` — today's date in ISO format (use `date +%Y-%m-%d` if unsure).
- `<slug>` — 2–4 lowercase words from the session's main topic, hyphenated. Derive from the feature name, PDCA feature slug, or issue/ticket if one exists.
- Examples: `2026-04-30-lightrag-guideline-rag.md`, `2026-05-01-protocol-daemon-fix.md`

### Project slug derivation

The `<project-slug>` field in the INDEX.md entry should match the project's canonical name:
- If a `hpw`/`csa`/similar CLI name exists — use it.
- Otherwise use the git repo name (last segment of `git remote get-url origin`, minus `.git`).
- Fall back to the directory name if no remote.

### Update the central index

After writing the handoff file, append (prepend, technically — newest first) a one-line entry to `~/.claude/handoffs/INDEX.md`. This is the **only** thing in `~/.claude/handoffs/`; the directory exists solely to host this file.

Format — newest entries at the top:

```
- 2026-04-28 · HemaSuite/guideline-category-facet · Shipped guideline-category-facet end-to-end via TDD multi-agent cowork · `/Users/kimhawk/Coding/HemaSuite/docs/handoffs/2026-04-28-guideline-category-facet.md`
```

Each entry has four pipe-free segments separated by `·`: ISO date, `<project-slug>/<handoff-slug>`, a one-line summary lifted from the doc's Session Summary (≤100 chars), and the absolute path in backticks. Use absolute paths (not `~/`) so a `grep` is unambiguous.

Create the file with a `# Handoffs Index\n\nNewest first. Format: ISO date · project/slug · summary · path\n\n` header block if missing. Don't commit `~/.claude/handoffs/INDEX.md` to any project repo — it's user-global state, not project state.

The reason this matters: project-local handoffs are great for versioning and PRs but bad for "what did I work on across all my projects last month" — the index is what makes that question answerable in one command (`head ~/.claude/handoffs/INDEX.md` for recent, `grep <topic> ~/.claude/handoffs/INDEX.md` for search).

---

## Gather context before drafting

Before you write anything, collect these in parallel:

1. **Conversation scan** — walk the current transcript. Note: the task the user brought, decisions made, problems hit, what got fixed, what's still broken, any verification that was skipped.
2. **In-flight tasks** — if you have a TodoList / task tool, read it. Anything pending or in-progress belongs in Open Items. Anything completed this session feeds Session Summary.
3. **Git state** — if the project is a git repo:
   - `git rev-parse --abbrev-ref HEAD` (current branch)
   - `git status --short` (uncommitted / untracked)
   - `git log --oneline -10` (recent commits for context)
   - `git diff --stat` (scope of unstaged changes)

   If not a git repo, skip silently — don't mention it.
4. **Plan backlog state** — if the project keeps plan docs in a structured directory (common patterns: `docs/01-plan/features/*.plan.md`, `docs/plans/`, `specs/`), do a fast scan to surface what's still unimplemented:
   - List the plan files and `grep` their frontmatter for `status:` (Draft / Deferred / In-progress / Complete) and `gate:` / `blocked_by:`.
   - Check whether each plan has a corresponding `docs/04-report/features/<name>.report.md` (or equivalent). A plan without a report is a candidate "unimplemented" entry; cross-check the codebase or session for evidence it actually shipped before flagging.
   - Skip silently if the project has no such structure. Don't fabricate one. The point is to surface backlog signal that already exists, not invent a tracking system.
5. **Live processes** — if the session launched any long-running background work that's still alive at the moment of writing (multi-hour ingests, soak tests, build pipelines, daemons started for testing): capture PID, the exact command (one line), the log path, started-at, elapsed, and a one-line "what to verify on exit". This populates the **In-Flight Processes** section. Skip silently if nothing is in flight — most sessions don't have any. The check costs nothing (`ps -p $! -o pid,etime` for each backgrounded job, or `pgrep -f <substring>` for processes the operator launched manually) and the value to a future resume is enormous: without it, the next session has to reverse-engineer "is this still going?" from log mtimes and ambiguous output.
6. **Worktree state** — if `git rev-parse --show-toplevel` returns a path containing `.claude/worktrees/<name>/`, the session ran in a worktree. Also capture the parent repo's branch (`git -C <parent> rev-parse --abbrev-ref HEAD`) so the handoff names both. The worktree's "to resume" `cd` should point at the worktree root, not the parent.
7. **Session observations** — if `~/.claude/homunculus/observations.jsonl` exists, read the last 50 lines. These structured observations often surface gotchas not explicit in the conversation. Use them to enrich Key Learnings extraction. Skip silently if absent.
   ```bash
   OBS_FILE="$HOME/.claude/homunculus/observations.jsonl"
   [ -f "$OBS_FILE" ] && tail -50 "$OBS_FILE"
   ```
8. **Proactive follow-ups** — after scanning plan backlog (item 4), look for plan items with `status: Draft` or `status: In-progress` that were NOT mentioned in the session. Append them to Next Steps as `[suggested]` items — concrete (cite the plan file path), brief, ≤3 items. The goal is a warm start for the next session, not a backlog dump. Skip if no plan structure exists.

Do **not** run tests, builds, or long-running commands just to populate the handoff. Use what was already observed in the session. If something wasn't verified, the handoff should say so — that's load-bearing information.

---

## Required template

Use this structure exactly. Every section is required; write "None" (with a one-line reason) rather than omitting a header.

```markdown
# Handoff — <Topic>

**Date:** YYYY-MM-DD
**Branch:** <branch-name or "n/a">
**Project:** <project name or root path>

## Session Summary

<2–5 sentences. What was worked on, what was the goal, what's the outcome (done / partial / blocked). No play-by-play — a future reader should know in 15 seconds whether to pick this up.>

## Key Learnings

<Non-obvious findings from this session — gotchas, surprising behavior, decisions made and why, dead ends ruled out. Each item 1–2 sentences. Skip anything a fresh reader could derive from the code or git log. If nothing non-obvious came up, write "None worth recording" — don't pad.>

- <learning 1>
- <learning 2>

## Next Steps

<Concrete, ordered actions. Each cites a file path (with line number when meaningful) or an exact command. Future-you should be able to pick item 1 and start immediately, not plan.>

1. <action> — `path/to/file.ts:42`
2. <action> — run `pnpm test packages/foo`

## Open / Blocked Items

<What's unfinished and why. Distinguish "not yet done" from "blocked on X" — name the blocker explicitly.>

- <item> — status: in progress | blocked on <reason> | deferred

## In-Flight Processes

<Include this section ONLY when the session is handing off long-running work that's still alive at the moment of writing — a multi-hour ingest, a soak/burn-in test, a build pipeline, a streaming job. Omit entirely otherwise.>

| PID | Command | Log | Started | Elapsed @ handoff | ETA | What to check on exit |
|---|---|---|---|---|---|---|
| 37219 | `nohup python -m scripts.foo --batch ...` | `/tmp/foo.log` | 11:29 | 2h 16m | ~3-4h more | `grep errors= /tmp/foo.log == 0` |

## Context for Next Session

**Files touched this session:**
- `path/to/file.ts`
- `path/to/other.ts`

**Worktree** (include only if the session ran in a git worktree, not the parent repo):
- Worktree root: `<repo>/.claude/worktrees/<name>/` — branch: `<branch>`
- Parent repo: `<repo>/` — branch: `<branch>`

**Uncommitted changes:** <one-line summary from `git status`, or "none">

**To resume:**
\`\`\`bash
cd <project root>
git checkout <branch>
# env setup, server start, etc.
\`\`\`

**Related docs:**
- <links to design docs, plan files, or external references the next session will need>
```

---

## Writing guidance

- **Session Summary**: 2–5 sentences max. Outcome-first (done/partial/blocked). No narrative.
- **Key Learnings**: non-obvious only. If a fresh reader could derive it from the code or git log, omit it.
- **Next Steps**: concrete + ordered. Each item must have a file path or a command. Vague actions ("look at the auth module") are not Next Steps.
- **Open / Blocked Items**: name blockers explicitly. "Blocked on X" is useful. "In progress" alone is not.
- **In-Flight Processes**: omit if nothing is alive. If present, every row needs all seven columns.
- **Context for Next Session**: the resume command should work. Test it mentally — if a future session ran exactly those commands in that order, would they be in the right state?

---

## After writing

If `--dry-run` was set: print the drafted doc to stdout and **stop here**. Do not save, commit, or run scout.

1. Save the file to `docs/handoffs/YYYY-MM-DD-<slug>.md` in the project root.
2. Update `~/.claude/handoffs/INDEX.md` (one-line entry, newest first — see §"Update the central index").
3. Proceed to §"Persist durable learnings" if Key Learnings is non-empty and `--skip-learnings` was not set.
4. Proceed to §"Automation scout" unless `--skip-scout` was set.
5. Proceed to §"Commit and push".

---

## Persist durable learnings to `docs/learnings.md`

After the handoff doc is saved, extract learnings that should survive future sessions — not in the handoff (which is ephemeral session context), but in the project's `docs/learnings.md` (which is a permanent, grepped, living record).

**What to extract**: any item from Key Learnings that is:
- A reusable pattern (applies next time this kind of work comes up)
- A non-obvious gotcha (would a fresh Claude session make the same mistake?)
- A stable architectural decision (why something was done a certain way)

**What to skip**: items that are session-specific ("we decided to defer X"), already in the code/docs ("see CLAUDE.md §F-12"), or too vague to be actionable.

For each qualifying learning:

```bash
python "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/learn.py" add \
  "<≤200-char kernel>" \
  --category gotcha|solution|pattern \
  --tags "domain1,domain2,handoff:YYYY-MM-DD-<slug>"
```

Always include `handoff:<date>-<slug>` as a tag so the learning is cross-referenced to this session.

---

## Automation scout

Scan this session's work for repeated patterns worth capturing as skills. Runs after learnings are persisted, before committing. Skip entirely if `--skip-scout` was set.

### How to run

Run this analysis inline (no external agent or plugin required). If a read-only subagent is available, spawn one for isolation — but the inline path is the default.

Review `git diff HEAD~10..HEAD` and the conversation. Find: command pipelines the user retyped multiple times, multi-step workflows done manually without a shortcut, patterns that recurred ≥2 times, or any sequence that felt like "there should be a skill for this." For each candidate: pattern name, recurrence count, one-line description. Cap at 5 candidates.

### Where to write

Append to `docs/skill-candidates.md` (create with `# Skill Candidates` header if absent):

```markdown
## YYYY-MM-DD — <session-slug>

- **<pattern>**: <description> — recurrence: N — candidate: yes/maybe/no
```

If zero candidates found, write: `## YYYY-MM-DD — <slug> — no candidates`.

---

## Commit and push (default finale)

After the handoff doc is written and learnings are persisted, commit and push unless the user explicitly says not to.

### Pre-flight (run before staging)

```bash
git status --short          # confirm only handoff + learnings files are staged
git diff --stat HEAD        # sanity-check scope
```

### Commit

```bash
git add docs/handoffs/YYYY-MM-DD-<slug>.md docs/learnings.md
git add docs/skill-candidates.md 2>/dev/null || true   # only if scout ran
git commit -m "chore(handoff): YYYY-MM-DD <slug>

Session closeout: <one-line summary from Session Summary>."
```

Do not use `git add -A` — only stage the handoff and learnings files.

### Push

```bash
git push origin HEAD
```

### Verify

```bash
git log --oneline -3    # confirm commit landed
```

### Don't

- Don't amend or force-push.
- Don't stage unrelated changes that were open before the handoff.
- Don't push if the user said "don't commit" or the repo is in a detached HEAD state.
