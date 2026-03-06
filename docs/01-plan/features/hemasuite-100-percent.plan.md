# Plan: HemaSuite 100% Gap Match Rate

> **Feature**: hemasuite-macos-app (gap remediation)
> **Current Match Rate**: 85% (30 PASS, 4 PARTIAL, 4 MISSING)
> **Target Match Rate**: 100%
> **Created**: 2026-03-06

---

## Gap Inventory

### PARTIAL Items (4 items, each +1.25% when fixed)

| # | Item | Current State | Effort |
|---|------|--------------|--------|
| P1 | CRF Pipeline Monitor (#13) | Placeholder text only | Medium |
| P2 | Zustand Store (#22) | Package installed, no store | Small |
| P3 | Universal Binary (#32) | Not configured in build | Small |
| P4 | HPW-CSA Integration (#40) | Separate views, no auto-insert | Large |

### MISSING Items (4 items, each +2.5% when fixed)

| # | Item | Current State | Effort |
|---|------|--------------|--------|
| M1 | Document Editor (#24) | No editor component | Medium |
| M2 | Charts/Visualization (#25) | Raw text output only | Medium |
| M3 | E2E Tests - Playwright (#38) | No config or tests | Medium |
| M4 | Tauri Integration Tests (#39) | No Rust-level tests | Small |

---

## Implementation Plan (6 Phases, TDD)

### Phase A: Quick Wins (+3.75%) — Target: 88.75%

**A1. Zustand Store (P2)**
- Install: already in package.json
- Create `src/stores/projectStore.ts` with Zustand store
  - State: activeProject, activePhase, activeTab
  - Actions: setProject, setPhase, setTab
- Test: `src/stores/projectStore.test.ts`
- Wire into MainLayout.tsx (replace local useState)
- Estimate: ~30 min

**A2. Universal Binary (P3)**
- Add `--target universal-apple-darwin` flag to `scripts/build-and-sign.sh`
- Update `BUILD.md` with universal binary instructions
- Test: update `test_build_workflow.py` to verify universal target flag
- Estimate: ~15 min

**A3. Tauri Integration Tests (M4)**
- Create `src-tauri/src/tests.rs` with `#[cfg(test)]` module
- Test sidecar path resolution logic
- Test menu item creation
- Test resource path resolution
- Estimate: ~30 min

### Phase B: Pipeline Monitor (+1.25%) — Target: 90%

**B1. CRF Pipeline Monitor View (P1)**
- Create `src/views/PipelineMonitor.tsx`
  - Step-by-step progress display (Extract -> Validate -> Analyze -> Report)
  - Wire to existing `/csa/run` endpoint for pipeline execution
  - Show step status (pending/running/done/error)
- Test: `src/views/PipelineMonitor.test.tsx`
- Update MainLayout.tsx to render PipelineMonitor instead of placeholder
- Estimate: ~1 hr

### Phase C: Visualization (+2.5%) — Target: 92.5%

**C1. Charts Library (M2)**
- Install `recharts` (lighter than plotly, React-native)
- Create `src/components/Chart.tsx` wrapper
  - Support KM curve (LineChart)
  - Support Forest plot (BarChart with error bars)
- Update `CsaDashboard.tsx` to parse R JSON output and render charts
- Test: `src/components/Chart.test.tsx`
- Estimate: ~1.5 hr

### Phase D: Document Editor (+2.5%) — Target: 95%

**D1. TipTap Editor (M1)**
- Install `@tiptap/react`, `@tiptap/starter-kit`, `@tiptap/extension-table`
- Create `src/components/Editor.tsx` with TipTap instance
  - Toolbar: bold, italic, headings, tables, lists
  - Content: load/save manuscript sections
- Update `HpwEditor.tsx` to include Editor for each phase's manuscript content
- Test: `src/components/Editor.test.tsx`
- Estimate: ~2 hr

### Phase E: HPW-CSA Integration (+1.25%) — Target: 96.25%

**E1. Auto-Insert Workflow (P4)**
- Backend: Add `POST /hpw/insert-results` endpoint in `routers/hpw.py`
  - Reads CSA output files (tables/figures)
  - Inserts into HPW manuscript at designated placeholders
  - Returns updated manuscript content
- Frontend: Add "Insert CSA Results" button in HpwEditor
  - Calls insert-results API
  - Updates editor content with inserted tables/figures
- Test: `tests/test_hpw_integration.py`, `src/views/HpwEditor.test.tsx`
- Estimate: ~2 hr

### Phase F: E2E Tests (+2.5%) — Target: 98.75%+

**F1. Playwright E2E (M3)**
- Install `@playwright/test`
- Create `e2e/` directory with config
- Tests:
  - `e2e/navigation.spec.ts` — sidebar nav, tab switching
  - `e2e/hpw-editor.spec.ts` — load phases, editor interaction
  - `e2e/csa-dashboard.spec.ts` — script list, run button
  - `e2e/project-manager.spec.ts` — create/open/delete project
- Note: Tauri WebView requires `@playwright/test` with custom WebView connection
- Estimate: ~2 hr

---

## Phase Summary

| Phase | Items | Score Gain | Cumulative | Effort |
|-------|-------|-----------|------------|--------|
| A | P2, P3, M4 | +3.75% | 88.75% | ~1.25 hr |
| B | P1 | +1.25% | 90.0% | ~1 hr |
| C | M2 | +2.5% | 92.5% | ~1.5 hr |
| D | M1 | +2.5% | 95.0% | ~2 hr |
| E | P4 | +1.25% | 96.25% | ~2 hr |
| F | M3 | +2.5% | 98.75%+ | ~2 hr |

**Total estimated effort: ~10 hours**

---

## Dependencies

```
Phase A (no deps) ──┐
Phase B (no deps) ──┼── Phase E (needs B + D)
Phase C (no deps) ──┤
Phase D (no deps) ──┘
Phase F (needs all views)
```

Phases A-D are independent and can run in parallel.
Phase E requires Pipeline Monitor (B) and Editor (D).
Phase F (E2E) should run last as it tests all views.

---

## TDD Approach

Each phase follows Red-Green-Refactor:
1. Write failing test for the gap item
2. Implement minimum code to pass
3. Refactor and verify all tests pass
4. Run gap analysis to confirm score improvement

---

## Success Criteria

- [ ] All 40 design requirements show PASS status
- [ ] Match rate >= 98% (allowing minor interpretation differences)
- [ ] All existing tests continue to pass (27 Vitest + 21 pytest)
- [ ] `pnpm build` succeeds with zero errors
- [ ] New tests added for every new component/endpoint

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| TipTap bundle size bloat | Medium | Use starter-kit only, lazy-load editor |
| Playwright + Tauri WebView compat | Medium | May need tauri-driver; fallback to component tests |
| R JSON output parsing for charts | Low | Define strict JSON schema in CSA scripts |
| Universal binary build time | Low | Only for release builds; dev stays native arch |
