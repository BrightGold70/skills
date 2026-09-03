## Summary
The design and implementation plan comprehensively outline a robust, secure, and rigorously tested approach for extracting, substituting, and executing opt-in tagged bash blocks from markdown files. The proposed `h_mad_doc_block_exec` helper ensures complete isolation, proper stream handling, bounding without external commands, and explicit failure reporting. The invariants around execution bounds, mutation verification, and error boundaries are well-managed across both the CLI and API boundaries.

## Must-fix
None

## Should-fix
- The Plan's FR-6 wire tests table describes the `wire-revert-extract` mutation mechanism as using `re.findall(r"```bash[^\n]*\n(.*?)```")` and explicitly calls this "the pre-migration shape". However, the Measurements section and Design confirm the actual pre-migration shape is `re.findall(r"```bash\n(.*?)```")`. If the mutation intentionally accommodates the tag to ensure the connection wire is tested without a regex matching failure, the phrase "the pre-migration shape" should be corrected or clarified to avoid a factual contradiction.

## Nit
None
