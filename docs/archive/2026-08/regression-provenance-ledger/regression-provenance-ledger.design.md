# Design: regression-provenance-ledger

## Executive Summary

A new stdlib-only `h_mad_wire_registry.py` holds a pure verifier over
`(registry, collected node ids, run results)` plus two thin I/O shells; the existing 5b gate's
`main()` — not its pure `check()` — calls the writer, which is the one new wire and is pinned in
both directions.

## Overview

Three constraints shape every decision below. **`check()` must stay a pure predicate**, so
registration is I/O and belongs in `main()`. **Resolve before running**, because one unresolvable
node id aborts a whole pytest selection and an empty selection collects the entire tree — both
measured. **A cannot-judge must never look like a pass**, so `missing`, `UNTRACKED` and a missing
`--base` each have a distinct, non-`PASS` outcome.

## Architecture Overview

```
h_mad_wire_pin_gate.main()                      h_mad_wire_registry
  └─ check(plan) -> dict        (pure, unchanged)
  └─ on WIREPIN: PASS  ────────────────────────►  register(entries, path)   ← THE NEW WIRE
        for each wiring task with a real WIRE-PIN                             (pinned both ways)

h_mad_wire_registry.main()   [5f]
  ├─ exists(path)?  no ────────────► PASS registered=0   (no git call at all)
  ├─ trackedness(path)              → UNTRACKED | ok      (only for a file that EXISTS)
  ├─ load(path)                     → records
  ├─ pytest --collect-only -q       → collected: set[node_id]          (subprocess 1, always)
  ├─ partition(records, collected)  → resolving / missing / unverified_renames   (pure)
  │     └─ a `renamed` successor enters `resolving` ONLY if it is in `collected`
  ├─ if resolving: pytest <ids> -q  → broken / verified                (subprocess 2, CONDITIONAL)
  │     └─ else: verified=0 broken=0, NO second call   ← empty selection would collect 1331 tests
  ├─ load_base(sha, path)  [I/O]    → base_records       (rev-parse validates, then git show)
  └─ compare(base, head)   [pure]   → undeclared removals

h_mad_wire_registry.challenge()   [5f, warning-only]      ← FR-5 lives HERE, not at 5b
  └─ ast(BASE file) vs ast(HEAD file) → cross-boundary calls added
        5b has no production diff (HEAD == BASE), so the challenge cannot run there
```

## Detailed Design

### The verifier is a pure core with two I/O shells

`partition()` and `compare()` take data and return verdict components; they never spawn a process
or touch git. The only I/O is `load()`, the two pytest calls, and one `git show`. This makes every
FR-1–FR-4 acceptance criterion unit-testable with no live pytest run, and it is why the empty-set
guard can be asserted directly rather than inferred from a suite that happens not to hit it.

### Reconciling the subprocess budget with the plan

The plan's success criterion reads "at most two subprocesses regardless of registry size". Taken
literally the design breaks it: `git check-ignore`, `git ls-files`, `git rev-parse` and `git show`
are four more. The constraint was written about the thing that could *scale* — one pytest process
per pin — and the design honours what it was protecting: **pytest invocations are at most two and
are independent of `N`.** The git calls are O(1) in registry size, run once per verify regardless of
whether the registry holds 1 wire or 1000, and several are skipped entirely (none run at all when
the registry is absent).

Restated precisely, and back-propagated to the plan: **at most two *pytest* subprocesses, and no
per-record process of any kind.** Leaving the original wording would have made a correct design read
as a violation, or invited someone to "fix" it by removing a git call that carries a guard.

### Why the second subprocess is conditional

`pytest` with no node-id arguments does not run nothing — it collects the whole tree (**1331 tests**
here). A registry whose pins are all `missing` or tombstoned would therefore report
`verified=1331`: a maximal false PASS from the gate built to prevent false passes. `run_pins()`
returns `(verified=0, broken=0)` without spawning anything when `resolving` is empty. The guard is
in the *caller*, not inside a pytest wrapper, so it is visible at the call site.

### `missing` vs `broken` — derived at different stages, deliberately

`missing` comes from set arithmetic against the collection; `broken` comes from run results. They
cannot be conflated because they are produced by different functions at different stages. A pin
absent from `collected` is never passed to the runner, so it can never be reported as passing.

**`missing` is derived from `status: "active"` records only.** A tombstoned record is a declared
removal, so it is excluded from the active partition before any set arithmetic — which is what
makes AC-2.4's rule (`missing > 0` ⇒ `FAIL`) sound without a second exemption pass: everything left
in `missing` is by construction an active wire whose pin vanished undeclared. Tombstones are
consulted only for their `successor_pin`.

**`partition()` returns three sets: `resolving`, `missing`, `unverified_renames`.** Besides the
active records, it takes the `successor_pin` of every `renamed` tombstone and — **only if that
successor is present in `collected`** — adds it to `resolving`, tagged with its tombstone's `id`. A
successor absent from `collected` goes to `unverified_renames` and is **never** handed to the
runner.

**`unverified_renames` is a FAIL condition, not a diagnostic.** It carries its own count in the
token and `unverified_renames > 0` produces `FAIL`. Dropping it on the floor would defeat FR-4
outright: an operator could tombstone a wire as `renamed`, point `successor_pin` at a test that does
not exist, and that wire would vanish from `missing` (it is tombstoned) *and* from `broken` (it was
never run) — a declared removal that verifies nothing, which is a cleaner evasion than deleting the
line. AC-4.3's rule that an unverifiable rename "is treated as `superseded`" is exactly this: it
must be re-declared naming a superseding feature, which is a deliberate act.

That intersection is not defensive tidiness, it is the A3 defect again. Passing an unresolvable
successor into the run would make pytest abort the whole selection (`rc=4`, `no tests ran`), so
**every** wire would go unverified while no test failed — the same silent no-op, re-entered through
the one path that had not been guarded. Nothing reaches the runner that did not come out of
`collected`, and that is an invariant of `partition()` rather than a caller's responsibility.

Without the injection at all, AC-4.3's "resolves **and** passes" would be half-checked: a rename
could be declared against a successor that exists but fails. A successor that runs and fails is
reported under its tombstone's `id`, not as an anonymous `broken` pin, so the operator is told which
declared rename is unsound.

### Mapping a batch failure back to its wire (AC-2.2) — measured, not assumed

`run_pins()` recovers failing node ids from pytest's short-summary lines, which are emitted in exact
node-id form. Probed with a deliberate 2-pass/2-fail batch:

```
$ pytest test_probe_batch.py -q
FAILED test_probe_batch.py::test_beta_fails - assert 1 == 2
FAILED test_probe_batch.py::test_delta_fails - AssertionError: assert 'a' == 'b'
2 failed, 2 passed

$ … | sed -n 's/^FAILED \([^ ]*\).*/\1/p'
test_probe_batch.py::test_beta_fails
test_probe_batch.py::test_delta_fails
```

The id is matched by **string equality** against each record's `pin`, which is how a failure is
attributed to its `owning_feature`. No re-run of the failures is required, so nothing depends on
those ids being re-dispatchable.

`--junitxml` was **rejected on evidence**: its `classname` is dotted
(`h-mad.tests.test_h_mad_phase7_preconditions.TestArchreviewLadder`), not the `path::Class::test`
node-id form, so recovering a pin would mean reversing a lossy transform — a directory containing a
`.` makes it ambiguous. The short-summary line already carries the exact key.

A `pin` that appears in neither the passed nor the failed set after a run that did execute is
reported as an internal inconsistency, not silently counted as verified.

### Verdict grammar

```
WIREREG: PASS      registered=N verified=K broken=0 missing=0 unverified_renames=0
                                                              undeclared_removals=0  exit 0
WIREREG: FAIL      registered=N verified=K broken=J missing=M unverified_renames=R
                                                              undeclared_removals=U  exit 0
                     (J>0, or M>0, or R>0, or U>0)
WIREREG: UNTRACKED registered=N verified=K broken=J missing=M unverified_renames=R
                                                              undeclared_removals=U  exit 0
                     (never PASS)
                   → missing --base, invalid --base, unreadable registry             exit 2
```

`undeclared_removals=U` carries FR-4's `compare()` result. It is in the grammar because AC-4.1
makes an undeclared removal a `FAIL`, and v1.6's amendment — *a count that drives a FAIL must be in
the grammar* — applies to it: without the count, that verdict prints `FAIL` beside `broken=0
missing=0 unverified_renames=0` and is unreadable.

**`UNTRACKED` does not short-circuit the run.** Trackedness is determined early but reported at the
end, after loading and verifying, so `registered=N` and the other counts are real on that verdict
too (AC-3.4 requires the count on **every** verdict). An untracked registry containing a broken pin
is a genuine `FAIL` *and* untracked; the token reports `UNTRACKED` because it is the more actionable
finding — entries that will not survive a clone make the other counts provisional — and the detail
lines carry the broken wires regardless. Short-circuiting on trackedness would have produced
`UNTRACKED registered=0` for a populated registry, which is simply false.

`registered=N` prints on **every** verdict including `PASS`, so a green gate over an empty registry
is legible as exactly that. `UNTRACKED` is a verdict (exit 0) because the registry was readable and
the finding is about the *repo*, not about the tool's ability to judge; a missing `--base` is exit 2
because the comparison could not be performed at all. That split follows the established grammar:
`UNSHAPED`/`UNREADABLE` exit 2, real verdicts exit 0.

### Trackedness detection (FR-3)

**Existence is checked first, and short-circuits.** If the registry file does not exist the result
is `PASS registered=0` (AC-3.1) and no git command runs at all. This ordering is mandatory:
`git ls-files --error-unmatch` exits **non-zero for an absent path** as well as for an untracked one
(measured: rc=1 either way), so running it first would report `UNTRACKED` for every repo that has
simply never seeded a registry — turning the intended no-op into a blocking verdict for the common
case.

Only for a file that exists: `git check-ignore -q <path>` (exit 0 = ignored) plus
`git ls-files --error-unmatch <path>` (non-zero = untracked). Either condition yields `UNTRACKED`.
The remedy string is computed from which condition fired — an ignored path is told to add `!.h-mad/wires.jsonl`, an untracked one is
told to `git add` it — because a generic message sends the operator to the wrong fix. This matters
concretely: `.h-mad/` is ignored in this repo and not in HemaSuite, so the identical gate must say
different things.

### Tombstones and the BASE comparison (FR-4)

Removal edits the record in place: `status: "removed"` plus `removal_provenance`,
`removed_by_feature`, and `successor_pin` when `renamed`. `compare()` therefore looks for ids
present at BASE and **absent** at HEAD — a tombstoned id is still present, so it is not a removal.
`renamed` is verified mechanically: `successor_pin` must appear in `collected` and pass in the run.

**One git primitive, two callers — and the SHA validation lives *in the primitive*.**
`git_show(sha, path) -> str | None` validates the SHA (via `git rev-parse --verify --quiet
<sha>^{commit}`, raising on rc=1), runs `git show`, and returns the file's text or `None` when the
path did not exist at that commit. Validation must sit here and **not** in `load_base()`: the AST
challenge calls `git_show` directly, so a validator one level up would leave the challenge accepting
an unvalidated SHA and reading "invalid commit" as "file did not exist at BASE" — a false clean by
the same mechanism the validation was added to prevent. `load_base(sha, path) -> list[record]` is a thin JSONL parser **on top of**
it, and the AST challenge calls `git_show` **directly** for `.py` files. An earlier draft said the
challenge read `.py` files "through the same `load_base()` shell", which was a contradiction —
`load_base` parses JSONL and would fail on Python source. The split removes it: the shared thing is
`git_show`, not `load_base`.

**The git calls live in the I/O shell, not in `compare()`.** `load_base(sha, path)` does the SHA
validation and the `git show`, and hands `compare(base_records, head_records)` two plain lists.
`compare()` performs no I/O and does not know git exists — which is what keeps FR-4 unit-testable
without a repository and what makes "pure core, thin shells" true rather than merely claimed. An
earlier draft of this design asserted `compare()` was pure in one section and gave it two git
commands in another; the split below is the resolution.

**`git_show()` validates the SHA before reading the path, because `git show` cannot tell the two
failures apart.** Both an absent path at a valid commit and an invalid commit exit **128** —
measured:

```
$ git show 88a31ff:.h-mad/wires.jsonl        rc=128  fatal: path '…' does not exist in '88a31ff'
$ git show deadbeef…:.h-mad/wires.jsonl      rc=128  fatal: invalid object name 'deadbeef…'
```

So an invalid `--base` would silently yield "empty base set" — i.e. *no undeclared removals* — which
is a false clean. The discriminator is **not** stderr parsing: `git rev-parse --verify --quiet
<sha>^{commit}` returns **rc=0** for a valid commit and **rc=1** for an invalid one (measured), a
structured check with no string matching. `git_show()` therefore validates the SHA first — an
invalid one is exit 2, an operational error — and only then reads the path, at which point a 128 is
unambiguously "the path did not exist at BASE", so it returns `None`; `load_base()` turns that into
an empty list, every id is new, and that is not an error.

### Registration is in `main()`, and that call is the wire (FR-6)

`check()` returns `{"verdict", "tasks", …}` and stays pure. `main()`, on `WIREPIN: PASS`, extracts
each `wiring` task carrying a real `WIRE`/`WIRE-PIN` and calls `registry.register()`. Two mutations
pin it, per `invariants.base.md:107`:

- **Removal direction** — delete the `register()` call, leave `h_mad_wire_registry` intact: a test
  asserting the registry file gained the entry must fail. The callee still imports and its own unit
  tests still pass, which is exactly why the module-level revert cannot establish this.
- **Unconditional direction** — make registration fire for every task regardless of shape: a
  fall-through test asserting a `new-behaviour` task registers **nothing** must fail. Without this,
  a hook that registers everything would pass the removal pin while silently polluting the registry.

### Shape challenge mechanism (FR-5) — AST, at 5f, not 5b

**The challenge runs at 5f, not 5b.** 5b audits the *impl-plan* (`SKILL.md:271`); 5c branches, 5d
writes RED tests and 5e writes production (`:276`, `:277`, `:282`). At 5b there is no production
diff at all — HEAD equals BASE — so an AST comparison there would see zero changes and could never
fire. Placing it at 5b would have shipped a guard that is structurally incapable of firing while
reporting `challenges=0` as though it had looked, which is the precise class of silent no-op this
feature exists to remove. It therefore runs at 5f alongside the verifier, against the same
`--base` (the 5c baseline) the verifier already takes.

The consequence is that the challenge is **retrospective**: it reports "this task you declared
`new-behaviour` in fact wired something", after the wiring exists. That is the correct strength for
a warning-only mechanism and is exactly what feeds the measurement FR-5 exists to produce. Making
the declaration *binding* at plan time is a different mechanism against a different artifact, and
is explicitly out of scope until this one's rates are known.

For each production `.py` the task changed, parse the BASE and HEAD versions with stdlib `ast` and
collect two sets: imported module names (`Import`/`ImportFrom`) and the root of each call target
(`Call` → `Name`/`Attribute` root). The challenge fires when HEAD contains a call or import that
BASE did not **and** the target resolves to a different boundary than the file's own.

**Attribution — how the challenge knows whose task a file belongs to (AC-5.1).** It takes
`--impl-plan <path>` and reuses the 5b gate's existing `_parse_tasks()` rather than re-parsing the
document (single-source contract). Each task yields its declared `Task shape` and its
`Production file` list; the challenge maps each changed `.py` back to the task that claims it. A
changed file claimed by **no** task is reported separately as `unattributed` — it is not silently
dropped, because an unclaimed production change is itself worth surfacing. A file claimed by more
than one task is attributed to all of them and counted once.

**The changed-file set comes from `git diff --name-status --diff-filter=d <base> HEAD -- '*.py'`**,
run with `cwd=repo`, filtered to production paths (test paths are never challenged) and to files not
already claimed by a `wiring` task.

Excluding deletions is load-bearing, not tidiness: an unfiltered diff includes files **deleted** in
HEAD, and parsing the HEAD version of a deleted file raises `FileNotFoundError` — crashing the
verifier at 5f rather than reporting a verdict. Probed on a real deletion commit: unfiltered **62**
paths, deletions **1**. A deleted file cannot add a cross-boundary call, so excluding it loses
nothing.

**The exclusion is `d`, not an `AM` allowlist — corrected at impl-plan audit cycle 4.** `AM` also
satisfies the deletion constraint, but it silently drops **renames**. Probed on a tree carrying all
four statuses at once:

```
A pkg/brandnew.py   D pkg/doomed.py   M pkg/keep.py   R073 pkg/tomove.py -> pkg/moved.py

--diff-filter=AM -> brandnew.py, keep.py                   # moved.py silently absent
--diff-filter=d  -> brandnew.py, keep.py, moved.py         # rename kept, deletion still excluded
```

`pkg/moved.py` had gained a new function in the same commit, so under `AM` a rename is a free pass
and every cross-boundary call it introduces is invisible. The earlier probe exercised only a
deletion, which is how the gap survived to the impl-plan. `d` is exclusion-based, so a git status
letter this design did not anticipate is included rather than dropped.

**And `--name-status`, not `--name-only`, because a renamed file's BASE version lives at its OLD
path.** `--name-only` prints just the new path, so `git_show(base, new_path, repo)` returns `None`,
the file reads as brand-new, and every *pre-existing* cross-boundary call in it is reported as an
addition — trading the false negative above for a false-positive flood. Probed:

```
$ git diff --name-status --diff-filter=d BASE HEAD -- '*.py'
R062<TAB>pkg/tomove.py<TAB>pkg/moved.py

$ git show BASE:pkg/moved.py    fatal: path 'pkg/moved.py' exists on disk, but not in 'BASE'
$ git show BASE:pkg/tomove.py   import json…                     # the real BASE version
```

Each changed file therefore resolves to a `(base_path, head_path)` pair: equal for `M`, old→new for
`R`, and `base_path = None` for a true addition — which the caller must handle as an empty BASE AST
rather than passing `None` into `git_show`. Attribution matches on `head_path`, since that is what
an impl-plan's `Production file` names.

**Both sides are normalised to repo-relative POSIX paths before matching.** `git diff --name-only`
emits repo-relative paths **regardless of the cwd it runs from** — probed from the repo root and
from `h-mad/scripts/`, identical output (`h-mad/scripts/h_mad_phase7_preconditions.py` both times),
so the normalisation has a fixed reference on that side. An impl-plan's
`Production file` is written by hand and may be a bare basename, a `./`-prefixed path, or an
absolute one. Normalisation is: strip a leading `./`, make absolute paths repo-relative, and fall
back to **suffix match** on the path segments when no exact match is found. An unresolvable claim
is reported as `unattributed` *and* named, so a systematically mis-written plan surfaces as a
pattern rather than as silent false positives — the failure mode here is a legitimate task claim
being read as unattributed, which would make the challenge noisy exactly where it must not be. Without that list the challenge has nothing to
iterate and `unattributed` cannot be computed at all — it was assumed rather than specified until
now. Each BASE version is then read via `git_show(base, path)`; `None` means the file is new, so
every cross-boundary call in it is an addition.

**Acknowledgment (AC-5.3).** A challenge is acknowledged with the repo's established mechanism, not
a new one: an `## Acknowledged-not-fixed` section in the impl-plan's audit sidecar, the same
construct the audit gate already honours for deferred should-fix items. **The parsing is imported
from `h_mad_audit_gate`, never reimplemented** — that module is the authoritative parser for this
section, and a second implementation would drift silently, which is precisely the single-source
violation the base invariant forbids. If the needed helper is not currently exported, it is
factored out there and imported here rather than copied. The challenge reports
`challenges=<raised> acknowledged=<matched>`; an acknowledgment naming a challenge that was not
raised is reported as `stale`, so the section cannot silently accumulate entries that no longer
correspond to anything. Because FR-5 is verdict-neutral, acknowledgment changes no outcome — it
exists solely to make the *residual* count meaningful when a later feature decides whether to
promote the challenge to a hard failure.

**Resolving an AST target to a boundary.** The AST yields Python namespaces (`h_mad_wire_registry`,
`pkg.mod`); boundaries are file globs. The mapping is explicit and stdlib-only: build a
module-name → repo-path index once per run by walking the repo for `*.py` and keying each file by
its module name (stem) *and* its dotted package path where `__init__.py` chains exist. An AST target
is resolved by looking up its root name in that index; the resulting path is matched against the
globs. **Unresolvable targets — stdlib, third-party, and anything not found in the index — are
skipped, not guessed**: a name that resolves to no file in this repo cannot cross one of this
repo's boundaries. Ambiguity (two files with the same stem) is reported rather than silently
resolved to the first, because picking one would fabricate a crossing.

This is a heuristic, and it is the second reason FR-5 is warning-only: it is a static name index,
not an import resolver, so a re-exported or aliased symbol may resolve to the wrong file or to none.

Boundaries are configuration, never hardcoded (AC-5.4): `.h-mad/boundaries.json` maps globs to
boundary names, e.g. `{"h-mad/scripts/*": "scripts", "h-mad/tests/*": "tests"}`. A repo with no
such file declares no boundaries, so nothing can cross one and the challenge never fires — the
correct default for a project that has not expressed its topology.

Regex over `git diff` was rejected: a changed call site is routinely reindented or line-wrapped, so
a textual diff reports crossings that did not change and misses ones that did. AST compares
*structure*, so reformatting is invisible to it.

**Known limitation, and the reason FR-5 ships warning-only:** `ast` sees static calls. Dynamic
dispatch, `getattr`, registry/plugin lookup and config-driven binding are invisible to it — and
those are exactly how several of the lost wires in HemaSuite were bound. The challenge is therefore
a floor on detection, never a proof of absence, which is why it may not gate a verdict until its
false-negative and false-positive rates have been measured.

### Runtime read-back inside `register()` (AC-6.2)

The read-back is **production behaviour, not a test step**. `register()` writes, then re-reads the
registry and compares the stored record to what it intended to write, raising when they differ. The
distinction is load-bearing: a read-back that exists only in a test proves the writer worked *on the
day the test ran*, whereas a read-back inside `register()` fails the run that drops a write.

This is not hypothetical. Earlier this session the same pattern caught a real bad write: an
`archreview` value captured with a two-line `$(...)` was refused by the writer, and the read-back —
not the exit code, and not schema validation — is what surfaced it. Schema validation could not
have: `archreview` is not a `required` field, so a record with it absent validates clean. The same
asymmetry applies here.

### Live-registry protection (J18 class)

The writer resolves *where* state is written, which is the resolver class that once redirected the
whole suite's writes onto the live pin file while reporting 642 passed. `conftest.py` already
carries `_protect_live_pin_file` (session-scoped, autouse); this adds a sibling guard for
`.h-mad/wires.jsonl` with the same shape — snapshot, restore if moved, fail loudly naming the cause.
Per-test `tmp_path` redirection is necessary and **not** sufficient: the failure mode is a mutation
that disables the redirection branch, which no test using that branch can detect.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| Registry schema, `load`/`register` (with runtime read-back)/`partition` (3 sets)/`run_pins`/`compare` (SHA-validated), CLI | `h-mad/scripts/h_mad_wire_registry.py` | **new** | FR-1–FR-4 |
| Registration call on `WIREPIN: PASS` | `h-mad/scripts/h_mad_wire_pin_gate.py` | modify | FR-6 |
| AST shape challenge (warning-only), **at 5f** — 5b has no production diff to compare | `h-mad/scripts/h_mad_wire_registry.py` (`challenge` subcommand) | new | FR-5 |
| Boundary map consumed by the shape challenge; absent ⇒ no boundaries ⇒ challenge never fires | `.h-mad/boundaries.json` (per-repo data) | **new** | FR-5 (AC-5.4) |
| Live `.h-mad/wires.jsonl` snapshot/restore guard | `h-mad/tests/conftest.py` | modify | J18 protection |
| 5b registers (invocation carries `--feature`) · 5f re-verifies · **five** named halts with `[H-MAD]` markers | `h-mad/SKILL.md` | modify | FR-2, FR-6 |
| Registry + verifier unit tests | `h-mad/tests/test_h_mad_wire_registry.py` | **new** | FR-1–FR-4 |
| Registration wire pins (both directions) + shape-challenge tests | `h-mad/tests/test_h_mad_wire_pin_gate.py` | modify | FR-5, FR-6 |

## Implementation Order

1. **Registry module + schema + `load`** — everything else consumes it. Includes the conftest guard,
   which must exist before any test writes a registry.
2. **`partition` + `run_pins`** with the empty-set guard — the verifier core, pure and unit-testable.
3. **`compare` + tombstones + `--base`** — FR-4, depends on the schema from step 1.
4. **CLI + verdict grammar + trackedness** — FR-2/FR-3, assembles steps 2–3 into `WIREREG:`.
5. **Registration hook in the 5b gate** — `wiring` shape, both mutation directions. Last of the code
   because it depends on a working `register()`.
6. **Shape challenge (warning-only), as a 5f subcommand** — depends on step 4's `--base` plumbing,
   not on 1–3; verdict-neutral by construction.
7. **`SKILL.md` protocol text + doc tests** — 5b registers, 5f re-verifies and challenges.

Nothing here arms a blocker before its means of satisfaction exists, because an absent registry is a
no-op: steps 1–4 can land while the registry is empty and change no verdict.

## Data Model / Schema Changes

`.h-mad/wires.jsonl` — one JSON object per line, per repo, **new file**:

| field | type | notes |
|---|---|---|
| `kind` | `"wire"` | validated enum; only value accepted this feature |
| `id` | string | unique key; duplicate on write updates in place |
| `caller` | string | `path.py:symbol` |
| `callee` | string | symbol reached |
| `pin` | string | pytest node id, the re-run handle |
| `owning_feature` | string | named when the wire breaks |
| `registered_ts` | ISO-8601 string | |
| `status` | `"active"` \| `"removed"` | default `active` |
| `removal_provenance` | `"superseded"` \| `"pinned-a-defect"` \| `"renamed"` | tombstones only |
| `removed_by_feature` | string | required on **every** tombstone — who removed it |
| `superseding_feature` | string | required when `removal_provenance == "superseded"` — what replaced it |
| `successor_pin` | string | required when `removal_provenance == "renamed"` |

The last three answer three different questions and none substitutes for another: *who removed
this*, *what feature replaced it*, *which test now carries the guarantee*. `removed_by_feature`
alone would leave a `superseded` tombstone attributable but with no way to find the successor — the
operator learns a wire was retired and nothing about what took over.

No change to `h_mad_state_schema.json` — the registry is a separate per-repo file, not
orchestrator state.

## API / Interface Changes

```
h_mad_wire_registry.py verify    [--registry PATH] [--base SHA] [--rootdir PATH]
h_mad_wire_registry.py register  --id … --caller … --callee … --pin … --feature …
h_mad_wire_registry.py challenge --base SHA --impl-plan PATH
                                 [--boundaries PATH] [--ack PATH]
```

`challenge` flags: `--base` (required, the 5c baseline — the AST comparison has nothing to compare
without it, so its absence is exit 2 like `verify`'s); `--impl-plan` (required, the source of task
shapes and production-file claims, parsed via the 5b gate's `_parse_tasks`); `--boundaries`
(default `.h-mad/boundaries.json`, absent ⇒ no boundaries ⇒ no crossings possible);
`--ack` (default the impl-plan's audit sidecar, read for `## Acknowledged-not-fixed`).
Output: `WIRECHALLENGE: challenges=N acknowledged=K unattributed=U dangling=D stale=S ambiguous=A`,
or `WIRECHALLENGE: NOT_COMPARED reason=<no_production_diff|no_boundaries>` when the comparison could
not be performed at all — always exit 0, verdict-neutral by construction (AC-5.2).

`dangling=D` is separate from `unattributed=U` deliberately: a changed file nobody claimed and a
claim matching no changed file are opposite directions with opposite remedies, so summing them makes
both unactionable. `ambiguous=A` counts module stems resolving to two files, which are reported
rather than resolved, because picking one would fabricate a crossing. `NOT_COMPARED` is a distinct
token rather than prose because `challenges=0` from a run that looked and from a run that *could
not* look are otherwise the same string — the silent no-op this feature exists to remove.

- `--registry` default `.h-mad/wires.jsonl`; absent file ⇒ `PASS registered=0`.
- `--base` omitted ⇒ **exit 2** (the FR-4 comparison cannot run).
- `h_mad_wire_pin_gate.py` takes a new `--feature <name>` flag supplying `owning_feature`. It is
  **not** derived from the plan's filename: the gate is routinely run on `/tmp` fixtures, so a
  filename-derived value would register wires under stems like `test_plan`, and a wrong
  `owning_feature` is worse than a missing one. Absent the flag the gate registers nothing and says
  so, leaving the `WIREPIN:` verdict unaffected. `SKILL.md`'s 5b invocation must pass it, or
  registration is a silent no-op in production.
- **Five** `[H-MAD]` halt reasons consumed by `SKILL.md` §5f — one per `FAIL` driver, since a
  verdict exits 0 and the marker is the only diagnosable signal: `step5f:wire_regression:<id>` on
  `broken`, `step5f:wire_pin_missing:<id>` on an undeclared `missing`, `step5f:registry_untracked`
  on `UNTRACKED`, `step5f:undeclared_removal:<id>` on an undeclared removal (AC-4.1), and
  `step5f:unverified_rename:<id>` on an unverifiable rename (AC-4.3). The last two were added at
  impl-plan audit cycle 1: both were already `FAIL` conditions with no marker, so a run could halt
  anonymously.
- `h_mad_wire_pin_gate.check()` signature and `WIREPIN:` grammar unchanged — additive only.

## Error Handling Strategy

Verdicts are data; only cannot-judges raise. `load()` raises on a malformed line naming the line
number (a skipped line is an unguarded wire reporting as guarded); the CLI turns that into exit 2.
Missing `--base` and an unreadable registry are exit 2. Everything else — including `broken`,
`missing` and `UNTRACKED` — is a token at exit 0, so a stricter gate never registers as a
`PostToolUseFailure` and leaks into coexisting plugins.

## Test Strategy

- **Unit, no live pytest** — `partition`, `compare`, `load`, and the verdict assembler are pure.
  The empty-resolving-set case is asserted against `run_pins` directly, including that it spawns
  **no** subprocess.
- **Subprocess-level** — one test proves the two-call shape and one proves the one-call shape.
- **Wire pins** — both mutation directions on the 5b→writer call.
- **Doc tests** — `SKILL.md` 5b/5f contract and the three halt reasons.
- **Isolation** — the conftest guard is itself tested by deliberately re-introducing the leak.
- **Regression** — full coupled suite green with the registry absent; branch-point count measured
  fresh, not carried.

## Test Plan

| Scenario | Asserts | AC |
|---|---|---|
| record missing a required field | rejected at write | AC-1.1 |
| `kind: "counter"` | rejected — enum is wire-only | AC-1.2 |
| duplicate `id` written twice | one record, updated | AC-1.3 |
| malformed line | raises, names the line number | AC-1.4 |
| 2 pins, 1 fails | `FAIL registered=2 verified=1 broken=1 missing=0` | AC-2.1, AC-2.2 |
| broken wire's owner named in output | content, not just count | AC-2.2 |
| renamed pin, undeclared | `missing=1`, distinct from `broken` | AC-2.3, AC-2.4 |
| **all pins missing** | `verified=0 broken=0`, **second subprocess never spawned** | AC-2.1 |
| verdict/exit discipline | exit 0 on PASS/FAIL/UNTRACKED; 2 on unreadable | AC-2.5 |
| registry absent | `PASS registered=0`, no-op | AC-3.1 |
| registry gitignored | `UNTRACKED`, not `PASS` | AC-3.2 |
| remedy text differs ignored vs untracked | content | AC-3.3 |
| `registered=N` present on PASS | content | AC-3.4 |
| id absent at HEAD, no tombstone | `FAIL`, names id + owning feature | AC-4.1 |
| tombstone missing provenance | rejected | AC-4.2 |
| `superseded` tombstone with no `superseding_feature` | rejected | AC-4.2 |
| tombstone of any provenance with no `removed_by_feature` | rejected | AC-4.2 |
| `renamed` whose successor fails | treated as unverified, not clean | AC-4.3 |
| declaration found from the removed id | the record at that id | AC-4.4 |
| missing `--base` | exit 2 | plan v1.3 |
| undeclared cross-module call, `new-behaviour` shape | warning raised, naming task + crossing | AC-5.1 |
| that warning | `WIREPIN`/`WIREREG` verdicts unchanged | AC-5.2 |
| raised/acknowledged counts reported | content | AC-5.3 |
| boundary config honoured | not hardcoded | AC-5.4 |
| passing 5b wiring task | registry entry appears, no operator action | AC-6.1 |
| `register()` read-back is runtime, not test-only | stub the write to drop silently ⇒ `register()` itself raises | AC-6.2 |
| `renamed` successor injected into `resolving` | successor is actually executed, failure reported under its tombstone id | AC-4.3 |
| invalid `--base` sha | exit 2, NOT an empty base set | design v1.1 |
| registry absent at a valid BASE | empty base set, every id new, no error | design v1.1 |
| boundary map absent | challenge never fires | AC-5.4 |
| reindent/line-wrap a call site with no semantic change | challenge does NOT fire (AST, not regex) | AC-5.1 |
| **`renamed` successor NOT in `collected`** | goes to `unverified_renames`, **never** reaches the runner; no `rc=4` abort | AC-4.3, plan A3 |
| registry absent | trackedness check never runs (no false `UNTRACKED`) | AC-3.1 |
| `compare()` called with two record lists | performs no git call; unit-testable outside a repo | design v1.2 |
| challenge invoked at a point with no production diff | reports that it could not compare, never `challenges=0` | AC-5.3 |
| changed file claimed by a `wiring` task | no challenge raised | AC-5.1 |
| changed file claimed by NO task | counted as `unattributed`, not dropped | AC-5.1 |
| acknowledgment naming a challenge never raised | counted `stale` | AC-5.3 |
| tombstoned record whose pin is gone | NOT in `missing` (declared removal) | AC-2.4 |
| `challenge` without `--base` | exit 2 | design v1.3 |
| `SKILL.md` states auto-registration + registry location | doc | AC-6.3 |
| **delete the `register()` call, callee intact** | wire pin FAILS | base invariant |
| **registration fires unconditionally** | fall-through test FAILS | `invariants.base.md:107` |
| mutate the writer's path branch | conftest guard fires, live file restored | J18 |

## Invariant Compliance

**Base — audit-gate signal discipline.** Verdicts exit 0; exit 2 only for unreadable input and a
missing `--base`. A stricter gate must not begin registering as a tool failure. Complies.

**Base — connection enforcement.** The one new wire (5b `main()` → `register()`) is pinned in both
directions, removal and unconditional-fire. Complies.

**Base — mutation verification.** Every new guard is mutated to its permissive value, including the
doc guards and the conftest guard, via `h_mad_mutation_harness.py` with `root` passed explicitly.

**Base — single-source contract.** Registry parsing lives only in `h_mad_wire_registry.py`; the 5b
gate calls it rather than re-implementing. `WIRE`/`WIRE-PIN` parsing stays in the existing
`_parse_tasks`. Complies.

**Base — no new external dependency.** Stdlib Python plus `git` and `pytest`, both already required.

**Base — backward compatibility.** Absent registry ⇒ `PASS registered=0`, so every existing repo and
in-flight feature is unaffected. `WIREPIN:` grammar and `check()`'s signature are unchanged;
additions only. No orchestrator-state schema change.

**Base — marker discipline.** Five named halts — one per `FAIL` driver — each emitting `[H-MAD]`, so
a 5f stop is diagnosable from logs alone (`invariants.base.md:61`). The set named in `SKILL.md` is
asserted equal to the set the verifier can emit, so neither side can gain a reason without the
other. Complies.

**Base — operator-override preservation.** FR-5 is warning-only and verdict-neutral, so the operator
is never blocked by an unproven heuristic; FR-4 provenance is the deliberate, recorded escape for a
wire that should die.

**Project — skill self-containment.** All new code is inside `h-mad/`; no cross-skill import; the
registry path is repo-relative. Complies.

**Project — skill manifest integrity.** `SKILL.md` gains 5b/5f behaviour, so its contract is updated
in the same commit; frontmatter `name`/`description` unchanged. Complies.

## Version History
- v1.0: Initial design draft. Places registration in `main()` rather than `check()` so the pure
  predicate stays side-effect-free and the call itself becomes the pinnable wire; makes the second
  pytest subprocess conditional because an empty selection collects 1331 tests; and splits exit
  codes so `UNTRACKED` is a verdict while a missing `--base` is an operational error.
- v1.1: Design audit cycle 1 — 2 must-fix, 2 should-fix. All four premises checked; one was probed
  and yielded a better remedy than the one proposed.
  1. **FR-5 had no mechanism at all** — it appeared in the Implementation Order and Test Plan with
     no design behind it. Now specified: stdlib `ast` over the BASE and HEAD versions of each
     changed production file, comparing import and call-target sets, with boundaries read from
     `.h-mad/boundaries.json`. Regex over `git diff` was rejected — a reindented call site reports a
     crossing that did not change. The AST limitation (dynamic dispatch, `getattr`, config-driven
     binding are invisible) is stated, and is the substantive reason FR-5 ships warning-only.
  2. **The read-back was specified as a test, not as production behaviour.** Now inside
     `register()`: write, re-read, compare, raise on mismatch. A read-back living only in a test
     proves the writer worked the day the test ran; one inside `register()` fails the run that drops
     a write. Precedent from this session: the same pattern caught a real bad `archreview` write that
     schema validation could not, because the field is not `required`.
  3. (should-fix) **`successor_pin` was never executed.** `partition()` now returns three sets,
     injecting each `renamed` tombstone's successor into `resolving` tagged with its tombstone id —
     otherwise AC-4.3's "resolves **and** passes" was half-checked and a rename could be declared
     against a successor that exists but fails.
  4. (should-fix) **`git show` cannot distinguish an absent path from an invalid sha** — both exit
     128, measured. An invalid `--base` would have silently produced "empty base set", i.e. a false
     "no undeclared removals". The reviewer proposed parsing stderr; probing found a cleaner
     discriminator, `git rev-parse --verify --quiet <sha>^{commit}` (rc 0 vs 1), so the SHA is
     validated first and no string matching is needed. Premise accepted, prescription improved.
- v1.2: Design audit cycle 2 — 4 must-fix. All four premises checked, two probed. Three were
  contradictions inside this design rather than gaps against the spec.
  1. **FR-5 was placed where it could never fire.** 5b audits the impl-plan (`SKILL.md:271`);
     branch, RED and production come at 5c/5d/5e. At 5b HEAD equals BASE, so an AST comparison sees
     zero changes always — a guard structurally incapable of firing while reporting `challenges=0`
     as though it had looked. Moved to **5f**, reusing the verifier's `--base`. The challenge is
     therefore retrospective ("this task you called `new-behaviour` in fact wired something"), which
     is the right strength for a warning-only mechanism; making the declaration binding at plan time
     is a different mechanism against a different artifact and stays out of scope.
  2. **`partition()` would have re-entered the A3 defect.** It added a `renamed` successor to
     `resolving` without intersecting against `collected`; an unresolvable successor handed to
     pytest aborts the entire selection (`rc=4`), leaving every wire unverified with no failure.
     Now three sets, and nothing reaches the runner that did not come out of `collected` — an
     invariant of `partition()`, not a caller's duty.
  3. **Trackedness would have false-positived on the common case.** `git ls-files --error-unmatch`
     exits non-zero for an *absent* path as well as an untracked one (measured rc=1 either way), so
     every repo that had simply never seeded a registry would have reported `UNTRACKED` instead of
     the required `PASS registered=0`. Existence is now checked first and short-circuits before any
     git call.
  4. **`compare()` was declared pure in one section and given two git commands in another.**
     Resolved by moving SHA validation and `git show` into `load_base()`, leaving `compare()` a
     function of two record lists — which is what makes FR-4 testable without a repository.
- v1.3: Design audit cycle 3 — 2 must-fix, 2 should-fix. All four in FR-5, which had been specified
  as an intent rather than a mechanism.
  1. **Attribution was undefined** — the challenge had no way to know which task claimed a changed
     file or what shape that task declared. Now takes `--impl-plan` and reuses the 5b gate's
     `_parse_tasks()` (single-source contract) to map file → task → shape. A file claimed by no
     task is reported as `unattributed` rather than dropped: an unclaimed production change is
     itself worth surfacing.
  2. **Acknowledgment had no home** — AC-5.3 counts acknowledgments with nowhere to record one.
     Reuses the repo's existing `## Acknowledged-not-fixed` sidecar construct rather than inventing
     a mechanism; an acknowledgment naming a challenge that was never raised counts as `stale`, so
     the section cannot silently accumulate dead entries.
  3. (should-fix) BASE files for the AST comparison are read with `git show <base>:<path>` through
     the same `load_base()` shell; a path absent at BASE means the file is new.
  4. (should-fix) `missing` is stated to derive from `status: "active"` records only, which is what
     makes AC-2.4 sound without a second exemption pass — everything in `missing` is by
     construction an undeclared vanished pin.
  Also added: `challenge`'s CLI surface, absent from API/Interface Changes entirely until now.
- v1.4: Design audit cycle 4 — 5 must-fix. All five checked; two were probed.
  1. **Batch-failure attribution was asserted without evidence.** Probed: a 2-pass/2-fail batch
     emits `FAILED <nodeid> - <msg>` in exact node-id form, cleanly recovered by `sed`, and matched
     to a record by string equality on `pin`. `--junitxml` was rejected **on evidence** — its
     `classname` is dotted, not node-id form, so recovering a pin means reversing a lossy transform
     that a `.` in a directory name makes ambiguous.
  2. **Sidecar parsing would have been a second implementation.** `## Acknowledged-not-fixed` is
     already parsed authoritatively by `h_mad_audit_gate`; the helper is imported (factored out
     there if not currently exported), never copied.
  3. **The changed-file set was assumed into existence.** Now explicit:
     `git diff --name-only <base> HEAD -- '*.py'`, production paths only — without it
     `unattributed` could not be computed at all.
  4. **The design silently violated the plan's own subprocess budget.** The plan said "at most two
     subprocesses"; the design adds four git calls. The constraint was about work that scales with
     `N`, so both documents now say **at most two *pytest* subprocesses and no per-record process**.
     Left unreconciled, a correct design reads as a violation — or someone "fixes" it by deleting a
     git call that carries a guard.
  5. **`load_base()` was given two incompatible return types.** Split: `git_show()` is the shared
     I/O primitive returning text or `None`; `load_base()` is a JSONL parser on top of it; the AST
     challenge calls `git_show` directly. The earlier "same shell" wording would have fed Python
     source to a JSONL parser.
- v1.5: Design audit cycle 5 — 2 must-fix, 2 should-fix. One must-fix was introduced by cycle 4's
  own fix, which is the reason it is recorded here rather than quietly corrected.
  1. **`unverified_renames` was collected and then dropped.** Cycle 3 added the set to stop an
     `rc=4` abort but never connected it to a verdict, so an operator could tombstone a wire as
     `renamed`, point `successor_pin` at a non-existent test, and have that wire disappear from
     `missing` (tombstoned) *and* `broken` (never run) — a declared removal verifying nothing, and a
     cleaner evasion than deleting the line. Now its own count, and `> 0` is `FAIL`.
  2. **SHA validation had two homes after cycle 4's split.** `git_show` was said to validate in one
     paragraph and `load_base` in the next. Since the AST challenge calls `git_show` directly,
     validation must live *there* — otherwise the challenge takes an unvalidated SHA and reads
     "invalid commit" as "file absent at BASE", the exact false clean the validation was added for.
  3. (should-fix) **`UNTRACKED` must not short-circuit.** Trackedness is decided early and reported
     late, so `registered=N` and the other counts are real on that verdict too (AC-3.4 wants the
     count on *every* verdict). Short-circuiting would emit `UNTRACKED registered=0` for a populated
     registry, which is false.
  4. (should-fix) **Path forms were assumed to match.** `git diff` emits repo-relative paths; an
     impl-plan's `Production file` is hand-written and may be a basename or absolute. Both sides are
     now normalised with a suffix-match fallback, and an unresolvable claim is named — a legitimate
     claim read as `unattributed` is noise in precisely the mechanism that must not be noisy.
- v1.6: Design audit cycle 6 — 5 must-fix. Three were FR-5 mechanics, two were Axis-C drift where
  the design had outgrown the spec; the latter were resolved by amending the **spec** (v1.3),
  because in both cases the design's version is what the mechanism requires.
  1. **AST targets had no path to a boundary.** The AST yields Python namespaces; boundaries are
     file globs, and nothing bridged them. Now an explicit module-name → repo-path index built by
     walking `*.py`; **unresolvable targets are skipped, never guessed** (a name resolving to no
     file here cannot cross a boundary here), and same-stem ambiguity is reported rather than
     resolved to the first match, which would fabricate a crossing. This heuristic is the second
     stated reason FR-5 ships warning-only.
  2. **Deleted files would have crashed the verifier.** `git diff --name-only` includes files
     deleted in HEAD, and parsing a deleted file's HEAD version raises `FileNotFoundError` — a
     crash at 5f instead of a verdict. Fixed with `--diff-filter=AM`, probed on a real deletion
     commit: 62 paths plain, 61 filtered, 1 deletion.
  3. **The repo-relative path assumption had no evidence.** Probed: `git diff --name-only` emits
     repo-relative paths from the repo root *and* from a subdirectory (identical output), so the
     normalisation has a fixed reference on that side.
  4. **Axis C, AC-2.1** — the design added `unverified_renames` to a token grammar the spec fixed.
     Spec amended: a count that drives a FAIL must be in the grammar.
  5. **Axis C, AC-4.2** — the design required `removed_by_feature` on all tombstones where the spec
     required a superseding feature only for `superseded`. Spec amended: *who removed it* and *what
     replaced it* are different questions, and without the former a `pinned-a-defect` or `renamed`
     tombstone is an anonymous edit.
- v1.7: Design audit cycle 7 — 1 must-fix. The schema table carried `removed_by_feature` and
  `successor_pin` but **no field for the superseding feature**, which AC-4.2 requires — so a
  `superseded` tombstone was attributable yet gave the operator no way to find what took over.
  Added `superseding_feature` (required when `removal_provenance == "superseded"`). The three
  tombstone fields answer three different questions and none substitutes for another: who removed
  it, what feature replaced it, which test now carries the guarantee.
- v1.9: **Back-propagated from impl-plan audit cycles 1–7.** Phase 5b surfaced defects in this
  design, not merely in the plan derived from it; the impl-plan audit's cross-doc consistency check
  (cycle 7) refused to let them be deferred to 6a-prime, which was correct — a stale design would
  have made the 6a-prime architectural review flag correct Phase-5 code as drift. Changes:
  - **`--diff-filter=AM` → `--name-status --diff-filter=d`.** `AM` is an allowlist and silently
    drops renames; probed on a tree carrying `A`/`M`/`D`/`R` at once, a file renamed *and* extended
    with a new function was absent from the changed set entirely, so every cross-boundary call a
    rename introduces was invisible. The v1.x probe had exercised only a deletion. `d` is
    exclusion-based and preserves the `FileNotFoundError` constraint (verified: every path it
    returns exists at HEAD). Separately, `--name-only` yields only a rename's new path, making
    `git_show(base, new_path, repo)` return `None` so the file reads as brand-new and its
    *pre-existing* calls all fire — hence `--name-status` and the `(base_path, head_path)` pair.
  - **Three named halts → five.** AC-4.1 (undeclared removal) and AC-4.3 (unverifiable rename) were
    already `FAIL` conditions with no `[H-MAD]` marker. Since a verdict exits 0, such a run halts
    anonymously — marker discipline violated by omission.
  - **`undeclared_removals=U` added to the `WIREREG:` grammar**, per this design's own v1.6
    amendment that a count driving a `FAIL` must be in the grammar; `compare()`'s result had none.
  - **`WIRECHALLENGE:` gains `dangling=D`, `ambiguous=A`, and a `NOT_COMPARED` token** so a run that
    could not compare is distinguishable from one that compared and found nothing.
  - **`--feature` flag specified** as the source of `owning_feature`, explicitly not the plan's
    filename, with the requirement that `SKILL.md`'s 5b invocation carries it.
