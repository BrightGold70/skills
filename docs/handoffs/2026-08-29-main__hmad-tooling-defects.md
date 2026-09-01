# Handoff — two h-mad tooling defects found during a live H-MAD run

**Date:** 2026-08-29
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · feature/202-guideline-claim-like-visibility · session f419d046-63a7-4e32-bac0-040f9bcabb04
**Taken-Over-By:** skills · main · session unknown · backfilled 2026-09-01 — the brief records its own closure: `90fce10`, `e87fe24`, merged `2b569da` -- all three verified present in git

## Session Summary

Two defects in `h-mad/scripts/` were found by hitting them, not by reading code: both produced
confident, real-looking verdicts that were wrong, and both cost a diversion mid-run. They are handed
over because they belong to this repo, not to the HemaSuite feature that tripped them — that feature
(#202 `guideline-claim-like-visibility`) is now merged to `main` and closed at Phase 7, so nobody in
that lane is coming back to these. Neither is claimed: both `.bkit-memory.json` files under this repo
have an empty `orchestrator_state`, verified, so there is nothing to release and nothing to force.

## Key Learnings

- **Both defects fail *plausibly*.** Neither errors. One names a real halt reason about a real
  feature; the other returns a real sha on the right branch. That is why they cost time — the output
  is verdict-shaped, so the reflex is to believe it and go investigate the thing it names.
- The wire-registry one is a **nested-project** defect specifically: it is invisible in a
  single-project repo, because there the cwd *is* the git root and the two paths coincide.

## Next Steps

**All three are done — closed out 2026-08-29 in `90fce10`, `e87fe24`, merged as `2b569da`.** One
premise below did not survive verification: Next Step 2 asks for whatever in the Phase-5 flow wrote
the three keys, and **there is nothing to find**. No code in this repo writes them — the only
`--set` key any script or document passes is `codex_status`, which is declared. They were
hand-written, which prose alone governed, so the enforceable fix landed at the guard instead (see
that item for what was actually done). Left in place below as written, because the analysis that
found the defects is still the best account of them.

1. **`h_mad_wire_registry.py verify` — derive the repo root instead of defaulting `--repo` to cwd.**
   `_registry_base_path(registry, repo)` computes the base-registry path relative to `--repo`, then
   `load_base()` runs `git show <base>:<path>`. Git resolves that path from the **git root**, not
   from `--repo`. In a monorepo sub-project those differ, so the base and HEAD registries are two
   different files and the comparison is meaningless.
   Reproduce (HemaSuite at `911a377f` or later):
   ```bash
   cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
   python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_registry.py verify \
     --registry .h-mad/wires.jsonl --base 7487b30f --rootdir . --testpath tests \
     --python "$(pwd)/.venv/bin/python"
   # WIREREG: FAIL … undeclared_removals=5   (names guideline-seeder-config-plumbing
   #                                          Tasks 7/8/9/11/12 — a feature with ZERO
   #                                          records in the file being compared)
   # add --repo /Users/kimhawk/orca/HemaSuite  →  WIREREG: PASS registered=23 verified=23
   ```
   Root cause confirmed by hand: the repo-root `.h-mad/wires.jsonl` at that base holds 6 records, 5
   of them `guideline-seeder-config-plumbing`; the HPW registry holds 23 and zero of that feature.
   Suggested fix: resolve the root from `git rev-parse --show-toplevel`, or refuse when `--repo` is
   not a git work tree — the same refusal `handoff_paths.py --repo` already makes, and for the same
   reason.
2. **`h_mad_state_write.py` / the Phase-5 flow — stop writing undeclared keys, or the record becomes
   unwritable.** A prior #202 session wrote `current_step`, `phase5_baseline` and `phase5_progress`
   into `orchestrator_state`. `h_mad_state_schema.json` is `additionalProperties: false`, so
   `classify()` returned `historical` and **every subsequent write was refused** — the claim could be
   neither released nor taken, on a feature halted mid-Phase-5. The guard behaved correctly; the
   writer of those keys did not.
   ```bash
   # grep across this checkout and the consuming project: ZERO readers of all three keys
   grep -rn "current_step\|phase5_baseline\|phase5_progress" /Users/kimhawk/orca/skills
   ```
   They were write-only notes whose content was already duplicated in the handoff doc and git log, so
   the fix taken downstream was to strip them (verdict returned to `strict`), **not** to widen the
   schema — adding schema surface for keys nothing reads is the wrong direction. What is owed here is
   finding whatever in the Phase-5 path wrote them and stopping it; otherwise the next live feature
   gets bricked the same way.
3. `[suggested]` **Consider a regression test for each**, since both are the kind that pass silently:
   a nested-project fixture for (1), and a state record carrying an undeclared key for (2) asserting
   the write is refused *and* that the refusal names the offending keys.

## Open / Blocked Items

- **#48 — ad-hoc state fields brick the orchestrator record** — status: **DONE** (`90fce10`). Worse
  than described: claim, release AND halt-recording were all refused, and the refusal named the tier
  rather than the keys. The refusal now names them and separates introduced from pre-existing;
  `--drop-undeclared` is the sanctioned repair. No Phase-5 writer existed to stop — see Next Steps.
  · repo: `/Users/kimhawk/orca/skills` · branch: `main` · worktree: `/Users/kimhawk/orca/skills`
  · touched: `h-mad/scripts/h_mad_state_write.py`, `h-mad/scripts/h_mad_state_schema.json`,
    `h-mad/scripts/h_mad_state_validate.py`, and whatever in the Phase-5 flow authored the keys
  · evidence: the three key names and their full values are quoted in the HemaSuite session
    transcript of 2026-08-29; the downstream strip is described in Next Step 2 above.
- **#49 — `verify` compares two different registries in a nested project** — status: **DONE**
  (`e87fe24`). Resolved against `git rev-parse --show-toplevel`, so the default `--repo` is now
  correct with no operator action. A registry outside the work tree is refused rather than silently
  compared against `DEFAULT_REGISTRY` — the same defect by a shorter route, found while fixing this.
  · repo: `/Users/kimhawk/orca/skills` · branch: `main` · worktree: `/Users/kimhawk/orca/skills`
  · touched: `h-mad/scripts/h_mad_wire_registry.py` (`verify`, `_registry_base_path`, `load_base`)
  · reproduce: the command block in Next Step 1, against HemaSuite `911a377f` or later.
- **Nothing is claimed** — both `.bkit-memory.json` files under this repo
  (`clinical-statistics-analyzer/docs/`, `hematology-paper-writer/docs/`) have an empty
  `orchestrator_state`. Checked, not assumed. Do not reach for `--force` on anything here.

## Context for Next Session

**Files touched this session:** none in this repo. This session worked in HemaSuite; the only
artifact it leaves here is this brief.

**Uncommitted changes:** none in this repo (`main` clean, in sync with `origin/main` at `2b3b4f0`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
# start with Next Step 1 — it has a one-command reproduction
```

**Related:**
- The run that found both: HemaSuite `feature/202-guideline-claim-like-visibility`, merged to `main`
  as `911a377f`. Its report is
  `hematology-paper-writer/docs/archive/2026-08/guideline-claim-like-visibility/guideline-claim-like-visibility.report.md`,
  whose "What To Improve Next Time" names both defects.
- A third, already fixed here: `2b3b4f0` — a fully-acknowledged gate section is clean, not
  off-template. That was the bug capping `## Acknowledged-not-fixed` at one bullet per section, and
  it is the reason #202 burned 41/43/34 audit cycles.
