## Summary

I re-derived every measured premise the v1.94 delta introduced, against the tree at `335f535`
(the `*.md` corpus is byte-identical to `a8e0372` — the only non-doc change in between is
`h_mad_assemble_audit.py` + its test). **Every number in the delta checks out**: tracked 30 /
glob 35; `both 292 old_only 82 new_only 1` with the single `new_only` identity the title-less `#`
at `h-mad/SKILL.md:984` (opened; blank line above and below, outside any fence, immediately above
`## Reading a dispatch verdict`, blamed to `bea1b60`); the `1861157` control reproduces
`files 25 both 263 old_only 76 new_only 0` exactly; `lines 159 blocks 7 gating 1` → `6`/`0` after
tagging, and `50`/`4`/`1` on the AC-1.5 span; eight `_second_surface()` enclosing symbols; 81
helper matrix rows with exactly one naming `SKILL.md`; 8 wire rows over 6 distinct tests; all four
python fences `ast.parse`; markdown-it-py 2.2.0 (which `python3.11` does carry locally) confirms
`## Text\t##` → `<h2>Text</h2>`, `##\tx` → `<h2>x</h2>`, `##␣␣␣x` → `<h2>x</h2>` and `####### x` →
a paragraph. Both self-reported repairs are real: the eight bare line pins in Task 5 are gone, and
the dangling fragment is gone. The three findings below are **not** measurement errors — they are
cross-document contradictions the same round created, two of them against the spec's own explicit
instruction.

Axis C — 49 ACs reconciled by identifier (the seven whose bare identifier does not appear are each
carried by a range row: `AC-1.1–1.7`, `AC-2.1–2.7`, `AC-3.1–3.10`, `AC-4.1–4.5`, `AC-6.1–6.6`, each
of which I opened and read for the specific behaviour).

| Classification | Count | Items |
|---|---|---|
| `implemented-as-written` | 48 | all except AC-6.4 |
| `restated` | 1 | AC-6.4 — see Must-fix 1 |
| `absent` | 0 | — |

Evidence: 19 files opened, 34 greps/scripted derivations run. (The differentials additionally read
all 30 tracked `*.md` twice from the worktree and 25 more from git blobs at `1861157`.)

## Must-fix

- **AC-6.4 is `restated`: the design writes a hand-written total (`+ 9`, "nine-node tuple") for the floor tuple, which the spec deliberately withholds and which the plan and impl-plan both explicitly reject — the design is now the only one of the four documents carrying that literal, i.e. exactly the "second authority" the spec's rule exists to prevent.** `len(tuple)` occurs **0** times in the design (`grep -c 'len(tuple)' docs/02-design/features/doc-block-exec.design.md` → `0`) and 4 times in the plan, and the impl-plan enumerates all nine node IDs while stating no total. The membership arithmetic is right — I verified `_SCANNED` is built at module level including `*sorted((SKILL / "scripts").glob("*.py"))` and is consumed by exactly two `@pytest.mark.parametrize("path", _SCANNED, ids=lambda p: p.name)` decorators (`h-mad/tests/test_h_mad_portable_timeout.py:165` and `:295`, both opened), that `test_h_mad_mutation_harness.py` and `handoff/tests/test_mutation_specs_clean.py` have `grep -c parametrize` → `0`, and that the only other name-fed `parametrize` over a directory (`REAL_AUDIT_REPORTS`, `test_h_mad_audit_cycle.py:1672`) is capped `[:8]` against 461 matching files so it cannot grow — but a correct literal is still a literal, and this is the third round in which that literal has gone stale. **Prescription**: replace `+ 9` with `+ len(tuple)` and "its nine-node tuple" with "its floor tuple", keep the seven-authored/two-collected derivation as the *empirical check* of the spec's membership rule (which is what it is), and correct the v1.94 Version-History routing note — it asserts a debt that no longer exists and prescribes the correction the other two documents refused.
  quote: docs/02-design/features/doc-block-exec.design.md › `+ **9**, the nine being the node IDs added to *existing* files, **seven authored and two collected**, each asserted present.`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `**This spec deliberately carries no total for that tuple**; the`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `**No total is written for that tuple, here or anywhere.** "Seven" was the instance and it went stale the moment a second source of members was noticed; "nine" would go stale the same`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `v1.88's literal '+ 9' would have been the next '+ 7'`

- **Task 5's new absolute statement that "a positional claim about them would describe something the code does not do" contradicts the spec's FR-6 and the plan, both of which state the two ordinals in the same round and call them "the load-bearing part".** The design's *mechanism* claim is correct and I confirmed it by opening the code: `h-mad/tests/test_h_mad_collect_report_docs.py:271` is `gating = [b for b in blocks if "h_mad_audit_gate.py" in b]` followed by `assert len(gating) == 1`, and `:412` is `(b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b)` — both select by content predicate, never by offset. But the ordinal is nonetheless a true, re-derivable property of what the code produces: I enumerated the seven blocks and the gate block is 1-based index 4, the `exec codex` block index 2, reproducing the spec's own inline command output `7 [4] [2]`. As written the design tells a reader that the spec's load-bearing statement describes something unreal, and a reader reconciling design against spec gets opposite instructions on the one axis this feature's Task 5 turns on. **Prescription**: narrow the sentence to *selection* — "neither block is **selected** by position; both are addressed by a content predicate" — keep the 0-based/1-based warning, and add the cross-reference that spec FR-6 and the plan state the ordinals 1-based with `enumerate(b, 1)` in their command, which is the base the design's own warning asks for. If the intent is instead that the ordinals leave the spec and plan, that is a routing item and must be written as one, since the spec is the source of truth.
  quote: docs/02-design/features/doc-block-exec.design.md › `**Neither block is identified by position anywhere, in this document or in`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `(block 2). The **ordinals are the load-bearing part and are unchanged.**`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `ordinals are the load-bearing part and did not move**: the gate block is still block 4 and the`

- **The closing-hash-run delimiter was widened from space-only to spaces-or-tabs at the design's two sites, and the divergence this creates with the impl-plan was not routed — the impl-plan still prescribes the space-only strip at two prose sites, and its `test_closing_hash_run_does_not_change_heading_identity` row does not carry the tab-preceded fixture the design now requires.** This is a hard gap, not a tidiness item: an implementer following the impl-plan writes a space-only strip, and the design's newly-required fixture `## Text\t##` then fails, because a space-only strip leaves the tab form unequal to `## Text`. The design's rule is the correct one — I confirmed the oracle it cites on the interpreter it names (`python3.11` carries markdown-it-py `2.2.0` here; `md.render('## Text\t##\n')` → `'<h2>Text</h2>\n'`). **Class, not instance**: the axis is *every `#`-run delimiter in ATX takes spaces-or-tabs*. I swept all four documents for it — the design is now correct at both its sites, the spec states no delimiter for the closing run (`text compared after the CommonMark closing hash run and trailing whitespace stripped`, so it is compatible), the plan states none, and the impl-plan is the only residual, at exactly the two prose sites plus the one test row. **Prescription**: add those three impl-plan sites to the design's "Owed elsewhere and routed" list by name; the residual after that is zero.
  quote: docs/02-design/features/doc-block-exec.design.md › `preceded by a space **or a tab** — both delimiters take spaces-or-tabs, see §Scanning's heading-bounding rule`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `optional closing `#` run preceded by a space is stripped before the text is compared`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `the line after the opening hash run, with the optional closing hash run (preceded`

## Should-fix

- **The command published as the way to re-derive `old_only=82`/`new_only=1` derives a different premise from the one the paragraph above it states, and the equality between the two is asserted rather than derivable from what is published.** The paragraph attributes the figures to "the old `re.search` heading regex", i.e. `titled_section`'s unbounded `#+` run; the fence's `OLD` is `re.compile(r"^#{1,6} ")`, which the prose itself identifies two paragraphs later as the *bounder*'s narrower shape, while the fence's own comment calls it "the fence-blind guard being replaced". I ran both: `^#{1,6} ` gives `both 292 old_only 82 new_only 1` and `^#+ ` gives `both 292 old_only 82 new_only 1` — identical, so the numbers are right and the tightening row's "0 instances" is confirmed. But a later reader running the published script cannot reach the stated premise, only its twin. Fix by publishing both `OLD` variants on adjacent lines (two characters apart) so the equality is a run, not a sentence.
  quote: docs/02-design/features/doc-block-exec.design.md › `OLD = re.compile(r"^#{1,6} ")                     # the fence-blind guard being replaced`

- **The new "locate by enclosing symbol, never by line" rule was applied at one site and the class was not closed.** Four bare line pins survive elsewhere in the same document: `` `:270` `` and `` `:412` `` in Task 5 and the AC-6.2 mutation row, and three `path:line` pins in Invariant Compliance. I opened every one — `test_h_mad_context_budget_docs.py:69` is `def _titled_section(...)`, `test_h_mad_batch_doc_rules.py:26` is `def section_text(...)`, `test_h_mad_collect_report_docs.py:40` is `def _section(...)`, `:270` is the `re.findall`, `:412` is the `exec codex` generator — so all five are accurate at HEAD and none is a correctness defect. But the three Invariant-Compliance pins address *definitions*, which is exactly what the ast locator Task 5 introduced would find by name, so the rule as stated covers them and the document does not say why they are exempt. Either state the exemption ("a pin on a `def` is stable under insertions above it only if re-derived; these are re-derived at each revision") or convert them.
  quote: docs/02-design/features/doc-block-exec.design.md › `never read it — no line numbers on purpose, since a line pin goes stale on any insertion above`

- **The "14 of 14" grammar-oracle premise is not re-derivable by any later reader, and neither document says so.** The design cites it as settled ("14 of 14 agree on both versions; the corpus and its output are in the plan's §Measurements") and the plan carries the transcript, but the plan also says the script is a throwaway — `grammar_corpus.py` is not in the tree (`git ls-files | grep grammar_corpus` → nothing). §"Behavioural premises carry their command" requires that a premise whose command has become expensive or impossible to re-run says so and names the cheap proxy. I confirmed four of the fourteen cases individually against the named oracle, so the premise is very likely sound — but that is my re-derivation, not the document's. Fix by either committing the corpus script beside the mutation specs or stating in the design that the 14-case corpus is a one-off whose cheap proxy is the four grammar rows the §Scanning table already names.

## Nit

- "**Each seam below is named, never numbered**" sits mid-paragraph, after five of the eight seams (`killpg`, `rmtree`, `mkdtemp`, `chmod`, `_final_write`, `_close_stream`) have already been described above it, so "below" is wrong for most of the set it governs. Move it to the head of the paragraph. (The counts themselves are consistent: both enumerations list the same seven module seams plus the one instance-level wrapper.)
- "rendering the whole file through markdown-it-py 2.2.0 under the CommonMark preset emits exactly one `<h1></h1>`" is literally true of the empty-`h1` token but reads as a claim about `<h1>` elements; the file renders **two**, the other being `<h1>/h-mad — 7-phase H-MAD Orchestrator (v2.2, standalone)</h1>`. One word ("exactly one *empty* `<h1></h1>`") removes the ambiguity.
