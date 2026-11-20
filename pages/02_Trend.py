"""UI-02 — monthly revenue/profit, seasonality and simple estimates."""

import pandas as pd
import streamlit as st

from src.charts import monthly_trend_figure, seasonal_index_figure
from src.metrics import (
    calculate_monthly_trend,
    calculate_seasonal_index,
)
from src.stats import three_month_forecast
from src.ui import (
    apply_global_filters,
    load_analysis_data_cached,
    render_analysis_filters,
    render_chart_card,
    render_data_table,
    render_page_header,
)


st.set_page_config(page_title="Sales Trend & Forecast", layout="wide")
analysis_data = load_analysis_data_cached()
filters = render_analysis_filters(analysis_data)
filtered = apply_global_filters(analysis_data, filters)
render_page_header(
    "Sales Trend & Forecast",
    "Monthly sales history, calendar seasonality and a transparent baseline estimate",
)

if filtered.empty:
    st.info("No sales match the selected filters. Adjust the filters to view trends.")
else:
    monthly = calculate_monthly_trend(filtered)
    if monthly.empty:
        st.info("No monthly sales are available for the selected filters.")
    else:
        st.caption(
            f"Selected period: {filters['start_date']:%d %b %Y} to "
            f"{filters['end_date']:%d %b %Y} | Monthly values are aggregated "
            "from the filtered sales lines."
        )
        st.subheader("Monthly revenue and profit")
        render_chart_card(
            "Revenue and profit by month",
            monthly_trend_figure(monthly),
            f"{len(monthly)} months | Revenue ₹{monthly['revenue'].sum():,.2f} | "
            f"Profit ₹{monthly['profit'].sum():,.2f}",
        )

        seasonality = calculate_seasonal_index(monthly)
        seasonality_chart, seasonality_table = st.columns([1.5, 1])
        with seasonality_chart:
            render_chart_card(
                "Calendar-month seasonal index",
                seasonal_index_figure(seasonality),
                "Index = calendar-month mean revenue ÷ overall monthly mean revenue; "
                "1.0 represents the average month.",
            )
        with seasonality_table:
            st.subheader("Seasonality by month")
            render_data_table(
                seasonality.sort_values("seasonal_index", ascending=False)
                .reset_index(drop=True),
                formatters={"seasonal_index": lambda value: f"{value:.3f}"},
            )
            highest = seasonality.nlargest(3, "seasonal_index")
            lowest = seasonality.nsmallest(3, "seasonal_index")
            st.caption(
                "Highest index: "
                + ", ".join(highest["month"].tolist())
                + " | Lowest index: "
                + ", ".join(lowest["month"].tolist())
            )

        st.subheader("Three-month forecast baseline")
        if len(monthly) < 24:
            st.info(
                f"The selected data contains {len(monthly)} observed months. "
                "At least 24 consecutive months are required; no forecast is shown."
            )
        else:
            try:
                forecast = three_month_forecast(
                    monthly.set_index("sale_month")["revenue"],
                    method="seasonal_naive",
                )
            except ValueError as exc:
                st.info(
                    "A forecast is unavailable for this selection: "
                    f"{exc}"
                )
            else:
                forecast_frame = pd.DataFrame(
                    {
                        "forecast_month": forecast["forecast_months"],
                        "estimated_revenue_inr": forecast["forecast_values"],
                        "label": [forecast["label"]] * 3,
                    }
                )
                forecast_card, method_card = st.columns([1.5, 1])
                with forecast_card:
                    forecast_frame["forecast_month"] = pd.to_datetime(
                        forecast_frame["forecast_month"]
                    ).dt.strftime("%b %Y")
                    forecast_frame = forecast_frame.rename(
                        columns={
                            "forecast_month": "Forecast month",
                            "estimated_revenue_inr": "Estimated revenue (INR)",
                            "label": "Status",
                        }
                    )
                    render_data_table(
                        forecast_frame,
                        formatters={
                            "Estimated revenue (INR)": lambda value: f"₹{value:,.2f}"
                        },
                    )
                with method_card:
                    mape = forecast["mape_pct"]
                    st.metric(
                        "Holdout MAPE",
                        f"{mape:.2f}%" if pd.notna(mape) else "N/A",
                    )
                    st.caption(
                        "Seasonal naive: each future month uses revenue from the "
                        "same calendar month in the prior year. MAPE uses the last "
                        "three known months as a holdout; zero actuals are excluded."
                    )
                st.caption(
                    "Every future value is an Estimate. This is a simple baseline, "
                    "not an advanced machine-learning forecast; advanced ML is "
                    "out of scope (BR-15 Won't)."
                )
