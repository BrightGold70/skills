## Summary
The design is otherwise internally consistent with the paired plan and covers the source specification, but its claimed CommonMark scanner admits a non-fence as an executable candidate. Axis C reconciliation follows (all listed ACs are implemented-as-written; none is restated or absent).

| Spec AC identifiers | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- The scanner calls its rule “full CommonMark” but never excludes a backtick-fence opener whose info string contains a backtick — CommonMark does not treat ```` ```bash hmad:exec ``` ```` as an opening backtick fence, whereas the specified opener logic accepts it and then yields `BAD_INFO` or an executable tagged candidate. This breaks the opt-in boundary by executing/refusing based on text that is not a Markdown fence; define and test the backtick-info prohibition in `_fence_events` (including a mutation), so this input is inert rather than a candidate.

## Should-fix
None

## Nit
None
