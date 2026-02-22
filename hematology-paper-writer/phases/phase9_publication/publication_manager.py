from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ProofElement(Enum):
    ABSTRACT = "abstract"
    MAIN_TEXT = "main_text"
    REFERENCES = "references"
    FIGURES = "figures"
    TABLES = "tables"
    SUPPLEMENTARY = "supplementary"
    AUTHOR_INFO = "author_info"
    AFFILIATIONS = "affiliations"


@dataclass
class ProofIssue:
    element: ProofElement
    issue_type: str
    original_text: str
    corrected_text: str
    page_number: Optional[int] = None
    line_number: Optional[int] = None
    notes: str = ""


@dataclass
class ProofReview:
    manuscript_title: str
    journal_name: str
    review_date: str
    issues: List[ProofIssue] = field(default_factory=list)
    approved: bool = False


@dataclass
class PostPublicationPlan:
    manuscript_title: str
    publication_date: str
    promotion_strategies: List[str] = field(default_factory=list)
    follow_up_studies: List[str] = field(default_factory=list)
    collaboration_opportunities: List[str] = field(default_factory=list)


class PublicationManager:
    PROOF_CHECKLIST = {
        ProofElement.ABSTRACT: [
            "Verify all numbers match main text",
            "Check word count within limit",
            "Confirm structured format if required",
            "Verify keywords are present",
        ],
        ProofElement.MAIN_TEXT: [
            "Read entire manuscript carefully",
            "Verify all cross-references to figures/tables",
            "Check pagination and section headers",
            "Confirm all abbreviations defined at first use",
            "Verify nomenclature consistency (BCR::ABL1, etc.)",
        ],
        ProofElement.REFERENCES: [
            "Verify all citations match reference list",
            "Check reference formatting per journal style",
            "Confirm all references are accessible (no preprint-only citations)",
            "Verify author names and year accuracy",
            "Check DOI links where available",
        ],
        ProofElement.FIGURES: [
            "Check figure labels and legends",
            "Verify figure quality (resolution, font size)",
            "Confirm color figures if paid for",
            "Check figure numbering sequence",
        ],
        ProofElement.TABLES: [
            "Verify table titles and footnotes",
            "Check data alignment and formatting",
            "Confirm statistical notations",
            "Verify table numbering",
        ],
        ProofElement.AUTHOR_INFO: [
            "Verify author order",
            "Check spelling of all author names",
            "Confirm corresponding author marked",
            "Verify email addresses",
        ],
        ProofElement.AFFILIATIONS: [
            "Check department and institution names",
            "Verify city and country for each affiliation",
            "Confirm superscript numbering matches author list",
        ],
    }

    COMMON_PROOF_ERRORS = [
        ("BCR-ABL", "BCR::ABL1", "gene fusion notation"),
        ("t(9;22)", "t(9;22)(q34.1;q11.2)", "cytogenetic notation"),
        ("WHO 2016", "WHO 2022", "classification version"),
        ("ELN 2017", "ELN 2022", "response criteria version"),
        ("NPM1", "*NPM1*", "gene symbol italicization"),
        (
            "AML with multilineage dysplasia",
            "AML with myelodysplasia-related changes",
            "disease terminology",
        ),
    ]

    PROMOTION_STRATEGIES = [
        "Share on ResearchGate, Academia.edu, and LinkedIn",
        "Create a plain language summary for social media",
        "Email collaborators and colleagues in the field",
        "Present findings at upcoming conferences",
        "Write a blog post or article for lay audiences",
        "Contact institution press office for news release",
        "Submit to relevant subreddit or online forums",
        "Create visual abstract for Twitter/X sharing",
    ]

    def __init__(self):
        self.current_review: Optional[ProofReview] = None
        self.review_history: List[ProofReview] = []

    def review_proofs(
        self, proof_text: str, manuscript_title: str, journal_name: str
    ) -> ProofReview:
        review = ProofReview(
            manuscript_title=manuscript_title,
            journal_name=journal_name,
            review_date=datetime.now().strftime("%Y-%m-%d"),
        )

        for original, corrected, issue_type in self.COMMON_PROOF_ERRORS:
            if original in proof_text:
                review.issues.append(
                    ProofIssue(
                        element=ProofElement.MAIN_TEXT,
                        issue_type=issue_type,
                        original_text=original,
                        corrected_text=corrected,
                        notes=f"Auto-detected: {issue_type}",
                    )
                )

        if "BCR-ABL" in proof_text or "PML-RARA" in proof_text:
            review.issues.append(
                ProofIssue(
                    element=ProofElement.MAIN_TEXT,
                    issue_type="nomenclature",
                    original_text="Old fusion notation detected",
                    corrected_text="Use ISCN 2024 double colon notation",
                    notes="Check for BCR::ABL1, PML::RARA, etc.",
                )
            )

        self.current_review = review
        self.review_history.append(review)
        return review

    def generate_proof_checklist(self) -> Dict[ProofElement, List[str]]:
        return self.PROOF_CHECKLIST

    def add_proof_correction(
        self,
        element: ProofElement,
        original: str,
        corrected: str,
        page: Optional[int] = None,
        line: Optional[int] = None,
        notes: str = "",
    ) -> None:
        if self.current_review:
            self.current_review.issues.append(
                ProofIssue(
                    element=element,
                    issue_type="manual_correction",
                    original_text=original,
                    corrected_text=corrected,
                    page_number=page,
                    line_number=line,
                    notes=notes,
                )
            )

    def generate_correction_summary(self) -> str:
        if not self.current_review:
            return "No active proof review."

        lines = [
            f"PROOF CORRECTION SUMMARY",
            f"Manuscript: {self.current_review.manuscript_title}",
            f"Journal: {self.current_review.journal_name}",
            f"Review Date: {self.current_review.review_date}",
            f"Total Corrections: {len(self.current_review.issues)}",
            "",
            "CORRECTIONS BY ELEMENT:",
        ]

        by_element = {}
        for issue in self.current_review.issues:
            elem = issue.element.value
            if elem not in by_element:
                by_element[elem] = []
            by_element[elem].append(issue)

        for element, issues in by_element.items():
            lines.append(f"\n{element.upper()}: {len(issues)} issue(s)")
            for i, issue in enumerate(issues, 1):
                lines.append(
                    f"  {i}. [{issue.issue_type}] {issue.original_text[:40]}..."
                )
                lines.append(f"     → {issue.corrected_text[:40]}...")

        return "\n".join(lines)

    def plan_post_publication(
        self,
        manuscript_title: str,
        publication_date: str,
        key_findings: List[str],
        target_audiences: List[str],
    ) -> PostPublicationPlan:
        strategies = self.PROMOTION_STRATEGIES.copy()

        follow_up = [
            "Validation cohort study",
            "Mechanism investigation",
            "Expanded patient population analysis",
            "Long-term outcome follow-up",
        ]

        collaborations = [
            "Contact international collaborators for multi-center validation",
            "Engage with patient advocacy groups",
            "Connect with industry partners for translation",
        ]

        return PostPublicationPlan(
            manuscript_title=manuscript_title,
            publication_date=publication_date,
            promotion_strategies=strategies,
            follow_up_studies=follow_up,
            collaboration_opportunities=collaborations,
        )

    def generate_publication_timeline(self) -> List[Dict[str, str]]:
        today = datetime.now()

        timeline = [
            {
                "date": today.strftime("%Y-%m-%d"),
                "event": "Proof review submitted",
                "status": "In Progress",
            },
            {
                "date": (today.replace(day=today.day + 7)).strftime("%Y-%m-%d"),
                "event": "Expected publication online",
                "status": "Planned",
            },
            {
                "date": (today.replace(day=today.day + 14)).strftime("%Y-%m-%d"),
                "event": "Social media promotion",
                "status": "Planned",
            },
            {
                "date": (today.replace(day=today.day + 30)).strftime("%Y-%m-%d"),
                "event": "Email collaborators",
                "status": "Planned",
            },
        ]

        return timeline


if __name__ == "__main__":
    manager = PublicationManager()

    print("=" * 60)
    print("Publication Manager Demo")
    print("=" * 60)

    sample_proof = """
    Patients with AML were diagnosed according to WHO 2016 criteria.
    BCR-ABL fusion was detected by FISH.
    """

    review = manager.review_proofs(
        proof_text=sample_proof,
        manuscript_title="Novel AML Treatment Strategy",
        journal_name="Blood",
    )

    print(f"\nProof Review: {review.manuscript_title}")
    print(f"Issues Detected: {len(review.issues)}")

    for issue in review.issues:
        print(f"\n  [{issue.issue_type}]")
        print(f"    Original: {issue.original_text}")
        print(f"    Correct:  {issue.corrected_text}")

    print("\n" + "=" * 60)
    print(manager.generate_correction_summary())

    print("\n\nProof Checklist:")
    checklist = manager.generate_proof_checklist()
    for element, items in list(checklist.items())[:3]:
        print(f"\n{element.value.upper()}:")
        for item in items[:2]:
            print(f"  □ {item}")
        print(f"  ... and {len(items) - 2} more items")

    print("\n\nPost-Publication Plan:")
    plan = manager.plan_post_publication(
        manuscript_title="Novel AML Treatment",
        publication_date="2024-03-01",
        key_findings=["Improved CR rates", "Better OS"],
        target_audiences=["Hematologists", "Oncologists"],
    )
    print(f"  Strategies: {len(plan.promotion_strategies)}")
    print(f"  Follow-up studies: {len(plan.follow_up_studies)}")
    print(f"  Collaboration opportunities: {len(plan.collaboration_opportunities)}")
