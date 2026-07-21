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
| `hmad-dispatch read <codex\|agy> [--lines N]` | Scrape the agent screen to stdout |
| `hmad-dispatch wait <codex\|agy> [--timeout S]` | Block until the agent is idle |
| `hmad-dispatch alive <codex\|agy>` | Liveness probe (exit 0/1) |
| `hmad-dispatch clear <codex\|agy>` | Reset the agent's context (`/clear`) |
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
