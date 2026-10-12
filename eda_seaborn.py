"""
Script: eda_seaborn.py
Description: Systematic exploratory data analysis (EDA) using Seaborn, matching
             analytical questions/requirements to ideal chart types for distributions
             and relationships.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def run_eda(csv_path: str = 'zomato_clean_validated.csv', output_dir: str = 'eda_plots'):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)

    # Global Aesthetic Theme
    sns.set_theme(style="whitegrid", font_scale=1.05)
    plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['axes.edgecolor'] = '#cccccc'
    plt.rcParams['axes.linewidth'] = 0.8

    print("=" * 80)
    print("MATCHING REQUIREMENTS TO SEABORN CHARTS & GENERATING EDA PLOTS")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # CHART 1: Univariate Distributions (Histplot + KDE)
    # Requirement: Assess shape, spread, central tendency, and skewness of core continuous variables.
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 1A. Rating distribution
    sns.histplot(df['rating'].dropna(), kde=True, ax=axes[0], color='#2b5c8f', bins=25)
    axes[0].set_title('1A. Distribution of Restaurant Ratings', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Rating (out of 5.0)')
    axes[0].set_ylabel('Restaurant Count')
    axes[0].axvline(df['rating'].median(), color='#d9534f', linestyle='--', label=f'Median: {df["rating"].median():.2f}')
    axes[0].legend()

    # 1B. Cost distribution
    sns.histplot(df['approx_cost_inr'].dropna(), kde=True, ax=axes[1], color='#e67e22', bins=30)
    axes[1].set_title('1B. Distribution of Approx Cost for Two (INR)', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Approx Cost for Two (INR)')
    axes[1].set_ylabel('Restaurant Count')
    axes[1].axvline(df['approx_cost_inr'].median(), color='#d9534f', linestyle='--', label=f'Median: INR {df["approx_cost_inr"].median():.0f}')
    axes[1].legend()

    plt.tight_layout()
    chart1_path = os.path.join(output_dir, '1_univariate_distributions.png')
    plt.savefig(chart1_path, dpi=300)
    plt.close()
    print(f"Chart 1 Saved: {chart1_path}")

    # -------------------------------------------------------------------------
    # CHART 2: Bivariate Continuous Relationship (Scatterplot + Regplot)
    # Requirement: Investigate whether meal price correlates with dining satisfaction.
    # -------------------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    plot_df = df.dropna(subset=['rating', 'approx_cost_inr']).copy()
    sns.scatterplot(
        data=plot_df,
        x='approx_cost_inr',
        y='rating',
        hue='has_online_order',
        palette={True: '#27ae60', False: '#7f8c8d'},
        alpha=0.6,
        s=35
    )
    sns.regplot(
        data=plot_df,
        x='approx_cost_inr',
        y='rating',
        scatter=False,
        ax=plt.gca(),
        color='#c0392b',
        line_kws={'linewidth': 2, 'label': 'Linear Trendline'}
    )
    plt.title('2. Relationship: Meal Cost vs. Customer Rating', fontsize=14, fontweight='bold')
    plt.xlabel('Approx Cost for Two (INR)')
    plt.ylabel('Customer Rating (out of 5.0)')
    plt.legend(title='Online Order Enabled', loc='lower right')
    plt.tight_layout()
    chart2_path = os.path.join(output_dir, '2_rating_vs_cost_relationship.png')
    plt.savefig(chart2_path, dpi=300)
    plt.close()
    print(f"Chart 2 Saved: {chart2_path}")

    # -------------------------------------------------------------------------
    # CHART 3: Categorical vs. Continuous Distribution (Boxplot with Means)
    # Requirement: Compare rating variances and medians across price segments.
    # -------------------------------------------------------------------------
    tier_order = ['Budget', 'Moderate', 'Premium', 'Fine Dining']
    plt.figure(figsize=(10, 6))
    sns.boxplot(
        data=df.dropna(subset=['rating', 'price_tier']),
        x='price_tier',
        y='rating',
        hue='price_tier',
        order=tier_order,
        palette='Blues',
        legend=False,
        showmeans=True,
        meanprops={"marker": "o", "markerfacecolor": "red", "markeredgecolor": "red"}
    )
    plt.title('3. Rating Variance Across Price Tiers (Red dot = Mean)', fontsize=14, fontweight='bold')
    plt.xlabel('Price Tier')
    plt.ylabel('Customer Rating')
    plt.tight_layout()
    chart3_path = os.path.join(output_dir, '3_price_tier_vs_rating_boxplot.png')
    plt.savefig(chart3_path, dpi=300)
    plt.close()
    print(f"Chart 3 Saved: {chart3_path}")

    # -------------------------------------------------------------------------
    # CHART 4: Channel Impact (Violin Plot for Log-Votes & Boxplot for Rating)
    # Requirement: Compare review engagement between online delivery and dine-in only.
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    df_plot4 = df.copy()
    df_plot4['log_votes'] = np.log1p(df_plot4['votes'])
    df_plot4['channel_label'] = df_plot4['has_online_order'].map({False: 'Dine-In Only', True: 'Online Delivery'})

    sns.violinplot(
        data=df_plot4,
        x='channel_label',
        y='log_votes',
        hue='channel_label',
        palette=['#95a5a6', '#2ecc71'],
        legend=False,
        ax=axes[0]
    )
    axes[0].set_title('4A. Log Review Volume by Channel', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Ordering Channel')
    axes[0].set_ylabel('ln(1 + Votes)')

    sns.boxplot(
        data=df_plot4.dropna(subset=['rating']),
        x='channel_label',
        y='rating',
        hue='channel_label',
        palette=['#95a5a6', '#2ecc71'],
        legend=False,
        ax=axes[1]
    )
    axes[1].set_title('4B. Rating Distribution by Channel', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Ordering Channel')
    axes[1].set_ylabel('Rating')

    plt.tight_layout()
    chart4_path = os.path.join(output_dir, '4_online_order_channel_impact.png')
    plt.savefig(chart4_path, dpi=300)
    plt.close()
    print(f"Chart 4 Saved: {chart4_path}")

    # -------------------------------------------------------------------------
    # CHART 5: Multivariate Correlation Heatmap
    # Requirement: Quantify collinearity and pairwise relationships among all numeric metrics.
    # -------------------------------------------------------------------------
    num_cols = ['rating', 'votes', 'approx_cost_inr', 'approx_cost_per_person', 'num_cuisines', 'engagement_index']
    corr_matrix = df[num_cols].corr()

    plt.figure(figsize=(9, 7))
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt='.2f',
        cmap='coolwarm',
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        cbar_kws={'label': 'Pearson Correlation Coefficient'}
    )
    plt.title('5. Correlation Matrix of Numerical Telemetry & Metrics', fontsize=14, fontweight='bold')
    plt.tight_layout()
    chart5_path = os.path.join(output_dir, '5_multivariate_correlation_heatmap.png')
    plt.savefig(chart5_path, dpi=300)
    plt.close()
    print(f"Chart 5 Saved: {chart5_path}")

    # -------------------------------------------------------------------------
    # CHART 6: Categorical Ranking & Metric Aggregation (Horizontal Barplot)
    # Requirement: Identify the most common primary cuisines and their mean satisfaction ratings.
    # -------------------------------------------------------------------------
    top_cuisines = df['primary_cuisine'].value_counts().head(10).index
    cuisine_stats = df[df['primary_cuisine'].isin(top_cuisines)].groupby('primary_cuisine', observed=True)['rating'].agg(['mean', 'count']).loc[top_cuisines].reset_index()

    plt.figure(figsize=(10, 6))
    bar_plot = sns.barplot(
        data=cuisine_stats,
        x='mean',
        y='primary_cuisine',
        hue='primary_cuisine',
        palette='viridis',
        legend=False,
        orient='h'
    )
    plt.xlim(3.0, 4.3)
    plt.title('6. Mean Customer Rating by Top 10 Primary Cuisines', fontsize=14, fontweight='bold')
    plt.xlabel('Mean Rating (out of 5.0)')
    plt.ylabel('Primary Cuisine')

    # Annotate bars with venue count
    for i, row in cuisine_stats.iterrows():
        bar_plot.text(row['mean'] + 0.02, i, f"n={int(row['count']):,}", va='center', fontsize=9, color='#333333')

    plt.tight_layout()
    chart6_path = os.path.join(output_dir, '6_top_cuisines_ratings.png')
    plt.savefig(chart6_path, dpi=300)
    plt.close()
    print(f"Chart 6 Saved: {chart6_path}")

    print("\nAll 6 EDA charts successfully generated and saved to 'eda_plots/'.")

if __name__ == '__main__':
    run_eda()
