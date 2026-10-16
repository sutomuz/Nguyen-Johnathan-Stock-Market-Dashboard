import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from backend.analytics import calculate_returns, summarize_volatility
from backend.comparisons import compare_volatility
from backend.performance import compare_returns


def sample_prices(values, dates=None, source_rows=None, valid=None):
    count = len(values)

    return pd.DataFrame({
        "trade_date": pd.to_datetime(
            dates if dates is not None
            else pd.date_range("2020-01-06", periods=count, freq="B")
        ).date,
        "adj_close": values,
        "source_row": (
            source_rows if source_rows is not None else range(count)
        ),
        "valid_adj_close": (
            valid if valid is not None else [True] * count
        ),
    })


class AnalyticsTests(unittest.TestCase):
    def test_known_returns(self):
        result = calculate_returns(sample_prices([100, 110, 99]))

        self.assertTrue(pd.isna(result.loc[0, "daily_return"]))
        self.assertAlmostEqual(result.loc[1, "daily_return"], 0.10)
        self.assertAlmostEqual(result.loc[2, "daily_return"], -0.10)

    def test_missing_price_is_not_filled(self):
        result = calculate_returns(
            sample_prices([100, np.nan, 110, 121])
        )

        self.assertTrue(result["daily_return"].iloc[:3].isna().all())
        self.assertAlmostEqual(result.loc[3, "daily_return"], 0.10)

    def test_invalid_prices_are_excluded(self):
        for value in [0, -10, np.inf]:
            with self.subTest(value=value):
                result = calculate_returns(
                    sample_prices([100, value, 110])
                )
                self.assertTrue(result["daily_return"].isna().all())

        flagged = calculate_returns(
            sample_prices([100, 110, 121], valid=[True, False, True])
        )
        self.assertTrue(flagged["daily_return"].isna().all())

    def test_removed_row_is_not_bridged(self):
        result = calculate_returns(
            sample_prices(
                [100, 110, 121],
                source_rows=[0, 2, 3],
            )
        )

        self.assertTrue(pd.isna(result.loc[1, "daily_return"]))
        self.assertAlmostEqual(result.loc[2, "daily_return"], 0.10)

    def test_sample_volatility(self):
        result = calculate_returns(sample_prices([100, 110, 99]))
        summary = summarize_volatility(result)

        expected = np.std([0.10, -0.10], ddof=1)

        self.assertEqual(summary["return_count"], 2)
        self.assertAlmostEqual(summary["daily_volatility"], expected)
        self.assertAlmostEqual(
            summary["annualized_volatility"],
            expected * np.sqrt(252),
        )

    def test_insufficient_returns(self):
        result = calculate_returns(sample_prices([100, 110]))
        summary = summarize_volatility(result)

        self.assertIsNone(summary["daily_volatility"])

    @patch("backend.performance.get_prices")
    def test_total_returns_use_shared_endpoints(self, mock_get):
        samples = {
            "AAA": sample_prices(
                [100, 110, 121, 133.1],
                dates=[
                    "2020-01-06", "2020-01-07",
                    "2020-01-08", "2020-01-09",
                ],
            ),
            "BBB": sample_prices(
                [200, 220, 242, 266.2],
                dates=[
                    "2020-01-07", "2020-01-08",
                    "2020-01-09", "2020-01-10",
                ],
            ),
        }
        mock_get.side_effect = lambda symbol, *_: samples[symbol].copy()

        result = compare_returns(
            ["AAA", "BBB"], "2020-01-06", "2020-01-10"
        )

        for row in result.itertuples():
            self.assertEqual(str(row.start_date), "2020-01-07")
            self.assertEqual(str(row.end_date), "2020-01-09")
            self.assertAlmostEqual(row.total_return, 0.21)

    @patch("backend.comparisons.get_prices")
    def test_volatility_matches_both_interval_dates(self, mock_get):
        samples = {
            "AAA": sample_prices(
                [100, 110, 99, 108.9, 98.01],
                dates=[
                    "2020-01-06", "2020-01-07", "2020-01-08",
                    "2020-01-09", "2020-01-10",
                ],
            ),
            "BBB": sample_prices(
                [200, 220, 242, 217.8],
                dates=[
                    "2020-01-06", "2020-01-08",
                    "2020-01-09", "2020-01-10",
                ],
            ),
        }
        mock_get.side_effect = lambda symbol, *_: samples[symbol].copy()

        result = compare_volatility(
            ["AAA", "BBB"], "2020-01-06", "2020-01-10"
        )

        # Only Jan 8–9 and Jan 9–10 have matching interval endpoints.
        self.assertTrue(result["shared_returns"].eq(2).all())


if __name__ == "__main__":
    unittest.main()