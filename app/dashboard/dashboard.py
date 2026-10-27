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
from backend.securities import get_security_details, search_securities


st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("Stock Market Dashboard")
st.caption("Explore historical stock and ETF data.")

if "selected_security" not in st.session_state:
    st.session_state.selected_security = None

if "security_page" not in st.session_state:
    st.session_state.security_page = 0

if "last_security_filters" not in st.session_state:
    st.session_state.last_security_filters = None

PAGE_SIZE = 20

left, center, right = st.columns([1, 3, 1.5], gap="large")


with left:
    st.subheader("Find securities")

    search = st.text_input(
        "Search by symbol or name",
        placeholder="Try AAPL",
    )

    with st.expander("Filters"):
        asset_choice = st.selectbox(
            "Asset type",
            ["All", "Stocks", "ETFs"],
        )

    asset_types = {
        "All": None,
        "Stocks": "stock",
        "ETFs": "etf",
    }

    # Return to the first page when the search or filter changes.
    current_filters = (search.strip(), asset_choice)

    if current_filters != st.session_state.last_security_filters:
        st.session_state.security_page = 0
        st.session_state.last_security_filters = current_filters

    try:
        # Request one extra result to tell whether another page exists.
        results = search_securities(
            query=search,
            limit=PAGE_SIZE + 1,
            asset_type=asset_types[asset_choice],
            offset=st.session_state.security_page * PAGE_SIZE,
        )

        has_next_page = len(results) > PAGE_SIZE
        visible_results = results.head(PAGE_SIZE)

        if visible_results.empty:
            st.info("No matching securities found.")
        else:
            st.caption(
                f"Page {st.session_state.security_page + 1} "
                f"· Up to {PAGE_SIZE} results per page"
            )

            with st.container(height=450):
                for _, security in visible_results.iterrows():
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

            previous_col, next_col = st.columns(2)

            with previous_col:
                if st.button(
                    "Previous",
                    disabled=st.session_state.security_page == 0,
                    use_container_width=True,
                ):
                    st.session_state.security_page -= 1
                    st.rerun()

            with next_col:
                if st.button(
                    "Next",
                    disabled=not has_next_page,
                    use_container_width=True,
                ):
                    st.session_state.security_page += 1
                    st.rerun()

    except Exception:
        logging.exception("Security search failed")
        st.error(
            "Could not search the database. "
            "Check the terminal for details."
        )


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

                    if not chart_data.dropna(subset=["adj_close"]).empty:
                        chart_data = chart_data.set_index("trade_date")

                        st.line_chart(
                            chart_data,
                            y="adj_close",
                        )

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

    if selected:
        try:
            details = get_security_details(selected["symbol"])

            if details is None:
                st.info("No details found for this security.")
            else:
                first = details["first_date"]
                last = details["last_date"]
                records = details["price_records"]

                detail_left, detail_mid, detail_right = st.columns(3)

                with detail_left:
                    st.metric(
                        "First available date",
                        str(first) if first else "N/A",
                    )

                with detail_mid:
                    st.metric(
                        "Last available date",
                        str(last) if last else "N/A",
                    )

                with detail_right:
                    st.metric(
                        "Price records",
                        f"{records:,}",
                    )

        except Exception:
            logging.exception("Security details failed")
            st.error(
                "Could not load security details. "
                "Check the terminal for details."
            )
    else:
        st.caption("Select a security to see its details.")


with right:
    st.subheader("Market assistant")
    st.caption("Ask questions about the historical data.")

    st.text_input(
        "Your question",
        placeholder="Which stocks had the highest returns?",
    )

    st.button("Ask")