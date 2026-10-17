# Triage of backlog task #5 + skill-candidate OPEN rows — 2026-10-18

Repo `/Users/kimhawk/orca/skills` @ main `3d6c260e`. Only `docs/skill-candidates.md` edited (16 inserted lines, 0 deleted). Nothing committed.

Census (`python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`):
- before: `candidates=282 OPEN(yes+maybe)=17` (not 13: rows 2610/2615/2618/2623 were appended 2026-10-17 after the "OPEN=13" count)
- after: `candidates=282 OPEN(yes+maybe)=15 SUPERSEDED=12`, coverage `parsed=288 row-shaped=288`; `handoff/tests/test_skill_candidates_census.py` 48 passed.

## Line-number findings (read first)

The #5 line numbers were stale in the handoffs that carried them, not only now. Blob-mapping:
- The 2026-10-12 set "2364, 2395, 1269, 2481, 2496" (blob `90fb4c70`, the 10-12 handoff's commit) = **reachability (now 2368), host-equivalent (now 2400), archreview tree-diff (1269), agreement-check mutants (now 2488), flake reproducer (now 2504)**. The handoff `2026-10-12-main__fence-probe-hmad-todo-rebuild.md:45-51` confirms 2364/2395/2481/1269 by name. The brief's hints for 2364 ("doc consumers") and 2395 ("preflight()") point to different rows; both of those are LANDED anyway. 2496 is in the flake row in `90fb4c70` and in the (LANDED) BashParse-sweep row in `fb6585e5`. Both readings are covered below.
- The 2026-10-05 set "1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288" maps to different rows in each blob: `ef241d9f` (10-04) and `beb17ac8` (10-05) disagree with each other and with today. **Every row that any of these readings can point to is now terminal** (table B). No row from that set is still open.
- "Review residuals on rows 1406/1937/1685" are from the 2026-10-05 numbering (handoff `2026-10-05-main__backlog-burn-to-five.md:55,79`). Their commits are `4739cd58` (four-clock liveness, now row 1412), `132f056f` (evidence distinct targets + pass logs, now row 2010) and `530e4564` (expect-N screens, now row ~1700). The brief's hints (census `__main__` guard, absent-find lint, suffixed report path) point to different rows, which are all LANDED.

## A. OPEN rows (census list, current lines after the edit)

| # | name | orig ref | cur line | verdict | evidence | size | value |
|---|---|---|---|---|---|---|---|
| 1 | archreview scorer tree-diff | #5 1269 | 1269 | STILL-OPEN (deferred, trigger unfired) | `grep -liE "audit…(changed…tree)\|tree delta: [1-9]" docs/handoffs/2026-10-1[2-8]-*.md` → rc=1, 0 files; `h_mad_archreview_cycle.py` has no git-status snapshot; `hmad-dispatch.sh:3457` prints an absolute `tree delta:` count only, no `--read-only` | S | low until trigger fires |
| 2 | mutation REACHABLE before caught | #5 2364 (10-12 numbering) | 2369 | STILL-OPEN (deferred) | `grep -niE 'reachab\|delete.line' h_mad_mutation_harness.py` → only prose `:575` | M | low; trigger unfired |
| 3 | EQUIVALENT on one host | #5 2395 (10-12) | 2402 | STILL-OPEN (deferred) | `grep -nE 'requires\|HOST_EQUIV' h_mad_mutation_harness.py` → 0 relevant | M | low; 1/1498 mutants |
| 4 | agreement-check mutants → stubbed-oracle hint | #5 2481 (10-12) | 2491 | STILL-OPEN (maybe) | `grep -niE 'redundan\|masked\|later guard' harness` → 0; no SURVIVED recurrence in 10-12..17 handoffs | S | low |
| 5 | flake reproducer (load × signal) | #5 2496 (10-12, one reading) | 2508 | STILL-OPEN (narrowed) | `grep -rniE 'reproduce.flake' h-mad handoff` → 0; `h_mad_failure_diff.py --repeat N` + `FLAKY` (`:43`) partly overlaps | M | low; 0 flakes since 10-08 |
| 6 | (b) Codex Phase-5 allowlist vs gate-task readings | — | 2538 | CANNOT-JUDGE (not annotated) | `READ_ONLY_COMMANDS` at `h_mad_target_identity.py:225` (since `54e2646f`, 2026-09-18) and the operator allowance file (`81920a9d`, 2026-10-04) both **predate** the 10-05 incident, and the row never names which commands were refused. The gap can't be re-derived without the HemaSuite incident log. | ? | ask the HemaSuite lane which probe was refused |
| 7 | (d) Regression guards vs 5d-before-5e | — | 2549 | STILL-OPEN | `h_mad_assemble_tdd.py:517-523` renders every guard "must pass from the first run"; `codex-implementer-prompt.md:70` same; the GREEN comment at `:530` covers mutation rows, not sequencing | S | med: false BLOCKED |
| 8 | (e) TDD judge 40 s budget starvation | — | 2555 | STILL-OPEN | `h_mad_tdd_judge.py:29` `JUDGE_BUDGET_S = 40.0`; `resolve()` `:288-332` collects every task's tests in plan order; `main()` has no budget arg | S | med: writes refused `kind=timeout` |
| 9 | census `--rev <ref>` | 2576 | 2583 | STILL-OPEN (rec 2) | `skill_candidates_census.py:156-159` parses `--list-open` only | S | med: stops pins flapping on other lanes' WIP |
| 10 | apply decisions table by open-line | 2582 | 2590 | STILL-OPEN (rec 2, rated yes by dup) | same, no `--apply` | M | med: 2 hand-scripted passes, `\|` escape trap |
| 11 | census `--rev` (dup) | 2595 | 2604 | SUPERSEDED → 2576 | duplicate; recurrence carried | — | — |
| 12 | apply table (dup) | 2598 | 2608 | SUPERSEDED → 2582 | duplicate; rec + `\|` trap + yes carried | — | — |
| 13 | mutation sweep in isolated worktree | 2603 | 2614 | STILL-OPEN | `grep -nE 'worktree\|isolat\|detach' h_mad_mutation_harness.py` → 0; reuse `h_mad_failure_diff.py` worktree lifecycle | S–M | high: rec 5; in-place mutation hits live HemaSuite sessions via symlink |
| 14 | assembler `gate`-shape path | 2610 | 2622 | STILL-OPEN | `h_mad_assemble_tdd.py:649` choices `("red","green")` | S | high: rec 5 hand prompts |
| 15 | assembler multi `--test-path` | 2615 | 2628 | STILL-OPEN | `h_mad_assemble_tdd.py:652` single `required=True` | S | med: broken re-run line |
| 16 | declarable sandbox teardown artefact | 2618 | 2632 | STILL-OPEN | `h-mad/tests/leak_reaper.py:34` unconditional `ps -axo` (only commit `4affd9e0`); `--env-known-failure` node-ids only (`:662`) | S | high: rec 20, 3 false BLOCKED |
| 17 | wire registry `verify` interpreter | 2623 | 2638 | STILL-OPEN (narrowed) | `--python` already at `h_mad_wire_registry.py:775` since `198a1a14` (2026-08-21), default `sys.executable`; missing: pytest probe on the default and a `register` warning for a non-repo-relative pin | S | med |

## B. #5 "deferred rows" and review residuals that are already terminal (re-verified in tree, no new line appended)

| name | orig ref(s) | cur line | verdict | tree evidence |
|---|---|---|---|---|
| a mutation that can never fire (self-match lint) | 1931 / 1937 | 1926 | LANDED (prior, re-verified) | `h_mad_mutation_harness.py:815,832` self-match diagnosis (`8d1edf05`) |
| `hmad-dispatch probe` | 1624 | 1621 | LANDED (prior) | `hmad-dispatch.sh:4452` `probe) _cmd_probe` |
| delta-self-review verb | 1662 | 1639 | LANDED (prior) | `h-mad/scripts/h_mad_delta_stage.py` exists |
| suffixed report path for re-dispatch | 1679 / 1685 | 1678 | LANDED (prior) | `h_mad_assemble_audit.py:581` `report_path_handed` HALT |
| live-shape-probe-before-the-gate | 1387 | 1387 | LANDED (prior) | `h-mad/invariants.base.md:238` |
| ask what a node asserts when nothing implemented | 1348 | 1336 | DECLINED (prior) | row's own calibration; no change needed |
| grep the ENFORCEMENT / positional shell arg | 2113 (prose block) | 1840, 1871 | LANDED (prior) | `h-mad/tests/test_skill_body_renderer_args.py` |
| calibrate a ranking screen (#56, 177 rows) | 2288 | 2286 | DECLINED (prior, useful-not-codable) | lesson in `docs/learnings.md` |
| name the tests that parse a doc | 2364 (brief's hint) | 2362 | LANDED (prior) | `h-mad/scripts/h_mad_doc_consumers.py` |
| audit-prompt preflight false-HALT | 2395 (brief's hint) | 2394 | LANDED (prior) | `h_mad_assemble_audit.py:141` `fill_slots` |
| census `__main__` guard | 1406 (brief's hint) | 1406 | LANDED (prior) | `skill_candidates_census.py:299` |
| commit the BashParse sweep as a test | 2496 (alt reading, `fb6585e5`) | 2494 | LANDED (prior) | row's own LANDED note |
| alt-mapped 10-04/10-05 rows: wrapped bold row (1976), carry-forward-sources (1634), freeze-candidate (1686), collect-report refuse (1670), measure a gate (2205), data fixture floods (1959), backlog row names refusing test (2135), batch-payload builder (2317) | 1931…2288 in blobs `ef241d9f`/`beb17ac8` | as listed | all LANDED/DECLINED | census TERM marker per row |

## C. Non-row items

| item | source | verdict | evidence | size | value |
|---|---|---|---|---|---|
| Review residual "1406": four-clock liveness limits (ps argv, merge-imported commits, codex/agy two clocks) | row 1412 note `:1415` | STILL-OPEN (watch-only, reopen-on-observation) | no commit to `h_mad_state_ownership.py` since `4739cd58` (`git log --since=2026-10-05`); `liveness_evidence` `:85` unchanged; no false LIVE/QUIET reported | M | low |
| Review residual "1937": evidence targets — codex unmeasured until `--json`; pass-log retention | row 2010 note `:2048` | STILL-OPEN | see pass-log row | S | low |
| Review residual "1685": expect-screens round 11 (M1–M7) | row ~1700 `:1716` | SUPERSEDED by the BashParse third reader | Spike #22 + rounds 12–17 FIXED (`:1717-1760`); `h_mad_expect_screens.py:85` `BashParse` | — | drop from carry |
| Accepted over-refusals (2026-10-06) | `measurement-discipline.md` §FREEZE | not a task: accepted by user decision 2026-10-05 | row ~1700 "Decided 2026-10-05 (user)" | — | drop from carry |
| Pass-log rotation | `:2048` | STILL-OPEN | `grep pass-logs h-mad/scripts/*.py` shows no prune/cap (`h_mad_audit_cycle.py:605`); HemaSuite `.h-mad/pass-logs` = 41 files, 20M; skills = 11 | S | low (20M) |
| `#56` residue trichotomy | `2026-09-15-main__two-false-task-premises.md:135` | not a task: deliberate convention | "Not a defect to fix; a convention to know" | — | drop from carry |
| graft statusline | `2026-10-05-main__backlog-burn-to-five.md:67` | LANDED (outside repo); the carry's path is stale | `~/.claude/settings.json:315-317` → `hud/omc-hud-graft.sh` (exists, 829 B); `omc-graft-statusline.sh` no longer exists | — | drop from carry |
| V-11.1 residuals | `2026-10-01-main__v111-file-tool-only.md:69-77` | not a task: deferred by design | accepted in the spec + `live-smoke.md` addenda | — | drop from carry |
| `tdd-gate-fail-opens` bookkeeping | report `:176-203` | **LANDED 2026-10-02** (`9e1d21c4`). The carry has been stale for 16 days | `docs/archive/2026-09/tdd-gate-fail-opens/probes/`: `reading-fixed.txt` has 80 `MANUAL:` lines; `t7-recheck-2026-10-02.md`, `t8-census-2026-10-02.txt`, `control4-absent-line.txt` all present | — | drop from carry |
| Bash pin blast radius | `2026-10-12-…fence-probe…md:77` | STILL-OPEN but inert | re-ran `h_mad_bash4_fence_probe.py /Users/kimhawk/orca/HemaSuite` → `TOTAL docs=570 blocks=1138 regex_hits=0 parse32_only=5 parse_both=37 unreadable=0`; all 5 are `screens=no exec=no` in 2 `docs/superpowers/plans/2026-05-22-*` docs | S | close as accepted |
| "concurrent HemaSuite sessions share the live skill" | 10-17 carry | duplicate of row 2603 (now 2614) | — | — | fold |
| HemaSuite feature/204 no-mutation-spec (4 probe scripts) | 10-17 carry NS2 | CANNOT-JUDGE (HemaSuite's call, not investigated) | — | — | — |

## Ranked shortlist (STILL-OPEN, worth doing)

1. **2632 declarable sandbox teardown artefact** (S): recurrence 20 and 3 false Codex BLOCKED. An env opt-out in `leak_reaper.find_leaked` plus one template line.
2. **2622 assembler `--phase gate`** (S): 5 hand prompts in one feature, each retyping the same rules. Same file as 3 and 4, so build them together.
3. **2628 repeatable `--test-path`** (S): the printed re-run line is broken today. Same file as 2.
4. **2614 mutation sweep `--isolate`** (S–M): recurrence 5, and an in-place sweep can corrupt live HemaSuite runs through the symlink. Can reuse the worktree lifecycle in `h_mad_failure_diff.py`.
5. **2555 TDD-judge budget: active-task-first ordering** (S): it refuses legitimate RED writes as `timeout`.
6. **2583 + 2590 census `--rev` / `--apply`** (S + M): recurrence 2 each. `--rev` is near-trivial (`git show`). `--apply` needs `\|` unescaping and an OPEN-delta print.
7. **2638 wire-registry pytest probe + `register` relative-pin warning** (S): `--python` already exists, so only the default-path probe is missing.
8. **2549 regression-guard scope note** (S): a one-line template change in `h_mad_assemble_tdd.py:517-523` and `codex-implementer-prompt.md:70`.

Kept off the list: trigger-deferred rows 1269, 2369, 2402, 2491, 2508 (no trigger fired); 2538 (CANNOT-JUDGE).
