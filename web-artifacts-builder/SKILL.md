---
name: web-artifacts-builder
description: Create elaborate HTML artifacts using React, Tailwind CSS, and shadcn/ui. Use for complex artifacts requiring state management, routing, or UI components.
---

# Web Artifacts Builder

Create complex frontend artifacts using modern web technologies.

## Stack

- React 18 + TypeScript
- Vite (development)
- Tailwind CSS
- shadcn/ui components
- Parcel (bundling)

## Workflow

1. **Initialize project** with required dependencies
2. **Develop artifact** by editing generated code
3. **Bundle to single HTML** for sharing
4. **Display to user**

## Step 1: Initialize

```bash
# Create React + TypeScript project
npm create vite@latest artifact-name -- --template react-ts
cd artifact-name

# Install Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install shadcn/ui dependencies
npx shadcn-ui@latest init

# Install components
npx shadcn-ui@latest add button card input etc.
```

## Step 2: Develop

Edit files in the project:
- `src/App.tsx` - Main component
- `src/components/` - UI components
- `src/index.css` - Global styles

### shadcn/ui Components
Available at: https://ui.shadcn.com/docs/components

## Step 3: Bundle

Use a bundler to create single HTML file:

```bash
# Using parcel (example)
npm install parcel html-inline
npx parcel build src/index.html --no-source-maps
# Then inline assets
```

Or use Vite with plugins for single-file output.

## Design Guidelines

**Avoid "AI slop":**
- ❌ Excessive centered layouts
- ❌ Purple gradients on white
- ❌ Uniform rounded corners
- ❌ Inter font

**Instead:**
- ✓ Unique typography choices
- ✓ Cohesive color palette
- ✓ Unexpected layouts
- ✓ Purposeful animations

## Testing (Optional)

Use Playwright or browser tools to verify the artifact works before sharing.
