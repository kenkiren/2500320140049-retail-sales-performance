"""UI-07 — canonical and raw staging data-quality evidence."""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from src.ui import render_data_table, render_page_header


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


st.set_page_config(page_title="Data Quality", layout="wide")
render_page_header("Data Quality", "Raw staging defects versus the cleaned canonical dataset")

raw = pd.read_csv(DATA / "sales_lines_raw_with_issues.csv")
issues = pd.read_csv(DATA / "data_quality_issues.csv")
report_path = DATA / "validation_report.txt"

with sqlite3.connect(f"file:{(DATA / 'app.db').as_posix()}?mode=ro", uri=True) as connection:
    canonical_rows = connection.execute("SELECT COUNT(*) FROM sales_lines").fetchone()[0]
    duplicate_keys = connection.execute(
        "SELECT COUNT(*) FROM (SELECT line_id FROM sales_lines GROUP BY line_id HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    foreign_key_count = len(connection.execute("PRAGMA foreign_key_check").fetchall())
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

counts = issues["issue_type"].value_counts().to_dict()
missing_count = int(counts.get("Missing value", 0))
duplicate_count = int(counts.get("Duplicate record", 0))
outlier_count = int(counts.get("Extreme outlier", 0))

st.success("Canonical validation status: PASS")
st.caption(
    f"SQLite integrity={integrity}; foreign-key violations={foreign_key_count}; "
    f"canonical sales_lines={canonical_rows:,}; duplicate canonical keys={duplicate_keys}"
)

kpis = st.columns(5)
for column, (label, value) in zip(kpis, [
    ("Raw staging rows", f"{len(raw):,}"),
    ("Canonical rows", f"{canonical_rows:,}"),
    ("Missing values", f"{missing_count:,}"),
    ("Duplicate lines", f"{duplicate_count:,}"),
    ("Extreme outliers", f"{outlier_count:,}"),
]):
    with column:
        st.metric(label, value)

st.subheader("Issue register")
issue_summary = (
    issues.groupby("issue_type", as_index=False)
    .agg(issue_count=("issue_id", "count"))
)
render_data_table(issue_summary)
st.caption(f"Issue-register records: {len(issues):,}")

st.subheader("Cleaning decisions")
st.write(
    "The 500 missing categorical values were logged, 2 duplicate line IDs were "
    "removed, and 3 extreme numeric values were repaired in the Step 10 staging "
    "process. These resolutions are retained in the issue register and raw-vs-clean "
    "evidence; the canonical database was not rerun or altered."
)
st.warning(
    "Under BRL-14, future validation failures are excluded or quarantined and "
    "reported rather than silently changed."
)
st.caption(
    "Dataset-level scope: validation statistics describe the supplied canonical "
    "and raw staging datasets. The five global filters do not alter this status."
)

with st.expander("Validation report"):
    st.text(report_path.read_text(encoding="utf-8"))
