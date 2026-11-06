# Analysis: gate-non-py-production-files

Change review — 246531ba..8a3fa99e — GATING. Phase 6 gap analysis, fourth measurement, at 8a3fa99e against spec v1.15, design v1.11 and impl-plan v1.10. Files opened: 23, plus 8 mutation-spec JSONs loaded by script only for names, counts and `command` (see Evidence).

## Executive Summary
AC-9.3 still does not hold at 8a3fa99e, by a much smaller margin. v3's 16 lines and 3 tests landed and every one reads as claimed. A fresh census finds 2 more lines with no row (`judge:344`, `judge:738`), both killed by existing tests. Separately, no test has a second readable active plan, so a mutant that reads only the first plan turns a listed write into ALLOW on all three hosts with the row `L-ANY-PLAN` still reporting caught. No verdict is wrong at this commit, and production is frozen. Whether these two items block Phase 7 is a question of what "guard" means, and it is the operator's call (§Verdict).

## Match Rate: 91%

FR level: 10 of 11 FRs have every AC met (10/11 = 90.9, stated as 91). AC level: 54 of 55 met, 1 unmet (AC-9.3). The number matches v2 and v3. The gap under it has shrunk from 16 lines to 2, plus one test gap outside the AC's letter.

## Evidence
- read: 23 files. Spec, design, impl-plan and their range diffs; `inline-protocols.md`; analysis.v3 (`analysis.md` is byte-identical to it, per `diff -q`); the 6 production files (`h-mad-tdd-gate.sh`, `h-mad-codex-tdd-gate.py`, `h-mad-agy-tdd-gate.py`, `h_mad_tdd_judge.py`, `h_mad_target_identity.py`, `h_mad_wire_pin_gate.py`); `h_mad_mutation_harness.py`; `non_py_gate_support.py`; `test_h_mad_tdd_judge_listing.py`, `test_h_mad_tdd_gate_non_py.py`, `test_h_mad_codex_tdd_gate_non_py.py`, `test_h_mad_agy_tdd_gate_non_py.py` (the killers and helpers); `listing_matcher.json`, `claude_gate_listing.json`, `codex_gate_listing.json`, `agy_gate_listing.json`, `listing_connections.json`, `codex_gate_judge_wiring.json`. Loaded by script only: the other 8 feature specs. v2 was not opened; its readings reach this report through v3's table.
- ran: 52 Bash calls, many holding several commands, all on scratch archives except reads. Scratch was under `/tmp/gnp_v4`, each `cd` confirmed by `pwd -P` before a dependent command. Interpreter: `.venv/bin/python` (absolute), wrapped by an argv logger for the harness runs.
- tests run: the 16 new rows' named nodes, one mutant each; the four non-Python gate modules (baseline `242 passed in 42.70s`) plus `test_h_mad_codex_gate_tmp_reports.py`, under each of 22 hand mutants; 5 gate modules under `sh:346`; the replay modules the design names; and, for the first-plan mutant and an unmutated baseline, 18 gate and judge modules (`test_h_mad_*tdd_judge*`, `*tdd_gate*` except `_docs` and `_fallback_agent`, `test_h_mad_codex_gate*`, `test_h_mad_codex_runtime.py`). Grep only, not opened: `test_h_mad_tdd_gate_docs.py`, `test_h_mad_tdd_gate_differential.py`, the FR-9 evidence directory listing.
- Confirmed as asked: `git diff --name-only e524b58a 8a3fa99e -- h-mad/hooks h-mad/scripts` printed nothing. `git diff --name-only e524b58a 8a3fa99e -- docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py` printed nothing, and `git merge-base 8a3fa99e origin/main` prints `e097dfcb`, so the FR-9 evidence's commit and base stand.
- The repository was not modified: `git status --short` printed nothing after the runs, and HEAD stayed 8a3fa99e.
- **A deviation from the brief, stated plainly.** The rubric said not to start from v3's table. I read v3 lines 1 to 230 during orientation, before my table existed, and that span holds its Question 1 table, its exclusions and the first part of its census. I then built my census by an AST script that takes nothing from v3, and classified each line by the rule below, and I opened the remaining part of v3's census only after that. The line sets were compared by script afterwards. A reader should weigh my agreement with v3's exclusions on `judge` and `cx` lines knowing I had seen them; both disagreements below go against v3.
- Two setup errors of mine, so they are not read as findings. My `mut.py` passed `-q -q`, which suppresses pytest's summary, so its per-mutant lines carry the `FAILED` list and not a count; the counts below are of those lines, and the summary lines I quote come from separate runs. A first single-process mutant run was killed and restarted in six shards, and I discarded its copy of the tree. The `.h-mad`-less archives of `h-mad/` alone also fail `test_class_a_names_are_in_the_recaptured_inventory`, `test_classification_table_is_the_recorded_inventory`, `test_three_message_bodies_match_a8d9ba99` and the `test_h_mad_tdd_gate_fallback_agent.py` nodes on the unmutated tree, so those are not attributed to any mutant.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: parser records every backticked production path | 5 | 5 | Complete | carried; `wp:247` rows U1, P-NONPY, P-PYFILTER |
| FR-2: `ungated` retired | 4 | 4 | Complete | carried |
| FR-3: one listing matcher | 5 | 5 | Complete | carried |
| FR-4: judge by the Task's tests only | 6 | 6 | Complete | carried |
| FR-5: Claude gate | 8 | 8 | Complete | carried |
| FR-6: codex gate | 5 | 5 | Complete | carried |
| FR-7: agy gate | 4 | 4 | Complete | carried |
| FR-8: undecidable listing fails closed | 4 | 4 | Complete | carried |
| FR-9: end-to-end proof | 5 | 4 | Partial | Missing AC-9.3 |
| FR-10: prose | 3 | 3 | Complete | carried |
| FR-11: doc/data allowed | 6 | 6 | Complete | carried |

## Question 1: AC-9.3

Text, spec:221: "Every new guard in FR-1, FR-3 to FR-8 and FR-11 has a mutation-spec entry. Each mutant is killed by a test that fails for the guard's own reason. Results are scored on the pytest summary, not on `$?`."

### The census

Source: `git diff -U0 3489f86b 8a3fa99e` under `h-mad/hooks` and `h-mad/scripts`, added or changed lines. Python by AST (conditions, loops, returns, `continue`, `except`, ternaries, boolean operators, comparisons, comprehension filters, assignments, and calls to `any`, `all`, `min`, `max`, `next`, `append`, `extend`, `read_chain`, `listing`, `judge`, `_match_plans`, `PlanMatch`, `Listing`). Shell by reading every changed line, so `case` arms, `[[ ]]`, `||` and `&&` guards are all in. Row coverage: the span of each row's `find` in the file at 8a3fa99e, over every spec JSON. The full table is §"Census".

**The rule I applied.** A line is a *new guard* when all of these hold: it is new in the range under a named FR; it is a condition, verdict return, recorded value or transport; and a mutant of that line alone moves a verdict across fail-open and fail-closed, or it is the only line choosing that verdict. A line is an *arm* when it runs only under a condition that has a row and its fail-open mutant gives that row's own verdict, or when it runs just before one and its mutant is identical to that row's. A distinct mutant is one no row already produces.

| Class | Lines |
|---|---|
| Guard with a row | 76 |
| Guard with no row | **2** |
| Arm of a guard with a row | 36 |
| Excluded, with reason | 41 |
| Measured and excluded | 3 |
| Structural (`fi`, `done`, `}`, NamedTuple fields) | 16 |
| **Total** | **174** |

### Lines with no row

| Line | Decision | Mutant | Verdict moved | Killed by |
|---|---|---|---|---|
| `judge:344` | the FR-8 condition: undecidable if ANY plan is unreadable | `for m in plans[:1] if m.status == "unreadable"` | f readable and not listing, g unreadable, write unlisted `scripts/hard.sh`: DENY judge-error → **ALLOW** on all three hosts (`received Outcome(decision='allow'...)` on Claude and codex, `received {'decision': 'allow'}` on agy) | 4 nodes: JL::test_listing_unreadable_when_no_plan_lists_the_target and the three `test_*_unlisted_beside_unreadable_is_judge_error` |
| `judge:738` | Claude's transport of the chain's records to the matcher | `listing(root, names, chain.records[:1])` | f not listing, g lists `scripts/tool.sh`, test absent: DENY test-missing → **ALLOW** on Claude only, while codex and agy stay DENY | 1 node: CL::test_claude_unlisted_beside_unreadable_is_judge_error. The two-plan-listing scenario itself has no test |

A scratch spec holding both, on the harness, printed them caught: `caught: L-UNREADABLE-ANY-PLAN` and `caught: LV-RECORDS`, each `killed by its named test ... (assertion: no traceback ...)`. So two rows land as written and no new test is needed for either.

**Why these two and not others.** `judge:344` is the twin of `judge:341`. `L-ANY-PLAN` was added because a condition one line above the rowed `if listed:` could be mutated distinctly, and `judge:344` stands in exactly that relation to the rowed `if bad:`. Full suppression of `judge:344` gives L-UNREADABLE's verdict; `plans[:1]` does not. `judge:738` is the same kind of transport line as `judge:732`, `cx:289` and `ag:185`, which v3 counted and which now have rows, and `chain.records` is what those rows do not cover. On codex and agy the line carrying the same argument, `cx:298` and `ag:195`, has rows, so only Claude's has none.

**How firm the count is.** Both are soft. Each is one line whose wholesale mutants match an existing row, and each is caught only by a partial mutant I chose. If "guard" means a decision rather than a line, FR-8's undecidable-listing guard already has three rows (`L-UNREADABLE-RECORD`, `L-UNREADABLE`, `L-LISTED`), `judge:738` is covered by `LV-ACTIVE` and `CL-FORCE`, clause 1 closes, and the match rate is 100. I hold to the line reading because the rubric asks for it by line, and v3's 16 were judged by it. Note that a partial mutant of `judge:336` (`tuple(result[:1])`) would also move a verdict; I excluded it because it carries no condition and is not transport, which is a judgement call. The class of "partial mutants of a row-less line" has no natural floor, so the operator should expect another census to find more if this standard stands.

### Comparison with v3

This comparison was made after the table above.

**v3 excluded, I count as a guard:**
- `judge:344`. v3: "same decision as L-UNREADABLE". Its reasoning holds for the full mutant, but not for `plans[:1]`, and it treated `judge:341` beside `judge:342` the other way.
- `judge:738`. v3: "call with the names of judge:732". The line also carries the records, and they are not in any row.

**I exclude, v3 counted:** none. `judge:347` is the softest v3 counted, since `L-NOT-LISTED` has a fail-closed direction only, and it now has a row, so nothing turns on it.

**Agree, driven again rather than taken from v3:**
| Line | Mutant | Result in the four modules plus `tmp_reports` |
|---|---|---|
| `sh:204` | `if false` | 4 fail; verdict stays DENY judge-error, reason only |
| `sh:208` | `if false`; `if true` | 24 and 25 of 80 fail in `test_h_mad_tdd_gate_non_py.py`; `grep` for `decision='allow'` on the assertion lines printed 0 both times. Fail-closed only |
| `sh:210` | `${CANON_NAMES[0]}` | 4 fail, all DENY judge-error |
| `sh:211` | `return 0`; `:` | foreign target: DENY judge-error → **ALLOW**, one killer, the same node as `H-LIST-NAME`. Arm: identical mutant; `:` fails closed, 23 fail |
| `sh:269` `"docdata yes"` | `DOC_DATA=no` | 17 fail, ALLOW → DENY. Same verdict as `H-DOCDATA`, so it is covered there. No fail-open direction |
| `sh:342` | removed | 37 fail, all DENY judge-error |
| `sh:346` | removed | 0 fail in the five modules; 1 of 270 fails in the wider Claude set: `test_h_mad_tdd_gate_judge.py::test_claude_hardlink_mixed_names_judges_the_production_name`. The line exists at 3489f86b at column 0 and is only re-indented, so it is not new |
| `judge:346` | `Listing("not-listed", None, None, "")` | 8 fail, same 3-host ALLOW as `L-UNREADABLE`. Arm |
| `judge:360`, `:363` | `if False` | 0 fail, notes only, no verdict moves. Re-homed `resolve` body |
| `cx:352` | `if True`; `if False` | 17 and 10 fail, both directions move. Not new: the condition predates the range, only an argument changed |
| `cx:372` | `reason = ""` | 23 fail, DENY → ALLOW. Identical to `CX-DENY`, so an arm |

**The line sets.** Every one of v3's 158 is in mine. Mine has 16 more: 8 NamedTuple fields and `sh:197`, `:205`, `:207`, `:209`, `:212`, `:214`, `:216`, `:347`. Only `sh:209` carries a decision. It has the row `H-LIST-DECODE`, so v3's census simply missed a rowed line and no gap follows.

### Lines from commits after FR-11's scope

`cx:213` to `cx:218` (`_tmp_report_target`), `ag:161` and `id:358` are in the census, and all have rows: `CX-TMP-RELATIVE`, `CX-TMP-PY-UNRESOLVABLE`, `CX-TMP-PY-ALLNAMES`, `CX-TMP-PY-NAME`, `AG-TMP-PY-NAME`, `G-PY-NAME` and the older `G-TMP` rows. Orchestrator's readings: `codex_gate_tmp_reports` 9, `shared_gate_policy` 5, `agy_tdd_gate` 23, each ALL_CAUGHT.

Does AC-9.3 reach them? I decided by reading the named FRs against the Security requirement. FR-7's description (spec:172) names `# M:AG-TMP-PY-NAME`, so `ag:161` is reached by the text. FR-6 (spec:152-163) says nothing of `_tmp_report_target`, and it says the Python path "runs unchanged", so `cx:213` to `cx:218` and `id:358` belong to the Security requirement (spec:295-300) and to §(d) (spec:332-337), neither of which AC-9.3 names. So those are **not reached by the letter**. Nothing turns on the reading, because each has a row whichever way it falls. `cx:352` is outside on both counts: it is not new.

### Clause 2: killed for the guard's own reason

Met on all 16 new rows, by applying each row's own `find` and `replace` to a scratch copy and reading the assertion. The harness, separately on another scratch copy, printed all four specs `ALL_CAUGHT` with `refused=0`: 7, 3, 3 and 3 rows.

| Row | Killer | What the killer asserts | Read under the mutant |
|---|---|---|---|
| LV-ACTIVE | JL::test_listing_cli_listed_prints_the_encoded_target | exact stdout `TDD-LISTING: listed target=...` | `listing must emit exactly the specified stdout line`; own reason |
| L-ANY-PLAN | JL::test_listing_listed_outranks_an_unreadable_sibling | `Listing("listed", target, None, "")` with plan f listing and g unreadable | `Listing(value='unreadable'...)`. Own reason for `all`, but see Must-fix 2 |
| L-READ-RECORD | JL::test_listing_any_canonical_name_lists_the_target | `Listing("listed", target, ...)` | `Listing(value='not-listed'...)`; own effect, though the message names a different property (Nit) |
| L-MATCH-RECORD | same | same | same |
| L-NOT-LISTED | JL::test_listing_not_listed_when_no_name_matches | `Listing("not-listed", ...)` | `Listing(value='unreadable'...)`; own reason, fail-closed direction |
| LV-NAMES | CL::test_claude_hard_link_denies | DENY test-missing, author arrangement | `decision='allow'`; own reason |
| LV-CHAIN-TARGET | CL::test_claude_nested_state_governs_a_subproject_target | DENY test-missing under `sub/` | `decision='allow'`; own reason |
| H-LIST-NAMES | CL::test_claude_hard_link_denies | same | `decision='allow'`; own reason |
| H-LIST-TARGET | CL::test_claude_selection_s2_denies | DENY test-missing, `scripts/hard.sh` and `tests/test_hard.py` in the reason | `decision='allow'`; own reason |
| H-DOCDATA-NO-ARM | CL::test_claude_listed_absent_test_denies | DENY test-missing | `decision='allow'`; own reason |
| CX-LIST-NAMES | CX::test_codex_hard_link_denies | DENY test-missing | `decision='allow'`; own reason |
| CX-JUDGED | CX::test_codex_selection_s2_denies | as Claude's | `decision='allow'`; own reason |
| CX-CHAIN-TARGET | CX::test_codex_nested_state_governs_a_subproject_target | DENY test-missing | `decision='allow'`; own reason |
| AG-LIST-NAMES | AG::test_agy_hard_link_denies | deny, kind test-missing | `{'decision': 'allow'}`; own reason |
| AG-JUDGED | AG::test_agy_selection_s2_denies | as Claude's | `{'decision': 'allow'}`; own reason |
| AG-CHAIN-TARGET | AG::test_agy_nested_state_governs_a_subproject_target | deny, kind test-missing | `{'decision': 'allow'}`; own reason |

**Crashes.** No new row is killed by a crash. Harness lines, `--only` the new rows: `crash_kills=0 crash_visible=1/1 hollow_kills=0` on `listing_matcher`, and `crash_kills=0 crash_visible=0/0 hollow_kills=0` on each of the three host specs. Read that `0/0` carefully: `_returncode_assertion_coverage` counts `assert ...returncode...` in the row's named test files, and the host modules hold none, so on those rows the harness's `crash_kills=0` is a reading with an empty denominator and its `assertion: no traceback` annotation is not evidence. The evidence is the assertion lines above, each reading a clean `allow`, not a `judge-error` from a crash.

**The nested tests.** Each fails on `read_chain(root, None)` on my own copy, for its own host only, and no other node moves. Run over the four modules plus `test_h_mad_codex_gate_tmp_reports.py`:
- `judge:733`: 1 FAILED, `test_claude_nested_state_governs_a_subproject_target`, `expected DENY kind=test-missing, received Outcome(decision='allow', ...)`
- `cx:293`: 1 FAILED, `test_codex_nested_state_governs_a_subproject_target`, same
- `ag:188`: 1 FAILED, `test_agy_nested_state_governs_a_subproject_target`, `received {'decision': 'allow'}`

The unmutated four modules read `242 passed`, which agrees with the plan's reading.

### Clause 3: scored on the summary

Met for kills. `h_mad_mutation_harness.py:1944` requires `ran_and_failed(counts)` from `outcome()`, which parses the pytest summary, and a red run with no failed test is a refusal, not a kill. The survivor branch does read `$?`, via `_run` at `:429`, but a pre-check at `:1895` already requires the named test to have run and passed, so a skipped pin cannot reach it. No kill can be scored on `$?` alone.

## Question 2: the `command` mismatch

**Rows naming host tests really ran those tests.** A row with a `test` key scores through `target_command`, not `command`:

```
h_mad_mutation_harness.py:1860  scoring_command = list(target_command) + [mutation["test"]]
```

Run verbosely with an argv-logging interpreter, on a scratch tree, `listing_matcher.json --only LV-NAMES` printed `MUTATION: ALL_CAUGHT mutations=1 caught=1` and `killed by its named test tests/test_h_mad_tdd_gate_non_py.py::test_claude_hard_link_denies (assertion: no traceback ...)`. The logged argv, in order:

```
-m pytest tests/test_h_mad_tdd_judge_listing.py -q                                   baseline, `command`
-m pytest -q tests/test_h_mad_tdd_gate_non_py.py::test_claude_hard_link_denies       pin pre-check, unmutated
-m pytest -q tests/test_h_mad_tdd_gate_non_py.py::test_claude_hard_link_denies       scored, under the mutant
-m pytest tests/test_h_mad_tdd_judge_listing.py -q                                   post-restore, `command`
```

So no row is scored differently because of the mismatch: the named host test is run on the unmutated tree, must pass, is run under the mutant, and must fail. `command` is used at three other sites, none of which scores a kill: the baseline (`:1793`), the survivor probe (`:2005`) and the post-restore check (`:2122`).

**What the mismatch does cost.**
1. The plan's sentences are false. `listing_matcher.json`'s `command` has held only `tests/test_h_mad_tdd_judge_listing.py` at every commit that touched it, from 12bc615e through c89db606, and neither did `listing_connections.json` ever gain a second module, nor `doc_data_definition.json`. Rows whose test file is outside their spec's `command`: `doc_data_definition` 27, `listing_matcher` 8, `listing_connections` 4, `shared_gate_policy` 2, `codex_gate_tmp_reports` 2, `agy_tdd_gate` 1.
2. A survivor's message overstates what ran. It says "the whole suite", but it ran `command`. My probe row printed `named test ... passed and so did the whole suite — nothing bites`, when the only module that ran beyond the pin was `test_h_mad_tdd_judge_listing.py`. On a row whose real killer sits in a host module, that message would misdirect. It changes no score: a survivor is a survivor.
3. The baseline does not prove a host module green. The per-row pre-check covers the named nodes, which is the part that matters for the score.

Fix either way: correct the plan's sentences, or widen `command` to the host modules. Correcting the plan is cheaper. Widening makes the survivor message true at the cost of one baseline run per module.

## Question 3: v3's items, and the document diffs

| v3 item | Status | Evidence |
|---|---|---|
| Must-fix 1: 13 lines with no row, plus `sh:269`'s arm in the 16 | **closed for the 16, moved for the AC** | 16 rows named in Clause 2, each landing once at the line departure 16 names; harness ALL_CAUGHT. AC-9.3 remains unmet on `judge:344` and `judge:738` |
| Must-fix 2: chain read bound by no row or test | **closed** | Three tests and `LV-CHAIN-TARGET`, `CX-CHAIN-TARGET`, `AG-CHAIN-TARGET`; each mutant fails exactly its host's node |
| Should-fix, `unverified`: primary record of the ninth-refusal ruling | **open** | `grep -n 'plan-absent\|absent at the base\|ninth\|nine refusals'` on the spec prints nothing; plan:29 is still the only statement |
| Nit: codex `kind=` token after a path | **open**, not re-driven | production unchanged; `cx:306` still puts `{relative}` before `kind=` |
| Nit: `sh:2` and `test_hook_line_names_both_gates` | **open** | `sh:2` reads `gate for production Python writes`; `test_h_mad_tdd_gate_docs.py:71` keeps the name |
| Nit: two spellings of the `.py` rule | **open** | `cx:287`, `ag:183`, `judge:492` still use `Path(...).suffix` |
| Nit: M5 reach figures | **open** | not re-derived; no AC names them |
| Nit: same-directory residual has no test | **open** | `git grep` for `os.link`, `hardlink_to`, `.link_to` under `h-mad/tests` finds one test-shaped target, `test_h_mad_tdd_gate_differential.py:182` |

**Design and impl-plan diffs: no false statement in the added text.** Executed or checked:
- "Fifteen of the 16 anchors are lines with no `# M:` marker": a script over the 16 rows prints only `H-DOCDATA-NO-ARM` on a marked line.
- Row lists for `listing_matcher` (24), `codex_gate_listing` (13), `agy_gate_listing` (11), `claude_gate_listing` (18): no name in the design outside the JSON, and none in the JSON outside the design.
- "Two of the eighteen are killed by a Claude host test": the JSON's 8 non-listing-module rows are the 6 host entries plus `LV-NAMES` and `LV-CHAIN-TARGET`.
- Each census line departure 16 names (`judge:330`, `:335`, `:341`, `:347`, `:732`, `:733`, `:737`, `sh:198`, `:269`, `:344`, `cx:289`, `:293`, `:303`, `ag:185`, `:188`, `:202`) is the line that row's `find` covers.
- The ledger: lengths by script at 57e4f9fc (102), e21afee3 (105), 246531ba (105), c89db606 (121), 8a3fa99e (121), and the table's rows sum to 121 (Tasks 1 to 8 sum to 100). `git diff --numstat 6d2c8056 c89db606` prints 0 deletions on seven files, and the hooks and scripts diff prints nothing.
- `W5AR` and `W5AF` swap in constant chains (`Chain("none", ...)`, `Chain("active", ...)`), as the design says. Replaying `read_chain(root, None)` at `# M:W5A`: `test_codex_hook_scopes_nested_state_to_the_target_project` fails and `test_root_step5_governs_a_subproject_with_its_own_state` passes, as stated.
- The residual: `git grep -l read_chain` over mutation-specs names only `agy_gate_listing`, `codex_gate_judge_wiring`, `codex_gate_listing` and `listing_matcher`, and their `find`s are the three chain-target rows and `W5A`, so no row names `ag:210` or `judge:750`. The replays fail the nodes the design lists on agy and on the `state` verb. Two more agy nodes also fail in my run, but they fail on the unmutated archive too, so they are not a contradiction, and the design says its lists are not exhaustive.
- Departure 16's `242 passed`: agrees with my run.

**One statement that was already false stayed false**, and it is the mismatch the author flagged (Question 2): plan:16 and plan:439. Plan v1.10 neither added nor corrected it.

## Acceptance Criteria

Re-read at 8a3fa99e: **AC-9.3 only.** No AC's text changed, because the spec is not in `git diff --name-only 246531ba 8a3fa99e`. No AC's test changed: the 3 test modules' diff prints 13 additions and 0 deletions each, adding only the nested tests, and every other row of those specs is untouched. So every other row is carried from v3 and v2, unread here, and production is frozen since v2. The four modules naming the listed-target behaviour pass unmodified (`242 passed`).

Abbreviations are v3's: CL, CX, AG, JL, PT, PP, WP, DD, DOC, FR9T under `h-mad/tests/`; E = the FR-9 evidence directory.

| AC | Verdict | Basis | Code | Test |
|---|---|---|---|---|
| AC-1.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wp:245-247` | PT::test_mixed_production_line_collects_all_three (list equality on the AC's three strings) |
| AC-1.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wp:245-247` | PP::test_paths_label_spelling, ::test_none_value_contributes_nothing, ::test_none_rule_keeps_a_real_path, ::test_label_lines_accumulate, ::test_existing_fields_unchanged, |
| AC-1.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wp:243` | PT::test_none_value_production_stays_empty |
| AC-1.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wp:244-247` | PT::test_non_py_test_token_stays_out_of_tests_and_production (asserts both lists) |
| AC-1.5 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wp:247` touches `production` only | PT::test_other_task_fields_match_with_and_without_a_non_py_token (real values, budget 37) |
| AC-2.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wp` `main`, print loop deleted | WP::test_cli_prints_no_ungated_line |
| AC-2.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wp:295` | WP::test_check_and_tasks_carry_no_ungated_key |
| AC-2.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wp:295` | WP::test_an_unshaped_plan_with_a_non_python_token_stays_unshaped |
| AC-2.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `wire_pin_ungated.json` | U1 → WP::test_a_shell_production_file_is_collected_in_production; U2 → WP::test_an_extensionless_production_path_is_collected_in_production |
| AC-3.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:339`; `cx:298`; `ag:195`; `sh:199`, `sh:343` | CX-CALLEE, AG-CALLEE, CL-CALLEE; CX/AG/CL-REMOVE and -FORCE naming each host's own node |
| AC-3.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `id` canonicalise; `sh:343`; `cx:298`; `ag:195` | CL/CX/AG::test_*_symlink_alias_denies |
| AC-3.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | same | CL/CX/AG::test_*_case_fold_spelling_denies |
| AC-3.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:339-343`, `judge:381` | CL/CX/AG::test_*_hard_link_denies |
| AC-3.5 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | realpath compare inside `_match_plans` | CL/CX/AG::test_*_residual_spellings_allow; JL::test_listing_residual_spellings_are_not_listed |
| AC-4.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:381` | JL::test_judge_listed_non_py_failing_test_is_red_measured (whole Verdict equality) |
| AC-4.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | same | JL::test_judge_listed_non_py_passing_test_is_test_passing |
| AC-4.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:381-382` | JL::test_judge_listed_non_py_absent_test_is_test_missing |
| AC-4.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:381-382` | JL::test_judge_listed_non_py_with_no_pytest_file_is_test_missing (literal `tests/tool.bats`) |
| AC-4.5 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:492` | JL::test_target_module_names_is_empty_for_a_non_py_target; JL::test_non_py_module_not_found_scores_pytest_error (asserts `1 error`, the exact E line, score and verdict) |
| AC-4.6 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | name-map branch of `resolve` | JL::test_judge_unlisted_non_py_is_no_test_resolved |
| AC-5.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `sh:340-349`, `sh:402-407` | CL::test_claude_listed_absent_test_denies |
| AC-5.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | same | CL::test_claude_listed_passing_test_denies; CL::test_claude_listed_failing_test_allows |
| AC-5.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | same | CL::test_claude_listed_extensionless_absent_test_denies |
| AC-5.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `sh:203`, `sh:328` | CL::test_claude_unlisted_code_like_allows; CL::test_claude_unlisted_doc_data_allows |
| AC-5.5 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `sh:358-369` | CL::test_claude_default_authorship_refuses_a_listed_target; CL::test_claude_default_authorship_allows_unlisted_doc_data |
| AC-5.6 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `sh:301`, `sh:203` | CL::test_claude_no_state_file_allows_a_listed_target; CL::test_claude_inactive_record_allows_a_listed_target |
| AC-5.7 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `sh:313` | CL::test_claude_listed_exempt_location_allows |
| AC-5.8 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:343`, `sh:344` | CL::test_claude_selection_s1_allows; CL::test_claude_selection_s2_denies (also asserts `hard.sh` and `test_hard.py` in the reason) |
| AC-6.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `cx:298-306`, `cx:372` | CX::test_codex_listed_absent_test_denies |
| AC-6.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | same | CX::test_codex_listed_passing_test_denies; CX::test_codex_listed_failing_test_allows |
| AC-6.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `cx:301`, `cx:363` | CX::test_codex_unlisted_code_like_allows; CX::test_codex_add_file_doc_data_allows |
| AC-6.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `cx:372` inside the `M:G5` loop | CX::test_codex_multi_target_patch_denies_on_the_listed_target |
| AC-6.5 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:343`, `cx:303` | CX::test_codex_selection_s1_allows; CX::test_codex_selection_s2_denies |
| AC-7.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `ag:195-206` | AG::test_agy_listed_absent_test_denies |
| AC-7.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | same | AG::test_agy_listed_passing_test_denies; AG::test_agy_listed_failing_test_allows |
| AC-7.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `ag:174`, `ag:200` | AG::test_agy_unlisted_code_like_allows; AG::test_agy_unlisted_doc_data_allows |
| AC-7.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:343`, `ag:202` | AG::test_agy_selection_s1_allows; AG::test_agy_selection_s2_denies |
| AC-8.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:320`, `judge:345`, `cx:299`, `ag:196`, `sh:206` | CL/CX/AG::test_*_unreadable_plan_is_judge_error |
| AC-8.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:735`, `cx:294`, `ag:189`, `sh:206` | CL/CX/AG::test_*_unreadable_state_is_judge_error, parametrised on `scripts/other.sh` |
| AC-8.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `judge:317` | CL/CX/AG::test_*_absent_plan_allows; JL::test_listing_absent_plan_is_not_listed |
| AC-8.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `sh:328`, `cx:363`, `ag:174` | CL/CX/AG::test_*_doc_data_allows_in_undecidable_states |
| AC-9.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | drive:139-141, drive:217-219, drive:257 | FR9T::test_fr9_driver_refuses[authorship-line] for the check |
| AC-9.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | drive:82-95 | FR9T::test_fr9_driver_refuses[dirty-hooks, hook-outside-tree, hook-blob-mismatch] |
| AC-9.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | drive:142-150, drive:203-214 | none (evidence is the proof) |
| AC-9.5 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | drive:72-79, drive:98-111 | FR9T::test_fr9_driver_refuses[missing-base, base-is-head, plan-absent-at-base, plan-blob-mismatch] |
| AC-10.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | prose | DOC::test_gate_prose_has_no_retired_phrasing (8 branches) |
| AC-10.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `codex-implementer-prompt.md:19-24` | DOC::test_hook_bullets_state_the_shipped_rule |
| AC-10.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `phase5-substeps.md:230`, `:235` | DOC::test_skill_states_the_docs_first_component_rule |
| AC-11.1 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `id:38`, `sh:328`, `cx:363`, `ag:174` | CL/CX/AG::test_*_listed_doc_data_allows |
| AC-11.2 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `id:33-34` | CL/CX/AG::test_*_listed_upper_case_doc_data_allows |
| AC-11.3 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `id:19`, `id:33-34` | CL/CX/AG::test_*_doc_data_member_allows (9 parameters each) |
| AC-11.4 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `id:33-38`, gates | CL/CX/AG::test_*_excluded_member_denies (7 parameters each) |
| AC-11.5 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `id:38` | CL/CX/AG::test_*_mixed_hard_links_deny |
| AC-11.6 | MET | carried (v3 at 246531ba, from v2 at 57e4f9fc) | `id:19`, `sh:266` (no bash copy) | DD-CX-*, DD-AG-*, DD-CL-* naming each host's `[<suffix>]` parameter |
| AC-9.3 | **UNMET** (`both`) | **re-read at 8a3fa99e** | `judge:344`, `judge:738` | Clause 1 unmet on 2 lines; clauses 2 and 3 met on all 16 new rows. See §"Question 1" |

## Gaps

### Gap 1: AC-9.3, 2 lines that decide a verdict have no mutation-spec entry
- **Missing**: an entry for `judge:344` and `judge:738`.
- **Classification**:

  | AC | Classification | Why | Action |
  |---|---|---|---|
  | AC-9.3 | `both` | design §Implementation Order Task 3 lists `listing_matcher.json`'s 24 rows by name and neither line is among them, and neither the design nor the specs argue for omitting them. Nothing was narrowed on purpose | amend the design's and plan's row lists and add 2 rows; no production change |

- **Where it should be**: `h-mad/tests/mutation-specs/listing_matcher.json`.
- **Fix**: two rows, which scored as below on a scratch spec.
  - `L-UNREADABLE-ANY-PLAN`: find `for m in plans if m.status == "unreadable"), None)`, replace with `plans[:1]`. Test `tests/test_h_mad_tdd_judge_listing.py::test_listing_unreadable_when_no_plan_lists_the_target`.
  - `LV-RECORDS`: find `result = listing(root, names, chain.records)`, replace with `chain.records[:1]`. Test `tests/test_h_mad_tdd_gate_non_py.py::test_claude_unlisted_beside_unreadable_is_judge_error`. Once Must-fix 2's test exists, that test is the sharper killer.
- **Refutation path**: an operator ruling that "guard" means a decision rather than a line closes clause 1 as it stands, since each wholesale mutant of these two lines already matches a row. The match rate then reads 100 and the AC-level count 55 of 55.

### Gap 2, outside AC-9.3's letter: a listing only in a later active plan is pinned by no test
Stated in Must-fix 2. Spec Terms (spec:11) define *Listed* by "some active record", so this is the spec's rule with no test holding it. No AC names a second readable plan.

## Test Results
```
.venv/bin/python -m pytest -q   (at 8a3fa99e, measured by the orchestrator; not re-run)
8639 passed, 3 warnings in 2348.28s
```
Orchestrator's mutation figures, each `ALL_CAUGHT survived=0 refused=0`, not re-run: `wire_pin_ungated` 2, `parse_tasks_non_py` 3, `doc_data_definition` 34, `listing_matcher` 24, `listing_connections` 6, `judge_non_py` 1, `claude_gate_listing` 18, `codex_gate_listing` 13, `agy_gate_listing` 11, `fr9_drive_refusals` 9, `shared_gate_policy` 5, `codex_gate_tmp_reports` 9, `agy_tdd_gate` 23. `--check-anchors`: `ANCHORS_OK specs=214 mutations=3040`. FR-9 evidence: 33 of 33 PASS at e524b58a.

Scoped runs by this analysis on scratch archives of 8a3fa99e: the four non-Python gate modules, `242 passed in 42.70s`. Harness, `--only` the new rows: `MUTATION: ALL_CAUGHT mutations=6 caught=6`, plus `mutations=1 caught=1` for `LV-NAMES` in a separate run, then `mutations=3 caught=3` for each host spec, all `refused=0 hollow_kills=0`. Probe spec: `MUTATION: SURVIVED mutations=3 caught=2 survived=1`, the survivor being `L-ANY-PLAN-FIRST`.

## Verdict
Match rate: 91% (threshold: 90%). Tests: 8639/8639 passing, per the orchestrator's measurement.
→ The formula alone would advance. This pass is GATING and carries 2 Must-fix, so as written it iterates: 1 gap in the AC and 1 test gap. Both close with no production change: 2 rows, and one nested-style test per host plus one row. Each of the 16 rows and 3 tests from the last cycle reads as claimed.

For the operator's Phase 7 decision, what is true:
- **No verdict is wrong at 8a3fa99e** on any scenario I drove, including the two-plan one, on all three hosts.
- **The census is converging but has no floor.** 3 lines, then 16, now 2, on standards that each round tightened, and the 2 depend on partial mutants I chose. Further passes are likely to find more in that class, at falling value.
- **Must-fix 2 is the one with teeth.** It is the same shape as the nested-state gap you closed: a fail-open on all three hosts with the row reporting caught. If only one thing is done before Phase 7, it should be this test, and it is cheap.
- A ruling that "guard" means a decision closes Must-fix 1 without work. Must-fix 2 would remain a test gap under no AC, and would need its own disposition.

## Must-fix
- AC-9.3 clause 1: two new lines that decide a verdict have no mutation-spec row. Failure scenario for `judge:344`: active records f and g, f's plan readable and not listing the target, g's plan invalid UTF-8; `for m in plans` becomes `for m in plans[:1]`, and a write to the unlisted `scripts/hard.sh` moves from DENY judge-error to ALLOW on all three hosts, against FR-8's second case. Failure scenario for `judge:738`: f not listing, g listing `scripts/tool.sh`, test absent; `chain.records` becomes `chain.records[:1]`, and Claude alone moves from DENY test-missing to ALLOW. The harness cannot report either, because it has no row to run. Existing tests kill both (4 nodes and 1 node), and a scratch spec scored both caught, so only the record is missing. Soft, and refutable by the path in Gap 1.
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:221 › `Every new guard in FR-1, FR-3 to FR-8 and FR-11 has a mutation-spec entry.`
  quote: h-mad/scripts/h_mad_tdd_judge.py:344 › `bad = next((m for _, plans in per_name for m in plans if m.status == "unreadable"), None)`
  quote: h-mad/scripts/h_mad_tdd_judge.py:738 › `result = listing(root, names, chain.records)`
- A target listed only by a later active plan is held by no test, so `L-ANY-PLAN` reports caught on a line whose fail-open has no killer. Failure scenario: two active features, `f.impl-plan.md` lists `scripts/other.sh`, `g.impl-plan.md` lists `scripts/tool.sh`, `tests/test_tool.py` absent. At head all three hosts read DENY test-missing, and with the test failing all three read ALLOW, which is right. With `any(m.matches for m in plans)` changed to `any(m.matches for m in plans[:1])`, a write to `scripts/tool.sh` reads **ALLOW on Claude, codex and agy** with the test absent. On that mutant the four modules printed `242 passed in 40.73s`, and the harness printed `MUTATION: SURVIVED` naming `L-ANY-PLAN-FIRST`. The cause is the fixtures: every `write_plan(root, "g", ...)` in the four modules and `non_py_gate_support.py` writes invalid UTF-8 (`test_h_mad_tdd_judge_listing.py:141`, `:156`; `non_py_gate_support.py:150`), so `L-ANY-PLAN`'s `all` mutant dies on an unreadable sibling and no test has two readable plans. Across 18 gate and judge modules the mutant's failing set equals the unmutated baseline's: the same 3 nodes, which fail on an `h-mad/`-only archive because they read files outside it. `test_h_mad_tdd_gate_fallback_agent.py`, which errors on such an archive either way, was excluded, and the rest of the suite was not run against this mutant, so "no test" is measured over those modules and not over all 8639. The same missing fixture leaves `chain.records[:1]` at `cx:303` and `ag:202` with 0 failures in the four modules; driven on codex, it moves test-failing from ALLOW to DENY no-test-resolved, fail-closed only. Fix: one test per host with that fixture (test absent DENY test-missing, test failing ALLOW), and a row `L-ANY-PLAN-FIRST` naming the judge-level one. This is not AC-9.3's letter, since the row it names exists and its mutant dies. I file it as Must-fix because v3's second Must-fix is the same shape and was treated as blocking; the operator may rule otherwise.
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:11 › `in the impl-plan of some active record`
  quote: h-mad/scripts/h_mad_tdd_judge.py:341 › `listed = [name for name, plans in per_name if any(m.matches for m in plans)]`
  quote: h-mad/tests/non_py_gate_support.py:150 › `write_plan(root, "g", "").write_bytes(b"\xff\xfe")`

## Should-fix
- The plan states twice that shared specs' `command` gains host files, and it never did. Rows are scored correctly regardless (Question 2), but a reader planning from the plan is misinformed, and a survivor's "whole suite" message reports one module. Correct the sentences, or widen `command`.
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md:16 › `gains a host's test file in that host's Task.`
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md:439 › `and Tasks 4, 5 and 6 add their host files`
  quote: h-mad/scripts/h_mad_mutation_harness.py:2011 › `f"whole suite — nothing bites"`
- On the host specs `crash_visible=0/0` means `crash_kills=0` is a reading with no denominator, and the harness's `assertion: no traceback` annotation on those rows proves nothing. The host modules assert through `_expect`, which has no `returncode` assertion for `_returncode_assertion_coverage` to count, and a hook's fail-closed refusal would not surface a traceback in any case. The harness's own docstring says such a figure is partial. So for these three specs only a reading of the assertion line can tell a crash from a guard. I did that for the 3 new rows of each host; I did not read the remaining rows of those specs.
  quote: h-mad/scripts/h_mad_mutation_harness.py:1726 › `is a bare count whose two causes`
- `unverified`: the operator ruling behind the ninth driver refusal still has no primary record I could find. Carried from v1, v2 and v3. AC-9.5 does not depend on it.
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md:29 › `This plan follows the operator ruling of 2026-11-04 instead`

## Nit
- Carried: codex's refusal puts the target path before `kind=`, so a listed `scripts/kind=x.sh` carries two `kind=` tokens. Not re-driven, since production has not changed.
- Carried: `sh:2` still says "gate for production Python writes", and `test_hook_line_names_both_gates` keeps its old name.
- Carried: `# M:CX-NOT-CODE-LIKE`, `# M:AG-NOT-CODE-LIKE` and `# M:K-IMPORT-NONPY` keep `Path.suffix` beside the `.endswith` form at `id:358`, `cx:216` and `ag:161`.
- Carried: spec FR-11's M5 reach figures remain un-re-derived.
- Carried: the same-directory residual has no test.
- New: `L-READ-RECORD` and `L-MATCH-RECORD` die on `test_listing_any_canonical_name_lists_the_target`, whose message reads "a later listed canonical hard-link name must be considered". The value is right, but the message names another guard's property.
- New: `H-LIST-TARGET` (`sh:344`) and `H-DOCDATA-NO-ARM` (`sh:269`) carry `symbol` `_read_listing`, though neither line is inside that function. The harness takes the nearest preceding definition for `.sh`, so `ANCHORS_OK` is right and the value only reads oddly. `H-CODE-LIKE` already does the same.

## Census

Every line of `git diff -U0 3489f86b..8a3fa99e` under `h-mad/hooks` and `h-mad/scripts` that carries a decision form, plus every changed shell line. "Row(s)" means a row's `find` covers that line at 8a3fa99e; six names at most are shown, `+` marks more. `wp`'s deletions are retired code, not guards. Abbreviations: `sh` `h-mad-tdd-gate.sh`, `cx` `h-mad-codex-tdd-gate.py`, `ag` `h-mad-agy-tdd-gate.py`, `judge` `h_mad_tdd_judge.py`, `id` `h_mad_target_identity.py`, `wp` `h_mad_wire_pin_gate.py`.

| Line | FR | Row(s) | Classification | Text |
|---|---|---|---|---|
| `ag:161` | FR-7/8 | AG-TMP-PY-NAME,fr4-artifact-py-refusal-dropped,fr4-t3-after-t5 | guard, row | `not any(identity.fold_py_suffix(name).endswith(".py") for name in resolved.nam` |
| `ag:174` | FR-7/8 | AG-DOCDATA | guard, row | `if identity.is_doc_data(resolved.names):  # M:AG-DOCDATA` |
| `ag:175` | FR-7/8 | - | arm of AG-DOCDATA | `continue` |
| `ag:183` | FR-7/8 | AG-NOT-CODE-LIKE | guard, row | `if any(Path(identity.fold_py_suffix(n)).suffix == ".py" for n in resolved.name` |
| `ag:184` | FR-7/8 | - | arm of AG-NOT-CODE-LIKE | `continue` |
| `ag:185` | FR-7/8 | AG-LIST-NAMES | guard, row | `names = [Path(resolved.target).parent / n for n in resolved.names]` |
| `ag:186` | FR-7/8 | AG-LIST-EXEMPT | guard, row | `if _is_exempt_location(names[0].relative_to(root).as_posix()):  # M:AG-LIST-EX` |
| `ag:187` | FR-7/8 | - | arm of AG-LIST-EXEMPT | `continue` |
| `ag:188` | FR-7/8 | AG-CHAIN-TARGET | guard, row | `chain = judge.read_chain(root, names[0])` |
| `ag:189` | FR-7/8 | AG-CHAIN-UNREADABLE | guard, row | `if chain.value == "unreadable":  # M:AG-CHAIN-UNREADABLE` |
| `ag:190` | FR-7/8 | - | arm: formats reason | `detail = f"{chain.error_file}: {chain.error}".replace("kind=", "kind:")` |
| `ag:191` | FR-7/8 | - | arm of AG-CHAIN-UNREADABLE | `decision = {"decision": "deny", "reason": f"State governing the write is unrea` |
| `ag:192` | FR-7/8 | - | arm of AG-CHAIN-UNREADABLE | `return 0` |
| `ag:193` | FR-7/8 | AG-ACTIVE | guard, row | `if chain.value != "active":  # M:AG-ACTIVE` |
| `ag:194` | FR-7/8 | - | arm of AG-ACTIVE | `continue` |
| `ag:195` | FR-7/8 | AG-FORCE,AG-REMOVE | guard, row | `listed = judge.listing(root, names, chain.records)  # M:AG-LIST` |
| `ag:196` | FR-7/8 | AG-LIST-UNREADABLE | guard, row | `if listed.value == "unreadable":  # M:AG-LIST-UNREADABLE` |
| `ag:197` | FR-7/8 | - | arm: formats reason | `detail = f"{listed.error_file}: {listed.error}".replace("kind=", "kind:")` |
| `ag:198` | FR-7/8 | - | arm of AG-LIST-UNREADABLE | `decision = {"decision": "deny", "reason": f"Listing is undecidable ({detail}).` |
| `ag:199` | FR-7/8 | - | arm of AG-LIST-UNREADABLE | `return 0` |
| `ag:200` | FR-7/8 | AG-NOT-LISTED | guard, row | `if listed.value == "not-listed":  # M:AG-NOT-LISTED` |
| `ag:201` | FR-7/8 | - | arm of AG-NOT-LISTED | `continue` |
| `ag:202` | FR-7/8 | AG-JUDGED | guard, row | `verdict = judge.judge(root, listed.selected, chain.records)` |
| `ag:203` | FR-7/8 | AG-VERDICT | guard, row | `if verdict.decision != "ALLOW":  # M:AG-VERDICT` |
| `ag:204` | FR-7/8 | - | arm: formats reason | `relative = listed.selected.relative_to(root).as_posix()` |
| `ag:205` | FR-7/8 | - | arm: formats reason | `detail = f"{relative}: {verdict.reason}".replace("kind=", "kind:")` |
| `ag:206` | FR-7/8 | - | arm of AG-VERDICT | `decision = {"decision": "deny", "reason": f"Phase 5 requires a failing test be` |
| `ag:207` | FR-7/8 | - | arm of AG-VERDICT | `return 0` |
| `cx:213` | FR-6/8 | CX-TMP-RELATIVE | guard, row | `canonical = _load_identity().canonicalise(str(root), str(path))` |
| `cx:214` | FR-6/8 | CX-TMP-PY-UNRESOLVABLE | guard, row | `if canonical.unresolvable:` |
| `cx:215` | FR-6/8 | CX-TMP-PY-UNRESOLVABLE | guard, row | `return False  # M:CX-TMP-PY-UNRESOLVABLE` |
| `cx:216` | FR-6/8 | CX-TMP-PY-ALLNAMES,CX-TMP-PY-NAME,python-under-tmp-admitted,the-name-check-reads-the-link-not-its-target | guard, row | `if any(_load_identity().fold_py_suffix(name).endswith(".py") for name in (Path` |
| `cx:218` | FR-6/8 | any-out-of-root-path-admitted,tmp-reports-refused-again | guard, row | `return _path_within(canonical.target, Path("/tmp"))  # M:G-TMP` |
| `cx:287` | FR-6/8 | CX-NOT-CODE-LIKE | guard, row | `if any(Path(fold_py_suffix(n)).suffix == ".py" for n in resolved.names):  # M:` |
| `cx:288` | FR-6/8 | - | arm of CX-NOT-CODE-LIKE | `return ""` |
| `cx:289` | FR-6/8 | CX-LIST-NAMES | guard, row | `names = [Path(resolved.target).parent / n for n in resolved.names]` |
| `cx:290` | FR-6/8 | CX-LIST-EXEMPT | guard, row | `if _is_exempt_location(names[0].relative_to(root).as_posix()):  # M:CX-LIST-EX` |
| `cx:291` | FR-6/8 | - | arm of CX-LIST-EXEMPT | `return ""` |
| `cx:292` | FR-6/8 | - | excl: loader | `judge = _load_judge()` |
| `cx:293` | FR-6/8 | CX-CHAIN-TARGET | guard, row | `chain = judge.read_chain(root, names[0])` |
| `cx:294` | FR-6/8 | CX-CHAIN-UNREADABLE | guard, row | `if chain.value == "unreadable":  # M:CX-CHAIN-UNREADABLE` |
| `cx:295` | FR-6/8 | - | arm of CX-CHAIN-UNREADABLE | `return f"H-MAD state governing this write is unreadable ({chain.error_file}: {` |
| `cx:296` | FR-6/8 | CX-ACTIVE | guard, row | `if chain.value != "active":  # M:CX-ACTIVE` |
| `cx:297` | FR-6/8 | - | arm of CX-ACTIVE | `return ""` |
| `cx:298` | FR-6/8 | CX-FORCE,CX-REMOVE | guard, row | `listed = judge.listing(root, names, chain.records)  # M:CX-LIST` |
| `cx:299` | FR-6/8 | CX-LIST-UNREADABLE | guard, row | `if listed.value == "unreadable":  # M:CX-LIST-UNREADABLE` |
| `cx:300` | FR-6/8 | - | arm of CX-LIST-UNREADABLE | `return f"H-MAD Phase 5 listing is undecidable ({listed.error_file}: {listed.er` |
| `cx:301` | FR-6/8 | CX-NOT-LISTED | guard, row | `if listed.value == "not-listed":  # M:CX-NOT-LISTED` |
| `cx:302` | FR-6/8 | - | arm of CX-NOT-LISTED | `return ""` |
| `cx:303` | FR-6/8 | CX-JUDGED | guard, row | `verdict = judge.judge(root, listed.selected, chain.records)` |
| `cx:304` | FR-6/8 | CX-VERDICT | guard, row | `if verdict.decision != "ALLOW":  # M:CX-VERDICT` |
| `cx:305` | FR-6/8 | - | arm: formats reason (CX-VERDICT) | `relative = listed.selected.relative_to(root).as_posix()` |
| `cx:306` | FR-6/8 | - | arm of CX-VERDICT | `return f"H-MAD Phase 5 requires a failing test before {relative}: kind={verdic` |
| `cx:307` | FR-6/8 | - | arm of CX-VERDICT | `return ""` |
| `cx:352` | FR-6/8 | - | excl: not new, condition predates range; args changed only | `if _tmp_report_target(root, raw, payload.get("cwd")):` |
| `cx:363` | FR-6/8 | CX-DOCDATA-DIRECTORY,CX-DOCDATA-VERDICT | guard, row | `if is_doc_data(resolved.names):  # M:CX-DOCDATA` |
| `cx:364` | FR-6/8 | - | arm of CX-DOCDATA-* | `continue` |
| `cx:372` | FR-6/8 | - | arm of CX-DENY (mutant identical) | `reason = _judge_listed(root, resolved)` |
| `cx:373` | FR-6/8 | CX-DENY | guard, row | `if reason:  # M:CX-DENY` |
| `cx:374` | FR-6/8 | - | arm of CX-DENY | `return _deny(reason)` |
| `sh:196` | FR-5/8/11 | - | struct | `_read_listing() {` |
| `sh:197` | FR-5/8/11 | - | struct | `local LARGS=() name LOUT LRC file` |
| `sh:198` | FR-5/8/11 | H-LIST-NAMES | guard, row | `for name in "${CANON_NAMES[@]}"; do LARGS[${#LARGS[@]}]=--name; LARGS[${#LARGS` |
| `sh:199` | FR-5/8/11 | W7F,W7R | guard, row | `LOUT=$(python3 "$JUDGE" listing --root "$ROOT_ABS" ${LARGS[@]+"${LARGS[@]}"} 2` |
| `sh:200` | FR-5/8/11 | - | excl: parse; H-LIST-RC decides (`LRC=0` equals that row) | `LRC=${LOUT##*rc=}; LOUT=${LOUT%rc=*}; LOUT=${LOUT%$'\n'}` |
| `sh:201` | FR-5/8/11 | H-LIST-LINES | guard, row | `case "$LOUT" in *$'\n'*\|"") _refuse judge-error "listing verb printed zero or` |
| `sh:202` | FR-5/8/11 | H-LIST-RC | guard, row | `[ "$LRC" = 0 ] \|\| _refuse judge-error "listing verb exited rc=$LRC"  # M:H-L` |
| `sh:203` | FR-5/8/11 | H-NOT-LISTED | guard, row | `if [ "$LOUT" = 'TDD-LISTING: not-listed' ]; then _allow; fi  # M:H-NOT-LISTED` |
| `sh:204` | FR-5/8/11 | - | measured excl: verdict stays DENY judge-error, reason only | `if [[ $LOUT =~ $LISTING_UNREADABLE_RE ]]; then` |
| `sh:205` | FR-5/8/11 | - | excl: decodes a message | `file=$(_pct_decode "${BASH_REMATCH[1]}")` |
| `sh:206` | FR-5/8/11 | H-LIST-UNREADABLE | guard, row | `_refuse judge-error "listing is undecidable ($file: ${BASH_REMATCH[2]})"  # M:` |
| `sh:207` | FR-5/8/11 | - | struct | `fi` |
| `sh:208` | FR-5/8/11 | - | measured excl: both directions DENY, 0 allow | `if [[ $LOUT =~ $LISTING_LISTED_RE ]]; then` |
| `sh:209` | FR-5/8/11 | H-LIST-DECODE | guard, row | `_pct_capture LISTED_TARGET "${BASH_REMATCH[1]}"  # M:H-LIST-DECODE` |
| `sh:210` | FR-5/8/11 | - | arm of H-LIST-NAME; `[0]` mutant fails closed only | `for name in "${CANON_NAMES[@]}"; do` |
| `sh:211` | FR-5/8/11 | - | arm of H-LIST-NAME (fail-open mutant identical to the row's, same killer) | `if [ "$LISTED_TARGET" = "${CANON_TARGET%/*}/$name" ]; then return 0; fi` |
| `sh:212` | FR-5/8/11 | - | struct | `done` |
| `sh:213` | FR-5/8/11 | H-LIST-NAME | guard, row | `_refuse judge-error "listing verb named a target it was not given"  # M:H-LIST` |
| `sh:214` | FR-5/8/11 | - | struct | `fi` |
| `sh:215` | FR-5/8/11 | H-LIST-UNRECOGNISED | guard, row | `_refuse judge-error "listing verb printed no well-formed listing line"  # M:H-` |
| `sh:216` | FR-5/8/11 | - | struct | `}` |
| `sh:266` | FR-5/8/11 | CG-CANON,H11 | guard, row | `CANON_RECORD=$(python3 -c 'import os,sys;sys.path.insert(0,os.path.join(os.pat` |
| `sh:267` | FR-5/8/11 | - | excl: split, next line guards | `DOC_DATA_LINE=${CANON_RECORD##*$'\n'}; CANON_RECORD=${CANON_RECORD%$'\n'*}` |
| `sh:269` | FR-5/8/11 | H-DOCDATA-LINE,H-DOCDATA-NO-ARM | guard, row | `case "$DOC_DATA_LINE" in "docdata yes") DOC_DATA=yes ;; "docdata no") DOC_DATA` |
| `sh:280` | FR-5/8/11 | - | excl: pattern | `LISTING_UNREADABLE_RE='^TDD-LISTING: unreadable file=([^ ]+) error=([A-Za-z_-]` |
| `sh:281` | FR-5/8/11 | - | excl: pattern | `LISTING_LISTED_RE='^TDD-LISTING: listed target=([^ ]+)$'` |
| `sh:328` | FR-5/8/11 | H-DOCDATA | guard, row | `[ "$DOC_DATA" = yes ] && _allow  # M:H-DOCDATA` |
| `sh:340` | FR-5/8/11 | H-CODE-LIKE | guard, row | `if [ "$ALL_NON_PY" = yes ]; then  # M:H-CODE-LIKE` |
| `sh:341` | FR-5/8/11 | H-LIST-INROOT | guard, row | `[ "$IN_ROOT" = yes ] \|\| _allow  # M:H-LIST-INROOT` |
| `sh:342` | FR-5/8/11 | - | measured excl: setup, DENY judge-error only | `_find_judge` |
| `sh:343` | FR-5/8/11 | CL-FORCE,CL-REMOVE | guard, row | `_read_listing  # M:H-LIST` |
| `sh:344` | FR-5/8/11 | H-LIST-TARGET | guard, row | `TARGET_PATH=$LISTED_TARGET` |
| `sh:345` | FR-5/8/11 | - | struct: else of H-CODE-LIKE | `else` |
| `sh:346` | FR-5/8/11 | - | excl: not new, re-indented line present at 3489f86b | `TARGET_PATH=$PRODUCTION_TARGET` |
| `sh:347` | FR-5/8/11 | - | struct | `fi` |
| `sh:406` | FR-5/8/11 | H-LIST-CONTEXT | guard, row | `if [[ $JOUT =~ $JUDGE_DENY_RE ]] && [ "$ALL_NON_PY" = yes ]; then _refuse "${B` |
| `id:19` | FR-11 | DD-AG-CFG,DD-AG-INI,DD-AG-JSON,DD-AG-MD,DD-AG-RST,DD-AG-TOML+ | guard, row | `DOC_DATA_SUFFIXES = (".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst",` |
| `id:20` | FR-11 | - | excl: table used by DD-CASE | `_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqr` |
| `id:34` | FR-11 | DD-CASE,DD-SUFFIX | guard, row | `return any(name[-len(s):].translate(_ASCII_LOWER) == s for s in DOC_DATA_SUFFI` |
| `id:38` | FR-11 | DD-ALL | guard, row | `return all(has_doc_data_suffix(n) for n in names)  # M:G-DOCDATA-ALL` |
| `id:42` | FR-11 | DD-EXEMPT-PARENT | guard, row | `parents = Path(relative).parts[:-1]  # M:G-EXEMPT-PARENT` |
| `id:43` | FR-11 | DD-EXEMPT-DOCS | guard, row | `if parents[:1] == ("docs",):  # M:G-EXEMPT-DOCS` |
| `id:44` | FR-11 | - | arm of DD-EXEMPT-DOCS | `return True` |
| `id:45` | FR-11 | DD-EXEMPT-DIRS | guard, row | `return "tests" in parents or "fixtures" in parents  # M:G-EXEMPT-DIRS` |
| `id:49` | FR-11 | DD-EMIT | guard, row | `print("docdata yes" if is_doc_data(identity.names) else "docdata no")  # M:G-D` |
| `id:358` | FR-11 | G-PY-NAME | guard, row | `if not name.endswith(".py"):  # M:G-PY-NAME` |
| `judge:64` | FR-3/4/8 | - | struct: NamedTuple field | `plan: Path` |
| `judge:65` | FR-3/4/8 | - | struct: NamedTuple field | `status: str` |
| `judge:66` | FR-3/4/8 | - | struct: NamedTuple field | `error: str` |
| `judge:67` | FR-3/4/8 | - | struct: NamedTuple field | `matches: tuple` |
| `judge:71` | FR-3/4/8 | - | struct: NamedTuple field | `value: str` |
| `judge:72` | FR-3/4/8 | - | struct: NamedTuple field | `selected: Optional[Path]` |
| `judge:73` | FR-3/4/8 | - | struct: NamedTuple field | `error_file: Optional[Path]` |
| `judge:74` | FR-3/4/8 | - | struct: NamedTuple field | `error: str` |
| `judge:312` | FR-3/4/8 | - | excl: container | `result = []` |
| `judge:317` | FR-3/4/8 | L-ABSENT | guard, row | `result.append(PlanMatch(plan, "absent", "", ()))  # M:L-ABSENT` |
| `judge:320` | FR-3/4/8 | L-UNREADABLE-RECORD | guard, row | `result.append(PlanMatch(plan, "unreadable", type(exc).__name__, ()))` |
| `judge:323` | FR-3/4/8 | - | excl: container | `matches = []` |
| `judge:330` | FR-3/4/8 | L-MATCH-RECORD | guard, row | `matches.append((task, base))` |
| `judge:335` | FR-3/4/8 | L-READ-RECORD | guard, row | `result.append(PlanMatch(plan, "read", "", tuple(matches)))` |
| `judge:336` | FR-3/4/8 | - | excl: returns container | `return tuple(result)` |
| `judge:340` | FR-3/4/8 | AG-CALLEE,CL-CALLEE,CX-CALLEE,L-ANY-NAME | guard, row | `per_name = [(name, _match_plans(root, name, records)) for name in names]` |
| `judge:341` | FR-3/4/8 | L-ANY-PLAN | guard, row | `listed = [name for name, plans in per_name if any(m.matches for m in plans)]` |
| `judge:342` | FR-3/4/8 | L-LISTED | guard, row | `if listed:  # M:L-LISTED` |
| `judge:343` | FR-3/4/8 | AG-SELECT,CL-SELECT,CX-SELECT,L-SELECT | guard, row | `return Listing("listed", min(listed, key=lambda p: p.name), None, "")  # M:L-S` |
| `judge:344` | FR-3/4/8 | - | **GUARD, NO ROW** (condition; distinct fail-open mutant `plans[:1]`) | `bad = next((m for _, plans in per_name for m in plans if m.status == "unreadab` |
| `judge:345` | FR-3/4/8 | L-UNREADABLE | guard, row | `if bad:  # M:L-UNREADABLE` |
| `judge:346` | FR-3/4/8 | - | arm of L-UNREADABLE (mutant identical to the row's) | `return Listing("unreadable", None, bad.plan, bad.error)` |
| `judge:347` | FR-3/4/8 | L-NOT-LISTED | guard, row | `return Listing("not-listed", None, None, "")` |
| `judge:351` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `real_root = Path(os.path.realpath(root))` |
| `judge:352` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `real_target = Path(os.path.realpath(target))` |
| `judge:353` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `notes = []` |
| `judge:354` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `candidates = []` |
| `judge:355` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `seen_candidates = set()` |
| `judge:356` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `matched = False` |
| `judge:357` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `declared_budget = None` |
| `judge:358` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `for found in _match_plans(root, target, records):` |
| `judge:359` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `plan = found.plan` |
| `judge:360` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `if found.status == "absent":` |
| `judge:361` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `notes.append(f"{plan}: absent")` |
| `judge:362` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `continue` |
| `judge:363` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `if found.status == "unreadable":` |
| `judge:364` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `notes.append(f"{plan}: impl-plan unreadable: {found.error}")` |
| `judge:365` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `continue` |
| `judge:366` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `plan_matched = False` |
| `judge:367` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `for task, base in found.matches:` |
| `judge:368` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `matched = plan_matched = True` |
| `judge:369` | FR-3/4/8 | declared-budget-not-read | excl: re-homed body of `resolve` (row declared-budget-not-read anchors it) | `if task.get("judge_budget") is not None:  # M:J-BUDGET-READ` |
| `judge:370` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `declared_budget = max(declared_budget or 0, task["judge_budget"])` |
| `judge:371` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `for entry in task["tests"]:` |
| `judge:372` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `candidate = Path(os.path.realpath(base / entry))` |
| `judge:373` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `if not _inside(str(candidate), str(real_root)):` |
| `judge:374` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `notes.append(f"candidate outside root dropped: {entry}")` |
| `judge:375` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `elif candidate not in seen_candidates:` |
| `judge:376` | FR-3/4/8 | - | excl: re-homed body of `resolve` | `candidates.append((candidate, base))` |
| `judge:492` | FR-3/4/8 | K-IMPORT-NONPY | guard, row | `if Path(fold_py_suffix(target.name)).suffix != ".py":  # M:K-IMPORT-NONPY` |
| `judge:493` | FR-3/4/8 | - | arm of K-IMPORT-NONPY | `return frozenset()` |
| `judge:682` | FR-3/4/8 | - | excl: argparse | `listing_command = commands.add_parser("listing")` |
| `judge:730` | FR-3/4/8 | - | excl: verb dispatch | `if args.command == "listing":` |
| `judge:732` | FR-3/4/8 | LV-NAMES | guard, row | `names = [root / name for name in args.name]` |
| `judge:733` | FR-3/4/8 | LV-CHAIN-TARGET | guard, row | `chain = read_chain(root, names[0])` |
| `judge:734` | FR-3/4/8 | LV-NONE | guard, row | `line = "not-listed"  # M:LV-NONE` |
| `judge:735` | FR-3/4/8 | LV-CHAIN-UNREADABLE | guard, row | `if chain.value == "unreadable":  # M:LV-CHAIN-UNREADABLE` |
| `judge:736` | FR-3/4/8 | - | arm of LV-CHAIN-UNREADABLE | `line = f"unreadable file={_enc(str(chain.error_file))} error={chain.error}"` |
| `judge:737` | FR-3/4/8 | LV-ACTIVE | guard, row | `elif chain.value == "active":` |
| `judge:738` | FR-3/4/8 | - | **GUARD, NO ROW** (records transport; same standard as judge:732) | `result = listing(root, names, chain.records)` |
| `judge:739` | FR-3/4/8 | LV-LISTED-ARM | guard, row | `if result.value == "listed":` |
| `judge:740` | FR-3/4/8 | - | arm of LV-LISTED-ARM | `line = f"listed target={_enc(str(result.selected))}"` |
| `judge:741` | FR-3/4/8 | LV-UNREADABLE-ARM | guard, row | `elif result.value == "unreadable":` |
| `judge:742` | FR-3/4/8 | - | arm of LV-UNREADABLE-ARM | `line = f"unreadable file={_enc(str(result.error_file))} error={result.error}"` |
| `judge:743` | FR-3/4/8 | - | arm of LV-RC | `except Exception as exc:` |
| `judge:745` | FR-3/4/8 | LV-RC | guard, row | `return 2  # M:LV-RC` |
| `judge:747` | FR-3/4/8 | - | excl: exit after print | `return 0` |
| `wp:247` | FR-1 | P-NONPY: NON-PY PRODUCTION PATHS NEVER COLLECTED,P-PYFILTER: PYTHON PRODUCTION TOKENS COLLECTED TWICE,U1: NON-PY PRODUCTION PATHS NEVER COLLECTED | guard, row | `current["production"].extend(token for token in _NON_PY_PATH_RE.findall(paths.` |

## Version History
- v1.0: Initial gap analysis draft, Phase 6a, first measurement at 7584ace9 (100 at FR level, AC-9.3 read as met by a marker census).
- v2.0: Second gap analysis at 57e4f9fc against spec v1.14 (91 at FR level, 54 of 55 ACs). AC-9.3 moves to UNMET on three unmarked judge arms.
- v3.0: Third gap analysis at 246531ba against spec v1.15, design v1.10 and impl-plan v1.9 (91 at FR level, 54 of 55 ACs). A census of 158 changed decision lines finds 16 with no row, 3 of which no test kills. 54 AC rows carried from v2, AC-9.3 re-read.
- v4.0: Fourth gap analysis at 8a3fa99e against spec v1.15, design v1.11 and impl-plan v1.10 (91 at FR level, 54 of 55 ACs). v3's two Must-fix closed: 16 rows and 3 nested tests read as claimed, each mutant failing for its own reason, no crash kills. A re-derived census of 174 lines finds 2 more with no row (`judge:344`, `judge:738`), soft, so AC-9.3 stays UNMET, `both`. A new test gap: no test has a second readable active plan, so `L-ANY-PLAN` reports caught while a first-plan-only mutant allows a listed write on all three hosts. The `command` mismatch changes no score: rows score through `target_command`; the plan's sentences are false. v3's Should-fix and five Nits remain open. 54 AC rows carried, AC-9.3 re-read.
