# Feature request: expose a stable per-terminal identity in `orca terminal list`

> Filed: https://github.com/stablyai/orca/issues/9870 (2026-07-22)
>
> **CLOSED 2026-07-23 as completed.** The field already existed — `orca worktree ps --json` returns
> `.result.worktrees[].agents[]` with an explicit `agentType` keyed by a `paneKey` of
> `<tabId>:<leafId>`, joinable to `terminal list`'s `.tabId`/`.leafId`. This document inventoried
> only `terminal list` and `terminal show`, which is why it concluded the capability was absent.
> Shipped our side as `_orca_find` Pass 0 (main `bf9c4c3`); see `docs/skill-monitoring.md` §J16.
>
> One gap was **not** closed and is deliberately not being tracked here: whether a pane where a
> human typed `codex` into an already-open shell registers in `agents[]`, or whether only
> Orca-spawned agents do. A plain `terminal create` shell is absent from `agents[]` (verified). If
> adoption is unsupported, option 3 below (`titleSource` discriminator) retains standalone value.
>
> **ANSWERED 2026-08-03 — adoption is NOT supported, so option 3 keeps its standalone value.**
> Measured on a live pair of hand-started agents: `codex` (pid 88221) and `agy` (pid 87919), both
> up 9 hours with cwd in this worktree, were **absent from `agents[]` entirely**. `worktree ps`
> reported `liveTerminalCount: 3` with exactly ONE `agents[]` entry — the coordinator, the only
> pane Orca had spawned. Both panes had survived an Orca restart (`incarnationId: null`,
> `rendererGraphEpoch: 0`).
>
> All three identity passes were blind at once for that pane class: the paneKey join (absent from
> `agents[]`), the title pass (the tab had been renamed, so both panes read `Claude - skills repo`
> — a *tab* title shared by every leaf), and the preview pass (`terminal read` returned
> `returnedLineCount: 0`, the renderer buffer having died with the restart). The wrapper reported
> "resolved to 0 candidates" while both agents were demonstrably alive.
>
> There is also **no OS-side join available**: the schema exposes no `tty`, `pid`, or `ptyId`
> (`orca agent-context --json` — 0 occurrences of each), and macOS blocks `ps e`, so a process
> found via `lsof -a -d cwd -c codex` cannot be mapped back to a pane. Our side ships this as
> `_orca_find` Pass 3 (OS evidence), which binds only when exactly one unclaimed pane and one live
> matching process make the mapping forced, and otherwise reports the evidence and declines —
> main `398d120`, see `references/orchestration-mode.md` §"Worker identity resolution".

**Component:** Orca CLI / daemon — `orca terminal list`, `orca terminal rename`
**Type:** Feature request (with a small correctness observation about `rename`)
**Environment:** macOS 26.5.2 · Orca daemon `daemon-v23`/`v24` (`orca --version` prints no version string) · CLI verbs `terminal list --json`, `terminal rename`

## Summary

There is no reliable way to identify **which CLI is running in which terminal** from `orca terminal list --json`. The only identity-bearing fields are `title` and `preview`, and for some agents neither is stable:

- `title` is the OSC/derived terminal title emitted by the **running program**, not something the caller controls. Google's `agy`/Gemini CLI emits `agy` (usable); **OpenAI's Codex CLI emits its cwd basename** (e.g. `skills`), never `codex`.
- `preview` is live scrollback — the launch banner (model id / `OpenAI Codex`) **scrolls out of view** once the agent does any work, so a preview match works only on a fresh pane.
- `orca terminal rename --title "…"` looks like the fix, but the value it sets is **not surfaced** in `terminal list --json` (see repro), so it cannot be used for identification.

Net: a multi-agent orchestrator cannot deterministically route "dispatch this to the Codex terminal" without the operator manually pinning a runtime handle.

## Repro

```console
$ orca terminal list --json | jq -r '.result.terminals[] | select(.worktreePath|endswith("/skills")) | "\(.handle)  title=\(.title)"'
term_41f3e488-…  title=skills        # ← the Codex pane; title is the cwd basename, not "codex"
term_92396979-…  title=agy           # ← the agy pane resolves fine

# Try to fix identity by renaming the Codex terminal:
$ orca terminal rename --terminal term_41f3e488-… --title "Codex - skills repo" --json
{"ok":true}

# The rename "succeeded", but the list still reports the derived title:
$ orca terminal list --json | jq -r '.result.terminals[] | select(.handle=="term_41f3e488-…") | .title'
skills                                # ← UNCHANGED; the custom title is not surfaced

# So any title-based identification still fails.
```

Observed full schema for one terminal (no field names the running program):

```json
{
  "handle": "term_41f3e488-…", "ptyId": "…::/Users/…/skills@@…",
  "worktreeId": "…", "worktreePath": "/Users/…/skills", "branch": "refs/heads/main",
  "tabId": "…", "leafId": "…", "title": "skills", "connected": true,
  "writable": true, "lastOutputAt": 1784695513234, "preview": "…decayed scrollback…"
}
```

## What I expected

Either (a) the custom title set via `orca terminal rename` is returned by `terminal list --json` (so an operator/orchestrator can label a terminal and match on it), or (b) `terminal list` exposes the running command/process so agents are identifiable without relying on the program's self-emitted title.

## Proposed fix (either is sufficient)

1. **Surface the custom tab title.** Return the value set by `orca terminal rename` as a distinct field (e.g. `customTitle`, or have `title` reflect it), so a rename is a usable, stable identity handle. This is the smaller change and matches the natural expectation that "rename" affects what `list` shows.
2. **Expose the running program.** Add a field naming the foreground command/process per terminal (e.g. `command`: `codex` / `agy` / `zsh`, or a `pid`/argv). This gives robust identity independent of what the program emits as its OSC title.

Option 1 unblocks the common case (operator can label a pane once). Option 2 is the more general fix (works with zero operator action).

## Why it matters

Multi-agent workflows dispatch tasks to specific agent terminals (a TDD/impl agent vs a review agent). Today that requires the operator to read a runtime `handle` from `terminal list` and pin it out-of-band, and to re-pin whenever a pane's banner decays. A stable identity field removes the manual step and the decay failure mode entirely.

## Minor correctness note

`orca terminal rename` returning `{"ok":true}` while the change is invisible to `terminal list --json` is surprising. If option 1 isn't adopted, consider documenting that `rename` affects only the in-app tab chrome and is not reflected in the CLI listing.

---

*Filed from the H-MAD dispatch layer (`BrightGold70/skills`, `h-mad/scripts/hmad-dispatch.sh`). Local workaround in place: an explicit runtime-handle pin (`hmad-dispatch pin <agent> <handle>`) captured at launch. See that repo's `docs/skill-monitoring.md` §H5.*
