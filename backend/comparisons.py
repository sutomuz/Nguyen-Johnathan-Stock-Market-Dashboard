import numpy as np
import pandas as pd

from backend.analytics import calculate_returns
from backend.prices import get_prices


def compare_volatility(symbols, start_date, end_date):
    """Rank securities using return intervals shared by every selection."""
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

        prices = calculate_returns(prices)

        # Match both ends of each return interval.
        prices["previous_date"] = prices["trade_date"].shift(1)

        returns = prices.dropna(subset=["daily_return"]).set_index(
            ["previous_date", "trade_date"]
        )["daily_return"]

        series.append(returns.rename(symbol))

    shared = pd.concat(series, axis=1).dropna()

    if len(shared) < 2:
        raise ValueError(
            "Need at least two valid return intervals shared by all symbols."
        )

    daily_volatility = shared.std(ddof=1)

    result = pd.DataFrame({
        "symbol": daily_volatility.index,
        "shared_returns": len(shared),
        "daily_volatility": daily_volatility.to_numpy(),
        "annualized_volatility": (
            daily_volatility.to_numpy() * np.sqrt(252)
        ),
    })

    return result.sort_values(
        ["daily_volatility", "symbol"],
        ascending=[False, True],
    ).reset_index(drop=True)


if __name__ == "__main__":
    comparison = compare_volatility(
        ["AAPL", "MSFT", "TSLA"],
        "2020-03-01",
        "2020-04-01",
    )

    display = comparison.copy()

    for column in ["daily_volatility", "annualized_volatility"]:
        display[column] = display[column].map(
            lambda value: f"{value:.2%}"
        )

    print(display.to_string(index=False))
    print("\nRanked from highest to lowest volatility.")