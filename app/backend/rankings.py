from datetime import date
import math
from time import perf_counter

import pandas as pd

from backend.database import get_connection


def rank_returns(
    start_date,
    end_date,
    top_n=5,
    asset_type="stock",
    exclude_flagged=True,
    threshold=0.50,
):
    """Rank endpoint returns with optional extreme-move screening."""
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
                        MIN(trade_date) OVER () AS range_start,
                        MAX(trade_date) OVER () AS range_end,
                        LAG(price) OVER security_history AS previous_price,
                        LAG(source_row) OVER security_history AS previous_row
                    FROM observations
                    WINDOW security_history AS (
                        PARTITION BY symbol ORDER BY trade_date
                    )
                ),
                summary AS (
                    SELECT
                        symbol,
                        MIN(range_start) AS start_date,
                        MAX(range_end) AS end_date,
                        MAX(price) FILTER (
                            WHERE trade_date = range_start
                        ) AS start_adj_close,
                        MAX(price) FILTER (
                            WHERE trade_date = range_end
                        ) AS end_adj_close,
                        COUNT(*) FILTER (
                            WHERE source_row = previous_row + 1
                              AND price IS NOT NULL
                              AND previous_price IS NOT NULL
                              AND ABS(
                                  price::numeric
                                  / NULLIF(previous_price::numeric, 0) - 1
                              ) > %s
                        ) AS extreme_move_count
                    FROM history
                    GROUP BY symbol
                ),
                eligible AS (
                    SELECT
                        *,
                        (
                            end_adj_close::numeric
                            / NULLIF(start_adj_close::numeric, 0) - 1
                        )::double precision AS total_return,
                        extreme_move_count > 0 AS needs_review
                    FROM summary
                    WHERE start_date < end_date
                      AND start_adj_close IS NOT NULL
                      AND end_adj_close IS NOT NULL
                )
                SELECT
                    e.symbol,
                    s.security_name,
                    e.start_date,
                    e.end_date,
                    e.start_adj_close,
                    e.end_adj_close,
                    e.total_return,
                    e.extreme_move_count,
                    e.needs_review
                FROM eligible AS e
                JOIN securities AS s USING (symbol)
                WHERE NOT %s OR NOT e.needs_review
                ORDER BY e.total_return DESC, e.symbol
                LIMIT %s;
                """,
                (
                    start,
                    end,
                    asset_type,
                    threshold,
                    exclude_flagged,
                    top_n,
                ),
            )

            description = cursor.description

            if description is None:
                raise RuntimeError(
                    "The returns query did not return column descriptions."
                )

            columns = [column.name for column in description]
            rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


if __name__ == "__main__":
    for exclude in [False, True]:
        print(
            f"\nExclude flagged securities: {exclude}",
            flush=True,
        )

        started = perf_counter()

        ranking = rank_returns(
            "2020-03-01",
            "2020-04-01",
            top_n=5,
            asset_type="stock",
            exclude_flagged=exclude,
        )

        if ranking.empty:
            print("No eligible securities found.")
        else:
            display = pd.DataFrame(
                ranking[
                    [
                        "symbol",
                        "start_date",
                        "end_date",
                        "total_return",
                        "extreme_move_count",
                        "needs_review",
                    ]
                ]
            ).copy()

            returns = pd.Series(display["total_return"])
            display["total_return"] = returns.map(
                lambda value: f"{value:.2%}"
            )

            print(display.to_string(index=False))

        print(f"Query finished in {perf_counter() - started:.2f} seconds.")

    print("\nReview threshold: absolute daily move above 50%.")
    print("Screening covers consecutive source rows within the date range.")
    print("Unflagged securities may still contain data errors.")