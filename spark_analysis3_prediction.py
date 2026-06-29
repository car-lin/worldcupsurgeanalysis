from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, avg, lit

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
    .appName("Analysis3_Prediction")
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

# Reads the cleaned CBP dataset from Azure Blob Storage
cbp = spark.read.csv(
    f"{base_path}/processed/clean/cbp_clean",
    header=True,
    inferSchema=True
)

# -----------------------------
# STEP 1: Qatar baseline demand
# -----------------------------
# Filters Comtrade data to keep only Qatar records and remove aggregate TOTAL commodity rows
qatar = (
    comtrade
    .filter(col("country_iso3") == "QAT")
    .filter(col("commodity_code") != "TOTAL")
)

# Calculates Qatar baseline demand by summing trade value for each commodity
qatar_demand = (
    qatar
    .groupBy("commodity_code")
    .agg(spark_sum("trade_value").alias("qatar_demand"))
)

# -----------------------------
# STEP 2: Country scaling (GDP)
# -----------------------------
# Extracts GDP per capita values from the World Bank dataset
gdp = (
    worldbank
    .filter(col("indicator_name") == "gdp_per_capita")
    .filter(col("value").isNotNull())
    .groupBy("country_iso3")
    .agg(avg("value").alias("avg_gdp"))
)

# Normalize GDP (simple scaling)
# Finds the maximum average GDP value to use as the scaling reference
gdp_max = gdp.agg({"avg_gdp": "max"}).collect()[0][0]

# Creates a GDP factor by dividing each country's GDP by the maximum GDP value
gdp_scaled = gdp.withColumn(
    "gdp_factor",
    col("avg_gdp") / gdp_max
)

# -----------------------------
# STEP 3: Capacity (CBP)
# -----------------------------
# Calculates average employment from CBP data as a simple capacity indicator
capacity = (
    cbp
    .groupBy()
    .agg(avg("employment").alias("avg_employment"))
)

# Collects the average capacity value from Spark into Python
avg_capacity = capacity.collect()[0][0]

# -----------------------------
# STEP 4: Predict demand for USA (example)
# -----------------------------
# Retrieves the GDP scaling factor for the USA
usa_factor = gdp_scaled.filter(col("country_iso3") == "USA").select("gdp_factor").collect()[0][0]

# Predicts demand by scaling Qatar demand using the USA GDP factor
prediction = qatar_demand.withColumn(
    "predicted_demand",
    col("qatar_demand") * usa_factor
)

# -----------------------------
# STEP 5: Opportunity score
# -----------------------------
# Calculates opportunity score by comparing predicted demand against average capacity
prediction = prediction.withColumn(
    "opportunity_score",
    col("predicted_demand") / (lit(avg_capacity) + 1)
)

# Rank
# Orders commodities from highest to lowest opportunity score
prediction = prediction.orderBy(col("opportunity_score").desc())

# -----------------------------
# SAVE OUTPUT
# -----------------------------
# Writes the prediction output to Azure Blob Storage
prediction.write.mode("overwrite").option("header", True).csv(
    f"{base_path}/processed/analysis3/prediction"
)

# Prints confirmation that the analysis has completed
print("Analysis 3 complete")

# Stops the Spark session to release resources
spark.stop()