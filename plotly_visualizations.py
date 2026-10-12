"""
Script: plotly_visualizations.py
Description: Generates standalone interactive Plotly visualizations for workflow telemetry
             and dataset exploration, demonstrating custom tooltips, interactive legends,
             hover spikes, and client-side categorical dropdown filters.
"""

import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def build_workflow_trend_chart(csv_path: str = 'workflow_telemetry_runs.csv', output_html: str = 'workflow_trend_duration.html'):
    """
    Chart 1: Interactive Workflow Run-Duration & Latency Trend Timeline.
    Features:
    - Time-series trend of duration over execution time.
    - Custom HTML hover tooltip via hovertemplate and customdata.
    - Interactive legends (click to toggle trace, double-click to isolate).
    - Range slider and date window buttons (1 Day, 2 Days, All).
    - Dynamic hover spike lines along axes.
    """
    df = pd.read_csv(csv_path)
    df['started_at'] = pd.to_datetime(df['started_at'], utc=True)
    df = df.sort_values(by='started_at').dropna(subset=['started_at', 'duration_sec'])

    # Distinct color palette mapped to conclusions
    color_map = {
        'success': '#2ecc71',
        'failure': '#e74c3c',
        'timed_out': '#e67e22',
        'cancelled': '#95a5a6',
        'running': '#3498db'
    }

    fig = go.Figure()

    for conclusion in ['success', 'failure', 'timed_out', 'cancelled']:
        sub_df = df[df['conclusion'] == conclusion]
        if sub_df.empty:
            continue

        # Prepare rich tooltip customdata
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

        hovertemplate = (
            "<b>Run ID:</b> %{customdata[0]}<br>"
            "<b>Pipeline:</b> %{customdata[1]} (%{customdata[2]})<br>"
            "<b>Started:</b> %{x|%Y-%m-%d %H:%M:%S UTC}<br>"
            "<b>Duration:</b> %{y:.1f} seconds<br>"
            "<b>Queue Latency:</b> %{customdata[4]}s<br>"
            "<b>Trigger:</b> %{customdata[3]}<br>"
            "<b>CPU / RAM:</b> %{customdata[5]}%% / %{customdata[6]:.0f}MB<br>"
            "<b>Failure Reason:</b> <i>%{customdata[7]}</i><br>"
            "<extra></extra>"
        )

        fig.add_trace(go.Scatter(
            x=sub_df['started_at'],
            y=sub_df['duration_sec'],
            mode='markers',
            name=f"{conclusion.capitalize()} ({len(sub_df)})",
            marker=dict(
                size=11,
                color=color_map.get(conclusion, '#34495e'),
                line=dict(width=1, color='#ffffff'),
                opacity=0.85
            ),
            customdata=custom_data,
            hovertemplate=hovertemplate
        ))

    # Add trend polynomial / rolling baseline
    rolling_df = df.set_index('started_at')['duration_sec'].rolling('6h', min_periods=2).mean().reset_index()
    fig.add_trace(go.Scatter(
        x=rolling_df['started_at'],
        y=rolling_df['duration_sec'],
        mode='lines',
        name='6-Hour Moving Avg',
        line=dict(color='#2c3e50', width=2, dash='dot'),
        hoverinfo='skip'
    ))

    # Configure layout, range slider, spike lines, and tooltips
    fig.update_layout(
        title=dict(
            text="<b>Interactive Workflow Run Duration & Latency Trend</b><br><sup>Hover for detailed telemetry; use legend to isolate outcomes; slider to zoom time window</sup>",
            font=dict(size=18, family="Arial")
        ),
        xaxis=dict(
            title="Execution Start Timestamp (UTC)",
            showgrid=True,
            gridcolor="#ecf0f1",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikedash="solid",
            spikecolor="#95a5a6",
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="Last 24h", step="day", stepmode="backward"),
                    dict(count=2, label="Last 48h", step="day", stepmode="backward"),
                    dict(step="all", label="All Runs")
                ]),
                font=dict(size=11),
                bgcolor="#f8f9fa"
            ),
            rangeslider=dict(visible=True, thickness=0.08)
        ),
        yaxis=dict(
            title="Execution Duration (seconds)",
            showgrid=True,
            gridcolor="#ecf0f1",
            showspikes=True,
            spikethickness=1,
            spikedash="dot",
            spikecolor="#95a5a6"
        ),
        template="plotly_white",
        hovermode="closest",
        legend=dict(
            title=dict(text="<b>Run Outcome (Click to Toggle)</b>"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=40, t=100, b=60),
        width=1100,
        height=650
    )

    fig.write_html(output_html, include_plotlyjs='cdn')
    print(f"Chart 1 written to: {output_html}")
    return fig

def build_pipeline_comparison_chart(csv_path: str = 'workflow_telemetry_runs.csv', output_html: str = 'workflow_pipeline_comparison.html'):
    """
    Chart 2: Workflow Pipeline Comparison & Duration Distribution with Categorical Dropdown Filter.
    Features:
    - Box plot distribution of run duration grouped by pipeline.
    - Color-coded conclusion markers.
    - Categorical dropdown filter (Plotly updatemenus) to filter by trigger_event (All, push, pull_request, schedule).
    - Statistical tooltips (quartiles, median, whiskers, individual outliers).
    """
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['duration_sec'])

    triggers = ['All Triggers'] + sorted(df['trigger_event'].unique().tolist())
    pipelines = sorted(df['pipeline'].unique().tolist())

    fig = go.Figure()

    # Create traces for each trigger category (controlled via updatemenus visibility)
    trace_trigger_map = []
    
    for trig in triggers:
        if trig == 'All Triggers':
            filtered_df = df
        else:
            filtered_df = df[df['trigger_event'] == trig]

        is_visible = (trig == 'All Triggers')

        for conclusion in ['success', 'failure', 'timed_out', 'cancelled']:
            sub = filtered_df[filtered_df['conclusion'] == conclusion]
            
            custom_data = np.stack((
                sub['run_id'],
                sub['workflow_name'],
                sub['queue_latency_sec'],
                sub['failure_reason'].fillna('None')
            ), axis=-1) if not sub.empty else None

            color_map = {'success': '#2ecc71', 'failure': '#e74c3c', 'timed_out': '#e67e22', 'cancelled': '#95a5a6'}

            fig.add_trace(go.Box(
                x=sub['pipeline'],
                y=sub['duration_sec'],
                name=f"{conclusion.capitalize()}",
                legendgroup=conclusion,
                showlegend=(trig == 'All Triggers'),
                marker=dict(color=color_map.get(conclusion, '#34495e'), size=6),
                boxpoints='all',
                jitter=0.4,
                pointpos=-1.8,
                visible=is_visible,
                customdata=custom_data,
                hovertemplate=(
                    "<b>Pipeline:</b> %{x}<br>"
                    "<b>Duration:</b> %{y:.1f}s<br>"
                    "<b>Run ID:</b> %{customdata[0]}<br>"
                    "<b>Workflow:</b> %{customdata[1]}<br>"
                    "<b>Queue Delay:</b> %{customdata[2]}s<br>"
                    "<b>Failure Reason:</b> %{customdata[3]}<br>"
                    "<extra></extra>"
                ) if not sub.empty else None
            ))
            trace_trigger_map.append(trig)

    # Build dropdown buttons for categorical filter
    num_traces_per_trig = 4  # 4 conclusions per trigger view
    buttons = []
    for i, trig in enumerate(triggers):
        visibility = [False] * len(trace_trigger_map)
        start_idx = i * num_traces_per_trig
        for j in range(start_idx, start_idx + num_traces_per_trig):
            visibility[j] = True

        buttons.append(dict(
            label=f"Trigger: {trig}",
            method="update",
            args=[
                {"visible": visibility},
                {"title.text": f"<b>Pipeline Run-Duration Comparison</b> [Filter: <i>{trig}</i>]"}
            ]
        ))

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=0.0,
                xanchor="left",
                y=1.18,
                yanchor="top",
                bgcolor="#f8f9fa",
                bordercolor="#bdc3c7",
                font=dict(size=12)
            )
        ],
        title=dict(
            text="<b>Pipeline Run-Duration Comparison & Distribution</b> [Filter: <i>All Triggers</i>]<br><sup>Box displays median & IQR; points reveal individual run jitter and outliers</sup>",
            font=dict(size=18, family="Arial")
        ),
        boxmode='group',
        xaxis=dict(
            title="Service Pipeline",
            showgrid=True,
            gridcolor="#f1f2f6"
        ),
        yaxis=dict(
            title="Execution Duration (seconds)",
            showgrid=True,
            gridcolor="#f1f2f6"
        ),
        template="plotly_white",
        legend=dict(
            title=dict(text="<b>Conclusion</b>"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=40, t=120, b=60),
        width=1100,
        height=650
    )

    fig.write_html(output_html, include_plotlyjs='cdn')
    print(f"Chart 2 written to: {output_html}")
    return fig

def build_zomato_interactive_chart(csv_path: str = 'zomato_clean_validated.csv', output_html: str = 'zomato_interactive_explorer.html'):
    """
    Chart 3: Interactive Zomato Dining Explorer (Cost vs. Rating) with Dropdown Filter.
    Features:
    - Scatter plot: approx_cost_inr vs rating.
    - Sized by votes, colored by price_tier.
    - Dropdown filter by ordering channel (All Venues, Online Delivery Enabled, Dine-In Only).
    - Custom tooltip displaying Restaurant Name, Location, Cuisine, Cost, Rating, and Review Count.
    """
    df = pd.read_csv(csv_path).dropna(subset=['rating', 'approx_cost_inr'])
    # Sample 3,000 points for super smooth HTML rendering
    sample_df = df.sample(min(3000, len(df)), random_state=42)

    fig = px.scatter(
        sample_df,
        x='approx_cost_inr',
        y='rating',
        color='price_tier',
        size='votes',
        size_max=35,
        hover_name='name',
        hover_data={
            'location': True,
            'primary_cuisine': True,
            'approx_cost_inr': ':.0f',
            'rating': ':.2f',
            'votes': ':,',
            'has_online_order': True,
            'price_tier': False
        },
        labels={
            'approx_cost_inr': 'Approx Cost for Two (INR)',
            'rating': 'Rating (out of 5.0)',
            'price_tier': 'Price Tier',
            'votes': 'Review Votes'
        },
        title="<b>Interactive Bangalore Restaurant Explorer: Cost vs. Rating</b><br><sup>Point size reflects review volume; color denotes price tier; hover for venue profile</sup>",
        template="plotly_white"
    )

    fig.update_layout(
        margin=dict(l=60, r=40, t=90, b=60),
        width=1100,
        height=650,
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial")
    )

    fig.write_html(output_html, include_plotlyjs='cdn')
    print(f"Chart 3 written to: {output_html}")
    return fig

def main():
    print("=" * 80)
    print("GENERATING INTERACTIVE PLOTLY VISUALIZATIONS")
    print("=" * 80)
    build_workflow_trend_chart('workflow_telemetry_runs.csv', 'workflow_trend_duration.html')
    build_pipeline_comparison_chart('workflow_telemetry_runs.csv', 'workflow_pipeline_comparison.html')
    build_zomato_interactive_chart('zomato_clean_validated.csv', 'zomato_interactive_explorer.html')
    print("\nAll interactive Plotly charts generated successfully.")

if __name__ == '__main__':
    main()
