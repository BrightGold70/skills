## Summary
The plan and spec are audited for adversarial consistency and invariant compliance. Three must-fix issues were identified, all stemming from the plan and spec drifting out of sync. The plan claims the spec references the plan's fence census for AC-6.1's scope, but the spec explicitly states it defines the sweep inline; the spec carries a stale extractor census control count (21) that the plan has updated to 23; and the spec violates the "Behavioural premises carry their command" invariant by asserting this count without its generating command.

## Must-fix
- Cross-doc contradiction on how AC-6.1 defines its scope — the Plan claims the Spec defines AC-6.1's sweep by reference to the plan's fence census, but the Spec explicitly states it defines the sweep inline and no longer uses the reference.
  quote: # Plan: doc-block-exec › `The spec reaches AC-6.1's scope by reference to this census ("the same sweep as the plan's fence census"), so the distinction has to be stated here or the reference imports the wrong one`
  quote: # Spec: doc-block-exec › `The sweep is stated here rather than by reference: `*.md` files under `h-mad/` and `handoff/`, excluding any `archive/` path and any dot-directory.`
- Cross-doc contradiction on the extractor census control count — the Spec carries the stale 21 measurement, while the Plan updated it to 23 and explicitly notes that 21 was its old value before it drifted.
  quote: # Spec: doc-block-exec › `Control: 21 `.py` files contain a fence literal, so the narrow pattern is not under-matching.`
  quote: # Plan: doc-block-exec › `23 `.py` files contain a fence literal of any language`
- Violation of "Behavioural premises carry their command" invariant — the Spec asserts the extractor census control count without carrying the command that produced it, whereas the Plan correctly includes it.
  quote: # Spec: doc-block-exec › `Control: 21 `.py` files contain a fence literal, so the narrow pattern is not under-matching.`

## Should-fix
None

## Nit
None
