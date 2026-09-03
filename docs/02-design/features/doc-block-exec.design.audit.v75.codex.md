## Summary
The design is otherwise aligned with the specification and covers the scanner, execution, cleanup, stream, timeout, and wiring requirements. Its AC-2.8 handling has one hard contradiction: the empty-key example and its mutation/test require an unquoted dynamic field despite the design's universal JSON-quoted field grammar.

| Spec acceptance criteria | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7 | implemented-as-written |
| AC-2.8 | restated |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- AC-2.8 is internally inconsistent with the universal verdict-field grammar — the spec form is `DOCBLOCK: BAD_SUBST arg="<raw>"`, while the design says `--subst =V` prints `arg==V` and makes `test_subst_empty_key_is_bad_subst` assert that spelling; elsewhere the same design requires every dynamic field to be a JSON-quoted string and defines no bare `arg=` exemption. `arg==V` cannot satisfy that grammar or preserve a raw value beginning with `=` unambiguously. Choose and state one contract (under the declared field grammar, it should be `arg="=V"`; the delegated API form for `""` should likewise be quoted), then update the mutation narrative and test expectation. This is a required explicit reconciliation: the design's special-case form narrows/restates AC-2.8 and undermines the one-line machine-parseable verdict invariant.

## Should-fix
None

## Nit
None
