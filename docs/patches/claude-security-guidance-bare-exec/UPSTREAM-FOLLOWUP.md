# Draft follow-up comment for claude-plugins-official#5085 — NOT POSTED

Target: https://github.com/anthropics/claude-plugins-official/issues/5085 (closed, fixed in 2.0.0)
Status: draft, for the user to post (or not). Written 2026-10-18 against security-guidance 2.0.14.

---

Thanks, 2.0.x fixes all four false positives from the report, and I've dropped my local patch.

One small detection gap remains. The `child_process_exec` regex is `(?<![a-zA-Z0-9_\.])exec\(`,
so a bare call with whitespace before the paren isn't flagged in a `.js` file:

```js
exec ('ls -la');          // 2.0.14: no match
```

This was also missed before 2.0 (the old `"exec("` substring had the same blind spot), so it isn't
a regression. The patch I attached to the original report used `exec\s*\(` for this reason. Changing
the regex to `(?<![a-zA-Z0-9_\.])exec\s*\(` would catch it without bringing back any of the method-call
false positives, since the lookbehind still rejects `re.exec (`.
