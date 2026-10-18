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
