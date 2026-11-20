"""Conservative cleaning for sales-line records."""

import numpy as np

from src.validation import _issue_report, _sales_line_issue_masks


def clean_sales_lines(df):
    """Exclude defective rows without repairing or otherwise changing their values."""
    issue_masks = _sales_line_issue_masks(df)
    invalid_rows = np.zeros(len(df), dtype=bool)
    for mask in issue_masks.values():
        invalid_rows |= mask

    cleaned = df.iloc[~invalid_rows].copy()
    return cleaned, _issue_report(issue_masks)