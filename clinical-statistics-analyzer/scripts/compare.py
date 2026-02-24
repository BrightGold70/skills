import pandas as pd
import json

df = pd.read_excel('/Users/kimhawk/Library/CloudStorage/Dropbox/Current studies/AML studies/SAPHIRE/SAPPHIRE-G/CRF/사파G_CRF 작성본/SAPHIRE_G_CRF (Full_Ver).xlsx', header=None)
excel_headers = []
for i in range(len(df.columns)):
    val = df.iloc[2, i]
    if pd.isna(val):
        val = df.iloc[1, i]
    if pd.isna(val):
        val = df.iloc[0, i]
    raw_str = str(val).strip()
    if raw_str != 'nan' and raw_str:
        excel_headers.append(raw_str)

crf_df = pd.read_csv('/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer/data/crf_mapping.csv')
crf_exprs = crf_df['Variable Expression'].dropna().tolist()
crf_names = crf_df['Variable Name'].dropna().tolist()

matches = []
for eh in excel_headers:
    eh_clean = eh.lower().replace('\ufeff', '').strip()
    found_match = None
    for i, ce in enumerate(crf_exprs):
        if eh_clean in str(ce).lower() or str(ce).lower() in eh_clean:
            found_match = (crf_names[i], ce)
            break
    if found_match:
        matches.append({"excel_header": eh, "crf_var": found_match[0], "crf_expr": found_match[1]})
    else:
        matches.append({"excel_header": eh, "crf_var": None, "crf_expr": None})

out_df = pd.DataFrame(matches)
out_df.to_csv("excel_crf_comparison.csv", index=False)
print(f"Matched {len([m for m in matches if m['crf_var']])} out of {len(excel_headers)} excel headers.")
