# Feature request: expose a stable per-terminal identity in `orca terminal list`

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
