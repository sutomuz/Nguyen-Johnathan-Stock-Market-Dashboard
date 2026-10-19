from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORT = ROOT / "docs" / "reports" / "cleaning_report.csv"

PRICES = ["Open", "High", "Low", "Close", "Adj Close"]
NUMERIC = PRICES + ["Volume"]
REQUIRED = ["Date"] + NUMERIC


def clean_file(path, category):
    df = pd.read_csv(path)

    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    original_rows = len(df)

    # Preserve original positions for tracing data and detecting gaps.
    df["source_row"] = np.arange(len(df))

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    for column in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df[NUMERIC] = df[NUMERIC].replace([np.inf, -np.inf], np.nan)

    # Flag issues before replacing invalid values.
    df["flag_missing_numeric"] = df[NUMERIC].isna().any(axis=1)
    df["flag_nonpositive_price"] = (df[PRICES] <= 0).any(axis=1)
    df["flag_invalid_adj_close"] = (
        df["Adj Close"].isna() | (df["Adj Close"] <= 0)
    )
    df["flag_zero_volume"] = df["Volume"].eq(0)
    df["flag_negative_volume"] = df["Volume"].lt(0)

    empty = df[NUMERIC].isna().all(axis=1)
    invalid_date = df["Date"].isna()

    # Do not silently choose between duplicate observations.
    if df.loc[~invalid_date, "Date"].duplicated().any():
        raise ValueError("Duplicate dates require review")

    # Replace invalid individual values; never fill missing prices.
    for column in PRICES:
        df.loc[df[column] <= 0, column] = np.nan

    df.loc[df["Volume"] < 0, "Volume"] = np.nan

    # Compare available OHLC values with a small rounding tolerance.
    tolerance = 0.000001

    df["flag_ohlc_inconsistent"] = (
        (df["High"] + tolerance < df["Low"])
        | (df["High"] + tolerance < df["Open"])
        | (df["High"] + tolerance < df["Close"])
        | (df["Low"] - tolerance > df["Open"])
        | (df["Low"] - tolerance > df["Close"])
    )

    df["valid_ohlc"] = (
        df[["Open", "High", "Low", "Close"]].notna().all(axis=1)
        & ~df["flag_ohlc_inconsistent"]
    )

    # Present and positive does not mean independently verified.
    df["valid_adj_close"] = df["Adj Close"].notna()

    report = {
        "category": category,
        "symbol": path.stem,
        "original_rows": original_rows,
        "empty_rows_removed": int(empty.sum()),
        "invalid_date_rows_removed": int(
            (invalid_date & ~empty).sum()
        ),
        "nonpositive_price_rows": int(
            df["flag_nonpositive_price"].sum()
        ),
        "invalid_adj_close_rows": int(
            df["flag_invalid_adj_close"].sum()
        ),
        "zero_volume_rows": int(df["flag_zero_volume"].sum()),
        "inconsistent_ohlc_rows": int(
            df["flag_ohlc_inconsistent"].sum()
        ),
    }

    df = df.loc[~empty & ~invalid_date].copy()
    df = df.sort_values("Date").reset_index(drop=True)

    df["symbol"] = path.stem
    df["asset_type"] = "stock" if category == "stocks" else "etf"

    report["usable_adj_close_rows"] = int(
        df["valid_adj_close"].sum()
    )
    report["cleaned_rows"] = len(df)
    report["error"] = ""

    output_folder = PROCESSED / category
    output_folder.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        output_folder / path.name,
        index=False,
        date_format="%Y-%m-%d",
    )

    return report


def main():
    reports = []

    for category in ["stocks", "etfs"]:
        files = sorted((RAW / category).glob("*.csv"))

        if not files:
            raise FileNotFoundError(
                f"No CSV files in {RAW / category}"
            )

        for number, path in enumerate(files, start=1):
            try:
                reports.append(clean_file(path, category))

            except Exception as error:
                reports.append({
                    "category": category,
                    "symbol": path.stem,
                    "error": str(error),
                })
                print(
                    f"ERROR: {category}/{path.name}: {error}",
                    flush=True,
                )

            if number % 250 == 0 or number == len(files):
                print(
                    f"{category}: processed {number}/{len(files)} files",
                    flush=True,
                )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(reports)
    summary.to_csv(REPORT, index=False)

    errors = summary["error"].fillna("").ne("").sum()

    print(f"\nFinished. Successful files: {len(summary) - errors}")
    print(f"Files with errors: {errors}")
    print(f"Cleaning report: {REPORT}")


if __name__ == "__main__":
    main()