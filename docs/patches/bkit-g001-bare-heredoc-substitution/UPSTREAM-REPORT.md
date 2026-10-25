<!-- Filed as the body of the upstream issue. Title:
     destructive-detector: stripHeredocBodies elides BARE-tag heredoc bodies, so an expanding $() delete is allowed -->

## Summary

`stripHeredocBodies()` (`lib/control/destructive-detector.js`, v2.1.40) removes the body of **every**
heredoc before the G-rules run, whatever the tag's quoting. But only a **quoted** tag (`<<'EOF'`,
`<<"EOF"`) makes the body inert. With a **bare** tag (`<<EOF`), bash runs command substitution
(`$(…)` and backticks) in the body before the program ever reads stdin. So a recursive delete inside
a bare-tag body reaches no rule, and the command is **allowed**.

`lib/defense/heredoc-detector.js` does not catch it either. It reports `lone-heredoc` at
`warning`, and `scripts/unified-bash-pre.js:513-514` treats a warning as allow-with-audit.

This is the converse of #145. That issue was a false positive on inert quoted-tag bodies. The fix
for it is correct for quoted tags, but it also applies to bare tags, where the body is not inert.

## Reproduce (module level — do NOT run these strings in a shell)

```js
const dd = require('./lib/control/destructive-detector.js');
const cmd = 'cat > /tmp/x <<EOF\n$(rm -rf ~)\nEOF';
console.log(dd.detect('Bash', { command: cmd }));
// v2.1.40: { detected: false, rules: [], confidence: 0 }
```

The same command fed through `scripts/unified-bash-pre.js` as a PreToolUse payload produces no
decision (allow). Same result for the backtick form, and for
`$(python3 -c "import shutil; shutil.rmtree('/x')")`.

That bash really expands the body is a language guarantee: `cat <<EOF` with `$(echo INJECTED)` in
the body prints `INJECTED`, while `cat <<'EOF'` prints the literal text.

## Suggested fix (what we run locally)

Have `findHeredocDelimiter()` report whether the tag was quoted. Inside a **bare**-tag body, keep
any line that can carry a substitution (contains `$(` or a backtick). Quoted-tag bodies, and plain
prose in bare-tag bodies, are still elided, so #145's fix keeps working.

```diff
-    if (m) return m[1] || m[2] || m[3];
+    if (m) return { delimiter: m[1] || m[2] || m[3], quoted: !m[3] };
 ...
-      if (found) { delimiter = found; terminated = false; }
+      if (found) { ({ delimiter, quoted } = found); terminated = false; }
 ...
       terminated = true;
+      continue;
     }
+    if (!quoted && (line.includes('$(') || line.includes('`'))) out.push(line);
```

Results with this change:
- `test/unit/destructive-detector.test.js`: 20/20.
- `test/regression/destructive-bypass.test.js`: 32/32.
- `tests/qa/v2114-defense-heredoc.test.js`: 53/53.

The three bare-body cases above now hit G-001. The hook returns `ask` (see the second finding for
why it is not `deny`). Quoted-body cases stay clean.

## Second, smaller finding: a broad delete inside `$()` grades `high`, not `critical`

`deleteTargetIsBroad()` takes operands up to `[\n;|&]`, so in `echo $(rm -rf ~)` the operand is
`~)`, which does not match the broad-target rules. The rule grades the command `high`/`ask` where a
bare `rm -rf ~` grades `critical`/`deny`. This happens without any heredoc. Stripping a trailing `)`
or backtick from each operand would fix it. We have not patched this one locally.

## Not a request

Quoted strings that only *name* `shutil.rmtree` are still denied as critical, for example
`git commit -m "…"` or `echo "…"`. We are **not** asking to loosen that, since `python3 -c "…"` has
the same shape and is real. `git commit -F <file>` is an adequate workaround.
