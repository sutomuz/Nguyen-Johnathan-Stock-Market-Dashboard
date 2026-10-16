import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

with (PROCESSED / "securities.csv").open(
    encoding="utf-8", newline=""
) as file:
    securities = {
        (row["price_file_symbol"], row["asset_type"])
        for row in csv.DictReader(file)
    }

total = 0
unmatched = []

for folder, asset_type in [("stocks", "stock"), ("etfs", "etf")]:
    directory = PROCESSED / folder

    if not directory.is_dir():
        raise FileNotFoundError(f"Missing folder: {directory}")

    for path in sorted(directory.glob("*.csv")):
        total += 1

        if (path.stem, asset_type) not in securities:
            unmatched.append(f"{folder}/{path.name}")

print("Processed price files:", total)
print("Files without matching metadata:", len(unmatched))

for name in unmatched:
    print("-", name)