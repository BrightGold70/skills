# Agent Dispatch Substrate (cmux | orca)

H-MAD drives two long-lived peer-agent REPLs — **codex** (implementation/tests) and
**agy** (Antigravity; spec/architectural review) — through one wrapper:
`scripts/hmad-dispatch.sh`. The wrapper hides whether the host is **cmux**
(`manaflow-ai/cmux`) or **Orca** (`stablyai/orca`). Never call `cmux`/`orca` directly.

## Verbs
| Verb | Purpose |
|------|---------|
| `hmad-dispatch env` | Print resolved substrate + agent→terminal mapping (run at Phase-5/audit preflight) |
| `hmad-dispatch send <codex\|agy> <promptfile>` | File-indirection dispatch + submit |
| `hmad-dispatch read <codex\|agy> [--lines N]` | Scrape the agent screen to stdout |
| `hmad-dispatch wait <codex\|agy> [--timeout S]` | Block until the agent is idle |
| `hmad-dispatch alive <codex\|agy>` | Liveness probe (exit 0/1) |
| `hmad-dispatch clear <codex\|agy>` | Reset the agent's context (`/clear`) |
| `hmad-dispatch notify <title> <body>` | Halt ping (best-effort) |

## Substrate detection (highest precedence wins)
1. `HMAD_SUBSTRATE=cmux|orca` — explicit override.
2. Session marker env var (best-effort; confirm names on your host).
3. Binary presence (`orca` alone → orca; `cmux` present → cmux; both → cmux).
4. Default `cmux`.

## Agent identity
- **cmux (static):** `HMAD_CMUX_CODEX_SURFACE` (default `surface:5`), `HMAD_CMUX_AGY_SURFACE` (default `surface:2`).
- **orca (dynamic):** `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL` pin an id/name; else resolved from `orca terminal list --json` by matching the terminal running `codex`/`agy`. Ambiguous → wrapper halts, pin the env var.

## Launching the panes
- **cmux:** `cmux split-window --command 'codex'` / `cmux split-window --command 'agy --dangerously-skip-permissions'`.
- **orca:** `orca terminal create` (then run `codex` / `agy` in it), or pin an existing one via the env vars above.

## Open items (confirm on your host, update this file)
- Session-marker env var names for cmux and Orca.
- Exact `orca terminal list --json` field shape (`.id`, `.command`/`.name`).
- `orca terminal wait … tui-idle` exact syntax.
Until confirmed, `HMAD_SUBSTRATE` + the explicit identity pins always yield a correct result.
