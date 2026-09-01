# Handoff — `_frame_satisfies` inverts BOTH wait gates on a large frame (SIGPIPE under `pipefail`)

**Date:** 2026-09-01
**Branch:** `BrightGold70/wait-frame-gate-sigpipe` (created 2026-09-01; Orca assigned this name, not the `fix/…` one this brief first predicted)
**Project:** orca/skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** orca/skills · feature/pin-agents-tail-banner · session 61bd3e31-7519-4b5e-aba0-f616a46e8799
**Taken-Over-By:** orca/skills · BrightGold70/wait-frame-gate-sigpipe · session unknown · 2026-09-01 — completed and merged as `282a3a5`; worktree removed

## Session Summary

A live defect in the **shipped** `hmad-dispatch.sh`, found while auditing an unrelated feature's
impl-plan. `_frame_satisfies` (`h-mad/scripts/hmad-dispatch.sh:3331`) matches a terminal frame with
`printf '%s' "$frame" | grep -Eq …`. Under the wrapper's global `set -o pipefail`, `grep -q` exits
at the first match, `printf` takes SIGPIPE, and the pipeline reports **141** — so a match is read
as a non-match. Both gates of `hmad-dispatch wait` invert, each in its worse direction.

**Nothing has been fixed. No claim exists.** `docs/.bkit-memory.json` has no record for
`wait-frame-gate-sigpipe` (verified: `NO SUCH FEATURE`), so there was nothing to release and
nothing for you to take over — claim it when you start.

## Key Learnings

- **The two gates fail in opposite directions, and the dangerous one fails OPEN.** With
  `--not-while-regex`, a frame that DOES contain the forbidden text is reported as clean, so `wait`
  returns "done" for a pane that is mid-generation — exactly the failure that flag was added to
  close (`SKILL.md` §"Idle is not completion"). With `--until-regex`, a condition that IS met is
  reported unmet, so `wait` burns its full timeout.
- **It is invisible below the pipe buffer (~64 KB on macOS).** Every small-input test passes. This
  is why it has survived: the idiom is correct for every frame anyone has tested it with.
- **Practically latent, not actively burning — say so rather than overselling it.** `wait` reads
  agent panes, and an agent pane retains only 12–18 lines of normal-buffer scrollback because it is
  a full-screen TUI on the alternate screen (measured 2026-09-01 on three real panes). ~1.5 KB, far
  under the buffer. cmux's 400-line cap cannot reach it either. It triggers on a pane carrying real
  normal-buffer history — i.e. **one where the agent exited to a shell**, which is a real state.
- **`HMAD_SNAPSHOT_LINES` defaults to 4000** (`orca` branch of `_snapshot`), so the input is
  bounded only by what the pane actually holds: 4000 × ~80 chars ≈ 320 KB when a pane is busy.
- The identical defect was found and fixed in the `pin-agents-tail-banner` impl-plan
  (commit `87aebed`, same repo). Reuse that reasoning; do not re-derive it.

## Next Steps

1. **Reproduce first — do not take this brief's word for it.** Save and run:

   ```bash
   cd /Users/kimhawk/orca/skills
   python3 - <<'PY' > /tmp/frame_probe.sh
   import pathlib
   src = pathlib.Path('h-mad/scripts/hmad-dispatch.sh').read_text().splitlines()
   assert src[-1] == 'main "$@"'      # the harness strips this; fail loudly if it moved
   print("\n".join(src[:-1]))
   print('''
   big="$(python3 -c "print('Waiting for background terminal'); print(('y'*79+chr(10))*4000, end='')")"
   small="Waiting for background terminal"
   rc=0; _frame_satisfies "$big"   "" "Waiting for background terminal" || rc=$?
   echo "large + not-while match -> rc=$rc   (want 1, blocked)"
   rc=0; _frame_satisfies "$small" "" "Waiting for background terminal" || rc=$?
   echo "small + not-while match -> rc=$rc   (control, want 1)"
   rc=0; _frame_satisfies "$big"   "Waiting for background terminal" "" || rc=$?
   echo "large + until match     -> rc=$rc   (want 0, satisfied)"
   rc=0; _frame_satisfies "$small" "Waiting for background terminal" "" || rc=$?
   echo "small + until match     -> rc=$rc   (control, want 0)"
   ''')
   PY
   bash /tmp/frame_probe.sh
   ```

   Observed 2026-09-01 — controls correct, large frame inverted on both gates:

   | gate | frame | expected | actual |
   |---|---|---|---|
   | `--not-while-regex` matches | 320,031 B | rc 1 | **rc 0** |
   | `--not-while-regex` matches | 31 B | rc 1 | rc 1 |
   | `--until-regex` matches | 320,031 B | rc 0 | **rc 1** |
   | `--until-regex` matches | 31 B | rc 0 | rc 0 |

2. **Fix both call sites in `_frame_satisfies`** — `h-mad/scripts/hmad-dispatch.sh:3333` and `:3339`.
   A here-string has no pipeline, so the compound's status is `grep`'s alone:

   ```sh
   -  if [ -n "$not_while_re" ] && printf '%s' "$frame" | grep -Eq -- "$not_while_re"; then
   +  if [ -n "$not_while_re" ] && grep -Eq -- "$not_while_re" <<<"$frame"; then
   ...
   -      printf '%s' "$frame" | grep -Eq -- "$pat" || return 1
   +      grep -Eq -- "$pat" <<<"$frame" || return 1
   ```

   `printf … | grep -Eq … >/dev/null` (dropping `-q`) also works — `grep` then reads to EOF so
   `printf` never gets SIGPIPE — but it reads the whole frame pointlessly and leaves a pipeline to
   reason about. Prefer the here-string. The wrapper is `#!/usr/bin/env bash`, so `<<<` is fine.

3. **TDD it.** RED first: a test calling `_frame_satisfies` with a ≥200 KB frame, one per gate, both
   failing against the unfixed function. Use the strip-`main` harness from step 1 — the wrapper ends
   in an unconditional `main "$@"`, so sourcing it to reach a private function runs `main` as a side
   effect, and `main`'s default arm `return 2` under `set -e` kills the shell before any definition
   survives. Assert on the terminal line, not on a line number.
4. **Mutation-test the guard**: revert each here-string to the pipeline form, one mutation per call
   site, each with a `test:` naming its own node so the kill is credited to the property and not to
   an unrelated failure. Spec `root` must be **relative** (`"../.."`, resolving to `h-mad/`), matching
   the sibling specs. Read the `MUTATION:` token, never `$?`.
5. **Sweep for the same idiom before closing.** `_frame_satisfies` is the instance with unbounded
   input, but the pattern is repo-wide:
   ```bash
   command grep -nE '\|[[:space:]]*(grep[^|]*-[a-zA-Z]*q|head( |$))' h-mad/scripts/hmad-dispatch.sh
   ```
   Most hits are `x="$(… | head -1)"` over small `jq` output and are fine. Two worth judging:
   `:2647` (`printf '%s\n' "$recovered" | grep -aqE …` — recovered transcript, can be large) and
   `:2906`/`:2967` (`printf '%s\n' "$live" | grep -qx` — handle list, small). Decide each on whether
   its input can exceed the buffer; record the ones you rule out and why, so the next sweep does not
   re-litigate them.
6. **Run both coupled suites before merging.** `~/.claude/skills/{h-mad,handoff}` are symlinks into
   this repo, so an edit here is live for every running session immediately — including the
   `pin-agents-tail-banner` lane, which is mid-Phase-5 and calls `wait`. Work in your own worktree
   and merge when green.

## Open / Blocked Items

- **The whole item is open; nothing is started.** No branch, no worktree, no claim, no code.
  - `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/wait-frame-gate-sigpipe · worktree: /Users/kimhawk/orca/workspaces/skills/wait-frame-gate-sigpipe`
  - Defect site: `h-mad/scripts/hmad-dispatch.sh:3331-3345` (`_frame_satisfies`)
  - Precedent fix, same class, same repo: commit `87aebed`
- **Not investigated: whether `wait` has ever actually mis-fired in a real run.** The mechanism is
  proven; a field occurrence is not. If you want that evidence it would come from a pane whose agent
  exited to a shell and then accumulated >64 KB, which is reproducible on demand but was not done.
- **Decide whether this warrants full h-mad or a direct TDD fix.** It is a two-line change with a
  clear reproduce and two tests. My read is that full 7-phase h-mad is disproportionate, but that is
  your call and I am not making it for you.

## In-Flight Processes

None. Nothing was started for this item.

## Context for Next Session

**Files touched by this handover:** this brief only. No code, no state, no claim.

**Sender's lane (coordination only — NOT yours to work):**
- `repo: /Users/kimhawk/orca/skills · branch: feature/pin-agents-tail-banner · worktree: /Users/kimhawk/orca/skills`
- Sender holds `pin-agents-tail-banner` (session `61bd3e31-…`) and keeps it — mid-Phase-5b, 15 audit
  cycles, impl-plan v1.12. Only this wrapper defect moves.
- That lane calls `hmad-dispatch wait`, so it is a live consumer of the function you are fixing.

**To pick this up:**
```bash
cd <your worktree>
sed -n '3325,3346p' h-mad/scripts/hmad-dispatch.sh          # the defect
bash /tmp/frame_probe.sh                                     # reproduce (step 1 writes it)
git log --oneline -1 87aebed                                 # the precedent fix
```

**Related docs:**
- `h-mad/SKILL.md` §"Reading a dispatch verdict" — documents the `--not-while-regex` guard this breaks
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md` — same defect class, measured at length
