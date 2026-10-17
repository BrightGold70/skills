# FR-8 steps 2, 2a, 3 — post-merge tracer record (impl-plan Task 21)

**skills sha:** `61c620e7` + Task 20 GREEN in the working tree (`PATH_KEYS` gains
`replace_file_content`; the installed gate `~/.gemini/config/skills/h-mad` → this checkout) ·
**agy --version:** `1.4.0` · **date:** 2026-10-17 · **fixture:** `/Users/kimhawk/orca/agy-fr8-fixture`
(`docs/.bkit-memory.json` `fixture-calc` `phase=step5`; `.agents/hooks.json` = FR-5's exact entry,
sha256 `23bba79b…81cbbc`; `h_mad_hook_wiring.py --agy` → `AGY-GATE: WIRED`). Transport for every
step: `hmad-dispatch exec agy … --cd <fixture>`. The operator's global `~/.gemini/config/hooks.json`
(`orca-status`, `PreToolUse` `*`) was loaded throughout. Raw prompts, stream-json logs, final
responses: `docs/03-analysis/agy-coder-fallback.authoring/fr8_tracer/`.

## Step 2 — real refusal: PASS

Instruction (`step2.txt`): add `sub` to `src/calc.py` directly, no test first, no retry.
- `src/calc.py` sha256 before and after: `ba1a531f…18bc772` — unchanged; tree clean.
- stream-json (`step2.log`) shows the gate's reason: `tool call denied by pre-tool hook: Phase 5
  requires a failing test before src/calc.py: no test resolved; … kind=no-test-resolved`.
- Settles: a gate `deny` wins over the sibling global `orca-status` handler; agy honours the
  project `.agents/hooks.json` at this location without a trust prompt (`permission_mode:
  always-proceed`).

## Step 2a — forced handler timeout: `timeout-blocks`

Delay handler `fr8-delay` (`PreToolUse`, matcher `*`, `timeout` T=5, `sleep 12` then
`{"decision":"deny","reason":"probe-timeout"}`) added to the fixture's `.agents/hooks.json`.
Instruction (`step2a.txt`): one `write_to_file` of `probe/timeout-probe.txt`.

| reading (each observed) | value |
|---|---|
| file afterwards | absent (`ls probe` → no such directory) |
| wall time, tool call → next event | `write_to_file` step `ERROR`, `duration_seconds: 6.138527` (≈ T; < 2T=10) |
| agy's runtime message | `JSON hook "jsonhook__fr8-delay_PreToolUse_0_0" failed: command failed: signal: killed` |

The handler's post-sleep marker file was never written (killed before `deny`). The session
continued and answered (`result.status: SUCCESS`), so this is not `session-error`.
**Outcome: `timeout-blocks`** — a handler that overruns its timeout is killed and the call is
blocked; the write guarantee holds when the gate overruns.

Removal (probe-then-delete): `.agents/hooks.json` restored; sha256 before
`23bba79bfc577ad552f6dc69376d9dac42380943f354d87ef66d89246581cbbc`, after identical; keys
`['h-mad-agy-tdd-gate']`.

## Step 3 — RED then GREEN with agy as implementer

Fixture impl-plan `fixture-calc` Task 1 (`sub`), staged by `h_mad_assemble_tdd.py --agent agy`
(the wiring check ran inside the assembler → `ASSEMBLE-TDD: PASS`).

| | RED | GREEN |
|---|---|---|
| assembler split | `--expect-fail 1 --expect-pass 1` | `--expect-fail 0 --expect-pass 2` |
| dispatch wall time (`date` around `exec agy`) | **117 s** | **71 s** |
| `h_mad_extract_verdict.py --key STATUS` | `STATUS: DONE` | `STATUS: DONE` |
| independent re-run (`.venv/bin/python -m pytest tests/test_calc.py -v`) | `test_add` PASSED, `test_sub` FAILED (`AttributeError`) | 2 passed |
| tree delta | `tests/test_calc.py` only | `src/calc.py` only (+4) |

- **Where files landed:** every `.py` write under the `--cd` root (RED: `replace_file_content` on
  `tests/test_calc.py`, which Task 20's `PATH_KEYS` entry made judgeable; GREEN: `src/calc.py`). The
  only writes outside the root were the assembler-named report file and its `.done` marker in the
  orchestrator scratchpad (non-`.py`). No `.py` outside the root.
- **Revert test:** `git stash push -u` → `1 failed, 1 passed`; `git stash pop` restored the GREEN tree.
- **Mutation:** `return a - b` → `return a + b` → `1 failed, 1 passed` (killed). Restored; a first
  re-run read `1 failed` from a **stale `__pycache__`** (same-size file rewritten within one second);
  after deleting `__pycache__`, `2 passed`. Measurement artefact, not a code state.

Fixture commits: `75673dd` (RED), `717a0f5` (GREEN).

## Readings for FR-8 step 4 (Task 22)

RED 117 s, GREEN 71 s → slower = 117 → `max(900, 3 × 117 = 351)` = 900 → rounded up to a multiple
of 60 = **900**.

## Task 22 — step 2 re-run in this repository (adoption): PASS

`.agents/hooks.json` created here with FR-5's exact entry (sha256 `23bba79b…81cbbc`, identical to
the fixture's; `git check-ignore -v .agents/hooks.json` printed nothing, rc 1;
`h_mad_hook_wiring.py --agy --project-root .` → `AGY-GATE: WIRED`). A throwaway
`fr8-trust-probe/` held a temporary `fr8-trust` `phase=step5` record and
`fr8-trust-probe/src/probe_mod.py` (sha256 `5b76d096…a235e352`). Instruction (`step2_repo.txt`)
through `hmad-dispatch exec agy … --cd /Users/kimhawk/orca/skills`:
- refused: `tool call denied by pre-tool hook: Phase 5 requires a failing test before
  fr8-trust-probe/src/probe_mod.py: no test resolved; … kind=no-test-resolved`;
- `probe_mod.py` sha256 unchanged; `fr8-trust-probe/` then deleted (`ls` → no such file).
Trust at this location is settled: agy loaded this repository's `.agents/hooks.json` with no prompt.
Derived default committed: `TIMEOUT_DEFAULTS["agy"] = 900`; `fr8_timeout_formula.py` → `PROBE: PASS`,
`--control` → `PROBE: FAIL`.
