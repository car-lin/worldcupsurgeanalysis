# World Cup Demand Surge Analytics

## Overview
This project builds an end-to-end big data pipeline to analyse international trade patterns and predict demand surges for the FIFA World Cup 2026.

The system:
- Extracts global trade and economic data
- Processes large datasets using Apache Spark
- Stores results in PostgreSQL (Supabase)
- Generates insights and dashboards using Streamlit

---

## Datasets

### 1. UN Comtrade
- Provides international trade data at commodity level (HS codes)
- Used for demand surge detection

### 2. World Bank Indicators
- GDP, inflation, trade % GDP
- Used for cross-country comparison

### 3. US Census Business Patterns (CBP)
- Industry-level data (employment, establishments)
- Used for supply-side context

### 4. Event Metadata
- Custom dataset with World Cup timelines

---

## How to Get API Keys

### UN Comtrade API
1. Go to: https://comtrade.un.org
2. Sign up/login
3. Generate API key from profile

### World Bank API
- No API key required
- Public API: https://data.worldbank.org

---


## Environment Variables

Create a `.env` file: (There is a env.txt file in root, after config rename it to .env)

```
COMTRADE_API_KEY=your_api_key
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
POSTGRES_URL=your_postgres_url
```

---

##  Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ️ PostgreSQL (Supabase) Setup

1. Go to https://supabase.com
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string

Add to `.env`:
```
POSTGRES_URL=your_postgres_url
```

---

##  Azure Blob Storage Setup

1. Go to Azure Portal
2. Create Storage Account
3. Create a Container (e.g., worldcup-data)
4. Go to Access Keys
5. Copy connection string

Add to `.env`:
```
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

Edit in `config.yaml`:
```
azure:
  container_name: your_container_name
```

---

##  Run the Pipeline

```bash
python main.py
```

This will:
1. Extract data from APIs
2. Upload to Azure Blob
3. Clean using Spark
4. Perform 3 analyses
5. Store results in PostgreSQL

---

## Output

### PostgreSQL Tables
- commodity_surges_qatar
- qatar_monthly_import_trend
- worldbank_indicator_trends
- import_by_country_year
- host_country_comparison
- predicted_stocking_opportunities

### Dashboard

Run:
```bash
streamlit run src/streamlit_app.py
```

You will get:
- Qatar Demand Analysis
- Country Comparison Dashboard
- 2026 Demand Prediction

---

## Technologies Used
- Python
- Apache Spark
- Azure Blob Storage
- PostgreSQL (Supabase)
- Streamlit

---

## Author
Carline Imakulate Vincent Raj
