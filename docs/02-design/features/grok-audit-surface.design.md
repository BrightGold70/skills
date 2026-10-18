# Design: grok-audit-surface

## Executive Summary
One stdlib-only probe, `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`, with eight modes (`check-ledger`, `build-root`, `record-cycle`, `commit-data`, `smoke`, `extract`, `score`, `rescore`), a declared exclusion list beside it, five new test modules under `h-mad/tests/`, and one new mutation spec. Together they measure grok against agy on 27 seeds, read every verdict the wrapper already computes from the wrapper's own token lines, and keep all calibration data on the never-merged branch `calibration/grok-audit-surface`. The only production code the feature edits is SKILL.md text (and `grok-runtime.md`); `exit_check`, `round_check`, `combine`, `scan_grok` and the wrapper are pinned by tests and not edited.

## Overview
This design takes spec v1.5 (`2f7bf7ae`) and plan v1.3 (`ab3c9f32`) as given and settles every item the plan leaves to the design (listed in "Plan obligations answered"). The plan and the delta review cite shas from before a rebase; this design cites only the post-rebase ids, which `docs/03-analysis/grok-audit-surface.sha-remap.md` maps (`946ffc5a→a0b41697`, `5b2df07b→bfb6960a`, `611c299d→2f7bf7ae`, `b085ad7a→ab3c9f32`). There are three key decisions. The probe never re-derives a verdict the wrapper or the gate computes: it reads the token, or imports the function. Every live root is used for exactly one cycle. Calibration data reaches the branch only through git plumbing, so it is never checked out in any work tree.

## Architecture Overview

```
 main (CI-tested, S0)                         calibration/grok-audit-surface (operator, never merged)
 ───────────────────────                      ──────────────────────────────────────────────────────
 grok_audit_probe.py ── reads ──> HEAD:exclusions.txt         calibration sha: ledger.jsonl + seeded/*.md
   │ imports h_mad_audit_gate (classify, section walk)        smoke commit:     + s1/<surface>/...
   │ imports h_mad_audit_origins (ORIGINS)                    score sha:        + s2/d<k>/v<N>/..., findings,
   │ imports h_mad_review_evidence (_GROK_TYPES)                                  key, labels, roots.jsonl
   │ reads hmad-dispatch.sh text (_GROK_TYPES_RE)
   │ runs h_mad_audit_gate.py CLI (GATE: token)
   │
   ├─ build-root ── git archive <calibration sha> ──> $TMPDIR/gas-root-d<k>-<purpose>-XXXX/  (non-git)
   │                 remove exclusions, place target + paired docs, scan, reach check
   │
   │   operator: env -u GIT_* HMAD_AUDIT_STEM_DIR=$KEEP/run-<cal12>/stem/<cycle>  hmad-dispatch audit-cycle ... | tee auditcycle.txt
   │
   ├─ record-cycle ── copies stem + root by-products ──> $KEEP/run-<cal12>/data/{s1,s2}/...
   ├─ commit-data ─── hash-object / read-tree / commit-tree / update-ref (temp index, no checkout) ──> branch
   ├─ smoke ───────── SMOKE: PASS|FAIL|UNREADABLE   (exit 0, 0, 2)
   ├─ extract ─────── findings.jsonl + key.jsonl (opaque ids, shuffled) + advisory hints on stdout
   ├─ score ───────── SEEDSCORE: ... from one exported score-sha tree
   └─ rescore ─────── ls-remote/fetch ref → sha checks → two-sha drift → git archive score sha → main leak
                      over HEAD → rebuild roots + scan + reach → score → remove temp dirs
```

The scorer is a pure function of two trees, as the plan's Architecture section requires: the `main` commit (probe and exclusion list) and the exported score-sha tree, which holds the ledger, the seeded copies, the recorded cycles, the findings, the key and the labels, plus the archive sources that came from `main` when the branch was made.

## Detailed Design

### D1. Probe file, imports and invocation
- **Path**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`, run as `python3 docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py <mode> …` from the repository root. It is not named `test_*.py`.
- **Imports**: the stdlib only, plus three `h-mad/scripts/` modules reached as `Path(__file__).resolve().parents[4] / "h-mad" / "scripts"` put first on `sys.path`. (`parents[0]` is the probe directory, `[1]` `probes`, `[2]` `03-analysis`, `[3]` `docs`, `[4]` the repository root.) The three modules are `h_mad_audit_gate` (`classify`, `_bullet_groups`, `_payload`, `_is_none_sentinel`), `h_mad_audit_origins` (`ORIGINS`) and `h_mad_review_evidence` (`_GROK_TYPES`). `_GROK_TYPES_RE` is read from the text of `h-mad/scripts/hmad-dispatch.sh` with the regex `^_GROK_TYPES_RE='([^']*)'$` (multiline), split on `|`, and never copied. The private names are imported the same way `h_mad_audit_cycle._must_findings_from_gate_parser` already imports `_BULLET_MARKERS` and `_payload` from the gate.
- **Subprocesses**: only `git` and `sys.executable h-mad/scripts/h_mad_audit_gate.py <report>`, the latter to obtain a real `GATE:` token. The probe never invokes `codex`, `agy`, `grok` or `hmad-dispatch` (base §"No new external dependency").
- **Source features** are the module constant `SOURCES`, in spec FR-2 order: `audit-report-docs-copy` (`docs/archive/2026-09/`), `tdd-gate-fail-opens` (`docs/archive/2026-09/`), `agy-coder-fallback` (`docs/archive/2026-10/`). Documents are numbered `d1`…`d9` in feature order, then plan, design, impl-plan (AC-2.2). `--sources <name>=<archive dir>,…` overrides the constant, and only the synthetic fixtures pass it. **DECISION (design-author):** a CLI override and not a config file, because the plan restricts the probe directory on `main` to "the probe and the declared exclusion list, and nothing else".
- **Token discipline**: every mode ends on exactly one token line on stdout. Operational modes exit 0 on success and 2 on a refusal. `smoke` exits 0 on PASS and FAIL and 2 on UNREADABLE. `score` and `rescore` exit 0 on PASS, MISS and INCONCLUSIVE and 2 on UNREADABLE. An `[H-MAD] grok-audit-surface <mode> <verdict>` marker goes to **stderr**, so the token stays the last stdout line (AC-5.1 "ends on one token line"; base §"Marker discipline").
- **One refusal vocabulary.** Every refusal in every mode except `smoke` prints `SEEDSCORE: UNREADABLE reason=<r>`, with `<r>` from the closed AC-5.4 list, so S0b, S1 and S2 refuse in the same grammar that AC-6.4 re-checks. **DECISION (design-author):** one grammar instead of a token per mode, because the same check (scan, reach, ref) runs at S0b and again inside `rescore`, and two spellings of one refusal would be two contracts.

### D2. Modes and command lines

| Mode | Command line | Success token | Stage |
|---|---|---|---|
| `check-ledger` | `check-ledger --repo . --calibration-sha <sha40> [--sources …]` | `LEDGER: OK seeds=<n> docs=<n> C1=<n> C2=<n> C3=<n> C4=<n>` | S0b, rescore |
| `build-root` | `build-root --repo . --calibration-sha <sha40> --doc d<k> --purpose <s1\|s2v1\|s2v2\|rescore> [--list-commit <sha>] [--dest-parent <dir>]` | `ROOT: READY doc=d<k> purpose=<p> path=<abs> calibration=<sha40> list_commit=<sha40> list_blob=<oid> absent=<n>` | S0b, S1, S2, rescore |
| `record-cycle` | `record-cycle --stem <dir> --root <dir> --stdout <file> --command <file> --dest <dir>` | `RECORD: OK dest=<abs> files=<n>` | S1, S2 |
| `commit-data` | `commit-data --repo . --parent <sha40> --src <dir> --message <text>` | `COMMIT: OK sha=<sha40> ref=refs/heads/calibration/grok-audit-surface` | S0b, S1, S2 |
| `smoke` | `smoke --data <dir>/s1 [--vocab-py <path>] [--vocab-sh <path>]` | `SMOKE: PASS` / `SMOKE: FAIL reason=…` | S1 |
| `extract` | `extract --tree <dir> --shuffle-seed <int> --out <dir>` | `FINDINGS: WRITTEN findings=<n> reports=<n>` | S2 |
| `score` | `score --tree <dir> [--calibration-sha <sha40> --score-sha <sha40>]` | `SEEDSCORE: PASS\|MISS\|INCONCLUSIVE …` | tests, rescore |
| `rescore` | `rescore --repo . --calibration-sha <sha40> --score-sha <sha40> [--remote origin]` | the `score` token | S3 (AC-6.4) |

`--tree <dir>` is always a directory holding an exported commit tree (or a synthetic fixture shaped like one), never a work tree. Each mode's refusals are listed in "Error Handling Strategy".

### D3. Calibration directory layout (branch only)
Every path is under `docs/03-analysis/probes/grok-audit-surface/calibration/` in the branch's tree:

```
ledger.jsonl                         one JSON object per seed (AC-2.4)
seeded/<feature>.<phase>.md          the 9 seeded copies (AC-2.5)
roots.jsonl                          every ROOT: READY line of S1 and S2, as {"line": "..."} records
s1/<surface>/                        surface ∈ {grok, agy, codex}; codex absent when not run
s2/d<k>/v<N>/                        k ∈ 1..9; N ∈ {1, 2}
findings.jsonl                       {"id","doc","cycle","text","quotes":[...]}; shuffled; no surface field
key.jsonl                            {"id","doc","cycle","pass","surface","report"}; plus one {"shuffle_seed": n} record
labels.jsonl                         {"id","label","why"}; "why" required for UNDECIDABLE
```

A cycle directory (`s1/<surface>/` or `s2/d<k>/v<N>/`) holds the following.

| File | From | Read by |
|---|---|---|
| `auditcycle.txt` | the wrapper's full stdout, captured with `tee` | smoke, score (the `AUDITCYCLE:` line and the `Effort:` block) |
| `command.txt` | the exact dispatch command, verbatim | score (`--surfaces`), measurement doc |
| `wall_seconds.txt` | `date +%s` before and after, as a difference (S1 grok only) | smoke (AC-1.4 timeout) |
| `p<i>.prompt.txt`, `p<i>.asm.txt`, `p<i>.out.txt`, `p<i>.log`, `p<i>.report.md` | the stem dir (`<stem>_p<i>.txt`, `.asm.txt`, `.out.txt`, `.log`, `.report.md`), each only if present | the labeller, smoke (log), opposed fixtures |
| `collected/<feature>.<phase>.audit.v<N>.p<i>.md` and its `.effort.json` | the root's `docs/0X-…/features/` | smoke and score (GATE, findings), AC-3.3 `log_sha256` |
| `pass-logs/<collected name>.log` | the root's `.h-mad/pass-logs/` | the measurement doc (AC-3.3) |

`record-cycle` copies these and nothing else. It never writes the root's `.gated.json` stamps, which are root-local artefacts.

What counts as calibration data under AC-2.7's catch-all: every file above except `auditcycle.txt`, `command.txt`, `wall_seconds.txt` and `roots.jsonl`, which carry no seed text. The main leak check's trigger (i) hashes exactly that set (D9).

### D4. Ledger checks (`check-ledger`; AC-2.2–2.5)
- Records are read from `ledger.jsonl`. A line that does not parse, or that lacks one of the nine AC-2.4 fields (`id source phase class origin section original seeded expected`), refuses `ledger_counts`.
- `ledger_counts`: the counts are derived, never carried. The ledger must hold exactly 3 seeds per document for all 9 documents, document `d<k>` must omit class `((k−1) mod 4)+1`, and the totals must come out as derived from that rule (C1=6, C2=7, C3=7, C4=7, sum 27). The probe computes the expected totals from the rule and compares them; the numbers are not literals in the code.
- `ledger_origin`: `origin ∉ ORIGINS` (the imported 8-tuple).
- `seed_rebuild`: for each document, start from the archive source bytes in the exported calibration tree. For each seed, the exact (unnormalised) `original` must occur **exactly once** in the source, and it is replaced by `seeded`. The result must equal `seeded/<feature>.<phase>.md` byte for byte. The AC-2.3 placement rules are also checked here: seeds sit in distinct `##`/`###` sections, none sits under `## Version History`, `section` names the heading the span sits under, and `seeded` occurs exactly once in the seeded copy. **DECISION (design-author):** placement violations refuse as `seed_rebuild`, because AC-5.4's list is closed and has no placement reason, and a placement violation makes the copy unrebuildable as specified. *Owed to the spec:* name AC-2.3 violations in AC-5.4.

### D5. Export root (`build-root`; AC-2.6)
**Parent directory.** By default this is `tempfile.mkdtemp(prefix=f"gas-root-d{k}-{purpose}-")` under `tempfile.gettempdir()`. On this Mac that is `$TMPDIR` (`/var/folders/…/T/`), and `git -C <a mktemp -d dir> rev-parse --git-dir` exits 128 there (Readings). The reach check, not this choice, is the evidence. `--dest-parent` exists for fixtures, including the "root nested inside a work tree" fixture.

**One root per cycle.** **DECISION (design-author):** S1 builds one fresh root for its three cycles (AC-1.6 requires the same root), and S2 builds a fresh root for every cycle, re-dispatch included (`s2v1`, `s2v2`). That makes ten or more roots in all, against the plan's S0b cell, which says "9 calibration roots, and the smoke document's root". A used root holds the earlier cycle's collected reports, `.effort.json` sidecars and `.h-mad/pass-logs/` (the wrapper writes them under `--project-root`), and a re-dispatched cycle that could read the first cycle's reports from other surfaces is a cross-surface leak. The S1 root is never reused for S2. **The smoke document is `d1`** (audit-report-docs-copy plan, the smallest), and S1 runs its cycles as `--cycle 1` (grok), `--cycle 2` (agy) and `--cycle 3` (codex), so the collected paths never collide.

**Order of operations**, each step re-read before the next (base §"Mutation verification"):
1. Read the exclusion list from `<list-commit>:docs/03-analysis/probes/grok-audit-surface/exclusions.txt` with `git cat-file blob`. `--list-commit` defaults to `HEAD` of `--repo`. The probe never reads the work tree copy. Record `list_commit` (full sha) and `list_blob` (`git rev-parse <list-commit>:<path>`).
2. Export `git archive --format=tar <calibration sha>`. Its stdout is read by `tarfile` with `extractall(filter="data")` into the fresh root. A `tarfile.FilterError` on member `m` refuses `leak:<m>`: a member the data filter rejects is a link leaving the root.
3. Remove every list entry (format below), then **assert each removed path is gone** by re-walking the root.
4. Place the documents, writing each as bytes from `git cat-file blob <calibration sha>:<path>`. The seeded target `seeded/<feature>.<phase>.md` goes to its live path (`docs/01-plan/features/<feature>.<phase>.md`, or `docs/02-design/features/<feature>.design.md`). Then only the paired documents the assembler reads for that phase are placed, at their live paths, from `docs/archive/<yyyy-mm>/<feature>/`: a plan root gets the spec; a design root gets the spec and the plan; an impl-plan root gets the design.
5. Run the content scan (D6), then the git reach check (D7). Only then print `ROOT: READY`.

**Exclusion list format** (`docs/03-analysis/probes/grok-audit-surface/exclusions.txt`, on `main`). It is UTF-8 with one entry per line, and `#` starts a comment. There are two kinds. `dir <tree path>` removes that subtree. `name-contains <s>` removes every file or directory, at any depth, whose final path component contains `<s>`. Any other line refuses with `leak:exclusions.txt`. **DECISION (design-author):** the file is fail-closed on its own grammar, and an unknown directive is reported under the scan's reason because AC-5.4 is closed. An entry naming a path absent from the export is counted in `absent=<n>` and is not a refusal. The committed list holds exactly these six entries:

```
dir docs/archive/2026-09/audit-report-docs-copy
dir docs/archive/2026-09/tdd-gate-fail-opens
dir docs/archive/2026-10/agy-coder-fallback
dir docs/03-analysis/probes/grok-audit-surface
dir docs/03-analysis/agy-coder-fallback.authoring
name-contains grok-audit-surface
```

**DECISION (design-author):** `name-contains` is a superset of the spec's "final component begins with `grok-audit-surface`" (which AC-2.6 allows as "at least"). At `3660aeeb` it also removes `docs/handoffs/2026-10-18-main__grok-audit-surface-phase3.md` and `docs/handoffs/2026-10-18-main__grok-audit-surface-phase3-exit.md`, which discuss this feature's answer key and which "begins with" would leave in place (Readings). Residual: a file that discusses the feature without its name in the file name (`docs/learnings.md` and `docs/skill-candidates.md` mention it at `3660aeeb`) is a name mention, AC-2.6 residual (4). Verbatim seed text in any such file is caught by the scan, not by the list.

**Which list version** (plan "Which list version"). Each `ROOT: READY` line carries `list_commit` and `list_blob`, and `record-cycle` appends the S1 and S2 root lines to `roots.jsonl` on the branch. `rescore` prints `LIST: recorded=<oid>[,<oid>…] current=<oid> match=yes|no` before its token, where `current` is `git rev-parse HEAD:<list path>`. `match=no` is **not** a refusal, because AC-5.4 is closed, so the operator check the plan states stays an operator check. *Owed to the spec:* an AC-5.4 reason (for example `list_changed:<oid>`) and an AC-3.6 citation of the list commit.

### D6. Content scan (AC-2.6 class closer)
- **Normaliser**, one function used for needle and haystack alike: `re.sub(r"\s+", " ", data.decode("utf-8", errors="replace"))`. There is no strip and no case folding.
- **Needles**: for all 27 seeds (every ledger record, not only the target's), the normalised `original` and the normalised `expected`. An empty needle refuses `ledger_counts` (D4), because it would match everywhere.
- **Walk**: `os.walk(root, followlinks=False)`. Every symlink, whether to a file or a directory, refuses `leak:<root-relative path>` whatever its target. Every regular file is read and scanned. The first hit in sorted path order refuses `leak:<root-relative path>`.
- **The one exemption**: a hit on seed `s`'s `original` in file `f` is exempt iff `f` sits at the live path where `s`'s own source document is placed as a paired copy, AND `sha256(f) == sha256(archive source of s)`. `expected` is never exempt. The seeded target sits at its source's live path, but its sha differs, so a hit there is a `leak` (spec: widen the span).
- **Residuals**, as the spec states them: paraphrase or partial copy; non-UTF-8 stored forms; reads outside the root by absolute path; name mentions; submodule paths, which `git archive` exports empty (a C2 seed must not name a path under `beautiful_prose`, `drawio-skills` or `humanizer`). Added here: special files other than symlinks are not refused. `git archive` emits only regular files, directories and symlinks.

### D7. Git reach check
The check walks the root for any entry named `.git` (file or directory) at any depth; the first one in sorted order refuses `root_git:<root-relative path>`. It then runs `git -C <root> rev-parse --absolute-git-dir` in an environment with `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY` and `GIT_ALTERNATE_OBJECT_DIRECTORIES` removed, which is the same environment the dispatch runs in. Exit 0 refuses `root_git:<the printed git dir>`.

### D8. Live dispatch and recording (S1, S2; the runbook in the measurement doc)
- **Kept directory**: `KEEP=$HOME/.local/state/h-mad/grok-audit-surface`. Under it, `authoring/` exists during S0b only. The stem dir for one cycle is `run-<cal12>/stem/<cycle-id>/`, and the recorded by-products go to `run-<cal12>/data/{s1,s2}/…`. `<cal12>` is the first 12 hex of the calibration sha, and `<cycle-id>` is `s1-<surface>` or `s2-d<k>-v<N>`. The kept directory lives under `$HOME`, so it is outside every export root (which live under `$TMPDIR`); `git -C $HOME/.local/state rev-parse --git-dir` fails there (Readings). The stem dir is created before the cycle, because the wrapper refuses a stem dir that is not "an existing absolute directory without ':'". This answers the delta review's S1 by-products should-fix: nothing the smoke derives from lives in `/tmp`, so `SMOKE: UNREADABLE`'s "derive again from the same passes" has its inputs.
- **One cycle**, as the runbook pins it. Every `<…>` is filled before the run; this block is a template for the measurement doc, not a command to run as written.

  ```bash
  ROOT=<path from ROOT: READY>; STEM="$KEEP/run-<cal12>/stem/<cycle-id>"; mkdir -p "$STEM"
  CMD=(env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR -u GIT_OBJECT_DIRECTORY \
       -u GIT_ALTERNATE_OBJECT_DIRECTORIES -u HMAD_AUDIT_CYCLE_SCRIPT_DIR \
       HMAD_AUDIT_STEM_DIR="$STEM" h-mad/bin/hmad-dispatch audit-cycle \
       --feature <source feature> --phase <phase> --cycle <N> --project-root "$ROOT" \
       --passes <P> --surfaces <list> --timeout <AC-1.4 seconds>)
  printf '%q ' "${CMD[@]}" > "$STEM.command.txt"
  t0=$(date +%s); "${CMD[@]}" | tee "$STEM.stdout.txt"; t1=$(date +%s)
  python3 docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py record-cycle \
    --stem "$STEM" --root "$ROOT" --stdout "$STEM.stdout.txt" --command "$STEM.command.txt" \
    --dest "$KEEP/run-<cal12>/data/<s1/surface | s2/d<k>/v<N>>"
  ```

  S1 runs this three times: `--passes 1 --surfaces grok` (and writes `$((t1-t0))` to `wall_seconds.txt` in the grok dest), then `agy`, then `codex` when `command -v codex` succeeds. S1 omits `--timeout`, so the wrapper default of 900 s applies. S2 runs `--passes 3 --surfaces codex,agy,grok`, or `--passes 2 --surfaces agy,grok` when codex is absent or refused the root at S1, with the AC-1.4 derived `--timeout`. The time bound is the wrapper's own `--timeout`, never `timeout <s>` (base §"Portable time bounds").
- **`record-cycle`** copies the D3 files from the stem dir (matched by the stem's single `audit_<feature>_<phase>_cycle<N>_run*` prefix; more than one prefix refuses `cycle_token:<cycle-id>`) and from the root. It then re-lists the dest and prints `files=<n>`. It refuses `cycle_token:<cycle-id>` when the stdout file holds no line starting `AUDITCYCLE: `, so a cycle whose wrapper exited 4 on assembly failure is caught at record time as well as at score time.
- **Re-dispatch (AC-3.4).** A cycle whose recorded `AUDITCYCLE:` is `UNVERIFIED` (any reason, `prompt_divergence` and `assemble_halt:pN` included) is re-run once, in a fresh root (`s2v2`), as `--cycle 2`, which gives a new sentinel. No third cycle is run.

### D9. Calibration data, the two shas and the ref (`commit-data`, `rescore`; AC-2.7)
- **No checkout anywhere (answers delta review should-fix 4).** `commit-data` builds each branch commit with plumbing in the operator's `main` clone. It uses a temporary index (`GIT_INDEX_FILE=<mkdtemp>/index`): `git read-tree <parent>`; `git hash-object -w` for each file under `--src`; `git update-index --add --cacheinfo 100644,<blob>,<calibration dir>/<rel>`; `git write-tree`; `git commit-tree <tree> -p <parent> -m <message>`; `git update-ref refs/heads/calibration/grok-audit-surface <new> <expected old>`. The expected old value is the parent when the ref exists, and the zero-oid form (`git update-ref <ref> <new> ""`) for the first commit. It re-reads `git rev-parse refs/heads/calibration/grok-audit-surface` and prints `COMMIT: OK` only when that equals `<new>`. It refuses (exit 2, `COMMIT: REFUSED reason=<parent_unknown|ref_moved|outside_calibration_dir>`) and writes no ref when `--parent` is not a commit, when the ref's current value is neither absent nor `--parent`, or when any `--src` path would land outside the calibration directory. The work tree and the real index are never touched. `$KEEP/authoring/` (the ledger and seeded copies as plain files) is deleted after the calibration sha is pushed and confirmed, so during S1 and S2 the ledger exists only as git objects (the AC-2.6 residual (3) and AC-2.7 residual (5) routes, which stay open).
- **The commits on the branch.** The first commit's parent is the `main` sha that holds S0. One or more commits follow while S0b answers refusals by re-choosing spans (never an amend). The **calibration sha** is the first one on which `check-ledger` reads `LEDGER: OK` and every `build-root` reads `ROOT: READY`. Next comes a **smoke commit** holding `s1/` and the S1 lines in `roots.jsonl`. Last comes the **score sha** holding `s2/`, the remaining `roots.jsonl` lines, `findings.jsonl`, `key.jsonl` and `labels.jsonl`. Every commit after the calibration sha touches only the calibration directory, which is what the drift rule requires. Each push is `git push origin refs/heads/calibration/grok-audit-surface:refs/heads/calibration/grok-audit-surface` (no force), confirmed by `git ls-remote origin refs/heads/calibration/grok-audit-surface` printing the expected sha.
- **DECISION (design-author): the smoke commit.** The S1 by-products are calibration data under the catch-all, because the smoke document is seeded. They are committed on every smoke outcome that derives (PASS or FAIL). On PASS the score sha descends from the smoke commit; on FAIL the smoke commit is the branch tip and no score sha exists (AC-1.8). *Owed to the spec:* AC-1.8 lists only the ref and the calibration sha as citations, and the measurement doc on a smoke failure has to cite the smoke commit too, so that the smoke can be re-derived.
- **`rescore` ref and sha checks**, in this order. The first failure refuses.
  1. `git ls-remote --exit-code <remote> refs/heads/calibration/grok-audit-surface`: exit 2 refuses `calibration_ref:ref_absent`; any other non-zero exit (128 for a missing remote or an unreachable URL; Readings) refuses `calibration_ref:fetch_failed`. Then `git fetch --no-tags <remote> +refs/heads/calibration/grok-audit-surface:refs/h-mad-probe/grok-audit-surface/calibration`; a non-zero exit refuses `calibration_ref:fetch_failed`, and so does a missing local ref afterwards. The fetched tip is that ref. It is a private namespace, never a branch, so nothing is ever checked out from it.
  2. For each cited sha (calibration, then score): `git cat-file -e <sha>^{commit}` fails, which refuses `calibration_ref:sha_unknown:<sha>`; or `git merge-base --is-ancestor <sha> <tip>` exits 1, which refuses `calibration_ref:not_on_ref:<sha>`.
  3. `git merge-base --is-ancestor <calibration> <score>` exits 1, which refuses `calibration_drift:not_descendant`. Then `git diff --name-only -z <calibration> <score>`, sorted: the first path not under the calibration directory refuses `calibration_drift:<path>`.
  4. Export the score sha (as in D5 step 2) into a fresh `mkdtemp` directory, and run the D7 reach check on it (`root_git:<path>` if it fails).
  5. **Main leak check** over `git ls-tree -r -z HEAD`, with blobs read through `git cat-file --batch`. It prints `MAINLEAK: scanned=<HEAD sha40> blobs=<n>` and refuses `main_leak:<path>` (first in sorted order) on: (i) `sha256(blob)` equal to the sha256 of any calibration data file (D3's set) in the export; (ii) the normalised blob containing any normalised `expected`; (iii) the normalised blob containing any normalised `seeded` span that does **not** occur in the normalised archived source of the same seed.
  6. `check-ledger` on the export; `build-root --purpose rescore` for `d1`…`d9` from the calibration sha, with the list at `HEAD`; the D5 `LIST:` line.
  7. `score --tree <export>`.
  8. In a `finally`: remove every temporary directory, re-list to confirm removal, and print the `[H-MAD]` marker. A removal failure is printed on stderr and never replaces the token.

### D10. One authority per wrapper verdict: the final member list (plan "The class")
The rule, restated from the plan: the probe reads each verdict the wrapper or the gate already computes from that authority's token line, or by importing its function, and re-derives none. The final list:

| Member | Authority | What the probe reads | Opposed-input fixture pair (one per direction) |
|---|---|---|---|
| M1 AC-3.2 `prompt_divergence` | `_cmd_audit_cycle` diff check | `reason=prompt_divergence` on the recorded `AUDITCYCLE:` line | (a1) prompts differing on a foreign line, beside a dispatched `PASS` token: the cycle must NOT fail AC-3.2. (a2) Byte-identical prompts beside a dispatched `PASS` token: must NOT fail. (b) Prompts differing only on report-path lines, beside `UNVERIFIED reason=prompt_divergence`: MUST fail |
| M2 AC-3.1 assembly | `_cmd_audit_cycle` `ASSEMBLE:` loop | `reason=assemble_halt:p<i>` on the recorded line; no line at all → `cycle_token` | (c1) every `p<i>.asm.txt` reading `ASSEMBLE: PASS …`, beside `UNVERIFIED reason=assemble_halt:p2`: MUST be treated as halted. (c2) `p2.asm.txt` reading `ASSEMBLE: HALT p2:preflight`, beside a `PASS` token: must NOT be treated as halted |
| M3 AC-1.1 `format=grok` vs `grok-truncated` | `h_mad_audit_cycle._effort_items` (shape from `scan_grok`) | the grok pass's `Effort:` item: `format=grok` present, or not | (d1) a log with an `end` event (scan says `grok`), beside a truncated Effort item: MUST give `truncated`. (d2) a log with no `end` event, beside a `format=grok` item: must NOT give `truncated` (it does give `vocab_missing:end`, a separate observation) |
| M4 AC-1.3 and AC-3.4 delivery | `h_mad_audit_cycle.collect` | the `delivered=` field, per pass position; plus the `GATE:` token from running `h_mad_audit_gate.py` on `collected/…md` | (e1) a clean collected report and a transport report present, beside `delivered=none`: MUST give `no_delivery` (smoke) and score zero findings for that pass (score). (e2) the transport `p1.report.md` absent but `delivered=report-file` with the collected copy present: must NOT give `no_delivery`, and is scored |
| M5 AC-1.6 and AC-3.4 `UNVERIFIED` | `h_mad_audit_cycle.combine` | the verdict word on the recorded line | (f1) a log whose `measure_effort` gives `ok` above the floor, beside `UNVERIFIED reason=low_evidence:p1`: MUST count as UNVERIFIED (S1: refused root; S2: v2 required). (f2) a log with `ok=0`, beside `PASS`: must NOT |
| M6 AC-4.1 `must_count` | `h_mad_audit_gate.classify` | imported; compared with the extractor's count | covered by the import itself, plus the `must_count_mismatch:<report>` fixture (the plan's rule for imported members) |

**Each fixture is checked against its authority when it is built** (delta review rule). The test that uses a pair first runs the real authority on the raw inputs and asserts that it gives the verdict *opposite* to the recorded token. That authority is `h_mad_review_evidence.scan_grok` / `h_mad_audit_cycle.measure_effort` for M3 and M5, `h_mad_audit_cycle.combine` for M5, and `h_mad_audit_gate.py` for M4. M1 and M2 are checked by driving the real `_cmd_audit_cycle` through `install_audit_cycle_stubs` and `run_audit_cycle` (from `h-mad/tests/test_hmad_dispatch_audit_cycle.py`) on the three M1 shapes and on an `ASSEMBLE: HALT` shape, asserting the wrapper's own verdicts. That is one test, `test_m1_m2_raw_shapes_are_what_the_wrapper_says`, in the wrapper test module. Residual, stated exactly: a member whose authority needs a live agent has no offline check. None of M1–M5 does.

**Excluded, with reasons.** These are read but never decided on, so a drift moves no verdict: the AC-1.4 `RESOLVED-MODEL` line (published only), the AC-3.3 `log_sha256` from `.effort.json` (published only), and the AC-1.2 vocabularies (sources, not verdicts; read by import and by text, never copied). The plan's residual stands: a second copy outside the probe, or a copy computed but never consulted, is not seen by the pairs.

`COLLECT:` is **not** a member. `hmad-dispatch audit-cycle` prints no `COLLECT:` line: `COLLECT:` is printed only by `h_mad_collect_report.py`, while `h_mad_audit_cycle.py` collects internally and reports `delivered=` (Readings). So AC-1.3's "`COLLECT: OK`, or a non-`none` `delivered=`" is always met through `delivered=` on this path, and no smoke input is a `COLLECT:` line.

### D11. Smoke mode (AC-1.7)
- **Inputs** (`--data <dir>/s1`): `grok/` and `agy/`, which are required, and `codex/`, which is optional (its absence means "not run"). Each holds D3's cycle files.
- **UNREADABLE first**, so that exactly one reason is printed. The inputs are checked in this fixed order, and the first problem wins:
  1. `grok/auditcycle.txt`
  2. `grok/p1.log`
  3. the grok `collected/*.md` when `delivered=report-file`
  4. `agy/auditcycle.txt`
  5. the agy `collected/*.md` when `delivered=report-file`
  6. the same files for `codex/` when present
  7. the two vocabulary sources

  A file that is absent gives `input_missing:<path>`. A file that is present gives `input_unparseable:<path>` in four cases: an `auditcycle.txt` with not exactly one line matching `^AUDITCYCLE: (PASS|FAIL|UNVERIFIED)( \S+)*$`, or with no `Effort:` item for `p1`; a log in which no line parses as a JSON object with a string `type`; a vocabulary source with no `_GROK_TYPES` frozenset or no `_GROK_TYPES_RE=` line; a collected report on which `h_mad_audit_gate.py` prints no `GATE:` line.
- **Vocabulary injection (plan obligation).** `--vocab-py <path>` (default `h-mad/scripts/h_mad_review_evidence.py`) is loaded with `importlib.util.spec_from_file_location("_gas_vocab_py", path)` and its `_GROK_TYPES` attribute is read. `--vocab-sh <path>` (default `h-mad/scripts/hmad-dispatch.sh`) is read as text. A fixture drives `vocab_split` by passing a three-line Python file and a one-line shell file whose sets differ.
- **Reasons, as independent observations, in AC-1.7 order:**
  - `truncated`: the grok `Effort:` item for `p1` lacks `format=grok`. This reads the cycle's `Effort:` block (the shape `scan_grok` decided).
  - `vocab_split`: the two vocabulary sets differ.
  - `vocab_missing:<type>`, for each of `end`, `tool_call`, `tool_call_update` (in that order) absent from the log's distinct `type` set. This reads the log's type set. Because `truncated` and `vocab_missing:end` read separate observations, each can be driven alone (D10 M3).
  - `no_delivery`: the grok pass's `delivered=` field is not `report-file`, or its `GATE:` token is neither `PASS` nor `FAIL`. **DECISION (design-author):** `delivered=out` (the report extracted from the agent's final message by `_run_extract_report`) is `no_delivery`, because AC-1.3 says "A verdict read from grok's final message alone does not count".
  - `nongit_root_refused:grok`, then `nongit_root_refused:agy`: the surface has no delivery evidence by the rule above, or its verdict word is `UNVERIFIED`.
- **codex** goes through the same acceptance predicate, is printed as `ROOT-ACCEPT: codex=accepted|refused|not_run`, and is never a reason.
- **Published lines, before the token:** one `VOCAB: type=<t> re=in|out frozenset=in|out tool=yes|no usage=yes|no` per distinct type, sorted. Here `tool`/`usage` is `yes` when any key of that type's events, to depth 2, contains `tool`, or contains `usage` or `token`. Then `ROOT-ACCEPT: grok=… agy=… codex=…`, and `TIMEOUT: wall_seconds=<W> derived=<max(900, ceil(1.5·W/60)·60)>` (or `wall_seconds=unrecorded`; `wall_seconds.txt` is not a smoke input, so its absence is not UNREADABLE).
- **Exit**: 0 on `SMOKE: PASS` and `SMOKE: FAIL reason=<r>[,<r>…]`, and 2 on `SMOKE: UNREADABLE reason=<r>`.

### D12. Extraction, blinding and hints (`extract`; AC-4.1–4.4)
- **The stands rule (AC-3.4, plan Risks).** For each document, `v1` is read. If its verdict word is `UNVERIFIED`, `v2` must exist and **the whole of `v2` stands for every surface**, including surfaces whose `v1` pass was fine; nothing in `v1` is scored. If `v1` is not `UNVERIFIED`, `v1` stands. If `v2` is also `UNVERIFIED`, it still stands: each pass whose `delivered=` is `none` or `unscorable:…` contributes zero findings, and every delivered pass is scored even when its evidence was low.
- **Cycle-record refusals**, all `cycle_token:d<k>.v<N>`: `v1` missing, or its `auditcycle.txt` lacking a parseable line; `v2` required but missing or unparseable; a `v2` present when `v1` is not `UNVERIFIED`; any `v3` or later; a `command.txt` with no parseable `--surfaces` of exactly `codex,agy,grok` or `agy,grok`; a delivered pass whose `collected/` report is missing. **DECISION (design-author):** these all share `cycle_token`, because AC-5.4 is closed and each one is a cycle record the score cannot read as written. *Owed to the spec:* AC-5.4 names only "no recorded line" and "does not parse".
- **Pass → surface** is read from `command.txt`'s `--surfaces` list by pass index (AC-10.1's sense: index, not time).
- **Findings**: for each scored report, the `## Must-fix` section's content lines go through `h_mad_audit_gate._bullet_groups`. Each group with a real parent payload is one finding, whose text is the group's lines joined. When the section has non-`None` content but no bullet, the whole content is one finding (the gate's fail-safe rule). The probe asserts `len(findings) == classify(text)["must_count"]`; a mismatch refuses `must_count_mismatch:<report tree path>`. The equality check, not this walk, is the guarantee. Residual: a report on which the walk and the gate disagree is refused, never scored. The walk is the pure function `extract_findings(text, *, must_count=<classify's must_count>)`, so a fixture can inject a disagreeing counter. A scratch probe at `3660aeeb` found no real report shape that makes the two disagree (5 shapes: nested children, a `- None` parent with a child, a `class:` line between children, a numbered item before a bullet, prose only), so the `must_count_mismatch` fixture drives the guard through that parameter, in process.
- **Blinding**: ids are `F%08x` from `random.Random(shuffle_seed).getrandbits(32)`, redrawn on collision, and the order is shuffled by the same generator. `findings.jsonl` carries `id doc cycle text quotes` (the `quote:` lines) and no surface or pass. `key.jsonl` carries `id doc cycle pass surface report`, plus one `{"shuffle_seed": n}` record.
- **Hints (AC-4.4)** are printed to stdout only, as `HINT: <id> candidate-fabrication` (a `quote:` whose span is absent from the named file in the exported calibration tree) or `HINT: <id> candidate-hit:<seed-id>` (a `quote:` overlapping a seed's `seeded` span). They are never written to any file that `score` reads.

### D13. Scoring (`score`; AC-4.3, 4.5, 5.1–5.3)
- **Inputs**: `--tree`'s calibration directory: the ledger, the recorded cycles, `findings.jsonl`, `key.jsonl`, `labels.jsonl`.
- **Order of refusals**: `ledger_counts`, then `ledger_origin`, then `seed_rebuild` (D4), then `cycle_token` (D12), then `must_count_mismatch` (re-extracted), then `key_mismatch`, then `label:<id>`. `key_mismatch` fires when the set of ids in `findings.jsonl` differs from the set in `key.jsonl`, or when re-extraction from the recorded reports does not reproduce the multiset of `(report, text)` that the findings joined with the key give. `label:<id>` fires on a finding with no label, a label for an unknown id, a value outside `HIT:<seed-id> REAL FABRICATED UNDECIDABLE`, an `UNDECIDABLE` with an empty `why`, or a `HIT` naming a seed that is not in that finding's document. **DECISION (design-author):** a seed of another document counts as "a `HIT` naming an unknown seed" for that finding.
- **Per surface**: `hits` = distinct seeds with at least one `HIT` from that surface (AC-4.5); `n` musts; `f` fabricated; `u` undecidable; `fab_rate = Fraction(f, n−u)`, with `0/0` read as `Fraction(0)` (AC-5.2). Each surface prints `SURFACE: <s> recall=<hits>/27 musts=<n> fabricated=<f> undecidable=<u> fab_rate=<f>/<n−u> delivered=<counts> low_evidence=<count>`. The denominator is the ledger's seed count, derived. On the codex-unavailable shape, codex prints `SURFACE: codex not_run`.
- **D3**: `d3(fg, rg, fa, ra) = (fg < fa and rg >= ra) or (fg == fa and rg > ra)`, over `Fraction` and `int`. The worst cases, with undecidables decided, use denominator `n`:
  - pessimistic grok: `Fraction(f+u, n)`
  - optimistic grok: `Fraction(f, n)`
  - and the same pair for agy.
  - `n = 0` reads as zero.
- **Verdict**, in this order:
  1. If no surface (codex included) has a hit: `INCONCLUSIVE reason=seeds_undetected`. **DECISION (design-author):** this is checked first, because AC-5.3 says the seeds then "measure nothing", and a zero-recall `PASS` on fabrication alone would promote on an instrument that measured nothing. *Owed to the spec:* make that precedence explicit.
  2. `d3(pess_g, rg, opt_a, ra)`: `PASS`.
  3. `not d3(opt_g, rg, pess_a, ra)`: `MISS reason=bar_missed`.
  4. Otherwise: `INCONCLUSIVE reason=undecidable_flips`.
- **Token**: `SEEDSCORE: <V>[ reason=<r>] calibration=<sha40|unstated> score=<sha40|unstated>` is the last stdout line.

### D14. SKILL.md and `grok-runtime.md` text (exact strings the tests pin)
- **AC-6.2a (S0).** In §"Teammate audit leg — when codex is unavailable", the code span `h_mad_audit_cycle.py --surfaces agy,grok` becomes `hmad-dispatch audit-cycle --feature <feature> --phase <phase> --cycle <N> --project-root <root> --passes 2 --surfaces agy,grok`. Nothing else in the section changes at S0.
- **AC-9.5 (S0).** This sentence is appended to the bullet in §"What you NEVER do" that starts "**Name the reviewer legs with `--legs`…**": "The first gate and the revisions run different leg sets by design, so the streak, when it is reached, is among revision cycles."
- **AC-6.2 (S3, scored outcomes).** At both sites (the `exec grok` bullet of §"Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot", and the teammate section) "audit precision" leaves the unmeasured list. It is replaced by the measured fractions and the pointer `docs/03-analysis/grok-audit-surface.measurement.md`, while `unmeasured` stays for GREEN, mutation and wiring. On a smoke failure (AC-1.8), audit precision stays, and the pointer and the clause "the grok 1.0.62 audit-path smoke failed" are added.
- **AC-7.1, 7.3 and 8.3 (S4, PASS only)** are as the spec states. Their pinned literal is `--surfaces codex,agy,grok`, in §"Never gate on one audit pass".
- **AC-7.4: does a test assert the MISS/INCONCLUSIVE state? Yes.** **DECISION (design-author):** on MISS or INCONCLUSIVE, S3 ships `test_never_gate_section_keeps_two_surface_routing_off_pass`. It asserts that §"Never gate on one audit pass" contains no `--surfaces codex,agy,grok` and still contains "that is three reports, of which two share a model family". The "byte-unchanged except the pointer" claim is evidenced by the plan's section-scoped diff in the measurement doc, not by the test, because a test that reads git history goes stale at archive time. On PASS this test is not shipped (the AC-7.3 pins replace it).

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| Scorer probe | `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` | new | the eight modes (D1–D13) |
| Declared exclusion list | `docs/03-analysis/probes/grok-audit-surface/exclusions.txt` | new | the six entries (D5) |
| Synthetic fixture builder | `h-mad/tests/grokauditfixtures.py` | new | invented archives, ledgers, cycle records, temp repos with a bare `origin` |
| Probe tests | `h-mad/tests/test_grok_audit_surface_probe.py` | new | AC-2.2–2.7, AC-3.2/3.4, AC-4.1–4.5, AC-5.1–5.5, D10 pairs |
| Smoke tests | `h-mad/tests/test_grok_audit_surface_smoke.py` | new | AC-1.7 fixtures, D10 M3–M5 smoke pairs |
| Gate pins | `h-mad/tests/test_grok_audit_surface_gate_pins.py` | new | FR-8 (AC-8.1, 8.2), FR-9 (AC-9.1–9.4) |
| Wrapper pins | `h-mad/tests/test_grok_audit_surface_wrapper.py` | new | FR-10, the identical-prompts divergence test, the M1/M2 authority check |
| Doc pins | `h-mad/tests/test_grok_audit_surface_docs.py` | new | AC-6.2a new test, AC-9.5, the exclusion list's required entries; S3/S4 pins by outcome |
| Audit-cycle stub | `h-mad/tests/test_hmad_dispatch_audit_cycle.py` (`install_audit_cycle_stubs`) | modify | one env knob, `HMAD_ASSEMBLE_SAME_REPORT_P<i>`: write a constant in place of the report path, so two passes can assemble byte-identical prompts |
| Mutation spec | `h-mad/tests/mutation-specs/grok_audit_surface.json` | new | the rows in Test Plan |
| SKILL.md text | `h-mad/SKILL.md` | modify | D14 |
| Runtime reference | `h-mad/references/grok-runtime.md` | modify (S3) | the AC-1.5 or AC-1.8 sentence |
| Measurement doc | `docs/03-analysis/grok-audit-surface.measurement.md` | new (S3) | FR-6 plus the runbook (D8) |

The FR-8, FR-9 and FR-10 tests go in **new** modules rather than extending `test_h_mad_audit_cycle_grok.py`, `test_h_mad_audit_gate.py` and `test_hmad_dispatch_audit_cycle_grok.py`. **DECISION (design-author):** the mutation rows name tests by path, and a new module keeps that path stable whatever happens to the large existing files. The new modules import the existing helpers rather than copying them: `audit_cycle` and `pass_result` from `test_h_mad_audit_cycle`; `f0_text`, `f_trunc` and `f0_with_completed` from `grokfixtures`; `run_with_cmd_exec_stub`, `_dispatch_artifacts_by_pass`, `dispatch_args`, `project_with_docs`, `read_jsonl`, `install_audit_cycle_stubs`, `run_audit_cycle` and `_script_dir_with_stub_assemble_and_real_cycle` from `test_hmad_dispatch_audit_cycle`; `titled_section` from `docsections`.

## Implementation Order
1. `exclusions.txt`, plus the doc test pinning its six entries.
2. `grokauditfixtures.py`: the synthetic archive builder (3 invented features × spec, plan, design, impl-plan; 9 documents, 27 seeds by the AC-2.2 rule) and the temp-repo builder (`git init`, a local bare `origin`).
3. Probe core: the normaliser, D4 ledger checks, D5/D6/D7 root build, scan and reach. Each refusal is written RED first.
4. `record-cycle`, `commit-data`.
5. `smoke` (D11), with D10 M3–M5.
6. `extract`, `score` (D12, D13), with D10 M1, M2, M4 and M6.
7. `rescore` (D9).
8. FR-8, FR-9, FR-10 pins; the stub knob plus the identical-prompts test; the M1/M2 authority test.
9. AC-6.2a: the RED run of the new doc test against the uncorrected SKILL.md, recorded first; then the correction. Then AC-9.5.
10. Phase 5e: the mutation spec rows (Test Plan); `MUTATION: ALL_CAUGHT` with `untargeted=0/<n>` and `crash_kills=0`; `ANCHORS: ANCHORS_OK`.
11. S0b, S1, S2 (operator, D8/D9); then S3 (measurement doc, `grok-runtime.md`, AC-6.2 text and its pointer tests, the K2 row re-anchored); then S4 on PASS.

## Data Model / Schema Changes
- `ledger.jsonl`: `{"id": str, "source": str (tree path of the archived document), "phase": "plan"|"design"|"impl-plan", "class": "C1"|"C2"|"C3"|"C4", "origin": str ∈ ORIGINS, "section": str, "original": str, "seeded": str, "expected": str}`.
- `findings.jsonl`: `{"id": str, "doc": "d<k>", "cycle": int, "text": str, "quotes": [str]}`.
- `key.jsonl`: `{"id", "doc", "cycle", "pass": int, "surface": "codex"|"agy"|"grok", "report": str}`, plus one `{"shuffle_seed": int}`.
- `labels.jsonl`: `{"id": str, "label": str, "why": str}`.
- `roots.jsonl`: `{"line": "ROOT: READY …"}`.
- `exclusions.txt`: the D5 grammar.
- No change to any `h-mad/` state file, stamp or schema.

## API / Interface Changes
- The new CLI is the D2 table. There is no new flag on any existing script, and no change to `hmad-dispatch`'s grammar.
- The test-only stub knob is `HMAD_ASSEMBLE_SAME_REPORT_P<i>=1` in `install_audit_cycle_stubs`. Existing tests do not set it, so their prompts are byte-for-byte what they are today.

## Error Handling Strategy
- Every refusal is a token line, read by callers from stdout and never from `$?` (base §"Audit-gate signal discipline").
- **`SEEDSCORE: UNREADABLE reason=<r>`** (exit 2). The reasons are AC-5.4's closed list. Where each one fires:
  - `ledger_counts`, `ledger_origin`, `seed_rebuild`: D4
  - `leak:<path>`: D5, D6
  - `root_git:<path>`: D7, D9
  - `must_count_mismatch:<report>`, `key_mismatch`, `label:<id>`: D12, D13
  - `calibration_drift:<path>`, `calibration_drift:not_descendant`, `calibration_ref:<kind>`, `main_leak:<path>`: D9
  - `cycle_token:<cycle>`: D8, D12

  The order inside each mode is the order listed in its section.
- **Smoke**: `SMOKE: UNREADABLE reason=input_missing:<path>|input_unparseable:<path>` (exit 2) is decided before any FAIL reason (D11).
- **Operational modes** refuse with their own tokens: `RECORD:` refuses as `cycle_token:<cycle-id>` (see D8), and `COMMIT: REFUSED reason=<parent_unknown|ref_moved|outside_calibration_dir>` exits 2.
- **Unexpected errors.** An exception that escapes (an `OSError` on read, a `git` binary that is absent) is caught at `main`. It prints `SEEDSCORE: UNREADABLE reason=…` only when it maps to a listed reason, and otherwise prints a Python traceback on stderr and exits 2 with **no** token, so no caller can read it as a verdict. **DECISION (design-author):** no catch-all reason, because AC-5.4 is closed and inventing one would widen it.

## Test Strategy
- **Synthetic only, never the network or the real ref** (AC-2.7). Every AC-2.7 fixture builds `tmp_path/origin.git` (bare) and `tmp_path/work` with `origin` pointing at it, and creates the branch inside that repo. Each test whose clean case depends on `tmp_path` lying outside a work tree first asserts that `git -C tmp_path rev-parse --git-dir` fails; it does not skip.
- **The probe is driven as a subprocess** (`sys.executable` plus the literal path), so the exit code and the token are asserted together. Pure helpers (the normaliser, `d3`) are also imported for unit tests, by path, through `importlib.util.spec_from_file_location`.
- **Archive survival.** Each probe test module defines `PROBE = REPO / "docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py"` as a single literal, which is what `h_mad_archive_feature.probe_readers` matches (needle `docs/03-analysis/probes/grok-audit-surface` followed by a path boundary).
- **Tests over unchanged code** (FR-8, FR-9, FR-10, the kept doc pins) are shown able to fail only by their mutation rows. **New probe guards** are RED first, and then each gets a row.
- **Incident replay** (base §"Incident replay"). The real artefacts are the archived documents and the live runs. AC-2.7 forbids real calibration data in the suite, so the replay is the S0b `check-ledger`/`build-root` run and the S3 `rescore` run over the real ref, whose token lines the measurement doc records.

## Test Plan

### Probe tests: `h-mad/tests/test_grok_audit_surface_probe.py`
Each named fixture is run with its trigger alone; everything else in the fixture is clean.
- **Ledger:** `test_ledger_counts_refuses_a_moved_class` (one seed's class changed), `test_ledger_counts_refuses_a_missing_field`, `test_ledger_origin_refuses_an_unknown_origin`, `test_seed_rebuild_refuses_one_byte`, `test_seed_rebuild_refuses_a_twice_occurring_original`, `test_seed_rebuild_refuses_a_seed_under_version_history`, `test_ledger_ok_reports_derived_counts`.
- **Leak**, one test per trigger:
  - `test_leak_original_hit`
  - `test_leak_expected_hit`
  - `test_leak_hit_only_after_rewrap` (a copy with its whitespace changed)
  - `test_leak_symlink_to_file`
  - `test_leak_symlink_to_dir`
  - `test_leak_original_in_paired_copy_with_other_sha` (the exemption must not apply)
  - `test_leak_expected_in_byte_identical_paired_copy` (the exemption never covers `expected`)
  - `test_leak_on_the_seeded_target`
  - `test_leak_unknown_exclusion_directive`
  - **must not refuse:** `test_original_in_byte_identical_own_source_copy_does_not_refuse`
- **Reach:** `test_root_git_dot_git_directory`, `test_root_git_dot_git_file`, `test_root_git_root_nested_in_work_tree` (`--dest-parent` inside a `git init`ed dir), `test_root_git_ignores_ambient_git_dir_env` (`GIT_DIR` set in the test's env; the check removes it and still passes a clean root).
- **Root build:** `test_build_root_places_only_the_phase_pairs` (plan → spec; design → spec+plan; impl-plan → design), `test_build_root_removes_every_exclusion_entry`, `test_build_root_reads_the_list_from_the_commit_not_the_work_tree` (an edited, uncommitted list is ignored), `test_build_root_prints_list_commit_and_blob`.
- **Drift:** `test_drift_outside_calibration_dir`, `test_drift_not_descendant`.
- **Main leak:** `test_main_leak_trigger_i_byte_equal_copy`, `test_main_leak_trigger_ii_expected`, `test_main_leak_trigger_iii_seeded_span`. **Must not refuse:** `test_seeded_span_also_in_its_own_archive_source_does_not_refuse`. Also `test_main_leak_prints_the_scanned_commit`.
- **Ref:** `test_ref_fetch_failed_no_remote`, `test_ref_absent`, `test_ref_sha_unknown`, `test_ref_not_on_ref`.
- **cycle_token:** `test_cycle_token_no_recorded_line`, `test_cycle_token_unparseable_line`, `test_cycle_token_v2_missing_after_unverified_v1`, `test_cycle_token_v3_present`, `test_cycle_token_unparseable_surfaces`, `test_cycle_token_delivered_report_missing`.
- **Extraction and labels:** `test_must_count_mismatch` (in process: `extract_findings` with an injected `must_count` one higher than the walk's count, D12), `test_key_mismatch_ids`, `test_key_mismatch_reextraction`, `test_label_unknown_value`, `test_label_unlabelled_finding`, `test_label_hit_unknown_seed`, `test_label_hit_seed_of_other_doc`, `test_label_undecidable_without_why`, `test_findings_carry_no_surface`, `test_hints_never_move_the_score` (AC-4.4: the score is equal with every hint changed or removed).
- **Verdicts.** These have no undecidables unless named:
  - `test_d3_strictly_lower_fab_equal_recall_pass`
  - `test_d3_equal_fab_greater_recall_pass`
  - `test_d3_full_tie_miss`
  - `test_d3_equal_fab_lower_recall_miss`
  - `test_d3_unreduced_equal_fab_equal_recall_miss` (`1/4` against `2/8`)
  - `test_undecidable_flips_inconclusive`
  - `test_seeds_undetected_inconclusive`
  - `test_seeds_undetected_outranks_a_fabrication_pass`
  - `test_zero_decidable_musts_prints_0_over_0`
  - `test_score_exit_codes` (0, 0, 0, 2)
- **Stands rule:** `test_whole_v2_stands_for_every_surface`, `test_undelivered_pass_counts_zero_findings`, `test_low_evidence_delivered_report_is_scored`.
- **Opposed pairs (D10):** `test_m1_a1_foreign_line_beside_dispatched_token_does_not_fail`, `test_m1_a2_identical_prompts_beside_dispatched_token_does_not_fail`, `test_m1_b_report_path_only_beside_divergence_token_fails`, `test_m2_c1_pass_asm_beside_halt_token_is_halted`, `test_m2_c2_halt_asm_beside_pass_token_is_not_halted`, `test_m4_e1_score_ignores_report_beside_delivered_none`, `test_m4_e2_score_reads_collected_beside_report_file`, `test_m5_f1_unverified_token_requires_v2`, `test_m5_f2_pass_token_beside_hollow_log_stands`.
- **`commit-data`:** `test_commit_data_never_touches_work_tree_or_index`, `test_commit_data_refuses_a_moved_ref`, `test_commit_data_refuses_outside_calibration_dir`, `test_commit_data_rereads_the_ref`.
- **`rescore` end to end:** `test_rescore_reproduces_the_score_and_removes_its_temp_dirs`.

### Smoke tests: `h-mad/tests/test_grok_audit_surface_smoke.py`
Each asserts its exit code beside its token.
- **PASS and FAIL, exit 0:** `test_smoke_pass`, `test_smoke_truncated`, `test_smoke_vocab_split`, `test_smoke_vocab_missing_end`, `test_smoke_vocab_missing_tool_call`, `test_smoke_vocab_missing_tool_call_update`, `test_smoke_no_delivery`, `test_smoke_no_delivery_on_out_delivery`, `test_smoke_nongit_root_refused_grok`, `test_smoke_nongit_root_refused_agy`.
- **UNREADABLE, exit 2:** `test_smoke_input_missing`, `test_smoke_input_unparseable`.
- **Must not fail:** `test_smoke_codex_refusal_is_not_a_reason`, `test_smoke_out_of_vocabulary_type_is_not_a_reason`.
- **Ordering and contracts:** `test_smoke_two_reasons_in_order` (`truncated,no_delivery`), `test_smoke_unreadable_outranks_fail`, `test_smoke_prints_timeout_derivation`.
- **Opposed pairs:** `test_m3_d1_end_event_beside_truncated_item_is_truncated`, `test_m3_d2_no_end_beside_format_grok_is_not_truncated`, `test_m4_e1_clean_report_beside_delivered_none_is_no_delivery`, `test_m4_e2_missing_transport_beside_report_file_is_delivered`, `test_m5_f1_unverified_token_beside_busy_log_refuses_root`, `test_m5_f2_pass_token_beside_hollow_log_accepts_root`.
- The grok logs come from `grokfixtures` (`f0_text`, `f_trunc`, `f0_with_completed`), so the smoke fixtures share the existing grok stream shapes.

### Gate pins: `h-mad/tests/test_grok_audit_surface_gate_pins.py`
- `test_union_three_passes_only_grok_must_fails` (AC-8.1; `combine` over `pass_result` indices 1–3, with p3 `verdict="FAIL"`).
- `test_union_three_passes_all_clean_pass`.
- `test_floor_low_evidence_at_index_3` (p3 effort from `f0_text`) and `test_floor_truncated_at_index_3` (p3 from `f_trunc`), both AC-8.2.
- FR-9, through the gate CLI (`--exit-check`, `--round-cap 2`) over real-grammar stamp names `gas-fx.design.audit.v<N>.p<i>.md.gated.json`, written with `verdict`, `suite` and `legs` the way `test_h_mad_audit_leg_set_gate.py`'s `_stamp` writes them: `test_exit_three_leg_first_gate_then_codex_blocks_legs_changed` (AC-9.1), `test_exit_two_codex_revisions_ready` (AC-9.2), `test_round_cap_first_gate_counts_one_cycle` (AC-9.3), `test_exit_mixed_first_gate_legs_disagree` (AC-9.4).

### Wrapper pins: `h-mad/tests/test_grok_audit_surface_wrapper.py`
- `test_three_surfaces_map_pass_index_to_agent` (AC-10.1). From `run_with_cmd_exec_stub` and `_dispatch_artifacts_by_pass`, this asserts pass 1 → `codex`, 2 → `agy`, 3 → `grok`, each with its own report path. The mapping is by pass index from the prompt path, never by invocation order: `_cmd_audit_cycle` backgrounds every pass.
- `test_three_surfaces_print_no_repeated_warning` (AC-10.2).
- `test_three_surface_stamps_carry_sorted_legs` (AC-10.2; every `*.gated.json` carries `"legs": ["agy","codex","grok"]`). The stamps come from the real cycle helper, via `_script_dir_with_stub_assemble_and_real_cycle`. Residual: whether the `_cmd_exec` stub delivers a report for all three surfaces, so that stamps are written, is not verified by this design. The impl-plan's RED step for this test confirms it, and adds the delivery to the stub if it is missing.
- `test_two_surfaces_for_three_passes_exit_2` (AC-10.3).
- `test_identical_prompts_halt_prompt_divergence`. `HMAD_ASSEMBLE_SAME_REPORT_P1=1` and `HMAD_ASSEMBLE_SAME_REPORT_P2=1` are set; the test asserts `AUDITCYCLE: UNVERIFIED reason=prompt_divergence` and zero dispatches. This is the empty-diff branch alone, which no existing test drives by name (Readings).
- `test_m1_m2_raw_shapes_are_what_the_wrapper_says` (D10).

### Doc pins: `h-mad/tests/test_grok_audit_surface_docs.py`
- **S0:**
  - `test_teammate_section_names_hmad_dispatch_audit_cycle`
  - `test_no_h_mad_md_pairs_audit_cycle_py_with_surfaces`. This scans `git ls-files -z 'h-mad/*.md'` with `h_mad_audit_cycle\.py[^\n]*\n?[^\n]*--surfaces`. It is RED before the correction, the RED run is recorded, and the stated residual is the spec's.
  - `test_never_do_legs_bullet_states_the_first_gate_leg_set`
  - `test_exclusion_list_holds_the_required_entries`
- **S3:** `test_both_unmeasured_sites_point_to_the_measurement_doc`, plus the outcome-specific assertion (retired fractions, or the smoke-failure clause).
- **S3, MISS or INCONCLUSIVE only:** `test_never_gate_section_keeps_two_surface_routing_off_pass` (D14).
- **S4, PASS only:** `test_never_gate_section_names_three_surface_first_gate`, `test_never_gate_section_names_grok_falsification`.

### Fixture names
`git ls-files 'h-mad/tests/*' | grep -E '\.(plan|design|impl-plan|spec)\.md$'` must print nothing, and printed nothing at `3660aeeb` (Readings). Every synthetic phase document is written under `tmp_path`. The doc test above does not enforce this, so the impl-plan's closing check re-runs the command.

### Mutation spec: `h-mad/tests/mutation-specs/grok_audit_surface.json`
- **Root:** `"root": "../.."`, which resolves to `h-mad/`, as for all 177 committed specs.
- **Commands:** `"command": ["/opt/anaconda3/bin/python3.11", "-m", "pytest", "tests/test_grok_audit_surface_probe.py", "tests/test_grok_audit_surface_smoke.py", "tests/test_grok_audit_surface_gate_pins.py", "tests/test_grok_audit_surface_wrapper.py", "tests/test_grok_audit_surface_docs.py", "tests/test_grok_fallback_docs.py", "tests/test_hmad_dispatch_audit_cycle.py", "-q"]`, and `"target_command": ["/opt/anaconda3/bin/python3.11", "-m", "pytest", "-q"]`. The harness requires a `target_command` once any row names a `test`.
- **Interpreter (R13). DECISION (design-author):** the absolute `/opt/anaconda3/bin/python3.11`, as 2 committed specs already do. It exists and runs pytest 9.1.1 on this Mac, whatever `PATH` holds (Readings). This **contradicts the brief and plan R13**, which say `python3.11` is absent: at `3660aeeb`, in this shell, `command -v python3.11` prints `/opt/anaconda3/bin/python3.11`. That binary is dated 2024, so the earlier "absent" was a `PATH` without `/opt/anaconda3/bin`, not a missing interpreter. The absolute path removes that dependency. The plan's Convention Prerequisites interpreter (`/opt/homebrew/opt/python@3.14/bin/python3.14`) has **no pytest** at `3660aeeb`, so it is not used.
- **Where Phase 5e runs:** on this Mac, from the repository root, in the Bash tool's shell: `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/grok_audit_surface.json` and `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/grok_audit_surface.json`. Before the run, a precondition: `/opt/anaconda3/bin/python3.11 -m pytest --version` must print a version. Accept only `MUTATION: ALL_CAUGHT` with `untargeted=0/<n>` and `crash_kills=0`, and `ANCHORS: ANCHORS_OK`, read from the token lines.

**Rows.** Every `find` below occurred exactly once in its file at `3660aeeb`, by `grep -cF` (Readings), except K1, whose text the S0 correction writes. Each row names exactly one `test`. A leading `␣` stands for one space, so the indentation is exact.

- **W1** `surf-map-rotate` (FR-10 remove). `scripts/hmad-dispatch.sh`, find `agent[$i]="${_surf[$((i - 1))]}"`, replace `agent[$i]="${_surf[$((i % passes))]}"`. Test: `tests/test_grok_audit_surface_wrapper.py::test_three_surfaces_map_pass_index_to_agent`.
- **W2** `surf-map-fixed` (FR-10 force). The same find, replaced by `agent[$i]="grok"`. Same test.
- **W3** `surf-map-fixed-warns` (FR-10 force, second assertion). The same find and replace as W2. Test: `::test_three_surfaces_print_no_repeated_warning`.
- **W4** `legs-default-dropped` (AC-10.2 remove). Find `␣␣␣␣legs=("${_surf[@]}")`, replace `␣␣␣␣legs=()`. Test: `::test_three_surface_stamps_carry_sorted_legs`.
- **W5** `legs-default-fixed` (AC-10.2 force). The same find, replaced by `␣␣␣␣legs=(codex)`. Same test.
- **W6** `surfaces-count-check-dropped` (AC-10.3). Find `␣␣␣␣[ "${#_surf[@]}" -eq "$passes" ] || {`, replace `␣␣␣␣true || {`. Test: `::test_two_surfaces_for_three_passes_exit_2`.
- **W7** `divergence-empty-branch-dropped` (R12, branch 1). Find `␣␣␣␣if [ -z "$div" ] || [ "$foreign" -ne 0 ]; then`, replace `␣␣␣␣if [ "$foreign" -ne 0 ]; then`. Test: `::test_identical_prompts_halt_prompt_divergence`. With `div` empty, `printf '%s\n' "$div" | … | grep -c '^[<>]'` counts 0, so only this branch halts identical prompts.
- **W8** `divergence-foreign-branch-dropped` (R12, branch 2). The same find, replaced by `␣␣␣␣if [ -z "$div" ]; then`. Test: `tests/test_hmad_dispatch_audit_cycle.py::test_verb_prompt_divergence`, which drives a foreign line through `HMAD_ASSEMBLE_DIVERGE_P2`.
- **G1** `leg-key-input-order` (AC-10.2 sort). `scripts/h_mad_audit_gate.py`, find `␣␣␣␣return sorted({str(name).strip() for name in legs if str(name).strip()})`, replace `␣␣␣␣return list(dict.fromkeys(str(name).strip() for name in legs if str(name).strip()))`. This keeps dedup and keeps the input order (`codex,agy,grok`) deterministically. It answers the delta review's point that dropping `sorted` alone leaves a hash-ordered set and a kill by chance. Test: `tests/test_grok_audit_surface_wrapper.py::test_three_surface_stamps_carry_sorted_legs`.
- **G2** `legs-changed-dropped` (AC-9.1). Find `␣␣␣␣␣␣␣␣if first != second:`, replace `␣␣␣␣␣␣␣␣if False:`. Test: `tests/test_grok_audit_surface_gate_pins.py::test_exit_three_leg_first_gate_then_codex_blocks_legs_changed`.
- **G3** `legs-disagree-dropped` (AC-9.4 remove). Find `␣␣␣␣␣␣␣␣if len(distinct) > 1:`, replace `␣␣␣␣␣␣␣␣if False:`. Test: `::test_exit_mixed_first_gate_legs_disagree`.
- **G4** `legs-disagree-always` (AC-9.4 force). The same find, replaced by `␣␣␣␣␣␣␣␣if True:`. Test: `::test_exit_two_codex_revisions_ready`. **DECISION (design-author):** the plan's force row, "treats every leg set as equal", is the same mutant as its remove row (the refusal never fires), so it would add no discrimination. The force direction is therefore "the refusal always fires".
- **G5** `round-counts-stamps` (AC-9.3). Find `␣␣␣␣␣␣␣␣grouped.add(key)`, replace `␣␣␣␣␣␣␣␣grouped.add((key[0], key[1], (key[2], path.name)))`. The three-field unpack in `round_check` still holds, so this is no crash kill. Test: `::test_round_cap_first_gate_counts_one_cycle`.
- **C1** `union-drops-p3` (AC-8.1). `scripts/h_mad_audit_cycle.py`, find `␣␣␣␣␣␣␣␣if result.verdict == "FAIL":`, replace `␣␣␣␣␣␣␣␣if result.verdict == "FAIL" and result.index != 3:`. It drops index 3, grok's, as the delta review's nit requires. Test: `::test_union_three_passes_only_grok_must_fails`.
- **C2** `floor-skips-last-pass` (AC-8.2). Find `␣␣␣␣␣␣␣␣if result.effort is None:`, replace `␣␣␣␣␣␣␣␣if result.effort is None or result.index == len(results):`. Test: `::test_floor_low_evidence_at_index_3`.
- **C3** `floor-skips-last-pass-truncated` (AC-8.2). The same find and replace as C2. Test: `::test_floor_truncated_at_index_3`.
- **K1** `teammate-surfaces-pin` (AC-6.2a kept pin; S0). `SKILL.md`, find `--project-root <root> --passes 2 --surfaces agy,grok`, replace `--project-root <root> --passes 2 --surfaces agy,codex`. Test: `tests/test_grok_fallback_docs.py::test_teammate_section_documents_the_grok_leg`.
- **K2** `teammate-unmeasured-pin` (AC-6.2 kept term). Written at S0, re-anchored at S3. At S0 it is `SKILL.md`, find `audit precision remain **unmeasured** (D4)`, replace `audit precision remain **measured** (D4)`; same test as K1. The S3 task that removes audit precision from that list re-points `find` to the S3 text's remaining `**unmeasured**` clause, and `--check-anchors` is what shows the move.
- **K3** `never-gate-surfaces-pin` (AC-7.3 kept pin; **S0, over today's text**). `SKILL.md`, find ``When Codex is unavailable and `fallback_agent=grok`, use `--surfaces agy,grok` ``, with `--surfaces agy,grok` replaced by `--surfaces agy,codex`. Test: `tests/test_grok_fallback_docs.py::test_never_gate_section_cross_references_the_grok_leg`. **DECISION (design-author):** written at S0 rather than only on PASS, because the pin exists today on every branch, and S4's edit of that section is exactly what it must survive (delta review should-fix: kept-pin rows had no stage).
- **P-rows, one per probe guard** (Phase 5e, S0). Each guard line in the probe carries a marker comment `# M:GAS-<NAME>` (the convention `hmad-dispatch.sh` uses, as in `# M:STEM-DIR`). Each row's `find` is that marker's line, its `replace` disarms the guard, and its `test` is the fixture above that drives that guard alone. The marker names:
  - **SMOKE:** `SMOKE-TRUNCATED`, `SMOKE-VOCAB-SPLIT`, `SMOKE-VOCAB-MISSING`, `SMOKE-NO-DELIVERY`, `SMOKE-NONGIT`, `SMOKE-INPUT-MISSING`, `SMOKE-INPUT-UNPARSEABLE`
  - **Ledger:** `LEDGER-COUNTS`, `LEDGER-ORIGIN`, `SEED-REBUILD`
  - **Leak:** `LEAK-ORIGINAL`, `LEAK-EXPECTED`, `LEAK-SYMLINK`, `LEAK-EXEMPT-SHA`, `LEAK-NORMALISE`
  - **Reach:** `GIT-ENTRY`, `GIT-REVPARSE`
  - **Extraction and labels:** `MUST-COUNT`, `KEY-MISMATCH`, `LABEL`
  - **Drift:** `DRIFT-PATH`, `DRIFT-DESCENDANT`
  - **Main leak:** `MAIN-LEAK-I`, `MAIN-LEAK-II`, `MAIN-LEAK-III`
  - **Ref:** `REF-FETCH`, `REF-ABSENT`, `REF-SHA-UNKNOWN`, `REF-NOT-ON-REF`
  - **Cycle:** `CYCLE-TOKEN`
  - **D3:** `D3-STRICT-LT`, `D3-EQ-STRICT-GT`

  `SMOKE-VOCAB-MISSING` and `SMOKE-NONGIT` loop over their alternatives at one site. Each gets one row per alternative fixture (three and two), so no alternative is covered only by a healthy sibling. The final P-row count is derived by Phase 5e from the probe's markers (`grep -c 'M:GAS-'` over the probe), never carried from this list.

**Residual.** A row shows its test can fail on that one change. A property the test asserts that no row disturbs stays unshown. `--check-anchors` catches a row that no longer lands, not one that lands somewhere harmless.

## Plan obligations answered
| Plan obligation | Answered in |
|---|---|
| Whether a test asserts the MISS-branch state of §"Never gate on one audit pass" (Ordering, MISS bullet) | D14, Doc pins |
| Scorer test module name; AC-6.2a doc-test module; FR-8/9/10 placement; fixture layout per AC-1.7/AC-5.5 branch, including the must-not-refuse fixtures (Where the tests live) | Components, Test Plan |
| Final list of consumed wrapper verdicts, and per member the token or function read (The class) | D10 |
| Prompt retention under `HMAD_AUDIT_STEM_DIR`; where the `AUDITCYCLE:`, `COLLECT:` and `Effort:` lines are recorded; the per-member pairs (One authority, design pins) | D3, D8, D10 |
| Vocabulary injection; smoke-mode command line; `truncated` vs `vocab_missing:end` as separate observations (SMOKE component) | D2, D11 |
| Mode names and command lines; `fetch_failed` vs `ref_absent`; the ancestry check; the calibration directory layout (Calibration data) | D2, D3, D9 |
| Each mutation row's find string and test (Connection tests) | Test Plan, mutation spec |
| The interpreter the new spec names and where Phase 5e runs it (R13) | Test Plan, mutation spec |
| The exclusion-list path (Which list version) | D5 |
| The root's parent directory (What the git reach check proves) | D5 |
| The AC-3.4 per-surface "stands" rule (Risks) | D12 |
| A `git ls-files` command showing no committed fixture is named like a phase document (Risks) | Test Plan, Fixture names; Readings |
| The export-root builder, the list format, the scan normaliser, the mutation-spec file (Next Steps 2) | D5, D6, Test Plan |
| The component that derives `SMOKE:` (spec AC-1.7) | D11 |
| The own-source exemption for the paired plan in design roots and the paired design in impl-plan roots (spec AC-2.6) | D5 step 4, D6 |
| Delta review should-fixes: R12 per branch; `_leg_key` row; S1 by-products' home; S0b's unnamed work tree; kept-pin row stages; the list version | W7/W8; G1; D8, D9 smoke commit; D9 `commit-data`; K1–K3; D5 "Which list version" |
| The opposed-fixture rule over every token-read check | D10 |

## Readings (stamped at `3660aeeb`)
The plan reserves the feature's probe directory on `main` for the probe and the exclusion list, so these readings carry their commands here rather than in a committed design probe. Each is a tree measurement; none counts this document.

| Claim | Reading | Unit |
|---|---|---|
| `python3.11` on this shell's `PATH` | `/opt/anaconda3/bin/python3.11`, `Python 3.11.8`, `pytest 9.1.1` | presence |
| `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest --version` | `No module named pytest` | presence |
| Committed specs by `command[0]`, over specs with a `command` | `python3.11` 166, `/opt/anaconda3/bin/python3` 9, `/opt/anaconda3/bin/python3.11` 2, of 177 | spec files |
| Spec `root` values | `../..` in all 177 | spec files |
| `h_mad_audit_cycle.py` then `--surfaces` (one line or across one break) over tracked `h-mad/*.md` | 1 occurrence in `h-mad/SKILL.md`; 32 files scanned | occurrences; files |
| Tracked files under `h-mad/tests/` named `*.plan.md`, `*.design.md`, `*.impl-plan.md` or `*.spec.md` | 0. The zero is load-bearing for the plan's Risks row, and holds because fixtures are built under `tmp_path` | files |
| `ORIGINS` entries | 8 | tuple members |
| `--surfaces agy,grok` in `h-mad/SKILL.md` | 2 occurrences on 2 lines (the teammate section and §"Never gate on one audit pass") | occurrences |
| Lines printing `COLLECT:` in `h_mad_audit_cycle.py` | 0 (2 matching lines, one in a docstring and one in a comment); printed by `h_mad_collect_report.py` | matching lines |
| Tests named for the empty-diff divergence branch alone | none found. The three `def test…diverg…` functions in the 3 test files that mention `prompt_divergence` are `test_verb_prompt_divergence` and `test_divergence_halt_survives_a_regex_metacharacter_stem_dir` (both drive a foreign line via `HMAD_ASSEMBLE_DIVERGE_P2`), and `test_main_no_pass_prompt_divergence_renders_single_auditcycle_line` (the helper's rendering; neither wrapper branch). This is a name search plus reading those three, not a full read | test names |
| `git ls-remote --exit-code` on a missing ref / a missing remote / a missing URL | exit 2 / 128 / 128 (scratch repo with a local bare origin, deleted after the run) | exit codes |
| `git -C <mktemp -d> rev-parse --git-dir`; `git -C $HOME/.local/state rev-parse --git-dir` | exit 128; fails (not a repository) | exit codes |
| Tracked files whose final component contains `grok-audit-surface` but does not begin with it | 2 (`docs/handoffs/2026-10-18-main__grok-audit-surface-phase3.md`, `…-phase3-exit.md`) | files |
| Mutation `find` anchors W1, W4, W6, W7, G1–G5, C1, C2, K2, K3 | each 1 matching line in its file | matching lines |

```bash
command -v python3.11; python3.11 --version; python3.11 -m pytest --version
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest --version
git ls-files -z 'h-mad/tests/mutation-specs/*.json' 'h-mad/tests/specs/*.json' | xargs -0 python3 -c 'import json,sys,collections
c=collections.Counter(); r=collections.Counter()
for p in sys.argv[1:]:
  d=json.load(open(p)); m=d.get("command"); r[d.get("root")]+=1
  if m: c[m[0]]+=1
print(dict(c), dict(r))'
git ls-files -z 'h-mad/*.md' | xargs -0 python3 -c 'import re,sys
rx=re.compile(r"h_mad_audit_cycle\.py[^\n]*\n?[^\n]*--surfaces"); n=0
for p in sys.argv[1:]:
  k=len(rx.findall(open(p,encoding="utf-8",errors="replace").read())); n+=k
print("occurrences",n,"files",len(sys.argv)-1)'
git ls-files 'h-mad/tests/*' | grep -cE '\.(plan|design|impl-plan|spec)\.md$'
grep -o -- '--surfaces agy,grok' h-mad/SKILL.md | wc -l
grep -n 'COLLECT:' h-mad/scripts/h_mad_audit_cycle.py h-mad/scripts/h_mad_collect_report.py
grep -n 'def test.*diverg' $(grep -ln 'prompt_divergence' h-mad/tests/*.py)
git ls-files | grep 'grok-audit-surface' | awk -F/ '$NF !~ /^grok-audit-surface/'
grep -cF 'agent[$i]="${_surf[$((i - 1))]}"' h-mad/scripts/hmad-dispatch.sh
grep -cF '    if [ -z "$div" ] || [ "$foreign" -ne 0 ]; then' h-mad/scripts/hmad-dispatch.sh
grep -cF '    legs=("${_surf[@]}")' h-mad/scripts/hmad-dispatch.sh
grep -cF '    [ "${#_surf[@]}" -eq "$passes" ] || {' h-mad/scripts/hmad-dispatch.sh
for s in '    return sorted({str(name).strip() for name in legs if str(name).strip()})' \
         '        if first != second:' '        if len(distinct) > 1:' '        grouped.add(key)'; do
  grep -cF -- "$s" h-mad/scripts/h_mad_audit_gate.py; done
grep -cF '        if result.verdict == "FAIL":' h-mad/scripts/h_mad_audit_cycle.py
grep -cF '        if result.effort is None:' h-mad/scripts/h_mad_audit_cycle.py
grep -cF 'audit precision remain **unmeasured** (D4)' h-mad/SKILL.md
grep -cF 'When Codex is unavailable and `fallback_agent=grok`, use `--surfaces agy,grok`' h-mad/SKILL.md
```

## Invariant Compliance
- **Audit-gate signal discipline**: complies. Every verdict is a stdout token, with exit 0 on PASS, FAIL, MISS and INCONCLUSIVE. Exit 2 is used only where an input could not be read (D1, Error Handling).
- **Single-source contract**: complies. The probe imports `classify`, `ORIGINS` and `_GROK_TYPES`, reads `_GROK_TYPES_RE` from its file, and reads wrapper verdicts from tokens (D10). There is one normaliser for the scan and the main leak check (D6).
- **Standalone / no plugin dependency**, and **No new external dependency**: complies. The probe uses the stdlib, `git` and pytest. No agent CLI is invoked by the probe or by any test; the wrapper tests use the existing stubs.
- **Portable time bounds**: complies. Live cycles are bounded by the wrapper's `--timeout`, and no design command uses `timeout`/`gtimeout`.
- **Doc-template superset compliance**: complies. This document carries the Phase 4 template's sections, and none of the plan-plus literals.
- **Operator-override preservation; Backward compatibility**: complies. There is no change to the gate, the sidecar or any verdict. The stub knob is opt-in, so existing tests' prompts are unchanged.
- **Marker discipline**: complies. Every probe mode writes an `[H-MAD]` marker to stderr (D1).
- **Mutation verification**: complies. `commit-data` re-reads the ref, `build-root` re-walks after each removal, every push is confirmed by `ls-remote`, and `rescore` re-lists after cleanup.
- **Test discrimination; Connection enforcement**: complies. New guards go RED first and get a P-row each. Tests over unchanged code get W/G/C/K rows, and each wire is mutated in both directions (W1/W2, W4/W5, G3/G4).
- **Incident replay; Reimplementation parity**: the replay is the operator's S0b and S3 runs over the real archive and the real ref (Test Strategy), because AC-2.7 forbids real data in the suite. Nothing is reimplemented: the extractor is checked against `classify` on every report (D12).
- **Regression provenance; Both halves of a doc change**: no existing test is edited to pass. AC-6.2a replaces the command with a working one (`hmad-dispatch audit-cycle`, which parses `--surfaces`) in the same change, and its new test asserts the new path is present, not only that the old one is gone.
- **Project: skill self-containment**: complies. No skill imports another skill. The probe lives under `docs/`, not in a skill. The mutation spec's absolute interpreter path is test infrastructure under `h-mad/tests/`, with 11 committed precedents (9 `/opt/anaconda3/bin/python3` and 2 `/opt/anaconda3/bin/python3.11`). Residual: it binds the spec to this Mac, as those 11 already are.
- **Project: skill manifest integrity**: complies. SKILL.md frontmatter is untouched, and the text edits are D14's.

## Version History
- v1.0: Initial design draft (2026-10-19) from spec v1.5 (`2f7bf7ae`) and plan v1.3 (`ab3c9f32`). Settles every plan design obligation: probe modes and command lines, calibration directory layout and the smoke commit, export-root builder with the six-entry exclusion list, scan normaliser and reach check, git-plumbing branch commits with no checkout, ref and ancestry mechanics, the consumed-verdict member list with opposed fixture pairs, AC-3.4 whole-cycle stands rule, test modules and fixtures, and the mutation spec with its rows and its interpreter (`/opt/anaconda3/bin/python3.11`). Answers the six delta-review should-fixes. Readings at `3660aeeb`.
