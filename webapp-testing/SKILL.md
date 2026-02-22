---
name: webapp-testing
description: Toolkit for testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, and capturing browser screenshots.
---

# Web Application Testing

This skill helps test local web applications using Playwright.

## Decision Tree

```
User task → Is it static HTML?
    ├─ Yes → Read HTML file directly to identify selectors
    │         └─ Write Playwright script using selectors
    │
    └─ No (dynamic webapp) → Is the server already running?
        ├─ No → Start server first, then write Playwright script
        └─ Yes → Reconnaissance-then-action:
            1. Navigate and wait for networkidle
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
```

## Basic Playwright Script

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto('http://localhost:5173')
    page.wait_for_load_state('networkidle')
    
    # Your automation logic
    page.click('button#submit')
    page.fill('input#name', 'Test User')
    
    # Take screenshot
    page.screenshot(path='screenshot.png')
    
    browser.close()
```

## Common Operations

### Click Elements
```python
page.click('button#submit')
page.click('.nav-link', nth=0)  # First matching
```

### Fill Forms
```python
page.fill('input#email', 'test@example.com')
page.type('input#name', 'John')  # Type with delays
```

### Wait for Elements
```python
page.wait_for_selector('.loading', state='hidden')
page.wait_for_url('**/dashboard')
```

### Get Text/Attributes
```python
text = page.locator('.title').inner_text()
href = page.locator('a').first.get_attribute('href')
```

### Handle Dialogs
```python
page.on('dialog', lambda dialog: dialog.accept())
page.on('dialog', lambda dialog: dialog.dismiss())
```

## Install Dependencies

```bash
pip install playwright
playwright install chromium
```

## Headless vs Headed

- **Headless (default)**: Faster, no visible browser
- **Headed**: `browser = p.chromium.launch(headless=False)` - Visible browser for debugging

## Best Practices

1. Always wait for `networkidle` on dynamic apps
2. Use specific selectors (IDs > classes > text)
3. Take screenshots for debugging
4. Handle loading states explicitly
5. Clean up resources (close browser)
