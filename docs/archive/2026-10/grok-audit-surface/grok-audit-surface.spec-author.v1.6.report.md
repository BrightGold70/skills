SPEC-AUTHOR: DONE version=v1.6 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.spec.md lines=290 sha256=7790404804eede0b1783957f3ff539c64add8b4508c61f506d561576c7502ff0

## premises verified (at b4ba87fc)
- h_mad_audit_cycle.py collect delivered values: `grep -n 'return "(out|report-file|none)"'` -> report-file (249,250), out (513), none (478,517); UNSCORABLE_PREFIX "unscorable:" (81). Four forms.
- render: `sed -n 1018,1066p` -> delivered=<v,...> on the AUDITCYCLE line when results non-empty, both branches; UNVERIFIED branch returns before the Premise checklist.
- premise_items/render: `sed -n 1001,1017p;1072,1082p` -> "Premise checklist:" + one item per finding with one-line text; else "Premise checklist: empty". Confirms D-d.
- COLLECT printers: `grep -n 'COLLECT: ' h_mad_audit_cycle.py h_mad_collect_report.py` -> printed only in h_mad_collect_report.py (123,143,149); audit_cycle hits are a docstring (362) and a comment (892). Confirms D-e.
- grok-truncated -> UNVERIFIED low_evidence_unmeasurable: `grep -n` -> h_mad_audit_cycle.py 596, 984, 988. Basis for the AC-1.7 coupled-reason axis.
- bfb6960a: `git log -1 bfb6960a` -> "plan v1.2 - answer gating round 1" (sha-remap row 5b2df07b).
- Old shas in the spec: `grep -E '946ffc5|5b2df07|611c299|b085ad7'` -> 1 line (v1.5 VH, "5b2df07"); annotated with bfb6960a. The filename of the delta review still carries 5b2df07, so the old token stays and the new sha is added beside it.

## findings applied
- D-a / codex AC-5.4: AC-5.4 closed list re-stated with every trigger named: placement violations under seed_rebuild; cycle_token's seven triggers; new list_changed:<oid> (oid or `unrecorded`); new internal:<ExceptionName>. Stated count: fifteen reason forms.
- D-b / codex AC-5.3: explicit precedence (seeds_undetected, PASS, MISS, undecidable_flips) with a worked example.
- D-c / codex AC-5.1: every exit carries a final token; MISS reason closed to bar_missed, INCONCLUSIVE to two reasons.
- D-d / agy must 1: AC-2.7 names reports, pass logs, kept prompts, captured agent output, captured wrapper stdout.
- D-e / codex smoke-fixture must: AC-1.7 inputs no longer name COLLECT:. The coupled-reason axis is stated with two kinds. The fixture rule now reads "plant one trigger, assert the exact reason list": no_delivery asserts `no_delivery,nongit_root_refused:grok`. The predicate is not weakened.
- D-f: AC-1.8 cites the smoke commit and the list commit/blob. AC-3.6 cites the list commit and blob. AC-2.7 defines the smoke commit.
- D-g / codex AC-1.3, AC-1.6: AC-1.3 counts delivered=out when the report is collected and the gate scores it.
- D-h: AC-4.5 unchanged (the wording is unambiguous: should-fix hits published separately, outside the bar).
- codex AC-2.2: per-document class-multiset check made explicit with the balanced counterexample; fixture added.
- codex AC-2.7 (main leak on smoke failure): trigger (i) uses the smoke commit when there is no score sha; "When it runs" clause added; AC-1.8 reworded to "no SEEDSCORE: verdict exists or is published".
- codex AC-4.3 (duplicate labels): label:<id> covers identical and conflicting duplicates; fixtures added.
- codex key-surface reassignment: key_mismatch covers duplicate ids and key rows checked against the recorded dispatch command and pass; fixture added.
- codex should-fix (ledger/seeded identity across shas): files present at the calibration sha must be byte-identical at the smoke commit and score sha -> calibration_drift:<path>; fixtures added. AC-6.4 step updated.
- Additional closures, found while sweeping (same reasons the design already uses): ledger_counts names an unparseable line, a missing field, a source outside the nine documents, and an empty original/expected; leak:<path> names a tar member leaving the root and an exclusion-list grammar violation.
- Old sha restamp: v1.5 VH line annotated with bfb6960a.

## values swept
- COLLECT: `grep -n -o -E '.{0,40}COLLECT.{0,40}'` -> 4 lines, all v1.6 text that says COLLECT: is not an input (Premises L43, AC-1.3, AC-1.7). No remaining COLLECT input.
- two-sha / Two shas: `grep -n -o -i -E '.{0,60}(two-sha|two shas).{0,60}'` -> AC-1.8, AC-2.7 heading, AC-5.4 calibration_drift, AC-6.4 (updated), VH v1.4/v1.5 (history, left as is).
- "no score sha"/"at the calibration sha when": the old trigger-(i) wording is gone (grep found no hit for "at the calibration sha when"); remaining hits are AC-1.8 and AC-2.7, consistent with the new text.
- Calibration data list: also swept into NFR Security and FR-6's stamp (smoke commit, list commit/blob).
- AC-5.4 count: awk over the AC-5.4 block -> 14 bullets; calibration_drift's bullet holds 2 forms, so 15 reason forms. The document states fifteen.
- cycle_token triggers (1)-(7) = seven, as stated in AC-5.5. seed_rebuild has four placement clauses, as stated in AC-5.5.
- internal:<ExceptionName>: `grep -c` -> 3 lines (AC-5.1, AC-5.4, AC-5.5).

## contradictions found
- Design D11 treated delivered=out as no_delivery. D-g reverts that: AC-1.3 now says out counts.
- Design D1 ("one refusal vocabulary: SEEDSCORE in every mode except smoke") contradicts D9 and Error Handling (COMMIT:/RECORD:). AC-5.1 now requires one token grammar per mode and leaves the choice to the design. Not resolved in the spec.
- Design Error Handling's no-token traceback branch contradicts the new AC-5.1 and AC-5.4 internal:<ExceptionName>.
- Design D5 "match=no is not a refusal": AC-5.4 now has list_changed:<oid>.
- Design D3 "auditcycle.txt carries no seed text" is false (Premises v1.6). AC-2.7 now names it.

## placeholder scan
PRECHECK: PASS issues=0. Advisories kept:
- STALESHA on the premise-block shas: these are stamped readings, so the old shas are correct where they stand.
- PATH on the measurement doc: the file is new and does not exist yet.
- COUNT L32: from an earlier revision, untouched.
- COUNT L130 and L178: false positives ("AC-5.5 fixture tests"; "nine AC-2.4 fields").

## owed to design-author (one line each; not touched)
- D11 no_delivery: accept delivered=out with a collected, gate-scored report (AC-1.3 v1.6); fix the D11 smoke ordering fixture to `truncated,no_delivery,nongit_root_refused:grok` per AC-1.7 "Coupled reasons".
- D1 vs D9/Error Handling: pick one token grammar per mode (AC-5.1).
- Error Handling: replace the no-token traceback with SEEDSCORE: UNREADABLE reason=internal:<ExceptionName> (SMOKE: maps to its two reasons).
- D3: move auditcycle.txt (and p<i>.out.txt) into the calibration-data set and main_leak trigger (i); name each excluded file and why (AC-2.7).
- D4: per-document class-multiset check plus the balanced counterexample fixture; ledger_counts on a source outside the nine documents.
- D5/D9: list_changed:<oid> refusal in rescore (oid or `unrecorded`); a retained root record per cycle (codex "root provenance has no declared recording input").
- D9: byte-identity of calibration-sha files at the smoke commit and score sha (calibration_drift:<path>); a main-leak path that needs no score sha, for smoke FAIL, using the smoke commit.
- D12: key_mismatch on duplicate ids and on key rows that disagree with the cycle's command and pass; shuffle_seed record handling (agy nit).
- D13: label:<id> on duplicate label records; MISS reason=bar_missed and INCONCLUSIVE reasons as AC-5.1 now closes them (already consistent).
- AC-4.5 should-fix publication path (D-h); FR-6 per-phase and per-class producer; AC-6.1 transfer residual in S3; AC-6.3 INCONCLUSIVE text branch; AC-7.2 availability fallback text and tests.
- agy: no exported tree containing s2/ when extract runs; candidate-fabrication must map live paths back to the calibration tree.
- M4: drive the real collector for both delivery directions, then check the gate separately (codex).
- Classify connection: discriminate it through the production path (codex).
- Should-fix items: P-row census unit (codex); the smoke input_unparseable over-refusal on agy/codex/assemble-halt (agy); check-ledger --repo vs --tree CLI split (agy); the stamps test helper (agy, also impl-plan).
- Overview nit: "every live root serves one cycle" holds only for S2.

## owed to plan-author (exact plan text affected)
- Plan "The component is the FR-5 probe's smoke mode": "It reads the S1 passes' `AUDITCYCLE:` and `COLLECT:` lines and their pass logs" -> drop COLLECT:, name delivered= and the collected reports' GATE: tokens (spec AC-1.7 v1.6).
- Plan "What counts": "These lines carry no seed text, so they are not calibration data under the catch-all" -> false for the captured wrapper stdout (Premise checklist). Spec AC-2.7 now names auditcycle.txt, reports, logs, prompts and captured agent output explicitly. The plan's "filed to the spec, Next Steps" item is now closed.
- Plan "Which list version": "Residual: no AC-5.4 reason refuses a mismatch, so this check is an operator step, not a probe refusal (owed to the spec and design, Next Steps)" -> AC-5.4 now has list_changed:<oid>, so the check becomes a probe refusal.
- Plan "The shas the measurement doc must cite" -> add the smoke commit (AC-2.7, AC-3.6) and the list blob id.
- Plan "`SEEDSCORE: UNREADABLE` -> nothing in S3 or S4 ships" enumerates reasons -> add list_changed:<oid> and internal:<ExceptionName>.
- Plan Next Steps item 1 ("Owed by the spec") -> both parts are now answered by spec v1.6.
- Plus the design-author's existing plan list (interpreter, R13, S0b root count, G4, old shas), not re-checked here.

## Quotable ACs (verbatim from the spec at the sha above)

### AC-1.3

  - AC-1.3: A pass **delivers a report** when its value in the `delivered=` field of the cycle's `AUDITCYCLE:` line is `report-file` or `out`, AND `h_mad_audit_gate.py`, run on that pass's collected report, prints `GATE: PASS` or `GATE: FAIL`. Both forms count: `report-file` is the agent's report file, and `out` is a complete report that the collector extracted from the agent's captured output, wrote as the collected report, and the gate then scored. A pass whose value is `none` or `unscorable:<reason>`, whose collected report is absent, or whose gate run prints any other token, has not delivered. The `delivered=` field is the only delivery input on the audit-cycle path, which prints no `COLLECT:` line (Premises). A verdict word read from grok's final message, without a collected report that the gate scored, does not count.

### AC-1.7

  - AC-1.7: The smoke ends on one line in the measurement doc: `SMOKE: PASS` or `SMOKE: FAIL reason=<r>[,<r>…]`. It is derived from each S1 cycle's recorded `AUDITCYCLE:` line (its verdict word, its `delivered=` field and its `Effort:` block), the `GATE:` token of each delivered pass's collected report (AC-1.3), and the pass logs, never typed by hand, and never from a `COLLECT:` line, which the audit-cycle path does not print (Premises). The design names the component that derives it. `reason=` lists every failing check, in this order:
    - `truncated`: the grok log is `grok-truncated` (AC-1.1).
    - `vocab_split`: `_GROK_TYPES_RE` and `_GROK_TYPES` differ from each other at the smoke sha (AC-1.2).
    - `vocab_missing:<type>`: `end`, `tool_call` or `tool_call_update` is absent from the live log, one reason per missing type (AC-1.2).
    - `no_delivery`: the AC-1.3 evidence is absent for the grok pass.
    - `nongit_root_refused:<agent>`, where `<agent>` is `grok` or `agy` (AC-1.6).

    There is no other reason value. An out-of-vocabulary type is published, and it is not a reason (AC-1.2).

    **Coupled reasons.** Each reason is read from its own observation: `truncated` from the grok pass's `Effort:` item, `vocab_split` from the two vocabulary sources, `vocab_missing:<type>` from the log's distinct `type` set, `no_delivery` from the AC-1.3 evidence, and `nongit_root_refused:<agent>` from that surface's AC-1.6 acceptance. The axis is *one reason whose trigger implies another reason's trigger*, and it has exactly two kinds:
    - **Implied by this spec's own definitions**, which no fixture can separate. There is one member: `no_delivery` implies `nongit_root_refused:grok`, because grok accepts the root only when its pass delivers a report (AC-1.6 uses the AC-1.3 evidence). Every grok `no_delivery` is therefore printed as `no_delivery,nongit_root_refused:grok` (with any other failing reasons in their places in the order above).
    - **Coupled only through an authority on real runs**, which a synthetic fixture can separate because each reason reads its own observation: a `grok-truncated` log has no `end` event (so `truncated` comes with `vocab_missing:end`) and gives `UNVERIFIED reason=low_evidence_unmeasurable:pN` (so it comes with `nongit_root_refused:grok`). The members are `truncated`, `vocab_missing:end` and `nongit_root_refused:grok`.

    Residual: a coupling introduced later by a change to `scan_grok`, `combine` or `collect` is of the second kind and is not listed here until the spec is revised.

    **Exit contract**, in the same style as AC-5.1: the component prints its token on stdout, and callers read the token, never `$?`. `SMOKE: PASS` and `SMOKE: FAIL reason=…` are both verdicts, and both exit 0. A non-zero exit is reserved for an operational error, where the inputs could not be read. In that case the component exits 2 and prints `SMOKE: UNREADABLE reason=<r>`. That token carries neither PASS nor FAIL, and `<r>` is exactly one of two values:
    - `input_missing:<path>`: a pass log, a cycle's recorded `AUDITCYCLE:` line, or a delivered pass's collected report, that the derivation needs, is absent.
    - `input_unparseable:<path>`: such an input is present, but it cannot be parsed.

    There is no other UNREADABLE reason. An UNREADABLE smoke is not a smoke failure, and it is never written to the measurement doc as `SMOKE: FAIL`. S2 does not start, and nothing in "Delivery by outcome" ships on its account. The operator restores the input and derives again from the same passes. If the passes themselves are lost, the operator runs a new smoke, which is a new reading.

    **Fixtures.** Each of the two UNREADABLE reasons, `PASS`, and each `FAIL` reason gets its own fixture test, which plants that one reason's trigger and no other, and asserts the exact `reason=` list the component prints. For every reason except `no_delivery`, that list is the reason alone. The `no_delivery` fixture plants only an absent grok delivery (its cycle not `UNVERIFIED`) and asserts exactly `reason=no_delivery,nongit_root_refused:grok`, the coupling of the first kind above. `nongit_root_refused:grok` has its own fixture, in which grok delivers on an `UNVERIFIED` cycle, and it asserts exactly `reason=nongit_root_refused:grok`, with no `no_delivery`. The second-kind members (`truncated`, `vocab_missing:end`, `nongit_root_refused:grok`) each get a fixture that plants that one observation alone, even though no real run produces it alone.

### AC-1.8

  - AC-1.8: **What ships when the smoke fails.** S2 does not start. No calibration runs, no findings are labelled, and no `SEEDSCORE:` verdict exists or is published. (The AC-2.7 main leak check still runs before the measurement doc is committed; a refusal it prints blocks that commit and is not a reading.) What ships:
    - The measurement doc `docs/03-analysis/grok-audit-surface.measurement.md`, holding the `SMOKE: FAIL` line, the AC-1.2 vocabulary table, the AC-1.4 `RESOLVED-MODEL` line and wall time, and the AC-1.6 acceptance outcome per surface. It cites the calibration ref, the full calibration sha the smoke's export root was built from, the full sha of the smoke commit that holds the S1 records (AC-2.7, "Two shas, and the smoke commit"), and the exclusion-list commit and blob the root was built with (AC-3.6), and there is no score sha. The smoke commit is what lets the smoke be derived again from the same passes. It holds no recall or fabrication figure, and it says so.
    - `h-mad/references/grok-runtime.md` §"Version and compatibility" gains one sentence: the audit path re-smoke against grok 1.0.62 failed, with the `reason=` values, naming the measurement doc. The AC-1.5 "re-smoked" sentence does **not** ship, and the 1.0.41 sentence stays unchanged.
    - In `h-mad/SKILL.md`, both AC-6.2 sites keep audit precision in grok's **unmeasured** list. Each gains the measurement-doc pointer and one clause saying that the 1.0.62 audit-path smoke failed. D3's "'Unmeasured' is retired either way" ranges over the three scored verdicts (PASS, MISS, INCONCLUSIVE), and on a smoke failure there is nothing to retire it with.
    - The AC-6.2 correction of the teammate-section command, and AC-9.5, ship as on every other branch (see "Delivery by outcome").
    - The codex-unavailable route itself (`--surfaces agy,grok`) is not changed by this feature (Out-of-Scope). Whether to stop routing to grok after a failed audit-path smoke is a follow-up, and the measurement doc records it as one.

### AC-2.2

  - AC-2.2: Class distribution. Number the documents 1 to 9 in the order the source list above gives them (feature order, then plan, design, impl-plan). Document k omits class `((k−1) mod 4) + 1` and carries one seed of each of the other three. That yields C1 = 6, C2 = 7, C3 = 7, C4 = 7, which sums to 27. The probe derives these counts from the ledger, never carries them, and refuses a ledger whose counts differ. The check is per document, not only on the totals: for every k, document k's multiset of seed classes must equal exactly the three classes other than `((k−1) mod 4) + 1`, one each. A ledger that meets every document size and every total but gives one document a repeated class (for example d1 as C2, C2, C4 and d4 as C1, C3, C3, which keeps the totals at 6/7/7/7) refuses `ledger_counts`.

### AC-2.7

  - AC-2.7: **Where calibration data lives** (operator decision 2026-10-18, answering plan audit cycle 2). *Calibration data* means these artifacts, named explicitly:
    - the ledger (AC-2.4) and the seeded copies (AC-2.5);
    - the findings file and the id-to-surface key (AC-4.2), and the labels (AC-4.3);
    - for every S1 and S2 cycle: every pass's report (the report file the agent wrote and the collected copy the scorer reads), every pass log, every kept prompt (the assembled prompt of each pass, which inlines the seeded document), every pass's captured agent output, and the cycle's captured wrapper stdout (`auditcycle.txt`). The wrapper stdout counts because, on a `PASS` or `FAIL` cycle, it prints a `Premise checklist:` carrying the one-line text of every finding of every pass (Premises), and those findings quote seeded spans.

    Any other file that carries a seed's `seeded` span or `expected` sentence, or the text of a finding filed on a seeded document, also counts as calibration data and follows the same rule. A file is outside the set only when it carries none of these; the design names each such file and why (for example the recorded dispatch command), and the catch-all still reaches any of them that turns out to carry such text.
    - **The branch.** Calibration data is committed only on the dedicated branch `calibration/grok-audit-surface`, pushed to origin as `refs/heads/calibration/grok-audit-surface`, under `docs/03-analysis/probes/grok-audit-surface/calibration/` in that branch's tree. The branch starts from a `main` commit that already holds the S0 probe. It is never merged into `main` or into any branch that is merged into `main`. It is never rebased, force-pushed or deleted, and archiving this feature on `main` leaves it alone. A later calibration adds commits to it and never rewrites earlier ones.
    - **What `main` holds.** `main` holds the FR-5 probe, its AC-5.5 fixture tests and the FR-6 measurement doc, and no calibration data. Every fixture is synthetic, made of invented text, and never a copy or excerpt of a real seed, ledger record, finding, key or label. The measurement doc cites the calibration data by ref and sha and never quotes it.
    - **Two shas, and the smoke commit.** The *calibration sha* is the branch commit that holds the ledger and the seeded copies. Every AC-2.6 export root is built from it before any dispatch, the FR-1 smoke included. The *smoke commit* is the next branch commit, which adds the S1 cycle records (each S1 cycle's calibration data listed above, its captured wrapper stdout with its `AUDITCYCLE:` line, and the record of the root it ran in), under the calibration directory. It is made on every smoke outcome that derives to `PASS` or `FAIL`. The *score sha* is the later branch commit, descending from the smoke commit, that adds the findings file, the key and the labels, and every FR-3 cycle's records, including its captured wrapper stdout and so its recorded `AUDITCYCLE:` line (the wrapper's stdout token line for that cycle, which AC-3.2 and AC-6.4 read), all under the calibration directory. Both the smoke commit and the score sha must descend from the calibration sha and differ from it only under `docs/03-analysis/probes/grok-audit-surface/calibration/`, so an export root rebuilt from any of them is the same root. Within that directory, later commits only add: every file present at the calibration sha (the ledger and every seeded copy) is byte-identical at the smoke commit and at the score sha, so the ground truth the roots were built from is the ground truth that is scored. The probe refuses with `calibration_drift:<path>` when a path outside that directory differs, or when a file present at the calibration sha differs or is absent at the later commit, naming the first such path in sorted order, and with `calibration_drift:not_descendant` when the later commit does not descend from the calibration sha. A smoke failure (AC-1.8) produces no score sha; the smoke commit is then the branch tip, and it is cited.
    - **Main leak check.** The probe scans every blob in the tree of the commit checked out where it runs (`HEAD`, read through `git ls-tree -r`, never the work tree). The commit it scanned is printed and recorded in the measurement doc. It refuses with `main_leak:<path>` on any one of three triggers: (i) the blob's sha256 equals that of a calibration data file at the score sha, or, when there is no score sha (a smoke failure), at the smoke commit; (ii) after AC-2.6 whitespace normalisation, the blob contains any seed's `expected` sentence; (iii) the blob contains any seed's normalised `seeded` span, unless that span also occurs in the normalised archived source document of the same seed. Residuals, stated exactly: (1) a `seeded` span that also occurs in its own archived source, which (iii) cannot tell apart from archive text; (2) a partial copy of a calibration data file that carries no whole `seeded` span and no whole `expected` sentence; (3) content that is not UTF-8 text in its stored form, as in AC-2.6 residual (2); (4) uncommitted files in the work tree and commits other than the scanned one; (5) calibration objects fetched into a local clone's object store, which are not in `main`'s tree and which the non-git export roots cannot reach (AC-2.6 route (b)). **When it runs**: on every outcome that publishes a measurement doc, before that doc is committed to `main`, and again inside the AC-6.4 re-run. On a smoke failure there is no score sha and no re-run, so the check runs against the smoke commit's calibration data, by a probe path that needs no score sha, and the measurement doc records the commit it scanned exactly as on the other outcomes. On any outcome, a `main_leak:<path>` refusal blocks the commit of the measurement doc to `main`; the leak is removed from `main` and the check is run again. A refusal is never published as a reading.
    - **Ref failure modes.** The probe reaches calibration data only through the ref. It refuses with `calibration_ref:<kind>`, and `<kind>` takes exactly one of four values:
      - `fetch_failed`: `git ls-remote` or the fetch of `refs/heads/calibration/grok-audit-surface` from origin did not complete (network, authentication, or no `origin` remote).
      - `ref_absent`: origin answered, but it has no such ref.
      - `sha_unknown:<sha>`: after the fetch, a cited sha does not resolve to a commit.
      - `not_on_ref:<sha>`: a cited sha is neither the fetched ref's tip nor an ancestor of it, which means the branch was rewritten.

      There is no other kind. On any of them, no reading is reproduced and the published reading stays unverified. The operator restores the ref, and never edits the measurement doc's shas to make them fit.

### AC-3.6

  - AC-3.6: The calibration ref `refs/heads/calibration/grok-audit-surface`, the full 40-hex calibration sha, smoke commit and score sha (AC-2.7), the full 40-hex sha of the exclusion-list commit (the `main` commit whose committed AC-2.6 declared exclusion list every S1 and S2 export root was built with) together with that list's blob id, the grok, agy and codex versions, and each surface's `RESOLVED-MODEL` line are recorded once in the measurement doc. Every export root records the list blob id it was built with, and those records go to the branch with the cycle that ran in the root (AC-2.7); the AC-6.4 re-run compares them with the list it reads (AC-5.4 `list_changed:<oid>`).

### AC-5.1

  - AC-5.1: The probe's score ends on one token line: `SEEDSCORE: PASS|MISS|INCONCLUSIVE|UNREADABLE`, with `reason=` on every verdict other than PASS. The reason values are closed: MISS carries `reason=bar_missed` and no other; INCONCLUSIVE carries exactly one of `reason=seeds_undetected` or `reason=undecidable_flips` (AC-5.3); UNREADABLE carries exactly one AC-5.4 reason. It exits 0 on PASS, MISS or INCONCLUSIVE and 2 on UNREADABLE, and callers read the token, never `$?`. **Every exit carries a final token.** Every invocation of the probe, in every mode and on every path out of it (an exception that escapes the mode's own checks included), ends on exactly one token line on stdout; there is no exit without one. An unexpected failure that no listed reason names is `SEEDSCORE: UNREADABLE reason=internal:<ExceptionName>` (AC-5.4) and exits 2, with the traceback on stderr only. The smoke's token is `SMOKE:` (AC-1.7), whose unexpected failures map to its own two UNREADABLE reasons. Every other mode has one token grammar, which the design names, and no mode prints two grammars.

### AC-5.3

  - AC-5.3: Verdict rules are computed with exact rational comparison and no rounding. "D3 holds" means the amended D3 predicate is true: `(fab_grok < fab_agy AND recall_grok ≥ recall_agy) OR (fab_grok = fab_agy AND recall_grok > recall_agy)`. Equality of fabrication rates is equality of the reduced rationals (`0/0` compares as zero, AC-5.2), so `1/4` and `2/8` are equal. A full tie on both quantities makes the predicate false.
    - **PASS**: D3 holds when every one of grok's UNDECIDABLE is counted as fabricated and every one of agy's is counted as not fabricated.
    - **MISS** (`reason=bar_missed`): D3 fails when the opposite worst case is taken (grok's undecidables counted as not fabricated, agy's as fabricated).
    - **INCONCLUSIVE**: covers every other case, with exactly one of two reasons. `reason=seeds_undetected` applies when no surface, codex included, hit any seed, which means the seeds measure nothing. `reason=undecidable_flips` applies to every remaining case, in which the two worst cases disagree.

    **Precedence.** The verdict is decided in this order, and the first rule that applies wins: (1) `seeds_undetected`; (2) PASS; (3) MISS (`reason=bar_missed`); (4) `undecidable_flips`. **`seeds_undetected` outranks PASS and MISS**: when no surface hit any seed, the verdict is `INCONCLUSIVE reason=seeds_undetected` even when the PASS rule or the MISS rule also holds. For example, zero hits on every surface with grok's pessimistic fabrication rate strictly below agy's optimistic one satisfies the PASS rule (`0 ≥ 0` on recall), and it scores `INCONCLUSIVE reason=seeds_undetected`, never `PASS`.

### AC-5.4

  - AC-5.4: UNREADABLE reasons, all fail-closed. **The list is closed**: these fifteen reason forms are the only ones, and each names every trigger it covers.
    - `ledger_counts` (AC-2.2): the per-document class rule or a derived total fails; or a ledger line does not parse as one JSON object, or a record lacks one of the nine AC-2.4 fields; or a record's `source` is not one of the nine FR-2 documents (which also keeps every seed out of the paired documents, AC-2.3); or a seed's `original` or `expected` is empty (an empty needle would match every file).
    - `ledger_origin` (AC-2.4): a record's `origin` is outside `ORIGINS`.
    - `seed_rebuild` (AC-2.5, AC-2.3): the re-derived seeded document differs from the committed seeded copy by any byte; or a seed's `original` does not occur exactly once in its archived source; or an **AC-2.3 placement violation**: two seeds of one document in the same `##`/`###` section, a seed under `## Version History`, a record whose `section` does not name the heading its span sits under, or a `seeded` span that does not occur exactly once in its seeded document.
    - `leak:<path>` (AC-2.6): a content-scan hit; a symlink in the root; an exported tree member that would land outside the root; or a line of the declared exclusion list outside the list's grammar (the path is then the list's own path).
    - `root_git:<path>` (AC-2.6 git reach check).
    - `must_count_mismatch:<report>` (AC-4.1).
    - `label:<id>` (AC-4.3): a finding with no label; two or more label records for one id, whether identical or conflicting; a label for an id not in the findings file; a value outside the four AC-4.3 labels; an `UNDECIDABLE` with no reason sentence; or a `HIT` naming a seed that is unknown or that belongs to another document than the finding's.
    - `key_mismatch` (AC-4.2): the set of finding ids and the set of key ids differ; an id occurs twice in either file; a key record's surface is not the surface that the cycle's recorded dispatch command lists at that pass index, or its document, cycle or report is not the one the finding was extracted from; or re-extraction from the recorded reports does not give the findings the key maps them to.
    - `calibration_drift:<path>` and `calibration_drift:not_descendant` (AC-2.7 "Two shas, and the smoke commit").
    - `main_leak:<path>` (AC-2.7 main leak check).
    - `calibration_ref:<kind>`, where `<kind>` is `fetch_failed`, `ref_absent`, `sha_unknown:<sha>` or `not_on_ref:<sha>` (AC-2.7 ref failure modes).
    - `cycle_token:<cycle>` (AC-3.2, AC-3.4): a cycle record that the score cannot read as written. The triggers are exactly these: (1) the cycle has no recorded `AUDITCYCLE:` line at the score sha, or (2) its recorded line does not parse as an `AUDITCYCLE:` token; (3) a document's first cycle is `UNVERIFIED` and no second cycle is recorded; (4) a second cycle is recorded although the first is not `UNVERIFIED`; (5) a third or later cycle is recorded for a document; (6) the cycle's recorded dispatch command has no `--surfaces` list that parses as exactly one of the two FR-3 shapes, `codex,agy,grok` or `agy,grok`; (7) a pass whose `delivered=` value is `report-file` or `out` has no recorded collected report. The wrapper prints no `AUDITCYCLE:` line when it exits 4 on an assembly failure (the `exit 4` lines after `h_mad_assemble_audit.py` in `_cmd_audit_cycle`), and an operator can fail to record one. A missing line is UNREADABLE, never PASS, and is never read as AC-3.4 `UNVERIFIED`, because a re-score cannot tell "never recorded" from "re-dispatched".
    - `list_changed:<oid>` (AC-2.6, AC-3.6, AC-6.4): the exclusion-list blob that the AC-6.4 re-run reads at its own `main` commit differs from a list blob recorded for an S1 or S2 export root. `<oid>` is the first recorded blob id, in record order, that differs, or the literal `unrecorded` when a cycle's root record is absent or names no list blob. A re-run never rebuilds roots with a list other than the one the dispatches used.
    - `internal:<ExceptionName>` (AC-5.1): an unexpected failure that none of the reasons above names; `<ExceptionName>` is the escaping exception's class name. An expected I/O or parse failure inside a listed check is reported as that check's reason, never as `internal`; `internal` is the last resort, so that no exit lacks a token.

    Fifteen counts the reason forms above, with `calibration_drift`'s two forms as two and each parameterised form (`leak`, `root_git`, `must_count_mismatch`, `label`, `main_leak`, `calibration_ref`, `cycle_token`, `list_changed`, `internal`) as one.

### AC-5.5

  - AC-5.5: Every verdict and every UNREADABLE reason has a fixture test. Each branch of an alternation gets its own fixture, run with that branch alone. The D3 predicate's two branches and its tie boundary each get a fixture with no undecidables: fabrication strictly lower with recall equal gives `PASS`; fabrication equal with recall strictly greater gives `PASS`; fabrication equal with recall equal (the full tie) gives `MISS`; fabrication equal with recall lower gives `MISS`; and fabrication equal as unreduced fractions (for example `1/4` against `2/8`) with recall equal gives `MISS`. The AC-2.6 refusals get one fixture per trigger, each run with that trigger alone. For `leak:<path>`: an `original` hit, an `expected` hit, a hit only after whitespace normalisation (a re-wrapped copy), a symlink, an `original` in a paired copy whose sha256 differs from the archive (the exemption must not apply), and an `expected` in a byte-identical paired copy (the exemption never covers `expected`). One more fixture, with an `original` in a byte-identical paired copy of its own source, must NOT refuse. For `root_git:<path>`: a `.git` directory, a `.git` file, and a root nested inside a git work tree. The AC-2.7 refusals likewise get one fixture per trigger, run with that trigger alone. They are built in a temporary git repository with a local bare repository as its `origin`, so no fixture needs the network or the real ref. For `calibration_drift`: a score sha that differs outside the calibration directory, and a score sha that does not descend from the calibration sha. For `main_leak:<path>`: triggers (i), (ii) and (iii) each alone, plus one fixture where a `seeded` span also occurs in its own archived source, which must NOT refuse. For `calibration_ref`: one fixture for each of the four kinds. For `cycle_token:<cycle>`: one fixture for each of its seven AC-5.4 triggers, each alone. The other multi-trigger reasons likewise get one fixture per AC-5.4 trigger, each alone: for `ledger_counts`, the per-document counterexample of AC-2.2 (totals 6/7/7/7 kept, one document with a repeated class), an unparseable line, a missing field, a `source` outside the nine FR-2 documents, an empty `original`, and an empty `expected`; for `seed_rebuild`, a one-byte difference, an `original` occurring twice in its source, and each of the four placement violations; for `leak:<path>`, additionally an exported member leaving the root and an exclusion-list line outside the grammar; for `label:<id>`, each of its triggers, including an identical duplicate label record and a conflicting one (`REAL` and `FABRICATED` for one id); for `key_mismatch`, each of its triggers, including a key row whose surface is moved from grok to agy with every id and text unchanged. For `list_changed:<oid>`: a recorded blob that differs from the current one, and a root record that is absent (`unrecorded`). For `internal:<ExceptionName>`: an injected exception that no listed check catches, which must still print a final `SEEDSCORE: UNREADABLE` line. For the AC-5.3 precedence, with no undecidables: zero hits on every surface with grok's fabrication strictly lower must give `INCONCLUSIVE reason=seeds_undetected`, not `PASS`, and zero hits with grok's fabrication strictly higher must give `INCONCLUSIVE reason=seeds_undetected`, not `MISS`. For the calibration-sha content rule: a seeded copy changed at the score sha, and the ledger changed at the smoke commit, each alone, both `calibration_drift:<path>`. Every fixture is synthetic (AC-2.7). The tests live in the suite under `h-mad/tests/`, so the probe directory is kept at archive time (`h_mad_archive_feature.py` keeps a probes directory that live code reads).

### AC-6.4

  - AC-6.4: The re-run command is run from a `main` checkout at the commit named in the doc and dispatches nothing. Its steps:
    - It fetches `refs/heads/calibration/grok-audit-surface` from origin and checks that the cited calibration sha and score sha are on that ref (AC-2.7 ref failure modes).
    - It exports the score sha's tree with `git archive` into a fresh temporary directory outside every git work tree, and reads the ledger, seeded copies, findings, key, labels and the recorded cycles (each cycle's captured wrapper stdout with its `AUDITCYCLE:` line, its dispatch command, its reports and its root record) from there. It never checks the ref out in `main`'s work tree and never uses a `git worktree`. The directory is removed when the run ends.
    - It runs the AC-2.7 two-sha check (descent, paths outside the calibration directory, and the byte-identity of every file present at the calibration sha) and the main leak check.
    - It compares the exclusion-list blob at its own `main` commit with every recorded root's list blob (AC-5.4 `list_changed:<oid>`), then rebuilds the AC-2.6 export roots from the calibration sha with that list and re-runs their content scan and git reach check.
    - It reproduces the `SEEDSCORE:` line from the labels.

    Every refusal is a `SEEDSCORE: UNREADABLE reason=` line (AC-5.4), so the caller reads the token. Run from a later `main` commit, a probe change can score differently, and that is a new reading; a later commit whose exclusion list differs refuses `list_changed:<oid>` instead of scoring. A fresh calibration, such as one after a grok upgrade, uses new export roots and new labels, and is recorded as a new reading. It never edits the previous one in place.
