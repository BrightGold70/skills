# Bug: `worker-abandon` / `worker-stop` report `dispatch_not_found` for a dispatch `dispatch-show` returns as active

**Component:** Orca runtime — `orca orchestration worker-abandon`, `orca orchestration worker-stop`
**Type:** Bug (correctness — a documented recovery path is unreachable)
**Environment:** macOS 26.5.2 · Orca `appVersion` 1.4.164 · runtime `5bf0c6d1-…` · orchestration experimental feature enabled

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

## Scope of what was measured

Both failing dispatches were created by the low-level `orchestration dispatch` path, so they
carry `launch_token_hash: null`, `capability_hash: null`, `process_incarnation: null`. A plausible
cause is that `worker-abandon`/`worker-stop` resolve only dispatches minted by `worker-start`,
while `dispatch-show` and the terminal-binding check read the dispatch table directly.

**That cause is a hypothesis, not something this report measured.** The positive control — the
same two verbs against a `worker-start`-created dispatch — was not run, because `worker-start`
requires a live recognized agent in the target terminal (`agent_unconfigured` on a plain shell)
and spawning one was out of scope for the repro. If the hypothesis holds, the surface bug is
still real: `dispatch-show` returns a dispatch that the release verbs treat as nonexistent, with
no field distinguishing the two classes.

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

## Proposed fix (either is sufficient)

1. **Resolve the id from the same source `dispatch-show` reads.** If the release verbs are scoped
   to a `worker-start` registry, widen them to the dispatch table so any live dispatch is
   fenceable.
2. **If the scoping is deliberate, make it visible and say so in the error.** Add a field to the
   `dispatch-show` payload marking which lifecycle verbs apply, and replace `dispatch_not_found`
   with an error that names the actual constraint (e.g. `dispatch_not_supervised`) plus the
   supported release path. A generic "was not found" for an id the caller just read back from the
   API is the part that makes this expensive to diagnose.

## Why it matters

Any orchestrator that dispatches to a pre-existing agent pane — the low-level `dispatch --inject`
topology the guide explicitly sanctions when "the composed start does not express the needed
topology" — has no way to release that pane when a worker stalls or is cancelled. The pane stays
wedged for the life of the runtime unless the coordinator falsifies the task as completed.

---

*Filed from the H-MAD dispatch layer (`BrightGold70/skills`, `h-mad/scripts/hmad-dispatch.sh`).
Related: `docs/orca-feature-request-terminal-identity.md`.*
