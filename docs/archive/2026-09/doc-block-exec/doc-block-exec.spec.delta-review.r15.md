# doc-block-exec.spec.md — delta review r15 (advisory, not a gate)

Subject: `git show 00b961f -- docs/01-plan/features/doc-block-exec.spec.md` (v1.60 → v1.61,
12 hunks). Tree read at HEAD `dfae038`; the four documents are byte-identical to `00b961f`.

## Summary

The `pgid` class is genuinely closed and every published figure reproduced: the seven bare
verdict-line fields match the impl-plan's seven exactly, FR-4's eleven detail keys match the
`DETAIL_KEYS` tuple at impl-plan.md:2434 member-for-member, and I re-ran the awk needle (1),
git-grep-n needle (1), opener census (21 over 11 tokens, `sed` ×2 the one change from `6f0ee85`),
no-token scale (75 at `6f0ee85`, 85 over the draft), reproduced-output lines (8), AC-1.2 anchor (1),
the invariants needle (1), the class-closure enumeration (110), all nine control strings at
`grep -cF` 1 with the Version History and control block cut, and the six MATCH / three NO MATCH
verdicts under the pattern extracted by its own anchored needle — all reproduce byte-for-byte. The
round's hunted class is nevertheless where the damage is: the revision restamped nine `v1.60
draft` → `v1.61 draft` sites and left **twelve body-scoped `this revision` phrases untouched**, eight
of which now describe v1.60, including the sentence naming this revision's freeze sha and one that
directly contradicts the v1.61 Version History entry. Two further musts are cross-document: a figure
the plan retires and I measured wrong at HEAD, and an "owed elsewhere" claim the same commit
falsified. Hunks 3–8, 10 and 11 map to **none** of the six routed reports — they are the author's own
decision-K restamp maintenance, and every figure in them reproduces. The two precheck-flagged paths
(`h-mad/tests/test_h_mad_doc_block_exec.py`, `h-mad/scripts/h_mad_doc_block_exec.py`) are the
feature's own unbuilt artifacts and are not filed.
Evidence: 8 files opened, 52 greps run.

## Must-fix

- **The `this revision` class was never swept, and one member contradicts this revision's own
  Version History.** Twelve body-scoped occurrences, identical count at `b3be433` and at HEAD, so
  none was re-examined while nine sibling stamps moved. Eight now mean v1.60: `:734` and `:735-736`
  (freeze sha), `:799`, `:812`, `:864`, `:878`, `:957`, `:1015`, `:1042`. The two sharpest: (a)
  `:735-736` calls `6f0ee85` "this revision's freeze sha" when v1.61's freeze is `b3be433` (its own
  entry says so, and `b3be433` occurs **0** times in the body) — I re-ran the closure at the real
  freeze, `git diff --name-only 74e126f b3be433 | grep -vc '^docs/'` → `0` and the `*.py` form prints
  nothing, so this is a wrong stamp, not a broken claim; (b) `:812` asserts this revision added the
  second `sed` command while the v1.61 entry asserts the opposite in the same commit. Prescription:
  per-site, never a blanket sweep — restamp only the four `6f0ee85` sites that assert a *current*
  state (`:735`, the `:740-741` closure range, the `:745` `git log` range, and the `:757` pair rule's
  committed half) to `b3be433` with the closure re-run, and rewrite the eight `this revision`
  phrases to `v1.60` where the event was v1.60's. The remaining twenty-one `6f0ee85` hits are
  legitimate historical stamps ("the commit that shipped v1.59: 20 openers") and must not move.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `revision's freeze sha, because every intervening commit touches only `docs/``
  quote: docs/01-plan/features/doc-block-exec.spec.md › ``sed` ×2, because this revision adds a second `sed` command to the `path:line` shape-grep block`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `unchanged because this revision adds no fenced command`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `it happened while this revision was drafted, when the v1.60 entry quoted the sixth positive and`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `and is the control on this revision's widening of the closing noun alternation: under the v1.59`

- **`:583`'s AC-6.4 gate-command comment publishes `2486` for the `h-mad/` collected count; the true
  value at HEAD is `2547`.** I measured it rather than inheriting the claim:
  `cd h-mad && python3.11 -m pytest --collect-only -q -p no:cacheprovider | tail -1` → `2547 tests
  collected`, and from the repository root `2809`. The plan's body already retires the figure
  (`plan.md:3085-3086`, "it does not reproduce"), the impl-plan already publishes the drift
  (`impl-plan.md:3219`, "`2486 → 2547`, both `+61`"), and `plan.audit.v85.teammate` routed the
  prescription — strike or sha-stamp — at this document. It was not applied and the v1.61 entry does
  not record it as deferred. This also falsifies the commit message's headline: a published figure
  in one of the four documents *is* wrong. Checked and **not** filed as a second defect: the `2748`
  in the same comment is stamped at `e8eaf6f` at `:538` and is an explicitly stale-tolerant floor
  re-measured at 5c, so it is defensible where `2486` is not.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `from h-mad/ the same command collects 2486`

- **The v1.61 entry's `OWED ELSEWHERE` item was false the moment it was committed** — `00b961f`
  itself repaired the design row it says was "reported and NOT edited". At `b3be433` the design's
  AC-4.6 row read ``cwd gone, `pgid=` in the detail``; at HEAD the same row reads ``cwd gone,
  `pgid:` in the detail``, and design v1.106's own entry in the same commit records the repair
  ("the design AC-4.6 row spelled the emitted DETAIL line in the constructor form … Repaired").
  A body sweep of the design at HEAD now returns only `pgid=<n>` ×2 and `pgid=None` ×2, all four
  Python constructor kwargs — zero diagnostic bare forms, which is exactly what the entry says still
  stands. A reader routing work from that sentence dispatches a fix for nothing. Prescription: a
  bracketed correction appended to the v1.61 entry per the standing practice, not a rewrite.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `OWED ELSEWHERE, reported and NOT edited: the design's AC-table row for AC-4.6 says 'pgid= in the detail' in its killpg-injection clause`

## Should-fix

- Hunk 1 leaves a dangling antecedent it created. The original ran "…is one quoted value; …stay
  bare); tested with newline-bearing…" as one sentence whose subject was the CLI's rendering rule.
  Nineteen lines of new text now sit between them and the clause reopens as "It is tested with…",
  whose nearest noun phrases are "this grammar", "the registry walk" and "a staleness" — none of
  which is what newline-bearing `--heading`/`--subst`/`--stdout` values test. Prescription: name the
  subject ("The escaping rule is tested with…") or move the new exemption block after the testing
  clause.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `not. It is`

- AC-4.2's exit-0 enumeration omits `BAD_ARGS` while FR-4's own description — the paragraph this
  hunk rewrote — lists it at exit 0, as do the design's verdict table and the impl-plan's
  `VERDICT_TABLE` (`"BAD_ARGS": 0`). AC-4.2 is the AC whose test "enumerates the verdict table and
  asserts the code of every row", so the gap sits in the one AC the partition claim rests on. Routed
  by `plan.audit.v85.teammate` as a should-fix, unaddressed and not recorded as deferred.
  quote: docs/01-plan/features/doc-block-exec.spec.md › ``SUBST_OVERLAP`, `BAD_INFO` and `TIMEOUT` each`
  quote: docs/01-plan/features/doc-block-exec.spec.md › ``BAD_TIMEOUT`, `BAD_ARGS`, `BAD_INFO`, `BAD_SUBST`, `SUBST_MISSING`,`

- The v1.61 entry's derivation clause (b) names ten detail keys as "every detail line in this
  document" and includes `stream`, which was **not** in the document: at `b3be433` the body carried
  nine `<key>: "` spellings (`duplicate_key`, `failed`, `leftover`, `missing_key`, `os_error`,
  `overlap`, `skipped`, `verify`, `written`) and `grep -c 'stream:'` over the body returned `0`. At
  HEAD `stream:` appears exactly once, inside FR-4's new enumeration — so the evidence list is true
  only of text the same edit introduced. The derivation still holds on the other nine; the evidence
  sentence overstates its scope by one.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `os_error, missing_key, duplicate_key, overlap, leftover, verify, written, failed, skipped, stream`

- Hunk 2 introduces `fields` as a counted noun over one of this document's own surfaces, and the
  class-closure screen returns NO MATCH on it — I ran the shipped `$RULE` against the string to
  confirm. **This is not a false negative**: I read the exclusions and residual (2) covers "counts of
  things that do not exist yet … design-derived, not tree-derived", which is precisely what the
  seven bare fields are (design v1.80). But residual (1) names the concrete un-counted nouns this
  document uses — `commits`, `tokens`, `values` — and `fields` now belongs in that list, or the
  sentence at `:399` should cite exclusion (2). v1.60 discharged this same obligation by adding
  `lines?` and `pins?`; v1.61 did not discharge it for `fields`.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `one of the seven bare verdict-line fields FR-4 closes, and it is emitted on a *detail* line,`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `and `values` are the concrete ones this document uses in passing without measuring.`

- FR-4 names `DETAIL_KEYS` as "the authority a reader checks the list against rather than this
  sentence", in the present tense, but this document gives it no address and its own AC-4.5 does not
  mention it — AC-4.5 names only the `h-mad/SKILL.md` registry. The tuple is defined at
  `impl-plan.md:2434`, a document the spec never cites here. The dispatch asked whether the spec is
  honest about not-yet-built artifacts: this is the one place it is not, because it points at a
  symbol as an existing authority without saying where it lives or that it does not exist until
  5d/5e. Prescription: name the impl-plan as the definition site, or say "will expose".
  quote: docs/01-plan/features/doc-block-exec.spec.md › `exposes as `DETAIL_KEYS` for AC-4.5's registry walk, which is the authority a reader checks the`

- The v1.61 entry says "ONE routed finding". `plan.audit.v85.teammate` routed **three** items at this
  document — must 3 (`pgid`, answered), the `2486` should-fix and the AC-4.2 `BAD_ARGS` should-fix
  (both above, neither answered nor deferred with a reason). The other five reports route nothing
  here; I greped all six for `spec`.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `ONE routed finding and no audit cycle of this document's own`

## Nit

- The v1.61 entry's sweep summary says the only bare-spelled field outside the seven was the AC-4.6
  `pgid`, and lists `heading` and `arg` among the quoted fields. Both also occur **bare** at `:320`,
  in FR-4's own opening parenthetical. This does not violate the grammar — those are field-*name*
  mentions, not verdict-line spellings, and FR-4's exhaustiveness claim is scoped to the verdict
  line — so it is the sweep's summary sentence that is imprecise, not the contract. Worth one clause
  saying the sweep excluded naming mentions.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `every dynamic field (`heading=`, `arg=`, keys, paths, OS-error text) is rendered as a`

- Owed elsewhere, not a spec finding: the design's `pgid`/`verify`/`leftover` triage arm at
  `design.md:2080` lists ten keys in its alternation and omits `duplicate_key`, while `DETAIL_KEYS`
  has eleven. Reported for the design's own leg; I did not pursue it here.
