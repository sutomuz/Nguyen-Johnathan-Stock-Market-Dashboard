import numpy as np

from backend.analytics import calculate_returns
from backend.prices import get_prices


def flag_extreme_returns(prices, threshold=0.50):
    """
    Flag absolute daily returns above a review threshold.

    A flag means review is needed, not that the price is incorrect.
    Prices and calculated returns are preserved.
    """
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("Threshold must be a positive, finite number.")

    result = calculate_returns(prices)

    result["flag_extreme_return"] = (
        result["daily_return"].abs().gt(threshold)
    )

    return result


if __name__ == "__main__":
    prices = get_prices("TAPR", "2020-03-01", "2020-04-01")
    reviewed = flag_extreme_returns(prices)

    flagged = reviewed.loc[
        reviewed["flag_extreme_return"],
        ["symbol", "trade_date", "adj_close", "daily_return"],
    ].copy()

    flagged["daily_return_pct"] = flagged.pop("daily_return") * 100

    if flagged.empty:
        print("No daily moves exceeded the review threshold.")
    else:
        print(flagged.to_string(index=False))

    print("\nReview threshold: absolute daily return above 50%.")
    print("Flagged moves require investigation; prices were preserved.")