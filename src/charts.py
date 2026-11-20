"""Reusable native Plotly figures for the analysis pages."""

import plotly.graph_objects as go


def monthly_trend_figure(monthly):
    """Create the revenue/profit monthly trend from a prepared metrics table."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=monthly["sale_month"],
            y=monthly["revenue"],
            name="Revenue",
            mode="lines+markers",
            line={"color": "#2563EB", "width": 3},
            hovertemplate="%{x|%b %Y}<br>Revenue: ₹%{y:,.2f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=monthly["sale_month"],
            y=monthly["profit"],
            name="Profit",
            mode="lines+markers",
            line={"color": "#0F766E", "width": 3},
            hovertemplate="%{x|%b %Y}<br>Profit: ₹%{y:,.2f}<extra></extra>",
        )
    )
    figure.update_layout(
        xaxis_title=None,
        yaxis_title="INR",
        hovermode="x unified",
        legend_title=None,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
    )
    return figure


def category_revenue_figure(categories):
    """Create a compact revenue ranking chart from category metric results."""
    ordered = categories.sort_values("revenue", ascending=True)
    figure = go.Figure(
        go.Bar(
            x=ordered["revenue"],
            y=ordered["category"],
            orientation="h",
            marker_color="#2563EB",
            hovertemplate="%{y}<br>Revenue: ₹%{x:,.2f}<extra></extra>",
        )
    )
    figure.update_layout(
        xaxis_title="Revenue (INR)",
        yaxis_title=None,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
    )
    return figure


def seasonal_index_figure(seasonality):
    """Create the 12-calendar-month seasonal-index chart."""
    figure = go.Figure(
        go.Bar(
            x=seasonality["month"],
            y=seasonality["seasonal_index"],
            marker_color="#0F766E",
            hovertemplate="%{x}<br>Index: %{y:.3f}<extra></extra>",
        )
    )
    figure.add_hline(y=1, line_dash="dash", line_color="#64748B")
    figure.update_layout(
        xaxis_title="Calendar month",
        yaxis_title="Index (1.0 = average month)",
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
    )
    return figure


def profitability_comparison_figure(metrics, dimension):
    """Compare revenue, cost and profit for a prepared business dimension."""
    figure = go.Figure()
    for column, color in (
        ("revenue", "#2563EB"),
        ("cost_amount", "#64748B"),
        ("profit", "#0F766E"),
    ):
        figure.add_trace(
            go.Bar(
                x=metrics[dimension],
                y=metrics[column],
                name=column.replace("_", " ").title(),
                marker_color=color,
                hovertemplate="%{x}<br>₹%{y:,.2f}<extra></extra>",
            )
        )
    figure.update_layout(
        barmode="group",
        xaxis_title=None,
        yaxis_title="INR",
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
    )
    return figure


def target_comparison_figure(store_results):
    """Compare filtered actual revenue with the corresponding monthly targets."""
    figure = go.Figure()
    for column, color in (("actual", "#2563EB"), ("target", "#94A3B8")):
        figure.add_trace(
            go.Bar(
                x=store_results["store_name"],
                y=store_results[column],
                name=column.title(),
                marker_color=color,
                hovertemplate="%{x}<br>₹%{y:,.2f}<extra></extra>",
            )
        )
    figure.update_layout(
        barmode="group",
        xaxis_title=None,
        yaxis_title="INR",
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
    )
    return figure


def scatter_figure(frame, x, y, color=None, title=None):
    """Create an optional scatter chart from prepared data."""
    figure = go.Figure()
    if color and color in frame:
        for value in frame[color].dropna().unique():
            subset = frame.loc[frame[color] == value]
            figure.add_trace(go.Scatter(
                x=subset[x], y=subset[y], mode="markers",
                name=str(value), opacity=0.65,
                hovertemplate=f"%{{x:.2f}}<br>%{{y:.2f}}<extra>{value}</extra>",
            ))
    else:
        figure.add_trace(go.Scatter(
            x=frame[x], y=frame[y], mode="markers", name=title or y,
            opacity=0.65,
        ))
    figure.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
    )
    return figure
