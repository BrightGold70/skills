# OMC interaction note (informational — not a bug report)

> Audience: oh-my-claudecode maintainers. Authored as a Phase-7 closure artifact of the
> `h-mad-audit-surfaces-reconcile` feature. This is **informational**, not a defect report —
> OMC's behavior is correct given the trigger; the durable fix was made on the h-mad side.

## Observed interaction

During `/h-mad` runs, OMC's `persistent-mode.mjs` surfaced two streams of noise:

1. **Autopilot Stop-hook nag** — `persistent-mode.mjs` emits an "Autopilot not complete" message on most turns even with no autopilot state on disk (deleting `.omc/state/*.json` did not stop it). It appears to be an unconditional nag rather than state-driven.
2. **Tool-error retry guidance** — `post-tool-use-failure.mjs` records any tool failure to `last-tool-error.json`; `persistent-mode.mjs` then injects `[TOOL ERROR - RETRY REQUIRED]` on the next Stop, escalating to `[TOOL ERROR - ALTERNATIVE APPROACH NEEDED]` ("STOP RETRYING") at `retry_count >= 5`.

## Root cause of stream 2 (now fixed h-mad-side)

The h-mad audit gate previously signalled its verdict via a non-zero process exit (`awk … END{exit (c>0)}`). A gate-FAIL is the *normal* mid-audit case, but as a Bash tool call a non-zero exit is reported by the Claude Code harness as a `PostToolUseFailure` — which `post-tool-use-failure.mjs` correctly records, triggering the retry-guidance injection. **OMC was behaving correctly**: it was flagging a genuine non-zero exit. The fix was to stop h-mad from emitting a non-zero exit for a verdict — the gate now prints a `GATE: PASS|FAIL` token and exits 0. No OMC change is required for stream 2.

## Possible OMC-side consideration (stream 1 only)

The autopilot Stop-hook nag (stream 1) appears to fire independent of on-disk autopilot state. If that is unintended, gating the message on the presence of a live autopilot state file would reduce noise for users running other workflows alongside OMC. Current operator workaround: `export DISABLE_OMC=1` or `OMC_SKIP_HOOKS=persistent-mode`.

## Reproduction context

- OMC version observed: marketplace build with `scripts/persistent-mode.mjs` (`getToolErrorRetryGuidance`) + `scripts/post-tool-use-failure.mjs` (`last-tool-error.json` writer with 60s staleness window).
- h-mad fix commit: gate token-verdict (feature `h-mad-audit-surfaces-reconcile`).
