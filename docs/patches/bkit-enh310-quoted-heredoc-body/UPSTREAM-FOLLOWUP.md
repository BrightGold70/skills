# Draft follow-up comment for bkit#145 — NOT POSTED

Target: https://github.com/popup-studio-ai/bkit-claude-code/issues/145 (closed, fixed in v2.1.34)
Status: draft, for the user to post (or not). Written 2026-10-18 against bkit 2.1.40.

---

Thanks for the fix in v2.1.34. I've dropped my local patch in favour of it. One case from the
original report's verifier still comes back `critical` on 2.1.40: a quoted-tag body containing a
line that only *starts* with the terminator.

```js
const det = require('<bkit>/lib/defense/heredoc-detector.js');
const D = '$';
det.detect(`python3 - <<'PY'\n  PY_NOT_REALLY\n${D}(cat <<EOF\nx\nEOF\n)\nPY`).severity;
// 2.1.40 → 'critical'   expected → not critical
```

bash only ends a heredoc on a line that is exactly the delimiter, so `  PY_NOT_REALLY` does not
close the `<<'PY'` body. Everything up to the final `PY` stays one quoted-tag body, and bash prints
the `$(cat <<EOF …)` in it literally. So this is the same inert-body false positive, reached through
a line that looks like the terminator. My guess is that the body-stripping step matches the
terminator too loosely (by prefix, or after trimming), so it ends the body early and the
`$(cat <<EOF` after it gets scanned as live text. I haven't read the 2.1.40 source to confirm that.

The other 8 cases from the report (including every "must still be critical" one) behave correctly
on 2.1.40.
