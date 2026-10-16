DESIGN-AUTHOR: DONE version=v1.4 path=/Users/kimhawk/orca/skills/docs/02-design/features/agy-coder-fallback.design.md lines=1486 sha256=43fbb608632330837b2a2f7f58bd88fb00fc80ef8e1e1dc145d7a660968aa6d2

## Ownership check
Before the first write: sha256 22a8dee8…, newest VH entry v1.3, mtime 1792146138, HEAD 84ec2133. All matched the brief. Nothing moved during the work.
Note: `git diff --stat` also shows uncommitted edits to `docs/01-plan/features/agy-coder-fallback.spec.md`. They are not mine; presumably the spec-author is working in parallel. I did not touch that file.

## Changes (Q1–Q3 only)
- **Q1 (OD-2).** FR-4 class (b) gains a **T2a** bullet between T2 and T3. If `Path(resolved.target).is_dir()` holds: deny `kind=judge-error` under S, allow under inactive. Because it runs before T3, an out-of-root directory is caught too. Symlinks are followed. Residual: a trailing-`/` path that names no existing directory.
  The deny table gains a row, and its count line now reads "17 rows (v1.4 adds T2a)". New deliberate-difference bullet: the Codex gate's per-target sequence has no such step. New FR-4 mutation bullet, naming the impl-plan's `od2-directory-target-check-dropped`. New entries in Residuals and Operator decisions.
- **Q2 (self-check).** The "nonzero exit" text is replaced by a class rule. A verdict FAIL (`classification`, `shell-policy`) exits 0. A could-not-run FAIL (`policy-import`) exits 2. FR-6's Codex `FAIL policy-import` exit 2 is consistent with this and was kept. FR-5's PASS-and-exit-0 requirement is unaffected. The Codex gate's `FAIL shell-policy` is corrected in impl-plan Task 4. Residual: a FAIL added later is classed by the rule.
- **Q3 (halts).** New FR-2 paragraph, "The caller's halts":
  - `record=failed` is read first and gives `step5:implementer_switch_unrecorded` (spec FR-2 already names this one);
  - `invalid field=` gives `step5:implementer_invalid`;
  - `no-record` or `unreadable` gives `step5:implementer_unresolved`.
  All three names are adopted from the impl-plan, Task 16.
- Owed section: spec items for P1–P3; one impl-plan item, below.
- VH: `VERSION-HISTORY: OK … version=v1.4 placement=append`.
- Precheck: `PRECHECK … PASS issues=0`, with 24 advisories. I compared their line numbers against `git diff -U0` hunk ranges, and none falls on a line I added. All of them are in pre-v1.4 text: future paths, and counts in older VH entries.

## Premises verified
- Directory targets: a scratch call to `canonicalise` (scratchpad root, deleted with `rmdir`) at 84ec2133. `.`, `src/`, `src` and the root each gave `unresolvable=False names=() is_dir=True`. `nodir/` gave `names=('nodir',) is_dir=False`. This confirms the T2a premise and its residual.
- The Codex gate's self-check tokens (`grep -n 'TDD-GATE: \(FAIL\|PASS\)' h-mad/hooks/h-mad-codex-tdd-gate.py`): `FAIL parser` and `FAIL shell-policy` both go to stderr and both `return 2`. `PASS` goes to stdout.
- The Codex gate has no write-target directory step. It makes 3 `is_dir` calls (`grep -n 'is_dir'`), in `_project_root` (2) and `_payload_cwd_base` (1), and none of them tests a write target.
- Deny table row count: an awk count of the table body gives 17.
- Spec FR-2 names only `step5:implementer_switch_unrecorded`. I grepped the spec for the other two names and found 0 hits.
- Sweep: I collapsed newlines with `tr '\n' ' '` and grepped for `nonzero|non-zero|16 rows|sixteen|FAIL <what>|self-check-failed|exits? 2`. The only stale hit is "16 rows" in the v1.2 VH entry. That is history and was left alone. I also grepped for `T1.T7|T2.T7`, and the only hit is VH v1.1, also history.

## Contradictions / owed
- **Impl-plan (class gap).** The Codex gate has two verdict FAILs that exit 2: `FAIL parser` and `FAIL shell-policy`. Decision I4 names only shell-policy. Task 4 should either fix both or say why `FAIL parser` stays. Recorded in the design's Owed section.
- **Spec.** P1 (OD-2), P2 (the halt names) and P3 (self-check exit 0), as listed on the decision sheet.
- Open, not mine: whether `failure-recovery.md` gets rows for the three step5 halts (impl-plan v1.1 report).
