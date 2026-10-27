from datetime import date

import pandas as pd

from backend.database import get_connection


def get_prices(symbol, start_date, end_date):
    """Retrieve historical prices within an inclusive date range."""
    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("Enter a stock or ETF symbol.")

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start > end:
        raise ValueError("Start date must be on or before end date.")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    symbol,
                    trade_date,
                    open,
                    high,
                    low,
                    close,
                    adj_close,
                    volume,
                    source_row,
                    flag_missing_numeric,
                    flag_nonpositive_price,
                    flag_invalid_adj_close,
                    flag_zero_volume,
                    flag_negative_volume,
                    valid_ohlc,
                    valid_adj_close
                FROM daily_prices
                WHERE symbol = %s
                  AND trade_date BETWEEN %s AND %s
                ORDER BY trade_date;
                """,
                (symbol, start, end),
            )

            description = cursor.description

            if description is None:
                raise RuntimeError(
                    "The price query did not return column descriptions."
                )

            columns = [column.name for column in description]
            rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


if __name__ == "__main__":
    prices = get_prices("AAPL", "2020-03-01", "2020-04-01")

    if prices.empty:
        print("No prices found for this symbol and date range.")
    else:
        print(
            prices[
                ["symbol", "trade_date", "close", "volume"]
            ].head(10).to_string(index=False)
        )
        print(f"\nRecords returned: {len(prices)}")
        print("First date:", prices["trade_date"].min())
        print("Last date:", prices["trade_date"].max())