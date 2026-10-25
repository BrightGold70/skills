# bkit G-001 — bare-tag heredoc bodies are not inert

**Status:** APPLIED locally to bkit `2.1.40` on 2026-10-25 (Hawui-Macmini). This patch only makes
the guard stricter.
**Upstream:** [ww-w-ai/bkit-claude-code#161](https://github.com/ww-w-ai/bkit-claude-code/issues/161),
filed 2026-10-25. See `UPSTREAM-FOLLOWUP.md`.
**Target file:** `~/.claude/plugins/cache/bkit-marketplace/bkit/<version>/lib/control/destructive-detector.js`
**Supersedes:** the 2026-10-24 handoff's "G-001 heredoc-body false positive" item. That item was
reported against `2.1.38` on the other Mac and is **already fixed upstream in 2.1.40**:
`stripHeredocBodies()` elides heredoc bodies before matching.

## What the investigation found (2026-10-25, bkit 2.1.40)

| case | 2.1.40 | after this patch |
|---|---|---|
| quoted `<<'EOF'` body names the rmtree token (the handoff's bug) | clean | clean |
| bare `<<EOF` body, plain prose naming a delete | clean | clean |
| bare `<<EOF` body, `$(rm -rf ~)` / backtick / `$(python3 -c …rmtree…)` | **clean — ALLOWED** | G-001, hook `ask` |
| quoted `<<'EOF'` body, `$(rm -rf ~)` (inert) | clean | clean |
| scoped `rm -rf <scratchpad path>`, alone or in a `&&` chain | G-001 high → **ask** | unchanged |
| `git commit -m` / `echo` / `python3 -c` string naming the rmtree token | G-001 critical → deny | unchanged |

- **The false negative (row 3) is why this patch exists.** Upstream's fix strips every heredoc
  body, but only a quoted tag disables expansion. With a bare tag, bash runs `$()` and backticks in
  the body. `heredoc-detector.js` gives only a `lone-heredoc` *warning*, which
  `unified-bash-pre.js:513-514` allows with an audit entry. So nothing blocked it. Proven through
  the real hook script: allow on the original, ask on the patched file.
- **Row 5 is not a bug.** It is the v2.1.34 D9 grading: a scoped delete asks, a broad one denies.
  The handoff's "G-001 fires on rm -rf in a compound command" was this ask, not a deny.
- **Row 6 is accepted and not loosened.** A quoted string that names the token cannot be told
  apart from real code (`python3 -c "…"`). For commit messages, use `git commit -F <file>`.
- **Unpatched, reported upstream:** a broad delete inside `$()` grades `high`/`ask` rather than
  `critical`/`deny`. `deleteTargetIsBroad()` reads `~)` as one operand. This is independent of
  heredocs.

## The fix

`findHeredocDelimiter()` now returns `{ delimiter, quoted }`. In a bare-tag body,
`stripHeredocBodies()` keeps any line containing `$(` or a backtick. Everything else is still
elided as before, so upstream's false-positive fix keeps working. 53 lines in
`destructive-detector.patch`.

## Re-applying after a bkit update

```bash
# 1. Did the update drop the patch, or did upstream fix it?
node docs/patches/bkit-g001-bare-heredoc-substitution/verify.js
#    exit 1 + "patch MISSING"  => re-apply
#    exit 0 + "patch MISSING"  => upstream fixed it: do NOT re-apply

# 2. Re-apply (adjust <version>)
cd ~/.claude/plugins/cache/bkit-marketplace/bkit/<version>
patch -p1 --dry-run < /Users/kimhawk/orca/skills/docs/patches/bkit-g001-bare-heredoc-substitution/destructive-detector.patch
patch -p1           < /Users/kimhawk/orca/skills/docs/patches/bkit-g001-bare-heredoc-substitution/destructive-detector.patch

# 3. Confirm
node /Users/kimhawk/orca/skills/docs/patches/bkit-g001-bare-heredoc-substitution/verify.js
node test/unit/destructive-detector.test.js && node test/regression/destructive-bypass.test.js \
  && node tests/qa/v2114-defense-heredoc.test.js
```

**Each Mac needs it separately.** The plugin cache is machine-local. The other Mac was on `2.1.38`:
update bkit there first, then apply.

## Verification evidence (2026-10-25)

- bkit's own suites, before and after the patch: unit **20/20**, regression **32/32**, QA heredoc
  **53/53**. No test changed.
- `verify.js` red-green: patched → exit 0 (9/11, 2 known gaps); original → exit 1 (the 3 bare-body
  cases fail); re-applied with `patch -p1` → **byte-identical** to the patched file.
- End-to-end through `scripts/unified-bash-pre.js`, fed a PreToolUse payload with nothing
  executed: bare `$()` delete → allow on the original, `ask` on the patched file. Quoted-body
  `$()` and bare-body prose → allow on both.
- sha256 prefixes: original `a27278dcc8938e36`, patched `a19e24ac606adbad`.
