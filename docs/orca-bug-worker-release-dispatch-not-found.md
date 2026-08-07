# Bug: `worker-abandon` / `worker-stop` report `dispatch_not_found` for a dispatch `dispatch-show` returns as active

**Component:** Orca runtime — `orca orchestration worker-abandon`, `orca orchestration worker-stop`
**Type:** Bug (correctness — a documented recovery path is unreachable; misleading error)
**Environment:** macOS 26.5.2 · orchestration experimental feature enabled
**Re-verified 2026-08-07 on Orca 1.4.175** — eleven builds after the original observation on
1.4.164 (runtime `871c7cbb-…`, vs `5bf0c6d1-…` originally). Same result, verbatim, with a fresh
terminal, task and dispatch id (`ctx_e1041e747d52`). The positive control below is new and was run
on 1.4.175. Note `appVersion` is no longer exposed in the CLI's `_meta` envelope on this build —
the version above is from the app bundle's `CFBundleShortVersionString`.

## Summary

A dispatch created with `orca orchestration dispatch` cannot be released. Three commands
disagree about whether the same dispatch id exists, in the same runtime, seconds apart:

| Command | Answer about `ctx_b4a0b03319b2` |
|---|---|
| `orchestration dispatch-show --task <t>` | exists, `"status": "dispatched"` |
| `orchestration dispatch --to <same terminal>` | exists — refuses with *"already has an active dispatch (ctx_b4a0b03319b2 …)"* |
| `orchestration worker-abandon --dispatch ctx_b4a0b03319b2` | **`dispatch_not_found`** |
| `orchestration worker-stop --dispatch ctx_b4a0b03319b2` | **`dispatch_not_found`** |

The net effect is a **permanently wedged terminal**: it holds an active dispatch that blocks any
further dispatch to that pane, and both documented release verbs deny the dispatch exists.

This matters because the orchestration guide prescribes exactly these two verbs as the escape
hatch for an unresolved worker:

> It remains `outcome_unknown`: either `worker-stop --dispatch <id>` and inspect again, or
> explicitly `worker-abandon --dispatch <id>` while accepting that resources may still be live.

Both halves of that instruction fail with `dispatch_not_found`.

## Repro

```console
$ orca orchestration task-create --spec "probe" --task-title "probe" --run run_1632386a175a --json
    → result.task.id = task_c8861cf7754d

$ orca orchestration dispatch --task task_c8861cf7754d --to term_eccee0b2-… --run run_1632386a175a --json
{"ok":true,"result":{"dispatch":{"id":"ctx_b4a0b03319b2","status":"dispatched",
  "assignee_handle":"term_eccee0b2-…","launch_token_hash":null,
  "capability_hash":null,"process_incarnation":null,"contract_version":1}, "injected":false}}

$ orca orchestration dispatch-show --task task_c8861cf7754d --json
{"ok":true,"result":{"dispatch":{"id":"ctx_b4a0b03319b2","status":"dispatched", …}}}   # ← exists

$ orca orchestration worker-abandon --dispatch ctx_b4a0b03319b2 --json
{"ok":false,"error":{"code":"dispatch_not_found",
  "message":"Dispatch ctx_b4a0b03319b2 was not found."}}                                # ← does not exist

$ orca orchestration worker-stop --dispatch ctx_b4a0b03319b2 --json
{"ok":false,"error":{"code":"dispatch_not_found",
  "message":"Dispatch ctx_b4a0b03319b2 was not found."}}                                # ← same

# And the terminal is now unusable for any other task:
$ orca orchestration dispatch --task task_330bb7ca8fab --to term_eccee0b2-… --json
{"ok":false,"error":{"code":"runtime_error",
  "message":"Terminal term_eccee0b2-… already has an active dispatch (ctx_b4a0b03319b2 for task task_c8861cf7754d)"}}
```

Reproduced twice, on two different freshly-created terminals, with two different dispatch ids
(`ctx_b4a0b03319b2`, `ctx_fce6b7f8a0a4`). Nothing intervened between `dispatch` and
`worker-abandon` in the second run — the failure is immediate and does not require any
intermediate state change.

## Cause — measured, via the positive control

Both failing dispatches were created by the low-level `orchestration dispatch` path, so they carry
`launch_token_hash: null`, `capability_hash: null`, `process_incarnation: null`.

**The positive control has now been run, and it confirms the scoping.** The same verb against a
`worker-start`-created dispatch, on the same runtime minutes later:

```console
$ orca orchestration worker-start --task <task> --agent codex --worktree current --json   # ok:true
$ orca orchestration dispatch-show --task <task> --json
    → {"id":"ctx_0f6f82769296","status":"dispatched",
       "capability_hash":"030330260603acb0…",           # ← populated
       "process_incarnation":"47c13b8f-…",              # ← populated
       "assignee_pane_key":"5d4ca30d…:eb4923a5…"}       # ← populated

$ orca orchestration worker-abandon --dispatch ctx_0f6f82769296 --json
{"ok":true,"result":{"dispatchId":"ctx_0f6f82769296","state":"abandoned",
  "alreadySettled":false,"stale":false,"processAction":"none", …}}          # ← works
```

Afterwards the dispatch reads `status: "failed"` with `capability_revoked_at` stamped — the
correct provenance, and exactly what the low-level path cannot obtain.

So the two classes behave differently by design:

| dispatch created by | `capability_hash` / `process_incarnation` | `worker-abandon` |
|---|---|---|
| `worker-start` (supervised) | populated | `ok:true`, `state: "abandoned"`, capability revoked |
| `dispatch` (low-level) | `null` | **`dispatch_not_found`** |

This makes the report narrower and, we think, more actionable. The defect is **not** that
`worker-abandon` is broken. It is that:

1. **`dispatch_not_found` is the wrong error for a dispatch that demonstrably exists** — the caller
   read the id back from `dispatch-show` seconds earlier, and `dispatch` itself names the same id
   when refusing a second dispatch to the pane. "Was not found" sends you looking for a lifecycle
   or id bug that is not there.
2. **The low-level `dispatch` path has no release verb at all.** `worker-start` dispatches can be
   abandoned; `dispatch` dispatches can only be falsified as `completed`.
3. **Nothing in the `dispatch-show` payload marks which class a dispatch is in**, so a caller
   cannot tell in advance which release path applies. The distinguishing fields
   (`capability_hash`, `process_incarnation`, `assignee_pane_key`) are present but undocumented
   as lifecycle-relevant.

## Workaround (and why it is not a fix)

`orca orchestration task-update --id <task> --status completed` settles the dispatch
(`status: "completed"`, `completed_at` stamped) and frees the terminal for re-dispatch. Verified:

```console
$ orca orchestration task-update --id task_c8861cf7754d --status completed --json    # ok:true
$ orca orchestration dispatch-show --task task_c8861cf7754d --json
    → {"id":"ctx_b4a0b03319b2","status":"completed","completed_at":"2026-08-03 10:05:21"}
$ orca orchestration dispatch --task task_8f32adfea05d --to term_eccee0b2-… --json   # ok:true, new ctx_40cf8a13e968
```

This is unsatisfactory on two counts. It records the work as **completed** when it was abandoned,
which is precisely the provenance lie the `worker-abandon` verb exists to avoid; and the guide
itself says to reserve manual `task-update` for "explicit recovery or overrides", not for routine
worker release. Note also that `--status ready` does **not** release the binding (correctly — it is
not a terminal state), so `completed` is the only value that works.

## What I expected

`worker-abandon --dispatch <id>` (and `worker-stop --dispatch <id>`) to accept any dispatch id
that `dispatch-show` returns, fence it, and free the assignee terminal — recording the outcome as
abandoned/stopped rather than completed.

## Proposed fix

The scoping is now confirmed deliberate, so **(2) is the ask**; (1) is offered only if widening is
cheaper than documenting.

1. **Widen the release verbs to the dispatch table**, so any live dispatch is fenceable regardless
   of how it was minted.
2. **Make the constraint visible, and stop calling it "not found".** Concretely:
   - replace `dispatch_not_found` with an error naming the real constraint — e.g.
     `dispatch_not_supervised` — and pointing at the supported release path for that class;
   - add a field to the `dispatch-show` payload marking which lifecycle verbs apply, so a caller
     can branch *before* it needs to release. The information already exists implicitly in
     `capability_hash` / `process_incarnation` / `assignee_pane_key`; it is just not documented as
     lifecycle-relevant, and inferring policy from three incidentally-null fields is not something
     a caller should have to reverse-engineer.

   Even the error-message change alone would have saved this investigation: a generic "was not
   found" for an id the caller read back from the API two commands earlier is what makes this
   expensive to diagnose.

Either way, the low-level path still needs *some* way to record an abandoned worker as abandoned
rather than completed — see below.

## Why it matters

Any orchestrator that dispatches to a pre-existing agent pane — the low-level `dispatch --inject`
topology the guide explicitly sanctions when "the composed start does not express the needed
topology" — has no way to release that pane when a worker stalls or is cancelled. The pane stays
wedged for the life of the runtime unless the coordinator falsifies the task as completed.

---

*Filed from the H-MAD dispatch layer (`BrightGold70/skills`, `h-mad/scripts/hmad-dispatch.sh`).
Related: `docs/orca-feature-request-terminal-identity.md`.*
