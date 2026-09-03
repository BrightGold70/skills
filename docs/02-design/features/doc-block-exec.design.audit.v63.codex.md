## Summary
The design is unusually complete, but its heading-address semantics contain a material internal contradiction that can select a different document section. Axis C classification (against the supplied source spec): every AC is implemented-as-written except that AC-1.5/AC-1.7 cannot be considered deterministically implemented until that contradiction is resolved.

| Spec AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | restated: the spec selects a heading by its text and level; the design simultaneously says the source line must equal the requested full form (apart from trailing whitespace) and that closing hashes are stripped before comparison. |
| AC-1.6 | implemented-as-written |
| AC-1.7 | restated: duplicate matching inherits the unresolved full-heading comparison rule from AC-1.5. |
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
- Resolve and pin full-heading equality in `find_heading` — the design first requires a source heading line “equal to `heading` (exact match, stripped of trailing whitespace),” but then says a full `## Text` request compares normalized text after optional closing hashes are stripped. Thus `## Text ##` both must not match and must match `## Text`; this controls section selection and duplicate detection, so it can silently execute/refuse the wrong section. Choose one rule, state it in the design and spec if it narrows AC-1.5/1.7, and add a discriminating `## Text` versus `## Text ##` test.

## Should-fix
- The paired plan’s compact `run_block` API table lists `LaunchFailed` only for “mkdtemp/chmod, spawn, reap,” while the design and spec also require the `collect` stage — include `collect` there to keep the caller-facing contract cross-document consistent.

## Nit
None
