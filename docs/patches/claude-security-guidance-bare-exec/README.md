# security-guidance — bare `"exec("` substring blocks legitimate edits

**Status:** applied locally on 2026-08-09. Upstream report drafted, **not filed**.
**Upstream:** `anthropics/claude-plugins-official` (plugin `security-guidance`)
**Target file:** `~/.claude/plugins/cache/claude-plugins-official/security-guidance/unknown/hooks/security_reminder_hook.py`

## Why this directory exists

Same story as the sibling `bkit-enh310-quoted-heredoc-body/` patch: the file lives in a
plugin cache that a plugin update replaces wholesale, silently. This directory holds the
diff, a re-apply procedure, and `verify.py` to detect the loss.

## The problem

`SECURITY_PATTERNS` matched content with naive `substring in content` (`check_patterns`,
~line 194). The `child_process_exec` rule listed:

```python
"substrings": ["child_process.exec", "exec(", "execSync("],
```

The bare `"exec("` matches **any** `x.exec(y)`. In practice that means JavaScript regex
`.exec()` — `START.exec(text)`, `while ((m = re.exec(s)) !== null)` — none of which are
`child_process`. And this hook does not merely warn: it calls `sys.exit(2)`, which **blocks
the edit**.

Hit live while editing a file containing `START.exec(text)`. The warning even recommends
`src/utils/execFileNoThrow.ts`, a path from Claude Code's own repo that does not exist in
most projects.

Mitigating factor: warnings are keyed `{file_path}-{rule_name}` and shown once per session
(`load_state` / `save_state`), so an immediate retry of the same edit succeeds. It is a
one-shot speed bump per file+rule, not a permanent wall.

## The fix

1. Add an optional `"regexes"` key to `SECURITY_PATTERNS`, evaluated in `check_patterns`
   after the substring pass.
2. Drop the bare `"exec("` substring and express the real signal as a regex requiring a
   **bare** call:

```python
"substrings": ["child_process.exec", "execSync("],
"regexes": [r"(?<![\w.$])exec\s*\("],
```

The negative lookbehind rejects a method call (`.` before the name) and an identifier that
merely ends in those four letters, while still matching a genuine bare call and the common
`const { exec } = require('child_process')` destructured shape. `child_process.exec` and
`execSync(` stay as substrings — both are specific enough already.

**This is strictly better in both directions.** Beyond removing 4 false positives, the regex
also catches a bare call written with a space before the paren, which the old substring
missed entirely — a false *negative* the patch closes. `verify.py`'s `bare-exec-space` case
pins it.

## Re-applying after a plugin update

```bash
# 1. Did the update drop the patch?
python3 docs/patches/claude-security-guidance-bare-exec/verify.py   # exit 1 => re-apply

# 2. Re-apply (plugin root, not the hooks/ dir)
cd ~/.claude/plugins/cache/claude-plugins-official/security-guidance/unknown
patch -p1 --dry-run < /Users/kimhawk/orca/skills/docs/patches/claude-security-guidance-bare-exec/security_reminder_hook.patch
patch -p1           < /Users/kimhawk/orca/skills/docs/patches/claude-security-guidance-bare-exec/security_reminder_hook.patch

# 3. Confirm
python3 /Users/kimhawk/orca/skills/docs/patches/claude-security-guidance-bare-exec/verify.py
```

## Which copy is live

Three identical copies ship on disk. Only the **cache** one is executed —
`~/.claude/plugins/installed_plugins.json` maps `security-guidance@claude-plugins-official`
to `…/plugins/cache/claude-plugins-official/security-guidance/unknown`.

The two under `plugins/marketplaces/…` are deliberately left **unpatched**, so after this
patch the three copies differ by md5. If Claude Code ever starts executing a marketplace
copy instead, `verify.py` would still report OK while the live behaviour reverted — check
`installed_plugins.json` first if the false positive ever reappears despite a green verify.

## Verification evidence (2026-08-09)

- `verify.py` red-green: **12/12** against the patched hook; against the pristine original,
  5 failures — the 4 false positives, plus `bare-exec-space` proving the old rule's false
  negative.
- Every other rule still fires (`eval_injection`, `.innerHTML =`, `new Function` pinned in
  the same run).
- Recovery procedure tested: reverting made `verify.py` exit 1, `patch -p1` applied cleanly,
  result **byte-identical** to the patched file, and `py_compile` clean.
- Observed live during this work: the hook blocked an edit once, then allowed the identical
  retry — confirming the one-shot session behaviour described above.
