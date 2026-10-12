"""
Script: inspect_zomato.py
Description: End-to-end pipeline to inspect raw Zomato Bangalore Restaurant data
             and convert it into an analysis-ready pandas DataFrame.
"""

import pandas as pd
import numpy as np

def inspect_and_prepare_zomato(csv_path: str = 'zomato.csv'):
    print("=" * 80)
    print("STEP 1: LOAD RAW ZOMATO DATASET")
    print("=" * 80)
    # Load dataset
    print(f"Reading {csv_path} ...")
    df_raw = pd.read_csv(csv_path)
    print(f"Raw Dataset Shape: {df_raw.shape[0]:,} rows x {df_raw.shape[1]} columns\n")
    print("Raw DataFrame Preview (first 3 rows):")
    cols_preview = ['name', 'online_order', 'book_table', 'rate', 'votes', 'location', 'approx_cost(for two people)']
    print(df_raw[cols_preview].head(3))

    print("\n" + "=" * 80)
    print("STEP 2: EXAMINE RAW SCHEMA & DATA TYPES")
    print("=" * 80)
    print("Raw dtypes and Non-Null Counts:")
    df_raw.info(memory_usage='deep')

    print("\n" + "=" * 80)
    print("STEP 3: ANALYZE MISSING DATA & DATA ANOMALIES")
    print("=" * 80)
    missing_summary = pd.DataFrame({
        'Missing Count': df_raw.isnull().sum(),
        'Missing (%)': (df_raw.isnull().mean() * 100).round(2)
    })
    print(missing_summary)

    print("\nUnique anomalies in 'rate' (e.g. 'NEW', '-', '/5'):")
    print(df_raw['rate'].value_counts(dropna=False).head(10))

    print("\n" + "=" * 80)
    print("STEP 4: INSPECT CATEGORICAL & STATUS VALUES")
    print("=" * 80)
    print("Online Order Acceptance:")
    print(df_raw['online_order'].value_counts(dropna=False))

    print("\nTable Booking Availability:")
    print(df_raw['book_table'].value_counts(dropna=False))

    print("\nTop 5 Restaurant Types:")
    print(df_raw['rest_type'].value_counts(dropna=False).head(5))

    print("\nTop 5 Service Types (listed_in(type)):")
    print(df_raw['listed_in(type)'].value_counts(dropna=False).head(5))

    print("\n" + "=" * 80)
    print("STEP 5: TRANSFORM RAW DATA TO ANALYSIS-READY DATAFRAME")
    print("=" * 80)
    df_clean = df_raw.copy()

    # 1. Drop high-overhead unstructured text columns if performing tabular restaurant analytics
    # (or keep clean reference)
    drop_unstructured = ['url', 'address', 'phone', 'reviews_list', 'menu_item']
    df_clean.drop(columns=[c for c in drop_unstructured if c in df_clean.columns], inplace=True)

    # 2. Clean 'rate' column: format is '4.1/5', 'NEW', '-', NaN
    def clean_rating(val):
        if pd.isna(val) or val in ['NEW', '-']:
            return np.nan
        val_str = str(val).split('/')[0].strip()
        try:
            return float(val_str)
        except ValueError:
            return np.nan

    df_clean['rating'] = df_clean['rate'].apply(clean_rating)
    df_clean.drop(columns=['rate'], inplace=True)

    # 3. Clean 'approx_cost(for two people)': contains commas like '1,200'
    def clean_cost(val):
        if pd.isna(val):
            return np.nan
        val_str = str(val).replace(',', '').strip()
        try:
            return float(val_str)
        except ValueError:
            return np.nan

    df_clean['approx_cost_inr'] = df_clean['approx_cost(for two people)'].apply(clean_cost)
    df_clean.drop(columns=['approx_cost(for two people)'], inplace=True)

    # 4. Standardize Boolean flags
    df_clean['has_online_order'] = df_clean['online_order'].map({'Yes': True, 'No': False}).astype('boolean')
    df_clean['has_table_booking'] = df_clean['book_table'].map({'Yes': True, 'No': False}).astype('boolean')
    df_clean.drop(columns=['online_order', 'book_table'], inplace=True)

    # 5. Clean Categorical columns
    cat_columns = ['location', 'rest_type', 'listed_in(type)', 'listed_in(city)']
    for col in cat_columns:
        df_clean[col] = df_clean[col].astype('category')

    # 6. Feature Engineering
    # Number of cuisines offered
    df_clean['num_cuisines'] = df_clean['cuisines'].fillna('').apply(
        lambda x: len([c.strip() for c in x.split(',') if c.strip()])
    ).astype('int16')

    # Cost per person (approx_cost_inr / 2)
    df_clean['approx_cost_per_person'] = (df_clean['approx_cost_inr'] / 2.0).round(2)

    # Flag for highly rated restaurants (>= 4.0 rating)
    df_clean['is_highly_rated'] = (df_clean['rating'] >= 4.0)

    # 7. Deduplicate restaurant listings (identifying duplicates by name, location, and rest_type)
    initial_rows = len(df_clean)
    df_clean.drop_duplicates(subset=['name', 'location', 'rest_type', 'cuisines'], inplace=True)
    deduped_rows = len(df_clean)
    print(f"Deduplication: removed {initial_rows - deduped_rows:,} duplicate listings across city delivery zones.")
    print(f"Cleaned unique restaurant profiles: {deduped_rows:,}")

    print("\nAnalysis-Ready DataFrame Schema:")
    df_clean.info(memory_usage='deep')

    print("\nAnalysis-Ready DataFrame Sample:")
    print(df_clean[['name', 'location', 'rating', 'votes', 'approx_cost_inr', 'has_online_order', 'num_cuisines']].head(5))

    print("\n" + "=" * 80)
    print("STEP 6: SUMMARY ANALYTICAL METRICS")
    print("=" * 80)
    numeric_summary = df_clean[['rating', 'votes', 'approx_cost_inr', 'approx_cost_per_person', 'num_cuisines']].describe().round(2)
    print(numeric_summary)

    print("\nOnline Order vs. Average Rating & Cost:")
    print(df_clean.groupby('has_online_order')[['rating', 'approx_cost_inr', 'votes']].agg(['mean', 'median']).round(2))

    return df_clean

if __name__ == '__main__':
    df_zomato_ready = inspect_and_prepare_zomato('zomato.csv')
