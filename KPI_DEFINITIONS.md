# Aggregation & KPI Definitions: Zomato Bangalore Analytics

This document defines the key performance indicators (KPIs), mathematical formulations, aggregation methodologies, and executive summary tables generated from the validated dataset [`zomato_clean_validated.csv`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/zomato_clean_validated.csv) using [`kpi_summary.py`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/kpi_summary.py).

---

## 1. Executive Compact KPI Summary Table

The table below provides a high-level executive snapshot across market supply, quality/sentiment, customer engagement, and commercial economics:

| Pillar | Key Performance Indicator (KPI) | Metric Value | Unit / Format | Benchmark & Operational Context |
| :--- | :--- | :--- | :--- | :--- |
| **Market & Supply** | **Total Physical Venues** | **12,924** | Count | Deduplicated physical establishments across Bangalore |
| **Market & Supply** | **Online Ordering Adoption Rate** | **53.6%** | Percentage | 6,930 venues accepting delivery orders via Zomato |
| **Market & Supply** | **Table Reservation Rate** | **7.7%** | Percentage | 1,000 venues supporting digital reservations |
| **Market & Supply** | **Average Menu Breadth** | **2.3** | Cuisines / Venue | Mean number of distinct cuisines per establishment |
| **Quality & Sentiment** | **Average Rating (Mean)** | **3.63** | $/ 5.0$ Score | Overall market average (Std Dev: 0.43) |
| **Quality & Sentiment** | **Median Rating (50th percentile)** | **3.70** | $/ 5.0$ Score | Median restaurant satisfaction score |
| **Quality & Sentiment** | **High-Rating Share ($\ge 4.0$)** | **23.0%** | Percentage | 2,220 elite restaurants rated 4.0 or higher |
| **Engagement & Reach** | **Total Feedback Volume** | **2,379,888** | Customer Votes | Cumulative verified user review votes recorded |
| **Engagement & Reach** | **Average Review Engagement** | **184.1** | Votes / Venue | Mean review volume (Median: 25.0 votes) |
| **Engagement & Reach** | **Average Engagement Index** | **15.46** | Index Score | Log-weighted sentiment metric: $\ln(1+\text{votes}) \times \text{rating}$ |
| **Commercial & Pricing**| **Avg Meal Cost (for Two People)** | **INR 487.62** | INR (₹) | Median cost for two is INR 400.00 |
| **Commercial & Pricing**| **Avg Cost Per Person** | **INR 243.81** | INR (₹) | Individual diner benchmark spend |

---

## 2. KPI Mathematical Definitions & Formulations

### A. Supply & Digital Adoption
1. **Online Ordering Penetration Rate:**
   $$\text{Online Adoption \%} = \left( \frac{\sum \mathbb{I}(\text{has\_online\_order} = \text{True})}{N} \right) \times 100 = 53.6\%$$
2. **Table Booking Penetration Rate:**
   $$\text{Table Booking \%} = \left( \frac{\sum \mathbb{I}(\text{has\_table\_booking} = \text{True})}{N} \right) \times 100 = 7.7\%$$

### B. Quality & Sentiment
3. **High-Rating Share:**
   $$\text{High-Rating Share} = \left( \frac{\sum \mathbb{I}(\text{rating} \ge 4.0)}{N_{\text{rated}}} \right) \times 100 = 23.0\%$$
   *Measures the proportion of rated venues ($N_{\text{rated}} = 9,640$) meeting top-tier culinary standards.*

### C. Engagement & Influence
4. **Engagement Index:**
   $$\text{Engagement Index} = \ln(1 + \text{votes}) \times \text{rating}$$
   *Penalizes low-sample outliers (e.g., 5.0 rating from 1 vote) while rewarding sustained quality across large customer bases.*

### D. Pricing & Economics
5. **Cost Per Person:**
   $$\text{Cost Per Person} = \frac{\text{approx\_cost\_inr}}{2}$$

---

## 3. Multi-Dimensional Segment Aggregations

### A. Performance by Price Tier

```
Price Tiers:
- Budget:       <= INR 300
- Moderate:     INR 301 - INR 700
- Premium:      INR 701 - INR 1,500
- Fine Dining:  > INR 1,500
```

| Price Tier | Venue Count | Market Share | Online Order % | Table Booking % | Mean Rating | High-Rating Share | Median Cost | Mean Votes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Budget** | 5,264 | 40.7% | 46.3% | 0.2% | 3.55 | 7.7% | INR 250 | 44.8 |
| **Moderate** | 5,682 | 44.0% | 62.6% | 2.3% | 3.58 | 14.9% | INR 500 | 139.3 |
| **Premium** | 1,612 | 12.5% | 54.2% | 39.4% | 3.87 | 46.2% | INR 900 | 638.9 |
| **Fine Dining** | 299 | 2.3% | 21.7% | 73.9% | 4.15 | 71.9% | INR 2,000 | 1,057.0 |

> **Key Observation:** Rating quality scales directly with price tier. While only **7.7%** of Budget venues achieve $\ge 4.0$ ratings, **71.9%** of Fine Dining establishments achieve top ratings, accompanied by an average of 1,057 votes per venue.

---

### B. Channel Comparison: Online Delivery vs. Dine-In Only

| Channel Group | Total Venues | Mean Rating | Median Rating | High-Rating Share | Mean Cost (INR) | Median Votes | Mean Votes | Engagement Index |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dine-In Only** | 5,994 | 3.59 | 3.60 | 13.2% | INR 504.03 | 7.0 | 147.0 | 14.03 |
| **Online Delivery Enabled** | 6,930 | 3.65 | 3.70 | 20.6% | INR 473.58 | **54.0** | **216.3** | **16.34** |

> **Key Observation:** Venues offering online ordering capture **7.7x greater median review engagement** (54 vs. 7 votes) and exhibit a **56% higher share of top-rated establishments** (20.6% vs. 13.2%).

---

### C. Top 5 Dining Hubs by Restaurant Density

| Location | Venue Count | Mean Rating | Mean Cost (INR) | Online Order Adoption | Mean Votes / Venue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Whitefield** | 878 | 3.60 | INR 559.50 | 49.5% | 161.0 |
| **BTM** | 777 | 3.57 | INR 379.51 | 58.4% | 95.1 |
| **Electronic City** | 723 | 3.47 | INR 461.41 | 43.6% | 74.1 |
| **HSR** | 715 | 3.64 | INR 442.82 | 65.6% | 159.8 |
| **Marathahalli** | 708 | 3.54 | INR 486.74 | 55.4% | 200.8 |

---

## 4. Exported KPI Artifacts

The aggregation script exports the summary tables directly to CSV:
- [`kpi_summary_executive.csv`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/kpi_summary_executive.csv) – Complete 12-metric executive table.
- [`kpi_summary_price_tier.csv`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/kpi_summary_price_tier.csv) – Aggregations segmented by spending tier.
- [`kpi_summary_channel.csv`](file:///d:/Akarsh/Mysore_pythonDocker/data_analysis/kpi_summary_channel.csv) – Aggregations comparing delivery vs. dine-in channels.

---

## 5. How to Recompute KPIs

To recalculate all KPIs from the validated dataset:
```powershell
python kpi_summary.py
```
