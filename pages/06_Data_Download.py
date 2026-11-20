"""UI-06 — privacy-safe aggregate preview and CSV export."""

import streamlit as st

from src.export import build_safe_aggregate, export_preview_csv
from src.ui import (
    apply_global_filters,
    load_analysis_data_cached,
    render_analysis_filters,
    render_data_table,
    render_page_header,
)


st.set_page_config(page_title="Data & Download", layout="wide")
analysis_data = load_analysis_data_cached()
filters = render_analysis_filters(analysis_data)
filtered = apply_global_filters(analysis_data, filters)
render_page_header("Data & Download", "Filtered aggregate preview; no customer-level identifiers")

preview = build_safe_aggregate(filtered)
st.caption(
    f"Selected period: {filters['start_date']} to {filters['end_date']} | "
    f"Source sales lines: {len(filtered):,}"
)
st.subheader("Filtered aggregate preview")
render_data_table(
    preview,
    formatters={"margin_pct": lambda value: f"{value:.2f}%"},
)

st.markdown(
    f"**Rows:** {len(preview)}  |  "
    f"**Revenue:** ₹{preview['revenue'].sum():,.2f}  |  "
    f"**Profit:** ₹{preview['profit'].sum():,.2f}"
)
csv_bytes = export_preview_csv(preview)
st.download_button(
    "Download visible aggregate as CSV",
    data=csv_bytes,
    file_name="shopsphere_filtered_aggregate.csv",
    mime="text/csv",
)
st.caption(
    "Privacy rule: exports contain category aggregates only. Customer IDs, "
    "names, addresses, phones and emails are excluded."
)
