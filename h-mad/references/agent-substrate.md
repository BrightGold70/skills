# Agent Dispatch Substrate (cmux | orca)

H-MAD drives two long-lived peer-agent REPLs — **codex** (implementation/tests) and
**agy** (Antigravity; spec/architectural review) — through one wrapper:
`scripts/hmad-dispatch.sh`. The wrapper hides whether the host is **cmux**
(`manaflow-ai/cmux`) or **Orca** (`stablyai/orca`). Never call `cmux`/`orca` directly.

## Putting it on PATH
Every verb below is written as a bare `hmad-dispatch <verb>`. Put the skill's
`bin/` on PATH once and they work verbatim:

```bash
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
```

`bin/hmad-dispatch` resolves its own physical location before exec'ing
`scripts/hmad-dispatch.sh`, so it works through the usual symlink chain
(`~/.claude/skills/h-mad` → a checkout) and from any working directory.
Without it, each call needs the absolute path to `scripts/hmad-dispatch.sh`,
which differs per install and per checkout.

## Verbs
| Verb | Purpose |
|------|---------|
| `hmad-dispatch env` | Print resolved substrate + agent→terminal mapping (run at Phase-5/audit preflight) |
| `hmad-dispatch send <codex\|agy> <promptfile>` | Dispatch + submit; inlines below the size threshold, otherwise file-indirection (see below) |
| `hmad-dispatch read <codex\|agy> [--lines N] [--cursor N \| --from-start]` | Scrape the agent screen to stdout. `--cursor N` reads from an absolute offset; `--from-start` (= `--cursor 0 --limit 4000`) recovers a report longer than the retained tail viewport |
| `hmad-dispatch wait <codex\|agy> [--timeout S]` | Block until the agent is idle — confirmed by two identical reads, not taken on trust (see below) |
| `hmad-dispatch alive <codex\|agy>` | Liveness probe (exit 0/1) |
| `hmad-dispatch clear <codex\|agy>` | Reset the agent's context (`/clear`) |
| `hmad-dispatch interrupt <codex\|agy>` | Cancel a running/wedged turn with Ctrl-C (0x03). NEVER nudge a TUI REPL with a bare Enter — it submits a blank turn |
| `hmad-dispatch report-wait <path> [--timeout S] [--interval S]` | Wait for the agent to drop `<path>` + `<path>.done`, then emit the file. Reliable replacement for `wait`+`read`+sentinel-extract; substrate-agnostic (shared fs). See orchestration-mode.md §"Report-file transport" |
| `hmad-dispatch notify <title> <body>` | Halt ping (best-effort) |

## How `send` delivers a prompt

`send` picks its delivery mode from the prompt's size, so callers do not have
to:

| Prompt size | Delivery |
|---|---|
| ≤ `HMAD_SEND_INLINE_MAX` (default 8192 bytes) | Contents inlined into the pane |
| > threshold | A short instruction naming the staged file, by canonical absolute path — the agent reads it itself |

The threshold sits inside the ~5–10 KB range the file-indirection rule names,
and well under the 32–61 KB that audit prompts reach in practice. Tune it with
`HMAD_SEND_INLINE_MAX` if a substrate turns out to tolerate more or less.

Before this split, `send` inlined unconditionally (`$(cat "$2")`), which put
the documented audit dispatch step in direct conflict with the indirection
rule at exactly the sizes that occur — so every audit had to be dispatched by
hand instead.

## Prompt size: the silent-output cliff

Above a size threshold an agent reads the staged file, reports a token count,
emits **nothing**, and returns to its prompt. No error, no partial output.

Measured on one agent in one session — treat as an order of magnitude, not a
constant:

| Prompt | Result |
|---|---|
| 38,921 B | emitted normally |
| 49,273 B | emitted normally |
| 53,066 B | **silent** — twice, and `/clear` did not recover it |

So the cliff sat between ~49 KB and ~53 KB there. Re-measure on your own host
before relying on the boundary; what generalises is that the failure is *silent
and total*, not that it starts at 53 KB.

**Idle detection cannot see this.** The pane really is settled — nothing is
being written — so `wait` returns satisfied and a two-read stability comparison
reports STABLE. Those probes answer "has output stopped", which is a different
question from "was there any output". A run that trusts `wait` alone will scrape
an empty pane and proceed.

What catches it is extraction, not readiness: `h_mad_extract_report.py` and
`h_mad_extract_verdict.py` both exit 2 on absent or empty output rather than
returning something scoreable. That is why the halt conditions are phrased
around a *missing* verdict and not only a bad one — see the `no_verdict` halts
in `failure-recovery.md`.

**Never write a sentinel literally into a dispatch prompt.** The prompt is
echoed in the pane, so the orchestrator's own grep matches its own instruction
instead of the agent's report — the extraction then succeeds against text the
agent never produced. Split the token across fragments when composing the
prompt (`"AUDIT-D2-BEG" + "IN"`), so only real agent output can match.

## How `wait` decides an agent is idle

Idleness is confirmed by **two consecutive identical non-empty reads** of the
pane, on both substrates. A single read can catch a pane mid-write; two
matching ones cannot. An empty read never counts — a blank pane is absence of
evidence, not evidence of idleness, and two empty reads are trivially
"identical".

| Substrate | Sequence |
|---|---|
| orca | `terminal wait --for tui-idle` as a fast first gate, then the stability check |
| cmux | stability check only (cmux has no native idle) |

Orca's native `--for tui-idle` was observed returning `satisfied: true` twice
while an agent was still generating, so downstream steps read a partial pane.
It is therefore treated as **one-directional evidence**: its "not idle" is
authoritative and aborts the wait, its "idle" is only a hint that the stability
check then confirms. Poll interval is `HMAD_WAIT_POLL_INTERVAL` (default 3s).

> **Verification status.** The stability logic is unit-tested against stubs,
> and it is the same approach cmux has always used. The live symptom — a real
> Orca agent mid-response — cannot be reproduced by a stub, which is idle by
> construction. Confirmation against a live runtime is outstanding; if you see
> a partial read after a `wait` returns, this fix did not hold and the issue
> should be reopened.

## Capturing an agy (Antigravity / Gemini-TUI) report

The Antigravity CLI redraws its whole screen every frame, which makes report
capture unreliable in ways cmux/Codex are not. Observed live and worked around:

- **Completion signal — poll for the sentinel, not `tui-idle`.** Gemini's spinner
  fools `terminal wait --for tui-idle` (it reports `satisfied:false` with a stale
  `blockedReason` when the report is actually done, and sometimes idle while still
  generating). Treat the appearance of the `<sentinel>-END` line in the tail as the
  completion signal instead.
- **Never nudge with a bare Enter.** At the REPL `>` prompt an empty submit starts
  a blank junk turn. To free a done-but-unrendered or wedged pane, use
  `hmad-dispatch interrupt agy` (Ctrl-C). Sent once it cancels the turn; the pane
  drops toward the shell and its scrollback **freezes**, which is the reliable
  capture state.
- **Recover a report the tail truncated.** The rendered report is often longer than
  the retained viewport, and per-frame redraw fragments the sentinel across frames.
  After freezing, `hmad-dispatch read agy --from-start` (full buffer) gets the whole
  `BEGIN…END` pair. Then dedent + normalize `•`→`-` before the gate (the gate now
  tolerates both, but the extractor still writes raw TUI text).
- **Version drift.** agy can self-upgrade via Homebrew mid-session (seen 1.1.1→1.1.5),
  dropping back to a welcome + trust-workspace prompt that interrupts the dispatch.
  Preflight the version / re-confirm trust before a dispatch block if reliability matters.

## Substrate detection (highest precedence wins)
1. `HMAD_SUBSTRATE=cmux|orca` — explicit override.
2. Session marker env var (best-effort; confirm names on your host).
3. Binary presence (`orca` alone → orca; `cmux` present → cmux; both → cmux).
4. Default `cmux`.

## Agent identity
- **cmux (dynamic):** `HMAD_CMUX_CODEX_SURFACE` / `HMAD_CMUX_AGY_SURFACE` pin a surface id; else resolved from `cmux tree --all` by matching the terminal title for `codex`/`agy` (`_cmux_find`, mirroring the orca path). Zero or multiple matches → wrapper halts (`UNRESOLVED`); pin the env var. Hardcoded `surface:5`/`surface:2` defaults were removed — they went stale per session and silently misrouted audits/TDD to the wrong pane.
- **orca (dynamic):** `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL` pin a terminal handle; else resolved from `orca terminal list --json` by matching terminal preview/title for `codex`/`agy`. Zero or multiple matches → wrapper halts; pin the env var. The list schema has no field that identifies the running program, so a handle pin is the reliable identity.

## Launching the panes
- **cmux:** `cmux split-window --command 'codex'` / `cmux split-window --command 'agy --dangerously-skip-permissions'`.
- **orca:** `orca terminal create` (then run `codex` / `agy` in it), or pin an existing one via the env vars above.

## Open items (confirm on your host, update this file)
- Session-marker env var names for cmux and Orca.

## Confirmed Orca terminal schema (v1)
- Wait: `orca terminal wait --terminal <handle> --for exit|tui-idle [--timeout-ms <n>]`.
- Read: `orca terminal read --terminal <handle> [--limit <n>]`.
- List: `orca terminal list --json` returns terminal handles at `.result.terminals[].handle`.
