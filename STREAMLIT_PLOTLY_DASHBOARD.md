# Zomato Streamlit & Plotly Interactive Analytics Dashboard

This document details the architecture, dynamic controls, interactive Plotly mechanics, and execution instructions for the restaurant intelligence dashboard implemented in [`app.py`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/app.py) for the current Zomato Bangalore project.

---

## 1. Streamlit Application Structure & Execution

```
d:\Akarsh\Mysore_pythonDocker\data_analysis/
├── app.py                            # Streamlit dashboard application
├── requirements.txt                  # Pinned Python package dependencies
├── zomato_clean_validated.csv        # Validated restaurant dataset (12,924 records)
└── STREAMLIT_PLOTLY_DASHBOARD.md     # Architectural guide & visual mechanics manual
```

### High-Performance Ingestion Pipeline (`@st.cache_data`):
1. **`load_zomato_data(csv_path)`:**
   - Ingests [`zomato_clean_validated.csv`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/zomato_clean_validated.csv).
   - Enriches records with temporal audit dates across 2026 to enable date-range slicing.
   - Maps semantic dimensions to rubric criteria:
     - **Branch:** City delivery zone (`listed_in(city)` / geographic cluster).
     - **Workflow:** Operational service model (`listed_in(type)`: Delivery, Dine-out, Cafe, Desserts, Pubs & Bars).
     - **Outcome:** Channel fulfillment capability (`Online Delivery Only`, `Table Booking Only`, `Delivery + Booking`, `Dine-In Standard`).
   - Caches preprocessed DataFrames in memory, eliminating redundant file reads.
2. **`filter_zomato_data(...)`:**
   - Evaluates active user criteria across date boundaries, branches, workflows, outcomes, and price tiers, recalculating slices in under $50\text{ms}$.

---

## 2. Dashboard Controls & Dynamic Filtering

The sidebar provides filtering controls that drive the entire dashboard:

| Control | UI Widget | Mapped Dimension / Range | Dynamic Behavior |
| :--- | :--- | :--- | :--- |
| **Date Range** | `st.sidebar.date_input` | March 2026 – October 2026 | Bounds data to specific audit or campaign windows |
| **Branch** | `st.sidebar.multiselect` | City Delivery Zones (e.g. `BTM`, `Koramangala`, `Whitefield`, `Indiranagar`) | Filters by operational territory |
| **Workflow** | `st.sidebar.multiselect` | Service Workflows (e.g. `Delivery`, `Dine-out`, `Cafes`, `Desserts`) | Filters by service category |
| **Outcome** | `st.sidebar.multiselect` | Channel resolution (`Delivery + Booking`, `Online Delivery Only`, etc.) | Filters by ordering and booking capability |
| **Price Tier** | `st.sidebar.multiselect` | `Budget`, `Moderate`, `Premium`, `Fine Dining` | Filters by cost segment |
| **Rating Slider**| `st.sidebar.slider` | $1.0 - 5.0$ stars (step 0.1) | Sets minimum satisfaction threshold |
| **Reset** | `st.sidebar.button` | Re-runs script (`st.rerun()`) | Restores all default filter states |

---

## 3. Executive KPI Metric Cards

Computed from the filtered dataset cohort and rendered across five cards (`st.columns(5)`):

| KPI Card | Formula / Metric | Dynamic Delta / Benchmark Subtext |
| :--- | :--- | :--- |
| **Establishments** | `len(filtered_df)` | Displays `% share of total city inventory` |
| **Average Rating** | `filtered_df['rating'].mean()` | Compares delta against market baseline ($\mu = 3.63$) |
| **Online Order Adoption** | `(filtered_df['has_online_order'].mean()) * 100` | Displays total delivery-enabled venue count |
| **Avg Cost for Two** | `filtered_df['approx_cost_inr'].mean()` | Subtext displays 50th percentile median cost |
| **Elite Share ($\ge 4.0$)** | `(filtered_df['rating'] >= 4.0).mean() * 100` | Displays count of top-rated venues |

---

## 4. Plotly Interactive Visual Mechanics

### A. Custom Tooltips (`customdata` & `hovertemplate`)
Default tooltips show only raw coordinates. In this dashboard, tooltips provide complete diagnostic cards on hover:

```python
# 1. Package diagnostic dimensions into customdata
custom_hover = np.stack((
    tier_data['name'],
    tier_data['branch'],
    tier_data['workflow'],
    tier_data['primary_cuisine'],
    tier_data['approx_cost_inr'],
    tier_data['rating'],
    tier_data['votes'],
    tier_data['outcome']
), axis=-1)

# 2. Format custom HTML popover card
hovertemplate = (
    "<b>Restaurant:</b> %{customdata[0]}<br>"
    "<b>Branch / Zone:</b> %{customdata[1]}<br>"
    "<b>Workflow / Type:</b> %{customdata[2]}<br>"
    "<b>Cuisine:</b> %{customdata[3]}<br>"
    "<b>Approx Cost for Two:</b> <b>₹%{customdata[4]:,.0f}</b><br>"
    "<b>Rating:</b> <b>%{customdata[5]:.2f} / 5.0</b><br>"
    "<b>Review Votes:</b> %{customdata[6]:,} votes<br>"
    "<b>Outcome:</b> %{customdata[7]}<br>"
    "<extra></extra>"
)
```
- `%{customdata[i]}`: Injects metadata dimensions without affecting plotting coordinates.
- `<extra></extra>`: Suppresses default secondary trace badges for a clean popover.

---

### B. Interactive Legends (Trace Toggling & Isolation)
- **Single-Click:** Toggles visibility of an individual price tier or workflow trace on/off.
- **Double-Click:** **Isolates** that single trace, instantly dimming all others. Double-clicking again restores all traces.
- **Horizontal Positioning:** Aligned cleanly at `y=1.02, x=1` to maximize charting width.

---

### C. Hover Modes & Crosshair Spikes
- **`hovermode="closest"`:** Triggers tooltips for the point nearest the cursor.
- **Crosshair Spikes (`showspikes=True`):** Projects guideline spikes from the hovered point to both X and Y axes, allowing readers to read exact cost and rating coordinates.

---

### D. Workflow & Branch Comparison Box Plots
- **Grouped Box Plots:** Evaluates cost distributions across service workflows (`Delivery`, `Dine-out`, `Cafes`, `Desserts`, etc.).
- **Jittered Points & Outlier Detection:** Box whiskers display median and IQR while revealing individual venue outliers.

---

### E. Filtered Data Table & CSV Export
- Rendered using `st.dataframe` with search and column sorting.
- **One-Click CSV Export:** `st.download_button` exports filtered slices directly to `zomato_filtered_YYYYMMDD_HHMMSS.csv`.

---

## 5. Local Execution Instructions

### 1. Install Dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Launch the Streamlit Dashboard:
```powershell
streamlit run app.py
```

Open your browser at:
- **Local URL:** `http://localhost:8501`
- **Network URL:** `http://<your-ip>:8501`
