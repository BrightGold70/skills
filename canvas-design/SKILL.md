---
name: canvas-design
description: Create beautiful visual art in .png and .pdf documents using design philosophy. Use when user asks to create posters, art, designs, or static visual pieces. Create original designs, never copying existing artists.
---

# Canvas Design

Create visual art through design philosophy - aesthetic movements expressed visually.

## Two-Step Process

1. **Design Philosophy Creation** (.md file)
2. **Express Visually** (.pdf or .png file)

## Step 1: Create Philosophy

Name your movement (1-2 words): "Brutalist Joy", "Chromatic Silence", "Organic Systems"

Articulate the philosophy (4-6 paragraphs) covering:
- Space and form
- Color and material
- Scale and rhythm
- Composition and balance
- Visual hierarchy

**Key Guidelines:**
- Emphasize craftsmanship - work should appear meticulously crafted
- Keep text minimal - essential only, integrated as visual element
- Express ideas through space, form, color, composition

## Example Philosophies

**"Concrete Poetry"**
- Massive color blocks, sculptural typography
- Brutalist spatial divisions
- Text as rare, powerful gesture - never paragraphs

**"Chromatic Language"**
- Geometric precision where color zones create meaning
- Typography minimal - small sans-serif labels
- Information encoded spatially and chromatically

**"Analog Meditation"**
- Paper grain, ink bleeds, vast negative space
- Photography dominates
- Japanese photobook aesthetic

**"Geometric Silence"**
- Grid-based precision, bold graphics
- Dramatic negative space
- Swiss formalism meets Brutalist honesty

## Implementation

### Python (PIL/Pillow)
```python
from PIL import Image, ImageDraw, ImageFont

# Create canvas
img = Image.new('RGB', (800, 1200), '#faf9f5')
draw = ImageDraw.Draw(img)

# Draw shapes, text, etc.
draw.rectangle([100, 100, 700, 300], fill='#141413')
draw.text((150, 180), "TITLE", fill='#faf9f5')
```

### Use Cases
- Posters
- Art prints
- Visual designs
- Presentations
- Marketing materials

## Principles

- **Visual over textual**: Communicate through design, not words
- **Minimal text**: Only essential words, integrated as visual element
- **Spatial expression**: Ideas live in space, form, color
- **Originality**: Create unique aesthetics, never copy existing work
