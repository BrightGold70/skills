# R23 review: round-22 F2 fix (7c2a1f27), V-11.1 `smoke_assert.py v111`

Baseline: `python3 smoke_assert.py rehearse`, result `REHEARSAL: PASS n=298` (at HEAD 9e1d21c4).
Fixtures: `r23/*.log`, built by `r23/gen.py` (agy; SKILL.md and adapter reads, then canonical `HMAD_HOST=agy python3 h-mad/scripts/h_mad_state_write.py`, then the probe event; all rows ACTIVE+DONE).
Command for each: `cd docs/03-analysis/probes/multi-host-runtime && python3 smoke_assert.py v111 --host agy --log <r23>/<NAME>.log --root /Users/kimhawk/orca/skills`.
Pre-fix comparison: `r23/old_smoke.py` = `git show 7c2a1f27^:.../smoke_assert.py`.

## Verdict: no HIGH, no MED. 3 LOW.

The fix only changes the count. Old code counted the prefix on inner[0], so the count reached v111 only when inner[0] was a script. New code counts it on the first inner command of kind script. Every log that counted before still counts, and the fix adds no counts beyond that. Each textual prefix counts at most once, at every depth (FO10, FO11, FO12, D1, D2). Credit still needs a completed canonical event, which a `bash -c` text can never match. So the fix cannot create a declaration on its own:
- `FO9-nocanon-wrapper-only` (wrapper only, no canonical event) gives UNVERIFIED `declaration not in the canonical form`.
- `FO13` (outer `HMAD_HOST=grok`) gives FAIL `declared another HMAD_HOST`.
- Inner strays `FO5` (echo) and `FO6` (unset) give UNVERIFIED.
- Correct PASS: FO14 (`-m`), FO15 (non-h_mad first script), FO16 (pipe), FO17 (two scripts), FC6 (venv activate), FC7 (`$SKILL_ROOT`), FC9 (`-lc`), FC10 (subshell).

### L1 LOW: the prefix is counted on a script that never runs (spec says "runs a script")
- FO1-exit-before-script `HMAD_HOST=agy bash -c "exit 0; python3 <S>"`: actual PASS (old UNVERIFIED).
- FO2-false-and-script `... "false && python3 <S>"`: PASS.
- FO3-noexec-n `HMAD_HOST=agy bash -n -c "python3 <S>"`: PASS. Live: `bash -n -c` runs nothing.
- Expected by the spec text ("one declaration only when the wrapper runs a script"): UNVERIFIED. Impact is nil. A canonical declaring event is still required, and a one-command env prefix cannot persist. This is a wording issue: the spec should say "names a script", not "runs".

### L2 LOW: a trailing script balances a prefix that also reaches other commands
- FO4-dispatch-then-script `HMAD_HOST=agy bash -c "./hmad-dispatch.sh run; python3 <S>"`: PASS (old UNVERIFIED).
- FO4c-dispatch-toplevel `HMAD_HOST=agy ./hmad-dispatch.sh run`: UNVERIFIED.
- FO7 `... "env > /tmp/e; python3 <S>"`: PASS.
- The same prefix on a non-script is UNVERIFIED at top level but PASS when a wrapper also names a script. The spec explicitly allows this (the prefix "reaches both A and B"). The env effects of other commands are an accepted residual. Record it, don't fix it.

### L3 LOW: fail-closed on compliant wrappers; pre-existing, unchanged by F2 (old = new = UNVERIFIED `used outside an exact declaration`)
- FC1 `cd . && exec python3 <S>`
- FC2 `/usr/bin/env python3 <S>`
- FC5 `command python3 <S>`
- FC8 `timeout 60 python3 <S>`
- FC3 `bash -euo pipefail -c "..."` (the -o rule): the most realistic of these.
- FC4 `bash -c -e "cd . && python3 <S>"`: a misparse. Live bash, zsh and sh all run the string (`bash -c -e 'echo ran'` prints ran), but the classifier takes `-e` as the command string.
- FC11 `if true; then python3 <S>; fi`
- These are UNVERIFIED, not FAIL, and match the top-level forms. Optional: pin FC3/FC4 as known UNVERIFIED.

### Checked and not a finding
ADJ1-dashc-dashe-before-adapter: a script run via `bash -c -e` before the reads gives FAIL `no adapter read`. The issue-order taint voids the reads, so the misparse cannot open the ordering check (control ADJ1-ctrl gives FAIL `script ran before adapter`).
