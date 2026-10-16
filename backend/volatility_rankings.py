from datetime import date
import math
from time import perf_counter

import pandas as pd

from backend.database import get_connection


def rank_volatility(
    start_date,
    end_date,
    top_n=5,
    asset_type="stock",
    exclude_flagged=True,
    threshold=0.50,
    min_returns=20,
):
    """Rank volatility across available valid daily returns."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start >= end:
        raise ValueError("Start date must be before end date.")

    if type(top_n) is not int or not 1 <= top_n <= 100:
        raise ValueError("Choose between 1 and 100 results.")

    if asset_type not in ("stock", "etf"):
        raise ValueError("Asset type must be 'stock' or 'etf'.")

    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("Threshold must be positive and finite.")

    if type(min_returns) is not int or min_returns < 2:
        raise ValueError("Minimum returns must be an integer of at least 2.")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '60s';")

            cursor.execute(
                """
                WITH observations AS (
                    SELECT
                        p.symbol,
                        p.trade_date,
                        p.source_row,
                        CASE
                            WHEN p.valid_adj_close
                             AND p.adj_close > 0
                             AND p.adj_close < 'Infinity'::float8
                            THEN p.adj_close
                        END AS price
                    FROM daily_prices AS p
                    JOIN securities AS s USING (symbol)
                    WHERE p.trade_date BETWEEN %s AND %s
                      AND s.asset_type = %s
                ),
                history AS (
                    SELECT
                        *,
                        LAG(price) OVER security_history AS previous_price,
                        LAG(source_row) OVER security_history AS previous_row
                    FROM observations
                    WINDOW security_history AS (
                        PARTITION BY symbol ORDER BY trade_date
                    )
                ),
                returns AS (
                    SELECT
                        symbol,
                        trade_date,
                        CASE
                            WHEN source_row = previous_row + 1
                             AND price IS NOT NULL
                             AND previous_price IS NOT NULL
                            THEN price::numeric
                                 / NULLIF(previous_price::numeric, 0) - 1
                        END AS daily_return
                    FROM history
                ),
                summary AS (
                    SELECT
                        symbol,
                        MIN(trade_date) FILTER (
                            WHERE daily_return IS NOT NULL
                        ) AS first_return_date,
                        MAX(trade_date) FILTER (
                            WHERE daily_return IS NOT NULL
                        ) AS last_return_date,
                        COUNT(daily_return) AS return_count,
                        STDDEV_SAMP(daily_return)::double precision
                            AS daily_volatility,
                        COUNT(*) FILTER (
                            WHERE ABS(daily_return) > %s
                        ) AS extreme_move_count
                    FROM returns
                    GROUP BY symbol
                    HAVING COUNT(daily_return) >= %s
                )
                SELECT
                    summary.symbol,
                    s.security_name,
                    summary.first_return_date,
                    summary.last_return_date,
                    summary.return_count,
                    summary.daily_volatility,
                    summary.daily_volatility * SQRT(252.0)
                        AS annualized_volatility,
                    summary.extreme_move_count,
                    summary.extreme_move_count > 0 AS needs_review
                FROM summary
                JOIN securities AS s USING (symbol)
                WHERE NOT %s OR summary.extreme_move_count = 0
                ORDER BY summary.daily_volatility DESC, summary.symbol
                LIMIT %s;
                """,
                (
                    start,
                    end,
                    asset_type,
                    threshold,
                    min_returns,
                    exclude_flagged,
                    top_n,
                ),
            )

            columns = [column.name for column in cursor.description]
            rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


if __name__ == "__main__":
    started = perf_counter()

    ranking = rank_volatility(
        "2020-03-01",
        "2020-04-01",
        top_n=5,
        min_returns=20,
        exclude_flagged=True,
    )

    if ranking.empty:
        print("No securities meet the selected requirements.")
    else:
        display = ranking.drop(columns=["security_name"]).copy()

        for column in ["daily_volatility", "annualized_volatility"]:
            display[column] = display[column].map(
                lambda value: f"{value:.2%}"
            )

        print(display.to_string(index=False))

    print(f"\nQuery finished in {perf_counter() - started:.2f} seconds.")
    print("Minimum valid returns: 20.")
    print("Securities with daily moves above 50% are excluded.")
    print("Each security uses its available valid return intervals.")