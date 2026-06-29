from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, avg, countDistinct, year

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
    .appName("Analysis2_HostCountryComparison")
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

# -----------------------------
# Load cleaned datasets
# -----------------------------
# Reads the cleaned Comtrade dataset from Azure Blob Storage
comtrade = spark.read.csv(
    f"{base_path}/processed/clean/comtrade_clean",
    header=True,
    inferSchema=True
)

# Reads the cleaned World Bank dataset from Azure Blob Storage
worldbank = spark.read.csv(
    f"{base_path}/processed/clean/worldbank_clean",
    header=True,
    inferSchema=True
)

# -----------------------------
# 1. World Bank indicator trends
# -----------------------------
# Filters valid World Bank records and selects required columns for trend analysis
worldbank_trends = (
    worldbank
    .filter(col("value").isNotNull())
    .select(
        "country_iso3",
        "country_name",
        "year",
        "indicator_name",
        "value"
    )
)

# Writes World Bank indicator trend output to Azure Blob Storage
worldbank_trends.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/analysis2/worldbank_indicator_trends"
)

# -----------------------------
# 2. Total imports by country/year
# -----------------------------
# Removes aggregate commodity rows and extracts year from the monthly date column
comtrade = (
    comtrade
    .filter(col("commodity_code") != "TOTAL")
    .withColumn("year", year("month_date"))
)

# Aggregates total import value and number of distinct commodities by country and year
import_by_country_year = (
    comtrade
    .groupBy("country_iso3", "year")
    .agg(
        spark_sum("trade_value").alias("total_import_value"),
        countDistinct("commodity_code").alias("distinct_commodities")
    )
    .orderBy("country_iso3", "year")
)

# Writes country-year import summary output to Azure Blob Storage
import_by_country_year.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/analysis2/import_by_country_year"
)

# -----------------------------
# 3. Host country comparison summary
# -----------------------------
# Use latest available non-null World Bank values
# Aggregates World Bank indicators to get average indicator values by country and indicator
latest_wb = (
    worldbank
    .filter(col("value").isNotNull())
    .groupBy("country_iso3", "country_name", "indicator_name")
    .agg(
        avg("value").alias("average_indicator_value")
    )
)

# Converts indicator names into separate columns for easier country comparison
wb_pivot = (
    latest_wb
    .groupBy("country_iso3", "country_name")
    .pivot("indicator_name")
    .agg(avg("average_indicator_value"))
)

# Creates an import summary by country using Comtrade data
import_summary = (
    comtrade
    .groupBy("country_iso3")
    .agg(
        spark_sum("trade_value").alias("total_import_value"),
        avg("trade_value").alias("average_transaction_value"),
        countDistinct("commodity_code").alias("distinct_commodities")
    )
)

# Combines World Bank indicators with import summary data for host comparison
host_comparison = (
    wb_pivot
    .join(import_summary, on="country_iso3", how="left")
    .orderBy("country_iso3")
)

# Writes the final host country comparison output to Azure Blob Storage
host_comparison.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/analysis2/host_country_comparison"
)

# Prints confirmation that the analysis has completed
print("Analysis 2 complete")

# Stops the Spark session to release resources
spark.stop()