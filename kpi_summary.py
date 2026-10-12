"""
Script: kpi_summary.py
Description: Computes operational, commercial, and sentiment KPIs for the Zomato Bangalore dataset
             and outputs compact KPI summary tables.
"""

import pandas as pd
import numpy as np

def compute_kpis(csv_path: str = 'zomato_clean_validated.csv'):
    df = pd.read_csv(csv_path)

    # -------------------------------------------------------------
    # 1. EXECUTIVE COMPACT KPI SUMMARY TABLE
    # -------------------------------------------------------------
    total_venues = len(df)
    rated_venues = df['rating'].notna().sum()
    online_order_count = df['has_online_order'].sum()
    table_booking_count = df['has_table_booking'].sum()
    
    online_order_pct = (online_order_count / total_venues) * 100
    table_booking_pct = (table_booking_count / total_venues) * 100

    mean_rating = df['rating'].mean()
    median_rating = df['rating'].median()
    high_rating_count = (df['rating'] >= 4.0).sum()
    high_rating_pct = (high_rating_count / rated_venues) * 100

    total_votes = df['votes'].sum()
    mean_votes = df['votes'].mean()
    median_votes = df['votes'].median()

    mean_cost_two = df['approx_cost_inr'].mean()
    median_cost_two = df['approx_cost_inr'].median()
    mean_cost_person = df['approx_cost_per_person'].mean()

    mean_cuisines = df['num_cuisines'].mean()
    mean_engagement = df['engagement_index'].mean()

    kpi_records = [
        {"Category": "Market & Supply", "KPI Name": "Total Establishments", "Value": f"{total_venues:,}", "Benchmark / Context": "Unique physical venues"},
        {"Category": "Market & Supply", "KPI Name": "Online Ordering Adoption", "Value": f"{online_order_pct:.1f}%", "Benchmark / Context": f"{online_order_count:,} venues with delivery"},
        {"Category": "Market & Supply", "KPI Name": "Table Reservation Rate", "Value": f"{table_booking_pct:.1f}%", "Benchmark / Context": f"{table_booking_count:,} venues with booking"},
        {"Category": "Market & Supply", "KPI Name": "Avg Menu Breadth", "Value": f"{mean_cuisines:.1f}", "Benchmark / Context": "Distinct cuisines offered"},
        {"Category": "Quality & Sentiment", "KPI Name": "Average Rating (Mean)", "Value": f"{mean_rating:.2f} / 5.0", "Benchmark / Context": f"Std Dev: {df['rating'].std():.2f}"},
        {"Category": "Quality & Sentiment", "KPI Name": "Median Rating", "Value": f"{median_rating:.2f} / 5.0", "Benchmark / Context": "50th percentile"},
        {"Category": "Quality & Sentiment", "KPI Name": "High-Rating Share (>= 4.0)", "Value": f"{high_rating_pct:.1f}%", "Benchmark / Context": f"{high_rating_count:,} top-rated venues"},
        {"Category": "Engagement & Reach", "KPI Name": "Total Review Feedback", "Value": f"{total_votes:,}", "Benchmark / Context": "Cumulative customer votes"},
        {"Category": "Engagement & Reach", "KPI Name": "Avg Review Engagement", "Value": f"{mean_votes:.1f}", "Benchmark / Context": f"Median votes: {median_votes:.0f}"},
        {"Category": "Engagement & Reach", "KPI Name": "Avg Engagement Index", "Value": f"{mean_engagement:.2f}", "Benchmark / Context": "ln(1+votes) * rating"},
        {"Category": "Commercial & Pricing", "KPI Name": "Avg Meal Cost (2 People)", "Value": f"INR {mean_cost_two:.2f}", "Benchmark / Context": f"Median: INR {median_cost_two:.0f}"},
        {"Category": "Commercial & Pricing", "KPI Name": "Avg Cost Per Person", "Value": f"INR {mean_cost_person:.2f}", "Benchmark / Context": "Individual diner spend"}
    ]
    df_kpi_summary = pd.DataFrame(kpi_records)

    # -------------------------------------------------------------
    # 2. SEGMENT KPI: PRICE TIER AGGREGATION
    # -------------------------------------------------------------
    tier_order = ['Budget', 'Moderate', 'Premium', 'Fine Dining']
    price_kpis = df.groupby('price_tier', observed=True).agg(
        Venue_Count=('name', 'count'),
        Online_Order_Pct=('has_online_order', lambda s: round(s.mean() * 100, 1)),
        Table_Booking_Pct=('has_table_booking', lambda s: round(s.mean() * 100, 1)),
        Avg_Rating=('rating', lambda s: round(s.mean(), 2)),
        High_Rating_Pct=('is_highly_rated', lambda s: round(s.mean() * 100, 1)),
        Median_Cost_INR=('approx_cost_inr', 'median'),
        Avg_Votes=('votes', lambda s: round(s.mean(), 1))
    ).reindex(tier_order)
    price_kpis['Share_of_Total_Pct'] = (price_kpis['Venue_Count'] / total_venues * 100).round(1)

    # -------------------------------------------------------------
    # 3. SEGMENT KPI: ONLINE ORDERING VS DINE-IN ONLY
    # -------------------------------------------------------------
    channel_kpis = df.groupby('has_online_order').agg(
        Establishments=('name', 'count'),
        Avg_Rating=('rating', lambda s: round(s.mean(), 2)),
        Median_Rating=('rating', lambda s: round(s.median(), 2)),
        High_Rating_Share=('is_highly_rated', lambda s: round(s.mean() * 100, 1)),
        Avg_Cost_INR=('approx_cost_inr', lambda s: round(s.mean(), 2)),
        Median_Votes=('votes', 'median'),
        Avg_Votes=('votes', lambda s: round(s.mean(), 1)),
        Avg_Engagement=('engagement_index', lambda s: round(s.mean(), 2))
    )
    channel_kpis.index = ['Dine-In Only', 'Online Delivery Enabled']

    # -------------------------------------------------------------
    # 4. TOP 5 DINING HUBS / LOCATIONS
    # -------------------------------------------------------------
    location_kpis = df.groupby('location', observed=True).agg(
        Venues=('name', 'count'),
        Avg_Rating=('rating', lambda s: round(s.mean(), 2)),
        Avg_Cost_INR=('approx_cost_inr', lambda s: round(s.mean(), 2)),
        Online_Order_Pct=('has_online_order', lambda s: round(s.mean() * 100, 1)),
        Avg_Votes=('votes', lambda s: round(s.mean(), 1))
    ).sort_values(by='Venues', ascending=False).head(5)

    # Print Formatted Reports
    print("=" * 90)
    print("EXECUTIVE COMPACT KPI SUMMARY TABLE")
    print("=" * 90)
    print(df_kpi_summary.to_string(index=False))

    print("\n" + "=" * 90)
    print("SEGMENT BREAKDOWN: KPIs BY PRICE TIER")
    print("=" * 90)
    print(price_kpis.to_string())

    print("\n" + "=" * 90)
    print("CHANNEL BREAKDOWN: ONLINE DELIVERY VS. DINE-IN ONLY")
    print("=" * 90)
    print(channel_kpis.to_string())

    print("\n" + "=" * 90)
    print("GEOGRAPHIC BREAKDOWN: TOP 5 RESTAURANT HUBS")
    print("=" * 90)
    print(location_kpis.to_string())

    # Export tables
    df_kpi_summary.to_csv('kpi_summary_executive.csv', index=False)
    price_kpis.to_csv('kpi_summary_price_tier.csv')
    channel_kpis.to_csv('kpi_summary_channel.csv')
    print("\nKPI tables exported to CSV files successfully.")

    return df_kpi_summary, price_kpis, channel_kpis, location_kpis

if __name__ == '__main__':
    compute_kpis('zomato_clean_validated.csv')
