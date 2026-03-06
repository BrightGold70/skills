# Design: HemaSuite 100% Gap Match Rate

> **Feature**: hemasuite-macos-app (gap remediation)
> **Plan Reference**: `docs/01-plan/features/hemasuite-100-percent.plan.md`
> **Created**: 2026-03-06

---

## 1. Architecture Overview

```
+-----------------------------------------------------------+
|  MainLayout.tsx                                           |
|  +-----------+  +---------------------------------------+ |
|  | Sidebar   |  | Tab Bar: Projects|HPW|CSA|Pipe|Settings| |
|  | (phases)  |  +---------------------------------------+ |
|  |           |  |                                       | |
|  |           |  |  Active View                          | |
|  |           |  |  - ProjectManager                     | |
|  |           |  |  - HpwEditor + TipTap Editor [NEW]    | |
|  |           |  |  - CsaDashboard + Recharts [NEW]      | |
|  |           |  |  - PipelineMonitor [NEW]               | |
|  |           |  |  - SettingsView                        | |
|  +-----------+  +---------------------------------------+ |
|                                                           |
|  Zustand Store (projectStore) [NEW]                       |
|  - activeProject, activeTab, activePhase                  |
+-----------------------------------------------------------+
         |  fetch()
         v
+-----------------------------------------------------------+
|  FastAPI Sidecar (:9720)                                  |
|  /hpw/phases, /hpw/search-pubmed                          |
|  /hpw/insert-results  [NEW]                               |
|  /csa/scripts, /csa/run                                   |
|  /csa/pipeline  [NEW]                                     |
|  /projects/*, /settings/*                                 |
+-----------------------------------------------------------+
```

---

## 2. Phase A: Quick Wins

### A1. Zustand Store

**File**: `src/stores/projectStore.ts`

```typescript
interface ProjectState {
  activeProject: string | null;
  activeTab: Tab;
  activePhase: number;
  setProject: (id: string | null) => ProjectState;
  setTab: (tab: Tab) => ProjectState;
  setPhase: (phase: number) => ProjectState;
}
```

**Design decisions**:
- Single store with flat state (no nesting) — matches Zustand v5 best practices
- Immutable updates via spread (aligns with project coding style)
- `Tab` type reused from existing `MainLayout.tsx` definition
- MainLayout.tsx replaces `useState` calls with `useProjectStore()` selectors

**Test**: `src/stores/projectStore.test.ts`
- Store initializes with defaults (null project, "hpw" tab, phase 0)
- setProject/setTab/setPhase update state correctly
- Selectors return individual slices

### A2. Universal Binary

**File**: `scripts/build-and-sign.sh` (modify)

Add `--target universal-apple-darwin` to the `pnpm tauri build` invocation:

```bash
TAURI_BUILD_TARGET="${TAURI_BUILD_TARGET:-universal-apple-darwin}"
pnpm tauri build --target "$TAURI_BUILD_TARGET"
```

- Environment variable override allows CI to build single-arch if needed
- Default: universal binary for release

**Test**: `src-tauri/sidecar/tests/test_build_workflow.py` — add assertion for `universal-apple-darwin` in script

### A3. Tauri Integration Tests

**File**: `src-tauri/src/tests.rs` (included via `#[cfg(test)] mod tests;` in lib.rs)

Tests:
1. `test_sidecar_python_path_resolution` — verifies `resolve_python()` logic for dev vs bundled paths
2. `test_menu_item_ids` — verifies all menu item IDs match the strings expected by frontend `useMenuEvents`
3. `test_resource_path_exists` — verifies sidecar scripts exist in expected locations

**Note**: These are unit-level Rust tests, not full integration tests. They test the logic functions extracted from `lib.rs` setup code.

---

## 3. Phase B: Pipeline Monitor

### B1. Backend: Pipeline Endpoint

**File**: `src-tauri/sidecar/routers/csa.py` (add endpoint)

```python
@router.post("/pipeline")
async def run_pipeline(req: RunPipelineRequest):
    """Run CRF pipeline: extract -> validate -> analyze -> report"""
```

**RunPipelineRequest**:
```python
class RunPipelineRequest(BaseModel):
    data_path: str        # Path to CRF data file (CSV/Excel)
    output_dir: str       # Output directory for results
    scripts: list[str] = []  # Optional: specific scripts to run (default: all)
```

**Response** (streaming via Server-Sent Events or sequential):
```python
class PipelineStepResult(BaseModel):
    step: str           # "extract" | "validate" | "analyze" | "report"
    status: str         # "running" | "done" | "error"
    exit_code: int | None
    output: str
    duration_ms: int
```

**Implementation**: Runs scripts sequentially using existing `run_script` logic. Returns list of step results. Each step maps to a CSA script pattern:
- extract: `01_*.R` or `01_*.py`
- validate: `02_*.R`
- analyze: `03_*.R` through `0N_*.R`
- report: last script in sequence

### B2. Frontend: PipelineMonitor View

**File**: `src/views/PipelineMonitor.tsx`

```
+-----------------------------------------------+
| CRF Pipeline Monitor                          |
+-----------------------------------------------+
| [Select Data File]  [Output Dir]  [Run]       |
+-----------------------------------------------+
| Step 1: Extract    [====] Done    0.8s        |
| Step 2: Validate   [====] Done    1.2s        |
| Step 3: Analyze    [==  ] Running...          |
| Step 4: Report     [    ] Pending             |
+-----------------------------------------------+
| Log Output:                                   |
| > Running 03_analysis.R ...                   |
| > Processing 142 records                      |
+-----------------------------------------------+
```

**State**:
```typescript
interface PipelineStep {
  step: string;
  status: "pending" | "running" | "done" | "error";
  output: string;
  durationMs: number | null;
}
```

**Behavior**:
- Calls `POST /csa/pipeline` with data path and output dir
- Renders 4 pipeline steps with progress indicators
- Shows log output in scrollable pre block (reuse CsaDashboard pattern)
- Error state shows stderr in red

**Test**: `src/views/PipelineMonitor.test.tsx`
- Renders step list with initial "pending" state
- Shows "running" state during API call
- Displays step results after completion
- Handles error state

---

## 4. Phase C: Charts / Visualization

### C1. Library Choice: Recharts

**Why Recharts over Plotly**:
- React-native (JSX components, not DOM manipulation)
- Lighter bundle (~45KB gzipped vs Plotly's ~1MB)
- Matches existing React component patterns
- Sufficient for KM curves and Forest plots

**Install**: `pnpm add recharts`

### C2. Chart Component

**File**: `src/components/ResultChart.tsx`

```typescript
interface ChartData {
  type: "km-curve" | "forest-plot" | "bar" | "line";
  title: string;
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
  series?: string[];  // for multi-line charts
}
```

**Supported chart types**:

| Type | Recharts Component | Use Case |
|------|-------------------|----------|
| `km-curve` | `<LineChart>` with step interpolation | Kaplan-Meier survival curves |
| `forest-plot` | `<BarChart>` + `<ErrorBar>` | Meta-analysis forest plots |
| `bar` | `<BarChart>` | Frequency distributions |
| `line` | `<LineChart>` | Time series, trends |

**Data flow**:
```
R script → stdout JSON → FastAPI → frontend → parse → ResultChart
```

R scripts output JSON when `CSA_OUTPUT_FORMAT=json` env var is set. The existing `run_script` endpoint already captures stdout. The frontend parses JSON from stdout and passes it to `ResultChart`.

### C3. CsaDashboard Integration

**File**: `src/views/CsaDashboard.tsx` (modify)

After running a script, attempt to parse stdout as JSON. If it contains a `chart` field, render `<ResultChart>`. Otherwise, fall back to the existing `<pre>` text display.

```typescript
// In CsaDashboard, after receiving result:
const chartData = tryParseChartData(result.stdout);
// If chartData exists, render <ResultChart data={chartData} />
// Otherwise, render existing <pre> block
```

**Test**: `src/components/ResultChart.test.tsx`
- Renders LineChart for km-curve type
- Renders BarChart for forest-plot type
- Handles empty data gracefully
- Displays title

---

## 5. Phase D: Document Editor (TipTap)

### D1. Library Choice: TipTap

**Why TipTap over Monaco**:
- TipTap = rich text (WYSIWYG) — matches manuscript editing use case
- Monaco = code editor — overkill for prose
- TipTap has table extension for clinical data tables
- Lighter weight for basic rich text

**Install**:
```bash
pnpm add @tiptap/react @tiptap/starter-kit @tiptap/extension-table \
         @tiptap/extension-table-row @tiptap/extension-table-cell \
         @tiptap/extension-table-header
```

### D2. Editor Component

**File**: `src/components/ManuscriptEditor.tsx`

```
+-----------------------------------------------+
| Toolbar: B I H1 H2 | Table | List | Undo Redo |
+-----------------------------------------------+
|                                               |
|  [Rich text editing area]                     |
|                                               |
|  Phase 4: Manuscript Drafting                 |
|  ─────────────────────────                    |
|  Introduction                                 |
|  Lorem ipsum dolor sit amet...                |
|                                               |
|  Methods                                      |
|  | Col1 | Col2 | Col3 |  <- table from CSA   |
|  | ...  | ...  | ...  |                       |
|                                               |
+-----------------------------------------------+
```

**Props**:
```typescript
interface ManuscriptEditorProps {
  content: string;          // HTML content to load
  onUpdate: (html: string) => void;  // Called on content change
  readOnly?: boolean;
}
```

**Extensions**:
- `StarterKit` (bold, italic, headings, lists, blockquote, code)
- `Table`, `TableRow`, `TableCell`, `TableHeader`

**Toolbar**: Minimal button bar with common formatting. Uses TipTap's chain commands:
```typescript
editor.chain().focus().toggleBold().run()
```

### D3. HpwEditor Integration

**File**: `src/views/HpwEditor.tsx` (modify)

Current: Shows phase cards (read-only grid).
New: Clicking a phase card opens `ManuscriptEditor` for that phase's content.

```typescript
// State addition:
const [editingPhase, setEditingPhase] = useState<number | null>(null);
const [content, setContent] = useState<string>("");

// When phase clicked: setEditingPhase(p.id), load content from project
// When editing: show <ManuscriptEditor content={content} onUpdate={setContent} />
// Back button: return to phase grid
```

**Content persistence**: Stored in project directory as `phase-{id}.html` files via existing `/projects` API (extend with file read/write).

### D4. Backend: Manuscript Content API

**File**: `src-tauri/sidecar/routers/hpw.py` (add endpoints)

```python
@router.get("/manuscript/{project_id}/{phase_id}")
async def get_manuscript(project_id: str, phase_id: int):
    """Read phase HTML content from project directory"""

@router.put("/manuscript/{project_id}/{phase_id}")
async def save_manuscript(project_id: str, phase_id: int, body: ManuscriptBody):
    """Save phase HTML content to project directory"""
```

**Test**: `src-tauri/sidecar/tests/test_hpw_manuscript.py`
- GET returns empty string for new phase
- PUT saves content, GET retrieves it
- Invalid project_id returns 404

**Test**: `src/components/ManuscriptEditor.test.tsx`
- Renders editor with initial content
- Toolbar buttons call TipTap commands
- onUpdate fires when content changes

---

## 6. Phase E: HPW-CSA Integration

### E1. Auto-Insert Workflow

**Design**: When user runs CSA analysis, results (tables/figures) can be auto-inserted into the HPW manuscript at the current cursor position or at designated `{{CSA_RESULT}}` placeholders.

**Backend endpoint**:

**File**: `src-tauri/sidecar/routers/hpw.py` (add endpoint)

```python
class InsertResultsRequest(BaseModel):
    project_id: str
    phase_id: int             # Target manuscript phase
    csa_output_dir: str       # Directory with CSA outputs
    insert_mode: str = "append"  # "append" | "placeholder" | "cursor"

@router.post("/insert-results")
async def insert_results(req: InsertResultsRequest):
    """Read CSA output files and insert into manuscript HTML"""
```

**Logic**:
1. Scan `csa_output_dir` for result files (`.html` tables, `.json` chart data, `.png` figures)
2. Convert to HTML snippets (tables stay as-is, charts become `<div data-chart='...'/>` placeholders, images become `<img src="data:..." />` base64)
3. Read current manuscript content
4. Insert based on mode:
   - `append`: Add at end of manuscript
   - `placeholder`: Replace `{{CSA_RESULT}}` markers
5. Return updated HTML

### E2. Frontend Integration

**File**: `src/views/HpwEditor.tsx` (modify)

Add "Insert CSA Results" button in the editor toolbar area:

```typescript
<button onClick={handleInsertResults}>
  Insert CSA Results
</button>
```

When clicked:
1. Calls `POST /hpw/insert-results` with current project, phase, and output dir
2. Updates editor content with returned HTML
3. Shows toast notification "N items inserted"

**Test**: `src/views/HpwEditor.test.tsx`
- "Insert CSA Results" button exists
- Clicking calls API with correct params
- Editor content updates after insert

---

## 7. Phase F: E2E Tests (Playwright)

### F1. Setup

**Install**: `pnpm add -D @playwright/test`

**Config**: `playwright.config.ts`
```typescript
export default defineConfig({
  testDir: './e2e',
  webServer: {
    command: 'pnpm dev',
    port: 1420,         // Vite dev server port
    reuseExistingServer: true,
  },
});
```

**Note**: E2E tests run against the Vite dev server (not the Tauri shell). This tests the React frontend in a browser context. Full Tauri E2E (with native menus, sidecar) would require `tauri-driver` and is out of scope for this phase.

### F2. Test Files

| File | Tests |
|------|-------|
| `e2e/navigation.spec.ts` | Tab switching, sidebar phase selection, URL state |
| `e2e/hpw-editor.spec.ts` | Phase card rendering, editor open/close, toolbar |
| `e2e/csa-dashboard.spec.ts` | Script list, run button, output display, chart render |
| `e2e/project-manager.spec.ts` | Create project, select project, delete project |

**Test patterns**:
- Use `page.getByRole()` and `page.getByText()` for accessibility-friendly selectors
- Mock API responses via `page.route()` to avoid needing live sidecar
- Each test file: 3-5 test cases covering happy path + error state

### F3. CI Integration

Add to `package.json` scripts:
```json
"test:e2e": "playwright test"
```

---

## 8. File Inventory

### New Files (13)

| File | Phase | Type |
|------|-------|------|
| `src/stores/projectStore.ts` | A | Store |
| `src/stores/projectStore.test.ts` | A | Test |
| `src-tauri/src/tests.rs` | A | Test (Rust) |
| `src/views/PipelineMonitor.tsx` | B | Component |
| `src/views/PipelineMonitor.test.tsx` | B | Test |
| `src/components/ResultChart.tsx` | C | Component |
| `src/components/ResultChart.test.tsx` | C | Test |
| `src/components/ManuscriptEditor.tsx` | D | Component |
| `src/components/ManuscriptEditor.test.tsx` | D | Test |
| `src-tauri/sidecar/tests/test_hpw_manuscript.py` | D | Test |
| `e2e/navigation.spec.ts` | F | E2E Test |
| `e2e/hpw-editor.spec.ts` | F | E2E Test |
| `e2e/csa-dashboard.spec.ts` | F | E2E Test |
| `e2e/project-manager.spec.ts` | F | E2E Test |
| `playwright.config.ts` | F | Config |

### Modified Files (7)

| File | Phase | Change |
|------|-------|--------|
| `src/layouts/MainLayout.tsx` | A, B | Use Zustand store, render PipelineMonitor |
| `src/views/HpwEditor.tsx` | D, E | Add editor + insert button |
| `src/views/CsaDashboard.tsx` | C | Add chart rendering |
| `src-tauri/sidecar/routers/csa.py` | B | Add `/pipeline` endpoint |
| `src-tauri/sidecar/routers/hpw.py` | D, E | Add manuscript + insert endpoints |
| `scripts/build-and-sign.sh` | A | Add universal binary target |
| `src-tauri/src/lib.rs` | A | Add `#[cfg(test)] mod tests;` |
| `package.json` | C, D, F | Add recharts, tiptap, playwright |

### Dependencies to Add

| Package | Phase | Size (gzipped) |
|---------|-------|----------------|
| `recharts` | C | ~45KB |
| `@tiptap/react` | D | ~15KB |
| `@tiptap/starter-kit` | D | ~20KB |
| `@tiptap/extension-table` | D | ~5KB |
| `@tiptap/extension-table-row` | D | ~2KB |
| `@tiptap/extension-table-cell` | D | ~2KB |
| `@tiptap/extension-table-header` | D | ~2KB |
| `@playwright/test` (dev) | F | N/A (dev only) |

Total new production bundle: ~91KB gzipped

---

## 9. Conventions

All new code follows existing patterns:
- **Components**: Functional React with hooks, Tailwind classes, typed props
- **API calls**: Use `api<T>()` from `hooks/useApi.ts`
- **Python routers**: FastAPI `APIRouter` with Pydantic models, async handlers
- **Tests (frontend)**: Vitest + React Testing Library + jsdom
- **Tests (python)**: pytest with httpx `AsyncClient`
- **State**: Zustand v5 with `create()` — immutable updates via spread
- **Naming**: PascalCase components, camelCase functions, snake_case Python

---

## 10. Gap-to-Design Traceability

| Gap # | Gap Item | Design Section | Files |
|-------|----------|---------------|-------|
| P1 | Pipeline Monitor | Section 3 (Phase B) | PipelineMonitor.tsx, csa.py |
| P2 | Zustand Store | Section 2 (Phase A1) | projectStore.ts, MainLayout.tsx |
| P3 | Universal Binary | Section 2 (Phase A2) | build-and-sign.sh |
| P4 | HPW-CSA Integration | Section 6 (Phase E) | hpw.py, HpwEditor.tsx |
| M1 | Document Editor | Section 5 (Phase D) | ManuscriptEditor.tsx, hpw.py |
| M2 | Charts/Visualization | Section 4 (Phase C) | ResultChart.tsx, CsaDashboard.tsx |
| M3 | E2E Tests | Section 7 (Phase F) | e2e/*.spec.ts, playwright.config.ts |
| M4 | Tauri Integration Tests | Section 2 (Phase A3) | tests.rs |

All 8 gap items (4 PARTIAL + 4 MISSING) are fully covered.
