from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "processed" / "securities.csv"

df = pd.read_csv(
    RAW / "symbols_valid_meta.csv",
    dtype="string",
    keep_default_na=False,
)

df = df.rename(
    columns={
        "Symbol": "symbol",
        "Security Name": "security_name",
        "Listing Exchange": "listing_exchange",
        "Market Category": "market_category",
        "ETF": "etf",
        "Test Issue": "test_issue",
        "Financial Status": "financial_status",
    }
)

columns = [
    "symbol",
    "security_name",
    "listing_exchange",
    "market_category",
    "etf",
    "test_issue",
    "financial_status",
]

df = df[columns].copy()

for column in columns:
    df[column] = df[column].str.strip().replace("", pd.NA)

original_rows = len(df)

df = df.loc[
    df["symbol"].notna()
    & ~df["test_issue"].eq("Y").fillna(False)
].copy()

if df["symbol"].duplicated().any():
    duplicates = df.loc[
        df["symbol"].duplicated(keep=False), "symbol"
    ]
    raise ValueError(
        f"Duplicate symbols require review: {duplicates.tolist()}"
    )

df["asset_type"] = df["etf"].map({"Y": "etf", "N": "stock"})

price_file_aliases = {
    "AGM$A": "AGM-A",
    "CARR.V": "CARR#",
    "UTX.V": "UTX#",
}

df["price_file_symbol"] = df["symbol"].replace(price_file_aliases)

if df.duplicated(["price_file_symbol", "asset_type"]).any():
    raise ValueError("Multiple securities map to the same price file.")

stock_symbols = {
    path.stem for path in (RAW / "stocks").glob("*.csv")
}
etf_symbols = {
    path.stem for path in (RAW / "etfs").glob("*.csv")
}

df["has_price_file"] = (
    (
        df["asset_type"].eq("stock")
        & df["price_file_symbol"].isin(stock_symbols)
    )
    | (
        df["asset_type"].eq("etf")
        & df["price_file_symbol"].isin(etf_symbols)
    )
)

df = df.sort_values("symbol").reset_index(drop=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print("Original metadata rows:", original_rows)
print("Cleaned metadata rows:", len(df))
print("Matched price files:", int(df["has_price_file"].sum()))
print(
    "Without matching price files:",
    int((~df["has_price_file"]).sum()),
)
print("Unknown asset types:", int(df["asset_type"].isna().sum()))
print(f"Saved to: {OUTPUT}")

unmatched = df.loc[
    ~df["has_price_file"],
    ["symbol", "security_name", "asset_type", "price_file_symbol"],
]

if not unmatched.empty:
    print("\nFirst unmatched securities:")
    print(unmatched.head(10).to_string(index=False))