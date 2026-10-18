# Plan: grok-audit-surface

## Executive Summary
Build and test a seeded-defect scorer that measures grok against agy on 27 planted build-class defects. An operator then runs a live smoke and, if it passes, the calibration. The result is published whatever the outcome. grok becomes a third leg on each document's first gating cycle only if the smoke prints `SMOKE: PASS` and the probe then prints `SEEDSCORE: PASS`. That token means the amended D3 predicate `(fab_grok < fab_agy AND recall_grok ≥ recall_agy) OR (fab_grok = fab_agy AND recall_grok > recall_agy)` held under the worst case. A full tie does not promote.

## Overview
grok's audit precision is labelled **unmeasured** in two places in `h-mad/SKILL.md`, so a third independent model family sits idle on every normal run. This plan turns that label into a number. It does so through a committed probe, a committed ledger, and a committed measurement doc, all of which can be re-run after a grok upgrade. The routing change is gated on that number, not on the build of the instrument. The work therefore splits into an unconditional, CI-tested half (the instrument, pins on existing gate behaviour, and two SKILL.md text fixes that are true today) and a conditional half (the "unmeasured" text and the routing text), with operator-run live steps between them. Every live dispatch runs in a non-git export root, so neither git history nor this feature's answer key is reachable from it.

## Scope
- **In**: the audit path of grok 1.0.62 (`exec grok` audit leg, NDJSON vocabulary, `scan_grok`, report delivery); non-git root acceptance by grok, agy and (when available) codex; the seeded-defect ledger and seeded copies of 9 archived documents; the export-root builder with its declared exclusion list, content scan and git reach check; the scorer probe and its suite tests; calibration dispatches through `hmad-dispatch audit-cycle`; blinded hand labelling; the measurement doc; the SKILL.md "unmeasured" text at both sites (every outcome except UNREADABLE); the AC-6.2a teammate-section command correction (every outcome); the first-gate routing text (PASS branch only); tests that pin existing three-pass union, evidence floors, and exit/round behaviour across leg sets.
- **User-visible behaviour on PASS**: a document's first gating cycle with codex and grok both available runs `hmad-dispatch audit-cycle --passes 3 --surfaces codex,agy,grok`. Revision cycles stay codex-gated with the doc-auditor ADVISORY delta review.
- **User-visible behaviour on MISS or INCONCLUSIVE**: routing is unchanged. SKILL.md gains the measured fractions and a pointer to the measurement doc in place of "audit precision … unmeasured".
- **User-visible behaviour on a smoke failure**: routing is unchanged and no calibration runs. Audit precision stays in grok's unmeasured list at both SKILL.md sites, each gaining the measurement-doc pointer and a clause saying the 1.0.62 audit-path smoke failed (AC-1.8).
- **User-visible behaviour on every outcome**: the §"Teammate audit leg — when codex is unavailable" command names `hmad-dispatch audit-cycle … --surfaces agy,grok` instead of a script that does not parse `--surfaces` (AC-6.2a).

## Goals
- Re-smoke the grok 1.0.62 audit path in a non-git export root, measure whether grok, agy and codex accept that root, derive the calibration `--timeout` from measured wall time, and end on one derived `SMOKE:` line (FR-1).
- Build a ground truth: 27 seeds in 9 documents, four classes, with a ledger that the probe can rebuild byte for byte, and close the leak axis with export roots, declared exclusions, a content scan and a git reach check (FR-2).
- Dispatch every seeded document once per surface through the production wrapper, with identical prompts across surfaces (FR-3).
- Label every must-fix by hand, blinded, and use mechanical hints only as advisories (FR-4).
- Ship a stdlib-only scorer whose verdict is exact rational arithmetic over the amended D3 predicate, with one fixture per verdict, per UNREADABLE reason, per leak and git-reach trigger, per predicate branch, and on the tie boundary (FR-5).
- Publish the reading on every outcome, retire "unmeasured" for audit precision on PASS, MISS and INCONCLUSIVE, and correct the teammate-section command unconditionally (FR-6).
- Ship the first-gate routing change on `SEEDSCORE: PASS` only (FR-7).
- Pin that the three-surface gate is the union, that the evidence floors hold at pass index 3 (FR-8), and that the exit streak and round cap behave across leg sets exactly as today (FR-9).
- Show end to end that `--passes 3 --surfaces codex,agy,grok` dispatches three distinct surfaces (FR-10).

## Requirements
- FR-1: Audit-path re-smoke on grok 1.0.62, non-git root acceptance, the `SMOKE:` line and the smoke-failure delivery (AC-1.1–1.8).
- FR-2: The seeded-defect set, N = 27 across 9 documents, and leak control (AC-2.1–2.6).
- FR-3: Calibration dispatch through the normal audit-cycle path (AC-3.1–3.6).
- FR-4: Finding classification and fabrication confirmation (AC-4.1–4.5).
- FR-5: The scorer probe (AC-5.1–5.5).
- FR-6: Measurement doc, the "unmeasured" text, and the teammate-section command correction (AC-6.1–6.4, including AC-6.2a).
- FR-7: Routing change on PASS only (AC-7.1–7.4).
- FR-8: Union gate across three surfaces (AC-8.1–8.3).
- FR-9: Exit streak and round cap across leg sets, with no change to `exit_check` or `round_check` (AC-9.1–9.5).
- FR-10: Three distinct surfaces through the wrapper, end to end (AC-10.1–10.3).

## Implementation Strategy

### Ordering: the instrument first, the routing last, and the routing conditional
The work runs in five stages. Each stage's entry condition is the previous stage's token, never its exit status.

| Stage | Who runs it | In CI? | Contents | Entry condition |
|---|---|---|---|---|
| S0 Instrument | Phase-5 TDD tasks | yes | FR-2 ledger, seeded copies and rebuild check; the AC-2.6 export-root builder, declared exclusion list, content scan and git reach check; FR-5 probe and every AC-5.5 fixture; AC-8.1/8.2 tests; AC-9.1–9.4 tests; FR-10 tests; the AC-9.5 sentence; AC-6.2a (RED run of the new doc test against the uncorrected SKILL.md, then the correction) | design and impl-plan gated |
| S1 Smoke | operator, live grok/agy (codex when available) | **no** | FR-1: build the smoke document's export root; the probe's content scan and git reach check read clean on it; in that root, one `--passes 1 --surfaces grok` cycle, one `--passes 1 --surfaces agy` cycle, and one `--passes 1 --surfaces codex` cycle when codex is available (AC-1.6); record vocabulary, delivery, `RESOLVED-MODEL`, wall time and per-surface root acceptance; derive `--timeout`; the derived `SMOKE:` line (AC-1.7) | S0 merged |
| S2 Calibration | operator, live grok/agy/codex | **no** | FR-3: 9 cycles, each in its own export root whose scan and reach check read clean (`codex,agy,grok`, or `agy,grok` when codex is unavailable or refused the root at S1); FR-4: findings extraction, blinding, hand labels by a labeller who does not hold the key | `SMOKE: PASS` |
| S3 Score and publish | Phase-5 task over committed data | the re-score yes; the dispatches no | Probe prints `SEEDSCORE:`; FR-6 measurement doc; the `grok-runtime.md` sentence and the AC-6.2 SKILL.md text, per the outcome branch below | `SMOKE: PASS` and labels and key committed; or `SMOKE: FAIL` (smoke-failure branch, below) |
| S4 Route | Phase-5 task | yes | **Branch on the S3 token** (below) | `SEEDSCORE:` is PASS, MISS or INCONCLUSIVE |

**The live dispatches in S1 and S2 are operator-run steps. They are not CI tests.** No suite test dispatches grok, agy or codex for real. The suite tests the probe against synthetic fixtures (S0), and it tests the re-run command (AC-6.4) against the committed ledger, labels and key, which needs no network and no agent (S3). A test that needed a live agent would go red on any machine without grok and would bill a dispatch on every run.

**The outcome branch** is read from token lines, never from `$?`: first the AC-1.7 `SMOKE:` line, then, only if the smoke passed, the AC-5.1 `SEEDSCORE:` line (PASS, MISS and INCONCLUSIVE all exit 0). Every branch also carries the unconditional S0 set, which includes AC-9.5 and AC-6.2a. This follows the spec's "Delivery by outcome" table, which is the authority; the plan does not restate its cells beyond what staging needs.

- **`SMOKE: FAIL reason=<r>[,<r>…]` → the smoke result ships, and nothing is scored.** S2 does not start, no findings are labelled, and no `SEEDSCORE:` line exists (AC-1.8). S3 ships the measurement doc holding the `SMOKE: FAIL` line, the AC-1.2 vocabulary table, the AC-1.4 `RESOLVED-MODEL` line and wall time, and the AC-1.6 per-surface acceptance outcome, saying it holds no recall or fabrication figure. It also ships the `grok-runtime.md` smoke-failure sentence (the AC-1.5 "re-smoked" sentence is withheld; the 1.0.41 sentence stays unchanged). At both AC-6.2 SKILL.md sites, audit precision **stays unmeasured**, and each site gains the measurement-doc pointer and the smoke-failure clause. S4 does not run, and none of AC-7.1–7.3 or AC-8.3 ships. A smoke failure is not retried as a pass. Any new smoke is a new reading at a new sha. The reason set is closed: `truncated`, `vocab_split`, `vocab_missing:<type>`, `no_delivery`, `nongit_root_refused:<agent>` with `<agent>` grok or agy. A codex refusal is not a smoke failure. It is published, and S2 runs the codex-unavailable shape with the codex ceiling published as not run. No surface ever falls back to a git work tree or a worktree root.
- **`SEEDSCORE: PASS` → routing ships.** S3 ships the AC-1.5 sentence and the AC-6.2 retirement to the measured fractions. S4 ships AC-7.1 (SKILL.md §"Never gate on one audit pass", the "**Which two surfaces …**" paragraph, names `--surfaces codex,agy,grok` and rewords the "three reports, of which two share a model family" sentence), AC-7.2 (availability fallback to `codex,agy`), AC-7.3 (doc-test pins), and AC-8.3 (the grok-must-fix falsification sentence at the AC-7.1 site).
- **`SEEDSCORE: MISS` or `INCONCLUSIVE` → numbers are published and routing is unchanged.** S3 ships as on PASS; INCONCLUSIVE additionally carries its `reason=` into the SKILL.md text (AC-6.3). None of AC-7.1–7.3 or AC-8.3 ships (AC-7.4). §"Never gate on one audit pass" stays byte-unchanged except for the FR-6 pointer, if one is placed there. The evidence that this branch was taken is the measurement doc's `SEEDSCORE:` line, plus a section-scoped diff of §"Never gate on one audit pass" against the S0 base that shows no other change. The design pins whether a test asserts this.
- **`SEEDSCORE: UNREADABLE` → nothing in S3 or S4 ships.** The cause (`ledger_counts`, `ledger_origin`, `seed_rebuild`, `leak:<path>`, `root_git:<path>`, `must_count_mismatch:<report>`, `label:<id>`, `key_mismatch`) is fixed, and the probe is re-run until it prints a non-UNREADABLE token.

AC-8.3 is PASS-only and AC-9.5 is unconditional at S0; spec v1.2 states both stagings with reasons. AC-6.2a is unconditional at S0 for the same reason as AC-9.5: the corrected command is true today, whatever the measurement says.

### Layers that change
- **New**: `docs/03-analysis/probes/grok-audit-surface/` holds the probe, the ledger (one JSON record per seed), the committed seeded copies, the declared exclusion list, and, after S2, the findings, labels and key. `docs/03-analysis/grok-audit-surface.measurement.md` holds the reading.
- **New tests** under `h-mad/tests/` (see "Where the tests live"), including the AC-6.2a doc test.
- **Edited text only**: `h-mad/SKILL.md` (AC-6.2a and AC-9.5 at S0; AC-6.2 or its AC-1.8 replacement at S3; AC-7.1 and AC-8.3 on PASS) and `h-mad/references/grok-runtime.md` (one added sentence: the AC-1.5 sentence, or on a smoke failure the AC-1.8 sentence; the 1.0.41 sentence unchanged in both).
- **Deliberately untouched**: `exit_check`, `round_check`, `combine`, `scan_grok`, the wrapper's `--surfaces` grammar, the codex-unavailable route, and `fallback_agent` semantics (spec NFR Compatibility). FR-8, FR-9 and FR-10 add tests over existing behaviour and no code.

### Where the tests live (AC-5.5, settled here)
- **Directory**: every scorer test lives in the suite under `h-mad/tests/`, never next to the probe. The probe directory is not collected, and a test there would be a second, untested harness.
- **Archive survival is a constraint on the test's source text.** `h_mad_archive_feature.py` `probe_readers` keeps a probes directory only when a tracked non-markdown file outside it spells `docs/03-analysis/probes/grok-audit-surface` followed by a path boundary (`/`, `"`, `'`, whitespace or end of line). So the scorer test file must name the probe through that literal string, for example `ROOT / "docs/03-analysis/probes/grok-audit-surface"`. A path assembled from parts (`"docs" / "03-analysis" / …`) is invisible to `probe_readers`, so the directory would be archived and the test would break at Phase 7.
- **The probe file is not named `test_*.py`** and imports only the stdlib plus `h_mad_audit_gate` / `h_mad_audit_origins` from `h-mad/scripts/` (AC-4.1 reuses `classify_detail`, and AC-2.4 reuses `ORIGINS`).
- **The design pins**: the scorer test module's file name; the AC-6.2a doc-test module; whether the FR-8, FR-9 and FR-10 tests extend the existing `test_h_mad_audit_cycle_grok.py`, `test_h_mad_audit_gate.py` and `test_hmad_dispatch_audit_cycle_grok.py` or go in new modules; and the fixture layout per AC-5.5 branch, including the leak and git-reach triggers (each run with that trigger alone) and the one must-not-refuse exemption fixture.

### The prompt-diff mask (AC-3.2)
- **The mask is the report-path lines only, which is the wrapper's own rule, and spec v1.2 states it.** `_cmd_audit_cycle` in `h-mad/scripts/hmad-dispatch.sh` diffs pass 1's prompt against each pass i ≥ 2 before any dispatch. It halts with `--halt-reason prompt_divergence` when the diff is empty, or when any differing line contains neither pass's report path (a `grep -F` fixed-string match on `${report[1]}` and `${report[$i]}`). The probe's AC-3.2 check applies the same rule. Sentinel lines are not masked, because the wrapper passes no `--sentinel` and every pass of a cycle gets the assembler's default `AUDIT-<feature>-<phase>-v<cycle>`.
- **Prompts are compared within a cycle only.** A re-dispatched cycle (AC-3.4) has a new cycle number, and therefore a different sentinel.
- **The design pins**: how the prompts are retained (the wrapper writes them under `HMAD_AUDIT_STEM_DIR`, default `/tmp`, and does not delete them, so S2 points that variable at a kept calibration directory outside every export root, since a prompt inlines the seeded document and is not part of what a reviewer may read); whether the probe re-runs the diff or reads the wrapper's `prompt_divergence` halt; and the exact report-path literal shapes produced by `prepend_output_contract`.

### Leak control (AC-2.6): what the plan carries
Spec v1.2 settles the axis and the rule, so this section stages it and names the constraints it puts on the work. The axis: **any route by which a reviewer with tools, working from the dispatch root, can recover a seed's `original` span or its `expected` finding**, through (a) this feature's own answer key, (b) git history, or (c) verbatim copies, named or not.

- **Order of operations per root.** Export the calibration sha's tree into a fresh directory outside every git work tree (never a `git worktree`, clone or checkout). Remove the declared exclusion list. Place the seeded target and only the paired documents the assembler reads for its phase. Run the content scan and the git reach check. Only on a clean result, dispatch with `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY` and `GIT_ALTERNATE_OBJECT_DIRECTORIES` unset, recording the command verbatim. S1's smoke root and each of S2's nine roots go through the same order. The probe's check refuses with `leak:<path>` or `root_git:<path>`, which are AC-5.4 UNREADABLE reasons and carry AC-5.5 fixtures at S0.
- **The scan has no "excluding the seeded target" carve-out.** Every regular file in the root is scanned, the seeded target included, for all 27 seeds' `original` and `expected`, after decoding as UTF-8 with replacement and collapsing whitespace runs. The single exemption is narrow: a seed's `original` may appear only inside the paired copy of **that seed's own source document**, and only when that file's sha256 equals the archived source's. `expected` is never exempt. A hit on the seeded target means the seed's `original` span must be widened until it no longer occurs there.
- **Which roots need the exemption.** The assembler pairs a plan with the spec, a design with the spec and plan, and an impl-plan with the design only (R2 command; read in `assemble`'s `slots[...]` block). So the 3 design roots carry the archive plan (which holds the plan seeds' originals), and the 3 impl-plan roots carry the archive design (which holds the design seeds' originals). 6 of the 9 roots are buildable only with the exemption. The 3 plan roots need none.
- **A constraint on seed choice the scan enforces.** The paired spec in every plan and design root is not seeded and is not anyone's own source, so the exemption never covers it. A plan or design seed whose `original` span also occurs verbatim in that feature's spec gives `leak:<spec path>`. The answer is to re-choose or widen the span, never an automatic exclusion. The same holds for any other tree file that quotes a source document (R6 shows the scale for the one directory the spec already excludes).
- **What the git reach check proves about placement.** It refuses a root holding a `.git` entry at any depth, and a root inside a work tree (`git -C <root> rev-parse --git-dir` succeeds). The design pins the root's parent directory. Whatever it pins, the check, not the choice, is the evidence.
- **Residuals carried as spec-stated**: paraphrase or partial copies; non-UTF-8 stored forms; reads outside the root by absolute path (not closed; agents' sandboxes are unmeasured; named in the measurement doc); name mentions with no seed text (R4 counts those mentions and is not a leak); submodule paths, which `git archive` exports empty, so a C2 seed must not name a path under the three gitlink entries (R11).

## Architecture Considerations
- **One wrapper call per first gate (AC-9.4).** The three first-gate legs must run as one `audit-cycle --passes 3` call so that every stamp in the cycle records the same leg set. Separately collected legs can disagree within a cycle, which gives `legs_disagree:<phase>.v<N>`. Stamps are written through `_leg_key` (sorted and deduped), so a `codex,agy,grok` surfaces list stamps `["agy","codex","grok"]`, as AC-10.2 expects.
- **"In that pass order" means pass index, not wall-clock order (AC-10.1).** `_cmd_audit_cycle` launches every pass in the background (`&`) and then waits on each one. The test asserts the pass-i → agent mapping and the per-pass report path. It does not assert invocation time order, which is nondeterministic.
- **The scorer is a pure function of committed files.** It takes the ledger, the archive sources, the seeded copies, the exclusion list, the reports, the findings, the labels and the key, and it returns one token line. That makes AC-6.4's re-run possible with no dispatch (it rebuilds the export roots and re-runs their scan and reach check), and it makes every verdict testable from fixtures.
- **Exact rationals.** Fabrication rates compare as reduced fractions (`fractions.Fraction`), and `0/0` compares as zero (AC-5.2). The worst-case bounds of AC-5.3 are two predicate evaluations: grok's undecidables counted as fabricated against agy's counted as not fabricated, and the reverse.
- **Blinding is procedural, and it has a residual.** Opaque ids and a shuffled order hide the surface label. They do not hide each model's writing style, so the labeller may still be able to infer the surface. The measurement doc names this residual. The labeller is a fresh context that holds the findings file and the export roots, and not the key.
- **Calibration uses the production path unchanged, in a non-git root.** Seeded documents sit at the assembler's live paths in each export root (`docs/01-plan/features/`, `docs/02-design/features/`, under the source feature's name), with byte-identical paired copies. That works only because the tree has no live copy of any source feature's phase documents (R3), so nothing collides. The wrapper's own root handling is already git-optional on the code side: `_cmd_exec` passes codex `--skip-git-repo-check`, passes grok `--cwd`, and prints `tree delta: n/a (… not a git repo)` for a non-git root. Whether each agent actually accepts the root is the AC-1.6 measurement at S1, not a premise.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| Seed ledger (27 JSON records) and committed seeded copies under `docs/03-analysis/probes/grok-audit-surface/` | data | FR-2 (AC-2.1–2.5) |
| Declared exclusion list, committed and published in the measurement doc | data | FR-2 (AC-2.6) |
| Export-root builder, content scan (refuses `leak:<path>`, one paired-copy exemption) and git reach check (refuses `root_git:<path>`) | probe module | FR-2 (AC-2.6), FR-5 (AC-5.4), FR-6 (AC-6.4) |
| `SMOKE:` line derivation from `AUDITCYCLE:` / `COLLECT:` lines and logs (component named by the design) | probe module or wrapper step | FR-1 (AC-1.7) |
| Prompt-diff check over retained per-pass prompts (report-path mask only) | probe module | FR-3 (AC-3.2) |
| Findings extractor plus blinder (findings file, separate key) plus advisory hints | probe module | FR-4 (AC-4.1, 4.2, 4.4) |
| Scorer: `SEEDSCORE: PASS\|MISS\|INCONCLUSIVE\|UNREADABLE` with per-surface exact fractions | probe CLI | FR-5 (AC-5.1–5.4), FR-4 (AC-4.3, 4.5) |
| Scorer fixture tests under `h-mad/tests/` naming the probe path literally, including one fixture per leak and git-reach trigger and the must-not-refuse exemption fixture | tests | FR-5 (AC-5.5), FR-4 (AC-4.4 hint-invariance), FR-2 (AC-2.2, 2.4, 2.5, 2.6) |
| Three-pass union and evidence-floor tests | tests | FR-8 (AC-8.1, 8.2) |
| Exit-streak and round-cap tests over real-grammar stamps | tests | FR-9 (AC-9.1–9.4) |
| Wrapper three-surface tests with stub agents | tests | FR-10 (AC-10.1–10.3) |
| Teammate-section command correction plus the doc test (section contains `hmad-dispatch audit-cycle`; no tracked `h-mad/**/*.md` pairs `h_mad_audit_cycle.py` with `--surfaces`), RED run recorded first | docs and test | FR-6 (AC-6.2a) |
| SKILL.md AC-9.5 sentence in §"What you NEVER do" | docs | FR-9 (AC-9.5) |
| Operator runbook for S1 and S2 (root build, env unset, commands, timeout derivation, re-dispatch rule) | doc section in the measurement doc | FR-1, FR-2 (AC-2.6), FR-3 |
| `docs/03-analysis/grok-audit-surface.measurement.md` (smoke-only form on `SMOKE: FAIL`; full form otherwise) | doc | FR-1 (AC-1.2–1.4, 1.6–1.8), FR-3 (AC-3.3, 3.4, 3.6), FR-6 (AC-6.1, 6.3, 6.4) |
| `h-mad/references/grok-runtime.md` sentence: AC-1.5 on a scored verdict, the AC-1.8 failure sentence on a smoke failure | docs | FR-1 (AC-1.5, 1.8) |
| SKILL.md AC-6.2 sites: retirement to the measured fractions on PASS/MISS/INCONCLUSIVE, or unmeasured plus pointer plus failure clause on a smoke failure, with a pointer assertion in both sections | docs and test | FR-6 (AC-6.2, 6.3), FR-1 (AC-1.8) |
| SKILL.md first-gate routing, rewording, falsification sentence, doc-test pins (**PASS only**) | docs and test | FR-7 (AC-7.1–7.3), FR-8 (AC-8.3) |
| MISS/INCONCLUSIVE branch evidence | measurement doc line plus section diff | FR-7 (AC-7.4) |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| A tool-using reviewer reads the answer key, git history, or a verbatim copy of a seed's original from the dispatch root | Recall is inflated for whichever surface looks; the reading is worthless and cannot be detected afterwards | Settled by spec AC-2.6: non-git export root, declared exclusions, content scan over all 27 seeds with the one paired-copy exemption, git reach check, GIT_* env unset. Each refusal has an S0 fixture. Residual 3 (absolute-path reads outside the root) stays open and is named in the measurement doc |
| grok or agy refuses the non-git root | No calibration can run in a leak-closed root | Measured at S1 (AC-1.6). A refusal is the named halt `SMOKE: FAIL reason=nongit_root_refused:<agent>`, never a fallback to a git root. A codex refusal drops codex to the codex-unavailable shape |
| A seed's `original` also occurs in the unseeded paired spec, or in another tree file | The root refuses with `leak:<path>` and that document cannot be dispatched | Expected and handled by the scan: re-choose or widen the span, or add the path to the declared exclusion list. Choosing seed spans with the scan run early (S0, against the built roots) surfaces these before S1 |
| The suite floor goes stale, so a deleted pre-existing test hides behind new ones | The no-regression guarantee is quietly false | Floor = collection count measured at the Phase-5c branch point, plus the count of tests this feature adds, re-measured at each task's GREEN. The reading below drifts by construction and is not the floor |
| The FR-1 smoke fails (`truncated`, `vocab_split`, `vocab_missing:<type>`, `no_delivery`, `nongit_root_refused:<agent>`) | No calibration can run | S2 does not start. The smoke-failure branch ships per AC-1.8 (see "The outcome branch"); audit precision stays unmeasured at both SKILL.md sites. Whether to stop routing to grok in the codex-unavailable route is a follow-up the measurement doc records, out of scope here |
| A re-dispatched cycle (AC-3.4) re-runs every surface, including passes that were fine | Which outcome "stands" per surface is ambiguous | The design pins the rule, which per AC-3.4's text is that the whole second cycle stands for every surface |
| The archived scorer test breaks because the probe dir was archived | A red suite after Phase 7 | The test names the probe path literally (see "Where the tests live") |
| Small N gives a decision driven by noise | Promotion on one seed's difference | Exact counts with denominators. Worst-case bounds turn a decision that depends on undecidables into INCONCLUSIVE. The per-phase split is observation only (FR-7) |
| Seed transfer: build-class seeds are easier or harder than real defects | Recall does not transfer to real defects | Transfer residual stated in the measurement doc (AC-6.1); seeds imitate real `ORIGINS` shapes (AC-2.4) |
| A suite sweep picks up the committed seeded copies as live phase documents | Unrelated doc tests go red or skew | Not measured here. The design measures, with a stated command over `git ls-files`, whether any test or script globs `*.plan.md` / `*.design.md` / `*.impl-plan.md` outside `docs/01-plan/features` and `docs/02-design/features`, and it names the seeded copies so that no such glob matches |

## Convention Prerequisites
- Feature branch off `main` at Phase 5c. S1 and S2 run in non-git export roots built from the calibration sha, outside every git work tree, never in the branch's working tree or a worktree. Seeded documents and the export roots are never merged into `main` (spec NFR Security), and the committed seeded copies live only under the probes directory.
- Test interpreter on this machine: `/opt/homebrew/opt/python@3.14/bin/python3.14`. `python3` resolves to 3.15, which has no pytest (`python3 -m pytest --version` printed `No module named pytest` at `1a470339`).
- grok 1.0.62 and agy on PATH for S1 and S2. codex is optional, and when it is absent or refuses the root, the reference ceiling is published as not run.
- Every token consumer reads the token line, never `$?`: `SMOKE:`, `SEEDSCORE:`, `AUDITCYCLE:`, `ASSEMBLE:`, `COLLECT:`, `EXIT:`, `ROUNDS:`, `GATE:`.
- The escalation-literal rule of the inline plan protocol applies to every document this feature writes.

## Success Criteria
- All ACs in the spec that are reachable on the branch taken pass automated tests. The unconditional S0 set (including AC-6.2a and AC-9.5) is green on every branch. On PASS that also includes AC-7.1–7.3 and AC-8.3. On MISS or INCONCLUSIVE, AC-7.4's evidence is present instead. On a smoke failure, the AC-1.8 deliverables are present and no `SEEDSCORE:` line exists.
- Every AC-5.5 fixture is green, and each D3 branch and the tie boundary is driven by its own fixture with no undecidables: strictly lower fabrication with equal recall → PASS; equal fabrication with strictly greater recall → PASS; full tie → MISS; equal fabrication with lower recall → MISS; `1/4` against `2/8` with equal recall → MISS.
- Every `leak:<path>` and `root_git:<path>` trigger refuses when run alone, and the byte-identical own-source exemption fixture does not refuse.
- `SEEDSCORE:` reproduces from the committed ledger, labels and key with the AC-6.4 re-run command and no dispatch.
- No pre-existing test is lost. The collection count at each GREEN is at least the Phase-5c branch-point count plus this feature's added tests.

### Readings (stamped at `1a470339`; each drifts as noted)
| # | Claim | Reading | Unit | Drifts? |
|---|---|---|---|---|
| R1 | Suite collection | `6733 tests collected` | tests | Yes, with every test commit. Re-measure at the Phase-5c branch point; that reading, not this one, is the floor |
| R2 | Largest assembled document set per phase (the assembler pairs plan → spec, design → spec + plan, impl-plan → design only; no prompt holds all four) | agy-coder-fallback design+spec+plan = `317110`, the maximum over all 9; next is agy-coder-fallback impl+design = `270854` | bytes of inlined documents | No: archived files are frozen. Bytes are an upper bound on chars for the 1,048,576-char ceiling; the template and invariants add to the prompt and are not counted here |
| R3 | Live copies of a source feature's phase docs | `0` | tracked file paths | Zero because all three features were archived, which moves their files. This is load-bearing: a later un-archive would collide with the export-root placement |
| R4 | Name mentions outside the archive (AC-2.6 residual 4, not a leak) | `94` | tracked files | Yes: handoffs and this feature's own docs add to it. The probe does not gate on it |
| R5 | Tracked files in `docs/03-analysis/agy-coder-fallback.authoring/` (on the declared exclusion list) | `124` | tracked files | Frozen unless that directory is edited |
| R6 | Distinct lines of 80 or more chars from agy-coder-fallback's plan, design and impl-plan (first 400 in sort order) that appear verbatim in R5's directory | `135 of 400` | distinct lines | Frozen with R5. This is a sample, not a census: it shows original spans are recoverable from quoting files, which is why the content scan, not the named list, is the class closer |
| R7 | grok vocabulary at both sites | the same seven types: `thought text available_commands tool_call tool_call_update usage end` | distinct type names | AC-1.2 re-checks this at the smoke sha |
| R8 | `surfaces` in `h_mad_audit_cycle.py` | `0` | matching lines | The premise behind AC-6.2a |
| R9 | grok version | `grok 1.0.62 (1474f9cbdd91) [stable]` | version string | Yes, on upgrade. AC-3.6 re-records it |
| R10 | `h_mad_audit_cycle.py` followed by `--surfaces` within one line or across one line break, over tracked `h-mad/*.md` | `1` occurrence (`h-mad/SKILL.md`), `32` files scanned | occurrences; files | Yes: AC-6.2a's correction takes it to 0, and the new doc test pins that 0 |
| R11 | Tracked symlinks; tracked gitlinks | `0` symlinks; `3` gitlinks (`beautiful_prose`, `drawio-skills`, `humanizer`) | tracked entries | Incidental zero: the scan refuses any symlink in a root whatever this count is. The gitlinks are AC-2.6 residual 5 |

Commands, run from the repository root:

```bash
# R1
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest --collect-only -q h-mad/tests | tail -1
# R2 (per-phase sums of the documents the assembler inlines)
for f in audit-report-docs-copy tdd-gate-fail-opens agy-coder-fallback; do d=$(ls -d docs/archive/*/$f); s=$(wc -c < $d/$f.spec.md); p=$(wc -c < $d/$f.plan.md); g=$(wc -c < $d/$f.design.md); i=$(wc -c < $d/$f.impl-plan.md); echo "$f plan+spec=$((p+s)) design+spec+plan=$((g+s+p)) impl+design=$((i+g))"; done
# R2 pairing: the slots block in assemble()
grep -n -A6 'if phase in ("plan", "design"):' h-mad/scripts/h_mad_assemble_audit.py
# R3
git ls-files docs/01-plan/features docs/02-design/features | grep -E 'audit-report-docs-copy|tdd-gate-fail-opens|agy-coder-fallback' | wc -l
# R4 (grep prints "Is a directory" for the three gitlinks on stderr; they are not counted)
git ls-files -z -- . ':(exclude)docs/archive' | xargs -0 grep -l -E 'audit-report-docs-copy|tdd-gate-fail-opens|agy-coder-fallback' | wc -l
# R5
git ls-files docs/03-analysis/agy-coder-fallback.authoring | wc -l
# R6 (bash)
P=docs/archive/2026-10/agy-coder-fallback; n=0; t=0; while IFS= read -r l; do t=$((t+1)); grep -rqF -- "$l" docs/03-analysis/agy-coder-fallback.authoring && n=$((n+1)); done < <(cat $P/agy-coder-fallback.plan.md $P/agy-coder-fallback.design.md $P/agy-coder-fallback.impl-plan.md | awk 'length($0)>=80' | sort -u | head -400); echo "$n of $t"
# R7
grep -n "^_GROK_TYPES_RE=" h-mad/scripts/hmad-dispatch.sh; grep -n -A1 "^_GROK_TYPES = " h-mad/scripts/h_mad_review_evidence.py
# R8
grep -c "surfaces" h-mad/scripts/h_mad_audit_cycle.py
# R9
grok --version
# R10
git ls-files -z 'h-mad/*.md' | xargs -0 python3 -c 'import re,sys
rx=re.compile(r"h_mad_audit_cycle\.py[^\n]*\n?[^\n]*--surfaces"); n=0
for p in sys.argv[1:]:
  k=len(rx.findall(open(p,encoding="utf-8",errors="replace").read())); n+=k
  k and print(p,k)
print("occurrences",n,"files",len(sys.argv)-1)'
# R11
git ls-files -s | awk '$1=="120000"' | wc -l; git ls-files -s | awk '$1=="160000"{print $4}'
```

## Out-of-Scope (confirmed from spec)
- grok as Phase-5 implementer, as doc author, or as the subject of a TDD write gate (D1).
- The host-mode adapter: hooks, `spawn_subagent`, the TDD gate, session id, and the 1.0.41 mapping line (D4).
- Replacing the doc-auditor delta review, or agy, with grok.
- Replaying the gateway-consolidation corpus.
- Changing the codex-unavailable route, or adding a `grok_status` state field, including after a failed smoke (AC-1.8 follow-up).
- Seeding measurement-class, prose or ordering defects (AC-2.1 residual).
- Preventing a reviewer from reading outside the export root by absolute path (AC-2.6 residual 3).

## Next Steps
1. **Spec v1.2 answered the four items plan v1.0 filed** (leak control, the AC-3.2 mask, the smoke-failure branch, the AC-8.3/AC-9.5 staging) and folded the pre-existing teammate-section command into AC-6.2a. Nothing is owed by the spec at this revision.
2. **The design pins**: the scorer test module name and fixture layout (including each leak and git-reach trigger alone, and the exemption fixture); the AC-6.2a doc-test module; the export-root builder, its parent directory, the exclusion-list file format and the scan normaliser; the component that derives the `SMOKE:` line; prompt retention under `HMAD_AUDIT_STEM_DIR` outside every export root; the probe's diff mechanism; the AC-3.4 per-surface "stands" rule; the seeded-copy file names, and the glob measurement that clears them; and whether a test asserts the MISS-branch state of §"Never gate on one audit pass".
3. User approves v1.1 → plan audit cycle (first gate `codex` + `agy` per today's routing) → Phase 4 design.

## Version History
- v1.0: Initial plan draft from spec v1.1 (`7b76f539`). Stages the work S0–S4, with the routing (FR-7) conditional on `SEEDSCORE: PASS` and the live dispatches operator-run, not CI. Settles that scorer tests live under `h-mad/tests/` and name the probe path literally for `probe_readers`. Settles the AC-3.2 mask at report-path lines only, matching the wrapper's `prompt_divergence` rule. Files three spec-owed leak members for AC-2.6.
- v1.1: Brought into line with spec v1.2 (`1a470339`). Leak control is settled by AC-2.6 and staged, not blocking: non-git export root per document, declared exclusions, content scan over all 27 seeds with the one own-source paired-copy exemption, git reach check; `root_git:<path>` added to the UNREADABLE causes. S1 adds the agy (and codex) non-git root smoke dispatches and the derived `SMOKE:` line; new smoke-failure branch (no calibration, no SEEDSCORE, audit precision stays unmeasured at both SKILL.md sites). AC-6.2a staged at S0. R2 corrected from a four-document sum (468756) to the per-phase maximum 317110 bytes. Readings re-stamped at `1a470339`; R10 and R11 added.
