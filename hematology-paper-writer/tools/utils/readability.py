"""Readability Metrics for Medical Writing."""

import re
from dataclasses import dataclass
from typing import Dict


@dataclass
class ReadabilityMetrics:
    flesch_kincaid_grade: float
    flesch_reading_ease: float
    avg_sentence_length: float
    avg_word_length: float
    complex_word_percentage: float
    score: int  # 0-100


class ReadabilityAnalyzer:
    """Calculates readability metrics for manuscripts."""

    def __init__(self):
        pass

    def analyze(self, text: str) -> ReadabilityMetrics:
        """Calculate readability metrics for text."""
        sentences = self._count_sentences(text)
        words = self._count_words(text)
        syllables = self._count_syllables(text)
        complex_words = self._count_complex_words(text)

        if sentences == 0 or words == 0:
            return ReadabilityMetrics(
                flesch_kincaid_grade=0,
                flesch_reading_ease=0,
                avg_sentence_length=0,
                avg_word_length=0,
                complex_word_percentage=0,
                score=0,
            )

        # Flesch Reading Ease
        avg_syllables_per_word = syllables / words
        avg_sentences_per_word = sentences / words
        flesch_reading_ease = 206.835 - (1.015 * (words / sentences)) - (84.6 * avg_syllables_per_word)

        # Flesch-Kincaid Grade
        flesch_kincaid_grade = (0.39 * (words / sentences)) + (11.8 * avg_syllables_per_word) - 15.59

        # Average sentence length
        avg_sentence_length = words / sentences

        # Average word length
        avg_word_length = sum(len(w) for w in text.split()) / words

        # Complex word percentage
        complex_percentage = (complex_words / words) * 100

        # Overall score (medical writing typically 30-50)
        score = max(0, min(100, int(flesch_reading_ease / 2 + 50)))

        return ReadabilityMetrics(
            flesch_kincaid_grade=round(flesch_kincaid_grade, 2),
            flesch_reading_ease=round(flesch_reading_ease, 2),
            avg_sentence_length=round(avg_sentence_length, 2),
            avg_word_length=round(avg_word_length, 2),
            complex_word_percentage=round(complex_percentage, 2),
            score=score,
        )

    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        sentences = re.split(r"[.!?]+", text)
        return len([s for s in sentences if s.strip()])

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len([w for w in text.split() if w.strip()])

    def _count_syllables(self, text: str) -> int:
        """Estimate syllable count."""
        words = text.split()
        total_syllables = 0
        for word in words:
            word = word.lower()
            # Count vowel groups
            syllables = len(re.findall(r"[aeiouy]+", word))
            # Subtract silent e
            if word.endswith("e") and syllables > 1:
                syllables -= 1
            # Ensure at least 1 syllable per word
            total_syllables += max(1, syllables)
        return total_syllables

    def _count_complex_words(self, text: str) -> int:
        """Count complex words (3+ syllables)."""
        words = text.split()
        complex_count = 0
        for word in words:
            word = word.lower()
            syllables = len(re.findall(r"[aeiouy]+", word))
            if word.endswith("e") and syllables > 1:
                syllables -= 1
            if syllables >= 3:
                complex_count += 1
        return complex_count
