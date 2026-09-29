"""
========================================================
 GOLD LAYER — Analytics-Ready Aggregation Tables
========================================================
 Simulates: Azure Synapse Analytics / Databricks Delta
 tables serving the BI and reporting layer.

 In production Azure:
   Input   → ADLS Gen2  abfss://silver@<account>.dfs.core.windows.net/ppr/
   Process → Azure Synapse SQL Pool OR Databricks Delta
   Output  → ADLS Gen2  abfss://gold@<account>.dfs.core.windows.net/ppr/
             + Azure Synapse dedicated SQL pool tables
   Consumed by → Power BI via DirectQuery / Import mode

 Gold tables produced:
   1. monthly_trends       — avg price + volume by month & county
   2. county_summary       — overall stats per county
   3. property_type_mix    — market share by property type per year
   4. price_band_dist      — distribution of sales across price bands
   5. yoy_growth           — year-on-year price growth by county
   6. region_comparison    — regional aggregates
   7. new_vs_second_hand   — new dwelling premium analysis
========================================================
"""

import pandas as pd
import numpy as np
import os

SILVER_PATH = "data/silver/ppr_clean.csv"
GOLD_DIR    = "data/gold"
os.makedirs(GOLD_DIR, exist_ok=True)

df = pd.read_csv(SILVER_PATH, parse_dates=["sale_date"])
print(f"[GOLD] Loaded {len(df):,} clean records from silver layer")

# ── 1. Monthly trends ─────────────────────────────────────────────────────────
monthly = (
    df.groupby(["month_label", "county"])
    .agg(
        avg_price  = ("price", "mean"),
        median_price = ("price", "median"),
        total_sales  = ("price", "count"),
        total_volume = ("price", "sum"),
    )
    .reset_index()
)
monthly["avg_price"]    = monthly["avg_price"].round(0)
monthly["median_price"] = monthly["median_price"].round(0)
monthly["total_volume"] = monthly["total_volume"].round(0)
monthly.to_csv(f"{GOLD_DIR}/monthly_trends.csv", index=False)
print(f"[GOLD] monthly_trends → {len(monthly):,} rows")

# ── 2. County summary ─────────────────────────────────────────────────────────
county_sum = (
    df.groupby("county")
    .agg(
        total_sales    = ("price", "count"),
        avg_price      = ("price", "mean"),
        median_price   = ("price", "median"),
        min_price      = ("price", "min"),
        max_price      = ("price", "max"),
        total_volume   = ("price", "sum"),
    )
    .reset_index()
    .sort_values("total_sales", ascending=False)
)
for col in ["avg_price","median_price","min_price","max_price","total_volume"]:
    county_sum[col] = county_sum[col].round(0)
county_sum.to_csv(f"{GOLD_DIR}/county_summary.csv", index=False)
print(f"[GOLD] county_summary → {len(county_sum):,} rows")

# ── 3. Property type mix per year ─────────────────────────────────────────────
prop_mix = (
    df.groupby(["year", "property_type"])
    .agg(
        sales = ("price","count"),
        avg_price = ("price","mean"),
        median_price = ("price","median"),
    )
    .reset_index()
)
year_totals = prop_mix.groupby("year")["sales"].transform("sum")
prop_mix["market_share_pct"] = (prop_mix["sales"] / year_totals * 100).round(1)
prop_mix["avg_price"] = prop_mix["avg_price"].round(0)
prop_mix["median_price"] = prop_mix["median_price"].round(0)
prop_mix.to_csv(f"{GOLD_DIR}/property_type_mix.csv", index=False)
print(f"[GOLD] property_type_mix → {len(prop_mix):,} rows")

# ── 4. Price band distribution ────────────────────────────────────────────────
band_order = ["Under €150k","€150k–€250k","€250k–€350k","€350k–€500k","€500k–€750k","Over €750k"]
price_bands = (
    df.groupby(["year","price_band"])
    .agg(sales=("price","count"))
    .reset_index()
)
year_totals2 = price_bands.groupby("year")["sales"].transform("sum")
price_bands["pct_of_year"] = (price_bands["sales"] / year_totals2 * 100).round(1)
price_bands["price_band"] = pd.Categorical(price_bands["price_band"], categories=band_order, ordered=True)
price_bands = price_bands.sort_values(["year","price_band"])
price_bands.to_csv(f"{GOLD_DIR}/price_band_dist.csv", index=False)
print(f"[GOLD] price_band_dist → {len(price_bands):,} rows")

# ── 5. Year-on-year growth by county ─────────────────────────────────────────
yearly_county = (
    df.groupby(["year","county"])
    .agg(avg_price=("price","mean"), median_price=("price","median"), sales=("price","count"))
    .reset_index()
)
yearly_county = yearly_county.sort_values(["county","year"])
yearly_county["prev_avg"]     = yearly_county.groupby("county")["avg_price"].shift(1)
yearly_county["yoy_growth_pct"] = (
    (yearly_county["avg_price"] - yearly_county["prev_avg"]) / yearly_county["prev_avg"] * 100
).round(1)
yearly_county["avg_price"]    = yearly_county["avg_price"].round(0)
yearly_county["median_price"] = yearly_county["median_price"].round(0)
yearly_county["prev_avg"]     = yearly_county["prev_avg"].round(0)
yearly_county.to_csv(f"{GOLD_DIR}/yoy_growth.csv", index=False)
print(f"[GOLD] yoy_growth → {len(yearly_county):,} rows")

# ── 6. Region comparison ──────────────────────────────────────────────────────
region_comp = (
    df.groupby(["year","region"])
    .agg(
        avg_price    = ("price","mean"),
        median_price = ("price","median"),
        sales        = ("price","count"),
        total_volume = ("price","sum"),
    )
    .reset_index()
)
region_comp["avg_price"]    = region_comp["avg_price"].round(0)
region_comp["median_price"] = region_comp["median_price"].round(0)
region_comp["total_volume"] = region_comp["total_volume"].round(0)
region_comp.to_csv(f"{GOLD_DIR}/region_comparison.csv", index=False)
print(f"[GOLD] region_comparison → {len(region_comp):,} rows")

# ── 7. New dwelling premium ───────────────────────────────────────────────────
new_vs_old = (
    df.groupby(["year","new_dwelling","property_type"])
    .agg(
        avg_price    = ("price","mean"),
        median_price = ("price","median"),
        sales        = ("price","count"),
    )
    .reset_index()
)
new_vs_old["avg_price"]    = new_vs_old["avg_price"].round(0)
new_vs_old["median_price"] = new_vs_old["median_price"].round(0)
new_vs_old.to_csv(f"{GOLD_DIR}/new_vs_second_hand.csv", index=False)
print(f"[GOLD] new_vs_second_hand → {len(new_vs_old):,} rows")

print(f"\n[GOLD] All 7 analytics tables saved to {GOLD_DIR}/")
