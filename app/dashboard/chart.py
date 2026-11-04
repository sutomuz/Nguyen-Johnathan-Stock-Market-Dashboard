import logging
from typing import Any
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend.prices import get_prices


@st.cache_data(ttl=300, show_spinner=False)
def load_price_history(symbol):
    """Load the available historical prices for one security."""
    return get_prices(
        symbol,
        "1900-01-01",
        date.today().isoformat(),
    )


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

    try:
        prices = load_price_history(selected["symbol"])

        if prices.empty:
            st.info("No historical price records were found.")
            return

        chart_data: Any = prices[
            ["trade_date", "adj_close", "valid_adj_close"]
        ].copy()

        chart_data["trade_date"] = pd.to_datetime(
            chart_data["trade_date"],
            errors="coerce",
        )

        chart_data["adj_close"] = pd.to_numeric(
            chart_data["adj_close"],
            errors="coerce",
        )

        valid_flags = pd.Series(chart_data["valid_adj_close"])
        invalid = ~valid_flags.fillna(False).astype(bool)

        chart_data.loc[invalid, "adj_close"] = float("nan")

        chart_data = chart_data.dropna(
            subset=["trade_date"]
        ).sort_values("trade_date")

        valid_prices = chart_data[
            chart_data["adj_close"].notna()
        ]

        if valid_prices.empty:
            st.info("No valid adjusted closing prices were found.")
            return

        first_date = valid_prices["trade_date"].min().date()
        last_date: Any = valid_prices["trade_date"].max().date()

        timeframe = st.radio(
            "Time frame",
            ["1M", "3M", "6M", "1Y", "5Y", "All", "Custom"],
            index=3,
            horizontal=True,
            key=f"chart_timeframe_{selected['symbol']}",
        )

        if timeframe == "Custom":
            date_left, date_right = st.columns(2)

            with date_left:
                start_date = st.date_input(
                    "Start date",
                    value=first_date,
                    min_value=first_date,
                    max_value=last_date,
                    key=f"chart_start_{selected['symbol']}",
                )

            with date_right:
                end_date = st.date_input(
                    "End date",
                    value=last_date,
                    min_value=first_date,
                    max_value=last_date,
                    key=f"chart_end_{selected['symbol']}",
                )

            if start_date > end_date:
                st.warning(
                    "The start date must be on or before the end date."
                )
                return

        else:
            end_date = last_date

            offsets = {
                "1M": pd.DateOffset(months=1),
                "3M": pd.DateOffset(months=3),
                "6M": pd.DateOffset(months=6),
                "1Y": pd.DateOffset(years=1),
                "5Y": pd.DateOffset(years=5),
            }

            if timeframe == "All":
                start_date = first_date
            else:
                end_timestamp: Any = pd.Timestamp(last_date)
                calculated_start = (end_timestamp - offsets[timeframe]).date()

                start_date = max(first_date, calculated_start)

        visible_data: Any = chart_data[
            (chart_data["trade_date"] >= pd.Timestamp(start_date))
            & (chart_data["trade_date"] <= pd.Timestamp(end_date))
        ].copy()

        visible_valid = visible_data[
            visible_data["adj_close"].notna()
        ]

        if visible_valid.empty:
            st.info("No valid prices were found for this date range.")
            return

        first_visible = visible_valid["trade_date"].min()
        last_visible = visible_valid["trade_date"].max()

        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=visible_data["trade_date"],
                y=visible_data["adj_close"],
                mode="lines",
                line=dict(color="#9bc8ff", width=2),
                connectgaps=False,
                hovertemplate=(
                    "Date: %{x|%b %d, %Y}<br>"
                    "Adjusted close: $%{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

        figure.update_layout(
            template="plotly_dark",
            paper_bgcolor="#181d24",
            plot_bgcolor="#181d24",
            margin=dict(l=20, r=20, t=20, b=20),
            height=450,
            xaxis_title=None,
            yaxis_title="Adjusted close",
            showlegend=False,
        )

        if first_visible < last_visible:
            figure.update_xaxes(
                range=[first_visible, last_visible],
                minallowed=first_visible,
                maxallowed=last_visible,
            )

        st.plotly_chart(
            figure,
            use_container_width=True,
            config={"scrollZoom": True},
        )

        st.caption(
            f"Showing available prices from {first_visible.date()} "
            f"through {last_visible.date()}. "
            "Invalid adjusted prices are shown as gaps."
        )

    except Exception:
        logging.exception("Price chart failed")
        st.error(
            "Could not load the price chart. "
            "Check the terminal for details."
        )