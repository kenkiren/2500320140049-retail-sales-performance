"""Validation rules for sales-line records."""

import re
from datetime import date, datetime

import numpy as np
import pandas as pd


_REQUIRED_COLUMNS = (
    "line_id",
    "order_id",
    "sale_date",
    "store_id",
    "product_id",
    "customer_id",
    "quantity",
    "list_unit_price",
    "discount_pct",
    "selling_unit_price",
    "payment_mode",
    "channel",
)
_FOREIGN_KEY_COLUMNS = ("store_id", "product_id", "customer_id")
_ENUM_VALUES = {
    "payment_mode": {"Cash", "Card", "UPI", "Wallet"},
    "channel": {"In-store", "Online"},
}


def _blank_values(values):
    blank = values.isna().to_numpy(dtype=bool)
    text = values.astype("string").str.strip().eq("").fillna(False).to_numpy(dtype=bool)
    return blank | text


def _numeric_values(values):
    converted = pd.to_numeric(values, errors="coerce")
    return converted.to_numpy(dtype="float64", na_value=np.nan)


def _valid_iso_date(value):
    if isinstance(value, np.datetime64):
        value = pd.Timestamp(value)
    if isinstance(value, pd.Timestamp):
        return not pd.isna(value) and value == value.normalize()
    if isinstance(value, datetime):
        return value.time() == datetime.min.time()
    if isinstance(value, date):
        return True
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _sales_line_issue_masks(df):
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    row_count = len(df)
    issues = {}

    def add(issue_type, mask):
        mask = np.asarray(mask, dtype=bool)
        if mask.shape != (row_count,):
            raise ValueError(f"Invalid validation mask for {issue_type}")
        if mask.any():
            if issue_type in issues:
                issues[issue_type] |= mask
            else:
                issues[issue_type] = mask

    available_required = [column for column in _REQUIRED_COLUMNS if column in df]
    if available_required:
        add(
            "blank_required",
            np.logical_or.reduce(
                [_blank_values(df[column]) for column in available_required]
            ),
        )

    if "line_id" in df:
        line_ids = df["line_id"]
        line_id_blank = _blank_values(line_ids)
        add(
            "duplicate_line_id",
            line_ids.duplicated(keep=False).to_numpy(dtype=bool) & ~line_id_blank,
        )
        values = _numeric_values(line_ids)
        non_integer = np.isfinite(values) & (values != np.floor(values))
        invalid = (
            (~line_id_blank & ~np.isfinite(values))
            | non_integer
            | (np.isfinite(values) & (values <= 0))
        )
        add("invalid_line_id", invalid)

    if "sale_date" in df:
        values = df["sale_date"]
        blank = _blank_values(values)
        add(
            "invalid_date",
            np.array(
                [
                    not is_blank and not _valid_iso_date(value)
                    for value, is_blank in zip(values, blank)
                ],
                dtype=bool,
            ),
        )

    numeric = {}
    for column in (
        "quantity",
        "list_unit_price",
        "discount_pct",
        "selling_unit_price",
        *_FOREIGN_KEY_COLUMNS,
    ):
        if column in df:
            numeric[column] = _numeric_values(df[column])

    if "quantity" in numeric:
        values = numeric["quantity"]
        finite = np.isfinite(values)
        blank = _blank_values(df["quantity"])
        add("invalid_quantity", ~blank & ~finite)
        add("non_positive_quantity", finite & (values <= 0))
        add(
            "invalid_quantity",
            finite & (values != np.floor(values)),
        )

    if "list_unit_price" in numeric:
        values = numeric["list_unit_price"]
        finite = np.isfinite(values)
        blank = _blank_values(df["list_unit_price"])
        add("invalid_list_price", ~blank & ~finite)
        add("non_positive_price", finite & (values <= 0))

    if "discount_pct" in numeric:
        values = numeric["discount_pct"]
        finite = np.isfinite(values)
        blank = _blank_values(df["discount_pct"])
        add("invalid_discount", ~blank & ~finite)
        add("discount_out_of_range", finite & ((values < 0) | (values > 100)))

    if "selling_unit_price" in numeric:
        values = numeric["selling_unit_price"]
        finite = np.isfinite(values)
        blank = _blank_values(df["selling_unit_price"])
        add("invalid_selling_price", ~blank & ~finite)
        invalid = finite & (values < 0)
        if "list_unit_price" in numeric:
            list_prices = numeric["list_unit_price"]
            invalid |= finite & np.isfinite(list_prices) & (values > list_prices)
        add("invalid_selling_price", invalid)

    for column in _FOREIGN_KEY_COLUMNS:
        if column not in numeric:
            continue
        values = numeric[column]
        finite = np.isfinite(values)
        blank = _blank_values(df[column])
        invalid = (
            (~blank & ~finite)
            | (finite & (values <= 0))
            | (finite & (values != np.floor(values)))
        )
        add("invalid_foreign_key", invalid)

    if "payment_mode" in df:
        values = df["payment_mode"]
        valid = values.astype("string").str.strip().isin(
            _ENUM_VALUES["payment_mode"]
        ).fillna(False)
        add(
            "invalid_payment_mode",
            ~_blank_values(values) & ~valid.to_numpy(dtype=bool),
        )

    if "channel" in df:
        values = df["channel"]
        valid = values.astype("string").str.strip().isin(
            _ENUM_VALUES["channel"]
        ).fillna(False)
        add(
            "invalid_channel",
            ~_blank_values(values) & ~valid.to_numpy(dtype=bool),
        )

    if all(
        column in numeric
        for column in ("list_unit_price", "discount_pct", "selling_unit_price")
    ):
        list_prices = numeric["list_unit_price"]
        discounts = numeric["discount_pct"]
        selling_prices = numeric["selling_unit_price"]
        valid_values = (
            np.isfinite(list_prices)
            & np.isfinite(discounts)
            & np.isfinite(selling_prices)
        )
        mismatch = np.abs(
            selling_prices - list_prices * (1 - discounts / 100)
        ) > 0.02
        add("pricing_mismatch", valid_values & mismatch)

    return issues


def _issue_report(issue_masks):
    rows = [
        {
            "issue_type": issue_type,
            "row_count": int(mask.sum()),
            "row_positions": np.flatnonzero(mask).tolist(),
        }
        for issue_type, mask in issue_masks.items()
    ]
    return pd.DataFrame(rows, columns=["issue_type", "row_count", "row_positions"])


def validate_sales_lines(df):
    """Return counts and source row positions for every detected sales-line defect."""
    return _issue_report(_sales_line_issue_masks(df))