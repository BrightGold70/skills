# #56 — the eleven impl-plan rows naming a different AC

**Date:** 2026-09-14
**Feature:** `wsg-56-impl-plan-ac-enumeration` (claimed, skills:docs/.bkit-memory.json)
**Brief:** `docs/handoffs/2026-09-14-main__wsg-56-impl-plan-ac-enumeration.md` (`da63499`)
**Supersedes as evidence:** `docs/04-report/features/wsg7-carried-claims.probe.v1.md` §8 (`c21e63e`), whose `CANNOT PROBE` verdict this report retires.

## Verdict

**The claim is TRUE, and it did not need re-deriving. The enumeration EXISTS.**

The brief's central premise — *"The eleven rows were never enumerated in any of the four handoffs
that carried the row, in the WSG audit reports, or anywhere in either repo… neither lane holds the
list. #56 is not a lookup — it is a re-derivation"* — is **FALSE**.

The census is in the impl-plan itself, at
`website-source-grounding.impl-plan.md:6643`, inside the **v1.12 Version History entry**, item (5).
That entry is a single **8485-character line**. It is not in a section, not under a heading, and not
findable by any of the searches either lane ran, which is why two lanes and one prior probe all
concluded it did not exist.

It says, verbatim:

> ELEVEN further rows cite an AC whose criterion is a different property, including two clean SWAPS
> (`ac_2_2` carries AC-2.3's subject while `ac_2_3` carries AC-2.2's; `ac_3_1` carries AC-2.1's
> set-equality subject while an `ac_2_1` row carries an `admitted_registry_ref` property AC-2.1 does
> not state). SIX of those eleven are ALREADY SHIPPED as test functions in committed code […] so
> re-spelling them in this document would desynchronise it from the tree and would need a code
> rename this author may not make. Rows 5 and 7 are unshipped, which is why they are the two that
> move.

Both figures in the carried claim — **eleven**, and **six already shipped** — are confirmed at their
origin, not reconstructed.

## The rows — 8 of 11 named, with provenance

Located in the impl-plan by node id. "SHIPPED" is the census's own classification.

| # | task | row | prefix | node id | why it mismatches | shipped |
|---|---|---|---|---|---|---|
| 1 | Task 1 | 1 | `AC-3.1` | `test_ac_3_1_admitted_classes_set_equality_per_setting` | carries **AC-2.1's** set-equality subject | yes |
| 2 | Task 1 | 2 | `AC-3.1` | `test_ac_3_1_monotonicity_as_set_containment` | same prefix class | yes |
| 3 | Task 1 | 9 | `AC-2.1` | `test_ac_2_1_admitted_registry_ref_admits_none_under_both_settings` | asserts an `admitted_registry_ref` property **AC-2.1 does not state** | yes |
| 4 | Task 3 | 3 | `AC-9.3` | `test_ac_9_3_fixture_mtimes_are_set_explicitly_not_inherited_from_checkout` | named by the census | yes |
| 5 | Task 12 | 6 | `AC-1.4` | `test_ac_1_4_korean_negative_resolves_to_no` | named by the census | yes |
| 6 | Task 12 | 7 | `AC-1.5` | `test_ac_1_5_strike_through_and_colour_residual_pins_to_yes` | named by the census | yes |
| 7 | Task 14 | 20 | `AC-2.2` | `test_ac_2_2_quorum_enforcing_site_and_claim_like_predicate_are_unmoved_by_the_flag` | **SWAP** — carries AC-2.3's subject | no |
| 8 | Task 14 | 21 | `AC-2.3` | `test_ac_2_3_resolve_quorum_is_zero_point_eight_with_the_environment_unset` | **SWAP** — carries AC-2.2's subject | no |

**Rows 1–6 are the census's "SIX already shipped", recovered by name.** Rows 7–8 are the two clean
swaps, recovered from the swap description and confirmed present at those node ids.

**Three rows remain unnamed.** The census states the count (eleven) but enumerates only the six
shipped ones plus the swap pairs; item (5) says the full list *"IS IN THE REVISION REPORT, NOT FIXED
IN PLACE"*. **That revision report is in neither repo** — searched across
`HemaSuite/hematology-paper-writer/docs` and `skills/docs`; the six node ids appear in exactly one
file, the impl-plan. So the last three are the only part of #56 that is genuinely a re-derivation.

## Two adjacent rows, already FIXED — not part of the eleven

Task 13 rows 5 and 7 carried `ac_10_9` prefixes for properties `AC-10.9` does not state. They were
re-spelled onto `test_d_11b_…` and `test_d_11a_…` at impl-plan v1.12. The census calls the eleven
*"further"* rows, i.e. beyond these two. Spec §Contradictions **Item 17** is where the defect was
first ruled on, and it declines to enumerate by row in so many words: *"the same mismatch applies to
it and is not separately enumerated, because the axis is the prefix and not the row."*

## Method, and two instruments that failed

- **Row grammar.** 202 test rows extracted as `| N | test_… | subject |`; 177 carry a parseable
  `ac_X_Y` prefix. The impl-plan's own `grep -n '^  - AC-'` (L114) does **not** match this document —
  it describes the **spec's** AC-definition grammar at `daed4229`, and returns 0 here.
- **The brief's warned-against proxy was not used.** Prefix-vs-test-name measures a different
  property than prefix-vs-AC-semantics.
- **A structural narrowing was tried and FAILED, and the failure is informative.** Flagging rows
  whose prefix AC is absent from their own task's declared `**ACs**:` line returns **0 of 177**.
  Every mismatched row sits in a task that *declares* the AC it mis-cites, so the defect is invisible
  at task level. This is independent confirmation that no cheap screen exists — the remaining three
  need each row read against the spec's AC text.
- **A count in the brief is mislabelled.** It states *"202 `AC-x.y` occurrences"*. 202 is the
  `grep -c` **line** count; occurrences are **341** (`grep -o … | wc -l`). Its own reproduce command
  is `grep -c`, so the number is right and the label is wrong.

## Closure — CLOSED 2026-09-14 by operator decision

**#56 is closed.** The row asked for the eleven rows to be enumerated on the premise that no
enumeration existed. That premise is false, so the task as framed is moot: the census was recovered
rather than re-derived, and its two load-bearing figures — **eleven**, and **six already shipped** —
are confirmed at their origin.

**What closing accepts, stated so it is not silently inherited.** Three of the eleven are named
nowhere, *including at the origin*: the v1.12 author counted eleven and enumerated eight. The
remainder was deferred to a "revision report" that was never written into either repo. So the three
are not work this lane declined — they are work that was never recorded by anyone, and closing #56
accepts them as not owed rather than carrying them forward as a debt.

Anyone who later needs all eleven should start from §Method below: the row grammar, the confirmed
count, and the measured fact that no mechanical screen narrows the residue.

## What was owed, at the time of writing

1. The remaining **three** rows, by reading each of the 169 not-yet-classified prefixed rows against
   the spec's AC text. No mechanical screen narrows this further — measured above.
2. Nothing else. The count and the shipped-six are settled at their origin and should not be
   re-derived again.

## Why this was missed three times

The census sits inside a Version History bullet, which is prose in a section every document-level
search treats as a changelog rather than as content. `handoff`'s own `pending-handovers` scan
deliberately reads only a document's **header** block for the same reason. A finding filed into a
changelog line is durable but unfindable; the lesson generalises past this row.
