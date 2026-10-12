"""
Streamlit Telemetry Analytics Dashboard: app.py
Comprehensive monitoring dashboard for CI/CD workflow telemetry runs.
Includes sidebar filters for date, branch, workflow, and outcome; KPI metric cards;
interactive Plotly charts; and filtered data tables with export functionality.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Workflow Telemetry Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished cards, KPI metrics, and badges
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
    }
    .badge-success {
        background-color: #dcfce7;
        color: #15803d;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-failure {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. REUSABLE DATA-LOADING & TRANSFORMATION FUNCTIONS (CACHED)
# -----------------------------------------------------------------------------
@st.cache_data
def load_telemetry_data(csv_path: str = 'workflow_telemetry_runs.csv') -> pd.DataFrame:
    """Loads and preprocesses workflow telemetry runs."""
    df = pd.read_csv(csv_path)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    df['started_at'] = pd.to_datetime(df['started_at'], utc=True)
    df['completed_at'] = pd.to_datetime(df['completed_at'], utc=True)
    df['date'] = df['started_at'].dt.date
    df['duration_sec'] = pd.to_numeric(df['duration_sec'], errors='coerce')
    df['queue_latency_sec'] = pd.to_numeric(df['queue_latency_sec'], errors='coerce')
    df['failure_reason'] = df['failure_reason'].fillna('None')
    return df

@st.cache_data
def filter_telemetry(
    df: pd.DataFrame,
    start_date: date,
    end_date: date,
    selected_branches: list,
    selected_workflows: list,
    selected_outcomes: list
) -> pd.DataFrame:
    """Filters telemetry dataset based on sidebar user controls."""
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    
    if selected_branches:
        mask &= df['branch'].isin(selected_branches)
    if selected_workflows:
        mask &= df['workflow_name'].isin(selected_workflows)
    if selected_outcomes:
        mask &= df['conclusion'].isin(selected_outcomes)
        
    return df[mask].copy()

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & DYNAMIC FILTERS
# -----------------------------------------------------------------------------
df_raw = load_telemetry_data()

st.sidebar.image("https://img.icons8.com/fluency/96/server.png", width=64)
st.sidebar.title("Telemetry Controls")
st.sidebar.markdown("Filter and drill down into pipeline workflow runs.")

# Date Range Filter
min_date = df_raw['date'].min()
max_date = df_raw['date'].max()

date_selection = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Select the start and end date of workflow execution."
)

if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start_date, end_date = date_selection
else:
    start_date, end_date = min_date, max_date

# Branch Filter
all_branches = sorted(df_raw['branch'].dropna().unique().tolist())
selected_branches = st.sidebar.multiselect(
    "Branch",
    options=all_branches,
    default=[],
    placeholder="All branches (default)"
)

# Workflow Name Filter
all_workflows = sorted(df_raw['workflow_name'].dropna().unique().tolist())
selected_workflows = st.sidebar.multiselect(
    "Workflow",
    options=all_workflows,
    default=[],
    placeholder="All workflows (default)"
)

# Outcome / Conclusion Filter
all_outcomes = sorted(df_raw['conclusion'].dropna().unique().tolist())
selected_outcomes = st.sidebar.multiselect(
    "Outcome (Conclusion)",
    options=all_outcomes,
    default=[],
    placeholder="All outcomes (default)"
)

# Reset Button
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.rerun()

st.sidebar.divider()
st.sidebar.caption("⚡ Powered by Streamlit & Plotly")

# Apply dynamic filtering
filtered_df = filter_telemetry(
    df_raw,
    start_date,
    end_date,
    selected_branches,
    selected_workflows,
    selected_outcomes
)

# -----------------------------------------------------------------------------
# 4. DASHBOARD HEADER & HIGH-LEVEL KPI METRIC CARDS
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">⚡ Workflow Telemetry Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-header">Monitoring pipeline reliability, duration trends, and failure root causes | Filtered Runs: <b>{len(filtered_df):,}</b> of {len(df_raw):,} total</div>',
    unsafe_allow_html=True
)

if filtered_df.empty:
    st.warning("⚠️ No workflow runs match the selected filter criteria. Please broaden your selection in the sidebar.")
    st.stop()

# Compute KPI calculations
total_runs = len(filtered_df)
success_runs = (filtered_df['conclusion'] == 'success').sum()
failure_runs = (filtered_df['conclusion'] == 'failure').sum()
timeout_runs = (filtered_df['conclusion'] == 'timed_out').sum()
cancelled_runs = (filtered_df['conclusion'] == 'cancelled').sum()
running_runs = (filtered_df['conclusion'] == 'running').sum()

success_rate = (success_runs / total_runs) * 100 if total_runs > 0 else 0
avg_duration = filtered_df['duration_sec'].mean()
avg_queue_latency = filtered_df['queue_latency_sec'].mean()
error_count = failure_runs + timeout_runs

# Render KPI Cards via st.columns
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

with kpi_col1:
    st.metric(
        label="Total Runs",
        value=f"{total_runs:,}",
        delta=f"{(total_runs/len(df_raw)*100):.0f}% of total"
    )

with kpi_col2:
    st.metric(
        label="Success Rate",
        value=f"{success_rate:.1f}%",
        delta=f"{success_runs} Passed",
        delta_color="normal" if success_rate >= 75 else "inverse"
    )

with kpi_col3:
    st.metric(
        label="Avg Duration",
        value=f"{avg_duration:.1f}s" if pd.notna(avg_duration) else "N/A",
        delta=f"Median: {filtered_df['duration_sec'].median():.0f}s"
    )

with kpi_col4:
    st.metric(
        label="Avg Queue Delay",
        value=f"{avg_queue_latency:.1f}s",
        delta=f"Max: {filtered_df['queue_latency_sec'].max():.0f}s"
    )

with kpi_col5:
    st.metric(
        label="Failures / Timeouts",
        value=f"{error_count}",
        delta=f"{failure_runs} fail | {timeout_runs} timeout",
        delta_color="inverse" if error_count > 0 else "normal"
    )

st.write("")

# -----------------------------------------------------------------------------
# 5. INTERACTIVE CHARTS & VISUALIZATIONS (CONNECTED TO FILTERS)
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📈 Duration Trend Timeline",
    "📊 Pipeline & Workflow Comparison",
    "📋 Telemetry Data Table & Errors"
])

# ----------------- TAB 1: RUN DURATION TREND -----------------
with tab1:
    st.subheader("Workflow Run-Duration & Latency Trend Timeline")
    st.caption("Point color indicates outcome; click legend items to toggle/isolate outcomes; hover for telemetry diagnostics.")

    color_palette = {
        'success': '#22c55e',
        'failure': '#ef4444',
        'timed_out': '#f97316',
        'cancelled': '#94a3b8',
        'running': '#3b82f6'
    }

    fig_trend = go.Figure()
    plot_data = filtered_df.sort_values(by='started_at').dropna(subset=['started_at', 'duration_sec'])

    for outcome in ['success', 'failure', 'timed_out', 'cancelled', 'running']:
        subset = plot_data[plot_data['conclusion'] == outcome]
        if subset.empty:
            continue

        custom_hover = np.stack((
            subset['run_id'],
            subset['branch'],
            subset['pipeline'],
            subset['workflow_name'],
            subset['queue_latency_sec'],
            subset['cpu_utilization_pct'],
            subset['memory_used_mb'],
            subset['failure_reason']
        ), axis=-1)

        hovertemplate = (
            "<b>Run ID:</b> %{customdata[0]}<br>"
            "<b>Branch:</b> <code>%{customdata[1]}</code><br>"
            "<b>Pipeline:</b> %{customdata[2]} (%{customdata[3]})<br>"
            "<b>Started:</b> %{x|%Y-%m-%d %H:%M:%S UTC}<br>"
            "<b>Duration:</b> <b>%{y:.1f}s</b><br>"
            "<b>Queue Delay:</b> %{customdata[4]}s<br>"
            "<b>Hardware:</b> CPU %{customdata[5]}%% | RAM %{customdata[6]:.0f}MB<br>"
            "<b>Error Reason:</b> %{customdata[7]}<br>"
            "<extra></extra>"
        )

        fig_trend.add_trace(go.Scatter(
            x=subset['started_at'],
            y=subset['duration_sec'],
            mode='markers',
            name=f"{outcome.capitalize()} ({len(subset)})",
            marker=dict(
                size=10,
                color=color_palette.get(outcome, '#64748b'),
                line=dict(width=1, color='#ffffff'),
                opacity=0.85
            ),
            customdata=custom_hover,
            hovertemplate=hovertemplate
        ))

    # Add moving average trendline
    if len(plot_data) >= 3:
        rolling_mean = plot_data.set_index('started_at')['duration_sec'].rolling('12h', min_periods=2).mean().reset_index()
        fig_trend.add_trace(go.Scatter(
            x=rolling_mean['started_at'],
            y=rolling_mean['duration_sec'],
            mode='lines',
            name='12h Rolling Mean',
            line=dict(color='#0f172a', width=2, dash='dash'),
            hoverinfo='skip'
        ))

    fig_trend.update_layout(
        xaxis=dict(
            title="Execution Start Time (UTC)",
            showgrid=True,
            gridcolor="#f1f5f9",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikecolor="#cbd5e1"
        ),
        yaxis=dict(
            title="Execution Duration (seconds)",
            showgrid=True,
            gridcolor="#f1f5f9",
            showspikes=True
        ),
        template="plotly_white",
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=20, t=40, b=40),
        height=520
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ----------------- TAB 2: PIPELINE & WORKFLOW COMPARISON -----------------
with tab2:
    col_chart_left, col_chart_right = st.columns([3, 2])

    with col_chart_left:
        st.subheader("Execution Duration by Service Pipeline")
        st.caption("Distribution box plots show median, IQR, and duration spreads across pipelines.")
        
        fig_box = px.box(
            filtered_df.dropna(subset=['duration_sec']),
            x='pipeline',
            y='duration_sec',
            color='conclusion',
            color_discrete_map=color_palette,
            points="all",
            hover_data=['run_id', 'branch', 'workflow_name', 'failure_reason'],
            labels={'duration_sec': 'Duration (s)', 'pipeline': 'Service Pipeline', 'conclusion': 'Outcome'},
            template="plotly_white"
        )
        fig_box.update_layout(
            boxmode="group",
            margin=dict(l=40, r=20, t=40, b=40),
            height=450,
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with col_chart_right:
        st.subheader("Outcome Share Breakdown")
        st.caption("Proportion of successful vs failed runs within the filtered cohort.")
        
        outcome_counts = filtered_df['conclusion'].value_counts().reset_index()
        outcome_counts.columns = ['Outcome', 'Count']
        
        fig_pie = px.pie(
            outcome_counts,
            values='Count',
            names='Outcome',
            color='Outcome',
            color_discrete_map=color_palette,
            hole=0.45,
            template="plotly_white"
        )
        fig_pie.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            height=450,
            legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Workflow Breakdown Bar Chart
    st.subheader("Average Duration & Run Volume by Workflow Name")
    wf_stats = filtered_df.groupby('workflow_name').agg(
        avg_dur=('duration_sec', 'mean'),
        run_count=('run_id', 'count')
    ).reset_index().sort_values(by='avg_dur', ascending=True)

    fig_wf = px.bar(
        wf_stats,
        x='avg_dur',
        y='workflow_name',
        orientation='h',
        color='avg_dur',
        color_continuous_scale='Blues',
        text=wf_stats['run_count'].apply(lambda x: f"n={x}"),
        labels={'avg_dur': 'Average Duration (seconds)', 'workflow_name': 'Workflow Name'},
        template="plotly_white"
    )
    fig_wf.update_layout(height=400, margin=dict(l=40, r=20, t=20, b=40))
    st.plotly_chart(fig_wf, use_container_width=True)

# ----------------- TAB 3: DATA TABLE & ERROR LOGS -----------------
with tab3:
    st.subheader("Filtered Telemetry Records")
    st.caption("Search, sort, and inspect individual run records matching sidebar filter selections.")

    # Table columns to display
    display_cols = [
        'run_id', 'branch', 'pipeline', 'workflow_name',
        'conclusion', 'started_at', 'duration_sec',
        'queue_latency_sec', 'cpu_utilization_pct', 'memory_used_mb',
        'failure_reason'
    ]

    st.dataframe(
        filtered_df[display_cols].sort_values(by='started_at', ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "started_at": st.column_config.DatetimeColumn("Started (UTC)", format="YYYY-MM-DD HH:mm:ss"),
            "duration_sec": st.column_config.NumberColumn("Duration", format="%.1f s"),
            "queue_latency_sec": st.column_config.NumberColumn("Queue Delay", format="%d s"),
            "cpu_utilization_pct": st.column_config.ProgressColumn("CPU Util", min_value=0, max_value=100, format="%d%%"),
            "memory_used_mb": st.column_config.NumberColumn("RAM", format="%.0f MB"),
            "conclusion": st.column_config.TextColumn("Outcome")
        }
    )

    # Export Button
    csv_bytes = filtered_df[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Filtered Telemetry to CSV",
        data=csv_bytes,
        file_name=f"telemetry_filtered_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=False
    )

    # Detailed Failure Root Cause Table if errors exist
    failed_runs = filtered_df[filtered_df['conclusion'].isin(['failure', 'timed_out'])]
    if not failed_runs.empty:
        st.divider()
        st.subheader("⚠️ Failure & Timeout Root Cause Investigation")
        st.dataframe(
            failed_runs[['run_id', 'branch', 'pipeline', 'workflow_name', 'conclusion', 'failure_reason']].reset_index(drop=True),
            use_container_width=True,
            column_config={
                "run_id": "Run ID",
                "failure_reason": "Exception / Error Stack",
                "conclusion": "Outcome"
            }
        )
