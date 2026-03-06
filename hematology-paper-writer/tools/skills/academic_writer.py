"""
AcademicWriter — Scientific Skills Integration
Maps to: academic-research-writer OpenCode skill
HPW Phases: 4 (Manuscript Prep), 4.5 (Updating)

Transforms notes, outlines, and data summaries into formal academic prose
following hematology journal conventions.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_TRANSITION_PHRASES: dict[str, list[str]] = {
    "contrast": [
        "In contrast to these findings,",
        "Contrary to the anticipated outcome,",
        "These results differ from those of prior studies,",
    ],
    "addition": [
        "Consistent with these observations,",
        "Further supporting this interpretation,",
        "In line with these results,",
    ],
    "causation": [
        "These findings suggest that",
        "This observation may be attributable to",
        "A plausible mechanism for this effect is",
    ],
    "limitation": [
        "Several limitations of this analysis merit consideration.",
        "This study has important limitations that should be acknowledged.",
        "Interpretation of these results should be tempered by the following limitations.",
    ],
    "conclusion": [
        "Taken together, these findings demonstrate",
        "In conclusion, the present study establishes",
        "Collectively, these results support the conclusion that",
    ],
}

_ACADEMIC_VERB_UPGRADES: dict[str, str] = {
    "showed": "demonstrated",
    "found": "identified",
    "used": "employed",
    "did": "performed",
    "got": "achieved",
    "saw": "observed",
    "looked at": "evaluated",
    "checked": "assessed",
    "tried": "attempted",
    "said": "reported",
}

_PASSIVE_VOICE_TEMPLATES: dict[str, str] = {
    "we included": "were included",
    "we excluded": "were excluded",
    "we measured": "was measured",
    "we performed": "was performed",
    "we analyzed": "was analyzed",
    "we assessed": "was assessed",
    "we calculated": "was calculated",
}

_SECTION_CONNECTORS: dict[str, list[str]] = {
    "methods": [". ", ". In addition, ", ". Furthermore, "],
    "results": [". ", ". Additionally, ", ". Importantly, "],
    "discussion": [". ", ". These findings suggest that ", ". Moreover, "],
    "introduction": [". ", ". Furthermore, ", ". Notably, "],
}


class AcademicWriter(SkillBase):
    """
    Transforms notes and bullet points into academic prose.
    Upgrades informal language to academic register.
    Writes to context.draft_sections[section].
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[AcademicWriter] {prompt[:200]}"
        except Exception:
            return ""

    def transform_to_prose(
        self,
        notes: str,
        section: str = "results",
        style: str = "academic",
    ) -> str:
        """
        Transform bullet notes or outlines into academic prose.

        Args:
            notes: Raw notes, bullet points, or outline text
            section: IMRaD section — "introduction" | "methods" | "results" | "discussion"
            style: "academic" | "clinical"

        Returns:
            str: Transformed academic prose.
            Writes to context.draft_sections[section].
        """
        try:
            lines = [line.strip() for line in notes.split("\n") if line.strip()]
            prose_lines = []
            for line in lines:
                cleaned = line.lstrip("•-*·1234567890.)").strip()
                if not cleaned:
                    continue
                upgraded = self._upgrade_verbs(cleaned)
                if style == "academic" and section == "methods":
                    upgraded = self._apply_passive_voice(upgraded)
                prose_lines.append(upgraded)

            text = self._join_to_paragraph(prose_lines, section)
            self.context.draft_sections[section] = text
            self._log.info(
                "AcademicWriter.transform_to_prose: section='%s', %d chars",
                section, len(text),
            )
            return text
        except Exception as exc:
            self._log.warning("AcademicWriter.transform_to_prose failed: %s", exc)
            return ""

    def upgrade_language(self, text: str) -> str:
        """
        Upgrade informal language to academic register.

        Args:
            text: Manuscript text with informal language

        Returns:
            str: Text with upgraded academic vocabulary.
        """
        try:
            result = text
            for informal, formal in _ACADEMIC_VERB_UPGRADES.items():
                result = result.replace(informal, formal)
                result = result.replace(informal.capitalize(), formal.capitalize())
            return result
        except Exception as exc:
            self._log.warning("upgrade_language failed: %s", exc)
            return text

    def get_transition(self, transition_type: str) -> str:
        """
        Return a transition phrase for the given type.

        Args:
            transition_type: "contrast" | "addition" | "causation" | "limitation" | "conclusion"

        Returns:
            str: An academic transition phrase.
        """
        try:
            options = _TRANSITION_PHRASES.get(transition_type, [])
            if options:
                import random
                return random.choice(options)
            return ""
        except Exception as exc:
            self._log.warning("get_transition failed: %s", exc)
            return ""

    def check_passive_voice(self, text: str) -> dict:
        """
        Check methods section for active voice constructions that should be passive.

        Args:
            text: Methods section text

        Returns:
            dict with violations list and passed boolean.
        """
        try:
            findings = []
            for active, passive in _PASSIVE_VOICE_TEMPLATES.items():
                if active in text.lower():
                    findings.append({
                        "active": active,
                        "passive_suggestion": passive,
                    })
            return {
                "violations": len(findings),
                "findings": findings,
                "passed": len(findings) == 0,
            }
        except Exception as exc:
            self._log.warning("check_passive_voice failed: %s", exc)
            return {}

    # ── private helpers ──────────────────────────────────────────────────────

    def _upgrade_verbs(self, text: str) -> str:
        result = text
        for informal, formal in _ACADEMIC_VERB_UPGRADES.items():
            result = result.replace(informal, formal)
        return result

    def _apply_passive_voice(self, text: str) -> str:
        result = text
        for active, passive in _PASSIVE_VOICE_TEMPLATES.items():
            idx = result.lower().find(active)
            if idx != -1:
                result = result[:idx] + passive + result[idx + len(active):]
        return result

    def _join_to_paragraph(self, lines: list[str], section: str) -> str:
        if not lines:
            return ""
        if len(lines) == 1:
            sentence = lines[0]
            result = sentence if sentence.endswith(".") else sentence + "."
        else:
            connectors = _SECTION_CONNECTORS.get(section, [". "])
            result = lines[0]
            for i, line in enumerate(lines[1:], 1):
                connector = connectors[i % len(connectors)]
                if result.endswith("."):
                    result += " " + line
                else:
                    result += connector + line
            if not result.endswith("."):
                result += "."

        # Under-development guard: flag paragraphs below the 5-sentence floor
        sentence_count = result.count(". ") + result.count("? ") + result.count("! ") + (
            1 if result.endswith((".", "?", "!")) else 0
        )
        if sentence_count < 5:
            result += (
                " [EXPAND: paragraph has fewer than 5 sentences — "
                "add Evidence, Elaboration, and Link sentences per Medical PEEL structure.]"
            )
        return result
