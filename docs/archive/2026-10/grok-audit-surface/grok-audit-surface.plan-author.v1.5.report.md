PLAN-AUTHOR: DONE version=v1.5 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.plan.md lines=291 sha256=e8e3c421bbc8d1e3190af8f8b37b52b1994e3577656cc8dc18effa61a4a00c35

# Plan author report: grok-audit-surface plan v1.5 (propagation only, not re-audited)

Base: HEAD abe47752, plan v1.4. The file is not committed. The spec and the design files also show as modified in the work tree; those changes belong to the concurrent authors, and I did not touch either file.

## What changed

### 1. Operator decision D4 (version-agnostic)
- Goals, first bullet: the D4 canonical sentence is quoted verbatim, with its source path. The bullet also defines "the recorded grok version" as the recorded `grok --version` line.
- `1.0.62` sites (6 before the edit, from `grep -n '1\.0\.62'`) are all rewritten:
  - Scope "In": now "the grok on PATH at S1, at the recorded grok version".
  - Scope smoke-failure clause: now "the audit-path smoke of the recorded grok version failed".
  - Goals bullet 1.
  - FR-1.
  - Convention Prerequisites: now "grok and agy on PATH", and no grok version is required.
  - R9 row: no longer stamped (see "Tree contradicts the D4 premise" below). Its command is now the D4 re-derive command.
- S1 stage row: S1 now also records the grok binary's path and its `grok --version` line.
- Sweep after the edit: `grep -n '1\.0\.62' <plan>` matches 0 lines, Version History included (none of the older entries contained it).

### 2. Design v1.1 facts
Each fact was checked by grep against the committed design (`eb085307`) before I wrote it:
- **Nine modes, including `main-leak`** (design header and the D2 table). The S0 row lists all nine.
- **Per-cycle `root.txt` replaces `roots.jsonl`** (D5 "Which list version", D8 `record-cycle`). `git show 3f367796:<design> | grep -c 'roots\.jsonl'` gives 6 matching lines, so v1.0 did use it.
  - Updated: the S1 smoke-commit bullet, the S2 score-sha bullet, and "Which list version".
  - The plan never wrote `roots.jsonl` itself; it only mentions the name when saying what `root.txt` replaces.
- **`extract` takes `--s2` and `--base-sha` (the smoke commit)** (D2 table, D12 Inputs). Added to the S2 score-sha bullet.
- **`rescore` takes `--smoke-sha`** (D2, D15 re-run command). The S3 re-score bullet now quotes `rescore --repo . --calibration-sha <sha40> --smoke-sha <sha40> --score-sha <sha40>`.
- **`main-leak` runs before the measurement-doc commit on every outcome** (D9 "When it runs"). Added in four places:
  - the S3 stage row;
  - a new S3 bullet: no `--score-sha` on a smoke failure, a refusal blocks the commit;
  - the runbook deliverable, which now covers S3;
  - the success criterion "No calibration data on `main`". It used to name only the AC-6.4 run, which does not exist on a smoke failure.
- **The labeller labels should-fix findings too** (D12 "Should-fix findings"). Updated:
  - Goals, FR-4 bullet: labels go to should-fix findings as well, are published separately, never enter the bar (AC-4.5), and add S2 labelling effort.
  - The S2 row.

### 3. S0b root count
- The S0b row no longer says "and the smoke document's root". It now says what each stage builds:
  - S0b builds one root per seeded document to fix the calibration sha.
  - The live cycles run in roots built fresh from that sha: one at S1 for its three cycles, and one per S2 cycle, re-dispatch included, never reusing the S1 root.
  - That gives 1 + 9 + one per re-dispatch = 10 to 19 dispatch roots. The upper bound holds because D8 allows no third cycle. The design names the count (D5 "Roots and cycles").
- The S1 and S2 rows were changed to match: S1 uses one fresh root for `d1`, and S2 uses a fresh root per cycle and per re-dispatch.

### 4. Bookkeeping
- Next Steps item 3 now reads "User approves v1.5".
- Version History: `h_mad_version_history.py` printed `VERSION-HISTORY: OK ... version=v1.5 line=291 placement=append`.

## Measurements re-run
- **Ownership check before writes:** `stat -f %m` = 1792366055 and the newest line was `- v1.4` before the first write. Before the later scripted write, the mtime had moved only through my own edits and the newest line was still `- v1.4`.
- **Grok binaries:** `which -a grok | sort -u | while read g; do echo "$g: $($g --version 2>&1 | head -1)"; done` printed:
  - `/opt/homebrew/bin/grok: 1.0.1`
  - `~/.grok/bin/grok: grok 1.0.62 (1474f9cbdd91) [stable]`
  - `~/.local/bin/grok: grok 1.0.62 (1474f9cbdd91) [stable]`
- **Changelog:** `head -1 ~/.grok/CHANGELOG.md` printed `# 1.0.52 — 2026-10-11`.
- **Readings still valid:** `git diff --quiet 94a4fd2c..HEAD -- h-mad` exits 0, so the readings stamped `94a4fd2c` over `h-mad/` (R1, R13, the interpreter) still hold. 94a4fd2c..HEAD touches only docs.
- **Precheck:** `python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py <plan> --phase plan --root /Users/kimhawk/orca/skills` gave `PRECHECK: PASS issues=0`. I kept five advisories on purpose:
  - PATH (2): `grok-audit-surface.measurement.md` is the new S3 deliverable and does not exist yet.
  - COUNT on the `cycle_token` bullet: "seven triggers" is "these two, plus" five more, which is 7; the checker counted the list as 5. The line is unchanged from v1.4.
  - COUNT on "What counts": unchanged v1.4 text.
  - STALESHA `94a4fd2c`: covered by the `git diff --quiet` result above.

## Tree contradicts the D4 premise (not resolved; filed)
- The D4 decision doc says every `grok` on PATH reports `1.0.52 (0920c8169e27)` and that "no 1.0.62 was ever observed".
- Measured now (2026-10-19, abe47752): both `~/.grok/bin/grok` and `~/.local/bin/grok` report `grok 1.0.62 (1474f9cbdd91) [stable]`. The changelog's newest entry is still 1.0.52.
- So the decision's premise does not match the tree at this moment. Grok may have updated itself after the decision was measured, or the changelog lags the binary.
- The decision itself (version-agnostic) does not depend on which version is installed, so I applied it as instructed.
- On R9 I chose not to stamp a reading, so that no version string appears in the plan. The reading above lives in this report instead. Revert option: put R9 back as a dated reading, explicitly labelled "a reading, not a target".
- The operator, or whoever owns the decision doc, should re-measure and correct the premise paragraph.

## Owed elsewhere
- **Decision doc** (`docs/03-analysis/grok-audit-surface.decision-2026-10-19-d4.md`): its premise measurement is contradicted by the tree; see above.
- **Spec and design:** none from this revision. Both are being revised by their own authors right now, and I make no claim about what they will say.
