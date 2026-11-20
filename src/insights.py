"""Evidence-linked, filter-aware insight generation."""

from __future__ import annotations

import pandas as pd

from src.metrics import (
    calculate_category_metrics,
    calculate_customer_mix,
    calculate_kpis,
)
from src.stats import correlation_analysis


def _scope_text(filters: dict) -> str:
    parts = [
        f"{filters['start_date']} to {filters['end_date']}",
        f"region={filters.get('region') or 'all'}",
        f"stores={filters.get('store_ids') or 'all'}",
        f"category={filters.get('category') or 'all'}",
        f"channel={filters.get('channel') or 'all'}",
    ]
    return "; ".join(parts)


def generate_insights(df: pd.DataFrame, filters: dict) -> list[dict[str, str]]:
    """Generate concise cards only from calculated current-filter data."""
    if df.empty:
        return [{
            "group": "Sales",
            "title": "No matching sales",
            "observation": "No records satisfy the selected filter scope.",
            "evidence": "0 sales lines",
            "scope": _scope_text(filters),
            "tone": "warning",
            "caveat": "Adjust filters; no historical or unfiltered values are substituted.",
        }]

    kpis = calculate_kpis(df)
    scope = _scope_text(filters)
    insights = [{
        "group": "Sales",
        "title": "Selected-period revenue",
        "observation": f"Revenue is ₹{kpis['revenue']:,.2f} across {kpis['units']:,.0f} units.",
        "evidence": f"{kpis['order_count']} distinct orders; AOV ₹{kpis['aov']:,.2f}",
        "scope": scope,
        "tone": "info",
        "caveat": "Revenue follows the active filters and excludes customer-level detail.",
    }]

    categories = calculate_category_metrics(df)
    if not categories.empty:
        top = categories.sort_values("revenue", ascending=False).iloc[0]
        lowest = categories.sort_values("profit").iloc[0]
        insights.append({
            "group": "Profitability",
            "title": "Category contribution",
            "observation": f"{top['category']} has the highest revenue at ₹{top['revenue']:,.2f}.",
            "evidence": f"Weighted margin {top['margin_pct']:.2f}%; profit ₹{top['profit']:,.2f}",
            "scope": scope,
            "tone": "success",
            "caveat": "Weighted margin is total profit divided by total revenue.",
        })
        insights.append({
            "group": "Profitability",
            "title": "Lowest profit category",
            "observation": f"{lowest['category']} has profit ₹{lowest['profit']:,.2f}.",
            "evidence": f"Margin {lowest['margin_pct']:.2f}%",
            "scope": scope,
            "tone": "warning" if lowest["profit"] < 0 or lowest["margin_pct"] < 10 else "info",
            "caveat": "A low result is descriptive and does not establish a causal cause.",
        })

    if "store_name" in df:
        top_store = df.groupby("store_name", as_index=False).agg(revenue=("revenue", "sum"))
        top_store = top_store.sort_values("revenue", ascending=False).iloc[0]
        insights.append({
            "group": "Stores",
            "title": "Leading store",
            "observation": f"{top_store['store_name']} leads this scope at ₹{top_store['revenue']:,.2f} revenue.",
            "evidence": f"Store revenue ₹{top_store['revenue']:,.2f}",
            "scope": scope,
            "tone": "success",
            "caveat": "This is selected-data ranking, not a prediction or guaranteed outcome.",
        })

    customer_mix = calculate_customer_mix(df)
    repeat_revenue = customer_mix.loc[
        customer_mix["repeat_status"] == "Repeat", "revenue"
    ].sum()
    repeat_share = repeat_revenue / kpis["revenue"] * 100 if kpis["revenue"] else 0
    insights.append({
        "group": "Customers",
        "title": "Repeat-customer contribution",
        "observation": f"Repeat customers contribute ₹{repeat_revenue:,.2f}, or {repeat_share:.2f}% of revenue.",
        "evidence": f"Repeat revenue {repeat_revenue:.2f}; total revenue {kpis['revenue']:.2f}",
        "scope": scope,
        "tone": "info",
        "caveat": "Repeat means at least two distinct orders in the selected period.",
    })

    correlations = correlation_analysis(df, method="pearson")
    if not correlations.empty:
        row = correlations.iloc[0]
        insights.append({
            "group": "Statistical Evidence",
            "title": f"{row['pair']} association",
            "observation": row["interpretation"],
            "evidence": f"Coefficient {row['coefficient']:.3f}; p-value {row['p_value']:.3f}; n={row['sample_size']}",
            "scope": scope,
            "tone": "warning",
            "caveat": "Correlation is not causation; confounding variables may affect both measures.",
        })
    return insights
