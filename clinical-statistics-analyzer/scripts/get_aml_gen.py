from docx import Document
doc = Document('/Users/kimhawk/Library/CloudStorage/Dropbox/Current studies/AML studies/SAPHIRE/SAPPHIRE-G/Protocol/3.SAPPIRE_G CRF_Ver 1.1_20210518.docx')
for t in doc.tables:
    for row in t.rows:
        if "AML with recurrent genetics" in row.cells[0].text:
            print("FOUND IN TABLE:", repr(row.cells[0].text), repr(row.cells[1].text))
