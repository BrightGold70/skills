# handoff reference — TAKEOVER mode

_Moved verbatim from `handoff/SKILL.md`; SKILL.md keeps a pointer stub under the same heading. Edit the text here. Everything below the marker line is the section body exactly as it stood in SKILL.md._

## TAKEOVER mode — adopt a handed-over brief WITHOUT ending the session

<!-- handoff split body: SKILL.md §"TAKEOVER mode — adopt a handed-over brief WITHOUT ending the session" -->

READ owns resuming; TAKEOVER owns adopting. They were the same mode, and that was the defect: the
adoption procedure lived only in READ Step 3.5, READ Step 0a **halts when the session is not fresh**,
and the `pending-handovers` scan that discovers an inbound brief is READ Step 1. So the one operation
you need precisely *because* you are already deep in a session was reachable only through a mode that
refuses to run there — and you could not even discover a brief had arrived. Observed 2026-09-07: an
inbound brief landed mid-session and every step below had to be hand-executed.

**TAKEOVER does NOT halt on a loaded session, and the reason is not convenience.** READ's halt exists
because a resume *replaces* context — the prior session's working assumptions would silently outrank
the document just read. A takeover *adds* one owned item and replaces nothing, so that conflict cannot
arise. READ keeps its Step 0a halt unchanged; this is an exception with a stated reason, not a
weakening.

### Step T1: Find what is addressed to this repo

```bash
HP="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/handoff/scripts/handoff_paths.py"
python3 "$HP" pending-handovers; RC=$?
```

`RC=0` one or more briefs are pending · `RC=1` none · `RC=2` at least one could not be read — **not an
empty queue**: report the `UNREADABLE:` paths and handle any that did print. If the user named a brief,
use that path and skip the scan.

### Step T2: Adopt it

<!-- SINGLE-SOURCE: READ Step 3.5 points here. Do not copy this body back into READ. -->


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
this repository has three. **No state file is not yet "nothing is claimed"** — on 2026-10-07 the state
file VANISHED over a feature with phase documents through Phase 6. Ask the oracle at the canonical
path anyway; it looks for the feature's phase documents:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_resume_decision.py" \
  --state ./docs/.bkit-memory.json --feature "<feature>" --session-id "<your-session-id>"
```

`state_lost`, `migrated_by_bkit` (or `cannot_judge`) → STOP and surface it; do not create a state file. `start_fresh` →
nothing is claimed: say so, skip to point 2, and do not invent one. Otherwise pass the path it printed:

**If the brief names NO feature but a state file exists, CREATE the record and claim it.** Use the
brief's **slug** as the feature name — derived and traceable back to the document that asked for the
work, never invented:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_state_write.py" \
  "<the path the find printed>" --feature "<the brief's slug>" --create --claim "<your-session-id>"
```

Run the oracle for that name first, exactly as above — `state_lost` (no record, but the name's phase
documents exist) and `migrated_by_bkit` (the record sits in `.bkit/state/memory.json`) STOP you like `cannot_judge`; on a name with no record and no documents it answers
`start_fresh`, and `owned_elsewhere` **still stops** you; the create path is a way to own unclaimed
work, never a way around the live-owner check.

Measured 2026-09-07, on this mode's first live run: the `audit-loop-cycle-count-evidence` brief
carried `**Handover-From:**` and named no feature, the state file held 34 records, and the rule above
covers only "no STATE FILE" — so the takeover concluded "nothing to claim" and five adopted items sat
owned by nobody. That is the failure this mode exists to prevent, reached *through* this mode. READ
Step 3.6 already carried the repair (`feature record absent, brief carries Handover-From` →
`--create --claim`) and TAKEOVER deliberately excludes Step 3.6, so it could not reach it. The repair
lives here now rather than TAKEOVER growing a resume's allowlist.

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_resume_decision.py" \
  --state "<the path the find printed>" \
  --feature "<feature>" --session-id "<your-session-id>"
```

- `owned_elsewhere` → someone **live** holds it. Do not take it; surface the collision. The handover may have raced another session, and that is a real finding, not a formality.
- `cannot_judge` or `state_lost` → STOP, exactly as HANDOVER Step 2 says. A lost record is not an unclaimed one, and a claim against a file you cannot read is a guess.
- `migrated_by_bkit` → STOP, exactly as HANDOVER Step 2 says: the record was moved by bkit, not lost. Restore it by COPY with the oracle's `cp` hint; a claim here would create a second record over the moved one.
- anything else → claim it:

```bash
python3 "${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}/h-mad/scripts/h_mad_state_write.py" \
  "<the path the find printed>" --feature "<feature>" --claim "<your-session-id>"
```

A stale claim is takeable by plain `--claim` — reach for `--force` only against a **live** owner, which the oracle just told you there isn't. If the brief says a claim was left deliberately unreleased (a dead session's), that is the one it means; taking it is your decision to make and now is when you make it.

**2. Verify the premises before adopting them.** A brief is a claim about the world made by a session that has stopped. Its reproduce commands are the cheap part — run them. Any premise that no longer holds becomes a divergence line, not a todo. A confident brief is not evidence.

A sha the brief cites is a premise too: `git cat-file -t <sha>` must answer `commit` before you treat it as one. Two backlog items once cited `cfc79129` and `45db0187` as commits; both were session UUIDs that resolve in no repo, and both sat unreproduced for weeks because nobody asked git. A sha that does not resolve is a divergence line, never a starting point.

**3. Restore the todos with their OWNER, not the branch you are sitting on.** Use READ Step 4's
sink ladder and all of its rules (the `[<repo>@<branch>]` prefix, the dedupe, the named sink) —
from READ continue into Step 4; from TAKEOVER restore only the brief's items.

**Take the prefix from the brief's `**Project:**` and `**Branch:**`**, which are the fields that
say whose work it is. Fall back to `**Handover-From:**` only when those are absent.

The earlier wording said to prefix from `**Handover-From:**` and justified it as "the work belongs
where the sender said it does". Those two disagree on a **returned** brief, and the justification is
the half that is right: on a return the sender says the work belongs to YOU, while `**Handover-From:**`
still names *them*. It identifies the courier, not the owner.

Measured 2026-09-14 in this repo. `#56` originated here, was handed to HemaSuite, and came back
unstarted; its brief read `**Project:** skills`, `**Branch:** main`, `**Handover-From:** HemaSuite ·
main`. Every other signal agreed with `**Project:**` — the brief was filed in *this* repo's store under
the `main__` slug, the claim was created in *this* repo's state file, and HemaSuite's state file held
nothing for it — yet the mechanical rule produced `[HemaSuite@main]`. Mislabelling work as another
repo's is what made that row ping-pong between the two lanes in the first place, so the rule that
restores it must not re-state the confusion.

**A path in the location block is where the FILES are, not whose the work is.** A returned brief
routinely cites read-only sources in the sender's tree (`#56`'s two documents live in a HemaSuite
archive, `worktree: none`). Keep those paths in the todo's body, never in its prefix.

**4. Stamp the BRIEF, so the next resume does not re-adopt it.** Add a `**Taken-Over-By:**` line directly under the brief's `**Handover-From:**` line, in the doc itself:

```markdown
**Handover-From:** <sender-repo> · <sender-branch> · session <sender-session-id>
**Taken-Over-By:** <this-repo> · <this-branch> · session <your-session-id> · <YYYY-MM-DD>
```

This is what Step 1's `pending-handovers` scan filters on, and it is **not optional**: leave it off and every future resume in this repo re-reads a brief you already own, forever. It has to live in the doc because the doc store is the only thing that scan can read — your claim is in a gitignored, machine-local state file and the worktree comment below is worktree-scoped, so neither can distinguish a brief that was picked up from one that fell on the floor. Commit the stamped brief; an uncommitted marker is one `git checkout` from being a dropped handover again.

If the brief is untracked in the store (senders often write it without committing), commit it first — that is the same defect one step earlier.

**5. Acknowledge on the worktree, so the transfer is visible.** Re-stamp the worktree comment from `handover: …` to something that says it was picked up (`taken over: <slug> · <state> · next: <next-step>`). The sender is not watching; this stamp, the brief's `**Taken-Over-By:**` line and your claim are the records that the handover completed rather than fell on the floor.

**Do not** silently work a handed-over item without claiming it. That is the failure this step exists for: the sender let go, you started, and the state file says nobody owns it.

### Step T3: Report, and go back to what you were doing

Say what moved and what you now own, then resume the work the takeover interrupted:

```
**Taken over:** <slug> from <sender-repo>@<sender-branch> (session <id>) — claimed as <your-id>.
**Premises re-verified:** N of M hold; <the ones that changed>.
**Todos added:** N, prefixed `[<origin-repo>@<origin-branch>]`. **Sink:** <task tool | .omc/notepad.md | this report>.
```

**What TAKEOVER deliberately does NOT do** — all of it belongs to READ, and doing it here would make
this a resume, which is what the halt exists to prevent:

- It does **not** sync with the remote, locate this branch's newest handoff, or read it.
- It does **not** reconcile the working tree, PRs, PIDs or worktrees against a doc (READ Step 3).
- It does **not** resolve divergences (READ Step 3.6) or rebuild the whole todo list (READ Step 4) —
  only the adopted brief's items are restored.

If you actually want all of that, you want READ, and READ wants a fresh session.

---

