# doc-block-exec — impl-plan audit rejections

A record *about* the audit of `docs/01-plan/features/doc-block-exec.impl-plan.md`, not a document
the audit judged. **Never passed as `--gated`** (h-mad/SKILL.md §"Record a rejected finding in the
rejections ledger, never in a gated document"). One entry per rejection: cycle, surface, claim,
refuting evidence.

---

## Cycle 34 — agy (p1) — must-fix — REJECTED

**Report**: `docs/01-plan/features/doc-block-exec.impl-plan.audit.v34.p1.md`
**Base**: `1861157`, 2026-09-04. Impl-plan at v1.34 when audited; rejected during the v1.35 pass.

**Claim.** That the impl-plan's exhaustive list of bare (unquoted) verdict-line fields wrongly
classifies `keys`: "The `keys` field is classified as a bare int/enum safely produced by the
helper, but it actually contains the caller-provided `--subst` keys (a list of strings or tuples),
violating the exemption rule and potentially exposing unescaped data in the verdict line."

**Refuted on three independent grounds.**

1. **`keys=` is a count, not a key.** `docs/02-design/features/doc-block-exec.design.md:348`:
   the field "counts the **distinct keys implicated**, not the pairs (`a`, `ab`, `abc` →
   `keys=3`, three pairs)". A decimal integer is exactly the helper-produced value the bare
   exemption is for.
2. **The caller's key *strings* are already in the quoted set.** `design.md:1001` renders
   `SUBST_MISSING keys=<n>` with `missing_key: "<k>"` per key, and `design.md:1002` renders
   `SUBST_OVERLAP keys=<n>` with `overlap: "<a>" "<b>"` per pair — the key text travels on
   separate, **double-quoted** detail lines, never in the `keys=` slot. `design.md:1047-1048`
   map `MissingSubstitution(keys)` and `OverlappingSubstitution(pairs)` to exactly that
   rendering. The finding appears to have read `MissingSubstitution`'s **constructor argument**
   (a list of key strings) as the rendered field.
3. **The quoted evidence names a path that does not exist.** The finding's `quote:` line cites
   `docs/03-impl-plan/features/doc-block-exec.impl-plan.md`. There is no `docs/03-impl-plan/`
   directory in this repository (`ls docs/` → `01-plan/ 02-design/ 03-analysis/ 04-report/
   05-review/ archive/ handoffs/ patches/ plans/`). The impl-plan lives at
   `docs/01-plan/features/doc-block-exec.impl-plan.md`.

**Action taken**: none in the impl-plan. The bare list is correct as written and no change was
made on this finding's account.
