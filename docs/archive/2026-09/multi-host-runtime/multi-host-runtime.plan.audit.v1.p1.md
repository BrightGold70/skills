## Summary
The plan addresses FR-1 through FR-12, but its FR-1 coverage threshold and FR-5 hook account differ from the source spec; the proposed smoke also cannot verify the unmerged adapters through the stated install layout. The findings below identify the changes needed before this plan can drive implementation.

| FR | Classification |
|---|---|
| FR-1 | restated |
| FR-2–FR-4 | implemented-as-written |
| FR-5 | restated |
| FR-6–FR-12 | implemented-as-written |

Evidence: 12 files opened, 18 greps run; source scripts, installed symlinks, sibling spec, and the published counts were checked. 🌱 graft saved ~81,716 tokens ($0.03 plus <$0.01) in 2 calls.

## Must-fix
- FR-1 is restated as per-alternative coverage in every declared skill — the spec requires hits per entry, while the plan's stronger success gate fails on the unchanged handoff corpus: at ae7593a, `/compact` has 0 literal hits in `handoff/SKILL.md` although `/clear` has 8. Requiring retirement or a split would change the seed pattern and its adapter rows; either retain the spec's per-entry gate and report branch coverage separately, or revise the spec explicitly.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `Every entry has ≥ 1 hit in every skill it declares and 0 hits in every skill it does not.`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `reports every registry entry and every alternative with ≥ 1 hit in each declared skill at `<base>`, or records the retirement.`
- FR-5's AC-5.2 evidence is restated before the spec changes — the spec requires the grok adapter to cite the current `exit 1` fail-open reason, while the plan proposes a different, undocumented-deny-form reason after a sibling edit. This may be the correct post-rebase account, but the spec and acceptance test must be revised from the measured gate before Phase 5.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `refuses by `exit 1`, which grok treats as fail-open`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `reason (i) becomes "deny form undocumented on grok", not "fail-open".`
- The pre-merge smoke loads main-tree skills while testing a worktree wrapper — the plan expressly points every installed skill link at main and says hosts cannot see unmerged work. Resolving only `$D` inside the worktree therefore cannot prove V-11.1 or the new adapter behavior; use a verified worktree skill-load path or run the smoke after the feature lands, and assert the loaded SKILL/adapter paths.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `The links point at the main checkout, never at the worktree, so no host sees unmerged work.`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `run one read-only `/h-mad status <feature>` through the **worktree's** wrapper by absolute path.`
- W1's prescribed ordering mutant is observationally equivalent on its named fixture — moving the `HMAD_HOST` check after a successful transcript lookup can still print exactly `host_unsupported`, so AC-8.1 need not kill it. Add a spy or failing transcript-access canary that proves no resolution or read occurs before the host verdict, then verify the mutant landed and goes red.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `the `HMAD_HOST` check moved after the transcript lookup (W1)`
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `Set `HMAD_HOST=grok` with a valid Claude JSONL present at the cwd slug and passed via`
- The sibling merge order still has an unsatisfied verification dependency — this plan requires `codex-tdd-gate-defects` to merge first, while that feature's V-1 says its live check cannot run until the multi-host-owned install lands. “Operator can create” is not a scheduled precondition for that sibling's V-1; place the link install and its observed verification before V-1, or change the merge/verification order in both plans.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `This feature merges **after** `grok-codex-fallback` and`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `install is owned by feature `multi-host-runtime`, and V-1 cannot run until it lands.`

## Should-fix
- Bound the three live host calls with the wrapper's `--timeout` and treat deadline 124 as a recorded halt — the shown command has no deadline, so an unauthenticated or stalled host can leave FR-11 waiting indefinitely.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `"$D" exec "$H" "$S/prompt.txt" --cd "$W" --out "$S/out" --log "$S/log" || { echo "HALT rc=$?"; exit 1; }`
- Clarify the adapter-by-adapter RED/GREEN sequence — the plan says the live-tree gate is green before any adapter table is added, yet that gate must report `TABLE_MISSING` for the other five until all six are complete. Use fixture-level green for each adapter and require live-tree green after the sixth.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `land against a green gate, one adapter at a time, each turning its `TABLE_MISSING` red to green.`
- Reconcile the known baseline failure with the final green-suite gate — the plan records one live-binary failure and permits that baseline failure in the node-id floor, but also requires both coupled suites green before merge. State the exact environmental repair or keep the full-suite gate red and escalate; do not treat the floor's exception as AC-12.1 passing.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `1 failed, 3892 passed, 1 warning in 588.67s.`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `Both coupled suites green in full before merge.`

## Nit
None
