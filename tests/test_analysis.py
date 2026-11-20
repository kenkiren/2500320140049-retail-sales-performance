"""Business KPI and statistical-method tests using tiny independent fixtures.

Step 15 implementation contract:
- src.metrics.calculate_kpis(df) -> dict with revenue, profit, units, order_count,
  aov and margin_pct.
- Other src.metrics functions return pandas DataFrames unless stated.
- src.stats functions return dictionaries containing the result fields asserted below.
"""
from __future__ import annotations

from datetime import date
import numpy as np
import pandas as pd
import pytest

metrics = pytest.importorskip("src.metrics")
stats = pytest.importorskip("src.stats")


@pytest.fixture
def tiny_sales() -> pd.DataFrame:
    df = pd.DataFrame([
        # line, order, date, store, product, customer, qty, list, disc, sell, cost, payment, channel, category, subcat, segment
        [1, "O-1", "2025-01-01", 1, 101, 1, 2, 100.00, 0.0, 100.00, 60.00, "Cash", "In-store", "Home", "Decor", "Budget"],
        [2, "O-1", "2025-01-01", 1, 102, 1, 1, 100.00, 10.0, 90.00, 60.00, "Card", "Online", "Home", "Decor", "Budget"],
        [3, "O-2", "2025-01-02", 2, 103, 2, 3, 62.50, 20.0, 50.00, 40.00, "UPI", "In-store", "Apparel", "Basics", "Premium"],
        [4, "O-3", "2025-01-03", 2, 104, 3, 1, 100.00, 0.0, 100.00, 120.00, "Wallet", "Online", "Apparel", "Basics", "Regular"],
    ], columns=[
        "line_id","order_id","sale_date","store_id","product_id","customer_id",
        "quantity","list_unit_price","discount_pct","selling_unit_price","cost_price",
        "payment_mode","channel","category","sub_category","segment",
    ])
    df["revenue"] = df["quantity"] * df["selling_unit_price"]
    df["cost_amount"] = df["quantity"] * df["cost_price"]
    df["profit"] = df["revenue"] - df["cost_amount"]
    df["margin_pct"] = np.where(df["revenue"] == 0, np.nan, 100 * df["profit"] / df["revenue"])
    df["sale_month"] = "2025-01-01"
    df["sale_weekday"] = pd.to_datetime(df["sale_date"]).dt.day_name()
    df["region"] = "North"
    return df


def test_t13_kpis_match_independent_hand_calculation(tiny_sales):
    result = metrics.calculate_kpis(tiny_sales)
    assert result["revenue"] == pytest.approx(540.00)
    assert result["profit"] == pytest.approx(120.00)
    assert result["units"] == 7
    assert result["order_count"] == 3
    assert result["aov"] == pytest.approx(180.00)
    assert result["margin_pct"] == pytest.approx(100 * 120 / 540, abs=0.001)


def test_t14_category_profitability_uses_weighted_margin_and_reconciles(tiny_sales):
    result = metrics.calculate_category_metrics(tiny_sales)
    assert {"category","revenue","cost_amount","profit","margin_pct","is_low_margin","is_loss_making"}.issubset(result.columns)
    assert result["revenue"].sum() == pytest.approx(540.00)
    assert result["profit"].sum() == pytest.approx(120.00)
    apparel = result.loc[result["category"] == "Apparel"].iloc[0]
    assert apparel["margin_pct"] == pytest.approx(4.0)
    assert bool(apparel["is_low_margin"]) is True


def test_t15_forecast_returns_three_estimates_and_meets_brd_backtest_target():
    # The TRD permits a simple seasonal-naive baseline or rolling mean.
    # Step 8's 3-month moving-average note must be reconciled: on Step 10 data,
    # a recursive 3-month moving average has ~25.99% MAPE for Oct-Dec 2025,
    # while the same-month-prior-year seasonal-naive baseline has ~1.92%.
    # This test requires the BRD target <=15%; it does not permit advanced ML.
    monthly = pd.Series(
        [100, 90, 110, 120, 95, 105, 130, 140, 115, 150, 160, 170,
         105, 95, 115, 125, 100, 110, 135, 145, 120, 155, 165, 175],
        index=pd.date_range("2024-01-01", periods=24, freq="MS"),
        dtype=float,
    )
    result = stats.three_month_forecast(monthly, method="seasonal_naive")
    assert len(result["forecast_values"]) == 3
    assert len(result["forecast_months"]) == 3
    assert "estimate" in str(result["label"]).lower()
    assert result["mape_pct"] <= 15.0
    assert "machine" not in str(result["method"]).lower()


def test_t16_product_rank_ties_follow_brl12_other_measure_then_name():
    products = pd.DataFrame([
        {"product_id": 1, "product_name": "Alpha", "revenue": 100.0, "quantity": 5},
        {"product_id": 2, "product_name": "Zulu", "revenue": 100.0, "quantity": 8},
        {"product_id": 3, "product_name": "Beta", "revenue": 100.0, "quantity": 8},
    ])
    ranked = metrics.rank_products(products, metric="revenue", ascending=False, limit=10)
    assert ranked["product_name"].tolist() == ["Beta", "Zulu", "Alpha"]


def test_t17_store_and_region_target_attainment_are_weighted(tiny_sales):
    targets = pd.DataFrame([
        {"store_id": 1, "target_month": "2025-01-01", "target_revenue": 200.0},
        {"store_id": 2, "target_month": "2025-01-01", "target_revenue": 500.0},
    ])
    stores = pd.DataFrame([
        {"store_id": 1, "region": "North"},
        {"store_id": 2, "region": "North"},
    ])
    store_result = metrics.calculate_store_target_attainment(tiny_sales, targets)
    assert store_result["achievement_pct"].tolist() == pytest.approx([145.0, 50.0])
    region_result = metrics.calculate_region_target_attainment(store_result, stores)
    north = region_result.loc[region_result["region"] == "North"].iloc[0]
    assert north["achievement_pct"] == pytest.approx(540 / 700 * 100)
    assert north["achievement_pct"] != pytest.approx(store_result["achievement_pct"].mean())


def test_t18_discount_band_boundaries_match_brl07(tiny_sales):
    frame = pd.DataFrame({
        "discount_pct": [0, 10, 11, 20, 20.01],
        "quantity": [1, 1, 1, 1, 1],
        "selling_unit_price": [100, 90, 89, 80, 79.99],
        "cost_price": [50, 50, 50, 50, 50],
    })
    result = metrics.calculate_discount_metrics(frame)
    labels = set(result["discount_band"])
    assert labels == {"0%", "1-10%", "11-20%", ">20%"}
    assert result["units"].sum() == 5


def test_t19_repeat_customer_uses_distinct_orders_in_selected_period():
    frame = pd.DataFrame([
        {"customer_id": 1, "order_id": "A", "revenue": 100, "segment": "Budget"},
        {"customer_id": 1, "order_id": "A", "revenue": 50, "segment": "Budget"},
        {"customer_id": 1, "order_id": "B", "revenue": 75, "segment": "Budget"},
        {"customer_id": 2, "order_id": "C", "revenue": 60, "segment": "Premium"},
    ])
    result = metrics.calculate_customer_mix(frame)
    repeat = result.loc[result["repeat_status"] == "Repeat", "revenue"].sum()
    one_time = result.loc[result["repeat_status"] == "One-time", "revenue"].sum()
    assert repeat == 225
    assert one_time == 60
    assert repeat + one_time == 285


def test_t20_customer_segment_shares_and_repeat_split_reconcile(tiny_sales):
    result = metrics.calculate_customer_mix(tiny_sales)
    assert result["revenue"].sum() == pytest.approx(540.0)
    assert result["revenue_share_pct"].sum() == pytest.approx(100.0)


def test_t21_payment_and_channel_mix_shares_reconcile_by_month(tiny_sales):
    payment = metrics.calculate_payment_mix(tiny_sales)
    channel = metrics.calculate_channel_mix(tiny_sales)
    assert payment.groupby("sale_month")["share_pct"].sum().eq(100.0).all()
    assert channel.groupby("sale_month")["share_pct"].sum().eq(100.0).all()
    assert set(payment["payment_mode"]) == {"Cash", "Card", "UPI", "Wallet"}
    assert set(channel["channel"]) == {"In-store", "Online"}


def test_t22_weekday_and_month_summary_zero_fills_full_calendar():
    result = metrics.calculate_weekday_month(pd.DataFrame({
        "sale_date": ["2025-01-06", "2025-01-08"],
        "revenue": [100.0, 200.0],
        "quantity": [1, 2],
    }))
    assert len(result["weekday"]) == 7
    assert len(result["month"]) == 12
    assert (result["weekday"]["revenue"] >= 0).all()
    assert (result["month"]["revenue"] >= 0).all()


def test_t23_welch_test_reports_n_statistic_pvalue_and_five_percent_verdict():
    a = np.array([100 + i * 0.2 for i in range(30)], dtype=float)
    b = np.array([130 + i * 0.2 for i in range(30)], dtype=float)
    result = stats.welch_aov_test(a, b)
    assert result["n_a"] == 30 and result["n_b"] == 30
    assert np.isfinite(result["t_statistic"])
    assert 0 <= result["p_value"] <= 1
    assert result["significant_5pct"] is True
    assert result["verdict"]


def test_t24_one_way_anova_reports_groups_assumptions_and_interpretation():
    groups = {
        "North": [100 + i for i in range(30)],
        "South": [140 + i for i in range(30)],
        "West": [180 + i for i in range(30)],
    }
    result = stats.one_way_anova(groups)
    assert result["group_sizes"] == {"North": 30, "South": 30, "West": 30}
    assert np.isfinite(result["f_statistic"])
    assert 0 <= result["p_value"] <= 1
    assert result["assumption_checks"]
    assert result["interpretation"]


def test_t25_correlation_reports_coefficients_pvalues_sample_size_and_caveat():
    x = np.arange(1, 61, dtype=float)
    frame = pd.DataFrame({
        "discount_pct": x,
        "quantity": 2 * x + (x % 3),
        "profit": 500 - 3 * x + (x % 4),
    })
    result = stats.correlation_analysis(frame, method="pearson")
    assert {"variable_x","variable_y","coefficient","p_value","sample_size","strength","interpretation"}.issubset(result.columns)
    assert set(result["sample_size"]) == {60}
    assert result["p_value"].between(0, 1).all()
    assert result["interpretation"].str.contains("causation", case=False).any()


def test_t26_groups_below_30_are_flagged_unreliable():
    result = stats.welch_aov_test([1, 2, 3, 4, 5], list(range(30, 70)))
    assert result["unreliable"] is True
    assert result["n_a"] == 5


def test_t27_global_filter_helper_applies_all_five_dimensions(tiny_sales):
    ui = pytest.importorskip("src.ui")
    frame = tiny_sales.copy()
    frame.loc[0, "sale_date"] = "2025-01-01"
    frame.loc[1, "sale_date"] = "2025-01-02"
    filters = {
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 1, 3),
        "region": "North",
        "store_ids": [1],
        "category": "Home",
        "channel": "In-store",
    }
    result = ui.apply_global_filters(frame, filters)
    assert result["line_id"].tolist() == [1]
