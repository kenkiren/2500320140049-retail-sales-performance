"""In-memory privacy-safe exports for filtered aggregate views."""

from io import BytesIO

import pandas as pd


_FORBIDDEN_COLUMNS = {
    "customer_id", "customer_name", "phone", "phone_number",
    "email", "address", "street_address",
}


def build_safe_aggregate(filtered: pd.DataFrame) -> pd.DataFrame:
    """Build a category-level aggregate; customer identifiers are never retained."""
    if filtered.empty:
        return pd.DataFrame(
            columns=["category", "revenue", "cost_amount", "profit", "margin_pct"]
        )
    frame = filtered.copy()
    frame["revenue"] = pd.to_numeric(frame["quantity"], errors="coerce").fillna(0) * pd.to_numeric(
        frame["selling_unit_price"], errors="coerce"
    ).fillna(0)
    frame["cost_amount"] = pd.to_numeric(frame["quantity"], errors="coerce").fillna(0) * pd.to_numeric(
        frame["cost_price"], errors="coerce"
    ).fillna(0)
    frame["profit"] = frame["revenue"] - frame["cost_amount"]
    result = frame.groupby("category", as_index=False).agg(
        revenue=("revenue", "sum"),
        cost_amount=("cost_amount", "sum"),
        profit=("profit", "sum"),
    )
    result["margin_pct"] = (
        result["profit"] / result["revenue"] * 100
    ).where(result["revenue"].ne(0), 0)
    return result[
        ["category", "revenue", "cost_amount", "profit", "margin_pct"]
    ].sort_values("category").reset_index(drop=True)


def export_preview_csv(preview: pd.DataFrame) -> bytes:
    """Serialize exactly the supplied preview table with no forbidden fields."""
    forbidden = set(preview.columns.str.lower()).intersection(_FORBIDDEN_COLUMNS)
    if forbidden:
        raise ValueError(f"Forbidden identifiers cannot be exported: {sorted(forbidden)}")
    return preview.to_csv(index=False).encode("utf-8")
