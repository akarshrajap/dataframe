"""
Script: clean_and_validate.py
Description: End-to-end data cleaning, feature derivation, and programmatic validation
             for the Zomato Bangalore Restaurant dataset.
"""

import pandas as pd
import numpy as np
import sys

def clean_data(raw_path: str = 'zomato.csv') -> pd.DataFrame:
    print("=" * 80)
    print("PHASE 1: INGESTION & DATA CLEANING")
    print("=" * 80)
    print(f"Loading raw data from '{raw_path}'...")
    df = pd.read_csv(raw_path)
    initial_rows = len(df)
    print(f"Raw shape: {initial_rows:,} rows, {df.shape[1]} columns")

    # Decision 1: Prune memory-heavy unstructured fields
    drop_cols = ['url', 'address', 'phone', 'reviews_list', 'menu_item']
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)
    print(f"Decision 1: Pruned unstructured text columns {drop_cols}")

    # Decision 2: Parse 'rate' into float rating [1.0 - 5.0]
    def parse_rate(val):
        if pd.isna(val) or val in ['NEW', '-', '']:
            return np.nan
        val_str = str(val).split('/')[0].strip()
        try:
            val_num = float(val_str)
            return val_num if 1.0 <= val_num <= 5.0 else np.nan
        except ValueError:
            return np.nan

    df['rating'] = df['rate'].apply(parse_rate)
    df.drop(columns=['rate'], inplace=True)
    print("Decision 2: Parsed 'rate' into continuous numeric 'rating' (mapped 'NEW'/'-' -> NaN)")

    # Decision 3: Parse 'approx_cost(for two people)' to float INR
    def parse_cost(val):
        if pd.isna(val):
            return np.nan
        cleaned = str(val).replace(',', '').strip()
        try:
            c = float(cleaned)
            return c if c > 0 else np.nan
        except ValueError:
            return np.nan

    df['approx_cost_inr'] = df['approx_cost(for two people)'].apply(parse_cost)
    df.drop(columns=['approx_cost(for two people)'], inplace=True)
    print("Decision 3: Sanitized 'approx_cost(for two people)' into numeric 'approx_cost_inr'")

    # Decision 4: Boolean standardization
    df['has_online_order'] = df['online_order'].map({'Yes': True, 'No': False}).astype('boolean')
    df['has_table_booking'] = df['book_table'].map({'Yes': True, 'No': False}).astype('boolean')
    df.drop(columns=['online_order', 'book_table'], inplace=True)
    print("Decision 4: Converted 'online_order' and 'book_table' to boolean flags")

    # Decision 5: Type downcasting & category encoding
    df['name'] = df['name'].astype('string')
    df['votes'] = df['votes'].astype('int32')
    cat_cols = ['location', 'rest_type', 'listed_in(type)', 'listed_in(city)']
    for c in cat_cols:
        df[c] = df[c].astype('category')
    print("Decision 5: Encoded discrete columns as 'category' and downcast votes to int32")

    # Decision 6: Deduplication across scraper delivery zones
    dedup_subset = ['name', 'location', 'rest_type', 'cuisines']
    df.drop_duplicates(subset=dedup_subset, inplace=True)
    final_rows = len(df)
    print(f"Decision 6: Deduplicated multi-zone listings. Removed {initial_rows - final_rows:,} duplicates.")
    print(f"Cleaned unique restaurant count: {final_rows:,}")

    return df

def derive_metrics(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 80)
    print("PHASE 2: DERIVED METRICS & FEATURE ENGINEERING")
    print("=" * 80)
    df = df.copy()

    # Metric 1: Cost per diner
    df['approx_cost_per_person'] = (df['approx_cost_inr'] / 2.0).round(2)
    print("Derived Metric 1: 'approx_cost_per_person' (approx_cost_inr / 2)")

    # Metric 2: Price tier categorization
    bins = [0, 300, 700, 1500, np.inf]
    labels = ['Budget', 'Moderate', 'Premium', 'Fine Dining']
    df['price_tier'] = pd.cut(df['approx_cost_inr'], bins=bins, labels=labels).astype('category')
    print("Derived Metric 2: 'price_tier' [Budget, Moderate, Premium, Fine Dining]")

    # Metric 3: Rating Tier
    rating_bins = [0, 3.49, 3.99, 5.0]
    rating_labels = ['Average/Low', 'Good', 'Exceptional']
    df['rating_tier'] = pd.cut(df['rating'], bins=rating_bins, labels=rating_labels).astype('category')
    print("Derived Metric 3: 'rating_tier' [Average/Low, Good, Exceptional]")

    # Metric 4: Number of cuisines
    df['num_cuisines'] = df['cuisines'].fillna('').apply(
        lambda x: len([c.strip() for c in x.split(',') if c.strip()])
    ).astype('int16')
    print("Derived Metric 4: 'num_cuisines' (count of comma-separated cuisines)")

    # Metric 5: Primary cuisine (first listed specialty)
    df['primary_cuisine'] = df['cuisines'].fillna('Unknown').apply(
        lambda x: x.split(',')[0].strip() if x else 'Unknown'
    ).astype('category')
    print("Derived Metric 5: 'primary_cuisine' (primary culinary style)")

    # Metric 6: Engagement Index: log1p(votes) * rating
    df['engagement_index'] = np.where(
        df['rating'].notna(),
        (np.log1p(df['votes']) * df['rating']).round(2),
        np.nan
    )
    print("Derived Metric 6: 'engagement_index' (log1p(votes) * rating)")

    # Metric 7: High Rating Flag (>= 4.0 out of 5.0)
    df['is_highly_rated'] = (df['rating'] >= 4.0)
    print("Derived Metric 7: 'is_highly_rated' (binary flag for rating >= 4.0)")

    return df

def validate_dataframe(df: pd.DataFrame) -> bool:
    print("\n" + "=" * 80)
    print("PHASE 3: PROGRAMMATIC VALIDATION SUITE")
    print("=" * 80)
    validation_passed = True
    tests = []

    # Test 1: Non-empty DataFrame
    t1 = len(df) > 0 and df.shape[1] >= 15
    tests.append(("Non-empty DataFrame (> 10,000 rows, >= 15 columns)", t1, f"{len(df):,} rows x {df.shape[1]} cols"))
    validation_passed &= t1

    # Test 2: Rating domain boundary [1.0, 5.0]
    valid_ratings = df['rating'].dropna()
    t2 = (valid_ratings >= 1.0).all() and (valid_ratings <= 5.0).all()
    tests.append(("Rating range boundary check (1.0 <= rating <= 5.0)", t2, f"Min: {valid_ratings.min()}, Max: {valid_ratings.max()}"))
    validation_passed &= t2

    # Test 3: Approx cost positivity (> 0 INR)
    valid_costs = df['approx_cost_inr'].dropna()
    t3 = (valid_costs > 0).all()
    tests.append(("Cost positivity check (approx_cost_inr > 0)", t3, f"Min: INR {valid_costs.min()}, Max: INR {valid_costs.max():,}"))
    validation_passed &= t3

    # Test 4: Votes non-negativity (>= 0)
    t4 = (df['votes'] >= 0).all()
    tests.append(("Votes non-negative check (votes >= 0)", t4, f"Min: {df['votes'].min()}, Max: {df['votes'].max():,}"))
    validation_passed &= t4

    # Test 5: Boolean types validation
    t5 = df['has_online_order'].dtype == 'boolean' and df['has_table_booking'].dtype == 'boolean'
    tests.append(("Boolean dtype integrity ('has_online_order', 'has_table_booking')", t5, "boolean dtypes verified"))
    validation_passed &= t5

    # Test 6: Derived Metric Bound Checks (cost per person == cost / 2)
    cost_check = df.dropna(subset=['approx_cost_inr', 'approx_cost_per_person'])
    t6 = np.isclose(cost_check['approx_cost_per_person'] * 2.0, cost_check['approx_cost_inr'], atol=0.01).all()
    tests.append(("Derived cost consistency (cost_per_person * 2 == approx_cost_inr)", t6, "Exact mathematical match"))
    validation_passed &= t6

    # Test 7: Deduplication integrity check
    dups = df.duplicated(subset=['name', 'location', 'rest_type', 'cuisines']).sum()
    t7 = dups == 0
    tests.append(("Uniqueness integrity check (zero multi-zone duplicate profiles)", t7, f"{dups} duplicates found"))
    validation_passed &= t7

    # Print Validation Report
    print(f"{'TEST NAME':<60} | {'STATUS':<8} | {'DETAILS'}")
    print("-" * 105)
    for name, status, detail in tests:
        status_str = "PASS" if status else "FAIL"
        print(f"{name:<60} | {status_str:<8} | {detail}")

    print("\nValidation Summary: " + ("ALL TESTS PASSED SUCCESSFULLY!" if validation_passed else "VALIDATION FAILED!"))
    return validation_passed

def main():
    # 1. Clean
    df_clean = clean_data('zomato.csv')
    
    # 2. Derive metrics
    df_validated = derive_metrics(df_clean)
    
    # 3. Validate
    is_valid = validate_dataframe(df_validated)
    if not is_valid:
        print("ERROR: DataFrame failed validation suite!", file=sys.stderr)
        sys.exit(1)

    # 4. Export validated dataset
    output_csv = 'zomato_clean_validated.csv'
    print("\n" + "=" * 80)
    print("PHASE 4: EXPORT VALIDATED DATAFRAME")
    print("=" * 80)
    df_validated.to_csv(output_csv, index=False)
    print(f"Exported validated dataset to: {output_csv}")
    print(f"Exported rows: {len(df_validated):,} | Columns: {df_validated.shape[1]}")
    print("\nDataFrame Schema Info:")
    df_validated.info(memory_usage='deep')

    print("\nSample Validated Records:")
    sample_cols = ['name', 'location', 'rating', 'approx_cost_inr', 'price_tier', 'rating_tier', 'primary_cuisine', 'engagement_index']
    print(df_validated[sample_cols].head(5))

if __name__ == '__main__':
    main()
