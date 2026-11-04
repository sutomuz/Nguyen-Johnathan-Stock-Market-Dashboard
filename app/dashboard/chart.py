import logging
from datetime import date

import pandas as pd
import streamlit as st

from backend.prices import get_prices


def show_price_chart(selected):
    """Display the selected security's historical price chart."""
    if not selected:
        st.subheader("Price chart")
        st.info("Select a security to view its historical price chart.")
        return

    st.subheader(f"{selected['symbol']} — {selected['name']}")

    st.caption(
        f"Type: {selected['asset_type']} | "
        f"Exchange code: {selected['exchange']}"
    )

    st.markdown("**Historical adjusted closing price**")

    date_left, date_right = st.columns(2)

    with date_left:
        start_date = st.date_input(
            "Start date",
            value=date(2019, 1, 1),
        )

    with date_right:
        end_date = st.date_input(
            "End date",
            value=date(2020, 4, 1),
        )

    if start_date > end_date:
        st.warning("The start date must be on or before the end date.")
        return

    try:
        prices = get_prices(
            selected["symbol"],
            start_date.isoformat(),
            end_date.isoformat(),
        )

        if prices.empty:
            st.info("No price records found for this date range.")
            return

        chart_data = pd.DataFrame(
            prices[["trade_date", "adj_close"]]
        ).copy()

        chart_data["trade_date"] = pd.to_datetime(
            chart_data["trade_date"]
        )

        chart_data["adj_close"] = pd.to_numeric(
            chart_data["adj_close"],
            errors="coerce",
        )

        # Mark invalid adjusted prices as missing.
        invalid = (
            ~prices["valid_adj_close"]
            .fillna(False)
            .astype(bool)
        )

        chart_data.loc[invalid, "adj_close"] = float("nan")

        if chart_data.dropna(subset=["adj_close"]).empty:
            st.info(
                "No valid adjusted closing prices were found "
                "for this date range."
            )
            return

        chart_data = chart_data.set_index("trade_date")

        st.line_chart(
            chart_data,
            y="adj_close",
        )

        st.caption(
            "Adjusted closing price; invalid values are shown as missing."
        )

    except Exception:
        logging.exception("Price chart failed")
        st.error(
            "Could not load the price chart. "
            "Check the terminal for details."
        )