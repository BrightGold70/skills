## Summary
Audit completed for implementation plan v39 (agy surface). Identified one Must-fix defect regarding missing `_mechanism` keys in the mutation specification which violates explicit instructions, and one Should-fix for a code comment in `hmad-dispatch.sh` that becomes stale with the addition of the tail signature pass.

## Must-fix
- **Task 6 missing `_mechanism` documentation**: The plan dictates in AC-6.12 to AC-6.20 that seven specific proof mutations (`stub-branch-swallows-terminal-list`, `stub-branch-ignores-env-var`, `stub-branch-above-capture`, `tail-re-widened-to-launch-line`, `signature-check-not-enforced`, `tail-sig-fabricates-banner-on-failure`, `skill-md-frontmatter-renamed`) plus two SIGPIPE guard mutations (`wanted-check-back-to-pipeline` and `rival-check-back-to-pipeline`) must have a `_mechanism` line that names the node the proof column claims. However, in the `tail_signature_pass.json` code block provided in Task 6, these 9 mutations are completely missing their `_mechanism` keys.

## Should-fix
- **Stale comment in `hmad-dispatch.sh`**: At line 513, the script currently comments "Codex therefore skips Pass 1 entirely and relies on the preview signature or, properly, on a pin/launch." Since this feature adds the tail signature pass (now Pass 3), this comment should be updated to accurately reflect that Codex will also rely on the tail signature.

## Nit
None
