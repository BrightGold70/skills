# WebMCP Browser Skill

## Overview

This skill enables AI agents to interact with WebMCP-enabled websites using the MCP-B polyfill. It provides structured tool discovery and invocation for websites that expose AI-callable tools via the WebMCP standard.

## When to Use This Skill

Use this skill when:
- User wants to interact with WebMCP-enabled websites
- Website exposes structured tools via `navigator.modelContext`
- User wants faster, more reliable browser automation (vs DOM scraping)
- Building integrations with websites that support WebMCP

## Prerequisites

```bash
# Install MCP-B polyfill
npm install @mcp-b/global

# Or use React hooks version
npm install @mcp-b/react-webmcp
```

## Core Capabilities

### 1. Tool Discovery

```javascript
// Check if website supports WebMCP
if (navigator.modelContext) {
  const tools = await navigator.modelContext.getTools();
  console.log('Available tools:', tools.map(t => t.name));
}
```

### 2. Tool Invocation

```javascript
// Call a registered tool directly
const result = await navigator.modelContext.callTool('search_products', {
  query: 'laptop',
  category: 'electronics',
  maxPrice: 1000
});
```

### 3. Polyfill Fallback

For browsers without native WebMCP support:

```javascript
// MCP-B provides polyfill
import { registerTool, getTools, callTool } from '@mcp-b/global';

registerTool({
  name: 'my_tool',
  description: 'My custom tool',
  inputSchema: { type: 'object', properties: {} },
  handler: async () => ({ result: 'success' })
});
```

## Integration with OpenCode

### Using with Playwright

```javascript
// Inject MCP-B polyfill into page
await page.addScriptTag({
  content: `
    // MCP-B polyfill would be loaded here
    // Check for navigator.modelContext
  `
});

// Discover tools
const tools = await page.evaluate(() => {
  if (navigator.modelContext) {
    return navigator.modelContext.getTools();
  }
  return [];
});
```

### Tool Detection Pattern

```javascript
async function detectWebMCP(page) {
  const result = await page.evaluate(() => {
    if (typeof navigator !== 'undefined' && navigator.modelContext) {
      return { supported: true };
    }
    // Check for MCP-B polyfill
    if (typeof window !== 'undefined' && window.mcpClient) {
      return { supported: true, polyfill: true };
    }
    return { supported: false };
  });
  return result;
}
```

## Available MCP-B Packages

| Package | Purpose |
|---------|---------|
| `@mcp-b/global` | W3C Web Model Context API polyfill |
| `@mcp-b/react-webmcp` | React hooks for WebMCP |
| `@mcp-b/transports` | Browser transport implementations |
| `@mcp-b/webmcp-ts-sdk` | TypeScript SDK for MCP-B |

## Example Workflows

### E-commerce Automation

```javascript
// 1. Navigate to WebMCP-enabled site
await page.goto('https://example-shop.com');

// 2. Detect WebMCP support
const webmcpSupport = await detectWebMCP(page);

// 3. If supported, use structured tools
if (webmcpSupport.supported) {
  const products = await page.evaluate(() => 
    navigator.modelContext.callTool('search', { query: 'headphones' })
  );
} else {
  // Fallback to DOM scraping
  await page.click('.search-button');
  // ... DOM-based interaction
}
```

### Form Submission

```javascript
// Instead of DOM selectors
// await page.fill('#email', 'test@example.com');
// await page.click('button[type="submit"]');

// Use structured tool
await page.evaluate(() =>
  navigator.modelContext.callTool('submit_contact_form', {
    email: 'test@example.com',
    message: 'Hello world'
  })
);
```

## Best Practices

1. **Always check for WebMCP support first** before falling back to DOM
2. **Use structured tools when available** for reliability
3. **Implement fallback** for non-WebMCP websites
4. **Handle errors gracefully** - WebMCP may not be available

## Error Handling

```javascript
async function safeCallTool(page, toolName, params) {
  try {
    const result = await page.evaluate(({ name, params }) => {
      if (navigator.modelContext) {
        return navigator.modelContext.callTool(name, params);
      }
      throw new Error('WebMCP not supported');
    }, { name: toolName, params });
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

## Related Skills

- `playwright` - Full browser automation
- `webmcp-explainer` - WebMCP concept explanation
- `chrome-devtools` - Low-level browser control

---

*Last Updated: February 2026*
