"""ShopSphere Retail Sales Performance Analysis application entry point."""

import logging
import sqlite3

import pandas as pd
import streamlit as st

from src.db import load_analysis_data


LOGGER = logging.getLogger(__name__)


@st.cache_data(show_spinner="Loading the read-only sales analysis data...")
def _load_data():
    return load_analysis_data()


st.set_page_config(
    page_title="ShopSphere Retail Sales Performance",
    page_icon="📊",
    layout="wide",
)

st.title("ShopSphere Retail Sales Performance")
st.caption("Retail Sales Performance Analysis | Synthetic data demonstration")
st.write(
    "Explore sales performance across stores, products, customers, targets, "
    "and trading periods. All records are synthetic; this application is "
    "read-only and does not represent actual ShopSphere or market results."
)

try:
    analysis_data = _load_data()
except (OSError, sqlite3.Error, pd.errors.DatabaseError, ValueError):
    LOGGER.exception("Unable to load canonical analysis data")
    st.error(
        "The canonical analysis dataset could not be loaded. Check that "
        "data/app.db is present and valid, then restart the application."
    )
else:
    st.success(
        f"Read-only data connection ready: {len(analysis_data):,} sales lines "
        f"and {analysis_data.shape[1]} analysis fields."
    )
    st.caption("Use the navigation menu to open one of the eight analysis screens.")
