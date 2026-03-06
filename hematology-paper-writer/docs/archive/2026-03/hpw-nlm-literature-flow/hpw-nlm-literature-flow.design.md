# Design: hpw-nlm-literature-flow

## Reference
Plan: `docs/01-plan/features/hpw-nlm-literature-flow.plan.md`

---

## 1. Data Schema

### 1.1 research_topic.json — `nlm` block

Added as a top-level key alongside `pico`, `study_type`, etc.

```json
{
  "pico": { "...": "..." },
  "nlm": {
    "notebook_id": "3f2a1c7e-...",
    "notebook_name": "HPW-AML-venetoclax-2026",
    "pmids_added": ["38234567", "37891234"],
    "last_synced": "2026-03-06T10:00:00"
  }
}
```

**Invariants**:
- `notebook_id` is `null` when NLM server was unreachable during Phase 1
- `pmids_added` contains only PMIDs of `selected=True` articles
- `last_synced` is an ISO-8601 UTC timestamp updated on every add operation
- `notebook_name` follows the pattern `HPW-{disease}-{intervention}-{YYYY}`

**Backward compatibility**: `load_project_topic()` wraps JSON in a `try/except KeyError`
so older files without the `nlm` key load without error; `nlm` defaults to `{}`.

---

## 2. Module: `tools/notebooklm_integration.py` — New Methods

All new methods follow the same fail-silent pattern as existing methods.

### 2.1 `list_notebooks() -> list[dict]`

```python
def list_notebooks(self, timeout: int = 5) -> list[dict]:
    """GET /api/notebooks → list of {id, name, description, ...}. Returns [] on failure."""
    if not _HAS_REQUESTS:
        return []
    try:
        resp = _requests.get(f"{self._base}/api/notebooks", timeout=timeout)
        resp.raise_for_status()
        return resp.json() if isinstance(resp.json(), list) else resp.json().get("notebooks", [])
    except Exception as exc:
        logger.debug("list_notebooks failed: %s", exc)
        return []
```

Note: `health_check()` already calls the same endpoint — `list_notebooks()` supersedes it
for callers that need the data. `health_check()` remains unchanged.

### 2.2 `find_by_name(prefix: str) -> Optional[dict]`

```python
def find_by_name(self, prefix: str) -> Optional[dict]:
    """Return first notebook whose name starts with `prefix`, case-insensitive. None if not found."""
    for nb in self.list_notebooks():
        if nb.get("name", "").lower().startswith(prefix.lower()):
            return nb
    return None
```

### 2.3 `get_notebook(notebook_id: str) -> Optional[dict]`

```python
def get_notebook(self, notebook_id: str, timeout: int = 5) -> Optional[dict]:
    """GET /api/notebooks/{id} → dict or None if 404/error."""
    if not _HAS_REQUESTS:
        return None
    try:
        resp = _requests.get(f"{self._base}/api/notebooks/{notebook_id}", timeout=timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.debug("get_notebook(%s) failed: %s", notebook_id, exc)
        return None
```

### 2.4 `add_source_pmid(notebook_id: str, pmid: str) -> bool`

```python
def add_source_pmid(self, notebook_id: str, pmid: str) -> bool:
    """Convenience wrapper: add PubMed article by PMID as a URL source."""
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    return self.add_source_url(notebook_id, url)
```

---

## 3. Module: `tools/nlm_query.py` (New File)

```python
"""
nlm_query.py — Phase-specific NotebookLM query helper.

Usage:
    context = query_for_phase("phase2", topic, notebook_id)
    # Returns NLM answer str, or "" with a logged warning if NLM offline.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phases.phase1_topic.topic_development import ResearchTopic

logger = logging.getLogger(__name__)

# ── Prompt templates ───────────────────────────────────────────────────────────
# {disease}, {intervention}, {comparator}, {outcome}, {section}, {year} are
# substituted from ResearchTopic fields.

_PROMPTS: dict[str, str] = {
    "phase2": (
        "{disease} {intervention} clinical trial study designs, primary and secondary endpoints, "
        "eligibility criteria, stratification factors, and response definitions used in published trials."
    ),
    "phase3": (
        "Publication impact and novelty arguments for {disease} {intervention}: "
        "key findings, knowledge gaps addressed, clinical significance, and suitable journal scope."
    ),
    "phase4_draft": (
        "Key results, statistics, hazard ratios, response rates, and comparative outcomes "
        "for {section} in {disease} {intervention} studies. Include specific numbers where available."
    ),
    "phase4_5": (
        "Most recent updates, new trial data, regulatory approvals, and guideline changes "
        "for {disease} {intervention} published since {year}."
    ),
    "phase4_7": (
        "Core claims and primary supporting evidence most cited in {disease} {intervention} literature. "
        "What are the landmark findings and how are they presented in published manuscripts?"
    ),
    "phase8": (
        "Common reviewer critiques, methodological concerns, and statistical objections raised in "
        "{disease} {intervention} manuscripts submitted to hematology journals."
    ),
    "phase9": (
        "Current consensus statements, clinical practice guidelines, and expert recommendations "
        "for {disease} {intervention} from major societies (ELN, NCCN, ASH, ESMO)."
    ),
}


def query_for_phase(
    phase: str,
    topic: "ResearchTopic",
    notebook_id: str,
    section: str = "",
    year: str = "2023",
    timeout: int = 10,
) -> str:
    """
    Query the project NLM notebook with a phase-specific prompt.

    Parameters
    ----------
    phase       : One of the keys in _PROMPTS (e.g. "phase2", "phase4_draft").
    topic       : ResearchTopic instance providing disease/intervention/etc.
    notebook_id : Project NLM notebook ID from research_topic.json.nlm.notebook_id.
    section     : Manuscript section name (used only for "phase4_draft").
    year        : Cutoff year for "phase4_5" recent-updates prompt.
    timeout     : HTTP timeout for the NLM ask() call.

    Returns
    -------
    str
        NLM answer text, or "" if NLM is unavailable or prompt key is unknown.
        Caller must handle empty string as "no context available".
    """
    from tools.notebooklm_integration import NotebookLMIntegration

    template = _PROMPTS.get(phase)
    if not template:
        logger.warning("query_for_phase: unknown phase key '%s'", phase)
        return ""

    prompt = template.format(
        disease=getattr(topic, "disease_entity", "") or "",
        intervention=getattr(topic.pico, "intervention", "") if hasattr(topic, "pico") else "",
        comparator=getattr(topic.pico, "comparator", "") if hasattr(topic, "pico") else "",
        outcome=getattr(topic.pico, "outcome", "") if hasattr(topic, "pico") else "",
        section=section,
        year=year,
    )

    nlm = NotebookLMIntegration()
    if not nlm.health_check():
        logger.warning(
            "NLM server unavailable — no literature context for %s. "
            "Ensure open-notebook is running at http://localhost:5055.",
            phase,
        )
        return ""

    answer = nlm.ask(prompt, notebook_id=notebook_id, timeout=timeout)
    if not answer:
        logger.warning("NLM returned empty answer for phase '%s'", phase)
    return answer
```

---

## 4. Phase 1 — Notebook Resolution Logic

### 4.1 `integrate_skills_phase1()` — Resolution Flow

Replace the existing Step 3 (create notebook) with this resolution function:

```python
def _resolve_project_notebook(
    nlm: NotebookLMIntegration,
    topic: ResearchTopic,
    project_dir: Path,
    ask_user_fn,          # callable(prompt: str) -> str  (CLI input or UI widget)
) -> Optional[str]:
    """
    Resolve or create the project NLM notebook. Returns notebook_id or None.

    Resolution order:
    1. Existing notebook_id in research_topic.json → verify alive → reuse
    2. Name-pattern search → user confirmation → adopt
    3. Create new notebook
    """
    import datetime

    # Step 1: check persisted notebook_id
    saved = TopicDevelopmentManager.load_project_topic(project_dir)
    if saved:
        existing_id = (saved.get("nlm") or {}).get("notebook_id")
        if existing_id and nlm.get_notebook(existing_id):
            logger.info("Reusing existing NLM notebook: %s", existing_id)
            return existing_id

    # Step 2: name-pattern search
    disease = topic.disease_entity or ""
    intervention = getattr(topic.pico, "intervention", "") if hasattr(topic, "pico") else ""
    prefix = f"HPW-{disease}-{intervention}"
    found = nlm.find_by_name(prefix)
    if found:
        answer = ask_user_fn(
            f"Found NLM note '{found['name']}'. Use it? [y/N]: "
        ).strip().lower()
        if answer in ("y", "yes"):
            return found["id"]

    # Step 3: create new
    year = datetime.datetime.utcnow().year
    name = f"HPW-{disease}-{intervention}-{year}"
    notebook_id = nlm.create_notebook(
        name=name,
        description=f"Literature for HPW project: {disease} / {intervention}",
    )
    return notebook_id
```

### 4.2 `save_project_topic()` — NLM Block Persistence

Add `nlm` merge logic:

```python
def save_project_topic(self, project_dir, nlm_block: dict = None) -> Path:
    # ... existing serialization ...
    data = { ...existing fields... }
    if nlm_block:
        data["nlm"] = nlm_block
    elif "nlm" in existing_data:          # preserve existing nlm block
        data["nlm"] = existing_data["nlm"]
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return out
```

### 4.3 `load_project_topic()` — NLM Block Loading

```python
@classmethod
def load_project_topic(cls, project_dir) -> Optional[dict]:
    path = Path(project_dir) / "research_topic.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    # nlm block defaults to {} for backward compatibility
    data.setdefault("nlm", {})
    return data
```

Note: The return type changes from `Optional[ResearchTopic]` to `Optional[dict]` to allow
`nlm` passthrough. Phase 2's `StudyDesignManager.load_phase1_topic()` reconstructs
`ResearchTopic` from the dict as before.

---

## 5. Phase Integration Points

### 5.1 Integration Pattern (All Phases)

Each phase follows this pattern at its main entry point:

```python
from tools.nlm_query import query_for_phase

# Load project state
topic = load_phase1_topic(project_dir)        # ResearchTopic
nlm_block = load_project_topic(project_dir).get("nlm", {})
notebook_id = nlm_block.get("notebook_id", "")

# Query NLM
nlm_context = ""
if notebook_id:
    nlm_context = query_for_phase("phaseN", topic, notebook_id)
    if not nlm_context:
        warnings.append("NLM context unavailable — drafting without curated literature")
```

`nlm_context` is passed as an additional parameter or prepended to the system prompt
in the relevant drafter/manager method.

### 5.2 Per-Phase Integration Points

| Phase | Class | Method | How nlm_context is used |
|-------|-------|--------|------------------------|
| 2 | `StudyDesignManager` | `generate_methods_section()` | Prepended to the methods template as "Literature context" |
| 3 | `JournalStrategyManager` | `recommend_journal()` | Added to novelty/gap analysis prompt |
| 4 | `ResearchWorkflow` | `_draft_section(section)` | Prepended to section-level Claude prompt |
| 4.5 | `ManuscriptUpdater` | `update_manuscript()` | Used to identify gaps vs. new evidence |
| 4.7 | `ProseVerifier` | `verify_prose()` | Used to validate claims against literature |
| 8 | `PeerReviewManager` | `generate_responses()` | Used to pre-empt known reviewer concerns |
| 9 | `PublicationManager` | `finalize_manuscript()` | Used to align with current guidelines |

---

## 6. CLI: `hpw add-to-nlm`

### 6.1 Argparse Subcommand (in `cli.py`)

```python
add_nlm_parser = subparsers.add_parser(
    "add-to-nlm",
    help="Add a PubMed article to the project NLM notebook",
)
add_nlm_parser.add_argument("--pmid", required=True, help="PubMed ID to add")
add_nlm_parser.add_argument(
    "--project-dir",
    default=".",
    help="Project directory containing research_topic.json",
)
```

### 6.2 Handler Logic

```python
def cmd_add_to_nlm(args):
    from tools.notebooklm_integration import NotebookLMIntegration
    import json, datetime
    from pathlib import Path

    project_dir = Path(args.project_dir)
    topic_path = project_dir / "research_topic.json"
    if not topic_path.exists():
        print("ERROR: research_topic.json not found. Run Phase 1 first.")
        return 1

    data = json.loads(topic_path.read_text())
    nlm_block = data.get("nlm", {})
    notebook_id = nlm_block.get("notebook_id")
    if not notebook_id:
        print("ERROR: No NLM notebook linked. Run Phase 1 first.")
        return 1

    nlm = NotebookLMIntegration()
    ok = nlm.add_source_pmid(notebook_id, args.pmid)
    if ok:
        pmids = nlm_block.setdefault("pmids_added", [])
        if args.pmid not in pmids:
            pmids.append(args.pmid)
        nlm_block["last_synced"] = datetime.datetime.utcnow().isoformat()
        data["nlm"] = nlm_block
        topic_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"Added PMID {args.pmid} to notebook {notebook_id}")
        return 0
    else:
        print(f"ERROR: Failed to add PMID {args.pmid}. Is open-notebook running?")
        return 1
```

---

## 7. UI: "Add PMID to NLM" Widget (`ui/components/action_panel.py`)

Visible only when `st.session_state.get("current_phase", 1) >= 2` and `notebook_id` is set.

```python
def _render_add_pmid_widget(self):
    nlm_block = st.session_state.get("research_topic", {}).get("nlm", {})
    notebook_id = nlm_block.get("notebook_id")
    if not notebook_id:
        return  # Phase 1 not yet completed

    with st.expander("Add PMID to NLM Notebook"):
        pmid = st.text_input("PubMed ID", key="add_pmid_input", placeholder="e.g. 38234567")
        if st.button("Add to NLM", key="add_pmid_btn"):
            from tools.notebooklm_integration import NotebookLMIntegration
            import datetime, json
            from pathlib import Path

            nlm = NotebookLMIntegration()
            ok = nlm.add_source_pmid(notebook_id, pmid.strip())
            if ok:
                # Update session state + research_topic.json
                pmids = nlm_block.setdefault("pmids_added", [])
                if pmid not in pmids:
                    pmids.append(pmid)
                nlm_block["last_synced"] = datetime.datetime.utcnow().isoformat()
                st.session_state["research_topic"]["nlm"] = nlm_block
                # Persist to disk
                project_dir = Path(st.session_state.get("project_dir", "."))
                tp = project_dir / "research_topic.json"
                if tp.exists():
                    data = json.loads(tp.read_text())
                    data["nlm"] = nlm_block
                    tp.write_text(json.dumps(data, indent=2))
                st.success(f"PMID {pmid} added to NLM notebook.")
            else:
                st.warning("Failed to add PMID. Is open-notebook running at port 5055?")
```

---

## 8. Warning Display — NLM Offline

### CLI
```python
if not nlm_context:
    import sys
    print(
        f"[WARNING] NLM unavailable for {phase} — "
        "proceeding without curated literature context. "
        "Start open-notebook at http://localhost:5055 to enable.",
        file=sys.stderr,
    )
```

### UI (Streamlit)
Each phase panel calls:
```python
if not nlm_context:
    st.warning(
        "NLM notebook unavailable — literature context not loaded. "
        "Start open-notebook at http://localhost:5055."
    )
```

---

## 9. Implementation Order

```
Step 1 (foundation):
  tools/notebooklm_integration.py  — add list_notebooks, find_by_name, get_notebook, add_source_pmid
  tools/nlm_query.py               — new file (query_for_phase)

Step 2 (Phase 1 sync):
  phases/phase1_topic/topic_development.py  — _resolve_project_notebook, nlm block in save/load

Step 3 (Phase 2-9 integration, parallel):
  phases/phase2_research/study_design_manager.py
  phases/phase3_journal/journal_strategy_manager.py
  tools/draft_generator/research_workflow.py
  phases/phase4_5_updating/manuscript_updater.py
  phases/phase4_7_prose/prose_verifier.py
  phases/phase8_peerreview/peer_review_manager.py
  phases/phase9_publication/publication_manager.py

Step 4 (user-facing):
  cli.py                          — add-to-nlm subcommand
  ui/components/action_panel.py   — Add PMID widget
```

## 10. Status
- Phase: design
- Created: 2026-03-06
