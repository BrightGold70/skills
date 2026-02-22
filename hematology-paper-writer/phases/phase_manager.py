"""
Phase Manager Module
Core component for tracking manuscript preparation workflow through phases.
Implements phase state management, transition logic, and milestone tracking.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime
import json
import os
from pathlib import Path


class ManuscriptPhase(Enum):
    """Enumeration of manuscript preparation phases."""

    TOPIC_SELECTION = "1"  # Phase 1: Topic Selection and Conceptual Development
    RESEARCH_DESIGN = "2"  # Phase 2: Deep Research and Data Collection
    JOURNAL_STRATEGY = "3"  # Phase 3: Journal Selection and Strategy
    MANUSCRIPT_PREP = "4"  # Phase 4: Manuscript Preparation and Structure
    MANUSCRIPT_UPDATING = "4.5"  # Phase 4.5: Manuscript Updating and Editing
    PUBMED_CONCORDANCE = "4.6"  # Phase 4.6: PubMed Reference Concordance Verification
    ACADEMIC_PROSE = "4.7"  # Phase 4.7: Academic Writing Style and Prose Development
    PRE_SUBMISSION = "5"  # Phase 5: Pre-Submission Review and Quality Assurance
    SUBMISSION_PROCESS = "6_7"  # Phases 6-7: Submission Process
    PEER_REVIEW = "8"  # Phase 8: Peer Review and Revision
    POST_ACCEPTANCE = "9"  # Phase 9: Post-Acceptance and Publication
    RESUBMISSION = "10"  # Phase 10: Rejection and Resubmission
    COMPLETED = "completed"  # Manuscript successfully published


@dataclass
class PhaseMilestone:
    """Represents a milestone within a phase."""

    name: str
    description: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    notes: str = ""

    def mark_completed(self, notes: str = ""):
        """Mark this milestone as completed."""
        self.completed = True
        self.completed_at = datetime.now()
        if notes:
            self.notes = notes


@dataclass
class PhaseState:
    """Represents the state of a manuscript preparation phase."""

    phase: ManuscriptPhase
    entered_at: datetime = field(default_factory=datetime.now)
    milestones: List[PhaseMilestone] = field(default_factory=list)
    completed: bool = False
    completed_at: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def get_completion_percentage(self) -> float:
        """Calculate percentage of completed milestones."""
        if not self.milestones:
            return 0.0
        completed = sum(1 for m in self.milestones if m.completed)
        return (completed / len(self.milestones)) * 100

    def add_milestone(self, name: str, description: str) -> PhaseMilestone:
        """Add a new milestone to this phase."""
        milestone = PhaseMilestone(name=name, description=description)
        self.milestones.append(milestone)
        return milestone


@dataclass
class ManuscriptMetadata:
    """Metadata about the manuscript being developed."""

    title: str = ""
    topic: str = ""
    target_journal: str = ""
    manuscript_type: str = ""  # systematic_review, clinical_trial, case_report, etc.
    authors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)


class PhaseManager:
    """
    Manages manuscript preparation workflow through phases.
    Tracks progress, manages transitions, and provides phase-specific guidance.
    """

    # Define milestones for each phase
    PHASE_MILESTONES: Dict[ManuscriptPhase, List[Dict[str, str]]] = {
        ManuscriptPhase.TOPIC_SELECTION: [
            {
                "name": "topic_identified",
                "description": "Research topic identified and scoped",
            },
            {
                "name": "literature_reviewed",
                "description": "Preliminary literature analysis completed",
            },
            {
                "name": "research_question_defined",
                "description": "Research question/hypothesis formulated",
            },
            {
                "name": "feasibility_assessed",
                "description": "Feasibility and resources assessed",
            },
        ],
        ManuscriptPhase.RESEARCH_DESIGN: [
            {
                "name": "study_design_selected",
                "description": "Study design selected and justified",
            },
            {
                "name": "methodology_documented",
                "description": "Methodology documented in detail",
            },
            {
                "name": "data_collection_planned",
                "description": "Data collection procedures defined",
            },
            {
                "name": "statistical_analysis_planned",
                "description": "Statistical analysis plan finalized",
            },
            {
                "name": "ethical_compliance_addressed",
                "description": "IRB/ethics approval obtained or planned",
            },
        ],
        ManuscriptPhase.JOURNAL_STRATEGY: [
            {
                "name": "journals_evaluated",
                "description": "Potential target journals evaluated",
            },
            {
                "name": "journal_scope_matched",
                "description": "Manuscript matched to journal scope",
            },
            {
                "name": "requirements_understood",
                "description": "Journal requirements and policies understood",
            },
            {
                "name": "target_journal_selected",
                "description": "Target journal selected and justified",
            },
        ],
        ManuscriptPhase.MANUSCRIPT_PREP: [
            {
                "name": "title_abstract_drafted",
                "description": "Title and abstract developed",
            },
            {
                "name": "introduction_written",
                "description": "Introduction section completed",
            },
            {
                "name": "methods_documented",
                "description": "Methods section fully documented",
            },
            {
                "name": "results_presented",
                "description": "Results section with data presented",
            },
            {
                "name": "discussion_interpreted",
                "description": "Discussion interpreting findings completed",
            },
            {
                "name": "supporting_elements_prepared",
                "description": "Figures, tables, and references prepared",
            },
        ],
        ManuscriptPhase.MANUSCRIPT_UPDATING: [
            {
                "name": "content_edited",
                "description": "Content edited for clarity and accuracy",
            },
            {
                "name": "literature_integrated",
                "description": "New literature integrated and references updated",
            },
            {
                "name": "comprehensive_revision",
                "description": "Comprehensive manuscript revision completed",
            },
            {
                "name": "structural_rechecked",
                "description": "Structure and quality rechecked",
            },
        ],
        ManuscriptPhase.PUBMED_CONCORDANCE: [
            {
                "name": "references_extracted",
                "description": "All references extracted and counted",
            },
            {
                "name": "pmid_assigned",
                "description": "PMID assigned to all cited references",
            },
            {
                "name": "missing_identified",
                "description": "Missing references identified and documented",
            },
            {
                "name": "replacements_developed",
                "description": "Replacement strategies for non-PubMed refs developed",
            },
            {
                "name": "details_verified",
                "description": "Author names, journal titles, publication details verified",
            },
            {
                "name": "documentation_created",
                "description": "Verification documentation created",
            },
        ],
        ManuscriptPhase.ACADEMIC_PROSE: [
            {
                "name": "paragraphs_developed",
                "description": "All paragraphs contain 3+ sentences with development",
            },
            {
                "name": "enumeration_eliminated",
                "description": "No bullet points, lists, or sequential connectors",
            },
            {
                "name": "transitions_added",
                "description": "All paragraphs connect logically through transitions",
            },
            {
                "name": "evidence_integrated",
                "description": "Evidence integrated into flowing prose",
            },
            {
                "name": "voice_consistent",
                "description": "Voice and tense consistent within sections",
            },
            {
                "name": "hedging_appropriate",
                "description": "Hedging language appropriately qualifies claims",
            },
            {
                "name": "technical_terms_defined",
                "description": "Technical terms defined at first use",
            },
            {
                "name": "manuscript_reviewed_aloud",
                "description": "Manuscript reviewed aloud for flow",
            },
        ],
        ManuscriptPhase.PRE_SUBMISSION: [
            {
                "name": "internal_review_completed",
                "description": "Internal review process completed",
            },
            {
                "name": "language_polished",
                "description": "Language and writing quality verified",
            },
            {"name": "plagiarism_checked", "description": "Plagiarism check passed"},
            {
                "name": "ethical_compliance_verified",
                "description": "Ethical compliance verified",
            },
            {
                "name": "all_authors_approved",
                "description": "All authors approved submission",
            },
        ],
        ManuscriptPhase.SUBMISSION_PROCESS: [
            {
                "name": "submission_prepared",
                "description": "Electronic submission files prepared",
            },
            {
                "name": "cover_letter_written",
                "description": "Cover letter crafted and completed",
            },
            {
                "name": "metadata_entered",
                "description": "Submission metadata accurately entered",
            },
            {
                "name": "tracking_established",
                "description": "Submission tracking established",
            },
        ],
        ManuscriptPhase.PEER_REVIEW: [
            {
                "name": "comments_analyzed",
                "description": "Reviewer comments thoroughly analyzed",
            },
            {"name": "responses_drafted", "description": "Response letter drafted"},
            {
                "name": "revisions_implemented",
                "description": "Revisions implemented systematically",
            },
            {
                "name": "resubmission_prepared",
                "description": "Revised manuscript prepared for resubmission",
            },
        ],
        ManuscriptPhase.POST_ACCEPTANCE: [
            {
                "name": "proofs_reviewed",
                "description": "Page proofs carefully reviewed",
            },
            {
                "name": "timeline_understood",
                "description": "Publication timeline understood",
            },
            {
                "name": "post_publication_planned",
                "description": "Post-publication activities planned",
            },
        ],
        ManuscriptPhase.RESUBMISSION: [
            {
                "name": "rejection_analyzed",
                "description": "Rejection feedback analytically assessed",
            },
            {
                "name": "new_journal_selected",
                "description": "New target journal selected",
            },
            {
                "name": "manuscript_adapted",
                "description": "Manuscript adapted for new journal",
            },
            {"name": "resubmission_executed", "description": "Resubmission executed"},
        ],
    }

    # Phase progression order
    PHASE_ORDER = [
        ManuscriptPhase.TOPIC_SELECTION,
        ManuscriptPhase.RESEARCH_DESIGN,
        ManuscriptPhase.JOURNAL_STRATEGY,
        ManuscriptPhase.MANUSCRIPT_PREP,
        ManuscriptPhase.MANUSCRIPT_UPDATING,
        ManuscriptPhase.PUBMED_CONCORDANCE,
        ManuscriptPhase.ACADEMIC_PROSE,
        ManuscriptPhase.PRE_SUBMISSION,
        ManuscriptPhase.SUBMISSION_PROCESS,
        ManuscriptPhase.PEER_REVIEW,
        ManuscriptPhase.POST_ACCEPTANCE,
        ManuscriptPhase.COMPLETED,
    ]

    def __init__(self, manuscript_id: str, project_dir: Optional[Path] = None):
        """
        Initialize the PhaseManager for a manuscript.

        Args:
            manuscript_id: Unique identifier for this manuscript
            project_dir: Directory for saving phase state (default: ~/.hpw/projects/)
        """
        self.manuscript_id = manuscript_id
        self.metadata = ManuscriptMetadata()
        self.phase_history: List[PhaseState] = []
        self.current_phase: Optional[ManuscriptPhase] = None
        self.current_state: Optional[PhaseState] = None

        if project_dir is None:
            project_dir = Path.home() / ".hpw" / "projects" / manuscript_id
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)

        self._load_state()

    def _load_state(self):
        """Load phase state from disk if it exists."""
        state_file = self.project_dir / "phase_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)

                if "metadata" in data:
                    self.metadata = ManuscriptMetadata(**data["metadata"])

                self.phase_history = []
                for phase_data in data.get("phase_history", []):
                    phase = ManuscriptPhase(phase_data["phase"])
                    state = PhaseState(
                        phase=phase,
                        entered_at=datetime.fromisoformat(phase_data["entered_at"]),
                        completed=phase_data.get("completed", False),
                        notes=phase_data.get("notes", ""),
                        metrics=phase_data.get("metrics", {}),
                    )
                    if phase_data.get("completed_at"):
                        state.completed_at = datetime.fromisoformat(
                            phase_data["completed_at"]
                        )

                    for ms_data in phase_data.get("milestones", []):
                        milestone = PhaseMilestone(
                            name=ms_data["name"],
                            description=ms_data["description"],
                            completed=ms_data.get("completed", False),
                            notes=ms_data.get("notes", ""),
                        )
                        if ms_data.get("completed_at"):
                            milestone.completed_at = datetime.fromisoformat(
                                ms_data["completed_at"]
                            )
                        state.milestones.append(milestone)

                    self.phase_history.append(state)

                if data.get("current_phase"):
                    self.current_phase = ManuscriptPhase(data["current_phase"])
                    for state in self.phase_history:
                        if state.phase == self.current_phase:
                            self.current_state = state
                            break

            except Exception as e:
                print(f"Warning: Could not load phase state: {e}")

    def _save_state(self):
        """Save phase state to disk."""
        state_file = self.project_dir / "phase_state.json"

        data = {
            "manuscript_id": self.manuscript_id,
            "metadata": {
                "title": self.metadata.title,
                "topic": self.metadata.topic,
                "target_journal": self.metadata.target_journal,
                "manuscript_type": self.metadata.manuscript_type,
                "authors": self.metadata.authors,
                "keywords": self.metadata.keywords,
                "created_at": self.metadata.created_at.isoformat(),
                "last_modified": datetime.now().isoformat(),
            },
            "current_phase": self.current_phase.value if self.current_phase else None,
            "phase_history": [],
        }

        for state in self.phase_history:
            phase_data = {
                "phase": state.phase.value,
                "entered_at": state.entered_at.isoformat(),
                "completed": state.completed,
                "notes": state.notes,
                "metrics": state.metrics,
                "milestones": [],
            }
            if state.completed_at:
                phase_data["completed_at"] = state.completed_at.isoformat()

            for milestone in state.milestones:
                ms_data = {
                    "name": milestone.name,
                    "description": milestone.description,
                    "completed": milestone.completed,
                    "notes": milestone.notes,
                }
                if milestone.completed_at:
                    ms_data["completed_at"] = milestone.completed_at.isoformat()
                phase_data["milestones"].append(ms_data)

            data["phase_history"].append(phase_data)

        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)

    def start_phase(self, phase: ManuscriptPhase) -> PhaseState:
        """
        Start working on a specific phase.

        Args:
            phase: The phase to start

        Returns:
            PhaseState for the new phase
        """
        if self.current_state and not self.current_state.completed:
            self._save_state()

        state = PhaseState(phase=phase)

        if phase in self.PHASE_MILESTONES:
            for milestone_def in self.PHASE_MILESTONES[phase]:
                state.add_milestone(
                    name=milestone_def["name"], description=milestone_def["description"]
                )

        self.current_phase = phase
        self.current_state = state
        self.phase_history.append(state)

        self._save_state()

        # Create new phase state
        state = PhaseState(phase=phase)

        # Add predefined milestones for this phase
        if phase in self.PHASE_MILESTONES:
            for milestone_def in self.PHASE_MILESTONES[phase]:
                state.add_milestone(
                    name=milestone_def["name"], description=milestone_def["description"]
                )

        # Update current tracking
        self.current_phase = phase
        self.current_state = state
        self.phase_history.append(state)

        # Save state
        self._save_state()

        return state

    def complete_current_phase(self, notes: str = ""):
        """Mark the current phase as completed."""
        if self.current_state:
            self.current_state.completed = True
            self.current_state.completed_at = datetime.now()
            if notes:
                self.current_state.notes = notes
            self._save_state()

    def complete_milestone(self, milestone_name: str, notes: str = ""):
        """
        Mark a specific milestone as completed.

        Args:
            milestone_name: Name of the milestone to complete
            notes: Optional notes about completion
        """
        if self.current_state:
            for milestone in self.current_state.milestones:
                if milestone.name == milestone_name:
                    milestone.mark_completed(notes)
                    self._save_state()
                    return True
        return False

    def can_transition_to(self, target_phase: ManuscriptPhase) -> tuple[bool, str]:
        """
        Check if transition to a target phase is allowed.

        Returns:
            Tuple of (allowed, reason)
        """
        if not self.current_phase:
            # Can start with any phase if no current phase
            return True, "No current phase, can start with any phase"

        if target_phase == self.current_phase:
            return True, "Already in this phase"

        # Get phase indices
        try:
            current_idx = self.PHASE_ORDER.index(self.current_phase)
            target_idx = self.PHASE_ORDER.index(target_phase)
        except ValueError:
            return False, f"Invalid phase transition"

        if target_idx > current_idx:
            if self.current_state:
                completion = self.current_state.get_completion_percentage()
                if completion < 50:
                    return (
                        False,
                        f"Current phase only {completion:.0f}% complete. Consider completing more milestones.",
                    )
            return True, "Forward progression allowed"

        # Allow backward navigation for revision
        if target_idx < current_idx:
            return True, "Backward navigation allowed for revision"

        return False, "Unknown transition"

    def get_phase_progress(self) -> Dict[str, Any]:
        """Get comprehensive progress information."""
        if not self.current_state:
            return {
                "current_phase": None,
                "overall_progress": 0.0,
                "message": "No phase started yet",
            }

        current_phase_idx = self.PHASE_ORDER.index(self.current_phase)
        total_phases = len(self.PHASE_ORDER) - 1  # Exclude COMPLETED

        phase_progress = self.current_state.get_completion_percentage()

        # Calculate overall progress
        completed_phases = sum(1 for s in self.phase_history if s.completed)
        overall_progress = ((completed_phases / total_phases) * 100) + (
            phase_progress / total_phases
        )

        return {
            "current_phase": self.current_phase.value,
            "current_phase_name": self.current_phase.name.replace("_", " ").title(),
            "phase_progress": phase_progress,
            "overall_progress": min(overall_progress, 100.0),
            "milestones": [
                {"name": m.name, "description": m.description, "completed": m.completed}
                for m in self.current_state.milestones
            ],
            "completed_milestones": sum(
                1 for m in self.current_state.milestones if m.completed
            ),
            "total_milestones": len(self.current_state.milestones),
            "phases_completed": completed_phases,
            "total_phases": total_phases,
        }

    def get_next_recommended_phase(self) -> Optional[ManuscriptPhase]:
        """Get the next recommended phase based on current state."""
        if not self.current_phase:
            return ManuscriptPhase.TOPIC_SELECTION

        if self.current_phase == ManuscriptPhase.COMPLETED:
            return None

        current_idx = self.PHASE_ORDER.index(self.current_phase)
        if current_idx < len(self.PHASE_ORDER) - 1:
            return self.PHASE_ORDER[current_idx + 1]

        return None

    def get_guidance_for_current_phase(self) -> str:
        """Get guidance text for the current phase."""
        if not self.current_phase:
            return (
                "Start with Phase 1: Topic Selection to begin manuscript preparation."
            )

        guidance = {
            ManuscriptPhase.TOPIC_SELECTION: """
Phase 1: Topic Selection and Conceptual Development
Focus on identifying a researchable topic that addresses knowledge gaps:
- Scan recent literature to identify unanswered questions
- Balance scientific significance, originality, feasibility
- Use PICO framework to develop research questions
- Formulate clear, testable hypotheses
""",
            ManuscriptPhase.RESEARCH_DESIGN: """
Phase 2: Research Design and Data Collection
Develop rigorous methodology for your research:
- Select appropriate study design (RCT, cohort, case-control, etc.)
- Ensure IRB/ethics approval for human subjects research
- Plan data collection with quality assurance procedures
- Develop statistical analysis plan before data collection
""",
            ManuscriptPhase.JOURNAL_STRATEGY: """
Phase 3: Journal Selection and Strategy
Strategically select your target journal:
- Evaluate journals by impact, scope, acceptance rates, timelines
- Match manuscript content to journal priorities
- Understand formatting and submission requirements
- Consider open access options and costs
""",
            ManuscriptPhase.MANUSCRIPT_PREP: """
Phase 4: Manuscript Preparation and Structure
Draft all sections following journal requirements:
- Develop clear, structured abstract
- Write Introduction with rationale and gap identification
- Document Methods with replicable detail
- Present Results systematically
- Interpret findings in Discussion
""",
            ManuscriptPhase.MANUSCRIPT_UPDATING: """
Phase 4.5: Manuscript Updating and Editing
Transform draft into polished manuscript:
- Edit for clarity, accuracy, argument strength
- Integrate new literature and update references
- Ensure cross-section consistency
- Verify narrative coherence throughout
""",
            ManuscriptPhase.PUBMED_CONCORDANCE: """
Phase 4.6: PubMed Reference Concordance Verification
Ensure 100% PubMed indexing for all references:
- Extract and count all references
- Verify each in PubMed database
- Assign PMIDs to all citations
- Develop replacements for non-PubMed references
- Verify author names and publication details
""",
            ManuscriptPhase.ACADEMIC_PROSE: """
Phase 4.7: Academic Writing Style and Prose Development
Ensure professional prose throughout manuscript:
- Write in flowing paragraphs (no lists, bullets, enumeration)
- Develop paragraphs with topic sentences, evidence, transitions
- Integrate citations seamlessly into prose
- Maintain consistent voice and appropriate hedging
- Define technical terms at first use
""",
            ManuscriptPhase.PRE_SUBMISSION: """
Phase 5: Pre-Submission Review and Quality Assurance
Complete comprehensive quality checks:
- Conduct internal review with colleagues
- Verify language and writing quality
- Run plagiarism detection
- Confirm ethical compliance
- Obtain author approvals
""",
            ManuscriptPhase.SUBMISSION_PROCESS: """
Phases 6-7: Submission Process
Prepare and submit to target journal:
- Format all submission files correctly
- Craft compelling cover letter
- Enter accurate metadata
- Establish submission tracking
- Monitor editorial process
""",
            ManuscriptPhase.PEER_REVIEW: """
Phase 8: Peer Review and Revision
Navigate review process effectively:
- Understand review types and decisions
- Analyze reviewer comments thoroughly
- Draft professional response letter
- Implement strategic revisions
- Address all concerns systematically
""",
            ManuscriptPhase.POST_ACCEPTANCE: """
Phase 9: Post-Acceptance and Publication
Manage publication and dissemination:
- Review and correct page proofs carefully
- Understand publication timelines
- Plan post-publication activities
- Share through appropriate channels
- Track citations and impact
""",
            ManuscriptPhase.RESUBMISSION: """
Phase 10: Rejection and Resubmission
Handle rejection constructively:
- Analyze rejection feedback objectively
- Determine if resubmission is warranted
- Select new target journal strategically
- Adapt manuscript for new venue
- Execute resubmission plan
""",
        }

        return guidance.get(
            self.current_phase, "Continue working on current phase milestones."
        )

    def set_metadata(self, **kwargs):
        """Update manuscript metadata."""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
        self.metadata.last_modified = datetime.now()
        self._save_state()

    def get_report(self) -> str:
        """Generate a comprehensive progress report."""
        lines = [
            f"Manuscript: {self.manuscript_id}",
            f"Title: {self.metadata.title or 'Not set'}",
            f"Topic: {self.metadata.topic or 'Not set'}",
            f"Target Journal: {self.metadata.target_journal or 'Not set'}",
            "",
            "Phase Progress Report",
            "=" * 50,
        ]

        progress = self.get_phase_progress()
        if progress["current_phase"]:
            lines.extend(
                [
                    f"Current Phase: {progress['current_phase_name']}",
                    f"Phase Completion: {progress['phase_progress']:.0f}%",
                    f"Overall Progress: {progress['overall_progress']:.0f}%",
                    f"Milestones: {progress['completed_milestones']}/{progress['total_milestones']} completed",
                    "",
                    "Milestones:",
                ]
            )

            for m in progress["milestones"]:
                status = "✓" if m["completed"] else "○"
                lines.append(f"  {status} {m['name']}: {m['description']}")
        else:
            lines.append("No phase started yet. Use start_phase() to begin.")

        lines.extend(["", self.get_guidance_for_current_phase()])

        return "\n".join(lines)


# Singleton instance manager
_phase_managers: Dict[str, PhaseManager] = {}


def get_phase_manager(
    manuscript_id: str, project_dir: Optional[Path] = None
) -> PhaseManager:
    """
    Get or create a PhaseManager for a manuscript.

    Args:
        manuscript_id: Unique identifier for the manuscript
        project_dir: Optional project directory

    Returns:
        PhaseManager instance
    """
    if manuscript_id not in _phase_managers:
        _phase_managers[manuscript_id] = PhaseManager(manuscript_id, project_dir)
    return _phase_managers[manuscript_id]
