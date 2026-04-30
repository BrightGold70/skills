---
name: handoff
description: Use this skill in three modes. WRITE mode — create a session handoff document, end-of-session summary, session closeout, wrap-up doc, or notes for the next session — produces a project-local markdown handoff at docs/handoffs/YYYY-MM-DD-<slug>.md capturing session summary, key learnings, next steps, open/blocked items, and resume context, aimed at future-you opening a fresh Claude Code session. READ mode — resume work after /clear or at the start of a fresh session by loading the most recent handoff, reconciling its state with the working tree, and restoring the TodoList. LEARN mode — record a single durable cross-session learning to <project>/docs/learnings.md via the bundled scripts/learn.py (no external skill or plugin dependency); also exposes a search command for grep-style retrieval across past learnings. Invoke for WRITE whenever the user says /handoff, "handoff", "session summary", "wrap up session", "close out session", "document what we did", "leave notes for next time"; invoke for READ whenever the user says "read handoff", "/handoff resume", "load handoff", "resume from handoff", "where did we leave off", "pick up where we left off", "continue from last session", or any variant about loading prior session state — especially right after /clear; invoke for LEARN whenever the user says "save this learning", "remember this for next time", "log this gotcha", "capture this pattern", "add to learnings", "this is a recurring issue, save it", "what learnings do we have on X", "search past learnings for Y", or any variant about recording or retrieving durable cross-session knowledge outside a full handoff. Use this skill whether or not the exact word "handoff" appears, and prefer LEARN mode for single-shot lesson capture, READ mode when phrasing is about *picking up* prior state, and WRITE mode when *closing out* a session.
---

# Handoff

A handoff is the bridge between two sessions: WRITE the doc when ending a session, READ it when starting the next one. Both modes live in this skill because they share the same artifact and the same goal — a clean, fast resume.

## Mode routing — decide first

Before doing anything else, decide which mode applies:

- **WRITE** if the user is closing out, summarizing, wrapping up, or invoking `/handoff` plain. Skip to **§ Audience** and follow the write-mode flow through to "Commit and push".
- **READ** if the user is loading, resuming, or asking where you left off — especially the first message after `/clear`. Follow **§ Reading a handoff (resume mode)** below and STOP at the report-back step. Do **not** fall through into write mode, and do **not** run the "Commit and push" finale (that's write-mode only).
- **LEARN** if the user wants to record OR retrieve a single durable cross-session learning *outside* a full handoff context — phrases like "save this learning", "remember this for next time", "log this gotcha", "search past learnings for X". Jump to **§ LEARN mode — single-shot durable learning** below and STOP after the script invocation. Do **not** write a handoff doc, do **not** run "Commit and push" — LEARN is a one-shot append/query against `docs/learnings.md`, no doc artifact and no automated commit.

If genuinely ambiguous (rare — usually phrasing is clear), ask one short question: "Read the latest handoff, create a new one, or just log/search a learning?" Don't guess and don't do more than one mode.

---

## Reading a handoff (resume mode)

Goal: in 3–5 tool calls, restore enough state that the user can pick item 1 from "Next Steps" and start. No transcript replay, no preamble.

### Step 1: Locate the doc

If the user is in a clear project context (CWD is inside a project), search **project-local** first; the index is a secondary lookup for cross-project queries.

```bash
ls -1 <project>/docs/handoffs/ 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}-' | sort | tail -1
```

Pick the **newest by ISO date in filename** (filenames are `YYYY-MM-DD-<slug>.md` so a lexicographic sort works). If multiple files share the newest date, take the last alphabetically — that's the latest `-2`/`-3` suffix from same-day handoffs. Auto-pick without asking; the user can always say "use the previous one".

**Use the index** (`~/.claude/handoffs/INDEX.md`) when:

- The user asks generically ("read my latest handoff", "where was I last working") without naming a project — the first line of the index is the answer regardless of which project it points to.
- The CWD is a parent of multiple projects and the user gave no further hint — fall back to the index instead of asking.
- The user references a topic but not a project ("the lightrag handoff", "that auth thing from last week") — `grep <topic> ~/.claude/handoffs/INDEX.md` is the lookup.

The index entries carry absolute paths, so once you've found the right entry, just read that path directly.

**Legacy fallback**: if `<project>/docs/handoffs/` is empty for the current project AND nothing in the index matches, check `<project>/.claude/handoff.md` (older single-file pattern some repos used). If that's also empty, tell the user no handoff was found and offer to (a) check a different project, (b) start fresh, or (c) write one for the work just done.

If the CWD is a parent of multiple projects (e.g., `~/Coding/`) and the user named no specific project AND the index is empty, ask which subdirectory before searching — don't guess.

**Worktree paths**: if the resolved handoff path contains `.claude/worktrees/<name>/`, the doc was written from inside a git worktree. Note both paths — the worktree root (`<repo>/.claude/worktrees/<name>/`) and the parent repo (`<repo>/`) — because each has independent branch/working-tree state and the user's CWD may be in either. Step 3 reconciles both.

### Step 2: Read it

Read the whole doc. It's intentionally short. Pay attention to:

- **Branch** — is it the current branch? If not, surface that before any other action.
- **Date** — compute today − doc date. Sub-day = fresh, treat in-flight claims as live. Days-old = "currently running" PIDs are almost certainly dead; treat the doc as a historical snapshot and reconcile aggressively.
- **Next Steps** — the ordered list. Item 1 is what the user starts with.
- **Open / Blocked Items** — these become TodoList entries.
- **In-Flight Processes** (if present) — PIDs, log paths, ETAs for long-running work that was alive when the handoff was written. The single most load-bearing piece of state for a fresh-resume; check liveness in Step 3.
- **Uncommitted changes** line — the doc's claim about working-tree state.
- **Files touched** — useful for verifying paths still exist.
- **Worktree path** (if cited at the top of the doc) — the handoff may span a worktree and its parent repo; both trees need reconciliation.

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

Lead with the essential trio: **handoff path, branch + tree state, todos restored**. Add a "Next:" line with the verbatim Next Step 1 (and its cited path/command). Keep the body to one screen — the user is mid-context-switch, not reading a status report.

For a simple resume (single tree, no live processes, fresh handoff), three lines are enough:

```
Resumed from docs/handoffs/2026-04-28-foo.md.
Branch: main (matches handoff). Working tree: clean. TodoList: 4 tasks restored.
Next: <verbatim text of Next Step 1, with its file path>.
```

For a non-trivial resume (multi-tree, live process, partial state, days-old), add tight bullet lines for each significant piece of state — these belong above "Next:" so the user sees them before they read the action:

```
Resumed from <path-to-handoff>. Handoff: 3h old, written today.
Worktree branch: main (matches). Origin branch: feat/x (deferred-cleanup, expected).
Working tree: 1 file modified (matches handoff's documented absolute-path swap).
In-flight: PID 37219 still running, 2h 24m elapsed (handoff snapshot 2h 16m → on trajectory).
TodoList: 6 tasks restored.
Next: <verbatim text of Next Step 1>.
```

Prefix any actual divergences (state that contradicts the handoff) with "⚠" so the user can spot them at a glance — not the merely-noteworthy bullets above. If the handoff is days old, lead with that ("Handoff: 8 days old — treat in-flight claims as historical") so the user adjusts expectations before reading the rest.

Then **stop**. Do not pre-emptively run any of the Next Steps. Wait for the user to say go (they may want to revise an item, skip ahead, or take a different direction the handoff didn't anticipate).

### Read-mode don'ts

- Don't re-write or update the handoff doc as part of resuming. The doc is a historical artifact; if state has changed, that goes in the *next* handoff.
- Don't run the write-mode "Commit and push" finale. The user hasn't authorized commits in this session yet.
- Don't read more than the one handoff doc unless the user asks. Earlier handoffs are git history, not active state.
- Don't try to "fix" divergences silently (e.g., switching branches, stashing changes, recreating missing files). Surface them and let the user decide.

---

## LEARN mode — single-shot durable learning

Goal: in 1 tool call, append (or search) a single durable cross-session
learning to `<project>/docs/learnings.md` via the bundled `scripts/learn.py`.
No handoff doc, no commit-and-push, no TodoList changes — pure side effect
on the project-local learnings file.

Use this mode when the user wants to capture or query *one* lesson without
the full session-closeout ceremony. Common phrasings: "save this learning",
"remember this for next time", "log this gotcha", "capture this pattern",
"add to learnings", "search past learnings for X", "what learnings do we
have on Y". The §"Persist durable learnings" section below the Audience
section covers the same script — that section runs as a finale-step inside
WRITE mode; LEARN mode runs the same script standalone.

### Step 1: Distill the kernel

Read what the user wants to capture. If they pasted a paragraph or a
log excerpt, distill it down to ≤200 chars of generalizable kernel —
the "X looks like Y but is actually Z" essence, NOT the full event
narrative. The script warns above 250 chars but won't reject; over-long
patterns dilute search quality across all future sessions.

If the user's intent is **search** rather than capture, skip distillation
and run the search command instead.

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
python ~/.claude/skills/handoff/scripts/learn.py add \
  "<≤200-char kernel>" \
  --category gotcha|solution|pattern \
  --tags "domain1,domain2,handoff:2026-04-30-foo"

# Search
python ~/.claude/skills/handoff/scripts/learn.py search "<term>"
```

Same-day exact-pattern duplicates are silently skipped (idempotent — safe
to re-invoke). The script writes to `<project>/docs/learnings.md` (newest
on top, one line per entry, tags backtick-quoted for grep cleanliness).

### Step 4: Report and stop

For an `add` invocation, report the line that was appended (or skipped
as duplicate) and the file path. Three lines max:

```
Logged to docs/learnings.md (line 1):
- 2026-04-30 · gotcha · `lightrag,nan-embed` — qwen3-embedding NaN's on long inputs; substitute random unit vector not zero (L2 poisons)
```

For a `search` invocation, just relay the script's output (it already
prints "N match(es)" + the matching lines).

Then **stop**. No commit, no push, no handoff doc. The file change is
already on disk; the user can review or discard. If the project is a git
repo and the user later runs WRITE mode, the new learnings.md entries
will ride along in the handoff commit naturally — no separate commit
needed for LEARN-mode operations.

### LEARN-mode don'ts

- Don't write a handoff doc. LEARN is one-shot append/query, not a session-close ceremony.
- Don't commit or push automatically. The user invoked LEARN to record knowledge, not to publish a snapshot — if they want it on the remote immediately, they'll say so.
- Don't update `~/.claude/handoffs/INDEX.md`. The index tracks handoff docs; learnings live in their own file and are searched directly via grep or `learn.py search`.
- Don't paraphrase the user's intent into a different category if the wording is ambiguous. Ask: "gotcha (failure pattern), solution (working fix), or pattern (architectural shape)?" — one short question is cheaper than a mis-categorized entry that grep-searches won't find later.

---

## Audience

The reader is a future Claude Code session opening with a fresh context — not a human teammate. That means:

- Cite file paths and line numbers, not prose descriptions.
- Include exact commands to resume work (branch checkout, server start, env setup).
- Don't assume prior conversation context — state things plainly.
- Skip the narrative glue ("great session", "we discussed..."); future-you doesn't need morale or preamble.

## Where to save

Handoffs always live **project-local** at `<project>/docs/handoffs/YYYY-MM-DD-<slug>.md`. They version with the project's code, ship in PRs with the session commit, and survive `~/.claude/` resets. The previous problem ("where did I put yesterday's handoff?") is solved by a **central index** at `~/.claude/handoffs/INDEX.md` that maps every handoff to its absolute path. With the index, one `grep` finds anything across every project — without splitting storage.

### Filename rules

- **Date** is today, in the project's local timezone.
- **Slug** is short kebab-case describing the session focus (3–6 words). Examples: `lightrag-qwen36-upgrade`, `auth-jwt-refactor`, `billing-webhook-retry`.
- Create `<project>/docs/handoffs/` if it doesn't exist.
- If a file with the same slug already exists for today, append `-2`, `-3`, etc.

If you can't confidently identify the project root (e.g., the CWD is a folder containing multiple unrelated projects), ask the user which subdirectory to use before proceeding. Don't guess — a handoff dropped in the wrong repo is worse than a delayed one.

### Project slug derivation

Used for the index entry and the read-mode locator. In order — first that resolves wins:

1. **Git remote**: `git remote get-url origin 2>/dev/null` → strip protocol/host/`.git` → take the last path segment. Examples: `git@github.com:BrightGold70/HemaSuite.git` → `HemaSuite`; `https://gitlab.com/team/web/frontend.git` → `frontend`.
2. **Project root basename**: `basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"`. Used when there's no remote (local-only repo) or no git at all.

Slug derivation should not surface to the user unless ambiguous. Two projects with the same basename (e.g., two `frontend/` dirs from different orgs) are disambiguated by the git remote step in (1); if neither has a remote, treat it as ambiguous and ask.

### Update the central index

After writing the handoff file, append (prepend, technically — newest first) a one-line entry to `~/.claude/handoffs/INDEX.md`. This is the **only** thing in `~/.claude/handoffs/`; the directory exists solely to host this file.

Format — newest entries at the top:

```
- 2026-04-28 · HemaSuite/guideline-category-facet · Shipped guideline-category-facet end-to-end via TDD multi-agent cowork · `/Users/kimhawk/Coding/HemaSuite/docs/handoffs/2026-04-28-guideline-category-facet.md`
```

Each entry has four pipe-free segments separated by `·`: ISO date, `<project-slug>/<handoff-slug>`, a one-line summary lifted from the doc's Session Summary (≤100 chars), and the absolute path in backticks. Use absolute paths (not `~/`) so a `grep` is unambiguous.

Create the file with a `# Handoffs Index\n\nNewest first. Format: ISO date · project/slug · summary · path\n\n` header block if missing. Don't commit `~/.claude/handoffs/INDEX.md` to any project repo — it's user-global state, not project state.

The reason this matters: project-local handoffs are great for versioning and PRs but bad for "what did I work on across all my projects last month" — the index is what makes that question answerable in one command (`head ~/.claude/handoffs/INDEX.md` for recent, `grep <topic> ~/.claude/handoffs/INDEX.md` for search).

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
   - List the plan files and `command grep` their frontmatter for `status:` (Draft / Deferred / In-progress / Complete) and `gate:` / `blocked_by:`.
   - Check whether each plan has a corresponding `docs/04-report/features/<name>.report.md` (or equivalent). A plan without a report is a candidate "unimplemented" entry; cross-check the codebase or session for evidence it actually shipped before flagging.
   - Skip silently if the project has no such structure. Don't fabricate one. The point is to surface backlog signal that already exists, not invent a tracking system.
5. **Live processes** — if the session launched any long-running background work that's still alive at the moment of writing (multi-hour ingests, soak tests, build pipelines, daemons started for testing): capture PID, the exact command (one line), the log path, started-at, elapsed, and a one-line "what to verify on exit". This populates the **In-Flight Processes** section. Skip silently if nothing is in flight — most sessions don't have any. The check costs nothing (`ps -p $! -o pid,etime` for each backgrounded job, or `pgrep -f <substring>` for processes the operator launched manually) and the value to a future resume is enormous: without it, the next session has to reverse-engineer "is this still going?" from log mtimes and ambiguous output.
6. **Worktree state** — if `git rev-parse --show-toplevel` returns a path containing `.claude/worktrees/<name>/`, the session ran in a worktree. Also capture the parent repo's branch (`git -C <parent> rev-parse --abbrev-ref HEAD`) so the handoff names both. The worktree's "to resume" `cd` should point at the worktree root, not the parent.

Do **not** run tests, builds, or long-running commands just to populate the handoff. Use what was already observed in the session. If something wasn't verified, the handoff should say so — that's load-bearing information.

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

<Include this section ONLY when the session is handing off long-running work that's still alive at the moment of writing — a multi-hour ingest, a soak/burn-in test, a build pipeline, a streaming job. Omit entirely otherwise. The point is to make resume mechanical: the next session can `ps -p <PID>` and `ls -la <log>` and instantly know whether to monitor, harvest results, or abandon.

For each in-flight process, list: PID, command (one line), log path, started-at (HH:MM), elapsed at handoff time, ETA, expected exit signal (a log line, a file appearing, a process exit), and what to verify on completion. If the user resumes hours or days later, this section's mtime/PID checks tell them immediately whether the work is still alive.>

| PID | Command | Log | Started | Elapsed @ handoff | ETA | What to check on exit |
|---|---|---|---|---|---|---|
| 37219 | `nohup .venv/bin/python -m scripts.compile_guidelines_db --batch ...` | `/tmp/hpw_logs/facets_ingest_20260429-1129.log` | 11:29 | 2h 16m (13/34 entries) | ~3-4h more | `yq '.documents \| length' MANIFEST.yaml` ≥ 55; grep `errors=` in log == 0 |

## Context for Next Session

**Files touched this session:**
- `path/to/file.ts`
- `path/to/other.ts`

**Worktree** (include only if the session ran in a git worktree, not the parent repo):
- Worktree root: `<repo>/.claude/worktrees/<name>/` — branch: `<branch>`
- Parent repo: `<repo>/` — branch: `<branch>` (note any deferred-cleanup state)

**Uncommitted changes:** <one-line summary from `git status`, or "none">

**To resume:**
\`\`\`bash
cd <project root>
git checkout <branch>
# env setup, server start, etc.
\`\`\`

**Related docs:**
- <links to design docs, plans, issues referenced in the session>

## Unimplemented Plans Backlog

<Include this section ONLY if the project has a plan-tracking directory (e.g., `docs/01-plan/features/`). Otherwise omit entirely — do not write "None" for projects that don't use plan docs at all.

When kept: a small table of plans not yet shipped, so future-you can pick one up without re-discovering the backlog. For each: file path, project (if monorepo), state (Draft / In-progress / Deferred / Blocked), and a one-line note about prereqs, gates, or what's needed to start. Also list plans that closed during this session-cluster so the recently-shipped context isn't lost. Keep this lean — link to plans, don't summarize them.>

| # | Plan | Project | State | Notes |
|---|---|---|---|---|
| 1 | `path/to/some-plan.plan.md` | <project> | Draft, ready | <prereqs / 1-line scope> |
| 2 | `path/to/other-plan.plan.md` | <project> | Deferred | <gate condition> |

Recently closed (this session-cluster):
- ✅ <plan name> — <report path>
```

## Writing guidance

- **Cite, don't describe.** "Refactored auth middleware" is useless. "Replaced `validateJWT` in `src/auth/middleware.ts:87` with `@auth/jwt-verify` — old version is in git if rollback needed" is useful. The reason is that future-you can navigate to a path; prose forces re-reading the transcript.
- **Next Steps must be actionable.** If an item reads like a goal ("improve test coverage"), rewrite it as the first concrete action ("add test for `parseInvoice` NaN case in `src/billing/invoice.test.ts`"). Goals are for plans; Next Steps are for picking up tools.
- **Flag unverified work loudly.** If a fix was applied but not run, say so: "Patched X in `foo.ts:12`; did not re-run integration suite — verify before merging." Silently shipping "done" for unverified work is the single most common way handoffs mislead the next session.
- **Keep each section tight.** A handoff is a map, not a transcript. If Session Summary is longer than 5 sentences, trim it.

## After writing

Report to the user in one or two lines: the file path, and the essential shape of the handoff (e.g., "Wrote `docs/handoffs/2026-04-24-auth-jwt-refactor.md` — 3 next steps, 1 blocker on Redis version upgrade"). Do not recap the file's contents; the user can open it.

## Persist durable learnings to `docs/learnings.md`

Before commit, push **durable** learnings into the project-local
`docs/learnings.md` so they survive as cross-session searchable knowledge —
not just narrative bullets buried in one handoff doc. The Key Learnings
section in the handoff is point-in-time; `docs/learnings.md` is the
persistent layer that future sessions can `grep` without re-reading every
old handoff.

**Mechanism — bundled, no external dependency**: this skill ships its own
`scripts/learn.py` that handles append, dedup, and search against
`<project>/docs/learnings.md`. There is no external `/learn` skill or
plugin to install — invoke the bundled script directly via Bash. The
script is self-contained (Python stdlib only, no third-party deps).

**What to push (durable signal):**

- Gotchas with reusable diagnostic value: "X looks like Y but is actually Z" insights, runner/library-state degradation patterns, API contract drifts that mask deeper bugs
- Solutions that codify a pattern: "use singleton calls + reload on NaN" (the pattern), not "fixed E9-R1 today" (the event)
- Recurring conventions or constraints just discovered: file-format quirks, version traps, environment-specific gotchas

**What NOT to push (session-specific noise):**

- Status updates ("rebuild PID 85062 finished")
- Sequence-of-events narration ("first X, then Y, then Z")
- Single-event observations without a generalizable lesson
- Anything already documented in a tech note / rules file the project owns

**How to invoke**: shell out to the bundled script — one call per durable
learning. Keep the pattern text under ~200 chars (the script warns above
250 but won't reject). Always include `handoff:<date>-<slug>` as one of
the tags so future readers can pull the full narrative from the
originating handoff doc:

```bash
python ~/.claude/skills/handoff/scripts/learn.py add \
  "qwen3-embedding NaN's on long inputs; substitute random unit vector not zero (L2 poisons)" \
  --category gotcha \
  --tags "lightrag,nan-embed,handoff:2026-04-28-rebuild"
```

The script writes one line per entry to `<project>/docs/learnings.md`,
newest entries at the top, tags backtick-quoted so `grep` can match the
tag-list cleanly without false positives from prose mentions. Same-day
exact-pattern duplicates are silently skipped (idempotent).

**Search later sessions** with either:

```bash
grep <term> docs/learnings.md                                       # plain grep
python ~/.claude/skills/handoff/scripts/learn.py search <term>     # case-insensitive entry-only
```

**Boundary with Key Learnings in the handoff doc**: keep both. Key Learnings remain in the handoff (narrative context, full sentences, why-it-mattered framing). `docs/learnings.md` entries are the kernel of each — short, searchable, generalizable. They're written from the same source material but serve different audiences (current handoff reader vs. cross-session grep).

If unsure whether something is durable, default to **not** pushing — over-pushing dilutes search quality. Better to lose a marginal entry than poison the cross-session index.

## Commit and push (default finale)

After the handoff is written and the index is updated, commit all session work — including the handoff doc — and push to the project's default branch. The handoff lives in the project repo (`docs/handoffs/`) so it ships in the same commit as the code it describes; this keeps a future-you reading the handoff confident that every path/line cited in it exists on the remote.

Do **not** commit `~/.claude/handoffs/INDEX.md` — that's user-global state outside any repo. The project's commit only contains project-local content.

Skip silently if the project isn't a git repo, or if the user has explicitly opted out ("don't commit" / "I'll push it myself"). The user invoking `/handoff` is the authorization for this step; the working tree state is what's about to ship.

The reason this lives in the handoff skill (not as a separate manual step) is that handoffs are session boundaries — leaving uncommitted work behind defeats the point of the doc. A future-you reading the handoff will reference paths and line numbers that may not exist on the remote yet; commit+push closes that gap.

### Pre-flight (run before staging)

Run `git status --short` and read the output before staging anything. Two filter passes:

1. **Refuse to auto-stage secrets.** Block files matching `.env*` (allow `.env.example`, `.env.sample`, `.env.template`), `*credentials*`, `*secret*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `*.pfx`. If any appear in `git status`, surface them to the user and ask whether to include — don't guess. The cost of accidentally pushing a secret to a shared branch is very high.
2. **Warn on noisy artifacts.** Generated dirs (`__pycache__/`, `node_modules/`, `dist/`, `build/`, `.venv/`, `target/`, `.next/`, `.cache/`) and large binaries (>10 MB) usually shouldn't ship. If `git status` shows them as untracked, mention them and ask before staging — they may indicate a missing `.gitignore` entry.

If pre-flight passes, proceed.

### Commit

Use a HEREDOC for the commit message (`-m "..."` mangles newlines). Compose a subject tied to the session topic — typically a one-line summary of what shipped, not just "handoff". Body: 2-4 lines describing the actual changes; the handoff doc is the long-form, the commit body is the short-form for git log readers.

```bash
git add -A      # only after pre-flight passes; otherwise add specific files

git commit -m "$(cat <<'EOF'
<type>: <one-line session outcome>

<2-4 line body — what changed and why, not a play-by-play>

🤖 Co-Authored-By: Claude <model-id> <noreply@anthropic.com>
EOF
)"
```

The `<type>:` prefix should match the project's convention (`feat:`, `docs:`, `fix:`, etc. for conventional-commits projects; whatever style `git log --oneline -10` shows for others).

### Push

Detect the default branch from the remote — don't hardcode `main`, since plenty of repos use `master`, `develop`, `trunk`, or feature-branch workflows. The current branch is usually right; only switch branches if the user explicitly asked to.

```bash
git push origin HEAD
```

If `git push` fails because there's no upstream tracking, surface the failure and ask whether to set up tracking (`git push -u origin HEAD`) rather than guessing.

### Verify

After the push, run `git log --oneline -3` and `git status --short` so the user (and future-you) can see the new commit hash and confirm the working tree is clean.

### Don't

- Force-push to a shared branch unless the user explicitly asked.
- Skip pre-commit hooks (`--no-verify`, `--no-gpg-sign`) without operator approval — if a hook fails, fix the underlying issue and retry, don't bypass.
- Stage and commit secrets that the pre-flight flagged. If the user insists, ask them to confirm by name once more.
- Amend an existing commit when adding the handoff. Always create a new commit — handoffs are timestamped session markers, not edits to prior work.
