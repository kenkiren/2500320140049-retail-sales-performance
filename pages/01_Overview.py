"""UI-01 — filtered headline KPIs and sales overview."""

import pandas as pd
import streamlit as st

from src.charts import category_revenue_figure, monthly_trend_figure
from src.metrics import (
    calculate_category_metrics,
    calculate_equal_period_comparison,
    calculate_kpis,
    calculate_monthly_trend,
)
from src.ui import (
    apply_global_filters,
    load_analysis_data_cached,
    render_analysis_filters,
    render_chart_card,
    render_kpi_card,
    render_page_header,
)


st.set_page_config(page_title="Overview & KPIs", layout="wide")
analysis_data = load_analysis_data_cached()
filters = render_analysis_filters(analysis_data)
filtered = apply_global_filters(analysis_data, filters)
render_page_header(
    "Overview & KPIs",
    "ShopSphere Retail | Synthetic sales performance in INR",
)
start_date, end_date = filters["start_date"], filters["end_date"]
st.caption(
    f"Selected period: {start_date:%d %b %Y} to {end_date:%d %b %Y} | "
    "All measures use the same date, region, store, category and channel filters."
)

if filtered.empty:
    st.info("No sales match the selected filters. Adjust the filters to view KPIs.")
else:
    comparison_scope = dict(filters)
    comparison_scope["start_date"] = pd.to_datetime(analysis_data["sale_date"]).min().date()
    comparison_scope["end_date"] = pd.to_datetime(analysis_data["sale_date"]).max().date()
    comparison_data = apply_global_filters(analysis_data, comparison_scope)
    comparison = calculate_equal_period_comparison(
        comparison_data, start_date, end_date
    )
    kpis = calculate_kpis(filtered)
    definitions = {
        "Revenue": "Quantity × post-discount selling price",
        "Profit": "Revenue − product cost",
        "Units": "Total quantity sold",
        "Distinct orders": "Distinct order IDs",
        "AOV": "Revenue ÷ distinct orders",
    }

    def format_absolute_change(value, metric):
        prefix = "+" if value > 0 else ""
        if metric in {"revenue", "profit", "aov"}:
            return f"{prefix}₹{value:,.2f}"
        return f"{prefix}{value:,.0f}"

    card_definitions = (
        ("Revenue", "revenue", lambda value: f"₹{value:,.2f}"),
        ("Profit", "profit", lambda value: f"₹{value:,.2f}"),
        ("Units", "units", lambda value: f"{value:,.0f}"),
        ("Distinct orders", "order_count", lambda value: f"{value:,.0f}"),
        ("AOV", "aov", lambda value: f"₹{value:,.2f}"),
    )
    cards = st.columns(5)
    for column, (label, key, formatter) in zip(cards, card_definitions):
        change = comparison["changes"][key]
        percent_change = change["pct_change"]
        percent_text = (
            f"{percent_change:+.1f}%"
            if pd.notna(percent_change)
            else "N/A (previous period was zero)"
        )
        delta = (
            f"{format_absolute_change(change['absolute_change'], key)} | "
            f"{percent_text} vs previous period"
        )
        with column:
            render_kpi_card(
                label,
                formatter(kpis[key]),
                delta=delta,
                helper=definitions[label],
            )

    monthly = calculate_monthly_trend(filtered)
    categories = calculate_category_metrics(filtered)
    stores = calculate_category_metrics(filtered, group_by="store_name")
    category_column, store_column = st.columns([1.5, 1])
    with category_column:
        render_chart_card(
            "Monthly revenue and profit",
            monthly_trend_figure(monthly),
            "Monthly totals reconcile to the selected-period KPI totals.",
        )
    with store_column:
        st.subheader("Category and store highlights")
        top_category = categories.sort_values("revenue", ascending=False).iloc[0]
        top_store = stores.sort_values("revenue", ascending=False).iloc[0]
        st.metric(
            "Top category by revenue",
            str(top_category["category"]),
            f"₹{top_category['revenue']:,.2f}",
        )
        st.metric(
            "Top store by revenue",
            str(top_store["store_name"]),
            f"₹{top_store['revenue']:,.2f}",
        )
        with st.expander("Revenue by category"):
            st.plotly_chart(
                category_revenue_figure(categories),
                use_container_width=True,
            )

    st.caption(
        f"Reconciliation: monthly revenue total ₹{monthly['revenue'].sum():,.2f}; "
        f"headline revenue ₹{kpis['revenue']:,.2f}."
    )
    st.caption(
        "Margin % is total profit divided by total revenue. It is not the mean "
        "of individual line margins. Period changes compare with the immediately "
        "preceding period of equal duration."
    )
