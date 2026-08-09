# bkit ENH-310 — quoted-tag heredoc bodies are inert

**Status:** applied locally to bkit `2.1.19` on 2026-08-09. Not yet reported upstream.
**Upstream:** `popup-studio-ai/bkit-claude-code`
**Target file:** `~/.claude/plugins/cache/bkit-marketplace/bkit/<version>/lib/defense/heredoc-detector.js`

## Why this directory exists

The patch lives in a **version-pinned plugin cache**
(`~/.claude/plugins/cache/bkit-marketplace/bkit/2.1.19/`). A bkit update installs a new
version directory and the patch is gone — silently. This directory holds everything needed
to detect that and re-apply.

`bkit-marketplace` currently has `"autoUpdate": false` in
`~/.claude/plugins/known_marketplaces.json`, so the loss can only happen on a *manual*
plugin update — but it will happen without warning when it does.

## The problem

ENH-310's `heredoc-detector.js` scans the raw command string with regexes. It has no notion
of quoting, so text that merely *mentions* the forbidden pattern is denied as if it were the
pattern. Concretely, this was denied:

```
python3 - <<'PY'
s = "$(cat <<'EOF' ... EOF)"     # <- inert prose, inside a quoted-tag heredoc
PY
```

It bites hardest when writing documentation, tests, or learnings *about the guard itself* —
which is exactly what triggered its discovery. bkit's own test suite works around it by
building `<<` via string concatenation (`const HD = '<' + '<'`, `tests/qa/v2114-defense-heredoc.test.js:41`),
which is evidence the literal-text problem was already felt internally.

## The fix

`stripQuotedHeredocBodies()` excises the **bodies** of quoted-tag heredocs (`<<'TAG'` /
`<<"TAG"`) before the `sub`-vector patterns run, keeping the heredoc markers intact.

The justification is a bash language guarantee, not heuristic quote-parsing: **a quoted tag
disables all expansion in the body.** Verified empirically —

| heredoc | body contains | bash prints |
|---|---|---|
| `<<'PY'` | `$(echo INJECTED)` | `$(echo INJECTED)` — literal |
| `<<'PY'` + terminator-lookalike line | `$(echo INJECTED)` | `$(echo INJECTED)` — literal |
| `<<PY` (bare) | `$(echo INJECTED)` | `INJECTED` — **expanded** |

So the exemption cannot hide a real substitution. It is scoped deliberately narrowly:

- **Only the `sub` vector** consults the reduced text.
- `pipe-shell` / `eval-source` / `sudo` still scan the **full** command string, because a
  quoted-tag body piped to a shell *is* executed verbatim even though it is never expanded
  (bkit's own CR-22/CR-23 cover this).
- **Bare-tag bodies are never excised**, since `$()` in those bodies does expand.
- Markers survive, so a genuine `$(cat <<'EOF' … EOF)` still matches critically.
- Unterminated heredoc → text left untouched (fail safe).

## Re-applying after a bkit update

```bash
# 1. Did the update drop the patch?
node docs/patches/bkit-enh310-quoted-heredoc-body/verify.js   # exit 1 => re-apply

# 2. Re-apply (adjust <version> to the newly installed one)
cd ~/.claude/plugins/cache/bkit-marketplace/bkit/<version>
patch -p1 --dry-run < /Users/kimhawk/orca/skills/docs/patches/bkit-enh310-quoted-heredoc-body/heredoc-detector.patch
patch -p1           < /Users/kimhawk/orca/skills/docs/patches/bkit-enh310-quoted-heredoc-body/heredoc-detector.patch

# 3. Confirm
node /Users/kimhawk/orca/skills/docs/patches/bkit-enh310-quoted-heredoc-body/verify.js
cd ~/.claude/plugins/cache/bkit-marketplace/bkit/<version> && node tests/qa/v2114-defense-heredoc.test.js
```

If the patch no longer applies cleanly, check whether upstream fixed it themselves before
forcing it — `verify.js` returning exit 0 with the patch symbol **MISSING** would mean
exactly that, and the local patch should then be dropped rather than re-applied.

**The 9 `QH-*` tests do not survive an update.** They were added to bkit's own
`tests/qa/v2114-defense-heredoc.test.js`, which lives in the same version-pinned cache and is
replaced wholesale. `verify.js` is the durable check and covers the same behaviour, which is
why it asserts absolute expectations rather than diffing against a saved original. The `QH-*`
sources are preserved in `UPSTREAM-REPORT.md` if you want to re-add them.

*Recovery procedure tested 2026-08-09*: reverting the lib file made `verify.js` exit 1, the
`patch -p1` above applied cleanly, and the result was **byte-identical** to the original
patched file.

## Verification evidence (2026-08-09)

- bkit's own suite: **53/53 → 62/62** with 9 added `QH-*` tests. No pre-existing test changed.
- Differential adversarial corpus (23 cases, original vs patched): **0 unintended
  regressions**, exactly 2 intended relaxations — both the same empirically-verified
  inert-body class.
- Red-green: with the patch reverted, `QH-01`, `QH-02`, `QH-08`, `QH-09` fail; restored, all pass.
- `verify.js` red-green: exits 1 against the unpatched module, 0 against the patched one.
- End-to-end through the live hook: the previously-denied command now runs, and a genuine
  `$(cat <<'EOF' … EOF)` is **still denied**.

## Known remaining false positive (accepted, not a bug)

Pipe-to-shell *text* inside a quoted body — e.g. `x = 'evil | bash'` — is still denied
(`QH-06` pins this). That is the conservative choice: the `pipe-shell` vector deliberately
keeps scanning the full string. Rare in practice compared to the `$()` case.
