import time
from pathlib import Path
import pandas as pd
import comtradeapicall

# Imports helper functions to load configuration values and environment variables
from settings import load_config, get_env

# Sets the base project directory by moving one level up from the current script location
BASE_DIR = Path(__file__).resolve().parents[1]

# Defines the folder where extracted Comtrade CSV files will be saved
OUTPUT_DIR = BASE_DIR / "data" / "temp" / "comtrade"

# Creates the output folder if it does not already exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Loads project configuration values from the settings file
cfg = load_config()

# Reads the Comtrade API key from environment variables
api_key = get_env("COMTRADE_API_KEY")

# Loads country configuration details, such as ISO3 codes and Comtrade reporter codes
countries = cfg["countries"]

# Controlled subset
# Defines which countries and year ranges should be extracted for the project
extract_plan = {
    "qatar": cfg["years"]["qatar_training"],
    "usa": cfg["years"]["host_prediction"],
    "canada": cfg["years"]["host_prediction"],
    "mexico": cfg["years"]["host_prediction"],
}

def months_for_year(year):
    # Generates all monthly period values for a given year in YYYYMM format
    return [f"{year}{month:02d}" for month in range(1, 13)]

# Loops through each country and its assigned years in the extraction plan
for country_key, years in extract_plan.items():
    # Gets the Comtrade reporter code for the selected country
    reporter_code = countries[country_key]["comtrade_code"]

    # Gets the ISO3 country code used for labelling and output filenames
    country_iso3 = countries[country_key]["iso3"]

    # Stores all extracted monthly dataframes for the current country
    all_rows = []

    # Prints the country currently being extracted
    print(f"\nExtracting Comtrade data for {country_iso3}")

    # Loops through each configured year for the current country
    for year in years:
        # Loops through all 12 monthly periods in the selected year
        for period in months_for_year(year):
            # Prints the current country and month being fetched
            print(f"Fetching {country_iso3} - {period}")

            try:
                # Calls the UN Comtrade API to retrieve monthly import trade data
                df = comtradeapicall.previewFinalData(
                    typeCode="C",
                    freqCode="M",
                    clCode="HS",
                    period=period,
                    reporterCode=reporter_code,
                    cmdCode=None,
                    flowCode="M",
                    partnerCode=None,
                    partner2Code=None,
                    customsCode=None,
                    motCode=None,
                    maxRecords=50000
                )

                # Checks whether the API returned any records
                if df is not None and len(df) > 0:
                    # Converts the returned data into a pandas dataframe
                    df = pd.DataFrame(df)

                    # Adds the country ISO3 code to identify the reporting country
                    df["country_iso3"] = country_iso3

                    # Adds the extraction period to track the month of each record
                    df["extract_period"] = period

                    # Stores the monthly dataframe for later combination
                    all_rows.append(df)

            except Exception as e:
                # Prints the error but allows the extraction process to continue
                print(f"Failed for {country_iso3} {period}: {e}")

            # Pauses briefly between API calls to avoid sending requests too quickly
            time.sleep(1)

    # If data was extracted for the country, combine and save it
    if all_rows:
        # Combines all monthly dataframes for the current country
        country_df = pd.concat(all_rows, ignore_index=True)

        # Defines the output CSV file path for the current country
        output_path = OUTPUT_DIR / f"comtrade_{country_iso3}.csv"

        # Saves the combined country-level Comtrade data to CSV
        country_df.to_csv(output_path, index=False)

        # Prints the saved file location and number of rows extracted
        print(f"Saved {country_iso3}: {output_path}")
        print(f"Rows: {len(country_df)}")
    else:
        # Prints a message if no data was extracted for the current country
        print(f"No data extracted for {country_iso3}")
