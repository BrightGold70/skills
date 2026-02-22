# WebMCP Explainer Skill

## Overview

**WebMCP** (Web Model Context Protocol) is an emerging W3C web standard that enables websites to expose AI-callable tools directly through the browser. This skill explains WebMCP to users and helps them understand its relevance to browser automation tasks.

## When to Use This Skill

Use this skill when:
- User asks "What is WebMCP?"
- User wants to know about AI agent browser interaction standards
- User asks about the future of browser automation
- User wants to compare WebMCP vs traditional DOM scraping
- User asks about MCP-B or browser-based MCP implementations

## What WebMCP Provides

### Core Capability
WebMCP allows websites to register structured tools via `navigator.modelContext.registerTool()`:

```javascript
navigator.modelContext.registerTool({
  name: "search_products",
  description: "Search products with filters",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string" },
      minPrice: { type: "number" },
      maxPrice: { type: "number" }
    }
  },
  handler: async (params) => {
    return await api.search(params);
  }
});
```

### Key Benefits

| Benefit | Traditional Approach | WebMCP Approach |
|---------|---------------------|------------------|
| **Reliability** | DOM selectors break easily | Structured API calls |
| **Token Efficiency** | Parse HTML/screenshots | Direct structured data |
| **Speed** | Visual rendering needed | Instant API response |
| **Precision** | Pixel guessing | Exact parameter binding |

### Current Limitations

- **Early Stage**: Chrome 146 Canary only (Feb 2026)
- **Limited Adoption**: Requires websites to implement WebMCP
- **User-Present**: Optimized for interactive sessions, not headless scraping

## OpenCode Integration Context

### Existing Browser Capabilities
OpenCode already has strong browser automation:

| Skill | Use Case |
|-------|----------|
| `playwright` | Full E2E testing, cross-browser |
| `agent-browser` | Simple CLI automation |
| `chrome-devtools` | Low-level CDP debugging |

### WebMCP Integration Potential

Future integration could enable:
1. **Tool Discovery**: Detect WebMCP endpoints on websites
2. **Structured Interactions**: Use registered tools instead of DOM scraping
3. **Fallback Handling**: Graceful degradation to DOM scraping for non-WebMCP sites

## Resources

- [Chrome Developers: WebMCP Early Preview](https://developer.chrome.com/blog/webmcp-epp)
- [MCP-B Documentation](https://docs.mcp-b.ai)
- [W3C WebMCP Explainer](https://github.com/webmachinelearning/webmcp)

## Related Skills

- `playwright` - Full browser automation
- `agent-browser` - Simple browser automation
- `chrome-devtools` - DevTools-level control

## Guidance for Users

When users ask about WebMCP:

1. **Explain the concept** clearly (structured tool exposure vs DOM scraping)
2. **Acknowledge early stage** (Chrome Canary, limited adoption)
3. **Connect to existing skills** (how it would enhance current capabilities)
4. **Suggest monitoring** (WebMCP is evolving rapidly)

---

*Last Updated: February 2026*
