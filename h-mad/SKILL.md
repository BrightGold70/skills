---
name: h-mad
description: "Orchestrate the seven-phase H-MAD development workflow end to end with project invariants, independent audits, test-first implementation, verification, and closure. Use for /h-mad feature, /h-mad do feature, /h-mad status, or /h-mad reset feature."
---

# /h-mad — 7-phase H-MAD Orchestrator (v2.2, standalone)

## Host runtime

This package supports Claude Code, OpenAI Codex, the Antigravity CLI (`agy`) and the grok CLI
(`grok`). In Codex, read [references/codex-runtime.md](references/codex-runtime.md) before
bootstrap; in agy, read [references/agy-runtime.md](references/agy-runtime.md) before
bootstrap; in grok, read [references/grok-runtime.md](references/grok-runtime.md) before
bootstrap. The adapter is required before any bootstrap, script, `hmad-dispatch` call or write.
A read-only `/h-mad status` on agy or grok may skip it, but only if it reads files through the
host's own file-read tool and runs no shell command at all (operator decision 2026-10-01; live
smoke V-11.1). On codex, read it anyway, because every codex step is a shell command. Apply
that adapter's path, hook, collaboration, checkpoint, and author/reviewer mappings as overrides
to the host-specific instructions below. Phase gates, state tokens, evidence requirements, and stop conditions do not
change between hosts.

Adapt a new host by adding an adapter beside these, never by rewriting the Claude spelling in
place: this one checkout is symlinked live into more than one host, so a global substitution
adapting it to one breaks the others the moment it lands.

## Activation surface

| Invocation | What you do |
|---|---|
| `/h-mad "<feature>"` | Auto-bootstrap if needed, then smart-resume via `h_mad_resume_decision.py`; act per the returned token. |
| `/h-mad do "<feature>"` | Auto-bootstrap if needed. Force-start Phase 5. Run `h_mad_do_preconditions.py` first and **read its `PRECONDITION:` token, never `$?`** — `FAIL` exits 0 like every other verdict; only `UNREADABLE` (bad `--repo-root`) is non-zero. Refuse on `FAIL`. |
| `/h-mad status [<feature>]` | Auto-bootstrap if needed. Read-only. Print state from `docs/.bkit-memory.json`. Surface stale `phase = "step5"` flags (heuristic: `autonomous_entry_ts > 60min` ago AND `halt_reason = null`). |
| `/h-mad reset "<feature>"` | Clear `orchestrator_state[<feature>]`. Do NOT delete docs or revert git. |
| `/h-mad bootstrap` | Explicit bootstrap (idempotent re-run). Not required as first step — feature invocations auto-bootstrap. |

## First-run auto-bootstrap

Before any feature-level operation, check:
1. Is the **skill itself** installed correctly? Run
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_install_check.py` and read the
   `INSTALL:` token — never `$?`, which is 0 on both verdicts by design. The check also reads
   `~/.agents/skills` and `~/.gemini/config/skills` (override with `HMAD_AGENTS_SKILLS_DIR` and
   `HMAD_AGY_SKILLS_DIR`, or with `--agents-skills-dir` and `--agy-skills-dir`); a root that does
   not exist adds no line, unless an enabled hook in the project's `.agents/hooks.json` runs a file
   under the agy root, which fails as `AGY_HOOK_TARGET_MISSING:<path>`.
2. Are the hooks **wired**, not merely installed? Run
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_hook_wiring.py` and read the `WIRING:`
   token. This one never halts — see §"Wired, not just installed" — but it is not
   optional to *run*: an unwired gate is silent in exactly the way a passing one is.
3. Are the **agents registered**? The eight agent definitions this skill dispatches
   (§"Teammate authors", §"Teammate audit leg", §"Helper work", §"Teammate change review") live in `agents/` inside
   this checkout and are reached through user-scope symlinks:

   ```bash
   for n in spec-author plan-author design-author implplan-author doc-auditor change-reviewer task-executor task-labeller; do
     ln -sfn "<checkout>/h-mad/agents/$n.md" "$HOME/.claude/agents/$n.md"
   done
   ```

   A **project-scoped** `.claude/agents/<name>.md` shadows the user-scope link, so a copy left
   there is a fork that drifts silently. Report it rather than deleting it — it may be a deliberate
   local override — per §"Bootstrap action" step 4, which owns this instruction. Verify with
   `head -2 ~/.claude/agents/<name>.md` naming the agent, not by trusting the link's presence:
   a dangling link and a correct one are both "present".
   Getting this wrong is not a halt: `Agent(subagent_type: "plan-author")` fails loudly with an
   unknown agent type (`Agent type '<name>' not found`), so it announces itself. Because Claude Code
   loads `~/.claude/agents/` at session start, symlinks created by bootstrap in the current session
   are not dispatchable by name until the next session; for the rest of the current session,
   dispatch `Agent(subagent_type: "general-purpose")` with the full text of
   `~/.claude/skills/h-mad/agents/<name>.md` prepended to the `prompt`.
4. Does `.h-mad/invariants.md` exist in the current working directory (project root)?
5. Does `docs/.bkit-memory.json` exist?

If 3, 4 or 5 is missing → run bootstrap automatically, then continue with the requested operation
— **except under `/h-mad status`, which is documented read-only and must stay so.** Item 3 writes
under `~/.claude/agents/`, i.e. outside the project entirely, so firing it from a read-only verb
widens that verb's blast radius into the user's home config. Under `status`, report item 3 as unmet
and register nothing.
Item 3 is in that trigger deliberately: the agents are the one thing on this list that a fresh
clone silently lacks, and a check with no action behind it detects the condition it was written to
repair and then leaves it in place.

`INSTALL: FAIL` → **halt `bootstrap:install_broken`** and surface the detail lines. Do not
bootstrap and do not proceed: the install is what decides *which* copy of every script and
prompt the run uses, so continuing means every later gate measures an unknown tree. The
detail lines each name one remedy, and all ten have one (the eleventh row, `AGY_SIBLING_COLLISION`, and the twelfth, `AGENTS_SIBLING_COLLISION`, are details that need none):

| detail line | what it means | remedy |
|---|---|---|
| `SKILL_NOT_INSTALLED` | no `~/.claude/skills/h-mad` at all | `ln -s <checkout> ~/.claude/skills/h-mad` |
| `SKILL_NOT_SYMLINK` | a real directory — a stale **copy** | remove it, then symlink as above |
| `SKILL_DANGLING` | symlink whose target is gone (checkout moved/deleted) | repoint it at the current checkout |
| `SKILL_NOT_A_CHECKOUT` | symlink resolves somewhere without `SKILL.md` | repoint it at a real h-mad checkout |
| `HOOK_NOT_INSTALLED` | no `~/.claude/hooks/h-mad-tdd-gate.sh` | `ln -s <checkout>/hooks/h-mad-tdd-gate.sh ~/.claude/hooks/h-mad-tdd-gate.sh` |
| `HOOK_DANGLING` | hook symlink whose target is gone | repoint it at the same checkout as the skills link |
| `SPLIT_INSTALL` | both links resolve, into **different** checkouts | repoint whichever is wrong so both name one checkout |
| `SIBLING_NOT_SYMLINK` | another skill from this checkout installed as a stale **copy** | remove the copy and link the checkout's skill in its place, in the skills directory the line names, which is one of `~/.claude/skills`, `~/.agents/skills` or `~/.gemini/config/skills` (for example `rm -rf ~/.agents/skills/handoff` then `ln -s <checkout>/handoff ~/.agents/skills/handoff`) |
| `SIBLING_DANGLING` | sibling symlink whose target is gone | repoint it at the current checkout |
| `SIBLING_WRONG_CHECKOUT` | sibling symlink resolving into a **different** checkout | repoint it at the same checkout as the skills link |
| `AGY_SIBLING_COLLISION` | a skill from this checkout that agy does not install (anything but `h-mad` and `handoff`) sits in `~/.gemini/config/skills` as a copy, a dangling link or another checkout's link; printed after the verdict and never changes it | none required: the operator decides whether that directory is theirs |
| `AGENTS_SIBLING_COLLISION` | a skill from this checkout (anything but `h-mad` and `handoff`) that is vendor-pinned in `~/.agents/.skill-lock.json` sits in `~/.agents/skills` as a copy, a dangling link or another checkout's link; printed after the verdict and never changes it | none required: it belongs to the pinned vendor install |

`SPLIT_INSTALL` is the one worth reading twice: each link looks correct on its own, so the
gate you arm and the gate the suites exercise are different files. The `SIBLING_*` lines are
the same hazard one directory over: **a correct h-mad link vouches for nothing but h-mad.**
Measured 2026-08-28 — `~/.claude/skills/h-mad` was a correct symlink while
`~/.claude/skills/handoff` was a plain directory copied 68 days earlier. The copy is what a
session loads, so a fix committed to the checkout a week before was invisible at runtime and
the skill behaved as its June self, while this check reported `INSTALL: PASS`. A skill that
is simply **not installed** is not an issue — only a present-but-wrong install is reported,
because only that one loads while misrepresenting its contents. Repairing the install is an
operator action; this check deliberately does not relink anything under `~/.claude` on its own.

`INSTALL: UNREADABLE` is a cannot-judge (exit 2), not a pass — nothing was examined, so it is
not a verdict about any install. **Halt `bootstrap:install_unreadable`**, distinct from
`install_broken` so a bad invocation is never recorded as a bad install. It fires only when a
path argument is empty, which means the caller passed one — re-run the documented command with
no arguments, which uses the defaults, and read the token again.

**No `INSTALL:` line at all — the script is missing, or the command errored — is itself the
finding: halt `bootstrap:install_broken`.** An absent checker is evidence *of* the condition
being checked, because the commonest way for this script not to exist is a `~/.claude/skills/h-mad`
that predates it — which is exactly the stale copy the check is for. This is the one branch where
"read the token, never `$?`" needs saying out loud: there is no token to read, and treating
silence as consent reproduces the original defect in the one place it is most likely to occur.

### Wired, not just installed

`INSTALL:` proves the two symlinks resolve. It cannot prove any settings file *references* them,
and an unwired hook is silent in the worst direction: writes and `advisor()` calls sail through
exactly as they would if the gate had approved them. Run the wiring check alongside it:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_hook_wiring.py
# WIRING: PASS
# WIRING: FAIL issues=1  +  detail lines
# WIRING: UNKNOWN reason=no_settings      (exit 2 — nothing was read)
```

**This is a separate verdict from `INSTALL:` on purpose, and it must never halt bootstrap.**
Wiring depends on enumerating settings sources this check cannot be certain it has seen — managed
policy, a `--settings` override, a plugin's own hooks, a project root above the directory it was
pointed at. A false `INSTALL: FAIL` halts the run and no local edit clears it, which is strictly
worse than a missed check. Treat `WIRING: FAIL` as a repair to make, not a reason to stop.

| detail line | what it means | remedy |
|---|---|---|
| `HOOK_NOT_WIRED:<hook>` | no `PreToolUse` entry anywhere names it | add `{ "matcher": "<tools>", "hooks": [{ "type": "command", "command": "bash $HOME/.claude/skills/h-mad/hooks/<hook>" }] }` to `~/.claude/settings.json` |
| `HOOK_WIRED_WRONG_MATCHER:<hook> matcher=… uncovered=…` | referenced, but no entry's matcher can fire on the named tools | widen the matcher to cover them — `Write\|Edit` for the TDD gate, `advisor` for the advisor gate |
| `HOOK_WIRED_STALE_PATH:<hook> -> <path>` | the command names a path that does not exist | repoint the command at `$HOME/.claude/skills/h-mad/hooks/<hook>`, which rides the verified skills symlink |

`uncovered=` is the field to read on a wrong matcher: a `Write`-only matcher gates half the TDD
gate's surface and stands down on every `Edit` — it looks wired, and it is, to the wrong half.
Sources searched are the user scope (`CLAUDE_CONFIG_DIR` when set, else `~/.claude`) plus every
`.claude/settings*.json` from the working directory **up**, because that is how project settings
resolve; a hook wired by an ancestor still counts. `UNKNOWN` means no settings file was readable
at all — a cannot-judge, carrying no `issues=` so it cannot be mistaken for a clean count.

Wiring can only be confirmed **live**, and hooks are snapshotted at session start, so this check
reports what the *next* session will load, not what this one is running.

Two properties of this check are worth knowing rather than rediscovering:

- **It is a copy detecting its own staleness.** If `~/.claude/skills/h-mad` is a stale copy,
  the script that runs is the *stale* one, so it can only report divergences the old copy is
  new enough to know about — and a copy predating this check reports nothing at all. A green
  `INSTALL: PASS` from an unknown vintage is therefore weaker evidence than it looks; the
  independent confirmation is that `ls -la` shows both paths as symlinks.
- **Both failure modes are silent by construction.** A stale copy keeps loading and running
  (the frontmatter is byte-identical, and both copies self-report the same version), and an
  absent hook link still leaves the gate *armed* whenever `settings.json` points at the
  skills path instead — so the tests and `references/codex-implementer-prompt.md` reference
  a path that does not exist while everything appears to work. Neither shows up as an error
  anywhere else, which is the whole reason this check exists.

## Bootstrap action

Run from current project root (`pwd` at invocation):

1. **Create docs structure**:
   ```bash
   mkdir -p docs/01-plan/features docs/02-design/features docs/03-analysis docs/04-report/features docs/archive .h-mad
   ```

2. **Create `docs/.bkit-memory.json` if missing**:
   ```bash
   [ -f docs/.bkit-memory.json ] || cat > docs/.bkit-memory.json <<'EOF'
   {
     "version": 1,
     "orchestrator_state": {}
   }
   EOF
   ```

3. **Copy invariants example if missing**:
   ```bash
   [ -f .h-mad/invariants.md ] || cp ~/.claude/skills/h-mad/invariants.example.md .h-mad/invariants.md
   ```

4. **Register the teammate agents** (idempotent; `ln -sfn` re-points an existing link rather than
   failing, so this is safe to re-run):
   ```bash
   SK="$(cd -P ~/.claude/skills/h-mad 2>/dev/null && pwd)"   # the skill dir; agents/ lives under it
   if [ -z "$SK" ] || [ ! -d "$SK/agents" ]; then
     echo "[h-mad] cannot resolve the skill checkout — agents NOT registered"
   else
     mkdir -p ~/.claude/agents
     for n in spec-author plan-author design-author implplan-author doc-auditor change-reviewer task-executor task-labeller; do
       ln -sfn "$SK/agents/$n.md" ~/.claude/agents/"$n".md
     done
     for n in spec-author plan-author design-author implplan-author doc-auditor change-reviewer task-executor task-labeller; do
       [ -r ~/.claude/agents/"$n".md ] || echo "DANGLING: $n — registration FAILED"
     done
   fi
   ```

   **The guard and the read-back loop are the point, not decoration.** `ln -sfn` exits 0 while
   writing a link to a path that does not exist, so an unresolvable `$SK` produces five broken
   agents silently — strictly worse than not registering at all, because item 3's verification then
   reports a *missing* file rather than a wrong one. A first cut of this step derived `$SK` with
   `dirname "$(readlink …)"`; measured on a constructed install whose skills symlink is **relative**,
   that collapses to `SK=/h-mad` and writes five dangling links, and `h_mad_install_check.py` calls
   the install `PASS` throughout because `Path.resolve()` resolves a relative link against the link's
   own directory. `cd -P` canonicalises in both that case and the stale-copy case.
   Then check nothing shadows them: a project-scoped `.claude/agents/<name>.md` outranks the
   user-scope link, so report any hit from `ls .claude/agents/ 2>/dev/null` rather than deleting
   it — a project copy may be somebody's deliberate local override.

5. **Surface customize-this notice**:
   > "Bootstrap complete. Customize `.h-mad/invariants.md` with your project's Axis B invariants (currently contains a worked example — replace with your own rules). The orchestrator inlines this file as the Axis B rubric for plan/design/impl-plan audits and the Phase 6a-prime architectural review."

6. **Optionally suggest** `.gitignore` additions if user wants `docs/.bkit-memory.json` out of git.

Bootstrap does NOT touch existing files, modify git config, or author plan/design/impl-plan docs.

## Decision routing (for `/h-mad "<feature>"`)

Run: `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature "<feature>" --session-id "<this session's id>"`

Pass `--session-id` so the collision check runs; omitting it opts out and you
will not see `owned_elsewhere`. On any token other than `owned_elsewhere`, `cannot_judge`,
`state_lost` or `migrated_by_bkit` (all four STOP — see the table below), claim the feature before working
it, and release when you stop:

```bash
# start_fresh — the feature does not exist yet, so create it in the same call.
# `--claim` ALONE exits 2 here with `ERROR: no such feature`, which is how every
# first-time claim used to fail exactly as documented (J5). `--started-ts` is
# optional: `--create` defaults it to now (J8).
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature "<feature>" --create --claim "<session-id>"

# every other route (resume_manual / enter_autonomous / halted) — the feature
# already exists, so claim it without --create.
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature "<feature>" --claim "<session-id>"
# ... work ... then release it, naming yourself — a live claim will not release
# anonymously, because --release + --claim used to bypass --claim's force guard (J45):
#   --feature "<feature>" --release --session-id "<session-id>"
# Keep the claim LIVE while you work (#126): pass --session-id on every phase write
# (the owner's --set refreshes the heartbeat), or beat explicitly between long stretches:
#   --feature "<feature>" --beat --session-id "<session-id>"
```

**A non-`owned_elsewhere` token guarantees the claim will be accepted** — among the tokens
that route to a claim at all; `cannot_judge`, `state_lost` and `migrated_by_bkit` STOP before any claim (there is
no readable record to claim, and `--claim` exits 2 with `no such feature`). The router
and `--claim` read the SAME staleness window (`h_mad_state_ownership`), so a claim
the router judged abandoned is takeable without `--force`. They used to disagree: the
router released a 19.6h-dead claim while `--claim` refused it outright, leaving
`--force` as the only way through. Keep `--force` for the one case it names — taking a
feature from a session that is still **live** (`owned_elsewhere`) — and treat needing
it on any other route as a bug, not as the usual step.

**The heartbeat is one clock; read all four before forcing, releasing, taking a stale
claim or calling a lane dead (row 1406).** A cold heartbeat misread a working lane as
dead four times — once into a `--force` claim that collided with a live run, once into
a plain `--claim` of a stale-looking feature. The `--claim` refusal carries a
`LIVENESS:` line, a `--claim` that takes another session's claim (stale or forced)
prints `STATE-WRITE: TAKEOVER … LIVENESS: …` on stderr, and
`h_mad_lane_liveness.py <lane> [--feature F]` prints the same reading on demand: `LIVE`
when ANY of the heartbeat, the owner's transcript mtime (subagent transcripts
included), the lane's newest non-merge commit inside the lane, or a process passing the
owner id to `--resume`/`-r`/`--session-id` is inside the ownership window; `QUIET` only
when every clock was read and is cold; `UNKNOWN` when nothing is fresh and a clock could
not be read; `NONE` when the lane holds no claim. A process match proves life, but its
absence proves nothing (the id is in argv only for resumed or explicit-id launches). A
Codex or agy owner's id is minted into the git dir, so it has no transcript clock
(`transcript_age=n/a`) and can still read QUIET. The commit clock is the lane's, so in a
shared checkout any session's commit reads LIVE. The `--claim` gate itself still reads
the heartbeat window; the evidence is what you read before acting on it, and a LIVE line
after a TAKEOVER means stop and coordinate.

**A claim that is never beaten looks abandoned two hours after Phase 0 (#126).** `--claim` was the only heartbeat writer, so a claim beat once and then aged toward the staleness window while its owner was busiest — measured live: one beat, then nothing for hours — and a stale-looking live claim is takeable by any other session with a plain `--claim`, which is the collision the window exists to prevent. Since 2026-10-25, `--claim`, `--release` and the resume oracle also refuse such a claim when the OWNER's own transcript proves it running inside the window (`owner_proven_live`). It never uses `ps`, which can be the claimant's own shell, so a Codex or agy owner, which has no transcript, is heartbeat-only. The lane's newest commit never counts, because in a shared checkout it can be anyone's. So `--beat` remains the reliable signal, and that check is a backstop. Two writers now beat it: **pass `--session-id "<session-id>"` on every `--set`** (a phase write by the owner is a sign of life and refreshes the heartbeat in the same write; a `--set` whose `--session-id` names a session other than the record's owner is refused with exit 2, so a displaced owner that names itself cannot keep writing phases — a `--set` with no `--session-id` is still accepted, which is one more reason to always pass it; `--set owner_session_id`/`owner_heartbeat_ts` is refused always — ownership moves only through `--claim`, `--release` and `--beat`), and `--beat --session-id "<session-id>"` between long dispatch stretches. A beat never claims: it refuses an unowned feature (that is `--claim`'s job) and a claim held by another session, so it cannot keep a dead claim alive. Residual: the beat still depends on the orchestrator writing state; wiring it into `hmad-dispatch exec`'s own watchdog heartbeat is the follow-up.

**Do not reach for `--create` on a resume route to make an error go away.** There,
`ERROR: no such feature` is a typo guard: the record is supposed to exist, so the
name is wrong. Adding `--create` would silently fork a second, empty record under
the misspelling and the run would proceed against it.

The claim is **advisory** — it reports who holds a feature and when they were
last seen, so a second session makes a deliberate choice rather than an
accidental one. A claim older than two hours is treated as abandoned, so a
crashed session cannot own a feature permanently.

**Then check that the state still describes reality**, before acting on it:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_staleness.py \
  docs/.bkit-memory.json --feature "<feature>"
```

The schema validates a record's *shape*; this compares its *contents* against
git. Both directions have been observed on one feature in a day — a
`halt_reason` that outlived its resolution by four hours and eight shipped
modules, and a `last_completed_phase` still reading 4 after Phase 5 had merged
and pushed. The first routes a resume to `halted` and presents a solved problem
as the blocker; the second routes to `enter_autonomous` and redoes merged work.
Both records validated cleanly the whole time.

`STALENESS: CLEAN` → the state is consistent with git. `STALENESS: SUSPECT` →
each finding names what disagrees. It **reports, it does not adjudicate** —
the failure being fixed is silent confidence, not a wrong guess, so decide
yourself and correct the record with `h_mad_state_write.py`.

| Token | What you do |
|---|---|
| `owned_elsewhere` | Another session holds this feature and was seen within the staleness window. **Stop and surface it** — print the owner id, heartbeat and the `h_mad_lane_liveness.py` reading, and ask whether to coordinate, take over (`--claim <id> --force`), or pick a different feature. Never proceed silently: two sessions on one feature produce contradictory conclusions on the same branch. |
| `cannot_judge` | The state file EXISTS and could not be read — truncated mid-write, invalid JSON, unreadable. **Stop. Do NOT initialize and do NOT resume.** This is the absence of evidence, not evidence of absence: the store may hold dozens of records and a live owner for this very feature. Inspect the file by hand, restore it from `git`/backup if it is corrupt, and only then re-run the oracle. It is deliberately not `start_fresh` — that token would have you create a record over a feature another session is working. **Second cause:** a declared or unknown non-Claude host (`HMAD_HOST` set to anything other than empty or `claude`) called without `--session-id` — the oracle cannot check ownership, so it refuses to route; pass the session id your adapter's §"Context budget and claims" names, do not repair the file. |
| `state_lost` | There is no record for this feature — no state file, or a file that parsed without it — **but its live phase documents exist** (`docs/01-plan/features/<feature>-brainstorm.md`, `.spec.md`, `.plan.md`, `.impl-plan.md`, or `docs/02-design/features/<feature>.design.md`). **Stop. Do NOT initialize and do NOT enter Phase 1.** The record was lost, not never written: measured 2026-10-07, a vanished `docs/.bkit-memory.json` (only its `.lock` left) over a feature with documents through Phase 6 answered `start_fresh` and would have restarted it from brainstorm. Restore the file from `git` if it is tracked; otherwise reconstruct the record — `h_mad_state_write.py --create --claim <session-id>`, then `--set last_completed_phase=<N>` inferred from which phase documents and audits exist — and re-run the oracle. `docs/archive/` is not consulted: an archived feature with no record closed its cycle and answers `start_fresh`. |
| `migrated_by_bkit` | The state file is missing, but `<root>/.bkit/state/memory.json` parses and holds this feature's record: **bkit's SessionStart migration moved it.** bkit (vendor plugin, `hooks/startup/migration.js`) renames `docs/.bkit-memory.json` — its legacy path, which h-mad uses — to `.bkit/state/memory.json` whenever the latter is absent, so the first session started in a fresh worktree moves the store away (reproduced 2026-10-26). **Stop. Do NOT initialize, do NOT reconstruct, do NOT claim.** The record is intact: restore it by **COPY**, never move — `cp <root>/.bkit/state/memory.json <root>/docs/.bkit-memory.json` (the oracle prints the exact command on stderr) — so bkit keeps a target and does not migrate again, then re-run the oracle. Every successful `h_mad_state_write.py` write and every `hmad-dispatch worktree-create` that learns the new path seeds `.bkit/state/memory.json` as `{}` when absent, so the migration has nothing to do; this token covers the stores that predate the seed. An unreadable or unusable `.bkit/state/memory.json` is not evidence and falls through to `state_lost` / `start_fresh`. |
| `start_fresh` | Initialize `orchestrator_state[<feature>]`. Enter Phase 1. Reached when there is no state file at all, or the file parsed and holds no record for this feature — and no live phase document for it exists (else `state_lost`) — which legitimately means nothing is claimed. |
| `resume_manual` | Print current phase + last marker. Ask "continue from phase <N>?" |
| `enter_autonomous` | Print "all manual checkpoints clear; entering autonomous block." Enter Phase 5. |
| `halted` | **Run the staleness check first** (below) — a halt that commits landed after is usually already resolved. Then print `halt_reason` + recovery hints (see `references/failure-recovery.md`). Ask "resume, retry, or reset?" |
| `complete` | Print "feature complete; see docs/archive/<YYYY-MM>/<feature>/". Exit. |

## Per-phase actions

See `references/phase-table.md` for the full gate table. Detailed inline protocols in `references/inline-protocols.md`.

1. **Brainstorm** — run inline brainstorm protocol (`references/inline-protocols.md §Phase 1`). Output: `docs/01-plan/features/<feature>-brainstorm.md`. Wait for user approval.
2. **Specify** — **dispatch the `spec-author` teammate** (§"Teammate authors"); the inline spec protocol (`references/inline-protocols.md §Phase 2`) is its contract, not yours to execute. Output: `docs/01-plan/features/<feature>.spec.md`. Wait for user approval.
3. **Plan + Audit-Plan** — **dispatch the `plan-author` teammate** (§"Teammate authors"); the inline plan protocol (`references/inline-protocols.md §Phase 3`) is its contract. Output: `docs/01-plan/features/<feature>.plan.md`. Wait for user-approved v1.0, then auto-cycle: audit-plan on **two surfaces** (§"Never gate on one audit pass" chooses which) → awk gate on the union → if must-fix > 0 OR should-fix > 0, surface bullets, then **re-dispatch `plan-author` with the findings** (§"Teammate authors" — a revision routes to the owning author, never to you) → re-audit. **Exit ONLY when build-class must-fix = 0 on BOTH surfaces at one commit AND every remaining finding — build-class should-fixes, measurement-class musts and shoulds — is either fixed or acknowledged.** The class is the reviewer's `class:` line under each bullet (§"Finding class — build vs measurement"): build-class findings drive the loop up to the cap of TWO gating rounds per revision line (§"Document-audit round cap — Phase 5 is the gate"), after which an open build-class must becomes an `OPEN-DECISION` on its impl-plan Task and is settled in 5d — and measurement-class findings never hold a phase past the round in which build-class reached 0: they go to the sidecar with their re-run command as the ack text. Operator escape at any cycle: author `.audit.v<N+1>.md` with `## Acknowledged-not-fixed` section listing the should-fix and measurement-class items the operator chooses to defer, commit `[audit-override]`, and the gate treats those items as cleared (a bullet the reviewer tagged `class: build` is refused by the sidecar and reported `ack_refused=N` on the `GATE-CLASS:` line).
4. **Design + Audit-Design** — **dispatch the `design-author` teammate** (§"Teammate authors"); the inline design protocol (`references/inline-protocols.md §Phase 4`) is its contract. Output: `docs/02-design/features/<feature>.design.md`. Same audit cycle pattern as Phase 3, with revisions re-dispatched to `design-author`. Back-propagation: if design revision invalidates a plan decision, return to Phase 3 to re-clean, then re-enter Phase 4 audit from cycle 1.
5. **Implementation (autonomous)** — see Phase 5 sub-section below.
6. **Verification (autonomous)** — run inline gap analysis (`references/inline-protocols.md §Phase 6`). If match rate < 90%, run inline iterate (`references/inline-protocols.md §Phase 6b`) — 5-cycle cap. Loop until ≥90% AND 100% test pass. Phase 6a-prime is an agy architectural review before gap analysis.
7. **Closure (autonomous)** — **run the precondition gate first; it is what makes the 6-before-7 ordering real rather than documented:**
   ```bash
   python3 ~/.claude/skills/h-mad/scripts/h_mad_phase7_preconditions.py \
     docs/.bkit-memory.json --feature <feature>
   ```
   Carry every `WARNING` line into the Phase-7 report, including `review_non_independent`, `review_independence_unrecorded` and `review_independence_malformed`; warnings do not change readiness.

   **Review attribution (FR-7, performed at each review leg).** After each 5e-review, 5e-verify and 6a-prime leg, run `h_mad_state_write.py docs/.bkit-memory.json --feature <feature> --session-id <owner-session-id> --append review_independence='{"leg":"<leg>","module":"<module>","reviewer":"<reviewer>","implementer":"<implementer>","independent":false}'` for every implementer, applying the attribution rule below and replacing the example boolean with the computed value: `independent` is `reviewer != implementer`. The 5e legs review one module; record one 6a-prime entry per module for the whole-diff review. Encode actual values as JSON and shell-quote the complete argument; do not interpolate raw agent-supplied text into shell syntax.

   `implementer` is read from the dispatch that authored the reviewed code, never read from `implementer_switch.to` or from the `implementer` field, which describe routing. Its agent is the resolved `TDD-IMPLEMENTER:` token used as `--agent` to `h_mad_assemble_tdd.py` when staging that dispatch; a Claude in-session fallback uses that token's `claude` value. Authors are the accepted 5e GREEN dispatch and every accepted fix dispatch for the module. A 5d RED dispatch authors no implementation; a dispatch that halted, timed out or was rejected authored nothing.

   The author set is read from `implementation_authors` only, never from earlier `review_independence` entries or an in-context dispatch list. Well-formed means `property_valid("implementation_authors", [entry])`; the orchestrator applies this schema definition, and no script reads the author field to compute attribution. For module M, collect the `agent` values whose `module` is M, preserving array order to identify the latest entry. If the reviewer is in that module's author set, `implementer` is the reviewer and `independent` is `false`. Otherwise `implementer` is the agent of the module's latest entry and `independent` is `true`. Resume uses the same durable field, even when dispatch context is gone. The writer does not check attribution; the Phase-7 check only verifies consistency between the recorded identities and boolean.

   When no author can be read, no entry is written for the module, in exactly three cases: the record has no `implementation_authors` field (a pre-field feature); the field is present and holds no well-formed entry for that module; or the field is present and is not a list, or holds an entry that is not well-formed (even for another module, invalidating the record's author set). An absent field is never an empty author set. `review_independence_unrecorded` detects no 6a-prime entry at all, but cannot detect one missing module among other recorded modules.

   Before 7f merges, the state file is main's while the Phase-6 artifacts (the analysis, its `v<N>` versions, any parked mutation spec) exist only in the feature worktree: pass `--docs-root <worktree>/docs`, which moves the default `--analysis`, the versioned-analysis check and the parked-spec check together. Without it the gate reads main's docs and reports `BLOCKED` on artifacts it never looked at (HemaSuite #101 closed Phase 7 through a hand-written `check(…, docs_root=…)` for this reason). A `--docs-root` that is not a directory is an operational error (exit 2), never a verdict.
   Parse the **token**, not `$?` (exit 0 on any verdict, 2 on operational error). `PHASE7: BLOCKED` → halt `step7:verification_not_run` and address each blocker. It refuses to close a feature that never ran Phase 6, whose analysis is missing or states no match rate, whose rate is below threshold, whose 6a-prime returned `WITH_FIXES`/`NO`, that carries an open halt, or that parked a mutation spec (`<name>.json.pending`) and never moved it back (#142). A `SKIPPED_NO_PANE` archreview **blocks** the gate — a headless `exec agy` review satisfies the gate. Then `h_mad_telemetry.py record`, inline report + archive (`references/inline-protocols.md §Phase 7`), then `git add -A -- ':/' ':(top,exclude)*.done' && git add -u -- ':/' && git commit`, then **7f — integrate** (below), then `git push origin <base>`.

   **7f — integrate the branch, which nothing used to do. It runs AFTER 7d's commit and before 7e's push**: 7c's archive `mv`s tracked documents, so a 7f placed before the commit blocks on its own `dirty_tree` gate on every real run. 5c creates `feature/NNN-<slug>` and this phase's exit criterion is "Push to origin/main succeeds", but no step between them merges: the stated commands cannot reach the stated exit, and the merge was performed by hand every time, carried between sessions as a handoff Next Step. Run `python3 ~/.claude/skills/h-mad/scripts/h_mad_phase7_integrate.py --repo-root <repo> --feature <feature> [--base <b>] [--route merge|pr|keep] [--apply]` and read the `INTEGRATE:` token, **never `$?`** — every verdict exits 0 and only `UNREADABLE` (git did not answer) is non-zero. Without `--apply` it PLANS: it evaluates every gate, prints the exact commands, and touches nothing. `BLOCKED` names its reasons and each is a fact about the world, not an error. The full set, which `test_h_mad_phase7_integrate_blockers_are_documented` holds to the script: `detached_head`, `dirty_tree:N_tracked_changes`, `no_default_base`, `unknown_base:<b>`, `base_not_a_local_branch:<b>`, `unknown_branch:<b>`, `base_is_the_feature_branch:<b>`, `base_checked_out_elsewhere:<worktree>`, `untracked_collision:<n>:<path>`, `nothing_to_integrate:<branch>_is_not_ahead_of_<base>`. **`--base` must name a LOCAL branch.** A tag, a raw sha or a remote-tracking ref would make `git checkout` DETACH — the merge would land on no branch, the base would never move, and the verdict would say MERGED at exit 0 — so those are refused as `base_not_a_local_branch:<b>` rather than followed. On a checkout whose trunk exists only as `origin/main` the remedy is to create it (`git branch main origin/main`); 7f will not do that for you, because which commit the local trunk should start at is not 7f's judgement to make. `no_default_base` is the same situation reached without `--base`: no `origin/HEAD` is set and neither `main` nor `master` exists locally. **`identity=y` is the verification half**: when the base is strictly behind, a `--no-ff` merge writes a tree byte-identical to the feature tip, so the green suite run you already have covers the merged result by proof rather than by a second eight-minute measurement (measured 2026-09-07 on `doc-block-exec`: both trees `381aaba2`). `identity=n` means the base moved and the merged tree is NEW — pass `--suite "<suite command>"` with `--apply` and 7f runs it on the merged tree, appending `suite=PASS rc=0` or `suite=FAIL rc=N` to the `MERGED` token (`suite=covered` when `identity=y`, `suite=unrun` when no command was given). **7e pushes only on `identity=y` or `suite=PASS`**; it was a printed reminder, and a test passed on the branch and failed on merged main that way. It never pushes, never deletes a branch, and never removes a worktree: sibling worktrees are REPORTED with their removal command, because that lane may have a live owner and #111 sat across five handoffs precisely because nothing in the protocol named it. **The route is recorded, never asked** — Phase 7 is autonomous, so a blocking three-option menu would break its contract; `keep` and `pr` integrate nothing and are not failures.

## Phase 5 (Implementation) sub-steps

**Read [references/phase5-substeps.md](references/phase5-substeps.md) in full at Phase 5 start, before the substrate preflight and before step 5a.** It holds every Phase 5 sub-step (5a–5f), the codex-authorship enforcement, and how 5d/5e are dispatched, watched and made visible. Nothing in Phase 5 may run from memory of it. **Its opening part — everything above `### Codex authors Phase 5` (substrate preflight, dispatch enforcement, pinning the agents, handle liveness) — and its §"Dispatch channels and their guarantees" also govern audit dispatches: read those two parts before a session's first audit dispatch, even before Phase 5.**

A cross-reference `SKILL.md §"…"` to any of these now resolves in `references/phase5-substeps.md`:

- §"Codex authors Phase 5 — enforced, not just instructed"
- §"Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot"
- §"Watching a headless dispatch"
- §"Making a dispatch visible in Orca (zsh shell pane)"
- §"Dispatch channels and their guarantees"
- §"Exception — `exec agy` on an audit phase: fill the report-file slot" (paragraph)
- §"A missing report on the `exec` path" (paragraph)
- §"Pin the agents once (Orca) — do it while identity is known" (paragraph)
- §"Give every dispatch its own `--out`" (paragraph)

## Phase 5 parallel fanout (Orca only)

The serial Phase 5 path above remains the default and fallback. First partition the
impl-plan: a task with `Dependencies on other tasks: None` is independent; every
other task is dependent and remains serial in topological order on the shared tree.

Engage fanout IFF `hmad-dispatch env` shows `substrate=orca` (the command displays
`substrate: orca`) AND `orchestration: on` AND there are `≥2 independent` tasks.
If any condition is unmet, use the existing serial fallback.

For each independent task, run at most `HMAD_ORCA_MAX_WORKTREES` live worktrees
(default 4). With a staged prompt, `worktree-create <module> --base
<feature-branch> --prompt-file <staged-prompt>` creates the worktree and registers
the task in one operation. It keeps stdout exactly the worktree selector and
prints `[H-MAD] worktree_task task=<id> selector=<sel>` on stderr; capture that
`<id>` as the task-id for `dispatch`, `await`, and `gate-create`. If no prompt
file is supplied, `worktree-create` registers no task: use the separate Tier-2
`task-create` then `dispatch --to <selector>` path and its returned task-id.
Then `await` the worker; stamp progress checkpoints and run the **winner-merge decision gate**
in place of a bare `git merge --no-ff` (see `references/orchestration-mode.md`
§"Winner-merge decision gate" and §"Progress checkpoints"); then `worktree-rm
<selector> --base <feature-branch>`. Tasks beyond the cap queue and log
`[H-MAD] worktree_queued module=<module>`.

**Pass `--base <feature-branch>` on fanout teardown.** The comparison base defaults to the
first of `origin/HEAD`, `main`, `master` that resolves, and a module worktree is branched
from the *feature* branch — so every commit on that feature is "not in `main`" and teardown
refuses for as long as the feature is unmerged. Measured live: a freshly created module
worktree reported 7 commits ahead of `main` and 1 ahead of its real base. With `--base` set
to the feature branch, the guard fires only on commits the feature branch does not have —
which is exactly the work that would be lost.

The gate engages only when `orchestration: on`: a clean verdict + clean merge
auto-records a `yes` decision (`[H-MAD] merge_gate auto-resolved`) without pausing,
while a `DRIFT`/non-clean verdict or a merge conflict opens a **blocking** gate for
a human decision (conflict path first runs `git merge --abort` and emits
`[H-MAD] merge_conflict module=<module>`). When orchestration is off, the merge is
the unchanged serial `git merge --no-ff`, conflict-aborted and re-dispatched serially
as before — no gate. On any Phase-5 halt during fanout, enumerate with `worktree-ps`
and run `worktree-rm` for every worktree in the fanout group. `worktree-rm`
refuses with rc=1 and removes nothing when the resolved worktree has uncommitted
work (`worktree_has_uncommitted_work`) or commits not reachable from its
comparison base (`worktree_has_unmerged_commits`); commit or merge the work
first, or pass `--force` when discarding it is intentional. `--force` skips both
guards and prints `[H-MAD] worktree-rm forced selector=<sel> — guards skipped`.
An unresolvable or ambiguous selector, or a truncated `worktree-ps` listing,
means the worktree cannot be checked and does not by itself refuse removal.
This teardown remains idempotent: a gone selector logs and no-ops.

## Phase 6 (Verification) sub-steps

- **6a-prime** — architectural review via agy (`references/agy-architectural-reviewer-prompt.md`). Inputs: Phase 5 diff (BASE = 5c sha; HEAD = 5g sha) + audited design. **Derive the 5c sha, never `git merge-base`.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_baseline_sha.py --branch <feature-branch> [--trunk main]`, reading the `BASELINE:` token, never `$?`. 5c is `git checkout -b …; commit impl-plan + audit files`, so the 5c commit is the branch's FIRST commit and `git merge-base main <branch>` returns the commit it forked FROM — off by exactly the impl-plan commit, and off plausibly, since both are real shas on the right branch. Measured (J41): merge-base `b5c8f41` against real 5c `730cc16`, 313 lines apart — the impl-plan and its three audits, which the wrong base feeds into the review as newly-added content when they are a separate INPUT to it. `UNVERIFIED` is a verdict, not an error: the branch's first commit does not touch an impl-plan, so something was committed before 5c and the rule does not hold — find the commit by hand, and note the token reports it as `candidate=` rather than `sha=` precisely so an unvouched value cannot be scraped as the answer. Only `OK` carries `sha=`.  Preflight with `command -v agy`; if the `agy` CLI is absent, halt `step6a-prime:no_reviewer_pane`. Then headlessly dispatch with `exec agy`; `exec agy` satisfies the gate and does not require a resolved pane. **Cite files in the prompt by ABSOLUTE path.** A correct `--cd` is not sufficient: the stream's `init.cwd` confirmed the repo root while agy resolved repo-relative citations against `~/.gemini/antigravity-cli/scratch/…`, every read failed, and the review proceeded on the inlined text alone. Say so in the prompt too — instruct the reviewer to return `ASSESSMENT: NO` if its reads fail, so a blind review declares itself instead of guessing. **Brief the reviewer with the question and the paths, never the answer** (#153): the same 740 KB prompt returned `tools=12` with no appendix and `tools=0` once it was handed the confirmed conclusion and told not to re-litigate — and the blind run still wrote 2154 fluent bytes. An appendix that states what the review should find removes its reason to read. The template now ends with the verdict line as the LAST thing it says, because three dispatches that were asked for "a final line" mid-template returned no `ASSESSMENT:` at all. **Position was necessary and not sufficient** — two more dispatches (2026-09-09, `#18 gateway-consolidation`, `tools=11` and `tools=19`, both `EVIDENCE: PASS`) still returned none, because the only exemplar the template showed was a FENCED SCHEMA, `ASSESSMENT: <A | B | C>`, in the same angle-bracket grammar the file uses for orchestrator-filled slots — so the one place it showed the line it wanted read as somebody else's placeholder, wrapped in the very fence the prose forbids. Both replies instead opened with `**Assessment**: YES`. The template now shows the three verdicts as complete, unfenced, copyable lines. A sixth dispatch against that fix emitted the token and still invented its word (`DRIFTED`, borrowed from the 5e spec reviewer's `VERDICT: COMPLIANT | DRIFT`), so the template also declares the set CLOSED and names the words that were actually tried. Guarded by `tests/test_h_mad_verdict_exemplar.py`; both tests that had asserted the old fenced tail were pinning the defect and now assert the literals. This is the only pass positioned to catch design-level problems — design-vs-spec drift, an exception hierarchy that does not scale, or a gate at the wrong altitude — which document audits and code-level gap analysis miss by construction. Read the `ASSESSMENT:` with `h_mad_extract_verdict.py`, never by grepping, because an empty review must not be indistinguishable from `READY_TO_MERGE`; **and then prove the review actually read something before you record a pass** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_review_evidence.py <the dispatch's --log>`, reading the `EVIDENCE:` token, never `$?`. `PASS` means at least one tool call reached `DONE` — necessary, and not sufficient for a CLEAN, because this channel's report-file contract costs one successful call by itself: `h_mad_archreview_cycle.py score` additionally refuses a `READY_TO_MERGE` resting on no more successful calls than this channel's report-file contract costs by itself (`DELIVERY_FLOOR = 1`, because the template says that write is the only one the reviewer may make), emitting `ARCHREVIEW: LOW_EVIDENCE_CLEAN tools=N floor=M` and recording nothing. A `WITH_FIXES` or `NO` at the same count IS recorded — findings are evidence of reading, a clean is not. `NONE` means the reviewer judged without reading anything → halt `step6a-prime:review_read_nothing`; do not record the `ASSESSMENT:`, fix the prompt and re-dispatch. `UNREADABLE` (exit 2) is a cannot-judge carrying no counts — no `--log` was passed, it is empty, or it is not an agy NDJSON transcript (`reason=unsupported_format`) — and is not a verdict about the review. The last reason is #154: `EVIDENCE: NONE tools=0` once fired on a **codex** review that had verifiably read the tree, because the gate parses agy's NDJSON and codex transcripts are `codex-text`; a zero from an instrument that cannot read its input is not a measurement. A codex review still does not satisfy this gate — dispatch 6a-prime with `exec agy` — and the token now says so instead of diagnosing a review that read nothing. **This is the same rule as the sentence before it, one level up.** `extract_verdict` closes the case where the agent says *nothing*; this closes the case where it says something *fluent* with nothing beneath it, which is harder to spot because it reads like a review. Measured: a 6a-prime dispatch whose single `view_file` errored returned `ASSESSMENT: READY_TO_MERGE` in 1510 confident bytes, and rc, the extractor and the Phase-7 gate all took it. Note the gate counts **any** tool reaching `DONE` and knows no tool names — the first probe of this defect hardcoded `view_file|grep_search` from an earlier dispatch and reported a false zero when agy switched to `run_command`. It also does **not** gate on `result.status`, because `hmad-dispatch` ignores that field for a sound reason (a single denied tool call yields `status: ERROR` beside a complete answer), so gating on it here would re-create the false `no_verdict` halt that reasoning prevents; halt `step6a-prime:architectural_review_failed` on `WITH_FIXES` or `NO`, and `step6a-prime:no_verdict` if none can be extracted after a re-read and re-dispatch. Immediately after extraction, write the extracted `ASSESSMENT:` into `orchestrator_state[<feature>].archreview` using `h_mad_state_write.py`, then read `orchestrator_state[<feature>].archreview` back and compare it to the value written. Capture the value line-scoped with `sed -n 's/^ASSESSMENT: //p'` rather than stripping the prefix off whatever came back. `h_mad_extract_verdict.py` now prints its `[H-MAD]` marker to **stderr**, so its stdout is only the verdict line and a bare `$(...)` capture is safe (J26, fixed) — but stay line-scoped anyway: the extractor is the one script whose stdout is a *value* rather than a report, and a line-scoped capture cannot be broken by anything a future version adds to stdout. Strict-only validation is not sufficient because `archreview` is not in the schema's `required` array: `STATE: PASS` can hide a dropped write. If no reviewer exists at all, the reviewer-less route records `SKIPPED_OPERATOR_OVERRIDE` as a deliberate operator decision and surfaces it as a warning in the Phase-7 report; `SKIPPED_OPERATOR_OVERRIDE` is not a pass. A pane that did not resolve is handled by headless dispatch, not that ordinary skip route. For this readback check, explicitly do not rely on h_mad_state_validate.py --strict-only. **After `WITH_FIXES`:** for each accepted fix dispatch, run `h_mad_state_write.py docs/.bkit-memory.json --feature <feature> --session-id <owner-session-id> --append implementation_authors='{"module":"<module>","agent":"<agent>"}'` before the next leg that reviews the fixed code. The agent is that accepted dispatch's resolved `TDD-IMPLEMENTER:` value used as `--agent` when staging, or `claude` for the in-session fallback, never a routing field. Encode actual values as JSON and shell-quote the complete argument; correct and retry a refused append before review.
- **6a** — run inline gap analysis. Save it as `docs/03-analysis/<feature>.analysis.v1.md` AND as the latest copy `docs/03-analysis/<feature>.analysis.md`; parse match rate from the latest copy. A delegated verifier's report is this file — never a `gap.v<N>.md` or other name.
- **6b** — if < 90%, run inline iterate (5-cycle cap). Each cycle writes the next `docs/03-analysis/<feature>.analysis.v<N>.md` — never overwrite a previous cycle's file — and refreshes the latest copy. Telemetry's `iterate_cycles` is `max(N) - 1` over these files, and `h_mad_phase7_preconditions.py` blocks `analysis_unversioned` without them. Loop until ≥90% AND 100% test pass.

### Surfacing diffs at review gates (Orca only)

At Phase 3 plan approval, Phase 4 design approval, and Phase 6a verification, the
orchestrator MAY call `hmad-dispatch file-open-changed --mode diff` (or
`hmad-dispatch file-diff <path>`) to surface the diff in Orca's editor. This is
best-effort and non-blocking: a non-zero result (substrate≠orca or no editor) is
logged as `[H-MAD] <feature> diff_surface_skipped`, and the gate proceeds exactly
as today. Surfacing is never a gate precondition; the cmux review flow is unchanged.

HemaSuite may use `file-diff <manuscript.docx>` to surface a generated manuscript
DOCX; this is documented usage only, with no HemaSuite code in this feature.

## `exec` bounds itself even when you omit `--timeout`

An omitted `--timeout` used to mean **no ceiling at all** — the deadline branch is skipped and the
wrapper waits on the pid forever. It now defaults to 3600, chosen to sit clear of the longest
timeout this skill documents (1800) so a legitimate dispatch can never reach it; an explicit
`--timeout` of any value still wins.

The symptom it bounds is real and intermittent: `exec agy` twice kept running for its full timeout
**after** agy had finished its turn and written the report — the `--log` ends with the `result`
event and the `.done` marker exists within about four minutes, but the wrapper waits on the PID
rather than on the completion signal already sitting on disk. Two of 29 cycles; codex on the same
runner exits normally every time, and it did not reproduce across roughly 70 later agy execs.
`audit-cycle` always passes a `--timeout`, so its cost was capped; a hand-run `exec agy` — the
reflex for Phases 1–4 — had no cap.

**`rc=124` now says which case it is.** That number is the whole operational cost of this fault:
the report and its `.done` marker are already on disk, so a coordinator reading a bare 124
re-dispatches work that is complete and gateable. The exit line now distinguishes "a verdict WAS
recovered — check the report before re-dispatching" from "no verdict recovered; re-dispatch".

**`exec-pane` needs no ceiling of its own.** It forwards `--timeout` only when given, which looks
like a second unbounded path, but it builds `<self> exec <agent> …` and so inherits this one. A
test pins that, because a refactor calling the agent directly would silently reopen the gap.

**Still owed, deliberately not built:** reaping on the `<report>.done` marker would end the wait
when the work actually finishes rather than at the ceiling. It needs the wrapper to learn the
report path, which it does not currently know — `--out` is the verdict file, and the report path
lives inside the prompt. With a ceiling and a legible 124 in place the remaining cost is one
timeout on an intermittent fault, so the smaller fix shipped and the better one is recorded.

## Reading a dispatch verdict

Every dispatch that gates a decision ends in a machine-parsed line, and each is
read off a live pane:

| Step | Key | Values |
|---|---|---|
| 5d / 5e codex | `STATUS:` | `DONE` \| `DONE_WITH_CONCERNS` \| `BLOCKED` \| `NEEDS_CONTEXT` |
| 5e-review agy | `VERDICT:` | `COMPLIANT` \| `DRIFT` |
| 6a-prime agy | `ASSESSMENT:` | `READY_TO_MERGE` \| `WITH_FIXES` \| `NO` |

**Never grep the scrape for the halt value.** The halt conditions are phrased
as "halt on `DRIFT`", "halt on `WITH_FIXES` or `NO`" — so a grep that finds
nothing looks identical to a clean pass. An agent that dispatched, went idle
and emitted nothing therefore reads as approval, and the module gets committed
on silence. A prior module's `STATUS: DONE` still in scrollback is the same
trap from the other direction.

**Third trap — the prompt's own contract echo (J17).** The 5d/5e dispatch prompt
states its output contract (`STATUS: DONE`, on its own line, as the canonical
form). That line is *typed into the pane* and echoed back. When the agent emits
nothing — a submit-Enter swallowed mid-boot, say — the buffer holds only the
echoed prompt, and the extractor reads the contract's own `STATUS: DONE` as the
agent's verdict: a false DONE, exit 0. The `key-must-start-the-line` guard does
not catch it because the echoed contract line *does* start the line. This is not
audit-immune-by-nature: the assembled audit prompt likewise echoes a complete
`<sentinel>-BEGIN … -END` pair (assemble substitutes the concrete sentinel), so
`extract_report` shares the trap on a raw scrape — the per-cycle sentinel only
defeats a *stale prior cycle*, not this *same-run echo*.

**The fix — always pass `--after-marker`.** `hmad-dispatch send` appends a fixed
boundary line (`===HMAD-DISPATCH-BOUNDARY===`) as the final line of every prompt.
The agent's reply always renders *after* the echoed prompt, so the extractors
slice to the region past the boundary's **last** occurrence and never re-read the
echoed contract. Taking the last occurrence also fences off prior-cycle
scrollback. **`--after-marker` is mandatory on every scrape extraction** — a
scrape missing the boundary fails closed (the dispatch was never captured, or you
read the wrong pane), which is correct.

Extract like this — fails closed on silence, echo, and stale scrollback:

```bash
# `ask` = send + wait-idle + full-buffer read in one call (the send/wait/read
# dance that repeats every audit). Its stdout is exactly the reply buffer;
# send/wait chatter goes to stderr. --out captures it for the extractor.
hmad-dispatch ask <agent> <promptfile> --out /tmp/scrape_<feature>_<module>.txt
python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_verdict.py \
  /tmp/scrape_<feature>_<module>.txt --key VERDICT --after-marker \
  --feature <feature> --phase 5e
```

`--after-marker` with no value uses the default boundary; pass a value only to
override it. `h_mad_extract_report.py` takes the same flag.

**Idle is not completion — gate `wait` on positive evidence.** `wait`'s idle
signal (native tui-idle, then two matching snapshots) reports done for a pane
parked on `Waiting for background terminal`: Codex delegated to a background
terminal, the TUI frame is static, generation still in flight. Idle is a *first
gate*, never proof. For a 5d/5e GREEN, require the verdict line **and** a
full-suite result in the same frame, and refuse a known-busy frame:

```bash
hmad-dispatch wait codex --timeout 900 \
  --until-regex 'STATUS:.*(DONE|BLOCKED|NEEDS_CONTEXT)' \
  --until-regex '[0-9]{3,4} passed' \
  --not-while-regex 'Waiting for background terminal'
```

Every `--until-regex` must match (repeatable = AND); any `--not-while-regex`
match keeps polling. Only then extract the verdict from the boundary-sliced tail.

If the pane was already dispatched into (you only need to re-read), use
`hmad-dispatch read <agent> --from-start`, never `--lines N` — a tail can render
a stale overdrawn frame (J3).

If you bypass the wrapper and scrape a pane read-only with the raw CLI
(`orca terminal read --terminal <handle> --limit <n> --json`), the scrollback
lines live at `.result.terminal.tail[]` — **not** `.rows[]` or `.lines[]`.
`jq -r '.result.terminal.tail[]?'` to grep a live pane; `--limit <n>` pulls more
retained rows. This is one instance of the `.result` envelope rule, which applies
to every raw `orca … --json` call and is stated once in
`references/agent-substrate.md` §"The `.result` envelope — assert the container
before reading a count": a wrong path yields empty, empty reads as "no match", and
the two are indistinguishable until you assert the container with `jq -e`. Read it
before writing any parser against a raw orca payload.

It takes the **last** matching line, validates the value against the contract,
and exits 2 printing nothing when the line is absent, empty, off-contract, or the
boundary marker is missing. Treat exit 2 as "no verdict", never as a pass:
re-read with `--from-start` (a larger tail does not escape an overdrawn frame
region — J3), and if the agent genuinely produced nothing, `hmad-dispatch clear
<agent>` and re-dispatch. Repeated silence is a halt
(`step5e:no_verdict:<module>`), not a reason to proceed.

## Verifying a review finding before acting on it

A finding from agy or a code reviewer arrives verdict-shaped — a premise, a consequence, and a
prescription — and the prescription is the part you are tempted to apply. Before applying it,
**check its stated premise against the source**. If the premise is wrong, the prescription is
usually wrong in a specific and expensive way: it is aimed at a mechanism that is not there.

Measured: in one session **2 of 5 findings were right about the symptom and wrong about the cause**.
Applying either prescription verbatim would have introduced a defect while closing a real finding —
the reviewer had seen something genuine and misattributed it, so the fix moved the bug rather than
removing it.

This is not a licence to dismiss findings. A finding whose premise fails to check is still
evidence that *something* is wrong: the reviewer saw a real symptom. Re-derive the cause from the
source, then fix that — and say in the response that the premise did not hold, so the next reviewer
is not re-litigating a settled point.

Cheap and mechanical: for each finding, open the file and line it names and confirm the code says
what the finding says it says. Most premises check out in seconds, and the ones that do not are
where the expensive mistakes live.

### Close the class, never the instance

Once a premise checks out, classify the finding before you fix it: is it a **singleton**, or one
**instance of an open-ended set**? Launch APIs, alias forms, escape sequences, error kinds, file
extensions — anything a reviewer can keep producing new members of. For a singleton, fix it and move
on. For an instance of a class, the fix is not the instance:

1. **Name the axis** the class ranges over, in the document.
2. **Write a rule over that axis** — a pattern over the resolved target, not the member the reviewer
   happened to name.
3. **State the residual exactly** — what the rule provably does *not* cover, spelled out as a
   concrete category, never "and similar" or an implied "etc.".
4. **Say in the response which of the three you did**, so the next reviewer audits the rule and the
   residual instead of proposing member N+1.

Skip any of the three and a reviewer supplies the next member next cycle, one per cycle, and each
one costs a full round trip.

**Measured — HemaSuite `#18 gateway-consolidation` plan audit, cycles 20–29** (reports
`gateway-consolidation.plan.audit.v{20,23..29}.codex.md`, plan Version History v1.25–v1.30). Seven
cycles went to one guard's scanner coverage, and they ran on **two** axes, not one:

- **Axis 1 — the spawn-API set.** c20, c23, c24, one API family per cycle. Closed at v1.25 by
  replacing the enumerated list with *a pattern over the resolved target* — "any `subprocess.*`,
  any `asyncio.create_subprocess_*`, `os.{system,popen,exec*,spawn*,posix_spawn*}`, `pty.spawn`
  … rather than a list that loses one API per audit cycle".
- **Axis 2 — how a callee resolves to a target.** Generalising axis 1 *opened* this one, and the
  same enumeration ran again: c26 function-local imports, c27 one-hop assignment aliases, c28
  transitive aliases, c29 literal `getattr`. Four more cycles.

Axis 2 did **not** close by generalising a third time. It closed at v1.30 when the residual was
stated exactly — *"the static-scanner residual is stated exactly as computed callees, so scanner
coverage stops being an open series."* **Step 3 is the one that ends the series**, and step 1 is why:
a rule with no named axis silently has more axes than you think, and generalising the first one just
moves the enumeration to the second.

Two neighbouring cycles look like this series and are not — count them against their own causes, not
this rule: c25 was fix-introduced (a pattern written at c20 missed `self._resolve_cli()`), and c18
was a behavioural premise stated without a command. The brief that filed this rule folded both in
and reported nine; re-derived from the reports, the enumeration itself is seven.

### Record a rejected finding in the rejections ledger, never in a gated document

When a premise does not hold and you reject the finding, write it to a ledger that sits **beside
the document the audit judged** — `<feature>.design.rejections.md` next to
`<feature>.design.md`, `<feature>.impl-plan.rejections.md` next to `<feature>.impl-plan.md`.
(Beside it, not in a per-phase directory: `plan` and `impl-plan` share `docs/01-plan/features/`,
so "the phase's directory" is ambiguous for exactly the two phases most often confused.) One entry
per rejection, naming the cycle, the surface, the claim, and the evidence that refuted it.
**Never pass that ledger as `--gated`.** It is a record *about* the audit, not a document the
audit judged.

The rejection does **not** go in the gated document's Version History, which is where it naturally
wants to go — the Version History is the session log, and a rejection feels like part of it. Two
measured reasons it must not:

- **It costs a second cycle.** The exit gate needs two consecutive both-clean cycles on
  *byte-identical* documents. Recording a rejection edits a gated file, so a rejection-only cycle
  changes the bytes and resets the streak: a fabricated finding costs two cycles, not one. Measured
  on HemaSuite `#18 gateway-consolidation` Phase 4 — streak-1 was reached at cycles 59, 65, 70, 73
  and 75 and lost every time, c73→c74 to a fabrication specifically.
- **It launders the fabrication into evidence.** Writing the rejected claim into the gated file
  makes the fabricated span *occur* in that file. Any later check that scores a finding's quoted
  evidence against the document it names then reads the fabrication back as legitimate. Measured
  2026-09-03 against the same corpus: a citation check that scores 1 of 6 against the prompts the
  reviewers actually read scores **0 of 6** against today's `design.md`, entirely because the
  rejections were recorded there. Full numbers:
  `docs/03-analysis/hmad-audit-evidence-gate.measurement.md`.

The same measurement is why there is **no** automatic evidence check in `h_mad_audit_gate.py`: no
span-occurrence rule separates a fabricated citation from a reviewer's *proposed* code, its
constructed test inputs, or a command it ran. Catching 4 of 6 fabrications costs 13 of 31 real
must-fixes. Rejection stays a human judgement; the ledger is where it is recorded.

## Teammate authors — one author, one document, fresh context every time

Phase documents are written by teammates, never in the orchestrator's own context: Phases 2, 3, 4 and 5a each dispatch a fresh-context author (`spec-author`, `plan-author`, `design-author`, `implplan-author`). **Read [references/teammate-authors.md](references/teammate-authors.md) in full before the first author dispatch of the run, and again before any re-dispatch after an audit** — it holds the dispatch shape, the DONE-line gate, the delta self-review and the rules that stay the orchestrator's.

A cross-reference `SKILL.md §"…"` to any of these now resolves in `references/teammate-authors.md`:

- §"Run the delta self-review as a SCRIPT before re-dispatching (#11/H4)"
- §"Tag every must-fix with its ORIGIN, at the moment it is verified (#11/H7)"
- §"Shared sentences are single-sourced, and adoption is checked BEFORE the commit (#11/H5)"
- §"Delta self-review — review the FIX before you re-dispatch the audit"
- §"The six rules that are the ORCHESTRATOR's, not the author's"
- §"Your own measurements — `references/measurement-discipline.md`"
- §"The measurement layer lives in probes, not in the phase document"
- §"Precheck before you dispatch — never spend a cycle on a greppable premise"
- §"Why the ack match is not fuzzy"
- §"Author dispatch rules the ORCHESTRATOR owns" (paragraph)

## Finding class — build vs measurement

Every Must-fix and Should-fix bullet a reviewer files carries a **class**, stated on a continuation
line under the bullet — the same shape as `quote:`, and like `quote:` never a `- ` bullet of its own:

```
- <issue> — <why>
  class: build | measurement
```

The operational test is one question, worded identically here, in `audit-prompt.template.md` and in
`agents/doc-auditor.md`: **would the code or tests a 5d/5e implementer writes differ if this finding were fixed?** Yes → `build` (an interface, a contract, a predicate, a
fixture, a test's assertion or its RED/GREEN count, a false premise about the platform an implementer
would code against). No → `measurement` (a published number, stamp, ledger row, sha series, pointer or
self-count about the tree that is stale or mis-derived — the tree is unchanged by fixing it).

**Why the class exists — measured, not chosen.** `doc-block-exec` ran eighteen gating rounds (design
c98 / plan c89 / impl-plan c49) under "exit only at must = should = 0, no cycle cap", and at r18 the
union still held 15 distinct musts, and applying the class test to the r18 verification ledger partitions them **9 measurement / 6 build** (the partition is written out in the r18 sheet's C8): a ledger row
that the gating report LANDING moves (88/88 → 89/89 by the orchestrator's own commit), an unstamped
trip-wire, "eight shas" over a ten-member list, a self-count of 4 that reads 5. Every one was a real
finding and not one of them changes a line an implementer writes; the round-over-round delta reviews
put 12 of 12 fix-introduced musts in the same layer. A document that publishes numbers about a tree it
moves is stale by construction, so a gate that scores that layer like a false timeout semantics cannot
converge — it measures itself. The build class is where the two model families kept finding DISJOINT
sets (r16, r17, r18), which is the class the loop exists for.

**Exit rule, both audit loops (Phase 3 auto-cycle and the 5b bullet):** build-class must = 0 on BOTH
surfaces at one commit; every remaining finding fixed or acknowledged. Measurement-class findings never
hold a phase past the round in which build-class reached 0 — they go to `## Acknowledged-not-fixed`
with their **re-run command** as the ack text, so the next reader can re-derive the figure instead of
trusting it. **The decision is made blind:** the orchestrator writes the classification rule into the
round's decision sheet BEFORE reading the round's verdicts, and may re-classify a reviewer's
`measurement` to `build` but never `build` to `measurement`.

**It fails closed** in every direction the reviewer can get wrong. `h_mad_audit_gate.py` counts an
untagged bullet as build, an unknown class value as build, and REFUSES the sidecar for a MUST-FIX bullet tagged
`class: build` or carrying an unknown value (a should-fix of any class stays deferrable, as it always was) (`ack_refused=N` on the `GATE-CLASS:` line — a build-class must is what 5d/5e would
implement wrongly, and no operator note clears that). Untagged bullets keep the pre-class ack
behaviour because every sidecar written before the tag existed is untagged. The verdict line
`GATE: PASS|FAIL must=N should=N` is unchanged; the breakdown is a second line,
`GATE-CLASS: build=N measurement=M untagged=K ack_refused=R`, over both blocking sections.

## Document-audit round cap — Phase 5 is the gate

**Every document audit loop (Phase 3 auto-cycle, Phase 4, 5b) is capped at TWO gating rounds per
document per revision line.** After the second round the phase EXITS whatever the verdict, on these
terms: every measurement-class finding goes to `## Acknowledged-not-fixed` with its re-run command;
every build-class must that is still open is written into the impl-plan as an explicit **open
decision on the Task it lands in** (`OPEN-DECISION: <finding> — resolve in 5d`), where a wrong choice is
a RED failure that costs minutes; the phase's exit is stamped at the commit carrying the sidecars and
5c/5d begin on that tree. **Phase 5 is the gate that matters**: RED/GREEN counts, the mutation
harness and 6a-prime run pytest against the tree, and a design-logic defect that survived the
documents shows up there as a failing test, not as a twentieth round.

**Why — measured, 2026-09-06.** `doc-block-exec` ran eighteen document rounds (design c98 / plan
c89 / impl-plan c49) with two surfaces per phase and no code written; r18 alone was six gating legs,
~90 minutes of agents, sixteen verified musts, nine of them measurement-class; r19 was three authors,
two reopens, three delta reviews and six legs again. The two model families found DISJOINT must sets
three rounds running, so the union never approached zero — each round found *new* defects in
documents of ~4,600 lines, not fewer. The operator called the cap on r19 and moved the feature to
Phase 5. A document loop with no cap is not rigour; it is the loop measuring itself.

**Enforced since 2026-09-07, having been prose until then.** A grep for cap logic over
`scripts/` returned nothing, which is why `#18 gateway-consolidation` reached **c105** with this cap
on the books — the same class as the two-consecutive-clean rule before #91. Check it before starting
another round:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py x --round-cap 2 <cycle stamps…>
```

Read the `ROUNDS:` token: `OK` / `OVER cap=N cycles=M`, exit 0 on a verdict and 2 only on a
cannot-judge (a stamp whose name is outside the audit grammar, since a stamp that cannot be placed
must never read as "under the cap"). Counted in **cycles per document** — legs of one cycle are
grouped out, and a plan cycle is not a design round. Not in "revision lines": those have no
mechanical definition, and a cap that cannot be computed is the prose it replaces.

**`cycles=N` is a FLOOR.** It counts cycles that were STAMPED, and a stamp exists only where
`--gated` was passed. Measured on the real doc-block-exec archive: 4 design and 9 plan cycles carry
stamps against the eighteen document rounds recorded above. The gap closes now that the cycle driver
passes `--gated` every cycle (§"Drive the gate through `h_mad_audit_cycle.py`"). Read it as "at
least N", never as evidence a loop was short.

**Why a cap is safe, measured.** Of 152 origin-tagged must-fixes on `#18` from c98–c105, only **10
(6.6%)** are `new-mechanism` — an actual design defect. 51 are fix-introduced, 27 are about
instruments the document publishes, 6 are stale records, 17 are propagation gaps. `design.md` grew
30 KB at c1 to 608 KB at c105, more than tripling in the last fourteen cycles. The late loop is not
finding design defects; it is correcting itself. A *yield*-based cap — stop when the last N cycles
produce no `new-mechanism` finding — is the better instrument and needs per-must origin tagging
(H7) first, which is still doctrine-only: of 1001 audit reports, 833 reviewer legs carry zero
`class:` lines.

Three rules that make the cap safe rather than a shortcut:

1. **Re-audit only what changed.** A document with no diff since the commit its last gate was
   scored at is not re-assembled — `git diff --quiet <last-gate-sha>..HEAD -- <document>` decides,
   and the gate stamp (`--gated`) is the record of which commit that was. A revision batch that
   touched the design and the impl-plan re-audits two documents, not three.
2. **The independent family gates; the same family reviews the diff.** On a revision cycle the codex
   leg is the gating pass and the `doc-auditor` runs §"Delta self-review" on the diff (ADVISORY) —
   not a second full pass. The delta layer is where the fix-introduced musts live (12 of 12 at r18)
   and a full same-family pass mostly re-reads what the author just wrote. Two full passes remain the
   rule for the FIRST gating cycle of a document (§"Never gate on one audit pass"), and for every
   cycle while codex is unavailable the teammate leg gates as before.
3. **The cap counts rounds, not cycles.** A round is one assembled prompt per changed document at
   one freeze; reopens inside a round and the delta review do not count. Two rounds means: batch →
   gate → batch → gate → exit.
4. **The cap forbids a third GATING ROUND, not a final corrective revision — and an
   `OPEN-DECISION` is only ever a DECISION.** This is the reading; the section said "the phase
   EXITS whatever the verdict" and did not say which of the two it meant, and the two prescribe
   opposite actions on the same finding.

   A corrective revision after the second gate is permitted and is **not** a third round, provided
   all three hold: it is **not re-audited** (no assembled prompt, no dispatch, no new gate stamp);
   it fixes **only findings the two rounds already filed** — a fix that discovers something new is
   a new finding for Phase 5, not a licence to keep editing; and every fix is **mechanically
   checkable**, so the delta self-review can confirm it rather than a reviewer re-reading prose.
   Run §"Delta self-review" over that revision — it is advisory and costs a quarter of a round.

   **What may become an `OPEN-DECISION`, and what may not.** The exit terms send an open
   build-class must to its impl-plan Task as `OPEN-DECISION: <finding> — resolve in 5d`, and the
   premise underneath that is explicit: *a wrong choice is a RED failure that costs minutes*. That
   premise requires a choice to exist. So:

   **Name an implementation that satisfies the criterion. If you cannot name one, it is not an
   open decision — it is a defect, and it is fixed by the corrective revision above.** A criterion
   no implementation can satisfy does not produce a decision 5d can settle; it produces a RED that
   no branch can clear, which arrives in Phase 5 as a blocked task rather than a minutes-long test
   failure. The whole argument for the cap is that Phase 5 is the *better* gate — that argument
   does not extend to handing Phase 5 something it provably cannot pass.

   Measured, and this is the case that forced the rule: `#18` Phase 5b cycle 2 filed a must where a
   revision had moved a mutation count 88 → 94 while Task 25's AC-7.5d still required **88** rows
   against a document enumerating **94**. Shipping that as an `OPEN-DECISION` would have been a
   misreading of the cap — there is no implementation of "94 rows" that satisfies "requires 88".
   (Re-probed 2026-09-07: the lane fixed it rather than deferring it, and at impl-plan v1.76 the AC
   requires 101 rows against exactly 101 enumerated ids. The rule is written from a case that was
   decided correctly by hand, not from a live failure.)

   The same shape as the vacuous-criterion rule in `invariants.base.md` §"Test discrimination":
   there, name the observation that differs between the implemented and unimplemented states; here,
   name the implementation that satisfies the criterion. Both fail closed on "I cannot name one".

The cap does not license skipping the class rule, the precheck, the delta review or the freeze; it
bounds how many times they run on one revision line.

## Never gate on one audit pass

**Agreement between two passes is not a stopping signal; it is one observation repeated.** Dispatch
**two** independent passes on the same assembled prompt and gate on the **union** of their must-fixes,
falsifying each against source before acting on it.

**`audit-cycle` runs one agent per pass, and you choose them.** `--surfaces agy,codex` names
the agent for each pass; the list length must equal `--passes`. The default is still every pass on
`agy`, because changing what an existing caller dispatches without being asked is worse than the
defect — but a same-surface run now **says so on stderr** instead of looking like two opinions
("one surface repeated, not a union"). Heed it: two passes of one surface re-confirm that
surface's blind spot, and on one feature the second leg was hollow in 21 of 22 passes while the
union reported as two.

When Codex is unavailable and `fallback_agent=grok`, use `--surfaces agy,grok`
for the independent audit legs (§"Teammate audit leg").

**Which two surfaces — routed by whether codex can run, and by whether this is the document's
first gate.** First gating cycle of a document, codex available: `codex` + `agy` + `grok` via
`--passes 3` and `--surfaces codex,agy,grok` (`docs/03-analysis/grok-audit-surface.measurement.md`;
or `codex` + `doc-auditor` full pass where agy is not dispatched — #77). If `command -v grok` fails, the first gate runs `--passes 2 --surfaces codex,agy`.
If the grok pass is the `pN` named in `UNVERIFIED reason=…:pN` on both the first run and its one
re-dispatch, the cycle is re-run as `--passes 2 --surfaces codex,agy`. Either way the stamp records the
legs that actually ran. A grok must-fix goes through §"Verifying a review finding before acting on it"
before it is acted on, and a rejected one is recorded per §"Record a rejected finding in the rejections
ledger, never in a gated document". Codex unavailable (§"Teammate audit
leg"): `grok` + `agy` when `fallback_agent=grok`; otherwise `doc-auditor` teammate + `agy`.
The stand-in holds codex's leg and **gates**.
**Revision cycles** (§"Document-audit round cap"): `codex` gates and the `doc-auditor` reviews the
DIFF (§"Delta self-review", advisory) — the delta review is the second surface, not a second full
pass. Never two full passes of one surface, and never the teammate full pass *plus* codex on the
same phase at the same cycle — in that case two reports share a model family, and the
union stops meaning what the rule below says it means.

Prefer two **different** surfaces. Measured across 15 cycles on one feature: a clean verdict was
falsified **four** times, and seven consecutive `agy`+`agy` cycles produced a false gate that a single
`codex` pass then broke. The surfaces catch different classes and alternate sides — which is the
whole reason the union, not the intersection, is the gate. Two passes of one surface mostly re-confirm
that surface's blind spot.

Two failure modes this replaces, both silent:

- **One pass, clean, shipped.** Nothing distinguishes "there is nothing to find" from "this surface
  cannot see it", and the artifact is a green you can quote and cannot defend.
- **Two passes, intersected.** Taking only findings both agree on discards exactly the findings that
  make a second surface worth paying for.

A pass's **thinking-token count predicts its reliability; its verdict does not.** A short clean report
has meant a truncated reply, so check the run before believing the token (§"Reading a dispatch
verdict", and the NDJSON genuineness check on duration and BEGIN/END sentinels).

## An agent's reported numbers are a claim, not a measurement

Never accept a dispatched agent's suite counts, `STATUS`, or its "unrelated / pre-existing"
diagnosis at face value. **Re-run it yourself with the pinned interpreter and re-derive the numbers.**

For a worktree executor, that re-run is one command: `python3 ~/.claude/skills/h-mad/scripts/h_mad_branch_evidence.py <worktree-or-branch> [--base main]`.
It reads the tip, commits and dirty state (deletions included), runs the changed and referencing tests, `h_mad_doc_consumers.py --run` for changed documents, `--check-anchors` and every spec over the changed code, one after another, and ends on `EVIDENCE-VERDICT: COMPLETE|INCOMPLETE reason=…|UNREADABLE reason=…`.
Read that token, not the executor's last message: a reply of "No change." once sat on a commit.

Measured repeatedly: Codex labelled a self-caused suite failure "unrelated pre-existing" when it was
caused by the feature's own docs; it reported a regression guard as `0/0` after misreading
`tests/test_references/` as `tests/references/`, so the guard never ran at all. Re-running took
twenty seconds in both cases and disproved the label.

**This includes the agent's refusals, and they are the ones worth taking seriously.** A
`STATUS: BLOCKED` refusing to make a test pass was once exactly right: the RED held a
self-contradiction that was invisible until the fix landed, because the unfixed code satisfied both
readings. A compliant agent would have shipped a guard pinning the defect. Verify a refusal the same
way you verify a success — by re-deriving it — and give it the benefit of the doubt for as long as
the evidence does.

Scope matters as much as the count: a per-task subset cannot see architectural guards
(forbidden-import checks, boundary censuses) because they live in files no feature subset touches.
**Scoped green is not suite green.**

## Re-measure a carried premise before working it

A backlog item, a filed finding, or a handover brief is a **claim about the world made by a session
that has stopped**. Reproduce its premise before implementing its prescription.

This is distinct from §"Verifying a review finding before acting on it", which is about a reviewer's
finding in front of you now; this is about an item that has been sitting. Measured: **four of five**
items swept in one session had false premises, and **three of four** in another — already shipped,
root-caused upstream of where they were filed, or with the prescription backwards. Re-running the
item's own reproduce command is the cheap half; do it first.

Two traps specific to carried items:

- **A carried number is stale by default.** Counts in this project have gone stale within days,
  repeatedly and in both directions. Re-run the census or the measurement rather than quoting it.
- **The measurement can be right and its method wrong.** Re-run the *measurement*, not just the
  claim — and measure through the production entry point rather than whichever helper is convenient
  to call, or the probe runs correctly on the wrong surface.

A premise that no longer holds is a finding in itself: record it as withdrawn with the evidence,
rather than quietly dropping the item.

## Reviewing a skill with agy

A skill is not a feature: there is no impl-plan task and no Codex report, so neither
`agy-spec-reviewer-prompt.md` nor `agy-architectural-reviewer-prompt.md` fits. Use
`references/agy-skill-reviewer-prompt.md` — fill its `INLINE_*` slots and dispatch headless:

```bash
hmad-dispatch exec agy <prompt-file> --cd <repo> --out <report.md> --log <run.log> --timeout 900 &
dispatch_pid=$!
hmad-dispatch progress <run.log> --pid $dispatch_pid   # bounded, returns immediately; poll, do NOT `tail -f`
wait $dispatch_pid
```

`exec` is pane-independent — it needs only the `agy` CLI on PATH, so a `PREFLIGHT: FAIL` from a
stale pin does **not** block it. Check `command -v agy` rather than re-pinning.

Three rules carry the value; the template states them, and skipping any one is how a review turns
into damage:

- **Ground truth is the binary, not its documentation.** When the skill wraps a CLI, run
  `<cmd> --help` before reporting a flag as missing or unsupported. One review returned four
  separate "undocumented flag" findings and every one was a real flag the vendor guide omitted;
  acting on them would have deleted working code. **Say so in the prompt** — a prompt that names a
  guide as ground truth *causes* this class of false finding.
- **Classify `[OURS]` / `[UPSTREAM]` / `[USAGE]` first.** A vendor skill pinned in
  `~/.agents/.skill-lock.json` cannot be patched locally — edits are clobbered on sync — so an
  `[UPSTREAM]` finding is information, not work. Spend the effort on `[OURS]`.
- **Verify every finding against the file before acting** (§"Verifying a review finding before
  acting on it"). Across four skill reviews this has killed 8 findings that did not survive
  checking, several of them confidently argued.

Then fix under the ordinary discipline: TDD the doc-test, mutation-verify the guard, run both
coupled suites (§"Editing this skill while a run is in flight" — the symlink couples repos).

Reviewing a skill you *depend on* is worth doing even when you cannot patch it: two `[OURS]`
defects in our own integration were found by reviewing `orca-cli`, both in a code path no test
had ever exercised.

## Orchestrator context hygiene (your own window)

The section below clears the *agents'* panes. This one is about **your** window — the
orchestrator's — which is the one that actually ends a run when it fills. An H-MAD feature is a
long session by construction (7 phases, N audit cycles, a live e2e), so the orchestrator's window
is a consumable resource that has to be budgeted, not a background fact.

### `advisor()` costs a second full copy of the session

`advisor()` takes **no parameters**: the payload is the entire transcript, forwarded to
`claude-fable-5` and billed into the **same turn's** input. There is no way to send it less — the
only two levers are how big the transcript is and whether you call it at all. Measured on session
`97490faf` (2026-08-19), three calls, one ratio:

| baseline | advisor turn | ratio |
|---|---|---|
| 245,617 | 499,633 | 2.03× |
| 302,589 | 606,450 | 2.00× |
| 525,742 | **1,056,891** | 2.01× |

The third call blew a 1M window from ~50% used. **At 50% used, one advisor call = 100%.** The
spike is transient, not cumulative — the next turn drops back onto the normal growth curve — but a
run that overflows mid-phase is over, and the overflow is not recoverable by compacting afterwards.

The trap is that nothing at the call site prices it. The visible return is ~4KB of advice, and the
cost scales with session age, so the identical call that was free in Phase 1 is fatal in Phase 6 —
which is exactly where the tool's own "call before declaring done" guidance points. Session start
is not free either: an H-MAD session opens at **~86k tokens before any work** (this skill plus
`handoff`, the CLAUDE.md chain, the memory index, hook injections). Count it.

### Hard ceiling: never call `advisor()` above ~45% window used

At the measured 2.0×, anything above 50% cannot fit; 45% is the margin, because the number you can
measure is a floor (see below). Measure it, don't estimate it — the `<total_tokens>` reminder is
budget *remaining*, not window *used*, and answers a different question:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py
# CTXBUDGET: OK   used=98353 window=1000000 pct=9.8 projected=196706 ceiling=45
# CTXBUDGET: DENY used=525742 window=1000000 pct=52.6 projected=1051484 ceiling=45
```

Read the `CTXBUDGET:` token, never `$?` — like every other H-MAD gate it exits 0 on a verdict, and
exits 2 only on `UNKNOWN` (a cannot-judge: no transcript, or no usage record yet), which carries
**no `used=`** precisely so it cannot be mistaken for an `OK`. `--window` (or
`HMAD_CONTEXT_WINDOW`) sets the model's window; the default is 1M.

It finds **your** session's transcript by `CLAUDE_CODE_SESSION_ID`, so it works from any cwd — a subdirectory, a linked worktree, anywhere. Two path-derived shortcuts it deliberately does not lead with: the project-dir slug is the *session's* root, not the process's cwd (run from `<repo>/h-mad` it names a directory that does not exist and the tool is `UNKNOWN` forever — safe, and useless, which is how a check stops being run), and newest-mtime picks the most recently written session in the project, which with two Claude sessions open on one repo is not necessarily yours — and a fresh sibling reads small, so that one fails toward a false `OK`. Override with `--transcript` when you need a specific file.

`used=` is the last recorded assistant turn's `input + cache_creation + cache_read`, so it **lags
the current turn** — tool results already in flight are not in it. It is a floor, which is why the
ceiling is 45 and not 50.

### Which advisory channel — routed by what the advice must SEE

`advisor()` is not the default advisory channel for an H-MAD run; **agy is**. Route by the
question's required input, not by how hard the question feels — "hard vs easy" is unjudgeable in
the moment and collapses under pressure, while "what does this advice have to read?" is a fact
about the question:

| the advice needs | channel | why |
|---|---|---|
| **artifacts** — design, spec, plan, diff, code, state | `hmad-dispatch exec agy` | it reads them itself, in its own context; only its report (~2k) returns |
| **this session's trajectory** — what was tried, what is assumed, where reasoning bent | `Agent(subagent_type: "fork")` | inherits the transcript at ~zero cost to your window, but runs on **your** model |
| **both** the trajectory *and* a stronger reviewer | `advisor()` | the only thing that supplies both — and the only one that costs a second copy of the session |

Everything H-MAD produces at a gate is an artifact, which is why agy is the reflex and `advisor()`
the exception. The rule to hold: **`advisor()` is for the hardest calls only** — reserve it, and
never spend it on a question agy could answer by reading the repo.

1. **`hmad-dispatch exec agy <promptfile>` — the default.** Reflex in Phases 1–4 (brainstorm,
   spec, plan, design) and at 6/6a-prime, where the work *is* static and a fresh independent
   reviewer is exactly what is wanted. It is an independent model, so the stronger-second-opinion
   property survives; it gets *fresh* context, so hand it durables. See
   `references/agy-architectural-reviewer-prompt.md` and the 6a-prime flow.
2. **`Agent(subagent_type: "fork")`** when the question is about the conversation and model
   strength is not the point — "did I miss something in what I just did", not "is this design
   right".
3. **`advisor()`, below the ceiling.** Cheapest in Phases 1–3, and its own docs say that is also
   where it adds the most value: before an approach crystallises. Budget one call there. The late
   "before declaring done" call is the optional one — it is the expensive one, and by Phase 6 the
   artifacts exist to review instead.
4. **`/compact` first, then `advisor()`** — last resort, and only when you specifically need the
   full-history view at a high baseline. Compacting is lossy, and late-session review is valuable
   *because* of the accumulated detail, so this degrades exactly what you are paying for.
   Compacting **after** the overflow recovers nothing.

**What defaulting to agy costs you: trajectory awareness.** agy runs fresh and has zero knowledge
of the dead ends you just explored, so a bare "what should I do here?" gets back, confidently, the
naive fix you rolled back five minutes ago. When you consult it while *stuck*, the prompt must
carry your failed attempts explicitly — what you tried, what the output was, why you reverted —
or you are paying for a review of a problem it cannot see. That is also the boundary: **5d/5e
(the RED/GREEN loop) and 6b (iterate) are where agy is the wrong tool**, because there the
trajectory is the whole of the evidence.

### Making it mechanical — the advisor budget advisory

A rule that only lives in prose is one the orchestrator talks itself out of, and it is most
tempting to do so at exactly the point where being wrong ends the run. `hooks/h-mad-advisor-warn.sh`
puts the ceiling in front of the model while it is deciding. Wire it under **`PostToolUse`**:

```json
{ "matcher": "*", "hooks": [{ "type": "command",
  "command": "bash $HOME/.claude/skills/h-mad/hooks/h-mad-advisor-warn.sh" }] }

```

**It is an advisory, not a gate, and that is structural — do not "fix" it back into a gate.**
`advisor` is a `server_tool_use` executed server-side; it never enters local tool dispatch, so **no
tool-scoped hook event fires for it** — not `PreToolUse`, not `PermissionRequest`, not
`PostToolUse`. Its predecessor was registered `{"matcher": "advisor"}` on `PreToolUse` and, on two
instrumented probes with the marker at line 1, never ran once while looking installed (J44). No
matcher string fixes that. Confirmed twice: the 2.1.241 binary calls it "the server-side advisor
tool", and a live transcript records three real `advisor()` calls as `server_tool_use` beside 101
ordinary `tool_use` blocks. What *is* attachable is the turn before the call — `PostToolUse` fires
at the rate risk accrues, and the verdict arrives as `additionalContext` during the orientation
window. `h_mad_hook_wiring.py` reports `HOOK_NOT_WIRED` for an advisory under `PreToolUse`.

It rides the `~/.claude/skills/h-mad` symlink on purpose (a second hook symlink would add a
`SPLIT_INSTALL` failure mode for no gain). **Verify it fires; do not assume either way.** The long-standing guidance here was that hooks are
snapshotted at session start and wiring takes effect in the NEXT session. That was **measured false
on 2.1.241**: this registration was added mid-session and the harness invoked it ~13 minutes later
in the *same* session, with a real payload — the throttle stamp carried the live `session_id` and
the budget read the live transcript. Assume nothing; run the check now, and if it stays quiet,
relaunch and run it again:

```bash
HMAD_CONTEXT_WINDOW=1000 claude    # then run ANY tool — the budget line MUST appear
```

If no line appears the hook never fired, and **that is the finding**: an advisory that stands down
silently is indistinguishable from one reporting all-clear, which is how J44 survived for days.
Note the check no longer needs an `advisor()` call — any tool call exercises the same path.

The advisory **stays silent** on every cannot-judge: no transcript, no usage record yet, no budget
script, an unparseable payload, or any verdict that is not `DENY`. A warning fired when it cannot
measure trains the reader to ignore the one that matters. (Hence `set -uo pipefail`, not `set -euo`:
the budget script exits 2 on `UNKNOWN`.) It matches `CTXBUDGET: DENY` and nothing else, so
`--mode run`'s `HALT` cannot read as an over-budget advisor call. There is **no override env var** —
an advisory has nothing to escape, and an escape hatch would tell the reader it blocks. It throttles
to one emission per `HMAD_ADVISOR_WARN_INTERVAL` seconds (default 60): not for cost, which is
~60 ms, but because a warning reprinted on every tool call is the context bloat it exists to prevent.

Two limits worth stating: it protects only sessions where it is wired (elsewhere the rule is
documentation), and `HMAD_CONTEXT_WINDOW` defaults to 1M — a smaller-window model needs it
exported or the percentage is wrong in the permissive direction. The deny prints the window it
assumed for that reason.

**Never batch `advisor()` into a heavy turn.** Its input is snapshotted at call time, so the 40
files you read in the same turn are inside the copy. Call it, then do the reading.

## Helper work — narrow agents, never `general-purpose`

Work the orchestrator hands off that is neither a phase document, an audit nor a review goes to
one of two narrow agents, never `general-purpose`. A default session starts each turn at ~53k
context and these at ~20k (measured 2026-11-02, row 2932), and the narrow tool grant is also
what keeps a helper inside its task.

- **One bounded change** — implement a named task, fix one verified finding, apply a mechanical
  edit — goes to `task-executor` (Sonnet; Read/Grep/Glob/Bash/Edit/Write). Hand it `TASK`,
  `FILES` (the only paths it may edit), `VERIFY`, `REPORT` and `PROJECT_ROOT`:

  ```
  Agent(subagent_type: "task-executor", prompt:
    "TASK: <what, and what done means>\nFILES: <paths>\nVERIFY: <command>\nREPORT: <path>\nPROJECT_ROOT: <root>")
  ```

- **Labelling a batch** — classify findings, triage rows, sort failures by cause — goes to
  `task-labeller` (Haiku; read-only plus its report). Hand it `ITEMS`, the closed `LABELS` set
  with a definition each, `REPORT` and `PROJECT_ROOT`:

  ```
  Agent(subagent_type: "task-labeller", prompt:
    "ITEMS: <file or list>\nLABELS: <label — definition, one per line>\nREPORT: <path>\nPROJECT_ROOT: <root>")
  ```

Both answer with a `DONE` line carrying the report's `sha256=`; gate it through
`h_mad_done_gate.py` before reading the report, exactly as for an author. Phase 5 implementation
still goes to codex through `hmad-dispatch exec` (§"Phase 5 sub-steps"); `task-executor` is for
the orchestrator's own side work, not a substitute for the TDD loop. The only `general-purpose`
dispatch this skill prescribes is the same-session bootstrap fallback above.

The judges never get the cheap tier: `doc-auditor`, `change-reviewer` and the spec/plan/design
authors pin Opus, and no prescribed dispatch of them may pass a lower `model:`
(`test_h_mad_judge_model_floor.py`). One override is outside the repository's reach:
`CLAUDE_CODE_SUBAGENT_MODEL` in the environment replaces every subagent's model, judges
included. Leave it unset for an h-mad run.

## `hooks/memory-index-guard.sh` — the auto-memory cap, surfaced without being asked

`h_mad_check_memory_index.py` was correct from the day it shipped and ran only when somebody READ
the step documenting it in `handoff/references/auto-memories.md`. The index then sat at 100% of its
cap for a day with two entries already invisible, and nothing said so — a documented rule is not an
enforced one. Wired at **two** events, because the loss and its cause happen at different moments:

```json
"SessionStart": [{ "hooks": [{ "type": "command",
  "command": "bash $HOME/.claude/hooks/memory-index-guard.sh --session-start" }] }],
"PreToolUse":   [{ "matcher": "Write|Edit", "hooks": [{ "type": "command",
  "command": "bash $HOME/.claude/hooks/memory-index-guard.sh" }] }]
```

`SessionStart` is the moment the loss actually occurs — the cap is enforced at LOAD, so an index
already over is being truncated for every session and that is the only point at which the fact is
observable. `PreToolUse` is the CAUSE, filtered to `*/memory/MEMORY.md`: a topic file is uncapped and
firing on one would be noise on the commonest memory write there is, which is how a hook gets
disabled. **ADVISORY, exit 0 on every path** — a block would have to be right about someone's memory
write and being wrong costs a refused write they cannot complete, while being wrong the other way
costs a line of text; both events place stdout into the session, so it is read rather than logged. It
says NOTHING on a healthy index (every session start pays for that line), reports `UNREADABLE` as its
own outcome rather than as clean, and surfaces an unrecognised verdict instead of swallowing it — a
renamed token is how a guard goes quiet while still appearing to run. ~0.04s. Calibrated in
`h-mad/tests/test_memory_index_guard.py` against real over-cap indexes through the real checker, both
dimensions controlled: a fixture built only to a byte target produced 479 lines against the 200-line
cap and was correctly called OVER while the test was asking for WARN.

**The wiring lives OUTSIDE this repo, in two places, and neither is versioned here** — so a clone of
this repo has the hook's CODE and none of its INSTALLATION, and the only record of what was changed
was a backup in a session scratchpad that does not survive cleanup. Both places:

1. `$HOME/.claude/settings.json` — the two `hooks` entries above.
2. `$HOME/.claude/hooks/memory-index-guard.sh` — a symlink to `h-mad/hooks/memory-index-guard.sh`
   in this repo. The `command` strings name that path, not the repo one, so the symlink is
   load-bearing and a moved checkout silently stops the hook (it reports `a missing checker` and
   exits 0, by design).

**Find them by VALUE, never by index.** They sat at `SessionStart[4]` and `PreToolUse[4]` when wired
on 2026-09-14, and any later edit to that file renumbers both:

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude/settings.json"
for event, groups in json.load(p.open()).get("hooks", {}).items():
    for gi, g in enumerate(groups):
        for hi, h in enumerate(g.get("hooks", [])):
            if "memory-index-guard" in h.get("command", ""):
                print(f'{event}[{gi}].hooks[{hi}]  matcher={g.get("matcher")!r}')
PY
ls -l "$HOME/.claude/hooks/memory-index-guard.sh"
```

**To unwire**: delete every entry that locator prints, then `rm` the symlink. **To wire on a fresh
machine**: recreate the symlink, then add the two entries exactly as shown above. Nothing else
depends on either — `h_mad_check_memory_index.py` remains runnable by hand, which is all it was
before the hook existed.

## Run-context ceiling — halt the run at 80%

The ceiling in the section above protects one *call*. This one protects the *run*. They are
separate sections because they are separate subjects: that one is about the cost of an advisory
channel, this one is about whether the session survives to finish the feature.

| ceiling | asks | why that number | remedy |
|---|---|---|---|
| 45% — `--mode advisor` (default) | can I afford one `advisor()` call | advisor forwards a second full copy (2.0x measured); 45 is the margin under 50 | pick a cheaper advisory channel |
| 80% — `--mode run` | is this session about to die mid-phase | leaves room for the phase in flight **plus** the handoff that ends it | halt and hand off |

**Why halt rather than warn.** An H-MAD run is long by construction — 7 phases, N audit cycles, a
live e2e — so the window is a consumable it will exhaust on any large feature. Overflowing
mid-phase is **unrecoverable**: the run is over, and `/compact` afterwards recovers nothing, because
what it would have compacted is already gone. A cap is therefore only worth having if it stops the
run while stopping is still cheap. At 80% there is room to write state, commit, and leave a
resumable handoff. At 100% there is not, and the whole session's work is what is lost.

Check it **at every phase boundary**, and before any dispatch that will return a large payload:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py --mode run
# CTXBUDGET: OK   mode=run used=400296 window=1000000 pct=40.0 ceiling=80
# CTXBUDGET: HALT mode=run used=810000 window=1000000 pct=81.0 ceiling=80
```

Read the **token**, never `$?` — as with every other gate here it exits 0 on a verdict, and 2 only
on `UNKNOWN`, which carries no `used=` precisely so a cannot-judge cannot be read as an `OK`.

**On `CTXBUDGET: HALT mode=run`, halt `<phase>:context_ceiling`** and follow the ordinary halt
protocol, with the one addition that is the entire point of this route: **invoke the `handoff` skill
in WRITE mode before you stop** — `Skill(skill: "handoff")`, or `/handoff` — so the next session
resumes instead of re-deriving. Then release the claim
(`h_mad_state_write.py --feature <feature> --release --session-id <your-session-id>`; a live claim refuses to release anonymously, J45), or the resuming session inherits a lock from
a session that has stopped. A halt that leaves no handoff has spent the ceiling and bought nothing.

**Invoke the skill; do not hand-write a doc that looks like one.** The two are not
interchangeable, and the difference is invisible at the moment of writing and fatal at the moment of
resuming. The skill's WRITE mode resolves the **canonical main-worktree store** and names the file
`YYYY-MM-DD-<branch-slug>__<slug>.md`; its READ mode locates a handoff by exactly that store and
that slug. A doc written by hand into the current linked worktree, or named freely, is not *slightly*
harder to find — it is **invisible to the resume**, which is the entire thing the ceiling was spent
to buy. WRITE also does four things a hand-written doc omits, each of which the next session depends
on: the central `~/.claude/handoffs/INDEX.md` entry (the only cross-project view), durable learnings,
the **auto-memory store** (`docs/learnings.md` is not loaded next session; the memory index is), and
a commit routed through `handoff_commit.py`, which guarantees the doc is reachable from a ref instead
of sitting untracked — three handoffs were orphaned exactly that way on 2026-08-29.

**Budgeting the write itself.** You are at 80% by construction, so WRITE's own phases cost context
too. They are not equally load-bearing: the doc, the index entry, and the commit are **not
discretionary** — without them the halt bought nothing. The two escape hatches, in the order to reach
for them, are `--skip-scout` (it reconciles a long candidates backlog and is the most context-hungry
phase) and then `--skip-memories`. Prefer skipping the scout: memories are what actually surface in
the next session, so skipping them last is the cheaper loss. If the halted work belongs to a
different repo or worktree, that is the skill's HANDOVER mode, not WRITE — it releases the claim as
part of the transfer, so do not also release it here.

**The hook suggests it, too — it does not oblige.** `hooks/h-mad-advisor-warn.sh` (PostToolUse,
every session, not only `/h-mad` runs) also reads `--mode run`. Past 80% it injects a suggestion,
not a halt: finish the task in hand, avoid starting a new large one, then `/handoff` (WRITE). From
90% the suggestion is the lean close-out: finish only the step in hand, then
`/handoff --skip-scout --skip-memories`. It speaks once on entering a band and then every
`HMAD_RUN_SUGGEST_INTERVAL` seconds (default 600). Escalating to 90% speaks at once, and it keeps
its own stamp, so the 45% advisor note never silences it. The thresholds are `HMAD_RUN_SUGGEST_AT`
(80) and `HMAD_RUN_URGENT_AT` (90). Suggestive by operator decision (2026-10-15): a phase
boundary is still where an orchestrator should check and act. The hook only makes sure the number
is SEEN, which it never was outside an h-mad run. A hook cannot invoke a skill; the model still
runs `/handoff`.

**`HALT` is not `DENY`, deliberately.** The advisor half of `hooks/h-mad-advisor-warn.sh` speaks on
the glob `*"CTXBUDGET: DENY"*`, and its run half speaks on `HALT`, with different words. Had a run-ceiling breach reused that word, no existing consumer could tell an
advisor refusal from a dying run — and they prescribe opposite actions (choose a cheaper channel
versus stop the run entirely). `--mode run` omits the `projected=` field for the same reason: it is
`used * 2` because advisor forwards a copy, a run cap forwards nothing, and printing it would invite
reading the run ceiling as an advisor projection.

**The number is a floor**, as in advisor mode: the last recorded usage predates the current turn's
own growth. That slack runs in the safe direction — it halts slightly early rather than slightly
late, and slightly late is fatal.

## Agent-pane context hygiene

The codex and agy agents are **long-lived REPLs reused across every audit cycle, feature, and session**. Their conversation context accumulates: a plan-audit thread bleeds into the next design audit, one feature's TDD bleeds into the next feature's, and stale scrollback pollutes the `hmad-dispatch read` output you later grep for a verdict. Clear the context at the boundaries below so each fresh pass starts clean.

**When to clear (fresh pass) vs keep warm (continuation):**
- **Clear** at: the first cycle of each audit phase (Phase 3/4/5b cycle 1); 5d and the first 5e dispatch of a feature; 6a-prime; and whenever you confirm a pane is alive at the *start* of a new feature.
- **Keep warm** at: cycles 2..N of the *same* audit (the running revision thread — "here's the fix for your prior should-fix" — is exactly the context you want); a Codex GREEN retry within the same module.

**How to clear (per pane), then verify it took:**
```bash
# agy (Antigravity CLI) and codex both accept /clear:
hmad-dispatch clear codex
hmad-dispatch clear agy
# verify a clean prompt (no leftover input, not mid-run):
# --from-start, NOT a tail: a tail can render an overdrawn region of the frame
# and show a stale boot screen for a pane that is actually at a ready prompt
# (J3). Readiness drives a relaunch decision, so it must not be read from a
# slice of one frame.
hmad-dispatch read <agent> --from-start | tail -20
```
If `/clear` is not honored or the pane is wedged (input box still shows queued text, or a 400/desync on agy), **restart the surface** instead: re-seed via the launch command (`agy --dangerously-skip-permissions` / the Codex CLI) per `AGENTS.md`, then re-confirm alive with `hmad-dispatch alive <agent>`. A restart is the hard reset; `/clear` is the cheap one. Never dispatch an audit/TDD prompt into a pane whose scrollback still shows the previous cycle's report — you will grep the wrong verdict.

**Cost note:** clearing is cheap and prevents two failure modes seen in practice — (a) an audit verdict influenced by an unrelated prior feature's discussion, and (b) `hmad-dispatch read` returning a stale prior-cycle report that the gate then parses as this cycle's result.

### Orchestration mode (Orca)

When `hmad-dispatch env` reports `orchestration: on` (Orca plus an `HMAD_ORCA_COORDINATOR_TERMINAL` pin), dispatch, verdict collection, and decision gates SHOULD use the structured orchestration verbs rather than screen scraping. The `send` / `read` / `wait` scrape flow remains the universal fallback for cmux or an unpinned coordinator. See `references/orchestration-mode.md`.

### Scheduling HemaSuite live-e2e as Orca automations (Orca only)

HemaSuite wiring is documented usage only: no HemaSuite code is changed by these lifecycle wrappers, and HemaSuite must execute in an Orca workspace. To schedule a nightly live-e2e, stage the prompt in a file and create the automation:

```bash
hmad-dispatch automation-create --name anemia-e2e --trigger cron --prompt-file <prompt-file> \
  --provider claude --precheck "hpw doctor" --repo HemaSuite
```

`--provider` must be a provider Orca recognizes — verified live-valid values are `claude`, `codex`, `gemini` (NOT `agent`; Orca rejects unknown providers with `invalid_argument`). Target the run with `--repo <name>` (or `--workspace`/`--project`). Note `--trigger` (`preset|cron|rrule`) and `--schedule` are mutually exclusive; a preset such as `daily` needs no `--schedule`.

Run one ad hoc with `hmad-dispatch automation-run <id>`, enumerate configured jobs with `hmad-dispatch automation-list`, and clean up with `hmad-dispatch automation-remove <id>`. The `<id>` is the automation id returned by `automation-create` (extracted from `.result.automation.id`), NOT the response envelope id.

## Halt protocol

See `references/failure-recovery.md` for per-phase routes + recovery hints.

1. Write `orchestrator_state[<feature>]`: `halt_reason = "<phase>:<sub-step>:<description>"`, `halt_ts = <now>`, `phase = null`. Pin `current_phase` + `last_completed_phase`.
2. Emit `[H-MAD] <feature> phase<N> halted reason=<reason>`.
3. `hmad-dispatch notify "/h-mad halted" "<reason>"`.
4. Print recovery hints.
5. Exit.

## What you NEVER do

- Never skip the gate (`h_mad_audit_gate.py`) after an audit.
- **Run the project suite with the gate in Phases 3, 4 and 5b, and read `SUITE:` as its own line (#91).** `python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py <report> --gated <doc> --project-tests <project-test-root> [--suite-cmd "<cmd>"]`. Measured on HemaSuite `#18 gateway-consolidation`: a dual-surface design audit ran **95 cycles** without meeting its exit gate while a repo test enforcing the **audit loop's own invariant** stayed red for the entire life of the feature — `tests/test_audit_phase_inline_summary_sync.py::test_real_features_synced`, whose guard is that every earlier cycle recording a FAIL must be cited in the Version History. It went green for the first time after 91+ cycles. The gate could not have caught it: before this it held **zero** occurrences of `subprocess|pytest|check_call|os.system`, and `pytest` appeared in this file only at 5e and 5f. **The root must be SCOPED** — an unscoped pytest from a repository root collects sibling-project import mismatches (step 5f says so, and HemaSuite carries two suites under a monorepo root). The verdict is scored on pytest's own **summary line, never on `$?`**: a skipped selection and a killed run both exit 0, and `SUITE: UNREADABLE reason=no_summary` is a cannot-judge that is neither a pass nor a failure.
- **A red suite blocks the EXIT, not the cycle.** The per-cycle `GATE:` verdict is untouched — blocking every cycle would make an audit hostage to an unrelated flaky test, and `docs/skill-candidates.md` §`concurrent-suite-runs-manufacture-phantom-failures` records two pytest runs over one working tree producing 6 and 3 failures in *different* sets, and 0 when the file ran alone. The refusal lives at the streak instead: the stamp records `"suite"`, and `--exit-check <stamp>…` prints `EXIT: READY|BLOCKED reason=<r>`, where a cycle whose suite was red **or unmeasured** cannot contribute. `suite: null` is what a cycle run without `--project-tests` records, and it is refused for the same reason silence is never a pass. This is enforced in the gate rather than written here as a step because **nothing counts the streak** — `grep -in 'streak|consecutive'` over `scripts/` returns nothing, so the two-consecutive-both-clean rule existed only as prose, and an instruction an orchestrator can skip is exactly what 91 cycles demonstrated.
- **One measured run per working tree, and a report when the tree moved under it.** The concurrent-suite hazard above is no longer prose: every pytest session under this repository's rootdir takes the same per-toplevel tree lock as the mutation harness. The repository's root conftest registers the lock, so bare `pytest`, `pytest handoff/tests`, one `handoff/scripts` file and `pytest .` all take it, and `h-mad/tests/conftest.py` registers it for install-path runs. As a result, a second session over one tree prints `SUITE: BUSY holder=<pid> age=<s> what=<pytest-session|spec path> lock=<file>` and exits 75 before collecting anything. This gate reads that as `SUITE: UNREADABLE reason=suite_busy`, naming the holder on the next line, and the wire registry reads it as UNREADABLE. Neither reads it as a failure. **The lock also blocks governed writes.** While a suite holds the tree, the TDD gate's judge is refused too, so every governed Edit or Write is denied as `no-summary` with the `SUITE: BUSY` line in its reason until the suite ends. Start a background suite only when no governed edit is planned before it finishes. A tree whose lock cannot be written (a read-only checkout) prints `SUITE: LOCK_UNAVAILABLE` and runs unlocked rather than erroring. A harness started under a suite prints `MUTATION: BUSY … spec=pytest-session`, and a suite started under a harness is refused the same way. The harness's own inner pytest runs are exempt through the holder token it exports (`H_MAD_TREE_LOCK_HELD`); separate worktrees are separate toplevels and never contend on the lock. Tests that share fixed `/tmp` paths can still collide across worktrees. At session end the suite also compares a digest of the non-ignored tree with the one taken at start and prints `SUITE: TREE_MOVED paths=… n=K` when they differ, so a pass count measured over bytes that changed says so. The gate and the cycle driver carry it onto their `SUITE:` line as `tree_moved=<paths>`. Before the suite starts both print `SUITE-HOLD: … tree=<git toplevel>`: hold your own writes to that tree, handoff commits and reports included, until the `SUITE:` line prints. It reports and never blocks an edit, it is quiet on ignored writes, and it cannot see an edit reverted before the run ends. The harness's own `TREE_MOVED` compares the same digest, not only HEAD. To tell a failure the change caused from one the base already has, use `h_mad_failure_diff.py run --base <ref> [--repeat N] -- <selection>` rather than a hand-built clean worktree: it runs the same selection in a throwaway detached worktree at the base, diffs the failure sets by node id, and reports a test that fails in only some runs as FLAKY (script inventory below).
- **Name the reviewer legs with `--legs`, and read `GATE-LEGS:` as its own line (#11/H3).** `… --gated <doc> --legs codex --legs agy`. A clean streak counts only over an **unchanged leg set**: `--exit-check` blocks with `reason=legs_changed:<a>|<b>` when the two cycles ran different legs, because a streak over two different leg sets measures two different questions. Measured on HemaSuite `#18 gateway-consolidation` (`gateway-consolidation.audit-ledger.md`): Σmust tracked the **leg count**, not document quality — the 13 design cycles ending at **c99** ran `3 3 7 5 3 5 4 3 8 4 7 12 6` and every rise coincided with a leg added or returning (teammate c87, doc-auditor+crossdoc c92, codex c97). Re-derive the series from the ledger rather than reading that window as current; it has grown since. The exit streak was reset by new legs **four times** and never once approached by the documents — zero at c99 when this was measured, and still zero at c104. Changing the set is legitimate — it just starts a **new baseline**, which falls out with no extra flag, since two fresh cycles under the new set agree with each other. The first gate and the revisions run different leg sets by design, so the streak, when it is reached, is among revision cycles.
- **Drive the gate through `h_mad_audit_cycle.py` and pass the flags THERE — the driver feeds every leg.** `--project-tests <root> [--suite-cmd "<cmd>"] [--suite-timeout <s>] --gated <doc> [--legs <name> …]` on the *cycle driver*, not on each gate call. `--suite-timeout` bounds that one suite run in whole positive seconds, default 3600: a suite that runs longer reads `SUITE: UNREADABLE reason=timeout_after_<s>s` on every cycle and can never close an exit streak, so raise it for a long suite (measured: HemaSuite's HPW suite runs past an hour). It is refused without `--project-tests`, because a bound on a suite that will not run is a flag silently dropped. `<cmd>` is parsed with POSIX shell quoting (`shlex`, not a shell): `-k "a or b"` stays one argument, so an apostrophe must be quoted and a backslash is an escape. The suite runs **once per cycle** and its verdict is forwarded to every per-leg gate invocation as `--suite-result`; running it inside the gate would be minutes per leg and is the design `audit_suite_gate.json` rejects outright. The leg set is forwarded identically to every leg, so the legs of one cycle cannot disagree about what that cycle ran. Before this, `gate()` built its command with the collected report and `--ack-file` and nothing else, so **every cycle driven through the script recorded `suite: null` with no leg set** and its exit gate was refused `suite_unmeasured` — both gates shipped, correct, and unreachable from the path that actually runs. `--suite-result` and `--project-tests` are mutually exclusive on the gate: one field, one source. **`GATE_RE` now tolerates trailing fields** on line 1, because `--gated` appends ` gated=N` there; the gate's own comment had recorded that collision as latent "because the cycle driver never passes `--gated`", and wiring this made it live — the first gated run died with `ERROR: missing GATE token` against a gate that had answered `GATE: PASS must=0 should=0 gated=1`.
- **A streak is two CYCLES, not two stamps — `--exit-check` groups by cycle.** A cycle emits one stamp **per leg**, so counting stamps counts legs. Measured 2026-09-07 over the real archive: of 17 cycles carrying stamps, **8 have two**, and same-cycle legs sort *adjacently*, so a glob hands the gate two legs of one cycle. Executed against the then-shipped gate, the real pair `doc-block-exec.design.audit.v20.codex` + `…v20.p1` returned `EXIT: READY` — a two-consecutive-clean-cycle streak certified from **one cycle**. H3 made it read worse rather than catching it: both legs carry the same declared leg set, so the leg check passed and lent false confidence. The cycle is derived from the stamp's name (`<feature>.<phase>.audit.v<N>.<leg>.md.gated.json`), ordered **numerically** (`v10` sorts before `v9` as text), **every** leg of a counted cycle must be clean with a green suite, and the legs of one cycle must agree about what that cycle ran (`legs_disagree:<phase>.v<N>`). A stamp whose name is outside that grammar is `EXIT: UNREADABLE reason=stamp_name:<name>` — a cannot-judge, never a pass, because an unplaceable stamp may be a second leg of a cycle already counted. Neither the offline suite nor the field tracer could see this: both used fixtures that were distinct cycles *by construction* (`v1.gated.json`/`v2.gated.json`, and v43/v44). The fixtures now carry the real grammar.
- **An unrecorded leg set does NOT block — it is reported.** `legs: null` is what a cycle stamped without `--legs` records, and it reads as a cannot-judge, not a mismatch: every stamp written before the field existed has none and was not thereby wrong. This is deliberately **unlike** `suite`, which the gate measures itself when asked; a hard fail here would fire on cycles that legitimately passed, which is the calibration error `docs/learnings.md` already records (detectors written as hard fired 104/49/48 times on documents that had passed 74–83 cycles). It is still never silent: `EXIT: READY … legs=unrecorded`, and `GATE-LEGS: unrecorded` on **every** stamped PASS, so the nudge lands each cycle at the point of use rather than once at the exit.
- Never parse the gate via `$?`/exit code — parse the `GATE:` token; the gate exits 0 on a verdict by design.
- Never auto-merge on `WITH_FIXES` or `NO` from agy.
- Never write `phase = null` before Phase 5g completes (that disarms the TDD hook prematurely).
- Never run `git push --force`.
- Never continue a run past `CTXBUDGET: HALT mode=run` (80% window used) — halt `<phase>:context_ceiling`, **invoke the `handoff` skill in WRITE mode** (`Skill(skill: "handoff")`; never a hand-written doc — READ finds a handoff only in the canonical store under its branch slug), and release the claim. Overflow mid-phase is unrecoverable and compacting afterwards recovers nothing; see §"Run-context ceiling".
- Never call `advisor()` above ~45% window used — it forwards the whole transcript, so the turn costs ~2x the current context and above 50% it cannot fit. Measure with `h_mad_context_budget.py` (read the `CTXBUDGET:` token, never `$?`); above the ceiling use the substitute ladder in §"Orchestrator context hygiene", not a smaller advisor call — there is no such thing. Surfaced by `hooks/h-mad-advisor-warn.sh` in any session where it is wired — an ADVISORY, not enforcement: `advisor` is a server-side tool no tool-scoped hook event fires for, so nothing can refuse the call (J44). Documentation everywhere else.
- Never invoke Codex or agy directly — always via `hmad-dispatch` (see `references/agent-substrate.md`), which also picks inline vs file-indirection delivery by prompt size, per CLAUDE.md §F-12.
- Never time-bound a command with `timeout` or `gtimeout` — **neither is a macOS system component**, so the form is unportable in both directions. Where coreutils is absent the call dies at 127 and the reflex is to re-run the same command *unbounded*, which does not fail at the deadline, it hangs the phase. Where someone has run `brew install coreutils` it silently *works*, which is worse: the 127 that used to expose the improvisation never fires. **What this box has is not an input to the rule** — h-mad already owns a time-bounder, reachable wherever `hmad-dispatch` is, so the form is forbidden unconditionally rather than because of any downstream failure; for anything committed or dispatched it is a new external CLI dependency besides. A local `command -v timeout` that succeeds is not licence — it proves only that this box has coreutils. Use `hmad-dispatch run --timeout <s> -- <cmd...>` (exit 124 at the deadline, GNU convention; the same process-group watchdog `exec` uses). If no time-bounder is reachable, **halt** — an unbounded retry is a silent downgrade, and in a log a hang and slow work look identical.

### A dispatch that rewrites the wrapper tears its own read

`hmad-dispatch.sh` ends `main "$@"; exit $?`, and the `exit` on that line is load-bearing.
Bash reads a script incrementally by byte offset, so a Phase-5 task that rewrites the wrapper
while dispatching through it leaves bash seeking to a stale offset in a longer file. Measured
twice, both **after** the child had already succeeded:

```
codex exec rc=0
line 3597: ame: command not found          <- the tail of a split identifier
line 3619: unexpected EOF while looking for matching `'
```

turning a good dispatch into a wrapper rc of 127 and 2. Those line numbers point at a blank line
and a comment in the version measured, which is the signature of a stale offset rather than a
syntax error — and is why this survived as "two wrapper bugs" in a backlog for weeks. **It is one
defect with two symptoms, and `RUN_RC` is not a work signal when the task edits the wrapper it
dispatches through.** Reproduced and guarded in `tests/test_hmad_dispatch_torn_read.py`, control
included.

## Editing this skill while a run is in flight

`~/.claude/skills/h-mad` **is a symlink into this repository**, so editing the working tree edits
the *live* skill. A run already in progress will read whatever is on disk at the moment it next
opens a file — including a half-finished edit, or a script whose test has not been written yet.

When a run is in flight, **edit in a git worktree** and merge when it is clean; the in-flight run
keeps reading the merged tree and never sees an intermediate state. `hmad-dispatch worktree-create`
already does this for fanout modules; the same applies to the operator editing by hand.

Two second-order consequences, both observed:
- The suites are coupled. A sibling repo's tests reach these scripts *through the symlink*, so a
  change here can fail a suite in a repo you did not touch. Run both before merging.
- Never run a history-rewriting git command (`reset --hard`, `checkout --`, `stash`) with
  uncommitted skill edits in the tree. Commit first — this is `## Mutation verification` applied
  to your own work, and a lost implementation is indistinguishable from one never written.

**Assert a scripted bulk edit was insertion-only before committing it.** When a script splices N
lines into a long document, check that `git diff --numstat` reports `N 0`, that every added line
matches the expected shape, and that the document's identifier set is byte-identical before and
after. Three commands, and they are what distinguishes a clean splice from a slice assignment that
quietly ate a section — a failure this repo has shipped before. The same check catches an append
that landed in the wrong place: a deletion count of zero says nothing about WHERE the insertion
went, so pair it with a grep for the value at its intended anchor.

## Confirming a suspected defect before fixing it

When you suspect a hole in a resolver, guard, or parser, **confirm it empirically before designing
the fix**. Write a throwaway probe that **drives the real function through the existing test
helpers** — source the shell function, or import the harness helpers from `tests/` into a scratch
pytest — feed it the inputs you suspect, and print what actually comes back. Then **delete the
probe**; a probe that survives becomes a second, untested harness that drifts from the first.

This is cheap and it repeatedly changes the answer. Probing `_worktree_path` against the selector
grammar took one command and converted a filed defect ("this selector form is rejected", true but
harmless) into the real one ("every *documented* selector form skips the guards entirely, and one
of them silently destroyed a worktree holding an unmerged commit"). An earlier probe in the same
session turned two hypotheses into verified bugs and killed a third that was wrong.

The failure it prevents is designing against an imagined mechanism. A fix aimed at the wrong
mechanism still passes its own tests, because those tests were written from the same wrong model.

## Filing to a public tracker

Before filing an issue, comment, or reply to a **public** tracker, **grep the body against a
forbidden-term list** and fix any hit. At minimum search for **absolute paths, usernames, sibling
project names**, private slugs, internal symbol names, and hostnames.

The bodies are assembled from live diagnostics — terminal listings, error envelopes, file paths —
so leakage is the default outcome, not an unlucky one. The check is mechanical and takes one
command; do it *before* the post, because an edited issue keeps its original text in the edit
history and a deleted comment may already be in a notification email.

## Known interactions (coexisting plugins)

`/h-mad` has **zero runtime dependency** on any other plugin. It does, however, coexist with plugins that install Claude Code hooks. The notable one is **OMC** (`oh-my-claudecode`), whose `persistent-mode.mjs` produces two streams of noise during `/h-mad` runs:

- **Autopilot Stop-hook nag** — emits "Autopilot not complete" on most turns even with no autopilot state on disk (an unconditional nag, not state-driven).
- **Tool-error retry guidance** — `post-tool-use-failure.mjs` records any tool failure to `last-tool-error.json`; `persistent-mode.mjs` then injects `[TOOL ERROR - RETRY REQUIRED]` (escalating to "STOP RETRYING" at retry_count ≥ 5) on the next Stop.

The retry-guidance stream was historically triggered by the audit gate itself: the old gate used a non-zero exit (`awk … exit (c>0)`) as its FAIL signal, which the harness reported as a `PostToolUseFailure`. **This is fixed at the root** — the gate now signals via the `GATE:` token and exits 0 (Audit-gate signal discipline, base invariant), so a legitimate gate-FAIL no longer registers as a tool error. The retry-guidance noise during `/h-mad` is therefore resolved skill-side; OMC's behavior was correct given a real non-zero exit.

Workaround for the **separate** autopilot Stop-hook nag (not addressed by the gate fix): `export DISABLE_OMC=1` (or `OMC_SKIP_HOOKS=persistent-mode`) for the session. Never switch to the OMC autopilot skill mid-`/h-mad`.

**bkit and security-guidance install content-scanning `PreToolUse` hooks that deny, not warn.** Neither is an h-mad defect — `/h-mad` never prescribes the idioms involved — but both collide with operator habits during the commit-heavy phases, and the failure mode reads as a tool error rather than a policy decision.

- **bkit ENH-310** (`lib/defense/heredoc-detector.js`) denies a heredoc inside a command substitution, which is exactly the standard multi-line commit idiom `git commit -m "$(cat <<'EOF' … EOF)"`. Use `git commit -F <file>` instead — write the message to a file, then pass it. This matters at Phase 7 and at every `chore(handoff)` commit.
- The match is on **raw command text**, not shell structure, so a command whose *quoted body* merely mentions the pattern is denied too — including one documenting the guard. Writing a plan, report, or handoff that quotes it must go through a script file. (Reported upstream as `popup-studio-ai/bkit-claude-code#145`; a local fix exempting quoted-tag heredoc bodies is carried in `docs/patches/bkit-enh310-quoted-heredoc-body/` in this repository.)
- **security-guidance** (`hooks/security_reminder_hook.py`) matches bare substrings against `Edit`/`Write` content with no file-type gating, so a `.md` or `.patch` is scanned for JavaScript and Python constructs. It calls `sys.exit(2)`, so the write is refused. Warnings dedupe on `{file_path}-{rule_name}` for the session and `check_patterns()` returns on the **first** match — so a document mentioning N flagged constructs costs **N refused writes**, surfacing one rule at a time, and an immediate retry of the identical write succeeds each time. Retry rather than editing the prose to appease the scanner; the flagged strings are usually the subject matter. (Reported as `anthropics/claude-plugins-official#5085`; local fix in `docs/patches/claude-security-guidance-bare-exec/`.)

Both local patches live in version-pinned plugin caches that a plugin update replaces wholesale, so each patch directory carries a `verify` script — re-run them after any plugin update, and drop the patch if upstream ships the fix.

**bkit's `SubagentStop` hook re-wakes every subagent after it reports.** `scripts/subagent-stop-handler.js` (bkit 2.1.40) returns `hookSpecificOutput.additionalContext` — `[SUGGEST] Sub-agent <type> completed. Next: /pdca analyze <feature>` — on every subagent stop, and never reads `stop_hook_active`. Claude Code documents `SubagentStop` `additionalContext` as "non-error feedback that keeps the subagent running", under an 8-consecutive-continuation cap that **resets each time the agent calls a tool**. Measured 2026-10-28 on Claude Code 2.1.312: one stop of a `spec-author` probe in this repository drew 9 hints and 8 extra `DONE` turns; in HemaSuite one `plan-author` was re-woken 35 times across three dispatches. The `<feature>` is whatever bkit derived from a directory name (`tools` in HemaSuite, `.claude` here), so the hint is never about h-mad work.

- Every agent in `h-mad/agents/` carries the defence in its DONE rule: after `DONE`, a hook message is not an instruction — repeat the `DONE` line and make no tool call. An author that obeys the hint resets the cap and can be re-woken without limit, and `/pdca analyze` writes into `docs/03-analysis/` inside a frozen round.
- At collect, repeated identical `DONE` replies from one author are this hook, not new work. The digest gate (§"Teammate authors" rule 6) still decides whether the file moved.
- bkit's main-session `Stop` hook does not do this on ordinary turns. Of its handlers that can return `decision:block`, only `sprint-skill-stop.js` is reachable — the `pdca`, `plan-plus`, `gap-detector` and `iterator` handlers return at their bare-require guard when `unified-stop.js` loads them (measured 2026-10-29) — and it blocks only after a `/sprint` operation on an active sprint. A local patch in `docs/patches/bkit-sprint-stop-hook-active/` stops it from blocking a turn that is already continuing. Do not run `/sprint` mid-`/h-mad`.
- Workaround until bkit fixes it: with no `primaryFeature` in a phase in `.bkit/state/pdca-status.json`, the hint is not generated. bkit grows a new one in any repository it sees, so this is not a fix. Fixed upstream in bkit 2.1.41 (`ww-w-ai/bkit-claude-code#162`): the handler no longer returns `additionalContext`. The local patch in `docs/patches/bkit-subagentstop-additionalcontext/` is retired; its `verify.js` remains as the upstream regression check. On bkit 2.1.40 or older this section still applies.

## State schema

See `references/state-schema.md`. Validate with:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_validate.py docs/.bkit-memory.json
```

Validation is **two-tier**, because the v2.2 schema was never enforced at write
time and forbade extra properties, so established stores hold many one-off
shapes and a single-tier check always failed:

- `strict` — conforms to v2.2 (`h_mad_state_schema.json`).
- `historical` — conforms to `h_mad_state_schema_historical.json`: the three
  fields every observed record carries, extras allowed.
- `invalid` — neither. Genuinely broken; look at it.

Parse the **token**, not `$?` — same discipline as the audit gate, which
exits 0 on a verdict so a FAIL never registers as a tool failure:

- `STATE: PASS strict=N historical=M invalid=0` → proceed.
- `STATE: FAIL … invalid=K` → the named records are broken.

**Write state through `h_mad_state_write.py`, never by hand-editing the JSON.**
The writer validates the record against the strict schema *before* the bytes
land, replaces the file atomically, and holds an exclusive lock across the
read-modify-write:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature <feature> --set last_completed_phase=5 --set current_phase=6
```

Values are parsed as JSON when possible and kept as strings otherwise, so
`phase=null` writes `null`, `current_phase=5` writes the integer, and
`halt_reason=step5d:red_not_all_failing` stays a string. A rejected write exits
2 and leaves the store byte-identical — an invented key cannot reach disk, which
is what turns "never invent a key" from a rule the orchestrator has to remember
into one it cannot break. Only the record being written is validated; legacy
siblings are left alone, so the writer works on stores with history.

**If a record already carries an undeclared key, repair it with
`--drop-undeclared` — do not widen the schema and do not hand-edit.** The guard
validates the whole merged record, so a key that reached the store by some other
route (a hand-edit, a record written before the guard) makes that record
permanently unwritable: claim, release and halt-recording are all refused, which
strands a live feature (J48 — three ad-hoc Phase-5 keys, `current_step`,
`phase5_baseline`, `phase5_progress`, none of which anything read). The refusal
names the offending keys and says which of them your write introduced versus
which were already there. Declaring a key in `h_mad_state_schema.json` is the
remedy only for a field that is genuinely needed and will be *read*; buying a
record's mobility by permanently widening the schema for a write-only note is
the wrong trade.

```bash
# repair and release a bricked record in one command; it names what it removes
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature <feature> --drop-undeclared --release --session-id <your-session-id>
```

What is left is validated like any other write, so stripping cannot launder a
record that is broken for some other reason into the store.

**After writing a record, verify it meets v2.2** — belt and braces, and the way
to check a record written before the writer existed:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_validate.py \
  docs/.bkit-memory.json --feature <feature> --strict-only
```

Never invent a key. If a run needs a field the schema lacks, add it to
`h_mad_state_schema.json` rather than writing it ad hoc — that is exactly how
the store accumulated five spellings of "merge sha".

## Audit prompt assembly

**Read [references/audit-prompt-assembly.md](references/audit-prompt-assembly.md) in full before every audit cycle in a session that has not yet read it — the run's first audit (Phase 3 onward), and any audit after a resume or a new session — and before any implementer dispatch.** It holds the substrate preflight for an audit that precedes Phase 5, the dispatch-time pin re-verification, every step of building, sending and gating an audit prompt, and the rules for judging a cycle (the `Effort:` block before trusting a clean pass, and the working-tree check after every audit dispatch).

## Putting `hmad-dispatch` on PATH

This file spells the wrapper as a bare `hmad-dispatch <verb>`. Put the skill's
`bin/` on PATH once so those commands work verbatim instead of needing the
absolute path to `scripts/hmad-dispatch.sh` (which differs per install and per
checkout):

```bash
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
```

## Second surface — the codex leg

When an audit cycle needs a codex leg beside the primary reviewer, assemble a
separate transport file for that surface and keep the staged report distinct:

```bash
RUN=$(date -u +%Y%m%dT%H%M%SZ)-$$
RP=/tmp/audit_<feature>_<phase>_cycle<N>_codex_run$RUN.report.md
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py \
  --feature <feature> --phase plan|design|impl-plan --cycle <N> \
  --project-root <PROJECT_ROOT> \
  --report-file "$RP" \
  --out /tmp/audit_<feature>_<phase>_cycle<N>_codex_run$RUN.txt
echo "RUN=$RUN RP=$RP"
```

Mint a new `RUN` for every dispatch, re-dispatches included: the assembler claims each report
path and its prompt path once. On `ASSEMBLE: HALT <phase>:report_path_handed`, mint a new `RUN`.
The block ends by echoing `RUN` and `RP`. Substitute those literal values into every
later step: each Bash call is a fresh shell, so `$RUN` and `$RP` do not survive into the
next block.

Dispatch it through the exec path so the codex process reads the assembled
prompt directly and writes the contracted report file:

```bash
hmad-dispatch exec codex /tmp/audit_<feature>_<phase>_cycle<N>_codex_run$RUN.txt \
  --cd <PROJECT_ROOT> \
  --out /tmp/audit_<feature>_<phase>_cycle<N>_codex_run$RUN.out.txt \
  --log /tmp/audit_<feature>_<phase>_cycle<N>_codex_run$RUN.log --timeout 1800
```

After `exec codex` returns, collect the surface report into the docs audit path
before running any gate:

```bash
COLLECT_OUT=$(hmad-dispatch collect-report --surface codex \
  --feature <feature> --phase <phase> --cycle <N> \
  --report "$RP" --out /tmp/audit_<feature>_<phase>_cycle<N>_codex_run$RUN.out.txt \
  --project-root <PROJECT_ROOT>)
printf '%s\n' "$COLLECT_OUT"
```

Read the `COLLECT:` token. Anything except `COLLECT: OK` is a delivery failure:
halt `<phase>:report_not_collected` and print `[H-MAD] <feature> <phase> halted reason=report_not_collected`.
Only the path printed on the `COLLECT: OK` line is gateable; the transport file
is never the audit document.

```bash hmad:exec
if ! printf '%s\n' "$COLLECT_OUT" | grep -q '^COLLECT: OK '; then
  printf '%s\n' '[H-MAD] <feature> <phase> halted reason=report_not_collected'
else
  DOCS=$(printf '%s\n' "$COLLECT_OUT" | sed -n 's/^COLLECT: OK path=\(.*\) delivered=.*/\1/p')
  python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py "$DOCS"
fi
```

## Teammate audit leg — when codex is unavailable

If `codex_status` records Codex unavailable and `fallback_agent=grok`, prefer
Grok as the independent stand-in: dispatch the audit with
`hmad-dispatch audit-cycle --feature <feature> --phase <phase> --cycle <N> --project-root <root> --passes 2 --surfaces agy,grok`.
Grok's GREEN, mutation, and wiring remain **unmeasured** (D4); audit precision
measured on 27 seeds: recall 12/27 against agy's 10/27, fabrication 0/38 against
agy's 0/23 (`SEEDSCORE: PASS`), measured with the calibration-only path-scope
clause (AC-3.9) (`docs/03-analysis/grok-audit-surface.measurement.md`). Check its
reported evidence against source. This audit routing is an orchestrator decision, not a script reading
`fallback_agent` for you. A codex audit round is still owed when Codex returns.
Switching the leg from `doc-auditor` to `grok` changes the stamped leg set: the
exit check reports `legs_changed:` once, starts a new baseline, and needs two
fresh agreeing cycles with the new set. When `fallback_agent` is absent, `null`,
or `claude`, the existing teammate path below is unchanged.

On that existing path, when the codex leg above cannot run, a fresh-context
`doc-auditor` teammate takes its place in the union and **gates**. This is the
audit-side twin of the Phase-5 authoring fallback; it keys off the same
`codex_status` declaration:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature <feature> --set codex_status=exhausted        # available|unavailable|exhausted
```

**Use the state write, not the env var, for this leg.** `HMAD_CODEX_UNAVAILABLE=1` governs the
Phase-5 TDD hook alone — it is a PreToolUse env override read only by `hooks/h-mad-tdd-gate.sh`,
nothing on the audit path reads it, and it leaves no record afterwards. An audit routed on it would
be neither explicit nor auditable, which is the opposite of the property this fallback needs.
**Falling back is explicit and auditable, never silent**, for the same reason it is at Phase 5: a
false declaration is a visible lie in the state record rather than an invisible shortcut. Declare
it, then read it back before you route on it — `available` (or absent) routes to §"Second surface —
the codex leg" and this section does not apply.

Assemble the prompt exactly as the codex leg does — the assembler does not care which surface
consumes its output — but stage the report under a `teammate` surface:

```bash
RUN=$(date -u +%Y%m%dT%H%M%SZ)-$$
RP=/tmp/audit_<feature>_<phase>_cycle<N>_teammate_run$RUN.report.md
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py \
  --feature <feature> --phase plan|design|impl-plan --cycle <N> \
  --project-root <PROJECT_ROOT> \
  --report-file "$RP" \
  --out /tmp/audit_<feature>_<phase>_cycle<N>_teammate_run$RUN.txt
echo "RUN=$RUN RP=$RP"
```

As for the codex leg, mint a new `RUN` for every dispatch. On
`ASSEMBLE: HALT <phase>:report_path_handed`, mint a new `RUN`. The block ends by echoing `RUN` and `RP`. Substitute those literal values into every
later step: each Bash call is a fresh shell, so `$RUN` and `$RP` do not survive into the
next block.

Dispatch the teammate against the assembled prompt **by path**, never by pasting it — it is large,
and a pasted copy is a second version of the prompt that no gate can trace:

```
Agent(subagent_type: "doc-auditor", prompt:
  "PROMPT=/tmp/audit_<feature>_<phase>_cycle<N>_teammate_run$RUN.txt
   REPORT=<the $RP above>
   PROJECT_ROOT=<PROJECT_ROOT>
   This pass is GATING.")
```

**Say `GATING` or `ADVISORY` in the dispatch.** The agent assumes gating when told neither, which
is the safe direction, but a pass that is genuinely advisory and is told nothing spends gating-level
care for no reason — and, worse, an orchestrator that never says it has no record of which it meant.

Then collect and gate through the ordinary path. `--surface teammate` needs **no code change**: the
discriminator token is open by design (§"Audit filename grammar"), and closing that set is what
made 98 real audits invisible once already.

```bash
COLLECT_OUT=$(hmad-dispatch collect-report --surface teammate \
  --feature <feature> --phase <phase> --cycle <N> \
  --report "$RP" --out /tmp/audit_<feature>_<phase>_cycle<N>_teammate_run$RUN.out.txt \
  --project-root <PROJECT_ROOT>)
printf '%s\n' "$COLLECT_OUT"
```

Read the `COLLECT:` token exactly as the codex leg does — anything but `COLLECT: OK` is
`<phase>:report_not_collected`, and only the path on the `COLLECT: OK` line is gateable.

### What this leg does NOT license

- **It is not a second opinion on itself.** The teammate shares a model family with the
  orchestrator whose documents it is auditing, so its blind spots and yours correlate by
  construction — the exact property the union of two surfaces exists to defeat. It is a *stand-in*
  for an independent surface, not an independent surface.
- **It has never been scored against a labelled corpus.** The surfaces it sits beside have numbers:
  over `c45–75` agy produced 6 fabricated must-fixes out of 11 on one feature and
  codex 0 of 25 on the same corpus. The teammate leg was escalated to gating on **yield** — 6
  confirmed must-fixes in one round that **82 codex+agy design cycles** had missed, including a CLI
  parser that was structurally unable to emit the verdict its own named test asserts — not on
  measured precision.
- **Nothing can measure its effort, so its `Evidence:` line is a claim.** The `Effort:` block that
  scores the agy leg comes from the NDJSON of a dispatch `h_mad_audit_cycle.py` ran itself, and
  `h_mad_review_evidence.py` counts tool events out of the same kind of log. An `Agent()` dispatch
  produces neither. What remains is the `Evidence: <N> files opened, <M> greps run.` line the agent
  writes **about itself** — exactly what §"An agent's reported numbers are a claim, not a
  measurement" forbids taking at face value. So the surface with the *weakest* evidence signal is
  the one now holding the gate, and the only check available to you is manual: grep-verify the
  report's `quote:` spans and every cited `path:line` against the tree before acting on a finding,
  and before accepting a clean.
- **So a codex round is owed before anything gated this way is treated as settled.** When codex
  becomes available again, run one round with the real leg on the current tree *before* stamping.
  It is the cheapest available check on the escalation decision, and skipping it converts a
  documented workaround into an undocumented standard.
- **It does not license Claude to write Phase 5 production code — audit-leg selection and
  resolved authorship are separate.** For phase *documents*, `codex_status` alone routes the
  5b audit to the teammate leg; `agy_status` does not route audits. For production authoring,
  read `h_mad_tdd_judge.py implementer`: Claude may write only when FR-2 resolves `claude`
  for every ACTIVE `step5` record on the chain. Both peers must be unavailable for each
  record (through PATH, the environment, or status `unavailable` or `exhausted`), with
  `fallback_agent` absent, `null`, or `claude`. A Codex outage with agy available resolves
  agy, so FR-3 refuses Claude as `agy-authorship`. **Flip `codex_status` back to `available`
  before 5d if codex has returned**, and re-stage the resolved implementer before dispatch.

**Do not drop the agy leg while running this one.** agy is not uniformly hollow, and its evidence
count sorts it: in one round its design pass ran **58** tool calls and found a real defect both
teammate passes missed, while its plan pass ran **2** — the report-file floor, meaning it read
nothing — and returned a clean worth nothing. Same surface, same round, opposite value. **Since #13 the combiner does this for you rather than
asking you to remember it**: pass the pass's NDJSON as the 5th `--pass` field and
`h_mad_audit_cycle.py` returns `UNVERIFIED reason=low_evidence:pN` instead of a clean, with the
`Effort:` block printed beside it as the evidence for that verdict. Without a log there is nothing
to measure and the pass is scored normally, so **the guard only arms when you give it the log** —
supply one for every agy leg. A leg dropped for being sometimes-hollow takes its sometimes-real
findings with it; a leg whose hollow passes cannot certify keeps them.

## Teammate change review — a reviewer that keeps its own report

A fresh-context review of a CHANGE by a subagent **goes to `change-reviewer`**. It applies to an
adversarial round, a second look at a batch, or a review of a fix before merge. Never use a
reviewer type without a Write tool for this. It cannot write the report file it is handed, and its
final reply is cut at about 4 KB. Five consecutive multi-host-runtime rounds (R18–R22) lost their
reports to that truncation and were relayed in ≤3 KB `SendMessage` chunks, reassembled by hand.
`change-reviewer` owns exactly one file, its report, and answers with a `DONE` line carrying the
report's sha256. Gate it through `h_mad_done_gate.py` before reading the report, exactly as
§"Teammate authors" rule 6 requires for the authors and `doc-auditor`:

```
Agent(subagent_type: "change-reviewer", prompt:
  "SUBJECT=<base>..<head> — <what the change claims to do>
   RUBRIC=<correctness | a named invariant | adversarial inputs>
   REPORT=/tmp/review_<topic>_r<N>.md
   PROJECT_ROOT=<PROJECT_ROOT>
   This pass is GATING.")
```

## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)

Every helper's contract — the question it answers, its verdict line, its exit codes, its detail lines and their remedies — is in [references/helper-scripts.md](references/helper-scripts.md). **Read that entry before running a helper whose verdict line or exit codes you have not read in this session, and before acting on a verdict token you have not seen documented this session.** Read the token, never `$?`, unless the entry says otherwise. Register a new helper there, not here.

Helpers (55): `h_mad_extract_verdict.py`, `h_mad_extract_report.py`, `h_mad_collect_report.py`, `h_mad_done_gate.py`, `h_mad_offcontract_scan.py`, `h_mad_audit_cycle.py`, `h_mad_check_memory_index.py`, `h_mad_precheck_doc.py`, `h_mad_delta_review.py`, `h_mad_expect_screens.py`, `h_mad_delta_stage.py`, `h_mad_audit_origins.py`, `h_mad_adoption_check.py`, `h_mad_audit_gate.py`, `h_mad_doc_consumers.py`, `h_mad_branch_evidence.py`, `h_mad_ac_census.py`, `h_mad_archive_feature.py`, `h_mad_live_runs.py`, `h_mad_lane_liveness.py`, `h_mad_install_check.py`, `h_mad_resume_decision.py`, `h_mad_do_preconditions.py`, `h_mad_prescribed_block_guards.py`, `h_mad_assemble_tdd.py`, `h_mad_derive_test_path.sh`, `h_mad_tdd_judge.py`, `h_mad_pane_janitor.py`, `h_mad_new_gate.py`, `h_mad_emit_marker.sh`, `h_mad_state_schema.json`, `h_mad_state_schema_historical.json`, `h_mad_phase7_preconditions.py`, `h_mad_state_staleness.py`, `h_mad_state_write.py`, `h_mad_version_history.py`, `h_mad_state_validate.py`, `h_mad_telemetry.py`, `h_mad_doc_block_exec.py`, `h_mad_mutation_harness.py`, `h_mad_archreview_cycle.py`, `h_mad_baseline_sha.py`, `h_mad_reproduce_flake.py`, `h_mad_backlog_cycle.py`, `h_mad_failure_diff.py`, `h_mad_wire_pin_gate.py`, `h_mad_response_probe.py`, `h_mad_resolved_model.py`, `h_mad_wire_registry.py`, `h_mad_issue_fix_gate.py`, `h_mad_review_evidence.py`, `h_mad_context_budget.py`, `h_mad_host.py`, `h_mad_hook_wiring.py`, `h_mad_doc_shape_check.py`.

A cross-reference `SKILL.md §"…"` to any of these now resolves in `references/helper-scripts.md`:

- §"file-issue-then-fix-under-TDD"

## Git hooks (in `~/.claude/skills/h-mad/git-hooks/`)

These are **git** hooks, not Claude Code hooks. `hooks/` holds the latter (`h-mad-tdd-gate.sh`,
`h-mad-advisor-warn.sh`) and they answer to a different contract; the two directories are kept
apart because the shared word is the whole confusion.

- `pre-push` — refuses a push when any mutation anchor has drifted, and `install.sh` links it into
  a clone's common hooks dir (`--repo <dir>` to target another clone, `--uninstall` to remove only
  symlinks it owns, `git push --no-verify` to override once). This closes the one gap the in-run
  sibling sweep cannot: 5e's precheck and `--check-anchors` both fire inside a mutation run, and
  anchors drift as a side effect of **unrelated refactors** — commits that never go through a run.
  Nothing fails until someone sweeps by hand, and 13 anchors had drifted before the 2026-08-27
  repair. `git push` is the last boundary before that becomes somebody else's problem.

  **The verdict is scored on the `ANCHORS_*` summary line, never on `$?` alone** (§"Audit-gate
  signal discipline"), and `ANCHORS_DRIFTED` or `ANCHORS_UNREADABLE` blocks. A missing harness, an
  `ANCHORS_NOTHING_SWEPT`, and a run that printed no `ANCHORS_*` token at all each warn on stderr
  and **allow** the push: blocking every push in a clone because the tooling is broken is a worse
  failure than missing one drift, and the inverse — allowing silently — is a different bug, so
  none of the three is quiet. A repo with no candidate JSON at all is the one silent allow;
  nothing to guard is not a finding.

  **Which specs get swept is discovered, not configured.** The hook ships in the skill and installs
  into arbitrary repositories, so a spec directory in this file would be a per-project fork of it —
  which is precisely how the two copies of a hook drift apart. It sweeps every tracked `*.json`
  (`git ls-files`) and lets the harness's own classifier decide what is a spec, so it needs no
  naming convention and costs one small read per tracked JSON. Measured in this repository: 77
  tracked JSONs, **19 specs across three directories**, one of them inside an unrelated skill — a
  single-directory parameter would have guarded 16 of the 19 and reported success. Untracked specs
  are invisible to `git ls-files` by design (a push publishes only what is tracked);
  `$HMAD_MUTATION_SPEC_DIR` (colon-separated, absolute or repo-relative) **replaces** discovery for
  the repo where that is wrong — replaces rather than widens, so it can narrow a sweep too.

  Pinned by `tests/test_h_mad_prepush_anchor_hook.py` and
  `tests/mutation-specs/prepush_anchor_hook.json` (14/14 caught). A pre-push hook is the guard
  shape with the weakest natural feedback — on a clean tree a correct one and one that
  unconditionally exits 0 are indistinguishable — so every mutation there forces it toward exit 0
  or toward sweeping nothing.


## Working a `skill-monitoring` item

`docs/skill-monitoring.md` is the standing bug/improvement registry. Closing one is not "read the
fix direction and apply it" — the filing is a snapshot and **the entry can be wrong**. This loop
closed nine items in one session (J1–J5, J11–J13, J17), and the premise-check step alone changed the
fix in four of them.

1. **Verify the entry's premise against the source.** Open the file and line it names; confirm the
   code says what the entry says. J9's stated cause (a test "probes the real binary") was false — the
   test already stubbed it. J1's two hypotheses were resolved by one probe. The registry's own
   *fix direction* is a hypothesis, not a spec: `ASSEMBLE: PASS_OVERSIZE` (J12) and "split by FR
   group" (J13) were both wrong, and one command each showed it.
2. **Reproduce it live** with a throwaway probe matching the real call shape, before designing the
   fix. A green stub suite can certify a bug as fixed; only the live path disproves it. Read a TUI
   pane with `--from-start`, never a tail (J3) — a tail-grep reports SILENT for replies that arrived.
3. **TDD the fix — RED first.** If a pre-existing test breaks, apply §"Regression provenance": check
   whether the test *pinned the defect* before adjusting it. Three tests this session asserted the
   bug as an acceptance criterion.
4. **Mutation-test every guard** (§"Test discrimination"): stub each to its permissive value and
   confirm a test fails. Verify the mutation applied — a `.replace()` matching nothing exits 0 and
   reports the guard as enforced. Never mutate a path-resolver without snapshotting live state first
   (J18).
5. **Dogfood against the runtime.** Every fix on the Phase-5 path (`launch`, `dispatch`, `wait`, the
   substrate record) must run once for real; isolation tests do not exercise adoption, redraws, or
   handle rotation.
6. **Flip the row with evidence**, linking the commit — `MONITORING` → `FIXED`/`DISPROVEN`. A stale
   row is a coverage hole in both directions. Run the same sweep on sibling rows the fix moots.

## Telemetry

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_telemetry.py record \
  --feature <feature> \
  --state docs/.bkit-memory.json \
  --out .h-mad/telemetry.jsonl
```

Non-fatal: if record fails, emit warning and continue to report.

**The cycle counts are derived from the artifacts on disk, not read from orchestrator state.**
`audit_cycles` is `max(N)` over each phase's `<feature>.<phase>.audit.v<N>.md` files, and
`iterate_cycles` is `max(N) - 1` over `<feature>.analysis.v<N>.md` — both via
`scripts/h_mad_cycle_counts.py`, searching the live `docs/` feature directories and
`docs/archive/*/<feature>/`. The `audit_cycles` and `iterate_cycles` fields still exist in the
state schema; they are simply no longer what telemetry reports. Nothing increments them, which is
why they read `0/0/0` on every feature before this changed, and why both drift warnings below
were unreachable.

`--docs-root PATH` (optional, on both subcommands) sets the tree that is searched. **Default**:
the parent of the `--state` file when that parent is named `docs`, else `docs/` relative to the
current directory — so the invocation above needs no change.

Ad-hoc summary: `python3 ~/.claude/skills/h-mad/scripts/h_mad_telemetry.py summary`

`summary` recomputes both counts from disk as it prints, so features recorded before this change
report their real numbers without `.h-mad/telemetry.jsonl` — an append-only log — being rewritten.
A feature whose artifacts are absent falls back to its stored row values, so a deleted or
never-archived docs tree cannot silently zero a real recorded number. The `audit_cycles > 3` and
`iterate_cycles > 3` drift warnings are computed from the displayed values.

### Audit filename grammar — one optional discriminator after the cycle

```
<feature>.<phase>.audit.v<N>[.<discriminator>].md
```

`<discriminator>` is a single dot-free token and is **optional**. Two kinds are in use, and a
file carries at most one of them:

| Token | Written by | Meaning |
|---|---|---|
| `p1`, `p2`, … | `audit-cycle` | One pass of a single cycle's output, split across files. |
| `codex`, `agy`, `teammate`, `claude`, … | whoever ran the audit | The surface that produced this audit. `teammate` is the `doc-auditor` leg (§"Teammate audit leg"). |

Both kinds carry the **same** `v<N>`, so a cycle is one number no matter how many files record
it. The surface half was an unwritten convention until it was documented here: 98 real audits
were named that way while `h_mad_cycle_counts._VERSION_RE` matched only the `p<i>` half, so those
files were invisible to every consumer and nothing raised. **A new surface needs no code change** —
the token is open by design, because a closed `(codex|agy|claude)` set re-creates that blindness
on the fourth surface, silently and for the same reason.

The token is equally deliberately **one dot-free token**: `…v26.codex.draft.md` is not an audit
report, and admitting it hands the Phase-5 gate a file with no `## Must-fix` headings at the
moment it reports a pass. Too wide is as silent as too narrow.

**Read every audit at a cycle, never one of them.** `latest_audit_path()` returns a single
deterministic representative and is fine for counting; anything *deciding whether a cycle is
clean* must use `latest_audit_paths()` (plural) and treat any one dirty or unscoreable report as
an issue — which is what `h_mad_do_preconditions.py` does. `.p1`/`.p2` are two halves of one
audit's output, and `.codex`/`.agy` at one cycle are two different auditors that in this project's
record alternate sides and disagree; scoring whichever the filesystem listed first is
"gate on one audit pass" wearing a green verdict. Archiving copies rather than moves, so the same
filename usually exists both live and under `docs/archive/` — that is one audit, and the live copy
is the one returned.

## References

- `references/inline-protocols.md` — **Inline protocols for all phases (standalone, no external skills)**
- `references/phase-table.md` — full phase gate table
- `references/failure-recovery.md` — halt routes + recovery hints
- `references/measurement-discipline.md` — the orchestrator's OWN verification errors, by species, with the command that closes each (§"Your own measurements")
- `references/state-schema.md` — state schema details
- `references/agent-substrate.md` — Agent dispatch substrate (cmux | orca) — hmad-dispatch verbs, detection, identity pins, pane launch
- `references/orchestration-mode.md` — Orca structured orchestration and Phase-5 worktree fanout protocol
- `agents/{spec,plan,design,implplan}-author.md` — the four phase-document authors (§"Teammate authors")
- `agents/doc-auditor.md` — the teammate audit leg (§"Teammate audit leg")
- `agents/change-reviewer.md` — fresh-context review of a CHANGE that writes its own report (§"Teammate change review")
- `agents/task-executor.md`, `agents/task-labeller.md` — the narrow helper agents (§"Helper work")
- `references/codex-implementer-prompt.md` — Phase 5d/5e Codex dispatch template
- `references/agy-spec-reviewer-prompt.md` — Phase 5e-review agy dispatch template
- `references/agy-architectural-reviewer-prompt.md` — Phase 6a-prime agy dispatch template
- `references/agy-skill-reviewer-prompt.md` — reviewing a **skill** (doc+script family) rather than a feature; not phase-gated, dispatched via `exec agy`. See §"Reviewing a skill with agy"
