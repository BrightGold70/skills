import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path


@dataclass
class PermissionRequest:
    result_index: int
    title: str
    url: str
    category: str
    metadata: Dict[str, Any]
    status: str = "pending"
    user_notes: str = ""
    decision_date: str = ""


@dataclass
class PermissionWorkflowState:
    query: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    requests: List[PermissionRequest] = field(default_factory=list)
    permitted_indices: List[int] = field(default_factory=list)
    rejected_indices: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "timestamp": self.timestamp,
            "requests": [asdict(r) for r in self.requests],
            "permitted_indices": self.permitted_indices,
            "rejected_indices": self.rejected_indices,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PermissionWorkflowState":
        state = cls(query=data.get("query", ""), timestamp=data.get("timestamp", ""))
        state.requests = [PermissionRequest(**r) for r in data.get("requests", [])]
        state.permitted_indices = data.get("permitted_indices", [])
        state.rejected_indices = data.get("rejected_indices", [])
        return state


class ReferencePermissionWorkflow:
    def __init__(self, storage_path: str = "reference_permissions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    def create_permission_review(
        self, query: str, results: List[Any]
    ) -> PermissionWorkflowState:
        from tools.draft_generator.tavily_searcher import SourceCategory

        state = PermissionWorkflowState(query=query)
        for i, result in enumerate(results):
            category = getattr(result, "category", SourceCategory.UNKNOWN)
            if category != SourceCategory.PEER_REVIEWED:
                request = PermissionRequest(
                    result_index=i,
                    title=result.title,
                    url=result.url,
                    category=category.value
                    if hasattr(category, "value")
                    else str(category),
                    metadata={
                        "source": getattr(result, "source", ""),
                        "published_date": getattr(result, "published_date", ""),
                        "year": getattr(result, "year", 0),
                        "organization": getattr(result, "organization", ""),
                        "conference": getattr(result, "conference", ""),
                        "doi": getattr(result, "doi", ""),
                        "content_preview": result.content[:300]
                        if hasattr(result, "content")
                        else "",
                    },
                )
                state.requests.append(request)
        return state

    def save_state(self, state: PermissionWorkflowState, filename: str = None) -> str:
        if filename is None:
            filename = f"permissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.storage_path / filename
        with open(filepath, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
        return str(filepath)

    def load_state(self, filepath: str) -> PermissionWorkflowState:
        with open(filepath, "r") as f:
            data = json.load(f)
        return PermissionWorkflowState.from_dict(data)

    def format_permission_prompt(self, state: PermissionWorkflowState) -> str:
        if not state.requests:
            return "No references require permission."

        prompt = "## Reference Permission Review\n\n"
        prompt += f"Query: {state.query}\n\n"
        prompt += "The following sources were found via web search but are NOT indexed in PubMed.\n"
        prompt += (
            "Please review each and decide whether to permit for use as references.\n\n"
        )

        for req in state.requests:
            status_icon = {
                "pending": "[ ]",
                "permitted": "[✓]",
                "rejected": "[✗]",
            }.get(req.status, "[?]")

            prompt += f"{status_icon} **{req.result_index + 1}. {req.title}**\n"
            prompt += f"   - Type: {req.category}\n"
            prompt += f"   - URL: {req.url}\n"

            if req.metadata.get("organization"):
                prompt += f"   - Organization: {req.metadata['organization']}\n"
            if req.metadata.get("year"):
                prompt += f"   - Year: {req.metadata['year']}\n"
            if req.metadata.get("conference"):
                prompt += f"   - Conference: {req.metadata['conference']}\n"

            preview = req.metadata.get("content_preview", "")
            if preview:
                prompt += f"   - Preview: {preview[:200]}...\n"

            prompt += "\n"

        prompt += "\n**Instructions:**\n"
        prompt += (
            "- Enter permitted indices (e.g., `1,3,5`) to approve specific references\n"
        )
        prompt += "- Enter `all` to permit all references\n"
        prompt += "- Enter `none` to reject all\n"
        prompt += "- Add notes after semicolon (e.g., `1,2; relevant for mechanism`)\n"

        return prompt

    def process_user_decision(
        self, state: PermissionWorkflowState, user_input: str
    ) -> PermissionWorkflowState:
        user_input = user_input.strip().lower()

        if user_input == "none":
            for req in state.requests:
                req.status = "rejected"
                req.decision_date = datetime.now().isoformat()
            state.rejected_indices = [r.result_index for r in state.requests]
            state.permitted_indices = []
            return state

        if user_input == "all":
            for req in state.requests:
                req.status = "permitted"
                req.decision_date = datetime.now().isoformat()
            state.permitted_indices = [r.result_index for r in state.requests]
            state.rejected_indices = []
            return state

        notes = ""
        if ";" in user_input:
            user_input, notes = user_input.split(";", 1)
            notes = notes.strip()

        try:
            indices = [
                int(x.strip()) - 1 for x in user_input.split(",") if x.strip().isdigit()
            ]
        except ValueError:
            return state

        for req in state.requests:
            if req.result_index in indices:
                req.status = "permitted"
            else:
                req.status = "rejected"
            req.decision_date = datetime.now().isoformat()

        if notes:
            for req in state.requests:
                if req.result_index in indices:
                    req.user_notes = notes

        state.permitted_indices = [
            r.result_index for r in state.requests if r.status == "permitted"
        ]
        state.rejected_indices = [
            r.result_index for r in state.requests if r.status == "rejected"
        ]
        return state

    def get_permitted_references(self, original_results: List[Any]) -> List[Any]:
        from tools.draft_generator.tavily_searcher import SourceCategory

        permitted = []
        for i, result in enumerate(original_results):
            category = getattr(result, "category", SourceCategory.UNKNOWN)
            if category == SourceCategory.PEER_REVIEWED:
                permitted.append(result)
            elif (
                i in self.current_state.permitted_indices
                if hasattr(self, "current_state")
                else False
            ):
                result.permission_status = "permitted"
                permitted.append(result)
        return permitted


def interactive_permission_review(query: str, results: List[Any]) -> List[Any]:
    workflow = ReferencePermissionWorkflow()
    state = workflow.create_permission_review(query, results)

    if not state.requests:
        print("All references are PubMed-indexed. No permission needed.")
        return results

    print(workflow.format_permission_prompt(state))
    user_input = input("\nEnter your decision: ")
    state = workflow.process_user_decision(state, user_input)

    workflow.save_state(state)
    print(
        f"\nPermission decision saved. {len(state.permitted_indices)} permitted, {len(state.rejected_indices)} rejected."
    )

    return [results[i] for i in state.permitted_indices] + [
        r
        for r in results
        if getattr(r, "category", None) == SourceCategory.PEER_REVIEWED
    ]


def format_permitted_as_reference(result: Any, index: int) -> str:
    category = getattr(result, "category", "unknown")
    title = result.title
    url = result.url

    authors = getattr(result, "authors", [])
    author_str = ", ".join(authors) if authors else "Unknown Authors"

    year = getattr(result, "year", "")
    organization = getattr(result, "organization", "")
    conference = getattr(result, "conference", "")
    doi = getattr(result, "doi", "")
    access_date = getattr(result, "access_date", "")

    if category == "conference_abstract" or category == "conference_proceedings":
        ref = f"[{index}] {author_str}. {title}. "
        if conference:
            ref += f"In Proc. {conference}"
        if year:
            ref += f", {year}"
        ref += f". Available from: {url}"
    elif category == "guideline":
        ref = f"[{index}] {title}"
        if organization:
            ref += f". {organization}"
        if year:
            ref += f" ({year})"
        ref += f". Available from: {url}"
    elif category == "clinical_trial":
        ref = f"[{index}] {title}. "
        if organization:
            ref += f"{organization}"
        if year:
            ref += f" ({year})"
        ref += f". ClinicalTrials.gov. Available from: {url}"
    elif category == "website":
        ref = f"[{index}] {title}. "
        if organization:
            ref += f"{organization}. "
        ref += f"Accessed {access_date}. Available from: {url}"
    else:
        ref = f"[{index}] {author_str}. {title}. "
        if year:
            ref += f"{year}. "
        ref += f"Available from: {url}"

    if doi:
        ref += f" DOI: {doi}"

    return ref


def get_permitted_reference_text(
    results: List[Any], permitted_indices: List[int]
) -> str:
    ref_lines = []
    pubmed_count = 1

    from tools.draft_generator.tavily_searcher import SourceCategory

    for result in results:
        category = getattr(result, "category", SourceCategory.UNKNOWN)
        if category == SourceCategory.PEER_REVIEWED:
            continue
        if results.index(result) not in permitted_indices:
            continue
        ref_text = format_permitted_as_reference(result, pubmed_count)
        ref_lines.append(ref_text)
        pubmed_count += 1

    return "\n".join(ref_lines)
