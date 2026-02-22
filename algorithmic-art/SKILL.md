---
name: algorithmic-art
description: Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use when users request creating generative art, flow fields, or particle systems. Create original algorithmic art, not copying existing artists.
---

# Algorithmic Art Creation

This skill creates generative art through computational processes.

## Two-Step Process

1. **Algorithmic Philosophy Creation** (.md file)
2. **Express in Code** (.html + .js files using p5.js)

## Step 1: Create Philosophy

Name your movement (1-2 words): "Organic Turbulence", "Quantum Harmonics", etc.

Articulate the philosophy (4-6 paragraphs):
- Computational processes and mathematical relationships
- Noise functions and randomness patterns
- Particle behaviors and field dynamics
- Temporal evolution and system states
- Parametric variation and emergent complexity

**Key Guidelines:**
- Emphasize craftsmanship - the algorithm should appear meticulously crafted
- Leave creative space for implementation choices
- Focus on algorithmic expression, not static images

## Example Philosophies

**"Organic Turbulence"**
- Flow fields driven by layered Perlin noise
- Thousands of particles following vector forces
- Color emerges from velocity and density

**"Quantum Harmonics"**
- Particles initialized on a grid with phase values
- Phase interference creates bright nodes and voids
- Simple harmonic motion generates complex mandalas

**"Recursive Whispers"**
- Branching structures that subdivide recursively
- Golden ratios constrain randomization
- Line weights diminish with recursion depth

## Step 2: Implement with p5.js

```javascript
// Basic p5.js sketch structure
function setup() {
  createCanvas(800, 600);
  // Initialize particles, fields, etc.
}

function draw() {
  // Update and draw particles
  // Apply forces, update positions
  // Render to canvas
}
```

## Key Concepts

- **Seeded randomness**: Use randomSeed() for reproducibility
- **Noise fields**: Perlin noise for organic movement
- **Particle systems**: Thousands of agents following rules
- **Flow fields**: Vector fields guiding particle motion
- **Emergent behavior**: Complex patterns from simple rules

## Tools

- **p5.js**: JavaScript library for creative coding
- **Canvas API**: HTML5 canvas for rendering

## Output

- Philosophy document (.md)
- Interactive p5.js sketch (.html + .js)
- Unique generative art on each run
