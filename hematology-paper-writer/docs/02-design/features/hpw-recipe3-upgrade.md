# Design: HPW Recipe 3 Structural Upgrade (Section Chaining + Full-Text)

## Architecture Overview
The upgrade modifies the prompt architecture within the `hematology-paper-writer/SKILL.md` file. Instead of allowing a single text generation block for an entire review, the skill's instructions will inherently act as a state machine. The LLM must verify the completion of prerequisite states (e.g., uploading to NotebookLM, generating an outline) before executing the next state (e.g., drafting a specific section).

## Components

### 1. Mandatory Context Gate (NotebookLM)
- **Current State:** AI drafts directly from PubMed abstracts.
- **New Design:** The skill will physically instruct the LLM to halt. The prompt instructions will say: "You MUST halt standard generation and strictly instruct the user to upload the full-text PDFs of the pivotal literature discovered in Step 1 into a specific NotebookLM notebook. *Do not proceed to drafting without deep context initialization.*"

### 2. The Chaining Loop (Section-by-Section)
- **Current State:** "Draft paragraph by paragraph." (Often ignored or collapsed by the LLM into a single response).
- **New Design:** Explicit prompt engineering enforcing a loop. "Draft exactly ONE section at a time. Query NotebookLM for deep, specific context bridging the current section's topic. Draft the section, ensure citations are aggressively placed, and wait for user approval before moving to the next section."

### 3. Submission Quality Definition
- **Current State:** Implied by "authoritative, narrative-driven".
- **New Design:** Explicitly codified rules: "A submission-quality review requires exact p-values, mechanistic context, and highly specific evidence synthesis without generalized fluff."

## Data Models
N/A (Prompt engineering/Skill modification, no backend data schemas).

## API Specifications
- Uses existing `pubmed-integration` and `notebooklm-assistant` API definitions. The change is in the orchestration of these tools within the `SKILL.md` Markdown instructions.

## Security/Safety Considerations
- **Hallucination Prevention:** By gating drafting behind NotebookLM full-text context, the probability of the LLM hallucinating trial outcomes (e.g., survival curves, exact dosages) is drastically reduced.
- **Plagiarism/Citation Integrity:** The section-by-section requirement allows the user to verify citations block-by-block rather than attempting to audit 150 citations spanning an entire paper simultaneously.

## Testing Strategy
- **Manual End-to-End Workflow Test:** Invoke Recipe 3 on a sample topic (e.g., "Venetoclax in AML"). Ensure the AI refuses to draft the paper until the user confirms NotebookLM initialization. Verify the AI stops generating after outputting the Abstract/Introduction.
