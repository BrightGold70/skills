# Handoff — Wave 2 shipped: preflight-signal-discipline

**Date:** 2026-07-23
**Branch:** main
**Project:** BrightGold70/skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Wave 2 of `docs/01-plan/h-mad-remediation-sequence.md` shipped end-to-end as `preflight-signal-discipline`:
merged to main at `787aecf`, 100% match rate (26/26 ACs), suite 498 → **530 passed**. `hmad-dispatch env`
now emits a canonical `PREFLIGHT: PASS|FAIL [stale=…] [conflict=…]` token with the exit code untouched,
`SKILL.md` obliges an orchestrator to assert it (and `ASSEMBLE: PASS`) before dispatching, and J7 is
closed — pinning agents and running the suite are no longer mutually exclusive. Two defects surfaced
along the way (J8's root cause, J10 newly filed) and were folded into Wave 4. Nothing is blocked;
Wave 3 (the dogfood run) is next and is the actual test of what this wave shipped.

## Key Learnings

- **A sentinel that is a *valid* value cannot be told from real data downstream.** J8 —
  "`elapsed_min` ≈ 56 years in every telemetry row" — was filed as a parse failure. It is not:
  `h_mad_state_write.py:138` reads `record["started_ts"] = started_ts or "1970-01-01T00:00:00Z"`, so the
  *stored* value is the epoch and the reader is fine. It read as "the reader must be broken" for weeks
  precisely because the sentinel parses cleanly. Diagnosed only because this feature happened to pass
  `--started-ts` explicitly and produced the one sane row (`110.3m`) — an accidental controlled experiment.
- **RED tests fix the contract; adapt the implementation to them, not the reverse.** Codex's Task-1 tests
  consumed `_NO_PIN_FILE` via `.is_absolute()` / `.parents` / `.exists()`, pinning it as a `Path`. The
  design had specified `os.path.join`, which returns a `str` and would have raised `AttributeError`. The
  5d reviewer proposed casting *inside the tests* because the impl-plan said so — that inverts TDD by
  treating the plan as authoritative over the test.
- **A review's verdict is worth less than its reasoning — verify the premise before acting.** Two of five
  review findings were accepted in substance but rejected in prescribed direction. 6a-prime cycle 1 held
  that `hmad-dispatch send` is mechanically unguarded; verified false (`terminal_handle_stale`, rc=1,
  nothing sent — shipped `912b93a`). Putting the correction back to the reviewer got it accepted in cycle 2.
- **Watch for guards that pass *vacuously*.** Several Task-2 ACs ("no `PREFLIGHT:` line when no substrate",
  "a FAIL line never contains `unresolved=`") were trivially true because no `PREFLIGHT` line existed yet.
  One was written as `for line in …: if line.startswith("PREFLIGHT: FAIL"): assert …` — it would keep
  passing forever if the implementation ever stopped emitting FAIL. Assert the thing **exists** before
  asserting what it lacks.
- **Label guards explicitly in refactor-shaped RED dispatches.** "Every new test must FAIL" is wrong when
  some tests are regression guards; given that instruction Codex has previously bolted on assertions to
  manufacture failures. Stating the expected split up front (3 fail/2 pass, then 12/3) and saying
  "all-failing means you over-strengthened the guards" produced exactly the intended counts both times.
- **Prove a regression test discriminates before keeping it.** The two 6a-prime fixes were temporarily
  reverted to confirm the new tests fail against the old behaviour. A regression test that passes against
  the code it was written to catch is decoration.
- **A test inside a suite cannot honestly assert a property *of* that suite.** AC-6.2 ("pass/fail counts
  identical with and without the pin file") was deliberately excluded from unit tests and verified by
  measurement instead — and named as such in the spec, design and impl-plan rather than covered by a test
  that looks like coverage and is not.
- **Verify pinned API against the actual file, not a sibling.** The first Task-1 dispatch named
  `REPO_ROOT`/`SKILL_DIR`, carried over from `test_h_mad_audit_conditionals.py`; `test_hmad_dispatch.py`
  defines `SKILL`/`WRAPPER`/`STUBS`. Codex returned `NEEDS_CONTEXT` and left the tree clean instead of
  inventing a plausible equivalent — the "stop, don't improvise" instruction paying for itself.
- **A measurement harness can produce false negatives.** The AC-6.2 A/B first compared whole pytest summary
  lines including elapsed time (`11.75s` vs `11.57s`) and reported a failure that did not exist. Compare
  the counts, not the line.

## Next Steps

1. **Run Wave 3 — the dogfood `/h-mad` run.** It is the actual test of FR-4/FR-5, which shipped as protocol
   with no mechanical enforcement. See `docs/01-plan/h-mad-remediation-sequence.md` §Wave 3. Treat it as the
   verification of Wave 2, not a formality.
2. **Delete the merged feature branch** — `git branch -d feature/191-preflight-signal-discipline` (merged at
   `787aecf`; still present locally).
3. **Wave 4 when Wave 3 lands** — candidates batch via worktree fanout, now also carrying J8 and J10. Both
   are diagnosed to a line and neither depends on Wave 3, so they can be pulled forward if the dogfood run
   slips: `docs/01-plan/h-mad-remediation-sequence.md` §Wave 4, "Defects → scripts".
4. **J8 is a one-line fix** when Wave 4 starts — `h_mad_state_write.py:138`, default to `now(UTC)` instead of
   the epoch. Wave 4's done-when now requires a plausible `elapsed_min`, so a row reading ~56 years is the
   signal it did not land.

## Open / Blocked Items

- **FR-4/FR-5 are protocol, not machinery** — status: deliberate carry. Nothing enforces that an
  orchestrator asserts `PREFLIGHT: PASS` / `ASSEMBLE: PASS`; 6a-prime cycle 1 confirmed this is a real
  residue. Wave 3 is the exercise.
- **The CONFLICT case is unguarded at `send`** — status: open, narrower than the original hazard. `send`
  refuses a *stale* handle (`912b93a`), but two agents resolving to one **live** handle is undetectable
  there; only the protocol read catches it.
- **J8 (`started_ts` epoch default)** — status: root cause found, unfixed, scheduled Wave 4.
- **J10 (`DONE_WITH_CONCERNS` with no concerns stated)** — status: filed, unfixed, scheduled Wave 4. No
  defect shipped from it; independent verification was done anyway and found nothing.
- **J1 (`launch` mis-captures the handle)** — status: filed, unfixed. Blocks zero-manual agent bootstrap;
  worked around by content-identifying the pane and pinning via env vars.
- **J9 (flaky `test_alive_cmux_true`)** — status: filed, unfixed. Probes the real `cmux` binary.
- **[stablyai/orca#9870](https://github.com/stablyai/orca/issues/9870)** — status: blocked upstream (Wave 5,
  watch-only). Every agent-resolution heuristic in `_orca_find` is a workaround for the missing field.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — `_cmd_env` verdict emission
- `h-mad/tests/test_hmad_dispatch.py` — J7 isolation + 15 preflight tests
- `h-mad/tests/test_h_mad_preflight_docs.py` (new) — doc-mandate assertions
- `h-mad/SKILL.md` — Phase-5 preflight + audit-assembly mandated reads
- `h-mad/references/orchestration-mode.md`, `h-mad/references/agent-substrate.md`
- `docs/skill-monitoring.md` — J7 resolved, J8 root cause, J10 filed
- `docs/01-plan/h-mad-remediation-sequence.md` — Waves 1–2 marked shipped, J8/J10 folded into Wave 4
- `docs/archive/2026-07/preflight-signal-discipline/` — 13 archived phase artifacts

**Commits (all pushed to `origin/main`):**
- `aa1f01a` phases 1–5b baseline · `f216d16` J7 · `04129a0` PREFLIGHT token · `51b9515` mandated reads
- `fcea6ab` 6a-prime fixes · `e17fbea` phase 7 report+archive · `787aecf` merge · `c5f11d4` monitoring
- `9d22d59` sequence doc

**Uncommitted changes:** none — clean, in sync with `origin/main` at `9d22d59`.

**Agent panes** (content-verified; titles lie — one pane's tab title reads `Codex - skills repo` while
running agy). Handles rotate, so re-identify by content rather than reusing these:
- codex `term_957ddb26…` (`gpt-5.6-luna`) · agy `term_5bb15287…` (`Antigravity CLI` / `Gemini 3.1 Pro`)

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
# identify agents by CONTENT, then pin via env vars (keep the pin FILE absent is no longer needed — J7 fixed):
orca terminal list --json | jq -r '.result.terminals[] | select(.worktreePath|endswith("/skills")) | "\(.handle) \(.title)"'
hmad-dispatch env          # assert PREFLIGHT: PASS before any dispatch — mandatory as of this wave
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q    # expect 530 passed
```

**Related docs:**
- `docs/01-plan/h-mad-remediation-sequence.md` — the wave plan; Waves 1–2 marked shipped with carries
- `docs/archive/2026-07/preflight-signal-discipline/preflight-signal-discipline.report.md` — full outcome,
  metrics and carry items
- `docs/skill-monitoring.md` — J1–J10 + F/G/H series; J6 recorded as **disproven**, do not re-file

## Version History
- v1.0: Wave 2 closeout.
