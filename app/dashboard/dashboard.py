import sys
from pathlib import Path

import streamlit as st


# Make the app and dashboard folders available for imports.
DASHBOARD_DIR = Path(__file__).resolve().parent
APP_DIR = DASHBOARD_DIR.parent

for folder in (APP_DIR, DASHBOARD_DIR):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from chart import show_price_chart
from details import show_security_details
from security_list import show_security_list


st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("Stock Market Dashboard")
st.caption("Explore historical stock and ETF data.")

# Remember selections and pagination when the page updates.
if "selected_security" not in st.session_state:
    st.session_state.selected_security = None

if "security_page" not in st.session_state:
    st.session_state.security_page = 0

if "last_security_filters" not in st.session_state:
    st.session_state.last_security_filters = None


left, center, right = st.columns([1, 3, 1.5], gap="large")

with left:
    show_security_list()

with center:
    selected = st.session_state.selected_security
    show_price_chart(selected)
    show_security_details(selected)

with right:
    st.subheader("Market assistant")
    st.caption("Ask questions about the historical data.")

    st.text_input(
        "Your question",
        placeholder="Which stocks had the highest returns?",
    )

    st.button("Ask")