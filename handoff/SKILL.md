---
name: handoff
description: "Use this skill in five modes. WRITE creates a durable session closeout. READ resumes from the latest reconciled handoff and restores work to an available task sink; restoration never no-ops. LEARN records or searches one cross-session lesson. TAKEOVER mode adopts an inbound brief on /handoff takeover and does NOT halt in a loaded session. HANDOVER mode — move ownership of tracked work; invoke for hand this over or hand off X to another worktree. Use the `orca-cli` skill directly instead for prompt delivery without ownership transfer, and the `orchestration` skill when the user wants the work supervised."
---

# Handoff

## Host runtime

This package supports Claude Code, OpenAI Codex, the Antigravity CLI (`agy`) and the grok CLI
(`grok`). In Codex, read [references/codex-runtime.md](references/codex-runtime.md) before
acting; in agy, read [references/agy-runtime.md](references/agy-runtime.md); in grok, read
[references/grok-runtime.md](references/grok-runtime.md) before acting. Apply that adapter's tool, path,
task-persistence, and delegation mappings as overrides to host-specific instructions below.
The five modes and their safety invariants remain unchanged.

Adapt a new host by adding an adapter beside these, never by rewriting the Claude spelling in
place: this one checkout is symlinked live into more than one host.

## Mode routing — decide first

Before doing anything else, identify which mode applies:

| Phrase / context | Mode |
|---|---|
| `/handoff`, "wrap up", "session summary", "close out", "document what we did", "leave notes" | **WRITE** |
| "read handoff", "resume", "where did we leave off", "pick up where we left off", "continue from last session", invoked right after `/clear` | **READ** |
| "save this learning", "remember this", "log this gotcha", "capture this pattern", "add to learnings", "search past learnings" | **LEARN** |
| "hand this over", "hand off <work> to <worktree/repo>", "give this task to another worktree", "transfer this feature", "this belongs to <other repo>'s todo" — **when there is tracked work to transfer** (a parked task, a claimed feature, in-flight state) | **HANDOVER** |
| `/handoff takeover`, "take over", "adopt the handover", "pick up that brief", "claim the inbound work" — **an inbound brief addressed to THIS repo, adopted mid-session** | **TAKEOVER** |

**HANDOVER vs `orca-cli`.** `orca-cli` owns full handoffs and already documents the transport (`worktree create --no-parent --agent … --prompt …`, `terminal send --enter`). Reach for it directly when the ask is "run this prompt over there" — a self-contained instruction with no state behind it. HANDOVER is for when *ownership* moves: there is a claim to release, context that would take a forensic hunt to reconstruct, or a todo that must stop being yours and start being theirs. HANDOVER **composes with** `orca-cli` rather than replacing it — it prepares the brief and releases ownership, then delegates delivery to `orca-cli`'s commands. Never reimplement that transport here.

**Compound requests are WRITE, not a coin flip.** "Wrap up and hand this off to <X>", "close out the session and give the rest to another worktree" name both modes at once. Run **WRITE**, and let its §"Route foreign-worktree work before closing out" step invoke HANDOVER for the items that move. Picking one mode arbitrarily is the failure here: choose HANDOVER alone and the session is never closed out; choose WRITE alone and the transfer silently does not happen.

If still ambiguous, default to **WRITE** for session-end invocations and **READ** for session-start ones.

---

## WRITE mode flags

Parse flags from the invocation before doing anything else. The flags in the table below are
WRITE-only. READ has one flag of its own, `--here` (§"Fresh-context precondition"); it is not
listed here because it is a precondition override rather than a WRITE behaviour switch.

| Flag | Default | Effect |
|---|---|---|
| `--dry-run` | off | Draft the doc and print to stdout; do not save, commit, or run scout. Stop after drafting. |
| `--skip-scout` | off | Skip the automation-scout phase entirely. |
| `--skip-learnings` | off | Skip the "Persist durable learnings" phase. |
| `--skip-memories` | off | Skip the "Update persistent auto-memories" phase. |

### WRITE — stamp an Orca checkpoint (best-effort, Orca only)

After the handoff markdown is written (and not on `--dry-run`), leave a durable, mobile-visible checkpoint on the active Orca worktree so the next session — and the Orca mobile app — sees where this one stopped without opening the doc:

- Gate on substrate: run `hmad-dispatch env`; proceed only if it reports `substrate: orca`. (`hmad-dispatch` is the h-mad wrapper; if it is not on PATH, skip this step.)
- Preserve a foreign note: the worktree comment is a single shared field. First read `.worktree.comment` via `hmad-dispatch worktree-current`. If it is non-empty AND does not already start with `handoff:`, `handover:`, `taken over:` or `h-mad` (i.e. a human wrote it, not a prior stamp), keep it — append the checkpoint after it (`<existing> — handoff: …`) rather than clobbering. An empty comment or a prior skill stamp is replaced outright.
- **Prove the read before acting on an empty result — this is the one destructive instance.** "Comment is empty" and "I could not read the comment" produce the same value and lead to opposite correct actions: the first says replace, the second says do not touch a field you cannot see. A wrong accessor, a non-zero exit, or unparseable output therefore **clobbers a human's note** while looking like the documented happy path. So require the container, not just a falsy value:

  ```python
  d = json.load(sys.stdin)
  if "worktree" not in d or "comment" not in d["worktree"]:
      sys.exit("[handoff] worktree_comment_skipped: could not read comment — refusing to overwrite")
  existing = d["worktree"]["comment"] or ""    # only NOW is empty meaningful
  ```

  Skipping the stamp costs a checkpoint; overwriting costs someone's note. Take the skip. (`worktree`/`comment` are post-unwrap keys — see READ Step 3 and `h-mad/references/agent-substrate.md` §"The `.result` envelope".)

  **All four prefixes, not just `handoff:`.** This skill writes three of them — WRITE stamps `handoff:`, HANDOVER Step 4 stamps `handover:`, TAKEOVER stamps `taken over:` — and HANDOVER's own preserve rule already lists them. A WRITE that knows only `handoff:` treats its sibling modes' stamps as human notes and appends to them, so a worktree accumulates `handover: … — handoff: … — handoff: …` instead of carrying one current checkpoint. Keep this list and HANDOVER Step 4's identical.
- Stamp: `hmad-dispatch worktree-comment active "handoff: <slug> · <status> · next: <next-step>"`, where `<slug>` is the handoff doc's slug, `<status>` a 2–4 word state, `<next-step>` the top Next Step.
- Non-fatal: a non-zero result (no runtime, non-orca, wrapper absent) emits `[handoff] worktree_comment_skipped` and is ignored. The handoff is complete regardless — the checkpoint is an enrichment, never a gate. All Orca access goes through `hmad-dispatch`; never call `orca` directly from this skill.

---

## Reading a handoff (resume mode)

**Read [references/read-mode.md](references/read-mode.md) in full before Step 0a, on every READ entry point** (`/handoff read`, `/handoff resume`, "where did we leave off", a bare "resume"). It holds the fresh-context halt, the remote sync, locating and reading the doc, reconciliation, the mechanical-resolve allowlist, the todo restore ladder and the resume report.

A cross-reference `SKILL.md §"…"` to any of these now resolves in `references/read-mode.md`:

- §"Step 0a: Fresh-context precondition — HALT if the session is not clean"
- §"Step 0b: Terse output mode (best-effort)"
- §"Step 0: Sync local with the remote BEFORE locating/reading"
- §"Step 1: Locate the doc"
- §"Step 2: Read it"
- §"Step 3: Reconcile with reality (silent verification)"
- §"Step 3.5: Take over handed-over work"
- §"Step 3.6: Resolve what is mechanically resolvable — and only that"
- §"Step 4: Restore the todo list"
- §"Step 5: Report back and stop"
- §"Read-mode don'ts"

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
  - 2026-04-30 · gotcha · [0.7] · `lightrag,nan-embed` — qwen3-embedding NaN's on long inputs; substitute random unit vector not zero (L2-norm poisons)
```

Then stop — this is a single-shot operation, not a gateway to more work.

### LEARN-mode don'ts

- Don't write learnings inline into the handoff doc (that's WRITE mode's job with the "Persist durable learnings" step — LEARN mode writes *only* to `docs/learnings.md`).
- Don't add more than one learning per LEARN invocation — if the user has several, tell them and invoke LEARN once per learning.
- Don't pad the kernel toward the 240-character cap to sound thorough — shorter is better.

---

## HANDOVER mode — move ownership to another worktree

**Read [references/handover-mode.md](references/handover-mode.md) in full before running HANDOVER, including when WRITE's §"Route foreign-worktree work before closing out" invokes it as a subroutine.** It holds the claim release, the brief, the worktree stamp, delivery through `orca-cli`, and the landed check.

A cross-reference `SKILL.md §"…"` to any of these now resolves in `references/handover-mode.md`:

- §"Step 1: Name the work and the target"
- §"Step 2: Release ownership BEFORE delivering"
- §"Step 3: Write the brief into the RECEIVER's store"
- §"Step 4: Stamp the target's worktree comment"
- §"Step 5: Deliver — via `orca-cli`, not by reimplementing it"
- §"Step 6: Let go"
- §"Step 7 (optional, later): check ONCE that it landed"
- §"HANDOVER don'ts"

## TAKEOVER mode — adopt a handed-over brief WITHOUT ending the session

**Read [references/takeover-mode.md](references/takeover-mode.md) in full before adopting a brief, whether from `/handoff takeover` or from READ Step 3.5.** It holds the pending-handover scan, the claim, the premise re-check, the `**Taken-Over-By:**` stamp and the report.

A cross-reference `SKILL.md §"…"` to any of these now resolves in `references/takeover-mode.md`:

- §"Step T1: Find what is addressed to this repo"
- §"Step T2: Adopt it"
- §"Step T3: Report, and go back to what you were doing"

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
- 2026-04-28 · HemaSuite/guideline-category-facet · Shipped guideline-category-facet end-to-end via TDD multi-agent cowork · `/Users/kimhawk/Coding/HemaSuite/docs/handoffs/2026-04-28-main__guideline-category-facet.md`
```

Each entry has four pipe-free segments separated by `·`: ISO date, `<project-slug>/<handoff-slug>`, a one-line summary lifted from the doc's Session Summary (≤100 chars), and the absolute path in backticks. Use absolute paths (not `~/`) so a `grep` is unambiguous.

Create the file with a `# Handoffs Index\n\nNewest first. Format: ISO date · project/slug · summary · path\n\n` header block if missing. Don't commit `~/.claude/handoffs/INDEX.md` to any project repo — it's user-global state, not project state.

**If the index has no `- ` bullet yet** (a fresh install, or a file you just created from the header block), there is nothing to insert *before* — append the entry after the header block instead. The anchor rule below assumes at least one existing entry; applying it to an empty index finds no anchor and is how an agent ends up guessing a position or reporting a failure over a file that is simply new.

**How to prepend — anchor on the first list item, never on the header text.** Insert the new entry *immediately before the first existing `- ` bullet line*, so it becomes the newest. Do **not** anchor the insert on the `Newest first. Format:` header string: this file has been observed carrying a duplicate of that line mid-file, and a header-anchored insert lands the newest entry in the middle instead of the top (observed 2026-07-23 — an entry went to line 36). "Before the first `- ` line" is unambiguous no matter how many stray header lines exist. After inserting, verify placement (`grep -n '^- ' INDEX.md | head -1` should return your entry) rather than trusting the write — and if you find a stray `Newest first.`/`Format:` line anywhere below the top block, delete it while you are here; it is corruption that will mis-anchor the next writer. Locate them first, and delete the ones it reports with a normal edit:

```bash
# lists only strays BELOW the first entry — the real header is above it and must survive
# lists only strays BELOW the first entry — the real header is above it and must survive.
# NO positional shell args anywhere in this snippet: one in a skill body is REWRITTEN by the
# slash-command renderer. Measured twice on this very line — it reached the agent as
# `…": "read}` under `/handoff read` and `…": "takeover}` under `/handoff takeover`, while
# the file on disk held the awk whole-record variable, so the command printed the ARGUMENT
# instead of the matching line. A documented command that silently does the wrong thing is
# worse than no command at all.
python3 - <<'EOF'
import pathlib
p = pathlib.Path.home() / ".claude/handoffs/INDEX.md"
seen_entry = False
for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
    if line.startswith("- "):
        seen_entry = True
    elif seen_entry and ("Newest first." in line or line.startswith("Format:")):
        print(f"{p}:{n}: {line}")
EOF
```

Do not pipe that into a blind `sed -i` delete-by-pattern: the same strings appear in the legitimate header block, and a pattern-scoped delete that guesses the header's line range removes it too.

The reason this matters: project-local handoffs are great for versioning and PRs but bad for "what did I work on across all my projects last month" — the index is what makes that question answerable in one command (`head ~/.claude/handoffs/INDEX.md` for recent, `grep <topic> ~/.claude/handoffs/INDEX.md` for search).

---

## Gather context before drafting

Before you write anything, collect these in parallel:

1. **Conversation scan** — walk the current transcript. Note: the task the user brought, decisions made, problems hit, what got fixed, what's still broken, any verification that was skipped.
2. **In-flight tasks** — if you have a TodoList / task tool, read it. Anything pending or in-progress belongs in Open Items. Anything completed this session feeds Session Summary. **This list is session-scoped and is not the backlog** — a session that never ran READ starts empty, so an empty task tool is evidence about *this session*, never about what this branch owes. Item 2b is the part that knows.

2b. **The predecessor handoff** — the doc this one continues, which is where everything owed to this branch actually lives:

   ```bash
   HP="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py"
   python3 "$HP" carry-forward-sources --branch "$(python3 "$HP" branch-slug)"; RC=$?
   ```

   Read **every** path it prints, in full — their **Open / Blocked Items** and unfinished **Next Steps** are the inputs to §"Carry the predecessor's open items forward". The branch's newest handoff is this doc's `**Supersedes:**` value; `RC=1` means there is none and `**Supersedes:**` is `none — first on this branch`. `RC=2` means a doc could not be read: report it, and do **not** write the doc as though nothing were owed.

   It prints **two** kinds of source, and the second is not optional. A handover brief is filed under the *sender's* branch slug, so `latest --branch` cannot see it — the same construction as the READ defect. Once READ Step 3.5 has stamped `**Taken-Over-By:**` the brief also stops appearing in `pending-handovers`, so if the taking session ends before it writes a handoff, the next WRITE on this branch would find an empty task list, no branch predecessor, and no re-offer: the whole taken-over backlog leaves the chain in one hop with nothing raised. So a brief this lane stamped, and that no handoff yet names in `**Supersedes:**`, is a predecessor too — until one does.
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
5. **Live processes** — if the session launched any long-running background work that's still alive at the moment of writing (multi-hour ingests, soak tests, build pipelines, daemons started for testing): capture PID, the exact command (one line), the log path, started-at, elapsed, and a one-line "what to verify on exit". **Write `none` or `stdout` when there is no log file** — plenty of processes were never redirected anywhere. A required-looking column is an invitation to invent a plausible path like `/tmp/job.log`, and a fabricated log is worse than an absent one: the next session tails a file that never existed and concludes the job died. This populates the **In-Flight Processes** section. Skip silently if nothing is in flight — most sessions don't have any. The check costs nothing (`ps -p $! -o pid,etime` for each backgrounded job, or `pgrep -f <substring>` for processes the operator launched manually) and the value to a future resume is enormous: without it, the next session has to reverse-engineer "is this still going?" from log mtimes and ambiguous output.
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
9. **Verify claimed state and files before drafting** — if the handoff mentions an H-MAD feature's ownership state (`released`, `claimed`, or an oracle verdict), run `h_mad_resume_decision.py` and read `owner_session_id` from `docs/.bkit-memory.json` (via `.get()`) before writing "released" or quoting an oracle token, and record the **observed** values in the doc rather than the intended ones. For every file path the handoff claims this session wrote or updated, verify it exists on disk (`ls -la` / `test -s`) before listing it in **Files touched this session** or **Session Summary**.

Do **not** run tests, builds, or long-running commands just to populate the handoff. Use what was already observed in the session. If something wasn't verified, the handoff should say so — that's load-bearing information.

---

## Required template

Use this structure exactly. Every section is required; write "None" (with a one-line reason) rather than omitting a header.

### The header fields

| Field | Written by | Meaning |
|---|---|---|
| `**Date:**` | WRITE | Local `date +%F`, matching the filename's date prefix. |
| `**Branch:**` | WRITE | The branch the work belongs to — under a multi-worktree layout this may differ from the branch you are sitting on. READ Step 4 builds its `[<repo>@<branch>]` todo prefix from this. |
| `**Project:**` | WRITE | Project slug or root path (§"Project slug derivation"). |
| `**Supersedes:**` | WRITE | Every doc this handoff absorbs, comma-separated — the branch predecessor **and** each taken-over brief whose items it carried. **It is a pointer, not a licence to drop what it holds** — see §"Carry the predecessor's open items forward". |
| `**Handover-From:**` | HANDOVER Step 3 | Present only on a brief whose ownership moved from another lane. Makes the brief addressed to this **repo** rather than to a branch, which is why READ Step 1 scans for it separately. |
| `**Taken-Over-By:**` | READ Step 3.5 | Stamped when someone picks the brief up. Its **absence** is what makes a brief show up in `pending-handovers`, so an unstamped brief is re-offered on every resume and a stamped one is never re-adopted. |
| `**Next-Session Focus:**` | WRITE (optional) | One-line statement of the next session's primary goal or starting mode, so the reader can tailor its first action before walking the full backlog. |
| `**Suggested-Skills:**` | WRITE (optional) | Comma-separated installed skills recommended for the next session, each with its purpose (`<skill-name> (<why>)`). Advisory recommendations only: the receiving session still applies current user instructions, checks availability, and routes through its host adapter without assuming every host exposes Claude's `Skill` tool. |

**A field that is read must be defined here.** `**Supersedes:**` was in use across a real handoff chain for weeks while `grep -c -i supersede SKILL.md` returned **0** — the skill neither defined, wrote, nor audited it, and an unspecified convention became the mechanism by which content was dropped: the first doc in that chain to carry it went from 9 backlog mentions to 2, and four hops later to 0. A field nobody specified cannot be relied on, and cannot be checked.

```markdown
# Handoff — <Topic>

**Date:** YYYY-MM-DD
**Branch:** <branch-name or "n/a">
**Project:** <project name or root path>
**Supersedes:** <filenames this handoff absorbs, comma-separated, or "none — first on this branch">

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

**If an item is parked feature-work that lives outside this repo/branch/session** (a separate H-MAD feature, a sibling worktree, another repo), you MUST record where it lives, or the next session cannot find it without a forensic hunt: `repo: <abs path> · branch: <name> · worktree: <path or "none">` plus the key artifact paths (the RED/GREEN/verify prompt files, the plan/spec, the scratchpad dir). "Parked in its own worktree" with no path is the failure mode this line exists to prevent — a resume then has to reconstruct the location from `hmad-dispatch worktree-list`, scratchpad prompts, and telemetry.
  - Example: `Task 3 audit — status: parked. repo: /Users/x/orca/HemaSuite/hematology-paper-writer · branch: feature/191 · worktree: none (merged) · prompts: <scratchpad>/codex_task3_{red,green,verify}.txt`
  - **Recording the location is not the same as handing it over.** If the item belongs to another repo/worktree *and ownership should move with it*, run HANDOVER mode rather than parking it here — a foreign item documented only in this doc is invisible to the session that would actually act on it. See §"Route foreign-worktree work before closing out"; the entry here then becomes a pointer to the brief you wrote there.

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

### Carry the predecessor's open items forward

**An item leaves the chain by being finished or by being handed over, never by not being mentioned.**

Before the doc is final, take the predecessor from §"Gather context" item 2b — the doc named in this one's `**Supersedes:**` — and walk **every** entry in its **Open / Blocked Items** plus every **Next Step** it left unfinished. For each one, this handoff must do exactly one of:

1. **Re-emit it** in Open / Blocked Items, with its status updated. Unchanged is a legitimate status — say "unchanged since <date>" rather than dropping it for being boring.
2. **Record it closed, with a reason** — finished (name the commit or the evidence), withdrawn (say why the premise failed), or handed over (name the receiver, per §"Route foreign-worktree work before closing out").

Silence is not a third option. Nothing anywhere checks whether a handoff mentions what its predecessor did, so an item that goes unmentioned is gone with no error, no diff signal and no one aware.

**Why this cannot be left to the task tool.** §"Gather context" item 2 reads a **session-scoped** list. A session that did not run READ starts with an empty one, and its WRITE then truthfully reports no pending todos while dropping everything a prior session restored. Measured: a 15-item backlog that had been explicitly taken over decayed **9 → 2 → 4 → 1 → 0 → 0 → 0 → 0** across 8 consecutive handoffs on one branch. No hop deleted 15 items; each dropped a few, so any adjacent pair diffed like ordinary scope change. `TaskList` returned `No tasks found` at the start of the session that finally noticed, while the items were nominally owned there.

**If the predecessor cannot be read** — the command errors, the file is unreadable, the store is missing — say so in Open / Blocked Items as an explicit unverified-carry-forward line, and do **not** write the doc as though the predecessor had no open items. "I could not read it" and "it had none" produce the same empty list and lead to opposite correct actions; this is the same fail-closed rule the WRITE worktree stamp and READ Step 3.6 already apply.

**Name every source you consumed in `**Supersedes:**`.** `carry-forward-sources` retires a doc only when a later handoff names it, so a source you read and absorbed but did not name stays in the list forever, on every future WRITE. Three of HemaSuite's four taken-over briefs did exactly that after the 2026-09-01 triage — closed work, yielding nothing when read, permanently in the queue. **A queue that only grows is abandoned exactly as fast as one that silently empties**, and the abandoned queue is where the next dropped handover hides. So a source leaves the list the same way an item leaves the chain: because a handoff proved it absorbed it, never because nobody mentioned it.

The mirror rule matters just as much: name **only** what you actually consumed. Listing a brief you did not read retires it on a false claim, and it is then invisible to every later WRITE — the original defect, reached through the field built to prevent it.

**Inherited items keep their origin.** An item that arrived from another lane keeps its `**Handover-From:**` attribution and its location block (`repo: … · branch: … · worktree: …`) as it moves down the chain. Stripping the origin makes it unresolvable two hops later, which is the same loss as dropping it, spread over more documents.

---

## Writing guidance

- **Session Summary**: 2–5 sentences max. Outcome-first (done/partial/blocked). No narrative.
- **Key Learnings**: non-obvious only. If a fresh reader could derive it from the code or git log, omit it.
- **Next Steps**: concrete + ordered. Each item must have a file path or a command. Vague actions ("look at the auth module") are not Next Steps.
- **Open / Blocked Items**: name blockers explicitly. "Blocked on X" is useful. "In progress" alone is not. Parked work outside this repo/branch/session must carry its `repo · branch · worktree` and key artifact paths (see the template note) — a location-less parked item is a forensic hunt for the next session.
- **In-Flight Processes**: omit if nothing is alive. If present, every row needs all seven columns.
- **Context for Next Session**: the resume command should work. Test it mentally — if a future session ran exactly those commands in that order, would they be in the right state?
- **Redaction check (before saving, indexing, stamping, or delivering)**: never copy secret values, API keys, bearer tokens, passwords, or private credentials from commands, environment dumps, or logs into the handoff file, `~/.claude/handoffs/INDEX.md`, Orca worktree comments, or HANDOVER briefs and delivery prompts. Preserve references to credential variable names (e.g. `$API_KEY`) or secret file locations (e.g. `~/.config/...`, `.env`) when needed for resumption.
- **Reference artifacts instead of duplicating bodies**: link to committed specs, plans, ADRs, issues, commits, and diffs rather than pasting their full contents into explanatory prose, while still keeping an explicit entry (status, origin, location, and next action or closure evidence) for every inherited obligation under §"Carry the predecessor's open items forward".

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
3. Proceed to §"Route foreign-worktree work before closing out" — do this before the phases below, because it can change what the doc's Open Items say.
4. Proceed to §"Persist durable learnings" if Key Learnings is non-empty and `--skip-learnings` was not set.
5. Proceed to §"Update persistent auto-memories, then automation scout" — it routes to `references/auto-memories.md` (unless `--skip-memories`) and `references/automation-scout.md` (unless `--skip-scout`).
6. Proceed to §"Commit and push".

---

## Route foreign-worktree work before closing out

Walk the Open / Blocked Items and ask of each: **does this belong to the repo/worktree I am closing out?**

Recording an item's `repo · branch · worktree` (§"Required template") makes it *findable*. It does not make it *found*. READ mode resolves the canonical store of the repo it is invoked in, so an item parked in this doc about another repo is invisible to that repo's next session — the only reader who would act on it. They would have to already know to go looking in a different project's handoffs, which is the forensic hunt the location rule exists to prevent, just moved up a level.

So for each item that belongs elsewhere, pick one deliberately:

- **Ownership should move** → run **HANDOVER mode** for that item now, before finishing this doc — **as a subroutine you return from.** HANDOVER ends with "let go / stop monitoring", which means stop watching the *receiver*; it does not end this WRITE. Come back and finish the remaining steps (learnings, memories, scout, commit and push). Then record the item here as *handed over*, naming the brief you wrote and where it went — the sender's doc becomes a pointer, not a parking space.
- **Ownership stays here** (you are still driving it; the other repo is only where the files live) → keep it as a normal Open Item with its location block. This is the common case for a feature you are working *from* this session across two checkouts.

Do not skip the question because the item is well documented. The failure this step exists to catch is a *good* entry in the wrong doc: a session closed out with a foreign task neatly described, its location recorded, and no one on the receiving side ever told. Observed 2026-08-03 — a Task 5 item belonging to a HemaSuite worktree sat in a skills-repo session's list, fully specified, and only moved because a human noticed it did not belong there.

If the item is a claimed feature, HANDOVER's release step matters here specifically: closing out a session while still holding an advisory claim leaves the receiver inheriting a lock from a session that has stopped.

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

## Update persistent auto-memories, then automation scout

Two WRITE phases live in reference files rather than here. They are real steps, not optional reading — but they run once, at the end, and carrying ~100 lines of their rules on the critical path dilutes attention on the reconciliation and handover checks that decide whether a handoff is correct at all.

- **Auto-memories** (unless `--skip-memories`) — read `references/auto-memories.md` and follow it. This is what makes a durable fact surface in *future* sessions; `docs/learnings.md` alone does not.
- **Automation scout** (unless `--skip-scout`) — read `references/automation-scout.md` and follow it. It **reconciles the open `docs/skill-candidates.md` rows before appending new ones**, not just appends: this scout is the only thing that writes that file, so a status nobody flips decays until the whole backlog has to be re-derived by hand (measured: 4 of 5 open rows described already-shipped work).

Read the file at the moment you run the phase. Doing it from memory is how a phase quietly degrades into a summary of itself.

---

## Commit and push (default finale)

After the handoff doc is written and learnings are persisted, commit and push unless the user explicitly says not to.

### Pre-flight (run before staging)

```bash
git status --short          # confirm only handoff + learnings files are staged
git diff --stat HEAD        # sanity-check scope
```

### Commit

Stage the **actual absolute paths** written in §Save, not a cwd-relative `docs/handoffs/…` — under a linked worktree the cwd path points at the wrong tree and would stage nothing.

This block re-derives `HP` rather than inheriting it from §Save: **shell variables do not survive
between tool calls**, so `$HP`, `$DIR` and `$BR` set back there are already empty here. An empty
`HP` used to be the dangerous case rather than the loud one — it made `ROOT` empty, and a
hand-written branch then concluded "linked worktree" and skipped the commit *on the main
worktree*, reporting the skip as correct behaviour. That branch is gone: routing now happens inside
`handoff_commit.py`, which reads the repo itself, so an empty `HP` can only fail as a missing
script path. Re-deriving `ROOT` and `LEARN` is safe because both are pure functions of the repo. `$FILE` is **not** — §Save's concurrency guard may
have appended a `-2`/`-<HHMMSS>` discriminator, so re-deriving it would name a file that does not
exist. Substitute the literal path §Save actually wrote.

```bash
HP="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py"
ROOT="$(python3 "$HP" root)"                 # canonical main-worktree root
LEARN="$(python3 "$HP" learnings)"
echo "$ROOT" "$LEARN"                        # carry these forward as literals too
```

Route the commit through **`handoff_commit.py`** rather than branching on `ROOT` by hand. It reads
the same repo state and picks one of three destinations — and **every one of them ends with the
file reachable from a ref**, which the hand-written branch this replaced did not:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_commit.py" \
  "<the handoff path §Save wrote>" "<the learnings path echoed above>" \
  -m "chore(handoff): YYYY-MM-DD <slug>

Session closeout: <one-line summary from Session Summary>."
```

Add the absolute `docs/skill-candidates.md` under the canonical root as a third path only if scout
ran. Paths that do not exist are dropped, so `--skip-learnings` needs no special-casing. Pass the
**literal** paths, not `$FILE`/`$LEARN` — this is a separate tool call and shell variables do not
survive between them.

| canonical-root state | destination |
|---|---|
| it **is** this worktree | normal commit on the current branch (`main`) |
| linked worktree; canonical tree clean and on its default branch | normal commit **there** (`direct`) |
| linked worktree; canonical tree dirty or off-default | commit onto `refs/handoffs/<branch-slug>` through a throwaway index, then push to `origin` as `handoff/<branch-slug>` (`ref`) |

`ref` mode is what closes the loop. It moves no HEAD, stages nothing and touches no working tree,
so the objection that used to make this step decline the commit — the main worktree may be mid-work
on an unrelated branch — no longer costs the doc. **What happened before it existed:** the decline
was the last thing that ever happened to the file. WRITE reported success, the doc was on disk, the
INDEX entry was written, the learnings landed; only `git log --all -- <path>`, which nothing
prompted anyone to run, showed zero commits. Three docs became orphans that way on 2026-08-29.

For **`main` only**, the script commits but does not push — continue to §Sync and §Push below.
For `direct` and `ref` the script has already pushed and you must **skip §Sync and §Push**: those
commands carry no `-C`, so they act on the session's cwd. In `main` mode that is the canonical tree
and they are correct; from a linked worktree they would inspect, rebase and push **this** worktree's
feature branch while the report claimed the handoff was pushed — leaving the handoff commit
unpushed on the canonical branch, which is the original silent failure wearing a new hat. A failed
push does not fail the closeout either way: the commit is local and the file is still referenced.

To land a `ref`-mode handoff on the default branch later, `git cherry-pick` the commit the script
names. Never `git merge` the ref — its first commit is parented on whatever the canonical tree's
HEAD happened to be, which can be an arbitrary stale feature tip.

Do not use `git add -A` — only the handoff and learnings files.

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
