"""Read-only access to the canonical sales analysis view."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


def _read_only_query(query, db_path=None):
    path = (
        Path(db_path)
        if db_path is not None
        else Path(__file__).resolve().parents[1] / "data" / "app.db"
    )
    database_uri = path.expanduser().resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(database_uri, uri=True)) as connection:
        frame = pd.read_sql_query(query, connection)
    return frame


def load_analysis_data(db_path=None):
    """Load the canonical 20,000-row analysis view without modifying its database."""
    frame = _read_only_query("SELECT * FROM v_sales_analysis", db_path)
    if frame.shape != (20_000, 38):
        raise ValueError(
            "Expected v_sales_analysis to contain 20,000 rows and 38 columns; "
            f"got {frame.shape[0]} rows and {frame.shape[1]} columns."
        )
    return frame


def load_store_targets(db_path=None):
    """Load target rows once from the physical store_targets table, read-only."""
    return _read_only_query(
        "SELECT store_id, target_month, target_revenue "
        "FROM store_targets ORDER BY store_id, target_month",
        db_path,
    )


def load_stores(db_path=None):
    """Load store IDs, names and regions from the physical stores table."""
    return _read_only_query(
        "SELECT store_id, store_name, region FROM stores ORDER BY store_id",
        db_path,
    )