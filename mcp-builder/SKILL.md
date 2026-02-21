---
name: mcp-builder
description: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools.
---

# MCP Server Development Guide

This skill helps create high-quality MCP servers for integrating external APIs.

## Overview

MCP (Model Context Protocol) servers provide tools that allow LLMs to access external services and APIs. Quality is measured by how well the tools enable agents to accomplish real-world tasks.

## High-Level Workflow

### Phase 1: Research and Planning

#### Agent-Centric Design Principles

**Build for Workflows, Not Just API Endpoints:**
- Don't simply wrap existing API endpoints - build thoughtful, high-impact workflow tools
- Consolidate related operations (e.g., `schedule_event` that checks availability AND creates event)
- Focus on tools that enable complete tasks, not just individual API calls

**Optimize for Limited Context:**
- Agents have constrained context windows
- Return high-signal information, not exhaustive data dumps
- Default to human-readable identifiers over technical codes

**Design Actionable Error Messages:**
- Error messages should guide agents toward correct usage
- Suggest specific next steps: "Try using filter='active_only'"
- Make errors educational, not just diagnostic

#### Study Documentation

- **MCP Protocol**: `https://modelcontextprotocol.io/`
- **Python SDK**: `https://github.com/modelcontextprotocol/python-sdk`
- **TypeScript SDK**: `https://github.com/modelcontextprotocol/typescript-sdk`

## Phase 2: Implementation

### Python (FastMCP)

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description that helps the LLM understand when to use this."""
    # Implementation
    return result
```

### TypeScript/Node

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

// Create server instance
const server = new Server(
  { name: "my-server", version: "1.0.0" },
  { capabilities: {} }
);

// Define tools
server.setRequestHandler("tools/list", async () => {
  return {
    tools: [{
      name: "my_tool",
      description: "Tool description",
      inputSchema: {
        type: "object",
        properties: {
          param: { type: "string", description: "Parameter description" }
        },
        required: ["param"]
      }
    }]
  };
});
```

## Phase 3: Testing

1. Test tools manually with the LLM
2. Create realistic evaluation scenarios
3. Iterate based on actual agent performance

## Best Practices

1. **Tool Names**: Reflect how humans think about tasks
2. **Descriptions**: Be descriptive about what the tool does
3. **Error Handling**: Provide actionable error messages
4. **Response Format**: Return concise, high-signal information
5. **Idioms**: Use human-readable identifiers

## Common Frameworks

| Language | Framework |
|----------|-----------|
| Python | FastMCP, mcp-server |
| Node/TypeScript | @modelcontextprotocol/sdk |
