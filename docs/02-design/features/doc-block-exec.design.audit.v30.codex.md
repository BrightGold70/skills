## Summary

Axis C reconciliation is below; AC-3.8 is `restated`, while every other acceptance criterion is implemented as written.

| Acceptance criteria | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7 | implemented-as-written |
| AC-3.8 | restated |
| AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

The restatement weakens the promised post-write verification and leaves its decode-error path outside the stated verdict mapping.

## Must-fix

- AC-3.8 is narrowed from the spec's “after the close each requested artifact is **read back and compared byte-for-byte to the stream text**” to the design's “`Path(path).read_text(encoding=\"utf-8\")` and compares it to the stream text.” — text decoding plus `str` comparison is not byte-for-byte verification; malformed or changed bytes can instead raise `UnicodeDecodeError`, for which the concrete read-back path specifies no `StreamWriteFailed` mapping. Use `read_bytes()` and compare with the exact UTF-8 bytes written (mapping read/compare failures to `UNREADABLE reason=stream_write_failed`), or explicitly amend the spec before implementation. This is an Axis C `restated` AC and a mutation-verification gap.

## Should-fix

- Define `fence_aware_end` when `start` lies inside an already-open fence, or state and enforce a precondition that it never does. — `section_from` is documented as taking an arbitrary offset, but the proposed scanner is described as starting its fence state at `start`; without prefix state it can mistake a fenced `#` after that offset for a section boundary. Add a direct hostile test for the chosen contract.

## Nit

None
