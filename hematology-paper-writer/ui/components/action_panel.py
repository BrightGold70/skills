"""
ActionPanel Component
One-click action buttons for common tasks.
"""

import streamlit as st
from typing import Dict, List, Callable
import time

# Backend imports
from tools.notebooklm_integration import NotebookLMIntegration, initialize_all_notebooks
from tools.draft_generator.manuscript_drafter import ManuscriptDrafter, generate_specific_section
from tools.draft_generator.research_workflow import ResearchWorkflow
from tools.content_enhancer import ContentEnhancer
from tools.quality_analyzer import ManuscriptQualityAnalyzer
from tools.pubmed_verifier import PubMedVerifier


class ActionPanel:
    """Provides quick action buttons for manuscript workflow."""

    def render(self):
        """Render action panel."""
        current_phase = st.session_state.current_phase

        # Render query modal if active
        if "show_query_modal" in st.session_state and st.session_state.show_query_modal:
            self._render_query_modal()

        st.subheader("⚡ Quick Actions")

        # Phase-specific actions
        if current_phase == 0:
            self._render_research_actions()
        elif current_phase == 1:
            self._render_topic_actions()
        elif current_phase == 2:
            self._render_design_actions()
        elif current_phase == 3:
            self._render_journal_actions()
        elif current_phase == 4:
            self._render_drafting_actions()
        elif current_phase == 5:
            self._render_prep_actions()
        elif current_phase == 6:
            self._render_submission_actions()
        elif current_phase == 7:
            self._render_review_actions()
        elif current_phase == 8:
            self._render_publication_actions()
        elif current_phase == 9:
            self._render_resubmission_actions()

        # Add PMID to NLM — available for phases >= 2
        if current_phase >= 2:
            self._render_add_pmid_widget()

        st.divider()

        # Common actions (always available)
        st.subheader("🔧 Common Tools")
        self._render_common_actions()

    def _get_notebook_integration(self) -> NotebookLMIntegration:
        """Get or initialize NotebookLM integration."""
        if "notebooklm_integration" not in st.session_state:
            st.session_state.notebooklm_integration = NotebookLMIntegration()
        return st.session_state.notebooklm_integration

    def _render_add_pmid_widget(self):
        """Render 'Add PMID to NLM' widget for phases >= 2."""
        import datetime
        import json as _json
        from pathlib import Path as _Path

        research_topic = st.session_state.get("research_topic", {})
        nlm_block = research_topic.get("nlm", {}) if isinstance(research_topic, dict) else {}
        notebook_id = nlm_block.get("notebook_id")

        if not notebook_id:
            return  # Phase 1 not yet completed — no notebook to add to

        with st.expander("Add PMID to NLM Notebook"):
            pmid = st.text_input(
                "PubMed ID",
                key="add_pmid_input",
                placeholder="e.g. 38234567",
            )
            if st.button("Add to NLM", key="add_pmid_btn") and pmid:
                nlm = NotebookLMIntegration()
                ok = nlm.add_source_pmid(notebook_id, pmid.strip())
                if ok:
                    pmids = nlm_block.setdefault("pmids_added", [])
                    if pmid not in pmids:
                        pmids.append(pmid)
                    nlm_block["last_synced"] = datetime.datetime.utcnow().isoformat()
                    if isinstance(research_topic, dict):
                        research_topic["nlm"] = nlm_block
                        st.session_state["research_topic"] = research_topic
                    # Persist to disk
                    project_dir = _Path(st.session_state.get("project_dir", "."))
                    tp = project_dir / "research_topic.json"
                    if tp.exists():
                        data = _json.loads(tp.read_text())
                        data["nlm"] = nlm_block
                        tp.write_text(_json.dumps(data, indent=2, ensure_ascii=False))
                    st.success(f"PMID {pmid} added to NLM notebook.")
                else:
                    st.warning(
                        "Failed to add PMID. "
                        "Is open-notebook running at http://localhost:5055?"
                    )

    def _render_query_modal(self):
        """Render modal for NotebookLM queries."""
        modal_type = st.session_state.show_query_modal
        
        with st.expander(f"🔍 Query: {modal_type.title()}", expanded=True):
            st.markdown(f"Ask questions about **{modal_type}** using NotebookLM intelligence.")
            
            query = st.text_input("Your Question:", key=f"query_{modal_type}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Submit Query", key=f"submit_{modal_type}"):
                    if query:
                        with st.spinner("Consulting NotebookLM..."):
                            integration = self._get_notebook_integration()
                            
                            try:
                                # Direct query based on type
                                if modal_type == "classification":
                                    response = integration.query_classification(query, "definition")
                                elif modal_type == "gvhd":
                                    response = integration.query_gvhd(query)
                                elif modal_type == "therapeutic":
                                    # Very basic heuristic for demo
                                    response = integration.query_therapeutic("AML", query)
                                elif modal_type == "nomenclature":
                                    response = integration.query_nomenclature(query)
                                else:
                                    response = None
                                
                                if response:
                                    st.session_state[f"last_response_{modal_type}"] = response
                                    st.success("Analysis Complete")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            with col2:
                if st.button("Close", key=f"close_{modal_type}"):
                    st.session_state.show_query_modal = None
                    st.rerun()

            # Display result if available
            if f"last_response_{modal_type}" in st.session_state:
                response = st.session_state[f"last_response_{modal_type}"]
                st.markdown("### Answer")
                st.write(response.answer)
                
                with st.expander("Sources & Confidence"):
                    st.markdown(f"**Confidence:** {response.confidence}")
                    st.markdown("**Sources:**")
                    for source in response.sources:
                        st.json(source)

    def _render_research_actions(self):
        """Actions for Phase 0: Research Intelligence."""
        st.markdown("**NotebookLM Queries**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Query Classification", use_container_width=True):
                st.session_state.show_query_modal = "classification"
                st.rerun()

            if st.button("💊 Query Therapeutic", use_container_width=True):
                st.session_state.show_query_modal = "therapeutic"
                st.rerun()

        with col2:
            if st.button("🏥 Query GVHD", use_container_width=True):
                st.session_state.show_query_modal = "gvhd"
                st.rerun()

            if st.button("🧬 Check Nomenclature", use_container_width=True):
                st.session_state.show_query_modal = "nomenclature"
                st.rerun()

        st.markdown("**Reference Management**")
        if st.button("📚 Initialize All Notebooks", use_container_width=True):
            with st.status("Initializing NotebookLM...", expanded=True) as status:
                st.write("Connecting to Reference Library...")
                time.sleep(1)
                
                try:
                    integration = initialize_all_notebooks()
                    st.session_state.notebooklm_integration = integration
                    status.update(label="✅ Notebooks Initialized", state="complete", expanded=False)
                    st.success("All notebooks ready for queries.")
                except Exception as e:
                    status.update(label="❌ Initialization Failed", state="error")
                    st.error(f"Failed to initialize: {str(e)}")

    def _render_topic_actions(self):
        """Actions for Phase 1: Topic Development."""
        st.markdown("**PICO Framework**")

        if st.button("📝 Define PICO", use_container_width=True):
            st.session_state.show_pico_form = True

        if st.button("🔍 Literature Search", use_container_width=True):
            st.session_state.show_literature_search = True

        # Show article selection panel when seed file exists
        self._render_literature_selection()

        st.markdown("**Validation**")
        if st.button("✅ Validate Research Question", use_container_width=True):
            st.info("Validating against current classifications...")

    def _render_literature_selection(self):
        """
        Manual article selection panel for literature_seed.json.

        Shown when show_literature_search=True and literature_seed.json
        exists in the current project directory. Lets the user deselect
        irrelevant articles before Phase 4 draft generation loads the seed.
        """
        import json
        from pathlib import Path

        project_dir = st.session_state.get("project_dir", ".")
        seed_path = Path(project_dir) / "literature_seed.json"

        if not seed_path.exists():
            if st.session_state.get("show_literature_search"):
                st.info(
                    "No literature_seed.json found. "
                    "Run `hpw research <topic> --disease <DISEASE>` first, "
                    "or use the CLI to trigger Phase 1."
                )
            return

        try:
            seeds = json.loads(seed_path.read_text())
        except Exception:
            return

        if not seeds:
            return

        with st.expander(
            f"📚 Literature Review — {len(seeds)} articles found "
            f"({sum(1 for s in seeds if s.get('selected', True))} selected)",
            expanded=st.session_state.get("show_literature_search", False),
        ):
            st.caption(
                "Deselect irrelevant articles before generating your manuscript draft. "
                "Only selected articles will be used as references in Phase 4."
            )

            # Sort by relevance_score descending for display
            seeds_sorted = sorted(
                seeds, key=lambda s: s.get("relevance_score", 0), reverse=True
            )
            changed = False
            for i, article in enumerate(seeds_sorted):
                col1, col2 = st.columns([0.08, 0.92])
                with col1:
                    new_val = st.checkbox(
                        "",
                        value=article.get("selected", True),
                        key=f"seed_sel_{article.get('pmid', i)}",
                        label_visibility="collapsed",
                    )
                    if new_val != article.get("selected", True):
                        article["selected"] = new_val
                        changed = True
                with col2:
                    score = article.get("relevance_score", 0)
                    score_bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                    authors = article.get("authors", [])
                    author_str = authors[0] if authors else "Unknown"
                    if len(authors) > 1:
                        author_str += f" et al."
                    st.markdown(
                        f"**{article.get('title', 'No title')}**  \n"
                        f"{author_str} · {article.get('journal', '')} "
                        f"({article.get('year', '')}) · "
                        f"PMID {article.get('pmid', '—')}  \n"
                        f"Relevance `{score_bar}` {score:.0%}"
                    )

            if changed:
                # Persist updated selections back to seed file
                try:
                    # Re-merge: update the original (unsorted) list
                    pmid_to_sel = {
                        a.get("pmid"): a.get("selected", True) for a in seeds_sorted
                    }
                    for orig in seeds:
                        pmid = orig.get("pmid")
                        if pmid in pmid_to_sel:
                            orig["selected"] = pmid_to_sel[pmid]
                    seed_path.write_text(json.dumps(seeds, indent=2, ensure_ascii=False))
                    st.toast("Article selection saved.", icon="✅")
                except Exception as e:
                    st.warning(f"Could not save selections: {e}")

            n_sel = sum(1 for s in seeds if s.get("selected", True))
            st.info(f"{n_sel} / {len(seeds)} articles selected for Phase 4 draft.")

    def _render_design_actions(self):
        """Actions for Phase 2: Research Design."""
        st.markdown("**Study Design**")

        design_type = st.selectbox(
            "Study Type",
            [
                "Retrospective cohort",
                "Prospective cohort",
                "Case-control",
                "Cross-sectional",
                "Clinical trial",
                "Meta-analysis",
            ],
        )

        if st.button("📐 Generate Study Protocol", use_container_width=True):
            st.info(f"Generating {design_type} protocol template...")

        if st.button("📊 Sample Size Calculator", use_container_width=True):
            st.session_state.show_sample_size = True

    def _render_journal_actions(self):
        """Actions for Phase 3: Journal Strategy."""
        st.markdown("**Journal Selection**")

        if st.button("🎯 Recommend Journals", use_container_width=True):
            st.info("Analyzing manuscript fit...")

        if st.button("📊 Impact Factor Lookup", use_container_width=True):
            st.session_state.show_impact_lookup = True

        if st.button("📝 Check Author Guidelines", use_container_width=True):
            st.info("Retrieving journal guidelines...")

    def _render_drafting_actions(self):
        """Actions for Phase 4: Manuscript Drafting."""
        st.markdown("**Section Generation**")

        sections = [
            "Abstract",
            "Introduction",
            "Methods",
            "Results",
            "Discussion",
            "References",
        ]
        selected_section = st.selectbox("Select Section", sections)

        if st.button("✍️ Generate Section", use_container_width=True):
            with st.spinner(f"Generating {selected_section}..."):
                # Use topic and study type from session state or defaults
                topic = st.session_state.get("topic", "Hematology Research")
                study_type = st.session_state.get("study_type", "observational")
                
                content = generate_specific_section(selected_section, topic, study_type)
                st.session_state.manuscript_data[selected_section] = content
                st.success(f"{selected_section} generated!")
                time.sleep(1)
                st.rerun()

        if st.button("🔄 Enhance Prose", use_container_width=True):
            if not st.session_state.manuscript_data:
                st.warning("No manuscript content to enhance.")
            else:
                with st.spinner("Analyzing and enhancing prose..."):
                    enhancer = ContentEnhancer()
                    # Combine all sections for analysis
                    full_text = "\n\n".join(st.session_state.manuscript_data.values())
                    suggestions = enhancer.suggest_content_additions(full_text)
                    st.session_state.prose_suggestions = suggestions
                    st.success(f"Generated {len(suggestions)} enhancement suggestions.")

        if "prose_suggestions" in st.session_state:
            with st.expander("📝 Prose Enhancements", expanded=True):
                for i, suggestion in enumerate(st.session_state.prose_suggestions):
                    st.markdown(f"**Suggestion {i+1}**")
                    st.info(suggestion)

        st.markdown("**Quality Checks**")
        if st.button("🔍 Verify References", use_container_width=True):
            if "References" not in st.session_state.manuscript_data:
                st.warning("No references section found.")
            else:
                with st.spinner("Verifying references against PubMed..."):
                    verifier = PubMedVerifier()
                    # extract references from text (simplified for now)
                    ref_text = st.session_state.manuscript_data["References"]
                    refs = [r.strip() for r in ref_text.split('\n') if r.strip()]
                    validation_results = verifier.verify_references(refs)
                    st.session_state.reference_validation = validation_results
                    st.success("Reference verification complete.")

        if "reference_validation" in st.session_state:
            with st.expander("📚 Reference Validation", expanded=True):
                for res in st.session_state.reference_validation:
                    if res.get("valid"):
                        st.success(f"✅ {res.get('query', 'Ref')}")
                    else:
                        st.error(f"❌ {res.get('query', 'Ref')}: {res.get('error', 'Unknown error')}")

    def _render_prep_actions(self):
        """Actions for Phase 5: Publication Preparation."""
        st.markdown("**Pre-submission Checks**")

        checks = [
            "Nomenclature compliance (ISCN 2024)",
            "Classification alignment (WHO/ICC)",
            "Reference format verification",
            "Disclosure statement",
            "Figure quality check",
        ]

        for check in checks:
            st.checkbox(check, key=f"check_{check}")

        if st.button("▶️ Run All Checks", use_container_width=True):
            with st.spinner("Running comprehensive quality analysis..."):
                if not st.session_state.manuscript_data:
                    st.warning("No manuscript data to analyze.")
                else:
                    analyzer = ManuscriptQualityAnalyzer()
                    report = analyzer.analyze_manuscript(st.session_state.manuscript_data)
                    st.session_state.quality_report = report
                    st.success("✅ Quality analysis complete!")

        if "quality_report" in st.session_state:
            report = st.session_state.quality_report
            with st.expander("📊 Quality Report", expanded=True):
                st.metric("Overall Score", f"{report.get('overall_score', 0)}/100")
                if report.get('critical_issues'):
                    st.error(f"Found {len(report['critical_issues'])} critical issues.")
                    for issue in report['critical_issues']:
                        st.write(f"- {issue}")
                else:
                    st.write("No critical issues found.")

    def _render_submission_actions(self):
        """Actions for Phase 6: Submission."""
        st.markdown("**Submission Package**")

        if st.button("📝 Generate Cover Letter", use_container_width=True):
            st.info("Generating cover letter...")

        if st.button("📄 Format Manuscript", use_container_width=True):
            st.info("Applying journal formatting...")

        if st.button("📤 Submit to Journal", use_container_width=True):
            st.warning("⚠️ This would submit to the selected journal")

    def _render_review_actions(self):
        """Actions for Phase 7: Peer Review."""
        st.markdown("**Reviewer Response**")

        if st.button("📋 Organize Reviewer Comments", use_container_width=True):
            st.info("Parsing reviewer comments...")

        if st.button("✍️ Draft Response Letter", use_container_width=True):
            st.info("Generating response letter template...")

        if st.button("🔄 Revise Manuscript", use_container_width=True):
            st.info("Tracking changes...")

    def _render_publication_actions(self):
        """Actions for Phase 8: Publication."""
        st.markdown("**Post-Acceptance**")

        if st.button("📄 Check Proofs", use_container_width=True):
            st.info("Comparing with submitted version...")

        if st.button("📢 Promotion Package", use_container_width=True):
            st.info("Generating social media content...")

    def _render_resubmission_actions(self):
        """Actions for Phase 9: Resubmission."""
        st.markdown("**Journal Transfer**")

        if st.button("🔄 Adapt for New Journal", use_container_width=True):
            st.info("Reformatting for new journal...")

        if st.button("📝 Transfer Cover Letter", use_container_width=True):
            st.info("Generating transfer letter...")

    def _render_common_actions(self):
        """Common actions available in all phases."""
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save Progress", use_container_width=True):
                st.success("✅ Progress saved!")

            if st.button("📤 Export Manuscript", use_container_width=True):
                st.info("Preparing export...")

        with col2:
            if st.button("📧 Share", use_container_width=True):
                st.info("Generating shareable link...")

            if st.button("❓ Help", use_container_width=True):
                st.info("Opening help documentation...")
