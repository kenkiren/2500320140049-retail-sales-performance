"""UI-08 — project methodology and documented limitations."""

import streamlit as st

from src.ui import render_page_header


st.set_page_config(page_title="About & Methodology", layout="wide")
render_page_header("About & Methodology", "ShopSphere | ABES MCA Data Analytics")

st.subheader("Project")
st.write(
    "ShopSphere Retail Pvt. Ltd. is a fictional organisation. This synthetic "
    "application covers 2024-01-01 to 2025-12-31, uses random seed 42, and "
    "contains 12 stores, 20,000 sales lines and a 38-column analysis view."
)

st.subheader("Metric definitions")
for title, value in [
    ("Revenue", "SUM(quantity × post-discount selling_unit_price)"),
    ("Profit", "SUM(quantity × (selling_unit_price − cost_price))"),
    ("Margin %", "100 × SUM(profit) / SUM(revenue)"),
    ("AOV", "Revenue / COUNT(DISTINCT order_id)"),
    ("Target achievement", "Store-month actual / store-month target × 100"),
]:
    st.markdown(f"**{title}:** {value}")

st.subheader("Methods")
st.markdown(
    "- **Seasonal index:** calendar-month mean revenue divided by overall monthly mean.\n"
    "- **Forecast:** seasonal-naive baseline; same calendar month in the prior year.\n"
    "- **Welch t-test:** two independent groups at alpha 5%; n<30 is unreliable.\n"
    "- **One-way ANOVA:** three or more groups at alpha 5%; group assumptions are shown.\n"
    "- **Correlation:** Pearson or Spearman; association is not causation."
)

st.subheader("Known limitations")
st.markdown(
    "- No real personal, customer, store or company data is used.\n"
    "- Returns and cancellations are excluded.\n"
    "- No live POS or external integration is represented.\n"
    "- Product cost is static in products.cost_price; no historical cost-at-sale is stored.\n"
    "- Advanced machine-learning forecasting is excluded (BR-15 Won't).\n"
    "- Forecast and statistical findings are estimates for this synthetic dataset, "
    "not claims about real retail markets."
)

st.subheader("Architecture")
st.write(
    "Five physical tables feed one read-only 38-column view: stores, products, "
    "customers, sales_lines and store_targets."
)
