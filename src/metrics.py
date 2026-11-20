"""Business measures and descriptive aggregations for sales analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


DISCOUNT_BANDS = ("0%", "1-10%", "11-20%", ">20%")
PAYMENT_MODES = ("Cash", "Card", "UPI", "Wallet")
CHANNELS = ("In-store", "Online")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df:
        raise ValueError(f"Required column is missing: {column}")
    return pd.to_numeric(df[column], errors="coerce").fillna(0)


def _revenue_series(df: pd.DataFrame) -> pd.Series:
    if "revenue" in df:
        return _numeric_series(df, "revenue")
    return _numeric_series(df, "quantity") * _numeric_series(df, "selling_unit_price")


def _profit_series(df: pd.DataFrame) -> pd.Series:
    if "profit" in df:
        return _numeric_series(df, "profit")
    if "cost_amount" in df:
        return _revenue_series(df) - _numeric_series(df, "cost_amount")
    return _numeric_series(df, "quantity") * (
        _numeric_series(df, "selling_unit_price") - _numeric_series(df, "cost_price")
    )


def _cost_series(df: pd.DataFrame) -> pd.Series:
    if "cost_amount" in df:
        return _numeric_series(df, "cost_amount")
    return _numeric_series(df, "quantity") * _numeric_series(df, "cost_price")


def _month_series(df: pd.DataFrame) -> pd.Series:
    if "sale_month" in df:
        values = pd.to_datetime(df["sale_month"], errors="coerce")
    elif "sale_date" in df:
        values = pd.to_datetime(df["sale_date"], errors="coerce")
    else:
        raise ValueError("A sale_month or sale_date column is required")
    return values.dt.to_period("M").dt.to_timestamp()


def _margin_pct(profit: pd.Series, revenue: pd.Series) -> float:
    total_revenue = float(revenue.sum())
    return float(profit.sum() / total_revenue * 100) if total_revenue else 0.0


def calculate_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Calculate revenue, profit, units, distinct orders, AOV and weighted margin."""
    revenue = _revenue_series(df)
    profit = _profit_series(df)
    units = float(_numeric_series(df, "quantity").sum())
    order_count = int(df["order_id"].nunique(dropna=True)) if "order_id" in df else 0
    revenue_total = float(revenue.sum())
    return {
        "revenue": revenue_total,
        "profit": float(profit.sum()),
        "units": int(units) if units.is_integer() else units,
        "order_count": order_count,
        "aov": revenue_total / order_count if order_count else 0.0,
        "margin_pct": _margin_pct(profit, revenue),
    }


def calculate_category_metrics(
    df: pd.DataFrame, group_by: str | list[str] = "category"
) -> pd.DataFrame:
    """Aggregate category profitability and weighted margin, with risk flags."""
    group_columns = [group_by] if isinstance(group_by, str) else list(group_by)
    missing = [column for column in group_columns if column not in df]
    if missing:
        raise ValueError(f"Grouping columns are missing: {', '.join(missing)}")
    frame = df[group_columns].copy()
    frame["revenue"] = _revenue_series(df)
    frame["cost_amount"] = _cost_series(df)
    frame["profit"] = _profit_series(df)
    result = frame.groupby(group_columns, dropna=False, as_index=False).agg(
        revenue=("revenue", "sum"),
        cost_amount=("cost_amount", "sum"),
        profit=("profit", "sum"),
    )
    result["margin_pct"] = np.where(
        result["revenue"].ne(0), result["profit"] / result["revenue"] * 100, 0.0
    )
    result["is_low_margin"] = result["margin_pct"] < 10
    result["is_loss_making"] = result["profit"] < 0
    return result


def rank_products(
    df: pd.DataFrame,
    metric: str,
    ascending: bool = False,
    limit: int | None = 10,
) -> pd.DataFrame:
    """Rank product aggregates with BRL-12 tie-breaks (other measure, then name)."""
    if metric not in {"revenue", "quantity", "units"}:
        raise ValueError("metric must be 'revenue', 'quantity', or 'units'")
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")
    units_column = "quantity" if "quantity" in df else "units"
    if units_column not in df:
        raise ValueError("Required column is missing: quantity or units")
    if "product_name" not in df:
        raise ValueError("Required column is missing: product_name")

    frame = df.copy()
    if "revenue" not in frame:
        frame["revenue"] = _revenue_series(frame)
    if units_column != "quantity":
        frame["quantity"] = _numeric_series(frame, units_column)
    group_columns = [
        column for column in ("product_id", "product_name") if column in frame
    ]
    if "product_name" not in group_columns:
        group_columns = ["product_name"]
    ranked = frame.groupby(group_columns, dropna=False, as_index=False).agg(
        revenue=("revenue", "sum"),
        quantity=("quantity", "sum"),
    )

    primary = "quantity" if metric in {"quantity", "units"} else "revenue"
    secondary = "revenue" if primary == "quantity" else "quantity"
    ranked = ranked.sort_values(
        [primary, secondary, "product_name"],
        ascending=[ascending, False, True],
        kind="mergesort",
    )
    if limit is not None:
        ranked = ranked.head(limit)
    return ranked.reset_index(drop=True)


def calculate_store_target_attainment(
    sales: pd.DataFrame, targets: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate actuals to store-month and join a single target record per key."""
    if "store_id" not in sales or "store_id" not in targets:
        raise ValueError("Both inputs must contain store_id")
    month_column = "sale_month" if "sale_month" in sales else "sale_date"
    if month_column not in sales or "target_month" not in targets:
        raise ValueError("Sales and targets must contain month columns")
    actuals = pd.DataFrame(
        {
            "store_id": sales["store_id"],
            "sale_month": _month_series(sales),
            "actual": _revenue_series(sales),
        }
    ).groupby(["store_id", "sale_month"], as_index=False, dropna=False)["actual"].sum()
    target_frame = targets[["store_id", "target_month", "target_revenue"]].copy()
    target_frame["sale_month"] = pd.to_datetime(
        target_frame.pop("target_month"), errors="coerce"
    ).dt.to_period("M").dt.to_timestamp()
    target_frame["target_revenue"] = pd.to_numeric(
        target_frame["target_revenue"], errors="coerce"
    )
    if target_frame.duplicated(["store_id", "sale_month"]).any():
        raise ValueError("Targets must contain at most one row per store-month")

    if target_frame.empty:
        result = actuals.assign(target_revenue=np.nan)
    else:
        result = target_frame.merge(
            actuals, on=["store_id", "sale_month"], how="left", validate="one_to_one"
        )
        result["actual"] = result["actual"].fillna(0.0)
    result = result.rename(columns={"target_revenue": "target"})
    result["variance"] = result["actual"] - result["target"]
    result["achievement_pct"] = np.where(
        result["target"].notna() & result["target"].ne(0),
        result["actual"] / result["target"] * 100,
        np.nan,
    )
    return result.sort_values(["store_id", "sale_month"]).reset_index(drop=True)


def calculate_region_target_attainment(
    store_results: pd.DataFrame, stores: pd.DataFrame
) -> pd.DataFrame:
    """Calculate region achievement as total actual divided by total target."""
    if "store_id" not in store_results or not {"store_id", "region"}.issubset(stores):
        raise ValueError("Store results need store_id and stores need store_id, region")
    store_columns = ["store_id", "region"]
    if stores["store_id"].duplicated().any():
        raise ValueError("stores must contain one row per store_id")
    frame = store_results.merge(stores[store_columns], on="store_id", how="left", validate="many_to_one")
    if frame["region"].isna().any():
        raise ValueError("Every store result must match a store region")
    result = frame.groupby(["region", "sale_month"], as_index=False, dropna=False).agg(
        actual=("actual", "sum"),
        target=("target", "sum"),
    )
    result["variance"] = result["actual"] - result["target"]
    result["achievement_pct"] = np.where(
        result["target"].ne(0), result["actual"] / result["target"] * 100, np.nan
    )
    return result.sort_values(["region", "sale_month"]).reset_index(drop=True)


def _discount_band(discount: pd.Series) -> pd.Series:
    return pd.cut(
        discount,
        bins=[-np.inf, 0, 10, 20, np.inf],
        labels=DISCOUNT_BANDS,
        right=True,
        include_lowest=True,
    )


def calculate_discount_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize units, revenue, profit and weighted margin by BRL-07 band."""
    frame = pd.DataFrame(
        {
            "discount_band": _discount_band(_numeric_series(df, "discount_pct")),
            "units": _numeric_series(df, "quantity"),
            "revenue": _revenue_series(df),
            "profit": _profit_series(df),
        }
    )
    result = frame.groupby("discount_band", observed=False, as_index=False).agg(
        units=("units", "sum"), revenue=("revenue", "sum"), profit=("profit", "sum")
    )
    result["margin_pct"] = np.where(
        result["revenue"].ne(0), result["profit"] / result["revenue"] * 100, 0.0
    )
    return result


def calculate_customer_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize segment and repeat/one-time revenue without returning customer IDs."""
    required = {"customer_id", "order_id", "segment"}
    if not required.issubset(df.columns):
        raise ValueError(f"Required columns are missing: {', '.join(sorted(required - set(df.columns)))}")
    frame = df[["customer_id", "order_id", "segment"]].copy()
    frame["revenue"] = _revenue_series(df)
    order_counts = frame.groupby("customer_id", dropna=False)["order_id"].nunique()
    frame["repeat_status"] = np.where(
        frame["customer_id"].map(order_counts).ge(2), "Repeat", "One-time"
    )
    result = frame.groupby(["segment", "repeat_status"], as_index=False, dropna=False).agg(
        revenue=("revenue", "sum"),
        customer_count=("customer_id", "nunique"),
        order_count=("order_id", "nunique"),
    )
    total_revenue = float(result["revenue"].sum())
    result["revenue_share_pct"] = (
        result["revenue"] / total_revenue * 100 if total_revenue else 0.0
    )
    return result


def _mix_by_month(
    df: pd.DataFrame, dimension: str, categories: tuple[str, ...]
) -> pd.DataFrame:
    output_columns = ["sale_month", dimension, "transaction_count", "revenue", "share_pct"]
    if df.empty:
        return pd.DataFrame(columns=output_columns)
    if dimension not in df:
        raise ValueError(f"Required column is missing: {dimension}")
    frame = pd.DataFrame(
        {
            "sale_month": _month_series(df),
            dimension: df[dimension],
            "revenue": _revenue_series(df),
        }
    )
    summary = frame.groupby(["sale_month", dimension], as_index=False, dropna=False).agg(
        transaction_count=("revenue", "size"), revenue=("revenue", "sum")
    )
    months = summary["sale_month"].dropna().drop_duplicates()
    grid = pd.MultiIndex.from_product(
        [months, categories], names=["sale_month", dimension]
    ).to_frame(index=False)
    summary = grid.merge(summary, on=["sale_month", dimension], how="left")
    summary[["transaction_count", "revenue"]] = summary[
        ["transaction_count", "revenue"]
    ].fillna(0)
    monthly_total = summary.groupby("sale_month")["revenue"].transform("sum")
    summary["share_pct"] = np.where(
        monthly_total.ne(0), summary["revenue"] / monthly_total * 100, 0.0
    )
    return summary[output_columns].sort_values(
        ["sale_month", dimension]
    ).reset_index(drop=True)


def calculate_payment_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Return all payment modes and their monthly revenue shares."""
    return _mix_by_month(df, "payment_mode", PAYMENT_MODES)


def calculate_channel_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Return both channels and their monthly revenue shares."""
    return _mix_by_month(df, "channel", CHANNELS)


def calculate_weekday_month(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return revenue and unit summaries with all weekdays and calendar months."""
    dates = pd.to_datetime(df["sale_date"], errors="coerce")
    base = pd.DataFrame(
        {
            "weekday": dates.dt.dayofweek.map(dict(enumerate(WEEKDAYS))),
            "month": dates.dt.month.map(dict(enumerate(MONTHS, start=1))),
            "revenue": _revenue_series(df),
            "quantity": _numeric_series(df, "quantity"),
        }
    )
    weekday = base.groupby("weekday", as_index=False, dropna=False).agg(
        revenue=("revenue", "sum"), quantity=("quantity", "sum")
    )
    weekday = pd.DataFrame({"weekday": WEEKDAYS}).merge(
        weekday, on="weekday", how="left"
    )
    month = base.groupby("month", as_index=False, dropna=False).agg(
        revenue=("revenue", "sum"), quantity=("quantity", "sum")
    )
    month = pd.DataFrame({"month": MONTHS}).merge(month, on="month", how="left")
    for frame in (weekday, month):
        frame[["revenue", "quantity"]] = frame[["revenue", "quantity"]].fillna(0)
    return {"weekday": weekday, "month": month}


def calculate_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue and profit by calendar month."""
    frame = pd.DataFrame(
        {
            "sale_month": _month_series(df),
            "revenue": _revenue_series(df),
            "profit": _profit_series(df),
        }
    )
    result = frame.groupby("sale_month", as_index=False).agg(
        revenue=("revenue", "sum"), profit=("profit", "sum")
    )
    return result.sort_values("sale_month").reset_index(drop=True)


def calculate_seasonal_index(monthly: pd.DataFrame) -> pd.DataFrame:
    """Calculate calendar-month indices relative to the average monthly revenue."""
    if "revenue" not in monthly:
        raise ValueError("monthly must contain revenue")
    frame = monthly.copy()
    if "sale_month" in frame:
        months = pd.to_datetime(frame["sale_month"], errors="coerce")
    elif isinstance(frame.index, pd.DatetimeIndex):
        months = pd.Series(frame.index, index=frame.index)
    else:
        raise ValueError("monthly must have a sale_month column or datetime index")
    frame["calendar_month"] = months.dt.month
    overall_average = pd.to_numeric(frame["revenue"], errors="coerce").mean()
    grouped = frame.groupby("calendar_month")["revenue"].mean()
    values = [
        float(grouped.get(month, 0) / overall_average) if overall_average else 0.0
        for month in range(1, 13)
    ]
    return pd.DataFrame(
        {"month": MONTHS, "seasonal_index": values}
    )


def calculate_equal_period_comparison(
    df: pd.DataFrame, start_date, end_date
) -> dict[str, object]:
    """Compare selected-date KPIs with the immediately preceding equal-length period."""
    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()
    if end < start:
        raise ValueError("end_date must not be before start_date")
    dates = pd.to_datetime(df["sale_date"], errors="coerce").dt.normalize()
    selected = df.loc[dates.between(start, end)]
    duration = end - start + pd.Timedelta(days=1)
    previous_start = start - duration
    previous_end = start - pd.Timedelta(days=1)
    previous = df.loc[dates.between(previous_start, previous_end)]
    current_kpis = calculate_kpis(selected)
    previous_kpis = calculate_kpis(previous)
    changes = {}
    for key, current_value in current_kpis.items():
        previous_value = previous_kpis[key]
        changes[key] = {
            "absolute_change": current_value - previous_value,
            "pct_change": (
                (current_value - previous_value) / abs(previous_value) * 100
                if previous_value
                else np.nan
            ),
        }
    return {
        "current": current_kpis,
        "previous": previous_kpis,
        "previous_start": previous_start.date(),
        "previous_end": previous_end.date(),
        "changes": changes,
    }
