## Summary

I read the tree, not only the inlined text: the inlined design is byte-identical to
`docs/02-design/features/doc-block-exec.design.md` at `a8e0372` (diff over lines 1–1511 is empty),
so nothing here is a stale-source artifact. Two Must-fixes, both measured with a control that
reproduces the design's own cited numbers at the commit it cites: the Guard-narrowing corpus and
its softening enumeration are stale AND not closed as a class (`new_only=1` at HEAD, not 0), and
the `:270` block census is a behavioural premise with no inline command that drifted 4→7 between
`1861157` and HEAD. Axis C found no `restated` or `absent` acceptance criterion.

Evidence: 12 named tree files opened plus 55 git blobs read in the two controlled differentials, 31 greps and probes run.

Axis C — spec reconciliation, every `AC-N.M` at spec v1.55 (49 criteria):

| FR | `implemented-as-written` | `restated` | `absent` |
|---|---|---|---|
| FR-1 | AC-1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9 | none | none |
| FR-2 | AC-2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8 | none | none |
| FR-3 | AC-3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 | none | none |
| FR-4 | AC-4.1, 4.2, 4.3, 4.4, 4.5, 4.6 | none | none |
| FR-5 | AC-5.1, 5.2, 5.3, 5.4, 5.5, 5.6 | none | none |
| FR-6 | AC-6.1, 6.2, 6.3, 6.4, 6.5, 6.6 | none | none |

Notes on the ones I weighed rather than waved through. AC-1.2, AC-2.3, AC-3.2, AC-3.4, AC-3.5,
AC-4.4 and AC-6.3 are never named by identifier in the design, but each is covered in substance by
a range row of the Test Plan plus a prose rule (AC-3.2 by "`git status --porcelain` byte-identical
across a writing block" and the `cwd-not-passed` mutation; AC-4.4 by "`AMBIGUOUS` is the only
refusal carrying `blocks=`"), so they are `implemented-as-written`, not `absent`. AC-3.9's "A
refusal here closes both handles" is realised in the design as the backstop `finally` closing them
rather than the refusal itself — the same outcome (both descriptors released before `main`
returns), a mechanism split rather than a narrowing, so not `restated`.

## Must-fix

- The Guard-narrowing corpus and its softening enumeration are both stale and not closed as a class: at `a8e0372` `git ls-files -- h-mad handoff` filtered to `*.md` with `archive/` excluded returns **30**, not 25 (commit `6db8e50` added `h-mad/agents/{design-author,doc-auditor,implplan-author,plan-author,spec-author}.md`), so the very number the document uses to mark the *contaminated glob* is now the tracked count — the glob at HEAD is 35 — and the load-bearing conclusion `new_only=0` is false: re-derived over the 30 tracked files I get `both=290 old_only=82 new_only=1`, the one `new_only` identity being the **title-less** ATX heading at `h-mad/SKILL.md:984` (a bare `#`, column 0, outside any fence, introduced by `bea1b60`), which the old `^#+ <text>` regex cannot see because it requires a space and a non-empty title. This breaks the base Guard-narrowing invariant's "account for **every** input whose verdict softened": the enumeration names two shapes (`##\tx`, `## x ##`) where the ATX grammar admits three, and the omitted third is exactly the one that has a live instance. Two controls, because neither alone would settle it. Method control: the same script over `git ls-tree -r 1861157` gives `files=25 both=261 old_only=76 new_only=0 titleless=0`, reproducing the design's cited `old_only=76`/`new_only=0` exactly, so the method matches theirs and only the tree moved. Oracle control, on the real document rather than a synthetic string: rendering the whole of `h-mad/SKILL.md` through markdown-it-py 2.2.0 under the CommonMark preset — the interpreter-local version the design names — emits exactly one `<h1></h1>`, so `:984` is a level-1 heading in the artifact itself, not only in my model of the grammar. Consequence to state in the fix: level 1 is shallower than every `##` section, so after AC-1.8 `fence_aware_end` ends a section at `:984` where today's `docsections._fence_aware_end` (`re.match(rf"^#{{1,{level}}} ", line)`, space required) does not. I verified this is **not** a live regression — the `Phase 5 (Implementation) sub-steps` section (`h-mad/SKILL.md:297`) ends at 887 and `test_h_mad_review_evidence.py`'s `section_from` anchor (`h-mad/SKILL.md:938`) bounds at 954, so no current `docsections` consumer's section spans 984 — which is the point: only the accounting catches it, and the accounting is what is wrong. Prescription: re-measure over the 30, add the title-less form to the enumerated softening set with its instance, and state the rule over the axis (the softened set is every ATX shape the old `^#+ <text>` regex rejects: tab-separated title, closing hash run, and empty title) with its residual, so the next `#`-only line does not need a 30th cycle to be noticed.
  quote: docs/02-design/features/doc-block-exec.design.md › `by `git ls-files -- h-mad handoff` filtered to `*.md` with `archive/` excluded — not by a filesystem`
  quote: docs/02-design/features/doc-block-exec.design.md › `theoretical softenings `##\tx` and `## x ##` have zero instances) and `old_only=76`, every one a `#``
  quote: docs/02-design/features/doc-block-exec.design.md › `files. Measured at `1861157`: both softening shapes 0 over the 25 (5 closing-hash over the 30, both`

- Task 5's block census is a behavioural premise carried without its command, and it went stale inside 22 commits: at `a8e0372` the section `_second_surface()` hands `:270` holds **7** bash blocks, not 4, and tagging the gate fence leaves **6, not 3**. **The gating condition is the missing command, not the behind-HEAD sha** — a measurement sha behind HEAD is the ordinary advisory condition and `1861157` is legitimately pinned; what makes this blocking is that the base "Behavioural premises carry their command" invariant requires the exact command inline and runnable beside the observed output, and this sentence has none, which is precisely why the number went stale unnoticed and why a reader at HEAD who counts 7 cannot tell a wrong document from a moved tree. Measured both ways from the git blobs so the two commits are compared by the same code — at `1861157`: section 50 lines, `blocks=4`, gate at index 4, `exec codex` at index 2, after the tag `3`/`0`; at `a8e0372`: section 159 lines, `blocks=7`, gate still at index 4, `exec codex` still at index 2, after the tag `6`/`0`. The cause is `6db8e50` inserting `## Teammate audit leg — when codex is unavailable` (`h-mad/SKILL.md:2229`) between the two string anchors `_section` uses (`SECOND_SURFACE_HEADING` … `"## Helper scripts"`), so the fence-blind span grew from 2179–2229 to 2179–2338. **The conclusion the sentence exists to carry is unaffected and must not be rewritten**: gating still goes 1→0 while `re.findall` stays non-empty (6), so `_gate_bash_block`'s `assert gating` is still the loud failure and the "not an empty `findall`" correction from v1.93 stands. Prescription: re-measure at HEAD and put the command beside the number — the extraction is `_section(SKILL.md, SECOND_SURFACE_HEADING, HELPER_HEADING)` then `re.findall(r"```bash\n(.*?)```", section, re.S)` — so the count is re-derivable rather than re-read. The identical premise is carried by the spec's FR-6 Description and is owed the same sweep.
  quote: docs/02-design/features/doc-block-exec.design.md › `4 blocks instead of 4** (re-measured at `1861157`, unchanged from `e8eaf6f`: before the tag`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `Second-surface section holds four bash blocks, `:270` takes the one containing`

## Should-fix

- The migrated address bounds a strictly smaller span than the slicer it replaces, and the design states the *fact* of the divergence without its *magnitude* or its residual. `_gate_block()` is specified as `dbe.extract(SKILL_MD, "## Second surface — the codex leg")`, which by AC-1.5 ends at the next same-or-shallower ATX heading — `h-mad/SKILL.md:2229` — where the `_second_surface()` it replaces ends at the *named* `## Helper scripts` heading, `h-mad/SKILL.md:2338`. Invariant Compliance already says `_second_surface()` leaves the executing path; what it does not say is that seven of its eight call sites do not migrate (`h-mad/tests/test_h_mad_collect_report_docs.py` lines 118, 154, 225, 248, 389, 409 and 431 — only `:269` inside `_gate_bash_block` moves, and `:409` feeding the `:412` scan is deliberately untouched), so after Task 5 the file holds two different notions of "the Second surface section" side by side: seven text pins on the 7-block, 159-line span and one executor on the 4-block, 50-line one. I confirmed the gate fence (`h-mad/SKILL.md:2220`–2227, the only one containing `h_mad_audit_gate.py`) falls inside both, so the migration works today; the residual is that an `h_mad_audit_gate.py`-bearing fence added under `## Teammate audit leg` would be visible to the seven survivors and invisible to the executor. One sentence in Task 5 naming the narrowing and that residual costs nothing and stops Phase 5 rediscovering it.

- The closing-hash-run predicate is stated space-only at two sites, and the oracle the design cites disagrees. §Scanning and the ATX-grammar sentence both say the optional closing `#` run is "preceded by a space"; CommonMark §4.2 says spaces *or tabs*, and on markdown-it-py 2.2.0 (CommonMark preset) `'## Text\t##\n'` renders `'<h2>Text</h2>'` — the tab-preceded run is stripped. This is the same axis the design already closed on the *opening* predicate, where `request-predicate-space-only` exists exactly because the scanner accepts "a space, a tab or end of line"; the rule over the axis is that every `#`-run delimiter in ATX takes spaces-or-tabs, and the closing run is the one member left at space-only. Residual, measured: 0 instances of a tab-preceded closing run in the 30-file tracked corpus, so no fixture or live document depends on it — this would ship as a divergence between `_fence_events` and the renderer the design claims 14-of-14 agreement with, not as a current defect.
  quote: docs/02-design/features/doc-block-exec.design.md › `(preceded by a space) and trailing whitespace stripped, per CommonMark §4.2, so `## Text ##` and`

- Invariant Compliance's closing pointer is now itself misleading. It says the plan "still states 30 and is owed the same sweep", but 30 is the *tracked* count at HEAD, so a reader chasing that pointer will find the plan's number agreeing with a fresh `git ls-files` for the wrong reason and close the item. Whatever number the design lands on after the first Must-fix, this sentence needs to name the corpus rather than the figure.
  quote: docs/02-design/features/doc-block-exec.design.md › `filesystem glob behind the plan's `files=30` is not reproducible on a clean clone; the plan's`

## Nit

- The eight fault injections are numbered inconsistently. Test Strategy's lead sentence makes the instance-level `Popen` wrapper the `+1` after "seven module-level seams", but the body then calls the wrapper "The seventh" and `os.unlink` "The eighth". The set and the count are right in both places; only the ordinals disagree.

- The count-rule sentence writes `index=`, `value=` and `seconds=` bare while the verdict table renders all three quoted (`index="<n>"`, `value="<v>"`, `seconds="<n>"`). Nothing turns on it — that sentence is about which counts a refusal may carry, not about quoting — but it reads as an exception to the exhaustive bare-field list three paragraphs above.
