"""
========================================================
 SILVER LAYER — Clean, Validate & Enrich
========================================================
 Simulates: Azure Databricks / Azure Data Factory
 mapping data flows applied to bronze layer files.

 In production Azure:
   Input   → ADLS Gen2  abfss://bronze@<account>.dfs.core.windows.net/ppr/
   Process → Databricks notebook OR ADF Mapping Data Flow
   Output  → ADLS Gen2  abfss://silver@<account>.dfs.core.windows.net/ppr/
   Format  → Parquet (here: CSV for portability)

 Transformations applied:
   1. Parse & standardise sale_date
   2. Standardise county and property_type casing
   3. Drop rows missing price or date (< 5% expected)
   4. Cast price to float
   5. Derive: year, month, quarter, price_band, is_new_dwelling
   6. Add a surrogate key (property_id)
   7. Log data quality metrics
========================================================
"""

import pandas as pd
import numpy as np
import os

BRONZE_PATH = "data/bronze/ppr_raw.csv"
SILVER_PATH = "data/silver/ppr_clean.csv"
QUALITY_LOG = "data/silver/quality_report.txt"

# ── Load bronze ───────────────────────────────────────────────────────────────
df = pd.read_csv(BRONZE_PATH, dtype=str)
raw_count = len(df)
print(f"[SILVER] Loaded {raw_count:,} rows from bronze layer")

# ── 1. Parse sale_date ────────────────────────────────────────────────────────
df["sale_date"] = pd.to_datetime(df["sale_date"], format="%d/%m/%Y", errors="coerce")
date_nulls = df["sale_date"].isna().sum()

# ── 2. Standardise string columns ─────────────────────────────────────────────
df["county"]        = df["county"].str.strip().str.title()
df["property_type"] = df["property_type"].str.strip().str.title()
df["vat_exclusive"] = df["vat_exclusive"].str.strip().str.title()
df["new_dwelling"]  = df["new_dwelling"].str.strip().str.title()
df["area"]          = df["area"].str.strip().str.title()
df["address"]       = df["address"].str.strip()
df["buyer_name"]    = df["buyer_name"].str.strip().str.title()

# ── 3. Cast price ─────────────────────────────────────────────────────────────
df["price"] = pd.to_numeric(df["price"], errors="coerce")
price_nulls = df["price"].isna().sum()

# ── 4. Drop rows missing critical fields ──────────────────────────────────────
before_drop = len(df)
df = df.dropna(subset=["sale_date", "price"])
dropped = before_drop - len(df)

# ── 5. Outlier filter (> €5M or < €30k — data entry errors) ──────────────────
outlier_mask = (df["price"] < 30_000) | (df["price"] > 5_000_000)
outliers = outlier_mask.sum()
df = df[~outlier_mask]

# ── 6. Derive date features ───────────────────────────────────────────────────
df["year"]    = df["sale_date"].dt.year
df["month"]   = df["sale_date"].dt.month
df["quarter"] = df["sale_date"].dt.quarter
df["month_label"] = df["sale_date"].dt.strftime("%Y-%m")

# ── 7. Price band ─────────────────────────────────────────────────────────────
def price_band(p):
    if p < 150_000:   return "Under €150k"
    elif p < 250_000: return "€150k–€250k"
    elif p < 350_000: return "€250k–€350k"
    elif p < 500_000: return "€350k–€500k"
    elif p < 750_000: return "€500k–€750k"
    else:             return "Over €750k"

df["price_band"] = df["price"].apply(price_band)

# ── 8. Region grouping ────────────────────────────────────────────────────────
dublin_commuter = {"Kildare","Meath","Wicklow","Louth"}
munster = {"Cork","Limerick","Waterford","Tipperary","Clare","Kerry"}
connacht = {"Galway","Mayo","Roscommon","Sligo","Leitrim"}

def region(county):
    if county == "Dublin": return "Greater Dublin"
    if county in dublin_commuter: return "Dublin Commuter Belt"
    if county in munster: return "Munster"
    if county in connacht: return "Connacht"
    return "Rest of Ireland"

df["region"] = df["county"].apply(region)

# ── 9. Surrogate key ──────────────────────────────────────────────────────────
df = df.reset_index(drop=True)
df.insert(0, "property_id", ["PPR" + str(i+1).zfill(6) for i in df.index])

# ── 10. Reorder columns ───────────────────────────────────────────────────────
df = df[[
    "property_id","sale_date","year","month","quarter","month_label",
    "address","area","county","region",
    "price","price_band","property_type","new_dwelling","vat_exclusive","buyer_name"
]]

# ── Save silver ───────────────────────────────────────────────────────────────
os.makedirs("data/silver", exist_ok=True)
df.to_csv(SILVER_PATH, index=False)

# ── Quality report ────────────────────────────────────────────────────────────
report = f"""
DATA QUALITY REPORT — Silver Layer
====================================
Raw records ingested      : {raw_count:,}
Missing dates (dropped)   : {date_nulls}
Missing prices (dropped)  : {price_nulls}
Outliers removed          : {outliers}
Total rows dropped        : {dropped + outliers}
Clean records output      : {len(df):,}
Data retention rate       : {len(df)/raw_count*100:.1f}%

County distribution:
{df['county'].value_counts().to_string()}

Property type distribution:
{df['property_type'].value_counts().to_string()}

Price statistics:
  Min    : €{df['price'].min():,.0f}
  Median : €{df['price'].median():,.0f}
  Mean   : €{df['price'].mean():,.0f}
  Max    : €{df['price'].max():,.0f}

Year range: {df['year'].min()} – {df['year'].max()}
"""

with open(QUALITY_LOG, "w") as f:
    f.write(report)

print(f"[SILVER] Clean records: {len(df):,} ({len(df)/raw_count*100:.1f}% retained)")
print(f"[SILVER] Saved → {SILVER_PATH}")
print(f"[SILVER] Quality report → {QUALITY_LOG}")
