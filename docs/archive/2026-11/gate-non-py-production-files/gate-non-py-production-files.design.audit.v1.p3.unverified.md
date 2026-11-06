## Summary
The design covers all 55 spec acceptance criteria in their spec form: one `listing` function shared with `resolve`, one `is_doc_data` definition used by all three hosts, and an FR-9 driver whose before side re-derives `git merge-base HEAD origin/main`. Two instructions a 5d/5e implementer would code from are false: a Claude directory write is judge-error when the chain may hold state, and the nine-suffix pin is required RED in Task 2 and also introduced in Task 6. Axis C: no restated item and no absent item.

| AC | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6, AC-5.7, AC-5.8 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5 | implemented-as-written |
| AC-7.1, AC-7.2, AC-7.3, AC-7.4 | implemented-as-written |
| AC-8.1, AC-8.2, AC-8.3, AC-8.4 | implemented-as-written |
| AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5 | implemented-as-written |
| AC-10.1, AC-10.2, AC-10.3 | implemented-as-written |
| AC-11.1, AC-11.2, AC-11.3, AC-11.4, AC-11.5, AC-11.6 | implemented-as-written |

Evidence: 26 files opened, 22 greps run.

## Must-fix
- Claude directory write is judge-error when state may exist, so the design's ALLOW premise is a false platform premise (base invariant Assumption verification). `h-mad/hooks/h-mad-tdd-gate.sh` is `set -euo pipefail`. A resolvable directory passes `_read_canon` with `names` count 0. `_chain_may_hold_state || _allow` then runs. When the chain may hold state, control reaches the `ALL_TEST_NAMES` loop, whose `for NAME in "${CANON_NAMES[@]}"` is the unguarded empty expansion. `/bin/bash` 3.2.57 on that expansion prints `CANON_NAMES[@]: unbound variable` and exits 1, and `_on_exit` emits judge-error. `ALL_SUFFIX_NAMES` is the next loop, so the empty suffix loop is not what runs. The new `[ "$DOC_DATA" = yes ] && _allow` is specified after the path exemptions, still after `ALL_TEST_NAMES`, so `is_doc_data(())` never decides this write. A preservation check written to the stated ALLOW fails on today's hook; changing the hook so that check passes turns judge-error into ALLOW, a new allow on a path the edit was required to leave alone. codex still skips an empty name set, and agy still denies at T2a.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `a directory reaches `ALL_SUFFIX_NAMES` with an empty loop, which stays `yes`, so it is ALLOW`
  quote: h-mad/hooks/h-mad-tdd-gate.sh › `for NAME in "${CANON_NAMES[@]}"; do`
- `test_doc_data_suffixes_are_the_spec_nine` is the Task 2 RED pin and is also added in Task 6, after Task 2 has already written the real `DOC_DATA_SUFFIXES`. Task 2 says the nine-suffix pin must fail by assertion before the real definitions. The R13 paragraph says Task 6 adds that test. Following Task 6, the pin is written against a constant that already matches the spec's nine strings, so it has never been seen failing (base invariant Test discrimination). Following Task 2, Task 6's "adds" sentence is wrong. The marker-tuple edit belongs in Task 6; the suffix-tuple pin belongs in Task 2.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `the nine-suffix pin and the predicate cases must then fail by assertion before the real definitions are written`
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `The same Task adds `test_doc_data_suffixes_are_the_spec_nine`, which pins `DOC_DATA_SUFFIXES` to the spec's nine strings in order.`

## Should-fix
- The `Path.suffix` mutant is not killed by `a.tar.md`. `Path("a.tar.md").suffix` is `.md`, so an end-of-basename check and a `Path.suffix` check both accept it. The spec already isolates the discriminator: `Path.suffix` is empty for a dotfile named `.md`, and that case does kill the mutant. A mutation entry whose test node is only the `a.tar.md` case survives. The dotfile case has to be the killing assertion.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › ``Path.suffix` in place of end-of-basename is killed by the `.md`-dotfile and `a.tar.md` cases.`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `a dotfile named exactly `.md`, for which `Path.suffix` is empty`
- The agy FR-9 invocation sets cwd to `<root>/.agents` because the hook runs `git -C Path.cwd().parent`. The driver builds the replay repo with `git init` and writes the plan, state, and target files. It never creates `.agents`. `subprocess` with a missing cwd raises before the hook runs, so the agy rows of AC-9.1 and AC-9.4 have no stated way to start. The driver has to create that directory before the agy call.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `That is where agy runs it: the gate takes `
  quote: h-mad/hooks/h-mad-agy-tdd-gate.py › `["git", "-C", str(Path.cwd().parent), "rev-parse", "--show-toplevel"],`

## Nit
- The overview still says the spec is v1.5 and the plan is v1.3. The in-force spec is v1.7 and the plan is v1.4; those revisions adopt this design (no bash copy, replay base re-derived, local `main` not pinned to `origin/main`).
