# Plan: hpw-ui-redesign

## Feature Overview
**Feature**: HPW Web UI Redesign — Visual Theming + UX Structural Fixes
**Date**: 2026-03-06
**Priority**: Medium
**Scope**: `hematology-paper-writer/ui/` (all components)

## Problem Statement

The HPW Streamlit UI is functionally complete but has several issues:

1. **Zero visual identity** — pure vanilla Streamlit; no custom CSS, fonts, or colors
2. **Nested tabs anti-pattern** — Statistical Analysis tab contains 3 sub-tabs (UX dead-end)
3. **Phase navigation is a dropdown** — no visual progress signaling across 10 phases
4. **StatusDashboard has dead code** — hardcoded placeholder activity log, broken "Add Note" button
5. **Hardcoded Dropbox path** in `status_dashboard.py:121` bypasses `ui_config.json`
6. **CSABadge shown in all phases** — only relevant in Phase 4
7. **Destructive Reset button** — wipes session state with no confirmation
8. **Manual progress slider** in StatusDashboard conflicts with automated `update_phase_status()`

## Goals

### G-1: Visual Theming (CSS injection layer)
Inject a "Clinical Editorial" theme via `st.markdown("<style>...</style>")` in `app.py`:
- Deep navy sidebar (`#0a1628`) / clinical off-white main area (`#f8f6f2`)
- Blood-red accent (`#c1121f`) for primary buttons and active states
- Display font: `DM Serif Display` (Google Fonts) for phase headings
- Monospace: `JetBrains Mono` for log output in `log_stream.py`
- Body: `Source Sans 3` for form labels and captions
- Styled HTML status pills (colored `<span>`) replacing raw emoji badges

### G-2: Flatten Tab Structure
Remove nested sub-tabs inside Statistical Analysis. Promote to top-level tabs:
- Before: Manuscript Workflow | Statistical Analysis (Documents / CRF Pipeline / Analysis) | Status
- After: Manuscript | Documents | CRF Pipeline | Analysis | Status

### G-3: Phase Stepper Component
Replace `st.selectbox` in sidebar with a visual phase stepper:
- Vertical list showing all 10 phases
- Each phase shows: icon + name + status badge (completed/in-progress/not-started/blocked)
- Active phase is highlighted
- Clicking a phase row switches to it (replaces selectbox)

### G-4: StatusDashboard Cleanup
- Remove dead activity log and broken "Add Note" button
- Remove manual progress slider (conflicts with automated phase runner)
- Read `ref_path` from `config` passed as parameter, not hardcoded
- Retain: overall progress metrics (4 metric cards + progress bar), phase details, NotebookLM library status

### G-5: CSABadge Scoping
Move CSABadge render call inside `phase_panel.py:_render_csa_manifest_banner()` — already guarded by `if phase_num == 4`. Remove from `app.py` tab_manuscript top-level render.

### G-6: Reset Confirmation
Wrap "Reset session" button in a two-step confirmation:
```python
if st.button("Reset session"):
    st.session_state["_confirm_reset"] = True
if st.session_state.get("_confirm_reset"):
    st.warning("This will clear all session data.")
    if st.button("Confirm reset", type="primary"):
        # clear and rerun
```

## Out of Scope
- Changing any backend logic, CLI commands, or phase business logic
- Changing `phase_registry.json` structure
- Adding new features beyond what's listed in G-1 through G-6

## Files to Modify

| File | Changes | Goals |
|------|---------|-------|
| `ui/app.py` | CSS injection, tab flattening, reset confirmation, remove CSABadge from top | G-1, G-2, G-5, G-6 |
| `ui/components/project_tree.py` | Phase stepper render method | G-3 |
| `ui/components/status_dashboard.py` | Remove dead code, fix hardcoded path, remove slider | G-4 |
| `ui/components/csa_badge.py` | No change (already correct) | — |
| `ui/components/phase_panel.py` | Remove CSABadge top-level call (now in banner only) | G-5 |
| `ui/components/log_stream.py` | Apply JetBrains Mono to code output (CSS-driven) | G-1 |

## Success Criteria

- [ ] Custom CSS applied; sidebar navy, main area off-white, primary buttons red-accented
- [ ] Google Fonts loaded (DM Serif Display, Source Sans 3, JetBrains Mono)
- [ ] Top-level tab count is 5 (no nested sub-tabs)
- [ ] Sidebar shows visual phase stepper, not dropdown
- [ ] StatusDashboard has no hardcoded paths, no dead code, no manual slider
- [ ] CSABadge only appears when active phase == 4
- [ ] Reset button requires confirmation before clearing session

## Implementation Order
1. G-1 CSS injection (smallest risk, purely additive)
2. G-4 StatusDashboard cleanup (remove dead code)
3. G-6 Reset confirmation (small, targeted)
4. G-5 CSABadge scoping (move call site)
5. G-2 Tab flattening (structural change to app.py)
6. G-3 Phase stepper (replace selectbox in project_tree.py)
