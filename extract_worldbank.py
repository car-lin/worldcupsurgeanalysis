import requests
import pandas as pd
from pathlib import Path
from settings import load_config

# Sets the base project directory by moving one level up from the current script location
BASE_DIR = Path(__file__).resolve().parents[1]

# Defines the folder where the extracted World Bank data will be stored
OUTPUT_DIR = BASE_DIR / "data" / "temp"

# Creates the output directory if it does not already exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Loads configuration values from the project settings file
cfg = load_config()

# Defines the list of countries (ISO3 codes) to extract data for
COUNTRIES = ["QAT", "USA", "CAN", "MEX"]

# Loads the required World Bank indicators from the configuration
INDICATORS = cfg["worldbank_indicators"]

# Loads the list of years to filter the data
YEARS = cfg["years"]["worldbank"]

# Stores all extracted records before converting into a dataframe
rows = []

# Loops through each country
for country in COUNTRIES:
    # Loops through each indicator code and its descriptive name
    for indicator_code, indicator_name in INDICATORS.items():
        # Constructs the World Bank API URL for the given country and indicator
        url = (
            f"https://api.worldbank.org/v2/country/{country}/indicator/"
            f"{indicator_code}?format=json&per_page=100"
        )

        # Sends a GET request to the API
        response = requests.get(url, timeout=30)

        # Raises an error if the API request fails
        response.raise_for_status()

        # Converts the API response into JSON format
        data = response.json()

        # Checks if the response contains valid data
        if len(data) < 2 or data[1] is None:
            continue

        # Iterates through each data entry returned by the API
        for item in data[1]:
            # Extracts the year from the data entry
            year = int(item["date"])

            # Filters the data to include only the required years
            if year in YEARS:
                # Appends the cleaned record to the rows list
                rows.append({
                    "country_iso3": country,
                    "country_name": item["country"]["value"],
                    "year": year,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "value": item["value"]
                })

# Converts the collected rows into a pandas dataframe
df = pd.DataFrame(rows)

# Defines the output file path for the cleaned World Bank data
output_path = OUTPUT_DIR / "worldbank_indicators.csv"

# Saves the dataframe to a CSV file
df.to_csv(output_path, index=False)

# Prints confirmation of file location and preview of extracted data
print(f"World Bank data saved to: {output_path}")
print(df.head())
print(f"Rows extracted: {len(df)}")