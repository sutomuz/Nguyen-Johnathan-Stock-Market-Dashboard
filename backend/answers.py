from backend.questions import parse_question
from backend.rankings import rank_returns
from backend.volatility_rankings import rank_volatility


def answer_question(
    question,
    start_date,
    end_date,
    exclude_flagged=True,
    threshold=0.50,
    min_returns=20,
):
    """Run a supported ranking question using selected dates and filters."""
    settings = parse_question(question)

    arguments = {
        "start_date": start_date,
        "end_date": end_date,
        "top_n": settings["top_n"],
        "asset_type": settings["asset_type"],
        "exclude_flagged": exclude_flagged,
        "threshold": threshold,
    }

    if settings["metric"] == "volatility":
        results = rank_volatility(
            **arguments,
            min_returns=min_returns,
        )
    else:
        results = rank_returns(**arguments)

    return {
        "settings": settings,
        "requested_start_date": start_date,
        "requested_end_date": end_date,
        "exclude_flagged": exclude_flagged,
        "threshold": threshold,
        "min_returns": (
            min_returns if settings["metric"] == "volatility" else None
        ),
        "results": results,
    }


if __name__ == "__main__":
    answer = answer_question(
        "Show the top 3 stocks by volatility",
        "2020-03-01",
        "2020-04-01",
    )

    print("Interpreted question:", answer["settings"])
    print(
        "Requested dates:",
        answer["requested_start_date"],
        "through",
        answer["requested_end_date"],
    )

    results = answer["results"]

    if results.empty:
        print("No securities meet the selected requirements.")
    else:
        display = results[
            [
                "symbol",
                "return_count",
                "daily_volatility",
                "annualized_volatility",
            ]
        ].copy()

        for column in ["daily_volatility", "annualized_volatility"]:
            display[column] = display[column].map(
                lambda value: f"{value:.2%}"
            )

        print(display.to_string(index=False))