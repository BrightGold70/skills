AUDIT-tdd-gate-fail-opens-design-v2-BEGIN
## Summary
The design covers the main identity and oracle flows, but AC-3.6 and AC-8.4 have narrower planned tests than the spec. Root and cwd errors can cause unintended refusals, and the reap and fold connection steps need a discriminating implementation contract.
Evidence: 11 files opened, 12 greps run; process-reap and suffix controls executed. 🌱 graft saved ~27,258 tokens (~$0.01) this turn, 1 call.

| Spec AC | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9, AC-1.10, AC-1.11 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5 | implemented-as-written |
| AC-3.6 | restated |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6, AC-4.7 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-7.1 | implemented-as-written |
| AC-8.1, AC-8.2, AC-8.3, AC-8.5, AC-8.6 | implemented-as-written |
| AC-8.4 | restated |

## Must-fix
- AC-3.6 is restated as governed mode-0311 coverage — the spec also requires separate step3 controls for both cells and a failing PermissionError precondition; otherwise arm 2 can appear covered on a volume where its trigger never occurs.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `(c) control: (a) and (b) under the `step3`-only state — both gates allow, fixed and unfixed.`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `| Dangling, loop, and mode-`0311` open or list failure, governed | allow on the unfixed tree for AC-3.6 (a); deny `no-test-resolved` for (b) | 3.1–3.3, 3.5, 3.6 |`
- AC-8.4 is restated as one grouped set of six branch tests on Claude — the spec requires each listed failure case on both Claude and Codex, including a mode-000 fixture that proves PermissionError. The current test row can pass while the Codex host or that filesystem precondition is wrong.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › ``--host codex` and under `--host claude`, and each prints `cannot_judge`. The cases: id file`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `| Worktree git dir, hermetic `PATH` without `git`, six failure branches, `--host claude` | missing id on claude reaches `decide` | 8.3, 8.4 |`
- Preserve governed-only handling when the Claude root cannot be opened — the designed root canonicalisation propagates OSError into a failed one-shot call, which the hook refuses as judge-error even when no H-MAD state governs the write. FR-3 includes root components in arm 2 and allows ungoverned writes; specify a record or other state-aware route for that failure.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `with no governing state, the gate allows, as today (the Claude fast path`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `A protocol or crash failure is always `judge-error`.`
- Keep the Codex cwd fallback for a nonexistent or inaccessible payload cwd — `_payload_cwd_base` currently falls back to root when cwd is not a usable directory, whereas the design maps any canonical_directory OSError to an unresolvable judge-error and skips that fallback. This changes the base of relative targets and can refuse an absolute target for an irrelevant cwd.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `A relative target is joined to its base exactly as today (Claude: the root;`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `An `OSError` is the same unresolvable result, reason naming the cwd, and`
- Finish reaping the killed child after the bounded pipe drain expires — closing stdout and stderr alone leaves Popen.returncode unset in a controlled detached-pipe run; the referenced house block calls proc.wait as well. Specify a wait bounded by the remaining reap grace so FR-5's child-reap and total-time contracts both hold.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `the runner closes its pipe ends, reaps the killed child, and reports a`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › ``subprocess.TimeoutExpired` close `stdout` and `stderr`. `reap_failed` becomes true.`
- Replace the claimed unconditional-fold control with a discriminating one — folding `d.md` or `prod.py ` produces the identical value, so merely moving this pure call before the unresolvable branch leaves AC-3.1 and AC-2.4 unchanged. A removal test does not establish the required forced-fire half of this connection.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `The unconditional arm runs the fold, or the production test, before the unresolvable branch.`

## Should-fix
- Define the CANON record for an existing directory target — the canonicaliser sets names empty for a directory referent, while the resolvable-record rule admits names=0 only for an empty spelled target. As written, the reader treats a valid resolved directory as a protocol error.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `Resolvable record: `unresolvable=no`, `arm=0`, `component` empty, `names` at least 1, `prefix``

## Nit
None
AUDIT-tdd-gate-fail-opens-design-v2-END
