"""
Script: inspect_workflow_runs.py
Description: End-to-end pipeline to inspect raw workflow telemetry data
             and convert it into an analysis-ready pandas DataFrame.
"""

import pandas as pd
import numpy as np

def inspect_and_prepare_telemetry(csv_path: str):
    print("=" * 80)
    print("STEP 1: LOAD RAW TELEMETRY CSV")
    print("=" * 80)
    df_raw = pd.read_csv(csv_path)
    print(f"Dataset Shape: {df_raw.shape[0]} rows x {df_raw.shape[1]} columns\n")
    print("Raw DataFrame Preview:")
    print(df_raw.head())

    print("\n" + "=" * 80)
    print("STEP 2: EXAMINE RAW SCHEMA & DATA TYPES")
    print("=" * 80)
    print("DataFrame Info (dtypes & non-null counts):")
    df_raw.info()
    
    print("\nSummary of dtypes:")
    print(df_raw.dtypes)

    print("\n" + "=" * 80)
    print("STEP 3: ANALYZE MISSING DATA (NULL VALUES)")
    print("=" * 80)
    missing_summary = pd.DataFrame({
        'Missing Values': df_raw.isnull().sum(),
        'Percentage (%)': (df_raw.isnull().mean() * 100).round(2)
    })
    print(missing_summary)

    print("\n" + "=" * 80)
    print("STEP 4: INSPECT STATUS & CONCLUSION VALUES")
    print("=" * 80)
    print("Status counts:")
    print(df_raw['status'].value_counts(dropna=False))
    
    print("\nConclusion counts:")
    print(df_raw['conclusion'].value_counts(dropna=False))

    print("\nTrigger Event counts:")
    print(df_raw['trigger_event'].value_counts(dropna=False))

    print("\n" + "=" * 80)
    print("STEP 5: TRANSFORM RAW DATA TO ANALYSIS-READY DATAFRAME")
    print("=" * 80)
    df_clean = df_raw.copy()

    # 1. Convert timestamps to datetime (UTC timezone-aware)
    timestamp_cols = ['created_at', 'started_at', 'completed_at']
    for col in timestamp_cols:
        df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce', utc=True)

    # 2. Derive engineered telemetry features:
    # Queue latency (wait time before execution starts in seconds)
    df_clean['queue_latency_sec'] = (df_clean['started_at'] - df_clean['created_at']).dt.total_seconds()

    # Execution duration (active run time in seconds)
    df_clean['duration_sec'] = (df_clean['completed_at'] - df_clean['started_at']).dt.total_seconds()

    # 3. Categorical encoding for low-cardinality discrete columns
    cat_cols = ['pipeline', 'trigger_event', 'status', 'conclusion']
    for col in cat_cols:
        df_clean[col] = df_clean[col].astype('category')

    # 4. Fill structural missing values vs random missing telemetry
    df_clean['failure_reason'] = df_clean['failure_reason'].fillna('None / Not Failed')

    # 5. Type cast run_id and run_attempt
    df_clean['run_id'] = df_clean['run_id'].astype('string')
    df_clean['run_attempt'] = df_clean['run_attempt'].astype('int16')

    print("\nAnalysis-Ready DataFrame Schema:")
    df_clean.info()

    print("\nAnalysis-Ready Preview with Derived Metrics:")
    cols_to_preview = ['run_id', 'pipeline', 'status', 'conclusion', 'queue_latency_sec', 'duration_sec', 'cpu_utilization_pct', 'memory_used_mb']
    print(df_clean[cols_to_preview])

    print("\n" + "=" * 80)
    print("STEP 6: SUMMARY TELEMETRY STATISTICS")
    print("=" * 80)
    numeric_summary = df_clean[['queue_latency_sec', 'duration_sec', 'cpu_utilization_pct', 'memory_used_mb']].describe().round(2)
    print(numeric_summary)

    return df_clean

if __name__ == '__main__':
    csv_file = 'workflow_runs.csv'
    df_analysis_ready = inspect_and_prepare_telemetry(csv_file)
