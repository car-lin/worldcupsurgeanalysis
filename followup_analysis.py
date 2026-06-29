from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Defines the folder containing exported CSV files from the database
EXPORT_DIR = Path("data/tableau_exports")

# Defines the folder where generated dashboard images will be saved
OUTPUT_DIR = Path("dashboard/screenshots")

# Creates the output directory if it does not already exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# HS commodity name mapping
# -----------------------------
# Maps HS2 commodity codes to readable commodity category names
HS2_MAP = {
    "01": "Live Animals", "02": "Meat", "03": "Fish", "04": "Dairy & Eggs",
    "05": "Animal Products", "06": "Plants", "07": "Vegetables", "08": "Fruit & Nuts",
    "09": "Coffee & Spices", "10": "Cereals", "11": "Milling Products",
    "12": "Oil Seeds", "13": "Gums & Resins", "14": "Vegetable Materials",
    "15": "Fats & Oils", "16": "Prepared Meat/Fish", "17": "Sugar",
    "18": "Cocoa", "19": "Cereal Preparations", "20": "Prepared Vegetables/Fruit",
    "21": "Misc. Food", "22": "Beverages", "23": "Food Industry Residues",
    "24": "Tobacco", "25": "Salt, Stone & Cement", "26": "Ores",
    "27": "Mineral Fuels", "28": "Inorganic Chemicals", "29": "Organic Chemicals",
    "30": "Pharmaceuticals", "31": "Fertilisers", "32": "Dyes & Paints",
    "33": "Perfumes & Cosmetics", "34": "Soap & Waxes", "35": "Proteins",
    "36": "Explosives", "37": "Photo Goods", "38": "Chemical Products",
    "39": "Plastics", "40": "Rubber", "41": "Raw Hides",
    "42": "Leather Goods", "43": "Furskins", "44": "Wood",
    "45": "Cork", "46": "Basketware", "47": "Pulp",
    "48": "Paper", "49": "Printed Books", "50": "Silk",
    "51": "Wool", "52": "Cotton", "53": "Vegetable Fibres",
    "54": "Man-made Filaments", "55": "Man-made Fibres", "56": "Wadding/Felt",
    "57": "Carpets", "58": "Special Fabrics", "59": "Coated Textiles",
    "60": "Knitted Fabrics", "61": "Knitted Clothing", "62": "Woven Clothing",
    "63": "Textile Articles", "64": "Footwear", "65": "Headgear",
    "66": "Umbrellas", "67": "Feathers", "68": "Stone/Cement Articles",
    "69": "Ceramics", "70": "Glass", "71": "Jewellery",
    "72": "Iron & Steel", "73": "Iron/Steel Articles", "74": "Copper",
    "75": "Nickel", "76": "Aluminium", "78": "Lead",
    "79": "Zinc", "80": "Tin", "81": "Other Metals",
    "82": "Tools", "83": "Metal Goods", "84": "Machinery",
    "85": "Electrical Machinery", "86": "Railway", "87": "Vehicles",
    "88": "Aircraft", "89": "Ships", "90": "Medical/Optical",
    "91": "Clocks", "92": "Musical Instruments", "93": "Arms",
    "94": "Furniture", "95": "Toys & Sports", "96": "Misc. Manufactures",
    "97": "Art & Antiques", "99": "Special Categories"
}

def commodity_name(code):
    # Cleans the commodity code and converts it into a string format
    code = str(code).replace(".0", "").strip()

    # Extracts the first two digits of the HS code and pads with zero if needed
    hs2 = code[:2].zfill(2)

    # Returns the readable commodity name, or a default label if the code is not found
    return HS2_MAP.get(hs2, f"Commodity {code}")

def add_commodity_label(df):
    # Creates a copy of the dataframe to avoid modifying the original directly
    df = df.copy()

    # Adds a readable commodity label using the commodity code
    df["commodity_label"] = df["commodity_code"].apply(commodity_name)

    # Returns the dataframe with the added commodity label column
    return df

# -----------------------------
# Load exported tables
# -----------------------------
# Loads the exported CSV tables required for dashboard creation
commodities = pd.read_csv(EXPORT_DIR / "commodity_surges_qatar.csv")
trend = pd.read_csv(EXPORT_DIR / "qatar_monthly_import_trend.csv")
worldbank = pd.read_csv(EXPORT_DIR / "worldbank_indicator_trends.csv")
import_year = pd.read_csv(EXPORT_DIR / "import_by_country_year.csv")
host = pd.read_csv(EXPORT_DIR / "host_country_comparison.csv")
predictions = pd.read_csv(EXPORT_DIR / "predicted_stocking_opportunities.csv")

# Adds readable commodity names to commodity-based datasets
commodities = add_commodity_label(commodities)
predictions = add_commodity_label(predictions)

# -----------------------------
# Clean numeric fields
# -----------------------------
# Converts import value columns to numeric format for analysis and plotting
commodities["total_import_value"] = pd.to_numeric(commodities["total_import_value"], errors="coerce")
trend["monthly_import_value"] = pd.to_numeric(trend["monthly_import_value"], errors="coerce")
predictions["opportunity_score"] = pd.to_numeric(predictions["opportunity_score"], errors="coerce")
predictions["predicted_demand"] = pd.to_numeric(predictions["predicted_demand"], errors="coerce")
predictions["qatar_demand"] = pd.to_numeric(predictions["qatar_demand"], errors="coerce")
import_year["total_import_value"] = pd.to_numeric(import_year["total_import_value"], errors="coerce")

# Creates a proper date column by combining year and month values
trend["date"] = pd.to_datetime(
    trend["year"].astype(str) + "-" + trend["month"].astype(str) + "-01"
)

# Sorts the monthly trend data by date to ensure correct line chart order
trend = trend.sort_values("date")

# Calculates month-on-month percentage growth in import value
trend["growth_rate"] = trend["monthly_import_value"].pct_change() * 100

# ============================================================
# DASHBOARD 1: QATAR DEMAND ANALYSIS
# ============================================================

# Selects the top 10 commodities with the highest total import value
top10 = (
    commodities
    .dropna(subset=["total_import_value"])
    .sort_values("total_import_value", ascending=False)
    .head(10)
)

# Creates a 2x2 dashboard layout for Qatar demand analysis
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Adds the main dashboard title
fig.suptitle("Dashboard 1: Qatar Demand Surge Analysis", fontsize=18)

# Creates a horizontal bar chart for the top 10 imported commodity categories
axes[0, 0].barh(top10["commodity_label"], top10["total_import_value"])
axes[0, 0].set_title("Top 10 Imported Commodity Categories")
axes[0, 0].set_xlabel("Total Import Value")
axes[0, 0].invert_yaxis()

# Creates a line chart showing monthly import value trends
axes[0, 1].plot(trend["date"], trend["monthly_import_value"], marker="o")
axes[0, 1].set_title("Monthly Import Trend")
axes[0, 1].set_xlabel("Month")
axes[0, 1].set_ylabel("Monthly Import Value")
axes[0, 1].tick_params(axis="x", rotation=45)

# Creates a line chart showing monthly import growth rate
axes[1, 0].plot(trend["date"], trend["growth_rate"], marker="o")
axes[1, 0].axhline(0, linewidth=1)
axes[1, 0].set_title("Monthly Import Growth Rate")
axes[1, 0].set_xlabel("Month")
axes[1, 0].set_ylabel("Growth Rate (%)")
axes[1, 0].tick_params(axis="x", rotation=45)

# Creates a pie chart showing the share of the top 10 commodity imports
axes[1, 1].pie(
    top10["total_import_value"],
    labels=top10["commodity_label"],
    autopct="%1.1f%%",
    startangle=90
)
axes[1, 1].set_title("Share of Top 10 Commodity Imports")

# Adjusts chart spacing to prevent overlap
plt.tight_layout()

# Saves the first dashboard as a high-resolution image
plt.savefig(OUTPUT_DIR / "dashboard1_qatar_analysis.png", dpi=300)

# Displays the dashboard
plt.show()

# ============================================================
# DASHBOARD 2: HOST COUNTRY COMPARISON
# ============================================================

# World Bank pivot
# Reshapes World Bank indicator data so each indicator becomes a separate column
wb_pivot = worldbank.pivot_table(
    index="country_iso3",
    columns="indicator_name",
    values="value",
    aggfunc="mean"
).reset_index()

# Creates a 2x2 dashboard layout for host country comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Adds the main dashboard title
fig.suptitle("Dashboard 2: Host Country Comparison", fontsize=18)

# Aggregates total import value by country
country_imports = (
    import_year
    .groupby("country_iso3", as_index=False)["total_import_value"]
    .sum()
    .sort_values("total_import_value", ascending=False)
)

# Creates a bar chart comparing total import value by country
axes[0, 0].bar(country_imports["country_iso3"], country_imports["total_import_value"])
axes[0, 0].set_title("Total Import Value by Country")
axes[0, 0].set_xlabel("Country")
axes[0, 0].set_ylabel("Total Import Value")

# Creates a line chart showing yearly import trends for each country
for country in import_year["country_iso3"].unique():
    subset = import_year[import_year["country_iso3"] == country].sort_values("year")
    axes[0, 1].plot(subset["year"], subset["total_import_value"], marker="o", label=country)

# Adds chart labels and legend for the import trend comparison
axes[0, 1].set_title("Import Trend by Country")
axes[0, 1].set_xlabel("Year")
axes[0, 1].set_ylabel("Total Import Value")
axes[0, 1].legend()

# Creates GDP per capita chart if the required indicator column exists
if "gdp_per_capita" in wb_pivot.columns:
    axes[1, 0].bar(wb_pivot["country_iso3"], wb_pivot["gdp_per_capita"])
    axes[1, 0].set_title("Average GDP per Capita")
    axes[1, 0].set_xlabel("Country")
    axes[1, 0].set_ylabel("GDP per Capita")

# Creates trade openness chart if the required indicator column exists
if "trade_percent_gdp" in wb_pivot.columns:
    axes[1, 1].bar(wb_pivot["country_iso3"], wb_pivot["trade_percent_gdp"])
    axes[1, 1].set_title("Trade Openness (% of GDP)")
    axes[1, 1].set_xlabel("Country")
    axes[1, 1].set_ylabel("Trade % of GDP")

# Adjusts chart spacing to prevent overlap
plt.tight_layout()

# Saves the second dashboard as a high-resolution image
plt.savefig(OUTPUT_DIR / "dashboard2_host_comparison.png", dpi=300)

# Displays the dashboard
plt.show()

# ============================================================
# DASHBOARD 3: 2026 STOCKING PREDICTION
# ============================================================

# Selects the top 10 commodities with the highest opportunity score
top_pred = (
    predictions
    .dropna(subset=["opportunity_score"])
    .sort_values("opportunity_score", ascending=False)
    .head(10)
)

# Creates a 2x2 dashboard layout for 2026 stocking prediction
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Adds the main dashboard title
fig.suptitle("Dashboard 3: Predicted Stocking Opportunities for World Cup 2026", fontsize=18)

# Creates a horizontal bar chart for the top 10 stocking opportunities
axes[0, 0].barh(top_pred["commodity_label"], top_pred["opportunity_score"])
axes[0, 0].set_title("Top 10 Stocking Opportunities")
axes[0, 0].set_xlabel("Opportunity Score")
axes[0, 0].invert_yaxis()

# Creates a histogram showing the spread of opportunity scores across commodities
axes[0, 1].hist(predictions["opportunity_score"].dropna(), bins=20)
axes[0, 1].set_title("Distribution of Opportunity Scores")
axes[0, 1].set_xlabel("Opportunity Score")
axes[0, 1].set_ylabel("Number of Commodities")

# Creates a scatter plot comparing Qatar demand with predicted 2026 demand
axes[1, 0].scatter(predictions["qatar_demand"], predictions["predicted_demand"])
axes[1, 0].set_title("Qatar Demand vs Predicted 2026 Demand")
axes[1, 0].set_xlabel("Qatar Demand")
axes[1, 0].set_ylabel("Predicted 2026 Demand")

# Creates a horizontal bar chart for predicted demand of the top opportunities
axes[1, 1].barh(top_pred["commodity_label"], top_pred["predicted_demand"])
axes[1, 1].set_title("Predicted Demand for Top Opportunities")
axes[1, 1].set_xlabel("Predicted Demand")
axes[1, 1].invert_yaxis()

# Adjusts chart spacing to prevent overlap
plt.tight_layout()

# Saves the third dashboard as a high-resolution image
plt.savefig(OUTPUT_DIR / "dashboard3_prediction_2026.png", dpi=300)

# Displays the dashboard
plt.show()

# Prints confirmation that all dashboard images were generated and saved
print("\nAll dashboard images saved in dashboard/screenshots/")