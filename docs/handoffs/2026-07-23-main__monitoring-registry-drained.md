# Handoff — The monitoring registry drained to zero

**Date:** 2026-07-23
**Branch:** main
**Project:** BrightGold70/skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Started from `/handoff read` of the Wave-3/4a closeout and worked the backlog to
exhaustion. **Waves 4b and 4c shipped** (11 skill candidates landed, 1 declined
with reasoning), **J16's paneKey identity join shipped and closed orca#9870
upstream**, and then **every remaining monitoring item was closed**: J1, J2, J3,
J4 (+F8), J5, J11, J12, J13, J17, J18, P1 fixed; J9 disproven. Suite **592 →
666**, zero regressions, every guard mutation-tested. `docs/skill-monitoring.md`
now has **zero `MONITORING` rows** and `docs/skill-candidates.md` has no
unlanded `candidate: yes`. Nothing is in flight; the next session starts from a
clean backlog.

## Key Learnings

- **Three separate tests encoded a filed defect as an acceptance criterion.**
  J17's 8 tests asserted the forwarded selector `repo::<path>` that a real Orca
  runtime rejects; J1's test asserted the create-response handle that the pane
  never has; J2's AC-6.5 asserted the cwd-relative pin path. Each was written
  alongside the bug and pinned it as correct. When a fix "breaks" an existing
  test, check whether the test was pinning the defect before adjusting the fix.
- **Mutation-testing a path-resolution branch overwrote live session state while
  reporting 642 passed** (J18). Stubbing `_pin_file`'s override branch — the
  branch every test uses to redirect writes to a temp path — sent the suite's pin
  writes onto the real `.h-mad/orca-pins.env`. A suite's isolation is itself
  implemented by branches, and mutation testing deletes branches. Guarded now by
  `h-mad/tests/conftest.py`.
- **A tail read of a TUI is not evidence, in either direction.** Three
  independent pollers reported `RESULT=SILENT` for a 61,493 B prompt whose
  complete token was in the full buffer (J13), and `wait` decided idle from a
  6-line tail = 676 of 47,711 bytes (J3). A bigger tail does not help; a tail is
  a slice of one frame however deep. Read `--from-start`.
- **Two filed fix directions were wrong and one command each showed it.**
  `ASSEMBLE: PASS_OVERSIZE` matches `grep "ASSEMBLE: PASS"` and
  `startswith(...)`, so it would have reproduced J12 rather than fixed it; and
  the 49 KB "reviewer cliff" J13's remedy defended against has never reproduced
  for the delivery mode this skill actually uses (five file-indirection prompts,
  53–61 KB, all answered).
- **`orca terminal create`'s `.result.terminal.handle` is a pre-adoption
  placeholder the pane never gets**; `.result.terminal.paneKey` is stable and
  joins to `terminal list`'s `tabId:leafId`. The same join resolves agent
  identity generally — which is why orca#9870 was closable: the field it asked
  for lives in `worktree ps`, not `terminal list`.
- **Draft-07 `format` is annotation-only** unless a checker is passed (so
  `started_ts: "not-a-date"` is valid today), and **`bool` is not an `integer`**
  in JSON Schema though it subclasses `int` in Python. Both would silently make a
  hand-rolled validator disagree with the real one.
- **A one-character flag typo cost 300 seconds.** `wait agy --timeut 2` was
  silently dropped and fell back to the 300 s default — it is what made the first
  RED run of the flag tests time out.
- **`git reset --hard` with uncommitted work destroyed my own implementation
  mid-session.** Recovered only because a mutation-testing backup happened to sit
  in `/tmp`. Commit before any history-rewriting git command; now documented in
  `SKILL.md` §"Editing this skill while a run is in flight".

## Next Steps

The backlog is empty, so these are openings rather than obligations.

1. **Dogfood a real `/h-mad` feature end-to-end on the repaired instrument.**
   Every fix this session was verified in isolation; none has been exercised by a
   full 7-phase run. `launch` (J1), the `size_status` read (J12), full-buffer
   `wait` (J3) and the substrate record (J11) all sit on the Phase-5 path and
   have never run together — `docs/01-plan/h-mad-remediation-sequence.md`.
2. **File the narrower Orca issue offered in the orca#9870 close** — a
   `titleSource: "osc"|"tab"|"assigned"` discriminator on `terminal list`. Only
   worth filing if the adoption case matters: a plain `terminal create` shell is
   absent from `agents[]` (verified), but whether a *human-typed* `codex` in an
   existing shell registers there was never established.
3. **Consider whether `_MiniDraft7` should become the only backend.** It agrees
   with `jsonschema` on every construct and on the live records, and keeping two
   backends means the differential test must keep running —
   `h-mad/scripts/h_mad_state_validate.py`.
4. `[suggested]` **Delete `BrightGold70/hmad-j15-live`** if it is dead — it is
   the only non-`main` branch left and is **unmerged**, so `git branch -d`
   refuses. Confirm before `-D`; it has commits not on `main`.

## Open / Blocked Items

- **`docs/skill-monitoring.md` open items** — status: **none**. Zero `MONITORING`
  rows for the first time; F8 closed via J4, J9 recorded as disproven-cause.
- **`docs/skill-candidates.md`** — status: **drained**. No `candidate: yes`
  remains unlanded; `staged-prompt repair sweep` is DECLINED with reasoning so it
  is not re-litigated.
- **J9's single observed failure** — status: cause unknown, deliberately not
  chased. The run did fail once; the *attributed* cause (probing the real `cmux`)
  is disproven, and it has not recurred in 200+ runs. A future observer should
  re-derive rather than re-apply the remedy that was already in place.
- **`BrightGold70/hmad-j15-live`** — status: unmerged, untouched. Not deleted
  because it holds commits not on `main`.
- **Pre-existing Pyright warning** on `_remove_stray_pin_file`
  (`atexit`-registered, false positive) — status: pre-existing, unchanged.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — paneKey identity (J16), `worktree-rm`
  selector + guard (J17), `launch` handle resolution (J1), repo-anchored pin file
  (J2), full-buffer `_snapshot` (J3), `_unknown_opt` at 11 sites (P1)
- `h-mad/scripts/h_mad_state_validate.py` — bundled `_MiniDraft7` (J4/F8)
- `h-mad/scripts/h_mad_assemble_audit.py` — `size_status` on the verdict line
  (J12), thresholds re-anchored (J13)
- `h-mad/scripts/h_mad_telemetry.py`, `h_mad_state_schema.json` — substrate
  record (J11)
- `h-mad/scripts/h_mad_issue_fix_gate.py` — **new**, Wave 4b
- `h-mad/invariants.base.md` — 4 new Axis-B rules (Waves 4b/4c)
- `h-mad/SKILL.md`, `h-mad/references/{agent-substrate,codex-implementer-prompt,failure-recovery}.md`
- `h-mad/tests/` — `conftest.py` + 4 new test files, ~10 modified
- `docs/skill-monitoring.md`, `docs/skill-candidates.md`,
  `docs/01-plan/h-mad-remediation-sequence.md`, `docs/learnings.md`

**Uncommitted changes:** none — clean, in sync with `origin/main` at `8499673`.

**Agent panes** — did **not** rotate this session (unusual). `codex
term_294ce89e…`, `agy term_0a2de455…`, `PREFLIGHT: PASS` at close. Re-verify
anyway; `launch` can now pin correctly if they are gone.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
hmad-dispatch env                       # assert PREFLIGHT: PASS; now also prints `pin file:`
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q    # expect 666 passed
python3 h-mad/scripts/h_mad_state_validate.py docs/.bkit-memory.json   # stock python3 works now
```

**Related docs:**
- `docs/skill-monitoring.md` — J1–J18 + P1; **zero open**; J6 and J9 disproven
- `docs/01-plan/h-mad-remediation-sequence.md` — Waves 1–4c shipped, Wave 5 moot
- `h-mad/invariants.base.md` — Mutation verification · Incident replay · Test
  discrimination · Assumption verification
- [stablyai/orca#9870](https://github.com/stablyai/orca/issues/9870) — closed as
  completed

## Version History
- v1.0: Waves 4b/4c + full monitoring-registry drain.
