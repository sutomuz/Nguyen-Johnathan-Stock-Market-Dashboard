from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "processed" / "securities.csv"

# Read as text to preserve symbols and category codes.
df = pd.read_csv(
    RAW / "symbols_valid_meta.csv",
    dtype="string",
)

df = df.rename(columns={
    "Symbol": "symbol",
    "Security Name": "security_name",
    "Listing Exchange": "listing_exchange",
    "Market Category": "market_category",
    "ETF": "etf",
    "Test Issue": "test_issue",
    "Financial Status": "financial_status",
})

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

# Remove entries without a symbol and explicitly marked test securities.
df = df.loc[
    df["symbol"].notna()
    & ~df["test_issue"].eq("Y").fillna(False)
].copy()

# Stop rather than silently choose between duplicate symbols.
if df["symbol"].duplicated().any():
    duplicates = df.loc[df["symbol"].duplicated(False), "symbol"]
    raise ValueError(
        f"Duplicate symbols require review: {duplicates.tolist()}"
    )

df["asset_type"] = df["etf"].map({"Y": "etf", "N": "stock"})

# Match each symbol against the original price filenames.
stock_symbols = {p.stem for p in (RAW / "stocks").glob("*.csv")}
etf_symbols = {p.stem for p in (RAW / "etfs").glob("*.csv")}

df["has_price_file"] = (
    (df["asset_type"].eq("stock") & df["symbol"].isin(stock_symbols))
    | (df["asset_type"].eq("etf") & df["symbol"].isin(etf_symbols))
)

df = df.sort_values("symbol").reset_index(drop=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print("Original metadata rows:", original_rows)
print("Cleaned metadata rows:", len(df))
print("Matched price files:", int(df["has_price_file"].sum()))
print("Without matching price files:", int((~df["has_price_file"]).sum()))
print("Unknown asset types:", int(df["asset_type"].isna().sum()))
print(f"Saved to: {OUTPUT}")

unmatched = df.loc[
    ~df["has_price_file"],
    ["symbol", "security_name", "asset_type"],
]

if not unmatched.empty:
    print("\nFirst unmatched securities:")
    print(unmatched.head(10).to_string(index=False))