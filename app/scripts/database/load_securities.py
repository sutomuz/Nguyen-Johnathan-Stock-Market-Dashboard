import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")

columns = [
    "symbol",
    "security_name",
    "listing_exchange",
    "market_category",
    "etf",
    "test_issue",
    "financial_status",
    "asset_type",
    "has_price_file",
]

with (ROOT / "data/processed/securities.csv").open(
    encoding="utf-8", newline=""
) as file:
    records = list(csv.DictReader(file))

rows = []
for record in records:
    values = [record[column] or None for column in columns]
    flag = record["has_price_file"].lower()
    if flag not in ("true", "false"):
        raise ValueError(f"Invalid has_price_file: {flag}")
    values[-1] = flag == "true"
    rows.append(values)

with psycopg.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    connect_timeout=10,
) as connection:
    with connection.cursor() as cursor:
        cursor.executemany("""
            INSERT INTO securities (
                symbol, security_name, listing_exchange,
                market_category, etf, test_issue,
                financial_status, asset_type, has_price_file
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE SET
                security_name = EXCLUDED.security_name,
                listing_exchange = EXCLUDED.listing_exchange,
                market_category = EXCLUDED.market_category,
                etf = EXCLUDED.etf,
                test_issue = EXCLUDED.test_issue,
                financial_status = EXCLUDED.financial_status,
                asset_type = EXCLUDED.asset_type,
                has_price_file = EXCLUDED.has_price_file;
        """, rows)

        cursor.execute("SELECT COUNT(*) FROM securities;")
        total = cursor.fetchone()[0]

print(f"Imported {len(rows):,} metadata records.")
print(f"Securities in database: {total:,}")