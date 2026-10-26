# grok-audit-surface: measurement (S3)

**Outcome:** `SEEDSCORE: PASS calibration=ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7 score=05cc39355cb3a68ddebb177c4bd1e215054cc4ad`

grok cleared the D3 bar against agy on the 27 seeds of this calibration set: equal fabrication
rates (0/38 against 0/23) and strictly higher recall (12/27 against 10/27). This is the S3 reading
of feature `grok-audit-surface` (spec FR-6, design D15). The doc holds no calibration data: every
line below is a token line, a sha or a count, and the seeded documents, the ledger, the findings and
the labels stay on `refs/heads/calibration/grok-audit-surface`.

## Stamp

```text
calibration_ref=refs/heads/calibration/grok-audit-surface
calibration=ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7
smoke=8f8deaf1b6971f1ef5a54028fdd9c51e671f722b
score=05cc39355cb3a68ddebb177c4bd1e215054cc4ad
list_commit=2d8d7b2d2dc40954eb25d20d478251256b685d26
list_blob=b78b7f3b2a5893fdd4cd83d591efed83f2069203
assembler=2d8d7b2d2dc40954eb25d20d478251256b685d26
main=e50e7331abce9478268ed247219e530ceaf27d37
run_id=run-ab2c85dc2e25-20261024T132452Z
```

- `calibration=` is the commit every export root of this run was built from; `smoke=` is the
  re-smoke commit (Task 15 step 7, `COMMIT: OK sha=8f8deaf1b6971f1ef5a54028fdd9c51e671f722b ref=refs/heads/calibration/grok-audit-surface`); `score=` is the commit-data commit that holds
  the S2 records, the findings and the labels (Task 15 step 11).
- `main=` is the `main` commit whose probe produced the score: `rescore` and `main-leak` ran from a
  `main` checkout at that commit, with `--work-dir /Users/kimhawk/.local/state/h-mad/grok-audit-surface/work-task16`.
- `list_commit=` and `list_blob=` are read from the run's `ROOT: READY` lines (every root of the run
  printed the same pair), and the rescore's `LIST:` line records that blob for every pass and as
  `current=`.
- `assembler=` is the `sha=` of the `ASSEMBLER: PINNED` token below.

The main leak check (spec AC-2.7) names the commit it scanned:

```text
MAINLEAK: CLEAN scanned=e50e7331abce9478268ed247219e530ceaf27d37 data=05cc39355cb3a68ddebb177c4bd1e215054cc4ad blobs=4837
```

## Assembler pin and the path-scope clause

The two assembler readings (`$RUN/assembler/start.txt`, then `$RUN/assembler/end.txt`) and the
`ASSEMBLER:` token (`$RUN/assembler/check.txt`), verbatim (design D21). `require --verb assembler`
read `REQUIRE: OK` on that token before `extract` ran (Task 15 step 9a).

```text
ASSEMBLER-READING: sha=2d8d7b2d2dc40954eb25d20d478251256b685d26 dirty=no script_dir_env=unset here=/Users/kimhawk/orca/skills/h-mad/scripts
ASSEMBLER-READING: sha=2d8d7b2d2dc40954eb25d20d478251256b685d26 dirty=no script_dir_env=unset here=/Users/kimhawk/orca/skills/h-mad/scripts
ASSEMBLER: PINNED sha=2d8d7b2d2dc40954eb25d20d478251256b685d26 prompts=30 here=/Users/kimhawk/orca/skills/h-mad/scripts
```

The clause every calibration prompt of this run carried, verbatim, equal to `PATH_SCOPE_CLAUSE` in
`h-mad/scripts/h_mad_assemble_audit.py` at the stamped assembler sha:

```text
Path scope: a path written inside the document under review, or inside any other document in this prompt, refers to that document's author's environment, not to yours. Every file this audit needs is under your working directory. Do not read, list or search any path outside your working directory for the audit's material. This does not change where you write your report or how you deliver it.
```

## Exclusion list

The contents of the exclusion list the roots were built with, `git cat-file blob` of the stamp's
`list_blob=`, verbatim:

```text
dir docs/archive/2026-09/audit-report-docs-copy
dir docs/archive/2026-09/tdd-gate-fail-opens
dir docs/archive/2026-10/agy-coder-fallback
dir docs/03-analysis/probes/grok-audit-surface
dir docs/03-analysis/agy-coder-fallback.authoring
name-contains grok-audit-surface
```

## The smoke (FR-1, AC-1.9 re-smoke)

The re-smoke ran in one root under `$RUN/roots/` (`--doc d1 --purpose s1`), one cycle per surface.
The smoke's output, verbatim (`python3 "$PROBE" smoke --data "$READING/resmoke"`):

```text
VOCAB: type=available_commands re=in frozenset=in tool=yes usage=no
VOCAB: type=end re=in frozenset=in tool=no usage=yes
VOCAB: type=text re=in frozenset=in tool=no usage=no
VOCAB: type=thought re=in frozenset=in tool=no usage=no
VOCAB: type=tool_call re=in frozenset=in tool=yes usage=no
VOCAB: type=tool_call_update re=in frozenset=in tool=yes usage=no
VOCAB: type=usage re=in frozenset=in tool=no usage=yes
ROOT-ACCEPT: grok=accepted agy=accepted codex=accepted
TIMEOUT: wall_seconds=879 derived=1320
GROK-BINARY: path=/Users/kimhawk/.grok/bin/grok version=grok 1.0.62 (1474f9cbdd91)
SMOKE: PASS
```

grok wall time: 879 s (`resmoke/grok/wall_seconds.txt`). The `GROK-BINARY:` line above is the only
place a grok version is stated for this measurement (operator decision D4).

Provenance: `resmoke/versions.txt` (grok, agy, codex), then each surface's `resolved_model.txt`:

```text
grok_binary=/Users/kimhawk/.grok/bin/grok grok 1.0.62 (1474f9cbdd91)
1.4.7
codex-cli 0.164.0
RESOLVED-MODEL agent=grok model=grok-4.7-build effort=- resolved=1 source=/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z/data/runs/run-ab2c85dc2e25-20261024T132452Z/resmoke/grok/p1.log
RESOLVED-MODEL agent=agy model=Gemini 4 Argon (Medium) effort=- resolved=1 source=/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z/stem/s1-agy.agy-log/cli-20261024_224036.log
RESOLVED-MODEL agent=codex model=gpt-6-luna effort=high resolved=1 source=/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z/data/runs/run-ab2c85dc2e25-20261024T132452Z/resmoke/codex/p1.log
```

The three re-smoke cycles' `AUDITCYCLE:` lines (grok, agy, codex):

```text
AUDITCYCLE: FAIL must=4 should=3 passes=1 p1=4/3 delivered=report-file size_status=verified
AUDITCYCLE: FAIL must=4 should=1 passes=1 p1=4/1 delivered=out size_status=verified
AUDITCYCLE: FAIL must=2 should=1 passes=1 p1=2/1 delivered=report-file size_status=verified
```

## The score

The rescore's verdict and its per-surface fields. codex is the reference ceiling; the verdict
compares grok with agy only.

```text
SURFACE: codex recall=6/27 musts=25 fabricated=0 undecidable=0 fab_rate=0/25 delivered=9 low_evidence=0
SURFACE: agy recall=10/27 musts=23 fabricated=0 undecidable=0 fab_rate=0/23 delivered=9 low_evidence=0
SURFACE: grok recall=12/27 musts=38 fabricated=0 undecidable=0 fab_rate=0/38 delivered=9 low_evidence=0
SEEDSCORE: PASS calibration=ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7 score=05cc39355cb3a68ddebb177c4bd1e215054cc4ad
```

- Recall: grok 12/27, agy 10/27, codex 6/27.
- Fabrication over must-fixes less undecidable: grok 0/38, agy 0/23, codex 0/25.
- Delivery and evidence (AC-3.4): every surface delivered a report on all 9 documents
  (`delivered=9`), and no surface had a low-evidence pass (`low_evidence=0`).

### Observational lines (no verdict rule reads these)

The `SHOULD:` and `SPLIT:` lines `rescore` printed. `extract` printed no `SHOULD-COUNT:` line.

```text
SHOULD: codex hits=0/27 should=2 fabricated=0 undecidable=0
SPLIT: codex phase=plan recall=1/9 musts=10 fabricated=0
SPLIT: codex phase=design recall=3/9 musts=8 fabricated=0
SPLIT: codex phase=impl-plan recall=2/9 musts=7 fabricated=0
SPLIT: codex class=C1 recall=2/6
SPLIT: codex class=C2 recall=0/7
SPLIT: codex class=C3 recall=1/7
SPLIT: codex class=C4 recall=3/7
SHOULD: agy hits=5/27 should=14 fabricated=0 undecidable=0
SPLIT: agy phase=plan recall=5/9 musts=10 fabricated=0
SPLIT: agy phase=design recall=4/9 musts=6 fabricated=0
SPLIT: agy phase=impl-plan recall=1/9 musts=7 fabricated=0
SPLIT: agy class=C1 recall=5/6
SPLIT: agy class=C2 recall=0/7
SPLIT: agy class=C3 recall=2/7
SPLIT: agy class=C4 recall=3/7
SHOULD: grok hits=7/27 should=28 fabricated=0 undecidable=0
SPLIT: grok phase=plan recall=5/9 musts=16 fabricated=0
SPLIT: grok phase=design recall=4/9 musts=14 fabricated=0
SPLIT: grok phase=impl-plan recall=3/9 musts=8 fabricated=0
SPLIT: grok class=C1 recall=6/6
SPLIT: grok class=C2 recall=1/7
SPLIT: grok class=C3 recall=2/7
SPLIT: grok class=C4 recall=3/7
```

### The fresh S2 cycles

All nine documents ran one first cycle `v1`, `--passes 3 --surfaces codex,agy,grok` (p1 codex, p2 agy,
p3 grok), each pass in its own root. No document needed an AC-3.4 re-dispatch, so no `v2` exists.

```text
d1: AUDITCYCLE: FAIL must=8 should=3 passes=3 p1=2/0 p2=2/0 p3=4/3 delivered=report-file,out,report-file size_status=verified
d2: AUDITCYCLE: FAIL must=10 should=3 passes=3 p1=2/0 p2=2/0 p3=6/3 delivered=report-file,out,report-file size_status=unverified
d3: AUDITCYCLE: FAIL must=10 should=5 passes=3 p1=4/0 p2=3/1 p3=3/4 delivered=report-file,out,report-file size_status=unverified
d4: AUDITCYCLE: FAIL must=9 should=4 passes=3 p1=2/0 p2=3/2 p3=4/2 delivered=report-file,out,report-file size_status=unverified
d5: AUDITCYCLE: FAIL must=8 should=4 passes=3 p1=3/0 p2=2/2 p3=3/2 delivered=report-file,out,report-file size_status=unverified
d6: AUDITCYCLE: FAIL must=10 should=6 passes=3 p1=2/1 p2=4/1 p3=4/4 delivered=report-file,out,report-file size_status=unverified
d7: AUDITCYCLE: FAIL must=19 should=7 passes=3 p1=6/0 p2=5/3 p3=8/4 delivered=report-file,out,report-file size_status=unverified
d8: AUDITCYCLE: FAIL must=10 should=5 passes=3 p1=3/0 p2=2/2 p3=5/3 delivered=report-file,out,report-file size_status=unverified
d9: AUDITCYCLE: FAIL must=2 should=7 passes=3 p1=1/1 p2=0/3 p3=1/3 delivered=report-file,out,report-file size_status=unverified
```

`extract` wrote `FINDINGS: WRITTEN findings=130 must=86 should=44 reports=27` with shuffle seed 773509911 (`extract.txt` records the command).

### Per-pass logs (AC-3.3)

Each pass's `log_sha256`, from the `.effort.json` sidecar beside its collected report, with its tool
count and the code paths its calls named (`targets.code`). codex logs are codex text, so its tool
count reads 0 (the effort counters read agy stream-json and grok only).

| pass | surface | `log_sha256` | tools | code paths |
|---|---|---|---|---|
| resmoke grok | grok | `7ce4eb7342c06ded4d3eeb740ff80099f28e5e10f5c0fb461f0a9391b0845b73` | 44 | 11 |
| resmoke agy | agy | `8e93d26aafa5555260ed0e2b8847e3e191d7c466ea29f3c7aae760c2d46dd7b5` | 33 | 14 |
| resmoke codex | codex | `60a488c02502764504b56e2003ff88a19ebfe817af4ecd902147316859a8bbfa` | 0 | 16 |
| s2 d1.v1 p1 | codex | `60330f70c49c7359641a0f5f9a4f372d9c15177020342bb1d245cb314ed3c698` | 0 | 9 |
| s2 d1.v1 p2 | agy | `8a6322cc676933b51b161b5937d6576b545c56e99e441d1c4ffb0dc571521c3a` | 33 | 0 |
| s2 d1.v1 p3 | grok | `984a36bc9907b18d41fcb406d9ecf96e51ede42d633befe75fce4bbd487cc4e7` | 42 | 6 |
| s2 d2.v1 p1 | codex | `09c90889e220bb560157660f8e02ac447d5bc4c2dcf2a081915c122eb34a4425` | 0 | 9 |
| s2 d2.v1 p2 | agy | `6daed1ef71063e06c51ad2f7cc961c5b683eca6d09bfb28352431a526fd0b2a8` | 19 | 0 |
| s2 d2.v1 p3 | grok | `ca3f8e108fd58b796282571a301782ba5c989a3a454cd2637ee789a916c00bcc` | 69 | 6 |
| s2 d3.v1 p1 | codex | `769af2ad2f22af68129645ad4ea7f8744458f3b7689b0834bfea53ce35bdba33` | 0 | 17 |
| s2 d3.v1 p2 | agy | `81af4f82142c5735ae9b58967beaff6487b99e5e67d8114d9abc925937e3e2b0` | 40 | 0 |
| s2 d3.v1 p3 | grok | `6e5a734eceea0c12e9bfc6de2d8c514d171612ac0c669e683b4d2e57999987a5` | 77 | 15 |
| s2 d4.v1 p1 | codex | `e3102aba4f32afed1cebb3296dd1618f3a1826be85d34a953799364a05eada1b` | 0 | 4 |
| s2 d4.v1 p2 | agy | `7daab10b9ab544757b8b6a9a74296002a0117d2a7620a92474224fb9795e5fcf` | 51 | 0 |
| s2 d4.v1 p3 | grok | `fda0a1933ca8f84c9222245639cbbf66194063d0326a2030d2f81d98fa4e9ad5` | 44 | 13 |
| s2 d5.v1 p1 | codex | `2db35cf945e55956bd0e3f3a897a074c8822bca6eb9b5eaf1917ec2276b40df9` | 0 | 10 |
| s2 d5.v1 p2 | agy | `f0213d7afe3706dc4c6efbce95323d2cc1516caf5d5337db1a0a6212fc15fc05` | 23 | 0 |
| s2 d5.v1 p3 | grok | `04065eec8180940eb8f8198562e4c89c33c85a55c18d3a499d866e8eb9abf38e` | 53 | 0 |
| s2 d6.v1 p1 | codex | `27153865ca1253fe29c6de79d86fbd3edc9426d91b0e12fbd83c407b6ab5ffa1` | 0 | 5 |
| s2 d6.v1 p2 | agy | `dba5686c8404d95517d801f03c3d3172f2dbdd2f7f3a6d227efd7ea7193114c3` | 39 | 0 |
| s2 d6.v1 p3 | grok | `0eaa68739a52701e45bf776d6c04d1f9d1925d208c0efe15f848d9b15b0e4e27` | 80 | 0 |
| s2 d7.v1 p1 | codex | `52ed4faa7feec3e94e3706d542fcbc73942ba2fa840bb5dcf0a44e8a2c849350` | 0 | 5 |
| s2 d7.v1 p2 | agy | `33d54e09fe72a9c1906d261a0506305b28075846f1b653130703adb221ea3bc9` | 13 | 0 |
| s2 d7.v1 p3 | grok | `9b483dd31127985d986e4c966e87d72dce6ca26f7ef49db3e9cc2bfaf1d1d837` | 56 | 4 |
| s2 d8.v1 p1 | codex | `0897cf238c3ce7fc6f76cf78edd967e5d931f833961e51591e860adedf2eac1e` | 0 | 4 |
| s2 d8.v1 p2 | agy | `b1bb9cc4e7cd6ffe82705f504cb3cc638755f9988477d261c8fc55683cf97325` | 47 | 0 |
| s2 d8.v1 p3 | grok | `839d8374a5772e8e1aaa26fdbb0d11c7b18340ef9b822c9bf534d37fa9d6d36a` | 54 | 1 |
| s2 d9.v1 p1 | codex | `061700de168d2aff9e30902cb03afab346c1805459df33263e38ec423ce23699` | 0 | 6 |
| s2 d9.v1 p2 | agy | `7811ba51e42923cf014c5b0491da89a733cce6c009f4f27692728997d76e1fe2` | 39 | 0 |
| s2 d9.v1 p3 | grok | `476501c5db74c2568bb878cc1bf0f5651cf2a98d1c887fcb0d2513642542afa6` | 79 | 4 |

## Containment (spec AC-6.5)

No verdict rule reads any item in this section.

- **Incident record.** `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`.
  The 2026-10-20 S2 run is incident evidence and is not scored.
- **Superseded smoke.** The first smoke commit `f7520e72` (`f7520e72c87e1c3c34e1c5f25fb3807343d84782`)
  is superseded by this run's re-smoke commit `8f8deaf1b6971f1ef5a54028fdd9c51e671f722b`.
- The first quarantine, before the run's first grok call (D20):

```text
QUARANTINE: VERIFIED moved=0 dest=/Users/kimhawk/.local/state/h-mad/grok-audit-surface/grok-quarantine-20261024T132508Z
```

- The canary (D18): its token, and the binary it ran (`canary/grok.txt`):

```text
GROK-CANARY: PASS
grok_binary=/Users/kimhawk/.grok/bin/grok
grok 1.0.62 (1474f9cbdd91)
```

- The re-smoke grok pass's scan (D19), read `REQUIRE: OK`:

```text
TOOLSCAN: CLEAN surface=grok calls=44 out_of_root=0 checkout=0 exempt=1 nonjson=7
```

- The second quarantine, after the re-smoke and before the fresh S2:

```text
MOVED: %2FUsers%2Fkimhawk%2F.local%2Fstate%2Fh-mad%2Fgrok-audit-surface%2Frun-ab2c85dc2e25-20261024T132452Z%2Froots%2Fgas-root-d1-s1-szujeqyy
QUARANTINE: VERIFIED moved=1 dest=/Users/kimhawk/.local/state/h-mad/grok-audit-surface/grok-quarantine-20261024T134737Z
```

- The positive control (D19, Task 15 step 10), the scan run over the 2026-10-20 incident run's
  `s2/d5/v1/p3.log`; its `checkout=` is above 0, so the scan sees the live checkout:

```text
TOOLSCAN: OUT_OF_ROOT surface=grok calls=58 out_of_root=24 checkout=21 exempt=14 nonjson=9
```

- Every `CONTAINMENT:` line of the score (D13). Each standing grok pass ran `profile=strict
  origin=default`.

```text
CONTAINMENT: d1.v1 p1 surface=codex scan=OUT_OF_ROOT calls=18 out_of_root=18 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d1.v1 p2 surface=agy scan=CLEAN calls=33 out_of_root=0 checkout=0 exempt=0 nonjson=3
CONTAINMENT: d1.v1 p3 surface=grok scan=CLEAN calls=42 out_of_root=0 checkout=0 exempt=0 nonjson=6 profile=strict origin=default
CONTAINMENT: d2.v1 p1 surface=codex scan=OUT_OF_ROOT calls=16 out_of_root=16 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d2.v1 p2 surface=agy scan=CLEAN calls=19 out_of_root=0 checkout=0 exempt=0 nonjson=1
CONTAINMENT: d2.v1 p3 surface=grok scan=CLEAN calls=69 out_of_root=0 checkout=0 exempt=1 nonjson=6 profile=strict origin=default
CONTAINMENT: d3.v1 p1 surface=codex scan=OUT_OF_ROOT calls=24 out_of_root=24 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d3.v1 p2 surface=agy scan=CLEAN calls=40 out_of_root=0 checkout=0 exempt=0 nonjson=3
CONTAINMENT: d3.v1 p3 surface=grok scan=CLEAN calls=77 out_of_root=0 checkout=0 exempt=1 nonjson=7 profile=strict origin=default
CONTAINMENT: d4.v1 p1 surface=codex scan=OUT_OF_ROOT calls=12 out_of_root=12 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d4.v1 p2 surface=agy scan=CLEAN calls=51 out_of_root=0 checkout=0 exempt=0 nonjson=4
CONTAINMENT: d4.v1 p3 surface=grok scan=OUT_OF_ROOT calls=44 out_of_root=4 checkout=0 exempt=2 nonjson=6 profile=strict origin=default
CONTAINMENT: d5.v1 p1 surface=codex scan=OUT_OF_ROOT calls=12 out_of_root=12 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d5.v1 p2 surface=agy scan=CLEAN calls=23 out_of_root=0 checkout=0 exempt=0 nonjson=2
CONTAINMENT: d5.v1 p3 surface=grok scan=CLEAN calls=53 out_of_root=0 checkout=0 exempt=13 nonjson=5 profile=strict origin=default
CONTAINMENT: d6.v1 p1 surface=codex scan=OUT_OF_ROOT calls=13 out_of_root=13 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d6.v1 p2 surface=agy scan=CLEAN calls=39 out_of_root=0 checkout=0 exempt=0 nonjson=3
CONTAINMENT: d6.v1 p3 surface=grok scan=CLEAN calls=80 out_of_root=0 checkout=0 exempt=4 nonjson=7 profile=strict origin=default
CONTAINMENT: d7.v1 p1 surface=codex scan=OUT_OF_ROOT calls=13 out_of_root=13 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d7.v1 p2 surface=agy scan=CLEAN calls=13 out_of_root=0 checkout=0 exempt=0 nonjson=2
CONTAINMENT: d7.v1 p3 surface=grok scan=CLEAN calls=56 out_of_root=0 checkout=0 exempt=3 nonjson=5 profile=strict origin=default
CONTAINMENT: d8.v1 p1 surface=codex scan=OUT_OF_ROOT calls=9 out_of_root=9 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d8.v1 p2 surface=agy scan=CLEAN calls=47 out_of_root=0 checkout=0 exempt=0 nonjson=3
CONTAINMENT: d8.v1 p3 surface=grok scan=CLEAN calls=54 out_of_root=0 checkout=0 exempt=9 nonjson=7 profile=strict origin=default
CONTAINMENT: d9.v1 p1 surface=codex scan=OUT_OF_ROOT calls=15 out_of_root=15 checkout=0 exempt=0 mcp_unmeasured=0
CONTAINMENT: d9.v1 p2 surface=agy scan=CLEAN calls=39 out_of_root=0 checkout=0 exempt=0 nonjson=3
CONTAINMENT: d9.v1 p3 surface=grok scan=OUT_OF_ROOT calls=79 out_of_root=1 checkout=0 exempt=4 nonjson=6 profile=strict origin=default
```

Codex and agy passes with `checkout=` above 0: none (0 of 18; every codex and agy `CONTAINMENT:` line reads `checkout=0`).

- **The codex last-message tracer pair** (D16, Task 15 step 2). Prompt `$RUN/work/tracer-prompt.txt`,
  one line. The control's log was `/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T/tmp.W9hkJE6ZYu/codex-control.log` (system temp); the treatment's was
  `$RUN/work/codex-treatment.log`. The four outputs, verbatim:
  - control stdout: `PONG`
  - control stderr: `hmad-dispatch: codex exec rc=0`
  - treatment stdout: `PONG`
  - treatment stderr: `hmad-dispatch: codex exec rc=0`

  Neither stderr carries an `EMPTY final message` line, so both pass. Cell: **pass/pass**, so the
  re-smoke and S2 ran the codex shape.
- **AC-2.6 residual (3), per surface.**
  - grok: bounded by the `strict` OS sandbox (FR-11). Reads are bounded to the working directory,
    system paths and system temp, and writes to the working directory and system temp; the canary
    tests one denied write and one denied read, and the scan is the read-bound evidence on every
    pass. Two grok passes read `scan=OUT_OF_ROOT` (d4 p3 `out_of_root=4`, d9 p3 `out_of_root=1`),
    both `checkout=0`; they are published above and did not halt the run.
  - codex: runs `workspace-write`, whose read bound was never probed against a sibling root or the
    live checkout. **UNVERIFIED** for reads and writes. Every codex pass reads `scan=OUT_OF_ROOT`
    with `out_of_root` equal to `calls`, and `checkout=0`.
  - agy: runs with no sandbox by default, with no verified read or write bound. **UNVERIFIED**.

## Readings

- **Task 0 tracer** (`$KEEP/agy-tracer/reading.txt`), the `exec agy` dispatch into a fresh `mktemp -d`
  directory. `T` is the `mktemp` spelling and `TP` its `pwd -P` form; agy's cli log named the `T`
  spelling, so D8's agy selection was used as written and AC-T0.3 did not fire:

```text
T=/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T/tmp.PaDtXiiCgX
TP=/private/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T/tmp.PaDtXiiCgX
new=cli-20261019_170743.log workspaceDirs=[/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T/tmp.PaDtXiiCgX]
CLASS=mktemp
```

- The S1 root's `ROOT: READY` line (re-smoke root):

```text
ROOT: READY doc=d1 purpose=s1 path=/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z/roots/gas-root-d1-s1-szujeqyy calibration=ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7 list_commit=2d8d7b2d2dc40954eb25d20d478251256b685d26 list_blob=b78b7f3b2a5893fdd4cd83d591efed83f2069203 absent=0
```

## Runbook as run

Task 15's steps, in D8's order, from the `main` clone `/Users/kimhawk/orca/skills` with
`KEEP=/Users/kimhawk/.local/state/h-mad/grok-audit-surface`, `CAL_SHA=ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7`, `CAL12=ab2c85dc2e25`, `LIST_SHA=2d8d7b2d2dc40954eb25d20d478251256b685d26`,
`PROBE=docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`,
`RUN=$KEEP/run-ab2c85dc2e25-20261024T132452Z` and `READING=$RUN/data/runs/run-ab2c85dc2e25-20261024T132452Z`. Every step was entered on the
previous step's token line, and every `GROK-CANARY:`, `QUARANTINE:`, `TOOLSCAN:` and `ASSEMBLER:`
token was read by `python3 h-mad/scripts/h_mad_grok_containment.py require`. Each step's completion
is recorded as a `LAST_STEP=` line in `$KEEP/run-current.env`, and its token lines are the files
this doc quotes.

1. Setup (D8 "Setup"): `RUN`, `READING`, `$RUN/{roots,work,stem,canary,assembler}`,
   `$READING/resmoke`, `$READING/s2`; `$RUN/run.txt` (`RUN: checkout=/Users/kimhawk/orca/skills
   home=/Users/kimhawk`) copied into both reading directories.
2. The codex tracer pair (above): cell pass/pass, codex shape.
3. First quarantine: `QUARANTINE: VERIFIED moved=0 …`, `REQUIRE: OK`.
4. Canary: `h-mad/bin/hmad-dispatch grok-canary --run-dir "$RUN"`: `GROK-CANARY: PASS`,
   `REQUIRE: OK`; `$RUN/canary/` copied into `$READING/resmoke/canary/`.
5. Re-smoke (AC-1.9), `--doc d1 --purpose s1`: `assembler-read > "$RUN/assembler/start.txt"`, then
   versions, then the grok cycle (`--cycle 1 --passes 1 --surfaces grok`, `--root-record`), its
   `record-cycle`, `wall_seconds.txt`, `resolved_model.txt`, and its scan into
   `$READING/resmoke/grok/p1.scan.txt` (`REQUIRE: OK`); the agy cycle (`--cycle 2`, `--reset
   "$ROOT_1"`) with D8's agy provenance block placed as carry 6 places it: the `cli-*.log` listing
   right after the cycle block's `STEM=…; mkdir -p "$STEM"` line and before its `build-root` line,
   and the selection after its `record-cycle` and before the codex block; then the codex cycle
   (`--cycle 3`, `--reset`). Every cycle carried `--halt-file "$RUN/HALT"`, `--pass-root "$ROOT_1"`
   and `--timeout 1800`.
6. Smoke: `python3 "$PROBE" smoke --data "$READING/resmoke"`: `SMOKE: PASS`. The `SMOKE: UNREADABLE`
   remedy is to restore the named input and derive again. Carry 10: an UNREADABLE caused by a
   non-grok (wrong-file) Effort item is not cleared by that remedy; only a new smoke, in a new run,
   clears it. This run did not reach that case.
7. Re-smoke commit: calibration-ref precondition (no `STOP`), forced fetch of the calibration ref,
   `ls-remote` confirm, `commit-data --parent "$TIP" --src "$RUN/data"`: `COMMIT: OK sha=8f8deaf1b6971f1ef5a54028fdd9c51e671f722b ref=refs/heads/calibration/grok-audit-surface`; pushed
   without force and confirmed.
8. Second quarantine: `QUARANTINE: VERIFIED moved=1 …`, `REQUIRE: OK`.
9. Fresh S2: nine documents, `v1` each, `--passes 3 --surfaces codex,agy,grok`, one
   `build-root --purpose s2v1 --dest-parent "$RUN/roots"` per pass passed as `--pass-root` in pass
   order, `--project-root "$ROOT_1" --halt-file "$RUN/HALT"`; `record-cycle` with one
   `--pass-root-record` per pass; the p3 (grok) scan of each cycle read `REQUIRE: OK`. No halt.
9a. Assembler pin: `assembler-read > "$RUN/assembler/end.txt"`, `assembler-check … --stems
   "$RUN/stem" --stages resmoke,s2 > "$RUN/assembler/check.txt"`, `require --verb assembler`:
   `REQUIRE: OK`.
10. Positive control: `h_mad_tool_calls.py scan --surface grok --log
    "$KEEP/run-ab2c85dc2e25/data/s2/d5/v1/p3.log"` with that cycle's root, the live checkout and
    `--home "$HOME"`: `checkout=21`.
11. Extract, labels, score sha: `SEED=773509911`; `/Users/kimhawk/orca/skills/docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py extract --repo . --base-sha 8f8deaf1b6971f1ef5a54028fdd9c51e671f722b --work-dir /Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z/work --s2 /Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z/data/runs/run-ab2c85dc2e25-20261024T132452Z/s2 --shuffle-seed 773509911 --out /Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z/data/runs/run-ab2c85dc2e25-20261024T132452Z`; labels into
    `$READING/labels.jsonl` (see Residuals); calibration-ref precondition, fetch, confirm,
    `commit-data`: score sha `05cc39355cb3a68ddebb177c4bd1e215054cc4ad`; pushed and confirmed.
16. Rescore and main leak from `main` at `e50e7331abce9478268ed247219e530ceaf27d37` (Task 16): the re-run command below with
    `--work-dir /Users/kimhawk/.local/state/h-mad/grok-audit-surface/work-task16`, and `main-leak` with the same shas.

## Re-run command (AC-6.4)

```bash
CAL_SHA=ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7
SMOKE_SHA=8f8deaf1b6971f1ef5a54028fdd9c51e671f722b
SCORE_SHA=05cc39355cb3a68ddebb177c4bd1e215054cc4ad
RUN=/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z
python3 docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py rescore --repo . --calibration-sha "$CAL_SHA" --smoke-sha "$SMOKE_SHA" --score-sha "$SCORE_SHA" --run-id "${RUN##*/}" --work-dir "$WORK"
```

`WORK` is any existing directory outside system temp and outside every git work tree (D5); the probe
refuses any other. The run id is `run-ab2c85dc2e25-20261024T132452Z`. Run it from a checkout that has fetched
`refs/heads/calibration/grok-audit-surface`.

## Residuals

- The seeds are build-class shapes from the four classes of spec AC-2.1, and whether recall on real defects would match is not measured.
- The measurement was taken with the calibration-only path-scope clause (AC-3.9): the calibration prompt is the production prompt plus exactly that clause, inserted once at the head of the audit body; production grok legs do not receive it, and whether a production grok leg without it behaves the same is not measured.
- **The labeller package (procedure deviation; design rows 122-123, backlog triage row 2 in
  `docs/03-analysis/2026-10-25-backlog-triage.md`).** The labels were written by 9 fresh AI
  subagents, one per document, not by a human. Each was given only its document's slice of the
  findings (must and should), that document's 3 ledger seeds, a copy of the document's p1 root
  (rsync exclusions in `$RUN/work/labeller-rsync-exclusions.txt`), and the redacted p1 prompt. The
  labeller prompt is at `$RUN/work/labeller-prompt.txt` and the provenance at
  `$RUN/work/labeller-provenance.txt`. `$RUN` and `run-current.env` were `chmod 000` for the whole
  dispatch. Residual: the same uid could read `~/.claude` transcripts and older runs under the state
  directory, so containment there was by instruction only.
- **All 130 labels are HIT or REAL.** 0 FABRICATED and 0 UNDECIDABLE on every surface: must-fixes
  30 HIT and 56 REAL, should-fixes 12 HIT and 32 REAL. A prior measurement counted 6 fabrications in
  37 must-fixes (`docs/03-analysis/hmad-audit-evidence-gate.measurement.md`). The PASS holds on D3's
  equal-fabrication clause (0/38 = 0/23) with recall 12 > 10: one grok must-fix relabelled
  FABRICATED, or two grok HITs relabelled REAL, would turn it to MISS.
- **Hint cross-check.** The labels agreed with 32 of the 33 `candidate-hit` hints; the one
  disagreement is `F5a289f55` (grok, d6), hinted `candidate-hit:d6-s3` and labelled REAL. The 30
  `candidate-fabrication` hint lines fall on 29 distinct findings, all codex or agy and none grok:
  `F5de7554d` (codex, d8) carries both `candidate-fabrication` and `candidate-hit:d8-s1` and is
  labelled `HIT:d8-s1`. Every one of the 29 was labelled HIT or REAL, each with a line-cited reason.
- The operator chose to publish PASS as measured (2026-10-26).
