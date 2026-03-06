"""
Phase 1: Topic Development Module
PICO framework formulation and research question validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path
import re
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class LiteratureSeed:
    """A PubMed article candidate for the literature seed file."""

    pmid: str
    title: str
    authors: List[str]
    journal: str
    year: int
    abstract: str
    relevance_score: float = 0.0  # 0.0–1.0; computed from PICO overlap
    selected: bool = True          # user can deselect in manual review
    notebooklm_added: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LiteratureSeed":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class StudyType(Enum):
    """Types of hematology studies."""

    CLASSIFICATION = "classification"
    GVHD = "gvhd"
    THERAPEUTIC = "therapeutic"
    PROGNOSTIC = "prognostic"
    DIAGNOSTIC = "diagnostic"


@dataclass
class PICO:
    """PICO framework structure for research questions."""

    population: str = ""
    intervention: str = ""
    comparator: str = ""
    outcome: str = ""
    study_design: str = ""

    def is_complete(self) -> bool:
        """Check if all PICO elements are defined."""
        return all([self.population, self.intervention, self.comparator, self.outcome])

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "Population": self.population,
            "Intervention": self.intervention,
            "Comparator": self.comparator,
            "Outcome": self.outcome,
            "Study Design": self.study_design,
        }

    def format_research_question(self) -> str:
        """Format PICO into research question."""
        if not self.is_complete():
            return "[Incomplete PICO - all elements required]"

        return (
            f"In {self.population}, "
            f"does {self.intervention} "
            f"compared to {self.comparator} "
            f"result in {self.outcome}?"
        )


@dataclass
class ResearchTopic:
    """Complete research topic with PICO and metadata."""

    title: str = ""
    pico: PICO = field(default_factory=PICO)
    study_type: StudyType = StudyType.THERAPEUTIC
    disease_entity: str = ""
    keywords: List[str] = field(default_factory=list)
    clinical_significance: str = ""
    innovation_score: int = 0  # 1-10
    feasibility_score: int = 0  # 1-10

    def validate(self) -> Dict[str, Any]:
        """Validate research topic completeness."""
        issues = []

        if not self.title:
            issues.append("Title is required")

        if not self.pico.is_complete():
            issues.append("Complete PICO framework required")

        if not self.disease_entity:
            issues.append("Disease/entity must be specified")

        if len(self.keywords) < 3:
            issues.append("At least 3 keywords recommended")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "completeness": self._calculate_completeness(),
        }

    def _calculate_completeness(self) -> float:
        """Calculate topic completeness percentage."""
        required_fields = [
            self.title,
            self.pico.population,
            self.pico.intervention,
            self.pico.comparator,
            self.pico.outcome,
            self.disease_entity,
        ]

        filled = sum(1 for field in required_fields if field)
        return (filled / len(required_fields)) * 100


class TopicDevelopmentManager:
    """Manages research topic development and PICO formulation."""

    # Hematology-specific study design recommendations
    STUDY_DESIGNS = {
        StudyType.CLASSIFICATION: [
            "Retrospective cohort analysis",
            "Cross-sectional diagnostic study",
            "Multi-center registry analysis",
            "Validation cohort study",
        ],
        StudyType.GVHD: [
            "Prospective cohort study",
            "Retrospective chart review",
            "Case-control study",
            "Cross-sectional analysis",
        ],
        StudyType.THERAPEUTIC: [
            "Randomized controlled trial",
            "Single-arm phase II trial",
            "Retrospective cohort comparison",
            "Registry-based comparative study",
        ],
        StudyType.PROGNOSTIC: [
            "Retrospective cohort analysis",
            "Prospective validation study",
            "Multi-center registry study",
            "Survival analysis",
        ],
        StudyType.DIAGNOSTIC: [
            "Cross-sectional diagnostic accuracy study",
            "Prospective validation cohort",
            "Case-control diagnostic study",
            "Method comparison study",
        ],
    }

    # Disease entities for validation
    DISEASE_ENTITIES = {
        "AML": [
            "AML with NPM1 mutation",
            "AML with FLT3-ITD",
            "AML with TP53 mutation",
            "AML with RUNX1::RUNX1T1",
            "AML with CBFB::MYH11",
            "AML with PML::RARA",
            "AML with myelodysplasia-related changes",
            "Therapy-related AML",
        ],
        "MDS": [
            "MDS with single vs multilineage dysplasia",
            "MDS with excess blasts",
            "MDS with del(5q)",
            "MDS-EB1",
            "MDS-EB2",
        ],
        "MPN": [
            "Chronic myeloid leukemia (CML)",
            "Polycythemia vera (PV)",
            "Essential thrombocythemia (ET)",
            "Primary myelofibrosis (PMF)",
        ],
        "GVHD": [
            "Acute GVHD Grade I-IV",
            "Chronic GVHD Mild-Severe",
            "Steroid-refractory GVHD",
            "Overlap syndrome",
        ],
        "ALL": ["B-ALL", "T-ALL", "Ph+ ALL (BCR::ABL1+)", "KMT2A-rearranged ALL"],
    }

    # Disease-specific MeSH terms for PubMed queries
    DISEASE_MESH_TERMS: Dict[str, str] = {
        "AML": (
            '"Leukemia, Myeloid, Acute"[MeSH] OR "acute myeloid leukemia"[tiab] OR "AML"[tiab]'
        ),
        "MDS": (
            '"Myelodysplastic Syndromes"[MeSH] OR "myelodysplastic syndrome"[tiab] OR "MDS"[tiab]'
        ),
        "CML": (
            '"Leukemia, Myelogenous, Chronic, BCR-ABL Positive"[MeSH]'
            ' OR "chronic myeloid leukemia"[tiab] OR "CML"[tiab]'
        ),
        "GVHD": (
            '"Graft vs Host Disease"[MeSH] OR "graft-versus-host disease"[tiab] OR "GVHD"[tiab]'
        ),
        "ALL": (
            '"Precursor Cell Lymphoblastic Leukemia-Lymphoma"[MeSH]'
            ' OR "acute lymphoblastic leukemia"[tiab] OR "ALL"[tiab]'
        ),
        "MPN": (
            '"Myeloproliferative Disorders"[MeSH] OR "myeloproliferative neoplasm"[tiab] OR "MPN"[tiab]'
        ),
        "HCT": (
            '"Hematopoietic Stem Cell Transplantation"[MeSH]'
            ' OR "allogeneic transplantation"[tiab] OR "HSCT"[tiab] OR "HCT"[tiab]'
        ),
        "Lymphoma": (
            '"Lymphoma"[MeSH] OR "lymphoma"[tiab] OR "NHL"[tiab] OR "diffuse large B-cell"[tiab]'
        ),
        "Myeloma": (
            '"Multiple Myeloma"[MeSH] OR "multiple myeloma"[tiab] OR "plasma cell myeloma"[tiab]'
        ),
    }

    # Drug/intervention → MeSH terms
    INTERVENTION_MESH_TERMS: Dict[str, str] = {
        "venetoclax": '"venetoclax"[tiab] OR "ABT-199"[tiab] OR "Venclexta"[tiab]',
        "azacitidine": '"Azacitidine"[MeSH] OR "azacitidine"[tiab] OR "5-azacytidine"[tiab]',
        "decitabine": '"Decitabine"[MeSH] OR "decitabine"[tiab] OR "5-aza-2-deoxycytidine"[tiab]',
        "asciminib": '"asciminib"[tiab] OR "ABL001"[tiab] OR "STAMP inhibitor"[tiab]',
        "imatinib": '"Imatinib Mesylate"[MeSH] OR "imatinib"[tiab] OR "Gleevec"[tiab]',
        "dasatinib": '"Dasatinib"[MeSH] OR "dasatinib"[tiab] OR "BMS-354825"[tiab]',
        "nilotinib": '"Nilotinib"[MeSH] OR "nilotinib"[tiab] OR "Tasigna"[tiab]',
        "ponatinib": '"ponatinib"[tiab] OR "AP24534"[tiab] OR "Iclusig"[tiab]',
        "ruxolitinib": '"Ruxolitinib"[MeSH] OR "ruxolitinib"[tiab] OR "INCB018424"[tiab]',
        "gilteritinib": '"gilteritinib"[tiab] OR "ASP2215"[tiab] OR "Xospata"[tiab]',
        "midostaurin": '"midostaurin"[tiab] OR "PKC412"[tiab] OR "Rydapt"[tiab]',
        "glasdegib": '"glasdegib"[tiab] OR "PF-04449913"[tiab]',
        "enasidenib": '"enasidenib"[tiab] OR "AG-221"[tiab] OR "Idhifa"[tiab]',
        "ivosidenib": '"ivosidenib"[tiab] OR "AG-120"[tiab] OR "Tibsovo"[tiab]',
    }

    # Study type → PubMed publication type / filter
    STUDY_TYPE_PUBMED_FILTERS: Dict["StudyType", str] = {}  # populated post-class

    def __init__(self):
        """Initialize topic development manager."""
        self.current_topic: Optional[ResearchTopic] = None
        self.topic_history: List[ResearchTopic] = []
        # Defer filter dict population until StudyType enum is in scope
        if not TopicDevelopmentManager.STUDY_TYPE_PUBMED_FILTERS:
            TopicDevelopmentManager.STUDY_TYPE_PUBMED_FILTERS = {
                StudyType.THERAPEUTIC: (
                    'AND ("Randomized Controlled Trial"[pt] OR "Clinical Trial"[pt]'
                    ' OR "cohort"[tiab] OR "survival"[tiab])'
                ),
                StudyType.PROGNOSTIC: (
                    'AND ("prognosis"[MeSH] OR "survival analysis"[MeSH]'
                    ' OR "overall survival"[tiab] OR "prognostic factor"[tiab])'
                ),
                StudyType.DIAGNOSTIC: (
                    'AND ("Sensitivity and Specificity"[MeSH] OR "diagnostic accuracy"[tiab]'
                    ' OR "ROC"[tiab] OR "area under"[tiab])'
                ),
                StudyType.CLASSIFICATION: (
                    'AND ("classification"[tiab] OR "WHO 2022"[tiab] OR "ICC 2022"[tiab]'
                    ' OR "criteria"[tiab])'
                ),
                StudyType.GVHD: (
                    'AND ("Graft vs Host Disease"[MeSH] OR "GVHD response"[tiab]'
                    ' OR "steroid-refractory"[tiab])'
                ),
            }

    def create_pico(
        self,
        population: str,
        intervention: str,
        comparator: str,
        outcome: str,
        study_design: str = "",
    ) -> PICO:
        """
        Create PICO framework from components.

        Args:
            population: Study population
            intervention: Intervention or exposure
            comparator: Control or comparison group
            outcome: Primary outcome measure
            study_design: Proposed study design

        Returns:
            PICO object
        """
        return PICO(
            population=population,
            intervention=intervention,
            comparator=comparator,
            outcome=outcome,
            study_design=study_design,
        )

    def suggest_population(self, disease_entity: str) -> List[str]:
        """
        Suggest appropriate study populations for disease entity.

        Args:
            disease_entity: Disease or entity being studied

        Returns:
            List of suggested population descriptions
        """
        suggestions = []

        disease_upper = disease_entity.upper()

        if "AML" in disease_upper:
            suggestions = [
                "Adults ≥18 years with newly diagnosed AML",
                "AML patients receiving first-line induction chemotherapy",
                "Older adults (≥60 years) with AML unfit for intensive chemotherapy",
                "Pediatric AML patients (1-18 years)",
                "AML patients with adverse-risk cytogenetics",
            ]
        elif "MDS" in disease_upper:
            suggestions = [
                "Adults with newly diagnosed MDS",
                "MDS patients with IPSS-R intermediate or higher risk",
                "MDS patients with del(5q) cytogenetic abnormality",
            ]
        elif "GVHD" in disease_upper or "GVHD" in disease_upper:
            suggestions = [
                "Allogeneic HSCT recipients with chronic GVHD",
                "Patients with steroid-refractory acute GVHD",
                "Pediatric HSCT recipients with any grade GVHD",
            ]
        elif "CML" in disease_upper:
            suggestions = [
                "CML patients in chronic phase",
                "CML patients with treatment failure on first-line TKI",
                "CML patients with BCR::ABL1 kinase domain mutations",
            ]
        else:
            suggestions = [
                f"Patients with {disease_entity}",
                f"Adults diagnosed with {disease_entity}",
                f"Treatment-naive patients with {disease_entity}",
            ]

        return suggestions

    def suggest_interventions(
        self, disease_entity: str, study_type: StudyType
    ) -> List[str]:
        """Suggest appropriate interventions based on disease and study type."""
        suggestions = []

        if study_type == StudyType.THERAPEUTIC:
            if "AML" in disease_entity.upper():
                suggestions = [
                    "Venetoclax + azacitidine combination",
                    "Intensive 7+3 chemotherapy",
                    "Targeted therapy based on molecular profiling",
                    "Hypomethylating agent monotherapy",
                    "Clinical trial novel agent",
                ]
            elif "CML" in disease_entity.upper():
                suggestions = [
                    "Second-generation TKI (dasatinib, nilotinib)",
                    "Third-generation TKI (ponatinib)",
                    "Switch to alternative TKI after failure",
                    "Asciminib (STAMP inhibitor)",
                ]
            elif "GVHD" in disease_entity.upper():
                suggestions = [
                    "Ruxolitinib (JAK1/2 inhibitor)",
                    "Extracorporeal photopheresis (ECP)",
                    "Mesenchymal stromal cell therapy",
                    "Belumosudil (ROCK2 inhibitor)",
                    "Ibrutinib (BTK inhibitor)",
                ]

        elif study_type == StudyType.DIAGNOSTIC:
            suggestions = [
                "Next-generation sequencing panel",
                "Flow cytometry immunophenotyping",
                "FISH analysis for common translocations",
                "RT-PCR for fusion transcripts",
                "Multiplex ligation-dependent probe amplification (MLPA)",
            ]

        elif study_type == StudyType.PROGNOSTIC:
            suggestions = [
                "Molecular risk stratification",
                "Minimal residual disease (MRD) monitoring",
                "Measurable residual disease by flow cytometry",
                "NGS-based measurable residual disease",
            ]

        return suggestions or ["[Specify intervention based on research question]"]

    def suggest_outcomes(self, study_type: StudyType) -> List[str]:
        """Suggest appropriate outcome measures."""
        outcomes = {
            StudyType.THERAPEUTIC: [
                "Overall survival (OS) at 2 years",
                "Event-free survival (EFS)",
                "Complete remission (CR) rate",
                "Minimal residual disease negativity",
                "Treatment-related mortality",
                "Time to progression",
            ],
            StudyType.GVHD: [
                "GVHD response rate (CR+PR)",
                "Steroid-free response",
                "Failure-free survival",
                "Overall survival",
                "Quality of life scores (LEFS, FACT-BMT)",
                "GVHD-specific survival",
            ],
            StudyType.CLASSIFICATION: [
                "Diagnostic accuracy (sensitivity/specificity)",
                "Inter-observer agreement (kappa)",
                "Reclassification rate",
                "Prognostic discrimination (C-index)",
            ],
            StudyType.DIAGNOSTIC: [
                "Sensitivity and specificity",
                "Positive predictive value",
                "Negative predictive value",
                "Area under ROC curve",
                "Diagnostic odds ratio",
            ],
            StudyType.PROGNOSTIC: [
                "Overall survival",
                "Disease-free survival",
                "Cumulative incidence of relapse",
                "Non-relapse mortality",
                "Risk stratification accuracy",
            ],
        }

        return outcomes.get(study_type, ["[Specify primary outcome measure]"])

    def recommend_study_design(
        self,
        study_type: StudyType,
        feasibility: str = "moderate",  # 'high', 'moderate', 'low'
    ) -> List[str]:
        """
        Recommend study designs based on study type and feasibility.

        Args:
            study_type: Type of study
            feasibility: Resource/feasibility level

        Returns:
            List of recommended study designs
        """
        designs = self.STUDY_DESIGNS.get(study_type, [])

        if feasibility == "high":
            # Prioritize RCTs and prospective studies
            return [
                d for d in designs if "trial" in d.lower() or "prospective" in d.lower()
            ]
        elif feasibility == "low":
            # Prioritize retrospective and registry studies
            return [
                d
                for d in designs
                if "retrospective" in d.lower() or "registry" in d.lower()
            ]
        else:
            return designs

    def validate_disease_entity(self, entity: str) -> Dict[str, Any]:
        """
        Validate disease entity against WHO 2022 and ICC 2022.

        Args:
            entity: Disease entity name

        Returns:
            Validation results with recommendations
        """
        entity_upper = entity.upper()

        # Check against known entities
        found_category = None
        for category, entities in self.DISEASE_ENTITIES.items():
            if category in entity_upper:
                found_category = category
                break

        validation = {
            "is_valid": found_category is not None,
            "category": found_category,
            "suggested_entities": [],
            "recommendations": [],
        }

        if not found_category:
            validation["recommendations"].append(
                "Specify exact WHO 2022 or ICC 2022 entity name"
            )
        else:
            validation["suggested_entities"] = self.DISEASE_ENTITIES[found_category][:5]

        # Check nomenclature
        if "BCR-ABL" in entity or "BCR/ABL" in entity:
            validation["recommendations"].append(
                "Use ISCN 2024 notation: BCR::ABL1 (not BCR-ABL or BCR/ABL)"
            )

        return validation

    def generate_literature_search_strategy(
        self, topic: ResearchTopic
    ) -> Dict[str, Any]:
        """
        Generate a structured PubMed search strategy using MeSH terms.

        Produces a disease-anchored query with disease MeSH terms,
        intervention-specific terms, study-type publication filters,
        and a 10-year date filter — replacing the naive word-extraction
        approach that returned irrelevant results.

        Args:
            topic: Research topic with PICO

        Returns:
            Search strategy dict with MeSH query, full filtered query,
            and a NotebookLM query string for the NotebookLM-first step.
        """
        pico = topic.pico

        # ── 1. Disease / population block ────────────────────────────
        disease_block = self._build_disease_mesh_block(topic.disease_entity)

        # ── 2. Intervention block ─────────────────────────────────────
        intervention_block = self._build_intervention_block(pico.intervention)

        # ── 3. Outcome/comparator keywords (lightweight) ─────────────
        outcome_keywords = self._extract_outcome_keywords(pico.outcome)
        outcome_block = ""
        if outcome_keywords:
            outcome_block = " OR ".join(
                f'"{kw}"[tiab]' for kw in outcome_keywords[:3]
            )

        # ── 4. Assemble base query ────────────────────────────────────
        parts = [f"({disease_block})"]
        if intervention_block:
            parts.append(f"AND ({intervention_block})")
        if outcome_block:
            parts.append(f"AND ({outcome_block})")

        base_query = " ".join(parts)

        # ── 5. Publication-type filter from study type ────────────────
        pub_filter = self.STUDY_TYPE_PUBMED_FILTERS.get(topic.study_type, "")

        # ── 6. Date filter (last 10 years) ────────────────────────────
        date_filter = 'AND ("2015/01/01"[PDAT] : "3000"[PDAT])'

        # ── 7. English-only filter ────────────────────────────────────
        lang_filter = 'AND "English"[Language]'

        full_query = f"{base_query} {pub_filter} {date_filter} {lang_filter}".strip()

        # ── 8. NotebookLM query (natural language for AI search) ──────
        notebooklm_query = (
            f"{topic.disease_entity or pico.population}: "
            f"{pico.intervention} vs {pico.comparator}, "
            f"outcome: {pico.outcome}, study type: {topic.study_type.value}"
        )

        return {
            "disease_block": disease_block,
            "intervention_block": intervention_block,
            "outcome_keywords": outcome_keywords,
            "base_query": base_query,
            "publication_type_filter": pub_filter,
            "date_filter": date_filter,
            "full_query": full_query,
            "notebooklm_query": notebooklm_query,
            "expected_results": "20-150",
        }

    def _build_disease_mesh_block(self, disease_entity: str) -> str:
        """Return a MeSH-anchored disease query block."""
        if not disease_entity:
            return '"hematologic neoplasms"[MeSH]'

        entity_upper = disease_entity.upper()
        for key, mesh_str in self.DISEASE_MESH_TERMS.items():
            if key in entity_upper:
                # Append the verbatim entity if it's specific enough (e.g. "AML with NPM1")
                if len(disease_entity) > len(key) + 2:
                    extra = f' OR "{disease_entity}"[tiab]'
                    return f"({mesh_str}{extra})"
                return f"({mesh_str})"

        # Fallback: quote the entity as a title/abstract phrase
        return f'"{disease_entity}"[tiab]'

    def _build_intervention_block(self, intervention: str) -> str:
        """Return a drug/intervention MeSH query block, or empty string."""
        if not intervention:
            return ""

        intervention_lower = intervention.lower()
        for drug, mesh_str in self.INTERVENTION_MESH_TERMS.items():
            if drug in intervention_lower:
                return f"({mesh_str})"

        # No pre-built template — fall back to quoted phrase
        clean = re.sub(r"\s+", " ", intervention).strip()
        if clean:
            return f'"{clean}"[tiab]'
        return ""

    def _extract_outcome_keywords(self, outcome_text: str) -> List[str]:
        """Extract 1-3 meaningful outcome keywords (avoids stop words)."""
        stop_words = {
            "with", "and", "or", "the", "of", "in", "for", "to", "a", "an",
            "at", "by", "rate", "years", "year", "months",
        }
        # Prefer known clinical endpoint abbreviations
        known = re.findall(
            r"\b(OS|EFS|DFS|RFS|CR|CRi|MRD|ORR|PFS|TRM|NRM|GVHD)\b",
            outcome_text,
        )
        if known:
            return known[:3]

        words = re.findall(r"\b[A-Za-z][A-Za-z0-9\-]+\b", outcome_text)
        return [w for w in words if w.lower() not in stop_words and len(w) > 3][:3]

    def export_topic_summary(self, topic: ResearchTopic) -> str:
        """Export topic as formatted summary."""
        lines = [
            "# Research Topic Summary",
            "",
            f"**Title:** {topic.title}",
            f"**Study Type:** {topic.study_type.value}",
            f"**Disease Entity:** {topic.disease_entity}",
            "",
            "## PICO Framework",
            "",
        ]

        for element, value in topic.pico.to_dict().items():
            lines.append(f"- **{element}:** {value}")

        lines.extend(
            [
                "",
                "## Research Question",
                f"{topic.pico.format_research_question()}",
                "",
                "## Keywords",
                ", ".join(topic.keywords) if topic.keywords else "[To be defined]",
            ]
        )

        if topic.clinical_significance:
            lines.extend(["", "## Clinical Significance", topic.clinical_significance])

        return "\n".join(lines)
    # ── Persistence ──────────────────────────────────────────────────────────

    def save_project_topic(self, project_dir, nlm_block: Optional[Dict] = None) -> Path:
        """
        Persist the current ResearchTopic to <project_dir>/research_topic.json.

        Downstream phases (2, 3, 4) load this file to avoid re-entry of PICO.
        If ``nlm_block`` is provided it is written under the "nlm" key; otherwise
        any existing "nlm" block in the file is preserved.

        Returns:
            Path to the saved file.
        Raises:
            ValueError: if no current_topic is set.
        """
        if not self.current_topic:
            raise ValueError("No current_topic to save. Call create_pico() first.")

        project_dir = Path(project_dir)
        project_dir.mkdir(parents=True, exist_ok=True)
        out = project_dir / "research_topic.json"

        # Preserve existing nlm block when none supplied
        existing_nlm: Dict = {}
        if out.exists():
            try:
                existing_nlm = json.loads(out.read_text()).get("nlm", {})
            except Exception:
                pass

        topic = self.current_topic
        data = {
            "title": topic.title,
            "study_type": topic.study_type.value,
            "disease_entity": topic.disease_entity,
            "keywords": topic.keywords,
            "clinical_significance": topic.clinical_significance,
            "innovation_score": topic.innovation_score,
            "feasibility_score": topic.feasibility_score,
            "pico": topic.pico.to_dict(),
            "nlm": nlm_block if nlm_block is not None else existing_nlm,
        }
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info("ResearchTopic saved → %s", out)
        return out

    @staticmethod
    def load_nlm_block(project_dir) -> Dict:
        """
        Read the ``nlm`` block from research_topic.json without reconstructing
        a ResearchTopic.  Returns {} if the file doesn't exist or has no nlm key.
        """
        path = Path(project_dir) / "research_topic.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text()).get("nlm", {})
        except Exception:
            return {}

    @classmethod
    def load_project_topic(cls, project_dir) -> Optional["ResearchTopic"]:
        """
        Load a previously saved ResearchTopic from <project_dir>/research_topic.json.

        Returns:
            ResearchTopic if the file exists, else None.
        """
        path = Path(project_dir) / "research_topic.json"
        if not path.exists():
            return None

        data = json.loads(path.read_text())
        pico_data = data.get("pico", {})
        pico = PICO(
            population=pico_data.get("Population", ""),
            intervention=pico_data.get("Intervention", ""),
            comparator=pico_data.get("Comparator", ""),
            outcome=pico_data.get("Outcome", ""),
            study_design=pico_data.get("Study Design", ""),
        )
        study_type_val = data.get("study_type", StudyType.THERAPEUTIC.value)
        study_type = next(
            (st for st in StudyType if st.value == study_type_val),
            StudyType.THERAPEUTIC,
        )
        return ResearchTopic(
            title=data.get("title", ""),
            pico=pico,
            study_type=study_type,
            disease_entity=data.get("disease_entity", ""),
            keywords=data.get("keywords", []),
            clinical_significance=data.get("clinical_significance", ""),
            innovation_score=data.get("innovation_score", 0),
            feasibility_score=data.get("feasibility_score", 0),
        )

    @staticmethod
    def save_literature_seed(
        articles: List[LiteratureSeed],
        project_dir,
        selected_only: bool = False,
    ) -> Path:
        """
        Save PubMed search results to <project_dir>/literature_seed.json.

        Phase 4 (draft generation) loads this file to build the reference
        pool and background section without another PubMed query.

        Args:
            articles: List of LiteratureSeed entries from the search.
            project_dir: Project output directory.
            selected_only: If True, only write user-selected articles.

        Returns:
            Path to the saved file.
        """
        project_dir = Path(project_dir)
        project_dir.mkdir(parents=True, exist_ok=True)
        out = project_dir / "literature_seed.json"

        to_save = [a for a in articles if a.selected] if selected_only else articles
        out.write_text(
            json.dumps([a.to_dict() for a in to_save], indent=2, ensure_ascii=False)
        )
        logger.info(
            "Literature seed saved → %s (%d articles)", out, len(to_save)
        )
        return out

    @staticmethod
    def load_literature_seed(project_dir) -> List[LiteratureSeed]:
        """Load literature_seed.json if it exists, else return empty list."""
        path = Path(project_dir) / "literature_seed.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text())
        return [LiteratureSeed.from_dict(d) for d in data]

    def load_protocol(self, protocol_path: str, project_dir: str) -> dict:
        """
        Load a clinical study protocol and auto-populate PICO fields.

        Args:
            protocol_path: Path to protocol DOCX or PDF.
            project_dir: HPW project directory (output folder).

        Returns:
            Extraction summary dict with keys:
            background_found, methods_found, sap_found,
            reference_count, verified_count, warnings, sap_params.
        """
        from tools.protocol_parser import ProtocolParser

        parser = ProtocolParser(project_dir)
        result = parser.load_and_extract(
            protocol_path,
            import_refs=True,
            verify_refs=True,
            verbose=True,
        )

        # Ensure current_topic exists
        if self.current_topic is None:
            self.current_topic = ResearchTopic()
        topic = self.current_topic

        # Auto-populate PICO from extraction
        if result.sap_params.primary_endpoint and not topic.pico.outcome:
            topic.pico.outcome = result.sap_params.primary_endpoint

        # Population: extract first inclusion criterion from methods seed
        if not topic.pico.population and result.methods_seed:
            inc_match = re.search(
                r"### Inclusion Criteria\s*\n+(.*?)(?:\n\n|\Z)",
                result.methods_seed, re.DOTALL
            )
            if inc_match:
                first_line = inc_match.group(1).strip().splitlines()[0]
                first_criterion = first_line.strip(" -•·1234567890.")
                if first_criterion and len(first_criterion) > 5:
                    topic.pico.population = first_criterion

        # Intervention: drug/agent keywords detected in protocol text
        if not topic.pico.intervention and result.disease_keywords:
            drug_agents = [
                kw for kw in result.disease_keywords if kw.lower() in {
                    "venetoclax", "azacitidine", "decitabine", "asciminib", "imatinib",
                    "dasatinib", "ponatinib", "ruxolitinib", "gilteritinib", "midostaurin",
                }
            ]
            if drug_agents:
                topic.pico.intervention = drug_agents[0]

        if result.study_type:
            # Map study type to StudyType enum
            type_map = {
                "RCT": StudyType.THERAPEUTIC,
                "Observational": StudyType.PROGNOSTIC,
                "Case Report": StudyType.DIAGNOSTIC,
            }
            topic.study_type = type_map.get(result.study_type, StudyType.THERAPEUTIC)

        if result.disease_keywords and not topic.disease_entity:
            topic.disease_entity = result.disease_keywords[0]

        return {
            "background_found": "[NOT FOUND IN PROTOCOL]" not in result.background_seed,
            "methods_found": "[NOT FOUND IN PROTOCOL]" not in result.methods_seed,
            "sap_found": "[SAP SECTION NOT FOUND" not in result.statistical_methods_seed,
            "reference_count": len(result.references),
            "verified_count": sum(1 for r in result.references if r.verified),
            "study_type": result.study_type,
            "reporting_guideline": result.reporting_guideline,
            "sap_params": result.sap_params,
            "warnings": result.warnings,
        }



# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1: Topic Development Module")
    print("=" * 60)

    # Example usage
    manager = TopicDevelopmentManager()

    # Create PICO for AML study
    pico = manager.create_pico(
        population="Adults ≥60 years with newly diagnosed AML",
        intervention="Venetoclax + azacitidine",
        comparator="Intensive 7+3 chemotherapy",
        outcome="Overall survival at 2 years",
        study_design="Retrospective cohort comparison",
    )

    print("\nPICO Framework:")
    for element, value in pico.to_dict().items():
        print(f"  {element}: {value}")

    print(f"\nResearch Question:")
    print(f"  {pico.format_research_question()}")

    # Suggest populations
    print("\nSuggested Populations for AML:")
    for i, pop in enumerate(manager.suggest_population("AML"), 1):
        print(f"  {i}. {pop}")

    # Validate entity
    validation = manager.validate_disease_entity("AML with NPM1 mutation")
    print(f"\nValidation: {'✅ Valid' if validation['is_valid'] else '❌ Invalid'}")
    if validation["recommendations"]:
        print("Recommendations:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")


# ── Scientific Skills Integration (additive, opt-in) ──────────────────────────


def _resolve_project_notebook(nlm, topic, project_dir, ask_user_fn=None):
    """
    Resolve the project NLM notebook, reusing an existing one when possible.

    Resolution order:
    1. Existing notebook_id in research_topic.json → verify alive → reuse
    2. Name-pattern search → user confirmation → adopt
    3. Create new notebook

    Parameters
    ----------
    nlm          : NotebookLMIntegration instance (already health-checked)
    topic        : ResearchTopic (provides disease_entity and pico.intervention)
    project_dir  : Path to project directory
    ask_user_fn  : Optional callable(prompt: str) -> str for interactive prompts.
                   Defaults to input() in CLI mode.

    Returns
    -------
    str or None
        Notebook ID string, or None if creation failed.
    """
    import datetime

    if ask_user_fn is None:
        ask_user_fn = input  # CLI default

    disease = getattr(topic, "disease_entity", "") or ""
    pico = getattr(topic, "pico", None)
    intervention = getattr(pico, "intervention", "") if pico else ""
    prefix = f"HPW-{disease}-{intervention}"

    # Step 1: check persisted notebook_id
    nlm_block = TopicDevelopmentManager.load_nlm_block(project_dir)
    existing_id = nlm_block.get("notebook_id")
    if existing_id:
        if nlm.get_notebook(existing_id):
            logger.info("Reusing existing NLM notebook: %s", existing_id)
            return existing_id
        logger.info("Stored notebook_id %s not found; searching by name", existing_id)

    # Step 2: name-pattern search
    found = nlm.find_by_name(prefix)
    if found:
        try:
            answer = ask_user_fn(
                f"Found NLM note '{found.get('name', found.get('id', ''))}'. Use it? [y/N]: "
            ).strip().lower()
        except Exception:
            answer = "n"
        if answer in ("y", "yes"):
            logger.info("Adopting existing NLM notebook: %s", found.get("id"))
            return found.get("id")

    # Step 3: create new notebook
    year = datetime.datetime.utcnow().year
    name = f"HPW-{disease}-{intervention}-{year}"
    notebook_id = nlm.create_notebook(
        name=name,
        description=f"Literature for HPW project: {disease} / {intervention}",
    )
    if notebook_id:
        logger.info("Created new NLM notebook '%s': %s", name, notebook_id)
    return notebook_id


def integrate_skills_phase1(
    project_name: str,
    project_dir,
    topic: str,
    disease: str = "",
    intervention: str = "",
    brainstorm_method: str = "free",
    max_pubmed_results: int = 50,
    manual_selection: bool = False,
    ask_user_fn=None,
) -> Dict[str, Any]:
    """
    Phase 1 pipeline orchestrator: NotebookLM → PubMed → literature_seed → persist.

    Execution order (per CLAUDE.md data-source priority):
      1. Query NotebookLM for existing curated knowledge on the topic.
      2. If NotebookLM is unavailable or returns sparse results, fall back to
         PubMed using MeSH-anchored queries built from the PICO.
      3. Score each PubMed article for PICO relevance.
      4. Save results to literature_seed.json (all articles; user can later
         deselect in the UI before the seed is locked for Phase 4).
      5. Create a project-specific NotebookLM notebook and add PubMed article
         URLs as sources (enables NotebookLM AI-powered queries in Phase 4).
      6. Save research_topic.json so Phase 2/3/4 can load PICO without re-entry.
      7. Run HypothesisGenerator, ScientificBrainstormer, ResearchLookup,
         persist SkillContext as before.

    Args:
        project_name: Manuscript project name.
        project_dir: HPW project directory (output folder).
        topic: Research topic string.
        disease: Disease type — "aml", "cml", "mds", "hct", etc.
        intervention: Primary intervention (optional).
        brainstorm_method: "scamper" | "six_hats" | "free".
        max_pubmed_results: Maximum PubMed articles to retrieve (default 50).
        manual_selection: If True, all articles start with selected=False so
            the user must explicitly choose in the UI. If False, all start
            selected=True (auto-include) and can be deselected.

    Returns:
        Summary dict with keys: notebooklm_used, pubmed_count, seed_path,
        topic_path, notebook_id, warnings.
    """
    result: Dict[str, Any] = {
        "notebooklm_used": False,
        "pubmed_count": 0,
        "seed_path": None,
        "topic_path": None,
        "notebook_id": None,
        "warnings": [],
    }

    project_dir = Path(project_dir)

    # ── Build/load ResearchTopic ──────────────────────────────────────────────
    mgr = TopicDevelopmentManager()
    saved_topic = TopicDevelopmentManager.load_project_topic(project_dir)
    if saved_topic:
        mgr.current_topic = saved_topic
    else:
        mgr.current_topic = ResearchTopic(
            title=topic,
            disease_entity=disease.upper() if disease else "",
        )

    current_topic = mgr.current_topic

    # Build search strategy using MeSH terms
    strategy = mgr.generate_literature_search_strategy(current_topic)

    # ── Step 1: NotebookLM first ──────────────────────────────────────────────
    notebooklm_context = ""
    try:
        from tools.notebooklm_integration import NotebookLMIntegration

        nlm = NotebookLMIntegration()
        if nlm.health_check():
            nlm_answer = nlm.ask(strategy["notebooklm_query"])
            if nlm_answer and len(nlm_answer) > 100:
                notebooklm_context = nlm_answer
                result["notebooklm_used"] = True
                logger.info("NotebookLM returned context (%d chars)", len(nlm_answer))
            else:
                result["warnings"].append(
                    "NotebookLM returned sparse results; proceeding with PubMed."
                )
    except Exception as exc:
        result["warnings"].append(f"NotebookLM unavailable: {exc}")

    # ── Step 2: PubMed search with MeSH query ─────────────────────────────────
    literature_seeds: List[LiteratureSeed] = []
    try:
        from tools.draft_generator.pubmed_searcher import PubMedSearcher

        searcher = PubMedSearcher()
        articles = searcher.search(
            query=strategy["full_query"],
            max_results=max_pubmed_results,
        )

        for art in articles:
            seed = LiteratureSeed(
                pmid=getattr(art, "pmid", "") or "",
                title=getattr(art, "title", "") or "",
                authors=getattr(art, "authors", []) or [],
                journal=getattr(art, "journal", "") or "",
                year=int(getattr(art, "year", 0) or 0),
                abstract=getattr(art, "abstract", "") or "",
                selected=not manual_selection,
            )
            # Simple relevance score: count PICO keyword matches in title+abstract
            seed.relevance_score = _score_pico_relevance(seed, current_topic)
            literature_seeds.append(seed)

        # Sort by relevance descending
        literature_seeds.sort(key=lambda s: s.relevance_score, reverse=True)
        result["pubmed_count"] = len(literature_seeds)
        logger.info("PubMed returned %d articles", len(literature_seeds))

    except Exception as exc:
        result["warnings"].append(f"PubMed search failed: {exc}")

    # ── Step 3: Resolve or create project NLM notebook; add selected sources ──
    nlm_block: Dict[str, Any] = {}
    try:
        from tools.notebooklm_integration import NotebookLMIntegration
        import datetime

        nlm = NotebookLMIntegration()
        if nlm.health_check():
            notebook_id = _resolve_project_notebook(
                nlm=nlm,
                topic=current_topic,
                project_dir=project_dir,
                ask_user_fn=ask_user_fn,
            )
            if notebook_id:
                result["notebook_id"] = notebook_id
                # Add only selected articles
                selected_seeds = [s for s in literature_seeds if s.selected and s.pmid]
                added = 0
                pmids_added: List[str] = []
                for seed in selected_seeds:
                    if nlm.add_source_pmid(notebook_id, seed.pmid):
                        seed.notebooklm_added = True
                        pmids_added.append(seed.pmid)
                        added += 1
                logger.info(
                    "NLM notebook '%s': %d selected sources added",
                    notebook_id, added,
                )
                # Build nlm_block for persistence
                disease = current_topic.disease_entity or ""
                interv = getattr(current_topic.pico, "intervention", "") if current_topic.pico else ""
                year = datetime.datetime.utcnow().year
                nlm_block = {
                    "notebook_id": notebook_id,
                    "notebook_name": f"HPW-{disease}-{interv}-{year}",
                    "pmids_added": pmids_added,
                    "last_synced": datetime.datetime.utcnow().isoformat(),
                }
    except Exception as exc:
        result["warnings"].append(f"NLM notebook resolution failed: {exc}")

    # ── Step 4: Persist literature_seed.json ──────────────────────────────────
    if literature_seeds:
        try:
            seed_path = TopicDevelopmentManager.save_literature_seed(
                literature_seeds, project_dir
            )
            result["seed_path"] = str(seed_path)
        except Exception as exc:
            result["warnings"].append(f"literature_seed save failed: {exc}")

    # ── Step 5: Persist research_topic.json (includes nlm block) ─────────────
    try:
        topic_path = mgr.save_project_topic(project_dir, nlm_block=nlm_block or None)
        result["topic_path"] = str(topic_path)
    except Exception as exc:
        result["warnings"].append(f"research_topic save failed: {exc}")

    # ── Step 6: SkillContext pipeline (unchanged behavior) ────────────────────
    try:
        from tools.skills import SkillContext, HypothesisGenerator, ScientificBrainstormer, ResearchLookup

        ctx = SkillContext.load(project_name, project_dir)
        if notebooklm_context:
            ctx.background_seed = notebooklm_context

        ctx.hypotheses = HypothesisGenerator(context=ctx).generate(
            topic=topic, disease=disease, intervention=intervention
        )
        ScientificBrainstormer(context=ctx).brainstorm(
            topic=topic, method=brainstorm_method, disease=disease
        )
        ResearchLookup(context=ctx).lookup(query=f"{disease} {topic}".strip())
        ctx.save(project_dir)
    except Exception as exc:
        result["warnings"].append(f"SkillContext pipeline failed: {exc}")

    return result


def _score_pico_relevance(seed: LiteratureSeed, topic: ResearchTopic) -> float:
    """
    Score a PubMed article's relevance to the PICO (0.0–1.0).

    Counts how many PICO keywords appear in the title + abstract,
    normalized to 1.0. Used to rank articles before user manual selection.
    """
    text = f"{seed.title} {seed.abstract}".lower()
    pico = topic.pico
    keywords = [
        w.lower() for phrase in [
            pico.population, pico.intervention, pico.comparator,
            pico.outcome, topic.disease_entity,
        ]
        for w in re.findall(r"\b[A-Za-z][A-Za-z0-9\-]+\b", phrase or "")
        if len(w) > 3 and w.lower() not in {
            "with", "and", "the", "for", "that", "this", "from",
        }
    ]
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw in text)
    return round(min(hits / len(keywords), 1.0), 3)


def integrate_skills_phase1_classification(
    project_name: str,
    project_dir,
    topic: str,
    disease: str = "",
) -> None:
    """
    Detect disease context from topic string and pre-populate
    classification_result["disease"] in SkillContext.

    Runs after integrate_skills_phase1(). Fails silently.

    Args:
        project_name: Manuscript project name
        project_dir: Project directory (Path or str)
        topic: Research topic string used for disease auto-detection
        disease: Explicit disease override (skips auto-detection if provided)
    """
    try:
        import re
        from pathlib import Path
        from tools.skills import SkillContext, ClassificationValidator

        ctx = SkillContext.load(project_name, Path(project_dir))

        detected = disease.upper().strip() if disease else ""
        if not detected:
            _DISEASE_PATTERNS = {
                "AML": r"\baml\b|acute myeloid|acute myelogenous",
                "CML": r"\bcml\b|chronic myeloid|chronic myelogenous",
                "MDS": r"\bmds\b|myelodysplastic",
                "HCT": r"\bhct\b|hematopoietic cell transplant|bone marrow transplant|allogeneic",
                "GVHD": r"\bgvhd\b|graft.versus.host",
                "ALL": r"\ball\b|acute lymphoblastic",
                "Myeloma": r"myeloma|plasma cell",
                "Lymphoma": r"lymphoma",
            }
            topic_lower = topic.lower()
            for disease_key, pattern in _DISEASE_PATTERNS.items():
                if re.search(pattern, topic_lower):
                    detected = disease_key
                    break

        if detected:
            ctx.classification_result["disease"] = detected

        ClassificationValidator(context=ctx).invoke(
            f"Disease context detected: {detected or 'unknown'}"
        )
        ctx.save(Path(project_dir))

    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "Phase 1 classification skill integration failed: %s", exc
        )
