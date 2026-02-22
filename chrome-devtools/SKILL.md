---
name: chrome-devtools
description: Chrome DevTools Protocol (CDP) browser automation. Use when debugging frontend issues, analyzing performance, inspecting network requests, testing responsive designs, or needing DevTools-level browser control. Triggers: "debug this page", "check performance", "inspect network", "test responsive", "emulate mobile", "capture console errors", "analyze web vitals".
allowed-tools: ChromeDevTools(*)
---

# Chrome DevTools Protocol (CDP) Automation

## Overview

The Chrome DevTools MCP server provides direct access to Chrome's debugging protocol. It gives AI assistants "eyes in the browser" to see runtime behavior, debug issues, and analyze performance.

**MCP Server**: `chrome-devtools-mcp` (Google Chrome DevTools team)
**Version**: 0.15.1+ 
**Use Case**: Low-level browser debugging, performance analysis, DevTools automation

---

## When to Use This Skill

Use `chrome-devtools` when:
- Debugging JavaScript errors or console issues
- Analyzing page performance and Core Web Vitals
- Inspecting network requests/responses
- Testing responsive designs with device emulation
- Capturing console logs and errors
- Taking accessibility snapshots
- Evaluating JavaScript in page context
- Performance profiling and tracing

**Prefer `playwright` (built-in) when**:
- Cross-browser testing (Firefox, WebKit)
- E2E test automation
- Recording videos of interactions
- Complex test scenarios with assertions

**Prefer `agent-browser` CLI when**:
- Simple browser automation tasks
- State persistence across sessions
- Quick one-off interactions

---

## Tool Catalog

### Navigation Tools

| Tool | Description | Example |
|------|-------------|---------|
| `chrome-devtools_navigate_page` | Navigate to URL | Navigate to https://example.com |
| `chrome-devtools_new_page` | Open new tab | New tab at URL |
| `chrome-devtools_close_page` | Close current tab | Close tab |
| `chrome-devtools_list_pages` | List all open tabs | Get tab list |
| `chrome-devtools_select_page` | Switch to tab | Select by index |
| `chrome-devtools_resize_page` | Resize viewport | Set 1920x1080 |

### Interaction Tools

| Tool | Description | Example |
|------|-------------|---------|
| `chrome-devtools_click` | Click element | Click button |
| `chrome-devtools_hover` | Hover over element | Hover menu |
| `chrome-devtools_drag` | Drag and drop | Drag element |
| `chrome-devtools_fill` | Type in input | Fill username |
| `chrome-devtools_fill_form` | Fill multiple fields | Fill entire form |
| `chrome-devtools_upload_file` | Upload file | Upload image |
| `chrome-devtools_press_key` | Press keyboard | Press Enter |
| `chrome-devtools_wait_for` | Wait for text | Wait for "Loaded" |

### Inspection Tools

| Tool | Description | Example |
|------|-------------|---------|
| `chrome-devtools_take_snapshot` | Get a11y tree | Get DOM snapshot |
| `chrome-devtools_take_screenshot` | Screenshot | Capture page |
| `chrome-devtools_evaluate_script` | Run JavaScript | Execute JS in page |

### Network Tools

| Tool | Description | Example |
|------|-------------|---------|
| `chrome-devtools_list_network_requests` | List all requests | Get request log |
| `chrome-devtools_get_network_request` | Inspect request | Get headers/body |

### Console Tools

| Tool | Description | Example |
|------|-------------|---------|
| `chrome-devtools_list_console_messages` | List console output | Get logs |
| `chrome-devtools_get_console_message` | Get specific message | Get error details |

### Performance Tools

| Tool | Description | Example |
|------|-------------|---------|
| `chrome-devtools_performance_start_trace` | Start profiling | Begin trace |
| `chrome-devtools_performance_stop_trace` | Stop and save | End trace |
| `chrome-devtools_performance_analyze_insight` | Analyze results | Get insights |

### Emulation Tools

| Tool | Description | Example |
|------|-------------|---------|
| `chrome-devtools_emulate` | Set device metrics | Emulate iPhone |
| `chrome-devtools_handle_dialog` | Handle alert/confirm | Accept dialog |

---

## Common Patterns

### Debug Console Errors

```javascript
// 1. Navigate to page
chrome-devtools_navigate_page({ url: "https://example.com" })

// 2. Wait for load
chrome-devtools_wait_for({ text: "Page loaded" })

// 3. Check console for errors
chrome-devtools_list_console_messages({ level: "error" })

// 4. Get details of specific error
chrome-devtools_get_console_message({ msgid: 0 })
```

### Network Request Inspection

```javascript
// 1. Navigate and trigger API call
chrome-devtools_navigate_page({ url: "https://app.example.com/data" })
chrome-devtools_wait_for({ text: "Loading..." })

// 2. List network requests
chrome-devtools_list_network_requests({})

// 3. Inspect specific request
chrome-devtools_get_network_request({ reqid: "request-id-from-list" })
```

### Device Emulation

```javascript
// Emulate iPhone 14 Pro
chrome-devtools_emulate({
  viewport: {
    width: 393,
    height: 852,
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true,
    isLandscape: false
  }
})

// Then navigate - page renders as mobile
chrome-devtools_navigate_page({ url: "https://example.com" })
```

### JavaScript Evaluation

```javascript
// Get page title
chrome-devtools_evaluate_script({
  function: "() => document.title"
})

// Get element value
chrome-devtools_evaluate_script({
  function: "() => document.querySelector('#input').value"
})

// Trigger action
chrome-devtools_evaluate_script({
  function: "() => { document.querySelector('#btn').click(); }"
})
```

### Performance Tracing

```javascript
// 1. Start trace
chrome-devtools_performance_start_trace({
  reload: true,
  autoStop: true
})

// 2. Navigate (triggers reload-based trace)
chrome-devtools_navigate_page({ url: "https://example.com" })

// 3. Wait for trace to complete
chrome-devtools_wait_for({ time: 5 })

// 4. Stop trace
chrome-devtools_performance_stop_trace({ filePath: "trace.json" })

// 5. Analyze insights
chrome-devtools_performance_analyze_insight({
  insightSetId: "performance-insights",
  insightName: "LCP"
})
```

### Form Automation

```javascript
// 1. Get interactive snapshot
chrome-devtools_take_snapshot({})

// 2. Fill form fields
chrome-devtools_fill_form({
  fields: [
    { name: "Email", ref: "@element-ref", type: "textbox", value: "user@example.com" },
    { name: "Password", ref: "@element-ref", type: "textbox", value: "password123" }
  ]
})

// 3. Submit
chrome-devtools_click({ ref: "@submit-button" })

// 4. Handle dialog if present
chrome-devtools_handle_dialog({ accept: true })
```

---

## Performance Analysis

### Core Web Vitals

Use performance tracing to analyze:

| Metric | What It Measures | Target |
|--------|------------------|--------|
| **LCP** | Largest Contentful Paint | < 2.5s |
| **FID** | First Input Delay | < 100ms |
| **CLS** | Cumulative Layout Shift | < 0.1 |

```javascript
// Start performance measurement
chrome-devtools_performance_start_trace({ reload: true })

// Navigate to page
chrome-devtools_navigate_page({ url: "https://yoursite.com" })

// Wait for load
chrome-devtools_wait_for({ time: 3 })

// Stop and analyze
chrome-devtools_performance_stop_trace({})
chrome-devtools_performance_analyze_insight({
  insightSetId: "performance-insights",
  insightName: "LCPBreakdown"
})
```

### Network Performance

```javascript
// Clear cache and reload
chrome-devtools_list_network_requests({})

// Analyze request timing
chrome-devtools_get_network_request({ reqid: "request-id" })
// Returns: "timing": { "dns": 10, "connect": 50, "ssl": 20, "send": 1, "wait": 200, "receive": 50 }
```

---

## Accessibility Testing

```javascript
// Get accessibility tree
chrome-devtools_take_snapshot({ verbose: true })

// Returns full a11y tree with:
// - Roles (button, heading, link, etc.)
// - Names (aria-label, alt text, text content)
// - States (checked, disabled, expanded)
// - Properties (required, invalid)
```

---

## Troubleshooting

### Page Not Loading

```javascript
// Check for console errors
chrome-devtools_list_console_messages({ level: "error" })

// Check network failures
chrome-devtools_list_network_requests({})
// Look for failed requests (4xx, 5xx status)
```

### Element Not Found

```javascript
// Take fresh snapshot - DOM may have changed
chrome-devtools_take_snapshot({})

// Wait for element to appear
chrome-devtools_wait_for({ text: "Expected element" })

// Or evaluate JavaScript to check existence
chrome-devtools_evaluate_script({
  function: "() => !!document.querySelector('.target')"
})
```

### Slow Performance

```javascript
// Start trace
chrome-devtools_performance_start_trace({ reload: true })

// Navigate
chrome-devtools_navigate_page({ url: "https://slowsite.com" })

// Analyze
chrome-devtools_performance_analyze_insight({
  insightSetId: "performance-insights", 
  insightName: "DocumentLatency"
})
```

---

## Tool Selection Guide

| Scenario | Recommended Tool |
|----------|------------------|
| Debug JS errors | `chrome-devtools` + console tools |
| Performance analysis | `chrome-devtools` + performance tools |
| Network inspection | `chrome-devtools` + network tools |
| E2E testing | `playwright` |
| Simple automation | `agent-browser` |
| Cross-browser | `playwright` |
| Mobile emulation | `chrome-devtools` |
| Screenshot comparison | `playwright` |
| Video recording | `playwright` |
| State persistence | `agent-browser` |

---

## Cross-Reference

- **Playwright Skill**: Cross-browser E2E testing, video recording, complex assertions
- **Agent-Browser Skill**: Simple CLI-based browser automation with state persistence
