## Summary
The design implements the safety and data-integrity fixes described in the spec, correctly placing guards in `worktree-rm` while maintaining byte-for-byte output compatibility on the happy path. The design cleanly handles `--force` short-circuiting. However, it explicitly restricts `worktree-create`'s task registration to only trigger when `--prompt-file` is passed, which narrows AC-5.1. Axis C reconciliation requires this narrowing to be raised as a `Must-fix` so it is consciously evaluated.

## Must-fix
- Spec reconciliation: AC-5.1 is `restated` — The spec states "`worktree-create` emits both the worktree selector and a task-id, each separately parseable by a caller." The design narrows this behavior: "When `--prompt-file` is supplied ... register a task after the worktree is created". The spec's requirement is unconditional, while the design makes it conditional on the `--prompt-file` flag.

## Should-fix
None

## Nit
- `orca worktree ps --json` matching ambiguity — If a selector matches multiple entries (e.g. via `branch`), the design states to "Take the matching `.path`" but doesn't specify if it should take the first match or fail on ambiguity.
- Case-insensitivity for `concern_stated` — The negation set (`none`, `n/a`, `na`, `no concerns`, `nothing`, `-`) should explicitly specify that it is evaluated case-insensitively.
