# Design: hpw-ui-redesign

## Reference
- Plan: `docs/01-plan/features/hpw-ui-redesign.plan.md`
- Date: 2026-03-06

## Architecture Overview

All changes are **additive CSS injection + targeted component edits**. No new files created. The Streamlit rendering pipeline means CSS must be injected as the first `st.markdown()` call in `main()` before any widget renders.

```
app.py::main()
  ├── _inject_theme()          [NEW] — G-1: CSS injection
  ├── _init_session()          [unchanged]
  ├── _render_sidebar()        [modified] — G-6: reset confirm; delegates phase nav to PhasePanel
  │     └── ProjectTree.render_phase_stepper()  [NEW method] — G-3
  ├── _render_header()         [unchanged]
  └── st.tabs([5 tabs])        [modified] — G-2: flatten nested tabs
        ├── tab_manuscript: PhasePanel (CSABadge removed from here) — G-5
        ├── tab_documents: DocumentsTab
        ├── tab_pipeline: PipelineTab
        ├── tab_analysis: AnalysisTab
        └── tab_status: StatusDashboard(config=config)  — G-4: pass config
```

---

## G-1: CSS Injection Design

### Location
New private function `_inject_theme()` in `app.py`, called as **first line of `main()`**.

### Google Fonts
```python
FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=DM+Serif+Display&"
    "family=Source+Sans+3:wght@400;600&"
    "family=JetBrains+Mono:wght@400;500&"
    "display=swap"
)
```
Injected via:
```python
st.markdown(f'<link href="{FONTS_URL}" rel="stylesheet">', unsafe_allow_html=True)
```

### CSS Variable Palette
```css
:root {
  --hpw-navy:       #0a1628;
  --hpw-navy-mid:   #152342;
  --hpw-navy-light: #1e3356;
  --hpw-offwhite:   #f8f6f2;
  --hpw-white:      #ffffff;
  --hpw-red:        #c1121f;
  --hpw-red-dark:   #9b0e18;
  --hpw-text:       #1a1a2e;
  --hpw-muted:      #6b7280;
  --hpw-border:     #e5e0d8;
  --hpw-success:    #166534;
  --hpw-warn:       #92400e;
}
```

### Key CSS Selectors

**Sidebar:**
```css
section[data-testid="stSidebar"] {
  background-color: var(--hpw-navy);
  border-right: 1px solid var(--hpw-navy-light);
}
section[data-testid="stSidebar"] * {
  color: #e8e4dc !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  font-family: 'DM Serif Display', serif;
  color: #ffffff !important;
}
```

**Main area:**
```css
.main .block-container {
  background-color: var(--hpw-offwhite);
  font-family: 'Source Sans 3', sans-serif;
}
h1, h2, h3 {
  font-family: 'DM Serif Display', serif;
  color: var(--hpw-navy);
}
```

**Primary button (Run Phase):**
```css
div.stButton > button[kind="primary"] {
  background-color: var(--hpw-red) !important;
  border-color: var(--hpw-red) !important;
  color: white !important;
  font-family: 'Source Sans 3', sans-serif;
  font-weight: 600;
  letter-spacing: 0.03em;
}
div.stButton > button[kind="primary"]:hover {
  background-color: var(--hpw-red-dark) !important;
  border-color: var(--hpw-red-dark) !important;
}
```

**Log output (code block):**
```css
.stCode code, pre {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.78rem;
  line-height: 1.5;
}
```

**Status pills (for phase stepper badges):**
```css
.hpw-badge-completed { background:#dcfce7; color:#166534; padding:2px 8px; border-radius:12px; font-size:0.7rem; font-weight:600; }
.hpw-badge-in_progress { background:#fef9c3; color:#92400e; padding:2px 8px; border-radius:12px; font-size:0.7rem; font-weight:600; }
.hpw-badge-not_started { background:#f3f4f6; color:#6b7280; padding:2px 8px; border-radius:12px; font-size:0.7rem; font-weight:600; }
.hpw-badge-blocked { background:#fee2e2; color:#991b1b; padding:2px 8px; border-radius:12px; font-size:0.7rem; font-weight:600; }
```

---

## G-2: Tab Flattening Design

### Current (app.py:156–174)
```python
tab_manuscript, tab_csa, tab_status = st.tabs([
    "Manuscript Workflow", "Statistical Analysis", "Status"
])
with tab_csa:
    sub_docs, sub_pipeline, sub_analysis = st.tabs([...])  # nested!
```

### New
```python
tab_manuscript, tab_documents, tab_pipeline, tab_analysis, tab_status = st.tabs([
    "Manuscript", "Documents", "CRF Pipeline", "Analysis", "Status"
])
with tab_manuscript:
    PhasePanel().render(active_phase, active_project)
with tab_documents:
    DocumentsTab(active_project).render()
with tab_pipeline:
    PipelineTab(active_project).render()
with tab_analysis:
    AnalysisTab(active_project).render()
with tab_status:
    StatusDashboard(config=config).render()
```

Note: `CSABadge` removed from `tab_manuscript` top — see G-5.

---

## G-3: Phase Stepper Design

### New method: `ProjectTree.render_phase_stepper(active_phase: int, project_dir: str) -> int`

Called from `_render_sidebar()` instead of `st.selectbox`.

**Renders each phase as a clickable HTML row:**
```python
def render_phase_stepper(self, active_phase: int, project_dir: str) -> int:
    phase_status = self._read_phase_status(Path(project_dir))
    for phase_num, (icon, label) in _PHASE_LABELS.items():
        status = phase_status.get(phase_num, "not_started")
        is_active = phase_num == active_phase
        badge_class = f"hpw-badge-{status}"
        active_style = "background:#1e3356; border-radius:6px; padding:4px 6px;" if is_active else "padding:4px 6px;"
        st.markdown(
            f'<div style="{active_style}">'
            f'<span style="font-size:0.85rem;">{icon} {label}</span> '
            f'<span class="{badge_class}">{status.replace("_"," ")}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        if st.button("", key=f"phase_nav_{phase_num}", help=label):
            return phase_num
    return active_phase
```

**Signature change in `_render_sidebar()`:**
```python
# Remove:
phase_num = st.selectbox(...)
# Add:
tree = ProjectTree(config["hpw_base_dir"])
tree.render()
if active_project:
    active_phase = tree.render_phase_stepper(
        st.session_state.get("active_phase", 0),
        active_project
    )
    if active_phase != st.session_state.get("active_phase"):
        st.session_state["active_phase"] = active_phase
        st.rerun()
```

---

## G-4: StatusDashboard Cleanup Design

### Constructor signature change
```python
# Before:
class StatusDashboard:
    def render(self): ...

# After:
class StatusDashboard:
    def __init__(self, config: dict | None = None) -> None:
        self._config = config or {}

    def render(self) -> None: ...
```

### `_render_notebooklm_status` fix
```python
# Before (line 121):
ref_path = "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/References"

# After:
base_dir = self._config.get("hpw_base_dir", "")
ref_path = str(Path(base_dir) / "References") if base_dir else ""
```

### Remove entirely:
- `_render_activity_log()` method (lines 161–173)
- The `st.divider()` + `st.subheader("Recent Activity")` + `self._render_activity_log()` call in `render()`
- The progress slider block in `_render_phase_details()` (lines 101–116)

### Remove from `render()`:
```python
# Remove these 4 lines from render():
st.divider()
st.subheader("📝 Recent Activity")
self._render_activity_log()
```

---

## G-5: CSABadge Scoping Design

### In `app.py` — remove from tab_manuscript:
```python
# Remove:
CSABadge(csa_port=config.get("csa_port", 8502)).render(active_project)

# The import of CSABadge from components.csa_badge can also be removed from app.py
```

`CSABadge` is already instantiated inside `phase_panel.py:_render_csa_manifest_banner()` — no, actually checking phase_panel.py, it uses `st.success()` and `st.button()` directly, not `CSABadge`. The `CSABadge` class is only called in `app.py`.

**Revised approach**: Move the `CSABadge(…).render(active_project)` call into `PhasePanel.render()` guarded by `if phase_num == 4`:

```python
# In phase_panel.py::render(), after rendering the subheader:
if phase_num == 4:
    from .csa_badge import CSABadge
    CSABadge().render(project_dir)
```

Remove the call + import from `app.py`.

---

## G-6: Reset Confirmation Design

### In `_render_sidebar()`, replace the current reset button block:
```python
# Before (app.py:111-114):
if st.button("Reset session", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# After:
if not st.session_state.get("_confirm_reset"):
    if st.button("Reset session", use_container_width=True):
        st.session_state["_confirm_reset"] = True
        st.rerun()
else:
    st.warning("Clear all session data?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, reset", type="primary", use_container_width=True):
            keys = [k for k in st.session_state if k != "_confirm_reset"]
            for k in keys:
                del st.session_state[k]
            st.rerun()
    with col_no:
        if st.button("Cancel", use_container_width=True):
            st.session_state["_confirm_reset"] = False
            st.rerun()
```

---

## Implementation Checklist

- [ ] G-1: Add `_inject_theme()` to `app.py`; call as first line of `main()`
- [ ] G-1: Add Google Fonts `<link>` injection
- [ ] G-4: Add `__init__(self, config)` to `StatusDashboard`; fix `ref_path`
- [ ] G-4: Remove `_render_activity_log()` and slider from `StatusDashboard`
- [ ] G-6: Replace reset button with two-step confirmation in `_render_sidebar()`
- [ ] G-5: Remove `CSABadge` import/call from `app.py`; add to `phase_panel.py:render()` guarded by `phase_num == 4`
- [ ] G-2: Flatten `st.tabs()` to 5 top-level tabs in `app.py`
- [ ] G-3: Add `render_phase_stepper()` to `ProjectTree`; replace `st.selectbox` in `_render_sidebar()`
- [ ] G-4: Pass `config` to `StatusDashboard(config=config)` in `app.py`

## Risk Assessment

| Change | Risk | Rollback |
|--------|------|---------|
| CSS injection | Very Low — purely additive | Remove `_inject_theme()` call |
| Tab flattening | Low — same components, different nesting | Revert `st.tabs()` block |
| Phase stepper | Medium — replaces navigation control | Revert to `st.selectbox` |
| StatusDashboard cleanup | Low — removing unused code | Git revert |
| CSABadge move | Low — same logic, different call site | Move back to app.py |
| Reset confirmation | Very Low | Remove extra state check |
