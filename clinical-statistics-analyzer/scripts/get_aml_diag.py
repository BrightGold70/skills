from docx import Document
doc = Document('/Users/kimhawk/Library/CloudStorage/Dropbox/Current studies/AML studies/SAPHIRE/SAPPHIRE-G/Protocol/3.SAPPIRE_G CRF_Ver 1.1_20210518.docx')
found = False
for p in doc.paragraphs:
    if "AML Diagnosis" in p.text:
        found = True
    if found:
        print(repr(p.text.strip()))
        if "Aute leukemia" in p.text:
            break
