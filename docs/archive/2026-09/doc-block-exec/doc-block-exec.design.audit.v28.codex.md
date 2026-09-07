## Summary
The design covers the stated feature and its cross-document wire/delegation commitments, but its prescribed substitution algorithm crashes on the normal no-`--subst` path. Axis C reconciliation is below; every listed AC is `implemented-as-written` (no `restated` or `absent` items).

| Acceptance criterion | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-2.8 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-3.14 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- Empty substitution maps are unspecified but the mandated implementation fails on them — `main` explicitly calls `substitute` after optional `--subst` parsing, so the ordinary invocation supplies `{}`; `"|".join(map(re.escape, keys))` is then `""`, and `re.sub("", lambda m: subs[m.group(0)], text)` raises `KeyError("")` instead of producing a `DOCBLOCK:` verdict. Define `substitute(block, {})` as a no-op returning a new/equivalent block and `{}`, short-circuit before compiling the alternation, and add API and zero-`--subst` CLI coverage.

## Should-fix
- Duplicate recognised info-string tokens have no grammar or refusal rule — `hmad:exec shell=strict shell=plain` (and repeated `hmad:exec`) is neither “any other token” nor an invalid `shell=` value, so the parser may silently choose a mode despite the design’s stated rule that a typo/mode nobody chose must not run. Reject duplicates deterministically as `BAD_INFO` or specify an unambiguous duplicate policy and test it.
- The mutation-accounting prose is internally false — the design and paired plan call all 41 `doc_block_exec.json` rows “source mutations of the helper,” while `registry-row-removed` and `detail-line-undocumented` explicitly mutate `h-mad/SKILL.md`. Correct the classification/count wording so the verification matrix accurately states its targets.

## Nit
None

