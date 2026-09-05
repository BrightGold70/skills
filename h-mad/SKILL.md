---
name: h-mad
description: Orchestrate the 7-phase H-MAD (Hawk Multi-Agents Development) workflow end-to-end. Standalone — no external skill dependencies (spec-kit, b-mad, or pdca). All phase protocols are built-in. Project-agnostic; splices project-specific Axis B invariants from `<PROJECT_ROOT>/.h-mad/invariants.md` into audit prompts at dispatch time. Use when user invokes /h-mad "<feature>", /h-mad do "<feature>", /h-mad status, or /h-mad reset "<feature>".
---

# /h-mad — 7-phase H-MAD Orchestrator (v2.2, standalone)

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
   `INSTALL:` token — never `$?`, which is 0 on both verdicts by design.
2. Are the hooks **wired**, not merely installed? Run
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_hook_wiring.py` and read the `WIRING:`
   token. This one never halts — see §"Wired, not just installed" — but it is not
   optional to *run*: an unwired gate is silent in exactly the way a passing one is.
3. Are the **agents registered**? The five teammate definitions this skill dispatches
   (§"Teammate authors", §"Teammate audit leg") live in `agents/` inside this checkout and are
   reached through user-scope symlinks:

   ```bash
   for n in spec-author plan-author design-author implplan-author doc-auditor; do
     ln -sfn "<checkout>/h-mad/agents/$n.md" "$HOME/.claude/agents/$n.md"
   done
   ```

   A **project-scoped** `.claude/agents/<name>.md` shadows the user-scope link, so a copy left
   there is a fork that drifts silently. Report it rather than deleting it — it may be a deliberate
   local override — per §"Bootstrap action" step 4, which owns this instruction. Verify with
   `head -2 ~/.claude/agents/<name>.md` naming the agent, not by trusting the link's presence:
   a dangling link and a correct one are both "present".
   Getting this wrong is not a halt: `Agent(subagent_type: "plan-author")` fails loudly with an
   unknown agent type, so it announces itself.
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
detail lines each name one remedy, and all ten have one:

| detail line | what it means | remedy |
|---|---|---|
| `SKILL_NOT_INSTALLED` | no `~/.claude/skills/h-mad` at all | `ln -s <checkout> ~/.claude/skills/h-mad` |
| `SKILL_NOT_SYMLINK` | a real directory — a stale **copy** | remove it, then symlink as above |
| `SKILL_DANGLING` | symlink whose target is gone (checkout moved/deleted) | repoint it at the current checkout |
| `SKILL_NOT_A_CHECKOUT` | symlink resolves somewhere without `SKILL.md` | repoint it at a real h-mad checkout |
| `HOOK_NOT_INSTALLED` | no `~/.claude/hooks/h-mad-tdd-gate.sh` | `ln -s <checkout>/hooks/h-mad-tdd-gate.sh ~/.claude/hooks/h-mad-tdd-gate.sh` |
| `HOOK_DANGLING` | hook symlink whose target is gone | repoint it at the same checkout as the skills link |
| `SPLIT_INSTALL` | both links resolve, into **different** checkouts | repoint whichever is wrong so both name one checkout |
| `SIBLING_NOT_SYMLINK` | another skill from this checkout installed as a stale **copy** | `rm -rf ~/.claude/skills/<name>` then `ln -s <checkout>/<name> ~/.claude/skills/<name>` |
| `SIBLING_DANGLING` | sibling symlink whose target is gone | repoint it at the current checkout |
| `SIBLING_WRONG_CHECKOUT` | sibling symlink resolving into a **different** checkout | repoint it at the same checkout as the skills link |

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
     for n in spec-author plan-author design-author implplan-author doc-auditor; do
       ln -sfn "$SK/agents/$n.md" ~/.claude/agents/"$n".md
     done
     for n in spec-author plan-author design-author implplan-author doc-auditor; do
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
will not see `owned_elsewhere`. On any token other than `owned_elsewhere`, claim
the feature before working it, and release when you stop:

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
```

**A non-`owned_elsewhere` token guarantees the claim will be accepted.** The router
and `--claim` read the SAME staleness window (`h_mad_state_ownership`), so a claim
the router judged abandoned is takeable without `--force`. They used to disagree: the
router released a 19.6h-dead claim while `--claim` refused it outright, leaving
`--force` as the only way through. Keep `--force` for the one case it names — taking a
feature from a session that is still **live** (`owned_elsewhere`) — and treat needing
it on any other route as a bug, not as the usual step.

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
| `owned_elsewhere` | Another session holds this feature and was seen within the staleness window. **Stop and surface it** — print the owner id and heartbeat, and ask whether to coordinate, take over (`--claim <id> --force`), or pick a different feature. Never proceed silently: two sessions on one feature produce contradictory conclusions on the same branch. |
| `start_fresh` | Initialize `orchestrator_state[<feature>]`. Enter Phase 1. |
| `resume_manual` | Print current phase + last marker. Ask "continue from phase <N>?" |
| `enter_autonomous` | Print "all manual checkpoints clear; entering autonomous block." Enter Phase 5. |
| `halted` | **Run the staleness check first** (below) — a halt that commits landed after is usually already resolved. Then print `halt_reason` + recovery hints (see `references/failure-recovery.md`). Ask "resume, retry, or reset?" |
| `complete` | Print "feature complete; see docs/archive/<YYYY-MM>/<feature>/". Exit. |

## Per-phase actions

See `references/phase-table.md` for the full gate table. Detailed inline protocols in `references/inline-protocols.md`.

1. **Brainstorm** — run inline brainstorm protocol (`references/inline-protocols.md §Phase 1`). Output: `docs/01-plan/features/<feature>-brainstorm.md`. Wait for user approval.
2. **Specify** — **dispatch the `spec-author` teammate** (§"Teammate authors"); the inline spec protocol (`references/inline-protocols.md §Phase 2`) is its contract, not yours to execute. Output: `docs/01-plan/features/<feature>.spec.md`. Wait for user approval.
3. **Plan + Audit-Plan** — **dispatch the `plan-author` teammate** (§"Teammate authors"); the inline plan protocol (`references/inline-protocols.md §Phase 3`) is its contract. Output: `docs/01-plan/features/<feature>.plan.md`. Wait for user-approved v1.0, then auto-cycle: audit-plan on **two surfaces** (§"Never gate on one audit pass" chooses which) → awk gate on the union → if must-fix > 0 OR should-fix > 0, surface bullets, then **re-dispatch `plan-author` with the findings** (§"Teammate authors" — a revision routes to the owning author, never to you) → re-audit. **Exit ONLY when both must-fix = 0 AND should-fix = 0.** No cycle cap — the rationale is that if errors are already known (whether breakage-level or improvement-level), shipping them is worse than burning more cycles. Operator escape at any cycle: author `.audit.v<N+1>.md` with `## Acknowledged-not-fixed` section listing the should-fix items the operator chooses to defer, commit `[audit-override]`, and the gate treats those items as cleared.
4. **Design + Audit-Design** — **dispatch the `design-author` teammate** (§"Teammate authors"); the inline design protocol (`references/inline-protocols.md §Phase 4`) is its contract. Output: `docs/02-design/features/<feature>.design.md`. Same audit cycle pattern as Phase 3, with revisions re-dispatched to `design-author`. Back-propagation: if design revision invalidates a plan decision, return to Phase 3 to re-clean, then re-enter Phase 4 audit from cycle 1.
5. **Implementation (autonomous)** — see Phase 5 sub-section below.
6. **Verification (autonomous)** — run inline gap analysis (`references/inline-protocols.md §Phase 6`). If match rate < 90%, run inline iterate (`references/inline-protocols.md §Phase 6b`) — 5-cycle cap. Loop until ≥90% AND 100% test pass. Phase 6a-prime is an agy architectural review before gap analysis.
7. **Closure (autonomous)** — **run the precondition gate first; it is what makes the 6-before-7 ordering real rather than documented:**
   ```bash
   python3 ~/.claude/skills/h-mad/scripts/h_mad_phase7_preconditions.py \
     docs/.bkit-memory.json --feature <feature>
   ```
   Parse the **token**, not `$?` (exit 0 on any verdict, 2 on operational error). `PHASE7: BLOCKED` → halt `step7:verification_not_run` and address each blocker. It refuses to close a feature that never ran Phase 6, whose analysis is missing or states no match rate, whose rate is below threshold, whose 6a-prime returned `WITH_FIXES`/`NO`, or that carries an open halt. A `SKIPPED_NO_PANE` archreview **blocks** the gate — a headless `exec agy` review satisfies the gate. Then `h_mad_telemetry.py record`, inline report + archive (`references/inline-protocols.md §Phase 7`), then `git add -A && git commit && git push origin main`.

## Phase 5 (Implementation) sub-steps

**Substrate preflight (Phase 5 + first audit dispatch).** Run `hmad-dispatch env`.
If it exits non-zero → halt `<phase>:no_substrate`. Record the printed substrate +
agent mapping into state so the run log states which environment it dispatched under:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature "<feature>" \
  --set substrate='{"name":"orca","agents":{"codex":"term_…","agy":"term_…"}}'
```

State is the carrier and `h_mad_telemetry.py record` is the reporter — it copies the
field onto the Phase-7 row it already builds from this record. Writing it here is what
makes the step executable at Phase-5 time; `record` is a close-out call and cannot
serve a Phase-5-start instruction. This is the explicit environment check (cmux vs orca) — do it
before any `send`/`read`. See `references/agent-substrate.md`.

**Dispatch enforcement.** `env` ends with a canonical `PREFLIGHT:` line and writes a
receipt when the verdict is `PASS`:

```text
PREFLIGHT: PASS
PREFLIGHT: FAIL stale=codex
PREFLIGHT: FAIL conflict=term_x
PREFLIGHT: FAIL unresolved=codex,agy
PREFLIGHT: FAIL stale=codex,agy conflict=term_x
```

`unresolved=` fires only when a coordinator resolves — i.e. the session is wired
for orchestration and is one step from dispatching, with nowhere to dispatch to.
An un-set-up session (no coordinator) keeps `PASS` with agents unresolved, since
nothing is about to dispatch there.

- `hmad-dispatch send` **refuses with rc=1 and sends nothing unless a valid receipt
  exists**. The receipt must say `PASS`, be within its TTL, and still match the
  current handle resolution. The refusal reason token is one of
  `preflight_not_run`, `preflight_expired`, `preflight_handles_rotated`, or
  `preflight_agent_conflict`.
- Recover `preflight_not_run` by running `hmad-dispatch env` and confirming
  `PREFLIGHT: PASS`, then retry. Recover `preflight_expired` by running `hmad-dispatch
  env` again to refresh the receipt, then retry.
- Recover `preflight_handles_rotated` by re-pin or relaunch the affected agent,
  run `hmad-dispatch env` again, and retry. Recover `preflight_agent_conflict` by
  pinning distinct handles for codex and agy, then run `hmad-dispatch env` again
  and retry. `clear` and `interrupt` remain unguarded recovery verbs.
- Re-assert `PREFLIGHT: PASS` after any re-pin (`pin`, `pin-agents`, `launch`);
  otherwise halt `<phase>:preflight_failed` and recover using the matching token.
- **Read the token, never `$?`.** `env` exits 0 on *both* verdicts by design — the base
  invariant on audit-gate signal discipline reserves a non-zero exit for genuine
  operational errors, because it registers as a `PostToolUseFailure` and leaks into
  coexisting plugins. A FAIL therefore cannot be detected by exit status, and
  `hmad-dispatch env && …` is **not** a guard. The send refusal is the enforced guard.
- `FAIL` is raised by a stale pin or a codex/agy handle collision only. An `UNRESOLVED`
  agent is *not* a failure — it is the ordinary state of a session that is not
  dispatching. Dispatch-readiness is `pin-agents`' job (it exits 1 on unresolved).

The detection has been in `env` for a while; what was missing was any step obliged to
consume it, which made a correct signal advisory. Skipping this assertion re-opens the
exact failure the token was added to close.

**Pin the agents once (Orca) — do it while identity is known.** Immediately after
a clean `env` under orca, run `hmad-dispatch pin-agents` to freeze the resolved
codex+agy handles into the session pin file, so later dispatches survive preview
decay. **Codex has no title identity at all, by construction.** Orca's `.title` is
the pane program's OSC title if it emits one and otherwise the enclosing *tab's*
title — and a tab title is shared by every leaf in that tab. Codex emits no OSC
title, so any `.title` matching `codex` was inherited and says nothing about what
runs in that pane. Observed live 2026-07-22: an **agy** pane sitting in a tab named
`Codex - skills repo` matched `^codex`; both agents return a well-formed sentinel
report, so handing Codex's work to agy would have been silent. Auto-detect therefore
never matches Codex on title — only on a fresh pane's `gpt-N` banner, which scrolls out of
the PREVIEW once it works — the tail-evidence pass recovers it from retained scrollback.

**Identity does exist — in a different call (J16, shipped 2026-07-23).** `orca worktree ps`
returns `agents[].agentType` keyed by a `paneKey` of `<tabId>:<leafId>`, and `terminal
list` returns `.tabId`/`.leafId`. `_orca_find` joins them as **Pass 0**, ahead of the
title, preview and tail-evidence passes, which resolves the case above exactly: measured live with pins
bypassed, both agents went from `UNRESOLVED` to correct. `agentType` is `antigravity`,
not `agy`. This does not retire pinning — handles still rotate, and `launch` still owns
identity best — but an un-owned pane is now recoverable. (stablyai/orca#9870, which asked
for this field, is closed as completed — it already existed in `worktree ps`.)

**A pin file records intent, not state.** Handles rotate. Measured on 2026-07-22:
every Orca handle rotated mid-run, `env` still printed the dead pins, and a dispatch
reported `Sent 7293 bytes` into a stale handle and simply vanished — no error, no
report file, no work done. **"Sent N bytes" is not delivery, and a resolvable pin is
not a live pane.** The wrapper now checks liveness at each point where a wrong handle
is cheap to catch:

| verb | behaviour on a handle the listing proves is gone |
|---|---|
| `pin` / `pin-agents` | refuses to write it (`pin --force` to pin a pane that does not exist yet) |
| `env` | prints `<handle> STALE` plus a `stale pins:` line — never as addressable |
| `send` | refuses, `terminal_handle_stale`, **nothing is sent** |
| `verify <agent>` | 0 live · 1 unresolved/`stale_pin` · 2 unknown agent |
| `resolve` | echoes the pin unverified, by design — pass `--verify` for the check |
| `worktree-rm` | refuses with `worktree_has_uncommitted_work` or `worktree_has_unmerged_commits`; pass `--force` to skip both guards |

`env` also prints `CONFLICT:` when codex and agy resolve to the **same** handle. Two
agents cannot be one pane, so identical handles prove at least one resolution is
wrong — and that is precisely the shape a tab-inherited title produces. Pin both
explicitly when you see it.

Only *positive* evidence blocks anything: if `orca terminal list` cannot be read at
all, the send still goes, because a pin has to keep working when the listing does
not. `resolve` stays listing-independent for the same reason — use `verify` when you
need the check.

**A missing report is neither pass nor fail.** This paragraph is the **pane-path** rule;
for the `exec` path there is no pane to read, so see §"A missing report on the `exec`
path" instead. If `report-wait` times out, read the
pane before concluding anything: `terminal_handle_stale` means the dispatch never
landed, and `Selected model is at capacity` means the agent stopped after doing the
work. Check the working tree for work completed but never reported. `pin-agents` therefore **fails
loud (rc=1)** if it cannot resolve an agent, naming the missing one and the exact
env var to set; a run must not proceed with Codex unpinned. If Codex does not
auto-resolve, read its handle from `orca terminal list` and
`export HMAD_ORCA_CODEX_TERMINAL=<handle>` (ideally captured right after launching
Codex, before it works), then re-run `pin-agents`. The env-var pin always
overrides; `pin-agents --clear` resets. Skip on cmux (surface pins there).
**Zero-manual alternative**: to start a FRESH agent rather than reuse an
operator-launched pane, `hmad-dispatch launch <codex|agy>` runs `orca terminal
create`, resolves the pane's live handle by joining the create response's `paneKey` against `terminal list`, and pins that —
no title/preview dependence, no manual pin (H5). Use `launch` when h-mad owns the
agent; `pin`/`pin-agents` when adopting an existing pane.

- **5a** — arm hook, then **dispatch the `implplan-author` teammate** (§"Teammate authors"); the inline impl-plan protocol (`references/inline-protocols.md §Phase 5`) is its contract. Write `orchestrator_state.<feature>.phase = "step5"` + `autonomous_entry_ts = <now>`. Output: `docs/01-plan/features/<feature>.impl-plan.md`.
- **5b** — auto-audit impl-plan (same audit-prompt mechanism as Phases 3/4 — see §"Audit prompt assembly"; §"Never gate on one audit pass" chooses the two surfaces). Write each surface's audit to `docs/01-plan/features/<feature>.impl-plan.audit.v<N>[.<surface>].md`. Run awk gate on the union. If must-fix > 0 OR should-fix > 0, **re-dispatch `implplan-author` with both the must-fix AND should-fix bullets** (§"Teammate authors" — you relay findings, you do not regenerate the document yourself); cycle until **both must-fix = 0 AND should-fix = 0**. No cycle cap — same rationale as Phase 3 (known errors at any severity worth fixing > shipping). Operator escape at any cycle: author `.impl-plan.audit.v<N+1>.md` with `## Acknowledged-not-fixed` listing deferred should-fix items, commit `[audit-override]`, gate treats those as cleared. **Tag each ack bullet with a `[key]`** — `- [ac-1.4 teardown-leak] <text>` — and it keeps matching however the next cycle's reviewer re-words the finding; without one, the match survives re-formatting (emphasis, backticks, wrapping, case) but not a genuine re-wording, and you pay a cycle re-acknowledging it. **There is deliberately no fuzzy matching** (§"Why the ack match is not fuzzy").

  **Then run the wire-pin gate — 5b is the last gate that can require it.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/<feature>.impl-plan.md --feature <feature>`. Read the `WIREPIN:` token, never `$?` (`UNSHAPED` exits 2 because it is a cannot-judge, not a verdict). On `WIREPIN: PASS`, 5b automatically registers each passing `wiring` task in `.h-mad/wires.jsonl`; without `--feature`, registration is skipped. `UNREADABLE` → halt `step5b:impl_plan_unreadable`: the gate could not read the file at all, so nothing was parsed — this token carries **no `tasks=`/`wiring=` counts** precisely so it cannot be mistaken for a verdict or routed by a count that was never measured; the stderr `ERROR:` names the path, which is almost always wrong rather than the plan. `UNSHAPED` → **read the `tasks=` count before choosing a remedy**: `tasks=N` with N>0 → halt `step5b:impl_plan_unshaped`, the plan declares no `Task shape` at all, so a wiring task in it is indistinguishable from new behaviour — return to 5a and **re-dispatch `implplan-author`** against the current template (§"Teammate authors"; this is a revision like any other, and regenerating it in your own context is the loop that cost 34 cycles); `tasks=0` → halt `step5b:impl_plan_no_tasks`, the parser saw no task header, so nothing is missing a field — you are almost certainly pointed at a legacy `.plan.md` or the design doc rather than the `.impl-plan.md`. `FAIL` has two causes and two different remedies, so **read the detail lines, not just the verdict**: an `unpinned:` line → halt `step5b:wire_pin_missing:<task>` and return to 5a to name the `WIRE`/`WIRE-PIN`; a `mislabeled:` line → halt `step5b:wire_pin_shape_mislabel:<task>` — the fields are already filled in, so nothing is missing to add and the missing-pin remedy would read as already satisfied. After 5b nothing downstream can tell a wired build from an unwired one, which is why the obligation is mechanical here and advisory nowhere.

  A shape is a self-declaration, and closing only the *absent* case leaves the plan one edited word from a PASS: demote a pinned `wiring` task to `refactor` and `wiring` drops to 0 with `unpinned=0`. The gate therefore trusts the filled-in `WIRE`/`WIRE-PIN` over the shape word — a task carrying either under a non-`wiring` shape contradicts the template, which declares both fields `wiring` shape only. Unfilled template lines and placeholders still count as declaring nothing, or the guard would refuse every plan the template generates.
  This is the 5b auto-register step: every passing `wiring` task is written to `.h-mad/wires.jsonl`.
- **5c** — baseline branch: `git checkout -b feature/NNN-<slug>`; commit impl-plan + audit files.
- **5d** — RED dispatch (see `references/codex-implementer-prompt.md`). **Stage it with `h_mad_assemble_tdd.py --phase red` rather than by hand** — it cuts §"Task N" from the impl-plan, fills the template, and prints the exact command block with the model, the scoped test path and the probed interpreter already baked in; hand-assembly produced five distinct invocation mistakes across two sessions, every one a default. It refuses a 5d without the stated counts, which is the one judgement here that must stay yours. **Transport: default `hmad-dispatch exec codex` for a one-shot RED** — hard exit code, no scrape, monitor via `--log` (§"Exit-code dispatch for 5d/5e"); use the pane path (`send`) only for an iterative revision loop. The pane-path steps in the rest of this bullet (alive-check, context clear) apply only when you use `send`; `exec` is a fresh subprocess and needs neither. For the pane path: verify codex + agy are alive by **reading `hmad-dispatch env` and requiring `PREFLIGHT: PASS`** — do not chain `alive codex && alive agy`, which branches on `$?` and is the exact habit §"Audit-gate signal discipline" forbids (`env` deliberately returns 0 even on `PREFLIGHT: FAIL`, so a `&&` chain reads a failure as success). Refuse on anything but `PASS` → halt `step5d:no_<agent>_pane`. **Immediately after confirming each pane is alive, clear its context** (see §"Agent-pane context hygiene") so no prior-feature/prior-cycle conversation bleeds into this feature's TDD. For each module, dispatch Codex for tests; dispatch agy for coverage review. **In the dispatch, state the expected failing/passing counts for the task and label any regression guards** — tests asserting behaviour that already works, which must pass from the first run. Read each `STATUS:` with `h_mad_extract_verdict.py` (§"Reading a dispatch verdict"); no extractable verdict after a re-read and re-dispatch → halt `step5d:no_verdict:<module>`. Then verify the results **match the stated counts**; halt `step5d:red_not_all_failing` when an unlabelled test passes without implementation.

  Not every RED task is all-new behaviour. A refactor-shaped task legitimately lands with most of its tests green, and a blanket "every test must FAIL" halts a correct RED — worse, the cheapest way for an implementer to satisfy it is to weaken an assertion or assert the current buggy value, manufacturing a failure that then "passes" in 5e without anything being fixed. Stating the counts up front makes the check discriminating in both directions: an unexpected pass still halts, and an expected one does not.

  **The third task shape is `wiring`, and counts cannot gate it.** When the deliverable is a connection rather than new behaviour, carry the task's `WIRE:` and `WIRE-PIN:` lines from the impl-plan into the dispatch, and require the RED report to give the **failure mode per test, not only the count**. A test whose RED is an `ImportError`/`AttributeError`/`NameError` — the callee missing — is not a wire test: it fails for the callee's absence and goes green the moment the callee exists, wired or not. The `WIRE-PIN` test's RED must be an assertion about the **caller's** observable behaviour (the call was not made; the value did not propagate). The traceback already carries this, so the check costs nothing. A `WIRE-PIN` whose RED reason is a missing symbol → halt `step5d:red_wrong_reason:<module>`. A `wiring` task dispatched with no `WIRE-PIN` at all → halt `step5d:no_wire_pin:<module>`; do not let 5e establish GREEN for it, because nothing downstream can see the wire (`invariants.base.md` §"Connection enforcement").
- **5e** — GREEN dispatch (`references/codex-implementer-prompt.md` + `references/agy-spec-reviewer-prompt.md`). **Stage the Codex half with `h_mad_assemble_tdd.py --phase green`** (the agy spec-review half is still assembled by hand). Note the sandbox rule it enforces for you: never dispatch a pytest-running phase with `--sandbox read-only` — it kills pytest's tempdir, so the run passes without measuring anything. The same applies to the anti-gaming verifier dispatch below, which the assembler does not yet stage. **Transport: default `hmad-dispatch exec` for a one-shot GREEN + its review** (§"Exit-code dispatch for 5d/5e"); use the pane path (`send`) for the iterative revision loop where cycles 2..N reuse the warm thread — there the alive-check + context-clear below apply. For the pane path: re-verify the Codex + agy panes alive and **clear each pane's context** (§"Agent-pane context hygiene") before the first GREEN dispatch of a feature. For each module, dispatch Codex for implementation; dispatch agy for spec-compliance review. Read both verdicts with `h_mad_extract_verdict.py` (§"Reading a dispatch verdict") — never by grepping the scrape for the halt value, which turns an agent's silence into a pass. If agy returns `VERDICT: DRIFT` → halt `step5e-review:spec_drift:<module>`. If no verdict can be extracted after a re-read and re-dispatch → halt `step5e:no_verdict:<module>`. On 3rd consecutive GREEN failure → halt `step5e:green_unreachable:<module>`. **After GREEN + spec-review, run the independent anti-gaming verification** (`references/codex-verifier-prompt.md`): module count → test-discrimination audit → quote the source line for each pinned property → full suite vs the reference, and cross-check every reported count a second way. Codex GREEN says the code was written; agy says it matches the spec; this pass answers "are the tests real and does the source hold the pinned properties" — the axis a green suite and a `STATUS: DONE` cannot self-certify (an agent can emit `DONE` over a fabricated count). A false property or a suite failure → halt `step5e:verify_failed:<module>`.
  **GREEN is established by the revert test, not by "tests pass".** For the module: revert production only (tests untouched) → confirm the RED split returns EXACTLY (the same tests fail) → restore production → confirm green returns. **Verify restoration by executing the symbol** (import it / run the test), **never by grepping the source** — a field-reorder or same-mtime-second `cp` leaves stale `.pyc` bytecode running while the source reads restored. Reading a diff cannot establish this. Only then run the anti-gaming verify.

  **Use this exact sequence to revert and restore.** The production code at this point is *uncommitted*, so a careless revert destroys it permanently: `git restore` / `git checkout --` **deletes** the new implementation with no way back. Stash is the safe direction, but only in the `-u` form — `git stash push -- <paths>` **refuses an untracked path**, and `git add -N` does not rescue it but breaks it (see the measured table below):

  ```bash
  git stash push -u -- <production-paths>   # the revert; -u is what reaches an untracked file
  [ ! -e <one-production-path> ] || echo "REVERT DID NOT LAND — do not trust this run"
  # ... run the module tests here; the RED split must return EXACTLY ...
  git stash pop                             # restore
  ```

  **Assert the revert landed with an EXISTENCE check, never `git diff --quiet`.** For an untracked file `git diff --quiet` is trivially clean — measured: it reported CLEAN with the file sitting in the worktree, i.e. a *false* "revert landed" — so it is exactly the readback that cannot see this failure. A revert that never happened reports as a pass, the same class of silent no-op the mutation harness refuses an unlanded anchor for.

  **Measured on git 2.50.1 (Apple Git-155), scratch repo, one untracked `new.py`:**

  | sequence | rc | stashed | file removed |
  |---|---|---|---|
  | `git stash push -- new.py` | **1** — `error: pathspec … did not match any file(s) known to git` | 0 | no |
  | `git add -N` then `git stash push -- new.py` | **1** — `error: Entry 'new.py' not uptodate. Cannot merge.` | 0 | no |
  | `git add -N` then `git stash push -u -- new.py` | **1** — same `not uptodate` error | 0 | no |
  | **`git stash push -u -- new.py`** | **0** | 1 | **yes** (`stash pop` restores it) |

  Two corrections this table makes to what this section said before, both worth stating because the wrong version was reasoned from for weeks. First, plain `stash push` on an untracked path is **not** a silent no-op exiting 0 — it is a loud rc=1 pathspec refusal. The hazard `git add -N` was introduced to close therefore did not exist in this form. Second, `add -N` is the thing that *breaks* the stash, and `-u` does **not** rescue an `add -N`'d file: the fix is to drop `add -N`, not to add a flag beside it. A reader who keeps `add -N` and appends `-u` gets rc=1 exactly as before.

  **For a `wiring` task the whole-module revert is not sufficient — run the wire-scoped revert too.** Revert the **connection only** (the call site / import / registration / propagated argument), leaving the callee *and* the tests intact, and confirm the `WIRE-PIN` test fails. Module suite still green → halt `step5e:wire_unenforced:<module>`. The whole-module revert removes both sides, so its RED split returns identically whether or not the wire exists; it is structurally incapable of establishing the one decision a wiring task ships. **Assert the revert landed before trusting the run** — use `git stash push -u -- <paths>` (the sequence above; `-u` is what reaches an untracked file, and `git add -N` breaks it rather than enabling it) and read the result back with an **existence** check, since `git diff --quiet` is trivially clean for an untracked path and cannot see this failure. A revert that never happened reports as a pass. Then mutate the other direction: force the connection to fire unconditionally and confirm the fall-through/negative test fails. See `invariants.base.md` §"Connection enforcement".
- **5f** — **Derive the 5c sha, never `git merge-base`.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_baseline_sha.py --branch <feature-branch> [--trunk main]`, reading the `BASELINE:` token, never `$?`. 5c is `git checkout -b …; commit impl-plan + audit files`, so the 5c commit is the branch's FIRST commit and `git merge-base main <branch>` returns the commit it forked FROM — off by exactly the impl-plan commit, and off plausibly, since both are real shas on the right branch. Measured (J41): merge-base `b5c8f41` against real 5c `730cc16`, 313 lines apart — the impl-plan and its three audits, which the wrong base feeds into the review as newly-added content when they are a separate INPUT to it. `UNVERIFIED` is a verdict, not an error: the branch's first commit does not touch an impl-plan, so something was committed before 5c and the rule does not hold — find the commit by hand, and note the token reports it as `candidate=` rather than `sha=` precisely so an unvouched value cannot be scraped as the answer. Only `OK` carries `sha=`. Then, from the repository root, re-verify the registry with `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_registry.py verify --base <5c sha> --rootdir <repository-root> --testpath <project-test-root>` (for this repository, `h-mad/tests` is an example), then run `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_registry.py challenge --base <5c sha>`. `--rootdir` is the repository root (pytest's cwd), while `--testpath <project-test-root>` must name a collectable test root whose node ids are repo-relative; use both to avoid collecting this repository root's pre-existing sibling-project import mismatches. The challenge is **warning-only and verdict-neutral**: an unproven heuristic never blocks an operator. The verifier's halt reasons are `step5f:wire_regression:<feature>::<id>`, `step5f:wire_pin_missing:<feature>::<id>`, `step5f:wire_pin_ambiguous:<feature>::<id>`, `step5f:registry_untracked`, `step5f:undeclared_removal:<feature>::<id>`, and `step5f:unverified_rename:<feature>::<id>`; each is emitted with `[H-MAD]`. **A `pin` may be a single test or a LIST of them**, because one wiring task can wire N call sites and one pin per record could only ever prove site 1 — the rest were left to ACs and the wire-scoped revert, which the registry cannot see. A record resolves only when EVERY pin resolves to exactly one node id, and is verified only when EVERY pin passes: a partial pass would report a wire as proven while a site it names went unchecked. Ambiguity outranks absence, since a pin naming more than one test must be qualified before the record can be judged at all. **On a multi-pin record the halt reason gains a `#<pin>` suffix** — `step5f:wire_pin_missing:<feature>::<id>#<pin>` — and one line is emitted per offending pin; a single-pin record's reason is unchanged. Without the suffix two broken sites on one record emit the same line twice and name neither, which is J43's defect one level down. `register --pin` is repeatable, and stores a bare string when given exactly once, so every record written before the list form reads back unchanged. **The registry's identity is `(owning_feature, id)`, never `id` alone** — `id` is the impl-plan task number and every impl-plan numbers its tasks from 1, so a bare id names no single wire once two features have run. Keyed on the bare id, registration silently upserted one feature's wire over another's and the comparison, keyed the same way, saw the successor and reported nothing — performing exactly the removal the `status`/`removal_provenance`/`removed_by_feature` tombstone fields exist to force an author to declare. Measured before the fix: 1 of the 7 records ever registered in this repository had already been lost that way, and it was unrestorable, because re-registering it evicted the successor (J43). Then run the full test suite: `pytest <project>/tests/ -v --tb=short`. All must pass (100%). Any failure → halt.
- **5g** — `git add -A && git commit -m "feat(<feature>): implement <module>"` per module. Write `phase = null` (disarms TDD gate hook). Emit `[H-MAD] <feature> phase5 complete`.

### Codex authors Phase 5 — enforced, not just instructed

  **Run the mutations through `h_mad_mutation_harness.py` rather than by hand.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py <spec.json>`, where the spec names the suite command and each mutation as an exact `find`/`replace`. Read the `MUTATION:` token, never `$?`. The harness exists because the hard part of this pass is not choosing mutations, it is proving each one **landed**: an anchor that matches zero times mutates nothing, the suite stays green, and the run reports the guard as enforced — the failure `invariants.base.md` §"Mutation verification" names, and one every hand-rolled harness has to re-derive. It refuses any anchor not found exactly once — printing `hint:` lines with the near-miss line numbers, so a drifted anchor no longer costs a manual re-grep — restores the tree on every path including an interrupt, and re-runs the suite afterwards to prove the restore landed. The mutation run performs the sibling sweep itself before the baseline command and refuses on sibling drift with `MUTATION: PRECHECK_FAILED specs=N drifted=K unreadable=J` (exit 2), so a stale sibling spec cannot be hidden by running only the spec you happened to touch. The standalone diagnostic remains available as `python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors <spec.json>…`, reading the `ANCHORS:` token, never `$?`; it applies nothing and runs no tests, so it costs file reads rather than a suite per spec, and it reads the same one-match rule the run does (`anchor_status`) rather than a second copy of it. `ANCHORS_DRIFTED` and `ANCHORS_UNREADABLE` are **separate verdicts because the remedy differs** — re-anchor a spec, versus restore a file that is gone — and `ANCHORS_UNREADABLE` outranks, since a spec cannot be re-anchored into a file that no longer exists (J37); `ANCHORS_UNREADABLE` also covers a swept file that is not valid JSON at all, which judged nothing for the same reason; both exit 2 and both carry `drifted=`/`unreadable=` counts, so the word chooses the FIRST action without hiding the other finding. The `MUTATION:` summary gains `unreadable=` for the same split, but keeps ONE `REFUSED` word: it has five causes and a single remedy, so five verdicts would be worse than the disease. `ANCHORS_DRIFTED` → re-anchor before trusting any verdict from that spec: a drifted anchor mutates nothing, so its run REFUSES, and a refusal measures NOTHING. A relative spec `root` is spec-relative, never cwd-relative: it resolves against the spec file's directory rather than the caller's cwd, which makes the spec portable across checkouts and correct inside a git worktree. Measured 2026-08-26: 7 of 177 anchors across 14 committed specs had drifted, and every one of those guards was unverified while its spec still reported a verdict-shaped line — two of the seven were broken by a refactor made minutes earlier in the same session.

  **To claim a prompt rule WORKS, run it against a control** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_ab_dispatch.py --template <prompt-with-{{VAR}}> --var VAR --a "<rule>" --b "" --observe '<regex with ONE capture group>' --out <dir> --run <argv token>…` (`{prompt}`, `{log}` and `{arm}` are substituted per arm — **put `{arm}` in every OTHER per-arm path you pass**, or both arms share it and arm B silently overwrites arm A, after which the comparison reads B against B and reports `SAME`, J40/F5). **It does not control the environment**: the tool holds the PROMPT constant apart from the declared variable and knows nothing about the rest — a changed file on disk, a different model default, an env var — so `UNCONTROLLED` only ever compares the two prompts, and holding everything else equal is yours to do. An unstated limit reads as a guarantee, which is why this is stated (J40/F3), reading the `AB:` token, never `$?`. One dispatch cannot distinguish a rule that steered the agent from an agent that would have done the right thing anyway, so "the rule is present" gets recorded as "the rule is causally effective". Three verdicts carry it. `UNCONTROLLED` → the arms differ in more than the declared variable (or in nothing), which is the mistake a hand-run A/B actually makes, and it is silent — the run completes, the numbers differ, and the difference is attributed to the wrong cause; nothing is dispatched. `INCONCLUSIVE` → an arm produced no log or the observable never matched, and **two silent arms compare equal**, so this must never read as `SAME`. `SAME` is itself a finding: the rule is present and not causally effective. **The exit code is reported and never scored** — a dispatch killed by its parent shell, a skipped test and a clean run all exit 0, and this repo has been fooled by each. **`--observe` takes the LAST match, not the first**, on the same rule as `h_mad_extract_verdict.py`: an agent's log carries the PROMPT before it carries the answer, so a first-match read routinely returns the observable's own name quoted back out of the instruction — and since both arms echo the same prompt, both observe the same value and the run reports `SAME`, a *finding* rather than an error (J39, measured: a log reading `RESULT: 0` as the echo and `RESULT: 42` as the answer observed `0`). The regex needs exactly one capture group and is refused at the boundary otherwise. **`--run` accepts a dash-leading token in either form** — `--run --model` and `--run=--model` both work; the space-separated form documented here used to fail with `expected one argument` for every real dispatch argv, since they all start with flags (J38).

  **After the LAST edit of a rename or removal, sweep the old identifier across every surface** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_identifier_sweep.py <old-name>… --root <repo> [--allow <path>]…`, reading the `SWEEP:` token, never `$?`. It reports each remaining hit with its surface (code · comment · doc · test · mutation-anchor), so the surfaces that get missed unevenly are visible rather than remembered. `LEFTOVERS` is **not** a verdict that the hits are wrong: deciding explanation-vs-leftover is yours, and a deliberate one is passed with `--allow` rather than edited away — which is why the allowlist is an input and never inferred. Hits on the *stem* of a renamed file (`advisor-gate` after `advisor-gate.sh` is gone) are reported as `related:` and do not move the verdict, because prose naming the concept is both real signal and the sweep's main source of noise. The timing is the property: `a311385` renamed `hooks/h-mad-advisor-gate.sh` and shipped three stale references to a file the same commit deletes, after the sweep was started by hand mid-work and abandoned when more edits followed. Run at the end it costs a second; run during, it is unreliable in exactly the way that produced the defect. **Give every mutation a `test`** (plus a spec-level `target_command`) unless there is a reason not to: `ALL_CAUGHT` only says something went red, and a mutant killed by a crash, a timeout, or an unrelated assertion looks exactly the same as one killed by the guard. With a `test`, only that test counts as a kill and a wrong-catcher is reported as a SURVIVOR naming what actually bit. `SURVIVED` → halt `step5e:mutation_survived:<module>`: the guard does not bite, so write the discriminating test rather than weakening the mutation. `REFUSED` / `BASELINE_NOT_GREEN` / `UNREADABLE` → halt `step5e:mutation_unverified:<module>`: **nothing was measured**, which is not a pass — treat it exactly as you would a cannot-judge from any other gate.

Phase 5 implementation is **Codex's job**; Claude orchestrates, verifies, and gates,
but does not write the production code itself while a feature is in `step5`. This is
now enforced mechanically, not left to discipline:

- The `Write|Edit` PreToolUse hook (`hooks/h-mad-tdd-gate.sh`) blocks Claude's own
  production-`.py` write during `step5`. Codex's writes — whether via `hmad-dispatch
  exec codex` (subprocess) or its pane (`send`) — go through Codex's process, **not**
  Claude's Write/Edit tool, so they never reach the hook. A prod write that *does*
  reach the hook is therefore Claude self-implementing, and is refused.
- The block fires **only when Codex is available** (the `codex` CLI is on PATH and no
  unavailable declaration is set). That is the answer to "use Codex when quota is
  enough": the default assumes Codex can author, so Claude cannot.
- **Falling back is explicit and auditable**, never silent. To let Claude author
  (e.g. Codex is genuinely out of quota or unreachable), record it:
  `h_mad_state_write.py --feature <feat> --set codex_status=exhausted <state_file>`
  (validated enum: `available|unavailable|exhausted`), or export
  `HMAD_CODEX_UNAVAILABLE=1` for a one-off. Then Claude's writes pass — still under
  the test-first gate. A false declaration is a visible lie in the state record, not
  an invisible shortcut.

Test files, docs, config, and shell are never gated; only production `.py`. The
gate stands down outside `step5` and disarms at 5g (`phase = null`).

### Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot

The pane REPL (`send`/`ask`) runs the agent as a long-lived TUI, so completion is
inferred by polling the buffer for idle and parsing a token — there is no process
to reap and no exit code. `exec` instead runs the agent headless as a real
subprocess and returns the agent's own exit code with no idle poll. **It is the
default for a one-shot 5d/5e dispatch** (see the guidance below), because the exit
code is a hard completion signal and it sidesteps most of the pane failure class —
tui-idle false-idle, scrape, identity resolution. Both agents are
supported, on their natural side of 5d/5e:

- **`exec codex`** — the RED/GREEN IMPLEMENTER dispatch (writes tests + impl). Prompt
  via stdin; final message via `--output-last-message`; default `--sandbox workspace-write`.
  **Pass no `--model`/`--effort` unless you mean to override.** Unset, codex
  resolves both from its own `$CODEX_HOME/config.toml` (`model`,
  `model_reasoning_effort`) — the same file its TUI writes — so the model shown
  in the CLI is the model 5d/5e runs, and changing it in one place moves both.
  Nothing in h-mad injects a model. `--effort` is still accepted and reaches
  codex as `-c model_reasoning_effort=<e>` (codex has no `--effort` flag of its
  own); use it, and `--model`, only to deviate from the configured setting for
  one dispatch. **`$CODEX_HOME` is not always `~/.codex`** — under Orca it points
  at a per-account home, so read the value in the environment before concluding
  which config governs. Verify the resolution rather than assuming it: the codex
  session header at the top of `--log` names the resolved `model:` and
  `reasoning effort:`. `hmad-dispatch resolved-model codex --log <f>` reads exactly
  that, and `resolved-model codex` with no log reports the CONFIGURED value
  instead, labelled as such — a config says what will run, never what did. That check matters because a model can be configured that
  **cannot execute a single tool** (`gpt-5.6-luna`, measured): it still writes
  prose, so it comes back as a well-formed `STATUS: BLOCKED`, not as an error.
- **`exec agy`** — the 5e-review (and Phase 3/4/5b audit) dispatch. Runs `agy --print`
  under `--output-format stream-json`, so the transcript is a live NDJSON event stream
  and the wrapper lifts the final response out of the stream's `result` event. A
  headless replacement for the agy `ask` scrape. Because it is a subprocess, it needs
  **no pane and no identity resolution** — the one thing the pane path can still fail
  at for an un-owned agent. The format switch is confined to the `--log` channel:
  `exec` stdout and `--out` still carry the response text verbatim.

Set `HMAD_EXEC_HEARTBEAT_SEC` to control the `exec` watchdog heartbeat interval in
seconds; it defaults to `120`, and `0` disables heartbeats. The feature adds
best-effort start, heartbeat, and exit worktree-comment checkpoints (mobile-visible
under Orca and a no-op on cmux), plus a best-effort desktop notification at exit.
These observability signals cannot change stdout or `rc`.

**Pass `--log` on every `exec` dispatch, background it, and poll `progress`.** Both
backends now write their transcript to `--log` while the run is in flight, so headless
is not blind — but only if you dispatch in a way that lets you look. A FOREGROUND `exec`
prints nothing until the process exits, which is what turns a 15-minute audit into a
blank screen indistinguishable from a wedged one.

**Do not use `tail -f` to watch.** It never returns, so it consumes your whole tool-call
budget and yields nothing; it is for a human at a terminal, not for you. Use
`hmad-dispatch progress <log>`, which returns immediately with a bounded digest.

```bash
# 5d/5e codex (implement), exit-code path. Background + poll:
hmad-dispatch exec codex <promptfile> --out /tmp/exec_<feature>_<module>.txt \
  --log /tmp/exec_<feature>_<module>.log --timeout 900 &
dispatch_pid=$!
hmad-dispatch progress /tmp/exec_<feature>_<module>.log --pid $dispatch_pid
wait $dispatch_pid                      # reap the dispatch
rc=$?                                   # operational: did the CLI run at all
python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_verdict.py \
  /tmp/exec_<feature>_<module>.txt --key STATUS --feature <feature> --phase 5d

# 5e-review agy (audit), exit-code path — no pane to resolve. Background it too:
hmad-dispatch exec agy <promptfile> --out /tmp/rev_<feature>_<module>.txt \
  --log /tmp/rev_<feature>_<module>.log --timeout 600 &
dispatch_pid=$!
hmad-dispatch progress /tmp/rev_<feature>_<module>.log --pid $dispatch_pid
wait $dispatch_pid
python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_verdict.py \
  /tmp/rev_<feature>_<module>.txt --key VERDICT --feature <feature> --phase 5e
```

### Watching a headless dispatch

`hmad-dispatch progress <logfile> [--lines <n>] [--pid <pid>]` prints a bounded,
non-blocking snapshot: transcript format, size, **liveness** (seconds since the last
write, classified `LIVE`/`STALE`), optional process state, and a digest of the last
`n` events — one line per event, tool names and arguments included for agy, framework
`hook:` noise dropped for codex.

Read the `liveness:` line; **never branch on `progress`'s exit code**, which is 0 for
every observable state by design (a gate-shaped exit invites `progress … && continue`,
the `$?`-branching habit §"Audit-gate signal discipline" forbids). **And do not launder that exit code through a pipe**: `progress … | grep -q LIVE` reports *grep's* verdict, not `progress`'s, so a perfectly healthy poll of a LIVE log exits 1 whenever the pattern happens not to match. Measured 2026-08-27 (J35): all five observable states — fresh, dead pid, empty log, missing log, stale — return 0 from the wrapper, while `| grep -q IDLE` on a LIVE log returns 1. That non-zero was read as the wrapper's, and the row it produced blamed the wrapper. `progress` reports,
it does not decide.

- `LIVE` — the agent touched its transcript recently. Keep waiting.
- `STALE` — no write for longer than twice the heartbeat (`HMAD_EXEC_HEARTBEAT_SEC`,
  default 120s). Combined with `--pid …: exited`, that is a dead dispatch, not a slow
  one. The wrapper also writes `#hmad-beat` lines into the transcript on the heartbeat,
  so a genuinely silent-but-alive run still moves the clock — a transcript that stops
  growing entirely means the process stopped, not that the agent is thinking.
- `format: empty` vs `format: missing` — "started, nothing emitted yet" vs "never
  started, or `--log` was not passed". They demand opposite actions (wait vs
  re-dispatch); do not collapse them.

**Relay what you see.** Polling into your own context and staying silent leaves the
operator exactly as blind as before, which is the whole complaint this machinery exists
to answer. Between polls, surface one short line naming the agent, the elapsed time, and
the current step — e.g. `agy 5e-review · 4m · tool run_command (pytest -q)`. A live log
nobody reports is not observability.

**Do not poll on a timer when you only need the result.** A 30–60s poll cadence means
learning that a dispatch finished up to a minute after it did — which is pure added
latency, not observability. `exec` returns within ~1s of the agent producing its result
(measured: result at t+23.44s, `exec` returned at t+24.43s), so the delay is entirely in
how you wait. Instead:

- **Run the blocking form as a BACKGROUND command** (`exec-pane … --wait`, or
  `exec … &`) so the harness re-invokes you the moment it exits. That is a completion
  *signal*, not a poll, and it costs no context while waiting.
- **Poll `progress` only when you actually want the intermediate state** — to relay a
  status line, or to decide whether to keep waiting. Then one poll per 30–60s is right,
  and doing other work between polls is the point of backgrounding.

`--wait` itself polls the rc file at 0.5s, so it adds well under a second.

### Making a dispatch visible in Orca (zsh shell pane)

`progress` is for **you** (the orchestrator) — it costs context on every poll. When a
**human** wants to watch, run the dispatch in a real zsh pane inside Orca instead: the
pane renders in Orca's UI process, so it costs the orchestrator **zero** context and is
visible on mobile. The two are complementary; the pane is the cheaper channel whenever a
person is the audience.

This is NOT a return to the pane dispatch path. That path failed on **agent identity
resolution** (which pane holds agy vs codex — orca#9870), tui-idle false-idle, and TUI
scraping. A *shell* pane has none of those: the handle comes back from `terminal
split`/`terminal create` at creation, a shell command genuinely completes, and the verdict
still comes from `--out` — a file — not from a scrape. The pane is a **viewport**, never a
transport.

Use the **`exec-pane`** verb — do not hand-assemble this. It builds the in-pane
digest loop and the rc capture for you, which is what makes the three traps below
unreachable rather than merely documented.

```bash
# SAME SURFACE: split the pane you are in (uses ORCA_TERMINAL_HANDLE, set by Orca).
hmad-dispatch exec-pane agy <prompt> --cd <repo> --out <o> --log <l> --timeout 900 --split
# → returns immediately; stdout is the new pane's handle.

# OWN TAB (the default — no guessing which pane to split):
hmad-dispatch exec-pane agy <prompt> --cd <repo> --out <o> --title "5e-review agy"

# DROP-IN for `exec`: blocks until done, stdout = the response, rc = the dispatch's.
hmad-dispatch exec-pane agy <prompt> --cd <repo> --out <o> --wait --wait-timeout 1200
```

**Panes are pooled and reused.** By default `exec-pane` looks for an idle pane it
created earlier in the same worktree and dispatches into that one, so you end up with a
single h-mad pane per worktree rather than a new tab per dispatch piling up until you
close them by hand. Only panes this verb created are ever reused: each registers and
releases its own slot from inside itself, so a pooled pane is provably a shell and
provably idle. Foreign panes are never probed — proving one is an idle shell is not
possible from Orca metadata (there is no busy/idle field), and probing by sending text
would type into an agent's TUI if the guess were wrong. `--no-reuse` forces a fresh pane;
`--split`/`--new-tab` bypass the pool entirely. A pooled pane is registered under the handle
resolved by joining the create response's `paneKey` against `terminal list`, not the
`.result.terminal.handle` the response carries — that field has been observed to be a
pre-adoption placeholder (J1), and pooling one would hand the next dispatch a handle Orca
has never heard of. Unlike `launch`, a response with no `paneKey` is not fatal here: the
dispatch is already running by then, so it falls back to the response handle with a
warning (`HMAD_PANE_RESOLVE_TIMEOUT`, default 5s, bounds the join). Slot state lives in files under
`.h-mad/panes/` (override with `HMAD_PANE_SLOT_DIR`) rather than in the tab title,
because the shell rewrites the title via OSC on every prompt — a pane renamed to
`h-mad slot · idle` reads back as `~/orca/skills` the moment it reaches a prompt.

`--wait` still returns the moment the rc file lands, ~1-2s before the pane finishes its
last digest and releases the slot — the verdict must not wait on cosmetics. A dispatch
fired inside that gap used to create a second pane; it no longer does. A pane drops a
`.finishing` marker as soon as its dispatch completes, and a claim that finds nothing idle
waits (default 8s, `--reuse-wait`, or `HMAD_PANE_REUSE_WAIT_SEC`) **only** for a slot
carrying that marker. A busy slot without one is genuinely working, so it is never waited
on — which is what keeps Phase 5 parallel fanout from paying the wait on every dispatch.
The wait costs no verdict latency: it happens before the dispatch starts, not after it
ends. It also refreshes its view of which panes are live as it waits, so a pane that dies
mid-wait ends the wait instead of running it out, and its stale marker is reaped.

`--split` with no value means **this** terminal — the only unambiguous reading of "the
same surface". It refuses rather than guessing a pane from `terminal list`: guessing
reopens the identity-resolution problem this verb exists to avoid, and could drop a
shell into an *agent's* tab. Pass `--split <handle>` for a specific pane, `--new-tab` to
force a tab. Outside Orca the verb **refuses** instead of quietly running headless — a
silent fallback leaves you watching for a pane that never appears, with a success exit
code on top. Also: `--direction horizontal|vertical`, `--poll <sec>` (in-pane digest
interval, default 6), `--focus` (new tab only), and `--model/--timeout/--sandbox/--effort`
passed through to `exec`.

**Two output contracts, deliberately different.** Without `--wait`, stdout is the pane
handle — the useful value while the run is in flight. With `--wait`, stdout is the
response, matching `exec` so the verb is a drop-in. `--wait` blocks on the rc **file**
and clears any stale rc first: `--out` paths are templated per feature+module and the
`no_verdict` remedy re-dispatches to the same path, so a leftover rc would otherwise
hand back the *previous* run's exit code instantly.

Three findings, each measured live on 2026-08-19. `exec-pane` closes all three in code;
they are recorded here because anyone assembling a pane command by hand will hit them,
and because the verb's shape is otherwise hard to justify:

1. **A pane running `exec` bare is BLIND.** `exec` redirects the agent's stream into
   `--log`, so the pane shows only the echoed command line and then nothing until the run
   ends — the exact blindness this whole section exists to cure, relocated somewhere
   prettier. Measured: at t+14s the pane held one line while `--log` already had three
   events. **The pane must tail or digest the log itself**, which is why
   `exec-pane` always provisions a `--log` and always builds the digest loop. (`tail -f <l>` also works here and is the one place it is appropriate — a human
   pane, never an orchestrator tool call.)

2. **`orca terminal wait --for exit` does NOT carry the command's exit code.** A pane
   running `sleep 2; exit 9` reported `{"satisfied":true,"status":"exited","exitCode":0}`.
   Reading that as the dispatch rc turns **every failure into a success** — the same
   `$?`-shaped defect §"Audit-gate signal discipline" forbids elsewhere. Capture rc from
   the command itself (`echo $? > <o>.rc`, verified returning 3 and 7 correctly), or use
   `report-wait`, which polls a path plus a `.done` marker and is transport-agnostic. **For a backgrounded `exec`, poll its `--out` with `report-wait <out> --no-done-marker`** rather than a sleep ladder — waiting on one was written ~25 times in a single session as `for i in 1 2 3; do hmad-dispatch run --timeout 110 -- sleep 105; done` plus a `test -f`, whose purpose is invisible to the next reader and whose arithmetic, when wrong, wastes wall-clock silently. The flag is opt-in because the `.done` marker is what keeps a half-written report unreadable for every other caller, and it is only sound at all because `exec` writes `--out` **atomically** (temp + rename): a `cp` or a `>` redirect can put a partial — or, for a redirect, a zero-byte — file under a poller checking existence, and a truncated verdict reads exactly like a real one. Note the verb name: `await` is already taken by the Orca task-id wait and answers a different contract.
   `exec-pane` never calls `terminal wait` at all.

3. **`wait --for exit` is unusable here in both directions.** End the command with `exit`
   and the shell dies: `wait` satisfies, the code is still wrong, and the scrollback goes
   with it. Let it return to a prompt (what you want — the scrollback is the point) and
   `wait --for exit` **times out**, because the shell is still alive. Neither shape gives
   a completion signal, so do not build one on it.

The verdict path is untouched by any of this: `--out` still holds the response, `--log`
still holds the stream, and `h_mad_extract_verdict.py` still reads the file. Never scrape
the pane for a verdict.

### Dispatch channels and their guarantees

The verdict comes from `--out` (the `--output-last-message` file / captured response),
which only lands at completion — so `--out` is NOT tailable. `--log` is: it streams
the live transcript to `<file>` as it runs — plain text for codex, the NDJSON event
stream for agy — without disturbing the verdict on stdout or the exit code. Watch it
with `hmad-dispatch progress`, never `tail -f` (see §"Watching a headless dispatch").
`--log` appends on both backends, so a caller-supplied log retains its prior content.

**Give every dispatch its own `--out`.** It is last-writer-wins: two dispatches
sharing one path both exit `0` and the file keeps only the second answer, so a
lost verdict is indistinguishable from a dispatch that never ran (J29). As a
backstop `exec` refuses to overwrite an `--out` whose content changed
while it ran — the other dispatch's file is preserved, this one's answer still
reaches stdout and `--log`, a `REFUSING to overwrite --out` line goes to stderr,
and `rc` is untouched (it answers "did the CLI run", nothing else). A stale
`--out` left by *this* caller's own failed attempt is unchanged since start and
so is still overwritten — which is what keeps the `no_verdict` re-dispatch remedy
(`references/failure-recovery.md`) working against its templated path.

**`rc` and the token are different questions.** `rc` is operational (`0` = the CLI
completed, `124` = watchdog timeout, non-zero = crash/abort); it does **not** mean
the TDD task passed. Read the `STATUS:`/`VERDICT:` token exactly as the pane path
does (§"Reading a dispatch verdict") — exit 0 with `STATUS: BLOCKED` is still a halt,
and Codex GREEN still needs the anti-gaming verify. `rc` replaces the *idle poll*,
not the *verdict extraction*.

An `exec` with an empty primary channel returns **rc 3** when the agent exited 0;
the wrapper recovers the last `STATUS:`/`VERDICT:` line from the transcript when
present and reports the working-tree delta, so check the tree and verify the code
before treating the dispatch as complete. Exec dispatches use terminal/last-message
mode: leave the report-file slot empty. Report-file mode belongs to the pane path
(`send`/`report-wait`), not to `exec`.

**Exception — `exec agy` on an audit phase: fill the report-file slot.** That rule is
codex-shaped, where `--output-last-message` *is* the deliverable. On an audit the report
is the deliverable, and `agy --print` surfaces only the agent's **last** message, so the
report has exactly one fragile channel for the DELIVERABLE. (Since `exec agy` moved to
`--output-format stream-json` the `--log` stream does retain earlier turns' text, which is
a recovery route — see `references/failure-recovery.md`. It is not a second delivery
channel, so fill the report slot anyway.) Measured 2026-08-01,
`grounding-shadow-measurement` design cycle 2: 358 bytes of narration ("I have completed
the audit and output the results as requested") naming the two Must-fix items it had
actually found, with no `<AUDIT_SENTINEL>` pair — `h_mad_extract_report.py` exit 2. Cycle
1 of the same feature on the same config delivered a clean 2.9 KB sentinel report, so the
empty slot is not itself the defect — it is intermittent. **Two mechanisms fit the
evidence and this data cannot separate them:** either the report was emitted and a later
summarizing turn became the last message, or it was never emitted and the agent narrated
having done so — the latter is catalogued as **F-10 claim-execution divergence**
(`AGENTS.md`; agy's self-narrative diverging from actual execution, rule: never trust the
narrative, verify the artifact). Discriminating them needs the agy-side trace, and the
remedy is the same either way, so do not spend a cycle on it. Fill the path and block on
`report-wait "$RP"` — the verb polls a path
and a `.done` marker, so it is transport-agnostic and works behind `exec … &` just as it
does behind `send`. A file cannot be overwritten by a later turn.

**A missing report on the `exec` path — recover from `--log` and the working tree, never
from the pane.** The pane-path rule above ("A missing report is neither pass nor fail")
tells you to *read the pane*; on `exec` there is no pane, so that recovery does not
apply and the step used to have none. Measured 2026-07-30 on a real 5e GREEN: the
`exec codex` dispatch wrote **neither** its report file nor the `.done` marker, the
process was gone, and the wrapper's own captured stdout was empty — while the working
tree held **both** artifacts, complete and correct (a one-line production edit plus a
new test module). Read in the wrong order that is a `step5e:no_verdict` halt over
finished work; read as "DONE because the tree changed" it is an unverified pass.

Recover in this order:

1. **`--log`** — it survived when `--out` and the report file did not, and it holds the
   live transcript, including the diffs the agent applied. This is the strongest reason
   to pass `--log` on every `exec` dispatch: it is the one channel observed to outlive
   the others. It appends on both backends, so a caller-supplied log retains prior
   content. **This used to be pointless for `exec agy` and no longer is.** While agy ran
   in text mode the two channels were byte-identical (verified on both cycles of a real
   design audit — `diff` clean at 2.9 KB and at 358 B), so reading `--log` after a short
   agy exec was the same bytes twice. Under `--output-format stream-json` the log holds
   the whole event stream — every tool call, its arguments, its duration — while `--out`
   holds only the final response. So on an agy exec that came back short, `--log` now
   carries strictly more than `--out`: read it, and read it with
   `hmad-dispatch progress`, which digests the stream instead of dumping raw NDJSON.
2. **`git status` / `git diff`** — enumerate what actually landed. Artifacts present with
   no report means the work happened and the reporting channel failed, which is a
   different situation from a crash before any write.
3. **Verify from the code, not from a self-report.** Re-derive the verdict yourself: run
   the module's tests, run the acceptance test the task was gated on, and execute the
   mutations the task required. A missing report is in one respect an advantage — there
   are no claimed counts to anchor on, so the anti-gaming pass is forced rather than
   optional. In the measured case the work was correct **and** its required mutations had
   never been executed; the tests pinned them, but pinning is not the same as having run
   them.

Do **not** re-dispatch before step 2. A re-dispatch onto a tree that already carries the
work is how a second, conflicting implementation gets written over a correct one.

**All three steps are scoped to an implementer dispatch — do not apply them to `exec
agy`.** They exist because a codex RED/GREEN leaves artifacts in the working tree, which
is both the thing to recover from and the reason a blind re-dispatch is destructive. An
audit writes nothing to the tree, so steps 2–3 have no delta to enumerate and no code to
re-derive a verdict from. **Step 1 is the exception and it now carries real weight:** it
used to be the same bytes twice, but under `--output-format stream-json` an agy `--log`
holds the whole event stream, so it is worth reading on its own before anything else.
A short or sentinel-less agy exec is therefore a plain `<phase>:no_verdict` halt whose
documented route is the opposite of this one — read the stream with
`hmad-dispatch progress <log> --lines 50` first, and only if the report is genuinely
absent, re-read, then `hmad-dispatch clear agy` and re-dispatch (audits are idempotent,
so that is safe). Never score the narration: the 358 B
case named real findings and would have read as a substantive review to a human skimming
it, while carrying no schema the gate can count.

**Output loss is not agent-specific.** In the same session a backgrounded `pytest` run
also completed while its captured output came back empty, so treat "process gone, output
empty" as a transport symptom rather than evidence about the work. When a long run's
result matters to a gate, redirect it to a file you name yourself (`> /tmp/<run>.log 2>&1`)
instead of relying on the harness capture, and re-run rather than inferring the result.

**Default for a one-shot 5d/5e dispatch is `exec`.** A single self-contained RED/GREEN
or a single audit cycle has no prior-cycle conversation to preserve, and the exit code
is a hard completion signal — so `exec` sidesteps most of the pane failure class at once:
no tui-idle false-idle, no scrape, no identity resolution. Monitor it
by tailing `--log` (above); headless is not blind.

**Prompt echo is NOT one of the things `exec` sidesteps — it is handled, which is a
different claim.** `codex exec … -` echoes the piped prompt into its transcript, so the
`exec` *failure* path reads a log that contains your own prompt. This shipped a real
false verdict on 2026-08-03: a dispatch that died on revoked auth returned
`STATUS: NEEDS_CONTEXT` — the last option of the prompt's own contract block — and wrote
it to `--out`, where `h_mad_extract_verdict.py` accepted it. `exec` now appends the same
`===HMAD-DISPATCH-BOUNDARY===` that `send` does and recovers only from after its last
occurrence; for codex, a transcript with no boundary at all (a truncated echo) recovers
**nothing** rather than guessing. Two consequences for you:

- **A recovered verdict is still not a reported verdict.** Recovery reads a transcript,
  not the agent's final message. Treat it as a hint for triage, never as the gate input.
- **`tree delta: N changed in <dir>` is scoped to `--cd`** (it was whole-repo until the
  same date, so a stale file elsewhere read as "the work landed"). A zero delta plus no
  verdict is the honest signature of a dispatch that never ran — re-dispatch it.

**Switch to the pane path when** the running revision thread matters — cycles 2..N of
the *same* 5e ("here's the fix for your prior should-fix"), where `exec`'s fresh session
each call would re-send the whole context — or when a human wants to watch/intervene in
the Orca pane live. In short: **one-shot → `exec`; iterative revision loop → pane.**

Codex sandbox defaults to `workspace-write` (5d/5e write test + impl files); its
prompt is delivered on stdin, so the 8192-byte keystroke inline cap and the pane-path
size frontier both do not apply — but stdin is **not uncapped**: codex refuses any
prompt past **1,048,576 characters** with `input_too_large` before running a turn
(measured 2026-09-05 on two real gating prompts — the full-history design and
impl-plan audits — and re-measured the same day with a 1,111,089-char probe: rc=1,
an empty last message, one `Error: turn/start … "input_error_code":"input_too_large"`
transcript line). agy runs `--print --dangerously-skip-permissions` (headless must
auto-approve or a tool request blocks); its prompt is an arg, bounded by `ARG_MAX` —
the same 1,048,576 figure. Audit prompts run 16–90 KB (a large design audit
assembles to ~88 KB), and **266,342 B (260.1 KB) was confirmed answered 8 of 8 on
2026-08-22** (agy 1.1.18), every run honouring both the report-file slot and the
sentinel pair — so at the sizes audits reach, the `exec` path has no transport
limit, only the receiving model's context budget. Do not trim an audit for size when
dispatching via `exec`. When a prompt does run past the ceiling — a full-history
design or impl-plan inline can — `h_mad_assemble_audit.py` HALTs `oversize` and
writes nothing, and the **first remedy is `--vh-tail N`** (body verbatim, only the
last N Version History entries of each embedded document inlined; the rest stay
reachable via `git show <sha>:<doc>`), never a trimmed document. If a refused prompt
does reach codex, `hmad-dispatch exec` reports `INPUT_TOO_LARGE` with
`max_chars=`/`actual_chars=` on its own stderr line and skips verdict recovery and
the tree-delta read — it used to flatten the refusal into the generic `EMPTY final
message` and then print a `tree delta` the recovery protocol reads as "the work
landed". (The pane path is separately confirmed answered to 92,055 B — see
`references/agent-substrate.md` §"Prompt size".)

**After GREEN, run the built binary against the design's documented output shapes** — every verdict
line, every field-presence rule — rather than only running the suite. There is no fixed command,
only a fixed question: *does the running binary emit what the design says it emits?* On one task
this found **four of five defects that neither the 49-test suite nor an independent reviewer saw**:
a hardcoded `cycle=1` behind an undeclared `--cycle`, a float/int mismatch that crashed every real
wait behind ten stubbed tests, a checklist printed on a cannot-judge verdict, and a verdict line
that did not match its own AC. Stubs are what make this necessary — a suite can be green about a
binary that never runs.

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

- **6a-prime** — architectural review via agy (`references/agy-architectural-reviewer-prompt.md`). Inputs: Phase 5 diff (BASE = 5c sha; HEAD = 5g sha) + audited design. **Derive the 5c sha, never `git merge-base`.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_baseline_sha.py --branch <feature-branch> [--trunk main]`, reading the `BASELINE:` token, never `$?`. 5c is `git checkout -b …; commit impl-plan + audit files`, so the 5c commit is the branch's FIRST commit and `git merge-base main <branch>` returns the commit it forked FROM — off by exactly the impl-plan commit, and off plausibly, since both are real shas on the right branch. Measured (J41): merge-base `b5c8f41` against real 5c `730cc16`, 313 lines apart — the impl-plan and its three audits, which the wrong base feeds into the review as newly-added content when they are a separate INPUT to it. `UNVERIFIED` is a verdict, not an error: the branch's first commit does not touch an impl-plan, so something was committed before 5c and the rule does not hold — find the commit by hand, and note the token reports it as `candidate=` rather than `sha=` precisely so an unvouched value cannot be scraped as the answer. Only `OK` carries `sha=`.  Preflight with `command -v agy`; if the `agy` CLI is absent, halt `step6a-prime:no_reviewer_pane`. Then headlessly dispatch with `exec agy`; `exec agy` satisfies the gate and does not require a resolved pane. **Cite files in the prompt by ABSOLUTE path.** A correct `--cd` is not sufficient: the stream's `init.cwd` confirmed the repo root while agy resolved repo-relative citations against `~/.gemini/antigravity-cli/scratch/…`, every read failed, and the review proceeded on the inlined text alone. Say so in the prompt too — instruct the reviewer to return `ASSESSMENT: NO` if its reads fail, so a blind review declares itself instead of guessing. This is the only pass positioned to catch design-level problems — design-vs-spec drift, an exception hierarchy that does not scale, or a gate at the wrong altitude — which document audits and code-level gap analysis miss by construction. Read the `ASSESSMENT:` with `h_mad_extract_verdict.py`, never by grepping, because an empty review must not be indistinguishable from `READY_TO_MERGE`; **and then prove the review actually read something before you record a pass** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_review_evidence.py <the dispatch's --log>`, reading the `EVIDENCE:` token, never `$?`. `PASS` means at least one tool call reached `DONE`. `NONE` means the reviewer judged without reading anything → halt `step6a-prime:review_read_nothing`; do not record the `ASSESSMENT:`, fix the prompt and re-dispatch. `UNREADABLE` (exit 2) is a cannot-judge carrying no counts — no `--log` was passed or it is empty — and is not a verdict about the review. **This is the same rule as the sentence before it, one level up.** `extract_verdict` closes the case where the agent says *nothing*; this closes the case where it says something *fluent* with nothing beneath it, which is harder to spot because it reads like a review. Measured: a 6a-prime dispatch whose single `view_file` errored returned `ASSESSMENT: READY_TO_MERGE` in 1510 confident bytes, and rc, the extractor and the Phase-7 gate all took it. Note the gate counts **any** tool reaching `DONE` and knows no tool names — the first probe of this defect hardcoded `view_file|grep_search` from an earlier dispatch and reported a false zero when agy switched to `run_command`. It also does **not** gate on `result.status`, because `hmad-dispatch` ignores that field for a sound reason (a single denied tool call yields `status: ERROR` beside a complete answer), so gating on it here would re-create the false `no_verdict` halt that reasoning prevents; halt `step6a-prime:architectural_review_failed` on `WITH_FIXES` or `NO`, and `step6a-prime:no_verdict` if none can be extracted after a re-read and re-dispatch. Immediately after extraction, write the extracted `ASSESSMENT:` into `orchestrator_state[<feature>].archreview` using `h_mad_state_write.py`, then read `orchestrator_state[<feature>].archreview` back and compare it to the value written. Capture the value line-scoped with `sed -n 's/^ASSESSMENT: //p'` rather than stripping the prefix off whatever came back. `h_mad_extract_verdict.py` now prints its `[H-MAD]` marker to **stderr**, so its stdout is only the verdict line and a bare `$(...)` capture is safe (J26, fixed) — but stay line-scoped anyway: the extractor is the one script whose stdout is a *value* rather than a report, and a line-scoped capture cannot be broken by anything a future version adds to stdout. Strict-only validation is not sufficient because `archreview` is not in the schema's `required` array: `STATE: PASS` can hide a dropped write. If no reviewer exists at all, the reviewer-less route records `SKIPPED_OPERATOR_OVERRIDE` as a deliberate operator decision and surfaces it as a warning in the Phase-7 report; `SKIPPED_OPERATOR_OVERRIDE` is not a pass. A pane that did not resolve is handled by headless dispatch, not that ordinary skip route. For this readback check, explicitly do not rely on h_mad_state_validate.py --strict-only.
- **6a** — run inline gap analysis. Parse match rate from `docs/03-analysis/<feature>.analysis.md`.
- **6b** — if < 90%, run inline iterate (5-cycle cap). Loop until ≥90% AND 100% test pass.

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

**You do not author a phase document in your own loaded context.** Phases 2, 3, 4 and 5a each
dispatch a fresh-context teammate that owns exactly one file:

| Phase | Document | Agent | Definition |
|---|---|---|---|
| 2 | `docs/01-plan/features/<feature>.spec.md` | `spec-author` | `agents/spec-author.md` |
| 3 | `docs/01-plan/features/<feature>.plan.md` | `plan-author` | `agents/plan-author.md` |
| 4 | `docs/02-design/features/<feature>.design.md` | `design-author` | `agents/design-author.md` |
| 5a | `docs/01-plan/features/<feature>.impl-plan.md` | `implplan-author` | `agents/implplan-author.md` |

```
Agent(subagent_type: "plan-author", prompt: "<feature>; documents: <spec> <design> <current plan>;
      audit reports for the cycle being answered: <paths>; orchestrator decisions: <none | list>")
```

The same routing applies to a **revision**, not only a first draft. A cycle's must-fixes go to the
author that owns the document they land in; you relay findings and decisions, you do not apply
them yourself. The sites that revise are Phase 3's audit loop, Phase 4's (which inherits it), 5b's, and the
wire-pin gate's `UNSHAPED` remedy — all four re-dispatch, none of them regenerate in your context.
Phase 6b edits production files and the analysis document, never a phase document, and the
rejections ledger writes a sidecar and forbids editing the gated document, so those are not
revision sites.

**The spec has no audit phase of its own**, and that is not an oversight to correct here:
`h_mad_assemble_audit.py` binds `--phase` to `plan|design|impl-plan` as argparse `choices`, so a
spec audit cannot be assembled or collected. The spec is nonetheless revised — by findings raised
against the other three that land in it, which is how it moved v1.52 → v1.55 in one session — and
**those revisions route to `spec-author` like any other**. A spec edited by the orchestrator
because "it was only one number" is the exact path by which a value gets swept in one surface and
not another.

**Why.** The orchestrator writing a fix is the same context that wrote the defect, and it sweeps
the value it is *thinking about* rather than the value that exists. Measured on one feature:
83 design cycles, 74 plan cycles, 34 impl-plan cycles without meeting an exit gate, and roughly
**half** of all must-fixes were introduced by the previous cycle's fix. In one session six defects
in the orchestrator's own work were caught by fresh contexts and **none** by the orchestrator
re-reading its own document. Each agent file states the failure class each of its rules closes;
they are contracts, not style guides.

**Author dispatch rules the ORCHESTRATOR owns.** Measured 2026-09-05 (r17): the design author
read a 3,500-line document whole more than once, called `advisor()` — which forwards its entire
transcript a second time — and died of context overflow (`failed: Prompt is too long`)
mid-verification. The orchestrator then spawned a successor **without ruling ownership**; the
original resumed from its transcript and kept writing, and two authors held one file for ~8
minutes, colliding only because the successor asserted-before-write and stood down. Four rules
follow, none of which an agent file can enforce for you:

1. **A `failed: Prompt is too long` notification is recoverable, not death.** The author can
   resume from its transcript. Before concluding it is gone, read the working file's mtime and its
   newest `- v1.N` Version History line and compare with the last DONE you have.
2. **Rule ownership explicitly before spawning a successor.** Say in the successor's prompt which
   author owns the file now, and require it to assert the file has not moved (mtime, newest
   `- v1.N` line) before every write and to stand down if it has.
3. **Authors never call `advisor()` and read in slices** — those rules live in every
   `agents/*-author.md`; do not undo them from the dispatch prompt ("read the whole design" is an
   instruction to overflow).
4. **Collect on the `DONE` line, not on the notification.** Every author's final message puts its
   `<ROLE>: DONE …` line FIRST (four r17 reports were truncated before a trailing DONE); a report
   file or a bumped Version History is the deliverable, and a DONE message that arrives ~45 minutes
   after the marker is benign.

### Delta self-review — review the FIX before you re-dispatch the audit

An author has just changed a document to answer findings. Review **what changed**, not the
document again, before assembling the next audit prompt.

The reason is a number this repository keeps re-measuring on itself. In the last gating round on
`doc-block-exec`, **two of the three must-fixes were introduced by the previous cycle's own
repairs** — that document's own version history records it, and says the delta was the first place
looked *because* of it. Across a whole session roughly half of all must-fixes were fix-introduced,
and the gateway-consolidation Phase-4 record (durable session memory, not this tree — so cite it as recalled rather than as citable here) has four consecutive cycles where the fix produced the next defect. A cycle spent
finding a defect the last cycle created is a cycle spent twice.

Two passes, cheapest first:

```bash
# 1. Mechanical — the greppable half, already covered by the precheck.
python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py \
  <document> --phase <phase> --root <PROJECT_ROOT>

# 2. What changed, and whether it answers what it claims to.
git diff <the commit the last cycle was audited at>..HEAD -- <document>
```

Then dispatch the diff, not the document:

```
Agent(subagent_type: "doc-auditor", prompt:
  "PROMPT=<none — a delta review has no assembled prompt; your subject is below>
   PROJECT_ROOT=<root>  REPORT=<path>  This pass is ADVISORY.
   Subject: the diff below / `git show <sha> -- <document>`, and the findings it answers: <paths>.
   For each hunk: does it close the finding it claims, or only the instance the reviewer named?
   Did it break a claim elsewhere in this document or in a sibling — a count, a cross-reference,
   a value stated in more than one place?")
```

`doc-auditor` rule 7 already carries the cross-document check, so **do not write a new agent for
this**. What is new is only the scoping: a diff and the findings it answers, rather than a whole
document.

**It is ADVISORY and it is not a gate.** Its findings go back to the owning author as an ordinary
revision. A delta review that blocked would just be another cycle, which is the cost it exists to
avoid.

### The four rules that are the ORCHESTRATOR's, not the author's

An author cannot enforce any of these, because each one is a property of the round rather than of
a document:

1. **File scoping is the whole mechanism — one author, one document, and an author that finds
   another document owes something REPORTS it.** Nothing is silently harmonised across documents.
   That is what keeps parallel authoring tractable, and it is what creates duty 3.

2. **Freeze the tree for the duration of a round.** Unlike a codex leg, which reads a frozen
   assembled prompt, a teammate reads the **working tree**. Measured: a `SKILL.md` commit landed
   mid-round and all three auditors returned line numbers correct for what they read and
   mislabelled against the base commit they were given (`:1897` reported "at `e8eaf6f`", which is
   `:1887`) — and the orchestrator then relayed the wrong number onward. Commit before the round
   or after it, never during.

3. **Cross-check any acceptance criterion two concurrent authors touched.** Running authors in
   parallel produces contradictions neither can see. Measured: `design-author` added a
   dot-directory exclusion to AC-6.1 (25 files) while `implplan-author` independently repaired the
   same AC's rebase (30 files). Both measurements were correct and answered different questions. It
   surfaced only because the two reports were read against each other. This duty has no other home.

4. **A teammate's view of its sibling documents goes stale mid-round.** An author that read the
   spec before your revision of it landed will report "nothing is owed to the spec" and
   "contradictions: none" in good faith, and be wrong. Re-state what moved, or re-dispatch, rather
   than believing a sibling-document claim made against a version you have since replaced.

### Precheck before you dispatch — never spend a cycle on a greppable premise

Before `h_mad_assemble_audit.py` for **any** phase audit (3, 4, 5b), run the document
through the precheck — and on a revision cycle run §"Delta self-review" first, which
covers this and the half a grep cannot reach. A dual-surface cycle costs two dispatches and roughly four minutes
of wall clock to discover a claim a `grep` refutes in a second, and then a second cycle
to fix it:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py \
  <document> --phase plan|design|impl-plan|spec --root <PROJECT_ROOT>
```

Read the `PRECHECK:` token, never `$?` — it exits 0 on both verdicts, and 2 only when the
document cannot be read. `PRECHECK: FAIL` → **re-dispatch the owning author with the detail
lines and do not assemble the prompt.** `PRECHECK: UNREADABLE` is a cannot-judge, not a pass.

**Read the advisories too, even on a PASS.** They are the larger half and they are advisory
because no rule can decide them, not because they are unimportant: a `PATH:` or `SYMBOL:`
line is either a file the feature creates or a citation that has gone stale, and only you
know which. `--allow <substring>` records a deliberate hit; it is an INPUT and is never
inferred.

**What is hard is only what is provably wrong** — an unfilled slot, a pin past end-of-file,
a pin into a file that changed since the document's own provenance commit, a provenance sha
that names no commit here. That split was measured, not chosen: every detector filed as hard
on first cut fired dozens of times on the design and plan that had just passed 83 and 74
audit cycles — 104 `PATH:` hits, then 49 `LINEPIN:`, then 48 `PLACEHOLDER:` — and each time
the hits were correct usage rather than defects. **A gate that fails a clean document is not
a gate**, and finding that out costs one test run here against a full cycle in the loop.

### Why the ack match is not fuzzy

Softening the `## Acknowledged-not-fixed` match stops at canonicalisation plus an explicit
operator `[key]`. No text-similarity rule is applied, and that is measured rather than timid.

On the real 7-bullet sidecar of HemaSuite's `gateway-consolidation.plan.audit.v18` — which
accreted seven bullets over about three underlying findings — token overlap scores the **negative
control above both true pairs**:

| pair | what it is | jaccard |
|---|---|---|
| 1 ~ 4 | the same finding, re-worded | 0.089 |
| 2 ~ 5 | the same finding, re-worded | 0.158 |
| **6 ~ 7** | **two genuinely different AC-1.4 process-group leaks** | **0.180** |

The ordering is inverted, so every threshold that pairs the re-worded duplicates collapses the two
distinct leaks *first* — and a collapsed ack silently clears a real finding, which is strictly
worse than the re-acknowledging cost it was meant to save. Same shape as the refused evidence check
(#27): the rule that would help does not discriminate, and the rule that discriminates is vacuous.
**The `[key]` tag is the escape**, because it is stated by the operator rather than inferred.

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

**Which two surfaces — routed by whether codex can run.** Codex available: `codex` + `agy`. Codex
unavailable (§"Teammate audit leg"): `doc-auditor` teammate + `agy`, with the teammate holding
codex's leg and **gating**. Never two passes of one surface, and never the teammate leg *plus*
codex on the same phase at the same cycle — that is three reports, of which two share a model
family, and the union stops meaning what the rule below says it means.

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

**`HALT` is not `DENY`, deliberately.** `hooks/h-mad-advisor-warn.sh` speaks on the glob
`*"CTXBUDGET: DENY"*`. Had a run-ceiling breach reused that word, no existing consumer could tell an
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

**When authoring a source-level assertion, assert the call form, not an occurrence count over a whole method.** A count over a method policing one call site over-constrains it and recruits the implementer into damaging unrelated code; assert the specific call/argument shape at the one site the contract concerns.

**Re-verify every impl-plan pin against the tree at dispatch time.** Every line number, site count, and "live defect" claim must be confirmed against the current tree before it is passed to an implementer — a stale pin produces a wrong edit or a fabricated failure (measured on `feature/193`: `:1583`→`:1575`, "three log sites"→two, "live defect"→already-citable).

**Substrate preflight (once per H-MAD run — at Phase 5 start, or the first audit dispatch if earlier; skip if the substrate was already recorded this run).** Run `hmad-dispatch env`.
If it exits non-zero → halt `<phase>:no_substrate`. Record the printed substrate +
agent mapping into state so the run log states which environment it dispatched under:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature "<feature>" \
  --set substrate='{"name":"orca","agents":{"codex":"term_…","agy":"term_…"}}'
```

State is the carrier and `h_mad_telemetry.py record` is the reporter — it copies the
field onto the Phase-7 row it already builds from this record. Writing it here is what
makes the step executable at Phase-5 time; `record` is a close-out call and cannot
serve a Phase-5-start instruction. This is the explicit environment check (cmux vs orca) — do it
before any `send`/`read`. See `references/agent-substrate.md`.

For each audit (Phase 3, 4, 5b), run one complete cycle with the verb:

```bash
hmad-dispatch audit-cycle --feature <feature> --phase plan|design|impl-plan \
  --cycle <N> --passes <K> --project-root <PROJECT_ROOT>
```

`audit-cycle` runs exactly one cycle: assemble, dispatch, collect, gate, and print one
`AUDITCYCLE:` verdict. It is not the revision loop; re-auditing until
`must=0 should=0` remains the orchestrator's job. For the codex second surface
used by the exec leg, see §"Second surface — the codex leg".

**Read the `Effort:` block before you trust a clean cycle.** The verb hands each pass's
NDJSON log to the combiner, which reports `tools=/ok=/failed=/thinking=` per pass and marks
`low-evidence` when a pass made at most the 2 successful calls the report-file contract
itself costs — the report write and the `.done` marker — so it cannot have read anything.
Measured across the 8 passes of cycles 21–24 on `grounding-evidence-coverage`: *every*
substantive finding came from a pass with high thinking or ~34 tool calls, while cycle 21
pass A made **0** tool calls and returned "CLEAN PASS" on a plan the other pass proved
defective, and cycle 24 double-cleaned with thinking collapsed to 6.2 k / 4.4 k and exactly
the 2 delivery calls each. At the `AUDITCYCLE:` line those are indistinguishable from real
clean passes.

It is a **scoring caveat, not a gate**, and deliberately so: a pass with 2 tool calls
honoured the contract exactly as asked, and one such pass in this repo (5,356 thinking,
2 calls) still returned a real finding. Treat `low-evidence` on a clean pass as a reason to
re-dispatch that pass, never as a verdict. `combine()` cannot see the block, and a log that
was named but could not be read renders `unreadable` rather than zeros — `tools=0` is
exactly what a genuinely hollow pass looks like, so zeros from an unread file would
manufacture the finding.

**Check the working tree after every audit dispatch, and treat any delta as a finding.** An audit
reads; it does not write. `git status --short` before and after a cycle should be identical, and a
difference is not a bonus fix — it is the reviewer having edited what it was measuring, which
destroys the evidence the next cycle depends on. Revert it (preserve the diff first, so a real
finding buried in it is not lost) and re-read the report knowing its author mutated the tree.
Measured 2026-08-28: a 5b audit changed three tracked files, one of them a test unrelated to the
feature, made green by stubbing out the call it existed to exercise — and its report described that
as restoring a green suite while asserting a cause the edit could not have affected. The prompt now
forbids this (`audit-prompt.template.md` §READ-ONLY), so the check is a backstop rather than the
guard, but a prompt rule is advice and the tree is fact.

For each audit pass, the verb **assembles with the script** — it performs steps 1
through 7.2 below deterministically and refuses to emit a prompt that fails the preflight:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py \
  --feature <feature> --phase plan|design|impl-plan --cycle <N> \
  --project-root <PROJECT_ROOT> \
  --report-file "$RP"          # Orca only; omit for the sentinel scrape
```

It prints `ASSEMBLE: PASS <path> <size> sentinel=<s> size_status=verified|unverified` or
`ASSEMBLE: HALT <phase>:preflight` with the
reasons, **exiting 0 either way** (a rejected prompt is a verdict, not a tool failure —
see the base invariant on audit-gate signal discipline). A halted prompt is deliberately
not written, so it cannot be dispatched by mistake. A non-zero exit means unreadable
inputs. On `HALT`, fix the template or invariants file and re-run; never hand-patch the
staged prompt.

**Assert `ASSEMBLE: PASS` before dispatching the assembled prompt** — the same mandated
read as the Phase-5 `PREFLIGHT:` assertion, for the same reason: the script exits 0 on
both verdicts, so `$?` cannot tell you which one you got, and an unread token is worth no
more than the unread `STALE` line it is modelled on.

**Read `size_status=` on the same line, not just the token.** `verified` means the prompt
is no larger than the biggest one confirmed answered (92,055 B — see
`references/agent-substrate.md`). `size_status=unverified` still dispatches, because
prompts that size have answered; what it changes is *diagnosis*. If the reply comes back
empty, **suspect size before re-dispatching** — first re-read the full buffer, since a
tail-grep reports SILENT for replies the TUI merely reflowed, and only then apply step 5.5.

The field is on the verdict line deliberately. It used to be a separate `!` warning beside
`ASSEMBLE: PASS`, which an orchestrator following this contract exactly never had to read —
the same defect the `PREFLIGHT:` token exists to fix, one signal over. Note the verdict
token stays exactly `PASS`/`HALT`: a `PASS_OVERSIZE` variant would still match every
`grep "ASSEMBLE: PASS"` consumer and would have reproduced the defect rather than fixed it.

Every defect this area has had came from doing the steps by hand: the rubrics were
inlined twice, `{Design only — cross-doc:}` reached the reviewer in 69 of 69 dispatched
prompts, and a hand-written duplication grep hardcoded a project-authored heading. None
of them raised an error. Use the script.

The steps below are what it implements — read them when debugging a `HALT`, or when
assembling by hand because the script is unavailable:

1. Start from `~/.claude/skills/h-mad/audit-prompt.template.md`, **dropping the leading orchestrator note** — every line from `<!-- ORCHESTRATOR-NOTE:START` through `ORCHESTRATOR-NOTE:END -->` inclusive. That block is assembly instructions to you, not reviewer content; left in, the prompt opens by telling the reviewer it is reading a template.
1.5. **Resolve the `{{ONLY:…}}` applicability markers** for this audit's type (`plan`,
   `design`, or `impl-plan`). A marker is an assembly directive and must never reach the
   reviewer. If the audience list contains this audit's type → delete the marker, keep the
   content. Otherwise → delete the marker **and the content it governs**. Inline form
   (`{{ONLY:design}} <content>`, possibly after a `- ` bullet) governs the rest of that line
   plus any following lines indented deeper than it; block form (marker alone on its line)
   governs down to the matching `{{END-ONLY}}`, both marker lines included.

   **Delete the whole line — never blank the slot and keep its label.** `Paired audited
   plan:` followed by nothing tells the reviewer a document is *missing*, not that it was
   inapplicable, and a design audit reading "the plan wasn't provided" discounts the
   cross-doc check it was supposed to perform.
2. Replace `<INLINE_TARGET_DOC>` with full text of the target doc (plan.md, design.md, or impl-plan.md).
3. Replace `<INLINE_BASE_INVARIANTS>` with full text of `~/.claude/skills/h-mad/invariants.base.md` (workflow-universal Axis B — always inlined, base before project, regardless of whether a project file exists).
4. Replace `<INLINE_PROJECT_INVARIANTS>` with full text of `<PROJECT_ROOT>/.h-mad/invariants.md` (domain Axis B). If the project file is absent/empty, leave the slot empty — the base layer still applies.
5. For design audits only: replace `<INLINE_PAIRED_PLAN>` with audited plan.md.
5.5. For plan and design audits: replace `<INLINE_PAIRED_SPEC>` with full text of `docs/01-plan/features/<feature>.spec.md` — the Axis C source of truth. Without it the reviewer has no AC list to reconcile against and Axis C degrades to prose review, which is the failure it exists to prevent: the paired plan carries only incidental AC references, not the enumeration. For impl-plan audits leave the slot empty; that audit contracts against the design.

   **Prompt size.** Axis C makes an already-large prompt larger: measured on a real feature, design 45 KB + plan 21 KB + spec 16 KB assembled to 88 KB (72 KB without the spec). Whether that is a problem depends on the transport. On the **`exec` path** it is not at these sizes — 266,342 B was confirmed answered 8 of 8 on 2026-08-22 (agy 1.1.18, both transports honoured every time), so dispatch the whole thing. The one `exec` ceiling is **1,048,576 characters** on both agents (codex refuses past it with `input_too_large`; agy's arg is bounded by `ARG_MAX` at the same figure), and a full-history design or impl-plan inline CAN reach it (measured 2026-09-05): the assembler then HALTs `oversize` and writes no prompt, and the **first remedy is `--vh-tail N`** — keep every body byte, inline only the last N Version History entries of each embedded document — never a trimmed document. On the **pane path** the confirmed-answered frontier is ~92 KB via file indirection (a 92,055 B prompt was answered by a live agy pane on 2026-07-30, falsifying the earlier ~61 KB ceiling); the old "49 KB normal / 53 KB silent" figure was a delivery-mode artifact (a paste, not file indirection) and never reproduced (see `references/agent-substrate.md`). A real audit assembles to at most ~88 KB, so it sits inside the confirmed pane frontier — but if a pane prompt ever does run past ~92 KB, two things follow. First, **do not solve it by trimming the design** — showing the reviewer only its AC-bearing sections is self-defeating, since `absent` becomes undetectable and `absent` is the failure Axis C exists to catch. Inlining the spec's `## Functional Requirements` section alone rather than the whole spec is a legitimate saving (~7 KB) and loses no AC; switching that dispatch to `exec` lifts the ceiling to the 1,048,576-character one above. Second, an over-long prompt is a **safe** failure: `h_mad_extract_report.py` exits 2 on a missing or empty sentinel pair, so the cycle halts instead of scoring silence as a clean gate.

   **Before treating a silent reply as a size failure, read the whole buffer.** `hmad-dispatch read <agent> --from-start`, not a tail — the TUI reflows a reply across redraw frames, and a tail-grep for a sentinel reports SILENT for prompts that answered (measured; see `references/agent-substrate.md`). Most "size failures" are this.

   **If it really is size, "split by FR group" usually will not help.** Only the spec divides; everything else is carried by every split. Measured on a real design audit totalling 50.9 KB:

   | term | size | divides on an FR split? |
   |---|---|---|
   | design | 22.4 KB | no |
   | plan | 10.3 KB | no |
   | audit template | 8.0 KB | no |
   | base + project invariants | 5.5 KB | no |
   | spec (FR-only trim) | 4.7 KB | **yes** |

   46.2 KB of 50.9 KB is fixed, so a two-way split yields ~48.5 KB per half — about 2 KB of relief for two dispatches, two audit files and two gate runs. The remedy silently assumes the *spec* is the marginal term; whenever the design dominates, which is the normal case for a detailed design, it does not work.

   The options that do work, in order:
   1. **Inline only the spec's `## Functional Requirements`** — ~7 KB, loses no AC. Already the default.
   2. **Shorten the design itself** — tighten prose and remove restated plan content. Note the constraint above: do *not* do this by showing the reviewer only AC-bearing sections.
   3. **Split the feature**, not the audit. Fewer FRs per feature shrinks the design, plan *and* spec together — it is the only division that touches the fixed terms.
   4. **Trim the rubric** as a last resort, remembering `invariants.base.md` is inlined into every audit prompt, so a rule added there is paid for by all of them.
6. For impl-plan audits only: replace `<INLINE_PAIRED_DESIGN>` with audited design.md.
6.5. Replace `<AUDIT_SENTINEL>` with `AUDIT-<feature>-<phase>-v<N>` — the per-cycle stem step 9 extracts on. It must be unique per cycle; reusing a previous cycle's stem reopens the stale-scrollback trap it exists to close.
6.6. **Report-file transport (preferred under Orca).** If `hmad-dispatch env` reports `substrate: orca`, replace `<REPORT_FILE_PATH>` with an absolute staged path `RP=/tmp/audit_<feature>_<phase>_cycle<N>.report.md` (and `rm -f "$RP" "$RP.done"` first); the agent will write its report there and mark `$RP.done`. Otherwise (cmux / unpinned) leave `<REPORT_FILE_PATH>` empty and rely on the sentinel scrape. Measured on `audit-cycle-verb`: across the 18 impl-plan audit passes, 17 delivered via the report file (file present, non-empty, `.done` written); 1 did not — cycle 7 pass 1 wrote neither the report file nor the marker, and its report was recovered from `--out`. The verb therefore always arms the `--out` fallback. **Arming it was not the same as it working**: until #16 the fallback passed `--after-marker` unconditionally, which requires the dispatch boundary that only the PANE transport writes, so on every `exec` `--out` file extraction exited 2 and the fallback silently yielded nothing. Measured: a codex pass wrote a **0-byte report file plus its `.done` marker** while `--out` held the complete report, and collection answered `COLLECT: MISSING delivered=none`. The flag is now passed only when the boundary is actually present. See `references/orchestration-mode.md` §"Report-file transport".
7. Stage: `cat > /tmp/audit_<feature>_<phase>_cycle<N>.txt`.
7.2. **Residual-placeholder preflight — mandatory, before any `send`.** Substitution is a
   literal string replace over the whole file, so it is silent in both failure directions: a
   slot you forgot stays in the prompt as a raw token, and a bracketed slot *mention* in prose
   gets replaced too, splicing a second copy of a rubric into the middle of a sentence. Neither
   raises an error; both reach the reviewer. Check:
   ```bash
   P=/tmp/audit_<feature>_<phase>_cycle<N>.txt
   grep -n '<INLINE_\|<AUDIT_SENTINEL>\|<REPORT_FILE_PATH>' "$P" && \
     echo "HALT <phase>:unfilled_slot" || echo "slots OK"
   grep -n '{{' "$P" && \
     echo "HALT <phase>:unresolved_conditional" || echo "conditionals OK"
   # Duplication check — each rubric must appear exactly once. Derive the needle from
   # each inlined file's own first line: the PROJECT invariants heading is written by
   # the project (HemaSuite's reads "# HPW Project Axis B Invariants"), so a hardcoded
   # heading reports a false 0 in every repo but the one it was written against.
   # Do NOT anchor to '^': a stray copy spliced into a blockquote is prefixed '> # …',
   # so an anchored grep reports a clean 1 while the prompt carries 2.
   BASE_MD=~/.claude/skills/h-mad/invariants.base.md
   PROJ_MD=<PROJECT_ROOT>/.h-mad/invariants.md
   grep -Fc "$(head -1 "$BASE_MD")" "$P"                          # must be 1
   [ -s "$PROJ_MD" ] && grep -Fc "$(head -1 "$PROJ_MD")" "$P"     # must be 1 when a project file exists
   ```
   Any hit on either grep, or a count > 1 on either rubric → halt (`<phase>:unfilled_slot` /
   `<phase>:unresolved_conditional`),
   fix the template/invariants file, re-assemble. Do **not** dispatch a prompt that still shows
   a raw `<INLINE_…>`: the reviewer reads it as an unfilled template and silently discounts the
   axis it belongs to, which scores as a clean gate on a rubric that was never delivered.

   This is a live failure, not a hypothetical: `<INLINE_BASE_INVARIANTS>` and
   `<INLINE_PROJECT_INVARIANTS>` were once written **bracketed** inside the template's own
   header blockquote and inside `invariants.base.md`'s header, so every assembled prompt carried
   both rubrics twice (measured: 2 copies of each in every `/tmp/audit_*.txt` on this machine —
   ~4–6 KB of dead bloat against the ~49–53 KB reviewer cliff in step 5.5) and still displayed a
   raw `<INLINE_BASE_INVARIANTS>` token. **Prose refers to a slot by bare name
   (`INLINE_BASE_INVARIANTS`); only a real slot is bracketed.** Keep it that way in any new
   template or invariants file.
7.5. **On cycle 1 of each audit phase (and after confirming agy is alive via `hmad-dispatch alive agy`), clear agy's context** (see §"Agent-pane context hygiene") so a prior feature's/phase's transcript can't drift the verdict or pollute the scrollback you later grep. Later cycles of the SAME audit reuse the warm context (the running revision thread is wanted).
8. Dispatch:
   ```bash
   hmad-dispatch send agy /tmp/audit_<feature>_<phase>_cycle<N>.txt
   ```
   `send` chooses its own delivery mode by size: it inlines below
   `HMAD_SEND_INLINE_MAX` (default 8192 bytes) and otherwise tells the agent to
   read the staged file by absolute path. Audit prompts run 16–90 KB, so they
   take the indirection path — no need to hand-roll it.
9. Capture the report. **Under Orca (report-file transport), skip the scrape entirely** — the agent wrote a clean file, so read it directly and jump to the gate:
   ```bash
   hmad-dispatch report-wait "$RP" --timeout 600 \
     > docs/01-plan/features/<feature>.<phase>.audit.v<N>.md
   ```
   The gate refuses a path named like a transport file (`audit_*.report.md`) — gate the docs path, never `$RP`.
   This has no sentinel-extraction step (the file is already the report), no `wait`, and no dedent/`•`-normalize (the file is clean markdown, not a TUI render). On timeout, the agent did not honour the contract — fall back to the scrape path below.

   **Never gate an audit on the dispatch's `result.status`.** The report file and its `.done` marker are the delivery contract; `status` is not. ANY failed or refused tool call yields `status: ERROR` beside a complete, correct answer, and the cause is usually incidental to the audit — measured three times with three unrelated causes: a refused `.tmp` write (`grounding-evidence-coverage` impl-plan cycle 22 pass B, on a report carrying two independently-verified real findings), a `find_by_name` timeout plus a `view_file` on a nonexistent path (2026-08-24, 31 tool calls / 29 ok, schema-correct report), and a `write_to_file` rejected for a missing argument that the agent immediately retried successfully (2026-08-24). This is the same rule `h_mad_review_evidence.py` follows for 6a-prime (step 6a-prime above): report `result.status`, never gate on it. Read the file and the marker.

   **Scrape fallback (cmux / unpinned, or when `report-wait` times out) — never hand a raw scrape to the gate.** The scrape holds live scrollback, so the previous cycle's report is usually still above the prompt; extracting on the first `## Summary` scores the wrong cycle:
   ```bash
   hmad-dispatch read agy --lines 200 > /tmp/scrape_<feature>_<phase>_cycle<N>.txt
   python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_report.py \
     /tmp/scrape_<feature>_<phase>_cycle<N>.txt \
     --feature <feature> --phase <phase> --cycle <N> \
     > docs/01-plan/features/<feature>.<phase>.audit.v<N>.md
   ```
   The extractor takes the **last** complete `<AUDIT_SENTINEL>-BEGIN`/`-END` pair, so neither an older cycle nor a retry within this one can win. It exits 2 and writes nothing when the pair is missing or its body is empty — that is the "dispatched, went idle, produced nothing" case, and it must halt the cycle rather than be scored. On exit 2: re-read with `--from-start` (a larger tail does not escape an overdrawn frame region — J3), and if the report genuinely never arrived, `hmad-dispatch clear agy` and re-dispatch.
10. Design audits write to `docs/02-design/features/` instead; adjust the redirect above.
11. Run the gate — the verdict unit counts bullets in BOTH `## Must-fix` AND `## Should-fix` (excluding the bare-`None` sentinel, a stray `- None`, and any `## Acknowledged-not-fixed` items in the same file or a sidecar `.audit.v<N+1>.md` passed via `--ack-file`):
    ```bash
    python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py <audit-file>
    ```
    The gate **prints a verdict token and always exits 0** on a verdict (a non-zero exit is reserved for operational errors such as a missing file — never for a FAIL, so the gate never registers as a tool failure). Parse the **token**, not `$?`:
    - `GATE: PASS must=0 should=0` → gate passes (must-fix=0 AND should-fix=0). Proceed.
    - `GATE: FAIL must=N should=M` (N or M > 0) → gate fails. Surface the bullets, revise, re-audit.
      "Revise" is where §"Close the class, never the instance" applies: before writing the fix,
      decide whether each bullet is a singleton or one member of an open-ended set, and for a set
      write the rule **and** the exactly-stated residual. Fixing the member the reviewer named is
      what turns one defect into a seven-cycle series.

    **Pass `--gated <doc>` for every document the audit judged, and read the stamp back before relying on the PASS.** The gate reads the *audit file* and never the document the audit was about, so a PASS survives every later edit to the thing it passed — including the edits that fix the previous cycle. Measured: a design that gated clean twice produced 9 findings on the next cycle, and 4 of them were created by the fixes for the cycle before. `--gated` is repeatable and a cycle that gates a design **and** an impl-plan must name both; a stamp is written only on PASS (a stamp over a FAIL would let the readback report `CURRENT` for a verdict that blocked), and a gated file that cannot be read yields `GATE: UNSTAMPABLE` and writes nothing rather than recording a verdict over content the gate never saw. Then:
    ```bash
    python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py <audit-file> --verify-stamp
    ```
    Read the `GATESTAMP:` token — deliberately **not** `GATE:`, so a consumer globbing the verdict line cannot conflate the two. `CURRENT` → the PASS is still about what is on disk. `STALE` → it is not; the changed files are named, and the edits since are themselves ungated — halt `audit_gate:verdict_stale` and re-audit. `UNSTAMPED` (exit 2) is a **cannot-judge**, never `CURRENT`: nothing was recorded, so nothing was compared, and it is the same class of lie as an empty scrape reading as "no findings".
    When you revise, bump the doc's `## Version History` with the helper, never with a hand-rolled
    anchored substitution:
    ```bash
    python3 ~/.claude/skills/h-mad/scripts/h_mad_version_history.py <doc> \
      --version v1.<N> --text "Audit v<N> fixes from <audit-file> — <summary>."
    ```
    **A cycle whose findings were all rejected has nothing to bump — do not bump it.** The Version
    History records *fixes*; a rejection goes to `<feature>.<phase>.rejections.md`
    (§"Record a rejected finding in the rejections ledger, never in a gated document"). Bumping
    here for a rejection edits a gated file, which resets the both-clean streak and costs a second
    cycle for a finding that was not real in the first place.
    Read the `VERSION-HISTORY:` token, not `$?` alone. This step runs once per cycle per doc, so it
    is the most-repeated edit in the loop and the one that fails most quietly: a `.replace()` whose
    anchor has drifted writes nothing and reports success, and appending at the end of a
    newest-first section puts the entry in the wrong place with no observable error. The helper
    refuses both, plus a re-run of the same version and the table-shaped sections it must not
    reformat. A `REFUSED` is a real stop — fix the doc or the arguments; never fall back to editing
    the section by hand, which is the failure this replaces.
    The gate emits a `[H-MAD] <feature> gate <verdict>` marker line. Nits never block. If the `GATE:` token is absent from stdout (unexpected), treat it as an operational error and halt `step<N>:gate_token_missing` with a `[H-MAD]` marker — never silently treat a missing token as PASS.

**Between revising and re-auditing, sweep the corrected VALUE.** After applying an audit fix,
`grep` the corrected value — not the section, the value — across every live doc in the feature. The
same claim is usually restated in two or three places and the fix lands in one. Roughly two-thirds
of one session's 79 findings were this single class, and four stale copies survived **two
independent reviewers**: a spec FR's description contradicting its own AC, a plan risk row still
asserting a disproven `exec` behaviour, a design cross-reference to a deleted plan clause, and an AC
counter that went stale twice. A sweep has five surfaces — prose, code blocks, comments, ACs, and
the PAIRED design — and numeral forms count. Closing a class in only one document of a pair
RELOCATES it rather than fixing it.

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
RP=/tmp/audit_<feature>_<phase>_cycle<N>_codex.report.md
rm -f "$RP" "$RP.done"
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py \
  --feature <feature> --phase plan|design|impl-plan --cycle <N> \
  --project-root <PROJECT_ROOT> \
  --report-file "$RP" \
  --out /tmp/audit_<feature>_<phase>_cycle<N>_codex.txt
```

Dispatch it through the exec path so the codex process reads the assembled
prompt directly and writes the contracted report file:

```bash
hmad-dispatch exec codex /tmp/audit_<feature>_<phase>_cycle<N>_codex.txt \
  --cd <PROJECT_ROOT> \
  --out /tmp/audit_<feature>_<phase>_cycle<N>_codex.out.txt \
  --log /tmp/audit_<feature>_<phase>_cycle<N>_codex.log --timeout 1800
```

After `exec codex` returns, collect the surface report into the docs audit path
before running any gate:

```bash
COLLECT_OUT=$(hmad-dispatch collect-report --surface codex \
  --feature <feature> --phase <phase> --cycle <N> \
  --report "$RP" --out /tmp/audit_<feature>_<phase>_cycle<N>_codex.out.txt \
  --project-root <PROJECT_ROOT>)
printf '%s\n' "$COLLECT_OUT"
```

Read the `COLLECT:` token. Anything except `COLLECT: OK` is a delivery failure:
halt `<phase>:report_not_collected` and print `[H-MAD] <feature> <phase> halted reason=report_not_collected`.
Only the path printed on the `COLLECT: OK` line is gateable; the transport file
is never the audit document.

```bash
if ! printf '%s\n' "$COLLECT_OUT" | grep -q '^COLLECT: OK '; then
  printf '%s\n' '[H-MAD] <feature> <phase> halted reason=report_not_collected'
else
  DOCS=$(printf '%s\n' "$COLLECT_OUT" | sed -n 's/^COLLECT: OK path=\(.*\) delivered=.*/\1/p')
  python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py "$DOCS"
fi
```

## Teammate audit leg — when codex is unavailable

When the codex leg above cannot run, a fresh-context `doc-auditor` teammate takes its place in the
union and **gates**. This is the audit-side twin of the Phase-5 authoring fallback, and it keys off
the **same declaration** — there is no second switch to set or to forget:

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
RP=/tmp/audit_<feature>_<phase>_cycle<N>_teammate.report.md
rm -f "$RP" "$RP.done"
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py \
  --feature <feature> --phase plan|design|impl-plan --cycle <N> \
  --project-root <PROJECT_ROOT> \
  --report-file "$RP" \
  --out /tmp/audit_<feature>_<phase>_cycle<N>_teammate.txt
```

Dispatch the teammate against the assembled prompt **by path**, never by pasting it — it is large,
and a pasted copy is a second version of the prompt that no gate can trace:

```
Agent(subagent_type: "doc-auditor", prompt:
  "PROMPT=/tmp/audit_<feature>_<phase>_cycle<N>_teammate.txt
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
  --report "$RP" --out /tmp/audit_<feature>_<phase>_cycle<N>_teammate.out.txt \
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
- **It does not license Claude to write Phase 5 production code — but the declaration you just
  made does, and that is one switch with two effects.** This section covers phase *documents*. The
  TDD gate hook (`hooks/h-mad-tdd-gate.sh`) reads the **same** `codex_status` for whichever feature
  is in `step5`, and 5b *is* inside `step5` — 5a writes that phase before the audit loop starts. So
  a declaration made to route a 5b document audit is live for 5d/5e production authoring on the
  same feature. The two conditions do not normally diverge (a codex exhausted for auditing is
  exhausted for authoring), which is why this is a note rather than a hazard. **Flip it back to
  `available` before 5d if codex has returned**, or the fallback silently outlives the outage it
  was declared for.

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

## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)

- `h_mad_extract_verdict.py` — read the last `STATUS:`/`VERDICT:`/`ASSESSMENT:` line off a scrape, validated against its contract; exit 2 (printing nothing) when absent, empty, or off-contract, so silence can never read as approval
- `h_mad_extract_report.py` — pull the reviewer's report out of a pane scrape on the last `AUDIT-<feature>-<phase>-v<N>-BEGIN`/`-END` pair; exit 2 (writing nothing) when the pair is missing or empty
- `h_mad_collect_report.py` — collect-report surface collector: copies a delivered report-file or `--out` fallback into the docs audit path (the fallback reads a pane scrape past the dispatch boundary and an `exec` `--out` file from its end — see §6.6; conflating the two made it dead for `exec`), prints `COLLECT: OK|MISSING|CONFLICT` plus the collected path/delivery source, and performs readback before reporting success. `OK`/`MISSING`/`CONFLICT` exit 0 because they are measured outcomes; operational errors and readback failures exit 2. `--force` overwrites an existing collected report after a conflict.
- `h_mad_offcontract_scan.py` — **where did the report actually go?** Locates an audit artifact written off-contract: `scan()` + CLI printing `OFFCONTRACT: NONE|FOUND|UNREADABLE`, exit 0 on `NONE` **and on `FOUND`** / 2 on `UNREADABLE reason=no_workspace`. `FOUND` exits 0 deliberately — this reports, it never decides. Reach for it when `h_mad_extract_report.py` exits 2: that exit is *correct* (silence must never score as a clean gate), but its remedy — `clear` and re-dispatch — is wrong when the audit already ran, and on a large prompt you pay a full cycle to reproduce a drop. **The defect it addresses is unfindability, not absence.** `exec agy` can honour neither the `--report-file` slot nor the sentinel pair while still doing the work and writing a real report at a path of its own choosing; two were observed eleven days apart — a workspace **dotfile** (`.design.audit.v14.md`, invisible to the `*audit.v14*` glob the orchestrator searches, which is exactly how one cycle concluded "no file was written" and re-dispatched over completed work) and `audit_report.md` in agy's own scratch directory while the run narrated "the current workspace". It therefore assumes **no** `audit.vN` stem — the whole failure is that the agent chose the name — and searches dotfiles too; `--cd <workspace>` plus agy's scratch dir by default, `--extra-dir` to widen, `--minutes`/`--since` to bound by mtime, `--expected` to exclude the path that was contracted for. **Its output does not feed the gate.** A report recovered this way has had NO schema enforcement applied, so it prints candidates with an explicit not-validated caution for a human to transcribe by hand, falsifying every premise against the source first; teaching `h_mad_extract_report.py` to glob these paths would score an unvalidated file as a clean gate, which is the opposite of the fix. `NONE` means nothing matched the search, **not** that the work was never done — it narrows a re-dispatch decision rather than making one. Closes J30. Stdlib-only.
- `h_mad_audit_cycle.py` — audit-cycle verdict combiner: collects each pass from report-file transport or the always-armed `--out` fallback, gates delivered reports, and prints `AUDITCYCLE: PASS|FAIL|UNVERIFIED` + `[H-MAD]` marker, exit 0 on a verdict / 4 on operational error. `PASS` means all delivered passes gate cleanly; `FAIL` carries findings; `UNVERIFIED` means a pass produced no report, no gateable sections, a non-zero dispatch rc, or — since #13 — too little evidence to certify anything. `--pass` takes an optional 5th field, `i:<report>:<out>:<rc>[:<log>]`; when a log is given the render carries an **`Effort:`** block — per pass `tools=/ok=/failed=/thinking=`, and `low-evidence` when `ok` is at or below the 2 successful calls the report-file contract itself costs, i.e. the pass cannot have read anything (J49). **Since #13 it decides, in ONE direction only**: a pass at or below the floor can no longer certify a clean (`UNVERIFIED reason=low_evidence:pN`), and a named-but-unreadable log fails closed as `low_evidence_unmeasurable:pN` — a distinct token because the remedy differs, find the log versus re-dispatch the pass. It still cannot manufacture a `FAIL`; it is checked AFTER the findings loop, so findings a hollow pass did write still count, and after the rc loop, so a timeout explains itself rather than being reported as hollowness. A pass with **no log named** is NOT scored as hollow — that is the ordinary shape of a codex leg and of every `Agent()` teammate pass, and absence of measurement is not measurement of absence. The counts still never appear inside the `AUDITCYCLE:` token, only as the `reason=` field, and the `Effort:` block now renders on `UNVERIFIED` too, because those counts are the evidence FOR the verdict. **This reverses the rule that stood until 2026-09-04** ("it reports; it never decides"), by operator decision on measured evidence: the second surface was hollow in 21 of 22 passes on one feature, and on another produced 6 fabricated must-fixes of 11 against codex's 0 of 25, while its low-evidence passes never found anything in either direction. Honouring the delivery contract is not evidence of having read the tree. A named-but-unreadable log still renders as `unreadable` rather than as zeros — `tools=0` is exactly what a genuinely hollow pass looks like.
- `h_mad_precheck_doc.py` — phase-document pre-dispatch precheck (§"Precheck before you dispatch"): `scan()` + CLI printing `PRECHECK: PASS|FAIL issues=N|UNREADABLE`, exit 0 on a verdict / 2 on operational error. Refutes before the prompt is assembled what a cycle would otherwise spend two dispatches discovering. **Hard** findings are only the provably-wrong ones — `PLACEHOLDER` (an unfilled `key=…` or bare `<slot>`, impl-plan only, plus `TBD`/`TODO`/`FIXME` anywhere), `LINEPIN` past end-of-file, `PINDRIFT` (a pin into a file that changed since the document's own newest provenance commit — the c33 defect exactly, six `SKILL.md` pins stale by 93 lines), and `UNKNOWNSHA` (a provenance sha naming no commit here). **Advisory, verdict-neutral**: `PATH` and `SYMBOL` (a planning document names files and symbols the feature will CREATE), `STALESHA` (behind-HEAD is the normal condition of every written measurement), ordinary `LINEPIN`, and `COUNT`. Every one of those started as a hard finding and was demoted by measurement, not by taste: they fired 104, 49 and 48 times on the design and plan that had just passed 83 and 74 audit cycles, and the hits were correct usage. `--allow` is an input, never inferred. The residual it cannot close: a document that NARRATES a stale pin quotes the stale number, and no detector distinguishes that from the defect. Stdlib-only.
- `h_mad_audit_gate.py` — audit-gate verdict unit (single source of truth): `classify()` + CLI printing `GATE: PASS|FAIL` + `[H-MAD]` marker, exit 0 on verdict / 2 on operational error; `--must-only` for the `/h-mad do` precondition. Imported by `h_mad_do_preconditions.py` Since #15 an `## Acknowledged-not-fixed` bullet matches a finding through canonicalisation (emphasis, backticks, wrapping, case, trailing punctuation) or an explicit leading `[key]`; **never through text similarity** — see §"Why the ack match is not fuzzy" for the measurement that refused it.
- `h_mad_install_check.py` — verifies the install shape of this checkout's skills (the two symlinks §"First-run auto-bootstrap" depends on, plus every sibling skill the checkout ships): `check()` / `check_siblings()` + CLI printing `INSTALL: PASS|FAIL issues=N|UNREADABLE` followed by `SKILL_NOT_SYMLINK:`/`SKILL_NOT_INSTALLED:`/`SKILL_DANGLING:`/`SKILL_NOT_A_CHECKOUT:`/`HOOK_NOT_INSTALLED:`/`HOOK_DANGLING:`/`SPLIT_INSTALL:`/`SIBLING_NOT_SYMLINK:`/`SIBLING_DANGLING:`/`SIBLING_WRONG_CHECKOUT:` detail lines, exit 0 on a verdict / 2 only when no path was given. Read the token, never `$?`. Reads paths and repairs nothing — relinking `~/.claude` is an operator action.
- `h_mad_resume_decision.py` — smart-resume decision
- `h_mad_do_preconditions.py` — `/h-mad do` prereq verifier (uses `h_mad_audit_gate.classify` **and `has_gate_sections`**): `check()` + CLI printing `PRECONDITION: PASS|FAIL issues=N|UNREADABLE` followed by `MISSING:`/`INVALID:`/`DIRTY:` detail lines, exit 0 on a verdict / 2 only when `--repo-root` cannot be read. Read the token, never `$?`. **`INVALID:` is not `DIRTY:`** — it means the report carried no `## Must-fix`/`## Should-fix` sections at all, so it was refused rather than scored; there are no findings to go and fix, the report needs re-obtaining. This caller used to reach past `has_gate_sections` straight into `classify()`, so a heading-less report scored `must_count=0` and **cleared** the Phase-5 gate while the audit-gate CLI returned `GATE: INVALID` on the same file (#39). Route the check through the shared guard — re-deriving it is how the two drifted apart.
- `h_mad_assemble_tdd.py` — Phase-5d/5e Codex dispatch assembler: `assemble()` / `task_body()` + CLI printing `ASSEMBLE-TDD: PASS <promptfile> <bytes>B phase=<red|green> task=<id> shape=<s>` followed by the verbatim command block (backgrounded `exec codex` with `--model`/`--effort`/`--out`/`--log`/`--timeout` → `progress` → `h_mad_extract_verdict.py --key STATUS` → an INDEPENDENT scoped pytest), exit 0 on PASS / 2 on `ASSEMBLE-TDD: HALT <reason>`. It stages the prompt and prints the commands; **it does not dispatch** — the dispatch/poll/wait loop is §"Exit-code dispatch for 5d/5e", and a driver that dispatches either blocks blind for the timeout or re-implements `progress`. Cuts §"Task N" out of the impl-plan using the wire-pin gate's own `_TASK_RE`/`_parse_tasks` rather than a second parser (#39), and stamps the phase into the task section because the template carries BOTH the RED and the GREEN instructions and nothing in it says which applies. Halt reasons: `task_not_found`, `impl_plan_unreadable`, `template_unreadable`, `residual_slots`, `no_wire_pin`, `counts_required`, `interpreter_has_no_pytest`, `sandbox_read_only`, `prompt_unwritable`. The defaults exist because hand-assembly produced five distinct mistakes, each an invocation default rather than a judgement: a model pinned in the assembler at all — it outranks the codex CLI's own `$CODEX_HOME/config.toml`, so the model the TUI shows and the model 5d/5e runs drift apart; `--model`/`--effort` are OVERRIDES, emitted only when given (effort reaches codex as `-c model_reasoning_effort=<e>`), and the escape hatch they provide is real because a configured `gpt-5.6-luna` cannot execute tools and fails as a well-formed `STATUS: BLOCKED`; a bare `python3` (3.14 here, no pytest) — so the chosen interpreter is PROBED for pytest and a failure names a working one; the prompt passed inline when `exec` takes a FILE PATH; `--sandbox read-only` on a run that executes pytest, which kills pytest's tempdir so the pass measures nothing — refused; and an unscoped pytest that collects the sibling project, so `--test-path` is required and the prompt tells the agent not to widen it. **What it refuses to guess is the judgement:** a 5d without `--expect-fail`/`--expect-pass` is `counts_required`, never defaulted, because "guard changed" and "test weakened" are otherwise indistinguishable. A `wiring` task needs no counts — the RED split is identical either way — but its `WIRE`/`WIRE-PIN` are carried automatically and a missing pin is `no_wire_pin`. Stdlib-only.
- `h_mad_derive_test_path.sh` — production-path → test-path mapper
- `h_mad_pane_janitor.py` — post-probe pane cleanup: `snapshot` / `plan` / `clean` + CLI printing `JANITOR: PLANNED|CLEANED|NOTHING|SNAPSHOT candidates=N settled=J closed=K skipped=S` or `JANITOR: REFUSED reason=<r>`, exit 0 on a verdict / 2 on a refusal. **Dry run unless `--apply`.** Refusal reasons: `cannot_identify_self`, `baseline_unreadable`, `baseline_malformed`, `too_many_candidates`, `orca_unavailable`, `orca_unparseable`, `orca_error`. The hard part is not closing panes, it is deciding which panes are the probe's: `worker-start` panes inherit the worktree name as their title, so they are indistinguishable from the operator's own agent pane, and each of the seven hand-runs re-typed the keep-list from memory. So take a `snapshot --worktree <path> --out <f>` BEFORE the probe and the keep-list is recorded rather than remembered; a candidate is then a pane in that worktree, absent from the baseline, and not the caller's own — the caller's handle is re-read live from `orca terminal show` (which with no `--terminal` returns the caller's pane) and the run REFUSES rather than proceeding when it cannot identify itself. **It settles before it closes**: an unsettled dispatch wedges its terminal permanently (`worker-abandon`/`worker-stop` both answer `dispatch_not_found` — upstream stablyai/orca#13005), so each candidate is looked up in `orchestration worker-list` (used rather than `task-list`, which needs a bound Run) and an unsettled one gets `task-update --status completed` first; a settle that FAILS leaves the pane open and says so, because a wedged terminal you can still see beats one you cannot. Every close carries an explicit `--terminal` — the CLI takes it optionally and a bare `terminal close` closes the CALLER'S pane. **Absence from the baseline is subtraction, and subtraction alone cannot tell the probe's panes from the operator's** — so a candidate is closed only when a `worker-list` row positively identifies it. One with no worker row is reported as `unidentified` and LEFT ALONE unless `--include-unidentified` is passed; an operator who opens a pane in the worktree after the snapshot (to tail a log while the probe runs) produces exactly that shape, and neither of the older guards saw it — `--max` only bounds how many get closed, and the self-handle protects the one shell the janitor runs in, not the operator's other tabs. Unidentified panes are always named, never silently skipped. `--max` (default 10) refuses a candidate set large enough to mean the baseline is wrong. A dry run reports `would_settle=`/`would_close=` rather than `settled=`/`closed=`, because a `PLANNED` line carrying `closed=1` reads as a pane that was closed. Live-verified 2026-08-25 on a real install: a freshly created pane came back with the title `~/orca/skills`, **byte-identical to a pre-existing pane in the same worktree** — the row's "indistinguishable by title" claim, confirmed, and the reason the baseline exists at all. Stdlib-only.
- `h_mad_new_gate.py` — verdict-token gate scaffold: `scaffold()` + CLI printing `SCAFFOLD: WROTE name=<slug> token=<TOKEN> files=3` or `SCAFFOLD: REFUSED reason=<r>`, exit 0 on a write / 2 on a refusal. Refusal reasons: `bad_slug`, `bad_token`, `token_taken`, `would_overwrite`. Emits three files — `scripts/h_mad_<slug>.py`, `tests/test_h_mad_<slug>.py`, `tests/mutation-specs/<slug>.json` — and prints the registry line to paste here. **Counted 2026-08-25 from the scripts themselves: 20 distinct verdict tokens, 18 of them sharing one contract.** The code was never what cost time; three invariants were, and this emits them by construction with the tests that pin them: (1) a cannot-judge carries **no counts**, because a zero is byte-identical to "nothing was measured" and reads as clean — the shape that let a heading-less report score `must_count=0` and CLEAR the Phase-5 gate (#39); (2) **exit 0 on any verdict**, since a FAIL is a successful measurement and non-zero is reserved for operational failure, which is what lets a caller read the token rather than `$?`; (3) the docs table is **pinned bidirectionally** — every detail line the script can print has a remedy row here and vice versa. The generated suite is deliberately RED until the registry line is pasted, because the doc step is the one most easily skipped. The emitted mutation spec is ALL_CAUGHT out of the box; if it ever is not, the scaffold is shipping the appearance of coverage. Stdlib-only.
- `h_mad_emit_marker.sh` — `[H-MAD]` marker writer
- `h_mad_state_schema.json` — JSON Schema (Draft-07) for `orchestrator_state` (v2.2, strict tier). Validated by `jsonschema` when importable, otherwise by the stdlib validator bundled in `h_mad_state_validate.py`, so the state scripts run on a stock `python3` with no third-party packages (J4). The two are held to identical verdicts by a differential test.
- `h_mad_state_schema_historical.json` — permissive tier for pre-v2.2 records
- `h_mad_phase7_preconditions.py` — Phase 7 gate: `check()` + CLI printing `PHASE7: READY|BLOCKED`, exit 0 on verdict / 2 on operational error. Enforces 6-before-7 by reading state and the gap analysis.
- `h_mad_state_staleness.py` — compares state against git and reports disagreement (`STALENESS: CLEAN|SUSPECT`); catches a record that is well-formed and no longer true.
- `h_mad_state_write.py` — the orchestrator_state write path: `create_feature()` / `set_fields()` / `drop_undeclared()` + CLI printing `STATE-WRITE: OK`, exit 0 on success / 2 on refusal. Validates the record against the strict schema before writing, replaces the file atomically, and serialises concurrent writers on a lock sidecar. A refusal names the undeclared keys and distinguishes the ones this write introduced from the ones already on the record; `--drop-undeclared` is the sanctioned repair for the latter, which would otherwise leave the record unwritable — including by `--release` (J48). Use this instead of hand-editing state.
- `h_mad_version_history.py` — the phase-doc `## Version History` bump: `bump()` / `plan_insertion()` + CLI printing `VERSION-HISTORY: OK|DRY-RUN path=<p> version=<v> line=<n> placement=<append|prepend>`, exit 0 on a completed write / 2 on refusal. Refusals print `VERSION-HISTORY: REFUSED path=<p> reason=<r>` carrying **no `line=`**, and an unreadable path prints a bare `VERSION-HISTORY: UNREADABLE` — a cannot-write must never read as a write that landed. Reasons: `anchor_missing`, `anchor_ambiguous`, `table_shape`, `unknown_shape`, `mixed_order`, `duplicate_version`, `bad_version`, `empty_text`, `multiline_text`, `splice_not_additive`, `unreadable`. **Use this instead of a hand-rolled anchored substitution** — the value is the assert, not the append: a `.replace()` whose anchor has drifted writes nothing and reports success, so a skipped bump and a completed bump are indistinguishable from the caller's side. Placement is derived from the section, never assumed: measured over 713 real sections, 191 of the 246 multi-entry ones are ascending, 29 descending and 26 unsorted, so a blind append-at-end is wrong for 22% of them and silently so. Tables (140 of 713) are refused rather than reformatted, the unsorted case is refused rather than guessed, and every write self-checks that its own splice was insertion-only. Stdlib-only.
- `h_mad_state_validate.py` — two-tier state validator: `classify()` + CLI printing `STATE: PASS|FAIL` + `[H-MAD]` marker, exit 0 on verdict / 2 on operational error; `--strict-only` enforces v2.2 on a record you just wrote
- `h_mad_telemetry.py` — Phase 7 cycle count recorder + summary. Also copies `substrate` from the feature's state record onto the run row (written at Phase-5 start — see §"Phase 5 (Implementation) sub-steps"); the row carries an explicit `null` when it was never recorded, so an unrecorded run is distinguishable from a pre-field one.
- `h_mad_mutation_harness.py` — Phase-5e mutation harness: `run_spec()` + CLI printing `MUTATION: ALL_CAUGHT|SURVIVED|REFUSED|BASELINE_NOT_GREEN|RESTORE_FAILED|UNREADABLE mutations=N caught=K survived=J refused=R` or `MUTATION: PRECHECK_FAILED specs=N drifted=K unreadable=J` + `[H-MAD]` marker, exit 0 on a verdict (`ALL_CAUGHT`/`SURVIVED`) / 2 on anything that measured nothing, including `MUTATION: PRECHECK_FAILED`. With `--check-anchors`, prints `ANCHORS: <verdict> specs=N mutations=M ok=K drifted=J unreadable=U skipped=S unclassifiable=C` for `ANCHORS_OK`/`ANCHORS_DRIFTED`/`ANCHORS_UNREADABLE`, or `ANCHORS: ANCHORS_NOTHING_SWEPT specs=0 skipped=K unclassifiable=J`; `ANCHORS_OK` exits 0, while `ANCHORS_DRIFTED`, `ANCHORS_UNREADABLE` and `ANCHORS_NOTHING_SWEPT` exit 2 because no usable mutation verdict was measured. **`skipped=` and `unclassifiable=` ride EVERY summary line, not only `ANCHORS_NOTHING_SWEPT`**: both were always counted, and a consumer that renders only the summary could not otherwise tell a sweep that set files aside from one that did not. **A file that is not valid JSON at all (`unclassifiable`) is a finding, not a skip** — it takes the `ANCHORS_UNREADABLE` verdict and exits 2. It rides that existing word rather than a new one because the consuming pre-push hook scores verdicts with an ordered substring `case` whose default arm ALLOWS the push, so a new verdict word would be silently non-blocking there until every consumer was updated in lockstep. `skipped` (`not-a-spec`: valid JSON declaring no `mutations`) stays non-fatal and is the category that earns “not every file beside a spec is a spec”; that rationale never covered a file that will not parse. Takes a JSON spec naming the suite command and each mutation as an exact `find`/`replace`. Refuses any anchor not matching exactly once — the "`.replace()` that matches nothing reports the guard as enforced" failure in `invariants.base.md` §"Mutation verification" — restores the tree on every path including SIGINT/SIGTERM, verifies the restore by re-reading, and re-runs the suite afterwards to prove it. Before the baseline command, the mutation run sweeps sibling specs in the same directory and refuses on sibling drift with `MUTATION: PRECHECK_FAILED`; the precheck summary carries `specs=`/`drifted=`/`unreadable=` counts and exits 2 because no mutation was measured. A mutation may add `"test": "<nodeid>"` (with a spec-level `"target_command"` argv prefix), which changes the question from **did the suite go red** to **did THAT test bite** — the discrimination `ALL_CAUGHT` structurally cannot express, since a mutant that dies on a crash, a timeout or an unrelated assertion is otherwise byte-identical to the guard biting. A named test that PASSES while the suite goes red is a **survivor**, and the detail line names what actually bit; the named test is also required green before the mutation is applied, because a kill credited against an already-failing pin measures nothing and the whole-suite baseline cannot see one red pin. Caught and survived mutations both print a `mechanism:` detail line naming the killer, and a refused anchor prints `hint:` lines — near misses with line numbers when it matched 0 times, the match locations when it matched more than once — because the REFUSED verdict was always right and the recovery was a manual re-grep. Relative spec `root` values resolve against the spec file's directory, not the caller's cwd, so committed specs remain portable across checkouts and correct from git worktrees. **The mutation-count summary line is unchanged**; everything new on measured mutation verdicts is an additional detail line. It also purges cached bytecode around every run: CPython invalidates a `.pyc` on (source mtime, size), a mutation is frequently byte-size-IDENTICAL, and it lands inside the same filesystem-mtime second as the previous run — so both invalidation inputs match, the stale bytecode is reused, the mutant never executes and the run reports `survived` while the file on disk is genuinely mutated (measured 4 false survivors in 6 trials before the fix). Reporting only: whether the mechanism that fired is the mechanism the spec claims stays with the author. Stdlib-only.
- `h_mad_archreview_cycle.py` — ONE Phase-6a-prime cycle, staged and scored: `stage` substitutes the reviewer template and prints the exact `exec agy` command, `score` runs the gates in the order that is the contract — **evidence FIRST, then verdict, then record, then READ BACK**. Prints `ARCHREVIEW: STAGED prompt=… base=… head=… bytes=N` or `ARCHREVIEW: READY_TO_MERGE|WITH_FIXES|NO tools=N recorded=yes` (exit 0), and `NO_EVIDENCE`/`NO_VERDICT`/`NOT_RECORDED`/`UNSUBSTITUTED`/`DEGENERATE_RANGE`/`UNREADABLE` (exit 2). The seven mechanical steps of 6a-prime were hand-assembled **7 times in one session**, and the two with no other home are the two that get skipped: the BASE/HEAD stamp (a stale sha silently reviews the PREVIOUS commit — J41 one level up, which is why `DEGENERATE_RANGE` refuses `BASE == HEAD`) and the evidence gate (a dispatch whose single `view_file` errored returned `READY_TO_MERGE` in 1510 confident bytes, and rc, the extractor and the Phase-7 gate all took it). **`NO_EVIDENCE` and `NO_VERDICT` record NOTHING and carry no verdict word** — a review that read nothing has no verdict whatever its last line says, and recording it is what made that defect survivable. `NOT_RECORDED` exists because `archreview` is not in the schema's `required` array, so strict validation passes over a dropped write and the read-back is the only check. **One cycle per invocation: it does not decide whether to run another**, because that run went to seven when cycle 3 came back clean and cycle 4 then found a Critical vacuous pass. Deliberately NOT a variant of `audit-cycle`, which is a multi-pass verdict COMBINER over already-finished runs and rejects any phase outside plan/design/impl-plan — same word, different machine. Stdlib-only.
- `h_mad_baseline_sha.py` — the Phase-5c baseline sha, derived and self-checked: `derive()` + CLI printing `BASELINE: OK sha=<40-hex> branch=<b> trunk=<t>`, `BASELINE: UNVERIFIED reason=no_impl_plan candidate=<sha>`, or `BASELINE: NONE reason=no_commits_on_branch` — exit 0 on a verdict — and `BASELINE: UNREADABLE reason=<r>` (exit 2) when nothing could be derived. **Only `OK` carries `sha=`**; `UNVERIFIED` reports the unvouched value as `candidate=` instead, so a caller scraping `sha=` cannot receive a value nothing stands behind — the defect this script exists for was a wrong sha that looked exactly like a right one. 6a-prime and 5f both consume a 5c sha and nothing produced it, so it was produced by hand as `git merge-base main <branch>`, which returns 5c's PARENT (J41). Derived rather than stored in state for two reasons that both cut the same way: a stored sha does not survive a rebase, and a stored sha cannot tell you it is wrong — whereas "the branch's first commit is 5c" is a protocol invariant with an observable consequence (that commit touches an impl-plan), so a violated assumption surfaces as `UNVERIFIED` instead of a confident wrong answer. Stdlib-only.
- `h_mad_wire_pin_gate.py` — Phase-5b wire-pin gate: `check()` + CLI printing `WIREPIN: PASS|FAIL|UNSHAPED tasks=N wiring=M unpinned=K mislabeled=J` (or a bare `WIREPIN: UNREADABLE`, counts omitted because nothing was parsed) + `[H-MAD]` marker, exit 0 on a verdict / 2 on `UNSHAPED` or an unreadable plan. Refuses a `wiring`-shaped task whose `WIRE`/`WIRE-PIN` is absent, still a template placeholder, or filler — and, in the other direction, a task carrying a real `WIRE`/`WIRE-PIN` under a non-`wiring` shape, which is how a pinned wiring task is demoted to a PASS by editing one word. Stdlib-only.
- `h_mad_response_probe.py` — measure a response SHAPE over N calls with cleanup as the design rather than an afterthought. Takes create/close/list commands as argv templates, so it is not welded to one verb and is testable without a runtime; reports `PROBE: field=<f> present=K/N absent=J/N` and `CLEANUP: closed=K failed=J possible_leaks=P`. Every attempt is journalled to disk BEFORE the create and completed after it, cleanup runs from `finally` and from installed SIGINT/SIGTERM handlers, and `--resume <journal>` closes what an earlier run could not — a `trap` covers none of: a kill that outruns it, or the window between a pane existing and this process learning its handle, which is reported as a POSSIBLE leak rather than dropped. Closes are journalled too, so `--resume` is idempotent and cannot kill a handle the runtime has since reissued. Exists because the value is making a larger N cheap: the `paneKey` finding read 5/5 one way and the 8th the opposite. Stdlib-only.
- `h_mad_resolved_model.py` — answers "which model did this dispatch actually run?" from evidence or refuses: `codex --log <f>` reads the session header (`resolved=1`), `codex` alone reads `$CODEX_HOME/config.toml` (`configured=1` — what WILL run, not proof), `agy` reads agy's own `cli-*.log` corpus. Exits 2 on anything it cannot establish and prints nothing on stdout, because a wrong model is read as fact. Two failures measured 2026-09-01 against the real 620-log corpus shape it: the agy log TEARS mid-line under concurrent writers (a greedy `label="[^"]+"` yielded eight fragments such as `GeminERROR: logging before google.Init: ...`), and the newest log by mtime was a long-lived pane while the newest by name was that day's `exec agy` — different sessions, so when the two most recent disagree it refuses rather than attributing one to a dispatch. An `exec agy` `--log` is stream-json and carries no model field at all; passing one is refused rather than silently answered from the cli logs. Stdlib-only.
- `h_mad_wire_registry.py` — Phase-5 wire registry: records passing `wiring` pins and re-verifies them at 5f, emitting the documented `[H-MAD]` halt reasons; its challenge command is warning-only and verdict-neutral. `pin` (and `successor_pin`) accept a string or a list of distinct non-empty strings, so one record can cover a task's every call site; all pins must resolve and pass for the record to verify, and halt reasons gain `#<pin>` only on multi-pin records. The base registry is located relative to the **git root**, not to `--repo`, because that is where `git show <sha>:<path>` reads from: in a nested project the two differ, and a `--repo`-relative path named a real but unrelated registry at the root, so `verify` compared two different files and reported every record of one as an undeclared removal of the other (J49 — `FAIL undeclared_removals=5` where the truth was `PASS registered=23 verified=23`). Invisible in a single-project repo, where cwd and the git root coincide. A registry outside the work tree is now refused rather than silently compared against the default path. Stdlib-only.
- `h_mad_issue_fix_gate.py` — file-issue-then-fix-under-TDD linkage gate: printing `ISSUEFIX: PASS|FAIL issue=N …`, exit 0 on verdict / 2 on operational error. Checks that issue N is tied to a test file that names it AND to a `Closes|Fixes|Resolves #N` trailer. `--suggest` prints the `gh` commands for the operator; the gate never invokes `gh` (§"No new external dependency").
- `h_mad_review_evidence.py` — 6a-prime evidence gate: `scan()` + CLI printing `EVIDENCE: PASS|NONE tools=N ok=K failed=J thinking=T [status=…]`, exit 0 on a verdict / 2 on `EVIDENCE: UNREADABLE reason=no_log|empty_log`, which carries **no counts** so a cannot-judge cannot read as a zero. Answers only "did the review read anything" — never whether its findings are right. Counts any tool reaching `DONE`, knows no tool names, and reports `result.status` without gating on it. `thinking=` sums `usage.thinking_tokens` over completed `agent_response` steps and is reported for the same reason `status` is — triage, never a verdict (J49). Stdlib-only.
- `h_mad_context_budget.py` — orchestrator context budget in two modes. `--mode run` prices the RUN against an 80% ceiling, printing `CTXBUDGET: OK|HALT mode=run used=N window=N pct=P ceiling=80` — no `projected=`, because a run cap forwards nothing (§"Run-context ceiling"). `--mode advisor` is the default and its output is unchanged, because `hooks/h-mad-advisor-warn.sh` parses it live; the verdict words differ (`HALT` vs `DENY`) so no consumer can confuse a dying run with an over-budget advisor call. Advisor mode: `last_context_tokens()` + CLI printing `CTXBUDGET: OK|DENY used=N window=N pct=P projected=N ceiling=C`, exit 0 on a verdict / 2 on `CTXBUDGET: UNKNOWN reason=…` (no transcript, no usage record yet, bad window) — which carries **no `used=`** so a cannot-judge can never be read as an `OK`. Prices an `advisor()` call before you make it (§"Orchestrator context hygiene"). Reads the newest **non-sidechain** assistant turn's `input + cache_creation + cache_read`: summing across turns inflates by ~the turn count because `cache_read` is the whole prompt replayed, and a subagent's usage line reports a fraction of the parent's context — both mis-reads fail toward a false `OK`. The number lags the current turn, so it is a floor. Stdlib-only.
- `h_mad_hook_wiring.py` — hook-wiring check: `check()` + CLI printing `WIRING: PASS|FAIL issues=N`, exit 0 on a verdict / 2 on `WIRING: UNKNOWN reason=no_settings` (no readable settings file, so nothing was examined — it carries no `issues=`). Detail lines `HOOK_NOT_WIRED:`/`HOOK_WIRED_WRONG_MATCHER:`/`HOOK_WIRED_STALE_PATH:`. Deliberately a separate verdict from `INSTALL:` so a settings source this check cannot see can never halt bootstrap (§"Wired, not just installed"). Searches the user scope honouring `CLAUDE_CONFIG_DIR` and every `.claude/settings*.json` up the tree, matches on the hook **basename** inside the command (the live wiring is `bash $HOME/…/hook.sh`, an unexpanded variable in a longer line), and treats match-all matchers before regex so `*` cannot raise. Stdlib-only.
- `h_mad_doc_shape_check.py` — doc-superset guard for saved phase documents (run at Phase 3/4/7 save, see `references/inline-protocols.md`): `check_document()` + CLI printing one `DOC-SHAPE: PASS|FAIL|SKIP path=… type=…` line per path, exit 0 on a verdict / 2 on an unreadable path (with no partial verdict stream). `SKIP` is the correct verdict for h-mad's brainstorm/spec/impl-plan/audit documents — they sit outside the external validator's detection by design and have no superset contract. FAIL reports dropped required sections *and* plan-plus escalation literals in a plan's prose: the templates are compliant and tested, but the authored body is not the template, and the escalation literals are ordinary words an author has no reason to suspect. The section tables and literals are h-mad's own copy so the check runs standalone (§"Standalone / no plugin dependency"); `tests/test_h_mad_doc_shape_check.py::TestMirrorFidelity` diffs the tables, the literals, and the verdicts against the live external validator when installed and fails on drift, which is what keeps the mirror honest (§"Single-source verdicts"). Stdlib-only.

### file-issue-then-fix-under-TDD

The loop, when a measurement turns into a defect:

1. **File the issue with the measurement in it** — the number, the command that produced it, the expected value. An issue that says "X is broken" without the observation cannot be verified closed. Sanitize first (§"Filing to a public tracker").
2. **One test file per issue**, and the file **names the issue** (`# pins #42`). This is the link that survives; six weeks on, a test whose motivation lives only in the author's head reads as arbitrary and gets deleted.
3. **RED before GREEN.** Confirm the new test fails against the unfixed code — a test that passes against the code it was written to catch is decoration.
4. **Fix, then close via the trailer** — `Closes #42` in the commit body.
5. **Gate the linkage**: `h_mad_issue_fix_gate.py --issue 42 --test <path>`. It catches the two failures that actually happen — a fix with no test naming the issue, and a test with no trailer closing it.

Steps 1–4 are the discipline; step 5 is the only part a script can check, which is why the script checks that and nothing else.

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
- `references/state-schema.md` — state schema details
- `references/agent-substrate.md` — Agent dispatch substrate (cmux | orca) — hmad-dispatch verbs, detection, identity pins, pane launch
- `references/orchestration-mode.md` — Orca structured orchestration and Phase-5 worktree fanout protocol
- `agents/{spec,plan,design,implplan}-author.md` — the four phase-document authors (§"Teammate authors")
- `agents/doc-auditor.md` — the teammate audit leg (§"Teammate audit leg")
- `references/codex-implementer-prompt.md` — Phase 5d/5e Codex dispatch template
- `references/agy-spec-reviewer-prompt.md` — Phase 5e-review agy dispatch template
- `references/agy-architectural-reviewer-prompt.md` — Phase 6a-prime agy dispatch template
- `references/agy-skill-reviewer-prompt.md` — reviewing a **skill** (doc+script family) rather than a feature; not phase-gated, dispatched via `exec agy`. See §"Reviewing a skill with agy"
