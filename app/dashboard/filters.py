import logging
from datetime import date

import streamlit as st

from backend.database import get_connection


DEFAULT_FILTERS = {
    "asset_type": None,
    "exchange": None,
    "start_date": date(2020, 3, 1),
    "end_date": date(2020, 4, 1),
    "min_return": None,
    "max_return": None,
    "min_volatility": None,
    "max_volatility": None,
    "exclude_flagged": False,
}


@st.cache_data(ttl=300, show_spinner=False)
def get_exchange_codes():
    """Return listing exchange codes found in the database."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT listing_exchange
                FROM securities
                WHERE has_price_file
                  AND listing_exchange IS NOT NULL
                  AND listing_exchange <> ''
                ORDER BY listing_exchange;
                """
            )

            return [row[0] for row in cursor.fetchall()]


def initialize_filter_state():
    """Initialize the applied filters and form version."""
    if "applied_filters" not in st.session_state:
        st.session_state.applied_filters = DEFAULT_FILTERS.copy()

    if "filters_active" not in st.session_state:
        st.session_state.filters_active = False

    if "filter_form_version" not in st.session_state:
        st.session_state.filter_form_version = 0


def reset_filters():
    """Clear applied filters and reset the form."""
    st.session_state.applied_filters = DEFAULT_FILTERS.copy()
    st.session_state.filters_active = False
    st.session_state.security_page = 0
    st.session_state.filter_form_version += 1


def as_percent(value):
    """Convert a stored decimal to a percentage for display."""
    if value is None:
        return None

    return float(value * 100)


def as_decimal(value):
    """Convert a percentage to a decimal for the screener."""
    if value is None:
        return None

    return float(value / 100)


def show_filters():
    """Display and apply the security filter form."""
    initialize_filter_state()

    try:
        exchange_codes = get_exchange_codes()
    except Exception:
        logging.exception("Could not load exchange codes")
        exchange_codes = []
        st.warning("Could not load exchange choices. Check the terminal.")

    active = st.session_state.applied_filters
    form_version = st.session_state.filter_form_version

    asset_options = {
        "All": None,
        "Stocks": "stock",
        "ETFs": "etf",
    }

    asset_labels = list(asset_options)
    asset_values = list(asset_options.values())

    exchange_options = ["All"] + exchange_codes

    if active["exchange"] in exchange_codes:
        exchange_index = exchange_options.index(active["exchange"])
    else:
        exchange_index = 0

    with st.expander("Filters"):
        with st.form(f"filter_form_{form_version}"):
            asset_label = st.selectbox(
                "Asset type",
                asset_labels,
                index=asset_values.index(active["asset_type"]),
            )

            exchange_label = st.selectbox(
                "Listing exchange code",
                exchange_options,
                index=exchange_index,
            )

            filter_start = st.date_input(
                "Filter start date",
                value=active["start_date"],
            )

            filter_end = st.date_input(
                "Filter end date",
                value=active["end_date"],
            )

            st.caption(
                "Return and volatility use this date range. "
                "The chart has separate date controls."
            )

            st.caption("Leave a field blank if you don't want a limit.")

            min_return_pct = st.number_input(
                "Minimum total return (%)",
                value=as_percent(active["min_return"]),
                placeholder="No minimum",
                step=1.0,
            )

            max_return_pct = st.number_input(
                "Maximum total return (%)",
                value=as_percent(active["max_return"]),
                placeholder="No maximum",
                step=1.0,
            )

            min_volatility_pct = st.number_input(
                "Minimum annualized volatility (%)",
                min_value=0.0,
                value=as_percent(active["min_volatility"]),
                placeholder="No minimum",
                step=1.0,
            )

            max_volatility_pct = st.number_input(
                "Maximum annualized volatility (%)",
                min_value=0.0,
                value=as_percent(active["max_volatility"]),
                placeholder="No maximum",
                step=1.0,
            )

            exclude_flagged = st.checkbox(
                "Exclude securities with flagged daily moves",
                value=active["exclude_flagged"],
            )

            st.caption(
                "Moves above 50% are flagged for review. "
                "A flag does not prove the data is incorrect."
            )

            apply_filters = st.form_submit_button(
                "Apply filters",
                use_container_width=True,
            )

        if apply_filters:
            min_return = as_decimal(min_return_pct)
            max_return = as_decimal(max_return_pct)
            min_volatility = as_decimal(min_volatility_pct)
            max_volatility = as_decimal(max_volatility_pct)

            if filter_start >= filter_end:
                st.error("Filter start date must be before the end date.")

            elif (
                min_return is not None
                and max_return is not None
                and min_return > max_return
            ):
                st.error("Minimum return cannot exceed maximum return.")

            elif (
                min_volatility is not None
                and max_volatility is not None
                and min_volatility > max_volatility
            ):
                st.error(
                    "Minimum volatility cannot exceed maximum volatility."
                )

            else:
                st.session_state.applied_filters = {
                    "asset_type": asset_options[asset_label],
                    "exchange": (
                        None if exchange_label == "All" else exchange_label
                    ),
                    "start_date": filter_start,
                    "end_date": filter_end,
                    "min_return": min_return,
                    "max_return": max_return,
                    "min_volatility": min_volatility,
                    "max_volatility": max_volatility,
                    "exclude_flagged": exclude_flagged,
                }

                st.session_state.filters_active = True
                st.session_state.security_page = 0
                st.rerun()

        st.button(
            "Clear filters",
            on_click=reset_filters,
            use_container_width=True,
        )