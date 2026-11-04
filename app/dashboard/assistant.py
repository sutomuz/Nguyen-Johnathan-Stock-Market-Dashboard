import logging
from datetime import date

import pandas as pd
import streamlit as st

from backend.answers import answer_question


def format_results(results):
    """Format return and volatility columns for display."""
    display = results.copy()

    percent_columns = [
        "total_return",
        "daily_volatility",
        "annualized_volatility",
    ]

    for column in percent_columns:
        if column in display.columns:
            display[column] = display[column].map(
                lambda value: (
                    f"{value:.2%}" if pd.notna(value) else "N/A"
                )
            )

    return display


def show_assistant():
    """Display example questions and the market assistant."""
    st.subheader("Market assistant")
    st.caption("Ask questions about the historical data.")

    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = []

    with st.expander("Assistant settings"):
        assistant_start = st.date_input(
            "Assistant start date",
            value=date(2020, 3, 1),
            key="assistant_start_date",
        )

        assistant_end = st.date_input(
            "Assistant end date",
            value=date(2020, 4, 1),
            key="assistant_end_date",
        )

        exclude_flagged = st.checkbox(
            "Exclude flagged daily moves",
            value=True,
            key="assistant_exclude_flagged",
        )

        st.caption(
            "Flagged moves exceed 50% in a day and require review. "
            "They are not automatically errors."
        )

    # Click an example to run it using the current assistant settings.
    st.markdown("**Try an example**")

    example_question = None

    if st.button(
        "Top 3 stocks by volatility",
        key="example_volatility",
        use_container_width=True,
    ):
        example_question = "Show the top 3 stocks by volatility"

    if st.button(
        "ETFs with the highest return",
        key="example_etfs",
        use_container_width=True,
    ):
        example_question = "Which ETFs had the highest return?"

    if st.button(
        "Top 3 stocks by gains",
        key="example_gains",
        use_container_width=True,
    ):
        example_question = "List 3 stocks with the highest gains"

    # Display earlier questions and answers.
    for message in st.session_state.assistant_messages:
        with st.chat_message(message["role"]):
            st.write(message["text"])

            if "results" in message:
                st.dataframe(
                    message["results"],
                    hide_index=True,
                    use_container_width=True,
                )

    typed_question = st.chat_input(
        "Ask about stocks or ETFs",
        key="assistant_question",
    )

    question = example_question or typed_question

    if question:
        st.session_state.assistant_messages.append(
            {
                "role": "user",
                "text": question,
            }
        )

        if assistant_start >= assistant_end:
            st.session_state.assistant_messages.append(
                {
                    "role": "assistant",
                    "text": (
                        "The assistant start date must be before "
                        "the end date."
                    ),
                }
            )

        else:
            try:
                with st.spinner("Checking the historical data..."):
                    answer = answer_question(
                        question=question,
                        start_date=assistant_start.isoformat(),
                        end_date=assistant_end.isoformat(),
                        exclude_flagged=exclude_flagged,
                    )

                settings = answer["settings"]
                results = answer["results"]

                metric = (
                    "annualized volatility"
                    if settings["metric"] == "volatility"
                    else "total return"
                )

                asset = (
                    "stocks"
                    if settings["asset_type"] == "stock"
                    else "ETFs"
                )

                summary = (
                    f"Top {settings['top_n']} {asset} by {metric}, "
                    f"requested for {assistant_start} through "
                    f"{assistant_end}. "
                )

                if exclude_flagged:
                    summary += "Securities with flagged moves were excluded."
                else:
                    summary += "Securities with flagged moves were included."

                if settings["metric"] == "volatility":
                    summary += (
                        " Volatility uses available valid return intervals "
                        "and requires at least 20 returns."
                    )
                else:
                    summary += " Returns use shared available endpoint dates."

                if results.empty:
                    st.session_state.assistant_messages.append(
                        {
                            "role": "assistant",
                            "text": (
                                summary
                                + " No securities met the selected criteria."
                            ),
                        }
                    )
                else:
                    st.session_state.assistant_messages.append(
                        {
                            "role": "assistant",
                            "text": summary,
                            "results": format_results(results),
                        }
                    )

            except ValueError as error:
                st.session_state.assistant_messages.append(
                    {
                        "role": "assistant",
                        "text": str(error),
                    }
                )

            except Exception:
                logging.exception("Assistant question failed")

                st.session_state.assistant_messages.append(
                    {
                        "role": "assistant",
                        "text": (
                            "I couldn't complete that query. "
                            "Check the terminal for details."
                        ),
                    }
                )

        st.rerun()

    if st.session_state.assistant_messages:
        if st.button("Clear conversation"):
            st.session_state.assistant_messages = []
            st.rerun()