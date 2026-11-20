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
