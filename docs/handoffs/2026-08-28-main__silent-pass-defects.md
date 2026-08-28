# Handoff — four defects that all looked like a pass

**Date:** 2026-08-28
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Resumed the inbound HemaSuite handover (`2026-08-28-main__stale-install-and-wire-registry-handover.md`)
and closed all three handed-over items, then fixed the stale-install class the session kept
tripping over. Five commits, all pushed (`b79b036` → `e4340c5`). The suite went from 2 failing to
**2381 passed / 0 failed**, anchors 305/305 across 24 specs, and both installed skills are now
canonical symlinks with the install check extended to cover them. Nothing is in flight and the
action queue is empty — this is a clean stopping point, not a pause.

## Key Learnings

- **A correct `h-mad` symlink vouches for nothing but h-mad.** `~/.claude/skills/h-mad` was a
  symlink into the checkout while `~/.claude/skills/handoff` was a plain directory copied 68 days
  earlier. The copy is what a session actually loads, so the READ-mode fallback-ladder fix
  committed a week before was invisible at runtime and the skill behaved as its June self — while
  `h_mad_install_check.py` reported `INSTALL: PASS` over it.
- **The todo-tools opt-in applies mid-session — no restart.** Writing
  `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` into `~/.claude/settings.json` surfaced
  `TaskCreate`/`TaskGet`/`TaskList`/`TaskUpdate` as deferred tools within the same conversation,
  after an earlier `ToolSearch` in that same session had returned no match. The skill called it a
  "launch option", which cost a resume.
- **A new verdict word can be silently non-blocking across repos.** HemaSuite's pre-push hook
  scores anchor verdicts with an ordered substring `case` whose default arm is *push ALLOWED*. A
  brand-new `ANCHORS_UNCLASSIFIABLE` would have printed the finding and let the push through,
  misreported as broken tooling, until that hook shipped a matching change. Folding into the
  existing `ANCHORS_UNREADABLE` got the same blocking outcome with zero coordination.
- **A red test can disable mutation coverage, not just an assertion.** `out_wait_atomicity.json`
  runs `test_hmad_dispatch.py` as its baseline command, so the two `TestAtomicOutWrite` failures
  made the whole atomic-write spec return `BASELINE_NOT_GREEN` — unrunnable for as long as those
  tests had been red. Measured by stashing the fix and re-running.
- **`hmad-dispatch.sh` cannot be sourced whole.** `main "$@"` sits unguarded at the bottom beside
  `set -euo pipefail`, so sourcing dispatches the *empty* verb, hits the `*)` arm and returns 2 —
  and errexit, re-armed by line 5 inside the caller's own shell, exits the sourcing shell before
  any helper is reachable. `|| true` does not save it. Strip `main "$@"` first, as
  `test_hmad_dispatch_audit_cycle.py` already does.
- **A fixture can make the bug it tests unreachable.** The first `check_siblings()` passed all six
  unit tests and still reported PASS against the real stale copy: it derived the sibling root from
  what the skills link resolves to — the `h-mad` *subdirectory* — and the fixture had put the
  skills and h-mad's `SKILL.md` in one directory. Only running it against the live install caught it.
- **Do not leave a backup inside `~/.claude/skills/`.** A `.handoff.copy-backup-<ts>/` directory
  parked there registered immediately as a duplicate skill. Backups belong outside the skills tree.
- The through-line: three of these were **"it loads, so it looks fine"** — a stale copy that loads,
  a malformed spec that reports clean, a test that sources a file which exits before the helper
  runs. In two of them the fix was already committed and simply not reachable.

## Next Steps

The handed-over queue is empty; these are genuine follow-ups, none urgent. (The
`docs/skill-candidates.md` reconcile that would have been item 1 was done by this handoff's own
scout pass — census reports 0 open `yes` rows.)

1. Consider giving `unclassifiable` its own verdict word once every consumer scores verdicts by
   exit code rather than an ordered substring `case` — `h-mad/scripts/h_mad_mutation_harness.py`
   (search `ANCHORS_UNREADABLE if unreadable or unclassifiable`). Deliberately deferred this
   session; the fold is correct until the consumers change.
2. `[suggested]` Extend `check_siblings()` to the `~/.claude/hooks/` tree the same way, so a hook
   installed as a copy is caught alongside a skill — `h-mad/scripts/h_mad_install_check.py`
   (`_check_hook_link` currently only checks existence, not shape).

## Open / Blocked Items

- **HemaSuite pre-push hook header comment is now incomplete** — status: deferred, not handed over.
  Its header lists the three blocking verdicts and does not say that `ANCHORS_UNREADABLE` also
  covers a file that is not valid JSON at all (as of `e9452d2`). The hook **blocks correctly with
  no change needed** — this is a comment accuracy issue only.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none · file: scripts/git-hooks/pre-push`
  (HemaSuite `6aa00407`). *Handover considered and declined*: there is no claim to release and the
  entire context is one sentence, so a brief would cost more than the fix. Whoever next touches
  that hook should fold it in.
- **Item 3 of the inbound handover — `gate-blindness-hardening` stale claim** — status: closed as
  moot, recorded here so it is not re-opened. The handover said the claim lived in this repo's
  `docs/.bkit-memory.json`; that file does not exist and is gitignored, `.bkit/state/memory.json`
  is a fresh 2026-08-28 session stub with no claim, and HemaSuite has no claim file either. No
  decision is owed.

## Context for Next Session

**Files touched this session:**
- `handoff/SKILL.md` — READ Step 4: the opt-in applies mid-session
- `h-mad/scripts/h_mad_mutation_harness.py` — unclassifiable blocks; `skipped=`/`unclassifiable=` on every summary line
- `h-mad/scripts/h_mad_wire_registry.py` — `pin`/`successor_pin` take a list; per-pin halt reasons
- `h-mad/scripts/h_mad_install_check.py` — `check_siblings()` + `--repo`
- `h-mad/SKILL.md` — multi-pin contract, `SIBLING_*` remedies, registry entries
- `h-mad/tests/test_h_mad_mutation_harness.py`, `test_h_mad_wire_registry.py`,
  `test_hmad_dispatch.py`, `test_h_mad_install_check.py`, `test_h_mad_install_check_docs.py`
- `h-mad/tests/mutation-specs/wire_registry_key.json` (+5), `install_check_siblings.json` (new, 5)

**Outside the repo (not version-controlled — re-check if they look wrong):**
- `~/.claude/settings.json` — added `env.CLAUDE_CODE_ENABLE_TODO_TOOLS=1`; backup at `~/.claude/settings.json.bak-*`
- `~/.claude/skills/handoff` — was a plain directory, now a symlink to `/Users/kimhawk/orca/skills/handoff`
- `~/.claude/.install-backups/handoff.copy-backup-20260828-173431` — the replaced copy; safe to delete
- Deleted local branch `wip/check-anchors-local-4aeee78` (was `4aeee78`, unpushed, recoverable via reflog)

**Uncommitted changes:** none — tree clean. `e4340c5` was the last code commit; this handoff itself lands on top of it, so `main` tips at the `chore(handoff)` commit and is in sync with `origin/main`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
python3 h-mad/scripts/h_mad_install_check.py                 # expect INSTALL: PASS
python3 -m pytest h-mad/tests handoff/tests -q               # expect 2381 passed, ~5 min
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors \
  h-mad/tests/mutation-specs/*.json handoff/tests/mutation-specs/*.json   # expect ok=305
```

**Related docs:**
- Inbound handover this session discharged: `docs/handoffs/2026-08-28-main__stale-install-and-wire-registry-handover.md`
- Prior diagnosis of the todo-tool gap: `docs/handoffs/2026-08-20-main__handoff-read-todolist-fallback.md`
- J43/J44 (the registry key defect multi-pin builds on): `docs/skill-monitoring.md`
- Consuming pre-push hook: `/Users/kimhawk/orca/HemaSuite/scripts/git-hooks/pre-push`
