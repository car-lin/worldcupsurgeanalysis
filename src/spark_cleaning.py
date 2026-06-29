from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, to_date, concat, substring

# Imports helper functions to load configuration and environment variables
from settings import load_config, get_env

# Loads configuration values from the YAML config file
cfg = load_config()

# Retrieves Azure Blob Storage connection string from environment variables
connection_string = get_env("AZURE_STORAGE_CONNECTION_STRING")

# Gets the Azure container name from the configuration
container = cfg["azure"]["container_name"]

# Parses the Azure connection string into key-value pairs
parts = dict(item.split("=", 1) for item in connection_string.split(";") if "=" in item)

# Extracts the storage account name and account key from the connection string
account_name = parts["AccountName"]
account_key = parts["AccountKey"]

# Initializes a Spark session with required Azure Blob Storage dependencies
spark = (
    SparkSession.builder
    .appName("WorldCupCleaning")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-azure:3.3.4,com.microsoft.azure:azure-storage:8.6.6"
    )
    .getOrCreate()
)

# Configures Spark to authenticate with Azure Blob Storage
spark._jsc.hadoopConfiguration().set(
    f"fs.azure.account.key.{account_name}.blob.core.windows.net",
    account_key
)

# Constructs the base Azure Blob Storage path
base_path = f"wasbs://{container}@{account_name}.blob.core.windows.net"

# Prints confirmation that Comtrade cleaning is starting
print("Cleaning Comtrade...")

# Defines the raw Comtrade file paths for each country
comtrade_paths = {
    "QAT": "raw/comtrade/comtrade_QAT.csv",
    "USA": "raw/comtrade/comtrade_USA.csv",
    "CAN": "raw/comtrade/comtrade_CAN.csv",
    "MEX": "raw/comtrade/comtrade_MEX.csv",
}

# Stores cleaned Comtrade dataframes before combining them
dfs = []

# Loops through each country and its corresponding Comtrade file path
for iso3, path in comtrade_paths.items():
    # Prints the country currently being read
    print(f"Reading Comtrade: {iso3}")

    # Reads the raw Comtrade CSV file from Azure Blob Storage
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", False)
        .csv(f"{base_path}/{path}")
    )

    # Standardises the commodity code column name if it exists
    if "cmdCode" in df.columns:
        df = df.withColumnRenamed("cmdCode", "commodity_code")

    # Standardises the commodity description column name if it exists
    if "cmdDesc" in df.columns:
        df = df.withColumnRenamed("cmdDesc", "commodity_desc")

    # Standardises different possible trade value column names into one common column
    if "primaryValue" in df.columns:
        df = df.withColumnRenamed("primaryValue", "trade_value")
    elif "TradeValue" in df.columns:
        df = df.withColumnRenamed("TradeValue", "trade_value")
    elif "cifvalue" in df.columns:
        df = df.withColumnRenamed("cifvalue", "trade_value")
    elif "fobvalue" in df.columns:
        df = df.withColumnRenamed("fobvalue", "trade_value")

    # Renames extract_period to period if the original period column is missing
    if "period" not in df.columns and "extract_period" in df.columns:
        df = df.withColumnRenamed("extract_period", "period")

    # Adds country ISO3 code if it is not already present in the dataset
    if "country_iso3" not in df.columns:
        df = df.withColumn("country_iso3", lit(iso3))

    # Adds an empty commodity description column if it does not exist
    if "commodity_desc" not in df.columns:
        df = df.withColumn("commodity_desc", lit(None).cast("string"))

    # Converts the period column to string so year and month can be extracted safely
    df = df.withColumn("period", col("period").cast("string"))

    # Converts the YYYYMM period value into a proper date using the first day of each month
    df = df.withColumn(
        "month_date",
        to_date(
            concat(
                substring(col("period"), 1, 4),
                lit("-"),
                substring(col("period"), 5, 2),
                lit("-01")
            )
        )
    )

    # Converts trade value into double format for numerical analysis
    df = df.withColumn("trade_value", col("trade_value").cast("double"))

    # Converts commodity code and description into string format for consistency
    df = df.withColumn("commodity_code", col("commodity_code").cast("string"))
    df = df.withColumn("commodity_desc", col("commodity_desc").cast("string"))

    # Selects only the cleaned columns required for analysis
    df = df.select(
        "country_iso3",
        "commodity_code",
        "commodity_desc",
        "trade_value",
        "month_date"
    )

    # Adds the cleaned dataframe to the list for later combination
    dfs.append(df)

# Uses the first dataframe as the starting point for combining all country data
comtrade_clean = dfs[0]

# Combines the remaining country dataframes into one Comtrade dataset
for df in dfs[1:]:
    comtrade_clean = comtrade_clean.unionByName(df, allowMissingColumns=True)

# Removes rows where key analytical fields are missing
comtrade_clean = comtrade_clean.dropna(subset=["trade_value", "month_date"])

# Writes the cleaned Comtrade dataset to Azure Blob Storage
comtrade_clean.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/clean/comtrade_clean"
)

# Prints confirmation that Comtrade cleaning is complete
print("Comtrade cleaned and saved")

# Prints confirmation that World Bank cleaning is starting
print("Cleaning World Bank...")

# Reads the raw World Bank CSV file from Azure Blob Storage
worldbank = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(f"{base_path}/raw/worldbank/worldbank_indicators.csv")
)

# Converts year and value columns into correct numeric types
worldbank_clean = (
    worldbank
    .withColumn("year", col("year").cast("int"))
    .withColumn("value", col("value").cast("double"))
)

# Writes the cleaned World Bank dataset to Azure Blob Storage
worldbank_clean.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/clean/worldbank_clean"
)

# Prints confirmation that World Bank cleaning is complete
print("World Bank cleaned and saved")

# Prints confirmation that CBP cleaning is starting
print("Cleaning CBP...")

# Reads the raw CBP CSV file from Azure Blob Storage
cbp = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(f"{base_path}/raw/cbp/cbp_filtered.csv")
)

# Renames CBP columns into readable names and converts business indicators into numeric values
cbp_clean = (
    cbp
    .withColumnRenamed("ESTAB", "establishments")
    .withColumnRenamed("EMP", "employment")
    .withColumnRenamed("PAYANN", "annual_payroll")
    .withColumn("establishments", col("establishments").cast("double"))
    .withColumn("employment", col("employment").cast("double"))
    .withColumn("annual_payroll", col("annual_payroll").cast("double"))
)

# Writes the cleaned CBP dataset to Azure Blob Storage
cbp_clean.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/clean/cbp_clean"
)

# Prints confirmation that CBP cleaning is complete
print("CBP cleaned and saved")

# Stops the Spark session to release resources
spark.stop()

# Prints final confirmation that all cleaning steps are complete
print("\nCleaning complete")
