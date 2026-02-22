"""
HPW Skill - Enhanced Editing Module
===================================
Advanced manuscript editing with topic search and context insertion capabilities.
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EditSuggestion:
    """Manuscript edit suggestion."""
    section: str
    original_text: str
    suggested_text: str
    rationale: str
    source: str
    confidence: float  # 0.0-1.0
    insertion_point: Tuple[int, int]  # line numbers


@dataclass  
class ManuscriptSection:
    """Manuscript section with metadata."""
    title: str
    content: str
    word_count: int
    line_start: int
    line_end: int
    section_type: str  # "introduction", "methods", "results", "discussion"


class EnhancedEditor:
    """
    Enhanced manuscript editor with search and insertion capabilities.
    """
    
    SECTION_TYPES = {
        "introduction": ["background", "rationale", "objectives", "introduction"],
        "methods": ["methods", "methodology", "materials and methods", "patients and methods"],
        "results": ["results", "study results", "outcome", "outcomes"],
        "discussion": ["discussion", "commentary", "interpretation"],
        "conclusion": ["conclusion", "conclusions", "summary"],
        "abstract": ["abstract"],
        "references": ["references", "bibliography"]
    }
    
    def __init__(self, manuscript_path: Optional[str] = None):
        """Initialize the enhanced editor."""
        self.manuscript_path = manuscript_path
        self.sections: List[ManuscriptSection] = []
        self.edit_history: List[EditSuggestion] = []
        
    def load_manuscript(self, path: str) -> List[ManuscriptSection]:
        """Load and parse manuscript into sections."""
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.sections = self._parse_sections(lines)
        return self.sections
    
    def _parse_sections(self, lines: List[str]) -> List[ManuscriptSection]:
        """Parse manuscript into sections."""
        sections = []
        current_section = None
        line_num = 0
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Detect section headers (## or ###)
            if line.startswith('##'):
                if current_section:
                    current_section.line_end = line_num - 1
                    current_section.content = ''.join(lines[current_section.line_start-1:current_section.line_end])
                    current_section.word_count = len(current_section.content.split())
                    sections.append(current_section)
                
                # Determine section type
                section_type = self._classify_section(line.lower())
                current_section = ManuscriptSection(
                    title=line.strip('# ').strip(),
                    content="",
                    word_count=0,
                    line_start=line_num,
                    line_end=len(lines),
                    section_type=section_type
                )
        
        # Don't forget last section
        if current_section:
            current_section.content = ''.join(lines[current_section.line_start-1:])
            current_section.word_count = len(current_section.content.split())
            sections.append(current_section)
        
        return sections
    
    def _classify_section(self, title: str) -> str:
        """Classify section type based on title."""
        for section_type, keywords in self.SECTION_TYPES.items():
            for keyword in keywords:
                if keyword in title:
                    return section_type
        return "other"
    
    def search_and_suggest(
        self, 
        topic: str, 
        context_length: int = 200
    ) -> List[EditSuggestion]:
        """
        Search for relevant content to insert into manuscript.
        
        Args:
            topic: Topic to search for
            context_length: Characters of surrounding context to include
            
        Returns:
            List of EditSuggestion objects
        """
        suggestions = []
        
        for section in self.sections:
            # Find relevant content in section
            matches = self._find_topic_matches(section.content, topic)
            
            for match_start, match_text in matches:
                # Get context
                ctx_start = max(0, match_start - context_length)
                ctx_end = min(len(section.content), match_start + len(match_text) + context_length)
                context = section.content[ctx_start:ctx_end]
                
                # Determine insertion type
                insertion_type = self._determine_insertion_type(topic, section.section_type)
                
                suggestion = EditSuggestion(
                    section=section.title,
                    original_text=context,
                    suggested_text=self._generate_insertion(topic, context, insertion_type),
                    rationale=f"Add relevant content about '{topic}' to {section.section_type}",
                    source="Topic search",
                    confidence=self._calculate_confidence(match_text, topic),
                    insertion_point=(section.line_start, section.line_end)
                )
                suggestions.append(suggestion)
        
        self.edit_history.extend(suggestions)
        return suggestions
    
    def _find_topic_matches(self, content: str, topic: str) -> List[Tuple[int, str]]:
        """Find all occurrences of topic in content."""
        topic_lower = topic.lower()
        content_lower = content.lower()
        
        matches = []
        start = 0
        
        while True:
            pos = content_lower.find(topic_lower, start)
            if pos == -1:
                break
            
            # Extract surrounding text
            match_text = content[pos:pos + len(topic) + 50]
            matches.append((pos, match_text))
            start = pos + 1
        
        return matches
    
    def _determine_insertion_type(self, topic: str, section_type: str) -> str:
        """Determine appropriate insertion type based on topic and section."""
        topic_lower = topic.lower()
        
        # Keyword-based classification
        if any(kw in topic_lower for kw in ['method', 'study design', 'population']):
            return "methodology"
        elif any(kw in topic_lower for kw in ['result', 'outcome', 'response', 'rate']):
            return "data"
        elif any(kw in topic_lower for kw in ['background', 'pathophysiology', 'mechanism']):
            return "background"
        elif any(kw in topic_lower for kw in ['implication', 'future', 'limitation']):
            return "discussion"
        elif any(kw in topic_lower for kw in ['definition', 'criteria', 'diagnosis']):
            return "definition"
        else:
            return section_type
    
    def _generate_insertion(self, topic: str, context: str, insertion_type: str) -> str:
        """Generate insertion text based on topic and type."""
        templates = {
            "background": f"""
### {topic.title()}

{topic.capitalize()} represents an important aspect of this study. The current understanding suggests that [relevant background information]. Previous research has demonstrated [key findings]. This context is essential for interpreting the study results.

**Key Points:**
- [Evidence 1]
- [Evidence 2]
- [Clinical Relevance]
""",
            "methodology": f"""
### {topic.title()}

The methodology for {topic} was established as follows. Patients were selected based on predefined criteria. The intervention was administered according to standardized protocols. Outcome measures were assessed at predetermined timepoints using validated instruments.

**Study Parameters:**
- Inclusion criteria: [criteria]
- Exclusion criteria: [criteria]
- Assessment schedule: [timeline]
""",
            "data": f"""
### {topic.title()}

The results regarding {topic} are presented below. The analysis revealed [key findings]. Statistical significance was achieved with [statistical measure]. The effect size was [magnitude].

**Summary Statistics:**
- [Measure 1]: [value]
- [Measure 2]: [value]
- [Statistical significance]: [p-value]
""",
            "discussion": f"""
### {topic.title()}

The implications of {topic} merit careful consideration. These findings align with [previous studies/consensus]. Potential mechanisms include [biological rationale]. Limitations affecting interpretation include [limitations].

**Future Directions:**
- [Research priority 1]
- [Research priority 2]
"""
        }
        
        return templates.get(insertion_type, templates["background"])
    
    def _calculate_confidence(self, match_text: str, topic: str) -> float:
        """Calculate confidence score for suggestion."""
        # Simple heuristic: longer matches = higher confidence
        overlap = len(topic) / len(match_text) if match_text else 0
        return min(0.95, 0.5 + overlap)
    
    def insert_content(
        self, 
        suggestion: EditSuggestion,
        position: str = "after_first_paragraph"
    ) -> str:
        """
        Insert suggested content into manuscript.
        
        Args:
            suggestion: EditSuggestion to implement
            position: Where to insert ("start", "end", "after_first_paragraph")
            
        Returns:
            Modified manuscript text
        """
        # This would modify the manuscript content
        # Implementation depends on manuscript storage
        self.edit_history.append(suggestion)
        return f"[Inserted content about: {suggestion.rationale}]"
    
    def generate_edit_report(self) -> str:
        """Generate report of all edits."""
        if not self.edit_history:
            return "No edits suggested."
        
        report_lines = [
            "=" * 60,
            "ENHANCED EDIT REPORT",
            "=" * 60,
            f"Total suggestions: {len(self.edit_history)}",
            ""
        ]
        
        # Group by section
        by_section: Dict[str, List[EditSuggestion]] = {}
        for edit in self.edit_history:
            if edit.section not in by_section:
                by_section[edit.section] = []
            by_section[edit.section].append(edit)
        
        for section, edits in by_section.items():
            report_lines.append(f"\n{section}:")
            report_lines.append("-" * 40)
            for i, edit in enumerate(edits, 1):
                report_lines.append(f"  {i}. {edit.rationale}")
                report_lines.append(f"     Confidence: {edit.confidence:.0%}")
                report_lines.append(f"     Source: {edit.source}")
        
        return "\n".join(report_lines)


class ContextSearcher:
    """
    Search for additional context to add to manuscripts.
    """
    
    def __init__(self, pubmed_searcher=None):
        """Initialize context searcher."""
        self.pubmed_searcher = pubmed_searcher
        self.search_history = []
    
    def search_topic(
        self, 
        topic: str, 
        max_results: int = 5
    ) -> List[Dict[str, str]]:
        """
        Search for topic-relevant information.
        
        Returns list of results with:
        - title
        - abstract_summary
        - key_findings
        - relevance_score
        """
        results = []
        
        if self.pubmed_searcher:
            # Use PubMed searcher
            pubmed_results = self.pubmed_searcher.search(
                query=topic,
                max_results=max_results
            )
            results.extend(pubmed_results)
        
        # Add general search results
        results.extend(self._local_search(topic))
        
        # Sort by relevance
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        self.search_history.append({
            'topic': topic,
            'results': len(results),
            'timestamp': datetime.now().isoformat()
        })
        
        return results[:max_results]
    
    def _local_search(self, topic: str) -> List[Dict[str, str]]:
        """Local search in reference database."""
        # Placeholder - would search local reference database
        return [
            {
                'title': f"Review: {topic}",
                'abstract_summary': f"Key findings related to {topic}...",
                'key_findings': [
                    f"Finding 1 about {topic}",
                    f"Finding 2 about {topic}"
                ],
                'relevance_score': 0.85,
                'source': 'Reference Database'
            }
        ]
    
    def format_for_insertion(self, search_result: Dict[str, str]) -> str:
        """Format search result for manuscript insertion."""
        return f"""
## {search_result['title']}

{search_result.get('abstract_summary', '')}

**Key Findings:**
{chr(10).join(f"- {finding}" for finding in search_result.get('key_findings', []))}

*Source: {search_result.get('source', 'Unknown')}*
"""
    
    def compare_and_merge(
        self, 
        existing_text: str, 
        new_info: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Compare existing text with new information.
        
        Returns:
        - additions: New information to add
        - conflicts: Potential conflicts
        - summary: Merged summary
        """
        return {
            'additions': [new_info.get('key_findings', [])],
            'conflicts': [],
            'summary': f"Merged information about {new_info.get('title', 'topic')}"
        }


class SectionEnhancer:
    """
    Enhance manuscript sections with additional content.
    """
    
    def __init__(self):
        """Initialize section enhancer."""
        self.enhancement_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load enhancement templates."""
        return {
            "introduction": """
### Enhanced Background

**Epidemiology:**
[Add epidemiological data]

**Pathophysiology:**
[Add mechanistic insights]

**Current Treatment Landscape:**
[Add treatment context]

**Unmet Medical Need:**
[Add rationale for study]
""",
            "methods": """
### Enhanced Methods

**Study Design:**
[Add design details]

**Population:**
[Add patient characteristics]

**Statistical Analysis:**
[Add statistical methods]

**Ethical Considerations:**
[Add IRB/ethics statement]
""",
            "results": """
### Enhanced Results

**Primary Endpoint Analysis:**
[Add detailed results]

**Secondary Endpoint Analysis:**
[Add secondary results]

**Subgroup Analyses:**
[Add subgroup findings]

**Safety Analysis:**
[Add safety data]
""",
            "discussion": """
### Enhanced Discussion

**Principal Findings:**
[Add summary of main findings]

**Comparison with Existing Literature:**
[Add literature comparison]

**Clinical Implications:**
[Add clinical relevance]

**Strengths and Limitations:**
[Add balanced assessment]

**Future Research Directions:**
[Add recommendations]
"""
        }
    
    def enhance_section(
        self, 
        section_type: str, 
        existing_content: str,
        topic: Optional[str] = None
    ) -> str:
        """
        Enhance section with additional content.
        
        Args:
            section_type: Type of section to enhance
            existing_content: Current section content
            topic: Optional topic focus
            
        Returns:
            Enhanced section content
        """
        template = self.enhancement_templates.get(
            section_type, 
            self.enhancement_templates.get("introduction", "")
        )
        
        return existing_content + template
    
    def generate_section_summary(self, section: ManuscriptSection) -> Dict[str, Any]:
        """Generate summary of section content."""
        return {
            'title': section.title,
            'word_count': section.word_count,
            'section_type': section.section_type,
            'completeness_score': self._calculate_completeness(section),
            'suggested_enhancements': self._suggest_enhancements(section)
        }
    
    def _calculate_completeness(self, section: ManuscriptSection) -> float:
        """Calculate section completeness score."""
        word_count = section.word_count
        section_type = section.section_type
        
        # Target word counts by section type
        targets = {
            "introduction": 500,
            "methods": 800,
            "results": 1000,
            "discussion": 800,
            "conclusion": 300
        }
        
        target = targets.get(section_type, 500)
        ratio = min(1.0, word_count / target)
        
        return ratio
    
    def _suggest_enhancements(self, section: ManuscriptSection) -> List[str]:
        """Suggest enhancements for section."""
        suggestions = []
        
        if section.word_count < 300:
            suggestions.append("Section is brief; consider expanding with additional context")
        
        if section.section_type == "methods":
            if "statistical" not in section.content.lower():
                suggestions.append("Add statistical analysis details")
            if "sample" not in section.content.lower():
                suggestions.append("Add sample size justification")
        
        if section.section_type == "results":
            if "table" not in section.content.lower() and "figure" not in section.content.lower():
                suggestions.append("Consider adding tables or figures")
        
        return suggestions


if __name__ == "__main__":
    # Example usage
    editor = EnhancedEditor()
    
    print("HPW Enhanced Editor Module Loaded")
    print("\nFeatures:")
    print("  - Load and parse manuscripts into sections")
    print("  - Search topics and generate insertion suggestions")
    print("  - Context-aware content insertion")
    print("  - Section enhancement templates")
    print("  - Completeness scoring")
    print("  - Edit history tracking")
