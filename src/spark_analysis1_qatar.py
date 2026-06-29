from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, month, year

# Imports helper functions to load configuration and environment variables
from settings import load_config, get_env

# Loads configuration values from the YAML config file
cfg = load_config()

# Retrieves Azure Blob Storage connection string from environment variables
connection_string = get_env("AZURE_STORAGE_CONNECTION_STRING")

# Gets the Azure container name from the configuration
container = cfg["azure"]["container_name"]

# Parses the connection string into key-value pairs
parts = dict(item.split("=", 1) for item in connection_string.split(";") if "=" in item)

# Extracts the storage account name and account key from the connection string
account_name = parts["AccountName"]
account_key = parts["AccountKey"]

# Initializes a Spark session with required Azure storage dependencies
spark = (
    SparkSession.builder
    .appName("Analysis1_QatarDemandSurge")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-azure:3.3.4,com.microsoft.azure:azure-storage:8.6.6"
    )
    .getOrCreate()
)

# Configures Spark to authenticate with Azure Blob Storage using the account key
spark._jsc.hadoopConfiguration().set(
    f"fs.azure.account.key.{account_name}.blob.core.windows.net",
    account_key
)

# Constructs the base path for accessing files in Azure Blob Storage
base_path = f"wasbs://{container}@{account_name}.blob.core.windows.net"

# Reads the cleaned Comtrade dataset from Azure Blob Storage
df = spark.read.csv(
    f"{base_path}/processed/clean/comtrade_clean",
    header=True,
    inferSchema=True
)

# Filters the dataset to include only Qatar data and excludes aggregate "TOTAL" rows
qatar = (
    df
    .filter(col("country_iso3") == "QAT")
    .filter(col("commodity_code") != "TOTAL")
)

# Computes total import value per commodity for Qatar
top_commodities = (
    qatar
    .groupBy("commodity_code", "commodity_desc")
    .agg(spark_sum("trade_value").alias("total_import_value"))
    .orderBy(col("total_import_value").desc())
)

# Writes the top commodities result to Azure Blob Storage
top_commodities.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/analysis1/top_commodities"
)

# Extracts year and month from the date column for time-based analysis
qatar = (
    qatar
    .withColumn("year", year("month_date"))
    .withColumn("month", month("month_date"))
)

# Aggregates monthly import values to analyze trends over time
monthly_trend = (
    qatar
    .groupBy("year", "month")
    .agg(spark_sum("trade_value").alias("monthly_import_value"))
    .orderBy("year", "month")
)

# Writes the monthly trend analysis result to Azure Blob Storage
monthly_trend.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/analysis1/monthly_trend"
)

# Prints confirmation that the analysis has completed
print("Analysis 1 complete")

# Stops the Spark session to release resources
spark.stop()
