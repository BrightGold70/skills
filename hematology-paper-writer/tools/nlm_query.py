"""
nlm_query.py — Phase-specific NotebookLM query helper.

Provides query_for_phase(), which builds a section/phase-targeted natural-language
prompt and queries the project NLM notebook via NotebookLMIntegration.ask().

Usage:
    from tools.nlm_query import query_for_phase
    context = query_for_phase("phase2", topic, notebook_id)
    # Returns NLM answer str, or "" with a logged warning if NLM offline.
"""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phases.phase1_topic.topic_development import ResearchTopic

logger = logging.getLogger(__name__)

# ── Prompt templates ──────────────────────────────────────────────────────────
# Placeholders: {disease}, {intervention}, {section}, {year}
# All are safe to leave blank if the topic lacks the field.

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
    phase       : Key in _PROMPTS — one of "phase2", "phase3", "phase4_draft",
                  "phase4_5", "phase4_7", "phase8", "phase9".
    topic       : ResearchTopic providing disease_entity and pico fields.
    notebook_id : Project NLM notebook ID from research_topic.json["nlm"]["notebook_id"].
    section     : Manuscript section label (used only for "phase4_draft" prompt).
    year        : Cutoff year string for the "phase4_5" recent-updates prompt.
    timeout     : HTTP timeout in seconds for the NLM ask() call.

    Returns
    -------
    str
        NLM answer text, or "" if NLM is unavailable, notebook_id is empty,
        or the phase key is unknown.  Caller should treat "" as "no context".
    """
    if not notebook_id:
        logger.debug("query_for_phase(%s): no notebook_id — skipping NLM query", phase)
        return ""

    template = _PROMPTS.get(phase)
    if not template:
        logger.warning("query_for_phase: unknown phase key '%s'", phase)
        return ""

    disease = getattr(topic, "disease_entity", "") or ""
    pico = getattr(topic, "pico", None)
    intervention = getattr(pico, "intervention", "") if pico else ""

    prompt = template.format(
        disease=disease,
        intervention=intervention,
        section=section,
        year=year,
    )

    try:
        from tools.notebooklm_integration import NotebookLMIntegration

        nlm = NotebookLMIntegration()
        if not nlm.health_check():
            _warn_nlm_offline(phase)
            return ""

        answer = nlm.ask(prompt, notebook_id=notebook_id, timeout=timeout)
        if not answer:
            logger.warning("query_for_phase(%s): NLM returned empty answer", phase)
        return answer

    except Exception as exc:  # noqa: BLE001
        logger.warning("query_for_phase(%s) error: %s", phase, exc)
        _warn_nlm_offline(phase)
        return ""


def load_context_for_phase(
    phase: str,
    project_dir,
    section: str = "",
    year: str = "2023",
) -> str:
    """
    Convenience wrapper: load ResearchTopic + nlm_block from ``project_dir``
    and call ``query_for_phase()``.  Returns "" on any error.

    Use this in phase managers that already have ``project_dir`` available:

        nlm_context = load_context_for_phase("phase2", project_dir)
    """
    try:
        from phases.phase1_topic.topic_development import TopicDevelopmentManager

        topic = TopicDevelopmentManager.load_project_topic(project_dir)
        if not topic:
            return ""
        nlm_block = TopicDevelopmentManager.load_nlm_block(project_dir)
        notebook_id = nlm_block.get("notebook_id", "")
        return query_for_phase(phase, topic, notebook_id, section=section, year=year)
    except Exception as exc:  # noqa: BLE001
        logger.debug("load_context_for_phase(%s) error: %s", phase, exc)
        return ""


def _warn_nlm_offline(phase: str) -> None:
    """Emit a user-visible stderr warning when NLM is unreachable."""
    msg = (
        f"[HPW WARNING] NLM server unavailable for {phase} — "
        "proceeding without curated literature context. "
        "Start open-notebook at http://localhost:5055 to enable NLM queries."
    )
    logger.warning(msg)
    print(msg, file=sys.stderr)
