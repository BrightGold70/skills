---
name: handoff
description: Use this skill in four modes. WRITE mode — create a session handoff document, end-of-session summary, session closeout, wrap-up doc, or notes for the next session — produces a project-local markdown handoff at docs/handoffs/YYYY-MM-DD-<slug>.md capturing session summary, key learnings, next steps, open/blocked items, and resume context, aimed at future-you opening a fresh Claude Code session. READ mode — resume work after /clear or at the start of a fresh session by loading the most recent handoff, reconciling its state with the working tree, and restoring the todo list (a task tool where one exists, else OMC's durable `.omc/notepad.md`, else an inline checklist in the report — the step never no-ops, and always names the sink it used); READ halts before doing anything when the session is not fresh, printing the `/clear` + re-invoke sequence for the user to run (no tool can trigger /clear), and switches output to caveman-ultra when that skill is installed. When running under Orca, WRITE also stamps a durable, mobile-visible checkpoint on the active worktree and READ reconciles against Orca's worktree model (both best-effort via `hmad-dispatch`, skipped cleanly when Orca is absent). LEARN mode — record a single durable cross-session learning to <project>/docs/learnings.md via the bundled scripts/learn.py (no external skill or plugin dependency); also exposes a search command for grep-style retrieval across past learnings. Invoke for WRITE whenever the user says /handoff, "handoff", "session summary", "wrap up session", "close out session", "document what we did", "leave notes for next time"; invoke for READ whenever the user says "read handoff", "/handoff resume", "load handoff", "resume from handoff", "where did we leave off", "pick up where we left off", "continue from last session", or any variant about loading prior session state — especially right after /clear; invoke for LEARN whenever the user says "save this learning", "remember this for next time", "log this gotcha", "capture this pattern", "add to learnings", "this is a recurring issue, save it", "what learnings do we have on X", "search past learnings for Y", or any variant about recording or retrieving durable cross-session knowledge outside a full handoff. Use this skill whether or not the exact word "handoff" appears, and prefer LEARN mode for single-shot lesson capture, READ mode when phrasing is about *picking up* prior state, and WRITE mode when *closing out* a session. HANDOVER mode — move ownership of tracked work to ANOTHER worktree, repo, or agent: writes the brief into the RECEIVER's canonical store (`handoff_paths.py --repo <target>`), releases any advisory claim so the receiver never has to reach for `--force`, stamps the target's Orca worktree comment, then delegates delivery to the `orca-cli` skill's Full Handoffs commands and stops monitoring. Invoke for HANDOVER whenever the user says "hand this over", "hand off X to <worktree>", "give this task to another worktree/repo/agent", "transfer this feature", "this belongs to <other repo>'s todo", or otherwise moves OWNERSHIP of work that has state behind it — a parked task, a claimed feature, or in-flight context. Use the `orca-cli` skill directly instead when the ask is merely to run a self-contained prompt elsewhere with no ownership or state to transfer, and the `orchestration` skill when the user wants the work supervised, waited on, or tracked to completion.
---

# Handoff

## Mode routing — decide first

Before doing anything else, identify which mode applies:

| Phrase / context | Mode |
|---|---|
| `/handoff`, "wrap up", "session summary", "close out", "document what we did", "leave notes" | **WRITE** |
| "read handoff", "resume", "where did we leave off", "pick up where we left off", "continue from last session", invoked right after `/clear` | **READ** |
| "save this learning", "remember this", "log this gotcha", "capture this pattern", "add to learnings", "search past learnings" | **LEARN** |
| "hand this over", "hand off <work> to <worktree/repo>", "give this task to another worktree", "transfer this feature", "this belongs to <other repo>'s todo" — **when there is tracked work to transfer** (a parked task, a claimed feature, in-flight state) | **HANDOVER** |

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

### Step 0a: Fresh-context precondition — HALT if the session is not clean

Run this before everything, including Step 0. A resume is a *replacement* of context, not an
addition to it: the handoff exists precisely because the prior session's working assumptions
should not survive into the next one. Reading one into a session that is already loaded gets you
the worst of both — stale assumptions from the live conversation silently outranking the
document you just read, and no signal that it happened.

**This applies to every READ entry point, not to a literal `/handoff read`.** `/handoff resume`,
"load handoff", "where did we leave off", "pick up where we left off", "continue from last
session", a bare "resume" — anything the §"Mode routing" table sends to READ arrives here first.
Routing decides the mode; the mode decides the steps. There is no path into Step 0 that skips 0a.

**Fresh** means the resume request arrives at the start of the session: no substantive prior work
in this conversation — no edits, no builds, no unrelated investigation. Being invoked right after
`/clear` is the canonical case.

If the session is **not** fresh, stop here. Print this and do nothing else — do not sync, do not
locate, do not read:

```
Resume needs a clean context. Run:

    /clear
    <the invocation they used>
```

**Echo back the invocation they actually used** — `/handoff resume` if that is what they typed,
`/handoff read` if that is. Handing someone a command they did not use reads as a correction and
invites them to wonder whether the two differ (they do not; both route to READ). If the trigger
was prose rather than a command — "where did we leave off" — print `/handoff read`, which is the
shortest thing that gets them back here.

Then wait. The user runs those two lines and READ re-enters at Step 0a with a fresh session,
which passes silently.

**Override**: if the user has explicitly asked to resume in place — "resume here", "don't clear",
"resume in place", or a `--here` flag — skip the halt, and say in the Step 5 report that the
resume ran against an existing context so they know which state won any conflict. Never infer the
override from impatience or from a repeated invocation; it has to be asked for.

### Step 0b: Terse output mode (best-effort)

Once Step 0a passes, invoke the caveman skill at ultra intensity before locating anything:

```
Skill(skill: "caveman:caveman", args: "ultra")
```

A resume report is dense reference material the user scans rather than reads, which is what that
mode is for. It applies to the report and to the rest of the session; the user reverts with
`stop caveman` or `/caveman full`.

This is **best-effort and never a dependency**. If the skill is not installed the invocation
fails — proceed to Step 0 silently and say nothing about it. READ must work identically on a
machine that has never heard of caveman.

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
3. **Repo-wide newest in the canonical store** — `python3 "$HP" latest` (no `--branch`). Use when this branch has none. If it matches a *different* branch, say so and confirm with the user before resuming — you may be picking up a sibling worktree's work. **Exception: a brief carrying `**Handover-From:**` is addressed to this repo, not to a branch.** A sender names the file for the branch they were told to target, so a handover routinely lands as `…-main__…` while you sit on a feature branch — check 2 then returns nothing and this check finds it under a "different branch" that is not a sibling's work at all. Do not treat that as a suspicious pickup: read it, and go to §"Take over handed-over work". Observed live 2026-08-03 — an inbound five-item handover was invisible to check 2 for exactly this reason.
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
- **PR state** — if the doc's Next Steps or Open Items name a PR (`#N`, "merge PR", "waiting on review"), check it before restoring that todo. A PR claim is the one piece of handoff state that lives entirely off the local machine, so every other check in this list passes while it is stale — and "merge PR #18" survived into a resume as the top Next Step when #18 had merged hours earlier. Both halves, because a squash-merge lands under a rewritten title and `gh` may be unavailable or unauthenticated:
  ```bash
  gh pr view <N> --json state,mergedAt,title 2>/dev/null   # OPEN | MERGED | CLOSED
  git log --oneline -50 | grep -F '(#<N>)'                 # squash title fallback
  ```
  Merged or closed → say so and drop the todo rather than restoring it. If `gh` errors (no CLI, not authenticated, not a GitHub remote), fall back to the `git log` grep and say the PR state is unverified — do **not** silently assume it is still open.
- **Remote ↔ local sync** — Step 0 already fast-forwarded the clean-behind case before reading; this bullet re-checks and covers what Step 0 deliberately skipped (dirty/diverged/ahead). The working tree may have moved on the remote since the handoff (another machine, a teammate, a CI bot, or a `/handoff` WRITE push from a different session). Before the user starts any new action, reconcile against the remote so they don't branch off a stale base:
  - `git fetch` (quiet; if no remote or no upstream, skip this bullet silently — `git rev-parse --abbrev-ref @{u}` errors → no upstream).
  - `git rev-list --left-right --count @{u}...HEAD` → `<behind>	<ahead>`.
  - **In sync** (0 behind, 0 ahead): state "in sync with `<upstream>`" on one line; no action.
  - **Behind, clean tree**: normally impossible here — Step 0 already fast-forwarded this exact case, so reaching it means the remote moved *while you were reading the doc*. Treat it as such: `git pull --ff-only` again and report the new HEAD. (If Step 0 was skipped because there was no upstream, this bullet does not apply either.) Seeing it a second time is information, not a contradiction.
  - **Behind, dirty tree** OR **diverged** (behind > 0 AND ahead > 0): do NOT auto-pull — flag it ("N behind / M ahead, uncommitted changes present" or "branches have diverged — rebase/merge needed") and let the user resolve. A surprise merge/rebase mid-resume is worse than a one-line warning.
  - **Ahead only** (unpushed local commits): flag as information ("M local commits not yet pushed") — relevant because the prior session may have committed without pushing.
- **In-flight processes** — for each PID cited in In-Flight Processes / Open Items / Next Steps, run `ps -p <PID> -o pid,etime,stat`. For each cited log path, `ls -la <log>` to read size + mtime. Surface one of: "still running, N min elapsed (matches handoff trajectory)" / "exited" / "log unchanged for N hours — likely dead, treat as historical". This is the single most load-bearing reconciliation when the handoff hands off live work; never skip it. If the doc is days old, treat all in-flight claims as historical without bothering to check `ps` (the PID has been recycled and reporting on a stranger's process is worse than silence).
- **Parked-item location** — if an Open/Blocked item is parked feature-work whose `repo · branch · worktree` the doc did NOT record (an older handoff, before this was required), recover the location before restoring its todo instead of guessing: check `hmad-dispatch worktree-list` (a child worktree's `childWorktreeIds`/comment — `worktree-ps` is a compact orchestration summary and does not carry them), the session scratchpad for `codex_*_{red,green,verify}.txt` (H-MAD TDD prompts carry `REPO:`/`BRANCH:`/`FEATURE:` verbatim), and `.h-mad/telemetry.jsonl` for the feature's last phase. Also reconcile whether the parked branch has since merged — "parked, nothing committed" can be stale, and the owed work may now be verification-only on the merged code. Resolve the default branch rather than assuming `main`, then check both directions:

  ```bash
  DEF="$(git -C <repo> symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)"
  DEF="${DEF#origin/}"; DEF="${DEF:-main}"      # falls back only when the remote HEAD is unset
  git -C <repo> branch --merged "$DEF" | grep -F <branch>   # did the branch land?
  git -C <repo> log --oneline "$DEF" -S'<feature symbol>'   # did the code land some other way?
  ```
- **Worktree split** — if the handoff path is inside `.claude/worktrees/<name>/`, the doc was written from a worktree. Run `git -C <worktree-root> rev-parse --abbrev-ref HEAD` AND `git -C <parent-repo> rev-parse --abbrev-ref HEAD` — both trees have independent state and both matter. The handoff's "Branch:" field usually refers to the *worktree*; the parent repo may be on a deferred-cleanup branch (the handoff often calls this out). State each tree's branch on its own divergence line if they disagree with the doc.
- **Orca worktree reconcile** (Orca only) — if `hmad-dispatch env` reports `substrate: orca`, reconcile against Orca's worktree model, which persists across sessions and the mobile app where git+PID state does not:
  - `hmad-dispatch worktree-current` → the payload is `{"worktree":{…}}`; read `.worktree.branch`, `.worktree.path`, `.worktree.comment`. Compare branch/path to the doc's Branch/worktree — **but `.worktree.branch` is a full ref (`refs/heads/main`) while the doc and `git rev-parse --abbrev-ref HEAD` use the short name (`main`), so strip the `refs/heads/` prefix before comparing** or every resume reports a phantom mismatch. A genuine mismatch is a divergence line (you may be in the wrong worktree). `.worktree.comment` is the last checkpoint the writing session left (see WRITE stamp) — quote it if present.
  - `hmad-dispatch worktree-ps` → the payload is `{"worktrees":[…],"totalCount","truncated"}`; iterate `.worktrees[]` and list each as `<.branch> · <.comment>` (branch is again a full ref — strip `refs/heads/`) so in-flight siblings (parallel agents, queued fanout modules) are visible before you act. If `.truncated` is true, say so — the list is capped (raise the cap with `worktree-ps --limit <n>`).

    **Assert the `worktrees` key before reporting a count.** "0 siblings" and "I read the wrong key" produce identical output, so a bare count is not evidence until the container is proven present — report `container missing` as its own outcome, distinct from an empty list:

    ```python
    d = json.load(sys.stdin)
    if "worktrees" not in d:          # NOT `d.get("worktrees", [])` — that silently becomes 0
        print("worktree-ps: container missing — not an empty list", file=sys.stderr)
    else:
        for w in d["worktrees"]: ...
    ```

    **These paths are post-unwrap.** `hmad-dispatch` emits the contents of orca's `.result` envelope, which is why `worktrees`/`worktree` are read at top level here. Raw `orca … --json` nests them under `.result` (`.result.worktrees[]`, `.result.terminals[]`), so a snippet copied from this bullet onto a raw `orca` call measures nothing and says `0`. Full rule: `h-mad/references/agent-substrate.md` §"The `.result` envelope — assert the container before reading a count".
  - Read-only: use only `worktree-current`/`worktree-ps`/`worktree-list` (the last one is what the Parked-item bullet above uses for `childWorktreeIds`); never `worktree-comment`/`create`/`rm` here, and never call `orca` directly. A non-zero result emits `[handoff] worktree_reconcile_skipped` and the reconcile falls through to the git+PID checks above unchanged.

A divergence is not a failure — it's just information the user needs before acting. State each one as a single sentence.

### Step 3.5: Take over handed-over work

Skip this unless the doc carries a `**Handover-From:**` line. If it does, the work arrived from another lane and READ's default behaviour is **half a protocol**: it restores the todos and never claims anything. The sender released ownership and stopped watching; if you do not take it, the feature is owned by nobody, and a third session can start the same work without either of you seeing a collision.

**1. Claim it — this is the step with no other home.** If the brief names a feature, locate the
state file the same way HANDOVER Step 2 does — canonical path first, then `find`; never a `**/`
glob, never `2>/dev/null`, never `head -1`. All three fail-opens are documented there, and all
three end in the same false "nothing is claimed":

```bash
STATE="./docs/.bkit-memory.json"
if [ ! -f "$STATE" ]; then
  ERR=$(mktemp)
  HITS="$(command find . -name .bkit-memory.json -path '*/docs/*' -not -path '*/.git/*' 2>"$ERR")"
  RC=$?
  N=$(printf '%s' "$HITS" | grep -c .)
  if [ "$RC" -ne 0 ] && [ "$N" -eq 0 ]; then
    echo "SEARCH FAILED — NOT 'nothing is claimed':"; cat "$ERR"; exit 1
  fi
  case "$N" in
    0) STATE="" ;;
    1) STATE="$HITS" ;;
    *) printf 'AMBIGUOUS — %s state files:\n%s\nPick the repo-root one by hand.\n' "$N" "$HITS"
       exit 1 ;;
  esac
fi
echo "${STATE:-no state file}"
```

A **failed** search is not an empty one, and more than one hit is not a reason to take the first —
this repository has three. No state file means nothing is claimed: say so, skip to point 2, and do
not invent one. Otherwise pass the path it printed:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_resume_decision.py" \
  --state "<the path the find printed>" \
  --feature "<feature>" --session-id "<your-session-id>"
```

- `owned_elsewhere` → someone **live** holds it. Do not take it; surface the collision. The handover may have raced another session, and that is a real finding, not a formality.
- anything else → claim it:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_state_write.py" \
  "<the path the find printed>" --feature "<feature>" --claim "<your-session-id>"
```

A stale claim is takeable by plain `--claim` — reach for `--force` only against a **live** owner, which the oracle just told you there isn't. If the brief says a claim was left deliberately unreleased (a dead session's), that is the one it means; taking it is your decision to make and now is when you make it.

**2. Verify the premises before adopting them.** A brief is a claim about the world made by a session that has stopped. Its reproduce commands are the cheap part — run them. Any premise that no longer holds becomes a divergence line, not a todo. A confident brief is not evidence.

**3. Restore the todos with their ORIGIN, not yours.** Continue to Step 4, but prefix from the brief's `**Handover-From:**` and location block rather than the branch you are sitting on — the work belongs where the sender said it does.

**4. Acknowledge, so the transfer is visible.** Re-stamp the worktree comment from `handover: …` to something that says it was picked up (`taken over: <slug> · <state> · next: <next-step>`). The sender is not watching; this stamp and your claim are the only records that the handover completed rather than fell on the floor.

**Do not** silently work a handed-over item without claiming it. That is the failure this step exists for: the sender let go, you started, and the state file says nobody owns it.

### Step 4: Restore the todo list

Repopulate todos from the doc's **Next Steps** and **Open / Blocked Items**. Each Next Step becomes a `pending` task with the cited path/command in the description. Each Open/Blocked Item becomes a `pending` task tagged with its blocker if any. Do this even if Next Steps is short — the point is that the user can start on item 1 without re-typing the list.

**Take the first sink that exists — this step must never be a no-op.** A todo-authoring tool is *not* guaranteed, and — the part that matters — **its presence varies between sessions on the same machine**, so this is a live check every time, never a fact you carry from the last resume. `TaskCreate` was in daily use here through 2026-08-19 — last invocation `2026-08-19T07:11:39Z`, then **zero** calls on 08-20 and 08-21 — and was gone the next morning under Claude Code 2.1.236, with no config change; it may equally be back tomorrow. **Do not treat the call count as a fixed figure.** An earlier pass recorded 465 calls; a re-count on 2026-08-21 across 2,734 transcripts returned 429. Neither is obviously wrong — they did not count the same thing — and a corpus count shrinks as transcripts age out. The load-bearing facts are the last-seen timestamp and the run of zeroes after it, not the total. An instruction that names one task tool unconditionally silently restores nothing while every other part of READ succeeds — the reconciliation reads correct, the action queue evaporates, and the report says neither.

**Probe it, do not infer it.** Your own tool list plus one `ToolSearch` is the only authority — and that probe is sound because **`ToolSearch` is not deferred-only**. Its description is written about deferred tools, which invites the worry that an empty result merely means "loaded, so not in the deferred list" — a false negative that would send you past a rung-1 tool you actually have. Measured 2026-08-21: `ToolSearch select:Bash,Read,Write` returns full schemas for tools already in the main tool list, so it resolves non-deferred tools too and an empty `select:` result is genuine absence. Two further ways to get this wrong, both measured 2026-08-20:

- **Absence of calls is not absence of the tool.** Grepping transcripts for `TaskCreate`/`TodoWrite` counts *use*; a session where the tool existed and went unused is byte-identical to one where it never existed. The report that opened this defect concluded "no todo tool on this machine" from zero `TodoWrite` hits — while `TaskCreate`, the name actually in use, had hundreds (the exact total is not the point — see the caveat above). The conclusion happened to be right for that session and the method could not have shown it.
- **A mention is not a tool.** `TodoWrite` appears in plugin hook matchers and in agent catalogs declaring subagent toolsets (`(Tools: …, TodoWrite, …)`). Grepping the name finds it everywhere and proves nothing about your main loop. Distinguish `"name":"TodoWrite"` inside a `tool_use` block from prose.

**When the probe comes back empty, try the opt-in BEFORE the ladder.** The todo tools became **opt-in** in Claude Code **2.1.236** — they were gated, not removed: all four names (`TaskCreate`, `TodoWrite`, `TaskUpdate`, `TaskList`) are still in the 2.1.238 binary, behind the `CLAUDE_CODE_ENABLE_TODO_TOOLS` launch option. Setting it in the `env` block of `~/.claude/settings.json` restores rung 1 for every session:

```json
{ "env": { "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1" } }
```

Measured 2026-08-21 by control/treatment: without it the probe answers `NOTOOL`; with it the transcript carries a real `TaskCreate` `tool_use`. (An earlier revision of this section asserted the opposite — *"no user config can add a built-in tool"* — and told the reader not to try. That was wrong, and it cost a resume: the ladder degraded to the notepad while rung 1 was one setting away. A separate user setting, `todoFeatureEnabled`, governs the TUI **panel** and is not the same switch; enabling only that leaves the tools absent.)

Only if the opt-in is unavailable or does not take effect, walk the ladder:

1. **A task/TodoList tool**, if one is in your tool set (`TaskCreate`, `TodoWrite`, or equivalent). Check this session, not your memory of the last one. If it is not in your loaded tools, one `ToolSearch select:TodoWrite,TaskCreate,TaskUpdate,TaskList` settles whether it is merely deferred; empty there means genuinely absent and you move to rung 2 without further hunting. **Prefer this rung when it exists** — it is the only sink the user can see and tick off in the UI, which is what they mean by "the todo list".
2. **OMC's notepad**, when that MCP is present — `mcp__plugin_oh-my-claudecode_t__notepad_write_working` writes to project-scoped `.omc/notepad.md`, which survives `/clear` and is pruned at 7 days. This is the only rung that is *durable*, so prefer it over rung 3 whenever it is available, and use it **in addition to** rung 1 when the work will outlive this session. Verified live 2026-08-20: the write lands in `.omc/notepad.md`, which `.gitignore` already covers, so it never pollutes the repo. **Its entry header is stamped in UTC**, while handoff filenames use local `date +%F` — east of UTC those disagree by a day for most of the morning (measured: notepad `### 2026-08-19 22:49` written at 07:50 KST on 2026-08-20). Do not read a notepad entry as older than the handoff it came from on the strength of that header.
3. **An inline numbered checklist in the Step 5 report.** Always reachable, so the ladder cannot bottom out. It is also the weakest: it lives only in scrollback, so say so when this is the sink you landed on.

**When rung 1 is unavailable, print the inline checklist IN ADDITION to whatever durable rung you used.** Rung 2 is durable but *invisible*: the user cannot see it, tick it off, or watch it shrink, so a resume that writes there and reports only `**Todos restored:** N` reads to them as "my todos disappeared" — reported by the operator on 2026-08-21 after a resume put 6 items in `.omc/notepad.md`. Both halves of that report were true and neither showed the user their queue. Durability and visibility are different properties and rung 2 supplies only the first.

Whichever rung you land on, **every rule below still applies** — the `[<repo>@<branch>]` prefix, the `[verify path …]` note, and the dedupe rule are properties of the todos, not of the sink.

**Prefix every restored todo with `[<repo>@<branch>]`** so that when todos from multiple worktrees/repos/handoffs coexist in one list, each one names its origin at a glance. `<repo>` is the project slug (§"Project slug derivation" — CLI name, else git-remote basename, else repo dir name); `<branch>` is the handoff doc's **Branch:** field (the branch the work belongs to, which under Orca multi-worktree may differ from the branch you resumed on). Example: `[skills@main] Verify report-file transport …`, `[HemaSuite@feature/12] Add _orca_json guard …`. If the doc's Branch is "n/a", use `[<repo>]` alone. Keep the prefix outside any inline reconciliation note (below) — prefix first, then the task, then any `[verify path …]` note.

If the doc's Next Steps reference a file that the reconciliation pass flagged as missing or moved, mark that task with an inline note (e.g., "[verify path — file moved since handoff]") rather than dropping it.

**Dedupe overlapping items.** It's normal for an in-flight piece of work to appear in both Next Steps ("monitor PID N") and Open Items ("PID N still running") — same thing, two framings. Make one Todo, not two. Same for "verify the 14 placeholder dates" appearing in both lists. Combine the descriptions and merge.

### Step 5: Report back and stop

After reconciliation and the todo restore, give the user a brief resume report.

**Name the sink Step 4 used, on its own line.** `**Todos restored to:** <task tool | .omc/notepad.md | this report only>`. Without it, a restore that reached a durable list and one that reached nothing at all print the same `**Todos restored:** N items` — which is exactly how the missing-tool failure stayed invisible. When the sink was "this report only", the checklist below it *is* the todo list: write it out in full rather than truncating to the first item, because nothing else holds it.

```
## Session resumed

**Handoff:** docs/handoffs/2026-04-30-main__lightrag-guideline-rag.md
**Branch:** main (matches)
**Remote:** 2 behind origin/main → fast-forwarded to `a1b2c3d`
**Uncommitted changes:** 2 files (matches handoff)

**Divergences:**
- PID 37219 (compile_guidelines_db): exited — log mtime 3h ago. Treat as complete; verify output.
- `protocol/sections/background.md` cited in Next Steps — file not found (may have been renamed).

**Todos restored:** 4 items. **Restored to:** `.omc/notepad.md` (no task tool in this install). Starting at:
1. [guideline-rag@main] Verify compile_guidelines_db output (`yq '.documents | length' MANIFEST.yaml` ≥ 55)
```

When the doc was a handover (§"Take over handed-over work"), say so on its own line and name what you did about ownership — a takeover that is not reported looks identical to an ordinary resume, and the sender is not watching to notice:

```
**Handover:** from HemaSuite@feature/196 (session 73aae80d) — claimed as <your-session-id>.
**Premises re-verified:** 3 of 5 hold; 2 changed (see divergences).
```

Then stop. Don't start executing tasks — the user reads the report and decides what to do first.

### Read-mode don'ts

- Don't run Step 0a's halt check *after* doing work — it is the first action of READ, ahead of the
  remote sync. Syncing, locating and reading a doc you are about to tell the user to discard by
  `/clear` wastes the round trip and, worse, half-loads the context the halt exists to keep clean.
- Don't offer to run `/clear` yourself. It is a built-in CLI command with no tool behind it — only
  the user can trigger it, and it would wipe this skill mid-run. Print the two lines and wait.
- Don't let a missing caveman skill (Step 0b) fail the resume, and don't announce its absence.
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
  - 2026-04-30 · gotcha · [0.7] · `lightrag,nan-embed` — qwen3-embedding NaN's on long inputs; substitute random unit vector not zero (L2-norm poisons)
```

Then stop — this is a single-shot operation, not a gateway to more work.

### LEARN-mode don'ts

- Don't write learnings inline into the handoff doc (that's WRITE mode's job with the "Persist durable learnings" step — LEARN mode writes *only* to `docs/learnings.md`).
- Don't add more than one learning per LEARN invocation — if the user has several, tell them and invoke LEARN once per learning.
- Don't pad the kernel toward the 240-character cap to sound thorough — shorter is better.

---

## HANDOVER mode — move ownership to another worktree

WRITE leaves a note for whoever picks this lane up next; that is usually future-you, same branch, same repo. HANDOVER is the cross-lane case: the work stops being yours and starts being someone else's, *now*. The difference matters because two things can go wrong here that WRITE never faces — the brief can land in a store the receiver never reads, and ownership can stay pinned to you after you have walked away.

### Step 1: Name the work and the target

Establish, before writing anything: **what** is moving (the task, feature, or todo), and **where** it goes as `repo · branch · worktree`. If the target is ambiguous — several worktrees could plausibly own it — ask rather than guess. A brief filed against the wrong branch is invisible to the receiver's resume even when it sits in the right directory, because READ matches the branch slug exactly.

### Step 2: Release ownership BEFORE delivering

This is the step with no other home, and the one whose absence is silent.

**First find the state file.** h-mad keeps the claim in its orchestrator state — the JSON path h-mad's own SKILL.md passes to `h_mad_state_write.py` in its Phase-0 snippet, `docs/.bkit-memory.json` relative to the project root in every current project. Locate it rather than assuming:

```bash
# 1. The canonical path first. h-mad's own Phase-0 snippet writes here, so a search
#    is the fallback, not the first move — and it is the search that goes wrong.
STATE="<target-repo>/docs/.bkit-memory.json"
if [ ! -f "$STATE" ]; then
  ERR=$(mktemp)
  # `command find`, and NO `2>/dev/null` — both deliberate; see below.
  HITS="$(command find <target-repo> -name .bkit-memory.json -path '*/docs/*' \
            -not -path '*/.git/*' -not -path '*/archive/*' 2>"$ERR")"
  RC=$?
  N=$(printf '%s' "$HITS" | grep -c .)
  if [ "$RC" -ne 0 ] && [ "$N" -eq 0 ]; then
    echo "SEARCH FAILED — this is NOT 'nothing found'. Do not conclude 'nothing is claimed':"
    cat "$ERR"; exit 1
  fi
  [ -s "$ERR" ] && { echo "warning: search reported errors, result may be partial:"; cat "$ERR"; }
  case "$N" in
    0) STATE="" ;;
    1) STATE="$HITS" ;;
    *) printf 'AMBIGUOUS — %s state files:\n%s\n' "$N" "$HITS"
       echo "Pick the one at the TARGET REPO ROOT by hand. Do not take the first."; exit 1 ;;
  esac
fi
[ -n "$STATE" ] || echo "no h-mad state file under <target-repo> — nothing is claimed, skip to Step 3"
```

Every deviation from the obvious one-liner is load-bearing, and each answers a *different*
observed failure:

- **`find`, not `<repo>/**/docs/.bkit-memory.json`** — the glob is a silent fail-open. Bash ships
  with `globstar` off, where `**` collapses to a single `*`: a real state file two directories down
  is not matched, `$STATE` comes back empty, and this step concludes "nothing is claimed" and skips
  the release entirely — the exact outcome it exists to prevent, with no error message. (Measured
  both shells: bash finds a depth-2 file only with `globstar` on; zsh finds it, but on *no* match
  prints `no matches found` past the `2>/dev/null`, since the failure is the shell's own glob
  expansion rather than anything `find`/`ls` emitted.)
- **No `2>/dev/null`, and the exit code is read** — `find` is not always `find`. A wrapper on
  `PATH`, a shell function, or a token-proxy hook may intercept it and *refuse* the call: rtk's
  does, with `rtk find does not support compound predicates or actions (e.g. -not, -exec)` on
  **stderr** and rc=1. Discard stderr and that refusal becomes an empty result, which reads
  identically to "no state file". This bit a real handover on 2026-08-27: the first probe reported
  "nothing is claimed", and it was false. **`failed` and `found nothing` lead to opposite correct
  actions, so they must not be spelled the same way** — the same asymmetry this skill already
  enforces for the worktree-comment read. `command find` bypasses a function or alias; the rc check
  catches an intercepting binary that `command` cannot bypass. Non-zero *with* hits is a partial
  result (an unreadable directory), which warns rather than halts.
- **No `| head -1`** — more than one hit is normal and picking one by traversal order is a coin
  flip. Measured in `orca/skills` on 2026-08-27: **three** matches, and the two `find`
  implementations on that machine returned them in *different orders*, so `head -1` yielded the
  repo-root state file one way and a sub-project's the other. Claiming or releasing in the wrong
  project's state file is silent in both directions. Ambiguity is a stop, not a default.

No state file means no claim to release. Say so and move on; do not invent one.

**Substitute the printed path into the blocks below — do not carry it in a shell variable.**
Each block runs as its own tool call in a fresh shell, so an assignment made here has already
expired by the next one; `--state ""` then fails outright, or worse, reads as "no claim".

**Then ask who holds it — do not eyeball the timestamp.** `h_mad_resume_decision.py` is the liveness oracle, and it applies the *same* staleness window the writer does, so its answer and `--claim`'s behaviour cannot disagree:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_resume_decision.py" \
  --state "<the path the find printed>" \
  --feature "<feature>" --session-id "<your-session-id>"
```

- **`owned_elsewhere`** → the owner is **LIVE**. The work is not yours to hand over. Stop and surface it — releasing here would yank a feature out from under a running session.
- **any other token** (`enter_autonomous`, `resume_manual`, `halted`, `start_fresh`) → no live owner. Safe to proceed.

Read the owner and heartbeat for the brief — the receiver needs to know a claim existed and what happened to it:

```bash
python3 -c "import json,sys; s=json.load(open(sys.argv[1])).get('orchestrator_state') or {}; \
r=s.get(sys.argv[2]); print('NO SUCH FEATURE — nothing claimed' if r is None else \
('owner: %s | heartbeat: %s' % (r.get('owner_session_id'), r.get('owner_heartbeat_ts'))))" \
  "<state-path from the find above>" "<feature>"
```

Use `.get()` throughout: a state file that exists but has no record for this feature is the **normal** case for loosely-tracked or newly-named work, and indexing it directly raises `KeyError` and halts the handover with a traceback instead of the correct answer, which is "nothing is claimed, carry on".

**Then release**, so the receiver inherits a free claim:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_state_write.py" \
  "<state-path from the find above>" --feature "<feature>" --release \
  --session-id "<your-session-id>"
```

`--session-id` is **your own**, and it is required here because your claim is still live — you are
releasing it seconds before handing over. Releasing a live claim without saying who you are is
refused rather than silently performed, because `--release` + `--claim` used to take a running
session's feature with no `--force` anywhere (J45). If the refusal says the owner is someone else,
that is a real finding: you are about to hand over work you do not hold. Do not reach for force to
get past it.

Hand work over without this and the receiver inherits a feature still owned by a session that has stopped. Depending on the version they run, `--claim` either refuses outright or makes them reach for `--force` — and `--force` is the verb for taking a feature from a session that is still *live*. Training a receiver to pass it routinely wears out the one guard protecting a running session.

Two cases that are not yours to fix silently:

- **The claim is held by a different, dead session** (the oracle returned something other than `owned_elsewhere`, but `owner_session_id` is not you). Releasing it is the right move *and* you must say so in the brief, with the session id and heartbeat you just read. Never `--claim --force` on the receiver's behalf — taking ownership is their decision, and a `--force` they did not choose hides that a claim was ever contested.
- **The claim is held by a live session** (`owned_elsewhere`). The work is not yours to hand over. Stop and surface it.

### Step 3: Write the brief into the RECEIVER's store

Use the target's canonical store, not yours — `--repo` resolves it without leaving your directory:

```bash
HP="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py"
DIR="$(python3 "$HP" --repo "<target-repo>" dir)"
BR="$(python3 "$HP" --repo "<target-repo>" branch-slug)"
mkdir -p "$DIR"
FILE="$DIR/$(date +%F)-${BR}__<slug>.md"
```

`--repo` refuses a path that is not a git work tree rather than resolving it anyway. That refusal is deliberate: `canonical_root` falls back to whatever path it was handed, so a typo would otherwise produce a real-looking `docs/handoffs` directory that the writer creates, reports, and nobody ever reads.

Use the §"Required template" as-is. The **Open / Blocked Items** location block (`repo · branch · worktree` plus artifact paths) is not optional here — for a receiver with none of your context, it is the difference between starting and excavating.

**Add the handover marker, directly under the `**Project:**` line:**

```markdown
**Handover-From:** <sender-repo> · <sender-branch> · session <sender-session-id>
```

This one line is what makes the brief *machine*-detectable. Prose like "this is a handover, not a closeout" reads clearly to a human and is invisible to the receiver's READ, which then treats the brief as an ordinary resume: it restores the todos but never claims the feature, so the work sits unowned — the sender released it and stopped watching, and nobody took it. See §"Take over handed-over work" for the half this marker switches on.

### Step 4: Stamp the target's worktree comment

**First, does the target worktree exist yet?** This step and Step 5 are written in the order that suits an *existing* lane. If the handover creates a **new** worktree, the target does not exist while you are reading this — a `worktree-ps` lookup will miss, and the rule below ("not in `worktree-ps` → skip the stamp") would silently swallow it, leaving the brand-new lane with no checkpoint at all. So:

- **Existing target worktree** → do this step now, then Step 5.
- **New worktree** (Step 5 will create it) → **skip ahead to Step 5, create the lane, then come back here** and stamp using the `worktree.id` the create response returned (`<repoId>::<worktreePath>` — copy the whole value; do not shorten it to the repo id). There is nothing to preserve on a worktree that did not exist a moment ago, so the read below is unnecessary in this direction.

Best-effort, Orca only. Same preservation rule as the WRITE stamp (§"WRITE — stamp an Orca checkpoint"), but **a different read command**: `worktree-current` reads the worktree you are *in*, which is the sender. To see the target's comment you must go through `worktree-ps` and select by path:

```bash
hmad-dispatch worktree-ps | python3 -c "
import json,sys
t = sys.argv[1].rstrip('/')
for w in json.load(sys.stdin)['worktrees']:
    if w.get('path','').rstrip('/') == t:
        print(w.get('comment') or '')
        break
else:
    print('WORKTREE-NOT-FOUND', file=sys.stderr)
" "<target-worktree-path>"
```

Then apply the rule: a non-empty comment that does **not** start with `handoff:`, `handover:`, `taken over:` or `h-mad` was written by a human — append after it (`<existing> — handover: …`). (Same four prefixes as the WRITE stamp; `taken over:` is what TAKEOVER writes, so a handover into a lane that already took one over must replace, not append.) An empty comment or a prior skill stamp is replaced outright. `worktree-comment` only ever overwrites, so preserving is something you do by *composing the new value*, not something the command does for you:

```bash
hmad-dispatch worktree-comment "<target-worktree>" "<composed-value>"
```

If the target is not in `worktree-ps` at all, skip the stamp — it is an enrichment, never a gate — and say so rather than stamping the wrong worktree.

The snippet's `['worktrees']` and `WORKTREE-NOT-FOUND` are load-bearing in opposite directions and neither is decoration: the subscript raises loudly if the container is absent (never soften it to `.get('worktrees', [])`, which turns a wrong key into a silent "no such worktree"), and the `for`/`else` distinguishes *scanned the list, target absent* from *never scanned anything*. As in READ Step 3, these keys are **post-unwrap** — `hmad-dispatch` strips orca's `.result` envelope, so a raw `orca worktree ps --json` needs `.result.worktrees[]` instead. See `h-mad/references/agent-substrate.md` §"The `.result` envelope".

### Step 5: Deliver — via `orca-cli`, not by reimplementing it

Invoke the **`orca-cli` skill by name** (the Skill tool — it is a registered skill, so do not go hunting for a file path) and use its Full Handoffs commands: `worktree create --no-parent --agent <agent> --prompt …` for a new lane, `terminal send --terminal <handle> --text … --enter` for an existing one.

`--no-parent` is the **default, not a rule**: it makes the handover an independent top-level lane, which is what "this is no longer mine" usually means. Drop it — and pass a parent/base instead — when the user actually asked for stacked work ("hand this to a child worktree", "branch from current", a named base). Hardcoding it there silently strips the lineage they asked for, and Orca's own guide conditions the flag the same way. Those flag names are a hint, not the contract — that skill defers to the `orca` binary's own version-matched guide, which is the only source that cannot drift from the binary you are about to run.

**Send the path, not the payload.** The prompt should name the brief and the location block, then stop — a prompt carrying the whole document decays the moment the doc is updated, and there is then no single source of truth about what was handed over.

**A successful send is not a pickup.** `terminal send` answers `accepted: true, bytesWritten: <n>`, and that is the *write* succeeding: the bytes reached a live pty handle. It is not evidence the receiving session read the prompt or acted on it — `bytesWritten` measures your payload, not their behaviour, and is non-zero into a pane that is wedged, mid-redraw, or running something else. A `connected: true` listing rules out only the **stale-pin** failure (writing into a handle that no longer exists); it says nothing about whether anyone picked the work up. Report the transfer accordingly: say the brief was delivered to `<handle>` and that acceptance was by a live handle, not that the receiver started. Pickup is proven only by something the receiver produces (a claim on the feature, a commit, a `taken over:` stamp) — and waiting for that is supervision, i.e. the `orchestration` skill and a different ask, per Step 6. The same distinction on h-mad's other delivery surfaces: `h-mad/references/orchestration-mode.md` §`worker-start`.

### Step 6: Let go

Drop the item from your own todo list — and if Step 4's sink was durable (`.omc/notepad.md`), *dropping* means editing that file, not merely not mentioning it again; a handed-over item left sitting in a durable list re-enters the next resume as work you still own. Then report what moved and where, and **stop monitoring** — that is what makes this a handover rather than supervision. If the user wants progress tracked, completion waited on, or results collected, that is the `orchestration` skill and a different request; say so rather than half-doing both.

**"Stop monitoring" means stop watching the receiver — it does not mean end your turn.** When HANDOVER was invoked *as a step inside another mode* (WRITE's §"Route foreign-worktree work before closing out" does exactly this), it is a **returning subroutine**: finish the handover, then go back and complete every remaining step of the calling mode. Treating "let go" as terminal is how a session closeout gets orphaned — the foreign item moves correctly and the handoff doc is then never saved, committed, or pushed.

### HANDOVER don'ts

- Don't deliver before releasing the claim — the receiver inherits a deadlock they can only break with `--force`.
- Don't write the brief into *your* store and mention the other repo in it; that is a note to yourself, not a handover.
- Don't paste the whole brief into the delivery prompt.
- Don't use `orca orchestration task-create` here; a task row means supervised work, which is a different ask.
- Don't keep watching the receiving lane. Handing over and hovering is the worst of both.

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
- 2026-04-28 · HemaSuite/guideline-category-facet · Shipped guideline-category-facet end-to-end via TDD multi-agent cowork · `/Users/kimhawk/Coding/HemaSuite/docs/handoffs/2026-04-28-main__guideline-category-facet.md`
```

Each entry has four pipe-free segments separated by `·`: ISO date, `<project-slug>/<handoff-slug>`, a one-line summary lifted from the doc's Session Summary (≤100 chars), and the absolute path in backticks. Use absolute paths (not `~/`) so a `grep` is unambiguous.

Create the file with a `# Handoffs Index\n\nNewest first. Format: ISO date · project/slug · summary · path\n\n` header block if missing. Don't commit `~/.claude/handoffs/INDEX.md` to any project repo — it's user-global state, not project state.

**If the index has no `- ` bullet yet** (a fresh install, or a file you just created from the header block), there is nothing to insert *before* — append the entry after the header block instead. The anchor rule below assumes at least one existing entry; applying it to an empty index finds no anchor and is how an agent ends up guessing a position or reporting a failure over a file that is simply new.

**How to prepend — anchor on the first list item, never on the header text.** Insert the new entry *immediately before the first existing `- ` bullet line*, so it becomes the newest. Do **not** anchor the insert on the `Newest first. Format:` header string: this file has been observed carrying a duplicate of that line mid-file, and a header-anchored insert lands the newest entry in the middle instead of the top (observed 2026-07-23 — an entry went to line 36). "Before the first `- ` line" is unambiguous no matter how many stray header lines exist. After inserting, verify placement (`grep -n '^- ' INDEX.md | head -1` should return your entry) rather than trusting the write — and if you find a stray `Newest first.`/`Format:` line anywhere below the top block, delete it while you are here; it is corruption that will mis-anchor the next writer. Locate them first, and delete the ones it reports with a normal edit:

```bash
# lists only strays BELOW the first entry — the real header is above it and must survive
awk 'f && /Newest first\.|^Format:/ {print FILENAME":"NR": "$0} /^- /{f=1}' ~/.claude/handoffs/INDEX.md
```

Do not pipe that into a blind `sed -i` delete-by-pattern: the same strings appear in the legitimate header block, and a pattern-scoped delete that guesses the header's line range removes it too.

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

## Writing guidance

- **Session Summary**: 2–5 sentences max. Outcome-first (done/partial/blocked). No narrative.
- **Key Learnings**: non-obvious only. If a fresh reader could derive it from the code or git log, omit it.
- **Next Steps**: concrete + ordered. Each item must have a file path or a command. Vague actions ("look at the auth module") are not Next Steps.
- **Open / Blocked Items**: name blockers explicitly. "Blocked on X" is useful. "In progress" alone is not. Parked work outside this repo/branch/session must carry its `repo · branch · worktree` and key artifact paths (see the template note) — a location-less parked item is a forensic hunt for the next session.
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
between tool calls**, so `$HP`, `$DIR` and `$BR` set back there are already empty here — and an
empty `HP` does not merely error, it makes `ROOT` empty, which sends the branch below down the
"linked worktree" path that skips the commit on purpose. Re-deriving `ROOT` and `LEARN` is safe
because both are pure functions of the repo. `$FILE` is **not** — §Save's concurrency guard may
have appended a `-2`/`-<HHMMSS>` discriminator, so re-deriving it would name a file that does not
exist. Substitute the literal path §Save actually wrote.

```bash
HP="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py"
ROOT="$(python3 "$HP" root)"                 # canonical main-worktree root
LEARN="$(python3 "$HP" learnings)"
echo "$ROOT" "$LEARN"                        # carry these forward as literals too
```

- **On the main worktree** (`ROOT` == `git rev-parse --show-toplevel`): stage + commit normally:
  ```bash
  git add "<the handoff path §Save wrote>" "<the learnings path echoed above>"
  git add docs/skill-candidates.md 2>/dev/null || true   # only if scout ran
  git commit -m "chore(handoff): YYYY-MM-DD <slug>

  Session closeout: <one-line summary from Session Summary>."
  ```
  Literal paths, not `$FILE`/`$LEARN` — this is a separate tool call and those are empty here.
  `git add ""` at least fails loudly (`fatal: empty string is not a valid pathspec`). The
  dangerous one is above it: an empty `HP` makes `ROOT` empty, `ROOT` then never equals the
  toplevel, and the branch below concludes "linked worktree" and **deliberately does not
  commit** — on the main worktree, reporting the skip as correct behaviour. Measured, both.
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
