# 🏠 Azure Property Analytics Ireland

> **Azure Cloud Data Engineering Portfolio Project**  
> End-to-end Medallion architecture pipeline — Bronze → Silver → Gold — built with Python to mirror real Azure services, analysing 5,000+ Irish residential property transactions from 2019–2024.

![Architecture](docs/arch_azure_property.png)

---

## 🎯 Project Overview

This project demonstrates **production-grade cloud data engineering** skills by building a complete data pipeline that mirrors an enterprise Azure stack. It ingests raw property data (modelled on Ireland's [Property Price Register](https://www.propertypriceregister.ie/)), applies multi-stage transformations, and produces a suite of analytics-ready gold tables consumed by an Excel dashboard with 6 Matplotlib charts.

| Layer | Azure Service (Production) | Local Simulation |
|---|---|---|
| **Bronze** | Azure Data Factory + ADLS Gen2 (raw) | `ingest.py` → CSV |
| **Silver** | Azure Databricks / ADF Mapping Data Flow | `transform.py` → cleaned CSV |
| **Gold** | Azure Synapse Analytics / Databricks Delta | `aggregate.py` → 7 analytics tables |
| **Reporting** | Power BI (DirectQuery) | `report.py` → Excel + 6 PNG charts |

---

## 🏗️ Architecture — Medallion Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     AZURE CLOUD (simulated locally)              │
│                                                                   │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────┐  │
│  │  BRONZE     │    │   SILVER     │    │        GOLD         │  │
│  │  ADLS Gen2  │───▶│  ADLS Gen2   │───▶│  Synapse Analytics  │  │
│  │  (raw CSV)  │    │  (clean CSV) │    │  (7 Delta tables)   │  │
│  └─────────────┘    └──────────────┘    └─────────────────────┘  │
│       ▲                   ▲                       │               │
│       │                   │                       ▼               │
│  Azure Data           Databricks            Power BI /            │
│  Factory (ADF)        Notebook             Excel Report           │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**🔵 Bronze — Raw Ingestion**  
Simulates Azure Data Factory pulling from the Irish Property Price Register HTTP endpoint and landing raw files in ADLS Gen2 (bronze container). No transformations; data quality issues deliberately preserved (missing prices, casing inconsistencies, blank dates).

**⚪ Silver — Clean & Enrich**  
Simulates Databricks / ADF Mapping Data Flows. Applies 9 transformation steps: date parsing, casing standardisation, null removal, outlier filtering, date feature derivation (year/month/quarter), price band classification, region grouping, and surrogate key assignment. Logs a full data quality report.

**🟡 Gold — Analytics Aggregates**  
Simulates Azure Synapse Analytics dedicated SQL pool tables. Produces 7 analytics-ready tables consumed by BI tools via DirectQuery.

---

## 📊 Gold Tables

| Table | Description | Key Columns |
|---|---|---|
| `monthly_trends.csv` | Avg/median price + volume by month & county | `month_label`, `county`, `avg_price` |
| `county_summary.csv` | Overall stats per county (all years) | `county`, `avg_price`, `total_sales` |
| `property_type_mix.csv` | Market share by property type per year | `year`, `property_type`, `market_share_pct` |
| `price_band_dist.csv` | Band distribution with % per year | `year`, `price_band`, `pct_of_year` |
| `yoy_growth.csv` | Year-on-year % price growth by county | `county`, `year`, `yoy_growth_pct` |
| `region_comparison.csv` | Regional aggregates by year | `region`, `year`, `avg_price` |
| `new_vs_second_hand.csv` | New dwelling premium analysis | `new_dwelling`, `property_type`, `avg_price` |

---

## 📈 Key Findings (2019–2024)

| Metric | Value |
|---|---|
| Total transactions analysed | 4,769 |
| National average price (2024) | ~€385,000 |
| National price growth 2019→2024 | **+24%** |
| Highest average county | Dublin |
| Lowest average county | Tipperary |
| New dwelling premium | ~18–22% above second-hand |
| COVID dip (2020) | –2% YoY |
| Peak growth year | 2022 (+8% YoY national) |
| Price band shift | "Under €150k" share halved from 2019→2024 |

---

## 📉 Charts Generated

1. **National Price Trend** — Monthly avg/median price 2019–2024
2. **County Average Price** — Horizontal bar, all 13 counties (2024)
3. **Region YoY Growth** — Line chart, 5 regions, 2020–2024
4. **Price Band Shift** — Side-by-side bars, 2019 vs 2024
5. **Property Type Mix** — Pie chart, market share (2024)
6. **New Dwelling Premium** — Area + line chart, 2019–2024

---

## 🗂️ Project Structure

```
azure-property-analytics-ireland/
├── ingest.py            # Bronze layer — simulates Azure Data Factory
├── transform.py         # Silver layer — simulates Azure Databricks
├── aggregate.py         # Gold layer  — simulates Azure Synapse Analytics
├── report.py            # Reporting   — simulates Power BI export
├── data/
│   ├── bronze/
│   │   └── ppr_raw.csv          # 5,000 raw records (with intentional DQ issues)
│   ├── silver/
│   │   ├── ppr_clean.csv        # 4,769 clean, enriched records
│   │   └── quality_report.txt   # Data quality audit log
│   └── gold/
│       ├── monthly_trends.csv
│       ├── county_summary.csv
│       ├── property_type_mix.csv
│       ├── price_band_dist.csv
│       ├── yoy_growth.csv
│       ├── region_comparison.csv
│       └── new_vs_second_hand.csv
├── output/
│   ├── charts/           # 6 Matplotlib PNG charts
│   └── reports/
│       └── ireland_property_analytics.xlsx   # 8-sheet styled Excel report
└── docs/
    └── arch_azure_property.png   # Architecture diagram
```

---

## 🚀 How to Run

### Prerequisites

```bash
pip install pandas numpy matplotlib openpyxl
```

### Run the Full Pipeline

```bash
# Step 1 — Bronze: ingest raw data (simulates Azure Data Factory)
python ingest.py

# Step 2 — Silver: clean & enrich (simulates Azure Databricks)
python transform.py

# Step 3 — Gold: aggregate for BI (simulates Azure Synapse)
python aggregate.py

# Step 4 — Report: charts + Excel dashboard (simulates Power BI export)
python report.py
```

---

## ☁️ Azure Services Mapped

| Script | Azure Equivalent | What it does |
|---|---|---|
| `ingest.py` | **Azure Data Factory** | HTTP-connector pipeline, lands raw CSV in ADLS Gen2 bronze container |
| `transform.py` | **Azure Databricks** | Spark notebook cleaning data; or ADF Mapping Data Flow |
| `aggregate.py` | **Azure Synapse Analytics** | Dedicated SQL pool or Databricks Delta table aggregations |
| `report.py` | **Power BI** | DirectQuery over Synapse gold tables → .pbix; Excel export via Logic App |
| `data/bronze/` | **ADLS Gen2 Bronze Container** | `abfss://bronze@<account>.dfs.core.windows.net/ppr/` |
| `data/silver/` | **ADLS Gen2 Silver Container** | `abfss://silver@<account>.dfs.core.windows.net/ppr/` |
| `data/gold/` | **ADLS Gen2 Gold / Synapse Tables** | `abfss://gold@<account>.dfs.core.windows.net/ppr/` |

---

## 🛠️ Data Quality Engineering

The silver layer applies 9 transformation steps and logs a quality report:

- **Date parsing** — handles `dd/mm/yyyy` format, flags unparseable dates
- **Casing standardisation** — fixes `DUBLIN` → `Dublin`, `apartment` → `Apartment`
- **Null removal** — drops records missing price or sale date (~4.6%)
- **Outlier filtering** — removes prices <€30k or >€5M (data entry errors)
- **Derived features** — year, month, quarter, `month_label` (YYYY-MM format)
- **Price bands** — 6 bands from "Under €150k" to "Over €750k"
- **Region mapping** — 5 regions: Greater Dublin, Dublin Commuter Belt, Munster, Connacht, Rest of Ireland
- **Surrogate key** — `PPR000001` format, uniquely identifies each clean record
- **Retention rate** — 95.4% (231 records dropped from 5,000 raw)

---

## 💼 Skills Demonstrated

- **Azure Medallion Architecture** — Bronze/Silver/Gold lake design
- **Azure Data Factory** — pipeline design, HTTP connectors, data landing
- **Azure Databricks** — notebook-based ETL, data quality patterns
- **Azure Synapse Analytics** — gold table design for BI consumption
- **Power BI / Excel** — dashboard design, multi-sheet reports, chart generation
- **Data Quality Engineering** — null handling, casing issues, outlier detection, audit logging
- **Python (pandas, numpy, matplotlib, openpyxl)** — production ETL scripting
- **Irish Property Market** — domain expertise in PPR data structure and market dynamics

---

## 📌 Dataset

This project uses **simulated data** modelled on the structure and statistical properties of Ireland's [Property Price Register](https://www.propertypriceregister.ie/) — a public register of residential property sales in Ireland. The synthetic dataset preserves realistic:
- County-level price distributions and market share
- Year-on-year price trends (including 2020 COVID dip)
- Seasonal variation patterns
- Property type mix ratios
- Data quality issues typical of real PPR data (casing, missing values)

---

## 🔗 Related Projects

- [ecom-sql-analytics](https://github.com/alansha1/ecom-sql-analytics) — Advanced SQL analytics, window functions, cohort analysis
- [enterprise-data-pipeline-ireland](https://github.com/alansha1/enterprise-data-pipeline-ireland) — ETL pipeline with Great Expectations validation
- [ai-jobfit-analyzer](https://github.com/alansha1/ai-jobfit-analyzer) — NLP/semantic similarity job-fit scoring
- [AIRFARE-FORECASTING](https://github.com/alansha1/AIRFARE-FORECASTING) — 5-model ML comparison, R²=0.869

---

*Built by [Alan Sha](https://linkedin.com/in/alan-sha) · MSc Data Analytics, Dublin Business School*
