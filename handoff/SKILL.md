---
name: handoff
description: Use this skill in three modes. WRITE mode — create a session handoff document, end-of-session summary, session closeout, wrap-up doc, or notes for the next session — produces a project-local markdown handoff at docs/handoffs/YYYY-MM-DD-<slug>.md capturing session summary, key learnings, next steps, open/blocked items, and resume context, aimed at future-you opening a fresh Claude Code session. READ mode — resume work after /clear or at the start of a fresh session by loading the most recent handoff, reconciling its state with the working tree, and restoring the TodoList. When running under Orca, WRITE also stamps a durable, mobile-visible checkpoint on the active worktree and READ reconciles against Orca's worktree model (both best-effort via `hmad-dispatch`, skipped cleanly when Orca is absent). LEARN mode — record a single durable cross-session learning to <project>/docs/learnings.md via the bundled scripts/learn.py (no external skill or plugin dependency); also exposes a search command for grep-style retrieval across past learnings. Invoke for WRITE whenever the user says /handoff, "handoff", "session summary", "wrap up session", "close out session", "document what we did", "leave notes for next time"; invoke for READ whenever the user says "read handoff", "/handoff resume", "load handoff", "resume from handoff", "where did we leave off", "pick up where we left off", "continue from last session", or any variant about loading prior session state — especially right after /clear; invoke for LEARN whenever the user says "save this learning", "remember this for next time", "log this gotcha", "capture this pattern", "add to learnings", "this is a recurring issue, save it", "what learnings do we have on X", "search past learnings for Y", or any variant about recording or retrieving durable cross-session knowledge outside a full handoff. Use this skill whether or not the exact word "handoff" appears, and prefer LEARN mode for single-shot lesson capture, READ mode when phrasing is about *picking up* prior state, and WRITE mode when *closing out* a session.
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
| `--skip-memories` | off | Skip the "Update persistent auto-memories" phase. |

### WRITE — stamp an Orca checkpoint (best-effort, Orca only)

After the handoff markdown is written (and not on `--dry-run`), leave a durable, mobile-visible checkpoint on the active Orca worktree so the next session — and the Orca mobile app — sees where this one stopped without opening the doc:

- Gate on substrate: run `hmad-dispatch env`; proceed only if it reports `substrate: orca`. (`hmad-dispatch` is the h-mad wrapper; if it is not on PATH, skip this step.)
- Preserve a foreign note: the worktree comment is a single shared field. First read `.worktree.comment` via `hmad-dispatch worktree-current`. If it is non-empty AND does not already start with `handoff:` or `h-mad` (i.e. a human wrote it, not a prior stamp), keep it — append the checkpoint after it (`<existing> — handoff: …`) rather than clobbering. An empty comment or a prior skill stamp is replaced outright.
- Stamp: `hmad-dispatch worktree-comment active "handoff: <slug> · <status> · next: <next-step>"`, where `<slug>` is the handoff doc's slug, `<status>` a 2–4 word state, `<next-step>` the top Next Step.
- Non-fatal: a non-zero result (no runtime, non-orca, wrapper absent) emits `[handoff] worktree_comment_skipped` and is ignored. The handoff is complete regardless — the checkpoint is an enrichment, never a gate. All Orca access goes through `hmad-dispatch`; never call `orca` directly from this skill.

---

## Reading a handoff (resume mode)

### Step 0: Sync local with the remote BEFORE locating/reading

Do this first, before Step 1 — otherwise you may locate + read a **stale** handoff: a newer one (or commits that updated the doc) may have been pushed from another machine / session and not exist locally yet. Step 3's "Remote ↔ local sync" runs *after* the doc is read, which is too late for this. If the current project is a git repo:

- `git rev-parse --abbrev-ref @{u}` — if it errors (no upstream / no remote), skip this step **silently** and proceed to Step 1 on the local tree.
- `git fetch` (quiet).
- `git rev-list --left-right --count @{u}...HEAD` → `<behind>\t<ahead>`.
  - **Behind, clean tree**: `git pull --ff-only`. Now Step 1 locates and Step 2 reads the freshest handoff + the commits it references. Report the new HEAD in the Step 5 resume report.
  - **Behind, dirty tree** OR **diverged** (behind > 0 AND ahead > 0): do NOT pull — a surprise merge/rebase is worse than a slightly-stale doc. Read the local doc as-is; Step 3 does the full divergence flagging.
  - **In sync / ahead only**: proceed.

This Step 0 fast-forward (clean-tree only) is the "sync remote and local before reading" guarantee. Step 3 still runs afterward for the dirty/diverged/ahead/in-flight cases this step deliberately skips (its `git fetch` is then a cheap idempotent no-op).

### Step 1: Locate the doc

Locate on the now-synced tree (Step 0). Check, in order:

1. **Explicit path in the user's message** — if they paste or type a path, use it.
2. **This branch's newest handoff in the canonical store** — with `HP="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py"`, run `python3 "$HP" latest --branch "$(python3 "$HP" branch-slug)"`. This resolves the shared main-worktree `docs/handoffs/` and prefers a handoff written on the branch you are resuming (exact `<branch>__` match — a `feat` resume never grabs a `feat-ab` sibling), so a parallel Orca session on another branch can't hand you the wrong one.
3. **Repo-wide newest in the canonical store** — `python3 "$HP" latest` (no `--branch`). Use when this branch has none. If it matches a *different* branch, say so and confirm with the user before resuming — you may be picking up a sibling worktree's work.
4. **`~/.claude/handoffs/INDEX.md`** — grep for the current project name / path; take the newest matching entry's path.

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
- **Remote ↔ local sync** — Step 0 already fast-forwarded the clean-behind case before reading; this bullet re-checks and covers what Step 0 deliberately skipped (dirty/diverged/ahead). The working tree may have moved on the remote since the handoff (another machine, a teammate, a CI bot, or a `/handoff` WRITE push from a different session). Before the user starts any new action, reconcile against the remote so they don't branch off a stale base:
  - `git fetch` (quiet; if no remote or no upstream, skip this bullet silently — `git rev-parse --abbrev-ref @{u}` errors → no upstream).
  - `git rev-list --left-right --count @{u}...HEAD` → `<behind>	<ahead>`.
  - **In sync** (0 behind, 0 ahead): state "in sync with `<upstream>`" on one line; no action.
  - **Behind, clean tree**: surface as a divergence and **fast-forward before acting** — run `git pull --ff-only`. If it fast-forwards cleanly, report the new HEAD. This is the "sync remote and local before starting" guarantee.
  - **Behind, dirty tree** OR **diverged** (behind > 0 AND ahead > 0): do NOT auto-pull — flag it ("N behind / M ahead, uncommitted changes present" or "branches have diverged — rebase/merge needed") and let the user resolve. A surprise merge/rebase mid-resume is worse than a one-line warning.
  - **Ahead only** (unpushed local commits): flag as information ("M local commits not yet pushed") — relevant because the prior session may have committed without pushing.
- **In-flight processes** — for each PID cited in In-Flight Processes / Open Items / Next Steps, run `ps -p <PID> -o pid,etime,stat`. For each cited log path, `ls -la <log>` to read size + mtime. Surface one of: "still running, N min elapsed (matches handoff trajectory)" / "exited" / "log unchanged for N hours — likely dead, treat as historical". This is the single most load-bearing reconciliation when the handoff hands off live work; never skip it. If the doc is days old, treat all in-flight claims as historical without bothering to check `ps` (the PID has been recycled and reporting on a stranger's process is worse than silence).
- **Worktree split** — if the handoff path is inside `.claude/worktrees/<name>/`, the doc was written from a worktree. Run `git -C <worktree-root> rev-parse --abbrev-ref HEAD` AND `git -C <parent-repo> rev-parse --abbrev-ref HEAD` — both trees have independent state and both matter. The handoff's "Branch:" field usually refers to the *worktree*; the parent repo may be on a deferred-cleanup branch (the handoff often calls this out). State each tree's branch on its own divergence line if they disagree with the doc.
- **Orca worktree reconcile** (Orca only) — if `hmad-dispatch env` reports `substrate: orca`, reconcile against Orca's worktree model, which persists across sessions and the mobile app where git+PID state does not:
  - `hmad-dispatch worktree-current` → the payload is `{"worktree":{…}}`; read `.worktree.branch`, `.worktree.path`, `.worktree.comment`. Compare branch/path to the doc's Branch/worktree — **but `.worktree.branch` is a full ref (`refs/heads/main`) while the doc and `git rev-parse --abbrev-ref HEAD` use the short name (`main`), so strip the `refs/heads/` prefix before comparing** or every resume reports a phantom mismatch. A genuine mismatch is a divergence line (you may be in the wrong worktree). `.worktree.comment` is the last checkpoint the writing session left (see WRITE stamp) — quote it if present.
  - `hmad-dispatch worktree-ps` → the payload is `{"worktrees":[…],"totalCount","truncated"}`; iterate `.worktrees[]` and list each as `<.branch> · <.comment>` (branch is again a full ref — strip `refs/heads/`) so in-flight siblings (parallel agents, queued fanout modules) are visible before you act. If `.truncated` is true, say so — the list is capped (raise the cap with `worktree-ps --limit <n>`).
  - Read-only: use only `worktree-current`/`worktree-ps`; never `worktree-comment`/`create`/`rm` here, and never call `orca` directly. A non-zero result emits `[handoff] worktree_reconcile_skipped` and the reconcile falls through to the git+PID checks above unchanged.

A divergence is not a failure — it's just information the user needs before acting. State each one as a single sentence.

### Step 4: Restore the TodoList

Use the TodoList tool (TaskCreate or equivalent) to repopulate todos from the doc's **Next Steps** and **Open / Blocked Items**. Each Next Step becomes a `pending` task with the cited path/command in the description. Each Open/Blocked Item becomes a `pending` task tagged with its blocker if any. Do this even if Next Steps is short — the point is that the user can start on item 1 without re-typing the list.

**Prefix every restored todo with `[<repo>@<branch>]`** so that when todos from multiple worktrees/repos/handoffs coexist in one list, each one names its origin at a glance. `<repo>` is the project slug (§"Project slug derivation" — CLI name, else git-remote basename, else repo dir name); `<branch>` is the handoff doc's **Branch:** field (the branch the work belongs to, which under Orca multi-worktree may differ from the branch you resumed on). Example: `[skills@main] Verify report-file transport …`, `[HemaSuite@feature/12] Add _orca_json guard …`. If the doc's Branch is "n/a", use `[<repo>]` alone. Keep the prefix outside any inline reconciliation note (below) — prefix first, then the task, then any `[verify path …]` note.

If the doc's Next Steps reference a file that the reconciliation pass flagged as missing or moved, mark that task with an inline note (e.g., "[verify path — file moved since handoff]") rather than dropping it.

**Dedupe overlapping items.** It's normal for an in-flight piece of work to appear in both Next Steps ("monitor PID N") and Open Items ("PID N still running") — same thing, two framings. Make one Todo, not two. Same for "verify the 14 placeholder dates" appearing in both lists. Combine the descriptions and merge.

### Step 5: Report back and stop

After reconciliation and TodoList restore, give the user a brief resume report:

```
## Session resumed

**Handoff:** docs/handoffs/2026-04-30-lightrag-guideline-rag.md
**Branch:** main (matches)
**Remote:** 2 behind origin/main → fast-forwarded to `a1b2c3d`
**Uncommitted changes:** 2 files (matches handoff)

**Divergences:**
- PID 37219 (compile_guidelines_db): exited — log mtime 3h ago. Treat as complete; verify output.
- `protocol/sections/background.md` cited in Next Steps — file not found (may have been renamed).

**Todos restored:** 4 items. Starting at:
1. [guideline-rag@main] Verify compile_guidelines_db output (`yq '.documents | length' MANIFEST.yaml` ≥ 55)
```

Then stop. Don't start executing tasks — the user reads the report and decides what to do first.

### Read-mode don'ts

- Don't rewrite or update the handoff doc in read mode — it's a historical record.
- Don't run tests or builds as part of reconciliation.
- Don't assume the in-flight process is still running if the doc is >4h old.
- Don't `git pull` when the tree is dirty or the branch has diverged — fast-forward-only (`git pull --ff-only`) on a clean tree, otherwise flag and let the user resolve. Never `git merge`/`git rebase`/`git push` during a resume.

---

## LEARN mode — single-shot durable learning

Capture a single non-obvious finding, pattern, or gotcha so it survives future `/clear` calls and new sessions. This is lighter than a full handoff — one learning, one command, done.

### Step 1: Distill the kernel

From the user's description (or the conversation context if they invoked LEARN without a message), extract:

- The **pattern** — a ≤240-character statement of the reusable finding. It should read like a fact, not a story ("qwen3-embedding NaN's on long inputs — substitute random unit vector, not zero vector; L2-norm poisons downstream embeddings"). Shorter is still better — the cap is a ceiling, not a target.
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
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/learn.py" add \
  "<≤240-char kernel>" \
  --category gotcha|solution|pattern \
  --confidence 0.3|0.5|0.7|0.9 \
  --tags "domain1,domain2,handoff:2026-04-30-foo"
# Over 240 chars? Add --trim to word-boundary-trim in one call (marked …), OR
# shorten to the ≤240 suggestion the plain rejection prints. Don't retry by
# eyeball — that overshoots. Prefer rewriting tighter when the kernel's punchline
# is at the END (trim cuts the tail); use --trim when the tail is expendable.

# Search
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/learn.py" search "<term>"
```

**Confidence guide**: `0.3` = single observation, unvalidated · `0.5` = observed 2-3×
or user confirmed once · `0.7` = repeatedly seen, no contradictions (default) ·
`0.9` = core pattern, multiple independent confirmations. Omit `--confidence` to use 0.7.

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
- Don't pad the kernel toward the 240-character cap to sound thorough — shorter is better.

---

## Audience

Write as if future-you is the reader: someone who knows the project deeply but has zero memory of this specific session. They've just typed `/clear`, opened a new Claude Code window, and are about to ask "where were we?". The handoff is their only briefing.

---

## Where to save

### Filename rules

```
<canonical>/docs/handoffs/YYYY-MM-DD-<branch-slug>__<slug>.md
```

- `<canonical>` — the **main-worktree** root from `handoff_paths.py dir` (see §Save), not the current linked worktree.
- `YYYY-MM-DD` — today's date in ISO format (use `date +%Y-%m-%d` if unsure).
- `<branch-slug>` — `handoff_paths.py branch-slug` (current branch, `/`→`-`, no `_`). The `__` after it is the branch|slug separator (never `-`, so READ matches the branch exactly).
- `<slug>` — 2–4 lowercase words from the session's main topic, hyphenated. Derive from the feature name, PDCA feature slug, or issue/ticket if one exists.
- Examples: `2026-04-30-main__lightrag-guideline-rag.md`, `2026-05-01-feature-189-handoff__protocol-daemon-fix.md`

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

**How to prepend — anchor on the first list item, never on the header text.** Insert the new entry *immediately before the first existing `- ` bullet line*, so it becomes the newest. Do **not** anchor the insert on the `Newest first. Format:` header string: this file has been observed carrying a duplicate of that line mid-file, and a header-anchored insert lands the newest entry in the middle instead of the top (observed 2026-07-23 — an entry went to line 36). "Before the first `- ` line" is unambiguous no matter how many stray header lines exist. After inserting, verify placement (`grep -n '^- ' INDEX.md | head -1` should return your entry) rather than trusting the write — and if you find a stray `Newest first.`/`Format:` line anywhere below the top block, delete it while you are here; it is corruption that will mis-anchor the next writer.

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
6. **Worktree state** — the session ran in a linked worktree if EITHER `git rev-parse --show-toplevel` contains `.claude/worktrees/<name>/` (Claude Code convention) OR it differs from `python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py" root` (any linked worktree, including **Orca's** sibling-dir layout; under Orca, `hmad-dispatch worktree-current` also reports `.worktree.isMainWorktree == false`). In that case capture the worktree root, its branch, AND the main-worktree root + branch (`git -C <main> rev-parse --abbrev-ref HEAD`) so the handoff names both. The "to resume" `cd` points at the worktree root, not the main repo. (The handoff *file* still lives in the canonical/main store — §Save — so siblings can find it.)
7. **Session observations** — if `~/.claude/homunculus/observations.jsonl` exists, read the last 50 lines. These structured observations often surface gotchas not explicit in the conversation. Use them to enrich Key Learnings extraction. Skip silently if absent.
   ```bash
   OBS_FILE="$HOME/.claude/homunculus/observations.jsonl"
   [ -f "$OBS_FILE" ] && tail -50 "$OBS_FILE"
   ```
   After reading, scan inline for these patterns (no external tools needed):
   - **User corrections**: a tool call followed immediately by user rephrasing the request ("no, do X instead", "wrong approach", "revert that") → `gotcha`, suggest confidence 0.5
   - **Error resolutions**: failed command (error output / non-zero exit) followed by successful alternative in the same session → `solution`, suggest confidence 0.7
   - **Repeated workflows**: same command or sequence appearing ≥3 times in the transcript → `pattern`, suggest confidence 0.7

   For each pattern detected, add a candidate learning to Key Learnings with the detected category and suggested confidence noted inline (e.g., `[suggested gotcha, 0.5]`). These become inputs to the "Persist durable learnings" step — the user can confirm or discard via the handoff doc.
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

1. Save the file to the **canonical, worktree-shared** handoffs dir, with the branch in the name so concurrent Orca sessions on different branches don't collide:
   ```bash
   HP="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py"
   DIR="$(python3 "$HP" dir)"          # main-worktree docs/handoffs (shared by all linked worktrees)
   BR="$(python3 "$HP" branch-slug)"
   mkdir -p "$DIR"
   FILE="$DIR/$(date +%F)-${BR}__<slug>.md"   # note the '__' separator between branch and slug
   ```
   `handoff_paths.py dir` resolves to the **main worktree** (`git rev-parse --git-common-dir` → parent), not the current linked worktree — so every parallel Orca worktree reads/writes ONE store, and the handoff survives when a worktree is archived/removed. The `__` between `<branch>` and `<slug>` is the unambiguous separator READ matches on (branch slugs never contain `__`), so resuming branch `feat` can't load a `feat-ab` sibling's handoff. **Concurrency guard:** if `$FILE` already exists (a live sibling session wrote the same branch+slug today), do NOT overwrite — append a short discriminator (`-2`, `-<HHMMSS>`) before `.md` so both survive.
2. Update `~/.claude/handoffs/INDEX.md` (one-line entry, newest first — see §"Update the central index").
3. Proceed to §"Persist durable learnings" if Key Learnings is non-empty and `--skip-learnings` was not set.
4. Proceed to §"Update persistent auto-memories" unless `--skip-memories` was set.
5. Proceed to §"Automation scout" unless `--skip-scout` was set.
6. Proceed to §"Commit and push".

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
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/learn.py" add \
  "<≤240-char kernel>" \
  --category gotcha|solution|pattern \
  --confidence 0.7 \
  --tags "domain1,domain2,handoff:YYYY-MM-DD-<slug>"
# Over 240 chars: add --trim (word-boundary trim in one call), or paste the
# ≤240 suggestion the rejection prints — never eyeball-retry, it overshoots.
```

Pick confidence based on the evidence: `0.3` for single-session observations not yet
re-confirmed · `0.5` for corrected-once or 2-3 occurrences · `0.7` for repeatedly seen
(safe default) · `0.9` for well-established patterns with no contradictions.

Always include `handoff:<date>-<slug>` as a tag so the learning is cross-referenced to this session.

---

## Update persistent auto-memories

`docs/learnings.md` is **project-scoped** (lives in the repo, grepped on demand). It is NOT the same
as the **persistent auto-memory** store at `~/.claude/projects/<project-dir-slug>/memory/`, which is
**user-global** and whose `MEMORY.md` index is loaded into context at the start of *every* session.
A learning written only to `docs/learnings.md` will not surface automatically next session; a
memory written to the auto-memory store will. Wrapping up is the moment to reconcile the store with
what this session proved — skip it and the next session starts with stale guidance. (Skip this phase
only if `--skip-memories` was set, or the memory dir does not exist.)

**When to write/update a memory** (distinct from a `docs/learnings.md` entry):
- The session produced **feedback on how to work** — a correction the user gave, or a confirmed
  approach (e.g. "tool X is reliable when invoked via Y", "always run a real end-to-end check").
- A **fact contradicts an existing memory** — flip/correct it; a stale memory is worse than none.
- A durable **user / project / reference** fact not derivable from the repo (who the user is, an
  ongoing constraint, an external dashboard/ticket).
Skip anything already captured in the code, git history, CLAUDE.md, or that only mattered this
session — those belong in the handoff doc or `docs/learnings.md`, not the auto-memory store.

**How to apply:**
1. Read the store's `MEMORY.md` index first. For each candidate, find an existing memory file it
   updates and **edit that file** (correct/flip stale claims, append a dated reinforcement) rather
   than creating a duplicate. Only create a new file when nothing covers it.
2. Each memory is one file with frontmatter (`name`, `description`, `metadata.type:
   user|feedback|project|reference`) and a body; for `feedback`/`project`, include **Why:** and
   **How to apply:** lines. Link related memories with `[[their-name]]`. Convert relative dates to
   absolute.
3. **Update the one-line pointer in `MEMORY.md`** when a memory's hook changes (e.g. a flipped
   conclusion) — the index is what the next session actually reads first.
4. The auto-memory dir is **not a git repo** — there is nothing to commit or push there. It is
   user-global local state. (The §"Commit and push" finale pushes only the project handoff +
   learnings to the project remote; it does not touch the memory store.)

If the project uses a different memory mechanism (no `~/.claude/projects/.../memory/` dir), skip
silently — do not invent one.

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

### Evolution bridge (opt-in)

After writing to `docs/skill-candidates.md`, check whether
`~/.claude/homunculus/evolved/skills/` exists. If it does **and** any candidate
has `recurrence: N` where N ≥ 3 **and** `candidate: yes`, write a minimal stub
there so the pattern is visible to continuous-learning-v2 if installed:

For each qualifying candidate, create
`~/.claude/homunculus/evolved/skills/<pattern-slug>.md`:

```markdown
---
name: <pattern-slug>
description: <one-line description from candidate>
source: handoff-scout
recurrence: N
session: YYYY-MM-DD
---

# <Pattern Name>

Candidate graduated from `docs/skill-candidates.md` via handoff automation scout.
Recurrence: N sessions. Promote to a full skill when the pattern stabilises further.
```

Skip silently if `~/.claude/homunculus/evolved/` does not exist — this bridge
is opt-in for users who have continuous-learning-v2 installed. Do not create
the directory; just skip.

---

## Commit and push (default finale)

After the handoff doc is written and learnings are persisted, commit and push unless the user explicitly says not to.

### Pre-flight (run before staging)

```bash
git status --short          # confirm only handoff + learnings files are staged
git diff --stat HEAD        # sanity-check scope
```

### Commit

Stage the **actual absolute paths** written in §Save (`$FILE` and `handoff_paths.py learnings`), not a cwd-relative `docs/handoffs/…` — under a linked worktree the cwd path points at the wrong tree and would stage nothing.

```bash
ROOT="$(python3 "$HP" root)"                 # canonical main-worktree root
LEARN="$(python3 "$HP" learnings)"
```

- **On the main worktree** (`ROOT` == `git rev-parse --show-toplevel`): stage + commit normally:
  ```bash
  git add "$FILE" "$LEARN"
  git add docs/skill-candidates.md 2>/dev/null || true   # only if scout ran
  git commit -m "chore(handoff): YYYY-MM-DD <slug>

  Session closeout: <one-line summary from Session Summary>."
  ```
- **On a linked worktree** (`ROOT` != current toplevel): the handoff + learnings were written into the **main** tree, not here. Do **not** auto-commit into the main worktree's branch — it may be mid-work on an unrelated branch, and a surprise handoff commit there is worse than none. The file is already written and shared (that is the durability win); note in your report that committing/pushing it is a deliberate step to run from the main worktree if cross-machine persistence is wanted.

Do not use `git add -A` — only stage the handoff and learnings files.

### Sync with remote (before push)

The remote may have moved since the session started (another machine, a teammate, CI, or a `/handoff` push from a different window). Reconcile the now-committed handoff against the remote so the push is a clean fast-forward and you don't leave a rejected-push surprise for next session.

```bash
git fetch                                          # skip if no remote/upstream (git rev-parse @{u} errors)
git rev-list --left-right --count @{u}...HEAD       # "<behind>	<ahead>"
```

- **In sync / ahead only** (behind = 0): proceed straight to Push.
- **Behind** (remote has new commits the local doesn't): integrate before pushing. The tree is clean here — everything except the handoff/learnings files was committed or untouched — so `git pull --rebase` replays your single handoff commit on top:
  ```bash
  git pull --rebase
  ```
  If the rebase conflicts (rare — handoff files are new/append-only), abort (`git rebase --abort`), tell the user the remote diverged and the handoff commit is local-only, and stop. Don't force-resolve.

### Push

```bash
git push origin HEAD
```

If the push is still rejected (remote moved again between fetch and push), re-run the Sync step once, then push. Never `--force`.

### Verify

```bash
git log --oneline -3    # confirm commit landed
```

### Don't

- Don't amend or force-push.
- Don't stage unrelated changes that were open before the handoff.
- Don't push if the user said "don't commit" or the repo is in a detached HEAD state.
