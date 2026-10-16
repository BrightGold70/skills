SPEC-AUTHOR: DONE version=v1.5 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=908 sha256=7324587ee97991fce3dc51063f427ebca69d81289d907d7fef771e569d8b9528

Starting state checked before the first write: sha 2f9991b2…, newest VH v1.4. Repo HEAD was 9c3b799d (the orchestrator's c2 reports commit); the spec bytes had not changed.

premises verified:
- h-mad/SKILL.md §"Teammate audit leg — when codex is unavailable": the bullet "- **It does not license Claude to write Phase 5 production code — but the declaration you just made does" is present (grep -n 'does not license Claude').
- h-mad/tests/test_h_mad_tdd_gate_docs.py: `_skill_gate_bullet` requires that anchor exactly once (count==1). `test_skill_gate_bullet_states_the_every_record_rule` requires the tokens ACTIVE/every/unavailable/exhausted. FR-10's rewrite keeps all of them.
- h_mad_assemble_tdd.py: the wiring header is inside `assemble()` under `if shape == "wiring":`, as two adjacent literals "...never a missing " + "symbol.". **The symbol `_format_wiring_pin_header` that the decision sheet names does not exist** (grep -rn over h-mad returns 0 hits). The spec locates the header by `assemble()` plus the shape branch instead.
- test_h_mad_assemble_tdd.py `TestWiringShape.test_the_pin_is_told_what_its_red_must_be` asserts "never a missing". `git ls-files h-mad | xargs grep -ln "never a missing"` returns 2 files: the assembler and that test.
- HemaSuite task commits, found with `git log --all --grep`: 531a6296b (T4), 7aa0d9dec (T5), c2d671f6b (T6). `git show --stat` for each:
  - T4 adds test_notebooklm_resolver.py.
  - T5 adds test_notebooklm_initialize.py.
  - T6 adds test_notebooklm_status_report.py (verified myself). T6 WIRE-PIN 2 is `test_status_entry_point_resolves_through_registry_arm` (impl-plan line `**WIRE-PIN 2**: tests/test_notebooklm_status_report.py::...`).
- Pin forms:
  - T4: `getattr(integration, "resolve_registry_notebook")`, the two-argument form, so its RED is AttributeError.
  - T5: `getattr(integration, "initialize_project_notebook", None)` plus `except (Exception, SystemExit)`.
  - T6: `getattr(integration.NotebookLMIntegration(), "generate_setup_report", None)` plus `except (Exception, SystemExit)`.
  - The impl-plan's §"WIRE-PIN RED scaffold" says these tasks' RED is the spy AssertionError. So the sheet's premise holds: old verdict = halt for T4 only.

findings applied:
- B: FR-10 has a new bullet for the SKILL.md teammate-audit bullet. It separates audit-leg selection (codex_status routes 5b) from resolved authorship. The new condition is that Claude authors only when FR-2 resolved=claude for every ACTIVE step5 record. The anchor prefix and the four pinned tokens are kept.
- C: FR-9's census now lists five rule surfaces, with the assembler header as surface 5, so the GREEN variant is the sixth copy. The header's carve-out is appended so that the literal `never a missing` survives. A third pin was added (the TestWiringShape test).
  - Census method: Python str constants are joined through ast (adjacent literals), and non-.py text is whitespace-collapsed. This was run at 9c3b799d.
  - Residual, stated: strings built at run time (f-string fields, %/.format, + of names).
  - AC-9.1 now lists the header plus test_h_mad_assemble_tdd.py, and requires the sweep to be re-run on the shipped tree.
- D: FR-9's replay now has a table of the three pins with file::test and commit. A new paragraph covers the pin forms.
  - T5/T6 evaluate the direct-call / two-argument getattr form, with the scaffold removed and the spy assertion unchanged.
  - The committed scaffolded RED (AssertionError) is recorded with old verdict valid. This corrects the false claim old-verdict = halt.
  - The wire-cut uses the committed pin. AC-9.3 was rewritten to match.
- A: new AC-9.4. The six copies are bound to one authority: either a shared source or an equality test, plus a control that mutates any single copy, run once per copy. The plan names the mechanism. ACS count 18→19.

values swept:
- `grep -n -i 'four surfaces|fifth|sixth|five surfaces|test_notebooklm|old verdict|old rule|17d73037|direct-call|license|declaration you just|assemble_tdd'` over the whole spec, including tables and fences. No stale "four surfaces" is left. The only "fifth" left is the NameError corpus-case line, which is about corpus cases, not surfaces, and is correct. The corpus table's old-verdict column (synthetic cases) is unchanged and still correct.
- The census sha moved from 17d73037 to 9c3b799d inside FR-9 only. The other 17d73037 stamps (FR-3 at line ~212, the owed SessionStart grep) measure different things and were left alone.
- Fixture path: changed to `h-mad/tests/fixtures/codex-text-8-exec.log` after a precheck PATH advisory.

contradictions found:
- The decision sheet names `_format_wiring_pin_header`, which is not in the tree (see above). The plan author should not cite it.
- Measurement on the census: the line grep and the joined sweep return the same file set except h_mad_assemble_tdd.py. The failure-recovery row gives 3 collapsed-regex occurrences on 1 line (unit: occurrences, not lines).

placeholder scan: PRECHECK: PASS issues=0. There are 12 PATH advisories, all kept on purpose:
- new files: h-mad-agy-tdd-gate.py and .agents/.codex hooks.json;
- a HemaSuite-relative archive path under FR-9's stated checkout root.
ACS: OK count=19 frs=9. FR-10 has no AC; that was already true before this revision.

owed by other documents:
- PLAN stage 7 list: the SKILL.md teammate-audit bullet rewrite, keeping the `_skill_gate_bullet` anchor and the four tokens.
- PLAN census / stage 6:
  - surface 5 (the assembler header) and its pin;
  - the joined-literal sweep command and its residual;
  - six copies, not five, for DO-7 / A.
- PLAN stage 6: the T5/T6 direct-call replay, the record of the scaffolded RED, the three test files and commits.
- PLAN DO-7: the AC-9.4 mechanism (shared source or equality test) plus a per-copy mutation control.
- PLAN E (not spec-owned): the pins in test_h_mad_tdd_gate_docs.py and test_grok_fallback_docs.py.
- No probe files were created; the census sweep ran inline in a heredoc.
