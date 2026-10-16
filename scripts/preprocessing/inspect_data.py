from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

metadata = pd.read_csv(RAW / "symbols_valid_meta.csv")

print("METADATA")
print("Shape:", metadata.shape)
print("Columns:", metadata.columns.tolist())
print(metadata.head().to_string(index=False))

for folder in ["stocks", "etfs"]:
    files = sorted((RAW / folder).glob("*.csv"))
    print(f"\n{folder.upper()}: {len(files)} CSV files")

    if files:
        sample = pd.read_csv(files[0])
        print("Sample file:", files[0].name)
        print("Shape:", sample.shape)
        print("Columns:", sample.columns.tolist())
        print(sample.head().to_string(index=False))
        print("Missing values:")
        print(sample.isna().sum())