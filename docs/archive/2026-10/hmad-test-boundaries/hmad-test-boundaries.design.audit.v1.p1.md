## Summary
The design covers the feature broadly, but its default project-root handling can bypass enforcement and its spec resolution can select the wrong file. The audit also found portability and operational-error gaps.

Evidence: 5 files opened, 3 greps run. 🌱 graft saved ~98,990 tokens this turn (1 call).

| Acceptance criteria | Classification |
|---|---|
| AC-1.1, AC-1.2 | implemented-as-written |
| AC-1.3 | restated |
| AC-2.1 | restated |
| AC-2.2, AC-2.3, AC-2.4 | implemented-as-written |
| AC-3.1, AC-3.2 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2, AC-4.3 | restated |
| AC-4.4, AC-5.1, AC-6.1, AC-6.2, AC-6.3 | implemented-as-written |

## Must-fix
- AC-4.2 and AC-4.3: the gate defaults activation to the skill checkout root rather than the project root, and passes no root to either the predicate or checker — a separately installed skill will skip a new canonical project design with no heading when its paired spec cannot activate arm 3, permitting a clean audit to pass. Derive and propagate the actual project root and test an installed skill against a separate project and a missing-section design.
  class: build
  quote: docs/02-design/features/hmad-test-boundaries.design.md › `Let effective_root = Path(root).resolve() if root is not None else REPO_ROOT.resolve()`
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › `<design_path> resides under docs/02-design/features/ (or docs/archive/)`
- AC-2.1: the workspace spec candidate uses `parents[2]`, which is the `docs` directory, producing `/work/project/docs/docs/01-plan/features/demo.spec.md` for `/work/project/docs/02-design/features/demo.design.md`. When invoked outside the project working directory without `--root`, a valid paired spec is missed or an unrelated cwd spec is selected; use the actual workspace root and test absolute paths from another cwd.
  class: build
  quote: docs/02-design/features/hmad-test-boundaries.design.md › `ws_cand = abs_design.parents[2] / "docs" / "01-plan" / "features" / f"{feature}.spec.md"`
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › `If <design_path> matches <root>/docs/02-design/features/<feature>.design.md (or relative docs/02-design/features/<feature>.design.md), resolve <root>/docs/01-plan/features/<feature>.spec.md.`
- AC-1.3: the prescribed author command hardcodes the Claude installation, narrowing the spec's skill-directory command and breaking Codex or agy installations and configured overrides. Resolve the actual skill location and test the host-independent instruction.
  class: build
  quote: docs/02-design/features/hmad-test-boundaries.design.md › `python3 ~/.claude/skills/h-mad/scripts/h_mad_test_boundaries_check.py docs/02-design/features/<feature>.design.md --spec docs/01-plan/features/<feature>.spec.md --root <PROJECT_ROOT>`
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › `python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py docs/02-design/features/<feature>.design.md --spec docs/01-plan/features/<feature>.spec.md`
- Activation arm 3 reads the paired spec without handling decoding or I/O errors — for an external candidate with no heading and a non-UTF-8 spec, the gate crashes before invoking the checker, so it emits neither the required UNREADABLE token nor a fail-closed GATE verdict. Route unreadable candidates to the checker and exercise this through the gate.
  class: build
  quote: docs/02-design/features/hmad-test-boundaries.design.md › `If spec_candidate.is_file(), reads spec_candidate as UTF-8, computes active_acs, _ = extract_spec_acs(spec_text), and returns len(active_acs) >= 1.`
- The new checker changes the skill's entry behavior but the design explicitly leaves the skill manifest unchanged — the project invariant requires the SKILL.md contract to reflect changed entry behavior. Update the manifest and verify its instructions agree with the implemented gate.
  class: build
  quote: docs/02-design/features/hmad-test-boundaries.design.md › `h-mad/SKILL.md frontmatter (name and description) is unchanged.`

## Should-fix
- The first self-bootstrap boundary row identifies a private test helper and the implementation's own required-sections constant as the oracle, while the proposed audit rubric rejects private-helper boundaries and implementation-derived expectations. Use public behavior and an independent bkit contract or fixture so the design satisfies its own semantic audit.
  class: build
  quote: docs/02-design/features/hmad-test-boundaries.design.md › `h-mad/tests/test_h_mad_doc_templates.py::_template_blocks`

## Nit
None
