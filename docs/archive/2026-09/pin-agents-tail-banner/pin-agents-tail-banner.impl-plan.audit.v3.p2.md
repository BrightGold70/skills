## Summary
The implementation plan is extremely thorough and accurately maps the design into concrete code modifications, integrating all necessary steps while addressing previous missing design elements. However, it contains a critical flaw in its mutation testing strategy where a specific mutant will survive its assigned test, and the regex used to ban `timeout` is fragile and bypassable.

## Must-fix
- **Mutation `local-masks-helper-rc` will survive its assigned test (AC-3.11)** — The mutant masks `_orca_tail_sig`'s non-zero exit, entering the `then` block with `tout=""`. Because an empty string fails `grep -Eiq "$tail_re"`, the block hits `|| continue` and declines anyway — making the mutant's outcome indistinguishable from the correct code (which skips the block entirely). To kill it, `test_tail_pass_all_unreadable_declines` must make an empty string match (e.g. by stubbing `_agent_pv_re` to `^$` during the test) so the mutant wrongly resolves the unreadable pane while the correct code declines.
- **The `timeout` invocation regex in AC-2.7 re-derives shell command positions and introduces a bypass** — By restricting the preceding character to `(?:^|[;|&(]|\$\()`, the regex `_INVOKE` completely misses commands preceded by shell keywords (`if`, `then`, `else`, `elif`, `do`, `!`, `{`). An implementer writing `if timeout 2 orca ...; then` will silently bypass the guard. To fix this without hitting `--timeout` or `local timeout=600`, use a negative lookbehind for hyphen and alphanumeric characters, and require a trailing space: `r"(?<![-a-zA-Z0-9_])g?timeout\s"`.

## Should-fix
- **AC-4.4 is weakly specified and risks vacuous passing** — It requires two candidates that "each carry the rival's signature" to prove rejection happens before counting. If those candidates carry *only* the rival's signature, they will fail the preceding `$tail_re` match and never reach the count anyway — so the test would pass even if rival rejection were incorrectly placed after counting. Explicitly state that these two decoy candidates must carry BOTH signatures to actually exercise the pre-count placement.

## Nit
None
