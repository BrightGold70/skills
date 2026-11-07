# HemaSuite test writes to tracked files — census (read-only)

Repo: /Users/kimhawk/orca/HemaSuite (branch main). Read-only: git ls-files, grep, AST reads, file reads.
Background read: b7290f03c (filed), 520d3a1e1 (fixed: `finally` restores only when missing or bytes differ, plus mtime assertion).

## Coverage

- Test-path files listed by `git ls-files | grep -E '(^|/)(tests?/|test_[^/]*\.py$|conftest\.py$)'`, excluding the `graft/` mirror: **1569 .py files** scanned (AST), plus 544 non-.py test-path data files cross-checked by basename.
- Raw grep hits (write_text, write_bytes, open w/a, shutil copy/move, os.replace/rename, json.dump, unlink, restore, checkout): **2458 hits in 571 files**. 233 hits were on lines naming tmp_path/tmp/tempfile, leaving 2225.
- AST write-call sites: **2853**. Split: 224 TMP (target expression names tmp_path/tmp*), 103 REPO-candidate (target name traced to `__file__`/`parents[`/ROOT/REPO/fixture/docs anchors), 2525 unresolved by static name trace (mostly `fixture.path`, `case.labels`, function-parameter `path`), 1 file not AST-parsed under the system python3 (`hematology-paper-writer/tests/test_reference_pdf_eligibility.py`, f-string backslash; grep-scanned only).
- `finally:` blocks containing a write, unlink, copy, or git call: **3 sites, all in one test** (`test_citation_fidelity_backtest.py:482-484`).
- Module-level writes: 1 (`capture_journal_golden.py:63`, under `__main__`).
- Cross-check: every literal `docs/`, `tests/fixtures`, `tests/data`, `baselines`, or `schemas/` path in a write call across the 1569 files resolves under tmp_path (`test_h_mad_do_preconditions.py`, 9 lines).
- Residual gap: the 2525 unresolved write sites were not dispositioned one by one. Their targets are fixture- or parameter-supplied; I checked the fixture roots for the sites that matter (the list below), not each one. A helper that receives a repo path from a fixture would show up here and would not be caught by name tracing.

Candidate sites dispositioned: 13 rows below (10 test sites, 3 generator scripts). Generators are not run by pytest.

## Counts

| label | count |
|---|---|
| UNCONDITIONAL_RESTORE | 0 |
| CONDITIONAL_RESTORE | 2 |
| WRITES_TRACKED_NO_RESTORE | 3 |
| NOT_TRACKED | 7 |
| UNCLEAR | 1 |

## Table

| item | label | evidence |
|---|---|---|
| hematology-paper-writer/tests/test_citation_fidelity_backtest.py:482 | CONDITIONAL_RESTORE | `hematology-paper-writer/tests/test_citation_fidelity_backtest.py:482 › \`COMMITTED_SIDECAR.unlink(missing_ok=True)\`` under `if not existed:` (line 481). Target tracked: `git ls-files --error-unmatch docs/03-analysis/probes/citation-fidelity-judge/backtest_citation_fidelity.out.md` succeeds. Unlinks only when the file was absent before the run. |
| hematology-paper-writer/tests/test_citation_fidelity_backtest.py:484 | CONDITIONAL_RESTORE | `hematology-paper-writer/tests/test_citation_fidelity_backtest.py:483 › \`elif not COMMITTED_SIDECAR.exists() or COMMITTED_SIDECAR.read_bytes() != before:\``; `:484 › \`COMMITTED_SIDECAR.write_bytes(before)  # restore only what the run changed\``. This is the 520d3a1e1 fix: the write is guarded by a byte comparison. The mtime assertion is at `:489-493`. Target tracked (same `ls-files` check). |
| hematology-paper-writer/tests/test_citation_fidelity_backtest.py:496 | NOT_TRACKED | `hematology-paper-writer/tests/test_citation_fidelity_backtest.py:494 › \`path = tmp_path / "operator.out.md"\``; `:496 › \`path.write_bytes(before)\``. Target under tmp_path. |
| hematology-paper-writer/tests/data/capture_journal_golden.py:63 | WRITES_TRACKED_NO_RESTORE | `hematology-paper-writer/tests/data/capture_journal_golden.py:63 › \`_OUT.write_text(json.dumps(snap, indent=2, sort_keys=True))\`` under `if __name__ == "__main__":` (`:61`). `_OUT` is `tests/data/journal_resolution_golden.json` (`:17`), tracked. Manual regeneration only; no test imports or calls it to write. |
| hematology-paper-writer/tests/fixtures/_build_frontmatter_synopsis.py:41 | WRITES_TRACKED_NO_RESTORE | `hematology-paper-writer/tests/fixtures/_build_frontmatter_synopsis.py:41 › \`doc.save(OUT)\``; `:8-9 › \`ROOT = Path(__file__).resolve().parent\`, \`OUT = ROOT / "frontmatter_synopsis.docx"\``. Target tracked: `git ls-files --error-unmatch hematology-paper-writer/tests/fixtures/frontmatter_synopsis.docx` succeeds. Called only under `__main__` (`:45-46`); `test_frontmatter_synopsis_parity.py` loads the module and only asserts `DOCX_PATH.exists()`. |
| hematology-paper-writer/tests/fixtures/guideline_web_evidence/build_fixtures.py:88 | WRITES_TRACKED_NO_RESTORE | `hematology-paper-writer/tests/fixtures/guideline_web_evidence/build_fixtures.py:88 › \`destination.write_bytes(content)\``; `:84 › \`root = Path(__file__).parent if root is None else root\``. Default root is the tracked fixture dir (a.pdf and build_fixtures.py are tracked). Called only under `__main__` (`:91-92`). `test_guideline_evidence_e2e.py:36-38` loads the module and reads constants; it does not call `build_fixtures()`. |
| hematology-paper-writer/tests/test_r_api_real_packages.py:50 | NOT_TRACKED | `hematology-paper-writer/tests/test_r_api_real_packages.py:50 › \`CACHE_ROOT.mkdir(parents=True, exist_ok=True)\``; `:33 › \`CACHE_ROOT = Path(__file__).parent / "fixtures" / "r_api_real_cache"\``. Gitignored: `hematology-paper-writer/.gitignore:15 › \`tests/fixtures/r_api_real_cache/\``; zero tracked files under it. |
| clinical-statistics-analyzer/tests/test_parse_rd_schema.py:107 | NOT_TRACKED | `clinical-statistics-analyzer/tests/test_parse_rd_schema.py:105 › \`out = tmp_path / "out"\``; `:107 › \`(out / 'stats.json').write_bytes(SENTINEL)\``. tmp_path. Same for `:110` and `:330`. |
| hematology-paper-writer/tests/test_section_scope.py:938 | NOT_TRACKED | `hematology-paper-writer/tests/test_section_scope.py:937 › \`legacy = _write_scope_file(store, "06_references")\``; `:942 › \`canonical.write_text(canonical.read_text(encoding='utf-8') + '\n## 7. References\n', encoding='utf-8')\``. `store` is built under tmp_path in the same test (`:928`, `:915`). |
| hematology-paper-writer/tests/test_evidence_labels.py:736 | NOT_TRACKED | `hematology-paper-writer/tests/test_evidence_labels.py:736 › \`path.write_text(saved, encoding='utf-8')\``; `:725-726 › \`def test_recovery_hash_mismatch_incomplete(tmp_path, source):\`, \`root, cfj, entry, _ = _fixture(tmp_path, source=...)\``. Restores the saved text, unconditionally, but the target is under tmp_path. Not a repo write. |
| clinical-statistics-analyzer/tests/test_guideline_snapshot_provider.py:75 | NOT_TRACKED | `clinical-statistics-analyzer/tests/test_guideline_snapshot_provider.py:70 › \`hpw_root = tmp_path / "hpw"\``; `:72 › \`manifest.write_text(\`` (path under hpw_root). tmp_path. |
| hematology-paper-writer/tests/test_citation_fidelity_rerun.py:609 | UNCLEAR | `hematology-paper-writer/tests/test_citation_fidelity_rerun.py:603 › \`path = warm.paths[0]\``; `:609 › \`path.write_bytes(path.read_bytes().swapcase())\``. Target is a warm-cache file from `_warmed` → `_warm(monkeypatch, rig.case, ...)`; `make_case` (`:61`) builds its dataset under tmp_path (`:66`). I did not trace `_warm` to its cache root, so tracked status is not verified. Not a restore (no finally). |
| hematology-paper-writer/tests/test_citation_fidelity_rerun.py:888 | NOT_TRACKED | Read-only (`read_replay_record`). Excluded from write counts; listed because it names a tracked docs path: `hematology-paper-writer/tests/test_citation_fidelity_rerun.py:888 › \`path = (Path(__file__).resolve().parents[2] / "docs/03-analysis/probes"\``. |

Other sites checked and not carried into the table: `test_evidence_shadow_session.py` writes (`target` under `_scratch_repo`, a fresh git repo under tmp_path); `test_script_select_fr8_order.py:97-115` and `test_class_calibration_origination_check.py:62` run `git checkout` in throwaway repos built under tmp_path; `test_parse_rd_schema.py:309-330` (tmp `out`).

## Answer summary

- UNCONDITIONAL_RESTORE: **0**. The only tracked-file restore in the suite (test_citation_fidelity_backtest.py:484) is already conditional.
- WRITES_TRACKED_NO_RESTORE: **3**, all manual `__main__` generators, none run by pytest:
  - `hematology-paper-writer/tests/data/capture_journal_golden.py:63`
  - `hematology-paper-writer/tests/fixtures/_build_frontmatter_synopsis.py:41`
  - `hematology-paper-writer/tests/fixtures/guideline_web_evidence/build_fixtures.py:88`
- CONDITIONAL_RESTORE: 2 (the citation-fidelity fix, `:482` and `:484`).
- NOT_TRACKED: 7. UNCLEAR: 1 (`test_citation_fidelity_rerun.py:609`).

Method caveat: the scan was static. Unresolved write sites (2525) are not individually dispositioned. The table is the set of sites that the anchor trace and the tracked-file cross-check could place near a repo path.
