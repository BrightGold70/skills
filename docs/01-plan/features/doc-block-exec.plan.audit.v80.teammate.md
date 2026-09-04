## Summary

I re-derived v1.93's published figures at the freeze sha `8909ec4` (and at `6f0ee85`/`35698f9`
where the document stamps them) and **every one of them reproduces exactly**: screen one returns 9
lines by the v1.92 program and 32 by the v1.93 program over `git show 6f0ee85:<plan>` on
`awk version 20200816`; the 9 is a **strict subset** of the 32, so the 23 is exactly the gap and the
intersection of the five named members with the nine the old screen printed is **empty** — the
load-bearing claim holds. The five triage categories partition the 32 exactly (9+8+5+5+5, and I
reproduced the membership of each), the control fixture returns its four positives and declines
`anything unmeasured`/`remeasured today`, the wrapper probe returns `rc=3` / `rc=124` byte-for-byte,
`--collect-only` returns 2809 from the root and 2547 from `h-mad/`, the opener census is 9/5 at
`35698f9` and 20/11 at `6f0ee85`, and `74e126f` counts 27/10. The three findings below are all
things the revision's *own new rules* reach but its sweeps did not: a boundary repair applied to two
of three sibling branches (Decision I), a hand-swept carve-out population missing a probe the
document itself assigns to the carve-out (Decision J), and a fourth repo-wide `.py` census left at
the stamp the same revision retired for the other three.

Axis C — FR reconciliation against spec v1.60 at `8909ec4`
(`git show 8909ec4:docs/01-plan/features/doc-block-exec.spec.md | grep -nE '^### FR-'`):

| FR | spec heading | plan | classification |
|---|---|---|---|
| FR-1 | Address a block by document, heading, and explicit tag | §Requirements + §Scope + §Deliverables | `implemented-as-written` |
| FR-2 | Substitute an explicit map, and refuse a substitution that would not apply | §Requirements + `substitute` API row | `implemented-as-written` |
| FR-3 | Execute in a disposable cwd under a declared shell mode | §Requirements + §Goals + §Architecture | `implemented-as-written` |
| FR-4 | Verdict-token CLI following the established gate contract | §Requirements + CLI-contract paragraph | `implemented-as-written` |
| FR-5 | Bounded execution without an external time-bounder | §Requirements + `run_block` row + 5f bounds | `implemented-as-written` |
| FR-6 | Migrate the existing inline harness onto the helper | §Requirements + wire table + §Deliverables | `implemented-as-written` |

No `restated` and no `absent` item. The six plan `FR-N` titles are byte-identical to the six spec
`### FR-N` headings.

Evidence: 8 files opened, 64 greps run.

## Must-fix

- **Screen one's third branch is bounded on NEITHER side, so the revision that states Decision I applied it to two of its three sibling branches.** The published program is `/(^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)|[Tt]his session/` (plan body line 707, extracted from the committed body, not retyped). The first two branches carry both-sides POSIX boundaries; `[Tt]his session` carries none, and the document asserts the opposite of its own program. Measured: `printf 'in this sessionless mode\nThis Session capitalised\nxthis session glued\nthis session\n' | awk '<the published program>'` returns `in this sessionless mode`, `xthis session glued` and `this session` — an unbounded match on both the leading and the trailing side — and declines `This Session capitalised`, so the branch is not case-folded past its first character either. This is the third revision in a row in which a boundary repair on this one expression was half-applied (`\b` → `today` only at v1.91; leading anchor only at v1.92; two of three branches at v1.93), which is exactly the class Decision I exists to close. Live impact today is zero and I say so rather than inflate it: `awk '/^## Version History/{exit} /[Tt]his session/ && !/…measured…|…today…/{print NR": "$0}'` over the v1.93 body returns **no** line, so no current hit depends on this branch — it is a residual, not a member. Prescription: write the branch as `(^|[^[:alnum:]_])[Tt]his [Ss]ession([^[:alnum:]_]|$)` and re-run the published control fixture, or drop the bolded claim to what the program actually does.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `Every marker is bounded on both sides and case-folded`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the same both-sides treatment is applied to *every* sibling branch in the expression`

- **The Decision-J carve-out sweep is published as the complete population and omits a probe the document assigns to that carve-out three paragraphs earlier — so the completeness claim is unmeasured.** The table has six rows (argparse `exit_on_error`, AC-5.2 group kill, AC-3.14 `rmtree`, AC-3.10 FIFO, AC-5.5 emptied group, plus the non-exempt wrapper). The awk boundary probe — `awk --version` → `awk version 20200816`, the `\b`-is-a-backspace measurement and the `awk version 20200816` stamp on the 9/32 readings — is an interpreter-behaviour probe carrying an interpreter stamp and **no sha**, and the document explicitly places it under this carve-out, yet it appears in no row. Under Decision G an absence/completeness claim is a measurement, and "five members, all five checked" is falsified by one command: `git ls-files awk` → **0** (so the probe is in fact exempt — the verdict is right, the sweep is not). **Closing the class rather than filing the instance:** the rule over the population is "every probe in this document that is stamped with a version/platform instead of a sha is a row in this table", and the sweep must be driven by the *stamp*, not by recall. A second member falls out of that rule immediately — the Scanner-grammar-corpus probe under §Measurements, stamped `markdown-it-py 2.2.0 (interpreter-local) AND 4.2.0`, `git ls-files markdown_it markdown-it-py` → **0**, also absent from the table — and it additionally strains the narrowed wording, since a third-party renderer is not "the OS, the kernel or the language runtime". Residual after the fix: the rule still cannot be run by a shape filter (the document says so), so the driver is a grep for version/platform stamps and a hand read of each hit.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `with its interpreter under the carve-out below rather than with a repository sha`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**Five members at `6f0ee85`, all five checked with that command**`

- **A fourth repo-wide `.py` census was missed by the sweep that re-stamped the other three, and it sits in the paragraph immediately above the one that states the corpus caveat.** The extractor census's command is `grep -rn 'findall.*```bash\|split.*```bash\|re\.compile.*```bash' --include='*.py' .` — corpus `.`, the whole repository, not the two roots — so the §Measurements closure over `74e126f`→`6f0ee85` does not reach it and its `35698f9` stamp rests on nothing, which is the exact defect the same revision repaired for the 6/24/4 censuses. The very next paragraph says so for the broader grep over the identical corpus and re-stamps it at `6f0ee85`; this one is left at `35698f9` with no corpus statement. Value and recorded output are fine and I checked both: re-run at `8909ec4` with `/usr/bin/grep` it still returns **2**, and the recorded lines reproduce verbatim **including the `./` prefix** (my first run appeared to drop it — that was this session's `grep` shell wrapper, not the document; corrected here so it is not read as a finding). Prescription: re-stamp to the audited commit and carry the same "this corpus is the whole repository, not the two roots" sentence, and drive the sweep off the *command's corpus argument* (`.` / `--include` vs `-- h-mad handoff`) rather than off which numbers an audit named — `git ls-files '*.py' | grep -vcE '^(h-mad|handoff)/'` → **411** at both `6f0ee85` and `8909ec4`, so the gap between the two corpora is not marginal.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**The extractor census — 2, re-run at `35698f9`.**`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**This corpus is the whole repository,`

## Should-fix

- **A self-describing sha label goes false the moment the revision lands, and it has: the opener census names `6f0ee85` as "the commit this revision is audited at", but v1.93 is committed at `8909ec4` and is being audited at `8909ec4`.** The figures themselves are correct where stamped — I re-derived 9 openers / 5 distinct tokens at `35698f9` and 20 / 11 at `6f0ee85`, matching the published distributions token for token — so this is a label defect, not a falsification. At the current freeze sha the census has moved again: `git show 8909ec4:<spec> | grep -oE '^  \$ [a-zA-Z0-9._-]+' | sort | uniq -c` → **21 openers over 11 distinct tokens**, the move being `sed` ×1 → ×2. The load-bearing conclusion survives a third move — `awk` ×1 at all three shas, and `grep -cE '^  \$ awk '` on the spec → 1 at `6f0ee85` and 1 at `8909ec4`, 0 on the design and 0 on the impl-plan — which is the document's own stated reason for separating census from conclusion. Prescription: write the label as "the commit this revision was audited at" or drop it, since a sibling-derived figure can never be stamped at the commit it lands in when all four documents move together.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the commit this revision is audited at: **20 openers** over **11 distinct tokens**`

- **"written from one list so they cannot drift apart" asserts a guarantee nothing enforces, in the paragraph whose sibling defect is exactly that drift.** The rule sentence and the awk program are two independent pieces of prose; no checker binds them, and this revision demonstrates they can diverge in *treatment* (three markers named, two of them boundary-repaired) even while the marker set matches. The document's own method — publish the checker, run the controls — is not applied to this claim. Prescription: state it as a convention with a residual ("the two are maintained together; nothing checks it"), or extract the marker list from the published program the way screen two's rule is extracted from the spec's fenced block.

- **Two figures whose subject is tracked are still stamped at a commit older than the freeze sha, and the closure is stated but not extended to them.** The fence census (73 at `a8e0372`) and the `30 / 35` corpus are `h-mad`/`handoff`-scoped and stamped older than `74e126f`, which the closure paragraph explicitly excludes ("Nor does it reach a figure stamped at a commit *older* than `74e126f`"). That is internally consistent, and I re-ran the census rather than assume: `git grep -c '^```bash' -- 'h-mad/*.md' 'handoff/*.md' ':!*/archive/*' | awk -F: '{s+=$NF} END {print s}'` → **73** at `8909ec4`, unchanged. Worth noting only because the closure now demonstrably reaches `8909ec4` too — `git diff --name-only 74e126f 8909ec4 -- h-mad handoff` prints nothing and the piped form prints `docs` alone — so the interval could be extended in one edit instead of leaving two figures outside it.

## Nit

- "Those three words are the marker set screen one below filters on" — `this session` is two words, so the marker set is three markers across four words. Trivial, but the sentence is the one the program is supposed to be written from.

- The carve-out table's `git ls-files` column carries the *result* ("empty", "two paths") but not the command per row; the command is stated once above the table. Fine as written, but a reader re-running row by row has to scroll up for the subject-to-argument mapping — naming the argument in the Subject cell (e.g. `os.killpg`, `os.setsid` → `git ls-files os` is not what was run) would make each row independently runnable.

- I did not re-run five things and name them rather than let silence read as verification: the `30 / 35` tracked-vs-glob corpus split, the `doc-auditor.md` fence-toggle 8/4 readings, the Setext differential, the markdown-it-py 14-case grammar corpus (it needs a throwaway venv), and the three OS probes (`rmtree` on `0o000`, the reader-less FIFO, the emptied-group `killpg`). None of them changed in this delta; all five remain `unverified` from this pass.
