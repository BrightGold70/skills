---
name: pptx-processing
description: Comprehensive PowerPoint creation, editing, and presentation building with support for slides, shapes, charts, and formatting.
---

# PowerPoint Processing Guide

This skill handles PowerPoint (.pptx) operations.

## Python Libraries

### python-pptx
```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

# Create presentation
prs = Presentation()
slide_layout = prs.slide_layouts[1]  # Title and Content
slide = prs.slides.add_slide(slide_layout)
title = slide.shapes.title
title.text = "My Title"

# Add content
body = slide.placeholders[1]
tf = body.text_frame
tf.text = "First bullet point"
p = tf.add_paragraph()
p.text = "Second bullet point"
p.level = 1

prs.save('presentation.pptx')
```

### Creating from HTML
```bash
# Use pandoc for HTML to PPTX conversion
pandoc -o output.pptx input.html
```

## Common Operations

### Add Images
```python
from pptx.util import Inches

# Add image to slide
slide.shapes.add_picture(
    'image.png',
    Inches(1), Inches(1),
    width=Inches(4)
)
```

### Add Charts
```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

chart_data = CategoryChartData()
chart_data.categories = ['Q1', 'Q2', 'Q3', 'Q4']
chart_data.add_series('Revenue', (10, 40, 30, 50))

x, y, cx, cy = Inches(2), Inches(2), Inches(6), Inches(4.5)
chart = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data
).chart
```

### Format Text
```python
from pptx.dml.color import RGBColor

# Format text
paragraph = tf.paragraphs[0]
run = paragraph.runs[0]
run.font.size = Pt(24)
run.font.bold = True
run.font.color.rgb = RGBColor(0, 0, 255)
```

### Add Tables
```python
from pptx.table import Table
from pptx.util import Inches

rows, cols = 3, 3
left, top, width, height = Inches(2), Inches(2), Inches(6), Inches(2)
table = slide.shapes.add_table(rows, cols, left, top, width, height).table

# Set cell values
table.cell(0, 0).text = 'Header 1'
```

## Slide Layouts

- 0: Title
- 1: Title and Content
- 5: Title Only
- 6: Blank

## Use Cases

- Create presentations from scratch
- Convert documents to slides
- Add charts and graphs
- Format consistently
- Add speaker notes
- Merge presentations
