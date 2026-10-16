import unittest
from unittest.mock import patch

import pandas as pd

from backend.answers import answer_question
from backend.questions import parse_question


class QuestionTests(unittest.TestCase):
    def test_volatility_question(self):
        result = parse_question("Show the top 3 stocks by volatility")

        self.assertEqual(result, {
            "metric": "volatility",
            "top_n": 3,
            "asset_type": "stock",
        })

    def test_etf_return_question(self):
        result = parse_question("Which ETFs had the highest return?")

        self.assertEqual(result, {
            "metric": "total_return",
            "top_n": 5,
            "asset_type": "etf",
        })

    def test_case_and_spaces(self):
        result = parse_question("  LIST   10 STOCKS WITH HIGHEST GAINS ")

        self.assertEqual(result["metric"], "total_return")
        self.assertEqual(result["top_n"], 10)

    def test_unsupported_questions(self):
        questions = [
            "",
            "What should I buy?",
            "Show the lowest volatility stocks",
            "Which stock has the most value?",
            "Show return and volatility",
            "Show top 0 stocks by return",
            "Show top 101 stocks by return",
            "Show top 3 and top 5 stocks by return",
            "Show stocks and ETFs by return",
            "Show returns from 2020-03-01",
        ]

        for question in questions:
            with self.subTest(question=question):
                with self.assertRaises(ValueError):
                    parse_question(question)

    @patch("backend.answers.rank_returns")
    @patch("backend.answers.rank_volatility")
    def test_volatility_routing(self, mock_volatility, mock_returns):
        mock_volatility.return_value = pd.DataFrame({"symbol": ["AAA"]})

        answer = answer_question(
            "Show top 3 stocks by volatility",
            "2020-03-01",
            "2020-04-01",
            exclude_flagged=False,
            threshold=0.75,
            min_returns=10,
        )

        mock_volatility.assert_called_once_with(
            start_date="2020-03-01",
            end_date="2020-04-01",
            top_n=3,
            asset_type="stock",
            exclude_flagged=False,
            threshold=0.75,
            min_returns=10,
        )

        mock_returns.assert_not_called()
        self.assertEqual(answer["results"].iloc[0]["symbol"], "AAA")

    @patch("backend.answers.rank_volatility")
    @patch("backend.answers.rank_returns")
    def test_return_routing(self, mock_returns, mock_volatility):
        mock_returns.return_value = pd.DataFrame()

        answer = answer_question(
            "Show top 5 ETFs by return",
            "2020-03-01",
            "2020-04-01",
        )

        mock_returns.assert_called_once_with(
            start_date="2020-03-01",
            end_date="2020-04-01",
            top_n=5,
            asset_type="etf",
            exclude_flagged=True,
            threshold=0.50,
        )

        mock_volatility.assert_not_called()
        self.assertTrue(answer["results"].empty)

    @patch("backend.answers.rank_returns")
    @patch("backend.answers.rank_volatility")
    def test_invalid_question_does_not_query_database(
        self, mock_volatility, mock_returns
    ):
        with self.assertRaises(ValueError):
            answer_question(
                "Which stock is undervalued?",
                "2020-03-01",
                "2020-04-01",
            )

        mock_volatility.assert_not_called()
        mock_returns.assert_not_called()


if __name__ == "__main__":
    unittest.main()