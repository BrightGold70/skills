from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class SubmissionType(Enum):
    ORIGINAL_ARTICLE = "original_article"
    REVIEW_ARTICLE = "review_article"
    CASE_REPORT = "case_report"
    LETTER_TO_EDITOR = "letter_to_editor"
    CLINICAL_TRIAL = "clinical_trial"


@dataclass
class SubmissionMetadata:
    manuscript_title: str
    corresponding_author: str
    corresponding_email: str
    institution: str
    manuscript_type: SubmissionType
    word_count: int = 0
    figure_count: int = 0
    table_count: int = 0
    reference_count: int = 0
    keywords: List[str] = field(default_factory=list)
    funding_sources: List[str] = field(default_factory=list)
    conflicts_of_interest: List[str] = field(default_factory=list)
    previous_submissions: List[str] = field(default_factory=list)
    suggested_reviewers: List[Dict[str, str]] = field(default_factory=list)
    opposed_reviewers: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CoverLetter:
    recipient: str
    salutation: str
    opening_paragraph: str
    manuscript_summary: str
    significance_statement: str
    fit_statement: str
    closing_paragraph: str
    signature: str
    full_text: str = ""


class SubmissionManager:
    COVER_LETTER_TEMPLATES = {
        "standard": """{date}

{recipient}
{journal_name}

Dear {editor_name},

{opening}

{manuscript_summary}

{significance}

{fit_statement}

{closing}

Sincerely,

{signature}
{title}
{institution}
{email}
""",
        "hematology_focused": """{date}

{recipient}
{journal_name}

Dear {editor_name},

We are submitting our manuscript entitled "{manuscript_title}" for consideration for publication in {journal_name}.

{background}

{study_summary}

{key_findings}

{clinical_relevance}

{journal_fit}

We confirm that this work is original and has not been published or submitted elsewhere. All authors have approved the manuscript and agree with its submission to {journal_name}.

We have no conflicts of interest to disclose.

Sincerely,

{signature}
{corresponding_author}
{institution}
{email}
""",
    }

    JOURNAL_SUBMISSION_CHECKLISTS = {
        "blood": [
            "Title page with full author information",
            "Abstract (structured, <250 words)",
            "Main text (<5000 words)",
            "References (Vancouver style, <60)",
            "Figures (<6, TIFF/EPS format)",
            "Tables (<6)",
            "Supplementary materials (if applicable)",
            "Author contributions statement",
            "Conflict of interest disclosures",
            "Funding statement",
            "Data availability statement",
            "Clinical trial registration (if applicable)",
        ],
        "blood_advances": [
            "Title page",
            "Abstract (<250 words)",
            "Main text (<6000 words)",
            "References (<60)",
            "Figures (<8)",
            "Tables (<8)",
            "Supplementary data",
            "Author contributions",
            "COI disclosures",
            "Funding sources",
        ],
        "bjh": [
            "Title page with running head",
            "Abstract (<200 words)",
            "Keywords (3-6)",
            "Main text (<5000 words)",
            "References (Vancouver, <50)",
            "Figures (<6)",
            "Tables (<6)",
            "Author contributions",
            "COI statement",
            "Funding acknowledgment",
        ],
    }

    def __init__(self):
        self.submission_history: List[Dict[str, Any]] = []

    def prepare_submission_metadata(
        self,
        title: str,
        corresponding_author: str,
        email: str,
        institution: str,
        manuscript_type: SubmissionType,
        **kwargs,
    ) -> SubmissionMetadata:
        return SubmissionMetadata(
            manuscript_title=title,
            corresponding_author=corresponding_author,
            corresponding_email=email,
            institution=institution,
            manuscript_type=manuscript_type,
            word_count=kwargs.get("word_count", 0),
            figure_count=kwargs.get("figure_count", 0),
            table_count=kwargs.get("table_count", 0),
            reference_count=kwargs.get("reference_count", 0),
            keywords=kwargs.get("keywords", []),
            funding_sources=kwargs.get("funding_sources", []),
            conflicts_of_interest=kwargs.get(
                "conflicts_of_interest", ["None declared"]
            ),
            suggested_reviewers=kwargs.get("suggested_reviewers", []),
            opposed_reviewers=kwargs.get("opposed_reviewers", []),
        )

    def generate_cover_letter(
        self,
        metadata: SubmissionMetadata,
        journal_name: str,
        editor_name: str = "Editor",
        template_type: str = "hematology_focused",
        **kwargs,
    ) -> CoverLetter:
        template = self.COVER_LETTER_TEMPLATES.get(
            template_type, self.COVER_LETTER_TEMPLATES["standard"]
        )

        date_str = datetime.now().strftime("%B %d, %Y")

        if template_type == "hematology_focused":
            full_text = template.format(
                date=date_str,
                recipient=editor_name,
                journal_name=journal_name,
                editor_name=editor_name,
                manuscript_title=metadata.manuscript_title,
                background=kwargs.get("background", "[Background paragraph]"),
                study_summary=kwargs.get("study_summary", "[Study summary]"),
                key_findings=kwargs.get("key_findings", "[Key findings]"),
                clinical_relevance=kwargs.get(
                    "clinical_relevance", "[Clinical relevance]"
                ),
                journal_fit=kwargs.get(
                    "journal_fit", f"[Why this fits {journal_name}]"
                ),
                signature="[Signature]",
                corresponding_author=metadata.corresponding_author,
                institution=metadata.institution,
                email=metadata.corresponding_email,
            )
        else:
            full_text = template.format(
                date=date_str,
                recipient=f"{editor_name}, Editor",
                journal_name=journal_name,
                editor_name=editor_name,
                opening=kwargs.get(
                    "opening",
                    f"Please consider our manuscript entitled '{metadata.manuscript_title}' for publication in {journal_name}.",
                ),
                manuscript_summary=kwargs.get("manuscript_summary", "[Summary]"),
                significance=kwargs.get("significance", "[Significance]"),
                fit_statement=kwargs.get("fit_statement", f"[Fit for {journal_name}]"),
                closing=kwargs.get("closing", "Thank you for your consideration."),
                signature="[Signature]",
                title=metadata.corresponding_author,
                institution=metadata.institution,
                email=metadata.corresponding_email,
            )

        return CoverLetter(
            recipient=editor_name,
            salutation=f"Dear {editor_name},",
            opening_paragraph=kwargs.get("opening", ""),
            manuscript_summary=kwargs.get("manuscript_summary", ""),
            significance_statement=kwargs.get("significance", ""),
            fit_statement=kwargs.get("journal_fit", ""),
            closing_paragraph=kwargs.get("closing", ""),
            signature=metadata.corresponding_author,
            full_text=full_text,
        )

    def generate_submission_checklist(self, journal: str) -> List[str]:
        journal_key = journal.lower().replace(" ", "_").replace("-", "_")
        return self.JOURNAL_SUBMISSION_CHECKLISTS.get(
            journal_key, self.JOURNAL_SUBMISSION_CHECKLISTS["blood"]
        )

    def suggest_reviewers(
        self, keywords: List[str], count: int = 3
    ) -> List[Dict[str, str]]:
        suggested = []

        expert_database = {
            "AML": [
                {
                    "name": "Dr. Jane Smith",
                    "institution": "Memorial Sloan Kettering",
                    "email": "j.smith@mskcc.org",
                    "expertise": "AML genomics",
                },
                {
                    "name": "Dr. John Doe",
                    "institution": "MD Anderson",
                    "email": "jdoe@mdanderson.org",
                    "expertise": "AML therapeutics",
                },
            ],
            "GVHD": [
                {
                    "name": "Dr. Mary Johnson",
                    "institution": "Stanford University",
                    "email": "mjohnson@stanford.edu",
                    "expertise": "GVHD immunology",
                },
                {
                    "name": "Dr. Robert Brown",
                    "institution": "University of Michigan",
                    "email": "rbrown@umich.edu",
                    "expertise": "Chronic GVHD",
                },
            ],
            "CML": [
                {
                    "name": "Dr. Sarah Lee",
                    "institution": "University of Heidelberg",
                    "email": "s.lee@dkfz.de",
                    "expertise": "CML treatment",
                },
                {
                    "name": "Dr. Michael Chen",
                    "institution": "University of Toronto",
                    "email": "mchen@uhn.ca",
                    "expertise": "TKI resistance",
                },
            ],
        }

        for keyword in keywords:
            keyword_upper = keyword.upper()
            if keyword_upper in expert_database:
                suggested.extend(expert_database[keyword_upper])

        return suggested[:count]

    def validate_submission_package(
        self, metadata: SubmissionMetadata, journal: str
    ) -> Dict[str, Any]:
        issues = []
        warnings = []

        if metadata.word_count > 6000:
            issues.append(
                f"Word count ({metadata.word_count}) exceeds typical limit for {journal}"
            )

        if metadata.figure_count > 8:
            issues.append(
                f"Figure count ({metadata.figure_count}) may exceed journal limits"
            )

        if metadata.reference_count > 60:
            warnings.append(f"Reference count ({metadata.reference_count}) is high")

        if len(metadata.keywords) < 3:
            warnings.append("Consider adding more keywords (3-6 recommended)")

        if not metadata.conflicts_of_interest:
            issues.append("Conflict of interest statement required")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "checklist": self.generate_submission_checklist(journal),
        }


if __name__ == "__main__":
    manager = SubmissionManager()

    metadata = manager.prepare_submission_metadata(
        title="Novel Therapeutic Approach for AML with NPM1 Mutation",
        corresponding_author="Dr. Jane Doe",
        email="jane.doe@hospital.edu",
        institution="University Medical Center",
        manuscript_type=SubmissionType.ORIGINAL_ARTICLE,
        word_count=4500,
        figure_count=5,
        table_count=3,
        reference_count=45,
        keywords=["AML", "NPM1", "targeted therapy"],
    )

    print("=" * 60)
    print("Submission Manager Demo")
    print("=" * 60)

    cover_letter = manager.generate_cover_letter(
        metadata=metadata,
        journal_name="Blood",
        editor_name="Dr. Editor",
        background="Acute myeloid leukemia (AML) with NPM1 mutation represents a distinct subtype with unique clinical characteristics.",
        study_summary="We conducted a retrospective analysis of 200 patients with NPM1-mutated AML treated with novel targeted therapy.",
        key_findings="Our study demonstrates significant improvement in complete remission rates (85% vs 65%, p<0.001).",
        clinical_relevance="These findings have immediate implications for clinical practice in AML treatment.",
        journal_fit="Blood is the premier journal for hematology research and reaches our target audience of clinicians and researchers.",
    )

    print("\nCover Letter Preview:")
    print("-" * 60)
    print(cover_letter.full_text[:800] + "...")

    print("\n\nSubmission Checklist for Blood:")
    checklist = manager.generate_submission_checklist("blood")
    for i, item in enumerate(checklist[:5], 1):
        print(f"  {i}. {item}")
    print(f"  ... and {len(checklist) - 5} more items")

    print("\n\nValidation:")
    validation = manager.validate_submission_package(metadata, "blood")
    print(f"  Valid: {validation['valid']}")
    print(f"  Issues: {len(validation['issues'])}")
    print(f"  Warnings: {len(validation['warnings'])}")
