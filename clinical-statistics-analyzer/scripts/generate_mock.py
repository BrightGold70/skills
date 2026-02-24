import pandas as pd
import numpy as np
import datetime
import os

np.random.seed(42)

n_patients = 100
patient_ids = [f"PT-{str(i).zfill(3)}" for i in range(1, n_patients + 1)]

# Demographics
ages = np.random.normal(55, 12, n_patients).astype(int)
sexes = np.random.choice(['Male', 'Female'], n_patients)
arms = np.random.choice(['Arm A', 'Arm B'], n_patients)
status = np.random.choice([0, 1], n_patients, p=[0.7, 0.3]) # 1 = dead
time_months = np.random.exponential(24, n_patients)

# Base DataFrame
df_base = pd.DataFrame({
    'PatientID': patient_ids,
    'Age': ages,
    'Sex': sexes,
    'TreatmentArm': arms,
    'SurvivalStatus': status,
    'SurvivalTime_Months': np.round(time_months, 1)
})

# Longitudinal Data for Sankey/Swimmer
records = []
drugs = ['Imatinib', 'Dasatinib', 'Nilotinib', 'Ponatinib']

for pid in patient_ids:
    num_lines = np.random.randint(1, 4)
    start_day = 0
    for line in range(1, num_lines + 1):
        drug = np.random.choice(drugs)
        dur = np.random.randint(30, 365)
        end_day = start_day + dur
        
        records.append({
            'PatientID': pid,
            'LineOfTherapy': line,
            'Drug': drug,
            'StartDay': start_day,
            'EndDay': end_day
        })
        start_day = end_day + np.random.randint(0, 30) # Gap between lines

df_long = pd.DataFrame(records)

# Save to Excel
folder = "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer/MockTrial_01"
base_path = os.path.join(folder, "mock_baseline.xlsx")
long_path = os.path.join(folder, "mock_longitudinal.xlsx")

df_base.to_excel(base_path, index=False)
df_long.to_excel(long_path, index=False)

print(f"Generated mock data at {folder}")
