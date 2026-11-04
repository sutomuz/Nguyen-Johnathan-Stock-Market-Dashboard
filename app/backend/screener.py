import math
from datetime import date

import pandas as pd

from backend.database import get_connection


def screen_securities(
    start_date,
    end_date,
    query="",
    asset_type=None,
    exchange=None,
    min_return=None,
    max_return=None,
    min_volatility=None,
    max_volatility=None,
    exclude_flagged=False,
    limit=21,
    offset=0,
):
    """
    Screen securities using historical returns, volatility, and quality flags.

    Return and volatility bounds are decimal values:
    0.10 means 10%, and 1.00 means 100%.
    """
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start >= end:
        raise ValueError("Start date must be before end date.")

    if asset_type not in (None, "stock", "etf"):
        raise ValueError("Asset type must be 'stock', 'etf', or None.")

    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    if type(offset) is not int or offset < 0:
        raise ValueError("Offset must be a nonnegative integer.")

    bounds = {
        "Minimum return": min_return,
        "Maximum return": max_return,
        "Minimum volatility": min_volatility,
        "Maximum volatility": max_volatility,
    }

    for label, value in bounds.items():
        if value is not None and not math.isfinite(value):
            raise ValueError(f"{label} must be finite.")

    if (
        min_return is not None
        and max_return is not None
        and min_return > max_return
    ):
        raise ValueError("Minimum return cannot exceed maximum return.")

    if min_volatility is not None and min_volatility < 0:
        raise ValueError("Minimum volatility cannot be negative.")

    if max_volatility is not None and max_volatility < 0:
        raise ValueError("Maximum volatility cannot be negative.")

    if (
        min_volatility is not None
        and max_volatility is not None
        and min_volatility > max_volatility
    ):
        raise ValueError(
            "Minimum volatility cannot exceed maximum volatility."
        )

    query = query.strip()

    params = {
        "start": start,
        "end": end,
        "query": query,
        "asset_type": asset_type,
        "exchange": exchange,
        "min_return": min_return,
        "max_return": max_return,
        "min_volatility": min_volatility,
        "max_volatility": max_volatility,
        "exclude_flagged": exclude_flagged,
        "limit": limit,
        "offset": offset,
    }

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '60s';")

            cursor.execute(
                """
                WITH universe AS (
                    SELECT
                        symbol,
                        security_name,
                        asset_type,
                        listing_exchange
                    FROM securities
                    WHERE has_price_file
                      AND (
                          %(asset_type)s::text IS NULL
                          OR asset_type = %(asset_type)s
                      )
                ),
                observations AS (
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
                    JOIN universe AS u ON u.symbol = p.symbol
                    WHERE p.trade_date BETWEEN %(start)s AND %(end)s
                ),
                range_dates AS (
                    SELECT
                        MIN(trade_date) AS range_start,
                        MAX(trade_date) AS range_end
                    FROM observations
                ),
                candidates AS (
                    SELECT *
                    FROM universe
                    WHERE (
                        %(query)s = ''
                        OR STRPOS(
                            LOWER(symbol),
                            LOWER(%(query)s)
                        ) > 0
                        OR STRPOS(
                            LOWER(security_name),
                            LOWER(%(query)s)
                        ) > 0
                    )
                    AND (
                        %(exchange)s::text IS NULL
                        OR listing_exchange = %(exchange)s
                    )
                ),
                history AS (
                    SELECT
                        o.symbol,
                        o.trade_date,
                        o.source_row,
                        o.price,
                        LAG(o.price) OVER security_history AS previous_price,
                        LAG(o.source_row) OVER security_history AS previous_row
                    FROM observations AS o
                    JOIN candidates AS c ON c.symbol = o.symbol
                    WINDOW security_history AS (
                        PARTITION BY o.symbol
                        ORDER BY o.trade_date
                    )
                ),
                returns AS (
                    SELECT
                        symbol,
                        trade_date,
                        price,
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
                        r.symbol,
                        MAX(r.price) FILTER (
                            WHERE r.trade_date = d.range_start
                        ) AS start_price,
                        MAX(r.price) FILTER (
                            WHERE r.trade_date = d.range_end
                        ) AS end_price,
                        COUNT(r.daily_return) AS return_count,
                        STDDEV_SAMP(r.daily_return)::double precision
                            * SQRT(252.0) AS annualized_volatility,
                        COUNT(*) FILTER (
                            WHERE ABS(r.daily_return) > 0.50
                        ) AS extreme_move_count
                    FROM returns AS r
                    CROSS JOIN range_dates AS d
                    GROUP BY r.symbol
                ),
                metrics AS (
                    SELECT
                        c.symbol,
                        c.security_name,
                        c.asset_type,
                        c.listing_exchange,
                        d.range_start,
                        d.range_end,
                        CASE
                            WHEN d.range_start < d.range_end
                             AND s.start_price IS NOT NULL
                             AND s.end_price IS NOT NULL
                            THEN (
                                s.end_price::numeric
                                / NULLIF(s.start_price::numeric, 0) - 1
                            )::double precision
                        END AS total_return,
                        CASE
                            WHEN s.return_count >= 20
                            THEN s.annualized_volatility
                        END AS annualized_volatility,
                        s.return_count,
                        s.extreme_move_count
                    FROM candidates AS c
                    CROSS JOIN range_dates AS d
                    LEFT JOIN summary AS s ON s.symbol = c.symbol
                )
                SELECT
                    symbol,
                    security_name,
                    asset_type,
                    listing_exchange,
                    range_start,
                    range_end,
                    total_return,
                    annualized_volatility,
                    return_count,
                    extreme_move_count,
                    extreme_move_count > 0 AS needs_review
                FROM metrics
                WHERE (
                    %(min_return)s::float8 IS NULL
                    OR total_return >= %(min_return)s
                )
                  AND (
                    %(max_return)s::float8 IS NULL
                    OR total_return <= %(max_return)s
                )
                  AND (
                    %(min_volatility)s::float8 IS NULL
                    OR annualized_volatility >= %(min_volatility)s
                )
                  AND (
                    %(max_volatility)s::float8 IS NULL
                    OR annualized_volatility <= %(max_volatility)s
                )
                  AND (
                    NOT %(exclude_flagged)s
                    OR (
                        return_count > 0
                        AND extreme_move_count = 0
                    )
                )
                ORDER BY
                    CASE
                        WHEN %(query)s <> ''
                             AND UPPER(symbol) = UPPER(%(query)s)
                        THEN 0
                        WHEN %(query)s <> ''
                             AND STRPOS(
                                 LOWER(symbol),
                                 LOWER(%(query)s)
                             ) = 1
                        THEN 1
                        ELSE 2
                    END,
                    symbol
                LIMIT %(limit)s OFFSET %(offset)s;
                """,
                params,
            )

            description = cursor.description

            if description is None:
                raise RuntimeError(
                    "The screener query did not return column descriptions."
                )

            columns = [column.name for column in description]
            rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


if __name__ == "__main__":
    results = screen_securities(
        "2020-03-01",
        "2020-04-01",
        asset_type="stock",
        query="AAPL",
    )

    if results.empty:
        print("No matching securities found.")
    else:
        print(results.to_string(index=False))