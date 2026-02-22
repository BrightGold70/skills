from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class JournalCategory(Enum):
    GVHD = "gvhd"
    CLASSIFICATION = "classification"
    THERAPEUTIC = "therapeutic"
    TRANSPLANTATION = "transplantation"
    GENERAL_HEMATOLOGY = "general"


@dataclass
class Journal:
    name: str
    category: JournalCategory
    impact_factor: float = 0.0
    acceptance_rate: Optional[float] = None
    review_time_days: Optional[int] = None
    word_limit: int = 5000
    abstract_limit: int = 250
    reference_limit: int = 50
    features: List[str] = field(default_factory=list)
    scope_keywords: List[str] = field(default_factory=list)

    def matches_scope(self, keywords: List[str]) -> float:
        if not self.scope_keywords:
            return 0.0
        matches = sum(
            1
            for kw in keywords
            if any(
                sk.lower() in kw.lower() or kw.lower() in sk.lower()
                for sk in self.scope_keywords
            )
        )
        return matches / len(self.scope_keywords) if self.scope_keywords else 0.0


@dataclass
class JournalMatch:
    journal: Journal
    match_score: float
    relevance_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class JournalStrategyManager:
    HEMATOLOGY_JOURNALS = [
        Journal(
            name="Blood",
            category=JournalCategory.GENERAL_HEMATOLOGY,
            impact_factor=21.0,
            acceptance_rate=0.15,
            review_time_days=21,
            word_limit=5000,
            abstract_limit=200,
            reference_limit=60,
            features=["High impact", "Broad readership", "Rapid review"],
            scope_keywords=[
                "hematology",
                "leukemia",
                "lymphoma",
                "transplantation",
                "cell therapy",
            ],
        ),
        Journal(
            name="Blood Advances",
            category=JournalCategory.GENERAL_HEMATOLOGY,
            impact_factor=7.4,
            acceptance_rate=0.25,
            review_time_days=30,
            word_limit=6000,
            abstract_limit=250,
            reference_limit=50,
            features=["Open access", "Rapid publication", "Broad scope"],
            scope_keywords=["hematology", "clinical research", "laboratory research"],
        ),
        Journal(
            name="Bone Marrow Transplantation",
            category=JournalCategory.TRANSPLANTATION,
            impact_factor=5.2,
            acceptance_rate=0.30,
            review_time_days=35,
            word_limit=5000,
            abstract_limit=200,
            reference_limit=50,
            features=["HCT focused", "Clinical emphasis", "GVHD"],
            scope_keywords=[
                "transplantation",
                "GVHD",
                "stem cell",
                "graft-versus-host",
            ],
        ),
        Journal(
            name="Biology of Blood and Marrow Transplantation (BBMT)",
            category=JournalCategory.TRANSPLANTATION,
            impact_factor=4.4,
            acceptance_rate=0.35,
            review_time_days=40,
            word_limit=6000,
            abstract_limit=250,
            reference_limit=60,
            features=["ASTCT journal", "HCT focus", "Clinical trials"],
            scope_keywords=[
                "transplantation",
                "cellular therapy",
                "GVHD",
                "complications",
            ],
        ),
        Journal(
            name="Leukemia",
            category=JournalCategory.THERAPEUTIC,
            impact_factor=12.8,
            acceptance_rate=0.20,
            review_time_days=28,
            word_limit=5000,
            abstract_limit=200,
            reference_limit=60,
            features=["High impact", "Leukemia focus", "Molecular studies"],
            scope_keywords=["leukemia", "AML", "ALL", "CML", "molecular biology"],
        ),
        Journal(
            name="Haematologica",
            category=JournalCategory.GENERAL_HEMATOLOGY,
            impact_factor=10.1,
            acceptance_rate=0.18,
            review_time_days=25,
            word_limit=5000,
            abstract_limit=250,
            reference_limit=50,
            features=["EHA journal", "European focus", "Broad scope"],
            scope_keywords=["hematology", "clinical trials", "translational research"],
        ),
        Journal(
            name="British Journal of Haematology (BJH)",
            category=JournalCategory.GENERAL_HEMATOLOGY,
            impact_factor=6.5,
            acceptance_rate=0.28,
            review_time_days=30,
            word_limit=5000,
            abstract_limit=200,
            reference_limit=50,
            features=["BSH journal", "Practical focus", "Guidelines"],
            scope_keywords=["hematology", "clinical practice", "laboratory medicine"],
        ),
        Journal(
            name="American Journal of Hematology",
            category=JournalCategory.GENERAL_HEMATOLOGY,
            impact_factor=12.2,
            acceptance_rate=0.22,
            review_time_days=28,
            word_limit=4000,
            abstract_limit=200,
            reference_limit=50,
            features=["High impact", "Clinical emphasis", "Brief reports"],
            scope_keywords=["hematology", "clinical research", "translational"],
        ),
        Journal(
            name="Modern Pathology",
            category=JournalCategory.CLASSIFICATION,
            impact_factor=8.2,
            acceptance_rate=0.25,
            review_time_days=35,
            word_limit=6000,
            abstract_limit=250,
            reference_limit=60,
            features=["Pathology focus", "Morphology", "Molecular diagnostics"],
            scope_keywords=[
                "pathology",
                "hematopathology",
                "diagnostic",
                "classification",
            ],
        ),
        Journal(
            name="American Journal of Clinical Pathology (AJCP)",
            category=JournalCategory.CLASSIFICATION,
            impact_factor=5.7,
            acceptance_rate=0.30,
            review_time_days=40,
            word_limit=5000,
            abstract_limit=200,
            reference_limit=50,
            features=["Clinical pathology", "Validation studies", "Laboratory"],
            scope_keywords=["pathology", "laboratory medicine", "diagnostic testing"],
        ),
    ]

    def __init__(self):
        self.journals = self.HEMATOLOGY_JOURNALS
        self.selected_journal: Optional[Journal] = None

    def match_manuscript_to_journal(
        self,
        manuscript_type: str,
        keywords: List[str],
        category: Optional[JournalCategory] = None,
    ) -> List[JournalMatch]:
        matches = []

        for journal in self.journals:
            if category and journal.category != category:
                continue

            score = 0.0
            reasons = []
            warnings = []

            scope_match = journal.matches_scope(keywords)
            score += scope_match * 50
            if scope_match > 0.5:
                reasons.append(f"Strong scope match ({scope_match:.0%})")

            if (
                manuscript_type == "clinical_trial"
                and "Clinical trials" in journal.features
            ):
                score += 20
                reasons.append("Clinical trial friendly")

            if (
                manuscript_type == "classification"
                and journal.category == JournalCategory.CLASSIFICATION
            ):
                score += 25
                reasons.append("Classification/pathology focus")

            if "GVHD" in keywords and "GVHD" in str(journal.scope_keywords):
                score += 20
                reasons.append("GVHD research specialty")

            if journal.acceptance_rate and journal.acceptance_rate < 0.20:
                warnings.append("Highly competitive journal")

            matches.append(
                JournalMatch(
                    journal=journal,
                    match_score=score,
                    relevance_reasons=reasons,
                    warnings=warnings,
                )
            )

        matches.sort(key=lambda x: x.match_score, reverse=True)
        return matches

    def analyze_journal_scope(self, journal_name: str) -> Dict[str, Any]:
        journal = next(
            (j for j in self.journals if j.name.lower() == journal_name.lower()), None
        )

        if not journal:
            return {"error": f"Journal '{journal_name}' not found"}

        return {
            "name": journal.name,
            "category": journal.category.value,
            "impact_factor": journal.impact_factor,
            "acceptance_rate": journal.acceptance_rate,
            "review_time": f"{journal.review_time_days} days"
            if journal.review_time_days
            else "Unknown",
            "word_limit": journal.word_limit,
            "abstract_limit": journal.abstract_limit,
            "reference_limit": journal.reference_limit,
            "features": journal.features,
            "scope_keywords": journal.scope_keywords,
        }

    def get_journal_by_category(self, category: JournalCategory) -> List[Journal]:
        return [j for j in self.journals if j.category == category]

    def recommend_journal_strategy(
        self, manuscript_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        keywords = manuscript_info.get("keywords", [])
        manuscript_type = manuscript_info.get("type", "")
        target_category = manuscript_info.get("category")

        category_map = {
            "gvhd": JournalCategory.TRANSPLANTATION,
            "transplantation": JournalCategory.TRANSPLANTATION,
            "classification": JournalCategory.CLASSIFICATION,
            "therapeutic": JournalCategory.THERAPEUTIC,
            "general": JournalCategory.GENERAL_HEMATOLOGY,
        }

        category = category_map.get(target_category)
        matches = self.match_manuscript_to_journal(manuscript_type, keywords, category)

        return {
            "top_matches": [
                {
                    "journal": m.journal.name,
                    "score": f"{m.match_score:.1f}",
                    "impact_factor": m.journal.impact_factor,
                    "reasons": m.relevance_reasons,
                    "warnings": m.warnings,
                }
                for m in matches[:5]
            ],
            "strategy_recommendations": [
                "Consider impact factor vs. acceptance rate",
                "Match manuscript scope to journal scope",
                "Check word count and reference limits",
            ],
        }


if __name__ == "__main__":
    manager = JournalStrategyManager()

    info = {
        "keywords": ["GVHD", "steroid-refractory", "ruxolitinib", "treatment"],
        "type": "clinical_trial",
        "category": "gvhd",
    }

    result = manager.recommend_journal_strategy(info)

    print("Journal Strategy Recommendations")
    print("=" * 50)
    for match in result["top_matches"]:
        print(f"\n{match['journal']}")
        print(f"  Match Score: {match['score']}")
        print(f"  Impact Factor: {match['impact_factor']}")
        print(f"  Reasons: {', '.join(match['reasons'])}")
        if match["warnings"]:
            print(f"  Warnings: {', '.join(match['warnings'])}")
