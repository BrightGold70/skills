from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import re
from datetime import datetime


class UpdateType(Enum):
    TERMINOLOGY = "terminology"
    NOMENCLATURE = "nomenclature"
    CLASSIFICATION = "classification"
    GVHD_CONTENT = "gvhd"
    THERAPEUTIC = "therapeutic"
    REFERENCE = "reference"


@dataclass
class UpdateReport:
    updates_made: List[Dict[str, str]] = field(default_factory=list)
    issues_found: List[Dict[str, str]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    updated_text: str = ""
    update_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConsistencyReport:
    section: str
    inconsistencies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ManuscriptUpdater:
    TERMINOLOGY_UPDATES = {
        "WHO 2016": "WHO 2022 (5th edition)",
        "WHO 4th edition": "WHO 2022 (5th edition)",
        "BCR-ABL": "BCR::ABL1",
        "BCR/ABL": "BCR::ABL1",
        "PML-RARA": "PML::RARA",
        "RUNX1-RUNX1T1": "RUNX1::RUNX1T1",
        "CBFB-MYH11": "CBFB::MYH11",
        "t(9;22)": "t(9;22)(q34.1;q11.2)",
        "t(8;21)": "t(8;21)(q22;q22.1)",
        "t(15;17)": "t(15;17)(q24.1;q21.2)",
        "inv(16)": "inv(16)(p13.1q22)",
        "del(5)": "del(5q)",
        "del(7)": "del(7q)",
    }

    DEPRECATED_DISEASE_NAMES = {
        "AML with multilineage dysplasia": "AML with myelodysplasia-related changes",
        "therapy-related AML": "AML, myelodysplasia-related",
        "AML with recurrent genetic abnormalities": "AML with defining genetic abnormalities",
    }

    GVHD_TERMINOLOGY = {
        "GVHD prophylaxis": "GVHD prophylaxis regimen",
        "chronic GVHD severity": "chronic GVHD global score",
        "GVHD grade": "GVHD stage/grade",
    }

    def __init__(self):
        self.update_history: List[UpdateReport] = []

    def update_classification_terminology(
        self, text: str, target_system: str = "WHO 2022"
    ) -> UpdateReport:
        report = UpdateReport()
        updated_text = text

        for old_term, new_term in self.TERMINOLOGY_UPDATES.items():
            if old_term in updated_text:
                count = updated_text.count(old_term)
                updated_text = updated_text.replace(old_term, new_term)
                report.updates_made.append(
                    {
                        "type": "nomenclature",
                        "original": old_term,
                        "replacement": new_term,
                        "count": str(count),
                    }
                )

        for old_name, new_name in self.DEPRECATED_DISEASE_NAMES.items():
            if old_name.lower() in updated_text.lower():
                pattern = re.compile(re.escape(old_name), re.IGNORECASE)
                count = len(pattern.findall(updated_text))
                updated_text = pattern.sub(new_name, updated_text)
                report.updates_made.append(
                    {
                        "type": "disease_nomenclature",
                        "original": old_name,
                        "replacement": new_name,
                        "count": str(count),
                    }
                )

        if "WHO 2022" not in updated_text and "ICC 2022" not in updated_text:
            if "WHO" in updated_text or "ICC" in updated_text:
                report.issues_found.append(
                    {
                        "type": "classification_version",
                        "issue": "Classification system version may be outdated",
                        "suggestion": f"Update to {target_system} terminology",
                    }
                )

        report.updated_text = updated_text
        self.update_history.append(report)
        return report

    def update_gvhd_content(self, text: str) -> UpdateReport:
        report = UpdateReport()
        updated_text = text

        for old_term, new_term in self.GVHD_TERMINOLOGY.items():
            if old_term in updated_text:
                count = updated_text.count(old_term)
                updated_text = updated_text.replace(old_term, new_term)
                report.updates_made.append(
                    {
                        "type": "gvhd_terminology",
                        "original": old_term,
                        "replacement": new_term,
                        "count": str(count),
                    }
                )

        if "MAGIC" not in updated_text and "NIH" not in updated_text:
            if "GVHD" in updated_text:
                report.issues_found.append(
                    {
                        "type": "gvhd_criteria",
                        "issue": "GVHD criteria system not specified",
                        "suggestion": "Specify MAGIC criteria for acute or NIH criteria for chronic GVHD",
                    }
                )

        if "organ assessment" not in updated_text.lower() and "GVHD" in updated_text:
            report.suggestions.append(
                "Consider adding organ-specific assessment details for GVHD"
            )

        report.updated_text = updated_text
        self.update_history.append(report)
        return report

    def update_therapeutic_content(
        self, text: str, disease: str = "AML"
    ) -> UpdateReport:
        report = UpdateReport()
        updated_text = text

        if disease.upper() == "AML":
            if "ELN 2017" in updated_text:
                updated_text = updated_text.replace("ELN 2017", "ELN 2022")
                report.updates_made.append(
                    {
                        "type": "guideline_version",
                        "original": "ELN 2017",
                        "replacement": "ELN 2022",
                        "count": "1",
                    }
                )

            if "complete remission" in updated_text.lower():
                if (
                    "CRi" not in updated_text
                    and "CR with incomplete count recovery" not in updated_text
                ):
                    report.suggestions.append(
                        "Consider specifying CR vs CRi vs CRh for AML response criteria"
                    )

        elif disease.upper() == "CML":
            if "ELN 2020" in updated_text or "ELN 2013" in updated_text:
                updated_text = updated_text.replace("ELN 2020", "ELN 2025").replace(
                    "ELN 2013", "ELN 2025"
                )
                report.updates_made.append(
                    {
                        "type": "guideline_version",
                        "original": "ELN 2020/2013",
                        "replacement": "ELN 2025",
                        "count": "1",
                    }
                )

        if (
            "adverse event" not in updated_text.lower()
            and "adverse reaction" not in updated_text.lower()
        ):
            if disease in ["AML", "CML", "GVHD"]:
                report.issues_found.append(
                    {
                        "type": "safety_reporting",
                        "issue": "Adverse event reporting criteria not mentioned",
                        "suggestion": "Add CTCAE v5.0 or other appropriate adverse event grading system",
                    }
                )

        report.updated_text = updated_text
        self.update_history.append(report)
        return report

    def verify_cross_section_consistency(self, text: str) -> ConsistencyReport:
        report = ConsistencyReport(section="cross_section_consistency")

        disease_entities = re.findall(r"AML with \w+ mutation", text)
        if len(set(disease_entities)) > 1:
            report.inconsistencies.append(
                f"Multiple disease entities mentioned: {set(disease_entities)}"
            )

        classification_systems = []
        if "WHO 2022" in text:
            classification_systems.append("WHO 2022")
        if "ICC 2022" in text:
            classification_systems.append("ICC 2022")
        if len(classification_systems) > 1:
            report.recommendations.append(
                f"Multiple classification systems referenced: {classification_systems}. Ensure consistent use."
            )

        response_criteria = []
        if "ELN 2022" in text:
            response_criteria.append("ELN 2022")
        if "ELN 2017" in text:
            response_criteria.append("ELN 2017")
        if "IWG 2003" in text:
            response_criteria.append("IWG 2003")
        if len(response_criteria) > 1:
            report.inconsistencies.append(
                f"Multiple response criteria versions: {response_criteria}"
            )

        ages_abstract = re.findall(r"(\d+)\s*years?", text[:1000])
        ages_methods = re.findall(
            r"(\d+)\s*years?",
            text[text.find("Methods") : text.find("Results")]
            if "Methods" in text
            else text,
        )
        if ages_abstract and ages_methods:
            if ages_abstract[0] != ages_methods[0]:
                report.inconsistencies.append(
                    f"Age criteria differ between Abstract ({ages_abstract[0]}) and Methods ({ages_methods[0]})"
                )

        sample_size_abstract = re.search(r"([\d,]+)\s+patients", text[:1000])
        sample_size_results = re.search(
            r"([\d,]+)\s+patients",
            text[text.find("Results") :] if "Results" in text else text,
        )
        if sample_size_abstract and sample_size_results:
            if sample_size_abstract.group(1).replace(
                ",", ""
            ) != sample_size_results.group(1).replace(",", ""):
                report.inconsistencies.append(
                    "Patient counts differ between Abstract and Results sections"
                )

        return report

    def generate_update_summary(self) -> str:
        if not self.update_history:
            return "No updates have been performed."

        lines = [
            "=" * 60,
            "MANUSCRIPT UPDATE SUMMARY",
            "=" * 60,
            f"Total Update Sessions: {len(self.update_history)}",
            "",
        ]

        for i, report in enumerate(self.update_history, 1):
            lines.append(f"Update #{i} ({report.update_timestamp})")
            lines.append(f"  Updates Made: {len(report.updates_made)}")
            lines.append(f"  Issues Found: {len(report.issues_found)}")
            lines.append(f"  Suggestions: {len(report.suggestions)}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)


if __name__ == "__main__":
    updater = ManuscriptUpdater()

    sample_text = """
    Patients with AML with NPM1 mutation were classified according to WHO 2016 criteria.
    BCR-ABL fusion was detected by FISH. The t(9;22) translocation was confirmed.
    """

    print("=" * 60)
    print("Testing Manuscript Updater")
    print("=" * 60)

    report = updater.update_classification_terminology(sample_text)

    print("\nOriginal Text:")
    print(sample_text)

    print("\nUpdated Text:")
    print(report.updated_text)

    print("\nUpdates Made:")
    for update in report.updates_made:
        print(
            f"  - {update['original']} → {update['replacement']} ({update['count']} occurrences)"
        )

    if report.issues_found:
        print("\nIssues Found:")
        for issue in report.issues_found:
            print(f"  ⚠️  {issue['issue']}")
            print(f"     Suggestion: {issue['suggestion']}")
