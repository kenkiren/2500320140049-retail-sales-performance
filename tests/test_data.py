"""Data-layer, schema, integrity and cleaning tests for ShopSphere Retail.

The database and raw staging files are Step 10 synthetic artifacts.
Application module contracts in the final tests are implemented in Step 15.
Run from repository root: pytest -q tests/test_data.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "app.db"
RAW_PATH = ROOT / "data" / "sales_lines_raw_with_issues.csv"
ISSUES_PATH = ROOT / "data" / "data_quality_issues.csv"

EXPECTED_TABLES = {
    "stores": 12,
    "products": 150,
    "customers": 2000,
    "sales_lines": 20000,
    "store_targets": 288,
}
EXPECTED_COLUMNS = {
    "stores": ["store_id", "store_name", "city", "region", "store_format", "opened_on", "is_active"],
    "products": ["product_id", "product_name", "category", "sub_category", "brand",
                 "cost_price", "base_list_price", "is_active"],
    "customers": ["customer_id", "segment", "city", "joined_on", "is_active"],
    "sales_lines": ["line_id", "order_id", "sale_date", "store_id", "product_id", "customer_id",
                    "quantity", "list_unit_price", "discount_pct", "selling_unit_price",
                    "payment_mode", "channel"],
    "store_targets": ["target_id", "store_id", "target_month", "target_revenue"],
}
VIEW_COLUMNS = [
    "line_id", "order_id", "sale_date", "sale_month", "sale_weekday", "sale_year",
    "store_id", "store_name", "store_city", "region", "store_format", "store_opened_on",
    "product_id", "product_name", "category", "sub_category", "brand",
    "customer_id", "segment", "customer_city", "customer_joined_on",
    "quantity", "list_unit_price", "discount_pct", "selling_unit_price", "cost_price",
    "payment_mode", "channel", "revenue", "cost_amount", "profit", "margin_pct",
    "discount_amount", "discount_band", "target_month", "target_revenue",
    "is_low_margin", "is_loss_making",
]


@pytest.fixture(scope="module")
def connection():
    assert DB_PATH.exists(), f"Step 10 database is missing: {DB_PATH}"
    # Open read-only so the test suite cannot mutate the canonical dataset.
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]


def test_t01_database_opens_read_only_and_integrity_is_ok(connection):
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_t02_exactly_five_physical_tables_and_one_analysis_view(connection):
    objects = {
        (r["name"], r["type"])
        for r in connection.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table','view') "
            "AND name NOT LIKE 'sqlite_%'"
        )
    }
    assert objects == {
        ("stores", "table"), ("products", "table"), ("customers", "table"),
        ("sales_lines", "table"), ("store_targets", "table"),
        ("v_sales_analysis", "view"),
    }


def test_t03_step8_physical_table_columns_and_release_row_counts(connection):
    for table, expected_rows in EXPECTED_TABLES.items():
        assert _columns(connection, table) == EXPECTED_COLUMNS[table]
        actual_rows = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert actual_rows == expected_rows


def test_t04_joined_analysis_view_has_exactly_38_columns_and_20000_rows(connection):
    assert _columns(connection, "v_sales_analysis") == VIEW_COLUMNS
    assert len(VIEW_COLUMNS) == 38
    assert connection.execute("SELECT COUNT(*) FROM v_sales_analysis").fetchone()[0] == 20000


@pytest.mark.parametrize(
    "table,pk",
    [
        ("stores", "store_id"),
        ("products", "product_id"),
        ("customers", "customer_id"),
        ("sales_lines", "line_id"),
        ("store_targets", "target_id"),
    ],
)
def test_t05_primary_keys_are_non_null_and_unique(connection, table, pk):
    total, distinct_count, null_count = connection.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT {pk}), "
        f"SUM(CASE WHEN {pk} IS NULL THEN 1 ELSE 0 END) FROM {table}"
    ).fetchone()
    assert null_count == 0
    assert total == distinct_count


def test_t06_all_foreign_keys_are_valid(connection):
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_t07_sales_dates_ranges_enumerations_and_price_math_are_valid(connection):
    invalid = connection.execute("""
        SELECT COUNT(*) FROM sales_lines
        WHERE sale_date < '2024-01-01' OR sale_date > '2025-12-31'
           OR quantity <= 0
           OR list_unit_price <= 0
           OR selling_unit_price < 0
           OR discount_pct < 0 OR discount_pct > 100
           OR payment_mode NOT IN ('Cash','Card','UPI','Wallet')
           OR channel NOT IN ('In-store','Online')
           OR ABS(selling_unit_price -
                  list_unit_price * (1 - discount_pct / 100.0)) > 0.02
    """).fetchone()[0]
    assert invalid == 0
    date_min, date_max = connection.execute(
        "SELECT MIN(sale_date), MAX(sale_date) FROM sales_lines"
    ).fetchone()
    assert (date_min, date_max) == ("2024-01-01", "2025-12-31")


def test_t08_store_month_targets_are_unique_and_complete(connection):
    total = connection.execute("SELECT COUNT(*) FROM store_targets").fetchone()[0]
    distinct_pairs = connection.execute(
        "SELECT COUNT(*) FROM (SELECT DISTINCT store_id,target_month FROM store_targets)"
    ).fetchone()[0]
    assert total == 288
    assert distinct_pairs == 288


def test_t09_step10_raw_quality_register_accounts_for_all_505_logged_issues():
    assert RAW_PATH.exists()
    assert ISSUES_PATH.exists()
    raw = pd.read_csv(RAW_PATH)
    issues = pd.read_csv(ISSUES_PATH)
    assert len(raw) == 20002
    assert len(issues) == 505
    counts = issues["issue_type"].value_counts().to_dict()
    assert counts == {
        "Missing value": 500,
        "Duplicate record": 2,
        "Extreme outlier": 3,
    }
    assert raw["line_id"].duplicated(keep=False).sum() == 2
    assert int(raw[["payment_mode", "channel"]].isna().sum().sum()) == 500


def _defect_fixture() -> pd.DataFrame:
    """One clean row plus deliberate defects for every required validation class."""
    return pd.DataFrame([
        [1, "O-1", "2025-01-01", 1, 1, 1, 1, 100.0, 0.0, 100.0, "Cash", "In-store"],
        [2, "O-2", "2025-01-02", 1, 1, 1, 1, 100.0, 5.0, 95.0, "UPI", "Online"],
        [2, "O-2", "2025-01-02", 1, 1, 1, 1, 100.0, 5.0, 95.0, "UPI", "Online"],
        [4, "", "2025-01-03", 1, 1, 1, 1, 100.0, 5.0, 95.0, "Card", "Online"],
        [5, "O-5", "2025-02-30", 1, 1, 1, 1, 100.0, 5.0, 95.0, "Card", "Online"],
        [6, "O-6", "2025-01-05", 1, 1, 1, 0, 100.0, 5.0, 95.0, "Card", "Online"],
        [7, "O-7", "2025-01-06", 1, 1, 1, 1, 0.0, 5.0, 0.0, "Card", "Online"],
        [8, "O-8", "2025-01-07", 1, 1, 1, 1, 100.0, 101.0, 0.0, "Card", "Online"],
    ], columns=[
        "line_id", "order_id", "sale_date", "store_id", "product_id", "customer_id",
        "quantity", "list_unit_price", "discount_pct", "selling_unit_price",
        "payment_mode", "channel",
    ])


def test_t10_validation_function_detects_every_injected_defect():
    validation = pytest.importorskip("src.validation")
    report = validation.validate_sales_lines(_defect_fixture())
    assert isinstance(report, pd.DataFrame)
    assert {"issue_type", "row_count"}.issubset(report.columns)
    counts = dict(zip(report["issue_type"], report["row_count"]))
    expected_types = {
        "duplicate_line_id", "blank_required", "invalid_date",
        "non_positive_quantity", "non_positive_price", "discount_out_of_range",
    }
    assert expected_types.issubset(set(counts))
    assert all(int(counts[k]) >= 1 for k in expected_types)


def test_t11_cleaning_quarantines_or_removes_invalid_rows_and_returns_issue_log():
    cleaning = pytest.importorskip("src.cleaning")
    cleaned, issue_report = cleaning.clean_sales_lines(_defect_fixture())
    assert isinstance(cleaned, pd.DataFrame)
    assert isinstance(issue_report, pd.DataFrame)
    assert cleaned["line_id"].is_unique
    assert cleaned["order_id"].notna().all()
    assert cleaned["order_id"].astype(str).str.strip().ne("").all()
    assert pd.to_datetime(cleaned["sale_date"], errors="coerce").notna().all()
    assert (cleaned["quantity"] > 0).all()
    assert (cleaned["list_unit_price"] > 0).all()
    assert cleaned["discount_pct"].between(0, 100).all()
    # Every removed/quarantined defect must remain visible in the issue register.
    assert len(issue_report) >= 1


def test_t12_database_loader_returns_20000_by_38_and_loads_under_three_seconds():
    db_module = pytest.importorskip("src.db")
    import time

    timings = []
    frame = None
    for _ in range(3):
        started = time.perf_counter()
        frame = db_module.load_analysis_data(DB_PATH)
        timings.append(time.perf_counter() - started)
    assert isinstance(frame, pd.DataFrame)
    assert frame.shape == (20000, 38)
    assert sorted(timings)[1] < 3.0
