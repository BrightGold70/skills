# handoff reference — READ mode

_Moved verbatim from `handoff/SKILL.md`; SKILL.md keeps a pointer stub under the same heading. Edit the text here. Everything below the marker line is the section body exactly as it stood in SKILL.md._

## Reading a handoff (resume mode)

<!-- handoff split body: SKILL.md §"Reading a handoff (resume mode)" -->

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
3. **Repo-wide newest in the canonical store** — `python3 "$HP" latest` (no `--branch`). Use when this branch has none. If it matches a *different* branch, say so and confirm with the user before resuming — you may be picking up a sibling worktree's work.
4. **`~/.claude/handoffs/INDEX.md`** — grep for the current project name / path; take the newest matching entry's path.

If no handoff is found after these checks, tell the user ("No handoff found for this project — nothing to resume from") and stop. Don't fabricate a handoff.

**Then, ALWAYS — inbound handovers, in addition to the checks above, never as a fallback to them.**
Checks 1–4 stop at the first hit, but a brief carrying `**Handover-From:**` is addressed to this repo, not to a branch. A sender names the file for the branch they were told to target, so a handover routinely lands as `…-main__…` while you sit on a feature branch — and on any branch that has a handoff of its own, the common case, it is never looked at.

```bash
HP="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py"
python3 "$HP" pending-handovers; RC=$?
```

| `RC` | Meaning | What to do |
|---|---|---|
| 0 | one or more briefs are addressed to this repo and nobody has taken them over | Read **each** in full and run §"Take over handed-over work" for it, **in addition to** whatever check 1–4 found. |
| 1 | none pending | Continue with the doc from checks 1–4. |
| 2 | at least one brief could not be read | **Not an empty queue.** Report the `UNREADABLE:` paths to the user as a divergence and handle any briefs that did print. |

This was placed in check 3 as an exception once, gated "use when this branch has none" — which put the remedy for an inbound-handover bug in the branch that only runs when the other branch fails. Measured 2026-09-01 on HemaSuite: `latest --branch feature-41-…` and bare `latest` returned the same file while **9** briefs in that store carried `**Handover-From:**`, none of them reachable. One of those was a 15-item backlog that had been explicitly handed over and was never picked up. Fixing a defect in the fallback path leaves the primary path defective.

**Cold start — the first run in a repo over-reports, and that is expected.** `**Taken-Over-By:**` is a newer field than the stores it filters, so on first use *every* historical handover brief shows as pending, including ones that were taken over and finished long ago. Measured on `orca/skills` 2026-09-01: **16** pending, of which the great majority are closed work. Triage them once — for each brief that was already picked up, add the `**Taken-Over-By:**` line (Step 3.5's format, with the session that did the work if you know it, else `unknown · backfilled <YYYY-MM-DD>`) and commit. After that pass the queue is live and short.

Do **not** skip the triage and learn to ignore a long queue instead — an alert that is always wrong is worse than no alert, and this scan exists precisely because a real brief sat unread among ordinary docs. Equally, do not bulk-stamp briefs you have not checked: a brief wrongly marked taken over is invisible again, which is the original defect restored by the tool built to fix it. If the queue is long and you cannot triage it now, say so to the user and record it as an open item.

The scan reads only the doc's HEADER block — the field run above the first `## ` section — because both markers are header fields while this skill's own carry-forward rule requires a line-start bold `**Handover-From:**` in the BODY of any closeout that inherits an item. Scanning the whole document made every such handoff report itself as an unadopted brief forever; two of this repo's own closeouts were offered that way, one of them the document describing the defect. Do not widen it back — a doc with no `## ` heading is treated as all-header on purpose, erring toward offering rather than hiding.

The scan filters on `**Taken-Over-By:**`, which Step 3.5 stamps into the brief. That marker lives in the doc because the doc store is what this scan reads: the `taken over:` worktree comment is worktree-scoped and the advisory claim lives in a gitignored, machine-local state file, so neither survives into the store and neither can tell a taken-over brief from an abandoned one.

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
  - **A carried "N unpushed commits" claim about any branch** is a premise, not a todo: run `python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/local_only_commits.py" --repo <repo>` (read-only; fetches first) before restoring it. Being ahead of its own remote says nothing about main. HemaSuite carried "26 unpushed" through three handoffs when all 26 were on main, reached through a stale `origin/main`. The script classifies each branch and worktree HEAD as `MERGED` / `ON_BASE` (patch or squash) / `PARTIAL` / `UNIQUE`.
  - **A carried "these N tests fail anyway / are environmental / pre-existing" claim** is a premise too. Do not run it here (READ runs no tests), but restore its todo with the command that settles it instead of a hand-built clean-worktree diff: `python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_failure_diff.py" run --base <ref> -- <test files>`. It runs the selection here and in a throwaway detached worktree at `<ref>`, diffs failure **ids** (never counts), and ends on one token: `FAILDIFF: SAME|NEW|FLAKY|FIXED_ONLY|UNREADABLE`. `UNREADABLE` (busy suite, collection error, no tests ran) is never "no new failures". Measured 2026-10-31: a session re-typed that worktree-and-`comm` sequence four times, and once read an empty control run as "39 new failures", while this script had existed since 2026-10-05 (`fb474949`). Nothing in this skill pointed at it.
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
Skip this unless the doc carries a `**Handover-From:**` line. If it does, run
§"TAKEOVER mode" in full — the procedure lives there, single-sourced, because the same
adoption is needed mid-session and a second copy of it would drift out of step with this one.

Then return here and continue with Step 3.6. Nothing else about READ changes.

### Step 3.6: Resolve what is mechanically resolvable — and only that

A resume that merely *reports* divergences hands the user a second task list on top of the one it
just restored. Most divergences have exactly one correct repair and no judgment in them; a few carry
a decision; a few belong to someone else. Repairing the first class is the point of this step.
Repairing the other two is how a resume does damage.

**The predicate rule — fail closed.** Every repair below is gated. If the gate cannot be *evaluated*
— a command errors, a listing is unreadable, an oracle is missing — that is not licence to proceed:
report it as a divergence and move on. **"I could not check" and "the check said yes" must never
take the same branch.** Same asymmetry the WRITE stamp already enforces for an unreadable worktree
comment, and the same one that made `find` under rtk report "nothing is claimed" when it had
actually refused to run.

**Resolve — the allowlist. Nothing outside it.**

| divergence | gate that must PASS first | repair |
|---|---|---|
| behind upstream, tree clean | clean **and** strictly behind (not diverged) | `git pull --ff-only` |
| feature record absent, brief carries `**Handover-From:**` | Step 3.5's oracle ran | `--create --claim` |
| claim on **this** feature held by a session that is not live | `h_mad_resume_decision.py` returns anything but `owned_elsewhere` | plain `--release` then `--claim` — never `--force` |
| the handoff doc you just read is untracked | it is that file and only that file | commit it |
| a cited PID is dead / its log is cold | `ps` answered, and the doc is recent enough for the PID to mean anything | do not restore "monitor PID N" — restore "verify what it produced" instead |
| a cited path moved | `git log --follow --diff-filter=R` names the rename | rewrite the todo's path, and say so in the todo |
| a cited PR is merged or closed | `gh` answered (not: `gh` is missing) | drop the todo |
| an agent pane is unresolved | **exactly one** candidate matches by content — the raw `orca terminal read` → `.result.terminal.tail`, because no wrapper verb reads an arbitrary handle yet (`hmad-dispatch read` resolves a pinned AGENT, not a handle); that gap is filed as a candidate | pin that one |

**Never resolve — report these, every time.**

- **A dirty or diverged tree.** No pull, rebase or merge. Unchanged from Step 3.
- **Anything in another repo, worktree or lane** — including a sibling branch that is cleanly
  fast-forwardable. It may have a live owner who is not watching your session, and "it was only a
  fast-forward" is not a defence when their working tree changes under a running agent.
  **The gate that would have made this resolvable was proposed, specified, and refused —
  2026-09-01.** The proposal: resolve it when no agent is live in that worktree, checked with
  the raw `orca terminal read` over its panes — raw because, as above, no wrapper verb addresses a
  handle. It cannot work, and the reason generalises past Orca: a tail
  proves an agent is **present** (a banner), never that one is **absent** — a quiet tail is an idle
  agent between turns, and a non-Orca session (a plain shell, an editor terminal, another Claude
  Code in that directory) is invisible to every Orca-side check. So the gate answers "present" or
  "could not verify", never "absent", and this step's own predicate rule then forbids the repair.
  **A gate that can never legitimately pass IS this never-list entry.** The check and the pull are
  also not atomic, so even a true answer decays before the repair runs. Do not re-derive it: report
  the sibling with its command instead (below).
- **A claim held by a LIVE session.** That is a collision and a finding, not a lock to break.
- **Any premise the brief asserts about the world.** It needs a probe, not a repair. A brief is a
  claim made by a session that has stopped; re-running its reproduce commands is Step 3.5's job and
  the answer may be that the work is already done, or was never true.
- **More than one candidate for a pane pin.** A wrong-but-live pin passes every liveness check and
  leaks dispatches into a stranger's shell — strictly worse than leaving it unresolved.
- **Anything needing `--force`, `-D`, `rm`, or a push.** If the repair is not reversible by the next
  reader, it is not mechanical.

**Report it with the command, don't run it.** A refused repair still has an ergonomic half that is
free, and taking it is what keeps the never-list from feeling like pure loss: name the exact command
in the divergence line so the user runs it with one keystroke when *they* judge the lane idle. For
the fast-forwardable sibling this costs nothing and touches nothing — worktrees of one repo share an
object store and a ref namespace, so the count comes from **here**, with no `-C` into their tree and
no read of their working files:

```bash
git rev-list --left-right --count "refs/remotes/origin/<branch>...refs/heads/<branch>"   # <behind> <ahead>
```

Step 0 already fetched, so that is offline and read-only. Report it in the shape the Step 5 template
shows: what is true, that you did **not** act, and the command that would. The judgement the gate
could not make — is anyone working that lane — is one the user makes for free, so hand it to them
rather than guessing on their behalf.

**Say what you did.** Step 5 gains a **Resolved** block, separate from **Divergences**. Name the
command for each repair so it can be undone. A repair nobody is told about is indistinguishable from
a state that was never broken — and the user then cannot tell a resume that fixed four things from
one that found nothing.

**Opt out** with `--report-only`, which runs Step 3 and skips this step entirely. Use it when
resuming into a tree someone else is actively working.

### Step 4: Restore the todo list

Repopulate todos from the doc's **Next Steps** and **Open / Blocked Items**. Each Next Step becomes a `pending` task with the cited path/command in the description. Each Open/Blocked Item becomes a `pending` task tagged with its blocker if any. Do this even if Next Steps is short — the point is that the user can start on item 1 without re-typing the list.

**Take the first sink that exists — this step must never be a no-op.** A todo-authoring tool is *not* guaranteed, and — the part that matters — **its presence varies between sessions on the same machine**, so this is a live check every time, never a fact you carry from the last resume. `TaskCreate` was in daily use here through 2026-08-19 — last invocation `2026-08-19T07:11:39Z`, then **zero** calls on 08-20 and 08-21 — and was gone the next morning under Claude Code 2.1.236, with no config change; it may equally be back tomorrow. **Do not treat the call count as a fixed figure.** An earlier pass recorded 465 calls; a re-count on 2026-08-21 across 2,734 transcripts returned 429. Neither is obviously wrong — they did not count the same thing — and a corpus count shrinks as transcripts age out. The load-bearing facts are the last-seen timestamp and the run of zeroes after it, not the total. An instruction that names one task tool unconditionally silently restores nothing while every other part of READ succeeds — the reconciliation reads correct, the action queue evaporates, and the report says neither.

**Probe it, do not infer it.** Your own tool list plus one `ToolSearch` is the only authority — and that probe is sound because **`ToolSearch` is not deferred-only**. Its description is written about deferred tools, which invites the worry that an empty result merely means "loaded, so not in the deferred list" — a false negative that would send you past a rung-1 tool you actually have. Measured 2026-08-21: `ToolSearch select:Bash,Read,Write` returns full schemas for tools already in the main tool list, so it resolves non-deferred tools too and an empty `select:` result is genuine absence. Two further ways to get this wrong, both measured 2026-08-20:

- **Absence of calls is not absence of the tool.** Grepping transcripts for `TaskCreate`/`TodoWrite` counts *use*; a session where the tool existed and went unused is byte-identical to one where it never existed. The report that opened this defect concluded "no todo tool on this machine" from zero `TodoWrite` hits — while `TaskCreate`, the name actually in use, had hundreds (the exact total is not the point — see the caveat above). The conclusion happened to be right for that session and the method could not have shown it.
- **A mention is not a tool.** `TodoWrite` appears in plugin hook matchers and in agent catalogs declaring subagent toolsets (`(Tools: …, TodoWrite, …)`). Grepping the name finds it everywhere and proves nothing about your main loop. Distinguish `"name":"TodoWrite"` inside a `tool_use` block from prose.

**When the probe comes back empty, try the opt-in BEFORE the ladder.** The todo tools became **opt-in** in Claude Code **2.1.236** — they were gated, not removed: all four names (`TaskCreate`, `TodoWrite`, `TaskUpdate`, `TaskList`) are still in the 2.1.238 binary, behind the `CLAUDE_CODE_ENABLE_TODO_TOOLS` setting — still true at **2.1.250**, where the flag string and all four names are present in the binary. Setting it in the `env` block of `~/.claude/settings.json` restores rung 1:

```json
{ "env": { "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1" } }
```

Measured 2026-08-21 by control/treatment: without it the probe answers `NOTOOL`; with it the transcript carries a real `TaskCreate` `tool_use`. **It applies mid-session — do not defer to a restart.** Measured 2026-08-28 on 2.1.250: writing the key mid-conversation surfaced `TaskCreate`/`TaskGet`/`TaskList`/`TaskUpdate` as deferred tools within the same session, after an earlier `ToolSearch` in that same session had returned no match. So the word "launch option" was misleading, and the reader who sets this must **re-run the probe immediately** and restore to rung 1 in the session they are already in, rather than descending the ladder or handing the queue to the next session. (An earlier revision of this section asserted the opposite — *"no user config can add a built-in tool"* — and told the reader not to try. That was wrong, and it cost a resume: the ladder degraded to the notepad while rung 1 was one setting away. A separate user setting, `todoFeatureEnabled`, governs the TUI **panel** and is not the same switch; enabling only that leaves the tools absent.)

Only if the opt-in is unavailable, or a re-probe after setting it still comes back empty, walk the ladder:

1. **A task/TodoList tool**, if one is in your tool set (`TaskCreate`, `TodoWrite`, or equivalent). Check this session, not your memory of the last one. If it is not in your loaded tools, one `ToolSearch select:TodoWrite,TaskCreate,TaskUpdate,TaskList` settles whether it is merely deferred; empty there — with the opt-in above already tried — means genuinely absent and you move to rung 2 without further hunting. **Prefer this rung when it exists** — it is the only sink the user can see and tick off in the UI, which is what they mean by "the todo list".
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

**Split the two lists.** `Resolved` and `Divergences` answer different questions — what you changed
versus what the user must decide — and merging them hides both. If Step 3.6 resolved nothing, say
`**Resolved:** none` rather than omitting the block; an absent block reads as "this resume does not
do that" and the next reader stops expecting it.

**Resolved** (Step 3.6 — mechanical repairs, each undoable):
- Stale claim on `guideline-rag` (owner `36032fe8`, heartbeat 2d old, oracle: not live) — released, then claimed as this session.
- `protocol/sections/background.md` → `protocol/sections/intro.md` (`git log --follow` names the rename) — todo 3 rewritten.

**Divergences** (reported, NOT resolved — each needs you):
- PID 37219 (compile_guidelines_db): exited — log mtime 3h ago. Treat as complete; verify output.
- Sibling worktree `feature/12` is 2 behind and cleanly fast-forwardable — **not pulled**; its owner
  may be mid-turn. Run `git -C ../feature-12 pull --ff-only` when that lane is idle.

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
- Don't rewrite or update the handoff doc in read mode — it's a historical record. (Step 3.6 may
  *commit* an untracked handoff doc, which changes no content.)
- Don't resolve a divergence that is not on Step 3.6's allowlist, and don't extend the allowlist in
  the moment. The list is short because each entry had to be shown to have exactly one correct
  repair and a gate that fails closed; "this one is obviously safe too" is how a resume starts
  mutating a tree it does not own.
- Don't run tests or builds as part of reconciliation.
- Don't assume the in-flight process is still running if the doc is >4h old.
- Don't `git pull` when the tree is dirty or the branch has diverged — fast-forward-only (`git pull --ff-only`) on a clean tree, otherwise flag and let the user resolve. Never `git merge`/`git rebase`/`git push` during a resume.

---

