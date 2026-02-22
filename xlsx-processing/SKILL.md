---
name: xlsx-processing
description: Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization.
---

# Spreadsheet Processing Guide

This skill handles Excel/spreadsheet operations.

## Requirements

### Zero Formula Errors
- All Excel files MUST have ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### Preserve Existing Templates
- Study and match existing format when modifying files
- Never impose standardized formatting on files with established patterns

## Color Coding Standards (Financial Models)

- **Blue text (RGB: 0,0,255)**: Hardcoded inputs
- **Black text**: Formulas and calculations
- **Green text (RGB: 0,128,0)**: Links to other worksheets
- **Red text (RGB: 255,0,0)**: External links to other files
- **Yellow background**: Key assumptions

## Number Formatting

- **Years**: Text strings ("2024" not "2,024")
- **Currency**: $#,##0 with units in headers
- **Zeros**: Use "-" via formatting
- **Percentages**: 0.0% format (one decimal)
- **Multiples**: 0.0x format
- **Negative numbers**: Use parentheses (123)

## Python Libraries

### openpyxl - Read/Write Excel
```python
from openpyxl import Workbook, load_workbook

# Create new workbook
wb = Workbook()
ws = wb.active
ws['A1'] = 'Hello'
wb.save('example.xlsx')

# Load existing
wb = load_workbook('example.xlsx')
ws = wb.active
```

### pandas - Data Analysis
```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx', sheet_name='Sheet1')

# Write Excel
df.to_excel('output.xlsx', index=False)

# Multiple sheets
with pd.ExcelWriter('output.xlsx') as writer:
    df1.to_excel(writer, sheet_name='Sheet1')
    df2.to_excel(writer, sheet_name='Sheet2')
```

### xlwings - Excel Automation
```python
import xlwings as xw

# Open Excel
app = xw.App()
wb = app.books.open('file.xlsx')

# Work with sheets
sheet = wb.sheets[0]
sheet.range('A1').value = 'Hello'

wb.save()
app.quit()
```

## Common Operations

### Add Formulas
```python
ws['C1'] = '=A1+B1'
```

### Conditional Formatting
```python
from openpyxl.formatting.rule import FormulaRule

ws.conditional_formatting.add('A1:A10',
    FormulaRule(formula=['$A1>100'], fill=red_fill))
```

### Charts
```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
data = Reference(ws, min_col=2, min_row=1, max_row=10)
chart.add_data(data)
ws.add_chart(chart, 'E5')
```

## Install Dependencies

```bash
pip install openpyxl pandas xlwings
```

## Use Cases

- Create financial models
- Data analysis and visualization
- Generate reports
- Automate Excel workflows
- Extract data from Excel files
