import pandas as pd
import os

files = [
    'all_pakistan_doctors.csv',
    'pakistan_doctors_comprehensive.csv'
]

for file in files:
    if os.path.exists(file):
        print(f"\n--- {file} ---")
        try:
            df = pd.read_csv(file)
            print("Columns:", list(df.columns))
            print("First 3 rows:")
            print(df.head(3))
            print("Total rows:", len(df))
        except Exception as e:
            print(f"Error reading {file}: {e}")
    else:
        print(f"{file} not found.")
