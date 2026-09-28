## Summary
The plan covers FR-0 through FR-8 at requirement level, but six hard gaps remain in its verification and delivery strategy. Axis C: all requirements are implemented-as-written at this granularity; no FR is restated or absent.

| FR | Classification |
|---|---|
| FR-0 | implemented-as-written |
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |

Evidence: 7 files opened, 9 greps run; the embedded probe hashes were re-derived and match. 🌱 graft saved ~62,955 tokens this turn (one call reported $0.03; two reported <$0.01 each).

## Must-fix
- The planned E1_DOES_NOT_BLOCK branch can select JSON denial without a live test that Claude Code blocks that form — V-0 measures exit codes only, while the spec explicitly calls JSON denial unmeasured. Add a live JSON-deny arm before selecting form (b), or select the measured rc-2 form (a).
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `The blocking form follows V-0's reading`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `This is not measured here. If FR-0 is re-run, E2 is its only exit-code control.`
- V-0 accepts any nonempty per-arm hook log as proof that the sentinel Write reached the refusal branch — a session can invoke Write for another path, leaving E1 absent and yielding a false E1_BLOCKS reading. Parse each arm's logged payload, assert tool_name=Write and the sentinel file_path before scoring file presence; a mismatch is UNMEASURED.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `[ -s "$S/$1.invoked" ] || { echo "V-0: $1 UNMEASURED hook_never_invoked"; exit 1; }`
- The prescribed AC-3.4 relative shell token and sub-project cwd point to a doubled sub-project path, so its ALLOW fixture cannot exercise the contained venv as stated. Amend the spec and plan fixture to use `.venv/bin/python` from that cwd, or use the prefixed token from the root cwd; test the actual resolution.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `shell policy admits a contained`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `hematology-paper-writer/.venv/bin/python -m pytest`
- The shell guard is deliberately relaxed for contained venv interpreters, but the plan supplies only selected examples and an existing untrusted-path test. The base guard-narrowing invariant requires an old/new differential corpus and an accounting of every newly allowed command, including relative-token and symlink cases.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `shell policy admits a contained`
- The fix is motivated by the HemaSuite Task 7 incident, whose impl-plan, production file and test exist on disk, yet the plan defers V-1 beyond this feature's merge and otherwise relies on authored fixtures. Add a read-only replay of the shipped gate against those real artifacts before merge; the later installed-hook V-1 can remain a separate live check.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `is not a merge condition of this feature.`
- R1 permits merging after an INCONCLUSIVE V-0 even though it says FR-6's refusal form cannot ship. That leaves a merged gate without the required blocking contract; make a conclusive V-0 reading and the selected form a merge gate, or explicitly split the incomplete feature and reconcile the spec.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `AC-6.1–AC-6.4 still ship; the halt reason from the probe is fixed and V-0 re-run; merge does not wait on it, the FR-6 form task does`

## Should-fix
- The node-id floor detects removed tests but cannot detect an existing test whose assertions were weakened under the same node id, although R6 claims it mitigates both cases. Pair it with a diff review or equivalent assertion-level check for every changed existing test.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `R6 — a pre-existing test is deleted or weakened while counts stay green | Compatibility NFR silently false | Node-id floor (Success Criteria), not a count`

## Nit
None
