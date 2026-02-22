---
name: docx-processing
description: Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction.
---

# DOCX Processing Guide

This skill handles Word document (.docx) operations.

## Workflow Decision Tree

### Reading/Analyzing Content
- Use text extraction with pandoc
- Use raw XML access for comments, complex formatting

### Creating New Document
- Use docx-js (JavaScript/TypeScript)
- Use python-docx (Python)

### Editing Existing Document
- Simple changes: Use python-docx
- Someone else's document: Use redlining workflow
- Legal/academic docs: Use redlining workflow (required)

## Text Extraction

Use pandoc to convert to markdown:

```bash
# Convert document to markdown
pandoc path-to-file.docx -o output.md

# With tracked changes
pandoc --track-changes=all path-to-file.docx -o output.md
# Options: --track-changes=accept/reject/all
```

## Creating New Documents

### Python (python-docx)
```python
from docx import Document

doc = Document()
doc.add_heading('Title', 0)
doc.add_paragraph('Hello, world!')

# Add formatted text
run = doc.add_paragraph().add_run('Bold Text')
run.bold = True

doc.save('document.docx')
```

### JavaScript/TypeScript (docx-js)
```javascript
import { Document, Packer, Paragraph, TextRun } from "docx";

const doc = new Document({
    sections: [{
        properties: {},
        children: [
            new Paragraph({
                children: [
                    new TextRun("Hello, World!")
                ],
            }),
        ],
    }],
});

const buffer = await Packer.toBuffer(doc);
```

## Editing Existing Documents

### Basic Editing (python-docx)
```python
from docx import Document

doc = Document("existing.docx")

# Add paragraph
doc.add_paragraph("New paragraph")

# Edit existing
for paragraph in doc.paragraphs:
    if "old text" in paragraph.text:
        paragraph.text = paragraph.text.replace("old text", "new text")

doc.save("edited.docx")
```

### Accessing Raw XML

Unpack the document to access XML:
```bash
python -c "import zipfile; zipfile.ZipFile('file.docx').extractall('output_dir')"
```

Key files:
- `word/document.xml` - Main content
- `word/comments.xml` - Comments
- `word/media/` - Images
- Tracked changes: `<w:ins>` (insertions), `<w:del>` (deletions)

## Redlining Workflow (Tracked Changes)

For professional document editing with tracked changes:

1. Extract original content to markdown
2. Create review document with proposed changes
3. Use python-docx or ooxml library for tracked changes

```python
# Example: Add text with track changes
from docx.oxml.ns import qn

# Add insertion
p = doc.add_paragraph()
ins = qn('w:ins')
p._element.get_or_add_pPr().add(ins)
```

## Install Dependencies

```bash
pip install python-docx
npm install docx
```

## Use Cases

- Create professional reports
- Edit existing documents while preserving formatting
- Add comments and tracked changes
- Extract content for analysis
- Batch process multiple documents
- Convert between formats
