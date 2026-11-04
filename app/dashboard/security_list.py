import logging

import pandas as pd
import streamlit as st

from backend.screener import screen_securities
from backend.securities import search_securities
from filters import show_filters


PAGE_SIZE = 20


@st.cache_data(ttl=300, show_spinner=False)
def cached_screen(
    start_date,
    end_date,
    query,
    asset_type,
    exchange,
    min_return,
    max_return,
    min_volatility,
    max_volatility,
    exclude_flagged,
    offset,
):
    """Cache screener results briefly to reduce repeated database work."""
    return screen_securities(
        start_date=start_date,
        end_date=end_date,
        query=query,
        asset_type=asset_type,
        exchange=exchange,
        min_return=min_return,
        max_return=max_return,
        min_volatility=min_volatility,
        max_volatility=max_volatility,
        exclude_flagged=exclude_flagged,
        limit=PAGE_SIZE + 1,
        offset=offset,
    )


def format_percent(value):
    """Format a decimal as a percentage, including missing values."""
    if pd.isna(value):
        return "N/A"

    return f"{value:.2%}"


def show_security_list():
    """Display filters, search, and paginated security results."""
    st.subheader("Find securities")

    search = st.text_input(
        "Search by symbol or name",
        placeholder="Try AAPL",
    ).strip()

    if "last_search" not in st.session_state:
        st.session_state.last_search = ""

    if search != st.session_state.last_search:
        st.session_state.security_page = 0
        st.session_state.last_search = search

    show_filters()

    filters = st.session_state.applied_filters
    offset = st.session_state.security_page * PAGE_SIZE

    try:
        if st.session_state.filters_active:
            with st.spinner("Screening historical prices..."):
                results = cached_screen(
                    start_date=filters["start_date"].isoformat(),
                    end_date=filters["end_date"].isoformat(),
                    query=search,
                    asset_type=filters["asset_type"],
                    exchange=filters["exchange"],
                    min_return=filters["min_return"],
                    max_return=filters["max_return"],
                    min_volatility=filters["min_volatility"],
                    max_volatility=filters["max_volatility"],
                    exclude_flagged=filters["exclude_flagged"],
                    offset=offset,
                )

            st.caption(
                f"Filter period: {filters['start_date']} "
                f"through {filters['end_date']}"
            )
        else:
            results = search_securities(
                query=search,
                limit=PAGE_SIZE + 1,
                offset=offset,
            )

        has_next_page = len(results) > PAGE_SIZE
        visible_results = results.head(PAGE_SIZE)

        if visible_results.empty:
            st.info("No matching securities found.")
            return

        st.caption(
            f"Page {st.session_state.security_page + 1} "
            f"· Up to {PAGE_SIZE} results per page"
        )

        with st.container(height=350):
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

                if st.session_state.filters_active:
                    total_return = format_percent(
                        security["total_return"]
                    )

                    volatility = format_percent(
                        security["annualized_volatility"]
                    )

                    st.caption(
                        f"Return: {total_return} · "
                        f"Annualized volatility: {volatility}"
                    )

                    needs_review = security["needs_review"]

                    if str(needs_review).lower() == "true":
                        st.caption("⚠️ Flagged move: review suggested")

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
        logging.exception("Security search or screening failed")
        st.error(
            "Could not load securities. Check the terminal for details."
        )