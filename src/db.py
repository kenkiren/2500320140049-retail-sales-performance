"""Read-only access to the canonical sales analysis view."""

import sqlite3
from pathlib import Path

import pandas as pd


def load_analysis_data(db_path=None):
    """Load the canonical 20,000-row analysis view without modifying its database."""
    path = (
        Path(db_path)
        if db_path is not None
        else Path(__file__).resolve().parents[1] / "data" / "app.db"
    )
    database_uri = path.expanduser().resolve().as_uri() + "?mode=ro"

    connection = sqlite3.connect(database_uri, uri=True)
    try:
        frame = pd.read_sql_query("SELECT * FROM v_sales_analysis", connection)
    finally:
        connection.close()

    if frame.shape != (20_000, 38):
        raise ValueError(
            "Expected v_sales_analysis to contain 20,000 rows and 38 columns; "
            f"got {frame.shape[0]} rows and {frame.shape[1]} columns."
        )
    return frame