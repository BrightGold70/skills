# Handoff — J1 pane-pin: took it over, shipped the code half, handed the residuals on

**Date:** 2026-08-31
**Branch:** `main`
**Project:** `/Users/kimhawk/orca/skills` (h-mad)

## Session Summary

Took over an inbound handover from HemaSuite (J1: `hmad-dispatch launch` cannot pin a pane when
Orca's create response omits `paneKey`), and closed everything it could close. The tracking half is
done — the item now lives in `docs/skill-candidates.md` instead of a TodoList number that pointed at
nothing. The code half shipped: `exec-pane` no longer trusts `.result.terminal.handle`, and the two
call sites that read that field now share one join helper while deliberately disagreeing on failure.
The two things that genuinely needed a probe nobody had run were handed to their own lane, which has
**picked them up** (claimed, stamped, premises re-verified). `main` is clean and owes nothing.

The sharpest outcome is a premise that broke *while the handover was being delivered*: creating the
receiving lane's own agent terminal reproduced the missing `paneKey` — with `surface: "visible"`,
falsifying the hypothesis this repo had recorded hours earlier.

## Key Learnings

- **A guard's justification can be falsified while the guard stays right.** `agent-substrate.md`
  said `.result.terminal.handle` is "a pre-adoption placeholder the pane never has (confirmed 3×)".
  Re-probed on Orca 1.4.192 it equalled the adopted handle **5/5**. The observations were real; the
  *tense* was wrong, and it was the stated reason for the whole resolve-by-paneKey path. Rewritten so
  the path rests on an argument that survives either behaviour — the join is correct whether or not
  the create handle happens to be real — rather than on an invariant the next Orca build can break.
- **Then the opposite half broke too, in the same session.** Creating the handover lane's terminal
  returned `paneKey: null` with `surface: "visible"` and a **genuine** handle (present in
  `terminal list` once, with tab/leaf). So `surface` does not discriminate, the omission is real and
  current, and this instance *inverts* J1: key missing, handle good. `launch` would have refused a
  good handle; `exec-pane`'s fallback was right. 1 omission in 8 creates; two isolation probes ruled
  out "new worktree" and the `id:` selector as sufficient causes.
- **Same field, opposite correct treatment, and the difference is the PRODUCT.** `launch` yields a
  durable pin every later dispatch resolves through, so a wrong value poisons the session — it
  refuses. `exec-pane` yields a dispatch that is *already running* when the response is read — it
  falls back. A fail-loud `exec-pane` would pass a "resolves by paneKey" test and break every host
  build that omits the field, so the fallback needed its own test rather than being left implicit.
- **`worktree create` snapshots the branch at that instant.** Two commits pushed after the lane was
  created never reached its checkout, so it held a brief whose section 2 I had already falsified. It
  adopted the correct premise anyway — only because the handoff store is canonical (READ resolves the
  *main* worktree's `docs/handoffs`, not the linked one). Create the lane last, or ff it after a late
  correction.
- **Three of my own measurements read as success while measuring nothing.** A mutant appending
  `; true` inside a command substitution produced an empty `resolved` — the fallback the test already
  expects — so it survived while proving nothing. A hand-run anchor sweep reported
  `ANCHORS_NOTHING_SWEPT` purely because **zsh does not word-split unquoted expansions**, sending all
  86 paths as one argument. And `grep --include=*.py` under zsh failed as a glob error, printing "no
  matches" for a test file that existed. Each looked like a finding about the repo and was a finding
  about my shell.
- **`orca terminal read` → `.result.terminal.tail` identifies panes the other surfaces cannot.**
  `hmad-dispatch env` reported `codex -> UNRESOLVED` over three candidates Orca named in no
  `agents[]` and whose previews were empty; `tail` distinguished all three on the first read. The
  field is `tail` — `.content`/`.output`/`.preview` are absent and return nothing in a way that looks
  exactly like an empty pane.

## Next Steps

Nothing is owed on this branch. In priority order if the topic is picked up again:

1. **Do NOT re-adopt the J1 residuals** — they are owned by session `01a0567a…` in
   `/Users/kimhawk/orca/workspaces/skills/j1-residual-probes`. Check its state before acting:
   `git -C /Users/kimhawk/orca/workspaces/skills/j1-residual-probes log --oneline -5`
2. [suggested] Reconcile the open rows in `docs/skill-candidates.md` — the `2026-08-31 —
   j1-launch-pane-pin` heading has one row still open (`.result.split.handle`, pending the other
   lane's probe) and the file's older headings carry rows nobody has flipped.
3. [suggested] If the other lane finds the omission tracks elapsed time since `worktree create`, the
   guard message at `h-mad/scripts/hmad-dispatch.sh` should say "retry" rather than "pin manually" —
   that wording change is this repo's to make, not the probing lane's.

## Open / Blocked Items

- **J1 residual probes** — status: **handed over and picked up**, not blocked. `.result.split.handle`
  shape and the missing-`paneKey` timing hypothesis.
  - `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/j1-residual-probes · worktree: /Users/kimhawk/orca/workspaces/skills/j1-residual-probes`
  - Brief: `docs/handoffs/2026-08-31-BrightGold70-j1-residual-probes__split-and-surface-probes.md`
  - Claim `j1-launch-pane-pin-durability` held by session `01a0567a…` (live). **Not ours.** Do not
    release, do not re-claim, do not monitor — the transfer is complete and was verified by claim,
    `taken over:` stamp, and the receiver's own takeover report.
  - Lane was fast-forwarded `2ce4201 → 83861eb` at the user's request and is 0 behind `main`.
- **`.result.split.handle` has no guard** — status: deliberate, filed. `_cmd_exec_pane`'s `--split`
  branch reads a handle from a response object nobody has probed. Not guessed at; the other lane owns
  the probe.
- **Task tool state vanished mid-session** — `TaskList` returned 7 tasks and then "No tasks found"
  at wrap-up with none deleted by me. All 7 were completed first, so nothing was lost, but the sink
  is not durable across a session and should not be treated as one.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` (new `_resolve_pane_by_key`; `_cmd_launch` routed through it; `_cmd_exec_pane` create branch; J1 comment block)
- `h-mad/tests/test_hmad_dispatch_exec_pane.py` (3 new tests), `h-mad/tests/test_hmad_dispatch.py` (comment)
- `h-mad/tests/mutation-specs/exec_pane_panekey.json` (new)
- `h-mad/references/agent-substrate.md`, `h-mad/SKILL.md`
- `docs/skill-candidates.md`, `docs/handoffs/` (3 briefs)

**Uncommitted changes:** none. `main` at `83861eb`, 0/0 with `origin/main`.

**Verification standing at close:** full h-mad suite **2281 passed** (`RUN_RC` captured on the
command, not read from the background notification, which has reported 0 over real failures);
`exec_pane_panekey.json` **ALL_CAUGHT 3/3**; anchors **ANCHORS_OK specs=29 mutations=340 ok=340
drifted=0**.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git log --oneline 214450a..HEAD          # the 8 commits of this session
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/exec_pane_panekey.json
# anchors: run under bash, NOT zsh -- zsh does not word-split the candidate list
bash -c 'mapfile -t C < <(git -c core.quotePath=false ls-files -- "*.json"); \
  python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors "${C[@]}" </dev/null | tail -2'
```

**Related docs:**
- `docs/handoffs/2026-08-31-main__j1-launch-pane-pin-durability.md` — the inbound brief
- `docs/handoffs/2026-08-31-BrightGold70-j1-residual-probes__split-and-surface-probes.md` — the outbound one
- `docs/skill-candidates.md` § `2026-08-31 — j1-launch-pane-pin (takeover probe)` — the durable row
- `h-mad/references/agent-substrate.md:27` — the `launch` row, now date-scoped
