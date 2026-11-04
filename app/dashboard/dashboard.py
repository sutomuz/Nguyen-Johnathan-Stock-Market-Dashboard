import sys
from pathlib import Path

import streamlit as st


DASHBOARD_DIR = Path(__file__).resolve().parent
APP_DIR = DASHBOARD_DIR.parent

for folder in (APP_DIR, DASHBOARD_DIR):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from assistant import show_assistant
from chart import show_price_chart
from details import show_security_details
from security_list import show_security_list


st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        [data-testid="stMainBlockContainer"] {
            max-width: 100%;
            padding: 3.75rem 0 0 0;
        }

        [data-testid="stHeader"] {
            background-color: #0e1117;
        }

        /* Left sidebar. */
        [data-testid="stSidebar"] {
            background-color: #1b1d24;
            border-right: 1px solid #343740;
        }

        .sidebar-title {
            font-size: 1.2rem;
            font-weight: 700;
            line-height: 1.25;
            margin: 0;
        }

        .sidebar-description {
            color: #a9aab1;
            font-size: 0.8rem;
            line-height: 1.4;
            margin: 0.3rem 0 0.75rem;
        }

        /* Middle column. */
        [data-testid="stColumn"]:has(.st-key-chart_section) {
            background-color: #0e1117;
            min-height: 100vh;
        }

        /* Right: market assistant. */
        [data-testid="stColumn"]:has(.st-key-assistant_section) {
            background-color: #1b1d24;
            border-left: 1px solid #343740;
            min-height: 100vh;
        }

        /* Rectangular chart section. */
        .st-key-chart_section {
            background-color: #181d24;
            border: 1px solid #343b44;
            border-radius: 0;
            padding: 0.75rem 1.25rem 1rem;
        }

        .st-key-chart_section [data-testid="stVerticalBlock"] {
            gap: 0.5rem;
        }

        /* Compact security details section. */
        .st-key-details_section {
            background-color: #1b1d24;
            border-top: 1px solid #343740;
            border-radius: 0;
            padding: 0.75rem 2rem 1rem;
        }

        .st-key-details_section [data-testid="stVerticalBlock"] {
            gap: 0.4rem;
        }

        .st-key-details_section h2 {
            font-size: 1.25rem;
            padding-bottom: 0.25rem;
        }

        .st-key-details_section [data-testid="stMetricLabel"] {
            font-size: 0.85rem;
        }

        .st-key-details_section [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }

        /* Compact assistant section. */
        .st-key-assistant_section {
            padding: 0.75rem 1rem;
        }

        [data-testid="stMainBlockContainer"] h1 {
            font-size: 2rem;
            padding-top: 0;
            padding-bottom: 0.25rem;
        }

        [data-testid="stMainBlockContainer"] h2 {
            font-size: 1.35rem;
            padding-top: 0;
            padding-bottom: 0.25rem;
        }

        [data-testid="stMainBlockContainer"] h3 {
            font-size: 1.15rem;
            padding-top: 0;
            padding-bottom: 0.25rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "selected_security" not in st.session_state:
    st.session_state.selected_security = None

if "security_page" not in st.session_state:
    st.session_state.security_page = 0

if "last_security_filters" not in st.session_state:
    st.session_state.last_security_filters = None


with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-title">Stock Market Dashboard</div>
        <div class="sidebar-description">
            Explore historical stock and ETF data.
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_security_list()


chart_column, assistant_column = st.columns(
    [2.5, 1],
    gap=None,
)

with chart_column:
    selected = st.session_state.selected_security

    with st.container(key="chart_section"):
        show_price_chart(selected)

    with st.container(key="details_section"):
        show_security_details(selected)

with assistant_column:
    with st.container(key="assistant_section"):
        show_assistant()