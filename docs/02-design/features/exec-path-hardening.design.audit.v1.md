AUDIT-exec-path-hardening-design-v1-BEGIN
## Summary
The design provides a robust implementation strategy that fully satisfies the spec requirements, notably introducing a smart segment-replacement composition to avoid clobbering existing comments. However, it contains a critical flaw where reusing the agent's watchdog for the stamp calls would inadvertently steal the agent's stdin, alongside an internal contradiction regarding the number of `codex` call sites remaining after unification. All Spec ACs are addressed as written.

| Spec AC | Classification |
|---|---|
| AC-1.1 to AC-1.5 | implemented-as-written |
| AC-2.1 to AC-2.5 | implemented-as-written |
| AC-3.1 to AC-3.3 | implemented-as-written |
| AC-4.1 to AC-4.4 | implemented-as-written |
| AC-5.1 to AC-5.4 | implemented-as-written |
| AC-6.1 to AC-6.3 | implemented-as-written |

## Must-fix
- Contradiction on codex call sites — The Executive Summary and Architecture Overview state the two execution shapes "collapse into one background-and-poll path" (`_exec_run`). However, the "codex `--log` append" section states that `> "$log"` becomes `>> "$log"` at "both codex call sites (timeout and no-timeout)." This is a direct internal contradiction; if the paths are unified into `_exec_run`, there is only one codex call site to modify.
- Stdin stealing / Watchdog reuse defect — The Overview states that every stamp is "wrapped in the same watchdog the agent is" (which is `_exec_run`). But `_exec_run` explicitly preserves `<&0` (stdin handoff) for the agent. If `_exec_stamp` uses `_exec_run` to bound its `orca` calls, the backgrounded `orca` call will steal stdin intended for the agent (e.g., during the `start` stamp). The bounding mechanism for stamps cannot safely reuse the agent's specialized watchdog if it retains these behaviors.
- Path prefix matching data-loss hazard — `_exec_wt_target` matches the longest `.path` that is a "prefix" of `cd_dir`. A naive string prefix match would incorrectly match `/path/repo` as a prefix of `/path/repo-other`. This causes the stamp to target the wrong worktree and clobber its comments; the prefix match must ensure directory boundaries (exact match or followed by `/`).

## Should-fix
- Inconsistent stamp text assembly — `_exec_comment_compose` expects the stamp to fit the format `h-mad: <agent> <feature-or-cd-basename> · <state> · <detail>⟦/h-mad⟧`. However, `_exec_stamp` specifies building `start` as `running · 0m` and `exit` as `<agent> · rc=<rc> · <verdict|no-verdict>`. It is unclear which helper is responsible for inserting the `<agent>` and `<feature-or-cd-basename>` fields, and the specified `kind` strings are missing them, leading to malformed or inconsistent stamps.
- Newline handling in comment read — The `_exec_wt_target` helper emits `<selector>\t<current comment>`. Since worktree comments can contain newlines (and `jq` will emit them literally), the bash caller must be careful not to consume only the first line if using `read -r`. The design should note that the string passing must tolerate multiline comments.

## Nit
None
AUDIT-exec-path-hardening-design-v1-END
