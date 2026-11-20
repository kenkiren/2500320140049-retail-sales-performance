"""UI-05 — evidence-linked filter-aware narratives."""

import streamlit as st

from src.insights import generate_insights
from src.ui import (
    apply_global_filters,
    load_analysis_data_cached,
    render_analysis_filters,
    render_insight_box,
    render_page_header,
)


st.set_page_config(page_title="Insights", layout="wide")
analysis_data = load_analysis_data_cached()
filters = render_analysis_filters(analysis_data)
filtered = apply_global_filters(analysis_data, filters)
render_page_header("Insights", "Calculated observations with supporting measures and caveats")

cards = generate_insights(filtered, filters)
if len(cards) == 1 and cards[0]["title"] == "No matching sales":
    render_insight_box(
        cards[0]["title"],
        cards[0]["observation"] + " " + cards[0]["caveat"],
        tone="warning",
    )
else:
    groups = ["Sales", "Profitability", "Stores", "Customers", "Statistical Evidence"]
    for group in groups:
        group_cards = [card for card in cards if card["group"] == group]
        if not group_cards:
            continue
        st.subheader(group)
        for card in group_cards:
            body = (
                f"{card['observation']}\n\n"
                f"Evidence: {card['evidence']}\n"
                f"Scope: {card['scope']}\n"
                f"Limitation: {card['caveat']}"
            )
            render_insight_box(card["title"], body, tone=card["tone"])
