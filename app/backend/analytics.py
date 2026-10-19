import numpy as np
import pandas as pd

from backend.prices import get_prices


def calculate_returns(prices):
    """Calculate returns without filling missing prices or removed rows."""
    result = prices.sort_values("trade_date").reset_index(drop=True).copy()

    adjusted = pd.to_numeric(result["adj_close"], errors="coerce")
    usable = (
        result["valid_adj_close"].fillna(False)
        & adjusted.gt(0)
        & np.isfinite(adjusted)
    )

    adjusted = adjusted.where(usable)
    previous = adjusted.shift(1)

    # Do not calculate across rows removed during cleaning.
    consecutive = result["source_row"].diff().eq(1)

    daily_return = adjusted.div(previous).sub(1)
    result["daily_return"] = daily_return.where(
        consecutive & np.isfinite(daily_return)
    )

    return result


def summarize_volatility(prices):
    """Return sample daily volatility and its annualized estimate."""
    returns = prices["daily_return"].dropna()
    count = len(returns)

    if count < 2:
        return {
            "return_count": count,
            "daily_volatility": None,
            "annualized_volatility": None,
        }

    daily = float(returns.std(ddof=1))

    return {
        "return_count": count,
        "daily_volatility": daily,
        "annualized_volatility": daily * np.sqrt(252),
    }


if __name__ == "__main__":
    prices = get_prices("AAPL", "2020-03-01", "2020-04-01")

    if prices.empty:
        raise ValueError("No price records found.")

    prices = calculate_returns(prices)
    summary = summarize_volatility(prices)

    display = prices[
        ["trade_date", "adj_close", "daily_return"]
    ].copy()

    display["daily_return_pct"] = display.pop("daily_return") * 100

    print(display.head(10).to_string(index=False))
    print("\nValid daily returns:", summary["return_count"])

    if summary["daily_volatility"] is not None:
        print(
            f"Daily volatility: "
            f"{summary['daily_volatility']:.2%}"
        )
        print(
            f"Annualized volatility estimate: "
            f"{summary['annualized_volatility']:.2%}"
        )