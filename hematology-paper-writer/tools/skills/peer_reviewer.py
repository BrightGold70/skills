"""
PeerReviewer — Scientific Skills Integration
Maps to: peer-review OpenCode skill
HPW Phase: 8 (Peer Review)

Simulates a peer reviewer's perspective and generates constructive
reviewer-style comments for hematology manuscripts.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_COMMENT_TEMPLATES: dict[str, str] = {
    "major_concern": (
        "Major concern: {issue}. This significantly impacts the validity of the "
        "conclusions. The authors must {action} before this manuscript can be accepted."
    ),
    "minor_comment": (
        "Minor comment: {issue}. The authors should {action} to strengthen the manuscript."
    ),
    "clarification": (
        "The authors should clarify {issue}. Specifically, {action}."
    ),
    "suggestion": (
        "It would be helpful if the authors {action} regarding {issue}."
    ),
}

_REVIEW_CRITERIA: dict[str, list[str]] = {
    "novelty": [
        "Does this advance the field beyond existing literature?",
        "Is the research question original?",
        "Are the findings sufficiently distinct from prior publications?",
    ],
    "methodology": [
        "Is the study design appropriate for the research question?",
        "Are inclusion/exclusion criteria clearly defined?",
        "Is the statistical approach appropriate and pre-specified?",
        "Is the sample size adequate?",
    ],
    "results_reporting": [
        "Are results reported with appropriate precision (95% CI, p-values)?",
        "Are all pre-specified endpoints reported?",
        "Are negative/null results reported?",
        "Are adverse events adequately reported?",
    ],
    "discussion": [
        "Are findings contextualized against existing literature?",
        "Are limitations acknowledged honestly?",
        "Are conclusions supported by the data presented?",
        "Is the clinical implication clearly stated?",
    ],
    "writing_quality": [
        "Is the manuscript clearly written?",
        "Are abbreviations defined on first use?",
        "Is the nomenclature current (WHO 2022, HGVS 2024)?",
        "Do abstract figures match the main text?",
    ],
}


class PeerReviewer(SkillBase):
    """
    Simulates peer review and generates structured reviewer-style comments.
    Writes to context.review_comments.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[PeerReviewer] {prompt[:200]}"
        except Exception:
            return ""

    def review(
        self,
        text: str,
        journal: str = "",
        study_type: str = "cohort",
        criteria: list[str] | None = None,
    ) -> list[dict]:
        """
        Generate structured peer review comments for a manuscript.

        Args:
            text: Full manuscript text or section to review
            journal: Target journal name for scope-specific review
            study_type: rct | cohort | retrospective | case_series | systematic_review
            criteria: List of criteria to check; defaults to all

        Returns:
            list[dict]: Structured reviewer comments.
            Appends to context.review_comments.
        """
        try:
            active_criteria = criteria or list(_REVIEW_CRITERIA.keys())
            comments: list[dict] = []

            for criterion in active_criteria:
                if criterion in _REVIEW_CRITERIA:
                    comments.extend(self._check_criterion(text, criterion))

            if journal:
                comments.extend(self._check_journal_scope(text, journal))

            if comments:
                self.context.review_comments.extend(comments)

            self._log.info(
                "PeerReviewer.review: generated %d comments for journal='%s'",
                len(comments), journal,
            )
            return comments
        except Exception as exc:
            self._log.warning("PeerReviewer.review failed: %s", exc)
            return []

    def generate_response_points(
        self, comments: list[dict] | None = None
    ) -> list[str]:
        """
        Generate point-by-point response templates for reviewer comments.

        Args:
            comments: Reviewer comments to respond to; uses context if None

        Returns:
            list[str]: Response letter bullet points.
        """
        try:
            source = comments if comments is not None else self.context.review_comments
            if not source:
                return []
            responses = []
            for comment in source:
                priority = comment.get("priority", "minor")
                issue = comment.get("issue", "this point")
                if priority in ("critical", "major"):
                    responses.append(
                        f"We thank the reviewer for this important concern regarding {issue}. "
                        "We have revised the manuscript accordingly (see line [X])."
                    )
                else:
                    responses.append(
                        f"We appreciate this comment regarding {issue}. "
                        "The manuscript has been updated to address this point."
                    )
            return responses
        except Exception as exc:
            self._log.warning("generate_response_points failed: %s", exc)
            return []

    def summarize_review(self) -> dict:
        """
        Summarize all accumulated review comments.

        Returns:
            dict: counts by priority, criteria, and overall recommendation.
        """
        try:
            comments = self.context.review_comments
            summary: dict = {
                "total": len(comments),
                "by_priority": {},
                "by_criterion": {},
                "recommendation": "accept",
            }
            for c in comments:
                p = c.get("priority", "minor")
                summary["by_priority"][p] = summary["by_priority"].get(p, 0) + 1
                cr = c.get("criterion", "general")
                summary["by_criterion"][cr] = summary["by_criterion"].get(cr, 0) + 1

            critical = summary["by_priority"].get("critical", 0)
            major = summary["by_priority"].get("major", 0)
            if critical > 0:
                summary["recommendation"] = "reject"
            elif major > 2:
                summary["recommendation"] = "major_revision"
            elif major > 0:
                summary["recommendation"] = "minor_revision"
            return summary
        except Exception as exc:
            self._log.warning("summarize_review failed: %s", exc)
            return {}

    def get_criteria_questions(self, criterion: str = "all") -> list[str]:
        """Return review questions for a given criterion."""
        try:
            if criterion == "all":
                questions: list[str] = []
                for q_list in _REVIEW_CRITERIA.values():
                    questions.extend(q_list)
                return questions
            return list(_REVIEW_CRITERIA.get(criterion, []))
        except Exception:
            return []

    # ── private helpers ──────────────────────────────────────────────────────

    def _check_criterion(self, text: str, criterion: str) -> list[dict]:
        comments = []
        text_lower = text.lower()

        if criterion == "methodology":
            if "sample size" not in text_lower and "power calculation" not in text_lower:
                comments.append({
                    "criterion": criterion,
                    "priority": "major",
                    "issue": "sample size justification",
                    "text": _COMMENT_TEMPLATES["major_concern"].format(
                        issue="No sample size calculation or power analysis is presented",
                        action="provide a formal power calculation with assumptions",
                    ),
                })
            if "95% ci" not in text_lower and "confidence interval" not in text_lower:
                comments.append({
                    "criterion": criterion,
                    "priority": "minor",
                    "issue": "confidence intervals",
                    "text": _COMMENT_TEMPLATES["minor_comment"].format(
                        issue="Confidence intervals are not consistently reported",
                        action="report 95% CIs alongside all effect estimates and p-values",
                    ),
                })

        elif criterion == "writing_quality":
            if "who 2022" not in text_lower and "icc 2022" not in text_lower:
                comments.append({
                    "criterion": criterion,
                    "priority": "minor",
                    "issue": "classification system version",
                    "text": _COMMENT_TEMPLATES["clarification"].format(
                        issue="the disease classification system version",
                        action="specify whether WHO 2022 or ICC 2022 criteria were used",
                    ),
                })

        elif criterion == "discussion":
            if "limitation" not in text_lower:
                comments.append({
                    "criterion": criterion,
                    "priority": "major",
                    "issue": "limitations section",
                    "text": _COMMENT_TEMPLATES["major_concern"].format(
                        issue="No limitations section is present",
                        action="add a dedicated limitations paragraph",
                    ),
                })

        return comments

    def _check_journal_scope(self, text: str, journal: str) -> list[dict]:
        comments = []
        journal_lower = journal.lower()
        text_lower = text.lower()
        if "blood" in journal_lower and "clinical significance" not in text_lower:
            comments.append({
                "criterion": "journal_scope",
                "priority": "minor",
                "issue": "clinical significance statement",
                "text": _COMMENT_TEMPLATES["suggestion"].format(
                    action="explicitly state the clinical significance of the findings",
                    issue=f"{journal} scope requirements",
                ),
            })
        return comments
