import numpy as np
import pandas as pd

from backend.prices import get_prices


def compare_returns(symbols, start_date, end_date):
    """Compare adjusted-price returns between shared endpoint dates."""
    symbols = list(dict.fromkeys(
        symbol.strip().upper() for symbol in symbols
    ))

    if len(symbols) < 2 or any(not symbol for symbol in symbols):
        raise ValueError("Enter at least two different, nonempty symbols.")

    series = []

    for symbol in symbols:
        prices = get_prices(symbol, start_date, end_date)

        if prices.empty:
            raise ValueError(
                f"No prices found for {symbol} in this date range."
            )

        adjusted = pd.to_numeric(
            prices["adj_close"], errors="coerce"
        )

        usable = (
            prices["valid_adj_close"].fillna(False)
            & adjusted.gt(0)
            & np.isfinite(adjusted)
        )

        prices = prices.assign(
            usable_adj_close=adjusted.where(usable)
        )

        series.append(
            prices.set_index("trade_date")["usable_adj_close"]
            .rename(symbol)
        )

    shared = pd.concat(series, axis=1).dropna().sort_index()

    if len(shared) < 2:
        raise ValueError(
            "Need at least two shared dates with valid adjusted prices."
        )

    first = shared.iloc[0]
    last = shared.iloc[-1]
    total_return = last.div(first).sub(1)

    if not np.isfinite(total_return).all():
        raise ValueError("Calculated returns contain nonfinite values.")

    result = pd.DataFrame({
        "symbol": shared.columns,
        "start_date": shared.index[0],
        "end_date": shared.index[-1],
        "start_adj_close": first.to_numpy(),
        "end_adj_close": last.to_numpy(),
        "total_return": total_return.to_numpy(),
    })

    return result.sort_values(
        ["total_return", "symbol"],
        ascending=[False, True],
    ).reset_index(drop=True)


if __name__ == "__main__":
    comparison = compare_returns(
        ["AAPL", "MSFT", "TSLA"],
        "2020-03-01",
        "2020-04-01",
    )

    display = comparison.copy()

    for column in ["start_adj_close", "end_adj_close"]:
        display[column] = display[column].map(
            lambda value: f"{value:.2f}"
        )

    display["total_return"] = display["total_return"].map(
        lambda value: f"{value:.2%}"
    )

    print(display.to_string(index=False))
    print("\nRanked from highest to lowest total return.")