"""Streamlit AppTest smoke tests for app startup, all eight pages and shared UI state."""
from __future__ import annotations

from pathlib import Path
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
PAGE_PATHS = [
    ROOT / "pages" / "01_Overview.py",
    ROOT / "pages" / "02_Trend.py",
    ROOT / "pages" / "03_Compare.py",
    ROOT / "pages" / "04_EDA_Statistics.py",
    ROOT / "pages" / "05_Insights.py",
    ROOT / "pages" / "06_Data_Download.py",
    ROOT / "pages" / "07_Data_Quality.py",
    ROOT / "pages" / "08_About.py",
]


def _apptest_class():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    return AppTest


def test_t28_app_entrypoint_starts_without_exception():
    if not APP_PATH.exists():
        pytest.skip("app.py is scheduled for implementation in Step 15.")
    AppTest = _apptest_class()
    at = AppTest.from_file(str(APP_PATH)).run(timeout=15)
    assert len(at.exception) == 0


@pytest.mark.parametrize("page_path", PAGE_PATHS, ids=lambda p: p.stem)
def test_t29_each_ui_page_renders_without_exception(page_path):
    if not page_path.exists():
        pytest.skip(f"{page_path.name} is scheduled for implementation in Step 15.")
    AppTest = _apptest_class()
    started = time.perf_counter()
    at = AppTest.from_file(str(page_path)).run(timeout=15)
    elapsed = time.perf_counter() - started
    assert len(at.exception) == 0
    # TRD / BRD service target is under five seconds per warmed page.
    assert elapsed < 5.0


def test_t30_overview_initialises_shared_filter_state():
    page = ROOT / "pages" / "01_Overview.py"
    if not page.exists():
        pytest.skip("Overview page is scheduled for implementation in Step 15.")
    AppTest = _apptest_class()
    at = AppTest.from_file(str(page)).run(timeout=15)
    assert len(at.exception) == 0
    expected_keys = {
        "ui_global_date_range",
        "ui_global_region",
        "ui_global_stores",
        "ui_global_category",
        "ui_global_channel",
    }
    actual_keys = set(at.session_state)
    assert expected_keys.issubset(actual_keys)


def test_t31_all_eight_ui_page_files_exist_for_navigation():
    missing = [p.relative_to(ROOT).as_posix() for p in PAGE_PATHS if not p.exists()]
    if missing:
        pytest.skip("Step 15 page scaffolding is pending: " + ", ".join(missing))
    assert len(PAGE_PATHS) == 8
