---
name: brand-guidelines
description: Applies brand colors and typography to artifacts. Use when brand colors, visual formatting, or company design standards apply.
---

# Brand Guidelines

Apply consistent brand identity to your designs.

## Colors

### Main Colors
- **Dark**: `#141413` - Primary text and dark backgrounds
- **Light**: `#faf9f5` - Light backgrounds
- **Mid Gray**: `#b0aea5` - Secondary elements
- **Light Gray**: `#e8e6dc` - Subtle backgrounds

### Accent Colors
- **Orange**: `#d97757` - Primary accent
- **Blue**: `#6a9bcc` - Secondary accent
- **Green**: `#788c5d` - Tertiary accent

## Typography

- **Headings**: Poppins (fallback: Arial)
- **Body Text**: Lora (fallback: Georgia)

## Application

### CSS Variables
```css
:root {
  --brand-dark: #141413;
  --brand-light: #faf9f5;
  --brand-orange: #d97757;
  --brand-blue: #6a9bcc;
  --brand-green: #788c5d;
  --font-heading: 'Poppins', Arial, sans-serif;
  --font-body: 'Lora', Georgia, serif;
}
```

### Font Sizing
- Headings (24pt+): Poppins
- Body text: Lora
- Smart color selection based on background

### Shapes & Accents
- Non-text shapes use accent colors
- Cycle through orange, blue, green
- Maintain visual interest while staying on-brand

## Best Practices

1. Use consistent color palette across all materials
2. Apply fonts appropriately (headings vs body)
3. Use accent colors sparingly for impact
4. Ensure proper contrast for accessibility
5. Preserve text hierarchy and formatting
