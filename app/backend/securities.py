import pandas as pd

from backend.database import get_connection


def search_securities(query="", limit=20, asset_type=None, offset=0):
    """Search and filter securities with available price files."""
    query = query.strip()

    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    if type(offset) is not int or offset < 0:
        raise ValueError("Offset must be a nonnegative integer.")

    if asset_type not in (None, "stock", "etf"):
        raise ValueError("Asset type must be 'stock', 'etf', or None.")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    symbol,
                    security_name,
                    asset_type,
                    listing_exchange
                FROM securities
                WHERE has_price_file
                  AND (
                      %s = ''
                      OR STRPOS(LOWER(symbol), LOWER(%s)) > 0
                      OR STRPOS(LOWER(security_name), LOWER(%s)) > 0
                  )
                  AND (%s::text IS NULL OR asset_type = %s)
                ORDER BY
                    CASE
                        WHEN %s <> '' AND UPPER(symbol) = UPPER(%s) THEN 0
                        WHEN %s <> ''
                             AND STRPOS(LOWER(symbol), LOWER(%s)) = 1 THEN 1
                        ELSE 2
                    END,
                    symbol
                LIMIT %s OFFSET %s;
                """,
                (
                    query,
                    query,
                    query,
                    asset_type,
                    asset_type,
                    query,
                    query,
                    query,
                    query,
                    limit,
                    offset,
                ),
            )

            description = cursor.description

            if description is None:
                raise RuntimeError(
                    "The search query did not return column descriptions."
                )

            columns = [column.name for column in description]
            rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


def get_security_details(symbol):
    """Return metadata and the available historical price range."""
    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("Enter a security symbol.")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    s.symbol,
                    s.security_name,
                    s.asset_type,
                    s.listing_exchange,
                    s.has_price_file,
                    (
                        SELECT MIN(p.trade_date)
                        FROM daily_prices AS p
                        WHERE p.symbol = s.symbol
                    ) AS first_date,
                    (
                        SELECT MAX(p.trade_date)
                        FROM daily_prices AS p
                        WHERE p.symbol = s.symbol
                    ) AS last_date,
                    (
                        SELECT COUNT(*)
                        FROM daily_prices AS p
                        WHERE p.symbol = s.symbol
                    ) AS price_records
                FROM securities AS s
                WHERE s.symbol = %s;
                """,
                (symbol,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            description = cursor.description

            if description is None:
                raise RuntimeError(
                    "The details query did not return column descriptions."
                )

            columns = [column.name for column in description]
            return dict(zip(columns, row))


if __name__ == "__main__":
    for query in ["AAPL", "Microsoft"]:
        print(f"\nSearch: {query}")
        results = search_securities(query)

        if results.empty:
            print("No matching securities found.")
        else:
            print(results.to_string(index=False))

    print("\nSecurity details: AAPL")
    details = get_security_details("AAPL")

    if details is None:
        print("Security not found.")
    else:
        for key, value in details.items():
            print(f"{key}: {value}")