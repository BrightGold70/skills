# doc-block-exec — round fifteen delta decision sheet (shared facts for the r15 revision batch)

**Status:** ADVISORY input to four parallel authors. Not a gate. Stamps nothing.
**Freeze:** `00b961f`. HEAD is `dfae038`; `git diff 00b961f..HEAD` over the four documents is
**empty** (`df04e8e` and `dfae038` touched only `docs/handoffs/`). The working tree you read IS the
frozen state.
**Delta reports:** `docs/03-analysis/doc-block-exec.{design,plan,impl-plan,spec}.delta-review.r15.md`

## Why this sheet exists

Four authors run in parallel, one document each. Every fact below is **cross-document**: two or
more authors would otherwise each re-derive it, and measured history says they reach different
answers and each document ends internally consistent, so no audit leg can see the disagreement.
These readings are taken once, here, by the orchestrator, with the command that produced them.
**Do not re-derive them to a different value without saying so in your report** — if your run
disagrees with a reading here, that is a finding about this sheet and it outranks the sheet.

The orchestrator is the least reliable surface in this loop: over rounds twelve to fourteen an
author refuted a claim in the decision sheet three rounds running, twice with two authors catching
the same one independently. Treat every line below as a claim to check, not as an instruction.

## Union result

| document | must | should | nit |
|---|---|---|---|
| design v1.106 | 4 | 3 | 1 |
| plan v1.101 | 6 | 3 | 1 |
| impl-plan v1.50 | 3 | 2 | 2 |
| spec v1.61 | 3 | 6 | 2 |
| **union** | **16** | — | — |

Delta-pass must by round: r13 **2** → r14 **6** → r15 **16**. Every must in all four reports is
fix-introduced by round fourteen's own repairs or is prose whose referent moved. Fourth consecutive
delta pass where the musts sit in the paragraph the previous round's must rewrote.

## FACT 1 — round fourteen's headline is FALSE. Seven published figures are wrong.

The r14 gating round concluded "not one published figure was wrong in any of the four documents".
Seven are. Provenance is stated per row, because it differs — rows marked **orch** were re-derived
by the orchestrator in a clean shell, one command per invocation; row 2 is **auditor-derived with
the orchestrator running only its first step**, and is labelled as such rather than passed off as a
full re-run:

| # | prov | site | published | true | command |
|---|---|---|---|---|---|
| 1 | orch | `spec.md:583` | `2486` | **2547** | `cd h-mad && python3.11 -m pytest --collect-only -q -p no:cacheprovider \| tail -1` |
| 2 | auditor | `design.md:3420` | `58` | **60** | see below |
| 3 | orch | `design.md:2093` | "twice more" | **once more** | `git show b3be433:<design> \| grep '^\| AC-4.6' \| grep -oE 'pgid[=:]' \| sort \| uniq -c` → `1 pgid:` `1 pgid=` |
| 4 | orch | `design.md:928` | "`b3be433`→working prints nothing" | **`61c61`** | `diff <(git show b3be433:"$D" \| grep -E "$RAISE") <(grep -E "$RAISE" "$D")`, `RAISE` from `:852` |
| 5 | orch | `design.md:928` | "`700c599`→working: one changed-line hunk" | **two** (`60,61c60,61`) | same command, `700c599` |
| 6 | orch | `impl-plan.md:2407` | "three of the eight sources are globs" | **four** | `sed -n '153,162p' h-mad/tests/test_h_mad_portable_timeout.py \| grep -c '\.glob('` → `4` |
| 7 | orch | `plan.md:110` | "Ten of the eleven" | **Ten of the twelve** | FACT 3 below |

**Row 2, provenance stated exactly.** The chain is the design auditor's: the prose walk raises `62`,
`2` of those sit inside a fence, leaving `60`, of which five are disposed of by name, leaving `55`.
The orchestrator ran **only its first step** and reproduced it —
`awk '/^## Version History$/{exit}{print}' "$D" | grep -ciE '(^|[^[:alnum:]_])(measured|probed)([^[:alnum:]_]|$)'`
→ **62**, matching the `62` the document publishes at `:3395`. The in-fence `2` and the five
named dispositions were **not** re-run here; what the orchestrator checked beyond that is the
arithmetic — `:3409` publishes `60`, `:3418` publishes `55`, and `60 − 5 = 55` while `58 − 5 ≠ 55`.
So `58` is a superseded value standing in a live sentence. **design-author: re-run the in-fence
split yourself before editing** — if it is not `2`, the correct replacement is not `60` and this row
is wrong.

Two further figures, from the plan leg, re-derived and confirmed:

- `plan.md` cardinal-list `≥ 2` check publishes **2** for `the three admissible categories`; the
  joined-grammar count is **1** at `1cbddb7`, `700c599`, `8c6539a` and `b3be433` (all four measured).
  At HEAD it is **4**, so that member's delta is **+3**, not the "+1" the following sentence claims
  for all six.

`8c6539a`→`b3be433` on the raised set genuinely **does** print nothing. Only the two hops in row 4
and row 5 are wrong; do not "fix" the third.

## FACT 2 — the mutual `pgid` OWED-ELSEWHERE debt. THREE authors each recorded a debt the same commit discharged.

This is the round's structural finding and it is the orchestrator's, not any author's — no author
could have seen it, because each read siblings that were being revised concurrently.

At `b3be433`, design's AC-4.6 row and spec's FR-4 policy sentence each spelled the emitted field in
the constructor form. **`00b961f` repaired BOTH, in the same commit**, while:

- **design v1.106** wrote an `OWED ELSEWHERE` saying the *spec* still owes it,
- **spec v1.61** wrote an `OWED ELSEWHERE` saying the *design* still owes it,
- **plan v1.101** wrote that the class "is open across the feature" until *both* repair it.

All three were false the moment they were committed. Readings at HEAD, taken once here:

```
design AC-4.6 row:   2 pgid:   0 bare        (b3be433: 1 pgid:  1 pgid=)
spec  FR-4:          pgid: "<n>"             (b3be433: pgid=<n>, at :378)
spec  body bare pgid=:   0
design body pgid=:       4  — ALL FOUR are Python constructor kwargs
                            (LaunchFailed(..., pgid=<n>) ×2, pgid=None ×2), zero diagnostic forms
```

**The class IS closed at HEAD.** Every author whose document carries a pending-`pgid` claim owes a
correction. Per this feature's practice since round six, a Version History entry takes a **bracketed
appended correction**, never a rewrite; a live body sentence is edited.

**Still genuinely owed, and NOT part of this discharge** — both reproduce at HEAD, so do not sweep
them away with the `pgid` correction: the spec's `2486` at `:583` (FACT 1 row 1) and the absence of
`BAD_ARGS` from spec AC-4.2's exit-0 enumeration at `:367-368`.

## FACT 3 — the `pgid=` census, settled once

Measured at `b3be433`, per document, `grep -c 'pgid='` and how many of those hits are
`LaunchFailed(` constructor calls:

| document | `pgid=` | of which `LaunchFailed(` |
|---|---|---|
| spec | 1 | 0 |
| plan | 0 | 0 |
| design | 5 | 4 |
| impl-plan | 6 | 6 |
| **total** | **12** | **10** |

So the correct phrasing is **"Ten of the twelve"**. `plan.md:110` says "Ten of the eleven", and the
same wrong denominator is carried in the v1.101 Version History entry **and in the `00b961f` commit
message** — three surfaces. The commit message cannot be amended (it is pushed); it takes the
bracketed-correction treatment in the next commit message, exactly as `8c6539a` did.

## FACT 4 — pytest collection counts, settled once

Run each in its **own** shell invocation. Measured at HEAD:

```
repository root:  2809 tests collected
h-mad/         :  2547 tests collected
```

**Orchestrator error, recorded:** I first reported root = `2547`. It was wrong — a `cd h-mad` in an
earlier command of the same `&&`-chained invocation persisted into the second run, so both
"measurements" read `h-mad/`. New instance of the SCOPE species (seventh orchestrator verification
error of this arc): **shell state survives a chained measurement; take each control in its own
invocation.** The auditor's figures were right and mine were not.

`2748`/`2486` are the pre-`b7d0d77` pair. The impl-plan already publishes the drift as
`2748 → 2809` and `2486 → 2547`, both `+61`, at `:3219`; the plan already retires the bare `2486` at
`:3085-3086`. Only the spec still asserts the retired value.

## FACT 5 — a cross-document defect the OWNING document's own leg missed. ROUTED to design.

The spec leg raised this and explicitly did not pursue it ("reported for the design's own leg"). The
design leg **did not find it** — `grep -n 'duplicate_key\|2080'` over
`doc-block-exec.design.delta-review.r15.md` returns nothing. So it has no owner unless routed here,
which is what this section is for.

`design.md:2080`'s triage alternation lists **ten** keys and omits `duplicate_key`:

```
(pgid|verify|leftover|written|failed|skipped|stream|os_error|missing_key|overlap)=
```

`DETAIL_KEYS` at `impl-plan.md:2434-2436` has **eleven**, and its own trailing comment says `# 11`:
`missing_key: overlap: duplicate_key: os_error: pgid: written: failed: skipped: verify: stream: leftover:`

Both readings taken by the orchestrator at HEAD. The arm is a screen whose stated job is to raise
every key spelled in the constructor form; it cannot raise `duplicate_key=` because the key is not
in its alternation. **design-author owns this.** The spec's FR-4 eleven-key list already matches
`DETAIL_KEYS` member-for-member, so the spec is not the document that drifted.

This is the shape of catch the fourth (spec) leg was dispatched for, and it points the other way to
where it was expected: the unaudited document found a defect in the most-audited one.

## FACT 6 — sibling locators that were checked, and hold

Do not re-open these; the impl-plan leg ran all fourteen against all three siblings at `b3be433`
(10 design / 2 plan / 2 spec) and both one-hit caveats confirmed. Separately confirmed by the spec
leg: the spec's seven bare verdict-line fields match the impl-plan's seven, and FR-4's eleven
detail keys match the `DETAIL_KEYS` tuple at `impl-plan.md:2434` member-for-member.

## What each author owes

Read your own delta report in full first; it carries the prescriptions and the quotes. This sheet
only settles what more than one of you would otherwise measure separately.

- **design-author** — 4 musts **+ 1 routed** (FACT 5). The raised-set differential (rows 4–5),
  `58`→`60` (re-run the in-fence split first — see row 2's provenance note), "twice more"→"once
  more", the `OWED ELSEWHERE` discharge (FACT 2), and the missing `duplicate_key` in the `:2080`
  alternation. Three of the four musts are repeated verbatim in the v1.106 Version History entry and
  each takes a bracketed appended correction there as well as the body edit.
- **plan-author** — 6 musts. The cardinal-list `≥ 2` reading and its "+1 for all six" sentence, the
  `pgid` denominator (FACT 3), the `OWED ELSEWHERE` conclusion (FACT 2), the "in this section"
  placement claim, the register's `and`→`or` lead, and residual (2)'s `git status --porcelain`
  figure that has no sha.
- **implplan-author** — 3 musts. The `_SCANNED` glob cardinal — **close the class, not the
  instance**: the repair is a rule over every `.glob(` source, not `three`→`four`, because the next
  glob a reviser adds moves the cardinal again. The `§Scanning` sibling-location prose. The
  `plan.md:` presence universal at `:478`.
- **spec-author** — 3 musts. The twelve unswept body-scoped `this revision` phrases (per site, never
  a blanket sweep — the twenty-one `6f0ee85` hits that are historical stamps must NOT move), the
  `2486` at `:583` (FACT 1 row 1, FACT 4), and the `OWED ELSEWHERE` discharge (FACT 2).

## Standing constraints for this batch

1. **One author, one document.** An author that finds another document owes something **reports**
   it; it does not edit it. That report comes back here and the orchestrator routes it.
2. **The tree is frozen.** Nothing is committed until all four authors are done. A commit landing
   mid-batch makes every line number an author reports wrong against the base they were given.
3. **A count is evidence only against another count taken at the SAME commit, over the SAME corpus,
   in the SAME grammar.** Three of this arc's seven orchestrator errors were exactly this.
4. **Before counting a token, check which language construct it sits in.** The four surviving
   `pgid=` hits in the design are Python kwargs, not verdict-line fields. A grammar-blind count of
   them is how FACT 2 gets mis-repaired.
5. **Do not claim a two-surface clean or an exit gate.** Codex is exhausted until 2026-09-07 11:28.
   Nothing gated by a teammate is settled until a real codex round runs.

---

# CORRECTIONS — appended after all four authors landed

Appended, never rewritten: this sheet was the input four authors read, and editing what they were
handed would make their reports unreadable against it. Deliberately appended **after** they
finished, because mutating shared input under running readers is the staleness hazard of
orchestrator rule 4 — the same rule this round's structural finding is about.

Three of these are the orchestrator's own errors, all three caught by authors, none by the
orchestrator. That is the fourth consecutive round in which an author refuted this sheet, and it is
the strongest argument for the instruction at the top of it: **your run outranks this document.**

## C1 — FACT 1 row 5 is WRONG. Withdrawn. (orchestrator error #49i)

Row 5 claimed `design.md:928`'s second hop was false because `700c599`→working prints two changed
lines rather than one. **The document's series is CONSECUTIVE hops, not cumulative diffs from a base
I chose.** Run as the document defines them:

```
700c599 → 8c6539a   60c60      one changed line   — the document says one.  CORRECT.
8c6539a → b3be433   (nothing)                     — the document says nothing. CORRECT.
b3be433 → working   61c61      one changed line   — the document says nothing. FALSE.
```

Only the **third** hop is false. Row 4 stands; row 5 is withdrawn, and the wrong-figure count for
this round is **six**, not seven.

`design-author-r15` reached this independently and did **not** adopt row 5 — its v1.107 entry states
"the document's THIRD hop was the false one, not its second". The author was right and the sheet was
wrong.

**Species: SCOPE — verifying a series against a scope the verifier picked rather than against its
stated definition.** That is verbatim orchestrator error #49f, which *this sheet's own constraint 3*
warns the authors about. Writing a rule down is not the same as applying it, and the rule was
violated in the document that publishes it.

## C2 — the freeze sha this batch stamps is `dfae038`, not `00b961f` (orchestrator error, and a distinction the sheet blurred)

The header says "Freeze: `00b961f`". That is correct for the **subject of the delta review** — the
diff that was audited — and wrong as a value any document **stamps**. The freeze sha, by the spec's
own published definition, is the last commit and the tree every tree-derived figure is taken over:
`dfae038`. `spec-author-r15` stopped before writing to raise it; verified and broadcast to all four.

```
git diff --name-only 74e126f dfae038 | grep -vc '^docs/'   → 0
git diff --name-only b3be433 dfae038 | grep -vc '^docs/'   → 0
git log --oneline 74e126f..dfae038 -- <spec>               → 4 commits, not the 2 published
git show --stat b3be433 -- <spec>                          → empty; b3be433 never touched the spec
```

**The boundary, because the correction invites over-application:** every reading stamped at a BLOB
stays there. FACT 3's census at `b3be433`, the four-sha cardinal-list series, the fourteen sibling
locators, design's AC-4.6 `grep -oE 'pgid[=:]'`. Only an entry's own freeze-sha field moves.

**And a flaw in the broadcast itself, caught by `plan-author-r15`:** the broadcast justified reusing
`00b961f`-derived figures at `dfae038` by the four documents being byte-identical. That licenses a
false inference for any reading whose corpus is **wider** than the four documents — byte-identity of
`docs/` says nothing about `h-mad/`. The author found one such reading (the `h-mad/`/`handoff/`
interval closure) left at `b3be433` on exactly that reasoning. Re-run at `dfae038` it holds, so
nothing was wrong — but it was right by a fact nobody had checked. The correct control is
`git diff --name-only b3be433 dfae038 | grep -vc '^docs/'` → `0`, run above.

## C3 — FACT 1's `this revision` count was 12; it is 14 (orchestrator error #49j)

Both this sheet and the spec's delta report published **12** body-scoped occurrences. Both were
line-scoped. `spec-author-r15` collapsed the wrap first:

```
awk '/^## Version History$/{exit}{print}' "$S" | grep -c 'this revision'                      → 12
awk '/^## Version History$/{exit}{print}' "$S" | tr '\n' ' ' | grep -o 'this  *revision' | wc -l → 14
```

Two members straddle a hard wrap and are invisible to every line-scoped grep — including the
auditor's and mine. **A hard wrap hides a member from any single-line sweep; collapse newlines
before counting a phrase that can span one.** One of the two was named by no surface at all.

## C4 — a near-miss of the same species, recorded because it did not become an error

Checking that FACT 2 was discharged, the orchestrator searched 1400 characters past each surviving
`OWED ELSEWHERE` for a bracketed correction and found none in the spec. The correction **is** there
— `[v1.62 corrections, four of them…]` — 1900 characters out, past an earlier appended block. A
window chosen without checking whether it fits the data returns a false absence that looks exactly
like a real one. Widened rather than reported. Same fail-closed rule as the `ugrep: exceeds
complexity limits` error hit twice this round, where an empty result was an unrun command and not an
absence.

## Post-batch reconciliation — run after all four landed

- `git status --porcelain` → exactly four modified files, one per author. No scoping breach.
- FACT 2 discharge verified per document: spec v1.61 entry carries a `[v1.62 corrections…]` block;
  plan v1.101 entry carries `[corrected in v1.102: …]`; design and impl-plan carry **zero**
  pgid-bearing owed-claims. The class is closed across the feature at `dfae038`.
- The raw `pgid=` census over the FINAL bytes is `35`, of which `22` are `LaunchFailed(` — **not
  comparable to FACT 3's `12`/`10`**, because the documents now quote the census commands and the
  corrections themselves. That is decision K: a figure the revision's own fix moves. It is why FACT
  3 stays stamped at `b3be433`, which is what plan's must-3 prescribed and did.
- `PRECHECK: PASS issues=0` on all four.

## Still owed after this batch

- The `00b961f` commit message carries "Ten of the eleven `pgid=`" (line 60). Pushed, so it takes a
  bracketed correction in this batch's commit message — the treatment `8c6539a` got.
- The spec's `2486` at AC-6.4 and `BAD_ARGS` in AC-4.2's exit-0 enumeration were both still owed at
  `00b961f`; spec v1.62 reports addressing both. Verify at the new commit, do not assume.

## C5 — the header's "touched only `docs/handoffs/`" was never measured, and it is FALSE (orchestrator error #49n)

Line 5 of this sheet reads: "`df04e8e` and `dfae038` touched only `docs/handoffs/`". Measured after the
fact — `git show --name-only --format='' dfae038` — `dfae038` touches THREE files: the handoff doc,
`docs/learnings.md`, and `docs/skill-candidates.md`. `df04e8e` does touch only its handoff doc. The
compound claim is false for one of its two members, and it was never run before it was written.

It propagated from this line into all four r15 author prompts, all three r15 gating prompts, the
`7b182b0` commit message, and — via the authors — into `plan.md` (four sites under a markup-admitting
needle, two under a markup-blind one) and `impl-plan.md` (the v1.51 entry's freeze-field
justification). Both were filed as musts by the r15 gating legs and repaired in r16 (plan v1.103,
impl-plan v1.52), each attributing the origin to this sheet by path.

**The conclusion line 5 was supporting survives**: the four documents ARE byte-identical between
`00b961f` and `dfae038` (`git diff --stat` over both feature dirs, 0 lines). Only the scope word is
wrong. The line above is left as written, per this sheet's own rule that authors' inputs are appended
to, never rewritten.
