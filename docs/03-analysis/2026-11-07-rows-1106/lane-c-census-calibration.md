# Lane C — rows 6, 7, 9 — done

Worktree `.../scratchpad/rows-c` (branch rows-1106-c, nothing committed). Interpreter `/opt/anaconda3/bin/python3.11`.
Changed (git status): M helper-scripts.md, h_mad_branch_evidence.py, mutation-specs/branch_evidence.json, test_h_mad_branch_evidence.py;
new h_mad_guard_census.py, test_h_mad_guard_census.py, test_h_mad_hook_live_interpreter.py, mutation-specs/guard_census.json, mutation-specs/hook_live_interpreter.json.
`h_mad_new_gate.py` was read for the convention (token last, cannot-judge carries no counts, exit 0 verdict / 2 unreadable, docs pinned both ways); I did not run the scaffold, I hand-wrote to the same shape.

## Verify (final tree, foreground)
- `pytest h-mad/tests/test_h_mad_guard_census.py h-mad/tests/test_h_mad_hook_live_interpreter.py h-mad/tests/test_h_mad_branch_evidence.py -q -p no:cacheprovider -rs` -> `134 passed in 67.93s (0:01:07)` (no skips; 52 + 10 + 72... 71 branch_evidence incl. 13 new)
- harness `--isolate --python /opt/anaconda3/bin/python3.11`:
  - guard_census.json: `MUTATION: ALL_CAUGHT mutations=40 caught=40 survived=0 refused=0 unreadable=0 crash_kills=5 crash_visible=1/4 ... untargeted=0/40 hollow_kills=0`
  - hook_live_interpreter.json: `MUTATION: ALL_CAUGHT mutations=7 caught=7 survived=0 refused=0 ...`
  - branch_evidence.json: `MUTATION: ALL_CAUGHT mutations=70 caught=70 survived=0 refused=0 ... crash_visible=9/10` (9 of the 70 are the new full-suite rows)
- `--check-anchors` on the three: `ANCHORS: ANCHORS_OK specs=3 mutations=117 ok=117 drifted=0` (guard_census 40/40, branch_evidence 70/70)
- `h_mad_doc_consumers.py --repo . --run h-mad/references/helper-scripts.md` -> `CONSUMERS-RUN: PASS files=94 passed=4477`
- No test enforces the SKILL.md `Helpers (55): ...` list; I did not touch SKILL.md (not in FILES), so that list does not name the new script. helper-scripts.md is the registry the scaffold and my pin test use.

## R9 --full-suite (h_mad_branch_evidence.py)
- Added `--full-suite`, `--python EXE`, `--full-suite-timeout S` (default 7200; `FULL_SUITE_TIMEOUT`), `_absolute_python` (abspath for a path with a separator, `shutil.which` for a bare name, resolved in `main` before any child changes cwd; no symlink resolve so a venv python keeps its venv), `_full_suite` (runs `_pytest(top, [], ...)` = bare `python -m pytest -q` from the top). Docstring + helper-scripts.md updated.
- Token: `FULL-SUITE: PASS passed=N [skipped=N]` / `FAIL failed= errors= passed=` (-> INCOMPLETE `full-suite-failed`) / `UNREADABLE reason=<python-missing|pytest-missing|pytest-timeout|pytest-rc<N>|pytest-no-summary|pytest-inconsistent|suite-busy|suite-tree-moved>` (-> UNREADABLE `full-suite-<r>`, exit 2) / `SKIPPED reason=dirty|no-commits`. Runs after every other step, also when an earlier step was unreadable.
- Off by default: the existing 58 tests pass unchanged; `test_full_suite_is_off_by_default` pins no `FULL-SUITE` line and no bare pytest.
- RED observed: 12 new tests failed on `unrecognized arguments: --full-suite` / empty FULL-SUITE lines before the code; GREEN after. Test-file edits to the shared stub (additive, existing tests untouched): `argv` logged in the event, `STUB_FULL_MODE` applies only to the bare run, `or 7` pass count and an empty-files guard in `fail` mode (so the bare run does not index `files[0]`).
- 9 mutation rows (all caught): failure not incomplete, unreadable not recorded, missing python, interpreter without pytest, full run names a path, uses child timeout, skip unnamed, runs when not asked, python not made absolute (the original bug).

## R7 hook live-interpreter smoke (test_h_mad_hook_live_interpreter.py)
- Finding: `h-mad-codex-tdd-gate.py` is mode 100644 in git (the agy hook and the Claude .sh are 100755), and docs launch it as `python3 <path>` (codex-runtime.md). So: agy is EXECed directly (shebang decides); codex is launched as `python3 <path>` with PATH deciding (the helper uses the direct exec if the file ever becomes executable). I did not chmod it (not in FILES).
- Allow (test-file write), deny (production write, no failing test, kind test-missing) and a symlink-loop target, for both hooks, in a hostile-named repo, no pytest needed in the hook's interpreter. Env via `hermetic_env`; state via `write_state`.
- Positive control: a PATH-first shim `python3` logs each launch then execs the real PATH `python3`; the test asserts exactly one launch through the shim and puts the resolved path and its `--version` in every assertion message. Here PATH python3 = /opt/homebrew/bin/python3 (3.15.2), sys.executable 3.11.8.
- Skips WITH a reason naming the interpreter when `python3` is absent or equals `sys.executable` (realpath); both skips are themselves tested by running the file in a nested pytest with a crafted PATH (`4 skipped`, reason text asserted). Also run with `/usr/bin:/bin` only: 8 passed under the system python.
- Version-sensitive regression: yes, drivable through the public payload. A self-referential symlink dir in the target path gives a clean deny "unresolvable ... kind=judge-error" on both 3.11 and 3.15 for both hooks (measured by hand first); the test asserts deny, "unresolvable", and no Traceback/RuntimeError. It cannot fail on this machine (both versions agree) but pins the live path; mutation rows prove the two unresolvable refusals are what it bites.
- RED: not applicable in the usual sense (tests of existing behaviour, green on first run); evidence of bite is the 7 mutation rows (both hooks' loop refusal, launch via sys.executable for each hook, shim not first on PATH, the two skip guards). 

## R6 guard census (h_mad_guard_census.py)
- CLI `--base REF [--head REF] [--spec-dir DIR] [--path P ...] [--repo DIR]`. Reads git objects only (diff, spec dir and files at `--head`; a spec only in the working tree does not anchor). Last line `GUARD-CENSUS: DONE decision=N anchored=M unanchored=K` (exit 0, also with candidates) or `GUARD-CENSUS: UNREADABLE reason=git|bad-ref|spec-dir|spec-unreadable|unreadable-file` (exit 2, no counts). Candidate lines: `file:line<TAB>kind<TAB>note<TAB>text`. Preceding lines `CENSUS-SCOPE:`, `SKIPPED:`, `ROWS:`, `ARMS:`.
- Decision set (docstring): Python by ast = if/elif/while/for/except/match-case headers, return/raise/assert/continue/break, every assignment and every call used as a statement, kind names ifexp/comp-if/boolop; shell = line rules (control, test, &&/||, case arm, jump, assignment, verdict-helper call). Anchored = a row of a spec for that file whose `find` occurs exactly once and overlaps the line; a `# M:` marker alone does not (tested); a find matching twice or nowhere anchors nothing and is counted on `ROWS:`; a shell line with several `;;` arms needs every arm overlapped.
- Order of work, stated plainly: I wrote the script first and the tests second. RED was shown afterwards by parking the script: 49 failed, 1 passed (that one not identified; likely a test needing no script) with the script absent, at the time the file held 50 tests; the first failure is `test_the_cannot_judge_line_has_no_count`. The real evidence of bite is the 40 ALL_CAUGHT rows.
- Hostile cases with tests: paths with spaces, `[`/`*` and non-ASCII; a glob-named file next to a sibling it would match as a pattern (found by a SURVIVED row, test added); find twice / nowhere / empty; deleted file; binary change; symlink and submodule; non-UTF-8 .py (UNREADABLE, never zero); declared latin-1 source read correctly; unparseable .py; CRLF; non-UTF-8 shell; malformed/non-UTF-8/ non-spec JSON; absolute spec root outside the repo; spec dir missing/outside; bad base/head; not a repo.
- Mutation-run notes: two rows were refused/ill-posed and were corrected: a row aimed at a class-nested test needed its `Class::` id; an `except (UnicodeDecodeError, ValueError)` row was an EQUIVALENT mutant (UnicodeDecodeError is a ValueError), so I simplified the code to `except ValueError` and dropped the row; a row whose uncaught SyntaxError was read by the harness as "mutated file did not parse" was re-aimed at swallowing the error.

### Calibration (required)
Base derived from analysis v3 §Census: `git diff 3489f86b..246531ba` under `h-mad/hooks` `h-mad/scripts` (both commits exist in this clone; no backup ref needed). Command: `h_mad_guard_census.py --base 3489f86b --head 246531ba --path h-mad/hooks --path h-mad/scripts`.
Result at 246531ba: `GUARD-CENSUS: DONE decision=170 anchored=58 unanchored=112` (hand census: 158 lines, 60 anchored). 
Compared by file:line: **16 of 16 hand-census lines listed, and v4's 2 of 2, none missed.**

| hand # | line | tool kind / note |
|---|---|---|
| 1 | judge:737 (h_mad_tdd_judge.py) | elif |
| 2 | sh:269 (h-mad-tdd-gate.sh) | control,arm, `arms-not-all-anchored` (the row H-DOCDATA-LINE overlaps only the `*)` arm; the line-granular rule would have called the line anchored, the all-arms rule catches it) |
| 3 | judge:341 | assign,comp-if |
| 4 | judge:335 | call |
| 5 | judge:330 | call |
| 6 | judge:347 | return |
| 7 | judge:732 | assign |
| 8 | sh:198 | control |
| 9 | cx:289 (codex hook) | assign |
| 10 | ag:185 (agy hook) | assign |
| 11 | cx:303 | assign |
| 12 | ag:202 | assign |
| 13 | sh:344 | assign |
| 14 | judge:733 | assign |
| 15 | cx:293 | assign |
| 16 | ag:188 | assign |
| v4 a | judge:344 | assign,comp-if |
| v4 b | judge:738 | assign |

Second calibration the other way (head 8a3fa99e, where Task 8 added the 16 rows): `decision=170 anchored=73 unanchored=97`; the 15 lines with new rows are now anchored and v4's judge:344 and judge:738 are still listed, matching v4's finding. sh:269 stays listed because the added row covers the `"docdata no"` arm and the `"docdata yes"` arm still has none (note `arms-not-all-anchored`). 
One thing the first draft got wrong, caught by comparing: it annotated judge:737 (`elif`) `arm-of-anchored:735`, which would invite a reviewer to skip the plainest real guard; branch headers are no longer annotated as arms (mutation row `elif-is-an-arm`).

Precision, stated plainly (candidates are not findings): 112 candidates against 18 true ones = 16%. Of the 112: 32 are non-header statements under an anchored header (annotated, still listed), 1 partial case line, 79 plain. 59 are in h_mad_tdd_judge.py, mostly the moved `resolve` body that the hand census excluded as "moved, not new"; the tool cannot see a move (it only reads the diff). Counts 170 vs 158: the tool's unit is the statement and its set is wider (calls, assignments in full); the sets are not the same, so the totals are not comparable line for line, only the 18 by file:line are.
Replayed in the suite: `test_the_gate_non_py_hand_census_is_listed_in_full` (asserts all 18 listed and the 170/58/112 counts; skips naming the missing commit in a clone without it).

## Not done / open
- SKILL.md "Helpers (55)" list not updated (outside FILES); registry entry is in helper-scripts.md only.
- Codex hook is mode 100644: if the live host execs it by shebang it would fail "permission denied"; docs say `python3 <path>`. Not verified against HemaSuite's tracked `.codex/hooks.json` (not read).
- A backgrounded (`&`) run of the suite makes SIGINT ignored in children, so `test_interrupt_restores_the_tree_and_reports_UNREADABLE[SIGINT]` fails (60 s timeout) in the consumers run and the combined pytest when launched from a background shell job; it passes in the foreground and when the background job first resets SIGINT. Not caused by these changes; seen twice before I identified it. A known trap for any wrapper that backgrounds the suite.
- The census does not detect moved code, nor whether a row's mutant really changes the decision on a line it overlaps (overlap, not kill). `FULL-SUITE` was exercised only against the stub pytest plus the existing real-pytest end-to-end test without `--full-suite`; no live run of `--full-suite` over the real 4477-test suite was done.

---
# Follow-up round (review findings 1-6) — done

Files touched again (rows-c, uncommitted on top of 97ead242): h_mad_guard_census.py, test_h_mad_guard_census.py, mutation-specs/guard_census.json, h_mad_branch_evidence.py, test_h_mad_branch_evidence.py, mutation-specs/branch_evidence.json, references/helper-scripts.md.
RED first for each: before the code, 38 of the new/changed census tests failed (e.g. no `removed=` field, no `UNMEASURED:`, one spec dir) and the item-6 test failed with a traceback.

## Verify (final tree, every command run with SIGINT default, nothing concurrent)
- pytest of the three files: `163 passed in 81.13s (0:01:21)` (census 81, hook 10, branch_evidence 72)
- guard_census.json `--isolate`: `MUTATION: ALL_CAUGHT mutations=64 caught=64 survived=0 refused=0 unreadable=0 crash_kills=5 crash_visible=1/5 ... hollow_kills=0`
- branch_evidence.json `--isolate` (run on the tree before the final census-only test/row edits; the script and its test file did not change after): `MUTATION: ALL_CAUGHT mutations=71 caught=71 survived=0 refused=0 ... crash_visible=10/11`
- `--check-anchors` (guard_census, branch_evidence, hook_live_interpreter): `ANCHORS: ANCHORS_OK specs=3 mutations=142 ok=142 drifted=0`
- `h_mad_doc_consumers.py --repo . --run h-mad/references/helper-scripts.md`: `CONSUMERS-RUN: PASS files=94 passed=4478`

## Per finding
1. **Silent zero.** `SKIPPED:` now carries `tests= other= unmeasured=`; each unmeasured file is listed as `UNMEASURED: <file>`. Unmeasured = `.js .jsx .mjs .cjs .ts .tsx .rb .pl .go .rs .java .kt .c .cc .cpp .h .swift .lua .php .cs .sql .ps1 ...` or any foreign `#!`; docs/data are `other`. Beyond the ask, I measure rather than only count: a `#!` python script of any name is read by `ast`, a `#!` shell script of any name (`gate.v2`) and `.zsh/.ksh` by the shell rule. `test_a_suffixless_file_with_another_shebang_is_not_a_target...` keeps "not a target" (ruby) and asserts `unmeasured=1` + the `UNMEASURED:` line. A `--path` matching no change (any one of several) is `UNREADABLE reason=path-no-match`.
2. **Removed guards.** The base blob of every modified/deleted measured file is parsed with the same rule; decision lines on removed/rewritten base lines are printed `REMOVED: <file>:<base line> <kind> "<text>"`, token `... unanchored=k removed=r` (appended). Stated behaviour: a rewritten decision line is both a candidate and REMOVED; a deleted file lists all its decisions; a rename is delete+add (`--no-renames`): old file REMOVED, new file candidates; a base that is not decodable/parseable with removed lines is UNREADABLE. Measured at 246531ba: `removed=42`.
3. **Spec dirs.** `--spec-dir` repeatable; default `h-mad/tests/mutation-specs` + `handoff/tests/mutation-specs`; explicit replaces the default and a missing explicit one is `UNREADABLE spec-dir`; a missing default is fine while another has specs, none at all is UNREADABLE. Replay `--base 5db87e97~1 --head 5db87e97 --path handoff/scripts`: default `anchored=7`; `--spec-dir h-mad/tests/mutation-specs` `anchored=0` (decision=119, removed=1 with my base choice; the review's 118 used a different base). In the suite as a skip-if-absent test.
4. **Python holes.** `await deny(x)` is a `call`; `with`/`async with` headers are decision lines (kind `with`; a deliberate widening: every `with open(...)` is now a candidate). Bare CR: statement lines are mapped from ast's line table to git's through character offsets; the `cr.py` case now gives assign@1, assign@1, if@2, call@3 (4 decisions).
5. **Replay.** Measured (final script, `--head 8a3fa99e`, base 3489f86b): `decision=170 anchored=73 unanchored=97 removed=42`; of the 18 hand lines **3** remain: `h_mad_tdd_judge.py:344`, `:738`, `h-mad-tdd-gate.sh:269`. Corrected helper-scripts.md ("3 remain, ..."), added `test_after_the_task_8_rows_exactly_three_of_the_eighteen_remain`; my earlier claim of 2 was wrong (I had noted sh:269 stays listed in this report but not in the doc).
   Re-run of the 246531ba calibration by file:line after the parsing change: 16 of 16 v3 lines and 2 of 2 v4 lines listed (table in the first section unchanged); `decision=170 anchored=58 unanchored=112 removed=42`.
6. **Unrunnable `--python`.** `FULL-SUITE: UNREADABLE reason=python-unrunnable`, verdict `INCOMPLETE reason=full-suite-python-unrunnable`, exit 0, no traceback; test uses an executable with `#!/no/such/interpreter`. (A second handler around the pytest launch was unreachable once the probe passes, so I did not keep it.)

## Defects my own work introduced and caught this round
- A scripted edit of the test file silently truncated 12 tests (an append before a slice-replace). They passed only because they were gone; the harness reported them as `did not run` and `REFUSED`. I re-added them and then checked every spec `test` id against the module's function names.
- Restructuring the file filter fetched a gitlink's sha as a blob (`cannot read blob`): caught by the symlink/submodule test, fixed by filtering before fetching.
- Two rows were equivalent or mis-pinned (missing-spec-dir row now pinned to the no-default-dir test; `deleted-file-blob-from-head` first survived because a deleted `.py` is typed by suffix, so a test with a deleted suffix-less shell script was added).

## Real `--full-suite` run
The tool refuses a dirty tree (`dirty` -> INCOMPLETE, `FULL-SUITE: SKIPPED`, run attempted once and it said exactly that), and I may not commit in rows-c. So I cloned rows-c (`git clone --local`) to `scratchpad/fs-clone`, copied the final files in, committed there (wip + a doc-only `NOTES-scratch.md` commit), and verified `diff -r h-mad` between the two trees was empty. I ran it on the clone with `--base HEAD~1` so the harness/consumers steps (run separately above) did not repeat. Started with SIGINT reset (python parent with SIG_DFL), alone on the machine, 06:41:32 -> 07:36:31 (55 min):
```
EVIDENCE: sha=cfc154c1b base=f18401a32 ahead=1 dirty=0
CHANGED: files=1 prod=0 tests=0 specs=0 docs=1 support=0 deleted=0
TESTS: NONE
CONSUMERS-RUN: NONE
ANCHORS: NONE specs=0
MUTATION: NONE specs=0
FULL-SUITE: PASS passed=8752
TREE: UNCHANGED
EVIDENCE-VERDICT: COMPLETE
rc=0
```
8752 tests = the whole `pytest.ini` testpaths (the consumers run is 4478 because it only selects tests that parse the document). The first attempt on a stale copy was killed and discarded (an unrelated pytest left orphan dispatcher processes in the clone; killed).

## Not done / open
- The tool run is of a clone with a doc-only diff, not of rows-c's own diff; `--full-suite` after a code diff through the evidence tool (which adds ~2 h of harness runs) was not repeated.
- branch_evidence `--isolate` was last run before the census-only final edits (no change to its script, test file or spec afterwards).
- `with` as a decision line and `other`/`unmeasured` suffix lists are judgment calls; reviewers may want them narrower.

---
# Second follow-up round (review 2: Must-fix 2; Should-fix 1, 7, 8, 10, 11, 12) — done

RED first: 75 of the new/changed census tests failed before the code (token shape, `UNPARSED-BASE`, per-side modes), plus the item-3 branch_evidence test. Changed (uncommitted): h_mad_guard_census.py, test_h_mad_guard_census.py, guard_census.json, h_mad_branch_evidence.py, test_h_mad_branch_evidence.py, branch_evidence.json, helper-scripts.md.

## Verify (final tree, foreground-safe launch, nothing concurrent)
- pytest, the three files: `202 passed in 115.11s (0:01:55)`
- guard_census.json `--isolate --python /opt/anaconda3/bin/python3.11`: `MUTATION: ALL_CAUGHT mutations=73 caught=73 survived=0 refused=0 ... hollow_kills=0`
- branch_evidence.json: `MUTATION: ALL_CAUGHT mutations=72 caught=72 survived=0 refused=0`
- `--check-anchors` (3 specs): `ANCHORS: ANCHORS_OK specs=3 mutations=152 ok=152 drifted=0` (2 branch_evidence/other rows carry no `symbol` pin; advisory)
- `h_mad_doc_consumers.py --repo . --run h-mad/references/helper-scripts.md`: `CONSUMERS-RUN: PASS files=94 passed=4478`
- 246531ba calibration by file:line, parsing changed again: `decision=170 anchored=58 unanchored=112 removed=42 unparsed_base=0`; 16 of 16 v3 lines and 2 of 2 v4 lines listed. At 8a3fa99e: `decision=170 anchored=73 unanchored=97`, 3 of the 18 remain (judge:344, judge:738, sh:269).

## Per item
1. **Must-fix 2.** `Change` now carries the old mode (`fields[0]`). Each side is read only if it exists and is a regular file (100644/100755); a 120000/160000 side is never fetched or parsed and counts as `link` when no side is measured. Tests: deleted gitlink beside a real change (DONE, `link=1`), deleted symlink whose target text is not valid Python (DONE, nothing parsed), symlink changed to file (head side only), python replaced by a symlink (its 3 base decisions listed).
2. **Unparsable base.** Kept DONE: `UNPARSED-BASE: <file>` lines and `unparsed_base=<n>` appended after `removed=`. A broken base that is fixed, and a non-UTF-8 base, behave the same; an unparsable HEAD side is still `UNREADABLE reason=unreadable-file` (tested). Replay `--base ff8234bb~1 --head ff8234bb`:
   `CENSUS-SCOPE: ... files=99 deleted=99`, `SKIPPED: binary=3 link=0 tests=9 other=85 unmeasured=0 ...`, `UNPARSED-BASE: hematology-paper-writer/tools/draft_generator/hpw_upgrade_core.py`, `GUARD-CENSUS: DONE decision=0 anchored=0 unanchored=0 removed=10495 unparsed_base=1` (in the suite as a skip-if-absent test).
3. **Unrunnable interpreter** is now `unreadable` (`UNREADABLE reason=full-suite-python-unrunnable`, rc 2); the docstring line is gone; helper-scripts.md says "like python-missing, exit 2". New row `unrunnable-python-reads-as-incomplete`.
4. **`--path`**: `.`, `./` and the absolute repo top match everything (dropped from the pathspec); a path outside the repo is `UNREADABLE path-no-match` (it had been reported as `spec-dir`).
5. **Language from the old blob** for the base side (Entry carries per-side kinds). Tested: bash -> python shebang (6 head decisions, 8 removed shell decisions, nothing unparsed), python script -> data (2 removed), python -> symlink (3 removed). A type change's deleted decisions are listed.
6. **Fail closed.** `CODE_SUFFIXES` is gone; `DOC_SUFFIXES` / `DOC_NAMES` (allow-list of documents and data) decide `other`; every other side that is not Python or shell is `unmeasured`. Checked on this repo (diff from the root commit to HEAD, 277 measured files): `unmeasured=73` = `.r` 23, `.tsx` 20, `.ts` 19, `.js` 7, `.rs` 4; `other=4609` (`.md .json .log .txt .xsd .csv .tex .png ...`, `rc stdout stderr LICENSE .gitignore`); `.sh` and `.py` measured; suffix-less hooks (`hmad-dispatch`, `pre-commit`, `agy`, ...) are measured through their shebang. Tested: `.vue .mts .pyw .pyi .dart .awk .cxx .tcl`, an unknown `.xyz` and `Makefile` are unmeasured.
7. **Docs.** `SKIPPED:` counters are now disjoint per entry (`binary link tests unmeasured other`, plus the two spec counters) and never count a measured file; `deleted=` moved to `CENSUS-SCOPE:` next to `files=` ("how many measured entries are deletions"); an entry with one measured and one unmeasured side is measured and also named unmeasured (stated). The docstring (scope paragraph, shell paragraph, the "skipped" sentence, per-side language, UNPARSED-BASE, path rules) and helper-scripts.md entry were rewritten together, and the pin test now includes `UNPARSED-BASE`.

## Rows
Re-anchored or replaced the rows that the restructure orphaned; new rows for: path-outside-repo (2), `.` path, deleted= count, base blob never fetched, base typed from the head blob, head-no-longer-code, symlink/gitlink as regular file (2), base/head link recognition (2), skipped entry uncounted, unknown suffix as a document, foreign side unlisted, shell shebang/suffix (2), unparsed base silent / losing the census / missing from the token (3), removed count missing from the token. Review-2's gap "no row or test covers a deleted symlink, deleted gitlink, or type change" is covered by tests and rows above.

## Open
- Supersession, stated: `test_a_removed_line_in_an_undecodable_base_is_UNREADABLE` encoded the previous behaviour and was replaced (renamed `..._is_unparsed_base_not_unreadable`) by your decision in item 2; no other existing test was weakened.
- The real `--full-suite` run was not repeated (as instructed). The branch_evidence change this round is the exit mapping only.
