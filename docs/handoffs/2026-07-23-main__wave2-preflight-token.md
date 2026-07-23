# Handoff — Wave 2: preflight token + mandated reads (h-mad remediation)

**Date:** 2026-07-23
**Branch:** main (Wave 1 merged as `5fa96ba`, pushed)
**Project:** BrightGold70/skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Wave 1 of `docs/01-plan/h-mad-remediation-sequence.md` shipped: `cycle-telemetry-fidelity`
merged to main at `5fa96ba`, 100% match rate, suite 498/0. Both h-mad cycle counters now derive
from versioned artifacts instead of state fields nothing incremented, so the telemetry drift
warnings can fire for the first time. **Wave 2 has not been started.** This handoff exists because
Wave 1 was driven cross-repo from a HemaSuite session, which repeatedly hit the cwd-relative
assumptions in the dispatch layer; Wave 2 should be run by a session whose cwd **is** this repo.

## Key Learnings

- **Run `/h-mad` from the repo it targets.** The session pin file resolves as
  `.h-mad/orca-pins.env` relative to cwd, and `_orca_find` scopes candidates to the *coordinator's*
  worktree. Driving this repo from another one makes both wrong at once (filed as J2). Passing
  `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL` as env vars is the reliable override.
- **The state scripts need a non-default interpreter.** `python3` (homebrew 3.14) lacks
  `jsonschema`, so every `h_mad_state_*.py` call exits 2. Use `/opt/anaconda3/bin/python3` for
  those. `h_mad_telemetry.py` and `h_mad_cycle_counts.py` are deliberately stdlib-only and run
  under bare `python3` — keep it that way. (F8, re-opened as J4.)
- **A review's verdict is worth less than its reasoning.** Across three coverage reviews agy
  produced 12 findings: 9 genuine, 2 whose stated premise was false but whose underlying point was
  real, 1 pedantic. Verify each claim against the source before acting; rejecting a finding whose
  premise is wrong can still lose a real defect.
- **"Every new test must FAIL" is wrong for a refactor dispatch.** A behaviour-preserving task can
  legitimately have exactly one RED — "the duplicate is gone" — and everything else is a regression
  guard. Given that instruction, Codex bolted unrelated source assertions onto two guards to
  manufacture failures. Say which tests are guards.
- **Shell-measured diff sizes understate the payload ~3×.** `git diff | wc -c` goes through the rtk
  filter; use `subprocess.run` when sizing an audit or review prompt against the ~49 KB reviewer
  cliff.
- **Identify Codex by content, never by title.** Two panes here share the tab title
  `Codex - skills repo`; the one that is actually Codex shows `gpt-5.6-terra` / `gpt-5.6-luna` in
  its status line. The other was an agy pane. Title-matching mis-dispatches silently.

## Next Steps

1. **Read the sequence doc first** — `docs/01-plan/h-mad-remediation-sequence.md` §Wave 2. It states
   the constraint that shapes the whole task.
2. **Start Wave 2 via `/h-mad "preflight-signal-discipline"`** (name is a suggestion) from
   `/Users/kimhawk/orca/skills`. Scope: give `hmad-dispatch env` a canonical
   `PREFLIGHT: PASS|FAIL` stdout token, and add the mandated read to `SKILL.md` Phase-5 preflight
   so an orchestrator must assert it before the first dispatch.
3. **Do NOT "fix" the weak signal by making `env` exit non-zero.** `invariants.base.md:16-21`
   makes stdout-token + exit-0 a base invariant, because a non-zero exit registers as a Claude Code
   `PostToolUseFailure` and leaks into coexisting plugins. `h_mad_audit_gate.py:178-180` follows the
   same rule (`GATE: FAIL` exits 0). The fix is a mandated *read*, not an exit-code change.
4. **Fold J7 into this wave** — `docs/skill-monitoring.md` §J7. F13 closed the env-var leak in
   `test_hmad_dispatch.py::run()` but not the pin-**file** leak. Because Phase 5 preflight *requires*
   `pin-agents` and Phase 5f *requires* running the suite, following the protocol guarantees 17
   failures at 5f on every run. Measured: 18 failed with the pin file present, 477 passed with it
   moved aside. Fix direction: resolve the pin file to a per-session path outside the repo, or
   honour `HMAD_ORCA_PIN_FILE` in the test harness and point it at a tmp path in `run()`. This
   belongs with Wave 2 because both are preflight correctness.
5. **Before dispatching, pin the agents** — `hmad-dispatch launch <agent>` is the intended path but
   currently mis-captures the handle (J1, reproduced 2×), so read the handle from
   `orca terminal list`, content-verify it, and `hmad-dispatch pin <agent> <handle>`. Then keep the
   pin file **absent** while running the suite until J7 is fixed, using env vars instead.

## Open / Blocked Items

- **Wave 2** — status: not started. This handoff is its brief.
- **Waves 3–5** — status: not started. Wave 3 is a dogfood `/h-mad` run over the Wave-1+2 payload
  (closes the standing "assembler audit cycle" and "merge-gate + handoff protocol" doc-verified
  gaps); Wave 4 is the candidates batch dispatched via worktree fanout, which is also the live
  e2e for the fanout path; Wave 5 is watching stablyai/orca#9870.
- **J1 `launch` handle mismatch** — status: filed, unfixed. Blocks zero-manual agent bootstrap.
- **J8 `elapsed_min` ≈ 56 years** — status: filed, unfixed. Pre-existing; `started_ts` parses to
  roughly the epoch, so the summary table's last columns misalign.
- **J9 flaky `test_alive_cmux_true`** — status: filed, unfixed. Probes the real `cmux` binary.
- **The `> 3` drift thresholds have never been exercised** because the counters were dead until
  Wave 1. They can fire now; whether 3 is right is unanswered.

## Context for Next Session

**Files that matter:**
- `docs/01-plan/h-mad-remediation-sequence.md` — the wave plan
- `docs/skill-monitoring.md` — J1–J9 + F/G/H series; J6 is recorded as **disproven**, do not re-file
- `h-mad/scripts/hmad-dispatch.sh:273-310` — `_cmd_env`, where the `PREFLIGHT:` token goes
- `h-mad/invariants.base.md:16-21` — the signal-discipline rule that constrains the fix
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps" — where the mandated read is added
- `docs/archive/2026-07/cycle-telemetry-fidelity/` — Wave 1's full artifact set, incl. its report

**Uncommitted changes:** none — main is clean and in sync with `origin/main`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
hmad-dispatch env                     # expect substrate: orca, orchestration: on
# pin by CONTENT, not title (see Key Learnings):
orca terminal list --json | jq -r '.result.terminals[] | select(.worktreePath|endswith("/skills")) | "\(.handle) \(.title) \(.preview[0:60])"'
export HMAD_ORCA_CODEX_TERMINAL=<handle-showing-gpt-5.6-*>
export HMAD_ORCA_AGY_TERMINAL=<handle-showing-Antigravity>
# state scripts need the interpreter that has jsonschema:
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q     # expect 498 passed
```

**Related docs:**
- `docs/archive/2026-07/cycle-telemetry-fidelity/cycle-telemetry-fidelity.report.md` — Wave 1
  outcome, metrics, and its carry items
- `docs/orca-feature-request-terminal-identity.md` — stablyai/orca#9870, the upstream blocker
  behind J1/H5

## Version History
- v1.0: Initial handoff for Wave 2.
