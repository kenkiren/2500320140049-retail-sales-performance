# Retail Sales Performance Analysis

ShopSphere Retail is a fictional, read-only retail sales dashboard built for an
MCA Data Analytics project at ABES Engineering College. The canonical data are
synthetic and cover 2024-01-01 through 2025-12-31.

## Features

- Five headline KPIs: revenue, profit, units, distinct orders and AOV
- Equal-period previous-period growth comparisons
- 24-month monthly revenue/profit trend and 12 calendar-month seasonal indices
- Seasonal-naive three-month revenue estimates labelled **Estimate**
- Category/sub-category profitability and product rankings
- Store-month and region target attainment
- Discount, customer, payment, channel and calendar analysis
- Welch t-test, one-way ANOVA and Pearson/Spearman correlation
- Evidence-linked insights
- Privacy-safe aggregate CSV export
- Dataset validation and raw-vs-clean data-quality evidence

The project answers the approved OQ-01 to OQ-10 operational questions.

## Eight pages

1. Overview & KPIs
2. Sales Trend & Forecast
3. Business Comparison
4. EDA & Statistics
5. Insights
6. Data & Download
7. Data Quality
8. About & Methodology

## Data

`data/app.db` is the canonical read-only SQLite source. It contains five physical
tables (`stores`, `products`, `customers`, `sales_lines`, `store_targets`) and
one 38-column `v_sales_analysis` view.

- 20,000 sales lines
- 12 stores
- 288 store-month targets
- Random seed: 42
- Raw staging and issue evidence remain in `data/`

No real personal, company or store data is included. Returns and cancellations
are excluded.

## Python setup

Use Python 3.12:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run locally:

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit.

## Tests

Run all technical and integration tests:

```powershell
python -m pytest -q tests/
python -m pytest --cov=src --cov-report=term-missing tests/
```

Run one layer:

```powershell
python -m pytest -q tests/test_data.py
python -m pytest -q tests/test_analysis.py
python -m pytest -q tests/test_app.py
```

## Metric definitions

- Revenue: `SUM(quantity * selling_unit_price)`
- Profit: `SUM(quantity * (selling_unit_price - cost_price))`
- Margin: `100 * SUM(profit) / SUM(revenue)`
- Units: `SUM(quantity)`
- Order count: `COUNT(DISTINCT order_id)`
- AOV: `revenue / distinct order count`
- Target achievement: `store-month actual / one store-month target * 100`

Store targets are joined once after actual sales are aggregated to store-month.
The repeated `target_revenue` values in `v_sales_analysis` are never summed.

## Statistical and forecast methods

The forecast is a simple seasonal-naive baseline. It uses the same calendar
month from the prior year and is labelled **Estimate**. It is not advanced
machine learning; BR-15 remains explicitly out of scope.

Welch t-tests and one-way ANOVA are evaluated at the 5% level. Groups with fewer
than 30 observations are flagged unreliable. Correlation is reported as
association only and never as proof of causation.

Product cost is static at the product-master level. The schema does not store
historical unit cost at sale.

## CSV privacy

The Data & Download page exports only the visible category aggregate. Customer
IDs, names, addresses, phones, emails and other personal identifiers are excluded.
The export is created in memory and is not written into the repository.

## Data quality

The Step 10 raw staging evidence contains 20,002 raw rows and 505 issue records:

- 500 missing-value rows
- 2 duplicate line IDs
- 3 extreme outliers

The canonical database contains 20,000 valid sales lines and has no duplicate
keys or foreign-key violations.

## Known limitations

- There is no live POS integration.
- There are no returns or cancellations.
- There is no historical cost-at-sale field.
- Advanced ML forecasting is excluded.
- Synthetic findings are not claims about real retail markets.
- A mentor change-control decision is still needed for the documented
  seasonal-naive versus moving-average forecast conflict.

## Deployment

Deployment status: **Deployment pending**

Streamlit Community Cloud deployment will require repository access and account
authorization. When live, configure `app.py` as the entry point and install
dependencies from `requirements.txt`. Do not use secrets or credentials in code.

## Project documents

- [BRD](docs/05_Devesh_BRD.docx)
- [Database design](docs/08_Database_Design.xlsx)
- [UI framework](docs/12_UI_Framework.docx)
- [Test cases](docs/13_Test_Cases.docx)
- [Final RTM](docs/13_Final_RTM.xlsx)
- [Build plan](BUILD_PLAN.md)
