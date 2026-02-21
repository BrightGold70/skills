---
name: slack-gif-creator
description: Create animated GIFs optimized for Slack. Use when users request GIFs for Slack reactions or messages.
---

# Slack GIF Creator

Create animated GIFs optimized for Slack.

## Slack Requirements

### Dimensions
- **Emoji GIFs**: 128x128 (recommended)
- **Message GIFs**: 480x480

### Parameters
- **FPS**: 10-30 (lower = smaller file)
- **Colors**: 48-128 (fewer = smaller file)
- **Duration**: Keep under 3 seconds for emoji GIFs

## Core Workflow (Python)

```python
from PIL import Image, ImageDraw

# Create frames
frames = []
width, height = 128, 128

for i in range(12):  # 12 frames
    frame = Image.new('RGB', (width, height), (240, 248, 255))
    draw = ImageDraw.Draw(frame)
    
    # Draw animation using PIL primitives
    # circles, polygons, lines, etc.
    
    frames.append(frame)

# Save as GIF
frames[0].save(
    'output.gif',
    save_all=True,
    append_images=frames[1:],
    duration=100,  # ms per frame
    loop=0
)
```

## Working with Images

### Load User Images
```python
from PIL import Image

uploaded = Image.open('file.png')
# Use directly or as inspiration
```

### Drawing Primitives
```python
draw = ImageDraw.Draw(frame)

# Circle
draw.ellipse([x1, y1, x2, y2], fill='color')

# Rectangle
draw.rectangle([x1, y1, x2, y2], fill='color')

# Line
draw.line([x1, y1, x2, y2], fill='color', width=3)

# Text
draw.text((x, y), "text", fill='color')
```

## Optimization

```python
# Optimize for Slack
frames[0].save(
    'output.gif',
    save_all=True,
    append_images=frames[1:],
    duration=100,
    optimize=True
)
```

## Best Practices

1. Keep dimensions small (128x128 for emoji)
2. Use fewer colors (48-64)
3. Limit duration (under 3 seconds)
4. Test in Slack before sharing
5. Use simple animations for better compression
