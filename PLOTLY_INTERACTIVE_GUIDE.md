# Plotly Interactive Visualizations: Telemetry Trends, Comparisons & Dynamic Controls

This guide explains the architecture, interactive mechanics, and implementation patterns for the interactive visualizations created in [`plotly_visualizations.py`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/plotly_visualizations.py).

---

## 1. Overview of Generated Interactive Charts

Three standalone interactive HTML visualizations have been generated:

| Chart File | Visualization Type | Key Metrics / Features | Interactive Capabilities |
| :--- | :--- | :--- | :--- |
| [`workflow_trend_duration.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/workflow_trend_duration.html) | **Time-Series Telemetry Scatter + Moving Avg** | Execution Duration, Queue Latency, CPU %, RAM MB, Outcome | Multi-line custom tooltips, interactive range slider, 24h/48h window buttons, trace isolating legends, hover spikes |
| [`workflow_pipeline_comparison.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/workflow_pipeline_comparison.html) | **Grouped Box Plot with Jittered Run Points** | Service Pipeline vs. Duration (sec) grouped by Conclusion | Client-side dropdown filter (`updatemenus`) by Trigger Event, statistical summary tooltips, jittered run drill-downs |
| [`zomato_interactive_explorer.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/zomato_interactive_explorer.html) | **Multivariate Bubble Scatter Explorer** | Approx Cost (INR) vs. Rating, sized by Review Votes | Bubble size scaling, price tier coloration, hover tooltip with restaurant metadata |

---

## 2. Core Interactive Plotly Mechanics Explained

### A. Tooltips & Custom Hover Templates
Default tooltips only display the raw X and Y coordinate numbers. In production telemetry, engineers require contextual diagnostics (Run ID, specific error messages, hardware utilization, queue wait times).

#### Implementation Pattern:
```python
# 1. Pack extra diagnostic dimensions into a custom NumPy matrix
custom_data = np.stack((
    sub_df['run_id'],
    sub_df['pipeline'],
    sub_df['workflow_name'],
    sub_df['trigger_event'],
    sub_df['queue_latency_sec'],
    sub_df['cpu_utilization_pct'],
    sub_df['memory_used_mb'],
    sub_df['failure_reason'].fillna('None')
), axis=-1)

# 2. Define HTML formatted template referencing customdata indices
hovertemplate = (
    "<b>Run ID:</b> %{customdata[0]}<br>"
    "<b>Pipeline:</b> %{customdata[1]} (%{customdata[2]})<br>"
    "<b>Started:</b> %{x|%Y-%m-%d %H:%M:%S UTC}<br>"
    "<b>Duration:</b> %{y:.1f} seconds<br>"
    "<b>Queue Latency:</b> %{customdata[4]}s<br>"
    "<b>Trigger:</b> %{customdata[3]}<br>"
    "<b>CPU / RAM:</b> %{customdata[5]}%% / %{customdata[6]:.0f}MB<br>"
    "<b>Failure Reason:</b> <i>%{customdata[7]}</i><br>"
    "<extra></extra>"  # Suppresses secondary trace tag box
)
```

- **Format Specifiers:**
  - `%{y:.1f}`: Formats floating-point numbers to 1 decimal place.
  - `%{x|%Y-%m-%d %H:%M:%S UTC}`: Formats ISO timestamps to human-readable UTC date-time.
  - `%{customdata[i]}`: Pulls the $i$-th column from the bundled `customdata` matrix.
  - `<extra></extra>`: Omits the default trace name badge on the right of the tooltip for a clean popover.

---

### B. Interactive Legends (Trace Toggling & Isolation)
Plotly legends provide built-in interactive filtering without writing custom JavaScript:
- **Single Click on Legend Item:** Toggles visibility of that specific outcome trace on/off (e.g., hide `Success` to inspect only `Failure` and `Timed_Out`).
- **Double Click on Legend Item:** **Isolates** that single trace, instantly dimming/hiding all other traces. Double-clicking again restores all traces.
- **Horizontal Orientation & Placement:**
  ```python
  fig.update_layout(
      legend=dict(
          title=dict(text="<b>Run Outcome (Click to Toggle)</b>"),
          orientation="h",
          yanchor="bottom",
          y=1.02,
          xanchor="right",
          x=1
      )
  )
  ```

---

### C. Hover Modes & Crosshair Spikes
Hover modes control how cursor events trigger tooltips and axis crosshairs:
- **`hovermode="closest"`**: Triggers the tooltip for the specific data point closest to the cursor.
- **`hovermode="x unified"`**: Displays a single unified tooltip summarizing all traces sharing the same X-coordinate (ideal for multi-line comparison).
- **Spike Lines:** Adds dynamic projection lines from the hovered point to the X and Y axes, making it easy to read exact dates and execution durations:
  ```python
  xaxis=dict(
      showspikes=True,
      spikemode="across",
      spikesnap="cursor",
      spikethickness=1,
      spikedash="solid",
      spikecolor="#95a5a6"
  )
  ```

---

### D. Client-Side Categorical Dropdown Filters (`updatemenus`)
A major advantage of Plotly is enabling **interactive filtering directly inside standalone HTML files** without requiring a live Python/Flask/Streamlit server:

#### How It Works:
Pre-computes all trace variations into the figure and toggles their boolean visibility vector via client-side JavaScript buttons:

```python
buttons = []
for i, trig in enumerate(triggers):
    # Construct boolean visibility mask for the traces
    visibility = [False] * total_traces
    start_idx = i * traces_per_group
    for j in range(start_idx, start_idx + traces_per_group):
        visibility[j] = True

    buttons.append(dict(
        label=f"Trigger: {trig}",
        method="update",
        args=[
            {"visible": visibility},
            {"title.text": f"<b>Pipeline Comparison</b> [Filter: <i>{trig}</i>]"}
        ]
    ))

fig.update_layout(
    updatemenus=[dict(
        buttons=buttons,
        direction="down",
        showactive=True,
        x=0.0, y=1.18
    )]
)
```

Users can click the dropdown menu to filter the box plot view between `All Triggers`, `push`, `pull_request`, `schedule`, and `workflow_dispatch`.

---

## 3. Walkthrough of the Generated Visualizations

### 1. [`workflow_trend_duration.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/workflow_trend_duration.html)
- **Visual Structure:** Scatter plot with execution start timestamp on the X-axis and duration (seconds) on the Y-axis.
- **Color Mapping:** Success (Green), Failure (Red), Timed Out (Orange), Cancelled (Grey).
- **Trend Curve:** 6-hour moving average dashed trendline.
- **Range Slider:** Drag sliders at the bottom to zoom into micro-incidents or peak traffic hours.
- **Quick Time Selectors:** Buttons at the top-left for `Last 24h`, `Last 48h`, and `All Runs`.

### 2. [`workflow_pipeline_comparison.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/workflow_pipeline_comparison.html)
- **Visual Structure:** Grouped box plot comparing five service pipelines (`backend-api`, `frontend-web`, `data-warehouse`, `ml-service`, `infra-ops`).
- **Jittered Points:** Individual run points overlaid alongside box plots to reveal outlier clusters.
- **Dropdown Filter:** Filter runs by invocation mechanism (`push`, `pull_request`, `schedule`, `workflow_dispatch`).
- **Telemetry Insight:** Data warehouse ETL jobs and ML model evaluations average 1,200 – 1,800 seconds, whereas frontend builds average ~120 seconds.

### 3. [`zomato_interactive_explorer.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/zomato_interactive_explorer.html)
- **Visual Structure:** Scatter bubble plot mapping meal expenditure (INR) against customer rating.
- **Marker Size:** Scales proportionally with verified customer review volume (`votes`).
- **Color Coding:** Categorized by price tier (`Budget`, `Moderate`, `Premium`, `Fine Dining`).

---

## 4. How to Generate & View the Charts

### Run the Script:
```powershell
python plotly_visualizations.py
```

### View in Browser:
Open any of the generated HTML files directly in your browser:
- [`workflow_trend_duration.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/workflow_trend_duration.html)
- [`workflow_pipeline_comparison.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/workflow_pipeline_comparison.html)
- [`zomato_interactive_explorer.html`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/zomato_interactive_explorer.html)
