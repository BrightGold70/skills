# Upstream report — FILED

**Filed 2026-08-09:** https://github.com/popup-studio-ai/bkit-claude-code/issues/145

Target: `popup-studio-ai/bkit-claude-code`. The posted issue inlines the diff and the
suggested tests (the attached-patch reference below does not exist for them), and omits all
local paths. Text below is the source draft.

If upstream ships the fix, drop the local patch rather than re-applying it — `verify.js`
returning exit 0 with the patch symbol **MISSING** is exactly that signal.

---

## Title

ENH-310 heredoc guard: quoted-tag heredoc bodies are inert but still denied (false positive)

## Summary

`lib/defense/heredoc-detector.js` matches its `sub`-vector patterns against the raw command
string. Because it has no notion of quoting, a command whose *heredoc body* merely contains
the text `$(cmd <<TAG … TAG)` is denied as `critical`, even though bash will never expand it.

This bites hardest when writing docs, tests, commit messages, or notes **about this guard** —
which is how we hit it. Notably, `tests/qa/v2114-defense-heredoc.test.js:41` already works
around the same underlying issue by constructing `<<` as `'<' + '<'`.

## Reproduction

```js
const { detect } = require('./lib/defense/heredoc-detector');

// A quoted-tag heredoc whose body is a Python string that mentions the pattern.
const cmd = [
  "python3 - <<'PY'",
  `s = "$(cat <<'EOF' ... EOF)"`,
  'PY',
].join('\n');

detect(cmd).severity;  // => 'critical'   (expected: not critical)
```

## Why it is a false positive

A **quoted** heredoc tag (`<<'TAG'` / `<<"TAG"`) disables all expansion in the body. That is
a bash language guarantee, not a heuristic. Verified:

```
$ cat <<'PY'
value = "$(echo INJECTED)"
PY
value = "$(echo INJECTED)"        # literal — no expansion

$ cat <<PY
value = "$(echo INJECTED)"
PY
value = "INJECTED"                # bare tag — expansion happens
```

The same holds when the body contains a terminator-lookalike line (`  PY_NOT_REALLY`).

So text inside a quoted-tag body cannot become shell syntax, and a `$(cmd <<TAG …)`
sequence appearing there is prose, not a substitution.

## Proposed fix

Excise quoted-tag heredoc **bodies** before evaluating `sub`-vector patterns, preserving the
heredoc markers. Patch attached as `heredoc-detector.patch`; the essential change is:

```js
const subScanText = stripQuotedHeredocBodies(stripped);

for (const p of CRITICAL_PATTERNS) {
  if (p.re.test(p.vector === 'sub' ? subScanText : stripped)) {
```

The exemption is scoped deliberately narrowly, so it **narrows** the guard rather than
loosening it:

- Only the `sub` vector uses the reduced text. `pipe-shell` / `eval-source` / `sudo` keep
  scanning the full string, because a quoted-tag body piped to a shell *is* executed
  verbatim — CR-22 and CR-23 stay correct and stay passing.
- Bare-tag bodies are never excised (`$()` in those bodies does expand).
- Markers survive, so a genuine `$(cat <<'EOF' … EOF)` remains `critical`.
- An unterminated heredoc leaves the text untouched (fail safe).

## Test evidence

Existing suite unchanged and passing: **53/53 → 62/62** with 9 added cases. A differential
corpus of 23 commands (original vs patched) shows **0 unintended regressions** and exactly 2
intended relaxations, both the verified inert-body class.

Suggested additions (they fail without the patch, pass with it):

```js
test('QH-01: prose about $(cmd <<TAG) inside quoted-tag body → not critical', () => {
  const cmd = `python3 - ${HD}'PY'\ns = "${DLR}(cat ${HD}'EOF' ... EOF)"\nPY`;
  assert.notEqual(detect(cmd).severity, 'critical');
});

test('QH-03: GENUINE $(cat <<TAG …) with quoted tag → still critical', () => {
  const cmd = `git commit -m "${DLR}(cat ${HD}'EOF'\nbody\nEOF\n)"`;
  assert.equal(detect(cmd).severity, 'critical');
});

test('QH-04: BARE outer tag wrapping quoted inner → still critical (bare expands)', () => {
  const cmd = `cat ${HD}OUTER\n${DLR}(cat ${HD}'IN'\nx\nIN\n)\nOUTER`;
  assert.equal(detect(cmd).severity, 'critical');
});

test('QH-05: quoted-tag body piped to bash → still critical (body is executed)', () => {
  const cmd = `python3 - ${HD}'PY' | bash\nprint('rm -rf /')\nPY`;
  assert.equal(detect(cmd).severity, 'critical');
});
```

## Not a bug — for the record

`echo "do not use $(cat <<TAG … TAG) in commits"` is correctly denied. `$()` **is** active
inside double quotes, so that command genuinely asks bash to run the substitution. We
initially misfiled this as a second false positive; it is the guard working.

## Environment

- bkit `2.1.19` (marketplace `popup-studio-ai/bkit-claude-code`)
- macOS (Darwin 25.5.0), bash 3.2 / node 22+
