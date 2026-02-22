from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class RejectionType(Enum):
    DESK_REJECT = "desk_reject"
    POST_REVIEW_REJECT = "post_review_reject"
    UNSUITABLE_SCOPE = "unsuitable_scope"
    MAJOR_FLAWS = "major_flaws"
    COMPETITION = "strong_competition"


class RevisionUrgency(Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RejectionAnalysis:
    rejection_type: RejectionType
    stated_reasons: List[str]
    inferred_reasons: List[str]
    severity_score: int
    salvageable: bool
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ResubmissionPlan:
    original_journal: str
    new_journal_options: List[Dict[str, Any]]
    required_revisions: List[str]
    timeline: str
    priority: RevisionUrgency
    strategy: str = ""


@dataclass
class JournalOption:
    journal_name: str
    impact_factor: float
    match_score: float
    acceptance_likelihood: str
    rationale: str


class ResubmissionManager:
    JOURNAL_HIERARCHY = {
        "blood": {
            "tier": 1,
            "if_range": (15, 25),
            "alternatives": ["blood_advances", "leukemia"],
        },
        "blood_advances": {
            "tier": 2,
            "if_range": (6, 8),
            "alternatives": ["bjh", "haematologica"],
        },
        "leukemia": {
            "tier": 1,
            "if_range": (10, 15),
            "alternatives": ["blood", "blood_advances"],
        },
        "bjh": {
            "tier": 2,
            "if_range": (5, 7),
            "alternatives": ["blood_research", "haematologica"],
        },
        "haematologica": {
            "tier": 2,
            "if_range": (9, 12),
            "alternatives": ["bjh", "blood_advances"],
        },
        "blood_research": {
            "tier": 3,
            "if_range": (2, 4),
            "alternatives": ["annals_hematology"],
        },
        "jco": {"tier": 1, "if_range": (40, 50), "alternatives": ["blood", "leukemia"]},
    }

    REJECTION_PATTERNS = {
        RejectionType.UNSUITABLE_SCOPE: [
            "outside the scope",
            "not suitable for our readership",
            "not within the aims",
            "better suited for",
        ],
        RejectionType.MAJOR_FLAWS: [
            "major concerns",
            "fundamental flaws",
            "significant limitations",
            "methodological issues",
            "inadequate sample size",
        ],
        RejectionType.COMPETITION: [
            "strong competition",
            "higher priority manuscripts",
            "limited space",
            "impact not sufficient",
        ],
        RejectionType.DESK_REJECT: [
            "does not meet our standards",
            "not considered for review",
            "cannot be sent for peer review",
        ],
    }

    def __init__(self):
        self.rejection_history: List[RejectionAnalysis] = []
        self.resubmission_plans: List[ResubmissionPlan] = []

    def analyze_rejection(
        self, rejection_letter: str, original_journal: str, manuscript_title: str
    ) -> RejectionAnalysis:
        stated_reasons = []
        inferred_reasons = []

        letter_lower = rejection_letter.lower()

        for rej_type, patterns in self.REJECTION_PATTERNS.items():
            for pattern in patterns:
                if pattern in letter_lower:
                    stated_reasons.append(f"Detected: {pattern}")

        if "impact" in letter_lower and (
            "limited" in letter_lower or "not sufficient" in letter_lower
        ):
            inferred_reasons.append("Perceived impact insufficient for journal tier")

        if "method" in letter_lower and (
            "concern" in letter_lower or "issue" in letter_lower
        ):
            inferred_reasons.append("Methodology concerns require revision")

        if "scope" in letter_lower or "suitable" in letter_lower:
            rejection_type = RejectionType.UNSUITABLE_SCOPE
        elif "competition" in letter_lower or "priority" in letter_lower:
            rejection_type = RejectionType.COMPETITION
        elif "desk" in letter_lower or "considered for review" in letter_lower:
            rejection_type = RejectionType.DESK_REJECT
        else:
            rejection_type = RejectionType.POST_REVIEW_REJECT

        severity_score = len(stated_reasons) + len(inferred_reasons)

        salvageable = (
            rejection_type not in [RejectionType.MAJOR_FLAWS] or severity_score < 5
        )

        recommendations = self._generate_recommendations(rejection_type, severity_score)

        analysis = RejectionAnalysis(
            rejection_type=rejection_type,
            stated_reasons=stated_reasons,
            inferred_reasons=inferred_reasons,
            severity_score=severity_score,
            salvageable=salvageable,
            recommendations=recommendations,
        )

        self.rejection_history.append(analysis)
        return analysis

    def _generate_recommendations(
        self, rejection_type: RejectionType, severity: int
    ) -> List[str]:
        recommendations = []

        if rejection_type == RejectionType.UNSUITABLE_SCOPE:
            recommendations.extend(
                [
                    "Identify journals with better scope fit",
                    "Rewrite cover letter to emphasize scope alignment",
                    "Consider specialized vs. general hematology journals",
                ]
            )
        elif rejection_type == RejectionType.MAJOR_FLAWS:
            recommendations.extend(
                [
                    "Address all methodological concerns",
                    "Consider additional validation studies",
                    "Consult with statistician if sample size questioned",
                ]
            )
        elif rejection_type == RejectionType.COMPETITION:
            recommendations.extend(
                [
                    "Target slightly lower-tier journal",
                    "Emphasize novelty more strongly in cover letter",
                    "Consider high-quality specialty journal",
                ]
            )
        elif rejection_type == RejectionType.DESK_REJECT:
            recommendations.extend(
                [
                    "Review journal's recent publications for scope alignment",
                    "Consider presubmission inquiry to another journal",
                    "Revise to better match journal's aims",
                ]
            )

        if severity > 3:
            recommendations.append("Consider substantial revision before resubmission")

        return recommendations

    def plan_resubmission(
        self,
        rejection_analysis: RejectionAnalysis,
        original_journal: str,
        manuscript_quality: str = "high",
    ) -> ResubmissionPlan:
        new_options = self._suggest_alternative_journals(
            original_journal, rejection_analysis
        )

        required_revisions = []
        if rejection_analysis.rejection_type == RejectionType.MAJOR_FLAWS:
            required_revisions.extend(
                [
                    "Revise methodology section",
                    "Add power analysis if needed",
                    "Address reviewer concerns",
                ]
            )
        elif rejection_analysis.rejection_type == RejectionType.COMPETITION:
            required_revisions.extend(
                [
                    "Strengthen novelty statement",
                    "Add additional validation data if available",
                ]
            )

        if rejection_analysis.severity_score > 4:
            priority = RevisionUrgency.HIGH
            timeline = "4-6 weeks for major revisions"
        elif rejection_analysis.severity_score > 2:
            priority = RevisionUrgency.MEDIUM
            timeline = "2-3 weeks for moderate revisions"
        else:
            priority = RevisionUrgency.LOW
            timeline = "1-2 weeks for minor revisions"

        strategy = self._generate_strategy(rejection_analysis, original_journal)

        plan = ResubmissionPlan(
            original_journal=original_journal,
            new_journal_options=new_options,
            required_revisions=required_revisions,
            timeline=timeline,
            priority=priority,
            strategy=strategy,
        )

        self.resubmission_plans.append(plan)
        return plan

    def _suggest_alternative_journals(
        self, original_journal: str, rejection_analysis: RejectionAnalysis
    ) -> List[Dict[str, Any]]:
        options = []

        original_lower = original_journal.lower().replace(" ", "_").replace("-", "_")
        journal_info = self.JOURNAL_HIERARCHY.get(original_lower)

        if not journal_info:
            return [
                {
                    "journal": "Blood Advances",
                    "rationale": "Good general hematology journal",
                }
            ]

        alternatives = journal_info.get("alternatives", [])

        if rejection_analysis.rejection_type == RejectionType.COMPETITION:
            tier = min(journal_info["tier"] + 1, 3)
            alternatives = self._get_journals_by_tier(tier)
        elif rejection_analysis.rejection_type == RejectionType.UNSUITABLE_SCOPE:
            alternatives = ["blood_advances", "bjh"]

        for alt in alternatives[:3]:
            alt_info = self.JOURNAL_HIERARCHY.get(alt, {})
            if_range = alt_info.get("if_range", (3, 5))
            options.append(
                {
                    "journal": alt.replace("_", " ").title(),
                    "impact_factor": f"{if_range[0]}-{if_range[1]}",
                    "rationale": self._get_journal_rationale(alt, rejection_analysis),
                }
            )

        return options

    def _get_journals_by_tier(self, tier: int) -> List[str]:
        return [
            name
            for name, info in self.JOURNAL_HIERARCHY.items()
            if info["tier"] == tier
        ]

    def _get_journal_rationale(self, journal: str, analysis: RejectionAnalysis) -> str:
        rationales = {
            "blood_advances": "Broad scope, good acceptance rate for solid studies",
            "bjh": "Practical focus, good for clinical research",
            "haematologica": "Strong European presence, good clinical focus",
            "leukemia": "High impact, disease-specific focus",
            "blood_research": "Good for Asian research, reasonable acceptance",
        }
        return rationales.get(journal, "Alternative journal option")

    def _generate_strategy(self, analysis: RejectionAnalysis, original: str) -> str:
        strategies = {
            RejectionType.UNSUITABLE_SCOPE: (
                f"Target journals with explicit interest in your specific topic. "
                f"Review {original}'s recent publications to better understand scope."
            ),
            RejectionType.COMPETITION: (
                "Submit to journal one tier lower. Emphasize practical impact "
                "over novelty in the cover letter."
            ),
            RejectionType.MAJOR_FLAWS: (
                "Complete thorough revision addressing all concerns. "
                "Consider additional experiments or analysis."
            ),
            RejectionType.DESK_REJECT: (
                "Reformat for new journal's requirements. "
                "Consider presubmission inquiry."
            ),
        }
        return strategies.get(analysis.rejection_type, "Standard resubmission strategy")

    def generate_resubmission_timeline(
        self, plan: ResubmissionPlan
    ) -> List[Dict[str, str]]:
        today = datetime.now()

        if plan.priority == RevisionUrgency.HIGH:
            days = [1, 7, 14, 28]
        elif plan.priority == RevisionUrgency.MEDIUM:
            days = [1, 5, 10, 21]
        else:
            days = [1, 3, 7, 14]

        timeline = [
            {
                "day": days[0],
                "task": "Review rejection letter and analyze feedback",
                "status": "Complete",
            },
            {
                "day": days[1],
                "task": "Complete required revisions",
                "status": "In Progress",
            },
            {
                "day": days[2],
                "task": "Revise cover letter for new journal",
                "status": "Pending",
            },
            {"day": days[3], "task": "Submit to new journal", "status": "Pending"},
        ]

        return timeline

    def get_resubmission_report(self) -> str:
        if not self.rejection_history:
            return "No rejection analyses recorded."

        lines = [
            "=" * 60,
            "RESUBMISSION HISTORY REPORT",
            "=" * 60,
            f"Total Rejections Analyzed: {len(self.rejection_history)}",
            f"Resubmission Plans Created: {len(self.resubmission_plans)}",
            "",
            "REJECTION TYPES:",
        ]

        type_counts = {}
        for analysis in self.rejection_history:
            rt = analysis.rejection_type.value
            type_counts[rt] = type_counts.get(rt, 0) + 1

        for rt, count in type_counts.items():
            lines.append(f"  {rt}: {count}")

        if self.resubmission_plans:
            lines.extend(
                [
                    "",
                    "RECENT RESUBMISSION PLAN:",
                    f"  Target: {self.resubmission_plans[-1].new_journal_options[0]['journal'] if self.resubmission_plans[-1].new_journal_options else 'TBD'}",
                    f"  Priority: {self.resubmission_plans[-1].priority.value}",
                    f"  Timeline: {self.resubmission_plans[-1].timeline}",
                ]
            )

        return "\n".join(lines)


if __name__ == "__main__":
    manager = ResubmissionManager()

    print("=" * 60)
    print("Resubmission Manager Demo")
    print("=" * 60)

    sample_rejection = """
    Dear Dr. Author,
    
    Thank you for submitting your manuscript to Blood. After careful consideration,
    we have decided not to consider your manuscript for publication.
    
    While your findings are interesting, the impact is not sufficient for our
    readership given strong competition. We receive many high-quality submissions
    and must prioritize those with the highest impact.
    
    We wish you success in finding a suitable venue for your work.
    
    Sincerely,
    Editor
    """

    analysis = manager.analyze_rejection(
        rejection_letter=sample_rejection,
        original_journal="Blood",
        manuscript_title="AML Study",
    )

    print(f"\nRejection Analysis:")
    print(f"  Type: {analysis.rejection_type.value}")
    print(f"  Severity: {analysis.severity_score}/10")
    print(f"  Salvageable: {analysis.salvageable}")

    print(f"\n  Stated Reasons:")
    for reason in analysis.stated_reasons[:3]:
        print(f"    - {reason}")

    print(f"\n  Recommendations:")
    for rec in analysis.recommendations[:3]:
        print(f"    • {rec}")

    plan = manager.plan_resubmission(analysis, "Blood")

    print(f"\n\nResubmission Plan:")
    print(f"  Priority: {plan.priority.value.upper()}")
    print(f"  Timeline: {plan.timeline}")
    print(f"\n  Alternative Journals:")
    for opt in plan.new_journal_options[:2]:
        print(f"    • {opt['journal']} (IF: {opt['impact_factor']})")
        print(f"      {opt['rationale']}")

    print(f"\n  Required Revisions:")
    for rev in plan.required_revisions[:2]:
        print(f"    - {rev}")

    print(f"\n  Strategy: {plan.strategy[:100]}...")
