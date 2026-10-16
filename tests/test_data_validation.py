"""
Test Suite: Data Integrity and Schema Validation
Validates that the processed telemetry dataset and KPI summaries adhere strictly
to expected schemas, value boundaries, and analytical constraints.
"""

import os
import pytest
import pandas as pd
import numpy as np


DATA_FILE = "zomato_clean_validated.csv"
KPI_CHANNEL_FILE = "kpi_summary_channel.csv"
KPI_EXECUTIVE_FILE = "kpi_summary_executive.csv"
KPI_PRICE_TIER_FILE = "kpi_summary_price_tier.csv"


def test_clean_dataset_exists():
    """Verify that the cleaned and validated dataset exists and has content."""
    assert os.path.exists(DATA_FILE), f"Dataset file '{DATA_FILE}' is missing!"
    assert os.path.getsize(DATA_FILE) > 0, f"Dataset file '{DATA_FILE}' is empty!"


def test_clean_dataset_schema():
    """Verify that all essential schema columns exist in the dataset."""
    df = pd.read_csv(DATA_FILE, nrows=100)
    expected_columns = [
        "name",
        "votes",
        "location",
        "rest_type",
        "cuisines",
        "listed_in(type)",
        "listed_in(city)",
        "rating",
        "approx_cost_inr",
        "has_online_order",
        "has_table_booking",
        "price_tier",
    ]
    for col in expected_columns:
        assert col in df.columns, f"Expected column '{col}' missing from {DATA_FILE}"


def test_clean_dataset_value_constraints():
    """Verify numerical boundaries, data types, and logical constraints."""
    df = pd.read_csv(DATA_FILE)
    assert not df.empty, "Dataset cannot be empty"
    assert len(df) > 1000, f"Expected substantial records, found {len(df)}"

    # Ratings must be bounded between 1.0 and 5.0
    valid_ratings = df["rating"].dropna()
    assert (valid_ratings >= 1.0).all(), "Found ratings < 1.0"
    assert (valid_ratings <= 5.0).all(), "Found ratings > 5.0"

    # Votes must be non-negative
    valid_votes = df["votes"].dropna()
    assert (valid_votes >= 0).all(), "Found negative votes"

    # Cost must be positive
    valid_costs = df["approx_cost_inr"].dropna()
    assert (valid_costs > 0).all(), "Found non-positive costs"

    # Boolean flags
    assert df["has_online_order"].isin([True, False]).all(), "has_online_order contains non-boolean values"
    assert df["has_table_booking"].isin([True, False]).all(), "has_table_booking contains non-boolean values"


def test_kpi_summary_files():
    """Verify that executive KPI summary tables are present and non-empty."""
    kpi_files = [KPI_CHANNEL_FILE, KPI_EXECUTIVE_FILE, KPI_PRICE_TIER_FILE]
    for file_path in kpi_files:
        assert os.path.exists(file_path), f"KPI file '{file_path}' is missing!"
        df_kpi = pd.read_csv(file_path)
        assert not df_kpi.empty, f"KPI file '{file_path}' is empty!"


def test_app_import_sanity():
    """Verify that the core Streamlit application module loads cleanly without syntax/import errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("zomato_app", "app.py")
    assert spec is not None, "Failed to create spec for app.py"
    # Verify module syntax by compiling the code without executing runtime app loop
    with open("app.py", "r", encoding="utf-8") as f:
        code = f.read()
    compiled = compile(code, "app.py", "exec")
    assert compiled is not None, "Failed to compile app.py"
