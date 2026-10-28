# grok-audit-surface — run 7 incident: S2 halted at d1 on an uncontaminated OUT_OF_ROOT (`HOME=/tmp`)

**Date:** 2026-10-23 (run), 2026-10-24 (ruling) · **Run:** `/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261023T110325Z` (kept, never scored)
**Checkout sha at run:** `896b9cf1` (Task 14g) · **Smoke commit:** `0b1dbb8d` (parent `533ed0c5`) on `calibration/grok-audit-surface`
**Status:** incident evidence. Step 9 halted after the d1 cycle; 9a, 10 and 11 were not run.

## What ran (driver `run7-all.sh`, impl-plan v1.15)

| Step | Token |
|---|---|
| 1–4 | `SETUP: OK … list_sha=896b9cf1…`; `D16: cell=pass/pass`; `QUARANTINE: VERIFIED moved=3` → `REQUIRE: OK`; `GROK-CANARY: PASS` → `REQUIRE: OK` |
| 5 | `ASSEMBLER-READING: sha=896b9cf1… dirty=no` |
| 5 grok | `AUDITCYCLE: FAIL must=5 should=3 delivered=report-file`; wall 675 s; `TOOLSCAN: CLEAN calls=44 out_of_root=0 exempt=1` → `REQUIRE: OK` |
| 5 agy | `AUDITCYCLE: FAIL must=2 should=2 delivered=out` |
| 5 codex | `AUDITCYCLE: FAIL must=1 should=0 delivered=report-file` |
| 6 | `ROOT-ACCEPT: grok=accepted agy=accepted codex=accepted`; `TIMEOUT: wall_seconds=675 derived=1020`; **`SMOKE: PASS`** |
| 7 | `COMMIT: OK sha=0b1dbb8d…`, pushed (parent `533ed0c5`) |
| 8 | `QUARANTINE: VERIFIED moved=1` → `REQUIRE: OK` |
| 9 d1 v1 | `AUDITCYCLE: FAIL must=7 should=7 passes=3`; 785 s; **`TOOLSCAN: OUT_OF_ROOT surface=grok calls=46 out_of_root=1 checkout=0 exempt=0 nonjson=6`** → `REQUIRE: STOP` |

## Cause: a shell override of `HOME`, not an escape

The one `out` path is `/tmp`, from a grok `run_terminal_command` at
`…/s2/d1/v1/p3.log:1370`. The command begins
`export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 HOME=/tmp` and then runs `git log -1`,
`git status --short` and `ls -1` on relative paths inside the root. grok set `HOME` so that `git`
would not read the operator's global config. `/dev/null` is exempt; `/tmp` is out of root. The call
named no live-checkout path, no archive source, no other run's state and no other grok session:
`checkout=0`.

This is the third S2 halt with `checkout=0`. Run 4 halted on `grep.pattern` (Task 14f) and run 6 on
`write.content` (Task 14g). Those were scanner false positives, so they were fixed in the scanner.
This one is not a false positive: `/tmp` really is outside the root. Exempting it is not safe,
because Claude session scratchpads live under `/private/tmp/claude-501/`. The scan reported the
truth. The policy built on top of it was too strict.

## Ruling (operator, 2026-10-24): contamination-only halt

The out-of-root scan keeps reporting the truth. The word `OUT_OF_ROOT`, every count and the line
format `TOOLSCAN: <WORD> surface=<s> calls=N out_of_root=N checkout=N exempt=N nonjson=N` are
unchanged. The halt and refusal policy changes: a run stops only on **contamination**, `checkout>0`.

`checkout` is redefined as the contamination count. It now covers:

- the live checkout (as before);
- the needle directories, which are the archive sources (as before);
- **(new)** any path under `<home>/.local/state/h-mad`, the calibration state tree, which holds other
  runs' roots and collected reports. The cycle's own root is there too, but it is classified `inside`
  first, so it never counts as out;
- **(new)** any path under `<home>/.grok/sessions` other than the pass's own session directory. The
  own session stays `exempt`. The sessions directory itself counts as contamination.

Out-of-root paths that are not contamination, such as `/tmp`, `/opt/anaconda3` or
`~/.grok/settings.json`, still count in `out_of_root` and still give the word `OUT_OF_ROOT`. They
neither halt the run nor refuse the score. They are published.

Task 14h (impl-plan v1.16) carries the change:

- the scanner's contamination classes (`scan_log`);
- `require --verb toolscan`, which now accepts `OUT_OF_ROOT … checkout=0`;
- the probe's `containment_checks`, which refuses `out_of_root:<cycle>` only when `checkout>0`, or
  when the scan is `UNREADABLE`.

Run 8 depends on Task 14h.

## Calibration (Task 14h, AC-T14h.4)

Run after GREEN and before run 8. Each recorded grok pass log under `~/.local/state/h-mad/grok-audit-surface` went through two pipelines, each against its recorded root and checkout:

- the 14g scanner (`bae6f97b`) with the old `require --verb toolscan`;
- the 14h scanner (working tree) with the new `require`.

The logs were every S1 log, every re-smoke log, and the S2 `p3` logs of each run. Both pipelines used the real CLIs, with scratch halt files. Script: `calibrate_14h.py`, in the session scratchpad.

- **25 logs. Exactly one `require` outcome changed:** run 7's S2 d1 v1 `p3.log` went from `OUT_OF_ROOT out=1 chk=0`, `STOP` (14g) to `OUT_OF_ROOT out=1 chk=0`, `REQUIRE: OK` (14h). That is the intended fix: the shell `HOME=/tmp` reference is published, not halted.
- **The 14 pre-route-b escape logs** (`run-ab2c85dc2e25` S1 and S2, and run 2's re-smoke) still read `STOP` under 14h. Most now count **more** contamination, because the h-mad state tree and other grok session dirs are new contamination classes. For example, S1 goes from `chk=10` to `15` and S2 d6 v2 from `4` to `13`. S2 d5 v2 goes from `out=5 chk=0` to `chk=3`: it was strict-halted under 14g and is contamination-halted under 14h.
- **Positive control** (old S2 d5 v1 `p3.log`): `chk=14` under 14g and `chk=21` under 14h. It still stops.
- **The other 10 logs** (the re-smokes and S2 cycles of runs 3–7) read `CLEAN`, `REQUIRE: OK` under both pipelines.
