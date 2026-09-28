AUDIT-codex-tdd-gate-defects-design-v1-BEGIN
## Summary
The design has nine blocking gaps, including three acceptance criteria whose proposed fixtures or ordering narrow the spec. The remaining 40 of 43 criteria are covered as written, but the Claude fast path, interpreter fixture, and two judge connections need correction before implementation.

Evidence: 9 files opened, 9 greps run; the current hook and parser paths were inspected, and the mutation-anchor check read `ANCHORS_OK specs=99 mutations=907 ok=907 drifted=0`. 🌱 graft saved ~58,156 tokens (~$0.03), 1 call.

| ACs | implemented-as-written | restated | absent |
|---|---|---|---|
| FR-0 | 0.1, 0.2 | — | — |
| FR-1 | 1.1–1.3 | — | — |
| FR-2 | 2.1–2.9 | — | — |
| FR-3 | 3.3–3.5 | 3.1, 3.2 | — |
| FR-4 | 4.1–4.7 | — | — |
| FR-5 | 5.1–5.4 | — | — |
| FR-6 | 6.1–6.8, 6.10 | 6.9 | — |
| FR-7 | 7.1, 7.2 | — | — |
| FR-8 | 8.1 | — | — |

## Must-fix
- AC-3.1 is restated as an isolated real venv rather than a pytest-capable, marker-writing shim — the proposed `--without-pip` fixture does not provision pytest or prove that the selected interpreter ran it, so the positive RED test cannot establish the spec's observation. Preserve the shim/marker control or explicitly reconcile the criterion in the spec.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `Its `bin/python` is a shim that runs an interpreter with`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `root/hematology-paper-writer/.venv/` is made by `python -m venv --without-pip``
- AC-3.2 is restated without its no-execution marker, and D12 specifies an impossible oracle for the missing-`pyvenv.cfg` row — `realpath` of a missing file under an otherwise contained venv remains under the root, so a test asserting every mutated path leaves the root will fail for the correct containment implementation. Assert the marker stays absent for the symlink escape, and check only the symlink paths with the realpath-leaves-root oracle.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `and the shim's marker is not written.`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `runs `os.path.realpath` on each mutated path and asserts that it leaves the root.`
- AC-6.9 is restated for production `.py` writes only — DD-1 allows an exempt write before reading a malformed state, while the spec says a write on an unreadable chain is refused. The repair-write rationale may be sound, but the narrower rule must be agreed in the spec and its exempt-write behavior tested.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `The write is refused with`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `The Claude gate runs the exemptions and the `.py` filter **before** the `state` verb`
- The Claude target precedence reverses FR-6 — D9 selects `$1` before stdin, so a stale positional path can override Claude Code's `tool_input.file_path` and govern a different write. Read stdin fields first, then use `$1` only as the fallback, and add a conflicting-input fixture.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `The gate reads `tool_input.file_path`, then the top-level `file_path`, then the`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `From `$1`, else from stdin JSON`
- The retained Claude fast path can silently allow a governed write before the shared chain reader runs — the current `_resolve_state_file` uses `-f` and `cd` to the target's parent (`h-mad/hooks/h-mad-tdd-gate.sh:31,39,51`); a dangling-symlink state is skipped, and a new file under a not-yet-existing directory misses a nested state when the root state is absent. D2 explicitly accepts a nonexistent target parent, so the fast path must use compatible chain semantics or defer to `state`; add both regressions.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `Any unreadable file on the chain`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `[ -f "$STATE_FILE" ] || _allow`
- W3 and W4 are promised but have no remove/force connection mutations in the specified mutation files — the table mutates Task authority and scoring branches, which can stay green if the judge stops calling `_parse_tasks` or `_suite_summary` and substitutes equivalent local logic. Add both directional call-site mutants and tests that observe the intact callees through the judge, as the paired plan requires.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `Each wire ships a test that fails when the connection alone is removed and the callee is intact.`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `W1–W6 are mutated in both directions (plan table)`
- The AC-2.8 denial detail is inconsistent across D3 and Error Handling — after an unreadable impl-plan, a name-map result that names a missing test takes D3's `test-missing` return, whose specified reason names candidates but not the plan read failure. Carry `impl-plan unreadable` into this DENY as the spec requires, and pin that exact route.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `When no name-map test exists either, the DENY reason contains`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `If the file does not exist, the verdict is `test-missing`.`
- DD-6 narrows the FR-3 shell contract by excluding H-MAD control commands under a contained venv interpreter — that changes the executable/argv matrix the spec states, even though the design's differential treats the row as unchanged. Either implement the spec's existing control allowlist or land the narrower contract and its control-row expectation in the spec first.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `only `python -m pytest …` and the H-MAD control allowlist pass.`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `The venv interpreter is admitted for `-m pytest …` only`
- DD-4 adds a PASS-to-FAIL audit-gate verdict outside FR-4's specified single change — this may be the right correction for a colored failing summary, but the design itself says the new behavior is owed to the spec. Amend FR-4 and its regression scope before using the design as the implementation contract.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `The one change to the audit gate`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `The first row is a verdict change outside spec FR-4's "one change". It is owed to the spec`

## Should-fix
- Resolve OQ-D1 before choosing a 40-second judge budget for a host hook — a shorter Claude or Codex hook deadline could terminate a correct judge before it emits a refusal, and the current design leaves that outcome unmeasured. Measure the host deadline/behavior with the live probe or specify an installed timeout above the judge budget and verify it.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `The Claude Code command-hook default timeout is **not measured here**`

## Nit
- D12 should locate `python-evil` explicitly under `.venv/bin/`; “Next to it” leaves the differential fixture path ambiguous.
AUDIT-codex-tdd-gate-defects-design-v1-END
