import logging
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# Allow the dashboard to import the backend package.
APP_DIR = Path(__file__).resolve().parents[1]

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backend.prices import get_prices
from backend.securities import search_securities


st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("Stock Market Dashboard")
st.caption("Explore historical stock and ETF data.")

# Remember the selected security when the page updates.
if "selected_security" not in st.session_state:
    st.session_state.selected_security = None

left, center, right = st.columns([1, 3, 1.5], gap="large")

with left:
    st.subheader("Find securities")

    search = st.text_input(
        "Search by symbol or name",
        placeholder="Try AAPL",
    )

    with st.expander("Filters"):
        st.caption("Filters will be connected in a later step.")

    if search.strip():
        try:
            results = search_securities(search, limit=20)

            if results.empty:
                st.info("No matching securities found.")
            else:
                st.caption("Showing up to 20 results")

                for _, security in results.iterrows():
                    symbol = security["symbol"]
                    name = security["security_name"]

                    if st.button(
                        f"{symbol} — {name}",
                        key=f"security_{symbol}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_security = {
                            "symbol": symbol,
                            "name": name,
                            "asset_type": security["asset_type"],
                            "exchange": security["listing_exchange"],
                        }

        except Exception:
            logging.exception("Security search failed")
            st.error(
                "Could not search the database. "
                "Check the terminal for details."
            )
    else:
        st.caption("Search for a security to see matching results.")

with center:
    selected = st.session_state.selected_security

    if selected:
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
        else:
            try:
                prices = get_prices(
                    selected["symbol"],
                    start_date.isoformat(),
                    end_date.isoformat(),
                )

                if prices.empty:
                    st.info("No price records found for this date range.")
                else:
                    chart_data = pd.DataFrame(prices[["trade_date", "adj_close"]]).copy()

                    chart_data["trade_date"] = pd.to_datetime(
                        chart_data["trade_date"]
                    )

                    chart_data["adj_close"] = pd.to_numeric(
                        chart_data["adj_close"],
                        errors="coerce",
                    )

                    # Mark invalid adjusted prices as missing.
                    invalid = ~prices["valid_adj_close"].fillna(False).astype(bool)
                    chart_data.loc[invalid, "adj_close"] = float("nan")

                    if not chart_data.dropna(subset=["adj_close"]).empty:
                        chart_data = chart_data.set_index("trade_date")
                        st.line_chart(chart_data, y="adj_close")
                        st.caption(
                            "Adjusted closing price; invalid values "
                            "are shown as missing."
                        )
                    else:
                        st.info(
                            "No valid adjusted closing prices were found "
                            "for this date range."
                        )

            except Exception:
                logging.exception("Price chart failed")
                st.error(
                    "Could not load the price chart. "
                    "Check the terminal for details."
                )
    else:
        st.subheader("Price chart")
        st.info("Select a security to view its historical price chart.")

    st.subheader("Security details")
    st.caption("Performance and other statistics will appear here.")

with right:
    st.subheader("Market assistant")
    st.caption("Ask questions about the historical data.")

    st.text_input(
        "Your question",
        placeholder="Which stocks had the highest returns?",
    )

    st.button("Ask")