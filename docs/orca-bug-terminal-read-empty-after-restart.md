# Bug: `terminal read` returns zero lines for a live pane that survived an Orca restart

**Component:** Orca runtime — `orca terminal read`
**Type:** Bug (silent data loss — success-shaped empty result)
**Environment:** macOS 26.5.2 · Orca `appVersion` 1.4.164 · runtime `5bf0c6d1-…`

## Summary

`orca terminal read` returns `{"ok": true}` with `returnedLineCount: 0` and an empty `tail` for a
terminal that is demonstrably alive and producing output. The condition is a pane that outlived an
Orca app restart: the runtime re-adopts the PTY (`status: "running"`, `connected: true`) but the
scrollback the read verb serves is gone, and the response does not say so.

Every cursor in the payload reads `"0"` — `oldestCursor`, `nextCursor`, `latestCursor` — and both
`truncated` and `limited` are `false`. So the response is not "paginated past the end" or "trimmed";
it asserts the buffer is genuinely empty. It is not: the pane has an agent that has been running
in it for over eleven hours.

## Repro

Preconditions: a terminal running an interactive TUI agent, then quit and relaunch the Orca app
(the pane survives; `terminal list` reports `incarnationId: null`, `rendererGraphEpoch: null`).

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

The pane is alive. The agent process in it has been up 11h34m with its cwd in that worktree:

```console
$ lsof -a -d cwd -c codex
codex   88221 kimhawk  cwd  DIR  …  /Users/kimhawk/orca/skills

$ ps -p 88221 -o pid,etime,comm
  PID  ELAPSED COMM
88221 11:34:31 codex
```

Reproduced on both hand-started agent panes in the worktree (`codex` pid 88221, `agy` pid 87919),
each returning identical all-zero-cursor empty reads.

## What I expected

One of:

- the actual scrollback, if the runtime retained it across the restart; or
- `ok: true` with an explicit marker that the buffer was lost and the cursors are not meaningful
  (e.g. `bufferAvailable: false`, or a non-null `oldestCursor` distinguishable from a real empty
  buffer); or
- a typed error such as `scrollback_unavailable`.

Anything except a success response whose fields affirmatively describe a live pane as having
produced no output.

## Why it matters

`terminal read` is the only content-bearing identity signal for a pane. When an orchestrator uses
it to answer "which agent is in this terminal" or "has the worker produced its report yet", a
success-shaped zero-line answer is indistinguishable from a genuinely idle pane. That produces a
false negative with full confidence: our wrapper reported "resolved to 0 candidates" for two agents
that were both alive and working.

This also compounds with the identity gap tracked in
`docs/orca-feature-request-terminal-identity.md`: for a hand-started agent pane, all three identity
routes fail at once — the `paneKey` join (such panes are absent from `worktree ps`'s `agents[]`),
the title (a renamed tab makes every leaf report the *tab* title), and the preview/read pass (this
bug). A caller that treats an empty read as evidence of an idle or wrong pane will route work
away from a healthy agent.

## Proposed fix

Distinguish "buffer empty" from "buffer unavailable" in the response. The cheapest form is a
boolean on the terminal payload; a typed error is also fine. The current all-zeros cursor triple
already encodes the state internally — it just is not exposed as anything a caller can branch on
without guessing.

---

*Filed from the H-MAD dispatch layer (`BrightGold70/skills`, `h-mad/scripts/hmad-dispatch.sh`).
Our side declines to bind on an empty read rather than treating it as evidence — `_orca_find`
Pass 3, see `h-mad/references/orchestration-mode.md` §"Worker identity resolution". Related:
`docs/orca-feature-request-terminal-identity.md`.*
