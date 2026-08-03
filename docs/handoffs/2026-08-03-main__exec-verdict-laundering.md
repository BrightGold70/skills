# Handoff — `hmad-dispatch exec` launders its own prompt into a verdict (plus a false tree-delta)

**Date:** 2026-08-03
**Branch:** main
**Project:** /Users/kimhawk/orca/skills
**Handover-From:** HemaSuite · feature/196-grounding-shadow-measurement · session d185c497-29e4-4de0-ac43-d3770b39d1d0

> **This is a HANDOVER, not a session closeout.** Two `hmad-dispatch` defects were found while
> running a real Phase-5 dispatch from the HemaSuite worktree. They are skills-repo bugs. The
> sending session has dropped them and is not monitoring. Nothing was started on either.

## Session Summary

A `hmad-dispatch exec codex` dispatch failed on revoked Codex auth (401
`refresh_token_invalidated`). The agent never ran and wrote nothing — but the wrapper reported
`STATUS: NEEDS_CONTEXT` and `tree delta: 1 changed`, both false, and **wrote the fabricated verdict
into the `--out` file** where the documented extractor reads it. An orchestrator following the
skill's own contract would have read a contract-valid verdict and concluded the agent asked a
question. Both defects are one-line-locatable and neither has a test.

**The skill currently claims `exec` is immune to this class.** §"Reading a dispatch verdict"
documents the J17 contract-echo trap for the *scrape* path and prescribes `--after-marker`, and
§"Exit-code dispatch" sells `exec` as sidestepping "the whole pane failure class — tui-idle
false-idle, prompt-echo, scrape, identity resolution". Prompt-echo is back, in the `exec`
recovery path, unguarded.

## Key Learnings

- **Defect 1 — `exec` log-recovery greps the whole transcript, prompt echo included.**
  `h-mad/scripts/hmad-dispatch.sh:1926`:
  ```bash
  recovered="$(grep -aE '^(STATUS|VERDICT):' "$log" 2>/dev/null | tail -1 || true)"
  ```
  The transcript contains the echoed prompt. A dispatch prompt that states its output contract —
  which the skill's own `references/codex-implementer-prompt.md` requires — lists the four legal
  values as fenced blocks, each starting its own line. `tail -1` therefore returns **the last
  option in the contract block**, deterministically. Measured: the only four `STATUS:` lines in a
  20,770-byte log were at lines 268/271/274/277 — `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`,
  `NEEDS_CONTEXT` — my prompt's own block, in order. No agent-authored `STATUS:` line existed.
  The `key-must-start-the-line` guard does not help: the echoed contract lines do start the line.
- **It is worse than a bad stderr message, because line 1930 writes it to `--out`.** The primary
  channel then holds a clean, contract-valid verdict that `h_mad_extract_verdict.py` accepts
  without complaint. Silence would have been safer; this manufactures confidence.
- **Defect 2 — `tree delta: N changed in <cd_dir>` counts the whole repository.**
  `h-mad/scripts/hmad-dispatch.sh:1934`:
  ```bash
  delta="$(git -C "$cd_dir" status --porcelain 2>/dev/null | grep -c . || true)"
  ```
  `git -C <subdir> status --porcelain` with no pathspec reports the entire work tree, not
  `<subdir>`. Measured: `--cd …/HemaSuite/hematology-paper-writer` reported `1 changed`, while
  `git status --short .` in that directory returned **nothing** — the counted file was
  `HemaSuite/.bkit/state/pdca-status.json`, pre-existing, unrelated, and one directory up. The
  skill's recovery protocol leans on this number ("Artifacts present with no report means the work
  happened"), so a false non-zero pushes the reader toward "work landed, reporting failed" when in
  fact nothing ran.
- **The two compound.** A fabricated verdict plus a fabricated tree delta is exactly the evidence
  pattern the skill's §"A missing report on the `exec` path" tells you to read as *work completed
  but unreported* — and the documented response to that is "do not re-dispatch". A correct reading
  took reading the raw log; the wrapper's own summary pointed the other way on both axes.

## Next Steps

1. **Fix Defect 1** — `h-mad/scripts/hmad-dispatch.sh:1926`. The clean fix is not `--after-marker`:
   that flag is a `send` affordance, and `exec` appends no boundary. Options, in rough order of
   how much they cost: (a) have `exec` append the same `===HMAD-DISPATCH-BOUNDARY===` line to the
   prompt it pipes to stdin, then slice the log past its last occurrence — this makes the two
   paths share one mechanism; (b) drop the log-recovery path entirely when the transcript contains
   the prompt echo, and report "no verdict" honestly; (c) recover only from log content written
   *after* the last line of the prompt file, which `exec` already has on disk. **RED first**: a
   test that pipes a prompt containing the four-option contract block, fails the agent, and asserts
   the wrapper does **not** emit a verdict.
2. **Fix Defect 2** — `h-mad/scripts/hmad-dispatch.sh:1934`. Add the pathspec:
   `git -C "$cd_dir" status --porcelain -- .`. RED: a repo whose only dirty file is outside
   `$cd_dir` must report `tree delta: 0`.
3. **Correct the skill text** — §"Exit-code dispatch for 5d/5e" claims `exec` sidesteps prompt-echo.
   It does, for the *success* path; the failure path does not. Say which.
4. **Mutation-verify both guards** (`h_mad_mutation_harness.py`), and run **both** suites — the
   `~/.claude/skills/h-mad` symlink couples this repo to HemaSuite's.

## Open / Blocked Items

- **Both defects** — status: not started, ownership now here.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills (main worktree)`
  - Both sites: `h-mad/scripts/hmad-dispatch.sh` lines **1926** (verdict recovery) and **1934** (tree delta),
    inside the `EMPTY final message` block that begins at ~1918.
  - Evidence transcript, if you want the raw artifact before it is cleaned up:
    `/private/tmp/claude-501/-Users-kimhawk-orca-HemaSuite/d185c497-29e4-4de0-ac43-d3770b39d1d0/scratchpad/task5.log`
    (20,770 B; the four echoed `STATUS:` lines are at 268/271/274/277) and its sibling
    `codex_task5.txt` (the 17,130 B prompt that produced them).
- **No claim to release** — verified, not assumed: `~/orca/skills/docs/.bkit-memory.json` holds 8
  features and zero live `owner_session_id`. These are new defects with no h-mad feature record.
- **Not reproduced on a healthy agent.** The trigger here was a 401 auth failure. Any `exec` whose
  agent exits without a final message should reproduce it — that is the whole `EMPTY final message`
  branch — but I did not construct a second, non-auth failure to confirm. Worth one probe before
  assuming the auth path is special.

## In-Flight Processes

None. The dispatch that produced this evidence exited (rc=1) and was reaped.

## Context for Next Session

**Files this handover concerns (none modified — both defects unstarted):**
- `h-mad/scripts/hmad-dispatch.sh:1926` — Defect 1, verdict laundering
- `h-mad/scripts/hmad-dispatch.sh:1934` — Defect 2, whole-repo tree delta
- `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e" — the immunity claim to correct

**Uncommitted changes:** none from this handover.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
sed -n '1918,1940p' h-mad/scripts/hmad-dispatch.sh     # both defects in one block
# Defect 2 reproduces in seconds from any repo whose dirty file is outside the subdir:
git -C <repo>/<subdir> status --porcelain | grep -c .     # counts the WHOLE repo
git -C <repo>/<subdir> status --porcelain -- . | grep -c . # what it should count
```

**Related docs:**
- `docs/handoffs/2026-08-03-main__five-hmad-items-handover.md` — the earlier five-item handover from
  the same HemaSuite session; unrelated defects, same sender
