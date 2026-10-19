from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "docs" / "data_audit.csv"

EXPECTED = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
PRICES = ["Open", "High", "Low", "Close", "Adj Close"]

results = []

for category in ["stocks", "etfs"]:
    files = sorted((RAW / category).glob("*.csv"))

    for number, file in enumerate(files, start=1):
        report = {
            "category": category,
            "symbol": file.stem,
            "filename": file.name,
        }

        try:
            df = pd.read_csv(file)

            report["rows"] = len(df)
            report["columns_match"] = list(df.columns) == EXPECTED
            report["missing_cells"] = int(df.isna().sum().sum())

            missing_columns = set(EXPECTED) - set(df.columns)
            report["missing_columns"] = ", ".join(sorted(missing_columns))

            if missing_columns:
                report["error"] = "Required columns missing"
            else:
                dates = pd.to_datetime(df["Date"], errors="coerce")
                numbers = df[PRICES + ["Volume"]].apply(
                    pd.to_numeric, errors="coerce"
                )

                report["first_date"] = dates.min()
                report["last_date"] = dates.max()
                report["invalid_dates"] = int(dates.isna().sum())
                report["duplicate_dates"] = int(
                    dates.dropna().duplicated().sum()
                )
                report["dates_sorted"] = dates.is_monotonic_increasing

                report["invalid_numeric_cells"] = int(
                    (numbers.isna() & df[PRICES + ["Volume"]].notna())
                    .sum()
                    .sum()
                )
                report["infinite_numeric_cells"] = int(
                    numbers.isin([float("inf"), float("-inf")])
                    .sum()
                    .sum()
                )
                report["nonpositive_price_rows"] = int(
                    (numbers[PRICES] <= 0).any(axis=1).sum()
                )
                report["negative_volume_rows"] = int(
                    (numbers["Volume"] < 0).sum()
                )
                report["zero_volume_rows"] = int(
                    (numbers["Volume"] == 0).sum()
                )

                # Adjusted Close is not part of the OHLC range check.
                bad_range = (
                    (numbers["High"] < numbers["Low"])
                    | (numbers["High"] < numbers["Open"])
                    | (numbers["High"] < numbers["Close"])
                    | (numbers["Low"] > numbers["Open"])
                    | (numbers["Low"] > numbers["Close"])
                )

                report["invalid_ohlc_rows"] = int(bad_range.sum())
                report["error"] = ""

        except Exception as error:
            report["error"] = str(error)

        results.append(report)

        if number % 250 == 0 or number == len(files):
            print(
                f"{category}: checked {number}/{len(files)} files",
                flush=True,
            )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
audit = pd.DataFrame(results)
audit.to_csv(OUTPUT, index=False)

print(f"\nDone! Audited {len(audit)} files.")
print(f"Report saved to: {OUTPUT}")