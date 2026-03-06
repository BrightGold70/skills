"""
ContentResearcher — Scientific Skills Integration
Maps to: literature-review OpenCode skill
HPW Phases: 1 (Topic), 3 (Journal Strategy)

Performs structured literature synthesis and gap analysis
for hematology manuscripts.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_LITERATURE_SECTIONS: dict[str, list[str]] = {
    "introduction_background": [
        "Epidemiology and disease burden",
        "Pathophysiology and molecular landscape",
        "Current standard of care",
        "Limitations of existing therapy",
        "Rationale for the proposed approach",
    ],
    "discussion_context": [
        "Comparison with landmark trials",
        "Consistency with mechanistic rationale",
        "Discordance with conflicting studies",
        "Contribution to evidence base",
        "Clinical translation implications",
    ],
}


class ContentResearcher(SkillBase):
    """
    Synthesizes literature and identifies research gaps for manuscript writing.
    Writes to context.research_gaps.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ContentResearcher] {prompt[:200]}"
        except Exception:
            return ""

    def identify_gaps(
        self,
        topic: str,
        disease: str = "",
        existing_evidence: str = "",
    ) -> list[str]:
        """
        Identify research gaps for a given topic.

        Args:
            topic: Research topic
            disease: Disease context (aml, cml, mds, hct)
            existing_evidence: Brief summary of known literature

        Returns:
            list[str]: Identified research gaps.
            Extends context.research_gaps.
        """
        try:
            gaps: list[str] = [
                f"Prospective randomized data for {topic} remain limited.",
                f"Long-term outcomes beyond 2 years for {topic} are not well characterized.",
                f"Patient-reported outcomes for {topic} have not been systematically evaluated.",
            ]

            if disease:
                gaps.append(
                    f"Subgroup analyses in high-risk {disease.upper()} patients are underrepresented."
                )

            evidence_lower = existing_evidence.lower()
            if "retrospective" in evidence_lower and "prospective" not in evidence_lower:
                gaps.append("Prospective validation of retrospective findings is needed.")
            if "single center" in evidence_lower or "single-center" in evidence_lower:
                gaps.append("Multi-center validation is required to confirm generalizability.")
            if "phase 1" in evidence_lower and "phase 2" not in evidence_lower:
                gaps.append("Phase 2 efficacy data are lacking to confirm the observed activity.")

            self.context.research_gaps.extend(gaps)
            self._log.info(
                "ContentResearcher.identify_gaps: topic='%s', %d gaps identified",
                topic, len(gaps),
            )
            return gaps
        except Exception as exc:
            self._log.warning("ContentResearcher.identify_gaps failed: %s", exc)
            return []

    def synthesize_literature(
        self,
        articles: list[dict],
        synthesis_type: str = "narrative",
    ) -> str:
        """
        Synthesize a list of articles into a narrative summary.

        Args:
            articles: List of article dicts with keys: title, authors, year, abstract
            synthesis_type: "narrative" | "chronological" | "thematic"

        Returns:
            str: Literature synthesis paragraph.
        """
        try:
            if not articles:
                return ""

            if synthesis_type == "chronological":
                sorted_articles: list[dict] = sorted(
                    articles, key=lambda a: a.get("year", 0)
                )
            else:
                sorted_articles = articles

            sentences = []
            for article in sorted_articles[:10]:
                title = article.get("title", "")
                year = article.get("year", "")
                authors_list = article.get("authors", [""])
                first_author = authors_list[0] if authors_list else ""
                abstract = article.get("abstract", "")
                if abstract:
                    summary = abstract[:150].rstrip() + "..."
                    sentences.append(
                        f"{first_author} et al. ({year}) reported that {summary}"
                    )
                elif title:
                    sentences.append(
                        f"{first_author} et al. ({year}) described {title.lower()}."
                    )

            synthesis = " ".join(sentences)
            self._log.info(
                "ContentResearcher.synthesize_literature: %d articles → %d chars",
                len(articles), len(synthesis),
            )
            return synthesis
        except Exception as exc:
            self._log.warning("ContentResearcher.synthesize_literature failed: %s", exc)
            return ""

    def get_section_outline(self, section: str) -> list[str]:
        """
        Return a structured outline for a manuscript section.

        Args:
            section: "introduction_background" | "discussion_context"

        Returns:
            list[str]: Outline points for the section.
        """
        try:
            return list(_LITERATURE_SECTIONS.get(section, []))
        except Exception:
            return []
