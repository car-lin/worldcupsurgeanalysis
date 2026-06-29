import os
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Loads environment variables from the .env file
load_dotenv()

# Retrieves the PostgreSQL connection URL from environment variables
POSTGRES_URL = os.getenv("POSTGRES_URL")

# Configures the Streamlit page title and layout
st.set_page_config(
    page_title="World Cup Demand Surge Dashboard",
    layout="wide"
)

# Defines custom colours used throughout the dashboard
GREEN = "#A8D5BA"
DARK_GREEN = "#84A98C"

# Adds custom CSS styling for KPI cards
st.markdown("""
<style>
.kpi-card {
    padding: 20px;
    border-radius: 18px;
    color: #1a1a1a;
    text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.18);
    margin-bottom: 10px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 800;
}
.kpi-label {
    font-size: 14px;
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

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
    # Cleans the commodity code and converts it into a readable HS2 category
    code = str(code).replace(".0", "").strip()
    hs2 = code[:2].zfill(2)
    return HS2_MAP.get(hs2, f"Commodity {code}")


def kpi(label, value, color):
    # Displays a custom styled KPI card with a label, value, and background colour
    st.markdown(
        f"""
        <div class="kpi-card" style="background:{color};">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def apply_green_theme(fig):
    # Applies green styling to bar and scatter charts
    for trace in fig.data:
        if trace.type == "bar":
            trace.marker.color = GREEN
        elif trace.type == "scatter":
            trace.line.color = DARK_GREEN
            trace.marker.color = GREEN

    # Applies a dark dashboard theme to the chart layout
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font=dict(color="#F5F5F5"),
        title_font=dict(size=18)
    )
    return fig


def apply_dark_theme(fig):
    # Applies a consistent dark theme to Plotly charts
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font=dict(color="#F5F5F5"),
        title_font=dict(size=18)
    )
    return fig


@st.cache_data
def load_table(table):
    # Creates a database engine using the PostgreSQL connection URL
    engine = create_engine(POSTGRES_URL)

    # Reads the selected PostgreSQL table into a pandas dataframe
    return pd.read_sql(f"SELECT * FROM {table}", engine)


# Loads all required analysis tables from PostgreSQL
commodity = load_table("commodity_surges_qatar")
monthly = load_table("qatar_monthly_import_trend")
host = load_table("host_country_comparison")
wb = load_table("worldbank_indicator_trends")
imports_year = load_table("import_by_country_year")
prediction = load_table("predicted_stocking_opportunities")

# Adds readable commodity names to commodity and prediction datasets
commodity["commodity_name"] = commodity["commodity_code"].apply(commodity_name)
prediction["commodity_name"] = prediction["commodity_code"].apply(commodity_name)

# Creates a proper date column for monthly trend analysis
monthly["date"] = pd.to_datetime(
    monthly["year"].astype(str) + "-" + monthly["month"].astype(str) + "-01"
)

# Sorts monthly records by date to ensure correct line chart order
monthly = monthly.sort_values("date")

# Calculates month-on-month import growth rate
monthly["growth_rate"] = monthly["monthly_import_value"].pct_change() * 100

# Displays the main dashboard title
st.title("⚽ World Cup Demand Surge Analytics")

# Creates a sidebar navigation menu for selecting dashboards
page = st.sidebar.radio(
    "Select Dashboard",
    [
        "1. Qatar Demand Analysis",
        "2. Host Country Comparison",
        "3. Prediction for 2026"
    ]
)

# =========================================================
# DASHBOARD 1: QATAR DEMAND ANALYSIS
# =========================================================
if page == "1. Qatar Demand Analysis":
    # Displays dashboard heading
    st.header("Dashboard 1: Qatar Demand Surge Analysis")

    # Allows the user to filter Qatar monthly data by year
    years = st.sidebar.multiselect(
        "Select Year",
        sorted(monthly["year"].unique()),
        default=sorted(monthly["year"].unique())
    )

    # Filters monthly data based on selected years
    monthly_f = monthly[monthly["year"].isin(years)]

    # Creates three KPI columns
    c1, c2, c3 = st.columns(3)
    with c1:
        # Shows total import value for the selected period
        kpi("Total Import Value", f"{monthly_f['monthly_import_value'].sum()/1e9:.2f}B", "#D8EFD3")
    with c2:
        # Shows average monthly import value
        kpi("Average Monthly Import", f"{monthly_f['monthly_import_value'].mean()/1e6:.2f}M", "#FFE5EC")
    with c3:
        # Shows the highest monthly import value
        kpi("Peak Monthly Import", f"{monthly_f['monthly_import_value'].max()/1e9:.2f}B", "#E0FBFC")

    # Displays monthly import trend section
    st.subheader("Monthly Import Trend")

    # Creates a line chart for monthly import values
    fig1 = px.line(
        monthly_f,
        x="date",
        y="monthly_import_value",
        markers=True,
        title="Monthly Import Trend Before Qatar 2022",
        labels={"date": "Month", "monthly_import_value": "Monthly Import Value"}
    )
    fig1.update_traces(line_color=DARK_GREEN, marker_color=GREEN)
    fig1 = apply_dark_theme(fig1)
    st.plotly_chart(fig1, use_container_width=True)

    # Displays monthly growth rate section
    st.subheader("Monthly Import Growth Rate")

    # Creates a line chart for monthly import growth rate
    fig2 = px.line(
        monthly_f,
        x="date",
        y="growth_rate",
        markers=True,
        title="Monthly Import Growth Rate",
        labels={"date": "Month", "growth_rate": "Growth Rate (%)"}
    )
    fig2.update_traces(line_color=DARK_GREEN, marker_color=GREEN)
    fig2 = apply_dark_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

    # Displays top commodities section
    st.subheader("Top Imported Commodity Categories")

    # Allows the user to choose how many top commodities to display
    top_n = st.slider("Select number of commodities", 5, 20, 10)

    # Groups imports by commodity and selects the top N categories
    top = (
        commodity.groupby("commodity_name", as_index=False)["total_import_value"]
        .sum()
        .sort_values("total_import_value", ascending=False)
        .head(top_n)
    )

    # Creates a horizontal bar chart for top imported commodity categories
    fig3 = px.bar(
        top,
        x="total_import_value",
        y="commodity_name",
        orientation="h",
        title=f"Top {top_n} Imported Commodity Categories",
        labels={"total_import_value": "Import Value", "commodity_name": "Commodity"},
        color_discrete_sequence=[GREEN]
    )
    fig3.update_layout(yaxis={"categoryorder": "total ascending"})
    fig3 = apply_green_theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)

    # Displays commodity share section
    st.subheader("Share of Top Commodity Imports")

    # Creates a pie chart showing proportional share of top imported commodities
    fig4 = px.pie(
        top,
        names="commodity_name",
        values="total_import_value",
        title="Share of Top Imported Commodities",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig4 = apply_dark_theme(fig4)
    st.plotly_chart(fig4, use_container_width=True)

# =========================================================
# DASHBOARD 2: HOST COUNTRY COMPARISON
# =========================================================
elif page == "2. Host Country Comparison":
    # Displays dashboard heading
    st.header("Dashboard 2: Host Country Comparison")

    # Allows the user to filter selected host countries
    countries = st.sidebar.multiselect(
        "Select Countries",
        sorted(host["country_iso3"].unique()),
        default=sorted(host["country_iso3"].unique())
    )

    # Filters datasets based on selected countries
    host_f = host[host["country_iso3"].isin(countries)]
    imports_f = imports_year[imports_year["country_iso3"].isin(countries)]
    wb_f = wb[wb["country_iso3"].isin(countries)]

    # Creates three KPI columns
    c1, c2, c3 = st.columns(3)
    with c1:
        # Shows number of countries currently compared
        kpi("Countries Compared", host_f["country_iso3"].nunique(), "#FDE2E4")
    with c2:
        # Identifies the country with the highest total import value
        highest = host_f.sort_values("total_import_value", ascending=False)["country_iso3"].iloc[0]
        kpi("Highest Import Country", highest, "#E2ECE9")
    with c3:
        # Shows combined import value across selected countries
        kpi("Total Import Value", f"{host_f['total_import_value'].sum()/1e12:.2f}T", "#D8E2DC")

    # Displays total import comparison section
    st.subheader("Total Import Value by Country")

    # Creates a bar chart comparing total imports by country
    fig5 = px.bar(
        host_f,
        x="country_iso3",
        y="total_import_value",
        title="Total Import Value by Host Country",
        labels={"country_iso3": "Country", "total_import_value": "Total Import Value"},
        color_discrete_sequence=[GREEN]
    )
    fig5 = apply_green_theme(fig5)
    st.plotly_chart(fig5, use_container_width=True)

    # Displays import trend section
    st.subheader("Import Trend by Country")

    # Creates a line chart showing import trend over years by country
    fig6 = px.line(
        imports_f,
        x="year",
        y="total_import_value",
        color="country_iso3",
        markers=True,
        title="Import Trend by Country",
        labels={"year": "Year", "total_import_value": "Total Import Value"}
    )
    fig6.update_traces(line_color=DARK_GREEN, marker_color=GREEN)
    fig6 = apply_dark_theme(fig6)
    st.plotly_chart(fig6, use_container_width=True)

    # Displays World Bank indicator comparison section
    st.subheader("World Bank Indicator Comparison")

    # Allows the user to select a World Bank indicator for comparison
    indicator = st.selectbox(
        "Select Indicator",
        sorted(wb_f["indicator_name"].unique())
    )

    # Filters World Bank data to the selected indicator
    wb_indicator = wb_f[wb_f["indicator_name"] == indicator]

    # Creates a bar chart comparing the selected indicator by country
    fig7 = px.bar(
        wb_indicator,
        x="country_iso3",
        y="value",
        color="country_iso3",
        title=f"{indicator} by Country",
        labels={"country_iso3": "Country", "value": indicator}
    )
    fig7 = apply_dark_theme(fig7)
    st.plotly_chart(fig7, use_container_width=True)

# =========================================================
# DASHBOARD 3: PREDICTION FOR 2026
# =========================================================
else:
    # Displays dashboard heading
    st.header("Dashboard 3: Predicted Stocking Opportunities for 2026")

    # Allows the user to select how many top predicted commodities to display
    top_n = st.sidebar.slider("Top predicted commodities", 5, 25, 10)

    # Groups prediction results by commodity and aggregates key demand metrics
    pred_grouped = (
        prediction.groupby("commodity_name", as_index=False)
        .agg({
            "opportunity_score": "sum",
            "predicted_demand": "sum",
            "qatar_demand": "sum"
        })
        .sort_values("opportunity_score", ascending=False)
    )

    # Selects the top predicted commodity opportunities
    top_pred = pred_grouped.head(top_n)

    # Creates three KPI columns
    c1, c2, c3 = st.columns(3)
    with c1:
        # Shows total predicted demand across all commodities
        kpi("Total Predicted Demand", f"{prediction['predicted_demand'].sum()/1e9:.2f}B", "#E6F4EA")
    with c2:
        # Shows the commodity with the highest opportunity score
        kpi("Highest Opportunity", top_pred["commodity_name"].iloc[0], "#FFF1E6")
    with c3:
        # Shows the maximum opportunity score
        kpi("Max Opportunity Score", f"{top_pred['opportunity_score'].max():,.0f}", "#E0FBFC")

    # Displays top stocking opportunities section
    st.subheader("Top Stocking Opportunities")

    # Creates a horizontal bar chart for top stocking opportunities
    fig8 = px.bar(
        top_pred,
        x="opportunity_score",
        y="commodity_name",
        orientation="h",
        title=f"Top {top_n} Stocking Opportunities",
        labels={"opportunity_score": "Opportunity Score", "commodity_name": "Commodity"},
        color_discrete_sequence=[GREEN]
    )
    fig8.update_layout(yaxis={"categoryorder": "total ascending"})
    fig8 = apply_green_theme(fig8)
    st.plotly_chart(fig8, use_container_width=True)

    # Displays predicted demand section
    st.subheader("Predicted Demand by Commodity")

    # Creates a horizontal bar chart showing predicted demand by commodity
    fig9 = px.bar(
        top_pred,
        x="predicted_demand",
        y="commodity_name",
        orientation="h",
        title="Predicted Demand by Commodity",
        labels={"predicted_demand": "Predicted Demand", "commodity_name": "Commodity"},
        color_discrete_sequence=[GREEN]
    )
    fig9.update_layout(yaxis={"categoryorder": "total ascending"})
    fig9 = apply_green_theme(fig9)
    st.plotly_chart(fig9, use_container_width=True)

    # Displays opportunity score distribution section
    st.subheader("Opportunity Score Distribution")

    # Creates a histogram showing the distribution of opportunity scores
    fig10 = px.histogram(
        pred_grouped,
        x="opportunity_score",
        nbins=30,
        title="Distribution of Opportunity Scores",
        labels={"opportunity_score": "Opportunity Score"},
        color_discrete_sequence=[GREEN]
    )
    fig10 = apply_green_theme(fig10)
    st.plotly_chart(fig10, use_container_width=True)

    # Displays demand comparison section
    st.subheader("Qatar Demand vs Predicted 2026 Demand")

    # Creates a scatter plot comparing Qatar baseline demand with predicted 2026 demand
    fig11 = px.scatter(
        pred_grouped,
        x="qatar_demand",
        y="predicted_demand",
        hover_name="commodity_name",
        title="Qatar Demand vs Predicted 2026 Demand",
        labels={"qatar_demand": "Qatar Demand", "predicted_demand": "Predicted 2026 Demand"},
        color_discrete_sequence=[GREEN]
    )
    fig11.update_traces(marker=dict(color=GREEN, size=10))
    fig11 = apply_dark_theme(fig11)
    st.plotly_chart(fig11, use_container_width=True)