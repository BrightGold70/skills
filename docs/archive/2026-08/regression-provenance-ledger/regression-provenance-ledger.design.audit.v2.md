AUDIT-regression-provenance-ledger-design-v2-BEGIN
## Summary
The design provides a robust implementation strategy for the regression provenance ledger, correctly incorporating the crucial resolve-then-run methodology to avoid pytest's `rc=4` trap and correctly scoping the tombstone mechanism. Axis C evaluation confirms that all Acceptance Criteria are implemented as written in the spec. However, adversarial review (Axis A) reveals several critical timing and logical contradictions that must be resolved: the AST shape challenge is scheduled for a phase where no diff exists, `compare()` contradicts its own purity guarantee, a false positive exists in the trackedness check, and a missing intersection for `successor_pin` threatens to reintroduce the `rc=4` bug.

**Axis C: Spec Reconciliation**
| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |

## Must-fix
- **FR-5 Shape challenge timing contradiction** (Axis A) — The design proposes using `ast` to parse the BASE and HEAD versions of production `.py` files changed by the task at the 5b gate. However, the 5b gate audits the *implementation plan* (the RED phase) before the production code is written. At this stage, HEAD is identical to BASE, meaning the AST challenge will always see zero changes and never fire. The design must resolve this timing contradiction (e.g., move the shape challenge to a post-implementation phase, or redesign the mechanism).
- **`partition()` sets and `rc=4` vulnerability** (Axis A) — The design states `partition()` returns "three sets, not two" but only lists `resolving` and `missing`. More critically, it states it extracts `successor_pin` and "adds it to `resolving`" without specifying that it must first intersect it against `collected`. If an invalid `successor_pin` is blindly added to `resolving` and passed to pytest, it will abort the entire run with `rc=4` (no tests ran), recreating the exact silent no-op vulnerability established in Plan A3. `partition` must validate successor pins against `collected` and flag invalid ones as unverified renames.
- **Trackedness detection false positive** (Axis A) — The design states `git ls-files --error-unmatch <path>` yielding non-zero means `UNTRACKED`. Since this command also exits non-zero for non-existent files, checking an absent registry will falsely yield `UNTRACKED` instead of the required `PASS registered=0` (violating AC-3.1). The design must explicitly guard the trackedness check to only run if the registry file exists.
- **Contradiction regarding `compare()` purity** (Axis A) — The "Detailed Design" section states that `compare()` is pure, "takes data", and "never touches git". However, the "Tombstones and the BASE comparison" section states that `compare()` "validates the SHA first" (via `git rev-parse`) "and only then reads the path" (via `git show`). The design must resolve this contradiction by moving the `git rev-parse` and `git show` logic into the I/O shell, passing only the resulting data to the pure `compare()` function.

## Should-fix
None

## Nit
None
AUDIT-regression-provenance-ledger-design-v2-END
