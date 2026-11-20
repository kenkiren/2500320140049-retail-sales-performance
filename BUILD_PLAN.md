# STEP 14 — BUILD PLAN
## Retail Sales Performance Analysis | Step 15 AI build input

**Project owner:** Devesh Chandra Gupta | MCA 2nd Year (Data Analytics), ABES  
**Mentor:** Alpna Lodhi  
**Organisation:** ShopSphere Retail Pvt. Ltd. (fictional), Noida  
**Version:** 1.0 | **Date:** 20 November 2026  
**Purpose:** One-task-at-a-time implementation plan for Step 15. This Markdown file is the controlling build instruction; `docs/14_BUILD_PLAN.docx` is its Word copy.

> **Execution rule:** Complete BUILD-01, verify its gate, then proceed to BUILD-02. Do not start the next BUILD task while the current task has a failing gate. Preserve the approved IDs, source data, metric rules, UI register and Step 13 tests. Never mark a test passed without running it.

---

# 1. Project summary — 10 lines

1. This is an academic MCA Data Analytics project at ABES Engineering College, Ghaziabad.
2. The business scenario is ShopSphere Retail Pvt. Ltd., a fictional retailer with 12 stores across Delhi NCR and an online channel.
3. The goal is a read-only, self-service Retail Sales Performance Analysis web application for managers and analysts.
4. The approved synthetic dataset covers January 2024–December 2025 and contains 20,000 sales lines, 12 stores, about 150 products, 2,000 anonymous customers and 288 store-month targets.
5. The SQLite database contains five physical tables (`stores`, `products`, `customers`, `sales_lines`, `store_targets`) and a 38-column `v_sales_analysis` view.
6. Python, pandas, NumPy, SciPy, statsmodels, SQLite, Streamlit and Plotly provide the data, analysis and application layers.
7. One shared filter context applies date range, region, store, product category and sales channel to all analysis pages.
8. The interface has eight screens: Overview, Trend, Compare, EDA & Statistics, Insights, Data & Download, Data Quality, and About & Methodology.
9. The approved traceability baseline contains OQ-01–OQ-10, HMW-01–HMW-12, BR-01–BR-16, FR-01–FR-18, US-01–US-18, UI-01–UI-08, TC-F-01–TC-F-38 and TC-T-01–TC-T-33.
10. All data is synthetic; returns, cancellations, live POS integration, personal data and advanced machine-learning forecasting are excluded; the intended public demo host is Streamlit Community Cloud.

## 1.1 Project document register — links to every available project document

These links are repository-relative. Keep the source documents in `docs/` so the links work in the project repository and the Step 14 package.

| Step | Source / document | Purpose and authority |
|---|---|---|
| 1 | [01_Retail_Sales_Project_Understanding.docx](docs/01_Retail_Sales_Project_Understanding.docx) | Initial project understanding, stakeholders and OQ baseline. Its early NorthStar / eight-store / 2026 / returns assumptions are superseded by the later BRD baseline below. |
| 2 | [02_HMW_Statements.docx](docs/02_HMW_Statements.docx) | HMW-01–HMW-12 and prioritisation. |
| 3 | [03_Needs_Analysis.docx](docs/03_Needs_Analysis.docx) | Initial business needs and BR-01–BR-15. |
| 4 | [04_Devesh_Traceability_Matrix.xlsx](docs/04_Devesh_Traceability_Matrix.xlsx) | Original HMW–BR–OQ traceability matrix. Retain as historical source; it predates BR-16. |
| 5 | [05_Devesh_BRD.docx](docs/05_Devesh_BRD.docx) | **Controlling business baseline:** BR-01–BR-16, BRL-01–BRL-15, MoSCoW priorities, acceptance criteria and success criteria SC-01–SC-09. |
| 6 | PRD deliberately skipped | There is no Step 6 PRD and no approved F-xx Feature ID family. Do not invent F-IDs. |
| 7 | [07_TRD.docx](docs/07_TRD.docx) | Technical architecture, FR-01–FR-18, Python 3.12, dependency pins, performance, quality, security and deployment requirements. |
| 8 | [08_Database_Design.xlsx](docs/08_Database_Design.xlsx) | Five-table schema, keys, data dictionary, 38-column analysis view, KPI definitions and SQLite DDL. |
| 9 | [09_ER_Diagram.docx](docs/09_ER_Diagram.docx), [09_ER_Diagram.mmd](docs/09_ER_Diagram.mmd), [09_ER_Diagram.png](docs/09_ER_Diagram.png) | Physical ER model and relationship notes. |
| 10 | [generate_data.py](src/generate_data.py), [app.db](data/app.db), [retail_sales_performance_data.xlsx](data/retail_sales_performance_data.xlsx), [validation_report.txt](data/validation_report.txt), [sales_lines_raw_with_issues.csv](data/sales_lines_raw_with_issues.csv), [data_quality_issues.csv](data/data_quality_issues.csv) | Synthetic data generator, canonical database, raw staging, quality register and validation evidence. |
| 11 | [11_User_Stories.docx](docs/11_User_Stories.docx), [11_Updated_RTM.xlsx](docs/11_Updated_RTM.xlsx) | US-01–US-18 and completed user-story traceability. |
| 12 | [12_UI_Framework.docx](docs/12_UI_Framework.docx), [12_Updated_RTM.xlsx](docs/12_Updated_RTM.xlsx), [ui.py](src/ui.py), [config.toml](.streamlit/config.toml) | Eight-screen UI framework, shared filters, wireframes, chart mapping, reusable components and starter UI module. |
| 13 | [13_Test_Cases.docx](docs/13_Test_Cases.docx), [13_Final_RTM.xlsx](docs/13_Final_RTM.xlsx), [tests/README.md](tests/README.md), [test_data.py](tests/test_data.py), [test_analysis.py](tests/test_analysis.py), [test_app.py](tests/test_app.py) | 38 functional tests, 33 technical tests, test-facing Python contracts and final test traceability. |
| 14 | [14_BUILD_PLAN.docx](docs/14_BUILD_PLAN.docx), this file [BUILD_PLAN.md](BUILD_PLAN.md) | Step-by-step build order and exact AI prompts for Step 15. |

## 1.2 Baseline precedence and decisions — read before coding

When source documents disagree, use this precedence for implementation:

1. Step 5 BRD v1.0 for business scope, BR IDs, acceptance criteria and business rules.
2. Step 7 TRD for architecture, FR IDs, runtime, performance, privacy and deployment.
3. Step 8 Database Design and Step 9 ER diagram for physical schema and data grain.
4. Step 10 generated files and `validation_report.txt` for the actual canonical dataset.
5. Step 11 User Stories for US IDs and Given/When/Then acceptance.
6. Step 12 UI Framework for the final eight-screen register, shared filter behaviour and page names.
7. Step 13 Test Cases and `13_Final_RTM.xlsx` for test IDs and test-facing function contracts.
8. Step 1–4 remain important historical context, but must not silently override later approved documents.

**Explicit conflicts and implementation treatment**

- **Business name / size / period:** Step 1 says NorthStar, eight stores and 2026. The later approved BRD, TRD, database and Step 10 data say ShopSphere, 12 stores and January 2024–December 2025. Build the latter.
- **Returns:** Step 1 discusses returns; Step 5 BRD assumption A-20 and scope exclude returns and cancellations. The Step 10 data contains completed positive sales lines only. Do not invent refund measures or return screens.
- **Step 6:** skipped. FR-01–FR-18 are technical functional references, not F-xx PRD Feature IDs.
- **Page architecture:** Step 7's early page-file proposal is superseded by the eight exact Step 12 page files listed in section 2.
- **Forecast:** Step 8 KPI sheet names a three-month moving average. Step 7 allows a simple seasonal-naive or rolling-mean baseline. Step 13's test contract defaults to `seasonal_naive`; its recorded Step 10 backtest is about 1.92% MAPE, while the recursive moving average is about 25.99% for the stated holdout. Use the Step 13 tested `seasonal_naive` default unless the mentor approves a different TRD-permitted method that meets BR-03's ≤15% MAPE target. Always label values **Estimate**. Never implement advanced ML (BR-15 Won't).
- **Cleaning:** BRL-14 requires failed records to be excluded and reported, never silently corrected. Step 10 explicitly logged imputation / repair of the staged missing values and outliers, and duplicate removal. Preserve the Step 10 issue register and resolution evidence. For new runtime validation fixtures, log every defect and exclude or quarantine invalid rows; never silently mutate them. The canonical `data/app.db` is already cleaned; do not run a second cleaning pass over it.
- **Ranking ties:** BRL-12 controls: secondary measure first, then product name alphabetically. This supersedes the earlier Step 7 product-ID tie-break note.
- **Targets:** `target_revenue` repeats on the line-grain `v_sales_analysis` view. Never sum it from that view. Aggregate sales to store-month and join one row per store-month from `store_targets`.
- **Historical cost:** Step 8 stores current product-level `products.cost_price`; historical cost-at-sale is not represented. Step 9 recommended a future `unit_cost_at_sale` enhancement, but Step 10 preserved the approved Step 8 schema. Do not change the five-table schema in Step 15 without explicit approval; document this limitation.
- **Filters:** BR-16 requires date, region, store, category **and channel**, together or individually, on every analysis view.
- **Performance:** satisfy both targets: database-loader median <3 seconds (Step 13 engineering target) and each warmed page ≤5 seconds (BRD SC-05 / TRD).
- **No fabricated pass status:** Step 13 cases start Not run. Syntax compilation or writing code does not mean a test passed.

---

# 2. Final repository folder structure

Use this as the final Step 15 repository layout. Keep exact page filenames and test filenames; add files only when they support an approved requirement.

```text
retail-sales-performance/
├── app.py
├── requirements.txt
├── .python-version                 # 3.12
├── .gitignore
├── README.md
├── BUILD_PLAN.md
├── .streamlit/
│   └── config.toml
├── data/
│   ├── app.db                      # canonical, cleaned SQLite database
│   ├── sales_lines_raw_with_issues.csv
│   ├── data_quality_issues.csv
│   ├── validation_report.txt
│   └── retail_sales_performance_data.xlsx
├── src/
│   ├── __init__.py
│   ├── generate_data.py            # existing Step 10 generator; do not run casually
│   ├── db.py
│   ├── validation.py
│   ├── cleaning.py
│   ├── metrics.py
│   ├── stats.py
│   ├── filters.py
│   ├── charts.py
│   ├── insights.py
│   ├── export.py
│   └── ui.py                       # preserve Step 12 starter; extend carefully
├── pages/
│   ├── 01_Overview.py
│   ├── 02_Trend.py
│   ├── 03_Compare.py
│   ├── 04_EDA_Statistics.py
│   ├── 05_Insights.py
│   ├── 06_Data_Download.py
│   ├── 07_Data_Quality.py
│   └── 08_About.py
├── tests/
│   ├── README.md
│   ├── test_data.py
│   ├── test_analysis.py
│   └── test_app.py
└── docs/
    ├── 01_Retail_Sales_Project_Understanding.docx
    ├── 02_HMW_Statements.docx
    ├── 03_Needs_Analysis.docx
    ├── 04_Devesh_Traceability_Matrix.xlsx
    ├── 05_Devesh_BRD.docx
    ├── 07_TRD.docx
    ├── 08_Database_Design.xlsx
    ├── 09_ER_Diagram.docx
    ├── 09_ER_Diagram.mmd
    ├── 09_ER_Diagram.png
    ├── 11_User_Stories.docx
    ├── 11_Updated_RTM.xlsx
    ├── 12_UI_Framework.docx
    ├── 12_Updated_RTM.xlsx
    ├── 13_Test_Cases.docx
    ├── 13_Final_RTM.xlsx
    └── 14_BUILD_PLAN.docx
```

**Folder rules**

- `data/app.db` is the runtime source of truth. Resolve its path from the repository root, not the current working directory.
- `src/generate_data.py` is the Step 10 reproducibility script. It deletes/rebuilds the database; run it only when intentionally regenerating the dataset, then rerun every data validation.
- `src/ui.py` is supplied by Step 12. Preserve its safe HTML escaping, Tailwind/native fallback and session-state filter keys.
- Streamlit's `pages/` directory is the approved eight-screen navigation structure.
- Keep the Step 13 test scripts unchanged unless a genuine test defect or approved requirement change is identified. If changed, document the reason and update the RTM.
- Do not commit `.venv/`, `__pycache__/`, `.pytest_cache/`, `.coverage`, secrets, credentials, personal data or local temporary files.

---

# 3. Build tasks — execute one at a time

## Common AI instruction for every task

Paste the task-specific prompt below into the coding AI. Work in the project repository. Ask it to inspect existing files before editing. It must implement only the named BUILD task, report files changed, run the stated checks and stop. If a check fails, fix the current task before continuing. Do not invent data, IDs, business rules or test passes.

### BUILD-01 — Project scaffold, Python runtime and requirements

**Goal:** Create the repository skeleton and a reproducible Python 3.12 environment using the Step 7 pinned packages.

**Files:** `requirements.txt`, `.python-version`, `.gitignore`, `README.md` placeholder if absent, `.streamlit/config.toml`, `src/__init__.py`, `pages/`, `tests/`, `docs/`, `data/`. Copy the approved project documents and Step 10/12/13 assets into the corresponding folders.

**Stories / FR / BR:** US-14, US-17, US-18 | FR-13, FR-17, FR-18 | BR-12, BR-13, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-01 only: create the Retail Sales Performance Analysis repository scaffold.
Use Python 3.12. Create requirements.txt with these exact initial pins:
streamlit==1.40.2
pandas==2.2.3
numpy==1.26.4
scipy==1.14.1
statsmodels==0.14.4
plotly==5.24.1
pytest==8.3.4
pytest-cov==6.0.0
Create .python-version containing 3.12 and a .gitignore for .venv, __pycache__,
.pytest_cache, .coverage, secrets and temporary files. Preserve the supplied
Step 12 .streamlit/config.toml and src/ui.py. Create the final folders and copy
the approved docs, Step 10 data assets and Step 13 tests without changing them.
Do not create business logic, app pages or fake placeholder modules. Do not
change the SQLite schema or any BR/HMW/OQ/US/FR/UI/TC IDs. Report the file tree.
Run Python-version and dependency-install checks, then stop.
```

**How to check:** `python --version` reports 3.12; `python -m pip install -r requirements.txt` completes; verify all baseline files exist and compare the copied `app.db` checksum / size with the supplied Step 10 file.

**Tests that must pass:** environment smoke check; no functional or technical test is to be marked passed at this setup-only stage.

**Gate:** clean environment installs all pinned packages and all baseline assets are present.

---

### BUILD-02 — SQLite data loader, validation and cleaning contracts

**Goal:** Implement a read-only database loader and repeatable validation / cleaning functions that match the Step 8 schema and Step 13 test contract.

**Files:** `src/db.py`, `src/validation.py`, `src/cleaning.py`, `data/*`, `tests/test_data.py`.

**Stories / FR / BR:** US-14, US-15, US-18 | FR-13, FR-14, FR-18 | BR-12, BR-13.

**Exact AI prompt:**

```text
Implement BUILD-02 only. Inspect Step 8 Database Design, Step 9 ER Diagram,
Step 10 generate_data.py and validation_report.txt, and tests/test_data.py.
Create:
1) src/db.py with load_analysis_data(db_path=None), resolving data/app.db from
the repository root, opening SQLite read-only, loading v_sales_analysis and
returning a pandas DataFrame with exactly 20,000 rows and 38 columns.
Use safe paths, a context-managed connection and no SQL built from user input.
2) src/validation.py with validate_sales_lines(df), returning a DataFrame that
contains issue_type and row_count and detects duplicate line_id, blank required
fields, invalid dates, non-positive quantity, non-positive list price and
discount_pct outside 0..100. Also validate FKs/enums/pricing where source
columns permit.
3) src/cleaning.py with clean_sales_lines(df), returning
(clean_dataframe, issue_report_dataframe). Log every defect and exclude or
quarantine invalid rows; never silently change a value.
Keep the supplied canonical data/app.db read-only and do not regenerate it.
Keep raw staging and data_quality_issues.csv separate from canonical data.
Match the exact function signatures and result contracts in tests/README.md.
Do not change schema, source CSVs or test expectations. Run test_data.py.
```

**How to check:** query `sqlite_master`, `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, `PRAGMA table_info(v_sales_analysis)`; loader returns `(20000, 38)`; median of three loads is below 3 seconds.

**Tests that must pass:** TC-T-01–TC-T-12 (`tests/test_data.py`).

**Gate:** all 12 data tests pass; no canonical database mutation; issue log remains available to UI-07.

---

### BUILD-03 — Business KPI and descriptive analysis functions

**Goal:** Implement the single source of truth for BRL formulas and all non-inferential analysis functions.

**Files:** `src/metrics.py`, optional pure helpers in `src/filters.py`, `tests/test_analysis.py`.

**Stories / FR / BR:** US-02, US-03, US-05–US-11, US-14 | FR-02, FR-03, FR-05–FR-11, FR-13 | BR-01, BR-02, BR-04–BR-10, BR-12.

**Exact AI prompt:**

```text
Implement BUILD-03 only. Read the Step 5 BRD business rules BRL-01 to BRL-12,
Step 8 KPIs_Measures, Step 11 user stories and Step 13 tests/test_analysis.py.
Create src/metrics.py with the Step 13 test-facing functions:
calculate_kpis(df)
calculate_category_metrics(df)
rank_products(df, metric, ascending, limit)
calculate_store_target_attainment(sales, targets)
calculate_region_target_attainment(store_results, stores)
calculate_discount_metrics(df)
calculate_customer_mix(df)
calculate_payment_mix(df)
calculate_channel_mix(df)
calculate_weekday_month(df)
Also provide documented monthly trend, seasonal-index and equal-period comparison
helpers needed by the UI.
Use BRL formulas exactly: revenue=sum(quantity*selling_unit_price);
profit=sum(quantity*(selling_unit_price-cost_price));
margin=100*sum(profit)/sum(revenue), not the mean of line margins;
units=sum(quantity); order_count=count distinct order_id; AOV=revenue/order_count.
For store targets, aggregate sales at store-month then join one target row from
store_targets; NEVER sum repeated target_revenue from v_sales_analysis.
For ranking ties follow BRL-12: secondary measure, then product_name alphabetically.
Repeat customers have >=2 distinct orders in the selected period. Discount bands
are 0%, 1-10%, 11-20%, >20%. Return all seven weekdays and twelve months,
zero-filling missing groups. Monthly payment/channel shares use consistent
denominators and reconcile to 100% subject to rounding.
Use stable, testable functions and do not calculate metrics in page files.
Run the relevant analysis tests and stop.
```

**How to check:** compare revenue, profit, units, distinct orders, AOV and weighted margin to independent SQL / hand calculations; reconcile category and monthly totals; verify target calculations against `store_targets`.

**Tests that must pass:** TC-T-13, TC-T-14, TC-T-16–TC-T-22.

**Gate:** all listed tests pass; every metric uses one documented definition; no target double-counting.

---

### BUILD-04 — Forecast baseline and statistical methods

**Goal:** Implement the simple estimate and required statistical analysis without advanced ML.

**Files:** `src/stats.py`, `tests/test_analysis.py`, method notes for UI-02 / UI-04 / UI-08.

**Stories / FR / BR:** US-04, US-12, US-13, US-18 | FR-04, FR-12, FR-16, FR-18 | BR-03, BR-07, BR-11, BR-15 (scope exclusion).

**Exact AI prompt:**

```text
Implement BUILD-04 only. Read BRL-11 and BRL-13, the Step 7 statistical plan,
Step 8 forecast note and Step 13 tests/test_analysis.py / tests/README.md.
Create src/stats.py with:
three_month_forecast(monthly, method="seasonal_naive")
welch_aov_test(a, b)
one_way_anova(groups)
correlation_analysis(df, method="pearson")
The forecast must return forecast_months, forecast_values, label, method and
mape_pct; it must produce exactly three future months and label every value
"Estimate". Use at least 24 months of history. The Step 13 test contract expects
the seasonal_naive default and a MAPE <=15% on its known fixture. Document the
method conflict: Step 8 says moving average; Step 7 permits a simple baseline;
Step 13 selects seasonal_naive provisionally because the Step 10 backtest is
about 1.92% versus about 25.99% for the recursive moving average. Keep it
transparent and record that mentor confirmation is required. Do NOT build
advanced machine-learning forecasting; BR-15 remains Won't.
Welch t-test: two independent order-level AOV groups; return n, t statistic,
p-value, 5% verdict, interpretation and unreliable flag. One-way ANOVA:
three or more groups; return group sizes, F statistic, p-value, assumption
checks and interpretation. Flag any group with n<30 as unreliable.
Correlation: report Pearson or Spearman coefficient, p-value, sample size,
strength and plain-English interpretation. Explicitly state association is
not causation. Handle empty/constant/invalid samples without raw exceptions.
Run the relevant analysis tests and stop.
```

**How to check:** verify test outputs against SciPy calculations; test two groups, three groups, small samples, constant series and forecast holdout.

**Tests that must pass:** TC-T-15, TC-T-23–TC-T-26.

**Gate:** all listed tests pass; no ML claim; forecast is an estimate; statistical caveats are visible.

---

### BUILD-05 — Shared filters and reusable UI components

**Goal:** Preserve and integrate the Step 12 UI helper so all pages share one filter context and reusable components.

**Files:** `src/ui.py`, `src/filters.py`, `.streamlit/config.toml`, `tests/test_analysis.py`.

**Stories / FR / BR:** US-01, US-14, US-17 | FR-01, FR-13, FR-17 | BR-12, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-05 only. Inspect the supplied Step 12 src/ui.py and UI Framework.
Preserve its render_page_header, render_kpi_card, render_chart_card,
render_insight_box, render_global_filters, reset_global_filters and
apply_global_filters helpers. Preserve the five exact session-state keys:
ui_global_date_range, ui_global_region, ui_global_stores,
ui_global_category, ui_global_channel.
Every page must use the same date, region, store, product-category and channel
filters. Store choices must be limited by selected region; blank store selection
means all stores in that region. Changing region clears invalid store choices.
Add or refine a pure filtering helper only if needed, but ensure
src.ui.apply_global_filters(df, filters) remains available for Step 13 tests.
Keep all interactive controls and Plotly charts in native Streamlit. The Tailwind
iframe is decorative only. Keep HTML values escaped and preserve the
Streamlit 1.40.2 components.v1.html fallback; do not assume st.iframe exists.
Do not create separate page-specific copies of global filters. Run TC-T-27.
```

**How to check:** change each filter alone and together; navigate between pages; reset filters; verify session state persists and empty selections do not show stale data.

**Tests that must pass:** TC-T-27; later integration check TC-T-30 and functional TC-F-01–TC-F-07.

**Gate:** shared filters are deterministic, persist across navigation and apply to all analytical outputs.

---

### BUILD-06 — Streamlit application shell and navigation

**Goal:** Create the app entry point and ensure all eight approved pages are discoverable.

**Files:** `app.py`, `pages/`, `src/db.py`, `src/ui.py`.

**Stories / FR / BR:** US-01, US-17 | FR-01, FR-17 | BR-16.

**Exact AI prompt:**

```text
Implement BUILD-06 only. Create app.py as the ShopSphere Retail landing page
and Streamlit multipage shell. Use the exact eight Step 12 page filenames:
01_Overview.py, 02_Trend.py, 03_Compare.py, 04_EDA_Statistics.py,
05_Insights.py, 06_Data_Download.py, 07_Data_Quality.py, 08_About.py.
Set page configuration, title, concise project introduction and a safe
database-load status. Use the repository-root path and the shared src modules.
Do not duplicate business calculations in app.py. Do not expose tracebacks,
secrets or personal data. Keep navigation consistent and do not add login or
write access. If a page is not yet built, leave it for its own BUILD task rather
than adding fake charts. Run the app-start smoke check and stop.
```

**How to check:** `streamlit run app.py`; confirm the app starts and all eight pages appear in navigation.

**Tests that must pass:** TC-T-28. Full page tests are completed after BUILD-14.

**Gate:** app starts without traceback and exposes the eight page routes.

---

### BUILD-07 — UI-01 Overview & KPIs

**Goal:** Deliver the five headline KPIs, equal-period comparison and concise overview.

**Files:** `pages/01_Overview.py`, `src/metrics.py`, `src/charts.py`, `src/ui.py`.

**Stories / FR / BR:** US-01, US-02, US-14, US-17 | FR-01, FR-02, FR-13, FR-17 | BR-01, BR-12, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-07 only: UI-01 Overview & KPIs. Follow the Step 12 wireframe.
Render the shared filters, five KPI cards (revenue, profit, units, distinct
orders, AOV), absolute and percentage changes versus the immediately preceding
equal-duration period, a monthly revenue/profit mini-trend and category/store
highlights. Use src.metrics and src.ui only; do not recalculate formulas here.
If the previous-period value is zero, show N/A rather than divide by zero.
Display the selected date range, INR units, metric definitions and a clear
empty state. Every displayed number must use the same five shared filters.
Use responsive cards and native Plotly charts. Do not show raw customer details.
Run the relevant tests and stop.
```

**How to check:** manually calculate one seven-day range and five comparison ranges; confirm zero-baseline growth displays N/A; compare overview totals to SQL.

**Tests that must pass:** TC-F-01–TC-F-09, TC-F-28; supporting TC-T-13 and TC-T-27.

**Gate:** all five KPIs reconcile exactly; filters persist; empty state is correct.

---

### BUILD-08 — UI-02 Sales Trend & Forecast

**Goal:** Show 24 monthly revenue/profit points, 12 seasonal indices and the three-month simple estimate.

**Files:** `pages/02_Trend.py`, `src/metrics.py`, `src/stats.py`, `src/charts.py`.

**Stories / FR / BR:** US-01, US-03, US-04, US-14, US-17 | FR-01, FR-03, FR-04, FR-13, FR-17 | BR-02, BR-03, BR-12, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-08 only: UI-02 Sales Trend & Forecast. Follow the Step 12
wireframe and use the full 2024-01 to 2025-12 dataset by default so all 24
months are visible. Display monthly revenue and profit as a line chart,
12 calendar-month seasonal indices as a bar chart, and exactly three future
monthly estimates in a table/panel with method and backtest MAPE.
Use src.stats.three_month_forecast; default to the Step 13 tested seasonal_naive
method unless mentor-approved change control says otherwise. Label every future
value Estimate, explain the method in plain English, and state that advanced
machine-learning forecasting is out of scope (BR-15 Won't). If the selected
filters/date range leave fewer than 24 months, show a clear limitation rather
than pretending the full-history method is valid. Use the shared filter context.
Run the relevant tests and stop.
```

**How to check:** confirm exactly 24 historical months, all 12 calendar months, three forecast months, backtest error ≤15%, and explicit Estimate labels.

**Tests that must pass:** TC-F-10–TC-F-12, TC-F-33; TC-T-15.

**Gate:** seasonality reconciles to monthly totals; forecast meets the BR-03 error target and is never represented as ML.

---

### BUILD-09 — UI-03 Business Comparison

**Goal:** Compare category profitability, top/bottom products and store/region target attainment.

**Files:** `pages/03_Compare.py`, `src/metrics.py`, `src/charts.py`.

**Stories / FR / BR:** US-01, US-05, US-06, US-07, US-14, US-17 | FR-01, FR-05, FR-06, FR-07, FR-13, FR-17 | BR-04, BR-05, BR-06, BR-12, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-09 only: UI-03 Business Comparison with three tabs:
Category & sub-category; Top/bottom products; Stores & regions vs targets.
Category tables/charts must show revenue, cost, profit and weighted margin;
flag margin below 10% and negative profit. Product rankings must show separate
top/bottom ten lists by revenue and units for chain-wide and selected-store
views; apply BRL-12 ties (secondary measure, then product name alphabetically).
Store/region target tables must show actual, target, variance and achievement %.
Aggregate actuals to store-month and join targets once from store_targets;
never sum repeated target_revenue from v_sales_analysis. Highlight stores below
100%. All tabs must respond to all shared filters and provide empty states.
Use existing src.metrics functions. Run relevant tests and stop.
```

**How to check:** independently recalculate category sums, weighted margin, rankings and store-month target achievement; compare region ratio to sum(actual)/sum(target), not the mean of store percentages.

**Tests that must pass:** TC-F-13–TC-F-17; TC-T-14, TC-T-16, TC-T-17.

**Gate:** category totals reconcile; rankings follow BRL-12; target totals are not duplicated.

---

### BUILD-10 — UI-04 EDA & Statistics

**Goal:** Deliver discount, customer, payment/channel, calendar and statistical analysis tabs.

**Files:** `pages/04_EDA_Statistics.py`, `src/metrics.py`, `src/stats.py`, `src/charts.py`.

**Stories / FR / BR:** US-01, US-08, US-09, US-10, US-11, US-12, US-13, US-14, US-17 | FR-01, FR-08–FR-13, FR-17 | BR-07–BR-12, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-10 only: UI-04 EDA & Statistics with Step 12 tabs:
Discounts, Customers, Channel & Payment, Calendar, Statistical Tests.
Discounts: show 0%, 1-10%, 11-20%, >20% bands with units, revenue and weighted
margin; include scatter views for discount vs quantity/profit.
Customers: show Budget/Regular/Premium revenue shares and repeat vs one-time
customer contribution using distinct orders in the selected period.
Channel & Payment: show all allowed payment modes and both channels, counts,
revenue shares and monthly trend; shares must reconcile to 100% subject to
rounding. Calendar: show all seven weekdays and twelve months, including
zero/no-data categories. Statistical Tests: provide two-group Welch t-test,
three-or-more-group one-way ANOVA, and correlation results with n, statistic,
p-value, effect size where available, assumptions and plain-English caveats.
Flag group n<30 as unreliable. Never say correlation proves causation.
Use shared filters; statistical group selector is local to the test panel only.
Run relevant tests and stop.
```

**How to check:** inspect all bands/modes/channels, reconcile monthly shares, check all calendar categories, compare statistics to independent SciPy outputs and verify small-group warnings.

**Tests that must pass:** TC-F-18–TC-F-27; TC-T-18–TC-T-26.

**Gate:** all five tabs work; statistical assumptions and caveats are visible; no unsupported causal claim.

---

### BUILD-11 — UI-05 Insights and evidence-linked narratives

**Goal:** Generate concise, filter-aware insights from calculated results, not invented or hard-coded business claims.

**Files:** `src/insights.py`, `pages/05_Insights.py`, `src/ui.py`.

**Stories / FR / BR:** US-01, US-12, US-13, US-14, US-18 | FR-01, FR-12, FR-13, FR-18 | BR-07, BR-11, BR-12, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-11 only: create src/insights.py and UI-05 pages/05_Insights.py.
Generate evidence-based insight cards grouped by Sales, Profitability, Stores,
Customers and Statistical Evidence. Each card must include a short title,
plain-English observation, exact supporting measure/value, selected filter
scope, severity/tone and a limitation/caveat. Derive every number from the
same filtered data and existing metrics/statistics functions. Do not hard-code
Step 10's expected patterns as if they were guaranteed outcomes; calculate
them from the current selected data. Do not imply correlation is causation.
Do not create an unsupported recommendation or forecast. Handle empty data
with a clear empty state. Use the Step 12 insight-box component and shared
filters. Run relevant tests and stop.
```

**How to check:** change date/store/category/channel filters and verify insight evidence changes; compare each card's values with UI-01–UI-04; inspect caveats.

**Tests that must pass:** TC-F-19, TC-F-27, TC-F-28, TC-F-38; related TC-T-25 and TC-T-27.

**Gate:** every insight is traceable to a displayed measure and active filter context.

---

### BUILD-12 — UI-06 Data & Download

**Goal:** Show and export exactly the currently filtered aggregate output without personal data.

**Files:** `src/export.py`, `pages/06_Data_Download.py`, `tests/test_app.py`.

**Stories / FR / BR:** US-01, US-14, US-16, US-17 | FR-01, FR-13, FR-15, FR-17 | BR-12, BR-14, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-12 only: UI-06 Data & Download. Create a safe export helper
and a page showing the filtered aggregate preview, selected-filter summary,
row count, total summary, column descriptions and CSV download button.
The downloaded CSV must represent exactly the table currently visible and
must use the same five shared filters. Exclude customer_id, customer names,
phone numbers, emails, addresses and all personal/customer-level identifiers.
Do not export raw line-level customer data. Add automated coverage for TC-T-33
in tests/test_app.py or a suitable test file: compare preview/export columns,
row count and totals, and assert no customer identifiers or personal fields
are present. Keep the export in-memory; do not write user downloads into the
repository. Run relevant tests and stop.
```

**How to check:** export two different filter slices; compare CSV rows, headers and totals with the on-screen aggregate; inspect for customer fields.

**Tests that must pass:** TC-F-31, TC-F-32, TC-T-33.

**Gate:** downloaded CSV equals the preview and contains no customer identifiers or personal data.

---

### BUILD-13 — UI-07 Data Quality

**Goal:** Expose dataset validation status, defect counts and cleaning decisions transparently.

**Files:** `pages/07_Data_Quality.py`, `src/validation.py`, `src/cleaning.py`, `data/data_quality_issues.csv`, `data/validation_report.txt`.

**Stories / FR / BR:** US-01, US-15, US-17, US-18 | FR-01, FR-14, FR-17, FR-18 | BR-12, BR-13, BR-16.

**Exact AI prompt:**

```text
Implement BUILD-13 only: UI-07 Data Quality. Read the Step 10 validation report,
raw staging CSV and issue register. Show a dataset-level validation banner,
canonical row count, duplicate-key count, missing required values, invalid
dates, invalid quantity/price, discount-range issues, foreign-key status and
issue-type counts. Clearly distinguish raw staging defects from the cleaned
canonical data loaded by the app. The Step 10 evidence is: 20,002 raw staging
rows, 20,000 clean sales lines, 500 missing-value issues, 2 duplicate lines,
3 extreme outliers, and 505 issue-register records. Do not rerun or silently
change the canonical database. Show how Step 10 logged imputation/repair and
duplicate removal; state that future validation failures are excluded or
quarantined and reported under BRL-14. Label validation scope as dataset-level;
global filters are context only unless validation is explicitly rerun on a
filtered subset. Run relevant tests and stop.
```

**How to check:** compare displayed counts with validation_report.txt and data_quality_issues.csv; verify the canonical DB has 20,000 valid rows, no FK violations and no duplicate line IDs.

**Tests that must pass:** TC-F-29, TC-F-30, TC-F-36; TC-T-01–TC-T-11.

**Gate:** data-quality page explains raw-vs-clean status without altering canonical data or misrepresenting the issue counts.

---

### BUILD-14 — UI-08 About & Methodology

**Goal:** Document project metadata, reproducibility, metric/statistical methods, limitations and scope.

**Files:** `pages/08_About.py`, `README.md` draft, `src/metrics.py`, `src/stats.py`.

**Stories / FR / BR:** US-01, US-14, US-17, US-18 | FR-01, FR-13, FR-17, FR-18 | BR-12, BR-13, BR-16; BR-15 Won't.

**Exact AI prompt:**

```text
Implement BUILD-14 only: UI-08 About & Methodology. Display the fictional
ShopSphere project summary, ABES / MCA project context, mentor, synthetic-data
policy, date coverage 2024-01-01 to 2025-12-31, random seed 42, five physical
tables, 20,000 sales lines, 38-column view, app/data version, and the glossary
and formulas from the BRD. Explain revenue, profit, margin, AOV, growth,
target achievement, discount bands, repeat customers, seasonal index,
Welch t-test, one-way ANOVA and correlation. State limitations: no real data,
no returns/cancellations, no POS integration, no advanced ML forecasting,
product-level static cost_price, and descriptive/synthetic findings are not
claims about real retail markets. Explicitly state BR-15 is Won't and BR-03 is
only a simple Estimate. Do not invent approval/sign-off or deployment details.
Run relevant tests and stop.
```

**How to check:** compare metadata and formulas with BRD, Step 8 and Step 10; confirm limitations and BR-15 exclusion are clear.

**Tests that must pass:** TC-F-33, TC-F-36, TC-F-37; TC-T-29.

**Gate:** all method statements are traceable to project sources and no unsupported claim is present.

---

### BUILD-15 — Full integration, all tests and traceability

**Goal:** Run every technical test, execute all functional acceptance cases, fix defects and complete the final evidence record.

**Files:** `tests/test_data.py`, `tests/test_analysis.py`, `tests/test_app.py`, `tests/README.md`, `docs/13_Final_RTM.xlsx`, all `src/`, `pages/`.

**Stories / FR / BR:** US-01–US-18 | FR-01–FR-18 (FR-16 is scope control) | BR-01–BR-16.

**Exact AI prompt:**

```text
Implement BUILD-15 only: full integration and quality assurance. Read the
Step 13 Test Cases and final RTM. Run all 33 technical test IDs TC-T-01 to
TC-T-33 and execute all 38 functional acceptance cases TC-F-01 to TC-F-38
against the running application. Fix root causes, not symptoms. Add automated
TC-T-33 CSV export coverage if not already present. Confirm all eight
Streamlit pages render in AppTest, the five shared session-state keys exist,
the loader median is <3 seconds, each warmed page is <=5 seconds, and
data/KPI logic coverage is >=80%. No test may be skipped or left Not run at
final release. For functional tests, record actual result, evidence and status;
do not claim a manual case passed without executing it. Update the Test Case
and Status fields in the final RTM only when evidence supports the status.
Every BR-01 to BR-16 must have at least one test; BR-15 is a negative scope
test and must not be implemented. Preserve all IDs and stop with a concise
test report, coverage report and remaining-defect list.
```

**How to check:** run full pytest and coverage commands; perform the 38 manual cases; inspect final RTM coverage and defect log.

**Tests that must pass:** TC-T-01–TC-T-33 and TC-F-01–TC-F-38.

**Gate:** zero failing tests, zero unexplained skips, ≥80% coverage of data/KPI logic, all Must BRs verified, and every test status supported by evidence.

---

### BUILD-16 — Complete README and handover documentation

**Goal:** Write a user/developer README that makes the repository independently installable, runnable, testable and understandable.

**Files:** `README.md`, `tests/README.md`, `docs/` references.

**Stories / FR / BR:** US-14, US-17, US-18 | FR-13, FR-17, FR-18 | BR-12, BR-13, BR-15.

**Exact AI prompt:**

```text
Implement BUILD-16 only: write the final root README.md. Include project
purpose, ShopSphere fictional/synthetic-data disclaimer, feature list mapped
to OQ-01–OQ-10, eight-page navigation guide, Python 3.12 setup, exact install
and run commands, test and coverage commands, database/schema summary,
business metric definitions, forecast method and Estimate caveat, statistical
methods and n<30 warning, CSV privacy rule, data-quality evidence, known
limitations, Streamlit Community Cloud deployment steps and document links.
State that BR-15 advanced ML forecasting is excluded, returns/cancellations
are not modelled, and product cost is static at product-master level. Include
the public deployment URL only after it is actually live; otherwise write
"Deployment pending". Do not invent screenshots, test results, mentor
approval or URLs. Keep tests/README.md implementation contracts aligned.
```

**How to check:** follow README from a clean Python 3.12 environment; confirm every command works and all linked files exist.

**Tests that must pass:** TC-F-33, TC-F-36, TC-F-37; all technical tests remain green.

**Gate:** a new user can install, run, test and understand the app without asking the developer for missing instructions.

---

### BUILD-17 — GitHub and Streamlit Community Cloud deployment

**Goal:** Publish a reproducible public demo and verify it from a clean browser session.

**Files:** repository root, `requirements.txt`, `.python-version`, `app.py`, `data/app.db`, `.streamlit/config.toml`, `README.md`.

**Stories / FR / BR:** US-01, US-17, US-18 | FR-01, FR-17, FR-18 | BR-01–BR-16; SC-03, SC-05, SC-07, SC-08.

**Exact AI prompt:**

```text
Implement BUILD-17 only: prepare and deploy the tested application to GitHub
and Streamlit Community Cloud. First confirm BUILD-15 and BUILD-16 gates are
green. Check that the repository contains only synthetic data, no credentials,
secrets, personal data or local cache. Confirm data/app.db is included and
the app resolves it with a repository-relative path. Push the approved branch
to GitHub, connect the repository to Streamlit Community Cloud, set app.py as
the entry point, select a compatible Python 3.12 runtime and install from
requirements.txt. Do not expose secrets in code or README. After deployment,
open the public URL in a clean browser without login on desktop and mobile.
Navigate all eight pages, change all five global filters, reconcile headline
KPIs, test empty states and download the safe aggregate CSV. Measure warmed
page response time and record environment, URL, date and evidence screenshots.
Do not claim deployment success until the public link is actually reachable.
Update README with the real URL and deployment instructions, then stop.
```

**How to check:** public URL works without login on desktop and mobile; all pages and filters work; no traceback; no private data; record deployment evidence.

**Tests that must pass:** TC-F-01–TC-F-07, TC-F-28, TC-F-31–TC-F-38; TC-T-28–TC-T-33; SC-07 public availability and SC-05 response time.

**Gate:** public application is reachable, README has the verified URL, and all release checks remain green.

---

# 4. Definition of Done (Step 15 release)

Step 15 is complete only when all conditions below are true.

## 4.1 Business requirements

The ten Must requirements are implemented and verified:

- **BR-01:** five headline measures and equal-length previous-period comparison.
- **BR-02:** 24-month monthly revenue/profit trend and 12 seasonal indices.
- **BR-04:** category/sub-category revenue, cost, profit, weighted margin and flags.
- **BR-05:** top/bottom ten products by revenue and units for chain / selected store.
- **BR-06:** store and region monthly actual vs target, variance and achievement.
- **BR-07:** discount bands, units, revenue, margin and association analysis.
- **BR-11:** Welch two-group test, one-way ANOVA, correlation and caveats.
- **BR-12:** one metric catalogue and zero unexplained reconciliation difference.
- **BR-13:** duplicate, missing and invalid record detection/reporting.
- **BR-16:** all five global filters apply consistently across all views.

BR-03, BR-08, BR-09 and BR-10 are Should; BR-14 is Could. They are included in this planned build and should be delivered if the schedule allows. BR-15 is Won't and must remain excluded. Never trade away a Must requirement to add an unapproved feature.

## 4.2 Technical and quality gates

- All 33 technical cases TC-T-01–TC-T-33 pass.
- All 38 functional cases TC-F-01–TC-F-38 are executed and evidenced.
- No test is skipped or left Not run at release; a skipped test is not a pass.
- Data/KPI logic test coverage is at least 80%.
- SQLite integrity check is `ok`; foreign-key violations = 0; canonical database contains 20,000 valid sales lines and the 38-column view.
- Database loader median is <3 seconds; each warmed page is ≤5 seconds on the recorded test setup.
- Every page uses the same filter state; no stale values appear for empty results.
- CSV output equals the displayed aggregate and excludes customer identifiers / personal fields.
- Statistical outputs show sample sizes, assumptions and caveats; correlation is not described as causation.
- Forecast uses a documented simple method, has ≤15% backtest MAPE, is labelled Estimate and does not claim ML.

## 4.3 Delivery gates

- Eight pages are live on Streamlit Community Cloud with a public link that works without login on desktop and mobile.
- Root `README.md` includes setup, run, tests, features, data policy, methods, limitations and the verified live URL.
- Final RTM contains the relevant test IDs and evidence-backed statuses for all 18 HMW–BR link rows.
- No secrets, real data or personal information are committed.
- Screenshots, test report, coverage report and deployment evidence are saved for the next academic submission steps.

---

# 5. Commands — Windows, macOS and Linux

Run from the repository root (`retail-sales-performance/`).

## 5.1 Create and activate a virtual environment

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

## 5.2 Install dependencies

```bash
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 5.3 Run the application

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

## 5.4 Run all tests and coverage

```bash
python -m pytest -q tests/
python -m pytest --cov=src --cov-report=term-missing tests/
```

Run one layer when debugging:

```bash
python -m pytest -q tests/test_data.py
python -m pytest -q tests/test_analysis.py
python -m pytest -q tests/test_app.py
```

## 5.5 Optional — regenerate the Step 10 dataset

**Do this only when intentionally rebuilding the synthetic dataset.** The generator deletes and recreates `data/app.db` and writes its staging / audit outputs. Back up the current data first and rerun all data tests afterwards.

```bash
python src/generate_data.py
python -m pytest -q tests/test_data.py
```

---

# 6. Viva notes — 10 likely questions with short answers

1. **What is the purpose of this project?**  
   To provide a single, interactive, SQLite-backed view of synthetic retail sales performance so managers can compare periods, stores, categories, targets and trading patterns.

2. **Why is the dataset synthetic?**  
   It protects privacy and makes the project safe to share publicly while allowing repeatable testing and demonstration. It does not represent actual ShopSphere or market performance.

3. **Why use SQLite and five physical tables?**  
   SQLite is lightweight and file-based for a student-scale read-only app. The five tables separate store, product and customer masters from sales-line and store-month target facts.

4. **Why count distinct order IDs instead of sales rows?**  
   One order can contain several product lines. `COUNT(DISTINCT order_id)` counts the bill once and gives the correct order count and AOV denominator.

5. **How are revenue, profit, margin and AOV calculated?**  
   Revenue = quantity × selling price after discount; profit = (selling price after discount − cost price) × quantity; margin = profit ÷ revenue × 100; AOV = revenue ÷ distinct orders.

6. **Why must targets be aggregated separately from the analysis view?**  
   The view is at sales-line grain and repeats the same store-month target on each line. Summing that repeated value overstates targets; aggregate actual sales to store-month and join the one target record once.

7. **How do global filters work across pages?**  
   Shared Streamlit widgets store selections in `st.session_state`. Every page calls the same filter helper, so date, region, store, category and channel selections remain consistent during navigation.

8. **When are Welch's t-test and ANOVA used?**  
   Welch's t-test compares the means of two independent groups; one-way ANOVA compares three or more groups. The app reports sample sizes and p-values, uses a 5% significance level and flags groups with fewer than 30 observations.

9. **Does correlation prove that discounting causes higher quantity or lower profit?**  
   No. Correlation measures association, not causation. Other variables may influence both; the app must show this limitation.

10. **How is the application tested and deployed?**  
    Pytest checks data integrity, formulas and statistics; Streamlit AppTest checks startup and page rendering; manual functional cases verify user behaviour. The tested app is published from GitHub to Streamlit Community Cloud.

---

# 7. Step 15 operating checklist

Use this checklist in order. Do not tick an item until it is actually complete.

- [ ] BUILD-01 — environment, dependencies and repository scaffold.
- [ ] BUILD-02 — read-only loader, validation and cleaning contracts.
- [ ] BUILD-03 — business metrics and descriptive analysis.
- [ ] BUILD-04 — forecast and statistical methods.
- [ ] BUILD-05 — shared filters and reusable UI helpers.
- [ ] BUILD-06 — app shell and navigation.
- [ ] BUILD-07 — UI-01 Overview & KPIs.
- [ ] BUILD-08 — UI-02 Sales Trend & Forecast.
- [ ] BUILD-09 — UI-03 Business Comparison.
- [ ] BUILD-10 — UI-04 EDA & Statistics.
- [ ] BUILD-11 — UI-05 Insights.
- [ ] BUILD-12 — UI-06 Data & Download.
- [ ] BUILD-13 — UI-07 Data Quality.
- [ ] BUILD-14 — UI-08 About & Methodology.
- [ ] BUILD-15 — all 71 tests, coverage and RTM evidence.
- [ ] BUILD-16 — final README and clean-environment handover.
- [ ] BUILD-17 — GitHub / Streamlit Community Cloud deployment and live verification.

**Final instruction to the Step 15 AI:** Read this file completely before writing code. Execute only one BUILD ID at a time in numerical order. Use the exact prompts, respect the source precedence and acceptance gates, preserve all IDs, and stop after each task with a summary of changed files, commands run, test results and any unresolved issue. Do not silently skip a task or move forward after a failing gate.

**END OF STEP 14 — BUILD PLAN**
