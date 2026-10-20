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

1. ~~A containment decision before any further grok dispatch against seeded documents.~~ **Decided 2026-10-20: agent-side sandbox, grok `--sandbox strict`, plus moving the roots.** See §"Containment decision" below. The decision is not yet implemented, and no grok dispatch against seeded documents may run until it is.
2. Then either a fresh S2 run (all nine documents as v1 in a new run directory) or a probe amendment for operator-declared void cycles, through the spec and design authors.
3. Task 16's measurement doc should cite this record, and the S4 grok routing (Task 17) must not run on the strength of an audit surface that can write outside its root.

The S2 records, both rounds, remain in `$HOME/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/data/s2/`.

## Containment decision (2026-10-20)

**Chosen: an agent-side OS sandbox.** The other two options do not stop the observed command. A read-only checkout is one `chmod` away for an agent with a shell, and "a clone the auditor cannot name" cannot be enforced, because the agent found the live path anyway. S2's grok legs ran with **no** `--sandbox`: `data/s2/d5/v1/command.txt` carries none, and `hmad-dispatch.sh` sets a default only for codex (`workspace-write`, `exec`'s `sandbox=` default). `exec` already passes `--sandbox` through to grok verbatim.

**Evidence: grok 1.0.62, macOS 27.0.1 Seatbelt, `--sandbox strict`.** These were live canaries, run headless with `--always-approve`, exactly as dispatch does:

| probe from cwd = root | result |
|---|---|
| write `/Users/kimhawk/orca/skills/<file>` (the escape class) | refused, `Operation not permitted` |
| `git -C /Users/kimhawk/orca/skills log`, read a repo file | refused |
| read or write a file under `$HOME/.local/state/` | refused |
| write inside cwd | allowed |
| `--prompt-file` outside cwd and system temp | grok exits rc=1 (`Failed to read … Operation not permitted`), which fails closed |
| unknown profile name | rc=1, no work done, which fails closed |
| read or write a **sibling root under `$TMPDIR`** | **allowed**: strict grants the whole system temp (`$TMPDIR`, `/private/tmp`) |
| read or write a sibling root under `$HOME/...`, with `TMPDIR` pointed into the own root | refused |
| read a file in the real `$TMPDIR`, even with `TMPDIR` overridden | allowed |

**What the implementation therefore owes.** Each of these goes through `spec-author`, then `design-author`, then TDD. Do not hot-patch on `main`, because the feature sits at `phase=step5` with the TDD gate armed:

1. **grok defaults to `--sandbox strict` in dispatch** (both `exec` and `exec-pane`). Overriding it to anything weaker needs an explicit flag that gets recorded.
2. **Export roots move out of system temp.** `build-root` currently uses `$TMPDIR`, and every parallel lane is then readable and writable by every other. The roots go under the run directory instead (`~/.local/state/h-mad/<feature>/run-*/roots/<cycle>/`), where strict denies everything except cwd.
3. **The grok prompt is staged inside `cd_dir`**, not with `mktemp -t` (`hmad-dispatch.sh`, `bounded_prompt`). Each grok child also gets `TMPDIR=<root>/.tmp`. Nothing seeded may be written to system temp, since strict leaves it readable.
4. **A per-run preflight canary.** grok documents that when "the sandbox cannot be applied … Grok logs a warning and continues without enforcement". That branch could not be triggered, and `~/.grok/sandbox-events.jsonl` was never written, so nothing positively shows a profile was applied. Before a run's first grok leg, dispatch must make one grok call under the same profile, asking it to write a file outside the root. If that file exists, or the log lacks `Operation not permitted`, the run is refused. A canary that cannot run is refused as well, never treated as passed.
5. **Optional hardening:** an outer `/usr/bin/sandbox-exec` wrapper, which does not depend on grok's own sandbox code. Not required.

**Out of scope here but the same class.** agy has no sandbox by default, and codex `workspace-write` was not probed against a sibling root. The relocated roots in point 2 protect against those legs too, but neither leg's sandbox is verified. Record that as a residual in the design, not as contained.

**Residuals.** Strict leaves system temp readable, which includes Claude session scratchpads under `/private/tmp`. Only non-seeded material may live there. The model's own in-process network is not restricted, and needs no restriction for this threat.

## S2 route decision (2026-10-20)

**Chosen: route (b), a probe amendment for operator-declared void cycles.** It is one corrective spec and design revision, which also carries §"Containment decision" items 1–4. The operator decided both points on 2026-10-20.

- **A void cycle is not an outcome, so it does not use up AC-3.4's single re-dispatch.** The stands rule runs over the non-void cycles of each document, and each document may still have at most two non-void cycles. The `v3` refusal (`M:GAS-CYCLE-V3`) is relaxed only as far as the voids require. How a void is declared is for the design to settle: a marker in the cycle directory, citing this record, and the measurement doc publishes every void.
- **What this means for each document, using the recorded verdicts:**
  - d1, d2, d7 and d8: v1 stands.
  - d4: v2 stands, as before.
  - d5 and d6: v1 is void, and v2 (FAIL, clean) stands.
  - **d3**: v1 is void and v2 is `UNVERIFIED`. It needs **v3**, a fresh grok dispatch.
  - **d9**: v1 ran from 07:58 to 08:17, across 08:08:54, so it is void. Its v2 was never recorded and is void too. It needs a **fresh cycle**.
- **So route (b) still dispatches grok**, for d3 and d9, and those two runs wait on the containment implementation.

## S2 route reversed to (a), from new evidence (2026-10-20)

**grok read the unseeded originals in 11 of the 12 recorded S2 cycles.** Every `tool_call` `rawInput` in every pass log under `data/s2/` was extracted line by line with `jq -R 'fromjson?'`, as in the probe below. The check has a positive control: the d5 v1 escape is visible to it, at 14 calls. A first, non-tolerant pass read d5 v1 as 0 and was discarded. These are the counts of tool calls naming `/Users/kimhawk/orca`:

| leg | cycles touching the live checkout | what it touched |
|---|---|---|
| grok (pass 3) | **11 of 12**. Only d5 v2 is clean. d1 v1 31/45, d3 v1 52/64, d7 v1 39/55, d8 v1 17/65, and so on | It read, grepped and `find`-ed the **original archived documents** in the live checkout, for example `read_file`/`grep` on `docs/archive/2026-10/agy-coder-fallback/agy-coder-fallback.design.md`. That is the answer key: the seeds are the difference between those files and the export root. |
| codex (pass 1) | 2 of 12: d6 v2 `ls -ld /Users/kimhawk/orca/skills`; d9 v1 `git rev-parse HEAD` and `git diff --stat … -- h-mad` with cwd in the live checkout | Only metadata and code. No archived document was read. |
| agy (pass 2) | 0 of 12 (`step_update` tool steps) | — |

```bash
S=~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/data/s2
for f in $S/d*/v*/p3.log; do
  jq -R -c 'fromjson? | select(type=="object" and .type=="tool_call") | .rawInput' "$f" \
    | grep -cE '/Users/kimhawk/orca'
done
```

**Consequence.** No grok reading from this S2 run is a valid measurement, whether the cycle was void or not. Route (b) cannot rescue it, because the whole-cycle stands rule would keep the contaminated grok legs of d1, d2, d4, d6, d7 and d8. **The operator chose route (a) on this evidence:** once containment ships, run a fresh S2 of all nine documents on all three surfaces, as v1 in a new run directory under `--sandbox strict`. The void-cycle amendment is dropped. This S2 run is kept as incident evidence only, and is never scored.

**This also widens what the containment is for.** `strict` bounds *reads* to the CWD and system paths, not only writes. For measurement validity, that read bound is the property that matters. codex `workspace-write` and agy have no verified read bound. The measurement therefore publishes this same out-of-root tool-call scan for every standing pass of every surface. A pass that touched the live checkout or an original document is a finding.
