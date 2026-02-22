from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import re


class CommentCategory(Enum):
    MAJOR_CONCERN = "major_concern"
    MINOR_COMMENT = "minor_comment"
    CLARIFICATION = "clarification"
    METHODOLOGY = "methodology"
    STATISTICS = "statistics"
    LITERATURE = "literature"
    WRITING = "writing"
    SUGGESTION = "suggestion"


class CommentPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ReviewerComment:
    comment_id: str
    reviewer_id: str
    original_text: str
    category: CommentCategory
    priority: CommentPriority
    location: str
    section: str
    suggested_change: str = ""
    response_draft: str = ""
    addressed: bool = False


@dataclass
class ResponseLetter:
    manuscript_title: str
    journal_name: str
    editor_name: str
    date: str
    responses: List[Dict[str, str]] = field(default_factory=list)
    full_text: str = ""


class PeerReviewManager:
    COMMENT_PATTERNS = {
        CommentCategory.MAJOR_CONCERN: [
            r"major concern",
            r"significant issue",
            r"fundamental problem",
            r"critical flaw",
            r"serious limitation",
        ],
        CommentCategory.METHODOLOGY: [
            r"method",
            r"design",
            r"approach",
            r"statistical analysis",
            r"power calculation",
            r"sample size",
        ],
        CommentCategory.STATISTICS: [
            r"statistic",
            r"p-value",
            r"significance",
            r"confidence interval",
            r"multivariate",
            r"regression",
        ],
        CommentCategory.LITERATURE: [
            r"reference",
            r"citation",
            r"previous work",
            r"recent study",
            r"literature",
        ],
        CommentCategory.WRITING: [
            r"grammar",
            r"typo",
            r"clarity",
            r"wording",
            r"language",
            r"style",
        ],
    }

    PRIORITY_INDICATORS = {
        CommentPriority.CRITICAL: [
            "must",
            "essential",
            "critical",
            "fundamental",
            "unacceptable",
        ],
        CommentPriority.HIGH: [
            "should",
            "important",
            "significant",
            "major",
            "strongly recommend",
        ],
        CommentPriority.MEDIUM: ["could", "would be helpful", "consider", "suggest"],
        CommentPriority.LOW: ["minor", "optional", "nitpick", "small suggestion"],
    }

    def __init__(self):
        self.comments: List[ReviewerComment] = []
        self.review_round: int = 1

    def categorize_reviewer_comments(
        self, reviewer_text: str, reviewer_id: str = "Reviewer #1"
    ) -> List[ReviewerComment]:
        comments = []

        numbered_pattern = r"(?:^|\n)\s*(\d+)[:.\)]\s*(.+?)(?=\n\s*\d+[:.\)]|\Z)"
        matches = re.findall(numbered_pattern, reviewer_text, re.DOTALL)

        if not matches:
            paragraphs = [p.strip() for p in reviewer_text.split("\n\n") if p.strip()]
            matches = [(str(i + 1), p) for i, p in enumerate(paragraphs)]

        for num, text in matches:
            text = text.strip()
            if len(text) < 20:
                continue

            category = self._detect_category(text)
            priority = self._detect_priority(text)

            comment = ReviewerComment(
                comment_id=f"R{self.review_round}_{reviewer_id}_{num}",
                reviewer_id=reviewer_id,
                original_text=text,
                category=category,
                priority=priority,
                location="",
                section=self._detect_section(text),
            )
            comments.append(comment)

        self.comments.extend(comments)
        return comments

    def _detect_category(self, text: str) -> CommentCategory:
        text_lower = text.lower()

        for category, patterns in self.COMMENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return category

        return CommentCategory.CLARIFICATION

    def _detect_priority(self, text: str) -> CommentPriority:
        text_lower = text.lower()

        for priority, indicators in self.PRIORITY_INDICATORS.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return priority

        return CommentPriority.MEDIUM

    def _detect_section(self, text: str) -> str:
        text_lower = text.lower()

        sections = {
            "abstract": ["abstract", "summary"],
            "introduction": ["introduction", "background"],
            "methods": ["method", "materials and methods"],
            "results": ["result", "findings"],
            "discussion": ["discussion"],
            "references": ["reference", "citation"],
            "figures": ["figure", "fig.", "image"],
            "tables": ["table"],
        }

        for section, keywords in sections.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return section

        return "general"

    def generate_response_letter(
        self,
        manuscript_title: str,
        journal_name: str,
        editor_name: str,
        comments: Optional[List[ReviewerComment]] = None,
    ) -> ResponseLetter:
        if comments is None:
            comments = self.comments

        sorted_comments = sorted(
            comments,
            key=lambda c: (
                0
                if c.priority == CommentPriority.CRITICAL
                else 1
                if c.priority == CommentPriority.HIGH
                else 2
                if c.priority == CommentPriority.MEDIUM
                else 3,
                c.reviewer_id,
            ),
        )

        responses = []
        letter_body = []

        letter_body.append(f"{datetime.now().strftime('%B %d, %Y')}")
        letter_body.append("")
        letter_body.append(f"{editor_name}")
        letter_body.append(f"Editor, {journal_name}")
        letter_body.append("")
        letter_body.append(f"Re: {manuscript_title}")
        letter_body.append("")
        letter_body.append(f"Dear {editor_name.split()[0]},")
        letter_body.append("")
        letter_body.append(
            "We thank the reviewers for their thoughtful comments and constructive feedback."
        )
        letter_body.append(
            "We have carefully addressed all concerns and revised the manuscript accordingly."
        )
        letter_body.append("")
        letter_body.append(
            "Below, we provide point-by-point responses to all reviewer comments."
        )
        letter_body.append(
            "Changes in the revised manuscript are highlighted in yellow."
        )
        letter_body.append("")

        current_reviewer = None
        for comment in sorted_comments:
            if comment.reviewer_id != current_reviewer:
                current_reviewer = comment.reviewer_id
                letter_body.append(f"\n{'=' * 60}")
                letter_body.append(f"Response to {current_reviewer}")
                letter_body.append("=" * 60)
                letter_body.append("")

            letter_body.append(
                f"\nComment ({comment.priority.value.upper()} - {comment.category.value}):"
            )
            letter_body.append(f'"{comment.original_text[:200]}..."')
            letter_body.append("")
            letter_body.append("Response:")

            if comment.response_draft:
                letter_body.append(comment.response_draft)
            else:
                letter_body.append(
                    f"[Response to be drafted - {comment.section} section]"
                )

            letter_body.append("")
            letter_body.append("-" * 40)

            responses.append(
                {
                    "comment_id": comment.comment_id,
                    "reviewer": comment.reviewer_id,
                    "original": comment.original_text[:100],
                    "response": comment.response_draft,
                    "addressed": comment.addressed,
                }
            )

        letter_body.append(
            "\n\nThank you again for considering our revised manuscript."
        )
        letter_body.append("")
        letter_body.append("Sincerely,")
        letter_body.append("")
        letter_body.append("[Corresponding Author]")
        letter_body.append("[Institution]")

        return ResponseLetter(
            manuscript_title=manuscript_title,
            journal_name=journal_name,
            editor_name=editor_name,
            date=datetime.now().strftime("%B %d, %Y"),
            responses=responses,
            full_text="\n".join(letter_body),
        )

    def generate_response_draft(self, comment: ReviewerComment) -> str:
        templates = {
            CommentCategory.METHODOLOGY: "We appreciate this methodological concern. We have revised the Methods section to clarify...",
            CommentCategory.STATISTICS: "Thank you for raising this statistical point. We have re-analyzed the data...",
            CommentCategory.LITERATURE: "We appreciate the suggestion to include additional references. We have added citations to...",
            CommentCategory.WRITING: "Thank you for pointing this out. We have revised the text for clarity...",
            CommentCategory.MAJOR_CONCERN: "We appreciate this important concern. We have addressed this by...",
        }

        return templates.get(
            comment.category,
            "Thank you for this comment. We have revised the manuscript accordingly.",
        )

    def get_summary_statistics(self) -> Dict[str, Any]:
        if not self.comments:
            return {"total_comments": 0}

        categories = {}
        priorities = {}
        reviewers = set()

        for comment in self.comments:
            cat = comment.category.value
            categories[cat] = categories.get(cat, 0) + 1

            pri = comment.priority.value
            priorities[pri] = priorities.get(pri, 0) + 1

            reviewers.add(comment.reviewer_id)

        return {
            "total_comments": len(self.comments),
            "unique_reviewers": len(reviewers),
            "by_category": categories,
            "by_priority": priorities,
            "addressed": sum(1 for c in self.comments if c.addressed),
            "pending": sum(1 for c in self.comments if not c.addressed),
        }


if __name__ == "__main__":
    manager = PeerReviewManager()

    sample_review = """
1. The sample size appears underpowered for the primary endpoint. Please provide a power calculation.

2. The methods section lacks detail on the statistical tests used. Please clarify which tests were used for each analysis.

3. The authors should cite recent work by Smith et al. (2023) on NPM1 mutations.

4. There is a typo in Figure 2 legend.

5. The major concern is the lack of external validation. This significantly limits the generalizability of the findings.
    """

    print("=" * 60)
    print("Peer Review Manager Demo")
    print("=" * 60)

    comments = manager.categorize_reviewer_comments(sample_review, "Reviewer #1")

    print(f"\nCategorized {len(comments)} comments:\n")
    for c in comments:
        print(f"  [{c.priority.value.upper()}] {c.category.value}")
        print(f"    Section: {c.section}")
        print(f"    Text: {c.original_text[:60]}...")
        print()

    stats = manager.get_summary_statistics()
    print("\nSummary Statistics:")
    print(f"  Total: {stats['total_comments']}")
    print(f"  By Priority: {stats['by_priority']}")
    print(f"  By Category: {stats['by_category']}")

    letter = manager.generate_response_letter(
        manuscript_title="Novel Approach to AML Treatment",
        journal_name="Blood",
        editor_name="Dr. Editor-in-Chief",
    )

    print("\n\nResponse Letter Preview:")
    print("-" * 60)
    print(letter.full_text[:600] + "...")
