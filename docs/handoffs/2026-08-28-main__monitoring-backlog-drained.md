# Handoff — monitoring backlog drained to zero

**Date:** 2026-08-28
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Started as a two-item handover (port the mutation-anchor pre-push guard into h-mad; fix the
`find` fail-open in `handoff/SKILL.md`) and turned into a full drain of the monitoring backlog.
Both handover items shipped, then J41/J34/J37/J38/J39/J40/J43/J44/J45/J46 were closed and J35/J36
were closed as refuted-or-doctrine. **No `J` row is left `MONITORING` (43 rows), and
`candidate: yes` is now 0** (census: `OPEN=8`, all `maybe`). Twelve commits, all pushed; suite grew
2190 → 2270 passing. The through-line: **four carried premises were false on re-probing**, and
premise-checking changed the work in four of nine items.

## Key Learnings

- **Four of nine carried premises were false, and each was false in a way that would have
  produced the wrong fix.** J41 claimed `git merge-base` yields the 5c sha (it yields 5c's
  *parent*, off by the impl-plan commit; the original "verification" re-ran the command that
  produced the value — circular, no control). J34 claimed the path bug was "survivable because it
  prints commands" (true for `--out`/`--log`, false for `--prompt`, which the tool *writes* — it
  halts). J35 blamed the `progress` wrapper (all five states return 0; the exit 1 came from
  `| grep -q IDLE` on a LIVE log). The last candidate row cited its sibling as "DECLINED as
  not-codable" (it reads `candidate: maybe`). Re-probe before fixing; the registry's fix direction
  is a hypothesis.
- **Adding a verdict word silently un-guarded a hook I had built earlier the same session.**
  Splitting `ANCHORS_UNREADABLE` out of `ANCHORS_DRIFTED` (J37) made the pre-push hook — which
  matched only `*ANCHORS_DRIFTED*` — fall through to its catch-all and print
  *"no ANCHORS_* verdict … Push ALLOWED"* for a spec whose target file was deleted: it allowed the
  push **and** misreported a real verdict as broken tooling. Grep every consumer before adding a
  token to a contract.
- **I fixed a race by adding a race, and only the FULL suite saw it.** `_write_out_atomic` keyed
  its temp on `$$`, which is constant across every `--out` a single wrapper invocation writes;
  `audit-cycle` writes one per pass, so two writes shared a temp and it **silently lost its p1
  report**. The targeted tests passed. Now `mktemp`.
- **Atomicity has no externally observable trace that `cp` + `rm` does not also produce.** A
  mutation swapping `mv` for `cp; rm` left every behavioural assertion green — content lands, no
  temp remains, either way. The guard had to become structural (the helper must name `mv`). This
  is the rare case where asserting on source is right, not lazy.
- **A tidy fixture let a mutation survive.** The prompt-echo fixture opened with `emit ASSESSMENT:
  …`, which never matched the line-anchored regex — one match where the test needed two, so
  first-vs-last was untestable. The surviving mutant is the only thing that exposed it.
- **Two ad-hoc census parsers returned false counts; the census was right both times.** One missed
  the last open candidate entirely. `docs/skill-candidates.md` terminal markers sit on the
  *continuation* line — count with `handoff/scripts/skill_candidates_census.py`, never a grep.
- **`--release` guarded nothing, so `--release` + `--claim` took a live owner's feature with no
  `--force` anywhere** (J45). The fix could not simply refuse a live owner: the handoff skill's own
  HANDOVER step releases its *own* live claim, so a naive guard would have taught the `--force`
  reflex it exists to prevent. It splits on identity, and the refusal message names `--session-id`,
  not `--force` — that message is mutation-pinned as a guard in its own right.
- **The wire registry silently performed the exact removal its schema forces you to declare**
  (J43). `register` upserted on bare `id` = `"Task N"`, which restarts at 1 per feature, and
  `compare` keyed the same way so the successor *masked* the eviction. 1 of 7 records lost here,
  **7 of 19 in HemaSuite**.

## Next Steps

1. First real use of the two new tools will be their live exercise — neither has run in anger:
   `report-wait <out> --no-done-marker` (`h-mad/scripts/h_mad_report_wait.py`) and
   `h_mad_archreview_cycle.py stage|score`.
2. Consider wiring `h_mad_archreview_cycle.py` into a `hmad-dispatch` verb — it is currently
   script-only, unlike `audit-cycle` which has one. Deliberate for now (the dispatch half is the
   operator's), but revisit if the two-step invocation proves to be friction.
3. `[suggested]` Work the 8 remaining `candidate: maybe` rows — run
   `python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md` to list them;
   none is `yes`, so all are judgement calls rather than queued work.

## Open / Blocked Items

- **None blocking.** All J rows closed; all claims released (0 of 18 features owned).
- `docs/skill-candidates.md` — 8 `candidate: maybe` rows remain open. Status: deferred by
  triage, not blocked.
- **HemaSuite — nothing owed by this session.** The 7 evicted wire records were restored and
  landed on `origin/main` as `024bec25`. The duplicate `c7c9a767` on
  `feature/clgcc-claim-like-guideline-citation-coverage` is redundant and resolves on merge; that
  session has since continued past it. `repo: /Users/kimhawk/orca/HemaSuite · branch: main
  (pushed) · worktree: none`.

## Context for Next Session

**Files touched this session:**
- `h-mad/git-hooks/pre-push`, `h-mad/git-hooks/install.sh` (new)
- `h-mad/scripts/h_mad_baseline_sha.py`, `h_mad_archreview_cycle.py` (new)
- `h-mad/scripts/h_mad_wire_registry.py`, `h_mad_state_write.py`, `h_mad_ab_dispatch.py`,
  `h_mad_assemble_tdd.py`, `h_mad_mutation_harness.py`, `h_mad_report_wait.py`, `hmad-dispatch.sh`
- `h-mad/SKILL.md`, `h-mad/invariants.base.md`, `handoff/SKILL.md`
- `docs/skill-monitoring.md`, `docs/skill-candidates.md`
- 6 new mutation specs, 5 new test files

**Uncommitted changes:** none (tree clean, `main` == `origin/main` at `d03c816`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git log --oneline -12
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md   # 8 maybe, 0 yes
./h-mad/git-hooks/pre-push origin none </dev/null                             # anchors clean
```

**Related docs:**
- `docs/skill-monitoring.md` — J34–J46, all closed
- `docs/05-review/features/wire-registry-feature-scoped-key.archreview.md` — the one 6a-prime run
- `docs/handoffs/2026-08-27-main__mutation-anchor-pre-push-hook.md` — the inbound handover
