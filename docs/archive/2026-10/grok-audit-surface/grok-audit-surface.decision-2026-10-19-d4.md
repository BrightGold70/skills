# grok-audit-surface: operator decision D4-agnostic (2026-10-19)

Premise found false: every document since the brainstorm (`0be0f064`) targets grok **1.0.62** and the brainstorm says it is "present: `~/.grok/bin/grok`". Measured 2026-10-19: every `grok` on PATH (`~/.grok/bin/grok`, `~/.local/bin/grok`) reports `grok 1.0.52 (0920c8169e27) [stable]`; `/opt/homebrew/bin/grok` reports `1.0.1`; the newest `~/.grok/CHANGELOG.md` entry is `1.0.52 — 2026-10-11`. No 1.0.62 was ever observed.

Operator decision: **version-agnostic.** Canonical sentence (quote verbatim):

> The audit-path re-smoke runs against the grok on PATH at S1, whatever its version; the smoke records that binary's path and its `grok --version` line, and the measurement doc names that version. No phase document names a target grok version.

Consequences: every "1.0.62" in spec, plan and design becomes "the recorded grok version" (or is removed); AC-1.5 / AC-1.8 sentences name the recorded version, not a literal one. `h-mad/references/grok-runtime.md`'s existing 1.0.41 sentence is unchanged.

Re-derive:
```bash
which -a grok | sort -u | while read g; do echo "$g: $($g --version 2>&1 | head -1)"; done
head -1 ~/.grok/CHANGELOG.md
```

## Addendum (2026-10-19, later the same day)

The measurement above was true when taken and is now stale: grok **auto-updated**. Re-measured after the spec/plan/design revisions: `~/.grok/bin/grok` and `~/.local/bin/grok` report `grok 1.0.62 (1474f9cbdd91) [stable]`, binary mtime `Oct 19 08:47:31 2026`; `~/.grok/CHANGELOG.md` still heads `1.0.52` (the changelog lags the binary, so it is not a version source). All three authors caught this independently.

This strengthens the decision rather than reversing it: the installed version moved under a live feature within one session, so any document pinning a literal version is stale by construction. The smoke records the version that actually ran; the measurement doc names it.
