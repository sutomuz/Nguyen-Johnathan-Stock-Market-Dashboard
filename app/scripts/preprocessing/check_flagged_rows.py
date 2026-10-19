from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
audit = pd.read_csv(ROOT / "docs" / "data_audit.csv")

checks = [
    "missing_cells",
    "nonpositive_price_rows",
    "invalid_ohlc_rows",
    "zero_volume_rows",
]

for check in checks:
    print(f"\n{'=' * 20} {check.upper()}")

    # Inspect two affected files per issue.
    flagged = audit.loc[audit[check] > 0].head(2)

    for _, record in flagged.iterrows():
        path = (
            ROOT
            / "data"
            / "raw"
            / record["category"]
            / record["filename"]
        )
        df = pd.read_csv(path)

        prices = df[["Open", "High", "Low", "Close", "Adj Close"]]

        if check == "missing_cells":
            mask = df.isna().any(axis=1)

        elif check == "nonpositive_price_rows":
            mask = (prices <= 0).any(axis=1)

        elif check == "invalid_ohlc_rows":
            mask = (
                (df["High"] < df["Low"])
                | (df["High"] < df["Open"])
                | (df["High"] < df["Close"])
                | (df["Low"] > df["Open"])
                | (df["Low"] > df["Close"])
            )

        else:
            mask = df["Volume"] == 0

        print(f"\n{record['category']}/{record['filename']}")
        print(df.loc[mask].head(5).to_string(index=False))