"""
NotebookLM Integration Module
=============================
Enables AI-powered research intelligence using NotebookLM with MCP (Model Context Protocol).
Integrates with WHO 2022, ICC 2022, ELN guidelines, NIH cGVHD criteria, and nomenclature references.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
from datetime import datetime


@dataclass
class ReferenceQuery:
    """Represents a query to NotebookLM reference notebooks."""

    query_text: str
    notebook_type: str  # 'classification', 'gvhd', 'therapeutic', 'nomenclature'
    context: Optional[str] = None
    max_sources: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text,
            "notebook_type": self.notebook_type,
            "context": self.context,
            "max_sources": self.max_sources,
        }


@dataclass
class NotebookLMResponse:
    """Represents a response from NotebookLM."""

    answer: str
    sources: List[Dict[str, str]]
    confidence: str  # 'high', 'medium', 'low'
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ClassificationEntity:
    """Represents a hematologic entity with classification info."""

    name: str
    who_definition: str
    icc_definition: str
    key_differences: List[str]
    diagnostic_criteria: List[str]
    molecular_markers: List[str]
    risk_stratification: Optional[str] = None


class NotebookLMIntegration:
    """
    MCP-based NotebookLM integration for hematology research intelligence.

    Manages 4 specialized notebooks:
    1. Classification (WHO 2022 + ICC 2022)
    2. GVHD (NIH cGVHD I-III)
    3. Therapeutic (ELN AML 2022 + ELN CML 2025)
    4. Nomenclature (ISCN 2024 + HGVS 2024)
    """

    REFERENCE_NOTEBOOKS = {
        "classification": {
            "name": "Hematologic Classifications",
            "sources": ["WHO_2022.pdf", "ICC_2022.pdf"],
            "description": "WHO 2022 and ICC 2022 classification systems",
            "topics": ["AML", "MDS", "MPN", "ALL", "CML", "lymphoma", "myeloma"],
            "notebook_id": "f47cebf8-a160-4980-8e38-69ddbe4a2712",
        },
        "gvhd": {
            "name": "cGVHD Guidelines",
            "sources": ["NIH_cGVHD_I.pdf", "NIH_cGVHD_II.pdf", "NIH_cGVHD_III.pdf"],
            "description": "NIH Consensus Development Project on chronic GVHD",
            "topics": [
                "diagnosis",
                "staging",
                "scoring",
                "response",
                "clinical trials",
            ],
            "notebook_id": "f47cebf8-a160-4980-8e38-69ddbe4a2712",
        },
        "therapeutic": {
            "name": "Therapeutic Guidelines",
            "sources": ["ELN_AML_2022.pdf", "ELN_CML_2025.pdf"],
            "description": "ELN recommendations for AML and CML",
            "topics": [
                "treatment",
                "risk stratification",
                "monitoring",
                "response criteria",
            ],
            "notebook_id": "f47cebf8-a160-4980-8e38-69ddbe4a2712",
        },
        "nomenclature": {
            "name": "Nomenclature Standards",
            "sources": ["ISCN 2024.pdf", "HGVS Nomenclature 2024.pdf"],
            "description": "ISCN 2024 and HGVS nomenclature standards",
            "topics": ["cytogenetics", "gene fusions", "mutations", "variant notation"],
            "notebook_id": "f47cebf8-a160-4980-8e38-69ddbe4a2712",
        },
    }

    SHARED_NOTEBOOK_ID = "f47cebf8-a160-4980-8e38-69ddbe4a2712"

    # Default reference path
    DEFAULT_REFERENCE_PATH = "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/References"

    def __init__(self, reference_path: Optional[str] = None):
        """
        Initialize NotebookLM integration.

        Args:
            reference_path: Path to reference PDFs. Defaults to Dropbox path.
        """
        self.reference_path = Path(reference_path or self.DEFAULT_REFERENCE_PATH)
        self.active_sessions: Dict[str, str] = {}  # notebook_type -> session_id
        self.query_history: List[Dict[str, Any]] = []

        # Verify reference files exist
        self._verify_references()

    def _verify_references(self) -> None:
        """Verify that reference files exist in the specified path."""
        if not self.reference_path.exists():
            raise FileNotFoundError(
                f"Reference path not found: {self.reference_path}\n"
                f"Please ensure Dropbox is accessible at /Users/kimhawk/Library/CloudStorage/Dropbox/"
            )

        missing_files = []
        for notebook_type, config in self.REFERENCE_NOTEBOOKS.items():
            for source in config["sources"]:
                source_path = self.reference_path / source
                if not source_path.exists():
                    missing_files.append(str(source_path))

        if missing_files:
            print(f"Warning: {len(missing_files)} reference files not found:")
            for f in missing_files[:5]:
                print(f"  - {f}")
            if len(missing_files) > 5:
                print(f"  ... and {len(missing_files) - 5} more")

    def initialize_notebook(self, notebook_type: str) -> bool:
        """
        Initialize a NotebookLM notebook with reference sources.

        Args:
            notebook_type: One of 'classification', 'gvhd', 'therapeutic', 'nomenclature'

        Returns:
            True if initialization successful
        """
        if notebook_type not in self.REFERENCE_NOTEBOOKS:
            raise ValueError(f"Unknown notebook type: {notebook_type}")

        config = self.REFERENCE_NOTEBOOKS[notebook_type]

        # In actual implementation, this would use MCP to:
        # 1. Create new notebook in NotebookLM
        # 2. Upload PDF sources
        # 3. Return session_id for queries

        # Placeholder for MCP integration
        print(f"Initializing '{config['name']}' notebook...")
        print(f"  Sources: {', '.join(config['sources'])}")

        # Simulate session creation
        session_id = (
            f"session_{notebook_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.active_sessions[notebook_type] = session_id

        return True

    def query_classification(
        self,
        entity_name: str,
        query_type: str = "comparison",  # 'comparison', 'definition', 'criteria'
    ) -> NotebookLMResponse:
        """
        Query classification notebook for entity information.

        Args:
            entity_name: Name of hematologic entity (e.g., "AML with NPM1 mutation")
            query_type: Type of information requested

        Returns:
            NotebookLMResponse with WHO 2022 vs ICC 2022 comparison
        """
        if "classification" not in self.active_sessions:
            self.initialize_notebook("classification")

        query = ReferenceQuery(
            query_text=f"What are the {query_type} differences between WHO 2022 and ICC 2022 for {entity_name}?",
            notebook_type="classification",
            context=f"Entity: {entity_name}",
        )

        return self._execute_query(query)

    def query_gvhd(
        self,
        aspect: str,  # 'diagnosis', 'staging', 'scoring', 'response'
        organ: Optional[str] = None,
    ) -> NotebookLMResponse:
        """
        Query GVHD notebook for NIH consensus criteria.

        Args:
            aspect: Aspect of GVHD to query
            organ: Specific organ system (skin, liver, GI, oral, etc.)

        Returns:
            NotebookLMResponse with NIH criteria
        """
        if "gvhd" not in self.active_sessions:
            self.initialize_notebook("gvhd")

        query_text = f"What are the NIH consensus criteria for {aspect}"
        if organ:
            query_text += f" of {organ}"
        query_text += " in chronic GVHD?"

        query = ReferenceQuery(
            query_text=query_text,
            notebook_type="gvhd",
            context=f"Aspect: {aspect}, Organ: {organ}",
        )

        return self._execute_query(query)

    def query_therapeutic(
        self,
        disease: str,  # 'AML', 'CML'
        topic: str,  # e.g., 'first-line treatment', 'risk stratification'
        eln_version: str = "2022",  # '2022' for AML, '2025' for CML
    ) -> NotebookLMResponse:
        """
        Query therapeutic notebook for ELN recommendations.

        Args:
            disease: Disease type ('AML' or 'CML')
            topic: Specific topic to query
            eln_version: ELN guideline version

        Returns:
            NotebookLMResponse with ELN recommendations
        """
        if "therapeutic" not in self.active_sessions:
            self.initialize_notebook("therapeutic")

        query = ReferenceQuery(
            query_text=f"What are the ELN {eln_version} recommendations for {topic} in {disease}?",
            notebook_type="therapeutic",
            context=f"Disease: {disease}, Topic: {topic}, Version: {eln_version}",
        )

        return self._execute_query(query)

    def query_nomenclature(
        self,
        notation: str,
        notation_type: str = "fusion",  # 'fusion', 'cytogenetic', 'mutation'
    ) -> NotebookLMResponse:
        """
        Query nomenclature notebook for correct notation.

        Args:
            notation: The notation to verify (e.g., "BCR-ABL", "t(9;22)")
            notation_type: Type of notation

        Returns:
            NotebookLMResponse with correct nomenclature
        """
        if "nomenclature" not in self.active_sessions:
            self.initialize_notebook("nomenclature")

        query = ReferenceQuery(
            query_text=f"What is the correct ISCN 2024 notation for {notation} ({notation_type})?",
            notebook_type="nomenclature",
            context=f"Notation: {notation}, Type: {notation_type}",
        )

        return self._execute_query(query)

    def verify_entity_classification(
        self, entity_name: str, proposed_classification: str
    ) -> Dict[str, Any]:
        """
        Verify if proposed classification matches WHO 2022 and ICC 2022.

        Args:
            entity_name: Name of the entity
            proposed_classification: Classification proposed by user

        Returns:
            Dictionary with verification results and recommendations
        """
        response = self.query_classification(entity_name, "comparison")

        # Analyze response for consistency
        verification = {
            "entity": entity_name,
            "proposed": proposed_classification,
            "who_match": None,
            "icc_match": None,
            "discrepancies": [],
            "recommendations": [],
            "sources": response.sources,
        }

        # In actual implementation, this would parse the AI response
        # to determine if proposed classification matches official criteria

        return verification

    def check_nomenclature_compliance(self, text: str) -> Dict[str, Any]:
        """
        Check text for nomenclature compliance against ISCN 2024 and HGVS.

        Args:
            text: Text to check

        Returns:
            Dictionary with compliance report
        """
        # Find potential nomenclature issues
        issues = []

        # Check for old fusion gene notation
        import re

        old_notations = re.findall(r"\b([A-Z][A-Z0-9]+[-/][A-Z][A-Z0-9]+)\b", text)

        for notation in old_notations:
            response = self.query_nomenclature(notation, "fusion")
            issues.append(
                {
                    "original": notation,
                    "correction": response.answer,
                    "explanation": "ISCN 2024: Use double colon notation",
                }
            )

        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "checked_at": datetime.now().isoformat(),
        }

    def _execute_query(self, query: ReferenceQuery) -> NotebookLMResponse:
        """
        Execute query against NotebookLM via MCP.

        Args:
            query: ReferenceQuery to execute

        Returns:
            NotebookLMResponse
        """
        # In actual implementation, this would:
        # 1. Use MCP client to send query to NotebookLM
        # 2. Retrieve AI-generated answer with sources
        # 3. Parse response into structured format

        # Placeholder implementation
        session_id = self.active_sessions.get(query.notebook_type)

        # Simulate query execution
        mock_response = NotebookLMResponse(
            answer=f"[MCP Placeholder] Query: {query.query_text}",
            sources=[
                {"source": "WHO_2022.pdf", "page": "N/A"},
                {"source": "ICC_2022.pdf", "page": "N/A"},
            ],
            confidence="medium",
            session_id=session_id,
        )

        # Log query
        self.query_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "query": query.to_dict(),
                "response": mock_response.to_dict(),
            }
        )

        return mock_response

    def get_notebook_status(self) -> Dict[str, Any]:
        """
        Get status of all reference notebooks.

        Returns:
            Dictionary with notebook initialization status
        """
        status = {}
        for notebook_type, config in self.REFERENCE_NOTEBOOKS.items():
            status[notebook_type] = {
                "name": config["name"],
                "initialized": notebook_type in self.active_sessions,
                "session_id": self.active_sessions.get(notebook_type),
                "sources": config["sources"],
                "topics": config["topics"],
            }
        return status

    def generate_setup_report(self) -> str:
        lines = ["=" * 60, "NOTEBOOKLM INTEGRATION STATUS", "=" * 60, ""]

        lines.append("🔗 SHARED NOTEBOOK")
        lines.append(f"   ID: {self.SHARED_NOTEBOOK_ID}")
        lines.append("   Status: ✅ Available for queries")
        lines.append("")

        for notebook_type, info in self.REFERENCE_NOTEBOOKS.items():
            lines.append(f"📚 {info['name']}")
            lines.append(f"   Sources: {len(info['sources'])} files")
            lines.append(
                f"   Status: {'✅ Initialized' if notebook_type in self.active_sessions else '⏳ Not initialized'}"
            )
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"Reference path: {self.reference_path}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def export_query_history(self, output_path: str) -> None:
        """
        Export query history to JSON file.

        Args:
            output_path: Path to save JSON file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "export_time": datetime.now().isoformat(),
                    "total_queries": len(self.query_history),
                    "queries": self.query_history,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )


class ResearchIntelligenceEngine:
    """
    High-level research intelligence engine combining NotebookLM with HPW phases.

    Provides intelligent assistance for:
    - Phase 0: Research Intelligence (query references)
    - Phase 1: Topic Development (validate research questions)
    - Phase 2: Research Design (check methodology against guidelines)
    - Phase 5: Publication Preparation (verify nomenclature)
    """

    def __init__(self, notebooklm: Optional[NotebookLMIntegration] = None):
        """
        Initialize research intelligence engine.

        Args:
            notebooklm: NotebookLM integration instance
        """
        self.notebooklm = notebooklm or NotebookLMIntegration()

    def validate_research_topic(
        self, disease_entity: str, study_type: str, population: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate research topic against current classifications and guidelines.

        Args:
            disease_entity: Disease/entity being studied
            study_type: Type of study (classification, GVHD, therapeutic)
            population: Study population if applicable

        Returns:
            Validation report with recommendations
        """
        validation = {
            "topic": f"{study_type} study of {disease_entity}",
            "classification_check": None,
            "guideline_alignment": None,
            "recommendations": [],
            "warnings": [],
        }

        # Query classification
        if study_type in ["classification", "diagnostic"]:
            classification_response = self.notebooklm.query_classification(
                disease_entity, "definition"
            )
            validation["classification_check"] = classification_response.to_dict()

        # Query therapeutic guidelines
        if study_type in ["therapeutic", "treatment"]:
            therapeutic_response = self.notebooklm.query_therapeutic(
                disease_entity.split()[0],  # Extract disease (AML, CML, etc.)
                "treatment",
            )
            validation["guideline_alignment"] = therapeutic_response.to_dict()

        return validation

    def check_manuscript_compliance(
        self, manuscript_text: str, manuscript_type: str = "research_article"
    ) -> Dict[str, Any]:
        """
        Check manuscript for nomenclature and classification compliance.

        Args:
            manuscript_text: Full manuscript text
            manuscript_type: Type of manuscript

        Returns:
            Compliance report
        """
        compliance = {
            "manuscript_type": manuscript_type,
            "nomenclature_check": None,
            "classification_check": None,
            "issues": [],
            "suggestions": [],
        }

        # Check nomenclature
        compliance["nomenclature_check"] = (
            self.notebooklm.check_nomenclature_compliance(manuscript_text)
        )

        return compliance


# ============================================================================
# Utility Functions
# ============================================================================


def initialize_all_notebooks(
    reference_path: Optional[str] = None,
) -> NotebookLMIntegration:
    """
    Initialize all reference notebooks.

    Args:
        reference_path: Path to reference PDFs

    Returns:
        Initialized NotebookLMIntegration instance
    """
    integration = NotebookLMIntegration(reference_path)

    for notebook_type in integration.REFERENCE_NOTEBOOKS.keys():
        print(f"\nInitializing {notebook_type} notebook...")
        integration.initialize_notebook(notebook_type)

    return integration


def get_quick_reference(entity_type: str, entity_name: str) -> str:
    """
    Get quick reference information for a specific entity.

    Args:
        entity_type: Type of entity ('classification', 'gvhd', 'therapeutic')
        entity_name: Name of entity

    Returns:
        Formatted reference string
    """
    integration = NotebookLMIntegration()

    if entity_type == "classification":
        response = integration.query_classification(entity_name)
    elif entity_type == "gvhd":
        response = integration.query_gvhd(entity_name)
    elif entity_type == "therapeutic":
        # Extract disease from entity_name
        disease = entity_name.split()[0] if " " in entity_name else entity_name
        response = integration.query_therapeutic(disease, entity_name)
    else:
        return f"Unknown entity type: {entity_type}"

    return response.answer


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("NotebookLM Integration Test")
    print("=" * 60)

    # Initialize integration
    try:
        integration = NotebookLMIntegration()

        # Check notebook status
        print("\nNotebook Status:")
        status = integration.get_notebook_status()
        for notebook_type, info in status.items():
            print(f"\n  {info['name']}:")
            print(f"    Initialized: {info['initialized']}")
            print(f"    Sources: {len(info['sources'])} files")

        # Test query
        print("\n" + "=" * 60)
        print("Testing Classification Query")
        print("=" * 60)

        response = integration.query_classification("AML with NPM1 mutation")
        print(f"\nQuery: AML with NPM1 mutation")
        print(f"Confidence: {response.confidence}")
        print(f"Sources: {len(response.sources)}")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nNote: This module requires Dropbox to be accessible.")
        print(
            "Reference path: /Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/References"
        )
