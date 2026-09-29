"""
========================================================
 BRONZE LAYER — Raw Data Ingestion
========================================================
 Simulates: Azure Data Factory pulling data from
 an external source (Irish Property Price Register)
 and landing raw files in Azure Data Lake Gen2
 (bronze container).

 In production Azure:
   Source  → HTTP connector / REST API in ADF
   Landing → ADLS Gen2  abfss://bronze@<account>.dfs.core.windows.net/ppr/
   Format  → raw CSV (no transformation at this layer)
========================================================
"""

import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

BRONZE_PATH = "data/bronze/ppr_raw.csv"

# ── Realistic Irish data pools ────────────────────────────────────────────────

COUNTIES = {
    "Dublin":      {"weight": 0.38, "base_price": 460000, "std": 180000},
    "Cork":        {"weight": 0.12, "base_price": 310000, "std": 110000},
    "Galway":      {"weight": 0.08, "base_price": 295000, "std": 100000},
    "Kildare":     {"weight": 0.07, "base_price": 370000, "std": 120000},
    "Meath":       {"weight": 0.06, "base_price": 345000, "std": 105000},
    "Wicklow":     {"weight": 0.05, "base_price": 390000, "std": 130000},
    "Limerick":    {"weight": 0.05, "base_price": 260000, "std": 90000},
    "Waterford":   {"weight": 0.04, "base_price": 230000, "std": 80000},
    "Kilkenny":    {"weight": 0.03, "base_price": 245000, "std": 85000},
    "Wexford":     {"weight": 0.03, "base_price": 235000, "std": 80000},
    "Tipperary":   {"weight": 0.03, "base_price": 185000, "std": 65000},
    "Clare":       {"weight": 0.03, "base_price": 210000, "std": 75000},
    "Louth":       {"weight": 0.03, "base_price": 290000, "std": 95000},
}

PROPERTY_TYPES = ["Detached", "Semi-Detached", "Terraced", "Apartment", "End-of-Terrace"]
PROPERTY_WEIGHTS = [0.22, 0.30, 0.20, 0.18, 0.10]

VAT_EXCLUSIVE = ["Yes", "No"]

DUBLIN_AREAS = [
    "Dublin 1","Dublin 2","Dublin 3","Dublin 4","Dublin 6","Dublin 7",
    "Dublin 8","Dublin 9","Dublin 10","Dublin 11","Dublin 12","Dublin 13",
    "Dublin 14","Dublin 15","Dublin 16","Dublin 17","Dublin 18","Dublin 20",
    "Dublin 22","Dublin 24","Clontarf","Swords","Malahide","Balbriggan",
    "Blanchardstown","Tallaght","Dún Laoghaire","Rathfarnham","Lucan","Clondalkin"
]

CORK_AREAS = ["Cork City","Ballincollig","Carrigaline","Cobh","Midleton","Mallow","Bandon","Kinsale"]
GALWAY_AREAS = ["Galway City","Salthill","Oranmore","Athenry","Tuam","Loughrea","Ballinasloe"]

STREET_TYPES = ["Road","Street","Avenue","Drive","Close","Way","Grove","Park","Court","Place","Lane","Crescent","Gardens"]

FIRST_NAMES = ["Liam","Emma","Conor","Aoife","Seán","Ciara","Patrick","Niamh","James","Sinéad",
               "Michael","Aisling","Daniel","Caoimhe","David","Sorcha","Thomas","Fiona","John","Roisín",
               "Paul","Orla","Brian","Deirdre","Kevin","Máire","Martin","Grainne","Peter","Siobhán"]

LAST_NAMES = ["Murphy","Kelly","O'Brien","Walsh","Smith","O'Sullivan","Ryan","Byrne","O'Connor","McCarthy",
              "Doyle","Hughes","O'Neill","Brennan","Collins","Fitzpatrick","Kavanagh","Kennedy","Lynch","Moran"]

def random_address(county):
    num = random.randint(1, 120)
    surname = random.choice(LAST_NAMES)
    street_type = random.choice(STREET_TYPES)
    street = f"{num} {surname} {street_type}"
    if county == "Dublin":
        area = random.choice(DUBLIN_AREAS)
    elif county == "Cork":
        area = random.choice(CORK_AREAS)
    elif county == "Galway":
        area = random.choice(GALWAY_AREAS)
    else:
        area = f"{county} Town" if random.random() > 0.4 else county
    return street, area

def price_with_trend(base, std, date):
    """Add a realistic time trend: prices rose ~8%/yr 2020-2022, slowed 2023, mild recovery 2024"""
    year = date.year
    month = date.month
    if year == 2019:
        trend = 1.00
    elif year == 2020:
        trend = 0.98  # COVID dip
    elif year == 2021:
        trend = 1.06
    elif year == 2022:
        trend = 1.14
    elif year == 2023:
        trend = 1.19
    elif year == 2024:
        trend = 1.24
    else:
        trend = 1.27
    seasonal = 1.0 + 0.02 * np.sin((month - 3) * np.pi / 6)
    raw = np.random.normal(base * trend * seasonal, std)
    return max(50000, round(raw / 1000) * 1000)

# ── Generate records ──────────────────────────────────────────────────────────

county_names = list(COUNTIES.keys())
county_weights = [COUNTIES[c]["weight"] for c in county_names]

START_DATE = datetime(2019, 1, 1)
END_DATE   = datetime(2024, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

N = 5000
rows = []

for _ in range(N):
    county = random.choices(county_names, weights=county_weights)[0]
    cfg = COUNTIES[county]

    days_offset = random.randint(0, TOTAL_DAYS)
    sale_date = START_DATE + timedelta(days=days_offset)

    prop_type = random.choices(PROPERTY_TYPES, weights=PROPERTY_WEIGHTS)[0]

    # Apartments cheaper; detached more expensive
    price_mult = {"Detached": 1.25, "Semi-Detached": 1.0, "Terraced": 0.90,
                  "End-of-Terrace": 0.95, "Apartment": 0.75}[prop_type]

    price = price_with_trend(cfg["base_price"] * price_mult, cfg["std"] * 0.7, sale_date)

    street, area = random_address(county)

    buyer_first = random.choice(FIRST_NAMES)
    buyer_last  = random.choice(LAST_NAMES)
    buyer_name  = f"{buyer_first} {buyer_last}"

    # Introduce some realistic data quality issues (raw layer)
    if random.random() < 0.03:
        price = None                       # missing price
    if random.random() < 0.02:
        county = county.upper()            # inconsistent casing
    if random.random() < 0.015:
        sale_date = None                   # missing date
    if random.random() < 0.01:
        prop_type = prop_type.lower()      # inconsistent casing

    rows.append({
        "sale_date":         sale_date.strftime("%d/%m/%Y") if sale_date else "",
        "address":           street,
        "area":              area,
        "county":            county,
        "price":             price if price else "",
        "vat_exclusive":     random.choices(VAT_EXCLUSIVE, weights=[0.15, 0.85])[0],
        "property_type":     prop_type,
        "buyer_name":        buyer_name,
        "new_dwelling":      random.choices(["Yes","No"], weights=[0.30, 0.70])[0],
    })

df = pd.DataFrame(rows)

os.makedirs("data/bronze", exist_ok=True)
df.to_csv(BRONZE_PATH, index=False)

print(f"[BRONZE] Ingested {len(df):,} raw records → {BRONZE_PATH}")
print(f"[BRONZE] Columns : {list(df.columns)}")
print(f"[BRONZE] Nulls   : price={df['price'].eq('').sum()}, date={df['sale_date'].eq('').sum()}")
print(f"[BRONZE] Date range: {df['sale_date'].min()} – {df['sale_date'].max()}")
