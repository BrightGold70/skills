# Bug: `terminal read` cannot distinguish "scrollback lost to a restart" from "pane printed nothing"

**Component:** Orca runtime — `orca terminal read`
**Type:** Bug (silent data loss — success-shaped empty result)
**Environment:** macOS 26.5.2 · Orca `appVersion` 1.4.164 · runtime `5bf0c6d1-…`

> **STATUS 2026-08-07 — NOT FILED. Needs the check in §"Open question" before it is.**
> Re-examined on Orca **1.4.175**. The `terminal read` payload is unchanged — still exactly
> `handle, status, tail, truncated, limited, oldestCursor, nextCursor, latestCursor,
> returnedLineCount`, with no field distinguishing a discarded buffer from a silent one. So the
> proposed fix has not landed.
>
> **But this report's central claim needs narrowing before it is filed.** It says the two states
> are "byte-identical in the response" — true of `terminal read`, and the reason we could not
> branch. It is *not* true of the caller's total information: `terminal list` also exposes
> `orphaned` and `lastOutputAt`, which were never examined when this was written. Measured today
> across 9 live panes, the correlation is clean:
>
> | panes | `orphaned` | `lastOutputAt` | `returnedLineCount` |
> |---|---|---|---|
> | 8 | `false` | populated | 2–65 |
> | 1 | `true` | `null` | **0** |
>
> A maintainer could reasonably answer "`lastOutputAt: null` is your flag" and close it. That
> answer may well be wrong for the case this report is actually about — see below — but the report
> as written does not address it, and filing it in that state spends credibility for nothing.

## Summary

A terminal that survives an Orca app restart loses its scrollback, and `orca terminal read` reports
that loss as an ordinary empty buffer: `{"ok": true}`, `tail: []`, `returnedLineCount: 0`, and every
cursor — `oldestCursor`, `nextCursor`, `latestCursor` — reading `"0"`, with `truncated` and `limited`
both `false`. Nothing in the response says the buffer was discarded rather than never written.

The state is recoverable-forward but not backward: as soon as the pane produces **new** output the
buffer repopulates and reads work normally. So the failure window is precisely a restart-surviving
pane that has been idle since the restart — which is exactly the pane an orchestrator most needs to
identify *before* it sends anything to it.

## Repro

Preconditions: a terminal running an interactive TUI agent, then quit and relaunch the Orca app.
The pane survives; `terminal list` reports `incarnationId: null` and `rendererGraphEpoch: null`.

```console
$ orca terminal list --json | jq '.result.terminals[] | select(.worktreePath|endswith("/skills"))
    | {handle, title, connected, incarnationId, rendererGraphEpoch}'
{"handle":"term_7d59e6d2-…","title":"Claude - skills repo","connected":true,
 "incarnationId":null,"rendererGraphEpoch":null}

$ orca terminal read --terminal term_7d59e6d2-… --json
{
  "ok": true,
  "result": {
    "terminal": {
      "handle": "term_7d59e6d2-…",
      "status": "running",
      "tail": [],
      "truncated": false,
      "limited": false,
      "oldestCursor": "0",
      "nextCursor": "0",
      "latestCursor": "0",
      "returnedLineCount": 0
    }
  }
}
```

The pane is alive. The agent process in it has been up 11h43m with its cwd in that worktree:

```console
$ lsof -a -d cwd -c codex
codex   88221 kimhawk  cwd  DIR  …  /Users/kimhawk/orca/skills

$ ps -p 88221 -o pid,etime,comm
  PID  ELAPSED COMM
88221 11:43:00 codex
```

## The controlled comparison

Two restart-surviving agent panes in the same worktree, read seconds apart. The only difference
between them is that one had since been given a prompt and done work; the other had stayed idle.

| pane | agent | new output since restart? | `returnedLineCount` | cursors (oldest → latest) |
|---|---|---|---|---|
| `term_7d59e6d2-…` | codex (pid 88221) | no | **0** | `"0"` → `"0"` |
| `term_4d3f4261-…` | agy (pid 87919) | yes | **61** | `14092` → `16092` |

```console
$ orca terminal read --terminal term_4d3f4261-… --json | jq '.result.terminal
    | {returnedLineCount, oldestCursor, latestCursor, truncated}'
{"returnedLineCount":61,"oldestCursor":"14092","latestCursor":"16092","truncated":true}
```

Note what this does and does not show. The read verb is **not** blind to a working pane — the agy
read is correct and complete for everything printed after the restart. What is unrecoverable is the
pre-restart scrollback, and what is undetectable is the difference between "that scrollback was
discarded" and "this pane has printed nothing."

Both panes were at `returnedLineCount: 0` earlier in the session; only the one that was subsequently
written to came back. I did not test whether the pre-restart lines ever return (they did not appear
in the agy read — `oldestCursor` starts at `14092`, not `0`).

## What I expected

For the empty case, one of:

- `ok: true` with an explicit marker that the buffer was discarded and the cursors are not
  meaningful (e.g. `bufferAvailable: false`); or
- a typed error such as `scrollback_unavailable`; or
- a cursor value distinguishable from a genuine zero-length buffer.

Anything that lets a caller branch on the difference. Today the two states are byte-identical in
the response.

## Why it matters

`terminal read` is the only content-bearing identity signal for a pane. An orchestrator uses it to
answer "which agent is in this terminal" and "has the worker produced its report yet". For an idle
restart-surviving pane, the zero-line answer is indistinguishable from a genuinely silent pane, so
both questions get a confident wrong answer: our wrapper reported "resolved to 0 candidates" for two
agents that were both alive.

This compounds with the identity gap tracked in `docs/orca-feature-request-terminal-identity.md`:
for a hand-started agent pane, all three identity routes fail at once — the `paneKey` join (such
panes are absent from `worktree ps`'s `agents[]`), the title (a renamed tab makes every leaf report
the *tab* title), and the preview/read pass (this bug). The pane is healthy and completely
unaddressable.

## Proposed fix

Distinguish "buffer empty" from "buffer discarded" in the response — a boolean on the terminal
payload (`bufferAvailable`, or similar), or a typed error. Optionally, persist scrollback across a
restart so the distinction stops mattering; that is the larger change and the flag is sufficient.

I have not read the runtime source, so I am not claiming the distinction is already tracked
internally and merely unexposed. If it is not tracked, that is the fix; if it is, exposing it is.

---

*Filed from the H-MAD dispatch layer (`BrightGold70/skills`, `h-mad/scripts/hmad-dispatch.sh`).
Our side declines to bind on an empty read rather than treating it as evidence — `_orca_find`
Pass 3, see `h-mad/references/orchestration-mode.md` §"Worker identity resolution". Related:
`docs/orca-feature-request-terminal-identity.md`.*

---

## Open question — the one check that decides whether this is filable

**Is `lastOutputAt: null` actually true for the case this report is about?**

The pane measured today (`orphaned: true`, `lastOutputAt: null`, read all-zeros) is a pane whose
worktree is gone. It is arguably *correctly* empty — there is no process and nothing to have
printed. That is **not** this report's case.

This report's case is a pane that is **healthy**: `connected: true`, `status: "running"`, a live
agent process in it (the original observation had codex pid 88221, up 11h43m, cwd in the
worktree), which had produced plenty of output *before* an app restart and none since. The
question is whether such a pane reports:

- `lastOutputAt: null` — in which case the caller already has its branch, this is a documentation
  gap at most, and the report should be withdrawn or reduced to "say so in the guide"; or
- `lastOutputAt: <a pre-restart timestamp>` — in which case the pane looks healthy *and* looks to
  have produced output, the read is empty, and there is genuinely nothing to branch on. That is
  the real bug, and it is worth filing.

**Why it is unresolved.** Reproducing it requires quitting and relaunching the Orca app while a
live agent pane is idle — destructive to whatever session is running, so it was not done
opportunistically. The natural experiment did not help: every restart-surviving pane in the
current runtime has since produced output, which this report already predicts repopulates the
buffer.

**To settle it, next time Orca is restarted for unrelated reasons**, before touching anything:

```console
$ orca terminal list --json     # for a pane with a live agent, idle since the restart:
                                #   note orphaned, lastOutputAt, incarnationId
$ orca terminal read --terminal <that handle> --json
```

If `lastOutputAt` is non-null while the read is all-zeros, file it — that is the pair of readings
this report always needed and never had. If it is null, close this WONTFIX and note that
`lastOutputAt` is the documented branch.

## Note on the identity claim

The closing paragraph says all three identity routes fail at once for a hand-started pane. One
third of that has since changed: `orca worktree ps` exposes `agents[].agentType` keyed by
`paneKey`, and our resolver's Pass 0 joins on it successfully. The "completely unaddressable"
wording overstates the current state and should be softened before filing.
