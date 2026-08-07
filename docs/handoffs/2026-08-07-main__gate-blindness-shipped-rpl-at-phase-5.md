# Handoff — gate-blindness-hardening SHIPPED; regression-provenance-ledger ready for Phase 5

**Date:** 2026-08-07
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Took `gate-blindness-hardening` from Phase 5 through merge (`379b881`): the Phase-7 `archreview`
ladder is now total, so a feature can no longer close without a recorded architectural review. Then
backfilled `docs/skill-monitoring.md` with J19–J27 (`b551ad1`), and — from the operator's
observation that new features silently break older ones "like losing wiring" — took a new feature,
`regression-provenance-ledger`, through Phases 1–4 with both gates clean (`a1fd2d4`). Also killed a
64-process / 6.97 GB orphan leak and filed its bug doc (`4ecc072`). Nothing is blocked;
`regression-provenance-ledger` is **ready to enter Phase 5**, claim released.

## Key Learnings

- **A read-back guard caught a real bad write on its first live use, and schema validation could
  not have.** §6a-prime's own auto-record instruction led into a two-line `$(...)` capture —
  `h_mad_extract_verdict.py` prints its `[H-MAD]` marker to **stdout**, right after the verdict. The
  writer refused the malformed value and the read-back reported `None`. `h_mad_state_validate.py
  --strict-only` returns `STATE: PASS` on a record with `archreview` **absent**, because the field
  is not in `required` — so the validator-based check the 5b audit originally proposed would have
  passed this silently. Filed as J26, still open: the script is unchanged, only the doc warns.
- **A broken RED test is indistinguishable from a good one by running it.** Two of Codex's generated
  RED tests would have made GREEN unreachable and both showed the expected failure counts: one
  lowercased its haystack then searched for an upper-case literal (could never match, even with the
  target sentence present verbatim), and two others were **mutually unsatisfiable** — one banned the
  substring `resolved pane`, its sibling required `does not require a resolved pane`, which contains
  it. Found by reading the diff, not by running.
- **One unresolvable pytest node id aborts the entire selection** (`rc=4`, `no tests ran`), and
  `--continue-on-collection-errors` does not help. Worse, an **empty** node-id list makes pytest
  collect the whole tree — 1331 tests here. Both measured; together they mean a naive
  "run all registry pins in one selection" verifies zero wires while producing zero failures.
- **h-mad's wire machinery is entirely creation-time.** The 5b gate, the 5d caller-side RED check
  and the 5e wire-scoped revert all fire while a wire is being built; **nothing re-checks it
  afterwards** — there is no consumer of `WIRE-PIN` after 5g. Combined with under-declaration
  (HemaSuite: 4 of 172 impl-plans declare `wiring`; **1** WIRE-PIN test across ~8000), that is why
  wires die unnoticed.
- **A doc test's scope can depend on prose length.** The §6a-prime tests sliced a magic
  `s[idx:idx+1600]` window; the bullet had grown to 1707 chars with **76 chars of margin** on the
  nearest guard, and a ban on `h_mad_state_validate.py` passed *only* because the sentence warning
  against it fell past the cliff. Fixed by slicing at the real bullet boundary.
- **`git show` cannot distinguish an absent path from an invalid sha** — both exit 128. The clean
  discriminator is `git rev-parse --verify --quiet <sha>^{commit}` (rc 0 vs 1), not stderr parsing.
  Separately, `git ls-files --error-unmatch` exits non-zero for an **absent** path as well as an
  untracked one, so an existence check must come first or every unseeded repo reports `UNTRACKED`.
- **`hematology-paper-writer/**/__pycache__/*.pyc` is tracked in this repo** and any full pytest run
  rewrites ~9 of them. They show up as modified in every `git status`; they are not yours and should
  not be staged.
- **Agent pane pins go stale within a session.** Repaired mid-session, stale again by the end.
  Irrelevant to `exec` (pane-independent), which is why every dispatch this session used it.

## Next Steps

1. **Enter Phase 5 for `regression-provenance-ledger`** — `/h-mad "regression-provenance-ledger"`
   routes to `enter_autonomous`. State: `current_phase=5, last_completed_phase=4`, claim **free**.
   Design has 7 implementation steps in `docs/02-design/features/regression-provenance-ledger.design.md`
   §"Implementation Order".
2. **Step 1 of that order is the conftest guard** — extend `h-mad/tests/conftest.py`'s existing
   `_protect_live_pin_file` to snapshot/restore `.h-mad/wires.jsonl`. It must exist **before** any
   test writes a registry (J18 class: the writer is a path resolver).
3. **The registration task must be `wiring` shape with both mutation directions** — remove the
   5b-gate→`register()` call (callee intact) ⇒ pin fails; force registration to fire unconditionally
   ⇒ a fall-through test fails. `invariants.base.md:107`.
4. **Push `a1fd2d4`** — 1 commit ahead of `origin/main`, everything else is pushed.
5. `[suggested]` **File the two Orca bug docs upstream** to `stablyai/orca` — carried unfiled across
   **four** sessions now. `docs/orca-bug-worker-release-dispatch-not-found.md`,
   `docs/orca-bug-terminal-read-empty-after-restart.md`. `gh` authenticated as `BrightGold70`.
   Either file them or mark WONTFIX; the carry itself is the problem.
6. `[suggested]` **J26 needs a caller sweep** — route `h_mad_extract_verdict.py`'s `[H-MAD]` marker
   to stderr (as the gate scripts already do), after checking every caller that may capture combined
   output. Currently doc-only mitigation.

## Open / Blocked Items

- **`regression-provenance-ledger` Phase 5** — status: ready, not started. Claim released this
  session, so the next session can `--claim` without `--force`. All FR-1–FR-6 designed; 13 audit
  cycles resolved 21 must-fix + 9 should-fix.
- **Two Orca bug docs unfiled upstream** — status: deliberate (operator chose docs-only), carried
  from three prior handoffs. Not blocked; needs a decision, not work.
- **J26 `h_mad_extract_verdict.py` marker on stdout** — status: MONITORING in
  `docs/skill-monitoring.md`. Doc-only mitigation; the trap is still live for the next caller that
  captures rather than reads.
- **9 tracked `.pyc` files perpetually dirty** — status: pre-existing, not this session's. Any full
  pytest run rewrites them. Left unstaged deliberately.
- **Stale codex/agy pane pins** — status: deferred, operational. `PREFLIGHT: FAIL stale=codex,agy`.
  Does not block anything that uses `exec`.
- **FR-5 (shape challenge) is the weakest part of the new design** — status: deliberate, operator
  decided to keep it in scope. It drove most of 8 design cycles, is warning-only and
  verdict-neutral, and rests on a static AST name index that cannot see dynamic dispatch. If Phase 5
  drags, it is the obvious thing to split out.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_phase7_preconditions.py` — total `archreview` ladder
- `h-mad/scripts/h_mad_state_schema.json` — `SKIPPED_OPERATOR_OVERRIDE` enum value
- `h-mad/SKILL.md` — §6a-prime headless + auto-record + read-back; Phase 7 bullet
- `h-mad/tests/stubs/orca` — `HMAD_STUB_HOSTILE` corpus
- `h-mad/references/codex-implementer-prompt.md` — hostile-fixture mandate
- `h-mad/tests/test_h_mad_{phase7_preconditions,archreview_pane_halt,state_write,hostile_fixtures,tdd_dispatch_discipline_prompt}.py`
- `docs/skill-monitoring.md` — J19–J27
- `docs/bug-gemini-auth-status-orphan-leak.md` — new
- `docs/01-plan/features/regression-provenance-ledger.*`, `docs/02-design/features/regression-provenance-ledger.*`

**Uncommitted changes:** 9 tracked `hematology-paper-writer/**/__pycache__/*.pyc` (incidental
pytest churn, deliberately unstaged). No source changes outstanding.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
# suite (default python3 has no pytest) — expect 1166 passed:
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ handoff/ -q
# then:
/h-mad "regression-provenance-ledger"      # routes to enter_autonomous / Phase 5
```

**Related docs:**
- `docs/02-design/features/regression-provenance-ledger.design.md` — authoritative; §"Implementation Order", §"Architecture Overview"
- `docs/01-plan/features/regression-provenance-ledger.plan.md` — §"Verified assumptions (probe evidence)" A1–A5
- `docs/04-report/features/gate-blindness-hardening.report.md` — what shipped and the five defects found in its own work
- `docs/skill-monitoring.md` — J19–J27, J26 is the only new open row
