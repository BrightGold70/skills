# Handoff — `hmad-dispatch exec agy` is broken against agy 1.1.14

**Date:** 2026-08-19
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · feature/71-run-report-seam-restoration · session 679a9622-c2e3-4665-b372-60356ffe889f

## Session Summary

Found while running 16 H-MAD audit cycles from a HemaSuite feature. `hmad-dispatch exec agy` returns
nothing at all against agy 1.1.14 — the documented headless audit path is dead. Root cause measured
and a working invocation confirmed; **no fix applied here**, because the defect belongs to this repo
and the finding session had no claim on it. One-line change plus a doc-test's worth of coverage.

## Key Learnings

- **`--print` takes the prompt as its value.** `agy --help` on 1.1.14 lists `--prompt  Alias for
  --print`. The wrapper invokes `agy --print --dangerously-skip-permissions <prompt>`, so `--print`
  swallows the *flag* as its prompt and the real prompt becomes a stray positional.
- **The failure is silent in the worst way**: agy answers the flag as if it were a question, the
  wrapper sees no `STATUS:`/`VERDICT:`/sentinel, and on a large prompt it just burns the watchdog.
  Observed `rc=124` with a **0-byte** `--log`, which reads as "agy hung" rather than "we passed
  garbage".
- **`--cd <path>` made it worse** — instant failure with no log file created at all, versus at least
  a 0-byte log without it. Worth checking whether `--cd` is still a supported wrapper flag.

## Reproduce

```bash
# BROKEN — agy answers ABOUT the flag
agy --print --dangerously-skip-permissions "Reply with exactly: PROBE_OK"
#   -> "It looks like you provided a command-line flag (--dangerously-skip-permissions),
#       but I need a bit more context..."

# CORRECT — boolean flags BEFORE --print
agy --dangerously-skip-permissions --print "Reply with exactly: PROBE_OK"
#   -> PROBE_OK
```

Confirmed at agy 1.1.14, `/Users/kimhawk/.local/bin/agy`.

## Next Steps

1. **Fix the flag order** in the `exec agy` branch of `scripts/hmad-dispatch.sh` — put
   `--dangerously-skip-permissions` (and any other boolean flags) *before* `--print`, or pass the
   prompt via `--prompt`.
2. **Check `--cd`** is still accepted by the wrapper's `exec` verb; it produced an instant silent
   failure with no log.
3. **Add a doc-test / smoke check** that the assembled argv puts booleans ahead of `--print`. This
   class is invisible to any test that stubs the agy binary, because the defect is entirely in argv
   ordering — the stub would accept either order.
4. Cross out the corresponding HemaSuite todo once fixed; it is tracked there only as a pointer.

## Open / Blocked Items

- **Nothing is claimed.** `/Users/kimhawk/orca/skills/clinical-statistics-analyzer/docs/.bkit-memory.json`
  exists but holds no record for this work — it is a sub-project store, unrelated to the wrapper.
  No h-mad claim was released because none was ever taken.
- **Not delivered to an agent lane.** The finding session wrote this brief but did **not** spawn a
  worktree/agent to act on it — that would have been an outward action nobody asked for. Pick it up
  from here.

## Context for Next Session

**Files touched this session:** none in this repo. The fix is unwritten.

**Likely target:** `scripts/hmad-dispatch.sh`, the `exec` verb's agy branch (the codex branch is
unaffected — it delivers its prompt on stdin).

**Uncommitted changes:** none in this repo.

**Workaround in use downstream** (HemaSuite ran all 16 audit cycles on it, prompts 41.7 KB → 75.8 KB,
every one answered):

```bash
agy --dangerously-skip-permissions --print "$(cat <promptfile>)" > raw.md
```

with the assembled prompt's `<REPORT_FILE_PATH>` slot filled, then reading the report file rather
than the last message. Worth keeping in mind: agy's final message on an audit was 540 bytes of
narration ("I have completed the review and written the audit report to the expected file") while the
real 2.9 KB report landed in the report file — exactly the case the h-mad SKILL already warns about
for `exec agy` on an audit phase.

**Related docs:**
- Sender's handoff: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-08-19-feature-71-run-report-seam-restoration__phase5-red-dispatch-next.md`
- h-mad SKILL §"Exit-code dispatch for 5d/5e" and §"Exception — `exec agy` on an audit phase"
