# grok-audit-surface — incident 2026-10-20: an S2 grok auditor wrote to the real checkout

**Status:** S2 stopped by operator decision; not scored. S3 (Task 16) and S4 (Task 17) not run.
**Feature:** grok-audit-surface, Phase 5 Task 15 (impl-plan §"Task 15: S0b, S1, S2 (operator)")
**Calibration ref:** `refs/heads/calibration/grok-audit-surface`; calibration sha `ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7`; smoke commit `f7520e72c87e1c3c34e1c5f25fb3807343d84782` (both pushed and confirmed with `git ls-remote`). No score sha exists.

This record carries metadata only. It quotes no seeded span, no ledger field and no finding text, so it adds nothing the AC-2.6 leak control or `main-leak` must exclude.

## What happened

S2 ran the nine `--passes 3 --surfaces codex,agy,grok --timeout 1140` cycles, three lanes in parallel, each in a fresh `build-root` export root under `$TMPDIR` (`ROOT: READY` on every one). In cycle `s2-d5-v1` (`tdd-gate-fail-opens` design, started 08:04:10, ended 08:23:12 KST), pass 3, the grok agent issued one `run_terminal_command` whose body began:

```
cd /Users/kimhawk/orca/skills
git checkout -q 1254595a -- . 2>/dev/null || true
```

`1254595a` is a real commit on `main` (2026-09-29, `docs(tdd-gate-fail-opens): plan v1.4 …`) that the audited archive document cites. The command overlaid that commit's tree onto the operator's live `main` checkout at **08:08:54**: 370 paths staged and rewritten in the same second (151 modified, 219 re-added), 24 of them under `h-mad/scripts/`, `hmad-dispatch.sh` included. HEAD did not move. The source is the pass's own NDJSON log, `run-ab2c85dc2e25/data/s2/d5/v1/p3.log` under the kept directory.

## Why the containment did not hold

The spec's AC-2.6 git reach check refuses a root that holds a `.git` entry or from which `git rev-parse --git-dir` succeeds, and every dispatch command unsets `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY` and `GIT_ALTERNATE_OBJECT_DIRECTORIES`. Both are true and both are irrelevant here: they stop git reaching a repository *from inside the root*. Nothing stops an agent with a shell tool from `cd`-ing to an absolute path outside the root. The residual the design states for the root (a reach check, not a sandbox) is therefore larger than written: an export root bounds what an auditor is *shown*, not where it can *write*.

## Consequences

- **The real checkout** was restored with `git reset --hard HEAD` (`d4b03fd9`) at about 08:42, after the full diff was saved as a binary patch outside the repo. `git status` is clean and `hmad-dispatch.sh` again matches HEAD.
- **S2 data.** A cycle running at 08:08:54, or started after it, ran some or all of its steps on reverted scripts (assembler, collector, gate, and the bash wrapper itself, which a running bash reads incrementally).

  | doc | cycle | window (KST) | verdict | status |
  |---|---|---|---|---|
  | d1 | v1 | 07:30–07:49 | FAIL | clean |
  | d2 | v1 | 07:49–08:01 | FAIL | clean |
  | d3 | v1 | 08:01–08:17 | FAIL | contaminated |
  | d4 | v1 / v2 | 07:30–07:50 / 07:50–08:04 | UNVERIFIED / FAIL | clean |
  | d5 | v1 | 08:04–08:23 | FAIL | contaminated (the escaping cycle) |
  | d6 | v1 | 08:23–08:36 | FAIL, `RECORD: REFUSED stem_prefix:0` | contaminated (old wrapper staged to `/tmp`) |
  | d7 | v1 | 07:30–07:46 | FAIL | clean |
  | d8 | v1 | 07:46–07:58 | FAIL | clean |
  | d9 | v1 / v2 | 07:58–08:17 / 08:17 | UNVERIFIED / `assemble_halt:p1`, not recorded | contaminated |

  After the restore, d3, d5 and d6 were re-run once each as v2, with a watcher polling `git status` every 5 s (it never fired): d3-v2 `UNVERIFIED unscorable_report:p2`, d5-v2 `FAIL`, d6-v2 `FAIL`, all recorded.
- **Extract refuses, correctly.** `extract --repo . --base-sha <smoke commit> …` prints `FINDINGS: UNREADABLE reason=cycle_token:d3.v2`: `stands()` admits a v2 only after an `UNVERIFIED` v1, and the probe has no record for a cycle voided by an outside event. The records were not renamed or deleted to get past it.
- **Sibling lanes.** Any process that read `h-mad/` through `~/.claude/skills` between 08:08:54 and ~08:42 read the reverted scripts. A HemaSuite `pytest tests/` run was in flight in that window; its result should not be trusted.

## What is still owed

1. A containment decision before any further grok dispatch against seeded documents: a read-only checkout for the run, a separate clone the auditor cannot name, or an agent-side sandbox. The watcher only detects.
2. Then either a fresh S2 run (all nine documents as v1 in a new run directory) or a probe amendment for operator-declared void cycles, through the spec and design authors.
3. Task 16's measurement doc should cite this record, and the S4 grok routing (Task 17) must not run on the strength of an audit surface that can write outside its root.

The S2 records, both rounds, remain in `$HOME/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/data/s2/`.
