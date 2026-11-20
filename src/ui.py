"""
Reusable UI helpers for Retail Sales Performance Analysis.

Compatible with the project's pinned Streamlit 1.40.2:
- Uses streamlit.components.v1.html as the iframe HTML fallback.
- Uses st.iframe automatically when the project upgrades to Streamlit >= 1.56.
- Tailwind CDN styles only the decorative header/KPI/insight cards.
- Interactive filters and Plotly charts remain native Streamlit components.
"""
from __future__ import annotations

from datetime import date
from html import escape
from typing import Any, Iterable

import pandas as pd
import streamlit as st

from src.db import load_analysis_data

try:
    # Streamlit 1.40.2-compatible API.
    from streamlit.components.v1 import html as _legacy_iframe_html
except ImportError:  # pragma: no cover - defensive fallback
    _legacy_iframe_html = None


TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'

_FALLBACK_CSS = """
<style>
  html, body { margin:0; padding:0; background:transparent;
    font-family: Inter, 'Segoe UI', Arial, sans-serif; color:#142B4A; }
  .rs-wrap { box-sizing:border-box; width:100%; padding:10px 2px; }
  .rs-header { background:#17365D; color:#fff; border-radius:14px;
    padding:18px 20px; border-left:5px solid #0F766E; }
  .rs-title { margin:0; font-size:22px; font-weight:750; line-height:1.2; }
  .rs-subtitle { margin:6px 0 0; color:#DCE8F5; font-size:12px; }
  .rs-kpi { background:#fff; border:1px solid #E2E8F0; border-radius:12px;
    padding:14px 15px; min-height:94px; box-shadow:0 1px 3px rgba(15,23,42,.06); }
  .rs-label { color:#64748B; font-size:11px; font-weight:650; letter-spacing:.04em;
    text-transform:uppercase; }
  .rs-value { color:#142B4A; font-size:24px; font-weight:750; margin-top:7px; }
  .rs-delta { color:#0F766E; font-size:11px; margin-top:4px; }
  .rs-insight { border-radius:12px; padding:13px 15px; border:1px solid #BFDBFE;
    background:#EFF6FF; color:#17365D; }
  .rs-insight.warning { border-color:#FDE68A; background:#FFFBEB; color:#92400E; }
  .rs-insight.success { border-color:#99F6E4; background:#F0FDFA; color:#115E59; }
  .rs-insight-title { font-weight:750; font-size:13px; margin:0 0 5px; }
  .rs-insight-body { font-size:12px; line-height:1.5; margin:0; }
</style>
"""


@st.cache_data(show_spinner="Loading sales analysis data...")
def load_analysis_data_cached() -> pd.DataFrame:
    """Cache the canonical read-only analysis view across page reruns."""
    return load_analysis_data()


def render_analysis_filters(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Render the common five filters using choices present in the dataset."""
    dates = pd.to_datetime(dataframe["sale_date"], errors="coerce").dropna()
    if dates.empty:
        raise ValueError("The analysis dataset contains no valid sale dates")
    store_columns = ["store_id", "store_name", "region"]
    stores = dataframe[store_columns].drop_duplicates("store_id").to_dict("records")
    return render_global_filters(
        date_min=dates.min().date(),
        date_max=dates.max().date(),
        regions=sorted(dataframe["region"].dropna().unique().tolist()),
        stores=stores,
        categories=sorted(dataframe["category"].dropna().unique().tolist()),
        channels=("In-store", "Online"),
    )


def _render_trusted_html(markup: str, height: int, accessible_name: str) -> None:
    """Render authored HTML. Never pass untrusted database/user HTML here."""
    iframe = getattr(st, "iframe", None)
    if callable(iframe):
        # st.iframe was introduced after the project's pinned Streamlit 1.40.2.
        # The optional alt argument arrived later, so support both signatures.
        try:
            iframe(markup, width="stretch", height=height, alt=accessible_name)
        except TypeError:
            iframe(markup, width="stretch", height=height)
    elif _legacy_iframe_html is not None:
        _legacy_iframe_html(markup, height=height, scrolling=False)
    else:
        # Last-resort native fallback if neither iframe API is available.
        st.info("Decorative HTML component is unavailable; using native Streamlit styling.")
        st.markdown(markup, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = "") -> None:
    """Render a decorative Tailwind header with a native text fallback."""
    safe_title = escape(str(title))
    safe_subtitle = escape(str(subtitle))
    markup = f"""
    {TAILWIND_CDN}
    {_FALLBACK_CSS}
    <div class="rs-wrap">
      <header class="rs-header rounded-xl px-5 py-4 text-white">
        <p class="rs-title text-xl font-bold">{safe_title}</p>
        <p class="rs-subtitle text-sm mt-1">{safe_subtitle}</p>
      </header>
    </div>
    """
    _render_trusted_html(markup, 112, f"{title} page header")


def render_kpi_card(
    label: str,
    value: Any,
    delta: str | None = None,
    helper: str = "",
) -> None:
    """Render one static KPI card. Values are escaped before HTML insertion."""
    safe_label = escape(str(label))
    safe_value = escape(str(value))
    safe_delta = escape(str(delta)) if delta is not None else ""
    safe_helper = escape(str(helper))
    delta_html = f'<p class="rs-delta text-xs mt-1">{safe_delta}</p>' if safe_delta else ""
    helper_html = (
        f'<p class="text-slate-500 text-xs mt-1">{safe_helper}</p>'
        if safe_helper else ""
    )
    markup = f"""
    {TAILWIND_CDN}
    {_FALLBACK_CSS}
    <div class="rs-wrap">
      <section class="rs-kpi rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <p class="rs-label text-xs font-semibold uppercase tracking-wide">{safe_label}</p>
        <p class="rs-value text-2xl font-bold mt-2">{safe_value}</p>
        {delta_html}
        {helper_html}
      </section>
    </div>
    """
    _render_trusted_html(markup, 126, f"{label} KPI card")


def render_chart_card(title: str, figure: Any, note: str = "") -> None:
    """Use native Streamlit for interactive Plotly charts."""
    with st.container(border=True):
        st.markdown(f"**{escape(str(title))}**")
        if note:
            st.caption(note)
        st.plotly_chart(figure, use_container_width=True)


def render_data_table(dataframe: pd.DataFrame, formatters=None) -> None:
    """Render a small, static, escaped HTML table without Arrow serialization."""
    formatters = formatters or {}
    headers = "".join(
        f"<th scope=\"col\">{escape(str(column))}</th>"
        for column in dataframe.columns
    )
    rows = []
    for row in dataframe.itertuples(index=False, name=None):
        cells = []
        for column, value in zip(dataframe.columns, row):
            if pd.isna(value):
                display = "—"
            elif column in formatters:
                display = str(formatters[column](value))
            elif isinstance(value, (date, pd.Timestamp)):
                display = value.strftime("%Y-%m-%d")
            elif isinstance(value, (int, float)):
                display = f"{value:,}" if isinstance(value, int) else f"{value:,.2f}"
            else:
                display = str(value)
            cells.append(f"<td>{escape(display)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    body = "".join(rows)
    st.markdown(
        f"<table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table>",
        unsafe_allow_html=True,
    )


def render_insight_box(
    title: str,
    body: str,
    tone: str = "info",
) -> None:
    """Render an explanatory insight; tone is limited to fixed safe styles."""
    tone_class = tone if tone in {"info", "warning", "success"} else "info"
    safe_title = escape(str(title))
    safe_body = escape(str(body))
    markup = f"""
    {TAILWIND_CDN}
    {_FALLBACK_CSS}
    <div class="rs-wrap">
      <section class="rs-insight {tone_class} rounded-xl border p-4">
        <p class="rs-insight-title font-semibold">{safe_title}</p>
        <p class="rs-insight-body text-sm">{safe_body}</p>
      </section>
    </div>
    """
    _render_trusted_html(markup, 112, f"{title} insight")


def _reset_store_selection() -> None:
    """Clear store selections when the selected region changes."""
    st.session_state["ui_global_stores"] = []


def reset_global_filters() -> None:
    """Reset filter state. Call from a Streamlit button callback."""
    for key in (
        "ui_global_date_range",
        "ui_global_region",
        "ui_global_stores",
        "ui_global_category",
        "ui_global_channel",
    ):
        st.session_state.pop(key, None)


def render_global_filters(
    date_min: date,
    date_max: date,
    regions: Iterable[str],
    stores: Iterable[dict[str, Any]],
    categories: Iterable[str],
    channels: Iterable[str] = ("In-store", "Online"),
) -> dict[str, Any]:
    """
    Render the shared sidebar filters and return a filter dictionary.

    `stores` must be an iterable of dicts with `store_id`, `store_name`, and
    `region`. Empty `store_ids` means all stores in the selected region.
    """
    region_values = sorted({str(x) for x in regions})
    category_values = sorted({str(x) for x in categories})
    channel_values = sorted({str(x) for x in channels})
    store_rows = list(stores)

    st.sidebar.markdown("### Global filters")
    st.sidebar.caption("Selections are shared across all pages.")

    # Keep existing date state within the available dataset range.
    default_range = (date_min, date_max)
    existing_range = st.session_state.get("ui_global_date_range", default_range)
    if not isinstance(existing_range, (tuple, list)) or len(existing_range) != 2:
        existing_range = default_range
    safe_start = max(date_min, min(existing_range[0], date_max))
    safe_end = max(date_min, min(existing_range[1], date_max))
    if safe_start > safe_end:
        safe_start, safe_end = date_min, date_max
    st.session_state["ui_global_date_range"] = (safe_start, safe_end)

    selected_region = st.session_state.get("ui_global_region", "All regions")
    region_options = ["All regions"] + region_values
    if selected_region not in region_options:
        st.session_state["ui_global_region"] = "All regions"

    region = st.sidebar.selectbox(
        "Region",
        region_options,
        key="ui_global_region",
        on_change=_reset_store_selection,
    )

    if region == "All regions":
        available_stores = store_rows
    else:
        available_stores = [s for s in store_rows if str(s.get("region")) == region]
    store_label_to_id = {
        f"{s.get('store_name', 'Store')} (ID {s.get('store_id')})": s.get("store_id")
        for s in available_stores
    }
    allowed_labels = set(store_label_to_id)
    old_store_labels = st.session_state.get("ui_global_stores", [])
    st.session_state["ui_global_stores"] = [
        x for x in old_store_labels if x in allowed_labels
    ]

    date_range = st.sidebar.date_input(
        "Date range",
        min_value=date_min,
        max_value=date_max,
        key="ui_global_date_range",
    )
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    elif isinstance(date_range, date):
        start_date = end_date = date_range
    else:
        start_date, end_date = date_min, date_max

    selected_store_labels = st.sidebar.multiselect(
        "Store (leave blank for all stores in region)",
        options=sorted(allowed_labels),
        key="ui_global_stores",
    )
    selected_store_ids = [store_label_to_id[x] for x in selected_store_labels]

    category_options = ["All categories"] + category_values
    if st.session_state.get("ui_global_category", "All categories") not in category_options:
        st.session_state["ui_global_category"] = "All categories"
    category = st.sidebar.selectbox(
        "Product category",
        category_options,
        key="ui_global_category",
    )

    channel_options = ["All channels"] + channel_values
    if st.session_state.get("ui_global_channel", "All channels") not in channel_options:
        st.session_state["ui_global_channel"] = "All channels"
    channel = st.sidebar.selectbox(
        "Sales channel",
        channel_options,
        key="ui_global_channel",
    )

    st.sidebar.button("Reset filters", on_click=reset_global_filters, use_container_width=True)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "region": None if region == "All regions" else region,
        "store_ids": selected_store_ids,
        "category": None if category == "All categories" else category,
        "channel": None if channel == "All channels" else channel,
    }


def apply_global_filters(dataframe, filters: dict[str, Any]):
    """
    Apply shared filters to a joined analysis DataFrame.

    Expected available columns when the corresponding filter is active:
    sale_date, region, store_id, category, channel.
    """
    result = dataframe.copy()
    if "sale_date" in result.columns:
        dates = __import__("pandas").to_datetime(result["sale_date"], errors="coerce").dt.date
        result = result.loc[
            dates.between(filters["start_date"], filters["end_date"])
        ]
    if filters.get("region") is not None and "region" in result.columns:
        result = result.loc[result["region"] == filters["region"]]
    if filters.get("store_ids") and "store_id" in result.columns:
        result = result.loc[result["store_id"].isin(filters["store_ids"])]
    if filters.get("category") is not None and "category" in result.columns:
        result = result.loc[result["category"] == filters["category"]]
    if filters.get("channel") is not None and "channel" in result.columns:
        result = result.loc[result["channel"] == filters["channel"]]
    return result
