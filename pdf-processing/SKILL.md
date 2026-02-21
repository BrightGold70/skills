---
name: pdf-processing
description: Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms.
---

# PDF Processing Guide

This skill covers essential PDF processing operations.

## Quick Start (Python)

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Common Operations

### Merge PDFs
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

### Split PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

### Extract Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
```

### Rotate Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()
page = reader.pages[0]
page.rotate(90)  # Rotate 90 degrees clockwise
writer.add_page(page)
with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

## Text and Table Extraction (pdfplumber)

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    # Extract text from all pages
    for page in pdf.pages:
        text = page.extract_text()
    
    # Extract tables
    for page in pdf.pages:
        tables = page.extract_tables()
```

## Fill PDF Forms

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("form.pdf")
writer = PdfWriter()

# Copy all pages
for page in reader.pages:
    writer.add_page(page)

# Fill form fields
if "/AcroForm" in reader.trailer["/Root"]:
    writer.add_form_topname("/AcroForm")
    writer.update_widget_form_value(
        "/AcroForm",
        {"field_name": "value"}
    )

with open("filled.pdf", "wb") as output:
    writer.write(output)
```

## Install Dependencies

```bash
pip install pypdf pdfplumber
```

## Use Cases

- Extract text from research papers
- Merge multiple documents into one
- Split large PDFs by chapters
- Extract tables from reports
- Fill out PDF forms programmatically
- Add page numbers or watermarks
- Convert PDF to images
