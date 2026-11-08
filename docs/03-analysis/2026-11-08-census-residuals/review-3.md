# Change review — working tree vs cdd36a6f (census-r3.diff, round 3) — GATING

## Evidence
- read: 2 files. I read the r3 diff's code hunks (`Entry`, the `census()` pre-check, the `_census_added` call and signature) and the new mutation row in `guard_census.json`. I also ran a consumer grep over `h-mad`, `handoff` and `git-hooks`.
- ran: 7 commands.
  - The N-window repro: 10 CLI runs at N = 2960, 2975, 2977-2981, 2984, 2985, 2990.
  - Real ranges with `/usr/bin/time -l`, new vs HEAD code: `--base` HEAD~50, HEAD~600 and 3d9af666 (root).
  - A reason-precedence probe.
- tests run: `h-mad/tests/test_h_mad_guard_census.py` (whole file, on a scratch tree byte-identical to the working tree), result `136 passed, 4 skipped`. I did not run the mutation harness.

## Round-2 finding
- **Must-fix (two parses at different depths): closed.**
  - On the r2 code, N=2978-2980 gave `UNREADABLE reason=unreadable-file`.
  - On the r3 code, N=2978/2979/2980 give `DONE decision=1` (measured), and N≥2981 give `UNMEASURED: run.conf … DONE`. No run in the scan ended UNREADABLE or crashed.
  - The boundary is now one parse deciding both questions. That is the claim, and it holds by construction: `_census_added` re-parses only when `decisions is None`.
- **Should-fix (the comment over-claimed): closed.** The comment now describes the reuse.

## Stale or second-parse paths
I checked each of these and found none:
- **Reset with stale decisions kept:** cannot happen. The reset line sets `h_kind, h_text, h_decisions = None, "", None` together.
- **A head with no decisions:** `[]` is not `None`, so a parse that yields zero decisions is reused, not re-parsed.
- **Head text changing after the parse:** it cannot. `h_text` is not reassigned between the parse and `_census_added`, so the stored offsets match the text they index.
- **`_census_added` re-parsing a head:** it is called only with `e.h_kind`, and every py head with `h_kind` set carries non-`None` decisions. Its fallback parse is therefore unreachable from `census()`.
- **The base side:** it is still parsed separately in `_census_removed`, as at HEAD. A failure there goes to `UNPARSED-BASE` as before, with no regression.
- **Real history:** output is byte-identical to HEAD code (`cmp` IDENTICAL) on all three ranges, e.g. root `decision=28991 anchored=2798 unanchored=26193 removed=4634`.
- **Cost of holding every head's decisions:** max RSS went from 141 to 149 MB on the root range (+6%); wall time was 6.3 s vs 6.5 s.

## Must-fix
None

## Should-fix
None

## Nit
- **A broken real `.py` now fails before the specs are read, so the UNREADABLE reason can change when two faults coincide.** The parse moved from the second loop into the first, ahead of `_anchor_spans`. Executed: a head with an unparsable `a.py` and an unparsable `keep.json` spec gives `UNREADABLE reason=unreadable-file` (r3) instead of `reason=spec-unreadable` (HEAD). Both are fail-closed with exit 2. The grep found no code consumer of the reason outside the script and its tests, only `SKILL.md` and `helper-scripts.md`. Mention it only if a reason precedence is meant to be documented.
