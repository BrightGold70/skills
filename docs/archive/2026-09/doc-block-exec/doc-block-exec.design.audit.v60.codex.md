## Summary

| Spec ACs | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.8 | implemented-as-written |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

The design covers all 49 source-spec acceptance criteria without an Axis C restatement or absence. One load-bearing ATX-only assumption remains unverified, and the stated preservation of `docsections.titled_section` conflicts with its proposed duplicate-heading behavior.

## Must-fix

- The ATX-only decision relies on the assertion “Every document in these skills is ATX,” but the cited heading-selector differential cannot prove that claim: its old and new selectors both ignore a Setext heading, so Setext usage would not appear in `new_only=0`. Add and cite a direct corpus check for Setext headings (or explicitly carry the limitation as unverified) before relying on it to migrate `docsections`; this breaches the base Assumption verification invariant.

## Should-fix

- The design calls the bare `find_heading(text, "Text")` form used by `docsections.titled_section` “its contract unchanged,” yet it raises `AmbiguousHeading` whenever more than one heading at any level has that text; the current implementation’s `re.search` takes the first match. State this compatibility change and test it, or preserve the old bare-heading selection rule, so callers do not acquire an unannounced new refusal.

## Nit

None
