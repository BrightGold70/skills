---
name: notebooklm-assistant
description: Interacts with NotebookLM to get zero-hallucination answers from your uploaded documents. Use when user wants to research or get accurate information from their NotebookLM notebooks.
---

# NotebookLM Assistant

This skill enables querying NotebookLM for zero-hallucination answers from your documents.

## When to Use This Skill

- User wants accurate information from their documents
- Researching library/framework APIs from NotebookLM
- Getting implementation details from uploaded docs
- User provides a NotebookLM link and wants to query it

## Setup (One-Time)

### 1. Install notebooklm-mcp-cli

```bash
# Using uv (recommended)
uv tool install notebooklm-mcp-cli

# Or using pip
pip install notebooklm-mcp-cli
```

### 2. Authenticate with NotebookLM

```bash
nlm login
```

This will open a Chrome browser for login. Cookies are extracted automatically.

### 3. Add MCP to OpenCode

Add to `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "notebooklm": {
      "type": "local",
      "command": ["notebooklm-mcp"],
      "enabled": true
    }
  }
}
```

Verify with:
```bash
opencode mcp list
```

## Tools Available

Once configured, use these tools via the `notebooklm` MCP:

| Tool | Description |
|------|-------------|
| `notebook_list` | List all saved notebooks |
| `notebook_create` | Create a new notebook |
| `notebook_query` | Query notebook with AI |
| `source_add` | Add sources (URL, text, Drive, file) |
| `studio_create` | Create audio/video/briefing |
| `download_artifact` | Download generated content |

## How to Use

Include "use notebooklm" in your prompt:

```
List my NotebookLM notebooks - use notebooklm
```

```
Query my "Hematology guidelines" notebook about treatment protocols
```

## Tips

- NotebookLM provides citation-backed answers (zero hallucinations)
- The MCP server name in OpenCode is `notebooklm`
