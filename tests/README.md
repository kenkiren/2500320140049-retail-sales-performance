# Step 13 — QA test suite

## Run

From the project root (Python 3.12 environment with the pinned `requirements.txt` installed):

```bash
python -m pytest -q tests/
python -m pytest --cov=src --cov-report=term-missing tests/
```

The target is **at least 80% coverage of data and KPI logic**, as required by BRD SC-03. AppTest tests are integration smoke tests; the final coverage report should include `src/` modules.

## Test files

- `test_data.py`: SQLite read-only access, exact Step 8 schema, release row counts, 38-column view, PK/FK integrity, value domains, Step 10 quality issue register, data loader and cleaning validation.
- `test_analysis.py`: hand-calculated tiny fixture for KPIs, weighted category margin, ranking tie-break, target attainment, discount bands, customer repeat classification, payment/channel shares, calendar zero-fill, forecast, Welch t-test, ANOVA, correlation and shared filters.
- `test_app.py`: Streamlit AppTest startup, all eight UI page smoke tests, page render timing and shared filter state.

## Step 15 implementation contract

These are the function names and return shapes assumed by the tests. Implement them in Step 15 or update the tests and RTM under change control.

| Module | Function | Expected return |
|---|---|---|
| `src.db` | `load_analysis_data(db_path=None)` | pandas DataFrame, 20,000 rows × 38 columns |
| `src.validation` | `validate_sales_lines(df)` | DataFrame with `issue_type`, `row_count` |
| `src.cleaning` | `clean_sales_lines(df)` | `(clean_dataframe, issue_report_dataframe)` |
| `src.metrics` | `calculate_kpis(df)` | dict: revenue, profit, units, order_count, aov, margin_pct |
| `src.metrics` | `calculate_category_metrics(df)` | DataFrame with revenue, cost_amount, profit, weighted margin_pct and flags |
| `src.metrics` | `rank_products(df, metric, ascending, limit)` | DataFrame; BRL-12 tie-break: other measure, then product name |
| `src.metrics` | `calculate_store_target_attainment(sales, targets)` | store-month DataFrame with actual, target, variance, achievement_pct |
| `src.metrics` | `calculate_region_target_attainment(store_results, stores)` | region results using sum(actual) / sum(target) |
| `src.metrics` | `calculate_discount_metrics(df)` | discount-band measures using BRL-07 |
| `src.metrics` | `calculate_customer_mix(df)` | segment/repeat revenue and share DataFrame |
| `src.metrics` | `calculate_payment_mix(df)` / `calculate_channel_mix(df)` | monthly share DataFrames |
| `src.metrics` | `calculate_weekday_month(df)` | dict with 7 weekdays and 12 months, zero-filled |
| `src.stats` | `three_month_forecast(monthly, method="seasonal_naive")` | dict with 3 months, 3 values, MAPE, method and Estimate label |
| `src.stats` | `welch_aov_test(a, b)` | dict with n, statistic, p-value, verdict and unreliable flag |
| `src.stats` | `one_way_anova(groups)` | dict with group sizes, F, p, assumptions and interpretation |
| `src.stats` | `correlation_analysis(df, method)` | DataFrame with pair, coefficient, p-value, n and plain-English caveat |

## Known baseline conflicts to resolve in Step 15

1. **Forecast:** Step 8 KPI sheet says simple 3-month moving average; BRD BR-03 requires backtest error within 15%; TRD allows a seasonal-naive baseline or rolling mean. On the supplied Step 10 monthly series, a recursive 3-month moving average gives about **25.99% MAPE** for Oct–Dec 2025, while same-month-prior-year seasonal-naive gives about **1.92%**. The tests therefore provisionally exercise seasonal-naive because it is TRD-permitted and meets the BRD threshold. Do not add advanced ML (BR-15 remains Won't). Record the chosen method in the methodology page.
2. **Data cleaning:** BRL-14 says failed records are excluded and reported, and US-15 says invalid records are excluded or quarantined. Step 10's raw-stage cleaning log records explicit imputations/repairs for 500 missing values and 3 outliers, plus removal of 2 duplicate lines. Tests require every issue to be logged and the canonical database to contain no invalid rows. Step 15 must keep the raw issue register separate from the clean analytical database and must never silently alter records.
3. **Ranking ties:** BRL-12 in the BRD says tie-break by the other measure, then product name alphabetically. The Step 7 TRD has an earlier product-ID tie-break note. The BRD rule controls; tests use BRL-12.

## Execution status

All functional test cases in the Word test plan and all technical test IDs are initially **Not run**. Tests that depend on Step 15 modules/pages are expected to skip or fail until those modules/pages are implemented. No test has been reported as passed merely because test code was written.
