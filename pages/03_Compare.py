"""UI-03 — category, product and store/region performance comparisons."""

import pandas as pd
import streamlit as st

from src.charts import (
    category_revenue_figure,
    target_comparison_figure,
)
from src.db import load_store_targets, load_stores
from src.metrics import (
    calculate_category_metrics,
    calculate_region_target_attainment,
    calculate_store_target_attainment,
    rank_products,
)
from src.ui import (
    apply_global_filters,
    load_analysis_data_cached,
    render_analysis_filters,
    render_chart_card,
    render_data_table,
    render_page_header,
)


@st.cache_data(show_spinner=False)
def _load_targets():
    return load_store_targets()


@st.cache_data(show_spinner=False)
def _load_stores():
    return load_stores()


st.set_page_config(page_title="Business Comparison", layout="wide")
analysis_data = load_analysis_data_cached()
filters = render_analysis_filters(analysis_data)
filtered = apply_global_filters(analysis_data, filters)
render_page_header(
    "Business Comparison",
    "Category profitability, deterministic product rankings and target attainment",
)

if filtered.empty:
    st.info("No sales match the selected filters. Adjust the filters to compare results.")
else:
    category_tab, product_tab, target_tab = st.tabs(
        ["Category & sub-category", "Top/bottom products", "Stores & regions vs targets"]
    )

    with category_tab:
        category_metrics = calculate_category_metrics(filtered)
        subcategory_metrics = calculate_category_metrics(
            filtered, group_by=["category", "sub_category"]
        )
        category_chart, category_summary = st.columns([1.5, 1])
        with category_chart:
            render_chart_card(
                "Revenue by category",
                category_revenue_figure(category_metrics),
                "Category totals use the same filtered sales lines as the headline KPIs.",
            )
        with category_summary:
            st.subheader("Category profitability")
            render_data_table(
                category_metrics.sort_values("revenue", ascending=False),
                formatters={
                    "margin_pct": lambda value: f"{value:.2f}%",
                    "is_low_margin": lambda value: "Yes" if value else "No",
                    "is_loss_making": lambda value: "Yes" if value else "No",
                },
            )
        st.subheader("Sub-category profitability")
        render_data_table(
            subcategory_metrics.sort_values(
                ["category", "revenue"], ascending=[True, False]
            ),
            formatters={
                "margin_pct": lambda value: f"{value:.2f}%",
                "is_low_margin": lambda value: "Yes" if value else "No",
                "is_loss_making": lambda value: "Yes" if value else "No",
            },
        )
        st.caption(
            "Margin is total profit divided by total revenue. Low margin means "
            "below 10%; loss-making means total profit is negative."
        )

    with product_tab:
        stores = _load_stores()
        available_stores = stores.copy()
        if filters["region"] is not None:
            available_stores = available_stores.loc[
                available_stores["region"] == filters["region"]
            ]
        if filters["store_ids"]:
            available_stores = available_stores.loc[
                available_stores["store_id"].isin(filters["store_ids"])
            ]
        if available_stores.empty:
            st.info("No stores are available in the selected filter scope.")
        else:
            scope_label = (
                "Current shared filter scope"
                if not filters["store_ids"]
                else "Selected global store scope"
            )
            st.caption(
                f"The first ranking uses {scope_label}. The selected-store ranking "
                "adds one store within the current region/store filter."
            )
            store_names = dict(
                zip(available_stores["store_id"], available_stores["store_name"])
            )
            chosen_store = st.selectbox(
                "Store for selected-store rankings",
                options=available_stores["store_id"].tolist(),
                format_func=lambda store_id: (
                    f"{store_names[store_id]} (ID {store_id})"
                ),
                key="compare_product_store",
            )
            selected_store_sales = filtered.loc[
                filtered["store_id"] == chosen_store
            ]
            for scope_title, sales_scope in (
                ("Current shared filter scope", filtered),
                (f"Selected store: {store_names[chosen_store]}", selected_store_sales),
            ):
                st.subheader(scope_title)
                if sales_scope.empty:
                    st.info("No sales match this ranking scope.")
                    continue
                revenue_column, unit_column = st.columns(2)
                with revenue_column:
                    st.markdown("**Top 10 by revenue**")
                    render_data_table(
                        rank_products(
                            sales_scope, metric="revenue", ascending=False, limit=10
                        )
                    )
                    st.markdown("**Bottom 10 by revenue**")
                    render_data_table(
                        rank_products(
                            sales_scope, metric="revenue", ascending=True, limit=10
                        )
                    )
                with unit_column:
                    st.markdown("**Top 10 by units**")
                    render_data_table(
                        rank_products(
                            sales_scope, metric="quantity", ascending=False, limit=10
                        )
                    )
                    st.markdown("**Bottom 10 by units**")
                    render_data_table(
                        rank_products(
                            sales_scope, metric="quantity", ascending=True, limit=10
                        )
                    )
            st.caption(
                "Ties follow BRL-12: the other measure is the secondary sort, "
                "then product name alphabetically."
            )

    with target_tab:
        targets = _load_targets()
        stores = _load_stores()
        start_month = pd.Timestamp(filters["start_date"]).to_period("M")
        end_month = pd.Timestamp(filters["end_date"]).to_period("M")
        target_dates = pd.to_datetime(targets["target_month"], errors="coerce")
        target_months = target_dates.dt.to_period("M").between(start_month, end_month)
        targets = targets.loc[target_months]
        if filters["region"] is not None:
            region_store_ids = stores.loc[
                stores["region"] == filters["region"], "store_id"
            ]
            targets = targets.loc[targets["store_id"].isin(region_store_ids)]
        if filters["store_ids"]:
            targets = targets.loc[targets["store_id"].isin(filters["store_ids"])]

        store_results = calculate_store_target_attainment(filtered, targets)
        if store_results.empty:
            st.info("No monthly targets match the selected date, region and store filters.")
        else:
            region_results = calculate_region_target_attainment(
                store_results, stores
            )
            store_results = store_results.merge(
                stores[["store_id", "store_name", "region"]],
                on="store_id",
                how="left",
                validate="many_to_one",
            )
            store_results["below_target"] = store_results["achievement_pct"] < 100
            if filters["category"] is not None or filters["channel"] is not None:
                st.info(
                    "Category/channel filters narrow actual sales, while targets "
                    "remain the approved full-store monthly targets; no category-"
                    "or channel-level targets exist in the source schema."
                )
            if (
                pd.Timestamp(filters["start_date"]).day != 1
                or filters["end_date"]
                != (
                    pd.Timestamp(filters["end_date"])
                    + pd.offsets.MonthEnd(0)
                ).date()
            ):
                st.info(
                    "The selected dates cover partial calendar months. Actuals use "
                    "the selected dates; targets remain full-month values."
                )

            st.subheader("Store-month actual vs target")
            month_values = sorted(store_results["sale_month"].dropna().unique())
            chosen_month = st.selectbox(
                "Month to chart",
                options=month_values,
                format_func=lambda value: pd.Timestamp(value).strftime("%b %Y"),
                key="compare_target_month",
            )
            selected_month_results = store_results.loc[
                store_results["sale_month"] == chosen_month
            ].sort_values("store_name")
            target_chart, target_table = st.columns([1.3, 1])
            with target_chart:
                render_chart_card(
                    "Actual revenue and monthly target",
                    target_comparison_figure(selected_month_results),
                    "Actual revenue follows the active global filters; target values "
                    "are loaded once per store-month from store_targets.",
                )
            with target_table:
                render_data_table(
                    selected_month_results[
                        [
                            "store_name", "actual", "target", "variance",
                            "achievement_pct", "below_target",
                        ]
                    ],
                    formatters={
                        "achievement_pct": lambda value: f"{value:.2f}%",
                        "below_target": lambda value: "Yes" if value else "No",
                    },
                )
            st.subheader("Region-month attainment")
            render_data_table(
                region_results,
                formatters={"achievement_pct": lambda value: f"{value:.2f}%"},
            )
            st.caption(
                "Variance = actual − target. Region achievement is sum(actual) ÷ "
                "sum(target), not the mean of store achievement percentages."
            )
