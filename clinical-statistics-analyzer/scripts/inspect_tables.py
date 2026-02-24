from docx import Document
import sys

doc = Document('/Users/kimhawk/Library/CloudStorage/Dropbox/Current studies/AML studies/SAPHIRE/SAPPHIRE-G/Protocol/3.SAPPIRE_G CRF_Ver 1.1_20210518.docx')
for i, table in enumerate(doc.tables[:10]):
    print(f"--- Table {i} ---")
    for j, row in enumerate(table.rows[:5]):
        cells = [c.text.replace("\n", " ").strip() for c in row.cells]
        print(f"Row {j}: {cells}")
