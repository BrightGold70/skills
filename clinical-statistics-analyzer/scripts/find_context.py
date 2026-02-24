from docx import Document
doc = Document('/Users/kimhawk/Library/CloudStorage/Dropbox/Current studies/AML studies/SAPHIRE/SAPPHIRE-G/Protocol/3.SAPPIRE_G CRF_Ver 1.1_20210518.docx')
for i, p in enumerate(doc.paragraphs):
    if "aml_gen" in p.text or "RBC" in p.text:
        print(f"PARA {i}: {repr(p.text)}")
