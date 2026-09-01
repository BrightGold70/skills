# Handoff — mutation-anchor pre-push hook (ported from HemaSuite)

**Date:** 2026-08-27
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** /Users/kimhawk/orca/HemaSuite · main · session 676e7f12-45f5-4a38-b13b-557f08a45f5d
**Taken-Over-By:** skills · main · session unknown · backfilled 2026-09-01 — shipped -- `h-mad/git-hooks/pre-push` runs `--check-anchors` and is symlinked live at `.git/hooks/pre-push`

## Session Summary

A working mutation-anchor pre-push guard was built and shipped in **HemaSuite** today
(`58a81732`): `scripts/git-hooks/pre-push` + `scripts/git-hooks/install.sh`. It closes the one
gap `anchor-precheck-phase-5e-wiring` deliberately does not cover — drift introduced by an
ordinary refactor commit that never goes through an h-mad Phase-5e run. Ownership of
**generalising it into the h-mad skill, and installing it in this repo**, moves here. Nothing was
claimed for it (oracle: `start_fresh`), so there is nothing to release and nothing to force.

A second, unrelated item is handed over with it: the handoff skill's own HANDOVER/TAKEOVER
`find … 2>/dev/null` snippet **silently fail-opens in this environment**, reporting "nothing is
claimed" when a state file exists. Found by executing this handover against the very command the
skill prescribes.

## Key Learnings

- **The `find` snippet in `handoff/SKILL.md` fail-opens here, and the mechanism is not the one the
  skill documents.** An `rtk` hook rewrites bare `find`; `rtk find` refuses compound predicates —
  `rtk: rtk find does not support compound predicates or actions (e.g. -not, -exec). Use 'find'
  directly.` — and writes that refusal to **stderr**, which `2>/dev/null` discards. Result: empty
  output, `rc=1`, and Step 2 concludes "no state file — nothing is claimed" and skips the release.
  Reproduced on this machine: the same predicate with `command find`, or piped to `wc -l`, returns
  the 3 real hits; the prescribed form returns 0. The skill already warns about a `**`-glob
  fail-open — this is the same outcome via a different cause, and the `2>/dev/null` is what makes
  it silent. It bit this handover: the first probe reported "no state file", which was false.
- **The push boundary is genuinely uncovered here.** `anchor-precheck-phase-5e-wiring` (`713f9ad`)
  made the sibling sweep an obligation *inside a mutation run*, and `--check-anchors` (`e0dd87b`)
  gave it a standalone diagnostic. Neither fires on `git push`. Verified: this repo's
  `/Users/kimhawk/orca/skills/.git/hooks` has **no** non-sample hook and `core.hooksPath` is unset,
  while 17 specs sit under `h-mad/tests/mutation-specs/`.
- **Score the guard on the `ANCHORS_*` verdict line, never on `$?` alone.** The HemaSuite hook does
  this deliberately: a missing verdict line means the harness broke, which must warn and **allow**
  the push. Only a real `ANCHORS_DRIFTED` blocks. Blocking every push when the tooling is missing is
  a worse failure than missing one drift.
- **`git rev-parse --git-common-dir` returns a RELATIVE `.git`.** With `-C <other-repo>` it still
  prints `.git`, so `ls "$(git -C "$D" rev-parse --git-common-dir)/hooks"` lists the *caller's*
  hooks and silently answers a question about the wrong repo. It reported "the skills repo already
  has the hook installed" — false. Use `--path-format=absolute` (git ≥ 2.31); the installer does.
- **`git rev-parse --short` accepts exactly one revision.** `git rev-parse --short A B` fails with
  `fatal: Needed a single revision`, which reads as "ref B does not exist". Cost a phantom
  "`origin/main` tracking ref is missing" divergence in the same session.
- Two portability bugs the installer hit and now avoids: `[ "$X" -eq 1 ] && exit 0` aborts the whole
  script under `set -e` when the test is false, and `for arg in "$@"` errors under `set -u` on
  bash 3.2 (macOS `/bin/bash`).

## Next Steps

1. **Port the hook into the h-mad skill, parameterised.** Source of truth is HemaSuite `58a81732`:
   `/Users/kimhawk/orca/HemaSuite/scripts/git-hooks/pre-push` (61 lines) and `install.sh` (103).
   The single thing that must change is the spec directory — the HemaSuite copy hardcodes
   `$REPO/hematology-paper-writer/docs/mutations`, this repo needs `h-mad/tests/mutation-specs`.
   Prefer discovery (any dir holding `*.json` the harness accepts) or a config key over a second
   hardcoded path; a per-project fork of this file is how the two copies drift apart.
2. **Install it in this repo and verify both directions** — `.git/hooks` here is empty, so 17 specs
   are unguarded at push time:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json`
   (expect `ANCHORS_OK`, exit 0). Then prove the reject direction with a deliberately corrupted
   copy of a spec before trusting the guard — a hook that cannot fail is not a guard.
3. **Fix the `find` fail-open in `handoff/SKILL.md`** — two sites prescribe it: §"HANDOVER mode"
   Step 2 and §"Take over handed-over work" point 1. Minimum fix: drop `2>/dev/null` so the refusal
   is visible, or use `command find`. Better: make "found nothing" and "the command failed"
   distinguishable, since they lead to opposite correct actions — the same asymmetry the skill
   already enforces for the worktree-comment read.
4. **[suggested] Decide whether the hook belongs in `h-mad/hooks/`** beside `h-mad-tdd-gate.sh` and
   `h-mad-advisor-warn.sh`, or in a new top-level `git-hooks/`. Those two are Claude Code hooks, not
   git hooks — same word, different contract — so co-locating them may be more confusing than
   separating them.

## Open / Blocked Items

- **The port itself** — status: not started, unclaimed. The oracle returned `start_fresh` for
  `mutation-anchor-pre-push-hook`; no record exists in
  `/Users/kimhawk/orca/skills/docs/.bkit-memory.json`, so claim it normally (plain `--claim`,
  never `--force`).
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills` ·
  source: `/Users/kimhawk/orca/HemaSuite/scripts/git-hooks/` @ `58a81732`
- **`gate-blindness-hardening` holds a stale claim** — status: pre-existing, NOT touched by this
  handover. `owner_session_id: session_01RGtJc4nHZmhZu6nYkG5Ksa`, heartbeat `2026-08-06T00:50:32Z`
  (21 days). It is the only owned feature of 15 in the state file. Releasing someone else's claim
  was not part of this transfer; flagging it so it is a decision rather than a surprise.
- **Whether `h_mad_wire_registry.py` still exists** — status: unverified, relevant to a separate
  HemaSuite-side todo (`Task 15 registry multi-pin support`). It is **not** in
  `h-mad/scripts/`; that todo may name a file that has been renamed or removed. Re-probe before
  acting on it. Not handed over here.

## Context for Next Session

**Files touched this session:** none in this repo — this brief is the only write. All code lives in
HemaSuite:
- `/Users/kimhawk/orca/HemaSuite/scripts/git-hooks/pre-push`
- `/Users/kimhawk/orca/HemaSuite/scripts/git-hooks/install.sh`

**Uncommitted changes:** none in this repo (tree was clean at handover).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short                       # expect clean
python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py \
  --check-anchors h-mad/tests/mutation-specs/*.json     # baseline: expect ANCHORS_OK
cat /Users/kimhawk/orca/HemaSuite/scripts/git-hooks/pre-push
cat /Users/kimhawk/orca/HemaSuite/scripts/git-hooks/install.sh
```

**Verification already done on the HemaSuite copy** (re-do it here after the port; do not inherit
the result):

| Case | Observed |
|---|---|
| clean tree, direct invoke | exit 0, silent |
| injected drifted spec, direct | exit 1, names the spec |
| `git push --dry-run`, drift present | `error: failed to push some refs` |
| `git push --dry-run`, anchors clean | exit 0, `* [new branch]` |
| installer re-run | `already installed` (idempotent) |
| foreign `pre-push` present | backed up to `pre-push.bak.<ts>`, content preserved |
| `--uninstall` on a foreign hook | `skipped: not our symlink — left in place` |
| `core.hooksPath` set | refuses with explanation |

**Related docs:**
- `h-mad/SKILL.md:392` and `:1669` — `--check-anchors` contract, `ANCHORS_*` tokens, exit codes
- `docs/archive/2026-08/anchor-precheck-phase-5e-wiring/` — the in-run sweep this complements
- `docs/skill-candidates.md:666-667` — the originating candidate row and its LANDED note
- HemaSuite `docs/handoffs/2026-08-27-fix-mutation-anchor-drift__issue-46-shipped-anchors-repaired.md`
  — the 13-anchor repair that motivated the hook
