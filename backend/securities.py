import pandas as pd

from backend.database import get_connection


def search_securities(query, limit=20):
    """Search symbols and names, prioritizing exact ticker matches."""
    query = query.strip()

    if not query:
        raise ValueError("Enter a ticker or company name.")

    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

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
                      STRPOS(LOWER(symbol), LOWER(%s)) > 0
                      OR STRPOS(LOWER(security_name), LOWER(%s)) > 0
                  )
                ORDER BY
                    CASE
                        WHEN UPPER(symbol) = UPPER(%s) THEN 0
                        WHEN STRPOS(LOWER(symbol), LOWER(%s)) = 1 THEN 1
                        ELSE 2
                    END,
                    symbol
                LIMIT %s;
                """,
                (query, query, query, query, limit),
            )

            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


if __name__ == "__main__":
    for query in ["AAPL", "Microsoft"]:
        print(f"\nSearch: {query}")
        results = search_securities(query)

        if results.empty:
            print("No matching securities found.")
        else:
            print(results.to_string(index=False))