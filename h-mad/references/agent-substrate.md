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
| `hmad-dispatch env` | Print resolved substrate + agent→terminal mapping, ending in a canonical `PREFLIGHT: PASS\|FAIL [stale=…] [conflict=…]` verdict line (run at Phase-5/audit preflight; assert the token — exit is 0 on both verdicts) |
| `hmad-dispatch resolve <codex\|agy>` | Resolve one agent to its handle; stdout + exit 0/1/2 |
| `hmad-dispatch launch <codex\|agy> [--worktree <sel>] [--focus]` | Spawn a FRESH agent terminal via `orca terminal create --command …`, then **resolve its live handle by joining the create response's `paneKey` against `terminal list`** and pin that. The zero-manual durable identity path (H5) — no title/preview dependence. **Not** `.result.terminal.handle`: that is a pre-adoption placeholder the pane never has (J1, confirmed 3×), and pinning it made every later dispatch vanish. Fails loud if the response carries no `paneKey`, or if the key does not appear within `HMAD_LAUNCH_RESOLVE_TIMEOUT` (default 20s). Launch command overridable via `HMAD_ORCA_CODEX_LAUNCH_CMD` / `HMAD_ORCA_AGY_LAUNCH_CMD` |
| `hmad-dispatch pin <codex\|agy> <handle>` | Record one agent's handle in the session pin file (preserves the sibling). The durable way to make Codex addressable — capture its handle from `orca terminal list` (or at launch) and pin it, since neither auto-detect nor `orca terminal rename` yields a stable `codex` identity (H5) |
| `hmad-dispatch pin-agents [--clear]` | Resolve codex+agy ONCE and freeze the handles into the session pin file (`${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}`). Run after the Phase-5 preflight so later dispatches survive preview decay (H4). **Fails loud (rc=1)** if it can't resolve an agent — Codex has no stable auto-identity, so pin `HMAD_ORCA_CODEX_TERMINAL` at launch; `--clear` removes the file |
| `hmad-dispatch send <codex\|agy> <promptfile>` | Dispatch + submit; inlines below the size threshold, otherwise file-indirection (see below) |
| `hmad-dispatch read <codex\|agy> [--lines N] [--cursor N \| --from-start]` | Scrape the agent screen to stdout. `--cursor N` reads from an absolute offset; `--from-start` (= `--cursor 0 --limit 4000`) recovers a report longer than the retained tail viewport |
| `hmad-dispatch wait <codex\|agy> [--timeout S]` | Block until the agent is idle — confirmed by two identical reads, not taken on trust (see below) |
| `hmad-dispatch alive <codex\|agy>` | Liveness probe (exit 0/1) |
| `hmad-dispatch clear <codex\|agy>` | Reset the agent's context (`/clear`) |
| `hmad-dispatch interrupt <codex\|agy>` | Cancel a running/wedged turn with Ctrl-C (0x03). NEVER nudge a TUI REPL with a bare Enter — it submits a blank turn |
| `hmad-dispatch report-wait <path> [--timeout S] [--interval S]` | Wait for the agent to drop `<path>` + `<path>.done`, then emit the file. Reliable replacement for `wait`+`read`+sentinel-extract; substrate-agnostic (shared fs). The polling loop is the standalone `scripts/h_mad_report_wait.py`; when the dispatched implementer is editing `hmad-dispatch.sh` itself, poll with that script directly so the coordinator never re-parses a half-saved wrapper (H3). See orchestration-mode.md §"Report-file transport" |
| `hmad-dispatch notify <title> <body>` | Halt ping (best-effort) |

## Preflight receipt enforcement

`hmad-dispatch env` writes a receipt artifact beside the pin file (unless
`HMAD_PREFLIGHT_RECEIPT_FILE` overrides its path) whenever it prints
`PREFLIGHT: PASS`; it removes the receipt on `PREFLIGHT: FAIL`. The artifact is
plain text containing `verdict=PASS`, the current `fingerprint=codex=…;agy=…`,
and a Unix `ts=…` timestamp. `hmad-dispatch send` refuses with rc=1 and sends
nothing unless the receipt exists, says PASS, is within the TTL, and its
fingerprint still matches current resolution. Refusal diagnostics name one of
`preflight_not_run`, `preflight_expired`, `preflight_handles_rotated`, or
`preflight_agent_conflict`.

The controls are:

| Variable | Default | Purpose |
|---|---|---|
| `HMAD_PREFLIGHT_RECEIPT_FILE` | beside the pin file | Override the receipt artifact path |
| `HMAD_PREFLIGHT_TTL_SEC` | `3600` | Maximum receipt age in seconds |
| `HMAD_SKIP_PREFLIGHT` | unset (enforced) | Skip receipt validation for `send` when set; handle-conflict protection remains active |

To recover, run `hmad-dispatch env` and confirm `PREFLIGHT: PASS`; re-pin or
relaunch after handle rotation, and pin distinct handles after a conflict.
`clear` and `interrupt` are recovery verbs and are not guarded.

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

## Prompt size: the silent-output failure mode

Above some size an agent reads the staged file, reports a token count, emits
**nothing**, and returns to its prompt. No error, no partial output. That failure
*shape* is real and worth designing against. The **boundary**, however, was
mis-recorded for years, and the number cost real work.

**Delivery mode is the variable the original measurement omitted.**
`hmad-dispatch send` inlines a prompt only up to `HMAD_SEND_INLINE_MAX`
(default **8192 B**); above that it stages the file and tells the agent to read
it. Audit prompts run 32–61 KB, so **every audit prompt is delivered by file
indirection and none is ever pasted into the TUI**. The 2026-07-21 session
recorded sizes but not which mode it used.

| Prompt | Delivery | Result |
|---|---|---|
| 38,921 B | unrecorded | emitted normally |
| 49,273 B | unrecorded | emitted normally |
| 53,066 B | unrecorded | **silent** — twice, `/clear` did not recover it |
| 52,997 B | file indirection | emitted normally |
| 53,058 B | file indirection | emitted normally |
| 56,349 B | file indirection | emitted — token fragmented across frames (2026-07-23) |
| 58,536 B | file indirection | emitted normally |
| 61,493 B | file indirection | emitted normally — contiguous token (2026-07-23) |

**Five file-indirection observations spanning 52,997–61,493 B, all answered.
There is no file-indirection silence on record**, including at sizes well past
the "cliff". Treat **61,493 B as the largest size confirmed answered** — beyond
it is *unverified*, not known-bad. `h_mad_assemble_audit.py` warns on that basis
now; it previously predicted failure above 49 KB, which caused at least one
design audit to be trimmed for no reason.

**Do not measure this by grepping a tail — that is probably how the original
boundary was mis-recorded.** The reply renders into a TUI that redraws and
fragments it across frames. Measured 2026-07-23: the 61,493 B probe's token
appeared first as a partial `J13OK J1` and only later as the complete
`J13OK J13-SIXTY-9F3A`; the 56,349 B probe's token split into `J13-FIFTYFIVE-4`
and `D8E` in separate frames and never appeared contiguously in any tail.

**Three** independent pollers tailing 40 lines for the exact token reported
`RESULT=SILENT after ~5min` — two for the 61,493 B probe, one for the 56,349 B
probe. **All three were wrong.** A full-buffer read found the 61,493 B token
contiguous (`J13OK J13-SIXTY-9F3A`) and the 56,349 B token as frame-split
fragments; the staged files' filler never appeared in the pane at all, so those
characters could only be the agent's own output. A tail-grep does not
distinguish "produced nothing" from "produced something the viewport reflowed",
and those two demand opposite responses.

Note also that the retained buffer was **47,711 B — smaller than either prompt**.
Scrollback capacity is not a measure of what the agent emitted, and it is another
reason to extract on the sentinel pair rather than eyeball a pane.

Read the whole buffer (`hmad-dispatch read <agent> --from-start`) and extract
with `h_mad_extract_report.py` — which is what the sentinel-pair protocol exists
for, and what F5 already warned about. An ad-hoc grep is the wrong instrument
even when you are only "probing".

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
- **orca (dynamic):** resolution precedence is **explicit env pin → session pin file → auto-detect**. `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL` pin a terminal handle; else the session pin file (`${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}`, written by `pin-agents`) is consulted; else auto-detect runs three passes, in this order:
  - **Pass 0 — the paneKey join (J16, the real identity).** `orca worktree ps --json` returns `.result.worktrees[].agents[]` with an explicit **`agentType`** (`codex`, `antigravity`, `claude`) keyed by a **`paneKey`** of `<tabId>:<leafId>`, and `orca terminal list --json` returns `.tabId`/`.leafId` per terminal. Joining them names the running program exactly, independent of title and preview. Note `agentType` is **`antigravity`, not `agy`** — `_orca_agent_type` maps the alias. Scoped to the coordinator's own worktree; **exactly one** match resolves, two decline to UNRESOLVED rather than guess. `worktree ps --limit` drops whole worktrees and never agents within one, so truncation cannot hide a same-worktree rival from a scoped match; unscoped (no coordinator, cwd inside no known worktree) a truncated listing is refused outright.
  - **Pass 1 — leading title word**, and **Pass 2 — preview signature** (`openai codex|model: *gpt-|gpt-N <effort>`, `antigravity cli|gemini N`). Both are inference from strings a pane may carry for other reasons, and both are now fallbacks for when Pass 0 is unavailable.

  Zero or multiple matches after all three → wrapper halts; pin the env var or run `pin-agents`. **What Pass 0 does not change:** `terminal list`'s own schema still has no identity field ([orca#9870](https://github.com/stablyai/orca/issues/9870), now an ergonomics request rather than a blocker), the preview banner still decays once the agent works, and **renaming still does not help** — `orca terminal rename` sets a separate tab-title layer that `terminal list --json` does not surface, so `.title` stays the OSC title the program emits (Codex emits its cwd basename, e.g. `skills`; agy emits `agy`), unaffected by any rename (verified: a rename returns `ok:true` while `.title` stays `skills` and `resolve codex` still finds 0). A handle pin — via the env var, `pin <agent> <handle>`, or the pin file — remains the most durable identity for a long run (H4/H5), and owning the launch beats resolving after the fact. Pass 0's value is that an **un-owned** pane is now recoverable instead of UNRESOLVED: measured live 2026-07-23 with pins bypassed, both agents went from `UNRESOLVED`/`UNRESOLVED` to correctly resolved, on a listing where the Antigravity pane's `.title` read `"Codex - skills repo"` and both previews were empty.

## Launching the panes
- **cmux:** `cmux split-window --command 'codex'` / `cmux split-window --command 'agy --dangerously-skip-permissions'`.
- **orca:** `orca terminal create` (then run `codex` / `agy` in it), or pin an existing one via the env vars above.

## Open items (confirm on your host, update this file)
- Session-marker env var names for cmux and Orca.

## Confirmed Orca terminal schema (v1)
- Wait: `orca terminal wait --terminal <handle> --for exit|tui-idle [--timeout-ms <n>]`.
- Read: `orca terminal read --terminal <handle> [--limit <n>]`.
- List: `orca terminal list --json` returns terminal handles at `.result.terminals[].handle`.
