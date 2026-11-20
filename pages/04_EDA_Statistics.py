"""UI-04 — discounts, customers, mixes, calendar and statistical tests."""

import pandas as pd
import streamlit as st

from src.metrics import (
    calculate_channel_mix,
    calculate_customer_mix,
    calculate_discount_metrics,
    calculate_payment_mix,
    calculate_weekday_month,
)
from src.stats import correlation_analysis, one_way_anova, welch_aov_test
from src.charts import scatter_figure
from src.ui import (
    apply_global_filters,
    load_analysis_data_cached,
    render_analysis_filters,
    render_chart_card,
    render_data_table,
    render_page_header,
)


st.set_page_config(page_title="EDA & Statistics", layout="wide")
analysis_data = load_analysis_data_cached()
filters = render_analysis_filters(analysis_data)
filtered = apply_global_filters(analysis_data, filters)
render_page_header("EDA & Statistics", "Descriptive patterns and 5% significance tests")

if filtered.empty:
    st.info("No sales match the selected filters. Adjust the filters to run EDA.")
else:
    discount_tab, customer_tab, mix_tab, calendar_tab, stats_tab = st.tabs(
        ["Discounts", "Customers", "Channel & Payment", "Calendar", "Statistical Tests"]
    )

    with discount_tab:
        discounts = calculate_discount_metrics(filtered)
        render_chart_card(
            "Discount vs quantity",
            scatter_figure(
                filtered, "discount_pct", "quantity",
                title="Discount vs quantity",
            ),
        )
        render_data_table(
            discounts,
            formatters={"margin_pct": lambda value: f"{value:.2f}%"},
        )
        st.caption("Bands: 0%; 1-10%; 11-20%; >20%. Margin is weighted profit/revenue.")

    with customer_tab:
        customer_mix = calculate_customer_mix(filtered)
        segment = customer_mix.groupby("segment", as_index=False).agg(revenue=("revenue", "sum"))
        segment["share_pct"] = (
            segment["revenue"] / segment["revenue"].sum() * 100
            if segment["revenue"].sum()
            else 0
        )
        st.subheader("Customer segment revenue")
        render_data_table(
            segment,
            formatters={"share_pct": lambda value: f"{value:.2f}%"},
        )
        st.subheader("Repeat vs one-time customers")
        repeat = customer_mix.groupby("repeat_status", as_index=False).agg(revenue=("revenue", "sum"))
        repeat["share_pct"] = (
            repeat["revenue"] / repeat["revenue"].sum() * 100
            if repeat["revenue"].sum()
            else 0
        )
        render_data_table(
            repeat,
            formatters={"share_pct": lambda value: f"{value:.2f}%"},
        )

    with mix_tab:
        payment = calculate_payment_mix(filtered)
        channel = calculate_channel_mix(filtered)
        st.subheader("Monthly payment shares")
        render_data_table(payment)
        st.subheader("Monthly channel shares")
        render_data_table(channel)
        st.caption("Payment and channel shares reconcile to 100% per month subject to rounding.")

    with calendar_tab:
        calendar = calculate_weekday_month(filtered)
        st.subheader("Weekday performance")
        render_data_table(calendar["weekday"])
        st.subheader("Month performance")
        render_data_table(calendar["month"])

    with stats_tab:
        st.subheader("Welch two-group AOV test")
        group_column = st.selectbox(
            "Comparison dimension",
            ["region", "segment", "channel"],
            key="stats_group_dimension",
        )
        available_groups = sorted(filtered[group_column].dropna().unique().tolist())
        if len(available_groups) < 2:
            st.info("At least two groups are required for a Welch test.")
        else:
            group_a = st.selectbox("Group A", available_groups, key="stats_group_a")
            group_b_options = [value for value in available_groups if value != group_a]
            group_b = st.selectbox("Group B", group_b_options, key="stats_group_b")
            aov_a = filtered.loc[filtered[group_column] == group_a].groupby("order_id")["revenue"].sum()
            aov_b = filtered.loc[filtered[group_column] == group_b].groupby("order_id")["revenue"].sum()
            welch = welch_aov_test(aov_a, aov_b)
            st.write(welch["verdict"])
            st.write(welch["interpretation"])
            st.caption(
                f"nA={welch['n_a']}, nB={welch['n_b']}, "
                f"t={welch['t_statistic']:.3f}, p={welch['p_value']:.3f}"
                + (" | UNRELIABLE: group n<30" if welch["unreliable"] else "")
            )

        st.subheader("One-way ANOVA")
        anova_groups = {
            str(value): filtered.loc[filtered[group_column] == value]
            .groupby("order_id")["revenue"].sum()
            .to_numpy()
            for value in available_groups
        }
        if len(anova_groups) >= 3:
            anova = one_way_anova(anova_groups)
            st.write(anova["verdict"])
            st.write(anova["interpretation"])
            st.caption(
                f"F={anova['f_statistic']:.3f}, p={anova['p_value']:.3f}"
                + (" | UNRELIABLE: group n<30" if anova["unreliable"] else "")
            )
        else:
            st.info("At least three groups are required for one-way ANOVA.")

        st.subheader("Correlation")
        method = st.selectbox("Correlation method", ["pearson", "spearman"])
        correlations = correlation_analysis(filtered, method=method)
        render_data_table(
            correlations[
                ["pair", "coefficient", "p_value", "sample_size", "strength", "interpretation"]
            ],
            formatters={
                "coefficient": lambda value: f"{value:.3f}",
                "p_value": lambda value: f"{value:.3f}",
            },
        )
        st.caption("Correlation measures association, not causation.")
