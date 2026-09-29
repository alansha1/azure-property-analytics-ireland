"""
========================================================
 REPORTING LAYER — Excel Dashboard + Charts
========================================================
 Simulates: Power BI consuming Gold layer tables via
 Azure Synapse DirectQuery, with Excel export for
 offline distribution.

 In production Azure:
   Input   → Azure Synapse SQL Pool (gold tables)
   Report  → Power BI .pbix connected via DirectQuery
   Export  → Excel via Power BI export / Azure Logic App

 Outputs:
   output/reports/ireland_property_report.xlsx  (8 sheets)
   output/charts/  (6 PNG charts)
========================================================
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from openpyxl import load_workbook
from openpyxl.styles import (PatternFill, Font, Alignment, Border, Side,
                              GradientFill)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, Reference
import os, warnings
warnings.filterwarnings("ignore")

GOLD    = "data/gold"
CHARTS  = "output/charts"
REPORTS = "output/reports"
os.makedirs(CHARTS, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

# ── Load gold tables ──────────────────────────────────────────────────────────
monthly   = pd.read_csv(f"{GOLD}/monthly_trends.csv")
county    = pd.read_csv(f"{GOLD}/county_summary.csv")
prop_mix  = pd.read_csv(f"{GOLD}/property_type_mix.csv")
bands     = pd.read_csv(f"{GOLD}/price_band_dist.csv")
yoy       = pd.read_csv(f"{GOLD}/yoy_growth.csv")
region    = pd.read_csv(f"{GOLD}/region_comparison.csv")
new_old   = pd.read_csv(f"{GOLD}/new_vs_second_hand.csv")
silver    = pd.read_csv("data/silver/ppr_clean.csv", parse_dates=["sale_date"])

# colour palette
NAVY   = "#1F3864"
TEAL   = "#2EC4B6"
ORANGE = "#F4A261"
GREEN  = "#3DDC84"
PURPLE = "#9B72CF"
PINK   = "#E76F9A"
YELLOW = "#F9C74F"
BGRAY  = "#F7F8FC"

def fmt_euro(ax, axis="y"):
    fmt = mticker.FuncFormatter(lambda x, _: f"€{x/1000:.0f}k" if x < 1_000_000 else f"€{x/1_000_000:.1f}M")
    if axis == "y": ax.yaxis.set_major_formatter(fmt)
    else: ax.xaxis.set_major_formatter(fmt)

# ════════════════════════════════════════════════════════
# CHART 1 — National Average Price Trend (2019–2024)
# ════════════════════════════════════════════════════════
national_monthly = (
    silver.groupby("month_label")["price"]
    .agg(["mean","median","count"]).reset_index()
    .sort_values("month_label")
)

fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor(BGRAY)
ax.set_facecolor(BGRAY)
ax.plot(range(len(national_monthly)), national_monthly["mean"],   color=NAVY,   lw=2.5, label="Average Price")
ax.plot(range(len(national_monthly)), national_monthly["median"], color=TEAL,   lw=2,   ls="--", label="Median Price")
ax.fill_between(range(len(national_monthly)), national_monthly["mean"], national_monthly["median"], alpha=0.1, color=NAVY)
xticks = [i for i, m in enumerate(national_monthly["month_label"]) if m.endswith("-01")]
ax.set_xticks(xticks)
ax.set_xticklabels([national_monthly["month_label"].iloc[i][:4] for i in xticks], fontsize=11)
fmt_euro(ax)
ax.set_title("Irish Property Market — National Price Trend (2019–2024)", fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax.set_xlabel("Year", fontsize=11)
ax.set_ylabel("Price", fontsize=11)
ax.legend(fontsize=11)
ax.grid(axis="y", alpha=0.3)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{CHARTS}/01_national_price_trend.png", dpi=150, bbox_inches="tight")
plt.close()
print("[CHART 1] National price trend")

# ════════════════════════════════════════════════════════
# CHART 2 — Average Price by County (2024)
# ════════════════════════════════════════════════════════
county_2024 = (
    silver[silver["year"] == 2024]
    .groupby("county")["price"].mean()
    .sort_values(ascending=True)
    .reset_index()
)
colors_bar = [TEAL if c != "Dublin" else NAVY for c in county_2024["county"]]

fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor(BGRAY)
ax.set_facecolor(BGRAY)
bars = ax.barh(county_2024["county"], county_2024["price"], color=colors_bar, edgecolor="white", linewidth=0.5)
for bar, val in zip(bars, county_2024["price"]):
    ax.text(bar.get_width() + 3000, bar.get_y() + bar.get_height()/2,
            f"€{val/1000:.0f}k", va="center", fontsize=9, color=NAVY)
fmt_euro(ax, "x")
ax.set_title("Average Property Price by County — 2024", fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax.set_xlabel("Average Price", fontsize=11)
ax.spines[["top","right","left"]].set_visible(False)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{CHARTS}/02_county_avg_price.png", dpi=150, bbox_inches="tight")
plt.close()
print("[CHART 2] County avg price")

# ════════════════════════════════════════════════════════
# CHART 3 — YoY Price Growth by Region
# ════════════════════════════════════════════════════════
region_yoy = (
    region[region["year"] >= 2020].copy()
    .sort_values(["region","year"])
)
region_yoy["prev"] = region_yoy.groupby("region")["avg_price"].shift(1)
region_yoy["growth"] = ((region_yoy["avg_price"] - region_yoy["prev"]) / region_yoy["prev"] * 100).round(1)
region_yoy = region_yoy.dropna(subset=["growth"])

regions = region_yoy["region"].unique()
colors_r = [NAVY, TEAL, ORANGE, PURPLE, GREEN]
fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor(BGRAY)
ax.set_facecolor(BGRAY)
for i, reg in enumerate(regions):
    d = region_yoy[region_yoy["region"] == reg].sort_values("year")
    ax.plot(d["year"], d["growth"], marker="o", lw=2, color=colors_r[i % len(colors_r)], label=reg)
ax.axhline(0, color="gray", lw=1, ls="--")
ax.set_title("Year-on-Year Price Growth by Region", fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax.set_ylabel("YoY Growth (%)", fontsize=11)
ax.set_xlabel("Year", fontsize=11)
ax.legend(fontsize=10, loc="upper right")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:+.0f}%"))
ax.grid(axis="y", alpha=0.3)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{CHARTS}/03_region_yoy_growth.png", dpi=150, bbox_inches="tight")
plt.close()
print("[CHART 3] Region YoY growth")

# ════════════════════════════════════════════════════════
# CHART 4 — Price Band Distribution 2019 vs 2024
# ════════════════════════════════════════════════════════
band_order = ["Under €150k","€150k–€250k","€250k–€350k","€350k–€500k","€500k–€750k","Over €750k"]
b19 = bands[bands["year"]==2019].set_index("price_band")["pct_of_year"].reindex(band_order).fillna(0)
b24 = bands[bands["year"]==2024].set_index("price_band")["pct_of_year"].reindex(band_order).fillna(0)

x = np.arange(len(band_order))
w = 0.38
fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor(BGRAY)
ax.set_facecolor(BGRAY)
ax.bar(x - w/2, b19, w, label="2019", color=TEAL, alpha=0.85, edgecolor="white")
ax.bar(x + w/2, b24, w, label="2024", color=NAVY, alpha=0.85, edgecolor="white")
ax.set_xticks(x)
ax.set_xticklabels(band_order, rotation=20, ha="right", fontsize=10)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}%"))
ax.set_title("Price Band Distribution — 2019 vs 2024", fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax.set_ylabel("% of Sales", fontsize=11)
ax.legend(fontsize=11)
ax.grid(axis="y", alpha=0.3)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{CHARTS}/04_price_band_shift.png", dpi=150, bbox_inches="tight")
plt.close()
print("[CHART 4] Price band distribution")

# ════════════════════════════════════════════════════════
# CHART 5 — Property Type Market Share (2024)
# ════════════════════════════════════════════════════════
prop_2024 = prop_mix[prop_mix["year"]==2024][["property_type","market_share_pct"]].sort_values("market_share_pct", ascending=False)
colors_pie = [NAVY, TEAL, ORANGE, PURPLE, GREEN]
fig, ax = plt.subplots(figsize=(7, 6))
fig.patch.set_facecolor(BGRAY)
wedges, texts, auts = ax.pie(
    prop_2024["market_share_pct"],
    labels=prop_2024["property_type"],
    autopct="%1.1f%%",
    colors=colors_pie[:len(prop_2024)],
    startangle=140,
    pctdistance=0.82,
    wedgeprops={"edgecolor":"white","linewidth":1.5}
)
for t in texts: t.set_fontsize(11)
for a in auts: a.set_fontsize(10); a.set_color("white"); a.set_fontweight("bold")
ax.set_title("Property Type Market Share — 2024", fontsize=14, fontweight="bold", color=NAVY, pad=14)
plt.tight_layout()
plt.savefig(f"{CHARTS}/05_property_type_mix.png", dpi=150, bbox_inches="tight")
plt.close()
print("[CHART 5] Property type mix")

# ════════════════════════════════════════════════════════
# CHART 6 — New Dwelling Premium
# ════════════════════════════════════════════════════════
new_premium = (
    new_old[new_old["property_type"].isin(["Detached","Semi-Detached","Apartment"])]
    .groupby(["year","new_dwelling"])["avg_price"].mean()
    .reset_index()
)
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor(BGRAY)
ax.set_facecolor(BGRAY)
for nd, col, lbl in [("Yes", ORANGE, "New Dwelling"), ("No", NAVY, "Second-Hand")]:
    d = new_premium[new_premium["new_dwelling"]==nd].sort_values("year")
    ax.plot(d["year"], d["avg_price"], marker="o", lw=2.5, color=col, label=lbl)
ax.fill_between(
    new_premium[new_premium["new_dwelling"]=="Yes"]["year"].values,
    new_premium[new_premium["new_dwelling"]=="Yes"]["avg_price"].values,
    new_premium[new_premium["new_dwelling"]=="No"]["avg_price"].values,
    alpha=0.12, color=ORANGE, label="Premium gap"
)
fmt_euro(ax)
ax.set_title("New Dwelling Premium vs Second-Hand — Average Price", fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax.set_xlabel("Year", fontsize=11)
ax.set_ylabel("Average Price", fontsize=11)
ax.legend(fontsize=11)
ax.grid(axis="y", alpha=0.3)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{CHARTS}/06_new_dwelling_premium.png", dpi=150, bbox_inches="tight")
plt.close()
print("[CHART 6] New dwelling premium")

# ════════════════════════════════════════════════════════
# EXCEL REPORT — 8 sheets
# ════════════════════════════════════════════════════════
REPORT_PATH = f"{REPORTS}/ireland_property_analytics.xlsx"

with pd.ExcelWriter(REPORT_PATH, engine="openpyxl") as writer:

    # ── KPI Summary ──
    national_avg = silver["price"].mean()
    national_med = silver["price"].median()
    total_sales  = len(silver)
    total_vol    = silver["price"].sum()
    avg_2024     = silver[silver["year"]==2024]["price"].mean()
    avg_2019     = silver[silver["year"]==2019]["price"].mean()
    growth_pct   = (avg_2024 - avg_2019) / avg_2019 * 100

    kpi = pd.DataFrame({
        "Metric": [
            "Total Sales (2019–2024)", "Total Market Volume",
            "National Average Price (all years)", "National Median Price (all years)",
            "Average Price 2024", "Average Price 2019",
            "Price Growth 2019→2024 (%)",
            "Highest Avg County (2024)", "Lowest Avg County (2024)"
        ],
        "Value": [
            f"{total_sales:,}", f"€{total_vol/1e9:.2f}B",
            f"€{national_avg:,.0f}", f"€{national_med:,.0f}",
            f"€{avg_2024:,.0f}", f"€{avg_2019:,.0f}",
            f"+{growth_pct:.1f}%",
            county_2024.sort_values("price", ascending=False).iloc[0]["county"],
            county_2024.sort_values("price").iloc[0]["county"]
        ]
    })
    kpi.to_excel(writer, sheet_name="Executive Summary", index=False)

    # ── Data sheets ──
    county.to_excel(writer,   sheet_name="County Summary",     index=False)
    monthly.to_excel(writer,  sheet_name="Monthly Trends",     index=False)
    yoy.to_excel(writer,      sheet_name="YoY Growth",         index=False)
    region.to_excel(writer,   sheet_name="Region Comparison",  index=False)
    prop_mix.to_excel(writer, sheet_name="Property Type Mix",  index=False)
    bands.to_excel(writer,    sheet_name="Price Bands",        index=False)
    new_old.to_excel(writer,  sheet_name="New vs Second Hand", index=False)

# ── Style the workbook ────────────────────────────────────────────────────────
wb = load_workbook(REPORT_PATH)

HEADER_FILL  = PatternFill("solid", fgColor="1F3864")
HEADER_FONT  = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
ALTROW_FILL  = PatternFill("solid", fgColor="EBF0FA")
KPI_FILL     = PatternFill("solid", fgColor="2EC4B6")
KPI_FONT     = Font(bold=True, color="FFFFFF", name="Calibri", size=12)
BORDER_THIN  = Border(
    left=Side(style="thin", color="D0D0D0"),
    right=Side(style="thin", color="D0D0D0"),
    bottom=Side(style="thin", color="D0D0D0"),
)

def style_sheet(ws, alt_rows=True):
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 32)
    if alt_rows:
        for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
            for cell in row:
                if i % 2 == 0:
                    cell.fill = ALTROW_FILL
                cell.border = BORDER_THIN
                cell.alignment = Alignment(horizontal="left")

for name in wb.sheetnames:
    style_sheet(wb[name])

# Special KPI styling
ws_kpi = wb["Executive Summary"]
ws_kpi.sheet_view.showGridLines = False
for row in ws_kpi.iter_rows(min_row=2, max_col=2):
    row[0].font = Font(bold=True, name="Calibri", size=11, color="1F3864")
    row[1].font = Font(bold=True, name="Calibri", size=12, color="2EC4B6")
    row[1].alignment = Alignment(horizontal="right")

wb.save(REPORT_PATH)
print(f"\n[REPORT] Excel saved → {REPORT_PATH}")
print(f"[REPORT] Charts saved → {CHARTS}/")
print("\n✅ Pipeline complete — all layers processed.")
