# Anti-Hallucination Citation Workflow

**Core Principle**: Never write BibTeX from memory. AI-generated citations have extremely high error rates.

## Verification Workflow (MANDATORY)

1. **Search**: Use Exa MCP or Web Search to find papers.
2. **Verify**: Confirm paper title, author, and year on Semantic Scholar or arXiv.
3. **Fetch BibTeX**: Retrieve original BibTeX data via DOI or arXiv ID.
4. **Mark**:
   - Verification successful: Use directly.
   - Verification failed: Mark as `[CITATION NEEDED]` or `\cite{PLACEHOLDER_author2024_verify}`.

## Recommended Tools

### 1. Exa MCP (Academic Search)
```bash
# Example query
"Find papers on RLHF for language models published after 2023"
```

### 2. Semantic Scholar API
Used to verify paper IDs and retrieve metadata.

### 3. DOI to BibTeX
```python
import requests

def doi_to_bibtex(doi: str) -> str:
    response = requests.get(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/x-bibtex"}
    )
    return response.text
```

## Failure Handling
If you cannot verify citations programmatically, you must inform the user:
> "I cannot verify the following citations and have marked them as placeholders. Please verify manually:
> - [Author et al., 2024] regarding X"
