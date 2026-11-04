import logging

import streamlit as st

from backend.securities import get_security_details


def show_security_details(selected):
    """Display the available data range for the selected security."""
    st.subheader("Security details")

    if not selected:
        st.caption("Select a security to see its details.")
        return

    try:
        details = get_security_details(selected["symbol"])

        if details is None:
            st.info("No details found for this security.")
            return

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