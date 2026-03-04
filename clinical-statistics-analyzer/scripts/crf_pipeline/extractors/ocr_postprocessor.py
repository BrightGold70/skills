"""OCR text cleanup from config-driven rules with optional LLM correction."""

import json
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

OCR_CORRECTION_PROMPT = """You are a clinical data OCR correction specialist. The following text was
extracted via OCR from a Korean/English hematological clinical trial CRF (Case Report Form).
The OCR output contains errors from scanning. Correct the text while preserving:

1. Medical terminology (e.g., AML, FLT3-ITD, NPM1, CEBPA, WBC, Hb, PLT)
2. Korean text (환자명, 진단일, 등록번호, etc.)
3. Numeric values (lab results, dates, patient IDs)
4. Field labels and their associations with values

Rules:
- Fix garbled characters (e.g., "0" misread as "O" in numbers, "1" as "l" in numbers)
- Preserve intentional Korean characters — do NOT convert Korean to ASCII
- Fix broken date formats (e.g., "2O24-O3-15" → "2024-03-15")
- Fix broken lab values (e.g., "WBC: 1O.5" → "WBC: 10.5")
- Do NOT add, remove, or rearrange content — only fix character-level OCR errors

Return ONLY the corrected text, nothing else."""


class OCRPostprocessor:
    """OCR text cleanup using configurable rules with optional LLM correction."""

    def __init__(self, cleanup_rules: Dict,
                 use_llm: bool = False,
                 llm_client=None,
                 llm_model: str = "claude-sonnet-4-5-20250514",
                 llm_max_chars: int = 8000):
        self.remove_chars = cleanup_rules.get("remove_chars", [])
        self.replace_pairs = cleanup_rules.get("replace_pairs", [])
        self.normalize_whitespace = cleanup_rules.get("normalize_whitespace", True)
        self.use_llm = use_llm
        self._llm_client = llm_client
        self.llm_model = llm_model
        self.llm_max_chars = llm_max_chars

    def clean(self, text: str) -> str:
        """Apply OCR noise correction.

        1. Remove noise characters
        2. Apply character substitution pairs (O->0, l->1, etc.)
        3. Normalize whitespace
        4. (Optional) LLM-assisted correction for remaining errors
        """
        # Stage 1: Rule-based cleanup
        text = self._rule_based_clean(text)

        # Stage 2: LLM-assisted correction (if enabled)
        if self.use_llm and self._llm_client is not None:
            text = self._llm_correct(text)

        return text

    def _rule_based_clean(self, text: str) -> str:
        """Apply rule-based OCR cleanup."""
        for char in self.remove_chars:
            text = text.replace(char, "")

        for pair in self.replace_pairs:
            if len(pair) == 2:
                text = text.replace(pair[0], pair[1])

        if self.normalize_whitespace:
            text = re.sub(r"\s+", " ", text).strip()

        return text

    def _llm_correct(self, text: str) -> str:
        """Use Claude API to correct remaining OCR errors.

        Processes text in chunks to stay within token limits.
        Only applied when rule-based cleanup leaves potential errors.
        """
        if not self._has_likely_errors(text):
            return text

        try:
            corrected_chunks = []
            for chunk in self._chunk_text(text, self.llm_max_chars):
                corrected = self._correct_chunk(chunk)
                corrected_chunks.append(corrected)
            return " ".join(corrected_chunks)
        except Exception as e:
            logger.warning("LLM OCR correction failed, using rule-based result: %s", e)
            return text

    def _correct_chunk(self, chunk: str) -> str:
        """Send a single text chunk to Claude for OCR correction."""
        response = self._llm_client.messages.create(
            model=self.llm_model,
            max_tokens=len(chunk) * 2,
            messages=[
                {"role": "user", "content": f"{OCR_CORRECTION_PROMPT}\n\n---\n\n{chunk}"}
            ],
        )
        return response.content[0].text.strip()

    def _has_likely_errors(self, text: str) -> bool:
        """Heuristic check for remaining OCR errors after rule-based cleanup.

        Returns True if text likely still contains OCR artifacts.
        """
        indicators = [
            # Mixed digits and letter-O/letter-l in numeric contexts
            re.search(r"\d[Ol]\d", text),
            # Broken date patterns
            re.search(r"\d{2}[Ol]\d-[Ol]\d-\d{2}", text),
            # Garbled Korean (incomplete Unicode sequences)
            re.search(r"[\uFFFD]", text),
            # Excessive consecutive consonants (unlikely in Korean or English)
            re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", text, re.IGNORECASE),
            # Numbers with unexpected letter insertions
            re.search(r"\d+[A-Za-z]\d+\.\d", text),
        ]
        return any(indicators)

    @staticmethod
    def _chunk_text(text: str, max_chars: int):
        """Split text into chunks at sentence boundaries."""
        if len(text) <= max_chars:
            yield text
            return

        sentences = re.split(r"(?<=[.!?\n])\s+", text)
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_chars and current_chunk:
                yield current_chunk
                current_chunk = sentence
            else:
                current_chunk = f"{current_chunk} {sentence}".strip() if current_chunk else sentence

        if current_chunk:
            yield current_chunk
