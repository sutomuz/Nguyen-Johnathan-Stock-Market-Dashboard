import csv
import os
from io import StringIO
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
load_dotenv(ROOT / ".env")

COLUMNS = [
    "symbol",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "source_row",
    "flag_missing_numeric",
    "flag_nonpositive_price",
    "flag_invalid_adj_close",
    "flag_zero_volume",
    "flag_negative_volume",
    "valid_ohlc",
    "valid_adj_close",
]

RENAME = {
    "Date": "trade_date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
}

with (PROCESSED / "securities.csv").open(
    encoding="utf-8", newline=""
) as file:
    metadata = list(csv.DictReader(file))

mapping = {}
for record in metadata:
    key = (record["price_file_symbol"], record["asset_type"])
    if key in mapping:
        raise ValueError(f"Duplicate price file mapping: {key}")
    mapping[key] = record["symbol"]

files = []

for folder, asset_type in [("stocks", "stock"), ("etfs", "etf")]:
    directory = PROCESSED / folder

    if not directory.is_dir():
        raise FileNotFoundError(directory)

    for path in sorted(directory.glob("*.csv")):
        key = (path.stem, asset_type)
        if key not in mapping:
            raise ValueError(f"No metadata for {path.name}")
        files.append((path, mapping[key]))

if not files:
    raise ValueError("No processed price files found.")

total_rows = 0

with psycopg.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    connect_timeout=10,
    autocommit=True,
) as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT symbol FROM securities;")
        database_symbols = {row[0] for row in cursor.fetchall()}

    missing = {symbol for _, symbol in files} - database_symbols
    if missing:
        raise ValueError(f"Load securities first. Missing: {sorted(missing)}")

    print(f"Loading {len(files):,} price files...", flush=True)

    for number, (path, symbol) in enumerate(files, start=1):
        try:
            df = pd.read_csv(path).rename(columns=RENAME)

            # Use the metadata symbol, including the three aliases.
            df["symbol"] = symbol
            df["volume"] = df["volume"].astype("Int64")
            df["source_row"] = df["source_row"].astype("Int64")
            df = df[COLUMNS]

            if df.empty:
                raise ValueError("Processed file contains no rows.")

            if df["trade_date"].isna().any():
                raise ValueError("Missing trade dates.")

            if df["trade_date"].duplicated().any():
                raise ValueError("Duplicate trade dates.")

            buffer = StringIO()
            df.to_csv(buffer, index=False, header=False, na_rep="")
            buffer.seek(0)

            # Each file is one transaction: a failure restores its old rows.
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM daily_prices WHERE symbol = %s;",
                        (symbol,),
                    )

                    copy_sql = (
                        f"COPY daily_prices ({', '.join(COLUMNS)}) "
                        "FROM STDIN WITH (FORMAT CSV)"
                    )

                    with cursor.copy(copy_sql) as copy:
                        while chunk := buffer.read(1024 * 1024):
                            copy.write(chunk)

            total_rows += len(df)

            if number == 1 or number % 100 == 0 or number == len(files):
                print(
                    f"{number:,}/{len(files):,} files | "
                    f"{total_rows:,} rows loaded",
                    flush=True,
                )

        except Exception as error:
            raise RuntimeError(
                f"Import stopped at {path.name}: {error}"
            ) from error

    with connection.cursor() as cursor:
        cursor.execute("ANALYZE daily_prices;")
        cursor.execute("SELECT COUNT(*) FROM daily_prices;")
        database_rows = cursor.fetchone()[0]

print("\nImport complete!")
print(f"Rows loaded this run: {total_rows:,}")
print(f"Total database price rows: {database_rows:,}")