# handoff reference — HANDOVER mode

_Moved verbatim from `handoff/SKILL.md`; SKILL.md keeps a pointer stub under the same heading. Edit the text here. Everything below the marker line is the section body exactly as it stood in SKILL.md._

## HANDOVER mode — move ownership to another worktree

<!-- handoff split body: SKILL.md §"HANDOVER mode — move ownership to another worktree" -->

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

**Then ask who holds it — do not eyeball the timestamp.** `h_mad_resume_decision.py` is the liveness oracle, and it applies the *same* liveness reading the writer does, so its answer and `--claim`'s and `--release`'s behaviour cannot disagree. That reading is the heartbeat window plus the owner's own transcript (`owner_proven_live`; never `ps`), and never the lane's shared commit clock:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_resume_decision.py" \
  --state "<the path the find printed>" \
  --feature "<feature>" --session-id "<your-session-id>"
```

- **`owned_elsewhere`** → the owner is **LIVE**. The work is not yours to hand over. Stop and surface it — releasing here would yank a feature out from under a running session.
- **`cannot_judge`** → the state file exists and could not be READ. Not a live owner and not a free claim: it is the absence of evidence either way, so treat it exactly as the predicate rule says and STOP. Releasing or claiming against a file you cannot parse is how a second session takes a feature the first is working.
- **`state_lost`** → no record for the feature, but its live phase documents exist on disk: the state file or the record was LOST, not never written. Not a free claim — creating a record here restarts a mid-flight feature at Phase 1. STOP and surface it; restore or reconstruct the record per h-mad's decision table, then re-run the oracle.
- **`migrated_by_bkit`** → the state file is missing because bkit's session-start migration MOVED it to `<root>/.bkit/state/memory.json`, where this feature's record is intact. Not a free claim and not a lost record — STOP and surface it; restore by COPY with the `cp` command the oracle prints on stderr (never move: bkit would migrate it again), then re-run the oracle.
- **one of `enter_autonomous`, `resume_manual`, `halted`, `start_fresh`, `complete`** → no live owner. Safe to proceed.

  `complete` was **missing from this list for the life of the file**, and the omission was not
  cosmetic: the oracle returns it whenever `last_completed_phase >= 7`, so a feature that had
  simply *finished* took the `anything else` branch below and **halted both HANDOVER and
  TAKEOVER**. The failure mode is the exact inverse of the one that closed the list — not a
  stale token treated as permission, but a live token treated as danger, which stops a handover
  on the work most likely to be ready to move. Reported by a resume on 2026-09-14.

  It is safe *because of an ordering the oracle states explicitly*, not because "complete sounds
  done": `_owned_elsewhere` is evaluated **before** every `complete` return, so the token cannot
  be reached while a live session holds the feature. Verify that ordering still holds before
  trusting this bullet — if a future edit moves the liveness check below the phase checks,
  `complete` becomes exactly the fail-open this list exists to prevent and belongs back with the
  STOP bullets.
- **anything else** → STOP and surface the token. This list is deliberately CLOSED. It previously ended with a catch-all bullet that granted the unknown case permission to proceed, which is fail-open: every token added to the oracle after that bullet was written would have been auto-classified as safe. `cannot_judge` was added FOR safety and would have been read as permission. The retired wording is not reproduced here on purpose — a hazardous instruction quoted verbatim is still copyable, and the test that guards this cannot tell a live instruction from prose quoting it.

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

- **The claim is held by a different, dead session** (the oracle returned something other than `owned_elsewhere`, but `owner_session_id` is not you). The oracle read the heartbeat alone, which has called working lanes dead; run `h_mad_lane_liveness.py <lane> --feature <feature>` first, and treat a `LIVENESS: LIVE` or `UNKNOWN` line as a live owner. An `UNKNOWN` that will not clear (a Claude transcript lost to retention, say) is the operator's call, not yours: ask, and release only on their word, quoting it in the brief. On `QUIET`, releasing it is the right move *and* you must say so in the brief, with the session id, heartbeat and `LIVENESS:` line you just read. Never `--claim --force` on the receiver's behalf — taking ownership is their decision, and a `--force` they did not choose hides that a claim was ever contested.
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

### Step 7 (optional, later): check ONCE that it landed

Not a walk-back of Step 6. *Watching* a receiver is supervision and belongs to the
`orchestration` skill; *asking once, later, whether they took it* is a handful of
read-only lookups and a different question — and Step 5 has already established that the
delivery receipt answers neither. Run it when you next think of that lane, not on a timer:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handover_landed.py" \
  --state "<target-repo>/docs/.bkit-memory.json" --feature "<feature>" \
  --sender-session "<your-session-id>" --worktree-path "<target-worktree-path>" \
  --repo "<target-repo>" --branch "<target-branch>" --slug "<the brief's slug>"
```

It reports only what the RECEIVER produced, on three signals: the claim moved to a
session that is not you; the worktree comment is no longer the `handover:` stamp you
left; the target branch carries commits of its own. Any ONE is proof — the others being
unavailable is the normal case (no Orca runtime, no branch given), so it never demands
all three.

**Pass `--slug` too.** It is the only thing that can tell a receiver's own closeout stamp
from a sibling lane's, and without it the comment signal keeps the older permissive rule.

**Pass `--repo`/`--branch` when you have them.** They are optional only so the older
invocation keeps working; without them the third signal is permanently `unknown`, and it
is the one that survives a receiver who claims nothing and stamps nothing and simply does
the work. Measured 2026-09-01: a handover picked up, fixed, tested and merged as
`282a3a5` reported `NOT_YET` on the other two — the receiver's worktree had its own
`docs/.bkit-memory.json` so no claim ever appeared, and it had replaced the stamp with
its own completion note. Both signals failed honestly and the verdict still prescribed
re-delivering work that was already on `main`.

Two consequences of that fix worth knowing before you read the output:

- **A comment that is neither stamp counts as pickup — unless `--slug` proves it is a
  different lane's.** You left `handover:` on that worktree in Step 4; if it is gone and
  something else is there, the receiver wrote it. Visible completion outranks the expected
  prefix, and an EMPTY comment does not count. The one exception is a `handoff:` WRITE
  closeout stamp that does NOT name the brief's slug: a sibling session closing out on the
  same worktree writes exactly that, and it was read as pickup for a brief nobody had
  opened (#100 defect A, measured 2026-09-05). That case reports `unknown`, never absence
  — and only when you pass `--slug`, because without it a receiver's own closeout stamp is
  indistinguishable from a stranger's and calling it `unknown` would restore the
  2026-09-01 false NOT_YET. Pass `--slug`.
- **The branch signal can only ever say `taken` or `unknown`, never `not_yet`.** A branch
  that merged and one that was created and never committed to are both level with the
  default and both listed by `git branch --merged`; refs cannot tell them apart. So it
  adds pickup evidence and never manufactures absence — and an ABSENT branch is
  `unknown`, because merged-and-deleted is the commonest reason for it.

**`UNKNOWN` (rc 2) is not `NOT_YET` (rc 1), and the difference is the point.** You have
already released the claim and stopped watching, so being told "nobody took it" because
a file would not parse is what makes you re-deliver work that is already in progress —
and two sessions on one feature produce contradictory conclusions on one branch. An
unreadable state file, an absent wrapper, a worktree that is not listed: all `UNKNOWN`,
none of them evidence it was dropped.

The receiving pane's own output is a third signal the row that asked for this named, and
it is deliberately **not** implemented: no wrapper verb reads an arbitrary terminal
handle (`hmad-dispatch read` resolves a PINNED agent), this skill does not call `orca`
directly, and a pane can echo a prompt it never acted on. The missing verb is filed as
the first half of the pane-ID candidate.

### HANDOVER don'ts

- Don't deliver before releasing the claim — the receiver inherits a deadlock they can only break with `--force`.
- Don't write the brief into *your* store and mention the other repo in it; that is a note to yourself, not a handover.
- Don't paste the whole brief into the delivery prompt.
- Don't use `orca orchestration task-create` here; a task row means supervised work, which is a different ask.
- Don't keep watching the receiving lane. Handing over and hovering is the worst of both.

---

