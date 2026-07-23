# Design: fanout-integrity-and-defects

## Executive Summary

Four independent changes: a resolve-then-inspect guard on `_cmd_worktree_rm` that refuses to destroy
a worktree holding work, an opt-in task registration in `_cmd_worktree_create` reported as an
`[H-MAD]` stderr marker so stdout stays byte-identical, a one-expression `now(UTC)` default in
`h_mad_state_write.py`, and a post-extraction concern check in `h_mad_extract_verdict.py`'s CLI that
leaves the pure function untouched.

## Overview

The design intent is that each fix sits where its failure becomes irreversible or unactionable, and
that none of them changes an existing observable contract. Three constraints drive every decision
below, and all three come from assertions already in the suite rather than from preference:
`worktree-rm --force` must produce exactly one Orca call, `worktree-create` (bare) must print exactly
the selector, and a bare-name selector that resolves to nothing must still be removable. The last one
also settles the brainstorm's open question about fail direction: **only positive evidence refuses.**

## Architecture Overview

```
hmad-dispatch worktree-rm <sel> [--force] [--base <ref>]
  │
  ├─ --force? ──yes──► [H-MAD] marker on stderr ──► orca worktree rm --force   (ONE call, no lookup)
  │      │no
  ├─ _worktree_path <sel>  ──► "" (unresolvable) ──────────────────┐
  │      │ <path>                                                   │
  ├─ _worktree_holds_work <path> [<base>]                           │
  │      ├─ dirty tree      → refuse  worktree_has_uncommitted_work │
  │      ├─ unmerged commits→ refuse  worktree_has_unmerged_commits │
  │      └─ clean           ─────────────────────────────────┐      │
  │                                                          ▼      ▼
  └────────────────────────────────────────────────► orca worktree rm

hmad-dispatch worktree-create <name> … [--prompt-file <p>]
  ├─ orca worktree create …            → stdout: <selector>      (UNCHANGED)
  └─ --prompt-file given? → task-create → stderr: [H-MAD] worktree_task task=<id> selector=<sel>
```

`_worktree_path` returning empty is *not* evidence the worktree is safe — it is absence of evidence,
and the guard treats it the same way `_orca_handle_live` treats an unreadable listing.

## Detailed Design

### Selector → path — `_worktree_path()`

Two-step, cheapest first:

1. If the selector contains `::`, the suffix after the **first** `::` is the path (this is Orca's
   `worktreeId` shape, `<repoId>::<path>`, confirmed against `worktree-ps`). Accept it only if that
   directory exists.
2. Otherwise, query `orca worktree ps --json` and match the selector against each entry's
   `worktreeId`, `path`, `displayName`, or `branch` (with and without the `refs/heads/` prefix, since
   Orca reports the full ref while every human-facing form is short).

   **Ambiguity is treated as unresolved, not as a first-match win.** If more than one entry matches
   — which `branch` and `displayName` make possible, since neither is unique across repos — the
   resolver returns empty rather than guessing. Picking the first match would mean inspecting one
   worktree and then removing a different one, which is a worse failure than not checking at all:
   it would report a confident clean verdict about the wrong directory. Returning empty degrades to
   the documented unresolvable path (remove as today), which is the behaviour that already exists.

Print nothing and return non-zero when neither step yields exactly one existing directory. Callers
treat that as "cannot check", never as "safe".

The `::`-split is first because it needs no Orca round trip and covers the shape the fanout actually
produces; the `worktree-ps` lookup is the correctness net for names, ids and `active`.

### Work detection — `_worktree_holds_work()`

Given a path and an optional base ref, returns a reason token on stdout and non-zero when the
worktree holds work:

- **Uncommitted** — `git -C <path> status --porcelain` is non-empty → `worktree_has_uncommitted_work`.
  `--porcelain` reports staged, unstaged **and** untracked-non-ignored entries while honouring
  `.gitignore`, which is exactly the FR-1 boundary: AC-1.3 (untracked alone must refuse) and AC-1.4
  (an ignored file alone must not) are both satisfied by one command, with no hand-rolled filtering
  to get wrong. This matters because the Wave-3 loss was untracked-and-modified, not staged — a
  guard checking only `git diff --cached` would have passed while the data was destroyed.
- **Unmerged** — `git -C <path> log --oneline <base>..HEAD` is non-empty →
  `worktree_has_unmerged_commits`.

Order is uncommitted-first: it is local, cannot fail for lack of a ref, and is the commoner case.

### The comparison ref

`--base <ref>` is honoured when given. Otherwise the default is resolved in order:
`origin/HEAD` → `main` → `master`, taking the first that `git -C <path> rev-parse --verify` accepts.
If none resolves, the unmerged check is **skipped entirely** — not failed — per AC-2.4. h-mad does
not record a base ref on the worktrees it creates, so an undeterminable ref is an ordinary state,
not an anomaly, and refusing on it would break teardown for any repo without those branch names.

This is the one guard that can silently under-protect. It is stated here rather than hidden: a
worktree on a repo with no `origin/HEAD`, `main` or `master` gets the uncommitted check only.

### `--force`

Handled by flag-scan **before** any resolution, so the forced path performs exactly the one
`orca worktree rm … --force --json` call the existing test pins byte-for-byte. It emits
`[H-MAD] worktree-rm forced selector=<sel> — guards skipped` on stderr (AC-3.3) so a bypass is
visible in a run log. The flag keeps its single meaning: "remove it anyway", covering both h-mad's
guards and Orca's own force semantics — splitting it would add a second flag for a case no caller
has.

### `worktree-create` task registration

When `--prompt-file` is supplied — the fanout path, and the only path where `await`/`gate-create`
are needed — register a task after the worktree is created and emit:

```
[H-MAD] worktree_task task=<task-id> selector=<selector>     (stderr)
```

**stdout is unchanged in every case**: exactly the selector, exactly as today. This is what preserves
`test_worktree_create_parses_selector_and_empty_match`'s `stdout == "wt-7\n"` and every existing
caller that reads the selector from stdout — including the Wave-3 fanout, which captured it directly.
An `[H-MAD]` stderr marker is the established convention for this kind of out-of-band fact
(`_cmd_pin` writes `[H-MAD] pinned <agent> -> <handle>` the same way), so this satisfies the
marker-discipline invariant rather than inventing a channel.

Registration reuses the existing `_cmd_task_create` path, so the coordinator handle and spec
envelope are constructed exactly once in the codebase. Failure to register is **non-fatal**
(AC-5.4): it emits `[H-MAD] worktree_task_skipped selector=<sel>` and returns success, because a
worktree that exists with no task-id is recoverable while a failed creation is not.

Gating on `--prompt-file` rather than a new flag means the bare `worktree-create` argv is untouched,
which is what keeps `test_worktree_create_argv_orca`'s exact-capture assertion passing.

### `started_ts` default

`h_mad_state_write.py:138` becomes `started_ts or datetime.now(timezone.utc)` rendered in the same
`...Z` form the rest of the store uses. Nothing else changes; existing records are never rewritten
(AC-6.4), and an explicit `--started-ts` still wins (AC-6.2).

### Contentless `DONE_WITH_CONCERNS`

`extract_verdict()` is **not** changed. It answers "what is the last value of this key", and widening
it to inspect surrounding prose would make its name a lie and put the new rule on the `VERDICT:` and
`ASSESSMENT:` paths by accident.

Instead a new `concern_stated(scrape) -> bool` is applied in `main()`, only when
`args.key == "STATUS"` and the extracted value is `DONE_WITH_CONCERNS`. On false it returns 2 with a
message distinct from the missing-verdict one (AC-7.5), so an operator can tell a mis-formatted
report from a silent agent.

`concern_stated` looks for a concerns heading (`Concerns`, `Concerns / blockers`, `Blockers`, in a
markdown heading, a bold run, or a bare `key:` line) and asks whether anything follows it beyond a
negation. The negation set is explicit and small — `none`, `n/a`, `na`, `no concerns`, `nothing`,
`-` — because the enumerable half is the negatives; judging whether a stated concern is a *good*
concern is out of scope by spec. Absent heading → false, which is the fail-closed direction the spec
requires.

**Both the heading match and the negation match are case-insensitive, and surrounding punctuation
and whitespace are stripped before comparison.** Agents write `None`, `NONE`, `none.`, `N/A` and
`- none` interchangeably; a case-sensitive set would accept `None` as a stated concern and pass
exactly the report J10 was filed against. The comparison is on the normalised token, not a substring
search, so a real concern containing the word "none" in prose is unaffected.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_worktree_path` | `h-mad/scripts/hmad-dispatch.sh` | new | Selector → path, empty when unresolvable — FR-1, FR-2, FR-4 |
| `_worktree_holds_work` | `h-mad/scripts/hmad-dispatch.sh` | new | Dirty-tree + unmerged-commit detection, reason token — FR-1, FR-2 |
| `_worktree_default_base` | `h-mad/scripts/hmad-dispatch.sh` | new | `origin/HEAD`→`main`→`master`, empty if none — FR-2 |
| `_cmd_worktree_rm` | `h-mad/scripts/hmad-dispatch.sh` | modify | `--force` short-circuit, guard, refusal messages — FR-1–FR-4 |
| `_cmd_worktree_create` | `h-mad/scripts/hmad-dispatch.sh` | modify | Task registration + stderr marker — FR-5 |
| `_new_record` default | `h-mad/scripts/h_mad_state_write.py` | modify | `now(UTC)` instead of the epoch — FR-6 |
| `concern_stated` | `h-mad/scripts/h_mad_extract_verdict.py` | new | Detect a stated concern — FR-7 |
| `main()` | `h-mad/scripts/h_mad_extract_verdict.py` | modify | Apply the check for one key/value pair — FR-7 |
| Guard + create tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-1–FR-5 |
| `started_ts` tests | `h-mad/tests/test_h_mad_state_write.py` (or existing home) | modify | FR-6 |
| Concern tests | `h-mad/tests/test_h_mad_extract_verdict.py` (or existing home) | modify | FR-7 |
| Concern obligation | `h-mad/references/codex-implementer-prompt.md` | modify | FR-8 |
| Guard + task-id docs | `h-mad/SKILL.md`, `h-mad/references/orchestration-mode.md` | modify | FR-9 |

## Implementation Order

- **Task 1 — worktree-rm guard** (`_worktree_path`, `_worktree_holds_work`, `_worktree_default_base`,
  `_cmd_worktree_rm`). FR-1, FR-2, FR-3, FR-4. *Dependencies: None.*
- **Task 2 — worktree-create task-id** (`_cmd_worktree_create`). FR-5. *Dependencies: None.*
- **Task 3 — started_ts default** (`h_mad_state_write.py`). FR-6. *Dependencies: None.*
- **Task 4 — contentless concern** (`h_mad_extract_verdict.py`). FR-7. *Dependencies: None.*
- **Task 5 — docs** (`SKILL.md`, `orchestration-mode.md`, `codex-implementer-prompt.md`). FR-8, FR-9.
  *Dependencies: Tasks 1–4, since the prose must name the shipped tokens.*

All four code tasks are mutually independent and touch disjoint regions or different files. **They
are nevertheless dispatched serially**: the fanout is the machinery under repair here, and using it
to repair itself is the category error this feature exists to prevent. This is a deliberate
departure from the "≥2 independent tasks → engage fanout" rule, recorded so it is not read as an
oversight.

## Data Model / Schema Changes

None. No store, schema or on-disk artifact is added or altered. `orchestrator_state` records gain a
different *value* for `started_ts` on creation, but the field, its type and its format are unchanged.

## API / Interface Changes

| Name | Type | Default | Purpose |
|---|---|---|---|
| `worktree-rm --base <ref>` | new optional arg | `origin/HEAD`→`main`→`master`, else skip | Comparison ref for the unmerged check — FR-2 |
| `worktree-rm --force` | existing flag | off | Now also skips the new guards, and says so — FR-3 |
| `[H-MAD] worktree_task task=<id> selector=<sel>` | stderr marker | emitted with `--prompt-file` | Task-id surfacing — FR-5 |
| `[H-MAD] worktree_task_skipped selector=<sel>` | stderr marker | on registration failure | Non-fatal signal — FR-5 |
| `[H-MAD] worktree-rm forced selector=<sel>` | stderr marker | with `--force` | Bypass visibility — FR-3 |

Refusal contract for `worktree-rm`:

| Condition | Return | Channel |
|---|---|---|
| Non-orca substrate (existing) | 2 | stderr, "requires orchestration mode" |
| Missing selector (existing) | 2 | stderr |
| Uncommitted work (new) | 1 | stderr, `worktree_has_uncommitted_work` |
| Unmerged commits (new) | 1 | stderr, `worktree_has_unmerged_commits` |
| `orca worktree rm` failed (existing) | its rc | stderr, existing `[H-MAD] worktree-rm failed` marker |
| Removed | 0 | — |

`worktree-create` stdout is unchanged in every case. No verb is added or removed.

## Error Handling Strategy

Refusals are non-zero returns with stderr diagnostics, matching `terminal_handle_stale` and the
`send` refusals shipped in Wave 3. `worktree-rm` is an operation, not a verdict-emitting gate, so the
audit-gate signal-discipline invariant — which governs gates whose verdict the orchestrator
consumes — does not apply and a stdout token would be the inconsistency. Each refusal names the
condition and the recovery (commit or `--force`).

Nothing is removed on any refusal path: the guard precedes the single `orca worktree rm` call, so
this is structural rather than a property each branch must remember. `_worktree_holds_work` prints
its reason to stdout for its caller inside the wrapper to compose; the token never reaches the user's
stdout.

`_worktree_path` failing is not an error — it is a normal outcome for a bare-name selector, and the
caller proceeds.

## Test Strategy

Subprocess-level against the real wrapper via the existing `run(args, *, substrate, env, capture,
cwd)` helper in `h-mad/tests/test_hmad_dispatch.py:94`, with stub `orca` from `STUBS` on an isolated
PATH. Module constants are `SKILL`, `WRAPPER`, `STUBS` — verified against the file, not assumed.

The guard tests need something the existing suite has never needed: **a real git repository**. A stub
cannot exercise `git status --porcelain` or `git log <base>..HEAD`. Each guard test therefore builds
a throwaway repo under `tmp_path` (`git init`, a commit, then dirty it or branch it as the case
requires) and passes a `<repoId>::<that path>` selector, so `_worktree_path`'s step 1 resolves
without any Orca round trip. This keeps the tests hermetic and fast while exercising the real git
commands rather than a mock of them.

`HMAD_STUB_CAPTURE` (via `capture=`) is how "nothing was removed" is asserted — against the absence
of the `orca worktree rm` call, not merely an exit code.

**Guards must discriminate.** Every refusal test is paired with a negative case proving the guard
does not fire when it should not: AC-1.4 (ignored file), AC-2.3 (merged commits), AC-4.1
(unresolvable selector), AC-7.4 (other keys and values). A refusal test that only ever observes
refusals passes forever against a guard that refuses unconditionally — and each guard will be
verified by mutation before it is accepted, not merely by a green run.

For FR-6, any existing test asserting the epoch sentinel encodes the defect and must be updated;
the design expects at least one and treats its failure as confirmation, not regression.

## Test Plan

Verification command: `/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q` (baseline **550**).

| Scenario | Asserts |
|---|---|
| Real repo, modified tracked file, `::`-selector → refused, no rm call | AC-1.1, AC-1.2 |
| Real repo, untracked non-ignored file only → refused | AC-1.3 |
| Real repo, only a `.gitignore`d file → removed | AC-1.4 |
| Clean repo, commit not in base → refused, distinct token, no rm call | AC-2.1, AC-2.2 |
| Clean repo, commits all in base → removed | AC-2.3 |
| Clean repo, no resolvable base ref → not refused for FR-2 | AC-2.4 |
| `--force` with a dirty worktree → removed | AC-3.1 |
| `--force` capture is exactly the one existing rm call | AC-3.2 |
| `--force` emits the bypass marker | AC-3.3 |
| Bare-name `wt-7` (unresolvable) → removed, existing test unchanged | AC-4.1 |
| Failing `orca worktree rm` → rc + existing marker unchanged | AC-4.2 |
| cmux → rc 2, "requires orchestration mode", no call | AC-4.3 |
| Already-gone selector → logs and no-ops | AC-4.4 |
| `--prompt-file` → selector on stdout, task marker on stderr | AC-5.1 |
| Emitted task-id accepted by `gate-create --task` | AC-5.2 |
| Bare `worktree-create` stdout byte-identical to today | AC-5.3 |
| Task registration failure → worktree still created, selector still printed | AC-5.4 |
| Create without `--started-ts` → timestamp within seconds of now | AC-6.1 |
| Explicit `--started-ts` honoured verbatim | AC-6.2 |
| Telemetry row from such a record → plausible `elapsed_min` | AC-6.3 |
| Pre-existing epoch record untouched by an unrelated write | AC-6.4 |
| `DONE_WITH_CONCERNS` + substantive concerns → verdict returned | AC-7.1 |
| Same, no concerns section → exit 2, no verdict printed | AC-7.2 |
| Same, concerns section says `none`/`n/a` → exit 2 | AC-7.3 |
| `DONE`/`BLOCKED`/`NEEDS_CONTEXT` and `VERDICT:`/`ASSESSMENT:` unaffected | AC-7.4 |
| Error message distinguishes no-concern from no-verdict | AC-7.5 |
| Codex template states the obligation and the consequence | AC-8.1, AC-8.2 |
| Docs state guards, tokens, and the unified task-id path | AC-9.1–AC-9.3 |
| `SKILL.md` frontmatter still valid | AC-9.4 |

Beyond the suite, the plan's success criteria require the guard demonstrated against a **real Orca
worktree**, not only a stub — a green suite has certified a dead tool in this repo before.

## Invariant Compliance

**Base — Audit-gate signal discipline.** Complies. No gate changes. `worktree-rm` is an operation
that declines to act, so its non-zero refusal is outside the rule's scope and matches the existing
`terminal_handle_stale` precedent. `h_mad_extract_verdict.py` already exits 2 on an unusable verdict;
FR-7 adds one more case to that same channel rather than inventing a signal.

**Base — Single-source contract.** Complies. `_worktree_path` is the only selector resolver,
`_worktree_holds_work` the only work detector, and task registration reuses `_cmd_task_create` rather
than rebuilding the spec envelope. `extract_verdict` remains the single verdict reader.

**Base — No-plugin-dependency.** Complies. `git`, `jq` and `orca` are already required by the
wrapper; no new external command.

**Base — Backward-compatibility.** Complies, and this drove the design rather than being checked
after it. `worktree-create` stdout is byte-identical in every case; the bare argv is unchanged; every
existing `worktree-rm` assertion holds, including the exact `--force` capture and the bare-name
removal. The only intentional break is an existing test asserting the epoch `started_ts`, which
encodes the defect being fixed and is called out in Test Strategy.

**Base — Operator-override preservation.** Complies. `--force` retains its meaning and gains no
peer; `--base` is additive; no override's precedence changes.

**Base — Marker discipline.** Complies. All three new stderr lines use the `[H-MAD]` prefix, matching
`_cmd_pin` and the existing `[H-MAD] worktree-rm failed` marker.

**Base — Doc-template superset compliance.** Complies. Every Phase-4 template heading is present.

**Project — Skill self-containment.** Complies. All changes are inside `h-mad/`; no cross-skill
import and no hardcoded path outside the skill directory. Test repos are created under `tmp_path`.

**Project — Skill manifest integrity.** Complies. `SKILL.md` frontmatter is unchanged and the prose
is updated in the same change that alters the verbs, so contract and documentation ship together
(AC-9.1–AC-9.4).

### Cross-cutting decision: serial Phase 5 despite four independent tasks

The fanout rule says engage when there are ≥2 independent tasks under orca with orchestration on. All
three conditions hold and the design deliberately declines, because the fanout's teardown step is the
defect under repair: a worker that left work uncommitted would be destroyed by the very
`worktree-rm` this feature is fixing. Recorded here so the audit reads it as a decision with a
reason, not a missed opportunity.

## Version History
- v1.0: Initial design draft.
- v1.1: Cycle-1 audit response. **Must-fix (AC-5.1 Axis C narrowing):** resolved by amending the
  spec to v1.1 rather than by widening the design — unconditional task registration breaks the
  pinned exact-capture assertion on the bare `worktree-create` argv and would orphan a task per
  non-fanout worktree, and backward compatibility is a base invariant. The design is unchanged on
  this point; the reconciliation is recorded in the spec's AC-5.1 and Version History.
  **Nits:** selector-resolution ambiguity now returns empty (degrading to the unresolvable path)
  instead of taking a first match, because inspecting one worktree and removing another is worse
  than not checking; and `concern_stated`'s heading and negation matching is specified
  case-insensitive with punctuation stripped, since `None` vs `none` would otherwise readmit the
  exact report J10 was filed against.
