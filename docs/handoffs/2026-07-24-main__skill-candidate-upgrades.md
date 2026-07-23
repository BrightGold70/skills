# Handoff — Promoted skill candidates into h-mad + handoff, fixed learn.py ergonomics

**Date:** 2026-07-24
**Branch:** main
**Project:** BrightGold70/skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Upgraded both skills from the open `docs/skill-candidates.md` backlog, then fixed
a recurring `learn.py` friction the user flagged. Shipped: **3 Axis-B rules**
(Regression provenance, Both halves of a doc change, Reimplementation parity) +
the **close-a-filed-defect playbook** in h-mad `SKILL.md`; **`hmad-dispatch ask`**
(the rec-12+ send→wait→read scrape verb, live-dogfooded against agy); the
**handoff `INDEX.md` anchor fix**; and **`learn.py --trim`** so an over-200-char
kernel saves in one step instead of an eyeball-retry loop. Suite 678 → **678
h-mad** (net; ask added 7, size fixture recalibrated) + handoff **17**. All
merged to `main`, pushed, clean. Both skill backlogs are now essentially drained.

## Key Learnings

- **Almost every "improve X" here was really "the tests pin the old X".** The
  learn.py word-boundary test passed under mutation twice — first the assertion
  was vacuous (`s.startswith(body)` is true for any prefix), then the *data* was
  (6-char words aligned so a naive cut also hit a boundary). Fixing the assertion
  was not enough; the data had to force a mid-word cut (3-char words). Mutation
  caught both; a green suite hid both.
- **`dispatch` was already an Orca orchestration verb** (agent + task_id, the
  fanout path). The scrape-path combo needed a new name — `ask`. Three dispatch
  paths now: `dispatch`+`await` (task), `report-wait` (file), `ask` (screen
  scrape). `ask`'s STDOUT is *only* the reply buffer; send/wait chatter goes to
  stderr, so it pipes straight into `h_mad_extract_verdict.py`.
- **Every base rule is paid for by every audit prompt.** The 3 new
  `invariants.base.md` rules grew the rubric ~2.8 KB and pushed the audit-size
  fixture past its band — recalibrated 2200/2300 → 2000/2200. This is the J13
  dynamic; watch it if the rubric keeps growing.
- **`--trim` cuts the tail, and kernels often put the punchline last** — so the
  SKILL note is explicit: rewrite tighter when the payoff is at the end; `--trim`
  only when the tail is expendable. The tool never silently truncates — the plain
  rejection surfaces the trim as a paste-ready suggestion so the caller decides.
- **The candidate backlog needed the same premise-check as the monitoring
  registry.** Three `skill-candidates.md` rows described work that had already
  shipped (assembler `3f8ae83`, content-probe superseded by J16, snapshot-guard
  by J18) — verified against code before flipping, not on the label.

## Next Steps

Both backlogs are near-empty; these are openings, not obligations.

1. **Dogfood `ask` inside a real `/h-mad` audit cycle.** It is unit- and
   live-verified in isolation but has never driven an actual Phase-5 review
   dispatch end to end — `h-mad/scripts/hmad-dispatch.sh` (`_cmd_ask`),
   `docs/01-plan/h-mad-remediation-sequence.md`.
2. **Decide the two remaining `yes` candidates.** `close-a-filed-defect cycle`
   landed; still open at rec ≥3: nothing — the top open rows are now `maybe`
   ("already the /h-mad skill"). Re-scout only if a fresh recurrence appears.
   `docs/skill-candidates.md` header table lists the live ones.
3. `[suggested]` **Consider raising the 200-char learn cap to ~240** if `--trim`
   proves it is still too tight in practice — the user said "almost always"
   needed trimming. `handoff/scripts/learn.py:142` region; would touch the arg
   help + the two `SKILL.md` `≤200` templates.

## Open / Blocked Items

- **`docs/skill-candidates.md`** — status: drained of actionable items. Open rows
  are `maybe` and mostly describe the /h-mad skill that exists; no `candidate:
  yes` with rec ≥3 remains unlanded.
- **`docs/skill-monitoring.md`** — status: still zero `MONITORING` rows (from the
  prior session); nothing re-opened.
- **`BrightGold70/hmad-j15-live`** — status: unmerged, untouched. Holds commits
  not on `main`; not deleted.
- **learn 200-char cap** — status: friction reduced, not removed. `--trim` +
  suggestion make it one-shot; the limit itself is unchanged (deliberate, but see
  Next Step 3).

## Context for Next Session

**Files touched this session:**
- `h-mad/invariants.base.md` — 3 rules (Regression provenance, Both halves,
  Reimplementation parity)
- `h-mad/SKILL.md` — `## Working a skill-monitoring item` playbook; `ask` in the
  verdict-reading block (fixed a residual `--lines 200` tail)
- `h-mad/scripts/hmad-dispatch.sh` — `_cmd_ask` verb + table entry
- `h-mad/references/agent-substrate.md` — `ask` verbs-table row
- `h-mad/tests/` — `test_hmad_dispatch_ask.py` (new), invariants/preflight/assemble tests
- `handoff/SKILL.md` — INDEX.md anchor rule; `--trim` notes in LEARN + WRITE blocks
- `handoff/scripts/learn.py` — `_trim_to`, `--trim`, `_build_parser` extraction
- `handoff/scripts/test_learn.py` — new, 7 tests
- `docs/skill-candidates.md` — verdict reconciliation + status legend + header table
- `docs/learnings.md` — ask verb, --trim ergonomics

**Uncommitted changes:** none — clean, in sync with `origin/main` at `50232de`.

**Live `~/.claude/handoffs/INDEX.md`** was repaired this session (stray mid-file
header removed, canonical preamble added) — user-global, not committed.

**Agent panes** — `codex term_294ce89e…`, `agy term_0a2de455…`, `PREFLIGHT: PASS`
at close; `ask` dogfood used agy and left it clean. Re-verify before reuse.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
hmad-dispatch env                       # assert PREFLIGHT: PASS
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ handoff/scripts/ -q   # expect 678 + 17
# try the new verb:  hmad-dispatch ask agy <promptfile> --out /tmp/reply.txt
```

**Related docs:**
- `docs/skill-candidates.md` — header table lists open candidates, verdict legend
- `h-mad/invariants.base.md` — 15 Axis-B rules now (12 prior + 3 this session)
- `h-mad/SKILL.md` §Working a `skill-monitoring` item — the defect-closing loop
- `docs/handoffs/2026-07-23-main__monitoring-registry-drained.md` — the session
  that produced these candidates

## Version History
- v1.0: skill-candidate upgrades + learn.py --trim.
