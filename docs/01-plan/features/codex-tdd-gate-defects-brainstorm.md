# Brainstorm: codex-tdd-gate-defects

## Executive Summary

Fix three measured defects in `h-mad/hooks/h-mad-codex-tdd-gate.py`, so that it both **permits** legitimate Phase-5 production writes and **refuses** unverified ones. Today it does the opposite of both.

## Problem Statement

The gate was armed for the first time on HemaSuite #28 Task 7 GREEN. It refused a legitimate edit, and it would also have passed an untested write vacuously. The brief is `docs/handoffs/2026-09-28-main__codex-tdd-gate-defects.md`, taken over by session 8a0b0625 and committed in 59c6703. The blocked codex report is preserved at `docs/03-analysis/probes/codex-tdd-gate-defects/hemasuite-t7_green.blocked1.report.md`. All three defects were re-verified on 2026-09-28:

- **D1 — the test path is derived from the module name only.** `_derived_test` calls `scripts/h_mad_derive_test_path.sh`, which maps `.../guideline_excerpts.py` to `tests/test_guideline_excerpts.py` and `cli/_parser.py` to `tests/test__parser.py`. Neither of those files exists. The impl-plan names each task's test file (`**Test file**:`), so every real write is denied.
- **D2 — the project virtualenv is untrusted.** `_trusted_executable` accepts `TRUSTED_BIN_DIRS` plus the hook interpreter's own directory. It does not accept `<repo>/.venv/bin/python`, which is the only interpreter with pytest in HemaSuite's HPW project.
- **D3 — the gate fails open.** `_test_exit` runs `[sys.executable, "-m", "pytest", …]`. `sys.executable` is Homebrew python3.14, which has no pytest (`No module named pytest`, rc=1). The refusal condition is `test_exit != 1`, so a missing pytest reads as "the test fails" and the write is **allowed** without any test running.

## Proposed Approach

Operator decisions from 2026-09-28 are marked **[D1]**–**[D3]**.

1. **[D1] Resolve from the impl-plan task first, then fall back to the name map.**
   - Read the ACTIVE feature's impl-plan. The Task whose `**Production file**:` lists the target (repo-relative, normalised) supplies its `**Test file**:`.
   - Parse the impl-plan with the existing Task parser (`h_mad_wire_pin_gate._parse_tasks`), not a new one.
   - If no Task matches, fall back to the derive-script name map.
   - If neither yields a path, deny, and name both paths that were tried.
2. **[D2] Trust a project venv only inside the repo root.**
   - Accept `<git-root>/**/.venv/bin/python*` only when its realpath stays inside the git root, so no symlink can escape. Today's system directories stay trusted.
   - Document the boundary in `h-mad/references/codex-runtime.md` §"Trust boundary".
3. **[D3] Fail closed, scored on pytest's summary line.**
   - Run pytest with the resolved project interpreter and score only its summary line, never the exit code. A missing module and a failing test both exit 1.
   - Allow the write only on a measured failing test (`N failed`, with N > 0, in the target test file).
   - A missing pytest, a collection error, no summary line, or `no tests ran` is a cannot-judge. It → DENY, with the reason.
   - Reuse the audit gate's summary scorer (`h_mad_audit_gate._suite_summary`) rather than a second parser.
4. **Tests.** TDD, run through the hook's actual entry point, with fixtures that reproduce the HemaSuite layout:
   - a nested sub-project with a `.venv` and an impl-plan whose Task names the test;
   - a python with no pytest (the D3 fail-open case);
   - a symlinked venv that escapes the root (D2).
   Every guard is mutation-tested.
5. **Live verification** comes before HemaSuite re-arms the gate: one real codex GREEN write through the fixed gate. The install of `~/.agents/skills/h-mad` is **out of scope here** and is owned by `multi-host-runtime`, which absorbed todo #5. The live check needs that install, which sets the order.

6. **[D4] The Claude-side gate may never block. Measure first, then fix.** Added 2026-09-28 by operator decision.
   - `h-mad/hooks/h-mad-tdd-gate.sh` blocks only through `exit 1`, at 5 sites, and never emits a JSON `permissionDecision: deny`. The codex gate does emit one.
   - Claude Code's PreToolUse contract treats exit 2 (or a JSON deny) as blocking. Any other non-zero exit is a non-blocking error. So the Claude-side Phase-5 authorship gate may never have refused a write.
   - The multi-host-runtime spec-author flagged this. It is **unverified**: my live probe on 2026-09-28 was inconclusive, because the hook exited 0 before reaching any BLOCK branch, so the write landing measured nothing.
   - Step 1: a live probe that provably reaches a BLOCK branch. Replay the payload by hand first and require hook rc=1, then attempt the real tool write.
   - If that probe confirms the defect, switch every BLOCK to exit 2 or a JSON deny, with a test that asserts the blocking form rather than just "non-zero".

## Alternatives Considered

- **Impl-plan only.** Rejected [D1]: it breaks legitimate ad-hoc fixes during step5.
- **An operator-named interpreter (environment variable or config).** Rejected [D2]: it adds a knob. Auto-trusting a venv bounded by the repo covers the measured case with no configuration.
- **Keeping the exit-code check but using the project interpreter.** Rejected [D3]: exit code 1 still conflates a missing module with a failing test.
- **An emergency escape variable.** Rejected [D3]: the declared `codex_status` fallback already exists for operator overrides.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Impl-plan parsing in a PreToolUse hook is slow or fragile | M | Reuse `_parse_tasks`; parse only the ACTIVE feature's impl-plan; any parse failure falls back to the name map and is reported |
| Running pytest per write is slow | M | Scope the run to one test file (today's behaviour); state the latency |
| Trusting a venv widens the attack surface (a malicious `.venv/bin/python` in the repo) | L | realpath containment; the repo is already trusted to run its own tests; documented |
| The summary scorer misreads `N failed` from an unrelated file | L | Run only the named test file; require N > 0 |
| Conflict with grok-codex-fallback and multi-host-runtime edits in `h-mad/` | M | This touches the hook, its tests, and the `codex-runtime.md` trust section only; separate worktree; merge order decided at 5c |

## Dependencies

- `h_mad_wire_pin_gate._parse_tasks` and `h_mad_audit_gate._suite_summary`: imported, not copied.
- The live check needs the `~/.agents/skills/h-mad` install from `multi-host-runtime`.

## Open Questions

1. Should ACTIVE feature resolution reuse the existing hook's state read? It must: one reader.
2. What if the Task's `**Test file**:` does not exist yet (a RED in progress)? Probably deny with "author the test first", which is what TDD wants.
3. ~~Does the Claude-side TDD gate share D1?~~ **Yes**, verified: `h-mad-tdd-gate.sh` sets `DERIVE_SCRIPT=…/h_mad_derive_test_path.sh`. D1's fix applies to both gates, through one shared resolver.

## Version History
- v1.0: Initial brainstorm draft (operator decisions D1–D3, 2026-09-28).
- v1.1: D4 added (the Claude gate's exit-1 blocking is unverified; measure first); OQ3 answered (D1 applies to both gates).
