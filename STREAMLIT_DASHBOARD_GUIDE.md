# Streamlit Telemetry Analytics Dashboard Guide

This guide details the architecture, dynamic filtering controls, KPI definitions, and local execution for the interactive telemetry dashboard implemented in [`app.py`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/app.py).

---

## 1. Application Architecture & Structure

```
d:\Akarsh\Mysore_pythonDocker\data_analysis/
├── app.py                         # Main Streamlit dashboard application
├── requirements.txt               # Pinned Python package dependencies
├── workflow_telemetry_runs.csv    # Telemetry dataset (120 runs across 6 branches)
├── generate_telemetry_runs.py     # Reproducible telemetry data generator
└── STREAMLIT_DASHBOARD_GUIDE.md   # System architecture and user manual
```

### Key Architectural Patterns in `app.py`:
1. **High-Performance Caching (`@st.cache_data`):**
   - The data ingestion function `load_telemetry_data()` and the multi-criteria slicing function `filter_telemetry()` are cached with `@st.cache_data`.
   - Prevents redundant disk reads and recalculations across UI filter interactions, delivering near-instant $(< 50\text{ms})$ dashboard updates.
2. **Wide Layout & Custom CSS:**
   - Configured via `st.set_page_config(layout="wide")`.
   - Injected custom CSS styles KPI cards, success/failure badges, and tab navigation.
3. **Responsive Multi-Tab Interface:**
   - Organizes diagnostics across three logical tabs:
     - **Tab 1:** Run Duration Trend Timeline
     - **Tab 2:** Pipeline & Workflow Comparison
     - **Tab 3:** Filtered Records Table & Failure Investigation

---

## 2. Dashboard Controls & Sidebar Filters

The dashboard provides sidebar controls that filter metrics and visualizations:

| Filter Control | UI Element | Options / Range | Filter Logic |
| :--- | :--- | :--- | :--- |
| **Date Range** | `st.sidebar.date_input` | Start Date to End Date (`min_value` to `max_value`) | Evaluates `started_at.dt.date` boundaries |
| **Branch** | `st.sidebar.multiselect` | `main`, `develop`, `feature/auth-service`, `feature/ui-refresh`, `release/v2.1`, `hotfix/db-locks` | Filters by branch name (defaults to all if empty) |
| **Workflow** | `st.sidebar.multiselect` | `ci_unit_tests`, `lint_and_build`, `hourly_dbt_run`, `feature_pipeline`, `e2e_playwright`, etc. | Filters by specific CI/CD jobs |
| **Outcome** | `st.sidebar.multiselect` | `success`, `failure`, `timed_out`, `cancelled`, `running` | Filters by execution conclusion |
| **Reset Filters** | `st.sidebar.button` | One-click button | Re-executes `st.rerun()` to restore defaults |

---

## 3. Executive KPI Metric Cards

Computed from the active filtered subset and rendered via `st.columns(5)`:

| KPI Card | Formula / Aggregation | Delta / Subtext Indicator | Business Purpose |
| :--- | :--- | :--- | :--- |
| **Total Runs** | `len(filtered_df)` | `X% of total dataset` | Measures workload volume in the selected window. |
| **Success Rate** | $\left( \frac{N_{\text{success}}}{N_{\text{total}}} \right) \times 100$ | `N Passed` (Green if $\ge 75\%$, Red if $<75\%$) | High-level reliability benchmark. |
| **Avg Duration** | `df['duration_sec'].mean()` | `Median: X s` | Quantifies compute efficiency and pipeline speed. |
| **Avg Queue Delay** | `df['queue_latency_sec'].mean()` | `Max: X s` | Diagnoses runner congestion and scheduling delays. |
| **Failures / Timeouts** | $N_{\text{failure}} + N_{\text{timed\_out}}$ | `X fail \| Y timeout` (Inverse red badge) | Flags broken builds and blocker incidents. |

---

## 4. Interactive Visualizations Connected to Filters

### Tab 1: Run-Duration Trend Timeline
- **Plotly Scatter + Moving Average:** Plots execution durations across timestamps.
- **Outcome Color Palette:**
  - `Success`: Emerald Green (`#22c55e`)
  - `Failure`: Crimson Red (`#ef4444`)
  - `Timed Out`: Orange (`#f97316`)
  - `Cancelled`: Slate Grey (`#94a3b8`)
  - `Running`: Blue (`#3b82f6`)
- **12-Hour Rolling Average:** Dashed trendline tracking latency drift over time.
- **Diagnostics Tooltip:** Displays Run ID, branch, pipeline, duration, queue delay, CPU %, RAM MB, and error traces on hover.

### Tab 2: Pipeline & Workflow Comparison
- **Grouped Box Plots:** Evaluates duration distributions across service pipelines (`backend-api`, `frontend-web`, `data-warehouse`, `ml-service`, `infra-ops`) with overlaid jittered run points.
- **Outcome Donut Chart:** High-level pie breakdown of pass/fail shares.
- **Workflow Ranking Horizontal Bar Chart:** Ranks individual jobs by average runtime (annotated with run sample counts `n=X`).

### Tab 3: Filtered Data Table & Error Logs
- **Searchable, Sortable Table:** Displayed via `st.dataframe` with formatted datetime and progress bar CPU utilization.
- **CSV Data Export:** One-click `st.download_button` to download the filtered cohort as CSV (`telemetry_filtered_YYYYMMDD_HHMMSS.csv`).
- **Failure & Timeout Root Cause Table:** Dedicated failure log showing Run ID, branch, pipeline, and the exact error exception string (e.g., `TestAssertionError`, `DBLockTimeout`, `OutOfMemoryError`).

---

## 5. How to Run Locally

### 1. Install Dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Launch the Streamlit Dashboard:
```powershell
streamlit run app.py
```

The application will start and open automatically at:
- **Local URL:** `http://localhost:8501`
- **Network URL:** `http://<your-ip>:8501`
