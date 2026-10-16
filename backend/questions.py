import re


def parse_question(question):
    """Convert a supported ranking question into ranking settings."""
    text = " ".join(question.lower().split())

    if not text:
        raise ValueError("Enter a question.")

    if re.search(
        r"\b(lowest|least|bottom|worst|safest|less|lower)\b",
        text,
    ):
        raise ValueError(
            "Currently supported: highest return or highest volatility."
        )

    if re.search(r"\b(value|valuable|undervalued|overvalued)\b", text):
        raise ValueError(
            "Value is ambiguous. Ask about total return or volatility."
        )

    if re.search(r"\b\d{4}-\d{2}-\d{2}\b", text):
        raise ValueError("Choose dates using the dashboard date controls.")

    volatility = bool(
        re.search(r"\b(volatility|volatile|riskiest)\b", text)
    )
    total_return = bool(
        re.search(r"\b(returns?|gains?|gainers|performance)\b", text)
    )

    if volatility == total_return:
        raise ValueError(
            "Ask for one metric: highest return or highest volatility."
        )

    stocks = bool(re.search(r"\bstocks?\b", text))
    etfs = bool(re.search(r"\betfs?\b", text))

    if stocks and etfs:
        raise ValueError("Choose stocks or ETFs for each question.")

    count_matches = re.findall(
        r"\b(?:top|show|list)\s+(\d+)\b",
        text,
    )

    if len(set(count_matches)) > 1:
        raise ValueError("Use one result count, such as 'top 5'.")

    top_n = int(count_matches[0]) if count_matches else 5

    if not 1 <= top_n <= 100:
        raise ValueError("Choose between 1 and 100 results.")

    return {
        "metric": "volatility" if volatility else "total_return",
        "top_n": top_n,
        "asset_type": "etf" if etfs else "stock",
    }


if __name__ == "__main__":
    examples = [
        "Show the top 5 stocks by volatility",
        "Which ETFs had the highest return?",
        "List 3 stocks with the highest gains",
    ]

    for question in examples:
        print(f"\nQuestion: {question}")
        print(parse_question(question))