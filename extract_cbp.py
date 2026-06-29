import zipfile
from pathlib import Path
import requests
import pandas as pd
from settings import load_config

# Sets the base project directory by moving one level up from the current script location
BASE_DIR = Path(__file__).resolve().parents[1]

# Defines folders for storing raw downloaded CBP files and temporary output files
RAW_DIR = BASE_DIR / "data" / "temp" / "cbp_raw"
OUTPUT_DIR = BASE_DIR / "data" / "temp"

# Creates the required folders if they do not already exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Loads configuration values from the project settings file
cfg = load_config()

# Contains the Census County Business Patterns ZIP file URLs for selected years
CBP_URLS = {
    "https://www2.census.gov/programs-surveys/cbp/datasets/2019/cbp19co.zip",
    "https://www2.census.gov/programs-surveys/cbp/datasets/2021/cbp21co.zip",
    "https://www2.census.gov/programs-surveys/cbp/datasets/2022/cbp22co.zip",
    "https://www2.census.gov/programs-surveys/cbp/datasets/2023/cbp23co.zip",
}

# Reads the configured host county information from the settings file
host_counties = cfg["cbp"]["host_counties"]

# Creates a lookup dictionary using county FIPS codes as keys
county_fips = {c["county_fips"]: c for c in host_counties}

# Reads the allowed NAICS sector prefixes from the configuration
allowed_naics_prefixes = set(cfg["cbp"]["naics_sectors"].keys())

# Stores the mapping between NAICS prefixes and industry group names
naics_map = cfg["cbp"]["naics_sectors"]

# Stores cleaned dataframes from each year before combining them
all_cleaned = []

def download_and_extract(url):
    # Extracts the ZIP filename from the URL
    filename = url.split("/")[-1]

    # Defines the local path where the ZIP file will be saved
    zip_path = RAW_DIR / filename

    # Downloads the ZIP file only if it has not already been downloaded
    if not zip_path.exists():
        print(f"Downloading {filename}...")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        zip_path.write_bytes(response.content)

    # Defines a folder where the ZIP file contents will be extracted
    extract_dir = RAW_DIR / filename.replace(".zip", "")

    # Creates the extraction folder if it does not already exist
    extract_dir.mkdir(exist_ok=True)

    # Extracts all files from the ZIP archive into the extraction folder
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)

    # Searches for TXT or CSV files inside the extracted folder
    files = list(extract_dir.glob("*.txt")) + list(extract_dir.glob("*.csv"))

    # Raises an error if no usable data file is found
    if not files:
        raise FileNotFoundError(f"No CSV/TXT inside {filename}")

    # Returns the first detected data file for cleaning
    return files[0]

def clean_cbp(file_path):
    # Prints the name of the file currently being cleaned
    print(f"Cleaning {file_path.name}")

    # Reads the CBP data file as strings to preserve codes such as leading-zero FIPS values
    df = pd.read_csv(file_path, dtype=str)

    # Standardises column names by converting them to uppercase and removing extra spaces
    df.columns = [c.upper().strip() for c in df.columns]

    # Prints available columns to help with debugging and validation
    print("Available columns:", df.columns.tolist())

    # Auto-detect columns
    state_col = next((c for c in ["STATE", "FIPSTATE", "STATEFP"] if c in df.columns), None)
    county_col = next((c for c in ["COUNTY", "FIPCOUNTY", "FIPSCTY", "COUNTYFP"] if c in df.columns), None)
    naics_col = next((c for c in ["NAICS2017", "NAICS2022", "NAICS"] if c in df.columns), None)
    estab_col = next((c for c in ["ESTAB", "ESTABLISHMENTS", "EST"] if c in df.columns), None)
    emp_col = next((c for c in ["EMP", "EMPLOYMENT"] if c in df.columns), None)
    payann_col = next((c for c in ["PAYANN", "ANNUAL_PAYROLL", "AP"] if c in df.columns), None)

    # Stores the detected column names so missing columns can be checked clearly
    required = {
        "state": state_col,
        "county": county_col,
        "naics": naics_col,
        "estab": estab_col,
        "emp": emp_col,
        "payann": payann_col,
    }

    # Identifies any required columns that were not found in the input file
    missing = [name for name, col in required.items() if col is None]

    # Stops execution if any required columns are missing
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available columns: {df.columns.tolist()}")

    # Keeps only the required columns for the project analysis
    df = df[[state_col, county_col, naics_col, estab_col, emp_col, payann_col]].copy()

    # Renames columns into a consistent format across different CBP years
    df.rename(columns={
        state_col: "STATE",
        county_col: "COUNTY",
        naics_col: "naics_code",
        estab_col: "ESTAB",
        emp_col: "EMP",
        payann_col: "PAYANN",
    }, inplace=True)

    # Combines state and county codes to create a full five-digit county FIPS code
    df["state_county_fips"] = df["STATE"].str.zfill(2) + df["COUNTY"].str.zfill(3)

    # Filters the data to include only the configured host counties
    df = df[df["state_county_fips"].isin(county_fips.keys())]

    # Extracts the first two digits of the NAICS code to identify the broad industry sector
    df["naics_prefix"] = df["naics_code"].astype(str).str[:2]

    # Keeps only rows whose NAICS sector is relevant to the project
    df = df[df["naics_prefix"].isin(allowed_naics_prefixes)]

    # Maps each NAICS prefix to a readable industry group name
    df["industry_group"] = df["naics_prefix"].map(naics_map)

    # Adds city names using the county FIPS lookup from the configuration
    df["city"] = df["state_county_fips"].map(lambda x: county_fips[x]["city"])

    # Adds state abbreviations using the county FIPS lookup from the configuration
    df["state_abbr"] = df["state_county_fips"].map(lambda x: county_fips[x]["state"])

    # Converts numeric business indicators from text to numeric values
    for col in ["ESTAB", "EMP", "PAYANN"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Returns the final cleaned and structured CBP dataframe
    return df[
        [
            "city",
            "state_abbr",
            "state_county_fips",
            "naics_code",
            "naics_prefix",
            "industry_group",
            "ESTAB",
            "EMP",
            "PAYANN",
        ]
    ]

# Downloads, extracts, cleans, and stores data for each CBP URL
for url in CBP_URLS:
    file_path = download_and_extract(url)
    cleaned = clean_cbp(file_path)
    all_cleaned.append(cleaned)

# Combines all cleaned yearly CBP datasets into one dataframe
final_df = pd.concat(all_cleaned, ignore_index=True)

# Defines the final output CSV path
output_path = OUTPUT_DIR / "cbp_filtered.csv"

# Saves the combined cleaned dataset as a CSV file
final_df.to_csv(output_path, index=False)

# Prints the output path, number of rows, and a preview of the cleaned data
print(f"\nSaved: {output_path}")
print(f"Rows: {len(final_df)}")
print(final_df.head())