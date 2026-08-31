# Handoff — wire-pin gate fix, and two skill upgrades that came out of using them

**Date:** 2026-09-01
**Branch:** `main`
**Project:** `/Users/kimhawk/orca/skills` (h-mad + handoff skills)

## Session Summary

Continuation past an earlier closeout (`0178a9d`) in the same sitting. Four things landed, all on
`main`, all pushed: the J1 residual lane's work merged back (`016120f`); a **live Phase-5b blocker**
in `h_mad_wire_pin_gate.py` was fixed properly rather than worked around (`3219bdd`); h-mad's 80%
context ceiling now routes to the handoff **skill** instead of telling the reader to "write a
handoff" (`2827109`); and handoff READ gained a bounded auto-resolve step so a resume repairs the
mechanical divergences instead of handing the user a second task list (`c8717ad`). Nothing is owed,
nothing is claimed, tree clean and 0/0 with origin.

The through-line: three of the four items were defects that had survived because they failed in the
**safe** direction, and nothing pointed at them.

## Key Learnings

- **A gate that fails CLOSED can hide indefinitely.** `h_mad_wire_pin_gate.py` could not see
  `**WIRE 1**:` / `**WIRE 2A**:` — five wires across two tasks read as `wiring` shape with *no wire*,
  a blocking `missing WIRE` on a correct plan. It went unnoticed for weeks because a gate that emits
  a false PASS gets hunted, while a gate that **blocks correct work gets worked around by hand** —
  here by rewriting the plan's labels to canonical pairs — and the workaround leaves no trace
  pointing at the gate. Ask of every gate not only "can it pass what it should fail?" but "can it
  fail what it should pass, and what would an author do about it?" The tell is a hand-edit making a
  document conform to a tool.
- **Fixing the visible half would have been worse than the bug.** `_parse_tasks` kept ONE wire slot
  per task and the registry's identity is `(owning_feature, id)`, so two wires from one task collide
  **by construction** — the second upserts the first while the gate prints `registered=2`. Same shape
  as the J43 collision one level down. A regex-only fix converts a loud blocker into a **silent
  under-registration**, and a short registry is indistinguishable from a plan that had one wire.
- **The `paneKey` omission is COMMAND-discriminated.** From the residual lane, over 31 creates on
  Orca 1.4.192: `sleep 300` carried a key 16/16, `agy` 3/3, **`codex` 0/11** — all `surface:
  visible`, with ten calls fired 115–134 ms after worktree creation *in each arm*. Not timing, not
  `surface`. This item falsified a confidently-worded claim of its own **three times in one day**
  (3 samples → 5 → 1); the answer needed 31 with a control arm per payload.
- **"Auto-resolve divergences" is three problems, not one.** Mechanical repairs; a premise needing a
  live probe; and work owned by another lane. A blanket rule sweeps all three. The fast-forwardable
  sibling branch is the trap: it looks cleanest (clean tree, true ancestor, pure ff) and the cost is
  not to git but to the agent whose files change mid-turn.
- **A doc test that slices a fixed character window goes vacuous as its section grows.** A 4000-char
  slice from a heading stopped covering the `HALT`/`DENY` distinction the moment a paragraph was
  added. It failed loudly this time; had the growth been elsewhere it would have passed while
  measuring nothing. Bound a section on the next heading, never on a byte count.
- **A mutation naming a `test` requires the spec to carry `target_command`.** Without it the harness
  answers `UNREADABLE` — loud, correctly. Adding one is not free: it runs the whole suite per
  mutation, so for four doc-rule mutants the right move was to match the spec's existing convention
  and keep intent in `_killed_by`.
- **zsh keeps finding new ways to make a probe lie.** Three distinct instances this session:
  `cmd $LIST` does not word-split (whole list becomes ONE argument →
  `ANCHORS_NOTHING_SWEPT`); an unquoted `--include=*.py` dies as a glob error *before* grep runs
  (reported "no exec-pane tests" over a 37 KB file); and `$B:h-mad` applied `:h` as a **history
  modifier**, mangling a git ref into `origin/BrightGold70-mad/...`. Same signature every time: the
  failure is the shell's, upstream of the tool, and its output is indistinguishable from a real
  empty result.

## Next Steps

Nothing is owed on this branch. In priority order if picked up again:

1. [suggested] **Widen Step 3.6's allowlist to the fast-forwardable sibling**, if wanted — it was
   offered and not taken. The gate would need "no live agent in that worktree", which is checkable
   via `orca terminal read` on the panes in that worktree; without that gate it must stay on the
   never-list. `handoff/SKILL.md` §"Step 3.6".
2. [suggested] **Two rows in `docs/skill-candidates.md` carry no `candidate:` token** (lines ~785 and
   ~833) — the census reports `verdict-less=1` after bump-row exclusions. They are rows `016120f`
   rewrote in past tense, dropping the verdict. Re-add one so the census reads clean:
   `python3 ~/.claude/skills/handoff/scripts/skill_candidates_census.py docs/skill-candidates.md`
3. [suggested] `.result.split.handle` (`hmad-dispatch.sh` `_cmd_exec_pane` split branch) was closed
   as **no joinable key** by the other lane — nothing owed, but it is the one surface that still
   trusts a create-response handle without a join.

## Open / Blocked Items

- **None blocking.** No claim is held (`docs/.bkit-memory.json` → no owner on any feature), the
  handed-over lane completed and merged, and the tree is clean.
- **`BrightGold70/j1-residual-probes` worktree is disposable** — status: informational. Its commit
  `016120f` is merged into `main`, so both the worktree and the branch can be removed
  (`git branch -d` now succeeds where it correctly refused earlier). Left in place deliberately; it
  costs nothing.
  - `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/j1-residual-probes · worktree: /Users/kimhawk/orca/workspaces/skills/j1-residual-probes`

## Context for Next Session

**Files touched this session** (since `0178a9d`; 17 files, +996/−221):
- `h-mad/scripts/h_mad_wire_pin_gate.py` (numbered labels, per-wire registration), `h-mad/scripts/hmad-dispatch.sh` (`_resolve_pane_by_handle`, from the merged lane)
- `h-mad/SKILL.md` §"Run-context ceiling" + the NEVER list; `h-mad/references/failure-recovery.md`
- `handoff/SKILL.md` (new READ Step 3.6, Step 5 report shape, don'ts, frontmatter description)
- tests: `test_h_mad_wire_pin_gate.py` (+7), `test_h_mad_context_budget_docs.py` (+6), `test_handoff_read_auto_resolve.py` (new, 23)
- specs: `wire_pin_numbered_labels.json`, `read_auto_resolve.json` (new); `context_budget_docs.json` (+4), `launch_no_panekey_fallback.json` (from the lane)

**Uncommitted changes:** none. `main` at `c8717ad`, 0/0 with `origin/main`.

**Verification standing at close:** full suite **2376 passed** (`RUN_RC` captured on the command, not
read from the background notification — those have reported 0 over real failures); anchors
**`ANCHORS_OK specs=32 mutations=355 ok=355 drifted=0`**; every spec touched this session
`ALL_CAUGHT` (`wire_pin_numbered_labels` 4/4, `read_auto_resolve` 5/5, `context_budget_docs` 20/20,
`exec_pane_panekey` 3/3, `launch_no_panekey_fallback` 2/2).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git log --oneline 0178a9d..HEAD          # the four commits of this stretch
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests handoff/tests -q
# anchors: run under bash, NOT zsh -- zsh does not word-split the candidate list
bash -c 'mapfile -t C < <(git -c core.quotePath=false ls-files -- "*.json"); \
  python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors "${C[@]}" </dev/null | tail -2'
```

**Related docs:**
- `docs/handoffs/2026-08-31-main__j1-pane-pin-takeover-and-handover.md` — the earlier closeout this continues
- `docs/skill-candidates.md` §`2026-08-31 — wire-pin-numbered-labels` and §`— j1-launch-pane-pin`
- `handoff/SKILL.md` §"Step 3.6" · `h-mad/SKILL.md` §"Run-context ceiling"
