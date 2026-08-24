# Handoff — Portable time bounds: the `run` verb, since macOS has no `timeout`

**Date:** 2026-08-25
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (h-mad skill)

## Session Summary

The operator surfaced a snippet from another session — *"timeout isn't on macOS. Checking auth
directly."* — and asked how to fix that process in the h-mad skill. Diagnosis reframed the ask:
h-mad **never emitted a `timeout` form anywhere**, so there was no broken command to fix. An agent
improvised `timeout <s> <cmd>`, got 127, and silently degraded to running the same command
**unbounded**. Shipped `hmad-dispatch run --timeout <s> -- <cmd...>` (exposing the private
`_exec_run` watchdog that had existed since `exec` shipped), the prohibition-plus-replacement rule
on all four surfaces that can improvise, and 62 tests. Suite 1730/0. Committed and pushed to
`main` as `81dc213`.

## Key Learnings

- **The 127 is not the hazard; its fallback is.** `timeout: command not found` is loud and
  self-correcting. What follows it is not: the measured reflex is to re-run the same command with
  no bound and narrate it as "checking directly". An unbounded probe does not fail at the deadline,
  it hangs — and in every log h-mad reads (a `--log` tail, `progress`, a transcript) a hang and slow
  work are the same bytes. The rule text therefore had to say *halt*, not merely *don't use
  `timeout`*.
- **A private helper is not a surface.** `_exec_run` was correct, battle-tested, and had five
  internal call sites — and because it had no verb, agents reaching for a time bound found nothing
  and invented something worse. Capability that has no callable name is capability nobody has. This
  is the actual root cause; the missing rule was secondary.
- **"The skill told them to do it wrong" and "the skill gave them nothing to do it right" are
  different defects with different fixes.** A tree-wide grep for a `timeout <n>` command form
  returned **zero hits** across `SKILL.md`, `scripts/`, `bin/`, `hooks/`, `references/`, the prompt
  templates and `tests/`. Establishing that *before* editing turned a hunt for a broken call site
  into a verb + a rule.
- **A prohibition with no replacement reproduces the failure it forbids.** Each of the four rule
  sites names the exact replacement command; the surface-coverage test asserts `run --timeout`
  is present in all four, not just that `timeout` is condemned.
- **The tree-scan guard caught its own author on the first run.** It failed on the literal
  `timeout 30 <cmd>` inside the new function's explanatory comment. A guard that fires on the
  commit that introduces it is a guard that will fire on the next one.
- **`ls -t <dir>` errors on this machine.** `ls` is shimmed to eza, where `-t` takes a `--time
  <FIELD>` value (`modified|changed|accessed|created`), so `ls -t docs/handoffs/` returns
  `error: invalid value ... for '--time <FIELD>'` rather than a listing. Use
  `handoff_paths.py latest` or `find`.
- **Editing a file while a full suite runs against it voids the run.** The first full-suite launch
  was killed mid-flight because a `set -e` cleanup landed in `hmad-dispatch.sh` after it started.
  The only full-suite evidence quoted here (1730/0) is the re-run on final bytes.

## Next Steps

1. **Nothing owed on this work.** `main` == `origin/main` == `81dc213`, tree clean, suite 1730/0.
2. **Live-fire the context-budget advisory in a fresh session** *(carried from
   `2026-08-24-main__registry-zero-j44-j49`, still open)* — `HMAD_CONTEXT_WINDOW=1000 claude`, then
   **any** tool call; the `[H-MAD] Context budget:` line must appear. Confirmation, not owed
   verification — it already fired in-session.
3. **Exercise `audit-cycle` end-to-end once with the 5th `--pass` field** *(carried, still open)* —
   `hmad-dispatch audit-cycle --feature <f> --phase impl-plan --cycle <N> --passes 2 --project-root <root>`.
   Unit-pinned in `tests/test_hmad_dispatch_audit_cycle.py` and mutation-covered, but never run
   against a live dispatch.
4. **[suggested] First real use of `run` inside a dispatched prompt.** The verb is shell-tested
   seven ways and mutation-covered 4/4, but no dispatched agent has yet been observed reaching for
   it instead of `timeout`. The next audit or 5d/5e dispatch that needs a time bound is the
   observation — check the log for `run_timeout` or a clean exit rather than a 127.

## Open / Blocked Items

- **Unverified, not actionable — an archived HemaSuite analysis cites a `timeout` that could not
  have run here as written.**
  `HemaSuite/docs/archive/2026-06/enhancement-consumer-consolidation/…analysis.md:22` reads
  *"on clean `main` (pre-feature) the test hangs identically (`timeout 60` → exit 124/143)"*. On
  this box `command -v timeout gtimeout` returns nothing, so either that ran on a different
  machine, coreutils was installed at the time, or the exit codes were assumed rather than
  observed. **I did not verify it and it needs no action** — it is an archived doc, and the live
  scan below is clean. Recorded because it is corroboration that the improvisation predates this
  session, not because anything is owed.
- **HemaSuite scanned, clean.** `grep -rnE '(^|[^-_[:alnum:]])timeout[[:space:]]+[0-9]+'` over
  `/Users/kimhawk/orca/HemaSuite` `--include='*.sh' --include='*.py' --include='*.md'`, minus
  `--timeout`/`_timeout`/`timeout=`, returned only prose and archive hits — **no live bare-`timeout`
  command form**. No cross-repo follow-up owed. (The h-mad fix reaches that repo automatically
  anyway: `~/.claude/skills` is a symlink into this one.)
- **Monitoring registry: still 0 open.** Not re-counted this session — no item was filed or closed.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — `_cmd_run` (~line 3270) + verb-table entry + header verb list
- `h-mad/SKILL.md` — NEVER-list bullet (§"What you NEVER do")
- `h-mad/references/agent-substrate.md` — `run` row in the verb table, after the `exec` row
- `h-mad/references/codex-implementer-prompt.md` — §"Before You Begin"
- `h-mad/invariants.base.md` — new §"Portable time bounds" (spliced into every audit prompt)
- `h-mad/tests/test_h_mad_portable_timeout.py` — new, 62 tests

**Uncommitted changes:** none — all six committed in `81dc213` and pushed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
/opt/anaconda3/bin/pytest h-mad/tests/ -q -p no:randomly   # 1730 passed, 246s
# the new verb, live:
h-mad/scripts/hmad-dispatch.sh run --timeout 2 -- sleep 30   # -> 124 + run_timeout on stderr
```

**Verification evidence (so it need not be re-derived):**
- Premise confirmed on this box: `command -v timeout gtimeout` → nothing, exit 1.
- Full suite on final bytes: **1730 passed, 0 failed, 246.75s**.
- Mutation-tested 4/4 killed — process-group kill → bare `$pid` (grandchild orphaned to init, the
  wrapper then hung 60s); `return 124` → `return 1`; the `run_timeout` stderr line removed;
  `gtimeout` dropped from the SKILL.md rule.

**Related docs:**
- `h-mad/references/agent-substrate.md` §verb table — the `run` row is the reference entry
- `h-mad/invariants.base.md` §"Portable time bounds" and §"No new external dependency" (the
  new section leans on the latter: a CLI you must install separately is a new external dependency)
- Prior handoff: `docs/handoffs/2026-08-24-main__registry-zero-j44-j49.md` (Next Steps 2 and 3
  carried forward above)
