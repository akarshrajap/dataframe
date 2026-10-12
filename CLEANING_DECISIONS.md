# Data Cleaning Decisions & Validated Metrics Specification

This document details the cleaning methodology, data modeling decisions, derived metrics formulations, and automated validation suite implemented in [`clean_and_validate.py`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/clean_and_validate.py) for the Zomato Bangalore Restaurant dataset.

---

## 1. Summary of Cleaning Decisions

| # | Feature / Field | Raw State | Cleaned / Target State | Rationale & Trade-off |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `url`, `address`, `phone`, `reviews_list`, `menu_item` | High-overhead text strings (535+ MB) | **Pruned / Dropped** | These columns represent 96% of the raw in-memory size. For restaurant metadata and business analytics, customer review paragraphs and menu dumps introduce unnecessary RAM pressure without contributing to tabular modeling. |
| **2** | `rate` | Dirty strings: `'4.1/5'`, `'3.9 /5'`, `'NEW'`, `'-'`, `NaN` | `rating` (`float64`, range `[1.0, 5.0]`) | Extracted the numeric numerator. Unrated entities (`'NEW'`, `'-'`) are explicitly preserved as `NaN` rather than imputed with `0.0` or mean to avoid biasing downstream restaurant performance calculations. |
| **3** | `approx_cost(for two people)` | String formatted with comma separators (`'1,200'`, `'800'`) | `approx_cost_inr` (`float64`, INR) | Commas stripped and cast to continuous numeric format for cost modeling, affordability binning, and arithmetic calculations. |
| **4** | `online_order`, `book_table` | String binary indicators (`'Yes'` / `'No'`) | `has_online_order`, `has_table_booking` (`boolean`) | Converted to native pandas nullable booleans (`boolean`), enabling efficient boolean masking, logical indexing, and 8x memory reduction compared to Python strings. |
| **5** | Discrete categorical attributes (`location`, `rest_type`, `listed_in(type)`, `city`) | High-cardinality repetitive strings | `category` dtypes | Low cardinality categories encoded as integer pointers, speeding up `groupby` aggregations and reducing memory footprint. |
| **6** | Scraper multi-zone duplicates | 51,717 records with same restaurant listed across multiple delivery zones | **Deduplicated unique entities (12,924 rows)** | The scraper recorded the same physical venue multiple times under each neighboring delivery area (`listed_in(city)`). Deduplicating by `['name', 'location', 'rest_type', 'cuisines']` eliminates 38,793 duplicate rows, ensuring per-restaurant metrics reflect physical establishment reality. |

---

## 2. Derived Metrics & Feature Engineering

The following derived metrics were engineered to support downstream analysis and machine learning:

### 1. `approx_cost_per_person`
- **Formula:** $\frac{\text{approx\_cost\_inr}}{2}$
- **Purpose:** Normalizes dining expenditure on an individual basis.
- **Dtype:** `float64`

### 2. `price_tier`
- **Definition:** Categorical tiering based on total cost for two:
  - `Budget`: $\le \text{INR } 300$
  - `Moderate`: $\text{INR } 301 - \text{INR } 700$
  - `Premium`: $\text{INR } 701 - \text{INR } 1,500$
  - `Fine Dining`: $> \text{INR } 1,500$
- **Dtype:** `category` (ordered)

### 3. `rating_tier`
- **Definition:** Performance segmentation based on customer ratings:
  - `Average/Low`: $< 3.50$
  - `Good`: $3.50 - 3.99$
  - `Exceptional`: $\ge 4.00$
- **Dtype:** `category` (ordered)

### 4. `num_cuisines`
- **Formula:** Count of distinct cuisines parsed from comma-separated string `cuisines`.
- **Purpose:** Quantifies menu diversity and culinary specialization.
- **Dtype:** `int16`

### 5. `primary_cuisine`
- **Definition:** The leading cuisine listed in the establishment profile (e.g., `'North Indian'`, `'Cafe'`, `'South Indian'`).
- **Purpose:** Primary category for cuisine-based segment comparisons.
- **Dtype:** `category`

### 6. `engagement_index`
- **Formula:** $\ln(1 + \text{votes}) \times \text{rating}$
- **Purpose:** Balances sample size reliability (number of customer reviews) with sentiment score (rating). Prevents restaurants with a single 5.0 rating from outranking venues with a 4.8 rating across 5,000 reviews.
- **Dtype:** `float64`

### 7. `is_highly_rated`
- **Formula:** $\text{rating} \ge 4.0$
- **Purpose:** Binary indicator for top-tier establishments.
- **Dtype:** `bool`

---

## 3. Automated Validation Suite

[`clean_and_validate.py`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/clean_and_validate.py) enforces 7 programmatic integrity tests prior to dataset export:

| Test Name | Validation Rule | Actual Result | Status |
| :--- | :--- | :--- | :--- |
| **Dataset Completeness** | Rows $> 10,000$ and Columns $\ge 15$ | 12,924 rows $\times$ 19 columns | **PASS** |
| **Rating Boundary Check** | $1.0 \le \text{rating} \le 5.0$ (or null) | Min: 1.8, Max: 4.9 | **PASS** |
| **Cost Positivity Check** | $\text{approx\_cost\_inr} > 0$ (or null) | Min: INR 40.0, Max: INR 6,000.0 | **PASS** |
| **Votes Non-Negativity** | $\text{votes} \ge 0$ | Min: 0, Max: 16,345 | **PASS** |
| **Boolean Dtype Integrity** | `has_online_order` & `has_table_booking` must be boolean | `boolean` dtype verified | **PASS** |
| **Mathematical Consistency** | $\text{approx\_cost\_per\_person} \times 2 == \text{approx\_cost\_inr}$ | Exact float match | **PASS** |
| **Uniqueness Check** | Duplicates on `[name, location, rest_type, cuisines] == 0` | 0 duplicate records | **PASS** |

---

## 4. Validated Dataset Artifact

The resulting validated DataFrame is persisted as:
- **File:** [`zomato_clean_validated.csv`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/zomato_clean_validated.csv)
- **Rows:** 12,924 unique establishments
- **Columns:** 19 clean & engineered features
- **File Size:** ~2.3 MB
