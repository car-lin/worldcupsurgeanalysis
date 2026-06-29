import pandas as pd
from sqlalchemy import create_engine
import os

# Imports function to load environment variables from a .env file
from dotenv import load_dotenv

# Loads environment variables from the .env file into the system environment
load_dotenv()

# Retrieves the PostgreSQL database connection URL from environment variables
POSTGRES_URL = os.getenv("POSTGRES_URL")

# Creates a SQLAlchemy engine to establish a connection with the PostgreSQL database
engine = create_engine(POSTGRES_URL)

# List of database tables that need to be exported for Tableau dashboard usage
tables = [
    "commodity_surges_qatar",
    "qatar_monthly_import_trend",
    "worldbank_indicator_trends",
    "import_by_country_year",
    "host_country_comparison",
    "predicted_stocking_opportunities"
]

# Iterates through each table in the list
for table in tables:
    # Executes a SQL query to fetch all records from the current table
    df = pd.read_sql(f"SELECT * FROM {table}", engine)

    # Exports the table data into a CSV file inside the Tableau exports folder
    df.to_csv(f"data/tableau_exports/{table}.csv", index=False)

    # Prints confirmation that the table has been successfully exported
    print(f"Exported {table}")